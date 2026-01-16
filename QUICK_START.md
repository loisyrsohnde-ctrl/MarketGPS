# 🚀 Quick Start Guide - MarketGPS

## Architecture (Janvier 2026)

```
Frontend: Next.js 13+ (TypeScript + Tailwind)
Backend:  FastAPI (Python)
Database: Supabase + SQLite
```

---

## ⚡ Démarrage Rapide

### 1️⃣ Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# ➜ http://localhost:3000
```

### 2️⃣ Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou: venv\Scripts\activate (Windows)
pip install -r requirements.txt
python main.py
# ➜ http://localhost:8501
```

---

## 🔌 Configuration API

### Frontend → Backend
**Fichier :** `frontend/lib/config.ts`

```typescript
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
};
```

**Variables d'environnement requises :**
```
NEXT_PUBLIC_API_URL=http://localhost:8501
```

### Utilisation dans les composants
```typescript
import { apiClient } from '@/lib/api-client';

// Récupérer des assets
const data = await apiClient.get('/api/assets/top-scored?limit=20');

// Ajouter à watchlist (bouton "Suivre")
await apiClient.post('/api/watchlist/add', {
  asset_id: '123',
  user_id: 'abc123'
});
```

---

## 📋 Endpoints API Backend

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | Santé du serveur |
| `/api/assets/top-scored` | GET | Top assets |
| `/api/assets/search` | GET | Recherche |
| `/api/assets/{id}` | GET | Détails |
| `/api/watchlist/add` | POST | Ajouter watchlist |
| `/api/watchlist/remove` | DELETE | Retirer watchlist |

---

## 🗂️ Structure du Projet

```
MarketGPS/
├── frontend/                # ✅ Next.js (ACTIF)
│   ├── app/                # Pages App Router
│   ├── components/         # Composants React
│   ├── lib/
│   │   ├── config.ts       # ← Config API
│   │   └── api-client.ts   # ← Client HTTP
│   └── package.json
│
├── backend/                # ✅ FastAPI (ACTIF)
│   ├── main.py            # Entrée principal
│   ├── api_routes.py      # Routes données
│   ├── user_routes.py     # Routes utilisateur
│   └── requirements.txt
│
├── core/                   # Logique métier
├── providers/              # Data providers
├── auth/                   # Authentification
├── data/                   # Base de données
│
├── _archive/
│   └── streamlit_old/      # ⚠️ OBSOLÈTE - Ne pas utiliser
│
└── PROJECT_STRUCTURE.md    # Documentation complète
```

---

## 🔍 Dépannage

### ❌ Erreur: "Cannot connect to backend"

1. Vérifier que le backend tourne : `http://localhost:8501/health`
2. Vérifier `NEXT_PUBLIC_API_URL` dans `.env.local` (frontend)
3. Vérifier CORS dans `backend/main.py` (ligne 60-75)

### ❌ Boutons "Suivre" ne fonctionnent pas

1. Vérifier l'endpoint dans `api_routes.py`
2. Vérifier la charge utile JSON
3. Vérifier l'authentification (headers JWT si requis)

### ❌ Port déjà utilisé

```bash
# Tuer le processus sur le port
lsof -ti:3000 | xargs kill -9    # Frontend
lsof -ti:8501 | xargs kill -9    # Backend
```

---

## 📚 Documentation

- **`PROJECT_STRUCTURE.md`** - Architecture complète
- **`CLEANUP_SUMMARY.md`** - Résumé du nettoyage
- **`_archive/streamlit_old/README.md`** - Info archive

---

## ⚠️ À Savoir

✅ **Frontend = Next.js** (exclusivement)  
❌ **Streamlit = OBSOLÈTE** (archivé dans `_archive/`)  
✅ **Backend = FastAPI**  
✅ **Database = Supabase + SQLite**

---

**Dernière mise à jour :** 12 Janvier 2026
