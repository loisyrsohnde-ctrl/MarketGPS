"""
MarketGPS v8.0 - Data Models
Dataclasses for all domain entities with multi-instrument support.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class AssetType(Enum):
    """Asset type enumeration - all supported instrument classes."""
    EQUITY = "EQUITY"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    FX = "FX"           # Forex / Currency pairs
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    BOND = "BOND"
    INDEX = "INDEX"
    FUND = "FUND"
    COMMODITY = "COMMODITY"  # Commodities (Gold, Oil, etc.)
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_string(cls, value: str) -> "AssetType":
        """Convert string to AssetType, with fallback to UNKNOWN."""
        try:
            return cls(value.upper())
        except (ValueError, AttributeError):
            return cls.UNKNOWN
    
    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        names = {
            "EQUITY": "Actions",
            "ETF": "ETF",
            "CRYPTO": "Crypto",
            "FX": "Forex",
            "FUTURE": "Futures",
            "OPTION": "Options",
            "BOND": "Obligations",
            "INDEX": "Indices",
            "FUND": "Fonds",
            "COMMODITY": "Matières 1ères",
            "UNKNOWN": "Autre"
        }
        return names.get(self.value, self.value)
    
    @property
    def has_value_pillar(self) -> bool:
        """Whether this asset type supports Value pillar scoring."""
        return self.value in ("EQUITY", "FUND")
    
    @property
    def has_fundamentals(self) -> bool:
        """Whether this asset type typically has fundamental data."""
        return self.value in ("EQUITY", "ETF", "FUND")


class StateLabel(Enum):
    """Score state labels (neutral language)."""
    EQUILIBRE = "Équilibre"
    EQUILIBRIUM = "Équilibre"  # Alias for compatibility
    EXTENSION_HAUTE = "Extension haute (+2σ)"
    EXTENSION_HIGH = "Extension haute (+2σ)"  # Alias
    EXTENSION_BASSE = "Extension basse (-2σ)"
    EXTENSION_LOW = "Extension basse (-2σ)"  # Alias
    STRESS_HAUSSIER = "Stress haussier"
    STRESS_BAISSIER = "Stress baissier"
    NA = "N/A"


class Tier(Enum):
    """Universe tier for refresh priority."""
    INSTITUTIONAL = 1  # Top priority, frequent refresh
    EXTENDED = 2       # Normal priority, daily refresh
    ON_DEMAND = 3      # Low priority, on-demand only


class QueueStatus(Enum):
    """Priority queue item status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProTier(Enum):
    """User subscription tier."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Asset:
    """Represents an asset in the universe."""
    asset_id: str
    symbol: str
    name: Optional[str] = None
    asset_type: AssetType = AssetType.EQUITY
    market_scope: str = "US_EU"      # Market scope: US_EU or AFRICA
    market_code: str = "US"          # Market identifier: US, EU, NG, BRVM, BVMAC
    exchange_code: str = "US"        # Exchange MIC code
    exchange: str = "US"             # Legacy: keep for compatibility
    currency: str = "USD"
    country: str = "US"
    sector: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None       # ISIN code for international assets
    active: bool = True
    tier: int = 2
    priority_level: int = 2          # Priority: 1=high, 2=normal, 3=low
    data_source: str = "EODHD"       # Data provider
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row: dict) -> "Asset":
        """Create Asset from database row."""
        return cls(
            asset_id=row["asset_id"],
            symbol=row.get("symbol", row["asset_id"].split(".")[0]),
            name=row.get("name"),
            asset_type=AssetType.from_string(row.get("asset_type", "EQUITY")),
            market_scope=row.get("market_scope", "US_EU"),
            market_code=row.get("market_code", "US"),
            exchange_code=row.get("exchange_code", "US"),
            exchange=row.get("exchange", "US"),
            currency=row.get("currency", "USD"),
            country=row.get("country", "US"),
            sector=row.get("sector"),
            industry=row.get("industry"),
            active=bool(row.get("active", 1)),
            tier=row.get("tier", 2),
            priority_level=row.get("priority_level", 2),
        )


@dataclass
class GatingStatus:
    """Data quality and eligibility status for an asset."""
    asset_id: str
    coverage: float = 0.0
    liquidity: float = 0.0
    price_min: Optional[float] = None
    stale_ratio: float = 0.0
    eligible: bool = False
    reason: Optional[str] = None
    data_confidence: int = 50
    last_bar_date: Optional[str] = None
    fx_risk: float = 0.0  # AFRICA: FX risk score (0-100)
    liquidity_risk: float = 0.0  # AFRICA: Liquidity risk score (0-100)
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row: dict) -> "GatingStatus":
        """Create GatingStatus from database row."""
        return cls(
            asset_id=row["asset_id"],
            coverage=row.get("coverage", 0.0) or 0.0,
            liquidity=row.get("liquidity", 0.0) or 0.0,
            price_min=row.get("price_min"),
            stale_ratio=row.get("stale_ratio", 0.0) or 0.0,
            eligible=bool(row.get("eligible", 0)),
            reason=row.get("reason"),
            data_confidence=row.get("data_confidence", 50) or 50,
            last_bar_date=row.get("last_bar_date"),
            fx_risk=row.get("fx_risk", 0.0) or 0.0,
            liquidity_risk=row.get("liquidity_risk", 0.0) or 0.0,
        )


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of score calculation."""
    version: str = "1.0"
    scoring_date: Optional[str] = None
    weights: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)  # Raw calculated features
    normalized: Dict[str, float] = field(default_factory=dict)  # Normalized pillar scores
    raw_values: Dict[str, Any] = field(default_factory=dict)  # Alias for features
    normalized_values: Dict[str, float] = field(default_factory=dict)  # Alias for normalized
    confidence_components: Dict[str, float] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "version": self.version,
            "scoring_date": self.scoring_date,
            "weights": self.weights,
            "features": self.features or self.raw_values,
            "normalized": self.normalized or self.normalized_values,
            "confidence_components": self.confidence_components
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "ScoreBreakdown":
        """Deserialize from JSON string."""
        if not json_str:
            return cls()
        try:
            data = json.loads(json_str)
            return cls(
                version=data.get("version", "1.0"),
                scoring_date=data.get("scoring_date"),
                weights=data.get("weights", {}),
                features=data.get("features", data.get("raw_values", {})),
                normalized=data.get("normalized", data.get("normalized_values", {})),
                raw_values=data.get("raw_values", data.get("features", {})),
                normalized_values=data.get("normalized_values", data.get("normalized", {})),
                confidence_components=data.get("confidence_components", {})
            )
        except (json.JSONDecodeError, TypeError):
            return cls()


