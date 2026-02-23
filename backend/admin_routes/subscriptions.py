"""
MarketGPS - Admin Subscription Endpoints

List subscriptions with detailed payment information.
"""

import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query

from .shared import (
    db, logger,
    SubscriptionSummary,
    require_admin, get_supabase_users,
)

router = APIRouter()


@router.get("/subscriptions", response_model=List[SubscriptionSummary])
async def list_subscriptions(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    status: Optional[str] = Query(None, description="Filter by status: active, canceled, etc."),
    limit: int = Query(50, ge=1, le=500),
):
    """
    List all subscriptions with detailed payment information.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        # Get Supabase users for email lookup
        supabase_users = await get_supabase_users()
        users_map = {}
        for user in supabase_users:
            user_id = user.get("id", "")
            user_metadata = user.get("user_metadata", {}) or {}
            full_name = (
                user_metadata.get("full_name") or
                user_metadata.get("name") or
                f"{user_metadata.get('first_name', '')} {user_metadata.get('last_name', '')}".strip() or
                None
            )
            users_map[user_id] = {
                "email": user.get("email", ""),
                "full_name": full_name
            }

        subscriptions = []

        with db._get_conn() as conn:
            # Query subscriptions table with all details
            query = """
                SELECT user_id, plan, status, created_at, current_period_start, current_period_end,
                       stripe_customer_id, stripe_subscription_id, amount, currency, interval,
                       cancel_at_period_end, payment_method
                FROM subscriptions
            """
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            try:
                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                for row in cursor.fetchall():
                    user_id = row[0]
                    user_info = users_map.get(user_id, {})

                    subscriptions.append(SubscriptionSummary(
                        user_id=user_id,
                        email=user_info.get("email"),
                        full_name=user_info.get("full_name"),
                        plan=row[1] or "unknown",
                        status=row[2] or "unknown",
                        created_at=row[3],
                        current_period_start=row[4] if len(row) > 4 else None,
                        current_period_end=row[5] if len(row) > 5 else None,
                        stripe_customer_id=row[6] if len(row) > 6 else None,
                        stripe_subscription_id=row[7] if len(row) > 7 else None,
                        amount=row[8] if len(row) > 8 else None,
                        currency=row[9] if len(row) > 9 else None,
                        interval=row[10] if len(row) > 10 else None,
                        cancel_at_period_end=bool(row[11]) if len(row) > 11 else False,
                        payment_method=row[12] if len(row) > 12 else None,
                    ))
            except Exception as e:
                logger.warning(f"subscriptions table query failed: {e}")
                # Try simpler query
                try:
                    cursor = conn.execute(
                        "SELECT user_id, plan, status, created_at, current_period_end FROM subscriptions ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )
                    for row in cursor.fetchall():
                        user_id = row[0]
                        user_info = users_map.get(user_id, {})
                        subscriptions.append(SubscriptionSummary(
                            user_id=user_id,
                            email=user_info.get("email"),
                            full_name=user_info.get("full_name"),
                            plan=row[1] or "unknown",
                            status=row[2] or "unknown",
                            created_at=row[3],
                            current_period_end=row[4],
                        ))
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    logger.error(f"Error processing subscription row: {e}")

            # Also check user_entitlements if subscriptions is empty
            if not subscriptions:
                try:
                    cursor = conn.execute(
                        "SELECT user_id, plan, status, created_at FROM user_entitlements WHERE plan != 'FREE' LIMIT ?",
                        (limit,)
                    )
                    for row in cursor.fetchall():
                        user_id = row[0]
                        user_info = users_map.get(user_id, {})
                        subscriptions.append(SubscriptionSummary(
                            user_id=user_id,
                            email=user_info.get("email"),
                            full_name=user_info.get("full_name"),
                            plan=row[1] or "unknown",
                            status=row[2] or "unknown",
                            created_at=row[3],
                        ))
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    logger.error(f"Error processing user_entitlements row: {e}")

        return subscriptions

    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
