"""
Logo Fetcher for MarketGPS
Downloads company logos from Clearbit API
Run: python -m pipeline.logo_fetcher
"""

import urllib.request
import ssl
from pathlib import Path
import time
import sqlite3
import os

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

LOGOS_DIR = Path("data/logos")
DB_PATH = "data/sqlite/marketgps.db"

# Company domain mappings
COMPANY_DOMAINS = {
    # France (Euronext Paris)
    "MC": "lvmh.com",
    "OR": "loreal.com",
    "SAN": "sanofi.com",
    "AI": "airliquide.com",
    "BNP": "bnpparibas.com",
    "TTE": "totalenergies.com",
    "CAP": "capgemini.com",
    "DG": "vinci.com",
    "CS": "axa.com",
    "ORA": "orange.com",
    
    # Germany (XETRA)
    "SAP": "sap.com",
    "SIE": "siemens.com",
    "ALV": "allianz.com",
    "DTE": "telekom.com",
    "BAS": "basf.com",
    "BMW": "bmw.com",
    "ADS": "adidas.com",
    "VOW3": "volkswagen.com",
    "DBK": "db.com",
    
    # UK (LSE)
    "SHEL": "shell.com",
    "AZN": "astrazeneca.com",
    "HSBA": "hsbc.com",
    "ULVR": "unilever.com",
    "BP": "bp.com",
    "GSK": "gsk.com",
    "RIO": "riotinto.com",
    "LLOY": "lloydsbank.com",
    "VOD": "vodafone.com",
    "BARC": "barclays.com",
    
    # South Africa (JSE)
    "NPN": "naspers.com",
    "BTI": "bat.com",
    "AGL": "angloamerican.com",
    "SOL": "sasol.com",
    "SBK": "standardbank.com",
    "FSR": "firstrand.co.za",
    "MTN": "mtn.com",
    "BID": "bidcorp.com",
    "SHP": "shopriteholdings.co.za",
    "DSY": "discovery.co.za",
    
    # US companies (additional)
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "GOOGL": "google.com",
    "AMZN": "amazon.com",
    "META": "meta.com",
    "TSLA": "tesla.com",
    "NVDA": "nvidia.com",
    "JPM": "jpmorganchase.com",
    "V": "visa.com",
    "MA": "mastercard.com",
    "JNJ": "jnj.com",
    "UNH": "unitedhealthgroup.com",
    "PG": "pg.com",
    "HD": "homedepot.com",
    "DIS": "disney.com",
    "KO": "coca-cola.com",
    "PEP": "pepsico.com",
    "WMT": "walmart.com",
    "COST": "costco.com",
    "NKE": "nike.com",
    "MCD": "mcdonalds.com",
    "INTC": "intel.com",
    "AMD": "amd.com",
    "CRM": "salesforce.com",
    "ADBE": "adobe.com",
    "CSCO": "cisco.com",
    "VZ": "verizon.com",
    "PFE": "pfizer.com",
    "ABT": "abbott.com",
    "TMO": "thermofisher.com",
    "DHR": "danaher.com",
    "LLY": "lilly.com",
    "ABBV": "abbvie.com",
    "CVX": "chevron.com",
    "XOM": "exxonmobil.com",
    "NEE": "nexteraenergy.com",
    "ACN": "accenture.com",
    "AVGO": "broadcom.com",
}


def download_logo(ticker: str, domain: str, output_dir: Path) -> bool:
    """Download logo from Clearbit API."""
    logo_path = output_dir / f"{ticker}.png"
    
    if logo_path.exists():
        return True
    
    url = f"https://logo.clearbit.com/{domain}"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
            if len(data) > 500:
                with open(logo_path, 'wb') as f:
                    f.write(data)
                return True
    except Exception as e:
        print(f"  Error downloading {ticker}: {e}")
    
    return False


def get_tickers_from_db() -> list:
    """Get all tickers from database."""
    if not os.path.exists(DB_PATH):
        return list(COMPANY_DOMAINS.keys())
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT DISTINCT symbol FROM universe WHERE active = 1")
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return tickers


def main():
    """Main logo fetcher function."""
    print("=" * 60)
    print("MarketGPS Logo Fetcher")
    print("=" * 60)
    
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get tickers
    tickers = get_tickers_from_db()
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    print(f"\nProcessing {len(tickers)} tickers...\n")
    
    for ticker in tickers:
        logo_path = LOGOS_DIR / f"{ticker}.png"
        
        if logo_path.exists():
            skipped += 1
            continue
        
        domain = COMPANY_DOMAINS.get(ticker)
        
        if not domain:
            # Try to guess domain
            domain = f"{ticker.lower()}.com"
        
        print(f"Downloading {ticker} from {domain}...", end=" ")
        
        if download_logo(ticker, domain, LOGOS_DIR):
            print("OK")
            downloaded += 1
        else:
            print("FAILED")
            failed += 1
        
        time.sleep(0.5)  # Rate limiting
    
    print("\n" + "=" * 60)
    print(f"Results: {downloaded} downloaded, {skipped} skipped, {failed} failed")
    print(f"Total logos: {len(list(LOGOS_DIR.glob('*.png')))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
