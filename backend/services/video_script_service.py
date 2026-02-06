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
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import uuid
import os

logger = logging.getLogger(__name__)

# Template Gemini pour la génération de scripts
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
