"""
Base Repository - Shared database operations for all repositories.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Literal

from core.config import get_config, get_logger

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]
VALID_SCOPES = {"US_EU", "AFRICA"}


class BaseRepository:
    """Base repository with shared database operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize base repository."""
        config = get_config()
        self.db_path = db_path or str(config.storage.sqlite_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

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

                    -- User profiles
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        display_name TEXT,
                        avatar_path TEXT,
                        bio TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    );

                    -- User settings
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY,
                        theme TEXT DEFAULT 'light',
                        notifications_enabled INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                """)

                self._ensure_subscriptions_table(conn)
                logger.info("Authentication tables created")

    def _ensure_subscriptions_table(self, conn):
        """Create subscriptions table if not exists."""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS subscriptions_state (
                user_id TEXT PRIMARY KEY,
                plan TEXT DEFAULT 'free',
                status TEXT DEFAULT 'active',
                daily_quota_used INTEGER DEFAULT 0,
                daily_quota_limit INTEGER DEFAULT 3,
                scopes_access TEXT DEFAULT 'US_EU',
                started_at TEXT,
                renews_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)

    def _ensure_strategy_tables(self):
        """Ensure strategy-related tables exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rotation_state (
                    asset_id TEXT PRIMARY KEY,
                    market_scope TEXT DEFAULT 'US_EU',
                    last_refresh_at TEXT,
                    priority_level INTEGER DEFAULT 2,
                    in_top50 INTEGER DEFAULT 0,
                    cooldown_until TEXT,
                    last_error TEXT,
                    refresh_count INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS calibration_params (
                    market_scope TEXT PRIMARY KEY,
                    weight_momentum REAL DEFAULT 0.4,
                    weight_safety REAL DEFAULT 0.3,
                    weight_value REAL DEFAULT 0.3,
                    weight_fx_risk REAL DEFAULT 0.0,
                    weight_liquidity_risk REAL DEFAULT 0.0,
                    rsi_optimal_low REAL DEFAULT 40.0,
                    rsi_optimal_high REAL DEFAULT 70.0,
                    vol_target_max REAL DEFAULT 30.0,
                    drawdown_target_max REAL DEFAULT 20.0,
                    min_liquidity_usd INTEGER DEFAULT 1000000,
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    user_id TEXT DEFAULT 'default',
                    market_scope TEXT DEFAULT 'US_EU',
                    market_code TEXT,
                    notes TEXT,
                    added_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(asset_id, user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
            """)

    def _ensure_news_tables(self):
        """Ensure news-related tables exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    raw_item_id INTEGER,
                    title TEXT NOT NULL,
                    excerpt TEXT,
                    content_md TEXT,
                    tldr_json TEXT,
                    tags_json TEXT,
                    country TEXT,
                    language TEXT DEFAULT 'en',
                    image_url TEXT,
                    source_name TEXT,
                    source_url TEXT,
                    canonical_url TEXT,
                    published_at TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    status TEXT DEFAULT 'published',
                    category TEXT,
                    sentiment TEXT DEFAULT 'neutral',
                    is_ai_processed INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0.0,
                    is_breaking_news INTEGER DEFAULT 0,
                    importance_level TEXT DEFAULT 'normal'
                );

                CREATE TABLE IF NOT EXISTS news_raw_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    published_at TEXT,
                    raw_payload TEXT,
                    content_hash TEXT,
                    fetched_at TEXT DEFAULT (datetime('now')),
                    processed INTEGER DEFAULT 0,
                    process_error TEXT
                );

                CREATE TABLE IF NOT EXISTS news_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    type TEXT DEFAULT 'rss',
                    rss_url TEXT,
                    country TEXT,
                    region TEXT,
                    language TEXT DEFAULT 'en',
                    tags TEXT,
                    trust_score REAL DEFAULT 0.7,
                    enabled INTEGER DEFAULT 1,
                    last_fetched_at TEXT,
                    fetch_error TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS news_user_saves (
                    user_id TEXT NOT NULL,
                    article_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    PRIMARY KEY(user_id, article_id),
                    FOREIGN KEY(article_id) REFERENCES news_articles(id)
                );

                CREATE INDEX IF NOT EXISTS idx_news_articles_status ON news_articles(status);
                CREATE INDEX IF NOT EXISTS idx_news_articles_country ON news_articles(country);
                CREATE INDEX IF NOT EXISTS idx_news_raw_items_processed ON news_raw_items(processed);
            """)

    def ensure_schema(self):
        """Ensure all tables exist (public method)."""
        self._init_schema()
        self._ensure_strategy_tables()
        self._ensure_news_tables()
        logger.info("All schemas ensured")

    def reset_schema(self):
        """Drop all tables and reinitialize (careful!)."""
        with self._get_connection() as conn:
            # Get all table names
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table['name']}")

            logger.warning("All tables dropped - reinitializing schema...")
            self._init_schema()
