import backtrader as bt
import numpy as np

class CandlestickPatternBase(bt.Indicator):
    """Base class for all candlestick pattern indicators"""
    lines = ('pattern',)
    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(pattern=dict(marker='o', markersize=8, color='lime', fillstyle='full'))

    def __init__(self):
        self.lines.pattern = np.nan  # Default to no pattern


class Doji(CandlestickPatternBase):
    """
    Doji candlestick pattern indicator.
    
    A Doji forms when the opening and closing prices are virtually equal,
    suggesting indecision in the market.
    
    Parameters:
    - body_ratio (float): Maximum percentage difference between open and close to be considered a Doji
    """
    params = (
        ('body_ratio', 0.05),  # Maximum body/range ratio to be considered a Doji
    )
    
    def __init__(self):
        super(Doji, self).__init__()
        self.plotlines.pattern = dict(marker='o', markersize=8, color='yellow', fillstyle='full')

    def next(self):
        body_size = abs(self.data.close[0] - self.data.open[0])
        range_size = self.data.high[0] - self.data.low[0]
        
        # Prevent division by zero
        if range_size == 0:
            self.lines.pattern[0] = np.nan
            return
            
        body_range_ratio = body_size / range_size
        
        # Check if it's a Doji
        if body_range_ratio <= self.p.body_ratio and range_size > 0:
            self.lines.pattern[0] = self.data.high[0]  # Plot at the high point
        else:
            self.lines.pattern[0] = np.nan


class Hammer(CandlestickPatternBase):
    """
    Hammer candlestick pattern indicator.
    
    A Hammer has a small body at the top with a long lower shadow and small or no upper shadow.
    It's a potential bullish reversal pattern when occurring after a downtrend.
    
    Parameters:
    - body_ratio (float): Maximum body to range ratio
    - shadow_ratio (float): Minimum lower shadow to range ratio
    - trend_bars (int): Number of bars to look back for trend determination
    - body_pos_ratio (float): Maximum body position ratio from top
    """
    params = (
        ('body_ratio', 0.3),        # Maximum body/range ratio
        ('shadow_ratio', 0.6),      # Minimum lower shadow/range ratio
        ('trend_bars', 5),          # Bars to look back for trend
        ('body_pos_ratio', 0.3),    # Body should be in the top 30% of the range
    )
    
    def __init__(self):
        super(Hammer, self).__init__()
        self.plotlines.pattern = dict(marker='^', markersize=8, color='lime', fillstyle='full')
    
    def next(self):
        # Calculate body, shadows, and range
        body_size = abs(self.data.close[0] - self.data.open[0])
        range_size = self.data.high[0] - self.data.low[0]
        
        # Prevent division by zero
        if range_size == 0:
            self.lines.pattern[0] = np.nan
            return
        
        body_ratio = body_size / range_size
        
        # Determine body position
        if self.data.close[0] >= self.data.open[0]:  # Bullish
            upper_body = self.data.close[0]
            lower_body = self.data.open[0]
        else:  # Bearish
            upper_body = self.data.open[0]
            lower_body = self.data.close[0]
        
        # Calculate shadows
        upper_shadow = self.data.high[0] - upper_body
        lower_shadow = lower_body - self.data.low[0]
        upper_shadow_ratio = upper_shadow / range_size
        lower_shadow_ratio = lower_shadow / range_size
        
        # Calculate body position ratio (from top)
        body_pos_ratio = (self.data.high[0] - upper_body) / range_size
        
        # Check if in a downtrend (simple check based on lower lows)
        downtrend = True
        for i in range(1, self.p.trend_bars + 1):
            if len(self.data) <= i:
                downtrend = False
                break
            if self.data.low[-i] > self.data.low[0]:
                downtrend = False
                break
        
        # Check if it's a Hammer
        if (body_ratio <= self.p.body_ratio and 
            lower_shadow_ratio >= self.p.shadow_ratio and
            upper_shadow_ratio <= 0.1 and
            body_pos_ratio <= self.p.body_pos_ratio and
            downtrend):
            self.lines.pattern[0] = self.data.low[0]  # Plot at the low point
        else:
            self.lines.pattern[0] = np.nan


