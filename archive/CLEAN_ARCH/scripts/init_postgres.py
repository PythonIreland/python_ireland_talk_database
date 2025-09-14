#!/usr/bin/env python3
"""
Database initialization and migration script
"""
import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath("."))

from backend.services.talk_service import TalkService
from backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database and run a basic migration test"""

    print(f"🚀 Initializing Python Ireland Talk Database")
    print(f"📊 Database URL: {settings.database_url}")

    # Create service
    talk_service = TalkService()

    # Check health
    print("🔍 Checking database health...")
    if not talk_service.is_healthy():
        print("❌ Database connection failed!")
        print("💡 Make sure PostgreSQL is running and the database exists")
        print("   Example setup commands:")
        print("   createdb talks_db")
        print("   # or adjust DATABASE_URL environment variable")
        return 1

    print("✅ Database connection successful!")

    # Initialize database
    print("🔧 Initializing database tables...")
    if not talk_service.init_database():
        print("❌ Database initialization failed!")
        return 1

    print("✅ Database tables created!")

    # Initialize default taxonomies
    print("🏷️  Creating default taxonomies...")
    talk_service.initialize_default_taxonomies()
    print("✅ Default taxonomies created!")

    # Test basic operations
    print("🧪 Testing basic operations...")

    # Create a test talk
    test_talk = {
        "id": "test_migration_talk",
        "talk_type": "pycon",
        "title": "Test Migration Talk",
        "description": "A test talk to verify the migration worked",
        "speaker_names": ["Migration Tester"],
        "auto_tags": ["Testing", "Migration"],
        "type_specific_data": {
            "event_name": "Migration Test Event",
            "room": "Virtual Room",
        },
    }

    talk_id = talk_service.create_talk(test_talk)
    print(f"✅ Created test talk: {talk_id}")

    # Retrieve the talk
    retrieved = talk_service.get_talk(talk_id)
    if retrieved and retrieved["title"] == test_talk["title"]:
        print("✅ Talk retrieval successful!")
    else:
        print("❌ Talk retrieval failed!")
        return 1

    # Test search
    results, total = talk_service.search_talks(query="migration")
    if total > 0:
        print(f"✅ Search successful! Found {total} talks")
    else:
        print("❌ Search failed!")
        return 1

    # Get talk count
    count = talk_service.get_talk_count()
    print(f"📊 Total talks in database: {count}")

    # Test taxonomies
    taxonomies = talk_service.get_taxonomies()
    print(f"🏷️  Available taxonomies: {len(taxonomies)}")
    for taxonomy in taxonomies:
        print(f"   - {taxonomy['name']}: {len(taxonomy['values'])} values")

    print("\n🎉 Migration to Postgres completed successfully!")
    print("💡 You can now:")
    print("   1. Start the backend: python backend/main.py")
    print("   2. Run data ingestion: POST /api/v1/talks/ingest")
    print("   3. Test the API endpoints")

    return 0


if __name__ == "__main__":
    sys.exit(main())
