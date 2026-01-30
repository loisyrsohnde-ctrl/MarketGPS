"""
MarketGPS - Notifications & Alerts Engine
==========================================

Proactive notification system for portfolio monitoring.

Features:
- Score drop/surge alerts
- Rebalance suggestions
- News impact notifications
- Morning brief generation
- Real-time WebSocket support (future)

Endpoints:
- GET  /api/notifications           - Get user notifications
- POST /api/notifications/read      - Mark as read
- POST /api/notifications/dismiss   - Dismiss notification
- GET  /api/notifications/settings  - Get notification preferences
- PUT  /api/notifications/settings  - Update preferences
- GET  /api/notifications/brief     - Get morning brief
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# =============================================================================
# Types & Models
# =============================================================================

class NotificationType(str, Enum):
    SCORE_DROP = "score_drop"
    SCORE_SURGE = "score_surge"
    REBALANCE = "rebalance"
    NEWS_IMPACT = "news_impact"
    MORNING_BRIEF = "morning_brief"
    OPPORTUNITY = "opportunity"
    ALERT = "alert"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NotificationAction(BaseModel):
    label: str
    action: str
    primary: bool = False


class Notification(BaseModel):
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    timestamp: str
    read: bool = False
    dismissed: bool = False
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[NotificationAction]] = None


class NotificationSettings(BaseModel):
    score_drop_enabled: bool = True
    score_drop_threshold: int = 5  # Points drop to trigger
    score_surge_enabled: bool = True
    score_surge_threshold: int = 10
    rebalance_enabled: bool = True
    rebalance_threshold: float = 5.0  # % deviation from target
    news_impact_enabled: bool = True
    morning_brief_enabled: bool = True
    morning_brief_time: str = "08:00"
    opportunity_enabled: bool = True
    sound_enabled: bool = True
    push_enabled: bool = False  # Browser push notifications


class MorningBrief(BaseModel):
    date: str
    greeting: str
    market_summary: str
    portfolio_status: Dict[str, Any]
    key_metrics: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    action_items: List[str]


# =============================================================================
# Alert Detection Engine
# =============================================================================

class AlertEngine:
    """
    Detects alert conditions based on portfolio and market data.
    In production, this would run as a background job.
    """
    
    def __init__(self, settings: NotificationSettings):
        self.settings = settings
    
    def detect_score_drops(
        self, 
        current_scores: Dict[str, int], 
        previous_scores: Dict[str, int]
    ) -> List[Notification]:
        """Detect assets with significant score drops."""
        notifications = []
        threshold = self.settings.score_drop_threshold
        
        for asset_id, current in current_scores.items():
            previous = previous_scores.get(asset_id)
            if previous is None:
                continue
                
            drop = previous - current
            if drop >= threshold:
                notifications.append(Notification(
                    id=f"score_drop_{asset_id}_{datetime.utcnow().timestamp()}",
                    type=NotificationType.SCORE_DROP,
                    priority=NotificationPriority.HIGH if drop >= 10 else NotificationPriority.MEDIUM,
                    title=f"{asset_id} : Score en baisse (-{drop} pts)",
                    message=f"Le score ProphetIA est passé de {previous} à {current}.",
                    timestamp=datetime.utcnow().isoformat(),
                    data={"ticker": asset_id, "oldScore": previous, "newScore": current, "drop": drop},
                    actions=[
                        NotificationAction(label="Analyser", action="analyze_asset", primary=True),
                        NotificationAction(label="Ignorer", action="dismiss"),
                    ],
                ))
        
        return notifications
    
    def detect_rebalance_need(
        self,
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float],
    ) -> Optional[Notification]:
        """Detect if portfolio needs rebalancing."""
        threshold = self.settings.rebalance_threshold
        deviations = []
        
        for asset_class, target in target_allocation.items():
            current = current_allocation.get(asset_class, 0)
            deviation = abs(current - target)
            if deviation >= threshold:
                deviations.append({
                    "class": asset_class,
                    "current": current,
                    "target": target,
                    "deviation": deviation,
                })
        
        if not deviations:
            return None
        
        max_deviation = max(d["deviation"] for d in deviations)
        priority = NotificationPriority.HIGH if max_deviation >= 10 else NotificationPriority.MEDIUM
        
        return Notification(
            id=f"rebalance_{datetime.utcnow().timestamp()}",
            type=NotificationType.REBALANCE,
            priority=priority,
            title="Rééquilibrage suggéré",
            message=f"Votre allocation présente des écarts significatifs par rapport à la cible ({len(deviations)} classe(s) affectée(s)).",
            timestamp=datetime.utcnow().isoformat(),
            data={"deviations": deviations},
            actions=[
                NotificationAction(label="Voir détails", action="view_rebalance", primary=True),
            ],
        )
    
    def detect_news_impact(
        self,
        news_items: List[Dict],
        holdings: List[str],
    ) -> List[Notification]:
        """Detect news that may impact portfolio holdings."""
        notifications = []
        
        for news in news_items:
            affected_tickers = news.get("affected_tickers", [])
            portfolio_impact = [t for t in affected_tickers if t in holdings]
            
            if portfolio_impact:
                sentiment = news.get("sentiment", "neutral")
                priority = NotificationPriority.HIGH if sentiment == "negative" else NotificationPriority.MEDIUM
                
                notifications.append(Notification(
                    id=f"news_impact_{news.get('id')}",
                    type=NotificationType.NEWS_IMPACT,
                    priority=priority,
                    title=f"Actualité : Impact sur {', '.join(portfolio_impact[:3])}",
                    message=news.get("title", "")[:100],
                    timestamp=datetime.utcnow().isoformat(),
                    data={
                        "news_id": news.get("id"),
                        "affected_tickers": portfolio_impact,
                        "sentiment": sentiment,
                    },
                ))
        
        return notifications


# =============================================================================
# Morning Brief Generator
# =============================================================================

def generate_morning_brief(
    portfolio_value: float = 250000,
    portfolio_score: int = 72,
    holdings: List[str] = None,
) -> MorningBrief:
    """
    Generate personalized morning brief.
    In production, this would aggregate real data.
    """
    today = datetime.now()
    hour = today.hour
    
    if hour < 12:
        greeting = "Bonjour"
    elif hour < 18:
        greeting = "Bon après-midi"
    else:
        greeting = "Bonsoir"
    
    # Market summary (demo)
    market_summary = """Les marchés européens ouvrent en hausse (+0.4%) portés par les valeurs technologiques. 
