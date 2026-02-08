"""
MarketGPS Macro Environment Overlay.

Adjusts scoring weights based on market regimes detected from macro data.
Uses yfinance for real-time macro indicators with intelligent caching.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """Market regime classifications."""
    RISK_ON = "RISK_ON"
    NEUTRAL = "NEUTRAL"
    RISK_OFF = "RISK_OFF"
    CRISIS = "CRISIS"


@dataclass
class RegimeData:
    """Container for macro regime data."""
    vix: Optional[float] = None
    fed_funds_rate: Optional[float] = None
    ten_year_yield: Optional[float] = None
    sp500_price: Optional[float] = None
    sp500_sma200: Optional[float] = None
    ten_year_yield_3mo_change: Optional[float] = None

    def is_complete(self) -> bool:
        """Check if we have all required data."""
        return all([
            self.vix is not None,
            self.sp500_price is not None,
            self.sp500_sma200 is not None,
        ])


@dataclass
class RegimeAdjustments:
    """Weight adjustments for each regime."""
    safety_adjustment: float = 0.0  # Additive percentage points
    momentum_adjustment: float = 0.0
    value_adjustment: float = 0.0

    def apply_to_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Apply adjustments to pillar weights.

        Args:
            weights: Original weights dict {pillar: weight}

        Returns:
            Adjusted weights dict
        """
        adjusted = weights.copy()

        # Apply adjustments (as percentage point changes)
        if "safety" in adjusted:
            adjusted["safety"] = max(0, adjusted["safety"] + self.safety_adjustment)
        if "momentum" in adjusted:
            adjusted["momentum"] = max(0, adjusted["momentum"] + self.momentum_adjustment)
        if "value" in adjusted:
            adjusted["value"] = max(0, adjusted["value"] + self.value_adjustment)

        # Renormalize so weights sum to 1
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        return adjusted


@dataclass
class CachedRegime:
    """Cached regime data with timestamp."""
    regime: MarketRegime
    adjustments: RegimeAdjustments
    timestamp: datetime = field(default_factory=datetime.utcnow)
    regime_data: RegimeData = field(default_factory=RegimeData)

    def is_valid(self, cache_hours: int = 4) -> bool:
        """Check if cache is still valid."""
        age = datetime.utcnow() - self.timestamp
        return age < timedelta(hours=cache_hours)


