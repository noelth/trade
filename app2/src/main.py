import os
import argparse
import datetime
import backtrader as bt
from dotenv import load_dotenv
import pandas as pd
import alpaca_trade_api as tradeapi
import importlib

# Plotly imports commented out since we're using Backtrader's built-in charting
# import plotly.graph_objs as go
# import plotly.io as pio

# ---------------------------------------------
#         LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------
import os.path
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

ALPACA_API_KEY = os.getenv('APCA_API_KEY_ID')
ALPACA_API_SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')
ALPACA_API_URL = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets/v2')
ALPACA_PAPER = os.getenv('ALPACA_PAPER', 'True')

print("ALPACA_API_KEY (APCA_API_KEY_ID):", ALPACA_API_KEY)
print("ALPACA_API_SECRET_KEY:", ALPACA_API_SECRET_KEY)
print("ALPACA_API_URL (APCA_API_BASE_URL):", ALPACA_API_URL)
print("ALPACA_PAPER:", ALPACA_PAPER)

# ---------------------------------------------
#          IMPORT CUSTOM STRATEGIES
# ---------------------------------------------
from strategy import SmaCross, BollingerBreakoutStrategy, RsiMacdStrategy, TestStrat1, HighVolPivotsStrategy, MarketStructureStrategy, CustomBuySell

# ---------------------------------------------
#           HELPER FUNCTIONS
# ---------------------------------------------
def get_alpaca_api():
    api = tradeapi.REST(
        key_id=ALPACA_API_KEY,
        secret_key=ALPACA_API_SECRET_KEY,
        base_url=ALPACA_API_URL,
        api_version='v2'
    )
    return api

def chunk_date_range(start_date, end_date, chunk_size_days=30):
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + datetime.timedelta(days=chunk_size_days), end_date)
        yield (current_start, current_end)
        current_start = current_end + datetime.timedelta(days=1)

def fetch_bars_in_chunks(api, symbol, timeframe_str, start_str, end_str):
    start_date = pd.to_datetime(start_str)
    end_date = pd.to_datetime(end_str)
    all_bars = []
    for (chunk_start, chunk_end) in chunk_date_range(start_date, end_date):
        chunk_start_str = chunk_start.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')
        try:
            bars_chunk = api.get_bars(
                symbol,
                timeframe_str,
                start=chunk_start_str,
                end=chunk_end_str,
                adjustment='all'
            ).df
            if not bars_chunk.empty:
                if 'symbol' in bars_chunk.columns:
                    bars_chunk = bars_chunk[bars_chunk['symbol'] == symbol]
                all_bars.append(bars_chunk)
        except Exception as e:
            print(f"Error fetching bars from {chunk_start_str} to {chunk_end_str}: {e}")
    if not all_bars:
        return pd.DataFrame()
    df = pd.concat(all_bars)
    df.sort_index(inplace=True)
    return df

def validate_symbol_is_tradable(api, symbol):
    try:
        asset = api.get_asset(symbol)
        if not asset.tradable:
            print(f"Warning: {symbol} is not tradable on Alpaca.")
    except Exception as e:
        print(f"Could not verify if {symbol} is tradable: {e}")

def convert_timeframe(tf_str):
    tf_str = tf_str.lower()
    if tf_str in ['1min', '1m', 'minute']:
        return "1Min"
    elif tf_str in ['5min', '5m']:
        return "5Min"
    elif tf_str in ['15min', '15m']:
        return "15Min"
    elif tf_str in ['1d', 'day', 'daily']:
        return "1Day"
    else:
        raise ValueError("Unsupported timeframe: " + tf_str)

def log_results(strategy_name, num_trades, num_profitable_trades, pct_change, underlying_growth, final_value, params):
    # Create the Results directory if it doesn't exist
    results_dir = 'Results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Create a DataFrame for the results
    results_df = pd.DataFrame({
        'Strategy': [strategy_name],
        'Number of Trades': [num_trades],
        'Number of Profitable Trades': [num_profitable_trades],
        'Percent Change': [pct_change],
        'Underlying Stock Growth': [underlying_growth],
        'Final Portfolio Value': [final_value],
        **params  # Unpack the parameters dictionary
    })

    # Define the filename based on the strategy name
    filename = os.path.join(results_dir, f"{strategy_name}_results.csv")

    # Append the results to the CSV file
    if os.path.exists(filename):
        results_df.to_csv(filename, index=False, header=False, mode='a')  # Append without header
    else:
        results_df.to_csv(filename, index=False)  # Create new file with header

