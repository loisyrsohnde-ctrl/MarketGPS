# Francophone Article Filtering System - TOP 20 Daily Selection

## Overview

The Francophone Filtering Service implements strict filtering to display only the **TOP 20 most relevant** francophone articles per day. This eliminates noise and ensures content is highly focused on the francophone audience's needs.

## Key Features

### 1. Multi-Dimensional Relevance Scoring (0-100)

Articles are scored across 5 components, each 0-100:

- **Interaction Score (35% weight)**: Relative to source median interactions
  - Must exceed 2x source median to qualify (unless featured)
  - Scoring: interactions / median interactions, capped at 100

- **Language Score (20% weight)**: Prioritize French language
  - French (fr) = 100
  - Translated/bilingual (en, es, pt) = 50
  - Other languages = 25

- **Region Score (20% weight)**: Geographic relevance to francophone world
  - Francophone Africa (SN, CI, CM, ML, BF, NE, TG, BJ, GN, GA, CG, CD) = 100
  - Developed francophone (FR, BE, CH, CA) = 85
  - North Africa (MA, TN, DZ) = 70
  - Other = 40

- **Recency Score (15% weight)**: Publication freshness
  - < 1 hour = 100
  - < 6 hours = 90
  - < 24 hours = 75
  - < 48 hours = 50
  - Older = 25

- **Topic Score (10% weight)**: Content relevance
  - Finance, economy, tech, business, startup keywords = 100
  - 2 relevant keywords = 80
  - 1 relevant keyword = 60
  - No keywords = 40

### 2. Median-Based Qualification

**Selection Rule**: Articles must have interactions > 2x source median

- Prevents popular sources from dominating
- Ensures each source contributes quality content
- Featured articles bypass this rule

### 3. Featured Article Override

Manually mark articles as "featured" to:
- Ignore the 2x median threshold
- Receive 1.5x relevance score boost
- Always appear in TOP 20

### 4. Daily TOP 20 Selection

Process:
1. Analyze all articles from last 24-48 hours
2. Calculate source metrics (median, average interactions)
3. Score each article across 5 dimensions
4. Filter: language=fr AND interactions > 2x median (or featured)
5. Sort by combined relevance score
6. Take top 20 articles
7. Store in `francophone_daily_top20` table for historical reference

## Database Schema

### New Columns in `news_articles`

```sql
-- Francophone filtering columns
francophone_relevance_score REAL      -- Final 0-100 score
is_featured INTEGER                    -- Manual override flag
interaction_score REAL                 -- Component: interactions relative to median
language_score REAL                    -- Component: language preference
region_score REAL                      -- Component: regional relevance
recency_score REAL                     -- Component: publication freshness
topic_score REAL                       -- Component: topic relevance
daily_rank INTEGER                     -- 1-20 position in daily top 20
score_calculated_at TEXT               -- Last calculation timestamp
```

### New Tables

**`francophone_daily_top20`**: Historical record of daily TOP 20 selections
- Immutable audit trail
- Indexed by date for fast historical queries
- Stores all component scores

**`source_metrics_cache`**: Source statistics cache
- Speeds up filtering (avoids recalculating median each run)
- Updated daily
- Indexed by calculation date

**`francophone_filter_log`**: Filtering run statistics
- Tracks daily filtering execution
- Records qualifications and rejections
- Useful for monitoring and debugging

## API Endpoints

### 1. GET `/api/viral-news/francophone/top20`

Get the TOP 20 francophone articles for today (or specified days).

**Parameters:**
- `days` (int, 1-7): Number of days to analyze (default: 1)

**Response:**
```json
{
  "date": "2026-02-09",
  "articles": [
    {
      "article_id": 123,
      "title": "Article Title",
      "source_name": "Source Name",
      "country": "SN",
      "language": "fr",
      "total_interactions": 250,
      "published_at": "2026-02-09T10:30:00",
      "url": "https://...",
      "interaction_score": 85.5,
      "language_score": 100.0,
      "region_score": 100.0,
      "recency_score": 95.0,
      "topic_score": 80.0,
      "francophone_relevance_score": 92.3,
      "is_featured": false,
      "rank": 1
    }
    // ... 19 more articles
  ],
  "total_articles_analyzed": 245,
  "articles_qualified": 42,
  "featured_count": 2,
  "avg_relevance_score": 78.5
}
```

### 2. GET `/api/viral-news/francophone/source-metrics`

