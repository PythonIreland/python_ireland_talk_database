from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class TalkType(Enum):
    CONFERENCE_TALK = "conference_talk"
    LIGHTNING_TALK = "lightning_talk"
    WORKSHOP = "workshop"
    KEYNOTE = "keynote"


@dataclass
class Talk:
    """Domain entity representing a talk"""

    id: str
    title: str
    description: str
    talk_type: TalkType
    speaker_names: List[str]

    def is_valid(self) -> bool:
        """Business rule: a talk must have a title and at least one speaker"""
        return bool(self.title.strip()) and len(self.speaker_names) > 0

    def get_display_title(self) -> str:
        """Business rule: format title for display"""
        return self.title.strip().title()
