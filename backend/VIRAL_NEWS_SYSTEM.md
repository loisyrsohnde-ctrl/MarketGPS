# Système de Viralité et Scripts Vidéo MarketGPS

## Vue d'ensemble

Ce système détecte les articles d'actualités viraux basées sur les interactions utilisateur et génère automatiquement des scripts vidéo style Hugo Décrypte.

### Composants principaux

1. **ViralityService** - Détection des articles viraux
2. **InteractionEstimator** - Estimation des interactions
3. **VideoScriptService** - Génération de scripts avec Gemini AI
4. **viral_news_routes** - API FastAPI

---

## 1. Service de Viralité (ViralityService)

### Localisation
`/backend/services/virality_service.py`

### Règles de viralité

#### Sources francophones sub-sahariennes (prioritaires)
Pays: Sénégal, Côte d'Ivoire, Mali, Burkina Faso, Niger, Togo, Bénin, Guinée, Cameroun, Gabon, Congo, RDC, Tchad, Centrafrique, Rwanda, Burundi

**Règle**: Articles inclus si `interactions > MIN_INTERACTIONS_THRESHOLD (50)`

#### Autres sources
**Règle**: Articles inclus SEULEMENT si `interactions >= 10x leur moyenne historique`

### Méthodes principales

```python
# Calculer les statistiques des sources (derniers 30 jours)
stats = virality_service.calculate_source_stats(days=30)

# Récupérer les articles viraux
viral_articles = virality_service.get_viral_articles(
    limit=20,
    include_francophone_priority=True,
    virality_multiplier=10.0,
    days=7
)

# Vérifier si une source est prioritaire
is_priority = virality_service.is_francophone_subsaharan(
    source_name="source_name",
    language="fr",
    region="WEST"
)
```

### SourceStats (Dataclass)

```python
@dataclass
class SourceStats:
    source_id: str              # ID unique
    source_name: str            # Nom de la source
    region: str                 # WEST, CENTRAL, NORTH, PANAFRICAIN, etc.
    language: str               # 'fr', 'en'
    avg_interactions: float     # Moyenne historique
    median_interactions: float  # Médiane
    total_articles: int         # Nombre total d'articles
    last_updated: datetime      # Dernière mise à jour
```

### ViralArticle (Dataclass)

```python
@dataclass
class ViralArticle:
    article_id: str             # ID unique
    title: str                  # Titre de l'article
    source_name: str            # Source
    interactions: int           # Nombre total d'interactions
    virality_score: float       # interactions / moyenne_source
    is_viral: bool              # True si respecte les règles
    region: str                 # Région de la source
    language: str               # Langue
    published_at: Optional[str] # Date de publication
    url: str                    # URL de l'article
```

---

## 2. Estimateur d'Interactions (InteractionEstimator)

### Localisation
`/backend/services/interaction_estimator.py`

### Facteurs pris en compte

1. **Trust score de la source** (x1 à x3)
   - Sources de confiance: Jeune Afrique (0.90), Agence Ecofin (0.95)
   - Sources génériques: 0.7

2. **Mots-clés viraux** (x1.0 à x3.0)
   - Mots-clés français/anglais
   - Exemple: "exclusif", "scandal", "breaking", "record"

3. **Heure de publication** (x1.5 si prime time)
   - Prime time: 7h-9h ou 18h-21h

4. **Style du titre** (x1.2 si entre 40-100 caractères)

5. **Chiffres et nombres** (x1.3)

6. **Variance basée sur hash** (0.85-1.15)

### Utilisation

```python
estimator = InteractionEstimator()

# Estimer pour un seul article
interactions = estimator.estimate_interactions(
    title="Révélation: Scandale de Milliards",
    content="Article content...",
    source_name="Jeune Afrique",
    published_at=datetime(2024, 1, 15, 8, 30),
    actual_interactions=None  # Si fourni, utilise cette valeur
)

# Batch estimation
articles = [
    {"title": "...", "content": "...", "source_name": "..."},
    {"title": "...", "content": "...", "source_name": "..."}
]
results = estimator.batch_estimate(articles)
```

---

## 3. Service de Scripts Vidéo (VideoScriptService)

### Localisation
`/backend/services/video_script_service.py`

### Configuration Gemini

Requiert une clé API Gemini:

```bash
export GEMINI_API_KEY="your-api-key"
# OU
export GOOGLE_API_KEY="your-api-key"
```

### Style Hugo Décrypte

**Caractéristiques**:
- Fait principal énoncé **immédiatement** à la première phrase
- Ton direct, factuel, accessible
- Structure: Accroche → Contexte → Développement → Conclusion
- Durée: 300-500 mots (1-2 minutes de voix off)
- ~150 mots/minute

