#!/usr/bin/env python3
"""
Script pour appliquer le patch quality/liquidity aux scores existants.

Étapes:
1. Relancer le gating pour US_EU (recalcule les métriques d'investabilité)
2. Relancer la rotation pour US_EU (recalcule les scores avec ajustements)
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.gating import GatingJob
from pipeline.rotation import RotationJob
from storage.parquet_store import ParquetStore
from storage.sqlite_store import SQLiteStore
from core.config import get_config

def main():
    config = get_config()
    market_scope = "US_EU"
    
    print("=" * 80)
    print("APPLICATION DU PATCH QUALITY/LIQUIDITY POUR US_EU")
    print("=" * 80)
    
    store = SQLiteStore(str(config.storage.sqlite_path))
    parquet_store = ParquetStore(market_scope=market_scope)
    
    # Étape 1: Gating
    print("\n[1/2] Relance du Gating Job pour US_EU...")
    print("      (Recalcule ADV_USD, coverage, stale_ratio, data_confidence)")
    gating = GatingJob(store=store, parquet_store=parquet_store, market_scope=market_scope)
    gating_results = gating.run(batch_size=100)
    print(f"      Résultat: {gating_results['processed']} traités, "
          f"{gating_results['eligible']} éligibles, "
          f"{gating_results['ineligible']} non éligibles")
    
    # Étape 2: Rotation (recalcule les scores avec ajustements)
    print("\n[2/2] Relance du Rotation Job pour US_EU...")
    print("      (Recalcule les scores avec pénalités quality/liquidity)")
    rotation = RotationJob(store=store, parquet_store=parquet_store, market_scope=market_scope)
    rotation_results = rotation.run(batch_size=50)
    print(f"      Résultat: {rotation_results['processed']} traités, "
          f"{rotation_results['updated']} mis à jour")
    
    print("\n" + "=" * 80)
    print("PATCH APPLIQUÉ!")
    print("=" * 80)
    print("\nPour vérifier les résultats, exécutez:")
    print("  python3 scripts/check_anomalies.py")
    print("  python3 scripts/verify_patch_status.py")

if __name__ == "__main__":
    main()
