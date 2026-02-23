"""
Common schemas shared across multiple endpoints.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "MarketScope",
]


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    status: str = "success"
    message: Optional[str] = None


class MarketScope(BaseModel):
    """Market scope filter."""
    market_scope: str = Field("US_EU", pattern="^(US_EU|AFRICA)$")
