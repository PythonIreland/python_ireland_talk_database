# tests/test_taxonomy_database.py
"""
Tests for Ring 3: Taxonomy database operations
These tests verify PostgreSQL-specific taxonomy functionality including CRUD operations,
many-to-many relationships, and analytics queries.
"""
import pytest
from backend.database.postgres_client import PostgresClient
from datetime import datetime


class TestTaxonomyDatabase:
    """Test the taxonomy database operations"""

    def test_create_and_get_taxonomy(self, postgres_client):
        """Test creating and retrieving a taxonomy"""
        # Create taxonomy
        taxonomy_id = postgres_client.create_taxonomy(
            name="test_difficulty",
            description="Test difficulty levels",
            created_by="test_user",
        )
        assert taxonomy_id is not None
        assert isinstance(taxonomy_id, int)

        # Get taxonomies
        taxonomies = postgres_client.get_taxonomies()
        assert len(taxonomies) >= 1

        # Find our taxonomy
        test_taxonomy = next(
            (t for t in taxonomies if t["name"] == "test_difficulty"), None
        )
        assert test_taxonomy is not None
        assert test_taxonomy["description"] == "Test difficulty levels"
        assert test_taxonomy["created_by"] == "test_user"

    def test_create_taxonomy_value(self, postgres_client):
        """Test creating taxonomy values"""
        # Create taxonomy first
        taxonomy_id = postgres_client.create_taxonomy(
            name="test_topic", description="Test topics"
        )

        # Create taxonomy value
        value_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id,
            value="test-web-dev",
            description="Test web development",
            color="#FF0000",
        )
        assert value_id is not None
        assert isinstance(value_id, int)

        # Verify value exists in taxonomy
        taxonomies = postgres_client.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert test_taxonomy is not None
        assert len(test_taxonomy["values"]) == 1
        assert test_taxonomy["values"][0]["value"] == "test-web-dev"
        assert test_taxonomy["values"][0]["color"] == "#FF0000"

    def test_update_taxonomy(self, postgres_client):
        """Test updating a taxonomy"""
        # Create taxonomy
        taxonomy_id = postgres_client.create_taxonomy(
            name="test_update", description="Original description"
        )

        # Update taxonomy
        success = postgres_client.update_taxonomy(
            taxonomy_id=taxonomy_id,
            name="updated_name",
            description="Updated description",
        )
        assert success is True

        # Verify update
        taxonomies = postgres_client.get_taxonomies()
        updated_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert updated_taxonomy is not None
        assert updated_taxonomy["name"] == "updated_name"
        assert updated_taxonomy["description"] == "Updated description"

    def test_delete_taxonomy(self, postgres_client):
        """Test deleting a taxonomy cascades to values"""
        # Create taxonomy with value
        taxonomy_id = postgres_client.create_taxonomy(name="test_delete")
        value_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="test_value"
        )

        # Verify exists
        taxonomies = postgres_client.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert test_taxonomy is not None
        assert len(test_taxonomy["values"]) == 1

        # Delete taxonomy
        success = postgres_client.delete_taxonomy(taxonomy_id)
        assert success is True

        # Verify deleted
        taxonomies = postgres_client.get_taxonomies()
        deleted_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert deleted_taxonomy is None

    def test_update_taxonomy_value(self, postgres_client):
        """Test updating taxonomy values"""
        # Create taxonomy and value
        taxonomy_id = postgres_client.create_taxonomy(name="test_update_value")
        value_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id,
            value="original_value",
            description="Original description",
            color="#000000",
        )

        # Update value
        success = postgres_client.update_taxonomy_value(
            value_id=value_id,
            value="updated_value",
            description="Updated description",
            color="#FFFFFF",
        )
        assert success is True

        # Verify update
        taxonomies = postgres_client.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert test_taxonomy is not None
        updated_value = test_taxonomy["values"][0]
        assert updated_value["value"] == "updated_value"
        assert updated_value["description"] == "Updated description"
        assert updated_value["color"] == "#FFFFFF"

    def test_delete_taxonomy_value(self, postgres_client):
        """Test deleting taxonomy values"""
        # Create taxonomy with multiple values
        taxonomy_id = postgres_client.create_taxonomy(name="test_delete_value")
        value1_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="value1"
        )
        value2_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="value2"
        )

        # Verify both exist
        taxonomies = postgres_client.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert len(test_taxonomy["values"]) == 2

        # Delete one value
        success = postgres_client.delete_taxonomy_value(value1_id)
        assert success is True

        # Verify only one remains
        taxonomies = postgres_client.get_taxonomies()
        test_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert len(test_taxonomy["values"]) == 1
        assert test_taxonomy["values"][0]["value"] == "value2"


