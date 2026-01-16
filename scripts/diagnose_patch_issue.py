#!/usr/bin/env python3
"""
Diagnostic: Pourquoi le patch ne change pas le classement?
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import json
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from pipeline.rotation import RotationJob
from pipeline.gating import GatingJob
from pipeline.quality_adjustments import apply_quality_liquidity_adjustments
from core.config import get_config

def main():
    config = get_config()
    market_scope = "US_EU"
    
    store = SQLiteStore(str(config.storage.sqlite_path))
    parquet_store = ParquetStore(market_scope=market_scope)
    
    print("=" * 100)
    print("DIAGNOSTIC: Pourquoi le classement n'a pas changé?")
    print("=" * 100)
    
    # 1. Vérifier un actif spécifique
    print("\n[1] Test sur un actif spécifique:")
    
    # Trouver un actif avec ADV faible et score élevé
    with store._get_connection() as conn:
        query = """
        SELECT 
            u.asset_id,
            u.symbol,
            s.score_total,
            g.liquidity as adv_usd,
            g.coverage,
            g.stale_ratio,
            g.data_confidence,
            g.eligible
        FROM scores_latest s
        JOIN universe u ON u.asset_id = s.asset_id
        JOIN gating_status g ON g.asset_id = s.asset_id
        WHERE u.market_scope = 'US_EU'
          AND g.liquidity > 0
          AND g.liquidity < 500000
          AND s.score_total > 70
        ORDER BY s.score_total DESC
        LIMIT 1;
        """
        
        row = conn.execute(query).fetchone()
        
        if not row:
            print("   Aucun actif trouvé pour le test")
            return
        
        asset_id = row['asset_id']
        symbol = row['symbol']
        old_score = row['score_total']
        adv = row['adv_usd']
        coverage = row['coverage']
        stale = row['stale_ratio']
        conf = row['data_confidence']
        
        print(f"   Actif: {symbol} ({asset_id})")
        print(f"   Score actuel: {old_score:.1f}")
        print(f"   ADV: {adv/1000:.0f}K USD")
        print(f"   Coverage: {coverage*100:.1f}%")
        print(f"   Stale ratio: {stale*100:.1f}%")
        print(f"   Data confidence: {conf}")
        
        # 2. Tester le patch manuellement
        print("\n[2] Test du patch manuellement:")
        
        gating_metrics = {
            "adv_usd": adv,
            "coverage": coverage,
            "stale_ratio": stale,
            "zero_volume_ratio": 0.0,  # Approximation
            "data_confidence": conf
        }
        
        adjusted_score, debug = apply_quality_liquidity_adjustments(
            raw_score_total=old_score,
            gating_metrics=gating_metrics,
            market_scope=market_scope
        )
        
        print(f"   Raw score: {old_score:.1f}")
        print(f"   Adjusted score: {adjusted_score:.1f}")
        print(f"   Différence: {adjusted_score - old_score:.1f}")
        print(f"   Confidence multiplier: {debug.get('confidence_multiplier', 'N/A')}")
        print(f"   Liquidity penalty: {debug.get('liquidity_penalty', 'N/A')}")
        print(f"   Caps appliqués: {debug.get('caps_applied', [])}")
        
        if abs(adjusted_score - old_score) < 0.1:
            print("\n   ⚠️  PROBLÈME: L'ajustement est très faible ou nul!")
            print("   → Vérifier les thresholds et la formule")
        else:
            print(f"\n   ✅ Le patch devrait changer le score de {old_score:.1f} à {adjusted_score:.1f}")
        
        # 3. Vérifier si le gating a été mis à jour
        print("\n[3] Vérification du gating:")
        print(f"   ADV dans gating_status: {adv/1000:.0f}K")
        print(f"   Data confidence: {conf}")
        
        if adv == 0 or conf == 0:
            print("   ⚠️  PROBLÈME: Gating non mis à jour ou données manquantes")
            print("   → Relancer gating job: python3 -m pipeline.jobs --run-gating --scope US_EU")
        
        # 4. Vérifier si rotation va appliquer le patch
        print("\n[4] Test du recalcul complet:")
        print(f"   Tentative de recalcul pour {symbol}...")
        
        try:
            rotation = RotationJob(store=store, parquet_store=parquet_store, market_scope=market_scope)
            success = rotation._process_asset(asset_id)
            
            if success:
                # Récupérer le nouveau score
                with store._get_connection() as conn2:
                    query2 = """
                    SELECT score_total, confidence, json_breakdown
                    FROM scores_latest
                    WHERE asset_id = ?
                    """
                    row2 = conn2.execute(query2, (asset_id,)).fetchone()
                    
                    if row2:
                        new_score = row2['score_total']
                        new_conf = row2['confidence']
                        breakdown_str = row2['json_breakdown'] or '{}'
                        
                        print(f"   ✅ Recalcul réussi!")
                        print(f"   Nouveau score: {new_score:.1f} (ancien: {old_score:.1f})")
                        print(f"   Nouvelle confidence: {new_conf}")
                        
                        # Vérifier le breakdown
                        try:
                            breakdown = json.loads(breakdown_str)
                            if 'raw_score_total' in breakdown.get('features', {}):
                                print(f"   ✅ Patch appliqué (raw_score_total présent dans breakdown)")
                            else:
                                print(f"   ⚠️  Patch non appliqué (raw_score_total absent)")
                        except:
                            print(f"   ⚠️  Breakdown non lisible")
                    else:
                        print(f"   ⚠️  Score non trouvé après recalcul")
            else:
                print(f"   ❌ Échec du recalcul")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    # 5. Recommandations
    print("\n" + "=" * 100)
    print("RECOMMANDATIONS:")
    print("=" * 100)
    print("1. Relancer le gating pour mettre à jour les métriques:")
    print("   python3 -m pipeline.jobs --run-gating --scope US_EU")
    print("\n2. Relancer la rotation pour recalculer les scores avec le patch:")
    print("   python3 -m pipeline.jobs --run-rotation --scope US_EU")
    print("\n3. Vérifier les résultats:")
    print("   python3 scripts/analyze_score_changes.py")

if __name__ == "__main__":
    main()
