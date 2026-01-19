# MarketGPS - Déploiement Dokploy

Guide complet pour déployer MarketGPS sur Dokploy (ou tout VPS avec Docker).

---

## 📋 Table des Matières

1. [Architecture](#architecture)
2. [Prérequis](#prérequis)
3. [Configuration Dokploy](#configuration-dokploy)
4. [Variables d'Environnement](#variables-denvironnement)
5. [Déploiement Étape par Étape](#déploiement-étape-par-étape)
6. [Vérification](#vérification)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture

MarketGPS est composé de **3 services Docker** :

```
┌─────────────────────────────────────────────────────────────────┐
│                         VPS / Dokploy                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   Frontend   │   │   Backend    │   │  Scheduler   │        │
│  │   (Next.js)  │   │   (FastAPI)  │   │  (Pipeline)  │        │
│  │   :3000      │   │   :8000      │   │   (no port)  │        │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘        │
│         │                  │                   │                │
│         └──────────────────┴───────────────────┘                │
│                            │                                    │
│                    ┌───────┴───────┐                           │
│                    │    Volume     │                           │
│                    │ marketgps_data│                           │
│                    │  - SQLite DB  │                           │
│                    │  - Parquet    │                           │
│                    │  - Logos      │                           │
│                    └───────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

| Service | Description | Port | Healthcheck |
|---------|-------------|------|-------------|
| **frontend** | Next.js App | 3000 | `GET /` |
| **backend** | FastAPI API | 8000 | `GET /health` |
| **scheduler** | Pipeline jobs | - | logs |

---

## ✅ Prérequis

### Sur votre VPS
- Docker 24+ et Docker Compose v2
- Dokploy installé (ou accès SSH)
- 2 Go RAM minimum (4 Go recommandé)
- 20 Go d'espace disque

### Domaines et DNS
- Un domaine principal (ex: `marketgps.com`)
- Sous-domaine pour l'API (ex: `api.marketgps.com`)
- DNS configuré pointant vers votre VPS

### Services Externes
- **Supabase** : Compte et projet créé
- **Stripe** (optionnel) : Compte et clés API

---

## ⚙️ Configuration Dokploy

### Service 1: Backend (API)

Dans Dokploy, créer un nouveau service avec ces paramètres :

| Champ | Valeur |
|-------|--------|
| **Name** | `marketgps-backend` |
| **Build Type** | Dockerfile |
| **Dockerfile Path** | `backend/Dockerfile` |
| **Docker Context** | `backend` |
| **Port Mapping** | `8000:8000` |
| **Healthcheck URL** | `http://localhost:8000/health` |
| **Domain** | `api.yourdomain.com` |

**Volumes à configurer :**
```
marketgps_data:/app/data
./data/marketgps.db:/app/data/marketgps.db
```

---

### Service 2: Frontend

| Champ | Valeur |
|-------|--------|
| **Name** | `marketgps-frontend` |
| **Build Type** | Dockerfile |
| **Dockerfile Path** | `frontend/Dockerfile` |
| **Docker Context** | `frontend` |
| **Port Mapping** | `3000:3000` |
| **Healthcheck URL** | `http://localhost:3000/` |
| **Domain** | `yourdomain.com` ou `app.yourdomain.com` |

**Build Args (IMPORTANT - injectés au build) :**
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=https://yourproject.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

### Service 3: Scheduler

| Champ | Valeur |
|-------|--------|
| **Name** | `marketgps-scheduler` |
| **Build Type** | Dockerfile |
| **Dockerfile Path** | `pipeline/Dockerfile` |
| **Docker Context** | `.` (racine) |
| **Port Mapping** | aucun |
| **Depends On** | `marketgps-backend` |

**Volumes (partagés avec backend) :**
```
marketgps_data:/app/data
./data/parquet:/app/data/parquet
./data/marketgps.db:/app/data/marketgps.db
```

---

## 🔐 Variables d'Environnement

### Backend

| Variable | Description | Exemple |
|----------|-------------|---------|
| `CORS_ORIGINS` | Origines autorisées | `https://yourdomain.com` |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé service Supabase | `eyJ...` |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook | `whsec_...` |
| `DATABASE_PATH` | Chemin SQLite | `/app/data/marketgps.db` |

### Frontend (Build Args)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | URL API backend | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_API_BASE_URL` | URL API (alias) | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | URL Supabase | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key | `eyJ...` |

### Scheduler

| Variable | Description | Exemple |
|----------|-------------|---------|
| `MARKET_SCOPE` | Scope marché | `US_EU` |
| `RUN_ON_START` | Run au démarrage | `false` |
| `TZ` | Timezone | `America/New_York` |

---

## 🚀 Déploiement Étape par Étape

### Étape 1: Préparer le serveur

```bash
# Connexion SSH
ssh user@your-vps

# Créer le répertoire data
mkdir -p /path/to/marketgps/data/parquet
mkdir -p /path/to/marketgps/data/logos

# Copier la base de données (si existante)
scp data/marketgps.db user@your-vps:/path/to/marketgps/data/

# Copier les fichiers Parquet (si nécessaire)
rsync -avz --progress data/parquet/ user@your-vps:/path/to/marketgps/data/parquet/
```

### Étape 2: Configurer l'environnement

```bash
# Copier le template
cp env.prod.example .env.prod

# Éditer avec vos valeurs
nano .env.prod
```

### Étape 3: Déployer avec Docker Compose (alternative à Dokploy)

```bash
# Lancer tous les services
./scripts/prod_up.sh

# Vérifier le statut
./scripts/prod_status.sh
```

### Étape 4: Appliquer les migrations

```bash
./scripts/prod_migrate.sh
```

---

## ✔️ Vérification

### Checklist Pré-Déploiement

- [ ] DNS configuré (A record → IP du VPS)
- [ ] Certificat TLS/SSL (Dokploy le gère automatiquement)
- [ ] Variables d'environnement remplies
- [ ] Base de données copiée ou initialisée
- [ ] Fichiers Parquet synchronisés (ou volume configuré)

### Checklist Post-Déploiement

- [ ] Frontend accessible : `https://yourdomain.com`
- [ ] Backend health : `https://api.yourdomain.com/health` → `{"status":"healthy"}`
- [ ] Login fonctionnel (Supabase)
- [ ] Dashboard charge les données
- [ ] Scheduler logs : pas d'erreurs

### Tests Manuels

```bash
# Test backend health
curl https://api.yourdomain.com/health

# Test API assets
curl https://api.yourdomain.com/api/assets/top-scored

# Test frontend
curl -I https://yourdomain.com
```

---

## 🔧 Maintenance

### Voir les logs

```bash
# Tous les services
./scripts/prod_logs.sh

# Un service spécifique
./scripts/prod_logs.sh backend
./scripts/prod_logs.sh scheduler
```

### Redémarrer un service

```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Mettre à jour

```bash
# Pull les changements
git pull

# Rebuild et redémarrer
./scripts/prod_up.sh
```

### Backup

```bash
# Backup SQLite
docker compose -f docker-compose.prod.yml exec backend \
  cp /app/data/marketgps.db /app/data/marketgps.db.backup

# Copier localement
docker cp marketgps-backend:/app/data/marketgps.db ./backup/
```

---

## 🐛 Troubleshooting

### Le frontend ne se connecte pas au backend

1. Vérifier que `NEXT_PUBLIC_API_URL` pointe vers le bon domaine
2. Vérifier CORS dans le backend (`CORS_ORIGINS`)
3. Vérifier que le backend est healthy

### Le scheduler ne s'exécute pas

1. Vérifier les logs : `./scripts/prod_logs.sh scheduler`
2. Vérifier le timezone : doit être `America/New_York`
3. Vérifier que le volume data est monté correctement

### Erreur "Database is locked"

Cause : Le scheduler et le backend écrivent simultanément.

Solution : Utiliser WAL mode pour SQLite :
```sql
PRAGMA journal_mode=WAL;
```

### Out of memory

Augmenter les workers uvicorn ou la RAM du VPS.
Dans le Dockerfile backend, réduire les workers :
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

---

## 📊 Minimum Viable Deploy (Sans Stripe)

Pour un déploiement minimal sans billing :

1. **Ignorer** les variables Stripe (`STRIPE_*`)
2. Le backend fonctionnera sans le module billing
3. Les endpoints `/billing/*` retourneront 503

Variables minimales requises :
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `CORS_ORIGINS`

---

## 📁 Structure des Fichiers Docker

```
MarketGPS/
├── frontend/
│   └── Dockerfile          # Next.js multi-stage build
├── backend/
│   └── Dockerfile          # FastAPI production
├── pipeline/
│   ├── Dockerfile          # Scheduler service
│   └── prod_scheduler.py   # US open/close scheduler
├── docker-compose.prod.yml # Orchestration 3 services
├── .dockerignore           # Fichiers exclus du build
├── env.prod.example        # Template variables d'env
├── scripts/
│   ├── prod_up.sh          # Démarrer
│   ├── prod_down.sh        # Arrêter
│   ├── prod_logs.sh        # Logs
│   ├── prod_status.sh      # Statut
│   └── prod_migrate.sh     # Migrations DB
└── DEPLOY_DOKPLOY.md       # Ce fichier
```

---

## 📞 Support

En cas de problème :
1. Consulter les logs : `./scripts/prod_logs.sh`
2. Vérifier le statut : `./scripts/prod_status.sh`
3. Tester le health : `curl localhost:8000/health`

---

*Dernière mise à jour : Janvier 2026*
