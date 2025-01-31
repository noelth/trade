import os
from datetime import datetime, timedelta
import pytz
import alpaca_trade_api as tradeapi
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve Alpaca API credentials from environment variables
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

if not API_KEY or not API_SECRET:
    raise Exception("API credentials not set. Please check your .env file for APCA_API_KEY_ID and APCA_API_SECRET_KEY.")

def fetch_historical_data(ticker, start, end, timeframe, api):
    """
    Fetch historical data for a given ticker and return a Pandas DataFrame,
    adjusted for splits (and dividends) using the 'adjustment' parameter.
    """
    try:
        # Request data adjusted for splits and dividends:
        bars = api.get_bars(
            ticker,
            timeframe,
            start.isoformat(),
            end.isoformat(),
            adjustment='all'
        ).df
        if isinstance(bars.index, pd.MultiIndex):
            if ticker in bars.index.levels[0]:
                df = bars.xs(ticker, level=0)
            else:
                print(f"No data returned for {ticker} in the multi-index.")
                return pd.DataFrame()
        else:
            df = bars

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def plot_all_data(all_data):
    """
    Plot the closing prices for all tickers on a single chart with different colors and labels.
    """
    plt.figure(figsize=(12, 6))
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, (ticker, df) in enumerate(all_data.items()):
        if not df.empty:
            plt.plot(df.index, df['close'], label=ticker, color=colors[i % len(colors)])
    plt.xlabel('Date')
    plt.ylabel('Closing Price')
    plt.title('Historical Closing Prices for Selected Tickers')
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    # User-definable variables:
    tickers = ['PLTR','AAPL','GOOGL']  # List of tickers to fetch data for
    chosen_timeframe = tradeapi.TimeFrame.Day  # Daily bars

    # Calculate date range: past 5 years up to one day ago (to avoid recent data restrictions)
    end_date = datetime.now(pytz.utc) - timedelta(days=1)
    start_date = end_date - timedelta(days=5 * 365)  # Approximate 5 years

    # Initialize the Alpaca API connection (v2)
    api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

    all_data = {}
    for ticker in tickers:
        print(f"Fetching historical data for {ticker} from {start_date.date()} to {end_date.date()}...")
        df = fetch_historical_data(ticker, start_date, end_date, chosen_timeframe, api)
        if not df.empty:
            print(f"Retrieved {len(df)} daily bars for {ticker}.")
            all_data[ticker] = df
            csv_filename = f"{ticker}_historical_{start_date.date()}_to_{end_date.date()}.csv"
            df.to_csv(csv_filename)
            print(f"Data for {ticker} saved to {csv_filename}.")
        else:
            print(f"No data available for {ticker}.")
    print("Finished fetching data for all tickers.")

    # Plot all ticker data in a single window
    plot_all_data(all_data)

if __name__ == "__main__":
    main()