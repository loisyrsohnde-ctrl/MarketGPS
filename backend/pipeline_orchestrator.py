"""
MarketGPS Pipeline Orchestrator

Unified orchestrator that connects all news pipeline stages:
1. Scrape raw news from RSS feeds
2. Score articles editorially (source diversity, engagement, importance)
3. Calculate virality scores (viral potential, trends, impact)
4. Update dashboard statistics

This orchestrator:
- Imports and chains existing pipeline components
- Runs stages sequentially with error handling
- Logs results with timestamps
- Stores pipeline metrics in backend/data/news_metrics.json
- Is importable from admin routes for the "Run Pipeline" dashboard button

Usage:
    from backend.pipeline_orchestrator import run_full_pipeline
    result = await run_full_pipeline()

Or individual stages:
    from backend.pipeline_orchestrator import run_scrape, run_score, run_viral_score
    scrape_result = await run_scrape()
    score_result = await run_score()
    viral_result = await run_viral_score()
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# Paths
METRICS_FILE = Path(__file__).parent.parent / "data" / "news_metrics.json"
METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _save_pipeline_metrics(stage: str, result: Dict, elapsed: float, success: bool = True):
    """Save stage results to metrics file."""
    try:
        METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Load existing metrics
        metrics = {}
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, 'r') as f:
                    metrics = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load existing metrics: {e}")

        # Initialize structure
        if "pipeline_runs" not in metrics:
            metrics["pipeline_runs"] = []

        # Add this run
        run_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage,
            "success": success,
            "elapsed_seconds": round(elapsed, 2),
            "result": result
        }

        metrics["pipeline_runs"].append(run_record)
        metrics["pipeline_runs"] = metrics["pipeline_runs"][-50:]  # Keep last 50 runs

        # Update last run timestamp
        metrics["last_run"] = datetime.utcnow().isoformat()

        # Save
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)

    except Exception as e:
        logger.warning(f"Failed to save metrics: {e}")


async def run_scrape(min_interactions: int = 50) -> Dict[str, Any]:
    """
    Stage 1: Scrape news from RSS feeds.

    Returns:
        Dictionary with scraping results
    """
    logger.info("=" * 70)
    logger.info("PIPELINE STAGE 1: RSS Scraping")
    logger.info("=" * 70)

    start_time = time.time()
    result = {
        "stage": "scrape",
        "status": "started",
        "items_total": 0,
        "items_new": 0,
        "sources_total": 0,
        "sources_success": 0,
    }

    try:
        # Import ingest_rss runner
        from pipeline.news.ingest_rss import run_ingest

        logger.info(f"Starting RSS feed ingestion...")
        ingest_result = run_ingest(limit=None)

        result.update({
            "status": "success",
            "items_total": ingest_result.get("items_total", 0),
            "items_new": ingest_result.get("items_new", 0),
            "sources_total": ingest_result.get("sources_total", 0),
            "sources_success": ingest_result.get("sources_success", 0),
            "details": ingest_result
        })

        elapsed = time.time() - start_time
        logger.info(f"✓ Scraping complete: {result['items_new']} new items in {elapsed:.1f}s")

        _save_pipeline_metrics("scrape", result, elapsed, success=True)
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ Scraping failed: {e}", exc_info=True)

        result.update({
            "status": "error",
            "error": str(e)
        })

        _save_pipeline_metrics("scrape", result, elapsed, success=False)
        return result


async def run_score(top_k: int = 30, days_back: int = 3) -> Dict[str, Any]:
    """
    Stage 2: Score articles using editorial intelligence.

    Editorial scoring combines:
    - Source diversity (40%): how many sources cover the topic
    - Verified engagement (25%): interaction counts
    - Topic importance (15%): keywords, entities
    - Freshness (10%): article age
    - Geographic relevance (10%): audience targeting

    Args:
        top_k: Return top K articles
        days_back: Look back this many days

    Returns:
        Dictionary with editorial scoring results
    """
    logger.info("=" * 70)
    logger.info("PIPELINE STAGE 2: Editorial Scoring")
    logger.info("=" * 70)

    start_time = time.time()
    result = {
        "stage": "editorial_score",
        "status": "started",
        "articles_scored": 0,
        "articles_above_threshold": 0,
        "top_k": top_k,
    }

    try:
        from pipeline.news.editorial_scorer import run_editorial_scoring

        db = SQLiteStore()
        logger.info(f"Running editorial scoring on articles from last {days_back} days...")

        scored = run_editorial_scoring(
            get_db_conn=db._get_conn,
            top_k=top_k,
            days_back=days_back
        )

        result.update({
            "status": "success",
            "articles_scored": len(scored),
            "articles_above_threshold": len(scored),
            "sample_scores": [
                {
                    "article_id": s.get("article_id"),
                    "editorial_score": s.get("editorial_score"),
                    "reasons": s.get("reasons", [])[:3]
                }
                for s in scored[:5]
            ]
        })

        elapsed = time.time() - start_time
        logger.info(f"✓ Editorial scoring complete: {len(scored)} articles scored in {elapsed:.1f}s")

        _save_pipeline_metrics("editorial_score", result, elapsed, success=True)
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ Editorial scoring failed: {e}", exc_info=True)

        result.update({
            "status": "error",
            "error": str(e)
        })

        _save_pipeline_metrics("editorial_score", result, elapsed, success=False)
        return result


async def run_viral_score(top_k: int = 40, days_back: int = 3) -> Dict[str, Any]:
    """
    Stage 3: Calculate virality scores using V2 algorithm.

    Viral scoring considers:
    - Social engagement (35%): verified interactions
    - Early trend velocity (20%): how fast it's trending
    - Controversy (15%): debate potential
    - Impact (15%): economic/geopolitical importance
    - Geographic relevance (10%): target audience fit
    - Headline power (5%): title quality

    Args:
        top_k: Return top K articles
        days_back: Look back this many days

    Returns:
        Dictionary with viral scoring results
    """
    logger.info("=" * 70)
    logger.info("PIPELINE STAGE 3: Viral Score V2")
    logger.info("=" * 70)

    start_time = time.time()
    result = {
        "stage": "viral_score",
        "status": "started",
        "articles_scored": 0,
        "articles_in_top_k": 0,
        "top_k": top_k,
    }

    try:
        from pipeline.news.viral_scorer_v2 import run_v2_scoring, ENABLE_VIRAL_FILTER_V2

        if not ENABLE_VIRAL_FILTER_V2:
            logger.warning("Viral Filter V2 is disabled (ENABLE_VIRAL_FILTER_V2=false)")
            result.update({
                "status": "skipped",
                "reason": "ENABLE_VIRAL_FILTER_V2=false"
            })
            return result

        db = SQLiteStore()
        logger.info(f"Running V2 viral scoring on articles from last {days_back} days...")

        scored = run_v2_scoring(
            get_db_conn=db._get_conn,
            top_k=top_k,
            days_back=days_back
        )

        result.update({
            "status": "success",
            "articles_scored": len(scored),
            "articles_in_top_k": len(scored),
            "sample_scores": [
                {
                    "article_id": s.get("article_id"),
                    "viral_score_v2": s.get("viral_score_v2"),
                    "reasons": s.get("reasons", [])[:3],
                    "trend_velocity": s.get("trend_velocity_ratio")
                }
                for s in scored[:5]
            ]
        })

        elapsed = time.time() - start_time
        logger.info(f"✓ Viral scoring complete: {len(scored)} articles scored in {elapsed:.1f}s")

        _save_pipeline_metrics("viral_score", result, elapsed, success=True)
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ Viral scoring failed: {e}", exc_info=True)

        result.update({
            "status": "error",
            "error": str(e)
        })

        _save_pipeline_metrics("viral_score", result, elapsed, success=False)
        return result


async def run_full_pipeline(
    ingest_limit: Optional[int] = None,
    publish_limit: int = 100,
    scrape: bool = True,
    score: bool = True,
    viral_score: bool = True,
) -> Dict[str, Any]:
    """
    Run the complete news pipeline with all stages.

    Pipeline sequence:
    1. Scrape: Ingest from 50+ RSS feeds → raw_items table
    2. Publish: Process raw_items with LLM → news_articles table
    3. Editorial Score: Score by source diversity, engagement, importance
    4. Viral Score: Score by virality potential, trends, impact

    Args:
        ingest_limit: Limit number of sources to fetch (None = all)
        publish_limit: Limit number of articles to publish (default: 100)
        scrape: Run scraping stage (default: True)
        score: Run editorial scoring (default: True)
        viral_score: Run viral scoring (default: True)

    Returns:
        Dictionary with full pipeline results
    """
    logger.info("=" * 70)
    logger.info("MarketGPS News Pipeline - Full Run")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    logger.info("=" * 70)

    pipeline_start = time.time()
    full_result = {
        "pipeline": "full",
        "started_at": datetime.utcnow().isoformat(),
        "stages": {},
        "summary": {
            "total_time": 0,
            "stages_completed": 0,
            "stages_failed": 0,
        }
    }

    # Stage 1: Scrape (ingest + publish are in publish.py's run_full_pipeline)
    if scrape:
        logger.info("\n>>> Starting Ingest + Publish (standard news pipeline)...")
        try:
            from pipeline.news.publish import run_full_pipeline as run_legacy_pipeline

            start = time.time()
            legacy_result = run_legacy_pipeline(
                ingest_limit=ingest_limit,
                publish_limit=publish_limit
            )
            elapsed = time.time() - start

            full_result["stages"]["ingest_publish"] = {
                "status": "success",
                "elapsed": round(elapsed, 2),
                "result": legacy_result
            }
            full_result["summary"]["stages_completed"] += 1

            logger.info(f"✓ Ingest + Publish complete in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"✗ Ingest + Publish failed: {e}", exc_info=True)
            full_result["stages"]["ingest_publish"] = {
                "status": "error",
                "error": str(e)
            }
            full_result["summary"]["stages_failed"] += 1

    # Stage 2: Editorial Scoring
    if score:
        logger.info("\n>>> Starting Editorial Scoring...")
        try:
            score_result = await run_score(top_k=30, days_back=3)
            full_result["stages"]["editorial_score"] = score_result

            if score_result.get("status") == "success":
                full_result["summary"]["stages_completed"] += 1
            else:
                full_result["summary"]["stages_failed"] += 1

        except Exception as e:
            logger.error(f"✗ Editorial Scoring failed: {e}", exc_info=True)
            full_result["stages"]["editorial_score"] = {
                "status": "error",
                "error": str(e)
            }
            full_result["summary"]["stages_failed"] += 1

    # Stage 3: Viral Scoring
    if viral_score:
        logger.info("\n>>> Starting Viral Score V2...")
        try:
            viral_result = await run_viral_score(top_k=40, days_back=3)
            full_result["stages"]["viral_score"] = viral_result

            if viral_result.get("status") == "success":
                full_result["summary"]["stages_completed"] += 1
            else:
                full_result["summary"]["stages_failed"] += 1

        except Exception as e:
            logger.error(f"✗ Viral Scoring failed: {e}", exc_info=True)
            full_result["stages"]["viral_score"] = {
                "status": "error",
                "error": str(e)
            }
            full_result["summary"]["stages_failed"] += 1

    # Finalize
    total_elapsed = time.time() - pipeline_start
    full_result["completed_at"] = datetime.utcnow().isoformat()
    full_result["summary"]["total_time"] = round(total_elapsed, 2)

    logger.info("\n" + "=" * 70)
    logger.info("Pipeline Summary")
    logger.info("=" * 70)
    logger.info(f"Stages completed: {full_result['summary']['stages_completed']}")
    logger.info(f"Stages failed: {full_result['summary']['stages_failed']}")
    logger.info(f"Total time: {total_elapsed:.1f}s")
    logger.info("=" * 70)

    # Save final metrics
    try:
        METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        metrics = {}
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, 'r') as f:
                    metrics = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass

        metrics["last_run"] = datetime.utcnow().isoformat()
        metrics["last_success"] = (full_result["summary"]["stages_failed"] == 0)
        metrics["last_result"] = full_result

        # Keep history of last 10 runs
        history = metrics.get("history", [])
        history.insert(0, {
            "timestamp": datetime.utcnow().isoformat(),
            "success": full_result["summary"]["stages_failed"] == 0,
            "stages_completed": full_result["summary"]["stages_completed"],
            "total_time": full_result["summary"]["total_time"]
        })
        metrics["history"] = history[:10]

        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)

    except Exception as e:
        logger.warning(f"Failed to save final metrics: {e}")

    return full_result


# Convenience aliases for backward compatibility
async def run_news_pipeline(ingest_limit: Optional[int] = None, publish_limit: int = 50) -> Dict[str, Any]:
    """Alias for run_full_pipeline for backward compatibility."""
    return await run_full_pipeline(
        ingest_limit=ingest_limit,
        publish_limit=publish_limit
    )


if __name__ == "__main__":
    import asyncio

    # Test the orchestrator
    result = asyncio.run(run_full_pipeline())
    print(json.dumps(result, indent=2))
