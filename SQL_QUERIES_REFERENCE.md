# Francophone Filtering - SQL Queries Reference

Quick reference for common queries to monitor and debug the filtering system.

## 1. TODAY'S TOP 20 ARTICLES

### Get today's complete TOP 20
```sql
SELECT
    dtp.rank,
    na.title,
    na.source_name,
    na.country,
    dtp.francophone_relevance_score,
    na.total_interactions,
    na.published_at,
    na.is_featured
FROM francophone_daily_top20 dtp
JOIN news_articles na ON dtp.article_id = na.id
WHERE dtp.date = date('now')
ORDER BY dtp.rank ASC;
```

### Get yesterday's TOP 20
```sql
SELECT
    dtp.rank,
    na.title,
    dtp.francophone_relevance_score,
    na.total_interactions
FROM francophone_daily_top20 dtp
JOIN news_articles na ON dtp.article_id = na.id
WHERE dtp.date = date('now', '-1 day')
ORDER BY dtp.rank ASC;
```

### Top 3 articles (current rankings)
```sql
SELECT
    rank,
    title,
    source_name,
    francophone_relevance_score,
    total_interactions
FROM news_articles
WHERE daily_rank <= 3 AND daily_rank IS NOT NULL
ORDER BY daily_rank ASC;
```

## 2. SOURCE METRICS & QUALIFICATION

### Show all sources with median thresholds
```sql
SELECT
    smc.source_name,
    smc.country,
    smc.language,
    smc.total_articles,
    ROUND(smc.median_interactions, 1) as median,
    ROUND(smc.median_interactions * 2, 1) as threshold_2x,
    smc.articles_above_2x_median as qualified,
    ROUND(100.0 * smc.articles_above_2x_median / smc.total_articles, 1) as pct_qualified
FROM source_metrics_cache smc
WHERE smc.calculation_date = (
    SELECT MAX(calculation_date) FROM source_metrics_cache
)
ORDER BY smc.median_interactions DESC;
```

### Sources with lowest qualification rates
```sql
SELECT
    source_name,
    total_articles,
    articles_above_2x_median,
    ROUND(100.0 * articles_above_2x_median / total_articles, 1) as pct_qualified,
    ROUND(median_interactions, 1) as median
FROM source_metrics_cache
WHERE calculation_date = (SELECT MAX(calculation_date) FROM source_metrics_cache)
ORDER BY pct_qualified ASC
LIMIT 10;
```

### Articles from a specific source
```sql
SELECT
    title,
    total_interactions,
    francophone_relevance_score,
    published_at
FROM news_articles
WHERE source_name = 'TechCabal'
AND status = 'published'
ORDER BY published_at DESC
LIMIT 20;
```

## 3. SCORING COMPONENT ANALYSIS

### View score components for top articles
```sql
SELECT
    title,
    ROUND(francophone_relevance_score, 1) as final_score,
    ROUND(interaction_score, 1) as interact,
    ROUND(language_score, 1) as lang,
    ROUND(region_score, 1) as region,
    ROUND(recency_score, 1) as recency,
    ROUND(topic_score, 1) as topic
FROM news_articles
WHERE status = 'published'
AND francophone_relevance_score > 0
ORDER BY francophone_relevance_score DESC
LIMIT 10;
```

### Find articles with low interaction scores
```sql
SELECT
    title,
    source_name,
    total_interactions,
    interaction_score,
    francophone_relevance_score
FROM news_articles
WHERE interaction_score < 30 AND status = 'published'
ORDER BY interaction_score ASC
LIMIT 20;
```

### Articles with high recency but low score
```sql
SELECT
    title,
    recency_score,
    francophone_relevance_score,
    published_at,
    total_interactions
FROM news_articles
WHERE recency_score > 80
AND francophone_relevance_score < 50
AND status = 'published'
ORDER BY published_at DESC
LIMIT 10;
```

### Topics representation in TOP 20
```sql
SELECT
    topic_score,
    COUNT(*) as count,
    AVG(francophone_relevance_score) as avg_score
FROM news_articles na
WHERE daily_rank IS NOT NULL AND daily_rank <= 20
GROUP BY topic_score
ORDER BY topic_score DESC;
```

## 4. FEATURED ARTICLES

### Show all featured articles
```sql
SELECT
    title,
    source_name,
    francophone_relevance_score,
    total_interactions,
    is_featured,
    daily_rank
FROM news_articles
WHERE is_featured = 1
AND status = 'published'
ORDER BY francophone_relevance_score DESC;
```

### Featured articles in TOP 20
```sql
SELECT
    title,
    source_name,
    francophone_relevance_score,
    total_interactions,
    daily_rank
FROM news_articles
WHERE is_featured = 1
AND daily_rank IS NOT NULL
AND daily_rank <= 20
ORDER BY daily_rank ASC;
```

