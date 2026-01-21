"""
MarketGPS - On-Demand Scoring Service
=====================================
Service pour le calcul de score a la demande avec gestion des quotas.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config, get_logger
from core.models import Asset, AssetType, Score
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

QUOTA_FREE_DAILY = 3
QUOTA_PRO_DAILY = 200
SCORE_FRESH_HOURS = 24


class QuotaExceededError(Exception):
    """Raised when user has exceeded their daily scoring quota."""
    pass


class AssetNotFoundError(Exception):
    """Raised when requested asset is not in the universe."""
    pass


class ScoringError(Exception):
    """Raised when scoring calculation fails."""
    pass


class QuotaManager:
    """Manages user scoring quotas."""
    
    def __init__(self, store: SQLiteStore):
        self._store = store
    
    def get_user_quota(self, user_id: str) -> Dict[str, Any]:
        """Get current quota status for a user."""
        with self._store._get_connection() as conn:
            row = conn.execute("""
                SELECT plan, status, daily_quota_used, daily_quota_limit
                FROM subscriptions_state WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            if not row:
                conn.execute("""
                    INSERT INTO subscriptions_state 
                    (user_id, plan, status, daily_quota_used, daily_quota_limit)
                    VALUES (?, 'free', 'active', 0, ?)
                """, (user_id, QUOTA_FREE_DAILY))
                return {
                    "plan": "free", "daily_used": 0, "daily_limit": QUOTA_FREE_DAILY,
                    "remaining": QUOTA_FREE_DAILY, "is_pro": False, "is_annual": False, "can_score": True,
                }
            
            r = dict(row)
            plan = r.get("plan", "free")
            daily_used = r.get("daily_quota_used", 0) or 0
            daily_limit = r.get("daily_quota_limit", QUOTA_FREE_DAILY) or QUOTA_FREE_DAILY
            
            is_pro = plan in ("monthly_9_99", "yearly_50", "pro", "enterprise")
            is_annual = plan in ("yearly_50", "enterprise")
            
            if is_annual:
                daily_limit = 99999
            
            remaining = max(0, daily_limit - daily_used)
            
            return {
                "plan": plan, "daily_used": daily_used, "daily_limit": daily_limit,
                "remaining": remaining, "is_pro": is_pro, "is_annual": is_annual,
                "can_score": remaining > 0 or is_annual,
            }
    
    def check_and_reset_daily(self, user_id: str) -> None:
        """Check if quota should be reset (new day) and reset if needed."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        with self._store._get_connection() as conn:
            row = conn.execute("""
                SELECT date FROM usage_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1
            """, (user_id,)).fetchone()
            
            if row and row["date"] != today:
                conn.execute("""
                    UPDATE subscriptions_state SET daily_quota_used = 0 WHERE user_id = ?
                """, (user_id,))
                logger.info(f"Reset daily quota for user {user_id}")
    
    def increment_usage(self, user_id: str) -> None:
        """Increment the daily usage count for a user."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        with self._store._get_connection() as conn:
            conn.execute("""
                UPDATE subscriptions_state SET daily_quota_used = daily_quota_used + 1, updated_at = datetime('now')
                WHERE user_id = ?
            """, (user_id,))
            conn.execute("""
                INSERT INTO usage_daily (user_id, date, calculations_count) VALUES (?, ?, 1)
                ON CONFLICT(user_id, date) DO UPDATE SET calculations_count = calculations_count + 1
            """, (user_id, today))
    
    def can_calculate_score(self, user_id: str) -> Tuple[bool, str]:
        """Check if user can calculate a score."""
        self.check_and_reset_daily(user_id)
        quota = self.get_user_quota(user_id)
        
        if quota["is_annual"]:
            return True, "Unlimited (Pro Annual)"
        if quota["remaining"] > 0:
            return True, f"{quota['remaining']} remaining today"
        return False, f"Daily limit reached ({quota['daily_limit']}/day). Upgrade to Pro Annual for unlimited access."


