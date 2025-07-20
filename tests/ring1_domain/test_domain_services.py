# tests/test_ring1.py
"""
Tests for Ring 1: Pure Python business logic
These tests should be fast and not require any database or external dependencies.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime
from lib.engine.data_pipeline import DataPipeline
from backend.domain.services.talk_domain_service import TalkDomainService


class TestDataPipeline:
    """Test the pure Python business logic in DataPipeline"""

    def test_extract_auto_tags_ai_ml(self):
        """Test auto tag extraction for AI/ML content"""
        # Test domain service directly since business logic moved there
        tags = TalkDomainService.extract_auto_tags(
            "Introduction to Machine Learning",
            "Learn about neural networks and deep learning",
        )
        assert "AI/ML" in tags

    def test_extract_auto_tags_web_dev(self):
        """Test auto tag extraction for web development"""
        tags = TalkDomainService.extract_auto_tags(
            "Building APIs with FastAPI",
            "Learn how to create REST APIs using FastAPI framework",
        )
        assert "Web Development" in tags

    def test_extract_auto_tags_data_science(self):
        """Test auto tag extraction for data science"""
        tags = TalkDomainService.extract_auto_tags(
            "Data Analysis with Pandas",
            "Explore data visualization and analysis techniques",
        )
        assert "Data Science" in tags

    def test_extract_auto_tags_testing(self):
        """Test auto tag extraction for testing"""
        tags = TalkDomainService.extract_auto_tags(
            "Test-Driven Development", "Learn pytest and unittest frameworks"
        )
        assert "Testing" in tags

    def test_extract_auto_tags_multiple(self):
        """Test auto tag extraction for content with multiple tags"""
        tags = TalkDomainService.extract_auto_tags(
            "Testing Django Applications",
            "Learn how to test your Django web applications using pytest",
        )
        assert "Web Development" in tags
        assert "Testing" in tags

    def test_extract_auto_tags_none(self):
        """Test auto tag extraction for content without recognizable keywords"""
        tags = TalkDomainService.extract_auto_tags(
            "Python Basics", "Introduction to Python programming"
        )
        # Should return empty list or only generic tags
        assert isinstance(tags, list)

    def test_process_sessionize_talk_structure(self):
        """Test the structure of processed Sessionize talk data"""
        pipeline = DataPipeline()

        # Mock a Sessionize talk
        mock_speaker = Mock()
        mock_speaker.name = "John Doe"
        mock_speaker.bio = "Python developer"
        mock_speaker.tagline = "Code enthusiast"
        mock_speaker.photo_url = "http://example.com/photo.jpg"

        mock_talk = Mock()
        mock_talk.id = "123"
        mock_talk.title = "Test Talk"
        mock_talk.description = "A test talk about Python"
        mock_talk.speakers = [mock_speaker]
        mock_talk.event_id = "event123"
        mock_talk.event_name = "PyCon Test"
        mock_talk.room = "Room A"
        mock_talk.start_time = "2023-10-01T10:00:00"
        mock_talk.end_time = "2023-10-01T11:00:00"

        processed = pipeline._process_sessionize_talk(mock_talk)

        # Check structure
        assert processed["id"] == "pycon_123"
        assert processed["talk_type"] == "pycon"
        assert processed["title"] == "Test Talk"
        assert processed["speaker_names"] == ["John Doe"]
        assert processed["event_name"] == "PyCon Test"
        assert isinstance(processed["auto_tags"], list)
        assert "created_at" in processed
        assert "updated_at" in processed

    def test_process_meetup_event_structure(self):
        """Test the structure of processed Meetup event data"""
        pipeline = DataPipeline()

        # Mock a Meetup event
        mock_host = Mock()
        mock_host.name = "Jane Smith"

        mock_venue = Mock()
        mock_venue.name = "Tech Hub"
        mock_venue.address = "123 Tech Street"
        mock_venue.city = "Dublin"

        mock_event = Mock()
        mock_event.id = "456"
        mock_event.title = "Python Meetup"
        mock_event.description = "Monthly Python meetup"
        mock_event.hosts = [mock_host]
        mock_event.event_url = "http://meetup.com/event/456"
        mock_event.venue = mock_venue
        mock_event.going_count = 25
        mock_event.start_time = "2023-10-15T19:00:00"
        mock_event.topics = ["Python", "Programming"]
        mock_event.group_name = "Python Ireland"

        processed = pipeline._process_meetup_event(mock_event)

        # Check structure
        assert processed["id"] == "meetup_456"
        assert processed["talk_type"] == "meetup"
        assert processed["title"] == "Python Meetup"
        assert processed["speaker_names"] == ["Jane Smith"]
        assert processed["city"] == "Dublin"
        assert processed["going_count"] == 25
        assert isinstance(processed["auto_tags"], list)
        assert "created_at" in processed
