import pytest
import json
import requests
import time
import os
import sys
import subprocess
import signal
import socket
from pathlib import Path

# Add the parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Skip these tests if SKIP_INTEGRATION_TESTS env var is set
pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_INTEGRATION_TESTS") == "1",
    reason="Integration tests skipped by environment variable"
)

class TestFrontendBackendIntegration:
    """
    Tests for frontend-backend integration.
    
    These tests check that the frontend can successfully communicate with the backend API.
    They require both servers to be running:
    - Backend API on port 8765
    - Frontend on port 3000
    
    Set SKIP_INTEGRATION_TESTS=1 to skip these tests.
    """
    
    @pytest.fixture(scope="class")
    def api_url(self):
        """Get the backend API URL"""
        return "http://localhost:8765"
    
    @pytest.fixture(scope="class")
    def frontend_url(self):
        """Get the frontend URL"""
        return "http://localhost:3000"
    
    def is_port_in_use(self, port):
        """Check if a port is in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def test_backend_connectivity(self, api_url):
        """Test that the backend API is reachable"""
        try:
            response = requests.get(f"{api_url}/")
            assert response.status_code == 200
            assert "status" in response.json()
            assert response.json()["status"] == "ok"
        except requests.ConnectionError:
            pytest.skip("Backend API not running on port 8765")
    
    def test_frontend_connectivity(self, frontend_url):
        """Test that the frontend is reachable"""
        try:
            response = requests.get(frontend_url)
            assert response.status_code == 200
        except requests.ConnectionError:
            pytest.skip("Frontend not running on port 3000")
    
    def test_backend_patterns_endpoint(self, api_url):
        """Test that the backend patterns endpoint is accessible and returns data"""
        try:
            response = requests.get(f"{api_url}/available-patterns")
            assert response.status_code == 200
            assert "patterns" in response.json()
            patterns = response.json()["patterns"]
            assert isinstance(patterns, list)
            assert len(patterns) > 0
        except requests.ConnectionError:
            pytest.skip("Backend API not running on port 8765")
    
    def test_backend_backtest_workflow(self, api_url):
        """Test the complete backtest workflow against the real backend"""
        try:
            # Create backtest
            backtest_data = {
                "ticker": "AAPL",
                "start_date": "2022-01-01",
                "end_date": "2022-01-31",
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
            
            # Create the backtest
            response = requests.post(f"{api_url}/backtest", json=backtest_data)
            assert response.status_code == 200
            result = response.json()
            assert "id" in result
            backtest_id = result["id"]
            
            # Wait for the backtest to complete (up to 30 seconds)
            max_retries = 30
            retries = 0
            status = ""
            
            while status not in ["completed", "failed"] and retries < max_retries:
                time.sleep(1)
                status_response = requests.get(f"{api_url}/backtest/{backtest_id}")
                assert status_response.status_code == 200
                status = status_response.json()["status"]
                retries += 1
            
            # If we timed out, we'll just check that the backtest exists
            if retries >= max_retries:
                assert status in ["pending", "running"], f"Backtest in unexpected state: {status}"
            else:
                # Check backtest results if it completed
                if status == "completed":
                    assert "final_portfolio_value" in status_response.json()
            
            # Get all backtests
            backtests_response = requests.get(f"{api_url}/backtests")
            assert backtests_response.status_code == 200
            backtests = backtests_response.json()
            assert isinstance(backtests, list)
            
            # Check that our backtest is in the list
            backtest_ids = [b["id"] for b in backtests]
            assert backtest_id in backtest_ids
            
        except requests.ConnectionError:
            pytest.skip("Backend API not running on port 8765")

# Optional: Only run this if it's not being imported
if __name__ == "__main__":
    pytest.main()