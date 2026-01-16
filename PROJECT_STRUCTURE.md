# 📐 Structure du Projet MarketGPS

## Architecture Actuelle (Nettoyée - Jan 2026)

### 🎯 Frontend - Next.js
```
frontend/
├── app/                    # Pages et routing Next.js 13+
├── components/             # Composants React réutilisables
├── lib/                    # Utilitaires et helpers
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript types
├── styles/                 # Styles globaux
├── public/                 # Assets statiques
└── package.json           # Dépendances npm
```

**Port :** 3000 (ou défini par PORT env)  
**Tech :** React 18 + Next.js + TypeScript + Tailwind CSS

---

### ⚙️ Backend - Python/FastAPI
```
backend/
├── main.py                # Entrée principale FastAPI
├── api_routes.py          # Routes principales
├── user_routes.py         # Routes utilisateur
├── security.py            # Authentification/Auth
├── stripe_service.py      # Intégration Stripe
├── supabase_admin.py      # Client Supabase admin
└── requirements.txt       # Dépendances Python
```

**Port :** À définir (généralement 8000 ou 5000)  
**Tech :** Python + FastAPI + Supabase

---

### 📦 Dossiers Partagés
```
core/                      # Logique métier partagée
├── models.py             # Modèles de données
├── config.py             # Configuration
├── compliance.py         # Règles de conformité
├── scoring_specs.py      # Spécifications scoring
└── utils.py              # Utilitaires

providers/                # Providers de données
├── base.py              # Classe de base
├── yfinance_provider.py
├── alpaca.py
├── eodhd.py
└── tiingo.py

auth/                      # Authentification
├── supabase_client.py
├── session.py
└── gating.py

data/                      # Données applicatives
├── logos/                # Logos des entreprises
├── parquet/              # Données parquet
├── sqlite/               # DB SQLite
└── marketgps.db          # DB principale
```

---

### 📚 Resources Annexes
```
pipeline/                  # Scripts ETL/traitement
scripts/                   # Scripts utilitaires
storage/                   # Gestion du stockage
supabase/                  # Migrations SQL Supabase
tests/                     # Tests unitaires
docs/                      # Documentation
```

---

## ⚠️ ARCHIVÉ (Obsolète depuis Jan 2026)

**Streamlit Frontend** (Archivé dans `_archive/streamlit_old/`)
```
_archive/streamlit_old/
├── app/                  # Ancien code Streamlit
├── download_logos.sh     # Scripts d'import
└── download_logos_robust.py
```

**Raison :** Migration vers Next.js pour meilleure performance et flexibilité.

---

## 🚀 Démarrage du Projet

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev        # Port 3000
```

### Backend (FastAPI)
```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/main.py
```

---

## 🔗 Communication Frontend-Backend

**Base URL Backend :** À configurer dans `frontend/lib/` (variables d'environnement)

Vérifier que les appels API pointent vers le bon endpoint :
- Endpoints utilisateur
- Endpoints watchlist (boutons "Suivre")
- Endpoints authentification

---

## 📝 Conventions

- **Frontend :** TypeScript + Tailwind + React hooks
- **Backend :** FastAPI avec Pydantic models
- **Database :** Supabase (PostgreSQL)
- **Auth :** JWT tokens via Supabase

---

**Dernière mise à jour :** 12 Jan 2026  
**Statut :** ✅ Architecture nettoyée, Streamlit archivé
