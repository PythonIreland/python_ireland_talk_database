"""Application services (business logic).

- Orchestrate tasks like creating talks and searching.
- Apply simple business rules (e.g., title trimming, auto-tagging).
- Delegate persistence to db.repo.

Keep this framework-agnostic and easy to unit test.
"""

from typing import Any, Dict, List, Optional
import os

from backend.app.tagging import extract_auto_tags
from backend.db import repo


def create_talk(talk: Dict[str, Any]) -> str:
    talk = dict(talk)
    talk["title"] = talk.get("title", "").strip()

    tags = extract_auto_tags(talk.get("title", ""), talk.get("description", ""))
    talk.setdefault("auto_tags", []).extend(tags)

    return repo.db_save_talk(talk)


def get_talk(talk_id: str) -> Optional[Dict[str, Any]]:
    return repo.db_get_talk(talk_id)


def search_talks(
    q: str = "",
    filters: Optional[Dict[str, Any]] = None,
    *,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    filters = filters or {}
    return repo.db_search_talks(
        q, filters, limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir
    )


def advanced_search_talks(
    q: str = "",
    *,
    talk_types: Optional[List[str]] = None,
    taxonomy_value_ids: Optional[List[int]] = None,
    taxonomy_filters_by_name: Optional[Dict[str, List[str]]] = None,
    match: str = "any",
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    # Resolve name/value filters to IDs if provided
    ids = list(taxonomy_value_ids or [])
    if taxonomy_filters_by_name:
        resolved = repo.db_resolve_taxonomy_value_ids_by_names(taxonomy_filters_by_name)
        ids.extend(resolved)
        # de-duplicate
        ids = sorted(set(ids))

    return repo.db_advanced_search_talks(
        q,
        talk_types=talk_types,
        taxonomy_value_ids=ids or None,
        match=match,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


def list_taxonomies() -> List[Dict[str, Any]]:
    return repo.db_list_taxonomies()


def list_talk_types() -> List[str]:
    return repo.db_list_talk_types()


def create_taxonomy(
    name: str,
    description: str = "",
    created_by: Optional[str] = None,
    is_system: bool = False,
) -> Dict[str, Any]:
    return repo.db_create_taxonomy(
        name=name, description=description, created_by=created_by, is_system=is_system
    )


def update_taxonomy(taxonomy_id: int, **fields: Any) -> Optional[Dict[str, Any]]:
    return repo.db_update_taxonomy(taxonomy_id, **fields)


def delete_taxonomy(taxonomy_id: int) -> bool:
    return repo.db_delete_taxonomy(taxonomy_id)


def create_taxonomy_value(
    taxonomy_id: int, value: str, *, color: Optional[str] = None, description: str = ""
) -> Optional[Dict[str, Any]]:
    return repo.db_create_taxonomy_value(
        taxonomy_id, value, color=color, description=description
    )


def update_taxonomy_value(value_id: int, **fields: Any) -> Optional[Dict[str, Any]]:
    return repo.db_update_taxonomy_value(value_id, **fields)


def delete_taxonomy_value(value_id: int) -> bool:
    return repo.db_delete_taxonomy_value(value_id)


def get_talk_tags_service(talk_id: str) -> Dict[str, Any]:
    return repo.db_get_talk_tags(talk_id)


def add_tags_to_talk_service(talk_id: str, value_ids: List[int]) -> bool:
    return repo.db_add_tags_to_talk(talk_id, value_ids)


def replace_talk_tags_service(talk_id: str, value_ids: List[int]) -> bool:
    return repo.db_replace_talk_tags(talk_id, value_ids)


def remove_talk_tag_service(talk_id: str, value_id: int) -> bool:
    return repo.db_remove_talk_tag(talk_id, value_id)


def ingest_full() -> Dict[str, Any]:
    """Run a full ingest.

    Attempts to fetch from external sources (Sessionize). If network or parsing
    fails, records an error in SyncStatus and continues.
    """
    results: List[Dict[str, Any]] = []

    # Sessionize
    try:
        # Allow disabling network fetch in some environments
        if os.getenv("INGEST_DISABLE_NETWORK"):
            raise RuntimeError("network disabled via INGEST_DISABLE_NETWORK")

        from lib.engine.sessionize import Sessionize  # lazy import

        client = Sessionize()
        talks = client.get_all_data()
        saved = 0
        for t in talks:
            speakers = [s.name for s in (t.speakers or [])]
            payload: Dict[str, Any] = {
                "id": None,  # let repo assign UUID unless upserting by source
                "title": t.title,
                "description": t.description or "",
                "talk_type": "talk",
                "speaker_names": speakers,
                "source_type": "sessionize",
                "source_id": t.id,
                "type_specific_data": {
                    "event_id": t.event_id,
                    "event_name": t.event_name,
                    "room": getattr(t, "room", ""),
                    "start_time": getattr(t, "start_time", ""),
                    "end_time": getattr(t, "end_time", ""),
                },
            }
            # auto-tag before save
            payload.setdefault("auto_tags", []).extend(
                extract_auto_tags(payload["title"], payload["description"])
            )
            repo.db_save_talk(payload)
            saved += 1
        status = repo.db_update_sync_status("sessionize", success=True)
        status["saved"] = saved
        results.append(status)
    except Exception as e:  # pragma: no cover - network/HTML may vary
        results.append(
            repo.db_update_sync_status("sessionize", success=False, error_msg=str(e))
        )

    # Meetup (real)
    try:
        if os.getenv("INGEST_DISABLE_NETWORK"):
            raise RuntimeError("network disabled via INGEST_DISABLE_NETWORK")

        from lib.engine.meetup import Meetup  # lazy import

        m_client = Meetup()
        events = m_client.get_all_data()
        saved_meetup = 0
        for ev in events:
            hosts = [h.name for h in (getattr(ev, "hosts", None) or [])]
            venue = getattr(ev, "venue", None)
            venue_dict = None
            if venue:
                venue_dict = {
                    "name": getattr(venue, "name", "") or "",
                    "city": getattr(venue, "city", "") or "",
                    "address": getattr(venue, "address", "") or "",
                }
            payload: Dict[str, Any] = {
                "id": None,
                "title": getattr(ev, "title", "") or "",
                "description": getattr(ev, "description", "") or "",
                "talk_type": "meetup",
                "speaker_names": hosts,
                "source_type": "meetup",
                "source_id": getattr(ev, "id", None),
                "source_url": getattr(ev, "event_url", None),
                "type_specific_data": {
                    "group_name": getattr(ev, "group_name", "") or "",
                    "venue": venue_dict,
                    "start_time": getattr(ev, "start_time", "") or "",
                    "end_time": getattr(ev, "end_time", "") or "",
                    "going_count": getattr(ev, "going_count", 0) or 0,
                    "topics": getattr(ev, "topics", None) or [],
                },
            }
            payload.setdefault("auto_tags", []).extend(
                extract_auto_tags(payload["title"], payload["description"])
            )
            repo.db_save_talk(payload)
            saved_meetup += 1
        m_status = repo.db_update_sync_status("meetup", success=True)
        m_status["saved"] = saved_meetup
        results.append(m_status)
    except Exception as e:  # pragma: no cover
        results.append(
            repo.db_update_sync_status("meetup", success=False, error_msg=str(e))
        )

    # Placeholder for other sources (e.g., more providers)

    return {"status": "ok", "sources": results}


def ingest_sync() -> Dict[str, Any]:
    """Run an incremental sync. For now, reuse full ingest until we add deltas."""
    return ingest_full()


def get_ingest_status() -> List[Dict[str, Any]]:
    return repo.db_get_all_sync_statuses()


def get_taxonomy_usage_service(taxonomy_id: Optional[int] = None):
    return repo.db_get_taxonomy_usage(taxonomy_id)


def get_popular_tags_service(limit: int = 20):
    return repo.db_get_popular_tags(limit)
