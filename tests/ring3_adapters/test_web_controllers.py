#!/usr/bin/env python3
"""
Ring 3 Interface Adapter Tests - Clean Architecture Example
Tests for web controllers and presenters demonstrating proper Ring 3 testing patterns
"""

import pytest
from unittest.mock import Mock, MagicMock
from backend.application.use_cases.create_talk import CreateTalkUseCase


class MockWebController:
    """
    Mock web controller for testing Ring 3 interface adapter patterns
    This demonstrates how to test controllers that adapt HTTP to use cases
    """

    def __init__(self, create_talk_use_case: CreateTalkUseCase):
        self.create_talk_use_case = create_talk_use_case

    def create_talk_endpoint(self, http_request_data: dict) -> dict:
        """Convert HTTP request to use case call and format response"""
        try:
            # Ring 3 responsibility: Extract and validate HTTP request format
            if "Content-Type" not in http_request_data.get("headers", {}):
                return {
                    "status_code": 400,
                    "body": {"error": "Content-Type header required"},
                    "headers": {"Content-Type": "application/json"},
                }

            request_body = http_request_data.get("body", {})

            # Ring 3 responsibility: Convert HTTP data to use case format
            talk_data = {
                "id": request_body.get("id"),
                "title": request_body.get("title"),
                "description": request_body.get("description"),
                "speaker_names": request_body.get("speakers", []),
                "talk_type": request_body.get("type"),
                "source_type": "web_api",
                "source_id": request_body.get("id"),
            }

            # Ring 3 responsibility: Delegate to Ring 2 use case
            talk_id = self.create_talk_use_case.execute(talk_data)

            # Ring 3 responsibility: Format success response for HTTP
            return {
                "status_code": 201,
                "body": {
                    "message": "Talk created successfully",
                    "talk_id": talk_id,
                    "resource_url": f"/api/talks/{talk_id}",
                },
                "headers": {"Content-Type": "application/json"},
            }

        except ValueError as e:
            # Ring 3 responsibility: Convert business errors to HTTP format
            return {
                "status_code": 400,
                "body": {"error": f"Validation failed: {str(e)}"},
                "headers": {"Content-Type": "application/json"},
            }
        except Exception as e:
            # Ring 3 responsibility: Handle unexpected errors for HTTP
            return {
                "status_code": 500,
                "body": {"error": "Internal server error"},
                "headers": {"Content-Type": "application/json"},
            }


class MockPresenter:
    """Mock presenter for testing Ring 3 data formatting patterns"""

    @staticmethod
    def present_talk_creation_success(talk_id: str, talk_data: dict) -> dict:
        """Format successful talk creation for presentation"""
        return {
            "success": True,
            "data": {
                "id": talk_id,
                "title": talk_data.get("title"),
                "speakers": talk_data.get("speaker_names", []),
                "type": talk_data.get("talk_type"),
                "created_at": "2025-07-20T10:30:00Z",
                "links": {
                    "self": f"/api/talks/{talk_id}",
                    "edit": f"/api/talks/{talk_id}/edit",
                    "delete": f"/api/talks/{talk_id}",
                },
            },
            "message": "Talk has been successfully created",
        }

    @staticmethod
    def present_validation_error(errors: list) -> dict:
        """Format validation errors for presentation"""
        return {
            "success": False,
            "errors": [{"field": "general", "message": error} for error in errors],
            "message": "Please correct the validation errors and try again",
        }