class ShootingStar(CandlestickPatternBase):
    """
    Shooting Star candlestick pattern indicator.
    
    A Shooting Star has a small body at the bottom with a long upper shadow and small or no lower shadow.
    It's a potential bearish reversal pattern when occurring after an uptrend.
    
    Parameters:
    - body_ratio (float): Maximum body to range ratio
    - shadow_ratio (float): Minimum upper shadow to range ratio
    - trend_bars (int): Number of bars to look back for trend determination
    - body_pos_ratio (float): Maximum body position ratio from bottom
    """
    params = (
        ('body_ratio', 0.3),        # Maximum body/range ratio
        ('shadow_ratio', 0.6),      # Minimum upper shadow/range ratio
        ('trend_bars', 5),          # Bars to look back for trend
        ('body_pos_ratio', 0.3),    # Body should be in the bottom 30% of the range
    )
    
    def __init__(self):
        super(ShootingStar, self).__init__()
        self.plotlines.pattern = dict(marker='v', markersize=8, color='red', fillstyle='full')
    
    def next(self):
        # Calculate body, shadows, and range
        body_size = abs(self.data.close[0] - self.data.open[0])
        range_size = self.data.high[0] - self.data.low[0]
        
        # Prevent division by zero
        if range_size == 0:
            self.lines.pattern[0] = np.nan
            return
        
        body_ratio = body_size / range_size
        
        # Determine body position
        if self.data.close[0] >= self.data.open[0]:  # Bullish
            upper_body = self.data.close[0]
            lower_body = self.data.open[0]
        else:  # Bearish
            upper_body = self.data.open[0]
            lower_body = self.data.close[0]
        
        # Calculate shadows
        upper_shadow = self.data.high[0] - upper_body
        lower_shadow = lower_body - self.data.low[0]
        upper_shadow_ratio = upper_shadow / range_size
        lower_shadow_ratio = lower_shadow / range_size
        
        # Calculate body position ratio (from bottom)
        body_pos_ratio = (lower_body - self.data.low[0]) / range_size
        
        # Check if in an uptrend (simple check based on higher highs)
        uptrend = True
        for i in range(1, self.p.trend_bars + 1):
            if len(self.data) <= i:
                uptrend = False
                break
            if self.data.high[-i] < self.data.high[0]:
                uptrend = False
                break
        
        # Check if it's a Shooting Star
        if (body_ratio <= self.p.body_ratio and 
            upper_shadow_ratio >= self.p.shadow_ratio and
            lower_shadow_ratio <= 0.1 and
            body_pos_ratio <= self.p.body_pos_ratio and
            uptrend):
            self.lines.pattern[0] = self.data.high[0]  # Plot at the high point
        else:
            self.lines.pattern[0] = np.nan


