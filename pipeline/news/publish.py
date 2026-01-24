"""
MarketGPS News Pipeline - Publisher

Processes raw items, extracts content, translates/rewrites to French,
and publishes to the news_articles table.

Fallback mode: If no LLM is available, stores extracted content as-is.
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

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
    
    def _init_llm(self):
        """Initialize LLM for translation/rewriting."""
        self.llm_provider = None
        
        # Try Gemini first
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if GEMINI_AVAILABLE and gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.llm_provider = "gemini"
                logger.info("Using Gemini for news rewriting")
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")
        
        # Try OpenAI as fallback
        if not self.llm_provider:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if OPENAI_AVAILABLE and openai_key:
                try:
                    openai.api_key = openai_key
                    self.llm_provider = "openai"
                    logger.info("Using OpenAI for news rewriting")
                except Exception as e:
                    logger.warning(f"OpenAI init failed: {e}")
        
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
        """Detect country from content or use source country."""
        if source_country:
            return source_country
        
        # Simple keyword detection
        country_keywords = {
            'NG': ['nigeria', 'lagos', 'abuja', 'naira', 'cbn'],
            'ZA': ['south africa', 'johannesburg', 'cape town', 'rand', 'sarb'],
            'KE': ['kenya', 'nairobi', 'mpesa', 'shilling'],
            'GH': ['ghana', 'accra', 'cedi'],
            'EG': ['egypt', 'cairo', 'pound'],
            'CI': ['ivory coast', "cote d'ivoire", 'abidjan', 'fcfa'],
            'SN': ['senegal', 'dakar'],
            'MA': ['morocco', 'maroc', 'casablanca', 'rabat'],
        }
        
        content_lower = content.lower() if content else ""
        
        for country_code, keywords in country_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return country_code
        
        return None
    
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
    
    def _rewrite_with_llm(self, raw_payload: Dict, source_language: str) -> Optional[Dict]:
        """Use LLM to translate and rewrite content to French with premium editorial style."""
        if not self.llm_provider:
            return None
        
        title = raw_payload.get("title", "")
        content = raw_payload.get("content") or raw_payload.get("summary", "")
        
        prompt = f"""Tu es un ÉDITEUR FINANCIER FRANCOPHONE SENIOR travaillant pour un magazine financier premium de type Financial Times ou Les Échos.

Ta mission est de transformer cet article brut en contenu éditorial de haute qualité.

Article original ({source_language}):
Titre: {title}
Contenu: {content[:2500]}

INSTRUCTIONS STRICTES:

1. **TITRE** (title_fr): Réécris un titre percutant, style "Une" de journal financier. Maximum 100 caractères. Doit être accrocheur et informatif.

2. **RÉSUMÉ** (excerpt_fr): Exactement 2 phrases concises résumant l'essentiel. Style journalistique professionnel.

3. **CONTENU** (content_md): Reformule le contenu en français soutenu, style éditorial. 3-4 paragraphes. Ne copie jamais mot pour mot.

4. **POINTS CLÉS** (tldr): Exactement 3 bullet points percutants résumant les informations essentielles.

5. **CATÉGORIE** (category): UNE seule parmi: "Fintech", "Finance", "Startup", "Tech", "Régulation", "Banking", "Crypto", "Économie"

6. **SENTIMENT** (sentiment): "positive", "negative", ou "neutral" selon le ton de l'article.

Réponds UNIQUEMENT en JSON valide avec ce format exact:
{{
  "title_fr": "...",
  "excerpt_fr": "...",
  "content_md": "...",
  "tldr": ["point1", "point2", "point3"],
  "category": "...",
  "sentiment": "..."
}}
"""
        
        try:
            if self.llm_provider == "gemini":
                response = self.gemini_model.generate_content(prompt)
                text = response.text
            elif self.llm_provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.7
                )
                text = response.choices[0].message.content
            else:
                return None
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            logger.warning(f"LLM rewrite failed: {e}")
        
        return None
    
    def _fallback_process(self, raw_payload: Dict) -> Dict:
        """Fallback processing without LLM (extract and clean only)."""
        title = raw_payload.get("title", "Untitled")
        content = raw_payload.get("content") or raw_payload.get("summary", "")
        
        # Clean HTML if present
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Create basic excerpt
        excerpt = content[:200] + "..." if len(content) > 200 else content
        
        return {
            "title_fr": title,
            "excerpt_fr": excerpt,
            "content_md": content,
            "tldr": None
        }
    
    def process_raw_item(self, raw_item: Dict) -> Optional[int]:
        """
        Process a single raw item and publish as article.
        
        Returns:
            Article ID if successful, None otherwise
        """
        try:
            raw_payload = json.loads(raw_item.get("raw_payload", "{}"))
            source_language = raw_item.get("source_language", "en")
            
            # Try LLM rewrite first, fallback to basic processing
            rewritten = self._rewrite_with_llm(raw_payload, source_language)
            is_ai_processed = rewritten is not None
            
            if not rewritten:
                rewritten = self._fallback_process(raw_payload)
            
            # Detect country and tags
            full_content = f"{rewritten.get('title_fr', '')} {rewritten.get('content_md', '')}"
            country = self._detect_country(full_content, raw_item.get("source_country"))
            tags = self._extract_tags(full_content, raw_payload.get("tags", []))
            
            # Get category and sentiment from AI response or default
            category = rewritten.get("category") or (tags[0].capitalize() if tags else "Actualité")
            sentiment = rewritten.get("sentiment", "neutral")
            
            # Generate slug
            slug = self._generate_slug(rewritten.get("title_fr", "article"))
            
            # Prepare article
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
                "image_url": raw_payload.get("image"),
                "source_name": raw_item.get("source_name", "Unknown"),
                "source_url": raw_item.get("url"),
                "canonical_url": raw_item.get("url"),
                "published_at": raw_item.get("published_at"),
                "status": "published",
                "category": category,
                "sentiment": sentiment,
                "is_ai_processed": is_ai_processed
            }
            
            # Insert article
            article_id = self.store.insert_news_article(article)
            
            if article_id:
                # Mark raw item as processed
                self.store.mark_raw_item_processed(raw_item["id"])
                return article_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error processing raw item {raw_item.get('id')}: {e}")
            self.store.mark_raw_item_processed(raw_item.get("id"), error=str(e))
            return None
    
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
