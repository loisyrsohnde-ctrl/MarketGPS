"""
Real Estate News Provider
Fetches real news from multiple sources.

Sources:
- NewsAPI (with API key)
- RSS feeds from official sources
- Property news sites
"""

import os
import logging
import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict, field
import xml.etree.ElementTree as ET
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class NewsCategory(str, Enum):
    REGULATION = "regulation"
    RATES = "rates"
    MARKET = "market"
    LOCAL = "local"
    FISCAL = "fiscal"
    ENERGY = "energy"


class ImpactLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class NewsItem:
    """Real estate news item."""
    id: str
    title: str
    summary: str
    content: Optional[str]
    source: str
    source_url: Optional[str]
    published_at: str
    category: str
    impact_level: str
    impact_type: str  # positive, negative, neutral, mixed
    countries_affected: List[str]
    keywords: List[str] = field(default_factory=list)
    author: Optional[str] = None
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# RSS Feed Sources
# =============================================================================

RSS_FEEDS = {
    # French sources
    "FR": [
        {
            "url": "https://www.lesechos.fr/rss/immobilier.xml",
            "name": "Les Échos Immobilier",
            "category": "market",
        },
        {
            "url": "https://www.lefigaro.fr/rss/figaro_immobilier.xml",
            "name": "Le Figaro Immobilier",
            "category": "market",
        },
        {
            "url": "https://www.legifrance.gouv.fr/rss/lois.xml",
            "name": "Légifrance",
            "category": "regulation",
        },
    ],
    # European/ECB
    "EU": [
        {
            "url": "https://www.ecb.europa.eu/rss/press.html",
            "name": "ECB Press",
            "category": "rates",
        },
    ],
    # UK sources
    "UK": [
        {
            "url": "https://www.bankofengland.co.uk/rss/news",
            "name": "Bank of England",
            "category": "rates",
        },
    ],
    # US sources
    "US": [
        {
            "url": "https://www.federalreserve.gov/feeds/press_all.xml",
            "name": "Federal Reserve",
            "category": "rates",
        },
    ],
}

# Keywords for categorization
CATEGORY_KEYWORDS = {
    "regulation": [
        "loi", "décret", "réglementation", "législation", "law", "regulation",
        "directive", "ordonnance", "arrêté", "legal", "règlement", "norm",
        "LMNP", "Pinel", "PTZ", "DPE", "audit énergétique", "passoire thermique",
    ],
    "rates": [
        "taux", "rate", "BCE", "ECB", "Fed", "banque centrale", "central bank",
        "inflation", "monetary", "monétaire", "crédit", "emprunt", "mortgage",
        "refinancing", "refinancement", "interest", "intérêt",
    ],
    "fiscal": [
        "impôt", "taxe", "fiscal", "tax", "plus-value", "capital gains",
        "déduction", "deduction", "amortissement", "depreciation", "IFI",
        "droits de mutation", "stamp duty", "property tax", "taxe foncière",
    ],
    "energy": [
        "DPE", "énergie", "energy", "rénovation", "renovation", "isolation",
        "passoire", "climate", "carbone", "carbon", "green", "vert", "durable",
        "EPC", "energy performance", "thermique", "thermal",
    ],
    "market": [
        "prix", "price", "marché", "market", "transaction", "vente", "sale",
        "achat", "purchase", "investissement", "investment", "rendement", "yield",
        "loyer", "rent", "location", "vacancy", "vacance",
    ],
}


# =============================================================================
# News Provider
# =============================================================================

