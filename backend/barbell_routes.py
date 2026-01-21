"""
MarketGPS - Barbell Portfolio Strategy API
==========================================
Endpoints for the Barbell investment strategy module.

The Barbell strategy allocates:
- Core (70-80%): Ultra-safe assets (bonds, gold, defensive stocks)
- Satellite (20-30%): High-growth/high-risk assets

This is an ADD-ON module - does not modify existing functionality.
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/barbell", tags=["Barbell Strategy"])


# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class BarbellAllocation(BaseModel):
    """Barbell portfolio allocation."""
    core_weight: float = 0.75  # 75% default
    satellite_weight: float = 0.25  # 25% default


class BarbellAsset(BaseModel):
    """Asset in barbell portfolio."""
    asset_id: str
    ticker: str
    name: str
    asset_type: str
    allocation_type: str  # "core" or "satellite"
    weight: float
    score_total: Optional[float] = None
    lt_score: Optional[float] = None
    lt_confidence: Optional[float] = None
    rationale: Optional[str] = None


class BarbellPortfolio(BaseModel):
    """Complete barbell portfolio."""
    id: str
    name: str
    created_at: str
    updated_at: str
    allocation: BarbellAllocation
    core_assets: List[BarbellAsset]
    satellite_assets: List[BarbellAsset]
    metrics: Dict[str, Any]


class BarbellSuggestion(BaseModel):
    """Suggested barbell portfolio."""
    risk_profile: str  # "conservative", "moderate", "aggressive"
    core_assets: List[BarbellAsset]
    satellite_assets: List[BarbellAsset]
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    rationale: str


class BarbellPortfolioList(BaseModel):
    """List of portfolios."""
    portfolios: List[BarbellPortfolio]
    total: int


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def barbell_health():
    """Health check for barbell module."""
    return {
        "status": "healthy",
        "module": "barbell",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/suggest", response_model=BarbellSuggestion)
async def suggest_barbell_portfolio(
    risk_profile: str = Query(
        "moderate", description="Risk profile: conservative, moderate, aggressive"),
    market_scope: str = Query("US_EU", description="Market scope"),
    core_count: int = Query(
        5, ge=1, le=20, description="Number of core assets"),
    satellite_count: int = Query(
        5, ge=1, le=20, description="Number of satellite assets"),
):
    """
    Generate a suggested barbell portfolio based on risk profile.

    Uses lt_score for institutional-quality selection:
    - Core: Highest lt_score assets with low volatility (Safety pillar)
    - Satellite: High momentum + growth assets (capped by institutional criteria)
    """
    try:
        # Import store here to avoid circular imports
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore

        store = SQLiteStore()

        # Get top scored assets - returns List[Tuple[Asset, Score]]
        all_assets = store.get_top_scores(market_scope=market_scope, limit=100)

        if not all_assets:
            raise HTTPException(
                status_code=404, detail="No scored assets found")

        # Separate into core (low vol, high safety) and satellite (high momentum)
        core_candidates = []
        satellite_candidates = []

        for asset_tuple in all_assets:
            # Unpack tuple (Asset, Score)
            asset_obj, score_obj = asset_tuple

            # Build combined dict from Asset and Score
            asset_dict = {
                'asset_id': asset_obj.asset_id,
                'symbol': asset_obj.symbol,
                'ticker': asset_obj.symbol,  # ticker = symbol
                'name': asset_obj.name or asset_obj.symbol,
                'asset_type': asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type),
                'market_scope': asset_obj.market_scope,
                'score_total': score_obj.score_total,
                'score_value': score_obj.score_value,
                'score_momentum': score_obj.score_momentum,
                'score_safety': score_obj.score_safety,
                'vol_annual': score_obj.vol_annual,
                'confidence': score_obj.confidence,
                'lt_score': getattr(score_obj, 'lt_score', None),
                'lt_confidence': getattr(score_obj, 'lt_confidence', None),
            }

            # Core: low volatility, defensive
            vol = asset_dict.get('vol_annual')  # Can be None
            lt_score = asset_dict.get('lt_score')
            score_safety = asset_dict.get('score_safety') or 0
            score_momentum = asset_dict.get('score_momentum') or 0
            score_total = asset_dict.get('score_total') or 0

            # Classify based on characteristics
            # Core criteria: High safety score (>65) OR (low vol < 25 AND safety > 50)
            # If vol_annual is missing, rely purely on safety score
            is_core_candidate = False
            if score_safety >= 70:
                # High safety = Core candidate regardless of volatility
                is_core_candidate = True
            elif vol is not None and vol < 25 and score_safety > 50:
                # Low volatility with decent safety
                is_core_candidate = True
            elif lt_score and lt_score > 65:
                # High long-term score
                is_core_candidate = True
            
            if is_core_candidate:
                core_candidates.append(asset_dict)
            elif score_momentum > 60 or score_total > 75:
                # High momentum or high total score = Satellite
                satellite_candidates.append(asset_dict)
            else:
                # Default to satellite for remaining assets
                satellite_candidates.append(asset_dict)

        # Sort by appropriate metrics
        core_candidates.sort(key=lambda x: (
            x.get('lt_score') or x.get('score_safety') or 0), reverse=True)
        satellite_candidates.sort(key=lambda x: (
            x.get('score_momentum') or x.get('score_total') or 0), reverse=True)

        # Take top N
        core_selected = core_candidates[:core_count]
        satellite_selected = satellite_candidates[:satellite_count]

        # Calculate weights
        core_weight = 0.80 if risk_profile == "conservative" else 0.75 if risk_profile == "moderate" else 0.65
        satellite_weight = 1.0 - core_weight

        core_individual_weight = core_weight / \
            len(core_selected) if core_selected else 0
        satellite_individual_weight = satellite_weight / \
            len(satellite_selected) if satellite_selected else 0

        # Build response
        core_assets = [
            BarbellAsset(
                asset_id=a.get('asset_id', a.get('symbol', '')),
                ticker=a.get('symbol', ''),
                name=a.get('name', ''),
                asset_type=a.get('asset_type', 'EQUITY'),
                allocation_type="core",
                weight=round(core_individual_weight, 4),
                score_total=a.get('score_total'),
                lt_score=a.get('lt_score'),
                lt_confidence=a.get('lt_confidence'),
                rationale="Low volatility, high safety score"
            )
            for a in core_selected
        ]

        satellite_assets = [
            BarbellAsset(
                asset_id=a.get('asset_id', a.get('symbol', '')),
                ticker=a.get('symbol', ''),
                name=a.get('name', ''),
                asset_type=a.get('asset_type', 'EQUITY'),
                allocation_type="satellite",
                weight=round(satellite_individual_weight, 4),
                score_total=a.get('score_total'),
                lt_score=a.get('lt_score'),
                lt_confidence=a.get('lt_confidence'),
                rationale="High momentum, growth potential"
            )
            for a in satellite_selected
        ]

        return BarbellSuggestion(
            risk_profile=risk_profile,
            core_assets=core_assets,
            satellite_assets=satellite_assets,
            rationale=f"Barbell portfolio with {int(core_weight*100)}% core / {int(satellite_weight*100)}% satellite allocation based on {risk_profile} risk profile."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating barbell suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/core-candidates")
async def get_core_candidates(
    market_scope: str = Query("US_EU", description="Market scope"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    Get candidate assets for the core (defensive) portion of a barbell portfolio.

    Criteria:
    - High lt_score (institutional quality)
    - High safety score
    - Low volatility
    - Liquid (high ADV)
    """
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore

        store = SQLiteStore()
        assets = store.get_top_scores(market_scope=market_scope, limit=100)

        # Filter for core characteristics
        candidates = []
        for asset_tuple in assets:
            asset_obj, score_obj = asset_tuple

            vol = score_obj.vol_annual or 100
            safety = score_obj.score_safety or 0
            lt_score = getattr(score_obj, 'lt_score', None) or 0

            # Core criteria: low vol OR high safety OR high lt_score
            if (vol and vol < 30) or (safety and safety > 55) or (lt_score and lt_score > 60):
                candidates.append({
                    "asset_id": asset_obj.asset_id,
                    "symbol": asset_obj.symbol,
                    "ticker": asset_obj.symbol,  # ticker = symbol
                    "name": asset_obj.name or asset_obj.symbol,
                    "asset_type": asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type),
                    "score_total": score_obj.score_total,
                    "score_safety": safety,
                    "vol_annual": vol,
                    "lt_score": lt_score,
                    "core_score": (100 - (vol or 50)) * 0.3 + (safety or 50) * 0.4 + (lt_score or 50) * 0.3
                })

        # Sort by core_score
        candidates.sort(key=lambda x: x.get('core_score', 0), reverse=True)

        return {
            "candidates": candidates[:limit],
            "total": len(candidates),
            "market_scope": market_scope
        }

    except Exception as e:
        logger.error(f"Error getting core candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satellite-candidates")