@dataclass
class Score:
    """Score data for an asset (supports US_EU and AFRICA scopes)."""
    asset_id: str
    score_total: Optional[float] = None
    score_value: Optional[float] = None
    score_momentum: Optional[float] = None
    score_safety: Optional[float] = None
    score_fx_risk: Optional[float] = None          # Africa-specific: FX risk score
    score_liquidity_risk: Optional[float] = None   # Africa-specific: Liquidity risk score
    confidence: int = 50
    state_label: StateLabel = StateLabel.NA
    rsi: Optional[float] = None
    zscore: Optional[float] = None
    vol_annual: Optional[float] = None
    max_drawdown: Optional[float] = None
    sma200: Optional[float] = None
    last_price: Optional[float] = None
    fundamentals_available: bool = False
    breakdown: Optional[ScoreBreakdown] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_calculated(self) -> bool:
        """Whether score has been calculated."""
        return self.score_total is not None
    
    @classmethod
    def from_row(cls, row: dict) -> "Score":
        """Create Score from database row."""
        state_str = row.get("state_label", "N/A")
        try:
            state = StateLabel(state_str)
        except ValueError:
            state = StateLabel.NA
        
        breakdown = None
        if row.get("json_breakdown"):
            breakdown = ScoreBreakdown.from_json(row["json_breakdown"])
        
        return cls(
            asset_id=row["asset_id"],
            score_total=row.get("score_total"),
            score_value=row.get("score_value"),
            score_momentum=row.get("score_momentum"),
            score_safety=row.get("score_safety"),
            score_fx_risk=row.get("score_fx_risk"),
            score_liquidity_risk=row.get("score_liquidity_risk"),
            confidence=row.get("confidence", 50) or 50,
            state_label=state,
            rsi=row.get("rsi"),
            zscore=row.get("zscore"),
            vol_annual=row.get("vol_annual"),
            max_drawdown=row.get("max_drawdown"),
            sma200=row.get("sma200"),
            last_price=row.get("last_price"),
            fundamentals_available=bool(row.get("fundamentals_available", 0)),
            breakdown=breakdown,
        )


