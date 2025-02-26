import backtrader as bt
import numpy as np
from candlestick_patterns import CANDLESTICK_PATTERNS

class CandlestickPatternStrategy(bt.Strategy):
    """
    A strategy that trades based on candlestick patterns.
    
    Parameters:
    - patterns (list): List of pattern names to use
    - pattern_params (dict): Dictionary of parameters for each pattern
    - stop_loss (float): Stop loss percentage
    - take_profit (float): Take profit percentage
    - consecutive_bars (int): Number of consecutive bars a pattern must be detected to trigger
    - confirmation_indicator (str): Optional indicator for confirmation (None, 'sma', 'rsi', 'macd')
    - confirmation_params (dict): Parameters for the confirmation indicator
    - exit_on_opposite (bool): Whether to exit on opposite pattern detection
    """
    params = dict(
        patterns=['engulfing'],  # Default pattern to look for
        pattern_params={},       # Parameters for each pattern
        stop_loss=0.05,          # Default stop loss percentage (5%)
        take_profit=0.10,        # Default take profit percentage (10%)
        consecutive_bars=1,      # Number of consecutive bars a pattern must be detected
        confirmation_indicator=None,   # 'sma', 'rsi', 'macd', etc.
        confirmation_params={},  # Parameters for the confirmation indicator
        exit_on_opposite=True,   # Exit on opposite pattern detection
    )
    
    def __init__(self):
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.target_price = None
        self.num_trades = 0
        self.num_profitable_trades = 0
        
        # Initialize pattern indicators
        self.patterns = {}
        self.bullish_patterns = ['hammer', 'engulfing', 'morning_star', 'three_white_soldiers']
        self.bearish_patterns = ['shooting_star', 'engulfing', 'evening_star', 'three_black_crows']
        
        # Instantiate pattern indicators
        for pattern_name in self.p.patterns:
            if pattern_name in CANDLESTICK_PATTERNS:
                pattern_class = CANDLESTICK_PATTERNS[pattern_name]
                params = self.p.pattern_params.get(pattern_name, {})
                self.patterns[pattern_name] = pattern_class(**params)
            else:
                self.log(f"Warning: Pattern '{pattern_name}' not found in available patterns")
        
        # Add confirmation indicator if specified
        self.confirmation = None
        if self.p.confirmation_indicator == 'sma':
            self.sma_fast = bt.indicators.SMA(
                self.data.close, 
                period=self.p.confirmation_params.get('fast_period', 20)
            )
            self.sma_slow = bt.indicators.SMA(
                self.data.close, 
                period=self.p.confirmation_params.get('slow_period', 50)
            )
            self.confirmation = self.sma_fast > self.sma_slow
        elif self.p.confirmation_indicator == 'rsi':
            self.rsi = bt.indicators.RSI(
                self.data.close,
                period=self.p.confirmation_params.get('period', 14)
            )
            self.oversold = self.p.confirmation_params.get('oversold', 30)
            self.overbought = self.p.confirmation_params.get('overbought', 70)
        elif self.p.confirmation_indicator == 'macd':
            self.macd = bt.indicators.MACD(
                self.data.close,
                period_me1=self.p.confirmation_params.get('fast_period', 12),
                period_me2=self.p.confirmation_params.get('slow_period', 26),
                period_signal=self.p.confirmation_params.get('signal_period', 9)
            )
        
        # Variables to track consecutive pattern detections
        self.bullish_count = {}
        self.bearish_count = {}
        for pattern_name in self.p.patterns:
            self.bullish_count[pattern_name] = 0
            self.bearish_count[pattern_name] = 0
    
    def next(self):
        if self.order:
            return
        
        # Update pattern detection counts
        for pattern_name, pattern in self.patterns.items():
            # Check for a non-NaN pattern detection
            if not np.isnan(pattern.lines.pattern[0]):
                # Determine if bullish or bearish
                if pattern_name in self.bullish_patterns and pattern_name not in self.bearish_patterns:
                    self.bullish_count[pattern_name] += 1
                    self.bearish_count[pattern_name] = 0
                elif pattern_name in self.bearish_patterns and pattern_name not in self.bullish_patterns:
                    self.bearish_count[pattern_name] += 1
                    self.bullish_count[pattern_name] = 0
                else:
                    # For patterns that can be both bullish and bearish (like engulfing)
                    # Need to determine direction based on the pattern instance
                    if self._is_bullish_pattern(pattern_name):
                        self.bullish_count[pattern_name] += 1
                        self.bearish_count[pattern_name] = 0
                    elif self._is_bearish_pattern(pattern_name):
                        self.bearish_count[pattern_name] += 1
                        self.bullish_count[pattern_name] = 0
            else:
                # Reset count on non-detection
                self.bullish_count[pattern_name] = 0
                self.bearish_count[pattern_name] = 0
        
        # Check if any bullish pattern has reached consecutive_bars count
        bullish_trigger = False
        triggered_pattern = None
        for pattern_name in self.p.patterns:
            if self.bullish_count[pattern_name] >= self.p.consecutive_bars:
                bullish_trigger = True
                triggered_pattern = pattern_name
                break
        
        # Check if any bearish pattern has reached consecutive_bars count
        bearish_trigger = False
        for pattern_name in self.p.patterns:
            if self.bearish_count[pattern_name] >= self.p.consecutive_bars:
                bearish_trigger = True
                triggered_pattern = pattern_name
                break
        
        # Check confirmation if needed
        if self.confirmation is not None:
            if self.p.confirmation_indicator == 'sma':
                bullish_confirmation = self.sma_fast[0] > self.sma_slow[0]
                bearish_confirmation = self.sma_fast[0] < self.sma_slow[0]
                
                bullish_trigger = bullish_trigger and bullish_confirmation
                bearish_trigger = bearish_trigger and bearish_confirmation
            
            elif self.p.confirmation_indicator == 'rsi':
                bullish_confirmation = self.rsi[0] < self.oversold
                bearish_confirmation = self.rsi[0] > self.overbought
                
                bullish_trigger = bullish_trigger and bullish_confirmation
                bearish_trigger = bearish_trigger and bearish_confirmation
            
            elif self.p.confirmation_indicator == 'macd':
                bullish_confirmation = self.macd.macd[0] > self.macd.signal[0]
                bearish_confirmation = self.macd.macd[0] < self.macd.signal[0]
                
                bullish_trigger = bullish_trigger and bullish_confirmation
                bearish_trigger = bearish_trigger and bearish_confirmation
        
        # Trading logic
        if not self.position:
            # No position, look to enter
            if bullish_trigger:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.stop_price = self.entry_price * (1 - self.p.stop_loss)
                self.target_price = self.entry_price * (1 + self.p.take_profit)
                self.log(f"BUY SIGNAL ({triggered_pattern}), Price: {self.entry_price:.2f}, Stop: {self.stop_price:.2f}, Target: {self.target_price:.2f}")
            
            elif bearish_trigger and self.p.short_allowed:
                self.order = self.sell()
                self.entry_price = self.data.close[0]
                self.stop_price = self.entry_price * (1 + self.p.stop_loss)
                self.target_price = self.entry_price * (1 - self.p.take_profit)
                self.log(f"SELL SIGNAL ({triggered_pattern}), Price: {self.entry_price:.2f}, Stop: {self.stop_price:.2f}, Target: {self.target_price:.2f}")
        
        else:
            # Have an open position, look to exit
            if self.position.size > 0:  # Long position
                # Check for take profit or stop loss
                if self.data.close[0] >= self.target_price:
                    self.order = self.close()
                    self.log(f"CLOSE LONG (TAKE PROFIT), Price: {self.data.close[0]:.2f}")
                    self.num_trades += 1
                    self.num_profitable_trades += 1
                
                elif self.data.close[0] <= self.stop_price:
                    self.order = self.close()
                    self.log(f"CLOSE LONG (STOP LOSS), Price: {self.data.close[0]:.2f}")
                    self.num_trades += 1
                
                # Check for bearish reversal if exit_on_opposite is enabled
                elif self.p.exit_on_opposite and bearish_trigger:
                    self.order = self.close()
                    self.log(f"CLOSE LONG (BEARISH SIGNAL: {triggered_pattern}), Price: {self.data.close[0]:.2f}")
                    self.num_trades += 1
                    if self.data.close[0] > self.entry_price:
                        self.num_profitable_trades += 1
            
            elif self.position.size < 0 and self.p.short_allowed:  # Short position
                # Check for take profit or stop loss
                if self.data.close[0] <= self.target_price:
                    self.order = self.close()
                    self.log(f"CLOSE SHORT (TAKE PROFIT), Price: {self.data.close[0]:.2f}")
                    self.num_trades += 1
                    self.num_profitable_trades += 1
                
                elif self.data.close[0] >= self.stop_price:
                    self.order = self.close()
                    self.log(f"CLOSE SHORT (STOP LOSS), Price: {self.data.close[0]:.2f}")
                    self.num_trades += 1
                
                # Check for bullish reversal if exit_on_opposite is enabled
                elif self.p.exit_on_opposite and bullish_trigger:
                    self.order = self.close()
                    self.log(f"CLOSE SHORT (BULLISH SIGNAL: {triggered_pattern}), Price: {self.data.close[0]:.2f}")
                    self.num_trades += 1
                    if self.data.close[0] < self.entry_price:
                        self.num_profitable_trades += 1
    
    def _is_bullish_pattern(self, pattern_name):
        """Determine if the pattern instance is bullish"""
        if pattern_name == 'engulfing':
            # For engulfing, check if current candle is bullish and previous is bearish
            return (self.data.close[0] > self.data.open[0] and 
                    self.data.close[-1] < self.data.open[-1])
        return False
    
    def _is_bearish_pattern(self, pattern_name):
        """Determine if the pattern instance is bearish"""
        if pattern_name == 'engulfing':
            # For engulfing, check if current candle is bearish and previous is bullish
            return (self.data.close[0] < self.data.open[0] and 
                    self.data.close[-1] > self.data.open[-1])
        return False
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}")
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
        
        self.order = None
    
    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime(0)
        print(f"{dt.isoformat()} {txt}")
    
    def stop(self):
        # Log the strategy results
        pct_profitable = (self.num_profitable_trades / self.num_trades * 100) if self.num_trades > 0 else 0.0
        self.log(f"Strategy finished. Total trades: {self.num_trades}, "
                 f"Profitable trades: {self.num_profitable_trades} ({pct_profitable:.1f}%)")