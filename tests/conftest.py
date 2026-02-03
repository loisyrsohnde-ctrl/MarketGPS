"""
MarketGPS Test Configuration
Provides shared fixtures and utilities for all tests.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import json

# Bootstrap the application
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.bootstrap import bootstrap
bootstrap()

from core.models import (
    Asset, AssetType, Score, StateLabel, GatingStatus,
    ScoreBreakdown, RotationState, WatchlistItem, ProQuota, ProTier
)
from core.config import get_config, reload_config
from storage.base_repository import BaseRepository


# ============================================================================
# FIXTURES: Configuration
# ============================================================================

@pytest.fixture
def test_config():
    """Reload and return fresh config for testing."""
    return reload_config()


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database for testing."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Initialize basic schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            asset_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            name TEXT,
            asset_type TEXT DEFAULT 'EQUITY',
            market_scope TEXT DEFAULT 'US_EU',
            market_code TEXT DEFAULT 'US',
            exchange_code TEXT DEFAULT 'US',
            exchange TEXT DEFAULT 'US',
            currency TEXT DEFAULT 'USD',
            country TEXT DEFAULT 'US',
            sector TEXT,
            industry TEXT,
            isin TEXT,
            active INTEGER DEFAULT 1,
            tier INTEGER DEFAULT 2,
            priority_level INTEGER DEFAULT 2,
            data_source TEXT DEFAULT 'EODHD',
            created_at DATETIME,
            updated_at DATETIME
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            asset_id TEXT PRIMARY KEY,
            score_total REAL,
            score_value REAL,
            score_momentum REAL,
            score_safety REAL,
            score_fx_risk REAL,
            score_liquidity_risk REAL,
            confidence INTEGER DEFAULT 50,
            state_label TEXT DEFAULT 'N/A',
            rsi REAL,
            zscore REAL,
            vol_annual REAL,
            max_drawdown REAL,
            sma200 REAL,
            last_price REAL,
            fundamentals_available INTEGER DEFAULT 0,
            json_breakdown TEXT,
            updated_at DATETIME,
            FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS gating_status (
            asset_id TEXT PRIMARY KEY,
            coverage REAL DEFAULT 0.0,
            liquidity REAL DEFAULT 0.0,
            price_min REAL,
            stale_ratio REAL DEFAULT 0.0,
            eligible INTEGER DEFAULT 0,
            reason TEXT,
            data_confidence INTEGER DEFAULT 50,
            last_bar_date TEXT,
            fx_risk REAL DEFAULT 0.0,
            liquidity_risk REAL DEFAULT 0.0,
            updated_at DATETIME,
            FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rotation_state (
            asset_id TEXT PRIMARY KEY,
            last_refresh_at DATETIME,
            priority_level INTEGER DEFAULT 2,
            in_top50 INTEGER DEFAULT 0,
            cooldown_until DATETIME,
            last_error TEXT,
            refresh_count INTEGER DEFAULT 0,
            FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
        )
    """)

    conn.commit()
    yield db_path
    conn.close()


@pytest.fixture
def test_repo(temp_db):
    """Create a test repository with temporary database."""
    return BaseRepository(db_path=temp_db)


# ============================================================================
# FIXTURES: Sample Data
# ============================================================================

@pytest.fixture
def sample_asset():
    """Sample equity asset for testing."""
    return Asset(
        asset_id="AAPL.US",
        symbol="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.EQUITY,
        market_scope="US_EU",
        market_code="US",
        exchange="NASDAQ",
        currency="USD",
        country="US",
        sector="Technology",
        industry="Consumer Electronics"
    )


@pytest.fixture
def sample_etf():
    """Sample ETF asset for testing."""
    return Asset(
        asset_id="SPY.US",
        symbol="SPY",
        name="SPDR S&P 500 ETF Trust",
        asset_type=AssetType.ETF,
        market_scope="US_EU",
        market_code="US",
        exchange="NYSE",
        currency="USD",
        country="US",
        sector=None,
        industry=None
    )


@pytest.fixture
def sample_crypto():
    """Sample crypto asset for testing."""
    return Asset(
        asset_id="BTC.CC",
        symbol="BTC",
        name="Bitcoin",
        asset_type=AssetType.CRYPTO,
        market_scope="US_EU",
        currency="USD",
        country="US"
    )


