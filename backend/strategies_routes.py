"""
MarketGPS - Strategies Module (Institutional Templates + Builder + Backtest)

This is an ADD-ON module that does not modify existing functionality.
Provides:
- Institutional strategy templates (Barbell, Permanent, Core-Satellite, etc.)
- User strategy customization and persistence
- Backtest/simulation engine with performance metrics
- Strategy Fit Score calculation for eligible instruments

SCOPE: US_EU only (Africa support can be added later)
"""

import os
import sys
import json
import hashlib
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel, Field, validator

# Add parent to path for storage imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["Strategies"])


# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class BlockDefinition(BaseModel):
    """Strategy block definition."""
    name: str
    label: str
    weight: float
    description: str
    eligibility: Optional[Dict[str, Any]] = None


class StrategyTemplate(BaseModel):
    """Strategy template response."""
    id: int
    slug: str
    name: str
    description: Optional[str] = None
    category: str = "balanced"
    risk_level: str = "moderate"
    horizon_years: int = 10
    rebalance_frequency: str = "annual"
    structure: Dict[str, Any]
    scope: str = "US_EU"
    created_at: Optional[str] = None


class InstrumentComposition(BaseModel):
    """Instrument in a strategy composition."""
    ticker: str
    block_name: str
    weight: float = Field(ge=0, le=1)
    fit_score: Optional[float] = None
    rationale: Optional[str] = None


class EligibleInstrument(BaseModel):
    """Eligible instrument for a strategy block."""
    ticker: str
    name: str
    asset_type: str
    fit_score: float
    global_score: Optional[float] = None
    lt_score: Optional[float] = None
    liquidity_badge: str = "good"
    data_quality_badge: str = "good"
    fit_breakdown: Optional[Dict[str, Any]] = None


