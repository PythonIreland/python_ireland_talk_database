"""backfill search_vector for existing talks

Revision ID: 0002_backfill_search_vector
Revises: 0001_initial
Create Date: 2025-08-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = "0002_backfill_search_vector"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Build a simple concatenation; mirrors the Python builder and remains cross-DB
    conn = op.get_bind()
    talks = sa.table(
        "talks",
        sa.column("id", sa.String()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("talk_type", sa.String()),
        sa.column("speaker_names", sa.JSON()),
        sa.column("auto_tags", sa.JSON()),
        sa.column("type_specific_data", sa.JSON()),
        sa.column("search_vector", sa.Text()),
    )

    # Fetch in batches to stay portable and simple
    result = conn.execute(
        sa.select(
            talks.c.id,
            talks.c.title,
            talks.c.description,
            talks.c.talk_type,
            talks.c.speaker_names,
            talks.c.auto_tags,
            talks.c.type_specific_data,
        )
    )
    rows = result.fetchall()

    def safe_list(v):
        if not v:
            return []
        if isinstance(v, list):
            return v
        try:
            import json

            d = json.loads(v)
            return d if isinstance(d, list) else [str(d)]
        except Exception:
            return [str(v)]

    updates = []
    for r in rows:
        parts = []
        parts.append((r.title or "").strip())
        parts.append(r.description or "")
        parts.append(r.talk_type or "")
        parts.extend([str(s) for s in safe_list(r.speaker_names)])
        parts.extend([str(t) for t in safe_list(r.auto_tags)])
        tsd = r.type_specific_data or {}
        if isinstance(tsd, str):
            try:
                import json

                tsd = json.loads(tsd)
            except Exception:
                tsd = {"_raw": tsd}
        for key in ("event_name", "group_name", "room", "topics"):
            val = (tsd or {}).get(key)
            if isinstance(val, list):
                parts.extend([str(x) for x in val])
            elif val is not None:
                parts.append(str(val))
        text = " ".join([p for p in parts if p]).lower()
        updates.append({"id": r.id, "sv": text})

    for u in updates:
        conn.execute(
            sa.text("UPDATE talks SET search_vector=:sv WHERE id=:id"),
            {"sv": u["sv"], "id": u["id"]},
        )


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE talks SET search_vector=NULL"))
