from typing import List, Optional, Dict, Any, Tuple
from backend.contracts.repositories import TalkRepository
from backend.domain.entities.talk import Talk
from backend.database.postgres_client import PostgresClient


class PostgresTalkRepository(TalkRepository):
    """PostgreSQL implementation of TalkRepository - Infrastructure Layer (Ring 4)"""

    def __init__(self, postgres_client: PostgresClient):
        self.db = postgres_client

    def save(self, talk: Talk) -> str:
        """Save a talk to PostgreSQL"""
        # Convert domain entity to database format
        talk_data = self._entity_to_db_format(talk)
        return self.db.index_talk(talk_data)

    def find_by_id(self, talk_id: str) -> Optional[Talk]:
        """Find a talk by ID"""
        db_talk = self.db.get_talk(talk_id)
        if not db_talk:
            return None
        return self._db_to_entity_format(db_talk)

    def find_by_source(self, source_id: str, source_type: str) -> Optional[Talk]:
        """Find a talk by source ID and type"""
        db_talk = self.db.get_talk_by_source(source_id, source_type)
        if not db_talk:
            return None
        return self._db_to_entity_format(db_talk)

    def search(
        self, query: str = "", filters: Dict[str, Any] = None
    ) -> Tuple[List[Talk], int]:
        """Search talks with optional filters"""
        if filters is None:
            filters = {}

        # Convert domain filters to database filters
        db_filters = self._domain_to_db_filters(filters)

        # Execute search in database
        db_results, total_count = self.db.search_talks(query, db_filters)

        # Convert results back to domain entities
        talks = [self._db_to_entity_format(db_talk) for db_talk in db_results]

        return talks, total_count

    def update(self, talk: Talk) -> bool:
        """Update an existing talk"""
        # For now, re-index the talk as there's no direct update method
        # This could be enhanced with a proper update method in PostgresClient
        talk_data = self._entity_to_db_format(talk)
        try:
            self.db.index_talk(talk_data)
            return True
        except Exception:
            return False

    def delete(self, talk_id: str) -> bool:
        """Delete a talk by ID"""
        # PostgresClient doesn't have delete_talk method yet
        # This would need to be implemented
        # For now, return False to indicate not implemented
        return False

    def _entity_to_db_format(self, talk: Talk) -> Dict[str, Any]:
        """Convert domain entity to database format"""
        return {
            "id": talk.id,
            "title": talk.title,
            "description": talk.description,
            "talk_type": talk.talk_type.value if talk.talk_type else None,
            "speaker_names": talk.speaker_names,
            "auto_tags": talk.auto_tags,
            "created_at": talk.created_at,
            "updated_at": talk.updated_at,
            "source_id": talk.source_id,
            "source_type": talk.source_type,
            "type_specific_data": talk.type_specific_data,
        }

    def _db_to_entity_format(self, db_talk: Dict[str, Any]) -> Talk:
        """Convert database format to domain entity"""
        return Talk.from_dict(db_talk)

    def _domain_to_db_filters(self, domain_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert domain filters to database filters"""
        # For now, pass through - could add transformation logic here
        return domain_filters