class Engulfing(CandlestickPatternBase):
    """
    Bullish or Bearish Engulfing candlestick pattern indicator.
    
    A Bullish Engulfing pattern forms when a small bearish (red) candle is followed by a larger bullish (green) candle
    that completely engulfs the previous candle. It's a potential bullish reversal pattern.
    
    A Bearish Engulfing pattern forms when a small bullish (green) candle is followed by a larger bearish (red) candle
    that completely engulfs the previous candle. It's a potential bearish reversal pattern.
    
    Parameters:
    - trend_bars (int): Number of bars to look back for trend determination
    """
    params = (
        ('trend_bars', 5),  # Bars to look back for trend
    )
    
    def __init__(self):
        super(Engulfing, self).__init__()
        self.plotlines.pattern = dict(marker='o', markersize=8, color='blue', fillstyle='full')
    
    def next(self):
        if len(self.data) <= 1:
            self.lines.pattern[0] = np.nan
            return
        
        # Current candle
        curr_open = self.data.open[0]
        curr_close = self.data.close[0]
        curr_high = self.data.high[0]
        curr_low = self.data.low[0]
        
        # Previous candle
        prev_open = self.data.open[-1]
        prev_close = self.data.close[-1]
        prev_high = self.data.high[-1]
        prev_low = self.data.low[-1]
        
        # Determine if current candle is bullish or bearish
        curr_bullish = curr_close > curr_open
        
        # Determine if previous candle is bullish or bearish
        prev_bullish = prev_close > prev_open
        
        # Check if in a downtrend (for bullish engulfing)
        downtrend = True
        for i in range(1, self.p.trend_bars + 1):
            if len(self.data) <= i + 1:
                downtrend = False
                break
            if self.data.low[-i-1] > self.data.low[-i]:
                downtrend = False
                break
        
        # Check if in an uptrend (for bearish engulfing)
        uptrend = True
        for i in range(1, self.p.trend_bars + 1):
            if len(self.data) <= i + 1:
                uptrend = False
                break
            if self.data.high[-i-1] < self.data.high[-i]:
                uptrend = False
                break
        
        # Bullish Engulfing criteria
        bullish_engulfing = (
            curr_bullish and
            not prev_bullish and
            curr_open <= prev_close and
            curr_close >= prev_open and
            downtrend
        )
        
        # Bearish Engulfing criteria
        bearish_engulfing = (
            not curr_bullish and
            prev_bullish and
            curr_open >= prev_close and
            curr_close <= prev_open and
            uptrend
        )
        
        # Set pattern value
        if bullish_engulfing:
            self.lines.pattern[0] = self.data.low[0]  # Plot at the low point
        elif bearish_engulfing:
            self.lines.pattern[0] = self.data.high[0]  # Plot at the high point
        else:
            self.lines.pattern[0] = np.nan


class MorningStar(CandlestickPatternBase):
    """
    Morning Star candlestick pattern indicator.
    
    A Morning Star is a bullish reversal pattern that consists of three candles:
    1. A large bearish candle
    2. A small candle (either bullish or bearish) with a gap down from the first
    3. A large bullish candle that closes at least halfway up the first candle
    
    It signifies a potential bullish reversal after a downtrend.
    
    Parameters:
    - gap_threshold (float): Minimum gap size as percentage of first candle's body
    - body_size_ratio (float): Minimum ratio for the first and third candles' bodies to be considered "large"
    - middle_body_ratio (float): Maximum ratio for the middle candle's body to be considered "small"
    - trend_bars (int): Number of bars to look back for trend determination
    """
    params = (
        ('gap_threshold', 0.1),     # Minimum gap size
        ('body_size_ratio', 0.5),   # Minimum ratio for large candles
        ('middle_body_ratio', 0.3), # Maximum ratio for middle candle
        ('trend_bars', 5),          # Bars to look back for trend
    )
    
    def __init__(self):
        super(MorningStar, self).__init__()
        self.plotlines.pattern = dict(marker='*', markersize=10, color='lime', fillstyle='full')
    
    def next(self):
        if len(self.data) <= 2:
            self.lines.pattern[0] = np.nan
            return
        
        # Candle 1 (large bearish)
        c1_open = self.data.open[-2]
        c1_close = self.data.close[-2]
        c1_high = self.data.high[-2]
        c1_low = self.data.low[-2]
        c1_body = abs(c1_open - c1_close)
        c1_range = c1_high - c1_low
        
        # Candle 2 (small with gap down)
        c2_open = self.data.open[-1]
        c2_close = self.data.close[-1]
        c2_high = self.data.high[-1]
        c2_low = self.data.low[-1]
        c2_body = abs(c2_open - c2_close)
        c2_range = c2_high - c2_low
        
        # Candle 3 (large bullish)
        c3_open = self.data.open[0]
        c3_close = self.data.close[0]
        c3_high = self.data.high[0]
        c3_low = self.data.low[0]
        c3_body = abs(c3_open - c3_close)
        c3_range = c3_high - c3_low
        
        # Prevent division by zero
        if c1_range == 0 or c2_range == 0 or c3_range == 0:
            self.lines.pattern[0] = np.nan
            return
        
        # Body/range ratios
        c1_body_ratio = c1_body / c1_range
        c2_body_ratio = c2_body / c2_range
        c3_body_ratio = c3_body / c3_range
        
        # Check candle directions
        c1_bearish = c1_close < c1_open  # First candle should be bearish
        c3_bullish = c3_close > c3_open  # Third candle should be bullish
        
        # Calculate gap
        # If first candle is bearish, its lower value is the close
        c1_lower = min(c1_open, c1_close)
        # If second candle is bullish, its higher value is the close, otherwise it's the open
        c2_higher = max(c2_open, c2_close)
        
        # Gap down condition
        gap_down = c2_higher < c1_lower
        
        # Check if third candle closes at least halfway up the first candle's body
        c3_closes_high = c3_close >= (c1_open + c1_close) / 2
        
        # Check if in a downtrend
        downtrend = True
        for i in range(2, self.p.trend_bars + 2):
            if len(self.data) <= i + 1:
                downtrend = False
                break
            if self.data.low[-i-1] > self.data.low[-i]:
                downtrend = False
                break
        
        # Check if it's a Morning Star
        if (c1_bearish and 
            c1_body_ratio >= self.p.body_size_ratio and
            c2_body_ratio <= self.p.middle_body_ratio and
            c3_bullish and 
            c3_body_ratio >= self.p.body_size_ratio and
            gap_down and
            c3_closes_high and
            downtrend):
            self.lines.pattern[0] = self.data.low[-1]  # Plot at the middle candle's low
        else:
            self.lines.pattern[0] = np.nan


