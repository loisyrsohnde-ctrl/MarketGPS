"""
MarketGPS Feature Computer.
Technical indicators and derived features.
"""
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd
import numpy as np

from core.utils import get_logger, safe_float

logger = get_logger(__name__)


@dataclass
class Features:
    """Computed features for an asset."""
    # Price info
    last_price: Optional[float] = None
    last_date: Optional[str] = None
    
    # Moving averages
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    
    # Momentum
    rsi: Optional[float] = None
    momentum_3m: Optional[float] = None  # 3-month return %
    momentum_12m: Optional[float] = None  # 12-month return %
    price_vs_sma200_pct: Optional[float] = None
    
    # Volatility / Risk
    volatility_daily: Optional[float] = None
    volatility_annual: Optional[float] = None
    max_drawdown: Optional[float] = None
    downside_deviation: Optional[float] = None
    
    # Z-score
    zscore: Optional[float] = None
    
    # Data quality
    data_points: int = 0
    coverage: float = 0.0
    stale_ratio: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "last_price": self.last_price,
            "last_date": self.last_date,
            "sma20": self.sma20,
            "sma50": self.sma50,
            "sma200": self.sma200,
            "rsi": self.rsi,
            "momentum_3m": self.momentum_3m,
            "momentum_12m": self.momentum_12m,
            "price_vs_sma200_pct": self.price_vs_sma200_pct,
            "volatility_daily": self.volatility_daily,
            "volatility_annual": self.volatility_annual,
            "max_drawdown": self.max_drawdown,
            "downside_deviation": self.downside_deviation,
            "zscore": self.zscore,
            "data_points": self.data_points,
            "coverage": self.coverage,
            "stale_ratio": self.stale_ratio,
        }


