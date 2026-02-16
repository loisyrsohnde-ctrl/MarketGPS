#!/usr/bin/env python3
"""
Example usage of the Francophone Filtering Service.

This script demonstrates:
1. Initializing the filter service
2. Getting daily TOP 20 articles
3. Viewing source metrics
4. Marking articles as featured
5. Recalculating scores
6. Querying historical data
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.francophone_filter_service import FrancophonicFilterService
from storage.sqlite_store import SQLiteStore


def get_db_connection():
    """Get database connection."""
    db = SQLiteStore()
    return db._get_conn


def example_1_basic_top20():
    """Example 1: Get today's TOP 20 articles."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Get Today's TOP 20 Francophone Articles")
    print("=" * 80)

    filter_svc = FrancophonicFilterService(db_conn=get_db_connection)

    articles = filter_svc.get_daily_top_20(days=1)

    if not articles:
        print("\nNo articles found for today.")
        return

    print(f"\nFound {len(articles)} TOP 20 articles for today:")
    print()

    for article in articles:
        print(f"#{article.rank:2d} | {article.title[:60]:<60} | Score: {article.francophone_relevance_score:5.1f}")
        print(f"      Source: {article.source_name} ({article.country}) | Interactions: {article.total_interactions}")
        print(f"      Featured: {article.is_featured} | Recency: {article.recency_score:.0f} | Region: {article.region_score:.0f}")
        print()


def example_2_source_metrics():
    """Example 2: View source metrics and qualification rules."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Source Metrics & 2x Median Threshold")
    print("=" * 80)

    filter_svc = FrancophonicFilterService(db_conn=get_db_connection)

    metrics = filter_svc.get_source_metrics_report(days=30)

    if not metrics:
        print("\nNo source metrics available.")
        return

    print(f"\nAnalyzed {len(metrics)} sources over last 30 days:")
    print()
    print(f"{'Source':<25} {'Country':<8} {'Articles':<10} {'Median':<10} {'2x Threshold':<15} {'Qualified':<10}")
    print("-" * 90)

    for source_name, stats in sorted(metrics.items(), key=lambda x: x[1].median_interactions, reverse=True):
        threshold = stats.median_interactions * 2
        print(
            f"{source_name:<25} {stats.country:<8} {stats.total_articles:<10} "
            f"{stats.median_interactions:>8.0f} {threshold:>13.0f} {stats.articles_above_2x_median:>9}"
        )

    print()
    print("Key insight:")
    print("- 'Median' = middle value of all interactions for this source")
    print("- '2x Threshold' = articles must exceed this to qualify (unless featured)")
    print("- 'Qualified' = articles that meet the threshold in the analyzed period")


def example_3_scoring_breakdown():
    """Example 3: Detailed scoring breakdown for one article."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Detailed Scoring Breakdown")
    print("=" * 80)

    filter_svc = FrancophonicFilterService(db_conn=get_db_connection)

    articles = filter_svc.get_daily_top_20(days=1)

    if not articles:
        print("\nNo articles found.")
        return

    # Show top article breakdown
    article = articles[0]

    print(f"\nArticle: {article.title}")
    print(f"Source: {article.source_name} ({article.country}) | Language: {article.language}")
    print(f"Interactions: {article.total_interactions} | Published: {article.published_at}")
    print()

    print("Scoring Components:")
    print("-" * 50)
    print(f"  Interaction Score:  {article.interaction_score:6.1f}/100  (relative to source median)")
    print(f"  Language Score:     {article.language_score:6.1f}/100  (French = 100, English = 50)")
    print(f"  Region Score:       {article.region_score:6.1f}/100  (Francophone Africa = 100)")
    print(f"  Recency Score:      {article.recency_score:6.1f}/100  (< 1 hour = 100)")
    print(f"  Topic Score:        {article.topic_score:6.1f}/100  (Finance/tech keywords)")
    print("-" * 50)

    # Calculate as shown
    combined = (
        (article.interaction_score * 0.35) +
        (article.language_score * 0.20) +
        (article.region_score * 0.20) +
        (article.recency_score * 0.15) +
        (article.topic_score * 0.10)
    )

    print(f"\nCombined Score Calculation:")
    print(f"  ({article.interaction_score:.1f} × 0.35) = {article.interaction_score * 0.35:.2f}")
    print(f"  ({article.language_score:.1f} × 0.20) = {article.language_score * 0.20:.2f}")
    print(f"  ({article.region_score:.1f} × 0.20) = {article.region_score * 0.20:.2f}")
    print(f"  ({article.recency_score:.1f} × 0.15) = {article.recency_score * 0.15:.2f}")
    print(f"  ({article.topic_score:.1f} × 0.10) = {article.topic_score * 0.10:.2f}")
    print(f"  {'-' * 40}")
    print(f"  Final Score: {combined:.2f}")

    if article.is_featured:
        boosted = combined * 1.5
        print(f"  Featured boost (× 1.5): {boosted:.2f}")

    print(f"\n  Final Relevance Score: {article.francophone_relevance_score:.1f}")
    print(f"  Daily Rank: #{article.rank}/20")


