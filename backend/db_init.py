"""
MarketGPS Database Initialization Module

Comprehensive database setup ensuring all required tables and migrations
are applied safely with proper error handling.

This module is designed to be called during application startup to ensure
the database schema is properly initialized and all migrations are applied.
"""

import sqlite3
import logging
from typing import Callable, List
from storage.sqlite_store import SQLiteStore


logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles safe database initialization with idempotent migrations."""

    def __init__(self, db: SQLiteStore = None):
        """Initialize the DatabaseInitializer with a SQLiteStore instance."""
        self.db = db or SQLiteStore()

    def safe_execute(self, query: str, description: str = "") -> bool:
        """
        Safely execute a database query with proper error handling.

        Args:
            query: SQL query to execute
            description: Description of what the query does (for logging)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db._get_conn() as conn:
                conn.execute(query)
                conn.commit()
                if description:
                    logger.debug(f"✓ {description}")
                return True
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.debug(f"✗ {description}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in {description}: {e}")
            return False

    def create_news_articles_table(self) -> bool:
        """Create the main news_articles table with all columns."""
        query = """
        CREATE TABLE IF NOT EXISTS news_articles (
            id TEXT PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT,
            category TEXT,
            language TEXT DEFAULT 'fr',
            image_url TEXT,
            author TEXT,
            published_at TEXT,
            scraped_at TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            total_interactions INTEGER DEFAULT 0,
            keywords TEXT,
            relevance_score REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pending',
            published_to_app INTEGER DEFAULT 0,
            published_to_app_at TEXT,
            admin_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            -- Estimated interactions (viral system)
            estimated_views INTEGER DEFAULT 0,
            estimated_shares INTEGER DEFAULT 0,
            estimated_likes INTEGER DEFAULT 0,
            estimated_comments INTEGER DEFAULT 0,
            virality_score REAL DEFAULT 0.0,
            interactions_source TEXT DEFAULT 'estimated',
            interactions_updated_at TEXT,
            -- Francophone filtering columns
            francophone_relevance_score REAL DEFAULT 0.0,
            is_featured INTEGER DEFAULT 0,
            interaction_score REAL DEFAULT 0.0,
            language_score REAL DEFAULT 0.0,
            region_score REAL DEFAULT 0.0,
            recency_score REAL DEFAULT 0.0,
            topic_score REAL DEFAULT 0.0,
            daily_rank INTEGER DEFAULT NULL,
            score_calculated_at TEXT DEFAULT NULL,
            -- Editorial scoring
            editorial_score REAL DEFAULT 0.0,
            importance_level INTEGER DEFAULT 0,
            editorial_notes TEXT
        )
        """
        return self.safe_execute(query, "Create news_articles table")

    def create_video_scripts_table(self) -> bool:
        """Create the video_scripts table for viral news system."""
        query = """
        CREATE TABLE IF NOT EXISTS video_scripts (
            id TEXT PRIMARY KEY,
            article_id TEXT NOT NULL,
            title TEXT NOT NULL,
            hook TEXT,
            script_text TEXT NOT NULL,
            word_count INTEGER,
            estimated_duration_seconds INTEGER,
            sources_json TEXT,
            key_facts_json TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES news_articles(id)
        )
        """
        return self.safe_execute(query, "Create video_scripts table")

    def create_news_source_stats_table(self) -> bool:
        """Create the news_source_stats table for tracking source metrics."""
        query = """
        CREATE TABLE IF NOT EXISTS news_source_stats (
            source_id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            region TEXT,
            language TEXT,
            avg_interactions REAL DEFAULT 0,
            median_interactions REAL DEFAULT 0,
            total_articles INTEGER DEFAULT 0,
            last_calculated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_name)
        )
        """
        return self.safe_execute(query, "Create news_source_stats table")

    def create_news_interactions_history_table(self) -> bool:
        """Create table for tracking interactions history over time."""
        query = """
        CREATE TABLE IF NOT EXISTS news_interactions_history (
            id TEXT PRIMARY KEY,
            article_id TEXT NOT NULL,
            total_interactions INTEGER,
            virality_score REAL,
            source TEXT,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES news_articles(id)
        )
        """
        return self.safe_execute(query, "Create news_interactions_history table")

    def create_gamification_tables(self) -> bool:
        """Create all gamification-related tables."""
        success = True

        # User Gamification
        query_user_gamification = """
        CREATE TABLE IF NOT EXISTS user_gamification (
            user_id TEXT PRIMARY KEY,
            total_points INTEGER DEFAULT 0,
            current_level INTEGER DEFAULT 1,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_activity_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        success &= self.safe_execute(query_user_gamification, "Create user_gamification table")

        # User Badges
        query_user_badges = """
        CREATE TABLE IF NOT EXISTS user_badges (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            badge_id TEXT NOT NULL,
            earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_id),
            FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
        )
        """
        success &= self.safe_execute(query_user_badges, "Create user_badges table")

        # User Objectives
        query_user_objectives = """
        CREATE TABLE IF NOT EXISTS user_objectives (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            objective_type TEXT NOT NULL DEFAULT 'weekly',
            title TEXT NOT NULL,
            description TEXT,
            action TEXT NOT NULL,
            target INTEGER NOT NULL,
            current INTEGER DEFAULT 0,
            points_reward INTEGER NOT NULL,
            expires_at TEXT,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
        )
        """
        success &= self.safe_execute(query_user_objectives, "Create user_objectives table")

        # User Actions
        query_user_actions = """
        CREATE TABLE IF NOT EXISTS user_actions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            metadata_json TEXT,
            points_earned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
        )
        """
        success &= self.safe_execute(query_user_actions, "Create user_actions table")

        return success

    def create_francophone_filtering_tables(self) -> bool:
        """Create tables for francophone article filtering system."""
        success = True

        # Daily top 20 articles
        query_daily_top20 = """
        CREATE TABLE IF NOT EXISTS francophone_daily_top20 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            francophone_relevance_score REAL NOT NULL,
            interaction_score REAL,
            language_score REAL,
            region_score REAL,
            recency_score REAL,
            topic_score REAL,
            is_featured INTEGER DEFAULT 0,
            calculated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(date, rank),
            UNIQUE(date, article_id),
            FOREIGN KEY (article_id) REFERENCES news_articles(id)
        )
        """
        success &= self.safe_execute(query_daily_top20, "Create francophone_daily_top20 table")

        # Source metrics cache
        query_source_metrics = """
        CREATE TABLE IF NOT EXISTS source_metrics_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calculation_date TEXT NOT NULL,
            source_name TEXT NOT NULL,
            country TEXT,
            language TEXT,
            total_articles INTEGER DEFAULT 0,
            median_interactions REAL DEFAULT 0.0,
            avg_interactions REAL DEFAULT 0.0,
            articles_above_2x_median INTEGER DEFAULT 0,
            calculated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(calculation_date, source_name)
        )
        """
        success &= self.safe_execute(query_source_metrics, "Create source_metrics_cache table")

        # Filtering log
        query_filter_log = """
        CREATE TABLE IF NOT EXISTS francophone_filter_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            articles_analyzed INTEGER DEFAULT 0,
            articles_qualified INTEGER DEFAULT 0,
            articles_top20 INTEGER DEFAULT 0,
            featured_count INTEGER DEFAULT 0,
            avg_relevance_score REAL DEFAULT 0.0,
            started_at TEXT DEFAULT (datetime('now')),
            ended_at TEXT,
            status TEXT DEFAULT 'running',
            error_message TEXT
        )
        """
        success &= self.safe_execute(query_filter_log, "Create francophone_filter_log table")

        return success

    def create_app_settings_table(self) -> bool:
        """Create app_settings table for storing global configuration."""
        query = """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        return self.safe_execute(query, "Create app_settings table")

    def create_feedback_table(self) -> bool:
        """Create feedback table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            email TEXT,
            message TEXT NOT NULL,
            rating INTEGER,
            category TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        return self.safe_execute(query, "Create feedback table")

    def create_indices(self) -> bool:
        """Create all required indices for optimized queries."""
        success = True

        indices = [
            # News articles indices
            ("CREATE INDEX IF NOT EXISTS idx_news_status ON news_articles(status)",
             "Index news_articles.status"),
            ("CREATE INDEX IF NOT EXISTS idx_news_interactions ON news_articles(total_interactions DESC)",
             "Index news_articles.total_interactions"),
            ("CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_to_app)",
             "Index news_articles.published_to_app"),
            ("CREATE INDEX IF NOT EXISTS idx_news_scraped ON news_articles(scraped_at DESC)",
             "Index news_articles.scraped_at"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_interactions ON news_articles(total_interactions DESC)",
             "Index news_articles.total_interactions (viral)"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_source_date ON news_articles(source_name, created_at DESC)",
             "Index news_articles by source and date"),

            # Viral/virality indices
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_virality ON news_articles(virality_score DESC)",
             "Index news_articles.virality_score"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_total_interactions ON news_articles(total_interactions DESC)",
             "Index news_articles.total_interactions (combined)"),

            # Francophone filtering indices
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_relevance ON news_articles(francophone_relevance_score DESC, published_at DESC)",
             "Index news_articles.francophone_relevance_score"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_featured ON news_articles(is_featured DESC, francophone_relevance_score DESC)",
             "Index news_articles.is_featured"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_daily_rank ON news_articles(daily_rank) WHERE daily_rank IS NOT NULL",
             "Index news_articles.daily_rank"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_interaction_score ON news_articles(interaction_score DESC)",
             "Index news_articles.interaction_score"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_score_calculated ON news_articles(score_calculated_at DESC)",
             "Index news_articles.score_calculated_at"),
            ("CREATE INDEX IF NOT EXISTS idx_news_articles_strict_filter ON news_articles(language, status, francophone_relevance_score DESC, published_at DESC) WHERE status = 'published' AND language = 'fr'",
             "Index news_articles for strict filtering"),

            # Video scripts indices
            ("CREATE INDEX IF NOT EXISTS idx_video_scripts_status ON video_scripts(status)",
             "Index video_scripts.status"),
            ("CREATE INDEX IF NOT EXISTS idx_video_scripts_article ON video_scripts(article_id)",
             "Index video_scripts.article_id"),
            ("CREATE INDEX IF NOT EXISTS idx_video_scripts_created ON video_scripts(created_at DESC)",
             "Index video_scripts.created_at"),

            # Interactions history indices
            ("CREATE INDEX IF NOT EXISTS idx_interactions_history_article ON news_interactions_history(article_id)",
             "Index news_interactions_history.article_id"),
            ("CREATE INDEX IF NOT EXISTS idx_interactions_history_date ON news_interactions_history(recorded_at)",
             "Index news_interactions_history.recorded_at"),

            # Gamification indices
            ("CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id)",
             "Index user_badges.user_id"),
            ("CREATE INDEX IF NOT EXISTS idx_user_badges_badge_id ON user_badges(badge_id)",
             "Index user_badges.badge_id"),
            ("CREATE INDEX IF NOT EXISTS idx_user_objectives_user_id ON user_objectives(user_id)",
             "Index user_objectives.user_id"),
            ("CREATE INDEX IF NOT EXISTS idx_user_objectives_type ON user_objectives(objective_type)",
             "Index user_objectives.objective_type"),
            ("CREATE INDEX IF NOT EXISTS idx_user_objectives_completed ON user_objectives(completed_at)",
             "Index user_objectives.completed_at"),
            ("CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id)",
             "Index user_actions.user_id"),
            ("CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action)",
             "Index user_actions.action"),
            ("CREATE INDEX IF NOT EXISTS idx_user_actions_date ON user_actions(created_at)",
             "Index user_actions.created_at"),
            ("CREATE INDEX IF NOT EXISTS idx_user_actions_user_date ON user_actions(user_id, created_at)",
             "Index user_actions by user and date"),
            ("CREATE INDEX IF NOT EXISTS idx_user_gamification_points ON user_gamification(total_points DESC)",
             "Index user_gamification.total_points"),
            ("CREATE INDEX IF NOT EXISTS idx_user_gamification_level ON user_gamification(current_level DESC)",
             "Index user_gamification.current_level"),

            # Francophone daily top 20 indices
            ("CREATE INDEX IF NOT EXISTS idx_daily_top20_date ON francophone_daily_top20(date DESC)",
             "Index francophone_daily_top20.date"),
            ("CREATE INDEX IF NOT EXISTS idx_daily_top20_rank ON francophone_daily_top20(date, rank)",
             "Index francophone_daily_top20 by date and rank"),
            ("CREATE INDEX IF NOT EXISTS idx_daily_top20_article ON francophone_daily_top20(article_id)",
             "Index francophone_daily_top20.article_id"),

            # Source metrics indices
            ("CREATE INDEX IF NOT EXISTS idx_source_metrics_date ON source_metrics_cache(calculation_date DESC)",
             "Index source_metrics_cache.calculation_date"),
            ("CREATE INDEX IF NOT EXISTS idx_source_metrics_source ON source_metrics_cache(source_name)",
             "Index source_metrics_cache.source_name"),

            # Filtering log indices
            ("CREATE INDEX IF NOT EXISTS idx_filter_log_date ON francophone_filter_log(date DESC)",
             "Index francophone_filter_log.date"),
            ("CREATE INDEX IF NOT EXISTS idx_filter_log_status ON francophone_filter_log(status)",
             "Index francophone_filter_log.status"),
        ]

        for query, description in indices:
            success &= self.safe_execute(query, description)

        return success

    def initialize(self) -> bool:
        """
        Run complete database initialization.

        Creates all tables and indices in the correct order.
        Safe for repeated calls (idempotent).

        Returns:
            True if all operations succeeded, False otherwise
        """
        logger.info("Starting MarketGPS database initialization...")

        success = True

        # Create tables in dependency order
        success &= self.create_news_articles_table()
        success &= self.create_video_scripts_table()
        success &= self.create_news_source_stats_table()
        success &= self.create_news_interactions_history_table()
        success &= self.create_gamification_tables()
        success &= self.create_francophone_filtering_tables()
        success &= self.create_app_settings_table()
        success &= self.create_feedback_table()

        # Create all indices
        success &= self.create_indices()

        if success:
            logger.info("✓ Database initialization completed successfully")
        else:
            logger.warning("⚠ Database initialization completed with some errors (non-critical)")

        return success


def initialize_database():
    """
    Convenience function to initialize the database.

    Call this from application startup to ensure the database
    schema is properly set up before any operations.

    Example:
        from db_init import initialize_database

        @app.on_event("startup")
        async def startup_event():
            initialize_database()
    """
    try:
        db = SQLiteStore()
        initializer = DatabaseInitializer(db)
        initializer.initialize()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    """Allow running this script standalone for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    initialize_database()
    print("Database initialized successfully!")
