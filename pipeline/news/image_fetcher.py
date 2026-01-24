"""
MarketGPS News Pipeline - Image Fetcher

Fetches relevant images for articles using free image APIs.
"""

import os
import re
import hashlib
import requests
from typing import Optional, List
from pathlib import Path

from core.config import get_logger

logger = get_logger(__name__)

# Free image sources (no API key needed for basic usage)
UNSPLASH_SOURCE_URL = "https://source.unsplash.com/800x450/"


class ImageFetcher:
    """Fetches relevant images for news articles."""
    
    # Keywords mapping for better image search
    CATEGORY_KEYWORDS = {
        "fintech": ["fintech", "mobile payment", "digital banking", "smartphone finance"],
        "finance": ["finance", "stock market", "business meeting", "african economy"],
        "startup": ["startup", "entrepreneur", "innovation", "tech office"],
        "tech": ["technology", "computer", "coding", "digital"],
        "banking": ["bank", "banking", "atm", "financial"],
        "crypto": ["cryptocurrency", "bitcoin", "blockchain", "digital currency"],
        "regulation": ["government", "policy", "law", "regulation"],
        "économie": ["economy", "business", "trade", "market"],
    }
    
    # Africa-specific image keywords to add context
    AFRICA_KEYWORDS = ["africa", "african", "lagos", "nairobi", "johannesburg"]
    
    def __init__(self):
        """Initialize the image fetcher."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MarketGPS/1.0 (+https://marketgps.online)"
        })
    
    def _generate_search_query(self, title: str, category: Optional[str], country: Optional[str]) -> str:
        """Generate a search query based on article metadata."""
        keywords = []
        
        # Add category-based keywords
        if category:
            cat_lower = category.lower()
            if cat_lower in self.CATEGORY_KEYWORDS:
                keywords.extend(self.CATEGORY_KEYWORDS[cat_lower][:2])
            else:
                keywords.append(cat_lower)
        
        # Add Africa context
        if country:
            country_names = {
                "NG": "nigeria lagos",
                "ZA": "south africa johannesburg",
                "KE": "kenya nairobi",
                "EG": "egypt cairo",
                "GH": "ghana accra",
                "CI": "ivory coast abidjan",
                "SN": "senegal dakar",
                "MA": "morocco casablanca",
                "CM": "cameroon douala",
            }
            if country in country_names:
                keywords.append(country_names[country])
        else:
            keywords.append("africa business")
        
        # Extract key terms from title (simple approach)
        title_words = re.findall(r'\b[A-Za-z]{4,}\b', title.lower())
        important_words = [w for w in title_words if w not in 
                         ['avec', 'pour', 'dans', 'vers', 'une', 'les', 'des', 'the', 'and', 'for']]
        keywords.extend(important_words[:2])
        
        # Build query
        query = " ".join(keywords[:4])
        return query
    
    def fetch_image_url(
        self, 
        title: str, 
        category: Optional[str] = None,
        country: Optional[str] = None,
        fallback_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch a relevant image URL for an article.
        
        Uses Unsplash Source API for free, high-quality images.
        
        Args:
            title: Article title
            category: Article category
            country: Country code
            fallback_url: URL to return if fetch fails
            
        Returns:
            Image URL or fallback
        """
        try:
            query = self._generate_search_query(title, category, country)
            
            # Use Unsplash Source API (redirects to a random matching image)
            # Format: https://source.unsplash.com/800x450/?keyword1,keyword2
            keywords = query.replace(" ", ",")
            image_url = f"https://source.unsplash.com/800x450/?{keywords}"
            
            # Verify the URL works by making a HEAD request
            response = self.session.head(image_url, allow_redirects=True, timeout=5)
            
            if response.status_code == 200:
                # Return the final redirected URL (actual image)
                return response.url
            
        except Exception as e:
            logger.warning(f"Image fetch failed: {e}")
        
        return fallback_url
    
    def get_fallback_image(self, category: Optional[str] = None) -> str:
        """Get a fallback image URL based on category."""
        # Use category-based Unsplash images as fallback
        if category:
            cat_lower = category.lower()
            return f"https://source.unsplash.com/800x450/?{cat_lower},africa,business"
        
        return "https://source.unsplash.com/800x450/?africa,business,finance"


def fetch_article_image(
    title: str,
    category: Optional[str] = None,
    country: Optional[str] = None,
    existing_url: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to fetch an image for an article.
    
    Args:
        title: Article title
        category: Article category  
        country: Country code
        existing_url: Existing image URL (returned if valid)
        
    Returns:
        Image URL
    """
    # If there's already a valid image URL, use it
    if existing_url and existing_url.startswith("http"):
        return existing_url
    
    fetcher = ImageFetcher()
    return fetcher.fetch_image_url(
        title=title,
        category=category,
        country=country,
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
