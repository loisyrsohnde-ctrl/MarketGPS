"""
MarketGPS - Score Alternative Assets
Scores Forex, Crypto, Commodities, Bonds, Options, Futures.

SAFE: Only updates scores, does not modify universe data.

Run: python scripts/score_alternative_assets.py --type CRYPTO --limit 50
     python scripts/score_alternative_assets.py --type FX --limit 30
     python scripts/score_alternative_assets.py --all
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Optional
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import AssetType, Score
from core.config import get_logger, get_config
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore

logger = get_logger(__name__)


class AlternativeAssetScorer:
    """
    Dedicated scorer for alternative assets (Forex, Crypto, Commodities, etc.)
    
    Uses simplified scoring methodology:
    - Momentum (60%): Price trend, RSI
    - Safety (40%): Volatility, max drawdown
    - No Value pillar (no fundamentals for these assets)
    """
    
    SUPPORTED_TYPES = ["FX", "CRYPTO", "COMMODITY", "BOND", "OPTION", "FUTURE"]
    
    def __init__(self, market_scope: str = "US_EU"):
        self._scope = market_scope
        self._config = get_config()
        self._store = SQLiteStore()
        self._parquet = ParquetStore(market_scope=market_scope)
        
        # Try to import yfinance for data fetching
        try:
            import yfinance as yf
            self._yf = yf
            logger.info("Using yfinance for data fetching")
        except ImportError:
            logger.warning("yfinance not available - will use cached data only")
            self._yf = None
    
    def get_assets_to_score(self, asset_type: str, limit: int = 100) -> List[str]:
        """Get assets of given type that need scoring."""
        with self._store._get_connection() as conn:
            cursor = conn.execute("""
                SELECT u.asset_id 
                FROM universe u
                LEFT JOIN scores_latest s ON u.asset_id = s.asset_id
                WHERE u.asset_type = ? AND u.active = 1
                ORDER BY 
                    CASE WHEN s.score_total IS NULL THEN 0 ELSE 1 END,
                    u.tier ASC,
                    s.updated_at ASC
                LIMIT ?
            """, (asset_type, limit))
            return [row[0] for row in cursor.fetchall()]
    
    def fetch_price_data(self, asset_id: str, days: int = 365) -> Optional[dict]:
        """Fetch price data using yfinance."""
        if not self._yf:
            return None
        
        # Convert asset_id to yfinance symbol
        symbol = self._convert_to_yfinance_symbol(asset_id)
        if not symbol:
            return None
        
        try:
            import pandas as pd
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            data = self._yf.download(
                symbol, 
                start=start_date.isoformat(), 
                end=end_date.isoformat(),
                progress=False
            )
            
            # Handle empty DataFrame
            if data is None or len(data) == 0:
                logger.warning(f"No data for {asset_id}")
                return None
            
            if len(data) < 20:
                logger.warning(f"Insufficient data for {asset_id}: {len(data)} bars")
                return None
            
            # Handle MultiIndex columns (newer yfinance returns MultiIndex)
            if isinstance(data.columns, pd.MultiIndex):
                # Flatten MultiIndex: ('Close', 'BTC-USD') -> 'Close'
                data.columns = data.columns.get_level_values(0)
            
            # Get close prices as Series
            close = data['Close'].squeeze()  # Ensure it's a Series, not DataFrame
            
            # Ensure close is a Series
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            
            # Returns
            returns = close.pct_change().dropna()
            
            # Volatility (annualized)
            vol_annual = float(returns.std() * (252 ** 0.5) * 100)
            
            # RSI (14-day)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1]) if len(rsi) > 0 and pd.notna(rsi.iloc[-1]) else 50.0
            
            # Z-score (current price vs 50-day mean)
            sma50 = close.rolling(50).mean()
            std50 = close.rolling(50).std()
            zscore = (close - sma50) / std50
            current_zscore = float(zscore.iloc[-1]) if len(zscore) > 0 and pd.notna(zscore.iloc[-1]) else 0.0
            
            # Max Drawdown
            rolling_max = close.cummax()
            drawdown = (close - rolling_max) / rolling_max
            max_dd = float(abs(drawdown.min()) * 100)
            
            # SMA200
            if len(close) >= 200:
                sma200_val = close.rolling(200).mean().iloc[-1]
            else:
                sma200_val = close.mean()
            sma200 = float(sma200_val) if pd.notna(sma200_val) else float(close.iloc[-1])
            
            # Last price
            last_price = float(close.iloc[-1])
            
            # Momentum score (0-100)
            # RSI in optimal range (40-70) = high score
            if 40 <= current_rsi <= 70:
                rsi_score = 80 + (10 - abs(current_rsi - 55) / 1.5)
            elif current_rsi < 40:
                rsi_score = max(30, current_rsi)  # Oversold = moderate score
            else:
                rsi_score = max(20, 100 - current_rsi)  # Overbought = lower score
            
            # Trend score (price vs SMA200)
            trend_strength = (last_price - sma200) / sma200 * 100 if sma200 > 0 else 0
            trend_score = min(100, max(0, 50 + trend_strength * 2))
            
            momentum = (rsi_score * 0.5 + trend_score * 0.5)
            
            # Safety score (0-100)
            # Lower volatility = higher safety
            vol_score = max(0, min(100, 100 - vol_annual * 2))
            
            # Lower drawdown = higher safety
            dd_score = max(0, min(100, 100 - max_dd * 2))
            
            safety = (vol_score * 0.6 + dd_score * 0.4)
            
            # Total score (Momentum 60%, Safety 40%)
            total = momentum * 0.60 + safety * 0.40
            
            return {
                "score_total": round(total, 1),
                "score_momentum": round(momentum, 1),
                "score_safety": round(safety, 1),
                "score_value": None,  # No fundamentals
                "rsi": round(current_rsi, 1),
                "zscore": round(current_zscore, 2),
                "vol_annual": round(vol_annual, 1),
                "max_drawdown": round(max_dd, 1),
                "sma200": round(sma200, 4),
                "last_price": round(last_price, 4),
                "confidence": min(90, len(data) // 3),  # More data = higher confidence
                "bars": len(data),
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {asset_id}: {e}")
            return None
    
    def _convert_to_yfinance_symbol(self, asset_id: str) -> Optional[str]:
        """Convert our asset_id to yfinance symbol format."""
        parts = asset_id.split(".")
        if len(parts) != 2:
            return None
        
        symbol, exchange = parts
        
        # Forex: EURUSD.FX -> EURUSD=X
        if exchange == "FX":
            return f"{symbol}=X"
        
        # Crypto: BTC.CRYPTO -> BTC-USD
        if exchange == "CRYPTO":
            return f"{symbol}-USD"
        
        # Futures: ES.CME -> ES=F
        if exchange in ["CME", "COMEX", "CBOT", "NYMEX"]:
            return f"{symbol}=F"
        
        # Commodities/Bonds/Options: use symbol directly (ETFs)
        if exchange in ["CMDTY", "US", "CBOE"]:
            return symbol
        
        # Default: try symbol directly
        return symbol
    
    def score_asset(self, asset_id: str) -> Optional[Score]:
        """Score a single asset."""
        metrics = self.fetch_price_data(asset_id)
        if not metrics:
            return None
        
        # Get asset info
        asset = self._store.get_asset(asset_id)
        if not asset:
            return None
        
        # Create Score object
        score = Score(
            asset_id=asset_id,
            score_total=metrics["score_total"],
            score_value=metrics["score_value"],
            score_momentum=metrics["score_momentum"],
            score_safety=metrics["score_safety"],
            confidence=metrics["confidence"],
            rsi=metrics["rsi"],
            zscore=metrics["zscore"],
            vol_annual=metrics["vol_annual"],
            max_drawdown=metrics["max_drawdown"],
            sma200=metrics["sma200"],
            last_price=metrics["last_price"],
            state_label="Équilibre",
            fundamentals_available=False,
        )
        
        return score
    
    def score_batch(self, asset_type: str, limit: int = 50) -> dict:
        """Score a batch of assets of given type."""
        assets = self.get_assets_to_score(asset_type, limit)
        
        if not assets:
            logger.info(f"No {asset_type} assets to score")
            return {"processed": 0, "success": 0, "failed": 0}
        
        logger.info(f"Scoring {len(assets)} {asset_type} assets...")
        
        success = 0
        failed = 0
        
        for i, asset_id in enumerate(assets):
            try:
                score = self.score_asset(asset_id)
                if score:
                    self._store.upsert_score(score, market_scope=self._scope)
                    success += 1
                    logger.info(f"[{i+1}/{len(assets)}] ✓ {asset_id}: {score.score_total}")
                else:
                    failed += 1
                    logger.warning(f"[{i+1}/{len(assets)}] ✗ {asset_id}: No data")
                
                # Rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                failed += 1
                logger.error(f"[{i+1}/{len(assets)}] ✗ {asset_id}: {e}")
        
        return {
            "processed": len(assets),
            "success": success,
            "failed": failed,
        }


def main():
    parser = argparse.ArgumentParser(description="Score alternative assets")
    parser.add_argument("--type", choices=AlternativeAssetScorer.SUPPORTED_TYPES,
                        help="Asset type to score")
    parser.add_argument("--all", action="store_true", help="Score all alternative asset types")
    parser.add_argument("--limit", type=int, default=50, help="Max assets to score per type")
    parser.add_argument("--scope", default="US_EU", help="Market scope")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MarketGPS - Alternative Asset Scorer")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scorer = AlternativeAssetScorer(market_scope=args.scope)
    
    if args.all:
        types_to_score = AlternativeAssetScorer.SUPPORTED_TYPES
    elif args.type:
        types_to_score = [args.type]
    else:
        print("Please specify --type or --all")
        sys.exit(1)
    
    total_results = {"processed": 0, "success": 0, "failed": 0}
    
    for asset_type in types_to_score:
        print(f"\n{'='*60}")
        print(f"Scoring {asset_type} assets...")
        print("=" * 60)
        
        result = scorer.score_batch(asset_type, limit=args.limit)
        
        print(f"\n{asset_type} Results:")
        print(f"  Processed: {result['processed']}")
        print(f"  Success: {result['success']}")
        print(f"  Failed: {result['failed']}")
        
        total_results["processed"] += result["processed"]
        total_results["success"] += result["success"]
        total_results["failed"] += result["failed"]
    
    print("\n" + "=" * 60)
    print("TOTAL RESULTS")
    print("=" * 60)
    print(f"  Processed: {total_results['processed']}")
    print(f"  Success: {total_results['success']}")
    print(f"  Failed: {total_results['failed']}")
    print()
    print("✓ Alternative asset scoring complete!")


if __name__ == "__main__":
    main()
