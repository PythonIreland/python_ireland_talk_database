"""SQLAlchemy ORM models and associations.

- Cross-database: SQLite by default, Postgres via DATABASE_URL.
- Uses JSON/Boolean for portability; defaults set for dict/list fields.
- Talks <-> TaxonomyValues many-to-many via association table.
- SyncStatus tracks ingestion state per source.
"""

from __future__ import annotations
from typing import Any, List, Dict, Optional
from datetime import datetime
import json

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Table,
    Index,
    JSON,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Association table
TalkTaxonomy = Table(
    "talk_taxonomy_values",
    Base.metadata,
    Column("talk_id", String, ForeignKey("talks.id"), primary_key=True),
    Column(
        "taxonomy_value_id", Integer, ForeignKey("taxonomy_values.id"), primary_key=True
    ),
    Index("ix_talk_taxonomy_unique", "talk_id", "taxonomy_value_id", unique=True),
)


class Talk(Base):
    __tablename__ = "talks"

    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_talk_source"),
    )

    id = Column(String, primary_key=True)
    talk_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, default="")
    speaker_names = Column(JSON, default=list)  # cross-db JSON
    source_url = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_id = Column(String)
    source_type = Column(String)
    last_synced = Column(DateTime)
    source_updated_at = Column(DateTime)

    type_specific_data = Column(JSON, default=dict)
    search_vector = Column(Text, index=True)

    auto_tags = Column(JSON, default=list)

    taxonomy_values = relationship(
        "TaxonomyValue", secondary=TalkTaxonomy, back_populates="talks"
    )

    @property
    def manual_tags(self) -> List[str]:
        return [tv.value for tv in self.taxonomy_values]

    def to_dict(self) -> Dict[str, Any]:
        def _decode(val):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return val
            return val

        return {
            "id": self.id,
            "talk_type": self.talk_type,
            "title": self.title,
            "description": self.description,
            "speaker_names": _decode(self.speaker_names) or [],
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "auto_tags": _decode(self.auto_tags) or [],
            "manual_tags": self.manual_tags,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
            "source_updated_at": (
                self.source_updated_at.isoformat() if self.source_updated_at else None
            ),
            **(_decode(self.type_specific_data) or {}),
        }


class Taxonomy(Base):
    __tablename__ = "taxonomies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(String)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    values = relationship(
        "TaxonomyValue", back_populates="taxonomy", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "values": [v.to_dict() for v in self.values],
        }


class TaxonomyValue(Base):
    __tablename__ = "taxonomy_values"

    id = Column(Integer, primary_key=True)
    taxonomy_id = Column(Integer, ForeignKey("taxonomies.id"), nullable=False)
    value = Column(String, nullable=False)
    description = Column(Text)
    color = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    taxonomy = relationship("Taxonomy", back_populates="values")
    talks = relationship(
        "Talk", secondary=TalkTaxonomy, back_populates="taxonomy_values"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "taxonomy_id": self.taxonomy_id,
            "value": self.value,
            "description": self.description,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SyncStatus(Base):
    __tablename__ = "sync_status"

    id = Column(Integer, primary_key=True)
    source_type = Column(String, unique=True, nullable=False)
    last_sync_time = Column(DateTime)
    last_successful_sync = Column(DateTime)
    sync_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "last_sync_time": (
                self.last_sync_time.isoformat() if self.last_sync_time else None
            ),
            "last_successful_sync": (
                self.last_successful_sync.isoformat()
                if self.last_successful_sync
                else None
            ),
            "sync_count": self.sync_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
