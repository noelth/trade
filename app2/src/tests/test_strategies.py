import pytest
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strategy import SmaCross, BollingerBreakoutStrategy, RsiMacdStrategy

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
def trending_data():
    """Create test data with a clear trend for SMA testing"""
    dates = pd.date_range(start='2022-01-01', periods=300)
    
    # Create an uptrend followed by a downtrend
    uptrend = np.arange(100, 200, 200/150)
    downtrend = np.arange(200, 100, -200/150)
    prices = np.concatenate([uptrend, downtrend])
    
    # Add some noise
    noise = np.random.normal(0, 2, 300)
    prices = prices + noise
    
    data = pd.DataFrame({
        'Close': prices,
        'Open': prices - np.random.normal(0, 1, 300),
        'Volume': 100000 + np.random.normal(0, 10000, 300)
    }, index=dates)
    
    data['High'] = data[['Open', 'Close']].max(axis=1) + abs(np.random.normal(0, 1, 300))
    data['Low'] = data[['Open', 'Close']].min(axis=1) - abs(np.random.normal(0, 1, 300))
    
    return data

@pytest.fixture
def volatile_data():
    """Create test data with high volatility for Bollinger Bands testing"""
    dates = pd.date_range(start='2022-01-01', periods=300)
    
    # Base prices
    base = np.concatenate([
        np.arange(100, 150, 50/100),
        np.arange(150, 100, -50/100),
        np.arange(100, 130, 30/100)
    ])
    
    # Increase volatility in the middle section
    volatility = np.concatenate([
        np.ones(100),
        np.ones(100) * 3,
        np.ones(100)
    ])
    
    # Generate prices with varying volatility
    noise = np.random.normal(0, volatility, 300)
    prices = base + noise
    
    data = pd.DataFrame({
        'Close': prices,
        'Open': prices - np.random.normal(0, 1, 300),
        'Volume': 100000 + np.random.normal(0, 10000, 300)
    }, index=dates)
    
    data['High'] = data[['Open', 'Close']].max(axis=1) + abs(np.random.normal(0, volatility, 300))
    data['Low'] = data[['Open', 'Close']].min(axis=1) - abs(np.random.normal(0, volatility, 300))
    
    return data

@pytest.fixture
def oscillating_data():
    """Create test data with oscillations for RSI/MACD testing"""
    dates = pd.date_range(start='2022-01-01', periods=300)
    
    # Create a sine wave with a slight upward trend
    t = np.linspace(0, 6*np.pi, 300)
    sine = np.sin(t) * 20
    trend = np.linspace(100, 150, 300)
    prices = trend + sine
    
    data = pd.DataFrame({
        'Close': prices,
        'Open': prices - np.random.normal(0, 2, 300),
        'Volume': 100000 + np.random.normal(0, 10000, 300)
    }, index=dates)
    
    data['High'] = data[['Open', 'Close']].max(axis=1) + abs(np.random.normal(0, 3, 300))
    data['Low'] = data[['Open', 'Close']].min(axis=1) - abs(np.random.normal(0, 3, 300))
    
    return data

class TestSmaCross:
    def test_sma_cross_strategy(self, trending_data):
        """Test that SMA Cross strategy triggers trades on crossovers"""
        cerebro = bt.Cerebro()
        data = TestData(trending_data)
        cerebro.adddata(data)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Add SMA Cross strategy
        cerebro.addstrategy(SmaCross, 
                          sma_fast_period=20, 
                          sma_slow_period=50,
                          take_profit=0.1)
        
        # Run with initial cash
        cerebro.broker.setcash(10000)
        cerebro.broker.setcommission(commission=0.001)
        
        results = cerebro.run()
        strategy = results[0]
        
        # Check that trades were executed
        trade_analysis = strategy.analyzers.trades.get_analysis()
        assert 'total' in trade_analysis
        assert trade_analysis['total']['total'] > 0, "No trades executed"
        
        # Since we have a clear trend with a reversal, strategy should have both long and short trades
        assert strategy.num_trades > 0, "No trades recorded by strategy"
    
    def test_sma_parameters(self, trending_data):
        """Test SMA strategy with different parameters"""
        # Test with different SMA combinations
        results = []
        
        for fast_period in [10, 20, 50]:
            for slow_period in [50, 100, 200]:
                if fast_period >= slow_period:
                    continue
                
                cerebro = bt.Cerebro()
                cerebro.adddata(TestData(trending_data))
                cerebro.broker.setcash(10000)
                
                cerebro.addstrategy(SmaCross,
                                  sma_fast_period=fast_period,
                                  sma_slow_period=slow_period)
                
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
                
                res = cerebro.run()
                strategy = res[0]
                
                trade_analysis = strategy.analyzers.trades.get_analysis()
                total_trades = trade_analysis.get('total', {}).get('total', 0)
                
                results.append({
                    'fast_period': fast_period,
                    'slow_period': slow_period,
                    'final_value': cerebro.broker.getvalue(),
                    'trades': total_trades
                })
        
        # Check that different parameters give different results
        assert len(results) > 1, "Not enough parameter combinations tested"
        final_values = [r['final_value'] for r in results]
        assert max(final_values) != min(final_values), "All parameter combinations gave same result"
        
        # Shorter fast periods should generate more trades
        fast_10_trades = [r['trades'] for r in results if r['fast_period'] == 10]
        fast_50_trades = [r['trades'] for r in results if r['fast_period'] == 50]
        
        if fast_10_trades and fast_50_trades:
            assert sum(fast_10_trades) > sum(fast_50_trades), "Shorter fast period didn't generate more trades"

