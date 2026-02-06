"""
Viral Scorer V2 — Algorithme de sélection d'articles pertinents/viraux.

Feature flag: ENABLE_VIRAL_FILTER_V2=true

Ce module:
1. Score chaque article sur 0-100 via une formule pondérée
2. Produit des "reasons" explicables pour chaque article retenu
3. Dédoublonne par titre normalisé + URL canonique
4. Limite le top-K par jour (configurable)
5. Applique la règle "early trend ≥ 1h"

Pondérations par défaut (configurables via env):
  social_score:       35%  (ou redistribué si indisponible)
  early_trend_score:  20%  (règle 1h — baseline comparison)
  controversy_score:  15%  (mots-clés polémiques)
  impact_score:       15%  (impact éco/géopolitique)
  geo_relevance:      10%  (pertinence géographique audience)
  headline_power:      5%  (qualité titre)

Auteur: MarketGPS
Date: Février 2026
"""

import os
import re
import json
import math
import hashlib
import logging
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Configuration (all overridable via env)
# ═══════════════════════════════════════════════════════════════════════════

ENABLE_VIRAL_FILTER_V2 = os.environ.get("ENABLE_VIRAL_FILTER_V2", "true").lower() == "true"

# Weights (must sum to 1.0)
W_SOCIAL = float(os.environ.get("V2_W_SOCIAL", "0.35"))
W_EARLY_TREND = float(os.environ.get("V2_W_EARLY_TREND", "0.20"))
W_CONTROVERSY = float(os.environ.get("V2_W_CONTROVERSY", "0.15"))
W_IMPACT = float(os.environ.get("V2_W_IMPACT", "0.15"))
W_GEO = float(os.environ.get("V2_W_GEO", "0.10"))
W_HEADLINE = float(os.environ.get("V2_W_HEADLINE", "0.05"))

# When social data is unavailable, redistribute weights
W_NOSOCIAL_ATTENTION = float(os.environ.get("V2_W_NOSOCIAL_ATTENTION", "0.20"))
W_NOSOCIAL_CONTROVERSY = float(os.environ.get("V2_W_NOSOCIAL_CONTROVERSY", "0.25"))
W_NOSOCIAL_IMPACT = float(os.environ.get("V2_W_NOSOCIAL_IMPACT", "0.25"))
W_NOSOCIAL_EARLY = float(os.environ.get("V2_W_NOSOCIAL_EARLY", "0.15"))
W_NOSOCIAL_GEO = float(os.environ.get("V2_W_NOSOCIAL_GEO", "0.10"))
W_NOSOCIAL_HEADLINE = float(os.environ.get("V2_W_NOSOCIAL_HEADLINE", "0.05"))

# Top-K config
TOP_K_PER_DAY = int(os.environ.get("V2_TOP_K", "40"))
MIN_SCORE_TO_KEEP = float(os.environ.get("V2_MIN_SCORE", "25"))
MAX_PER_CLUSTER = int(os.environ.get("V2_MAX_PER_CLUSTER", "4"))

# Target audience countries
TARGET_COUNTRIES = {
    "FR", "CI", "CM", "SN", "BJ", "ML", "BF",  # Francophone
    "DE", "US", "CA", "BE",                       # Diaspora
}

# Francophone sub-Saharan (priority)
FRANCOPHONE_SSA = {"CI", "SN", "CM", "BF", "ML", "TG", "BJ", "GA", "CG", "CD", "NE", "GN", "TD"}

# ═══════════════════════════════════════════════════════════════════════════
# Keyword dictionaries
# ═══════════════════════════════════════════════════════════════════════════

CONTROVERSY_KEYWORDS = {
    # French
    "scandale", "corruption", "fraude", "détournement", "polémique", "accusé",
    "manifestation", "grève", "crise", "colère", "dénonce", "révélation",
    "affaire", "litige", "condamné", "interpellé", "procès", "enquête",
    "violence", "tensions", "conflit", "contestation", "protestation",
    "opposition", "rebelle", "putsch", "coup d'état", "sanctions",
    "controversé", "illégal", "arnaque", "escroquerie", "faillite",
    # English
    "scandal", "corruption", "fraud", "crisis", "protest", "clash",
    "controversy", "accused", "investigation", "arrest", "lawsuit",
    "coup", "rebellion", "sanctions", "crackdown",
}

