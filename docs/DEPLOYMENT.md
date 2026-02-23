# MarketGPS Deployment Guide

## Overview

MarketGPS runs on a **Hostinger VPS** via **Dokploy** with Docker Compose.
Three services: **Frontend** (Next.js), **Backend** (FastAPI), **Scheduler** (Pipeline).

For Dokploy-specific setup, see [deployment/DEPLOY_DOKPLOY.md](deployment/DEPLOY_DOKPLOY.md).

---

## Prerequisites

- Docker 24+ & Docker Compose v2
- 2 GB RAM minimum (4 GB recommended)
- Dokploy or direct SSH access
- Supabase project (auth + database)
- Stripe account (billing)
- Domain names configured (api.marketgps.online, app.marketgps.online)

---

## Environment Setup

1. Copy the template:
   ```bash
   cp env.prod.example .env.prod
   ```

2. Fill in **all** required variables:

   | Variable | Required | Description |
   |----------|----------|-------------|
   | `ENV` | Yes | Must be `production` |
   | `SUPABASE_URL` | Yes | Supabase project URL |
   | `SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |
   | `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
   | `SUPABASE_JWT_SECRET` | Yes | JWT secret for token verification |
   | `ADMIN_KEY` | Yes | Admin dashboard key (generate with `openssl rand -hex 32`) |
   | `INTERNAL_API_KEY` | Yes | Pipeline-to-API key (generate with `openssl rand -hex 32`) |
   | `STRIPE_SECRET_KEY` | Yes | Stripe secret key |
   | `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
   | `STRIPE_PRICE_MONTHLY_ID` | Yes | Stripe monthly price ID |
   | `STRIPE_PRICE_YEARLY_ID` | Yes | Stripe yearly price ID |
   | `SECRET_KEY` | Yes | App secret (generate with `openssl rand -hex 32`) |

3. **Never** commit `.env.prod` to git. It is in `.gitignore`.

---

## Deploy

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Check status
docker compose -f docker-compose.prod.yml ps
```

---

## Post-Deploy Verification

### 1. Smoke Tests

```bash
bash scripts/smoke_test.sh
```

This checks:
- Backend health endpoint
- All major API endpoints (assets, metrics, strategies, barbell, watchlist)
- Frontend pages (landing, login, signup, pricing, dashboard)
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- CORS origin rejection
- Admin endpoint authentication

### 2. Manual Checks

```bash
# Health check
curl -s https://api.marketgps.online/health | jq .

# Security headers
curl -sI https://api.marketgps.online/health | grep -iE "(x-content-type|x-frame|strict-transport|content-security|referrer-policy)"

# CORS rejection test
curl -sI -H "Origin: http://evil.com" https://api.marketgps.online/health | grep -i "access-control"
```

### 3. Logs

```bash
docker compose -f docker-compose.prod.yml logs -f backend --tail 100
docker compose -f docker-compose.prod.yml logs -f frontend --tail 100
```

---

## Rollback

```bash
# Stop current version
docker compose -f docker-compose.prod.yml down

# Deploy previous image
docker compose -f docker-compose.prod.yml up -d
```

Data is persisted in the `marketgps_data` Docker volume, so rollbacks are safe.

---

## Monitoring

Optional Grafana + Prometheus stack:

```bash
docker compose -f docker-compose.monitoring.yml up -d
```

Grafana available at port 3001. Credentials are set via `GF_ADMIN_USER` / `GF_ADMIN_PASSWORD` env vars.

---

## CI/CD

GitHub Actions runs on every push/PR to `main`:

1. **Lint** - `ruff check` (Python) + `eslint` (TypeScript)
2. **Security scan** - `pip-audit`, `npm audit`, `bandit`
3. **Tests** - `pytest tests/ -m "not slow"`
4. **Build** - Docker image build verification

See `.github/workflows/ci.yml` for the full pipeline.