@dataclass
class RotationState:
    """Rotation/refresh state for an asset."""
    asset_id: str
    last_refresh_at: Optional[datetime] = None
    priority_level: int = 2
    in_top50: bool = False
    cooldown_until: Optional[datetime] = None
    last_error: Optional[str] = None
    refresh_count: int = 0
    
    @classmethod
    def from_row(cls, row: dict) -> "RotationState":
        """Create RotationState from database row."""
        return cls(
            asset_id=row["asset_id"],
            last_refresh_at=row.get("last_refresh_at"),
            priority_level=row.get("priority_level", 2),
            in_top50=bool(row.get("in_top50", 0)),
            cooldown_until=row.get("cooldown_until"),
            last_error=row.get("last_error"),
            refresh_count=row.get("refresh_count", 0),
        )


@dataclass
class WatchlistItem:
    """User watchlist item."""
    id: Optional[int] = None
    asset_id: str = ""
    user_id: str = "default"
    notes: Optional[str] = None
    alert_price_above: Optional[float] = None
    alert_price_below: Optional[float] = None
    alert_score_below: Optional[int] = None
    added_at: Optional[datetime] = None
    
    # Joined fields from other tables
    symbol: Optional[str] = None
    name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    score_total: Optional[float] = None
    last_price: Optional[float] = None
    
    @classmethod
    def from_row(cls, row: dict) -> "WatchlistItem":
        """Create WatchlistItem from database row."""
        asset_type = None
        if row.get("asset_type"):
            asset_type = AssetType.from_string(row["asset_type"])
        
        return cls(
            id=row.get("id"),
            asset_id=row["asset_id"],
            user_id=row.get("user_id", "default"),
            notes=row.get("notes"),
            alert_price_above=row.get("alert_price_above"),
            alert_price_below=row.get("alert_price_below"),
            alert_score_below=row.get("alert_score_below"),
            added_at=row.get("added_at"),
            symbol=row.get("symbol"),
            name=row.get("name"),
            asset_type=asset_type,
            score_total=row.get("score_total"),
            last_price=row.get("last_price"),
        )


@dataclass
class PriorityQueueItem:
    """Item in the priority calculation queue."""
    id: Optional[int] = None
    asset_id: str = ""
    requested_by: str = "user"
    priority: int = 1
    status: QueueStatus = QueueStatus.PENDING
    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @classmethod
    def from_row(cls, row: dict) -> "PriorityQueueItem":
        """Create PriorityQueueItem from database row."""
        status = QueueStatus.PENDING
        if row.get("status"):
            try:
                status = QueueStatus(row["status"])
            except ValueError:
                pass
        
        return cls(
            id=row.get("id"),
            asset_id=row["asset_id"],
            requested_by=row.get("requested_by", "user"),
            priority=row.get("priority", 1),
            status=status,
            requested_at=row.get("requested_at"),
            completed_at=row.get("completed_at"),
            error=row.get("error"),
        )


@dataclass
class ProQuota:
    """Pro mode usage quota."""
    id: Optional[int] = None
    user_id: str = "default"
    period_start: str = ""
    period_end: str = ""
    calculations_used: int = 0
    calculations_limit: int = 200
    tier: ProTier = ProTier.FREE
    
    @property
    def remaining(self) -> int:
        """Remaining calculations in current period."""
        return max(0, self.calculations_limit - self.calculations_used)
    
    @property
    def usage_percent(self) -> float:
        """Usage percentage."""
        if self.calculations_limit == 0:
            return 100.0
        return (self.calculations_used / self.calculations_limit) * 100
    
    @classmethod
    def from_row(cls, row: dict) -> "ProQuota":
        """Create ProQuota from database row."""
        tier = ProTier.FREE
        if row.get("tier"):
            try:
                tier = ProTier(row["tier"])
            except ValueError:
                pass
        
        return cls(
            id=row.get("id"),
            user_id=row.get("user_id", "default"),
            period_start=row.get("period_start", ""),
            period_end=row.get("period_end", ""),
            calculations_used=row.get("calculations_used", 0),
            calculations_limit=row.get("calculations_limit", 200),
            tier=tier,
        )


@dataclass
class ProviderHealth:
    """Provider health check result."""
    provider: str
    status: str  # "healthy", "degraded", "down"
    message: Optional[str] = None
    latency_ms: int = 0
    last_check: Optional[datetime] = None


@dataclass
class SearchResult:
    """Search result item from provider."""
    symbol: str
    name: str
    asset_type: AssetType
    exchange: str
    currency: str = "USD"
    country: str = "US"


@dataclass 
class PaginatedResult:
    """Paginated query result."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1