class FeatureComputer:
    """
    Computes technical features from OHLCV data.
    
    All methods are NaN-safe and handle edge cases gracefully.
    """
    
    def __init__(self, expected_days: int = 252):
        """
        Initialize feature computer.
        
        Args:
            expected_days: Expected trading days for coverage calculation
        """
        self.expected_days = expected_days
    
    def compute_all(self, df: pd.DataFrame) -> Features:
        """
        Compute all features from OHLCV DataFrame.
        
        Args:
            df: OHLCV DataFrame with columns [Open, High, Low, Close, Volume]
            
        Returns:
            Features object with all computed values
        """
        if df is None or df.empty or "Close" not in df.columns:
            return Features()
        
        features = Features()
        close = df["Close"]
        
        # Data quality
        features.data_points = len(df)
        features.coverage = min(1.0, len(df) / self.expected_days)
        features.stale_ratio = self._compute_stale_ratio(close)
        
        # Price info
        features.last_price = safe_float(close.iloc[-1])
        features.last_date = str(df.index[-1].date()) if len(df) > 0 else None
        
        # Moving averages
        features.sma20 = self._sma(close, 20)
        features.sma50 = self._sma(close, 50)
        features.sma200 = self._sma(close, 200)
        
        # Price vs SMA200
        if features.sma200 and features.last_price and features.sma200 > 0:
            features.price_vs_sma200_pct = (
                (features.last_price - features.sma200) / features.sma200 * 100
            )
        
        # RSI
        features.rsi = self._rsi(close, 14)
        
        # Momentum
        features.momentum_3m = self._momentum(close, 63)
        features.momentum_12m = self._momentum(close, 252)
        
        # Volatility
        returns = close.pct_change().dropna()
        features.volatility_daily = self._std(returns)
        if features.volatility_daily:
            features.volatility_annual = features.volatility_daily * np.sqrt(252) * 100
        
        # Max Drawdown
        features.max_drawdown = self._max_drawdown(close)
        
        # Downside deviation
        features.downside_deviation = self._downside_deviation(returns)
        
        # Z-score
        features.zscore = self._zscore(close, 20)
        
        return features
    
    def _sma(self, series: pd.Series, window: int) -> Optional[float]:
        """Simple Moving Average."""
        if len(series) < window:
            return None
        return safe_float(series.rolling(window).mean().iloc[-1])
    
    def _std(self, series: pd.Series, window: int = None) -> Optional[float]:
        """Standard deviation."""
        if len(series) < 2:
            return None
        if window:
            if len(series) < window:
                return None
            return safe_float(series.rolling(window).std().iloc[-1])
        return safe_float(series.std())
    
    def _rsi(self, series: pd.Series, window: int = 14) -> Optional[float]:
        """
        Relative Strength Index.
        
        RSI = 100 - (100 / (1 + RS))
        RS = Avg Gain / Avg Loss
        """
        if len(series) < window + 1:
            return None
        
        try:
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = (-delta.where(delta < 0, 0))
            
            avg_gain = gain.rolling(window).mean()
            avg_loss = loss.rolling(window).mean()
            
            # Avoid division by zero
            avg_loss = avg_loss.replace(0, np.nan)
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return safe_float(rsi.iloc[-1])
        except Exception:
            return None
    
    def _momentum(self, series: pd.Series, days: int) -> Optional[float]:
        """
        Price momentum (return) over N days.
        
        Returns percentage change.
        """
        if len(series) < days + 1:
            return None
        
        try:
            current = series.iloc[-1]
            past = series.iloc[-days - 1]
            
            if past == 0 or pd.isna(past) or pd.isna(current):
                return None
            
            return ((current / past) - 1) * 100
        except Exception:
            return None
    
    def _max_drawdown(self, series: pd.Series, window: int = 252) -> Optional[float]:
        """
        Maximum drawdown over window.
        
        Returns negative percentage (e.g., -15.5 for 15.5% drawdown).
        """
        if len(series) < 2:
            return None
        
        try:
            # Use full series or window
            if len(series) > window:
                series = series.iloc[-window:]
            
            rolling_max = series.cummax()
            drawdown = (series - rolling_max) / rolling_max
            max_dd = drawdown.min()
            
            return safe_float(max_dd * 100)
        except Exception:
            return None
    
    def _downside_deviation(self, returns: pd.Series, threshold: float = 0) -> Optional[float]:
        """
        Downside deviation (semi-deviation below threshold).
        
        Returns annualized value.
        """
        if len(returns) < 20:
            return None
        
        try:
            downside = returns[returns < threshold]
            if len(downside) < 5:
                return None
            
            dd = downside.std() * np.sqrt(252) * 100
            return safe_float(dd)
        except Exception:
            return None
    
    def _zscore(self, series: pd.Series, window: int = 20) -> Optional[float]:
        """
        Z-score: (Price - SMA) / STD.
        
        Measures how many standard deviations from mean.
        """
        if len(series) < window:
            return None
        
        try:
            sma = series.rolling(window).mean()
            std = series.rolling(window).std()
            
            current_std = std.iloc[-1]
            if current_std == 0 or pd.isna(current_std):
                return None
            
            zscore = (series.iloc[-1] - sma.iloc[-1]) / current_std
            return safe_float(zscore)
        except Exception:
            return None
    
    def _compute_stale_ratio(self, series: pd.Series) -> float:
        """
        Compute ratio of consecutive identical closes (stale data).
        """
        if len(series) < 2:
            return 0.0
        
        try:
            # Count where close equals previous close
            stale_count = (series == series.shift(1)).sum()
            return stale_count / len(series)
        except Exception:
            return 0.0
    
    def compute_adv(self, df: pd.DataFrame, window: int = 20) -> Optional[float]:
        """
        Compute Average Dollar Volume.
        
        ADV = mean(Close * Volume) over window.
        """
        if df is None or df.empty:
            return None
        
        if "Close" not in df.columns or "Volume" not in df.columns:
            return None
        
        try:
            dollar_volume = df["Close"] * df["Volume"]
            if len(dollar_volume) < window:
                return safe_float(dollar_volume.mean())
            return safe_float(dollar_volume.tail(window).mean())
        except Exception:
            return None
    
    def get_state_label(self, zscore: Optional[float]) -> str:
        """
        Get state label based on z-score.
        
        Returns neutral vocabulary labels.
        """
        if zscore is None:
            return "N/A"
        
        if zscore > 2:
            return "Extension haute (+2σ)"
        elif zscore < -2:
            return "Extension basse (-2σ)"
        else:
            return "Équilibre"