class OnDemandScoringService:
    """Service for calculating scores on-demand."""
    
    def __init__(self, store: Optional[SQLiteStore] = None):
        self._store = store or SQLiteStore()
        self._quota_manager = QuotaManager(self._store)
        self._config = get_config()
    
    def get_cached_score(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get cached score if it exists and is fresh (< 24h)."""
        with self._store._get_connection() as conn:
            row = conn.execute("""
                SELECT s.*, u.symbol, u.name, u.asset_type, u.market_scope, u.market_code
                FROM scores_latest s JOIN universe u ON s.asset_id = u.asset_id
                WHERE s.asset_id = ? AND s.score_total IS NOT NULL
            """, (asset_id,)).fetchone()
            
            if not row:
                return None
            
            r = dict(row)
            updated_at = r.get("updated_at")
            if updated_at:
                try:
                    score_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    age_hours = (datetime.now() - score_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours < SCORE_FRESH_HOURS:
                        r["is_fresh"] = True
                        r["age_hours"] = round(age_hours, 1)
                        return r
                except Exception:
                    pass
            return None
    
    def calculate_score(self, ticker: str, user_id: str = "default", force: bool = False) -> Dict[str, Any]:
        """Calculate score for an asset on-demand."""
        asset_id = self._resolve_asset_id(ticker)
        if not asset_id:
            raise AssetNotFoundError(f"Asset '{ticker}' not found in universe")
        
        if not force:
            cached = self.get_cached_score(asset_id)
            if cached:
                logger.info(f"Returning cached score for {ticker}")
                cached["from_cache"] = True
                cached["quota_used"] = False
                return cached
        
        can_score, reason = self._quota_manager.can_calculate_score(user_id)
        if not can_score:
            raise QuotaExceededError(reason)
        
        try:
            score_result = self._compute_score_for_asset(asset_id)
        except Exception as e:
            logger.error(f"Scoring failed for {ticker}: {e}")
            raise ScoringError(f"Failed to calculate score: {str(e)}")
        
        self._quota_manager.increment_usage(user_id)
        score_result["from_cache"] = False
        score_result["quota_used"] = True
        
        quota = self._quota_manager.get_user_quota(user_id)
        score_result["quota_remaining"] = quota["remaining"]
        
        return score_result
    
    def _resolve_asset_id(self, ticker: str) -> Optional[str]:
        """Resolve ticker to asset_id."""
        ticker_upper = ticker.upper().strip()
        
        with self._store._get_connection() as conn:
            row = conn.execute("""
                SELECT asset_id FROM universe WHERE UPPER(symbol) = ?
                ORDER BY CASE market_scope WHEN 'US_EU' THEN 0 ELSE 1 END,
                         CASE market_code WHEN 'US' THEN 0 ELSE 1 END LIMIT 1
            """, (ticker_upper,)).fetchone()
            
            if row:
                return row["asset_id"]
            
            for suffix in [".US", ".PA", ".XETRA", ".LSE", ".JSE", ".NG", ".BC"]:
                candidate = f"{ticker_upper}{suffix}"
                row = conn.execute("SELECT asset_id FROM universe WHERE asset_id = ?", (candidate,)).fetchone()
                if row:
                    return row["asset_id"]
        return None
    
    def _compute_score_for_asset(self, asset_id: str) -> Dict[str, Any]:
        """Actually compute the score for an asset."""
        from providers.eodhd import EODHDProvider
        from pipeline.scoring import ScoringEngine
        from storage.parquet_store import ParquetStore
        
        asset = self._store.get_asset(asset_id)
        if not asset:
            raise AssetNotFoundError(f"Asset {asset_id} not found")
        
        provider = EODHDProvider()
        scope = asset.market_scope if hasattr(asset, 'market_scope') else "US_EU"
        parquet = ParquetStore(market_scope=scope)
        
        logger.info(f"Fetching data for {asset_id}...")
        
        try:
            df = provider.get_ohlcv(asset_id=asset_id, lookback_days=self._config.scoring_lookback_days)
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {asset_id}: {e}")
            raise ScoringError(f"Could not fetch price data: {str(e)}")
        
        if df.empty or len(df) < 50:
            raise ScoringError(f"Insufficient data for {asset_id} ({len(df)} bars)")
        
        try:
            parquet.write(asset_id, df)
        except Exception as e:
            logger.warning(f"Failed to cache parquet for {asset_id}: {e}")
        
        fundamentals = None
        if asset.asset_type == AssetType.EQUITY:
            try:
                fundamentals = provider.get_fundamentals(asset_id)
            except Exception as e:
                logger.debug(f"No fundamentals for {asset_id}: {e}")
        
        gating = self._store.get_gating_status(asset_id)
        
        engine = ScoringEngine()
        score = engine.compute_score(asset=asset, df=df, fundamentals=fundamentals, gating=gating)
        
        self._store.upsert_score(score, market_scope=scope)
        
        logger.info(f"Scored {asset_id}: {score.score_total}")
        
        return {
            "asset_id": asset_id, "symbol": asset.symbol, "name": asset.name,
            "asset_type": asset.asset_type.value, "market_scope": scope,
            "score_total": score.score_total, "score_value": score.score_value,
            "score_momentum": score.score_momentum, "score_safety": score.score_safety,
            "confidence": score.confidence, "rsi": score.rsi, "zscore": score.zscore,
            "vol_annual": score.vol_annual, "max_drawdown": score.max_drawdown,
            "last_price": score.last_price,
            "state_label": score.state_label.value if score.state_label else None,
            "updated_at": datetime.now().isoformat(),
        }
    
    def get_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get current quota status for a user."""
        return self._quota_manager.get_user_quota(user_id)
