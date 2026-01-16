"""
MarketGPS v14.0 - AFRICA Pipeline Module
Production-grade pipeline for African markets.

Modules:
- exchanges_catalog: African exchange definitions
- universe_validator: CSV import validation
- data_fetcher: OHLCV data retrieval
- gating: Africa-specific eligibility rules
- scoring: Africa-adapted scoring engine
- rotation: Complete rotation job with atomic publish

Usage:
    from pipeline.africa import RotationAfricaJob, GatingAfricaJob
    
    # Run rotation with atomic publish
    job = RotationAfricaJob()
    result = job.run(batch_size=50)
"""

from pipeline.africa.exchanges_catalog import (
    AFRICA_EXCHANGES,
    CURRENCY_INFO,
    get_exchange_info,
    get_supported_exchanges,
    is_valid_exchange,
)

from pipeline.africa.universe_validator import (
    AfricaUniverseValidator,
    validate_africa_row,
    normalize_africa_row,
)

from pipeline.africa.gating_africa import (
    GatingAfricaJob,
    compute_coverage_africa,
    compute_stale_ratio_africa,
    compute_liquidity_africa,
    compute_fx_risk,
    compute_liquidity_risk,
)

from pipeline.africa.scoring_africa_v2 import (
    ScoringAfricaEngine,
    AFRICA_SCORING_WEIGHTS,
)

from pipeline.africa.rotation_africa import (
    RotationAfricaJob,
)

from pipeline.africa.data_fetcher_africa import (
    AfricaDataFetcher,
    fetch_bars_africa,
)

__all__ = [
    # Exchanges
    "AFRICA_EXCHANGES",
    "CURRENCY_INFO",
    "get_exchange_info",
    "get_supported_exchanges",
    "is_valid_exchange",
    # Validation
    "AfricaUniverseValidator",
    "validate_africa_row",
    "normalize_africa_row",
    # Gating
    "GatingAfricaJob",
    "compute_coverage_africa",
    "compute_stale_ratio_africa",
    "compute_liquidity_africa",
    "compute_fx_risk",
    "compute_liquidity_risk",
    # Scoring
    "ScoringAfricaEngine",
    "AFRICA_SCORING_WEIGHTS",
    # Rotation
    "RotationAfricaJob",
    # Data
    "AfricaDataFetcher",
    "fetch_bars_africa",
]
