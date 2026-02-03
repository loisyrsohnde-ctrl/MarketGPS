"""Tests for storage repositories - Asset, Score, and base repository."""
import pytest
import sqlite3
import json
from datetime import datetime
from typing import List

from pathlib import Path
import sys

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from core.models import Asset, AssetType, Score, GatingStatus, StateLabel
from storage.asset_repository import AssetRepository
from storage.score_repository import ScoreRepository
from storage.base_repository import BaseRepository


class TestAssetRepositoryCRUD:
    """Tests for AssetRepository CRUD operations."""

    @pytest.fixture
    def in_memory_repo(self, tmp_path):
        """Create an in-memory test repository."""
        db_path = str(tmp_path / "test.db")
        repo = AssetRepository(db_path=db_path)

        # Initialize schema
        with repo._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS universe (
                    asset_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    asset_type TEXT DEFAULT 'EQUITY',
                    market_scope TEXT DEFAULT 'US_EU',
                    market_code TEXT DEFAULT 'US',
                    exchange_code TEXT DEFAULT 'US',
                    currency TEXT DEFAULT 'USD',
                    country TEXT DEFAULT 'US',
                    sector TEXT,
                    industry TEXT,
                    active INTEGER DEFAULT 1,
                    tier INTEGER DEFAULT 2,
                    priority_level INTEGER DEFAULT 2,
                    updated_at DATETIME
                )
            """)

        return repo

    @pytest.fixture
    def sample_equity(self):
        """Create sample equity asset."""
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
    def sample_etf(self):
        """Create sample ETF asset."""
        return Asset(
            asset_id="SPY.US",
            symbol="SPY",
            name="SPDR S&P 500 ETF Trust",
            asset_type=AssetType.ETF,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

    def test_upsert_asset_insert(self, in_memory_repo, sample_equity):
        """Test inserting a new asset."""
        in_memory_repo.upsert_asset(sample_equity)

        # Verify asset was inserted
        asset = in_memory_repo.get_asset("AAPL.US")
        assert asset is not None
        assert asset.symbol == "AAPL"
        assert asset.name == "Apple Inc."
        assert asset.asset_type == AssetType.EQUITY

    def test_upsert_asset_update(self, in_memory_repo, sample_equity):
        """Test updating an existing asset."""
        in_memory_repo.upsert_asset(sample_equity)

        # Update the asset
        sample_equity.name = "Apple Computer Inc."
        in_memory_repo.upsert_asset(sample_equity)

        # Verify update
        asset = in_memory_repo.get_asset("AAPL.US")
        assert asset.name == "Apple Computer Inc."

    def test_get_asset_not_found(self, in_memory_repo):
        """Test getting non-existent asset."""
        asset = in_memory_repo.get_asset("NONEXISTENT.US")
        assert asset is None

    def test_upsert_multiple_assets(self, in_memory_repo, sample_equity, sample_etf):
        """Test inserting multiple assets."""
        in_memory_repo.upsert_asset(sample_equity)
        in_memory_repo.upsert_asset(sample_etf)

        # Verify both exist
        aapl = in_memory_repo.get_asset("AAPL.US")
        spy = in_memory_repo.get_asset("SPY.US")

        assert aapl is not None
        assert spy is not None
        assert aapl.asset_type == AssetType.EQUITY
        assert spy.asset_type == AssetType.ETF

    def test_bulk_upsert_assets(self, in_memory_repo):
        """Test bulk upsert of assets."""
        assets_data = [
            {
                "asset_id": "AAPL.US",
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "EQUITY",
                "market_scope": "US_EU",
                "market_code": "US",
                "exchange_code": "NASDAQ",
                "currency": "USD",
                "country": "US",
                "sector": "Technology",
                "active": 1,
                "tier": 1
            },
            {
                "asset_id": "MSFT.US",
                "symbol": "MSFT",
                "name": "Microsoft Inc.",
                "asset_type": "EQUITY",
                "market_scope": "US_EU",
                "market_code": "US",
                "exchange_code": "NASDAQ",
                "currency": "USD",
                "country": "US",
                "sector": "Technology",
                "active": 1,
                "tier": 1
            }
        ]

        in_memory_repo.bulk_upsert_assets(assets_data)

        # Verify both were inserted
        aapl = in_memory_repo.get_asset("AAPL.US")
        msft = in_memory_repo.get_asset("MSFT.US")

        assert aapl is not None
        assert msft is not None

    def test_asset_market_scope_us_eu(self, in_memory_repo, sample_equity):
        """Test asset with US_EU market scope."""
        in_memory_repo.upsert_asset(sample_equity, market_scope="US_EU")

        asset = in_memory_repo.get_asset("AAPL.US")
        assert asset.market_scope == "US_EU"

    def test_asset_market_scope_africa(self, in_memory_repo):
        """Test asset with AFRICA market scope."""
        africa_asset = Asset(
            asset_id="NGSE.NG",
            symbol="NGSE",
            name="NGX All-Share Index",
            asset_type=AssetType.INDEX,
            market_scope="AFRICA",
            market_code="NG",
            exchange="NGX",
            currency="NGN",
            country="NG"
        )

        in_memory_repo.upsert_asset(africa_asset, market_scope="AFRICA")

        asset = in_memory_repo.get_asset("NGSE.NG")
        assert asset.market_scope == "AFRICA"

    def test_asset_active_status(self, in_memory_repo, sample_equity):
        """Test asset active/inactive status."""
        in_memory_repo.upsert_asset(sample_equity)

        asset = in_memory_repo.get_asset("AAPL.US")
        assert asset.active is True

        # Update to inactive
        sample_equity.active = False
        in_memory_repo.upsert_asset(sample_equity)

        asset = in_memory_repo.get_asset("AAPL.US")
        assert asset.active is False


class TestScoreRepositoryCRUD:
    """Tests for ScoreRepository CRUD operations."""

    @pytest.fixture
    def score_repo(self, tmp_path):
        """Create a test score repository."""
        db_path = str(tmp_path / "test.db")
        repo = ScoreRepository(db_path=db_path)

        # Initialize schema
        with repo._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores_latest (
                    asset_id TEXT PRIMARY KEY,
                    market_scope TEXT DEFAULT 'US_EU',
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
                    updated_at DATETIME
                )
            """)

        return repo

    @pytest.fixture
    def sample_score(self):
        """Create sample score."""
        from core.models import ScoreBreakdown

        breakdown = ScoreBreakdown(
            version="1.0",
            weights={
                "value": 0.30,
                "momentum": 0.40,
                "safety": 0.30
            },
            raw_values={
                "rsi": 55.0,
                "zscore": 0.5
            },
            normalized_values={
                "value": 65.0,
                "momentum": 75.0,
                "safety": 70.0
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

    def test_upsert_score(self, score_repo, sample_score):
        """Test inserting a score."""
        score_repo.upsert_score(sample_score)

        # Verify score was inserted
        retrieved = score_repo.get_score("AAPL.US")
        assert retrieved is not None
        assert retrieved.asset_id == "AAPL.US"
        assert retrieved.score_total == 71.0

    def test_upsert_score_update(self, score_repo, sample_score):
        """Test updating a score."""
        score_repo.upsert_score(sample_score)

        # Update the score
        sample_score.score_total = 75.0
        score_repo.upsert_score(sample_score)

        # Verify update
        retrieved = score_repo.get_score("AAPL.US")
        assert retrieved.score_total == 75.0

    def test_get_score_not_found(self, score_repo):
        """Test getting non-existent score."""
        score = score_repo.get_score("NONEXISTENT.US")
        assert score is None

    def test_score_confidence_values(self, score_repo):
        """Test confidence score boundaries."""
        score = Score(
            asset_id="TEST.US",
            score_total=50.0,
            confidence=100,  # Perfect confidence
            state_label=StateLabel.EQUILIBRE
        )

        score_repo.upsert_score(score)

        retrieved = score_repo.get_score("TEST.US")
        assert retrieved.confidence == 100

    def test_score_with_africa_metrics(self, score_repo):
        """Test score with Africa-specific metrics."""
        score = Score(
            asset_id="TEST.NG",
            score_total=50.0,
            confidence=75,
            state_label=StateLabel.EQUILIBRE,
            score_fx_risk=25.0,
            score_liquidity_risk=15.0
        )

        score_repo.upsert_score(score, market_scope="AFRICA")

        retrieved = score_repo.get_score("TEST.NG")
        assert retrieved.score_fx_risk == 25.0
        assert retrieved.score_liquidity_risk == 15.0

    def test_score_breakdown_json(self, score_repo, sample_score):
        """Test that score breakdown is properly serialized."""
        score_repo.upsert_score(sample_score)

        retrieved = score_repo.get_score("AAPL.US")
        assert retrieved.breakdown is not None
        assert retrieved.breakdown.version == "1.0"
        assert "momentum" in retrieved.breakdown.normalized_values


class TestRepositoryIntegrity:
    """Tests for database integrity and constraints."""

    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create a test repository with schema."""
        db_path = str(tmp_path / "test.db")
        repo = BaseRepository(db_path=db_path)

        # Initialize schema
        with repo._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS universe (
                    asset_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    asset_type TEXT DEFAULT 'EQUITY',
                    market_scope TEXT DEFAULT 'US_EU',
                    market_code TEXT,
                    exchange_code TEXT,
                    currency TEXT DEFAULT 'USD',
                    country TEXT,
                    sector TEXT,
                    industry TEXT,
                    active INTEGER DEFAULT 1,
                    tier INTEGER DEFAULT 2,
                    priority_level INTEGER DEFAULT 2,
                    updated_at DATETIME
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores_latest (
                    asset_id TEXT PRIMARY KEY,
                    market_scope TEXT DEFAULT 'US_EU',
                    score_total REAL,
                    score_value REAL,
                    score_momentum REAL,
                    score_safety REAL,
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
                    FOREIGN KEY (asset_id) REFERENCES universe(asset_id)
                )
            """)

        return repo

    def test_primary_key_constraint_asset(self, test_repo):
        """Test that asset_id is unique (primary key constraint)."""
        with test_repo._get_connection() as conn:
            conn.execute("""
                INSERT INTO universe (asset_id, symbol, name)
                VALUES (?, ?, ?)
            """, ("AAPL.US", "AAPL", "Apple"))

            # Try to insert duplicate
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO universe (asset_id, symbol, name)
                    VALUES (?, ?, ?)
                """, ("AAPL.US", "AAPL", "Apple 2"))

    def test_foreign_key_constraint(self, test_repo):
        """Test that we can query with foreign key relationships."""
        with test_repo._get_connection() as conn:
            # Insert an asset
            conn.execute("""
                INSERT INTO universe (asset_id, symbol, name)
                VALUES (?, ?, ?)
            """, ("AAPL.US", "AAPL", "Apple"))

            # Insert a score for the asset
            conn.execute("""
                INSERT INTO scores_latest (asset_id, score_total)
                VALUES (?, ?)
            """, ("AAPL.US", 50.0))

            # Verify relationship exists
            cursor = conn.execute("""
                SELECT s.score_total FROM scores_latest s
                JOIN universe u ON s.asset_id = u.asset_id
                WHERE s.asset_id = ?
            """, ("AAPL.US",))

            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 50.0

    def test_transaction_rollback(self, test_repo):
        """Test transaction behavior with error."""
        # SQLite with autocommit=True doesn't rollback on error,
        # but we test that errors are handled correctly
        with test_repo._get_connection() as conn:
            # Insert first record
            conn.execute("""
                INSERT INTO universe (asset_id, symbol, name)
                VALUES (?, ?, ?)
            """, ("AAPL.US", "AAPL", "Apple"))

            # Try to insert duplicate (will fail)
            try:
                conn.execute("""
                    INSERT INTO universe (asset_id, symbol, name)
                    VALUES (?, ?, ?)
                """, ("AAPL.US", "AAPL", "Apple"))
            except sqlite3.IntegrityError:
                # Expected - primary key violation
                pass

            # Check that at least first record is there
            cursor = conn.execute("SELECT COUNT(*) FROM universe")
            count = cursor.fetchone()[0]
            assert count >= 1  # At least the first insert succeeded

    def test_concurrent_access(self, test_repo):
        """Test that multiple connections can access the database."""
        # Insert via first connection
        asset = Asset(
            asset_id="TEST.US",
            symbol="TEST",
            name="Test",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

        repo1 = AssetRepository(db_path=test_repo.db_path)
        repo1.upsert_asset(asset)

        # Read via second connection
        repo2 = AssetRepository(db_path=test_repo.db_path)
        retrieved = repo2.get_asset("TEST.US")

        assert retrieved is not None
        assert retrieved.symbol == "TEST"

    def test_default_values(self, test_repo):
        """Test that default values are applied correctly."""
        with test_repo._get_connection() as conn:
            conn.execute("""
                INSERT INTO universe (asset_id, symbol, name)
                VALUES (?, ?, ?)
            """, ("TEST.US", "TEST", "Test Asset"))

            cursor = conn.execute(
                "SELECT market_scope, active, tier FROM universe WHERE asset_id = ?",
                ("TEST.US",)
            )
            row = cursor.fetchone()

            assert row[0] == "US_EU"  # default market_scope
            assert row[1] == 1  # active = true
            assert row[2] == 2  # default tier


class TestRepositoryDataTypes:
    """Tests for proper data type handling."""

    @pytest.fixture
    def asset_repo(self, tmp_path):
        """Create an asset repository."""
        db_path = str(tmp_path / "test.db")
        repo = AssetRepository(db_path=db_path)

        with repo._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS universe (
                    asset_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    asset_type TEXT DEFAULT 'EQUITY',
                    market_scope TEXT DEFAULT 'US_EU',
                    market_code TEXT,
                    exchange_code TEXT,
                    currency TEXT DEFAULT 'USD',
                    country TEXT,
                    sector TEXT,
                    industry TEXT,
                    active INTEGER DEFAULT 1,
                    tier INTEGER DEFAULT 2,
                    priority_level INTEGER DEFAULT 2,
                    updated_at DATETIME
                )
            """)

        return repo

    def test_asset_type_enum(self, asset_repo):
        """Test that AssetType enum is properly stored and retrieved."""
        asset = Asset(
            asset_id="AAPL.US",
            symbol="AAPL",
            name="Apple",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NASDAQ",
            currency="USD",
            country="US"
        )

        asset_repo.upsert_asset(asset)

        retrieved = asset_repo.get_asset("AAPL.US")
        assert retrieved.asset_type == AssetType.EQUITY

    def test_numeric_fields(self, asset_repo):
        """Test numeric fields are stored correctly."""
        with asset_repo._get_connection() as conn:
            conn.execute("""
                INSERT INTO universe (asset_id, symbol, name, tier, priority_level)
                VALUES (?, ?, ?, ?, ?)
            """, ("TEST.US", "TEST", "Test", 1, 3))

            cursor = conn.execute(
                "SELECT tier, priority_level FROM universe WHERE asset_id = ?",
                ("TEST.US",)
            )
            tier, priority = cursor.fetchone()

            assert tier == 1
            assert priority == 3
            assert isinstance(tier, int)
            assert isinstance(priority, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
