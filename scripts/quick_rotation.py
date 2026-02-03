#!/usr/bin/env python3
"""Rotation rapide pour appliquer le patch."""
from pathlib import Path
project_root = Path(__file__).parent.parent

# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

from pipeline.rotation import RotationJob
from storage.parquet_store import ParquetStore
from storage.sqlite_store import SQLiteStore
from core.config import get_config

config = get_config()
store = SQLiteStore(str(config.storage.sqlite_path))
parquet_store = ParquetStore(market_scope='US_EU')

print("Relance de la rotation pour US_EU...")
rotation = RotationJob(store=store, parquet_store=parquet_store, market_scope='US_EU')
results = rotation.run(batch_size=100)  # Traiter plus d'actifs
print(f"✅ Rotation terminée: {results['processed']} traités, {results['updated']} mis à jour")
