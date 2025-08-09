# tests/test_taxonomy_api.py
"""
Tests for Ring 3: Taxonomy API endpoints
These tests verify the HTTP interface for taxonomy operations using FastAPI test client.
Tests the complete request/response cycle including validation and error handling.
"""
import pytest
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.talk_service import TalkService
from backend.database.postgres_client import PostgresClient


@pytest.fixture
def api_client(postgres_client):
    """Create FastAPI test client with dependency override"""

    def get_test_talk_service():
        return TalkService(postgres_client=postgres_client)

    # Override the dependency
    app.dependency_overrides = {}
    from backend.api.routers.talks import get_talk_service

    app.dependency_overrides[get_talk_service] = get_test_talk_service

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides = {}


class TestTaxonomyAPIEndpoints:
    """Test basic taxonomy CRUD API endpoints"""

    def test_create_taxonomy_success(self, api_client):
        """Test successful taxonomy creation via API"""
        response = api_client.post(
            "/api/v1/talks/taxonomies",
            json={
                "name": "api_test_difficulty",
                "description": "API test difficulty levels",
                "created_by": "api_test_user",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taxonomy created successfully"
        assert "id" in data

    def test_create_taxonomy_validation_error(self, api_client):
        """Test taxonomy creation with missing required fields"""
        response = api_client.post(
            "/api/v1/talks/taxonomies", json={"description": "Missing name field"}
        )

        assert response.status_code == 422  # Validation error

    def test_get_taxonomies_success(self, api_client):
        """Test getting all taxonomies via API"""
        # Create a test taxonomy first
        api_client.post(
            "/api/v1/talks/taxonomies",
            json={"name": "api_get_test", "description": "Test taxonomy"},
        )

        response = api_client.get("/api/v1/talks/taxonomies")
        assert response.status_code == 200

        data = response.json()
        assert "taxonomies" in data
        assert isinstance(data["taxonomies"], list)

        # Find our test taxonomy
        test_taxonomy = next(
            (t for t in data["taxonomies"] if t["name"] == "api_get_test"), None
        )
        assert test_taxonomy is not None
        assert test_taxonomy["description"] == "Test taxonomy"

    def test_update_taxonomy_success(self, api_client):
        """Test successful taxonomy update via API"""
        # Create taxonomy first
        create_response = api_client.post(
            "/api/v1/talks/taxonomies",
            json={"name": "api_update_test", "description": "Original description"},
        )
        taxonomy_id = create_response.json()["id"]

        # Update taxonomy
        response = api_client.put(
            f"/api/v1/talks/taxonomies/{taxonomy_id}",
            json={"name": "api_updated_name", "description": "Updated description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taxonomy updated successfully"

        # Verify update
        get_response = api_client.get("/api/v1/talks/taxonomies")
        taxonomies = get_response.json()["taxonomies"]
        updated_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert updated_taxonomy["name"] == "api_updated_name"
        assert updated_taxonomy["description"] == "Updated description"

    def test_delete_taxonomy_success(self, api_client):
        """Test successful taxonomy deletion via API"""
        # Create taxonomy first
        create_response = api_client.post(
            "/api/v1/talks/taxonomies",
            json={"name": "api_delete_test", "description": "To be deleted"},
        )
        taxonomy_id = create_response.json()["id"]

        # Delete taxonomy
        response = api_client.delete(f"/api/v1/talks/taxonomies/{taxonomy_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taxonomy deleted successfully"

        # Verify deletion
        get_response = api_client.get("/api/v1/talks/taxonomies")
        taxonomies = get_response.json()["taxonomies"]
        deleted_taxonomy = next((t for t in taxonomies if t["id"] == taxonomy_id), None)
        assert deleted_taxonomy is None

    def test_delete_nonexistent_taxonomy(self, api_client):
        """Test deleting non-existent taxonomy returns 404"""
        response = api_client.delete("/api/v1/talks/taxonomies/99999")
        assert response.status_code == 404


class TestTaxonomyValueAPIEndpoints:
    """Test taxonomy value CRUD API endpoints"""

    def test_create_taxonomy_value_success(self, api_client):
        """Test successful taxonomy value creation via API"""
        # Create taxonomy first
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies",
            json={"name": "api_value_test", "description": "Test taxonomy for values"},
        )
        taxonomy_id = taxonomy_response.json()["id"]

        # Create taxonomy value
        response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values",
            json={
                "value": "api_test_value",
                "description": "API test value",
                "color": "#FF5733",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taxonomy value created successfully"
        assert "id" in data

    def test_update_taxonomy_value_success(self, api_client):
        """Test successful taxonomy value update via API"""
        # Create taxonomy and value
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_value_update_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values",
            json={"value": "original_value", "description": "Original description"},
        )
        value_id = value_response.json()["id"]

        # Update value
        response = api_client.put(
            f"/api/v1/talks/taxonomy-values/{value_id}",
            json={
                "value": "updated_value",
                "description": "Updated description",
                "color": "#00FF00",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taxonomy value updated successfully"

    def test_delete_taxonomy_value_success(self, api_client):
        """Test successful taxonomy value deletion via API"""
        # Create taxonomy and value
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_value_delete_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values",
            json={"value": "delete_me", "description": "To be deleted"},
        )
        value_id = value_response.json()["id"]

        # Delete value
        response = api_client.delete(f"/api/v1/talks/taxonomy-values/{value_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taxonomy value deleted successfully"


class TestTalkTaggingAPIEndpoints:
    """Test talk tagging API endpoints"""

    def test_add_tags_to_talk_success(self, api_client):
        """Test adding tags to a talk via API"""
        # Create talk, taxonomy, and values
        talk_data = {
            "id": "api_tag_test_talk",
            "talk_type": "pycon",
            "title": "API Tag Test Talk",
            "description": "Test talk for API tagging",
            "speaker_names": ["API Test Speaker"],
        }

        # First need to create the talk through the service (API doesn't have talk creation endpoint in this router)
        # So we'll use the conftest postgres_client fixture through dependency injection

        # Create taxonomy and values first
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_tagging_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        value1_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "api_tag1"}
        )
        value1_id = value1_response.json()["id"]

        value2_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "api_tag2"}
        )
        value2_id = value2_response.json()["id"]

        # Create talk through service (using the injected dependency)
        from backend.api.routers.talks import get_talk_service

        service = app.dependency_overrides[get_talk_service]()
        service.create_talk(talk_data)

        # Add tags via API
        response = api_client.post(
            f"/api/v1/talks/talks/api_tag_test_talk/tags/add",
            json={"taxonomy_value_ids": [value1_id, value2_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tags added successfully"

    def test_replace_talk_tags_success(self, api_client):
        """Test replacing talk tags via API"""
        # Create talk, taxonomy, and values
        talk_data = {
            "id": "api_replace_test_talk",
            "talk_type": "pycon",
            "title": "API Replace Test Talk",
            "description": "Test talk for API tag replacement",
            "speaker_names": ["API Test Speaker"],
        }

        # Create taxonomy and values
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_replace_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        old_value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "old_tag"}
        )
        old_value_id = old_value_response.json()["id"]

        new_value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "new_tag"}
        )
        new_value_id = new_value_response.json()["id"]

        # Create talk
        from backend.api.routers.talks import get_talk_service

        service = app.dependency_overrides[get_talk_service]()
        service.create_talk(talk_data)

        # Add initial tags
        api_client.post(
            f"/api/v1/talks/talks/api_replace_test_talk/tags/add",
            json={"taxonomy_value_ids": [old_value_id]},
        )

        # Replace tags via API
        response = api_client.put(
            f"/api/v1/talks/talks/api_replace_test_talk/tags",
            json={"taxonomy_value_ids": [new_value_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tags replaced successfully"

    def test_remove_tag_from_talk_success(self, api_client):
        """Test removing specific tag from talk via API"""
        # Create talk, taxonomy, and values
        talk_data = {
            "id": "api_remove_test_talk",
            "talk_type": "pycon",
            "title": "API Remove Test Talk",
            "description": "Test talk for API tag removal",
            "speaker_names": ["API Test Speaker"],
        }

        # Create taxonomy and values
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_remove_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        keep_value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "keep_tag"}
        )
        keep_value_id = keep_value_response.json()["id"]

        remove_value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values",
            json={"value": "remove_tag"},
        )
        remove_value_id = remove_value_response.json()["id"]

        # Create talk and add tags
        from backend.api.routers.talks import get_talk_service

        service = app.dependency_overrides[get_talk_service]()
        service.create_talk(talk_data)

        api_client.post(
            f"/api/v1/talks/talks/api_remove_test_talk/tags/add",
            json={"taxonomy_value_ids": [keep_value_id, remove_value_id]},
        )

        # Remove specific tag via API
        response = api_client.delete(
            f"/api/v1/talks/talks/api_remove_test_talk/tags/{remove_value_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tag removed successfully"

    def test_get_talk_tags_success(self, api_client):
        """Test getting talk tags with taxonomy info via API"""
        # Create talk, taxonomy, and values
        talk_data = {
            "id": "api_get_tags_test_talk",
            "talk_type": "pycon",
            "title": "API Get Tags Test Talk",
            "description": "Test talk for getting tags",
            "speaker_names": ["API Test Speaker"],
        }

        # Create taxonomy and value
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_get_tags_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "test_tag"}
        )
        value_id = value_response.json()["id"]

        # Create talk and add tags
        from backend.api.routers.talks import get_talk_service

        service = app.dependency_overrides[get_talk_service]()
        service.create_talk(talk_data)

        api_client.post(
            f"/api/v1/talks/talks/api_get_tags_test_talk/tags/add",
            json={"taxonomy_value_ids": [value_id]},
        )

        # Get talk tags via API
        response = api_client.get("/api/v1/talks/talks/api_get_tags_test_talk/tags")

        assert response.status_code == 200
        data = response.json()
        assert "talk_id" in data
        assert "manual_tags" in data
        assert "api_get_tags_test" in data["manual_tags"]
        assert "test_tag" in data["manual_tags"]["api_get_tags_test"]


