# ADR-001: FastAPI as Backend Framework

## Status
Accepted

## Context
MarketGPS needs a high-performance REST API serving financial data to a Next.js frontend and a React Native mobile app. Requirements include async I/O, automatic OpenAPI docs, request validation, and a rich middleware ecosystem.

## Decision
Use **FastAPI** with Uvicorn as the ASGI server.

## Rationale
- Native async/await for non-blocking I/O (critical for concurrent API calls to Stripe, Supabase, etc.)
- Automatic OpenAPI/Swagger documentation from Pydantic models
- Built-in request validation via Pydantic v2
- Starlette-based middleware stack allows layered security (rate limiting, input validation, error handling)
- Large ecosystem and active community
- Python aligns with the data pipeline (scoring, ML, pandas)

## Alternatives Considered
- **Express.js/Node** - Would require separate language for pipeline. No native validation.
- **Django REST Framework** - Too heavyweight for an API-only service. Sync by default.
- **Flask** - No native async. Manual validation. Fewer built-in features.

## Consequences
- Backend team must know Python 3.10+
- Middleware ordering is critical (outermost runs first)
- Route files can grow large and need periodic refactoring into packages
