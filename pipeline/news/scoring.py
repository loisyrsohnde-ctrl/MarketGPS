"""
MarketGPS News Scoring Module
Calculates engagement scores and detects breaking news.
"""
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Mots-clés pour détecter les breaking news
BREAKING_KEYWORDS_FR = [
    "breaking", "urgent", "alerte", "exclusif", "vient de", "en direct",
    "dernière minute", "flash", "annonce", "officiel", "confirmation",
    "révélation", "scandale", "crash", "effondrement", "record"
]

BREAKING_KEYWORDS_EN = [
    "breaking", "urgent", "alert", "exclusive", "just in", "live",
    "breaking news", "flash", "announcement", "official", "confirmed",
    "revealed", "scandal", "crash", "collapse", "record", "major"
]

# Mots-clés de haute importance (finance/business)
HIGH_IMPORTANCE_KEYWORDS = [
    # Français
    "milliard", "million", "acquisition", "fusion", "ipo", "levée de fonds",
    "faillite", "banque centrale", "taux directeur", "inflation",
    "régulation", "licence", "partenariat stratégique",
    # Anglais
    "billion", "million", "acquisition", "merger", "ipo", "funding round",
    "bankruptcy", "central bank", "interest rate", "inflation",
    "regulation", "license", "strategic partnership", "unicorn"
]

# Entités importantes (entreprises, institutions)
IMPORTANT_ENTITIES = [
    # Banques centrales
    "bceao", "beac", "cbk", "sarb", "cbn", "bank of ghana",
    # Grandes entreprises tech
    "flutterwave", "paystack", "interswitch", "m-pesa", "mtn", "orange money",
    "wave", "chipper cash", "opay", "palmpay", "kuda", "moniepoint",
    # Institutions
    "bad", "afd", "ifc", "fmi", "banque mondiale", "african development bank"
]


def calculate_trust_score(source_name: str, sources_registry: Dict) -> float:
    """Get trust score from source registry."""
    for source in sources_registry.get("sources", []):
        if source.get("name", "").lower() == source_name.lower():
            return source.get("trust_score", 0.7)
    return 0.7  # Default


def calculate_content_quality_score(
    title: str,
    content: str,
    excerpt: str = "",
    has_image: bool = False,
    tags: List[str] = None
) -> float:
    """
    Calculate content quality score based on various factors.
    Returns a score between 0.0 and 1.0.
    """
    score = 0.0
    tags = tags or []

    # 1. Content length (max 0.25)
    word_count = len(content.split()) if content else 0
    if word_count >= 500:
        score += 0.25
    elif word_count >= 300:
        score += 0.20
    elif word_count >= 150:
        score += 0.15
    elif word_count >= 50:
        score += 0.10

    # 2. Title quality (max 0.20)
    title_words = len(title.split()) if title else 0
    if 5 <= title_words <= 15:
        score += 0.20  # Optimal title length
    elif 3 <= title_words <= 20:
        score += 0.15
    else:
        score += 0.05

    # 3. Has excerpt (max 0.10)
    if excerpt and len(excerpt) >= 50:
        score += 0.10

    # 4. Has image (max 0.15)
    if has_image:
        score += 0.15

    # 5. Important entities mentioned (max 0.15)
    text_lower = f"{title} {content}".lower()
    entities_found = sum(1 for entity in IMPORTANT_ENTITIES if entity in text_lower)
    score += min(0.15, entities_found * 0.05)

    # 6. Tags richness (max 0.15)
    if tags:
        score += min(0.15, len(tags) * 0.03)

    return min(1.0, score)


def calculate_freshness_score(published_at: str) -> float:
    """
    Calculate freshness score based on publication time.
    Newer articles get higher scores.
    Returns a score between 0.0 and 1.0.
    """
    if not published_at:
        return 0.5  # Default for unknown dates

    try:
        # Parse various date formats
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                pub_date = datetime.strptime(published_at[:19], fmt)
                break
            except ValueError:
                continue
        else:
            return 0.5

        now = datetime.utcnow()
        age = now - pub_date

        # Score based on age
        if age < timedelta(hours=1):
            return 1.0
        elif age < timedelta(hours=3):
            return 0.95
        elif age < timedelta(hours=6):
            return 0.90
        elif age < timedelta(hours=12):
            return 0.80
        elif age < timedelta(hours=24):
            return 0.70
        elif age < timedelta(days=2):
            return 0.60
        elif age < timedelta(days=3):
            return 0.50
        elif age < timedelta(days=7):
            return 0.40
        elif age < timedelta(days=14):
            return 0.30
        elif age < timedelta(days=30):
            return 0.20
        else:
            return 0.10

    except Exception:
        return 0.5


