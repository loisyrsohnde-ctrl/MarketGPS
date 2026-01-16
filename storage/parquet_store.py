"""
MarketGPS v11.0 - Parquet Storage (SCOPE-AWARE)
Storage for historical OHLCV bar data organized by market scope.

Scopes:
- US_EU: data/parquet/us_eu/bars_daily/
- AFRICA: data/parquet/africa/bars_daily/
"""
from pathlib import Path
from datetime import date, datetime
from typing import Optional, Literal
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from core.config import get_config, get_logger

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]

# Valid scopes
VALID_SCOPES = {"US_EU", "AFRICA"}


class ParquetStore:
    """
    Parquet storage for historical bar data - SCOPE-AWARE.
    Stores data in separate directories per scope for isolation.
    """
    
    def __init__(self, base_dir: Optional[Path] = None, market_scope: MarketScope = "US_EU"):
        """
        Initialize Parquet store for a specific scope.
        
        Args:
            base_dir: Base directory for parquet files
            market_scope: Market scope ("US_EU" or "AFRICA")
        """
        config = get_config()
        self._base_dir = base_dir or config.storage.parquet_dir
        self._market_scope = market_scope if market_scope in VALID_SCOPES else "US_EU"
        
        # Create scope-specific directory
        scope_dir = self._market_scope.lower()  # us_eu or africa
        self._bars_dir = self._base_dir / scope_dir / "bars_daily"
        self._bars_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"ParquetStore initialized for scope {self._market_scope}: {self._bars_dir}")
    
    @property
    def market_scope(self) -> str:
        """Get current market scope."""
        return self._market_scope
    
    @property
    def bars_dir(self) -> Path:
        """Get the bars directory path."""
        return self._bars_dir
    
    def _get_symbol_path(self, asset_id: str) -> Path:
        """
        Get the parquet file path for a symbol.
        
        Args:
            asset_id: Asset identifier (e.g., "AAPL.US", "DANGOTE.NG")
            
        Returns:
            Path to the parquet file
        """
        # Sanitize the asset_id for filesystem
        safe_name = asset_id.replace(".", "_").replace("/", "_").replace(":", "_")
        return self._bars_dir / f"{safe_name}.parquet"
    
    def save_bars(self, asset_id: str, df: pd.DataFrame) -> bool:
        """
        Save daily bars to parquet (overwrites existing).
        
        Args:
            asset_id: Asset identifier
            df: DataFrame with OHLCV data (DatetimeIndex)
            
        Returns:
            True if successful
        """
        if df.empty:
            logger.debug(f"[{self._market_scope}] Empty DataFrame, skipping save for {asset_id}")
            return False
        
        try:
            path = self._get_symbol_path(asset_id)
            
            # Ensure proper column types
            df = df.copy()
            
            # Ensure index is datetime and timezone-naive
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Reset index to make date a column for parquet
            df = df.reset_index()
            df = df.rename(columns={df.columns[0]: "date"})
            
            # Convert to pyarrow table
            table = pa.Table.from_pandas(df, preserve_index=False)
            
            # Write parquet
            pq.write_table(table, path, compression="snappy")
            
            logger.debug(f"[{self._market_scope}] Saved {len(df)} bars for {asset_id} to {path}")
            return True
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to save bars for {asset_id}: {e}")
            return False
    
    def load_bars(self, asset_id: str) -> Optional[pd.DataFrame]:
        """
        Load daily bars from parquet.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            DataFrame with OHLCV data, or None if not found
        """
        try:
            path = self._get_symbol_path(asset_id)
            
            if not path.exists():
                logger.debug(f"[{self._market_scope}] No parquet file found for {asset_id}")
                return None
            
            # Read parquet
            table = pq.read_table(path)
            df = table.to_pandas()
            
            # Set date as index
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
                df.index = df.index.tz_localize(None)
            
            # Sort by date
            df = df.sort_index()
            
            logger.debug(f"[{self._market_scope}] Loaded {len(df)} bars for {asset_id}")
            return df
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to load bars for {asset_id}: {e}")
            return None
    
    def upsert_bars(self, asset_id: str, new_df: pd.DataFrame) -> bool:
        """
        Merge new bars with existing data (incremental update).
        
        Args:
            asset_id: Asset identifier
            new_df: New OHLCV data to merge
            
        Returns:
            True if successful
        """
        if new_df.empty:
            return False
        
        try:
            # Load existing data
            existing_df = self.load_bars(asset_id)
            
            if existing_df is not None and not existing_df.empty:
                # Ensure new_df has datetime index
                new_df = new_df.copy()
                if not isinstance(new_df.index, pd.DatetimeIndex):
                    new_df.index = pd.to_datetime(new_df.index)
                if new_df.index.tz is not None:
                    new_df.index = new_df.index.tz_localize(None)
                
                # Combine and deduplicate
                combined = pd.concat([existing_df, new_df])
                combined = combined[~combined.index.duplicated(keep="last")]
                combined = combined.sort_index()
                
                return self.save_bars(asset_id, combined)
            else:
                return self.save_bars(asset_id, new_df)
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to upsert bars for {asset_id}: {e}")
            return False
    
    def get_last_date(self, asset_id: str) -> Optional[date]:
        """Get the last available date for an asset."""
        try:
            df = self.load_bars(asset_id)
            
            if df is not None and not df.empty:
                last_ts = df.index.max()
                if pd.notna(last_ts):
                    return last_ts.date()
            
            return None
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to get last date for {asset_id}: {e}")
            return None
    
    def get_bar_count(self, asset_id: str) -> int:
        """Get the number of bars stored for an asset."""
        try:
            path = self._get_symbol_path(asset_id)
            
            if not path.exists():
                return 0
            
            # Read metadata only
            metadata = pq.read_metadata(path)
            return metadata.num_rows
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to get bar count for {asset_id}: {e}")
            return 0
    
    def delete_bars(self, asset_id: str) -> bool:
        """Delete bars for an asset."""
        try:
            path = self._get_symbol_path(asset_id)
            
            if path.exists():
                path.unlink()
                logger.info(f"[{self._market_scope}] Deleted bars for {asset_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to delete bars for {asset_id}: {e}")
            return False
    
    def list_symbols(self) -> list:
        """List all symbols with stored data."""
        try:
            symbols = []
            
            for path in self._bars_dir.glob("*.parquet"):
                # Convert filename back to asset_id
                asset_id = path.stem.replace("_", ".")
                symbols.append(asset_id)
            
            return sorted(symbols)
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to list symbols: {e}")
            return []
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics for this scope."""
        try:
            total_files = 0
            total_size = 0
            total_rows = 0
            
            for path in self._bars_dir.glob("*.parquet"):
                total_files += 1
                total_size += path.stat().st_size
                
                try:
                    metadata = pq.read_metadata(path)
                    total_rows += metadata.num_rows
                except Exception:
                    pass
            
            return {
                "scope": self._market_scope,
                "files": total_files,
                "size_mb": round(total_size / (1024 * 1024), 2),
                "total_bars": total_rows
            }
            
        except Exception as e:
            logger.error(f"[{self._market_scope}] Failed to get storage stats: {e}")
            return {"scope": self._market_scope, "files": 0, "size_mb": 0, "total_bars": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_parquet_store(market_scope: MarketScope = "US_EU") -> ParquetStore:
    """
    Factory function to get a ParquetStore for a specific scope.
    
    Args:
        market_scope: "US_EU" or "AFRICA"
        
    Returns:
        ParquetStore instance for the scope
    """
    return ParquetStore(market_scope=market_scope)


def get_parquet_store_us_eu() -> ParquetStore:
    """Get ParquetStore for US/EU scope."""
    return ParquetStore(market_scope="US_EU")


def get_parquet_store_africa() -> ParquetStore:
    """Get ParquetStore for AFRICA scope."""
    return ParquetStore(market_scope="AFRICA")


# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def migrate_existing_data():
    """
    Migrate existing data from flat structure to scope-aware structure.
    Moves data/parquet/bars_daily/* to data/parquet/us_eu/bars_daily/*
    """
    config = get_config()
    old_bars_dir = config.storage.parquet_dir / "bars_daily"
    new_bars_dir = config.storage.parquet_dir / "us_eu" / "bars_daily"
    
    if not old_bars_dir.exists():
        logger.info("No existing data to migrate")
        return
    
    if new_bars_dir.exists() and list(new_bars_dir.glob("*.parquet")):
        logger.info("US_EU data already exists, skipping migration")
        return
    
    new_bars_dir.mkdir(parents=True, exist_ok=True)
    
    import shutil
    migrated = 0
    
    for pq_file in old_bars_dir.glob("*.parquet"):
        dest = new_bars_dir / pq_file.name
        if not dest.exists():
            shutil.copy2(pq_file, dest)
            migrated += 1
    
    logger.info(f"Migrated {migrated} parquet files to US_EU scope")


if __name__ == "__main__":
    # Run migration if executed directly
    migrate_existing_data()
