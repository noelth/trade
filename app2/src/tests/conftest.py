import os
import sys
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Add the parent directory to path so we can import from the main app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
load_dotenv()

from api import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def test_ticker():
    """Return a common test ticker for all tests"""
    return "AAPL"

@pytest.fixture
def test_date_range():
    """Return a common test date range for all tests"""
    return {
        "start_date": "2022-01-01",
        "end_date": "2022-01-31"
    }

@pytest.fixture
def candlestick_backtest_params(test_ticker, test_date_range):
    """Return a set of parameters for testing a candlestick backtest"""
    return {
        "ticker": test_ticker,
        "start_date": test_date_range["start_date"],
        "end_date": test_date_range["end_date"],
        "timeframe": "1d",
        "principal": 10000.0,
        "commission": 0.0003,
        "strategy_type": "candlestick",
        "strategy_params": {
            "patterns": ["doji", "hammer"],
            "pattern_params": {},
            "stop_loss": 0.05,
            "take_profit": 0.10,
            "consecutive_bars": 1,
            "exit_on_opposite": True
        }
    }

@pytest.fixture
def sma_backtest_params(test_ticker, test_date_range):
    """Return a set of parameters for testing an SMA backtest"""
    return {
        "ticker": test_ticker,
        "start_date": test_date_range["start_date"],
        "end_date": test_date_range["end_date"],
        "timeframe": "1d",
        "principal": 10000.0,
        "commission": 0.0003,
        "strategy_type": "sma_cross",
        "strategy_params": {
            "sma_fast_period": 50,
            "sma_slow_period": 200,
            "take_profit": 0.10
        }
    }

@pytest.fixture
def bollinger_backtest_params(test_ticker, test_date_range):
    """Return a set of parameters for testing a Bollinger Bands backtest"""
    return {
        "ticker": test_ticker,
        "start_date": test_date_range["start_date"],
        "end_date": test_date_range["end_date"],
        "timeframe": "1d",
        "principal": 10000.0,
        "commission": 0.0003,
        "strategy_type": "bollinger_breakout",
        "strategy_params": {
            "period": 20,
            "devfactor": 2.0,
            "stop_loss": 0.05,
            "take_profit": 0.10
        }
    }