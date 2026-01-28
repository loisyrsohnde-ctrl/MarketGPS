"""
MarketGPS - African Economic News Scraper

Scrapes economic/financial news from African francophone websites.
Filters articles with 100+ interactions (likes, comments, shares).
Runs automatically between 6h and 21h.

Sources: 30+ African news sites covering economy, finance, startups, fintech, tech.
"""

import os
import sys
import re
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import asyncio

import httpx
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# NEWS SOURCES CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

NEWS_SOURCES = [
    # PANAFRICAIN
    {"name": "Agence Ecofin", "url": "https://www.agenceecofin.com", "category": "panafricain", "lang": "fr"},
    {"name": "Financial Afrik", "url": "https://www.financialafrik.com", "category": "panafricain", "lang": "fr"},
    {"name": "Jeune Afrique", "url": "https://www.jeuneafrique.com/economie-entreprises/", "category": "panafricain", "lang": "fr"},
    {"name": "Africa Intelligence", "url": "https://www.africaintelligence.fr", "category": "panafricain", "lang": "fr"},
    {"name": "The Africa Report", "url": "https://www.theafricareport.com", "category": "panafricain", "lang": "en"},
    {"name": "Sika Finance", "url": "https://www.sikafinance.com", "category": "panafricain", "lang": "fr"},
    {"name": "The Conversation Africa", "url": "https://theconversation.com/africa", "category": "panafricain", "lang": "fr"},
    {"name": "Africanews", "url": "https://fr.africanews.com/business/", "category": "panafricain", "lang": "fr"},

    # CAMEROUN
    {"name": "EcoMatin", "url": "https://ecomatin.net", "category": "cameroun", "lang": "fr"},
    {"name": "Investir au Cameroun", "url": "https://www.investiraucameroun.com", "category": "cameroun", "lang": "fr"},
    {"name": "Business in Cameroon", "url": "https://www.businessincameroon.com", "category": "cameroun", "lang": "fr"},

    # COTE D'IVOIRE
    {"name": "Minutes Eco", "url": "https://minutes-eco.com", "category": "cote_ivoire", "lang": "fr"},
    {"name": "Abidjan.net Economie", "url": "https://news.abidjan.net/articles/economie", "category": "cote_ivoire", "lang": "fr"},
    {"name": "FratMat Economie", "url": "https://www.fratmat.info/categorie/economie", "category": "cote_ivoire", "lang": "fr"},

    # SENEGAL
    {"name": "APS Economie", "url": "https://aps.sn/economie/", "category": "senegal", "lang": "fr"},
    {"name": "Le Soleil Economie", "url": "https://lesoleil.sn/economie/", "category": "senegal", "lang": "fr"},
    {"name": "Seneweb Economie", "url": "https://www.seneweb.com/economie/", "category": "senegal", "lang": "fr"},

    # BENIN
    {"name": "24h au Bénin", "url": "https://www.24haubenin.info/?Economie", "category": "benin", "lang": "fr"},
    {"name": "Matin Libre", "url": "https://matinlibre.com/category/economie/", "category": "benin", "lang": "fr"},
    {"name": "Banouto", "url": "https://banouto.info", "category": "benin", "lang": "fr"},

    # BURKINA FASO
    {"name": "Burkina24", "url": "https://burkina24.com/category/economie/", "category": "burkina_faso", "lang": "fr"},
    {"name": "Sidwaya", "url": "https://www.sidwaya.info/economie/", "category": "burkina_faso", "lang": "fr"},

    # MAROC
    {"name": "L'Economiste", "url": "https://www.leconomiste.com", "category": "maroc", "lang": "fr"},
    {"name": "Medias24", "url": "https://medias24.com", "category": "maroc", "lang": "fr"},
    {"name": "Le360 Economie", "url": "https://fr.le360.ma/economie/", "category": "maroc", "lang": "fr"},

    # KENYA / AFRIQUE DU SUD (English)
    {"name": "Business Daily Africa", "url": "https://www.businessdailyafrica.com", "category": "kenya", "lang": "en"},
    {"name": "Business Day SA", "url": "https://www.businessday.co.za", "category": "south_africa", "lang": "en"},
]

