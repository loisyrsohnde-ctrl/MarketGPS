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
from datetime import datetime

from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from security import get_user_id_from_request
from services.virality_service import ViralityService, ViralArticle
from services.video_script_service import VideoScriptService, VideoScript
from services.francophone_filter_service import FrancophonicFilterService, FrancophonicArticle

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/viral-news", tags=["Viral News"])

# Database store
db = SQLiteStore()

# Initialize services
virality_service = None
video_script_service = None
francophone_filter_service = None


def get_services():
    """Récupère les instances des services."""
    global virality_service, video_script_service, francophone_filter_service

    if not virality_service:
        virality_service = ViralityService(db_conn=db._get_conn)

    if not video_script_service:
        video_script_service = VideoScriptService(get_db_conn=db._get_conn)

    if not francophone_filter_service:
        francophone_filter_service = FrancophonicFilterService(db_conn=db._get_conn)

    return virality_service, video_script_service, francophone_filter_service


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


class FrancophonicArticleResponse(BaseModel):
    """Article francophone avec score de pertinence."""
    article_id: int
    title: str
    source_name: str
    country: str
    language: str
    total_interactions: int
    published_at: Optional[str]
    url: str

    # Scoring components
    interaction_score: float
    language_score: float
    region_score: float
    recency_score: float
    topic_score: float
    francophone_relevance_score: float

    # Status
    is_featured: bool
    rank: int


class SourceMetricsResponse(BaseModel):
    """Métriques d'une source."""
    source_name: str
    country: str
    language: str
    total_articles: int
    median_interactions: float
    avg_interactions: float
    articles_above_2x_median: int


class Top20Response(BaseModel):
    """Réponse avec le TOP 20 articles francophones."""
    date: str
    articles: List[FrancophonicArticleResponse]
    total_articles_analyzed: int
    articles_qualified: int
    featured_count: int
    avg_relevance_score: float


