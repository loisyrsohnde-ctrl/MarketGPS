"""
Routes API pour les actualités virales et scripts vidéo.

Endpoints:
- GET /viral-news/viral - Articles viraux selon les règles de viralité
- GET /viral-news/source-stats - Statistiques par source
- POST /viral-news/generate-script - Générer un script vidéo
- GET /viral-news/scripts - Liste des scripts générés
- GET /viral-news/scripts/{script_id} - Détail d'un script
- PUT /viral-news/scripts/{script_id} - Modifier un script
- POST /viral-news/scripts/{script_id}/publish-to-news - Publier vers actualités
- POST /viral-news/auto-process - Traitement automatique des articles viraux
"""

import asyncio
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
import logging

from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from backend.security import get_user_id_from_request
from services.virality_service import ViralityService, ViralArticle
from services.video_script_service import VideoScriptService, VideoScript

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/viral-news", tags=["Viral News"])

# Database store
db = SQLiteStore()

# Initialize services
virality_service = None
video_script_service = None


def get_services():
    """Récupère les instances des services."""
    global virality_service, video_script_service

    if not virality_service:
        virality_service = ViralityService(db_conn=db._get_conn)

    if not video_script_service:
        video_script_service = VideoScriptService(get_db_conn=db._get_conn)

    return virality_service, video_script_service


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class SourceStatsResponse(BaseModel):
    """Statistiques d'une source."""
    source_name: str
    region: str
    language: str
    avg_interactions: float
    median_interactions: float
    total_articles: int


class ViralArticleResponse(BaseModel):
    """Article viral."""
    article_id: str
    title: str
    source_name: str
    interactions: int
    virality_score: float
    region: str
    language: str
    published_at: Optional[str]
    url: str


class GenerateScriptRequest(BaseModel):
    """Requête pour générer un script vidéo."""
    article_id: str


class UpdateScriptRequest(BaseModel):
    """Requête pour mettre à jour un script."""
    script_text: Optional[str] = None
    hook: Optional[str] = None
    status: Optional[str] = None


class VideoScriptResponse(BaseModel):
    """Réponse avec un script vidéo."""
    id: str
    article_id: str
    title: str
    hook: str
    script_text: str
    word_count: int
    estimated_duration_seconds: int
    sources_mentioned: List[str]
    key_facts: List[str]
    status: str
    created_at: str
    updated_at: str


class AutoProcessResponse(BaseModel):
    """Réponse du traitement automatique."""
    articles_processed: int
    scripts_generated: int
    scripts: List[VideoScriptResponse]


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/viral", response_model=List[ViralArticleResponse])
async def get_viral_articles(
    limit: int = Query(20, ge=1, le=100, description="Nombre d'articles à retourner"),
    francophone_only: bool = Query(False, description="Inclure seulement les sources francophones"),
    min_virality: float = Query(1.0, ge=0.5, description="Score de viralité minimum"),
    days: int = Query(7, ge=1, le=30, description="Nombre de jours à considérer"),
):
    """
    Récupère les articles viraux selon les règles.

    Règles:
    - Afrique francophone sub-saharienne: inclus si > seuil minimum
    - Autres: inclus si viralité >= 10x moyenne de la source

    Query params:
    - limit: Nombre max d'articles (défaut: 20, max: 100)
    - francophone_only: Si True, seulement les sources francophones
    - min_virality: Score de viralité minimum (défaut: 1.0)
    - days: Nombre de jours à analyser (défaut: 7)

    Returns:
        List[ViralArticleResponse]
    """
    try:
        virality_svc, _ = get_services()

        viral_articles = virality_svc.get_viral_articles(
            limit=limit,
            include_francophone_priority=not francophone_only,
            virality_multiplier=10.0,
            days=days,
        )

        # Filtrer par score minimum
        filtered = [
            a for a in viral_articles
            if a.virality_score >= min_virality
        ]

        # Filtrer par francophone si demandé
        if francophone_only:
            filtered = [a for a in filtered if a.language == 'fr']

        # Convertir en réponse
        return [
            ViralArticleResponse(
                article_id=a.article_id,
                title=a.title,
                source_name=a.source_name,
                interactions=a.interactions,
                virality_score=a.virality_score,
                region=a.region,
                language=a.language,
                published_at=a.published_at,
                url=a.url,
            )
            for a in filtered[:limit]
        ]

    except Exception as e:
        logger.error(f"Error getting viral articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source-stats", response_model=dict)
async def get_source_stats(days: int = Query(30, ge=7, le=90)):
    """
    Récupère les statistiques d'interactions par source.

    Query params:
    - days: Nombre de jours à analyser (défaut: 30)

    Returns:
        Dict avec source_name -> SourceStatsResponse
    """
    try:
        virality_svc, _ = get_services()

        stats = virality_svc.calculate_source_stats(days=days)

        return {
            name: {
                "source_name": s.source_name,
                "region": s.region,
                "language": s.language,
                "avg_interactions": s.avg_interactions,
                "median_interactions": s.median_interactions,
                "total_articles": s.total_articles,
            }
            for name, s in stats.items()
        }

    except Exception as e:
        logger.error(f"Error getting source stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-script", response_model=VideoScriptResponse)
