# Long-Term Institutional Scoring (LT Score)

> **Version:** 1.0  
> **Scope:** US_EU only  
> **Horizon:** 5-20 years investment perspective

## Overview

The Long-Term Score (LT Score) is an **add-on** to MarketGPS designed for institutional investors with long-term horizons. It complements the existing short-term scoring system without replacing it.

### Key Features

- **5-Pillar approach**: Investability, Quality, Safety, Value, Momentum
- **Institutional caps**: Prevents illiquid/microcap assets from achieving inflated scores
- **Confidence scoring**: Reflects data completeness and reliability
- **Non-destructive**: Does not modify existing scoring or API behavior

---

## Score Structure

### Pillar Weights

| Pillar | Weight | Focus |
|--------|--------|-------|
| **Investability (I)** | 20% | Can institutions actually trade this? |
| **Quality (Q)** | 35% | Is this a well-run, profitable company? |
| **Safety (S)** | 20% | How risky is this investment? |
| **Value (V)** | 15% | Is the stock cheap relative to fundamentals? |
| **Momentum (M)** | 10% | Is price trend favorable? |

### Formula

```
lt_raw = 0.20 × I + 0.35 × Q + 0.20 × S + 0.15 × V + 0.10 × M
lt_score = min(lt_raw, lt_score_max)
```

Where `lt_score_max` is determined by institutional caps.

---

## Institutional Caps

**The most important feature** of LT scoring is preventing illiquid or microcap assets from achieving top ranks through caps:

| Condition | Cap Applied | Reason |
|-----------|------------|--------|
| ADV < $250K **OR** Market Cap < $50M | `lt_score_max = 55` | Too illiquid for institutional trading |
| $250K ≤ ADV < $1M | `lt_score_max = 70` | Low liquidity limits position sizing |
| Price < $1 | `lt_score_max = 60` | Penny stock risk |
| Data Coverage < 60% | `lt_score_max = 65` | Insufficient data reliability |
| Confidence < 40% | `lt_score *= 0.85` + cap 65 | Low data quality penalty |

### Why Caps Matter

Without caps, a microcap with limited trading history could score artificially high on momentum or value metrics. This creates problems for institutional investors who:

1. Cannot enter/exit positions without moving the market
2. Have regulatory constraints on illiquid holdings
3. Need reliable data for due diligence

**Example:**
```
Asset: MICROCAP.US
- Raw LT Score: 82 (good fundamentals, high momentum)
- ADV: $150K (very illiquid)
- Market Cap: $40M (microcap)

Applied caps: LOW_LIQUIDITY, MICRO_CAP
Final LT Score: 55 (capped)
```

---

## Pillar Details

### Investability (I) - 20%

Measures institutional tradability:

| Component | Weight | Scoring |
|-----------|--------|---------|
| ADV (log scale) | 40% | $100K=30, $1M=60, $10M=90, $100M=100 |
| Market Cap (log) | 30% | $10M=20, $1B=60, $100B=100 |
| Data Coverage | 20% | Linear 0-100 based on coverage % |
| Trading Quality | 10% | Low stale/zero volume = higher |

### Quality (Q) - 35%

Assesses business fundamentals:

| Component | Weight | Metrics |
|-----------|--------|---------|
| Profitability | 40% | Profit margin, Operating margin, ROE, ROA |
| Financial Health | 35% | Debt/Equity (lower=better), Current Ratio |
| Growth | 25% | Revenue growth, Earnings growth |

### Safety (S) - 20%

Evaluates risk metrics:

| Component | Weight | Scoring |
|-----------|--------|---------|
| Volatility | 40% | Lower annual vol = higher score |
| Max Drawdown | 40% | Smaller drawdown = higher score |
| Beta | 10% | Lower market correlation = higher |
| Sharpe Ratio | 10% | Higher risk-adjusted return = higher |

### Value (V) - 15%

Assesses valuation:

| Component | Weight | Notes |
|-----------|--------|-------|
| P/E Ratio | 50% | Optimal 5-30, penalize extremes |
| Forward P/E | 25% | Forward-looking valuation |
| Price/Book | 15% | Asset-based valuation |
| Dividend Yield | 10% | Income component |

### Momentum (M) - 10%

Technical trend analysis:

| Component | Weight | Optimal |
|-----------|--------|---------|
| RSI | 30% | 40-70 range optimal, peak at 55 |
| Price vs SMA200 | 30% | Above SMA = positive |
| 3-Month Momentum | 20% | Recent trend |
| 12-Month Momentum | 20% | Long-term trend |

---

## Confidence Calculation

LT Confidence reflects data completeness:

```
coverage_fundamentals = fields_present / 11 fundamental fields
coverage_price = fields_present / 7 price fields

lt_confidence = 0.6 × coverage_fundamentals + 0.4 × coverage_price
```

### Fundamental Fields (11)
`pe_ratio, forward_pe, profit_margin, operating_margin, roe, roa, revenue_growth, earnings_growth, debt_to_equity, current_ratio, market_cap`

### Price Fields (7)
`last_price, sma200, rsi, volatility_annual, max_drawdown, momentum_12m, adv_usd`

### Low Confidence Penalty
When `lt_confidence < 0.4`:
- `lt_score *= 0.85` (15% penalty)
- `lt_score_max = 65`
- Breakdown notes `LOW_CONFIDENCE`

