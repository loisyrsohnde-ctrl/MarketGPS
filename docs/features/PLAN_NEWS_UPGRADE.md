# Plan d'amélioration du module Actualités

## Objectifs
1. **Page d'archives** — Accès aux actualités anciennes (1 mois de rétention)
2. **Système de pertinence** — Scoring hybride pour mettre en avant les articles importants
3. **Notifications Breaking News** — Alertes in-app + email pour actualités urgentes
4. **Nouvelles sources** — Ajouter Africa Intelligence et Africa Tech Business
5. **Recherche améliorée** — Tri par pertinence

---

## Phase 1 : Système de Scoring de Pertinence

### 1.1 Modification du schéma de base de données
**Fichier:** `storage/migrations/add_news_engagement.sql`

```sql
-- Ajouter les colonnes de scoring à news_articles
ALTER TABLE news_articles ADD COLUMN engagement_score REAL DEFAULT 0.0;
ALTER TABLE news_articles ADD COLUMN save_count INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN is_breaking_news INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN importance_level TEXT DEFAULT 'normal';
-- importance_level: 'breaking', 'high', 'normal', 'low'

-- Index pour le tri par pertinence
CREATE INDEX IF NOT EXISTS idx_news_engagement ON news_articles(engagement_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_breaking ON news_articles(is_breaking_news, published_at DESC);
```

### 1.2 Calcul du score de pertinence
**Fichier:** `pipeline/news/scoring.py` (nouveau)

Formule de scoring :
```
engagement_score =
  0.30 × trust_score (source)
+ 0.25 × content_quality_score
+ 0.25 × freshness_score
+ 0.20 × user_engagement_score
```

Où :
- **trust_score** : Déjà présent dans sources_registry.json (0.0-1.0)
- **content_quality_score** : Basé sur longueur, entités nommées, présence d'images
- **freshness_score** : Décroît avec le temps (1.0 pour < 1h, 0.5 pour < 24h, etc.)
- **user_engagement_score** : save_count normalisé

### 1.3 Détection Breaking News
Critères pour marquer un article comme "Breaking News" :
- trust_score source ≥ 0.9
- Mots-clés urgents : "breaking", "urgent", "alerte", "exclusif", "vient de"
- Publication < 2 heures
- Score engagement > 0.8

---

## Phase 2 : Page d'Archives

### 2.1 Nouvelle page archives
**Fichier:** `frontend/app/news/archives/page.tsx` (nouveau)

Fonctionnalités :
- Liste paginée de TOUS les articles (1 mois)
- Filtres : région, pays, tags, période
- Tri : date, pertinence
- Design cohérent avec l'existant (cards compactes)
- Pagination : 30 articles par page

### 2.2 Bouton "Voir plus d'actualités"
**Fichier:** `frontend/app/news/page.tsx` (modifier)

Ajouter en bas de la page principale :
```tsx
<Link href="/news/archives" className="...">
  Voir toutes les actualités →
</Link>
```

### 2.3 Endpoint API archives
**Fichier:** `backend/news_routes.py` (modifier)

```python
@router.get("/api/news/archives")
async def get_news_archives(
    page: int = 1,
    page_size: int = 30,
    region: str = None,
    country: str = None,
    tag: str = None,
    date_from: str = None,  # Format: YYYY-MM-DD
    date_to: str = None,
    sort_by: str = "date"   # "date" ou "relevance"
):
```

---

## Phase 3 : Système de Notifications

### 3.1 Table notifications news
**Fichier:** `storage/migrations/add_news_notifications.sql`

```sql
CREATE TABLE IF NOT EXISTS news_alerts (
    id INTEGER PRIMARY KEY,
    article_id INTEGER REFERENCES news_articles(id),
    alert_type TEXT NOT NULL,  -- 'breaking', 'high_importance', 'trending'
    title TEXT NOT NULL,
    message TEXT,
    sent_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_news_alert_prefs (
    user_id TEXT PRIMARY KEY,
    receive_breaking_news INTEGER DEFAULT 1,
    receive_high_importance INTEGER DEFAULT 1,
    email_enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Service de notifications
**Fichier:** `backend/news_notifications.py` (nouveau)

- Vérifier les nouveaux articles avec is_breaking_news = 1
- Envoyer notification in-app via le système existant
- Envoyer email via Resend (déjà configuré)
- Respecter les préférences utilisateur

### 3.3 UI Notifications
**Fichier:** `frontend/components/news/BreakingNewsBanner.tsx` (nouveau)

Bannière en haut de la page news :
```
🔴 BREAKING NEWS | [Titre de l'article] | Il y a X min
```

Intégration avec le NotificationCenter existant.

---

## Phase 4 : Nouvelles Sources

### 4.1 Ajouter dans sources_registry.json
**Fichier:** `pipeline/news/sources_registry.json`

```json
{
  "name": "Africa Intelligence",
  "url": "https://www.africaintelligence.com",
  "rss_url": "https://www.africaintelligence.com/rss",
  "type": "rss",
  "country": null,
  "region": "PAN",
  "language": "en",
  "tags": ["business", "politics", "intelligence"],
  "trust_score": 0.95,
  "enabled": true
},
{
  "name": "Africa Tech Business",
  "url": "https://africatechbusiness.com",
  "rss_url": "https://africatechbusiness.com/feed/",
  "type": "rss",
  "country": null,
  "region": "PAN",
  "language": "en",
  "tags": ["tech", "startup", "business"],
  "trust_score": 0.8,
  "enabled": true
}
```

---

## Phase 5 : Recherche Améliorée

### 5.1 Endpoint recherche avec pertinence
**Fichier:** `backend/news_routes.py` (modifier)

Améliorer `/api/news` pour supporter :
- `sort_by=relevance` : tri par engagement_score
- `sort_by=date` : tri par date (défaut actuel)
- Recherche full-text améliorée

### 5.2 UI Recherche
**Fichier:** `frontend/app/news/page.tsx` (modifier)

Ajouter :
- Barre de recherche visible
- Toggle "Trier par : Date | Pertinence"
- Filtres rapides par tags populaires

---

## Ordre d'implémentation

| Étape | Description | Fichiers | Durée estimée |
|-------|-------------|----------|---------------|
| 1 | Migration DB + scoring | migrations, scoring.py | 30 min |
| 2 | Modifier ingest/publish pour calculer scores | ingest_rss.py, publish.py | 45 min |
| 3 | Ajouter les 2 nouvelles sources | sources_registry.json | 5 min |
| 4 | Page archives + endpoint | archives/page.tsx, news_routes.py | 45 min |
| 5 | Bouton "Voir plus" sur page principale | news/page.tsx | 15 min |
| 6 | Système notifications | news_notifications.py, tables | 45 min |
| 7 | Bannière Breaking News | BreakingNewsBanner.tsx | 30 min |
| 8 | Recherche améliorée + tri | news_routes.py, page.tsx | 30 min |

**Total estimé : ~4 heures**

---

## Fichiers à créer
- `storage/migrations/add_news_engagement.sql`
- `pipeline/news/scoring.py`
- `frontend/app/news/archives/page.tsx`
- `backend/news_notifications.py`
- `frontend/components/news/BreakingNewsBanner.tsx`

## Fichiers à modifier
- `pipeline/news/sources_registry.json`
- `pipeline/news/publish.py`
- `backend/news_routes.py`
- `frontend/app/news/page.tsx`
- `storage/sqlite_store.py`
