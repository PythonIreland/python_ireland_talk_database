"""Analytics endpoints for talks and taxonomies.

- Mounted under /api/v1/talks/analytics
- Returns aggregate usage information for tags/taxonomies.
"""

from fastapi import APIRouter, Query
from typing import Optional

from backend.app.service import (
    get_taxonomy_usage_service,
    get_popular_tags_service,
)

router = APIRouter(prefix="/talks/analytics", tags=["analytics"])


@router.get("/taxonomy-usage")
def taxonomy_usage():
    return {"usage": get_taxonomy_usage_service()}


@router.get("/taxonomies/{taxonomy_id}/usage")
def taxonomy_usage_by_id(taxonomy_id: int):
    return {"usage": get_taxonomy_usage_service(taxonomy_id)}


@router.get("/popular-tags")
def popular_tags(limit: int = Query(20, ge=1, le=200)):
    return {"tags": get_popular_tags_service(limit)}
