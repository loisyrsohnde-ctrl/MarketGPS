"""
MarketGPS - Geographic Validation Module (PR6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Validates geographic consistency of assets:
- scope → region → country → exchange hierarchy
- No cross-scope leaks
- No cross-region leaks

Quarantine:
- Assets with validation errors are flagged
- Quarantine report available via API
- Pipeline can auto-fix or manual review

Usage:
    from geo_validation import GeoValidator, validate_asset

    validator = GeoValidator()
    is_valid, errors = validator.validate_asset(asset_dict)

    # Batch validation
    report = validator.validate_universe(store)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHIC CONSTANTS (Single Source of Truth)
# ═══════════════════════════════════════════════════════════════════════════════

# Import from asset_query for consistency
from asset_query import (
    AFRICA_REGIONS,
    AFRICA_COUNTRY_EXCHANGES,
    ALL_AFRICA_COUNTRIES,
    ALL_AFRICA_REGIONS,
    MarketScope,
)

# US_EU specific mappings
US_EU_MARKET_CODES = {"US", "EU", "UK", "FR", "DE", "CH", "NL", "BE", "IT", "ES"}

US_EU_EXCHANGES = {
    "US": ["NYSE", "NASDAQ", "AMEX", "BATS", "ARCA"],
    "EU": ["XETRA", "EURONEXT", "LSE", "SIX", "BME", "BORSA"],
    "UK": ["LSE", "AIM"],
    "FR": ["EURONEXT"],
    "DE": ["XETRA", "FSE"],
}

# Flatten for validation
ALL_US_EU_EXCHANGES = set()
for exchanges in US_EU_EXCHANGES.values():
    ALL_US_EU_EXCHANGES.update(exchanges)

ALL_AFRICA_EXCHANGES = set()
for exchanges in AFRICA_COUNTRY_EXCHANGES.values():
    ALL_AFRICA_EXCHANGES.update(exchanges)


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION ERROR TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class GeoErrorCode:
    """Geographic validation error codes."""
    INVALID_SCOPE = "INVALID_SCOPE"
    SCOPE_EXCHANGE_MISMATCH = "SCOPE_EXCHANGE_MISMATCH"
    COUNTRY_NOT_IN_SCOPE = "COUNTRY_NOT_IN_SCOPE"
    COUNTRY_NOT_IN_REGION = "COUNTRY_NOT_IN_REGION"
    EXCHANGE_NOT_FOR_COUNTRY = "EXCHANGE_NOT_FOR_COUNTRY"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_REGION = "INVALID_REGION"
    CROSS_SCOPE_LEAK = "CROSS_SCOPE_LEAK"


@dataclass
class GeoValidationError:
    """A single geographic validation error."""
    code: str
    message: str
    field: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    severity: str = "error"  # "error" or "warning"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity,
        }


@dataclass
class GeoValidationResult:
    """Result of geographic validation for an asset."""
    asset_id: str
    is_valid: bool
    errors: List[GeoValidationError] = field(default_factory=list)
    warnings: List[GeoValidationError] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "validated_at": self.validated_at,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATOR CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class GeoValidator:
    """
    Geographic consistency validator for MarketGPS assets.

    Validates the hierarchy:
        market_scope → region (AFRICA only) → country → exchange

    Rules:
    1. market_scope must be "US_EU" or "AFRICA"
    2. Exchange must belong to the correct scope
    3. For AFRICA: country must be valid and match exchange
    4. For AFRICA: region must contain the country
    5. No cross-scope data leaks
    """

    def validate_asset(self, asset: Dict[str, Any]) -> GeoValidationResult:
        """
        Validate a single asset's geographic data.

        Args:
            asset: Asset dictionary with market_scope, exchange, country, etc.

        Returns:
            GeoValidationResult with is_valid flag and any errors
        """
        asset_id = asset.get("asset_id", "unknown")
        errors: List[GeoValidationError] = []
        warnings: List[GeoValidationError] = []

        # Extract fields
        market_scope = asset.get("market_scope")
        market_code = asset.get("market_code")
        exchange = asset.get("exchange") or asset.get("exchange_code")
        country = asset.get("country") or asset.get("country_code")
        region = asset.get("region")

        # Also try to extract exchange from asset_id (e.g., "JSE:ABC")
        if not exchange and asset_id and ":" in asset_id:
            exchange = asset_id.split(":")[0]

        # Rule 1: market_scope required and valid
        if not market_scope:
            errors.append(GeoValidationError(
                code=GeoErrorCode.MISSING_REQUIRED_FIELD,
                message="market_scope is required",
                field="market_scope",
            ))
        elif market_scope not in (MarketScope.US_EU.value, MarketScope.AFRICA.value):
            errors.append(GeoValidationError(
                code=GeoErrorCode.INVALID_SCOPE,
                message=f"Invalid market_scope: {market_scope}",
                field="market_scope",
                expected="US_EU or AFRICA",
                actual=market_scope,
            ))

        # Rule 2: Exchange must belong to scope
        if exchange and market_scope:
            if market_scope == MarketScope.US_EU.value:
                if exchange in ALL_AFRICA_EXCHANGES:
                    errors.append(GeoValidationError(
                        code=GeoErrorCode.CROSS_SCOPE_LEAK,
                        message=f"African exchange {exchange} found in US_EU scope",
                        field="exchange",
                        expected="US/EU exchange",
                        actual=exchange,
                    ))
            elif market_scope == MarketScope.AFRICA.value:
                if exchange in ALL_US_EU_EXCHANGES:
                    errors.append(GeoValidationError(
                        code=GeoErrorCode.CROSS_SCOPE_LEAK,
                        message=f"US/EU exchange {exchange} found in AFRICA scope",
                        field="exchange",
                        expected="African exchange",
                        actual=exchange,
                    ))

        # Rule 3: AFRICA-specific validations
        if market_scope == MarketScope.AFRICA.value:
            # Country validation
            if country:
                if country not in ALL_AFRICA_COUNTRIES:
                    errors.append(GeoValidationError(
                        code=GeoErrorCode.COUNTRY_NOT_IN_SCOPE,
                        message=f"Country {country} is not a valid African country",
                        field="country",
                        expected=f"One of: {sorted(ALL_AFRICA_COUNTRIES)}",
                        actual=country,
                    ))
                else:
                    # Check exchange matches country
                    if exchange:
                        valid_exchanges = AFRICA_COUNTRY_EXCHANGES.get(country, [])
                        if exchange not in valid_exchanges:
                            errors.append(GeoValidationError(
                                code=GeoErrorCode.EXCHANGE_NOT_FOR_COUNTRY,
                                message=f"Exchange {exchange} not valid for country {country}",
                                field="exchange",
                                expected=f"One of: {valid_exchanges}",
                                actual=exchange,
                            ))

            # Region validation
            if region:
                if region not in ALL_AFRICA_REGIONS:
                    errors.append(GeoValidationError(
                        code=GeoErrorCode.INVALID_REGION,
                        message=f"Invalid African region: {region}",
                        field="region",
                        expected=f"One of: {sorted(ALL_AFRICA_REGIONS)}",
                        actual=region,
                    ))
                elif country:
                    # Check country is in region
                    region_countries = AFRICA_REGIONS.get(region, [])
                    if country not in region_countries:
                        errors.append(GeoValidationError(
                            code=GeoErrorCode.COUNTRY_NOT_IN_REGION,
                            message=f"Country {country} not in region {region}",
                            field="country",
                            expected=f"One of: {region_countries}",
                            actual=country,
                        ))

        # Rule 4: US_EU-specific validations
        if market_scope == MarketScope.US_EU.value:
            # Warn if AFRICA-related fields are set
            if region and region in ALL_AFRICA_REGIONS:
                warnings.append(GeoValidationError(
                    code=GeoErrorCode.CROSS_SCOPE_LEAK,
                    message=f"African region {region} set for US_EU asset",
                    field="region",
                    severity="warning",
                ))
            if country and country in ALL_AFRICA_COUNTRIES:
                warnings.append(GeoValidationError(
                    code=GeoErrorCode.CROSS_SCOPE_LEAK,
                    message=f"African country {country} set for US_EU asset",
                    field="country",
                    severity="warning",
                ))

        is_valid = len(errors) == 0

        return GeoValidationResult(
            asset_id=asset_id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )

    def validate_universe(self, store, limit: int = None) -> Dict[str, Any]:
        """
        Validate all assets in the universe.

        Args:
            store: SQLiteStore instance
            limit: Optional limit for testing

        Returns:
            Validation report with summary and invalid assets
        """
        invalid_assets = []
        warning_assets = []
        total = 0
        valid_count = 0

        with store._get_connection() as conn:
            query = "SELECT asset_id, symbol, market_scope, market_code, exchange_code, country FROM universe WHERE active = 1"
            if limit:
                query += f" LIMIT {limit}"

            rows = conn.execute(query).fetchall()
            total = len(rows)

            for row in rows:
                asset = {
                    "asset_id": row[0],
                    "symbol": row[1],
                    "market_scope": row[2],
                    "market_code": row[3],
                    "exchange": row[4],
                    "country": row[5],
                }

                result = self.validate_asset(asset)

                if result.is_valid:
                    valid_count += 1
                    if result.warnings:
                        warning_assets.append(result.to_dict())
                else:
                    invalid_assets.append(result.to_dict())

        return {
            "validated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total": total,
                "valid": valid_count,
                "invalid": len(invalid_assets),
                "with_warnings": len(warning_assets),
                "validity_rate": round(valid_count / total * 100, 2) if total > 0 else 0,
            },
            "invalid_assets": invalid_assets[:100],  # Limit to first 100
            "warning_assets": warning_assets[:50],   # Limit to first 50
        }


# ═══════════════════════════════════════════════════════════════════════════════
# QUARANTINE TABLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_quarantine_table(store) -> None:
    """Create quarantine table if it doesn't exist."""
    with store._get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS geo_quarantine (
                asset_id TEXT PRIMARY KEY,
                symbol TEXT,
                market_scope TEXT,
                error_codes TEXT,           -- Comma-separated error codes
                error_details TEXT,         -- JSON string of full errors
                quarantined_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT,
                review_status TEXT DEFAULT 'pending',  -- pending, fixed, ignored
                review_notes TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_quarantine_status
            ON geo_quarantine(review_status)
        """)
        logger.info("✅ geo_quarantine table ready")


def quarantine_asset(
    store,
    asset_id: str,
    symbol: str,
    market_scope: str,
    errors: List[GeoValidationError],
) -> None:
    """Add an asset to quarantine."""
    import json

    error_codes = ",".join([e.code for e in errors])
    error_details = json.dumps([e.to_dict() for e in errors])

    with store._get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO geo_quarantine
            (asset_id, symbol, market_scope, error_codes, error_details, quarantined_at, review_status)
            VALUES (?, ?, ?, ?, ?, datetime('now'), 'pending')
        """, (asset_id, symbol, market_scope, error_codes, error_details))

    logger.info(f"Quarantined asset {asset_id}: {error_codes}")


