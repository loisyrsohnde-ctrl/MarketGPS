"""
MarketGPS - Institutional Liquidity & Data Quality Guard
=========================================================
ADD-ONLY module - does NOT modify existing score_total behavior.

Purpose:
- Prevent illiquid/low-quality assets from appearing "excellent" for long-term investors
- Calculate score_institutional with liquidity and data quality penalties
- Classify assets into liquidity tiers (A/B/C/D)
- Recommend minimum investment horizons

IMPORTANT:
- score_total is PRESERVED as-is for backward compatibility
- All new fields are ADDITIVE (score_institutional, liquidity_tier, flags, etc.)
- This module runs AFTER the existing scoring pipeline

Usage:
    from pipeline.institutional_guard import InstitutionalGuard
    
    guard = InstitutionalGuard(store=sqlite_store, market_scope="US_EU")
    guard.run()  # Updates scores_latest with institutional fields
"""

from typing import Optional, Dict, Any, List, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime
import json

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]


# ═══════════════════════════════════════════════════════════════════════════
# INSTITUTIONAL THRESHOLDS (US/EU Market Standards)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class InstitutionalThresholds:
    """
    Thresholds based on institutional investment standards.
    
    Liquidity Tiers (based on Average Daily Volume in USD):
    - Tier A (Institutional): ADV >= $5M - Freely tradeable by institutions
    - Tier B (Good): $1M <= ADV < $5M - Tradeable with minor impact
    - Tier C (Limited): $500K <= ADV < $1M - Significant market impact risk
    - Tier D (Illiquid): ADV < $500K - Not suitable for institutional investment
    
    Data Quality:
    - Coverage: % of expected trading days with valid data
    - Stale Days: Days since last price movement
    - Zero Volume Ratio: % of days with zero volume
    """
    
    # Liquidity tiers (ADV_USD thresholds)
    TIER_A_ADV_MIN: float = 5_000_000     # Institutional grade
    TIER_B_ADV_MIN: float = 1_000_000     # Good liquidity
    TIER_C_ADV_MIN: float = 500_000       # Limited liquidity
    # Below TIER_C_ADV_MIN = Tier D (Illiquid)
    
    # Penalties by tier (points deducted from score)
    TIER_A_PENALTY: float = 0.0
    TIER_B_PENALTY: float = 5.0           # Minor penalty
    TIER_C_PENALTY: float = 20.0          # Significant penalty
    TIER_D_PENALTY: float = 45.0          # Severe penalty
    
    # Score caps by tier (maximum possible score_institutional)
    TIER_A_CAP: float = 100.0             # No cap
    TIER_B_CAP: float = 90.0              # Slight cap
    TIER_C_CAP: float = 70.0              # Moderate cap
    TIER_D_CAP: float = 55.0              # Severe cap
    
    # Data quality thresholds
    MIN_COVERAGE: float = 0.80            # 80% minimum data coverage
    MAX_STALE_DAYS: int = 7               # Max 7 days without price update
    MAX_ZERO_VOLUME_RATIO: float = 0.10   # Max 10% zero volume days
    MAX_STALE_RATIO: float = 0.15         # Max 15% unchanged price days
    
    # Data quality penalties
    LOW_COVERAGE_PENALTY: float = 15.0
    STALE_PRICE_PENALTY: float = 20.0
    ZERO_VOLUME_PENALTY: float = 10.0
    
    # Data quality caps
    LOW_COVERAGE_CAP: float = 65.0
    STALE_PRICE_CAP: float = 55.0
    
    # Recommended horizons (years)
    TIER_A_HORIZON: int = 10              # Long-term OK
    TIER_B_HORIZON: int = 5               # Medium-term
    TIER_C_HORIZON: int = 3               # Short-medium term
    TIER_D_HORIZON: int = 1               # Short-term only / Not recommended


