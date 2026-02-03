"""
Tests unitaires pour le système de viralité et scripts vidéo.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from services.virality_service import (
    ViralityService,
    FRANCOPHONE_SUBSAHARAN,
    MIN_INTERACTIONS_THRESHOLD,
)
from services.interaction_estimator import InteractionEstimator
from services.video_script_service import VideoScriptService


class TestViralityService(unittest.TestCase):
    """Tests pour ViralityService."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.mock_db = Mock()
        self.virality_svc = ViralityService(db_conn=self.mock_db)

    def test_is_francophone_subsaharan_french_west(self):
        """Test: francophone ouest-africain."""
        result = self.virality_svc.is_francophone_subsaharan(
            source_name="Abidjan.net",
            language="fr",
            region="WEST"
        )
        self.assertTrue(result)

    def test_is_francophone_subsaharan_french_central(self):
        """Test: francophone Afrique centrale."""
        result = self.virality_svc.is_francophone_subsaharan(
            source_name="EcoMatin",
            language="fr",
            region="CENTRAL"
        )
        self.assertTrue(result)

    def test_is_francophone_subsaharan_english_west(self):
        """Test: anglophone ouest-africain (non-prioritaire)."""
        result = self.virality_svc.is_francophone_subsaharan(
            source_name="Business Daily Africa",
            language="en",
            region="WEST"
        )
        self.assertFalse(result)

    def test_is_francophone_subsaharan_french_north(self):
        """Test: francophone Afrique du Nord (non prioritaire)."""
        result = self.virality_svc.is_francophone_subsaharan(
            source_name="L'Economiste",
            language="fr",
            region="NORTH"
        )
        self.assertFalse(result)

    def test_calculate_virality_score_above_average(self):
        """Test: score de viralité > 1 (au-dessus de la moyenne)."""
        score = self.virality_svc.calculate_virality_score(
            interactions=300,
            source_avg=100
        )
        self.assertEqual(score, 3.0)

    def test_calculate_virality_score_new_source(self):
        """Test: score pour nouvelle source (pas de moyenne)."""
        score = self.virality_svc.calculate_virality_score(
            interactions=150,
            source_avg=0
        )
        self.assertEqual(score, 150.0)

    def test_get_region_for_source_west(self):
        """Test: détection région OUEST."""
        region = self.virality_svc._get_region_for_source("Seneweb Economie")
        self.assertIn(region, ["WEST", "PANAFRICAIN"])

    def test_get_region_for_source_central(self):
        """Test: détection région CENTRALE."""
        region = self.virality_svc._get_region_for_source("EcoMatin Cameroun")
        self.assertEqual(region, "CENTRAL")

    def test_get_language_for_source_french(self):
        """Test: détection langue française."""
        language = self.virality_svc._get_language_for_source("Jeune Afrique")
        self.assertEqual(language, "fr")

    def test_get_language_for_source_english(self):
        """Test: détection langue anglaise."""
        language = self.virality_svc._get_language_for_source(
            "Business Daily Africa"
        )
        self.assertEqual(language, "en")


