#!/usr/bin/env python3
"""
Analyser pourquoi le classement n'a pas changé après le patch.
"""
import sqlite3
import json
import sys
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "sqlite" / "marketgps.db"
if not db_path.exists():
    print(f"ERREUR: Base de données non trouvée: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("=" * 100)
print("ANALYSE: Pourquoi le classement n'a pas changé?")
print("=" * 100)

# 1. Vérifier si le patch a été appliqué
print("\n[1] Vérification du statut du patch:")
query1 = """
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN json_breakdown LIKE '%raw_score_total%' THEN 1 ELSE 0 END) as avec_patch
FROM scores_latest s
JOIN universe u ON u.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU' AND s.score_total IS NOT NULL;
"""
row1 = conn.execute(query1).fetchone()
total = row1['total']
avec_patch = row1['avec_patch']
print(f"   Total scores US_EU: {total}")
print(f"   Scores avec patch: {avec_patch} ({(avec_patch/total*100) if total > 0 else 0:.1f}%)")

if avec_patch == 0:
    print("\n   ⚠️  PROBLÈME: Le patch n'a PAS été appliqué!")
    print("   → Les scores n'ont pas été recalculés avec les ajustements")
    print("   → Solution: Relancer rotation job pour US_EU")
    print("\n   Commande: python3 -m pipeline.jobs --run-rotation --scope US_EU")
    conn.close()
    sys.exit(0)

# 2. Analyser les différences raw_score vs final_score
print("\n[2] Analyse des ajustements appliqués:")
query2 = """
SELECT 
    u.symbol,
    s.score_total as final_score,
    s.confidence,
    g.liquidity as adv_usd,
    g.coverage,
    g.stale_ratio,
    s.json_breakdown
FROM scores_latest s
JOIN universe u ON u.asset_id = s.asset_id
JOIN gating_status g ON g.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU'
  AND s.json_breakdown LIKE '%raw_score_total%'
ORDER BY s.score_total DESC
LIMIT 20;
"""

rows2 = conn.execute(query2).fetchall()
if not rows2:
    print("   Aucun score avec patch trouvé")
    conn.close()
    sys.exit(0)

print(f"\n   Top 20 scores (avec patch appliqué):")
print(f"   {'Symbol':<12} {'Raw':<8} {'Final':<8} {'Diff':<8} {'ADV (K)':<10} {'Conf':<6} {'Caps':<20}")
print("   " + "-" * 80)

adjustments_count = 0
for row in rows2:
    symbol = row['symbol'][:12]
    final_score = row['score_total']
    conf = row['confidence']
    adv = row['adv_usd'] / 1000 if row['adv_usd'] else 0
    breakdown_str = row['json_breakdown'] or '{}'
    
    try:
        breakdown = json.loads(breakdown_str)
        features = breakdown.get('features', {})
        raw_score = features.get('raw_score_total', final_score)
        diff = final_score - raw_score
        caps = features.get('caps_applied', [])
        caps_str = ', '.join(caps[:1]) if caps else 'Aucun'
        
        if abs(diff) > 0.1:  # Ajustement significatif
            adjustments_count += 1
    except:
        raw_score = final_score
        diff = 0
        caps_str = 'N/A'
    
    print(f"   {symbol:<12} {raw_score:<8.1f} {final_score:<8.1f} {diff:<8.1f} {adv:<10.0f} {conf:<6} {caps_str[:20]:<20}")

print(f"\n   Scores avec ajustement significatif (>0.1): {adjustments_count}/{len(rows2)}")

# 3. Vérifier les actifs illiquides
print("\n[3] Vérification des actifs illiquides (ADV < 250K):")
query3 = """
SELECT 
    COUNT(*) as total_illiquid,
    AVG(s.score_total) as avg_score,
    MAX(s.score_total) as max_score,
    MIN(s.score_total) as min_score
FROM scores_latest s
JOIN universe u ON u.asset_id = s.asset_id
JOIN gating_status g ON g.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU'
  AND g.liquidity < 250000
  AND s.score_total IS NOT NULL;
"""
row3 = conn.execute(query3).fetchone()
print(f"   Nombre d'actifs illiquides: {row3['total_illiquid']}")
if row3['total_illiquid'] > 0:
    print(f"   Score moyen: {row3['avg_score']:.1f}")
    print(f"   Score max: {row3['max_score']:.1f}")
    print(f"   Score min: {row3['min_score']:.1f}")
    
    if row3['max_score'] > 60:
        print(f"\n   ⚠️  PROBLÈME: Score max {row3['max_score']:.1f} > 60 pour actifs illiquides!")
        print("   → Le cap ADV < 250K → max 60 n'est pas appliqué correctement")
        
        # Trouver les contre-exemples
        query4 = """
        SELECT 
            u.symbol,
            s.score_total,
            g.liquidity as adv_usd,
            s.json_breakdown
        FROM scores_latest s
        JOIN universe u ON u.asset_id = s.asset_id
        JOIN gating_status g ON g.asset_id = s.asset_id
        WHERE u.market_scope = 'US_EU'
          AND g.liquidity < 250000
          AND s.score_total > 60
        ORDER BY s.score_total DESC
        LIMIT 5;
        """
        rows4 = conn.execute(query4).fetchall()
        print("\n   Contre-exemples:")
        for r in rows4:
            print(f"     {r['symbol']}: score={r['score_total']:.1f}, ADV={r['adv_usd']/1000:.0f}K")
            breakdown = json.loads(r['json_breakdown'] or '{}')
            if 'raw_score_total' in breakdown.get('features', {}):
                print(f"       → Patch appliqué mais cap non respecté!")

# 4. Vérifier si les scores ont vraiment changé
print("\n[4] Comparaison Top 50 avant/après (si historique disponible):")
print("   (Note: Cette analyse nécessite un historique des scores)")

# 5. Vérifier le code du patch
print("\n[5] Vérification du code du patch:")
print("   → Vérifier que rotation.py appelle bien apply_quality_liquidity_adjustments")
print("   → Vérifier que market_scope == 'US_EU' dans la condition")

# 6. Diagnostic final
print("\n" + "=" * 100)
print("DIAGNOSTIC:")
print("=" * 100)

if avec_patch == 0:
    print("❌ Le patch n'a PAS été appliqué - les scores n'ont pas été recalculés")
    print("   Solution: python3 -m pipeline.jobs --run-rotation --scope US_EU")
elif adjustments_count == 0:
    print("⚠️  Le patch est appliqué mais aucun ajustement significatif détecté")
    print("   → Possible: tous les actifs sont déjà de bonne qualité")
    print("   → Ou: les ajustements sont trop faibles")
elif row3['total_illiquid'] > 0 and row3['max_score'] > 60:
    print("❌ Le patch est appliqué mais les caps ne sont pas respectés")
    print("   → Bug possible dans apply_quality_liquidity_adjustments")
else:
    print("✅ Le patch semble fonctionner correctement")
    print("   → Si le classement n'a pas changé, c'est normal si:")
    print("     - Les actifs de qualité étaient déjà en haut")
    print("     - Les ajustements ne changent pas l'ordre relatif")

conn.close()
