"""
MarketGPS v7.0 - Scoring Engine
Multi-pillar scoring system for asset analysis.
"""
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from core.config import get_config, get_logger
from core.models import (
    Asset, AssetType, Score, ScoreBreakdown, StateLabel, GatingStatus
)

logger = get_logger(__name__)


def normalize(
    value: Optional[float],
    min_target: float,
    max_target: float,
    invert: bool = False
) -> Optional[float]:
    """
    Normalize a value to 0-100 scale.
    
    Args:
        value: Raw value to normalize
        min_target: Value that maps to 0 (or 100 if inverted)
        max_target: Value that maps to 100 (or 0 if inverted)
        invert: If True, lower values get higher scores
        
    Returns:
        Normalized score 0-100, or None if value is None/NaN
    """
    if value is None or pd.isna(value):
        return None
    
    try:
        # Clamp to range
        clamped = max(min_target, min(max_target, value))
        
        # Normalize to 0-1
        if max_target == min_target:
            normalized = 0.5
        else:
            normalized = (clamped - min_target) / (max_target - min_target)
        
        # Convert to 0-100
        score = normalized * 100
        
        # Invert if needed
        if invert:
            score = 100 - score
        
        return round(score, 1)
        
    except Exception:
        return None


class FeatureCalculator:
    """Calculates technical features from OHLCV data."""
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """
        Calculate RSI (Relative Strength Index).
        
        Returns:
            RSI value 0-100, or None if insufficient data
        """
        if df.empty or "Close" not in df.columns or len(df) < period + 1:
            return None
        
        try:
            close = df["Close"].dropna()
            
            if len(close) < period + 1:
                return None
            
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            
            avg_gain = gain.rolling(window=period, min_periods=period).mean()
            avg_loss = loss.rolling(window=period, min_periods=period).mean()
            
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            last_rsi = rsi.iloc[-1]
            return float(last_rsi) if pd.notna(last_rsi) else None
            
        except Exception as e:
            logger.debug(f"RSI calculation failed: {e}")
            return None
    
    @staticmethod
    def sma(df: pd.DataFrame, period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average.
        
        Returns:
            SMA value, or None if insufficient data
        """
        if df.empty or "Close" not in df.columns or len(df) < period:
            return None
        
        try:
            close = df["Close"].dropna()
            
            if len(close) < period:
                return None
            
            sma_val = close.rolling(window=period).mean().iloc[-1]
            return float(sma_val) if pd.notna(sma_val) else None
            
        except Exception:
            return None
    
    @staticmethod
    def zscore(df: pd.DataFrame, period: int = 20) -> Optional[float]:
        """
        Calculate Z-score (standard deviations from mean).
        
        Returns:
            Z-score, or None if insufficient data
        """
        if df.empty or "Close" not in df.columns or len(df) < period:
            return None
        
        try:
            close = df["Close"].dropna()
            
            if len(close) < period:
                return None
            
            recent = close.tail(period)
            mean = recent.mean()
            std = recent.std()
            
            if std == 0 or pd.isna(std):
                return 0.0
            
            current_price = close.iloc[-1]
            z = (current_price - mean) / std
            
            return float(z) if pd.notna(z) else None
            
        except Exception:
            return None
    
    @staticmethod
    def volatility_annual(df: pd.DataFrame, period: int = 252) -> Optional[float]:
        """
        Calculate annualized volatility.
        
        Returns:
            Volatility as percentage (e.g., 20.0 for 20%), or None
        """
        if df.empty or "Close" not in df.columns or len(df) < 21:
            return None
        
        try:
            close = df["Close"].dropna()
            
            # Use available data up to period
            recent = close.tail(min(period, len(close)))
            
            if len(recent) < 21:
                return None
            
            # Daily returns
            returns = recent.pct_change().dropna()
            
            if len(returns) < 20:
                return None
            
            # Daily volatility
            daily_vol = returns.std()
            
            # Annualize
            annual_vol = daily_vol * np.sqrt(252) * 100
            
            return float(annual_vol) if pd.notna(annual_vol) else None
            
        except Exception:
            return None
    
    @staticmethod
    def max_drawdown(df: pd.DataFrame, period: int = 252) -> Optional[float]:
        """
        Calculate maximum drawdown over the period.
        
        Returns:
            Drawdown as percentage (e.g., 15.0 for 15%), or None
        """
        if df.empty or "Close" not in df.columns or len(df) < 21:
            return None
        
        try:
            close = df["Close"].dropna()
            recent = close.tail(min(period, len(close)))
            
            if len(recent) < 21:
                return None
            
            # Running maximum
            running_max = recent.expanding().max()
            
            # Drawdown at each point
            drawdown = (recent - running_max) / running_max
            
            # Maximum drawdown (most negative)
            max_dd = drawdown.min() * 100
            
            return abs(float(max_dd)) if pd.notna(max_dd) else None
            
        except Exception:
            return None
    
    @staticmethod
    def price_vs_sma(df: pd.DataFrame, period: int = 200) -> Optional[float]:
        """
        Calculate price position relative to SMA.
        
        Returns:
            Percentage above/below SMA (e.g., 5.0 means 5% above)
        """
        if df.empty or "Close" not in df.columns or len(df) < period:
            return None
        
        try:
            close = df["Close"].dropna()
            
            if len(close) < period:
                return None
            
            sma_val = close.rolling(window=period).mean().iloc[-1]
            current = close.iloc[-1]
            
            if sma_val == 0 or pd.isna(sma_val):
                return None
            
            pct_diff = ((current - sma_val) / sma_val) * 100
            return float(pct_diff) if pd.notna(pct_diff) else None
            
        except Exception:
            return None


class ScoringEngine:
    """
    Multi-pillar scoring engine.
    
    Pillars:
    - Value (EQUITY only): P/E, margins, fundamentals
    - Momentum: RSI, price vs SMA, trend
    - Safety: Volatility, drawdown, liquidity
    """
    
    def __init__(self):
        """Initialize scoring engine."""
        self._config = get_config().scoring
        self._features = FeatureCalculator()
    
    def compute_score(
        self,
        asset: Asset,
        df: pd.DataFrame,
        fundamentals: Optional[Dict[str, Any]] = None,
        gating: Optional[GatingStatus] = None
    ) -> Score:
        """
        Compute full score for an asset.
        
        Args:
            asset: Asset information
            df: OHLCV DataFrame
            fundamentals: Optional fundamental data dict
            gating: Optional gating status for confidence
            
        Returns:
            Score object with all metrics
        """
        # Calculate features
        rsi = self._features.rsi(df)
        zscore = self._features.zscore(df)
        vol_annual = self._features.volatility_annual(df)
        max_dd = self._features.max_drawdown(df)
        sma200 = self._features.sma(df, 200)
        price_vs_sma200 = self._features.price_vs_sma(df, 200)
        last_price = df["Close"].iloc[-1] if not df.empty and "Close" in df.columns else None
        
        # Calculate pillar scores
        momentum_score = self._score_momentum(rsi, price_vs_sma200)
        safety_score = self._score_safety(vol_annual, max_dd)
        
        # Value score only for equities with fundamentals
        value_score = None
        has_fundamentals = False
        
        if asset.asset_type == AssetType.EQUITY and fundamentals:
            value_score = self._score_value(fundamentals)
            has_fundamentals = value_score is not None
        
        # Calculate total score
        total_score, weights_used = self._calculate_total(
            asset_type=asset.asset_type,
            value_score=value_score,
            momentum_score=momentum_score,
            safety_score=safety_score
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            df=df,
            gating=gating,
            has_fundamentals=has_fundamentals,
            asset_type=asset.asset_type
        )
        
        # Determine state label
        state_label = self._determine_state(zscore, rsi)
        
        # Build breakdown
        breakdown = ScoreBreakdown(
            version="1.0",
            weights=weights_used,
            raw_values={
                "rsi": rsi,
                "zscore": zscore,
                "vol_annual": vol_annual,
                "max_drawdown": max_dd,
                "price_vs_sma200": price_vs_sma200,
                "fundamentals": fundamentals or {}
            },
            normalized_values={
                "momentum": momentum_score,
                "safety": safety_score,
                "value": value_score
            },
            confidence_components={
                "data_coverage": gating.coverage * 100 if gating else 50,
                "data_freshness": 80,  # Placeholder
                "fundamentals": 100 if has_fundamentals else 0
            }
        )
        
        return Score(
            asset_id=asset.asset_id,
            score_total=total_score,
            score_value=value_score,
            score_momentum=momentum_score,
            score_safety=safety_score,
            confidence=confidence,
            state_label=state_label,
            rsi=rsi,
            zscore=zscore,
            vol_annual=vol_annual,
            max_drawdown=max_dd,
            sma200=sma200,
            last_price=float(last_price) if last_price and pd.notna(last_price) else None,
            fundamentals_available=has_fundamentals,
            breakdown=breakdown
        )
    
    def _score_momentum(
        self,
        rsi: Optional[float],
        price_vs_sma: Optional[float]
    ) -> Optional[float]:
        """
        Calculate momentum pillar score.
        
        Components:
        - RSI: Optimal 40-70, penalize extremes
        - Price vs SMA200: Higher = better
        """
        scores = []
        
        # RSI score (40-70 is optimal)
        if rsi is not None:
            if 40 <= rsi <= 70:
                rsi_score = 100 - abs(rsi - 55) * 2  # Peak at 55
            elif rsi < 40:
                rsi_score = max(0, rsi * 2)  # Lower scores for oversold
            else:
                rsi_score = max(0, 100 - (rsi - 70) * 3)  # Penalize overbought
            scores.append(rsi_score)
        
        # Price vs SMA200 score
        if price_vs_sma is not None:
            # Above SMA is positive
            sma_score = normalize(price_vs_sma, -20, 20, invert=False)
            if sma_score is not None:
                scores.append(sma_score)
        
        if not scores:
            return None
        
        return round(sum(scores) / len(scores), 1)
    
    def _score_safety(
        self,
        volatility: Optional[float],
        drawdown: Optional[float]
    ) -> Optional[float]:
        """
        Calculate safety pillar score.
        
        Components:
        - Volatility: Lower is better
        - Max Drawdown: Lower is better
        """
        scores = []
        
        # Volatility score (inverted - lower vol = higher score)
        if volatility is not None:
            vol_score = normalize(volatility, 5, 50, invert=True)
            if vol_score is not None:
                scores.append(vol_score)
        
        # Drawdown score (inverted - lower drawdown = higher score)
        if drawdown is not None:
            dd_score = normalize(drawdown, 0, 40, invert=True)
            if dd_score is not None:
                scores.append(dd_score)
        
        if not scores:
            return None
        
        return round(sum(scores) / len(scores), 1)
    
    def _score_value(self, fundamentals: Dict[str, Any]) -> Optional[float]:
        """
        Calculate value pillar score (EQUITY only).
        
        Components:
        - P/E ratio: Lower is better (within reason)
        - Profit margin: Higher is better
        """
        scores = []
        
        # P/E score (optimal 5-25)
        pe = fundamentals.get("pe_ratio")
        if pe is not None and pe > 0:
            pe_score = normalize(pe, 5, 50, invert=True)
            if pe_score is not None:
                scores.append(pe_score)
        
        # Profit margin score
        margin = fundamentals.get("profit_margin")
        if margin is not None:
            margin_pct = margin * 100 if margin < 1 else margin
            margin_score = normalize(margin_pct, 0, 30, invert=False)
            if margin_score is not None:
                scores.append(margin_score)
        
        # ROE score
        roe = fundamentals.get("return_on_equity")
        if roe is not None:
            roe_pct = roe * 100 if roe < 1 else roe
            roe_score = normalize(roe_pct, 0, 25, invert=False)
            if roe_score is not None:
                scores.append(roe_score)
        
        if not scores:
            return None
        
        return round(sum(scores) / len(scores), 1)
    
    def _calculate_total(
        self,
        asset_type: AssetType,
        value_score: Optional[float],
        momentum_score: Optional[float],
        safety_score: Optional[float]
    ) -> tuple:
        """
        Calculate weighted total score based on asset type.
        
        Returns:
            Tuple of (total_score, weights_used_dict)
        """
        # Get weights based on asset type
        if asset_type == AssetType.EQUITY:
            base_weights = self._config.equity_weights.copy()
        else:
            base_weights = self._config.etf_weights.copy()
        
        # Build scores dict
        pillar_scores = {
            "value": value_score,
            "momentum": momentum_score,
            "safety": safety_score
        }
        
        # Calculate actual weights (redistribute if pillars missing)
        active_weights = {}
        total_weight = 0
        
        for pillar, weight in base_weights.items():
            if pillar_scores.get(pillar) is not None:
                active_weights[pillar] = weight
                total_weight += weight
        
        if total_weight == 0 or not active_weights:
            return None, base_weights
        
        # Normalize weights
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}
        
        # Calculate weighted sum
        total = 0
        for pillar, weight in normalized_weights.items():
            score = pillar_scores.get(pillar, 0) or 0
            total += score * weight
        
        return round(total, 1), normalized_weights
    
    def _calculate_confidence(
        self,
        df: pd.DataFrame,
        gating: Optional[GatingStatus],
        has_fundamentals: bool,
        asset_type: AssetType
    ) -> int:
        """
        Calculate overall confidence score.
        """
        scores = []
        
        # Data coverage
        if gating:
            scores.append(gating.coverage * 100)
        elif not df.empty:
            scores.append(70)  # Assume decent if we have data
        else:
            scores.append(20)
        
        # Data recency (is most recent bar today or yesterday?)
        if not df.empty:
            last_date = df.index.max()
            days_old = (pd.Timestamp.now() - last_date).days
            recency_score = max(0, 100 - days_old * 10)
            scores.append(recency_score)
        
        # Fundamentals (only relevant for equities)
        if asset_type == AssetType.EQUITY:
            scores.append(100 if has_fundamentals else 40)
        
        # Average
        if not scores:
            return 50
        
        return int(round(sum(scores) / len(scores)))
    
    def _determine_state(
        self,
        zscore: Optional[float],
        rsi: Optional[float]
    ) -> StateLabel:
        """
        Determine state label based on metrics.
        Uses neutral, non-advisory language.
        """
        if zscore is None and rsi is None:
            return StateLabel.NA
        
        # Check for extensions based on z-score
        if zscore is not None:
            if zscore > 2.0:
                return StateLabel.EXTENSION_HAUTE
            elif zscore < -2.0:
                return StateLabel.EXTENSION_BASSE
        
        # Check RSI for stress conditions
        if rsi is not None:
            if rsi > 80:
                return StateLabel.STRESS_HAUSSIER
            elif rsi < 20:
                return StateLabel.STRESS_BAISSIER
        
        return StateLabel.EQUILIBRE
