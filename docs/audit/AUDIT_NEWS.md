# AUDIT NEWS MODULE - MarketGPS

**Date**: 2026-01-24  
**Auditeur**: Claude (AI Lead Engineer)  
**Statut**: CRITIQUE - Pipeline non opérationnel

---

## RÉSUMÉ EXÉCUTIF

Le module news de MarketGPS **NE FONCTIONNE PAS** en production. Seulement **4 articles** existent, tous datés du 24 janvier 2026. Aucune mise à jour automatique n'est effectuée.

---

## TOP 10 CAUSES RACINES

| # | Cause | Criticité | Preuve |
|---|-------|-----------|--------|
| 1 | **SCHEDULER NEWS ABSENT** | CRITIQUE | `prod_scheduler.py` ne contient aucune référence à "news" |
| 2 | **Pas de cron/job planifié** | CRITIQUE | Aucun job APScheduler pour news dans `scheduler.py` |
| 3 | **Classification région manquante** | HAUTE | `sources_registry.json` n'a pas de champ `region` |
| 4 | **Contamination inter-régions** | HAUTE | Pas de validation région avant publication |
| 5 | **Peu de sources activées** | MOYENNE | 46 sources, beaucoup avec `enabled: false` |
| 6 | **Pas de health endpoint news** | MOYENNE | Impossible de monitorer le pipeline |
| 7 | **Pas de retry automatique** | MOYENNE | Si échec fetch, pas de re-tentative |
| 8 | **Pas de purge/rotation** | BASSE | Articles anciens jamais supprimés |
| 9 | **Pas de logs structurés** | BASSE | Difficile à débugger |
| 10 | **Pas de métriques exposées** | BASSE | Pas de stats `last_run`, `error_count` |

---

## ANALYSE DÉTAILLÉE

### 1. ARCHITECTURE ACTUELLE

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE PROD                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌───────────────┐                │
│  │ FRONTEND│    │ BACKEND │    │  SCHEDULER    │                │
│  │  :3000  │───▶│  :8000  │    │ (US_EU only!) │                │
│  └─────────┘    └────┬────┘    └───────────────┘                │
│                      │                                           │
│                ┌─────▼─────┐                                     │
│                │  SQLite   │ ← news_articles (4 rows)            │
│                │   DB      │ ← news_sources (46 rows)            │
│                └───────────┘ ← news_raw_items                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2. FICHIERS ANALYSÉS

| Fichier | Existe | Fonctionnel | Notes |
|---------|--------|-------------|-------|
| `pipeline/news/__init__.py` | ✅ | ✅ | Module OK |
| `pipeline/news/ingest_rss.py` | ✅ | ✅ | RSSIngester fonctionnel |
| `pipeline/news/publish.py` | ✅ | ✅ | NewsPublisher avec LLM |
| `pipeline/news/image_fetcher.py` | ✅ | ⚠️ | Non testé |
| `pipeline/news/sources_registry.json` | ✅ | ⚠️ | Pas de champ region |
| `pipeline/jobs.py` | ✅ | ✅ | --news-full existe |
| `pipeline/prod_scheduler.py` | ✅ | ❌ | PAS DE NEWS |
| `pipeline/scheduler.py` | ✅ | ❌ | PAS DE NEWS |
| `backend/news_routes.py` | ✅ | ✅ | API /api/news OK |
| `storage/sqlite_store.py` | ✅ | ✅ | Tables news existent |

### 3. ÉTAT DE LA BASE DE DONNÉES

```sql
-- Requête de diagnostic (via API)
SELECT COUNT(*) FROM news_articles;        -- 4 articles
SELECT COUNT(*) FROM news_sources;         -- 46 sources
SELECT MAX(published_at) FROM news_articles; -- 2026-01-24T18:25:20
```

**Dernier article publié**: 24 janvier 2026 à 18:25:20

### 4. SCHEDULER ACTUEL (prod_scheduler.py)

```python
# CONTENU ACTUEL - AUCUNE RÉFÉRENCE À NEWS
def run_pipeline():
    """Run the full pipeline at market open/close."""
    # ... uniquement US_EU market data ...
```

**Jobs planifiés**:
- 09:35 ET - Market Open (US_EU scoring)
- 16:10 ET - Market Close (US_EU scoring)
- **AUCUN job news**

### 5. CLASSIFICATION RÉGIONALE MANQUANTE

Sources actuelles sans champ `region`:
```json
{
  "name": "TechCabal",
  "country": "NG",
  "region": null  // ❌ MANQUANT
}
```

Devrait être:
```json
{
  "name": "TechCabal", 
  "country": "NG",
  "region": "WEST"  // ✅ Afrique de l'Ouest
}
```

---

## IMPACT

| Métrique | Attendu | Réel |
|----------|---------|------|
| Articles/jour | 50+ | 0 |
| Fréquence refresh | 30min | JAMAIS |
| Sources actives | 50 | 0 en prod |
| Régions couvertes | 5 | 0 (pas de classification) |

---

## RECOMMANDATIONS (PRIORISÉES)

### CRITIQUE (P0) - À faire immédiatement

1. **Créer `pipeline/news/news_scheduler.py`**
   - APScheduler avec job toutes les 30 minutes
   - Exécute `run_full_pipeline()` de `publish.py`

2. **Ajouter service Docker pour news scheduler**
   - Nouveau service dans `docker-compose.prod.yml`
   - Ou intégrer dans scheduler existant

3. **Ajouter champ `region` aux sources**
   - NORTH, WEST, CENTRAL, EAST, SOUTH, PAN
   - Mettre à jour `sources_registry.json`

### HAUTE (P1) - Cette semaine

4. **Implémenter région guard**
   - Valider que country correspond à region
   - Quarantine si incohérence

5. **Ajouter endpoint `/api/news/health`**
   - Retourne `last_run`, `articles_today`, `errors`

6. **Activer plus de sources**
   - Passer les sources `enabled: false` à `true`
   - Vérifier RSS URLs fonctionnels

### MOYENNE (P2) - Ce mois

7. **Logs structurés**
8. **Métriques Prometheus**
9. **Purge articles > 30 jours**
10. **Dashboard monitoring**

---

## COMMANDES DE VÉRIFICATION

```bash
# Tester ingestion manuelle
python -m pipeline.jobs --news-ingest --news-limit 5

# Tester publication manuelle
python -m pipeline.jobs --news-rewrite --news-limit 5

# Tester pipeline complet
python -m pipeline.jobs --news-full --news-limit 10

# Vérifier API
curl https://api.marketgps.online/api/news | jq '.total'

# Vérifier health (après implémentation)
curl https://api.marketgps.online/api/news/health
```

---

## PLAN D'ACTION

| Phase | Description | Durée estimée |
|-------|-------------|---------------|
| Phase 1 | Mettre à jour sources avec régions | 1h |
| Phase 2 | Créer news scheduler | 1h |
| Phase 3 | Ajouter health endpoint | 30min |
| Phase 4 | Intégrer dans Docker | 30min |
| Phase 5 | Tester en prod | 1h |
| Phase 6 | Documenter | 30min |

**Total**: ~5h de travail

---

## CONCLUSION

Le module news est **complet sur le plan code** mais **non opérationnel** car:
1. Aucun scheduler ne déclenche les jobs
2. Pas de classification régionale
3. Pas de monitoring

La correction nécessite d'ajouter un scheduler dédié et d'améliorer la classification des sources.