THRESHOLDS = InstitutionalThresholds()


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class InstitutionalAssessment:
    """Result of institutional guard assessment for a single asset."""
    
    asset_id: str
    score_total: float
    score_institutional: float
    
    # Liquidity assessment
    liquidity_tier: str                   # A, B, C, D
    liquidity_penalty: float
    liquidity_flag: bool
    adv_usd: float
    market_cap: Optional[float]
    
    # Data quality assessment
    data_quality_score: float
    data_quality_flag: bool
    stale_price_flag: bool
    coverage: float
    stale_ratio: float
    zero_volume_ratio: float
    
    # Recommendation
    min_recommended_horizon_years: int
    
    # Explanation
    explanation: str
    penalties_applied: List[str]
    caps_applied: List[str]
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dict for database update."""
        return {
            "score_institutional": round(self.score_institutional, 1),
            "liquidity_tier": self.liquidity_tier,
            "liquidity_penalty": round(self.liquidity_penalty, 1),
            "liquidity_flag": 1 if self.liquidity_flag else 0,
            "data_quality_flag": 1 if self.data_quality_flag else 0,
            "data_quality_score": round(self.data_quality_score, 1),
            "stale_price_flag": 1 if self.stale_price_flag else 0,
            "min_recommended_horizon_years": self.min_recommended_horizon_years,
            "institutional_explanation": self.explanation,
            "adv_usd": round(self.adv_usd, 2) if self.adv_usd else None,
            "market_cap": round(self.market_cap, 2) if self.market_cap else None,
        }


# ═══════════════════════════════════════════════════════════════════════════
# INSTITUTIONAL GUARD IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════

class InstitutionalGuard:
    """
    Institutional Liquidity & Data Quality Guard.
    
    Calculates score_institutional by applying penalties and caps based on:
    1. Liquidity (ADV_USD)
    2. Data coverage
    3. Price staleness
    4. Volume patterns
    
    The original score_total is NEVER modified.
    """
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        market_scope: MarketScope = "US_EU",
        thresholds: InstitutionalThresholds = THRESHOLDS
    ):
        """
        Initialize Institutional Guard.
        
        Args:
            store: SQLite store instance
            market_scope: Market scope to process
            thresholds: Threshold configuration
        """
        self._store = store or SQLiteStore()
        self._market_scope = market_scope
        self._thresholds = thresholds
        self._config = get_config()
    
    def run(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Run the institutional guard on all scored assets.
        
        Args:
            batch_size: Number of assets to process per batch
            
        Returns:
            Dict with processing stats
        """
        logger.info(f"Starting Institutional Guard [{self._market_scope}]")
        
        stats = {
            "processed": 0,
            "updated": 0,
            "tier_a": 0,
            "tier_b": 0,
            "tier_c": 0,
            "tier_d": 0,
            "liquidity_flagged": 0,
            "quality_flagged": 0,
            "errors": 0
        }
        
        try:
            # Ensure columns exist
            self._ensure_columns()
            
            # Get all scored assets with gating info
            assets_data = self._get_scored_assets_with_gating()
            
            logger.info(f"[{self._market_scope}] Processing {len(assets_data)} scored assets")
            
            # Process in batches
            for i in range(0, len(assets_data), batch_size):
                batch = assets_data[i:i + batch_size]
                
                for asset_data in batch:
                    try:
                        assessment = self.assess_asset(asset_data)
                        self._update_score(assessment)
                        
                        stats["processed"] += 1
                        stats["updated"] += 1
                        stats[f"tier_{assessment.liquidity_tier.lower()}"] += 1
                        
                        if assessment.liquidity_flag:
                            stats["liquidity_flagged"] += 1
                        if assessment.data_quality_flag:
                            stats["quality_flagged"] += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to assess {asset_data.get('asset_id')}: {e}")
                        stats["errors"] += 1
                
                logger.debug(f"Processed batch {i // batch_size + 1}")
            
            logger.info(f"Institutional Guard complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Institutional Guard failed: {e}")
            stats["errors"] += 1
            return stats
    
    def assess_asset(self, asset_data: Dict[str, Any]) -> InstitutionalAssessment:
        """
        Assess a single asset for institutional quality.
        
        Args:
            asset_data: Dict containing score and gating data
            
        Returns:
            InstitutionalAssessment with calculated values
        """
        asset_id = asset_data.get("asset_id", "UNKNOWN")
        score_total = asset_data.get("score_total") or 0.0
        
        # Extract gating metrics
        adv_usd = asset_data.get("liquidity") or asset_data.get("adv_usd") or 0.0
        coverage = asset_data.get("coverage") or 0.0
        stale_ratio = asset_data.get("stale_ratio") or 0.0
        zero_volume_ratio = asset_data.get("zero_volume_ratio") or 0.0
        market_cap = asset_data.get("market_cap")
        
        # Calculate days since last bar
        last_bar_date = asset_data.get("last_bar_date")
        stale_days = self._calculate_stale_days(last_bar_date)
        
        # Initialize tracking
        penalties_applied = []
        caps_applied = []
        current_score = score_total
        
        # ─────────────────────────────────────────────────────────────────────
        # 1. LIQUIDITY ASSESSMENT
        # ─────────────────────────────────────────────────────────────────────
        
        liquidity_tier, liquidity_penalty, liquidity_cap = self._assess_liquidity(adv_usd)
        liquidity_flag = liquidity_tier in ("C", "D")
        
        if liquidity_penalty > 0:
            penalties_applied.append(
                f"Liquidity Tier {liquidity_tier}: -{liquidity_penalty:.0f}pts (ADV=${adv_usd:,.0f})"
            )
            current_score -= liquidity_penalty
        
        if liquidity_cap < 100:
            caps_applied.append(f"Tier {liquidity_tier} cap: max {liquidity_cap:.0f}")
            current_score = min(current_score, liquidity_cap)
        
        # ─────────────────────────────────────────────────────────────────────
        # 2. DATA QUALITY ASSESSMENT
        # ─────────────────────────────────────────────────────────────────────
        
        data_quality_score = self._calculate_data_quality_score(
            coverage=coverage,
            stale_ratio=stale_ratio,
            zero_volume_ratio=zero_volume_ratio,
            stale_days=stale_days
        )
        
        data_quality_flag = False
        stale_price_flag = False
        
        # Low coverage penalty
        if coverage < self._thresholds.MIN_COVERAGE:
            penalty = self._thresholds.LOW_COVERAGE_PENALTY
            penalties_applied.append(f"Low coverage ({coverage:.0%}): -{penalty:.0f}pts")
            current_score -= penalty
            current_score = min(current_score, self._thresholds.LOW_COVERAGE_CAP)
            caps_applied.append(f"Low coverage cap: max {self._thresholds.LOW_COVERAGE_CAP:.0f}")
            data_quality_flag = True
        
        # Stale price penalty
        if stale_days > self._thresholds.MAX_STALE_DAYS or stale_ratio > self._thresholds.MAX_STALE_RATIO:
            penalty = self._thresholds.STALE_PRICE_PENALTY
            penalties_applied.append(f"Stale prices (stale_days={stale_days}, ratio={stale_ratio:.1%}): -{penalty:.0f}pts")
            current_score -= penalty
            current_score = min(current_score, self._thresholds.STALE_PRICE_CAP)
            caps_applied.append(f"Stale price cap: max {self._thresholds.STALE_PRICE_CAP:.0f}")
            stale_price_flag = True
            data_quality_flag = True
        
        # Zero volume penalty
        if zero_volume_ratio > self._thresholds.MAX_ZERO_VOLUME_RATIO:
            penalty = self._thresholds.ZERO_VOLUME_PENALTY
            penalties_applied.append(f"High zero-volume days ({zero_volume_ratio:.1%}): -{penalty:.0f}pts")
            current_score -= penalty
            data_quality_flag = True
        
        # ─────────────────────────────────────────────────────────────────────
        # 3. FINAL SCORE & HORIZON
        # ─────────────────────────────────────────────────────────────────────
        
        # Clamp to 0-100
        score_institutional = max(0.0, min(100.0, current_score))
        
        # Determine recommended horizon
        min_horizon = self._determine_horizon(
            liquidity_tier=liquidity_tier,
            data_quality_flag=data_quality_flag
        )
        
        # Build explanation
        explanation = self._build_explanation(
            score_total=score_total,
            score_institutional=score_institutional,
            liquidity_tier=liquidity_tier,
            penalties_applied=penalties_applied,
            caps_applied=caps_applied
        )
        
        return InstitutionalAssessment(
            asset_id=asset_id,
            score_total=score_total,
            score_institutional=score_institutional,
            liquidity_tier=liquidity_tier,
            liquidity_penalty=liquidity_penalty,
            liquidity_flag=liquidity_flag,
            adv_usd=adv_usd,
            market_cap=market_cap,
            data_quality_score=data_quality_score,
            data_quality_flag=data_quality_flag,
            stale_price_flag=stale_price_flag,
            coverage=coverage,
            stale_ratio=stale_ratio,
            zero_volume_ratio=zero_volume_ratio,
            min_recommended_horizon_years=min_horizon,
            explanation=explanation,
            penalties_applied=penalties_applied,
            caps_applied=caps_applied
        )
    
    def _assess_liquidity(self, adv_usd: float) -> Tuple[str, float, float]:
        """
        Assess liquidity tier, penalty, and cap.
        
        Returns:
            Tuple of (tier, penalty, cap)
        """
        t = self._thresholds
        
        if adv_usd >= t.TIER_A_ADV_MIN:
            return "A", t.TIER_A_PENALTY, t.TIER_A_CAP
        elif adv_usd >= t.TIER_B_ADV_MIN:
            return "B", t.TIER_B_PENALTY, t.TIER_B_CAP
        elif adv_usd >= t.TIER_C_ADV_MIN:
            return "C", t.TIER_C_PENALTY, t.TIER_C_CAP
        else:
            return "D", t.TIER_D_PENALTY, t.TIER_D_CAP
    
    def _calculate_data_quality_score(
        self,
        coverage: float,
        stale_ratio: float,
        zero_volume_ratio: float,
        stale_days: int
    ) -> float:
        """
        Calculate data quality score (0-100).
        
        Higher = better quality data.
        """
        score = 100.0
        t = self._thresholds
        
        # Coverage impact (40% weight)
        if coverage < t.MIN_COVERAGE:
            coverage_penalty = ((t.MIN_COVERAGE - coverage) / t.MIN_COVERAGE) * 40
            score -= coverage_penalty
        
        # Stale ratio impact (25% weight)
        if stale_ratio > 0.05:
            stale_penalty = min(25.0, stale_ratio * 100)
            score -= stale_penalty
        
        # Zero volume impact (20% weight)
        if zero_volume_ratio > 0.02:
            zero_vol_penalty = min(20.0, zero_volume_ratio * 100)
            score -= zero_vol_penalty
        
        # Stale days impact (15% weight)
        if stale_days > 3:
            days_penalty = min(15.0, (stale_days - 3) * 3)
            score -= days_penalty
        
        return max(0.0, min(100.0, score))
    
    def _calculate_stale_days(self, last_bar_date: Optional[str]) -> int:
        """Calculate days since last price bar."""
        if not last_bar_date:
            return 999  # Unknown = very stale
        
        try:
            from datetime import datetime
            last_date = datetime.strptime(last_bar_date[:10], "%Y-%m-%d").date()
            today = datetime.now().date()
            return (today - last_date).days
        except Exception:
            return 999
    
    def _determine_horizon(
        self,
        liquidity_tier: str,
        data_quality_flag: bool
    ) -> int:
        """
        Determine minimum recommended investment horizon (years).
        """
        t = self._thresholds
        
        base_horizons = {
            "A": t.TIER_A_HORIZON,
            "B": t.TIER_B_HORIZON,
            "C": t.TIER_C_HORIZON,
            "D": t.TIER_D_HORIZON
        }
        
        horizon = base_horizons.get(liquidity_tier, t.TIER_D_HORIZON)
        
        # Reduce horizon if data quality issues
        if data_quality_flag and horizon > 3:
            horizon = min(horizon, 5)
        
        return horizon
    
    def _build_explanation(
        self,
        score_total: float,
        score_institutional: float,
        liquidity_tier: str,
        penalties_applied: List[str],
        caps_applied: List[str]
    ) -> str:
        """Build human-readable explanation."""
        parts = []
        
        diff = score_total - score_institutional
        if diff > 0:
            parts.append(f"Score adjusted from {score_total:.0f} to {score_institutional:.0f} (-{diff:.0f}pts)")
        else:
            parts.append(f"Score: {score_institutional:.0f} (no adjustment needed)")
        
        parts.append(f"Liquidity Tier: {liquidity_tier}")
        
        if penalties_applied:
            parts.append("Penalties: " + "; ".join(penalties_applied))
        
        if caps_applied:
            parts.append("Caps: " + "; ".join(caps_applied))
        
        return " | ".join(parts)
    
    def _ensure_columns(self):
        """Ensure institutional columns exist in scores_latest."""
        migration_path = Path(__file__).parent.parent / "storage" / "migrations" / "add_institutional_guard_columns.sql"
        
        with self._store._get_connection() as conn:
            # Check if score_institutional column exists
            columns = conn.execute("PRAGMA table_info(scores_latest)").fetchall()
            column_names = [c["name"] for c in columns]
            
            if "score_institutional" not in column_names:
                logger.info("Applying institutional guard migration...")
                
                if migration_path.exists():
                    with open(migration_path, "r") as f:
                        # Execute each statement separately to handle "column already exists" errors
                        for statement in f.read().split(";"):
                            statement = statement.strip()
                            if statement and not statement.startswith("--"):
                                try:
                                    conn.execute(statement)
                                except sqlite3.OperationalError as e:
                                    if "duplicate column" not in str(e).lower():
                                        logger.warning(f"Migration statement warning: {e}")
                    logger.info("Migration applied successfully")
                else:
                    logger.warning(f"Migration file not found: {migration_path}")
    
    def _get_scored_assets_with_gating(self) -> List[Dict[str, Any]]:
        """Get all scored assets with their gating information."""
        with self._store._get_connection() as conn:
            query = """
                SELECT 
                    s.asset_id,
                    s.score_total,
                    s.score_value,
                    s.score_momentum,
                    s.score_safety,
                    s.confidence,
                    g.coverage,
                    g.liquidity,
                    g.stale_ratio,
                    g.last_bar_date,
                    g.data_confidence
                FROM scores_latest s
                LEFT JOIN gating_status g ON s.asset_id = g.asset_id
                WHERE s.market_scope = ?
                  AND s.score_total IS NOT NULL
            """
            rows = conn.execute(query, (self._market_scope,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def _update_score(self, assessment: InstitutionalAssessment):
        """Update scores_latest with institutional assessment."""
        with self._store._get_connection() as conn:
            data = assessment.to_db_dict()
            
            # Build UPDATE query dynamically
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [assessment.asset_id, self._market_scope]
            
            query = f"""
                UPDATE scores_latest
                SET {set_clause}, updated_at = datetime('now')
                WHERE asset_id = ? AND market_scope = ?
            """
            
            conn.execute(query, values)


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def run_institutional_guard(
    market_scope: MarketScope = "US_EU",
    store: Optional[SQLiteStore] = None
) -> Dict[str, int]:
    """
    Run the institutional guard for a market scope.
    
    Args:
        market_scope: Market scope to process
        store: Optional SQLite store
        
    Returns:
        Processing stats
    """
    guard = InstitutionalGuard(store=store, market_scope=market_scope)
    return guard.run()


def assess_single_asset(
    asset_id: str,
    store: Optional[SQLiteStore] = None,
    market_scope: MarketScope = "US_EU"
) -> Optional[InstitutionalAssessment]:
    """
    Assess a single asset for institutional quality.
    
    Args:
        asset_id: Asset to assess
        store: Optional SQLite store
        market_scope: Market scope
        
    Returns:
        InstitutionalAssessment or None
    """
    store = store or SQLiteStore()
    guard = InstitutionalGuard(store=store, market_scope=market_scope)
    
    # Get asset data
    with store._get_connection() as conn:
        query = """
            SELECT 
                s.asset_id,
                s.score_total,
                g.coverage,
                g.liquidity,
                g.stale_ratio,
                g.last_bar_date
            FROM scores_latest s
            LEFT JOIN gating_status g ON s.asset_id = g.asset_id
            WHERE s.asset_id = ?
        """
        row = conn.execute(query, (asset_id,)).fetchone()
        
        if not row:
            return None
        
        return guard.assess_asset(dict(row))


# Import sqlite3 for exception handling
import sqlite3
from pathlib import Path
