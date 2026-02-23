"""
MarketGPS News Pipeline - Publisher

Processes raw items, extracts content, translates/rewrites to French,
and publishes to the news_articles table.

Fallback mode: If no LLM is available, stores extracted content as-is.
"""

import hashlib
import html as html_lib
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from pipeline.news.image_fetcher import fetch_article_image
from pipeline.news.scoring import score_article, load_sources_registry
from pipeline.news.interactions_fetcher import get_interactions_fetcher, InteractionMetrics

logger = get_logger(__name__)

# Backend API configuration for remote publishing
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "").rstrip("/")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

# ─── English article pre-filter: only process EN articles if they meet these criteria ───
# Francophone sub-Saharan countries (articles ABOUT these countries always pass)
FRANCOPHONE_COUNTRIES = {"CI", "CM", "SN", "BJ", "BF", "TG", "GA", "ML", "NE", "GN", "TD", "CG", "CD"}

# Breaking / urgent keywords in English titles
BREAKING_KEYWORDS_EN = {
    "breaking", "urgent", "exclusive", "just in", "flash", "alert",
    "breaking news", "developing", "confirmed"
}

# High-impact keywords that justify LLM token spend
IMPACT_KEYWORDS_EN = {
    "billion", "acquisition", "ipo", "merger", "crisis", "scandal", "record",
    "first ever", "unprecedented", "collapsed", "shutdown", "default", "bailout",
    "sanctions", "embargo", "crash", "surge", "plunge", "bankrupt", "fraud",
    "central bank", "interest rate", "gdp", "inflation"
}

# Minimum trust score for English sources to be considered
EN_MIN_TRUST_SCORE = float(os.getenv("EN_ARTICLE_MIN_TRUST", "0.85"))

# Try to import LLM libraries
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


