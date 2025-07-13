# tests/test_taxonomy_service.py
"""
Tests for Ring 2: Taxonomy service layer operations
These tests verify the business logic orchestration in TalkService for taxonomy operations.
Uses mocked database client to test service logic without database dependencies.
"""
import pytest
from unittest.mock import Mock, patch
from backend.services.talk_service import TalkService
from backend.database.postgres_client import PostgresClient


class TestTaxonomyService:
    """Test the taxonomy service operations with real database"""

    def test_create_taxonomy_success(self, postgres_client):
        """Test successful taxonomy creation through service layer"""
        service = TalkService(postgres_client=postgres_client)

        taxonomy_id = service.create_taxonomy(
            name="service_test_difficulty",
            description="Service test difficulty levels",
            created_by="service_test",
        )

        assert taxonomy_id is not None
        assert isinstance(taxonomy_id, int)

        # Verify through service layer
        taxonomies = service.get_taxonomies()
        test_taxonomy = next(
            (t for t in taxonomies if t["name"] == "service_test_difficulty"), None
        )
        assert test_taxonomy is not None
        assert test_taxonomy["description"] == "Service test difficulty levels"

    def test_create_taxonomy_value_success(self, postgres_client):
        """Test successful taxonomy value creation"""
        service = TalkService(postgres_client=postgres_client)

        # Create taxonomy first
        taxonomy_id = service.create_taxonomy(name="service_test_topic")

        # Create value
        value_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id,
            value="service-web-dev",
            description="Service test web development",
            color="#00FF00",
        )

        assert value_id is not None
        assert isinstance(value_id, int)

        # Verify through service layer
        taxonomies = service.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert len(test_taxonomy["values"]) == 1
        assert test_taxonomy["values"][0]["value"] == "service-web-dev"

    def test_initialize_default_taxonomies(self, postgres_client):
        """Test initialization of default taxonomies"""
        service = TalkService(postgres_client=postgres_client)

        # Delete existing taxonomies to ensure clean state
        existing_taxonomies = service.get_taxonomies()
        for taxonomy in existing_taxonomies:
            if taxonomy.get("is_system"):
                service.delete_taxonomy(taxonomy["id"])

        # Initialize defaults
        service.initialize_default_taxonomies()

        taxonomies = service.get_taxonomies()
        taxonomy_names = [t["name"] for t in taxonomies]

        # Verify all default taxonomies exist
        assert "difficulty" in taxonomy_names
        assert "topic" in taxonomy_names
        assert "conference" in taxonomy_names

        # Verify difficulty taxonomy has expected values
        difficulty_taxonomy = next(
            (t for t in taxonomies if t["name"] == "difficulty"), None
        )
        assert difficulty_taxonomy is not None
        difficulty_values = [v["value"] for v in difficulty_taxonomy["values"]]
        assert "beginner" in difficulty_values
        assert "intermediate" in difficulty_values
        assert "advanced" in difficulty_values

        # Verify topic taxonomy has expected values
        topic_taxonomy = next((t for t in taxonomies if t["name"] == "topic"), None)
        assert topic_taxonomy is not None
        topic_values = [v["value"] for v in topic_taxonomy["values"]]
        assert "web-development" in topic_values
        assert "data-science" in topic_values
        assert "ai-ml" in topic_values

    def test_update_taxonomy_success(self, postgres_client):
        """Test successful taxonomy update"""
        service = TalkService(postgres_client=postgres_client)

        # Create taxonomy
        taxonomy_id = service.create_taxonomy(name="service_update_test")

        # Update taxonomy
        success = service.update_taxonomy(
            taxonomy_id=taxonomy_id,
            name="service_updated_name",
            description="Updated description",
        )
        assert success is True

        # Verify update
        taxonomies = service.get_taxonomies()
        updated_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert updated_taxonomy["name"] == "service_updated_name"
        assert updated_taxonomy["description"] == "Updated description"

    def test_delete_taxonomy_success(self, postgres_client):
        """Test successful taxonomy deletion"""
        service = TalkService(postgres_client=postgres_client)

        # Create taxonomy
        taxonomy_id = service.create_taxonomy(name="service_delete_test")

        # Verify exists
        taxonomies = service.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert test_taxonomy is not None

        # Delete taxonomy
        success = service.delete_taxonomy(taxonomy_id)
        assert success is True

        # Verify deleted
        taxonomies = service.get_taxonomies()
        deleted_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert deleted_taxonomy is None


