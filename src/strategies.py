# strategies.py
import backtrader as bt

class SmaCross(bt.Strategy):
    params = dict(
        pfast=21,  # fast SMA period
        pslow=55   # slow SMA period
    )

    def __init__(self):
        sma_fast = bt.indicators.SMA(self.data.close, period=self.p.pfast)
        sma_slow = bt.indicators.SMA(self.data.close, period=self.p.pslow)
        self.crossover = bt.indicators.CrossOver(sma_fast, sma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()  # enter long on bullish crossover
        elif self.crossover < 0:
            self.close()  # exit when crossover turns negative

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}")

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")