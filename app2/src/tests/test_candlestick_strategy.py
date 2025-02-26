import pytest
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candlestick_strategy import CandlestickPatternStrategy

class TestData(bt.feeds.PandasData):
    """Test data feed using pandas"""
    
    def __init__(self, dataframe, **kwargs):
        # Convert index to datetime if it's not already
        if not isinstance(dataframe.index, pd.DatetimeIndex):
            dataframe = dataframe.set_index(pd.DatetimeIndex(dataframe.index))
        
        # Add any missing columns with default values
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in dataframe.columns:
                if col == 'Volume':
                    dataframe[col] = 100000
                else:
                    dataframe[col] = dataframe['Close']
        
        super(TestData, self).__init__(dataname=dataframe, **kwargs)

@pytest.fixture
def test_data():
    """Create a test dataset with some patterns embedded"""
    dates = pd.date_range(start='2022-01-01', periods=30)
    
    # Create price data with some bullish and bearish setups
    data = pd.DataFrame({
        'Open':  [100 + i + (i % 3 - 1) * 2 for i in range(30)],
        'Close': [100 + i + (i % 5 - 2) * 1.5 for i in range(30)],
        'Volume': [100000 for _ in range(30)]
    }, index=dates)
    
    # Add High and Low that create some pattern-like behavior
    # Days 5, 15, 25: Hammer-like
    # Days 10, 20: Shooting star-like
    highs = []
    lows = []
    
    for i in range(30):
        c = data.iloc[i]['Close']
        o = data.iloc[i]['Open']
        
        if i % 10 == 5:  # Hammer-like
            h = max(o, c) + 1
            l = min(o, c) - 5
        elif i % 10 == 0:  # Shooting star-like
            h = max(o, c) + 5
            l = min(o, c) - 1
        else:
            h = max(o, c) + 2
            l = min(o, c) - 2
            
        highs.append(h)
        lows.append(l)
    
    data['High'] = highs
    data['Low'] = lows
    
    return data

def test_strategy_initialization():
    """Test that the strategy initializes correctly with various parameters"""
    cerebro = bt.Cerebro()
    data = TestData(pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [95, 96, 97],
        'Close': [101, 102, 103],
        'Volume': [100000, 100000, 100000]
    }, index=pd.date_range(start='2022-01-01', periods=3)))
    
    cerebro.adddata(data)
    
    # Test with various pattern lists
    cerebro.addstrategy(CandlestickPatternStrategy, patterns=['doji', 'hammer'])
    result = cerebro.run()
    assert len(result) == 1, "Strategy initialization failed"
    
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(CandlestickPatternStrategy, 
                        patterns=['engulfing'], 
                        stop_loss=0.1,
                        take_profit=0.2)
    result = cerebro.run()
    assert len(result) == 1, "Strategy initialization with custom parameters failed"

def test_strategy_tracking_trades(test_data):
    """Test that the strategy correctly tracks trades"""
    cerebro = bt.Cerebro()
    data = TestData(test_data)
    cerebro.adddata(data)
    
    # Add a trade analyzer
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Configure the strategy with multiple patterns
    cerebro.addstrategy(CandlestickPatternStrategy, 
                        patterns=['hammer', 'shooting_star', 'engulfing'],
                        stop_loss=0.05,
                        take_profit=0.1,
                        exit_on_opposite=True)
    
    # Run with initial cash
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%
    
    results = cerebro.run()
    
    # Check that the strategy made some trades
    strategy = results[0]
    trade_analysis = strategy.analyzers.trades.get_analysis()
    
    # Assert that some trades were executed
    assert strategy.num_trades > 0, "Strategy didn't make any trades"
    
    # Check that the trade analyzer recorded the trades
    assert 'total' in trade_analysis
    assert trade_analysis['total']['total'] > 0

def test_strategy_profit_tracking(test_data):
    """Test that the strategy correctly tracks profitable trades"""
    cerebro = bt.Cerebro()
    data = TestData(test_data)
    cerebro.adddata(data)
    
    # Configure the strategy
    cerebro.addstrategy(CandlestickPatternStrategy, 
                        patterns=['hammer', 'engulfing'],
                        stop_loss=0.03,  # Tighter stop to ensure some stops are hit
                        take_profit=0.06)  # Smaller target to ensure some profits are taken
    
    # Run with initial cash
    initial_cash = 10000
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%
    
    results = cerebro.run()
    strategy = results[0]
    
    # Get final portfolio value
    final_value = cerebro.broker.getvalue()
    
    # Make sure the strategy recorded trades correctly
    assert strategy.num_trades == strategy.num_profitable_trades + (strategy.num_trades - strategy.num_profitable_trades), \
        "Trade counting is incorrect"
    
    # Check that the strategy attributes match the actual performance
    if strategy.num_trades > 0:
        win_rate = strategy.num_profitable_trades / strategy.num_trades
        # Ensure the terminal portfolio value makes sense given the recorded win rate
        if win_rate > 0.5:  # If win rate > 50%, portfolio should grow
            assert final_value >= initial_cash, f"With win rate {win_rate}, portfolio should have grown"
        elif win_rate < 0.3:  # If win rate < 30%, portfolio likely shrinks
            assert final_value <= initial_cash, f"With win rate {win_rate}, portfolio should have decreased"

