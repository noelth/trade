import pytest
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candlestick_patterns import (
    Doji, Hammer, ShootingStar, Engulfing, 
    MorningStar, EveningStar, ThreeWhiteSoldiers, ThreeBlackCrows,
    CANDLESTICK_PATTERNS
)

class TestData(bt.feeds.PandasData):
    """Test data feed using pandas"""
    
    def __init__(self, dataframe, **kwargs):
        # Convert index to datetime if it's not already
        if not isinstance(dataframe.index, pd.DatetimeIndex):
            dataframe = dataframe.set_index(pd.DatetimeIndex(dataframe.index))
        
        # Add any missing columns with default values
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in dataframe.columns:
                if col == 'Volume':
                    dataframe[col] = 100000
                else:
                    dataframe[col] = dataframe['Close']
        
        super(TestData, self).__init__(dataname=dataframe, **kwargs)

@pytest.fixture
def doji_data():
    """Create data containing a Doji pattern"""
    dates = pd.date_range(start='2022-01-01', periods=5)
    data = pd.DataFrame({
        'Open':  [100, 105, 110, 115, 120],
        'High':  [105, 110, 118, 120, 125],
        'Low':   [95,  100, 108, 110, 115],
        'Close': [101, 106, 110.1, 116, 121],  # 3rd day is a Doji (open=110, close=110.1)
        'Volume':[100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def hammer_data():
    """Create data containing a Hammer pattern in a downtrend"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    # Create a downtrend first
    data = pd.DataFrame({
        'Open':  [120, 115, 110, 105, 100, 95, 90, 85, 82, 80],
        'High':  [125, 120, 115, 110, 105, 100, 95, 90, 83, 85],
        'Low':   [115, 110, 105, 100, 95, 90, 85, 75, 70, 78],  # 8th day has a long lower shadow
        'Close': [115, 110, 105, 100, 95, 90, 85, 82, 81, 79],  # 8th day closes near high (hammer)
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def shooting_star_data():
    """Create data containing a Shooting Star pattern in an uptrend"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    # Create an uptrend first
    data = pd.DataFrame({
        'Open':  [80, 85, 90, 95, 100, 105, 110, 118, 120, 115],
        'High':  [85, 90, 95, 100, 105, 110, 115, 130, 125, 120],  # 8th day has a long upper shadow
        'Low':   [78, 83, 88, 93, 98, 103, 108, 115, 115, 110],
        'Close': [85, 90, 95, 100, 105, 110, 115, 119, 118, 112],  # 8th day closes near low (shooting star)
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def engulfing_data():
    """Create data containing both Bullish and Bearish Engulfing patterns"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    data = pd.DataFrame({
        # Create a downtrend first (for bullish engulfing)
        'Open':  [120, 115, 110, 105, 100, 98, 95, 85, 90, 95],
        'High':  [125, 120, 115, 110, 105, 100, 98, 95, 95, 100],
        'Low':   [115, 110, 105, 100, 95, 90, 90, 80, 85, 90],
        # Day 7-8: Bullish engulfing (small red candle followed by large green candle)
        # Day 9-10: Bearish engulfing (small green candle followed by large red candle)
        'Close': [115, 110, 105, 100, 95, 92, 90, 93, 92, 85],
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def morning_star_data():
    """Create data containing a Morning Star pattern"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    data = pd.DataFrame({
        # Create a downtrend first
        'Open':  [120, 115, 110, 105, 100, 98, 95, 90, 85, 95],
        'High':  [125, 120, 115, 110, 105, 100, 98, 91, 90, 100],
        'Low':   [115, 110, 105, 100, 95, 90, 90, 84, 80, 85],
        # Days 7-8-9: Morning star (large red, small body, large green)
        'Close': [115, 110, 105, 100, 95, 92, 90, 85, 88, 93],
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def evening_star_data():
    """Create data containing an Evening Star pattern"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    data = pd.DataFrame({
        # Create an uptrend first
        'Open':  [80, 85, 90, 95, 100, 105, 110, 115, 120, 110],
        'High':  [85, 90, 95, 100, 105, 110, 115, 120, 125, 115],
        'Low':   [78, 83, 88, 93, 98, 103, 108, 110, 115, 100],
        # Days 7-8-9: Evening star (large green, small body, large red)
        'Close': [85, 90, 95, 100, 105, 110, 115, 118, 115, 102],
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def three_white_soldiers_data():
    """Create data containing Three White Soldiers pattern"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    data = pd.DataFrame({
        # Create a downtrend first
        'Open':  [120, 115, 110, 105, 100, 95, 90, 92, 97, 103],
        'High':  [125, 120, 115, 110, 105, 100, 95, 98, 103, 110],
        'Low':   [115, 110, 105, 100, 95, 90, 85, 90, 95, 100],
        # Days 8-9-10: Three white soldiers (consecutive bullish candles with higher closes)
        'Close': [115, 110, 105, 100, 95, 90, 85, 97, 102, 109],
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

@pytest.fixture
def three_black_crows_data():
    """Create data containing Three Black Crows pattern"""
    dates = pd.date_range(start='2022-01-01', periods=10)
    data = pd.DataFrame({
        # Create an uptrend first
        'Open':  [80, 85, 90, 95, 100, 105, 110, 115, 110, 105],
        'High':  [85, 90, 95, 100, 105, 110, 115, 118, 112, 107],
        'Low':   [78, 83, 88, 93, 98, 103, 108, 110, 105, 100],
        # Days 8-9-10: Three black crows (consecutive bearish candles with lower closes)
        'Close': [85, 90, 95, 100, 105, 110, 115, 112, 107, 102],
        'Volume':[100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000]
    }, index=dates)
    return data

class TestDoji:
    def test_doji_detection(self, doji_data):
        """Test that Doji correctly identifies a doji pattern"""
        cerebro = bt.Cerebro()
        data = TestData(doji_data)
        cerebro.adddata(data)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio)
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
        
        # Add the Doji indicator
        doji = Doji(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=doji)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The 3rd bar (index 2) should be a Doji
        assert observer.detected.array[2]
        
        # Other bars should not be Doji
        assert not observer.detected.array[0]
        assert not observer.detected.array[1]

class TestHammer:
    def test_hammer_detection(self, hammer_data):
        """Test that Hammer correctly identifies a hammer pattern"""
        cerebro = bt.Cerebro()
        data = TestData(hammer_data)
        cerebro.adddata(data)
        
        # Add the Hammer indicator
        hammer = Hammer(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=hammer)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The 8th bar (index 7) should be a Hammer
        assert observer.detected.array[7]
        
        # Other bars should not be Hammers
        assert not observer.detected.array[5]
        assert not observer.detected.array[6]
        assert not observer.detected.array[8]

class TestShootingStar:
    def test_shooting_star_detection(self, shooting_star_data):
        """Test that ShootingStar correctly identifies a shooting star pattern"""
        cerebro = bt.Cerebro()
        data = TestData(shooting_star_data)
        cerebro.adddata(data)
        
        # Add the ShootingStar indicator
        shooting_star = ShootingStar(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=shooting_star)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The 8th bar (index 7) should be a Shooting Star
        assert observer.detected.array[7]
        
        # Other bars should not be Shooting Stars
        assert not observer.detected.array[6]
        assert not observer.detected.array[8]

class TestEngulfing:
    def test_engulfing_detection(self, engulfing_data):
        """Test that Engulfing correctly identifies engulfing patterns"""
        cerebro = bt.Cerebro()
        data = TestData(engulfing_data)
        cerebro.adddata(data)
        
        # Add the Engulfing indicator
        engulfing = Engulfing(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=engulfing)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # We should detect engulfing patterns at certain points
        # Note: The exact indices will depend on the pattern implementation
        assert any(observer.detected.array[7:9]), "Bullish engulfing pattern not detected"
        assert any(observer.detected.array[8:10]), "Bearish engulfing pattern not detected"

class TestMorningStar:
    def test_morning_star_detection(self, morning_star_data):
        """Test that MorningStar correctly identifies a morning star pattern"""
        cerebro = bt.Cerebro()
        data = TestData(morning_star_data)
        cerebro.adddata(data)
        
        # Add the MorningStar indicator
        morning_star = MorningStar(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=morning_star)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The pattern should be detected around bar 8
        assert any(observer.detected.array[7:9]), "Morning star pattern not detected"

class TestEveningStar:
    def test_evening_star_detection(self, evening_star_data):
        """Test that EveningStar correctly identifies an evening star pattern"""
        cerebro = bt.Cerebro()
        data = TestData(evening_star_data)
        cerebro.adddata(data)
        
        # Add the EveningStar indicator
        evening_star = EveningStar(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=evening_star)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The pattern should be detected around bar 8
        assert any(observer.detected.array[7:9]), "Evening star pattern not detected"

class TestThreeWhiteSoldiers:
    def test_three_white_soldiers_detection(self, three_white_soldiers_data):
        """Test that ThreeWhiteSoldiers correctly identifies the pattern"""
        cerebro = bt.Cerebro()
        data = TestData(three_white_soldiers_data)
        cerebro.adddata(data)
        
        # Add the indicator
        indicator = ThreeWhiteSoldiers(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=indicator)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The pattern should be detected in the last bar
        assert observer.detected.array[9], "Three white soldiers pattern not detected"

class TestThreeBlackCrows:
    def test_three_black_crows_detection(self, three_black_crows_data):
        """Test that ThreeBlackCrows correctly identifies the pattern"""
        cerebro = bt.Cerebro()
        data = TestData(three_black_crows_data)
        cerebro.adddata(data)
        
        # Add the indicator
        indicator = ThreeBlackCrows(data)
        
        # Create an observer to check the indicator values
        class Observer(bt.Observer):
            lines = ('detected',)
            params = (('indicator', None),)
            
            def next(self):
                self.lines.detected[0] = not np.isnan(self.p.indicator[0])
        
        cerebro.addobserver(Observer, indicator=indicator)
        
        # Run the backtest
        results = cerebro.run()
        
        # Get the observer data
        observer = results[0].observers[0]
        
        # The pattern should be detected in the last bar
        assert observer.detected.array[9], "Three black crows pattern not detected"

def test_candlestick_patterns_dictionary():
    """Test that all patterns are correctly registered in the CANDLESTICK_PATTERNS dictionary"""
    expected_patterns = [
        'doji',
        'hammer',
        'shooting_star',
        'engulfing',
        'morning_star',
        'evening_star',
        'three_white_soldiers',
        'three_black_crows'
    ]
    
    for pattern in expected_patterns:
        assert pattern in CANDLESTICK_PATTERNS, f"Pattern {pattern} missing from CANDLESTICK_PATTERNS dictionary"
        
    # Check that all entries are valid classes
    for name, pattern_class in CANDLESTICK_PATTERNS.items():
        assert isinstance(pattern_class, type), f"Entry for {name} is not a class"
        assert issubclass(pattern_class, bt.Indicator), f"Pattern {name} does not inherit from bt.Indicator"