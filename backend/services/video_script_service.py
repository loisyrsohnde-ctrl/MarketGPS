"""
Service de génération de scripts vidéo style Hugo Décrypte.

Style caractéristique:
- Fait principal énoncé directement au début
- Ton direct, factuel, accessible
- Structure: Accroche → Contexte → Développement → Conclusion
- Durée cible: 300-500 mots (1-2 minutes de voix off)
"""

import json
import sqlite3
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import logging
import uuid
import os

logger = logging.getLogger(__name__)

# Template Gemini pour la génération de scripts courts (Hugo Décrypte style)
HUGO_DECRYPTE_PROMPT = '''Tu es un rédacteur de scripts pour des vidéos d'actualité style "Hugo Décrypte".

STYLE HUGO DÉCRYPTE:
- Le fait principal est TOUJOURS énoncé dans la première phrase
- Ton direct, factuel, accessible au grand public
- Phrases courtes et percutantes
- Pas de jargon technique non expliqué
- Utilise "on" plutôt que "nous" ou formes passives
- Rythme dynamique pour captiver l'attention

STRUCTURE DU SCRIPT:
1. ACCROCHE (1-2 phrases): Le fait principal, chiffre clé ou information choc
2. CONTEXTE (2-3 phrases): Qui, quoi, où, quand
3. DÉVELOPPEMENT (3-5 paragraphes): Détails, enjeux, réactions
4. CONCLUSION (1-2 phrases): Impact ou ce qu'il faut retenir

CONTRAINTES:
- Entre 300 et 500 mots exactement
- Destiné à être lu en voix off pour une vidéo
- Pas de questions rhétoriques
- Pas d'expressions comme "dans cet article" ou "comme vous le savez"
- Chaque phrase doit apporter une information nouvelle

ARTICLE À TRANSFORMER:
Titre: {title}
Source: {source}
Date: {date}
Contenu: {content}

RÉPONDS EN JSON:
{{
  "hook": "Première phrase percutante qui donne le fait principal",
  "script": "Le script complet pour voix off (300-500 mots)",
  "key_facts": ["fait clé 1", "fait clé 2", "fait clé 3"],
  "sources_to_cite": ["source 1", "source 2"]
}}'''

# Template pour scripts YouTube longs (10 minutes)
YOUTUBE_LONG_FORM_PROMPT = '''Tu es un rédacteur expert en création de contenus YouTube pour un public francophone africain et global.

OBJECTIF:
Créer un script pour une vidéo YouTube de 10 minutes (~1500 mots) qui propose une analyse approfondie d'un sujet d'actualité.

STYLE:
- Accroche percutante dans les 3 premières secondes
- Ton expert mais accessible (pas de jargon non expliqué)
- Structure narrative qui maintient l'engagement
- Adressé directement aux spectateurs ("tu", "vous")
- Utilise des transitions fluides entre les sections
- Inclut des moments de "révélation" ou de "twist" informatif

STRUCTURE REQUISE:
1. INTRO HOOK (15 secondes): Question rhétorique ou statement qui captive
2. CONTEXTE GLOBAL (1-2 minutes): Background, historique, qui est affecté
3. ANALYSE APPROFONDIE (4-5 sections, 6-8 minutes):
   - Causes/origines
   - Impacts économiques/sociaux
   - Perspectives régionales (Afrique, monde)
   - Perspectives futures/tendances
4. EXPERT INSIGHTS (1-2 minutes): Ce que les experts disent, données clés
5. IMPLICATIONS PRATIQUES (1 minute): "Pourquoi tu devrais t'en soucier"
6. CONCLUSION + CTA (30 secondes): Résumé, appel à l'action (like, subscribe, comment)

CONTRAINTES:
- Exactement entre 1400-1600 mots
- Destiné à être lu en voix off (pas de dialogues)
- Chaque section doit être claire et mémorable
- Inclure au minimum 3 statistiques/données concrètes
- Pas de publicités déguisées ou promotions
- Langage neutre et factuel

ARTICLE À ANALYSER:
Titre: {title}
Source: {source}
Date: {date}
Contenu: {content}

RÉPONDS EN JSON:
{{
  "title_suggestions": [
    "Suggestion 1 pour titre YouTube (50-60 caractères)",
    "Suggestion 2 pour titre YouTube",
    "Suggestion 3 pour titre YouTube"
  ],
  "description": "Description YouTube complète avec timestamps de chaque section (200-300 mots)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "script_sections": [
    {{
      "section": "intro",
      "duration_seconds": 15,
      "title": "Hook d'introduction",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "context",
      "duration_seconds": 90,
      "title": "Contexte global",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "analysis_part1",
      "duration_seconds": 120,
      "title": "Causes et origines",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "analysis_part2",
      "duration_seconds": 120,
      "title": "Impacts économiques",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "analysis_part3",
      "duration_seconds": 120,
      "title": "Perspective africaine",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "analysis_part4",
      "duration_seconds": 120,
      "title": "Tendances futures",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "expert_insights",
      "duration_seconds": 90,
      "title": "Ce que disent les experts",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "implications",
      "duration_seconds": 60,
      "title": "Pourquoi c'est important pour toi",
      "content": "Texte exact pour voix off..."
    }},
    {{
      "section": "conclusion",
      "duration_seconds": 30,
      "title": "Conclusion et appel à l'action",
      "content": "Texte exact pour voix off..."
    }}
  ],
  "total_word_count": 1500,
  "key_statistics": [
    {"stat": "Statistique 1", "source": "Source of stat"},
    {"stat": "Statistique 2", "source": "Source of stat"}
  ],
  "thumbnail_suggestions": [
    "Text to display on thumbnail 1",
    "Text to display on thumbnail 2"
  ]
}}'''

