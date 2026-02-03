# Quick Start - Système de Viralité (5 min)

## Installation (1 min)

```bash
# Optionnel: Ajouter google-generativeai (pour génération de scripts)
pip install google-generativeai>=0.3.0

# OU si dans requirements.txt
pip install -r requirements.txt
```

## Configuration (1 min)

```bash
# Ajouter au fichier .env (optionnel mais recommandé)
export GEMINI_API_KEY="your-api-key-from-ai.google.dev"
```

Ou directement:
```bash
echo "GEMINI_API_KEY=your-api-key" >> .env
```

## Démarrer (1 min)

```bash
cd /backend
uvicorn main:app --reload --port 8000
```

Vérifier: `http://localhost:8000/docs`

## Test des endpoints (2 min)

### 1. Articles viraux (ne requiert pas Gemini)

```bash
curl "http://localhost:8000/api/viral-news/viral?limit=10&days=7"
```

**Réponse**: Liste des articles viraux avec:
- `title` - Titre
- `interactions` - Nombre d'interactions
- `virality_score` - 1.0x = moyenne, 10.0x = 10x la moyenne
- `source_name` - Source
- `region` / `language` - Région et langue

### 2. Statistiques des sources

```bash
curl "http://localhost:8000/api/viral-news/source-stats"
```

**Réponse**: Pour chaque source:
- `avg_interactions` - Moyenne historique
- `median_interactions` - Médiane
- `total_articles` - Nombre total

### 3. Générer un script vidéo (requiert Gemini)

D'abord, récupérer un `article_id`:

```bash
curl "http://localhost:8000/api/viral-news/viral?limit=1" | jq '.[] .article_id'
```

Puis générer le script:

```bash
curl -X POST "http://localhost:8000/api/viral-news/generate-script" \
  -H "Content-Type: application/json" \
  -d '{"article_id":"YOUR_ARTICLE_ID"}'
```

**Réponse**: Script vidéo avec:
- `hook` - Première phrase percutante
- `script_text` - Texte complet (300-500 mots)
- `estimated_duration_seconds` - Durée estimée
- `key_facts` - Faits clés

### 4. Lister les scripts générés

```bash
curl "http://localhost:8000/api/viral-news/scripts?status=draft&limit=5"
```

### 5. Auto-processing

Génère automatiquement des scripts pour les top 5 articles viraux:

```bash
curl -X POST "http://localhost:8000/api/viral-news/auto-process?top_n=5"
```

---

## Tests unitaires

```bash
python -m pytest tests/test_viral_system.py -v
```

Exécute 25+ tests couvrant:
- Détection de viralité
- Estimation d'interactions
- Génération de scripts

---

## Exemples complets

```bash
python viral_system_integration_example.py
```

Lance 4 exemples:
1. Analyse de viralité
2. Estimation d'interactions
3. Génération de scripts
4. Auto-processing

---

## Points clés

### Règles de viralité

**Sources francophones sub-sahariennes** (Sénégal, Côte d'Ivoire, Cameroun, etc.):
- Viral si: `interactions >= 50`

**Autres sources**:
- Viral si: `interactions >= 10x moyenne de la source`

### Exemple

- Jeune Afrique (francophone) + 50 interactions = VIRAL ✓
- Business Daily Africa (anglophone) + 50 interactions = dépend de sa moyenne
  - Si moyenne = 10 → VIRAL (50 >= 10x10)
  - Si moyenne = 100 → NON (50 < 10x100)

---

## FAQ rapide

**Q: Pourquoi "Gemini API key not configured"?**
A: Ajouter `GEMINI_API_KEY` au `.env`. Voir: https://ai.google.dev/

**Q: Comment les articles deviennent viraux?**
A: Le service `ViralityService` les détecte automatiquement. Voir: `/api/viral-news/viral`

**Q: Peut-on éditer les scripts?**
A: Oui! `PUT /api/viral-news/scripts/{script_id}`

**Q: Comment publier les scripts?**
A: `POST /api/viral-news/scripts/{script_id}/publish-to-news`

---

## Architecture simple

```
Requête HTTP
    ↓
viral_news_routes.py
    ↓
ViralityService / VideoScriptService
    ↓
SQLiteDB + Gemini API (optionnel)
    ↓
Réponse JSON
```

---

## Prochaines étapes

1. ✓ Setup & test (fait)
2. Tester avec articles réels
3. Intégrer avec interface frontend
4. Mettre en production

---

**Pour plus**: Voir `VIRAL_NEWS_SYSTEM.md` et `VIRAL_SYSTEM_SETUP.md`
