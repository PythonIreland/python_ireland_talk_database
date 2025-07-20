from typing import List
from backend.domain.entities.taxonomy import Taxonomy, TaxonomyValue
from backend.contracts.repositories import TaxonomyRepository


class ManageTaxonomyUseCase:
    """Use case for managing taxonomies"""

    def __init__(self, taxonomy_repository: TaxonomyRepository):
        self.taxonomy_repository = taxonomy_repository

    def create_taxonomy(self, name: str, description: str = "") -> Taxonomy:
        """Create a new taxonomy"""
        taxonomy = Taxonomy(name=name, description=description)
        taxonomy_id = self.taxonomy_repository.save(taxonomy)
        taxonomy.id = taxonomy_id
        return taxonomy

    def add_taxonomy_value(
        self, taxonomy_id: int, value_name: str, value_description: str = ""
    ) -> Taxonomy:
        """Add a value to existing taxonomy"""
        taxonomy = self.taxonomy_repository.find_by_id(taxonomy_id)
        if not taxonomy:
            raise ValueError(f"Taxonomy with ID {taxonomy_id} not found")

        # Use domain entity method to add value
        new_value = TaxonomyValue(name=value_name, description=value_description)
        updated_taxonomy = taxonomy.add_value(new_value)

        self.taxonomy_repository.update(updated_taxonomy)
        return updated_taxonomy

    def remove_taxonomy_value(self, taxonomy_id: int, value_name: str) -> Taxonomy:
        """Remove a value from taxonomy"""
        taxonomy = self.taxonomy_repository.find_by_id(taxonomy_id)
        if not taxonomy:
            raise ValueError(f"Taxonomy with ID {taxonomy_id} not found")

        # Use domain entity method to remove value
        updated_taxonomy = taxonomy.remove_value(value_name)

        self.taxonomy_repository.update(updated_taxonomy)
        return updated_taxonomy

    def get_all_taxonomies(self) -> List[Taxonomy]:
        """Get all taxonomies"""
        return self.taxonomy_repository.find_all()
