"""
SQLiteStore - Main interface for MarketGPS database operations.

This module provides backward-compatible access to the database through
the SQLiteStore class, which uses the Repository pattern internally
for better code organization.

REFACTORED: The implementation has been split into specialized repositories:
- AssetRepository: Universe and gating operations
- ScoreRepository: Score, rotation, calibration, watchlist, and job runs
- NewsRepository: News articles and sources
- UserRepository: User accounts and profiles
- SubscriptionRepository: Subscription and quota management
- GeneralRepository: Jobs queue, quotas, settings, statistics
- ExplorerRepository: Search, landing page metrics, long-term scoring

All methods maintain backward compatibility by delegating to these repositories.
"""

# For backward compatibility, re-export from the facade
from storage.sqlite_store_facade import SQLiteStore

__all__ = ["SQLiteStore"]
