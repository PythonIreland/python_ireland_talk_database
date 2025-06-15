# lib/engine/__init__.py
"""
Data scraping and processing engine for Python Ireland Talk Database
"""

from .sessionize import Sessionize, Talk, Speaker
from .meetup import Meetup, MeetupEvent, MeetupVenue, MeetupHost
from .elasticsearch_client import ElasticsearchClient
from .data_pipeline import DataPipeline

__all__ = [
    "Sessionize",
    "Talk",
    "Speaker",
    "Meetup",
    "MeetupEvent",
    "MeetupVenue",
    "MeetupHost",
    "ElasticsearchClient",
    "DataPipeline",
]
