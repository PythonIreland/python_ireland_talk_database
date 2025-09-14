from typing import Optional
from backend.domain.entities.talk import Talk
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.contracts.repositories import TalkRepository


class UpdateTalkUseCase:
    """Use case for updating existing talks"""

    def __init__(self, talk_repository: TalkRepository):
        self.talk_repository = talk_repository

    def execute(self, talk_id: str, updates: dict) -> Talk:
        """Update talk with new data"""
        # Get existing talk
        existing_talk = self.talk_repository.find_by_id(talk_id)
        if not existing_talk:
            raise ValueError(f"Talk with ID {talk_id} not found")

        # Create updated talk data
        talk_data = existing_talk.to_dict()
        talk_data.update(updates)

        # Validate updated data using domain service
        validation_result = TalkDomainService.validate_talk_data(talk_data)
        if not validation_result.is_valid:
            raise ValueError(
                f"Invalid talk data: {', '.join(validation_result.errors)}"
            )

        # Create updated talk
        updated_talk = Talk.from_dict(talk_data)

        # Apply domain rules for updates
        if TalkDomainService.should_update_talk(existing_talk.to_dict(), talk_data):
            self.talk_repository.update(updated_talk)
            return updated_talk
        else:
            return existing_talk
