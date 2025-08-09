"""Talks API router.

- HTTP layer only: validates inputs lightly and delegates to services.
- Mounted under /api/v1/talks by the application.
- Returns simple JSON payloads expected by the frontend.
"""

from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Body, Query, HTTPException, Request

from backend.app.service import create_talk, search_talks, get_talk, list_talk_types
from backend.app.service import advanced_search_talks

__all__ = [
    "router",
    "list_talks",
    "search",
    "create",
    "get_one",
    "get_talk_types",
]

router = APIRouter(prefix="/talks", tags=["talks"])


@router.get("")
def list_talks(
    q: str = Query(""),
    talk_type: Optional[str] = None,
    talk_types: Optional[List[str]] = Query(None),
    limit: int = 50,
    offset: int = 0,
):
    filters: Dict[str, Any] = {}
    if talk_type:
        filters["talk_type"] = talk_type
    if talk_types:
        filters["talk_types"] = talk_types
    res = search_talks(q, filters, limit=limit, offset=offset)
    return {"talks": res.get("items", []), "total": res.get("total", 0)}


@router.get("/search")
def search(
    q: str = Query(""),
    talk_type: Optional[str] = None,
    talk_types: Optional[List[str]] = Query(None),
    limit: int = 50,
    offset: int = 0,
):
    filters: Dict[str, Any] = {}
    if talk_type:
        filters["talk_type"] = talk_type
    if talk_types:
        filters["talk_types"] = talk_types
    res = search_talks(q, filters, limit=limit, offset=offset)
    return {"talks": res.get("items", []), "total": res.get("total", 0)}


@router.get("/types")
def get_talk_types():
    return {"types": list_talk_types()}


@router.get("/search/advanced")
def advanced_search(
    request: Request,
    q: str = Query(""),
    talk_types: Optional[List[str]] = Query(None),
    taxonomy_value_ids: Optional[List[int]] = Query(None),
    match: str = Query("any"),
    limit: int = 50,
    offset: int = 0,
):
    # Extract taxonomy_<Name>=Value filters from query params
    filters_by_name: Dict[str, List[str]] = {}
    for key, value in request.query_params.multi_items():
        if key.startswith("taxonomy_"):
            tax_name = key[len("taxonomy_") :]
            filters_by_name.setdefault(tax_name, []).append(value)

    res = advanced_search_talks(
        q,
        talk_types=talk_types,
        taxonomy_value_ids=taxonomy_value_ids,
        taxonomy_filters_by_name=filters_by_name or None,
        match=match,
        limit=limit,
        offset=offset,
    )
    return {"talks": res.get("items", []), "total": res.get("total", 0)}


@router.get("/{talk_id}")
def get_one(talk_id: str):
    talk = get_talk(talk_id)
    if not talk:
        raise HTTPException(status_code=404, detail="Talk not found")
    return talk


@router.post("")
def create(talk: Dict[str, Any] = Body(...)):
    talk_id = create_talk(talk)
    return {"id": talk_id}