@pytest.fixture
def sample_africa_asset():
    """Sample African market asset for testing."""
    return Asset(
        asset_id="NGSEINDEX.BRVM",
        symbol="NGSEINDEX",
        name="NGX All-Share Index",
        asset_type=AssetType.INDEX,
        market_scope="AFRICA",
        market_code="NG",
        exchange_code="BRVM",
        currency="NGN",
        country="NG"
    )


@pytest.fixture
def sample_score():
    """Sample score object for testing."""
    breakdown = ScoreBreakdown(
        version="1.0",
        scoring_date="2026-01-15",
        weights={
            "value": 0.30,
            "momentum": 0.40,
            "safety": 0.30
        },
        features={
            "pe_ratio": 25.5,
            "rsi": 55.0,
            "volatility": 18.5
        },
        normalized={
            "value": 0.65,
            "momentum": 0.75,
            "safety": 0.70
        }
    )

    return Score(
        asset_id="AAPL.US",
        score_total=71.0,
        score_value=65.0,
        score_momentum=75.0,
        score_safety=70.0,
        confidence=85,
        state_label=StateLabel.EQUILIBRE,
        rsi=55.0,
        zscore=0.5,
        vol_annual=18.5,
        max_drawdown=12.3,
        sma200=180.5,
        last_price=185.25,
        fundamentals_available=True,
        breakdown=breakdown
    )


@pytest.fixture
def sample_gating_status():
    """Sample gating status for testing."""
    return GatingStatus(
        asset_id="AAPL.US",
        coverage=0.98,
        liquidity=50_000_000,
        price_min=150.0,
        stale_ratio=0.02,
        eligible=True,
        reason=None,
        data_confidence=95,
        last_bar_date="2026-01-15",
        fx_risk=0.0,
        liquidity_risk=0.0
    )


@pytest.fixture
def sample_rotation_state():
    """Sample rotation state for testing."""
    return RotationState(
        asset_id="AAPL.US",
        last_refresh_at=datetime.now() - timedelta(hours=1),
        priority_level=1,
        in_top50=True,
        cooldown_until=None,
        last_error=None,
        refresh_count=25
    )


@pytest.fixture
def sample_pro_quota():
    """Sample Pro quota for testing."""
    return ProQuota(
        id=1,
        user_id="test_user_123",
        period_start="2026-01-01",
        period_end="2026-02-01",
        calculations_used=50,
        calculations_limit=200,
        tier=ProTier.PRO
    )


@pytest.fixture
def sample_watchlist_item():
    """Sample watchlist item for testing."""
    return WatchlistItem(
        id=1,
        asset_id="AAPL.US",
        user_id="test_user_123",
        notes="Monitor for entry",
        alert_price_above=190.0,
        alert_price_below=170.0,
        alert_score_below=50,
        added_at=datetime.now(),
        symbol="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.EQUITY,
        score_total=71.0,
        last_price=185.25
    )


# ============================================================================
# FIXTURES: Data Utilities
# ============================================================================

@pytest.fixture
def seed_database(test_repo, sample_asset, sample_etf, sample_crypto):
    """Seed test database with sample data."""
    conn = sqlite3.connect(test_repo.db_path)

    # Insert sample assets
    assets = [sample_asset, sample_etf, sample_crypto]
    for asset in assets:
        conn.execute("""
            INSERT INTO assets
            (asset_id, symbol, name, asset_type, market_scope, market_code,
             exchange, currency, country, sector, industry, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset.asset_id, asset.symbol, asset.name, asset.asset_type.value,
            asset.market_scope, asset.market_code, asset.exchange, asset.currency,
            asset.country, asset.sector, asset.industry, 1
        ))

    conn.commit()
    conn.close()

    return test_repo


# ============================================================================
# FIXTURES: Mocking Helpers
# ============================================================================

@pytest.fixture
def mock_logger(caplog):
    """Fixture to capture and inspect logs."""
    return caplog


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# ============================================================================
# PYTEST OPTIONS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection for better organization."""
    for item in items:
        # Auto-mark tests based on file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath) or item.name.startswith("test_"):
            item.add_marker(pytest.mark.unit)
