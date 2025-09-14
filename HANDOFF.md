# Project Handoff: Python Ireland Talk Database

Concise status and next steps for new maintainers. See README.md for quickstart; this doc summarizes what’s working and where to pick up.

---

## TL;DR – Current State

- Backend API (FastAPI) is stable and tested.
  - Talks: list/search (+advanced), get by id, create, list talk types.
  - Taxonomies & tagging: CRUD for taxonomies/values; add/replace/remove tags on talks; get a talk’s tags.
  - Analytics: taxonomy usage and popular tags.
  - Ingestion: Sessionize and Meetup full ingest; incremental sync currently reuses full; SyncStatus tracked per source.
  - Logging: structured request logs with X-Request-ID.
- Data & search
  - SQLite by default (app.db). Postgres supported via DATABASE_URL.
  - Search uses Postgres FTS when on PG; falls back to LIKE on SQLite.
  - Alembic migrations in place and PG-safe (GIN index applied only on PG).
- Tests
  - Test suite is green locally (SQLite). Legacy/archived tests excluded from discovery.
- Frontend
  - Vite/React scaffold exists but not wired to new API yet. Temporary alias routes for tagging kept to ease FE migration.

---

## How to run

- Prereqs: Python 3.11+, Pipenv; Node 20+ for FE; Postgres optional.
- Dev API: `make dev` (http://localhost:8000, docs at /docs)
- Tests: `make test`
- Migrate (if using Postgres): set DATABASE_URL then `make migrate`
- Ingest sample data (API running): `make ingest`
- Frontend (not wired yet): `make frontend`

Environment:

- DATABASE_URL (optional, for Postgres)
- LOG_LEVEL (INFO default)
- INGEST_DISABLE_NETWORK (set to disable external calls during CI/local)

---

## What’s solid vs. pending

Solid

- Core CRUD/search APIs for talks, taxonomies, tags.
- Ingestion job runs end-to-end for Sessionize/Meetup; errors recorded in SyncStatus without failing the job.
- Repo layer supports advanced search by taxonomy (ANY/ALL) and Postgres FTS.

Pending/Partial

- Frontend pages and wiring to the new API.
- Search relevance on PG (no ranking/weights yet).
- Ingestion “delta” logic (sync currently equals full).
- Optional auth/admin flows for managing taxonomies.

---

## Suggested next steps (prioritized)

1. Frontend integration

- Point FE at http://localhost:8000/api/v1; wire talks list/detail/search.
- Hook tagging UI to tag endpoints; then remove temporary alias routes.

2. API contract tooling

- Generate TS types/client from OpenAPI (e.g., openapi-typescript or Orval) and add a Makefile target.

3. Search & data quality

- Add PG ranking (ts_rank + weights); keep SQLite LIKE fallback.
- Improve dedupe/merge across sources; consider stricter uniqueness where safe.

4. Ingestion polish

- Track last-seen IDs/timestamps for incremental sync per source.
- Make provider config explicit; document tokens if needed.

5. CI

- Add GH Actions: pipenv install + tests, optional OpenAPI client generation, and migration smoke test.

---

## Ownership notes

- Active branch: `simplify-arch` (consider merging to default once FE is wired).
- Logging is configured; X-Request-ID is included on responses.
- SQLite used for local/tests; Postgres recommended in prod for FTS performance.

---

## Appendix A – Endpoint map (brief)

Base: `/api/v1`

Talks

- GET `/talks` – list/search (q, talk_type, talk_types, limit, offset)
- GET `/talks/search` – same as list with q
- GET `/talks/search/advanced` – q, talk*types, taxonomy_value_ids, taxonomy*<Name>=Value, match=any|all
- GET `/talks/types` – list distinct talk types
- GET `/talks/{id}` – talk detail
- POST `/talks` – create talk

Taxonomies & tagging (prefix `/talks`)

- GET `/taxonomies` | POST `/taxonomies` | PUT `/taxonomies/{taxonomy_id}` | DELETE `/taxonomies/{taxonomy_id}`
- POST `/taxonomies/{taxonomy_id}/values` | PUT `/taxonomy-values/{value_id}` | DELETE `/taxonomy-values/{value_id}`
- GET `/{talk_id}/tags` | POST `/{talk_id}/tags/add` | PUT `/{talk_id}/tags` | DELETE `/{talk_id}/tags/{value_id}`
- Temporary aliases exist under `/talks/{talk_id}/tags*` (remove after FE updates).

Analytics

- GET `/talks/analytics/taxonomy-usage`
- GET `/talks/analytics/taxonomies/{taxonomy_id}/usage`
- GET `/talks/analytics/popular-tags?limit=`

Ingestion

- POST `/ingest/full` | POST `/ingest/sync` | GET `/ingest/status`

---

## Appendix B – Operations notes

- Migrations: Alembic configured for SQLite by default; PG-safe with conditional GIN index on `talks.search_vector`.
- Search: PG uses `to_tsvector`/`plainto_tsquery`; SQLite falls back to case-insensitive LIKE.
- Sync status: each source has a single row with counters, last error, and timestamps.

---

## Appendix C – Testing

- Run: `make test` (uses Pipenv)
- Tests run on SQLite; legacy archived tests are excluded via `pytest.ini`.
