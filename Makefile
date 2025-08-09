.PHONY: dev test migrate ingest frontend

# Start the FastAPI backend (http://localhost:8000)
dev:
	@echo "Starting API on http://localhost:8000"
	pipenv run uvicorn backend.main:app --reload --port 8000

# Run test suite
test:
	pipenv run pytest -q

# Apply database migrations (uses DATABASE_URL if set)
migrate:
	pipenv run alembic upgrade head

# Trigger a full ingest via API (backend must be running)
ingest:
	curl -s -X POST http://localhost:8000/api/v1/ingest/full | python -m json.tool

# Start the frontend dev server (http://localhost:5173)
frontend:
	cd frontend && npm install && npm run dev
