"""
MarketGPS v7.0 - Bootstrap Module

Centralizes application initialization:
- Environment variables loading (load_dotenv)
- Proper import path setup
- Logging configuration

This module should be imported ONCE at application startup.
All other modules should import from core.config, not call load_dotenv() directly.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv


# Singleton flag to ensure single initialization
_initialized = False


def bootstrap():
    """
    Initialize the MarketGPS application.

    This function:
    1. Loads environment variables from .env file
    2. Ensures proper sys.path setup for imports
    3. Should be called ONCE at application startup

    Safe to call multiple times - will only initialize once.
    """
    global _initialized

    if _initialized:
        return

    # Load environment variables once
    load_dotenv()

    # Ensure project root is in sys.path for proper imports
    project_root = Path(__file__).parent.parent.resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    _initialized = True


def ensure_bootstrap():
    """
    Ensure bootstrap has been called.

    Returns True if this call triggered bootstrap, False if already initialized.
    """
    global _initialized
    if not _initialized:
        bootstrap()
        return True
    return False
