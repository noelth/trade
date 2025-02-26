# Trading Strategies

This directory contains the implementation of various trading strategies using the Backtrader library. The following strategies are available:

## 1. SmaCross

A simple moving average crossover strategy.

**Parameters:**
- `pfast` (int): Fast SMA period (default: 50)
- `pslow` (int): Slow SMA period (default: 200)
- `take_profit` (float): Take profit percentage (default: 0.0, disabled)

## 2. BollingerBreakoutStrategy

A strategy based on Bollinger Bands.

**Parameters:**
- `period` (int): Bollinger Bands period (default: 20)
- `devfactor` (float): Bollinger Bands deviation factor (default: 2.0)
- `stop_loss` (float): Stop loss percentage (default: 0.0, disabled)
- `take_profit` (float): Take profit percentage (default: 0.0, disabled)

## 3. RsiMacdStrategy

A strategy that uses the RSI and MACD indicators.

**Parameters:**
- `rsi_period` (int): Period for the RSI indicator (default: 14)
- `rsi_oversold` (int): Buy signal threshold for RSI (default: 30)
- `rsi_overbought` (int): Sell signal threshold for RSI (default: 70)
- `macd_fast` (int): Fast EMA for MACD (default: 12)
- `macd_slow` (int): Slow EMA for MACD (default: 26)
- `macd_signal` (int): Signal period for MACD (default: 9)
- `stop_loss` (float): Stop loss percentage (default: 0.05)
- `take_profit` (float): Take profit percentage (default: 0.0, disabled)

## 4. PivotLine

A custom indicator that plots a horizontal line at a specified price level from a given bar index.

**Parameters:**
- `pivot_value` (float): Price level for the line
- `start_bar` (int): Bar index from which to start plotting the line

## 5. HighVolPivotsStrategy

A strategy that detects pivot highs and lows occurring alongside high trading volume.

**Parameters:**
- `left_bars` (int): Number of bars to the left for pivot detection (default: 15)
- `right_bars` (int): Number of bars to the right for pivot detection (default: 1)
- `filter_vol` (float): Normalized volume threshold (0-6, default: ~5.6)
- `lookback` (int): Number of bars for rolling volume percentile calculation (default: 300)
- `percentile_rank` (float): Percentile used for "high volume" detection (default: 95.0)
- `show_levels` (bool): If True, a PivotLine is added to the chart at detected pivot points (default: True)
- `step` (float): Parameter for adjusting marker sizes (default: 0.6)

# TestStrat1 Strategy

## Description
The `TestStrat1` strategy is designed for a 15-minute timeframe, combining multiple indicators to trigger trade entries and exits. It uses Bollinger Bands, Simple Moving Averages (SMA), and Average True Range (ATR) to make trading decisions.

## Buy Condition
- A buy signal is generated when the closing price crosses below the lower Bollinger Band **and** the short SMA is above the long SMA, indicating an uptrend.

## Sell Condition
- A sell signal is generated when the closing price crosses above the upper Bollinger Band **and** the short SMA is below the long SMA, indicating a downtrend.

## Parameters
- **bb_period**: The period for the Bollinger Bands (default: 20).
- **bb_dev**: The deviation factor for the Bollinger Bands (default: 2.0).
- **sma_short_period**: The short SMA period (default: 100).
- **sma_long_period**: The long SMA period (default: 200).
- **atr_period**: The period for calculating the ATR (default: 14).
- **atr_multiplier**: The multiplier for the ATR to determine exit levels (default: 2.0).
- **basic_stop_pct**: The basic stop-loss percentage (default: 0.025).

## Example Usage
```bash
python main.py \
  --ticker AAPL \
  --start 2020-01-01 \
  --end 2023-01-01 \
  --timeframe 1D \
  --principal 10000 \
  --commission 0.0003 \
  --percent 20 \
  --strategy TestStrat1 \
  --bb-period 20 \
  --bb-dev 2.0 \
  --sma-short-period 100 \
  --sma-long-period 200 \
  --ts1-atr-period 14 \
  --ts1-atr-multiplier 2.0 \
  --basic-stop-pct 0.025
```

# BollingerBreakoutStrategy

## Description
The `BollingerBreakoutStrategy` is based on Bollinger Bands, which are used to identify overbought and oversold conditions in the market. The strategy aims to capture price movements when the price breaks out of the Bollinger Bands.

## Buy Condition
- A buy signal is generated when the closing price crosses above the upper Bollinger Band.

## Sell Condition
- A sell signal is generated when the closing price crosses below the lower Bollinger Band.

## Parameters
- **period**: The period for the Bollinger Bands (default: 20).
- **devfactor**: The deviation factor for the Bollinger Bands (default: 2.0).
- **stop_loss**: The stop loss percentage (default: 0.0, disabled).
- **take_profit**: The take profit percentage (default: 0.0, disabled).

## Example Usage
```bash
python main.py \
  --ticker AAPL \
  --start 2020-01-01 \
  --end 2023-01-01 \
  --timeframe 1D \
  --principal 10000 \
  --commission 0.0003 \
  --percent 20 \
  --strategy bbbreak \
  --bbbreak-bb-period 20 \
  --bbbreak-bb-dev 2.0 \
  --bbbreak-stop-loss 0.05 \
  --bbbreak-take-profit 0.10
```