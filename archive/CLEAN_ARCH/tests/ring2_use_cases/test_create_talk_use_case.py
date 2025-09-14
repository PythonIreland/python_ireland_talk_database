#!/usr/bin/env python3
"""
Ring 2 Use Case Tests - Clean Architecture Example
        talk_data = {
            "title":          # Arrange - Invalid data (missing required fields)
        invalid_talk_data = {
            "id": "invalid-test-001",
            "title": "",  # Empty title should fail validation
            "description": "Valid description",
            "speaker_names": [],  # Empty speakers should fail
            "talk_type": "conference_talk"
        }alk_data = {
         talk_data = {
            "tit        talk_data = {
            "title": "Dependency         talk_data_1 = {"title": "Talk 1", "speaker_names": ["Speaker 1"], "talk_type": "tutorial", "id": "stateless-1"}
        talk_data_2 = {"title": "Talk 2", "speaker_names": ["Speaker 2"], "talk_type": "workshop", "id": "stateless-2"}
        talk_data_3 = {"title": "Talk 3", "speaker_names": ["Speaker 3"], "talk_type": "conference_talk", "id": "stateless-3"},
            "description": "Testing DI resilience",
            "speaker_names": ["DI Expert"],
            "talk_type": "tutorial",
            "id": "di-test-001"
        }Unique Talk",
            "description": "A unique talk",
            "speaker_names": ["Speaker"],
            "talk_type": "conference_talk",
            "source_type": "sessionize",
            "source_id": "unique-123",
            "id": "unique-talk-001"
        }   "title": "Valid Talk",
            "description": "Valid description",
            "speaker_names": ["Valid Speaker"],
            "talk_type": "conference_talk",
            "id": "valid-talk-001"
        }ine Learning with TensorFlow",
            "description": "Deep dive into neural networks and deep learning algorithms",
            "speaker_names": ["ML Expert"],
            "talk_type": "conference_talk",
            "id": "ml-tf-001"
        }for CreateTalkUseCase demonstrating proper Ring 2 testing patterns
"""

import pytest
from unittest.mock import Mock, MagicMock
from backend.domain.entities.talk import Talk, TalkType
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.application.use_cases.create_talk import CreateTalkUseCase
from backend.contracts.repositories import TalkRepository


