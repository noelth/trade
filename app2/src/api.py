from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import pandas as pd
import backtrader as bt
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import pytz
import json
import uuid
import asyncio
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')  # Use Agg backend to prevent display requirement

# Import strategies
from strategy import SmaCross, BollingerBreakoutStrategy, RsiMacdStrategy
from candlestick_strategy import CandlestickPatternStrategy
from candlestick_patterns import CANDLESTICK_PATTERNS

app = FastAPI(title="Trading Backtest API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()
ALPACA_API_KEY = os.getenv('APCA_API_KEY_ID')
ALPACA_API_SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')
ALPACA_API_URL = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets/v2')

# Dictionary to store backtest results
backtest_results = {}

# Pydantic models for request and response
class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    timeframe: str = "1d"
    principal: float = 10000.0
    commission: float = 0.0003
    strategy_type: str
    strategy_params: Dict[str, Any] = {}

class PatternParams(BaseModel):
    pattern_name: str
    params: Dict[str, Any] = {}

class CandlestickStrategyParams(BaseModel):
    patterns: List[str]
    pattern_params: Dict[str, Dict[str, Any]] = {}
    stop_loss: float = 0.05
    take_profit: float = 0.10
    consecutive_bars: int = 1
    confirmation_indicator: Optional[str] = None
    confirmation_params: Dict[str, Any] = {}
    exit_on_opposite: bool = True

class BacktestResult(BaseModel):
    id: str
    status: str
    ticker: str
    start_date: str
    end_date: str
    final_portfolio_value: Optional[float] = None
    total_return: Optional[float] = None
    num_trades: Optional[int] = None
    num_profitable_trades: Optional[int] = None
    profit_factor: Optional[float] = None
    strategy_type: str
    strategy_params: Dict[str, Any]
    chart_path: Optional[str] = None
    error: Optional[str] = None

class AvailablePatternsResponse(BaseModel):
    patterns: List[str]

# Helper functions
def get_alpaca_api():
    return tradeapi.REST(
        key_id=ALPACA_API_KEY,
        secret_key=ALPACA_API_SECRET_KEY,
        base_url=ALPACA_API_URL,
        api_version='v2'
    )

def fetch_data(ticker, start_date, end_date, timeframe):
    """Fetch historical data from Alpaca"""
    api = get_alpaca_api()
    
    # Convert timeframe to Alpaca format
    if timeframe.lower() in ['1d', 'day', 'daily']:
        alpaca_timeframe = "1Day"
    elif timeframe.lower() in ['1h', 'hour', 'hourly']:
        alpaca_timeframe = "1Hour"
    elif timeframe.lower() in ['15m', '15min']:
        alpaca_timeframe = "15Min"
    elif timeframe.lower() in ['5m', '5min']:
        alpaca_timeframe = "5Min"
    elif timeframe.lower() in ['1m', '1min', 'minute']:
        alpaca_timeframe = "1Min"
    else:
        alpaca_timeframe = "1Day"
    
    try:
        bars = api.get_bars(
            ticker, 
            alpaca_timeframe, 
            start=start_date, 
            end=end_date, 
            adjustment='all'
        ).df
        
        # Handle multi-index DataFrame if returned
        if isinstance(bars.index, pd.MultiIndex):
            if ticker in bars.index.levels[0]:
                bars = bars.xs(ticker, level=0)
        
        # Standardize column names to match Backtrader expectations
        bars.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        return bars
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching data from Alpaca: {str(e)}"
        )

def get_strategy_class(strategy_type):
    """Get the appropriate strategy class based on type"""
    strategies = {
        "sma_cross": SmaCross,
        "bollinger_breakout": BollingerBreakoutStrategy,
        "rsi_macd": RsiMacdStrategy,
        "candlestick": CandlestickPatternStrategy
    }
    
    return strategies.get(strategy_type)

