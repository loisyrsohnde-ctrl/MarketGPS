# MarketGPS News Pipeline

## Vue d'ensemble

Le pipeline de news MarketGPS agrège des actualités économiques et financières africaines depuis 50+ sources RSS, les réécrit en français avec un style éditorial professionnel via LLM, et les publie dans l'application.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  RSS Sources    │───▶│   Ingester      │───▶│  Raw Items DB   │
│  (50+ feeds)    │    │  (feedparser)   │    │ (news_raw_items)│
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  news_articles  │◀───│   Publisher     │◀───│  LLM Rewriter   │
│     (DB)        │    │  (publish.py)   │    │ (OpenAI/Gemini) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Composants

### 1. Ingester (`pipeline/news/ingest_rss.py`)

- Récupère les flux RSS de toutes les sources activées
- Déduplique via hash du contenu
- Stocke dans `news_raw_items` pour traitement ultérieur

### 2. Publisher (`pipeline/news/publish.py`)

- Lit les items bruts non traités
- Appelle le LLM pour réécriture en français
- Filtre les articles hors-sujet (sport, people, etc.)
- Récupère une image pertinente
- Publie dans `news_articles`

### 3. Scheduler (`pipeline/news/news_scheduler.py`)

- Exécute le pipeline toutes les 30 minutes (configurable)
- Protection contre les exécutions concurrentes (lock file)
- Métriques et historique des exécutions

## Configuration

### Variables d'environnement

```bash
# LLM (au moins un requis pour la réécriture)
OPENAI_API_KEY=sk-...          # Recommandé - meilleure qualité
GEMINI_API_KEY=AIzaSy...       # Alternative gratuite

# Scheduler
NEWS_INTERVAL_MINUTES=30       # Intervalle entre les exécutions
NEWS_RUN_ON_START=true         # Exécuter immédiatement au démarrage
```

### Sources RSS

Les sources sont configurées dans `pipeline/news/sources_registry.json` :

```json
{
  "sources": [
    {
      "name": "Jeune Afrique",
      "url": "https://www.jeuneafrique.com",
      "rss_url": "https://www.jeuneafrique.com/feed/",
      "type": "rss",
      "region": "PAN",
      "language": "fr",
      "enabled": true
    }
  ]
}
```

#### Régions disponibles

| Code | Région |
|------|--------|
| PAN | Panafricain |
| NORTH | Afrique du Nord (Maghreb + Égypte) |
| WEST | Afrique de l'Ouest (UEMOA + Nigeria/Ghana) |
| CENTRAL | Afrique Centrale (CEMAC) |
| EAST | Afrique de l'Est (EAC) |
| SOUTH | Afrique Australe (SADC) |

## Déploiement

### Option A: Cron (Recommandé pour VPS)

Ajouter au crontab :

```bash
# Toutes les 30 minutes de 6h à 21h
*/30 6-21 * * * cd /app/MarketGPS && /app/MarketGPS/scripts/deploy_news_scheduler.sh --once >> /var/log/news_pipeline.log 2>&1
```

### Option B: Daemon (Docker/Systemd)

```bash
# Lancer en mode daemon
./scripts/deploy_news_scheduler.sh --daemon
```

### Option C: Dokploy

Créer un service séparé avec la commande :

```bash
python -m pipeline.news.news_scheduler
```

Variables d'environnement requises :
- `OPENAI_API_KEY` ou `GEMINI_API_KEY`
- `NEWS_INTERVAL_MINUTES=30`

## API Admin

### Déclencher manuellement le pipeline

```bash
# Pipeline complet (ingest + publish)
curl -X POST \
  -H "X-Admin-Key: marketgps-admin-2024" \
  "https://api.marketgps.online/news-admin/pipeline/run?sync=true"

# Ingest uniquement
curl -X POST \
  -H "X-Admin-Key: marketgps-admin-2024" \
  "https://api.marketgps.online/news-admin/pipeline/ingest"

# Publish uniquement
curl -X POST \
  -H "X-Admin-Key: marketgps-admin-2024" \
  "https://api.marketgps.online/news-admin/pipeline/publish"
```

### Vérifier le status

```bash
curl -H "X-Admin-Key: marketgps-admin-2024" \
  "https://api.marketgps.online/news-admin/pipeline/status"
```

### Lister les sources

```bash
curl -H "X-Admin-Key: marketgps-admin-2024" \
  "https://api.marketgps.online/news-admin/pipeline/sources?region=WEST"
```

## Monitoring

### Vérifier la fraîcheur des news

```bash
curl https://api.marketgps.online/api/news/status
```

Réponse :
```json
{
  "status": "ok",
  "total_articles": 1250,
  "minutes_since_update": 15,
  "articles_last_24h": 42,
  "is_fresh": true
}
```

### Logs

Les métriques sont stockées dans `data/news_metrics.json` :

```json
{
  "last_run": "2026-01-30T14:30:00",
  "last_success": true,
  "history": [
    {
      "timestamp": "2026-01-30T14:30:00",
      "success": true,
      "articles_published": 12
    }
  ]
}
```

## Dépannage

### Le pipeline ne s'exécute pas

1. Vérifier que les dépendances sont installées :
   ```bash
   pip install feedparser apscheduler
   ```

2. Vérifier les logs :
   ```bash
   cat data/news_metrics.json
   ```

3. Tester manuellement :
   ```bash
   python -m pipeline.news.news_scheduler --once
   ```

### Les articles ne sont pas réécrits

1. Vérifier la clé API :
   ```bash
   echo $OPENAI_API_KEY  # ou GEMINI_API_KEY
   ```

2. Le pipeline fonctionne en mode fallback sans LLM (articles copiés tels quels)

### Sources RSS en erreur

1. Lister les sources avec erreurs :
   ```bash
   sqlite3 data/marketgps.db "SELECT name, last_error FROM news_sources WHERE last_error IS NOT NULL"
   ```

2. Mettre à jour les URLs RSS dans `sources_registry.json`

## Tables de données

### news_sources

| Colonne | Description |
|---------|-------------|
| id | ID unique |
| name | Nom de la source |
| url | URL du site |
| rss_url | URL du flux RSS |
| region | Code région (PAN, WEST, etc.) |
| enabled | Source activée |
| last_fetched | Dernier fetch réussi |
| last_error | Dernière erreur |

### news_raw_items

| Colonne | Description |
|---------|-------------|
| id | ID unique |
| source_id | FK vers news_sources |
| url | URL de l'article |
| title | Titre original |
| raw_payload | Contenu brut JSON |
| content_hash | Hash pour déduplication |
| processed | Traité par le publisher |

### news_articles

| Colonne | Description |
|---------|-------------|
| id | ID unique |
| slug | URL-friendly slug |
| title | Titre (FR) |
| excerpt | Résumé court |
| content_md | Contenu markdown |
| country | Code pays |
| region | Code région |
| image_url | URL de l'image |
| source_name | Nom de la source |
| is_ai_processed | Traité par LLM |
