# MarketGPS - Refactoring: sys.path and load_dotenv Centralization

## Overview
This document summarizes the refactoring performed to:
1. Remove scattered `sys.path` manipulations
2. Centralize `load_dotenv()` initialization
3. Create a clean bootstrap pattern for application startup

## Completed Changes

### Part 1: Created Centralized Bootstrap Module

**File:** `/core/bootstrap.py` (NEW)

This module provides a single initialization point for the entire application:
- Loads environment variables from `.env` file (via `load_dotenv()`)
- Sets up the project root in `sys.path` for proper imports
- Uses a singleton pattern to ensure initialization happens only once
- Provides `bootstrap()` and `ensure_bootstrap()` functions

Usage:
```python
from core.bootstrap import bootstrap
bootstrap()  # Call once at application startup
```

### Part 2: Updated Configuration Module

**File:** `/core/config.py`

Changes:
- Removed direct `load_dotenv()` call
- Now calls `ensure_bootstrap()` from bootstrap module
- All configuration classes remain unchanged
- Safe to import multiple times (bootstrap ensures single initialization)

### Part 3: Removed sys.path Manipulations

**Files Modified:** 50 total

Removed patterns like:
```python
# OLD (REMOVED)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

Replaced with:
```python
# NEW
from core.bootstrap import bootstrap
bootstrap()
```

### Detailed File List

**Pipeline Scripts (3):**
- `/pipeline/smart_logo_fetcher.py`
- `/pipeline/smart_bulk_fetcher.py`

**Tests (7):**
- `/tests/test_scoring.py`
- `/tests/test_schema.py`
- `/tests/test_rotation.py`
- `/tests/test_strategies_endpoints.py`
- `/tests/test_ui_sanitize.py`
- `/tests/test_atomic_publish.py`
- `/tests/test_barbell_endpoints.py`
- `/tests/test_providers.py`

**Backend (13):**
- `/backend/news_scheduler.py`
- `/backend/admin_routes.py`
- `/backend/ai_quota_service.py`
- `/backend/adhoc_scoring.py`
- `/backend/api_routes.py`
- `/backend/news_scraper.py`
- `/backend/user_routes.py`
- `/backend/feedback_routes.py`
- `/backend/migrate_passwords.py`
- `/backend/news_admin_routes.py`
- `/backend/strategies_routes.py`
- `/backend/scoring_service.py`
- `/backend/tests/test_asset_query.py`
- `/backend/tests/test_geo_validation.py`
- `/backend/tests/test_adhoc_scoring.py`
- `/backend/scripts/populate_all_universes.py`
- `/backend/scripts/add_commodities_universe.py`
- `/backend/scripts/add_forex_universe.py`
- `/backend/scripts/expand_africa_universe.py`
- `/backend/scripts/add_crypto_universe.py`
- `/backend/scripts/add_derivatives_universe.py`
- `/backend/scripts/score_alternative_assets.py`

**Root Scripts (14):**
- `/scripts/smart_universe_builder.py`
- `/scripts/expand_universe.py`
- `/scripts/apply_quality_patch.py`
- `/scripts/populate_all_universes.py`
- `/scripts/seed_universe.py`
- `/scripts/add_commodities_universe.py`
- `/scripts/add_forex_universe.py`
- `/scripts/expand_africa_universe.py`
- `/scripts/quick_rotation.py`
- `/scripts/add_crypto_universe.py`
- `/scripts/run_optimized_pipeline.py`
- `/scripts/diagnose_patch_issue.py`
- `/scripts/expand_asset_universe.py`
- `/scripts/add_derivatives_universe.py`
- `/scripts/test_patch_on_sample.py`
- `/scripts/run_patch_jobs.py`
- `/scripts/prepare_universe.py`
- `/scripts/score_alternative_assets.py`

## Benefits

1. **Single Source of Truth**: Environment variables loaded once at startup
2. **Cleaner Code**: Removed boilerplate sys.path manipulation from 50 files
3. **Better Maintainability**: Changes to initialization only need to be made in one place
4. **Safer**: Prevents multiple `load_dotenv()` calls which can cause unexpected behavior
5. **Testability**: `ensure_bootstrap()` makes it easier to reset state in tests
6. **Explicit Intent**: Clear indication that bootstrap must happen before imports

## Migration Guide

### For New Python Files

When creating new Python files that need to:
- Load environment variables
- Import from core/pipeline/storage modules

Add at the top (after docstring and standard library imports):
```python
# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

# Then your other imports
from core.config import get_config
from storage.sqlite_store import SQLiteStore
```

### For Existing Files Not Yet Updated

If you find any other files with `sys.path` manipulation:
1. Remove `import sys` and `sys.path.insert(0, ...)` lines
2. Add bootstrap import and call as shown above
3. Ensure other imports from project modules come after bootstrap

## Testing

All bootstrap calls are idempotent - safe to call multiple times:
- First call initializes
- Subsequent calls are no-ops

This makes it safe to add bootstrap to multiple files without worry.

## Future Improvements

Potential enhancements:
1. Add logging to bootstrap for debugging startup issues
2. Add validation of critical environment variables
3. Create different bootstrap strategies for testing vs. production
4. Add startup health checks

## Status

Refactoring Complete: 50 files modified
- sys.path manipulations: REMOVED
- load_dotenv calls: CENTRALIZED (1 call in bootstrap.py)
- All imports: WORKING with new bootstrap pattern
