#!/usr/bin/env python3
"""
Vérifier le statut du patch: combien de scores ont été ajustés?
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

# Compter les scores avec et sans patch
query = """
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN json_breakdown LIKE '%raw_score_total%' THEN 1 ELSE 0 END) as avec_patch,
    SUM(CASE WHEN json_breakdown IS NULL OR json_breakdown NOT LIKE '%raw_score_total%' THEN 1 ELSE 0 END) as sans_patch
FROM scores_latest s
JOIN universe u ON u.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU'
  AND s.score_total IS NOT NULL;
"""

row = conn.execute(query).fetchone()
total = row['total']
avec_patch = row['avec_patch']
sans_patch = row['sans_patch']

print("=" * 80)
print("STATUT DU PATCH QUALITY/LIQUIDITY")
print("=" * 80)
print(f"Total scores US_EU: {total}")
print(f"Scores avec patch appliqué (json_breakdown contient 'raw_score_total'): {avec_patch}")
print(f"Scores sans patch (anciens scores): {sans_patch}")
print(f"Pourcentage avec patch: {(avec_patch/total*100) if total > 0 else 0:.1f}%")

# Vérifier quelques exemples
print("\n" + "=" * 80)
print("EXEMPLES DE SCORES AVEC PATCH:")
print("=" * 80)

query2 = """
SELECT 
    u.symbol,
    s.score_total,
    s.confidence,
    g.liquidity as adv_usd,
    s.json_breakdown
FROM scores_latest s
JOIN universe u ON u.asset_id = s.asset_id
JOIN gating_status g ON g.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU'
  AND s.json_breakdown LIKE '%raw_score_total%'
ORDER BY s.score_total DESC
LIMIT 5;
"""

rows = conn.execute(query2).fetchall()
for row in rows:
    symbol = row['symbol']
    score = row['score_total']
    conf = row['confidence']
    adv = row['adv_usd'] / 1000 if row['adv_usd'] else 0
    breakdown_str = row['json_breakdown'] or '{}'
    
    try:
        breakdown = json.loads(breakdown_str)
        raw_score = breakdown.get('features', {}).get('raw_score_total', 'N/A')
        final_score = breakdown.get('features', {}).get('final_score_total', score)
        caps = breakdown.get('features', {}).get('caps_applied', [])
    except:
        raw_score = 'N/A'
        final_score = score
        caps = []
    
    print(f"\n{symbol}:")
    print(f"  Score final: {final_score:.1f} (raw: {raw_score})")
    print(f"  Confidence: {conf}, ADV: {adv:.0f}K USD")
    if caps:
        print(f"  Caps appliqués: {', '.join(caps[:2])}")

# Vérifier les scores illiquides qui ont été ajustés
print("\n" + "=" * 80)
print("SCORES ILLIQUIDES (ADV < 250K) APRÈS PATCH:")
print("=" * 80)

query3 = """
SELECT 
    u.symbol,
    s.score_total,
    s.confidence,
    g.liquidity as adv_usd,
    g.coverage,
    s.json_breakdown
FROM scores_latest s
JOIN universe u ON u.asset_id = s.asset_id
JOIN gating_status g ON g.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU'
  AND g.liquidity < 250000
  AND s.json_breakdown LIKE '%raw_score_total%'
ORDER BY s.score_total DESC
LIMIT 10;
"""

rows3 = conn.execute(query3).fetchall()
if rows3:
    print(f"{'Symbol':<12} {'Score':<8} {'Conf':<6} {'ADV (K)':<10} {'Coverage':<10}")
    print("-" * 60)
    for row in rows3:
        symbol = row['symbol'][:12]
        score = row['score_total']
        conf = row['confidence']
        adv = row['adv_usd'] / 1000 if row['adv_usd'] else 0
        coverage = row['coverage'] * 100 if row['coverage'] else 0
        print(f"{symbol:<12} {score:<8.1f} {conf:<6} {adv:<10.0f} {coverage:<10.1f}%")
        
        # Vérifier que le score est bien capé
        if score > 60:
            print(f"  ⚠️  ATTENTION: Score {score:.1f} > 60 malgré ADV < 250K")
else:
    print("Aucun score illiquide trouvé (bon signe!)")

conn.close()
