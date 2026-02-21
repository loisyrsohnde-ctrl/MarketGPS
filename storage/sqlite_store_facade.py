"""
SQLiteStore Facade - Main interface delegating to specialized repositories.

This is the refactored SQLiteStore following the Repository pattern.
All methods are delegated to specialized repositories for better maintainability.
"""
from typing import Optional, List, Dict, Any, Tuple, Literal
from pathlib import Path

from core.config import get_config, get_logger
from core.models import (
    Asset, AssetType, GatingStatus, Score, RotationState,
    WatchlistItem, StateLabel, ScoreBreakdown
)

from storage.base_repository import BaseRepository, MarketScope, VALID_SCOPES
from storage.asset_repository import AssetRepository
from storage.score_repository import ScoreRepository
from storage.news_repository import NewsRepository
from storage.user_repository import UserRepository
from storage.subscription_repository import SubscriptionRepository
from storage.general_repository import GeneralRepository
from storage.explorer_repository import ExplorerRepository

logger = get_logger(__name__)


class SQLiteStore:
    """
    SQLiteStore - Main facade for database operations.

    Delegates to specialized repositories:
    - AssetRepository: Universe and gating operations
    - ScoreRepository: Score, rotation, calibration, watchlist, and job runs
    - NewsRepository: News articles and sources
    - UserRepository: User accounts and profiles
    - SubscriptionRepository: Subscription and quota management
    - GeneralRepository: Jobs queue, quotas, settings, statistics
    - ExplorerRepository: Search, landing page metrics, long-term scoring
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLiteStore and all repositories."""
        config = get_config()
        self.db_path = db_path or str(config.storage.sqlite_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize repositories
        self._assets = AssetRepository(self.db_path)
        self._scores = ScoreRepository(self.db_path)
        self._news = NewsRepository(self.db_path)
        self._users = UserRepository(self.db_path)
        self._subscriptions = SubscriptionRepository(self.db_path)
        self._general = GeneralRepository(self.db_path)
        self._explorer = ExplorerRepository(self.db_path)

        # Initialize schema
        self._init_schema()

    def _get_connection(self):
        """Delegate to base repository for connection management."""
        return self._assets._get_connection()

    _get_conn = _get_connection

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEMA INITIALIZATION (from base repository)
    # ═══════════════════════════════════════════════════════════════════════════

    def _init_schema(self):
        """Delegate schema initialization."""
        self._assets._init_schema()

    def _ensure_auth_tables(self):
        """Delegate auth table creation."""
        self._assets._ensure_auth_tables()

    def _ensure_subscriptions_table(self, conn):
        """Delegate subscriptions table creation."""
        self._assets._ensure_subscriptions_table(conn)

    def _ensure_strategy_tables(self):
        """Delegate strategy tables creation."""
        self._assets._ensure_strategy_tables()

    def _ensure_news_tables(self):
        """Delegate news tables creation."""
        self._assets._ensure_news_tables()

    def ensure_schema(self):
        """Ensure all tables exist."""
        self._assets.ensure_schema()

    def reset_schema(self):
        """Reset database schema."""
        self._assets.reset_schema()

    # ═══════════════════════════════════════════════════════════════════════════
    # ASSET OPERATIONS (delegated to AssetRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    def upsert_asset(self, asset: Asset, market_scope: MarketScope = "US_EU"):
        return self._assets.upsert_asset(asset, market_scope)

    def bulk_upsert_assets(self, assets: List[Dict], market_scope: MarketScope = "US_EU"):
        return self._assets.bulk_upsert_assets(assets, market_scope)

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self._assets.get_asset(asset_id)

    def get_active_assets(
        self,
        asset_type: Optional[AssetType] = None,
        market_scope: Optional[MarketScope] = None
    ) -> List[Asset]:
        return self._assets.get_active_assets(asset_type, market_scope)

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
        return self._assets.list_assets_paginated(
            market_scope, asset_type, search, scored_filter, eligible_only,
            active_only, sort_by, sort_desc, page, page_size
        )

    def list_top_n(
        self,
        market_scope: Optional[MarketScope] = None,
        asset_type: Optional[str] = None,
        n: int = 50
    ) -> List[Dict]:
        return self._assets.list_top_n(market_scope, asset_type, n)

    def get_asset_detail(self, asset_id: str) -> Optional[Dict]:
        return self._assets.get_asset_detail(asset_id)

    def search_assets(
        self,
        query: str,
        market_scope: Optional[MarketScope] = None,
        limit: int = 20
    ) -> List[Dict]:
        return self._assets.search_assets(query, market_scope, limit)

    def count_assets(
        self,
        asset_type: Optional[str] = None,
        market_scope: Optional[MarketScope] = None
    ) -> Dict[str, int]:
        return self._assets.count_assets(asset_type, market_scope)

    def count_by_type(self, market_scope: Optional[MarketScope] = None) -> Dict[str, int]:
        return self._assets.count_by_type(market_scope)

    def count_by_scope(self) -> Dict[str, int]:
        return self._assets.count_by_scope()

    def upsert_gating(self, gating: GatingStatus, market_scope: MarketScope = "US_EU"):
        return self._assets.upsert_gating(gating, market_scope)

    def get_gating(self, asset_id: str) -> Optional[GatingStatus]:
        return self._assets.get_gating(asset_id)

    def get_eligible_assets(self, market_scope: MarketScope = "US_EU") -> List[str]:
        return self._assets.get_eligible_assets(market_scope)

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORE OPERATIONS (delegated to ScoreRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    def upsert_score(self, score: Score, market_scope: MarketScope = "US_EU"):
        return self._scores.upsert_score(score, market_scope)

    def get_score(self, asset_id: str) -> Optional[Score]:
        return self._scores.get_score(asset_id)

    def get_latest_score(self, ticker: str, market_scope: str = "US_EU") -> Optional[Dict]:
        return self._scores.get_latest_score(ticker, market_scope)

    def get_asset_by_ticker(self, ticker: str) -> Optional[Dict]:
        return self._scores.get_asset_by_ticker(ticker)

    def get_top_scores(
        self,
        limit: int = 50,
        asset_type: Optional[AssetType] = None,
        market_scope: Optional[MarketScope] = None
    ) -> List[Tuple[Asset, Score]]:
        return self._scores.get_top_scores(limit, asset_type, market_scope)

    def upsert_rotation_state(self, state: RotationState, market_scope: MarketScope = "US_EU"):
        return self._scores.upsert_rotation_state(state, market_scope)

    def get_priority_assets(self, limit: int = 50, market_scope: MarketScope = "US_EU") -> List[str]:
        return self._scores.get_priority_assets(limit, market_scope)

    def set_priority_level(self, asset_ids: List[str], priority: int = 1, market_scope: MarketScope = "US_EU"):
        return self._scores.set_priority_level(asset_ids, priority, market_scope)

    def get_calibration_params(self, market_scope: MarketScope = "US_EU") -> Dict:
        return self._scores.get_calibration_params(market_scope)

    def update_calibration_params(self, market_scope: MarketScope, params: Dict):
        return self._scores.update_calibration_params(market_scope, params)

    def add_watchlist(
        self,
        ticker: str,
        user_id: str = "default",
        notes: str = None,
        market_scope: MarketScope = "US_EU"
    ) -> bool:
        return self._scores.add_watchlist(ticker, user_id, notes, market_scope)

    def remove_watchlist(self, ticker: str, user_id: str = "default") -> bool:
        return self._scores.remove_watchlist(ticker, user_id)

    def list_watchlist(
        self,
        user_id: str = "default",
        market_scope: Optional[MarketScope] = None
    ) -> List[Dict]:
        return self._scores.list_watchlist(user_id, market_scope)

    def is_in_watchlist(self, ticker: str, user_id: str = "default") -> bool:
        return self._scores.is_in_watchlist(ticker, user_id)

    def get_watchlist_tickers(self, user_id: str = "default") -> List[str]:
        return self._scores.get_watchlist_tickers(user_id)

    # Job Runs
    def create_job_run(
        self,
        market_scope: MarketScope,
        job_type: str,
        mode: str = "daily_full",
        created_by: str = "scheduler"
    ) -> str:
        return self._scores.create_job_run(market_scope, job_type, mode, created_by)

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
        return self._scores.update_job_run_status(
            run_id, status, assets_processed, assets_success, assets_failed,
            duration_seconds, stats, error
        )

    def insert_staging_score(self, run_id: str, score: Score, market_scope: MarketScope = "US_EU"):
        return self._scores.insert_staging_score(run_id, score, market_scope)

    def insert_staging_gating(self, run_id: str, gating: GatingStatus, market_scope: MarketScope = "US_EU"):
        return self._scores.insert_staging_gating(run_id, gating, market_scope)

    def publish_run(
        self,
        run_id: str,
        market_scope: MarketScope,
        publish_scores: bool = True,
        publish_gating: bool = True
    ) -> Dict[str, int]:
        return self._scores.publish_run(run_id, market_scope, publish_scores, publish_gating)

    def rollback_run(self, run_id: str):
        return self._scores.rollback_run(run_id)

    def get_job_run(self, run_id: str) -> Optional[Dict]:
        return self._scores.get_job_run(run_id)

    def get_recent_job_runs(
        self,
        market_scope: Optional[MarketScope] = None,
        job_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        return self._scores.get_recent_job_runs(market_scope, job_type, limit)

    def cleanup_old_staging(self, hours_old: int = 24):
        return self._scores.cleanup_old_staging(hours_old)

    # ═══════════════════════════════════════════════════════════════════════════
    # NEWS OPERATIONS (delegated to NewsRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_news_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None,
        country: Optional[str] = None,
        tag: Optional[str] = None,
        region: Optional[str] = None,
        sort_by: Optional[str] = "date",
        status: str = "published",
        prioritize_francophone: bool = True
    ) -> Dict:
        return self._news.get_news_articles(
            page, page_size, query, country, tag, region, sort_by, status, prioritize_francophone
        )

    def get_news_article_by_slug(self, slug: str) -> Optional[Dict]:
        return self._news.get_news_article_by_slug(slug)

    def save_news_article_for_user(self, user_id: str, article_id: int) -> bool:
        return self._news.save_news_article_for_user(user_id, article_id)

    def unsave_news_article_for_user(self, user_id: str, article_id: int) -> bool:
        return self._news.unsave_news_article_for_user(user_id, article_id)

    def get_saved_news_articles(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        return self._news.get_saved_news_articles(user_id, page, page_size)

    def is_article_saved_by_user(self, user_id: str, article_id: int) -> bool:
        return self._news.is_article_saved_by_user(user_id, article_id)

    def article_exists(self, source_url: str, title: str) -> bool:
        return self._news.article_exists(source_url, title)

    def insert_news_article(self, article: Dict) -> Optional[int]:
        return self._news.insert_news_article(article)

    def insert_news_raw_item(self, item: Dict) -> Optional[int]:
        return self._news.insert_news_raw_item(item)

    def get_unprocessed_raw_items(self, limit: int = 50) -> List[Dict]:
        return self._news.get_unprocessed_raw_items(limit)

    def mark_raw_item_processed(self, item_id: int, error: Optional[str] = None) -> bool:
        return self._news.mark_raw_item_processed(item_id, error)

    def get_news_sources(self, enabled_only: bool = True) -> List[Dict]:
        return self._news.get_news_sources(enabled_only)

    def upsert_news_source(self, source: Dict) -> Optional[int]:
        return self._news.upsert_news_source(source)

    def update_source_fetch_status(self, source_id: int, error: Optional[str] = None) -> bool:
        return self._news.update_source_fetch_status(source_id, error)

    # ═══════════════════════════════════════════════════════════════════════════
    # USER OPERATIONS (delegated to UserRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    def create_user(self, email: str, password_hash: str) -> Optional[str]:
        return self._users.create_user(email, password_hash)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        return self._users.get_user_by_email(email)

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        return self._users.get_user_by_id(user_id)

    def update_last_login(self, user_id: str):
        return self._users.update_last_login(user_id)

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        return self._users.get_user_profile(user_id)

    def update_user_profile(self, user_id: str, display_name: str = None, avatar_path: str = None, bio: str = None) -> bool:
        return self._users.update_user_profile(user_id, display_name, avatar_path, bio)

    # ═══════════════════════════════════════════════════════════════════════════
    # SUBSCRIPTION OPERATIONS (delegated to SubscriptionRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_subscription(self, user_id: str) -> Dict:
        return self._subscriptions.get_subscription(user_id)

    def set_subscription(self, user_id: str, plan: str, status: str = "active", renews_at: str = None) -> bool:
        return self._subscriptions.set_subscription(user_id, plan, status, renews_at)

    def is_pro_user(self, user_id: str) -> bool:
        return self._subscriptions.is_pro_user(user_id)

    def can_calculate_score(self, user_id: str) -> bool:
        return self._subscriptions.can_calculate_score(user_id)

    def consume_calculation_quota(self, user_id: str, count: int = 1) -> bool:
        return self._subscriptions.consume_calculation_quota(user_id, count)

    def reset_daily_quotas(self):
        return self._subscriptions.reset_daily_quotas()

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERAL OPERATIONS (delegated to GeneralRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    # Jobs Queue
    def enqueue_job(
        self,
        job_type: str,
        payload: Dict,
        market_scope: MarketScope = "US_EU",
        priority: int = 2,
        user_id: str = "default"
    ) -> int:
        return self._general.enqueue_job(job_type, payload, market_scope, priority, user_id)

    def fetch_next_job_atomic(self, market_scope: Optional[MarketScope] = None) -> Optional[Dict]:
        return self._general.fetch_next_job_atomic(market_scope)

    def mark_job_done(self, job_id: int):
        return self._general.mark_job_done(job_id)

    def mark_job_failed(self, job_id: int, error: str):
        return self._general.mark_job_failed(job_id, error)

    def get_pending_jobs_count(self, market_scope: Optional[MarketScope] = None) -> int:
        return self._general.get_pending_jobs_count(market_scope)

    def get_recent_jobs(self, limit: int = 10, market_scope: Optional[MarketScope] = None) -> List[Dict]:
        return self._general.get_recent_jobs(limit, market_scope)

    # Quota
    def get_today_usage(self, user_id: str = "default") -> Dict:
        return self._general.get_today_usage(user_id)

    def can_consume_quota(self, count: int, user_id: str = "default") -> bool:
        return self._general.can_consume_quota(count, user_id)

    def consume_quota(self, count: int, user_id: str = "default") -> bool:
        return self._general.consume_quota(count, user_id)

    def set_user_tier(self, user_id: str, tier: str, limit: int):
        return self._general.set_user_tier(user_id, tier, limit)

    # Settings
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        return self._general.get_setting(key, default)

    def set_setting(self, key: str, value: str):
        return self._general.set_setting(key, value)

    def is_pro_mode_enabled(self) -> bool:
        return self._general.is_pro_mode_enabled()

    def set_pro_mode(self, enabled: bool):
        return self._general.set_pro_mode(enabled)

    # Statistics
    def get_stats(self, market_scope: Optional[MarketScope] = None) -> Dict[str, Any]:
        return self._general.get_stats(market_scope)

    # ═══════════════════════════════════════════════════════════════════════════
    # EXPLORER OPERATIONS (delegated to ExplorerRepository)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_landing_metrics(self, market_scope: str = "US_EU") -> Dict:
        return self._explorer.get_landing_metrics(market_scope)

    def search_universe(
        self,
        market_scope: str = "US_EU",
        market_code: str = None,
        asset_type: str = None,
        country: str = None,
        region: str = None,
        query: str = None,
        only_scored: bool = True,
        sort_by: str = "score_total",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        return self._explorer.search_universe(
            market_scope, market_code, asset_type, country, region, query,
            only_scored, sort_by, sort_desc, limit, offset
        )

    def get_top_scored_assets(
        self,
        market_scope: str = "US_EU",
        asset_type: str = None,
        limit: int = 50,
        market_filter: str = "ALL"
    ) -> List[Dict]:
        return self._explorer.get_top_scored_assets(market_scope, asset_type, limit, market_filter)

    def get_asset_types_for_scope(self, market_scope: str = "US_EU") -> List[str]:
        return self._explorer.get_asset_types_for_scope(market_scope)

    # Long-term Scoring
    def ensure_longterm_schema(self) -> bool:
        return self._explorer.ensure_longterm_schema()

    def upsert_longterm_score(
        self,
        asset_id: str,
        market_scope: str = "US_EU",
        lt_score: float = None,
        lt_confidence: float = None,
        lt_breakdown: Dict = None
    ) -> bool:
        return self._explorer.upsert_longterm_score(
            asset_id, market_scope, lt_score, lt_confidence, lt_breakdown
        )

    def get_top_longterm_scores(
        self,
        market_scope: str = "US_EU",
        asset_type: str = None,
        limit: int = 50
    ) -> List[Dict]:
        return self._explorer.get_top_longterm_scores(market_scope, asset_type, limit)
