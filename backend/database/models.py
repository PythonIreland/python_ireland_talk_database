# backend/database/models.py
"""
Infrastructure layer (Ring 3) - Database persistence models

This layer contains:
- SQLAlchemy models for database persistence
- PostgreSQL-specific features (JSONB, full-text search)
- Database schema definitions
- ORM relationships and constraints

Dependencies: SQLAlchemy, PostgreSQL-specific libraries
No business logic - pure infrastructure concerns
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Any

Base = declarative_base()

# Association table for talk-taxonomy relationships
talk_taxonomy_values = Table(
    "talk_taxonomy_values",
    Base.metadata,
    Column("talk_id", String, ForeignKey("talks.id"), primary_key=True),
    Column(
        "taxonomy_value_id", Integer, ForeignKey("taxonomy_values.id"), primary_key=True
    ),
)


class Talk(Base):
    """Core talk model for Postgres storage"""

    __tablename__ = "talks"

    # Core fields
    id = Column(String, primary_key=True)
    talk_type = Column(String, nullable=False)  # 'pycon', 'meetup', 'youtube', etc.
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    speaker_names = Column(JSONB, default=list)  # List[str]
    source_url = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sync tracking fields for incremental updates
    source_id = Column(String, nullable=True)  # Original ID from source (e.g., "260082480" for meetup)
    source_type = Column(String, nullable=True)  # 'meetup', 'sessionize', 'youtube', etc.
    last_synced = Column(DateTime, default=datetime.utcnow)  # When this record was last synced
    source_updated_at = Column(DateTime, nullable=True)  # When source data was last updated

    # Extensible JSON field for type-specific data
    type_specific_data = Column(JSONB, default=dict)  # Dict[str, Any]

    # Full-text search fields (for Postgres FTS)
    search_vector = Column(Text)  # Will contain concatenated searchable text

    # Auto-generated tags (from content analysis)
    auto_tags = Column(JSONB, default=list)  # List[str]

    # Relationships
    taxonomy_values = relationship(
        "TaxonomyValue", secondary=talk_taxonomy_values, back_populates="talks"
    )

    @property
    def manual_tags(self) -> List[str]:
        """Get manual tags from taxonomy relationships"""
        return [tv.value for tv in self.taxonomy_values]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "id": self.id,
            "talk_type": self.talk_type,
            "title": self.title,
            "description": self.description,
            "speaker_names": self.speaker_names or [],
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "auto_tags": self.auto_tags or [],
            "manual_tags": self.manual_tags,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
            "source_updated_at": self.source_updated_at.isoformat() if self.source_updated_at else None,
        }

        # Merge type-specific data
        if self.type_specific_data:
            result.update(self.type_specific_data)

        return result


class Taxonomy(Base):
    """Taxonomy definition (e.g., 'conference', 'difficulty', 'topic')"""

    __tablename__ = "taxonomies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(String)  # User who created this taxonomy
    is_system = Column(String, default=False)  # System vs user-defined
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
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
    """Specific values within a taxonomy (e.g., 'beginner', 'intermediate', 'advanced')"""

    __tablename__ = "taxonomy_values"

    id = Column(Integer, primary_key=True)
    taxonomy_id = Column(Integer, ForeignKey("taxonomies.id"), nullable=False)
    value = Column(String, nullable=False)
    description = Column(Text)
    color = Column(String)  # For UI display
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    taxonomy = relationship("Taxonomy", back_populates="values")
    talks = relationship(
        "Talk", secondary=talk_taxonomy_values, back_populates="taxonomy_values"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "taxonomy_id": self.taxonomy_id,
            "value": self.value,
            "description": self.description,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "talk_count": len(self.talks),
        }


class SyncStatus(Base):
    """Track synchronization status for different data sources"""

    __tablename__ = "sync_status"

    id = Column(Integer, primary_key=True)
    source_type = Column(String, unique=True, nullable=False)  # 'meetup', 'sessionize', etc.
    last_sync_time = Column(DateTime, nullable=True)  # When we last synced this source
    last_successful_sync = Column(DateTime, nullable=True)  # Last successful sync
    sync_count = Column(Integer, default=0)  # Total number of syncs performed
    error_count = Column(Integer, default=0)  # Number of failed syncs
    last_error = Column(Text, nullable=True)  # Last error message
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "last_successful_sync": self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            "sync_count": self.sync_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
