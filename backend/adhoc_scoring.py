"""
MarketGPS - Ad-Hoc Scoring Service
==================================
Score any asset on-the-fly, even if it's not in the universe.
Uses the same scoring algorithms as the batch pipeline.
"""

import os
import sys
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config, get_logger
from core.models import Asset, AssetType, Score, GatingStatus

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Constants & Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Default exchange mappings for automatic symbol resolution
EXCHANGE_SUFFIXES = {
    "US": ".US",
    "NYSE": ".US",
    "NASDAQ": ".US",
    "PA": ".PA",
    "PARIS": ".PA",
    "XETRA": ".XETRA",
    "FRANKFURT": ".XETRA",
    "LSE": ".LSE",
    "LONDON": ".LSE",
    "JSE": ".JSE",
    "JOHANNESBURG": ".JSE",
    "NG": ".NG",
    "NIGERIA": ".NG",
    "CA": ".CA",
    "EGYPT": ".CA",
    "BRVM": ".BRVM",
    "HK": ".HK",
    "HONGKONG": ".HK",
    "AS": ".AS",
    "AMSTERDAM": ".AS",
    "TO": ".TO",
    "TORONTO": ".TO",
    "SW": ".SW",
    "SWISS": ".SW",
    "MI": ".MI",
    "MILAN": ".MI",
    "MC": ".MC",
    "MADRID": ".MC",
    "SG": ".SG",
    "SINGAPORE": ".SG",
    "AU": ".AU",
    "AUSTRALIA": ".AU",
}

# Market scope mapping based on exchange
EXCHANGE_TO_SCOPE = {
    ".US": "US_EU",
    ".PA": "US_EU",
    ".XETRA": "US_EU",
    ".LSE": "US_EU",
    ".AS": "US_EU",
    ".SW": "US_EU",
    ".MI": "US_EU",
    ".MC": "US_EU",
    ".TO": "US_EU",
    ".HK": "ASIA",
    ".SG": "ASIA",
    ".AU": "ASIA",
    ".JSE": "AFRICA",
    ".NG": "AFRICA",
    ".CA": "AFRICA",
    ".BRVM": "AFRICA",
}