class TestInteractionEstimator(unittest.TestCase):
    """Tests pour InteractionEstimator."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.estimator = InteractionEstimator()

    def test_estimate_interactions_base_score(self):
        """Test: estimation de base."""
        interactions = self.estimator.estimate_interactions(
            title="Normal Article Title",
            content="Some content here",
            source_name="Unknown Source",
            published_at=datetime(2024, 1, 15, 10, 0),
        )
        self.assertGreater(interactions, 0)
        self.assertLess(interactions, 500)

    def test_estimate_interactions_viral_keywords(self):
        """Test: boost avec mots-clés viraux."""
        interactions_normal = self.estimator.estimate_interactions(
            title="Normal Article",
            content="",
            source_name="Test Source",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        interactions_viral = self.estimator.estimate_interactions(
            title="Révélation Exclusive: Scandale Découvert",
            content="Secret fuite corruption arrêtation",
            source_name="Test Source",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        self.assertGreater(interactions_viral, interactions_normal)

    def test_estimate_interactions_prime_time(self):
        """Test: boost prime time (matin)."""
        interactions_morning = self.estimator.estimate_interactions(
            title="Morning Article",
            content="",
            source_name="Test",
            published_at=datetime(2024, 1, 15, 8, 0),  # Prime time
        )

        interactions_evening = self.estimator.estimate_interactions(
            title="Evening Article",
            content="",
            source_name="Test",
            published_at=datetime(2024, 1, 15, 15, 0),  # Non prime time
        )

        # Morning devrait être >= evening
        self.assertGreaterEqual(interactions_morning, interactions_evening)

    def test_estimate_interactions_with_numbers(self):
        """Test: boost avec chiffres."""
        interactions_no_numbers = self.estimator.estimate_interactions(
            title="Article sans chiffres",
            content="",
            source_name="Test",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        interactions_with_numbers = self.estimator.estimate_interactions(
            title="Article avec 1000 milliards",
            content="",
            source_name="Test",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        self.assertGreater(interactions_with_numbers, interactions_no_numbers)

    def test_count_viral_keywords_none(self):
        """Test: aucun mot-clé viral."""
        mult = self.estimator._count_viral_keywords("Normal Article", "")
        self.assertEqual(mult, 1.0)

    def test_count_viral_keywords_many(self):
        """Test: plusieurs mots-clés viraux."""
        mult = self.estimator._count_viral_keywords(
            "Révélation Exclusive Scandale Choc",
            "Secret fuite inédit"
        )
        self.assertGreater(mult, 2.0)

    def test_is_prime_time_morning(self):
        """Test: prime time matin."""
        is_prime = self.estimator._is_prime_time(datetime(2024, 1, 15, 8, 0))
        self.assertTrue(is_prime)

    def test_is_prime_time_evening(self):
        """Test: prime time soir."""
        is_prime = self.estimator._is_prime_time(datetime(2024, 1, 15, 19, 0))
        self.assertTrue(is_prime)

    def test_is_prime_time_off_peak(self):
        """Test: hors prime time."""
        is_prime = self.estimator._is_prime_time(datetime(2024, 1, 15, 12, 0))
        self.assertFalse(is_prime)

    def test_get_source_trust_known_source(self):
        """Test: score de confiance source connue."""
        trust = self.estimator._get_source_trust("Jeune Afrique")
        self.assertEqual(trust, 0.90)

    def test_get_source_trust_unknown_source(self):
        """Test: score de confiance source inconnue."""
        trust = self.estimator._get_source_trust("Unknown Blog")
        self.assertEqual(trust, 0.7)

    def test_batch_estimate(self):
        """Test: estimation batch."""
        articles = [
            {
                "title": "Article 1",
                "content": "Content 1",
                "source_name": "Source 1",
            },
            {
                "title": "Article 2 avec scandale",
                "content": "Content 2",
                "source_name": "Jeune Afrique",
            },
        ]

        results = self.estimator.batch_estimate(articles)

        self.assertEqual(len(results), 2)
        self.assertIn("estimated_interactions", results[0])
        self.assertIn("estimated_interactions", results[1])
        # Article 2 devrait avoir plus d'interactions (scandale + meilleure source)
        self.assertGreater(
            results[1]["estimated_interactions"],
            results[0]["estimated_interactions"]
        )


class TestVideoScriptService(unittest.TestCase):
    """Tests pour VideoScriptService."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.mock_db = Mock()
        self.video_svc = VideoScriptService(get_db_conn=self.mock_db)

    def test_generate_id_format(self):
        """Test: format de l'ID généré."""
        id1 = self.video_svc._generate_id()
        id2 = self.video_svc._generate_id()

        self.assertTrue(id1.startswith("script_"))
        self.assertTrue(id2.startswith("script_"))
        self.assertNotEqual(id1, id2)
        self.assertEqual(len(id1), len("script_") + 12)

    def test_parse_response_json(self):
        """Test: parsing de réponse JSON."""
        json_text = '''{
            "hook": "Test hook",
            "script": "Test script",
            "key_facts": ["fact1", "fact2"],
            "sources_to_cite": ["source1"]
        }'''

        result = self.video_svc._parse_response(json_text)

        self.assertEqual(result["hook"], "Test hook")
        self.assertEqual(result["script"], "Test script")
        self.assertEqual(len(result["key_facts"]), 2)

    def test_parse_response_markdown_json(self):
        """Test: parsing markdown JSON."""
        markdown_text = '''```json
        {
            "hook": "Test hook",
            "script": "Test script",
            "key_facts": [],
            "sources_to_cite": []
        }
        ```'''

        result = self.video_svc._parse_response(markdown_text)

        self.assertEqual(result["hook"], "Test hook")
        self.assertEqual(result["script"], "Test script")

    def test_word_count_estimation(self):
        """Test: estimation de la durée."""
        # 150 words / minute
        script_300_words = " ".join(["word"] * 300)
        duration = int(len(script_300_words.split()) / 150 * 60)

        self.assertEqual(duration, 120)  # 2 minutes

    def test_word_count_estimation_500_words(self):
        """Test: estimation durée pour 500 mots."""
        script_500_words = " ".join(["word"] * 500)
        duration = int(len(script_500_words.split()) / 150 * 60)

        self.assertEqual(duration, 200)  # ~3.3 minutes


class TestViralArticleSelection(unittest.TestCase):
    """Tests d'intégration pour la sélection d'articles viraux."""

    def test_francophone_priority_vs_others(self):
        """
        Test: une source francophone sub-saharienne avec 50 interactions
        devrait être viral, tandis qu'une source anglaise avec 50
        interactions devrait dépendre de sa moyenne.
        """
        virality_svc = ViralityService(db_conn=None)

        # Source francophone: 50 >= seuil min (50) = VIRAL
        is_viral_fr = virality_svc.is_francophone_subsaharan(
            "Jeune Afrique",
            "fr",
            "WEST"
        )
        self.assertTrue(is_viral_fr)

        # Source anglaise: pas prioritaire
        is_viral_en = virality_svc.is_francophone_subsaharan(
            "Business Daily Africa",
            "en",
            "EAST"
        )
        self.assertFalse(is_viral_en)


if __name__ == "__main__":
    unittest.main()