class TestTalkTaggingService:
    """Test talk tagging operations through service layer"""

    def test_add_tags_to_talk_success(self, postgres_client):
        """Test adding tags to a talk through service layer"""
        service = TalkService(postgres_client=postgres_client)

        # Create talk
        talk_data = {
            "id": "service_tag_test",
            "talk_type": "pycon",
            "title": "Service Tag Test",
            "description": "Test talk for service tagging",
            "speaker_names": ["Test Speaker"],
        }
        service.create_talk(talk_data)

        # Create taxonomy and values
        taxonomy_id = service.create_taxonomy(name="service_tagging")
        value1_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="service_tag1"
        )
        value2_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="service_tag2"
        )

        # Add tags through service
        success = service.add_tags_to_talk("service_tag_test", [value1_id, value2_id])
        assert success is True

        # Verify tags added
        talk_tags = service.get_talk_tags_grouped("service_tag_test")
        assert talk_tags is not None
        assert "service_tagging" in talk_tags["manual_tags"]
        assert len(talk_tags["manual_tags"]["service_tagging"]) == 2

    def test_replace_talk_tags_success(self, postgres_client):
        """Test replacing talk tags through service layer"""
        service = TalkService(postgres_client=postgres_client)

        # Create talk and taxonomy
        talk_data = {
            "id": "service_replace_test",
            "talk_type": "pycon",
            "title": "Service Replace Test",
            "description": "Test talk",
            "speaker_names": ["Test Speaker"],
        }
        service.create_talk(talk_data)

        taxonomy_id = service.create_taxonomy(name="service_replace")
        old_tag_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="old_tag"
        )
        new_tag_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="new_tag"
        )

        # Add initial tags
        service.add_tags_to_talk("service_replace_test", [old_tag_id])

        # Replace tags
        success = service.replace_talk_tags("service_replace_test", [new_tag_id])
        assert success is True

        # Verify replacement
        talk_tags = service.get_talk_tags_grouped("service_replace_test")
        assert "service_replace" in talk_tags["manual_tags"]
        assert len(talk_tags["manual_tags"]["service_replace"]) == 1
        assert talk_tags["manual_tags"]["service_replace"][0] == "new_tag"

    def test_remove_tag_from_talk_success(self, postgres_client):
        """Test removing specific tag from talk"""
        service = TalkService(postgres_client=postgres_client)

        # Create talk and taxonomy
        talk_data = {
            "id": "service_remove_test",
            "talk_type": "pycon",
            "title": "Service Remove Test",
            "description": "Test talk",
            "speaker_names": ["Test Speaker"],
        }
        service.create_talk(talk_data)

        taxonomy_id = service.create_taxonomy(name="service_remove")
        keep_tag_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="keep_tag"
        )
        remove_tag_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="remove_tag"
        )

        # Add both tags
        service.add_tags_to_talk("service_remove_test", [keep_tag_id, remove_tag_id])

        # Remove one tag
        success = service.remove_tag_from_talk("service_remove_test", remove_tag_id)
        assert success is True

        # Verify only one remains
        talk_tags = service.get_talk_tags_grouped("service_remove_test")
        assert "service_remove" in talk_tags["manual_tags"]
        assert len(talk_tags["manual_tags"]["service_remove"]) == 1
        assert talk_tags["manual_tags"]["service_remove"][0] == "keep_tag"


