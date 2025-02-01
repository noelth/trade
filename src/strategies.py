import backtrader as bt

class SmaCross(bt.Strategy):
    params = dict(
        pfast=10,         # Fast SMA period
        pslow=30,         # Slow SMA period
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

        # Not in the market
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            # Record the entry price if not already recorded
            if self.entry_price is None:
                self.entry_price = self.position.price
            # Check take-profit if set
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
                return
            # Exit condition from crossover turning negative
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

class RsiMacdStrategy(bt.Strategy):
    params = dict(
        rsi_period=14,         # Period for RSI
        rsi_oversold=30,       # RSI oversold threshold (buy trigger)
        rsi_overbought=70,     # RSI overbought threshold (sell trigger)
        macd_fast=12,          # Fast EMA for MACD
        macd_slow=26,          # Slow EMA for MACD
        macd_signal=9,         # Signal period for MACD
        stop_loss=0.05,        # Stop loss margin (5% default)
        take_profit=0.0        # Take profit margin (0 means disabled by default)
    )

    def __init__(self):
        # Initialize the RSI indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        # Initialize the MACD indicator
        self.macd = bt.indicators.MACD(self.data.close,
                                       period_me1=self.p.macd_fast,
                                       period_me2=self.p.macd_slow,
                                       period_signal=self.p.macd_signal)
        self.order = None
        self.entry_price = None

    def next(self):
        # Wait for any pending order to complete
        if self.order:
            return

        # Not in the market: Check if conditions for a buy are met.
        if not self.position:
            if self.rsi[0] < self.p.rsi_oversold and self.macd.macd[0] > self.macd.signal[0]:
                self.order = self.buy()
        else:
            # Record entry price if not already set
            if self.entry_price is None:
                self.entry_price = self.position.price

            # Check if take profit is enabled and met
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
                return

            # Check if stop loss is hit
            if self.entry_price and self.data.close[0] < self.entry_price * (1 - self.p.stop_loss):
                self.order = self.close()
                return

            # Exit if RSI is overbought or MACD signal turns bearish
            if self.rsi[0] > self.p.rsi_overbought or self.macd.macd[0] < self.macd.signal[0]:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # Do nothing for now

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

class BollingerBreakoutStrategy(bt.Strategy):
    params = dict(
        period=20,         # Bollinger Bands period
        devfactor=2.0,     # Bollinger Bands deviation factor
        stop_loss=0.05,    # 5% stop loss
        take_profit=0.0    # Take profit percentage (0 means disabled)
    )

    def __init__(self):
        # Calculate Bollinger Bands on the close price
        self.bbands = bt.indicators.BollingerBands(self.data.close,
                                                    period=self.p.period,
                                                    devfactor=self.p.devfactor)
        # Disable plotting for Bollinger Bands (optional)
        self.bbands.plotinfo.plot = False

        # Create crossover indicators:
        # Cross up: Price crossing above the upper band triggers a buy signal.
        self.crossup = bt.indicators.CrossOver(self.data.close, self.bbands.top)
        # Cross down: Price crossing below the middle band triggers an exit.
        self.crossdown = bt.indicators.CrossOver(self.data.close, self.bbands.mid)
        # Disable plotting for the crossover indicators
        self.crossup.plotinfo.plot = False
        self.crossdown.plotinfo.plot = False

        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # Buy if the price crosses above the upper Bollinger band
            if self.crossup > 0:
                self.order = self.buy()
        else:
            # Record entry price if not already set
            if self.entry_price is None:
                self.entry_price = self.position.price
            # Check take profit condition (if enabled)
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
                return
            # Check stop-loss condition
            if self.entry_price and self.data.close[0] < self.entry_price * (1 - self.p.stop_loss):
                self.order = self.close()
                return
            # Exit when price crosses below the middle Bollinger band
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