"""
MarketGPS - Smart Logo Fetcher (Batch Optimization)
Fetches logos efficiently using multiple strategies.

STRATEGIES:
1. EODHD Fundamentals API (if available in your plan)
   - GET /fundamentals/{SYMBOL} → General.LogoURL
   
2. Clearbit API (free, rate limited)
   - GET https://logo.clearbit.com/{domain}
   
3. Domain guessing
   - Try {ticker.lower()}.com as fallback

4. Fallback to type-specific icons
   - Frontend handles this gracefully

Usage:
    python -m pipeline.smart_logo_fetcher --scope US_EU --limit 500
    python -m pipeline.smart_logo_fetcher --top-scored  # Only logos for top scored
"""
import os
import sys
import time
import argparse
import urllib.request
import ssl
from pathlib import Path
from typing import Dict, List, Optional, Set
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore
from providers.eodhd import EODHDProvider

logger = get_logger(__name__)

# Disable SSL verification for Clearbit
ssl._create_default_https_context = ssl._create_unverified_context


# Well-known company domains
KNOWN_DOMAINS = {
    # US Large Caps
    "AAPL": "apple.com", "MSFT": "microsoft.com", "GOOGL": "google.com",
    "AMZN": "amazon.com", "META": "meta.com", "TSLA": "tesla.com",
    "NVDA": "nvidia.com", "JPM": "jpmorganchase.com", "V": "visa.com",
    "MA": "mastercard.com", "JNJ": "jnj.com", "UNH": "unitedhealthgroup.com",
    "PG": "pg.com", "HD": "homedepot.com", "DIS": "disney.com",
    "KO": "coca-cola.com", "PEP": "pepsico.com", "WMT": "walmart.com",
    "COST": "costco.com", "NKE": "nike.com", "MCD": "mcdonalds.com",
    "INTC": "intel.com", "AMD": "amd.com", "CRM": "salesforce.com",
    "ADBE": "adobe.com", "CSCO": "cisco.com", "VZ": "verizon.com",
    "PFE": "pfizer.com", "ABT": "abbott.com", "TMO": "thermofisher.com",
    "CVX": "chevron.com", "XOM": "exxonmobil.com", "AVGO": "broadcom.com",
    "LLY": "lilly.com", "ABBV": "abbvie.com", "MRK": "merck.com",
    "ORCL": "oracle.com", "IBM": "ibm.com", "GE": "ge.com",
    "BA": "boeing.com", "CAT": "caterpillar.com", "MMM": "3m.com",
    
    # European
    "MC": "lvmh.com", "OR": "loreal.com", "SAN": "sanofi.com",
    "SAP": "sap.com", "SIE": "siemens.com", "ALV": "allianz.com",
    "SHEL": "shell.com", "AZN": "astrazeneca.com", "HSBA": "hsbc.com",
    "ULVR": "unilever.com", "BP": "bp.com", "GSK": "gsk.com",
    "ASML": "asml.com", "NESN": "nestle.com", "NOVN": "novartis.com",
    
    # African
    "NPN": "naspers.com", "BTI": "bat.com", "AGL": "angloamerican.com",
    "SOL": "sasol.com", "SBK": "standardbank.com", "MTN": "mtn.com",
    "DANGCEM": "dangote.com", "GTCO": "gtbank.com", "ZENITHBANK": "zenithbank.com",
}


