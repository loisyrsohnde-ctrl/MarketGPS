"""
MarketGPS - Add Crypto Universe
Adds top cryptocurrencies to the universe using Yahoo Finance.

SAFE: Uses UPSERT - does not delete existing data.

Run: python scripts/add_crypto_universe.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import AssetType, Asset
from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CRYPTOCURRENCIES - Top coins by market cap
# Format: Yahoo Finance uses BTC-USD format
# ═══════════════════════════════════════════════════════════════════════════

# Top 10 (Mega Cap)
TOP_10_CRYPTO = [
    {"symbol": "BTC-USD", "name": "Bitcoin", "category": "Layer 1"},
    {"symbol": "ETH-USD", "name": "Ethereum", "category": "Layer 1"},
    {"symbol": "USDT-USD", "name": "Tether", "category": "Stablecoin"},
    {"symbol": "BNB-USD", "name": "Binance Coin", "category": "Exchange"},
    {"symbol": "SOL-USD", "name": "Solana", "category": "Layer 1"},
    {"symbol": "XRP-USD", "name": "XRP", "category": "Payments"},
    {"symbol": "USDC-USD", "name": "USD Coin", "category": "Stablecoin"},
    {"symbol": "ADA-USD", "name": "Cardano", "category": "Layer 1"},
    {"symbol": "DOGE-USD", "name": "Dogecoin", "category": "Meme"},
    {"symbol": "TRX-USD", "name": "Tron", "category": "Layer 1"},
]

# Top 11-30 (Large Cap)
LARGE_CAP_CRYPTO = [
    {"symbol": "AVAX-USD", "name": "Avalanche", "category": "Layer 1"},
    {"symbol": "LINK-USD", "name": "Chainlink", "category": "Oracle"},
    {"symbol": "TON-USD", "name": "Toncoin", "category": "Layer 1"},
    {"symbol": "SHIB-USD", "name": "Shiba Inu", "category": "Meme"},
    {"symbol": "DOT-USD", "name": "Polkadot", "category": "Layer 0"},
    {"symbol": "BCH-USD", "name": "Bitcoin Cash", "category": "Payments"},
    {"symbol": "LTC-USD", "name": "Litecoin", "category": "Payments"},
    {"symbol": "XLM-USD", "name": "Stellar", "category": "Payments"},
    {"symbol": "UNI-USD", "name": "Uniswap", "category": "DeFi"},
    {"symbol": "ATOM-USD", "name": "Cosmos", "category": "Layer 0"},
    {"symbol": "XMR-USD", "name": "Monero", "category": "Privacy"},
    {"symbol": "ETC-USD", "name": "Ethereum Classic", "category": "Layer 1"},
    {"symbol": "NEAR-USD", "name": "NEAR Protocol", "category": "Layer 1"},
    {"symbol": "APT-USD", "name": "Aptos", "category": "Layer 1"},
    {"symbol": "ICP-USD", "name": "Internet Computer", "category": "Layer 1"},
    {"symbol": "FIL-USD", "name": "Filecoin", "category": "Storage"},
    {"symbol": "HBAR-USD", "name": "Hedera", "category": "Layer 1"},
    {"symbol": "VET-USD", "name": "VeChain", "category": "Supply Chain"},
    {"symbol": "MKR-USD", "name": "Maker", "category": "DeFi"},
    {"symbol": "ARB-USD", "name": "Arbitrum", "category": "Layer 2"},
]

# Top 31-60 (Mid Cap)
MID_CAP_CRYPTO = [
    {"symbol": "OP-USD", "name": "Optimism", "category": "Layer 2"},
    {"symbol": "INJ-USD", "name": "Injective", "category": "DeFi"},
    {"symbol": "AAVE-USD", "name": "Aave", "category": "DeFi"},
    {"symbol": "RNDR-USD", "name": "Render Token", "category": "AI/GPU"},
    {"symbol": "IMX-USD", "name": "Immutable X", "category": "Gaming"},
    {"symbol": "GRT-USD", "name": "The Graph", "category": "Data"},
    {"symbol": "SUI-USD", "name": "Sui", "category": "Layer 1"},
    {"symbol": "ALGO-USD", "name": "Algorand", "category": "Layer 1"},
    {"symbol": "FTM-USD", "name": "Fantom", "category": "Layer 1"},
    {"symbol": "THETA-USD", "name": "Theta Network", "category": "Media"},
    {"symbol": "SAND-USD", "name": "The Sandbox", "category": "Metaverse"},
    {"symbol": "MANA-USD", "name": "Decentraland", "category": "Metaverse"},
    {"symbol": "AXS-USD", "name": "Axie Infinity", "category": "Gaming"},
    {"symbol": "FLOW-USD", "name": "Flow", "category": "NFT"},
    {"symbol": "XTZ-USD", "name": "Tezos", "category": "Layer 1"},
    {"symbol": "SNX-USD", "name": "Synthetix", "category": "DeFi"},
    {"symbol": "CRV-USD", "name": "Curve DAO Token", "category": "DeFi"},
    {"symbol": "RUNE-USD", "name": "THORChain", "category": "DeFi"},
    {"symbol": "LDO-USD", "name": "Lido DAO", "category": "Staking"},
    {"symbol": "KAVA-USD", "name": "Kava", "category": "DeFi"},
    {"symbol": "ENS-USD", "name": "Ethereum Name Service", "category": "Infrastructure"},
    {"symbol": "CFX-USD", "name": "Conflux", "category": "Layer 1"},
    {"symbol": "EGLD-USD", "name": "MultiversX", "category": "Layer 1"},
    {"symbol": "ZEC-USD", "name": "Zcash", "category": "Privacy"},
    {"symbol": "DYDX-USD", "name": "dYdX", "category": "DeFi"},
    {"symbol": "1INCH-USD", "name": "1inch", "category": "DeFi"},
    {"symbol": "COMP-USD", "name": "Compound", "category": "DeFi"},
    {"symbol": "RPL-USD", "name": "Rocket Pool", "category": "Staking"},
    {"symbol": "BLUR-USD", "name": "Blur", "category": "NFT"},
    {"symbol": "FET-USD", "name": "Fetch.ai", "category": "AI"},
]

# Top 61-100 (Small Cap but notable)
SMALL_CAP_CRYPTO = [
    {"symbol": "PEPE-USD", "name": "Pepe", "category": "Meme"},
    {"symbol": "WLD-USD", "name": "Worldcoin", "category": "AI"},
    {"symbol": "SEI-USD", "name": "Sei", "category": "Layer 1"},
    {"symbol": "MINA-USD", "name": "Mina Protocol", "category": "Layer 1"},
    {"symbol": "GMT-USD", "name": "STEPN", "category": "Move2Earn"},
    {"symbol": "FLOKI-USD", "name": "Floki", "category": "Meme"},
    {"symbol": "GALA-USD", "name": "Gala", "category": "Gaming"},
    {"symbol": "CAKE-USD", "name": "PancakeSwap", "category": "DeFi"},
    {"symbol": "CELO-USD", "name": "Celo", "category": "Layer 1"},
    {"symbol": "ROSE-USD", "name": "Oasis Network", "category": "Privacy"},
    {"symbol": "ZIL-USD", "name": "Zilliqa", "category": "Layer 1"},
    {"symbol": "ENJ-USD", "name": "Enjin Coin", "category": "Gaming"},
    {"symbol": "BAT-USD", "name": "Basic Attention Token", "category": "Web3"},
    {"symbol": "CHZ-USD", "name": "Chiliz", "category": "Sports"},
    {"symbol": "DASH-USD", "name": "Dash", "category": "Payments"},
    {"symbol": "NEO-USD", "name": "Neo", "category": "Layer 1"},
    {"symbol": "WAVES-USD", "name": "Waves", "category": "Layer 1"},
    {"symbol": "QTUM-USD", "name": "Qtum", "category": "Layer 1"},
    {"symbol": "IOTA-USD", "name": "IOTA", "category": "IoT"},
    {"symbol": "KSM-USD", "name": "Kusama", "category": "Layer 0"},
    {"symbol": "ZRX-USD", "name": "0x", "category": "DeFi"},
    {"symbol": "YFI-USD", "name": "yearn.finance", "category": "DeFi"},
    {"symbol": "SUSHI-USD", "name": "SushiSwap", "category": "DeFi"},
    {"symbol": "UMA-USD", "name": "UMA", "category": "DeFi"},
    {"symbol": "OCEAN-USD", "name": "Ocean Protocol", "category": "Data"},
    {"symbol": "ANKR-USD", "name": "Ankr", "category": "Infrastructure"},
    {"symbol": "SKL-USD", "name": "SKALE", "category": "Layer 2"},
    {"symbol": "AUDIO-USD", "name": "Audius", "category": "Media"},
    {"symbol": "MASK-USD", "name": "Mask Network", "category": "Web3"},
    {"symbol": "API3-USD", "name": "API3", "category": "Oracle"},
    {"symbol": "STORJ-USD", "name": "Storj", "category": "Storage"},
    {"symbol": "LRC-USD", "name": "Loopring", "category": "Layer 2"},
    {"symbol": "BAND-USD", "name": "Band Protocol", "category": "Oracle"},
    {"symbol": "REN-USD", "name": "Ren", "category": "DeFi"},
    {"symbol": "OMG-USD", "name": "OMG Network", "category": "Layer 2"},
    {"symbol": "BNT-USD", "name": "Bancor", "category": "DeFi"},
    {"symbol": "CELR-USD", "name": "Celer Network", "category": "Layer 2"},
    {"symbol": "NMR-USD", "name": "Numeraire", "category": "AI"},
    {"symbol": "RAY-USD", "name": "Raydium", "category": "DeFi"},
    {"symbol": "SRM-USD", "name": "Serum", "category": "DeFi"},
]

# All cryptos combined
ALL_CRYPTO = TOP_10_CRYPTO + LARGE_CAP_CRYPTO + MID_CAP_CRYPTO + SMALL_CAP_CRYPTO


def add_crypto_to_universe(store: SQLiteStore, cryptos: List[Dict], tier: int) -> tuple:
    """Add cryptocurrencies to the universe."""
    added = 0
    skipped = 0
    
    for crypto in cryptos:
        symbol = crypto["symbol"]
        # Create a clean asset_id (BTC-USD -> BTC.CRYPTO)
        clean_symbol = symbol.replace("-USD", "")
        asset_id = f"{clean_symbol}.CRYPTO"
        
        # Check if already exists
        existing = store.get_asset(asset_id)
        if existing:
            skipped += 1
            continue
        
        try:
            asset = Asset(
                asset_id=asset_id,
                symbol=clean_symbol,
                name=crypto["name"],
                asset_type=AssetType.CRYPTO,
                market_scope="US_EU",  # Crypto is global but we put it in US_EU
                market_code="CRYPTO",
                exchange_code="CRYPTO",
                exchange="Cryptocurrency",
                currency="USD",
                country="GLOBAL",
                tier=tier,
                active=True,
                sector=crypto["category"],
                industry="Cryptocurrency",
                data_source="YFINANCE",
            )
            store.upsert_asset(asset, market_scope="US_EU")
            added += 1
            logger.info(f"Added CRYPTO: {clean_symbol} - {crypto['name']} ({crypto['category']})")
        except Exception as e:
            logger.error(f"Failed to add {symbol}: {e}")
    
    return added, skipped


def verify_yfinance_crypto():
    """Verify that yfinance can fetch crypto data."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed")
        return False
    
    print("Testing yfinance Crypto connectivity...")
    test_cryptos = ["BTC-USD", "ETH-USD", "SOL-USD"]
    
    for symbol in test_cryptos:
        try:
            data = yf.download(symbol, period='5d', progress=False)
            if len(data) > 0:
                last_price = data['Close'].iloc[-1]
                print(f"  ✓ {symbol}: {len(data)} bars, last: ${last_price:,.2f}")
            else:
                print(f"  ✗ {symbol}: No data")
        except Exception as e:
            print(f"  ✗ {symbol}: Error - {e}")
    
    return True