class EveningStar(CandlestickPatternBase):
    """
    Evening Star candlestick pattern indicator.
    
    An Evening Star is a bearish reversal pattern that consists of three candles:
    1. A large bullish candle
    2. A small candle (either bullish or bearish) with a gap up from the first
    3. A large bearish candle that closes at least halfway down the first candle
    
    It signifies a potential bearish reversal after an uptrend.
    
    Parameters:
    - gap_threshold (float): Minimum gap size as percentage of first candle's body
    - body_size_ratio (float): Minimum ratio for the first and third candles' bodies to be considered "large"
    - middle_body_ratio (float): Maximum ratio for the middle candle's body to be considered "small"
    - trend_bars (int): Number of bars to look back for trend determination
    """
    params = (
        ('gap_threshold', 0.1),     # Minimum gap size
        ('body_size_ratio', 0.5),   # Minimum ratio for large candles
        ('middle_body_ratio', 0.3), # Maximum ratio for middle candle
        ('trend_bars', 5),          # Bars to look back for trend
    )
    
    def __init__(self):
        super(EveningStar, self).__init__()
        self.plotlines.pattern = dict(marker='*', markersize=10, color='red', fillstyle='full')
    
    def next(self):
        if len(self.data) <= 2:
            self.lines.pattern[0] = np.nan
            return
        
        # Candle 1 (large bullish)
        c1_open = self.data.open[-2]
        c1_close = self.data.close[-2]
        c1_high = self.data.high[-2]
        c1_low = self.data.low[-2]
        c1_body = abs(c1_open - c1_close)
        c1_range = c1_high - c1_low
        
        # Candle 2 (small with gap up)
        c2_open = self.data.open[-1]
        c2_close = self.data.close[-1]
        c2_high = self.data.high[-1]
        c2_low = self.data.low[-1]
        c2_body = abs(c2_open - c2_close)
        c2_range = c2_high - c2_low
        
        # Candle 3 (large bearish)
        c3_open = self.data.open[0]
        c3_close = self.data.close[0]
        c3_high = self.data.high[0]
        c3_low = self.data.low[0]
        c3_body = abs(c3_open - c3_close)
        c3_range = c3_high - c3_low
        
        # Prevent division by zero
        if c1_range == 0 or c2_range == 0 or c3_range == 0:
            self.lines.pattern[0] = np.nan
            return
        
        # Body/range ratios
        c1_body_ratio = c1_body / c1_range
        c2_body_ratio = c2_body / c2_range
        c3_body_ratio = c3_body / c3_range
        
        # Check candle directions
        c1_bullish = c1_close > c1_open  # First candle should be bullish
        c3_bearish = c3_close < c3_open  # Third candle should be bearish
        
        # Calculate gap
        # If first candle is bullish, its higher value is the close
        c1_higher = max(c1_open, c1_close)
        # If second candle is bearish, its lower value is the close, otherwise it's the open
        c2_lower = min(c2_open, c2_close)
        
        # Gap up condition
        gap_up = c2_lower > c1_higher
        
        # Check if third candle closes at least halfway down the first candle's body
        c3_closes_low = c3_close <= (c1_open + c1_close) / 2
        
        # Check if in an uptrend
        uptrend = True
        for i in range(2, self.p.trend_bars + 2):
            if len(self.data) <= i + 1:
                uptrend = False
                break
            if self.data.high[-i-1] < self.data.high[-i]:
                uptrend = False
                break
        
        # Check if it's an Evening Star
        if (c1_bullish and 
            c1_body_ratio >= self.p.body_size_ratio and
            c2_body_ratio <= self.p.middle_body_ratio and
            c3_bearish and 
            c3_body_ratio >= self.p.body_size_ratio and
            gap_up and
            c3_closes_low and
            uptrend):
            self.lines.pattern[0] = self.data.high[-1]  # Plot at the middle candle's high
        else:
            self.lines.pattern[0] = np.nan