# ---------------------------------------------
#                  MAIN LOGIC
# ---------------------------------------------
def main(args):
    api = get_alpaca_api()
    validate_symbol_is_tradable(api, args.ticker)
    alpaca_timeframe = convert_timeframe(args.timeframe)
    data_df = fetch_bars_in_chunks(api, args.ticker, alpaca_timeframe, args.start, args.end)
    
    if data_df.empty:
        print("No data returned from Alpaca for the specified parameters.")
        return
    
    data_df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    print(f"Running backtest for {args.ticker} from {data_df.index[0]} to {data_df.index[-1]} using timeframe: {args.timeframe}")
    data_feed = bt.feeds.PandasData(dataname=data_df)
    cerebro = bt.Cerebro()

    # Select strategy based on CLI argument.
    if args.strategy == 'sma':
        cerebro.addstrategy(
            SmaCross,
            sma_fast_period=args.sma_fast_period,
            sma_slow_period=args.sma_slow_period,
            take_profit=args.sma_take_profit
        )
        params = {
            'sma_fast_period': args.sma_fast_period,
            'sma_slow_period': args.sma_slow_period,
            'take_profit': args.sma_take_profit,
            'ticker': args.ticker,
            'start_date': args.start,
            'end_date': args.end,
            'timeframe': args.timeframe,
            'commission': args.commission,
            'principal': args.principal
        }
    elif args.strategy == 'bbbreak':
        cerebro.addstrategy(
            BollingerBreakoutStrategy,
            period=args.bbbreak_bb_period,
            devfactor=args.bbbreak_bb_dev,
            stop_loss=args.bbbreak_stop_loss,
            take_profit=args.bbbreak_take_profit
        )
        params = {
            'period': args.bbbreak_bb_period,
            'devfactor': args.bbbreak_bb_dev,
            'stop_loss': args.bbbreak_stop_loss,
            'take_profit': args.bbbreak_take_profit,
            'ticker': args.ticker,
            'start_date': args.start,
            'end_date': args.end,
            'timeframe': args.timeframe,
            'commission': args.commission,
            'principal': args.principal,
            'num_trades': 0,  # Initialize to 0
            'num_profitable_trades': 0  # Initialize to 0
        }
    else:
        print("Unknown strategy specified.")
        return

    cerebro.adddata(data_feed)
    cerebro.broker.setcash(args.principal)
    cerebro.broker.setcommission(commission=args.commission)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=args.percent)
    cerebro.addobserver(CustomBuySell)

    initial_value = args.principal
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    
    # Run the strategy and get the results
    strategies = cerebro.run()
    
    # Ensure strategies is not empty
    if not strategies:
        print("No strategies were run.")
        return

    final_value = cerebro.broker.getvalue()
    pct_change = (final_value - initial_value) / initial_value * 100
    first_close = data_df['Close'].iloc[0]
    last_close = data_df['Close'].iloc[-1]
    stock_growth = (last_close - first_close) / first_close * 100

    # Get the number of trades and profitable trades from the strategy
    num_trades = strategies[0].num_trades
    num_profitable_trades = strategies[0].num_profitable_trades

    # Log results to CSV
    log_results(args.strategy, num_trades, num_profitable_trades, pct_change, stock_growth, final_value, params)

    cerebro.plot(style='candle', volume=False)