async def generate_video_script(
    request: GenerateScriptRequest,
):
    """
    Génère un script vidéo style Hugo Décrypte pour un article.

    Body:
        - article_id: ID de l'article à transformer en script

    Returns:
        VideoScriptResponse avec le script généré
    """
    try:
        _, video_svc = get_services()

        # Récupérer l'article
        conn = db._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, summary, source_name, published_at
            FROM news_articles
            WHERE id = ?
        """, (request.article_id,))

        article = cursor.fetchone()
        conn.close()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article_id, title, content, source, published_at = article

        # Générer le script
        script = await video_svc.generate_script(
            article_id=article_id,
            title=title,
            content=content or "",
            source=source,
            date=published_at or "",
        )

        if not script:
            raise HTTPException(status_code=500, detail="Failed to generate script")

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scripts", response_model=List[VideoScriptResponse])
async def get_scripts(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Liste les scripts vidéo générés.

    Query params:
    - status: Filtrer par statut ('draft', 'reviewed', 'approved', 'published')
    - limit: Nombre max de scripts (défaut: 20)
    - offset: Offset pour pagination (défaut: 0)

    Returns:
        List[VideoScriptResponse]
    """
    try:
        _, video_svc = get_services()

        scripts = video_svc.get_scripts(status=status, limit=limit, offset=offset)

        return [
            VideoScriptResponse(
                id=s.id,
                article_id=s.article_id,
                title=s.title,
                hook=s.hook,
                script_text=s.script_text,
                word_count=s.word_count,
                estimated_duration_seconds=s.estimated_duration_seconds,
                sources_mentioned=s.sources_mentioned,
                key_facts=s.key_facts,
                status=s.status,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in scripts
        ]

    except Exception as e:
        logger.error(f"Error getting scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scripts/{script_id}", response_model=VideoScriptResponse)
async def get_script(script_id: str):
    """
    Récupère un script spécifique.

    Path params:
    - script_id: ID du script

    Returns:
        VideoScriptResponse
    """
    try:
        _, video_svc = get_services()

        script = video_svc.get_script_by_id(script_id)

        if not script:
            raise HTTPException(status_code=404, detail="Script not found")

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/scripts/{script_id}", response_model=VideoScriptResponse)
async def update_script(
    script_id: str,
    request: UpdateScriptRequest,
):
    """
    Modifie un script (texte ou statut).

    Path params:
    - script_id: ID du script

    Body:
    - script_text: Nouveau texte du script (optionnel)
    - hook: Nouvelle accroche (optionnel)
    - status: Nouveau statut (optionnel)

    Returns:
        VideoScriptResponse mis à jour
    """
    try:
        _, video_svc = get_services()

        success = video_svc.update_script(
            script_id=script_id,
            script_text=request.script_text,
            hook=request.hook,
            status=request.status,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update script")

        # Récupérer le script mis à jour
        script = video_svc.get_script_by_id(script_id)

        if not script:
            raise HTTPException(status_code=404, detail="Script not found after update")

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scripts/{script_id}/publish-to-news", response_model=dict)
async def publish_script_to_news(script_id: str):
    """
    Publie le contenu du script vers la page actualités publique.

    Path params:
    - script_id: ID du script à publier

    Returns:
        Dict avec succès/erreur
    """
    try:
        _, video_svc = get_services()

        success = video_svc.publish_script_to_news(script_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to publish script")

        return {"success": True, "message": f"Script {script_id} published successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-process", response_model=AutoProcessResponse)
async def auto_process_viral(
    top_n: int = Query(5, ge=1, le=20, description="Nombre de top articles à traiter"),
    status_filter: Optional[str] = Query(None, description="Filtrer articles par statut"),
):
    """
    Processus automatique:
    1. Identifie les articles les plus viraux
    2. Génère des scripts pour les top N
    3. Retourne les scripts générés

    Query params:
    - top_n: Nombre de top articles à traiter (défaut: 5)
    - status_filter: Filtrer articles par statut (optionnel)

    Returns:
        AutoProcessResponse avec articles et scripts générés
    """
    try:
        virality_svc, video_svc = get_services()

        # Récupérer les articles viraux
        viral_articles = virality_svc.get_viral_articles(
            limit=top_n,
            include_francophone_priority=True,
            virality_multiplier=10.0,
            days=7,
        )

        if not viral_articles:
            return AutoProcessResponse(
                articles_processed=0,
                scripts_generated=0,
                scripts=[],
            )

        # Générer les scripts
        generated_scripts = []
        articles_processed = len(viral_articles)

        for article in viral_articles:
            # Récupérer le contenu complet de l'article
            conn = db._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, title, summary, source_name, published_at
                FROM news_articles
                WHERE id = ?
            """, (article.article_id,))

            article_row = cursor.fetchone()
            conn.close()

            if not article_row:
                continue

            article_id, title, content, source, published_at = article_row

            # Générer le script
            script = await video_svc.generate_script(
                article_id=article_id,
                title=title,
                content=content or "",
                source=source,
                date=published_at or "",
            )

            if script:
                generated_scripts.append(
                    VideoScriptResponse(
                        id=script.id,
                        article_id=script.article_id,
                        title=script.title,
                        hook=script.hook,
                        script_text=script.script_text,
                        word_count=script.word_count,
                        estimated_duration_seconds=script.estimated_duration_seconds,
                        sources_mentioned=script.sources_mentioned,
                        key_facts=script.key_facts,
                        status=script.status,
                        created_at=script.created_at,
                        updated_at=script.updated_at,
                    )
                )

        return AutoProcessResponse(
            articles_processed=articles_processed,
            scripts_generated=len(generated_scripts),
            scripts=generated_scripts,
        )

    except Exception as e:
        logger.error(f"Error in auto-process: {e}")
        raise HTTPException(status_code=500, detail=str(e))
