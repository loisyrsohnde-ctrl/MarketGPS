"""
MarketGPS - API Routes Package
Assembles all sub-module routers into a single router.

Sub-modules:
  - assets: Asset lookup, search, explorer, chart, details, logos
  - metrics: Dashboard counts, stats, landing metrics
  - watchlist: User watchlist management
  - scoring: On-demand and ad-hoc scoring
  - validation: Geographic validation and quarantine
"""

from fastapi import APIRouter

from .assets import router as assets_router
from .metrics import router as metrics_router
from .watchlist import router as watchlist_router
from .scoring import router as scoring_router
from .validation import router as validation_router

# Main router with /api prefix - same as original api_routes.py
router = APIRouter(prefix="/api", tags=["Assets"])

# Include all sub-routers
router.include_router(assets_router)
router.include_router(metrics_router)
router.include_router(watchlist_router)
router.include_router(scoring_router)
router.include_router(validation_router)

# Re-export response models for backward compatibility
from .shared import (
    AssetResponse,
    PaginatedResponse,
    ScopeCountsResponse,
    AssetDetailResponse,
    WatchlistAddRequest,
    db,
    resolve_user_id,
)

__all__ = [
    "router",
    "AssetResponse",
    "PaginatedResponse",
    "ScopeCountsResponse",
    "AssetDetailResponse",
    "WatchlistAddRequest",
    "db",
    "resolve_user_id",
]
