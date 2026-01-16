"""
MarketGPS v7.0 - Universe Pipeline
Manages the universe of tradable assets.
"""
from pathlib import Path
from typing import List, Optional
import csv

from core.config import get_config, get_logger
from core.models import Asset, AssetType
from storage.sqlite_store import SQLiteStore
from providers import get_provider

logger = get_logger(__name__)

# Default universe if no CSV provided
DEFAULT_UNIVERSE = [
    # US Large Cap Equities
    ("AAPL", "Apple Inc.", "EQUITY", "US"),
    ("MSFT", "Microsoft Corporation", "EQUITY", "US"),
    ("AMZN", "Amazon.com Inc.", "EQUITY", "US"),
    ("NVDA", "NVIDIA Corporation", "EQUITY", "US"),
    ("GOOGL", "Alphabet Inc.", "EQUITY", "US"),
    ("META", "Meta Platforms Inc.", "EQUITY", "US"),
    ("TSLA", "Tesla Inc.", "EQUITY", "US"),
    ("BRK-B", "Berkshire Hathaway Inc.", "EQUITY", "US"),
    ("UNH", "UnitedHealth Group Inc.", "EQUITY", "US"),
    ("JNJ", "Johnson & Johnson", "EQUITY", "US"),
    ("JPM", "JPMorgan Chase & Co.", "EQUITY", "US"),
    ("V", "Visa Inc.", "EQUITY", "US"),
    ("PG", "Procter & Gamble Co.", "EQUITY", "US"),
    ("XOM", "Exxon Mobil Corporation", "EQUITY", "US"),
    ("HD", "Home Depot Inc.", "EQUITY", "US"),
    ("CVX", "Chevron Corporation", "EQUITY", "US"),
    ("MA", "Mastercard Inc.", "EQUITY", "US"),
    ("ABBV", "AbbVie Inc.", "EQUITY", "US"),
    ("MRK", "Merck & Co. Inc.", "EQUITY", "US"),
    ("LLY", "Eli Lilly and Company", "EQUITY", "US"),
    ("PFE", "Pfizer Inc.", "EQUITY", "US"),
    ("KO", "Coca-Cola Company", "EQUITY", "US"),
    ("PEP", "PepsiCo Inc.", "EQUITY", "US"),
    ("COST", "Costco Wholesale Corporation", "EQUITY", "US"),
    ("AVGO", "Broadcom Inc.", "EQUITY", "US"),
    ("TMO", "Thermo Fisher Scientific Inc.", "EQUITY", "US"),
    ("MCD", "McDonald's Corporation", "EQUITY", "US"),
    ("WMT", "Walmart Inc.", "EQUITY", "US"),
    ("CSCO", "Cisco Systems Inc.", "EQUITY", "US"),
    ("ACN", "Accenture plc", "EQUITY", "US"),
    ("ABT", "Abbott Laboratories", "EQUITY", "US"),
    ("DHR", "Danaher Corporation", "EQUITY", "US"),
    ("NEE", "NextEra Energy Inc.", "EQUITY", "US"),
    ("VZ", "Verizon Communications Inc.", "EQUITY", "US"),
    ("DIS", "Walt Disney Company", "EQUITY", "US"),
    ("ADBE", "Adobe Inc.", "EQUITY", "US"),
    ("CRM", "Salesforce Inc.", "EQUITY", "US"),
    ("NKE", "Nike Inc.", "EQUITY", "US"),
    ("INTC", "Intel Corporation", "EQUITY", "US"),
    ("AMD", "Advanced Micro Devices Inc.", "EQUITY", "US"),
    
    # Popular ETFs
    ("SPY", "SPDR S&P 500 ETF Trust", "ETF", "US"),
    ("QQQ", "Invesco QQQ Trust", "ETF", "US"),
    ("IWM", "iShares Russell 2000 ETF", "ETF", "US"),
    ("VTI", "Vanguard Total Stock Market ETF", "ETF", "US"),
    ("VOO", "Vanguard S&P 500 ETF", "ETF", "US"),
    ("VEA", "Vanguard FTSE Developed Markets ETF", "ETF", "US"),
    ("VWO", "Vanguard FTSE Emerging Markets ETF", "ETF", "US"),
    ("EFA", "iShares MSCI EAFE ETF", "ETF", "US"),
    ("EEM", "iShares MSCI Emerging Markets ETF", "ETF", "US"),
    ("GLD", "SPDR Gold Shares", "ETF", "US"),
    ("SLV", "iShares Silver Trust", "ETF", "US"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "ETF", "US"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF", "ETF", "US"),
    ("LQD", "iShares iBoxx $ Investment Grade Corporate Bond ETF", "ETF", "US"),
    ("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF", "ETF", "US"),
    ("XLF", "Financial Select Sector SPDR Fund", "ETF", "US"),
    ("XLK", "Technology Select Sector SPDR Fund", "ETF", "US"),
    ("XLE", "Energy Select Sector SPDR Fund", "ETF", "US"),
    ("XLV", "Health Care Select Sector SPDR Fund", "ETF", "US"),
    ("XLI", "Industrial Select Sector SPDR Fund", "ETF", "US"),
]


class UniverseJob:
    """
    Universe management job.
    Loads and maintains the universe of tradable assets.
    """
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        csv_path: Optional[Path] = None
    ):
        """
        Initialize Universe job.
        
        Args:
            store: SQLite store instance
            csv_path: Optional path to universe CSV file
        """
        self._store = store or SQLiteStore()
        self._csv_path = csv_path
        self._provider = get_provider("auto")
    
    def run(self) -> dict:
        """
        Run the universe initialization job.
        
        Returns:
            Dict with job results
        """
        logger.info("Starting Universe job")
        
        results = {
            "added": 0,
            "updated": 0,
            "errors": 0,
            "source": "default"
        }
        
        try:
            # Try to load from CSV first
            if self._csv_path and self._csv_path.exists():
                assets = self._load_from_csv(self._csv_path)
                results["source"] = "csv"
            else:
                # Check for universe.csv in data directory
                config = get_config()
                default_csv = config.storage.data_dir / "universe.csv"
                
                if default_csv.exists():
                    assets = self._load_from_csv(default_csv)
                    results["source"] = "csv"
                else:
                    # Use default universe
                    assets = self._create_default_universe()
                    results["source"] = "default"
            
            # Insert assets into database
            for asset in assets:
                try:
                    self._store.upsert_asset(asset)
                    results["added"] += 1
                except Exception as e:
                    logger.warning(f"Failed to insert asset {asset.symbol}: {e}")
                    results["errors"] += 1
            
            # Initialize rotation state for all assets
            self._init_rotation_states(assets)
            
            logger.info(f"Universe job complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Universe job failed: {e}")
            results["errors"] += 1
            return results
    
    def _create_default_universe(self) -> List[Asset]:
        """Create default universe from hardcoded list."""
        assets = []
        
        for symbol, name, asset_type, exchange in DEFAULT_UNIVERSE:
            asset_id = f"{symbol}.{exchange}"
            
            try:
                asset = Asset(
                    asset_id=asset_id,
                    symbol=symbol,
                    name=name,
                    asset_type=AssetType(asset_type),
                    exchange=exchange,
                    currency="USD",
                    active=True
                )
                assets.append(asset)
            except Exception as e:
                logger.warning(f"Failed to create asset {symbol}: {e}")
        
        logger.info(f"Created {len(assets)} assets from default universe")
        return assets
    
    def _load_from_csv(self, path: Path) -> List[Asset]:
        """
        Load universe from CSV file.
        
        Expected columns: symbol, name, asset_type, exchange (optional), currency (optional)
        """
        assets = []
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    symbol = row.get("symbol", "").strip().upper()
                    if not symbol:
                        continue
                    
                    exchange = row.get("exchange", "US").strip().upper()
                    asset_id = f"{symbol}.{exchange}"
                    
                    asset_type_str = row.get("asset_type", "EQUITY").strip().upper()
                    try:
                        asset_type = AssetType(asset_type_str)
                    except ValueError:
                        asset_type = AssetType.EQUITY
                    
                    asset = Asset(
                        asset_id=asset_id,
                        symbol=symbol,
                        name=row.get("name", symbol),
                        asset_type=asset_type,
                        exchange=exchange,
                        currency=row.get("currency", "USD").strip().upper(),
                        active=True
                    )
                    assets.append(asset)
            
            logger.info(f"Loaded {len(assets)} assets from {path}")
            
        except Exception as e:
            logger.error(f"Failed to load CSV {path}: {e}")
        
        return assets
    
    def _init_rotation_states(self, assets: List[Asset]) -> None:
        """Initialize rotation state for all assets."""
        from core.models import RotationState
        
        for asset in assets:
            state = RotationState(
                asset_id=asset.asset_id,
                priority_level=0
            )
            try:
                self._store.upsert_rotation_state(state)
            except Exception as e:
                logger.warning(f"Failed to init rotation state for {asset.asset_id}: {e}")
    
    def add_from_search(self, query: str, limit: int = 20) -> List[Asset]:
        """
        Search for assets via provider and add to universe.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of added assets
        """
        try:
            results = self._provider.search(query, limit=limit)
            
            added = []
            for result in results:
                # Map search result type to AssetType
                type_map = {
                    "Common Stock": AssetType.EQUITY,
                    "ETF": AssetType.ETF,
                    "Index": AssetType.INDEX,
                    "Mutual Fund": AssetType.FUND,
                }
                asset_type = type_map.get(result.asset_type, AssetType.EQUITY)
                
                asset_id = f"{result.symbol}.{result.exchange}"
                
                asset = Asset(
                    asset_id=asset_id,
                    symbol=result.symbol,
                    name=result.name,
                    asset_type=asset_type,
                    exchange=result.exchange,
                    currency=result.currency,
                    active=True
                )
                
                try:
                    self._store.upsert_asset(asset)
                    
                    # Init rotation state
                    from core.models import RotationState
                    state = RotationState(asset_id=asset_id, priority_level=0)
                    self._store.upsert_rotation_state(state)
                    
                    added.append(asset)
                except Exception as e:
                    logger.warning(f"Failed to add {asset_id}: {e}")
            
            logger.info(f"Added {len(added)} assets from search '{query}'")
            return added
            
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            return []