async def get_satellite_candidates(
    market_scope: str = Query("US_EU", description="Market scope"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    Get candidate assets for the satellite (growth) portion of a barbell portfolio.

    Criteria:
    - High momentum score
    - High score_total
    - Acceptable lt_confidence (data quality)
    """
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore

        store = SQLiteStore()
        assets = store.get_top_scores(market_scope=market_scope, limit=100)

        # Filter for satellite characteristics
        candidates = []
        for asset_tuple in assets:
            asset_obj, score_obj = asset_tuple

            momentum = score_obj.score_momentum or 0
            score_total = score_obj.score_total or 0
            lt_confidence = getattr(score_obj, 'lt_confidence', None) or 50

            # Satellite criteria: high momentum
            if momentum and momentum > 50:
                candidates.append({
                    "asset_id": asset_obj.asset_id,
                    "symbol": asset_obj.symbol,
                    "ticker": asset_obj.symbol,  # ticker = symbol
                    "name": asset_obj.name or asset_obj.symbol,
                    "asset_type": asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type),
                    "score_total": score_total,
                    "score_momentum": momentum,
                    "lt_confidence": lt_confidence,
                    "satellite_score": (momentum or 50) * 0.5 + (score_total or 50) * 0.3 + min(lt_confidence or 50, 100) * 0.2
                })

        # Sort by satellite_score
        candidates.sort(key=lambda x: x.get(
            'satellite_score', 0), reverse=True)

        return {
            "candidates": candidates[:limit],
            "total": len(candidates),
            "market_scope": market_scope
        }

    except Exception as e:
        logger.error(f"Error getting satellite candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocation-ratios")
async def get_allocation_ratios():
    """
    Get recommended allocation ratios for different risk profiles.
    """
    return {
        "profiles": [
            {
                "name": "conservative",
                "label": "Conservateur",
                "core_weight": 0.85,
                "satellite_weight": 0.15,
                "description": "Priorité à la préservation du capital"
            },
            {
                "name": "moderate",
                "label": "Modéré",
                "core_weight": 0.75,
                "satellite_weight": 0.25,
                "description": "Équilibre entre sécurité et croissance"
            },
            {
                "name": "aggressive",
                "label": "Dynamique",
                "core_weight": 0.65,
                "satellite_weight": 0.35,
                "description": "Priorité à la croissance avec risque accru"
            }
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENHANCED CANDIDATES ENDPOINTS (with filters & pagination)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/candidates/core")
async def get_core_candidates_v2(
    market_scope: str = Query("US_EU", description="Market scope"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Search ticker/name"),
    min_score_total: Optional[float] = Query(None, ge=0, le=100),
    min_score_safety: Optional[float] = Query(None, ge=0, le=100),
    max_vol_annual: Optional[float] = Query(None, ge=0),
    min_coverage: Optional[float] = Query(None, ge=0, le=100),
    asset_type: Optional[str] = Query(None),
    sort_by: str = Query("core_score", description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
):
    """
    Enhanced core candidates endpoint with filtering and pagination.
    """
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore

        store = SQLiteStore()
        assets = store.get_top_scores(market_scope=market_scope, limit=500)

        candidates = []
        for asset_tuple in assets:
            asset_obj, score_obj = asset_tuple

            vol = score_obj.vol_annual or 100
            safety = score_obj.score_safety or 0
            lt_score = getattr(score_obj, 'lt_score', None) or 0
            coverage = score_obj.confidence or 50
            score_total = score_obj.score_total or 0

            # Apply filters
            if min_score_total and score_total < min_score_total:
                continue
            if min_score_safety and safety < min_score_safety:
                continue
            if max_vol_annual and vol > max_vol_annual:
                continue
            if min_coverage and coverage < min_coverage:
                continue
            if asset_type:
                at = asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type)
                if at.upper() != asset_type.upper():
                    continue

            # Search filter
            ticker = asset_obj.symbol or ""
            name = asset_obj.name or ""
            if q:
                search = q.lower()
                if search not in ticker.lower() and search not in name.lower():
                    continue

            # Core score calculation
            core_score = (100 - min(vol, 100)) * 0.3 + safety * 0.4 + lt_score * 0.3

            # Determine warnings
            warnings = []
            if vol > 40:
                warnings.append("high_volatility")
            if coverage < 70:
                warnings.append("low_coverage")
            if safety < 50:
                warnings.append("low_safety")

            candidates.append({
                "asset_id": asset_obj.asset_id,
                "ticker": ticker,
                "name": name,
                "asset_type": asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type),
                "score_total": round(score_total, 1),
                "score_safety": round(safety, 1),
                "score_momentum": round(score_obj.score_momentum or 0, 1),
                "score_value": round(score_obj.score_value or 0, 1),
                "vol_annual": round(vol, 1),
                "coverage": round(coverage, 1),
                "lt_score": round(lt_score, 1) if lt_score else None,
                "core_score": round(core_score, 1),
                "eligible": len(warnings) == 0,
                "warnings": warnings,
            })

        # Sort
        reverse = sort_order.lower() == "desc"
        candidates.sort(key=lambda x: x.get(sort_by, 0) or 0, reverse=reverse)

        # Pagination
        total = len(candidates)
        paginated = candidates[offset:offset + limit]

        return {
            "candidates": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "market_scope": market_scope,
            "filters_applied": {
                "q": q,
                "min_score_total": min_score_total,
                "min_score_safety": min_score_safety,
                "max_vol_annual": max_vol_annual,
            }
        }

    except Exception as e:
        logger.error(f"Error getting core candidates v2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/satellite")
async def get_satellite_candidates_v2(
    market_scope: str = Query("US_EU", description="Market scope"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Search ticker/name"),
    min_score_total: Optional[float] = Query(None, ge=0, le=100),
    min_score_momentum: Optional[float] = Query(None, ge=0, le=100),
    min_coverage: Optional[float] = Query(None, ge=0, le=100),
    asset_type: Optional[str] = Query(None),
    sort_by: str = Query("satellite_score", description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
):
    """
    Enhanced satellite candidates endpoint with filtering and pagination.
    """
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore

        store = SQLiteStore()
        assets = store.get_top_scores(market_scope=market_scope, limit=500)

        candidates = []
        for asset_tuple in assets:
            asset_obj, score_obj = asset_tuple

            momentum = score_obj.score_momentum or 0
            score_total = score_obj.score_total or 0
            coverage = score_obj.confidence or 50
            lt_confidence = getattr(score_obj, 'lt_confidence', None) or 50
            vol = score_obj.vol_annual or 50

            # Apply filters
            if min_score_total and score_total < min_score_total:
                continue
            if min_score_momentum and momentum < min_score_momentum:
                continue
            if min_coverage and coverage < min_coverage:
                continue
            if asset_type:
                at = asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type)
                if at.upper() != asset_type.upper():
                    continue

            # Search filter
            ticker = asset_obj.symbol or ""
            name = asset_obj.name or ""
            if q:
                search = q.lower()
                if search not in ticker.lower() and search not in name.lower():
                    continue

            # Satellite score
            satellite_score = momentum * 0.5 + score_total * 0.3 + min(lt_confidence, 100) * 0.2

            # Warnings
            warnings = []
            if coverage < 70:
                warnings.append("low_coverage")
            if momentum < 50:
                warnings.append("low_momentum")

            candidates.append({
                "asset_id": asset_obj.asset_id,
                "ticker": ticker,
                "name": name,
                "asset_type": asset_obj.asset_type.value if hasattr(asset_obj.asset_type, 'value') else str(asset_obj.asset_type),
                "score_total": round(score_total, 1),
                "score_momentum": round(momentum, 1),
                "score_safety": round(score_obj.score_safety or 0, 1),
                "score_value": round(score_obj.score_value or 0, 1),
                "vol_annual": round(vol, 1),
                "coverage": round(coverage, 1),
                "satellite_score": round(satellite_score, 1),
                "eligible": len(warnings) == 0,
                "warnings": warnings,
            })

        # Sort
        reverse = sort_order.lower() == "desc"
        candidates.sort(key=lambda x: x.get(sort_by, 0) or 0, reverse=reverse)

        # Pagination
        total = len(candidates)
        paginated = candidates[offset:offset + limit]

        return {
            "candidates": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "market_scope": market_scope,
        }

    except Exception as e:
        logger.error(f"Error getting satellite candidates v2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATION ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

class SimulationRequest(BaseModel):
    """Request body for portfolio simulation."""
    compositions: List[Dict[str, Any]]  # [{asset_id, weight, block}]
    period_years: int = 10
    rebalance_frequency: str = "yearly"  # monthly, quarterly, yearly
    initial_capital: float = 10000
    market_scope: str = "US_EU"


class SimulationResult(BaseModel):
    """Simulation result."""
    cagr: Optional[float] = None
    volatility: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None
    final_value: Optional[float] = None
    equity_curve: List[Dict[str, Any]] = []
    yearly_table: List[Dict[str, Any]] = []
    best_year: Optional[Dict[str, Any]] = None
    worst_year: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    data_quality_score: Optional[float] = None
    assets_included: int = 0
    assets_excluded: int = 0
    error: Optional[str] = None
    executed_at: Optional[str] = None


@router.post("/simulate", response_model=SimulationResult)
async def simulate_barbell_portfolio(request: SimulationRequest):
    """
    Run backtest simulation on a barbell portfolio.
    
    Uses Parquet OHLCV data for historical returns.
    Caches results for repeated queries.
    """
    try:
        from barbell_service import get_simulator
        
        simulator = get_simulator()
        
        # Validate compositions
        if not request.compositions:
            raise HTTPException(status_code=400, detail="No compositions provided")
            
        total_weight = sum(c.get('weight', 0) for c in request.compositions)
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400, 
                detail=f"Total weight must be 100% (got {total_weight*100:.1f}%)"
            )
            
        if request.period_years not in [5, 10, 20]:
            raise HTTPException(status_code=400, detail="Period must be 5, 10, or 20 years")
            
        if request.rebalance_frequency not in ["monthly", "quarterly", "yearly"]:
            raise HTTPException(status_code=400, detail="Invalid rebalance frequency")
        
        # Run simulation
        result = simulator.simulate_portfolio(
            compositions=request.compositions,
            period_years=request.period_years,
            rebalance_frequency=request.rebalance_frequency,
            initial_capital=request.initial_capital,
            market_scope=request.market_scope
        )
        
        return SimulationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return SimulationResult(
            error=str(e),
            warnings=[str(e)],
            executed_at=datetime.now().isoformat()
        )


# ═══════════════════════════════════════════════════════════════════════════
# PORTFOLIO PERSISTENCE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

class PortfolioCreate(BaseModel):
    """Create portfolio request."""
    name: str
    description: Optional[str] = None
    risk_profile: str = "moderate"
    market_scope: str = "US_EU"
    core_ratio: float = 0.75
    satellite_ratio: float = 0.25
    items: List[Dict[str, Any]] = []  # [{asset_id, block, weight}]


class PortfolioUpdate(BaseModel):
    """Update portfolio request."""
    name: Optional[str] = None
    description: Optional[str] = None
    risk_profile: Optional[str] = None
    core_ratio: Optional[float] = None
    satellite_ratio: Optional[float] = None
    items: Optional[List[Dict[str, Any]]] = None


@router.get("/portfolios")
async def list_portfolios(
    user_id: str = Query("default_user", description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List user's saved barbell portfolios."""
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Check if table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='barbell_portfolios'"
            ).fetchone()
            
            if not table_check:
                return {"portfolios": [], "total": 0}
            
            # Count total
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM barbell_portfolios WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
            total = count_row["cnt"] if count_row else 0
            
            # Fetch portfolios
            rows = conn.execute("""
                SELECT * FROM barbell_portfolios 
                WHERE user_id = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset)).fetchall()
            
            portfolios = []
            for row in rows:
                row_dict = dict(row)
                
                # Fetch items for this portfolio
                items = conn.execute("""
                    SELECT * FROM barbell_portfolio_items 
                    WHERE portfolio_id = ?
                    ORDER BY block, weight DESC
                """, (row_dict["id"],)).fetchall()
                
                row_dict["items"] = [dict(item) for item in items]
                portfolios.append(row_dict)
            
            return {
                "portfolios": portfolios,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"Error listing portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolios")
async def create_portfolio(
    portfolio: PortfolioCreate,
    user_id: str = Query("default_user", description="User ID"),
):
    """Create a new barbell portfolio."""
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore
        import uuid
        
        store = SQLiteStore()
        portfolio_id = str(uuid.uuid4())[:16]
        
        with store._get_connection() as conn:
            # Ensure table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS barbell_portfolios (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    risk_profile TEXT DEFAULT 'moderate',
                    market_scope TEXT DEFAULT 'US_EU',
                    core_ratio REAL DEFAULT 0.75,
                    satellite_ratio REAL DEFAULT 0.25,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    is_active INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS barbell_portfolio_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    block TEXT NOT NULL,
                    weight REAL NOT NULL,
                    notes TEXT,
                    added_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(portfolio_id, asset_id)
                )
            """)
            
            # Insert portfolio
            conn.execute("""
                INSERT INTO barbell_portfolios 
                (id, user_id, name, description, risk_profile, market_scope, core_ratio, satellite_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                portfolio_id,
                user_id,
                portfolio.name,
                portfolio.description,
                portfolio.risk_profile,
                portfolio.market_scope,
                portfolio.core_ratio,
                portfolio.satellite_ratio
            ))
            
            # Insert items
            for item in portfolio.items:
                conn.execute("""
                    INSERT INTO barbell_portfolio_items (portfolio_id, asset_id, block, weight)
                    VALUES (?, ?, ?, ?)
                """, (
                    portfolio_id,
                    item.get("asset_id"),
                    item.get("block", "core"),
                    item.get("weight", 0)
                ))
        
        return {
            "id": portfolio_id,
            "message": "Portfolio created successfully",
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """Get a specific portfolio with its items."""
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM barbell_portfolios WHERE id = ?",
                (portfolio_id,)
            ).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            portfolio = dict(row)
            
            # Fetch items
            items = conn.execute("""
                SELECT bpi.*, u.symbol as ticker, u.name as asset_name
                FROM barbell_portfolio_items bpi
                LEFT JOIN universe u ON bpi.asset_id = u.asset_id
                WHERE bpi.portfolio_id = ?
                ORDER BY bpi.block, bpi.weight DESC
            """, (portfolio_id,)).fetchall()
            
            portfolio["items"] = [dict(item) for item in items]
            
            return portfolio
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/portfolios/{portfolio_id}")
async def update_portfolio(portfolio_id: str, update: PortfolioUpdate):
    """Update an existing portfolio."""
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Check exists
            existing = conn.execute(
                "SELECT id FROM barbell_portfolios WHERE id = ?",
                (portfolio_id,)
            ).fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Build update query
            updates = []
            params = []
            
            if update.name is not None:
                updates.append("name = ?")
                params.append(update.name)
            if update.description is not None:
                updates.append("description = ?")
                params.append(update.description)
            if update.risk_profile is not None:
                updates.append("risk_profile = ?")
                params.append(update.risk_profile)
            if update.core_ratio is not None:
                updates.append("core_ratio = ?")
                params.append(update.core_ratio)
            if update.satellite_ratio is not None:
                updates.append("satellite_ratio = ?")
                params.append(update.satellite_ratio)
            
            updates.append("updated_at = datetime('now')")
            
            if updates:
                params.append(portfolio_id)
                conn.execute(
                    f"UPDATE barbell_portfolios SET {', '.join(updates)} WHERE id = ?",
                    params
                )
            
            # Update items if provided
            if update.items is not None:
                # Clear existing items
                conn.execute(
                    "DELETE FROM barbell_portfolio_items WHERE portfolio_id = ?",
                    (portfolio_id,)
                )
                
                # Insert new items
                for item in update.items:
                    conn.execute("""
                        INSERT INTO barbell_portfolio_items (portfolio_id, asset_id, block, weight)
                        VALUES (?, ?, ?, ?)
                    """, (
                        portfolio_id,
                        item.get("asset_id"),
                        item.get("block", "core"),
                        item.get("weight", 0)
                    ))
        
        return {
            "id": portfolio_id,
            "message": "Portfolio updated successfully",
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Soft delete a portfolio."""
    try:
        import sys
        sys.path.insert(0, '..')
        from storage.sqlite_store import SQLiteStore
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            result = conn.execute(
                "UPDATE barbell_portfolios SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (portfolio_id,)
            )
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return {"message": "Portfolio deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
