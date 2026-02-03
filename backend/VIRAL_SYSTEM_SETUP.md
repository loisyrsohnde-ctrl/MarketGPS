# Guide de Setup - Système de Viralité et Scripts Vidéo

## Installation rapide (5 min)

### 1. Vérifier les dépendances

Le système utilise:
- `google-generativeai` - Pour Gemini API (génération de scripts)
- `sqlite3` - Déjà inclus en standard Python
- `fastapi` - Déjà dans requirements.txt

Vérifier que `google-generativeai` est dans requirements.txt:

```bash
grep "google-generativeai" /backend/requirements.txt
```

Si absent, l'ajouter:

```bash
echo "google-generativeai>=0.3.0" >> /backend/requirements.txt
```

Puis réinstaller:

```bash
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

**Pour la génération de scripts vidéo (optionnel mais recommandé)**:

```bash
# Dans /backend/.env
export GEMINI_API_KEY="your-api-key-here"
```

Ou ajouter à `.env`:

```
GEMINI_API_KEY=your-api-key-here
```

Pour obtenir une clé API Gemini:
1. Aller sur https://ai.google.dev/
2. Créer un projet
3. Générer une clé API
4. L'ajouter à votre `.env`

### 3. Initialiser la base de données

Les tables sont créées automatiquement au premier appel des services.

Pour initialiser manuellement:

```bash
cd /backend
python -c "
from storage.sqlite_store import SQLiteStore
from services.video_script_service import VideoScriptService

db = SQLiteStore()
video_svc = VideoScriptService(get_db_conn=db._get_conn)
print('✓ Database initialized')
"
```

### 4. Démarrer le serveur

```bash
cd /backend
uvicorn main:app --reload --port 8000
```

Vérifier que les routes sont chargées:

```bash
curl http://localhost:8000/api/viral-news/viral
```

## Configuration détaillée

### Variable GEMINI_API_KEY

**Nécessaire pour**:
- Génération automatique de scripts vidéo
- Endpoint `/api/viral-news/generate-script`
- Endpoint `/api/viral-news/auto-process`

**Sans cette clé**:
- Les endpoints de génération retourneront une erreur
- Les autres endpoints (viralité, stats) fonctionnent normalement

**Comment obtenir la clé**:

1. Aller sur Google AI Studio: https://ai.google.dev/
2. Cliquer "Get API Key"
3. Créer un nouveau projet ou utiliser un existant
4. Générer la clé
5. Copier-coller dans `.env`

**Format .env**:

```bash
# .env
GEMINI_API_KEY=AIzaSyD...votre-clé...
# Ou alternativement:
GOOGLE_API_KEY=AIzaSyD...votre-clé...
```

### Variables système optionnelles

Dans `services/virality_service.py`:

```python
VIRALITY_THRESHOLD = 10  # Multiplicateur pour sources non-prioritaires
MIN_INTERACTIONS_THRESHOLD = 50  # Seuil minimum d'interactions
```

## Tester le système

### Test 1: API Viralité (pas besoin de Gemini)

```bash
# Récupérer les articles viraux
curl "http://localhost:8000/api/viral-news/viral?limit=5&days=7"

# Récupérer les stats des sources
curl "http://localhost:8000/api/viral-news/source-stats?days=30"
```

### Test 2: Génération de scripts (nécessite Gemini)

```bash
# Générer un script pour un article
curl -X POST "http://localhost:8000/api/viral-news/generate-script" \
  -H "Content-Type: application/json" \
  -d '{"article_id": "article_123"}'
