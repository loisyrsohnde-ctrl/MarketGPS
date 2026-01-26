"""
Tests for Ad-Hoc Scoring Service
================================
Tests the ability to score arbitrary tickers on-the-fly.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adhoc_scoring import (
    AdHocScoringService,
    AdHocScoringResult,
    score_any_ticker,
    EXCHANGE_SUFFIXES,
    EXCHANGE_TO_SCOPE,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_store():
    """Create a mock SQLite store."""
    store = Mock()
    store._get_connection = Mock()

    # Mock get_asset to return None (asset not in universe)
    store.get_asset = Mock(return_value=None)

    # Mock upsert_score
    store.upsert_score = Mock()

    return store


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
    np.random.seed(42)

    # Generate realistic price data
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, 252)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 252)),
        'High': prices * (1 + np.random.uniform(0, 0.02, 252)),
        'Low': prices * (1 - np.random.uniform(0, 0.02, 252)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 252),
    }, index=dates)

    return df


@pytest.fixture
def sample_fundamentals():
    """Create sample fundamentals data."""
    return {
        "name": "Test Company Inc.",
        "sector": "Technology",
        "industry": "Software",
        "pe_ratio": 25.5,
        "profit_margin": 0.18,
        "return_on_equity": 0.22,
        "market_cap": 500000000000,
    }


@pytest.fixture
def service(mock_store):
    """Create AdHocScoringService with mocked store."""
    return AdHocScoringService(store=mock_store)


# ═══════════════════════════════════════════════════════════════════════════════
# Ticker Resolution Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTickerResolution:
    """Test ticker resolution logic."""

    def test_resolve_simple_us_ticker(self, service):
        """Test resolving a simple US ticker."""
        resolved = service._resolve_ticker("AAPL")

        assert resolved["asset_id"] == "AAPL.US"
        assert resolved["symbol"] == "AAPL"
        assert resolved["exchange"] == "US"
        assert resolved["asset_type"] == "EQUITY"
        assert resolved["market_scope"] == "US_EU"

    def test_resolve_ticker_with_exchange_suffix(self, service):
        """Test resolving ticker that already has exchange suffix."""
        resolved = service._resolve_ticker("VOD.LSE")

        assert resolved["asset_id"] == "VOD.LSE"
        assert resolved["symbol"] == "VOD"
        assert resolved["exchange"] == "LSE"
        assert resolved["market_scope"] == "US_EU"

    def test_resolve_ticker_with_explicit_exchange(self, service):
        """Test resolving ticker with explicit exchange parameter."""
        resolved = service._resolve_ticker("NPN", exchange="JSE")

        assert resolved["asset_id"] == "NPN.JSE"
        assert resolved["symbol"] == "NPN"
        assert resolved["exchange"] == "JSE"
        assert resolved["market_scope"] == "AFRICA"

    def test_resolve_african_exchange(self, service):
        """Test resolving African exchange tickers."""
        # South Africa
        resolved = service._resolve_ticker("SOL.JSE")
        assert resolved["market_scope"] == "AFRICA"

        # Nigeria
        resolved = service._resolve_ticker("DANGCEM", exchange="NG")
        assert resolved["asset_id"] == "DANGCEM.NG"
        assert resolved["market_scope"] == "AFRICA"

    def test_resolve_european_exchanges(self, service):
        """Test resolving European exchange tickers."""
        # Paris
        resolved = service._resolve_ticker("TTE.PA")
        assert resolved["market_scope"] == "US_EU"
        assert resolved["exchange"] == "PA"

        # Frankfurt/Xetra
        resolved = service._resolve_ticker("SAP", exchange="XETRA")
        assert resolved["asset_id"] == "SAP.XETRA"
        assert resolved["market_scope"] == "US_EU"

    def test_resolve_crypto_ticker(self, service):
        """Test resolving crypto tickers."""
        resolved = service._resolve_ticker("BTC-USD")

        assert resolved["asset_type"] == "CRYPTO"
        # Crypto keeps original format
        assert "BTC" in resolved["symbol"]

    def test_resolve_case_insensitive(self, service):
        """Test that resolution is case-insensitive."""
        resolved = service._resolve_ticker("aapl")

        assert resolved["asset_id"] == "AAPL.US"
        assert resolved["symbol"] == "AAPL"

    def test_resolve_with_whitespace(self, service):
        """Test that resolution strips whitespace."""
        resolved = service._resolve_ticker("  AAPL  ")

        assert resolved["asset_id"] == "AAPL.US"


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdHocScoring:
    """Test the scoring functionality."""

    def test_score_ticker_success(self, service, sample_ohlcv_df, sample_fundamentals):
        """Test successful scoring of a ticker."""
        from core.models import Score, StateLabel

        with patch.object(service, '_get_cached_score', return_value=None):
            with patch.object(service, '_fetch_price_data', return_value=(sample_ohlcv_df, "EODHD")):
                with patch.object(service, '_fetch_fundamentals', return_value=sample_fundamentals):
                    # Create mock score
                    mock_score = Score(
                        asset_id="AAPL.US",
                        score_total=75.0,
                        score_momentum=80.0,
                        score_safety=70.0,
                        score_value=72.5,
                        confidence=85,
                        rsi=55.0,
                        zscore=0.5,
                        vol_annual=25.0,
                        max_drawdown=15.0,
                        sma200=150.0,
                        last_price=185.0,
                        state_label=StateLabel.EQUILIBRE,
                    )
                    mock_engine = Mock()
                    mock_engine.compute_score.return_value = mock_score

                    with patch.dict('sys.modules', {'pipeline.scoring': Mock(ScoringEngine=Mock(return_value=mock_engine))}):
                        service._store.upsert_score = Mock()
                        result = service.score_ticker("AAPL")

        assert result.success is True
        assert result.asset_id == "AAPL.US"
        assert result.symbol == "AAPL"
        assert result.asset_type == "EQUITY"
        assert result.data_source == "EODHD"
        assert result.data_points == 252

        # Score should be calculated
        assert result.score_total == 75.0
        assert result.score_momentum == 80.0
        assert result.score_safety == 70.0
        assert result.confidence == 85

        # Technical metrics
        assert result.rsi == 55.0
        assert result.vol_annual == 25.0

    @patch('adhoc_scoring.AdHocScoringService._fetch_price_data')
    def test_score_ticker_insufficient_data(self, mock_price_data, service):
        """Test scoring fails with insufficient data."""
        # Return only 30 bars (minimum is 50)
        mock_price_data.return_value = (pd.DataFrame({'Close': [100]*30}), "EODHD")

        result = service.score_ticker("XYZ")

        assert result.success is False
        assert "Insufficient data" in result.error
        assert result.data_points == 30

    @patch('adhoc_scoring.AdHocScoringService._fetch_price_data')
    def test_score_ticker_no_data(self, mock_price_data, service):
        """Test scoring fails with no data."""
        mock_price_data.return_value = (pd.DataFrame(), "none")

        result = service.score_ticker("INVALID")

        assert result.success is False
        assert "Insufficient data" in result.error

    @patch('adhoc_scoring.AdHocScoringService._fetch_price_data')
    @patch('adhoc_scoring.AdHocScoringService._fetch_fundamentals')
    def test_score_ticker_force_refresh(
        self, mock_fundamentals, mock_price_data, service, sample_ohlcv_df
    ):
        """Test force_refresh bypasses cache."""
        mock_price_data.return_value = (sample_ohlcv_df, "EODHD")
        mock_fundamentals.return_value = None

        # Mock cache to return a cached score
        with patch.object(service, '_get_cached_score') as mock_cache:
            mock_cache.return_value = {"score_total": 75.0, "symbol": "AAPL"}

            # Without force_refresh - should use cache
            result = service.score_ticker("AAPL", force_refresh=False)
            # Cache is checked
            mock_cache.assert_called()

            # With force_refresh - should skip cache
            mock_cache.reset_mock()
            result = service.score_ticker("AAPL", force_refresh=True)
            # Cache is not checked
            mock_cache.assert_not_called()

    def test_score_etf_no_value_pillar(self, service, sample_ohlcv_df):
        """Test that ETF scoring doesn't include value pillar."""
        from core.models import Score, StateLabel

        with patch.object(service, '_get_cached_score', return_value=None):
            with patch.object(service, '_fetch_price_data', return_value=(sample_ohlcv_df, "EODHD")):
                with patch.object(service, '_fetch_fundamentals', return_value=None):
                    # Create mock score with no value
                    mock_score = Score(
                        asset_id="SPY.US",
                        score_total=70.0,
                        score_momentum=75.0,
                        score_safety=65.0,
                        score_value=None,  # No value for ETF
                        confidence=80,
                        rsi=50.0,
                        zscore=0.2,
                        vol_annual=20.0,
                        max_drawdown=12.0,
                        sma200=400.0,
                        last_price=450.0,
                        state_label=StateLabel.EQUILIBRE,
                    )
                    mock_engine = Mock()
                    mock_engine.compute_score.return_value = mock_score

                    with patch.dict('sys.modules', {'pipeline.scoring': Mock(ScoringEngine=Mock(return_value=mock_engine))}):
                        service._store.upsert_score = Mock()
                        result = service.score_ticker("SPY", asset_type="ETF")

        assert result.success is True
        assert result.asset_type == "ETF"
        # Value score is None for ETF
        assert result.score_value is None
        assert result.score_total == 70.0
        assert result.score_momentum == 75.0
        assert result.score_safety == 65.0


