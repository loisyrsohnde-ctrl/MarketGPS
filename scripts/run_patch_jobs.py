#!/usr/bin/env python3
"""
Relancer les jobs gating et rotation pour appliquer le patch quality/liquidity.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.gating import GatingJob
from pipeline.rotation import RotationJob
from storage.parquet_store import ParquetStore
from storage.sqlite_store import SQLiteStore
from core.config import get_config
import time

def main():
    config = get_config()
    market_scope = "US_EU"
    
    print("=" * 100)
    print("APPLICATION DU PATCH QUALITY/LIQUIDITY POUR US_EU")
    print("=" * 100)
    
    store = SQLiteStore(str(config.storage.sqlite_path))
    parquet_store = ParquetStore(market_scope=market_scope)
    
    # Étape 1: Gating
    print("\n[1/2] Relance du Gating Job pour US_EU...")
    print("      (Recalcule ADV_USD, coverage, stale_ratio, data_confidence)")
    print("      Cela peut prendre plusieurs minutes...\n")
    
    try:
        gating = GatingJob(store=store, parquet_store=parquet_store, market_scope=market_scope)
        gating_results = gating.run(batch_size=100)
        
        print(f"\n✅ Gating terminé:")
        print(f"   - {gating_results['processed']} actifs traités")
        print(f"   - {gating_results['eligible']} éligibles")
        print(f"   - {gating_results['ineligible']} non éligibles")
        print(f"   - {gating_results['errors']} erreurs")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du gating: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Étape 2: Rotation (recalcule les scores avec ajustements)
    print("\n" + "=" * 100)
    print("[2/2] Relance du Rotation Job pour US_EU...")
    print("      (Recalcule les scores avec pénalités quality/liquidity)")
    print("      Cela peut prendre plusieurs minutes...\n")
    
    try:
        rotation = RotationJob(store=store, parquet_store=parquet_store, market_scope=market_scope)
        rotation_results = rotation.run(batch_size=50)
        
        print(f"\n✅ Rotation terminée:")
        print(f"   - {rotation_results['processed']} actifs traités")
        print(f"   - {rotation_results['updated']} scores mis à jour")
        print(f"   - {rotation_results['errors']} erreurs")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la rotation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Vérification
    print("\n" + "=" * 100)
    print("VÉRIFICATION DES RÉSULTATS")
    print("=" * 100)
    
    import sqlite3
    conn = sqlite3.connect(str(config.storage.sqlite_path))
    conn.row_factory = sqlite3.Row
    
    # Compter les scores avec patch
    query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN json_breakdown LIKE '%raw_score_total%' THEN 1 ELSE 0 END) as avec_patch
    FROM scores_latest s
    JOIN universe u ON u.asset_id = s.asset_id
    WHERE u.market_scope = 'US_EU' AND s.score_total IS NOT NULL;
    """
    row = conn.execute(query).fetchone()
    total = row['total']
    avec_patch = row['avec_patch']
    
    print(f"\nScores US_EU: {total}")
    print(f"Scores avec patch appliqué: {avec_patch} ({(avec_patch/total*100) if total > 0 else 0:.1f}%)")
    
    # Vérifier les anomalies
    query2 = """
    SELECT COUNT(*) as anomalies
    FROM scores_latest s
    JOIN universe u ON u.asset_id = s.asset_id
    JOIN gating_status g ON g.asset_id = s.asset_id
    WHERE u.market_scope = 'US_EU'
      AND g.liquidity < 250000
      AND s.score_total > 70;
    """
    row2 = conn.execute(query2).fetchone()
    anomalies = row2['anomalies']
    
    print(f"\nAnomalies (ADV < 250K et score > 70): {anomalies}")
    
    if anomalies == 0:
        print("✅ Aucune anomalie détectée!")
    else:
        print(f"⚠️  {anomalies} anomalies restantes")
    
    # Top 10 pour voir le classement
    print("\n" + "=" * 100)
    print("TOP 10 SCORES (après patch):")
    print("=" * 100)
    
    query3 = """
    SELECT 
        u.symbol,
        s.score_total,
        s.confidence,
        g.liquidity as adv_usd,
        g.coverage,
        g.stale_ratio
    FROM scores_latest s
    JOIN universe u ON u.asset_id = s.asset_id
    JOIN gating_status g ON g.asset_id = s.asset_id
    WHERE u.market_scope = 'US_EU'
      AND s.score_total IS NOT NULL
    ORDER BY s.score_total DESC, s.confidence DESC
    LIMIT 10;
    """
    
    rows = conn.execute(query3).fetchall()
    print(f"{'Symbol':<12} {'Score':<8} {'Conf':<6} {'ADV (K)':<12} {'Coverage':<10} {'Stale':<8}")
    print("-" * 70)
    for r in rows:
        symbol = r['symbol'][:12]
        score = r['score_total']
        conf = r['confidence']
        adv = r['adv_usd'] / 1000 if r['adv_usd'] else 0
        coverage = r['coverage'] * 100 if r['coverage'] else 0
        stale = r['stale_ratio'] * 100 if r['stale_ratio'] else 0
        print(f"{symbol:<12} {score:<8.1f} {conf:<6} {adv:<12.0f} {coverage:<10.1f}% {stale:<8.1f}%")
    
    conn.close()
    
    print("\n" + "=" * 100)
    print("✅ PATCH APPLIQUÉ!")
    print("=" * 100)
    print("\nLe classement devrait maintenant refléter la qualité des données.")
    print("Les actifs illiquides ou à faible qualité sont pénalisés.")

if __name__ == "__main__":
    main()
