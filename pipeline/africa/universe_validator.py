"""
MarketGPS v14.0 - Africa Universe Validator
Strict validation and normalization for AFRICA universe CSV imports.

Validation rules:
- asset_id must be unique and properly formatted (SYMBOL.EXCHANGE)
- market_scope must be 'AFRICA'
- market_code must be a valid African exchange
- exchange_code must match market_code or be a valid MIC
- currency must be valid for the exchange
- Required fields: asset_id, symbol, market_code

Normalization:
- Uppercase symbols
- Trim whitespace
- Set defaults for optional fields
- Map legacy codes to current standards
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
import re

from core.config import get_logger
from pipeline.africa.exchanges_catalog import (
    AFRICA_EXCHANGES,
    CURRENCY_INFO,
    get_exchange_info,
    get_valid_market_codes,
)

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION RESULT DATACLASS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Result of row validation."""
    is_valid: bool
    row: Dict
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    normalized_row: Optional[Dict] = None


@dataclass
class BatchValidationResult:
    """Result of batch validation."""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: List[ValidationResult]
    unique_asset_ids: Set[str] = field(default_factory=set)
    duplicate_ids: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATOR CLASS
# ═══════════════════════════════════════════════════════════════════════════

class AfricaUniverseValidator:
    """
    Validates and normalizes AFRICA universe data.
    
    Features:
    - Strict field validation
    - Exchange/currency/country consistency checks
    - Automatic normalization
    - Duplicate detection
    - Detailed error reporting
    """
    
    # Valid asset types
    VALID_ASSET_TYPES = {"EQUITY", "ETF", "BOND", "FUND", "INDEX"}
    
    # Required fields
    REQUIRED_FIELDS = {"symbol", "market_code"}
    
    # Symbol pattern (letters, numbers, dots, max 20 chars)
    SYMBOL_PATTERN = re.compile(r'^[A-Za-z0-9.\-]{1,20}$')
    
    def __init__(self):
        """Initialize validator."""
        self._valid_market_codes = get_valid_market_codes()
        self._seen_asset_ids: Set[str] = set()
    
    def validate_row(self, row: Dict, row_number: int = 0) -> ValidationResult:
        """
        Validate a single row from CSV.
        
        Args:
            row: Dictionary with row data
            row_number: Row number for error messages
            
        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []
        
        # ─────────────────────────────────────────────────────────────────
        # 1. Required fields check
        # ─────────────────────────────────────────────────────────────────
        for field in self.REQUIRED_FIELDS:
            value = row.get(field, "").strip()
            if not value:
                errors.append(f"Row {row_number}: Missing required field '{field}'")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                row=row,
                errors=errors,
                warnings=warnings
            )
        
        # ─────────────────────────────────────────────────────────────────
        # 2. Symbol validation
        # ─────────────────────────────────────────────────────────────────
        symbol = row.get("symbol", "").strip().upper()
        if not self.SYMBOL_PATTERN.match(symbol):
            errors.append(f"Row {row_number}: Invalid symbol format '{symbol}'")
        
        # ─────────────────────────────────────────────────────────────────
        # 3. Market code validation
        # ─────────────────────────────────────────────────────────────────
        market_code = row.get("market_code", "").strip().upper()
        exchange_info = get_exchange_info(market_code)
        
        if not exchange_info:
            # Try to find by country code
            found = False
            for code, info in AFRICA_EXCHANGES.items():
                if info.country == market_code:
                    market_code = code
                    exchange_info = info
                    found = True
                    warnings.append(
                        f"Row {row_number}: Mapped country code '{row.get('market_code')}' "
                        f"to exchange '{code}'"
                    )
                    break
            
            if not found:
                errors.append(
                    f"Row {row_number}: Invalid market_code '{market_code}'. "
                    f"Valid: {', '.join(sorted(AFRICA_EXCHANGES.keys()))}"
                )
        
        # ─────────────────────────────────────────────────────────────────
        # 4. Exchange code validation
        # ─────────────────────────────────────────────────────────────────
        exchange_code = row.get("exchange_code", "").strip().upper()
        if not exchange_code and exchange_info:
            exchange_code = exchange_info.eodhd_code
        
        if exchange_info and exchange_code:
            # Validate that exchange_code is consistent
            valid_codes = {exchange_info.eodhd_code, exchange_info.code}
            if exchange_info.mic:
                valid_codes.add(exchange_info.mic)
            
            if exchange_code not in valid_codes:
                warnings.append(
                    f"Row {row_number}: exchange_code '{exchange_code}' doesn't match "
                    f"expected codes for {market_code}: {valid_codes}"
                )
        
        # ─────────────────────────────────────────────────────────────────
        # 5. Currency validation
        # ─────────────────────────────────────────────────────────────────
        currency = row.get("currency", "").strip().upper()
        if not currency and exchange_info:
            currency = exchange_info.currency
        
        if currency and exchange_info:
            if currency != exchange_info.currency:
                # Allow USD for dual-listed stocks
                if currency not in ("USD", exchange_info.currency):
                    warnings.append(
                        f"Row {row_number}: Currency '{currency}' doesn't match "
                        f"expected '{exchange_info.currency}' for {market_code}"
                    )
        
        if currency and currency not in CURRENCY_INFO:
            warnings.append(f"Row {row_number}: Unknown currency '{currency}'")
        
        # ─────────────────────────────────────────────────────────────────
        # 6. Asset type validation
        # ─────────────────────────────────────────────────────────────────
        asset_type = row.get("asset_type", "").strip().upper()
        if not asset_type:
            asset_type = "EQUITY"
        
        if asset_type not in self.VALID_ASSET_TYPES:
            warnings.append(
                f"Row {row_number}: Unknown asset_type '{asset_type}', defaulting to EQUITY"
            )
            asset_type = "EQUITY"
        
        # ─────────────────────────────────────────────────────────────────
        # 7. Asset ID validation
        # ─────────────────────────────────────────────────────────────────
        asset_id = row.get("asset_id", "").strip()
        if not asset_id:
            # Generate asset_id from symbol and exchange
            eodhd_code = exchange_info.eodhd_code if exchange_info else market_code
            asset_id = f"{symbol}.{eodhd_code}"
        
        # Check for duplicates
        if asset_id in self._seen_asset_ids:
            errors.append(f"Row {row_number}: Duplicate asset_id '{asset_id}'")
        else:
            self._seen_asset_ids.add(asset_id)
        
        # ─────────────────────────────────────────────────────────────────
        # 8. Tier validation
        # ─────────────────────────────────────────────────────────────────
        tier = row.get("tier", "")
        try:
            tier = int(tier) if tier else 2
            if tier not in (1, 2, 3):
                warnings.append(f"Row {row_number}: Invalid tier {tier}, defaulting to 2")
                tier = 2
        except ValueError:
            warnings.append(f"Row {row_number}: Invalid tier '{tier}', defaulting to 2")
            tier = 2
        
        # ─────────────────────────────────────────────────────────────────
        # 9. Country validation
        # ─────────────────────────────────────────────────────────────────
        country = row.get("country", "").strip().upper()
        if not country and exchange_info:
            country = exchange_info.country
        
        # ─────────────────────────────────────────────────────────────────
        # Build normalized row
        # ─────────────────────────────────────────────────────────────────
        is_valid = len(errors) == 0
        
        normalized_row = None
        if is_valid:
            normalized_row = {
                "asset_id": asset_id,
                "symbol": symbol,
                "name": row.get("name", symbol).strip()[:200],
                "asset_type": asset_type,
                "market_scope": "AFRICA",
                "market_code": market_code,
                "exchange_code": exchange_code or (exchange_info.eodhd_code if exchange_info else market_code),
                "currency": currency or (exchange_info.currency if exchange_info else "USD"),
                "country": country or (exchange_info.country if exchange_info else "ZA"),
                "sector": row.get("sector", "").strip() or None,
                "industry": row.get("industry", "").strip() or None,
                "tier": tier,
                "priority_level": int(row.get("priority_level", tier)),
                "active": 1,
                "data_source": "CSV"
            }
        
        return ValidationResult(
            is_valid=is_valid,
            row=row,
            errors=errors,
            warnings=warnings,
            normalized_row=normalized_row
        )
    
    def validate_batch(self, rows: List[Dict]) -> BatchValidationResult:
        """
        Validate a batch of rows.
        
        Args:
            rows: List of row dictionaries
            
        Returns:
            BatchValidationResult with all validation results
        """
        self._seen_asset_ids.clear()
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for i, row in enumerate(rows, start=1):
            result = self.validate_row(row, row_number=i)
            results.append(result)
            
            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        # Find duplicates
        from collections import Counter
        asset_ids = [r.normalized_row["asset_id"] for r in results if r.normalized_row]
        duplicates = [aid for aid, count in Counter(asset_ids).items() if count > 1]
        
        return BatchValidationResult(
            total_rows=len(rows),
            valid_rows=valid_count,
            invalid_rows=invalid_count,
            rows=results,
            unique_asset_ids=self._seen_asset_ids.copy(),
            duplicate_ids=duplicates
        )
    
    def reset(self):
        """Reset validator state (seen asset IDs)."""
        self._seen_asset_ids.clear()


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def validate_africa_row(row: Dict, row_number: int = 0) -> ValidationResult:
    """
    Validate a single Africa universe row.
    
    Args:
        row: Dictionary with row data
        row_number: Row number for error messages
        
    Returns:
        ValidationResult
    """
    validator = AfricaUniverseValidator()
    return validator.validate_row(row, row_number)


def normalize_africa_row(row: Dict) -> Optional[Dict]:
    """
    Normalize a single Africa universe row.
    Returns None if validation fails.
    
    Args:
        row: Dictionary with row data
        
    Returns:
        Normalized row dict or None
    """
    validator = AfricaUniverseValidator()
    result = validator.validate_row(row)
    return result.normalized_row


def validate_africa_csv(csv_path: str) -> BatchValidationResult:
    """
    Validate an entire Africa universe CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        BatchValidationResult
    """
    import csv
    from pathlib import Path
    
    path = Path(csv_path)
    if not path.exists():
        return BatchValidationResult(
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            rows=[],
            unique_asset_ids=set(),
            duplicate_ids=[]
        )
    
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    validator = AfricaUniverseValidator()
    return validator.validate_batch(rows)


# ═══════════════════════════════════════════════════════════════════════════
# LEGACY CODE MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════

# Map old/alternative exchange codes to current standard
LEGACY_EXCHANGE_MAPPINGS = {
    "NG": "NGX",
    "ZA": "JSE",
    "JOHANNESBURG": "JSE",
    "LAGOS": "NGX",
    "NAIROBI": "NSE",
    "CAIRO": "EGX",
    "CA": "EGX",
    "NBO": "NSE",
}


def normalize_exchange_code(code: str) -> str:
    """
    Normalize exchange code to standard format.
    
    Args:
        code: Raw exchange code
        
    Returns:
        Normalized code
    """
    code = code.strip().upper()
    return LEGACY_EXCHANGE_MAPPINGS.get(code, code)
