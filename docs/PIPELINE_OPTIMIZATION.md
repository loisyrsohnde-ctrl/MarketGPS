# MarketGPS - Pipeline Optimization Guide

## 🎯 Problem Statement

The original pipeline made **individual API calls** for each asset:
- 20,000 assets × 1 EOD call = 20,000 API calls
- 20,000 assets × 1 fundamentals call = 20,000 API calls
- **Total: ~40,000+ API calls** per full pipeline run

This was:
- ❌ Slow (hours to complete)
- ❌ Expensive (API quota consumption)
- ❌ Unreliable (rate limiting, timeouts)

---

## ✅ Solution: Smart Pipeline

The optimized pipeline uses **bulk endpoints** and **intelligent pre-filtering**:

| Endpoint | Old Approach | New Approach |
|----------|--------------|--------------|
| Listings | N/A | 1 call per exchange (~20 calls) |
| EOD Data | 1 call per asset | 1 bulk call per exchange (~20 calls) |
| History | 1 call per asset | Only for NEW assets |
| Fundamentals | 1 call per asset | Only for scored assets |

**Result: ~97% reduction in API calls!**

---

## 📁 New Files Created

```
scripts/
├── smart_universe_builder.py   # Pre-filters using bulk data
├── run_optimized_pipeline.py   # Full orchestration

pipeline/
├── smart_bulk_fetcher.py       # Bulk EOD fetching
├── smart_logo_fetcher.py       # Batch logo fetching
```

---

## 🚀 Usage

### Quick Daily Update (Fastest)
```bash
python scripts/run_optimized_pipeline.py --scope US_EU --skip-history
```
- Uses bulk EOD to update existing assets
- Skips fetching history for new assets
- ~5-10 minutes

### Standard Daily Run
```bash
python scripts/run_optimized_pipeline.py --scope US_EU
```
- Updates existing assets (bulk)
- Fetches 5-year history for new assets (limited)
- ~30-60 minutes

### Full Rebuild (Both Scopes)
```bash
python scripts/run_optimized_pipeline.py --full
```
- Runs for US_EU and AFRICA
- Complete rebuild
- ~2-3 hours

### Africa Only
```bash
python scripts/run_optimized_pipeline.py --scope AFRICA --tier1-limit 500
```

---

## 📊 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMIZED PIPELINE FLOW                       │
└─────────────────────────────────────────────────────────────────┘

STEP 1: Smart Universe Builder
         │
         ├─> GET /exchange-symbol-list/{EXCHANGE}  (20 calls)
         │   Returns: All tickers for each exchange
         │
         ├─> GET /eod-bulk-last-day/{EXCHANGE}     (20 calls)
         │   Returns: Latest price/volume for ALL tickers
         │
         ├─> Estimate ADV (close × volume)
         │
         ├─> Categorize by Tier:
         │   ┌─────────────────────────────────────────┐
         │   │ TIER 1: ADV > $5M   → ACTIVE (2000 max) │
         │   │ TIER 2: ADV > $1M   → ACTIVE (1000 max) │
         │   │ TIER 3: ADV > $100K → INACTIVE          │
         │   │ TIER 4: ADV < $100K → INACTIVE          │
         │   └─────────────────────────────────────────┘
         │
         └─> Insert into SQLite: universe table
                                                      
STEP 2: Smart Bulk Fetcher
         │
         ├─> GET /eod-bulk-last-day/{EXCHANGE}     (20 calls)
         │   Returns: Latest bar for ALL tickers
         │
         ├─> Update existing Parquet files          (0 calls!)
         │   Uses bulk data, no individual fetches
         │
         └─> For NEW assets only:
             GET /eod/{SYMBOL}?from=5y              (N calls)
             (Limited to Tier 1 new assets)
                                                      
STEP 3: Gating
         │
         ├─> Load Parquet data (cached)             (0 calls!)
         │
         ├─> Calculate: coverage, liquidity, stale_ratio
         │
         └─> Mark eligible/ineligible in DB
                                                      
STEP 4: Scoring
         │
         ├─> Load Parquet data (cached)             (0 calls!)
         │
         ├─> Calculate: RSI, SMA, volatility, drawdown
         │
         ├─> Calculate pillar scores:
         │   - Momentum (RSI + Price vs SMA)
         │   - Safety (Vol + Drawdown)
         │   - Value (P/E + Margins + ROE) [EQUITY only]
         │
         └─> Save to scores_latest table
                                                      
STEP 5: Logos (Optional)
         │
         ├─> For top scored assets only
         │
         └─> Clearbit API (free, rate limited)