class UserStrategy(BaseModel):
    """User's custom strategy."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    template_id: Optional[int] = None
    template_slug: Optional[str] = None
    compositions: List[InstrumentComposition] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SimulationRequest(BaseModel):
    """Request for portfolio simulation."""
    compositions: List[InstrumentComposition]
    period_years: int = Field(default=10, ge=1, le=30)
    initial_value: float = Field(default=10000, ge=100)
    rebalance_frequency: str = Field(default="annual")
    
    @validator('compositions')
    def validate_weights(cls, v):
        total = sum(c.weight for c in v)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Total weights must sum to 1.0, got {total:.4f}")
        return v
    
    @validator('rebalance_frequency')
    def validate_rebalance(cls, v):
        valid = ["monthly", "quarterly", "annual"]
        if v not in valid:
            raise ValueError(f"Invalid rebalance frequency. Use: {valid}")
        return v


class SimulationResult(BaseModel):
    """Simulation/backtest result."""
    cagr: Optional[float] = None
    volatility: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    final_value: Optional[float] = None
    total_return: Optional[float] = None
    series: Optional[List[Dict[str, Any]]] = None  # Monthly downsampled
    data_quality_score: Optional[float] = None
    warnings: List[str] = []
    composition_hash: Optional[str] = None
    executed_at: Optional[str] = None


class SaveStrategyRequest(BaseModel):
    """Request to save a user strategy."""
    name: str
    description: Optional[str] = None
    template_id: Optional[int] = None
    compositions: List[InstrumentComposition]


# ═══════════════════════════════════════════════════════════════════════════
# STRATEGY FIT SCORE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════

class StrategyFitScorer:
    """
    Calculate Strategy Fit Score for instruments based on block type.
    
    This is DIFFERENT from the global score and is contextual to each strategy block.
    For example:
    - "Ultra-Safe" block: prioritizes low volatility, low drawdown
    - "Crisis Alpha" block: prioritizes convexity, crisis performance
    - "Growth" block: prioritizes momentum, equity beta
    """
    
    @staticmethod
    def score_ultra_safe(asset_data: Dict) -> Tuple[float, Dict]:
        """Score for ultra-safe/defensive block (T-bills, short treasuries)."""
        score = 50.0  # Base
        breakdown = {}
        
        # Low volatility is good
        vol = asset_data.get('vol_annual') or 20
        vol_score = max(0, 100 - vol * 3)  # Lower vol = higher score
        breakdown['volatility'] = vol_score
        score = score * 0.3 + vol_score * 0.7
        
        # Low drawdown is good
        mdd = abs(asset_data.get('max_drawdown') or 10)
        dd_score = max(0, 100 - mdd * 4)
        breakdown['drawdown'] = dd_score
        score = score * 0.6 + dd_score * 0.4
        
        # High confidence/coverage is good
        coverage = (asset_data.get('coverage') or 0.7) * 100
        breakdown['data_quality'] = coverage
        score = score * 0.9 + coverage * 0.1
        
        return min(100, max(0, score)), breakdown
    
    @staticmethod
    def score_crisis_alpha(asset_data: Dict) -> Tuple[float, Dict]:
        """Score for crisis alpha/convex block."""
        score = 50.0
        breakdown = {}
        
        # High volatility can be acceptable if it's convex
        vol = asset_data.get('vol_annual') or 20
        vol_score = min(100, vol * 2)  # Some volatility expected
        breakdown['volatility_tolerance'] = vol_score
        
        # Momentum in crisis-type assets
        momentum = asset_data.get('score_momentum') or 50
        breakdown['momentum'] = momentum
        
        # Combine
        score = vol_score * 0.3 + momentum * 0.4 + 50 * 0.3
        
        return min(100, max(0, score)), breakdown
    
    @staticmethod
    def score_growth(asset_data: Dict) -> Tuple[float, Dict]:
        """Score for growth/equity block."""
        score = 50.0
        breakdown = {}
        
        # Use existing scores if available
        total = asset_data.get('score_total') or 50
        momentum = asset_data.get('score_momentum') or 50
        lt_score = asset_data.get('lt_score') or total
        
        breakdown['global_score'] = total
        breakdown['momentum'] = momentum
        breakdown['lt_score'] = lt_score
        
        score = total * 0.3 + momentum * 0.3 + lt_score * 0.4
        
        return min(100, max(0, score)), breakdown
    
    @staticmethod
    def score_inflation_hedge(asset_data: Dict) -> Tuple[float, Dict]:
        """Score for inflation hedge block (gold, commodities)."""
        score = 50.0
        breakdown = {}
        
        # Moderate volatility acceptable
        vol = asset_data.get('vol_annual') or 15
        vol_score = 100 if 10 <= vol <= 25 else max(0, 100 - abs(vol - 17) * 3)
        breakdown['volatility'] = vol_score
        
        # Stability
        safety = asset_data.get('score_safety') or 50
        breakdown['safety'] = safety
        
        score = vol_score * 0.4 + safety * 0.6
        
        return min(100, max(0, score)), breakdown
    
    @staticmethod
    def score_core(asset_data: Dict) -> Tuple[float, Dict]:
        """Score for core holdings (diversified ETFs)."""
        score = 50.0
        breakdown = {}
        
        # Balance of all factors
        total = asset_data.get('score_total') or 50
        safety = asset_data.get('score_safety') or 50
        lt_score = asset_data.get('lt_score')
        
        breakdown['global_score'] = total
        breakdown['safety'] = safety
        
        if lt_score:
            breakdown['lt_score'] = lt_score
            score = total * 0.3 + safety * 0.3 + lt_score * 0.4
        else:
            score = total * 0.5 + safety * 0.5
        
        return min(100, max(0, score)), breakdown
    
    @staticmethod
    def score_satellite(asset_data: Dict) -> Tuple[float, Dict]:
        """Score for satellite holdings (thematic, factor, tactical)."""
        score = 50.0
        breakdown = {}
        
        # Emphasize momentum and total score
        total = asset_data.get('score_total') or 50
        momentum = asset_data.get('score_momentum') or 50
        
        breakdown['global_score'] = total
        breakdown['momentum'] = momentum
        
        score = total * 0.4 + momentum * 0.6
        
        return min(100, max(0, score)), breakdown
    
    @classmethod
    def calculate(cls, block_type: str, asset_data: Dict) -> Tuple[float, Dict]:
        """Calculate fit score based on block type."""
        scorers = {
            'ultra_safe': cls.score_ultra_safe,
            'defensive': cls.score_ultra_safe,
            'crisis_alpha': cls.score_crisis_alpha,
            'convex': cls.score_crisis_alpha,
            'growth': cls.score_growth,
            'inflation': cls.score_inflation_hedge,
            'inflation_hedge': cls.score_inflation_hedge,
            'core': cls.score_core,
            'core_equity': cls.score_core,
            'core_bond': cls.score_core,
            'satellite': cls.score_satellite,
            'liquidity': cls.score_ultra_safe,
            'deflation': cls.score_core,
            'dividend': cls.score_growth,
            'dividend_core': cls.score_growth,
            'value': cls.score_growth,
            'momentum': cls.score_satellite,
            'quality': cls.score_core,
            'low_vol': cls.score_ultra_safe,
        }
        
        scorer = scorers.get(block_type.lower(), cls.score_core)
        return scorer(asset_data)


# ═══════════════════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class BacktestEngine:
    """
    Simple backtest engine for portfolio simulation.
    
    MVP Features:
    - Annual rebalancing
    - Uses adjusted close prices from Parquet
    - Calculates CAGR, volatility, Sharpe, max drawdown
    - Downsamples to monthly for storage
    
    Limitations:
    - No transaction costs
    - No taxes
    - Risk-free rate = 0 for Sharpe
    """
    
    def __init__(self):
        self.parquet_base = Path(__file__).parent.parent / "data" / "parquet" / "ohlcv"
        
    def _load_price_data(self, ticker: str, years: int) -> Optional[Dict]:
        """Load price data for a ticker."""
        try:
            import pandas as pd
            
            # Try multiple parquet paths
            paths_to_try = [
                self.parquet_base / f"{ticker}.parquet",
                self.parquet_base / "us_eu" / f"{ticker}.parquet",
                Path(__file__).parent.parent / "data" / "parquet" / "us_eu" / f"{ticker}.parquet",
            ]
            
            df = None
            for path in paths_to_try:
                if path.exists():
                    df = pd.read_parquet(path)
                    break
            
            if df is None:
                logger.warning(f"No price data found for {ticker}")
                return None
            
            # Ensure datetime index
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Filter to period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            df = df[df.index >= start_date]
            
            # Use adjusted close if available, else close
            price_col = 'adj_close' if 'adj_close' in df.columns else 'close'
            if price_col not in df.columns:
                logger.warning(f"No close price column for {ticker}")
                return None
            
            return {
                'prices': df[price_col].dropna(),
                'coverage': len(df) / (years * 252)  # Approximate trading days
            }
            
        except Exception as e:
            logger.warning(f"Failed to load {ticker}: {e}")
            return None
    
    def run_simulation(self, request: SimulationRequest) -> SimulationResult:
        """Run portfolio simulation."""
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return SimulationResult(
                warnings=["pandas/numpy not available for simulation"]
            )
        
        warnings = []
        compositions = request.compositions
        period = request.period_years
        initial = request.initial_value
        
        # Load all price data
        price_data = {}
        missing_tickers = []
        
        for comp in compositions:
            data = self._load_price_data(comp.ticker, period)
            if data:
                price_data[comp.ticker] = data
            else:
                missing_tickers.append(comp.ticker)
        
        if missing_tickers:
            warnings.append(f"Missing data for: {', '.join(missing_tickers)}")
        
        if len(price_data) < len(compositions) * 0.5:
            return SimulationResult(
                warnings=warnings + ["Insufficient data for simulation (< 50% coverage)"],
                data_quality_score=len(price_data) / len(compositions) * 100
            )
        
        # Align all price series to common dates
        all_prices = pd.DataFrame({
            ticker: data['prices'] for ticker, data in price_data.items()
        })
        all_prices = all_prices.dropna()
        
        if len(all_prices) < 252:  # Less than 1 year of data
            return SimulationResult(
                warnings=warnings + ["Less than 1 year of aligned data"],
                data_quality_score=min(100, len(all_prices) / 252 * 100)
            )
        
        # Calculate portfolio returns with rebalancing
        # Normalize weights for available tickers
        available_weights = {}
        total_avail = 0
        for comp in compositions:
            if comp.ticker in price_data:
                available_weights[comp.ticker] = comp.weight
                total_avail += comp.weight
        
        # Renormalize
        if total_avail < 0.99:
            warnings.append(f"Only {total_avail*100:.1f}% of allocation available")
            for ticker in available_weights:
                available_weights[ticker] /= total_avail
        
        # Daily returns
        returns = all_prices.pct_change().dropna()
        
        # Apply weights (simplified - no actual rebalancing in MVP)
        weights = pd.Series(available_weights)
        portfolio_returns = (returns[list(available_weights.keys())] * weights).sum(axis=1)
        
        # Calculate metrics
        cumulative = (1 + portfolio_returns).cumprod()
        final_value = initial * cumulative.iloc[-1] if len(cumulative) > 0 else initial
        
        # CAGR
        n_years = len(portfolio_returns) / 252
        cagr = ((final_value / initial) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
        
        # Volatility (annualized)
        volatility = portfolio_returns.std() * np.sqrt(252) * 100
        
        # Sharpe (assuming 0 risk-free rate)
        sharpe = (portfolio_returns.mean() * 252) / (portfolio_returns.std() * np.sqrt(252)) if portfolio_returns.std() > 0 else 0
        
        # Max Drawdown
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Downsample to monthly for storage
        monthly_values = cumulative.resample('ME').last() * initial
        series = [
            {"date": idx.strftime("%Y-%m-%d"), "value": round(val, 2)}
            for idx, val in monthly_values.items()
        ]
        
        # Composition hash for caching
        comp_str = json.dumps([{"t": c.ticker, "w": c.weight} for c in compositions], sort_keys=True)
        comp_hash = hashlib.md5(comp_str.encode()).hexdigest()[:12]
        
        # Data quality score
        coverage_avg = sum(d['coverage'] for d in price_data.values()) / len(price_data)
        data_quality = min(100, coverage_avg * 100)
        
        return SimulationResult(
            cagr=round(cagr, 2),
            volatility=round(volatility, 2),
            sharpe=round(sharpe, 2),
            max_drawdown=round(max_drawdown, 2),
            final_value=round(final_value, 2),
            total_return=round((final_value / initial - 1) * 100, 2),
            series=series,
            data_quality_score=round(data_quality, 1),
            warnings=warnings,
            composition_hash=comp_hash,
            executed_at=datetime.now().isoformat()
        )


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Health check for strategies module."""
    return {
        "status": "healthy",
        "module": "strategies",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/templates", response_model=List[StrategyTemplate])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level")
):
    """
    List all available strategy templates.
    
    Categories: defensive, balanced, growth, tactical
    Risk levels: low, moderate, high
    """
    try:
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            conditions = []
            params = []
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            if risk_level:
                conditions.append("risk_level = ?")
                params.append(risk_level)
            
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            rows = conn.execute(f"""
                SELECT * FROM strategy_templates
                {where}
                ORDER BY 
                    CASE category 
                        WHEN 'defensive' THEN 1 
                        WHEN 'balanced' THEN 2 
                        WHEN 'growth' THEN 3 
                        ELSE 4 
                    END,
                    name
            """, params).fetchall()
            
            templates = []
            for row in rows:
                template = dict(row)
                try:
                    template['structure'] = json.loads(template.get('structure_json', '{}'))
                except:
                    template['structure'] = {}
                templates.append(StrategyTemplate(**template))
            
            return templates
            
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{slug}", response_model=StrategyTemplate)
async def get_template(slug: str):
    """Get a specific strategy template by slug."""
    try:
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM strategy_templates WHERE slug = ?",
                (slug,)
            ).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Template not found")
            
            template = dict(row)
            try:
                template['structure'] = json.loads(template.get('structure_json', '{}'))
            except:
                template['structure'] = {}
            
            return StrategyTemplate(**template)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{slug}/compositions")
