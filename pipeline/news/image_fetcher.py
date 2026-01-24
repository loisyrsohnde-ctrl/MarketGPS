"""
MarketGPS News Pipeline - Image Fetcher

Fetches HIGHLY RELEVANT images using DuckDuckGo Search (Google Images alternative).
Prioritizes specific entity images over generic stock photos.
"""

import os
import random
import requests
from typing import Optional
from duckduckgo_search import DDGS

from core.config import get_logger

logger = get_logger(__name__)

class ImageFetcher:
    """Fetches real-world context images for news articles."""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def search_web_image(self, query: str) -> Optional[str]:
        """
        Search for a specific image on the web using DuckDuckGo.
        Returns a direct image URL.
        """
        try:
            # Search for images (Safe search on, Aspect ratio Wide)
            # We add "news" or "business" to context to avoid weird memes
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
                # Try to find a high-quality URL from the first few results
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
            # Skip some problematic domains or formats
            if any(x in url.lower() for x in ['.svg', 'base64', 'data:image']):
                return False
                
            response = self.session.head(url, timeout=3, allow_redirects=True)
            content_type = response.headers.get("Content-Type", "")
            return response.status_code == 200 and "image" in content_type
        except:
            return False

    def fetch_image_url(
        self, 
        title: str, 
        category: Optional[str] = None,
        keywords: Optional[str] = None,
        existing_url: Optional[str] = None
    ) -> str:
        """
        Get the best possible image.
        Priority:
        1. Web Search for specific entities (highly relevant)
        2. Valid existing URL from source
        3. Fallback to generic category image
        """
        # 1. Try Web Search first for specific visual keywords if provided by LLM
        # This gives the most "newspaper-like" feel (specific photos of people/places)
        if keywords:
            logger.info(f"Searching web for image: {keywords}")
            web_image = self.search_web_image(keywords)
            if web_image:
                return web_image
        
        # 2. Try Web Search with title if no keywords
        clean_title = ' '.join(title.split()[:6]) # First 6 words
        web_image = self.search_web_image(clean_title)
        if web_image:
            return web_image

        # 3. Fallback to existing URL if valid
        if existing_url and self._validate_image_url(existing_url):
            return existing_url

        # 4. Last resort: Category fallback (updated with professional business look)
        return self._get_fallback_image(category)

    def _get_fallback_image(self, category: Optional[str]) -> str:
        """Professional fallback images."""
        fallbacks = {
            "fintech": "https://images.pexels.com/photos/6214476/pexels-photo-6214476.jpeg?auto=compress&cs=tinysrgb&w=800", # Mobile money
            "finance": "https://images.pexels.com/photos/6801648/pexels-photo-6801648.jpeg?auto=compress&cs=tinysrgb&w=800", # Stock chart
            "tech": "https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg?auto=compress&cs=tinysrgb&w=800", # Coding/Office
            "startup": "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg?auto=compress&cs=tinysrgb&w=800", # Meeting
            "default": "https://images.pexels.com/photos/3184287/pexels-photo-3184287.jpeg?auto=compress&cs=tinysrgb&w=800" # Handshake
        }
        key = (category or "default").lower()
        return fallbacks.get(key, fallbacks["default"])

def fetch_article_image(
    title: str,
    category: Optional[str] = None,
    country: Optional[str] = None,
    keywords: Optional[str] = None,
    existing_url: Optional[str] = None
) -> str:
    return ImageFetcher().fetch_image_url(title, category, keywords, existing_url)
