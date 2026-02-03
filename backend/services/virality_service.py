"""
Service de calcul de viralité des actualités.

Règles:
- Sources francophones Afrique sub-saharienne: toujours incluses si > seuil minimum
- Autres sources: incluses SEULEMENT si interactions >= 10x leur moyenne historique
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class SourceStats:
    """Statistiques d'une source de news."""
    source_id: str
    source_name: str
    region: str
    language: str
    avg_interactions: float
    median_interactions: float
    total_articles: int
    last_updated: datetime

@dataclass
class ViralArticle:
    """Article considéré comme viral."""
    article_id: str
    title: str
    source_name: str
    interactions: int
    virality_score: float  # interactions / avg_interactions
    is_viral: bool
    region: str
    language: str
    published_at: Optional[str]
    url: str

# Pays francophones sub-sahariens prioritaires
FRANCOPHONE_SUBSAHARAN = [
    "SN",  # Sénégal
    "CI",  # Côte d'Ivoire
    "ML",  # Mali
    "BF",  # Burkina Faso
    "NE",  # Niger
    "TG",  # Togo
    "BJ",  # Bénin
    "GN",  # Guinée
    "CM",  # Cameroun
    "GA",  # Gabon
    "CG",  # Congo
    "CD",  # RDC
    "TD",  # Tchad
    "CF",  # Centrafrique
    "RW",  # Rwanda
    "BI",  # Burundi
]

# Régions francophones
FRANCOPHONE_REGIONS = {
    "senegal": ("SN", "WEST", "fr"),
    "cote_ivoire": ("CI", "WEST", "fr"),
    "mali": ("ML", "WEST", "fr"),
    "burkina_faso": ("BF", "WEST", "fr"),
    "niger": ("NE", "WEST", "fr"),
    "togo": ("TG", "WEST", "fr"),
    "benin": ("BJ", "WEST", "fr"),
    "cameroun": ("CM", "CENTRAL", "fr"),
    "gabon": ("GA", "CENTRAL", "fr"),
    "congo": ("CG", "CENTRAL", "fr"),
    "rdc": ("CD", "CENTRAL", "fr"),
    "tchad": ("TD", "CENTRAL", "fr"),
    "maroc": ("MA", "NORTH", "fr"),
}

VIRALITY_THRESHOLD = 10  # 10x la moyenne pour sources non-prioritaires
MIN_INTERACTIONS_THRESHOLD = 50  # Minimum pour être considéré viral