### Méthodes principales

```python
video_svc = VideoScriptService(get_db_conn=db._get_conn)

# Générer un script
script = await video_svc.generate_script(
    article_id="article_123",
    title="Titre de l'article",
    content="Contenu complet...",
    source="Jeune Afrique",
    date="2024-01-15"
)

# Récupérer les scripts
scripts = video_svc.get_scripts(status='draft', limit=20)

# Récupérer un script
script = video_svc.get_script_by_id("script_abc123")

# Mettre à jour un script
success = video_svc.update_script(
    script_id="script_abc123",
    script_text="Nouveau texte...",
    status="reviewed"
)

# Publier vers les actualités
success = video_svc.publish_script_to_news("script_abc123")
```

### VideoScript (Dataclass)

```python
@dataclass
class VideoScript:
    id: str                              # script_xxxxx
    article_id: str                      # Lien vers article
    title: str                           # Titre
    hook: str                            # Première phrase percutante
    script_text: str                     # Script complet
    word_count: int                      # Nombre de mots
    estimated_duration_seconds: int      # Durée estimée
    sources_mentioned: List[str]         # Sources citées
    key_facts: List[str]                 # Faits clés
    status: str                          # 'draft', 'reviewed', 'approved', 'published'
    created_at: str                      # ISO timestamp
    updated_at: str                      # ISO timestamp
```

---

## 4. Routes API

### Localisation
`/backend/viral_news_routes.py`

Préfixe de base: `/api/viral-news`

### Endpoints

#### GET `/api/viral-news/viral`
Récupère les articles viraux.

**Query params**:
```
- limit: 1-100 (défaut: 20)
- francophone_only: boolean (défaut: false)
- min_virality: float >= 0.5 (défaut: 1.0)
- days: 1-30 (défaut: 7)
```

**Exemple**:
```bash
curl "http://localhost:8000/api/viral-news/viral?limit=10&days=7"
```

**Réponse**:
```json
[
  {
    "article_id": "article_123",
    "title": "Révélation Exclusive: Scandale Financier",
    "source_name": "Jeune Afrique",
    "interactions": 2500,
    "virality_score": 15.5,
    "region": "WEST",
    "language": "fr",
    "published_at": "2024-01-15T08:30:00",
    "url": "https://..."
  }
]
```

---

#### GET `/api/viral-news/source-stats`
Récupère les statistiques des sources.

**Query params**:
```
- days: 7-90 (défaut: 30)
```

**Réponse**:
```json
{
  "Jeune Afrique": {
    "source_name": "Jeune Afrique",
    "region": "WEST",
    "language": "fr",
    "avg_interactions": 156.5,
    "median_interactions": 120,
    "total_articles": 45
  }
}
```

---

#### POST `/api/viral-news/generate-script`
Génère un script vidéo pour un article.

**Body**:
```json
{
  "article_id": "article_123"
}
```

