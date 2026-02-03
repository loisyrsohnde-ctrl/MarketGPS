"""
Backtesting Service for MarketGPS

Provides a comprehensive backtesting engine for investment strategies on historical data.
Supports:
- Multiple rebalancing frequencies (daily, weekly, monthly, quarterly)
- Performance metrics (returns, volatility, Sharpe, Sortino, drawdown)
- Benchmark comparison (SPY, QQQ, IWM, VEA, AGG)
- Transaction costs modeling
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""
    strategy_id: str
    initial_capital: float
    start_date: date
    end_date: date
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    transaction_cost_pct: float = 0.001  # 0.1% per transaction
    benchmark: str = "SPY"  # Benchmark ticker
    compositions: List[Dict[str, float]] = field(default_factory=list)  # [{ticker: weight}]


@dataclass
class EquityCurvePoint:
    """Single point in equity curve."""
    date: str
    portfolio_value: float
    benchmark_value: float
    portfolio_return_pct: float
    benchmark_return_pct: float
    drawdown_pct: float


@dataclass
class MonthlyReturn:
    """Monthly return data."""
    period: str  # YYYY-MM
    return_pct: float
    benchmark_return_pct: float


@dataclass
class BacktestResult:
    """Complete backtest results."""
    # Performance metrics
    total_return_pct: float
    annualized_return_pct: float
    benchmark_return_pct: float
    benchmark_annualized_return_pct: float
    alpha: float  # Excess return vs benchmark

    # Risk metrics
    volatility_annual_pct: float
    benchmark_volatility_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float

    # Win/loss statistics
    winning_periods: int
    losing_periods: int
    win_rate_pct: float
    best_period_pct: float
    worst_period_pct: float
    best_month: str
    worst_month: str

    # Final values
    final_portfolio_value: float
    final_benchmark_value: float

    # Time series data
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    monthly_returns: List[Dict[str, Any]]

    # Metadata
    data_points: int
    start_date: str
    end_date: str
    strategy_id: str
    benchmark: str


class BacktestService:
    """Main backtesting engine."""

    def __init__(self, parquet_store=None):
        """
        Initialize backtesting service.

        Args:
            parquet_store: ParquetStore instance for loading historical data
        """
        self.parquet = parquet_store
        self.risk_free_rate = 0.02  # 2% annual

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """
        Execute a complete backtest.

        Args:
            config: BacktestConfig with strategy parameters

        Returns:
            BacktestResult with full performance metrics
        """
        try:
            # Get price data
            portfolio_prices = self._get_historical_prices(
                list(config.compositions[0].keys()),
                config.start_date,
                config.end_date
            )

            benchmark_prices = self._get_historical_prices(
                [config.benchmark],
                config.start_date,
                config.end_date
            )

            # Align dates
            common_dates = portfolio_prices.index.intersection(benchmark_prices.index)
            portfolio_prices = portfolio_prices.loc[common_dates].copy()
            benchmark_prices = benchmark_prices.loc[common_dates].copy()

            if len(portfolio_prices) < 2:
                raise ValueError("Insufficient data for backtest")

            # Calculate portfolio values
            portfolio_values = self._calculate_portfolio_value(
                config.compositions,
                portfolio_prices,
                config.initial_capital,
                config.rebalance_frequency,
                config.transaction_cost_pct
            )

            benchmark_values = self._calculate_benchmark_value(
                benchmark_prices,
                config.initial_capital
            )

            # Align series
            portfolio_values = portfolio_values[portfolio_values.index.isin(benchmark_values.index)]
            benchmark_values = benchmark_values[benchmark_values.index.isin(portfolio_values.index)]

            # Calculate returns
            portfolio_returns = portfolio_values.pct_change().dropna()
            benchmark_returns = benchmark_values.pct_change().dropna()

            # Build equity curve
            equity_curve = self._build_equity_curve(
                portfolio_values,
                benchmark_values,
                portfolio_returns,
                benchmark_returns
            )

            # Calculate drawdown
            drawdown_curve = self._calculate_drawdown(portfolio_values)

            # Calculate monthly returns
            monthly_returns = self._calculate_monthly_returns(
                portfolio_values,
                benchmark_values
            )

            # Calculate metrics
            total_return = (portfolio_values.iloc[-1] / config.initial_capital - 1) * 100
            bench_total_return = (benchmark_values.iloc[-1] / config.initial_capital - 1) * 100

            num_years = len(portfolio_values) / 252  # Trading days per year
            ann_return = (((portfolio_values.iloc[-1] / config.initial_capital) ** (1/num_years)) - 1) * 100
            ann_bench_return = (((benchmark_values.iloc[-1] / config.initial_capital) ** (1/num_years)) - 1) * 100

            volatility = portfolio_returns.std() * np.sqrt(252) * 100
            bench_volatility = benchmark_returns.std() * np.sqrt(252) * 100

            max_dd = drawdown_curve['drawdown_pct'].min()

            sharpe = self._calculate_sharpe(portfolio_returns, volatility)
            sortino = self._calculate_sortino(portfolio_returns, volatility)

            # Win rate
            winning = (portfolio_returns > 0).sum()
            losing = (portfolio_returns <= 0).sum()
            win_rate = (winning / len(portfolio_returns) * 100) if len(portfolio_returns) > 0 else 0

            best_period = portfolio_returns.max() * 100
            worst_period = portfolio_returns.min() * 100

            # Monthly stats
            best_month = monthly_returns.loc[monthly_returns['return_pct'].idxmax()] if len(monthly_returns) > 0 else None
            worst_month = monthly_returns.loc[monthly_returns['return_pct'].idxmin()] if len(monthly_returns) > 0 else None

            result = BacktestResult(
                total_return_pct=total_return,
                annualized_return_pct=ann_return,
                benchmark_return_pct=bench_total_return,
                benchmark_annualized_return_pct=ann_bench_return,
                alpha=ann_return - ann_bench_return,
                volatility_annual_pct=volatility,
                benchmark_volatility_pct=bench_volatility,
                max_drawdown_pct=max_dd,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                winning_periods=int(winning),
                losing_periods=int(losing),
                win_rate_pct=win_rate,
                best_period_pct=best_period,
                worst_period_pct=worst_period,
                best_month=best_month['period'] if best_month is not None else "",
                worst_month=worst_month['period'] if worst_month is not None else "",
                final_portfolio_value=float(portfolio_values.iloc[-1]),
                final_benchmark_value=float(benchmark_values.iloc[-1]),
                equity_curve=equity_curve,
                drawdown_curve=drawdown_curve,
                monthly_returns=[m.to_dict() if hasattr(m, 'to_dict') else m for m in monthly_returns.to_dict('records')],
                data_points=len(portfolio_values),
                start_date=portfolio_values.index[0].strftime('%Y-%m-%d'),
                end_date=portfolio_values.index[-1].strftime('%Y-%m-%d'),
                strategy_id=config.strategy_id,
                benchmark=config.benchmark,
            )

            return result

        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}", exc_info=True)
            raise

    def _get_historical_prices(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Load historical price data from parquet store.

        Args:
            tickers: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with dates as index and tickers as columns
        """
        try:
            if not self.parquet:
                logger.warning("Parquet store not available, returning dummy data")
                return self._generate_dummy_prices(tickers, start_date, end_date)

            # Load OHLCV data from parquet
            dfs = []
            for ticker in tickers:
                try:
                    df = self.parquet.read(f"prices/{ticker}.parquet")
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                    else:
                        df.index = pd.to_datetime(df.index)

                    # Filter by date range
                    df = df[(df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))]

                    # Use close price
                    if 'close' in df.columns:
                        dfs.append(df[['close']].rename(columns={'close': ticker}))
                    elif 'Close' in df.columns:
                        dfs.append(df[['Close']].rename(columns={'Close': ticker}))
                except Exception as e:
                    logger.warning(f"Could not load {ticker}: {e}")
                    continue

            if not dfs:
                return self._generate_dummy_prices(tickers, start_date, end_date)

            result = pd.concat(dfs, axis=1)
            result = result.fillna(method='ffill').fillna(method='bfill')
            return result

        except Exception as e:
            logger.warning(f"Error loading prices: {e}, using dummy data")
            return self._generate_dummy_prices(tickers, start_date, end_date)

    def _generate_dummy_prices(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Generate dummy price data for testing."""
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        data = {}

        np.random.seed(42)
        for ticker in tickers:
            # Generate random walk
            returns = np.random.normal(0.0005, 0.015, len(date_range))
            prices = 100 * np.exp(np.cumsum(returns))
            data[ticker] = prices

        return pd.DataFrame(data, index=date_range)

    def _calculate_portfolio_value(
        self,
        compositions: List[Dict[str, float]],
        prices: pd.DataFrame,
        initial_capital: float,
        rebalance_frequency: str,
        transaction_cost_pct: float
    ) -> pd.Series:
        """
        Calculate portfolio value over time with rebalancing.

        Args:
            compositions: List of {ticker: weight} dicts
            prices: Price data
            initial_capital: Starting amount
            rebalance_frequency: How often to rebalance
            transaction_cost_pct: Cost per transaction

        Returns:
            Series of portfolio values
        """
        if not compositions:
            return pd.Series(initial_capital, index=prices.index)

        weights = compositions[0]  # Use first composition for now

        # Get rebalance dates
        rebalance_dates = self._get_rebalance_dates(prices.index, rebalance_frequency)

        portfolio_values = []
        current_value = initial_capital
        shares = {}

        # Initialize shares
        for ticker, weight in weights.items():
            if ticker in prices.columns:
                initial_price = prices[ticker].iloc[0]
                shares[ticker] = (current_value * weight) / initial_price

        for i, date in enumerate(prices.index):
            # Calculate current portfolio value
            value = 0
            for ticker, count in shares.items():
                if ticker in prices.columns:
                    value += count * prices[ticker].iloc[i]

            # Rebalance if needed
            if date in rebalance_dates and i > 0:
                # Incur transaction costs
                value *= (1 - transaction_cost_pct)

                # Rebalance to target weights
                for ticker, weight in weights.items():
                    if ticker in prices.columns:
                        target_value = value * weight
                        price = prices[ticker].iloc[i]
                        shares[ticker] = target_value / price

            portfolio_values.append(value)

        return pd.Series(portfolio_values, index=prices.index)

    def _calculate_benchmark_value(
        self,
        prices: pd.DataFrame,
        initial_capital: float
    ) -> pd.Series:
        """
        Calculate benchmark portfolio value (buy and hold).

        Args:
            prices: Price data with benchmark ticker
            initial_capital: Starting amount

        Returns:
            Series of benchmark values
        """
        ticker = prices.columns[0]
        initial_price = prices[ticker].iloc[0]
        shares = initial_capital / initial_price

        return shares * prices[ticker]

    def _calculate_drawdown(self, equity_curve: pd.Series) -> List[Dict[str, Any]]:
        """
        Calculate drawdown from peak.

        Args:
            equity_curve: Series of portfolio values

        Returns:
            List of {date, drawdown_pct} dicts
        """
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100

        result = []
        for date, dd in drawdown.items():
            result.append({
                'date': date.strftime('%Y-%m-%d'),
                'drawdown_pct': float(dd)
            })

        return result

    def _build_equity_curve(
        self,
        portfolio_values: pd.Series,
        benchmark_values: pd.Series,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> List[Dict[str, Any]]:
        """Build equity curve data points."""
        result = []

        for i, (date, pv) in enumerate(portfolio_values.items()):
            if i == 0:
                p_ret = 0
                b_ret = 0
            else:
                p_ret = portfolio_returns.iloc[i-1] * 100 if i > 0 else 0
                b_ret = benchmark_returns.iloc[i-1] * 100 if i > 0 else 0

            result.append({
                'date': date.strftime('%Y-%m-%d'),
                'portfolio_value': float(pv),
                'benchmark_value': float(benchmark_values.iloc[i]),
                'portfolio_return_pct': float(p_ret),
                'benchmark_return_pct': float(b_ret),
            })

        # Downsample to monthly for performance
        if len(result) > 252:
            result = result[::max(1, len(result) // 252)]

        return result

    def _calculate_monthly_returns(
        self,
        portfolio_values: pd.Series,
        benchmark_values: pd.Series
    ) -> pd.DataFrame:
        """Calculate returns for each month."""
        # Resample to monthly
        portfolio_monthly = portfolio_values.resample('M').last()
        benchmark_monthly = benchmark_values.resample('M').last()

        portfolio_monthly_returns = portfolio_monthly.pct_change() * 100
        benchmark_monthly_returns = benchmark_monthly.pct_change() * 100

        result = []
        for date, pret in portfolio_monthly_returns.items():
            if pd.notna(pret):
                bret = benchmark_monthly_returns.loc[date]
                result.append({
                    'period': date.strftime('%Y-%m'),
                    'return_pct': float(pret),
                    'benchmark_return_pct': float(bret),
                })

        return pd.DataFrame(result)

    def _get_rebalance_dates(
        self,
        dates: pd.DatetimeIndex,
        frequency: str
    ) -> set:
        """Get dates when rebalancing occurs."""
        rebalance_dates = set()

        if frequency == "daily":
            rebalance_dates = set(dates)
        elif frequency == "weekly":
            rebalance_dates = set(dates[dates.dayofweek == 0])  # Mondays
        elif frequency == "monthly":
            rebalance_dates = set(dates[dates.is_month_end])
        elif frequency == "quarterly":
            rebalance_dates = set(dates[dates.is_quarter_end])

        return rebalance_dates

    def _calculate_sharpe(
        self,
        returns: pd.Series,
        volatility: float,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: Daily returns series
            volatility: Annual volatility percentage
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        if volatility == 0:
            return 0.0

        excess_return = (returns.mean() * 252 * 100) - (risk_free_rate * 100)
        return excess_return / volatility if volatility > 0 else 0.0

    def _calculate_sortino(
        self,
        returns: pd.Series,
        volatility: float,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sortino ratio (downside volatility only).

        Args:
            returns: Daily returns series
            volatility: Annual volatility percentage (unused, for compatibility)
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        # Calculate downside volatility
        downside_returns = returns[returns < 0]
        downside_variance = (downside_returns ** 2).mean()
        downside_volatility = np.sqrt(downside_variance) * np.sqrt(252) * 100

        if downside_volatility == 0:
            return 0.0

        excess_return = (returns.mean() * 252 * 100) - (risk_free_rate * 100)
        return excess_return / downside_volatility


def create_backtest_service(parquet_store=None) -> BacktestService:
    """Factory function to create backtest service."""
    return BacktestService(parquet_store)
