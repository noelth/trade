import backtrader as bt
import numpy as np
from collections import deque

# -----------------------------
# Existing Strategy: SmaCross
# -----------------------------
class SmaCross(bt.Strategy):
    params = dict(
        pfast=50,         # Fast SMA period
        pslow=200,        # Slow SMA period
        take_profit=0.0   # Take profit percentage (0 means disabled)
    )

    def __init__(self):
        sma_fast = bt.indicators.SMA(self.data.close, period=self.p.pfast)
        sma_slow = bt.indicators.SMA(self.data.close, period=self.p.pslow)
        self.crossover = bt.indicators.CrossOver(sma_fast, sma_slow)
        # Disable plotting for the crossover indicator
        self.crossover.plotinfo.plot = False
        self.entry_price = None
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            if self.entry_price is None:
                self.entry_price = self.position.price
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
                return
            if self.crossover < 0:
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
# Existing Strategy: BollingerBreakoutStrategy
# -----------------------------
class BollingerBreakoutStrategy(bt.Strategy):
    params = dict(
        period=20,         # Bollinger Bands period
        devfactor=2.0,     # Bollinger Bands deviation factor
        stop_loss=0.00,    # Stop loss percentage (0 means disabled)
        take_profit=0.0    # Take profit percentage (0 means disabled)
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

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.crossup > 0:
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
            if self.crossdown < 0:
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
# Existing Strategy: RsiMacdStrategy
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
        # No additional calculation needed; we override next()
        pass

    def next(self):
        # If current bar index is >= start_bar, output pivot_value; otherwise, output NaN.
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
    high trading volume. Inspired by the PineScript logic, it:

      - Defines pivot highs/lows based on user-defined left/right bars.
      - Calculates a rolling percentile of volume (default 95th percentile over a specified lookback).
      - Logs pivot points if volume exceeds a certain 'filter_vol' threshold.
      - When a pivot is detected, a PivotLine indicator is added to plot a horizontal line from the pivot to the right,
        representing potential support/resistance levels.

    Parameters:
      - left_bars (int): Number of bars to the left for pivot detection (default: 15).
      - right_bars (int): Number of bars to the right for pivot detection (default: 1).
      - filter_vol (float): Normalized volume threshold (0-6, default: ~5.6).
      - lookback (int): Number of bars for rolling volume percentile calculation (default: 300).
      - percentile_rank (float): Percentile used for "high volume" detection (default: 95).
      - show_levels (bool): If True, a PivotLine is added to the chart at detected pivot points.
      - step (float): Parameter for adjusting marker sizes (default: 0.6; for future customization).
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
                msg = f"Pivot HIGH at bar {pivot_bar} Price={pivot_price:.2f}, norm_vol={norm_vol:.2f}"
                self.log(msg)
                self.pivot_points.append(('HIGH', self.data.datetime.datetime(ago=self.p.right_bars), pivot_price))
                if self.p.show_levels:
                    pline = PivotLine(self.data, pivot_value=pivot_price, start_bar=pivot_bar)
                    self.pivot_lines.append(pline)
            elif is_pivot_low:
                msg = f"Pivot LOW at bar {pivot_bar} Price={pivot_price:.2f}, norm_vol={norm_vol:.2f}"
                self.log(msg)
                self.pivot_points.append(('LOW', self.data.datetime.datetime(ago=self.p.right_bars), pivot_price))
                if self.p.show_levels:
                    pline = PivotLine(self.data, pivot_value=pivot_price, start_bar=pivot_bar)
                    self.pivot_lines.append(pline)

    def log(self, txt):
        dt = self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} - {txt}")