---

## API Response

### Asset List Response
```json
{
  "asset_id": "AAPL.US",
  "ticker": "AAPL",
  "score_total": 78.5,
  "lt_score": 82.3,
  "lt_confidence": 94.2
}
```

### Asset Detail Response
```json
{
  "asset_id": "AAPL.US",
  "lt_score": 82.3,
  "lt_confidence": 94.2,
  "lt_breakdown": {
    "version": "1.0",
    "lt_raw": 82.3,
    "lt_capped": 82.3,
    "pillar_weights": {
      "investability": 0.20,
      "quality": 0.35,
      "safety": 0.20,
      "value": 0.15,
      "momentum": 0.10
    },
    "pillar_scores": {
      "investability": 95.2,
      "quality": 78.4,
      "safety": 82.1,
      "value": 65.3,
      "momentum": 72.8
    },
    "caps": {
      "applied": [],
      "reason": null,
      "score_before_cap": 82.3,
      "score_after_cap": 82.3
    },
    "confidence": {
      "fund_coverage": 1.0,
      "price_coverage": 1.0,
      "lt_confidence": 1.0
    },
    "macro_overlay": {
      "enabled": false,
      "reason": "no reliable macro feed in repo"
    }
  }
}
```

---

## Example Breakdown: Capped Microcap

```json
{
  "asset_id": "SMALLCO.US",
  "lt_score": 55.0,
  "lt_confidence": 62.5,
  "lt_breakdown": {
    "lt_raw": 74.8,
    "lt_capped": 55.0,
    "pillar_scores": {
      "investability": 35.2,
      "quality": 82.1,
      "safety": 68.4,
      "value": 88.9,
      "momentum": 71.3
    },
    "caps": {
      "applied": [
        "LOW_LIQUIDITY_ADV<250K",
        "MICRO_CAP<50M"
      ],
      "reason": "LOW_LIQUIDITY_ADV<250K; MICRO_CAP<50M",
      "score_before_cap": 74.8,
      "score_after_cap": 55.0
    }
  }
}
```

**Interpretation:**
- Raw score was 74.8 (fairly good on fundamentals)
- But ADV < $250K and Market Cap < $50M triggered caps
- Final score capped at 55, preventing false "top pick" status

---

## Usage

### CLI Flag

Enable long-term scoring during pipeline rotation:

```bash
# Run rotation with LT scoring
python -m pipeline.jobs rotation --scope US_EU --run-longterm-scoring

# Full pipeline with LT scoring
python -m pipeline.jobs rotation --scope US_EU --run-longterm-scoring --batch-size 100
```

### Database Storage

LT scores are stored in `scores_latest`:

| Column | Type | Description |
|--------|------|-------------|
| `lt_score` | REAL | Final capped score (0-100) |
| `lt_confidence` | REAL | Confidence score (0-100) |
| `lt_breakdown` | TEXT | JSON breakdown details |
| `lt_updated_at` | TEXT | Last update timestamp |

### Migration

Apply the schema migration:

```bash
sqlite3 data/sqlite/marketgps.db < storage/add_longterm_scores.sql
```

Or let the pipeline auto-migrate on first run with `--run-longterm-scoring`.

---

## Limitations

1. **Macro/News Overlay**: Not implemented - no reliable macro feed in repository
   - Breakdown includes `"macro_overlay": {"enabled": false}`
   - Future work could integrate economic indicators

2. **Sector Normalization**: Value pillar could benefit from sector-relative comparisons
   - Currently uses absolute thresholds
   - Banks vs Tech have different P/E norms

3. **Data Freshness**: Relies on pipeline refresh frequency
   - Stale data reduces confidence but doesn't prevent scoring

4. **US_EU Only**: African markets not supported
   - Different liquidity norms would require separate thresholds

---

## Testing

Run the test suite:

```bash
# From project root
pytest tests/test_longterm_scoring.py -v
```

Key test cases:
- `test_microcap_illiquid_is_capped`: Verifies caps work
- `test_largecap_good_fundamentals_scores_high`: Quality assets rank high
- `test_missing_fundamentals_low_confidence_penalizes`: Incomplete data penalized
- `test_no_crash_with_empty_data`: Robustness check

---

## Architecture

```
pipeline/scoring_longterm.py    # Core scoring logic
├── compute_longterm_score()    # Main entry point
├── compute_*_pillar()          # 5 pillar functions
├── compute_lt_confidence()     # Data quality assessment
└── apply_institutional_caps()  # Cap enforcement

pipeline/rotation.py            # Integration point
├── run_longterm flag
└── calls compute_longterm_score after existing scoring

storage/sqlite_store.py         # Persistence
├── ensure_longterm_schema()
├── upsert_longterm_score()
└── get_top_longterm_scores()

backend/api_routes.py           # API exposure
├── AssetResponse.lt_score/lt_confidence
└── AssetDetailResponse.lt_breakdown
```

---

## Summary

The LT Score provides a robust, institutional-grade ranking that:

✅ **Prevents illiquid assets from inflating** through hard caps  
✅ **Rewards quality fundamentals** with 35% weight on Quality pillar  
✅ **Penalizes incomplete data** through confidence scoring  
✅ **Maintains backward compatibility** as an opt-in add-on  
✅ **Provides full transparency** via detailed breakdown JSON