### Featured articles NOT in TOP 20
```sql
SELECT
    title,
    source_name,
    francophone_relevance_score,
    total_interactions
FROM news_articles
WHERE is_featured = 1
AND (daily_rank IS NULL OR daily_rank > 20)
AND status = 'published'
ORDER BY francophone_relevance_score DESC;
```

## 5. FILTERING STATISTICS & LOGS

### Daily filtering statistics (last 30 days)
```sql
SELECT
    date,
    articles_analyzed,
    articles_qualified,
    articles_top20,
    featured_count,
    ROUND(avg_relevance_score, 1) as avg_score,
    status
FROM francophone_filter_log
ORDER BY date DESC
LIMIT 30;
```

### Filtering success rate trend
```sql
SELECT
    date,
    CASE WHEN status = 'success' THEN 1 ELSE 0 END as successful,
    articles_top20,
    ROUND(avg_relevance_score, 1) as avg_score
FROM francophone_filter_log
WHERE date >= date('now', '-7 days')
ORDER BY date DESC;
```

### Days with low average relevance
```sql
SELECT
    date,
    articles_top20,
    ROUND(avg_relevance_score, 1) as avg_score,
    featured_count
FROM francophone_filter_log
WHERE avg_relevance_score < 70
ORDER BY avg_relevance_score ASC;
```

## 6. LANGUAGE & REGION DISTRIBUTION

### Language distribution in TOP 20
```sql
SELECT
    language,
    COUNT(*) as count,
    ROUND(AVG(francophone_relevance_score), 1) as avg_score
FROM news_articles na
WHERE daily_rank IS NOT NULL AND daily_rank <= 20
GROUP BY language
ORDER BY count DESC;
```

### Country distribution in TOP 20
```sql
SELECT
    country,
    COUNT(*) as count,
    ROUND(AVG(francophone_relevance_score), 1) as avg_score,
    ROUND(AVG(region_score), 1) as avg_region_score
FROM news_articles na
WHERE daily_rank IS NOT NULL AND daily_rank <= 20
GROUP BY country
ORDER BY count DESC;
```

### Francophone vs non-francophone articles
```sql
SELECT
    CASE
        WHEN country IN ('SN', 'CI', 'CM', 'ML', 'BF', 'NE', 'TG', 'BJ', 'GN', 'GA', 'CG', 'CD')
        THEN 'Francophone Africa'
        WHEN country IN ('FR', 'BE', 'CH', 'CA')
        THEN 'Developed Francophone'
        ELSE 'Other'
    END as region_type,
    COUNT(*) as count,
    ROUND(AVG(francophone_relevance_score), 1) as avg_score,
    ROUND(AVG(total_interactions), 0) as avg_interactions
FROM news_articles
WHERE daily_rank IS NOT NULL AND daily_rank <= 20
GROUP BY region_type;
```

## 7. RECENCY ANALYSIS

### Articles by age in TOP 20
```sql
SELECT
    ROUND((julianday('now') - julianday(published_at)) * 24) as hours_old,
    COUNT(*) as count,
    ROUND(AVG(francophone_relevance_score), 1) as avg_score
FROM news_articles
WHERE daily_rank IS NOT NULL AND daily_rank <= 20
GROUP BY hours_old
ORDER BY hours_old ASC;
```

### Most recent articles in last 24 hours
```sql
SELECT
    title,
    source_name,
    published_at,
    recency_score,
    francophone_relevance_score,
    daily_rank
FROM news_articles
WHERE published_at >= datetime('now', '-24 hours')
AND status = 'published'
AND language = 'fr'
ORDER BY published_at DESC
LIMIT 20;
```

## 8. INTERACTION ANALYSIS

### Articles above and below 2x median
```sql
SELECT
    source_name,
    COUNT(*) as total,
    SUM(CASE WHEN (
        SELECT median_interactions FROM source_metrics_cache
        WHERE source_name = news_articles.source_name
        LIMIT 1
    ) IS NOT NULL AND total_interactions > (
        SELECT median_interactions * 2 FROM source_metrics_cache
        WHERE source_name = news_articles.source_name
        LIMIT 1
    ) THEN 1 ELSE 0 END) as above_2x,
    ROUND(AVG(total_interactions), 0) as avg_interactions
FROM news_articles
WHERE status = 'published'
AND language = 'fr'
GROUP BY source_name
ORDER BY source_name;
```

### Interaction distribution
```sql
SELECT
    CASE
        WHEN total_interactions < 50 THEN '0-50'
        WHEN total_interactions < 100 THEN '50-100'
        WHEN total_interactions < 250 THEN '100-250'
        WHEN total_interactions < 500 THEN '250-500'
        ELSE '500+'
    END as interaction_range,
    COUNT(*) as count,
    ROUND(AVG(francophone_relevance_score), 1) as avg_score
FROM news_articles
WHERE status = 'published' AND language = 'fr'
GROUP BY interaction_range
ORDER BY MIN(total_interactions) ASC;
```

