"""
Explorer Repository - Manages universe search, landing page metrics, and long-term scoring.
"""
from typing import Optional, List, Dict, Tuple

from storage.base_repository import BaseRepository, MarketScope, VALID_SCOPES
from core.config import get_logger

logger = get_logger(__name__)


class ExplorerRepository(BaseRepository):
    """Repository for explorer/search operations and long-term scoring."""

    # ═══════════════════════════════════════════════════════════════════════════
    # LANDING PAGE METRICS (NEW v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_landing_metrics(self, market_scope: str = "US_EU") -> Dict:
        """Get metrics for landing page display."""
        with self._get_connection() as conn:
            metrics = {}

            # Total assets
            metrics["total_assets"] = conn.execute(
                "SELECT COUNT(*) FROM universe WHERE active = 1 AND market_scope = ?",
                (market_scope,)
            ).fetchone()[0]

            # Scored assets
            metrics["total_scored"] = conn.execute("""
                SELECT COUNT(*) FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                WHERE s.score_total IS NOT NULL AND u.market_scope = ?
            """, (market_scope,)).fetchone()[0]

            # Last refresh
            row = conn.execute("""
                SELECT MAX(updated_at) as last_refresh FROM scores_latest
            """).fetchone()
            metrics["last_refresh"] = row["last_refresh"] if row else None

            # Top example asset (best score)
            row = conn.execute("""
                SELECT u.symbol, u.name, s.score_total, s.score_value,
                       s.score_momentum, s.score_safety, s.confidence,
                       g.coverage, g.liquidity, g.fx_risk
                FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                LEFT JOIN gating_status g ON s.asset_id = g.asset_id
                WHERE s.score_total IS NOT NULL AND u.market_scope = ?
                ORDER BY s.score_total DESC
                LIMIT 1
            """, (market_scope,)).fetchone()

            if row:
                metrics["top_asset"] = dict(row)
            else:
                metrics["top_asset"] = None

            return metrics

    # ═══════════════════════════════════════════════════════════════════════════
    # UNIVERSE SEARCH (ENHANCED for Explorer v12)
    # ═══════════════════════════════════════════════════════════════════════════

    # Africa region to country mapping
    AFRICA_REGIONS = {
        "SOUTHERN": ["ZA", "BW", "ZW", "ZM", "MW", "MZ", "NA", "LS", "SZ"],
        "WEST": ["NG", "GH", "CI", "SN", "ML", "BF", "NE", "BJ", "TG"],
        "NORTH": ["MA", "DZ", "TN", "EG", "LY"],
        "EAST": ["KE", "TZ", "UG", "RW", "ET", "MU"],
        "CENTRAL": ["CM", "CD", "CG", "GA", "CF", "TD"],
    }

    # Country to exchange mapping for Africa
    AFRICA_COUNTRY_EXCHANGES = {
        "ZA": ["JSE", "JO"],
        "NG": ["NGX", "NG"],
        "EG": ["EGX", "CA"],
        "MA": ["CSE", "BC"],
        "KE": ["NSE"],
        "CI": ["BRVM"],
        "GH": ["GSE"],
        "TN": ["BVMT"],
        "MU": ["SEM"],
        "BW": ["BSE"],
    }

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
        """
        Search universe with filters for Explorer page.
        Returns (results, total_count).
        Supports Africa filtering by country or region.
        """
        conditions = ["u.active = 1"]
        params = []

        # Market scope
        if market_scope:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        # Market code (US, EU, ZA, etc.)
        if market_code and market_code not in ("ALL", "Tous"):
            conditions.append("u.market_code = ?")
            params.append(market_code)

        # Country filter (for Africa) - filter by exchange codes
        if country and country in self.AFRICA_COUNTRY_EXCHANGES:
            exchanges = self.AFRICA_COUNTRY_EXCHANGES[country]
            placeholders = ", ".join(["?" for _ in exchanges])
            # Match asset_id ending with any of the exchange codes
            exchange_conditions = " OR ".join([f"u.asset_id LIKE ?" for _ in exchanges])
            conditions.append(f"({exchange_conditions})")
            params.extend([f"%.{ex}" for ex in exchanges])

        # Region filter (for Africa) - filter by countries in region
        if region and region in self.AFRICA_REGIONS:
            region_countries = self.AFRICA_REGIONS[region]
            all_exchanges = []
            for c in region_countries:
                if c in self.AFRICA_COUNTRY_EXCHANGES:
                    all_exchanges.extend(self.AFRICA_COUNTRY_EXCHANGES[c])
            if all_exchanges:
                exchange_conditions = " OR ".join([f"u.asset_id LIKE ?" for _ in all_exchanges])
                conditions.append(f"({exchange_conditions})")
                params.extend([f"%.{ex}" for ex in all_exchanges])

        # Asset type
        if asset_type and asset_type not in ("ALL", "Tous"):
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        # Search query
        if query:
            conditions.append("(u.symbol LIKE ? OR u.name LIKE ?)")
            pattern = f"%{query}%"
            params.extend([pattern, pattern])

        # Only scored
        if only_scored:
            conditions.append("s.score_total IS NOT NULL")

        where_clause = " AND ".join(conditions)

        # Count total
        count_sql = f"""
            SELECT COUNT(DISTINCT u.asset_id)
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            WHERE {where_clause}
        """

        # Sort mapping
        sort_map = {
            "score_total": "COALESCE(s.score_total, -999)",
            "symbol": "u.symbol",
            "name": "u.name",
            "confidence": "COALESCE(s.confidence, 0)"
        }
        order_col = sort_map.get(sort_by, "COALESCE(s.score_total, -999)")
        order_dir = "DESC" if sort_desc else "ASC"

        # Data query
        data_sql = f"""
            SELECT
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_scope, u.market_code,
                u.sector, u.industry,
                s.score_total, s.score_value, s.score_momentum, s.score_safety,
                s.confidence, s.rsi, s.vol_annual, s.max_drawdown,
                g.coverage, g.liquidity, g.fx_risk
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE {where_clause}
            ORDER BY {order_col} {order_dir}, u.symbol ASC
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            total = conn.execute(count_sql, params).fetchone()[0]
            rows = conn.execute(data_sql, params + [limit, offset]).fetchall()
            return [dict(row) for row in rows], total

    def get_top_scored_assets(
        self,
        market_scope: str = "US_EU",
        asset_type: str = None,
        limit: int = 50,
        market_filter: str = "ALL"
    ) -> List[Dict]:
        """Get top N scored assets with optional market and type filters."""
        conditions = ["u.active = 1", "s.score_total IS NOT NULL"]
        params = []

        # Filter by market_scope (US_EU or AFRICA)
        if market_scope:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        # Filter by specific market within scope (US or EU)
        if market_filter and market_filter not in ("ALL", "Tous"):
            if market_filter == "US":
                conditions.append("u.market_code LIKE 'US%'")
            elif market_filter == "EU":
                conditions.append(
                    "u.market_code NOT LIKE 'US%' AND u.market_scope = 'US_EU'")
            elif market_filter == "AFRICA":
                conditions.append("u.market_scope = 'AFRICA'")

        if asset_type and asset_type not in ("ALL", "Tous"):
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        sql = f"""
            SELECT
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_code,
                s.score_total, s.score_momentum, s.score_safety, s.score_value,
                s.confidence, g.coverage, g.liquidity
            FROM universe u
            INNER JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
            WHERE {" AND ".join(conditions)}
            ORDER BY s.score_total DESC, s.confidence DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, params + [limit]).fetchall()
            return [dict(row) for row in rows]

    def get_asset_types_for_scope(self, market_scope: str = "US_EU") -> List[str]:
        """Get available asset types for a scope."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT DISTINCT asset_type FROM universe
                WHERE active = 1 AND market_scope = ?
                ORDER BY asset_type
            """, (market_scope,)).fetchall()
            return [row["asset_type"] for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # LONG-TERM SCORING (ADD-ON)
    # ═══════════════════════════════════════════════════════════════════════════

    def ensure_longterm_schema(self) -> bool:
        """
        Ensure long-term scoring columns exist in scores_latest and scores_staging.
        Idempotent - safe to call multiple times.

        Returns:
            True if columns already existed or were added successfully
        """
        try:
            with self._get_connection() as conn:
                # Check if lt_score column exists in scores_latest
                columns = conn.execute(
                    "PRAGMA table_info(scores_latest)").fetchall()
                column_names = [c["name"] for c in columns]

                if "lt_score" not in column_names:
                    logger.info(
                        "Adding long-term scoring columns to scores_latest...")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_score REAL")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_confidence REAL")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_breakdown TEXT")
                    conn.execute(
                        "ALTER TABLE scores_latest ADD COLUMN lt_updated_at TEXT")

                    # Create index
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_scores_lt_score
                        ON scores_latest(lt_score DESC) WHERE lt_score IS NOT NULL
                    """)
                    logger.info(
                        "Long-term scoring columns added to scores_latest")

                # Check scores_staging table
                staging_columns = conn.execute(
                    "PRAGMA table_info(scores_staging)").fetchall()
                staging_names = [c["name"] for c in staging_columns]

                if "lt_score" not in staging_names:
                    logger.info(
                        "Adding long-term scoring columns to scores_staging...")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_score REAL")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_confidence REAL")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_breakdown TEXT")
                    conn.execute(
                        "ALTER TABLE scores_staging ADD COLUMN lt_updated_at TEXT")
                    logger.info(
                        "Long-term scoring columns added to scores_staging")

                return True

        except Exception as e:
            logger.error(f"Failed to ensure long-term schema: {e}")
            return False

    def upsert_longterm_score(
        self,
        asset_id: str,
        market_scope: str = "US_EU",
        lt_score: float = None,
        lt_confidence: float = None,
        lt_breakdown: Dict = None
    ) -> bool:
        """
        Update long-term score for an asset.

        Args:
            asset_id: Asset ID
            market_scope: US_EU or AFRICA
            lt_score: Long-term score value
            lt_confidence: Confidence in the score
            lt_breakdown: Breakdown dict (will be JSON stringified)

        Returns:
            True if successful
        """
        try:
            import json
            breakdown_json = json.dumps(lt_breakdown) if lt_breakdown else None

            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE scores_latest
                    SET lt_score = ?, lt_confidence = ?, lt_breakdown = ?, lt_updated_at = datetime('now')
                    WHERE asset_id = ?
                """, (lt_score, lt_confidence, breakdown_json, asset_id))
                return True
        except Exception as e:
            logger.error(f"Failed to upsert long-term score for {asset_id}: {e}")
            return False

    def get_top_longterm_scores(
        self,
        market_scope: str = "US_EU",
        asset_type: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get top assets by long-term score.

        Args:
            market_scope: US_EU or AFRICA
            asset_type: Filter by asset type (optional)
            limit: Number of results

        Returns:
            List of asset dicts with long-term scores
        """
        conditions = ["u.active = 1", "s.lt_score IS NOT NULL"]
        params = []

        if market_scope:
            conditions.append("u.market_scope = ?")
            params.append(market_scope)

        if asset_type:
            conditions.append("u.asset_type = ?")
            params.append(asset_type)

        sql = f"""
            SELECT
                u.asset_id, u.symbol, u.name, u.asset_type, u.market_code,
                s.lt_score, s.lt_confidence, s.lt_breakdown, s.lt_updated_at,
                s.score_total, s.confidence
            FROM universe u
            INNER JOIN scores_latest s ON u.asset_id = s.asset_id
            WHERE {" AND ".join(conditions)}
            ORDER BY s.lt_score DESC, s.lt_confidence DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, params + [limit]).fetchall()
            return [dict(row) for row in rows]
