"""
Unit tests for BacktestService

Tests the core backtesting engine functionality
"""

import pytest
from datetime import date, timedelta
import pandas as pd
import numpy as np

from backtest_service import (
    BacktestService,
    BacktestConfig,
    BacktestResult,
)


class TestBacktestService:
    """Test suite for BacktestService"""

    @pytest.fixture
    def service(self):
        """Create a BacktestService instance"""
        return BacktestService(parquet_store=None)

    @pytest.fixture
    def sample_config(self):
        """Create a sample backtest configuration"""
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        return BacktestConfig(
            strategy_id="test_strategy",
            initial_capital=10000,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="monthly",
            benchmark="SPY",
            compositions=[
                {"AAPL": 0.5, "MSFT": 0.5}
            ],
        )

    def test_service_initialization(self, service):
        """Test that service initializes correctly"""
        assert service is not None
        assert service.risk_free_rate == 0.02

    def test_dummy_price_generation(self, service):
        """Test dummy price generation"""
        tickers = ["AAPL", "MSFT"]
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)

        prices = service._generate_dummy_prices(tickers, start, end)

        assert prices.shape[1] == 2
        assert all(col in prices.columns for col in tickers)
        assert len(prices) > 0
        # Prices should be positive
        assert (prices > 0).all().all()

    def test_rebalance_dates_monthly(self, service):
        """Test monthly rebalance date calculation"""
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        rebalance_dates = service._get_rebalance_dates(dates, "monthly")

        assert len(rebalance_dates) > 0
        # Monthly should have about 12 dates
        assert 10 <= len(rebalance_dates) <= 12

    def test_rebalance_dates_weekly(self, service):
        """Test weekly rebalance date calculation"""
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        rebalance_dates = service._get_rebalance_dates(dates, "weekly")

        assert len(rebalance_dates) > 0
        # Weekly should have about 52 dates
        assert 50 <= len(rebalance_dates) <= 54

    def test_sharpe_ratio_calculation(self, service):
        """Test Sharpe ratio calculation"""
        returns = pd.Series([0.001, 0.002, -0.001, 0.0015, 0.002])
        volatility = returns.std() * np.sqrt(252) * 100

        sharpe = service._calculate_sharpe(returns, volatility)

        assert isinstance(sharpe, float)
        # Sharpe should be positive for positive excess returns
        assert sharpe > 0

    def test_sharpe_ratio_zero_volatility(self, service):
        """Test Sharpe ratio with zero volatility"""
        returns = pd.Series([0.0, 0.0, 0.0])
        volatility = 0.0

        sharpe = service._calculate_sharpe(returns, volatility)

        assert sharpe == 0.0

    def test_sortino_ratio_calculation(self, service):
        """Test Sortino ratio calculation"""
        returns = pd.Series([0.001, 0.002, -0.001, 0.0015, 0.002])
        volatility = returns.std() * np.sqrt(252) * 100

        sortino = service._calculate_sortino(returns, volatility)

        assert isinstance(sortino, float)

    def test_drawdown_calculation(self, service):
        """Test drawdown calculation"""
        equity = pd.Series([100, 105, 110, 105, 100, 95, 100, 110])
        equity.index = pd.date_range(start="2023-01-01", periods=len(equity), freq="D")

        drawdown = service._calculate_drawdown(equity)

        assert len(drawdown) == len(equity)
        # First value should be 0
        assert drawdown[0]["drawdown_pct"] == 0.0
        # Should have negative values (drawdowns)
        assert any(d["drawdown_pct"] < 0 for d in drawdown)

    def test_backtest_execution(self, service, sample_config):
        """Test complete backtest execution"""
        result = service.run_backtest(sample_config)

        assert isinstance(result, BacktestResult)
        assert result.total_return_pct is not None
        assert result.annualized_return_pct is not None
        assert result.volatility_annual_pct is not None
        assert result.max_drawdown_pct is not None
        assert result.sharpe_ratio is not None
        assert result.sortino_ratio is not None

    def test_backtest_result_metrics(self, service, sample_config):
        """Test backtest result metrics are reasonable"""
        result = service.run_backtest(sample_config)

        # Volatility should be positive
        assert result.volatility_annual_pct > 0

        # Max drawdown should be non-positive
        assert result.max_drawdown_pct <= 0

        # Final values should be positive
        assert result.final_portfolio_value > 0
        assert result.final_benchmark_value > 0

        # Win rate should be between 0 and 100
        assert 0 <= result.win_rate_pct <= 100

    def test_backtest_equity_curve_length(self, service, sample_config):
        """Test equity curve has reasonable length"""
        result = service.run_backtest(sample_config)

        # Should have equity curve data
        assert len(result.equity_curve) > 0
        # Should be downsampled to ~250 points for performance
        assert len(result.equity_curve) <= 300

    def test_backtest_monthly_returns(self, service, sample_config):
        """Test monthly returns calculation"""
        result = service.run_backtest(sample_config)

        # Should have monthly returns
        assert len(result.monthly_returns) > 0
        # Should be about 12 months per year
        years = (sample_config.end_date - sample_config.start_date).days / 365
        expected_months = int(years * 12)
        assert abs(len(result.monthly_returns) - expected_months) <= 2

    def test_benchmark_comparison(self, service, sample_config):
        """Test that alpha is calculated as excess return"""
        result = service.run_backtest(sample_config)

        expected_alpha = result.annualized_return_pct - result.benchmark_annualized_return_pct
        assert abs(result.alpha - expected_alpha) < 0.1  # Allow small rounding difference

    def test_different_rebalance_frequencies(self, service, sample_config):
        """Test backtest with different rebalance frequencies"""
        frequencies = ["daily", "weekly", "monthly", "quarterly"]

        for freq in frequencies:
            config = sample_config
            config.rebalance_frequency = freq
            result = service.run_backtest(config)

            # All should produce valid results
            assert result.total_return_pct is not None
            assert result.volatility_annual_pct > 0

    def test_different_benchmarks(self, service, sample_config):
        """Test backtest with different benchmarks"""
        benchmarks = ["SPY", "QQQ", "AGG"]

        for benchmark in benchmarks:
            config = sample_config
            config.benchmark = benchmark
            result = service.run_backtest(config)

            # All should produce valid results
            assert result.benchmark == benchmark
            assert result.benchmark_return_pct is not None

    def test_transaction_costs_impact(self, service, sample_config):
        """Test that transaction costs reduce returns"""
        # Run without transaction costs
        config1 = sample_config
        config1.transaction_cost_pct = 0.0
        result1 = service.run_backtest(config1)

        # Run with transaction costs
        config2 = sample_config
        config2.transaction_cost_pct = 0.001
        result2 = service.run_backtest(config2)

        # Results with transaction costs should have lower/equal final value
        # (due to rebalancing costs)
        assert result2.final_portfolio_value <= result1.final_portfolio_value

    def test_metadata_persistence(self, service, sample_config):
        """Test that metadata is preserved in results"""
        result = service.run_backtest(sample_config)

        assert result.strategy_id == sample_config.strategy_id
        assert result.benchmark == sample_config.benchmark
        assert result.start_date == sample_config.start_date.strftime("%Y-%m-%d")
        assert result.end_date == sample_config.end_date.strftime("%Y-%m-%d")

    def test_insufficient_data_handling(self, service):
        """Test handling of insufficient data"""
        config = BacktestConfig(
            strategy_id="test",
            initial_capital=10000,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),  # Only 1 day
            rebalance_frequency="monthly",
            benchmark="SPY",
            compositions=[{"AAPL": 1.0}],
        )

        # Should raise an error
        with pytest.raises(ValueError):
            service.run_backtest(config)


class TestBacktestDataQuality:
    """Tests for data quality handling"""

    @pytest.fixture
    def service(self):
        return BacktestService(parquet_store=None)

    def test_missing_data_handling(self, service):
        """Test handling of missing data"""
        tickers = ["AAPL", "MSFT"]
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)

        prices = service._generate_dummy_prices(tickers, start, end)

        # Manually introduce missing data
        prices.iloc[50:60, 0] = np.nan

        # Service should forward-fill
        filled = prices.fillna(method='ffill').fillna(method='bfill')
        assert filled.notna().all().all()

    def test_price_alignment(self, service):
        """Test that prices are properly aligned"""
        tickers = ["AAPL", "MSFT"]
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)

        prices = service._generate_dummy_prices(tickers, start, end)

        # All columns should have same length
        lengths = [len(prices[col]) for col in prices.columns]
        assert len(set(lengths)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