# ═══════════════════════════════════════════════════════════════════════════════
# Batch Scoring Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchScoring:
    """Test batch scoring functionality."""

    @patch('adhoc_scoring.AdHocScoringService.score_ticker')
    def test_score_batch(self, mock_score, service):
        """Test batch scoring multiple tickers."""
        # Mock successful scoring
        mock_score.return_value = AdHocScoringResult(
            success=True,
            asset_id="TEST.US",
            symbol="TEST",
            name="Test",
            asset_type="EQUITY",
            market_scope="US_EU",
            exchange="US",
            score_total=75.0,
        )

        results = service.score_batch(["AAPL", "MSFT", "GOOGL"])

        assert len(results) == 3
        assert all(r.success for r in results)
        assert mock_score.call_count == 3

    @patch('adhoc_scoring.AdHocScoringService.score_ticker')
    def test_score_batch_partial_failure(self, mock_score, service):
        """Test batch scoring with some failures."""
        def side_effect(ticker, **kwargs):
            if ticker == "INVALID":
                return AdHocScoringResult(
                    success=False,
                    asset_id=ticker,
                    symbol=ticker,
                    name=None,
                    asset_type="UNKNOWN",
                    market_scope="UNKNOWN",
                    exchange="UNKNOWN",
                    error="Not found",
                )
            return AdHocScoringResult(
                success=True,
                asset_id=f"{ticker}.US",
                symbol=ticker,
                name=ticker,
                asset_type="EQUITY",
                market_scope="US_EU",
                exchange="US",
                score_total=75.0,
            )

        mock_score.side_effect = side_effect

        results = service.score_batch(["AAPL", "INVALID", "GOOGL"])

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True