IMPACT_KEYWORDS = {
    # Economique
    "milliard", "billion", "million", "investissement", "croissance", "pib",
    "inflation", "recession", "dette", "budget", "réforme", "privatisation",
    "bceao", "cemac", "bourse", "brvm", "nasdaq", "ipo", "startup",
    "fintech", "mobile money", "orange money", "mtn", "wave",
    "fcfa", "franc cfa", "zlecaf", "zone de libre-échange",
    # Géopolitique
    "sommet", "accord", "traité", "diplomatie", "onu", "ua", "cedeao",
    "union africaine", "france-afrique", "chine-afrique", "brics",
    "indépendance", "souveraineté", "élection", "référendum",
    "président", "premier ministre", "parlement",
    # English
    "billion", "investment", "growth", "gdp", "reform", "summit",
    "trade deal", "election", "president", "sovereignty",
}

HEADLINE_POWER_PATTERNS = [
    (r"\d+\s*(milliards?|billions?|millions?|%)", 15),  # Chiffres clés
    (r"(?:exclu|breaking|urgent|alerte)", 12),           # Breaking
    (r"(?:première|historique|record|inédit)", 10),       # Historique
    (r"(?:pourquoi|comment|qui est)", 8),                 # Question hooks
    (r"(?:révèle|dévoile|expose|découvre)", 8),           # Révélation
    (r"(?:chute|effondrement|explosion|boom)", 7),        # Dramatic
]


# ═══════════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ScoredArticle:
    """Résultat du scoring V2 pour un article."""
    article_id: int
    viral_score_v2: float           # 0-100
    reasons: List[str]              # Top 5 raisons
    component_scores: Dict[str, float]  # Détail par composant
    cluster_id: Optional[str] = None
    cluster_label: Optional[str] = None
    trend_velocity_ratio: Optional[float] = None
    attention_proxy_score: Optional[float] = None
    social_engagement_total: Optional[int] = None
    has_social_data: bool = False
    scored_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════
# Core Scorer
# ═══════════════════════════════════════════════════════════════════════════

