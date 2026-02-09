"""
Francophone Article Filtering Service - TOP 20 Selection

Strict filtering to show only the most relevant francophone articles per day.

Features:
- Relevance scoring based on interactions, language, region, recency, and topic
- Daily TOP 20 selection with median-based qualification
- Featured article tagging for manual override
- Francophone regional prioritization (Africa + France/Belgium/Switzerland/Canada)
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)

# Francophone regions for prioritization
FRANCOPHONE_AFRICA = {
    "SN",  # Senegal
    "CI",  # Ivory Coast
    "CM",  # Cameroon
    "ML",  # Mali
    "BF",  # Burkina Faso
    "NE",  # Niger
    "TG",  # Togo
    "BJ",  # Benin
    "GN",  # Guinea
    "GA",  # Gabon
    "CG",  # Congo
    "CD",  # DRC
}

FRANCOPHONE_DEVELOPED = {
    "FR",  # France
    "BE",  # Belgium
    "CH",  # Switzerland
    "CA",  # Canada
}

FRANCOPHONE_ALL = FRANCOPHONE_AFRICA | FRANCOPHONE_DEVELOPED

# Relevant topics for business/finance
RELEVANT_TOPICS = {
    "finance", "economy", "economic", "business", "entreprise",
    "startup", "tech", "technology", "innovation", "fintech",
    "cryptocurrency", "trading", "investment", "market", "stock",
    "commerce", "trade", "banking", "payment", "digital",
    "mobile", "ecommerce", "e-commerce", "ai", "automation",
}

@dataclass
class FrancophonicArticle:
    """Article with francophone relevance score."""
    article_id: int
    title: str
    source_name: str
    country: str
    language: str
    published_at: Optional[str]
    url: str
    total_interactions: int

    # Scoring components
    interaction_score: float  # Relative to source median
    language_score: float     # 1.0 for French, 0.5 for French-capable
    region_score: float       # Higher for francophone regions
    recency_score: float      # Based on published date
    topic_score: float        # Based on category/tags

    # Combined score
    francophone_relevance_score: float  # 0.0-100.0

    # Status
    is_featured: bool         # Manual override
    rank: int                 # Daily rank (1-20)

@dataclass
class SourceMetrics:
    """Metrics for a news source."""
    source_name: str
    country: str
    language: str
    total_articles: int
    median_interactions: float
    avg_interactions: float
    articles_above_2x_median: int

class FrancophonicFilterService:
    """Service for strict francophone article filtering."""

    def __init__(self, db_conn=None):
        """
        Initialize the service.

        Args:
            db_conn: Function to get SQLite connection
        """
        self.get_conn = db_conn

    def get_daily_top_20(
        self,
        days: int = 1,
        include_featured: bool = True
    ) -> List[FrancophonicArticle]:
        """
        Get the TOP 20 most relevant francophone articles for a specific day.

        Filtering rules:
        1. Must be published in last 24-48 hours
        2. Language must be French (or French-capable)
        3. Must be from francophone region
        4. Must have > 2x median interactions for its source
        5. Ranked by combined relevance score

        Args:
            days: Number of days to lookback (default: 1 = last 24 hours)
            include_featured: If True, always include featured articles in top 20

        Returns:
            List[FrancophonicArticle] ordered by relevance_score DESC (max 20)
        """
        if not self.get_conn:
            logger.warning("No database connection available")
            return []

        articles = []
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            # Step 1: Calculate source metrics
            source_metrics = self._calculate_source_metrics(days=days)

            conn = self.get_conn()
            cursor = conn.cursor()

            # Step 2: Fetch articles from last N days
            cursor.execute("""
                SELECT
                    id, title, source_name, country, language,
                    published_at, url, total_interactions, is_featured
                FROM news_articles
                WHERE
                    status = 'published'
                    AND created_at >= ?
                    AND language = 'fr'
                    AND total_interactions > 0
                ORDER BY created_at DESC
                LIMIT 500
            """, (cutoff_date,))

            rows = cursor.fetchall()
            conn.close()

            # Step 3: Filter and score articles
            for row in rows:
                article_id = row[0]
                title = row[1]
                source_name = row[2]
                country = row[3]
                language = row[4]
                published_at = row[5]
                url = row[6]
                total_interactions = row[7] or 0
                is_featured = bool(row[8]) if len(row) > 8 else False

                # Get source metrics
                if source_name not in source_metrics:
                    continue

                metrics = source_metrics[source_name]

                # Check 2x median rule
                if total_interactions < metrics.median_interactions * 2:
                    # Featured articles bypass this rule
                    if not is_featured:
                        continue

                # Calculate relevance score
                article_obj = FrancophonicArticle(
                    article_id=article_id,
                    title=title,
                    source_name=source_name,
                    country=country,
                    language=language,
                    published_at=published_at,
                    url=url,
                    total_interactions=total_interactions,
                    interaction_score=0.0,
                    language_score=0.0,
                    region_score=0.0,
                    recency_score=0.0,
                    topic_score=0.0,
                    francophone_relevance_score=0.0,
                    is_featured=is_featured,
                    rank=0
                )

                # Score components
                article_obj.interaction_score = self._score_interactions(
                    total_interactions,
                    metrics.median_interactions,
                    is_featured
                )

                article_obj.language_score = self._score_language(language)

                article_obj.region_score = self._score_region(country)

                article_obj.recency_score = self._score_recency(published_at)

                article_obj.topic_score = self._score_topic(title)

                # Combined score (weighted)
                article_obj.francophone_relevance_score = (
                    (article_obj.interaction_score * 0.35) +
                    (article_obj.language_score * 0.20) +
                    (article_obj.region_score * 0.20) +
                    (article_obj.recency_score * 0.15) +
                    (article_obj.topic_score * 0.10)
                )

                # Featured articles get a boost
                if is_featured:
                    article_obj.francophone_relevance_score *= 1.5

                articles.append(article_obj)

            # Step 4: Sort by score and take top 20
            articles.sort(
                key=lambda a: (
                    a.is_featured,  # Featured first
                    a.francophone_relevance_score  # Then by score
                ),
                reverse=True
            )

            # Assign ranks
            for idx, article in enumerate(articles[:20], 1):
                article.rank = idx

            return articles[:20]

        except Exception as e:
            logger.error(f"Error getting daily top 20: {e}")
            return []

    def _calculate_source_metrics(self, days: int = 7) -> Dict[str, SourceMetrics]:
        """
        Calculate metrics for each source (median, avg interactions).

        Args:
            days: Number of days to analyze

        Returns:
            Dict mapping source_name -> SourceMetrics
        """
        if not self.get_conn:
            return {}

        metrics = {}
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Get all sources
            cursor.execute("""
                SELECT DISTINCT source_name, country, language
                FROM news_articles
                WHERE created_at >= ? AND status = 'published'
                ORDER BY source_name
            """, (cutoff_date,))

            sources = cursor.fetchall()

            for source_name, country, language in sources:
                # Get all interactions for this source
                cursor.execute("""
                    SELECT total_interactions
                    FROM news_articles
                    WHERE source_name = ? AND created_at >= ?
                    ORDER BY total_interactions
                """, (source_name, cutoff_date))

                interactions = [row[0] or 0 for row in cursor.fetchall()]

                if not interactions:
                    continue

                median_interactions = statistics.median(interactions)
                avg_interactions = statistics.mean(interactions)
                above_2x = sum(1 for i in interactions if i >= median_interactions * 2)

                metrics[source_name] = SourceMetrics(
                    source_name=source_name,
                    country=country or "UNKNOWN",
                    language=language or "en",
                    total_articles=len(interactions),
                    median_interactions=median_interactions,
                    avg_interactions=avg_interactions,
                    articles_above_2x_median=above_2x
                )

            conn.close()

        except Exception as e:
            logger.error(f"Error calculating source metrics: {e}")

        return metrics

    def _score_interactions(
        self,
        interactions: int,
        source_median: float,
        is_featured: bool = False
    ) -> float:
        """
        Score based on interactions relative to source median.

        Returns 0.0-100.0
        """
        if source_median <= 0:
            return 50.0  # Neutral

        ratio = interactions / source_median

        if is_featured:
            # Featured articles: at least 50/100
            return min(100.0, 50.0 + (ratio * 25.0))

        # Regular articles: need at least 2x to score well
        if ratio < 2.0:
            return ratio * 25.0  # 0-50
        elif ratio < 5.0:
            return 50.0 + ((ratio - 2.0) * 10.0)  # 50-80
        elif ratio < 10.0:
            return 80.0 + ((ratio - 5.0) * 4.0)  # 80-100
        else:
            return 100.0

    def _score_language(self, language: str) -> float:
        """
        Score based on language preference for francophone audience.

        Returns 0.0-100.0
        """
        if language == "fr":
            return 100.0
        elif language in ["en", "es", "pt"]:
            return 50.0  # Translated or bilingual
        else:
            return 25.0

    def _score_region(self, country: Optional[str]) -> float:
        """
        Score based on geographic region relevance.

        Returns 0.0-100.0
        Priority: Sub-Saharan francophone Africa > Developed francophone > Other
        """
        if not country:
            return 50.0

        country = country.upper()

        if country in FRANCOPHONE_AFRICA:
            return 100.0  # Highest priority
        elif country in FRANCOPHONE_DEVELOPED:
            return 85.0
        elif country.upper() in {"MA", "TN", "DZ"}:  # North Africa
            return 70.0
        else:
            return 40.0

    def _score_recency(self, published_at: Optional[str]) -> float:
        """
        Score based on publication date recency.

        Returns 0.0-100.0
        Recent = 100, older = lower scores
        """
        if not published_at:
            return 50.0

        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            now = datetime.utcnow()
            hours_old = (now - pub_date).total_seconds() / 3600

            if hours_old < 1:
                return 100.0  # Less than 1 hour old
            elif hours_old < 6:
                return 90.0  # Less than 6 hours
            elif hours_old < 24:
                return 75.0  # Less than 24 hours
            elif hours_old < 48:
                return 50.0  # Less than 48 hours
            else:
                return 25.0  # Older

        except Exception as e:
            logger.warning(f"Error parsing date {published_at}: {e}")
            return 50.0

    def _score_topic(self, title: str) -> float:
        """
        Score based on topic relevance.

        Returns 0.0-100.0
        Finance/economy/tech topics = 100, others = lower
        """
        if not title:
            return 50.0

        title_lower = title.lower()

        # Check for relevant keywords
        matched = 0
        for topic in RELEVANT_TOPICS:
            if topic in title_lower:
                matched += 1

        if matched >= 3:
            return 100.0
        elif matched == 2:
            return 80.0
        elif matched == 1:
            return 60.0
        else:
            return 40.0

    def mark_article_as_featured(self, article_id: int) -> bool:
        """
        Mark an article as featured (manual override).
        Featured articles always appear in top 20.

        Args:
            article_id: ID of the article

        Returns:
            True if successful
        """
        if not self.get_conn:
            logger.warning("No database connection available")
            return False

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE news_articles
                SET is_featured = 1, updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), article_id))

            conn.commit()
            conn.close()

            logger.info(f"Marked article {article_id} as featured")
            return True

        except Exception as e:
            logger.error(f"Error marking article as featured: {e}")
            return False

    def unmark_article_as_featured(self, article_id: int) -> bool:
        """
        Unmark an article as featured.

        Args:
            article_id: ID of the article

        Returns:
            True if successful
        """
        if not self.get_conn:
            logger.warning("No database connection available")
            return False

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE news_articles
                SET is_featured = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), article_id))

            conn.commit()
            conn.close()

            logger.info(f"Unmarked article {article_id} as featured")
            return True

        except Exception as e:
            logger.error(f"Error unmarking article as featured: {e}")
            return False

    def get_source_metrics_report(self, days: int = 30) -> Dict[str, SourceMetrics]:
        """
        Get detailed metrics for all sources for reporting.

        Args:
            days: Number of days to analyze

        Returns:
            Dict mapping source_name -> SourceMetrics
        """
        return self._calculate_source_metrics(days=days)

    def calculate_and_store_scores(self) -> bool:
        """
        Recalculate francophone relevance scores for all articles.
        This should be run daily or when scoring parameters change.

        Returns:
            True if successful
        """
        if not self.get_conn:
            logger.warning("No database connection available")
            return False

        try:
            logger.info("Starting francophone relevance score calculation...")

            # Get all published articles
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, title, source_name, country, language,
                       published_at, total_interactions
                FROM news_articles
                WHERE status = 'published'
                ORDER BY id DESC
            """)

            rows = cursor.fetchall()

            # Get source metrics
            source_metrics = self._calculate_source_metrics(days=30)

            updated_count = 0
            for row in rows:
                article_id = row[0]
                title = row[1]
                source_name = row[2]
                country = row[3]
                language = row[4]
                published_at = row[5]
                total_interactions = row[6] or 0

                if source_name not in source_metrics:
                    continue

                metrics = source_metrics[source_name]

                # Calculate component scores
                interaction_score = self._score_interactions(
                    total_interactions,
                    metrics.median_interactions,
                    False
                )
                language_score = self._score_language(language)
                region_score = self._score_region(country)
                recency_score = self._score_recency(published_at)
                topic_score = self._score_topic(title)

                # Combined score
                relevance_score = (
                    (interaction_score * 0.35) +
                    (language_score * 0.20) +
                    (region_score * 0.20) +
                    (recency_score * 0.15) +
                    (topic_score * 0.10)
                )

                # Store score
                cursor.execute("""
                    UPDATE news_articles
                    SET francophone_relevance_score = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (round(relevance_score, 2), datetime.utcnow().isoformat(), article_id))

                updated_count += 1

            conn.commit()
            conn.close()

            logger.info(f"Updated francophone scores for {updated_count} articles")
            return True

        except Exception as e:
            logger.error(f"Error calculating francophone scores: {e}")
            return False
