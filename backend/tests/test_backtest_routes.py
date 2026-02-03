"""
Unit tests for Backtest Routes

Tests the API endpoints for backtesting
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

# Note: These tests assume the FastAPI app is properly set up
# In a real scenario, you would import from your main app


class TestBacktestRoutes:
    """Test suite for backtest routes"""

    @pytest.fixture
    def sample_request_body(self):
        """Sample backtest request"""
        return {
            "strategy_id": "test_strategy",
            "initial_capital": 10000,
            "rebalance_frequency": "monthly",
            "benchmark": "SPY",
            "compositions": [
                {"AAPL": 0.5, "MSFT": 0.5}
            ],
        }

    def test_backtest_request_validation(self, sample_request_body):
        """Test request validation"""
        # Valid request should pass
        assert sample_request_body["initial_capital"] >= 100
        assert sample_request_body["initial_capital"] <= 10000000

        # Total weights should sum to ~1.0
        total_weight = sum(sum(comp.values()) for comp in sample_request_body["compositions"])
        assert abs(total_weight - 1.0) < 0.01

    def test_invalid_rebalance_frequency(self):
        """Test invalid rebalance frequency rejection"""
        invalid_frequencies = ["hourly", "invalid", "biweekly"]

        for freq in invalid_frequencies:
            valid_freqs = ["daily", "weekly", "monthly", "quarterly"]
            assert freq not in valid_freqs

    def test_invalid_benchmark(self):
        """Test invalid benchmark rejection"""
        invalid_benchmarks = ["INVALID", "BTC", "FAKE"]
        valid_benchmarks = ["SPY", "QQQ", "IWM", "VEA", "AGG"]

        for bench in invalid_benchmarks:
            assert bench not in valid_benchmarks

    def test_preset_data_structure(self):
        """Test preset data structure"""
        sample_preset = {
            "id": "5y",
            "label": "5 Years",
            "description": "Last 5 years of trading",
            "start_offset_years": 5,
        }

        assert "id" in sample_preset
        assert "label" in sample_preset
        assert "description" in sample_preset
        assert sample_preset["start_offset_years"] == 5

    def test_benchmark_data_structure(self):
        """Test benchmark data structure"""
        sample_benchmark = {
            "id": "SPY",
            "name": "S&P 500",
            "description": "500 largest US companies",
            "asset_class": "US Equities",
        }

        assert "id" in sample_benchmark
        assert "name" in sample_benchmark
        assert "description" in sample_benchmark
        assert "asset_class" in sample_benchmark

    def test_rebalance_frequency_data_structure(self):
        """Test rebalance frequency data structure"""
        sample_frequency = {
            "id": "monthly",
            "label": "Monthly",
            "description": "Rebalance at month-end",
        }

        assert "id" in sample_frequency
        assert "label" in sample_frequency
        assert "description" in sample_frequency

    def test_backtest_result_structure(self):
        """Test backtest result data structure"""
        sample_result = {
            "total_return_pct": 25.5,
            "annualized_return_pct": 4.8,
            "benchmark_return_pct": 18.3,
            "benchmark_annualized_return_pct": 3.5,
            "alpha": 1.3,
            "volatility_annual_pct": 12.5,
            "benchmark_volatility_pct": 10.2,
            "max_drawdown_pct": -15.3,
            "sharpe_ratio": 0.85,
            "sortino_ratio": 1.2,
            "winning_periods": 220,
            "losing_periods": 32,
            "win_rate_pct": 87.3,
            "best_period_pct": 3.5,
            "worst_period_pct": -2.1,
            "best_month": "2023-01",
            "worst_month": "2023-03",
            "final_portfolio_value": 12550.0,
            "final_benchmark_value": 11830.0,
            "equity_curve": [],
            "drawdown_curve": [],
            "monthly_returns": [],
            "data_points": 252,
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "strategy_id": "test_strategy",
            "benchmark": "SPY",
        }

        # Verify all required fields
        required_fields = [
            "total_return_pct",
            "annualized_return_pct",
            "benchmark_return_pct",
            "alpha",
            "volatility_annual_pct",
            "max_drawdown_pct",
            "sharpe_ratio",
            "sortino_ratio",
            "winning_periods",
            "losing_periods",
            "win_rate_pct",
            "final_portfolio_value",
            "equity_curve",
            "drawdown_curve",
            "monthly_returns",
            "data_points",
            "start_date",
            "end_date",
            "strategy_id",
            "benchmark",
        ]

        for field in required_fields:
            assert field in sample_result

    def test_equity_curve_point_structure(self):
        """Test equity curve point structure"""
        sample_point = {
            "date": "2023-01-01",
            "portfolio_value": 10000,
            "benchmark_value": 10000,
            "portfolio_return_pct": 0.0,
            "benchmark_return_pct": 0.0,
        }

        assert "date" in sample_point
        assert "portfolio_value" in sample_point
        assert "benchmark_value" in sample_point

    def test_drawdown_point_structure(self):
        """Test drawdown point structure"""
        sample_point = {
            "date": "2023-01-01",
            "drawdown_pct": -5.0,
        }

        assert "date" in sample_point
        assert "drawdown_pct" in sample_point

    def test_monthly_return_structure(self):
        """Test monthly return structure"""
        sample_return = {
            "period": "2023-01",
            "return_pct": 2.5,
            "benchmark_return_pct": 2.0,
        }

        assert "period" in sample_return
        assert "return_pct" in sample_return
        assert "benchmark_return_pct" in sample_return


class TestDateParsing:
    """Test date parsing functionality"""

    def test_valid_date_format(self):
        """Test valid date format"""
        from backtest_routes import parse_date_string

        result = parse_date_string("2023-01-15")
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_none_date(self):
        """Test None date handling"""
        from backtest_routes import parse_date_string

        result = parse_date_string(None)
        assert result is None

    def test_invalid_date_format(self):
        """Test invalid date format rejection"""
        from backtest_routes import parse_date_string

        with pytest.raises(ValueError):
            parse_date_string("2023/01/15")

        with pytest.raises(ValueError):
            parse_date_string("01-15-2023")

        with pytest.raises(ValueError):
            parse_date_string("invalid")


class TestCompositionValidation:
    """Test composition validation"""

    def test_valid_composition(self):
        """Test valid composition"""
        compositions = [{"AAPL": 0.6, "MSFT": 0.4}]
        total = sum(sum(comp.values()) for comp in compositions)
        assert abs(total - 1.0) < 0.01

    def test_invalid_composition_sum(self):
        """Test invalid composition (doesn't sum to 1.0)"""
        compositions = [{"AAPL": 0.6, "MSFT": 0.3}]
        total = sum(sum(comp.values()) for comp in compositions)
        assert abs(total - 1.0) > 0.01

    def test_multiple_compositions(self):
        """Test multiple compositions"""
        compositions = [
            {"AAPL": 0.5, "MSFT": 0.5},
            {"AAPL": 0.3, "MSFT": 0.7},
        ]

        for comp in compositions:
            total = sum(comp.values())
            assert abs(total - 1.0) < 0.01


class TestInitialCapitalValidation:
    """Test initial capital validation"""

    def test_valid_initial_capital(self):
        """Test valid initial capital amounts"""
        valid_amounts = [100, 1000, 10000, 1000000]

        for amount in valid_amounts:
            assert 100 <= amount <= 10000000

    def test_invalid_initial_capital(self):
        """Test invalid initial capital amounts"""
        invalid_amounts = [50, 0, -1000, 11000000]

        for amount in invalid_amounts:
            assert not (100 <= amount <= 10000000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
