# strategies.py
import backtrader as bt

class SmaCross(bt.Strategy):
    params = dict(
        pfast=10,   # fast SMA period
        pslow=30    # slow SMA period
    )

    def __init__(self):
        sma_fast = bt.indicators.SMA(self.data.close, period=self.p.pfast)
        sma_slow = bt.indicators.SMA(self.data.close, period=self.p.pslow)
        self.crossover = bt.indicators.CrossOver(sma_fast, sma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("BUY EXECUTED, Price: %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, Price: %.2f" % order.executed.price)

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")


class RsiMacdStrategy(bt.Strategy):
    params = dict(
        rsi_period=7,
        rsi_oversold=40,
        rsi_overbought=60,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        stop_loss=0.03  # 3% stop loss
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
        # Debug logging
        self.log(f"RSI: {self.rsi[0]:.2f}, MACD: {self.macd.macd[0]:.2f}, Signal: {self.macd.signal[0]:.2f}")
        if self.order:
            return
        if not self.position:
            if self.rsi[0] < self.p.rsi_oversold and self.macd.macd[0] > self.macd.signal[0]:
                self.order = self.buy()
        else:
            # Check stop-loss condition:
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
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}")
                self.entry_price = None
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")


class BollingerBreakoutStrategy(bt.Strategy):
    params = dict(
        period=20,      # Bollinger Bands period
        devfactor=2.0,  # Bollinger Bands deviation factor
        stop_loss=0.05  # 5% stop loss
    )

    def __init__(self):
        # Calculate Bollinger Bands
        self.bbands = bt.indicators.BollingerBands(self.data.close,
                                                    period=self.p.period,
                                                    devfactor=self.p.devfactor)
        # Create crossovers:
        # Buy signal: price crosses above the upper band
        self.crossup = bt.indicators.CrossOver(self.data.close, self.bbands.top)
        # Sell signal: price crosses below the middle band
        self.crossdown = bt.indicators.CrossOver(self.data.close, self.bbands.mid)
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossup > 0:
                self.order = self.buy()
        else:
            # Stop loss check:
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