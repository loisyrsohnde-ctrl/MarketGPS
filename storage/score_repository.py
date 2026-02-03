"""
Score Repository - Manages score, rotation state, calibration data, and job runs.
"""
import json
import uuid
from typing import Optional, List, Dict, Tuple

from core.models import Score, Asset, AssetType, RotationState, GatingStatus
from storage.base_repository import BaseRepository, MarketScope, VALID_SCOPES
from core.config import get_logger

logger = get_logger(__name__)


class ScoreRepository(BaseRepository):
    """Repository for score operations."""

    def upsert_score(self, score: Score, market_scope: MarketScope = "US_EU"):
        """Insert or update score with scope."""
        breakdown_json = score.breakdown.to_json() if score.breakdown else None

        # Africa-specific scores
        score_fx_risk = getattr(score, 'score_fx_risk', None)
        score_liquidity_risk = getattr(score, 'score_liquidity_risk', None)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO scores_latest (asset_id, market_scope, score_total, score_value, score_momentum,
                                          score_safety, score_fx_risk, score_liquidity_risk,
                                          confidence, state_label, rsi, zscore,
                                          vol_annual, max_drawdown, sma200, last_price,
                                          fundamentals_available, json_breakdown, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(asset_id) DO UPDATE SET
                    market_scope = excluded.market_scope,
                    score_total = excluded.score_total,
                    score_value = excluded.score_value,
                    score_momentum = excluded.score_momentum,
                    score_safety = excluded.score_safety,
                    score_fx_risk = excluded.score_fx_risk,
                    score_liquidity_risk = excluded.score_liquidity_risk,
                    confidence = excluded.confidence,
                    state_label = excluded.state_label,
                    rsi = excluded.rsi,
                    zscore = excluded.zscore,
                    vol_annual = excluded.vol_annual,
                    max_drawdown = excluded.max_drawdown,
                    sma200 = excluded.sma200,
                    last_price = excluded.last_price,
                    fundamentals_available = excluded.fundamentals_available,
                    json_breakdown = excluded.json_breakdown,
                    updated_at = datetime('now')
            """, (
                score.asset_id, market_scope, score.score_total, score.score_value,
                score.score_momentum, score.score_safety, score_fx_risk, score_liquidity_risk,
                score.confidence, score.state_label.value, score.rsi, score.zscore,
                score.vol_annual, score.max_drawdown, score.sma200, score.last_price,
                int(score.fundamentals_available), breakdown_json
            ))

    def get_score(self, asset_id: str) -> Optional[Score]:
        """Get score for an asset."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM scores_latest WHERE asset_id = ?", (asset_id,)
            ).fetchone()
            if row:
                return Score.from_row(dict(row))
        return None

    def get_latest_score(self, ticker: str, market_scope: str = "US_EU") -> Optional[Dict]:
        """Get latest score data for a ticker, including price."""
        with self._get_connection() as conn:
            # First try exact match with ticker
            row = conn.execute("""
                SELECT s.*, u.currency, u.name
                FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                WHERE u.symbol = ? AND u.market_scope = ?
                LIMIT 1
            """, (ticker.upper(), market_scope)).fetchone()

            if row:
                return dict(row)

            # Try with asset_id pattern
            row = conn.execute("""
                SELECT s.*, u.currency, u.name
                FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                WHERE s.asset_id LIKE ? AND u.market_scope = ?
                LIMIT 1
            """, (f"{ticker.upper()}.%", market_scope)).fetchone()

            if row:
                return dict(row)

        return None

    def get_asset_by_ticker(self, ticker: str) -> Optional[Dict]:
        """Get asset info by ticker symbol."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM universe
                WHERE symbol = ? OR asset_id LIKE ?
                LIMIT 1
            """, (ticker.upper(), f"{ticker.upper()}.%")).fetchone()

            if row:
                return dict(row)
        return None

    def get_top_scores(
        self,
        limit: int = 50,
        asset_type: Optional[AssetType] = None,
        market_scope: Optional[MarketScope] = None
    ) -> List[Tuple[Asset, Score]]:
        """Get top N assets by score within a scope."""
        conditions = ["s.score_total IS NOT NULL", "u.active = 1"]
        params = []

        if asset_type:
            conditions.append("u.asset_type = ?")
            params.append(asset_type.value)

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        sql = f"""
            SELECT u.*, s.*
            FROM scores_latest s
            JOIN universe u ON s.asset_id = u.asset_id
            WHERE {" AND ".join(conditions)}
            ORDER BY s.score_total DESC, s.confidence DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, params + [limit]).fetchall()
            results = []
            for row in rows:
                row_dict = dict(row)
                asset = Asset.from_row(row_dict)
                score = Score.from_row(row_dict)
                results.append((asset, score))
            return results

    # ═══════════════════════════════════════════════════════════════════════════
    # ROTATION STATE (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def upsert_rotation_state(self, state: RotationState, market_scope: MarketScope = "US_EU"):
        """Insert or update rotation state with scope."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO rotation_state (asset_id, market_scope, last_refresh_at, priority_level,
                                           in_top50, cooldown_until, last_error,
                                           refresh_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(asset_id) DO UPDATE SET
                    market_scope = excluded.market_scope,
                    last_refresh_at = excluded.last_refresh_at,
                    priority_level = excluded.priority_level,
                    in_top50 = excluded.in_top50,
                    cooldown_until = excluded.cooldown_until,
                    last_error = excluded.last_error,
                    refresh_count = rotation_state.refresh_count + 1,
                    updated_at = datetime('now')
            """, (
                state.asset_id, market_scope, state.last_refresh_at, state.priority_level,
                int(state.in_top50), state.cooldown_until, state.last_error,
                state.refresh_count
            ))

    def get_priority_assets(self, limit: int = 50, market_scope: MarketScope = "US_EU") -> List[str]:
        """Get assets by priority for next refresh within a scope."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT u.asset_id FROM universe u
                LEFT JOIN rotation_state r ON u.asset_id = r.asset_id
                WHERE u.active = 1 AND u.market_scope = ?
                ORDER BY
                    COALESCE(r.priority_level, 2) ASC,
                    r.last_refresh_at ASC
                LIMIT ?
            """, (market_scope, limit)).fetchall()
            return [row["asset_id"] for row in rows]

    def set_priority_level(self, asset_ids: List[str], priority: int = 1, market_scope: MarketScope = "US_EU"):
        """Set priority level for multiple assets within a scope."""
        with self._get_connection() as conn:
            for asset_id in asset_ids:
                conn.execute("""
                    INSERT INTO rotation_state (asset_id, market_scope, priority_level, updated_at)
                    VALUES (?, ?, ?, datetime('now'))
                    ON CONFLICT(asset_id) DO UPDATE SET
                        market_scope = ?,
                        priority_level = ?,
                        updated_at = datetime('now')
                """, (asset_id, market_scope, priority, market_scope, priority))

    # ═══════════════════════════════════════════════════════════════════════════
    # CALIBRATION PARAMS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_calibration_params(self, market_scope: MarketScope = "US_EU") -> Dict:
        """Get scoring calibration parameters for a scope."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM calibration_params WHERE market_scope = ?", (
                    market_scope,)
            ).fetchone()
            if row:
                return dict(row)
            # Return defaults
            return {
                "market_scope": market_scope,
                "weight_momentum": 0.40,
                "weight_safety": 0.30,
                "weight_value": 0.30,
                "weight_fx_risk": 0.0,
                "weight_liquidity_risk": 0.0,
                "rsi_optimal_low": 40.0,
                "rsi_optimal_high": 70.0,
                "vol_target_max": 30.0,
                "drawdown_target_max": 20.0,
                "min_liquidity_usd": 1000000
            }

    def update_calibration_params(self, market_scope: MarketScope, params: Dict):
        """Update calibration parameters for a scope."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO calibration_params (market_scope, weight_momentum, weight_safety,
                                               weight_value, weight_fx_risk, weight_liquidity_risk,
                                               rsi_optimal_low, rsi_optimal_high, vol_target_max,
                                               drawdown_target_max, min_liquidity_usd, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(market_scope) DO UPDATE SET
                    weight_momentum = excluded.weight_momentum,
                    weight_safety = excluded.weight_safety,
                    weight_value = excluded.weight_value,
                    weight_fx_risk = excluded.weight_fx_risk,
                    weight_liquidity_risk = excluded.weight_liquidity_risk,
                    rsi_optimal_low = excluded.rsi_optimal_low,
                    rsi_optimal_high = excluded.rsi_optimal_high,
                    vol_target_max = excluded.vol_target_max,
                    drawdown_target_max = excluded.drawdown_target_max,
                    min_liquidity_usd = excluded.min_liquidity_usd,
                    updated_at = datetime('now')
            """, (
                market_scope, params.get('weight_momentum', 0.40),
                params.get('weight_safety', 0.30), params.get(
                    'weight_value', 0.30),
                params.get('weight_fx_risk', 0.0), params.get(
                    'weight_liquidity_risk', 0.0),
                params.get('rsi_optimal_low', 40.0), params.get(
                    'rsi_optimal_high', 70.0),
                params.get('vol_target_max', 30.0), params.get(
                    'drawdown_target_max', 20.0),
                params.get('min_liquidity_usd', 1000000)
            ))

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHLIST (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def add_watchlist(
        self,
        ticker: str,
        user_id: str = "default",
        notes: str = None,
        market_scope: MarketScope = "US_EU"
    ) -> bool:
        """Add ticker to watchlist."""
        try:
            with self._get_connection() as conn:
                # First, get asset_id from ticker/symbol
                asset_row = conn.execute("""
                    SELECT asset_id, market_code
                    FROM universe
                    WHERE symbol = ? AND market_scope = ?
                    LIMIT 1
                """, (ticker, market_scope)).fetchone()

                if not asset_row:
                    logger.warning(
                        f"Asset not found for ticker {ticker} in scope {market_scope}")
                    return False

                asset_id = asset_row["asset_id"]
                market_code = asset_row["market_code"] if asset_row["market_code"] else "US"

                # Insert with asset_id
                conn.execute("""
                    INSERT INTO watchlist (asset_id, ticker, user_id, market_scope, market_code, notes, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(asset_id, user_id) DO UPDATE SET
                        notes = excluded.notes,
                        added_at = datetime('now'),
                        ticker = excluded.ticker
                """, (asset_id, ticker, user_id, market_scope, market_code, notes))
                return True
        except Exception as e:
            logger.error(f"Failed to add to watchlist: {e}")
            return False

    def remove_watchlist(self, ticker: str, user_id: str = "default") -> bool:
        """Remove ticker from watchlist."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "DELETE FROM watchlist WHERE ticker = ? AND user_id = ?",
                    (ticker, user_id)
                )
            return True
        except Exception as e:
            logger.error(f"Failed to remove from watchlist: {e}")
            return False

    def list_watchlist(
        self,
        user_id: str = "default",
        market_scope: Optional[MarketScope] = None
    ) -> List[Dict]:
        """Get user's watchlist with asset and score info."""
        conditions = ["w.user_id = ?"]
        params = [user_id]

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("w.market_scope = ?")
            params.append(market_scope)

        sql = f"""
            SELECT w.ticker, w.notes, w.added_at, w.market_scope,
                   u.symbol, u.name, u.asset_type, u.asset_id,
                   s.score_total, s.confidence, s.last_price,
                   s.score_momentum, s.score_safety, s.score_value,
                   s.rsi, s.vol_annual, s.max_drawdown
            FROM watchlist w
            JOIN universe u ON w.asset_id = u.asset_id
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id AND s.market_scope = w.market_scope
            WHERE {' AND '.join(conditions)}
            ORDER BY w.added_at DESC
        """
        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def is_in_watchlist(self, ticker: str, user_id: str = "default") -> bool:
        """Check if ticker is in watchlist."""
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT 1 FROM watchlist WHERE ticker = ? AND user_id = ?",
                (ticker, user_id)
            ).fetchone()
            return result is not None

    def get_watchlist_tickers(self, user_id: str = "default") -> List[str]:
        """Get list of watchlist ticker symbols for user."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at DESC",
                (user_id,)
            ).fetchall()
            return [row["ticker"] for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # PRODUCTION PIPELINE: Job Runs & Atomic Publish (NEW v13)
    # ═══════════════════════════════════════════════════════════════════════════

    def create_job_run(
        self,
        market_scope: MarketScope,
        job_type: str,
        mode: str = "daily_full",
        created_by: str = "scheduler"
    ) -> str:
        """
        Create a new job run and return its run_id.

        Args:
            market_scope: US_EU or AFRICA
            job_type: gating, rotation, scoring, universe
            mode: daily_full, hourly_overlay, on_demand
            created_by: scheduler, manual, api

        Returns:
            run_id (UUID string)
        """
        run_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO job_runs (run_id, market_scope, job_type, mode, status, created_by)
                VALUES (?, ?, ?, ?, 'running', ?)
            """, (run_id, market_scope, job_type, mode, created_by))

        logger.info(
            f"[{market_scope}] Created job run {run_id[:8]}... ({job_type}/{mode})")
        return run_id

    def update_job_run_status(
        self,
        run_id: str,
        status: str,
        assets_processed: int = 0,
        assets_success: int = 0,
        assets_failed: int = 0,
        duration_seconds: float = None,
        stats: Dict = None,
        error: str = None
    ):
        """Update job run status and metrics."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE job_runs SET
                    status = ?,
                    assets_processed = ?,
                    assets_success = ?,
                    assets_failed = ?,
                    duration_seconds = ?,
                    stats_json = ?,
                    error = ?,
                    ended_at = CASE WHEN ? IN ('success', 'failed', 'cancelled')
                               THEN datetime('now') ELSE ended_at END
                WHERE run_id = ?
            """, (
                status, assets_processed, assets_success, assets_failed,
                duration_seconds, json.dumps(stats) if stats else None, error,
                status, run_id
            ))

    def insert_staging_score(self, run_id: str, score: Score, market_scope: MarketScope = "US_EU"):
        """
        Insert a score into staging table (not yet published).

        Args:
            run_id: Job run ID
            score: Score object to stage
            market_scope: US_EU or AFRICA
        """
        breakdown_json = score.breakdown.to_json() if score.breakdown else None
        score_fx_risk = getattr(score, 'score_fx_risk', None)
        score_liquidity_risk = getattr(score, 'score_liquidity_risk', None)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO scores_staging
                    (run_id, asset_id, market_scope, score_total, score_value, score_momentum,
                     score_safety, score_fx_risk, score_liquidity_risk, confidence, state_label,
                     rsi, zscore, vol_annual, max_drawdown, sma200, last_price,
                     fundamentals_available, json_breakdown, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                run_id, score.asset_id, market_scope, score.score_total, score.score_value,
                score.score_momentum, score.score_safety, score_fx_risk, score_liquidity_risk,
                score.confidence, score.state_label.value, score.rsi, score.zscore,
                score.vol_annual, score.max_drawdown, score.sma200, score.last_price,
                int(score.fundamentals_available), breakdown_json
            ))

    def insert_staging_gating(self, run_id: str, gating: GatingStatus, market_scope: MarketScope = "US_EU"):
        """
        Insert a gating status into staging table (not yet published).

        Args:
            run_id: Job run ID
            gating: GatingStatus object to stage
            market_scope: US_EU or AFRICA
        """
        fx_risk = getattr(gating, 'fx_risk', 0.0)
        liquidity_risk = getattr(gating, 'liquidity_risk', 0.0)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO gating_status_staging
                    (run_id, asset_id, market_scope, coverage, liquidity, price_min,
                     stale_ratio, eligible, reason, data_confidence, last_bar_date,
                     data_available, fx_risk, liquidity_risk, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                run_id, gating.asset_id, market_scope, gating.coverage, gating.liquidity,
                gating.price_min, gating.stale_ratio, int(
                    gating.eligible), gating.reason,
                gating.data_confidence, gating.last_bar_date, int(
                    getattr(gating, 'data_available', 0)),
                fx_risk, liquidity_risk
            ))

    def publish_run(
        self,
        run_id: str,
        market_scope: MarketScope,
        publish_scores: bool = True,
        publish_gating: bool = True
    ) -> Dict[str, int]:
        """
        Atomically publish staging data to production tables.

        This method:
        1. Begins a transaction
        2. Replaces scores_latest for this scope with scores_staging data
        3. Replaces gating_status for this scope with gating_status_staging data
        4. Updates job_runs status to 'success'
        5. Cleans up staging tables
        6. Commits transaction

        Args:
            run_id: Job run ID to publish
            market_scope: US_EU or AFRICA
            publish_scores: Whether to publish scores
            publish_gating: Whether to publish gating data

        Returns:
            Dict with counts: scores_published, gating_published
        """
        results = {"scores_published": 0, "gating_published": 0}

        with self._get_connection() as conn:
            try:
                # Count staged records
                if publish_scores:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM scores_staging WHERE run_id = ?", (run_id,)
                    ).fetchone()[0]
                    results["scores_published"] = count

                if publish_gating:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM gating_status_staging WHERE run_id = ?", (run_id,)
                    ).fetchone()[0]
                    results["gating_published"] = count

                # Publish scores: DELETE existing for this scope, then INSERT from staging
                if publish_scores and results["scores_published"] > 0:
                    # Delete existing scores for assets in staging
                    conn.execute("""
                        DELETE FROM scores_latest
                        WHERE asset_id IN (
                            SELECT asset_id FROM scores_staging WHERE run_id = ?
                        )
                    """, (run_id,))

                    # Insert from staging
                    conn.execute("""
                        INSERT INTO scores_latest
                            (asset_id, market_scope, score_total, score_value, score_momentum,
                             score_safety, score_fx_risk, score_liquidity_risk, confidence,
                             state_label, rsi, zscore, vol_annual, max_drawdown, sma200,
                             last_price, fundamentals_available, json_breakdown, updated_at)
                        SELECT
                            asset_id, market_scope, score_total, score_value, score_momentum,
                            score_safety, score_fx_risk, score_liquidity_risk, confidence,
                            state_label, rsi, zscore, vol_annual, max_drawdown, sma200,
                            last_price, fundamentals_available, json_breakdown, updated_at
                        FROM scores_staging WHERE run_id = ?
                    """, (run_id,))

                # Publish gating: same approach
                if publish_gating and results["gating_published"] > 0:
                    conn.execute("""
                        DELETE FROM gating_status
                        WHERE asset_id IN (
                            SELECT asset_id FROM gating_status_staging WHERE run_id = ?
                        )
                    """, (run_id,))

                    conn.execute("""
                        INSERT INTO gating_status
                            (asset_id, market_scope, coverage, liquidity, price_min,
                             stale_ratio, eligible, reason, data_confidence, last_bar_date,
                             data_available, fx_risk, liquidity_risk, updated_at)
                        SELECT
                            asset_id, market_scope, coverage, liquidity, price_min,
                            stale_ratio, eligible, reason, data_confidence, last_bar_date,
                            data_available, fx_risk, liquidity_risk, updated_at
                        FROM gating_status_staging WHERE run_id = ?
                    """, (run_id,))

                # Update job_runs status
                conn.execute("""
                    UPDATE job_runs SET
                        status = 'success',
                        ended_at = datetime('now'),
                        stats_json = ?
                    WHERE run_id = ?
                """, (json.dumps(results), run_id))

                # Clean up staging tables for this run
                conn.execute(
                    "DELETE FROM scores_staging WHERE run_id = ?", (run_id,))
                conn.execute(
                    "DELETE FROM gating_status_staging WHERE run_id = ?", (run_id,))

                logger.info(
                    f"[{market_scope}] Published run {run_id[:8]}...: "
                    f"{results['scores_published']} scores, {results['gating_published']} gating"
                )

                return results

            except Exception as e:
                # Mark job as failed
                conn.execute("""
                    UPDATE job_runs SET status = 'failed', error = ?, ended_at = datetime('now')
                    WHERE run_id = ?
                """, (str(e), run_id))
                logger.error(f"Publish failed for run {run_id}: {e}")
                raise

    def rollback_run(self, run_id: str):
        """
        Rollback a job run by clearing its staging data.

        Args:
            run_id: Job run ID to rollback
        """
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM scores_staging WHERE run_id = ?", (run_id,))
            conn.execute(
                "DELETE FROM gating_status_staging WHERE run_id = ?", (run_id,))
            conn.execute("""
                UPDATE job_runs SET status = 'cancelled', ended_at = datetime('now')
                WHERE run_id = ?
            """, (run_id,))
        logger.info(f"Rolled back job run {run_id[:8]}...")

    def get_job_run(self, run_id: str) -> Optional[Dict]:
        """Get job run by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM job_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_recent_job_runs(
        self,
        market_scope: Optional[MarketScope] = None,
        job_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent job runs with optional filters."""
        conditions = []
        params = []

        if market_scope:
            conditions.append("market_scope = ?")
            params.append(market_scope)

        if job_type:
            conditions.append("job_type = ?")
            params.append(job_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._get_connection() as conn:
            rows = conn.execute(f"""
                SELECT * FROM job_runs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params + [limit]).fetchall()
            return [dict(row) for row in rows]

    def cleanup_old_staging(self, hours_old: int = 24):
        """Clean up old staging records (for failed runs)."""
        with self._get_connection() as conn:
            # Clean scores_staging
            conn.execute("""
                DELETE FROM scores_staging
                WHERE run_id IN (
                    SELECT run_id FROM job_runs
                    WHERE status IN ('failed', 'cancelled')
                    AND created_at < datetime('now', ? || ' hours')
                )
            """, (f"-{hours_old}",))

            # Clean gating_status_staging
            conn.execute("""
                DELETE FROM gating_status_staging
                WHERE run_id IN (
                    SELECT run_id FROM job_runs
                    WHERE status IN ('failed', 'cancelled')
                    AND created_at < datetime('now', ? || ' hours')
                )
            """, (f"-{hours_old}",))
        logger.info(f"Cleaned up staging records older than {hours_old} hours")
