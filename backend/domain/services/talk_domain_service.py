from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TalkDomainService:
    """Pure business logic for talks - Entities Layer (Ring 1)

    This service contains business rules that don't belong to any specific entity
    but are core to the talk domain. It's framework-independent and testable.
    """

    @staticmethod
    def extract_auto_tags(title: str, description: str) -> List[str]:
        """Business rule: extract auto tags from talk content

        Args:
            title: Talk title
            description: Talk description

        Returns:
            List of automatically generated tags based on content analysis
        """
        if not title and not description:
            return []

        text = f"{title} {description}".lower()
        keywords = []

        # AI/ML Keywords
        ai_keywords = [
            "ai",
            "machine learning",
            "neural",
            "deep learning",
            "llm",
            "gpt",
            "artificial intelligence",
            "ml",
        ]
        if any(keyword in text for keyword in ai_keywords):
            keywords.append("AI/ML")

        # Web Development Keywords
        web_keywords = [
            "django",
            "flask",
            "fastapi",
            "web",
            "http",
            "api",
            "rest",
            "frontend",
            "backend",
            "react",
            "vue",
        ]
        if any(keyword in text for keyword in web_keywords):
            keywords.append("Web Development")

        # Data Science Keywords
        data_keywords = [
            "pandas",
            "numpy",
            "data",
            "analysis",
            "visualization",
            "jupyter",
            "matplotlib",
            "seaborn",
            "plotly",
            "analytics",
        ]
        if any(keyword in text for keyword in data_keywords):
            keywords.append("Data Science")

        # Testing Keywords
        test_keywords = [
            "test",
            "pytest",
            "unittest",
            "tdd",
            "testing",
            "quality assurance",
            "qa",
            "automation",
        ]
        if any(keyword in text for keyword in test_keywords):
            keywords.append("Testing")

        # DevOps Keywords
        devops_keywords = [
            "docker",
            "kubernetes",
            "ci/cd",
            "deployment",
            "infrastructure",
            "cloud",
            "aws",
            "azure",
        ]
        if any(keyword in text for keyword in devops_keywords):
            keywords.append("DevOps")

        # Security Keywords
        security_keywords = [
            "security",
            "authentication",
            "authorization",
            "encryption",
            "vulnerability",
            "penetration testing",
            "cybersecurity",
        ]
        if any(keyword in text for keyword in security_keywords):
            keywords.append("Security")

        return keywords

    @staticmethod
    def determine_talk_type(source_type: str, session_data: Dict[str, Any]) -> str:
        """Business rule: determine talk type from source and session data

        Args:
            source_type: Source of the talk (e.g., 'sessionize', 'meetup')
            session_data: Raw session data from the source

        Returns:
            Standardized talk type
        """
        if source_type == "meetup":
            # Meetup events are typically meetup talks
            return "meetup"
        elif source_type == "sessionize":
            # Sessionize talks are typically conference talks
            session_format = session_data.get("format", "").lower()

            if "lightning" in session_format:
                return "lightning_talk"
            elif "workshop" in session_format:
                return "workshop"
            elif "keynote" in session_format:
                return "keynote"
            else:
                return "conference_talk"
        else:
            # Default for unknown sources
            return "talk"

    @staticmethod
    def validate_talk_data(talk_data: Dict[str, Any]) -> List[str]:
        """Business rule: validate talk data according to domain rules

        Args:
            talk_data: Talk data to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Title validation
        title = talk_data.get("title", "").strip()
        if not title:
            errors.append("Title is required")
        elif len(title) > 500:
            errors.append("Title cannot exceed 500 characters")

        # Speaker validation
        speaker_names = talk_data.get("speaker_names", [])
        if not speaker_names:
            errors.append("At least one speaker is required")
        elif any(not name.strip() for name in speaker_names):
            errors.append("Speaker names cannot be empty")

        # Description validation
        description = talk_data.get("description", "").strip()
        if description and len(description) > 10000:
            errors.append("Description cannot exceed 10,000 characters")

        # Source validation
        source_id = talk_data.get("source_id")
        source_type = talk_data.get("source_type")
        if source_id and not source_type:
            errors.append("Source type is required when source ID is provided")
        elif source_type and not source_id:
            errors.append("Source ID is required when source type is provided")

        return errors

    @staticmethod
    def should_update_talk(
        existing_talk: Dict[str, Any], new_talk_data: Dict[str, Any]
    ) -> bool:
        """Business rule: determine if an existing talk should be updated

        This implements the business logic for when a talk needs updating based on:
        - Content changes (title, description, speakers)
        - Time-based rules (periodic refresh)
        - Source-specific rules

        Args:
            existing_talk: Current talk data
            new_talk_data: New talk data from source

        Returns:
            True if talk should be updated, False otherwise
        """
        # Check for content changes
        content_fields = ["title", "description", "speaker_names"]
        for field in content_fields:
            if existing_talk.get(field) != new_talk_data.get(field):
                logger.info(f"Talk content changed in field: {field}")
                return True

        # Check for auto-tag changes (content analysis might improve over time)
        existing_tags = set(existing_talk.get("auto_tags", []))
        new_tags = set(new_talk_data.get("auto_tags", []))
        if existing_tags != new_tags:
            logger.info("Talk auto-tags changed")
            return True

        # Time-based update rule: refresh every 24 hours
        last_synced = existing_talk.get("last_synced") or existing_talk.get(
            "updated_at"
        )
        if last_synced:
            try:
                # Handle both ISO format and timezone-aware strings
                if isinstance(last_synced, str):
                    # Remove timezone info for simple comparison
                    last_synced_clean = last_synced.replace("Z", "").replace(
                        "+00:00", ""
                    )
                    last_synced_dt = datetime.fromisoformat(last_synced_clean)
                else:
                    last_synced_dt = last_synced

                if datetime.utcnow() - last_synced_dt > timedelta(hours=24):
                    logger.info("Talk due for periodic refresh (24+ hours)")
                    return True
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse last_synced date: {e}, forcing update")
                return True

        # Source-specific rules
        source_type = new_talk_data.get("source_type")
        if source_type == "meetup":
            # Meetup events might have attendance updates
            existing_going = existing_talk.get("type_specific_data", {}).get(
                "going_count", 0
            )
            new_going = new_talk_data.get("type_specific_data", {}).get(
                "going_count", 0
            )
            if existing_going != new_going:
                logger.info("Meetup attendance count changed")
                return True

        return False

    @staticmethod
    def normalize_speaker_names(speaker_names: List[str]) -> List[str]:
        """Business rule: normalize speaker names for consistency

        Args:
            speaker_names: Raw speaker names

        Returns:
            Normalized speaker names
        """
        if not speaker_names:
            return []

        normalized = []
        for name in speaker_names:
            if not name or not name.strip():
                continue

            # Basic normalization
            clean_name = name.strip()

            # Remove common prefixes/suffixes that might cause duplicates
            prefixes_to_remove = ["Dr.", "Prof.", "Mr.", "Ms.", "Mrs."]
            for prefix in prefixes_to_remove:
                if clean_name.startswith(prefix + " "):
                    clean_name = clean_name[len(prefix) :].strip()

            if clean_name and clean_name not in normalized:
                normalized.append(clean_name)

        return normalized

    @staticmethod
    def generate_talk_id(source_type: str, source_id: str) -> str:
        """Business rule: generate consistent talk IDs

        Args:
            source_type: Type of source (e.g., 'meetup', 'sessionize')
            source_id: ID from the source system

        Returns:
            Standardized talk ID
        """
        if not source_type or not source_id:
            raise ValueError("Both source_type and source_id are required")

        # Normalize source type
        source_type_normalized = source_type.lower().strip()

        # Generate consistent ID
        return f"{source_type_normalized}_{source_id}"

    @staticmethod
    def is_valid_talk_type(talk_type: str) -> bool:
        """Business rule: validate talk type

        Args:
            talk_type: Talk type to validate

        Returns:
            True if valid talk type
        """
        valid_types = {
            "conference_talk",
            "lightning_talk",
            "workshop",
            "keynote",
            "meetup",
            "talk",
            "presentation",
        }
        return talk_type in valid_types
