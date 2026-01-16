"""
MarketGPS v14.0 - Africa Scoring Engine v2
Production-grade scoring for African markets with detailed breakdown.

Scoring pillars:
1. Momentum (35%): 6M/12M returns, SMA, RSI
2. Safety (25%): Volatility, drawdown, data stability
3. Value (20%): Fundamentals if available, else neutral
4. FX Risk (10%): Currency volatility penalty
5. Liquidity Risk (10%): Market depth penalty

Output:
- score_total (0-100)
- score_momentum, score_safety, score_value
- score_fx_risk, score_liquidity_risk
- confidence (0-100)
- json_breakdown with full transparency
"""

import json
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np

from core.config import get_config, get_logger
from core.models import Score, StateLabel, ScoreBreakdown
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from pipeline.africa.exchanges_catalog import (
    AFRICA_EXCHANGES,
    CURRENCY_INFO,
    get_exchange_info,
    get_currency_volatility,
    get_min_liquidity_for_exchange,
)
from pipeline.africa.gating_africa import (
    compute_coverage_africa,
    compute_stale_ratio_africa,
    compute_liquidity_africa,
    compute_fx_risk,
    compute_liquidity_risk,
)

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SCORING WEIGHTS (AFRICA-SPECIFIC)
# ═══════════════════════════════════════════════════════════════════════════