class MarkFeaturedRequest(BaseModel):
    """Requête pour marquer un article comme vedette."""
    article_id: int
    featured: bool = True


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
            SELECT id, title, content_md, summary, source_name, published_at
            FROM news_articles
            WHERE id = ?
        """, (request.article_id,))

        article = cursor.fetchone()
        conn.close()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article_id, title, content_md, summary, source, published_at = article
        # Use content_md first (full article), fallback to summary
        content = content_md or summary or ""

        if not content.strip():
            raise HTTPException(status_code=400, detail="Article has no content to generate script from")

        # Générer le script (Gemini SDK is synchronous, run in threadpool)
        import asyncio
        script = await asyncio.to_thread(
            video_svc.generate_script_sync,
            article_id=article_id,
            title=title,
            content=content,
            source=source,
            date=published_at or "",
        )

        if not script:
            raise HTTPException(status_code=500, detail="Gemini generation failed — check GEMINI_API_KEY and API quota")

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


# ═══════════════════════════════════════════════════════════════════════════════
# Francophone Strict Filtering Routes (TOP 20 Daily Selection)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/francophone/top20", response_model=Top20Response)
async def get_francophone_top20(
    days: int = Query(1, ge=1, le=7, description="Nombre de jours à analyser"),
):
    """
    Récupère le TOP 20 des articles francophones les plus pertinents.

    Critères de sélection stricte:
    - Langue: Français uniquement
    - Région: Afrique francophone + France, Belgique, Suisse, Canada
    - Interactions: > 2x la médiane de la source
    - Recency: Publié dans les 24-48 dernières heures
    - Pertinence: Basée sur interactions, région, actualité, et thème

    Query params:
    - days: Nombre de jours à analyser (défaut: 1, max: 7)

    Returns:
        Top20Response avec les 20 meilleurs articles et statistiques
    """
    try:
        _, _, filter_svc = get_services()

        # Get top 20 articles
        articles = filter_svc.get_daily_top_20(
            days=days,
            include_featured=True
        )

        if not articles:
            return Top20Response(
                date=datetime.utcnow().strftime("%Y-%m-%d"),
                articles=[],
                total_articles_analyzed=0,
                articles_qualified=0,
                featured_count=0,
                avg_relevance_score=0.0
            )

        # Build response
        article_responses = [
            FrancophonicArticleResponse(
                article_id=a.article_id,
                title=a.title,
                source_name=a.source_name,
                country=a.country,
                language=a.language,
                total_interactions=a.total_interactions,
                published_at=a.published_at,
                url=a.url,
                interaction_score=round(a.interaction_score, 2),
                language_score=round(a.language_score, 2),
                region_score=round(a.region_score, 2),
                recency_score=round(a.recency_score, 2),
                topic_score=round(a.topic_score, 2),
                francophone_relevance_score=round(a.francophone_relevance_score, 2),
                is_featured=a.is_featured,
                rank=a.rank
            )
            for a in articles
        ]

        avg_score = (
            sum(a.francophone_relevance_score for a in articles) / len(articles)
            if articles else 0.0
        )

        featured_count = sum(1 for a in articles if a.is_featured)

        return Top20Response(
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            articles=article_responses,
            total_articles_analyzed=0,  # Will be tracked in logging
            articles_qualified=len(articles),
            featured_count=featured_count,
            avg_relevance_score=round(avg_score, 2)
        )

    except Exception as e:
        logger.error(f"Error getting francophone top 20: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/francophone/source-metrics", response_model=dict)
async def get_francophone_source_metrics(
    days: int = Query(30, ge=7, le=90, description="Nombre de jours à analyser"),
):
    """
    Récupère les métriques de source pour le filtering strict.

    Montre la médiane et la moyenne des interactions par source,
    essentielles pour comprendre les seuils de qualification (2x médiane).

    Query params:
    - days: Nombre de jours à analyser (défaut: 30)

    Returns:
        Dict mapping source_name -> SourceMetricsResponse
    """
    try:
        _, _, filter_svc = get_services()

        metrics = filter_svc.get_source_metrics_report(days=days)

        return {
            name: {
                "source_name": m.source_name,
                "country": m.country,
                "language": m.language,
                "total_articles": m.total_articles,
                "median_interactions": round(m.median_interactions, 2),
                "avg_interactions": round(m.avg_interactions, 2),
                "articles_above_2x_median": m.articles_above_2x_median,
            }
            for name, m in metrics.items()
        }

    except Exception as e:
        logger.error(f"Error getting source metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/francophone/mark-featured", response_model=dict)
async def mark_article_featured(request: MarkFeaturedRequest):
    """
    Marque un article comme vedette (featured).

    Les articles vedettes:
    - Ignorent la règle du seuil 2x médiane
    - Ont un boost de score de 1.5x
    - Apparaissent toujours dans le TOP 20

    Body:
        - article_id: ID de l'article
        - featured: True pour marquer, False pour demarquer (défaut: True)

    Returns:
        Dict avec succès/erreur
    """
    try:
        _, _, filter_svc = get_services()

        if request.featured:
            success = filter_svc.mark_article_as_featured(request.article_id)
            message = f"Article {request.article_id} marked as featured"
        else:
            success = filter_svc.unmark_article_as_featured(request.article_id)
            message = f"Article {request.article_id} unmarked as featured"

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update article")

        return {
            "success": True,
            "message": message,
            "article_id": request.article_id,
            "featured": request.featured
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking article featured: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/francophone/recalculate-scores", response_model=dict)
async def recalculate_francophone_scores():
    """
    Recalcule les scores de pertinence francophone pour tous les articles.

    Cette opération doit être exécutée:
    - Quotidiennement (tâche planifiée)
    - Après l'ajout de nouveaux articles importants
    - Après modification des paramètres de scoring

    Peut prendre quelques secondes selon le nombre d'articles.

    Returns:
        Dict avec statistiques de recalcul
    """
    try:
        _, _, filter_svc = get_services()

        success = filter_svc.calculate_and_store_scores()

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to recalculate francophone scores"
            )

        return {
            "success": True,
            "message": "Francophone relevance scores recalculated",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/viral", response_model=List[ViralArticleResponse])
async def get_viral_articles_strict(
    strict: bool = Query(
        True,
        description="Si True, utilise le filtering strict TOP 20. Si False, utilise les anciennes règles de viralité."
    ),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'articles à retourner"),
    francophone_only: bool = Query(False, description="Inclure seulement les sources francophones"),
    min_virality: float = Query(1.0, ge=0.5, description="Score de viralité minimum"),
    days: int = Query(7, ge=1, le=30, description="Nombre de jours à considérer"),
):
    """
    Endpoint flexible pour les articles viraux.

    Utilise le filtering strict TOP 20 par défaut (strict=True).
    Compatible avec l'ancienne API virale avec strict=False.

    Query params:
    - strict: Utiliser le strict filtering TOP 20 (défaut: True)
    - limit: Nombre max d'articles (défaut: 20)
    - francophone_only: Seulement les sources francophones
    - min_virality: Score minimum (pour mode non-strict)
    - days: Nombre de jours à analyser

    Returns:
        List[ViralArticleResponse]
    """
    try:
        if strict:
            # New strict filtering mode
            _, _, filter_svc = get_services()

            articles = filter_svc.get_daily_top_20(
                days=min(days, 2),  # Cap at 2 days for TOP 20
                include_featured=True
            )

            return [
                ViralArticleResponse(
                    article_id=str(a.article_id),
                    title=a.title,
                    source_name=a.source_name,
                    interactions=a.total_interactions,
                    virality_score=a.francophone_relevance_score / 10.0,
                    region=a.country,
                    language=a.language,
                    published_at=a.published_at,
                    url=a.url,
                )
                for a in articles[:limit]
            ]
        else:
            # Old virality mode (backward compatibility)
            virality_svc, _, _ = get_services()

            viral_articles = virality_svc.get_viral_articles(
                limit=limit,
                include_francophone_priority=not francophone_only,
                virality_multiplier=10.0,
                days=days,
            )

            # Filter by minimum virality
            filtered = [
                a for a in viral_articles
                if a.virality_score >= min_virality
            ]

            # Filter by francophone if requested
            if francophone_only:
                filtered = [a for a in filtered if a.language == 'fr']

            # Convert to response
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