class TestBulkOperations:
    """Test Phase 2 bulk operations"""

    def test_bulk_update_talk_tags_success(self, postgres_client):
        """Test bulk tag operations"""
        service = TalkService(postgres_client=postgres_client)

        # Create talks and taxonomy
        talk_ids = ["bulk_talk_1", "bulk_talk_2", "bulk_talk_3"]
        for talk_id in talk_ids:
            talk_data = {
                "id": talk_id,
                "talk_type": "pycon",
                "title": f"Bulk Test Talk {talk_id}",
                "description": "Test talk",
                "speaker_names": ["Test Speaker"],
            }
            service.create_talk(talk_data)

        taxonomy_id = service.create_taxonomy(name="bulk_test")
        tag1_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="bulk_tag1"
        )
        tag2_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="bulk_tag2"
        )
        tag3_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="bulk_tag3"
        )

        # Define bulk operations
        operations = [
            {
                "action": "add",
                "talk_id": "bulk_talk_1",
                "taxonomy_value_ids": [tag1_id, tag2_id],
            },
            {
                "action": "add",
                "talk_id": "bulk_talk_2",
                "taxonomy_value_ids": [tag2_id, tag3_id],
            },
            {
                "action": "replace",
                "talk_id": "bulk_talk_3",
                "taxonomy_value_ids": [tag1_id],
            },
        ]

        # Execute bulk operations
        success = service.bulk_update_talk_tags(operations)
        assert success is True

        # Verify results
        talk1_tags = service.get_talk_tags_grouped("bulk_talk_1")
        assert len(talk1_tags["manual_tags"]["bulk_test"]) == 2

        talk2_tags = service.get_talk_tags_grouped("bulk_talk_2")
        assert len(talk2_tags["manual_tags"]["bulk_test"]) == 2

        talk3_tags = service.get_talk_tags_grouped("bulk_talk_3")
        assert len(talk3_tags["manual_tags"]["bulk_test"]) == 1
        assert talk3_tags["manual_tags"]["bulk_test"][0] == "bulk_tag1"

    def test_bulk_update_partial_failure(self, postgres_client):
        """Test bulk operations with some failures"""
        service = TalkService(postgres_client=postgres_client)

        # Create one valid talk
        talk_data = {
            "id": "bulk_valid_talk",
            "talk_type": "pycon",
            "title": "Valid Bulk Talk",
            "description": "Test talk",
            "speaker_names": ["Test Speaker"],
        }
        service.create_talk(talk_data)

        taxonomy_id = service.create_taxonomy(name="bulk_fail_test")
        valid_tag_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="valid_tag"
        )

        # Operations with invalid talk ID
        operations = [
            {
                "action": "add",
                "talk_id": "bulk_valid_talk",
                "taxonomy_value_ids": [valid_tag_id],
            },
            {
                "action": "add",
                "talk_id": "invalid_talk_id",
                "taxonomy_value_ids": [valid_tag_id],
            },
        ]

        # Should return False due to partial failure
        success = service.bulk_update_talk_tags(operations)
        assert success is False  # Not all operations succeeded


