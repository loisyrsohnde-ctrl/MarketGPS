# 🧹 Nettoyage Complet - Résumé Exécutif

## ✅ Archivage Effectué

### 1. Frontend Streamlit → ARCHIVÉ
```
_archive/streamlit_old/
├── app/                      ← Ancien code Streamlit (pages, componentes, UI)
├── download_logos.sh         ← Scripts dépendants (obsolètes)
├── download_logos_robust.py  ← Utilitaires Streamlit (obsolètes)
└── README.md                 ← Documentation d'archivage
```

**Raison :** Remplacé par Next.js (meilleure perf, UX, architecture)

---

## 📦 Architecture Finale (Propre)

### Stack Frontend : **Next.js 13+** ✅
```
frontend/
├── app/                    # Routes App Router Next.js
├── components/             # Composants React réutilisables  
├── lib/
│   └── config.ts          # ← Configuration centralisée API
├── hooks/                 # Custom React hooks
├── types/                 # Types TypeScript
├── public/                # Assets statiques
└── package.json
```

**Tech :** React 18 + Next.js + TypeScript + Tailwind CSS  
**Port :** 3000 (ou `PORT` env variable)

---

### Stack Backend : **FastAPI** ✅
```
backend/
├── main.py               # Entrée FastAPI + Stripe webhooks
├── api_routes.py         # Routes données (assets, scores, watchlist)
├── user_routes.py        # Routes utilisateur
├── security.py           # Auth & JWT
├── stripe_service.py     # Intégration Stripe
├── supabase_admin.py     # Client Supabase
└── requirements.txt
```

**Tech :** Python + FastAPI + Supabase  
**Port :** 8501 (par défaut, configurable avec `PORT`)  
**Endpoints disponibles :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | Health check |
| `/api/assets/top-scored` | GET | Top assets par score |
| `/api/assets/search` | GET | Recherche d'assets |
| `/api/assets/{id}` | GET | Détails d'un asset |
| `/api/watchlist/add` | POST | Ajouter watchlist |
| `/api/watchlist/remove` | DELETE | Retirer watchlist |
| `/billing/checkout-session` | POST | Session Stripe |
| `/billing/webhook` | POST | Webhook Stripe |

---

### Dossiers Partagés (Inchangés)
```
core/              # Logique métier (models, config, compliance)
providers/         # Data providers (YFinance, Alpaca, EODHD, Tiingo)
auth/              # Authentification (Supabase)
data/              # DB + logos + données
storage/           # Stores (SQLite, Parquet)
pipeline/          # Scripts ETL
```

---

## 🚀 Démarrage du Projet

### Frontend (Next.js)
```bash
cd /Users/cyrilsohnde/Documents/MarketGPS/frontend
npm install
npm run dev        # Lance sur http://localhost:3000
```

### Backend (FastAPI)
```bash
cd /Users/cyrilsohnde/Documents/MarketGPS/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py     # Lance sur http://localhost:8501
```

---

## 🔗 Configuration API Frontend

**Fichier :** `frontend/lib/config.ts`

```typescript
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  ENDPOINTS: {
    WATCHLIST: '/api/watchlist/add',  // ← Pour les boutons "Suivre"
    // ...
  }
};
```

**À configurer :**
- `NEXT_PUBLIC_API_URL` → Port du backend (8501 par défaut)

---

## 📋 Checklist Nettoyage

- ✅ Streamlit archivé dans `_archive/streamlit_old/`
- ✅ Documentation de structure créée (`PROJECT_STRUCTURE.md`)
- ✅ Configuration centralisée créée (`frontend/lib/config.ts`)
- ✅ Ancien code inaccessible pour éviter la confusion
- ✅ Notes d'archivage ajoutées
- ✅ Backend prêt avec endpoints clairs

---

## ⚠️ Points à Vérifier

1. **Boutons "Suivre"** → Vérifier que le frontend appelle le bon endpoint
2. **Backend Port** → S'assurer que le backend tourne sur le bon port (8501)
3. **CORS** → Vérifier que `localhost:3000` est autorisé en CORS
4. **Environment Variables** → Configurer `NEXT_PUBLIC_API_URL`

---

## 📝 Prochaines Étapes

1. ✅ **Archivage** - FAIT
2. 🔧 **Vérifier les endpoints API** - À faire
3. 🧪 **Tester les boutons "Suivre"** - À faire
4. 📚 **Documenter les changements dans git** - À faire

---

**Date :** 12 Janvier 2026  
**Statut :** 🟢 Nettoyage architecture complété
