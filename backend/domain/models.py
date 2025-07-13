# backend/domain/models.py
"""
Domain layer (Ring 2) - Pure business domain models

This layer contains:
- Domain entities and value objects (Pydantic models)
- Business data structures and contracts
- Domain enums and types
- Pure business logic validation

Dependencies: Only standard library and domain libraries (Pydantic)
No infrastructure dependencies - these models should work with any persistence layer
"""
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from datetime import datetime
from enum import Enum


class TalkType(str, Enum):
    PYCON = "pycon"  # From Sessionize
    MEETUP = "meetup"  # From Meetup API
    YOUTUBE = "youtube"  # Future: YouTube videos
    OTHER = "other"  # For extensibility


class BaseTalk(BaseModel):
    """Core fields that all talk types have"""

    id: str
    title: str
    description: str = ""
    speaker_names: List[str] = []
    talk_type: TalkType
    source_url: Optional[str] = None

    # Common metadata
    auto_tags: List[str] = []
    manual_tags: List[str] = []
    created_at: datetime
    updated_at: datetime


class PyConTalk(BaseTalk):
    """Sessionize/PyConf specific fields"""

    talk_type: TalkType = TalkType.PYCON
    event_id: str
    event_name: str
    room: str = ""
    start_time: str = ""
    end_time: str = ""
    speaker_bios: List[str] = []
    speaker_taglines: List[str] = []
    speaker_photos: List[str] = []


class MeetupTalk(BaseTalk):
    """Meetup specific fields"""

    talk_type: TalkType = TalkType.MEETUP
    meetup_id: str
    event_url: str = ""
    venue_name: str = ""
    venue_address: str = ""
    city: str = ""
    going_count: int = 0
    event_date: str = ""
    hosts: List[str] = []
    topics: List[str] = []


class YouTubeTalk(BaseTalk):
    """YouTube specific fields (for future)"""

    talk_type: TalkType = TalkType.YOUTUBE
    video_id: str
    channel_name: str = ""
    duration: str = ""
    view_count: int = 0
    published_date: str = ""
    thumbnail_url: str = ""


# Union type for API responses
Talk = Union[PyConTalk, MeetupTalk, YouTubeTalk]


class TalkSearch(BaseModel):
    query: Optional[str] = None
    talk_types: Optional[List[TalkType]] = None
    tags: Optional[List[str]] = None
    events: Optional[List[str]] = None  # For PyConf events
    cities: Optional[List[str]] = None  # For Meetup cities
    limit: int = 20
    offset: int = 0


# Taxonomy management models
class CreateTaxonomyRequest(BaseModel):
    name: str
    description: str = ""
    created_by: str = "system"


class UpdateTaxonomyRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CreateTaxonomyValueRequest(BaseModel):
    value: str
    description: str = ""
    color: str = ""


class UpdateTaxonomyValueRequest(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class AddTagsRequest(BaseModel):
    taxonomy_value_ids: List[int]


class ReplaceTalkTagsRequest(BaseModel):
    taxonomy_value_ids: List[int]


class TalkTagsResponse(BaseModel):
    talk_id: str
    auto_tags: List[str]
    manual_tags: Dict[str, List[str]]  # taxonomy_name -> [values]