def get_quarantine_report(store, status: str = None, limit: int = 100) -> Dict[str, Any]:
    """Get quarantine report."""
    import json

    with store._get_connection() as conn:
        # Summary counts
        summary_query = """
            SELECT review_status, COUNT(*) as count
            FROM geo_quarantine
            GROUP BY review_status
        """
        summary_rows = conn.execute(summary_query).fetchall()
        summary = {row[0]: row[1] for row in summary_rows}

        # Detailed list
        list_query = """
            SELECT asset_id, symbol, market_scope, error_codes, error_details,
                   quarantined_at, reviewed_at, review_status, review_notes
            FROM geo_quarantine
        """
        params = []
        if status:
            list_query += " WHERE review_status = ?"
            params.append(status)
        list_query += f" ORDER BY quarantined_at DESC LIMIT {limit}"

        rows = conn.execute(list_query, params).fetchall()

        assets = []
        for row in rows:
            assets.append({
                "asset_id": row[0],
                "symbol": row[1],
                "market_scope": row[2],
                "error_codes": row[3].split(",") if row[3] else [],
                "errors": json.loads(row[4]) if row[4] else [],
                "quarantined_at": row[5],
                "reviewed_at": row[6],
                "review_status": row[7],
                "review_notes": row[8],
            })

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total": sum(summary.values()),
                "pending": summary.get("pending", 0),
                "fixed": summary.get("fixed", 0),
                "ignored": summary.get("ignored", 0),
            },
            "assets": assets,
        }


