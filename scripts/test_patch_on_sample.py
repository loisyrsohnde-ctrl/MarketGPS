#!/usr/bin/env python3
"""
Tester le patch sur un échantillon d'actifs pour vérifier qu'il fonctionne.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from pipeline.rotation import RotationJob
from core.config import get_config
import json

def main():
    config = get_config()
    market_scope = "US_EU"
    
    store = SQLiteStore(str(config.storage.sqlite_path))
    parquet_store = ParquetStore(market_scope=market_scope)
    
    print("=" * 80)
    print("TEST DU PATCH SUR UN ÉCHANTILLON")
    print("=" * 80)
    
    # Récupérer quelques actifs illiquides avec scores élevés
    query = """
    SELECT 
        u.asset_id,
        u.symbol,
        s.score_total,
        g.liquidity as adv_usd
    FROM scores_latest s
    JOIN universe u ON u.asset_id = s.asset_id
    JOIN gating_status g ON g.asset_id = s.asset_id
    WHERE u.market_scope = 'US_EU'
      AND g.liquidity < 500000
      AND s.score_total > 60
    ORDER BY s.score_total DESC
    LIMIT 10;
    """
    
    with store._get_connection() as conn:
        rows = conn.execute(query).fetchall()
    
    if not rows:
        print("Aucun actif illiquide avec score élevé trouvé")
        print("(C'est bon signe - peut-être que le patch a déjà été appliqué?)")
        return
    
    print(f"\nTrouvé {len(rows)} actifs illiquides avec scores élevés")
    print("Recalcul des scores avec le patch...\n")
    
    rotation = RotationJob(store=store, parquet_store=parquet_store, market_scope=market_scope)
    
    results = []
    for row in rows[:5]:  # Tester sur 5 actifs
        asset_id = row['asset_id']
        symbol = row['symbol']
        old_score = row['score_total']
        adv = row['adv_usd']
        
        print(f"  {symbol} (ADV: {adv/1000:.0f}K, ancien score: {old_score:.1f})...", end=" ")
        
        try:
            # Recalculer le score
            score_obj = rotation.refresh_single(asset_id)
            
            if score_obj:
                new_score = score_obj.score_total
                diff = new_score - old_score
                
                # Vérifier le breakdown
                breakdown_str = score_obj.breakdown.to_json() if score_obj.breakdown else '{}'
                breakdown = json.loads(breakdown_str) if breakdown_str else {}
                features = breakdown.get('features', {})
                raw_score = features.get('raw_score_total', new_score)
                caps = features.get('caps_applied', [])
                
                results.append({
                    'symbol': symbol,
                    'old': old_score,
                    'new': new_score,
                    'raw': raw_score,
                    'diff': diff,
                    'caps': caps,
                    'adv': adv
                })
                
                status = "✅" if abs(diff) > 0.1 or caps else "➡️"
                print(f"{status} {old_score:.1f} → {new_score:.1f} (raw: {raw_score:.1f})")
                if caps:
                    print(f"      Caps: {', '.join(caps[:2])}")
            else:
                print("❌ Échec")
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ:")
    print("=" * 80)
    
    if results:
        changed = sum(1 for r in results if abs(r['diff']) > 0.1)
        print(f"Scores modifiés: {changed}/{len(results)}")
        
        print(f"\n{'Symbol':<12} {'Ancien':<8} {'Nouveau':<8} {'Raw':<8} {'Diff':<8} {'ADV (K)':<10}")
        print("-" * 70)
        for r in results:
            print(f"{r['symbol']:<12} {r['old']:<8.1f} {r['new']:<8.1f} {r['raw']:<8.1f} {r['diff']:<8.1f} {r['adv']/1000:<10.0f}")
        
        # Vérifier les caps
        capped = [r for r in results if r['caps']]
        if capped:
            print(f"\n✅ Caps appliqués sur {len(capped)} actifs")
        else:
            print("\n⚠️  Aucun cap appliqué - vérifier les thresholds")
        
        # Vérifier si les scores illiquides sont bien capés
        high_scores = [r for r in results if r['adv'] < 250000 and r['new'] > 60]
        if high_scores:
            print(f"\n❌ PROBLÈME: {len(high_scores)} actifs avec ADV < 250K ont encore score > 60")
            for r in high_scores:
                print(f"   {r['symbol']}: score={r['new']:.1f}, ADV={r['adv']/1000:.0f}K")
        else:
            print("\n✅ Tous les actifs illiquides sont bien capés à ≤ 60")
    else:
        print("Aucun résultat à afficher")

if __name__ == "__main__":
    main()
