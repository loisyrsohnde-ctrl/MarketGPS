"""
MarketGPS - Gamification System Data Models
Defines gamification structures: levels, badges, objectives, progress, and streaks.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class BadgeCategory(Enum):
    """Categories of badges"""
    EXPLORER = "explorer"          # Discovery badges
    ANALYST = "analyst"            # Analysis badges
    INVESTOR = "investor"          # Investment-related badges
    SOCIAL = "social"              # Sharing and community badges
    STREAK = "streak"              # Consistency badges
    MILESTONE = "milestone"        # Achievement milestones


class BadgeRarity(Enum):
    """Rarity levels for badges"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ObjectiveType(Enum):
    """Types of objectives"""
    DAILY = "daily"                # Reset every day
    WEEKLY = "weekly"              # Reset every week
    MONTHLY = "monthly"            # Reset every month
    SPECIAL = "special"            # One-time special objectives
    MILESTONE = "milestone"        # Permanent achievements


@dataclass
class Badge:
    """Badge definition that users can earn"""
    id: str
    name: str
    description: str
    icon: str                       # Emoji or icon name
    category: str                   # BadgeCategory enum value as string
    points_reward: int
    condition: Dict[str, Any]      # Unlock condition e.g., {"action": "analyze", "count": 10}
    rarity: str                     # BadgeRarity enum value as string
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Badge':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class UserLevel:
    """Level definition with perks and requirements"""
    level: int
    name: str
    min_points: int
    max_points: Optional[int]      # None for max level
    perks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserLevel':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Objective:
    """Single objective/quest for user"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = ""
    description: str = ""
    action: str = ""                # Action type to track
    target: int = 0                 # Goal count
    current: int = 0                # Current progress
    points_reward: int = 0
    objective_type: str = "weekly"  # ObjectiveType enum value as string
    expires_at: str = ""            # ISO format datetime
    completed_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Objective':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class UserProgress:
    """User's gamification progress"""
    user_id: str = ""
    total_points: int = 0
    current_level: int = 1
    current_streak: int = 0         # Days of consecutive engagement
    longest_streak: int = 0
    badges_earned: List[str] = field(default_factory=list)  # List of badge IDs
    last_activity_date: Optional[str] = None  # ISO format datetime
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProgress':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class UserAction:
    """Tracked user action for gamification"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    action: str = ""                # Type of action
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context
    points_earned: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserAction':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class GamificationStats:
    """Statistics about gamification for a user"""
    user_id: str = ""
    rank: int = 0
    rank_percentile: float = 0.0
    total_badges: int = 0
    total_objectives_completed: int = 0
    avg_daily_points: float = 0.0
    last_7_days_points: int = 0
    last_30_days_points: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class GamificationConfig:
    """Configuration constants for gamification system"""

    # Points earned per action
    POINTS_PER_ACTION = {
        "login": 5,
        "view_asset": 2,
        "analyze": 10,
        "create_alert": 5,
        "add_watchlist": 3,
        "read_news": 2,
        "run_backtest": 20,
        "view_portfolio": 3,
        "view_morning_brief": 5,
        "share_analysis": 15,
        "subscribe_pro": 100,
    }

    # Streak bonus multiplier (increases points earned)
    STREAK_BONUS_MULTIPLIER = {
        3: 1.1,      # 3 days: +10%
        7: 1.25,     # 7 days: +25%
        14: 1.5,     # 14 days: +50%
        30: 2.0,     # 30 days: +100%
    }

    # Objective reset times (cron-like format in UTC)
    DAILY_RESET_TIME = "00:00"
    WEEKLY_RESET_TIME = "Monday 00:00"
    MONTHLY_RESET_TIME = "1st 00:00"

    # Engagement metrics
    STREAKS_REQUIRE_DAILY_ACTION = True
    MAX_DAILY_POINTS = 200           # Safety cap per day
    LEADERBOARD_PERIOD_OPTIONS = ["weekly", "monthly", "all-time"]
    LEADERBOARD_TOP_USERS = 100
