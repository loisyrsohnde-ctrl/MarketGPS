"""
MarketGPS News Pipeline - Image Fetcher

Fetches relevant images for articles using Pexels API.
"""

import os
import re
import hashlib
import requests
from typing import Optional, List
from urllib.parse import quote

from core.config import get_logger

logger = get_logger(__name__)


class ImageFetcher:
    """Fetches relevant images for news articles using Pexels API."""
    
    # Pexels API (free, reliable)
    PEXELS_API_URL = "https://api.pexels.com/v1/search"
    
    # Category to search query mapping
    CATEGORY_QUERIES = {
        "fintech": "mobile payment technology africa",
        "finance": "african business finance",
        "startup": "african entrepreneur startup",
        "tech": "technology africa digital",
        "banking": "bank finance africa",
        "crypto": "cryptocurrency blockchain",
        "régulation": "government policy africa",
        "économie": "african economy market",
        "business": "african business meeting",
        "actualité": "africa city business",
    }
    
    # Fallback images (curated high-quality Pexels images - direct links)
    FALLBACK_IMAGES = {
        "fintech": "https://images.pexels.com/photos/6963944/pexels-photo-6963944.jpeg?auto=compress&cs=tinysrgb&w=800",
        "finance": "https://images.pexels.com/photos/7567443/pexels-photo-7567443.jpeg?auto=compress&cs=tinysrgb&w=800",
        "startup": "https://images.pexels.com/photos/3184360/pexels-photo-3184360.jpeg?auto=compress&cs=tinysrgb&w=800",
        "tech": "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&w=800",
        "banking": "https://images.pexels.com/photos/4386158/pexels-photo-4386158.jpeg?auto=compress&cs=tinysrgb&w=800",
        "crypto": "https://images.pexels.com/photos/6771900/pexels-photo-6771900.jpeg?auto=compress&cs=tinysrgb&w=800",
        "business": "https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=800",
        "économie": "https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg?auto=compress&cs=tinysrgb&w=800",
        "default": "https://images.pexels.com/photos/3184287/pexels-photo-3184287.jpeg?auto=compress&cs=tinysrgb&w=800",
    }
    
    def __init__(self):
        """Initialize the image fetcher."""
        self.pexels_key = os.environ.get("PEXELS_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MarketGPS/1.0 (+https://marketgps.online)"
        })
        if self.pexels_key:
            self.session.headers["Authorization"] = self.pexels_key
    
    def _get_search_query(self, title: str, category: Optional[str], keywords: Optional[str]) -> str:
        """Generate search query for Pexels."""
        # Use provided keywords if available
        if keywords:
            return keywords
        
        # Use category mapping
        if category:
            cat_lower = category.lower()
            if cat_lower in self.CATEGORY_QUERIES:
                return self.CATEGORY_QUERIES[cat_lower]
        
        # Extract keywords from title
        return "africa business finance"
    
    def fetch_image_url(
        self, 
        title: str, 
        category: Optional[str] = None,
        country: Optional[str] = None,
        keywords: Optional[str] = None,
        fallback_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch a relevant image URL for an article.
        
        Uses Pexels API if key available, otherwise returns curated fallback.
        """
        # If we have a Pexels API key, try to fetch a relevant image
        if self.pexels_key:
            try:
                query = self._get_search_query(title, category, keywords)
                
                response = self.session.get(
                    self.PEXELS_API_URL,
                    params={
                        "query": query,
                        "per_page": 5,
                        "orientation": "landscape"
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    photos = data.get("photos", [])
                    if photos:
                        # Get a random-ish photo based on title hash
                        idx = hash(title) % len(photos)
                        photo = photos[idx]
                        # Return medium size (good balance of quality/speed)
                        return photo.get("src", {}).get("large", photo.get("src", {}).get("medium"))
                        
            except Exception as e:
                logger.warning(f"Pexels API failed: {e}")
        
        # Return category-based fallback
        return self.get_fallback_image(category)
    
    def get_fallback_image(self, category: Optional[str] = None) -> str:
        """Get a fallback image URL based on category."""
        if category:
            cat_lower = category.lower()
            if cat_lower in self.FALLBACK_IMAGES:
                return self.FALLBACK_IMAGES[cat_lower]
        
        return self.FALLBACK_IMAGES["default"]


def fetch_article_image(
    title: str,
    category: Optional[str] = None,
    country: Optional[str] = None,
    keywords: Optional[str] = None,
    existing_url: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to fetch an image for an article.
    
    Args:
        title: Article title
        category: Article category  
        country: Country code
        keywords: Image search keywords from LLM
        existing_url: Existing image URL (returned if valid)
        
    Returns:
        Image URL
    """
    # If there's already a valid image URL, verify it works
    if existing_url and existing_url.startswith("http"):
        try:
            # Quick HEAD check to verify image exists
            resp = requests.head(existing_url, timeout=3, allow_redirects=True)
            if resp.status_code == 200:
                return existing_url
        except:
            pass
    
    fetcher = ImageFetcher()
    return fetcher.fetch_image_url(
        title=title,
        category=category,
        country=country,
        keywords=keywords,
        fallback_url=fetcher.get_fallback_image(category)
    )


if __name__ == "__main__":
    # Test
    url = fetch_article_image(
        title="Flutterwave raises $250M Series D funding",
        category="Fintech",
        country="NG"
    )
    print(f"Image URL: {url}")
