"""
MarketGPS News Pipeline - RSS Ingester

Fetches articles from RSS/Atom feeds and stores them in the database.
Handles deduplication via content hash.
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import feedparser
except ImportError:
    feedparser = None
    
import requests

from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# Constants
USER_AGENT = "MarketGPS/1.0 (+https://marketgps.online; news-aggregator)"
REQUEST_TIMEOUT = 15
MAX_WORKERS = 5
RATE_LIMIT_DELAY = 0.5  # seconds between requests to same domain


class RSSIngester:
    """RSS/Atom feed ingester for news sources."""
    
    def __init__(self, store: Optional[SQLiteStore] = None):
        """Initialize the ingester."""
        self.store = store or SQLiteStore()
        self.store._ensure_news_tables()
        self._load_sources()
        
    def _load_sources(self):
        """Load sources from registry and database."""
        registry_path = Path(__file__).parent / "sources_registry.json"
        
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Sync sources to database
            for source in data.get("sources", []):
                if source.get("enabled", False):
                    self.store.upsert_news_source({
                        "name": source["name"],
                        "url": source["url"],
                        "type": source.get("type", "rss"),
                        "rss_url": source.get("rss_url"),
                        "country": source.get("country"),
                        "language": source.get("language", "en"),
                        "tags": json.dumps(source.get("tags", [])),
                        "trust_score": source.get("trust_score", 0.7),
                        "enabled": 1 if source.get("enabled", False) else 0
                    })
            
            logger.info(f"Loaded {len(data.get('sources', []))} sources from registry")
    
    def _compute_hash(self, url: str, title: str) -> str:
        """Compute content hash for deduplication."""
        content = f"{url}|{title[:100] if title else ''}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _parse_date(self, entry: Dict) -> Optional[str]:
        """Parse date from feed entry."""
        # Try common date fields
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    dt = datetime(*getattr(entry, field)[:6])
                    return dt.isoformat()
                except:
                    pass
        
        # Try string dates
        for field in ['published', 'updated', 'created']:
            if hasattr(entry, field) and getattr(entry, field):
                return str(getattr(entry, field))
        
        return None
    
    def _fetch_feed(self, source: Dict) -> Dict:
        """Fetch and parse a single RSS feed."""
        source_id = source["id"]
        rss_url = source.get("rss_url") or source.get("url")
        source_name = source["name"]
        
        if not rss_url:
            return {"source_id": source_id, "items": 0, "new": 0, "errors": 0, "error": "No RSS URL"}
        
        if feedparser is None:
            return {"source_id": source_id, "items": 0, "new": 0, "errors": 0, "error": "feedparser not installed"}
        
        try:
            # Fetch with custom headers
            response = requests.get(
                rss_url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo and not feed.entries:
                error = str(feed.bozo_exception) if hasattr(feed, 'bozo_exception') else "Parse error"
                self.store.update_source_fetch_status(source_id, error=error)
                return {"source_id": source_id, "items": 0, "new": 0, "errors": 1, "error": error}
            
            items_count = 0
            new_count = 0
            
            for entry in feed.entries[:50]:  # Limit to 50 most recent
                try:
                    url = entry.get('link', '')
                    title = entry.get('title', '')
                    
                    if not url or not title:
                        continue
                    
                    content_hash = self._compute_hash(url, title)
                    published_at = self._parse_date(entry)
                    
                    # Prepare raw payload
                    raw_payload = json.dumps({
                        "title": title,
                        "link": url,
                        "summary": entry.get('summary', ''),
                        "content": entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                        "author": entry.get('author', ''),
                        "tags": [t.get('term', '') for t in entry.get('tags', [])],
                        "published": published_at,
                        "source": source_name
                    }, ensure_ascii=False)
                    
                    # Insert raw item (will be ignored if duplicate)
                    result = self.store.insert_news_raw_item({
                        "source_id": source_id,
                        "url": url,
                        "title": title,
                        "published_at": published_at,
                        "raw_payload": raw_payload,
                        "content_hash": content_hash
                    })
                    
                    items_count += 1
                    if result:
                        new_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {e}")
            
            # Update source status
            self.store.update_source_fetch_status(source_id, error=None)
            
            return {
                "source_id": source_id,
                "source_name": source_name,
                "items": items_count,
                "new": new_count,
                "errors": 0
            }
            
        except requests.RequestException as e:
            error = f"HTTP error: {str(e)[:100]}"
            self.store.update_source_fetch_status(source_id, error=error)
            return {"source_id": source_id, "items": 0, "new": 0, "errors": 1, "error": error}
        except Exception as e:
            error = f"Error: {str(e)[:100]}"
            self.store.update_source_fetch_status(source_id, error=error)
            return {"source_id": source_id, "items": 0, "new": 0, "errors": 1, "error": error}
    
    def run(self, limit: Optional[int] = None) -> Dict:
        """
        Run the RSS ingestion job.
        
        Args:
            limit: Maximum number of sources to fetch (for testing)
            
        Returns:
            Summary statistics
        """
        logger.info("Starting RSS ingestion...")
        start_time = time.time()
        
        # Get enabled RSS sources
        sources = self.store.get_news_sources(enabled_only=True)
        rss_sources = [s for s in sources if s.get("type") == "rss" and s.get("rss_url")]
        
        if limit:
            rss_sources = rss_sources[:limit]
        
        logger.info(f"Found {len(rss_sources)} RSS sources to fetch")
        
        results = {
            "sources_total": len(rss_sources),
            "sources_success": 0,
            "sources_error": 0,
            "items_fetched": 0,
            "items_new": 0,
            "errors": []
        }
        
        # Fetch feeds in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self._fetch_feed, source): source for source in rss_sources}
            
            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    results["items_fetched"] += result.get("items", 0)
                    results["items_new"] += result.get("new", 0)
                    
                    if result.get("errors", 0) > 0:
                        results["sources_error"] += 1
                        results["errors"].append({
                            "source": source["name"],
                            "error": result.get("error", "Unknown")
                        })
                    else:
                        results["sources_success"] += 1
                        
                except Exception as e:
                    results["sources_error"] += 1
                    results["errors"].append({
                        "source": source["name"],
                        "error": str(e)
                    })
                    logger.error(f"Error fetching {source['name']}: {e}")
        
        elapsed = time.time() - start_time
        results["elapsed_seconds"] = round(elapsed, 2)
        
        logger.info(
            f"RSS ingestion complete: {results['sources_success']}/{results['sources_total']} sources, "
            f"{results['items_new']} new items in {elapsed:.1f}s"
        )
        
        return results


def run_ingest(limit: Optional[int] = None) -> Dict:
    """Entry point for pipeline.jobs integration."""
    ingester = RSSIngester()
    return ingester.run(limit=limit)


if __name__ == "__main__":
    # Test run
    result = run_ingest(limit=5)
    print(json.dumps(result, indent=2))
