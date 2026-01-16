"""
MarketGPS - API Routes for Assets/Scores/Watchlist
Exposes SQLite data to the Next.js frontend.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

# Add parent directory to path to import from storage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore

# Initialize SQLite store
db = SQLiteStore()

# Initialize Parquet stores for each scope
parquet_us_eu = ParquetStore(market_scope="US_EU")
parquet_africa = ParquetStore(market_scope="AFRICA")

# Create router
router = APIRouter(prefix="/api", tags=["Assets"])


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
    sector: Optional[str] = None
    industry: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Assets Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/assets/top-scored")
async def get_top_scored(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    market_scope: Optional[str] = Query(None, description="US_EU or AFRICA"),
    asset_type: Optional[str] = Query(None, description="ETF, EQUITY, FX, BOND"),
    market_filter: Optional[str] = Query(None, description="ALL, US, EU, AFRICA"),
    only_scored: bool = Query(True, description="Only return assets with scores"),
):
    """
    Get top scored assets with optional filters.
    """
    try:
        # Handle scope and market_code from market_filter
        scope = market_scope
        market_code = None
        
        if market_filter:
            if market_filter == "AFRICA":
                scope = "AFRICA"
            elif market_filter == "US":
                scope = "US_EU"
                market_code = "US"
            elif market_filter == "EU":
                scope = "US_EU"
                market_code = "EU"
            elif market_filter == "ALL":
                scope = "US_EU"
        
        # Use scope or default to US_EU
        scope = scope or "US_EU"
        
        # For EU or AFRICA filters, also show unscored assets
        show_only_scored = only_scored
        if market_filter in ("EU", "AFRICA"):
            show_only_scored = False
        
        # Use search_universe which supports unscored assets and market_code
        assets, total = db.search_universe(
            market_scope=scope,
            market_code=market_code,
            asset_type=asset_type,
            query=None,
            only_scored=show_only_scored,
            sort_by="score_total",
            sort_desc=True,
            limit=limit,
            offset=offset
        )
        
        # Format response
        formatted = []
        for a in assets:
            formatted.append({
                "asset_id": a.get("asset_id"),
                "ticker": a.get("symbol"),
                "symbol": a.get("symbol"),
                "name": a.get("name"),
                "asset_type": a.get("asset_type"),
                "market_scope": a.get("market_scope", scope),
                "market_code": a.get("market_code"),
                "score_total": a.get("score_total"),
                "score_value": a.get("score_value"),
                "score_momentum": a.get("score_momentum"),
                "score_safety": a.get("score_safety"),
                "confidence": a.get("confidence"),
                "coverage": a.get("coverage"),
                "liquidity": a.get("liquidity"),
            })
        
        return {
            "data": formatted,
            "total": total,
            "page": (offset // limit) + 1,
            "page_size": limit,
            "total_pages": max(1, (total + limit - 1) // limit) if limit > 0 else 1,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/search")
async def search_assets(
    q: str = Query(..., min_length=1),
    market_scope: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search assets by symbol or name.
    """
    try:
        results = db.search_assets(
            query=q,
            market_scope=market_scope,
            limit=limit
        )
        
        formatted = []
        for a in results:
            formatted.append({
                "asset_id": a.get("asset_id"),
                "ticker": a.get("symbol"),
                "symbol": a.get("symbol"),
                "name": a.get("name"),
                "asset_type": a.get("asset_type"),
                "market_scope": a.get("market_scope"),
                "market_code": a.get("market_code"),
                "score_total": a.get("score_total"),
                "confidence": a.get("confidence"),
            })
        
        return formatted
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/explorer")
async def explore_assets(
    market_scope: str = Query("US_EU"),
    asset_type: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    only_scored: bool = Query(True),
    sort_by: str = Query("score_total"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    Paginated explorer for all assets.
    """
    try:
        offset = (page - 1) * page_size
        
        results, total = db.search_universe(
            market_scope=market_scope,
            asset_type=asset_type,
            query=query,
            only_scored=only_scored,
            sort_by=sort_by,
            sort_desc=sort_desc,
            limit=page_size,
            offset=offset
        )
        
        formatted = []
        for a in results:
            formatted.append({
                "asset_id": a.get("asset_id"),
                "ticker": a.get("symbol"),
                "symbol": a.get("symbol"),
                "name": a.get("name"),
                "asset_type": a.get("asset_type"),
                "market_scope": a.get("market_scope"),
                "market_code": a.get("market_code"),
                "score_total": a.get("score_total"),
                "score_value": a.get("score_value"),
                "score_momentum": a.get("score_momentum"),
                "score_safety": a.get("score_safety"),
                "confidence": a.get("confidence"),
                "coverage": a.get("coverage"),
                "liquidity": a.get("liquidity"),
                "fx_risk": a.get("fx_risk"),
                "sector": a.get("sector"),
                "industry": a.get("industry"),
            })
        
        return {
            "data": formatted,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 1,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{ticker}/chart")
async def get_asset_chart(
    ticker: str,
    period: str = Query("30d", description="1d, 1w, 7d, 30d, 3m, 6m, 1y, 5y, 10y"),
):
    """
    Get historical price data for charting.
    """
    import pandas as pd
    from pathlib import Path
    
    try:
        # Determine market scope from ticker
        results = db.search_assets(query=ticker, limit=10)
        asset = None
        for a in results:
            if a.get("symbol", "").upper() == ticker.upper():
                asset = a
                break
        
        market_scope = asset.get("market_scope", "US_EU") if asset else "US_EU"
        asset_id = asset.get("asset_id", f"{ticker.upper()}.US") if asset else f"{ticker.upper()}.US"
        exchange_code = asset.get("exchange_code", "US") if asset else "US"
        
        # Build parquet file path
        base_dir = Path(__file__).parent.parent / "data" / "parquet"
        scope_dir = "us_eu" if market_scope == "US_EU" else "africa"
        
        # Create file name from asset_id (replace . with _)
        file_name = asset_id.replace(".", "_")
        
        # Try different file name formats
        possible_paths = [
            base_dir / scope_dir / "bars_daily" / f"{file_name}.parquet",  # e.g., NPN_JSE.parquet
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_{exchange_code}.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_US.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_EU.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_JSE.parquet",  # For Africa
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_NG.parquet",  # Nigeria
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_BC.parquet",  # BRVM
        ]
        
        df = None
        for path in possible_paths:
            if path.exists():
                df = pd.read_parquet(path)
                break
        
        if df is None or df.empty:
            return []  # No data available
        
        # Normalize column names (handle both lowercase and uppercase)
        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['open', 'high', 'low', 'close', 'volume', 'date']:
                col_map[col] = col_lower
        df = df.rename(columns=col_map)
        
        # Ensure date column exists and is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # Filter by period - support all periods
        end_date = datetime.now()
        period_days = {
            "1d": 1,
            "1w": 7,
            "7d": 7,
            "30d": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "5y": 365 * 5,
            "10y": 365 * 10,
        }
        days = period_days.get(period, 30)
        start_date = end_date - timedelta(days=days)
        
        # Filter data
        df_filtered = df[df.index >= start_date]
        
        # Format response
        chart_data = []
        for idx, row in df_filtered.iterrows():
            chart_data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": float(row.get("open", 0) or 0),
                "high": float(row.get("high", 0) or 0),
                "low": float(row.get("low", 0) or 0),
                "close": float(row.get("close", 0) or 0),
                "volume": int(row.get("volume", 0) or 0) if row.get("volume") is not None else None,
            })
        
        return chart_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{ticker}")
async def get_asset_details(ticker: str):
    """
    Get detailed information for a specific asset.
    """
    try:
        # Search for asset by symbol
        results = db.search_assets(query=ticker, limit=10)
        
        # Find exact match
        asset = None
        for a in results:
            if a.get("symbol", "").upper() == ticker.upper():
                asset = a
                break
        
        if not asset:
            # Try with asset_id format
            asset_id = f"{ticker.upper()}.US"
            detail = db.get_asset_detail(asset_id)
            if not detail:
                asset_id = f"{ticker.upper()}.EU"
                detail = db.get_asset_detail(asset_id)
            if detail:
                asset = detail
        
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")
        
        # Get full details
        asset_id = asset.get("asset_id")
        detail = db.get_asset_detail(asset_id) if asset_id else asset
        
        return {
            "asset_id": detail.get("asset_id"),
            "ticker": detail.get("symbol"),
            "symbol": detail.get("symbol"),
            "name": detail.get("name"),
            "asset_type": detail.get("asset_type"),
            "market_scope": detail.get("market_scope"),
            "market_code": detail.get("market_code"),
            # Scores
            "score_total": detail.get("score_total"),
            "score_value": detail.get("score_value"),
            "score_momentum": detail.get("score_momentum"),
            "score_safety": detail.get("score_safety"),
            "score_fx_risk": detail.get("score_fx_risk"),
            "score_liquidity_risk": detail.get("score_liquidity_risk"),
            # Data quality
            "confidence": detail.get("confidence"),
            "coverage": detail.get("coverage"),
            "liquidity": detail.get("liquidity"),
            "fx_risk": detail.get("fx_risk"),
            "liquidity_risk": detail.get("liquidity_risk"),
            # Technical indicators
            "rsi": detail.get("rsi"),
            "vol_annual": detail.get("vol_annual"),
            "max_drawdown": detail.get("max_drawdown"),
            "sma200": detail.get("sma200"),
            "last_price": detail.get("last_price"),
            "zscore": detail.get("zscore"),
            "state_label": detail.get("state_label"),
            # Metadata
            "sector": detail.get("sector"),
            "industry": detail.get("industry"),
            "currency": detail.get("currency"),
            "updated_at": detail.get("updated_at"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Metrics Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/metrics/counts")
async def get_scope_counts():
    """
    Get asset counts by market scope.
    """
    try:
        counts = db.count_by_scope()
        return {
            "US_EU": counts.get("US_EU", 0),
            "AFRICA": counts.get("AFRICA", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/stats")
async def get_stats(market_scope: Optional[str] = Query(None)):
    """
    Get comprehensive statistics.
    """
    try:
        stats = db.get_stats(market_scope=market_scope)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/landing")
async def get_landing_metrics(market_scope: str = Query("US_EU")):
    """
    Get metrics for landing page.
    """
    try:
        metrics = db.get_landing_metrics(market_scope=market_scope)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Watchlist Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/watchlist")
async def get_watchlist(
    user_id: str = Query("default"),
    market_scope: Optional[str] = Query(None),
):
    """
    Get user's watchlist.
    """
    try:
        items = db.list_watchlist(user_id=user_id, market_scope=market_scope)
        
        formatted = []
        for item in items:
            formatted.append({
                "ticker": item.get("ticker"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "asset_type": item.get("asset_type"),
                "asset_id": item.get("asset_id"),
                "market_scope": item.get("market_scope"),
                "score_total": item.get("score_total"),
                "score_value": item.get("score_value"),
                "score_momentum": item.get("score_momentum"),
                "score_safety": item.get("score_safety"),
                "confidence": item.get("confidence"),
                "last_price": item.get("last_price"),
                "notes": item.get("notes"),
                "added_at": item.get("added_at"),
            })
        
        return formatted
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class WatchlistAddRequest(BaseModel):
    ticker: str
    market_scope: Optional[str] = "US_EU"
    notes: Optional[str] = None


@router.post("/watchlist")
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Query("default"),
):
    """
    Add asset to watchlist.
    """
    try:
        success = db.add_watchlist(
            ticker=request.ticker,
            user_id=user_id,
            notes=request.notes,
            market_scope=request.market_scope
        )
        
        if success:
            return {"status": "success", "ticker": request.ticker}
        else:
            raise HTTPException(status_code=400, detail="Failed to add to watchlist")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    user_id: str = Query("default"),
):
    """
    Remove asset from watchlist.
    """
    try:
        success = db.remove_watchlist(ticker=ticker, user_id=user_id)
        
        if success:
            return {"status": "success", "ticker": ticker}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove from watchlist")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist/check/{ticker}")
async def check_in_watchlist(
    ticker: str,
    user_id: str = Query("default"),
):
    """
    Check if asset is in watchlist.
    """
    try:
        in_watchlist = db.is_in_watchlist(ticker=ticker, user_id=user_id)
        return {"in_watchlist": in_watchlist}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Asset Types Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/asset-types")
async def get_asset_types(market_scope: str = Query("US_EU")):
    """
    Get available asset types for a scope.
    """
    try:
        types = db.get_asset_types_for_scope(market_scope=market_scope)
        return {"types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
