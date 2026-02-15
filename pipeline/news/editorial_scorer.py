"""
Editorial Scorer — Intelligence-driven article clustering and scoring.

Ce module:
1. Groupe les articles par sujet via chevauchement de mots-clés
2. Calcule un score éditorial composé de:
   - 40% Source Diversity (nombre de sources par topic)
   - 25% Verified Engagement (interactions validées)
   - 15% Topic Importance (keywords et entities)
   - 10% Freshness (age de l'article)
   - 10% Geographic Relevance (pertinence géographique)
3. Marque les articles avec score éditorial et cluster ID
4. Retourne les top articles triés par score éditorial

Auteur: MarketGPS
Date: Février 2026
"""

import os
import re
import json
import logging
import unicodedata
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

ENABLE_EDITORIAL_SCORER = os.environ.get("ENABLE_EDITORIAL_SCORER", "true").lower() == "true"

# Weights (must sum to 1.0)
W_SOURCE_DIVERSITY = float(os.environ.get("ED_W_SOURCE_DIVERSITY", "0.40"))
W_VERIFIED_ENGAGEMENT = float(os.environ.get("ED_W_VERIFIED_ENGAGEMENT", "0.25"))
W_TOPIC_IMPORTANCE = float(os.environ.get("ED_W_TOPIC_IMPORTANCE", "0.15"))
W_FRESHNESS = float(os.environ.get("ED_W_FRESHNESS", "0.10"))
W_GEO_RELEVANCE = float(os.environ.get("ED_W_GEO_RELEVANCE", "0.10"))

# Top-K config
TOP_K_EDITORIAL = int(os.environ.get("ED_TOP_K", "30"))
MIN_SCORE_EDITORIAL = float(os.environ.get("ED_MIN_SCORE", "30"))

# Francophone sub-Saharan — Tier 1 : CI & CM (priorité maximale)
TIER1_GEO_PRIORITY = {"CI", "CM"}

# Francophone sub-Saharan — Tier 2 : Autres pays francophones
TIER2_GEO_FRANCOPHONE = {"SN", "BF", "ML", "TG", "BJ", "GA", "CG", "CD", "NE", "GN", "TD"}

# Tous combinés (rétro-compatibilité)
FRANCOPHONE_SSA = TIER1_GEO_PRIORITY | TIER2_GEO_FRANCOPHONE

# Stop words for title normalization (French + English)
STOP_WORDS = {
    # French
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "en", "à", "au", "aux",
    "pour", "par", "sur", "dans", "avec", "qui", "que", "ce", "cette", "ces",
    "ou", "pas", "ne", "se", "il", "elle", "on", "sont", "est", "ai", "a",
    # English
    "the", "a", "an", "of", "to", "in", "for", "on", "with", "at", "by", "from",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "and", "or", "but", "as", "if", "this", "that", "which", "who", "where", "when", "why",
}

# Topic importance keywords
TOPIC_IMPORTANCE_KEYWORDS = {
    "ipo", "acquisition", "fusion", "merger", "levée de fonds", "funding round",
    "banque centrale", "central bank", "régulation", "regulation", "licence", "license",
    "milliard", "million", "billion", "record", "historique", "first", "breakthrough",
    "bceao", "bad", "fmi", "imf", "bafد", "afdb", "union africaine", "african union",
    "cemac", "uemoa", "zlecaf", "trade", "accord", "agreement", "sommet", "summit",
    "investing", "investissement", "croissance", "growth", "startup", "fintech",
    "paystack", "flutterwave", "mtn", "orange", "wave", "chipper", "opay",
}

# ═══════════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EditorialScore:
    """Résultat du scoring éditorial pour un article."""
    article_id: int
    editorial_score: float           # 0-100
    reasons: List[str]              # Top raisons
    component_scores: Dict[str, float]  # Détail par composant
    cluster_id: Optional[str] = None
    cluster_size: int = 1
    cluster_sources: List[str] = field(default_factory=list)
    scored_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════
# Core Editorial Scorer
# ═══════════════════════════════════════════════════════════════════════════