# Template pour enrichissement d'articles
ARTICLE_ENRICHMENT_PROMPT = '''Tu es un chercheur et analyste spécialisé dans les actualités africaines et mondiales.

TÂCHE:
Enrichir le contenu d'un article en ajoutant:
1. Contexte historique pertinent
2. Statistiques et données clés
3. Perspectives régionales (particulièrement Afrique)
4. Tendances et prédictions
5. Acteurs clés impliqués

L'enrichissement doit:
- Rester factuel et sourcé
- Ajouter de la profondeur au sujet
- Être compréhensible par un public non-expert
- Inclure au minimum 3 faits/données supplémentaires
- Respecter l'angle original de l'article

ARTICLE À ENRICHIR:
Titre: {title}
Contenu original: {content}

RÉPONDS EN JSON:
{{
  "enriched_content": "Contenu original enrichi avec contexte, statistiques et analyse approfondie",
  "added_statistics": [
    {{
      "statistic": "La statistique",
      "context": "Explication et contexte",
      "source": "Source si disponible"
    }}
  ],
  "historical_context": "Contexte historique pertinent en 2-3 paragraphes",
  "regional_impact": {{
    "africa": "Impact et pertinence pour l'Afrique",
    "global": "Perspective mondiale"
  }},
  "key_actors": ["Acteur 1", "Acteur 2", "Acteur 3"],
  "future_implications": "Tendances et implications futures en 2-3 paragraphes"
}}'''

# Template pour métadonnées sociales
SOCIAL_METADATA_PROMPT = '''Tu es un expert en optimisation de contenu pour réseaux sociaux et YouTube.

TÂCHE:
Générer des métadonnées optimisées pour partage sur YouTube et réseaux sociaux:
1. 3 variantes de titre YouTube (différentes longueurs et angles)
2. Description YouTube détaillée avec timestamps
3. Hashtags pertinents (mix de populaires et nichés)
4. Suggestions pour miniatures/thumbnails

Optimisation requise:
- Titres: Hook fort, mots-clés importants au début
- Description: Structure avec timestamps, CTA, liens
- Hashtags: 10-15 hashtags variés et pertinents
- Thumbnails: Texte court, accrocheur, en français

ARTICLE:
Titre: {title}
Contenu: {content}

RÉPONDS EN JSON:
{{
  "title_variants": [
    {{
      "variant": "Titre long pour maximum visibilité (55-60 caractères)",
      "approach": "Approche utilisée (curiosity gap, numbers, etc)"
    }},
    {{
      "variant": "Titre court et direct (40-45 caractères)",
      "approach": "Approche utilisée"
    }},
    {{
      "variant": "Titre avec angle africain/local",
      "approach": "Approche utilisée"
    }}
  ],
  "description": "Description YouTube complète:\\n00:00 - Introduction\\n00:30 - Premier point\\n02:15 - Deuxième point\\n...\\n\\nContenu et contexte...\\n\\nSuscribe pour plus de contenu...\\n\\n#hashtag #hashtag",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
  "thumbnail_text_options": [
    "Texte court et impactant pour thumbnail",
    "Alternative 2",
    "Alternative 3"
  ],
  "seo_keywords": ["keyword1", "keyword2", "keyword3"]
}}'''

