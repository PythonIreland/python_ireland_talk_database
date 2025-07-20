from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TalkType(Enum):
    CONFERENCE_TALK = "conference_talk"
    LIGHTNING_TALK = "lightning_talk"
    WORKSHOP = "workshop"
    KEYNOTE = "keynote"
    MEETUP = "meetup"
    PYCON = "pycon"
    GENERAL_TALK = "talk"


@dataclass
class Talk:
    """Rich domain entity with business behavior"""

    id: str
    title: str
    description: str
    talk_type: TalkType
    speaker_names: List[str]
    auto_tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    type_specific_data: Dict[str, Any] = field(default_factory=dict)

    # Business methods
    def is_valid(self) -> bool:
        """Comprehensive validation"""
        return (
            bool(self.title.strip())
            and len(self.speaker_names) > 0
            and all(name.strip() for name in self.speaker_names)
        )

    def add_speaker(self, speaker_name: str) -> None:
        """Business rule: add speaker with validation"""
        if speaker_name.strip() and speaker_name not in self.speaker_names:
            self.speaker_names.append(speaker_name.strip())

    def update_content(self, title: str = None, description: str = None) -> None:
        """Business rule: update content and refresh auto-tags"""
        if title is not None:
            self.title = title.strip()
        if description is not None:
            self.description = description.strip()
        self.updated_at = datetime.now()
        # Could trigger auto-tag refresh

    def has_keyword(self, keyword: str) -> bool:
        """Business rule: search for keyword in talk content"""
        search_text = f"{self.title} {self.description}".lower()
        return keyword.lower() in search_text

    def is_by_speaker(self, speaker_name: str) -> bool:
        """Business rule: check if talk is by specific speaker"""
        return any(speaker_name.lower() in name.lower() for name in self.speaker_names)

    def get_duration_minutes(self) -> Optional[int]:
        """Business rule: extract duration from type-specific data"""
        if "duration" in self.type_specific_data:
            return self.type_specific_data["duration"]
        # Default durations by type
        defaults = {
            TalkType.LIGHTNING_TALK: 5,
            TalkType.CONFERENCE_TALK: 30,
            TalkType.WORKSHOP: 180,
            TalkType.KEYNOTE: 45,
        }
        return defaults.get(self.talk_type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "talk_type": self.talk_type.value,
            "speaker_names": self.speaker_names,
            "auto_tags": self.auto_tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "type_specific_data": self.type_specific_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Talk":
        """Create from dictionary (from persistence)"""
        # Parse datetime fields
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            talk_type=TalkType(data["talk_type"]),
            speaker_names=data.get("speaker_names", []),
            auto_tags=data.get("auto_tags", []),
            created_at=created_at,
            updated_at=updated_at,
            source_id=data.get("source_id"),
            source_type=data.get("source_type"),
            type_specific_data=data.get("type_specific_data", {}),
        )