class EditorialScorer:
    """
    Scorer éditorial — calcule un score basé sur l'intelligence éditoriale.

    Focus: Source diversity (combien de sources couvrent le même topic).
    """

    def __init__(self, get_db_conn=None):
        self.get_conn = get_db_conn
        self._clusters: Dict[str, List[Dict]] = {}
        self._cluster_metadata: Dict[str, Dict] = {}

    # ─── Public API ───────────────────────────────────────────────────

    def score_and_rank(
        self,
        articles: Optional[List[Dict]] = None,
        top_k: int = TOP_K_EDITORIAL,
        min_score: float = MIN_SCORE_EDITORIAL,
        days_back: int = 3,
    ) -> List[EditorialScore]:
        """
        Score articles based on editorial intelligence.

        If articles is None, loads from DB (last `days_back` days).
        Returns top-K scored articles sorted by editorial_score DESC.
        """
        if not ENABLE_EDITORIAL_SCORER:
            logger.info("Editorial Scorer disabled (ENABLE_EDITORIAL_SCORER=false)")
            return []

        # 1. Load articles if not provided
        if articles is None:
            articles = self._load_recent_articles(days_back)

        if not articles:
            logger.info("No articles to score")
            return []

        logger.info(f"Scoring {len(articles)} articles with Editorial Scorer...")

        # 2. Cluster articles by topic
        self._cluster_articles(articles)
        logger.info(f"Clustered into {len(self._clusters)} topics")

        # 3. Score each article
        scored = []
        for article in articles:
            try:
                result = self._score_article(article)
                scored.append(result)
            except Exception as e:
                logger.error(f"Error scoring article {article.get('id')}: {e}")

        # 4. Filter by min score
        filtered = [s for s in scored if s.editorial_score >= min_score]

        # 5. Sort and take top-K
        filtered.sort(key=lambda s: s.editorial_score, reverse=True)
        top = filtered[:top_k]

        logger.info(
            f"Editorial scoring: {len(articles)} articles → "
            f"{len(scored)} scored → "
            f"{len(filtered)} above min_score → "
            f"{len(top)} top-K returned"
        )

        return top

    def score_single(self, article: Dict) -> EditorialScore:
        """Score a single article (for real-time use)."""
        self._cluster_articles([article])
        return self._score_article(article)

    # ─── Clustering Logic ────────────────────────────────────────────────

    def _normalize_title(self, title: str) -> str:
        """Normalize title for clustering."""
        t = title.lower().strip()
        # Remove accents
        t = unicodedata.normalize("NFD", t)
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        # Remove punctuation
        t = re.sub(r"[^\w\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _extract_key_terms(self, title: str) -> Set[str]:
        """Extract significant keywords from title for clustering."""
        norm = self._normalize_title(title)
        words = [w for w in norm.split() if len(w) > 3 and w not in STOP_WORDS]
        return set(words)

    def _cluster_articles(self, articles: List[Dict]):
        """
        Cluster articles by topic using keyword overlap.

        Articles with >50% keyword overlap are in the same cluster.
        """
        self._clusters = defaultdict(list)
        self._cluster_metadata = {}

        for article in articles:
            title = article.get("title", "")
            key_terms = self._extract_key_terms(title)

            # Try to find existing cluster
            assigned = False
            for cluster_id, cluster_articles in self._clusters.items():
                # Get key terms of first article in cluster
                if not cluster_articles:
                    continue

                cluster_title = cluster_articles[0].get("title", "")
                cluster_terms = self._extract_key_terms(cluster_title)

                # Calculate overlap
                if not key_terms or not cluster_terms:
                    continue

                overlap = len(key_terms & cluster_terms) / max(len(key_terms | cluster_terms), 1)
                if overlap >= 0.5:  # 50% overlap = same topic
                    cluster_id_to_use = cluster_id
                    self._clusters[cluster_id_to_use].append(article)
                    assigned = True
                    break

            if not assigned:
                # Create new cluster
                cluster_id = hashlib.md5(
                    self._normalize_title(title).encode()
                ).hexdigest()[:12]
                self._clusters[cluster_id].append(article)

    def _get_cluster_info(self, article_id: int) -> Tuple[str, int, List[str]]:
        """Get cluster info for an article."""
        for cluster_id, cluster_articles in self._clusters.items():
            for article in cluster_articles:
                if article.get("id") == article_id:
                    # Get unique sources in this cluster
                    sources = set()
                    for ca in cluster_articles:
                        source = (ca.get("source_name") or "").strip()
                        if source:
                            sources.add(source)

                    return cluster_id, len(cluster_articles), sorted(list(sources))

        # Not found
        return "", 1, []

    # ─── Scoring Logic ────────────────────────────────────────────────

    def _score_article(self, article: Dict) -> EditorialScore:
        """Compute editorial_score for one article."""
        now = datetime.utcnow()
        scored_at = now.isoformat()

        # Component scores (each 0-100)
        source_div = self._calc_source_diversity(article)
        engagement = self._calc_verified_engagement(article)
        importance = self._calc_topic_importance(article)
        freshness = self._calc_freshness(article, now)
        geo = self._calc_geo_relevance(article)

        # Weighted sum
        final = (
            source_div * W_SOURCE_DIVERSITY +
            engagement * W_VERIFIED_ENGAGEMENT +
            importance * W_TOPIC_IMPORTANCE +
            freshness * W_FRESHNESS +
            geo * W_GEO_RELEVANCE
        )

        # Clamp 0-100
        final = max(0, min(100, final))

        # Get cluster info
        cluster_id, cluster_size, cluster_sources = self._get_cluster_info(
            article.get("id", 0)
        )

        # Build reasons
        components = {
            "source_diversity": source_div,
            "verified_engagement": engagement,
            "topic_importance": importance,
            "freshness": freshness,
            "geo_relevance": geo,
        }
        reasons = self._build_reasons(components)

        return EditorialScore(
            article_id=article.get("id", 0),
            editorial_score=round(final, 1),
            reasons=reasons[:5],
            component_scores={k: round(v, 1) for k, v in components.items()},
            cluster_id=cluster_id,
            cluster_size=cluster_size,
            cluster_sources=cluster_sources,
            scored_at=scored_at,
        )

    # ─── Component Calculators ────────────────────────────────────────

    def _calc_source_diversity(self, article: Dict) -> float:
        """
        Score based on source diversity for this topic (KEY CRITERIA - 40%).

        1 source → 10/100
        2-3 sources → 40/100
        4-5 sources → 70/100
        6+ sources → 90-100/100
        """
        cluster_id, cluster_size, cluster_sources = self._get_cluster_info(
            article.get("id", 0)
        )
        num_sources = len(cluster_sources)

        if num_sources >= 6:
            # Bonus if multiple regions represented
            regions = self._detect_regions(cluster_sources)
            if len(regions) >= 2:
                return 100
            return 90
        elif num_sources >= 4:
            return 70
        elif num_sources >= 2:
            return 40
        else:
            return 10

    def _calc_verified_engagement(self, article: Dict) -> float:
        """
        Score based on validated interaction counts (25%).

        Normalize by source baseline and score based on ratio.
        """
        total = article.get("total_interactions", 0) or 0
        source_name = (article.get("source_name") or "").lower().strip()

        # Get source baseline
        from pipeline.news.interactions_fetcher import SOURCE_BASELINE
        baseline = SOURCE_BASELINE.get(source_name, SOURCE_BASELINE.get("default", 150))

        ratio = total / max(baseline, 1)

        # Map ratio to 0-100 score (more generous than viral_scorer)
        if ratio >= 3.0:
            return 100
        elif ratio >= 2.0:
            return 70 + (ratio - 2.0) / 1.0 * 30
        elif ratio >= 1.0:
            return 40 + (ratio - 1.0) * 30
        elif ratio >= 0.5:
            return 20 + (ratio - 0.5) / 0.5 * 20
        else:
            return ratio / 0.5 * 20

    def _calc_topic_importance(self, article: Dict) -> float:
        """
        Score based on topic importance (15%).

        Keywords: IPO, fusion, acquisition, régulation, banque centrale, etc.
        Entities: BCEAO, BAD, FMI, CEMAC, UEMOA, Union Africaine, etc.
        """
        title = (article.get("title") or "").lower()
        content = (article.get("content_md") or article.get("excerpt") or "").lower()
        text = title + " " + content[:500]

        # Count keyword matches
        matches = sum(1 for kw in TOPIC_IMPORTANCE_KEYWORDS if kw in text)

        # Title matches count double
        title_matches = sum(1 for kw in TOPIC_IMPORTANCE_KEYWORDS if kw in title)
        matches += title_matches

        # Score mapping
        if matches >= 6:
            return 100
        elif matches >= 4:
            return 75 + (matches - 4) / 2 * 25
        elif matches >= 2:
            return 45 + (matches - 2) / 2 * 30
        elif matches >= 1:
            return 25 + matches * 20
        return 0

    def _calc_freshness(self, article: Dict, now: datetime) -> float:
        """
        Score based on age (10%).

        < 6h: 100
        < 12h: 85
        < 24h: 70
        < 48h: 50
        > 48h: 20
        """
        published_at = self._parse_date(article.get("published_at"))
        if not published_at:
            return 50

        age_hours = (now - published_at).total_seconds() / 3600

        if age_hours < 6:
            return 100
        elif age_hours < 12:
            return 85
        elif age_hours < 24:
            return 70
        elif age_hours < 48:
            return 50
        else:
            return 20

    def _calc_geo_relevance(self, article: Dict) -> float:
        """
        Score based on geographic relevance (10%).

        Tier 1 (CI, CM): 100 — toujours prioritaires
        Tier 2 (autres francophones): 60 de base, monte à 85 si engagement > 500
        Anglophone Africa avec > 500 interactions: 70
        Autres: 30
        """
        country = (article.get("country") or "").upper()
        total = article.get("total_interactions", 0) or 0

        if country in TIER1_GEO_PRIORITY:
            return 100
        elif country in TIER2_GEO_FRANCOPHONE:
            # Les autres francophones peuvent monter s'ils ont du bon engagement
            if total >= 500:
                return 85
            return 60
        elif country in {"NG", "GH", "KE", "ZA", "TZ", "RW", "ET"}:
            if total >= 500:
                return 70
            return 50
        else:
            return 30

    def _detect_regions(self, sources: List[str]) -> Set[str]:
        """Detect regions from source names."""
        regions = set()

        for source in sources:
            source_lower = source.lower()
            if any(x in source_lower for x in ["jeune afrique", "agence ecofin", "africa"]):
                regions.add("pan-african")
            if any(x in source_lower for x in ["business daily", "punch", "thisday"]):
                regions.add("west")
            if any(x in source_lower for x in ["the eastafrican", "capital fm"]):
                regions.add("east")
            if any(x in source_lower for x in ["daily maverick", "itweb", "mybroadband"]):
                regions.add("south")

        return regions

    # ─── Reason Builder ───────────────────────────────────────────────

    def _build_reasons(self, components: Dict[str, float]) -> List[str]:
        """Build human-readable reasons for the score."""
        reasons = []

        sorted_comp = sorted(components.items(), key=lambda x: x[1], reverse=True)

        for comp_name, score in sorted_comp:
            if score <= 20:
                continue

            if comp_name == "source_diversity" and score >= 40:
                reasons.append(f"Couverture multi-sources ({score:.0f}%)")
            elif comp_name == "verified_engagement" and score >= 40:
                reasons.append(f"Engagement vérifié élevé ({score:.0f}%)")
            elif comp_name == "topic_importance" and score >= 40:
                reasons.append(f"Sujet éditorialement important ({score:.0f}%)")
            elif comp_name == "freshness" and score >= 70:
                reasons.append("Article très récent / Breaking")
            elif comp_name == "geo_relevance" and score >= 70:
                reasons.append("Pertinent pour l'audience cible")

        if not reasons:
            reasons.append("Score basé sur pertinence éditoriale")

        return reasons

    # ─── Database Operations ──────────────────────────────────────────

    def _load_recent_articles(self, days_back: int = 3) -> List[Dict]:
        """Load recent articles from DB."""
        if not self.get_conn:
            return []

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM news_articles
                WHERE created_at >= datetime('now', ?)
                ORDER BY created_at DESC
            """, (f"-{days_back} days",))

            columns = [desc[0] for desc in cursor.description]
            articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()

            logger.info(f"Loaded {len(articles)} articles from last {days_back} days")
            return articles

        except Exception as e:
            logger.error(f"Error loading articles: {e}")
            return []

    def save_scores(self, scored_articles: List[EditorialScore]) -> int:
        """Persist editorial scores to the database."""
        if not self.get_conn or not scored_articles:
            return 0

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Ensure columns exist
            for col, dtype, default in [
                ("editorial_score", "REAL", "0"),
                ("editorial_reasons", "TEXT", "NULL"),
                ("cluster_id_editorial", "TEXT", "NULL"),
                ("cluster_size", "INTEGER", "1"),
                ("cluster_sources", "TEXT", "NULL"),
                ("scored_at_editorial", "TEXT", "NULL"),
            ]:
                try:
                    cursor.execute(f"ALTER TABLE news_articles ADD COLUMN {col} {dtype} DEFAULT {default}")
                except Exception:
                    pass  # Column already exists

            # Update scores
            updated = 0
            for s in scored_articles:
                cursor.execute("""
                    UPDATE news_articles
                    SET editorial_score = ?,
                        editorial_reasons = ?,
                        cluster_id_editorial = ?,
                        cluster_size = ?,
                        cluster_sources = ?,
                        scored_at_editorial = ?
                    WHERE id = ?
                """, (
                    s.editorial_score,
                    json.dumps(s.reasons, ensure_ascii=False),
                    s.cluster_id,
                    s.cluster_size,
                    json.dumps(s.cluster_sources, ensure_ascii=False),
                    s.scored_at,
                    s.article_id,
                ))
                updated += 1

            conn.commit()
            conn.close()
            logger.info(f"Saved editorial scores for {updated} articles")
            return updated

        except Exception as e:
            logger.error(f"Error saving scores: {e}")
            return 0

    # ─── Helpers ──────────────────────────────────────────────────────

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00").replace("+00:00", ""))
        except Exception:
            try:
                return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None


# ═══════════════════════════════════════════════════════════════════════════
# Convenience functions
# ═══════════════════════════════════════════════════════════════════════════

def run_editorial_scoring(
    get_db_conn=None,
    top_k: int = TOP_K_EDITORIAL,
    days_back: int = 3
) -> List[Dict]:
    """
    Entry point: score articles and save to DB.

    Returns list of top-K scored article dicts.
    """
    scorer = EditorialScorer(get_db_conn=get_db_conn)
    results = scorer.score_and_rank(top_k=top_k, days_back=days_back)
    scorer.save_scores(results)
    return [r.to_dict() for r in results]