Get source statistics needed for understanding the 2x median threshold.

**Parameters:**
- `days` (int, 7-90): Number of days to analyze (default: 30)

**Response:**
```json
{
  "TechCabal": {
    "source_name": "TechCabal",
    "country": "NG",
    "language": "en",
    "total_articles": 45,
    "median_interactions": 125.0,
    "avg_interactions": 180.5,
    "articles_above_2x_median": 8
  },
  "Jeune Afrique": {
    "source_name": "Jeune Afrique",
    "country": "FR",
    "language": "fr",
    "total_articles": 62,
    "median_interactions": 95.0,
    "avg_interactions": 140.2,
    "articles_above_2x_median": 15
  }
  // ... more sources
}
```

### 3. POST `/api/viral-news/francophone/mark-featured`

Mark an article as featured (manual override).

**Request:**
```json
{
  "article_id": 123,
  "featured": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Article 123 marked as featured",
  "article_id": 123,
  "featured": true
}
```

### 4. POST `/api/viral-news/francophone/recalculate-scores`

Recalculate francophone relevance scores for all articles.

**Use cases:**
- Daily scheduled task
- After adding important articles
- After parameter adjustments
- On-demand by administrators

**Response:**
```json
{
  "success": true,
  "message": "Francophone relevance scores recalculated",
  "timestamp": "2026-02-09T15:30:00"
}
```

### 5. GET `/api/viral-news/viral` (Updated)

Enhanced endpoint with strict filtering support.

**Parameters:**
- `strict` (bool): Use strict TOP 20 filtering (default: true)
- `limit` (int): Max articles to return (1-100, default: 20)
- `francophone_only` (bool): Filter to francophone sources only
- `min_virality` (float): Minimum virality score (for non-strict mode)
- `days` (int): Days to analyze (1-30, default: 7)

**When `strict=true`:**
- Returns TOP 20 using francophone filtering
- Ignores `min_virality` parameter
- Capped at 2 days lookback (more recent articles)

**When `strict=false`:**
- Uses original virality rules
- Backward compatible with existing integrations
- Respects all filtering parameters

## Integration Guide

### Step 1: Run Database Migration

```bash
sqlite3 your_database.db < backend/migrations/003_francophone_filtering.sql
```

This adds:
- New columns to `news_articles`
- New tables for tracking and history
- Indexes for fast queries

### Step 2: Import the Service

```python
from services.francophone_filter_service import FrancophonicFilterService

# Initialize
filter_svc = FrancophonicFilterService(db_conn=get_db_connection)
```

### Step 3: Calculate Initial Scores

```python
# Run once to populate all francophone_relevance_score values
filter_svc.calculate_and_store_scores()
```

### Step 4: Get Daily TOP 20

```python
# Get today's top 20
articles = filter_svc.get_daily_top_20(days=1)

for article in articles:
    print(f"#{article.rank}: {article.title}")
    print(f"  Score: {article.francophone_relevance_score:.1f}")
    print(f"  Interactions: {article.total_interactions}")
```

### Step 5: Mark Featured Articles (Optional)

```python
# Manually feature an important article
filter_svc.mark_article_as_featured(article_id=456)

# Unmark if needed
filter_svc.unmark_article_as_featured(article_id=456)
```

### Step 6: Schedule Daily Recalculation

```python
# Add to your scheduler (e.g., APScheduler, Celery, Airflow)
@scheduled_job('cron', hour=0, minute=0)  # Daily at midnight
def daily_francophone_scoring():
    filter_svc = FrancophonicFilterService(db_conn=get_db_connection)
    filter_svc.calculate_and_store_scores()
    logger.info("Daily francophone scoring complete")
```

## Scoring Algorithm Details

### Combined Score Calculation

```
francophone_relevance_score = (
    interaction_score × 0.35 +
    language_score × 0.20 +
    region_score × 0.20 +
    recency_score × 0.15 +
    topic_score × 0.10
)

# If featured, apply boost
if is_featured:
    francophone_relevance_score *= 1.5
```

### Example Calculation

Article: "Nigeria's Fintech Revolution Reaches $500M"
- Source: TechCabal (median: 125 interactions)
- Actual interactions: 300
- Language: English (translated)
- Country: NG (Nigeria)
- Published: 3 hours ago
- Keywords: fintech, innovation, business