async def run_backtest(backtest_id, request):
    """Run backtest in background and save results"""
    try:
        # Update status to "running"
        backtest_results[backtest_id]["status"] = "running"
        
        # Fetch data
        data = fetch_data(
            request.ticker,
            request.start_date,
            request.end_date,
            request.timeframe
        )
        
        if data.empty:
            raise Exception(f"No data available for {request.ticker} in the specified date range")
        
        # Setup cerebro
        cerebro = bt.Cerebro()
        
        # Add data feed
        data_feed = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_feed)
        
        # Set initial cash
        cerebro.broker.setcash(request.principal)
        cerebro.broker.setcommission(commission=request.commission)
        
        # Add strategy
        strategy_class = get_strategy_class(request.strategy_type)
        if not strategy_class:
            raise Exception(f"Strategy type {request.strategy_type} not supported")
        
        cerebro.addstrategy(strategy_class, **request.strategy_params)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        
        # Run backtest
        initial_value = request.principal
        results = cerebro.run()
        strategy = results[0]
        
        # Get trade statistics
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - initial_value) / initial_value * 100
        
        # Get analyzer results
        trades = strategy.analyzers.trades.get_analysis()
        total_trades = trades.get('total', {}).get('closed', 0)
        winning_trades = trades.get('won', {}).get('total', 0)
        
        # Save plot if possible
        plot_path = f"static/charts/{backtest_id}.png"
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        
        try:
            cerebro.plot(style='candle', barup='#77d879', bardown='#db3f3f', 
                         volup='#77d879', voldown='#db3f3f', 
                         gridstyle='--', plotdist=1, fmt_x_data='%Y-%m-%d')[0][0].savefig(plot_path)
        except Exception as e:
            print(f"Error saving plot: {e}")
            plot_path = None
        
        # Update results
        backtest_results[backtest_id].update({
            "status": "completed",
            "final_portfolio_value": final_value,
            "total_return": total_return,
            "num_trades": total_trades,
            "num_profitable_trades": winning_trades,
            "profit_factor": winning_trades / total_trades if total_trades > 0 else 0,
            "chart_path": plot_path
        })
    
    except Exception as e:
        backtest_results[backtest_id].update({
            "status": "failed",
            "error": str(e)
        })
        print(f"Backtest error: {e}")

# Routes
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Trading Backtest API is running"}

@app.get("/available-patterns", response_model=AvailablePatternsResponse, tags=["Configuration"])
async def get_available_patterns():
    """Get list of available candlestick patterns"""
    return {"patterns": list(CANDLESTICK_PATTERNS.keys())}

@app.post("/backtest", response_model=BacktestResult, tags=["Backtest"])
async def create_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Initiate a backtest with the specified parameters"""
    # Validate basic parameters
    try:
        datetime.strptime(request.start_date, '%Y-%m-%d')
        datetime.strptime(request.end_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD format."
        )
    
    # Generate unique ID for this backtest
    backtest_id = str(uuid.uuid4())
    
    # Create initial result entry
    result = {
        "id": backtest_id,
        "status": "pending",
        "ticker": request.ticker,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "strategy_type": request.strategy_type,
        "strategy_params": request.strategy_params
    }
    
    backtest_results[backtest_id] = result
    
    # Schedule backtest to run in background
    background_tasks.add_task(run_backtest, backtest_id, request)
    
    return result

@app.get("/backtest/{backtest_id}", response_model=BacktestResult, tags=["Backtest"])
async def get_backtest_status(backtest_id: str):
    """Get the status and results of a backtest"""
    if backtest_id not in backtest_results:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest with ID {backtest_id} not found"
        )
    
    return backtest_results[backtest_id]

@app.get("/backtests", response_model=List[BacktestResult], tags=["Backtest"])
async def list_backtests():
    """Get a list of all backtests"""
    return list(backtest_results.values())

if __name__ == "__main__":
    import uvicorn
    # Create directory for chart images if it doesn't exist
    os.makedirs("static/charts", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)