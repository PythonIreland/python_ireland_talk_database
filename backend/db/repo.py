"""Repository: SQLAlchemy-backed data access helpers.

- Uses engine/session from backend.db.engine (SQLite by default; Postgres via DATABASE_URL).
- Provides simple functions used by services: upsert-lite save, search w/ pagination, get by id, list taxonomies.
- Keeps persistence concerns here so routers/services stay clean.
"""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy import or_, func, desc, asc, delete
from sqlalchemy.orm import Session

from backend.db.engine import SessionLocal
from backend.db.models import Talk, Taxonomy, TaxonomyValue, TalkTaxonomy, SyncStatus


# Session factory helper


def _open_session() -> Session:
    return SessionLocal()


def _is_postgres(session: Session) -> bool:
    try:
        return session.bind and session.bind.dialect.name == "postgresql"
    except Exception:
        return False


def _apply_text_search(session: Session, query, q_raw: str):
    """Apply text search condition depending on dialect.

    - Postgres: to_tsvector @@ plainto_tsquery on search_vector
    - Others: case-insensitive LIKE on search_vector/title/description
    """
    ql = (q_raw or "").strip().lower()
    if not ql:
        return query
    if _is_postgres(session):
        return query.filter(
            func.to_tsvector("english", Talk.search_vector).op("@@")(
                func.plainto_tsquery("english", q_raw)
            )
        )
    like = f"%{ql}%"
    return query.filter(
        or_(
            func.lower(Talk.search_vector).like(like),
            func.lower(Talk.title).like(like),
            func.lower(Talk.description).like(like),
        )
    )


# Utility: search vector builders


def _build_search_vector_from_payload(talk: Dict[str, Any]) -> str:
    title = (talk.get("title") or "").strip()
    desc = talk.get("description") or ""
    speakers = talk.get("speaker_names") or []
    talk_type = talk.get("talk_type") or talk.get("type", "") or ""
    auto_tags = talk.get("auto_tags") or []
    tsd = talk.get("type_specific_data") or {}
    parts: List[str] = [title, desc, talk_type]
    parts.extend([str(s) for s in speakers])
    parts.extend([str(t) for t in auto_tags])
    # pick a few common fields
    for key in ("event_name", "group_name", "room", "topics"):
        val = tsd.get(key)
        if isinstance(val, list):
            parts.extend([str(x) for x in val])
        elif val is not None:
            parts.append(str(val))
    text = " ".join(p for p in parts if p)
    return text.lower()


def _build_search_vector_from_model(obj: Talk) -> str:
    parts: List[str] = []
    parts.append(obj.title or "")
    parts.append(obj.description or "")
    parts.append(obj.talk_type or "")

    # JSON-like fields may be strings in some DBs; normalize
    def _ensure_list(v):
        if not v:
            return []
        if isinstance(v, list):
            return v
        try:
            import json as _json

            data = _json.loads(v)
            return data if isinstance(data, list) else [str(data)]
        except Exception:
            return [str(v)]

    parts.extend([str(s) for s in (obj.speaker_names or [])])
    parts.extend([str(t) for t in (obj.auto_tags or [])])
    parts.extend(obj.manual_tags or [])
    tsd = obj.type_specific_data or {}
    if isinstance(tsd, str):
        try:
            import json as _json

            tsd = _json.loads(tsd)
        except Exception:
            tsd = {"_raw": tsd}
    for key in ("event_name", "group_name", "room", "topics"):
        val = (tsd or {}).get(key)
        if isinstance(val, list):
            parts.extend([str(x) for x in val])
        elif val is not None:
            parts.append(str(val))
    text = " ".join(p for p in parts if p)
    return text.lower()


# CRUD helpers


def _find_existing_talk(session: Session, talk: Dict[str, Any]) -> Optional[Talk]:
    # Prefer explicit id
    tid = talk.get("id")
    if tid:
        return session.get(Talk, tid)

    # Otherwise try upsert-by-source if both are present
    src_type = talk.get("source_type")
    src_id = talk.get("source_id")
    if src_type and src_id:
        return (
            session.query(Talk)
            .filter(Talk.source_type == src_type, Talk.source_id == src_id)
            .one_or_none()
        )
    return None


