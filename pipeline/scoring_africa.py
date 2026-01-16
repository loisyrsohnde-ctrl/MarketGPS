"""
MarketGPS v11.0 - Africa Scoring Pipeline
Specialized scoring for African markets with FX risk and liquidity risk factors.
Supports: JSE (South Africa), NGX (Nigeria), BRVM (West Africa)
"""
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from core.config import get_config, get_logger
from core.models import Score, StateLabel, ScoreBreakdown
from core.scoring_specs import normalize
from storage.parquet_store import ParquetStore
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# AFRICA-SPECIFIC SCORING WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════

# Default weights for African markets (can be overridden via calibration_params)
AFRICA_WEIGHTS = {
    "EQUITY": {
        "momentum": 0.30,
        "safety": 0.30,
        "value": 0.15,
        "fx_risk": 0.15,
        "liquidity_risk": 0.10
    },
    "ETF": {
        "momentum": 0.40,
        "safety": 0.30,
        "fx_risk": 0.15,
        "liquidity_risk": 0.15
    },
    "DEFAULT": {
        "momentum": 0.35,
        "safety": 0.35,
        "fx_risk": 0.15,
        "liquidity_risk": 0.15
    }
}

# Currency volatility ratings (higher = more volatile)
CURRENCY_VOLATILITY = {
    "ZAR": 0.35,   # South African Rand - moderately volatile
    "NGN": 0.60,   # Nigerian Naira - highly volatile, managed float
    "XOF": 0.15,   # CFA Franc - pegged to EUR, low volatility
    "KES": 0.40,   # Kenyan Shilling - moderately volatile
    "GHS": 0.55,   # Ghanaian Cedi - volatile
    "USD": 0.00,   # Reference currency
    "EUR": 0.10    # Low volatility vs USD
}

# Market liquidity tiers
MARKET_LIQUIDITY_TIER = {
    "JSE": 1,     # High liquidity
    "NGX": 2,     # Medium liquidity
    "BRVM": 3,    # Lower liquidity
    "BVMAC": 3,   # Lower liquidity
    "EGX": 2,     # Egyptian Exchange
    "NSE": 2      # Nairobi
}


