"""
MarketGPS Advanced Risk Metrics Calculator.

Professional-grade risk metrics for portfolio and asset analysis.
Handles edge cases gracefully and returns None for insufficient data.
"""

from typing import Optional
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RiskMetrics:
    """
    Advanced risk metrics calculator.

    Provides institutional-grade risk metrics including Sharpe/Sortino ratios,
    VaR, CVaR, maximum drawdown duration, and correlation-based metrics.
    All methods handle edge cases gracefully without raising exceptions.
    """

    @staticmethod
    def sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.05
    ) -> Optional[float]:
        """
        Calculate Sharpe Ratio.

        Measures excess return per unit of risk (volatility).

        Args:
            returns: Series of returns (as decimals, e.g., 0.01 for 1%)
            risk_free_rate: Annual risk-free rate (default: 5%)

        Returns:
            Sharpe ratio, or None if insufficient data
        """
        if returns is None or len(returns) < 2:
            return None

        try:
            returns = returns.dropna()

            if len(returns) < 2:
                return None

            # Annualize assuming daily returns
            excess_return = returns.mean() * 252 - risk_free_rate
            volatility = returns.std() * np.sqrt(252)

            if volatility == 0 or np.isnan(volatility):
                return None

            sharpe = excess_return / volatility
            return float(sharpe) if np.isfinite(sharpe) else None

        except Exception as e:
            logger.debug(f"Sharpe ratio calculation failed: {e}")
            return None

    @staticmethod
    def sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.05
    ) -> Optional[float]:
        """
        Calculate Sortino Ratio.

        Like Sharpe, but only penalizes downside volatility (downside deviation).
        More meaningful for asymmetric return distributions.

        Args:
            returns: Series of returns (as decimals)
            risk_free_rate: Annual risk-free rate (default: 5%)

        Returns:
            Sortino ratio, or None if insufficient data
        """
        if returns is None or len(returns) < 2:
            return None

        try:
            returns = returns.dropna()

            if len(returns) < 2:
                return None

            # Annualized excess return
            excess_return = returns.mean() * 252 - risk_free_rate

            # Downside deviation (only negative returns)
            negative_returns = returns[returns < 0]

            if len(negative_returns) == 0:
                # No downside volatility means all positive returns
                return float("inf") if excess_return > 0 else 0.0

            downside_deviation = negative_returns.std() * np.sqrt(252)

            if downside_deviation == 0 or np.isnan(downside_deviation):
                return None

            sortino = excess_return / downside_deviation
            return float(sortino) if np.isfinite(sortino) else None

        except Exception as e:
            logger.debug(f"Sortino ratio calculation failed: {e}")
            return None

    @staticmethod
    def calmar_ratio(
        returns: pd.Series,
        max_drawdown: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate Calmar Ratio.

        Annual return divided by maximum drawdown.
        Higher is better (more return, less downside).

        Args:
            returns: Series of returns (as decimals)
            max_drawdown: Pre-calculated maximum drawdown (as decimal).
                         If None, calculated from returns.

        Returns:
            Calmar ratio, or None if insufficient data
        """
        if returns is None or len(returns) < 2:
            return None

        try:
            returns = returns.dropna()

            if len(returns) < 2:
                return None

            # Annual return
            annual_return = returns.mean() * 252

            # Max drawdown
            if max_drawdown is None:
                max_drawdown = RiskMetrics.maximum_drawdown(returns)

            if max_drawdown is None or max_drawdown == 0:
                return None

            calmar = annual_return / abs(max_drawdown)
            return float(calmar) if np.isfinite(calmar) else None

        except Exception as e:
            logger.debug(f"Calmar ratio calculation failed: {e}")
            return None

    @staticmethod
    def beta(
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> Optional[float]:
        """
        Calculate Beta (systematic risk).

        Measures asset's volatility relative to the market.
        Beta = 1: moves with market
        Beta > 1: more volatile than market
        Beta < 1: less volatile than market

        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns (e.g., S&P 500)

        Returns:
            Beta, or None if insufficient data
        """
        if (asset_returns is None or market_returns is None or
            len(asset_returns) < 10 or len(market_returns) < 10):
            return None

        try:
            # Align series by index
            combined = pd.DataFrame({
                'asset': asset_returns,
                'market': market_returns
            })
            combined = combined.dropna()

            if len(combined) < 10:
                return None

            asset = combined['asset'].values
            market = combined['market'].values

            # Covariance matrix
            cov_matrix = np.cov(asset, market)
            market_variance = cov_matrix[1, 1]

            if market_variance == 0 or np.isnan(market_variance):
                return None

            # Beta = covariance(asset, market) / variance(market)
            beta = cov_matrix[0, 1] / market_variance

            return float(beta) if np.isfinite(beta) else None

        except Exception as e:
            logger.debug(f"Beta calculation failed: {e}")
            return None

    @staticmethod
    def information_ratio(
        asset_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Optional[float]:
        """
        Calculate Information Ratio.

        Measures active return per unit of active risk (tracking error).
        Useful for evaluating active managers vs. benchmark.

        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns

        Returns:
            Information ratio, or None if insufficient data
        """
        if (asset_returns is None or benchmark_returns is None or
            len(asset_returns) < 10 or len(benchmark_returns) < 10):
            return None

        try:
            # Align series by index
            combined = pd.DataFrame({
                'asset': asset_returns,
                'benchmark': benchmark_returns
            })
            combined = combined.dropna()

            if len(combined) < 10:
                return None

            # Calculate excess returns (active returns)
            active_returns = combined['asset'] - combined['benchmark']

            # Active return (mean)
            mean_active = active_returns.mean() * 252

            # Tracking error (std of active returns)
            tracking_error = active_returns.std() * np.sqrt(252)

            if tracking_error == 0 or np.isnan(tracking_error):
                return None

            ir = mean_active / tracking_error
            return float(ir) if np.isfinite(ir) else None

        except Exception as e:
            logger.debug(f"Information ratio calculation failed: {e}")
            return None

    @staticmethod
    def value_at_risk(
        returns: pd.Series,
        confidence: float = 0.95
    ) -> Optional[float]:
        """
        Calculate Value at Risk (VaR) - Historical method.

        The maximum loss at a given confidence level over a time period.
        E.g., 95% VaR of -0.05 means 95% chance of not losing more than 5%.

        Args:
            returns: Series of returns (as decimals)
            confidence: Confidence level (default: 0.95 for 95%)

        Returns:
            VaR as decimal (e.g., -0.05 for 5% loss), or None
        """
        if returns is None or len(returns) < 20:
            return None

        try:
            returns = returns.dropna()

            if len(returns) < 20:
                return None

            # Historical percentile method
            var = np.percentile(returns, (1 - confidence) * 100)

            return float(var) if np.isfinite(var) else None

        except Exception as e:
            logger.debug(f"VaR calculation failed: {e}")
            return None

    @staticmethod
    def conditional_var(
        returns: pd.Series,
        confidence: float = 0.95
    ) -> Optional[float]:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.

        Average loss in the worst (1 - confidence) percent of cases.
        More conservative than VaR.

        Args:
            returns: Series of returns (as decimals)
            confidence: Confidence level (default: 0.95 for 95%)

        Returns:
            CVaR as decimal, or None
        """
        if returns is None or len(returns) < 20:
            return None

        try:
            returns = returns.dropna()

            if len(returns) < 20:
                return None

            # Calculate VaR first
            var_threshold = np.percentile(returns, (1 - confidence) * 100)

            # CVaR is the mean of returns worse than VaR
            worst_returns = returns[returns <= var_threshold]

            if len(worst_returns) == 0:
                return float(var_threshold)

            cvar = worst_returns.mean()

            return float(cvar) if np.isfinite(cvar) else None

        except Exception as e:
            logger.debug(f"CVaR calculation failed: {e}")
            return None

    @staticmethod
    def maximum_drawdown(returns: pd.Series) -> Optional[float]:
        """
        Calculate maximum drawdown.

        The largest peak-to-trough decline from historical peak.

        Args:
            returns: Series of returns (as decimals)

        Returns:
            Maximum drawdown as decimal (e.g., -0.25 for 25%), or None
        """
        if returns is None or len(returns) < 2:
            return None

        try:
            returns = returns.dropna()

            if len(returns) < 2:
                return None

            # Convert returns to cumulative growth
            cumulative = (1 + returns).cumprod()

            # Running maximum
            running_max = cumulative.expanding().max()

            # Drawdown at each point
            drawdown = (cumulative - running_max) / running_max

            # Maximum drawdown
            max_dd = drawdown.min()

            return float(max_dd) if np.isfinite(max_dd) else None

        except Exception as e:
            logger.debug(f"Maximum drawdown calculation failed: {e}")
            return None

    @staticmethod
    def maximum_drawdown_duration(prices: pd.Series) -> Optional[int]:
        """
        Calculate duration of maximum drawdown in days.

        The number of trading days from peak to trough in the longest drawdown.

        Args:
            prices: Series of prices (daily closing prices)

        Returns:
            Number of days, or None if insufficient data
        """
        if prices is None or len(prices) < 2:
            return None

        try:
            prices = prices.dropna()

            if len(prices) < 2:
                return None

            # Running maximum
            running_max = prices.expanding().max()

            # Identify when we're in a drawdown (below running max)
            in_drawdown = prices < running_max

            # Find all drawdown periods
            drawdown_durations = []
            current_duration = 0
            max_idx = 0

            for i, (price, below_max) in enumerate(zip(prices, in_drawdown)):
                if below_max:
                    current_duration += 1
                else:
                    if current_duration > 0:
                        drawdown_durations.append(current_duration)
                    current_duration = 0

            # Don't forget the last period if it's still in drawdown
            if current_duration > 0:
                drawdown_durations.append(current_duration)

            if not drawdown_durations:
                return 0

            return int(max(drawdown_durations))

        except Exception as e:
            logger.debug(f"Maximum drawdown duration calculation failed: {e}")
            return None