def db_get_talk(talk_id: str) -> Optional[Dict[str, Any]]:
    session = _open_session()
    try:
        obj = session.get(Talk, talk_id)
        return obj.to_dict() if obj else None
    finally:
        session.close()


def db_save_talk(talk: Dict[str, Any]) -> str:
    """Create or update a Talk row from a plain dict and return its id."""
    session = _open_session()
    try:
        existing = _find_existing_talk(session, talk)
        if existing is None:
            # Assign id if not provided
            tid = talk.get("id") or str(uuid4())
            obj = Talk(
                id=tid,
                talk_type=talk.get("talk_type") or talk.get("type", "talk"),
                title=(talk.get("title") or "").strip(),
                description=talk.get("description") or "",
                speaker_names=talk.get("speaker_names") or [],
                source_url=talk.get("source_url"),
                source_id=talk.get("source_id"),
                source_type=talk.get("source_type"),
                auto_tags=talk.get("auto_tags") or [],
                type_specific_data=talk.get("type_specific_data") or {},
                search_vector=_build_search_vector_from_payload(talk),
            )
            session.add(obj)
            session.commit()
            return obj.id
        else:
            # Update a subset of fields
            existing.talk_type = talk.get("talk_type") or existing.talk_type
            if "title" in talk:
                existing.title = (talk.get("title") or "").strip()
            if "description" in talk:
                existing.description = talk.get("description") or ""
            if "speaker_names" in talk:
                existing.speaker_names = talk.get("speaker_names") or []
            if "source_url" in talk:
                existing.source_url = talk.get("source_url")
            if "auto_tags" in talk:
                existing.auto_tags = talk.get("auto_tags") or []
            if "type_specific_data" in talk:
                existing.type_specific_data = talk.get("type_specific_data") or {}
            # Recompute search vector on update
            existing.search_vector = _build_search_vector_from_model(existing)
            session.commit()
            return existing.id
    finally:
        session.close()


