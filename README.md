# Trading Strategy Dashboard

A complete system for backtesting trading strategies with candlestick pattern recognition, built with Python (FastAPI, Backtrader) and Next.js.

## Features

- Identify and backtest various candlestick patterns (Doji, Hammer, Engulfing, etc.)
- Configure trading parameters (stop loss, take profit)
- Visualize backtest results with performance charts
- Dark theme UI with pastel red/green color scheme

## Project Structure

- `app2/src/`: Backend trading engine and API
  - `candlestick_patterns.py`: Candlestick pattern detection indicators
  - `candlestick_strategy.py`: Backtrader strategy using candlestick patterns
  - `api.py`: FastAPI endpoints for backtesting
  - `tests/`: Unit and integration tests
  
- `app2/trade-strategy-dashboard/`: Frontend React application
  - Built with Next.js and shadcn/ui components
  - Dark theme with pastel red/green for trading visuals

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
   ```
   cd app2/src
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env` file:
   ```
   APCA_API_KEY_ID=your_alpaca_api_key
   APCA_API_SECRET_KEY=your_alpaca_secret_key
   APCA_API_BASE_URL=https://paper-api.alpaca.markets/v2
   ```

3. Run the FastAPI server:
   ```
   cd app2/src
   ./run_api.sh
   ```
   The server will run on port 8765 by default.

### Frontend Setup

1. Install Node.js dependencies:
   ```
   cd app2/trade-strategy-dashboard
   npm install
   ```

2. Configure environment variables in `.env.local` file:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8765
   ```

3. Run the Next.js development server:
   ```
   npm run dev
   ```

4. Access the UI at `http://localhost:3000`

## Testing

The project includes a comprehensive test suite that covers:

1. **API Tests**: Test the FastAPI backend endpoints
2. **Strategy Tests**: Test the trading strategies (SMA Cross, Bollinger Bands, RSI+MACD)
3. **Candlestick Tests**: Test the candlestick pattern detection and strategy
4. **Integration Tests**: Test the frontend-backend connectivity

To run the tests:

```bash
cd app2/src
./run_tests.sh
```

You can also run specific test types:

```bash
# Run API tests only
./run_tests.sh -t api

# Run strategy tests only
./run_tests.sh -t strategy

# Run candlestick tests only
./run_tests.sh -t candlestick

# Run integration tests only (requires both backend and frontend to be running)
./run_tests.sh -t integration

# Run with verbose output
./run_tests.sh -v

# Skip integration tests
./run_tests.sh -s
```

### Testing Requirements

- For unit tests: `pytest`
- For integration tests: Both the backend (port 8765) and frontend (port 3000) servers must be running

## Candlestick Patterns Supported

1. **Doji**: Indicates market indecision, with open and close prices nearly equal
2. **Hammer**: Bullish reversal pattern with a small body at the top and a long lower shadow
3. **Shooting Star**: Bearish reversal pattern with a small body at the bottom and a long upper shadow
4. **Engulfing**: A larger candle completely engulfing the previous one
5. **Morning Star**: Bullish reversal pattern consisting of three candles
6. **Evening Star**: Bearish reversal pattern consisting of three candles
7. **Three White Soldiers**: Three consecutive bullish candles indicating a strong uptrend
8. **Three Black Crows**: Three consecutive bearish candles indicating a strong downtrend

## Usage

1. Select a ticker symbol and date range
2. Choose one or more candlestick patterns to test
3. Configure trading parameters (stop loss, take profit)
4. Run the backtest
5. View the results and performance charts

## License

This project is licensed under the ISC License.