Le CAC 40 progresse de 0.5% tandis que le DAX gagne 0.3%. 
Aux États-Unis, les futures indiquent une ouverture stable après les résultats mitigés des GAFAM."""
    
    # Portfolio status
    portfolio_status = {
        "value": portfolio_value,
        "change_1d": 0.8,
        "change_1d_value": portfolio_value * 0.008,
        "score": portfolio_score,
        "score_trend": "stable",
        "vs_benchmark": 2.3,  # % outperformance vs S&P 500
    }
    
    # Key metrics
    key_metrics = [
        {"label": "Score ProphetIA", "value": str(portfolio_score), "status": "good" if portfolio_score >= 70 else "warning"},
        {"label": "Perf. YTD", "value": "+12.4%", "status": "good"},
        {"label": "Volatilité", "value": "14.2%", "status": "neutral"},
        {"label": "Alpha", "value": "+2.3%", "status": "good"},
    ]
    
    # Alerts
    alerts = [
        {"type": "warning", "message": "AAPL : résultats Q4 ce soir à 22h"},
        {"type": "info", "message": "BCE : décision taux à 14h15"},
    ]
    
    # Opportunities
    opportunities = [
        {"ticker": "MSFT", "score": 84, "signal": "Accumulation institutionnelle"},
        {"ticker": "GOOGL", "score": 79, "signal": "Breakout technique"},
    ]
    
    # Action items
    action_items = [
        "Surveiller les résultats AAPL ce soir",
        "Considérer renforcement position MSFT",
        "Rééquilibrage suggéré : -5% actions, +5% obligations",
    ]
    
    return MorningBrief(
        date=today.strftime("%d %B %Y"),
        greeting=greeting,
        market_summary=market_summary,
        portfolio_status=portfolio_status,
        key_metrics=key_metrics,
        alerts=alerts,
        opportunities=opportunities,
        action_items=action_items,
    )


# =============================================================================
# Demo Notifications Generator
# =============================================================================

def generate_demo_notifications(user_id: str = "default") -> List[Notification]:
    """Generate demo notifications for testing."""
    now = datetime.utcnow()
    
    return [
        Notification(
            id="1",
            type=NotificationType.MORNING_BRIEF,
            priority=NotificationPriority.MEDIUM,
            title=f"Brief Matinal — {now.strftime('%d %B')}",
            message="Marchés en hausse de 0.8%. Votre portefeuille surperforme le S&P 500. 2 opportunités détectées.",
            timestamp=(now - timedelta(hours=1)).isoformat(),
            actions=[
                NotificationAction(label="Voir le brief", action="view_brief", primary=True),
            ],
        ),
        Notification(
            id="2",
            type=NotificationType.SCORE_DROP,
            priority=NotificationPriority.HIGH,
            title="AAPL : Score en baisse (-8 pts)",
            message="Le score ProphetIA d'Apple est passé de 82 à 74 suite aux résultats trimestriels.",
            timestamp=(now - timedelta(hours=2)).isoformat(),
            data={"ticker": "AAPL", "oldScore": 82, "newScore": 74},
            actions=[
                NotificationAction(label="Analyser", action="analyze_asset", primary=True),
                NotificationAction(label="Ignorer", action="dismiss"),
            ],
        ),
        Notification(
            id="3",
            type=NotificationType.REBALANCE,
            priority=NotificationPriority.MEDIUM,
            title="Rééquilibrage suggéré",
            message="Votre allocation actions dépasse la cible de 5%. Considérez un arbitrage vers les obligations.",
            timestamp=(now - timedelta(days=1)).isoformat(),
            read=True,
            actions=[
                NotificationAction(label="Voir détails", action="view_rebalance", primary=True),
            ],
        ),
        Notification(
            id="4",
            type=NotificationType.NEWS_IMPACT,
            priority=NotificationPriority.MEDIUM,
            title="BCE : Impact sur votre portefeuille",
            message="La décision de la BCE sur les taux pourrait impacter vos positions obligataires (+0.3% estimé).",
            timestamp=(now - timedelta(days=2)).isoformat(),
            read=True,
            data={"impact": 0.3, "sector": "bonds"},
        ),
        Notification(
            id="5",
            type=NotificationType.OPPORTUNITY,
            priority=NotificationPriority.LOW,
            title="Nouvelle opportunité : MSFT",
            message="Microsoft atteint un score de 84 avec un signal d'accumulation institutionnelle.",
            timestamp=(now - timedelta(days=3)).isoformat(),
            read=True,
            data={"ticker": "MSFT", "score": 84},
            actions=[
                NotificationAction(label="Voir", action="view_opportunity"),
                NotificationAction(label="Ajouter watchlist", action="add_watchlist", primary=True),
            ],
        ),
    ]


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("")
async def get_notifications(
    user_id: str = Query("default", description="User ID"),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get user notifications.
    Returns notifications sorted by timestamp (newest first).
    """
    notifications = generate_demo_notifications(user_id)
    
    if unread_only:
        notifications = [n for n in notifications if not n.read]
    
    # Apply pagination
    total = len(notifications)
    notifications = notifications[offset:offset + limit]
    
    return {
        "success": True,
        "notifications": [n.dict() for n in notifications],
        "total": total,
        "unread_count": sum(1 for n in notifications if not n.read),
    }


