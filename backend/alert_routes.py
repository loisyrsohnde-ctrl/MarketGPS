"""
MarketGPS - Alert Routes
API endpoints for managing alerts and alert rules
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends, Header
from pydantic import BaseModel

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore
from security import get_user_id_from_request
from services.alert_service import AlertService
from services.alert_detector import AlertDetector
from models.alerts import (
    Alert,
    AlertRule,
    AlertType,
    AlertStatus,
    AlertPriority,
    AlertStatistics,
)

# Initialize database and services
db = SQLiteStore()
alert_service = AlertService(db)
alert_detector = AlertDetector(db)

# Create router
router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class AlertRuleCreateRequest(BaseModel):
    """Request to create an alert rule"""
    alert_type: str
    asset_id: Optional[str] = None
    condition: dict
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = True


class AlertRuleUpdateRequest(BaseModel):
    """Request to update an alert rule"""
    alert_type: Optional[str] = None
    asset_id: Optional[str] = None
    condition: Optional[dict] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Response model for Alert"""
    id: str
    user_id: str
    rule_id: Optional[str]
    alert_type: str
    priority: str
    title: str
    message: str
    data: dict
    status: str
    created_at: str
    read_at: Optional[str]
    dismissed_at: Optional[str]
    sent_at: Optional[str]

    @classmethod
    def from_alert(cls, alert: Alert) -> "AlertResponse":
        """Convert Alert model to response"""
        return cls(**alert.to_dict())


class AlertRuleResponse(BaseModel):
    """Response model for AlertRule"""
    id: str
    user_id: str
    alert_type: str
    asset_id: Optional[str]
    condition: dict
    channels: List[str]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_rule(cls, rule: AlertRule) -> "AlertRuleResponse":
        """Convert AlertRule model to response"""
        return cls(**rule.to_dict())


class AlertStatisticsResponse(BaseModel):
    """Response model for Alert Statistics"""
    user_id: str
    total_alerts: int
    unread_count: int
    pending_count: int
    active_rules: int
    today_alerts: int

    @classmethod
    def from_stats(cls, stats: AlertStatistics) -> "AlertStatisticsResponse":
        """Convert AlertStatistics model to response"""
        return cls(**stats.to_dict())


class AlertsListResponse(BaseModel):
    """Response for listing alerts"""
    alerts: List[AlertResponse]
    total: int
    limit: int
    offset: int


