import backtrader as bt
import numpy as np
from collections import deque

# -----------------------------
# SmaCross Strategy
# -----------------------------
class SmaCross(bt.Strategy):
    params = dict(
        sma_fast_period=50,         # Fast SMA period
        sma_slow_period=200,        # Slow SMA period
        take_profit=0.0             # Take profit percentage (0 means disabled)
    )

    def __init__(self):
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.p.sma_fast_period)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.p.sma_slow_period)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        self.entry_price = None
        self.order = None
        self.num_trades = 0
        self.num_profitable_trades = 0

    def next(self):
        if self.order:
            return

        # Log the current values of the SMAs and crossover
        self.log(f"SMA Fast: {self.sma_fast[0]:.2f}, SMA Slow: {self.sma_slow[0]:.2f}, Crossover: {self.crossover[0]}")

        if not self.position:
            if self.crossover > 0:  # Buy signal
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.log(f"BUY EXECUTED, Price: {self.entry_price:.2f}")
        else:
            if self.crossover < 0:  # Sell signal
                self.order = self.close()
                self.log(f"SELL EXECUTED, Price: {self.data.close[0]:.2f}")
                # Track the trade
                self.num_trades += 1
                if self.data.close[0] > self.entry_price:  # Check if the trade was profitable
                    self.num_profitable_trades += 1

    def log(self, txt):
        dt = self.data.datetime.date(0)
        print(f"{dt.isoformat()} - {txt}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"Buy order executed at {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"Sell order executed at {order.executed.price:.2f}")
        self.order = None

    def stop(self):
        # Log the results at the end of the strategy
        self.log(f"Total Trades: {self.num_trades}, Profitable Trades: {self.num_profitable_trades}")


# -----------------------------
# BollingerBreakoutStrategy
# -----------------------------

class BollingerBreakoutStrategy(bt.Strategy):
    params = dict(
        period=20,         # Bollinger Bands period
        devfactor=2.0,     # Bollinger Bands deviation factor
        stop_loss=0.00,    # Stop loss percentage (0 means disabled)
        take_profit=0.0     # Take profit percentage (0 means disabled)
    )

    def __init__(self):
        self.bbands = bt.indicators.BollingerBands(self.data.close,
                                                    period=self.p.period,
                                                    devfactor=self.p.devfactor)
        self.bbands.plotinfo.plot = False
        self.crossup = bt.indicators.CrossOver(self.data.close, self.bbands.top)
        self.crossdown = bt.indicators.CrossOver(self.data.close, self.bbands.mid)
        self.crossup.plotinfo.plot = False
        self.crossdown.plotinfo.plot = False
        self.order = None
        self.entry_price = None
        self.num_trades = 0
        self.num_profitable_trades = 0

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.crossup > 0:  # Buy signal
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.log(f"BUY EXECUTED, Price: {self.entry_price:.2f}")
        else:
            if self.entry_price is None:
                self.entry_price = self.position.price
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
                self.log(f"SELL EXECUTED, Price: {self.data.close[0]:.2f}")
                self.num_trades += 1
                if self.data.close[0] > self.entry_price:  # Check if the trade was profitable
                    self.num_profitable_trades += 1
                return
            if self.entry_price and self.data.close[0] < self.entry_price * (1 - self.p.stop_loss):
                self.order = self.close()
                self.log(f"SELL EXECUTED, Price: {self.data.close[0]:.2f}")
                self.num_trades += 1
                if self.data.close[0] > self.entry_price:  # Check if the trade was profitable
                    self.num_profitable_trades += 1
                return
            if self.crossdown < 0:  # Sell signal
                self.order = self.close()
                self.log(f"SELL EXECUTED, Price: {self.data.close[0]:.2f}")
                self.num_trades += 1
                if self.data.close[0] > self.entry_price:  # Check if the trade was profitable
                    self.num_profitable_trades += 1

    def log(self, txt):
        dt = self.data.datetime.date(0)
        print(f"{dt.isoformat()} - {txt}")

    def stop(self):
        # Log the results at the end of the strategy
        self.log(f"Total Trades: {self.num_trades}, Profitable Trades: {self.num_profitable_trades}")


# -----------------------------
# RsiMacdStrategy
# -----------------------------
class RsiMacdStrategy(bt.Strategy):
    params = dict(
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        stop_loss=0.05,
        take_profit=0.0
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.macd = bt.indicators.MACD(self.data.close,
                                       period_me1=self.p.macd_fast,
                                       period_me2=self.p.macd_slow,
                                       period_signal=self.p.macd_signal)
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.rsi[0] < self.p.rsi_oversold and self.macd.macd[0] > self.macd.signal[0]:
                self.order = self.buy()
        else:
            if self.entry_price is None:
                self.entry_price = self.position.price
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
                return
            if self.entry_price and self.data.close[0] < self.entry_price * (1 - self.p.stop_loss):
                self.order = self.close()
                return
            if self.rsi[0] > self.p.rsi_overbought or self.macd.macd[0] < self.macd.signal[0]:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log("BUY EXECUTED, Price: %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, Price: %.2f" % order.executed.price)
                self.entry_price = None
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")


# -----------------------------
# TestStrat1
# -----------------------------
class TestStrat1(bt.Strategy):
    """
    TestStrat1 is designed for a 15-minute timeframe, combining multiple indicators to
    trigger trade entries and exits. It uses:
    
      - Bollinger Bands:
          * Middle Band: A moving average (default period: 20).
          * Upper Band: Middle Band + (devfactor × standard deviation).
          * Lower Band: Middle Band - (devfactor × standard deviation).
          Signals:
            - Price touching or crossing below the lower band indicates oversold conditions (potential long entry).
            - Price touching or crossing above the upper band indicates overbought conditions (potential short entry).

      - Simple Moving Averages (SMA):
          * SMA1 (default: 100-period): Medium-term trend indicator.
          * SMA2 (default: 200-period): Long-term trend indicator.
          Trend Confirmation:
            - If SMA1 > SMA2, the market is in an uptrend.
            - If SMA1 < SMA2, the market is in a downtrend.

      - Average True Range (ATR):
          * Measures market volatility over a specified period (default: 14-period).
          * Used to set dynamic stop-loss levels with a multiplier (default: 2.0).

      - Basic Stop-loss:
          * A fixed stop-loss at 2.5% (by default) below (or above for shorts) the entry price to control risk.

    Parameters (modifiable at runtime):
      - bb_period (default: 20)
      - bb_dev (default: 2.0)
      - sma_short_period (default: 100)
      - sma_long_period (default: 200)
      - atr_period (default: 14)
      - atr_multiplier (default: 2.0)
      - basic_stop_pct (default: 0.025)
      - sma_crossover_bars (default: 3)
    """
    params = (
        ('bb_period', 20),
        ('bb_dev', 2.0),
        ('sma_short_period', 100),
        ('sma_long_period', 200),
        ('atr_period', 14),
        ('atr_multiplier', 2.0),
        ('basic_stop_pct', 0.025),
        ('sma_crossover_bars', 3),
    )

    def __init__(self):
        self.bbands = bt.indicators.BollingerBands(self.data.close,
                                                    period=self.p.bb_period,
                                                    devfactor=self.p.bb_dev)
        self.sma_short = bt.indicators.SMA(self.data.close, period=self.p.sma_short_period)
        self.sma_long = bt.indicators.SMA(self.data.close, period=self.p.sma_long_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.order = None
        self.entry_price = None
        self.num_trades = 0
        self.num_profitable_trades = 0
        self.sma_crossed_bars = 0

    def next(self):
        if self.order:
            return

        if self.sma_short[0] > self.sma_long[0]:
            self.sma_crossed_bars += 1
        else:
            self.sma_crossed_bars = 0

        if not self.position:
            if self.data.close[0] < self.bbands.lines.bot[0] and self.sma_crossed_bars >= self.p.sma_crossover_bars:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.log(f"BUY EXECUTED, Price: {self.entry_price:.2f}")
        else:
            if self.data.close[0] > self.bbands.lines.top[0] and self.sma_crossed_bars < self.p.sma_crossover_bars:
                self.order = self.close()
                self.log(f"SELL EXECUTED, Price: {self.data.close[0]:.2f}")
                # Track the trade
                self.num_trades += 1
                if self.data.close[0] > self.entry_price:  # Check if the trade was profitable
                    self.num_profitable_trades += 1

    def log(self, txt):
        dt = self.data.datetime.date(0)
        print(f"{dt.isoformat()} - {txt}")

    def stop(self):
        # Log the results at the end of the strategy
        self.log(f"Total Trades: {self.num_trades}, Profitable Trades: {self.num_profitable_trades}")


# -----------------------------
# New Custom Indicator: PivotLine
# -----------------------------
class PivotLine(bt.Indicator):
    lines = ('pivot',)
    params = (
        ('pivot_value', 0.0),
        ('start_bar', 0),
    )
    plotinfo = dict(subplot=False)  # Plot on main chart
    plotlines = dict(pivot=dict(color='red', linestyle='--', linewidth=2))

    def __init__(self):
        pass

    def next(self):
        if len(self.data) - 1 >= self.p.start_bar:
            self.lines.pivot[0] = self.p.pivot_value
        else:
            self.lines.pivot[0] = float('nan')


# -----------------------------
# New Strategy: HighVolPivotsStrategy
# -----------------------------
class HighVolPivotsStrategy(bt.Strategy):
    """
    HighVolPivotsStrategy detects pivot highs and pivot lows occurring alongside
    high trading volume. Inspired by PineScript logic, it:

      - Uses user-defined left/right bars to determine pivot points.
      - Calculates a rolling volume percentile (default 95th over a lookback period) to normalize volume.
      - Logs pivot points when the normalized volume exceeds a threshold.
      - When a pivot is detected, adds a PivotLine indicator that draws a horizontal line
        from that pivot to the right on the main chart, indicating potential support/resistance.

    Parameters (modifiable at runtime):
      - left_bars (int): Number of bars to the left for pivot detection (default: 15).
      - right_bars (int): Number of bars to the right for pivot detection (default: 1).
      - filter_vol (float): Normalized volume threshold (default: 5.6).
      - lookback (int): Number of bars for rolling volume percentile calculation (default: 300).
      - percentile_rank (float): Percentile used for volume detection (default: 95.0).
      - show_levels (bool): If True, adds a PivotLine on the chart at detected pivot points (default: True).
      - step (float): For future customization of marker size (default: 0.6).
    """
    params = (
        ('left_bars', 15),
        ('right_bars', 1),
        ('filter_vol', 5.6),
        ('lookback', 300),
        ('percentile_rank', 95.0),
        ('show_levels', True),
        ('step', 0.6),
    )

    def __init__(self):
        self.volume_window = deque(maxlen=self.p.lookback)
        self.pivot_points = []
        self.pivot_lines = []

    def next(self):
        current_vol = self.data.volume[0]
        self.volume_window.append(current_vol)

        if len(self.data) <= (self.p.left_bars + self.p.right_bars):
            return

        pivot_index = -self.p.right_bars

        if len(self.volume_window) < self.p.lookback:
            return

        vol_array = np.array(self.volume_window)
        reference_vol = np.percentile(vol_array, self.p.percentile_rank)
        if reference_vol == 0:
            return
        norm_vol = (current_vol / reference_vol) * 5

        pivot_price = self.data.close[pivot_index]
        left_slice = self.data.close.get(ago=self.p.right_bars, size=self.p.left_bars)
        right_slice = self.data.close.get(ago=0, size=self.p.right_bars)
        if not left_slice or not right_slice:
            return

        left_values = list(left_slice)
        right_values = list(right_slice)

        is_pivot_high = all(pivot_price > lv for lv in left_values) and \
                        all(pivot_price >= rv for rv in right_values)
        is_pivot_low  = all(pivot_price < lv for lv in left_values) and \
                        all(pivot_price <= rv for rv in right_values)
        volume_is_high = (norm_vol > self.p.filter_vol)

        if volume_is_high:
            pivot_bar = len(self.data) - self.p.right_bars
            if is_pivot_high:
                self.log(f"Pivot HIGH at bar {pivot_bar} Price={pivot_price:.2f}, norm_vol={norm_vol:.2f}")
                self.pivot_points.append(('HIGH', self.data.datetime.datetime(ago=self.p.right_bars), pivot_price))
                if self.p.show_levels:
                    pline = PivotLine(self.data, pivot_value=pivot_price, start_bar=pivot_bar)
                    self.pivot_lines.append(pline)
                    self.plot_pivot_line(pline)

            elif is_pivot_low:
                self.log(f"Pivot LOW at bar {pivot_bar} Price={pivot_price:.2f}, norm_vol={norm_vol:.2f}")
                self.pivot_points.append(('LOW', self.data.datetime.datetime(ago=self.p.right_bars), pivot_price))
                if self.p.show_levels:
                    pline = PivotLine(self.data, pivot_value=pivot_price, start_bar=pivot_bar)
                    self.pivot_lines.append(pline)
                    self.plot_pivot_line(pline)

    def plot_pivot_line(self, pline):
        self.lines.pivot[0] = pline.pivot_value

    def log(self, txt):
        dt = self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} - {txt}")

# -----------------------------
# New Strategy: MarketStructureStrategy
# -----------------------------
class MarketStructureStrategy(bt.Strategy):
    """
    MarketStructureStrategy is a trend-following strategy that uses the Average True Range (ATR)
    indicator to determine entry and exit points. It aims to capture market trends while managing risk.

    The strategy works as follows:

    1. Entry:
       - If the current price breaks above the highest high of the last N bars (defined by the 'breakout_bars' parameter),
         and the breakout is greater than a multiple of the ATR (defined by the 'atr_multiplier' parameter),
         a long position is initiated.
       - If the current price breaks below the lowest low of the last N bars, and the breakout is greater than
         a multiple of the ATR, a short position is initiated.

    2. Exit:
       - The position is exited when the price moves against the trade by a multiple of the ATR.

    Parameters (modifiable at runtime):
      - atr_period (int): The period for calculating the ATR indicator (default: 20).
      - breakout_bars (int): The number of bars to consider for breakout detection (default: 10).
      - atr_multiplier (float): The multiplier for the ATR to determine entry and exit levels (default: 2.0).

    """
    params = (
        ('atr_period', 20),
        ('breakout_bars', 10),
        ('atr_multiplier', 2.0),
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.highest_high = bt.indicators.Highest(self.data.high, period=self.p.breakout_bars)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=self.p.breakout_bars)
        self.entry_price = None
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # Check for long entry
            if self.data.high[0] > self.highest_high[0] and \
               self.data.high[0] - self.highest_high[0] > self.p.atr_multiplier * self.atr[0]:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.log(f"Long Entry at {self.entry_price:.2f}")

            # Check for short entry
            elif self.data.low[0] < self.lowest_low[0] and \
                 self.lowest_low[0] - self.data.low[0] > self.p.atr_multiplier * self.atr[0]:
                self.order = self.sell()
                self.entry_price = self.data.close[0]
                self.log(f"Short Entry at {self.entry_price:.2f}")

        else:
            # Exit long position
            if self.position.size > 0 and self.data.close[0] < self.entry_price - (self.p.atr_multiplier * self.atr[0]):
                self.order = self.close()
                self.log(f"Long Exit at {self.data.close[0]:.2f}")
                self.entry_price = None

            # Exit short position
            elif self.position.size < 0 and self.data.close[0] > self.entry_price + (self.p.atr_multiplier * self.atr[0]):
                self.order = self.close()
                self.log(f"Short Exit at {self.data.close[0]:.2f}")
                self.entry_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"Buy order executed at {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"Sell order executed at {order.executed.price:.2f}")
            self.order = None

    def log(self, txt):
        dt = self.data.datetime.date(0)
        print(f"{dt.isoformat()} - {txt}")

class CustomBuySell(bt.Observer):
    lines = ('buy', 'sell',)
    plotinfo = dict(subplot=False)  # Plot on the main chart

    def __init__(self):
        self.buy = []
        self.sell = []

    def next(self):
        if self._owner.order:
            if self._owner.order.isbuy():
                self.buy.append(self._owner.data.close[0])
                self.sell.append(float('nan'))  # No sell signal
            elif self._owner.order.issell():
                self.sell.append(self._owner.data.close[0])
                self.buy.append(float('nan'))  # No buy signal
        else:
            self.buy.append(float('nan'))
            self.sell.append(float('nan'))