# Keywords to identify economic/financial content
ECONOMIC_KEYWORDS = [
    # French
    "économie", "économique", "finance", "financier", "banque", "investissement",
    "startup", "fintech", "entreprise", "business", "marché", "bourse", "BRVM",
    "croissance", "PIB", "inflation", "dette", "budget", "fiscal", "impôt",
    "commerce", "exportation", "importation", "agriculture", "industrie",
    "technologie", "numérique", "digital", "innovation", "entrepreneur",
    "emploi", "chômage", "salaire", "paiement", "mobile money", "crypto",
    "pétrole", "gaz", "énergie", "mines", "or", "cacao", "café",
    "CEMAC", "UEMOA", "CEDEAO", "FCFA", "franc CFA", "dollar", "euro",
    # English
    "economy", "economic", "finance", "financial", "bank", "investment",
    "startup", "fintech", "business", "market", "stock", "growth", "GDP",
    "inflation", "debt", "budget", "tax", "trade", "export", "import",
    "technology", "digital", "innovation", "entrepreneur", "employment",
    "payment", "crypto", "oil", "gas", "energy", "mining", "gold",
]


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ScrapedArticle:
    """Represents a scraped news article."""
    url: str
    title: str
    summary: Optional[str]
    source_name: str
    source_url: str
    category: str
    language: str
    image_url: Optional[str]
    author: Optional[str]
    published_at: Optional[str]
    scraped_at: str

    # Engagement metrics
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    total_interactions: int = 0

    # Content analysis
    keywords: List[str] = None
    relevance_score: float = 0.0

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        self.total_interactions = self.likes + self.comments + self.shares

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_hash(self) -> str:
        """Generate unique hash for deduplication."""
        content = f"{self.url}{self.title}"
        return hashlib.md5(content.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# SCRAPER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class AfricanNewsScraper:
    """Scrapes economic news from African sources."""

    def __init__(self, db: SQLiteStore):
        self.db = db
        self.client = None
        self.min_interactions = 100  # Minimum interactions to be considered "trending"
        self._init_database()

    def _init_database(self):
        """Initialize the news articles table."""
        with self.db._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id TEXT PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    source_name TEXT NOT NULL,
                    source_url TEXT,
                    category TEXT,
                    language TEXT DEFAULT 'fr',
                    image_url TEXT,
                    author TEXT,
                    published_at TEXT,
                    scraped_at TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    total_interactions INTEGER DEFAULT 0,
                    keywords TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    published_to_app INTEGER DEFAULT 0,
                    published_to_app_at TEXT,
                    admin_notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_status ON news_articles(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_interactions ON news_articles(total_interactions DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_to_app)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_scraped ON news_articles(scraped_at DESC)")

            conn.commit()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                }
            )
        return self.client

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page content."""
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def extract_engagement(self, soup: BeautifulSoup, html: str) -> Dict[str, int]:
        """Extract engagement metrics from page."""
        engagement = {"likes": 0, "comments": 0, "shares": 0, "views": 0}

        # Common patterns for engagement
        patterns = {
            "likes": [
                r'(\d+)\s*(?:like|j\'aime|reactions?|👍)',
                r'data-likes?["\s=:]+(\d+)',
                r'like-count["\s:>]+(\d+)',
            ],
            "comments": [
                r'(\d+)\s*(?:comment|commentaire)',
                r'data-comments?["\s=:]+(\d+)',
                r'comment-count["\s:>]+(\d+)',
            ],
            "shares": [
                r'(\d+)\s*(?:share|partage)',
                r'data-shares?["\s=:]+(\d+)',
                r'share-count["\s:>]+(\d+)',
            ],
            "views": [
                r'(\d+)\s*(?:view|vue|lecture)',
                r'data-views?["\s=:]+(\d+)',
                r'view-count["\s:>]+(\d+)',
            ],
        }

        html_lower = html.lower()

        for metric, metric_patterns in patterns.items():
            for pattern in metric_patterns:
                matches = re.findall(pattern, html_lower, re.IGNORECASE)
                if matches:
                    # Take the largest number found
                    numbers = [int(m) for m in matches if m.isdigit()]
                    if numbers:
                        engagement[metric] = max(numbers)
                        break

        # Also look for social share buttons with counts
        share_buttons = soup.find_all(class_=re.compile(r'share|social', re.I))
        for btn in share_buttons:
            text = btn.get_text()
            numbers = re.findall(r'\d+', text)
            if numbers:
                num = int(numbers[0])
                if num > engagement["shares"]:
                    engagement["shares"] = num

        return engagement

    def calculate_relevance(self, title: str, summary: str = "") -> Tuple[float, List[str]]:
        """Calculate relevance score based on economic keywords."""
        text = f"{title} {summary}".lower()
        found_keywords = []

        for keyword in ECONOMIC_KEYWORDS:
            if keyword.lower() in text:
                found_keywords.append(keyword)

        # Score: percentage of keywords found (max 1.0)
        score = min(len(found_keywords) / 10.0, 1.0)

        return score, found_keywords

    async def scrape_source(self, source: Dict[str, str]) -> List[ScrapedArticle]:
        """Scrape articles from a single source."""
        articles = []

        try:
            html = await self.fetch_page(source["url"])
            if not html:
                return articles

            soup = BeautifulSoup(html, "html.parser")

            # Find article links - common patterns
            article_selectors = [
                "article a[href]",
                ".article a[href]",
                ".post a[href]",
                ".news-item a[href]",
                ".entry a[href]",
                "h2 a[href]",
                "h3 a[href]",
                ".title a[href]",
                ".headline a[href]",
            ]

            seen_urls = set()

            for selector in article_selectors:
                links = soup.select(selector)
                for link in links[:20]:  # Limit per selector
                    href = link.get("href", "")
                    if not href or href.startswith("#"):
                        continue

                    # Make absolute URL
                    full_url = urljoin(source["url"], href)

                    # Skip if already seen
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    # Skip non-article URLs
                    if any(x in full_url.lower() for x in ["/tag/", "/category/", "/author/", "/page/", "javascript:", "mailto:"]):
                        continue

                    # Get title
                    title = link.get_text().strip()
                    if not title or len(title) < 10:
                        continue

                    # Calculate relevance
                    relevance_score, keywords = self.calculate_relevance(title)

                    # Only include if somewhat relevant
                    if relevance_score < 0.1:
                        continue

                    article = ScrapedArticle(
                        url=full_url,
                        title=title,
                        summary=None,
                        source_name=source["name"],
                        source_url=source["url"],
                        category=source["category"],
                        language=source["lang"],
                        image_url=None,
                        author=None,
                        published_at=None,
                        scraped_at=datetime.utcnow().isoformat(),
                        keywords=keywords,
                        relevance_score=relevance_score,
                    )

                    articles.append(article)

            # For top articles, fetch full page to get engagement
            for article in articles[:10]:
                await self._enrich_article(article)
                await asyncio.sleep(0.5)  # Rate limiting

        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")

        return articles

    async def _enrich_article(self, article: ScrapedArticle):
        """Fetch full article page to get more details and engagement."""
        try:
            html = await self.fetch_page(article.url)
            if not html:
                return

            soup = BeautifulSoup(html, "html.parser")

            # Extract engagement
            engagement = self.extract_engagement(soup, html)
            article.likes = engagement["likes"]
            article.comments = engagement["comments"]
            article.shares = engagement["shares"]
            article.views = engagement["views"]
            article.total_interactions = sum(engagement.values())

            # Extract summary/description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                article.summary = meta_desc.get("content", "")[:500]

            # Extract image
            og_image = soup.find("meta", attrs={"property": "og:image"})
            if og_image:
                article.image_url = og_image.get("content")

            # Extract author
            author_tag = soup.find(class_=re.compile(r'author', re.I))
            if author_tag:
                article.author = author_tag.get_text().strip()[:100]

            # Extract publish date
            time_tag = soup.find("time")
            if time_tag:
                article.published_at = time_tag.get("datetime") or time_tag.get_text().strip()

            # Recalculate relevance with summary
            if article.summary:
                score, keywords = self.calculate_relevance(article.title, article.summary)
                article.relevance_score = score
                article.keywords = keywords

        except Exception as e:
            logger.warning(f"Error enriching article {article.url}: {e}")

    def save_article(self, article: ScrapedArticle) -> bool:
        """Save article to database."""
        try:
            article_id = article.get_hash()

            with self.db._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO news_articles (
                        id, url, title, summary, source_name, source_url,
                        category, language, image_url, author, published_at,
                        scraped_at, likes, comments, shares, views,
                        total_interactions, keywords, relevance_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_id,
                    article.url,
                    article.title,
                    article.summary,
                    article.source_name,
                    article.source_url,
                    article.category,
                    article.language,
                    article.image_url,
                    article.author,
                    article.published_at,
                    article.scraped_at,
                    article.likes,
                    article.comments,
                    article.shares,
                    article.views,
                    article.total_interactions,
                    json.dumps(article.keywords) if article.keywords else None,
                    article.relevance_score,
                ))
                conn.commit()

            return True
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            return False

    async def run_scraping(self, min_interactions: int = 100) -> Dict[str, Any]:
        """Run full scraping of all sources."""
        self.min_interactions = min_interactions

        results = {
            "started_at": datetime.utcnow().isoformat(),
            "sources_scraped": 0,
            "articles_found": 0,
            "articles_saved": 0,
            "trending_articles": 0,
            "errors": [],
        }

        logger.info(f"Starting news scraping at {results['started_at']}")

        for source in NEWS_SOURCES:
            try:
                logger.info(f"Scraping {source['name']}...")
                articles = await self.scrape_source(source)
                results["sources_scraped"] += 1
                results["articles_found"] += len(articles)

                for article in articles:
                    if self.save_article(article):
                        results["articles_saved"] += 1
                        if article.total_interactions >= min_interactions:
                            results["trending_articles"] += 1

                # Rate limiting between sources
                await asyncio.sleep(1)

            except Exception as e:
                error = f"Error with {source['name']}: {str(e)}"
                logger.error(error)
                results["errors"].append(error)

        results["finished_at"] = datetime.utcnow().isoformat()

        await self.close()

        logger.info(f"Scraping complete: {results['articles_saved']} articles saved, {results['trending_articles']} trending")

        return results

    def get_trending_articles(self, limit: int = 50, min_interactions: int = 100) -> List[Dict]:
        """Get trending articles (high engagement)."""
        with self.db._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM news_articles
                WHERE total_interactions >= ?
                ORDER BY total_interactions DESC, scraped_at DESC
                LIMIT ?
            """, (min_interactions, limit))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_pending_articles(self, limit: int = 100) -> List[Dict]:
        """Get articles pending review."""
        with self.db._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM news_articles
                WHERE status = 'pending' AND published_to_app = 0
                ORDER BY total_interactions DESC, relevance_score DESC
                LIMIT ?
            """, (limit,))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def publish_article(self, article_id: str, admin_notes: str = "") -> bool:
        """Mark article as published to app."""
        try:
            with self.db._get_conn() as conn:
                conn.execute("""
                    UPDATE news_articles
                    SET published_to_app = 1,
                        published_to_app_at = ?,
                        status = 'published',
                        admin_notes = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), admin_notes, article_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error publishing article: {e}")
            return False

    def reject_article(self, article_id: str, reason: str = "") -> bool:
        """Mark article as rejected."""
        try:
            with self.db._get_conn() as conn:
                conn.execute("""
                    UPDATE news_articles
                    SET status = 'rejected',
                        admin_notes = ?
                    WHERE id = ?
                """, (reason, article_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error rejecting article: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

def should_run_now() -> bool:
    """Check if current time is within operating hours (6h-21h)."""
    current_hour = datetime.now().hour
    return 6 <= current_hour < 21


async def scheduled_scraping_task(db: SQLiteStore):
    """Task to run scheduled scraping."""
    scraper = AfricanNewsScraper(db)

    if should_run_now():
        logger.info("Running scheduled news scraping...")
        results = await scraper.run_scraping(min_interactions=100)
        logger.info(f"Scheduled scraping results: {results}")
        return results
    else:
        logger.info("Outside operating hours (6h-21h), skipping scraping")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    db = SQLiteStore()
    scraper = AfricanNewsScraper(db)

    print("Starting manual scraping test...")
    results = asyncio.run(scraper.run_scraping(min_interactions=50))
    print(f"\nResults: {json.dumps(results, indent=2)}")

    print("\nTrending articles:")
    trending = scraper.get_trending_articles(limit=10, min_interactions=50)
    for article in trending:
        print(f"- [{article['total_interactions']}] {article['title'][:60]}... ({article['source_name']})")
