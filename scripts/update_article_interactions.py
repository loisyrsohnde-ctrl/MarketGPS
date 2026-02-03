#!/usr/bin/env python3
"""
Script pour mettre à jour les interactions de tous les articles existants.

Ce script:
1. Récupère tous les articles avec 0 interactions
2. Estime les interactions basées sur la source, catégorie, pays, etc.
3. Met à jour la base de données avec les nouvelles valeurs

Usage:
    python scripts/update_article_interactions.py [--limit N] [--dry-run]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.bootstrap import bootstrap
bootstrap()

from datetime import datetime
from core.config import get_logger
from storage.news_repository import NewsRepository
from pipeline.news.interactions_fetcher import InteractionsFetcher

logger = get_logger(__name__)


def ensure_columns_exist(conn):
    """S'assurer que TOUTES les colonnes nécessaires existent pour l'admin dashboard."""
    # Vérifier les colonnes existantes
    columns = conn.execute("PRAGMA table_info(news_articles)").fetchall()
    column_names = [c[1] for c in columns]  # c[1] est le nom de la colonne

    logger.info(f"Existing columns: {column_names}")

    # Colonnes requises par le frontend admin (admin.html)
    columns_to_add = []

    # Colonnes d'interactions principales (utilisées par le dashboard)
    if "total_interactions" not in column_names:
        columns_to_add.append(("total_interactions", "INTEGER DEFAULT 0"))
    if "likes" not in column_names:
        columns_to_add.append(("likes", "INTEGER DEFAULT 0"))
    if "comments" not in column_names:
        columns_to_add.append(("comments", "INTEGER DEFAULT 0"))
    if "shares" not in column_names:
        columns_to_add.append(("shares", "INTEGER DEFAULT 0"))

    # Colonnes d'estimation (pour garder les détails)
    if "estimated_views" not in column_names:
        columns_to_add.append(("estimated_views", "INTEGER DEFAULT 0"))
    if "estimated_shares" not in column_names:
        columns_to_add.append(("estimated_shares", "INTEGER DEFAULT 0"))
    if "estimated_likes" not in column_names:
        columns_to_add.append(("estimated_likes", "INTEGER DEFAULT 0"))
    if "estimated_comments" not in column_names:
        columns_to_add.append(("estimated_comments", "INTEGER DEFAULT 0"))

    # Colonnes de scoring
    if "engagement_score" not in column_names:
        columns_to_add.append(("engagement_score", "REAL DEFAULT 0.0"))
    if "importance_level" not in column_names:
        columns_to_add.append(("importance_level", "TEXT DEFAULT 'LOW'"))
    if "is_breaking_news" not in column_names:
        columns_to_add.append(("is_breaking_news", "INTEGER DEFAULT 0"))
    if "virality_score" not in column_names:
        columns_to_add.append(("virality_score", "REAL DEFAULT 0.0"))
    if "interactions_source" not in column_names:
        columns_to_add.append(("interactions_source", "TEXT DEFAULT 'estimated'"))
    if "interactions_updated_at" not in column_names:
        columns_to_add.append(("interactions_updated_at", "TEXT"))

    # Colonnes admin
    if "status" not in column_names:
        columns_to_add.append(("status", "TEXT DEFAULT 'pending'"))
    if "published_to_app" not in column_names:
        columns_to_add.append(("published_to_app", "INTEGER DEFAULT 0"))
    if "published_to_app_at" not in column_names:
        columns_to_add.append(("published_to_app_at", "TEXT"))
    if "scraped_at" not in column_names:
        columns_to_add.append(("scraped_at", "TEXT"))

    for col_name, col_def in columns_to_add:
        try:
            conn.execute(f"ALTER TABLE news_articles ADD COLUMN {col_name} {col_def}")
            logger.info(f"✅ Added column: {col_name}")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add column {col_name}: {e}")

    # Créer les index si nécessaire
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_total_interactions ON news_articles(total_interactions DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_status ON news_articles(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_published ON news_articles(published_to_app)")
    except Exception as e:
        logger.warning(f"Could not create indexes: {e}")


def update_all_articles(limit: int = None, dry_run: bool = False):
    """
    Met à jour les interactions de tous les articles.

    Args:
        limit: Nombre maximum d'articles à traiter (None = tous)
        dry_run: Si True, ne fait pas les modifications
    """
    repo = NewsRepository()
    fetcher = InteractionsFetcher()

    with repo._get_connection() as conn:
        # S'assurer que les colonnes existent
        ensure_columns_exist(conn)

        # Récupérer tous les articles
        query = """
            SELECT
                id,
                title,
                source_name,
                source_url,
                published_at,
                category,
                country,
                language,
                COALESCE(total_interactions, 0) as current_interactions
            FROM news_articles
            ORDER BY published_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        articles = conn.execute(query).fetchall()

        logger.info(f"📰 Found {len(articles)} articles to update")

        updated = 0
        errors = 0

        for article in articles:
            article_id = article[0]
            title = article[1]
            source_name = article[2]
            source_url = article[3]
            published_at = article[4]
            category = article[5] or "default"
            country = article[6] or "default"
            language = article[7] or "en"
            current_interactions = article[8] or 0

            try:
                # Parse published_at
                if isinstance(published_at, str):
                    try:
                        published_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    except Exception:
                        published_dt = datetime.utcnow()
                else:
                    published_dt = published_at or datetime.utcnow()

                # Estimer les interactions
                metrics = fetcher.get_interactions(
                    url=source_url or "",
                    source_name=source_name or "Unknown",
                    title=title or "",
                    published_at=published_dt,
                    category=category,
                    country=country,
                    language=language
                )

                # Calculer les valeurs
                total_interactions = metrics.total_interactions
                likes = metrics.likes
                comments = metrics.comments
                shares = metrics.shares
                views = metrics.views

                # Score d'engagement (0-1)
                engagement_score = min(1.0, metrics.virality_score / 10)

                # Déterminer l'importance
                if metrics.virality_score >= 5 or total_interactions >= 500:
                    importance_level = "HIGH"
                elif metrics.virality_score >= 2 or total_interactions >= 100:
                    importance_level = "MEDIUM"
                else:
                    importance_level = "LOW"

                is_viral = 1 if metrics.is_viral else 0

                if dry_run:
                    logger.info(
                        f"[DRY-RUN] {title[:50]}... | "
                        f"👍{likes} 💬{comments} 🔄{shares} = {total_interactions} | "
                        f"Virality: {metrics.virality_score:.1f}x | "
                        f"Importance: {importance_level}"
                    )
                else:
                    # Mettre à jour dans la base avec TOUTES les colonnes
                    conn.execute("""
                        UPDATE news_articles
                        SET
                            total_interactions = ?,
                            likes = ?,
                            comments = ?,
                            shares = ?,
                            estimated_views = ?,
                            estimated_likes = ?,
                            estimated_comments = ?,
                            estimated_shares = ?,
                            engagement_score = ?,
                            importance_level = ?,
                            is_breaking_news = ?,
                            virality_score = ?,
                            interactions_source = 'estimated',
                            interactions_updated_at = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        total_interactions,
                        likes,
                        comments,
                        shares,
                        views,
                        likes,
                        comments,
                        shares,
                        engagement_score,
                        importance_level,
                        is_viral,
                        metrics.virality_score,
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat(),
                        article_id
                    ))

                    if updated % 50 == 0 and updated > 0:
                        logger.info(f"✅ Updated {updated} articles...")

                updated += 1

            except Exception as e:
                logger.error(f"❌ Error updating article {article_id}: {e}")
                errors += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Updated: {updated} articles")
    logger.info(f"❌ Errors: {errors}")
    logger.info(f"{'='*50}")

    return updated, errors


def show_stats():
    """Affiche les statistiques des interactions actuelles."""
    repo = NewsRepository()

    with repo._get_connection() as conn:
        # D'abord s'assurer que les colonnes existent
        ensure_columns_exist(conn)

        stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN COALESCE(total_interactions, 0) > 0 THEN 1 ELSE 0 END) as with_interactions,
                SUM(CASE WHEN COALESCE(total_interactions, 0) >= 100 THEN 1 ELSE 0 END) as trending,
                SUM(CASE WHEN importance_level = 'HIGH' THEN 1 ELSE 0 END) as high_importance,
                SUM(CASE WHEN importance_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_importance,
                SUM(CASE WHEN published_to_app = 1 THEN 1 ELSE 0 END) as published,
                SUM(CASE WHEN status = 'pending' OR status IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(COALESCE(total_interactions, 0)) as avg_interactions,
                MAX(COALESCE(total_interactions, 0)) as max_interactions
            FROM news_articles
        """).fetchone()

    print("\n📊 STATISTIQUES ACTUELLES")
    print("="*50)
    print(f"Total articles: {stats[0]}")
    print(f"Avec interactions > 0: {stats[1] or 0}")
    print(f"Trending (100+): {stats[2] or 0}")
    print(f"Haute importance: {stats[3] or 0}")
    print(f"Importance moyenne: {stats[4] or 0}")
    print(f"Publiés: {stats[5] or 0}")
    print(f"En attente: {stats[6] or 0}")
    print(f"Interactions moyennes: {stats[7]:.0f}" if stats[7] else "Interactions moyennes: 0")
    print(f"Interactions max: {stats[8] or 0}")
    print("="*50)


def main():
    parser = argparse.ArgumentParser(
        description="Met à jour les interactions des articles de news"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Nombre maximum d'articles à traiter"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Simuler sans modifier la base"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Afficher uniquement les statistiques"
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    print("\n🔄 MISE À JOUR DES INTERACTIONS")
    print("="*50)

    if args.dry_run:
        print("⚠️  Mode DRY-RUN: aucune modification ne sera faite")

    print(f"Limite: {args.limit if args.limit else 'Tous les articles'}")
    print("="*50 + "\n")

    # Afficher stats avant
    print("📊 Avant mise à jour:")
    show_stats()

    # Exécuter la mise à jour
    updated, errors = update_all_articles(
        limit=args.limit,
        dry_run=args.dry_run
    )

    if not args.dry_run:
        # Afficher stats après
        print("\n📊 Après mise à jour:")
        show_stats()


if __name__ == "__main__":
    main()
