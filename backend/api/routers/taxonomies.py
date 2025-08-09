"""Taxonomy and tagging API routes under /talks.

- CRUD for taxonomies and values.
- Tag associations for talks.
- Thin HTTP layer; delegates to services.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException

from backend.app.service import (
    list_taxonomies,
    create_taxonomy,
    update_taxonomy,
    delete_taxonomy,
    create_taxonomy_value,
    update_taxonomy_value,
    delete_taxonomy_value,
    get_talk_tags_service,
    add_tags_to_talk_service,
    replace_talk_tags_service,
    remove_talk_tag_service,
)

router = APIRouter(prefix="/talks", tags=["taxonomies"])


# Taxonomies
@router.get("/taxonomies")
def list_all_taxonomies():
    return {"taxonomies": list_taxonomies()}


@router.post("/taxonomies")
def create_one_taxonomy(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    desc = payload.get("description", "")
    created_by = payload.get("created_by")
    is_system = bool(payload.get("is_system", False))
    t = create_taxonomy(
        name, description=desc, created_by=created_by, is_system=is_system
    )
    return t


@router.put("/taxonomies/{taxonomy_id}")
def update_one_taxonomy(taxonomy_id: int, payload: Dict[str, Any] = Body(...)):
    t = update_taxonomy(taxonomy_id, **payload)
    if not t:
        raise HTTPException(status_code=404, detail="taxonomy not found")
    return t


@router.delete("/taxonomies/{taxonomy_id}")
def delete_one_taxonomy(taxonomy_id: int):
    ok = delete_taxonomy(taxonomy_id)
    if not ok:
        raise HTTPException(status_code=404, detail="taxonomy not found")
    return {"ok": True}


# Taxonomy values
@router.post("/taxonomies/{taxonomy_id}/values")
def create_value(taxonomy_id: int, payload: Dict[str, Any] = Body(...)):
    value = payload.get("value")
    if not value:
        raise HTTPException(status_code=400, detail="value is required")
    tv = create_taxonomy_value(
        taxonomy_id,
        value,
        color=payload.get("color"),
        description=payload.get("description", ""),
    )
    if not tv:
        raise HTTPException(status_code=404, detail="taxonomy not found")
    return tv


@router.put("/taxonomy-values/{value_id}")
def update_value(value_id: int, payload: Dict[str, Any] = Body(...)):
    tv = update_taxonomy_value(value_id, **payload)
    if not tv:
        raise HTTPException(status_code=404, detail="taxonomy value not found")
    return tv


@router.delete("/taxonomy-values/{value_id}")
def delete_value(value_id: int):
    ok = delete_taxonomy_value(value_id)
    if not ok:
        raise HTTPException(status_code=404, detail="taxonomy value not found")
    return {"ok": True}


# Talk tagging
@router.get("/{talk_id}/tags")
def get_talk_tags(talk_id: str):
    return get_talk_tags_service(talk_id)


@router.post("/{talk_id}/tags/add")
def add_tags_to_talk(talk_id: str, payload: Dict[str, Any] = Body(...)):
    value_ids = payload.get("value_ids") or []
    if not isinstance(value_ids, list):
        raise HTTPException(status_code=400, detail="value_ids must be a list")
    ok = add_tags_to_talk_service(talk_id, value_ids)
    if not ok:
        raise HTTPException(status_code=404, detail="talk not found")
    return {"ok": True}


@router.put("/{talk_id}/tags")
def replace_talk_tags(talk_id: str, payload: Dict[str, Any] = Body(...)):
    value_ids = payload.get("value_ids") or []
    if not isinstance(value_ids, list):
        raise HTTPException(status_code=400, detail="value_ids must be a list")
    ok = replace_talk_tags_service(talk_id, value_ids)
    if not ok:
        raise HTTPException(status_code=404, detail="talk not found")
    return {"ok": True}


@router.delete("/{talk_id}/tags/{value_id}")
def remove_talk_tag(talk_id: str, value_id: int):
    ok = remove_talk_tag_service(talk_id, value_id)
    if not ok:
        raise HTTPException(status_code=404, detail="talk not found")
    return {"ok": True}


# Temporary alias routes to support FE paths with an extra '/talks'
@router.get("/talks/{talk_id}/tags")
def get_talk_tags_alias(talk_id: str):
    return get_talk_tags_service(talk_id)


@router.post("/talks/{talk_id}/tags/add")
def add_tags_to_talk_alias(talk_id: str, payload: Dict[str, Any] = Body(...)):
    value_ids = payload.get("value_ids") or []
    if not isinstance(value_ids, list):
        raise HTTPException(status_code=400, detail="value_ids must be a list")
    ok = add_tags_to_talk_service(talk_id, value_ids)
    if not ok:
        raise HTTPException(status_code=404, detail="talk not found")
    return {"ok": True}


@router.put("/talks/{talk_id}/tags")
def replace_talk_tags_alias(talk_id: str, payload: Dict[str, Any] = Body(...)):
    value_ids = payload.get("value_ids") or []
    if not isinstance(value_ids, list):
        raise HTTPException(status_code=400, detail="value_ids must be a list")
    ok = replace_talk_tags_service(talk_id, value_ids)
    if not ok:
        raise HTTPException(status_code=404, detail="talk not found")
    return {"ok": True}


@router.delete("/talks/{talk_id}/tags/{value_id}")
def remove_talk_tag_alias(talk_id: str, value_id: int):
    ok = remove_talk_tag_service(talk_id, value_id)
    if not ok:
        raise HTTPException(status_code=404, detail="talk not found")
    return {"ok": True}
