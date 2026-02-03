# MarketGPS Storage Module - Repository Pattern Architecture

## Quick Start

Import and use `SQLiteStore` exactly as before:

```python
from storage.sqlite_store import SQLiteStore

# Initialize store
store = SQLiteStore(db_path="/path/to/database.sqlite")

# Use any method - all work as before
assets = store.get_active_assets()
scores = store.get_top_scores(limit=50)
store.upsert_asset(asset)
store.publish_run(run_id, market_scope="US_EU")
```

## Structure

The storage module is organized into specialized repositories, each with a single responsibility:

### Entry Point
- **`sqlite_store.py`** - Main entry point (re-exports SQLiteStore from facade)

### Main Facade
- **`sqlite_store_facade.py`** - SQLiteStore class that delegates to all repositories

### Core Repositories

#### 1. BaseRepository (`base_repository.py`)
Foundation class providing:
- Database connection management
- Schema initialization
- Common constants (MarketScope, VALID_SCOPES)

Used by all other repositories.

#### 2. AssetRepository (`asset_repository.py`)
Manages the asset universe and gating status:

```python
# Create/update assets
store.upsert_asset(asset)
store.bulk_upsert_assets([assets])

# Query assets
store.get_asset(asset_id)
store.get_active_assets()
store.list_assets_paginated(page=1)
store.search_assets(query)

# Asset statistics
store.count_assets()
store.count_by_type()
store.count_by_scope()

# Gating operations
store.upsert_gating(gating)
store.get_gating(asset_id)
store.get_eligible_assets()
```

#### 3. ScoreRepository (`score_repository.py`)
Manages scores, rotation, calibration, watchlist, and job runs:

```python
# Score operations
store.upsert_score(score)
store.get_score(asset_id)
store.get_top_scores()
store.get_latest_score(ticker)

# Rotation and priority
store.upsert_rotation_state(state)
store.get_priority_assets()
store.set_priority_level(asset_ids)

# Calibration
store.get_calibration_params()
store.update_calibration_params(params)

# Watchlist
store.add_watchlist(ticker)
store.list_watchlist()
store.is_in_watchlist(ticker)

# Job runs (atomic publishing)
store.create_job_run(scope, job_type)
store.insert_staging_score(run_id, score)
store.publish_run(run_id, scope)
store.rollback_run(run_id)
```

#### 4. NewsRepository (`news_repository.py`)
Manages news articles, sources, and raw items:

```python
# Articles
store.get_news_articles(page=1, country="CM")
store.get_news_article_by_slug(slug)
store.insert_news_article(article)

# User saved articles
store.save_news_article_for_user(user_id, article_id)
store.get_saved_news_articles(user_id)
store.is_article_saved_by_user(user_id, article_id)

# Raw items (for processing pipeline)
store.insert_news_raw_item(item)
store.get_unprocessed_raw_items()
store.mark_raw_item_processed(item_id)

# Sources
store.get_news_sources()
store.upsert_news_source(source)
store.update_source_fetch_status(source_id)
```

#### 5. UserRepository (`user_repository.py`)
Manages user accounts and profiles:

```python
# Authentication
store.create_user(email, password_hash)
store.get_user_by_email(email)
store.get_user_by_id(user_id)
store.update_last_login(user_id)

# Profiles
store.get_user_profile(user_id)
store.update_user_profile(user_id, display_name, avatar_path, bio)
```

#### 6. SubscriptionRepository (`subscription_repository.py`)
Manages subscriptions and quota:

```python
# Subscriptions
store.get_subscription(user_id)
store.set_subscription(user_id, plan="monthly_9_99")
store.is_pro_user(user_id)

# Quota
store.can_calculate_score(user_id)
store.consume_calculation_quota(user_id, count=1)
store.reset_daily_quotas()
```

#### 7. GeneralRepository (`general_repository.py`)
Manages jobs queue, quotas, settings, and statistics:

