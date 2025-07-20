#!/usr/bin/env python3
"""
Database migration script to add sync tracking fields
"""
import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.abspath("."))

from backend.services.talk_service import TalkService
from backend.core.config import settings
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Add sync tracking fields to existing database"""

    print(f"🔄 Migrating Python Ireland Talk Database")
    print(f"📊 Database URL: {settings.database_url}")

    # Create service
    talk_service = TalkService()

    # Check health
    print("🔍 Checking database health...")
    if not talk_service.is_healthy():
        print("❌ Database connection failed!")
        return 1

    print("✅ Database connection successful!")

    # Run migration
    print("🔧 Adding sync tracking fields...")
    
    try:
        # Get database engine
        engine = talk_service.db.engine
        
        with engine.connect() as conn:
            # Add new columns to talks table
            print("   Adding source_id column...")
            try:
                conn.execute(text("ALTER TABLE talks ADD COLUMN source_id VARCHAR"))
            except Exception as e:
                if "already exists" in str(e):
                    print("   ✓ source_id column already exists")
                else:
                    raise e
            
            print("   Adding source_type column...")
            try:
                conn.execute(text("ALTER TABLE talks ADD COLUMN source_type VARCHAR"))
            except Exception as e:
                if "already exists" in str(e):
                    print("   ✓ source_type column already exists")
                else:
                    raise e
            
            print("   Adding last_synced column...")
            try:
                conn.execute(text("ALTER TABLE talks ADD COLUMN last_synced TIMESTAMP"))
            except Exception as e:
                if "already exists" in str(e):
                    print("   ✓ last_synced column already exists")
                else:
                    raise e
            
            print("   Adding source_updated_at column...")
            try:
                conn.execute(text("ALTER TABLE talks ADD COLUMN source_updated_at TIMESTAMP"))
            except Exception as e:
                if "already exists" in str(e):
                    print("   ✓ source_updated_at column already exists")
                else:
                    raise e
            
            # Create sync_status table
            print("   Creating sync_status table...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sync_status (
                        id SERIAL PRIMARY KEY,
                        source_type VARCHAR UNIQUE NOT NULL,
                        last_sync_time TIMESTAMP,
                        last_successful_sync TIMESTAMP,
                        sync_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        last_error TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                print("   ✓ sync_status table created")
            except Exception as e:
                print(f"   ⚠️  sync_status table creation: {e}")
            
            # Add indexes for performance
            print("   Adding performance indexes...")
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_talks_source ON talks(source_id, source_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_talks_sync ON talks(last_synced)"))
                print("   ✓ Indexes created")
            except Exception as e:
                print(f"   ⚠️  Index creation: {e}")
            
            # Commit changes
            conn.commit()
        
        # Populate sync tracking fields for existing data
        print("🔄 Populating sync fields for existing talks...")
        
        with engine.connect() as conn:
            # Update existing meetup talks
            result = conn.execute(text("""
                UPDATE talks 
                SET source_id = SUBSTRING(id FROM 'meetup_(.*)'),
                    source_type = 'meetup',
                    last_synced = created_at
                WHERE id LIKE 'meetup_%' AND source_id IS NULL
            """))
            print(f"   ✓ Updated {result.rowcount} meetup talks")
            
            # Update existing pycon talks  
            result = conn.execute(text("""
                UPDATE talks 
                SET source_id = SUBSTRING(id FROM 'pycon_(.*)'),
                    source_type = 'sessionize', 
                    last_synced = created_at
                WHERE id LIKE 'pycon_%' AND source_id IS NULL
            """))
            print(f"   ✓ Updated {result.rowcount} pycon talks")
            
            # Update test migration talk
            result = conn.execute(text("""
                UPDATE talks 
                SET source_id = 'test_migration_talk',
                    source_type = 'manual',
                    last_synced = created_at  
                WHERE id = 'test_migration_talk' AND source_id IS NULL
            """))
            print(f"   ✓ Updated {result.rowcount} test talks")
            
            conn.commit()

        print("✅ Migration completed successfully!")
        
        # Show summary
        print("\n📊 Migration Summary:")
        print("   ✓ Added source_id column")
        print("   ✓ Added source_type column") 
        print("   ✓ Added last_synced column")
        print("   ✓ Added source_updated_at column")
        print("   ✓ Created sync_status table")
        print("   ✓ Added performance indexes")
        print("   ✓ Populated existing data")
        
        # Get counts
        count = talk_service.get_talk_count()
        print(f"\n📈 Total talks in database: {count}")
        
        print("\n🎉 Database migration completed successfully!")
        print("💡 You can now use the new sync endpoints:")
        print("   - POST /api/v1/talks/sync (incremental sync)")
        print("   - GET /api/v1/talks/sync/status (sync status)")
        print("   - POST /api/v1/talks/ingest (full reload)")

        return 0

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logger.exception("Migration failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
