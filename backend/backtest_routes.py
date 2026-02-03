"""
Backtest API Routes for MarketGPS

Provides endpoints for:
- Running backtests on user strategies
- Retrieving available benchmarks and presets
- Comparing strategies vs benchmarks
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Query, HTTPException, Header, Body, Depends
from pydantic import BaseModel, Field, validator

from backtest_service import (
    BacktestService,
    BacktestConfig,
    create_backtest_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class BacktestRequestModel(BaseModel):
    """Request to run a backtest."""
    strategy_id: str
    initial_capital: float = Field(default=10000, ge=100, le=10000000)
    start_date: Optional[str] = None  # YYYY-MM-DD, default: 5 years ago
    end_date: Optional[str] = None  # YYYY-MM-DD, default: today
    rebalance_frequency: str = Field(default="monthly")
    benchmark: str = Field(default="SPY")
    compositions: List[Dict[str, float]] = Field(default_factory=list)  # [{ticker: weight}]

    @validator('rebalance_frequency')
    def validate_rebalance(cls, v):
        valid = ["daily", "weekly", "monthly", "quarterly"]
        if v not in valid:
            raise ValueError(f"Invalid rebalance frequency. Use: {valid}")
        return v

    @validator('benchmark')
    def validate_benchmark(cls, v):
        valid_benchmarks = ["SPY", "QQQ", "IWM", "VEA", "AGG"]
        if v not in valid_benchmarks:
            raise ValueError(f"Invalid benchmark. Use: {valid_benchmarks}")
        return v


class BacktestPreset(BaseModel):
    """Backtest time period preset."""
    id: str
    label: str
    description: str
    start_offset_years: Optional[int] = None
    start_date: Optional[str] = None


class BenchmarkInfo(BaseModel):
    """Available benchmark information."""
    id: str
    name: str
    description: str
    asset_class: str


class BacktestMetrics(BaseModel):
    """Key backtest metrics."""
    total_return_pct: float
    annualized_return_pct: float
    benchmark_return_pct: float
    alpha: float
    volatility_annual_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float


class EquityCurvePoint(BaseModel):
    """Single point in equity curve."""
    date: str
    portfolio_value: float
    benchmark_value: float
    portfolio_return_pct: float
    benchmark_return_pct: float


class DrawdownPoint(BaseModel):
    """Drawdown data point."""
    date: str
    drawdown_pct: float


class MonthlyReturnData(BaseModel):
    """Monthly return statistics."""
    period: str
    return_pct: float
    benchmark_return_pct: float


class BacktestResponseModel(BaseModel):
    """Complete backtest result."""
    # Metrics
    total_return_pct: float
    annualized_return_pct: float
    benchmark_return_pct: float
    benchmark_annualized_return_pct: float
    alpha: float
    volatility_annual_pct: float
    benchmark_volatility_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float

    # Win/loss
    winning_periods: int
    losing_periods: int
    win_rate_pct: float
    best_period_pct: float
    worst_period_pct: float
    best_month: str
    worst_month: str

    # Final values
    final_portfolio_value: float
    final_benchmark_value: float

    # Time series
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    monthly_returns: List[Dict[str, Any]]

    # Metadata
    data_points: int
    start_date: str
    end_date: str
    strategy_id: str
    benchmark: str


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_backtest_service() -> BacktestService:
    """Get or create backtest service instance."""
    # Try to load parquet store if available
    try:
        from storage.parquet_store import ParquetStore
        parquet_store = ParquetStore()
    except Exception as e:
        logger.warning(f"Parquet store unavailable: {e}")
        parquet_store = None

    return create_backtest_service(parquet_store)


def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """Parse date string in YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/run", response_model=BacktestResponseModel)
async def run_backtest(request: BacktestRequestModel) -> BacktestResponseModel:
    """
    Run a backtest on a strategy.

    Args:
        request: Backtest configuration

    Returns:
        Complete backtest results with metrics and time series data
    """
    try:
        # Parse dates
        start_date = parse_date_string(request.start_date)
        end_date = parse_date_string(request.end_date)

        # Set defaults
        if end_date is None:
            end_date = date.today()

        if start_date is None:
            start_date = end_date - timedelta(days=365*5)  # 5 years

        # Validate
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        if not request.compositions:
            raise ValueError("compositions cannot be empty")

        # Validate weights sum to ~1.0
        total_weight = sum(sum(comp.values()) for comp in request.compositions)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Composition weights must sum to 1.0, got {total_weight:.4f}")

        # Create config
        config = BacktestConfig(
            strategy_id=request.strategy_id,
            initial_capital=request.initial_capital,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency=request.rebalance_frequency,
            benchmark=request.benchmark,
            compositions=request.compositions,
        )

        # Run backtest
        service = get_backtest_service()
        result = service.run_backtest(config)

        # Convert to response model
        return BacktestResponseModel(
            total_return_pct=result.total_return_pct,
            annualized_return_pct=result.annualized_return_pct,
            benchmark_return_pct=result.benchmark_return_pct,
            benchmark_annualized_return_pct=result.benchmark_annualized_return_pct,
            alpha=result.alpha,
            volatility_annual_pct=result.volatility_annual_pct,
            benchmark_volatility_pct=result.benchmark_volatility_pct,
            max_drawdown_pct=result.max_drawdown_pct,
            sharpe_ratio=result.sharpe_ratio,
            sortino_ratio=result.sortino_ratio,
            winning_periods=result.winning_periods,
            losing_periods=result.losing_periods,
            win_rate_pct=result.win_rate_pct,
            best_period_pct=result.best_period_pct,
            worst_period_pct=result.worst_period_pct,
            best_month=result.best_month,
            worst_month=result.worst_month,
            final_portfolio_value=result.final_portfolio_value,
            final_benchmark_value=result.final_benchmark_value,
            equity_curve=result.equity_curve,
            drawdown_curve=result.drawdown_curve,
            monthly_returns=result.monthly_returns,
            data_points=result.data_points,
            start_date=result.start_date,
            end_date=result.end_date,
            strategy_id=result.strategy_id,
            benchmark=result.benchmark,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Backtest execution failed")


@router.get("/presets", response_model=List[BacktestPreset])
async def get_backtest_presets() -> List[BacktestPreset]:
    """
    Get predefined backtest time period presets.

    Returns:
        List of BacktestPreset configurations
    """
    today = date.today()

    return [
        BacktestPreset(
            id="1y",
            label="1 Year",
            description="Last 12 months of trading",
            start_offset_years=1,
        ),
        BacktestPreset(
            id="3y",
            label="3 Years",
            description="Last 3 years of trading",
            start_offset_years=3,
        ),
        BacktestPreset(
            id="5y",
            label="5 Years",
            description="Last 5 years of trading",
            start_offset_years=5,
        ),
        BacktestPreset(
            id="10y",
            label="10 Years",
            description="Last 10 years of trading",
            start_offset_years=10,
        ),
        BacktestPreset(
            id="ytd",
            label="Year-to-Date",
            description="Since January 1st of current year",
            start_date=f"{today.year}-01-01",
        ),
    ]


@router.get("/benchmarks", response_model=List[BenchmarkInfo])
async def get_available_benchmarks() -> List[BenchmarkInfo]:
    """
    Get available benchmarks for strategy comparison.

    Returns:
        List of BenchmarkInfo objects
    """
    return [
        BenchmarkInfo(
            id="SPY",
            name="S&P 500",
            description="500 largest US companies",
            asset_class="US Equities",
        ),
        BenchmarkInfo(
            id="QQQ",
            name="Nasdaq 100",
            description="Top 100 non-financial US companies",
            asset_class="US Tech Equities",
        ),
        BenchmarkInfo(
            id="IWM",
            name="Russell 2000",
            description="2000 smallest US public companies",
            asset_class="US Small Caps",
        ),
        BenchmarkInfo(
            id="VEA",
            name="MSCI EAFE",
            description="Developed markets (Europe, Australia, Far East)",
            asset_class="International Equities",
        ),
        BenchmarkInfo(
            id="AGG",
            name="US Aggregate Bond",
            description="US investment-grade bonds",
            asset_class="Fixed Income",
        ),
    ]


@router.get("/rebalance-frequencies", response_model=List[Dict[str, str]])
async def get_rebalance_frequencies() -> List[Dict[str, str]]:
    """
    Get available rebalancing frequencies.

    Returns:
        List of frequency options
    """
    return [
        {"id": "daily", "label": "Daily", "description": "Rebalance every trading day"},
        {"id": "weekly", "label": "Weekly", "description": "Rebalance every Monday"},
        {"id": "monthly", "label": "Monthly", "description": "Rebalance at month-end"},
        {"id": "quarterly", "label": "Quarterly", "description": "Rebalance at quarter-end"},
    ]


@router.get("/stats", response_model=Dict[str, Any])
async def get_backtest_statistics() -> Dict[str, Any]:
    """
    Get general backtest statistics and information.

    Returns:
        Dictionary with backtest information
    """
    return {
        "default_initial_capital": 10000,
        "min_initial_capital": 100,
        "max_initial_capital": 10000000,
        "risk_free_rate_annual": 0.02,
        "default_rebalance_frequency": "monthly",
        "default_benchmark": "SPY",
        "supported_frequencies": ["daily", "weekly", "monthly", "quarterly"],
        "available_benchmarks": ["SPY", "QQQ", "IWM", "VEA", "AGG"],
    }