class AfricaScoringPipeline:
    """
    Scoring pipeline specialized for African markets.
    Includes FX risk and liquidity risk factors.
    """
    
    def __init__(self, sqlite_store: SQLiteStore, parquet_store: ParquetStore):
        self._store = sqlite_store
        self._pq = parquet_store
        self._config = get_config()
        self._calibration = sqlite_store.get_calibration_params("AFRICA")
    
    def score_asset(self, asset_id: str) -> Optional[Score]:
        """
        Calculate comprehensive score for an African asset.
        
        Returns:
            Score object with all pillar scores and breakdown
        """
        try:
            # 1. Load asset metadata
            asset = self._store.get_asset(asset_id)
            if not asset:
                logger.warning(f"Asset not found: {asset_id}")
                return None
            
            # 2. Load price history
            df = self._pq.load_bars(asset_id)
            if df is None or df.empty or len(df) < 50:
                logger.warning(f"Insufficient data for {asset_id}: {len(df) if df is not None else 0} bars")
                return self._create_no_data_score(asset_id, "Insufficient price history")
            
            # Normalize column names
            df.columns = df.columns.str.lower()
            if 'close' not in df.columns:
                logger.error(f"No 'close' column in data for {asset_id}")
                return None
            
            # 3. Calculate features
            features = self._calculate_features(df)
            
            # 4. Get market-specific factors
            currency = getattr(asset, 'currency', 'USD')
            exchange = getattr(asset, 'exchange', 'JSE')
            fx_risk_raw = CURRENCY_VOLATILITY.get(currency, 0.40)
            liquidity_tier = MARKET_LIQUIDITY_TIER.get(exchange, 3)
            
            # 5. Calculate pillar scores
            momentum_score = self._score_momentum(features)
            safety_score = self._score_safety(features)
            value_score = self._score_value(asset_id)  # From fundamentals if available
            fx_risk_score = self._score_fx_risk(fx_risk_raw)
            liquidity_risk_score = self._score_liquidity_risk(features, liquidity_tier)
            
            # 6. Get weights for asset type
            asset_type = asset.asset_type.value if hasattr(asset.asset_type, 'value') else asset.asset_type
            weights = AFRICA_WEIGHTS.get(asset_type, AFRICA_WEIGHTS["DEFAULT"])
            
            # 7. Calculate total score
            total_score = (
                momentum_score * weights.get("momentum", 0.35) +
                safety_score * weights.get("safety", 0.35) +
                value_score * weights.get("value", 0.0) +
                fx_risk_score * weights.get("fx_risk", 0.15) +
                liquidity_risk_score * weights.get("liquidity_risk", 0.15)
            )
            
            # 8. Calculate confidence
            confidence = self._calculate_confidence(df, features, fx_risk_raw, liquidity_tier)
            
            # 9. Determine state label
            state_label = self._determine_state(features.get("zscore", 0))
            
            # 10. Build breakdown
            breakdown = ScoreBreakdown(
                version="AFRICA_1.0",
                scoring_date=datetime.now().isoformat(),
                features=features,
                normalized={
                    "momentum": momentum_score,
                    "safety": safety_score,
                    "value": value_score,
                    "fx_risk": fx_risk_score,
                    "liquidity_risk": liquidity_risk_score
                },
                weights=weights,
                confidence_components={
                    "data_coverage": features.get("coverage", 0.9),
                    "data_freshness": 1.0 if self._is_data_fresh(df) else 0.7,
                    "fx_stability": 1.0 - fx_risk_raw,
                    "market_liquidity": 1.0 - (liquidity_tier - 1) * 0.25
                }
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
                fundamentals_available=False,  # TODO: Add fundamentals
                breakdown=breakdown
            )
            
        except Exception as e:
            logger.error(f"Scoring failed for {asset_id}: {e}", exc_info=True)
            return None
    
    def _calculate_features(self, df: pd.DataFrame) -> Dict:
        """Calculate technical features from price data."""
        close = df["close"]
        
        features = {
            "last_price": float(close.iloc[-1]),
            "coverage": 1.0 - (close.isna().sum() / len(close))
        }
        
        # RSI (14)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        features["rsi"] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        
        # SMAs
        features["sma20"] = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
        features["sma50"] = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        features["sma200"] = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        
        # Price vs SMA200
        if features["sma200"]:
            features["price_vs_sma200"] = (features["last_price"] / features["sma200"] - 1) * 100
        else:
            features["price_vs_sma200"] = 0.0
        
        # Volatility (annualized)
        returns = close.pct_change().dropna()
        features["vol_annual"] = float(returns.std() * np.sqrt(252) * 100) if len(returns) > 20 else 30.0
        
        # Max Drawdown (12 months)
        if len(close) >= 252:
            rolling_max = close.rolling(252).max()
            drawdown = (close - rolling_max) / rolling_max
            features["max_drawdown"] = abs(float(drawdown.min()) * 100)
        else:
            rolling_max = close.rolling(len(close)).max()
            drawdown = (close - rolling_max) / rolling_max
            features["max_drawdown"] = abs(float(drawdown.min()) * 100)
        
        # Z-Score (Bollinger-based)
        if len(close) >= 20:
            sma = close.rolling(20).mean()
            std = close.rolling(20).std()
            zscore = (close - sma) / std.replace(0, 1e-10)
            features["zscore"] = float(zscore.iloc[-1]) if not pd.isna(zscore.iloc[-1]) else 0.0
        else:
            features["zscore"] = 0.0
        
        # Momentum (12M return)
        if len(close) >= 252:
            features["momentum_12m"] = (close.iloc[-1] / close.iloc[-252] - 1) * 100
        else:
            features["momentum_12m"] = 0.0
        
        # ADV (Average Daily Value) - approximate
        if "volume" in df.columns:
            features["adv"] = float((df["close"] * df["volume"]).tail(20).mean())
        else:
            features["adv"] = 0.0
        
        return features
    
    def _score_momentum(self, features: Dict) -> float:
        """Score momentum pillar (higher = better trend)."""
        # RSI score (optimal 45-65 for African markets)
        rsi = features.get("rsi", 50)
        if 45 <= rsi <= 65:
            rsi_score = 100
        elif rsi < 30:
            rsi_score = 30  # Oversold
        elif rsi > 80:
            rsi_score = 20  # Overbought risk
        else:
            rsi_score = normalize(abs(rsi - 55), 0, 40, invert=True)
        
        # Price vs SMA200 score
        price_vs_sma = features.get("price_vs_sma200", 0)
        if price_vs_sma > 20:
            sma_score = 85
        elif price_vs_sma > 0:
            sma_score = normalize(price_vs_sma, 0, 20) * 0.4 + 60
        elif price_vs_sma > -15:
            sma_score = normalize(abs(price_vs_sma), 0, 15, invert=True) * 0.4 + 40
        else:
            sma_score = 30
        
        # Combine
        return rsi_score * 0.5 + sma_score * 0.5
    
    def _score_safety(self, features: Dict) -> float:
        """Score safety pillar (higher = lower risk)."""
        # Volatility score (lower = better, target < 35% for Africa)
        vol = features.get("vol_annual", 30)
        vol_score = normalize(vol, 15, 60, invert=True)
        
        # Max Drawdown score (lower = better, target < 30% for Africa)
        mdd = features.get("max_drawdown", 20)
        mdd_score = normalize(mdd, 10, 50, invert=True)
        
        # Combine
        return vol_score * 0.5 + mdd_score * 0.5
    
    def _score_value(self, asset_id: str) -> float:
        """Score value pillar from fundamentals (if available)."""
        # TODO: Implement fundamental scoring for African stocks
        # For now, return neutral score
        return 50.0
    
    def _score_fx_risk(self, fx_volatility: float) -> float:
        """
        Score FX risk (higher score = lower risk).
        
        Args:
            fx_volatility: Currency volatility factor (0-1)
        """
        # Invert: low volatility = high score
        return normalize(fx_volatility, 0, 0.7, invert=True)
    
    def _score_liquidity_risk(self, features: Dict, liquidity_tier: int) -> float:
        """
        Score liquidity risk (higher score = better liquidity).
        
        Args:
            features: Calculated features including ADV
            liquidity_tier: Market tier (1=high, 2=medium, 3=low)
        """
        # Base score from market tier
        tier_scores = {1: 80, 2: 55, 3: 35}
        base_score = tier_scores.get(liquidity_tier, 40)
        
        # Adjust for ADV if available
        adv = features.get("adv", 0)
        if adv > 1_000_000:
            adv_bonus = 20
        elif adv > 500_000:
            adv_bonus = 10
        elif adv > 100_000:
            adv_bonus = 5
        else:
            adv_bonus = 0
        
        return min(100, base_score + adv_bonus)
    
    def _calculate_confidence(
        self, 
        df: pd.DataFrame, 
        features: Dict,
        fx_risk: float,
        liquidity_tier: int
    ) -> float:
        """Calculate data confidence score (0-100)."""
        components = []
        
        # Data coverage (weight: 30%)
        coverage = features.get("coverage", 0.9)
        components.append(coverage * 100 * 0.30)
        
        # Data freshness (weight: 25%)
        freshness = 100 if self._is_data_fresh(df) else 60
        components.append(freshness * 0.25)
        
        # FX stability (weight: 20%)
        fx_score = (1 - fx_risk) * 100
        components.append(fx_score * 0.20)
        
        # Market liquidity (weight: 15%)
        liq_scores = {1: 100, 2: 70, 3: 45}
        liq_score = liq_scores.get(liquidity_tier, 50)
        components.append(liq_score * 0.15)
        
        # History length (weight: 10%)
        if len(df) >= 252:
            history_score = 100
        elif len(df) >= 126:
            history_score = 75
        else:
            history_score = 50
        components.append(history_score * 0.10)
        
        return sum(components)
    
    def _is_data_fresh(self, df: pd.DataFrame) -> bool:
        """Check if data is recent (within 5 business days)."""
        if df.empty:
            return False
        last_date = df.index.max()
        days_old = (datetime.now() - pd.Timestamp(last_date).to_pydatetime()).days
        return days_old <= 7
    
    def _determine_state(self, zscore: float) -> StateLabel:
        """Determine market state label based on Z-score."""
        if zscore > 2:
            return StateLabel.EXTENSION_HIGH
        elif zscore < -2:
            return StateLabel.EXTENSION_LOW
        else:
            return StateLabel.EQUILIBRIUM
    
    def _create_no_data_score(self, asset_id: str, reason: str) -> Score:
        """Create a placeholder score when data is insufficient."""
        return Score(
            asset_id=asset_id,
            score_total=None,
            score_momentum=None,
            score_safety=None,
            score_value=None,
            confidence=0,
            state_label=StateLabel.EQUILIBRIUM,
            rsi=None,
            zscore=None,
            vol_annual=None,
            max_drawdown=None,
            sma200=None,
            last_price=None,
            fundamentals_available=False,
            breakdown=ScoreBreakdown(
                version="AFRICA_1.0",
                scoring_date=datetime.now().isoformat(),
                features={},
                normalized={},
                weights={},
                confidence_components={"reason": reason}
            )
        )


