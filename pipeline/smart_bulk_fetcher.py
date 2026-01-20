"""
MarketGPS - Smart Bulk Fetcher (API Optimization)
Uses EODHD bulk endpoints to minimize API calls.

STRATEGY:
- Instead of 1 API call per asset (N calls for N assets)
- Use 1 bulk call per exchange (M calls for M exchanges)
- This reduces 20,000 calls to ~30 calls!

Usage:
    python -m pipeline.smart_bulk_fetcher --scope US_EU
    python -m pipeline.smart_bulk_fetcher --scope AFRICA
"""
import os
import sys
import time
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from providers.eodhd import EODHDProvider

logger = get_logger(__name__)


class SmartBulkFetcher:
    """
    Fetches price data using EODHD bulk endpoints.
    
    Key Optimization:
    - bulk_eod endpoint: 1 call = all symbols for 1 exchange for 1 day
    - We call this for the LAST trading day only
    - Then identify which assets need full history fetch
    
    API Call Reduction:
    - Before: 20,000 assets × 1 call = 20,000 calls
    - After: 30 exchanges × 1 bulk call = 30 calls (for daily update)
    - Full history only fetched for NEW assets
    """
    
    # Exchange groupings by market scope
    US_EU_EXCHANGES = [
        "US",      # USA (NYSE, NASDAQ, AMEX)
        "LSE",     # London
        "PA",      # Paris (Euronext)
        "XETRA",   # Frankfurt
        "AS",      # Amsterdam
        "SW",      # Switzerland
        "MI",      # Milan
        "MC",      # Madrid
        "BR",      # Brussels
        "LIS",     # Lisbon
        "VI",      # Vienna
        "HE",      # Helsinki
        "ST",      # Stockholm
        "CO",      # Copenhagen
        "OL",      # Oslo
        "IR",      # Ireland
    ]
    
    AFRICA_EXCHANGES = [
        "JSE",     # Johannesburg (South Africa)
        "NG",      # Nigeria (NGX)
        "CA",      # Cairo (Egypt)
        "BRVM",    # West Africa (BRVM)
    ]
    
    def __init__(self, market_scope: str = "US_EU"):
        """
        Initialize the bulk fetcher.
        
        Args:
            market_scope: US_EU or AFRICA
        """
        self._scope = market_scope
        self._config = get_config()
        self._store = SQLiteStore()
        self._parquet = ParquetStore(market_scope=market_scope)
        self._provider = EODHDProvider()
        
        # Select exchanges based on scope
        self._exchanges = (
            self.US_EU_EXCHANGES if market_scope == "US_EU" 
            else self.AFRICA_EXCHANGES
        )
        
        if not self._provider.is_configured:
            raise RuntimeError("EODHD API key not configured")
    
    def fetch_bulk_latest(self) -> Dict[str, Dict]:
        """
        Fetch latest EOD data for ALL assets using bulk endpoint.
        
        Returns:
            Dict mapping asset_id to latest price data
        """
        logger.info(f"[{self._scope}] Fetching bulk EOD for {len(self._exchanges)} exchanges")
        
        all_data = {}
        
        for exchange in self._exchanges:
            try:
                logger.info(f"  Fetching bulk EOD for {exchange}...")
                
                # Get bulk data for today (or last trading day)
                bulk_data = self._provider.get_bulk_eod(exchange)
                
                if not bulk_data:
                    logger.warning(f"  No bulk data for {exchange}")
                    continue
                
                # Process each symbol
                for item in bulk_data:
                    symbol = item.get("code", "")
                    if not symbol:
                        continue
                    
                    asset_id = f"{symbol}.{exchange}"
                    all_data[asset_id] = {
                        "date": item.get("date"),
                        "open": item.get("open"),
                        "high": item.get("high"),
                        "low": item.get("low"),
                        "close": item.get("close"),
                        "adjusted_close": item.get("adjusted_close"),
                        "volume": item.get("volume"),
                        "exchange": exchange,
                    }
                
                logger.info(f"  {exchange}: {len(bulk_data)} symbols")
                
                # Small delay between exchanges
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"  Bulk fetch failed for {exchange}: {e}")
                continue
        
        logger.info(f"[{self._scope}] Total bulk data: {len(all_data)} assets")
        return all_data
    
    def identify_new_assets(self, bulk_data: Dict[str, Dict]) -> List[str]:
        """
        Identify assets that need full history (no Parquet file exists).
        
        Args:
            bulk_data: Dict of asset_id to latest data
            
        Returns:
            List of asset_ids needing full history
        """
        new_assets = []
        
        for asset_id in bulk_data.keys():
            # Check if Parquet file exists
            parquet_path = self._parquet._get_symbol_path(asset_id)
            
            if not parquet_path.exists():
                new_assets.append(asset_id)
        
        logger.info(f"[{self._scope}] Found {len(new_assets)} new assets needing full history")
        return new_assets
    
    def fetch_full_history(
        self,
        asset_ids: List[str],
        years: int = 5,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Fetch full history for new assets (individual calls).
        
        Args:
            asset_ids: Assets to fetch
            years: Years of history
            batch_size: Batch size for rate limiting
            
        Returns:
            Dict with fetch stats
        """
        stats = {"success": 0, "failed": 0, "skipped": 0}
        
        start_date = date.today() - timedelta(days=years * 365)
        end_date = date.today()
        
        logger.info(f"[{self._scope}] Fetching full history for {len(asset_ids)} assets")
        
        for i, asset_id in enumerate(asset_ids):
            try:
                # Progress log every batch
                if i > 0 and i % batch_size == 0:
                    logger.info(f"  Progress: {i}/{len(asset_ids)} ({stats['success']} success)")
                    time.sleep(1)  # Rate limiting pause
                
                # Fetch from EODHD
                df = self._provider.fetch_daily_bars(
                    asset_id,
                    start=start_date,
                    end=end_date
                )
                
                if df is None or df.empty:
                    stats["skipped"] += 1
                    continue
                
                # Save to Parquet
                self._parquet.upsert_bars(asset_id, df)
                stats["success"] += 1
                
            except Exception as e:
                logger.warning(f"  Failed to fetch {asset_id}: {e}")
                stats["failed"] += 1
        
        logger.info(f"[{self._scope}] Full history: {stats['success']} success, {stats['failed']} failed, {stats['skipped']} skipped")
        return stats
    
    def update_existing_assets(
        self,
        bulk_data: Dict[str, Dict],
        existing_assets: Set[str]
    ) -> Dict[str, int]:
        """
        Update existing Parquet files with latest data from bulk fetch.
        
        This is MUCH faster than individual API calls!
        
        Args:
            bulk_data: Bulk EOD data
            existing_assets: Asset IDs that have Parquet files
            
        Returns:
            Dict with update stats
        """
        stats = {"updated": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"[{self._scope}] Updating {len(existing_assets)} existing assets from bulk data")
        
        for asset_id in existing_assets:
            if asset_id not in bulk_data:
                stats["skipped"] += 1
                continue
            
            try:
                item = bulk_data[asset_id]
                
                # Create single-row DataFrame
                new_row = pd.DataFrame([{
                    "Date": pd.to_datetime(item["date"]),
                    "Open": item["open"],
                    "High": item["high"],
                    "Low": item["low"],
                    "Close": item["close"],
                    "Volume": item["volume"],
                    "Adj Close": item.get("adjusted_close", item["close"]),
                }])
                new_row = new_row.set_index("Date")
                
                # Upsert to Parquet (handles deduplication)
                self._parquet.upsert_bars(asset_id, new_row)
                stats["updated"] += 1
                
            except Exception as e:
                logger.debug(f"  Failed to update {asset_id}: {e}")
                stats["failed"] += 1
        
        logger.info(f"[{self._scope}] Updated: {stats['updated']} assets")
        return stats
    
    def sync_universe(self, bulk_data: Dict[str, Dict]) -> Dict[str, int]:
        """
        Sync universe table with bulk data (add missing assets).
        
        Args:
            bulk_data: Bulk EOD data
            
        Returns:
            Dict with sync stats
        """
        stats = {"added": 0, "existing": 0}
        
        for asset_id, data in bulk_data.items():
            try:
                # Check if exists
                existing = self._store.get_asset(asset_id)
                
                if existing:
                    stats["existing"] += 1
                    continue
                
                # Extract symbol and exchange
                parts = asset_id.rsplit(".", 1)
                symbol = parts[0]
                exchange = parts[1] if len(parts) > 1 else "US"
                
                # Insert new asset (inactive by default, tier 2)
                from core.models import Asset, AssetType
                
                asset = Asset(
                    asset_id=asset_id,
                    symbol=symbol,
                    name=symbol,  # Will be updated later
                    asset_type=AssetType.EQUITY,  # Default
                    exchange=exchange,
                    currency="USD",
                    active=False,  # Not active until gating
                    tier=2,
                )
                
                self._store.upsert_asset(asset)
                stats["added"] += 1
                
            except Exception:
                continue
        
        logger.info(f"[{self._scope}] Universe sync: {stats['added']} added, {stats['existing']} existing")
        return stats
    
    def run(
        self,
        fetch_new_history: bool = True,
        history_years: int = 5,
        limit_new: Optional[int] = None
    ) -> Dict:
        """
        Run the smart bulk fetch pipeline.
        
        Args:
            fetch_new_history: Whether to fetch full history for new assets
            history_years: Years of history to fetch
            limit_new: Limit number of new assets to fetch history for
            
        Returns:
            Dict with all stats
        """
        start_time = time.time()
        results = {
            "scope": self._scope,
            "exchanges": len(self._exchanges),
            "bulk_fetch": {},
            "new_assets": {},
            "updated": {},
            "universe_sync": {},
        }
        
        # Step 1: Bulk fetch latest data
        logger.info("=" * 60)
        logger.info("STEP 1: Bulk fetch latest EOD data")
        logger.info("=" * 60)
        bulk_data = self.fetch_bulk_latest()
        results["bulk_fetch"]["total"] = len(bulk_data)
        
        # Step 2: Sync universe
        logger.info("=" * 60)
        logger.info("STEP 2: Sync universe table")
        logger.info("=" * 60)
        results["universe_sync"] = self.sync_universe(bulk_data)
        
        # Step 3: Identify existing vs new assets
        logger.info("=" * 60)
        logger.info("STEP 3: Identify new vs existing assets")
        logger.info("=" * 60)
        
        new_asset_ids = self.identify_new_assets(bulk_data)
        existing_asset_ids = set(bulk_data.keys()) - set(new_asset_ids)
        
        results["new_assets"]["count"] = len(new_asset_ids)
        results["updated"]["existing_count"] = len(existing_asset_ids)
        
        # Step 4: Update existing assets with bulk data (FREE - no API calls!)
        logger.info("=" * 60)
        logger.info("STEP 4: Update existing assets (no API calls)")
        logger.info("=" * 60)
        update_stats = self.update_existing_assets(bulk_data, existing_asset_ids)
        results["updated"].update(update_stats)
        
        # Step 5: Fetch full history for new assets (API calls)
        if fetch_new_history and new_asset_ids:
            logger.info("=" * 60)
            logger.info("STEP 5: Fetch full history for new assets")
            logger.info("=" * 60)
            
            # Apply limit if specified
            if limit_new and len(new_asset_ids) > limit_new:
                logger.info(f"  Limiting to {limit_new} new assets")
                new_asset_ids = new_asset_ids[:limit_new]
            
            history_stats = self.fetch_full_history(
                new_asset_ids,
                years=history_years
            )
            results["new_assets"].update(history_stats)
        
        # Summary
        duration = time.time() - start_time
        results["duration_seconds"] = round(duration, 1)
        
        logger.info("=" * 60)
        logger.info(f"SMART BULK FETCH COMPLETE ({duration:.1f}s)")
        logger.info(f"  Bulk data: {results['bulk_fetch']['total']} assets")
        logger.info(f"  Updated: {results['updated'].get('updated', 0)} existing")
        logger.info(f"  New: {results['new_assets'].get('success', 0)} fetched")
        logger.info("=" * 60)
        
        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Smart Bulk Fetcher")
    parser.add_argument(
        "--scope",
        choices=["US_EU", "AFRICA"],
        default="US_EU",
        help="Market scope"
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip fetching full history for new assets"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Years of history to fetch for new assets"
    )
    parser.add_argument(
        "--limit-new",
        type=int,
        default=None,
        help="Limit number of new assets to fetch history for"
    )
    
    args = parser.parse_args()
    
    fetcher = SmartBulkFetcher(market_scope=args.scope)
    results = fetcher.run(
        fetch_new_history=not args.no_history,
        history_years=args.years,
        limit_new=args.limit_new
    )
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
