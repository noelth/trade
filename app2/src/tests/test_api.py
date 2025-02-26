import pytest
import json
import time

def test_root_endpoint(client):
    """Test the root endpoint returns a 200 OK response"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_available_patterns_endpoint(client):
    """Test the available patterns endpoint returns a list of patterns"""
    response = client.get("/available-patterns")
    assert response.status_code == 200
    assert "patterns" in response.json()
    patterns = response.json()["patterns"]
    assert isinstance(patterns, list)
    # Check that at least some of our patterns are present
    assert "doji" in patterns
    assert "hammer" in patterns
    assert "engulfing" in patterns

def test_create_backtest_endpoint(client, candlestick_backtest_params):
    """Test creating a backtest returns a valid response with an ID"""
    response = client.post("/backtest", json=candlestick_backtest_params)
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "status" in result
    assert result["status"] in ["pending", "running"]
    assert result["ticker"] == candlestick_backtest_params["ticker"]
    assert result["strategy_type"] == candlestick_backtest_params["strategy_type"]

def test_get_backtest_status(client, candlestick_backtest_params):
    """Test we can get the status of a backtest after creating it"""
    # First create a backtest
    create_response = client.post("/backtest", json=candlestick_backtest_params)
    assert create_response.status_code == 200
    backtest_id = create_response.json()["id"]
    
    # Then get its status
    status_response = client.get(f"/backtest/{backtest_id}")
    assert status_response.status_code == 200
    result = status_response.json()
    assert result["id"] == backtest_id
    assert "status" in result
    
    # Status should be one of: pending, running, completed, failed
    assert result["status"] in ["pending", "running", "completed", "failed"]

def test_list_backtests(client, candlestick_backtest_params):
    """Test we can get a list of all backtests"""
    # First create a backtest
    client.post("/backtest", json=candlestick_backtest_params)
    
    # Then get the list
    response = client.get("/backtests")
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    # Make sure we have at least one backtest
    assert len(result) > 0
    
    # Check the structure of the first backtest
    backtest = result[0]
    assert "id" in backtest
    assert "status" in backtest
    assert "ticker" in backtest

def test_invalid_backtest_parameters(client):
    """Test that invalid backtest parameters return an appropriate error"""
    # Missing required fields
    invalid_params = {
        "ticker": "AAPL",
        # Missing start_date and end_date
        "timeframe": "1d",
        "strategy_type": "candlestick"
    }
    
    response = client.post("/backtest", json=invalid_params)
    assert response.status_code in [400, 422]  # Either a client error or validation error

def test_nonexistent_backtest_id(client):
    """Test that requesting a nonexistent backtest ID returns a 404"""
    response = client.get("/backtest/nonexistent-id")
    assert response.status_code == 404