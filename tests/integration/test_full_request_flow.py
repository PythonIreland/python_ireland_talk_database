#!/usr/bin/env python3
"""
Integration Tests - Clean Architecture Example
Tests for full request flow and architecture boundary enforcement
"""

import pytest
from unittest.mock import Mock, patch
from backend.domain.entities.talk import Talk, TalkType
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.application.use_cases.create_talk import CreateTalkUseCase
from backend.contracts.repositories import TalkRepository


class MockFullRepository(TalkRepository):
    """Mock repository for integration testing"""

    def __init__(self):
        self.talks = {}
        self.next_id = 1

    def save(self, talk: Talk) -> str:
        # Use the talk's own ID for consistent lookup
        self.talks[talk.id] = talk
        return talk.id

    def find_by_id(self, talk_id: str) -> Talk | None:
        return self.talks.get(talk_id)

    def search(self, query: str, filters: dict) -> tuple[list[Talk], int]:
        results = [
            talk for talk in self.talks.values() if query.lower() in talk.title.lower()
        ]
        return results, len(results)

    def delete_all(self) -> bool:
        self.talks.clear()
        return True

    def delete(self, talk_id: str) -> bool:
        if talk_id in self.talks:
            del self.talks[talk_id]
            return True
        return False

    def find_by_source(self, source_type: str, source_id: str) -> Talk | None:
        for talk in self.talks.values():
            if talk.source_type == source_type and talk.source_id == source_id:
                return talk
        return None

    def update(self, talk: Talk) -> bool:
        if talk.id in self.talks:
            self.talks[talk.id] = talk
            return True
        return False


class MockWebController:
    """Mock controller for integration testing"""

    def __init__(self, create_talk_use_case: CreateTalkUseCase):
        self.create_talk_use_case = create_talk_use_case

    def create_talk_endpoint(self, http_request_data: dict) -> dict:
        try:
            request_body = http_request_data.get("body", {})

            # Generate ID if not provided
            import uuid

            generated_id = request_body.get("id") or str(uuid.uuid4())

            talk_data = {
                "id": generated_id,  # Required field for CreateTalkUseCase
                "title": request_body.get("title"),
                "description": request_body.get("description"),
                "speaker_names": request_body.get("speakers", []),
                "talk_type": request_body.get("type"),
                "source_type": "web_api",
                "source_id": generated_id,
            }

            talk_id = self.create_talk_use_case.execute(talk_data)

            return {
                "status_code": 201,
                "body": {"message": "Talk created", "talk_id": talk_id},
            }
        except Exception as e:
            return {"status_code": 400, "body": {"error": str(e)}}


