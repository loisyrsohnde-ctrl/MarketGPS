"""
MarketGPS News Pipeline - Image Fetcher

Downloads unique images for each article using free APIs.
"""

import os
import re
import hashlib
import random
import requests
from typing import Optional, List
from urllib.parse import quote, urlencode

from core.config import get_logger

logger = get_logger(__name__)


class ImageFetcher:
    """Fetches and downloads relevant images for news articles."""
    
    # Pixabay API (free, 100 requests/minute)
    PIXABAY_API_URL = "https://pixabay.com/api/"
    
    # Large pool of curated business/finance images from Pexels CDN (direct links)
    CURATED_IMAGES = {
        "fintech": [
            "https://images.pexels.com/photos/6963944/pexels-photo-6963944.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6289065/pexels-photo-6289065.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6214476/pexels-photo-6214476.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5926389/pexels-photo-5926389.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6347720/pexels-photo-6347720.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5849559/pexels-photo-5849559.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4386431/pexels-photo-4386431.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6347707/pexels-photo-6347707.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "finance": [
            "https://images.pexels.com/photos/7567443/pexels-photo-7567443.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6801648/pexels-photo-6801648.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5716001/pexels-photo-5716001.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5980856/pexels-photo-5980856.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5716025/pexels-photo-5716025.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/7172827/pexels-photo-7172827.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5849592/pexels-photo-5849592.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4386476/pexels-photo-4386476.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "startup": [
            "https://images.pexels.com/photos/3184360/pexels-photo-3184360.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3182812/pexels-photo-3182812.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184405/pexels-photo-3184405.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3182773/pexels-photo-3182773.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184339/pexels-photo-3184339.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "tech": [
            "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3912981/pexels-photo-3912981.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3183197/pexels-photo-3183197.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/1181673/pexels-photo-1181673.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3182826/pexels-photo-3182826.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "banking": [
            "https://images.pexels.com/photos/4386158/pexels-photo-4386158.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6693661/pexels-photo-6693661.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4386373/pexels-photo-4386373.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5926382/pexels-photo-5926382.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4386442/pexels-photo-4386442.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5716032/pexels-photo-5716032.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6347720/pexels-photo-6347720.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5849577/pexels-photo-5849577.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "business": [
            "https://images.pexels.com/photos/3184287/pexels-photo-3184287.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184357/pexels-photo-3184357.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184338/pexels-photo-3184338.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184416/pexels-photo-3184416.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184306/pexels-photo-3184306.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184325/pexels-photo-3184325.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184431/pexels-photo-3184431.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "économie": [
            "https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6801647/pexels-photo-6801647.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5980866/pexels-photo-5980866.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/7567565/pexels-photo-7567565.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5849561/pexels-photo-5849561.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4386431/pexels-photo-4386431.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6693655/pexels-photo-6693655.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5716001/pexels-photo-5716001.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "actualité": [
            "https://images.pexels.com/photos/3184339/pexels-photo-3184339.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184357/pexels-photo-3184357.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5717411/pexels-photo-5717411.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3182812/pexels-photo-3182812.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184416/pexels-photo-3184416.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3182773/pexels-photo-3182773.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/3182826/pexels-photo-3182826.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "régulation": [
            "https://images.pexels.com/photos/5668859/pexels-photo-5668859.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5669619/pexels-photo-5669619.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4427621/pexels-photo-4427621.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5668858/pexels-photo-5668858.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5668773/pexels-photo-5668773.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5669614/pexels-photo-5669614.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/4427430/pexels-photo-4427430.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/5668856/pexels-photo-5668856.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
        "crypto": [
            "https://images.pexels.com/photos/6771900/pexels-photo-6771900.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6770609/pexels-photo-6770609.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6771985/pexels-photo-6771985.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6781273/pexels-photo-6781273.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6778656/pexels-photo-6778656.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6771607/pexels-photo-6771607.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/8370752/pexels-photo-8370752.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg?auto=compress&cs=tinysrgb&w=800",
        ],
    }
    
    # Track used images to avoid duplicates within session
    _used_images = set()
    
    def __init__(self):
        """Initialize the image fetcher."""
        self.pixabay_key = os.environ.get("PIXABAY_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    def _search_pixabay(self, query: str) -> Optional[str]:
        """Search Pixabay for an image."""
        if not self.pixabay_key:
            return None
            
        try:
            params = {
                "key": self.pixabay_key,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "min_width": 800,
                "per_page": 10,
                "safesearch": "true"
            }
            
            response = self.session.get(self.PIXABAY_API_URL, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", [])
                if hits:
                    # Pick a random image from results
                    hit = random.choice(hits)
                    return hit.get("webformatURL") or hit.get("largeImageURL")
                    
        except Exception as e:
            logger.debug(f"Pixabay search failed: {e}")
        
        return None
    
    def get_unique_image(self, title: str, category: Optional[str] = None, article_id: Optional[str] = None) -> str:
        """
        Get a unique image for the article.
        
        Uses title hash to ensure same article always gets same image,
        but different articles get different images.
        """
        # Create a hash from title to get consistent but unique selection
        title_hash = hashlib.md5(title.encode()).hexdigest()
        hash_int = int(title_hash[:8], 16)
        
        # Determine category for image pool
        cat_lower = (category or "business").lower()
        if cat_lower not in self.CURATED_IMAGES:
            cat_lower = "business"
        
        # Get image pool for this category
        image_pool = self.CURATED_IMAGES[cat_lower]
        
        # Select image based on hash (consistent per title)
        idx = hash_int % len(image_pool)
        selected_image = image_pool[idx]
        
        # If this image was recently used, try next one
        attempts = 0
        while selected_image in self._used_images and attempts < len(image_pool):
            idx = (idx + 1) % len(image_pool)
            selected_image = image_pool[idx]
            attempts += 1
        
        # Track this image as used
        self._used_images.add(selected_image)
        
        # Reset tracker if it gets too large
        if len(self._used_images) > 50:
            self._used_images.clear()
        
        return selected_image
    
    def fetch_image_url(
        self, 
        title: str, 
        category: Optional[str] = None,
        country: Optional[str] = None,
        keywords: Optional[str] = None,
        existing_url: Optional[str] = None
    ) -> str:
        """
        Fetch a relevant image URL for an article.
        
        Priority:
        1. Valid existing URL from source
        2. Pixabay search (if API key available)
        3. Curated image pool (guaranteed unique per article)
        """
        # Check if existing URL is valid
        if existing_url and existing_url.startswith("http"):
            try:
                resp = self.session.head(existing_url, timeout=3, allow_redirects=True)
                if resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "image" in content_type:
                        return existing_url
            except:
                pass
        
        # Try Pixabay if we have keywords and API key
        if keywords and self.pixabay_key:
            pixabay_url = self._search_pixabay(keywords)
            if pixabay_url:
                return pixabay_url
        
        # Fall back to curated images (always works)
        return self.get_unique_image(title, category)


def fetch_article_image(
    title: str,
    category: Optional[str] = None,
    country: Optional[str] = None,
    keywords: Optional[str] = None,
    existing_url: Optional[str] = None
) -> str:
    """
    Convenience function to fetch an image for an article.
    
    Returns:
        Image URL (always returns a valid URL)
    """
    fetcher = ImageFetcher()
    return fetcher.fetch_image_url(
        title=title,
        category=category,
        country=country,
        keywords=keywords,
        existing_url=existing_url
    )


if __name__ == "__main__":
    # Test with different titles
    titles = [
        "Flutterwave raises $250M Series D funding",
        "Kenya's M-Pesa hits 50 million users",
        "Nigeria Central Bank new regulations",
    ]
    
    for title in titles:
        url = fetch_article_image(title=title, category="Fintech")
        print(f"{title[:40]}... -> {url[:60]}...")
