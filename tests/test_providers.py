"""Tests for data providers."""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from providers.base import BaseProvider, Fundamentals, AssetMetadata
from providers.yahoo_yfinance import YFinanceProvider


class TestYFinanceProvider:
    """Tests for YFinance provider."""
    
    def test_provider_initialization(self):
        """Test provider initializes correctly."""
        provider = YFinanceProvider()
        assert provider.name == "yfinance"
    
    def test_healthcheck(self):
        """Test healthcheck returns valid result."""
        provider = YFinanceProvider()
        result = provider.healthcheck()
        
        assert result.status in ["healthy", "degraded", "unhealthy"]
        assert isinstance(result.latency_ms, int)
        assert result.timestamp is not None
    
    def test_normalize_dataframe_empty(self):
        """Test normalizing empty DataFrame."""
        provider = YFinanceProvider()
        result = provider.normalize_dataframe(pd.DataFrame())
        
        assert result.empty
    
    def test_normalize_dataframe_standard(self):
        """Test normalizing standard DataFrame."""
        provider = YFinanceProvider()
        
        df = pd.DataFrame({
            "Open": [100, 101],
            "High": [102, 103],
            "Low": [99, 100],
            "Close": [101, 102],
            "Volume": [1000, 1100],
        }, index=pd.to_datetime(["2024-01-01", "2024-01-02"]))
        
        result = provider.normalize_dataframe(df)
        
        assert not result.empty
        assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.tz is None  # Timezone-naive
    
    def test_normalize_dataframe_timezone(self):
        """Test timezone is removed."""
        provider = YFinanceProvider()
        
        df = pd.DataFrame({
            "Open": [100],
            "High": [102],
            "Low": [99],
            "Close": [101],
            "Volume": [1000],
        }, index=pd.to_datetime(["2024-01-01"]).tz_localize("UTC"))
        
        result = provider.normalize_dataframe(df)
        
        assert result.index.tz is None
    
    def test_normalize_dataframe_multiindex(self):
        """Test MultiIndex columns are handled."""
        provider = YFinanceProvider()
        
        # Single ticker in MultiIndex
        arrays = [["Open", "High", "Low", "Close", "Volume"], ["AAPL"] * 5]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples)
        
        df = pd.DataFrame(
            [[100, 102, 99, 101, 1000]],
            columns=index,
            index=pd.to_datetime(["2024-01-01"])
        )
        
        result = provider.normalize_dataframe(df)
        
        # Should flatten for single ticker
        assert not result.empty
    
    def test_infer_asset_type(self):
        """Test asset type inference."""
        provider = YFinanceProvider()
        
        assert provider.infer_asset_type({"quoteType": "EQUITY"}) == "EQUITY"
        assert provider.infer_asset_type({"quoteType": "ETF"}) == "ETF"
        assert provider.infer_asset_type({"quoteType": "CRYPTOCURRENCY"}) == "CRYPTO"
        assert provider.infer_asset_type({"quoteType": "UNKNOWN"}) == "UNKNOWN"
        assert provider.infer_asset_type({}) == "UNKNOWN"


class TestFundamentals:
    """Tests for Fundamentals dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        fund = Fundamentals(pe_ratio=15.5, profit_margin=0.20)
        d = fund.to_dict()
        
        assert d["pe_ratio"] == 15.5
        assert d["profit_margin"] == 0.20
    
    def test_is_complete(self):
        """Test completeness check."""
        fund_complete = Fundamentals(pe_ratio=15.5, profit_margin=0.20)
        fund_incomplete = Fundamentals()
        
        assert fund_complete.is_complete()
        assert not fund_incomplete.is_complete()


class TestAssetMetadata:
    """Tests for AssetMetadata dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        meta = AssetMetadata(
            symbol="AAPL",
            name="Apple Inc",
            asset_type="EQUITY",
            exchange="NASDAQ",
            currency="USD"
        )
        d = meta.to_dict()
        
        assert d["symbol"] == "AAPL"
        assert d["name"] == "Apple Inc"
        assert d["asset_type"] == "EQUITY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
