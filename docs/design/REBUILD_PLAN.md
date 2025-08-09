# Rebuild Plan: Simple Architecture with Feature Parity

This document defines the target architecture, milestones, and task breakdown to reach parity with the archived CLEAN_ARCH implementation while staying beginner-friendly and contributor-focused.

## Goals (Parity Scope)

- Data ingestion (on-demand) from lib/engine
  - Sessionize events, Meetup groups
  - Full ingest and incremental refresh endpoints
- Talks search & retrieval
  - Text search (title/description), type filter, basic pagination
- Tagging
  - Auto-tag extraction (keyword-based)
  - Manual taxonomy tagging
- Taxonomy management
  - CRUD for taxonomies and values
  - Talk ↔ taxonomy_value relationship
- Storage
  - SQLAlchemy with SQLite by default
  - PostgreSQL via DATABASE_URL without code changes
- Testing
  - Fast unit tests (tagging, services)
  - API tests (FastAPI TestClient)
  - DB tests on SQLite
  - Optional Postgres tests via env/compose

---

## Architecture (Simple First)

One path: API → service (functions) → DB (SQLAlchemy functions).

```mermaid
flowchart LR
  FE[Frontend] --> API[FastAPI Routers]
  API --> SRV[Service Functions]
  SRV --> DB[DB Layer (SQLAlchemy)]
  SRV --> ENG[lib/engine (Meetup, Sessionize)]

  subgraph Storage
    SQL[SQLite (default)]
    PG[PostgreSQL (DATABASE_URL)]
  end

  DB --> SQL
  DB --> PG
```

Key principles:

- Functions over classes for services and DB helpers
- No interfaces/DI; keep file layout predictable
- Shared SQLAlchemy models for SQLite/Postgres switch
- Keep ingestion logic in lib/engine; services orchestrate

---

## Frontend Alignment (Endpoints & Shapes)

Current frontend (frontend/src) expects these behaviors:

- Base URL: http://localhost:8000/api/v1
- Search endpoint: GET /talks/search with query params q, talk_types (multi), tags (multi)
- Search response shape: { talks: [...], total?: number }
- Item detail: GET /talks/search?q=id:<talk_id> (backend should support id: prefix or provide GET /talks/{id} and update FE)
- Talk types: GET /talks/types -> { types: string[] }
- Taxonomy management (all under /talks prefix):
  - GET /talks/taxonomies
  - POST /talks/taxonomies
  - PUT /talks/taxonomies/{id}
  - DELETE /talks/taxonomies/{id}
  - POST /talks/taxonomies/{id}/values
  - PUT /talks/taxonomy-values/{value_id}
  - DELETE /talks/taxonomy-values/{value_id}
- Talk tagging (note: FE currently builds URLs like /talks/talks/{id}/... which likely needs a small FE fix):
  - GET /talks/{id}/tags
  - POST /talks/{id}/tags/add
  - PUT /talks/{id}/tags
  - DELETE /talks/{id}/tags/{value_id}
  - POST /talks/bulk-tag-operations
- Analytics:
  - GET /talks/analytics/taxonomy-usage
  - GET /talks/analytics/popular-tags?limit=20
  - GET /talks/analytics/taxonomies/{taxonomyId}/usage
- Advanced search:
  - GET /talks/search/advanced?query=...&taxonomy\_<TaxName>=Value (repeatable)

Action:

- Align backend endpoints and shapes to the above to minimize FE changes.
- Fix small FE bug: remove the extra '/talks' segment when building talk tag URLs, or provide temporary backend aliases.

---

## Proposed Layout

- backend/

  - main.py (FastAPI app + router mounts)
  - api/
    - routers/
      - health.py (GET /health, GET /version)
      - talks.py (GET /talks, GET /talks/search, GET /talks/{id}, POST /talks, GET /talks/types, GET /talks/search/advanced)
      - taxonomies.py (mounted under /talks: CRUD endpoints: /talks/taxonomies, /talks/taxonomy-values/\*)
      - ingest.py (POST /ingest/full, POST /ingest/sync)
  - app/
    - service.py (create_talk, search_talks, list_taxonomies, update_talk_tags)
    - tagging.py (extract_auto_tags)
  - db/
    - engine.py (get_engine, get_sessionmaker; SQLite by default, Postgres via env)
    - models.py (Talk, Taxonomy, TaxonomyValue, TalkTaxonomyValue association)
    - repo.py (save_talk, find_talk, search_talks, taxonomy CRUD, tagging helpers, analytics helpers)