class SmartLogoFetcher:
    """
    Efficiently fetches logos using multiple strategies.
    
    Priority:
    1. Skip if logo already exists
    2. Try EODHD fundamentals (if fundamentals endpoint works)
    3. Try Clearbit with known domain
    4. Try Clearbit with guessed domain
    5. Mark as failed (frontend shows fallback icon)
    """
    
    LOGOS_DIR = Path("data/logos")
    
    def __init__(self):
        """Initialize the logo fetcher."""
        self._config = get_config()
        self._store = SQLiteStore()
        self._provider = EODHDProvider()
        
        # Create logos directory
        self.LOGOS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Track existing logos
        self._existing_logos: Set[str] = set()
        self._refresh_existing()
    
    def _refresh_existing(self):
        """Refresh list of existing logos."""
        self._existing_logos = {
            f.stem.upper() for f in self.LOGOS_DIR.glob("*.png")
        }
        logger.info(f"Found {len(self._existing_logos)} existing logos")
    
    def get_priority_tickers(
        self,
        scope: str = "US_EU",
        top_scored: bool = False,
        limit: int = 500
    ) -> List[str]:
        """
        Get tickers that need logos, prioritized.
        
        Args:
            scope: Market scope
            top_scored: Only get tickers from top scored
            limit: Max tickers to return
            
        Returns:
            List of tickers needing logos
        """
        with self._store._get_connection() as conn:
            if top_scored:
                # Only top scored assets
                query = """
                    SELECT u.symbol 
                    FROM universe u
                    JOIN scores_latest s ON u.asset_id = s.asset_id
                    WHERE u.market_scope = ?
                      AND u.active = 1
                      AND s.score_total IS NOT NULL
                    ORDER BY s.score_total DESC
                    LIMIT ?
                """
            else:
                # All active assets
                query = """
                    SELECT symbol 
                    FROM universe
                    WHERE market_scope = ? AND active = 1
                    LIMIT ?
                """
            
            rows = conn.execute(query, (scope, limit)).fetchall()
            all_tickers = [row["symbol"] for row in rows]
        
        # Filter out already existing
        tickers = [t for t in all_tickers if t.upper() not in self._existing_logos]
        
        logger.info(f"Found {len(tickers)} tickers needing logos (out of {len(all_tickers)})")
        return tickers
    
    def fetch_from_clearbit(self, ticker: str, domain: str) -> bool:
        """
        Fetch logo from Clearbit API.
        
        Args:
            ticker: Ticker symbol
            domain: Company domain
            
        Returns:
            True if successful
        """
        url = f"https://logo.clearbit.com/{domain}"
        logo_path = self.LOGOS_DIR / f"{ticker.upper()}.png"
        
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
                
                # Check if we got actual image data (not error page)
                if len(data) > 500:
                    with open(logo_path, "wb") as f:
                        f.write(data)
                    return True
                    
        except Exception as e:
            logger.debug(f"Clearbit failed for {ticker} ({domain}): {e}")
        
        return False
    
    def fetch_from_eodhd(self, asset_id: str, ticker: str) -> bool:
        """
        Try to get logo URL from EODHD fundamentals.
        
        Args:
            asset_id: Full asset ID (e.g., AAPL.US)
            ticker: Ticker symbol
            
        Returns:
            True if successful
        """
        try:
            fundamentals = self._provider.fetch_fundamentals(asset_id)
            
            if not fundamentals:
                return False
            
            # Check for logo URL
            logo_url = fundamentals.get("logo_url")
            if not logo_url:
                # Try extracting from general info
                general = fundamentals.get("General", {})
                logo_url = general.get("LogoURL") or general.get("ImageURL")
            
            if logo_url:
                return self._download_image(logo_url, ticker)
                
        except Exception as e:
            logger.debug(f"EODHD fundamentals failed for {ticker}: {e}")
        
        return False
    
    def _download_image(self, url: str, ticker: str) -> bool:
        """Download image from URL."""
        logo_path = self.LOGOS_DIR / f"{ticker.upper()}.png"
        
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
                
                if len(data) > 500:
                    with open(logo_path, "wb") as f:
                        f.write(data)
                    return True
                    
        except Exception as e:
            logger.debug(f"Download failed for {ticker}: {e}")
        
        return False
    
    def guess_domain(self, ticker: str, name: str = "") -> List[str]:
        """
        Guess possible domains for a company.
        
        Args:
            ticker: Ticker symbol
            name: Company name (optional)
            
        Returns:
            List of possible domains to try
        """
        domains = []
        
        # Check known domains first
        if ticker.upper() in KNOWN_DOMAINS:
            domains.append(KNOWN_DOMAINS[ticker.upper()])
        
        # Try ticker.com
        domains.append(f"{ticker.lower()}.com")
        
        # Try variations
        clean_ticker = ticker.lower().replace("-", "").replace(".", "")
        if clean_ticker != ticker.lower():
            domains.append(f"{clean_ticker}.com")
        
        # If we have company name, try that too
        if name:
            # Extract first word
            first_word = name.split()[0].lower() if name.split() else ""
            if first_word and len(first_word) > 2:
                domains.append(f"{first_word}.com")
        
        return list(dict.fromkeys(domains))  # Remove duplicates
    
    def fetch_logo(self, ticker: str, asset_id: str = "", name: str = "") -> bool:
        """
        Fetch logo using all available strategies.
        
        Args:
            ticker: Ticker symbol
            asset_id: Full asset ID (optional)
            name: Company name (optional)
            
        Returns:
            True if logo was fetched
        """
        # Skip if already exists
        if ticker.upper() in self._existing_logos:
            return True
        
        # Strategy 1: Try EODHD fundamentals (if we have asset_id)
        if asset_id and self._provider.is_configured:
            if self.fetch_from_eodhd(asset_id, ticker):
                self._existing_logos.add(ticker.upper())
                return True
        
        # Strategy 2: Try known domains
        domains = self.guess_domain(ticker, name)
        
        for domain in domains:
            if self.fetch_from_clearbit(ticker, domain):
                self._existing_logos.add(ticker.upper())
                return True
            time.sleep(0.3)  # Rate limiting
        
        return False
    
    def run(
        self,
        scope: str = "US_EU",
        top_scored: bool = False,
        limit: int = 500,
        use_eodhd: bool = False
    ) -> Dict:
        """
        Run the logo fetcher.
        
        Args:
            scope: Market scope
            top_scored: Only fetch for top scored
            limit: Max logos to fetch
            use_eodhd: Use EODHD fundamentals API (more API calls)
            
        Returns:
            Dict with stats
        """
        stats = {"processed": 0, "success": 0, "failed": 0, "skipped": 0}
        
        # Get tickers needing logos
        tickers = self.get_priority_tickers(
            scope=scope,
            top_scored=top_scored,
            limit=limit
        )
        
        if not tickers:
            logger.info("No tickers need logos")
            return stats
        
        logger.info(f"Fetching logos for {len(tickers)} tickers")
        
        # Get asset info for better domain guessing
        asset_info = {}
        with self._store._get_connection() as conn:
            for ticker in tickers:
                row = conn.execute(
                    "SELECT asset_id, name FROM universe WHERE symbol = ? LIMIT 1",
                    (ticker,)
                ).fetchone()
                if row:
                    asset_info[ticker] = {
                        "asset_id": row["asset_id"],
                        "name": row["name"]
                    }
        
        # Fetch logos
        for i, ticker in enumerate(tickers):
            if i > 0 and i % 50 == 0:
                logger.info(f"Progress: {i}/{len(tickers)} ({stats['success']} success)")
            
            info = asset_info.get(ticker, {})
            asset_id = info.get("asset_id", "") if use_eodhd else ""
            name = info.get("name", "")
            
            try:
                if self.fetch_logo(ticker, asset_id, name):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.warning(f"Error fetching logo for {ticker}: {e}")
                stats["failed"] += 1
            
            stats["processed"] += 1
        
        logger.info("=" * 60)
        logger.info(f"Logo fetch complete:")
        logger.info(f"  Processed: {stats['processed']}")
        logger.info(f"  Success: {stats['success']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Total logos: {len(list(self.LOGOS_DIR.glob('*.png')))}")
        logger.info("=" * 60)
        
        return stats


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Smart Logo Fetcher")
    parser.add_argument(
        "--scope",
        choices=["US_EU", "AFRICA"],
        default="US_EU",
        help="Market scope"
    )
    parser.add_argument(
        "--top-scored",
        action="store_true",
        help="Only fetch logos for top scored assets"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max logos to fetch"
    )
    parser.add_argument(
        "--use-eodhd",
        action="store_true",
        help="Use EODHD fundamentals API (uses more API calls)"
    )
    
    args = parser.parse_args()
    
    fetcher = SmartLogoFetcher()
    stats = fetcher.run(
        scope=args.scope,
        top_scored=args.top_scored,
        limit=args.limit,
        use_eodhd=args.use_eodhd
    )
    
    print(f"\nDone! {stats['success']} logos fetched.")


if __name__ == "__main__":
    main()