class MacroOverlay:
    """
    Macro environment overlay for scoring engine.

    Detects market regimes and adjusts pillar weights accordingly.
    Includes caching and graceful degradation.
    """

    # Regime detection thresholds
    CRISIS_VIX_THRESHOLD = 30.0
    RISK_OFF_VIX_THRESHOLD = 20.0
    RISK_ON_VIX_THRESHOLD = 15.0

    RISK_OFF_YIELD_CHANGE_THRESHOLD = 0.50  # 50 basis points in 3 months

    # Regime adjustments (percentage point changes to weights)
    ADJUSTMENTS = {
        MarketRegime.CRISIS: RegimeAdjustments(
            safety_adjustment=20.0,
            momentum_adjustment=-15.0,
            value_adjustment=-5.0
        ),
        MarketRegime.RISK_OFF: RegimeAdjustments(
            safety_adjustment=10.0,
            momentum_adjustment=-10.0,
            value_adjustment=0.0
        ),
        MarketRegime.RISK_ON: RegimeAdjustments(
            safety_adjustment=-10.0,
            momentum_adjustment=10.0,
            value_adjustment=0.0
        ),
        MarketRegime.NEUTRAL: RegimeAdjustments(
            safety_adjustment=0.0,
            momentum_adjustment=0.0,
            value_adjustment=0.0
        ),
    }

    def __init__(self, cache_hours: int = 4):
        """
        Initialize macro overlay.

        Args:
            cache_hours: Cache duration for regime data
        """
        self.cache_hours = cache_hours
        self._cached_regime: Optional[CachedRegime] = None

    def get_current_regime(self) -> MarketRegime:
        """
        Get current market regime.

        Uses cache if available and valid. Falls back to NEUTRAL if data
        unavailable.

        Returns:
            Current MarketRegime
        """
        # Check cache
        if self._cached_regime and self._cached_regime.is_valid(self.cache_hours):
            logger.debug(
                f"Using cached regime: {self._cached_regime.regime} "
                f"(age: {datetime.utcnow() - self._cached_regime.timestamp})"
            )
            return self._cached_regime.regime

        # Fetch fresh data
        regime_data = self._fetch_macro_data()

        if not regime_data.is_complete():
            logger.warning(
                "Incomplete macro data; unable to determine regime. "
                "Defaulting to NEUTRAL."
            )
            # Cache neutral fallback
            self._cached_regime = CachedRegime(
                regime=MarketRegime.NEUTRAL,
                adjustments=self.ADJUSTMENTS[MarketRegime.NEUTRAL],
                regime_data=regime_data
            )
            return MarketRegime.NEUTRAL

        # Detect regime
        regime = self._detect_regime(regime_data)

        # Cache result
        self._cached_regime = CachedRegime(
            regime=regime,
            adjustments=self.ADJUSTMENTS[regime],
            regime_data=regime_data
        )

        logger.info(
            f"Market regime detected: {regime} | "
            f"VIX={regime_data.vix:.1f} | "
            f"S&P500={regime_data.sp500_price:.2f} | "
            f"200d_SMA={regime_data.sp500_sma200:.2f}"
        )

        return regime

    def adjust_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Adjust pillar weights based on current market regime.

        Args:
            weights: Original weights dict {pillar: weight}

        Returns:
            Regime-adjusted weights dict
        """
        regime = self.get_current_regime()
        adjustments = self.ADJUSTMENTS[regime]

        adjusted = adjustments.apply_to_weights(weights)

        logger.debug(
            f"Weight adjustments for {regime}: "
            f"safety={adjustments.safety_adjustment:+.0f}pp, "
            f"momentum={adjustments.momentum_adjustment:+.0f}pp, "
            f"value={adjustments.value_adjustment:+.0f}pp"
        )

        return adjusted

    def _fetch_macro_data(self) -> RegimeData:
        """
        Fetch macro data from yfinance.

        Returns:
            RegimeData object with available data
        """
        data = RegimeData()

        try:
            # Fetch VIX
            try:
                vix = yf.Ticker("^VIX").history(period="1d")
                if not vix.empty and "Close" in vix.columns:
                    data.vix = float(vix["Close"].iloc[-1])
            except Exception as e:
                logger.debug(f"Failed to fetch VIX: {e}")

            # Fetch Fed Funds Rate
            try:
                ffr = yf.Ticker("^IRX").history(period="1d")
                if not ffr.empty and "Close" in ffr.columns:
                    data.fed_funds_rate = float(ffr["Close"].iloc[-1])
            except Exception as e:
                logger.debug(f"Failed to fetch Fed Funds Rate: {e}")

            # Fetch 10Y Yield
            try:
                tny = yf.Ticker("^TNX").history(period="1d")
                if not tny.empty and "Close" in tny.columns:
                    data.ten_year_yield = float(tny["Close"].iloc[-1])
            except Exception as e:
                logger.debug(f"Failed to fetch 10Y Yield: {e}")

            # Fetch S&P 500 data
            try:
                sp500 = yf.Ticker("^GSPC").history(period="250d")
                if not sp500.empty and "Close" in sp500.columns:
                    close = sp500["Close"]
                    data.sp500_price = float(close.iloc[-1])

                    # Calculate 200-day SMA
                    if len(close) >= 200:
                        data.sp500_sma200 = float(close.rolling(200).mean().iloc[-1])
            except Exception as e:
                logger.debug(f"Failed to fetch S&P 500 data: {e}")

            # Calculate 10Y yield 3-month change
            if data.ten_year_yield is not None:
                try:
                    tny = yf.Ticker("^TNX").history(period="100d")
                    if len(tny) > 60:
                        current_yield = float(tny["Close"].iloc[-1])
                        yield_60d_ago = float(tny["Close"].iloc[-60])
                        data.ten_year_yield_3mo_change = current_yield - yield_60d_ago
                except Exception as e:
                    logger.debug(f"Failed to calculate yield change: {e}")

        except Exception as e:
            logger.error(f"Unexpected error fetching macro data: {e}")

        return data

    def _detect_regime(self, data: RegimeData) -> MarketRegime:
        """
        Detect market regime from macro data.

        Detection hierarchy (in order):
        1. CRISIS: VIX > 30 OR S&P below 200d SMA with high VIX
        2. RISK_OFF: VIX > 20 AND yield rising fast
        3. RISK_ON: VIX < 15 AND S&P above 200d SMA
        4. NEUTRAL: Everything else

        Args:
            data: RegimeData object

        Returns:
            Detected MarketRegime
        """
        if not data.is_complete():
            return MarketRegime.NEUTRAL

        vix = data.vix
        sp500 = data.sp500_price
        sma200 = data.sp500_sma200

        # CRISIS detection
        if vix > self.CRISIS_VIX_THRESHOLD:
            return MarketRegime.CRISIS

        # Check S&P 200d SMA cross (CRISIS indicator)
        if sma200 is not None and sp500 < sma200 and vix > self.RISK_OFF_VIX_THRESHOLD:
            return MarketRegime.CRISIS

        # RISK_OFF detection
        if vix > self.RISK_OFF_VIX_THRESHOLD:
            # Check if yield is rising fast
            if (data.ten_year_yield_3mo_change is not None and
                data.ten_year_yield_3mo_change > self.RISK_OFF_YIELD_CHANGE_THRESHOLD):
                return MarketRegime.RISK_OFF

        # RISK_ON detection
        if vix < self.RISK_ON_VIX_THRESHOLD:
            if sma200 is not None and sp500 > sma200:
                return MarketRegime.RISK_ON

        # Default to NEUTRAL
        return MarketRegime.NEUTRAL

    def clear_cache(self):
        """Clear the cached regime."""
        self._cached_regime = None
        logger.debug("Macro overlay cache cleared")

    def get_regime_data(self) -> Optional[RegimeData]:
        """Get the current cached regime data for debugging/inspection."""
        if self._cached_regime:
            return self._cached_regime.regime_data
        return None
