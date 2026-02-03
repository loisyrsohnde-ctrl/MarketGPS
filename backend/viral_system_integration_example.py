"""
Exemple d'intégration du système de viralité et scripts vidéo.

Démontre comment utiliser les services de viralité et de génération de scripts vidéo.
"""

import asyncio
import logging
from datetime import datetime

from storage.sqlite_store import SQLiteStore
from services.virality_service import ViralityService
from services.video_script_service import VideoScriptService
from services.interaction_estimator import InteractionEstimator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_virality_analysis():
    """Exemple d'analyse de viralité."""
    print("\n" + "=" * 80)
    print("EXEMPLE 1: Analyse de Viralité")
    print("=" * 80)

    db = SQLiteStore()
    virality_svc = ViralityService(db_conn=db._get_conn)

    # Récupérer les statistiques des sources
    print("\n1. Statistiques des sources (derniers 30 jours):")
    source_stats = virality_svc.calculate_source_stats(days=30)

    for source_name, stats in list(source_stats.items())[:5]:
        print(f"\n  Source: {source_name}")
        print(f"    Région: {stats.region}")
        print(f"    Langue: {stats.language}")
        print(f"    Articles: {stats.total_articles}")
        print(f"    Avg interactions: {stats.avg_interactions:.1f}")
        print(f"    Median interactions: {stats.median_interactions:.1f}")

    # Récupérer les articles viraux
    print("\n2. Articles viraux (derniers 7 jours):")
    viral_articles = virality_svc.get_viral_articles(
        limit=10,
        include_francophone_priority=True,
        virality_multiplier=10.0,
        days=7,
    )

    if viral_articles:
        for i, article in enumerate(viral_articles[:5], 1):
            print(f"\n  {i}. {article.title[:60]}...")
            print(f"     Source: {article.source_name}")
            print(f"     Region: {article.region}")
            print(f"     Interactions: {article.interactions}")
            print(f"     Virality Score: {article.virality_score:.2f}x")
            print(f"     Is Viral: {'Yes' if article.is_viral else 'No'}")
    else:
        print("  Aucun article viral trouvé")


async def example_interaction_estimation():
    """Exemple d'estimation d'interactions."""
    print("\n" + "=" * 80)
    print("EXEMPLE 2: Estimation d'Interactions")
    print("=" * 80)

    estimator = InteractionEstimator()

    # Exemples d'articles
    test_articles = [
        {
            "title": "Révélation Exclusive: Scandale Financier de Milliards Découvert",
            "content": "Un scandale impliquant des milliards de francs CFA a été découvert.",
            "source_name": "Jeune Afrique",
            "published_at": datetime(2024, 1, 15, 8, 30),
        },
        {
            "title": "Nouvelle Source d'Énergie Verte en Afrique",
            "content": "Un projet éolien révolutionnaire lancé au Sénégal.",
            "source_name": "Financial Afrik",
            "published_at": datetime(2024, 1, 15, 14, 45),
        },
        {
            "title": "MarketGPS Raises $10M in Funding",
            "content": "African fintech startup receives major investment round.",
            "source_name": "Business Daily Africa",
            "published_at": datetime(2024, 1, 15, 19, 0),
        },
    ]

    print("\nEstimations d'interactions:")
    for article in test_articles:
        estimated = estimator.estimate_interactions(
            title=article["title"],
            content=article["content"],
            source_name=article["source_name"],
            published_at=article["published_at"],
        )

        is_prime_time = estimator._is_prime_time(article["published_at"])
        viral_mult = estimator._count_viral_keywords(
            article["title"], article["content"]
        )

        print(f"\n  Article: {article['title'][:50]}...")
        print(f"    Source: {article['source_name']}")
        print(f"    Hour: {article['published_at'].hour}h (Prime time: {is_prime_time})")
        print(f"    Viral keywords multiplier: {viral_mult:.1f}x")
        print(f"    Estimated interactions: {estimated}")


async def example_video_script_generation():
    """Exemple de génération de scripts vidéo."""
    print("\n" + "=" * 80)
    print("EXEMPLE 3: Génération de Scripts Vidéo")
    print("=" * 80)

    db = SQLiteStore()
    video_svc = VideoScriptService(get_db_conn=db._get_conn)

    if not video_svc.model:
        print("⚠️  Gemini API not configured")
        print("   Pour activer: définir GEMINI_API_KEY ou GOOGLE_API_KEY")
        return

    # Récupérer un article
    conn = db._get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, summary, source_name, published_at
        FROM news_articles
        WHERE summary IS NOT NULL
        LIMIT 1
    """)

    article = cursor.fetchone()
    conn.close()

    if not article:
        print("Aucun article trouvé avec summary")
        return

    article_id, title, content, source, published_at = article

    print(f"\nGénération d'un script pour:")
    print(f"  Titre: {title}")
    print(f"  Source: {source}")

    # Générer le script
    script = await video_svc.generate_script(
        article_id=article_id,
        title=title,
        content=content or "",
        source=source,
        date=published_at or "",
    )

    if script:
        print(f"\n✓ Script généré avec succès!")
        print(f"  ID: {script.id}")
        print(f"  Accroche: {script.hook}")
        print(f"  Mots: {script.word_count}")
        print(f"  Durée estimée: {script.estimated_duration_seconds}s")
        print(f"  Statut: {script.status}")
        print(f"\n  Faits clés:")
        for fact in script.key_facts[:3]:
            print(f"    - {fact}")
        print(f"\n  Début du script:")
        print(f"    {script.script_text[:200]}...")
    else:
        print("✗ Erreur lors de la génération du script")


async def example_auto_process_viral():
    """Exemple de traitement automatique des articles viraux."""
    print("\n" + "=" * 80)
    print("EXEMPLE 4: Traitement Automatique")
    print("=" * 80)

    db = SQLiteStore()
    virality_svc = ViralityService(db_conn=db._get_conn)
    video_svc = VideoScriptService(get_db_conn=db._get_conn)

    if not video_svc.model:
        print("⚠️  Gemini API not configured")
        return

    # Récupérer les articles viraux
    print("\nRécupération des top articles viraux...")
    viral_articles = virality_svc.get_viral_articles(
        limit=3,
        include_francophone_priority=True,
        virality_multiplier=10.0,
        days=7,
    )

    print(f"Trouvé {len(viral_articles)} articles viraux")

    # Générer les scripts
    print("\nGénération des scripts...")
    for i, article in enumerate(viral_articles, 1):
        print(f"\n  [{i}/{len(viral_articles)}] {article.title[:50]}...")

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

        script = await video_svc.generate_script(
            article_id=article_id,
            title=title,
            content=content or "",
            source=source,
            date=published_at or "",
        )

        if script:
            print(f"    ✓ Script généré: {script.word_count} mots")
        else:
            print(f"    ✗ Erreur génération")


async def main():
    """Exécute tous les exemples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 16 + "SYSTÈME DE VIRALITÉ ET SCRIPTS VIDÉO" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # Exemple 1: Analyse de viralité
        await example_virality_analysis()

        # Exemple 2: Estimation d'interactions
        await example_interaction_estimation()

        # Exemple 3: Génération de scripts vidéo
        await example_video_script_generation()

        # Exemple 4: Auto-process (nécessite Gemini)
        await example_auto_process_viral()

        print("\n" + "=" * 80)
        print("✓ Exemples complétés")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Error in examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