**Scores:**
- Interaction: (300/125) → 2.4x median → 75.0
- Language: English → 50.0
- Region: Nigeria (not francophone Africa) → 40.0
- Recency: 3 hours → 90.0
- Topic: 3 keywords → 100.0

**Final:**
```
(75.0 × 0.35) + (50.0 × 0.20) + (40.0 × 0.20) + (90.0 × 0.15) + (100.0 × 0.10)
= 26.25 + 10.0 + 8.0 + 13.5 + 10.0
= 67.75
```

## Francophone Regions

### High Priority (100 points)
**Sub-Saharan Francophone Africa:**
- SN (Senegal), CI (Côte d'Ivoire), CM (Cameroon)
- ML (Mali), BF (Burkina Faso), NE (Niger)
- TG (Togo), BJ (Benin), GN (Guinea)
- GA (Gabon), CG (Congo), CD (DRC)

### Second Priority (85 points)
**Developed Francophone:**
- FR (France), BE (Belgium)
- CH (Switzerland), CA (Canada)

### Third Priority (70 points)
**North Africa:**
- MA (Morocco), TN (Tunisia), DZ (Algeria)

## Monitoring & Debugging

### Check Qualification Rules

```python
# Get source metrics to understand 2x median threshold
metrics = filter_svc.get_source_metrics_report(days=30)

for source_name, stats in metrics.items():
    threshold = stats.median_interactions * 2
    print(f"{source_name}:")
    print(f"  Median: {stats.median_interactions:.0f}")
    print(f"  2x Threshold: {threshold:.0f}")
    print(f"  Articles qualified: {stats.articles_above_2x_median}/{stats.total_articles}")
```

### View Historical TOP 20

```sql
-- See yesterday's TOP 20
SELECT rank, title, francophone_relevance_score, total_interactions
FROM francophone_daily_top20
JOIN news_articles ON francophone_daily_top20.article_id = news_articles.id
WHERE francophone_daily_top20.date = date('now', '-1 day')
ORDER BY rank ASC;

-- See featured articles
SELECT title, francophone_relevance_score, is_featured
FROM news_articles
WHERE is_featured = 1 AND status = 'published'
ORDER BY francophone_relevance_score DESC;

-- See filtering statistics
SELECT date, articles_analyzed, articles_qualified, articles_top20, avg_relevance_score
FROM francophone_filter_log
ORDER BY date DESC
LIMIT 30;
```

## Troubleshooting

### Too Many Articles Not Qualifying

**Issue**: Few articles exceed the 2x median threshold

**Solution:**
- Check if sources are publishing low-engagement content
- Verify interaction data is being tracked properly
- Consider adjusting source weights if some sources are consistently low

### Featured Articles Not Appearing

**Issue**: Featured articles aren't in TOP 20

**Causes:**
- Article might not have `language='fr'` set
- Status might not be 'published'
- Refresh scores with `calculate_and_store_scores()`

### Scores Not Updating

**Issue**: Articles still show old francophone_relevance_score

**Solution:**
```python
# Force recalculation
filter_svc.calculate_and_store_scores()

# Verify in database
SELECT id, title, francophone_relevance_score, score_calculated_at
FROM news_articles
WHERE id = 123;
```

## Performance Considerations

### Indexing

The migration creates optimized indexes:
- Primary: `idx_news_articles_relevance` (score DESC + date DESC)
- Featured: `idx_news_articles_featured` (featured DESC + score DESC)
- Strict filter: `idx_news_articles_strict_filter` (language + status + score)

### Caching

Source metrics are cached in `source_metrics_cache` table:
- Avoids recalculating median each run
- Updated daily
- Expired after 30 days

### Query Performance

TOP 20 selection typically takes < 1 second:
- Queries limited to recent articles (24-48 hours)
- Indexed lookups on language and status
- In-memory sorting of candidate articles

## Future Enhancements

1. **Machine Learning Scoring**: Train model on engagement metrics
2. **A/B Testing**: Test different weight combinations
3. **User Preferences**: Personalized scoring based on user interests
4. **Topic Diversification**: Ensure varied topics in TOP 20
5. **Trending Detection**: Boost emerging trends earlier
6. **Multi-language Support**: Extend to English, Spanish, Portuguese

## Questions & Support

For issues or feature requests:
1. Check this documentation
2. Review `francophone_filter_log` for recent runs
3. Query `source_metrics_cache` for source statistics
4. Check article-level scores in `news_articles`