class ViralScorerV2:
    """
    Scorer V2 — calcule un score de viralité 0-100 pour chaque article.

    Utilisation:
        scorer = ViralScorerV2(db_conn_fn)
        results = scorer.score_and_rank(limit=40)
    """

    def __init__(self, get_db_conn=None):
        self.get_conn = get_db_conn
        self._baselines_cache: Dict[str, Dict] = {}
        self._baselines_loaded_at: Optional[datetime] = None

    # ─── Public API ───────────────────────────────────────────────────

    def score_and_rank(
        self,
        articles: Optional[List[Dict]] = None,
        top_k: int = TOP_K_PER_DAY,
        min_score: float = MIN_SCORE_TO_KEEP,
        max_per_cluster: int = MAX_PER_CLUSTER,
        days_back: int = 3,
    ) -> List[ScoredArticle]:
        """
        Score, deduplicate, cluster, and rank articles.

        If articles is None, loads from DB (last `days_back` days).
        Returns top-K scored articles sorted by viral_score_v2 DESC.
        """
        if not ENABLE_VIRAL_FILTER_V2:
            logger.info("Viral Filter V2 disabled (ENABLE_VIRAL_FILTER_V2=false)")
            return []

        # 1. Load articles if not provided
        if articles is None:
            articles = self._load_recent_articles(days_back)

        if not articles:
            logger.info("No articles to score")
            return []

        logger.info(f"Scoring {len(articles)} articles with V2...")

        # 2. Load baselines for early trend detection
        self._load_baselines()

        # 3. Score each article
        scored = []
        for article in articles:
            try:
                result = self._score_article(article)
                scored.append(result)
            except Exception as e:
                logger.error(f"Error scoring article {article.get('id')}: {e}")

        # 4. Dedup by normalized title
        deduped = self._deduplicate(scored, articles)

        # 5. Cluster similar articles
        clustered = self._cluster_articles(deduped, articles)

        # 6. Apply diversity limit per cluster
        diverse = self._apply_diversity(clustered, max_per_cluster)

        # 7. Filter by min score
        filtered = [s for s in diverse if s.viral_score_v2 >= min_score]

        # 8. Sort and take top-K
        filtered.sort(key=lambda s: s.viral_score_v2, reverse=True)
        top = filtered[:top_k]

        logger.info(
            f"V2 scoring: {len(articles)} articles → "
            f"{len(deduped)} deduped → "
            f"{len(diverse)} diverse → "
            f"{len(filtered)} above min_score → "
            f"{len(top)} top-K returned"
        )

        return top

    def score_single(self, article: Dict) -> ScoredArticle:
        """Score a single article (for real-time use)."""
        self._load_baselines()
        return self._score_article(article)

    # ─── Scoring Logic ────────────────────────────────────────────────

    def _score_article(self, article: Dict) -> ScoredArticle:
        """Compute viral_score_v2 for one article."""
        now = datetime.utcnow()
        scored_at = now.isoformat()

        # Determine if we have real social data
        interactions_source = article.get("interactions_source", "estimated")
        total_interactions = article.get("total_interactions", 0) or 0
        has_social = (
            interactions_source in ("scraped", "facebook", "google")
            and total_interactions > 0
        )

        # Component scores (each 0-100)
        social = self._calc_social_score(article) if has_social else 0
        early_trend = self._calc_early_trend_score(article, now)
        controversy = self._calc_controversy_score(article)
        impact = self._calc_impact_score(article)
        geo = self._calc_geo_relevance(article)
        headline = self._calc_headline_power(article)
        attention_proxy = self._calc_attention_proxy(article) if not has_social else 0

        # Weighted sum
        if has_social:
            final = (
                social * W_SOCIAL +
                early_trend * W_EARLY_TREND +
                controversy * W_CONTROVERSY +
                impact * W_IMPACT +
                geo * W_GEO +
                headline * W_HEADLINE
            )
        else:
            # Redistribute social weight
            final = (
                attention_proxy * W_NOSOCIAL_ATTENTION +
                controversy * W_NOSOCIAL_CONTROVERSY +
                impact * W_NOSOCIAL_IMPACT +
                early_trend * W_NOSOCIAL_EARLY +
                geo * W_NOSOCIAL_GEO +
                headline * W_NOSOCIAL_HEADLINE
            )

        # Clamp 0-100
        final = max(0, min(100, final))

        # Build reasons
        components = {
            "social": social,
            "early_trend": early_trend,
            "controversy": controversy,
            "impact": impact,
            "geo_relevance": geo,
            "headline_power": headline,
            "attention_proxy": attention_proxy,
        }
        reasons = self._build_reasons(components, article, has_social)

        # Trend velocity for the article
        trend_velocity = self._get_trend_velocity(article, now)

        return ScoredArticle(
            article_id=article.get("id", 0),
            viral_score_v2=round(final, 1),
            reasons=reasons[:5],
            component_scores={k: round(v, 1) for k, v in components.items()},
            trend_velocity_ratio=trend_velocity,
            attention_proxy_score=round(attention_proxy, 1) if not has_social else None,
            social_engagement_total=total_interactions if has_social else None,
            has_social_data=has_social,
            scored_at=scored_at,
        )

    # ─── Component Calculators ────────────────────────────────────────

    def _calc_social_score(self, article: Dict) -> float:
        """Score based on real social engagement (0-100)."""
        total = article.get("total_interactions", 0) or 0
        source_name = (article.get("source_name") or "").lower().strip()

        # Get source baseline
        from pipeline.news.interactions_fetcher import SOURCE_BASELINE
        baseline = SOURCE_BASELINE.get(source_name, SOURCE_BASELINE.get("default", 150))

        ratio = total / max(baseline, 1)

        # Map ratio to 0-100 score
        if ratio >= 5.0:
            return 100
        elif ratio >= 3.0:
            return 80 + (ratio - 3.0) / 2.0 * 20
        elif ratio >= 2.0:
            return 60 + (ratio - 2.0) * 20
        elif ratio >= 1.0:
            return 40 + (ratio - 1.0) * 20
        elif ratio >= 0.5:
            return 20 + (ratio - 0.5) / 0.5 * 20
        else:
            return ratio / 0.5 * 20

    def _calc_early_trend_score(self, article: Dict, now: datetime) -> float:
        """
        Règle spéciale "≥ 1h" :
        Comparer engagement actuel à la baseline "à âge comparable".
        """
        published_at = self._parse_date(article.get("published_at"))
        if not published_at:
            return 30  # Default if no date

        age_minutes = (now - published_at).total_seconds() / 60

        # Only apply early trend rule for articles ≥ 60 minutes old
        if age_minutes < 60:
            # Very fresh article — give moderate boost
            return 50

        # Get the hour bucket for baseline comparison
        hour_bucket = self._get_hour_bucket(age_minutes)
        source_name = (article.get("source_name") or "default").lower().strip()

        baseline = self._get_baseline(source_name, hour_bucket)
        if baseline is None or baseline <= 0:
            return 30  # No baseline data

        # Current metric (use total_interactions, or attention_proxy)
        current = article.get("total_interactions", 0) or 0
        if current == 0:
            # Try attention proxy (engagement_score * 100)
            current = (article.get("engagement_score", 0) or 0) * 100

        velocity = current / baseline if baseline > 0 else 0

        # Apply bonus scoring
        score = 30  # base
        if velocity >= 3.0:
            score = 90 + min(10, (velocity - 3.0) * 5)  # 90-100
        elif velocity >= 2.0:
            score = 70 + (velocity - 2.0) * 20  # 70-90
        elif velocity >= 1.2:
            score = 50 + (velocity - 1.2) / 0.8 * 20  # 50-70
        elif velocity >= 0.8:
            score = 30 + (velocity - 0.8) / 0.4 * 20  # 30-50
        else:
            score = velocity / 0.8 * 30  # 0-30

        return min(100, max(0, score))

    def _calc_controversy_score(self, article: Dict) -> float:
        """Score based on controversy/debate potential (0-100)."""
        title = (article.get("title") or "").lower()
        content = (article.get("content_md") or article.get("excerpt") or "").lower()
        text = title + " " + content[:500]

        matches = sum(1 for kw in CONTROVERSY_KEYWORDS if kw in text)

        # Title matches count double
        title_matches = sum(1 for kw in CONTROVERSY_KEYWORDS if kw in title)
        matches += title_matches  # Double count for title

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

    def _calc_impact_score(self, article: Dict) -> float:
        """Score based on economic/geopolitical impact (0-100)."""
        title = (article.get("title") or "").lower()
        content = (article.get("content_md") or article.get("excerpt") or "").lower()
        text = title + " " + content[:500]

        matches = sum(1 for kw in IMPACT_KEYWORDS if kw in text)
        title_matches = sum(1 for kw in IMPACT_KEYWORDS if kw in title)
        matches += title_matches

        # Check for big numbers in title (milliards, billions)
        big_number_boost = 0
        if re.search(r"\d+\s*milliards?", title) or re.search(r"\d+\s*billions?", title):
            big_number_boost = 20
        elif re.search(r"\d+\s*millions?", title):
            big_number_boost = 10

        base_score = min(80, matches * 12)
        return min(100, base_score + big_number_boost)

    def _calc_geo_relevance(self, article: Dict) -> float:
        """Score based on geographic relevance to target audience (0-100)."""
        country = (article.get("country") or "").upper()
        language = (article.get("language") or "").lower()
        source_name = (article.get("source_name") or "").lower()

        score = 0

        # Country match
        if country in FRANCOPHONE_SSA:
            score += 70  # Primary audience
        elif country in TARGET_COUNTRIES:
            score += 50
        elif country in {"NG", "GH", "KE", "ZA", "TZ", "RW", "ET"}:
            score += 30  # Major African economies
        else:
            score += 10

        # Language bonus
        if language == "fr":
            score += 20
        elif language == "en":
            score += 10

        # Pan-African source bonus
        pan_sources = ["jeune afrique", "agence ecofin", "the africa report", "african business"]
        if any(s in source_name for s in pan_sources):
            score += 10

        return min(100, score)

    def _calc_headline_power(self, article: Dict) -> float:
        """Score based on headline quality (0-100)."""
        title = article.get("title") or ""

        score = 0
        for pattern, points in HEADLINE_POWER_PATTERNS:
            if re.search(pattern, title, re.IGNORECASE):
                score += points

        # Length penalty (too short or too long)
        tlen = len(title)
        if tlen < 30:
            score -= 10
        elif tlen > 120:
            score -= 5

        # Has numbers (engaging)
        if re.search(r"\d+", title):
            score += 5

        return max(0, min(100, score))

    def _calc_attention_proxy(self, article: Dict) -> float:
        """
        Proxy d'attention quand les données sociales sont absentes.
        Combine: engagement_score existant + signaux indirects.
        """
        # Use the existing engagement_score (0-1) from scoring.py
        eng_score = article.get("engagement_score", 0) or 0

        # Importance level bonus
        importance = article.get("importance_level", "normal")
        importance_bonus = {
            "breaking": 30,
            "high": 20,
            "normal": 5,
            "low": 0,
        }.get(importance, 5)

        # Is breaking news bonus
        is_breaking = article.get("is_breaking_news", 0)
        breaking_bonus = 15 if is_breaking else 0

        # Source trust
        source_name = (article.get("source_name") or "").lower()
        high_trust = ["jeune afrique", "agence ecofin", "financial afrik", "the africa report"]
        trust_bonus = 10 if any(s in source_name for s in high_trust) else 0

        # Combine
        proxy = (eng_score * 50) + importance_bonus + breaking_bonus + trust_bonus
        return min(100, max(0, proxy))

    # ─── Early Trend Baselines ────────────────────────────────────────

    def _load_baselines(self):
        """Load engagement baselines per source + hour bucket."""
        if self._baselines_loaded_at and (datetime.utcnow() - self._baselines_loaded_at).seconds < 3600:
            return  # Cache for 1 hour

        if not self.get_conn:
            return

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Calculate baselines from last 30 days of articles
            cursor.execute("""
                SELECT source_name,
                       CASE
                           WHEN (julianday('now') - julianday(published_at)) * 24 < 1 THEN '0h'
                           WHEN (julianday('now') - julianday(published_at)) * 24 < 3 THEN '1h'
                           WHEN (julianday('now') - julianday(published_at)) * 24 < 6 THEN '3h'
                           WHEN (julianday('now') - julianday(published_at)) * 24 < 12 THEN '6h'
                           WHEN (julianday('now') - julianday(published_at)) * 24 < 24 THEN '12h'
                           ELSE '24h'
                       END as hour_bucket,
                       AVG(total_interactions) as avg_interactions,
                       COUNT(*) as sample_size
                FROM news_articles
                WHERE published_at >= datetime('now', '-30 days')
                  AND total_interactions > 0
                GROUP BY source_name, hour_bucket
            """)

            self._baselines_cache = {}
            for row in cursor.fetchall():
                source, bucket, avg_val, sample = row
                key = f"{(source or 'default').lower().strip()}_{bucket}"
                self._baselines_cache[key] = {
                    "avg": avg_val or 0,
                    "sample_size": sample or 0,
                }

            conn.close()
            self._baselines_loaded_at = datetime.utcnow()
            logger.debug(f"Loaded {len(self._baselines_cache)} baseline entries")

        except Exception as e:
            logger.error(f"Error loading baselines: {e}")

    def _get_baseline(self, source_name: str, hour_bucket: str) -> Optional[float]:
        """Get baseline for source at given age bucket."""
        key = f"{source_name}_{hour_bucket}"
        entry = self._baselines_cache.get(key)
        if entry and entry["sample_size"] >= 5:
            return entry["avg"]

        # Fallback to "default" source
        key = f"default_{hour_bucket}"
        entry = self._baselines_cache.get(key)
        if entry and entry["sample_size"] >= 5:
            return entry["avg"]

        return None

    def _get_hour_bucket(self, age_minutes: float) -> str:
        """Map article age to hour bucket."""
        hours = age_minutes / 60
        if hours < 1:
            return "0h"
        elif hours < 3:
            return "1h"
        elif hours < 6:
            return "3h"
        elif hours < 12:
            return "6h"
        elif hours < 24:
            return "12h"
        return "24h"

    def _get_trend_velocity(self, article: Dict, now: datetime) -> Optional[float]:
        """Calculate trend velocity ratio for an article."""
        published_at = self._parse_date(article.get("published_at"))
        if not published_at:
            return None

        age_minutes = (now - published_at).total_seconds() / 60
        if age_minutes < 60:
            return None

        hour_bucket = self._get_hour_bucket(age_minutes)
        source_name = (article.get("source_name") or "default").lower().strip()
        baseline = self._get_baseline(source_name, hour_bucket)

        if not baseline or baseline <= 0:
            return None

        current = article.get("total_interactions", 0) or 0
        return round(current / baseline, 2)

    # ─── Deduplication ────────────────────────────────────────────────

    def _deduplicate(self, scored: List[ScoredArticle], articles: List[Dict]) -> List[ScoredArticle]:
        """Remove duplicate articles by normalized title + canonical URL."""
        articles_by_id = {a.get("id"): a for a in articles}
        seen_keys = {}
        result = []

        # Sort by score DESC so we keep the highest-scored version
        scored.sort(key=lambda s: s.viral_score_v2, reverse=True)

        for s in scored:
            article = articles_by_id.get(s.article_id, {})
            title = article.get("title") or ""
            url = article.get("canonical_url") or article.get("source_url") or ""

            # Normalize title
            norm_title = self._normalize_title(title)
            title_hash = hashlib.md5(norm_title.encode()).hexdigest()[:10]

            # Normalize URL
            url_key = re.sub(r"https?://", "", url).rstrip("/").lower()

            # Check both
            if title_hash in seen_keys:
                logger.debug(f"Dedup (title): '{title[:50]}' already seen")
                continue
            if url_key and url_key in seen_keys:
                logger.debug(f"Dedup (URL): '{url_key}' already seen")
                continue

            seen_keys[title_hash] = s.article_id
            if url_key:
                seen_keys[url_key] = s.article_id
            result.append(s)

        removed = len(scored) - len(result)
        if removed > 0:
            logger.info(f"Dedup removed {removed} duplicate articles")

        return result

    def _normalize_title(self, title: str) -> str:
        """Normalize title for dedup comparison."""
        # Lowercase, remove accents, remove punctuation, collapse spaces
        t = title.lower().strip()
        t = unicodedata.normalize("NFD", t)
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        t = re.sub(r"[^\w\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        # Remove common prefixes
        for prefix in ["breaking ", "urgent ", "alerte ", "exclu "]:
            if t.startswith(prefix):
                t = t[len(prefix):]
        return t

    # ─── Clustering ───────────────────────────────────────────────────

    def _cluster_articles(self, scored: List[ScoredArticle], articles: List[Dict]) -> List[ScoredArticle]:
        """
        Lightweight clustering: group articles about the same subject.
        Uses keyword overlap in normalized titles.
        """
        articles_by_id = {a.get("id"): a for a in articles}
        clusters: Dict[str, List[ScoredArticle]] = defaultdict(list)

        for s in scored:
            article = articles_by_id.get(s.article_id, {})
            title = article.get("title") or ""
            norm = self._normalize_title(title)
            words = set(w for w in norm.split() if len(w) > 3)

            # Find existing cluster with high overlap
            assigned = False
            for cluster_key, cluster_items in clusters.items():
                cluster_article = articles_by_id.get(cluster_items[0].article_id, {})
                cluster_title = self._normalize_title(cluster_article.get("title") or "")
                cluster_words = set(w for w in cluster_title.split() if len(w) > 3)

                if not words or not cluster_words:
                    continue

                overlap = len(words & cluster_words) / max(len(words | cluster_words), 1)
                if overlap >= 0.5:  # 50% word overlap = same cluster
                    s.cluster_id = cluster_key
                    s.cluster_label = cluster_key[:60]
                    cluster_items.append(s)
                    assigned = True
                    break

            if not assigned:
                # Create new cluster
                cluster_key = norm[:80]
                s.cluster_id = cluster_key
                s.cluster_label = (article.get("title") or "")[:60]
                clusters[cluster_key].append(s)

        return scored

    def _apply_diversity(self, scored: List[ScoredArticle], max_per_cluster: int) -> List[ScoredArticle]:
        """Limit articles per cluster for diversity."""
        cluster_counts: Dict[str, int] = defaultdict(int)
        result = []

        # Already sorted by score from dedup step
        scored.sort(key=lambda s: s.viral_score_v2, reverse=True)

        for s in scored:
            cid = s.cluster_id or f"unique_{s.article_id}"
            if cluster_counts[cid] < max_per_cluster:
                cluster_counts[cid] += 1
                result.append(s)

        removed = len(scored) - len(result)
        if removed > 0:
            logger.info(f"Diversity limit removed {removed} articles (max {max_per_cluster} per cluster)")

        return result

    # ─── Reason Builder ───────────────────────────────────────────────

    def _build_reasons(self, components: Dict[str, float], article: Dict, has_social: bool) -> List[str]:
        """Build human-readable reasons for the score."""
        reasons = []

        # Sort components by score
        sorted_comp = sorted(components.items(), key=lambda x: x[1], reverse=True)

        for comp_name, score in sorted_comp:
            if score <= 10:
                continue

            if comp_name == "social" and has_social:
                total = article.get("total_interactions", 0)
                reasons.append(f"Engagement social élevé ({total} interactions)")
            elif comp_name == "early_trend" and score >= 50:
                velocity = self._get_trend_velocity(article, datetime.utcnow())
                if velocity and velocity > 1.2:
                    reasons.append(f"Tendance précoce forte ({velocity}x la moyenne)")
                else:
                    reasons.append("Article récent avec potentiel de viralité")
            elif comp_name == "controversy" and score >= 30:
                reasons.append("Sujet polémique / fort potentiel de débat")
            elif comp_name == "impact" and score >= 30:
                reasons.append("Fort impact économique ou géopolitique")
            elif comp_name == "geo_relevance" and score >= 50:
                country = article.get("country") or "?"
                reasons.append(f"Pertinent pour l'audience cible ({country})")
            elif comp_name == "headline_power" and score >= 30:
                reasons.append("Titre accrocheur / forte capacité d'attention")
            elif comp_name == "attention_proxy" and not has_social and score >= 40:
                reasons.append("Score d'attention élevé (proxy)")

        if not reasons:
            reasons.append("Score général basé sur la combinaison des facteurs")

        return reasons[:5]

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

    def save_scores(self, scored_articles: List[ScoredArticle]) -> int:
        """Persist V2 scores to the database."""
        if not self.get_conn or not scored_articles:
            return 0

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Ensure columns exist (safe ALTER TABLE)
            for col, dtype, default in [
                ("viral_score_v2", "REAL", "0"),
                ("viral_reasons_v2", "TEXT", "NULL"),
                ("attention_proxy_score", "REAL", "NULL"),
                ("trend_velocity_ratio", "REAL", "NULL"),
                ("cluster_id", "TEXT", "NULL"),
                ("cluster_label", "TEXT", "NULL"),
                ("scored_at", "TEXT", "NULL"),
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
                    SET viral_score_v2 = ?,
                        viral_reasons_v2 = ?,
                        attention_proxy_score = ?,
                        trend_velocity_ratio = ?,
                        cluster_id = ?,
                        cluster_label = ?,
                        scored_at = ?
                    WHERE id = ?
                """, (
                    s.viral_score_v2,
                    json.dumps(s.reasons, ensure_ascii=False),
                    s.attention_proxy_score,
                    s.trend_velocity_ratio,
                    s.cluster_id,
                    s.cluster_label,
                    s.scored_at,
                    s.article_id,
                ))
                updated += 1

            conn.commit()
            conn.close()
            logger.info(f"Saved V2 scores for {updated} articles")
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

def run_v2_scoring(get_db_conn=None, top_k: int = TOP_K_PER_DAY, days_back: int = 3) -> List[Dict]:
    """
    Entry point: score articles and save to DB.

    Returns list of top-K scored article dicts.
    """
    scorer = ViralScorerV2(get_db_conn=get_db_conn)
    results = scorer.score_and_rank(top_k=top_k, days_back=days_back)
    scorer.save_scores(results)
    return [r.to_dict() for r in results]