def calculate_user_engagement_score(
    save_count: int,
    view_count: int,
    total_users: int = 100
) -> float:
    """
    Calculate user engagement score based on saves and views.
    Returns a score between 0.0 and 1.0.
    """
    if total_users <= 0:
        total_users = 100

    # Save ratio (saves are more valuable than views)
    save_ratio = min(1.0, save_count / max(1, total_users * 0.1))

    # View ratio (normalized)
    view_ratio = min(1.0, view_count / max(1, total_users * 2))

    # Combined score (saves weighted more heavily)
    score = (save_ratio * 0.7) + (view_ratio * 0.3)

    return min(1.0, score)


def calculate_engagement_score(
    trust_score: float,
    content_quality_score: float,
    freshness_score: float,
    user_engagement_score: float
) -> float:
    """
    Calculate final engagement score using weighted average.

    Weights:
    - Trust score: 30% (source reliability)
    - Content quality: 25% (article richness)
    - Freshness: 25% (recency)
    - User engagement: 20% (saves/views)
    """
    return (
        (trust_score * 0.30) +
        (content_quality_score * 0.25) +
        (freshness_score * 0.25) +
        (user_engagement_score * 0.20)
    )


def detect_breaking_news(
    title: str,
    content: str,
    trust_score: float,
    published_at: str,
    engagement_score: float
) -> Tuple[bool, str]:
    """
    Detect if an article qualifies as breaking news.
    Returns (is_breaking, importance_level).

    Importance levels:
    - 'breaking': Urgent, time-sensitive news
    - 'high': Important but not urgent
    - 'normal': Regular news
    - 'low': Less important content
    """
    text_lower = f"{title} {content}".lower()

    # Check for breaking keywords
    has_breaking_keyword = any(
        kw in text_lower
        for kw in BREAKING_KEYWORDS_FR + BREAKING_KEYWORDS_EN
    )

    # Check for high importance keywords
    has_importance_keyword = any(
        kw in text_lower
        for kw in HIGH_IMPORTANCE_KEYWORDS
    )

    # Check freshness
    freshness = calculate_freshness_score(published_at)
    is_very_fresh = freshness >= 0.90  # < 3 hours old

    # Decision logic
    if has_breaking_keyword and is_very_fresh and trust_score >= 0.85:
        return True, "breaking"

    if has_breaking_keyword and trust_score >= 0.80 and engagement_score >= 0.75:
        return True, "breaking"

    if has_importance_keyword and is_very_fresh and trust_score >= 0.80:
        return False, "high"

    if engagement_score >= 0.80:
        return False, "high"

    if engagement_score >= 0.50:
        return False, "normal"

    return False, "low"


def score_article(
    title: str,
    content: str,
    excerpt: str,
    source_name: str,
    published_at: str,
    image_url: Optional[str],
    tags: List[str],
    save_count: int = 0,
    view_count: int = 0,
    sources_registry: Dict = None
) -> Dict[str, Any]:
    """
    Calculate all scores for an article.
    Returns a dict with all scoring information.
    """
    sources_registry = sources_registry or {"sources": []}

    # Calculate individual scores
    trust = calculate_trust_score(source_name, sources_registry)
    quality = calculate_content_quality_score(
        title, content, excerpt,
        has_image=bool(image_url),
        tags=tags
    )
    freshness = calculate_freshness_score(published_at)
    engagement = calculate_user_engagement_score(save_count, view_count)

    # Final engagement score
    final_score = calculate_engagement_score(trust, quality, freshness, engagement)

    # Breaking news detection
    is_breaking, importance_level = detect_breaking_news(
        title, content, trust, published_at, final_score
    )

    return {
        "engagement_score": round(final_score, 3),
        "trust_score": round(trust, 3),
        "content_quality_score": round(quality, 3),
        "freshness_score": round(freshness, 3),
        "user_engagement_score": round(engagement, 3),
        "is_breaking_news": is_breaking,
        "importance_level": importance_level
    }


def load_sources_registry() -> Dict:
    """Load the sources registry JSON file."""
    registry_path = Path(__file__).parent / "sources_registry.json"
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sources": []}


# For direct testing
if __name__ == "__main__":
    # Test the scoring system
    test_article = score_article(
        title="BREAKING: Flutterwave lève 250 millions de dollars",
        content="La fintech nigériane Flutterwave vient d'annoncer une levée de fonds de 250 millions de dollars...",
        excerpt="Flutterwave annonce une levée de fonds record",
        source_name="TechCabal",
        published_at=datetime.utcnow().isoformat(),
        image_url="https://example.com/image.jpg",
        tags=["fintech", "funding", "nigeria"],
        save_count=5,
        view_count=100,
        sources_registry=load_sources_registry()
    )

    print("Test Article Scores:")
    for key, value in test_article.items():
        print(f"  {key}: {value}")
