"""
Asset Repository - Manages asset (universe) data.
"""
from typing import Optional, List, Dict, Tuple

from core.models import Asset, AssetType
from storage.base_repository import BaseRepository, MarketScope, VALID_SCOPES
from core.config import get_logger

logger = get_logger(__name__)


class AssetRepository(BaseRepository):
    """Repository for asset operations."""

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

    def upsert_gating(self, gating, market_scope: MarketScope = "US_EU"):
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

    def get_gating(self, asset_id: str):
        """Get gating status for an asset."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM gating_status WHERE asset_id = ?", (asset_id,)
            ).fetchone()
            if row:
                from core.models import GatingStatus
                return GatingStatus.from_row(dict(row))
        return None

    def get_eligible_assets(self, market_scope: MarketScope = "US_EU") -> List[str]:
        """Get list of eligible asset IDs for a scope."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT g.asset_id FROM gating_status g
                JOIN universe u ON g.asset_id = u.asset_id
                WHERE g.eligible = 1 AND u.market_scope = ?
            """, (market_scope,)).fetchall()
            return [row["asset_id"] for row in rows]
