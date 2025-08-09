"""Ingestion endpoints.

- POST /ingest/full and /ingest/sync: run ingestion jobs (stubbed for now).
- GET /ingest/status: report sync status per source.
"""

from fastapi import APIRouter

from backend.app.service import ingest_full, ingest_sync, get_ingest_status

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/full")
def run_full_ingest():
    return ingest_full()


@router.post("/sync")
def run_incremental_sync():
    return ingest_sync()


@router.get("/status")
def get_status():
    return {"statuses": get_ingest_status()}
