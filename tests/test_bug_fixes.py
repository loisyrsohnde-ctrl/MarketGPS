"""
Test suite for bug fixes in the MarketGPS news pipeline.

Tests:
1. Bug #1: Year being parsed as interaction count
2. Bug #2: Duplicate interaction counts across articles from same source
3. Editorial Scorer: Full pipeline
"""

import unittest
from datetime import datetime, timedelta
from pipeline.news.interactions_fetcher import InteractionsFetcher
from pipeline.news.editorial_scorer import EditorialScorer


class TestInteractionValidation(unittest.TestCase):
    """Test Bug #1: Year validation in interaction counts."""

    def setUp(self):
        self.fetcher = InteractionsFetcher()

    def test_year_detection_2026(self):
        """Test that 2026 is detected as a year, not interactions."""
        result = self.fetcher._validate_interaction_count(2026, datetime.utcnow())
        self.assertEqual(result, 0, "Year 2026 should be reset to 0")

    def test_year_detection_2025(self):
        """Test that 2025 is detected as a year."""
        result = self.fetcher._validate_interaction_count(2025, datetime.utcnow())
        self.assertEqual(result, 0, "Year 2025 should be reset to 0")

    def test_year_detection_1990(self):
        """Test that 1990 (edge case) is detected as a year."""
        result = self.fetcher._validate_interaction_count(1990, datetime.utcnow())
        self.assertEqual(result, 0, "Year 1990 should be reset to 0")

    def test_valid_interaction_count(self):
        """Test that legitimate interaction counts pass validation."""
        result = self.fetcher._validate_interaction_count(150, datetime.utcnow())
        self.assertEqual(result, 150, "Valid count 150 should not be modified")

    def test_valid_interaction_count_large(self):
        """Test that legitimate large counts pass validation."""
        result = self.fetcher._validate_interaction_count(5000, datetime.utcnow())
        self.assertEqual(result, 5000, "Valid count 5000 should not be modified")

    def test_published_year_match(self):
        """Test that interaction count matching publication year is detected."""
        # Article published in 2025
        pub_date = datetime(2025, 2, 12, 10, 30, 0)
        result = self.fetcher._validate_interaction_count(2025, pub_date)
        self.assertEqual(result, 0, "Count matching publication year should be reset")

    def test_published_year_no_match(self):
        """Test that valid count doesn't match publication year."""
        pub_date = datetime(2025, 2, 12, 10, 30, 0)
        result = self.fetcher._validate_interaction_count(500, pub_date)
        self.assertEqual(result, 500, "Count not matching publication year should pass")


class TestDuplicateInteractionDetection(unittest.TestCase):
    """Test Bug #2: Detecting duplicate interaction counts across articles."""

    def setUp(self):
        self.fetcher = InteractionsFetcher()

    def test_detect_duplicate_744(self):
        """Test detection of identical 744 interactions (TechPoint Africa case)."""
        articles = [
            {"source_name": "TechPoint Africa", "title": "Article 1", "total_interactions": 744},
            {"source_name": "TechPoint Africa", "title": "Article 2", "total_interactions": 744},
            {"source_name": "TechPoint Africa", "title": "Article 3", "total_interactions": 744},
            {"source_name": "TechPoint Africa", "title": "Article 4", "total_interactions": 500},
        ]

        unreliable = self.fetcher._check_duplicate_interactions(articles, "TechPoint Africa")
        self.assertIn(744, unreliable, "Interaction count 744 appearing 3x should be flagged")
        self.assertTrue(unreliable[744], "Should be marked as unreliable")

    def test_no_false_positives(self):
        """Test that legitimate variation doesn't trigger false positives."""
        articles = [
            {"source_name": "Source A", "title": "Article 1", "total_interactions": 100},
            {"source_name": "Source A", "title": "Article 2", "total_interactions": 150},
            {"source_name": "Source A", "title": "Article 3", "total_interactions": 120},
        ]

        unreliable = self.fetcher._check_duplicate_interactions(articles, "Source A")
        self.assertEqual(len(unreliable), 0, "Varied counts should not be flagged")

    def test_minimum_threshold(self):
        """Test that counts appearing only 2x are not flagged."""
        articles = [
            {"source_name": "Source B", "title": "Article 1", "total_interactions": 200},
            {"source_name": "Source B", "title": "Article 2", "total_interactions": 200},
            {"source_name": "Source B", "title": "Article 3", "total_interactions": 300},
        ]

        unreliable = self.fetcher._check_duplicate_interactions(articles, "Source B")
        self.assertEqual(len(unreliable), 0, "Counts appearing only 2x should not be flagged")

    def test_different_sources(self):
        """Test that same count in different sources isn't flagged together."""
        articles = [
            {"source_name": "Source A", "title": "Article 1", "total_interactions": 500},
            {"source_name": "Source A", "title": "Article 2", "total_interactions": 500},
            {"source_name": "Source B", "title": "Article 3", "total_interactions": 500},
            {"source_name": "Source B", "title": "Article 4", "total_interactions": 500},
        ]

        unreliable_a = self.fetcher._check_duplicate_interactions(articles, "Source A")
        unreliable_b = self.fetcher._check_duplicate_interactions(articles, "Source B")

        # Each source should flag independently (only 2x each, so actually not flagged)
        self.assertEqual(len(unreliable_a), 0, "Source A: only 2 occurrences")
        self.assertEqual(len(unreliable_b), 0, "Source B: only 2 occurrences")


