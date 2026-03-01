"""
Scoring endpoints: on-demand scoring, quota, ad-hoc scoring.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Header

from .shared import db, resolve_user_id

router = APIRouter()


@router.post("/assets/{ticker}/score")
async def calculate_score_on_demand(
    ticker: str,
    force: bool = Query(False, description="Force recalculation even if cached"),
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Calculate score for an asset on-demand."""
    from scoring_service import (
        OnDemandScoringService,
        QuotaExceededError,
        AssetNotFoundError,
        ScoringError
    )

    try:
        resolved_user_id = resolve_user_id(user_id, authorization)
        service = OnDemandScoringService(store=db)

        result = service.calculate_score(
            ticker=ticker,
            user_id=resolved_user_id,
            force=force
        )

        return result

    except QuotaExceededError as e:
        # Return cached score if available instead of hard 403
        try:
            cached = db.query("SELECT * FROM scores_latest WHERE ticker = ?", (ticker,))
            if cached:
                row = cached[0] if isinstance(cached, list) else cached
                return {
                    "ticker": ticker,
                    "score_total": row.get("score_total"),
                    "score_value": row.get("score_value"),
                    "score_momentum": row.get("score_momentum"),
                    "score_safety": row.get("score_safety"),
                    "from_cache": True,
                    "quota_exceeded": True,
                    "message": str(e),
                }
        except Exception:
            pass
        raise HTTPException(status_code=403, detail={"error": "quota_exceeded", "message": str(e)})
    except AssetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ScoringError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/quota")
async def get_user_quota(
    user_id: str = Query("default"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Get current quota status for user."""
    from scoring_service import OnDemandScoringService

    try:
        resolved_user_id = resolve_user_id(user_id, authorization)
        service = OnDemandScoringService(store=db)
        quota = service.get_quota_status(resolved_user_id)
        return quota
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/adhoc")
async def score_adhoc(
    ticker: str = Query(..., description="Ticker symbol"),
    exchange: Optional[str] = Query(None, description="Exchange code"),
    asset_type: Optional[str] = Query(None, description="Asset type override"),
    add_to_universe: bool = Query(False, description="Add asset to universe"),
    force_refresh: bool = Query(False, description="Force data refresh"),
):
    """Score any ticker on-the-fly, even if it's not in the universe."""
    try:
        from adhoc_scoring import AdHocScoringService

        service = AdHocScoringService(store=db)
        result = service.score_ticker(
            ticker=ticker,
            exchange=exchange,
            asset_type=asset_type,
            add_to_universe=add_to_universe,
            force_refresh=force_refresh,
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail={"error": "scoring_failed", "ticker": ticker, "message": result.error}
            )

        return result.to_dict()

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="adhoc_scoring module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/adhoc/batch")
async def score_adhoc_batch(
    tickers: str = Query(..., description="Comma-separated list of tickers (max 10)"),
    add_to_universe: bool = Query(False, description="Add assets to universe"),
):
    """Score multiple tickers in batch."""
    try:
        from adhoc_scoring import AdHocScoringService

        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]

        if not ticker_list:
            raise HTTPException(status_code=400, detail="No tickers provided")

        if len(ticker_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 tickers per batch request")

        service = AdHocScoringService(store=db)
        results = service.score_batch(ticker_list, add_to_universe=add_to_universe)

        return {
            "total": len(results),
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "results": [r.to_dict() for r in results],
        }

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="adhoc_scoring module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/adhoc/resolve")
async def resolve_ticker(
    ticker: str = Query(..., description="Ticker to resolve"),
    exchange: Optional[str] = Query(None, description="Exchange hint"),
):
    """Resolve a ticker to its full asset_id without scoring."""
    try:
        from adhoc_scoring import AdHocScoringService

        service = AdHocScoringService(store=db)
        resolved = service._resolve_ticker(ticker, exchange)

        return {"original": ticker, "resolved": resolved}

    except ImportError:
        raise HTTPException(status_code=503, detail="adhoc_scoring module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
