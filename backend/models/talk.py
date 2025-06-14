# backend/models/talk.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class Talk(BaseModel):
    id: str
    title: str
    description: str
    speaker_name: str
    event_name: str
    tags: List[str] = []


class TalkSearch(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 20
