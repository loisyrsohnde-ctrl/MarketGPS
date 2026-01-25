"""
MarketGPS - Systeme.io Integration Service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: Systeme.io is for MARKETING ONLY.
It should NEVER be used to decide access control.
All access decisions are made by Stripe via billing_routes.py.

This service:
- Syncs contacts to Systeme.io
- Applies/removes tags based on subscription events
- Operates asynchronously (non-blocking)
- Failures here do NOT affect user access
"""

import os
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEMEIO_API_KEY = os.environ.get("SYSTEMEIO_API_KEY", "")
SYSTEMEIO_API_URL = "https://api.systeme.io/api"

# Tag IDs (configured via environment or hardcoded)
# These should be created in Systeme.io dashboard first
TAG_IDS = {
    "subscriber_monthly": os.environ.get("SYSTEMEIO_TAG_MONTHLY", ""),
    "subscriber_annual": os.environ.get("SYSTEMEIO_TAG_ANNUAL", ""),
    "active_subscriber": os.environ.get("SYSTEMEIO_TAG_ACTIVE", ""),
    "payment_failed": os.environ.get("SYSTEMEIO_TAG_PAYMENT_FAILED", ""),
    "churned": os.environ.get("SYSTEMEIO_TAG_CHURNED", ""),
    "trial": os.environ.get("SYSTEMEIO_TAG_TRIAL", ""),
}


class SystemeIOService:
    """
    Service for Systeme.io marketing automation.
    Non-blocking, failure-tolerant.
    """
    
    def __init__(self):
        self.api_key = SYSTEMEIO_API_KEY
        self.base_url = SYSTEMEIO_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        })
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[Dict]:
        """Make API request with error handling."""
        if not self.is_configured:
            logger.warning("Systeme.io not configured, skipping API call")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=10)
            else:
                logger.error(f"Unknown HTTP method: {method}")
                return None
            
            if response.status_code >= 400:
                logger.warning(f"Systeme.io API error: {response.status_code} - {response.text}")
                return None
            
            return response.json() if response.content else {}
        
        except requests.RequestException as e:
            logger.error(f"Systeme.io request failed: {e}")
            return None
    
    def get_or_create_contact(self, email: str, fields: dict = None) -> Optional[str]:
        """
        Get or create a contact in Systeme.io.
        Returns contact ID if successful.
        """
        # First, try to find existing contact
        result = self._request("GET", f"contacts?email={email}")
        
        if result and result.get("items"):
            contact = result["items"][0]
            return contact.get("id")
        
        # Create new contact
        data = {
            "email": email,
            "fields": fields or {},
        }
        result = self._request("POST", "contacts", data)
        
        if result:
            return result.get("id")
        
        return None
    
    def add_tag(self, contact_id: str, tag_name: str) -> bool:
        """Add a tag to a contact."""
        tag_id = TAG_IDS.get(tag_name)
        if not tag_id:
            logger.warning(f"Tag ID not configured for: {tag_name}")
            return False
        
        result = self._request("POST", f"contacts/{contact_id}/tags", {"tagId": tag_id})
        return result is not None
    
    def remove_tag(self, contact_id: str, tag_name: str) -> bool:
        """Remove a tag from a contact."""
        tag_id = TAG_IDS.get(tag_name)
        if not tag_id:
            logger.warning(f"Tag ID not configured for: {tag_name}")
            return False
        
        result = self._request("DELETE", f"contacts/{contact_id}/tags/{tag_id}")
        return result is not None
    
    def sync_subscription_status(
        self, 
        email: str, 
        plan: str, 
        status: str,
    ) -> bool:
        """
        Sync subscription status to Systeme.io.
        
        Args:
            email: User email
            plan: 'free', 'monthly', 'annual'
            status: 'active', 'trialing', 'past_due', 'canceled'
        """
        try:
            contact_id = self.get_or_create_contact(email)
            if not contact_id:
                return False
            
            # Remove all subscription tags first
            for tag in ["subscriber_monthly", "subscriber_annual", "active_subscriber", 
                       "payment_failed", "churned", "trial"]:
                self.remove_tag(contact_id, tag)
            
            # Apply appropriate tags based on status
            if status == "active":
                self.add_tag(contact_id, "active_subscriber")
                if plan == "monthly":
                    self.add_tag(contact_id, "subscriber_monthly")
                elif plan == "annual":
                    self.add_tag(contact_id, "subscriber_annual")
            
            elif status == "trialing":
                self.add_tag(contact_id, "trial")
            
            elif status == "past_due":
                self.add_tag(contact_id, "payment_failed")
            
            elif status == "canceled":
                self.add_tag(contact_id, "churned")
            
            logger.info(f"Synced to Systeme.io: {email}, plan={plan}, status={status}")
            return True
        
        except Exception as e:
            logger.error(f"Systeme.io sync failed for {email}: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# QUEUE PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════

def process_sync_queue(db: SQLiteStore, limit: int = 50) -> Dict[str, int]:
    """
    Process pending Systeme.io sync queue items.
    Called periodically by scheduler or manually.
    
    Returns stats on processed items.
    """
    service = SystemeIOService()
    
    if not service.is_configured:
        logger.info("Systeme.io not configured, skipping queue processing")
        return {"skipped": 0, "sent": 0, "failed": 0}
    
    stats = {"skipped": 0, "sent": 0, "failed": 0}
    
    with db._get_connection() as conn:
        # Get pending items
        rows = conn.execute("""
            SELECT id, user_id, email, action, tag_name, attempts
            FROM systemeio_sync_queue
            WHERE status = 'pending' AND attempts < 3
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,)).fetchall()
        
        for row in rows:
            item_id, user_id, email, action, tag_name, attempts = row
            
            try:
                contact_id = service.get_or_create_contact(email)
                if not contact_id:
                    raise Exception("Could not get/create contact")
                
                if action == "tag_add":
                    success = service.add_tag(contact_id, tag_name)
                elif action == "tag_remove":
                    success = service.remove_tag(contact_id, tag_name)
                else:
                    success = False
                
                if success:
                    conn.execute("""
                        UPDATE systemeio_sync_queue 
                        SET status = 'sent', last_attempt_at = datetime('now')
                        WHERE id = ?
                    """, (item_id,))
                    stats["sent"] += 1
                else:
                    raise Exception("API call returned failure")
            
            except Exception as e:
                conn.execute("""
                    UPDATE systemeio_sync_queue 
                    SET status = CASE WHEN attempts >= 2 THEN 'failed' ELSE 'pending' END,
                        attempts = attempts + 1,
                        last_attempt_at = datetime('now'),
                        error_message = ?
                    WHERE id = ?
                """, (str(e), item_id))
                stats["failed"] += 1
    
    if stats["sent"] > 0 or stats["failed"] > 0:
        logger.info(f"Systeme.io queue processed: {stats}")
    
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def sync_subscriber(email: str, plan: str, status: str):
    """
    Quick sync for subscription changes.
    Non-blocking, logs errors but doesn't raise.
    """
    try:
        service = SystemeIOService()
        service.sync_subscription_status(email, plan, status)
    except Exception as e:
        logger.warning(f"Systeme.io sync failed (non-blocking): {e}")
