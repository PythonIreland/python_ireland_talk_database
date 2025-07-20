from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from backend.domain.entities.talk import Talk
from backend.domain.entities.taxonomy import Taxonomy


class TalkRepository(ABC):
    """Repository interface for talks - Interface defined in Use Cases Layer (Ring 2), implemented in Interface Adapters Layer (Ring 3)"""

    @abstractmethod
    def save(self, talk: Talk) -> str:
        """Save talk and return ID"""
        pass

    @abstractmethod
    def find_by_id(self, talk_id: str) -> Optional[Talk]:
        """Find talk by ID"""
        pass

    @abstractmethod
    def find_by_source(self, source_id: str, source_type: str) -> Optional[Talk]:
        """Find talk by source"""
        pass

    @abstractmethod
    def search(self, query: str, filters: Dict[str, Any]) -> Tuple[List[Talk], int]:
        """Search talks with filters"""
        pass

    @abstractmethod
    def update(self, talk: Talk) -> bool:
        """Update existing talk"""
        pass

    @abstractmethod
    def delete(self, talk_id: str) -> bool:
        """Delete talk by ID"""
        pass


class TaxonomyRepository(ABC):
    """Repository interface for taxonomies"""

    @abstractmethod
    def save(self, taxonomy: Taxonomy) -> int:
        """Save taxonomy and return ID"""
        pass

    @abstractmethod
    def find_by_id(self, taxonomy_id: int) -> Optional[Taxonomy]:
        """Find taxonomy by ID"""
        pass

    @abstractmethod
    def find_all(self) -> List[Taxonomy]:
        """Find all taxonomies"""
        pass

    @abstractmethod
    def update(self, taxonomy: Taxonomy) -> bool:
        """Update existing taxonomy"""
        pass

    @abstractmethod
    def delete(self, taxonomy_id: int) -> bool:
        """Delete taxonomy by ID"""
        pass