@router.post("/read")
async def mark_as_read(
    notification_ids: List[str] = Body(..., description="List of notification IDs"),
    user_id: str = Query("default"),
):
    """Mark notifications as read."""
    # In production: update database
    return {
        "success": True,
        "message": f"Marked {len(notification_ids)} notification(s) as read",
    }


@router.post("/read-all")
async def mark_all_as_read(user_id: str = Query("default")):
    """Mark all notifications as read."""
    return {
        "success": True,
        "message": "All notifications marked as read",
    }


@router.post("/dismiss")
async def dismiss_notification(
    notification_ids: List[str] = Body(..., description="List of notification IDs"),
    user_id: str = Query("default"),
):
    """Dismiss notifications (hide from list)."""
    return {
        "success": True,
        "message": f"Dismissed {len(notification_ids)} notification(s)",
    }


@router.get("/settings")
async def get_notification_settings(user_id: str = Query("default")):
    """Get user notification preferences."""
    # In production: fetch from database
    settings = NotificationSettings()
    return {
        "success": True,
        "settings": settings.dict(),
    }


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    user_id: str = Query("default"),
):
    """Update user notification preferences."""
    # In production: save to database
    return {
        "success": True,
        "message": "Settings updated",
        "settings": settings.dict(),
    }


@router.get("/brief")
async def get_morning_brief(
    user_id: str = Query("default"),
    portfolio_value: float = Query(250000),
    portfolio_score: int = Query(72),
):
    """
    Get personalized morning brief.
    This endpoint is called at the configured morning time.
    """
    brief = generate_morning_brief(
        portfolio_value=portfolio_value,
        portfolio_score=portfolio_score,
    )
    
    return {
        "success": True,
        "brief": brief.dict(),
    }


@router.post("/test-alert")
async def trigger_test_alert(
    alert_type: NotificationType = Query(...),
    user_id: str = Query("default"),
):
    """
    Trigger a test notification for development/testing.
    """
    test_notifications = {
        NotificationType.SCORE_DROP: Notification(
            id=f"test_{datetime.utcnow().timestamp()}",
            type=NotificationType.SCORE_DROP,
            priority=NotificationPriority.HIGH,
            title="[TEST] Score Drop Alert",
            message="This is a test notification for score drop alerts.",
            timestamp=datetime.utcnow().isoformat(),
        ),
        NotificationType.REBALANCE: Notification(
            id=f"test_{datetime.utcnow().timestamp()}",
            type=NotificationType.REBALANCE,
            priority=NotificationPriority.MEDIUM,
            title="[TEST] Rebalance Alert",
            message="This is a test notification for rebalance alerts.",
            timestamp=datetime.utcnow().isoformat(),
        ),
        NotificationType.MORNING_BRIEF: Notification(
            id=f"test_{datetime.utcnow().timestamp()}",
            type=NotificationType.MORNING_BRIEF,
            priority=NotificationPriority.MEDIUM,
            title="[TEST] Morning Brief",
            message="This is a test morning brief notification.",
            timestamp=datetime.utcnow().isoformat(),
        ),
    }
    
    notification = test_notifications.get(alert_type)
    if not notification:
        notification = Notification(
            id=f"test_{datetime.utcnow().timestamp()}",
            type=alert_type,
            priority=NotificationPriority.LOW,
            title=f"[TEST] {alert_type.value} Alert",
            message=f"This is a test notification for {alert_type.value}.",
            timestamp=datetime.utcnow().isoformat(),
        )
    
    return {
        "success": True,
        "notification": notification.dict(),
    }
