# Institutional Liquidity & Data Quality Guard

**Version**: 2.0.0  
**Type**: ADD-ON (Zero Breaking Changes)  
**Status**: Production Ready  

---

## 📋 Overview

The Institutional Guard is an **additive module** that prevents illiquid or low-quality assets from appearing "excellent" in rankings. It introduces:

1. **`score_institutional`**: Adjusted score with liquidity & quality penalties
2. **Liquidity Tiers (A/B/C/D)**: Classification based on Average Daily Volume
3. **Data Quality Flags**: Warnings for stale prices, low coverage, etc.
4. **Recommended Horizons**: Minimum investment timeframe (1/3/5/10 years)

**Key Principle**: `score_total` is **never modified** - it remains for backward compatibility.

---

## 🏗️ Architecture

### Database Changes (ADD-ONLY)

New columns in `scores_latest` table:

| Column | Type | Description |
|--------|------|-------------|
| `score_institutional` | REAL | Adjusted score (0-100) |
| `liquidity_tier` | TEXT | A, B, C, or D |
| `liquidity_penalty` | REAL | Points deducted |
| `liquidity_flag` | INTEGER | 1 if liquidity concern |
| `data_quality_flag` | INTEGER | 1 if quality concern |
| `data_quality_score` | REAL | Data quality (0-100) |
| `stale_price_flag` | INTEGER | 1 if stale prices |
| `min_recommended_horizon_years` | INTEGER | 1, 3, 5, or 10 |
| `institutional_explanation` | TEXT | Human-readable explanation |
| `adv_usd` | REAL | Average Daily Volume in USD |

### Pipeline Module

`pipeline/institutional_guard.py`

```python
from pipeline.institutional_guard import InstitutionalGuard

# Run for all scored assets
guard = InstitutionalGuard(market_scope="US_EU")
stats = guard.run()

# Assess single asset
assessment = guard.assess_single_asset("AAPL.US")
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/assets/top-scored` | Original endpoint (now includes institutional fields) |
| `GET /api/assets/top-scored-institutional` | **NEW** - Ranked by `score_institutional` |
| `GET /api/assets/{ticker}` | Asset detail (now includes institutional fields) |

---

## 📊 Liquidity Tiers

| Tier | ADV (USD) | Penalty | Cap | Horizon |
|------|-----------|---------|-----|---------|
| A | ≥ $5M | 0 pts | 100 | 10 years |
| B | $1M - $5M | 5 pts | 90 | 5 years |
| C | $500K - $1M | 20 pts | 70 | 3 years |
| D | < $500K | 45 pts | 55 | 1 year |

### Example Calculations

**Case 1: Small Cap Illiquid (ADV $200K, score_total=90)**
```
- Tier: D
- Penalty: -45 pts
- Cap: 55
- score_institutional = min(90 - 45, 55) = 45
- liquidity_flag = TRUE
- Horizon: 1 year
```

**Case 2: Large Cap Institutional (ADV $20M, score_total=80)**
```
- Tier: A
- Penalty: 0 pts
- Cap: 100
- score_institutional = 80
- liquidity_flag = FALSE
- Horizon: 10 years
```

---

## 🔧 Data Quality Rules

| Condition | Penalty | Cap | Flag |
|-----------|---------|-----|------|
| Coverage < 80% | -15 pts | 65 | data_quality_flag |
| Stale > 7 days OR stale_ratio > 15% | -20 pts | 55 | stale_price_flag |
| Zero volume > 10% | -10 pts | — | data_quality_flag |

---

## 🖥️ Frontend Components

### Badges

```tsx
import {
  LiquidityTierBadge,
  LiquidityFlagBadge,
  DataQualityBadge,
  HorizonBadge,
  InstitutionalWarnings,
  RankingModeToggle
} from '@/components/ui/institutional-badges';

// Display warnings for an asset
<InstitutionalWarnings asset={asset} />

// Toggle ranking mode
<RankingModeToggle 
  mode={rankingMode} 
  onChange={setRankingMode} 
/>
```

### Visual Indicators

- **LOW LIQUIDITY** (red): Asset has liquidity concerns
- **DATA RISK** (yellow): Data quality issues detected
- **STALE** (yellow): Prices may be outdated
- **Tier A/B/C/D**: Liquidity classification
- **Horizon: X+ ans**: Minimum recommended investment period

---

## 🚀 Deployment

### 1. Apply Migration

```bash
cd MarketGPS
sqlite3 data/marketgps.db < storage/migrations/add_institutional_guard_columns.sql
```

### 2. Run Institutional Guard

```bash
cd MarketGPS
source venv/bin/activate
python -c "from pipeline.institutional_guard import run_institutional_guard; run_institutional_guard('US_EU')"
```

### 3. Verify

```bash
# Check columns exist
sqlite3 data/marketgps.db "PRAGMA table_info(scores_latest);" | grep institutional

# Check data
sqlite3 data/marketgps.db "SELECT asset_id, score_total, score_institutional, liquidity_tier, liquidity_flag FROM scores_latest WHERE score_institutional IS NOT NULL LIMIT 10;"

# Test API
curl http://localhost:8501/api/assets/top-scored-institutional?limit=5
```

---

## ✅ Definition of Done Checklist

### Migration
- [ ] SQL file created: `storage/migrations/add_institutional_guard_columns.sql`
- [ ] Columns added to `scores_latest` without breaking existing data
- [ ] Indexes created for efficient queries

### Pipeline
- [ ] `pipeline/institutional_guard.py` created
- [ ] All liquidity tiers implemented (A/B/C/D)
- [ ] Data quality checks implemented
- [ ] Horizon calculation implemented
- [ ] Unit tests pass

### Backend API
- [ ] `AssetResponse` model extended with institutional fields
- [ ] `AssetDetailResponse` model extended
- [ ] `/api/assets/top-scored` returns new fields
- [ ] `/api/assets/top-scored-institutional` endpoint created
- [ ] `/api/assets/{ticker}` returns new fields
- [ ] No breaking changes to existing responses

### Frontend
- [ ] Types extended with institutional fields
- [ ] Badge components created
- [ ] `RankingModeToggle` component created
- [ ] API function `getTopScoredInstitutional` added

### Tests
- [ ] `tests/test_institutional_guard.py` created
- [ ] Liquidity tier tests pass
- [ ] Score calculation tests pass
- [ ] Data quality tests pass
- [ ] Horizon tests pass

---

## 🔄 Backward Compatibility

**Guaranteed**: 
- `score_total` is NEVER modified
- All existing endpoints continue to work
- New fields are `NULL` until guard runs
- Frontend renders gracefully if fields are missing

---

## 📈 Integration with Pipeline

Add to your scoring pipeline (optional):

```python
# In pipeline/jobs.py or similar
from pipeline.institutional_guard import run_institutional_guard

def run_full_pipeline(market_scope="US_EU"):
    # ... existing scoring ...
    
    # Add institutional guard at the end
    run_institutional_guard(market_scope)
```

---

## 📚 Related Documentation

- [BARBELL_BUILDER.md](./BARBELL_BUILDER.md) - Barbell strategy module
- [STRATEGIES_MODULE.md](./STRATEGIES_MODULE.md) - Strategies module
- [LONG_TERM_SCORING.md](./LONG_TERM_SCORING.md) - Long-term scoring specs
