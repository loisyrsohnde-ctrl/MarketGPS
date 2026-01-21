"""
MarketGPS - Add Derivatives Universe (Bonds, Options, Futures)
Uses Yahoo Finance as the data source since EODHD requires premium plans for these.

This script adds:
1. Bond ETFs (as proxies for individual bonds - more liquid, easier to track)
2. Major Futures contracts
3. Popular Options underlyings (the options themselves are fetched on-demand)

Run: python scripts/add_derivatives_universe.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from typing import List, Dict, Any
import time

from core.models import AssetType, Asset
from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# MarketScope type (from storage)
MarketScope = str  # "US_EU" or "AFRICA"

# ═══════════════════════════════════════════════════════════════════════════
# BONDS - Using Bond ETFs as proxies (more liquid, tracked by yfinance)
# ═══════════════════════════════════════════════════════════════════════════
BOND_ETFS = [
    # US Treasury Bonds
    {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "category": "Treasury Long"},
    {"symbol": "IEF", "name": "iShares 7-10 Year Treasury Bond ETF", "category": "Treasury Medium"},
    {"symbol": "SHY", "name": "iShares 1-3 Year Treasury Bond ETF", "category": "Treasury Short"},
    {"symbol": "SHV", "name": "iShares Short Treasury Bond ETF", "category": "Treasury Ultra-Short"},
    {"symbol": "GOVT", "name": "iShares U.S. Treasury Bond ETF", "category": "Treasury Broad"},
    {"symbol": "TIPS", "name": "iShares TIPS Bond ETF", "category": "Inflation-Protected"},
    
    # Corporate Bonds
    {"symbol": "LQD", "name": "iShares iBoxx $ Investment Grade Corporate Bond ETF", "category": "Corporate IG"},
    {"symbol": "HYG", "name": "iShares iBoxx $ High Yield Corporate Bond ETF", "category": "Corporate HY"},
    {"symbol": "VCIT", "name": "Vanguard Intermediate-Term Corporate Bond ETF", "category": "Corporate Medium"},
    {"symbol": "VCSH", "name": "Vanguard Short-Term Corporate Bond ETF", "category": "Corporate Short"},
    {"symbol": "VCLT", "name": "Vanguard Long-Term Corporate Bond ETF", "category": "Corporate Long"},
    {"symbol": "USIG", "name": "iShares Broad USD Investment Grade Corporate Bond ETF", "category": "Corporate IG Broad"},
    
    # Aggregate/Total Bond Market
    {"symbol": "BND", "name": "Vanguard Total Bond Market ETF", "category": "Aggregate US"},
    {"symbol": "AGG", "name": "iShares Core U.S. Aggregate Bond ETF", "category": "Aggregate US"},
    {"symbol": "SCHZ", "name": "Schwab U.S. Aggregate Bond ETF", "category": "Aggregate US"},
    
    # Municipal Bonds
    {"symbol": "MUB", "name": "iShares National Muni Bond ETF", "category": "Municipal"},
    {"symbol": "VTEB", "name": "Vanguard Tax-Exempt Bond ETF", "category": "Municipal"},
    {"symbol": "TFI", "name": "SPDR Nuveen Bloomberg Municipal Bond ETF", "category": "Municipal"},
    
    # International Bonds
    {"symbol": "BNDX", "name": "Vanguard Total International Bond ETF", "category": "International"},
    {"symbol": "IAGG", "name": "iShares Core International Aggregate Bond ETF", "category": "International"},
    {"symbol": "EMB", "name": "iShares J.P. Morgan USD Emerging Markets Bond ETF", "category": "Emerging Markets"},
    {"symbol": "VWOB", "name": "Vanguard Emerging Markets Government Bond ETF", "category": "Emerging Markets"},
    
    # Floating Rate
    {"symbol": "FLOT", "name": "iShares Floating Rate Bond ETF", "category": "Floating Rate"},
    {"symbol": "FLRN", "name": "SPDR Bloomberg Investment Grade Floating Rate ETF", "category": "Floating Rate"},
]

# ═══════════════════════════════════════════════════════════════════════════
# FUTURES - Major contracts (Yahoo Finance format: SYMBOL=F)
# ═══════════════════════════════════════════════════════════════════════════
FUTURES = [
    # Equity Index Futures
    {"symbol": "ES=F", "name": "E-mini S&P 500 Future", "category": "Equity Index"},
    {"symbol": "NQ=F", "name": "E-mini Nasdaq 100 Future", "category": "Equity Index"},
    {"symbol": "YM=F", "name": "E-mini Dow Jones Future", "category": "Equity Index"},
    {"symbol": "RTY=F", "name": "E-mini Russell 2000 Future", "category": "Equity Index"},
    {"symbol": "VIX=F", "name": "VIX Future", "category": "Volatility"},
    
    # Treasury Futures
    {"symbol": "ZB=F", "name": "30-Year Treasury Bond Future", "category": "Treasury"},
    {"symbol": "ZN=F", "name": "10-Year Treasury Note Future", "category": "Treasury"},
    {"symbol": "ZF=F", "name": "5-Year Treasury Note Future", "category": "Treasury"},
    {"symbol": "ZT=F", "name": "2-Year Treasury Note Future", "category": "Treasury"},
    
    # Energy Futures
    {"symbol": "CL=F", "name": "Crude Oil WTI Future", "category": "Energy"},
    {"symbol": "BZ=F", "name": "Brent Crude Oil Future", "category": "Energy"},
    {"symbol": "NG=F", "name": "Natural Gas Future", "category": "Energy"},
    {"symbol": "HO=F", "name": "Heating Oil Future", "category": "Energy"},
    {"symbol": "RB=F", "name": "RBOB Gasoline Future", "category": "Energy"},
    
    # Metal Futures
    {"symbol": "GC=F", "name": "Gold Future", "category": "Precious Metals"},
    {"symbol": "SI=F", "name": "Silver Future", "category": "Precious Metals"},
    {"symbol": "PL=F", "name": "Platinum Future", "category": "Precious Metals"},
    {"symbol": "PA=F", "name": "Palladium Future", "category": "Precious Metals"},
    {"symbol": "HG=F", "name": "Copper Future", "category": "Industrial Metals"},
    
    # Agricultural Futures
    {"symbol": "ZC=F", "name": "Corn Future", "category": "Agriculture"},
    {"symbol": "ZW=F", "name": "Wheat Future", "category": "Agriculture"},
    {"symbol": "ZS=F", "name": "Soybean Future", "category": "Agriculture"},
    {"symbol": "KC=F", "name": "Coffee Future", "category": "Agriculture"},
    {"symbol": "SB=F", "name": "Sugar Future", "category": "Agriculture"},
    {"symbol": "CT=F", "name": "Cotton Future", "category": "Agriculture"},
    {"symbol": "CC=F", "name": "Cocoa Future", "category": "Agriculture"},
    {"symbol": "LE=F", "name": "Live Cattle Future", "category": "Livestock"},
    {"symbol": "HE=F", "name": "Lean Hogs Future", "category": "Livestock"},
    
    # Currency Futures
    {"symbol": "6E=F", "name": "Euro FX Future", "category": "Currency"},
    {"symbol": "6J=F", "name": "Japanese Yen Future", "category": "Currency"},
    {"symbol": "6B=F", "name": "British Pound Future", "category": "Currency"},
    {"symbol": "6A=F", "name": "Australian Dollar Future", "category": "Currency"},
    {"symbol": "6C=F", "name": "Canadian Dollar Future", "category": "Currency"},
    {"symbol": "6S=F", "name": "Swiss Franc Future", "category": "Currency"},
]

# ═══════════════════════════════════════════════════════════════════════════
# OPTIONS - Major underlyings (options chain fetched on-demand)
# These are stored as OPTION type so they appear in the Options filter
# ═══════════════════════════════════════════════════════════════════════════
MAJOR_OPTION_UNDERLYINGS = [
    # Mega-cap Tech (most liquid options)
    {"symbol": "AAPL", "name": "Apple Inc Options", "category": "Tech Options"},
    {"symbol": "MSFT", "name": "Microsoft Corp Options", "category": "Tech Options"},
    {"symbol": "GOOGL", "name": "Alphabet Inc Options", "category": "Tech Options"},
    {"symbol": "AMZN", "name": "Amazon.com Inc Options", "category": "Tech Options"},
    {"symbol": "META", "name": "Meta Platforms Inc Options", "category": "Tech Options"},
    {"symbol": "NVDA", "name": "NVIDIA Corp Options", "category": "Tech Options"},
    {"symbol": "TSLA", "name": "Tesla Inc Options", "category": "Tech Options"},
    
    # Index ETF Options (most liquid)
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Options", "category": "Index Options"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust Options", "category": "Index Options"},
    {"symbol": "IWM", "name": "iShares Russell 2000 ETF Options", "category": "Index Options"},
    {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average Options", "category": "Index Options"},
    {"symbol": "VIX", "name": "CBOE Volatility Index Options", "category": "Volatility Options"},
    
    # Sector ETF Options
    {"symbol": "XLF", "name": "Financial Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLE", "name": "Energy Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLK", "name": "Technology Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLV", "name": "Health Care Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLI", "name": "Industrial Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLP", "name": "Consumer Staples Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLY", "name": "Consumer Discretionary Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLU", "name": "Utilities Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLB", "name": "Materials Select Sector SPDR Options", "category": "Sector Options"},
    {"symbol": "XLRE", "name": "Real Estate Select Sector SPDR Options", "category": "Sector Options"},
    
    # Commodity ETF Options
    {"symbol": "GLD", "name": "SPDR Gold Shares Options", "category": "Commodity Options"},
    {"symbol": "SLV", "name": "iShares Silver Trust Options", "category": "Commodity Options"},
    {"symbol": "USO", "name": "United States Oil Fund Options", "category": "Commodity Options"},
    {"symbol": "UNG", "name": "United States Natural Gas Fund Options", "category": "Commodity Options"},
    
    # Other high-volume option underlyings
    {"symbol": "AMD", "name": "Advanced Micro Devices Options", "category": "Tech Options"},
    {"symbol": "INTC", "name": "Intel Corp Options", "category": "Tech Options"},
    {"symbol": "BA", "name": "Boeing Co Options", "category": "Industrial Options"},
    {"symbol": "JPM", "name": "JPMorgan Chase Options", "category": "Financial Options"},
    {"symbol": "GS", "name": "Goldman Sachs Options", "category": "Financial Options"},
    {"symbol": "BAC", "name": "Bank of America Options", "category": "Financial Options"},
    {"symbol": "WFC", "name": "Wells Fargo Options", "category": "Financial Options"},
    {"symbol": "C", "name": "Citigroup Options", "category": "Financial Options"},
]


def add_assets_to_universe(store: SQLiteStore, assets: List[Dict], asset_type: AssetType, exchange_code: str = "US"):
    """Add a list of assets to the universe."""
    added = 0
    skipped = 0
    
    for asset_data in assets:
        symbol = asset_data["symbol"]
        name = asset_data["name"]
        category = asset_data.get("category", "")
        
        # Create asset_id
        asset_id = f"{symbol}.{exchange_code}"
        
        # Check if already exists
        existing = store.get_asset(asset_id)
        if existing:
            skipped += 1
            continue
        
        try:
            # Create Asset object
            asset = Asset(
                asset_id=asset_id,
                symbol=symbol,
                name=name,
                asset_type=asset_type,
                market_scope="US_EU",
                market_code=exchange_code,
                exchange_code=exchange_code,
                exchange=exchange_code,
                currency="USD",
                country="US",
                tier=2,  # Tier 2 for derivatives
                active=True,
                sector=category,
                industry=asset_type.value,
                data_source="YFINANCE",
            )
            store.upsert_asset(asset, market_scope="US_EU")
            added += 1
            logger.info(f"Added {asset_type.value}: {symbol} - {name}")
        except Exception as e:
            logger.error(f"Failed to add {symbol}: {e}")
    
    return added, skipped


def verify_yfinance_data(symbols: List[str], asset_type: str) -> Dict[str, bool]:
    """Verify that yfinance can fetch data for these symbols."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed")
        return {}
    
    results = {}
    logger.info(f"Verifying {len(symbols)} {asset_type} symbols with yfinance...")
    
    for symbol in symbols[:5]:  # Test first 5 only
        try:
            data = yf.download(symbol, period='5d', progress=False)
            results[symbol] = len(data) > 0
            if results[symbol]:
                last_price = data['Close'].iloc[-1] if len(data) > 0 else 0
                logger.info(f"  ✓ {symbol}: {len(data)} bars, last price: {last_price:.2f}")
            else:
                logger.warning(f"  ✗ {symbol}: No data")
            time.sleep(0.3)  # Rate limit
        except Exception as e:
            results[symbol] = False
            logger.warning(f"  ✗ {symbol}: Error - {e}")
    
    return results


