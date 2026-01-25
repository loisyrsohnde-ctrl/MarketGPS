# NEWS MODULE - STATUS REPORT

**Date**: 2026-01-24  
**Statut**: ✅ CORRIGÉ - Prêt pour déploiement

---

## RÉSUMÉ DES CORRECTIONS

Le module news a été complètement corrigé et est maintenant opérationnel.

### Problèmes identifiés et corrigés

| Problème | Solution |
|----------|----------|
| Scheduler news inexistant | Créé `pipeline/news/news_scheduler.py` avec APScheduler |
| Pas de classification région | Ajouté champ `region` aux 50 sources |
| Sources sans régions | Mise à jour `sources_registry.json` avec 50 sources classifiées |
| Pas de health endpoint | Ajouté `/api/news/health` |
| Pas de endpoint regions dynamique | Ajouté `/api/news/regions` avec compteurs |
| Docker sans news scheduler | Ajouté service `news-scheduler` dans docker-compose |
| UI statique | Frontend utilise maintenant les compteurs dynamiques |

---

## FICHIERS MODIFIÉS/CRÉÉS

### Nouveaux fichiers
- `pipeline/news/news_scheduler.py` - Scheduler APScheduler toutes les 30 min
- `scripts/smoke_news.sh` - Script de test smoke
- `AUDIT_NEWS.md` - Rapport d'audit
- `NEWS_STATUS.md` - Ce fichier

### Fichiers modifiés
- `pipeline/news/sources_registry.json` - 50 sources avec classification régionale
- `pipeline/news/ingest_rss.py` - Support du champ region
- `backend/news_routes.py` - Endpoints `/health` et `/regions`
- `storage/sqlite_store.py` - Colonne region dans tables
- `docker-compose.prod.yml` - Service news-scheduler
- `frontend/app/news/page.tsx` - Compteurs régions dynamiques

---

## ARCHITECTURE CORRIGÉE

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE PROD                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌───────────────┐                │
│  │ FRONTEND│    │ BACKEND │    │  SCHEDULER    │                │
│  │  :3000  │───▶│  :8000  │    │ (US_EU data)  │                │
│  └─────────┘    └────┬────┘    └───────────────┘                │
│                      │                                           │
│                      │         ┌───────────────┐                │
│                      │         │ NEWS-SCHEDULER│ ← NOUVEAU!     │
│                      │         │ (every 30min) │                │
│                      │         └───────────────┘                │
│                      │                                           │
│                ┌─────▼─────┐                                     │
│                │  SQLite   │                                     │
│                │   DB      │                                     │
│                └───────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## CLASSIFICATION RÉGIONALE

| Région | Code | Pays inclus |
|--------|------|-------------|
| PAN | Panafricain | Multi-pays, continent-wide |
| NORTH | Afrique du Nord | MA, DZ, TN, EG, LY |
| WEST | Afrique de l'Ouest | NG, GH, SN, CI, BF, ML, NE, TG, BJ |
| CENTRAL | Afrique Centrale | CM, GA, CG, TD, CF, GQ, CD |
| EAST | Afrique de l'Est | KE, TZ, UG, RW, ET |
| SOUTH | Afrique Australe | ZA, AO, MZ, ZW, NA, BW |

---

## COMMANDES DE VÉRIFICATION

### En local

```bash
# Tester l'ingestion
python -m pipeline.jobs --news-ingest --news-limit 5

# Tester la publication
python -m pipeline.jobs --news-rewrite --news-limit 10

# Pipeline complet
python -m pipeline.jobs --news-full --news-limit 20

# Scheduler (une fois)
python -m pipeline.news.news_scheduler --once

# Scheduler (continu, toutes les 30 min)
python -m pipeline.news.news_scheduler
```

### Via API

```bash
# Liste des articles
curl https://api.marketgps.online/api/news | jq '.total'

# Health du pipeline
curl https://api.marketgps.online/api/news/health | jq

# Compteurs par région
curl https://api.marketgps.online/api/news/regions | jq
```

### Smoke test

```bash
./scripts/smoke_news.sh
```

---

## DÉPLOIEMENT

### Option 1: Docker Compose (recommandé)

```bash
# Rebuild et redéployer
docker compose -f docker-compose.prod.yml up -d --build news-scheduler

# Vérifier les logs
docker logs -f marketgps-news-scheduler
```

### Option 2: Dokploy

1. Accéder à Dokploy dashboard
2. Créer nouveau service `news-scheduler`:
   - Image: utiliser le même Dockerfile que scheduler
   - Command: `python -m pipeline.news.news_scheduler`
   - Env vars:
     - `NEWS_INTERVAL_MINUTES=30`
     - `NEWS_RUN_ON_START=true`
     - `OPENAI_API_KEY=xxx` (requis pour réécriture)
3. Déployer

---

## MONITORING

### Endpoint Health

`GET /api/news/health` retourne:

```json
{
  "status": "healthy",
  "last_run": "2026-01-24T22:30:00",
  "minutes_since_last_run": 5,
  "last_success": true,
  "total_articles": 150,
  "articles_last_24h": 25,
  "history": [...]
}
```

### Métriques fichier

Le scheduler écrit dans `/app/data/news_metrics.json`:

```json
{
  "last_run": "2026-01-24T22:30:00",
  "last_success": true,
  "last_result": {
    "ingest": { "items_new": 15 },
    "publish": { "items_published": 12 }
  }
}
```

---

## SLA ATTENDU

| Métrique | Valeur |
|----------|--------|
| Fréquence refresh | Toutes les 30 minutes |
| Sources actives | 50 |
| Articles nouveaux/jour | 50-100+ |
| Temps moyen pipeline | 2-5 minutes |
| Uptime scheduler | 99.9% |

---

## AJOUTER UNE NOUVELLE SOURCE

1. Éditer `pipeline/news/sources_registry.json`
2. Ajouter un objet:

```json
{
  "name": "Nom de la Source",
  "url": "https://example.com",
  "rss_url": "https://example.com/feed/",
  "type": "rss",
  "country": "XX",
  "region": "WEST|NORTH|CENTRAL|EAST|SOUTH|PAN",
  "language": "en|fr",
  "tags": ["fintech", "startup"],
  "trust_score": 0.8,
  "enabled": true
}
```

3. La source sera automatiquement synchronisée au prochain run

---

## CONCLUSION

Le module news est maintenant **pleinement opérationnel** avec:

- ✅ 50 sources classifiées par région
- ✅ Scheduler toutes les 30 minutes
- ✅ Classification régionale stricte
- ✅ Endpoints health et metrics
- ✅ UI dynamique avec compteurs
- ✅ Docker service dédié
- ✅ Scripts de test

**Prochaine étape**: Déployer le service `news-scheduler` en production.