def main():
    """Main function to add Cryptocurrencies to universe."""
    print("=" * 60)
    print("MarketGPS - Add Crypto Universe")
    print("=" * 60)
    print(f"Source: Yahoo Finance")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize store
    store = SQLiteStore()
    
    # Verify yfinance
    verify_yfinance_crypto()
    print()
    
    total_added = 0
    total_skipped = 0
    
    # Add Top 10 (Tier 1 - highest priority)
    print("-" * 60)
    print("Adding Top 10 Cryptocurrencies (Tier 1)...")
    print("-" * 60)
    added, skipped = add_crypto_to_universe(store, TOP_10_CRYPTO, tier=1)
    print(f"Top 10: {added} added, {skipped} already existed")
    total_added += added
    total_skipped += skipped
    
    # Add Large Cap (Tier 1)
    print("-" * 60)
    print("Adding Large Cap Cryptocurrencies (Tier 1)...")
    print("-" * 60)
    added, skipped = add_crypto_to_universe(store, LARGE_CAP_CRYPTO, tier=1)
    print(f"Large Cap: {added} added, {skipped} already existed")
    total_added += added
    total_skipped += skipped
    
    # Add Mid Cap (Tier 2)
    print("-" * 60)
    print("Adding Mid Cap Cryptocurrencies (Tier 2)...")
    print("-" * 60)
    added, skipped = add_crypto_to_universe(store, MID_CAP_CRYPTO, tier=2)
    print(f"Mid Cap: {added} added, {skipped} already existed")
    total_added += added
    total_skipped += skipped
    
    # Add Small Cap (Tier 3)
    print("-" * 60)
    print("Adding Small Cap Cryptocurrencies (Tier 3)...")
    print("-" * 60)
    added, skipped = add_crypto_to_universe(store, SMALL_CAP_CRYPTO, tier=3)
    print(f"Small Cap: {added} added, {skipped} already existed")
    total_added += added
    total_skipped += skipped
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    with store._get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM universe 
            WHERE asset_type = 'CRYPTO' AND active = 1
        """)
        crypto_count = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT sector, COUNT(*) as count 
            FROM universe 
            WHERE asset_type = 'CRYPTO' AND active = 1
            GROUP BY sector
            ORDER BY count DESC
        """)
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    print(f"Total Cryptocurrencies: {crypto_count}")
    print(f"Added this run: {total_added}")
    print(f"Already existed: {total_skipped}")
    print()
    print("By Category:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    print()
    print("✓ Crypto universe added successfully!")
    print()
    print("Next: Run scoring for Crypto assets")


if __name__ == "__main__":
    main()