```

---

## ⚙️ Configuration Options

### Tier Limits
Control how many assets are actively processed:

```bash
--tier1-limit 2000   # Very liquid assets (default: 2000)
--tier2-limit 1000   # Liquid assets (default: 1000)
```

**Total active = tier1 + tier2 = 3000 assets**

### History Options
```bash
--skip-history       # Don't fetch history for new assets
--history-years 5    # Years of history (default: 5)
--limit-new 500      # Max new assets to fetch history for
```

### Logo Options
```bash
--skip-logos         # Don't fetch logos
--logo-limit 200     # Max logos to fetch (default: 200)
```

---

## 📈 API Call Comparison

### Before (Old Approach)
| Step | Calls per Asset | Total Assets | Total Calls |
|------|----------------|--------------|-------------|
| Expand Universe | 1 | 20,000 | 20,000 |
| Gating (EOD) | 1 | 20,000 | 20,000 |
| Scoring (EOD) | 1 | 10,000 | 10,000 |
| Scoring (Fund) | 1 | 10,000 | 10,000 |
| **TOTAL** | | | **60,000** |

### After (Optimized)
| Step | Calls | Notes |
|------|-------|-------|
| Universe Listings | 20 | 1 per exchange |
| Universe Bulk EOD | 20 | 1 per exchange |
| Bulk Fetcher | 20 | 1 per exchange |
| New Asset History | ~1,000 | Only NEW Tier 1 |
| Gating | 0 | Uses Parquet |
| Scoring | 0 | Uses Parquet |
| **TOTAL** | **~1,060** | **98% reduction!** |

---

## 🛡️ Backward Compatibility

All existing functionality is preserved:

| Component | Status |
|-----------|--------|
| `pipeline/scoring.py` | ✅ Unchanged |
| `pipeline/gating.py` | ✅ Unchanged |
| `pipeline/jobs.py` | ✅ Unchanged |
| `backend/api_routes.py` | ✅ Unchanged |
| Frontend | ✅ Unchanged |
| Database schema | ✅ Unchanged |

The new scripts are **ADD-ONLY**. You can still use the old approach:
```bash
# Old approach still works
python -m pipeline.jobs --full-pipeline --scope US_EU
```

---

## 🔧 Troubleshooting

### "EODHD API key not configured"
```bash
export EODHD_API_KEY=your_api_key
```

### "Rate limit exceeded"
The scripts have built-in rate limiting. If you still hit limits:
```bash
# Process fewer assets
python scripts/run_optimized_pipeline.py --tier1-limit 500 --tier2-limit 500
```

### "No data for exchange X"
Some exchanges may not be available in your EODHD plan. The scripts will skip them gracefully.

---

## 📋 Recommended Schedule

### Daily (Market Open - 09:35 ET)
```bash
python scripts/run_optimized_pipeline.py --scope US_EU --skip-history
```
- Fast update using bulk data
- ~5-10 minutes

### Daily (Market Close - 16:10 ET)
```bash
python scripts/run_optimized_pipeline.py --scope US_EU --limit-new 100
```
- Full update with limited new asset history
- ~30 minutes

### Weekly (Weekend)
```bash
python scripts/run_optimized_pipeline.py --full
```
- Complete rebuild for both scopes
- Fetch all new asset history
- ~2-3 hours

---

## 🎓 How It Works: Technical Details

### Smart Universe Builder (`smart_universe_builder.py`)

1. **Fetch Listings**: Uses `/exchange-symbol-list/{EXCHANGE}` to get all available tickers (name, type, currency, ISIN)

2. **Fetch Bulk EOD**: Uses `/eod-bulk-last-day/{EXCHANGE}` to get latest price/volume for ALL tickers at once

3. **Estimate Liquidity**: Calculates ADV = close × volume from bulk data (no extra API calls!)

4. **Tier Classification**:
   - Tier 1: ADV > $5M (very liquid - prioritized)
   - Tier 2: ADV > $1M (liquid - included)
   - Tier 3: ADV > $100K (low liquidity - inactive)
   - Tier 4: ADV < $100K (illiquid - inactive)

5. **Insert to DB**: Only Tier 1 + Tier 2 marked as `active=1`

### Smart Bulk Fetcher (`smart_bulk_fetcher.py`)

1. **Bulk Latest**: Gets today's data for ALL assets (1 call per exchange)

2. **Update Existing**: Appends bulk data to existing Parquet files (0 API calls!)

3. **Identify New**: Finds assets without Parquet files

4. **Fetch History**: Only for NEW assets, uses individual `/eod/{SYMBOL}` calls

### Gating & Scoring

No changes needed! They already use Parquet files, so:
- Gating reads from `data/parquet/us_eu/bars_daily/*.parquet`
- Scoring reads from same Parquet files
- **Zero additional API calls**
