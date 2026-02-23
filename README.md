# MarketGPS v15 — Institutional-Grade Financial Intelligence Platform

Quantitative scoring engine for equities and ETFs across US & EU markets, with portfolio analytics, strategy building, AI concierge, and real-time news.

> This tool does not constitute investment advice.

---

## Architecture

```
                     +-----------------+
                     |   Next.js 14    |  app.marketgps.online
                     |   (Frontend)    |
                     +--------+--------+
                              |
                              | HTTPS / JWT
                              v
                     +--------+--------+
                     |   FastAPI v15   |  api.marketgps.online
                     |   (Backend)     |
                     +---+----+----+---+
                         |    |    |
               +---------+  |  +---------+
               v             v            v
        +------+---+  +-----+-----+  +---+------+
        | Supabase |  |  SQLite   |  |  Stripe  |
        |  (Auth)  |  |  (Data)   |  | (Billing)|
        +----------+  +-----------+  +----------+
```

### Stack

| Layer       | Technology                                             |
|-------------|--------------------------------------------------------|
| Frontend    | Next.js 14, App Router, Tailwind CSS, Zustand          |
| Backend     | FastAPI, Uvicorn, Pydantic v2, 6-layer middleware stack |
| Auth        | Supabase (JWT HS256)                                   |
| Database    | SQLite (scores, assets, strategies, gamification)      |
| Billing     | Stripe (checkout, portal, webhooks)                    |
| Mobile      | React Native / Expo 54                                 |
| Infra       | Docker, Dokploy, Hostinger VPS                         |
| CI/CD       | GitHub Actions (lint, security scan, tests, build)     |

### Backend Middleware Stack (outermost to innermost)

1. **GlobalErrorHandler** - catches all unhandled exceptions
2. **RequestLogging** - structured JSON logging + X-Request-ID
3. **RateLimit** - sliding-window per-IP rate limiting
4. **InputValidation** - body size, query length, injection detection
5. **SecurityHeaders** - OWASP headers (CSP, HSTS, X-Frame-Options, etc.)
6. **CORS** - origin whitelisting (production vs dev)

### Project Structure

```
MarketGPS/
├── backend/                 # FastAPI application (55 modules)
│   ├── main.py              # App entry + middleware stack
│   ├── api_routes/          # Asset, metrics, watchlist, scoring endpoints
│   ├── admin_routes/        # Admin dashboard endpoints
│   ├── schemas/             # Pydantic request/response models
│   ├── dependencies.py      # Shared auth/subscription dependencies
│   ├── security.py          # JWT verification, user extraction
│   ├── security_config.py   # CORS, CSP, header configuration
│   ├── admin_auth.py        # Admin key verification (timing-safe)
│   ├── env_validator.py     # Startup env validation
│   ├── middleware.py         # Rate limit, logging, error handling
│   └── storage/             # SQLite store, data access layer
├── frontend/                # Next.js 14 application
│   ├── app/                 # App Router pages (19 routes)
│   ├── components/          # Reusable UI components
│   ├── lib/                 # API clients, auth, utilities
│   └── next.config.js       # Security headers, CSP
├── mobile/                  # React Native / Expo 54
├── pipeline/                # Data pipeline (scoring, news, universe)
├── tests/                   # Pytest test suite
│   ├── test_security.py     # 17 security tests
│   ├── test_auth_flow.py    # 15 auth tests
│   └── test_api_integration.py
├── scripts/                 # Smoke tests, deployment scripts
├── docs/                    # Documentation
│   ├── features/            # Feature documentation
│   ├── audit/               # Security audit reports
│   ├── deployment/          # Deployment guides
│   └── changelog/           # Release notes
├── docker-compose.prod.yml  # Production Docker Compose
├── Dockerfile.backend       # Backend container (non-root, health check)
├── .github/workflows/ci.yml # CI pipeline
└── .pre-commit-config.yaml  # Ruff, detect-secrets hooks
```

---

## Quick Start (Development)

### Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase project (for auth)

### Backend

```bash
cd MarketGPS/backend
cp .env.example .env           # Configure env vars
pip install -r requirements.txt
uvicorn main:app --reload --port 8501
```

API docs available at `http://localhost:8501/docs` (Swagger) or `/redoc`.

### Frontend

```bash
cd MarketGPS/frontend
cp .env.example .env.local     # Configure NEXT_PUBLIC_* vars
npm install
npm run dev
```

### Run Tests

```bash
cd MarketGPS
python3 -m pytest tests/ -v
```

---

## Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full guide.

```bash
# Quick deploy via Dokploy on Hostinger VPS
cp env.prod.example .env.prod  # Fill in all secrets
docker compose -f docker-compose.prod.yml up -d

# Verify
bash scripts/smoke_test.sh
```

---

## Scoring System

| Pillar   | Description               | Weight (Equity) | Weight (ETF) |
|----------|---------------------------|-----------------|--------------|
| Value    | P/E, margins, ROE         | 30%             | N/A          |
| Momentum | RSI, price vs SMA200      | 40%             | 60%          |
| Safety   | Volatility, max drawdown  | 30%             | 40%          |

Each asset receives a composite score (0-100) with a **data confidence** indicator.

---

## API Documentation

Interactive docs are auto-generated from Pydantic schemas:

- **Swagger UI**: `https://api.marketgps.online/docs`
- **ReDoc**: `https://api.marketgps.online/redoc`

Key endpoint groups: Assets, Strategies, Portfolio, Billing, News, Admin.

---

## Security

- JWT authentication via Supabase (HS256)
- Timing-safe admin key comparison (`secrets.compare_digest`)
- OWASP security headers on all responses
- Input validation middleware (injection detection)
- Rate limiting (sliding window per-IP)
- CORS origin whitelisting (no `*`, no localhost in production)
- CSP without `unsafe-eval`
- Environment validation at startup (no hardcoded secrets)
- Pre-commit hooks with `detect-secrets`

---

## License

Proprietary. All rights reserved.