# ═══════════════════════════════════════════════════════════════════════════════
# Result Serialization Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestResultSerialization:
    """Test AdHocScoringResult serialization."""

    def test_to_dict(self):
        """Test result serialization to dict."""
        result = AdHocScoringResult(
            success=True,
            asset_id="AAPL.US",
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="EQUITY",
            market_scope="US_EU",
            exchange="US",
            score_total=75.5,
            score_momentum=80.0,
            score_safety=70.0,
            score_value=72.5,
            confidence=85,
            rsi=55.3,
            zscore=0.5,
            vol_annual=25.0,
            max_drawdown=15.0,
            last_price=185.50,
            state_label="Équilibre",
            data_points=252,
            data_source="EODHD",
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["asset_id"] == "AAPL.US"
        assert d["score_total"] == 75.5
        assert d["rsi"] == 55.3
        assert d["data_points"] == 252

    def test_to_dict_with_none_values(self):
        """Test serialization handles None values."""
        result = AdHocScoringResult(
            success=False,
            asset_id="INVALID",
            symbol="INVALID",
            name=None,
            asset_type="UNKNOWN",
            market_scope="UNKNOWN",
            exchange="UNKNOWN",
            error="Not found",
        )

        d = result.to_dict()

        assert d["success"] is False
        assert d["score_total"] is None
        assert d["error"] == "Not found"


# ═══════════════════════════════════════════════════════════════════════════════
# yfinance Ticker Conversion Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestYfinanceConversion:
    """Test conversion to yfinance ticker format."""

    def test_us_ticker(self, service):
        """Test US ticker conversion (no suffix needed)."""
        yf = service._convert_to_yfinance_ticker("AAPL.US")
        assert yf == "AAPL"

    def test_london_ticker(self, service):
        """Test London ticker conversion."""
        yf = service._convert_to_yfinance_ticker("VOD.LSE")
        assert yf == "VOD.L"

    def test_paris_ticker(self, service):
        """Test Paris ticker conversion."""
        yf = service._convert_to_yfinance_ticker("TTE.PA")
        assert yf == "TTE.PA"

    def test_frankfurt_ticker(self, service):
        """Test Frankfurt/Xetra ticker conversion."""
        yf = service._convert_to_yfinance_ticker("SAP.XETRA")
        assert yf == "SAP.DE"

    def test_johannesburg_ticker(self, service):
        """Test JSE ticker conversion."""
        yf = service._convert_to_yfinance_ticker("NPN.JSE")
        assert yf == "NPN.JO"


# ═══════════════════════════════════════════════════════════════════════════════
# Exchange Constants Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestExchangeConstants:
    """Test exchange mappings and constants."""

    def test_exchange_suffixes_completeness(self):
        """Test all major exchanges have suffixes."""
        major_exchanges = ["US", "NYSE", "NASDAQ", "PA", "XETRA", "LSE", "JSE", "NG"]
        for ex in major_exchanges:
            assert ex in EXCHANGE_SUFFIXES, f"Missing suffix for {ex}"

    def test_exchange_to_scope_africa(self):
        """Test African exchanges map to AFRICA scope."""
        african_suffixes = [".JSE", ".NG", ".CA", ".BRVM"]
        for suffix in african_suffixes:
            assert EXCHANGE_TO_SCOPE.get(suffix) == "AFRICA", f"{suffix} should map to AFRICA"

    def test_exchange_to_scope_us_eu(self):
        """Test US/EU exchanges map to US_EU scope."""
        us_eu_suffixes = [".US", ".PA", ".XETRA", ".LSE", ".AS"]
        for suffix in us_eu_suffixes:
            assert EXCHANGE_TO_SCOPE.get(suffix) == "US_EU", f"{suffix} should map to US_EU"


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience Function Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch('adhoc_scoring.AdHocScoringService')
    def test_score_any_ticker(self, mock_service_class):
        """Test score_any_ticker convenience function."""
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        mock_result = AdHocScoringResult(
            success=True,
            asset_id="AAPL.US",
            symbol="AAPL",
            name="Apple",
            asset_type="EQUITY",
            market_scope="US_EU",
            exchange="US",
            score_total=75.0,
        )
        mock_instance.score_ticker.return_value = mock_result

        result = score_any_ticker("AAPL")

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["score_total"] == 75.0


# ═══════════════════════════════════════════════════════════════════════════════
# Integration-Like Tests (with mocked providers)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration-like tests with mocked external dependencies."""

    def test_yfinance_ticker_conversion_integration(self, service):
        """Test yfinance ticker conversion works for common exchanges."""
        # US stocks
        assert service._convert_to_yfinance_ticker("AAPL.US") == "AAPL"
        assert service._convert_to_yfinance_ticker("MSFT.US") == "MSFT"

        # European stocks
        assert service._convert_to_yfinance_ticker("VOD.LSE") == "VOD.L"
        assert service._convert_to_yfinance_ticker("SAP.XETRA") == "SAP.DE"
        assert service._convert_to_yfinance_ticker("TTE.PA") == "TTE.PA"

        # African stocks
        assert service._convert_to_yfinance_ticker("NPN.JSE") == "NPN.JO"

    def test_fundamentals_optional(self, service, sample_ohlcv_df):
        """Test scoring works without fundamentals."""
        from core.models import Score, StateLabel

        with patch.object(service, '_get_cached_score', return_value=None):
            with patch.object(service, '_fetch_price_data', return_value=(sample_ohlcv_df, "EODHD")):
                with patch.object(service, '_fetch_fundamentals', return_value=None):
                    # Mock the scoring engine
                    mock_score = Score(
                        asset_id="AAPL.US",
                        score_total=70.0,
                        score_momentum=75.0,
                        score_safety=65.0,
                        score_value=None,
                        confidence=75,
                        rsi=50.0,
                        zscore=0.2,
                        vol_annual=22.0,
                        max_drawdown=14.0,
                        state_label=StateLabel.EQUILIBRE,
                    )
                    mock_engine = Mock()
                    mock_engine.compute_score.return_value = mock_score

                    with patch.dict('sys.modules', {'pipeline.scoring': Mock(ScoringEngine=Mock(return_value=mock_engine))}):
                        service._store.upsert_score = Mock()
                        result = service.score_ticker("AAPL")

                        # Should still succeed, just without value pillar
                        assert result.success is True
                        assert result.score_total == 70.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
