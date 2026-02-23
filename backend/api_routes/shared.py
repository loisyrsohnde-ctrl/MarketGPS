"""
Shared dependencies for API routes.
Database instances, helper functions, and response models.
"""

import os
from typing import Optional, List
from pathlib import Path as FilePath
from pydantic import BaseModel

from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore
from security import get_user_id_from_request
from storage.parquet_store import ParquetStore

# Centralized asset query module (PR3)
try:
    from asset_query import AssetQueryBuilder, AssetFilters, AFRICA_REGIONS
    ASSET_QUERY_AVAILABLE = True
except ImportError:
    ASSET_QUERY_AVAILABLE = False
    AFRICA_REGIONS = {}

# Shared database instances
db = SQLiteStore()
parquet_us_eu = ParquetStore(market_scope="US_EU")
parquet_africa = ParquetStore(market_scope="AFRICA")

# Logo directory
LOGOS_DIR = FilePath(__file__).parent.parent.parent / "data" / "logos"

# 1x1 transparent PNG placeholder
PLACEHOLDER_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
    0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
    0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
])


def resolve_user_id(user_id: Optional[str], authorization: Optional[str]) -> str:
    """Resolve user_id from token in prod, or fallback in dev."""
    fallback_user_id = user_id or "default"
    return get_user_id_from_request(authorization, fallback_user_id=fallback_user_id)


# ═══════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════

class AssetResponse(BaseModel):
    asset_id: str
    ticker: str
    symbol: str
    name: str
    asset_type: str
    market_scope: Optional[str] = None
    market_code: Optional[str] = None
    score_total: Optional[float] = None
    score_value: Optional[float] = None
    score_momentum: Optional[float] = None
    score_safety: Optional[float] = None
    confidence: Optional[float] = None
    coverage: Optional[float] = None
    liquidity: Optional[float] = None
    fx_risk: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    lt_score: Optional[float] = None
    lt_confidence: Optional[float] = None
    score_institutional: Optional[float] = None
    liquidity_tier: Optional[str] = None
    liquidity_flag: Optional[bool] = None
    data_quality_flag: Optional[bool] = None
    data_quality_score: Optional[float] = None
    stale_price_flag: Optional[bool] = None
    min_recommended_horizon_years: Optional[int] = None
    adv_usd: Optional[float] = None


class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScopeCountsResponse(BaseModel):
    US_EU: int
    AFRICA: int


class AssetDetailResponse(BaseModel):
    asset_id: str
    symbol: str
    name: str
    asset_type: str
    market_scope: Optional[str] = None
    market_code: Optional[str] = None
    score_total: Optional[float] = None
    score_value: Optional[float] = None
    score_momentum: Optional[float] = None
    score_safety: Optional[float] = None
    score_fx_risk: Optional[float] = None
    score_liquidity_risk: Optional[float] = None
    confidence: Optional[float] = None
    coverage: Optional[float] = None
    liquidity: Optional[float] = None
    fx_risk: Optional[float] = None
    rsi: Optional[float] = None
    vol_annual: Optional[float] = None
    max_drawdown: Optional[float] = None
    last_price: Optional[float] = None
    score_institutional: Optional[float] = None
    liquidity_tier: Optional[str] = None
    liquidity_flag: Optional[bool] = None
    liquidity_penalty: Optional[float] = None
    data_quality_flag: Optional[bool] = None
    data_quality_score: Optional[float] = None
    stale_price_flag: Optional[bool] = None
    min_recommended_horizon_years: Optional[int] = None
    institutional_explanation: Optional[str] = None
    adv_usd: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    lt_score: Optional[float] = None
    lt_confidence: Optional[float] = None
    lt_breakdown: Optional[dict] = None


class WatchlistAddRequest(BaseModel):
    ticker: str
    market_scope: Optional[str] = "US_EU"
    notes: Optional[str] = None
