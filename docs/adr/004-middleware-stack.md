# ADR-004: Six-Layer Middleware Stack

## Status
Accepted

## Context
MarketGPS serves financial data over a public API. Security, observability, and reliability are critical. The API must defend against injection attacks, rate abuse, and common web vulnerabilities while providing structured logging for debugging.

## Decision
Implement a **six-layer middleware stack** in FastAPI, ordered outermost to innermost:

1. **GlobalErrorHandler** - catches all unhandled exceptions, returns structured JSON errors
2. **RequestLogging** - structured JSON logs with X-Request-ID correlation
3. **RateLimit** - sliding-window per-IP rate limiting
4. **InputValidation** - body size limits, query length limits, SQL/XSS injection detection
5. **SecurityHeaders** - OWASP headers (CSP, HSTS, X-Frame-Options, etc.)
6. **CORS** - origin whitelisting with separate production/dev origin lists

## Rationale
- Defense-in-depth: each layer handles a specific concern
- Ordering matters: error handler must be outermost to catch middleware failures
- Rate limiting before input validation prevents resource exhaustion on malformed requests
- Security headers applied to all responses, including error responses
- CORS is innermost because it must run after all other processing

## Alternatives Considered
- **Nginx-level security** - Would handle some concerns (rate limiting, headers) but lacks application-level injection detection.
- **API Gateway (Kong, Traefik)** - Adds infrastructure complexity. Overkill for a single-server deployment.
- **Single combined middleware** - Harder to test, configure, and debug independently.

## Consequences
- Middleware ordering in `main.py` is critical and must not be reordered casually
- Each middleware can be independently tested and configured
- Adding new middleware requires understanding the execution order
- Performance overhead is minimal (~1-2ms per request for the full stack)