class TestWebController:
    """
    Ring 3 Testing Pattern: Interface Adapters (Controllers)

    These tests focus on:
    - HTTP request/response transformations
    - Data format conversions
    - Error handling and status codes
    - Boundary adaptation between HTTP and application

    Test Strategy:
    - Mock Ring 2 use cases (application boundary)
    - Test adapter logic, not business logic
    - Focus on data transformation and protocol handling
    """

    def setup_method(self):
        """Set up test dependencies for each test"""
        # Ring 2 dependency - MOCKED (application boundary)
        self.mock_use_case = Mock(spec=CreateTalkUseCase)

        # System under test - Ring 3 controller
        self.controller = MockWebController(self.mock_use_case)

    def test_create_talk_endpoint_success(self):
        """Test successful HTTP request handling and response formatting"""
        # Arrange
        self.mock_use_case.execute.return_value = "controller-test-123"

        http_request = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "id": "http-001",
                "title": "REST API Design",
                "description": "Learn REST API best practices",
                "speakers": ["API Expert"],
                "type": "tutorial",
            },
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - HTTP response format
        assert response["status_code"] == 201
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["body"]["message"] == "Talk created successfully"
        assert response["body"]["talk_id"] == "controller-test-123"
        assert response["body"]["resource_url"] == "/api/talks/controller-test-123"

        # Assert - Use case was called with properly transformed data
        self.mock_use_case.execute.assert_called_once()
        call_args = self.mock_use_case.execute.call_args[0][0]
        assert call_args["title"] == "REST API Design"
        assert call_args["speaker_names"] == ["API Expert"]
        assert call_args["talk_type"] == "tutorial"
        assert call_args["source_type"] == "web_api"

    def test_create_talk_endpoint_missing_content_type(self):
        """Test HTTP validation for missing Content-Type header"""
        # Arrange
        http_request = {
            "headers": {},  # Missing Content-Type
            "body": {"title": "Test Talk"},
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert
        assert response["status_code"] == 400
        assert "Content-Type header required" in response["body"]["error"]

        # Verify use case was never called
        self.mock_use_case.execute.assert_not_called()

    def test_create_talk_endpoint_validation_error(self):
        """Test handling of business validation errors from use case"""
        # Arrange
        self.mock_use_case.execute.side_effect = ValueError("Title is required")

        http_request = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "title": "",  # Invalid empty title
                "speakers": ["Speaker"],
                "type": "tutorial",
            },
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - Business error converted to HTTP format
        assert response["status_code"] == 400
        assert "Validation failed: Title is required" in response["body"]["error"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_create_talk_endpoint_unexpected_error(self):
        """Test handling of unexpected system errors"""
        # Arrange
        self.mock_use_case.execute.side_effect = Exception("Database connection lost")

        http_request = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "title": "Valid Talk",
                "speakers": ["Speaker"],
                "type": "tutorial",
            },
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - System error converted to generic HTTP error
        assert response["status_code"] == 500
        assert response["body"]["error"] == "Internal server error"
        # Should not leak internal error details to client
        assert "Database connection lost" not in response["body"]["error"]

    def test_create_talk_endpoint_data_transformation(self):
        """Test proper data transformation between HTTP and application formats"""
        # Arrange
        self.mock_use_case.execute.return_value = "transform-test-id"

        # HTTP request with API-specific field names
        http_request = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "id": "api-specific-id",
                "title": "Data Transformation Test",
                "description": "Testing data format conversion",
                "speakers": ["Data Expert", "API Designer"],  # HTTP uses "speakers"
                "type": "workshop",  # HTTP uses "type"
            },
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - Verify transformation to application format
        call_args = self.mock_use_case.execute.call_args[0][0]
        assert call_args["speaker_names"] == [
            "Data Expert",
            "API Designer",
        ]  # Transformed to domain format
        assert call_args["talk_type"] == "workshop"  # Transformed to domain format
        assert call_args["source_type"] == "web_api"  # Added by controller
        assert call_args["source_id"] == "api-specific-id"  # Mapped from HTTP id

    def test_controller_is_stateless(self):
        """Test that controller can handle multiple requests safely"""
        # Arrange
        self.mock_use_case.execute.side_effect = ["id-1", "id-2"]

        request_1 = {
            "headers": {"Content-Type": "application/json"},
            "body": {"title": "Talk 1", "speakers": ["Speaker 1"], "type": "tutorial"},
        }

        request_2 = {
            "headers": {"Content-Type": "application/json"},
            "body": {"title": "Talk 2", "speakers": ["Speaker 2"], "type": "workshop"},
        }

        # Act
        response_1 = self.controller.create_talk_endpoint(request_1)
        response_2 = self.controller.create_talk_endpoint(request_2)

        # Assert - Each request handled independently
        assert response_1["body"]["talk_id"] == "id-1"
        assert response_2["body"]["talk_id"] == "id-2"
        assert self.mock_use_case.execute.call_count == 2