```

### Test 3: Exécuter les tests unitaires

```bash
cd /backend
python -m pytest tests/test_viral_system.py -v
```

### Test 4: Lancer les exemples

```bash
cd /backend
python viral_system_integration_example.py
```

## Architecture du système

```
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
├─────────────────────────────────────────────┤
│      viral_news_routes.py                   │
│   (Endpoints /api/viral-news/*)             │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ViralityService  │  │VideoScriptService│
├──────────────────┤  ├──────────────────┤
│- Détect viral    │  │- Generate script │
│- Stats sources   │  │- Save to DB      │
│- Rules engine    │  │- Gemini API      │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         │    ┌────────────────┴────────────┐
         │    │                            │
         └────┼────────────────────────────┤
              │                            │
              ▼                            ▼
    ┌──────────────────┐    ┌──────────────────┐
    │InteractionEst    │    │VideoScriptService│
    ├──────────────────┤    ├──────────────────┤
    │- Est. viral lift │    │- API Gemini      │
    │- Keyword boost   │    │- Prompt template │
    │- Prime time      │    │- Response parse  │
    └────────┬─────────┘    └────────┬─────────┘
             │                       │
             └───────────┬───────────┘
                         │
                    ┌────▼─────┐
                    │SQLiteDB  │
                    ├──────────┤
                    │- news    │
                    │- scripts │
                    │- stats   │
                    └──────────┘
```

## Flux de données

### 1. Articles viraux

```
news_articles (raw)
     ↓
ViralityService.get_viral_articles()
     ↓
InteractionEstimator (optionne)l
     ↓
Filtrage par règles
     ↓
ViralArticle[] (viral uniquement)
```

### 2. Génération de scripts

```
ViralArticle
     ↓
VideoScriptService.generate_script()
     ↓
Récupère article complet
     ↓
Gemini API (Google AI)
     ↓
Parse réponse JSON
     ↓
Sauvegarde en DB
     ↓
VideoScript (status: 'draft')
```

### 3. Publication

```
VideoScript (status: 'draft')
     ↓
Revue manuelle (optionnel)
     ↓
PUT /scripts/{id} (status: 'approved')
     ↓
POST /scripts/{id}/publish-to-news
     ↓
news_articles.summary = script_text
     ↓
Article visible publiquement
```

## Dépannage

### Erreur: "Gemini API key not configured"

**Cause**: `GEMINI_API_KEY` non définie

**Solution**:
```bash
export GEMINI_API_KEY="votre-clé"
# ou dans .env
echo "GEMINI_API_KEY=votre-clé" >> .env
```

### Erreur: "No viral articles found"

**Cause**: Pas d'articles avec assez d'interactions

**Solution**:
- Vérifier que les articles ont une colonne `total_interactions`
- S'assurer que le scraper met à jour cette colonne
- Vérifier les seuils dans `virality_service.py`

### Erreur: "Failed to generate script"

**Causes possibles**:
1. Gemini API key invalide
2. Contenu de l'article trop court
3. Quota Gemini atteint
4. Erreur réseau

**Solution**:
- Vérifier les logs: `tail -f logs/app.log`
- Tester la clé API directement
- Vérifier le quota sur https://ai.google.dev/

### Erreur: "Script not found"

**Cause**: ID de script incorrect

**Solution**:
- Vérifier que le script a bien été généré: `GET /api/viral-news/scripts`
- Vérifier le format: `script_xxxxx`

## Performance et scalabilité

### Optimisations incluses

1. **Index de base de données**
   - Sur `status` pour filtrage rapide
   - Sur `article_id` pour JOIN
   - Sur `created_at DESC` pour tri

2. **Cache des stats**
   - Recalculées à la demande
   - Possible d'ajouter une mise en cache

3. **Batch processing**
   - `/api/viral-news/auto-process` traite plusieurs articles

### Limites de l'API Gemini

- **Rate limit**: ~60 requêtes/minute (gratuit)
- **Tokens**: ~32k tokens par requête
- **Timeout**: 30-60 secondes

Pour la production, recommandé:
- Queue asynchrone (Celery, RQ)
- Rate limiting côté backend
- Cache des scripts générés

## Prochaines étapes

### Court terme (immédiat)

1. Tester les endpoints API
2. Générer les premiers scripts
3. Valider la qualité des scripts

### Moyen terme (1-2 semaines)

1. Intégrer avec le workflow de news
2. Ajouter interface de revue des scripts
3. Analytics d'engagement

### Long terme (1-3 mois)

1. Support text-to-speech (Google Cloud TTS)
2. Publication automatique (YouTube, TikTok)
3. A/B testing de scripts
4. Support multilingue

## Support

**Questions?** Consultez:
- Documentation: `VIRAL_NEWS_SYSTEM.md`
- Code source: `/backend/services/`
- Tests: `/backend/tests/test_viral_system.py`
- Exemples: `/backend/viral_system_integration_example.py`