- lib/engine/ (keep)

  - meetup.py, sessionize.py, data_pipeline.py (reuse via service orchestration)

- tests/
  - app/test_tagging.py
  - api/test_talks_api.py
  - api/test_taxonomies_api.py
  - db/test_repo.py (SQLite)
  - integration/test_ingest.py (optional; can be slow)

---

## Data Model (initial)

Tables (SQLAlchemy models):

- talks

  - id (TEXT/UUID PK)
  - title (TEXT, indexed)
  - description (TEXT)
  - talk_type (TEXT)
  - speaker_names (JSON on PG, TEXT JSON on SQLite)
  - source_url (TEXT)
  - created_at, updated_at (TIMESTAMP)
  - source_type, source_id (TEXT) for upsert/duplicate detection
  - last_synced, source_updated_at (TIMESTAMP) for sync tracking
  - type_specific_data (JSON on PG, TEXT JSON on SQLite) for event_name, venue_name, group_name, topics, hosts, etc.
  - search_vector (TEXT) concatenated searchable text (PG index later)
  - auto_tags (JSON on PG, TEXT JSON on SQLite)

- taxonomies

  - id (INT PK)
  - name (TEXT, unique)
  - description (TEXT)
  - created_by (TEXT), is_system (BOOL/TEXT)
  - created_at

- taxonomy_values

  - id (INT PK)
  - taxonomy_id (FK)
  - value (TEXT)
  - description (TEXT)
  - color (TEXT)
  - created_at

- talk_taxonomy_values (association)

  - talk_id (TEXT FK)
  - taxonomy_value_id (INT FK)
  - UNIQUE(talk_id, taxonomy_value_id)

- sync_status (optional but recommended)
  - id (INT PK)
  - source_type (TEXT, unique)
  - last_sync_time, last_successful_sync (TIMESTAMP)
  - sync_count, error_count (INT)
  - last_error (TEXT)
  - created_at, updated_at

Notes:

- Use JSON/JSONB on PG; encode/decode JSON to TEXT on SQLite.
- Add indexes: talks(title), talks(talk_type), talks(created_at DESC), and PG GIN index on to_tsvector(search_vector) later.

---

## Endpoints (MVP)

- Health
  - GET /api/v1/health → { status }
  - GET /api/v1/version → { version }
- Talks
  - GET /api/v1/talks?q=&talk_types=&tags=&limit=&offset= → { talks, total }
  - GET /api/v1/talks/search?q=&talk_types=&tags=&limit=&offset= → { talks, total }
  - GET /api/v1/talks/{id} → single talk (optional if we support q=id:<id>)
  - GET /api/v1/talks/types → { types: string[] }
  - GET /api/v1/talks/search/advanced?query=&taxonomy\_<Name>=Value → { talks, total }
  - POST /api/v1/talks { title, description, talk_type?, event_name?, source_type?, source_id? } → { id }
- Taxonomies (under /api/v1/talks path to match FE)
  - GET /api/v1/talks/taxonomies
  - POST /api/v1/talks/taxonomies { name, description }
  - PUT /api/v1/talks/taxonomies/{id}
  - DELETE /api/v1/talks/taxonomies/{id}
  - POST /api/v1/talks/taxonomies/{id}/values { value, color? }
  - PUT /api/v1/talks/taxonomy-values/{id}
  - DELETE /api/v1/talks/taxonomy-values/{id}