class TestPresenter:
    """
    Ring 3 Testing Pattern: Interface Adapters (Presenters)

    These tests focus on:
    - Data formatting for different output formats
    - Response structure consistency
    - Error message formatting
    - Presentation layer concerns
    """

    def test_present_talk_creation_success(self):
        """Test successful talk creation presentation formatting"""
        # Arrange
        talk_id = "presenter-test-123"
        talk_data = {
            "title": "Presentation Patterns",
            "speaker_names": ["Presenter Expert"],
            "talk_type": "tutorial",
        }

        # Act
        presentation = MockPresenter.present_talk_creation_success(talk_id, talk_data)

        # Assert - Presentation structure
        assert presentation["success"] is True
        assert presentation["message"] == "Talk has been successfully created"

        # Assert - Data structure
        data = presentation["data"]
        assert data["id"] == talk_id
        assert data["title"] == "Presentation Patterns"
        assert data["speakers"] == ["Presenter Expert"]
        assert data["type"] == "tutorial"
        assert "created_at" in data

        # Assert - Links structure (HATEOAS pattern)
        links = data["links"]
        assert links["self"] == f"/api/talks/{talk_id}"
        assert links["edit"] == f"/api/talks/{talk_id}/edit"
        assert links["delete"] == f"/api/talks/{talk_id}"

    def test_present_validation_error(self):
        """Test validation error presentation formatting"""
        # Arrange
        errors = ["Title is required", "At least one speaker is required"]

        # Act
        presentation = MockPresenter.present_validation_error(errors)

        # Assert
        assert presentation["success"] is False
        assert (
            presentation["message"]
            == "Please correct the validation errors and try again"
        )

        # Assert - Error structure
        assert len(presentation["errors"]) == 2
        assert presentation["errors"][0]["field"] == "general"
        assert presentation["errors"][0]["message"] == "Title is required"
        assert (
            presentation["errors"][1]["message"] == "At least one speaker is required"
        )

    def test_presenter_is_stateless(self):
        """Test that presenter methods are stateless and pure"""
        # Arrange
        talk_data_1 = {
            "title": "Talk 1",
            "speaker_names": ["Speaker 1"],
            "talk_type": "tutorial",
        }
        talk_data_2 = {
            "title": "Talk 2",
            "speaker_names": ["Speaker 2"],
            "talk_type": "workshop",
        }

        # Act - Multiple calls
        result_1 = MockPresenter.present_talk_creation_success("id-1", talk_data_1)
        result_2 = MockPresenter.present_talk_creation_success("id-2", talk_data_2)

        # Assert - Independent results
        assert result_1["data"]["title"] == "Talk 1"
        assert result_2["data"]["title"] == "Talk 2"
        assert result_1["data"]["id"] == "id-1"
        assert result_2["data"]["id"] == "id-2"


class TestInterfaceAdapterBoundaries:
    """Test that Ring 3 properly maintains architectural boundaries"""

    def test_controller_only_depends_on_use_case_interface(self):
        """Test that controller only calls use case methods, not implementation details"""
        # This test verifies that Ring 3 only uses the public interface of Ring 2
        mock_use_case = Mock(spec=CreateTalkUseCase)
        mock_use_case.execute.return_value = "boundary-test-id"

        controller = MockWebController(mock_use_case)

        request = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "title": "Boundary Test",
                "speakers": ["Tester"],
                "type": "tutorial",
            },
        }

        # Act
        controller.create_talk_endpoint(request)

        # Assert - Only the interface method was called
        mock_use_case.execute.assert_called_once()

        # Verify no other methods were accessed (would raise AttributeError if tried)
        assert not hasattr(mock_use_case, "_internal_method")

    def test_presenter_does_not_contain_business_logic(self):
        """Test that presenter only formats data, doesn't make business decisions"""
        # Presenters should be pure data transformation - no business logic
        talk_data = {
            "title": "Business Logic Test",
            "speaker_names": ["Logic Expert"],
            "talk_type": "invalid_type",  # Presenter shouldn't validate this
        }

        # Act - Presenter should format data as-is, not validate
        result = MockPresenter.present_talk_creation_success("test-id", talk_data)

        # Assert - Data passed through without business validation
        assert result["data"]["type"] == "invalid_type"  # Not validated by presenter
        assert result["success"] is True  # Presenter doesn't make business decisions


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/ring3_adapters/test_web_controllers.py -v
    pytest.main([__file__, "-v"])
