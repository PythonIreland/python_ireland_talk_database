from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)  # Value object - immutable
class TaxonomyValue:
    """Value object for taxonomy values"""

    id: int
    value: str
    description: str
    color: str = ""

    def __post_init__(self):
        if not self.value.strip():
            raise ValueError("Taxonomy value cannot be empty")


@dataclass
class Taxonomy:
    """Domain entity for taxonomies"""

    id: int
    name: str
    description: str
    values: List[TaxonomyValue]

    def add_value(
        self, value: str, description: str = "", color: str = ""
    ) -> TaxonomyValue:
        """Business rule: add new taxonomy value"""
        # Check for duplicates
        if any(v.value.lower() == value.lower() for v in self.values):
            raise ValueError(
                f"Value '{value}' already exists in taxonomy '{self.name}'"
            )

        # Generate new ID (in real implementation, this would come from persistence)
        new_id = max((v.id for v in self.values), default=0) + 1
        new_value = TaxonomyValue(new_id, value.strip(), description.strip(), color)
        self.values.append(new_value)
        return new_value

    def find_value_by_name(self, value_name: str) -> Optional[TaxonomyValue]:
        """Business rule: find value by name (case-insensitive)"""
        return next(
            (v for v in self.values if v.value.lower() == value_name.lower()), None
        )

    def remove_value(self, value_id: int) -> bool:
        """Business rule: remove taxonomy value"""
        original_length = len(self.values)
        self.values = [v for v in self.values if v.id != value_id]
        return len(self.values) < original_length

    def get_value_count(self) -> int:
        """Business rule: get count of values"""
        return len(self.values)

    def is_valid(self) -> bool:
        """Business rule: taxonomy must have a name and at least one value"""
        return bool(self.name.strip()) and len(self.values) > 0
