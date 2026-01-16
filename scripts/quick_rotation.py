#!/usr/bin/env python3
"""Rotation rapide pour appliquer le patch."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