class ThreeWhiteSoldiers(CandlestickPatternBase):
    """
    Three White Soldiers candlestick pattern indicator.
    
    Three White Soldiers is a bullish reversal pattern that consists of three consecutive bullish candles,
    each opening within the previous candle's body and closing higher than the previous close.
    
    Parameters:
    - body_size_ratio (float): Minimum body to range ratio for each candle
    - trend_bars (int): Number of bars to look back for trend determination
    """
    params = (
        ('body_size_ratio', 0.5),  # Minimum body/range ratio
        ('trend_bars', 5),         # Bars to look back for trend
    )
    
    def __init__(self):
        super(ThreeWhiteSoldiers, self).__init__()
        self.plotlines.pattern = dict(marker='^', markersize=10, color='lime', fillstyle='full')
    
    def next(self):
        if len(self.data) <= 2:
            self.lines.pattern[0] = np.nan
            return
        
        # Candle 1
        c1_open = self.data.open[-2]
        c1_close = self.data.close[-2]
        c1_high = self.data.high[-2]
        c1_low = self.data.low[-2]
        c1_body = abs(c1_open - c1_close)
        c1_range = c1_high - c1_low
        
        # Candle 2
        c2_open = self.data.open[-1]
        c2_close = self.data.close[-1]
        c2_high = self.data.high[-1]
        c2_low = self.data.low[-1]
        c2_body = abs(c2_open - c2_close)
        c2_range = c2_high - c2_low
        
        # Candle 3
        c3_open = self.data.open[0]
        c3_close = self.data.close[0]
        c3_high = self.data.high[0]
        c3_low = self.data.low[0]
        c3_body = abs(c3_open - c3_close)
        c3_range = c3_high - c3_low
        
        # Prevent division by zero
        if c1_range == 0 or c2_range == 0 or c3_range == 0:
            self.lines.pattern[0] = np.nan
            return
        
        # Body/range ratios
        c1_body_ratio = c1_body / c1_range
        c2_body_ratio = c2_body / c2_range
        c3_body_ratio = c3_body / c3_range
        
        # Check candle directions (all should be bullish)
        c1_bullish = c1_close > c1_open
        c2_bullish = c2_close > c2_open
        c3_bullish = c3_close > c3_open
        
        # Check opening price relationships
        c2_open_within_c1 = c2_open > c1_open and c2_open < c1_close
        c3_open_within_c2 = c3_open > c2_open and c3_open < c2_close
        
        # Check closing price relationships
        c2_closes_higher = c2_close > c1_close
        c3_closes_higher = c3_close > c2_close
        
        # Check if in a downtrend
        downtrend = True
        for i in range(2, self.p.trend_bars + 2):
            if len(self.data) <= i + 1:
                downtrend = False
                break
            if self.data.low[-i-1] > self.data.low[-i]:
                downtrend = False
                break
        
        # Check if it's Three White Soldiers
        if (c1_bullish and c2_bullish and c3_bullish and
            c1_body_ratio >= self.p.body_size_ratio and
            c2_body_ratio >= self.p.body_size_ratio and
            c3_body_ratio >= self.p.body_size_ratio and
            c2_open_within_c1 and c3_open_within_c2 and
            c2_closes_higher and c3_closes_higher and
            downtrend):
            self.lines.pattern[0] = self.data.high[0]  # Plot at the highest point
        else:
            self.lines.pattern[0] = np.nan