def update_quarantine_status(
    store,
    asset_id: str,
    status: str,
    notes: str = None,
) -> bool:
    """Update quarantine status for an asset."""
    if status not in ("pending", "fixed", "ignored"):
        return False

    with store._get_connection() as conn:
        conn.execute("""
            UPDATE geo_quarantine
            SET review_status = ?, review_notes = ?, reviewed_at = datetime('now')
            WHERE asset_id = ?
        """, (status, notes, asset_id))

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_asset(asset: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Simple validation function.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    validator = GeoValidator()
    result = validator.validate_asset(asset)
    error_messages = [e.message for e in result.errors]
    return result.is_valid, error_messages


def run_validation_pipeline(store, quarantine: bool = True) -> Dict[str, Any]:
    """
    Run full validation pipeline on universe.

    Args:
        store: SQLiteStore instance
        quarantine: If True, add invalid assets to quarantine table

    Returns:
        Validation report
    """
    # Ensure table exists
    if quarantine:
        ensure_quarantine_table(store)

    validator = GeoValidator()
    report = validator.validate_universe(store)

    # Quarantine invalid assets
    if quarantine:
        for invalid in report["invalid_assets"]:
            errors = [
                GeoValidationError(**e) for e in invalid["errors"]
            ]
            quarantine_asset(
                store,
                asset_id=invalid["asset_id"],
                symbol=invalid.get("symbol", ""),
                market_scope=invalid.get("market_scope", ""),
                errors=errors,
            )

    return report
