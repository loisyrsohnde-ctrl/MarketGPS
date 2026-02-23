# ADR-003: SQLite as Primary Data Store

## Status
Accepted

## Context
MarketGPS stores asset universe metadata, scoring results, strategies, gamification data, and news articles. The data is write-infrequent / read-heavy, with a single-server deployment on a VPS.

## Decision
Use **SQLite** as the primary data store, accessed via `SQLiteStore` (repository pattern).

## Rationale
- Zero-config, serverless database. No separate database process to manage.
- Excellent read performance for the workload pattern (frequent reads, batch writes)
- Single-file database simplifies backup (just copy the file) and Docker volume management
- WAL mode enables concurrent reads during writes
- Sufficient for current scale (thousands of assets, not millions of concurrent users)
- Docker volume (`marketgps_data`) persists data across container restarts

## Alternatives Considered
- **Supabase PostgreSQL** - Available via Supabase, but adds network latency for every query. Financial data queries are latency-sensitive.
- **PostgreSQL (self-hosted)** - More powerful but adds operational complexity (separate container, backups, migrations) on a single VPS.
- **DuckDB** - Better for analytics but less mature for transactional workloads.

## Consequences
- Single-writer limitation: batch pipeline writes must be coordinated
- No native full-text search (compensated by LIKE queries + application-level filtering)
- Migration management is manual (schema.sql + db_init.py)
- Horizontal scaling would require migrating to PostgreSQL
