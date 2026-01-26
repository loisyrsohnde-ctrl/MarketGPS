"""
MarketGPS - Centralized Asset Query Module
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PR3: Single source of truth for all asset queries.

Consolidates:
- search_universe()
- get_top_scores()
- get_top_scored_assets()
- Inline SQL queries (e.g., /top-scored-institutional)

Design principles:
- Additive: Does not break existing endpoints
- Consistent: Same filters produce same results everywhere
- Validated: Geographic hierarchy enforced (scope → region → country → exchange)
- Testable: Pure functions, injectable store

Usage:
    from asset_query import AssetQueryBuilder, AssetFilters

    builder = AssetQueryBuilder(store)
    filters = AssetFilters(market_scope="US_EU", only_scored=True)
    results, total = builder.search(filters)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS - Geographic Hierarchy
# ═══════════════════════════════════════════════════════════════════════════════

class MarketScope(str, Enum):
    """Primary market scope."""
    US_EU = "US_EU"
    AFRICA = "AFRICA"


# US_EU market codes
US_EU_MARKETS = {"US", "EU"}

# Africa regions and their countries
AFRICA_REGIONS = {
    "SOUTHERN": ["ZA", "BW", "MU", "NA", "ZW"],
    "WEST": ["NG", "GH", "CI", "SN"],
    "EAST": ["KE", "TZ", "UG", "RW", "ET"],
    "NORTH": ["EG", "MA", "TN"],
}

# Country to exchange mapping (for asset_id LIKE queries)
AFRICA_COUNTRY_EXCHANGES = {
    "ZA": ["JSE"],      # South Africa
    "NG": ["NGX"],      # Nigeria
    "KE": ["NSE"],      # Kenya
    "EG": ["EGX"],      # Egypt
    "MA": ["CSE"],      # Morocco
    "GH": ["GSE"],      # Ghana
    "MU": ["SEM"],      # Mauritius
    "BW": ["BSE"],      # Botswana
    "TZ": ["DSE"],      # Tanzania
    "CI": ["BRVM"],     # Ivory Coast (BRVM covers WAEMU)
    "TN": ["BVMT"],     # Tunisia
    "UG": ["USE"],      # Uganda
    "RW": ["RSE"],      # Rwanda
    "NA": ["NSX"],      # Namibia
    "ZW": ["ZSE"],      # Zimbabwe
    "ET": ["ESX"],      # Ethiopia
    "SN": ["BRVM"],     # Senegal (also BRVM)
}

# Flatten for validation
ALL_AFRICA_COUNTRIES = set(AFRICA_COUNTRY_EXCHANGES.keys())
ALL_AFRICA_REGIONS = set(AFRICA_REGIONS.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AssetFilters:
    """
    Unified filter specification for asset queries.

    Geographic Hierarchy (PR6 ready):
        market_scope → region → country → exchange

    Validation rules:
        - If country is set, it must belong to market_scope
        - If region is set, it must be valid for AFRICA scope
        - market_code is US_EU only (US or EU)
    """
    # Geographic filters
    market_scope: str = "US_EU"
    market_code: Optional[str] = None   # US or EU (for US_EU scope)
    region: Optional[str] = None        # AFRICA regions: SOUTHERN, WEST, EAST, NORTH
    country: Optional[str] = None       # ISO 2-letter country code

    # Asset type filter
    asset_type: Optional[str] = None    # EQUITY, ETF, BOND, FX, CRYPTO, etc.

    # Score filters
    only_scored: bool = True            # Require score_total IS NOT NULL
    min_score: Optional[float] = None   # Minimum score_total
    max_score: Optional[float] = None   # Maximum score_total

    # Institutional filters (v2.0)
    institutional_only: bool = False    # Require score_institutional IS NOT NULL
    min_lt_score: Optional[float] = None
    min_liquidity_tier: Optional[str] = None  # A, B, C, D
    exclude_flagged: bool = False       # Exclude gating_status.flagged = 1
    min_horizon_years: Optional[int] = None

    # Search & pagination
    query: Optional[str] = None         # Text search (symbol + name)
    sort_by: str = "score_total"
    sort_desc: bool = True
    limit: int = 50
    offset: int = 0

    def validate(self) -> List[str]:
        """
        Validate filter consistency.
        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Validate market_scope
        if self.market_scope not in (MarketScope.US_EU.value, MarketScope.AFRICA.value):
            errors.append(f"Invalid market_scope: {self.market_scope}")

        # Validate market_code (US_EU only)
        if self.market_code:
            if self.market_scope != MarketScope.US_EU.value:
                errors.append(f"market_code only valid for US_EU scope, got {self.market_scope}")
            elif self.market_code not in US_EU_MARKETS:
                errors.append(f"Invalid market_code: {self.market_code}. Must be US or EU")

        # Validate region (AFRICA only)
        if self.region:
            if self.market_scope != MarketScope.AFRICA.value:
                errors.append(f"region only valid for AFRICA scope, got {self.market_scope}")
            elif self.region not in ALL_AFRICA_REGIONS:
                errors.append(f"Invalid region: {self.region}. Valid: {ALL_AFRICA_REGIONS}")

        # Validate country
        if self.country:
            if self.market_scope == MarketScope.AFRICA.value:
                if self.country not in ALL_AFRICA_COUNTRIES:
                    errors.append(f"Invalid AFRICA country: {self.country}")
                # Check region consistency
                if self.region:
                    region_countries = AFRICA_REGIONS.get(self.region, [])
                    if self.country not in region_countries:
                        errors.append(f"Country {self.country} not in region {self.region}")

        # Validate liquidity tier
        if self.min_liquidity_tier and self.min_liquidity_tier not in ("A", "B", "C", "D"):
            errors.append(f"Invalid liquidity_tier: {self.min_liquidity_tier}")

        return errors

    def is_valid(self) -> bool:
        """Check if filters are valid."""
        return len(self.validate()) == 0


