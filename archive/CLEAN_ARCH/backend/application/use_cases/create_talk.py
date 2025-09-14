from typing import Dict, Any
from datetime import datetime
from backend.domain.entities.talk import Talk, TalkType
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.contracts.repositories import TalkRepository


class CreateTalkUseCase:
    """Use case for creating a new talk - Use Cases Layer (Ring 2)"""

    def __init__(
        self, talk_repository: TalkRepository, domain_service: TalkDomainService
    ):
        self.talk_repository = talk_repository
        self.domain_service = domain_service

    def execute(self, talk_data: Dict[str, Any]) -> str:
        """Create a new talk with business validation"""

        # Check for duplicates if source information is provided
        source_type = talk_data.get("source_type")
        source_id = talk_data.get("source_id")
        if source_type and source_id:
            existing_talk = self.talk_repository.find_by_source(source_type, source_id)
            if existing_talk:
                raise ValueError(
                    f"Talk already exists with source {source_type}:{source_id}"
                )

        # Validate using domain service
        errors = self.domain_service.validate_talk_data(talk_data)
        if errors:
            raise ValueError(f"Invalid talk data: {', '.join(errors)}")

        # Determine talk type from provided data or source data
        if "talk_type" in talk_data and talk_data["talk_type"]:
            # Use provided talk type if available
            talk_type_str = talk_data["talk_type"]
        else:
            # Determine from source data
            talk_type_str = self.domain_service.determine_talk_type(
                talk_data.get("source_type", ""), talk_data
            )

        # Validate that talk_type is a valid enum value
        try:
            # Normalize to lowercase for enum matching
            talk_type = TalkType(talk_type_str.lower())
        except ValueError:
            # If invalid, default to conference_talk
            talk_type = TalkType.CONFERENCE_TALK

        # Create domain entity
        talk = Talk(
            id=talk_data["id"],
            title=talk_data["title"].strip(),  # Clean whitespace
            description=talk_data.get("description", ""),
            talk_type=talk_type,
            speaker_names=self.domain_service.normalize_speaker_names(
                talk_data.get("speaker_names", [])
            ),
            auto_tags=[],  # Will be populated below
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source_id=talk_data.get("source_id"),
            source_type=talk_data.get("source_type"),
            type_specific_data=talk_data.get("type_specific_data", {}),
        )

        # Apply business rules
        if not talk.is_valid():
            raise ValueError("Talk does not meet business requirements")

        # Enhance with auto-tags using domain service
        auto_tags = self.domain_service.extract_auto_tags(talk.title, talk.description)
        talk.auto_tags = auto_tags

        # Persist through repository
        return self.talk_repository.save(talk)
