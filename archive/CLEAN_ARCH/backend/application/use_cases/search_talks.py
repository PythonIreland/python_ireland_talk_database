from typing import List, Tuple, Dict, Any
from backend.domain.entities.talk import Talk
from backend.contracts.repositories import TalkRepository


class SearchTalksUseCase:
    """Use case for searching talks"""

    def __init__(self, talk_repository: TalkRepository):
        self.talk_repository = talk_repository

    def execute(
        self, query: str = "", filters: Dict[str, Any] = None
    ) -> Tuple[List[Talk], int]:
        """Search talks with optional filters"""
        if filters is None:
            filters = {}

        # Apply business rules for search
        processed_filters = self._process_search_filters(filters)

        return self.talk_repository.search(query, processed_filters)

    def _process_search_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply business rules to search filters"""
        processed = filters.copy()

        # Normalize speaker names if present
        if "speaker" in processed:
            processed["speaker"] = processed["speaker"].strip().title()

        # Validate year ranges
        if "year_from" in processed and "year_to" in processed:
            if processed["year_from"] > processed["year_to"]:
                raise ValueError("Start year cannot be greater than end year")

        return processed
