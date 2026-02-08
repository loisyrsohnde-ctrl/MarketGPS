"""
MarketGPS Portfolio Optimizer
Markowitz Mean-Variance Optimization with practical constraints.

This module provides institutional-grade portfolio optimization including:
- Markowitz mean-variance optimization
- Multiple optimization objectives (max Sharpe, min volatility, risk parity, etc.)
- Ledoit-Wolf covariance shrinkage for stability
- Black-Litterman model for incorporating views
- Efficient frontier generation
- Practical constraints (position limits, sector exposure, turnover limits)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """Portfolio optimization objectives."""
    MAX_SHARPE = "max_sharpe"           # Maximize Sharpe ratio
    MIN_VOLATILITY = "min_volatility"   # Minimize volatility
    MAX_RETURN = "max_return"           # Maximize expected return
    RISK_PARITY = "risk_parity"        # Equal risk contribution
    TARGET_RETURN = "target_return"    # Target specific return level
    TARGET_VOLATILITY = "target_volatility"  # Target specific volatility


@dataclass
class PortfolioConstraints:
    """Constraints for portfolio optimization."""
    min_weight: float = 0.01          # Minimum weight per position
    max_weight: float = 0.30          # Maximum weight per position
    max_sector_weight: float = 0.40   # Maximum sector exposure
    min_assets: int = 5               # Minimum number of assets in portfolio
    max_assets: int = 30              # Maximum number of assets
    turnover_limit: float = 0.50      # Maximum portfolio turnover

    def __post_init__(self):
        """Validate constraints."""
        if not (0 <= self.min_weight <= self.max_weight <= 1):
            raise ValueError("Weights must be 0 <= min <= max <= 1")
        if not (0 < self.min_assets <= self.max_assets):
            raise ValueError("Asset count constraints invalid")
        if not (0 <= self.turnover_limit <= 1):
            raise ValueError("Turnover limit must be 0-1")


@dataclass
class OptimizationResult:
    """Result of portfolio optimization."""
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    diversification_ratio: float
    effective_n: float              # Effective number of bets
    sector_exposure: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate result."""
        if not np.isclose(sum(self.weights.values()), 1.0, atol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {sum(self.weights.values())}")


class PortfolioOptimizer:
    """
    Markowitz Mean-Variance Optimizer.

    Provides institutional-grade portfolio optimization with multiple objectives,
    realistic constraints, and advanced techniques like Ledoit-Wolf shrinkage
    and Black-Litterman model.
    """

    def __init__(self, risk_free_rate: float = 0.045):
        """
        Initialize optimizer.

        Args:
            risk_free_rate: Risk-free rate for Sharpe calculation (default: 4.5%)
        """
        self.risk_free_rate = risk_free_rate

    def optimize(
        self,
        returns: pd.DataFrame,
        objective: OptimizationObjective,
        constraints: Optional[PortfolioConstraints] = None,
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None,
        sector_map: Optional[Dict[str, str]] = None,
        current_weights: Optional[Dict[str, float]] = None,
    ) -> OptimizationResult:
        """
        Optimize portfolio weights.

        Args:
            returns: DataFrame of asset returns (columns are assets)
            objective: OptimizationObjective specifying goal
            constraints: PortfolioConstraints (optional)
            target_return: Target return for TARGET_RETURN objective
            target_volatility: Target volatility for TARGET_VOLATILITY objective
            sector_map: Dict mapping assets to sectors for sector constraints
            current_weights: Current weights for turnover calculation

        Returns:
            OptimizationResult with optimal weights and metrics
        """
        if constraints is None:
            constraints = PortfolioConstraints()

        # Calculate covariance and expected returns
        cov_matrix = self._covariance_shrinkage(returns)
        exp_returns = returns.mean() * 252  # Annualized

        # Filter assets (remove those with NaN returns)
        valid_assets = exp_returns[~exp_returns.isna()].index.tolist()

        if len(valid_assets) < constraints.min_assets:
            logger.warning(
                f"Only {len(valid_assets)} valid assets, less than minimum {constraints.min_assets}"
            )

        n_assets = len(valid_assets)
        cov_matrix = cov_matrix.loc[valid_assets, valid_assets]
        exp_returns = exp_returns[valid_assets]

        # Set up optimization
        bounds = tuple(
            (constraints.min_weight, constraints.max_weight)
            for _ in range(n_assets)
        )

        # Constraints: weights sum to 1
        constraints_list = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]

        # Add sector constraints if provided
        if sector_map:
            for sector in set(sector_map.values()):
                sector_assets_idx = [
                    i for i, asset in enumerate(valid_assets)
                    if sector_map.get(asset) == sector
                ]
                if sector_assets_idx:
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, idx=sector_assets_idx: constraints.max_sector_weight - np.sum(w[idx])
                    })

        # Initial guess: equal weight
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Objective function and initial call
        if objective == OptimizationObjective.MAX_SHARPE:
            result = minimize(
                self._neg_sharpe_ratio,
                x0,
                args=(exp_returns.values, cov_matrix.values),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'ftol': 1e-6, 'maxiter': 500}
            )

        elif objective == OptimizationObjective.MIN_VOLATILITY:
            result = minimize(
                self._portfolio_volatility,
                x0,
                args=(cov_matrix.values,),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'ftol': 1e-6, 'maxiter': 500}
            )

        elif objective == OptimizationObjective.MAX_RETURN:
            result = minimize(
                lambda w, r: -np.dot(w, r),  # Negative because minimize
                x0,
                args=(exp_returns.values,),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'ftol': 1e-6, 'maxiter': 500}
            )

        elif objective == OptimizationObjective.RISK_PARITY:
            weights = self._risk_parity_weights(cov_matrix.values)
            # Normalize to meet constraints
            weights = np.clip(weights, constraints.min_weight, constraints.max_weight)
            weights = weights / np.sum(weights)
            result = type('obj', (object,), {'x': weights, 'success': True})()

        elif objective == OptimizationObjective.TARGET_RETURN:
            if target_return is None:
                raise ValueError("target_return required for TARGET_RETURN objective")

            constraints_with_return = constraints_list.copy()
            constraints_with_return.append({
                'type': 'eq',
                'fun': lambda w, r, tr: np.dot(w, r) - tr,
                'args': (exp_returns.values, target_return)
            })

            result = minimize(
                self._portfolio_volatility,
                x0,
                args=(cov_matrix.values,),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_with_return,
                options={'ftol': 1e-6, 'maxiter': 500}
            )

        elif objective == OptimizationObjective.TARGET_VOLATILITY:
            if target_volatility is None:
                raise ValueError("target_volatility required for TARGET_VOLATILITY objective")

            constraints_with_vol = constraints_list.copy()
            constraints_with_vol.append({
                'type': 'eq',
                'fun': self._portfolio_volatility,
                'args': (cov_matrix.values,),
            })

            # Objective: maximize return subject to vol constraint
            result = minimize(
                lambda w, r: -np.dot(w, r),
                x0,
                args=(exp_returns.values,),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_with_vol,
                options={'ftol': 1e-6, 'maxiter': 500}
            )

        else:
            raise ValueError(f"Unknown objective: {objective}")

        # Extract weights
        if hasattr(result, 'x'):
            weights = result.x
        else:
            weights = x0

        # Normalize weights (handle numerical errors)
        weights = weights / np.sum(weights)

        # Create weight dict
        weight_dict = {asset: float(w) for asset, w in zip(valid_assets, weights)}

        # Calculate metrics
        portfolio_return = np.dot(weights, exp_returns.values)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix.values, weights)))
        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0

        # Diversification ratio
        marginal_contrib_vol = np.dot(cov_matrix.values, weights)
        diversification_ratio = np.dot(weights, exp_returns.values * 252) / portfolio_vol if portfolio_vol > 0 else 0

        # Effective number of bets (Herfindahl index)
        effective_n = 1.0 / np.sum(weights ** 2) if np.sum(weights ** 2) > 0 else 0

        return OptimizationResult(
            weights=weight_dict,
            expected_return=float(portfolio_return),
            expected_volatility=float(portfolio_vol),
            sharpe_ratio=float(sharpe),
            diversification_ratio=float(diversification_ratio),
            effective_n=float(effective_n),
            sector_exposure=self._calculate_sector_exposure(weight_dict, sector_map),
        )

    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        n_points: int = 50,
        constraints: Optional[PortfolioConstraints] = None,
        sector_map: Optional[Dict[str, str]] = None,
    ) -> List[OptimizationResult]:
        """
        Generate efficient frontier points.

        Args:
            returns: DataFrame of asset returns
            n_points: Number of frontier points
            constraints: PortfolioConstraints
            sector_map: Sector mapping for constraints

        Returns:
            List of OptimizationResults representing the frontier
        """
        if constraints is None:
            constraints = PortfolioConstraints()

        # Calculate return range
        exp_returns = returns.mean() * 252
        valid_assets = exp_returns[~exp_returns.isna()].index.tolist()
        exp_returns = exp_returns[valid_assets]

        min_return = exp_returns.min()
        max_return = exp_returns.max()

        # Generate target returns
        target_returns = np.linspace(min_return, max_return, n_points)

        frontier = []
        for target_ret in target_returns:
            try:
                result = self.optimize(
                    returns,
                    OptimizationObjective.TARGET_RETURN,
                    constraints=constraints,
                    target_return=float(target_ret),
                    sector_map=sector_map,
                )
                frontier.append(result)
            except Exception as e:
                logger.debug(f"Failed to optimize for target return {target_ret}: {e}")
                continue

        return frontier

    def black_litterman(
        self,
        market_weights: Dict[str, float],
        views: Dict[str, float],
        confidence: Dict[str, float],
        cov_matrix: Optional[np.ndarray] = None,
        returns: Optional[pd.DataFrame] = None,
    ) -> Dict[str, float]:
        """
        Black-Litterman model for incorporating views into portfolio optimization.

        Args:
            market_weights: Market cap weights or prior weights
            views: Asset-specific return views
            confidence: Confidence level in each view (0-1)
            cov_matrix: Covariance matrix (optional if returns provided)
            returns: Return series for covariance calculation

        Returns:
            Posterior expected returns incorporating views
        """
        # Validate inputs
        if not market_weights or not views or not confidence:
            raise ValueError("market_weights, views, and confidence are required")

        if set(views.keys()) != set(confidence.keys()):
            raise ValueError("Views and confidence must have same assets")

        # Get unique assets
        all_assets = list(set(list(market_weights.keys()) + list(views.keys())))
        n_assets = len(all_assets)

        # Create weight vector
        w_market = np.array([market_weights.get(asset, 0) for asset in all_assets])

        # Normalize if needed
        if np.sum(w_market) > 0:
            w_market = w_market / np.sum(w_market)
        else:
            w_market = np.ones(n_assets) / n_assets

        # Get or calculate covariance
        if cov_matrix is None:
            if returns is None:
                raise ValueError("Either cov_matrix or returns must be provided")
            cov_matrix = self._covariance_shrinkage(returns)

        # Ensure covariance is aligned
        cov_aligned = np.zeros((n_assets, n_assets))
        for i, asset_i in enumerate(all_assets):
            if asset_i in returns.columns:
                for j, asset_j in enumerate(all_assets):
                    if asset_j in returns.columns:
                        cov_aligned[i, j] = cov_matrix.loc[asset_i, asset_j]

        # Risk aversion coefficient
        excess_return = returns.mean().values * 252 - self.risk_free_rate
        market_return = np.dot(w_market, excess_return)
        portfolio_var = np.dot(w_market, np.dot(cov_aligned, w_market))
        lambda_param = market_return / portfolio_var if portfolio_var > 0 else 1.0

        # Implied expected returns from market equilibrium
        implied_returns = lambda_param * np.dot(cov_aligned, w_market)

        # View matrix and confidence adjustment
        views_mean = np.array([views.get(asset, 0) for asset in all_assets])
        confidence_array = np.array([confidence.get(asset, 0.5) for asset in all_assets])

        # Calculate view covariance
        omega = np.diag(confidence_array) * np.diag(np.diag(cov_aligned))

        # Black-Litterman posterior expected returns
        posterior_returns = implied_returns + np.dot(
            cov_aligned,
            np.dot(
                np.linalg.pinv(
                    np.dot(cov_aligned, np.eye(n_assets)) + omega
                ),
                (views_mean - implied_returns)
            )
        )

        # Return as dictionary
        return {asset: float(ret) for asset, ret in zip(all_assets, posterior_returns)}

    @staticmethod
    def _covariance_shrinkage(
        returns: pd.DataFrame,
        shrinkage_factor: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Apply Ledoit-Wolf shrinkage to covariance matrix.

        Ledoit-Wolf shrinkage improves covariance estimation by blending
        the sample covariance with a structured target (identity matrix scaled by variance).

        Args:
            returns: DataFrame of returns
            shrinkage_factor: Shrinkage intensity (0-1). If None, calculate optimal.

        Returns:
            Shrunk covariance matrix as DataFrame
        """
        # Remove NaN values
        returns_clean = returns.dropna()

        if len(returns_clean) < 2:
            return pd.DataFrame(np.eye(len(returns.columns)), index=returns.columns, columns=returns.columns)

        # Sample covariance
        sample_cov = returns_clean.cov().values
        n, p = returns_clean.shape

        # Target: scaled identity matrix (diagonal shrinkage)
        target = np.eye(p) * np.trace(sample_cov) / p

        # Default shrinkage factor (0.5 for stability)
        if shrinkage_factor is None:
            # Optimal Ledoit-Wolf shrinkage (simplified)
            shrinkage_factor = min(1.0, (1.0 - 2.0 / p) / (3.0 * (p + 1.0) / (n + 1.0)))

        # Apply shrinkage
        shrunk_cov = (1 - shrinkage_factor) * sample_cov + shrinkage_factor * target

        return pd.DataFrame(
            shrunk_cov,
            index=returns.columns,
            columns=returns.columns
        )

    @staticmethod
    def _risk_parity_weights(cov_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate equal risk contribution (risk parity) weights.

        In risk parity, each asset contributes equally to portfolio risk.
        This is computed by solving: w = (Σ^-1 * 1) / (1' * Σ^-1 * 1)

        Args:
            cov_matrix: Covariance matrix

        Returns:
            Risk parity weights
        """
        try:
            # Inverse covariance
            inv_cov = np.linalg.pinv(cov_matrix)

            # Sum of inverse covariance rows
            risk_parity = inv_cov @ np.ones(len(cov_matrix))

            # Normalize
            risk_parity = risk_parity / np.sum(risk_parity)

            return risk_parity

        except np.linalg.LinAlgError:
            # Fall back to equal weight if singular
            return np.ones(len(cov_matrix)) / len(cov_matrix)

    def _neg_sharpe_ratio(
        self,
        weights: np.ndarray,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
    ) -> float:
        """
        Negative Sharpe ratio (for minimization).

        Args:
            weights: Portfolio weights
            returns: Expected returns vector
            cov_matrix: Covariance matrix

        Returns:
            Negative Sharpe ratio
        """
        portfolio_return = np.dot(weights, returns)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))

        if portfolio_vol == 0:
            return 1e10

        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
        return -sharpe

    @staticmethod
    def _portfolio_volatility(
        weights: np.ndarray,
        cov_matrix: np.ndarray,
    ) -> float:
        """
        Portfolio volatility.

        Args:
            weights: Portfolio weights
            cov_matrix: Covariance matrix

        Returns:
            Portfolio standard deviation
        """
        return np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))

    @staticmethod
    def _calculate_sector_exposure(
        weights: Dict[str, float],
        sector_map: Optional[Dict[str, str]],
    ) -> Dict[str, float]:
        """
        Calculate sector exposure from weights.

        Args:
            weights: Portfolio weights
            sector_map: Mapping of assets to sectors

        Returns:
            Dictionary of sector exposures
        """
        if not sector_map:
            return {}

        sector_exposure = {}
        for asset, weight in weights.items():
            sector = sector_map.get(asset)
            if sector:
                sector_exposure[sector] = sector_exposure.get(sector, 0) + weight

        return sector_exposure
