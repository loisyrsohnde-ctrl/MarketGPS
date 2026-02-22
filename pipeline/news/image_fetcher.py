"""
MarketGPS News Pipeline - Image Fetcher

Fetches HIGHLY RELEVANT images using DuckDuckGo Search (Google Images alternative).
Prioritizes: og:image from source → LLM search query → title search → diverse fallbacks.
"""

import os
import random
import re
import requests
from typing import Optional

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    DDGS = None

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from core.config import get_logger

logger = get_logger(__name__)

class ImageFetcher:
    """Fetches real-world context images for news articles."""

    def __init__(self):
        self.ddgs = DDGS() if DDGS_AVAILABLE else None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def fetch_og_image(self, url: str) -> Optional[str]:
        """Fetch og:image from source article URL (most relevant image)."""
        if not url or not BS4_AVAILABLE:
            return None
        try:
            resp = self.session.get(url, timeout=8, allow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try og:image first
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                img_url = og["content"]
                if self._validate_image_url(img_url):
                    return img_url

            # Try twitter:image
            tw = soup.find("meta", attrs={"name": "twitter:image"})
            if tw and tw.get("content"):
                img_url = tw["content"]
                if self._validate_image_url(img_url):
                    return img_url

        except Exception as e:
            logger.debug(f"og:image fetch failed for {url}: {e}")
        return None

    def search_web_image(self, query: str) -> Optional[str]:
        """
        Search for a specific image on the web using DuckDuckGo.
        Returns a direct image URL.
        """
        if not self.ddgs:
            logger.debug("DuckDuckGo search not available - skipping web image search")
            return None

        try:
            search_query = f"{query} news africa business"

            results = self.ddgs.images(
                search_query,
                region="wt-wt",
                safesearch="moderate",
                max_results=5,
                type_image="photo",
                layout="Wide"
            )

            if results:
                for res in results[:3]:
                    image_url = res.get("image")
                    if image_url and self._validate_image_url(image_url):
                        return image_url

        except Exception as e:
            logger.warning(f"Image search failed for '{query}': {e}")

        return None

    def _validate_image_url(self, url: str) -> bool:
        """Check if URL is reachable and is an image."""
        try:
            if any(x in url.lower() for x in ['.svg', 'base64', 'data:image', 'placeholder', '1x1']):
                return False

            response = self.session.head(url, timeout=4, allow_redirects=True)
            content_type = response.headers.get("Content-Type", "")
            return response.status_code == 200 and "image" in content_type
        except (requests.RequestException, TimeoutError) as e:
            logger.debug(f"Image URL validation failed for '{url}': {e}")
            return False

    def fetch_image_url(
        self,
        title: str,
        category: Optional[str] = None,
        source_url: Optional[str] = None,
        keywords: Optional[str] = None,
        existing_url: Optional[str] = None
    ) -> str:
        """
        Get the best possible image.
        Priority:
        1. Valid existing URL from source (og:image already extracted)
        2. Fetch og:image from source URL (most relevant)
        3. Web Search with LLM-provided keywords
        4. Web Search with article title
        5. Diverse category fallback
        """
        # 1. Use existing URL if valid (og:image already in RSS)
        if existing_url and self._validate_image_url(existing_url):
            return existing_url

        # 2. Fetch og:image directly from source article page
        if source_url:
            og_image = self.fetch_og_image(source_url)
            if og_image:
                logger.info(f"📸 Got og:image from source: {og_image[:80]}...")
                return og_image

        # 3. Web Search with LLM-provided specific keywords
        if keywords:
            logger.info(f"🔍 Searching web for image: {keywords}")
            web_image = self.search_web_image(keywords)
            if web_image:
                return web_image

        # 4. Web Search with article title
        clean_title = ' '.join(title.split()[:6])
        web_image = self.search_web_image(clean_title)
        if web_image:
            return web_image

        # 5. Diverse category fallback (randomized within category)
        return self._get_fallback_image(category)

    def _get_fallback_image(self, category: Optional[str]) -> str:
        """Diverse professional fallback images — randomized to avoid repetition."""
        fallbacks = {
            "fintech": [
                "https://images.pexels.com/photos/6214476/pexels-photo-6214476.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/4386431/pexels-photo-4386431.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/6289065/pexels-photo-6289065.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "finance": [
                "https://images.pexels.com/photos/6801648/pexels-photo-6801648.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/7567443/pexels-photo-7567443.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/6120214/pexels-photo-6120214.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "tech": [
                "https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3184611/pexels-photo-3184611.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "startup": [
                "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "business": [
                "https://images.pexels.com/photos/3184287/pexels-photo-3184287.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3182812/pexels-photo-3182812.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3184339/pexels-photo-3184339.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "regulation": [
                "https://images.pexels.com/photos/5668473/pexels-photo-5668473.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/5669619/pexels-photo-5669619.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/4427611/pexels-photo-4427611.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "energy": [
                "https://images.pexels.com/photos/9875441/pexels-photo-9875441.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/414837/pexels-photo-414837.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/2800832/pexels-photo-2800832.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "markets": [
                "https://images.pexels.com/photos/6801648/pexels-photo-6801648.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/6120214/pexels-photo-6120214.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/7567443/pexels-photo-7567443.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
            "default": [
                "https://images.pexels.com/photos/3184287/pexels-photo-3184287.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3184611/pexels-photo-3184611.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3182812/pexels-photo-3182812.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/7567443/pexels-photo-7567443.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/6120214/pexels-photo-6120214.jpeg?auto=compress&cs=tinysrgb&w=800",
                "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&w=800",
            ],
        }
        key = (category or "default").lower()
        # Normalize category names (French → key)
        category_map = {
            "économie": "finance", "economie": "finance",
            "régulation": "regulation",
            "énergie": "energy",
            "marchés": "markets",
            "vc": "startup",
            "banking": "finance",
            "latest": "default",
            "actualité": "default",
        }
        key = category_map.get(key, key)
        image_list = fallbacks.get(key, fallbacks["default"])
        return random.choice(image_list)


def fetch_article_image(
    title: str,
    category: Optional[str] = None,
    country: Optional[str] = None,
    keywords: Optional[str] = None,
    existing_url: Optional[str] = None
) -> str:
    return ImageFetcher().fetch_image_url(title, category, keywords=keywords, existing_url=existing_url)
