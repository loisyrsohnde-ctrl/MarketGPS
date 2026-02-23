"""
Billing schemas for Stripe checkout and subscription endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field

__all__ = [
    "CheckoutRequest",
    "CheckoutResponse",
    "PortalResponse",
    "SubscriptionStatusResponse",
]


class CheckoutRequest(BaseModel):
    """Create a Stripe Checkout Session."""
    plan: str = Field(..., pattern="^(monthly|yearly)$", description="Subscription plan")
    success_url: Optional[str] = Field(None, description="Custom success redirect URL")
    cancel_url: Optional[str] = Field(None, description="Custom cancel redirect URL")


class CheckoutResponse(BaseModel):
    """Stripe Checkout Session URL."""
    checkout_url: str


class PortalResponse(BaseModel):
    """Stripe Customer Portal URL."""
    portal_url: str


class SubscriptionStatusResponse(BaseModel):
    """Current subscription status."""
    plan: str = "FREE"
    status: str = "inactive"
    stripe_customer_id: Optional[str] = None
    current_period_end: Optional[str] = None
    daily_requests_limit: int = 10
