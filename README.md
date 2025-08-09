# Python Ireland Talk Database

A searchable database of Python Ireland conference talks and meetup events with tagging, taxonomies, search (including Postgres FTS), and simple analytics.

---

## New Contributors Start Here

Prerequisites:

- Python 3.11+
- Pipenv: `pip install pipenv`
- Node.js 20+ (for the frontend, optional)
- PostgreSQL (optional; SQLite works by default)

Quick start (SQLite by default):

- Install deps: `pipenv install --dev`
- Run API: `make dev` (http://localhost:8000, docs at /docs)
- Run tests: `make test`
- Ingest sample data (with API running): `make ingest`
- Start frontend (optional): `make frontend` (http://localhost:5173)

Using Postgres instead of SQLite:

- Export: `export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/pyireland`
- Migrate: `make migrate`
- Run API: `make dev`

---

## Developer Commands (Makefile)

- `make dev` → Start FastAPI on http://localhost:8000
- `make test` → Run pytest (-q)
- `make migrate` → Alembic upgrade head (uses DATABASE_URL if set)
- `make ingest` → POST /api/v1/ingest/full then pretty-print result
- `make frontend` → Start Vite dev server (http://localhost:5173)

---

## API Highlights

- Talks search: `GET /api/v1/talks/search?q=&talk_types=&tags=&limit=&offset=` → `{ talks, total }`
- Advanced search: `GET /api/v1/talks/search/advanced?query=...&taxonomy_<Name>=Value`
- Talk detail via id: prefix: `GET /api/v1/talks/search?q=id:<talk_id>`
- Talk types: `GET /api/v1/talks/types`
- Taxonomies: CRUD under `/api/v1/talks/taxonomies` and `/api/v1/talks/taxonomy-values/*`
- Tagging on talks: `GET/POST/PUT/DELETE /api/v1/talks/{id}/tags*`
- Analytics: `/api/v1/talks/analytics/*` (popular tags, taxonomy usage)
- Ingestion: `POST /api/v1/ingest/full`, `POST /api/v1/ingest/sync`, `GET /api/v1/ingest/status`

Full interactive docs at `/docs`.

---

## Storage

- Default: SQLite file `app.db` with zero config
- Postgres: set `DATABASE_URL` and run `make migrate`
- Search uses Postgres FTS (`to_tsvector`) when on PG; falls back to LIKE on SQLite

---

## Logging & Error Handling

- Structured request logs with latency and status
- `X-Request-ID` is generated if missing and returned in responses
- Set log level via `LOG_LEVEL` (INFO by default)

Example env:

- `export LOG_LEVEL=DEBUG`

---

## Frontend

The Vite/React frontend lives in `frontend/`.

- Start: `make frontend`
- Configure API base URL in `frontend/src/config.ts` if needed (defaults to http://localhost:8000/api/v1)

---

## Contributing

- Keep endpoints stable and response shape `{ talks, total }`
- Prefer small PRs; include tests under `tests/`
- SQLite used in tests; outbound network disabled in CI by env

---

## Postgres quickstart

- Ensure Postgres is running and create a database.
- Set `DATABASE_URL`, e.g. `export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/pyireland`
- Initialize schema: `make migrate`
- Run tests: `make test`