class TestCreateTalkUseCase:
    """
    Ring 2 Testing Pattern: Use Case Orchestration

    These tests focus on:
    - Application workflow coordination
    - Dependency injection patterns
    - Error handling and edge cases
    - Business rule enforcement through use cases

    Test Strategy:
    - Mock Ring 3 interfaces (TalkRepository)
    - Use real Ring 1 dependencies (TalkDomainService)
    - Test the orchestration logic, not implementation details
    """

    def setup_method(self):
        """Set up test dependencies for each test"""
        # Ring 3 dependency - MOCKED (interface boundary)
        self.mock_repository = Mock(spec=TalkRepository)
        # Default behavior: no existing talks found
        self.mock_repository.find_by_source.return_value = None

        # Ring 1 dependency - REAL (internal to application)
        self.domain_service = TalkDomainService()

        # System under test - Ring 2 use case
        self.use_case = CreateTalkUseCase(
            talk_repository=self.mock_repository, domain_service=self.domain_service
        )

    def test_create_talk_success_workflow(self):
        """Test successful talk creation workflow"""
        # Arrange
        self.mock_repository.save.return_value = "generated-talk-id-123"

        talk_data = {
            "id": "workshop-001",
            "title": "Python Clean Web Development",
            "description": "Learn Clean Architecture principles with Python web API examples",
            "speaker_names": ["Architecture Expert"],
            "talk_type": "workshop",
            "source_type": "manual",
            "source_id": "workshop-001",
        }

        # Act
        result = self.use_case.execute(talk_data)

        # Assert - Verify workflow orchestration
        assert result == "generated-talk-id-123"

        # Verify repository was called with properly constructed Talk entity
        self.mock_repository.save.assert_called_once()
        saved_talk = self.mock_repository.save.call_args[0][0]

        assert isinstance(saved_talk, Talk)
        assert saved_talk.title == "Python Clean Web Development"
        assert saved_talk.speaker_names == ["Architecture Expert"]
        assert saved_talk.talk_type == TalkType.WORKSHOP
        assert (
            "Web Development" in saved_talk.auto_tags
        )  # Domain service applied    def test_create_talk_with_auto_tagging(self):
        """Test that use case applies domain service auto-tagging"""
        # Arrange
        self.mock_repository.save.return_value = "tagged-talk-id"

        talk_data = {
            "id": "ml-tf-001",
            "title": "Machine Learning with TensorFlow",
            "description": "Deep dive into neural networks and deep learning algorithms",
            "speaker_names": ["ML Expert"],
            "talk_type": "conference_talk",
        }

        # Act
        self.use_case.execute(talk_data)

        # Assert - Verify domain service was applied
        saved_talk = self.mock_repository.save.call_args[0][0]
        assert "AI/ML" in saved_talk.auto_tags  # Auto-tagging applied

    def test_create_talk_validation_failure(self):
        """Test use case handles validation failures appropriately"""
        # Arrange - Invalid data (missing required fields)
        invalid_talk_data = {
            "title": "",  # Empty title should fail validation
            "description": "Valid description",
            "speaker_names": [],  # Empty speakers should fail
            "talk_type": "conference_talk",
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Title is required"):
            self.use_case.execute(invalid_talk_data)

        # Verify repository was never called
        self.mock_repository.save.assert_not_called()

    def test_create_talk_repository_failure(self):
        """Test use case handles repository failures gracefully"""
        # Arrange
        self.mock_repository.save.side_effect = Exception("Database connection failed")

        talk_data = {
            "id": "valid-talk-001",
            "title": "Valid Talk",
            "description": "Valid description",
            "speaker_names": ["Valid Speaker"],
            "talk_type": "conference_talk",
        }

        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            self.use_case.execute(talk_data)

    def test_create_talk_duplicate_handling(self):
        """Test use case handles potential duplicates"""
        # Arrange
        self.mock_repository.find_by_source.return_value = None  # No existing talk
        self.mock_repository.save.return_value = "new-talk-id"

        talk_data = {
            "id": "unique-talk-001",
            "title": "Unique Talk",
            "description": "A unique talk",
            "speaker_names": ["Speaker"],
            "talk_type": "conference_talk",
            "source_type": "sessionize",
            "source_id": "unique-123",
        }

        # Act
        result = self.use_case.execute(talk_data)

        # Assert
        assert result == "new-talk-id"
        self.mock_repository.find_by_source.assert_called_once_with(
            "sessionize", "unique-123"
        )
        self.mock_repository.save.assert_called_once()

    def test_create_talk_dependency_injection_resilience(self):
        """Test that use case gracefully handles different repository implementations"""
        # Arrange - Different mock repository implementation
        alternative_repository = Mock(spec=TalkRepository)
        alternative_repository.save.return_value = "alternative-id"

        # Create use case with different repository
        alternative_use_case = CreateTalkUseCase(
            talk_repository=alternative_repository, domain_service=self.domain_service
        )

        talk_data = {
            "id": "di-test-001",
            "title": "Dependency Injection Test",
            "description": "Testing DI resilience",
            "speaker_names": ["DI Expert"],
            "talk_type": "tutorial",
        }

        # Act
        result = alternative_use_case.execute(talk_data)

        # Assert - Use case works with any repository implementation
        assert result == "alternative-id"
        alternative_repository.save.assert_called_once()

    def test_create_talk_with_complex_data_transformation(self):
        """Test use case handles complex data transformations correctly"""
        # Arrange
        self.mock_repository.save.return_value = "complex-talk-id"

        # Complex input data requiring transformation
        complex_talk_data = {
            "id": "external-id-123",
            "title": "  Advanced Python Patterns  ",  # Whitespace to trim
            "description": "LEARN ADVANCED PATTERNS",  # Case to normalize
            "speaker_names": ["Dr. Jane Smith", "Prof. John Doe"],  # Multiple speakers
            "talk_type": "WORKSHOP",  # Case variation
            "source_type": "external_api",
            "source_id": "api-123",
            "metadata": {  # Additional metadata to process
                "duration": 180,
                "level": "advanced",
            },
        }

        # Act
        result = self.use_case.execute(complex_talk_data)

        # Assert
        saved_talk = self.mock_repository.save.call_args[0][0]
        assert (
            saved_talk.title == "Advanced Python Patterns"
        )  # Trimmed by implementation
        assert (
            saved_talk.talk_type == TalkType.WORKSHOP
        )  # WORKSHOP correctly normalized to lowercase
        assert len(saved_talk.speaker_names) == 2
        assert isinstance(saved_talk.auto_tags, list)  # Domain service was applied

    def test_create_talk_use_case_is_stateless(self):
        """Test that use case can be safely reused (stateless)"""
        # Arrange
        self.mock_repository.save.side_effect = ["id-1", "id-2", "id-3"]

        talk_data_1 = {
            "id": "stateless-1",
            "title": "Talk 1",
            "speaker_names": ["Speaker 1"],
            "talk_type": "tutorial",
        }
        talk_data_2 = {
            "id": "stateless-2",
            "title": "Talk 2",
            "speaker_names": ["Speaker 2"],
            "talk_type": "workshop",
        }
        talk_data_3 = {
            "id": "stateless-3",
            "title": "Talk 3",
            "speaker_names": ["Speaker 3"],
            "talk_type": "conference_talk",
        }

        # Act - Multiple calls to same use case instance
        result_1 = self.use_case.execute(talk_data_1)
        result_2 = self.use_case.execute(talk_data_2)
        result_3 = self.use_case.execute(talk_data_3)

        # Assert - Each call is independent
        assert result_1 == "id-1"
        assert result_2 == "id-2"
        assert result_3 == "id-3"
        assert self.mock_repository.save.call_count == 3


class TestCreateTalkUseCaseIntegrationPatterns:
    """
    Examples of how Ring 2 tests can include limited integration testing
    while still maintaining fast execution times
    """

    def test_use_case_with_real_domain_service_integration(self):
        """Test use case with real domain service to verify integration"""
        # This test uses real Ring 1 components but mocks Ring 3
        mock_repository = Mock(spec=TalkRepository)
        mock_repository.save.return_value = "integration-test-id"

        # Real domain service
        domain_service = TalkDomainService()
        use_case = CreateTalkUseCase(mock_repository, domain_service)

        # Test data designed to trigger multiple domain service behaviors
        talk_data = {
            "title": "Machine Learning and Web Development Workshop",
            "description": "Learn ML algorithms and build web APIs with Flask and FastAPI for data science applications",
            "speaker_names": ["Full Stack Data Scientist"],
            "talk_type": "workshop",
            "id": "integration-test-001",
        }

        # Execute
        result = use_case.execute(talk_data)

        # Verify integration between use case and domain service
        saved_talk = mock_repository.save.call_args[0][0]

        # Should have multiple tags from domain service
        assert "AI/ML" in saved_talk.auto_tags
        assert "Web Development" in saved_talk.auto_tags
        assert "Data Science" in saved_talk.auto_tags

        # Verify talk is valid according to domain rules
        assert saved_talk.is_valid()
        assert len(saved_talk.speaker_names) > 0
        assert saved_talk.title.strip() == saved_talk.title  # Domain service validation


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/ring2_use_cases/test_create_talk_use_case.py -v
    pytest.main([__file__, "-v"])
