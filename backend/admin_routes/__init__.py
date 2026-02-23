"""
MarketGPS - Admin Dashboard API Routes (READ-ONLY)

Ce module fournit des endpoints en LECTURE SEULE pour surveiller :
- Utilisateurs inscrits (Supabase)
- Abonnements actifs (Stripe/DB)
- Activite utilisateur
- Feedbacks recus
- Diagnostics donnees
- Quotas IA

IMPORTANT: Ce module est 100% READ-ONLY et ne modifie RIEN dans le systeme.
Il se connecte aux sources de donnees existantes sans les affecter.

Refactored from a single monolithic admin_routes.py into a Python package.
"""

from fastapi import APIRouter

# Import sub-routers
from .dashboard import router as dashboard_router
from .users import router as users_router
from .subscriptions import router as subscriptions_router
from .feedback import router as feedback_router
from .diagnostics import router as diagnostics_router
from .ai_quotas import router as ai_quotas_router

# Re-export key models for external consumers
from .shared import (
    UserSummary,
    SubscriptionSummary,
    DashboardStats,
    FeedbackSummary,
    AIQuotaUpdate,
)

# Create the main router with /admin prefix
router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# Include all sub-routers (no prefix -- the main router already has /admin)
router.include_router(dashboard_router)
router.include_router(users_router)
router.include_router(subscriptions_router)
router.include_router(feedback_router)
router.include_router(diagnostics_router)
router.include_router(ai_quotas_router)
