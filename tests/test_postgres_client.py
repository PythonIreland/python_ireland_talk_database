# tests/test_postgres_client.py
"""
Tests for Ring 2: Database/API layer using test PostgreSQL database
These tests verify PostgreSQL-specific functionality like full-text search.
"""
import pytest
from backend.database.postgres_client import PostgresClient
from datetime import datetime


class TestPostgresClient:
    """Test the database operations"""

    def test_index_and_get_talk(self, postgres_client):
        """Test creating and retrieving a talk"""
        talk_data = {
            "id": "test_talk_1",
            "talk_type": "pycon",
            "title": "Test Talk",
            "description": "A test talk about testing",
            "speaker_names": ["John Doe"],
            "auto_tags": ["Testing"],
            "type_specific_data": {"event_name": "PyCon Test", "room": "Room A"},
        }

        # Index the talk
        talk_id = postgres_client.index_talk(talk_data)
        assert talk_id == "test_talk_1"

        # Retrieve the talk
        retrieved = postgres_client.get_talk(talk_id)
        assert retrieved is not None
        assert retrieved["title"] == "Test Talk"
        assert retrieved["talk_type"] == "pycon"
        assert retrieved["speaker_names"] == ["John Doe"]

    def test_search_talks_text_search(self, postgres_client):
        """Test text search functionality"""
        # Create some test talks
        talks = [
            {
                "id": "talk_1",
                "talk_type": "pycon",
                "title": "Machine Learning Basics",
                "description": "Introduction to ML",
                "speaker_names": ["Alice"],
                "auto_tags": ["AI/ML"],
            },
            {
                "id": "talk_2",
                "talk_type": "meetup",
                "title": "Web Development with Django",
                "description": "Building web apps",
                "speaker_names": ["Bob"],
                "auto_tags": ["Web Development"],
            },
        ]

        for talk in talks:
            postgres_client.index_talk(talk)

        # Search for machine learning
        results, total = postgres_client.search_talks(query="machine learning")
        assert total > 0
        assert any("Machine Learning" in talk["title"] for talk in results)

    def test_search_talks_filters(self, postgres_client):
        """Test filtering functionality"""
        # Create test talks
        talks = [
            {
                "id": "pycon_talk",
                "talk_type": "pycon",
                "title": "PyConf Talk",
                "description": "Conference talk",
                "speaker_names": ["Speaker 1"],
                "auto_tags": ["Testing"],
                "type_specific_data": {"event_name": "PyCon 2023"},
            },
            {
                "id": "meetup_talk",
                "talk_type": "meetup",
                "title": "Meetup Talk",
                "description": "Meetup presentation",
                "speaker_names": ["Speaker 2"],
                "auto_tags": ["Web Development"],
                "type_specific_data": {"city": "Dublin"},
            },
        ]

        for talk in talks:
            postgres_client.index_talk(talk)

        # Filter by talk type
        results, total = postgres_client.search_talks(talk_types=["pycon"])
        assert total == 1
        assert results[0]["talk_type"] == "pycon"

        # Filter by tags
        results, total = postgres_client.search_talks(tags=["Testing"])
        assert total == 1
        assert "Testing" in results[0]["auto_tags"]

    def test_get_talk_count(self, postgres_client):
        """Test counting talks"""
        assert postgres_client.get_talk_count() == 0

        # Add a talk
        postgres_client.index_talk(
            {
                "id": "count_test",
                "talk_type": "other",
                "title": "Count Test",
                "description": "Test",
                "speaker_names": [],
            }
        )

        assert postgres_client.get_talk_count() == 1

    def test_update_existing_talk(self, postgres_client):
        """Test updating an existing talk"""
        # Create initial talk
        initial_data = {
            "id": "update_test",
            "talk_type": "pycon",
            "title": "Original Title",
            "description": "Original description",
            "speaker_names": ["Original Speaker"],
        }

        postgres_client.index_talk(initial_data)

        # Update the talk
        updated_data = {
            "id": "update_test",
            "talk_type": "pycon",
            "title": "Updated Title",
            "description": "Updated description",
            "speaker_names": ["Updated Speaker"],
        }

        postgres_client.index_talk(updated_data)

        # Verify update
        retrieved = postgres_client.get_talk(updated_data["id"])
        assert retrieved["title"] == "Updated Title"
        assert retrieved["description"] == "Updated description"
        assert retrieved["speaker_names"] == ["Updated Speaker"]

    def test_delete_all_talks(self, postgres_client):
        """Test deleting all talks"""
        # Add some talks
        for i in range(3):
            postgres_client.index_talk(
                {
                    "id": f"delete_test_{i}",
                    "talk_type": "other",
                    "title": f"Delete Test {i}",
                    "description": "Test",
                    "speaker_names": [],
                }
            )

        assert postgres_client.get_talk_count() == 3

        # Delete all talks
        success = postgres_client.delete_all_talks()
        assert success
        assert postgres_client.get_talk_count() == 0