class TestAnalyticsService:
    """Test Phase 2 analytics features"""

    def test_get_taxonomy_value_counts(self, postgres_client):
        """Test getting taxonomy value usage counts"""
        service = TalkService(postgres_client=postgres_client)

        # Create taxonomy and values
        taxonomy_id = service.create_taxonomy(name="analytics_test")
        popular_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="popular_value"
        )
        rare_id = service.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="rare_value"
        )

        # Create talks and tag them differently
        for i in range(3):
            talk_data = {
                "id": f"analytics_talk_{i}",
                "talk_type": "pycon",
                "title": f"Analytics Test {i}",
                "description": "Test talk",
                "speaker_names": ["Test Speaker"],
            }
            service.create_talk(talk_data)

            # All talks get popular tag, only first gets rare tag
            service.add_tags_to_talk(f"analytics_talk_{i}", [popular_id])
            if i == 0:
                service.add_tags_to_talk(f"analytics_talk_{i}", [rare_id])

        # Get value counts
        counts = service.get_taxonomy_value_counts(taxonomy_id)
        assert len(counts) == 2

        # Verify counts
        popular_count = next((c for c in counts if c["value"] == "popular_value"), None)
        rare_count = next((c for c in counts if c["value"] == "rare_value"), None)

        assert popular_count["usage_count"] == 3
        assert rare_count["usage_count"] == 1

    def test_get_most_popular_tags(self, postgres_client):
        """Test getting most popular tags across taxonomies"""
        service = TalkService(postgres_client=postgres_client)

        # Create multiple taxonomies
        tax1_id = service.create_taxonomy(name="popularity_test1")
        tax2_id = service.create_taxonomy(name="popularity_test2")

        very_popular_id = service.create_taxonomy_value(
            taxonomy_id=tax1_id, value="very_popular"
        )
        somewhat_popular_id = service.create_taxonomy_value(
            taxonomy_id=tax2_id, value="somewhat_popular"
        )

        # Create talks with different tag popularity
        for i in range(5):
            talk_data = {
                "id": f"popularity_talk_{i}",
                "talk_type": "pycon",
                "title": f"Popularity Test {i}",
                "description": "Test talk",
                "speaker_names": ["Test Speaker"],
            }
            service.create_talk(talk_data)

            # All get very_popular, some get somewhat_popular
            service.add_tags_to_talk(f"popularity_talk_{i}", [very_popular_id])
            if i < 2:
                service.add_tags_to_talk(f"popularity_talk_{i}", [somewhat_popular_id])

        # Get popular tags
        popular_tags = service.get_most_popular_tags(limit=2)
        assert len(popular_tags) >= 2

        # Verify ordering
        assert popular_tags[0]["value"] == "very_popular"
        assert popular_tags[0]["usage_count"] == 5
        assert popular_tags[1]["value"] == "somewhat_popular"
        assert popular_tags[1]["usage_count"] == 2

    def test_advanced_search_talks(self, postgres_client):
        """Test advanced search with taxonomy filters"""
        service = TalkService(postgres_client=postgres_client)

        # Create taxonomies
        difficulty_id = service.create_taxonomy(name="search_difficulty")
        topic_id = service.create_taxonomy(name="search_topic")

        beginner_id = service.create_taxonomy_value(
            taxonomy_id=difficulty_id, value="beginner"
        )
        advanced_id = service.create_taxonomy_value(
            taxonomy_id=difficulty_id, value="advanced"
        )
        web_id = service.create_taxonomy_value(taxonomy_id=topic_id, value="web")
        ai_id = service.create_taxonomy_value(taxonomy_id=topic_id, value="ai")

        # Create test talks
        test_talks = [
            {
                "id": "search_1",
                "title": "Beginner Web Guide",
                "tags": [beginner_id, web_id],
            },
            {
                "id": "search_2",
                "title": "Advanced AI Methods",
                "tags": [advanced_id, ai_id],
            },
            {
                "id": "search_3",
                "title": "Web Security Advanced",
                "tags": [advanced_id, web_id],
            },
        ]

        for talk_data in test_talks:
            service.create_talk(
                {
                    "id": talk_data["id"],
                    "talk_type": "pycon",
                    "title": talk_data["title"],
                    "description": "Test description",
                    "speaker_names": ["Test Speaker"],
                }
            )
            service.add_tags_to_talk(talk_data["id"], talk_data["tags"])

        # Test filtering by difficulty
        talks, total = service.advanced_search_talks(
            taxonomy_filters={"search_difficulty": ["beginner"]}
        )
        assert total == 1
        assert talks[0]["title"] == "Beginner Web Guide"

        # Test filtering by multiple taxonomies
        talks, total = service.advanced_search_talks(
            taxonomy_filters={
                "search_difficulty": ["advanced"],
                "search_topic": ["web"],
            }
        )
        assert total == 1
        assert talks[0]["title"] == "Web Security Advanced"

        # Test text search with taxonomy filter
        talks, total = service.advanced_search_talks(
            query="Security", taxonomy_filters={"search_difficulty": ["advanced"]}
        )
        assert total == 1
        assert talks[0]["title"] == "Web Security Advanced"
