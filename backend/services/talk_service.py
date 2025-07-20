# backend/services/talk_service.py
from typing import Dict, List, Any, Optional, Tuple
import logging
from backend.database.postgres_client import PostgresClient
from backend.domain.models import TalkType
from backend.core.config import settings

logger = logging.getLogger(__name__)


class TalkService:
    """Service layer for talk operations - Ring 2 of the architecture"""

    def __init__(self, postgres_client: Optional[PostgresClient] = None):
        # Allow dependency injection for testing
        self.db = postgres_client or PostgresClient(settings.database_url)

    def is_healthy(self) -> bool:
        """Check service health"""
        return self.db.is_healthy()

    def init_database(self) -> bool:
        """Initialize database"""
        return self.db.init_database()

    def create_talk(self, talk_data: Dict[str, Any]) -> str:
        """Create a new talk"""
        # Convert talk data to the format expected by Postgres
        postgres_data = self._convert_to_postgres_format(talk_data)
        return self.db.index_talk(postgres_data)

    def get_talk(self, talk_id: str) -> Optional[Dict[str, Any]]:
        """Get a single talk by ID"""
        return self.db.get_talk(talk_id)

    def search_talks(
        self,
        query: Optional[str] = None,
        talk_types: Optional[List[TalkType]] = None,
        tags: Optional[List[str]] = None,
        events: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search talks with filters"""

        # Convert TalkType enums to strings
        type_strings = None
        if talk_types:
            type_strings = [t.value for t in talk_types]

        return self.db.search_talks(
            query=query,
            talk_types=type_strings,
            tags=tags,
            events=events,
            cities=cities,
            limit=limit,
            offset=offset,
        )

    def update_talk_tags(self, talk_id: str, taxonomy_value_ids: List[int]) -> bool:
        """Update manual tags for a talk"""
        return self.db.update_talk_tags(talk_id, taxonomy_value_ids)

    def get_events(self) -> List[str]:
        """Get all event names"""
        return self.db.get_all_events()

    def get_tags(self) -> Dict[str, int]:
        """Get all auto tags with counts"""
        return self.db.get_all_tags()

    def get_talk_count(self) -> int:
        """Get total number of talks"""
        return self.db.get_talk_count()

    def delete_all_talks(self) -> bool:
        """Delete all talks (testing only)"""
        return self.db.delete_all_talks()

    def _convert_to_postgres_format(self, talk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert talk data from pipeline format to Postgres format"""

        # Core fields that map directly
        postgres_data = {
            "id": talk_data.get("id"),
            "talk_type": talk_data.get("talk_type"),
            "title": talk_data.get("title", ""),
            "description": talk_data.get("description", ""),
            "speaker_names": talk_data.get("speaker_names", []),
            "auto_tags": talk_data.get("auto_tags", []),
            "created_at": talk_data.get("created_at"),
            "updated_at": talk_data.get("updated_at"),
            # New sync tracking fields
            "source_id": talk_data.get("source_id"),
            "source_type": talk_data.get("source_type"),
            "last_synced": talk_data.get("last_synced"),
            "source_updated_at": talk_data.get("source_updated_at"),
        }

        # Type-specific data - everything else goes here
        type_specific_data = {}
        excluded_keys = {
            "id", "talk_type", "title", "description", "speaker_names", 
            "auto_tags", "created_at", "updated_at", "source_id", 
            "source_type", "last_synced", "source_updated_at", "type_specific_data"
        }
        
        for key, value in talk_data.items():
            if key not in excluded_keys:
                type_specific_data[key] = value

        postgres_data["type_specific_data"] = type_specific_data

        return postgres_data

    # Taxonomy management methods

    def create_taxonomy(
        self, name: str, description: str = "", created_by: str = "system"
    ) -> Optional[int]:
        """Create a new taxonomy"""
        return self.db.create_taxonomy(name, description, created_by)

    def create_taxonomy_value(
        self, taxonomy_id: int, value: str, description: str = "", color: str = ""
    ) -> Optional[int]:
        """Create a new taxonomy value"""
        return self.db.create_taxonomy_value(taxonomy_id, value, description, color)

    def get_taxonomies(self) -> List[Dict[str, Any]]:
        """Get all taxonomies with their values"""
        return self.db.get_taxonomies()

    def initialize_default_taxonomies(self) -> None:
        """Initialize default taxonomies for the system"""
        default_taxonomies = [
            {
                "name": "difficulty",
                "description": "Talk difficulty level",
                "values": [
                    {
                        "value": "beginner",
                        "description": "Suitable for beginners",
                        "color": "#4CAF50",
                    },
                    {
                        "value": "intermediate",
                        "description": "Some Python experience required",
                        "color": "#FF9800",
                    },
                    {
                        "value": "advanced",
                        "description": "Advanced Python knowledge required",
                        "color": "#F44336",
                    },
                ],
            },
            {
                "name": "topic",
                "description": "Main topic areas",
                "values": [
                    {
                        "value": "web-development",
                        "description": "Web frameworks and development",
                        "color": "#2196F3",
                    },
                    {
                        "value": "data-science",
                        "description": "Data analysis and machine learning",
                        "color": "#9C27B0",
                    },
                    {
                        "value": "testing",
                        "description": "Testing frameworks and practices",
                        "color": "#607D8B",
                    },
                    {
                        "value": "devops",
                        "description": "Deployment and infrastructure",
                        "color": "#795548",
                    },
                    {
                        "value": "ai-ml",
                        "description": "Artificial Intelligence and Machine Learning",
                        "color": "#E91E63",
                    },
                ],
            },
            {
                "name": "conference",
                "description": "Conference or event names",
                "values": [],  # Will be populated from actual data
            },
        ]

        for taxonomy_def in default_taxonomies:
            taxonomy_id = self.create_taxonomy(
                name=taxonomy_def["name"],
                description=taxonomy_def["description"],
                created_by="system",
            )

            if taxonomy_id:
                for value_def in taxonomy_def["values"]:
                    self.create_taxonomy_value(
                        taxonomy_id=taxonomy_id,
                        value=value_def["value"],
                        description=value_def["description"],
                        color=value_def.get("color", ""),
                    )

        logger.info("Default taxonomies initialized")

    def update_taxonomy(
        self, taxonomy_id: int, name: str = None, description: str = None
    ) -> bool:
        """Update taxonomy"""
        return self.db.update_taxonomy(taxonomy_id, name=name, description=description)

    def delete_taxonomy(self, taxonomy_id: int) -> bool:
        """Delete taxonomy and all its values"""
        return self.db.delete_taxonomy(taxonomy_id)

    def update_taxonomy_value(
        self,
        value_id: int,
        value: str = None,
        description: str = None,
        color: str = None,
    ) -> bool:
        """Update taxonomy value"""
        return self.db.update_taxonomy_value(
            value_id, value=value, description=description, color=color
        )

    def delete_taxonomy_value(self, value_id: int) -> bool:
        """Delete taxonomy value"""
        return self.db.delete_taxonomy_value(value_id)

    def get_talk_tags_grouped(self, talk_id: str) -> Optional[Dict[str, Any]]:
        """Get talk tags grouped by taxonomy"""
        return self.db.get_talk_tags_with_taxonomy_info(talk_id)

    def replace_talk_tags(self, talk_id: str, taxonomy_value_ids: List[int]) -> bool:
        """Replace all manual tags for a talk"""
        return self.db.replace_talk_tags(talk_id, taxonomy_value_ids)

    def add_tags_to_talk(self, talk_id: str, taxonomy_value_ids: List[int]) -> bool:
        """Add specific tags to a talk"""
        return self.db.add_tags_to_talk(talk_id, taxonomy_value_ids)

    def remove_tag_from_talk(self, talk_id: str, value_id: int) -> bool:
        """Remove specific tag from talk"""
        return self.db.remove_tag_from_talk(talk_id, value_id)

    def get_taxonomy_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all taxonomies"""
        return self.db.get_tag_usage_stats()

    def get_most_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most used tags across all taxonomies"""
        return self.db.get_most_popular_tags(limit)

    # ===== PHASE 2: ENHANCED SERVICE LAYER METHODS =====

    def get_taxonomy_value_counts(self, taxonomy_id: int) -> List[Dict[str, Any]]:
        """Get usage counts for values in a specific taxonomy"""
        return self.db.get_taxonomy_value_counts(taxonomy_id)

    def bulk_update_talk_tags(self, operations: List[Dict]) -> bool:
        """Perform bulk tag operations for efficiency

        Expected operation format:
        {
            "action": "add|remove|replace",
            "talk_id": "talk_id",
            "taxonomy_value_ids": [1, 2, 3],  # for add/replace
            "taxonomy_value_id": 1  # for remove (single)
        }
        """
        try:
            success_count = 0
            for operation in operations:
                action = operation.get("action")
                talk_id = operation.get("talk_id")

                if action == "add":
                    taxonomy_value_ids = operation.get("taxonomy_value_ids", [])
                    if self.add_tags_to_talk(talk_id, taxonomy_value_ids):
                        success_count += 1

                elif action == "remove":
                    taxonomy_value_id = operation.get("taxonomy_value_id")
                    if taxonomy_value_id and self.remove_tag_from_talk(
                        talk_id, taxonomy_value_id
                    ):
                        success_count += 1

                elif action == "replace":
                    taxonomy_value_ids = operation.get("taxonomy_value_ids", [])
                    if self.replace_talk_tags(talk_id, taxonomy_value_ids):
                        success_count += 1

            # Return True if all operations succeeded
            return success_count == len(operations)

        except Exception as e:
            print(f"Bulk operation failed: {e}")
            return False

    def advanced_search_talks(
        self,
        query: Optional[str] = None,
        talk_types: Optional[List[str]] = None,
        taxonomy_filters: Optional[Dict[str, List[str]]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """Advanced search with taxonomy-based filtering

        Args:
            query: Text search query
            talk_types: Filter by talk types
            taxonomy_filters: Dict of taxonomy_name -> [values] filters
                e.g., {"difficulty": ["beginner"], "topic": ["web-development", "ai-ml"]}
            limit: Number of results
            offset: Pagination offset

        Returns:
            Tuple of (talks, total_count)
        """
        return self.db.advanced_search_talks(
            query=query,
            talk_types=talk_types,
            taxonomy_filters=taxonomy_filters or {},
            limit=limit,
            offset=offset,
        )

    # ===== SYNC MANAGEMENT METHODS =====

    def get_sync_status(self, source_type: str) -> Optional[Dict[str, Any]]:
        """Get sync status for a specific source"""
        return self.db.get_sync_status(source_type)

    def get_all_sync_statuses(self) -> List[Dict[str, Any]]:
        """Get sync status for all sources"""
        return self.db.get_all_sync_statuses()

    def update_sync_status(self, source_type: str, success: bool = True, error_message: str = None) -> bool:
        """Update sync status for a source"""
        return self.db.update_sync_status(source_type, success, error_message)

    def get_last_sync_time(self, source_type: str) -> Optional[str]:
        """Get last sync time for a source type"""
        sync_status = self.db.get_sync_status(source_type)
        if sync_status and sync_status.get('last_sync_time'):
            return sync_status['last_sync_time']
        return None

    def upsert_talk(self, talk_data: Dict[str, Any]) -> str:
        """Insert or update talk based on source_id and source_type"""
        # Convert talk data to postgres format
        postgres_data = self._convert_to_postgres_format(talk_data)
        return self.db.upsert_talk(postgres_data)

    def get_talk_by_source(self, source_id: str, source_type: str) -> Optional[Dict[str, Any]]:
        """Get talk by source ID and type"""
        return self.db.get_talk_by_source(source_id, source_type)

    def talk_exists_by_source(self, source_id: str, source_type: str) -> bool:
        """Check if talk exists by source ID and type"""
        return self.db.get_talk_by_source(source_id, source_type) is not None

    def get_talks_needing_sync(self, source_type: str, since_datetime: Optional[str] = None) -> List[str]:
        """Get talk IDs that might need syncing"""
        from datetime import datetime
        since_dt = None
        if since_datetime:
            since_dt = datetime.fromisoformat(since_datetime.replace('Z', '+00:00'))
        return self.db.get_talks_needing_sync(source_type, since_dt)
