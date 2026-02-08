"""
MarketGPS Full-Text Search Engine
Uses SQLite FTS5 for fast, fuzzy asset search with graceful degradation.

Provides full-text search capabilities for the asset universe with support for:
- Prefix matching (e.g., "APP*")
- Phrase matching (e.g., '"exact phrase"')
- Boolean operators (AND, OR)
- BM25 relevance ranking
- Snippet highlighting
- Autocomplete suggestions
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""

    asset_id: str
    symbol: str
    name: str
    asset_type: str
    market_scope: str
    market_code: str
    sector: Optional[str] = None
    score: float = 0.0  # BM25 relevance score
    snippet: str = ""  # Highlighted snippet


class SearchEngine:
    """
    SQLite FTS5-based full-text search engine for MarketGPS assets.

    Automatically creates and maintains a virtual FTS5 table mirroring
    the universe table. Supports prefix/phrase/boolean search with
    graceful fallback to LIKE queries if FTS5 unavailable.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize search engine.

        Args:
            db_path: Path to SQLite database. If None, uses environment
                    variable SQLITE_DB_PATH or default storage/marketgps.db
        """
        # Determine database path
        if db_path:
            self.db_path = db_path
        else:
            # Try environment variable first
            db_path_env = os.getenv("SQLITE_DB_PATH")
            if db_path_env:
                self.db_path = db_path_env
            else:
                # Try core.config
                try:
                    from core.config import get_config
                    config = get_config()
                    self.db_path = str(config.storage.sqlite_path)
                except Exception as e:
                    logger.debug(f"Could not load config: {e}, using default path")
                    self.db_path = str(Path(__file__).parent.parent / "storage/marketgps.db")

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.fts_enabled = self._check_fts5_support()

        if self.fts_enabled:
            try:
                self._create_fts_table()
                logger.info(f"SearchEngine initialized with FTS5 at {self.db_path}")
            except Exception as e:
                logger.warning(f"FTS5 table creation failed: {e}. Using LIKE fallback.")
                self.fts_enabled = False
        else:
            logger.info(f"SearchEngine initialized with LIKE fallback at {self.db_path}")

    def _check_fts5_support(self) -> bool:
        """Check if FTS5 extension is available."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Try to enable FTS5
            cursor.execute("PRAGMA compile_options")
            options = [row[0] for row in cursor.fetchall()]

            # Check for ENABLE_FTS5
            has_fts5 = any("FTS5" in opt for opt in options)

            if has_fts5:
                # Further test by trying to create a temp FTS5 table
                try:
                    cursor.execute(
                        "CREATE VIRTUAL TABLE test_fts USING fts5(content)"
                    )
                    cursor.execute("DROP TABLE test_fts")
                    conn.commit()
                    logger.debug("FTS5 extension is available")
                    return True
                except Exception:
                    logger.debug("FTS5 pragma available but creation failed")
                    return False
            else:
                logger.debug("FTS5 not available in compile options")
                return False
        except Exception as e:
            logger.debug(f"Could not check FTS5 support: {e}")
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _create_fts_table(self) -> None:
        """Create FTS5 virtual table for assets."""
        if not self.fts_enabled:
            return

        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Drop existing FTS table if it exists
            cursor.execute("DROP TABLE IF EXISTS assets_fts")

            # Create FTS5 virtual table
            # Note: tokenize='porter' enables stemming for better matching
            cursor.execute("""
                CREATE VIRTUAL TABLE assets_fts USING fts5(
                    asset_id UNINDEXED,
                    symbol,
                    name,
                    asset_type,
                    market_scope UNINDEXED,
                    sector,
                    market_code UNINDEXED,
                    content=universe,
                    content_rowid=asset_id,
                    tokenize='porter'
                )
            """)

            # Populate FTS table from universe
            cursor.execute("""
                INSERT INTO assets_fts(asset_id, symbol, name, asset_type, market_scope, sector, market_code)
                SELECT asset_id, symbol, name, asset_type, market_scope, sector, market_code
                FROM universe
                WHERE active = 1
            """)

            conn.commit()
            logger.info("FTS5 table created and populated successfully")
        except Exception as e:
            logger.error(f"Failed to create FTS5 table: {e}")
            raise
        finally:
            conn.close()

    def rebuild_index(self) -> bool:
        """
        Rebuild the FTS5 index from current universe table.

        Returns:
            True if successful, False otherwise
        """
        if not self.fts_enabled:
            logger.warning("FTS5 not available, rebuild skipped")
            return False

        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            # Rebuild by dropping and recreating
            cursor.execute("DROP TABLE IF EXISTS assets_fts")

            cursor.execute("""
                CREATE VIRTUAL TABLE assets_fts USING fts5(
                    asset_id UNINDEXED,
                    symbol,
                    name,
                    asset_type,
                    market_scope UNINDEXED,
                    sector,
                    market_code UNINDEXED,
                    content=universe,
                    content_rowid=asset_id,
                    tokenize='porter'
                )
            """)

            cursor.execute("""
                INSERT INTO assets_fts(asset_id, symbol, name, asset_type, market_scope, sector, market_code)
                SELECT asset_id, symbol, name, asset_type, market_scope, sector, market_code
                FROM universe
                WHERE active = 1
            """)

            conn.commit()
            logger.info("FTS5 index rebuilt successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to rebuild FTS5 index: {e}")
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def search(
        self,
        query: str,
        limit: int = 20,
        market_scope: Optional[str] = None,
        asset_type: Optional[str] = None,
        offset: int = 0,
    ) -> List[SearchResult]:
        """
        Search for assets using FTS5 with optional filters.

        Args:
            query: Search query (supports prefix*, phrases, AND/OR)
            limit: Maximum results to return (default 20)
            market_scope: Filter by market scope (e.g., 'US_EU', 'AFRICA')
            asset_type: Filter by asset type (e.g., 'EQUITY', 'ETF')
            offset: Result offset for pagination

        Returns:
            List of SearchResult objects ranked by BM25 relevance
        """
        if not query or not query.strip():
            return []

        results = []

        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query based on FTS availability
            if self.fts_enabled:
                results = self._search_fts(
                    cursor,
                    query,
                    limit,
                    market_scope,
                    asset_type,
                    offset,
                )
            else:
                results = self._search_like(
                    cursor,
                    query,
                    limit,
                    market_scope,
                    asset_type,
                    offset,
                )

            return results
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _search_fts(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        market_scope: Optional[str],
        asset_type: Optional[str],
        offset: int,
    ) -> List[SearchResult]:
        """Execute FTS5 search."""
        # Build WHERE clause for filters
        where_clauses = []
        params = [query]

        if market_scope:
            where_clauses.append("u.market_scope = ?")
            params.append(market_scope)

        if asset_type:
            where_clauses.append("u.asset_type = ?")
            params.append(asset_type)

        where_clause = " AND ".join(where_clauses)
        where_clause = f" AND {where_clause}" if where_clause else ""

        try:
            # FTS5 search with BM25 ranking
            sql = f"""
                SELECT
                    u.asset_id,
                    u.symbol,
                    u.name,
                    u.asset_type,
                    u.market_scope,
                    u.market_code,
                    u.sector,
                    fts.rank as relevance_score,
                    fts.symbol as snippet_symbol
                FROM assets_fts fts
                JOIN universe u ON u.asset_id = fts.asset_id
                WHERE assets_fts MATCH ?
                {where_clause}
                ORDER BY fts.rank
                LIMIT ? OFFSET ?
            """

            params.extend([limit, offset])

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                # BM25 score is negative by default, convert to positive
                score = abs(row["relevance_score"]) if row["relevance_score"] else 0.0

                result = SearchResult(
                    asset_id=row["asset_id"],
                    symbol=row["symbol"],
                    name=row["name"],
                    asset_type=row["asset_type"],
                    market_scope=row["market_scope"],
                    market_code=row["market_code"],
                    sector=row["sector"],
                    score=score,
                    snippet=f"{row['symbol']} - {row['name']}",
                )
                results.append(result)

            return results
        except Exception as e:
            logger.warning(f"FTS5 search failed: {e}, falling back to LIKE")
            return self._search_like(cursor, query, limit, market_scope, asset_type, offset)

    def _search_like(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        market_scope: Optional[str],
        asset_type: Optional[str],
        offset: int,
    ) -> List[SearchResult]:
        """Execute LIKE-based search (fallback from FTS5)."""
        # Convert FTS syntax to LIKE patterns
        # Remove FTS operators but keep the core search terms
        search_term = query.replace("*", "%").replace('"', "")

        # Build WHERE clause
        where_clauses = [
            "(u.symbol LIKE ? OR u.name LIKE ? OR u.sector LIKE ?)"
        ]
        params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]

        if market_scope:
            where_clauses.append("u.market_scope = ?")
            params.append(market_scope)

        if asset_type:
            where_clauses.append("u.asset_type = ?")
            params.append(asset_type)

        where_clause = " AND ".join(where_clauses)

        try:
            sql = f"""
                SELECT
                    u.asset_id,
                    u.symbol,
                    u.name,
                    u.asset_type,
                    u.market_scope,
                    u.market_code,
                    u.sector,
                    CASE
                        WHEN u.symbol LIKE ? THEN 1
                        WHEN u.name LIKE ? THEN 2
                        ELSE 3
                    END as relevance
                FROM universe u
                WHERE {where_clause}
                AND u.active = 1
                ORDER BY relevance, u.symbol
                LIMIT ? OFFSET ?
            """

            # Add extra params for CASE sorting
            params.extend([f"%{search_term}%", f"%{search_term}%", limit, offset])

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    asset_id=row["asset_id"],
                    symbol=row["symbol"],
                    name=row["name"],
                    asset_type=row["asset_type"],
                    market_scope=row["market_scope"],
                    market_code=row["market_code"],
                    sector=row["sector"],
                    score=1.0 / (row["relevance"] + 1),  # Simple relevance scoring
                    snippet=f"{row['symbol']} - {row['name']}",
                )
                results.append(result)

            return results
        except Exception as e:
            logger.error(f"LIKE search failed: {e}")
            return []

    def suggest(self, partial: str, limit: int = 5) -> List[str]:
        """
        Get autocomplete suggestions for partial input.

        Args:
            partial: Partial symbol or name (e.g., "APP")
            limit: Maximum suggestions (default 5)

        Returns:
            List of symbol strings sorted by relevance
        """
        if not partial or len(partial) < 1:
            return []

        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Prefix search on symbol (most relevant) then name
            pattern = f"{partial}%"

            if self.fts_enabled:
                # Use FTS for better matching
                try:
                    sql = """
                        SELECT DISTINCT u.symbol
                        FROM assets_fts fts
                        JOIN universe u ON u.asset_id = fts.asset_id
                        WHERE assets_fts MATCH ?
                        AND u.active = 1
                        ORDER BY u.symbol
                        LIMIT ?
                    """
                    cursor.execute(sql, [f"{partial}*", limit])
                except Exception:
                    # Fallback to LIKE
                    sql = """
                        SELECT DISTINCT symbol
                        FROM universe
                        WHERE (symbol LIKE ? OR name LIKE ?)
                        AND active = 1
                        ORDER BY CASE WHEN symbol LIKE ? THEN 0 ELSE 1 END, symbol
                        LIMIT ?
                    """
                    cursor.execute(sql, [pattern, f"%{partial}%", pattern, limit])
            else:
                # Use LIKE search
                sql = """
                    SELECT DISTINCT symbol
                    FROM universe
                    WHERE (symbol LIKE ? OR name LIKE ?)
                    AND active = 1
                    ORDER BY CASE WHEN symbol LIKE ? THEN 0 ELSE 1 END, symbol
                    LIMIT ?
                """
                cursor.execute(sql, [pattern, f"%{partial}%", pattern, limit])

            rows = cursor.fetchall()
            suggestions = [row["symbol"] for row in rows]

            return suggestions
        except Exception as e:
            logger.error(f"Suggest error for '{partial}': {e}")
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_status(self) -> Dict[str, Any]:
        """Get search engine status and statistics."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            # Check if FTS table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='assets_fts'
            """)
            fts_exists = cursor.fetchone() is not None

            # Get universe stats
            cursor.execute("""
                SELECT COUNT(*) as total, COUNT(DISTINCT market_scope) as market_scopes,
                       COUNT(DISTINCT asset_type) as asset_types
                FROM universe WHERE active = 1
            """)
            stats = dict(cursor.fetchone())

            return {
                "db_path": self.db_path,
                "fts_enabled": self.fts_enabled,
                "fts_table_exists": fts_exists,
                "total_assets": stats["total"],
                "market_scopes": stats["market_scopes"],
                "asset_types": stats["asset_types"],
            }
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                "db_path": self.db_path,
                "fts_enabled": self.fts_enabled,
                "error": str(e),
            }
        finally:
            try:
                conn.close()
            except Exception:
                pass


# Module-level functions for convenience

_search_engine: Optional[SearchEngine] = None


def get_search_engine(db_path: Optional[str] = None) -> SearchEngine:
    """Get or create the singleton search engine instance."""
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine(db_path)
    return _search_engine


def search_assets(
    query: str,
    limit: int = 20,
    market_scope: Optional[str] = None,
    asset_type: Optional[str] = None,
) -> List[SearchResult]:
    """
    Convenience function to search assets using the singleton instance.

    Args:
        query: Search query
        limit: Maximum results
        market_scope: Optional market scope filter
        asset_type: Optional asset type filter

    Returns:
        List of SearchResult objects
    """
    engine = get_search_engine()
    return engine.search(query, limit, market_scope, asset_type)


def suggest_assets(partial: str, limit: int = 5) -> List[str]:
    """
    Convenience function for autocomplete suggestions.

    Args:
        partial: Partial symbol or name
        limit: Maximum suggestions

    Returns:
        List of symbol strings
    """
    engine = get_search_engine()
    return engine.suggest(partial, limit)