**Réponse**:
```json
{
  "id": "script_abc123",
  "article_id": "article_123",
  "title": "Révélation Exclusive: Scandale Financier",
  "hook": "Un scandale impliquant des milliards a été découvert ce matin.",
  "script_text": "Un scandale impliquant des milliards a été découvert ce matin. Le rapport officiellement publié par l'agence d'État révèle...",
  "word_count": 387,
  "estimated_duration_seconds": 154,
  "sources_mentioned": ["Jeune Afrique", "Agence Ecofin"],
  "key_facts": [
    "Milliards impliqués",
    "Découvert ce matin",
    "Rapport officiel"
  ],
  "status": "draft",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

#### GET `/api/viral-news/scripts`
Liste les scripts générés.

**Query params**:
```
- status: 'draft', 'reviewed', 'approved', 'published' (optionnel)
- limit: 1-100 (défaut: 20)
- offset: >= 0 (défaut: 0)
```

**Exemple**:
```bash
curl "http://localhost:8000/api/viral-news/scripts?status=draft&limit=10"
```

---

#### GET `/api/viral-news/scripts/{script_id}`
Récupère un script spécifique.

---

#### PUT `/api/viral-news/scripts/{script_id}`
Met à jour un script.

**Body** (tous optionnels):
```json
{
  "script_text": "Nouveau texte...",
  "hook": "Nouvelle accroche...",
  "status": "reviewed"
}
```

---

#### POST `/api/viral-news/scripts/{script_id}/publish-to-news`
Publie le script vers les actualités publiques.

**Réponse**:
```json
{
  "success": true,
  "message": "Script script_abc123 published successfully"
}
```

---

#### POST `/api/viral-news/auto-process`
Traitement automatique:
1. Identifie les top articles viraux
2. Génère des scripts pour chacun
3. Retourne les scripts générés

**Query params**:
```
- top_n: 1-20 (défaut: 5)
- status_filter: optionnel
```

**Réponse**:
```json
{
  "articles_processed": 5,
  "scripts_generated": 5,
  "scripts": [
    { /* VideoScriptResponse */ }
  ]
}
```

---

## 5. Base de données

### Tables créées

#### `news_source_stats`
Statistiques cachées des sources.

```sql
CREATE TABLE news_source_stats (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    region TEXT,
    language TEXT,
    avg_interactions REAL,
    median_interactions REAL,
    total_articles INTEGER,
    last_calculated TEXT
)
```

#### `video_scripts`
Scripts vidéo générés.

```sql
CREATE TABLE video_scripts (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    title TEXT NOT NULL,
    hook TEXT,
    script_text TEXT NOT NULL,
    word_count INTEGER,
    estimated_duration_seconds INTEGER,
    sources_json TEXT,
    key_facts_json TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (article_id) REFERENCES news_articles(id)
)
```

### Indexes
- `idx_video_scripts_status` - Sur status pour filtrage rapide
- `idx_video_scripts_article` - Sur article_id
- `idx_video_scripts_created` - Sur created_at DESC

---

## 6. Utilisation pratique

### Intégration dans le flux de news

1. **Scraping d'articles** → stored en `news_articles`
2. **ViralityService** → détecte les articles viraux
3. **VideoScriptService** → génère les scripts
4. **Approvals** → revue manuelle des scripts
5. **Publishing** → publie vers le feed public

### Exemple d'intégration

```python
from services.virality_service import ViralityService
from services.video_script_service import VideoScriptService

# Initialiser les services
db = SQLiteStore()
virality_svc = ViralityService(db_conn=db._get_conn)
video_svc = VideoScriptService(get_db_conn=db._get_conn)

# Trouver les articles viraux
viral_articles = virality_svc.get_viral_articles(limit=5)

# Générer les scripts
for article in viral_articles:
    script = await video_svc.generate_script(
        article_id=article.article_id,
        title=article.title,
        # ... autres params
    )

    if script:
        # Script généré, en attente d'approbation
        print(f"Script généré: {script.id}")
```

---

## 7. Configuration et variables d'environnement

### Requises pour Gemini API
```bash
GEMINI_API_KEY=votre-clé-api
# OU
GOOGLE_API_KEY=votre-clé-api
```

### Variables de service (optionnelles)
```python
# Dans virality_service.py
VIRALITY_THRESHOLD = 10  # Multiplicateur pour autres sources
MIN_INTERACTIONS_THRESHOLD = 50  # Seuil minimum

# Dans interaction_estimator.py
# Mappage des trust scores par source
SOURCE_TRUST_SCORES = {
    "Jeune Afrique": 0.90,
    # ...
}
```

---

## 8. Exemples d'exécution

### Lancer les exemples

```bash
cd /backend
python viral_system_integration_example.py
```

### Exemples inclus

1. **Analyse de viralité** - Affiche les top articles et stats des sources
2. **Estimation d'interactions** - Démontre l'algorithme d'estimation
3. **Génération de scripts** - Crée un script avec Gemini
4. **Auto-process** - Traitement complet (détection → scripts)

---

## 9. Dépannage

### Gemini API non configurée

**Erreur**: `Gemini API key not configured`

**Solution**:
```bash
export GEMINI_API_KEY="votre-clé"
# ou dans .env
GEMINI_API_KEY=votre-clé
```

### Pas d'articles viraux détectés

**Cause possible**: Articles sans interactions
**Solution**: Vérifier que `news_articles.total_interactions` est rempli

### Scripts de qualité faible

**Cause**: Contenu de l'article trop court ou peu informatif
**Solution**: Vérifier que `content` a au moins 500 caractères

---

## 10. Roadmap future

- [ ] Support de la génération vidéo (text-to-speech)
- [ ] Analytics des scripts (engagement, views)
- [ ] A/B testing de scripts différents
- [ ] Intégration avec plateformes vidéo (YouTube, TikTok)
- [ ] Support multilingue (scripts en anglais, etc.)
- [ ] Cache des estimations d'interactions
- [ ] Webhook pour notifications de nouveaux articles viraux

---

## Support et documentation

Pour plus d'informations, consultez:
- Code source: `/backend/services/`
- Routes API: `/backend/viral_news_routes.py`
- Exemples: `/backend/viral_system_integration_example.py`