# Asset type detection patterns
CRYPTO_SUFFIXES = ["-USD", "-EUR", "-GBP", "USDT", "BTC", "ETH"]
FX_PAIRS = ["EUR", "USD", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD"]


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AdHocScoringResult:
    """Result of an ad-hoc scoring request."""
    success: bool
    asset_id: str
    symbol: str
    name: Optional[str]
    asset_type: str
    market_scope: str
    exchange: str

    # Score components
    score_total: Optional[float] = None
    score_value: Optional[float] = None
    score_momentum: Optional[float] = None
    score_safety: Optional[float] = None
    confidence: Optional[int] = None

    # Technical metrics
    rsi: Optional[float] = None
    zscore: Optional[float] = None
    vol_annual: Optional[float] = None
    max_drawdown: Optional[float] = None
    last_price: Optional[float] = None
    sma200: Optional[float] = None
    price_vs_sma200: Optional[float] = None

    # Fundamentals (EQUITY only)
    pe_ratio: Optional[float] = None
    profit_margin: Optional[float] = None
    roe: Optional[float] = None
    market_cap: Optional[float] = None

    # Metadata
    state_label: Optional[str] = None
    data_points: int = 0
    data_source: str = "EODHD"
    scored_at: Optional[str] = None
    was_in_universe: bool = False
    added_to_universe: bool = False

    # Error info
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "asset_id": self.asset_id,
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type,
            "market_scope": self.market_scope,
            "exchange": self.exchange,
            "score_total": self.score_total,
            "score_value": self.score_value,
            "score_momentum": self.score_momentum,
            "score_safety": self.score_safety,
            "confidence": self.confidence,
            "rsi": self.rsi,
            "zscore": self.zscore,
            "vol_annual": self.vol_annual,
            "max_drawdown": self.max_drawdown,
            "last_price": self.last_price,
            "sma200": self.sma200,
            "price_vs_sma200": self.price_vs_sma200,
            "pe_ratio": self.pe_ratio,
            "profit_margin": self.profit_margin,
            "roe": self.roe,
            "market_cap": self.market_cap,
            "state_label": self.state_label,
            "data_points": self.data_points,
            "data_source": self.data_source,
            "scored_at": self.scored_at,
            "was_in_universe": self.was_in_universe,
            "added_to_universe": self.added_to_universe,
            "error": self.error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Ad-Hoc Scoring Service
# ═══════════════════════════════════════════════════════════════════════════════

class AdHocScoringService:
    """
    Service for scoring arbitrary assets on-the-fly.

    Features:
    - Auto-detects exchange and asset type from ticker
    - Fetches data from EODHD/yfinance
    - Uses standard scoring algorithms
    - Optionally adds asset to universe
    - Caches results in scores_latest

    Usage:
        service = AdHocScoringService()
        result = service.score_ticker("AAPL")  # Auto-detects .US
        result = service.score_ticker("VOD.LSE")  # Explicit exchange
        result = service.score_ticker("BTC-USD")  # Crypto
    """

    def __init__(self, store=None):
        """Initialize the ad-hoc scoring service."""
        self._config = get_config()
        self._store = store
        if self._store is None:
            from storage.sqlite_store import SQLiteStore
            self._store = SQLiteStore()

    def score_ticker(
        self,
        ticker: str,
        exchange: Optional[str] = None,
        asset_type: Optional[str] = None,
        add_to_universe: bool = False,
        force_refresh: bool = False,
    ) -> AdHocScoringResult:
        """
        Score any ticker on-the-fly.

        Args:
            ticker: Symbol (e.g., "AAPL", "VOD.LSE", "BTC-USD")
            exchange: Optional exchange override (e.g., "US", "LSE", "JSE")
            asset_type: Optional asset type override ("EQUITY", "ETF", "CRYPTO")
            add_to_universe: If True, add asset to universe after scoring
            force_refresh: If True, fetch fresh data even if cached

        Returns:
            AdHocScoringResult with score details or error
        """
        try:
            # Step 1: Resolve ticker to full asset_id
            resolved = self._resolve_ticker(ticker, exchange, asset_type)
            asset_id = resolved["asset_id"]
            symbol = resolved["symbol"]
            exchange_code = resolved["exchange"]
            detected_type = AssetType.from_string(resolved["asset_type"])
            market_scope = resolved["market_scope"]

            logger.info(f"Scoring ad-hoc: {asset_id} ({detected_type.value}) in {market_scope}")

            # Step 2: Check if already in universe
            existing_asset = self._store.get_asset(asset_id)
            was_in_universe = existing_asset is not None

            # Step 3: Check for cached score (< 24h old)
            if not force_refresh:
                cached = self._get_cached_score(asset_id)
                if cached:
                    logger.info(f"Returning cached score for {asset_id}")
                    return AdHocScoringResult(
                        success=True,
                        asset_id=asset_id,
                        symbol=symbol,
                        name=cached.get("name"),
                        asset_type=detected_type.value,
                        market_scope=market_scope,
                        exchange=exchange_code,
                        score_total=cached.get("score_total"),
                        score_value=cached.get("score_value"),
                        score_momentum=cached.get("score_momentum"),
                        score_safety=cached.get("score_safety"),
                        confidence=cached.get("confidence"),
                        rsi=cached.get("rsi"),
                        zscore=cached.get("zscore"),
                        vol_annual=cached.get("vol_annual"),
                        max_drawdown=cached.get("max_drawdown"),
                        last_price=cached.get("last_price"),
                        sma200=cached.get("sma200"),
                        state_label=cached.get("state_label"),
                        data_points=cached.get("data_points", 0),
                        scored_at=cached.get("updated_at"),
                        was_in_universe=was_in_universe,
                    )

            # Step 4: Fetch price data
            df, data_source = self._fetch_price_data(asset_id, market_scope)

            if df.empty or len(df) < 50:
                return AdHocScoringResult(
                    success=False,
                    asset_id=asset_id,
                    symbol=symbol,
                    name=None,
                    asset_type=detected_type.value,
                    market_scope=market_scope,
                    exchange=exchange_code,
                    error=f"Insufficient data: {len(df)} bars (minimum 50 required)",
                    data_points=len(df),
                    data_source=data_source,
                )

            # Step 5: Fetch fundamentals (EQUITY only)
            fundamentals = None
            if detected_type == AssetType.EQUITY:
                fundamentals = self._fetch_fundamentals(asset_id)

            # Step 6: Create temporary Asset object for scoring
            asset = Asset(
                asset_id=asset_id,
                symbol=symbol,
                name=fundamentals.get("name") if fundamentals else None,
                asset_type=detected_type,
                market_scope=market_scope,
                market_code=exchange_code,
                exchange_code=exchange_code,
                exchange=exchange_code,
            )

            # Step 7: Run scoring engine
            from pipeline.scoring import ScoringEngine

            engine = ScoringEngine()
            score = engine.compute_score(
                asset=asset,
                df=df,
                fundamentals=fundamentals,
                gating=None
            )

            # Step 8: Optionally add to universe
            added_to_universe = False
            if add_to_universe and not was_in_universe:
                try:
                    self._add_to_universe(asset, fundamentals)
                    added_to_universe = True
                    logger.info(f"Added {asset_id} to universe")
                except Exception as e:
                    logger.warning(f"Failed to add {asset_id} to universe: {e}")

            # Step 9: Save score to cache
            try:
                self._store.upsert_score(score, market_scope=market_scope)
            except Exception as e:
                logger.warning(f"Failed to cache score for {asset_id}: {e}")

            # Step 10: Build result
            return AdHocScoringResult(
                success=True,
                asset_id=asset_id,
                symbol=symbol,
                name=asset.name,
                asset_type=detected_type.value,
                market_scope=market_scope,
                exchange=exchange_code,
                score_total=score.score_total,
                score_value=score.score_value,
                score_momentum=score.score_momentum,
                score_safety=score.score_safety,
                confidence=score.confidence,
                rsi=score.rsi,
                zscore=score.zscore,
                vol_annual=score.vol_annual,
                max_drawdown=score.max_drawdown,
                last_price=score.last_price,
                sma200=score.sma200,
                state_label=score.state_label.value if score.state_label else None,
                data_points=len(df),
                data_source=data_source,
                scored_at=datetime.now().isoformat(),
                was_in_universe=was_in_universe,
                added_to_universe=added_to_universe,
                pe_ratio=fundamentals.get("pe_ratio") if fundamentals else None,
                profit_margin=fundamentals.get("profit_margin") if fundamentals else None,
                roe=fundamentals.get("return_on_equity") if fundamentals else None,
                market_cap=fundamentals.get("market_cap") if fundamentals else None,
            )

        except Exception as e:
            logger.error(f"Ad-hoc scoring failed for {ticker}: {e}")
            return AdHocScoringResult(
                success=False,
                asset_id=ticker,
                symbol=ticker,
                name=None,
                asset_type=asset_type or "UNKNOWN",
                market_scope="UNKNOWN",
                exchange=exchange or "UNKNOWN",
                error=str(e),
            )

    def score_batch(
        self,
        tickers: List[str],
        add_to_universe: bool = False,
    ) -> List[AdHocScoringResult]:
        """
        Score multiple tickers in batch.

        Args:
            tickers: List of tickers to score
            add_to_universe: If True, add assets to universe

        Returns:
            List of AdHocScoringResult
        """
        results = []
        for ticker in tickers:
            result = self.score_ticker(ticker, add_to_universe=add_to_universe)
            results.append(result)
        return results

    def _resolve_ticker(
        self,
        ticker: str,
        exchange: Optional[str] = None,
        asset_type: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Resolve ticker to full asset_id with exchange suffix.

        Returns:
            Dict with asset_id, symbol, exchange, asset_type, market_scope
        """
        ticker = ticker.strip().upper()

        # Check if already has exchange suffix
        if "." in ticker and not any(ticker.endswith(sfx) for sfx in CRYPTO_SUFFIXES):
            parts = ticker.rsplit(".", 1)
            symbol = parts[0]
            exchange_code = parts[1]
            asset_id = ticker
        else:
            # Need to add exchange suffix
            symbol = ticker

            # Check for crypto patterns
            is_crypto = any(sfx in ticker for sfx in CRYPTO_SUFFIXES)
            if is_crypto:
                exchange_code = "CC"  # Crypto
                asset_id = ticker  # Keep as-is for crypto
            else:
                # Use provided exchange or default to US
                exchange_code = exchange.upper() if exchange else "US"
                suffix = EXCHANGE_SUFFIXES.get(exchange_code, f".{exchange_code}")
                asset_id = f"{symbol}{suffix}"

        # Determine asset type
        if asset_type:
            detected_type = asset_type.upper()
        elif any(sfx in ticker for sfx in CRYPTO_SUFFIXES):
            detected_type = "CRYPTO"
        elif "/" in ticker or (len(ticker) == 6 and all(ticker[i:i+3] in FX_PAIRS for i in [0, 3])):
            detected_type = "FX"
        else:
            detected_type = "EQUITY"

        # Determine market scope
        suffix = f".{exchange_code}" if not asset_id.endswith(f".{exchange_code}") else asset_id[asset_id.rfind("."):]
        market_scope = EXCHANGE_TO_SCOPE.get(suffix, "US_EU")

        return {
            "asset_id": asset_id,
            "symbol": symbol,
            "exchange": exchange_code,
            "asset_type": detected_type,
            "market_scope": market_scope,
        }

    def _fetch_price_data(
        self,
        asset_id: str,
        market_scope: str,
    ) -> Tuple[Any, str]:
        """
        Fetch OHLCV data from provider.

        Returns:
            Tuple of (DataFrame, data_source_name)
        """
        import pandas as pd

        # Get lookback days from pipeline config
        lookback_days = getattr(self._config, 'pipeline', None)
        if lookback_days and hasattr(lookback_days, 'scoring_lookback_days'):
            lookback_days = lookback_days.scoring_lookback_days
        else:
            lookback_days = 365  # Default 1 year

        # Try EODHD first
        try:
            from providers.eodhd import EODHDProvider, EODHDQuotaExhaustedError

            provider = EODHDProvider()
            if provider.is_configured:
                end_date = date.today()
                start_date = date.today() - pd.Timedelta(days=lookback_days)

                df = provider.fetch_daily_bars(asset_id, start=start_date, end=end_date)

                if not df.empty:
                    logger.info(f"Fetched {len(df)} bars from EODHD for {asset_id}")
                    return df, "EODHD"
        except EODHDQuotaExhaustedError:
            logger.warning(f"EODHD quota exhausted, falling back to yfinance")
        except Exception as e:
            logger.warning(f"EODHD fetch failed for {asset_id}: {e}")

        # Fallback to yfinance
        try:
            from providers.yfinance_provider import YFinanceProvider

            yf_provider = YFinanceProvider()

            # Convert asset_id to yfinance format
            yf_ticker = self._convert_to_yfinance_ticker(asset_id)

            df = yf_provider.fetch_daily_bars(yf_ticker, lookback_days=lookback_days)

            if not df.empty:
                logger.info(f"Fetched {len(df)} bars from yfinance for {yf_ticker}")
                return df, "yfinance"
        except Exception as e:
            logger.warning(f"yfinance fetch failed for {asset_id}: {e}")

        return pd.DataFrame(), "none"

    def _convert_to_yfinance_ticker(self, asset_id: str) -> str:
        """Convert EODHD asset_id to yfinance ticker format."""
        # EODHD format: AAPL.US, VOD.LSE
        # yfinance format: AAPL, VOD.L

        if "." not in asset_id:
            return asset_id

        symbol, exchange = asset_id.rsplit(".", 1)

        yf_suffix_map = {
            "US": "",
            "LSE": ".L",
            "PA": ".PA",
            "XETRA": ".DE",
            "AS": ".AS",
            "SW": ".SW",
            "MI": ".MI",
            "MC": ".MC",
            "TO": ".TO",
            "HK": ".HK",
            "SG": ".SI",
            "AU": ".AX",
            "JSE": ".JO",
            "NG": ".NG",  # May not work in yfinance
        }

        suffix = yf_suffix_map.get(exchange, "")
        return f"{symbol}{suffix}"

    def _fetch_fundamentals(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data for an asset."""
        try:
            from providers.eodhd import EODHDProvider

            provider = EODHDProvider()
            if provider.is_configured:
                fundamentals = provider.fetch_fundamentals(asset_id)
                if fundamentals:
                    logger.info(f"Fetched fundamentals for {asset_id}: {len(fundamentals)} fields")
                    return fundamentals
        except Exception as e:
            logger.warning(f"Failed to fetch fundamentals for {asset_id}: {e}")

        return None

    def _get_cached_score(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get cached score if fresh (< 24 hours old)."""
        try:
            with self._store._get_connection() as conn:
                row = conn.execute("""
                    SELECT s.*, u.symbol, u.name, u.asset_type
                    FROM scores_latest s
                    LEFT JOIN universe u ON s.asset_id = u.asset_id
                    WHERE s.asset_id = ? AND s.score_total IS NOT NULL
                """, (asset_id,)).fetchone()

                if not row:
                    return None

                r = dict(row)
                updated_at = r.get("updated_at")

                if updated_at:
                    from datetime import timedelta
                    score_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    age = datetime.now() - score_time.replace(tzinfo=None)

                    if age < timedelta(hours=24):
                        return r

                return None
        except Exception as e:
            logger.warning(f"Cache lookup failed for {asset_id}: {e}")
            return None

    def _add_to_universe(self, asset: Asset, fundamentals: Optional[Dict]) -> None:
        """Add an asset to the universe table."""
        with self._store._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO universe (
                    asset_id, symbol, name, asset_type, market_scope, market_code,
                    exchange_code, exchange, currency, country, sector, industry,
                    active, tier, priority_level, data_source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 3, 3, 'adhoc', datetime('now'), datetime('now'))
            """, (
                asset.asset_id,
                asset.symbol,
                asset.name or fundamentals.get("name") if fundamentals else asset.symbol,
                asset.asset_type.value,
                asset.market_scope,
                asset.market_code,
                asset.exchange_code,
                asset.exchange,
                asset.currency,
                asset.country,
                fundamentals.get("sector") if fundamentals else None,
                fundamentals.get("industry") if fundamentals else None,
            ))
            logger.info(f"Added {asset.asset_id} to universe (tier 3, adhoc)")


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════════

def score_any_ticker(
    ticker: str,
    exchange: Optional[str] = None,
    add_to_universe: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to score any ticker.

    Args:
        ticker: Symbol (e.g., "AAPL", "VOD.LSE", "NPN.JSE")
        exchange: Optional exchange (e.g., "US", "LSE", "JSE")
        add_to_universe: If True, add to universe for future batch scoring

    Returns:
        Dict with score result

    Example:
        >>> result = score_any_ticker("AAPL")
        >>> print(f"Score: {result['score_total']}")

        >>> result = score_any_ticker("NPN", exchange="JSE")
        >>> print(f"Naspers score: {result['score_total']}")
    """
    service = AdHocScoringService()
    result = service.score_ticker(ticker, exchange=exchange, add_to_universe=add_to_universe)
    return result.to_dict()


# CLI support
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score any ticker ad-hoc")
    parser.add_argument("ticker", help="Ticker symbol (e.g., AAPL, VOD.LSE)")
    parser.add_argument("--exchange", "-e", help="Exchange code (e.g., US, LSE, JSE)")
    parser.add_argument("--add-to-universe", "-a", action="store_true", help="Add to universe")
    parser.add_argument("--force", "-f", action="store_true", help="Force refresh")

    args = parser.parse_args()

    service = AdHocScoringService()
    result = service.score_ticker(
        args.ticker,
        exchange=args.exchange,
        add_to_universe=args.add_to_universe,
        force_refresh=args.force,
    )

    if result.success:
        print(f"\n{'='*60}")
        print(f"  {result.symbol} ({result.asset_type}) - {result.exchange}")
        print(f"{'='*60}")
        print(f"  Score Total:    {result.score_total or 'N/A'}")
        print(f"  Score Value:    {result.score_value or 'N/A'}")
        print(f"  Score Momentum: {result.score_momentum or 'N/A'}")
        print(f"  Score Safety:   {result.score_safety or 'N/A'}")
        print(f"  Confidence:     {result.confidence or 'N/A'}%")
        print(f"{'='*60}")
        print(f"  RSI:            {result.rsi:.1f}" if result.rsi else "  RSI:            N/A")
        print(f"  Z-Score:        {result.zscore:.2f}" if result.zscore else "  Z-Score:        N/A")
        print(f"  Volatility:     {result.vol_annual:.1f}%" if result.vol_annual else "  Volatility:     N/A")
        print(f"  Max Drawdown:   {result.max_drawdown:.1f}%" if result.max_drawdown else "  Max Drawdown:   N/A")
        print(f"  Last Price:     ${result.last_price:.2f}" if result.last_price else "  Last Price:     N/A")
        print(f"  State:          {result.state_label}")
        print(f"{'='*60}")
        print(f"  Data Points:    {result.data_points}")
        print(f"  Data Source:    {result.data_source}")
        print(f"  In Universe:    {'Yes' if result.was_in_universe else 'No'}")
        if result.added_to_universe:
            print(f"  Added:          Yes (tier 3)")
        print(f"{'='*60}\n")
    else:
        print(f"\nError scoring {result.symbol}: {result.error}\n")
