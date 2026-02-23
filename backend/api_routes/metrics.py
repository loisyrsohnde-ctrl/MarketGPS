"""
Metrics endpoints: counts, stats, landing, universe metrics.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from .shared import db, ASSET_QUERY_AVAILABLE, AFRICA_REGIONS

router = APIRouter()


@router.get("/metrics/counts")
async def get_scope_counts():
    """Get asset counts by market scope."""
    try:
        counts = db.count_by_scope()
        return {"US_EU": counts.get("US_EU", 0), "AFRICA": counts.get("AFRICA", 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/stats")
async def get_stats(market_scope: Optional[str] = Query(None)):
    """Get comprehensive statistics."""
    try:
        stats = db.get_stats(market_scope=market_scope)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/landing")
async def get_landing_metrics(market_scope: str = Query("US_EU")):
    """Get metrics for landing page."""
    try:
        metrics = db.get_landing_metrics(market_scope=market_scope)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/asset-type-counts")
async def get_asset_type_counts(market_scope: Optional[str] = Query(None)):
    """Get asset counts and average scores by asset type."""
    try:
        with db._get_connection() as conn:
            scope_filter = ""
            params = []
            if market_scope:
                scope_filter = "WHERE u.market_scope = ?"
                params.append(market_scope)

            query = f"""
                SELECT
                    u.asset_type,
                    COUNT(*) as count,
                    ROUND(AVG(sl.score_total), 1) as avg_score
                FROM universe u
                LEFT JOIN scores_latest sl ON u.asset_id = sl.asset_id
                {scope_filter}
                GROUP BY u.asset_type
            """
            rows = conn.execute(query, params).fetchall()

            result = {}
            for row in rows:
                asset_type = row[0] or "UNKNOWN"
                result[asset_type] = {"count": row[1], "avgScore": row[2]}
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/counts/v2")
async def get_counts_v2(
    market_scope: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    only_scored: Optional[bool] = Query(None),
):
    """Get dynamic asset counts with flexible filtering."""
    try:
        with db._get_connection() as conn:
            conditions = ["u.active = 1"]
            params = []

            if market_scope:
                conditions.append("u.market_scope = ?")
                params.append(market_scope)

            if asset_type:
                conditions.append("u.asset_type = ?")
                params.append(asset_type)

            if country and ASSET_QUERY_AVAILABLE:
                from asset_query import AFRICA_COUNTRY_EXCHANGES
                exchanges = AFRICA_COUNTRY_EXCHANGES.get(country, [])
                if exchanges:
                    exchange_conditions = []
                    for exch in exchanges:
                        exchange_conditions.append("u.asset_id LIKE ?")
                        params.append(f"{exch}:%")
                    if exchange_conditions:
                        conditions.append(f"({' OR '.join(exchange_conditions)})")

            if region and not country and ASSET_QUERY_AVAILABLE:
                region_countries = AFRICA_REGIONS.get(region, [])
                if region_countries:
                    from asset_query import AFRICA_COUNTRY_EXCHANGES
                    exchange_conditions = []
                    for country_code in region_countries:
                        exchanges = AFRICA_COUNTRY_EXCHANGES.get(country_code, [])
                        for exch in exchanges:
                            exchange_conditions.append("u.asset_id LIKE ?")
                            params.append(f"{exch}:%")
                    if exchange_conditions:
                        conditions.append(f"({' OR '.join(exchange_conditions)})")

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            count_query = f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN sl.score_total IS NOT NULL THEN 1 ELSE 0 END) as scored,
                    SUM(CASE WHEN sl.score_total IS NULL THEN 1 ELSE 0 END) as unscored
                FROM universe u
                LEFT JOIN scores_latest sl ON u.asset_id = sl.asset_id
                {where_clause}
            """
            row = conn.execute(count_query, params).fetchone()
            total = row[0] or 0
            scored = row[1] or 0
            unscored = row[2] or 0

            if only_scored is True:
                main_count = scored
            elif only_scored is False:
                main_count = unscored
            else:
                main_count = total

            result = {
                "total": main_count,
                "breakdown": {"scored": scored, "unscored": unscored},
                "filters": {
                    "market_scope": market_scope, "asset_type": asset_type,
                    "country": country, "region": region, "only_scored": only_scored,
                },
            }

            if not market_scope:
                scope_query = f"""
                    SELECT u.market_scope, COUNT(*) as total,
                        SUM(CASE WHEN sl.score_total IS NOT NULL THEN 1 ELSE 0 END) as scored
                    FROM universe u
                    LEFT JOIN scores_latest sl ON u.asset_id = sl.asset_id
                    {where_clause}
                    GROUP BY u.market_scope
                """
                scope_rows = conn.execute(scope_query, params).fetchall()
                result["by_scope"] = {}
                for srow in scope_rows:
                    scope_name = srow[0] or "UNKNOWN"
                    result["by_scope"][scope_name] = {"total": srow[1], "scored": srow[2]}

            if not asset_type:
                type_query = f"""
                    SELECT u.asset_type, COUNT(*) as total,
                        SUM(CASE WHEN sl.score_total IS NOT NULL THEN 1 ELSE 0 END) as scored,
                        ROUND(AVG(sl.score_total), 1) as avg_score
                    FROM universe u
                    LEFT JOIN scores_latest sl ON u.asset_id = sl.asset_id
                    {where_clause}
                    GROUP BY u.asset_type
                    ORDER BY total DESC
                """
                type_rows = conn.execute(type_query, params).fetchall()
                result["by_asset_type"] = {}
                for trow in type_rows:
                    type_name = trow[0] or "UNKNOWN"
                    result["by_asset_type"][type_name] = {
                        "total": trow[1], "scored": trow[2], "avgScore": trow[3],
                    }

            if market_scope == "AFRICA" and not region and ASSET_QUERY_AVAILABLE:
                result["by_region"] = {}
                for region_name, region_countries in AFRICA_REGIONS.items():
                    from asset_query import AFRICA_COUNTRY_EXCHANGES
                    exchange_patterns = []
                    region_params = list(params)
                    for country_code in region_countries:
                        exchanges = AFRICA_COUNTRY_EXCHANGES.get(country_code, [])
                        for exch in exchanges:
                            exchange_patterns.append("u.asset_id LIKE ?")
                            region_params.append(f"{exch}:%")

                    if exchange_patterns:
                        region_where = where_clause
                        if region_where:
                            region_where += f" AND ({' OR '.join(exchange_patterns)})"
                        else:
                            region_where = f"WHERE ({' OR '.join(exchange_patterns)})"

                        region_query = f"""
                            SELECT COUNT(*) as total,
                                SUM(CASE WHEN sl.score_total IS NOT NULL THEN 1 ELSE 0 END) as scored
                            FROM universe u
                            LEFT JOIN scores_latest sl ON u.asset_id = sl.asset_id
                            {region_where}
                        """
                        rrow = conn.execute(region_query, region_params).fetchone()
                        if rrow and rrow[0] > 0:
                            result["by_region"][region_name] = {"total": rrow[0], "scored": rrow[1] or 0}

            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scope-counts")
async def get_scope_counts_alias():
    """Alias for /metrics/counts."""
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
