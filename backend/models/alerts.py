"""
MarketGPS - Alert System Data Models
Defines Alert Types, Alert Rules, and Alert Statuses
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json


class AlertType(Enum):
    """Types of alerts that can be triggered"""
    SCORE_CHANGE = "score_change"          # Score increases/decreases significantly
    SCORE_THRESHOLD = "score_threshold"    # Score crosses a threshold
    PRICE_ALERT = "price_alert"            # Price reaches a level
    WATCHLIST_ALERT = "watchlist_alert"    # Asset on watchlist changes
    OPPORTUNITY = "opportunity"             # New opportunity detected (high score)
    BREAKING_NEWS = "breaking_news"        # Important news item
    PORTFOLIO_ALERT = "portfolio_alert"    # Portfolio-related alert


class AlertStatus(Enum):
    """Status of an alert"""
    PENDING = "pending"        # Created but not yet processed
    SENT = "sent"              # Delivered to user
    READ = "read"              # User has seen the alert
    DISMISSED = "dismissed"    # User explicitly dismissed it
    EXPIRED = "expired"        # Alert is too old to be relevant


class AlertPriority(Enum):
    """Priority level of alert"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConditionOperator(Enum):
    """Operators for alert conditions"""
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CONTAINS = "contains"
    BETWEEN = "between"


@dataclass
class AlertCondition:
    """Single condition for an alert rule"""
    field: str                          # Field to check (e.g., "score", "price", "sector")
    operator: str                        # Comparison operator
    value: Any                           # Value to compare against
    value_high: Optional[Any] = None    # For BETWEEN operator

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertCondition':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class AlertRule:
    """Rule that defines when alerts should be generated"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    alert_type: str = ""                 # AlertType enum value as string
    asset_id: Optional[str] = None       # None for global alerts
    condition: Dict[str, Any] = field(default_factory=dict)  # Alert condition
    channels: List[str] = field(default_factory=lambda: ["in_app"])  # ["email", "push", "in_app"]
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertRule':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Alert:
    """Individual alert generated when conditions are met"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    rule_id: Optional[str] = None
    alert_type: str = ""                 # AlertType enum value as string
    priority: str = "medium"             # AlertPriority enum value as string
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)  # Context data (asset, score, price, etc.)
    status: str = "pending"              # AlertStatus enum value as string
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    read_at: Optional[str] = None
    dismissed_at: Optional[str] = None
    sent_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class AlertStatistics:
    """Statistics about alerts for a user"""
    user_id: str = ""
    total_alerts: int = 0
    unread_count: int = 0
    pending_count: int = 0
    active_rules: int = 0
    today_alerts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AlertConfig:
    """Configuration for alert system"""

    # Default channels
    DEFAULT_CHANNELS = ["in_app"]

    # Score change detection (percentage change from previous day)
    SCORE_CHANGE_THRESHOLD_PERCENT = 10

    # Opportunity threshold (minimum score to consider as opportunity)
    OPPORTUNITY_MIN_SCORE = 80

    # News scoring
    BREAKING_NEWS_MIN_SCORE = 7

    # Alert retention (days)
    ALERT_RETENTION_DAYS = 30

    # Rate limiting (max alerts per hour per user)
    MAX_ALERTS_PER_HOUR = 50

    # Email configuration
    EMAIL_DIGEST_ENABLED = True
    EMAIL_DIGEST_TIME = "08:00"  # UTC
    EMAIL_DIGEST_FREQUENCY = "daily"  # daily, weekly

    # Push notification configuration
    PUSH_ENABLED = True

    # In-app notification configuration
    INAPP_ENABLED = True