def example_4_mark_featured():
    """Example 4: Mark an article as featured."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Mark Article as Featured")
    print("=" * 80)

    filter_svc = FrancophonicFilterService(db_conn=get_db_connection)

    articles = filter_svc.get_daily_top_20(days=1)

    if not articles:
        print("\nNo articles found.")
        return

    # Example with the second article
    if len(articles) > 1:
        article = articles[1]
    else:
        article = articles[0]

    print(f"\nArticle: {article.title}")
    print(f"Current status - Featured: {article.is_featured}")
    print(f"Current score: {article.francophone_relevance_score:.1f}")

    # Mark as featured
    print(f"\nMarking article #{article.article_id} as featured...")
    success = filter_svc.mark_article_as_featured(article.article_id)

    if success:
        print("✓ Article marked as featured successfully")
        print("\nBenefits of featuring this article:")
        print("  1. Bypasses the 2x median interaction threshold")
        print("  2. Receives 1.5× score boost")
        print("  3. Guaranteed to appear in TOP 20")
        print("\nNote: Run recalculate_and_store_scores() to see the boost reflected.")
    else:
        print("✗ Failed to mark article as featured")


def example_5_recalculate_scores():
    """Example 5: Recalculate all francophone scores."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Recalculate All Francophone Scores")
    print("=" * 80)

    filter_svc = FrancophonicFilterService(db_conn=get_db_connection)

    print("\nThis operation will:")
    print("  1. Analyze all published articles")
    print("  2. Calculate source metrics (median, average)")
    print("  3. Score each article across 5 dimensions")
    print("  4. Update francophone_relevance_score in database")
    print("\nUse cases:")
    print("  - Daily scheduled task")
    print("  - After adding new articles")
    print("  - After adjusting scoring parameters")
    print("\nStarting recalculation...")

    success = filter_svc.calculate_and_store_scores()

    if success:
        print("✓ Francophone scores recalculated successfully")
    else:
        print("✗ Recalculation failed - check logs")


def example_6_query_history():
    """Example 6: Query historical TOP 20 data."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Query Historical Data")
    print("=" * 80)

    conn = get_db_connection()
    cursor = conn.cursor()

    print("\nLast 7 days of TOP 20 selections:")
    print("-" * 80)

    try:
        cursor.execute("""
            SELECT date, COUNT(*) as count, AVG(francophone_relevance_score) as avg_score
            FROM francophone_daily_top20
            GROUP BY date
            ORDER BY date DESC
            LIMIT 7
        """)

        rows = cursor.fetchall()

        if not rows:
            print("No historical data available yet.")
        else:
            print(f"{'Date':<15} {'Articles':<10} {'Avg Score':<15}")
            print("-" * 40)
            for date, count, avg_score in rows:
                print(f"{date:<15} {count:<10} {avg_score:>13.1f}")

    except Exception as e:
        print(f"Note: Historical table may not exist yet. {e}")

    conn.close()

    print("\n\nFeatured articles that appeared in TOP 20:")
    print("-" * 80)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT title, source_name, francophone_relevance_score, COUNT(*) as times_featured
            FROM (
                SELECT na.title, na.source_name, na.francophone_relevance_score,
                       dtp.date
                FROM francophone_daily_top20 dtp
                JOIN news_articles na ON dtp.article_id = na.id
                WHERE na.is_featured = 1
            )
            GROUP BY title
            ORDER BY times_featured DESC
            LIMIT 10
        """)

        rows = cursor.fetchall()

        if not rows:
            print("No featured articles in history.")
        else:
            print(f"{'Title':<50} {'Source':<20} {'Score':<8} {'Times':<8}")
            print("-" * 90)
            for title, source, score, times in rows:
                print(f"{title[:49]:<50} {source:<20} {score:>7.1f} {times:>7}")

    except Exception as e:
        print(f"Note: Featured tracking may not be available. {e}")

    conn.close()


def main():
    """Run all examples."""
    print("\n╔════════════════════════════════════════════════════════════════════════╗")
    print("║     Francophone Article Filtering Service - Usage Examples             ║")
    print("║                    MarketGPS TOP 20 Selection                          ║")
    print("╚════════════════════════════════════════════════════════════════════════╝")

    try:
        # Run examples
        example_1_basic_top20()
        example_2_source_metrics()
        example_3_scoring_breakdown()
        example_4_mark_featured()
        example_5_recalculate_scores()
        example_6_query_history()

        print("\n" + "=" * 80)
        print("All examples completed!")
        print("=" * 80)
        print("\nFor more information, see: FRANCOPHONE_FILTERING.md")
        print()

    except Exception as e:
        print(f"\nError during examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