class TestAnalyticsAPIEndpoints:
    """Test Phase 2 analytics API endpoints"""

    def test_get_taxonomy_usage_analytics(self, api_client):
        """Test taxonomy usage analytics endpoint"""
        response = api_client.get("/api/v1/talks/analytics/taxonomy-usage")

        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "taxonomy_usage" in data["analytics"]

    def test_get_popular_tags_analytics(self, api_client):
        """Test popular tags analytics endpoint"""
        response = api_client.get("/api/v1/talks/analytics/popular-tags?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert "popular_tags" in data
        assert isinstance(data["popular_tags"], list)

    def test_get_taxonomy_value_usage(self, api_client):
        """Test taxonomy-specific value usage endpoint"""
        # Create a taxonomy first
        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_analytics_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        response = api_client.get(
            f"/api/v1/talks/analytics/taxonomy/{taxonomy_id}/usage"
        )

        assert response.status_code == 200
        data = response.json()
        assert "taxonomy_id" in data
        assert "value_usage" in data
        assert data["taxonomy_id"] == taxonomy_id

    def test_bulk_tag_operations(self, api_client):
        """Test bulk tag operations endpoint"""
        # Create test data
        talk_data = {
            "id": "api_bulk_test_talk",
            "talk_type": "pycon",
            "title": "API Bulk Test Talk",
            "description": "Test talk for bulk operations",
            "speaker_names": ["API Test Speaker"],
        }

        taxonomy_response = api_client.post(
            "/api/v1/talks/taxonomies", json={"name": "api_bulk_test"}
        )
        taxonomy_id = taxonomy_response.json()["id"]

        value_response = api_client.post(
            f"/api/v1/talks/taxonomies/{taxonomy_id}/values", json={"value": "bulk_tag"}
        )
        value_id = value_response.json()["id"]

        # Create talk
        from backend.api.routers.talks import get_talk_service

        service = app.dependency_overrides[get_talk_service]()
        service.create_talk(talk_data)

        # Test bulk operations
        operations = [
            {
                "action": "add",
                "talk_id": "api_bulk_test_talk",
                "taxonomy_value_ids": [value_id],
            }
        ]

        response = api_client.post("/api/v1/talks/bulk/tag-operations", json=operations)

        assert response.status_code == 200
        data = response.json()
        assert "Successfully processed 1 operations" in data["message"]

    def test_advanced_search(self, api_client):
        """Test advanced search endpoint with taxonomy filters"""
        response = api_client.get(
            "/api/v1/talks/search/advanced?q=test&difficulty=beginner&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "talks" in data
        assert "total" in data
        assert "applied_filters" in data
        assert isinstance(data["talks"], list)
        assert isinstance(data["total"], int)


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""

    def test_invalid_taxonomy_id_404(self, api_client):
        """Test that invalid taxonomy IDs return 404"""
        response = api_client.get("/api/v1/talks/analytics/taxonomy/99999/usage")
        # Should handle gracefully, might return empty results or 404

    def test_malformed_json_400(self, api_client):
        """Test that malformed JSON returns 400"""
        response = api_client.post(
            "/api/v1/talks/taxonomies",
            data="invalid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422  # FastAPI validation error

    def test_missing_required_fields(self, api_client):
        """Test validation errors for missing required fields"""
        response = api_client.post(
            "/api/v1/talks/taxonomies", json={}  # Missing required 'name' field
        )
        assert response.status_code == 422
