# Barbell Builder & Simulation

## Overview

The Barbell Strategy module provides an interactive, customizable portfolio builder combining:
- **Core Assets (60-85%)**: Ultra-safe, low-volatility assets for capital preservation
- **Satellite Assets (15-40%)**: High-momentum, growth-oriented assets for upside potential

## Features

### 1. Portfolio Suggestion
Automatic portfolio generation based on risk profile:
- **Conservative**: 85% Core / 15% Satellite
- **Moderate**: 75% Core / 25% Satellite  
- **Aggressive**: 65% Core / 35% Satellite

### 2. Candidates Tables
Paginated, filterable tables for asset selection:

#### Core Candidates
Filters available:
- Minimum score (total, safety)
- Maximum volatility
- Asset type (EQUITY, ETF, BOND)
- Search by ticker/name

#### Satellite Candidates
Filters available:
- Minimum score (total, momentum)
- Asset type
- Search by ticker/name

### 3. Barbell Builder
Interactive composition editor:
- Add/remove assets
- Adjust weights per asset
- Auto-normalization to 100%
- Core/Satellite ratio visualization
- Warnings for invalid configurations
- Save portfolios

### 4. Backtest Simulation
Historical performance simulation:
- Period: 5, 10, or 20 years
- Rebalancing: Monthly, Quarterly, or Yearly
- Custom initial capital

Metrics returned:
- CAGR (Compound Annual Growth Rate)
- Volatility
- Sharpe Ratio
- Maximum Drawdown
- Equity curve (monthly data points)
- Yearly performance table
- Best/Worst year

## API Endpoints

### Existing (unchanged)
- `GET /api/barbell/health` - Health check
- `GET /api/barbell/allocation-ratios` - Risk profile definitions
- `GET /api/barbell/suggest` - AI-suggested portfolio
- `GET /api/barbell/core-candidates` - Basic core candidates
- `GET /api/barbell/satellite-candidates` - Basic satellite candidates

### New Endpoints

#### Enhanced Candidates
```
GET /api/barbell/candidates/core
GET /api/barbell/candidates/satellite
```

Query parameters:
- `market_scope`: US_EU or AFRICA
- `limit`, `offset`: Pagination
- `q`: Search query
- `min_score_total`, `min_score_safety`, `min_score_momentum`
- `max_vol_annual`
- `asset_type`: EQUITY, ETF, BOND
- `sort_by`, `sort_order`

#### Simulation
```
POST /api/barbell/simulate
```

Request body:
```json
{
  "compositions": [
    {"asset_id": "AAPL_NASDAQ", "weight": 0.15, "block": "core"},
    {"asset_id": "NVDA_NASDAQ", "weight": 0.10, "block": "satellite"}
  ],
  "period_years": 10,
  "rebalance_frequency": "yearly",
  "initial_capital": 10000,
  "market_scope": "US_EU"
}
```

Response:
```json
{
  "cagr": 8.54,
  "volatility": 15.2,
  "sharpe": 0.56,
  "max_drawdown": -32.4,
  "total_return": 127.3,
  "final_value": 22730,
  "equity_curve": [{"date": "2014-01-31", "value": 10234}],
  "yearly_table": [{"year": 2014, "return": 12.3}],
  "best_year": {"year": 2019, "return": 28.4},
  "worst_year": {"year": 2022, "return": -18.2},
  "warnings": ["TSLA: Low data coverage"],
  "data_quality_score": 85,
  "assets_included": 8,
  "assets_excluded": 2
}
```

#### Portfolio Persistence
```
GET /api/barbell/portfolios?user_id=default_user
POST /api/barbell/portfolios?user_id=default_user
GET /api/barbell/portfolios/{portfolio_id}
PUT /api/barbell/portfolios/{portfolio_id}
DELETE /api/barbell/portfolios/{portfolio_id}
```

## Database Tables

### barbell_portfolios
Stores saved portfolio configurations:
- `id`, `user_id`, `name`, `description`
- `risk_profile` (conservative/moderate/aggressive)
- `core_ratio`, `satellite_ratio`
- `created_at`, `updated_at`, `is_active`

### barbell_portfolio_items
Assets in each portfolio:
- `portfolio_id`, `asset_id`
- `block` (core/satellite)
- `weight` (0-1)
- `notes`, `added_at`

### barbell_simulation_cache
Cached simulation results:
- `composition_hash` (unique key)
- `period_years`, `rebalance_frequency`, `initial_capital`
- `result_json` (full results)
- `computed_at`, `expires_at`, `data_quality_score`

## Usage

### Frontend

1. Navigate to `/barbell`
2. Select risk profile (Conservative/Moderate/Aggressive)
3. View suggested portfolio or browse candidates
4. Customize in Builder tab:
   - Add assets from candidates
   - Adjust weights
   - Normalize to 100%
5. Run simulation to see backtested performance
6. Save portfolio for future reference

### Testing Simulation

```bash
curl -X POST http://localhost:8501/api/barbell/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "compositions": [
      {"asset_id": "AAPL_NASDAQ", "weight": 0.5, "block": "core"},
      {"asset_id": "MSFT_NASDAQ", "weight": 0.5, "block": "satellite"}
    ],
    "period_years": 10,
    "rebalance_frequency": "yearly",
    "initial_capital": 10000
  }'
```

## Warnings & Data Quality

The system tracks data quality issues:

- **high_volatility**: Asset has vol > 40%
- **low_coverage**: Data coverage < 70%
- **low_safety**: Safety score < 50
- **low_momentum**: Momentum score < 50
- **insufficient_history**: Less than 1 year of price data

Assets with warnings are still eligible but flagged in the UI.

## Technical Notes

### Simulation Engine
- Uses Parquet OHLCV files from `data/parquet/us_eu/bars_daily/`
- Adjusted close prices for accurate returns
- Monthly sampling for equity curve (performance optimization)
- Assets without sufficient history are excluded and weights renormalized

### Performance
- Backend pagination prevents large data transfers
- React Query caching reduces API calls
- Simulation results can be cached via `barbell_simulation_cache`

## Zero Breaking Changes

This module is purely additive:
- No existing routes modified
- No existing tables altered
- No existing components changed
- All new files in `/components/barbell/` and `/api/barbell/`
