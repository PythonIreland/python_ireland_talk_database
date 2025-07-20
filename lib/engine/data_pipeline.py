# lib/engine/data_pipeline.py
from .sessionize import Sessionize, Talk as SessionizeTalk
from .meetup import Meetup
from typing import Dict, List, Union
import logging
from datetime import datetime

# Import domain service for business logic
from backend.domain.services.talk_domain_service import TalkDomainService

logger = logging.getLogger(__name__)


class DataPipeline:
    """Ring 1: Pure Python business logic for data processing"""

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
            results["pycon"] = sessionize_count
        except Exception as e:
            logger.error(f"Failed to ingest Sessionize data: {e}")
            results["pycon"] = 0

        # Ingest Meetup data
        try:
            meetup_count = self.ingest_meetup_data()
            results["meetup"] = meetup_count
        except Exception as e:
            logger.error(f"Failed to ingest Meetup data: {e}")
            results["meetup"] = 0

        return results

    def ingest_sessionize_data(self, events: Dict[str, str] = None) -> int:
        """Ingest data from Sessionize and store via talk service"""
        sessionize = Sessionize(events=events)
        talks = sessionize.get_all_data()

        processed_count = 0
        for talk in talks:
            try:
                processed_talk = self._process_sessionize_talk(talk)
                talk_id = self.talk_service.create_talk(processed_talk)
                logger.info(f"Indexed PyConf talk: {talk.title} (ID: {talk_id})")
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process Sessionize talk {talk.id}: {e}")
                continue

        return processed_count

    def ingest_meetup_data(self, groups: Dict[str, str] = None) -> int:
        """Ingest data from Meetup and store via talk service"""
        meetup = Meetup(groups=groups)  # Pass groups, not group

        # Get meetup events using the correct method
        meetup_events = meetup.get_all_data()  # Returns List[MeetupEvent], not dict

        processed_count = 0
        for event in meetup_events:
            try:
                processed_talk = self._process_meetup_event(
                    event
                )  # Pass MeetupEvent object
                talk_id = self.talk_service.create_talk(processed_talk)
                logger.info(f"Indexed Meetup talk: {event.title} (ID: {talk_id})")
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process Meetup event {event.id}: {e}")
                continue

        return processed_count

    def _process_sessionize_talk(self, talk: SessionizeTalk) -> Dict:
        """Process Sessionize Talk object for storage"""
        return {
            "id": f"pycon_{talk.id}",  # Prefix to avoid ID conflicts
            "talk_type": "pycon",
            "title": talk.title,
            "description": talk.description,
            "speaker_names": [s.name for s in talk.speakers],
            "speaker_bios": [s.bio for s in talk.speakers if s.bio],
            "speaker_taglines": [s.tagline for s in talk.speakers if s.tagline],
            "speaker_photos": [s.photo_url for s in talk.speakers if s.photo_url],
            # PyConf specific fields
            "event_id": talk.event_id,
            "event_name": talk.event_name,
            "room": talk.room,
            "start_time": talk.start_time,
            "end_time": talk.end_time,
            # Common fields
            "auto_tags": TalkDomainService.extract_auto_tags(
                talk.title, talk.description
            ),
            "manual_tags": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _process_meetup_event(self, event) -> Dict:  # event is MeetupEvent object
        """Process MeetupEvent object for storage"""
        return {
            "id": f"meetup_{event.id}",
            "talk_type": "meetup",
            "title": event.title,
            "description": event.description,
            "speaker_names": [host.name for host in event.hosts],  # Hosts as speakers
            # Meetup specific fields
            "meetup_id": event.id,
            "event_url": event.event_url,
            "venue_name": event.venue.name if event.venue else "",
            "venue_address": event.venue.address if event.venue else "",
            "city": event.venue.city if event.venue else "",
            "going_count": event.going_count,
            "event_date": event.start_time,
            "hosts": [host.name for host in event.hosts],
            "topics": event.topics,
            "group_name": event.group_name,
            # Common fields
            "auto_tags": TalkDomainService.extract_auto_tags(
                event.title, event.description
            ),
            "manual_tags": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _convert_meetup_to_talk(self, event) -> Dict:
        """Convert meetup event to standardized talk format"""

        return {
            "id": f"meetup_{event.id}",
            "source_id": event.id,
            "source_type": "meetup",
            "talk_type": "meetup",
            "title": event.title,
            "description": event.description,
            "speaker_names": [host.name for host in event.hosts] if event.hosts else [],
            "auto_tags": TalkDomainService.extract_auto_tags(
                event.title, event.description
            ),
            "source_updated_at": datetime.utcnow(),  # Meetup doesn't provide update timestamps
            "type_specific_data": {
                "meetup_id": event.id,
                "event_url": event.event_url,
                "venue_name": event.venue.name if event.venue else "",
                "venue_address": event.venue.address if event.venue else "",
                "city": event.venue.city if event.venue else "",
                "going_count": event.going_count,
                "event_date": event.start_time,
                "hosts": [host.name for host in event.hosts] if event.hosts else [],
                "topics": event.topics or [],
                "group_name": event.group_name,
            },
        }

    def _convert_sessionize_to_talk(self, talk) -> Dict:
        """Convert sessionize talk to standardized talk format"""

        return {
            "id": f"pycon_{talk.id}",
            "source_id": talk.id,
            "source_type": "sessionize",
            "talk_type": "pycon",
            "title": talk.title,
            "description": talk.description,
            "speaker_names": (
                [speaker.name for speaker in talk.speakers] if talk.speakers else []
            ),
            "auto_tags": TalkDomainService.extract_auto_tags(
                talk.title, talk.description
            ),
            "source_updated_at": datetime.utcnow(),  # Sessionize doesn't provide update timestamps
            "type_specific_data": {
                "event_name": talk.event_name,
                "room": talk.room,
                "start_time": talk.start_time,
                "end_time": talk.end_time,
            },
        }
