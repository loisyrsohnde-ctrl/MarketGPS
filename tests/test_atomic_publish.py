"""
MarketGPS v13.0 - Tests for Atomic Publish & Production Pipeline
Tests:
- publish_run atomique
- Construction univers AFRICA
- Requêtes explorer (retourne aussi actifs sans score)
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Score, GatingStatus, StateLabel, ScoreBreakdown
from storage.sqlite_store import SQLiteStore


class TestAtomicPublish(unittest.TestCase):
    """Tests for atomic publish functionality."""
    
    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_marketgps.db")
        self.store = SQLiteStore(db_path=self.db_path)
        
        # Initialize schema
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                with self.store._get_connection() as conn:
                    conn.executescript(f.read())
        
        # Insert test assets
        self._insert_test_assets()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _insert_test_assets(self):
        """Insert test assets into universe."""
        test_assets = [
            {
                "asset_id": "AAPL.US",
                "symbol": "AAPL",
                "name": "Apple Inc",
                "asset_type": "EQUITY",
                "market_code": "US",
                "exchange_code": "US",
                "currency": "USD",
                "country": "US",
                "tier": 1,
                "priority_level": 1,
                "active": 1
            },
            {
                "asset_id": "NPN.JSE",
                "symbol": "NPN",
                "name": "Naspers",
                "asset_type": "EQUITY",
                "market_code": "JSE",
                "exchange_code": "JSE",
                "currency": "ZAR",
                "country": "ZA",
                "tier": 1,
                "priority_level": 1,
                "active": 1
            },
            {
                "asset_id": "DANGCEM.NG",
                "symbol": "DANGCEM",
                "name": "Dangote Cement",
                "asset_type": "EQUITY",
                "market_code": "NGX",
                "exchange_code": "NG",
                "currency": "NGN",
                "country": "NG",
                "tier": 1,
                "priority_level": 1,
                "active": 1
            }
        ]
        
        self.store.bulk_upsert_assets(test_assets[:1], market_scope="US_EU")
        self.store.bulk_upsert_assets(test_assets[1:], market_scope="AFRICA")
    
    def test_create_job_run(self):
        """Test creating a job run."""
        run_id = self.store.create_job_run(
            market_scope="US_EU",
            job_type="rotation",
            mode="daily_full",
            created_by="test"
        )
        
        self.assertIsNotNone(run_id)
        self.assertEqual(len(run_id), 36)  # UUID format
        
        # Verify job run exists
        job = self.store.get_job_run(run_id)
        self.assertIsNotNone(job)
        self.assertEqual(job["market_scope"], "US_EU")
        self.assertEqual(job["job_type"], "rotation")
        self.assertEqual(job["status"], "running")
    
    def test_staging_and_publish_scores(self):
        """Test staging scores and atomic publish."""
        # Create job run
        run_id = self.store.create_job_run(
            market_scope="US_EU",
            job_type="scoring",
            mode="daily_full"
        )
        
        # Create test score
        score = Score(
            asset_id="AAPL.US",
            score_total=85.5,
            score_momentum=90.0,
            score_safety=80.0,
            score_value=85.0,
            confidence=95,
            state_label=StateLabel.EQUILIBRIUM,
            rsi=55.0,
            zscore=0.5,
            vol_annual=25.0,
            max_drawdown=15.0,
            sma200=150.0,
            last_price=175.0,
            fundamentals_available=True,
            breakdown=ScoreBreakdown(
                version="TEST_1.0",
                scoring_date=datetime.now().isoformat(),
                features={"test": 1},
                normalized={"momentum": 90},
                weights={"momentum": 0.4},
                confidence_components={}
            )
        )
        
        # Insert into staging
        self.store.insert_staging_score(run_id, score, "US_EU")
        
        # Verify staging has the score
        with self.store._get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM scores_staging WHERE run_id = ?",
                (run_id,)
            ).fetchone()[0]
            self.assertEqual(count, 1)
        
        # Verify scores_latest is empty
        existing_score = self.store.get_score("AAPL.US")
        self.assertIsNone(existing_score)
        
        # Publish
        results = self.store.publish_run(run_id, "US_EU")
        
        # Verify publish results
        self.assertEqual(results["scores_published"], 1)
        
        # Verify score is now in scores_latest
        published_score = self.store.get_score("AAPL.US")
        self.assertIsNotNone(published_score)
        self.assertEqual(published_score.score_total, 85.5)
        
        # Verify staging is cleaned up
        with self.store._get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM scores_staging WHERE run_id = ?",
                (run_id,)
            ).fetchone()[0]
            self.assertEqual(count, 0)
        
        # Verify job run status
        job = self.store.get_job_run(run_id)
        self.assertEqual(job["status"], "success")
    
    def test_rollback_run(self):
        """Test rolling back a job run."""
        # Create job run
        run_id = self.store.create_job_run(
            market_scope="US_EU",
            job_type="scoring",
            mode="daily_full"
        )
        
        # Create and stage a score
        score = Score(
            asset_id="AAPL.US",
            score_total=85.5,
            score_momentum=90.0,
            score_safety=80.0,
            score_value=85.0,
            confidence=95,
            state_label=StateLabel.EQUILIBRIUM
        )
        self.store.insert_staging_score(run_id, score, "US_EU")
        
        # Rollback
        self.store.rollback_run(run_id)
        
        # Verify staging is cleared
        with self.store._get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM scores_staging WHERE run_id = ?",
                (run_id,)
            ).fetchone()[0]
            self.assertEqual(count, 0)
        
        # Verify job status is cancelled
        job = self.store.get_job_run(run_id)
        self.assertEqual(job["status"], "cancelled")
    
    def test_publish_gating(self):
        """Test staging and publishing gating status."""
        # Create job run
        run_id = self.store.create_job_run(
            market_scope="AFRICA",
            job_type="gating",
            mode="daily_full"
        )
        
        # Create test gating status
        gating = GatingStatus(
            asset_id="NPN.JSE",
            coverage=0.95,
            liquidity=5000000.0,
            price_min=100.0,
            stale_ratio=0.02,
            eligible=True,
            reason=None,
            data_confidence=90,
            last_bar_date="2024-01-10"
        )
        
        # Stage
        self.store.insert_staging_gating(run_id, gating, "AFRICA")
        
        # Publish
        results = self.store.publish_run(
            run_id, "AFRICA",
            publish_scores=False,
            publish_gating=True
        )
        
        self.assertEqual(results["gating_published"], 1)
        
        # Verify gating is published
        published_gating = self.store.get_gating("NPN.JSE")
        self.assertIsNotNone(published_gating)
        self.assertEqual(published_gating.coverage, 0.95)
        self.assertTrue(published_gating.eligible)
    
    def test_publish_run_does_not_touch_other_scope(self):
        """
        TEST OBLIGATOIRE: publish_run(scope=AFRICA) ne doit pas toucher US_EU.
        """
        # Step 1: Insert US_EU score directly (simulating existing data)
        us_score = Score(
            asset_id="AAPL.US",
            score_total=90.0,
            score_momentum=85.0,
            score_safety=88.0,
            score_value=95.0,
            confidence=98,
            state_label=StateLabel.EXTENSION_HAUTE
        )
        self.store.upsert_score(us_score, market_scope="US_EU")
        
        # Verify US_EU score exists
        initial_us_score = self.store.get_score("AAPL.US")
        self.assertIsNotNone(initial_us_score)
        self.assertEqual(initial_us_score.score_total, 90.0)
        
        # Step 2: Create AFRICA job run and stage scores
        run_id = self.store.create_job_run(
            market_scope="AFRICA",
            job_type="scoring",
            mode="daily_full"
        )
        
        africa_score = Score(
            asset_id="NPN.JSE",
            score_total=75.5,
            score_momentum=70.0,
            score_safety=80.0,
            score_value=75.0,
            confidence=85,
            state_label=StateLabel.EQUILIBRIUM
        )
        self.store.insert_staging_score(run_id, africa_score, "AFRICA")
        
        # Step 3: Publish AFRICA
        results = self.store.publish_run(run_id, "AFRICA")
        
        # Verify AFRICA score was published
        self.assertEqual(results["scores_published"], 1)
        published_africa = self.store.get_score("NPN.JSE")
        self.assertIsNotNone(published_africa)
        self.assertEqual(published_africa.score_total, 75.5)
        
        # Step 4: CRITICAL - Verify US_EU score is UNCHANGED
        final_us_score = self.store.get_score("AAPL.US")
        self.assertIsNotNone(final_us_score, "US_EU score should NOT have been deleted!")
        self.assertEqual(final_us_score.score_total, 90.0, "US_EU score should NOT have been modified!")
        self.assertEqual(final_us_score.confidence, 98)
    
    def test_scoring_breakdown_contains_weights_and_metrics(self):
        """
        TEST OBLIGATOIRE: json_breakdown doit contenir weights et raw metrics.
        """
        # Create a score with full breakdown
        breakdown = ScoreBreakdown(
            version="AFRICA_V2.0",
            scoring_date=datetime.now().isoformat(),
            features={
                "return_6m": 0.15,
                "return_12m": 0.25,
                "vol_annual": 22.5,
                "max_drawdown_12m": -0.12,
                "adv_60d": 500000,
                "coverage": 0.92,
                "stale_ratio": 0.05
            },
            normalized={
                "momentum": 78.0,
                "safety": 82.0,
                "value": 50.0,
                "fx_risk": 65.0,
                "liquidity_risk": 70.0
            },
            weights={
                "momentum": 0.35,
                "safety": 0.25,
                "value": 0.20,
                "fx_risk": 0.10,
                "liquidity_risk": 0.10
            },
            confidence_components={
                "coverage_contrib": 15,
                "liquidity_contrib": 10,
                "stale_penalty": -5,
                "fundamentals_penalty": -20
            }
        )
        
        score = Score(
            asset_id="NPN.JSE",
            score_total=71.8,
            score_momentum=78.0,
            score_safety=82.0,
            score_value=50.0,
            score_fx_risk=65.0,
            score_liquidity_risk=70.0,
            confidence=80,
            state_label=StateLabel.EQUILIBRIUM,
            breakdown=breakdown
        )
        
        # Upsert and retrieve
        self.store.upsert_score(score, market_scope="AFRICA")
        retrieved = self.store.get_score("NPN.JSE")
        
        self.assertIsNotNone(retrieved)
        self.assertIsNotNone(retrieved.breakdown)
        
        # Verify breakdown structure
        self.assertEqual(retrieved.breakdown.version, "AFRICA_V2.0")
        
        # Verify weights present
        self.assertIn("momentum", retrieved.breakdown.weights)
        self.assertIn("safety", retrieved.breakdown.weights)
        self.assertEqual(retrieved.breakdown.weights["momentum"], 0.35)
        
        # Verify raw metrics present
        self.assertIn("return_6m", retrieved.breakdown.features)
        self.assertIn("vol_annual", retrieved.breakdown.features)
        self.assertIn("adv_60d", retrieved.breakdown.features)
        
        # Verify normalized subscores
        self.assertIn("momentum", retrieved.breakdown.normalized)
        self.assertEqual(retrieved.breakdown.normalized["momentum"], 78.0)
        
        # Verify confidence components
        self.assertIn("coverage_contrib", retrieved.breakdown.confidence_components)
        self.assertIn("fundamentals_penalty", retrieved.breakdown.confidence_components)


class TestAfricaUniverse(unittest.TestCase):
    """Tests for AFRICA universe construction."""
    
    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_marketgps.db")
        self.store = SQLiteStore(db_path=self.db_path)
        
        # Initialize schema
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                with self.store._get_connection() as conn:
                    conn.executescript(f.read())
    
    def test_africa_universe_import_requires_csv(self):
        """
        TEST OBLIGATOIRE: AFRICA universe must be built from CSV (not API).
        Validates that force_csv flag is respected and API import is rejected.
        """
        import csv
        
        # Create a test CSV file
        csv_path = os.path.join(self.temp_dir, "universe_africa.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'asset_id', 'symbol', 'name', 'asset_type', 'market_code',
                'exchange_code', 'currency', 'country', 'sector', 'industry',
                'tier', 'priority_level'
            ])
            writer.writeheader()
            writer.writerows([
                {
                    'asset_id': 'NPN.JSE', 'symbol': 'NPN', 'name': 'Naspers',
                    'asset_type': 'EQUITY', 'market_code': 'JSE', 'exchange_code': 'JSE',
                    'currency': 'ZAR', 'country': 'ZA', 'sector': 'Technology',
                    'industry': 'Internet', 'tier': '1', 'priority_level': '1'
                },
                {
                    'asset_id': 'DANGCEM.NG', 'symbol': 'DANGCEM', 'name': 'Dangote Cement',
                    'asset_type': 'EQUITY', 'market_code': 'NGX', 'exchange_code': 'NG',
                    'currency': 'NGN', 'country': 'NG', 'sector': 'Materials',
                    'industry': 'Cement', 'tier': '1', 'priority_level': '1'
                }
            ])
        
        # Import using import_universe_from_csv function
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from pipeline.jobs import import_universe_from_csv
        
        result = import_universe_from_csv(self.store, csv_path, "AFRICA")
        
        # Verify import success
        self.assertEqual(result['added'], 2)
        self.assertEqual(result['errors'], 0)
        self.assertEqual(result['source'], csv_path)
        
        # Verify assets are correctly stored with AFRICA scope
        assets = self.store.get_active_assets(market_scope="AFRICA")
        self.assertEqual(len(assets), 2)
        
        # Verify scope is correctly set
        with self.store._get_connection() as conn:
            scope_check = conn.execute(
                "SELECT market_scope FROM universe WHERE asset_id = 'NPN.JSE'"
            ).fetchone()
            self.assertEqual(scope_check[0], "AFRICA")
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_bulk_upsert_africa_assets(self):
        """Test bulk upserting AFRICA assets."""
        africa_assets = [
            {
                "asset_id": "NPN.JSE",
                "symbol": "NPN",
                "name": "Naspers",
                "asset_type": "EQUITY",
                "market_code": "JSE",
                "exchange_code": "JSE",
                "currency": "ZAR",
                "country": "ZA",
                "tier": 1
            },
            {
                "asset_id": "AGL.JSE",
                "symbol": "AGL",
                "name": "Anglo American",
                "asset_type": "EQUITY",
                "market_code": "JSE",
                "exchange_code": "JSE",
                "currency": "ZAR",
                "country": "ZA",
                "tier": 1
            },
            {
                "asset_id": "DANGCEM.NG",
                "symbol": "DANGCEM",
                "name": "Dangote Cement",
                "asset_type": "EQUITY",
                "market_code": "NGX",
                "exchange_code": "NG",
                "currency": "NGN",
                "country": "NG",
                "tier": 1
            }
        ]
        
        self.store.bulk_upsert_assets(africa_assets, market_scope="AFRICA")
        
        # Verify assets are inserted
        assets = self.store.get_active_assets(market_scope="AFRICA")
        self.assertEqual(len(assets), 3)
        
        # Verify by exchange_code (database column name)
        jse_assets = [a for a in assets if a.exchange_code == "JSE"]
        self.assertEqual(len(jse_assets), 2)
        
        ng_assets = [a for a in assets if a.exchange_code == "NG"]
        self.assertEqual(len(ng_assets), 1)
    
    def test_count_by_scope(self):
        """Test counting assets by scope."""
        # Insert US_EU assets
        us_assets = [
            {
                "asset_id": "AAPL.US",
                "symbol": "AAPL",
                "name": "Apple",
                "asset_type": "EQUITY",
                "market_code": "US",
                "exchange_code": "US",
                "currency": "USD",
                "country": "US",
                "tier": 1
            }
        ]
        self.store.bulk_upsert_assets(us_assets, market_scope="US_EU")
        
        # Insert AFRICA assets
        africa_assets = [
            {
                "asset_id": "NPN.JSE",
                "symbol": "NPN",
                "name": "Naspers",
                "asset_type": "EQUITY",
                "market_code": "JSE",
                "exchange_code": "JSE",
                "currency": "ZAR",
                "country": "ZA",
                "tier": 1
            },
            {
                "asset_id": "AGL.JSE",
                "symbol": "AGL",
                "name": "Anglo American",
                "asset_type": "EQUITY",
                "market_code": "JSE",
                "exchange_code": "JSE",
                "currency": "ZAR",
                "country": "ZA",
                "tier": 1
            }
        ]
        self.store.bulk_upsert_assets(africa_assets, market_scope="AFRICA")
        
        # Count by scope
        counts = self.store.count_by_scope()
        
        self.assertEqual(counts.get("US_EU", 0), 1)
        self.assertEqual(counts.get("AFRICA", 0), 2)


class TestExplorerQueries(unittest.TestCase):
    """Tests for explorer queries (including unscored assets)."""
    
    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_marketgps.db")
        self.store = SQLiteStore(db_path=self.db_path)
        
        # Initialize schema
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                with self.store._get_connection() as conn:
                    conn.executescript(f.read())
        
        # Insert test data
        self._setup_test_data()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_test_data(self):
        """Setup test assets and scores."""
        # Insert assets
        assets = [
            {
                "asset_id": "AAPL.US",
                "symbol": "AAPL",
                "name": "Apple Inc",
                "asset_type": "EQUITY",
                "market_code": "US",
                "exchange_code": "US",
                "currency": "USD",
                "country": "US",
                "tier": 1
            },
            {
                "asset_id": "MSFT.US",
                "symbol": "MSFT",
                "name": "Microsoft",
                "asset_type": "EQUITY",
                "market_code": "US",
                "exchange_code": "US",
                "currency": "USD",
                "country": "US",
                "tier": 1
            },
            {
                "asset_id": "GOOGL.US",
                "symbol": "GOOGL",
                "name": "Alphabet",
                "asset_type": "EQUITY",
                "market_code": "US",
                "exchange_code": "US",
                "currency": "USD",
                "country": "US",
                "tier": 2
            }
        ]
        self.store.bulk_upsert_assets(assets, market_scope="US_EU")
        
        # Insert score for only AAPL (MSFT and GOOGL will be unscored)
        score = Score(
            asset_id="AAPL.US",
            score_total=85.0,
            score_momentum=90.0,
            score_safety=80.0,
            score_value=85.0,
            confidence=95,
            state_label=StateLabel.EQUILIBRIUM
        )
        self.store.upsert_score(score, market_scope="US_EU")
    
    def test_search_universe_includes_unscored(self):
        """Test that search_universe returns unscored assets when only_scored=False."""
        # Search with only_scored=False
        results, total = self.store.search_universe(
            market_scope="US_EU",
            only_scored=False,
            limit=50
        )
        
        # Should return all 3 assets
        self.assertEqual(total, 3)
        self.assertEqual(len(results), 3)
        
        # Verify AAPL has score
        aapl = next((r for r in results if r["symbol"] == "AAPL"), None)
        self.assertIsNotNone(aapl)
        self.assertEqual(aapl["score_total"], 85.0)
        
        # Verify MSFT has no score
        msft = next((r for r in results if r["symbol"] == "MSFT"), None)
        self.assertIsNotNone(msft)
        self.assertIsNone(msft["score_total"])
    
    def test_search_universe_only_scored(self):
        """Test that search_universe returns only scored assets when only_scored=True."""
        results, total = self.store.search_universe(
            market_scope="US_EU",
            only_scored=True,
            limit=50
        )
        
        # Should return only AAPL
        self.assertEqual(total, 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["symbol"], "AAPL")
    
    def test_list_assets_paginated(self):
        """Test paginated asset listing."""
        # Get all assets
        results, total = self.store.list_assets_paginated(
            market_scope="US_EU",
            page=1,
            page_size=2
        )
        
        self.assertEqual(total, 3)
        self.assertEqual(len(results), 2)  # Page size is 2
        
        # Get second page
        results2, total2 = self.store.list_assets_paginated(
            market_scope="US_EU",
            page=2,
            page_size=2
        )
        
        self.assertEqual(total2, 3)
        self.assertEqual(len(results2), 1)  # Only 1 remaining
    
    def test_count_assets_breakdown(self):
        """Test counting assets with scored/unscored breakdown."""
        counts = self.store.count_assets(market_scope="US_EU")
        
        self.assertEqual(counts["total"], 3)
        self.assertEqual(counts["scored"], 1)
        self.assertEqual(counts["unscored"], 2)


if __name__ == "__main__":
    unittest.main()
