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
        }

        # Type-specific data - everything else goes here
        type_specific_data = {}
        for key, value in talk_data.items():
            if key not in postgres_data:
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
