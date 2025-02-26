import os
import argparse
import datetime
import backtrader as bt
from dotenv import load_dotenv
import pandas as pd
import alpaca_trade_api as tradeapi
import importlib

# ---------------------------------------------
#         LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------
import os.path
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

ALPACA_API_KEY = os.getenv('APCA_API_KEY_ID')
ALPACA_API_SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')
ALPACA_API_URL = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets/v2')

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

def parse_optparams(optparams_str):
    """
    Parses a comma-separated list of parameter ranges.
    Returns a dictionary mapping parameter names to a tuple (min, max, type).
    Example input: "atr_period:15:25,breakout_bars:8:12,atr_multiplier:1.5:2.5"
    """
    optparams = {}
    if not optparams_str:
        return optparams
    parts = optparams_str.split(',')
    for part in parts:
        try:
            param, vmin, vmax = part.split(':')
            try:
                vmin = int(vmin)
                vmax = int(vmax)
                optparams[param] = (vmin, vmax, 'int')
            except ValueError:
                vmin = float(vmin)
                vmax = float(vmax)
                optparams[param] = (vmin, vmax, 'float')
        except Exception as e:
            print(f"Error parsing parameter range '{part}': {e}")
    return optparams

def build_opt_params(optparams):
    """
    Converts the dictionary of optimization ranges to a dictionary of parameter lists
    suitable for passing to cerebro.optstrategy.
    For int type, uses range(min, max+1).
    For float type, uses a list of values with step=0.1 (adjustable as needed).
    """
    opt_dict = {}
    for param, (vmin, vmax, vtype) in optparams.items():
        if vtype == 'int':
            if vmin < 1:
                vmin = 1  # Ensure valid value
            opt_dict[param] = range(vmin, vmax + 1)
        elif vtype == 'float':
            values = []
            val = vmin
            while val <= vmax + 1e-6:
                values.append(round(val, 2))
                val += 0.1
            opt_dict[param] = values
    return opt_dict

def main(args):
    api = get_alpaca_api()
    alpaca_timeframe = convert_timeframe(args.timeframe)
    data_df = fetch_bars_in_chunks(api, args.ticker, alpaca_timeframe, args.start, args.end)
    if data_df.empty:
        print("No data returned from Alpaca for the specified parameters.")
        return
    data_df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
    data_feed = bt.feeds.PandasData(dataname=data_df)
    cerebro = bt.Cerebro(optreturn=False)
    
    # Dynamically import the strategy from the strategies file.
    try:
        strategies_module = importlib.import_module('strategy')
        strategy_class = getattr(strategies_module, args.strategy)
    except Exception as e:
        print(f"Error loading strategy '{args.strategy}': {e}")
        return

    optparams_dict = parse_optparams(args.optparams)
    opt_strategy_params = build_opt_params(optparams_dict)
    if not opt_strategy_params:
        print("No optimization parameters provided; exiting optimization.")
        return

    cerebro.optstrategy(strategy_class, **opt_strategy_params)
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(args.principal)
    cerebro.broker.setcommission(commission=args.commission)
    # Use PercentSizer for dynamic percentage-based position sizing:
    cerebro.addsizer(bt.sizers.PercentSizer, percents=args.percent)
    
    print("Starting optimization...")
    try:
        optimized_runs = cerebro.run()
    except Exception as e:
        print("Error during optimization run:", e)
        return
    
    best_result = None
    best_value = -float('inf')
    for run in optimized_runs:
        strat = run[0]
        final_value = strat.broker.getvalue()
        if final_value > best_value:
            best_value = final_value
            best_result = strat

    print(f"Best final portfolio value: {best_value:.2f}")
    # Use explicit check to avoid calling __nonzero__ on best_result:
    if best_result is not None:
        print("Best Strategy Parameters:")
        for param, value in best_result.params._getitems():
            print(f"  {param}: {value}")
    else:
        print("No best result found.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optimize parameters for a strategy using Alpaca data.')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker symbol (e.g., TSLA)')
    parser.add_argument('--start', type=str, default='2019-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2025-02-01', help='End date (YYYY-MM-DD)')
    parser.add_argument('--timeframe', type=str, default='1D', help='Candlestick timeframe (e.g., "1Min", "5Min", "15Min", "1D")')
    parser.add_argument('--principal', type=float, default=1000, help='Initial cash amount')
    parser.add_argument('--commission', type=float, default=0.0003, help='Commission per transaction')
    parser.add_argument('--percent', type=float, default=10, help='Percentage of portfolio to invest per trade (default: 10%)')
    parser.add_argument('--strategy', type=str, required=True, help='Name of the strategy to optimize (must exist in strategies file)')
    parser.add_argument('--optparams', type=str, default='', help="Comma-separated optimization parameters in the format 'param:min:max,param2:min2:max2'.")
    
    args = parser.parse_args()
    main(args)