def db_search_talks(
    q: str,
    filters: Dict[str, Any],
    *,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    session = _open_session()
    try:
        q_raw = q or ""
        ql = q_raw.strip().lower()

        # id: prefix short-circuit
        if ql.startswith("id:"):
            target_id = q_raw.split(":", 1)[1].strip()
            if target_id:
                obj = session.get(Talk, target_id)
                items = [obj.to_dict()] if obj else []
                return {"items": items, "total": len(items)}

        query = session.query(Talk)
        if ql:
            # Apply dialect-aware text search
            query = _apply_text_search(session, query, q_raw)

        # Filters: singular or list
        talk_type = filters.get("talk_type")
        if talk_type:
            query = query.filter(Talk.talk_type == talk_type)
        talk_types = filters.get("talk_types") or []
        if talk_types:
            query = query.filter(Talk.talk_type.in_(talk_types))

        # Sorting
        column = getattr(Talk, sort_by, Talk.created_at)
        direction = desc if sort_dir.lower() == "desc" else asc
        query = query.order_by(direction(column))

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        data = [t.to_dict() for t in items]
        return {"items": data, "total": total}
    finally:
        session.close()


def db_list_taxonomies() -> List[Dict[str, Any]]:
    session = _open_session()
    try:
        tax = session.query(Taxonomy).all()
        return [t.to_dict() for t in tax]
    finally:
        session.close()


def db_create_taxonomy(
    name: str,
    description: str = "",
    created_by: Optional[str] = None,
    is_system: bool = False,
) -> Dict[str, Any]:
    session = _open_session()
    try:
        obj = Taxonomy(
            name=name,
            description=description,
            created_by=created_by,
            is_system=is_system,
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj.to_dict()
    finally:
        session.close()


def db_update_taxonomy(
    taxonomy_id: int,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_system: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    session = _open_session()
    try:
        obj = session.get(Taxonomy, taxonomy_id)
        if not obj:
            return None
        if name is not None:
            obj.name = name
        if description is not None:
            obj.description = description
        if is_system is not None:
            obj.is_system = is_system
        session.commit()
        session.refresh(obj)
        return obj.to_dict()
    finally:
        session.close()


def db_delete_taxonomy(taxonomy_id: int) -> bool:
    session = _open_session()
    try:
        obj = session.get(Taxonomy, taxonomy_id)
        if not obj:
            return False
        # Remove tag associations for values under this taxonomy first
        value_ids = [v.id for v in obj.values]
        if value_ids:
            session.execute(
                delete(TalkTaxonomy).where(
                    TalkTaxonomy.c.taxonomy_value_id.in_(value_ids)
                )
            )
        session.delete(obj)
        session.commit()
        return True
    finally:
        session.close()


def db_create_taxonomy_value(
    taxonomy_id: int, value: str, *, color: Optional[str] = None, description: str = ""
) -> Optional[Dict[str, Any]]:
    session = _open_session()
    try:
        tax = session.get(Taxonomy, taxonomy_id)
        if not tax:
            return None
        # Optional uniqueness guard per taxonomy
        exists = (
            session.query(TaxonomyValue)
            .filter(
                TaxonomyValue.taxonomy_id == taxonomy_id,
                func.lower(TaxonomyValue.value) == func.lower(value),
            )
            .first()
        )
        if exists:
            return exists.to_dict()
        tv = TaxonomyValue(
            taxonomy_id=taxonomy_id, value=value, color=color, description=description
        )
        session.add(tv)
        session.commit()
        session.refresh(tv)
        return tv.to_dict()
    finally:
        session.close()


def db_update_taxonomy_value(
    value_id: int,
    *,
    value: Optional[str] = None,
    color: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    session = _open_session()
    try:
        tv = session.get(TaxonomyValue, value_id)
        if not tv:
            return None
        if value is not None:
            tv.value = value
        if color is not None:
            tv.color = color
        if description is not None:
            tv.description = description
        session.commit()
        session.refresh(tv)
        return tv.to_dict()
    finally:
        session.close()


def db_delete_taxonomy_value(value_id: int) -> bool:
    session = _open_session()
    try:
        tv = session.get(TaxonomyValue, value_id)
        if not tv:
            return False
        # Remove associations first
        session.execute(
            delete(TalkTaxonomy).where(TalkTaxonomy.c.taxonomy_value_id == value_id)
        )
        session.delete(tv)
        session.commit()
        return True
    finally:
        session.close()


# Tagging helpers


def db_get_talk_tags(talk_id: str) -> Dict[str, Any]:
    session = _open_session()
    try:
        talk = session.get(Talk, talk_id)
        if not talk:
            return {"tags": []}
        grouped: Dict[int, Dict[str, Any]] = {}
        for tv in talk.taxonomy_values:
            t = tv.taxonomy
            if t.id not in grouped:
                grouped[t.id] = {
                    "taxonomy_id": t.id,
                    "taxonomy_name": t.name,
                    "values": [],
                }
            grouped[t.id]["values"].append(
                {"id": tv.id, "value": tv.value, "color": tv.color}
            )
        return {"tags": list(grouped.values())}
    finally:
        session.close()


def db_add_tags_to_talk(talk_id: str, value_ids: List[int]) -> bool:
    session = _open_session()
    try:
        talk = session.get(Talk, talk_id)
        if not talk:
            return False
        values = (
            session.query(TaxonomyValue).filter(TaxonomyValue.id.in_(value_ids)).all()
        )
        current_ids = {v.id for v in talk.taxonomy_values}
        for v in values:
            if v.id not in current_ids:
                talk.taxonomy_values.append(v)
        session.commit()
        return True
    finally:
        session.close()


def db_replace_talk_tags(talk_id: str, value_ids: List[int]) -> bool:
    session = _open_session()
    try:
        talk = session.get(Talk, talk_id)
        if not talk:
            return False
        values = (
            session.query(TaxonomyValue).filter(TaxonomyValue.id.in_(value_ids)).all()
        )
        talk.taxonomy_values = values
        session.commit()
        return True
    finally:
        session.close()


def db_remove_talk_tag(talk_id: str, value_id: int) -> bool:
    session = _open_session()
    try:
        talk = session.get(Talk, talk_id)
        if not talk:
            return False
        talk.taxonomy_values = [v for v in talk.taxonomy_values if v.id != value_id]
        session.commit()
        return True
    finally:
        session.close()


def db_list_talk_types() -> List[str]:
    session = _open_session()
    try:
        rows = (
            session.query(Talk.talk_type)
            .filter(Talk.talk_type.isnot(None))
            .distinct()
            .all()
        )
        types = sorted({r[0] for r in rows if r[0]})
        return types
    finally:
        session.close()


# SyncStatus helpers


def db_get_sync_status(source_type: str) -> Optional[Dict[str, Any]]:
    session = _open_session()
    try:
        row = (
            session.query(SyncStatus)
            .filter(SyncStatus.source_type == source_type)
            .one_or_none()
        )
        return row.to_dict() if row else None
    finally:
        session.close()


def db_update_sync_status(
    source_type: str, *, success: bool, error_msg: Optional[str] = None
) -> Dict[str, Any]:
    session = _open_session()
    try:
        row = (
            session.query(SyncStatus)
            .filter(SyncStatus.source_type == source_type)
            .one_or_none()
        )
        now = datetime.utcnow()
        if row is None:
            row = SyncStatus(
                source_type=source_type,
                last_sync_time=now,
                last_successful_sync=now if success else None,
                sync_count=1,
                error_count=0 if success else 1,
                last_error=None if success else (error_msg or "error"),
            )
            session.add(row)
        else:
            row.last_sync_time = now
            row.sync_count = (row.sync_count or 0) + 1
            if success:
                row.last_successful_sync = now
                row.last_error = None  # clear stale error on success
            else:
                row.error_count = (row.error_count or 0) + 1
                row.last_error = error_msg or "error"
        session.commit()
        session.refresh(row)
        return row.to_dict()
    finally:
        session.close()


def db_get_all_sync_statuses() -> List[Dict[str, Any]]:
    session = _open_session()
    try:
        rows = session.query(SyncStatus).order_by(SyncStatus.source_type).all()
        return [r.to_dict() for r in rows]
    finally:
        session.close()


def db_resolve_taxonomy_value_ids_by_names(
    filters_by_taxonomy: Dict[str, List[str]],
) -> List[int]:
    """Resolve taxonomy value IDs from a mapping of taxonomy name -> list of values.

    Name and value matches are case-insensitive.
    """
    if not filters_by_taxonomy:
        return []
    session = _open_session()
    try:
        ids: List[int] = []
        for tax_name, values in filters_by_taxonomy.items():
            if not values:
                continue
            rows = (
                session.query(TaxonomyValue.id)
                .join(Taxonomy, TaxonomyValue.taxonomy_id == Taxonomy.id)
                .filter(func.lower(Taxonomy.name) == func.lower(tax_name))
                .filter(
                    func.lower(TaxonomyValue.value).in_([v.lower() for v in values])
                )
                .all()
            )
            ids.extend([r[0] for r in rows])
        # de-duplicate
        return sorted(set(ids))
    finally:
        session.close()


def db_advanced_search_talks(
    q: str = "",
    *,
    talk_types: Optional[List[str]] = None,
    taxonomy_value_ids: Optional[List[int]] = None,
    match: str = "any",  # 'any' or 'all'
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    """Advanced search supporting taxonomy value filtering with any/all semantics."""
    session = _open_session()
    try:
        q_raw = q or ""
        ql = q_raw.strip().lower()
        ids = [int(i) for i in (taxonomy_value_ids or []) if i is not None]

        # Base query
        base_query = session.query(Talk)

        if ql:
            # Apply dialect-aware text search
            base_query = _apply_text_search(session, base_query, q_raw)

        if talk_types:
            base_query = base_query.filter(Talk.talk_type.in_(talk_types))

        if ids:
            if match.lower() == "all":
                # Subquery of Talk IDs having all of the requested taxonomy values
                subq = (
                    session.query(Talk.id)
                    .join(TalkTaxonomy, Talk.id == TalkTaxonomy.c.talk_id)
                    .filter(TalkTaxonomy.c.taxonomy_value_id.in_(ids))
                    .group_by(Talk.id)
                    .having(
                        func.count(func.distinct(TalkTaxonomy.c.taxonomy_value_id))
                        == len(ids)
                    )
                    .subquery()
                )
                base_query = base_query.filter(Talk.id.in_(session.query(subq.c.id)))
            else:
                # ANY: talks having at least one of the requested values
                base_query = (
                    base_query.join(Talk.taxonomy_values)
                    .filter(TaxonomyValue.id.in_(ids))
                    .distinct()
                )

        # Sorting
        column = getattr(Talk, sort_by, Talk.created_at)
        direction = desc if sort_dir.lower() == "desc" else asc
        base_query = base_query.order_by(direction(column))

        # Count total (handle DISTINCT properly when joining)
        if ids and match.lower() != "all":
            id_subq = base_query.with_entities(Talk.id).distinct().subquery()
            total = session.query(func.count()).select_from(id_subq).scalar() or 0
        else:
            total = base_query.count()

        items = base_query.offset(offset).limit(limit).all()
        data = [t.to_dict() for t in items]
        return {"items": data, "total": total}
    finally:
        session.close()


def db_get_taxonomy_usage(taxonomy_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return usage counts of taxonomy values, grouped by taxonomy.

    If taxonomy_id is provided, returns a single-group list for that taxonomy.
    Shape:
      [{
        taxonomy_id, taxonomy_name, total, values: [{id, value, count}]
      }]
    """
    session = _open_session()
    try:
        q = (
            session.query(
                Taxonomy.id.label("taxonomy_id"),
                Taxonomy.name.label("taxonomy_name"),
                TaxonomyValue.id.label("value_id"),
                TaxonomyValue.value.label("value"),
                func.count(TalkTaxonomy.c.talk_id).label("count"),
            )
            .join(TaxonomyValue, Taxonomy.id == TaxonomyValue.taxonomy_id)
            .outerjoin(
                TalkTaxonomy,
                TaxonomyValue.id == TalkTaxonomy.c.taxonomy_value_id,
            )
            .group_by(Taxonomy.id, Taxonomy.name, TaxonomyValue.id, TaxonomyValue.value)
            .order_by(Taxonomy.name.asc(), func.count(TalkTaxonomy.c.talk_id).desc())
        )
        if taxonomy_id is not None:
            q = q.filter(Taxonomy.id == taxonomy_id)
        rows = q.all()
        grouped: Dict[int, Dict[str, Any]] = {}
        for r in rows:
            tid = r.taxonomy_id
            if tid not in grouped:
                grouped[tid] = {
                    "taxonomy_id": r.taxonomy_id,
                    "taxonomy_name": r.taxonomy_name,
                    "total": 0,
                    "values": [],
                }
            grouped[tid]["values"].append(
                {"id": r.value_id, "value": r.value, "count": int(r.count)}
            )
            grouped[tid]["total"] += int(r.count)
        return list(grouped.values())
    finally:
        session.close()


def db_get_popular_tags(limit: int = 20) -> List[Dict[str, Any]]:
    """Return top taxonomy values by usage across all talks."""
    session = _open_session()
    try:
        q = (
            session.query(
                TaxonomyValue.id.label("value_id"),
                TaxonomyValue.value.label("value"),
                Taxonomy.id.label("taxonomy_id"),
                Taxonomy.name.label("taxonomy_name"),
                func.count(TalkTaxonomy.c.talk_id).label("count"),
            )
            .join(Taxonomy, TaxonomyValue.taxonomy_id == Taxonomy.id)
            .outerjoin(
                TalkTaxonomy, TaxonomyValue.id == TalkTaxonomy.c.taxonomy_value_id
            )
            .group_by(TaxonomyValue.id, TaxonomyValue.value, Taxonomy.id, Taxonomy.name)
            .order_by(
                func.count(TalkTaxonomy.c.talk_id).desc(), TaxonomyValue.value.asc()
            )
            .limit(limit)
        )
        rows = q.all()
        return [
            {
                "id": r.value_id,
                "value": r.value,
                "count": int(r.count),
                "taxonomy_id": r.taxonomy_id,
                "taxonomy_name": r.taxonomy_name,
            }
            for r in rows
        ]
    finally:
        session.close()
