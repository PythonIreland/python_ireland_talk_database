# backend/database/postgres_client.py
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Any, Optional, Tuple
import logging
from .models import Base, Talk, Taxonomy, TaxonomyValue
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

                # Filter by auto tags
                if tags:
                    for tag in tags:
                        query_obj = query_obj.filter(
                            func.json_array_elements_text(Talk.auto_tags).op("=")(tag)
                        )

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
        """Delete all talks (useful for testing)"""
        with self.get_session() as session:
            try:
                session.query(Talk).delete()
                session.commit()
                logger.info("Deleted all talks")
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to delete talks: {e}")
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
