# backend/database/models.py
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