```python
# Jobs queue
store.enqueue_job(job_type, payload)
store.fetch_next_job_atomic()
store.mark_job_done(job_id)
store.mark_job_failed(job_id, error)
store.get_pending_jobs_count()
store.get_recent_jobs()

# Daily quota
store.get_today_usage(user_id)
store.can_consume_quota(count, user_id)
store.consume_quota(count, user_id)
store.set_user_tier(user_id, tier, limit)

# Settings
store.get_setting(key)
store.set_setting(key, value)
store.is_pro_mode_enabled()
store.set_pro_mode(enabled)

# Statistics
store.get_stats(market_scope="US_EU")
```

#### 8. ExplorerRepository (`explorer_repository.py`)
Manages search, landing page metrics, and long-term scoring:

```python
# Landing page
store.get_landing_metrics(market_scope="US_EU")

# Search/Explorer
store.search_universe(
    market_scope="AFRICA",
    region="WEST",
    asset_type="EQUITY",
    query="search term"
)
store.get_top_scored_assets()
store.get_asset_types_for_scope()

# Long-term scoring
store.ensure_longterm_schema()
store.upsert_longterm_score(asset_id, lt_score=85.5)
store.get_top_longterm_scores()
```

## Design Principles

### Single Responsibility
Each repository has one clear domain and purpose.

### Composition Over Inheritance
Repositories extend BaseRepository but remain independent.

### Backward Compatibility
All methods remain in SQLiteStore facade - zero API changes.

### Delegation Pattern
SQLiteStore delegates to repositories without adding logic.

## Adding New Features

### Add method to existing repository:

```python
# In score_repository.py
class ScoreRepository(BaseRepository):
    def new_method(self):
        with self._get_connection() as conn:
            # implementation
            pass

# Automatically available in SQLiteStore
store.new_method()  # Works!
```

### Create new repository for new domain:

```python
# Create storage/my_repository.py
from storage.base_repository import BaseRepository

class MyRepository(BaseRepository):
    def my_method(self):
        pass

# Add to sqlite_store_facade.py
def __init__(self, db_path: Optional[str] = None):
    # ... existing code ...
    self._my = MyRepository(self.db_path)

def my_method(self):
    return self._my.my_method()
```

## Testing

Test individual repositories in isolation:

```python
from storage.asset_repository import AssetRepository

repo = AssetRepository(db_path="/test/db.sqlite")
assets = repo.get_active_assets()
```

Or test through the facade:

```python
from storage.sqlite_store import SQLiteStore

store = SQLiteStore(db_path="/test/db.sqlite")
assets = store.get_active_assets()
```

## Performance Considerations

- **Connection pooling**: Each repository uses the same connection manager
- **No overhead**: Delegation adds negligible overhead
- **Same SQL**: All queries remain unchanged from original implementation
- **Scoped transactions**: Job runs use atomic transactions for consistency

## Database Schema

Database schema is initialized automatically by `BaseRepository._init_schema()`.

Run manually if needed:

```python
store.ensure_schema()
store.reset_schema()
store._ensure_news_tables()
store._ensure_strategy_tables()
store.ensure_longterm_schema()
```

## Troubleshooting

### "No module named 'storage...'"
Ensure you're running from project root and storage module is in Python path.

### "database is locked"
SQLiteStore uses WAL mode. Ensure database file is not corrupted:
```bash
sqlite3 your_database.db "VACUUM;"
sqlite3 your_database.db "PRAGMA integrity_check;"
```

### Connection timeout
Default timeout is 30 seconds. Increase if needed:
```python
# Modify BaseRepository._get_connection()
conn = sqlite3.connect(self.db_path, timeout=60)
```

## Documentation

- **`REFACTORING.md`** - Detailed refactoring documentation
- **`README.md`** - This file, overview and usage guide
- **Repository files** - Well-commented method docstrings

## License

Part of MarketGPS project