class RealEstateNewsProvider:
    """
    Provider for real estate news and market intelligence.
    Aggregates from multiple sources.
    """
    
    CACHE_TTL = 1800  # 30 minutes
    
    def __init__(self):
        self._cache: Dict[str, List[NewsItem]] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._newsapi_key = os.getenv("NEWSAPI_KEY")
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_time:
            return False
        return datetime.utcnow() - self._cache_time[key] < timedelta(seconds=self.CACHE_TTL)
    
    def _generate_id(self, title: str, source: str) -> str:
        """Generate unique ID for news item."""
        content = f"{title}:{source}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def get_news(
        self,
        countries: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[NewsItem]:
        """
        Get news from all sources.
        
        Args:
            countries: Filter by country codes (FR, US, UK, etc.)
            categories: Filter by category
            limit: Maximum number of items
            
        Returns:
            List of news items sorted by date
        """
        all_items: List[NewsItem] = []
        
        # Fetch from RSS feeds
        rss_items = await self._fetch_rss_feeds(countries or ["FR", "EU", "US", "UK"])
        all_items.extend(rss_items)
        
        # Fetch from NewsAPI if available
        if self._newsapi_key:
            api_items = await self._fetch_newsapi(countries or ["FR"])
            all_items.extend(api_items)
        
        # Filter by category
        if categories:
            all_items = [item for item in all_items if item.category in categories]
        
        # Sort by date (newest first)
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        
        # Remove duplicates based on title similarity
        unique_items = self._deduplicate(all_items)
        
        return unique_items[:limit]
    
    async def _fetch_rss_feeds(self, countries: List[str]) -> List[NewsItem]:
        """Fetch news from RSS feeds."""
        cache_key = f"rss_{'-'.join(sorted(countries))}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        items: List[NewsItem] = []
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for country in countries:
                feeds = RSS_FEEDS.get(country, [])
                
                for feed_config in feeds:
                    try:
                        response = await client.get(feed_config["url"])
                        if response.status_code == 200:
                            feed_items = self._parse_rss(
                                response.text,
                                feed_config["name"],
                                feed_config.get("category", "market"),
                                [country] if country != "EU" else ["FR", "DE", "BE", "ES", "IT"],
                            )
                            items.extend(feed_items)
                    except Exception as e:
                        logger.warning(f"Failed to fetch RSS {feed_config['url']}: {e}")
        
        self._cache[cache_key] = items
        self._cache_time[cache_key] = datetime.utcnow()
        
        return items
    
    def _parse_rss(
        self,
        xml_content: str,
        source_name: str,
        default_category: str,
        countries: List[str],
    ) -> List[NewsItem]:
        """Parse RSS/Atom feed XML."""
        items = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle RSS 2.0
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                
                if not title:
                    continue
                
                # Parse date
                parsed_date = self._parse_date(pub_date)
                
                # Determine category from content
                category = self._categorize_content(title + " " + description)
                if not category:
                    category = default_category
                
                # Determine impact
                impact_level, impact_type = self._assess_impact(title + " " + description)
                
                news_item = NewsItem(
                    id=self._generate_id(title, source_name),
                    title=self._clean_html(title),
                    summary=self._clean_html(description)[:500],
                    content=None,
                    source=source_name,
                    source_url=link,
                    published_at=parsed_date,
                    category=category,
                    impact_level=impact_level,
                    impact_type=impact_type,
                    countries_affected=countries,
                    keywords=self._extract_keywords(title + " " + description),
                )
                items.append(news_item)
            
            # Handle Atom feeds
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                title = entry.findtext("atom:title", "", ns)
                summary = entry.findtext("atom:summary", "", ns) or entry.findtext("atom:content", "", ns)
                link_elem = entry.find("atom:link", ns)
                link = link_elem.get("href", "") if link_elem is not None else ""
                updated = entry.findtext("atom:updated", "", ns) or entry.findtext("atom:published", "", ns)
                
                if not title:
                    continue
                
                parsed_date = self._parse_date(updated)
                category = self._categorize_content(title + " " + (summary or ""))
                if not category:
                    category = default_category
                    
                impact_level, impact_type = self._assess_impact(title + " " + (summary or ""))
                
                news_item = NewsItem(
                    id=self._generate_id(title, source_name),
                    title=self._clean_html(title),
                    summary=self._clean_html(summary or "")[:500],
                    content=None,
                    source=source_name,
                    source_url=link,
                    published_at=parsed_date,
                    category=category,
                    impact_level=impact_level,
                    impact_type=impact_type,
                    countries_affected=countries,
                    keywords=self._extract_keywords(title + " " + (summary or "")),
                )
                items.append(news_item)
                
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS XML: {e}")
        except Exception as e:
            logger.error(f"Error parsing RSS: {e}")
        
        return items
    
    async def _fetch_newsapi(self, countries: List[str]) -> List[NewsItem]:
        """Fetch news from NewsAPI."""
        if not self._newsapi_key:
            return []
        
        cache_key = f"newsapi_{'-'.join(sorted(countries))}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        items: List[NewsItem] = []
        
        # Build search query for real estate
        queries = [
            "immobilier OR real estate OR property market",
            "taux hypothécaire OR mortgage rate",
            "prix immobilier OR housing price",
        ]
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for query in queries[:1]:  # Limit API calls
                    response = await client.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": query,
                            "apiKey": self._newsapi_key,
                            "language": "fr,en",
                            "sortBy": "publishedAt",
                            "pageSize": 10,
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for article in data.get("articles", []):
                            title = article.get("title", "")
                            description = article.get("description", "")
                            
                            if not title:
                                continue
                            
                            category = self._categorize_content(title + " " + (description or ""))
                            impact_level, impact_type = self._assess_impact(title + " " + (description or ""))
                            
                            news_item = NewsItem(
                                id=self._generate_id(title, article.get("source", {}).get("name", "NewsAPI")),
                                title=title,
                                summary=(description or "")[:500],
                                content=article.get("content"),
                                source=article.get("source", {}).get("name", "NewsAPI"),
                                source_url=article.get("url"),
                                published_at=article.get("publishedAt", datetime.utcnow().isoformat()),
                                category=category or "market",
                                impact_level=impact_level,
                                impact_type=impact_type,
                                countries_affected=countries,
                                author=article.get("author"),
                                image_url=article.get("urlToImage"),
                                keywords=self._extract_keywords(title + " " + (description or "")),
                            )
                            items.append(news_item)
                            
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
        
        self._cache[cache_key] = items
        self._cache_time[cache_key] = datetime.utcnow()
        
        return items
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to ISO format."""
        if not date_str:
            return datetime.utcnow().isoformat()
        
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RSS format
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S%z",  # ISO format
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return datetime.utcnow().isoformat()
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        clean = clean.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        return clean.strip()
    
    def _categorize_content(self, text: str) -> Optional[str]:
        """Categorize content based on keywords."""
        text_lower = text.lower()
        
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def _assess_impact(self, text: str) -> tuple[str, str]:
        """Assess impact level and type from content."""
        text_lower = text.lower()
        
        # Impact level keywords
        critical_kw = ["urgent", "alerte", "crise", "effondrement", "collapse", "emergency"]
        high_kw = ["important", "majeur", "significant", "hausse forte", "baisse forte", "record"]
        
        # Impact type keywords  
        negative_kw = ["baisse", "chute", "déclin", "crise", "risque", "perte", "fall", "decline", "risk"]
        positive_kw = ["hausse", "croissance", "opportunité", "growth", "increase", "opportunity", "gain"]
        
        # Determine level
        if any(kw in text_lower for kw in critical_kw):
            level = "critical"
        elif any(kw in text_lower for kw in high_kw):
            level = "high"
        else:
            level = "medium"
        
        # Determine type
        neg_count = sum(1 for kw in negative_kw if kw in text_lower)
        pos_count = sum(1 for kw in positive_kw if kw in text_lower)
        
        if neg_count > pos_count:
            impact_type = "negative"
        elif pos_count > neg_count:
            impact_type = "positive"
        elif neg_count > 0 and pos_count > 0:
            impact_type = "mixed"
        else:
            impact_type = "neutral"
        
        return level, impact_type
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        keywords = []
        text_lower = text.lower()
        
        for category, kw_list in CATEGORY_KEYWORDS.items():
            for kw in kw_list:
                if kw.lower() in text_lower and kw not in keywords:
                    keywords.append(kw)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate news items based on title similarity."""
        unique = []
        seen_titles = set()
        
        for item in items:
            # Normalize title for comparison
            normalized = item.title.lower()[:50]
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(item)
        
        return unique


# Singleton instance
_news_provider: Optional[RealEstateNewsProvider] = None

def get_news_provider() -> RealEstateNewsProvider:
    """Get or create the news provider instance."""
    global _news_provider
    if _news_provider is None:
        _news_provider = RealEstateNewsProvider()
    return _news_provider