- Tags on talks
  - GET /api/v1/talks/{talk_id}/tags → grouped by taxonomy
  - POST /api/v1/talks/{talk_id}/tags/add { value_ids: number[] }
  - PUT /api/v1/talks/{talk_id}/tags { value_ids: number[] }
  - DELETE /api/v1/talks/{talk_id}/tags/{value_id}
  - POST /api/v1/talks/bulk-tag-operations { operations: [...] }
- Analytics (later milestone)
  - GET /api/v1/talks/analytics/taxonomy-usage
  - GET /api/v1/talks/analytics/popular-tags?limit=
  - GET /api/v1/talks/analytics/taxonomies/{taxonomyId}/usage
- Ingestion
  - POST /api/v1/ingest/full
  - POST /api/v1/ingest/sync
  - GET /api/v1/ingest/status (aggregate sync statuses per source)

---

## Milestones & Tasks (updated)

Milestone 1: Baseline API + SQLite (1–2 days)

- [x] Add db/engine.py (SQLite default, Postgres via DATABASE_URL)
- [x] Add db/models.py (talks, taxonomies, taxonomy_values, association)
- [x] Auto-create tables at startup
- [x] Implement repo.py: save_talk, find_talk, search_talks (LIKE), basic pagination
- [x] Wire service.py to repo
- [x] Talks router: GET /talks, GET /talks/search, GET /talks/{id}, POST /talks, GET /talks/types
- [x] Ensure search response shape is { talks, total } to match FE
- [x] Tests: app/test_tagging.py; api/test_talks_api.py (SQLite)

Milestone 2: Taxonomy CRUD + Tagging (1–2 days)

- [x] Repo: taxonomy CRUD, list_taxonomies, talk↔value association helpers
- [x] Router: /talks/taxonomies*, /talks/taxonomy-values/*
- [x] Talk tag endpoints: GET /talks/{id}/tags, POST add, PUT replace, DELETE one
- [x] Tests: api/test_taxonomies_api.py; db/test_repo.py (relations)
- [x] FE alias for double '/talks' path in tag URLs (temporary)

Milestone 3: Ingestion (2–3 days)

- [x] Service: ingest_full() using lib/engine (sessionize + meetup)
- [x] Upsert in repo.save_talk via source_type + source_id
- [x] Router: ingest endpoints (+ GET /ingest/status)
- [x] Repo: sync status helpers (get_sync_status, update_sync_status, get_all_sync_statuses)
- [x] Tests: ingestion via api/test_ingest_api.py (mocking optional for CI)

Milestone 4: Advanced search + Analytics (1–2 days)

- [x] GET /talks/search/advanced with taxonomy filters (join association table)
- [x] Add simple concatenated search_vector and use it
- [x] Analytics endpoints under /talks/analytics/\*
- [x] Indexes/optimizations as needed
- [x] PG-only FTS: use to_tsvector/plainto_tsquery when on Postgres; fallback to LIKE elsewhere

Milestone 5: Postgres readiness (1 day)

- [x] Ensure JSON/JSONB handling works on PG (validated via ingest/search)
- [x] Alembic init and migrations
- [x] Docs: DATABASE_URL usage; runbook
- [x] Optional PG GIN index on to_tsvector(search_vector)

Milestone 6: DX polish

- [x] Makefile (dev, test, migrate, ingest, frontend)
- [x] README “New Contributors Start Here” (quickstart added to README)
- [x] Simple error handling and logging (request logger, X-Request-ID, generic error handler)

---

## Service/Repo Contracts (adjusted for FE)

- Service: search returns { talks, total }
- Repo: support filtering by talk_types (list) and tags (list of strings) where feasible
- Service: support id:ID query pattern or expose GET /talks/{id}
- Repo: advanced_search_talks(query, talk_types, taxonomy_filters, limit, offset) -> (talks, total)
- Repo: sync status helpers: get_sync_status(source_type), update_sync_status(source_type, success, error_msg), get_all_sync_statuses()

---

## Environment & Commands

- Run API:
  - make dev
- Default DB:
  - SQLite app.db (no env needed)
- Switch to Postgres:
  - export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/pyireland
- Migrations:
  - make migrate
- Run tests:
  - make test
- Ingest (API running):
  - make ingest