async def get_template_compositions(slug: str):
    """Get default instrument compositions for a template."""
    try:
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Get template ID
            template = conn.execute(
                "SELECT id FROM strategy_templates WHERE slug = ?",
                (slug,)
            ).fetchone()
            
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Get compositions
            rows = conn.execute("""
                SELECT * FROM strategy_template_compositions
                WHERE template_id = ?
                ORDER BY block_name, weight DESC
            """, (template['id'],)).fetchall()
            
            return {
                "template_slug": slug,
                "compositions": [dict(row) for row in rows]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compositions for {slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eligible-instruments", response_model=Dict[str, Any])
async def get_eligible_instruments(
    block_type: str = Query(..., description="Block type (ultra_safe, growth, core, satellite, etc.)"),
    strategy_slug: Optional[str] = Query(None, description="Strategy slug for context"),
    limit: int = Query(100, ge=5, le=500),
    include_unscored: bool = Query(False, description="Include unscored assets with estimated fit")
):
    """
    Get eligible instruments for a specific strategy block.
    
    Returns instruments with their Strategy Fit Score for this block.
    This score is DIFFERENT from the global score.
    
    Relaxed criteria to ensure at least 100 instruments are returned.
    """
    try:
        store = SQLiteStore()
        
        # Get assets - include unscored if needed
        scored_filter = None if include_unscored else "scored"
        
        # Get more assets to have a good pool
        assets, total = store.list_assets_paginated(
            market_scope="US_EU",
            scored_filter=scored_filter,
            eligible_only=False,
            page=1,
            page_size=min(limit * 5, 2000),  # Get 5x more to filter
            sort_by="score_total",
            sort_desc=True
        )
        
        eligible = []
        scorer = StrategyFitScorer()
        
        # Define eligibility criteria per block type - RELAXED for better coverage
        eligibility_criteria = {
            'ultra_safe': {'max_vol': 25, 'min_safety': 45, 'max_drawdown': 25},  # Relaxed
            'defensive': {'max_vol': 35, 'min_safety': 35, 'max_drawdown': 30},   # Relaxed
            'core': {'max_vol': 50, 'min_score': 20, 'min_coverage': 0.3},        # Relaxed
            'core_equity': {'max_vol': 50, 'min_score': 20},                       # Relaxed
            'core_bond': {'max_vol': 25, 'min_safety': 30},                        # Relaxed
            'satellite': {'min_momentum': 20, 'min_score': 15},                    # Relaxed
            'growth': {'min_momentum': 30, 'min_score': 20},                       # Relaxed
            'crisis_alpha': {'min_coverage': 0.2},                                 # Relaxed
            'inflation_hedge': {'max_vol': 60, 'min_coverage': 0.2},               # Relaxed
        }
        
        # If criteria not found, use very permissive defaults
        criteria = eligibility_criteria.get(block_type.lower(), {})
        
        for asset in assets:
            # Apply eligibility filters (relaxed)
            vol = asset.get('vol_annual') or 30  # Default to moderate
            safety = asset.get('score_safety') or 50  # Default to neutral
            momentum = asset.get('score_momentum') or 50
            score = asset.get('score_total') or 40  # Default to neutral
            coverage = asset.get('coverage') or 0.5
            drawdown = abs(asset.get('max_drawdown') or 20)
            
            # Skip only if FAR outside criteria
            skip = False
            if criteria.get('max_vol') and vol > criteria['max_vol'] * 1.5:  # 50% tolerance
                skip = True
            if criteria.get('min_safety') and safety < criteria['min_safety'] * 0.5:  # 50% tolerance
                skip = True
            if criteria.get('min_momentum') and momentum < criteria['min_momentum'] * 0.5:
                skip = True
            if criteria.get('min_score') and score < criteria['min_score'] * 0.5:
                skip = True
            if criteria.get('max_drawdown') and drawdown > criteria['max_drawdown'] * 2:
                skip = True
            
            if skip:
                continue
            
            # Calculate fit score for this block
            fit_score, breakdown = scorer.calculate(block_type, asset)
            
            # Penalize if doesn't meet criteria perfectly
            if criteria.get('max_vol') and vol > criteria['max_vol']:
                fit_score *= 0.9
            if criteria.get('min_safety') and safety < criteria['min_safety']:
                fit_score *= 0.9
            if criteria.get('min_momentum') and momentum < criteria['min_momentum']:
                fit_score *= 0.9
            if criteria.get('min_score') and score < criteria['min_score']:
                fit_score *= 0.85
            
            # Determine badges
            liquidity = asset.get('data_confidence') or asset.get('liquidity') or 0.7
            liquidity_badge = "good" if liquidity > 0.6 else "medium" if liquidity > 0.3 else "low"
            
            coverage_val = asset.get('coverage') or 0.8
            data_badge = "good" if coverage_val > 0.8 else "medium" if coverage_val > 0.5 else "low"
            
            eligible.append(EligibleInstrument(
                ticker=asset.get('symbol', ''),
                name=asset.get('name', ''),
                asset_type=asset.get('asset_type', 'EQUITY'),
                fit_score=round(fit_score, 1),
                global_score=asset.get('score_total'),
                lt_score=asset.get('lt_score'),
                liquidity_badge=liquidity_badge,
                data_quality_badge=data_badge,
                fit_breakdown=breakdown
            ))
        
        # Sort by fit score and limit
        eligible.sort(key=lambda x: x.fit_score, reverse=True)
        eligible = eligible[:limit]
        
        return {
            "block_type": block_type,
            "strategy_slug": strategy_slug,
            "instruments": [e.dict() for e in eligible],
            "total": len(eligible)
        }
        
    except Exception as e:
        logger.error(f"Error getting eligible instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate", response_model=SimulationResult)
async def simulate_portfolio(request: SimulationRequest):
    """
    Run a backtest/simulation on a portfolio composition.
    
    Calculates:
    - CAGR (Compound Annual Growth Rate)
    - Volatility (annualized)
    - Sharpe Ratio (risk-free = 0)
    - Max Drawdown
    
    Returns monthly downsampled series for charting.
    """
    try:
        # Validate US_EU scope for all tickers
        store = SQLiteStore()
        
        for comp in request.compositions:
            # Quick check that ticker exists in US_EU
            with store._get_connection() as conn:
                row = conn.execute("""
                    SELECT 1 FROM universe 
                    WHERE symbol = ? AND market_scope = 'US_EU' AND active = 1
                """, (comp.ticker,)).fetchone()
                
                # For MVP, we'll be lenient about missing tickers
                # as some may be ETFs not in our universe
        
        # Run simulation
        engine = BacktestEngine()
        result = engine.run_simulation(request)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")


@router.get("/user", response_model=List[UserStrategy])
async def list_user_strategies(
    user_id: str = Query("default", description="User ID")
):
    """List user's saved strategies."""
    try:
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            rows = conn.execute("""
                SELECT us.*, st.slug as template_slug
                FROM user_strategies us
                LEFT JOIN strategy_templates st ON us.template_id = st.id
                WHERE us.user_id = ?
                ORDER BY us.updated_at DESC
            """, (user_id,)).fetchall()
            
            strategies = []
            for row in rows:
                strategy = dict(row)
                
                # Get compositions
                comps = conn.execute("""
                    SELECT instrument_ticker as ticker, block_name, weight, fit_score
                    FROM user_strategy_compositions
                    WHERE user_strategy_id = ?
                """, (strategy['id'],)).fetchall()
                
                strategy['compositions'] = [
                    InstrumentComposition(
                        ticker=c['ticker'],
                        block_name=c['block_name'],
                        weight=c['weight'],
                        fit_score=c['fit_score']
                    )
                    for c in comps
                ]
                
                strategies.append(UserStrategy(**strategy))
            
            return strategies
            
    except Exception as e:
        logger.error(f"Error listing user strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user", response_model=UserStrategy)
async def save_user_strategy(
    request: SaveStrategyRequest,
    user_id: str = Query("default", description="User ID")
):
    """Save or update a user strategy."""
    try:
        # Validate weights
        total_weight = sum(c.weight for c in request.compositions)
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400, 
                detail=f"Weights must sum to 1.0, got {total_weight:.4f}"
            )
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Insert strategy
            cursor = conn.execute("""
                INSERT INTO user_strategies (user_id, template_id, name, description, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (user_id, request.template_id, request.name, request.description))
            
            strategy_id = cursor.lastrowid
            
            # Insert compositions
            for comp in request.compositions:
                conn.execute("""
                    INSERT INTO user_strategy_compositions 
                        (user_strategy_id, instrument_ticker, block_name, weight, fit_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    strategy_id, comp.ticker, comp.block_name, 
                    comp.weight, comp.fit_score
                ))
            
            return UserStrategy(
                id=strategy_id,
                name=request.name,
                description=request.description,
                template_id=request.template_id,
                compositions=request.compositions,
                created_at=datetime.now().isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving user strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{strategy_id}", response_model=UserStrategy)
async def get_user_strategy(
    strategy_id: int,
    user_id: str = Query("default", description="User ID")
):
    """Get a specific user strategy."""
    try:
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            row = conn.execute("""
                SELECT us.*, st.slug as template_slug
                FROM user_strategies us
                LEFT JOIN strategy_templates st ON us.template_id = st.id
                WHERE us.id = ? AND us.user_id = ?
            """, (strategy_id, user_id)).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            strategy = dict(row)
            
            # Get compositions
            comps = conn.execute("""
                SELECT instrument_ticker as ticker, block_name, weight, fit_score
                FROM user_strategy_compositions
                WHERE user_strategy_id = ?
            """, (strategy_id,)).fetchall()
            
            strategy['compositions'] = [
                InstrumentComposition(
                    ticker=c['ticker'],
                    block_name=c['block_name'],
                    weight=c['weight'],
                    fit_score=c['fit_score']
                )
                for c in comps
            ]
            
            return UserStrategy(**strategy)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/user/{strategy_id}", response_model=UserStrategy)
async def update_user_strategy(
    strategy_id: int,
    request: SaveStrategyRequest,
    user_id: str = Query("default", description="User ID")
):
    """Update an existing user strategy."""
    try:
        # Validate weights
        total_weight = sum(c.weight for c in request.compositions)
        if abs(total_weight - 1.0) > 0.02:
            raise HTTPException(
                status_code=400, 
                detail=f"Weights must sum to 1.0, got {total_weight:.4f}"
            )
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Check ownership
            row = conn.execute("""
                SELECT 1 FROM user_strategies WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id)).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Update strategy info
            conn.execute("""
                UPDATE user_strategies 
                SET name = ?, description = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (request.name, request.description, strategy_id))
            
            # Delete old compositions
            conn.execute("""
                DELETE FROM user_strategy_compositions WHERE user_strategy_id = ?
            """, (strategy_id,))
            
            # Insert new compositions
            for comp in request.compositions:
                conn.execute("""
                    INSERT INTO user_strategy_compositions 
                        (user_strategy_id, instrument_ticker, block_name, weight, fit_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    strategy_id, comp.ticker, comp.block_name, 
                    comp.weight, comp.fit_score
                ))
            
            return UserStrategy(
                id=strategy_id,
                name=request.name,
                description=request.description,
                template_id=request.template_id,
                compositions=request.compositions,
                updated_at=datetime.now().isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{strategy_id}")
async def delete_user_strategy(
    strategy_id: int,
    user_id: str = Query("default", description="User ID")
):
    """Delete a user strategy."""
    try:
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Check ownership
            row = conn.execute("""
                SELECT 1 FROM user_strategies WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id)).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Delete (compositions deleted via CASCADE)
            conn.execute("DELETE FROM user_strategies WHERE id = ?", (strategy_id,))
            
            return {"status": "deleted", "id": strategy_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{strategy_id}/add-instrument")
async def add_instrument_to_strategy(
    strategy_id: int,
    data: Dict[str, Any] = Body(...),
    user_id: str = Query("default", description="User ID")
):
    """Add an instrument to an existing user strategy."""
    try:
        ticker = data.get('ticker')
        weight = data.get('weight', 0.05)
        block_name = data.get('block_name', 'custom')
        
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker required")
        
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Check ownership
            row = conn.execute("""
                SELECT 1 FROM user_strategies WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id)).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Check if ticker already exists
            existing = conn.execute("""
                SELECT 1 FROM user_strategy_compositions 
                WHERE user_strategy_id = ? AND instrument_ticker = ?
            """, (strategy_id, ticker)).fetchone()
            
            if existing:
                raise HTTPException(status_code=400, detail="Instrument already in strategy")
            
            # Insert
            conn.execute("""
                INSERT INTO user_strategy_compositions 
                    (user_strategy_id, instrument_ticker, block_name, weight)
                VALUES (?, ?, ?, ?)
            """, (strategy_id, ticker, block_name, weight))
            
            # Update timestamp
            conn.execute("""
                UPDATE user_strategies SET updated_at = datetime('now')
                WHERE id = ?
            """, (strategy_id,))
            
            return {"status": "added", "ticker": ticker, "strategy_id": strategy_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding instrument to strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AISuggestRequest(BaseModel):
    """Request for AI-powered asset suggestions."""
    risk_profile: str = Field(default="balanced")
    horizon_years: int = Field(default=10, ge=1, le=30)
    exclude_tickers: List[str] = []
    limit: int = Field(default=10, ge=1, le=50)


@router.post("/ai-suggest")
async def get_ai_suggestions(request: AISuggestRequest):
    """
    Get AI-powered asset suggestions based on risk profile and horizon.
    
    Uses the existing scoring system to find appropriate assets:
    - Conservative: Low volatility, high safety score
    - Balanced: Mix of safety and momentum
    - Growth: High momentum and total score
    - Aggressive: Highest momentum, accepts higher volatility
    """
    try:
        store = SQLiteStore()
        
        # Map risk profile to scoring criteria
        sort_criteria = {
            'conservative': ('score_safety', True),
            'balanced': ('score_total', True),
            'growth': ('score_momentum', True),
            'aggressive': ('score_momentum', True),
        }
        
        sort_by, sort_desc = sort_criteria.get(request.risk_profile, ('score_total', True))
        
        # Get assets from store
        assets, _ = store.list_assets_paginated(
            market_scope="US_EU",
            scored_filter="scored",
            eligible_only=True,
            page=1,
            page_size=request.limit * 3,  # Get more to filter
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        # Filter out excluded tickers
        filtered = [a for a in assets if a.get('symbol') not in request.exclude_tickers]
        
        # Apply additional risk-based filters
        if request.risk_profile == 'conservative':
            # Low volatility only
            filtered = [a for a in filtered if (a.get('vol_annual') or 100) < 20]
        elif request.risk_profile == 'aggressive':
            # Higher volatility acceptable for momentum plays
            filtered = [a for a in filtered if (a.get('score_momentum') or 0) > 50]
        
        # Limit results
        filtered = filtered[:request.limit]
        
        # Format response
        suggestions = []
        for asset in filtered:
            suggestions.append({
                'ticker': asset.get('symbol'),
                'name': asset.get('name', ''),
                'asset_type': asset.get('asset_type', 'EQUITY'),
                'score_total': asset.get('score_total'),
                'score_safety': asset.get('score_safety'),
                'score_momentum': asset.get('score_momentum'),
                'vol_annual': asset.get('vol_annual'),
                'rationale': _get_suggestion_rationale(request.risk_profile, asset),
            })
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_suggestion_rationale(profile: str, asset: Dict) -> str:
    """Generate a brief rationale for why an asset is suggested."""
    score_total = asset.get('score_total') or 0
    score_safety = asset.get('score_safety') or 0
    score_momentum = asset.get('score_momentum') or 0
    vol = asset.get('vol_annual') or 0
    
    if profile == 'conservative':
        if score_safety > 70:
            return f"Score sécurité élevé ({score_safety:.0f}/100), volatilité maîtrisée ({vol:.1f}%)"
        return f"Volatilité faible ({vol:.1f}%), bon score global ({score_total:.0f})"
    
    elif profile == 'balanced':
        return f"Équilibre sécurité/performance ({score_safety:.0f}/{score_momentum:.0f})"
    
    elif profile == 'growth':
        if score_momentum > 60:
            return f"Fort momentum ({score_momentum:.0f}/100), tendance positive"
        return f"Score global élevé ({score_total:.0f}), potentiel de croissance"
    
    else:  # aggressive
        return f"Momentum exceptionnel ({score_momentum:.0f}), forte dynamique"


# ═══════════════════════════════════════════════════════════════════════════
# AI-POWERED STRATEGY GENERATION
# ═══════════════════════════════════════════════════════════════════════════

class AIStrategyRequest(BaseModel):
    """Request for AI-powered strategy generation."""
    description: str = Field(..., min_length=10, max_length=2000, description="User's strategy description")


class AIStrategyResponse(BaseModel):
    """Response from AI strategy generation."""
    success: bool
    strategy_name: str
    description: str
    risk_profile: str
    investment_horizon: int
    rationale: str
    blocks: List[Dict[str, Any]]
    key_principles: List[str]
    warnings: List[str]
    matched_assets: Dict[str, List[Dict[str, Any]]]
    explanation: str


@router.post("/ai-generate", response_model=AIStrategyResponse)
async def generate_ai_strategy(request: AIStrategyRequest):
    """
    Generate a strategy using AI based on user's description.
    
    1. Sends description to ChatGPT for analysis
    2. Gets structured strategy recommendations
    3. Matches assets from our universe to each block
    4. Returns complete strategy with explanation
    """
    from ai_strategy_service import (
        get_ai_strategy_suggestion,
        match_assets_to_strategy,
        generate_strategy_explanation
    )
    
    try:
        logger.info(f"AI strategy request: {request.description[:100]}...")
        
        # Step 1: Get AI recommendations
        strategy_data = await get_ai_strategy_suggestion(request.description)
        
        # Step 2: Get available assets from our universe
        store = SQLiteStore()
        assets, _ = store.list_assets_paginated(
            market_scope="US_EU",
            scored_filter="scored",
            eligible_only=True,
            page=1,
            page_size=500,
            sort_by="score_total",
            sort_desc=True
        )
        
        # Convert to dict format
        available_assets = []
        for asset in assets:
            available_assets.append({
                "ticker": asset.get("symbol"),
                "name": asset.get("name", ""),
                "asset_type": asset.get("asset_type", "EQUITY"),
                "score_total": asset.get("score_total"),
                "score_safety": asset.get("score_safety"),
                "score_momentum": asset.get("score_momentum"),
                "vol_annual": asset.get("vol_annual"),
                "sector": asset.get("sector", ""),
            })
        
        # Step 3: Match assets to strategy blocks
        matched_assets = await match_assets_to_strategy(
            strategy_data.get("blocks", []),
            available_assets
        )
        
        # Step 4: Generate human-readable explanation
        explanation = generate_strategy_explanation(strategy_data, matched_assets)
        
        return AIStrategyResponse(
            success=True,
            strategy_name=strategy_data.get("strategy_name", "Ma Stratégie"),
            description=strategy_data.get("description", ""),
            risk_profile=strategy_data.get("risk_profile", "balanced"),
            investment_horizon=strategy_data.get("investment_horizon", 10),
            rationale=strategy_data.get("rationale", ""),
            blocks=strategy_data.get("blocks", []),
            key_principles=strategy_data.get("key_principles", []),
            warnings=strategy_data.get("warnings", []),
            matched_assets=matched_assets,
            explanation=explanation
        )
        
    except Exception as e:
        logger.error(f"AI strategy generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de la stratégie: {str(e)}"
        )
