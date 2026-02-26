"""
MarketGPS - Admin User Endpoints

List users and get user detail.
"""

import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query

from .shared import (
    db, logger,
    UserSummary,
    require_admin, get_supabase_users,
)

router = APIRouter()


@router.get("/users")
async def list_users(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    filter: Optional[str] = Query(None, description="Filter: all, pro, free"),
):
    """
    List all users with their full subscription details.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        supabase_users = await get_supabase_users()

        # Get detailed subscription data from local DB
        subscriptions_map = {}
        with db._get_conn() as conn:
            try:
                cursor = conn.execute("""
                    SELECT user_id, plan, status, created_at, current_period_end,
                           stripe_customer_id, stripe_subscription_id, amount, currency
                    FROM subscriptions
                """)
                for row in cursor.fetchall():
                    subscriptions_map[row[0]] = {
                        "plan": row[1],
                        "status": row[2],
                        "subscription_started": row[3],
                        "subscription_ends": row[4],
                        "stripe_customer_id": row[5],
                        "stripe_subscription_id": row[6],
                        "amount": row[7],
                        "currency": row[8],
                    }
            except Exception as e:
                logger.warning(f"Error fetching subscriptions: {e}")

            try:
                cursor = conn.execute("""
                    SELECT user_id, plan, status, created_at
                    FROM user_entitlements
                """)
                for row in cursor.fetchall():
                    if row[0] not in subscriptions_map:
                        subscriptions_map[row[0]] = {
                            "plan": row[1],
                            "status": row[2],
                            "subscription_started": row[3],
                        }
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error fetching user_entitlements: {e}")

        # Combine data
        users = []
        for user in supabase_users:
            user_id = user.get("id", "")
            sub_data = subscriptions_map.get(user_id, {})
            plan = sub_data.get("plan", "FREE")
            is_pro = plan and plan.upper() not in ("FREE", "")

            # Apply filter
            if filter == "pro" and not is_pro:
                continue
            if filter == "free" and is_pro:
                continue

            # Extract user metadata
            user_metadata = user.get("user_metadata", {}) or {}
            app_metadata = user.get("app_metadata", {}) or {}
            identities = user.get("identities", []) or []

            # Determine provider
            provider = "email"
            if identities:
                provider = identities[0].get("provider", "email")

            # Get full name from various possible sources
            full_name = (
                user_metadata.get("full_name") or
                user_metadata.get("name") or
                f"{user_metadata.get('first_name', '')} {user_metadata.get('last_name', '')}".strip() or
                None
            )

            users.append(UserSummary(
                id=user_id,
                email=user.get("email", ""),
                full_name=full_name,
                phone=user.get("phone"),
                provider=provider,
                email_confirmed=user.get("email_confirmed_at") is not None,
                created_at=user.get("created_at"),
                last_sign_in=user.get("last_sign_in_at"),
                sign_in_count=app_metadata.get("sign_in_count", 0) if app_metadata else 0,
                is_pro=is_pro,
                plan=plan if plan else "FREE",
                subscription_status=sub_data.get("status"),
                subscription_started=sub_data.get("subscription_started"),
                subscription_ends=sub_data.get("subscription_ends"),
                stripe_customer_id=sub_data.get("stripe_customer_id"),
                amount_paid=sub_data.get("amount"),
                currency=sub_data.get("currency"),
            ))

        # Sort by creation date (newest first)
        users.sort(key=lambda x: x.created_at or "", reverse=True)

        total = len(users)
        return {"users": users[offset:offset + limit], "total": total}

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_detail(
    user_id: str,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get detailed information about a specific user.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        # Get user from Supabase
        supabase_users = await get_supabase_users()
        user = None
        for u in supabase_users:
            if u.get("id") == user_id:
                user = u
                break

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get subscription data
        subscription_data = None
        with db._get_conn() as conn:
            try:
                cursor = conn.execute("""
                    SELECT plan, status, created_at, current_period_start, current_period_end,
                           stripe_customer_id, stripe_subscription_id, amount, currency, interval,
                           cancel_at_period_end, payment_method
                    FROM subscriptions WHERE user_id = ?
                """, (user_id,))
                row = cursor.fetchone()
                if row:
                    subscription_data = {
                        "plan": row[0],
                        "status": row[1],
                        "created_at": row[2],
                        "current_period_start": row[3] if len(row) > 3 else None,
                        "current_period_end": row[4] if len(row) > 4 else None,
                        "stripe_customer_id": row[5] if len(row) > 5 else None,
                        "stripe_subscription_id": row[6] if len(row) > 6 else None,
                        "amount": row[7] if len(row) > 7 else None,
                        "currency": row[8] if len(row) > 8 else None,
                        "interval": row[9] if len(row) > 9 else None,
                        "cancel_at_period_end": bool(row[10]) if len(row) > 10 else False,
                        "payment_method": row[11] if len(row) > 11 else None,
                    }
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error processing subscription data: {e}")

            # Check entitlements if no subscription
            if not subscription_data:
                try:
                    cursor = conn.execute(
                        "SELECT plan, status, created_at FROM user_entitlements WHERE user_id = ?",
                        (user_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        subscription_data = {
                            "plan": row[0],
                            "status": row[1],
                            "created_at": row[2],
                        }
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    logger.error(f"Error querying entitlements: {e}")

        # Extract user metadata
        user_metadata = user.get("user_metadata", {}) or {}
        app_metadata = user.get("app_metadata", {}) or {}
        identities = user.get("identities", []) or []

        # Determine provider
        provider = "email"
        if identities:
            provider = identities[0].get("provider", "email")

        # Get full name
        full_name = (
            user_metadata.get("full_name") or
            user_metadata.get("name") or
            f"{user_metadata.get('first_name', '')} {user_metadata.get('last_name', '')}".strip() or
            None
        )

        return {
            "id": user_id,
            "email": user.get("email", ""),
            "full_name": full_name,
            "phone": user.get("phone"),
            "provider": provider,
            "email_confirmed": user.get("email_confirmed_at") is not None,
            "email_confirmed_at": user.get("email_confirmed_at"),
            "created_at": user.get("created_at"),
            "last_sign_in": user.get("last_sign_in_at"),
            "updated_at": user.get("updated_at"),
            "sign_in_count": app_metadata.get("sign_in_count", 0) if app_metadata else 0,
            "user_metadata": user_metadata,
            "app_metadata": app_metadata,
            "identities": [{
                "provider": i.get("provider"),
                "created_at": i.get("created_at"),
                "last_sign_in_at": i.get("last_sign_in_at"),
            } for i in identities],
            "subscription": subscription_data,
            "is_pro": subscription_data and subscription_data.get("plan", "").upper() not in ("FREE", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
