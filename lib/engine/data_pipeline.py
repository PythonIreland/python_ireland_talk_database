# lib/engine/data_pipeline.py
from .sessionize import Sessionize, Talk as SessionizeTalk
from .meetup import Meetup
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DataPipeline:
    """Simple data pipeline that fetches from sources and hands off to a talk service.

    Note: The provided talk_service is expected to expose `create_talk(payload: dict) -> str`.
    This keeps the pipeline independent of any legacy domain layer.
    """

    def __init__(self, talk_service=None):
        # Accept dependency injection for testing
        self.talk_service = talk_service

    def ingest_all_data(self) -> Dict[str, int]:
        """Ingest data from all sources"""
        if not self.talk_service:
            raise ValueError("TalkService must be provided for data ingestion")

        results = {}

        # Ingest Sessionize data
        try:
            sessionize_count = self.ingest_sessionize_data()
            results["sessionize"] = sessionize_count
        except Exception as e:
            logger.error(f"Failed to ingest Sessionize data: {e}")
            results["sessionize"] = 0

        # Ingest Meetup data
        try:
            meetup_count = self.ingest_meetup_data()
            results["meetup"] = meetup_count
        except Exception as e:
            logger.error(f"Failed to ingest Meetup data: {e}")
            results["meetup"] = 0

        return results

    def ingest_sessionize_data(self, events: Dict[str, str] | None = None) -> int:
        """Ingest data from Sessionize and store via talk service"""
        sessionize = Sessionize(events=events)
        talks = sessionize.get_all_data()

        processed_count = 0
        for talk in talks:
            try:
                payload = self._process_sessionize_talk(talk)
                self.talk_service.create_talk(payload)
                logger.info(f"Indexed Sessionize talk: {talk.title}")
                processed_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to process Sessionize talk {getattr(talk, 'id', 'unknown')}: {e}"
                )
                continue

        return processed_count

    def ingest_meetup_data(self, groups: Dict[str, str] | None = None) -> int:
        """Ingest data from Meetup and store via talk service"""
        meetup = Meetup(groups=groups)
        meetup_events = meetup.get_all_data()

        processed_count = 0
        for ev in meetup_events:
            try:
                payload = self._process_meetup_event(ev)
                self.talk_service.create_talk(payload)
                logger.info(f"Indexed Meetup event: {ev.title}")
                processed_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to process Meetup event {getattr(ev, 'id', 'unknown')}: {e}"
                )
                continue

        return processed_count

    def _process_sessionize_talk(self, talk: SessionizeTalk) -> Dict:
        """Convert Sessionize talk to our talk payload shape.

        Let the service compute auto-tags and timestamps.
        """
        return {
            # id omitted so the repo can assign one unless upserting by source
            "talk_type": "talk",  # keep consistent with API/search
            "title": talk.title,
            "description": talk.description or "",
            "speaker_names": [s.name for s in (talk.speakers or [])],
            "source_type": "sessionize",
            "source_id": talk.id,
            "type_specific_data": {
                "event_id": talk.event_id,
                "event_name": talk.event_name,
                "room": getattr(talk, "room", "") or "",
                "start_time": getattr(talk, "start_time", "") or "",
                "end_time": getattr(talk, "end_time", "") or "",
            },
        }

    def _process_meetup_event(self, ev) -> Dict:
        """Convert Meetup event to our talk payload shape."""
        venue = getattr(ev, "venue", None)
        venue_dict = None
        if venue:
            venue_dict = {
                "name": getattr(venue, "name", "") or "",
                "city": getattr(venue, "city", "") or "",
                "address": getattr(venue, "address", "") or "",
            }
        return {
            "talk_type": "meetup",
            "title": getattr(ev, "title", "") or "",
            "description": getattr(ev, "description", "") or "",
            "speaker_names": [h.name for h in (getattr(ev, "hosts", None) or [])],
            "source_type": "meetup",
            "source_id": getattr(ev, "id", None),
            "source_url": getattr(ev, "event_url", None),
            "type_specific_data": {
                "group_name": getattr(ev, "group_name", "") or "",
                "venue": venue_dict,
                "start_time": getattr(ev, "start_time", "") or "",
                "end_time": getattr(ev, "end_time", "") or "",
                "going_count": getattr(ev, "going_count", 0) or 0,
                "topics": getattr(ev, "topics", None) or [],
            },
        }
