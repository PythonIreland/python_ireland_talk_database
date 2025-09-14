# lib/engine/__init__.py
"""
Data scraping and processing engine for Python Ireland Talk Database

Note: Avoid eager imports that depend on archived/legacy modules.
"""

from .sessionize import Sessionize, Talk, Speaker
from .meetup import Meetup, MeetupEvent, MeetupVenue, MeetupHost

__all__ = [
    "Sessionize",
    "Talk",
    "Speaker",
    "Meetup",
    "MeetupEvent",
    "MeetupVenue",
    "MeetupHost",
]

# If/when needed later, DataPipeline can be imported directly as
# `from lib.engine.data_pipeline import DataPipeline` without polluting package init.