@dataclass
class AssetResult:
    """
    Standardized asset result with score data.
    Maps to frontend AssetView DTO.
    """
    # Core identifiers
    asset_id: str
    symbol: str
    name: str

    # Classification
    asset_type: str
    market_scope: str
    market_code: str
    exchange: Optional[str] = None
    country: Optional[str] = None

    # Score data (always present if only_scored=True)
    score_total: Optional[float] = None
    score_value: Optional[float] = None
    score_momentum: Optional[float] = None
    score_safety: Optional[float] = None
    score_quality: Optional[float] = None
    confidence: Optional[float] = None

    # Institutional data (v2.0)
    score_institutional: Optional[float] = None
    lt_score: Optional[float] = None
    liquidity_tier: Optional[str] = None
    min_recommended_horizon_years: Optional[int] = None

    # Gating status
    flagged: bool = False
    coverage_score: Optional[float] = None
    fx_risk_score: Optional[float] = None

    # Timestamps
    last_score_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "asset_id": self.asset_id,
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type,
            "market_scope": self.market_scope,
            "market_code": self.market_code,
            "exchange": self.exchange,
            "country": self.country,
            "score_total": self.score_total,
            "score_value": self.score_value,
            "score_momentum": self.score_momentum,
            "score_safety": self.score_safety,
            "score_quality": self.score_quality,
            "confidence": self.confidence,
            "score_institutional": self.score_institutional,
            "lt_score": self.lt_score,
            "liquidity_tier": self.liquidity_tier,
            "min_recommended_horizon_years": self.min_recommended_horizon_years,
            "flagged": self.flagged,
            "coverage_score": self.coverage_score,
            "fx_risk_score": self.fx_risk_score,
            "last_score_date": self.last_score_date,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class AssetQueryBuilder:
    """
    Centralized asset query builder.

    Single source of truth for all asset queries across:
    - /api/assets/top-scored
    - /api/assets/top-scored-institutional
    - /api/assets/explorer
    - /api/barbell/candidates/*

    Usage:
        builder = AssetQueryBuilder(store)
        filters = AssetFilters(market_scope="US_EU", only_scored=True)
        results, total_count = builder.search(filters)
    """

    def __init__(self, store):
        """
        Initialize with SQLite store.

        Args:
            store: SQLiteStore instance with _get_connection() method
        """
        self.store = store

    def search(self, filters: AssetFilters) -> Tuple[List[Dict[str, Any]], int]:
        """
        Execute unified asset search.

        Args:
            filters: AssetFilters specification

        Returns:
            Tuple of (results list, total count without pagination)
        """
        # Validate filters
        errors = filters.validate()
        if errors:
            logger.warning(f"Invalid filters: {errors}")
            # Don't fail, but log warning - backward compatible

        # Build query
        sql, params = self._build_query(filters)
        count_sql, count_params = self._build_count_query(filters)

        # Execute
        with self.store._get_connection() as conn:
            # Get total count
            total = conn.execute(count_sql, count_params).fetchone()[0]

            # Get results
            rows = conn.execute(sql, params).fetchall()

            # Map to dicts
            columns = [
                "asset_id", "symbol", "name", "asset_type", "market_scope", "market_code",
                "exchange", "country",
                "score_total", "score_value", "score_momentum", "score_safety", "score_quality",
                "confidence", "last_score_date",
                "score_institutional", "lt_score", "liquidity_tier", "min_recommended_horizon_years",
                "flagged", "coverage_score", "fx_risk_score"
            ]

            results = []
            for row in rows:
                result = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        result[col] = row[i]
                results.append(result)

            return results, total

    def get_top_scored(
        self,
        market_scope: str = "US_EU",
        asset_type: Optional[str] = None,
        market_code: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get top scored assets.

        Convenience method wrapping search() with score-focused defaults.
        """
        filters = AssetFilters(
            market_scope=market_scope,
            market_code=market_code,
            asset_type=asset_type,
            only_scored=True,
            sort_by="score_total",
            sort_desc=True,
            limit=limit,
        )
        results, _ = self.search(filters)
        return results

    def get_institutional(
        self,
        market_scope: str = "US_EU",
        asset_type: Optional[str] = None,
        min_liquidity_tier: Optional[str] = None,
        exclude_flagged: bool = True,
        min_horizon_years: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get institutional-grade assets.

        Convenience method for /top-scored-institutional endpoint.
        """
        filters = AssetFilters(
            market_scope=market_scope,
            asset_type=asset_type,
            institutional_only=True,
            min_liquidity_tier=min_liquidity_tier,
            exclude_flagged=exclude_flagged,
            min_horizon_years=min_horizon_years,
            sort_by="score_institutional",
            sort_desc=True,
            limit=limit,
        )
        results, _ = self.search(filters)
        return results

    def get_explorer(
        self,
        market_scope: str = "US_EU",
        market_code: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        asset_type: Optional[str] = None,
        query: Optional[str] = None,
        only_scored: bool = False,
        sort_by: str = "symbol",
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Explorer search with pagination.

        Convenience method for /explorer endpoint.
        """
        filters = AssetFilters(
            market_scope=market_scope,
            market_code=market_code,
            country=country,
            region=region,
            asset_type=asset_type,
            query=query,
            only_scored=only_scored,
            sort_by=sort_by,
            sort_desc=(sort_by == "score_total"),
            limit=limit,
            offset=offset,
        )
        return self.search(filters)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: Query Building
    # ─────────────────────────────────────────────────────────────────────────

    def _build_query(self, filters: AssetFilters) -> Tuple[str, List[Any]]:
        """Build the main SELECT query."""

        select_clause = """
            SELECT
                u.asset_id,
                u.symbol,
                u.name,
                u.asset_type,
                u.market_scope,
                u.market_code,
                u.exchange,
                u.country,
                s.score_total,
                s.score_value,
                s.score_momentum,
                s.score_safety,
                s.score_quality,
                s.confidence,
                s.date as last_score_date,
                s.score_institutional,
                s.lt_score,
                g.liquidity_tier,
                g.min_recommended_horizon_years,
                COALESCE(g.flagged, 0) as flagged,
                g.coverage_score,
                g.fx_risk_score
        """

        from_clause = """
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
        """

        conditions, params = self._build_conditions(filters)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Order by
        order_col = self._map_sort_column(filters.sort_by)
        order_dir = "DESC" if filters.sort_desc else "ASC"

        # For score sorting, put NULLs last
        if "score" in filters.sort_by.lower():
            order_clause = f"ORDER BY {order_col} IS NULL, {order_col} {order_dir}"
        else:
            order_clause = f"ORDER BY {order_col} {order_dir}"

        # Pagination
        limit_clause = f"LIMIT {filters.limit}"
        if filters.offset > 0:
            limit_clause += f" OFFSET {filters.offset}"

        sql = f"{select_clause} {from_clause} {where_clause} {order_clause} {limit_clause}"

        return sql, params

    def _build_count_query(self, filters: AssetFilters) -> Tuple[str, List[Any]]:
        """Build COUNT query for pagination."""

        from_clause = """
            FROM universe u
            LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
            LEFT JOIN gating_status g ON u.asset_id = g.asset_id
        """

        conditions, params = self._build_conditions(filters)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"SELECT COUNT(*) {from_clause} {where_clause}"

        return sql, params

    def _build_conditions(self, filters: AssetFilters) -> Tuple[List[str], List[Any]]:
        """Build WHERE conditions and parameters."""
        conditions = []
        params = []

        # Market scope
        if filters.market_scope:
            conditions.append("u.market_scope = ?")
            params.append(filters.market_scope)

        # Market code (US/EU)
        if filters.market_code:
            conditions.append("u.market_code = ?")
            params.append(filters.market_code)

        # Country (AFRICA - using exchange mapping)
        if filters.country:
            exchanges = AFRICA_COUNTRY_EXCHANGES.get(filters.country, [])
            if exchanges:
                # Match asset_id pattern like "JSE:XXX" or "NGX:XXX"
                exchange_conditions = []
                for exch in exchanges:
                    exchange_conditions.append("u.asset_id LIKE ?")
                    params.append(f"{exch}:%")
                if exchange_conditions:
                    conditions.append(f"({' OR '.join(exchange_conditions)})")

        # Region (AFRICA - expand to countries)
        if filters.region and not filters.country:
            region_countries = AFRICA_REGIONS.get(filters.region, [])
            if region_countries:
                exchange_conditions = []
                for country_code in region_countries:
                    exchanges = AFRICA_COUNTRY_EXCHANGES.get(country_code, [])
                    for exch in exchanges:
                        exchange_conditions.append("u.asset_id LIKE ?")
                        params.append(f"{exch}:%")
                if exchange_conditions:
                    conditions.append(f"({' OR '.join(exchange_conditions)})")

        # Asset type
        if filters.asset_type:
            conditions.append("u.asset_type = ?")
            params.append(filters.asset_type)

        # Only scored
        if filters.only_scored:
            conditions.append("s.score_total IS NOT NULL")

        # Score range
        if filters.min_score is not None:
            conditions.append("s.score_total >= ?")
            params.append(filters.min_score)
        if filters.max_score is not None:
            conditions.append("s.score_total <= ?")
            params.append(filters.max_score)

        # Institutional filters
        if filters.institutional_only:
            conditions.append("s.score_institutional IS NOT NULL")

        if filters.min_lt_score is not None:
            conditions.append("s.lt_score >= ?")
            params.append(filters.min_lt_score)

        if filters.min_liquidity_tier:
            # A is best, D is worst - so min_tier="B" means A or B
            tier_order = {"A": 1, "B": 2, "C": 3, "D": 4}
            max_tier_value = tier_order.get(filters.min_liquidity_tier, 4)
            allowed_tiers = [t for t, v in tier_order.items() if v <= max_tier_value]
            placeholders = ",".join(["?" for _ in allowed_tiers])
            conditions.append(f"g.liquidity_tier IN ({placeholders})")
            params.extend(allowed_tiers)

        if filters.exclude_flagged:
            conditions.append("(g.flagged IS NULL OR g.flagged = 0)")

        if filters.min_horizon_years is not None:
            conditions.append("g.min_recommended_horizon_years <= ?")
            params.append(filters.min_horizon_years)

        # Text search
        if filters.query:
            search_term = f"%{filters.query}%"
            conditions.append("(u.symbol LIKE ? OR u.name LIKE ?)")
            params.extend([search_term, search_term])

        return conditions, params

    def _map_sort_column(self, sort_by: str) -> str:
        """Map sort field name to SQL column."""
        mapping = {
            "score_total": "s.score_total",
            "score": "s.score_total",
            "score_value": "s.score_value",
            "score_momentum": "s.score_momentum",
            "score_safety": "s.score_safety",
            "score_quality": "s.score_quality",
            "score_institutional": "s.score_institutional",
            "lt_score": "s.lt_score",
            "confidence": "s.confidence",
            "symbol": "u.symbol",
            "name": "u.name",
            "asset_type": "u.asset_type",
        }
        return mapping.get(sort_by, "s.score_total")


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_countries_for_region(region: str) -> List[str]:
    """Get list of country codes for a region."""
    return AFRICA_REGIONS.get(region, [])


def get_region_for_country(country: str) -> Optional[str]:
    """Get region for a country code."""
    for region, countries in AFRICA_REGIONS.items():
        if country in countries:
            return region
    return None


def get_exchanges_for_country(country: str) -> List[str]:
    """Get exchange codes for a country."""
    return AFRICA_COUNTRY_EXCHANGES.get(country, [])


def validate_geographic_hierarchy(
    market_scope: str,
    region: Optional[str] = None,
    country: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate geographic filter hierarchy.

    Returns:
        Tuple of (is_valid, error_message)
    """
    filters = AssetFilters(
        market_scope=market_scope,
        region=region,
        country=country,
    )
    errors = filters.validate()
    if errors:
        return False, "; ".join(errors)
    return True, None