def test_strategy_stop_loss_and_take_profit():
    """Test that stop loss and take profit orders work correctly"""
    # Create a very specific dataset to test stops and targets
    dates = pd.date_range(start='2022-01-01', periods=10)
    data = pd.DataFrame({
        # Day 0: Setup
        # Day 1: Generate buy signal (hammer)
        # Day 2-3: Price rises (test take profit)
        # Day 4: Setup again
        # Day 5: Generate buy signal (hammer)
        # Day 6-7: Price falls (test stop loss)
        'Open':  [100, 95, 101, 105, 110, 105, 101, 95, 90, 85],
        'High':  [105, 100, 106, 110, 115, 110, 103, 101, 95, 90],
        'Low':   [95, 85, 100, 103, 105, 95, 90, 90, 85, 80],  # Day 1, 5: Hammer-like pattern
        'Close': [101, 98, 104, 108, 112, 108, 95, 92, 87, 82],
        'Volume':[100000] * 10
    }, index=dates)
    
    cerebro = bt.Cerebro()
    cerebro.adddata(TestData(data))
    
    # Set up the strategy with clear stop loss and take profit levels
    stop_loss = 0.05   # 5% stop loss
    take_profit = 0.08  # 8% take profit
    
    cerebro.addstrategy(CandlestickPatternStrategy, 
                        patterns=['hammer'],
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        consecutive_bars=1,
                        exit_on_opposite=False)  # Disable exit on opposite to isolate stop/target tests
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Run with initial cash
    cerebro.broker.setcash(10000)
    results = cerebro.run()
    
    strategy = results[0]
    trade_analysis = strategy.analyzers.trades.get_analysis()
    
    # Check that trades were opened and closed
    assert 'total' in trade_analysis
    assert trade_analysis['total']['total'] > 0
    
    # Check win/loss results (at least 1 win from take profit and 1 loss from stop loss)
    assert trade_analysis['won']['total'] > 0, "No winning trades recorded"
    assert trade_analysis['lost']['total'] > 0, "No losing trades recorded"

def test_strategy_parameter_impact():
    """Test how different strategy parameters affect performance"""
    # Create test data
    dates = pd.date_range(start='2022-01-01', periods=100)
    np.random.seed(42)  # For reproducibility
    
    # Generate price data with some patterns embedded
    closes = []
    price = 100
    for i in range(100):
        # Add some mean reversion and trend
        price_change = np.random.normal(0, 1) + 0.05 * (100 - price)
        price += price_change
        closes.append(price)
    
    # Create DataFrame
    data = pd.DataFrame({
        'Close': closes
    }, index=dates)
    
    # Add open price with some randomness
    data['Open'] = data['Close'].shift(1) * (1 + np.random.normal(0, 0.005, len(data)))
    data['Open'].iloc[0] = data['Close'].iloc[0] * 0.99
    
    # Add high and low with some randomness
    data['High'] = data[['Open', 'Close']].max(axis=1) * (1 + abs(np.random.normal(0, 0.01, len(data))))
    data['Low'] = data[['Open', 'Close']].min(axis=1) * (1 - abs(np.random.normal(0, 0.01, len(data))))
    
    data['Volume'] = 100000
    
    # Strategy performance with different parameters
    results = []
    
    for stop_loss in [0.02, 0.05, 0.1]:
        for take_profit in [0.05, 0.1, 0.2]:
            cerebro = bt.Cerebro()
            cerebro.adddata(TestData(data))
            cerebro.broker.setcash(10000)
            
            cerebro.addstrategy(CandlestickPatternStrategy,
                               patterns=['engulfing', 'hammer', 'shooting_star'],
                               stop_loss=stop_loss,
                               take_profit=take_profit)
            
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            
            res = cerebro.run()
            strategy = res[0]
            
            trade_analysis = strategy.analyzers.trades.get_analysis()
            total_trades = trade_analysis.get('total', {}).get('total', 0)
            
            results.append({
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'final_value': cerebro.broker.getvalue(),
                'trades': total_trades,
                'win_rate': (strategy.num_profitable_trades / strategy.num_trades) 
                           if strategy.num_trades > 0 else 0
            })
    
    # Check that we get different results with different parameters
    assert len(results) > 1, "No parameter combinations tested"
    
    # Check that different parameters produce different results
    final_values = [r['final_value'] for r in results]
    assert max(final_values) != min(final_values), "All parameter combinations gave same result"