AFRICA_SCORING_WEIGHTS = {
    "EQUITY": {
        "momentum": 0.35,
        "safety": 0.25,
        "value": 0.20,
        "fx_risk": 0.10,
        "liquidity_risk": 0.10
    },
    "ETF": {
        "momentum": 0.40,
        "safety": 0.30,
        "value": 0.00,
        "fx_risk": 0.15,
        "liquidity_risk": 0.15
    },
    "BOND": {
        "momentum": 0.25,
        "safety": 0.45,
        "value": 0.10,
        "fx_risk": 0.10,
        "liquidity_risk": 0.10
    },
    "DEFAULT": {
        "momentum": 0.35,
        "safety": 0.30,
        "value": 0.15,
        "fx_risk": 0.10,
        "liquidity_risk": 0.10
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# SCORING ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════

class ScoringAfricaEngine:
    """
    Africa-specific scoring engine with full transparency.
    
    Features:
    - 5 pillar scoring system
    - Exchange-aware thresholds
    - Currency risk integration
    - Detailed breakdown export
    - Staging table support
    """
    
    VERSION = "AFRICA_2.0"
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        parquet_store: Optional[ParquetStore] = None
    ):
        """
        Initialize scoring engine.
        
        Args:
            store: SQLite store for metadata and calibration
            parquet_store: Parquet store for price data
        """
        self._store = store or SQLiteStore()
        self._parquet = parquet_store or ParquetStore(market_scope="AFRICA")
        self._config = get_config()
        
        # Load calibration params (can override defaults)
        self._calibration = self._store.get_calibration_params("AFRICA")
    
    def score_asset(self, asset_id: str) -> Optional[Score]:
        """
        Calculate comprehensive score for an African asset.
        
        Args:
            asset_id: Asset ID (e.g., "NPN.JSE")
            
        Returns:
            Score object with all metrics and breakdown
        """
        try:
            # 1. Load asset metadata
            asset = self._store.get_asset(asset_id)
            if not asset:
                logger.warning(f"[AFRICA] Asset not found: {asset_id}")
                return None
            
            # 2. Load price data
            df = self._parquet.load_bars(asset_id)
            if df is None or df.empty:
                logger.warning(f"[AFRICA] No price data for {asset_id}")
                return self._create_no_data_score(asset_id, "No price data")
            
            # Normalize columns
            df.columns = df.columns.str.lower()
            if "close" not in df.columns:
                logger.error(f"[AFRICA] No 'close' column for {asset_id}")
                return None
            
            if len(df) < 50:
                logger.warning(f"[AFRICA] Insufficient data for {asset_id}: {len(df)} bars")
                return self._create_no_data_score(asset_id, f"Only {len(df)} bars")
            
            # 3. Get asset metadata
            currency = getattr(asset, 'currency', 'ZAR')
            exchange_code = getattr(asset, 'exchange', 'JSE')
            asset_type = (
                asset.asset_type.value 
                if hasattr(asset.asset_type, 'value') 
                else str(asset.asset_type)
            )
            
            # 4. Calculate features
            features = self._calculate_features(df)
            
            # 5. Get gating info for context
            gating = self._store.get_gating(asset_id)
            
            # 6. Calculate FX and liquidity metrics
            fx_risk_raw = compute_fx_risk(currency)
            adv = features.get("adv", 0)
            liquidity_risk_raw = compute_liquidity_risk(df, exchange_code, adv)
            
            # 7. Calculate pillar scores
            momentum_score = self._score_momentum(features)
            safety_score = self._score_safety(features)
            value_score = self._score_value(asset_id, asset_type)
            fx_risk_score = self._score_fx_risk(fx_risk_raw)
            liquidity_risk_score = self._score_liquidity_risk(liquidity_risk_raw, features)
            
            # 8. Get weights for asset type
            weights = AFRICA_SCORING_WEIGHTS.get(asset_type, AFRICA_SCORING_WEIGHTS["DEFAULT"])
            
            # 9. Calculate total score
            total_score = (
                momentum_score * weights["momentum"] +
                safety_score * weights["safety"] +
                value_score * weights["value"] +
                fx_risk_score * weights["fx_risk"] +
                liquidity_risk_score * weights["liquidity_risk"]
            )
            
            # 10. Calculate confidence
            confidence = self._calculate_confidence(
                df=df,
                features=features,
                gating=gating,
                fx_risk_raw=fx_risk_raw,
                liquidity_risk_raw=liquidity_risk_raw,
                exchange_code=exchange_code,
                has_fundamentals=False  # TODO: Add fundamentals
            )
            
            # 11. Determine state label
            state_label = self._determine_state(features.get("zscore", 0), features.get("rsi", 50))
            
            # 12. Build breakdown
            breakdown = self._build_breakdown(
                features=features,
                scores={
                    "momentum": momentum_score,
                    "safety": safety_score,
                    "value": value_score,
                    "fx_risk": fx_risk_score,
                    "liquidity_risk": liquidity_risk_score
                },
                weights=weights,
                confidence=confidence,
                fx_risk_raw=fx_risk_raw,
                liquidity_risk_raw=liquidity_risk_raw,
                currency=currency,
                exchange_code=exchange_code
            )
            
            return Score(
                asset_id=asset_id,
                score_total=round(total_score, 1),
                score_momentum=round(momentum_score, 1),
                score_safety=round(safety_score, 1),
                score_value=round(value_score, 1),
                score_fx_risk=round(fx_risk_score, 1),
                score_liquidity_risk=round(liquidity_risk_score, 1),
                confidence=round(confidence),
                state_label=state_label,
                rsi=features.get("rsi"),
                zscore=features.get("zscore"),
                vol_annual=features.get("vol_annual"),
                max_drawdown=features.get("max_drawdown"),
                sma200=features.get("sma200"),
                last_price=features.get("last_price"),
                fundamentals_available=False,
                breakdown=breakdown
            )
            
        except Exception as e:
            logger.error(f"[AFRICA] Scoring failed for {asset_id}: {e}", exc_info=True)
            return None
    
    def _calculate_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical features from price data."""
        close = df["close"]
        features = {}
        
        # Basic price info
        features["last_price"] = float(close.iloc[-1])
        features["bar_count"] = len(df)
        features["coverage"] = 1.0 - (close.isna().sum() / len(close))
        
        # RSI (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        features["rsi"] = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0
        
        # Moving Averages
        features["sma20"] = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
        features["sma50"] = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        features["sma200"] = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        
        # Price vs SMA200
        if features["sma200"]:
            features["price_vs_sma200"] = (features["last_price"] / features["sma200"] - 1) * 100
        else:
            features["price_vs_sma200"] = 0.0
        
        # Returns
        if len(close) >= 126:
            features["return_6m"] = (close.iloc[-1] / close.iloc[-126] - 1) * 100
        else:
            features["return_6m"] = 0.0
        
        if len(close) >= 252:
            features["return_12m"] = (close.iloc[-1] / close.iloc[-252] - 1) * 100
        else:
            features["return_12m"] = 0.0
        
        # Volatility (annualized)
        returns = close.pct_change().dropna()
        features["vol_annual"] = float(returns.std() * np.sqrt(252) * 100) if len(returns) > 20 else 30.0
        
        # Max Drawdown
        lookback = min(252, len(close))
        if lookback >= 21:
            rolling_max = close.tail(lookback).expanding().max()
            drawdown = (close.tail(lookback) - rolling_max) / rolling_max
            features["max_drawdown"] = abs(float(drawdown.min()) * 100)
        else:
            features["max_drawdown"] = 20.0
        
        # Z-Score
        if len(close) >= 20:
            sma = close.rolling(20).mean()
            std = close.rolling(20).std()
            zscore = (close - sma) / std.replace(0, 1e-10)
            features["zscore"] = float(zscore.iloc[-1]) if pd.notna(zscore.iloc[-1]) else 0.0
        else:
            features["zscore"] = 0.0
        
        # ADV (Average Dollar Value)
        if "volume" in df.columns:
            features["adv"] = float((df["close"] * df["volume"]).tail(20).median())
        else:
            features["adv"] = 0.0
        
        # Downside deviation
        neg_returns = returns[returns < 0]
        features["downside_deviation"] = float(neg_returns.std() * np.sqrt(252) * 100) if len(neg_returns) > 10 else 15.0
        
        # Stale ratio
        features["stale_ratio"] = float(compute_stale_ratio_africa(df))
        
        return features
    
    def _score_momentum(self, features: Dict) -> float:
        """
        Score momentum pillar.
        
        Components (equal weight):
        - RSI position (optimal 45-65)
        - Price vs SMA200
        - 6M return
        - 12M return
        """
        scores = []
        
        # RSI score (45-65 optimal for African markets - less volatile)
        rsi = features.get("rsi", 50)
        if 45 <= rsi <= 65:
            rsi_score = 100 - abs(rsi - 55) * 2
        elif rsi < 30:
            rsi_score = 40  # Oversold - potential
        elif rsi > 80:
            rsi_score = 30  # Overbought risk
        else:
            rsi_score = self._normalize(abs(rsi - 55), 0, 35, invert=True)
        scores.append(rsi_score)
        
        # Price vs SMA200
        price_vs_sma = features.get("price_vs_sma200", 0)
        if price_vs_sma >= 0:
            sma_score = min(100, 60 + price_vs_sma * 2)
        else:
            sma_score = max(20, 60 + price_vs_sma * 2)
        scores.append(sma_score)
        
        # 6M return score
        ret_6m = features.get("return_6m", 0)
        ret_6m_score = self._normalize(ret_6m, -30, 50, invert=False)
        scores.append(ret_6m_score)
        
        # 12M return score
        ret_12m = features.get("return_12m", 0)
        ret_12m_score = self._normalize(ret_12m, -40, 60, invert=False)
        scores.append(ret_12m_score)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _score_safety(self, features: Dict) -> float:
        """
        Score safety pillar.
        
        Components:
        - Volatility (lower = better)
        - Max drawdown (lower = better)
        - Downside deviation (lower = better)
        - Data stability (lower stale ratio = better)
        """
        scores = []
        
        # Volatility score (Africa targets: 20-45% is acceptable)
        vol = features.get("vol_annual", 30)
        vol_score = self._normalize(vol, 15, 60, invert=True)
        scores.append(vol_score * 0.35)
        
        # Max drawdown score
        mdd = features.get("max_drawdown", 20)
        mdd_score = self._normalize(mdd, 5, 50, invert=True)
        scores.append(mdd_score * 0.30)
        
        # Downside deviation score
        dd = features.get("downside_deviation", 15)
        dd_score = self._normalize(dd, 5, 35, invert=True)
        scores.append(dd_score * 0.20)
        
        # Data stability score (stale ratio)
        stale = features.get("stale_ratio", 0.1)
        stale_score = self._normalize(stale, 0, 0.35, invert=True)
        scores.append(stale_score * 0.15)
        
        return sum(scores) if scores else 50.0
    
    def _score_value(self, asset_id: str, asset_type: str) -> float:
        """
        Score value pillar.
        
        For African markets, fundamentals are often unavailable.
        Returns neutral score (50) when no data available.
        
        TODO: Integrate fundamentals from EODHD when available.
        """
        # Try to get fundamentals
        try:
            # Placeholder - would fetch from provider
            fundamentals = None  # self._fetch_fundamentals(asset_id)
            
            if fundamentals:
                return self._score_fundamentals(fundamentals)
            
        except Exception:
            pass
        
        # Return neutral score for equities without fundamentals
        if asset_type == "EQUITY":
            return 50.0  # Neutral
        else:
            return 50.0  # Not applicable for non-equities
    
    def _score_fx_risk(self, fx_risk_raw: float) -> float:
        """
        Score FX risk (higher score = LOWER risk = better).
        
        Inverted: high currency volatility = low score.
        
        Args:
            fx_risk_raw: Raw FX risk factor (0-1)
            
        Returns:
            Score 0-100 (100 = stable currency)
        """
        # Invert: low risk = high score
        return (1.0 - fx_risk_raw) * 100
    
    def _score_liquidity_risk(
        self,
        liquidity_risk_raw: float,
        features: Dict
    ) -> float:
        """
        Score liquidity risk (higher score = LOWER risk = better).
        
        Args:
            liquidity_risk_raw: Raw liquidity risk (0-1)
            features: Calculated features
            
        Returns:
            Score 0-100 (100 = highly liquid)
        """
        # Base score from risk
        base_score = (1.0 - liquidity_risk_raw) * 100
        
        # Bonus for high ADV
        adv = features.get("adv", 0)
        if adv > 1_000_000:
            bonus = 10
        elif adv > 500_000:
            bonus = 5
        else:
            bonus = 0
        
        return min(100, base_score + bonus)
    
    def _calculate_confidence(
        self,
        df: pd.DataFrame,
        features: Dict,
        gating: Optional[Any],
        fx_risk_raw: float,
        liquidity_risk_raw: float,
        exchange_code: str,
        has_fundamentals: bool
    ) -> int:
        """
        Calculate overall confidence score.
        
        Components:
        - Data coverage (25%)
        - Data freshness (20%)
        - Data stability (15%)
        - FX stability (15%)
        - Market liquidity (15%)
        - Fundamentals (10%)
        """
        components = []
        
        # Data coverage (25%)
        coverage = features.get("coverage", 0.9)
        coverage_score = min(100, coverage * 100 / 0.70) * 0.25
        components.append(coverage_score)
        
        # Data freshness (20%)
        if not df.empty:
            last_date = df.index.max()
            days_old = (datetime.now() - pd.Timestamp(last_date).to_pydatetime()).days
            freshness = max(0, 100 - days_old * 10)
        else:
            freshness = 0
        components.append(freshness * 0.20)
        
        # Data stability (15%)
        stale_ratio = features.get("stale_ratio", 0.1)
        stability = max(0, (1 - stale_ratio / 0.35) * 100)
        components.append(stability * 0.15)
        
        # FX stability (15%)
        fx_stability = (1 - fx_risk_raw) * 100
        components.append(fx_stability * 0.15)
        
        # Market liquidity (15%)
        liq_score = (1 - liquidity_risk_raw) * 100
        components.append(liq_score * 0.15)
        
        # Fundamentals (10%)
        fund_score = 100 if has_fundamentals else 40
        components.append(fund_score * 0.10)
        
        # History length penalty
        bar_count = features.get("bar_count", 0)
        if bar_count < 260:
            penalty = (260 - bar_count) / 260 * 20
        else:
            penalty = 0
        
        total = sum(components) - penalty
        return int(round(min(100, max(0, total))))
    
    def _determine_state(self, zscore: float, rsi: float) -> StateLabel:
        """Determine market state label."""
        if zscore > 2.0:
            return StateLabel.EXTENSION_HAUTE
        elif zscore < -2.0:
            return StateLabel.EXTENSION_BASSE
        elif rsi > 75:
            return StateLabel.STRESS_HAUSSIER
        elif rsi < 25:
            return StateLabel.STRESS_BAISSIER
        else:
            return StateLabel.EQUILIBRE
    
    def _build_breakdown(
        self,
        features: Dict,
        scores: Dict,
        weights: Dict,
        confidence: int,
        fx_risk_raw: float,
        liquidity_risk_raw: float,
        currency: str,
        exchange_code: str
    ) -> ScoreBreakdown:
        """Build detailed score breakdown."""
        return ScoreBreakdown(
            version=self.VERSION,
            scoring_date=datetime.now().isoformat(),
            features=features,
            normalized=scores,
            weights=weights,
            confidence_components={
                "data_coverage": features.get("coverage", 0) * 100,
                "bar_count": features.get("bar_count", 0),
                "stale_ratio": features.get("stale_ratio", 0),
                "fx_risk_raw": fx_risk_raw,
                "liquidity_risk_raw": liquidity_risk_raw,
                "currency": currency,
                "exchange": exchange_code,
                "total_confidence": confidence
            },
            raw_values={
                "rsi": features.get("rsi"),
                "zscore": features.get("zscore"),
                "vol_annual": features.get("vol_annual"),
                "max_drawdown": features.get("max_drawdown"),
                "return_6m": features.get("return_6m"),
                "return_12m": features.get("return_12m"),
                "adv": features.get("adv"),
                "downside_deviation": features.get("downside_deviation")
            }
        )
    
    def _create_no_data_score(self, asset_id: str, reason: str) -> Score:
        """Create placeholder score when data is unavailable."""
        return Score(
            asset_id=asset_id,
            score_total=None,
            score_momentum=None,
            score_safety=None,
            score_value=None,
            score_fx_risk=None,
            score_liquidity_risk=None,
            confidence=0,
            state_label=StateLabel.EQUILIBRE,
            rsi=None,
            zscore=None,
            vol_annual=None,
            max_drawdown=None,
            sma200=None,
            last_price=None,
            fundamentals_available=False,
            breakdown=ScoreBreakdown(
                version=self.VERSION,
                scoring_date=datetime.now().isoformat(),
                features={},
                normalized={},
                weights={},
                confidence_components={"reason": reason}
            )
        )
    
    @staticmethod
    def _normalize(
        value: float,
        min_val: float,
        max_val: float,
        invert: bool = False
    ) -> float:
        """Normalize value to 0-100 scale."""
        if value is None or np.isnan(value):
            return 50.0
        
        # Clamp to range
        clamped = max(min_val, min(max_val, value))
        
        # Normalize
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (clamped - min_val) / (max_val - min_val)
        
        # Convert to 0-100
        score = normalized * 100
        
        # Invert if needed
        if invert:
            score = 100 - score
        
        return round(score, 1)


# ═══════════════════════════════════════════════════════════════════════════
# BATCH SCORING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def score_africa_batch(
    asset_ids: list,
    store: Optional[SQLiteStore] = None,
    parquet_store: Optional[ParquetStore] = None,
    batch_size: int = 50
) -> Dict[str, int]:
    """
    Score a batch of African assets.
    
    Args:
        asset_ids: List of asset IDs
        store: SQLite store
        parquet_store: Parquet store (AFRICA scope)
        batch_size: Max assets per batch
        
    Returns:
        Dict with success/failed counts
    """
    engine = ScoringAfricaEngine(store=store, parquet_store=parquet_store)
    
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for asset_id in asset_ids[:batch_size]:
        try:
            score = engine.score_asset(asset_id)
            
            if score and score.score_total is not None:
                store = store or SQLiteStore()
                store.upsert_score(score, market_scope="AFRICA")
                results["success"] += 1
                logger.info(f"[AFRICA] Scored {asset_id}: {score.score_total}/100")
            else:
                results["skipped"] += 1
                
        except Exception as e:
            results["failed"] += 1
            logger.error(f"[AFRICA] Failed to score {asset_id}: {e}")
    
    logger.info(f"[AFRICA] Batch scoring: {results}")
    return results
