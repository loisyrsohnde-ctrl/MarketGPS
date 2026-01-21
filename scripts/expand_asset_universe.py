"""
MarketGPS - Expand Asset Universe
Fetches additional asset classes from EODHD to enrich the platform.

This script adds:
- ETFs (US and EU markets)
- Bonds/Fixed Income ETFs
- REITs
- Commodities ETFs
- Popular/Blue Chip stocks that might be missing

USAGE:
    python scripts/expand_asset_universe.py --scope US_EU --dry-run
    python scripts/expand_asset_universe.py --scope US_EU --commit

The --dry-run flag shows what would be added without making changes.
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from core.models import Asset, AssetType
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# POPULAR INSTRUMENTS BY CATEGORY
# ═══════════════════════════════════════════════════════════════════════════

# Major US ETFs - Must have for any strategy
US_CORE_ETFS = [
    # Broad Market
    ("SPY", "SPDR S&P 500 ETF Trust", "ETF", "US"),
    ("VOO", "Vanguard S&P 500 ETF", "ETF", "US"),
    ("VTI", "Vanguard Total Stock Market ETF", "ETF", "US"),
    ("QQQ", "Invesco QQQ Trust", "ETF", "US"),
    ("IWM", "iShares Russell 2000 ETF", "ETF", "US"),
    ("DIA", "SPDR Dow Jones Industrial Average ETF", "ETF", "US"),
    
    # Bond ETFs
    ("BND", "Vanguard Total Bond Market ETF", "ETF", "US"),
    ("AGG", "iShares Core U.S. Aggregate Bond ETF", "ETF", "US"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "ETF", "US"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF", "ETF", "US"),
    ("SHY", "iShares 1-3 Year Treasury Bond ETF", "ETF", "US"),
    ("TIPS", "iShares TIPS Bond ETF", "ETF", "US"),
    ("LQD", "iShares iBoxx $ Investment Grade Corporate Bond ETF", "ETF", "US"),
    ("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF", "ETF", "US"),
    
    # Commodities
    ("GLD", "SPDR Gold Shares", "ETF", "US"),
    ("IAU", "iShares Gold Trust", "ETF", "US"),
    ("SLV", "iShares Silver Trust", "ETF", "US"),
    ("USO", "United States Oil Fund", "ETF", "US"),
    ("DBC", "Invesco DB Commodity Index Tracking Fund", "ETF", "US"),
    
    # International
    ("EFA", "iShares MSCI EAFE ETF", "ETF", "US"),
    ("VEA", "Vanguard FTSE Developed Markets ETF", "ETF", "US"),
    ("VWO", "Vanguard FTSE Emerging Markets ETF", "ETF", "US"),
    ("EEM", "iShares MSCI Emerging Markets ETF", "ETF", "US"),
    
    # Sector ETFs
    ("XLK", "Technology Select Sector SPDR Fund", "ETF", "US"),
    ("XLV", "Health Care Select Sector SPDR Fund", "ETF", "US"),
    ("XLF", "Financial Select Sector SPDR Fund", "ETF", "US"),
    ("XLE", "Energy Select Sector SPDR Fund", "ETF", "US"),
    ("XLU", "Utilities Select Sector SPDR Fund", "ETF", "US"),
    ("XLP", "Consumer Staples Select Sector SPDR Fund", "ETF", "US"),
    ("XLI", "Industrial Select Sector SPDR Fund", "ETF", "US"),
    
    # Dividend/Income
    ("VYM", "Vanguard High Dividend Yield ETF", "ETF", "US"),
    ("SCHD", "Schwab U.S. Dividend Equity ETF", "ETF", "US"),
    ("DVY", "iShares Select Dividend ETF", "ETF", "US"),
    
    # REITs
    ("VNQ", "Vanguard Real Estate ETF", "ETF", "US"),
    ("IYR", "iShares U.S. Real Estate ETF", "ETF", "US"),
    
    # Low Volatility / Factor
    ("SPLV", "Invesco S&P 500 Low Volatility ETF", "ETF", "US"),
    ("USMV", "iShares MSCI USA Min Vol Factor ETF", "ETF", "US"),
    ("MTUM", "iShares MSCI USA Momentum Factor ETF", "ETF", "US"),
    ("QUAL", "iShares MSCI USA Quality Factor ETF", "ETF", "US"),
    ("VLUE", "iShares MSCI USA Value Factor ETF", "ETF", "US"),
]

# Major US Stocks (Blue Chips) - Must haves
US_BLUE_CHIPS = [
    ("AAPL", "Apple Inc.", "EQUITY", "US"),
    ("MSFT", "Microsoft Corporation", "EQUITY", "US"),
    ("GOOGL", "Alphabet Inc. Class A", "EQUITY", "US"),
    ("AMZN", "Amazon.com, Inc.", "EQUITY", "US"),
    ("NVDA", "NVIDIA Corporation", "EQUITY", "US"),
    ("META", "Meta Platforms, Inc.", "EQUITY", "US"),
    ("TSLA", "Tesla, Inc.", "EQUITY", "US"),
    ("BRK-B", "Berkshire Hathaway Inc. Class B", "EQUITY", "US"),
    ("UNH", "UnitedHealth Group Incorporated", "EQUITY", "US"),
    ("JNJ", "Johnson & Johnson", "EQUITY", "US"),
    ("JPM", "JPMorgan Chase & Co.", "EQUITY", "US"),
    ("V", "Visa Inc.", "EQUITY", "US"),
    ("PG", "The Procter & Gamble Company", "EQUITY", "US"),
    ("XOM", "Exxon Mobil Corporation", "EQUITY", "US"),
    ("HD", "The Home Depot, Inc.", "EQUITY", "US"),
    ("CVX", "Chevron Corporation", "EQUITY", "US"),
    ("MA", "Mastercard Incorporated", "EQUITY", "US"),
    ("ABBV", "AbbVie Inc.", "EQUITY", "US"),
    ("KO", "The Coca-Cola Company", "EQUITY", "US"),
    ("PEP", "PepsiCo, Inc.", "EQUITY", "US"),
    ("COST", "Costco Wholesale Corporation", "EQUITY", "US"),
    ("WMT", "Walmart Inc.", "EQUITY", "US"),
    ("DIS", "The Walt Disney Company", "EQUITY", "US"),
    ("MCD", "McDonald's Corporation", "EQUITY", "US"),
    ("AMD", "Advanced Micro Devices, Inc.", "EQUITY", "US"),
    ("INTC", "Intel Corporation", "EQUITY", "US"),
    ("NFLX", "Netflix, Inc.", "EQUITY", "US"),
    ("CRM", "Salesforce, Inc.", "EQUITY", "US"),
    ("ADBE", "Adobe Inc.", "EQUITY", "US"),
    ("PYPL", "PayPal Holdings, Inc.", "EQUITY", "US"),
]

# European ETFs (listed on Paris, London, Frankfurt)
EU_CORE_ETFS = [
    # iShares on LSE
    ("CSPX", "iShares Core S&P 500 UCITS ETF", "ETF", "LSE"),
    ("IWDA", "iShares Core MSCI World UCITS ETF", "ETF", "LSE"),
    ("EIMI", "iShares Core MSCI Emerging Markets IMI UCITS ETF", "ETF", "LSE"),
    
    # Vanguard on LSE
    ("VUSA", "Vanguard S&P 500 UCITS ETF", "ETF", "LSE"),
    ("VWRL", "Vanguard FTSE All-World UCITS ETF", "ETF", "LSE"),
    
    # Amundi on Paris (Euronext)
    ("CW8", "Amundi MSCI World UCITS ETF", "ETF", "PA"),
    ("MWRD", "Amundi MSCI World UCITS ETF - EUR", "ETF", "PA"),
    ("PANX", "Amundi PEA S&P 500 UCITS ETF", "ETF", "PA"),
    
    # Lyxor on Paris
    ("EWLD", "Lyxor MSCI World UCITS ETF", "ETF", "PA"),
    
    # Xtrackers on Frankfurt
    ("XDWD", "Xtrackers MSCI World UCITS ETF", "ETF", "XETRA"),
    ("XMWO", "Xtrackers MSCI World Quality UCITS ETF", "ETF", "XETRA"),
]

# Major European Stocks
EU_BLUE_CHIPS = [
    # France (Paris)
    ("MC", "LVMH Moët Hennessy Louis Vuitton SE", "EQUITY", "PA"),
    ("OR", "L'Oréal SA", "EQUITY", "PA"),
    ("TTE", "TotalEnergies SE", "EQUITY", "PA"),
    ("SAN", "Sanofi", "EQUITY", "PA"),
    ("AI", "Air Liquide S.A.", "EQUITY", "PA"),
    ("BNP", "BNP Paribas SA", "EQUITY", "PA"),
    
    # Germany (Frankfurt)
    ("SAP", "SAP SE", "EQUITY", "XETRA"),
    ("SIE", "Siemens AG", "EQUITY", "XETRA"),
    ("ALV", "Allianz SE", "EQUITY", "XETRA"),
    ("DTE", "Deutsche Telekom AG", "EQUITY", "XETRA"),
    ("VOW3", "Volkswagen AG", "EQUITY", "XETRA"),
    ("BMW", "Bayerische Motoren Werke AG", "EQUITY", "XETRA"),
    
    # UK (London)
    ("SHEL", "Shell plc", "EQUITY", "LSE"),
    ("HSBA", "HSBC Holdings plc", "EQUITY", "LSE"),
    ("AZN", "AstraZeneca PLC", "EQUITY", "LSE"),
    ("ULVR", "Unilever PLC", "EQUITY", "LSE"),
    ("GSK", "GSK plc", "EQUITY", "LSE"),
    ("BP", "BP p.l.c.", "EQUITY", "LSE"),
    
    # Switzerland
    ("NESN", "Nestlé S.A.", "EQUITY", "SW"),
    ("ROG", "Roche Holding AG", "EQUITY", "SW"),
    ("NOVN", "Novartis AG", "EQUITY", "SW"),
    
    # Netherlands
    ("ASML", "ASML Holding N.V.", "EQUITY", "AS"),
]


class UniverseExpander:
    """Expands the asset universe with curated instruments."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.store = SQLiteStore()
        self.stats = {
            "etfs_added": 0,
            "stocks_added": 0,
            "already_exists": 0,
            "errors": 0,
        }
    
    def _get_asset_type(self, type_str: str) -> AssetType:
        """Convert string to AssetType enum."""
        mapping = {
            "ETF": AssetType.ETF,
            "EQUITY": AssetType.EQUITY,
            "BOND": AssetType.BOND,
            "FUND": AssetType.FUND,
        }
        return mapping.get(type_str, AssetType.EQUITY)
    
    def _get_market_scope(self, exchange: str) -> str:
        """Determine market scope from exchange."""
        if exchange == "US":
            return "US_EU"
        elif exchange in ["LSE", "PA", "XETRA", "AS", "SW", "MI", "MC"]:
            return "US_EU"
        elif exchange in ["JSE", "NG", "BRVM", "CA"]:
            return "AFRICA"
        return "US_EU"
    
    def _get_market_code(self, exchange: str) -> str:
        """Get market code from exchange."""
        mapping = {
            "US": "US",
            "LSE": "UK",
            "PA": "FR",
            "XETRA": "DE",
            "AS": "NL",
            "SW": "CH",
            "MI": "IT",
            "MC": "ES",
            "JSE": "ZA",
            "NG": "NG",
        }
        return mapping.get(exchange, exchange)
    
    def _get_currency(self, exchange: str) -> str:
        """Get currency from exchange."""
        mapping = {
            "US": "USD",
            "LSE": "GBP",
            "PA": "EUR",
            "XETRA": "EUR",
            "AS": "EUR",
            "SW": "CHF",
            "MI": "EUR",
            "MC": "EUR",
            "JSE": "ZAR",
        }
        return mapping.get(exchange, "USD")
    
    def add_instrument(self, ticker: str, name: str, type_str: str, exchange: str) -> bool:
        """Add a single instrument to the universe."""
        asset_id = f"{ticker}.{exchange}"
        
        # Check if already exists
        existing = self.store.get_asset(asset_id)
        if existing:
            self.stats["already_exists"] += 1
            return False
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would add: {asset_id} ({name})")
            if type_str == "ETF":
                self.stats["etfs_added"] += 1
            else:
                self.stats["stocks_added"] += 1
            return True
        
        try:
            asset = Asset(
                asset_id=asset_id,
                symbol=ticker,
                name=name,
                asset_type=self._get_asset_type(type_str),
                exchange=exchange,
                currency=self._get_currency(exchange),
                country=self._get_market_code(exchange),
                active=True,
                tier=1,  # Core instruments are Tier 1
            )
            
            market_scope = self._get_market_scope(exchange)
            self.store.upsert_asset(asset, market_scope=market_scope)
            
            if type_str == "ETF":
                self.stats["etfs_added"] += 1
            else:
                self.stats["stocks_added"] += 1
            
            logger.info(f"✅ Added: {asset_id} ({name})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add {asset_id}: {e}")
            self.stats["errors"] += 1
            return False
    
    def run(self, scope: str = "US_EU"):
        """Run the expansion for a given scope."""
        logger.info(f"{'=' * 60}")
        logger.info(f"MarketGPS Universe Expansion - Scope: {scope}")
        logger.info(f"Mode: {'DRY-RUN (no changes)' if self.dry_run else 'COMMIT (real changes)'}")
        logger.info(f"{'=' * 60}")
        
        if scope in ["US_EU", "ALL"]:
            # Add US Core ETFs
            logger.info("\n📊 Adding US Core ETFs...")
            for ticker, name, asset_type, exchange in US_CORE_ETFS:
                self.add_instrument(ticker, name, asset_type, exchange)
            
            # Add US Blue Chips
            logger.info("\n🏢 Adding US Blue Chip Stocks...")
            for ticker, name, asset_type, exchange in US_BLUE_CHIPS:
                self.add_instrument(ticker, name, asset_type, exchange)
            
            # Add EU ETFs
            logger.info("\n🇪🇺 Adding EU Core ETFs...")
            for ticker, name, asset_type, exchange in EU_CORE_ETFS:
                self.add_instrument(ticker, name, asset_type, exchange)
            
            # Add EU Blue Chips
            logger.info("\n🏰 Adding EU Blue Chip Stocks...")
            for ticker, name, asset_type, exchange in EU_BLUE_CHIPS:
                self.add_instrument(ticker, name, asset_type, exchange)
        
        # Print summary
        logger.info(f"\n{'=' * 60}")
        logger.info("📈 EXPANSION SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"  ETFs added:       {self.stats['etfs_added']}")
        logger.info(f"  Stocks added:     {self.stats['stocks_added']}")
        logger.info(f"  Already existed:  {self.stats['already_exists']}")
        logger.info(f"  Errors:           {self.stats['errors']}")
        logger.info(f"  TOTAL NEW:        {self.stats['etfs_added'] + self.stats['stocks_added']}")
        
        if self.dry_run:
            logger.info(f"\n⚠️  DRY-RUN mode - no changes were made.")
            logger.info(f"    Run with --commit to apply changes.")


def main():
    parser = argparse.ArgumentParser(description="Expand MarketGPS asset universe")
    parser.add_argument("--scope", choices=["US_EU", "AFRICA", "ALL"], default="US_EU",
                        help="Market scope to expand")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview changes without committing (default)")
    parser.add_argument("--commit", action="store_true",
                        help="Actually commit changes to database")
    
    args = parser.parse_args()
    
    # If --commit is specified, override dry-run
    dry_run = not args.commit
    
    expander = UniverseExpander(dry_run=dry_run)
    expander.run(scope=args.scope)


if __name__ == "__main__":
    main()