class NewsPublisher:
    """Processes and publishes news articles."""
    
    def __init__(self, store: Optional[SQLiteStore] = None):
        """Initialize the publisher."""
        self.store = store or SQLiteStore()
        self.store._ensure_news_tables()
        self._init_llm()
        self.sources_registry = load_sources_registry()
        self._pending_articles: List[Dict] = []
    
    def _init_llm(self):
        """Initialize LLM for translation/rewriting."""
        self.llm_provider = None
        self.openai_client = None
        
        # Try OpenAI first (more reliable)
        openai_key = os.environ.get("OPENAI_API_KEY")
        if OPENAI_AVAILABLE and openai_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.llm_provider = "openai"
                logger.info("Using OpenAI for news rewriting")
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")
        
        # Try Gemini as fallback
        if not self.llm_provider:
            gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if GEMINI_AVAILABLE and gemini_key:
                try:
                    genai.configure(api_key=gemini_key)
                    self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                    self.llm_provider = "gemini"
                    logger.info("Using Gemini for news rewriting")
                except Exception as e:
                    logger.warning(f"Gemini init failed: {e}")
        
        if not self.llm_provider:
            logger.warning("No LLM available - running in fallback mode (no translation)")
    
    def _generate_slug(self, title: str, article_id: Optional[int] = None) -> str:
        """Generate URL-friendly slug from title."""
        # Normalize
        slug = title.lower()
        
        # Remove accents (basic)
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        for old, new in replacements.items():
            slug = slug.replace(old, new)
        
        # Keep only alphanumeric and spaces
        slug = re.sub(r'[^a-z0-9\s]', '', slug)
        
        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug.strip())
        
        # Limit length
        slug = slug[:80]
        
        # Add hash for uniqueness
        hash_suffix = hashlib.md5(f"{title}{article_id or datetime.now().isoformat()}".encode()).hexdigest()[:6]
        
        return f"{slug}-{hash_suffix}"
    
    def _detect_country(self, content: str, source_country: Optional[str]) -> Optional[str]:
        """Detect country from content or use source country.

        Uses word-boundary matching and a scoring approach to avoid
        false positives (e.g. 'coast' matching 'ivory coast').
        """
        if source_country:
            return source_country

        # Keywords per country — use word-boundary regex to avoid
        # substring collisions like 'coast' matching 'ivory coast'.
        country_keywords = {
            'NG': ['nigeria', 'lagos', 'abuja', 'naira', r'\bcbn\b'],
            'ZA': ['south africa', 'johannesburg', 'cape town', r'\brand\b', r'\bsarb\b'],
            'KE': ['kenya', 'nairobi', 'mpesa', 'mombasa', r'\bksh\b'],
            'GH': ['ghana', 'accra', 'cedi'],
            'EG': [r'\begypt', 'cairo', r'\begyptian'],
            'CI': ["cote d'ivoire", r"c[ôo]te d'ivoire", 'abidjan',
                    'ivory coast', r'\bfcfa\b', r'\bbceao\b'],
            'SN': ['senegal', r's[ée]n[ée]gal', 'dakar'],
            'MA': ['morocco', 'maroc', 'casablanca', 'rabat'],
            'CM': ['cameroun', 'cameroon', 'douala', r'yaound[ée]'],
            'TN': ['tunisia', 'tunisie', 'tunis'],
            'RW': ['rwanda', 'kigali'],
        }

        content_lower = content.lower() if content else ""
        if not content_lower:
            return None

        # Score each country by number of keyword hits
        scores: Dict[str, int] = {}
        for country_code, keywords in country_keywords.items():
            score = 0
            for keyword in keywords:
                # Use word boundaries for short keywords to avoid
                # substring false positives
                if keyword.startswith(r'\b') or len(keyword) <= 4:
                    if re.search(keyword, content_lower):
                        score += 1
                else:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                        score += 1
            if score > 0:
                scores[country_code] = score

        if not scores:
            return None

        # Return the country with the highest score
        return max(scores, key=scores.get)
    
    def _extract_tags(self, content: str, raw_tags: List[str]) -> List[str]:
        """Extract tags from content and raw tags."""
        tags = set()
        
        # Add raw tags if any
        for tag in raw_tags:
            if tag and len(tag) < 30:
                tags.add(tag.lower().strip())
        
        # Simple keyword matching for common tags
        content_lower = content.lower() if content else ""
        
        tag_keywords = {
            'fintech': ['fintech', 'financial technology', 'digital banking'],
            'startup': ['startup', 'start-up', 'founded', 'launched'],
            'vc': ['funding', 'raised', 'investment', 'series a', 'series b', 'seed round', 'venture capital'],
            'crypto': ['crypto', 'bitcoin', 'blockchain', 'cryptocurrency'],
            'payments': ['payments', 'mobile money', 'mpesa', 'transfer'],
            'banking': ['bank', 'banking', 'neobank'],
            'regulation': ['regulation', 'central bank', 'license', 'compliance'],
            'insurtech': ['insurance', 'insurtech'],
        }
        
        for tag, keywords in tag_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    tags.add(tag)
                    break
        
        return list(tags)[:8]  # Limit to 8 tags
    
    def _fetch_full_article(self, url: str) -> Optional[str]:
        """Fetch full article text from source URL for richer LLM context."""
        if not url or not BS4_AVAILABLE:
            return None
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "MarketGPS/1.0 (+https://marketgps.online)"},
                timeout=12,
                allow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove non-content elements
            for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                tag.decompose()

            # Try common article containers
            article = (
                soup.find("article")
                or soup.find("div", class_=re.compile(r"article|post|entry|content|story", re.I))
                or soup.find("main")
            )
            target = article if article else soup.body
            if not target:
                return None

            text = target.get_text(separator="\n", strip=True)
            # Clean up excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text[:8000] if text else None
        except Exception as e:
            logger.debug(f"Could not fetch full article from {url}: {e}")
            return None

    def _rewrite_with_llm(self, raw_payload: Dict, source_language: str, full_article_text: Optional[str] = None) -> Optional[Dict]:
        """Use LLM to translate and rewrite content to French with premium editorial style."""
        if not self.llm_provider:
            return None

        title = raw_payload.get("title", "")
        content = raw_payload.get("content") or raw_payload.get("summary", "")

        # Use full article text when available for much richer context
        if full_article_text and len(full_article_text) > len(content):
            content = full_article_text

        prompt = f"""Rôle : Tu es un Rédacteur en Chef senior pour "MarketGPS", un média économique et financier de référence couvrant l'Afrique et les marchés internationaux (type Jeune Afrique / Les Échos / Financial Times).

LANGUE OBLIGATOIRE : FRANÇAIS. Tout l'article DOIT être rédigé intégralement en français, quelle que soit la langue source ({source_language}). Aucun mot anglais sauf les noms propres (entreprises, personnes, technologies).

TÂCHE 1 : FILTRAGE STRICT
Le sujet est-il CLAIREMENT lié à l'un de ces thèmes ?
- Économie / Finance / Bourse / Marchés
- Tech / Startups / Innovation / Fintech / IA
- Entreprises / Business / Entrepreneuriat / Levées de fonds
- Régulation économique / Politique monétaire
- Énergie / Matières premières / Agriculture (angle économique)
- Immobilier / Infrastructures (angle business)

SI NON (ex: Sport pur, Faits divers, Politique sans angle éco, People, Religion) :
Réponds UNIQUEMENT : {{"skip": true}}

SI OUI — Rédige un article COMPLET et APPROFONDI en suivant ces instructions :

1. STYLE ÉDITORIAL :
- Journalistique premium, fluide, professionnel — niveau Jeune Afrique / Les Échos.
- INTERDIT : "Introduction", "Conclusion", "Développement", "En résumé", "Pour conclure".
- Commence par un LEAD percutant (l'information clé en 1-2 phrases).
- Ton factuel, analytique et engageant.

2. CONTENU APPROFONDI (800-1200 mots) :
- Ne te contente PAS de reformuler l'article source. ENRICHIS-le considérablement :
  a) Contextualise : Explique le contexte historique et sectoriel. Pourquoi cette info est importante maintenant ?
  b) Chiffres & données : Intègre tous les chiffres disponibles. Mets en perspective avec des comparaisons (YoY, par rapport aux concurrents, benchmarks sectoriels).
  c) Acteurs clés : Identifie et présente les entreprises, dirigeants, investisseurs impliqués.
  d) Impact marché : Analyse l'impact sur le marché africain, les investisseurs, l'écosystème concerné.
  e) Perspectives : Quelles sont les implications futures ? Quels scénarios possibles ?
  f) Enjeux régionaux : Si pertinent, comment cela affecte la zone UEMOA, CEMAC, EAC, ou l'Afrique du Sud.
- Utilise le **gras** pour les noms d'entreprises, montants financiers et chiffres clés.
- Structure avec des sous-titres en ## markdown (2-3 sous-titres max, pas de numérotation).
- Paragraphes aérés de 3-5 phrases max.

3. IMAGE SEARCH (IMPORTANT) :
- Génère une requête de recherche d'image précise en ANGLAIS pour illustrer cet article.
- Exemples : "Aliko Dangote cement factory nigeria", "Flutterwave office lagos fintech"

Article source ({source_language}) :
Titre : {title}
Contenu : {content[:7000]}

Réponds UNIQUEMENT en JSON valide STRICT (pas de commentaires, pas de markdown) :
{{
  "skip": false,
  "title_fr": "Titre accrocheur en français (max 100 caractères)",
  "excerpt_fr": "Résumé de 2-3 phrases en français captant l'essentiel de l'article",
  "content_md": "Article complet en markdown (800-1200 mots, EN FRANÇAIS UNIQUEMENT)",
  "category": "Finance|Tech|Business|Startup|Régulation|Énergie|Marchés",
  "sentiment": "positive|neutral|negative",
  "image_search_query": "requête image en anglais",
  "tldr": ["Point clé 1 en français", "Point clé 2 en français", "Point clé 3 en français"]
}}
"""
        
        try:
            if self.llm_provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=6000,
                    temperature=0.7
                )
                text = response.choices[0].message.content
            elif self.llm_provider == "gemini":
                response = self.gemini_model.generate_content(prompt)
                text = response.text
            else:
                return None
            
            # Extract JSON from response - handle markdown code blocks
            json_str = text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(json_str)
                # Validate that we got French content
                if result.get("skip") is True:
                     return result
                     
                if result.get("title_fr") and result.get("content_md"):
                    return result
                else:
                    logger.warning(f"LLM response missing fields. Got keys: {list(result.keys())}")
            except json.JSONDecodeError:
                # Try regex as fallback
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    return json.loads(json_match.group())
                logger.warning(f"LLM response not valid JSON: {text[:200]}...")
            
        except Exception as e:
            logger.warning(f"LLM rewrite failed: {e}")
        
        return None
    
    def _fallback_process(self, raw_payload: Dict) -> Dict:
        """Fallback processing without LLM (extract and clean only)."""
        title = raw_payload.get("title", "Untitled")
        content = raw_payload.get("content") or raw_payload.get("summary", "")

        # Clean HTML tags and decode entities (&amp; -> &, etc.)
        content = re.sub(r'<[^>]+>', '', content)
        content = html_lib.unescape(content)
        content = re.sub(r'\s+', ' ', content).strip()

        title = html_lib.unescape(title)

        # Create basic excerpt
        excerpt = content[:200] + "..." if len(content) > 200 else content

        return {
            "title_fr": title,
            "excerpt_fr": excerpt,
            "content_md": content,
            "tldr": None
        }
    
    def _should_process_english(self, raw_item: Dict) -> bool:
        """
        Decide if an English article is worth spending LLM tokens on.
        Returns True if the article should be processed (translated).

        Criteria for accepting an English article:
        1. Source country is francophone (e.g. "Business in Cameroon" in English)
        2. Title contains breaking/urgent keywords
        3. Title contains high-impact keywords (billion, acquisition, crisis...)
        4. Source trust score >= threshold (high-quality source)
        """
        title = raw_item.get("title", "").lower()
        source_country = (raw_item.get("source_country") or "").upper()
        trust_score = float(raw_item.get("source_trust_score", 0) or 0)

        # 1. Article about a francophone country → always process
        if source_country in FRANCOPHONE_COUNTRIES:
            logger.debug(f"EN article accepted (francophone country {source_country}): {title[:50]}")
            return True

        # 2. Breaking/urgent keywords in title
        if any(kw in title for kw in BREAKING_KEYWORDS_EN):
            logger.debug(f"EN article accepted (breaking keyword): {title[:50]}")
            return True

        # 3. High-impact keywords in title
        if any(kw in title for kw in IMPACT_KEYWORDS_EN):
            logger.debug(f"EN article accepted (impact keyword): {title[:50]}")
            return True

        # 4. High-trust source (Tier 1 quality)
        if trust_score >= EN_MIN_TRUST_SCORE:
            logger.debug(f"EN article accepted (trust={trust_score:.2f}): {title[:50]}")
            return True

        # None of the criteria met → skip this English article
        return False

    def process_raw_item(self, raw_item: Dict) -> Optional[int]:
        """
        Process a single raw item and publish as article.

        Returns:
            Article ID if successful, None otherwise
        """
        try:
            raw_payload = json.loads(raw_item.get("raw_payload", "{}"))
            source_language = raw_item.get("source_language", "en")

            # ─── Pre-filter: skip low-priority English articles to save LLM tokens ───
            if source_language != "fr" and not self._should_process_english(raw_item):
                title_preview = raw_payload.get("title", raw_item.get("title", ""))[:60]
                logger.info(f"⏭️  Skipped (low_priority_{source_language}): {title_preview}")
                self.store.mark_raw_item_processed(raw_item["id"], error="low_priority_english")
                return None

            # Decode HTML entities in raw payload before processing
            for key in ("title", "summary", "content"):
                if raw_payload.get(key):
                    raw_payload[key] = html_lib.unescape(raw_payload[key])

            # Fetch full article content from source URL for richer context
            article_url = raw_item.get("url", "")
            full_article_text = self._fetch_full_article(article_url) if article_url else None
            if full_article_text:
                logger.info(f"📄 Fetched full article ({len(full_article_text)} chars) from {article_url[:60]}...")

            # Try LLM rewrite first, fallback only for French sources
            rewritten = self._rewrite_with_llm(raw_payload, source_language, full_article_text=full_article_text)
            is_ai_processed = rewritten is not None

            if rewritten:
                logger.info(f"✓ AI processed: {rewritten.get('title_fr', '')[:50]}...")
            else:
                if source_language == "fr":
                    # French source: fallback is OK (content already in French)
                    logger.warning(f"✗ AI failed, using FR fallback for: {raw_payload.get('title', '')[:50]}...")
                    rewritten = self._fallback_process(raw_payload)
                else:
                    # Non-French source: DO NOT publish untranslated content
                    # Don't mark as processed → will be retried next cycle when LLM may be available
                    logger.warning(f"✗ AI unavailable for {source_language} article, deferring: {raw_payload.get('title', '')[:50]}...")
                    return None
            
            # Skip based on AI decision (off-topic)
            if rewritten.get("skip") is True:
                logger.info(f"⏭️  Skipped (off-topic): {raw_payload.get('title', '')[:50]}...")
                self.store.mark_raw_item_processed(raw_item["id"])
                return None
            
            # Detect country and tags
            full_content = f"{rewritten.get('title_fr', '')} {rewritten.get('content_md', '')}"
            country = self._detect_country(full_content, raw_item.get("source_country"))
            tags = self._extract_tags(full_content, raw_payload.get("tags", []))
            
            # Get category and sentiment from AI response or default
            category = rewritten.get("category") or (tags[0].capitalize() if tags else "Actualité")
            sentiment = rewritten.get("sentiment", "neutral")
            
            # Fetch image using SPECIFIC SEARCH QUERY from LLM
            existing_image = raw_payload.get("image")
            search_query = rewritten.get("image_search_query")
            
            image_url = fetch_article_image(
                title=rewritten.get("title_fr", raw_payload.get("title", "")),
                category=category,
                country=country,
                keywords=search_query,
                existing_url=existing_image,
                source_url=raw_item.get("url", "")
            )
            
            # Generate slug
            slug = self._generate_slug(rewritten.get("title_fr", "article"))

            # Fetch/estimate interactions for the article
            interactions_fetcher = get_interactions_fetcher()
            interactions = interactions_fetcher.get_interactions(
                url=raw_item.get("url", ""),
                source_name=raw_item.get("source_name", "Unknown"),
                title=rewritten.get("title_fr", raw_payload.get("title", "")),
                published_at=raw_item.get("published_at", datetime.utcnow()),
                category=category,
                country=country,
                language="fr"
            )

            logger.info(f"📊 Interactions for article: {interactions.total_interactions} (virality: {interactions.virality_score}x)")

            # Calculate engagement score using fetched interactions
            scoring_result = score_article(
                title=rewritten.get("title_fr", raw_payload.get("title", "")),
                content=rewritten.get("content_md", ""),
                excerpt=rewritten.get("excerpt_fr", ""),
                source_name=raw_item.get("source_name", "Unknown"),
                published_at=raw_item.get("published_at"),
                image_url=image_url,
                tags=tags,
                save_count=interactions.shares,  # Use shares as saves
                view_count=interactions.views,   # Use views
                sources_registry=self.sources_registry
            )

            # Log breaking news detection
            if scoring_result.get("is_breaking_news"):
                logger.info(f"🔴 BREAKING NEWS detected: {rewritten.get('title_fr', '')[:60]}...")

            # Prepare article
            original_url = raw_item.get("url", "")
            article = {
                "slug": slug,
                "raw_item_id": raw_item.get("id"),
                "title": rewritten.get("title_fr", raw_payload.get("title", "Untitled")),
                "excerpt": rewritten.get("excerpt_fr"),
                "content_md": rewritten.get("content_md"),
                "tldr_json": json.dumps(rewritten.get("tldr")) if rewritten.get("tldr") else None,
                "tags_json": json.dumps(tags) if tags else None,
                "country": country,
                "language": "fr",
                "image_url": image_url,
                "source_name": raw_item.get("source_name", "Unknown"),
                "source_url": original_url,
                "canonical_url": original_url,
                "published_at": raw_item.get("published_at"),
                "status": "published",
                "category": category,
                "sentiment": sentiment,
                "is_ai_processed": is_ai_processed,
                # New scoring fields
                "engagement_score": scoring_result.get("engagement_score", 0.0),
                "is_breaking_news": 1 if scoring_result.get("is_breaking_news") else 0,
                "importance_level": scoring_result.get("importance_level", "normal")
            }
            
            # Insert article locally (dedup check is inside insert_news_article)
            article_id = self.store.insert_news_article(article)

            # Mark raw item as processed regardless (avoid infinite retry)
            self.store.mark_raw_item_processed(raw_item["id"])

            if article_id:
                # Collect article for remote API push
                self._pending_articles.append(article)
                return article_id
            else:
                # Duplicate or insert error — already logged in repository
                return None

        except Exception as e:
            logger.error(f"Error processing raw item {raw_item.get('id')}: {e}")
            self.store.mark_raw_item_processed(raw_item.get("id"), error=str(e))
            return None

    def _push_to_backend_api(self, articles: List[Dict]) -> int:
        """
        Push published articles to the backend API so they appear in the
        frontend. This bridges the gap between the scheduler container
        (which has its own SQLite) and the backend container.

        Returns the number of successfully ingested articles.
        """
        if not BACKEND_API_URL:
            logger.info("BACKEND_API_URL not set — skipping remote push (local dev mode)")
            return 0

        if not articles:
            return 0

        url = f"{BACKEND_API_URL}/api/news/ingest"
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Key": INTERNAL_API_KEY
        }

        # Send in batches of 25 to avoid timeouts
        batch_size = 25
        total_inserted = 0

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            payload = {"articles": batch}

            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    total_inserted += data.get("inserted", 0)
                    logger.info(
                        f"API batch {i // batch_size + 1}: "
                        f"{data.get('inserted', 0)} inserted, "
                        f"{data.get('errors', 0)} errors"
                    )
                else:
                    logger.error(f"API ingest failed (HTTP {resp.status_code}): {resp.text[:200]}")
            except Exception as e:
                logger.error(f"API ingest request failed: {e}")

        logger.info(f"Remote API push complete: {total_inserted}/{len(articles)} articles ingested")
        return total_inserted
    
    def run(self, limit: int = 50) -> Dict:
        """
        Process unprocessed raw items and publish as articles.
        
        Args:
            limit: Maximum number of items to process
            
        Returns:
            Summary statistics
        """
        logger.info(f"Starting news publishing (limit={limit})...")
        start_time = time.time()
        
        # Get unprocessed items
        raw_items = self.store.get_unprocessed_raw_items(limit=limit)
        logger.info(f"Found {len(raw_items)} unprocessed items")
        
        results = {
            "items_total": len(raw_items),
            "items_published": 0,
            "items_error": 0,
            "llm_provider": self.llm_provider or "fallback"
        }
        
        for item in raw_items:
            article_id = self.process_raw_item(item)
            
            if article_id:
                results["items_published"] += 1
            else:
                results["items_error"] += 1
            
            # Small delay to avoid rate limits
            time.sleep(0.2)
        
        elapsed = time.time() - start_time
        results["elapsed_seconds"] = round(elapsed, 2)
        
        logger.info(
            f"Publishing complete: {results['items_published']}/{results['items_total']} articles "
            f"in {elapsed:.1f}s (provider: {results['llm_provider']})"
        )

        # Push articles to backend API (bridges separate Docker containers)
        if self._pending_articles:
            api_count = self._push_to_backend_api(self._pending_articles)
            results["api_pushed"] = api_count
            self._pending_articles = []

        return results


def run_publish(limit: int = 50) -> Dict:
    """Entry point for pipeline.jobs integration."""
    publisher = NewsPublisher()
    return publisher.run(limit=limit)


def run_full_pipeline(ingest_limit: Optional[int] = None, publish_limit: int = 50) -> Dict:
    """Run full news pipeline: ingest + publish."""
    from .ingest_rss import run_ingest
    
    logger.info("=" * 60)
    logger.info("MarketGPS News Pipeline - Full Run")
    logger.info("=" * 60)
    
    # Step 1: Ingest
    ingest_result = run_ingest(limit=ingest_limit)
    
    # Step 2: Publish
    publish_result = run_publish(limit=publish_limit)
    
    return {
        "ingest": ingest_result,
        "publish": publish_result
    }


if __name__ == "__main__":
    # Test run
    result = run_publish(limit=5)
    print(json.dumps(result, indent=2))