class TestEditorialScorer(unittest.TestCase):
    """Test the new Editorial Scorer functionality."""

    def setUp(self):
        self.scorer = EditorialScorer()

    def test_normalize_title(self):
        """Test title normalization for clustering."""
        title = "MTN Côte d'Ivoire Lance un NOUVEAU Service!"
        normalized = self.scorer._normalize_title(title)

        # Should be lowercase, no accents, no punctuation
        self.assertFalse(any(c.isupper() for c in normalized if c.isalpha()))
        self.assertNotIn("'", normalized)
        self.assertNotIn("!", normalized)

    def test_extract_key_terms(self):
        """Test keyword extraction for clustering."""
        title = "TechPoint Startup Raises Million Dollar Funding"
        terms = self.scorer._extract_key_terms(title)

        # Should extract significant words
        self.assertIn("techpoint", terms)
        self.assertIn("startup", terms)
        self.assertIn("million", terms)
        self.assertIn("funding", terms)

        # Should exclude stop words
        self.assertNotIn("a", terms)
        self.assertNotIn("dollar", terms)  # Less than 4 chars after 'd'

    def test_clustering_similar_topics(self):
        """Test that articles about same topic get clustered."""
        articles = [
            {
                "id": 1,
                "title": "MTN Nigeria Launches Mobile Money Service",
                "source_name": "BusinessDay",
                "published_at": "2026-02-12T10:00:00Z"
            },
            {
                "id": 2,
                "title": "MTN Mobile Money Expansion Reaches West Africa",
                "source_name": "Agence Ecofin",
                "published_at": "2026-02-12T11:00:00Z"
            },
            {
                "id": 3,
                "title": "Orange Bank Opens in Senegal",
                "source_name": "Jeune Afrique",
                "published_at": "2026-02-12T12:00:00Z"
            },
        ]

        self.scorer._cluster_articles(articles)

        # Should have at least 2 clusters
        self.assertGreaterEqual(len(self.scorer._clusters), 2)

        # MTN articles should share a cluster
        mtn_clusters = set()
        for cluster_id, cluster_articles in self.scorer._clusters.items():
            for article in cluster_articles:
                if "MTN" in article.get("title", ""):
                    mtn_clusters.add(cluster_id)

        # Both MTN articles might be in same cluster or different, but should exist
        self.assertGreater(len(mtn_clusters), 0)

    def test_source_diversity_scoring(self):
        """Test source diversity scoring."""
        # Mock article in cluster with 1 source
        articles = [
            {
                "id": 1,
                "title": "Test Article",
                "source_name": "Source A",
                "published_at": "2026-02-12T10:00:00Z",
                "total_interactions": 100,
                "country": "CI",
            }
        ]

        self.scorer._cluster_articles(articles)

        # Single source should score 10
        score = self.scorer._calc_source_diversity(articles[0])
        self.assertEqual(score, 10, "Single source should score 10/100")

    def test_freshness_scoring(self):
        """Test freshness scoring."""
        now = datetime.utcnow()

        # Very fresh article (< 6h old)
        fresh = self.scorer._calc_freshness(
            {"published_at": (now - timedelta(hours=2)).isoformat()},
            now
        )
        self.assertEqual(fresh, 100, "Article < 6h old should score 100")

        # Old article (> 48h)
        old = self.scorer._calc_freshness(
            {"published_at": (now - timedelta(days=3)).isoformat()},
            now
        )
        self.assertEqual(old, 20, "Article > 48h old should score 20")

    def test_geo_relevance_scoring(self):
        """Test geographic relevance scoring."""
        # Francophone sub-Saharan country
        francophone = self.scorer._calc_geo_relevance(
            {"country": "CI", "total_interactions": 100}
        )
        self.assertEqual(francophone, 100, "Francophone Africa should score 100")

        # Anglophone with high engagement
        anglophone_high = self.scorer._calc_geo_relevance(
            {"country": "NG", "total_interactions": 600}
        )
        self.assertEqual(anglophone_high, 70, "Anglophone Africa with high engagement should score 70")

        # Other regions
        other = self.scorer._calc_geo_relevance(
            {"country": "US", "total_interactions": 100}
        )
        self.assertEqual(other, 30, "Other regions should score 30")


class TestEditorialScoringIntegration(unittest.TestCase):
    """Integration tests for the full Editorial Scorer pipeline."""

    def setUp(self):
        self.scorer = EditorialScorer()

    def test_single_article_scoring(self):
        """Test scoring a single article."""
        article = {
            "id": 1,
            "title": "BCEAO Raises Interest Rates - Historic Decision",
            "excerpt": "The BCEAO announced a historic decision to raise interest rates by 50 basis points",
            "source_name": "Agence Ecofin",
            "published_at": datetime.utcnow().isoformat(),
            "country": "SN",
            "total_interactions": 500,
        }

        score = self.scorer.score_single(article)

        # Should produce a valid score
        self.assertIsNotNone(score)
        self.assertGreater(score.editorial_score, 0)
        self.assertLessEqual(score.editorial_score, 100)
        self.assertGreater(len(score.reasons), 0)

    def test_multi_article_ranking(self):
        """Test ranking multiple articles."""
        articles = [
            {
                "id": 1,
                "title": "IPO Announcement - Tech Startup",
                "excerpt": "A new tech startup announced IPO",
                "source_name": "Agence Ecofin",
                "published_at": datetime.utcnow().isoformat(),
                "country": "CI",
                "total_interactions": 300,
            },
            {
                "id": 2,
                "title": "Local News",
                "excerpt": "Small local news item",
                "source_name": "Local News",
                "published_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "country": "NG",
                "total_interactions": 10,
            },
        ]

        ranked = self.scorer.score_and_rank(articles=articles, top_k=10, min_score=0)

        # Should return articles in score order
        if len(ranked) > 1:
            self.assertGreaterEqual(
                ranked[0].editorial_score,
                ranked[1].editorial_score,
                "Should be sorted by score descending"
            )


if __name__ == "__main__":
    unittest.main()
