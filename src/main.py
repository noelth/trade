# main.py
import os
from datetime import datetime, timedelta
import pytz
import alpaca_trade_api as tradeapi
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve Alpaca API credentials
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

if not API_KEY or not API_SECRET:
    raise Exception("API credentials not set. Please check your .env file for APCA_API_KEY_ID and APCA_API_SECRET_KEY.")

# Import strategy classes from strategies.py
from strategies import SmaCross

# Map strategy names to classes for easy selection
STRATEGIES = {
    'sma': SmaCross,
    # You can add additional strategies here
}

def fetch_historical_data(ticker, start, end, timeframe, api):
    """
    Fetch historical data for a given ticker from Alpaca and return a Pandas DataFrame.
    This function handles both MultiIndex (when multiple tickers are returned) and simple DatetimeIndex.
    """
    try:
        # Request bars with adjustments for splits/dividends
        bars = api.get_bars(ticker, timeframe, start.isoformat(), end.isoformat(), adjustment='all').df
        if isinstance(bars.index, pd.MultiIndex):
            if ticker in bars.index.levels[0]:
                df = bars.xs(ticker, level=0)
            else:
                print(f"No data returned for {ticker} in multi-index format.")
                return pd.DataFrame()
        else:
            df = bars
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def run_backtest(strategy_class, ticker, backtest_start, backtest_end, granularity, principal, fee):
    # Initialize Alpaca API connection (v2)
    api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

    # Map granularity to Alpaca's timeframe and determine compression if needed
    tf_mapping = {
        'day': tradeapi.TimeFrame.Day,
        'hour': tradeapi.TimeFrame.Hour,
        '5min': tradeapi.TimeFrame.Minute,
        '30min': tradeapi.TimeFrame.Minute,
    }
    timeframe = tf_mapping.get(granularity.lower(), tradeapi.TimeFrame.Day)
    compression = 1
    if granularity.lower() == '5min':
        compression = 5
    elif granularity.lower() == '30min':
        compression = 30

    tz = pytz.utc
    start_date = tz.localize(datetime.strptime(backtest_start, '%Y-%m-%d'))
    end_date   = tz.localize(datetime.strptime(backtest_end, '%Y-%m-%d'))

    print(f"Fetching historical data for {ticker} from {start_date.date()} to {end_date.date()}...")
    df = fetch_historical_data(ticker, start_date, end_date, timeframe, api)
    if df.empty:
        print(f"No data available for {ticker}. Exiting backtest.")
        return

    # Define a custom PandasData feed to support compression (for minute data)
    class CustomPandasData(bt.feeds.PandasData):
        params = (
            ('compression', compression),
            ('datetime', None),
            ('open', 'open'),
            ('high', 'high'),
            ('low', 'low'),
            ('close', 'close'),
            ('volume', 'volume'),
            ('openinterest', -1),
        )

    data = CustomPandasData(dataname=df)

    # Set up Cerebro engine
    cerebro = bt.Cerebro()
    cerebro.adddata(data, name=ticker)
    cerebro.addstrategy(strategy_class)
    cerebro.broker.setcash(principal)
    cerebro.broker.setcommission(commission=fee)

    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    dollar_change = final_value - principal
    pct_change = (dollar_change / principal) * 100

    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Dollar Change: ${dollar_change:.2f}")
    print(f"Percentage Change: {pct_change:.2f}%")

    # Plot the result with candlestick style; buy/sell markers are added automatically
    cerebro.plot(style='candlestick')

def main():
    parser = argparse.ArgumentParser(description="Backtest a trading strategy using Alpaca data and Backtrader.")
    parser.add_argument("--strategy", type=str, default="sma", help="Strategy to use (e.g., 'sma')")
    parser.add_argument("--ticker", type=str, required=True, help="Ticker symbol for backtesting")
    parser.add_argument("--start", type=str, required=True, help="Backtest start date in YYYY-MM-DD format")
    parser.add_argument("--end", type=str, required=True, help="Backtest end date in YYYY-MM-DD format")
    parser.add_argument("--granularity", type=str, default="day", help="Data granularity (day, hour, 5min, 30min)")
    parser.add_argument("--principal", type=float, default=100000.0, help="Starting principal amount")
    parser.add_argument("--fee", type=float, default=0.001, help="Trading fee as a fraction (e.g., 0.001 for 0.1%)")
    args = parser.parse_args()

    strategy_class = STRATEGIES.get(args.strategy.lower())
    if strategy_class is None:
        print(f"Strategy '{args.strategy}' not found. Available strategies: {list(STRATEGIES.keys())}")
        return

    run_backtest(strategy_class, args.ticker, args.start, args.end, args.granularity, args.principal, args.fee)

if __name__ == "__main__":
    main()