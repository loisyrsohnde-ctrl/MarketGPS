"""
MarketGPS v11.0 - SQLite Storage (SCOPE-AWARE)
Complete CRUD with SQL pagination, job queue, and Pro quota management.
Supports market scopes: US_EU and AFRICA.
Zero API calls - all data from local DB only.
"""
import sqlite3
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Literal

from core.config import get_config, get_logger
from core.models import (
    Asset, AssetType, GatingStatus, Score, RotationState,
    WatchlistItem, StateLabel, ScoreBreakdown
)

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]
VALID_SCOPES = {"US_EU", "AFRICA"}


class SQLiteStore:
    """SQLite database operations for MarketGPS with full pagination and SCOPE support."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite store."""
        config = get_config()
        self.db_path = db_path or str(config.storage.sqlite_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    _get_conn = _get_connection

    def _init_schema(self):
        """Initialize database schema if tables don't exist."""
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='universe'"
            ).fetchone()
            if result:
                # Check if market_scope column exists
                columns = conn.execute(
                    "PRAGMA table_info(universe)").fetchall()
                column_names = [c["name"] for c in columns]
                if "market_scope" not in column_names:
                    logger.warning(
                        "Schema outdated - run reset_schema() to update")
                # Always ensure auth tables exist
                self._ensure_auth_tables()
                return

        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                with self._get_connection() as conn:
                    conn.executescript(f.read())
            logger.info(f"Schema initialized from {schema_path}")

    def _ensure_auth_tables(self):
        """Ensure authentication tables exist with correct schema (idempotent)."""
        with self._get_connection() as conn:
            # Check if users table exists
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            ).fetchone()

            if not result:
                logger.info("Creating authentication tables...")
                conn.executescript("""
                    -- Users table
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        email_verified INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT (datetime('now')),
                        last_login_at TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    
                    -- User profiles
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        display_name TEXT,
                        avatar_path TEXT,
                        bio TEXT,
                        preferred_scope TEXT DEFAULT 'US_EU',
                        preferred_asset_types TEXT DEFAULT 'EQUITY,ETF',
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    );
                    
                    -- Sessions
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT DEFAULT (datetime('now')),
                        expires_at TEXT,
                        ip_address TEXT,
                        user_agent TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

                    -- User sessions (API-specific)
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        user_id TEXT NOT NULL,
                        session_token TEXT PRIMARY KEY,
                        created_at TEXT DEFAULT (datetime('now')),
                        expires_at TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
                    
                    -- User settings
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY DEFAULT 'default',
                        theme TEXT DEFAULT 'dark',
                        language TEXT DEFAULT 'fr',
                        default_market TEXT DEFAULT 'US',
                        default_scope TEXT DEFAULT 'US_EU',
                        default_top_n INTEGER DEFAULT 30,
                        refresh_interval INTEGER DEFAULT 15,
                        show_tutorial INTEGER DEFAULT 1,
                        notifications_enabled INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    );
                    
                    -- Insert default user settings
                    INSERT OR IGNORE INTO user_settings (user_id) VALUES ('default');
                """)
                logger.info("Authentication tables created successfully")
            else:
                # Ensure user_settings table exists even if users table exists
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY DEFAULT 'default',
                        theme TEXT DEFAULT 'dark',
                        language TEXT DEFAULT 'fr',
                        default_market TEXT DEFAULT 'US',
                        default_scope TEXT DEFAULT 'US_EU',
                        default_top_n INTEGER DEFAULT 30,
                        refresh_interval INTEGER DEFAULT 15,
                        show_tutorial INTEGER DEFAULT 1,
                        notifications_enabled INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    );
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        user_id TEXT NOT NULL,
                        session_token TEXT PRIMARY KEY,
                        created_at TEXT DEFAULT (datetime('now')),
                        expires_at TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
                    INSERT OR IGNORE INTO user_settings (user_id) VALUES ('default');
                """)

            # Ensure subscriptions_state table has correct schema
            self._ensure_subscriptions_table(conn)

    def _ensure_subscriptions_table(self, conn):
        """Ensure subscriptions_state table exists with all required columns."""
        # Check if table exists
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions_state'"
        ).fetchone()

        if not result:
            # Create the table from scratch
            conn.executescript("""
                CREATE TABLE subscriptions_state (
                    user_id TEXT PRIMARY KEY,
                    plan TEXT DEFAULT 'free',
                    status TEXT DEFAULT 'inactive',
                    daily_quota_used INTEGER DEFAULT 0,
                    daily_quota_limit INTEGER DEFAULT 3,
                    markets_access TEXT DEFAULT 'US,EU',
                    scopes_access TEXT DEFAULT 'US_EU',
                    features_json TEXT,
                    started_at TEXT,
                    renews_at TEXT,
                    expires_at TEXT,
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions_state(status);
                CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions_state(plan);
                
                INSERT OR IGNORE INTO subscriptions_state (user_id, plan, status, daily_quota_limit) 
                VALUES ('default', 'free', 'active', 3);
            """)
            logger.info("Created subscriptions_state table")
        else:
            # Table exists - check if it has the 'status' column
            columns = conn.execute(
                "PRAGMA table_info(subscriptions_state)").fetchall()
            column_names = [c["name"] for c in columns]

            # Add missing columns
            if "status" not in column_names:
                conn.execute(
                    "ALTER TABLE subscriptions_state ADD COLUMN status TEXT DEFAULT 'active'")
                logger.info("Added 'status' column to subscriptions_state")

            if "daily_quota_used" not in column_names:
                conn.execute(
                    "ALTER TABLE subscriptions_state ADD COLUMN daily_quota_used INTEGER DEFAULT 0")
                logger.info(
                    "Added 'daily_quota_used' column to subscriptions_state")

            if "daily_quota_limit" not in column_names:
                conn.execute(
                    "ALTER TABLE subscriptions_state ADD COLUMN daily_quota_limit INTEGER DEFAULT 3")
                logger.info(
                    "Added 'daily_quota_limit' column to subscriptions_state")

            if "scopes_access" not in column_names:
                conn.execute(
                    "ALTER TABLE subscriptions_state ADD COLUMN scopes_access TEXT DEFAULT 'US_EU'")
                logger.info(
                    "Added 'scopes_access' column to subscriptions_state")

            if "stripe_customer_id" not in column_names:
                conn.execute(
                    "ALTER TABLE subscriptions_state ADD COLUMN stripe_customer_id TEXT")
                logger.info(
                    "Added 'stripe_customer_id' column to subscriptions_state")

            if "stripe_subscription_id" not in column_names:
                conn.execute(
                    "ALTER TABLE subscriptions_state ADD COLUMN stripe_subscription_id TEXT")
                logger.info(
                    "Added 'stripe_subscription_id' column to subscriptions_state")

            # Ensure default user exists
            conn.execute("""
                INSERT OR IGNORE INTO subscriptions_state (user_id, plan, status, daily_quota_limit) 
                VALUES ('default', 'free', 'active', 3)
            """)

    def ensure_schema(self):
        """Public method to ensure all schema tables exist."""
        self._init_schema()
        self._ensure_auth_tables()
        self._ensure_strategy_tables()

    def _ensure_strategy_tables(self):
        """Ensure strategy tables exist (idempotent)."""
        migration_path = Path(__file__).parent / \
            "migrations" / "add_strategy_tables.sql"
        if not migration_path.exists():
            return

        with self._get_connection() as conn:
            # Check if main table exists
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_templates'"
            ).fetchone()

            if not result:
                logger.info("Creating strategy tables...")
                with open(migration_path, "r") as f:
                    conn.executescript(f.read())
                logger.info("Strategy tables created successfully")

    def reset_schema(self):
        """Force reset the database schema."""
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                with self._get_connection() as conn:
                    conn.executescript(f.read())
            logger.info("Schema reset complete")

    # ═══════════════════════════════════════════════════════════════════════════
    # UNIVERSE - CRUD + PAGINATION (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def upsert_asset(self, asset: Asset, market_scope: MarketScope = "US_EU"):
        """Insert or update an asset with scope."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO universe (asset_id, symbol, name, asset_type, market_scope, market_code,
                                     exchange_code, currency, country, sector, industry, active, tier, 
                                     priority_level, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(asset_id) DO UPDATE SET
                    symbol = excluded.symbol,
                    name = excluded.name,
                    asset_type = excluded.asset_type,
                    market_scope = excluded.market_scope,
                    market_code = excluded.market_code,
                    exchange_code = excluded.exchange_code,
                    currency = excluded.currency,
                    country = excluded.country,
                    sector = excluded.sector,
                    industry = excluded.industry,
                    active = excluded.active,
                    tier = excluded.tier,
                    priority_level = excluded.priority_level,
                    updated_at = datetime('now')
            """, (
                asset.asset_id, asset.symbol, asset.name, asset.asset_type.value,
                market_scope, getattr(asset, 'market_code', 'US'),
                getattr(asset, 'exchange',
                        asset.exchange), asset.currency, asset.country,
                asset.sector, asset.industry, int(asset.active), asset.tier,
                getattr(asset, 'priority_level', 2)
            ))

    def bulk_upsert_assets(self, assets: List[Dict], market_scope: MarketScope = "US_EU"):
        """Bulk insert/update assets from dict list."""
        with self._get_connection() as conn:
            for a in assets:
                conn.execute("""
                    INSERT INTO universe (asset_id, symbol, name, asset_type, market_scope, market_code,
                                         exchange_code, currency, country, sector, industry, active, tier, 
                                         priority_level, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(asset_id) DO UPDATE SET
                        symbol = excluded.symbol,
                        name = excluded.name,
                        asset_type = excluded.asset_type,
                        market_scope = excluded.market_scope,
                        market_code = excluded.market_code,
                        exchange_code = excluded.exchange_code,
                        currency = excluded.currency,
                        country = excluded.country,
                        sector = excluded.sector,
                        industry = excluded.industry,
                        active = excluded.active,
                        tier = excluded.tier,
                        priority_level = excluded.priority_level,
                        updated_at = datetime('now')
                """, (
                    a.get('asset_id'), a.get('symbol'), a.get('name'),
                    a.get('asset_type', 'EQUITY'), market_scope,
                    a.get('market_code', 'US'), a.get('exchange_code', 'US'),
                    a.get('currency', 'USD'), a.get('country', 'US'),
                    a.get('sector'), a.get('industry'),
                    int(a.get('active', 1)), a.get(
                        'tier', 2), a.get('priority_level', 2)
                ))
        logger.info(f"[{market_scope}] Bulk upserted {len(assets)} assets")

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get asset by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM universe WHERE asset_id = ?", (asset_id,)
            ).fetchone()
            if row:
                return Asset.from_row(dict(row))
        return None

    def get_active_assets(
        self,
        asset_type: Optional[AssetType] = None,
        market_scope: Optional[MarketScope] = None
    ) -> List[Asset]:
        """Get all active assets, optionally filtered by type and scope."""
        conditions = ["active = 1"]
        params = []

        if asset_type:
            conditions.append("asset_type = ?")
            params.append(asset_type.value)

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("market_scope = ?")
            params.append(market_scope)

        sql = f"SELECT * FROM universe WHERE {' AND '.join(conditions)}"

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [Asset.from_row(dict(row)) for row in rows]

    def list_assets_paginated(
        self,
        market_scope: Optional[MarketScope] = None,
        asset_type: Optional[str] = None,
        search: Optional[str] = None,
        scored_filter: Optional[str] = None,
        eligible_only: bool = False,
        active_only: bool = True,
        sort_by: str = "score_total",
        sort_desc: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict], int]:
        """
        List assets with SQL pagination - SCOPE-AWARE.
        Returns (rows, total_count)
        """
        offset = (page - 1) * page_size

        conditions = []
        params = []

        if active_only:
            conditions.append("u.active = 1")

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        if asset_type and asset_type != "ALL":
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        if search:
            conditions.append("(u.symbol LIKE ? OR u.name LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern])

        if eligible_only:
            conditions.append("COALESCE(g.eligible, 0) = 1")

        if scored_filter == "scored":
            conditions.append("s.score_total IS NOT NULL")
        elif scored_filter == "unscored":
            conditions.append("s.score_total IS NULL")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        order_map = {
            "score_total": "COALESCE(s.score_total, -999)",
            "symbol": "u.symbol",
            "name": "u.name",
            "updated_at": "COALESCE(s.updated_at, u.updated_at)",
            "confidence": "COALESCE(s.confidence, 0)"
        }
        order_col = order_map.get(sort_by, "COALESCE(s.score_total, -999)")
        order_dir = "DESC" if sort_desc else "ASC"

        count_sql = f"""
            SELECT COUNT(DISTINCT u.asset_id)
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE {where_clause}
        """

        data_sql = f"""
            SELECT 
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_scope, u.market_code,
                u.exchange_code, u.currency, u.active, u.tier, u.priority_level, u.sector, u.industry,
                s.score_total, s.score_value, s.score_momentum, s.score_safety,
                s.score_fx_risk, s.score_liquidity_risk,
                s.confidence, s.last_price, s.rsi, s.vol_annual, s.max_drawdown,
                s.state_label, s.updated_at as score_updated,
                g.eligible, g.data_confidence
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE {where_clause}
            ORDER BY {order_col} {order_dir}, u.symbol ASC
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            total = conn.execute(count_sql, params).fetchone()[0]
            rows = conn.execute(data_sql, params +
                                [page_size, offset]).fetchall()
            return [dict(row) for row in rows], total

    def list_top_n(
        self,
        market_scope: Optional[MarketScope] = None,
        asset_type: Optional[str] = None,
        n: int = 50
    ) -> List[Dict]:
        """Get top N assets by score for a given type and scope."""
        conditions = ["s.score_total IS NOT NULL", "u.active = 1"]
        params = []

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        if asset_type and asset_type != "ALL":
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT 
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_scope, u.market_code,
                u.sector, u.industry,
                s.score_total, s.score_value, s.score_momentum, s.score_safety,
                s.score_fx_risk, s.score_liquidity_risk,
                s.confidence, s.last_price, s.state_label, s.updated_at
            FROM universe u
            INNER JOIN scores_latest s ON u.asset_id = s.asset_id
            WHERE {where_clause}
            ORDER BY s.score_total DESC, s.confidence DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, params + [n]).fetchall()
            return [dict(row) for row in rows]

    def get_asset_detail(self, asset_id: str) -> Optional[Dict]:
        """Get full asset detail with scores and gating info."""
        sql = """
            SELECT 
                u.*,
                s.score_total, s.score_value, s.score_momentum, s.score_safety,
                s.score_fx_risk, s.score_liquidity_risk,
                s.confidence, s.last_price, s.rsi, s.zscore, s.vol_annual, 
                s.max_drawdown, s.sma200, s.state_label, s.fundamentals_available,
                s.json_breakdown, s.updated_at as score_updated,
                g.coverage, g.liquidity, g.eligible, g.data_confidence,
                g.last_bar_date, g.fx_risk, g.liquidity_risk
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE u.asset_id = ?
        """
        with self._get_connection() as conn:
            row = conn.execute(sql, (asset_id,)).fetchone()
            if row:
                return dict(row)
        return None

    def search_assets(
        self,
        query: str,
        market_scope: Optional[MarketScope] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Quick search by symbol or name within a scope."""
        pattern = f"%{query}%"

        conditions = ["u.active = 1", "(u.symbol LIKE ? OR u.name LIKE ?)"]
        params = [pattern, pattern]

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        sql = f"""
            SELECT u.asset_id, u.symbol, u.name, u.asset_type, u.market_scope, u.market_code,
                   s.score_total, s.confidence
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            WHERE {' AND '.join(conditions)}
            ORDER BY 
                CASE WHEN u.symbol LIKE ? THEN 0 ELSE 1 END,
                COALESCE(s.score_total, -999) DESC
            LIMIT ?
        """
        params.append(f"{query}%")
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def count_assets(
        self,
        asset_type: Optional[str] = None,
        market_scope: Optional[MarketScope] = None
    ) -> Dict[str, int]:
        """Count assets by type and scope with scored/unscored breakdown."""
        conditions = ["u.active = 1"]
        params = []

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        if asset_type and asset_type != "ALL":
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        sql = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN s.score_total IS NOT NULL THEN 1 ELSE 0 END) as scored
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            WHERE {' AND '.join(conditions)}
        """

        with self._get_connection() as conn:
            result = conn.execute(sql, params).fetchone()
            return {
                "total": result["total"] or 0,
                "scored": result["scored"] or 0,
                "unscored": (result["total"] or 0) - (result["scored"] or 0)
            }

    def count_by_type(self, market_scope: Optional[MarketScope] = None) -> Dict[str, int]:
        """Count active assets grouped by type within a scope."""
        conditions = ["active = 1"]
        params = []

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("market_scope = ?")
            params.append(market_scope)

        sql = f"""
            SELECT asset_type, COUNT(*) as count
            FROM universe WHERE {' AND '.join(conditions)}
            GROUP BY asset_type
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return {row["asset_type"]: row["count"] for row in rows}

    def count_by_scope(self) -> Dict[str, int]:
        """Count active assets grouped by market scope."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT market_scope, COUNT(*) as count
                FROM universe WHERE active = 1
                GROUP BY market_scope
            """).fetchall()
            return {row["market_scope"]: row["count"] for row in rows}

    # ═══════════════════════════════════════════════════════════════════════════
    # GATING STATUS (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def upsert_gating(self, gating: GatingStatus, market_scope: MarketScope = "US_EU"):
        """Insert or update gating status with scope."""
        fx_risk = getattr(gating, 'fx_risk', 0.0)
        liquidity_risk = getattr(gating, 'liquidity_risk', 0.0)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO gating_status (asset_id, market_scope, coverage, liquidity, price_min,
                                          stale_ratio, eligible, reason, data_confidence,
                                          last_bar_date, fx_risk, liquidity_risk, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(asset_id) DO UPDATE SET
                    market_scope = excluded.market_scope,
                    coverage = excluded.coverage,
                    liquidity = excluded.liquidity,
                    price_min = excluded.price_min,
                    stale_ratio = excluded.stale_ratio,
                    eligible = excluded.eligible,
                    reason = excluded.reason,
                    data_confidence = excluded.data_confidence,
                    last_bar_date = excluded.last_bar_date,
                    fx_risk = excluded.fx_risk,
                    liquidity_risk = excluded.liquidity_risk,
                    updated_at = datetime('now')
            """, (
                gating.asset_id, market_scope, gating.coverage, gating.liquidity, gating.price_min,
                gating.stale_ratio, int(gating.eligible), gating.reason,
                gating.data_confidence, gating.last_bar_date, fx_risk, liquidity_risk
            ))

    def get_gating(self, asset_id: str) -> Optional[GatingStatus]:
        """Get gating status for an asset."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM gating_status WHERE asset_id = ?", (asset_id,)
            ).fetchone()
            if row:
                return GatingStatus.from_row(dict(row))
        return None

    def get_eligible_assets(self, market_scope: MarketScope = "US_EU") -> List[str]:
        """Get list of eligible asset IDs for a scope."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT g.asset_id FROM gating_status g
                JOIN universe u ON g.asset_id = u.asset_id
                WHERE g.eligible = 1 AND g.market_scope = ? AND u.active = 1
            """, (market_scope,)).fetchall()
            return [row["asset_id"] for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORES (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

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
        """Get list of tickers in watchlist."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at DESC",
                (user_id,)
            ).fetchall()
            return [row["ticker"] for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # JOBS QUEUE (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def enqueue_job(
        self,
        job_type: str,
        payload: Dict,
        market_scope: MarketScope = "US_EU",
        priority: int = 2,
        user_id: str = "default"
    ) -> int:
        """Add a job to the queue with scope."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO jobs_queue (job_type, market_scope, payload_json, priority, status, user_id, created_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?, datetime('now'))
            """, (job_type, market_scope, json.dumps(payload), priority, user_id))
            return cursor.lastrowid

    def fetch_next_job_atomic(self, market_scope: Optional[MarketScope] = None) -> Optional[Dict]:
        """Atomically fetch and lock the next pending job."""
        with self._get_connection() as conn:
            conditions = ["status = 'PENDING'"]
            params = []

            if market_scope and market_scope in VALID_SCOPES:
                conditions.append("market_scope = ?")
                params.append(market_scope)

            row = conn.execute(f"""
                SELECT * FROM jobs_queue
                WHERE {' AND '.join(conditions)}
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """, params).fetchone()

            if not row:
                return None

            job_id = row["id"]

            conn.execute("""
                UPDATE jobs_queue 
                SET status = 'RUNNING', started_at = datetime('now')
                WHERE id = ? AND status = 'PENDING'
            """, (job_id,))

            return dict(row)

    def mark_job_done(self, job_id: int):
        """Mark a job as completed."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs_queue 
                SET status = 'DONE', completed_at = datetime('now')
                WHERE id = ?
            """, (job_id,))

    def mark_job_failed(self, job_id: int, error: str):
        """Mark a job as failed."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs_queue 
                SET status = 'FAILED', completed_at = datetime('now'), error_message = ?
                WHERE id = ?
            """, (error, job_id))

    def get_pending_jobs_count(self, market_scope: Optional[MarketScope] = None) -> int:
        """Count pending jobs."""
        with self._get_connection() as conn:
            if market_scope and market_scope in VALID_SCOPES:
                result = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING' AND market_scope = ?",
                    (market_scope,)
                ).fetchone()
            else:
                result = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING'"
                ).fetchone()
            return result[0] if result else 0

    def get_recent_jobs(self, limit: int = 10, market_scope: Optional[MarketScope] = None) -> List[Dict]:
        """Get recent jobs for status display."""
        conditions = []
        params = []

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("market_scope = ?")
            params.append(market_scope)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._get_connection() as conn:
            rows = conn.execute(f"""
                SELECT * FROM jobs_queue
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params + [limit]).fetchall()
            return [dict(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # QUOTA (unchanged)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_today_usage(self, user_id: str = "default") -> Dict:
        """Get today's usage and limits."""
        today = date.today().isoformat()

        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM usage_daily
                WHERE user_id = ? AND date = ?
            """, (user_id, today)).fetchone()

            if row:
                return dict(row)

            limit_row = conn.execute(
                "SELECT value FROM app_settings WHERE key = 'daily_quota_free'"
            ).fetchone()
            default_limit = int(limit_row["value"]) if limit_row else 200

            conn.execute("""
                INSERT INTO usage_daily (user_id, date, calculations_count, calculations_limit)
                VALUES (?, ?, 0, ?)
            """, (user_id, today, default_limit))

            return {
                "user_id": user_id,
                "date": today,
                "calculations_count": 0,
                "calculations_limit": default_limit,
                "tier": "free"
            }

    def can_consume_quota(self, count: int, user_id: str = "default") -> bool:
        """Check if user can consume quota for N calculations."""
        usage = self.get_today_usage(user_id)
        return (usage["calculations_count"] + count) <= usage["calculations_limit"]

    def consume_quota(self, count: int, user_id: str = "default") -> bool:
        """Consume quota for N calculations."""
        if not self.can_consume_quota(count, user_id):
            return False

        today = date.today().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE usage_daily 
                SET calculations_count = calculations_count + ?
                WHERE user_id = ? AND date = ?
            """, (count, user_id, today))

        return True

    def set_user_tier(self, user_id: str, tier: str, limit: int):
        """Set user tier and daily limit."""
        today = date.today().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE usage_daily 
                SET tier = ?, calculations_limit = ?
                WHERE user_id = ? AND date = ?
            """, (tier, limit, user_id, today))

    # ═══════════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get app setting."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """Set app setting."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value, updated_at = datetime('now')
            """, (key, value))

    def is_pro_mode_enabled(self) -> bool:
        """Check if pro mode is enabled."""
        return self.get_setting("pro_mode_enabled", "false") == "true"

    def set_pro_mode(self, enabled: bool):
        """Enable or disable pro mode."""
        self.set_setting("pro_mode_enabled", "true" if enabled else "false")

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self, market_scope: Optional[MarketScope] = None) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        with self._get_connection() as conn:
            stats = {}

            scope_filter = ""
            params = []
            if market_scope and market_scope in VALID_SCOPES:
                scope_filter = " AND market_scope = ?"
                params = [market_scope]
                stats["scope"] = market_scope

            # Universe counts
            stats["universe_total"] = conn.execute(
                f"SELECT COUNT(*) FROM universe WHERE active = 1{scope_filter}", params
            ).fetchone()[0]

            # Scores counts
            if market_scope:
                stats["scores_total"] = conn.execute(
                    "SELECT COUNT(*) FROM scores_latest WHERE score_total IS NOT NULL AND market_scope = ?",
                    (market_scope,)
                ).fetchone()[0]
            else:
                stats["scores_total"] = conn.execute(
                    "SELECT COUNT(*) FROM scores_latest WHERE score_total IS NOT NULL"
                ).fetchone()[0]

            # Watchlist count
            stats["watchlist_count"] = conn.execute(
                "SELECT COUNT(*) FROM watchlist"
            ).fetchone()[0]

            # Pending jobs
            if market_scope:
                stats["jobs_pending"] = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING' AND market_scope = ?",
                    (market_scope,)
                ).fetchone()[0]
            else:
                stats["jobs_pending"] = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING'"
                ).fetchone()[0]

            # Types breakdown
            types = conn.execute(f"""
                SELECT asset_type, COUNT(*) as count
                FROM universe WHERE active = 1{scope_filter}
                GROUP BY asset_type
            """, params).fetchall()
            stats["by_type"] = {row["asset_type"]: row["count"]
                                for row in types}

            # Scope breakdown
            scopes = conn.execute("""
                SELECT market_scope, COUNT(*) as count
                FROM universe WHERE active = 1
                GROUP BY market_scope
            """).fetchall()
            stats["by_scope"] = {row["market_scope"]: row["count"] for row in scopes}

            return stats

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTHENTICATION (NEW v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def create_user(self, email: str, password_hash: str) -> Optional[str]:
        """Create a new user and return user_id."""
        import uuid
        user_id = str(uuid.uuid4())

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (user_id, email, password_hash, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                """, (user_id, email.lower().strip(), password_hash))

                # Create default profile
                conn.execute("""
                    INSERT INTO user_profiles (user_id, display_name, created_at)
                    VALUES (?, ?, datetime('now'))
                """, (user_id, email.split('@')[0]))

                # Create default subscription (free)
                conn.execute("""
                    INSERT INTO subscriptions_state (user_id, plan, status, daily_quota_limit, created_at)
                    VALUES (?, 'free', 'active', 3, datetime('now'))
                """, (user_id,))

                # Create default user settings
                conn.execute("""
                    INSERT INTO user_settings (user_id, created_at)
                    VALUES (?, datetime('now'))
                """, (user_id,))

            logger.info(f"Created user {user_id} for {email}")
            return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"User with email {email} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (email.lower().strip(),)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_last_login(self, user_id: str):
        """Update last login timestamp."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = datetime('now') WHERE user_id = ?",
                (user_id,)
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # USER PROFILES (NEW v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile with subscription info."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT p.*, u.email, s.plan, s.status as subscription_status, 
                       s.daily_quota_used, s.daily_quota_limit
                FROM user_profiles p
                JOIN users u ON p.user_id = u.user_id
                LEFT JOIN subscriptions_state s ON p.user_id = s.user_id
                WHERE p.user_id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def update_user_profile(self, user_id: str, display_name: str = None, avatar_path: str = None, bio: str = None) -> bool:
        """Update user profile."""
        try:
            updates = []
            params = []

            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            if avatar_path is not None:
                updates.append("avatar_path = ?")
                params.append(avatar_path)
            if bio is not None:
                updates.append("bio = ?")
                params.append(bio)

            if not updates:
                return True

            updates.append("updated_at = datetime('now')")
            params.append(user_id)

            with self._get_connection() as conn:
                conn.execute(f"""
                    UPDATE user_profiles SET {', '.join(updates)}
                    WHERE user_id = ?
                """, params)
            return True
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # SUBSCRIPTIONS (NEW v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_subscription(self, user_id: str) -> Dict:
        """Get user subscription info."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM subscriptions_state WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if row:
                return dict(row)

            # Return default free plan
            return {
                "user_id": user_id,
                "plan": "free",
                "status": "active",
                "daily_quota_used": 0,
                "daily_quota_limit": 3
            }

    def set_subscription(self, user_id: str, plan: str, status: str = "active", renews_at: str = None) -> bool:
        """Set or update subscription."""
        try:
            quota_limits = {
                "free": 3,
                "monthly_9_99": 200,
                "yearly_50": 200
            }
            quota = quota_limits.get(plan, 3)
            scopes = "US_EU,AFRICA" if plan != "free" else "US_EU"

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO subscriptions_state (user_id, plan, status, daily_quota_limit, 
                                                    scopes_access, started_at, renews_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'))
                    ON CONFLICT(user_id) DO UPDATE SET
                        plan = excluded.plan,
                        status = excluded.status,
                        daily_quota_limit = excluded.daily_quota_limit,
                        scopes_access = excluded.scopes_access,
                        started_at = COALESCE(subscriptions_state.started_at, datetime('now')),
                        renews_at = excluded.renews_at,
                        updated_at = datetime('now')
                """, (user_id, plan, status, quota, scopes, renews_at))

            logger.info(f"Set subscription for {user_id}: {plan} ({status})")
            return True
        except Exception as e:
            logger.error(f"Failed to set subscription: {e}")
            return False

    def is_pro_user(self, user_id: str) -> bool:
        """Check if user has an active pro subscription."""
        sub = self.get_subscription(user_id)
        return sub.get("status") == "active" and sub.get("plan") in ("monthly_9_99", "yearly_50")

    def can_calculate_score(self, user_id: str) -> bool:
        """Check if user can calculate a score (quota check)."""
        sub = self.get_subscription(user_id)
        return sub.get("daily_quota_used", 0) < sub.get("daily_quota_limit", 3)

    def consume_calculation_quota(self, user_id: str, count: int = 1) -> bool:
        """Consume calculation quota."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE subscriptions_state 
                    SET daily_quota_used = daily_quota_used + ?
                    WHERE user_id = ?
                """, (count, user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to consume quota: {e}")
            return False

    def reset_daily_quotas(self):
        """Reset all daily quotas (call this daily via scheduler)."""
        with self._get_connection() as conn:
            conn.execute("UPDATE subscriptions_state SET daily_quota_used = 0")
        logger.info("Reset all daily quotas")

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
                ORDER BY started_at DESC
                LIMIT ?
            """, params + [limit]).fetchall()
            return [dict(row) for row in rows]

    def cleanup_old_staging(self, hours_old: int = 24):
        """
        Clean up old staging data that was never published.

        Args:
            hours_old: Delete staging data older than this many hours
        """
        with self._get_connection() as conn:
            # Get old run IDs
            old_runs = conn.execute("""
                SELECT run_id FROM job_runs 
                WHERE status = 'running' 
                AND started_at < datetime('now', ?)
            """, (f'-{hours_old} hours',)).fetchall()

            for row in old_runs:
                run_id = row["run_id"]
                conn.execute(
                    "DELETE FROM scores_staging WHERE run_id = ?", (run_id,))
                conn.execute(
                    "DELETE FROM gating_status_staging WHERE run_id = ?", (run_id,))
                conn.execute("""
                    UPDATE job_runs SET status = 'cancelled', 
                    error = 'Timed out - staging never published'
                    WHERE run_id = ?
                """, (run_id,))

            if old_runs:
                logger.info(f"Cleaned up {len(old_runs)} stale job runs")

    # ═══════════════════════════════════════════════════════════════════════════
    # LANDING PAGE METRICS (NEW v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_landing_metrics(self, market_scope: str = "US_EU") -> Dict:
        """Get metrics for landing page display."""
        with self._get_connection() as conn:
            metrics = {}

            # Total assets
            metrics["total_assets"] = conn.execute(
                "SELECT COUNT(*) FROM universe WHERE active = 1 AND market_scope = ?",
                (market_scope,)
            ).fetchone()[0]

            # Scored assets
            metrics["total_scored"] = conn.execute("""
                SELECT COUNT(*) FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                WHERE s.score_total IS NOT NULL AND u.market_scope = ?
            """, (market_scope,)).fetchone()[0]

            # Last refresh
            row = conn.execute("""
                SELECT MAX(updated_at) as last_refresh FROM scores_latest
            """).fetchone()
            metrics["last_refresh"] = row["last_refresh"] if row else None

            # Top example asset (best score)
            row = conn.execute("""
                SELECT u.symbol, u.name, s.score_total, s.score_value, 
                       s.score_momentum, s.score_safety, s.confidence,
                       g.coverage, g.liquidity, g.fx_risk
                FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                LEFT JOIN gating_status g ON s.asset_id = g.asset_id
                WHERE s.score_total IS NOT NULL AND u.market_scope = ?
                ORDER BY s.score_total DESC
                LIMIT 1
            """, (market_scope,)).fetchone()

            if row:
                metrics["top_asset"] = dict(row)
            else:
                metrics["top_asset"] = None

            return metrics

    # ═══════════════════════════════════════════════════════════════════════════
    # UNIVERSE SEARCH (ENHANCED for Explorer v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_universe(
        self,
        market_scope: str = "US_EU",
        market_code: str = None,
        asset_type: str = None,
        query: str = None,
        only_scored: bool = True,
        sort_by: str = "score_total",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        Search universe with filters for Explorer page.
        Returns (results, total_count).
        """
        conditions = ["u.active = 1"]
        params = []

        # Market scope
        if market_scope:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        # Market code (US, EU, ZA, etc.)
        if market_code and market_code not in ("ALL", "Tous"):
            conditions.append("u.market_code = ?")
            params.append(market_code)

        # Asset type
        if asset_type and asset_type not in ("ALL", "Tous"):
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        # Search query
        if query:
            conditions.append("(u.symbol LIKE ? OR u.name LIKE ?)")
            pattern = f"%{query}%"
            params.extend([pattern, pattern])

        # Only scored
        if only_scored:
            conditions.append("s.score_total IS NOT NULL")

        where_clause = " AND ".join(conditions)

        # Count total
        count_sql = f"""
            SELECT COUNT(DISTINCT u.asset_id)
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            WHERE {where_clause}
        """

        # Sort mapping
        sort_map = {
            "score_total": "COALESCE(s.score_total, -999)",
            "symbol": "u.symbol",
            "name": "u.name",
            "confidence": "COALESCE(s.confidence, 0)"
        }
        order_col = sort_map.get(sort_by, "COALESCE(s.score_total, -999)")
        order_dir = "DESC" if sort_desc else "ASC"

        # Data query
        data_sql = f"""
            SELECT 
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_scope, u.market_code,
                u.sector, u.industry,
                s.score_total, s.score_value, s.score_momentum, s.score_safety,
                s.confidence, s.rsi, s.vol_annual, s.max_drawdown,
                g.coverage, g.liquidity, g.fx_risk
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE {where_clause}
            ORDER BY {order_col} {order_dir}, u.symbol ASC
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            total = conn.execute(count_sql, params).fetchone()[0]
            rows = conn.execute(data_sql, params + [limit, offset]).fetchall()
            return [dict(row) for row in rows], total

    def get_top_scored_assets(
        self,
        market_scope: str = "US_EU",
        asset_type: str = None,
        limit: int = 50,
        market_filter: str = "ALL"
    ) -> List[Dict]:
        """Get top N scored assets with optional market and type filters."""
        conditions = ["u.active = 1", "s.score_total IS NOT NULL"]
        params = []

        # Filter by market_scope (US_EU or AFRICA)
        if market_scope:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        # Filter by specific market within scope (US or EU)
        if market_filter and market_filter not in ("ALL", "Tous"):
            if market_filter == "US":
                conditions.append("u.market_code LIKE 'US%'")
            elif market_filter == "EU":
                conditions.append(
                    "u.market_code NOT LIKE 'US%' AND u.market_scope = 'US_EU'")
            elif market_filter == "AFRICA":
                conditions.append("u.market_scope = 'AFRICA'")

        if asset_type and asset_type not in ("ALL", "Tous"):
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        sql = f"""
            SELECT 
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_code,
                s.score_total, s.score_momentum, s.score_safety, s.score_value,
                s.confidence, g.coverage, g.liquidity
            FROM universe u
            INNER JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE {" AND ".join(conditions)}
            ORDER BY s.score_total DESC, s.confidence DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, params + [limit]).fetchall()
            return [dict(row) for row in rows]

    def get_asset_types_for_scope(self, market_scope: str = "US_EU") -> List[str]:
        """Get available asset types for a scope."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT DISTINCT asset_type FROM universe
                WHERE active = 1 AND market_scope = ?
                ORDER BY asset_type
            """, (market_scope,)).fetchall()
            return [row["asset_type"] for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # LONG-TERM SCORING (ADD-ON)
    # ═══════════════════════════════════════════════════════════════════════════

    def ensure_longterm_schema(self) -> bool:
        """
        Ensure long-term scoring columns exist in scores_latest and scores_staging.
        Idempotent - safe to call multiple times.

        Returns:
            True if columns already existed or were added successfully
        """
        try:
            with self._get_connection() as conn:
                # Check if lt_score column exists in scores_latest
                columns = conn.execute(
                    "PRAGMA table_info(scores_latest)").fetchall()
                column_names = [c["name"] for c in columns]

                if "lt_score" not in column_names:
                    logger.info(
                        "Adding long-term scoring columns to scores_latest...")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_score REAL")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_confidence REAL")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_breakdown TEXT")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_updated_at TEXT")

                    # Create index
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_scores_lt_score 
                        ON scores_latest(lt_score DESC) WHERE lt_score IS NOT NULL
                    """)
                    logger.info(
                        "Long-term scoring columns added to scores_latest")

                # Check scores_staging table
                staging_columns = conn.execute(
                    "PRAGMA table_info(scores_staging)").fetchall()
                staging_names = [c["name"] for c in staging_columns]

                if "lt_score" not in staging_names:
                    logger.info(
                        "Adding long-term scoring columns to scores_staging...")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_score REAL")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_confidence REAL")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_breakdown TEXT")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_updated_at TEXT")
                    logger.info(
                        "Long-term scoring columns added to scores_staging")

                return True

        except Exception as e:
            logger.error(f"Failed to ensure longterm schema: {e}")
            return False

    def upsert_longterm_score(
        self,
        asset_id: str,
        lt_score: Optional[float],
        lt_confidence: Optional[float],
        lt_breakdown: Optional[str],
        market_scope: MarketScope = "US_EU"
    ) -> bool:
        """
        Update long-term score for an asset.
        Only updates lt_* columns, does not touch existing score columns.

        Args:
            asset_id: Asset identifier
            lt_score: Long-term score (0-100)
            lt_confidence: Confidence score (0-100)
            lt_breakdown: JSON string with breakdown details
            market_scope: Market scope

        Returns:
            True if update successful
        """
        try:
            with self._get_connection() as conn:
                # Check if row exists
                existing = conn.execute(
                    "SELECT 1 FROM scores_latest WHERE asset_id = ?", (
                        asset_id,)
                ).fetchone()

                if existing:
                    # Update existing row
                    conn.execute("""
                        UPDATE scores_latest SET
                            lt_score = ?,
                            lt_confidence = ?,
                            lt_breakdown = ?,
                            lt_updated_at = datetime('now')
                        WHERE asset_id = ?
                    """, (lt_score, lt_confidence, lt_breakdown, asset_id))
                else:
                    # Insert new row with only lt_* columns
                    conn.execute("""
                        INSERT INTO scores_latest (asset_id, market_scope, lt_score, 
                                                   lt_confidence, lt_breakdown, lt_updated_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (asset_id, market_scope, lt_score, lt_confidence, lt_breakdown))

                return True

        except Exception as e:
            logger.error(
                f"Failed to upsert longterm score for {asset_id}: {e}")
            return False

    def get_top_longterm_scores(
        self,
        market_scope: MarketScope = "US_EU",
        limit: int = 50
    ) -> List[Dict]:
        """
        Get top N assets by long-term score.

        Args:
            market_scope: Market scope filter
            limit: Number of results

        Returns:
            List of dicts with asset info and lt_score
        """
        sql = """
            SELECT 
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_code,
                s.score_total, s.lt_score, s.lt_confidence, s.lt_breakdown,
                s.confidence, g.liquidity, g.coverage
            FROM universe u
            INNER JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE u.active = 1 AND u.market_scope = ? AND s.lt_score IS NOT NULL
            ORDER BY s.lt_score DESC, s.lt_confidence DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, (market_scope, limit)).fetchall()
            return [dict(row) for row in rows]