class TestTalkTagging:
    """Test talk-taxonomy tagging operations"""

    def test_add_tags_to_talk(self, postgres_client):
        """Test adding taxonomy tags to a talk"""
        # Create a talk
        talk_data = {
            "id": "test_talk_tags",
            "talk_type": "pycon",
            "title": "Test Talk for Tagging",
            "description": "A test talk",
            "speaker_names": ["Test Speaker"],
        }
        postgres_client.index_talk(talk_data)

        # Create taxonomy and values
        taxonomy_id = postgres_client.create_taxonomy(name="test_tagging")
        value1_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="tag1"
        )
        value2_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="tag2"
        )

        # Add tags to talk
        success = postgres_client.add_tags_to_talk(
            "test_talk_tags", [value1_id, value2_id]
        )
        assert success is True

        # Verify tags added
        talk_tags = postgres_client.get_talk_tags_with_taxonomy_info("test_talk_tags")
        assert talk_tags is not None
        assert "manual_tags" in talk_tags
        assert "test_tagging" in talk_tags["manual_tags"]
        assert len(talk_tags["manual_tags"]["test_tagging"]) == 2
        tag_values = talk_tags["manual_tags"]["test_tagging"]
        assert "tag1" in tag_values
        assert "tag2" in tag_values

    def test_replace_talk_tags(self, postgres_client):
        """Test replacing all tags on a talk"""
        # Create talk and taxonomy
        talk_data = {
            "id": "test_talk_replace",
            "talk_type": "pycon",
            "title": "Test Talk for Replace",
            "description": "A test talk",
            "speaker_names": ["Test Speaker"],
        }
        postgres_client.index_talk(talk_data)

        taxonomy_id = postgres_client.create_taxonomy(name="test_replace")
        value1_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="old_tag"
        )
        value2_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="new_tag"
        )

        # Add initial tags
        postgres_client.add_tags_to_talk("test_talk_replace", [value1_id])

        # Replace with new tags
        success = postgres_client.replace_talk_tags("test_talk_replace", [value2_id])
        assert success is True

        # Verify only new tags exist
        talk_tags = postgres_client.get_talk_tags_with_taxonomy_info(
            "test_talk_replace"
        )
        assert "manual_tags" in talk_tags
        assert "test_replace" in talk_tags["manual_tags"]
        assert len(talk_tags["manual_tags"]["test_replace"]) == 1
        assert "new_tag" in talk_tags["manual_tags"]["test_replace"]

    def test_remove_tag_from_talk(self, postgres_client):
        """Test removing specific tag from a talk"""
        # Create talk and taxonomy
        talk_data = {
            "id": "test_talk_remove",
            "talk_type": "pycon",
            "title": "Test Talk for Remove",
            "description": "A test talk",
            "speaker_names": ["Test Speaker"],
        }
        postgres_client.index_talk(talk_data)

        taxonomy_id = postgres_client.create_taxonomy(name="test_remove")
        value1_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="keep_tag"
        )
        value2_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="remove_tag"
        )

        # Add both tags
        postgres_client.add_tags_to_talk("test_talk_remove", [value1_id, value2_id])

        # Remove one tag
        success = postgres_client.remove_tag_from_talk("test_talk_remove", value2_id)
        assert success is True

        # Verify only one tag remains
        talk_tags = postgres_client.get_talk_tags_with_taxonomy_info("test_talk_remove")
        assert "manual_tags" in talk_tags
        assert "test_remove" in talk_tags["manual_tags"]
        assert len(talk_tags["manual_tags"]["test_remove"]) == 1
        assert "keep_tag" in talk_tags["manual_tags"]["test_remove"]


