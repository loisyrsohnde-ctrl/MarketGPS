# MarketGPS News Module (Actualités)

## Overview

The News module provides a curated feed of African Fintech & Startup news, automatically aggregated from 80+ sources, translated to French, and displayed with TL;DR summaries.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           NEWS PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌───────────┐ │
│  │   Sources   │───▶│   Ingest    │───▶│   Rewrite   │───▶│  Publish  │ │
│  │  Registry   │    │   (RSS)     │    │ (Translate) │    │  (SQLite) │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └───────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND API                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  GET  /api/news           - List articles (paginated, filterable)       │
│  GET  /api/news/{slug}    - Get single article                          │
│  POST /api/news/{id}/save - Save article                                │
│  DEL  /api/news/{id}/save - Unsave article                              │
│  GET  /api/news/saved     - Get user's saved articles                   │
│  GET  /api/news/tags      - Get available tags                          │
│  GET  /api/news/countries - Get available countries                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND PAGES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  /news           - News feed with filters                               │
│  /news/{slug}    - Article detail with TL;DR, share, save               │
│  /news/saved     - User's saved articles                                │
└─────────────────────────────────────────────────────────────────────────┘
```

## Database Tables

All tables are created with `CREATE TABLE IF NOT EXISTS` for safe, additive migrations.

| Table | Purpose |
|-------|---------|
| `news_sources` | Registry of news sources (RSS feeds, websites) |
| `news_raw_items` | Raw fetched items before processing |
| `news_articles` | Processed articles ready for display |
| `news_user_saves` | User-saved articles |
| `news_fetch_log` | Fetch operation logs |

## Pipeline Commands

```bash
# Run RSS ingestion (fetch new items from sources)
python -m pipeline.jobs --news-ingest

# Process and publish pending articles (with translation if LLM available)
python -m pipeline.jobs --news-rewrite

# Run full pipeline (ingest + rewrite)
python -m pipeline.jobs --news-full

# With item limit (for testing)
python -m pipeline.jobs --news-full --news-limit 10
```

## Adding New Sources

Edit `pipeline/news/sources_registry.json`:

```json
{
  "name": "Source Name",
  "url": "https://example.com",
  "rss_url": "https://example.com/feed/",
  "type": "rss",
  "country": "NG",
  "language": "en",
  "tags": ["fintech", "startup"],
  "trust_score": 0.8,
  "enabled": true
}
```

### Source Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `url` | Yes | Base URL (unique identifier) |
| `rss_url` | For RSS | RSS/Atom feed URL |
| `type` | No | `rss` (default), `html`, or `api` |
| `country` | No | ISO country code (NG, ZA, KE, etc.) |
| `language` | No | `en` or `fr` (default: en) |
| `tags` | No | Array of topic tags |
| `trust_score` | No | 0.0 to 1.0 (default: 0.7) |
| `enabled` | No | true/false (default: false) |

## Translation/Rewriting

The pipeline supports two modes:

### With LLM (Full Mode)
When `GEMINI_API_KEY` or `OPENAI_API_KEY` is set:
- Detects source language
- Translates to French
- Rewrites to avoid plagiarism
- Generates TL;DR (3 bullet points)
- Extracts tags

### Fallback Mode
Without LLM credentials:
- Extracts and cleans content
- Stores as-is (no translation)
- Still functional, just not French

## Scheduling (Production)

Add to your cron or scheduler:

```bash
# Every 2 hours: full news pipeline
0 */2 * * * cd /app && python -m pipeline.jobs --news-full --news-limit 100

# Or via Docker
docker exec marketgps-backend python -m pipeline.jobs --news-full
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | For Gemini-based translation (preferred) |
| `GOOGLE_API_KEY` | Alternative Gemini key |
| `OPENAI_API_KEY` | OpenAI fallback for translation |

## Smoke Test

Run the smoke test to verify the module:

```bash
# Default (API at localhost:8000)
./scripts/smoke_news.sh

# Custom API URL
API_BASE=https://api.marketgps.online ./scripts/smoke_news.sh
```

## API Response Examples

### GET /api/news

```json
{
  "data": [
    {
      "id": 1,
      "slug": "flutterwave-leve-250m-series-d-abc123",
      "title": "Flutterwave lève 250M$ en Série D",
      "excerpt": "La fintech nigériane Flutterwave annonce...",
      "tldr": [
        "Levée de 250M$ valorisant la société à 3B$",
        "Focus sur l'expansion pan-africaine",
        "Nouveaux produits de paiement B2B prévus"
      ],
      "tags": ["fintech", "vc", "payments"],
      "country": "NG",
      "source_name": "TechCabal",
      "published_at": "2026-01-24T10:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### GET /api/news/{slug}

```json
{
  "id": 1,
  "slug": "flutterwave-leve-250m-series-d-abc123",
  "title": "Flutterwave lève 250M$ en Série D",
  "excerpt": "...",
  "content_md": "La fintech nigériane Flutterwave a annoncé...",
  "tldr": ["...", "...", "..."],
  "tags": ["fintech", "vc"],
  "country": "NG",
  "language": "fr",
  "image_url": "https://...",
  "source_name": "TechCabal",
  "source_url": "https://techcabal.com/...",
  "published_at": "2026-01-24T10:00:00",
  "view_count": 42,
  "is_saved": false
}
```

## Troubleshooting

### No articles appearing

1. Check sources are enabled in `sources_registry.json`
2. Run ingestion manually: `python -m pipeline.jobs --news-ingest --news-limit 5`
3. Check for errors in logs
4. Verify RSS URLs are accessible

### Translation not working

1. Verify LLM API key is set: `echo $GEMINI_API_KEY`
2. Check pipeline logs for "Using Gemini" or "fallback mode"
3. Install required packages: `pip install google-generativeai openai`

### Database errors

1. Tables are auto-created on first run
2. Force recreation: Delete `data/sqlite/*.db` and restart

## Files Reference

```
backend/
├── news_routes.py          # FastAPI router

frontend/app/news/
├── page.tsx                 # Feed listing
├── [slug]/page.tsx          # Article detail
└── saved/page.tsx           # Saved articles

pipeline/news/
├── __init__.py
├── sources_registry.json    # 80+ African news sources
├── ingest_rss.py            # RSS fetcher
└── publish.py               # Translation & publishing

storage/migrations/
└── add_news_tables.sql      # Database schema

scripts/
└── smoke_news.sh            # Smoke test
```