class TestBollingerBreakout:
    def test_bollinger_breakout_strategy(self, volatile_data):
        """Test that Bollinger Breakout strategy triggers trades on breakouts"""
        cerebro = bt.Cerebro()
        data = TestData(volatile_data)
        cerebro.adddata(data)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Add Bollinger Breakout strategy
        cerebro.addstrategy(BollingerBreakoutStrategy, 
                          period=20, 
                          devfactor=2.0,
                          stop_loss=0.05,
                          take_profit=0.1)
        
        # Run with initial cash
        cerebro.broker.setcash(10000)
        cerebro.broker.setcommission(commission=0.001)
        
        results = cerebro.run()
        strategy = results[0]
        
        # Check that trades were executed
        trade_analysis = strategy.analyzers.trades.get_analysis()
        assert 'total' in trade_analysis
        assert trade_analysis['total']['total'] > 0, "No trades executed"
        
        # Strategy should have recorded trades
        assert strategy.num_trades > 0, "No trades recorded by strategy"
    
    def test_bollinger_parameters(self, volatile_data):
        """Test Bollinger strategy with different parameters"""
        # Test with different Bollinger parameters
        results = []
        
        for period in [10, 20, 30]:
            for devfactor in [1.5, 2.0, 2.5]:
                cerebro = bt.Cerebro()
                cerebro.adddata(TestData(volatile_data))
                cerebro.broker.setcash(10000)
                
                cerebro.addstrategy(BollingerBreakoutStrategy,
                                  period=period,
                                  devfactor=devfactor,
                                  stop_loss=0.05,
                                  take_profit=0.1)
                
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
                
                res = cerebro.run()
                strategy = res[0]
                
                trade_analysis = strategy.analyzers.trades.get_analysis()
                total_trades = trade_analysis.get('total', {}).get('total', 0)
                
                results.append({
                    'period': period,
                    'devfactor': devfactor,
                    'final_value': cerebro.broker.getvalue(),
                    'trades': total_trades
                })
        
        # Check that different parameters give different results
        assert len(results) > 1, "Not enough parameter combinations tested"
        
        # Narrower bands (smaller devfactor) should generate more trades
        narrow_trades = [r['trades'] for r in results if r['devfactor'] == 1.5]
        wide_trades = [r['trades'] for r in results if r['devfactor'] == 2.5]
        
        if narrow_trades and wide_trades:
            assert sum(narrow_trades) > sum(wide_trades), "Narrower bands didn't generate more trades"

class TestRsiMacd:
    def test_rsi_macd_strategy(self, oscillating_data):
        """Test that RSI+MACD strategy triggers trades on appropriate signals"""
        cerebro = bt.Cerebro()
        data = TestData(oscillating_data)
        cerebro.adddata(data)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Add RSI+MACD strategy
        cerebro.addstrategy(RsiMacdStrategy, 
                          rsi_period=14,
                          rsi_overbought=70,
                          rsi_oversold=30,
                          macd_fast=12,
                          macd_slow=26,
                          macd_signal=9,
                          stop_loss=0.05,
                          take_profit=0.1)
        
        # Run with initial cash
        cerebro.broker.setcash(10000)
        cerebro.broker.setcommission(commission=0.001)
        
        results = cerebro.run()
        strategy = results[0]
        
        # Check that trades were executed
        trade_analysis = strategy.analyzers.trades.get_analysis()
        assert 'total' in trade_analysis
        assert trade_analysis['total']['total'] > 0, "No trades executed"
    
    def test_rsi_macd_parameters(self, oscillating_data):
        """Test RSI+MACD strategy with different parameters"""
        # Test with different RSI and MACD parameters
        results = []
        
        for rsi_period in [7, 14, 21]:
            for macd_fast in [8, 12, 16]:
                cerebro = bt.Cerebro()
                cerebro.adddata(TestData(oscillating_data))
                cerebro.broker.setcash(10000)
                
                cerebro.addstrategy(RsiMacdStrategy,
                                  rsi_period=rsi_period,
                                  rsi_oversold=30,
                                  rsi_overbought=70,
                                  macd_fast=macd_fast,
                                  macd_slow=26,
                                  macd_signal=9,
                                  stop_loss=0.05,
                                  take_profit=0.1)
                
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
                
                res = cerebro.run()
                strategy = res[0]
                
                trade_analysis = strategy.analyzers.trades.get_analysis()
                total_trades = trade_analysis.get('total', {}).get('total', 0)
                
                results.append({
                    'rsi_period': rsi_period,
                    'macd_fast': macd_fast,
                    'final_value': cerebro.broker.getvalue(),
                    'trades': total_trades
                })
        
        # Check that different parameters give different results
        assert len(results) > 1, "Not enough parameter combinations tested"
        
        # Shorter RSI periods should generally be more sensitive
        short_rsi_trades = [r['trades'] for r in results if r['rsi_period'] == 7]
        long_rsi_trades = [r['trades'] for r in results if r['rsi_period'] == 21]
        
        if short_rsi_trades and long_rsi_trades:
            assert sum(short_rsi_trades) >= sum(long_rsi_trades), "Shorter RSI period didn't generate more trades"