class ThreeBlackCrows(CandlestickPatternBase):
    """
    Three Black Crows candlestick pattern indicator.
    
    Three Black Crows is a bearish reversal pattern that consists of three consecutive bearish candles,
    each opening within the previous candle's body and closing lower than the previous close.
    
    Parameters:
    - body_size_ratio (float): Minimum body to range ratio for each candle
    - trend_bars (int): Number of bars to look back for trend determination
    """
    params = (
        ('body_size_ratio', 0.5),  # Minimum body/range ratio
        ('trend_bars', 5),         # Bars to look back for trend
    )
    
    def __init__(self):
        super(ThreeBlackCrows, self).__init__()
        self.plotlines.pattern = dict(marker='v', markersize=10, color='red', fillstyle='full')
    
    def next(self):
        if len(self.data) <= 2:
            self.lines.pattern[0] = np.nan
            return
        
        # Candle 1
        c1_open = self.data.open[-2]
        c1_close = self.data.close[-2]
        c1_high = self.data.high[-2]
        c1_low = self.data.low[-2]
        c1_body = abs(c1_open - c1_close)
        c1_range = c1_high - c1_low
        
        # Candle 2
        c2_open = self.data.open[-1]
        c2_close = self.data.close[-1]
        c2_high = self.data.high[-1]
        c2_low = self.data.low[-1]
        c2_body = abs(c2_open - c2_close)
        c2_range = c2_high - c2_low
        
        # Candle 3
        c3_open = self.data.open[0]
        c3_close = self.data.close[0]
        c3_high = self.data.high[0]
        c3_low = self.data.low[0]
        c3_body = abs(c3_open - c3_close)
        c3_range = c3_high - c3_low
        
        # Prevent division by zero
        if c1_range == 0 or c2_range == 0 or c3_range == 0:
            self.lines.pattern[0] = np.nan
            return
        
        # Body/range ratios
        c1_body_ratio = c1_body / c1_range
        c2_body_ratio = c2_body / c2_range
        c3_body_ratio = c3_body / c3_range
        
        # Check candle directions (all should be bearish)
        c1_bearish = c1_close < c1_open
        c2_bearish = c2_close < c2_open
        c3_bearish = c3_close < c3_open
        
        # Check opening price relationships
        c2_open_within_c1 = c2_open < c1_open and c2_open > c1_close
        c3_open_within_c2 = c3_open < c2_open and c3_open > c2_close
        
        # Check closing price relationships
        c2_closes_lower = c2_close < c1_close
        c3_closes_lower = c3_close < c2_close
        
        # Check if in an uptrend
        uptrend = True
        for i in range(2, self.p.trend_bars + 2):
            if len(self.data) <= i + 1:
                uptrend = False
                break
            if self.data.high[-i-1] < self.data.high[-i]:
                uptrend = False
                break
        
        # Check if it's Three Black Crows
        if (c1_bearish and c2_bearish and c3_bearish and
            c1_body_ratio >= self.p.body_size_ratio and
            c2_body_ratio >= self.p.body_size_ratio and
            c3_body_ratio >= self.p.body_size_ratio and
            c2_open_within_c1 and c3_open_within_c2 and
            c2_closes_lower and c3_closes_lower and
            uptrend):
            self.lines.pattern[0] = self.data.low[0]  # Plot at the lowest point
        else:
            self.lines.pattern[0] = np.nan


# Dictionary mapping pattern names to pattern classes
CANDLESTICK_PATTERNS = {
    'doji': Doji,
    'hammer': Hammer,
    'shooting_star': ShootingStar,
    'engulfing': Engulfing,
    'morning_star': MorningStar,
    'evening_star': EveningStar,
    'three_white_soldiers': ThreeWhiteSoldiers,
    'three_black_crows': ThreeBlackCrows,
}