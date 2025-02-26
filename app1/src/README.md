# Trading Strategy Backtester

This project allows you to backtest various trading strategies using historical data from the Alpaca API and the Backtrader framework.

## Run Command

To run the backtest, use the following command:

```bash
python src/main.py --strategy <strategy_name> --ticker <ticker_symbol> --start <start_date> --end <end_date> --granularity <granularity> --principal <initial_capital> --fee <trading_fee> --take_profit <take_profit_percentage>
```

### Parameters

- `--strategy`: The name of the strategy to use. Available strategies:
  - `sma`: Simple Moving Average Crossover Strategy
  - `rsimacd`: RSI and MACD Strategy
  - `bbbreak`: Bollinger Bands Breakout Strategy

- `--ticker`: The ticker symbol for the asset you want to backtest (e.g., `AAPL`, `TSLA`).

- `--start`: The start date for the backtest in `YYYY-MM-DD` format.

- `--end`: The end date for the backtest in `YYYY-MM-DD` format.

- `--granularity`: The data granularity. Options include:
  - `day`: Daily data
  - `hour`: Hourly data
  - `5min`: 5-minute data
  - `30min`: 30-minute data

- `--principal`: The initial capital for the backtest (default is `1000.0`).

- `--fee`: The trading fee as a fraction (default is `0.003` for 0.3%).

- `--take_profit`: The take profit margin as a fraction (default is `0.0`, meaning disabled).

## Strategy Quickrun

Here are example commands to quickly run each strategy:

### 1. Simple Moving Average Crossover (SmaCross)
```bash
python main.py --strategy sma --ticker MSFT --start 2020-01-01 --end 2024-10-01 --granularity day --principal 1000 --fee 0.003 --take_profit 0
```

### 2. RSI and MACD Strategy (RsiMacdStrategy)
```bash
python main.py --strategy rsimacd --ticker TSLA --start 2020-01-01 --end 2024-10-01 --granularity day --principal 1000 --fee 0.003 --take_profit 0
```

### 3. Bollinger Bands Breakout Strategy (BollingerBreakoutStrategy)
```bash
python main.py --strategy bbbreak --ticker MSFT --start 2020-01-01 --end 2024-10-01 --granularity day --principal 1000 --fee 0.003 --take_profit 0
```

## Strategies

### 1. Simple Moving Average Crossover (SmaCross)
- **Parameters**:
  - `pfast`: Fast SMA period (default is `50`).
  - `pslow`: Slow SMA period (default is `200`).
  - `take_profit`: Take profit percentage (default is `0.0`).

### 2. RSI and MACD Strategy (RsiMacdStrategy)
- **Parameters**:
  - `rsi_period`: Period for the RSI indicator (default is `14`).
  - `rsi_oversold`: Buy signal threshold for RSI (default is `30`).
  - `rsi_overbought`: Sell signal threshold for RSI (default is `70`).
  - `macd_fast`: Fast EMA for MACD (default is `12`).
  - `macd_slow`: Slow EMA for MACD (default is `26`).
  - `macd_signal`: Signal period for MACD (default is `9`).
  - `stop_loss`: Stop loss percentage (default is `0.05` for 5%).
  - `take_profit`: Take profit percentage (default is `0.0`).

### 3. Bollinger Bands Breakout Strategy (BollingerBreakoutStrategy)
- **Parameters**:
  - `period`: Bollinger Bands period (default is `20`).
  - `devfactor`: Bollinger Bands deviation factor (default is `2.0`).
  - `stop_loss`: Stop loss percentage (default is `0.0`).
  - `take_profit`: Take profit percentage (default is `0.0`).

## Requirements

Make sure to install the required packages listed in `requirements.txt`:

```bash
pip install -r src/requirements.txt
```

## License

This project is licensed under the MIT License.
