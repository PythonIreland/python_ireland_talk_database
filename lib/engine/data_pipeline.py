# lib/engine/data_pipeline.py
from .sessionize import Sessionize, Talk as SessionizeTalk
from .meetup import Meetup
from typing import Dict, List, Union
import logging
from datetime import datetime

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
            "auto_tags": self._extract_auto_tags(talk.title, talk.description),
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
            "auto_tags": self._extract_auto_tags(event.title, event.description),
            "manual_tags": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _extract_auto_tags(self, title: str, description: str) -> List[str]:
        """Extract auto tags from title and description"""
        text = f"{title} {description}".lower()
        keywords = []

        # Same tagging logic as before but moved to common method
        ai_keywords = [
            "ai",
            "machine learning",
            "neural",
            "deep learning",
            "llm",
            "gpt",
        ]
        if any(keyword in text for keyword in ai_keywords):
            keywords.append("AI/ML")

        web_keywords = ["django", "flask", "fastapi", "web", "http", "api", "rest"]
        if any(keyword in text for keyword in web_keywords):
            keywords.append("Web Development")

        data_keywords = [
            "pandas",
            "numpy",
            "data",
            "analysis",
            "visualization",
            "jupyter",
        ]
        if any(keyword in text for keyword in data_keywords):
            keywords.append("Data Science")

        test_keywords = ["test", "pytest", "unittest", "tdd", "testing"]
        if any(keyword in text for keyword in test_keywords):
            keywords.append("Testing")

        return keywords

    # ===== INCREMENTAL SYNC METHODS =====

    def sync_incremental_data(self) -> Dict[str, int]:
        """Sync only new and updated records from all sources"""
        if not self.talk_service:
            raise ValueError("TalkService must be provided for data synchronization")

        results = {
            "new_meetup": 0,
            "updated_meetup": 0,
            "new_sessionize": 0,
            "updated_sessionize": 0,
            "errors": 0
        }

        # Sync Meetup data incrementally
        try:
            logger.info("Starting meetup sync...")
            meetup_results = self.sync_meetup_incremental()
            logger.info(f"Meetup sync completed with results: {meetup_results}")
            if meetup_results is None:
                meetup_results = {"new_meetup": 0, "updated_meetup": 0}
            results["new_meetup"] = meetup_results.get("new_meetup", 0) or 0
            results["updated_meetup"] = meetup_results.get("updated_meetup", 0) or 0
            self.talk_service.update_sync_status("meetup", success=True)
        except Exception as e:
            import traceback
            logger.error(f"Failed to sync Meetup data: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            results["errors"] += 1
            self.talk_service.update_sync_status("meetup", success=False, error_message=str(e))

        # Sync Sessionize data incrementally
        try:
            sessionize_results = self.sync_sessionize_incremental()
            if sessionize_results is None:
                sessionize_results = {"new_sessionize": 0, "updated_sessionize": 0}
            results["new_sessionize"] = sessionize_results.get("new_sessionize", 0) or 0
            results["updated_sessionize"] = sessionize_results.get("updated_sessionize", 0) or 0
            self.talk_service.update_sync_status("sessionize", success=True)
        except Exception as e:
            logger.error(f"Failed to sync Sessionize data: {e}")
            results["errors"] += 1
            self.talk_service.update_sync_status("sessionize", success=False, error_message=str(e))

        return results

    def sync_meetup_incremental(self) -> Dict[str, int]:
        """Sync Meetup data incrementally"""
        results = {"new_meetup": 0, "updated_meetup": 0}
        
        # Get last sync time
        last_sync = self.talk_service.get_last_sync_time("meetup")
        logger.info(f"Last meetup sync: {last_sync}")
        
        # Initialize meetup client
        meetup = Meetup()
        
        # Get all events (for now, we'll check all and filter by updated_at)
        # In a real implementation, you'd want to use since_datetime if Meetup API supports it
        events = meetup.get_all_data()
        logger.info(f"Found {len(events)} meetup events")
        
        # Debug: Check if events is None or empty
        if events is None:
            logger.warning("Meetup events is None")
            return results
        if not events:
            logger.warning("No meetup events found")
            return results
        
        for event in events:
            try:
                # Convert meetup event to our talk format
                talk_data = self._convert_meetup_to_talk(event)
                
                # Check if talk already exists
                existing_talk = self.talk_service.get_talk_by_source(
                    source_id=event.id,
                    source_type="meetup"
                )
                
                if existing_talk:
                    # Check if we should update (compare timestamps or content)
                    if self._should_update_talk(existing_talk, talk_data):
                        talk_id = self.talk_service.upsert_talk(talk_data)
                        if talk_id:
                            # Ensure results["updated_meetup"] is not None before incrementing
                            if results.get("updated_meetup") is None:
                                results["updated_meetup"] = 0
                            results["updated_meetup"] += 1
                            logger.info(f"Updated meetup talk: {talk_data['id']}")
                else:
                    # Create new talk
                    talk_id = self.talk_service.upsert_talk(talk_data)
                    if talk_id:
                        # Ensure results["new_meetup"] is not None before incrementing
                        if results.get("new_meetup") is None:
                            results["new_meetup"] = 0
                        results["new_meetup"] += 1
                        logger.info(f"Created new meetup talk: {talk_data['id']}")
                    
            except Exception as e:
                logger.error(f"Failed to process meetup event {event.id}: {e}")
                continue
        
        logger.info(f"Meetup sync results: {results}")
        return results

    def sync_sessionize_incremental(self) -> Dict[str, int]:
        """Sync Sessionize data incrementally"""
        results = {"new_sessionize": 0, "updated_sessionize": 0}
        
        # Get last sync time
        last_sync = self.talk_service.get_last_sync_time("sessionize")
        logger.info(f"Last sessionize sync: {last_sync}")
        
        # Initialize sessionize client
        sessionize = Sessionize()
        
        # Get all talks
        talks = sessionize.get_all_data()
        logger.info(f"Found {len(talks)} sessionize talks")
        
        for talk in talks:
            try:
                # Convert sessionize talk to our format
                talk_data = self._convert_sessionize_to_talk(talk)
                
                # Check if talk already exists
                existing_talk = self.talk_service.get_talk_by_source(
                    source_id=talk.id,
                    source_type="sessionize"
                )
                
                if existing_talk:
                    # Check if we should update
                    if self._should_update_talk(existing_talk, talk_data):
                        talk_id = self.talk_service.upsert_talk(talk_data)
                        if talk_id:
                            # Ensure results["updated_sessionize"] is not None before incrementing
                            if results.get("updated_sessionize") is None:
                                results["updated_sessionize"] = 0
                            results["updated_sessionize"] += 1
                            logger.info(f"Updated sessionize talk: {talk_data['id']}")
                else:
                    # Create new talk
                    talk_id = self.talk_service.upsert_talk(talk_data)
                    if talk_id:
                        # Ensure results["new_sessionize"] is not None before incrementing
                        if results.get("new_sessionize") is None:
                            results["new_sessionize"] = 0
                        results["new_sessionize"] += 1
                        logger.info(f"Created new sessionize talk: {talk_data['id']}")
                    
            except Exception as e:
                logger.error(f"Failed to process sessionize talk {talk.id}: {e}")
                continue
        
        logger.info(f"Sessionize sync results: {results}")
        return results

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
            "auto_tags": self._extract_auto_tags(event.title, event.description),
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
            }
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
            "speaker_names": [speaker.name for speaker in talk.speakers] if talk.speakers else [],
            "auto_tags": self._extract_auto_tags(talk.title, talk.description),
            "source_updated_at": datetime.utcnow(),  # Sessionize doesn't provide update timestamps
            "type_specific_data": {
                "event_name": talk.event_name,
                "room": talk.room,
                "start_time": talk.start_time,
                "end_time": talk.end_time,
            }
        }

    def _should_update_talk(self, existing_talk: Dict, new_talk_data: Dict) -> bool:
        """Determine if an existing talk should be updated"""
        # For now, we'll update if the content has changed
        # In a more sophisticated system, you'd compare timestamps
        
        # Compare key fields that might change
        if existing_talk.get("title") != new_talk_data.get("title"):
            return True
        if existing_talk.get("description") != new_talk_data.get("description"):
            return True
        if existing_talk.get("speaker_names") != new_talk_data.get("speaker_names"):
            return True
            
        # Check if it's been more than 24 hours since last sync
        if existing_talk.get("last_synced"):
            try:
                from datetime import timedelta
                last_synced = datetime.fromisoformat(existing_talk["last_synced"].replace('Z', '+00:00'))
                if datetime.utcnow() - last_synced > timedelta(hours=24):
                    return True
            except (ValueError, TypeError):
                return True
        
        return False
