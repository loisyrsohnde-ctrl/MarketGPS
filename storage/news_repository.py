"""
News Repository - Manages news articles and raw news items.
"""
from typing import Optional, List, Dict

from storage.base_repository import BaseRepository
from core.config import get_logger

logger = get_logger(__name__)


class NewsRepository(BaseRepository):
    """Repository for news operations."""

    # Pays francophones prioritaires — Tier 1 : Côte d'Ivoire & Cameroun
    TIER1_PRIORITY_COUNTRIES = ['CI', 'CM']

    # Tier 2 : Autres pays francophones (apparaissent après Tier 1,
    # sauf si leur engagement_score dépasse celui des articles Tier 1)
    TIER2_FRANCOPHONE_COUNTRIES = [
        'SN', 'BJ', 'TG', 'GA', 'CG', 'ML', 'BF', 'NE', 'TD', 'GN', 'RW', 'CD'
    ]

    # Tous les pays francophones combinés (pour rétro-compatibilité)
    FRANCOPHONE_PRIORITY_COUNTRIES = TIER1_PRIORITY_COUNTRIES + TIER2_FRANCOPHONE_COUNTRIES

    # Region to country mapping for news filtering
    REGION_TO_COUNTRIES = {
        "PAN": [],  # Pan-African - no specific country filter
        "WEST": ["NG", "GH", "SN", "CI", "BF", "ML", "NE", "TG", "BJ", "GN"],
        "CENTRAL": ["CM", "GA", "CG", "TD", "CF", "GQ", "CD"],
        "EAST": ["KE", "TZ", "UG", "RW", "ET", "SO", "DJ"],
        "SOUTH": ["ZA", "ZW", "MW", "MZ", "BW", "NA"],
        "NORTH": ["EG", "MA", "DZ", "TN", "SD"]
    }

    def get_news_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None,
        country: Optional[str] = None,
        tag: Optional[str] = None,
        region: Optional[str] = None,
        sort_by: Optional[str] = "date",
        status: str = "published",
        prioritize_francophone: bool = True
    ) -> Dict:
        """
        Get paginated news articles with filtering.

        Args:
            region: Filter by region (PAN, WEST, CENTRAL, EAST, SOUTH, NORTH)
            sort_by: Sort by 'date' (default) or 'relevance' (engagement_score)
            prioritize_francophone: If True (default), francophone countries appear first

        Returns:
            Dict with {data, total, page, page_size, total_pages}
        """
        conditions = ["status = ?"]
        params = [status]

        # Exclude untranslated English content from fallback processing.
        # Allow: AI-processed articles (=1), legacy articles (IS NULL),
        # and French-language articles (already readable, no translation needed).
        conditions.append("(is_ai_processed = 1 OR is_ai_processed IS NULL OR language = 'fr')")

        if query:
            conditions.append("(title LIKE ? OR excerpt LIKE ? OR content_md LIKE ?)")
            pattern = f"%{query}%"
            params.extend([pattern, pattern, pattern])

        # Handle region filter - convert to country list
        if region and region.upper() in self.REGION_TO_COUNTRIES:
            region_countries = self.REGION_TO_COUNTRIES[region.upper()]
            if region_countries:  # If specific countries for this region
                placeholders = ','.join(['?' for _ in region_countries])
                conditions.append(f"country IN ({placeholders})")
                params.extend(region_countries)
            # For PAN (pan-african), no country filter needed

        elif country:
            # Support comma-separated countries for region filtering
            countries = [c.strip() for c in country.split(',') if c.strip()]
            if len(countries) == 1:
                conditions.append("country = ?")
                params.append(countries[0])
            elif len(countries) > 1:
                placeholders = ','.join(['?' for _ in countries])
                conditions.append(f"country IN ({placeholders})")
                params.extend(countries)

        if tag:
            conditions.append("tags_json LIKE ?")
            params.append(f'%"{tag}"%')

        where_clause = " AND ".join(conditions)

        # Count total
        count_sql = f"SELECT COUNT(*) FROM news_articles WHERE {where_clause}"

        # Build ORDER BY clause based on sort_by
        # NOTE: Breaking news and francophone priority are only applied to
        # articles published within the last 48 hours so that older articles
        # don't permanently block the feed.
        if sort_by == "relevance":
            # Sort by engagement score first, then by freshness
            order_clause = """
                ORDER BY
                    CASE WHEN is_breaking_news = 1
                              AND published_at >= datetime('now', '-48 hours')
                         THEN 0 ELSE 1 END,
                    engagement_score DESC,
                    published_at DESC
            """
        elif prioritize_francophone and not country and not region:
            # Priorité : CI & CM d'abord (Tier 1), puis TOUS les francophones
            # (Tier 2), puis le reste. Les francophones passent TOUJOURS avant
            # les anglophones, quel que soit leur engagement_score.
            tier1 = ','.join([f"'{c}'" for c in self.TIER1_PRIORITY_COUNTRIES])
            tier2 = ','.join([f"'{c}'" for c in self.TIER2_FRANCOPHONE_COUNTRIES])
            order_clause = f"""
                ORDER BY
                    CASE WHEN is_breaking_news = 1
                              AND published_at >= datetime('now', '-48 hours')
                         THEN 0 ELSE 1 END,
                    DATE(published_at) DESC,
                    CASE
                        WHEN country IN ({tier1}) THEN 0
                        WHEN country IN ({tier2}) THEN 1
                        ELSE 2
                    END,
                    engagement_score DESC,
                    published_at DESC
            """
        else:
            order_clause = """
                ORDER BY
                    CASE WHEN is_breaking_news = 1
                              AND published_at >= datetime('now', '-48 hours')
                         THEN 0 ELSE 1 END,
                    published_at DESC
            """

        # Get paginated data with new scoring fields
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT id, slug, title, excerpt, tldr_json, tags_json, country,
                   image_url, source_name, source_url, published_at, created_at, view_count,
                   category, sentiment, engagement_score, is_breaking_news, importance_level
            FROM news_articles
            WHERE {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            total = conn.execute(count_sql, params).fetchone()[0]
            rows = conn.execute(data_sql, params + [page_size, offset]).fetchall()

            return {
                "data": [dict(row) for row in rows],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

    def get_news_article_by_slug(self, slug: str) -> Optional[Dict]:
        """Get a single news article by slug."""
        sql = """
            SELECT id, slug, title, excerpt, content_md, tldr_json, tags_json,
                   country, language, image_url, source_name, source_url,
                   canonical_url, published_at, created_at, view_count
            FROM news_articles
            WHERE slug = ? AND status = 'published'
        """

        with self._get_connection() as conn:
            row = conn.execute(sql, (slug,)).fetchone()
            if row:
                # Increment view count
                conn.execute(
                    "UPDATE news_articles SET view_count = view_count + 1 WHERE slug = ?",
                    (slug,)
                )
                return dict(row)
            return None

    def save_news_article_for_user(self, user_id: str, article_id: int) -> bool:
        """Save an article to user's saved list."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO news_user_saves (user_id, article_id)
                    VALUES (?, ?)
                """, (user_id, article_id))
                return True
        except Exception as e:
            logger.error(f"Failed to save article {article_id} for user {user_id}: {e}")
            return False

    def unsave_news_article_for_user(self, user_id: str, article_id: int) -> bool:
        """Remove an article from user's saved list."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    DELETE FROM news_user_saves WHERE user_id = ? AND article_id = ?
                """, (user_id, article_id))
                return True
        except Exception as e:
            logger.error(f"Failed to unsave article {article_id} for user {user_id}: {e}")
            return False

    def get_saved_news_articles(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """Get user's saved articles with pagination."""
        offset = (page - 1) * page_size

        count_sql = """
            SELECT COUNT(*) FROM news_user_saves WHERE user_id = ?
        """

        data_sql = """
            SELECT a.id, a.slug, a.title, a.excerpt, a.tldr_json, a.tags_json,
                   a.country, a.image_url, a.source_name, a.published_at, s.created_at as saved_at
            FROM news_user_saves s
            JOIN news_articles a ON s.article_id = a.id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            total = conn.execute(count_sql, (user_id,)).fetchone()[0]
            rows = conn.execute(data_sql, (user_id, page_size, offset)).fetchall()

            return {
                "data": [dict(row) for row in rows],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

    def is_article_saved_by_user(self, user_id: str, article_id: int) -> bool:
        """Check if an article is saved by a user."""
        with self._get_connection() as conn:
            result = conn.execute("""
                SELECT 1 FROM news_user_saves WHERE user_id = ? AND article_id = ?
            """, (user_id, article_id)).fetchone()
            return result is not None

    def article_exists(self, source_url: str, title: str) -> bool:
        """Check if an article with the same source_url or very similar title already exists.

        This prevents duplicate articles from being inserted when the same
        story is picked up from multiple RSS sources or re-processed.
        """
        try:
            with self._get_connection() as conn:
                # 1. Exact source_url match
                if source_url:
                    row = conn.execute(
                        "SELECT 1 FROM news_articles WHERE source_url = ? LIMIT 1",
                        (source_url,)
                    ).fetchone()
                    if row:
                        return True

                # 2. Exact title match (catches same story from different sources)
                if title:
                    row = conn.execute(
                        "SELECT 1 FROM news_articles WHERE title = ? LIMIT 1",
                        (title,)
                    ).fetchone()
                    if row:
                        return True

                return False
        except Exception as e:
            logger.error(f"Dedup check failed: {e}")
            return False  # Fail open — allow insert on error

    def insert_news_article(self, article: Dict) -> Optional[int]:
        """Insert a new article. Returns the article ID, or None if duplicate."""
        # Deduplication check before insert
        source_url = article.get("source_url", "")
        title = article.get("title", "")
        if self.article_exists(source_url, title):
            logger.info(f"⏩ Duplicate skipped: {title[:60]}...")
            return None

        sql = """
            INSERT INTO news_articles (
                slug, raw_item_id, title, excerpt, content_md, tldr_json,
                tags_json, country, language, image_url, source_name,
                source_url, canonical_url, published_at, status,
                category, sentiment, is_ai_processed,
                engagement_score, is_breaking_news, importance_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (
                    article.get("slug"),
                    article.get("raw_item_id"),
                    article.get("title"),
                    article.get("excerpt"),
                    article.get("content_md"),
                    article.get("tldr_json"),
                    article.get("tags_json"),
                    article.get("country"),
                    article.get("language", "fr"),
                    article.get("image_url"),
                    article.get("source_name"),
                    article.get("source_url"),
                    article.get("canonical_url"),
                    article.get("published_at"),
                    article.get("status", "published"),
                    article.get("category"),
                    article.get("sentiment", "neutral"),
                    1 if article.get("is_ai_processed") else 0,
                    article.get("engagement_score", 0.0),
                    1 if article.get("is_breaking_news") else 0,
                    article.get("importance_level", "normal")
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to insert article: {e}")
            return None

    def insert_news_raw_item(self, item: Dict) -> Optional[int]:
        """Insert a raw news item. Returns the item ID, or None if duplicate."""
        sql = """
            INSERT OR IGNORE INTO news_raw_items (
                source_id, url, title, published_at, raw_payload, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?)
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (
                    item.get("source_id"),
                    item.get("url"),
                    item.get("title"),
                    item.get("published_at"),
                    item.get("raw_payload"),
                    item.get("content_hash")
                ))
                if cursor.rowcount > 0:
                    return cursor.lastrowid
                return None  # Duplicate
        except Exception as e:
            logger.error(f"Failed to insert raw item: {e}")
            return None

    def get_unprocessed_raw_items(self, limit: int = 50) -> List[Dict]:
        """Get raw items that haven't been processed yet.
        Priority: French sources first, then francophone countries, then rest."""
        sql = """
            SELECT r.*, s.name as source_name, s.country as source_country,
                   s.language as source_language, s.trust_score as source_trust_score
            FROM news_raw_items r
            JOIN news_sources s ON r.source_id = s.id
            WHERE r.processed = 0 AND r.process_error IS NULL
            ORDER BY
                CASE WHEN s.language = 'fr' THEN 0 ELSE 1 END,
                CASE WHEN s.country IN ('CI','CM','SN','BJ','BF','TG','GA','ML','NE','GN','TD') THEN 0 ELSE 1 END,
                r.fetched_at DESC
            LIMIT ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def mark_raw_item_processed(self, item_id: int, error: Optional[str] = None) -> bool:
        """Mark a raw item as processed or failed."""
        try:
            with self._get_connection() as conn:
                if error:
                    conn.execute("""
                        UPDATE news_raw_items SET process_error = ? WHERE id = ?
                    """, (error, item_id))
                else:
                    conn.execute("""
                        UPDATE news_raw_items SET processed = 1 WHERE id = ?
                    """, (item_id,))
                return True
        except Exception as e:
            logger.error(f"Failed to mark raw item {item_id}: {e}")
            return False

    def get_news_sources(self, enabled_only: bool = True) -> List[Dict]:
        """Get all news sources."""
        conditions = ["1=1"]
        if enabled_only:
            conditions.append("enabled = 1")

        sql = f"""
            SELECT * FROM news_sources
            WHERE {' AND '.join(conditions)}
            ORDER BY trust_score DESC, name
        """

        with self._get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

    def upsert_news_source(self, source: Dict) -> Optional[int]:
        """Insert or update a news source."""
        sql = """
            INSERT INTO news_sources (name, url, type, rss_url, country, region, language, tags, trust_score, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                rss_url = excluded.rss_url,
                country = excluded.country,
                region = excluded.region,
                language = excluded.language,
                tags = excluded.tags,
                trust_score = excluded.trust_score,
                enabled = excluded.enabled,
                updated_at = datetime('now')
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (
                    source.get("name"),
                    source.get("url"),
                    source.get("type", "rss"),
                    source.get("rss_url"),
                    source.get("country"),
                    source.get("region"),
                    source.get("language", "en"),
                    source.get("tags"),
                    source.get("trust_score", 0.7),
                    source.get("enabled", 1)
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to upsert source: {e}")
            return None

    def update_source_fetch_status(
        self,
        source_id: int,
        error: Optional[str] = None
    ) -> bool:
        """Update source's last fetch timestamp and error status."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE news_sources SET
                        last_fetched_at = datetime('now'),
                        fetch_error = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (error, source_id))
                return True
        except Exception as e:
            logger.error(f"Failed to update source {source_id}: {e}")
            return False
