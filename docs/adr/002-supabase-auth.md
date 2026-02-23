# ADR-002: Supabase for Authentication

## Status
Accepted

## Context
MarketGPS needs user authentication with email/password, session management, and JWT-based API access. The solution must work across web (Next.js) and mobile (React Native).

## Decision
Use **Supabase Auth** with JWT (HS256) for all authentication.

## Rationale
- Managed auth service: email/password, OAuth providers, magic links out of the box
- JWT tokens verified server-side with `python-jose` and `SUPABASE_JWT_SECRET`
- `@supabase/ssr` handles secure cookie-based sessions in Next.js (no localStorage tokens)
- Row-Level Security (RLS) in PostgreSQL for data isolation
- Free tier sufficient for current scale
- Unified auth across web and mobile via `@supabase/supabase-js`

## Alternatives Considered
- **Auth0** - More features but paid at scale. Vendor lock-in.
- **Firebase Auth** - Google ecosystem dependency. No PostgreSQL integration.
- **Custom JWT** - Full control but significant maintenance burden for session management, password hashing, token refresh.

## Consequences
- Backend depends on Supabase JWT secret for token verification
- Auth state lives in Supabase, not in the local SQLite database
- Token refresh and session management delegated to Supabase client libraries
- Dev mode falls back to a test user when `ENV != production` and no token is present