def run_africa_scoring_batch(
    sqlite_store: SQLiteStore,
    parquet_store: ParquetStore,
    asset_ids: list,
    batch_size: int = 50
) -> Dict[str, int]:
    """
    Run scoring for a batch of African assets.
    
    Args:
        sqlite_store: SQLite store instance
        parquet_store: Parquet store instance (scope=AFRICA)
        asset_ids: List of asset IDs to score
        batch_size: Maximum assets per batch
        
    Returns:
        Dict with success/failure counts
    """
    pipeline = AfricaScoringPipeline(sqlite_store, parquet_store)
    
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for asset_id in asset_ids[:batch_size]:
        try:
            score = pipeline.score_asset(asset_id)
            
            if score and score.score_total is not None:
                sqlite_store.upsert_score(score, market_scope="AFRICA")
                results["success"] += 1
                logger.info(f"[AFRICA] Scored {asset_id}: {score.score_total}/100")
            else:
                results["skipped"] += 1
                logger.debug(f"[AFRICA] Skipped {asset_id}: No valid score")
                
        except Exception as e:
            results["failed"] += 1
            logger.error(f"[AFRICA] Failed to score {asset_id}: {e}")
    
    logger.info(
        f"[AFRICA] Scoring batch complete: "
        f"{results['success']} success, {results['failed']} failed, {results['skipped']} skipped"
    )
    
    return results
