"""
Asset endpoints: top-scored, search, explorer, chart, details, logos, asset-types.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse, Response

from .shared import db, LOGOS_DIR, PLACEHOLDER_PNG

router = APIRouter()


@router.get("/assets/top-scored")
async def get_top_scored(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    market_scope: Optional[str] = Query(None, description="US_EU or AFRICA"),
    asset_type: Optional[str] = Query(None, description="ETF, EQUITY, FX, BOND"),
    market_filter: Optional[str] = Query(None, description="ALL, US, EU, AFRICA"),
    only_scored: bool = Query(True, description="Only return assets with scores"),
):
    """Get top scored assets with optional filters."""
    try:
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

        scope = scope or "US_EU"

        show_only_scored = only_scored
        if market_filter in ("EU", "AFRICA"):
            show_only_scored = False

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
    """Get top scored assets ranked by score_institutional."""
    try:
        scope = market_scope or "US_EU"

        with db._get_connection() as conn:
            query = """
                SELECT
                    u.asset_id, u.symbol, u.name, u.asset_type,
                    u.market_scope, u.market_code, u.sector, u.industry,
                    s.score_total, s.score_value, s.score_momentum, s.score_safety,
                    s.confidence, s.score_institutional, s.liquidity_tier,
                    s.liquidity_flag, s.liquidity_penalty, s.data_quality_flag,
                    s.data_quality_score, s.stale_price_flag,
                    s.min_recommended_horizon_years, s.institutional_explanation,
                    s.adv_usd, g.coverage, g.liquidity
                FROM universe u
                LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
                LEFT JOIN gating_status g ON u.asset_id = g.asset_id
                WHERE u.market_scope = ?
                  AND u.active = 1
                  AND s.score_institutional IS NOT NULL
            """
            params = [scope]

            if asset_type:
                query += " AND u.asset_type = ?"
                params.append(asset_type.upper())

            if min_liquidity_tier:
                tier_order = {"A": 1, "B": 2, "C": 3, "D": 4}
                min_tier_value = tier_order.get(min_liquidity_tier.upper(), 4)
                valid_tiers = [t for t, v in tier_order.items() if v <= min_tier_value]
                placeholders = ",".join(["?" for _ in valid_tiers])
                query += f" AND s.liquidity_tier IN ({placeholders})"
                params.extend(valid_tiers)

            if exclude_flagged:
                query += " AND (s.liquidity_flag = 0 OR s.liquidity_flag IS NULL)"
                query += " AND (s.data_quality_flag = 0 OR s.data_quality_flag IS NULL)"

            if min_horizon_years:
                query += " AND s.min_recommended_horizon_years >= ?"
                params.append(min_horizon_years)

            count_query = f"SELECT COUNT(*) as total FROM ({query})"
            total = conn.execute(count_query, params).fetchone()["total"]

            query += " ORDER BY s.score_institutional DESC NULLS LAST"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()

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
                "score_total": r.get("score_total"),
                "score_value": r.get("score_value"),
                "score_momentum": r.get("score_momentum"),
                "score_safety": r.get("score_safety"),
                "confidence": r.get("confidence"),
                "coverage": r.get("coverage"),
                "liquidity": r.get("liquidity"),
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
    """Search assets by symbol or name."""
    try:
        results = db.search_assets(query=q, market_scope=market_scope, limit=limit)

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
    country: Optional[str] = Query(None, description="Country code for Africa filtering"),
    region: Optional[str] = Query(None, description="Region for Africa filtering"),
    query: Optional[str] = Query(None),
    only_scored: bool = Query(True),
    sort_by: str = Query("score_total"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Paginated explorer for all assets."""
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
    """Get historical price data for charting."""
    import pandas as pd
    from pathlib import Path

    try:
        results = db.search_assets(query=ticker, limit=10)
        asset = None
        for a in results:
            if a.get("symbol", "").upper() == ticker.upper():
                asset = a
                break

        market_scope = asset.get("market_scope", "US_EU") if asset else "US_EU"
        asset_id = asset.get("asset_id", f"{ticker.upper()}.US") if asset else f"{ticker.upper()}.US"
        exchange_code = asset.get("exchange_code", "US") if asset else "US"

        base_dir = Path(__file__).parent.parent.parent / "data" / "parquet"
        scope_dir = "us_eu" if market_scope == "US_EU" else "africa"
        file_name = asset_id.replace(".", "_")

        possible_paths = [
            base_dir / scope_dir / "bars_daily" / f"{file_name}.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_{exchange_code}.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_US.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_EU.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_JSE.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_NG.parquet",
            base_dir / scope_dir / "bars_daily" / f"{ticker.upper()}_BC.parquet",
        ]

        df = None
        for path in possible_paths:
            if path.exists():
                df = pd.read_parquet(path)
                break

        if df is None or df.empty:
            return []

        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['open', 'high', 'low', 'close', 'volume', 'date']:
                col_map[col] = col_lower
        df = df.rename(columns=col_map)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

        end_date = datetime.now()
        period_days = {
            "1d": 1, "1w": 7, "7d": 7, "30d": 30,
            "3m": 90, "6m": 180, "1y": 365, "5y": 365 * 5, "10y": 365 * 10,
        }
        days = period_days.get(period, 30)
        start_date = end_date - timedelta(days=days)

        df_filtered = df[df.index >= start_date]

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
    """Get detailed information for a specific asset."""
    try:
        asset = None

        if "." in ticker:
            asset = db.get_asset_detail(ticker.upper())
            if not asset:
                symbol_part = ticker.split(".")[0]
                results = db.search_assets(query=symbol_part, limit=10)
                for a in results:
                    if a.get("symbol", "").upper() == symbol_part.upper():
                        asset = a
                        break

        if not asset:
            results = db.search_assets(query=ticker, limit=10)
            for a in results:
                if a.get("symbol", "").upper() == ticker.upper():
                    asset = a
                    break

        if not asset:
            suffixes = [
                "US", "EU", "CRYPTO", "FX", "CMDTY", "FUTURE", "OPTION", "INDEX",
                "JSE", "NGX", "BRVM", "EGX", "NSE", "CSE", "GSE", "BVMT",
                "CME", "COMEX", "CBOT", "NYMEX", "CBOE"
            ]
            for suffix in suffixes:
                asset_id = f"{ticker.upper()}.{suffix}"
                detail = db.get_asset_detail(asset_id)
                if detail:
                    asset = detail
                    break

        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

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
            "score_total": detail.get("score_total"),
            "score_value": detail.get("score_value"),
            "score_momentum": detail.get("score_momentum"),
            "score_safety": detail.get("score_safety"),
            "score_fx_risk": detail.get("score_fx_risk"),
            "score_liquidity_risk": detail.get("score_liquidity_risk"),
            "confidence": detail.get("confidence"),
            "coverage": detail.get("coverage"),
            "liquidity": detail.get("liquidity"),
            "fx_risk": detail.get("fx_risk"),
            "liquidity_risk": detail.get("liquidity_risk"),
            "rsi": detail.get("rsi"),
            "vol_annual": detail.get("vol_annual"),
            "max_drawdown": detail.get("max_drawdown"),
            "sma200": detail.get("sma200"),
            "last_price": detail.get("last_price"),
            "zscore": detail.get("zscore"),
            "state_label": detail.get("state_label"),
            "sector": detail.get("sector"),
            "industry": detail.get("industry"),
            "currency": detail.get("currency"),
            "updated_at": detail.get("updated_at"),
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


@router.get("/asset-types")
async def get_asset_types(market_scope: str = Query("US_EU")):
    """Get available asset types for a scope."""
    try:
        types = db.get_asset_types_for_scope(market_scope=market_scope)
        return {"types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logos/{ticker}")
async def get_logo(ticker: str):
    """Serve asset logo from data/logos/ directory."""
    clean_ticker = ticker.upper().replace(".PNG", "").replace(".png", "")
    logo_path = LOGOS_DIR / f"{clean_ticker}.png"

    if logo_path.exists() and logo_path.is_file():
        return FileResponse(
            path=str(logo_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}
        )

    return Response(
        content=PLACEHOLDER_PNG,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )
