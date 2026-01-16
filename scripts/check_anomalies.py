#!/usr/bin/env python3
"""
Script pour détecter les anomalies: actifs illiquides avec scores élevés.
"""
import sqlite3
import sys
from pathlib import Path

# Use default DB path
db_path = Path(__file__).parent.parent / "data" / "sqlite" / "marketgps.db"
if not db_path.exists():
    print(f"ERREUR: Base de données non trouvée: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

query = """
SELECT 
    u.symbol, 
    u.name,
    s.score_total, 
    s.confidence, 
    g.liquidity AS adv_usd, 
    g.coverage, 
    g.stale_ratio,
    g.eligible,
    g.reason
FROM scores_latest s
JOIN universe u ON u.asset_id=s.asset_id
JOIN gating_status g ON g.asset_id=s.asset_id
WHERE u.market_scope='US_EU'
  AND g.liquidity < 250000
  AND s.score_total > 70
ORDER BY s.score_total DESC
LIMIT 100;
"""

rows = conn.execute(query).fetchall()
print(f"Nombre d'anomalies détectées: {len(rows)}\n")
print("=" * 120)
print(f"{'Symbol':<12} {'Score':<8} {'Conf':<6} {'ADV (K)':<10} {'Coverage':<10} {'Stale':<8} {'Eligible':<10}")
print("=" * 120)

for row in rows[:30]:  # Afficher les 30 premiers
    symbol = row['symbol'][:12]
    score = row['score_total']
    conf = row['confidence']
    adv = row['adv_usd'] / 1000 if row['adv_usd'] else 0
    coverage = row['coverage'] * 100 if row['coverage'] else 0
    stale = row['stale_ratio'] * 100 if row['stale_ratio'] else 0
    eligible = 'Oui' if row['eligible'] else 'Non'
    print(f"{symbol:<12} {score:<8.1f} {conf:<6} {adv:<10.0f} {coverage:<10.1f}% {stale:<8.1f}% {eligible:<10}")

if len(rows) > 30:
    print(f"\n... et {len(rows) - 30} autres anomalies")

# Analyse supplémentaire
print("\n" + "=" * 120)
print("ANALYSE:")
print(f"- Actifs avec ADV < 250K et score > 70: {len(rows)}")
print(f"- Actifs avec ADV < 250K et score > 60: ", end="")

query2 = """
SELECT COUNT(*) as cnt
FROM scores_latest s
JOIN universe u ON u.asset_id=s.asset_id
JOIN gating_status g ON g.asset_id=s.asset_id
WHERE u.market_scope='US_EU'
  AND g.liquidity < 250000
  AND s.score_total > 60;
"""
cnt = conn.execute(query2).fetchone()['cnt']
print(f"{cnt}")

print(f"- Actifs avec ADV < 250K et score > 55: ", end="")
query3 = """
SELECT COUNT(*) as cnt
FROM scores_latest s
JOIN universe u ON u.asset_id=s.asset_id
JOIN gating_status g ON g.asset_id=s.asset_id
WHERE u.market_scope='US_EU'
  AND g.liquidity < 250000
  AND s.score_total > 55;
"""
cnt = conn.execute(query3).fetchone()['cnt']
print(f"{cnt}")

# Vérifier si ces scores ont été calculés AVANT le patch
print("\n" + "=" * 120)
print("VÉRIFICATION: Ces scores ont-ils été ajustés?")
print("(Si json_breakdown contient 'raw_score_total', le patch a été appliqué)")

query4 = """
SELECT 
    u.symbol,
    s.score_total,
    s.json_breakdown
FROM scores_latest s
JOIN universe u ON u.asset_id=s.asset_id
JOIN gating_status g ON g.asset_id=s.asset_id
WHERE u.market_scope='US_EU'
  AND g.liquidity < 250000
  AND s.score_total > 70
ORDER BY s.score_total DESC
LIMIT 5;
"""

rows4 = conn.execute(query4).fetchall()
for row in rows4:
    symbol = row['symbol']
    score = row['score_total']
    breakdown = row['json_breakdown'] or '{}'
    has_raw = 'raw_score_total' in breakdown
    print(f"{symbol}: score={score:.1f}, patch_appliqué={'OUI' if has_raw else 'NON'}")

conn.close()
