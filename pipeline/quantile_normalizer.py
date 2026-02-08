"""
MarketGPS Rolling Quantile Normalizer.

Replaces fixed bounds with adaptive quantile-based normalization.
Tracks historical metric distributions and normalizes using percentile rank.
"""

from typing import Optional, Dict, List
from collections import deque
from datetime import datetime
import json
import logging
from threading import Lock

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class QuantileNormalizer:
    """
    Rolling quantile-based normalization engine.

    Maintains a sliding window of historical metric values and normalizes
    new values using percentile rank within that window. Automatically
    falls back to fixed bounds when insufficient historical data exists.
    """

    # Minimum samples required before using quantile normalization
    MIN_SAMPLES = 30

    # Percentiles for winsorization (clip outliers)
    WINSORIZE_LOWER = 1.0  # 1st percentile
    WINSORIZE_UPPER = 99.0  # 99th percentile

    def __init__(self, window_size: int = 252):
        """
        Initialize quantile normalizer.

        Args:
            window_size: Rolling window size (default: 252 trading days)
        """
        self.window_size = window_size
        self._distributions: Dict[str, deque] = {}
        self._lock = Lock()

        # Fallback fixed bounds (used when < MIN_SAMPLES)
        self._fixed_bounds: Dict[str, tuple] = {
            "rsi": (30, 70),
            "price_vs_sma200": (-20, 20),
            "volatility_annual": (5, 50),
            "max_drawdown": (0, 40),
            "pe_ratio": (5, 50),
            "profit_margin": (0, 30),
        }

    def fit(self, metric_name: str, values: List[float]) -> None:
        """
        Update distribution for a metric.

        Args:
            metric_name: Name of the metric (e.g., 'rsi', 'volatility_annual')
            values: List of historical values to add to the distribution
        """
        if not values or metric_name is None:
            return

        with self._lock:
            # Initialize deque if first time
            if metric_name not in self._distributions:
                self._distributions[metric_name] = deque(maxlen=self.window_size)

            # Add new values to distribution
            for value in values:
                if value is not None and np.isfinite(value):
                    self._distributions[metric_name].append(float(value))

            logger.debug(
                f"Updated distribution for {metric_name}: "
                f"{len(self._distributions[metric_name])} samples"
            )

    def transform(self, metric_name: str, value: float) -> float:
        """
        Normalize a value using percentile rank.

        Args:
            metric_name: Name of the metric
            value: Value to normalize

        Returns:
            Normalized score (0-100), or fallback fixed bounds normalization
        """
        if value is None or not np.isfinite(value):
            return 50.0  # Neutral default

        with self._lock:
            # Get distribution
            if metric_name not in self._distributions:
                return self._fallback_normalize(metric_name, value)

            distribution = list(self._distributions[metric_name])

            # Use fallback if insufficient data
            if len(distribution) < self.MIN_SAMPLES:
                return self._fallback_normalize(metric_name, value)

            # Winsorize the distribution to handle outliers
            dist_array = np.array(distribution)
            lower = np.percentile(dist_array, self.WINSORIZE_LOWER)
            upper = np.percentile(dist_array, self.WINSORIZE_UPPER)
            winsorized = np.clip(dist_array, lower, upper)

            # Calculate percentile rank of the new value
            # Clip value to winsorized range for ranking
            value_clipped = np.clip(value, lower, upper)
            percentile_rank = np.mean(winsorized <= value_clipped)

            # Convert to 0-100 score
            normalized_score = percentile_rank * 100

            return round(normalized_score, 1)

    def _fallback_normalize(self, metric_name: str, value: float) -> float:
        """
        Fallback to fixed bounds normalization.

        Used when historical data is insufficient.

        Args:
            metric_name: Name of the metric
            value: Value to normalize

        Returns:
            Normalized score (0-100)
        """
        if metric_name not in self._fixed_bounds:
            return 50.0  # Neutral default for unknown metrics

        min_val, max_val = self._fixed_bounds[metric_name]

        # Handle division by zero
        if min_val == max_val:
            return 50.0

        # Linear interpolation with clamping
        normalized = ((value - min_val) / (max_val - min_val)) * 100
        normalized = np.clip(normalized, 0, 100)

        return round(normalized, 1)

    def set_fixed_bound(
        self,
        metric_name: str,
        min_val: float,
        max_val: float
    ) -> None:
        """
        Set or update fixed bounds for a metric.

        Used for fallback normalization when insufficient data exists.

        Args:
            metric_name: Name of the metric
            min_val: Minimum bound
            max_val: Maximum bound
        """
        with self._lock:
            self._fixed_bounds[metric_name] = (min_val, max_val)
            logger.debug(f"Updated fixed bounds for {metric_name}: [{min_val}, {max_val}]")

    def get_distribution_stats(self, metric_name: str) -> Optional[Dict]:
        """
        Get statistics about a metric's distribution.

        Useful for debugging and monitoring.

        Args:
            metric_name: Name of the metric

        Returns:
            Dict with count, mean, std, min, max, or None if not found
        """
        with self._lock:
            if metric_name not in self._distributions:
                return None

            dist_array = np.array(list(self._distributions[metric_name]))

            if len(dist_array) == 0:
                return None

            return {
                "metric_name": metric_name,
                "count": len(dist_array),
                "mean": float(np.mean(dist_array)),
                "std": float(np.std(dist_array)),
                "min": float(np.min(dist_array)),
                "max": float(np.max(dist_array)),
                "p25": float(np.percentile(dist_array, 25)),
                "p50": float(np.percentile(dist_array, 50)),
                "p75": float(np.percentile(dist_array, 75)),
            }

    def save_state(self, filepath: str) -> None:
        """
        Serialize state to JSON file for persistence.

        Args:
            filepath: Path to save state JSON file
        """
        with self._lock:
            state = {
                "window_size": self.window_size,
                "timestamp": datetime.utcnow().isoformat(),
                "distributions": {
                    metric: list(distribution)
                    for metric, distribution in self._distributions.items()
                },
                "fixed_bounds": self._fixed_bounds,
            }

            try:
                with open(filepath, "w") as f:
                    json.dump(state, f, indent=2)
                logger.info(f"Saved quantile normalizer state to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save state to {filepath}: {e}")

    def load_state(self, filepath: str) -> bool:
        """
        Load state from JSON file.

        Args:
            filepath: Path to load state from

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                with open(filepath, "r") as f:
                    state = json.load(f)

                self.window_size = state.get("window_size", self.window_size)
                self._fixed_bounds = state.get("fixed_bounds", self._fixed_bounds)

                # Reload distributions
                self._distributions.clear()
                for metric, values in state.get("distributions", {}).items():
                    self._distributions[metric] = deque(
                        values, maxlen=self.window_size
                    )

                logger.info(
                    f"Loaded quantile normalizer state from {filepath} "
                    f"({len(self._distributions)} metrics)"
                )
                return True

            except Exception as e:
                logger.error(f"Failed to load state from {filepath}: {e}")
                return False

    def clear(self) -> None:
        """Clear all historical distributions."""
        with self._lock:
            self._distributions.clear()
            logger.debug("Cleared all quantile normalizer distributions")

    def clear_metric(self, metric_name: str) -> None:
        """Clear distribution for a specific metric."""
        with self._lock:
            if metric_name in self._distributions:
                del self._distributions[metric_name]
                logger.debug(f"Cleared distribution for metric: {metric_name}")

    def is_ready(self, metric_name: str) -> bool:
        """
        Check if a metric has sufficient data for quantile normalization.

        Args:
            metric_name: Name of the metric

        Returns:
            True if distribution has >= MIN_SAMPLES
        """
        with self._lock:
            if metric_name not in self._distributions:
                return False
            return len(self._distributions[metric_name]) >= self.MIN_SAMPLES