class TestTaxonomyAnalytics:
    """Test taxonomy analytics and reporting"""

    def test_get_taxonomy_value_counts(self, postgres_client):
        """Test getting usage counts for taxonomy values"""
        # Create taxonomy and values
        taxonomy_id = postgres_client.create_taxonomy(name="test_analytics")
        value1_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="popular_tag"
        )
        value2_id = postgres_client.create_taxonomy_value(
            taxonomy_id=taxonomy_id, value="rare_tag"
        )

        # Create talks
        for i in range(3):
            talk_data = {
                "id": f"analytics_talk_{i}",
                "talk_type": "pycon",
                "title": f"Analytics Test Talk {i}",
                "description": "Test talk",
                "speaker_names": ["Test Speaker"],
            }
            postgres_client.index_talk(talk_data)

            # Tag first two talks with popular_tag, only first with rare_tag
            postgres_client.add_tags_to_talk(f"analytics_talk_{i}", [value1_id])
            if i == 0:
                postgres_client.add_tags_to_talk(f"analytics_talk_{i}", [value2_id])

        # Get value counts
        counts = postgres_client.get_taxonomy_value_counts(taxonomy_id)
        assert len(counts) == 2

        # Find counts for each value
        popular_count = next((c for c in counts if c["value"] == "popular_tag"), None)
        rare_count = next((c for c in counts if c["value"] == "rare_tag"), None)

        assert popular_count is not None
        assert popular_count["usage_count"] == 3
        assert rare_count is not None
        assert rare_count["usage_count"] == 1

    def test_get_most_popular_tags(self, postgres_client):
        """Test getting most popular tags across all taxonomies"""
        # Create taxonomies and values
        tax1_id = postgres_client.create_taxonomy(name="test_popular1")
        tax2_id = postgres_client.create_taxonomy(name="test_popular2")

        val1_id = postgres_client.create_taxonomy_value(
            taxonomy_id=tax1_id, value="very_popular"
        )
        val2_id = postgres_client.create_taxonomy_value(
            taxonomy_id=tax2_id, value="somewhat_popular"
        )
        val3_id = postgres_client.create_taxonomy_value(
            taxonomy_id=tax1_id, value="not_popular"
        )

        # Create talks and tag them
        for i in range(5):
            talk_data = {
                "id": f"popular_talk_{i}",
                "talk_type": "pycon",
                "title": f"Popular Test Talk {i}",
                "description": "Test talk",
                "speaker_names": ["Test Speaker"],
            }
            postgres_client.index_talk(talk_data)

            # Tag all with very_popular, some with somewhat_popular, few with not_popular
            postgres_client.add_tags_to_talk(f"popular_talk_{i}", [val1_id])
            if i < 3:
                postgres_client.add_tags_to_talk(f"popular_talk_{i}", [val2_id])
            if i < 1:
                postgres_client.add_tags_to_talk(f"popular_talk_{i}", [val3_id])

        # Get popular tags
        popular_tags = postgres_client.get_most_popular_tags(limit=10)
        assert len(popular_tags) >= 3

        # Find our specific tags in the results
        very_popular_tag = next(
            (tag for tag in popular_tags if tag["value"] == "very_popular"), None
        )
        somewhat_popular_tag = next(
            (tag for tag in popular_tags if tag["value"] == "somewhat_popular"), None
        )
        not_popular_tag = next(
            (tag for tag in popular_tags if tag["value"] == "not_popular"), None
        )

        # Verify our tags exist with correct counts
        assert very_popular_tag is not None
        assert very_popular_tag["usage_count"] == 5
        assert somewhat_popular_tag is not None
        assert somewhat_popular_tag["usage_count"] == 3
        assert not_popular_tag is not None
        assert not_popular_tag["usage_count"] == 1

    def test_advanced_search_with_taxonomy_filters(self, postgres_client):
        """Test advanced search with taxonomy-based filtering"""
        # Create taxonomies
        difficulty_id = postgres_client.create_taxonomy(name="difficulty")
        topic_id = postgres_client.create_taxonomy(name="topic")

        beginner_id = postgres_client.create_taxonomy_value(
            taxonomy_id=difficulty_id, value="beginner"
        )
        advanced_id = postgres_client.create_taxonomy_value(
            taxonomy_id=difficulty_id, value="advanced"
        )
        web_id = postgres_client.create_taxonomy_value(
            taxonomy_id=topic_id, value="web-development"
        )
        ai_id = postgres_client.create_taxonomy_value(
            taxonomy_id=topic_id, value="ai-ml"
        )

        # Create test talks with different tag combinations
        talks_data = [
            {
                "id": "talk_1",
                "title": "Beginner Web Development",
                "tags": [beginner_id, web_id],
            },
            {
                "id": "talk_2",
                "title": "Advanced AI Techniques",
                "tags": [advanced_id, ai_id],
            },
            {
                "id": "talk_3",
                "title": "Beginner AI Tutorial",
                "tags": [beginner_id, ai_id],
            },
            {
                "id": "talk_4",
                "title": "Advanced Web Security",
                "tags": [advanced_id, web_id],
            },
        ]

        for talk_data in talks_data:
            postgres_client.index_talk(
                {
                    "id": talk_data["id"],
                    "talk_type": "pycon",
                    "title": talk_data["title"],
                    "description": "Test description",
                    "speaker_names": ["Test Speaker"],
                }
            )
            postgres_client.add_tags_to_talk(talk_data["id"], talk_data["tags"])

        # Test filtering by single taxonomy
        talks, total = postgres_client.advanced_search_talks(
            taxonomy_filters={"difficulty": ["beginner"]}
        )
        assert total == 2
        talk_titles = [talk["title"] for talk in talks]
        assert "Beginner Web Development" in talk_titles
        assert "Beginner AI Tutorial" in talk_titles

        # Test filtering by multiple taxonomies (AND operation)
        talks, total = postgres_client.advanced_search_talks(
            taxonomy_filters={"difficulty": ["advanced"], "topic": ["ai-ml"]}
        )
        assert total == 1
        assert talks[0]["title"] == "Advanced AI Techniques"

        # Test filtering with multiple values in same taxonomy (OR operation)
        talks, total = postgres_client.advanced_search_talks(
            taxonomy_filters={"topic": ["web-development", "ai-ml"]}
        )
        assert total == 4  # All talks have either web-development or ai-ml

        # Test combining text search with taxonomy filters
        talks, total = postgres_client.advanced_search_talks(
            query="Security", taxonomy_filters={"difficulty": ["advanced"]}
        )
        assert total == 1
        assert talks[0]["title"] == "Advanced Web Security"
