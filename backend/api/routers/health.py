"""Health and version endpoints.

These are used by clients and deployment to check liveness and surface API version
without touching the database.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/version")
def version():
    # Keep version simple; can read from package metadata later
    return {"version": "0.1.0"}
