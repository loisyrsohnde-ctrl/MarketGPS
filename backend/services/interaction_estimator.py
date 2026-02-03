"""
Estimateur d'interactions pour les articles.

Comme nous n'avons pas accès aux vraies métriques des sites,
nous estimons les interactions basées sur:
- Trust score de la source
- Présence de mots-clés viraux
- Heure de publication (prime time = plus d'interactions)
- Longueur et style du titre
"""

import re
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Mots-clés qui indiquent un contenu potentiellement viral
VIRAL_KEYWORDS_FR = [
    "exclusif", "urgent", "breaking", "scandale", "révélation",
    "milliards", "millions", "record", "historique", "choc",
    "crise", "explosion", "effondrement", "première fois",
    "inédit", "secret", "fuite", "corruption", "arrestation",
    "mystère", "disparition", "découverte", "insolite",
]

VIRAL_KEYWORDS_EN = [
    "exclusive", "breaking", "scandal", "revealed", "billions",
    "millions", "record", "historic", "shock", "crisis",
    "collapse", "first ever", "unprecedented", "secret",
    "leaked", "corruption", "arrested", "mystery",
    "disappearance", "discovery", "unusual",
]

# Scores de confiance par source (mapping)
SOURCE_TRUST_SCORES = {
    "Agence Ecofin": 0.95,
    "Jeune Afrique": 0.90,
    "Financial Afrik": 0.85,
    "Africa Intelligence": 0.90,
    "The Africa Report": 0.85,
    "Sika Finance": 0.80,
    "Business Daily Africa": 0.80,
    "Business Day SA": 0.80,
    "EcoMatin": 0.75,
    "Minutes Eco": 0.75,
    "APS Economie": 0.75,
    "Le Soleil Economie": 0.75,
}

class InteractionEstimator:
    """Estime le nombre d'interactions pour les articles."""

    def __init__(self, sources_registry: Optional[List[Dict]] = None):
        """
        Initialise l'estimateur.

        Args:
            sources_registry: Liste optionnelle des sources avec leurs métadonnées
        """
        self.sources = sources_registry or []

    def estimate_interactions(
        self,
        title: str,
        content: str = "",
        source_name: str = "",
        published_at: Optional[datetime] = None,
        actual_interactions: Optional[int] = None,
    ) -> int:
        """
        Estime le nombre d'interactions pour un article.

        Si actual_interactions est fourni (scraping réel), l'utilise.
        Sinon, estime basé sur plusieurs facteurs.

        Args:
            title: Titre de l'article
            content: Contenu de l'article (optionnel)
            source_name: Nom de la source
            published_at: Date/heure de publication
            actual_interactions: Interactions réelles si disponibles

        Returns:
            Estimation du nombre d'interactions
        """
        if actual_interactions is not None:
            return actual_interactions

        base_score = 100  # Score de base

        # 1. Trust score de la source (x1 à x3)
        source_trust = self._get_source_trust(source_name)
        base_score *= (1 + source_trust * 2)

        # 2. Mots-clés viraux (x1.0 à x3.0)
        viral_multiplier = self._count_viral_keywords(title, content)
        base_score *= viral_multiplier

        # 3. Heure de publication (prime time = x1.5)
        if published_at and self._is_prime_time(published_at):
            base_score *= 1.5

        # 4. Longueur du titre (titres accrocheurs = x1.2)
        if 40 <= len(title) <= 100:
            base_score *= 1.2
        elif 20 <= len(title) < 40:
            base_score *= 0.9

        # 5. Nombres et chiffres dans le titre (x1.3)
        if re.search(r'\d+', title):
            base_score *= 1.3

        # 6. Questions rhétoriques ou listes (x1.1)
        if re.search(r'[?:]$', title):
            base_score *= 1.1

        # Ajouter une variance
        import hashlib
        hash_value = int(hashlib.md5(f"{title}{source_name}".encode()).hexdigest(), 16)
        variance = 0.85 + (hash_value % 30) / 100  # Entre 0.85 et 1.15
        base_score *= variance

        return max(int(base_score), 30)

    def _get_source_trust(self, source_name: str) -> float:
        """
        Récupère le trust score de la source.

        Args:
            source_name: Nom de la source

        Returns:
            Score entre 0 et 1
        """
        # Vérifier dans le mapping
        if source_name in SOURCE_TRUST_SCORES:
            return SOURCE_TRUST_SCORES[source_name]

        # Chercher par correspondance partielle
        source_lower = source_name.lower()
        for mapped_source, score in SOURCE_TRUST_SCORES.items():
            if mapped_source.lower() in source_lower or source_lower in mapped_source.lower():
                return score

        # Score par défaut selon les catégories
        if any(x in source_lower for x in ['agence', 'afp', 'reuters', 'ap']):
            return 0.9
        elif any(x in source_lower for x in ['magazine', 'journal', 'echo']):
            return 0.7
        elif any(x in source_lower for x in ['blog', 'independent']):
            return 0.6

        return 0.7

    def _count_viral_keywords(self, title: str, content: str = "") -> float:
        """
        Compte les mots-clés viraux et retourne un multiplicateur.

        Args:
            title: Titre de l'article
            content: Contenu de l'article

        Returns:
            Multiplicateur entre 1.0 et 3.0
        """
        text = (title + " " + content).lower()
        count = 0

        for kw in VIRAL_KEYWORDS_FR + VIRAL_KEYWORDS_EN:
            if kw.lower() in text:
                count += 1

        if count >= 5:
            return 3.0
        elif count >= 3:
            return 2.2
        elif count >= 2:
            return 1.8
        elif count >= 1:
            return 1.5

        return 1.0

    def _is_prime_time(self, dt: datetime) -> bool:
        """
        Vérifie si l'heure est en prime time.
        Prime time: 7h-9h (matin) ou 18h-21h (soir)

        Args:
            dt: Datetime à vérifier

        Returns:
            True si c'est une heure de prime time
        """
        hour = dt.hour
        return (7 <= hour <= 9) or (18 <= hour <= 21)

    def batch_estimate(
        self,
        articles: List[Dict],
        source_registry: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Estime les interactions pour un lot d'articles.

        Args:
            articles: Liste de dicts avec keys: title, content, source_name, published_at
            source_registry: Registry optionnel des sources

        Returns:
            Même liste avec colonne 'estimated_interactions' ajoutée
        """
        if source_registry:
            self.sources = source_registry

        results = []
        for article in articles:
            estimated = self.estimate_interactions(
                title=article.get('title', ''),
                content=article.get('content', ''),
                source_name=article.get('source_name', ''),
                published_at=article.get('published_at'),
                actual_interactions=article.get('actual_interactions'),
            )

            article_copy = article.copy()
            article_copy['estimated_interactions'] = estimated
            results.append(article_copy)

        return results