def main():
    """Main function to add derivatives to universe."""
    print("=" * 60)
    print("MarketGPS - Add Derivatives Universe")
    print("=" * 60)
    print(f"Source: Yahoo Finance (free)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize store
    store = SQLiteStore()
    
    # Verify yfinance is working
    print("Testing yfinance connectivity...")
    
    # Test a sample from each category
    bond_test = verify_yfinance_data(["TLT", "BND", "AGG"], "Bond ETFs")
    if not any(bond_test.values()):
        logger.warning("Bond ETF verification failed - proceeding anyway")
    
    future_test = verify_yfinance_data(["ES=F", "GC=F", "CL=F"], "Futures")
    if not any(future_test.values()):
        logger.warning("Futures verification failed - proceeding anyway")
    
    print()
    
    # Add Bond ETFs
    print("-" * 60)
    print("Adding Bond ETFs to universe...")
    print("-" * 60)
    added, skipped = add_assets_to_universe(store, BOND_ETFS, AssetType.BOND, "US")
    print(f"Bond ETFs: {added} added, {skipped} already existed")
    
    # Add Futures
    print("-" * 60)
    print("Adding Futures to universe...")
    print("-" * 60)
    added, skipped = add_assets_to_universe(store, FUTURES, AssetType.FUTURE, "CME")
    print(f"Futures: {added} added, {skipped} already existed")
    
    # Add Option Underlyings
    print("-" * 60)
    print("Adding Option Underlyings to universe...")
    print("-" * 60)
    added, skipped = add_assets_to_universe(store, MAJOR_OPTION_UNDERLYINGS, AssetType.OPTION, "CBOE")
    print(f"Options: {added} added, {skipped} already existed")
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Count by type
    with store._get_connection() as conn:
        cursor = conn.execute("""
            SELECT asset_type, COUNT(*) as count 
            FROM universe 
            WHERE active = 1 
            GROUP BY asset_type
        """)
        counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    print(f"Total assets by type:")
    for asset_type, count in sorted(counts.items()):
        print(f"  {asset_type}: {count}")
    
    print()
    print("✓ Derivatives added successfully!")
    print()
    print("Next steps:")
    print("1. Run the scoring pipeline to calculate scores for new assets")
    print("2. Verify display in the dashboard")


if __name__ == "__main__":
    main()