class TestFullRequestFlowIntegration:
    """
    Integration Testing Pattern: Full Request Flow

    These tests verify:
    - Complete user journey through all architectural rings
    - Data transformations at each boundary
    - End-to-end workflow correctness
    - Integration between real components

    Test Strategy:
    - Use real implementations for internal components (Ring 1, Ring 2)
    - Use mock implementations for external boundaries (Ring 4)
    - Test complete workflows, not individual components
    """

    def setup_method(self):
        """Set up integration test components"""
        # Ring 4 - Mock infrastructure
        self.repository = MockFullRepository()

        # Ring 1 - Real domain service
        self.domain_service = TalkDomainService()

        # Ring 2 - Real use case
        self.use_case = CreateTalkUseCase(self.repository, self.domain_service)

        # Ring 3 - Mock controller
        self.controller = MockWebController(self.use_case)

    def test_complete_talk_creation_flow(self):
        """Test complete flow from HTTP request to data persistence"""
        # Arrange - Simulate HTTP request
        http_request = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "id": "integration-001",
                "title": "Full Integration Test",
                "description": "Testing complete request flow through all rings",
                "speakers": ["Integration Expert"],
                "type": "workshop",
            },
        }

        # Act - Complete flow through all rings
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - HTTP response
        assert response["status_code"] == 201
        assert "talk_id" in response["body"]
        assert response["body"]["message"] == "Talk created"

        # Assert - Data was persisted
        talk_id = response["body"]["talk_id"]
        persisted_talk = self.repository.find_by_id(talk_id)
        assert persisted_talk is not None
        assert persisted_talk.title == "Full Integration Test"
        assert persisted_talk.speaker_names == ["Integration Expert"]
        assert persisted_talk.talk_type == TalkType.WORKSHOP

        # Assert - Domain logic was applied
        assert "Integration" in persisted_talk.auto_tags  # Auto-tagging applied
        assert persisted_talk.source_type == "web_api"  # Controller added source

    def test_integration_data_transformation_chain(self):
        """Test data transformations through the entire chain"""
        # Arrange - HTTP data with transformations needed at each ring
        http_request = {
            "body": {
                "title": "  Machine Learning Workshop  ",  # Whitespace (Ring 3 → Ring 2)
                "description": "DEEP LEARNING WITH TENSORFLOW",  # Case (Ring 2 → Ring 1)
                "speakers": ["Dr. ML Expert", "Prof. AI"],  # Multiple speakers
                "type": "WORKSHOP",  # Case variation (Ring 3 → Ring 2)
            }
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - Verify transformations at each ring
        talk_id = response["body"]["talk_id"]
        final_talk = self.repository.find_by_id(talk_id)

        # Ring 3 transformations
        assert final_talk.source_type == "web_api"

        # Ring 2 transformations
        assert final_talk.talk_type == TalkType.WORKSHOP

        # Ring 1 transformations (domain service)
        assert "AI/ML" in final_talk.auto_tags
        assert final_talk.title.strip() == final_talk.title  # Cleaned

    def test_integration_error_propagation(self):
        """Test how errors propagate through the architectural layers"""
        # Arrange - Invalid data that should fail domain validation
        http_request = {
            "body": {
                "title": "",  # Invalid - should fail Ring 1 validation
                "description": "Valid description",
                "speakers": [],  # Invalid - should fail Ring 1 validation
                "type": "workshop",
            }
        }

        # Act
        response = self.controller.create_talk_endpoint(http_request)

        # Assert - Error propagated correctly
        assert response["status_code"] == 400
        assert "error" in response["body"]

        # Assert - No data was persisted
        assert len(self.repository.talks) == 0

    def test_integration_multiple_requests(self):
        """Test multiple requests to verify system state management"""
        # Arrange - Multiple different requests
        requests = [
            {
                "body": {
                    "title": "Python Basics",
                    "description": "Introduction to Python",
                    "speakers": ["Python Expert"],
                    "type": "tutorial",
                }
            },
            {
                "body": {
                    "title": "Advanced Django",
                    "description": "Building web applications with Django",
                    "speakers": ["Django Master"],
                    "type": "workshop",
                }
            },
            {
                "body": {
                    "title": "Machine Learning",
                    "description": "ML algorithms and implementation",
                    "speakers": ["ML Scientist"],
                    "type": "conference_talk",
                }
            },
        ]

        # Act - Process multiple requests
        responses = [self.controller.create_talk_endpoint(req) for req in requests]

        # Assert - All requests processed successfully
        assert all(response["status_code"] == 201 for response in responses)
        assert len(self.repository.talks) == 3

        # Assert - Each talk has appropriate auto-tags
        talks = list(self.repository.talks.values())
        python_talk = next(talk for talk in talks if "Python" in talk.title)
        django_talk = next(talk for talk in talks if "Django" in talk.title)
        ml_talk = next(talk for talk in talks if "Machine Learning" in talk.title)

        assert "Web Development" in django_talk.auto_tags
        assert "AI/ML" in ml_talk.auto_tags


class TestArchitectureBoundaryEnforcement:
    """
    Tests to verify Clean Architecture boundary rules are enforced

    These tests ensure:
    - Dependencies only point inward
    - Rings don't have inappropriate dependencies
    - Interface contracts are properly defined
    - Dependency injection works correctly
    """

    def test_ring1_has_no_outward_dependencies(self):
        """Test that Ring 1 (domain) has no dependencies on outer rings"""
        # Ring 1 should be pure business logic with no external dependencies
        domain_service = TalkDomainService()

        # These operations should work without any external dependencies
        tags = domain_service.extract_auto_tags(
            "Machine Learning Workshop", "Deep dive into neural networks"
        )
        assert "AI/ML" in tags

        # Domain service should not know about repositories, HTTP, databases, etc.
        domain_attrs = dir(domain_service)
        problematic_attrs = [
            attr
            for attr in domain_attrs
            if any(
                term in attr.lower()
                for term in ["repository", "database", "http", "api", "client"]
            )
        ]
        assert (
            not problematic_attrs
        ), f"Domain service has external dependencies: {problematic_attrs}"

    def test_ring2_only_depends_on_ring1_and_ring3_interfaces(self):
        """Test that Ring 2 (use cases) only depends on Ring 1 and Ring 3 interfaces"""
        # Mock Ring 3 interface
        mock_repository = Mock(spec=TalkRepository)
        mock_repository.save.return_value = "boundary-test-id"

        # Real Ring 1 dependency
        domain_service = TalkDomainService()

        # Ring 2 should work with interface, not implementation
        use_case = CreateTalkUseCase(mock_repository, domain_service)

        talk_data = {
            "id": "boundary-test-001",
            "title": "Boundary Test",
            "description": "Testing architectural boundaries",
            "speaker_names": ["Boundary Expert"],
            "talk_type": "tutorial",
        }

        # Should work with any repository implementation
        result = use_case.execute(talk_data)
        assert result == "boundary-test-id"

    def test_ring3_defines_interfaces_not_implementations(self):
        """Test that Ring 3 interfaces are abstract, not concrete"""
        # Ring 3 should define contracts, not implementations

        # Repository interface should be abstract
        with pytest.raises(TypeError):
            # Should not be able to instantiate abstract base class
            TalkRepository()

    def test_dependency_injection_works_with_different_implementations(self):
        """Test that dependency injection allows substituting implementations"""
        # Arrange - Two different repository implementations
        repo1 = MockFullRepository()
        repo2 = MockFullRepository()

        domain_service = TalkDomainService()

        # Create use cases with different repository implementations
        use_case1 = CreateTalkUseCase(repo1, domain_service)
        use_case2 = CreateTalkUseCase(repo2, domain_service)

        talk_data = {
            "id": "di-test-001",
            "title": "DI Test",
            "description": "Testing dependency injection",
            "speaker_names": ["DI Expert"],
            "talk_type": "tutorial",
        }

        # Act - Both should work independently
        id1 = use_case1.execute(talk_data)

        # Use different ID for second use case
        talk_data_2 = talk_data.copy()
        talk_data_2["id"] = "di-test-002"
        id2 = use_case2.execute(talk_data_2)

        # Assert - Each use case used its own repository
        assert repo1.find_by_id(id1) is not None
        assert repo1.find_by_id(id2) is None  # Not in repo1

        assert repo2.find_by_id(id2) is not None
        assert repo2.find_by_id(id1) is None  # Not in repo2

    def test_rings_dont_skip_layers(self):
        """Test that rings don't bypass intermediate layers"""
        # Ring 4 (infrastructure) should not directly call Ring 1 (domain)
        # It should go through Ring 2 (use cases) and Ring 3 (interfaces)

        # This is more of a design test - in a real implementation,
        # you'd use static analysis tools to enforce this

        # For demonstration, we verify use case orchestrates correctly
        mock_repository = Mock(spec=TalkRepository)
        mock_repository.save.return_value = "orchestration-test"

        domain_service = TalkDomainService()
        use_case = CreateTalkUseCase(mock_repository, domain_service)

        # Use case should orchestrate Ring 1 and Ring 3, not bypass them
        talk_data = {
            "id": "orchestration-test-001",
            "title": "Orchestration Test",
            "description": "Testing proper orchestration",
            "speaker_names": ["Orchestration Expert"],
            "talk_type": "tutorial",
        }

        result = use_case.execute(talk_data)

        # Verify Ring 1 was used (auto-tagging applied)
        saved_talk = mock_repository.save.call_args[0][0]
        assert len(saved_talk.auto_tags) > 0  # Domain service was used

        # Verify Ring 3 was used (repository called)
        mock_repository.save.assert_called_once()


class TestDependencyWiring:
    """Test complete dependency injection setup"""

    def test_complete_dependency_setup(self):
        """Test that all dependencies can be properly wired together"""
        # This simulates a complete application setup

        # Ring 4 - Infrastructure
        repository = MockFullRepository()

        # Ring 1 - Domain
        domain_service = TalkDomainService()

        # Ring 2 - Use Cases
        create_use_case = CreateTalkUseCase(repository, domain_service)

        # Ring 3 - Controllers
        controller = MockWebController(create_use_case)

        # Test complete wiring
        request = {
            "body": {
                "title": "Complete Wiring Test",
                "description": "Testing full dependency setup",
                "speakers": ["Wiring Expert"],
                "type": "workshop",
            }
        }

        response = controller.create_talk_endpoint(request)

        # Verify complete flow works
        assert response["status_code"] == 201
        assert len(repository.talks) == 1

    def test_dependency_lifecycle_independence(self):
        """Test that components can be created and destroyed independently"""
        # Each component should manage its own lifecycle

        # Create multiple instances
        repo1, repo2 = MockFullRepository(), MockFullRepository()
        domain1, domain2 = TalkDomainService(), TalkDomainService()

        use_case1 = CreateTalkUseCase(repo1, domain1)
        use_case2 = CreateTalkUseCase(repo2, domain2)

        # They should be independent
        assert use_case1 is not use_case2
        assert use_case1.talk_repository is repo1
        assert use_case2.talk_repository is repo2


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/integration/ -v
    pytest.main([__file__, "-v"])
