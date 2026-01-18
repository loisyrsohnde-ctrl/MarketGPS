"""
MarketGPS - Barbell Portfolio Simulation Service
=================================================
Handles backtesting and portfolio simulation using Parquet OHLCV data.
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import pandas - required for simulation
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas/numpy not available - simulation disabled")


class BarbellSimulator:
    """Portfolio simulation engine using Parquet OHLCV data."""

    def __init__(self, data_dir: str = None):
        # Resolve path relative to project root
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to project_root/data/parquet
            project_root = Path(__file__).parent.parent
            self.data_dir = project_root / "data" / "parquet"

        logger.info(
            f"BarbellSimulator initialized with data_dir: {self.data_dir}")
        self.cache = {}

    def get_parquet_path(self, asset_id: str, market_scope: str = "US_EU") -> Optional[Path]:
        """Get parquet file path for an asset."""
        # Try different path patterns
        scope_folder = "us_eu" if market_scope == "US_EU" else "africa"

        # Pattern 1: {asset_id}.parquet in bars_daily (exact match)
        path1 = self.data_dir / scope_folder / \
            "bars_daily" / f"{asset_id}.parquet"
        if path1.exists():
            return path1

        # Pattern 2: {ticker}_{exchange}.parquet format
        # For asset_ids like "CSH2.PA" -> try "CSH2_PA.parquet"
        clean_id = asset_id.replace('.', '_').replace('/', '_')
        path2 = self.data_dir / scope_folder / \
            "bars_daily" / f"{clean_id}.parquet"
        if path2.exists():
            return path2

        # Pattern 3: Just the ticker part (e.g., "AAPL" from "AAPL_US")
        ticker = asset_id.split(
            '_')[0] if '_' in asset_id else asset_id.split('.')[0]
        path3 = self.data_dir / scope_folder / \
            "bars_daily" / f"{ticker}_US.parquet"
        if path3.exists():
            return path3

        # Pattern 4: {ticker}_{exchange}.parquet for assets like "AAPL.US"
        if '.' in asset_id:
            parts = asset_id.split('.')
            path4 = self.data_dir / scope_folder / \
                "bars_daily" / f"{parts[0]}_{parts[1]}.parquet"
            if path4.exists():
                return path4

        # Pattern 5: Check in ohlcv folder
        path5 = self.data_dir / "ohlcv" / f"{asset_id}.parquet"
        if path5.exists():
            return path5

        # Pattern 6: Check in bars_daily root
        path6 = self.data_dir / "bars_daily" / f"{asset_id}.parquet"
        if path6.exists():
            return path6

        logger.debug(
            f"No parquet found for {asset_id}, tried: {path1}, {path2}, {path3}")
        return None

    def load_price_series(
        self,
        asset_id: str,
        market_scope: str = "US_EU",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Optional[pd.DataFrame]:
        """Load OHLCV data for an asset."""
        if not PANDAS_AVAILABLE:
            return None

        path = self.get_parquet_path(asset_id, market_scope)
        if not path:
            logger.warning(f"No parquet file found for {asset_id}")
            return None

        try:
            df = pd.read_parquet(path)

            # Ensure date column exists and convert to index
            # First, check original column names (before lowercasing)
            original_cols = df.columns.tolist()

            # Handle date column (could be 'date', 'Date', 'timestamp', etc.)
            date_col = None
            for col in original_cols:
                if col.lower() == 'date':
                    date_col = col
                    break
                elif col.lower() == 'timestamp':
                    date_col = col
                    break

            if date_col:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            df.sort_index(inplace=True)

            # Filter date range
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]

            # Find price column (case-insensitive check on original columns)
            price_col = None
            cols_lower = {c.lower().replace(' ', '_'): c for c in df.columns}

            # Priority: Adj Close > Close
            for pattern in ['adj_close', 'adjclose', 'adj close', 'close']:
                pattern_normalized = pattern.replace(' ', '_')
                if pattern_normalized in cols_lower:
                    price_col = cols_lower[pattern_normalized]
                    break

            # Also check for exact "Adj Close" (with space)
            if price_col is None:
                for col in df.columns:
                    if col.lower().replace(' ', '') == 'adjclose':
                        price_col = col
                        break
                    elif col.lower() == 'close':
                        price_col = col
                        break

            if price_col is None:
                logger.warning(
                    f"No close price column found for {asset_id}. Columns: {df.columns.tolist()}")
                return None

            df['price'] = df[price_col]

            return df[['price']].dropna()

        except Exception as e:
            logger.error(f"Error loading parquet for {asset_id}: {e}")
            return None

    def compute_composition_hash(
        self,
        compositions: List[Dict],
        period_years: int,
        rebalance_freq: str
    ) -> str:
        """Generate unique hash for a portfolio composition."""
        # Sort compositions for consistency
        sorted_comps = sorted(
            compositions, key=lambda x: x.get('asset_id', ''))
        data = {
            'compositions': sorted_comps,
            'period_years': period_years,
            'rebalance_freq': rebalance_freq
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def simulate_portfolio(
        self,
        compositions: List[Dict[str, Any]],
        period_years: int = 10,
        rebalance_frequency: str = "yearly",
        initial_capital: float = 10000,
        market_scope: str = "US_EU"
    ) -> Dict[str, Any]:
        """
        Run portfolio backtest simulation.

        Args:
            compositions: List of {asset_id, weight, block}
            period_years: Backtest period (5, 10, 20)
            rebalance_frequency: monthly, quarterly, yearly
            initial_capital: Starting capital
            market_scope: US_EU or AFRICA

        Returns:
            Dict with metrics and equity curve
        """
        if not PANDAS_AVAILABLE:
            return {
                "error": "Simulation requires pandas/numpy",
                "cagr": None,
                "volatility": None,
                "sharpe": None,
                "max_drawdown": None,
                "equity_curve": [],
                "warnings": ["pandas not installed"]
            }

        warnings = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * period_years)

        # Load all price series
        price_data = {}
        valid_compositions = []
        total_valid_weight = 0

        for comp in compositions:
            asset_id = comp.get('asset_id', '')
            weight = comp.get('weight', 0)

            df = self.load_price_series(
                asset_id, market_scope, start_date, end_date)

            # Require minimum 50 days of data for MVP (we'll warn if less than expected)
            MIN_DAYS = 50
            if df is None or len(df) < MIN_DAYS:
                warnings.append(
                    f"{asset_id}: Insufficient history ({len(df) if df is not None else 0} days, min {MIN_DAYS})")
                continue

            # Check data coverage
            expected_days = (end_date - start_date).days * \
                0.7  # Expect ~70% trading days
            if len(df) < expected_days * 0.5:
                warnings.append(
                    f"{asset_id}: Low data coverage ({len(df)}/{int(expected_days)} days)")

            price_data[asset_id] = df
            valid_compositions.append(comp)
            total_valid_weight += weight

        if not valid_compositions:
            return {
                "error": "No valid assets with sufficient history",
                "cagr": None,
                "volatility": None,
                "sharpe": None,
                "max_drawdown": None,
                "equity_curve": [],
                "warnings": warnings,
                "data_quality_score": 0
            }

        # Renormalize weights
        for comp in valid_compositions:
            comp['normalized_weight'] = comp['weight'] / \
                total_valid_weight if total_valid_weight > 0 else 0

        # Align all series to common dates
        all_prices = pd.DataFrame()
        for asset_id, df in price_data.items():
            all_prices[asset_id] = df['price']

        all_prices.dropna(inplace=True)

        if len(all_prices) < 252:
            return {
                "error": "Insufficient overlapping data between assets",
                "cagr": None,
                "volatility": None,
                "sharpe": None,
                "max_drawdown": None,
                "equity_curve": [],
                "warnings": warnings,
                "data_quality_score": 20
            }

        # Calculate daily returns
        returns = all_prices.pct_change().dropna()

        # Determine rebalance dates
        if rebalance_frequency == "monthly":
            rebalance_mask = returns.index.to_series().dt.month.diff().fillna(1) != 0
        elif rebalance_frequency == "quarterly":
            rebalance_mask = (returns.index.to_series().dt.month % 3 == 1) & \
                             (returns.index.to_series().dt.day <= 7)
        else:  # yearly
            rebalance_mask = returns.index.to_series().dt.dayofyear <= 7

        # Build portfolio returns
        weights = {comp['asset_id']: comp['normalized_weight']
                   for comp in valid_compositions}
        weight_series = pd.Series(weights)

        # Simple weighted returns (assuming rebalancing at specified frequency)
        portfolio_returns = (
            returns[list(weights.keys())] * weight_series).sum(axis=1)

        # Calculate equity curve
        equity = initial_capital * (1 + portfolio_returns).cumprod()

        # Calculate metrics
        trading_days = 252
        total_return = (equity.iloc[-1] / initial_capital) - 1
        years = len(returns) / trading_days
        cagr = ((1 + total_return) ** (1 / years) - 1) * \
            100 if years > 0 else 0

        volatility = portfolio_returns.std() * np.sqrt(trading_days) * 100

        # Sharpe (assuming 2% risk-free rate)
        risk_free = 0.02
        excess_return = (cagr / 100) - risk_free
        sharpe = excess_return / (volatility / 100) if volatility > 0 else 0

        # Max drawdown
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        # Yearly performance table
        yearly_table = []
        for year in returns.index.year.unique():
            year_returns = portfolio_returns[portfolio_returns.index.year == year]
            if len(year_returns) > 0:
                year_return = ((1 + year_returns).prod() - 1) * 100
                yearly_table.append({
                    "year": int(year),
                    "return": round(year_return, 2)
                })

        # Sample equity curve (monthly points for chart)
        equity_monthly = equity.resample('M').last()
        equity_curve = [
            {"date": d.strftime("%Y-%m-%d"), "value": round(v, 2)}
            for d, v in equity_monthly.items()
        ]

        # Data quality score
        coverage_ratio = len(all_prices) / (period_years * 252)
        data_quality_score = min(100, int(coverage_ratio * 100))

        return {
            "cagr": round(cagr, 2),
            "volatility": round(volatility, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_return": round(total_return * 100, 2),
            "final_value": round(equity.iloc[-1], 2),
            "initial_capital": initial_capital,
            "period_years": period_years,
            "rebalance_frequency": rebalance_frequency,
            "equity_curve": equity_curve,
            "yearly_table": yearly_table,
            "best_year": max(yearly_table, key=lambda x: x['return']) if yearly_table else None,
            "worst_year": min(yearly_table, key=lambda x: x['return']) if yearly_table else None,
            "warnings": warnings,
            "data_quality_score": data_quality_score,
            "assets_included": len(valid_compositions),
            "assets_excluded": len(compositions) - len(valid_compositions),
            "executed_at": datetime.now().isoformat()
        }


# Singleton instance
_simulator = None


def get_simulator() -> BarbellSimulator:
    """Get or create simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = BarbellSimulator()
    return _simulator
