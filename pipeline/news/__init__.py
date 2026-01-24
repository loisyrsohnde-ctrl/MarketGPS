"""
MarketGPS News Pipeline Module

This module handles:
- Ingestion from RSS feeds and web scraping
- Content extraction and cleaning
- Translation and rewriting to French
- Publishing to the database

Usage via CLI:
    python -m pipeline.jobs --news-ingest
    python -m pipeline.jobs --news-rewrite
    python -m pipeline.jobs --news-full
"""

from .ingest_rss import RSSIngester
from .publish import NewsPublisher

__all__ = ["RSSIngester", "NewsPublisher"]