# ---------------------------------------------
#             COMMAND-LINE INTERFACE
# ---------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtest a trading strategy for a given stock ticker using Alpaca data.')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker symbol (e.g., TSLA)')
    parser.add_argument('--start', type=str, default='2019-01-01', help='Start date (YYYY-MM-DD) [default: 2019-01-01]')
    parser.add_argument('--end', type=str, default='2025-02-01', help='End date (YYYY-MM-DD) [default: 2025-02-01]')
    parser.add_argument('--timeframe', type=str, default='1D', help='Candlestick timeframe (e.g., "1Min", "5Min", "15Min", "1D")')
    parser.add_argument('--principal', type=float, default=1000, help='Initial cash/principal amount (default: 1000)')
    parser.add_argument('--commission', type=float, default=0.0003, help='Brokerage fee as commission per transaction (default: 0.03%%, i.e., 0.0003)')
    parser.add_argument('--percent', type=float, default=20, help='Percentage of portfolio to invest per trade (default: 20%)')
    parser.add_argument('--strategy', type=str, choices=['MarketStructure', 'TestStrat1', 'marketstructure', 'volpivots', 'sma', 'bbbreak'], default='MarketStructure', help='Strategy to run (default: MarketStructure)')
    
    # Parameters for MarketStructureStrategy:
    parser.add_argument('--atr-period', type=int, default=20, help='ATR period for MarketStructure strategy (default: 20)')
    parser.add_argument('--atr-multiplier', type=float, default=2.0, help='ATR multiplier for MarketStructure strategy (default: 2.0)')
    parser.add_argument('--breakout-bars', type=int, default=10, help='Breakout bars to wait for pullback (default: 10)')
    
    # Parameters for TestStrat1:
    parser.add_argument('--bb-period', type=int, default=20, help='Bollinger Bands period for TestStrat1 (default: 20)')
    parser.add_argument('--bb-dev', type=float, default=2.0, help='Bollinger Bands deviation factor for TestStrat1 (default: 2.0)')
    parser.add_argument('--sma-short-period', type=int, default=100, help='Short SMA period for TestStrat1 (default: 100)')
    parser.add_argument('--sma-long-period', type=int, default=200, help='Long SMA period for TestStrat1 (default: 200)')
    parser.add_argument('--ts1-atr-period', type=int, default=14, help='ATR period for TestStrat1 (default: 14)')
    parser.add_argument('--ts1-atr-multiplier', type=float, default=2.0, help='ATR multiplier for TestStrat1 (default: 2.0)')
    parser.add_argument('--basic-stop-pct', type=float, default=0.025, help='Basic stop-loss percentage for TestStrat1 (default: 0.025)')
    parser.add_argument('--sma-crossover-bars', type=int, default=3, help='Number of bars for SMA crossover condition (default: 3)')
    
    # Parameters for MarketStructureStrategy:
    parser.add_argument('--ms-atr-period', type=int, default=20, help='ATR period for MarketStructureStrategy (default: 20)')
    parser.add_argument('--ms-breakout-bars', type=int, default=10, help='Breakout bars for MarketStructureStrategy (default: 10)')
    parser.add_argument('--ms-atr-multiplier', type=float, default=2.0, help='ATR multiplier for MarketStructureStrategy (default: 2.0)')
    
    # Parameters for HighVolPivotsStrategy:
    parser.add_argument('--left-bars', type=int, default=15, help='Number of bars to the left for pivot detection (default: 15)')
    parser.add_argument('--right-bars', type=int, default=1, help='Number of bars to the right for pivot detection (default: 1)')
    parser.add_argument('--filter-vol', type=float, default=5.6, help='Normalized volume threshold for pivot detection (default: 5.6)')
    parser.add_argument('--lookback', type=int, default=300, help='Number of bars for rolling volume percentile calculation (default: 300)')
    parser.add_argument('--percentile-rank', type=float, default=95.0, help='Percentile used for "high volume" detection (default: 95.0)')
    parser.add_argument('--show-levels', action='store_true', help='Whether to add PivotLine indicators for detected pivots (default: False)')
    parser.add_argument('--step', type=float, default=0.6, help='Parameter for adjusting marker sizes (default: 0.6)')
    
    # Parameters for SmaCross:
    parser.add_argument('--sma-fast-period', type=int, default=50, help='Fast SMA period for SmaCross (default: 50)')
    parser.add_argument('--sma-slow-period', type=int, default=200, help='Slow SMA period for SmaCross (default: 200)')
    parser.add_argument('--sma-take-profit', type=float, default=0.0, help='Take profit percentage for SmaCross (default: 0.0, disabled)')

    # Parameters for BollingerBreakoutStrategy:
    parser.add_argument('--bbbreak-bb-period', type=int, default=20, help='Bollinger Bands period for BollingerBreakoutStrategy (default: 20)')
    parser.add_argument('--bbbreak-bb-dev', type=float, default=2.0, help='Bollinger Bands deviation factor for BollingerBreakoutStrategy (default: 2.0)')
    parser.add_argument('--bbbreak-stop-loss', type=float, default=0.05, help='Stop loss percentage for BollingerBreakoutStrategy (default: 0.05)')
    parser.add_argument('--bbbreak-take-profit', type=float, default=0.10, help='Take profit percentage for BollingerBreakoutStrategy (default: 0.10)')

    args = parser.parse_args()
    main(args)

STRATEGIES = {
    'sma': SmaCross,
    'bbbreak': BollingerBreakoutStrategy,
    'rsimacd': RsiMacdStrategy,
    'teststrat1': TestStrat1,
    'volpivots': HighVolPivotsStrategy,
    'marketstructure': MarketStructureStrategy
}