import backtrader as bt

class SmaCross(bt.Strategy):
    params = dict(
        pfast=10,         # Fast SMA period
        pslow=30,         # Slow SMA period
        take_profit=0.0,  # Take profit percentage (0 means disabled)
        stop_loss=0.05,   # Stop loss margin
        trailing_stop=0.03,# Trailing stop loss margin
        atr_period=14,    # ATR period for volatility based exit
        atr_multiplier=2.0 # ATR multiplier for profit taking
    )

    def __init__(self):
        # Initialize SMA indicators
        sma_fast = bt.indicators.SMA(self.data.close, period=self.p.pfast)
        sma_slow = bt.indicators.SMA(self.data.close, period=self.p.pslow)
        self.crossover = bt.indicators.CrossOver(sma_fast, sma_slow)
        # Disable plotting for the crossover indicator
        self.crossover.plotinfo.plot = False
        
        # Initialize ATR indicator with proper data feed
        self.atr = bt.indicators.ATR(self.data, period=int(self.p.atr_period))
        self.atr.plotinfo.plot = False  # Disable ATR plotting
        
        self.entry_price = None
        self.highest_price = None
        self.order = None

    def next(self):
        if self.order:
            return

        # Not in the market
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            # Record the entry price and highest price if not already recorded
            if self.entry_price is None:
                self.entry_price = self.position.price
                self.highest_price = self.position.price
            # Update highest price for trailing stop
            if self.data.close[0] > self.highest_price:
                self.highest_price = self.data.close[0]

            # Check take-profit if set
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"TAKE PROFIT EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return
            
            # Check ATR-based profit target (ensure ATR is valid)
            if self.p.atr_multiplier > 0 and len(self.atr) > self.p.atr_period and self.data.close[0] > self.entry_price + (self.atr[0] * self.p.atr_multiplier):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"ATR PROFIT EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return

            # Check trailing stop
            if self.data.close[0] < self.highest_price * (1 - self.p.trailing_stop):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"TRAILING STOP EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return

            # Check stop loss
            if self.data.close[0] < self.entry_price * (1 - self.p.stop_loss):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"STOP LOSS EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
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
                self.highest_price = order.executed.price
                self.log("BUY EXECUTED, Price: %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, Price: %.2f" % order.executed.price)
                self.entry_price = None
                self.highest_price = None
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
        take_profit=0.0,       # Take profit margin (0 means disabled by default)
        trailing_stop=0.03,    # Trailing stop loss margin
        atr_period=14,         # ATR period for volatility based exit
        atr_multiplier=2.0     # ATR multiplier for profit taking
    )

    def __init__(self):
        # Initialize the RSI indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        # Initialize the MACD indicator
        self.macd = bt.indicators.MACD(self.data.close,
                                       period_me1=self.p.macd_fast,
                                       period_me2=self.p.macd_slow,
                                       period_signal=self.p.macd_signal)
        # Initialize ATR indicator with proper data feed
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.atr.plotinfo.plot = False  # Disable ATR plotting
        
        self.order = None
        self.entry_price = None
        self.highest_price = None

    def next(self):
        # Wait for any pending order to complete
        if self.order:
            return

        # Not in the market: Check if conditions for a buy are met.
        if not self.position:
            if self.rsi[0] < self.p.rsi_oversold and self.macd.macd[0] > self.macd.signal[0]:
                self.order = self.buy()
        else:
            # Record entry price and highest price if not already set
            if self.entry_price is None:
                self.entry_price = self.position.price
                self.highest_price = self.position.price
            # Update highest price for trailing stop
            if self.data.close[0] > self.highest_price:
                self.highest_price = self.data.close[0]

            # Check if take profit is enabled and met
            if self.p.take_profit > 0 and self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"TAKE PROFIT EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return

            # Check ATR-based profit target (ensure ATR is valid)
            if self.p.atr_multiplier > 0 and len(self.atr) > self.p.atr_period and self.data.close[0] > self.entry_price + (self.atr[0] * self.p.atr_multiplier):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"ATR PROFIT EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return

            # Check trailing stop
            if self.data.close[0] < self.highest_price * (1 - self.p.trailing_stop):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"TRAILING STOP EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return

            # Check if stop loss is hit
            if self.entry_price and self.data.close[0] < self.entry_price * (1 - self.p.stop_loss):
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"STOP LOSS EXIT - Change: ${change:.2f} ({pct_change:.2f}%) [Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
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
                self.highest_price = order.executed.price
                self.log("BUY EXECUTED, Price: %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, Price: %.2f" % order.executed.price)
                self.entry_price = None
                self.highest_price = None
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")