class ViralityService:
    """Service pour calculer la viralité et identifier les articles viraux."""

    def __init__(self, db_conn=None):
        """
        Initialise le service.

        Args:
            db_conn: Fonction pour obtenir une connexion SQLite
        """
        self.get_conn = db_conn

    def calculate_source_stats(self, days: int = 30) -> Dict[str, SourceStats]:
        """
        Calcule les statistiques d'interactions par source sur les N derniers jours.

        Args:
            days: Nombre de jours à analyser (défaut: 30)

        Returns:
            Dict mapping source_name -> SourceStats
        """
        if not self.get_conn:
            logger.warning("No database connection available")
            return {}

        stats = {}
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Récupérer les stats par source
            cursor.execute("""
                SELECT
                    source_name,
                    COUNT(*) as total_articles,
                    AVG(COALESCE(total_interactions, 0)) as avg_interactions,
                    MAX(COALESCE(total_interactions, 0)) as max_interactions
                FROM news_articles
                WHERE created_at >= ?
                GROUP BY source_name
                ORDER BY total_articles DESC
            """, (cutoff_date,))

            rows = cursor.fetchall()

            for row in rows:
                source_name = row[0]
                total_articles = row[1]
                avg_interactions = row[2] or 0
                max_interactions = row[3] or 0

                # Récupérer les valeurs de médiane
                cursor.execute("""
                    SELECT total_interactions
                    FROM news_articles
                    WHERE source_name = ? AND created_at >= ?
                    ORDER BY total_interactions
                """, (source_name, cutoff_date))

                interactions = [r[0] or 0 for r in cursor.fetchall()]
                median_interactions = statistics.median(interactions) if interactions else 0

                # Déterminer la région et la langue
                region = self._get_region_for_source(source_name)
                language = self._get_language_for_source(source_name)

                stats[source_name] = SourceStats(
                    source_id=source_name.lower().replace(" ", "_"),
                    source_name=source_name,
                    region=region,
                    language=language,
                    avg_interactions=avg_interactions,
                    median_interactions=median_interactions,
                    total_articles=total_articles,
                    last_updated=datetime.utcnow()
                )

            conn.close()

        except Exception as e:
            logger.error(f"Error calculating source stats: {e}")

        return stats

    def get_viral_articles(
        self,
        limit: int = 20,
        include_francophone_priority: bool = True,
        virality_multiplier: float = 10.0,
        days: int = 7
    ) -> List[ViralArticle]:
        """
        Récupère les articles viraux selon les règles:
        1. Sources francophones sub-sahariennes: interactions > MIN_THRESHOLD
        2. Autres sources: interactions >= virality_multiplier * avg_interactions

        Args:
            limit: Nombre max d'articles à retourner
            include_francophone_priority: Si True, les sources francophones sont prioritaires
            virality_multiplier: Multiplicateur pour les sources non-prioritaires (défaut: 10x)
            days: Nombre de jours à considérer (défaut: 7)

        Returns:
            List[ViralArticle]
        """
        if not self.get_conn:
            logger.warning("No database connection available")
            return []

        viral_articles = []
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            # Calculer les stats des sources
            source_stats = self.calculate_source_stats(days=days)

            conn = self.get_conn()
            cursor = conn.cursor()

            # Récupérer tous les articles des derniers jours
            cursor.execute("""
                SELECT
                    id,
                    title,
                    source_name,
                    total_interactions,
                    published_at,
                    url
                FROM news_articles
                WHERE created_at >= ?
                ORDER BY total_interactions DESC
                LIMIT 1000
            """, (cutoff_date,))

            rows = cursor.fetchall()

            for row in rows:
                article_id = row[0]
                title = row[1]
                source_name = row[2]
                interactions = row[3] or 0
                published_at = row[4]
                url = row[5]

                # Déterminer la région et la langue
                region = self._get_region_for_source(source_name)
                language = self._get_language_for_source(source_name)

                # Appliquer les règles de viralité
                is_viral = False
                virality_score = 0.0

                if include_francophone_priority and self.is_francophone_subsaharan(
                    source_name, language, region
                ):
                    # Règle 1: Sources francophones sub-sahariennes
                    is_viral = interactions >= MIN_INTERACTIONS_THRESHOLD
                    virality_score = (
                        interactions / MIN_INTERACTIONS_THRESHOLD
                        if MIN_INTERACTIONS_THRESHOLD > 0
                        else interactions
                    )
                else:
                    # Règle 2: Autres sources - 10x la moyenne
                    if source_name in source_stats:
                        avg = source_stats[source_name].avg_interactions
                        threshold = max(
                            avg * virality_multiplier,
                            MIN_INTERACTIONS_THRESHOLD
                        )
                        is_viral = interactions >= threshold
                        virality_score = interactions / avg if avg > 0 else interactions
                    else:
                        # Nouvelle source - utiliser le seuil minimum
                        is_viral = interactions >= MIN_INTERACTIONS_THRESHOLD
                        virality_score = (
                            interactions / MIN_INTERACTIONS_THRESHOLD
                            if MIN_INTERACTIONS_THRESHOLD > 0
                            else interactions
                        )

                if is_viral:
                    viral_articles.append(
                        ViralArticle(
                            article_id=article_id,
                            title=title,
                            source_name=source_name,
                            interactions=interactions,
                            virality_score=virality_score,
                            is_viral=True,
                            region=region,
                            language=language,
                            published_at=published_at,
                            url=url
                        )
                    )

                if len(viral_articles) >= limit:
                    break

            conn.close()

        except Exception as e:
            logger.error(f"Error getting viral articles: {e}")

        return viral_articles

    def is_francophone_subsaharan(
        self,
        source_name: str,
        language: str,
        region: str
    ) -> bool:
        """
        Vérifie si la source est francophone sub-saharienne.

        Args:
            source_name: Nom de la source
            language: Code langue (ex: 'fr', 'en')
            region: Région (ex: 'WEST', 'CENTRAL')

        Returns:
            True si c'est une source prioritaire
        """
        # Vérifier par région et langue
        if language == 'fr' and region in ['WEST', 'CENTRAL']:
            return True

        # Vérifier par catégorie dans le mapping des régions
        source_lower = source_name.lower()
        for category_name, (country, cat_region, cat_lang) in FRANCOPHONE_REGIONS.items():
            if category_name in source_lower or source_name in category_name:
                return cat_lang == 'fr' and cat_region in ['WEST', 'CENTRAL']

        return False

    def calculate_virality_score(
        self,
        interactions: int,
        source_avg: float
    ) -> float:
        """
        Calcule le score de viralité (interactions / moyenne).

        Args:
            interactions: Nombre d'interactions réelles
            source_avg: Moyenne historique pour la source

        Returns:
            Score de viralité
        """
        if source_avg <= 0:
            return float(interactions)  # Nouvelle source, pas de moyenne
        return interactions / source_avg

    def _get_region_for_source(self, source_name: str) -> str:
        """Détermine la région d'une source."""
        source_lower = source_name.lower()

        # Vérifier le mapping des régions
        for category_name, (country, region, lang) in FRANCOPHONE_REGIONS.items():
            if category_name in source_lower or category_name in source_lower:
                return region

        # Par défaut, utiliser des heuristiques
        if any(x in source_lower for x in ['senegal', 'sn', 'dakar']):
            return 'WEST'
        elif any(x in source_lower for x in ['cote ivoire', 'ivory', 'ci', 'abidjan']):
            return 'WEST'
        elif any(x in source_lower for x in ['cameroun', 'cm', 'yaoundé']):
            return 'CENTRAL'
        elif any(x in source_lower for x in ['maroc', 'ma', 'casablanca']):
            return 'NORTH'
        elif any(x in source_lower for x in ['kenya', 'south africa', 'sa', 'ke']):
            return 'EAST'
        else:
            return 'PANAFRICAIN'

    def _get_language_for_source(self, source_name: str) -> str:
        """Détermine la langue d'une source."""
        source_lower = source_name.lower()

        # Vérifier les mots-clés anglais
        if any(x in source_lower for x in ['business', 'africa report', 'daily', 'news']):
            if 'french' not in source_lower and 'maroc' not in source_lower:
                return 'en'

        # Par défaut francophone pour l'Afrique francophone
        return 'fr'