## 9. SCORE RECALCULATION STATUS

### When were scores last calculated?
```sql
SELECT
    MAX(score_calculated_at) as last_calculation,
    COUNT(*) as articles_with_scores,
    MIN(francophone_relevance_score) as min_score,
    MAX(francophone_relevance_score) as max_score,
    ROUND(AVG(francophone_relevance_score), 1) as avg_score
FROM news_articles
WHERE francophone_relevance_score > 0;
```

### Articles not yet scored
```sql
SELECT
    COUNT(*) as unscored_articles
FROM news_articles
WHERE (francophone_relevance_score IS NULL OR francophone_relevance_score = 0)
AND status = 'published'
AND language = 'fr';
```

### Score calculation progress
```sql
SELECT
    (SELECT COUNT(*) FROM news_articles WHERE francophone_relevance_score > 0) as scored,
    (SELECT COUNT(*) FROM news_articles WHERE francophone_relevance_score = 0) as unscored,
    (SELECT COUNT(*) FROM news_articles) as total,
    ROUND(100.0 * (SELECT COUNT(*) FROM news_articles WHERE francophone_relevance_score > 0) /
          (SELECT COUNT(*) FROM news_articles), 1) as pct_scored;
```

## 10. COMPARISON & TREND ANALYSIS

### TOP 20 comparison: today vs yesterday
```sql
SELECT
    dtp_today.rank as today_rank,
    COALESCE(dtp_yesterday.rank, 'NEW') as yesterday_rank,
    na.title,
    ROUND(dtp_today.francophone_relevance_score, 1) as today_score,
    ROUND(COALESCE(dtp_yesterday.francophone_relevance_score, 0), 1) as yesterday_score
FROM francophone_daily_top20 dtp_today
JOIN news_articles na ON dtp_today.article_id = na.id
LEFT JOIN francophone_daily_top20 dtp_yesterday ON
    dtp_today.article_id = dtp_yesterday.article_id
    AND dtp_yesterday.date = date('now', '-1 day')
WHERE dtp_today.date = date('now')
ORDER BY dtp_today.rank ASC;
```

### Average score trend (last 7 days)
```sql
SELECT
    date,
    ROUND(avg_relevance_score, 1) as avg_score,
    articles_top20,
    featured_count
FROM francophone_filter_log
WHERE date >= date('now', '-7 days')
ORDER BY date DESC;
```

## 11. DATA QUALITY CHECKS

### Articles with zero interactions in TOP 20
```sql
SELECT
    title,
    source_name,
    total_interactions,
    francophone_relevance_score
FROM news_articles
WHERE daily_rank IS NOT NULL
AND total_interactions = 0
ORDER BY francophone_relevance_score DESC;
```

### Orphaned daily rank entries
```sql
SELECT
    na.id,
    na.title,
    na.daily_rank,
    na.status
FROM news_articles na
WHERE na.daily_rank IS NOT NULL
AND (na.status != 'published' OR na.language != 'fr');
```

### Score consistency check
```sql
SELECT
    COUNT(*) as issues
FROM news_articles
WHERE francophone_relevance_score > 0
AND (
    interaction_score < 0 OR interaction_score > 100 OR
    language_score < 0 OR language_score > 100 OR
    region_score < 0 OR region_score > 100 OR
    recency_score < 0 OR recency_score > 100 OR
    topic_score < 0 OR topic_score > 100
);
```

## 12. ADMIN OPERATIONS

### Clear all featured flags
```sql
UPDATE news_articles SET is_featured = 0 WHERE is_featured = 1;
```

### Reset daily rankings
```sql
UPDATE news_articles SET daily_rank = NULL WHERE daily_rank IS NOT NULL;
```

### Bulk recalculate scores from scratch
```sql
UPDATE news_articles
SET francophone_relevance_score = NULL,
    score_calculated_at = NULL,
    interaction_score = NULL,
    language_score = NULL,
    region_score = NULL,
    recency_score = NULL,
    topic_score = NULL
WHERE status = 'published';
```

### Archive old filtering logs (keep last 180 days)
```sql
DELETE FROM francophone_filter_log
WHERE date < date('now', '-180 days');
```

### Archive old daily rankings (keep last 90 days)
```sql
DELETE FROM francophone_daily_top20
WHERE date < date('now', '-90 days');
```

---

**Tips:**
- Use `ROUND(value, 1)` for cleaner output
- Remember `date('now')` for today and `date('now', '-N days')` for past dates
- Always filter by `status = 'published'` for real articles
- Use `daily_rank IS NOT NULL` to find articles currently in TOP 20
- Check `score_calculated_at` to ensure scores are fresh
