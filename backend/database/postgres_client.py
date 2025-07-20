# backend/database/postgres_client.py
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Any, Optional, Tuple
import logging
from .models import Base, Talk, Taxonomy, TaxonomyValue, talk_taxonomy_values
from datetime import datetime

logger = logging.getLogger(__name__)


class PostgresClient:
    """Postgres client for talk database operations"""

    def __init__(self, connection_string: str = "postgresql://localhost/talks"):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def init_database(self) -> bool:
        """Initialize database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self._create_search_indexes()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

    def _create_search_indexes(self):
        """Create full-text search indexes"""
        with self.engine.connect() as conn:
            # Create GIN index for full-text search on search_vector
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_talks_search 
                ON talks USING gin(to_tsvector('english', search_vector))
            """
                )
            )

            # Create indexes for common queries
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_talks_type ON talks(talk_type)")
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_talks_created_at ON talks(created_at DESC)"
                )
            )
            conn.commit()

    def is_healthy(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def index_talk(self, talk_data: Dict[str, Any]) -> str:
        """Index a single talk"""
        with self.get_session() as session:
            try:
                # Check if talk already exists
                existing_talk = (
                    session.query(Talk).filter(Talk.id == talk_data["id"]).first()
                )

                if existing_talk:
                    # Update existing talk
                    for key, value in talk_data.items():
                        if key == "type_specific_data":
                            # Merge type-specific data
                            existing_data = existing_talk.type_specific_data or {}
                            existing_data.update(value or {})
                            setattr(existing_talk, key, existing_data)
                        elif hasattr(existing_talk, key):
                            setattr(existing_talk, key, value)

                    existing_talk.updated_at = datetime.utcnow()
                    existing_talk.search_vector = self._build_search_vector(talk_data)
                    talk = existing_talk
                else:
                    # Create new talk
                    talk_data["search_vector"] = self._build_search_vector(talk_data)
                    talk = Talk(**talk_data)
                    session.add(talk)

                session.commit()
                session.refresh(talk)
                return talk.id

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to index talk: {e}")
                raise

    def _build_search_vector(self, talk_data: Dict[str, Any]) -> str:
        """Build search vector from talk data"""
        searchable_fields = [
            talk_data.get("title", ""),
            talk_data.get("description", ""),
            " ".join(talk_data.get("speaker_names", [])),
        ]

        # Add type-specific searchable fields
        type_data = talk_data.get("type_specific_data", {})
        if isinstance(type_data, dict):
            searchable_fields.extend(
                [
                    type_data.get("event_name", ""),
                    type_data.get("venue_name", ""),
                    type_data.get("group_name", ""),
                    " ".join(type_data.get("topics", [])),
                    " ".join(type_data.get("hosts", [])),
                ]
            )

        return " ".join(filter(None, searchable_fields))

    def get_talk(self, talk_id: str) -> Optional[Dict[str, Any]]:
        """Get a single talk by ID"""
        with self.get_session() as session:
            try:
                talk = session.query(Talk).filter(Talk.id == talk_id).first()
                return talk.to_dict() if talk else None
            except SQLAlchemyError as e:
                logger.error(f"Failed to get talk {talk_id}: {e}")
                return None

    def search_talks(
        self,
        query: Optional[str] = None,
        talk_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        events: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search talks with filters"""
        with self.get_session() as session:
            try:
                # Build base query
                query_obj = session.query(Talk)

                # Text search using PostgreSQL full-text search
                if query:
                    query_obj = query_obj.filter(
                        func.to_tsvector("english", Talk.search_vector).match(query)
                    )

                # Filter by talk types
                if talk_types:
                    query_obj = query_obj.filter(Talk.talk_type.in_(talk_types))

                # Filter by auto tags - use JSONB ? operator
                if tags:
                    for tag in tags:
                        # Use ? operator to check if JSON array contains the value
                        query_obj = query_obj.filter(Talk.auto_tags.op("?")(tag))

                # Filter by events (stored in type_specific_data)
                if events:
                    query_obj = query_obj.filter(
                        Talk.type_specific_data["event_name"].astext.in_(events)
                    )

                # Filter by cities (stored in type_specific_data)
                if cities:
                    query_obj = query_obj.filter(
                        Talk.type_specific_data["city"].astext.in_(cities)
                    )

                # Get total count before pagination
                total_count = query_obj.count()

                # Apply pagination and ordering
                talks = (
                    query_obj.order_by(Talk.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                return [talk.to_dict() for talk in talks], total_count

            except SQLAlchemyError as e:
                logger.error(f"Search failed: {e}")
                raise

    def update_talk_tags(self, talk_id: str, taxonomy_value_ids: List[int]) -> bool:
        """Update manual tags (taxonomy values) for a talk"""
        with self.get_session() as session:
            try:
                talk = session.query(Talk).filter(Talk.id == talk_id).first()
                if not talk:
                    return False

                # Get taxonomy values
                taxonomy_values = (
                    session.query(TaxonomyValue)
                    .filter(TaxonomyValue.id.in_(taxonomy_value_ids))
                    .all()
                )

                # Update relationships
                talk.taxonomy_values = taxonomy_values
                talk.updated_at = datetime.utcnow()

                session.commit()
                return True

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to update tags for talk {talk_id}: {e}")
                return False

    def get_all_events(self) -> List[str]:
        """Get list of all event names"""
        with self.get_session() as session:
            try:
                # Query distinct event names from type_specific_data
                result = (
                    session.query(
                        func.distinct(Talk.type_specific_data["event_name"].astext)
                    )
                    .filter(Talk.type_specific_data["event_name"].astext.isnot(None))
                    .all()
                )

                return [row[0] for row in result if row[0]]

            except SQLAlchemyError as e:
                logger.error(f"Failed to get events: {e}")
                return []

    def get_all_tags(self) -> Dict[str, int]:
        """Get all auto tags with their counts"""
        with self.get_session() as session:
            try:
                # This is a complex query in Postgres - we'll use raw SQL
                result = session.execute(
                    text(
                        """
                    SELECT tag, COUNT(*) as count
                    FROM talks,
                         json_array_elements_text(auto_tags) as tag
                    GROUP BY tag
                    ORDER BY count DESC
                """
                    )
                )

                return {row[0]: row[1] for row in result}

            except SQLAlchemyError as e:
                logger.error(f"Failed to get tags: {e}")
                return {}

    def delete_all_talks(self) -> bool:
        """Delete all talks (useful for testing) - handles foreign key constraints"""
        with self.get_session() as session:
            try:
                # First delete all talk-taxonomy relationships
                session.query(talk_taxonomy_values).delete(synchronize_session=False)
                # Then delete all talks
                session.query(Talk).delete()
                session.commit()
                logger.info("Deleted all talks and their taxonomy relationships")
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to delete talks: {e}")
                return False

    def delete_all_taxonomies(self) -> bool:
        """Delete all taxonomies and their values (useful for testing)"""
        with self.get_session() as session:
            try:
                # First delete all talk-taxonomy relationships
                session.query(talk_taxonomy_values).delete(synchronize_session=False)
                # Then delete all taxonomy values
                session.query(TaxonomyValue).delete()
                # Finally delete all taxonomies
                session.query(Taxonomy).delete()
                session.commit()
                logger.info("Deleted all taxonomies, values, and relationships")
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to delete taxonomies: {e}")
                return False

    def get_talk_count(self) -> int:
        """Get total number of talks"""
        with self.get_session() as session:
            try:
                return session.query(Talk).count()
            except SQLAlchemyError as e:
                logger.error(f"Failed to get talk count: {e}")
                return 0

    # Taxonomy management methods

    def create_taxonomy(
        self, name: str, description: str = "", created_by: str = "system"
    ) -> Optional[int]:
        """Create a new taxonomy"""
        with self.get_session() as session:
            try:
                taxonomy = Taxonomy(
                    name=name,
                    description=description,
                    created_by=created_by,
                    is_system=(created_by == "system"),
                )
                session.add(taxonomy)
                session.commit()
                session.refresh(taxonomy)
                return taxonomy.id
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to create taxonomy: {e}")
                return None

    def create_taxonomy_value(
        self, taxonomy_id: int, value: str, description: str = "", color: str = ""
    ) -> Optional[int]:
        """Create a new taxonomy value"""
        with self.get_session() as session:
            try:
                taxonomy_value = TaxonomyValue(
                    taxonomy_id=taxonomy_id,
                    value=value,
                    description=description,
                    color=color,
                )
                session.add(taxonomy_value)
                session.commit()
                session.refresh(taxonomy_value)
                return taxonomy_value.id
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to create taxonomy value: {e}")
                return None

    def get_taxonomies(self) -> List[Dict[str, Any]]:
        """Get all taxonomies with their values"""
        with self.get_session() as session:
            try:
                taxonomies = session.query(Taxonomy).all()
                return [taxonomy.to_dict() for taxonomy in taxonomies]
            except SQLAlchemyError as e:
                logger.error(f"Failed to get taxonomies: {e}")
                return []

    def get_taxonomy_by_id(self, taxonomy_id: int) -> Optional[Dict]:
        """Get taxonomy by ID"""
        with self.get_session() as session:
            try:
                taxonomy = (
                    session.query(Taxonomy).filter(Taxonomy.id == taxonomy_id).first()
                )
                return taxonomy.to_dict() if taxonomy else None
            except SQLAlchemyError as e:
                logger.error(f"Failed to get taxonomy by ID: {e}")
                return None

    def update_taxonomy(self, taxonomy_id: int, **kwargs) -> bool:
        """Update taxonomy"""
        with self.get_session() as session:
            try:
                taxonomy = (
                    session.query(Taxonomy).filter(Taxonomy.id == taxonomy_id).first()
                )
                if not taxonomy:
                    return False

                for key, value in kwargs.items():
                    if value is not None and hasattr(taxonomy, key):
                        setattr(taxonomy, key, value)

                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to update taxonomy: {e}")
                return False

    def delete_taxonomy(self, taxonomy_id: int) -> bool:
        """Delete taxonomy and cascade to values"""
        with self.get_session() as session:
            try:
                taxonomy = (
                    session.query(Taxonomy).filter(Taxonomy.id == taxonomy_id).first()
                )
                if not taxonomy:
                    return False

                session.delete(taxonomy)
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to delete taxonomy: {e}")
                return False

    def update_taxonomy_value(self, value_id: int, **kwargs) -> bool:
        """Update taxonomy value"""
        with self.get_session() as session:
            try:
                taxonomy_value = (
                    session.query(TaxonomyValue)
                    .filter(TaxonomyValue.id == value_id)
                    .first()
                )
                if not taxonomy_value:
                    return False

                for key, value in kwargs.items():
                    if value is not None and hasattr(taxonomy_value, key):
                        setattr(taxonomy_value, key, value)

                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to update taxonomy value: {e}")
                return False

    def delete_taxonomy_value(self, value_id: int) -> bool:
        """Delete taxonomy value"""
        with self.get_session() as session:
            try:
                taxonomy_value = (
                    session.query(TaxonomyValue)
                    .filter(TaxonomyValue.id == value_id)
                    .first()
                )
                if not taxonomy_value:
                    return False

                session.delete(taxonomy_value)
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to delete taxonomy value: {e}")
                return False

    def get_talk_tags_with_taxonomy_info(
        self, talk_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get talk tags with full taxonomy information"""
        with self.get_session() as session:
            try:
                talk = session.query(Talk).filter(Talk.id == talk_id).first()
                if not talk:
                    return None

                result = {
                    "talk_id": talk_id,
                    "auto_tags": talk.auto_tags or [],
                    "manual_tags": {},
                }

                # Group manual tags by taxonomy
                for taxonomy_value in talk.taxonomy_values:
                    taxonomy_name = taxonomy_value.taxonomy.name
                    if taxonomy_name not in result["manual_tags"]:
                        result["manual_tags"][taxonomy_name] = []
                    result["manual_tags"][taxonomy_name].append(taxonomy_value.value)

                return result
            except SQLAlchemyError as e:
                logger.error(f"Failed to get talk tags: {e}")
                return None

    def replace_talk_tags(self, talk_id: str, taxonomy_value_ids: List[int]) -> bool:
        """Replace all manual tags for a talk"""
        with self.get_session() as session:
            try:
                talk = session.query(Talk).filter(Talk.id == talk_id).first()
                if not talk:
                    return False

                # Clear existing tags
                talk.taxonomy_values.clear()

                # Add new tags
                if taxonomy_value_ids:
                    taxonomy_values = (
                        session.query(TaxonomyValue)
                        .filter(TaxonomyValue.id.in_(taxonomy_value_ids))
                        .all()
                    )
                    talk.taxonomy_values.extend(taxonomy_values)

                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to replace talk tags: {e}")
                return False

    def add_tags_to_talk(self, talk_id: str, taxonomy_value_ids: List[int]) -> bool:
        """Add specific tags to a talk"""
        with self.get_session() as session:
            try:
                talk = session.query(Talk).filter(Talk.id == talk_id).first()
                if not talk:
                    return False

                # Get existing tag IDs to avoid duplicates
                existing_ids = {tv.id for tv in talk.taxonomy_values}
                new_ids = [id for id in taxonomy_value_ids if id not in existing_ids]

                if new_ids:
                    taxonomy_values = (
                        session.query(TaxonomyValue)
                        .filter(TaxonomyValue.id.in_(new_ids))
                        .all()
                    )
                    talk.taxonomy_values.extend(taxonomy_values)

                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to add tags to talk: {e}")
                return False

    def remove_tag_from_talk(self, talk_id: str, value_id: int) -> bool:
        """Remove specific tag from talk"""
        with self.get_session() as session:
            try:
                talk = session.query(Talk).filter(Talk.id == talk_id).first()
                if not talk:
                    return False

                # Find and remove the specific tag
                taxonomy_value = (
                    session.query(TaxonomyValue)
                    .filter(TaxonomyValue.id == value_id)
                    .first()
                )
                if taxonomy_value and taxonomy_value in talk.taxonomy_values:
                    talk.taxonomy_values.remove(taxonomy_value)
                    session.commit()
                    return True

                return False
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to remove tag from talk: {e}")
                return False

    def get_tag_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all tags"""
        with self.get_session() as session:
            try:
                # Get taxonomy value usage counts
                from sqlalchemy import func

                usage_stats = (
                    session.query(
                        TaxonomyValue.id,
                        TaxonomyValue.value,
                        Taxonomy.name.label("taxonomy_name"),
                        func.count(talk_taxonomy_values.c.talk_id).label("usage_count"),
                    )
                    .join(Taxonomy, TaxonomyValue.taxonomy_id == Taxonomy.id)
                    .outerjoin(
                        talk_taxonomy_values,
                        TaxonomyValue.id == talk_taxonomy_values.c.taxonomy_value_id,
                    )
                    .group_by(TaxonomyValue.id, TaxonomyValue.value, Taxonomy.name)
                    .all()
                )

                return {
                    "taxonomy_usage": [
                        {
                            "value_id": stat.id,
                            "value": stat.value,
                            "taxonomy_name": stat.taxonomy_name,
                            "usage_count": stat.usage_count,
                        }
                        for stat in usage_stats
                    ]
                }
            except SQLAlchemyError as e:
                logger.error(f"Failed to get tag usage stats: {e}")
                return {"taxonomy_usage": []}

    def get_most_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most used tags across all taxonomies"""
        with self.get_session() as session:
            try:
                from sqlalchemy import func

                popular_tags = (
                    session.query(
                        TaxonomyValue.id,
                        TaxonomyValue.value,
                        Taxonomy.name.label("taxonomy_name"),
                        func.count(talk_taxonomy_values.c.talk_id).label("usage_count"),
                    )
                    .join(Taxonomy, TaxonomyValue.taxonomy_id == Taxonomy.id)
                    .join(
                        talk_taxonomy_values,
                        TaxonomyValue.id == talk_taxonomy_values.c.taxonomy_value_id,
                    )
                    .group_by(TaxonomyValue.id, TaxonomyValue.value, Taxonomy.name)
                    .order_by(func.count(talk_taxonomy_values.c.talk_id).desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "value_id": tag.id,
                        "value": tag.value,
                        "taxonomy_name": tag.taxonomy_name,
                        "usage_count": tag.usage_count,
                    }
                    for tag in popular_tags
                ]
            except SQLAlchemyError as e:
                logger.error(f"Failed to get most popular tags: {e}")
                return []

    # ===== PHASE 2: ENHANCED DATABASE METHODS =====

    def get_taxonomy_value_counts(self, taxonomy_id: int) -> List[Dict[str, Any]]:
        """Get usage counts for values in a specific taxonomy"""
        with self.get_session() as session:
            try:
                from sqlalchemy import func

                value_counts = (
                    session.query(
                        TaxonomyValue.id,
                        TaxonomyValue.value,
                        TaxonomyValue.description,
                        TaxonomyValue.color,
                        func.count(talk_taxonomy_values.c.talk_id).label("usage_count"),
                    )
                    .outerjoin(
                        talk_taxonomy_values,
                        TaxonomyValue.id == talk_taxonomy_values.c.taxonomy_value_id,
                    )
                    .filter(TaxonomyValue.taxonomy_id == taxonomy_id)
                    .group_by(
                        TaxonomyValue.id,
                        TaxonomyValue.value,
                        TaxonomyValue.description,
                        TaxonomyValue.color,
                    )
                    .order_by(func.count(talk_taxonomy_values.c.talk_id).desc())
                    .all()
                )

                return [
                    {
                        "value_id": value.id,
                        "value": value.value,
                        "description": value.description,
                        "color": value.color,
                        "usage_count": value.usage_count,
                    }
                    for value in value_counts
                ]
            except SQLAlchemyError as e:
                logger.error(f"Failed to get taxonomy value counts: {e}")
                return []

    def advanced_search_talks(
        self,
        query: Optional[str] = None,
        talk_types: Optional[List[str]] = None,
        taxonomy_filters: Optional[Dict[str, List[str]]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """Advanced search with taxonomy-based filtering"""
        with self.get_session() as session:
            try:
                from sqlalchemy import and_, or_, func, text

                # Base query
                query_obj = session.query(Talk)

                # Text search
                if query:
                    # Simplified search without speaker_names for now
                    search_filter = or_(
                        Talk.title.ilike(f"%{query}%"),
                        Talk.description.ilike(f"%{query}%"),
                    )
                    query_obj = query_obj.filter(search_filter)

                # Talk type filtering
                if talk_types:
                    query_obj = query_obj.filter(Talk.talk_type.in_(talk_types))

                # Taxonomy-based filtering
                if taxonomy_filters:
                    for taxonomy_name, values in taxonomy_filters.items():
                        if values:  # Only apply filter if values are provided
                            # Subquery for talks that have at least one of the specified values
                            subquery = (
                                session.query(talk_taxonomy_values.c.talk_id)
                                .join(
                                    TaxonomyValue,
                                    TaxonomyValue.id
                                    == talk_taxonomy_values.c.taxonomy_value_id,
                                )
                                .join(
                                    Taxonomy, Taxonomy.id == TaxonomyValue.taxonomy_id
                                )
                                .filter(
                                    and_(
                                        Taxonomy.name == taxonomy_name,
                                        TaxonomyValue.value.in_(values),
                                    )
                                )
                                .distinct()
                            )

                            query_obj = query_obj.filter(Talk.id.in_(subquery))

                # Get total count before pagination
                total_count = query_obj.count()

                # Apply pagination
                talks = query_obj.offset(offset).limit(limit).all()

                # Convert to dictionaries
                return [talk.to_dict() for talk in talks], total_count

            except SQLAlchemyError as e:
                logger.error(f"Failed to perform advanced search: {e}")
                return [], 0

    def upsert_talk(self, talk_data: Dict[str, Any]) -> Optional[str]:
        """Insert or update a talk, returns the talk ID"""
        try:
            with self.SessionLocal() as session:
                # Try to find existing talk by source_id and source_type
                existing_talk = (
                    session.query(Talk)
                    .filter(
                        Talk.source_id == talk_data.get("source_id"),
                        Talk.source_type == talk_data.get("source_type"),
                    )
                    .first()
                )

                if existing_talk:
                    # Update existing talk
                    for key, value in talk_data.items():
                        if key != "id":  # Don't update the primary key
                            setattr(existing_talk, key, value)
                    existing_talk.updated_at = datetime.utcnow()
                    existing_talk.last_synced = datetime.utcnow()
                    session.commit()
                    session.refresh(existing_talk)
                    return existing_talk.id
                else:
                    # Create new talk
                    talk = Talk(**talk_data)
                    talk.last_synced = datetime.utcnow()
                    session.add(talk)
                    session.commit()
                    session.refresh(talk)
                    return talk.id

        except SQLAlchemyError as e:
            logger.error(f"Failed to upsert talk: {e}")
            return None

    def get_talk_by_source(
        self, source_id: str, source_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get a talk by source_id and source_type"""
        try:
            with self.SessionLocal() as session:
                talk = (
                    session.query(Talk)
                    .filter(
                        Talk.source_id == source_id, Talk.source_type == source_type
                    )
                    .first()
                )

                return talk.to_dict() if talk else None

        except SQLAlchemyError as e:
            logger.error(f"Failed to get talk by source: {e}")
            return None

    def get_sync_status(self, source_type: str) -> Optional[Dict[str, Any]]:
        """Get sync status for a specific source type"""
        try:
            with self.SessionLocal() as session:
                from .models import SyncStatus

                sync_status = (
                    session.query(SyncStatus)
                    .filter(SyncStatus.source_type == source_type)
                    .first()
                )

                return sync_status.to_dict() if sync_status else None

        except SQLAlchemyError as e:
            logger.error(f"Failed to get sync status: {e}")
            return None

    def update_sync_status(
        self, source_type: str, success: bool = True, error_message: str = None
    ) -> bool:
        """Update sync status for a source type"""
        try:
            with self.SessionLocal() as session:
                from .models import SyncStatus

                sync_status = (
                    session.query(SyncStatus)
                    .filter(SyncStatus.source_type == source_type)
                    .first()
                )

                if not sync_status:
                    # Create new sync status
                    sync_status = SyncStatus(
                        source_type=source_type, sync_count=0, error_count=0
                    )
                    session.add(sync_status)

                # Update sync info
                sync_status.last_sync_time = datetime.utcnow()
                # Ensure sync_count is not None before incrementing
                if sync_status.sync_count is None:
                    sync_status.sync_count = 0
                sync_status.sync_count += 1

                if success:
                    sync_status.last_successful_sync = datetime.utcnow()
                    sync_status.last_error = None
                else:
                    # Ensure error_count is not None before incrementing
                    if sync_status.error_count is None:
                        sync_status.error_count = 0
                    sync_status.error_count += 1
                    sync_status.last_error = error_message

                session.commit()
                return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to update sync status: {e}")
            return False

    def get_all_sync_statuses(self) -> List[Dict[str, Any]]:
        """Get sync status for all source types"""
        try:
            with self.SessionLocal() as session:
                from .models import SyncStatus

                statuses = session.query(SyncStatus).all()
                return [status.to_dict() for status in statuses]

        except SQLAlchemyError as e:
            logger.error(f"Failed to get all sync statuses: {e}")
            return []

    def get_talks_needing_sync(
        self, source_type: str, since_datetime: Optional[datetime] = None
    ) -> List[str]:
        """Get talk IDs that might need syncing based on last_synced timestamp"""
        try:
            with self.SessionLocal() as session:
                query = session.query(Talk.id).filter(Talk.source_type == source_type)

                if since_datetime:
                    query = query.filter(Talk.last_synced < since_datetime)

                return [row[0] for row in query.all()]

        except SQLAlchemyError as e:
            logger.error(f"Failed to get talks needing sync: {e}")
            return []
