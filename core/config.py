"""
MarketGPS v7.0 - Configuration Module
Loads environment variables and provides application-wide settings.
"""
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


@dataclass
class EODHDConfig:
    """EODHD API Configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("EODHD_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("EODHD_BASE_URL", "https://eodhd.com/api"))
    default_exchange: str = field(default_factory=lambda: os.getenv("DEFAULT_EXCHANGE", "US"))
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_per_second: float = 5.0  # Max 5 requests/second
    
    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and self.api_key != "changeme" and len(self.api_key) > 10)
    
    def validate_at_startup(self, raise_error: bool = False) -> bool:
        """
        Validate EODHD API key at startup.
        
        Args:
            raise_error: If True, raise ValueError if not configured
            
        Returns:
            True if configured, False otherwise
        """
        if not self.is_configured:
            msg = (
                "EODHD API key not configured. "
                "Set EODHD_API_KEY environment variable. "
                "Get your key at https://eodhd.com"
            )
            if raise_error:
                raise ValueError(msg)
            logging.getLogger(__name__).warning(msg)
            return False
        return True


@dataclass
class PipelineConfig:
    """Pipeline Configuration."""
    rotation_batch_size: int = field(
        default_factory=lambda: int(os.getenv("ROTATION_BATCH_SIZE", "50"))
    )
    rotation_period_minutes: int = field(
        default_factory=lambda: int(os.getenv("ROTATION_PERIOD_MINUTES", "15"))
    )
    gating_coverage_min: float = 0.90
    gating_adv_min_equity: float = 2_000_000  # $2M ADV minimum
    gating_adv_min_etf: float = 5_000_000     # $5M ADV minimum for ETFs
    gating_lookback_days: int = 1260          # 5 years (institutional grade)
    scoring_lookback_days: int = 1260         # 5 years for scoring calculations
    top_n_scores: int = 50
    
    # Scheduler configuration
    schedule_rotation_minutes: int = field(
        default_factory=lambda: int(os.getenv("SCHEDULE_ROTATION_MINUTES", "15"))
    )
    schedule_gating_hours: int = field(
        default_factory=lambda: int(os.getenv("SCHEDULE_GATING_HOURS", "6"))
    )
    schedule_pool_hours: int = field(
        default_factory=lambda: int(os.getenv("SCHEDULE_POOL_HOURS", "6"))
    )
    schedule_universe_days: int = field(
        default_factory=lambda: int(os.getenv("SCHEDULE_UNIVERSE_DAYS", "7"))
    )
    
    # AFRICA-specific thresholds (more lenient)
    africa_gating_coverage_min: float = 0.70
    africa_gating_adv_min_equity: float = 100_000  # $100K ADV for Africa
    africa_gating_lookback_days: int = 180         # 6 months


@dataclass
class ScoringConfig:
    """Scoring Configuration."""
    # Weights for EQUITY
    equity_weights: dict = field(default_factory=lambda: {
        "value": 0.30,
        "momentum": 0.40,
        "safety": 0.30
    })
    # Weights for ETF (no value pillar)
    etf_weights: dict = field(default_factory=lambda: {
        "momentum": 0.60,
        "safety": 0.40
    })
    # Feature targets for normalization
    rsi_optimal_low: float = 40.0
    rsi_optimal_high: float = 70.0
    volatility_target_max: float = 30.0  # 30% annual vol
    drawdown_target_max: float = 20.0    # 20% max drawdown
    pe_target_low: float = 5.0
    pe_target_high: float = 40.0


@dataclass
class StorageConfig:
    """Storage Configuration."""
    # Get project root directory (where this config file is located, going up to project root)
    _project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.resolve())
    
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", str(Path(__file__).parent.parent / "data")))
    )
    sqlite_path: Path = field(
        default_factory=lambda: Path(os.getenv("SQLITE_PATH", str(Path(__file__).parent.parent / "data/sqlite/marketgps.db")))
    )
    parquet_dir: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "data/parquet"
    )
    
    def ensure_paths(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        (self.parquet_dir / "bars_daily").mkdir(parents=True, exist_ok=True)


@dataclass
class UIConfig:
    """UI Configuration."""
    app_name: str = "MarketGPS"
    app_subtitle: str = "Score d'Analyse — 0 à 100"
    # Color palette
    bg_primary: str = "#0B1220"
    bg_secondary: str = "#0F1A2B"
    bg_surface: str = "#141E30"
    border_color: str = "#1E2A3A"
    text_high: str = "#E6EDF7"
    text_mid: str = "#8899AA"
    text_low: str = "#556677"
    green_primary: str = "#2EA043"
    green_dark: str = "#238636"
    green_light: str = "#3FB950"
    amber: str = "#D29922"
    red_soft: str = "#DA3633"


@dataclass 
class ComplianceConfig:
    """Compliance Configuration."""
    forbidden_terms: list = field(default_factory=lambda: [
        r"acheter", r"vendre", r"buy", r"sell", r"hold",
        r"recommandation", r"conseil", r"objectif de prix",
        r"target", r"take profit", r"stop loss", r"entry",
        r"short", r"long position", r"gagner", r"pari", r"win",
        r"opportunité", r"signal", r"alerte trading"
    ])
    disclaimer: str = (
        "Outil d'analyse statistique et éducatif. "
        "Aucune information ne constitue un conseil en investissement. "
        "Capital exposé à un risque de perte. "
        "Les performances passées ne préjugent pas des performances futures."
    )


@dataclass
class BillingConfig:
    """Billing/Subscription Configuration."""
    # Mode: "dev" (direct activation) or "stripe" (Stripe Checkout)
    mode: str = field(default_factory=lambda: os.getenv("BILLING_MODE", "dev"))
    
    # Plans
    plans: dict = field(default_factory=lambda: {
        "free": {
            "name": "Gratuit",
            "price_monthly": 0,
            "price_yearly": 0,
            "daily_quota": 3,
            "features": ["3 calculs/jour", "Marchés US/EU"]
        },
        "monthly_9_99": {
            "name": "Pro Mensuel",
            "price_monthly": 9.99,
            "price_yearly": None,
            "daily_quota": 200,
            "features": ["200 calculs/jour", "Tous les marchés", "Alertes personnalisées"]
        },
        "yearly_50": {
            "name": "Pro Annuel",
            "price_monthly": None,
            "price_yearly": 99.99,
            "daily_quota": 200,
            "features": ["200 calculs/jour", "Tous les marchés", "Alertes personnalisées", "Support prioritaire"]
        }
    })
    
    # Stripe configuration (for production)
    stripe_public_key: str = field(default_factory=lambda: os.getenv("STRIPE_PUBLIC_KEY", ""))
    stripe_secret_key: str = field(default_factory=lambda: os.getenv("STRIPE_SECRET_KEY", ""))
    stripe_webhook_secret: str = field(default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET", ""))
    
    # Stripe Price IDs (set in Stripe Dashboard)
    stripe_price_monthly: str = field(default_factory=lambda: os.getenv("STRIPE_PRICE_MONTHLY", ""))
    stripe_price_yearly: str = field(default_factory=lambda: os.getenv("STRIPE_PRICE_YEARLY", ""))
    
    @property
    def is_stripe_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(self.stripe_public_key and self.stripe_secret_key)
    
    @property
    def is_dev_mode(self) -> bool:
        """Check if running in dev mode (direct activation)."""
        return self.mode == "dev"


@dataclass
class AppConfig:
    """Main Application Configuration."""
    eodhd: EODHDConfig = field(default_factory=EODHDConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    billing: BillingConfig = field(default_factory=BillingConfig)
    
    def __post_init__(self):
        """Ensure paths exist after initialization."""
        self.storage.ensure_paths()


# Singleton instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the application configuration singleton."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration (useful for testing)."""
    global _config
    _config = AppConfig()
    return _config


# Lazy settings object for convenience
class _Settings:
    """Lazy proxy to AppConfig for convenient access."""
    
    @property
    def SQLITE_PATH(self) -> str:
        return str(get_config().storage.sqlite_path)
    
    @property
    def PARQUET_PATH(self) -> str:
        return str(get_config().storage.parquet_dir)
    
    @property
    def DATA_DIR(self) -> str:
        return str(get_config().storage.data_dir)
    
    @property
    def EODHD_API_KEY(self) -> str:
        return get_config().eodhd.api_key
    
    @property
    def ROTATION_BATCH_SIZE(self) -> int:
        return get_config().pipeline.rotation_batch_size
    
    @property
    def TOP_N(self) -> int:
        return get_config().pipeline.top_n_scores
    
    @property
    def BILLING_MODE(self) -> str:
        return get_config().billing.mode
    
    @property
    def IS_BILLING_DEV(self) -> bool:
        return get_config().billing.is_dev_mode


# Singleton settings instance
settings = _Settings()
