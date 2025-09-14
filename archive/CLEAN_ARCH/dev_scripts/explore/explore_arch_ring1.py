#!/usr/bin/env python3
"""
Ring 1 Architecture Exploration: Domain Entities & Services
Pure business logic with no external dependencies
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path so we can import our modules
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("🎯 Ring 1: Enterprise Business Rules")
print("=" * 50)
print("Exploring pure business logic and domain entities...")
print(f"Backend path: {backend_path}")
print()

# Import Ring 1 components - Domain Entities
from domain.entities.talk import Talk, TalkType
from domain.entities.taxonomy import Taxonomy, TaxonomyValue
from domain.services.talk_domain_service import TalkDomainService

print("✅ Successfully imported Ring 1 components:")
print("  - Talk (domain entity)")
print("  - Taxonomy, TaxonomyValue (domain entities)")
print("  - TalkDomainService (pure business logic)")
print()

# Let's examine what these domain entities can do
print("📋 Talk entity capabilities:")
talk_methods = [method for method in dir(Talk) if not method.startswith("_")]
for method in sorted(talk_methods):
    print(f"  - {method}")
print()

# Check docstring
print("📖 Talk docstring:")
print(f"   {Talk.__doc__}")
print()

# Show available TalkType options
print("🏷️  Available TalkType options:")
for talk_type in TalkType:
    print(f"   • TalkType.{talk_type.name} = '{talk_type.value}'")
print()


def explore_talk_entity():
    """Explore Talk entity creation and business methods"""
    print("🔍 Creating a sample Talk entity...")

    # Create a talk with some sample data
    sample_talk_data = {
        "id": "sample-123",
        "title": "Building Clean Architecture with Python",
        "description": "Learn how to implement Clean Architecture principles in Python applications, including dependency inversion, separation of concerns, and testability.",
        "speaker_names": ["Alice Developer", "Bob Architect"],
        "talk_type": TalkType.CONFERENCE_TALK,  # Use the enum directly
        "source_type": "sessionize",
        "source_id": "sample-123",
    }

    # Create the Talk entity
    talk = Talk(**sample_talk_data)

    print(f"✅ Created talk: {talk.title}")
    print(f"👥 Speakers: {', '.join(talk.speaker_names)}")
    print(f"🏷️  Type: {talk.talk_type}")
    print()

    return talk


def explore_talk_business_methods(talk):
    """Test the business methods of the Talk entity"""
    print("🧪 Testing Talk entity business methods...")
    print()

    # Test validation
    print("1. Business Validation:")
    is_valid = talk.is_valid()
    print(f"   ✅ Is talk valid? {is_valid}")
    print()

    # Test keyword search
    print("2. Keyword Search (business rule):")
    has_python = talk.has_keyword("Python")
    has_architecture = talk.has_keyword("Architecture")
    has_irrelevant = talk.has_keyword("Cooking")
    print(f"   🔍 Contains 'Python': {has_python}")
    print(f"   🔍 Contains 'Architecture': {has_architecture}")
    print(f"   🔍 Contains 'Cooking': {has_irrelevant}")
    print()

    # Test speaker check
    print("3. Speaker Business Rules:")
    is_by_alice = talk.is_by_speaker("Alice Developer")
    is_by_charlie = talk.is_by_speaker("Charlie Unknown")
    print(f"   👤 Is by Alice Developer: {is_by_alice}")
    print(f"   👤 Is by Charlie Unknown: {is_by_charlie}")
    print()


def explore_domain_service():
    """Explore TalkDomainService - Pure Business Logic (Ring 1)"""
    print("⚙️ TalkDomainService - Pure Business Logic")
    print("=" * 50)

    # Test auto-tagging business rules
    print("1. Auto-tagging Business Rules:")
    title = "Building RESTful APIs with FastAPI and PostgreSQL"
    description = "Learn how to create scalable web APIs using FastAPI, implement database operations with SQLAlchemy, and write comprehensive tests for your application."

    auto_tags = TalkDomainService.extract_auto_tags(title, description)
    print(f"   📝 Title: {title}")
    print(f"   📄 Description: {description[:100]}...")
    print(f"   🏷️  Auto-generated tags: {auto_tags}")
    print()

    # Test talk type determination
    print("2. Talk Type Business Rules:")
    session_data_examples = [
        {"session_type": "Conference Session", "duration": 45},
        {"session_type": "Lightning Talk", "duration": 5},
        {"session_type": "Workshop", "duration": 180},
    ]

    for session_data in session_data_examples:
        talk_type = TalkDomainService.determine_talk_type("sessionize", session_data)
        print(f"   📊 {session_data} → Talk Type: {talk_type}")
    print()


def explore_validation_and_normalization():
    """Test more TalkDomainService business rules"""
    print("3. Data Validation Business Rules:")

    # Test with valid talk data
    valid_talk_data = {
        "title": "Introduction to Machine Learning",
        "description": "A comprehensive overview of ML concepts",
        "speaker_names": ["Dr. Sarah Chen"],  # Fixed field name
        "talk_type": "conference_talk",
    }

    validation_errors = TalkDomainService.validate_talk_data(valid_talk_data)
    print(f"   ✅ Valid data errors: {validation_errors}")

    # Test with invalid talk data
    invalid_talk_data = {
        "title": "",  # Empty title
        "description": "A",  # Too short description
        "speaker_names": [],  # No speakers
        "talk_type": "",  # Empty talk type
    }

    validation_errors = TalkDomainService.validate_talk_data(invalid_talk_data)
    print(f"   ❌ Invalid data errors: {validation_errors}")
    print()

    print("4. Speaker Name Normalization:")
    messy_names = ["  alice DEVELOPER  ", "Bob-Architect", "charlie_coder@email.com"]
    normalized = TalkDomainService.normalize_speaker_names(messy_names)
    print(f"   📝 Original: {messy_names}")
    print(f"   ✨ Normalized: {normalized}")
    print()


def main():
    """Main exploration function"""
    try:
        # Explore Talk entity
        talk = explore_talk_entity()

        # Test business methods
        explore_talk_business_methods(talk)

        # Explore domain service
        explore_domain_service()

        # Test validation and normalization
        explore_validation_and_normalization()

        print("🎯 Ring 1 Summary:")
        print("  ✅ Pure business logic - no external dependencies")
        print("  ✅ Rich domain entities with behavior")
        print("  ✅ Domain services for complex business rules")
        print("  ✅ Framework-agnostic and testable")

    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
