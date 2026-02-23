"""
Geographic validation endpoints: validation pipeline, quarantine management.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from .shared import db

router = APIRouter()


@router.get("/validation/geo/run")
async def run_geo_validation(
    limit: Optional[int] = Query(None, description="Limit number of assets to validate"),
    quarantine: bool = Query(True, description="Add invalid assets to quarantine table"),
):
    """Run geographic validation pipeline on all assets."""
    try:
        from geo_validation import run_validation_pipeline
        report = run_validation_pipeline(db, quarantine=quarantine)

        if limit:
            report["note"] = f"Validation limited to {limit} assets"

        return report
    except ImportError:
        raise HTTPException(status_code=503, detail="geo_validation module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation/geo/asset/{asset_id}")
async def validate_single_asset(asset_id: str):
    """Validate a single asset's geographic data."""
    try:
        from geo_validation import GeoValidator

        with db._get_connection() as conn:
            row = conn.execute("""
                SELECT asset_id, symbol, name, market_scope, market_code,
                       exchange_code, country
                FROM universe
                WHERE asset_id = ?
            """, (asset_id,)).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

            asset = {
                "asset_id": row[0], "symbol": row[1], "name": row[2],
                "market_scope": row[3], "market_code": row[4],
                "exchange": row[5], "country": row[6],
            }

        validator = GeoValidator()
        result = validator.validate_asset(asset)

        return {"asset": asset, "validation": result.to_dict()}
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="geo_validation module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation/quarantine")
async def get_quarantine_list(
    status: Optional[str] = Query(None, description="Filter by status: pending, fixed, ignored"),
    limit: int = Query(100, description="Maximum number of assets to return"),
):
    """Get list of quarantined assets with geographic validation errors."""
    try:
        from geo_validation import get_quarantine_report, ensure_quarantine_table

        ensure_quarantine_table(db)
        report = get_quarantine_report(db, status=status, limit=limit)
        return report
    except ImportError:
        raise HTTPException(status_code=503, detail="geo_validation module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validation/quarantine/{asset_id}/status")
async def update_asset_quarantine_status(
    asset_id: str,
    status: str = Query(..., description="New status: pending, fixed, or ignored"),
    notes: Optional[str] = Query(None, description="Review notes"),
):
    """Update the quarantine status for an asset."""
    try:
        from geo_validation import update_quarantine_status

        if status not in ("pending", "fixed", "ignored"):
            raise HTTPException(status_code=400, detail="Status must be: pending, fixed, or ignored")

        success = update_quarantine_status(db, asset_id, status, notes)

        if success:
            return {"status": "updated", "asset_id": asset_id, "new_status": status}
        else:
            raise HTTPException(status_code=400, detail="Failed to update status")
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="geo_validation module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
