"""
MarketGPS - API Routes for Assets/Scores/Watchlist
Exposes SQLite data to the Next.js frontend.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path as FilePath
from fastapi import APIRouter, Query, HTTPException, Depends, Header
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

# Add parent directory to path to import from storage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteStore
from security import get_user_id_from_request
from storage.parquet_store import ParquetStore

# Initialize SQLite store
db = SQLiteStore()

# Initialize Parquet stores for each scope
parquet_us_eu = ParquetStore(market_scope="US_EU")
parquet_africa = ParquetStore(market_scope="AFRICA")

# Create router
router = APIRouter(prefix="/api", tags=["Assets"])


def _resolve_user_id(user_id: Optional[str], authorization: Optional[str]) -> str:
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
    # Long-term institutional score (ADD-ON)
    lt_score: Optional[float] = None
    lt_confidence: Optional[float] = None
    # Institutional Guard fields (ADD-ON v2.0)
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
    # Institutional Guard fields (ADD-ON v2.0)
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
    # Long-term institutional score (ADD-ON)
    lt_score: Optional[float] = None
    lt_confidence: Optional[float] = None
    lt_breakdown: Optional[dict] = None


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
                # Institutional Guard fields (ADD-ON - backward compatible)
                "score_institutional": a.get("score_institutional"),
                "liquidity_tier": a.get("liquidity_tier"),
                "liquidity_flag": bool(a.get("liquidity_flag")) if a.get("liquidity_flag") is not None else None,
                "data_quality_flag": bool(a.get("data_quality_flag")) if a.get("data_quality_flag") is not None else None,
                "data_quality_score": a.get("data_quality_score"),
                "min_recommended_horizon_years": a.get("min_recommended_horizon_years"),
                "adv_usd": a.get("adv_usd"),
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


# ═══════════════════════════════════════════════════════════════════════════
# NEW ENDPOINT: Institutional Ranking (ADD-ON v2.0)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/assets/top-scored-institutional")
async def get_top_scored_institutional(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    market_scope: Optional[str] = Query("US_EU", description="US_EU or AFRICA"),
    asset_type: Optional[str] = Query(None, description="ETF, EQUITY"),
    min_liquidity_tier: Optional[str] = Query(None, description="A, B, C - minimum tier"),
    exclude_flagged: bool = Query(False, description="Exclude assets with liquidity/quality flags"),
    min_horizon_years: Optional[int] = Query(None, ge=1, le=20, description="Min recommended horizon"),
):
    """
    Get top scored assets ranked by score_institutional (liquidity & quality adjusted).
    
    ADD-ON endpoint - does not replace /assets/top-scored.
    
    Features:
    - Ranks by score_institutional instead of score_total
    - Filter by minimum liquidity tier (A = best, D = worst)
    - Exclude flagged assets (liquidity or data quality issues)
    - Filter by minimum recommended investment horizon
    """
    try:
        scope = market_scope or "US_EU"
        
        # Build query with institutional columns
        with db._get_connection() as conn:
            # Base query
            query = """
                SELECT 
                    u.asset_id,
                    u.symbol,
                    u.name,
                    u.asset_type,
                    u.market_scope,
                    u.market_code,
                    u.sector,
                    u.industry,
                    s.score_total,
                    s.score_value,
                    s.score_momentum,
                    s.score_safety,
                    s.confidence,
                    s.score_institutional,
                    s.liquidity_tier,
                    s.liquidity_flag,
                    s.liquidity_penalty,
                    s.data_quality_flag,
                    s.data_quality_score,
                    s.stale_price_flag,
                    s.min_recommended_horizon_years,
                    s.institutional_explanation,
                    s.adv_usd,
                    g.coverage,
                    g.liquidity
                FROM universe u
                LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
                LEFT JOIN gating_status g ON u.asset_id = g.asset_id
                WHERE u.market_scope = ?
                  AND u.active = 1
                  AND s.score_institutional IS NOT NULL
            """
            params = [scope]
            
            # Asset type filter
            if asset_type:
                query += " AND u.asset_type = ?"
                params.append(asset_type.upper())
            
            # Liquidity tier filter
            if min_liquidity_tier:
                tier_order = {"A": 1, "B": 2, "C": 3, "D": 4}
                min_tier_value = tier_order.get(min_liquidity_tier.upper(), 4)
                valid_tiers = [t for t, v in tier_order.items() if v <= min_tier_value]
                placeholders = ",".join(["?" for _ in valid_tiers])
                query += f" AND s.liquidity_tier IN ({placeholders})"
                params.extend(valid_tiers)
            
            # Exclude flagged assets
            if exclude_flagged:
                query += " AND (s.liquidity_flag = 0 OR s.liquidity_flag IS NULL)"
                query += " AND (s.data_quality_flag = 0 OR s.data_quality_flag IS NULL)"
            
            # Min horizon filter
            if min_horizon_years:
                query += " AND s.min_recommended_horizon_years >= ?"
                params.append(min_horizon_years)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query})"
            total = conn.execute(count_query, params).fetchone()["total"]
            
            # Add ordering and pagination
            query += " ORDER BY s.score_institutional DESC NULLS LAST"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = conn.execute(query, params).fetchall()
        
        # Format response
        formatted = []
        for row in rows:
            r = dict(row)
            formatted.append({
                "asset_id": r.get("asset_id"),
                "ticker": r.get("symbol"),
                "symbol": r.get("symbol"),
                "name": r.get("name"),
                "asset_type": r.get("asset_type"),
                "market_scope": r.get("market_scope"),
                "market_code": r.get("market_code"),
                "sector": r.get("sector"),
                "industry": r.get("industry"),
                # Original scores
                "score_total": r.get("score_total"),
                "score_value": r.get("score_value"),
                "score_momentum": r.get("score_momentum"),
                "score_safety": r.get("score_safety"),
                "confidence": r.get("confidence"),
                "coverage": r.get("coverage"),
                "liquidity": r.get("liquidity"),
                # Institutional Guard fields
                "score_institutional": r.get("score_institutional"),
                "liquidity_tier": r.get("liquidity_tier"),
                "liquidity_flag": bool(r.get("liquidity_flag")) if r.get("liquidity_flag") is not None else None,
                "liquidity_penalty": r.get("liquidity_penalty"),
                "data_quality_flag": bool(r.get("data_quality_flag")) if r.get("data_quality_flag") is not None else None,
                "data_quality_score": r.get("data_quality_score"),
                "stale_price_flag": bool(r.get("stale_price_flag")) if r.get("stale_price_flag") is not None else None,
                "min_recommended_horizon_years": r.get("min_recommended_horizon_years"),
                "institutional_explanation": r.get("institutional_explanation"),
                "adv_usd": r.get("adv_usd"),
            })
        
        return {
            "data": formatted,
            "total": total,
            "page": (offset // limit) + 1,
            "page_size": limit,
            "total_pages": max(1, (total + limit - 1) // limit) if limit > 0 else 1,
            "ranking_mode": "institutional",
            "filters_applied": {
                "market_scope": scope,
                "asset_type": asset_type,
                "min_liquidity_tier": min_liquidity_tier,
                "exclude_flagged": exclude_flagged,
                "min_horizon_years": min_horizon_years,
            }
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
    country: Optional[str] = Query(None, description="Country code for Africa filtering (e.g., ZA, NG)"),
    region: Optional[str] = Query(None, description="Region for Africa filtering (e.g., SOUTHERN, WEST)"),
    query: Optional[str] = Query(None),
    only_scored: bool = Query(True),
    sort_by: str = Query("score_total"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    Paginated explorer for all assets.
    Supports Africa filtering by country or region.
    """
    try:
        offset = (page - 1) * page_size
        
        results, total = db.search_universe(
            market_scope=market_scope,
            asset_type=asset_type,
            country=country,
            region=region,
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
    Supports both symbol (BTC) and asset_id (BTC.CRYPTO) formats.
    """
    try:
        asset = None
        
        # If ticker contains a dot, it might be a full asset_id - try it directly first
        if "." in ticker:
            asset = db.get_asset_detail(ticker.upper())
            if not asset:
                # Maybe the format is wrong, extract symbol and try search
                symbol_part = ticker.split(".")[0]
                results = db.search_assets(query=symbol_part, limit=10)
                for a in results:
                    if a.get("symbol", "").upper() == symbol_part.upper():
                        asset = a
                        break
        
        # If no asset yet, search by symbol
        if not asset:
            results = db.search_assets(query=ticker, limit=10)
            
            # Find exact match
            for a in results:
                if a.get("symbol", "").upper() == ticker.upper():
                    asset = a
                    break
        
        # If still no asset, try with asset_id format for various exchanges
        if not asset:
            suffixes = [
                "US", "EU", "CRYPTO", "FX", "CMDTY", "FUTURE", "OPTION", "INDEX",  # Global
                "JSE", "NGX", "BRVM", "EGX", "NSE", "CSE", "GSE", "BVMT",           # Africa
                "CME", "COMEX", "CBOT", "NYMEX", "CBOE"                              # Derivatives
            ]
            
            for suffix in suffixes:
                asset_id = f"{ticker.upper()}.{suffix}"
                detail = db.get_asset_detail(asset_id)
                if detail:
                    asset = detail
                    break
        
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
            # Institutional Guard fields (ADD-ON v2.0)
            "score_institutional": detail.get("score_institutional"),
            "liquidity_tier": detail.get("liquidity_tier"),
            "liquidity_flag": bool(detail.get("liquidity_flag")) if detail.get("liquidity_flag") is not None else None,
            "liquidity_penalty": detail.get("liquidity_penalty"),
            "data_quality_flag": bool(detail.get("data_quality_flag")) if detail.get("data_quality_flag") is not None else None,
            "data_quality_score": detail.get("data_quality_score"),
            "stale_price_flag": bool(detail.get("stale_price_flag")) if detail.get("stale_price_flag") is not None else None,
            "min_recommended_horizon_years": detail.get("min_recommended_horizon_years"),
            "institutional_explanation": detail.get("institutional_explanation"),
            "adv_usd": detail.get("adv_usd"),
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


@router.get("/metrics/asset-type-counts")
async def get_asset_type_counts(market_scope: Optional[str] = Query(None)):
    """
    Get asset counts and average scores by asset type.
    Used by the Markets page to show breakdown by asset type.
    """
    try:
        with db._get_connection() as conn:
            scope_filter = ""
            params = []
            if market_scope:
                scope_filter = "WHERE u.market_scope = ?"
                params.append(market_scope)
            
            # Join with rotation_state to get scores (score_total is in rotation_state, not universe)
            query = f"""
                SELECT 
                    u.asset_type,
                    COUNT(*) as count,
                    ROUND(AVG(rs.score_total), 1) as avg_score
                FROM universe u
                LEFT JOIN rotation_state rs ON u.asset_id = rs.asset_id
                {scope_filter}
                GROUP BY u.asset_type
            """
            rows = conn.execute(query, params).fetchall()
            
            result = {}
            for row in rows:
                asset_type = row[0] or "UNKNOWN"
                result[asset_type] = {
                    "count": row[1],
                    "avgScore": row[2]
                }
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Watchlist Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/watchlist")
async def get_watchlist(
    user_id: str = Query("default"),
    market_scope: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Get user's watchlist.
    """
    try:
        resolved_user_id = _resolve_user_id(user_id, authorization)
        items = db.list_watchlist(user_id=resolved_user_id, market_scope=market_scope)
        
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
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Add asset to watchlist.
    """
    try:
        resolved_user_id = _resolve_user_id(user_id, authorization)
        success = db.add_watchlist(
            ticker=request.ticker,
            user_id=resolved_user_id,
            notes=request.notes,
            market_scope=request.market_scope
        )
        
        if success:
            # Create notification for watchlist addition
            try:
                from user_routes import create_notification
                create_notification(
                    user_id=resolved_user_id,
                    type="info",
                    title="Actif ajouté à la watchlist",
                    description=f"{request.ticker} a été ajouté à votre liste de surveillance"
                )
            except Exception:
                pass  # Don't fail the main operation if notification fails
            
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
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Remove asset from watchlist.
    """
    try:
        resolved_user_id = _resolve_user_id(user_id, authorization)
        success = db.remove_watchlist(ticker=ticker, user_id=resolved_user_id)
        
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
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Check if asset is in watchlist.
    """
    try:
        resolved_user_id = _resolve_user_id(user_id, authorization)
        in_watchlist = db.is_in_watchlist(ticker=ticker, user_id=resolved_user_id)
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


# ═══════════════════════════════════════════════════════════════════════════
# Logo Endpoints
# ═══════════════════════════════════════════════════════════════════════════

# Path to logos directory (relative to project root)
LOGOS_DIR = FilePath(__file__).parent.parent / "data" / "logos"

# 1x1 transparent PNG placeholder (base64 decoded)
PLACEHOLDER_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
    0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
    0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
])


@router.get("/logos/{ticker}")
async def get_logo(ticker: str):
    """
    Serve asset logo from data/logos/ directory.
    Returns a transparent placeholder if logo doesn't exist.
    """
    # Normalize ticker (uppercase, remove .png extension if present)
    clean_ticker = ticker.upper().replace(".PNG", "").replace(".png", "")
    
    # Try to find the logo file
    logo_path = LOGOS_DIR / f"{clean_ticker}.png"
    
    if logo_path.exists() and logo_path.is_file():
        return FileResponse(
            path=str(logo_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache 24h
        )
    
    # Return transparent placeholder if logo doesn't exist
    return Response(
        content=PLACEHOLDER_PNG,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}  # Cache 1h for placeholders
    )


# ═══════════════════════════════════════════════════════════════════════════
# On-Demand Scoring Endpoints (NEW - Hybrid Architecture)
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/assets/{ticker}/score")
async def calculate_score_on_demand(
    ticker: str,
    force: bool = Query(False, description="Force recalculation even if cached"),
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Calculate score for an asset on-demand.
    """
    from scoring_service import (
        OnDemandScoringService,
        QuotaExceededError,
        AssetNotFoundError,
        ScoringError
    )
    
    try:
        resolved_user_id = _resolve_user_id(user_id, authorization)
        service = OnDemandScoringService(store=db)
        
        result = service.calculate_score(
            ticker=ticker,
            user_id=resolved_user_id,
            force=force
        )
        
        return result
        
    except QuotaExceededError as e:
        raise HTTPException(status_code=403, detail={"error": "quota_exceeded", "message": str(e)})
    except AssetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ScoringError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/quota")
async def get_user_quota(
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Get current quota status for user."""
    from scoring_service import OnDemandScoringService
    
    try:
        resolved_user_id = _resolve_user_id(user_id, authorization)
        service = OnDemandScoringService(store=db)
        quota = service.get_quota_status(resolved_user_id)
        return quota
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scope-counts")
async def get_scope_counts_alias():
    """Alias for /metrics/counts - returns asset counts by market scope."""
    try:
        counts = db.count_by_scope()
        return {"US_EU": counts.get("US_EU", 0), "AFRICA": counts.get("AFRICA", 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/universe")
async def get_universe_metrics():
    """Get comprehensive universe metrics."""
    try:
        with db._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) as count FROM universe WHERE active = 1").fetchone()["count"]
            scored = conn.execute("SELECT COUNT(*) as count FROM scores_latest WHERE score_total IS NOT NULL").fetchone()["count"]
            tier1 = conn.execute("SELECT COUNT(*) as count FROM universe WHERE tier = 1 AND active = 1").fetchone()["count"]
            markets = conn.execute("SELECT COUNT(DISTINCT market_code) as count FROM universe WHERE active = 1").fetchone()["count"]
            exchanges = conn.execute("SELECT COUNT(DISTINCT exchange_code) as count FROM universe WHERE active = 1").fetchone()["count"]
            by_scope = {row["market_scope"]: row["count"] for row in conn.execute("SELECT market_scope, COUNT(*) as count FROM universe WHERE active = 1 GROUP BY market_scope").fetchall()}
            by_type = {row["asset_type"]: row["count"] for row in conn.execute("SELECT asset_type, COUNT(*) as count FROM universe WHERE active = 1 GROUP BY asset_type").fetchall()}
        
        return {
            "total_assets": total,
            "scored_assets": scored,
            "tier1_assets": tier1,
            "markets_covered": markets,
            "exchanges_covered": exchanges,
            "by_scope": by_scope,
            "by_type": by_type,
            "scoring_coverage": round(scored / total * 100, 1) if total > 0 else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
