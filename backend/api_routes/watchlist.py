"""
Watchlist endpoints: list, add, remove, check.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Header

from .shared import db, resolve_user_id, WatchlistAddRequest

router = APIRouter()


@router.get("/watchlist")
async def get_watchlist(
    user_id: str = Query("default"),
    market_scope: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Get user's watchlist."""
    try:
        resolved_user_id = resolve_user_id(user_id, authorization)
        items = db.list_watchlist(user_id=resolved_user_id, market_scope=market_scope)

        formatted = []
        for item in items:
            formatted.append({
                "ticker": item.get("ticker"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "asset_type": item.get("asset_type"),
                "asset_id": item.get("asset_id"),
                "market_scope": item.get("market_scope"),
                "score_total": item.get("score_total"),
                "score_value": item.get("score_value"),
                "score_momentum": item.get("score_momentum"),
                "score_safety": item.get("score_safety"),
                "confidence": item.get("confidence"),
                "last_price": item.get("last_price"),
                "notes": item.get("notes"),
                "added_at": item.get("added_at"),
            })

        return formatted

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Add asset to watchlist."""
    try:
        resolved_user_id = resolve_user_id(user_id, authorization)
        success = db.add_watchlist(
            ticker=request.ticker,
            user_id=resolved_user_id,
            notes=request.notes,
            market_scope=request.market_scope
        )

        if success:
            try:
                from user_routes import create_notification
                create_notification(
                    user_id=resolved_user_id,
                    type="info",
                    title="Actif ajouté à la watchlist",
                    description=f"{request.ticker} a été ajouté à votre liste de surveillance"
                )
            except Exception:
                pass

            return {"status": "success", "ticker": request.ticker}
        else:
            raise HTTPException(status_code=400, detail="Failed to add to watchlist")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Remove asset from watchlist."""
    try:
        resolved_user_id = resolve_user_id(user_id, authorization)
        success = db.remove_watchlist(ticker=ticker, user_id=resolved_user_id)

        if success:
            return {"status": "success", "ticker": ticker}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove from watchlist")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist/check/{ticker}")
async def check_in_watchlist(
    ticker: str,
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Check if asset is in watchlist."""
    try:
        resolved_user_id = resolve_user_id(user_id, authorization)
        in_watchlist = db.is_in_watchlist(ticker=ticker, user_id=resolved_user_id)
        return {"in_watchlist": in_watchlist}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
