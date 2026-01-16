"""Tests for database schema."""
import pytest
import sqlite3
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSchema:
    """Tests for SQLite schema."""
    
    @pytest.fixture
    def db_path(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def conn(self, db_path):
        """Create database connection with schema."""
        conn = sqlite3.connect(db_path)
        
        # Load schema
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path) as f:
                conn.executescript(f.read())
        
        yield conn
        conn.close()
    
    def test_tables_exist(self, conn):
        """Test all required tables exist."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required_tables = {
            "universe",
            "gating_status",
            "pool",
            "rotation_state",
            "scores_latest",
            "scores_history",
            "provider_logs",
            "user_interest",
            "job_runs",
        }
        
        for table in required_tables:
            assert table in tables, f"Missing table: {table}"
    
    def test_indexes_exist(self, conn):
        """Test important indexes exist."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        
        # Check for key indexes
        assert any("universe_symbol" in idx for idx in indexes)
        assert any("scores_total" in idx for idx in indexes)
        assert any("rotation_refresh" in idx for idx in indexes)
    
    def test_universe_insert(self, conn):
        """Test inserting into universe table."""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO universe (asset_id, symbol, name, asset_type)
            VALUES ('EQUITY:AAPL', 'AAPL', 'Apple Inc', 'EQUITY')
        """)
        conn.commit()
        
        cursor.execute("SELECT * FROM universe WHERE asset_id = 'EQUITY:AAPL'")
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == "AAPL"  # symbol column
    
    def test_scores_insert(self, conn):
        """Test inserting into scores_latest table."""
        cursor = conn.cursor()
        
        # First insert asset
        cursor.execute("""
            INSERT INTO universe (asset_id, symbol, name, asset_type)
            VALUES ('EQUITY:TEST', 'TEST', 'Test Corp', 'EQUITY')
        """)
        
        # Then insert score
        cursor.execute("""
            INSERT INTO scores_latest (asset_id, score_total, confidence)
            VALUES ('EQUITY:TEST', 75, 85)
        """)
        conn.commit()
        
        cursor.execute("SELECT score_total, confidence FROM scores_latest WHERE asset_id = 'EQUITY:TEST'")
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 75
        assert row[1] == 85
    
    def test_scores_history_insert(self, conn):
        """Test inserting into scores_history table."""
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO universe (asset_id, symbol, name, asset_type)
            VALUES ('EQUITY:HIST', 'HIST', 'History Test', 'EQUITY')
        """)
        
        cursor.execute("""
            INSERT INTO scores_history (asset_id, score_total, confidence, json_breakdown)
            VALUES ('EQUITY:HIST', 70, 80, '{"version": "1.0"}')
        """)
        conn.commit()
        
        cursor.execute("SELECT json_breakdown FROM scores_history WHERE asset_id = 'EQUITY:HIST'")
        row = cursor.fetchone()
        
        assert row is not None
        assert '"version"' in row[0]
    
    def test_asset_type_constraint(self, conn):
        """Test asset_type constraint."""
        cursor = conn.cursor()
        
        # Valid type should work
        cursor.execute("""
            INSERT INTO universe (asset_id, symbol, name, asset_type)
            VALUES ('ETF:SPY', 'SPY', 'SPDR S&P 500', 'ETF')
        """)
        conn.commit()
        
        # Invalid type should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO universe (asset_id, symbol, name, asset_type)
                VALUES ('INVALID:X', 'X', 'Invalid', 'INVALID_TYPE')
            """)
            conn.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
