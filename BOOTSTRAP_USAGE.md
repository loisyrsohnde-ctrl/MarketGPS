# MarketGPS Bootstrap Usage Guide

## Quick Start

When creating a new Python file that needs to:
- Load environment variables
- Import modules from `core/`, `pipeline/`, `storage/`, `auth/`, etc.

Add this at the very top (after the docstring):

```python
"""Module documentation."""

from core.bootstrap import bootstrap
bootstrap()

# Now you can import project modules
from core.config import get_config
from storage.sqlite_store import SQLiteStore
```

## Pattern Examples

### Example 1: Backend Route Handler

```python
"""User authentication endpoints."""

from fastapi import APIRouter, HTTPException

# Bootstrap FIRST
from core.bootstrap import bootstrap
bootstrap()

# Then project imports
from core.config import get_config
from auth.supabase_client import SupabaseClient
from storage.sqlite_store import SQLiteStore

router = APIRouter(prefix="/api/auth")

@router.post("/login")
async def login(email: str, password: str):
    config = get_config()
    # ... rest of implementation
```

### Example 2: Script/CLI Tool

```python
"""Database migration script."""

import argparse
from pathlib import Path

# Bootstrap
from core.bootstrap import bootstrap
bootstrap()

# Project imports
from storage.sqlite_store import SQLiteStore
from core.config import get_config, get_logger

logger = get_logger(__name__)

def main():
    config = get_config()
    store = SQLiteStore(config.storage.sqlite_path)
    # ... migration logic
```

### Example 3: Test File

```python
"""Tests for payment processing."""

import pytest
from unittest.mock import Mock, patch

# Bootstrap
from core.bootstrap import bootstrap
bootstrap()

# Project imports
from providers.stripe_provider import StripeProvider
from core.config import get_config

class TestStripePayments:
    def test_charge_creation(self):
        provider = StripeProvider()
        # ... test code
```

### Example 4: Scheduled Job

```python
"""Daily cleanup job."""

import asyncio
from datetime import datetime

# Bootstrap
from core.bootstrap import bootstrap
bootstrap()

# Project imports
from storage.sqlite_store import SQLiteStore
from core.config import get_logger

logger = get_logger(__name__)

async def cleanup_expired_tokens():
    store = SQLiteStore()
    # ... cleanup logic

if __name__ == "__main__":
    asyncio.run(cleanup_expired_tokens())
```

## Why Bootstrap?

### Problem It Solves

Before bootstrap, you had to write in every file:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()
```

This was:
- Repetitive (copy-pasted 50+ times)
- Error-prone (easy to get wrong)
- Hard to maintain (changes needed in all files)
- Inefficient (load_dotenv called multiple times)

### Bootstrap Solution

One line does everything:
```python
from core.bootstrap import bootstrap
bootstrap()
```

Benefits:
- DRY (Don't Repeat Yourself)
- Idempotent (safe to call multiple times)
- Centralized (one place to change)
- Efficient (load_dotenv called once)

## Important Notes

### Safe to Call Multiple Times

If you import multiple modules that call bootstrap(), it's safe:

```python
# File A
from core.bootstrap import bootstrap
bootstrap()
from core.config import get_config

# File B (imported by File A)
from core.bootstrap import bootstrap
bootstrap()  # This is safe - second call is a no-op
from storage.sqlite_store import SQLiteStore
```

### Always Put Bootstrap First

Make sure bootstrap is called before importing project modules:

```python
# CORRECT
from core.bootstrap import bootstrap
bootstrap()
from core.config import get_config

# WRONG - will fail
from core.config import get_config
from core.bootstrap import bootstrap
bootstrap()
```

### Don't Import sys Anymore

Old pattern (no longer needed):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

New pattern:
```python
from core.bootstrap import bootstrap
bootstrap()
```

## What Bootstrap Does

1. **Loads Environment Variables**
   - Reads `.env` file
   - Makes all env vars available via `os.getenv()`
   - Uses python-dotenv library

2. **Sets Up Import Paths**
   - Adds project root to sys.path
   - Enables clean imports like `from core.config import get_config`

3. **Singleton Pattern**
   - First call: initializes everything
   - Subsequent calls: no-op (safe and efficient)

## Environment Variables

Once bootstrap is called, you can access environment variables:

```python
from core.bootstrap import bootstrap
bootstrap()

import os

# These work because bootstrap called load_dotenv()
api_key = os.getenv("EODHD_API_KEY")
db_url = os.getenv("DATABASE_URL")
```

Or use the config module:

```python
from core.bootstrap import bootstrap
bootstrap()

from core.config import get_config

config = get_config()
api_key = config.eodhd.api_key
db_path = config.storage.sqlite_path
```

## Troubleshooting

### Error: "No module named 'core'"

Make sure bootstrap is called BEFORE importing project modules:

```python
# CORRECT
from core.bootstrap import bootstrap
bootstrap()
from core.config import get_config

# WRONG
from core.config import get_config  # Will fail!
```

### Error: "load_dotenv not found"

Make sure `.env` file exists in project root and dependencies are installed:

```bash
pip install python-dotenv
```

### Environment variables are None

1. Check `.env` file exists at project root
2. Call bootstrap() before accessing env vars
3. Verify variable is actually in `.env` file

```python
from core.bootstrap import bootstrap
bootstrap()

import os
print(os.getenv("MY_VAR"))  # Should work now
```

## Common Use Cases

### In a FastAPI Route

```python
"""API routes."""
from fastapi import APIRouter

from core.bootstrap import bootstrap
bootstrap()

from core.config import get_config

@app.get("/health")
def health_check():
    config = get_config()
    return {"status": "healthy", "env": config.storage.data_dir}
```

### In a Database Script

```python
"""Initialize database."""
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore

store = SQLiteStore()
store.initialize()
```

### In Tests

```python
"""Test user authentication."""
import pytest

from core.bootstrap import bootstrap
bootstrap()

from auth.supabase_client import SupabaseClient

def test_auth():
    client = SupabaseClient()
    # ... test code
```

### In Background Jobs

```python
"""Email notification job."""
import time

from core.bootstrap import bootstrap
bootstrap()

from core.config import get_logger

logger = get_logger(__name__)

while True:
    logger.info("Sending emails...")
    time.sleep(3600)
```

## See Also

- `REFACTORING_NOTES.md` - Detailed refactoring documentation
- `REFACTORING_SUMMARY.txt` - High-level summary
- `/core/bootstrap.py` - Implementation details
- `/core/config.py` - Configuration module