@dataclass
class VideoScript:
    """Représente un script vidéo généré."""
    id: str
    article_id: str
    title: str
    hook: str  # Accroche (première phrase percutante)
    script_text: str  # Texte complet pour voix off
    word_count: int
    estimated_duration_seconds: int  # ~150 mots/minute
    sources_mentioned: List[str]
    key_facts: List[str]
    status: str  # 'draft', 'reviewed', 'approved', 'published'
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return asdict(self)

    @classmethod
    def from_db(cls, row: tuple) -> "VideoScript":
        """Crée depuis une ligne de base de données."""
        (
            id,
            article_id,
            title,
            hook,
            script_text,
            word_count,
            estimated_duration_seconds,
            sources_json,
            key_facts_json,
            status,
            created_at,
            updated_at,
        ) = row

        sources = json.loads(sources_json) if sources_json else []
        key_facts = json.loads(key_facts_json) if key_facts_json else []

        return cls(
            id=id,
            article_id=article_id,
            title=title,
            hook=hook,
            script_text=script_text,
            word_count=word_count,
            estimated_duration_seconds=estimated_duration_seconds,
            sources_mentioned=sources,
            key_facts=key_facts,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class YouTubeScript:
    """Représente un script YouTube long-form (10 minutes)."""
    id: str
    article_id: str
    title_suggestions: List[str]
    description: str
    tags: List[str]
    script_sections: List[Dict[str, Any]]
    total_word_count: int
    key_statistics: List[Dict[str, str]]
    thumbnail_suggestions: List[str]
    status: str = 'draft'
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return asdict(self)


@dataclass
class SocialMetadata:
    """Métadonnées sociales pour un article."""
    id: str
    article_id: str
    title_variants: List[Dict[str, str]]
    description: str
    hashtags: List[str]
    thumbnail_text_options: List[str]
    seo_keywords: List[str]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return asdict(self)


@dataclass
class EnrichedArticle:
    """Article enrichi avec contexte et données additionnelles."""
    id: str
    original_article_id: str
    enriched_content: str
    added_statistics: List[Dict[str, str]]
    historical_context: str
    regional_impact: Dict[str, str]
    key_actors: List[str]
    future_implications: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return asdict(self)


class VideoScriptService:
    """Service pour générer des scripts vidéo avec Gemini."""

    def __init__(self, get_db_conn=None):
        """
        Initialise le service.

        Args:
            get_db_conn: Fonction pour obtenir une connexion SQLite
        """
        self.get_conn = get_db_conn
        self.model = None
        self._setup_gemini()
        self._init_database()

    def _setup_gemini(self):
        """Configure Gemini API."""
        try:
            import google.generativeai as genai

            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini API configured successfully")
            else:
                logger.warning("GEMINI_API_KEY not found in environment")
        except Exception as e:
            logger.warning(f"Failed to setup Gemini: {e}")

    def _init_database(self):
        """Initialise la table des scripts vidéo."""
        if not self.get_conn:
            return

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_scripts (
                    id TEXT PRIMARY KEY,
                    article_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    hook TEXT,
                    script_text TEXT NOT NULL,
                    word_count INTEGER,
                    estimated_duration_seconds INTEGER,
                    sources_json TEXT,
                    key_facts_json TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES news_articles(id)
                )
            """)

            # Créer les index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_scripts_status
                ON video_scripts(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_scripts_article
                ON video_scripts(article_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_scripts_created
                ON video_scripts(created_at DESC)
            """)

            conn.commit()
            conn.close()
            logger.info("Video scripts table initialized")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def generate_script_sync(
        self,
        article_id: str,
        title: str,
        content: str,
        source: str,
        date: str,
    ) -> Optional[VideoScript]:
        """
        Génère un script vidéo style Hugo Décrypte pour un article (synchrone).

        Args:
            article_id: ID de l'article
            title: Titre de l'article
            content: Contenu de l'article
            source: Nom de la source
            date: Date de publication

        Returns:
            VideoScript généré, ou None si erreur
        """
        if not self.model:
            logger.error("Gemini model not configured — GEMINI_API_KEY missing or invalid")
            return None

        prompt = HUGO_DECRYPTE_PROMPT.format(
            title=title,
            source=source,
            date=date,
            content=content[:4000],  # Limiter pour le contexte
        )

        try:
            logger.info(f"Generating script for article {article_id} with Gemini")
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            # Valider la réponse
            if not all(k in result for k in ['hook', 'script', 'key_facts']):
                logger.error(f"Invalid response format: {result}")
                return None

            word_count = len(result['script'].split())

            # Vérifier la longueur (300-500 mots)
            if word_count < 250 or word_count > 600:
                logger.warning(f"Script word count {word_count} outside recommended range")

            # Estimation durée: ~150 mots/minute
            duration = int(word_count / 150 * 60)

            script = VideoScript(
                id=self._generate_id(),
                article_id=article_id,
                title=title,
                hook=result['hook'],
                script_text=result['script'],
                word_count=word_count,
                estimated_duration_seconds=duration,
                sources_mentioned=result.get('sources_to_cite', []),
                key_facts=result.get('key_facts', []),
                status='draft',
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )

            # Sauvegarder en base
            self._save_script(script)
            logger.info(f"Script generated successfully: {script.id}")

            return script

        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

    async def generate_script(
        self,
        article_id: str,
        title: str,
        content: str,
        source: str,
        date: str,
    ) -> Optional[VideoScript]:
        """
        Génère un script vidéo style Hugo Décrypte pour un article (async wrapper).
        """
        return self.generate_script_sync(
            article_id=article_id,
            title=title,
            content=content,
            source=source,
            date=date,
        )

    def _generate_script_internal(
        self,
        article_id: str,
        title: str,
        content: str,
        source: str,
        date: str,
    ) -> Optional[VideoScript]:
        """Internal script generation logic — kept for backward compatibility."""
        if not self.model:
            logger.error("Gemini model not configured")
            return None

        prompt = HUGO_DECRYPTE_PROMPT.format(
            title=title,
            source=source,
            date=date,
            content=content[:4000],
        )

        try:
            logger.info(f"Generating script for article {article_id}")
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            # Valider la réponse
            if not all(k in result for k in ['hook', 'script', 'key_facts']):
                logger.error(f"Invalid response format: {result}")
                return None

            word_count = len(result['script'].split())

            # Vérifier la longueur (300-500 mots)
            if word_count < 250 or word_count > 600:
                logger.warning(f"Script word count {word_count} outside recommended range")

            # Estimation durée: ~150 mots/minute
            duration = int(word_count / 150 * 60)

            script = VideoScript(
                id=self._generate_id(),
                article_id=article_id,
                title=title,
                hook=result['hook'],
                script_text=result['script'],
                word_count=word_count,
                estimated_duration_seconds=duration,
                sources_mentioned=result.get('sources_to_cite', []),
                key_facts=result.get('key_facts', []),
                status='draft',
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )

            # Sauvegarder en base
            self._save_script(script)
            logger.info(f"Script generated successfully: {script.id}")

            return script

        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

    def get_scripts(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[VideoScript]:
        """
        Récupère les scripts avec filtrage optionnel.

        Args:
            status: Filtrer par statut ('draft', 'reviewed', 'approved', 'published')
            limit: Nombre max de scripts
            offset: Offset pour pagination

        Returns:
            List[VideoScript]
        """
        if not self.get_conn:
            logger.warning("No database connection")
            return []

        scripts = []

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            query = "SELECT * FROM video_scripts WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                scripts.append(VideoScript.from_db(row))

            conn.close()

        except Exception as e:
            logger.error(f"Error getting scripts: {e}")

        return scripts

    def get_script_by_id(self, script_id: str) -> Optional[VideoScript]:
        """
        Récupère un script par son ID.

        Args:
            script_id: ID du script

        Returns:
            VideoScript ou None
        """
        if not self.get_conn:
            return None

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM video_scripts WHERE id = ?", (script_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return VideoScript.from_db(row)

        except Exception as e:
            logger.error(f"Error getting script: {e}")

        return None

    def update_script(
        self,
        script_id: str,
        script_text: Optional[str] = None,
        hook: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """
        Met à jour un script (édition manuelle ou changement de statut).

        Args:
            script_id: ID du script
            script_text: Nouveau texte du script (optionnel)
            hook: Nouvelle accroche (optionnel)
            status: Nouveau statut (optionnel)

        Returns:
            True si succès
        """
        if not self.get_conn:
            return False

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            updates = []
            params = []

            if script_text is not None:
                updates.append("script_text = ?")
                params.append(script_text)
                # Recalculer word_count
                word_count = len(script_text.split())
                updates.append("word_count = ?")
                params.append(word_count)
                # Recalculer durée
                duration = int(word_count / 150 * 60)
                updates.append("estimated_duration_seconds = ?")
                params.append(duration)

            if hook is not None:
                updates.append("hook = ?")
                params.append(hook)

            if status is not None:
                updates.append("status = ?")
                params.append(status)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(script_id)

            query = f"UPDATE video_scripts SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            conn.close()

            logger.info(f"Script {script_id} updated")
            return True

        except Exception as e:
            logger.error(f"Error updating script: {e}")
            return False

    def publish_script_to_news(self, script_id: str) -> bool:
        """
        Publie le contenu du script vers les articles (news_articles).

        Args:
            script_id: ID du script à publier

        Returns:
            True si succès
        """
        if not self.get_conn:
            return False

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Récupérer le script
            script = self.get_script_by_id(script_id)
            if not script:
                logger.error(f"Script not found: {script_id}")
                return False

            # Récupérer l'article
            cursor.execute(
                "SELECT id FROM news_articles WHERE id = ?",
                (script.article_id,)
            )
            article = cursor.fetchone()

            if not article:
                logger.error(f"Article not found: {script.article_id}")
                conn.close()
                return False

            # Mettre à jour l'article avec le contenu du script
            cursor.execute("""
                UPDATE news_articles
                SET summary = ?, status = 'published'
                WHERE id = ?
            """, (script.script_text, script.article_id))

            # Marquer le script comme publié
            self.update_script(script_id, status='published')

            conn.commit()
            conn.close()

            logger.info(f"Script {script_id} published to news article {script.article_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing script: {e}")
            return False

    def _parse_response(self, text: str) -> Dict:
        """
        Parse la réponse JSON de Gemini.

        Args:
            text: Texte de la réponse

        Returns:
            Dict avec les clés hook, script, key_facts, sources_to_cite
        """
        # Nettoyer les blocs markdown
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]

        return json.loads(text.strip())

    def _generate_id(self) -> str:
        """Génère un ID unique pour le script."""
        return f"script_{uuid.uuid4().hex[:12]}"

    def rewrite_as_journalistic_article(
        self,
        article_content: str,
        script_text: str,
    ) -> Optional[str]:
        """
        Rédige le script vidéo en style article journalistique professionnel.

        Transforme un script vidéo court en article blog/actualité complet:
        - Enrichissement de contexte et de faits
        - Structure journalistique (introduction, développement, conclusion)
        - Ton professionnel et inclusif
        - Adaptation pour lecture linéaire (vs. voix off)

        Args:
            article_content: Contenu complet de l'article source
            script_text: Texte du script vidéo à transformer

        Returns:
            Article journalistique rédité, ou None si erreur
        """
        if not self.model:
            logger.error("Gemini model not configured for journalistic rewrite")
            return None

        prompt = '''Tu es un journaliste professionnel rédigeant pour un blog/portail d'actualités.

TÂCHE:
Transformer ce script vidéo court en article journalistique complet et professionnel.

STYLE REQUIS:
- Introduction accrocheuse avec le fait principal
- Structure claire: Contexte → Enjeux → Développement → Conclusion
- Ton professionnel, factuel et accessible
- Paragraphes bien structurés (4-6 phrases chacun)
- Inclusion de détails et contexte enrichis
- Longueur cible: 500-800 mots

ENRICHISSEMENT:
- Ajouter contexte historique ou comparatif si pertinent
- Inclure citations ou chiffres si disponibles
- Expliquer les enjeux et implications
- Adapter pour lectorat large (pas uniquement francophone)

STRUCTURE RECOMMANDÉE:
1. Titre accrocheur (optionnel, sur une ligne seule)
2. Chapô/lead (1-2 phrases percutantes)
3. 3-4 paragraphes de développement
4. Conclusion ou perspective

ORIGINAL (script vidéo):
{script}

ARTICLE SOURCE (pour enrichissement):
{article}

Rédige directement l'article sans explications préalables. Commence par le titre si pertinent, puis le contenu.
'''

        try:
            logger.info("Rewriting script as journalistic article")
            prompt_formatted = prompt.format(
                script=script_text[:2000],  # Limiter la longueur
                article=article_content[:3000],
            )

            response = self.model.generate_content(prompt_formatted)
            rewritten = response.text.strip()

            if not rewritten:
                logger.warning("Gemini returned empty response for journalistic rewrite")
                return None

            # Nettoyer les artefacts markdown si présents
            if rewritten.startswith("```"):
                # Si c'est un bloc de code, l'extraire
                if "```markdown" in rewritten:
                    rewritten = rewritten.split("```markdown")[1].split("```")[0].strip()
                elif "```" in rewritten:
                    rewritten = rewritten.split("```")[1].split("```")[0].strip()

            logger.info(f"Journalistic rewrite completed: {len(rewritten)} characters")
            return rewritten

        except Exception as e:
            logger.error(f"Error rewriting as journalistic article: {e}")
            return None

    def _save_script(self, script: VideoScript):
        """Sauvegarde le script en base de données."""
        if not self.get_conn:
            logger.warning("No database connection")
            return

        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO video_scripts
                (id, article_id, title, hook, script_text, word_count,
                 estimated_duration_seconds, sources_json, key_facts_json,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                script.id,
                script.article_id,
                script.title,
                script.hook,
                script.script_text,
                script.word_count,
                script.estimated_duration_seconds,
                json.dumps(script.sources_mentioned),
                json.dumps(script.key_facts),
                script.status,
                script.created_at,
                script.updated_at,
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error saving script: {e}")

    def generate_youtube_script(
        self,
        article_content: str,
        article_title: str,
        article_id: Optional[str] = None,
        source: str = "Unknown",
        date: str = "",
    ) -> Optional[YouTubeScript]:
        """
        Génère un script YouTube long-form (10 minutes, ~1500 mots).

        Inclut: accroche, contexte, plusieurs sections d'analyse, expert insights,
        implications pratiques, et conclusion avec CTA.

        Args:
            article_content: Contenu de l'article à transformer
            article_title: Titre de l'article
            article_id: ID de l'article (optionnel)
            source: Source de l'article
            date: Date de publication

        Returns:
            YouTubeScript généré, ou None si erreur
        """
        if not self.model:
            logger.error("Gemini model not configured — GEMINI_API_KEY missing or invalid")
            return None

        prompt = YOUTUBE_LONG_FORM_PROMPT.format(
            title=article_title,
            source=source,
            date=date,
            content=article_content[:6000],  # Augmenter la limite pour plus de contexte
        )

        try:
            logger.info(f"Generating YouTube long-form script for {article_title}")
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            # Valider la réponse
            required_keys = ['title_suggestions', 'description', 'tags', 'script_sections', 'total_word_count']
            if not all(k in result for k in required_keys):
                logger.error(f"Invalid response format for YouTube script: missing keys")
                return None

            youtube_script = YouTubeScript(
                id=self._generate_id(),
                article_id=article_id or self._generate_id(),
                title_suggestions=result.get('title_suggestions', []),
                description=result.get('description', ''),
                tags=result.get('tags', []),
                script_sections=result.get('script_sections', []),
                total_word_count=result.get('total_word_count', 0),
                key_statistics=result.get('key_statistics', []),
                thumbnail_suggestions=result.get('thumbnail_suggestions', []),
                status='draft',
            )

            logger.info(f"YouTube script generated successfully: {youtube_script.id}")
            return youtube_script

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in YouTube script generation: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating YouTube script: {e}")
            return None

    def generate_social_metadata(
        self,
        article_content: str,
        article_title: str,
        article_id: Optional[str] = None,
    ) -> Optional[SocialMetadata]:
        """
        Génère des métadonnées optimisées pour réseaux sociaux et YouTube.

        Inclut:
        - 3 variantes de titre (différents angles et longueurs)
        - Description YouTube avec timestamps
        - Hashtags et mots-clés SEO
        - Suggestions pour miniatures/thumbnails

        Args:
            article_content: Contenu de l'article
            article_title: Titre de l'article
            article_id: ID de l'article (optionnel)

        Returns:
            SocialMetadata générées, ou None si erreur
        """
        if not self.model:
            logger.error("Gemini model not configured — GEMINI_API_KEY missing or invalid")
            return None

        prompt = SOCIAL_METADATA_PROMPT.format(
            title=article_title,
            content=article_content[:4000],
        )

        try:
            logger.info(f"Generating social metadata for {article_title}")
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            # Valider la réponse
            required_keys = ['title_variants', 'description', 'hashtags', 'thumbnail_text_options', 'seo_keywords']
            if not all(k in result for k in required_keys):
                logger.error(f"Invalid response format for social metadata: missing keys")
                return None

            metadata = SocialMetadata(
                id=self._generate_id(),
                article_id=article_id or self._generate_id(),
                title_variants=result.get('title_variants', []),
                description=result.get('description', ''),
                hashtags=result.get('hashtags', []),
                thumbnail_text_options=result.get('thumbnail_text_options', []),
                seo_keywords=result.get('seo_keywords', []),
            )

            logger.info(f"Social metadata generated successfully: {metadata.id}")
            return metadata

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in social metadata generation: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating social metadata: {e}")
            return None

    def enrich_article_with_research(
        self,
        article_content: str,
        article_title: str,
        article_id: Optional[str] = None,
    ) -> Optional[EnrichedArticle]:
        """
        Enrichit un article avec recherche et contexte supplémentaire.

        Ajoute:
        - Contexte historique pertinent
        - Statistiques et données clés
        - Perspectives régionales (notamment Afrique)
        - Tendances et prédictions futures
        - Acteurs clés impliqués

        Args:
            article_content: Contenu de l'article original
            article_title: Titre de l'article
            article_id: ID de l'article (optionnel)

        Returns:
            EnrichedArticle avec contexte supplémentaire, ou None si erreur
        """
        if not self.model:
            logger.error("Gemini model not configured — GEMINI_API_KEY missing or invalid")
            return None

        prompt = ARTICLE_ENRICHMENT_PROMPT.format(
            title=article_title,
            content=article_content[:5000],
        )

        try:
            logger.info(f"Enriching article with research: {article_title}")
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            # Valider la réponse
            required_keys = ['enriched_content', 'added_statistics', 'historical_context',
                           'regional_impact', 'key_actors', 'future_implications']
            if not all(k in result for k in required_keys):
                logger.error(f"Invalid response format for article enrichment: missing keys")
                return None

            enriched = EnrichedArticle(
                id=self._generate_id(),
                original_article_id=article_id or self._generate_id(),
                enriched_content=result.get('enriched_content', ''),
                added_statistics=result.get('added_statistics', []),
                historical_context=result.get('historical_context', ''),
                regional_impact=result.get('regional_impact', {}),
                key_actors=result.get('key_actors', []),
                future_implications=result.get('future_implications', ''),
            )

            logger.info(f"Article enriched successfully: {enriched.id}")
            return enriched

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in article enrichment: {e}")
            return None
        except Exception as e:
            logger.error(f"Error enriching article: {e}")
            return None

    def get_youtube_script_by_article(self, article_id: str) -> Optional[Dict]:
        """
        Récupère les données d'un script YouTube pour un article.

        Args:
            article_id: ID de l'article

        Returns:
            Dict avec le script YouTube, ou None
        """
        # Note: Implémentation simplifiée - dans une vraie app,
        # il faudrait stocker les YouTubeScript en BD
        logger.info(f"Retrieving YouTube script for article {article_id}")
        return None

    def get_social_metadata_by_article(self, article_id: str) -> Optional[Dict]:
        """
        Récupère les métadonnées sociales d'un article.

        Args:
            article_id: ID de l'article

        Returns:
            Dict avec les métadonnées, ou None
        """
        # Note: Implémentation simplifiée - dans une vraie app,
        # il faudrait stocker les SocialMetadata en BD
        logger.info(f"Retrieving social metadata for article {article_id}")
        return None

    def get_enriched_article(self, article_id: str) -> Optional[Dict]:
        """
        Récupère un article enrichi.

        Args:
            article_id: ID de l'article

        Returns:
            Dict avec l'article enrichi, ou None
        """
        # Note: Implémentation simplifiée - dans une vraie app,
        # il faudrait stocker les EnrichedArticle en BD
        logger.info(f"Retrieving enriched article {article_id}")
        return None
