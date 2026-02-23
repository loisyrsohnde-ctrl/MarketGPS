"""
Portfolio schemas for account and position management.
"""

from typing import Optional, List
from pydantic import BaseModel, Field

__all__ = [
    "AccountCreateRequest",
    "AccountResponse",
    "PositionCreateRequest",
    "PositionResponse",
    "CSVMappingRequest",
    "PortfolioSummaryResponse",
]


class AccountCreateRequest(BaseModel):
    """Create a portfolio account/envelope."""
    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    broker: Optional[str] = Field(None, max_length=100, description="Broker name")
    account_type: str = Field("brokerage", description="Account type")
    currency: str = Field("USD", max_length=3, description="Account currency")
    notes: Optional[str] = Field(None, max_length=500)


class AccountResponse(BaseModel):
    """Portfolio account response."""
    id: str
    name: str
    broker: Optional[str] = None
    account_type: str = "brokerage"
    currency: str = "USD"
    position_count: int = 0
    total_value: Optional[float] = None
    created_at: Optional[str] = None


class PositionCreateRequest(BaseModel):
    """Create or update a portfolio position."""
    account_id: str = Field(..., description="Account ID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    isin: Optional[str] = Field(None, max_length=12, description="ISIN code")
    quantity: float = Field(..., gt=0, description="Number of shares")
    avg_cost: Optional[float] = Field(None, ge=0, description="Average cost basis per share")
    currency: str = Field("USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=500)


class PositionResponse(BaseModel):
    """Portfolio position response."""
    id: str
    account_id: str
    symbol: str
    name: Optional[str] = None
    asset_id: Optional[str] = None
    quantity: float
    avg_cost: Optional[float] = None
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    score_total: Optional[float] = None
    currency: str = "USD"


class CSVMappingRequest(BaseModel):
    """Column mapping for CSV import."""
    template_id: Optional[str] = Field(None, description="Broker template ID")
    symbol_col: Optional[str] = Field(None, description="Symbol column name")
    quantity_col: Optional[str] = Field(None, description="Quantity column name")
    cost_col: Optional[str] = Field(None, description="Average cost column name")
    isin_col: Optional[str] = Field(None, description="ISIN column name")


class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary with aggregations."""
    total_value: float = 0
    total_cost: float = 0
    total_gain_loss: float = 0
    total_gain_loss_pct: Optional[float] = None
    position_count: int = 0
    account_count: int = 0
    avg_score: Optional[float] = None
    allocation_by_type: Optional[dict] = None
    allocation_by_sector: Optional[dict] = None