class AlertRulesListResponse(BaseModel):
    """Response for listing alert rules"""
    rules: List[AlertRuleResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/", response_model=AlertsListResponse)
def get_alerts(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    days: Optional[int] = Query(None, description="Filter alerts from last N days"),
):
    """
    Get alerts for the current user

    Query parameters:
    - status: Filter by status (pending, sent, read, dismissed)
    - limit: Number of alerts to return (default 50)
    - offset: Pagination offset (default 0)
    - days: Only return alerts from last N days
    """
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        alerts, total = alert_service.get_user_alerts(
            user_id=resolved_user_id,
            status=status,
            limit=limit,
            offset=offset,
            days=days,
        )

        alert_responses = [AlertResponse.from_alert(a) for a in alerts]

        return AlertsListResponse(
            alerts=alert_responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
def get_unread_count(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Get count of unread alerts for the current user"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)
        count = alert_service.get_unread_count(resolved_user_id)
        return {"unread_count": count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
def get_statistics(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Get alert statistics for the current user"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)
        stats = alert_service.get_statistics(resolved_user_id)
        return AlertStatisticsResponse.from_stats(stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}")
def get_alert(
    alert_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Get a specific alert"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        alert = alert_service.get_alert(alert_id)
        if not alert or alert.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Alert not found")

        return AlertResponse.from_alert(alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/read")
def mark_alert_as_read(
    alert_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Mark an alert as read"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        alert = alert_service.get_alert(alert_id)
        if not alert or alert.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert = alert_service.mark_as_read(alert_id)
        return AlertResponse.from_alert(alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Dismiss an alert"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        alert = alert_service.get_alert(alert_id)
        if not alert or alert.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert = alert_service.dismiss_alert(alert_id)
        return AlertResponse.from_alert(alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dismiss-all")
def dismiss_all_alerts(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Dismiss all pending alerts for the user"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        count = alert_service.dismiss_all_for_user(resolved_user_id)
        return {"dismissed_count": count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ALERT RULES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/rules")
def list_alert_rules(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    active_only: bool = Query(False),
):
    """Get all alert rules for the current user"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        rules = alert_service.get_user_rules(resolved_user_id, active_only=active_only)
        rule_responses = [AlertRuleResponse.from_rule(r) for r in rules]

        return AlertRulesListResponse(
            rules=rule_responses,
            total=len(rule_responses),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=AlertRuleResponse)
def create_alert_rule(
    request: AlertRuleCreateRequest,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Create a new alert rule"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        rule_data = {
            "alert_type": request.alert_type,
            "asset_id": request.asset_id,
            "condition": request.condition,
            "channels": request.channels or ["in_app"],
            "is_active": request.is_active,
        }

        rule = alert_service.create_rule(resolved_user_id, rule_data)
        return AlertRuleResponse.from_rule(rule)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
def get_alert_rule(
    rule_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Get a specific alert rule"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        rule = alert_service.get_rule(rule_id)
        if not rule or rule.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Rule not found")

        return AlertRuleResponse.from_rule(rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: str,
    request: AlertRuleUpdateRequest,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Update an alert rule"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        rule = alert_service.get_rule(rule_id)
        if not rule or rule.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Rule not found")

        updates = {}
        if request.alert_type:
            updates["alert_type"] = request.alert_type
        if request.asset_id is not None:
            updates["asset_id"] = request.asset_id
        if request.condition:
            updates["condition"] = request.condition
        if request.channels:
            updates["channels"] = request.channels
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        rule = alert_service.update_rule(rule_id, updates)
        return AlertRuleResponse.from_rule(rule)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
def delete_alert_rule(
    rule_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Delete an alert rule"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        rule = alert_service.get_rule(rule_id)
        if not rule or rule.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Rule not found")

        success = alert_service.delete_rule(rule_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete rule")

        return {"deleted": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/toggle")
def toggle_alert_rule(
    rule_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Toggle an alert rule active/inactive"""
    try:
        user_id = user_id or "default"
        resolved_user_id = get_user_id_from_request(authorization, fallback_user_id=user_id)

        rule = alert_service.get_rule(rule_id)
        if not rule or rule.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Rule not found")

        rule = alert_service.toggle_rule(rule_id)
        return AlertRuleResponse.from_rule(rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION ENDPOINTS (for manual triggering/testing)
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/detect/score-changes")
def trigger_score_change_detection(
    threshold: float = Query(10, description="Score change threshold %"),
    authorization: Optional[str] = Header(None),
):
    """Manually trigger score change detection"""
    try:
        # Verify admin/authorized user
        user_id = get_user_id_from_request(authorization, fallback_user_id=None)
        if not user_id or user_id == "default":
            raise HTTPException(status_code=403, detail="Unauthorized")

        alerts = alert_detector.detect_score_changes(threshold_percent=threshold)
        return {
            "alerts_generated": len(alerts),
            "alert_ids": [a.id for a in alerts],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/opportunities")
def trigger_opportunity_detection(
    min_score: float = Query(80, description="Minimum score threshold"),
    authorization: Optional[str] = Header(None),
):
    """Manually trigger opportunity detection"""
    try:
        user_id = get_user_id_from_request(authorization, fallback_user_id=None)
        if not user_id or user_id == "default":
            raise HTTPException(status_code=403, detail="Unauthorized")

        alerts = alert_detector.detect_opportunities(min_score=min_score)
        return {
            "alerts_generated": len(alerts),
            "alert_ids": [a.id for a in alerts],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/breaking-news")
def trigger_breaking_news_detection(
    min_score: float = Query(7, description="Minimum news score"),
    authorization: Optional[str] = Header(None),
):
    """Manually trigger breaking news detection"""
    try:
        user_id = get_user_id_from_request(authorization, fallback_user_id=None)
        if not user_id or user_id == "default":
            raise HTTPException(status_code=403, detail="Unauthorized")

        alerts = alert_detector.detect_breaking_news(min_score=min_score)
        return {
            "alerts_generated": len(alerts),
            "alert_ids": [a.id for a in alerts],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