class BollingerBreakoutStrategy(bt.Strategy):
    params = dict(
        period=20,                        # Bollinger Bands period
        devfactor=2.0,                    # Bollinger Bands deviation factor
        stop_loss=0.05,                   # 5% stop loss (initially, not used in trailing stop)
        take_profit=0.0,                  # Static take profit percentage (disabled by default)
        trailing_stop=0.03,               # Trailing stop loss percentage (3% drop from the highest price reached)
        atr_period=14,                    # ATR period for volatility-based exit
        atr_multiplier=2.0,               # ATR multiplier for profit taking exit
    )

    def __init__(self):
        # Initialize indicators in order of dependency
        # First, price-based indicators
        self.bbands = bt.indicators.BollingerBands(
            self.data.close,
            period=self.p.period,
            devfactor=self.p.devfactor,
            plotname='Bollinger Bands'
        )
        self.bbands.plotinfo.plot = False

        # ATR indicator
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.p.atr_period,
            plotname='ATR'
        )
        self.atr.plotinfo.plot = False

        # Finally, crossover indicators that depend on Bollinger Bands
        self.crossup = bt.indicators.CrossOver(
            self.data.close,
            self.bbands.top,
            plotname='Cross Up'
        )
        self.crossdown = bt.indicators.CrossOver(
            self.data.close,
            self.bbands.mid,
            plotname='Cross Down'
        )
        self.crossup.plotinfo.plot = False
        self.crossdown.plotinfo.plot = False

        # Explicitly cast atr_period to int
        atr_period_int = int(self.p.atr_period)
        # ATR indicator for volatility based exit
        self.atr = bt.indicators.ATR(self.data, period=atr_period_int)


        self.order = None
        self.entry_price = None
        self.highest_price = None  # To track the highest price reached since entry

    def next(self):
        # If there is a pending order, do nothing.
        if self.order:
            return

        # Entry logic: buy when price crosses above the upper Bollinger band.
        if not self.position:
            if self.crossup > 0:
                self.order = self.buy()
                # Reset tracking variables once a new position is opened.
                self.entry_price = None
                self.highest_price = None
        else:
            # Initialize entry_price and highest_price when position is active.
            if self.entry_price is None:
                self.entry_price = self.position.price
                self.highest_price = self.data.close[0]

            # Update the highest price reached.
            if self.data.close[0] > self.highest_price:
                self.highest_price = self.data.close[0]

            # 1. Check ATR-based profit taking exit:
            #    If the current price exceeds the entry price by a multiple of ATR, exit.
            if self.p.atr_multiplier > 0 and len(self.atr) > self.p.atr_period and self.data.close[0] >= self.entry_price + self.p.atr_multiplier * self.atr[0]:
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"ATR TAKE PROFIT EXIT - Change: ${change:.2f} ({pct_change:.2f}%) "
                         f"[Entry: ${self.entry_price:.2f}, Exit: ${self.data.close[0]:.2f}]")
                self.order = self.close()
                return

            # 2. Check trailing stop loss exit:
            #    Exit if price falls below the highest reached price by the trailing_stop percentage.
            trailing_stop_price = self.highest_price * (1 - self.p.trailing_stop)
            if self.data.close[0] < trailing_stop_price:
                change = self.data.close[0] - self.entry_price
                pct_change = (change / self.entry_price) * 100
                self.log(f"TRAILING STOP EXIT - Highest: ${self.highest_price:.2f}, "
                         f"Stop Price: ${trailing_stop_price:.2f}, Current: ${self.data.close[0]:.2f} "
                         f"[Entry: ${self.entry_price:.2f}, Change: ${change:.2f} ({pct_change:.2f}%)]")
                self.order = self.close()
                return

            # 3. Existing exit logic based on crossing below the middle Bollinger band.
            if self.crossdown < 0:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.highest_price = order.executed.price  # Reset highest on entry
                self.log("BUY EXECUTED, Price: %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, Price: %.2f" % order.executed.price)
                self.entry_price = None
                self.highest_price = None
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")
