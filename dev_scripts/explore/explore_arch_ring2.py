#!/usr/bin/env python3
"""
Ring 2 Architecture Exploration: Use Cases (Application Business Rules)
Application workflows that orchestrate domain entities and services
"""

from typing import Dict, Any

# Import from backend package
from backend.domain.entities.talk import Talk, TalkType
from backend.domain.entities.taxonomy import Taxonomy, TaxonomyValue
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.application.use_cases.create_talk import CreateTalkUseCase
from backend.contracts.repositories import TalkRepository

print("⚙️ Ring 2: Use Cases (Application Business Rules)")
print("=" * 60)
print("Exploring application workflows and use case orchestration...")
print()

print("✅ Successfully imported Ring 2 components:")
print("  - CreateTalkUseCase (application business rule)")
print("  - TalkRepository (interface from Ring 3)")
print("  - Ring 1 dependencies (domain entities & services)")
print()


class MockTalkRepository(TalkRepository):
    """Mock repository for testing use cases without Ring 4 dependencies"""

    def __init__(self):
        self.talks = {}
        self.next_id = 1

    def save(self, talk: Talk) -> str:
        """Save talk and return ID"""
        talk_id = f"mock-{self.next_id}"
        self.next_id += 1
        self.talks[talk_id] = talk
        print(f"   📁 MockRepository: Saved talk '{talk.title}' with ID: {talk_id}")
        return talk_id

    def find_by_id(self, talk_id: str) -> Talk | None:
        """Find talk by ID"""
        talk = self.talks.get(talk_id)
        if talk:
            print(f"   📁 MockRepository: Found talk '{talk.title}' with ID: {talk_id}")
        else:
            print(f"   📁 MockRepository: No talk found with ID: {talk_id}")
        return talk

    def search(self, query: str, filters: Dict[str, Any]) -> tuple[list[Talk], int]:
        """Search talks with filters"""
        # Simple mock search
        results = [
            talk
            for talk in self.talks.values()
            if query.lower() in talk.title.lower()
            or query.lower() in talk.description.lower()
        ]
        print(
            f"   📁 MockRepository: Search for '{query}' found {len(results)} results"
        )
        return results, len(results)

    def delete_all(self) -> bool:
        """Clear all talks"""
        count = len(self.talks)
        self.talks.clear()
        print(f"   📁 MockRepository: Deleted {count} talks")
        return True

    def delete(self, talk_id: str) -> bool:
        """Delete a specific talk"""
        if talk_id in self.talks:
            talk = self.talks.pop(talk_id)
            print(
                f"   📁 MockRepository: Deleted talk '{talk.title}' with ID: {talk_id}"
            )
            return True
        else:
            print(f"   📁 MockRepository: No talk found to delete with ID: {talk_id}")
            return False

    def find_by_source(self, source_type: str, source_id: str) -> Talk | None:
        """Find talk by source type and ID"""
        for talk in self.talks.values():
            if talk.source_type == source_type and talk.source_id == source_id:
                print(
                    f"   📁 MockRepository: Found talk by source {source_type}:{source_id}"
                )
                return talk
        print(
            f"   📁 MockRepository: No talk found for source {source_type}:{source_id}"
        )
        return None

    def update(self, talk: Talk) -> bool:
        """Update an existing talk"""
        if talk.id in self.talks:
            self.talks[talk.id] = talk
            print(
                f"   📁 MockRepository: Updated talk '{talk.title}' with ID: {talk.id}"
            )
            return True
        else:
            print(f"   📁 MockRepository: No talk found to update with ID: {talk.id}")
            return False


def explore_use_case_structure():
    """Examine the structure of use cases"""
    print("🔍 Examining Use Case Structure:")
    print()

    # Look at CreateTalkUseCase methods
    use_case_methods = [
        method for method in dir(CreateTalkUseCase) if not method.startswith("_")
    ]
    print("📋 CreateTalkUseCase capabilities:")
    for method in sorted(use_case_methods):
        print(f"  - {method}")
    print()

    # Check constructor signature
    import inspect

    sig = inspect.signature(CreateTalkUseCase.__init__)
    print(f"🏗️  CreateTalkUseCase constructor: {sig}")
    print()


def explore_create_talk_use_case():
    """Test the CreateTalkUseCase with dependency injection"""
    print("🧪 Testing CreateTalkUseCase (Ring 2)")
    print("=" * 40)

    # Set up dependencies (Ring 1)
    domain_service = TalkDomainService()
    mock_repository = MockTalkRepository()

    # Create the use case with dependency injection
    create_talk_use_case = CreateTalkUseCase(
        talk_repository=mock_repository, domain_service=domain_service
    )

    print("✅ Use case created with injected dependencies:")
    print("  - TalkDomainService (Ring 1)")
    print("  - MockTalkRepository (Ring 3 interface)")
    print()

    return create_talk_use_case, mock_repository


def test_valid_talk_creation(use_case: CreateTalkUseCase):
    """Test creating a valid talk through the use case"""
    print("1. Creating Valid Talk:")

    valid_talk_data = {
        "title": "FastAPI Best Practices",
        "description": "Learn advanced patterns for building scalable APIs with FastAPI, including dependency injection, background tasks, and testing strategies.",
        "speaker_names": ["Jane Developer"],
        "talk_type": "conference_talk",
        "source_type": "manual",
        "source_id": "manual-001",
    }

    try:
        talk_id = use_case.execute(valid_talk_data)
        print(f"   ✅ Talk created successfully with ID: {talk_id}")
        return talk_id
    except Exception as e:
        print(f"   ❌ Error creating talk: {e}")
        return None


def test_invalid_talk_creation(use_case: CreateTalkUseCase):
    """Test use case validation with invalid data"""
    print("2. Testing Validation (Invalid Talk):")

    invalid_talk_data = {
        "title": "",  # Empty title - should fail validation
        "description": "Short",  # Too short
        "speaker_names": [],  # No speakers
        "talk_type": "invalid_type",  # Invalid type
    }

    try:
        talk_id = use_case.execute(invalid_talk_data)
        print(f"   ❌ Unexpected success: {talk_id}")
    except Exception as e:
        print(f"   ✅ Validation caught error (expected): {e}")


def test_auto_tagging_integration(use_case: CreateTalkUseCase):
    """Test that use case integrates domain service auto-tagging"""
    print("3. Testing Auto-tagging Integration:")

    ml_talk_data = {
        "title": "Machine Learning with scikit-learn",
        "description": "Introduction to machine learning algorithms using Python's scikit-learn library. Cover classification, regression, and clustering techniques with practical examples.",
        "speaker_names": ["Dr. ML Expert"],
        "talk_type": "workshop",
        "source_type": "manual",
    }

    try:
        talk_id = use_case.execute(ml_talk_data)
        print(f"   ✅ Talk created with auto-tagging: {talk_id}")

        # The use case should have applied auto-tags via domain service
        print("   🏷️  Auto-tagging should have been applied by domain service")
        return talk_id
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def test_repository_interaction(
    use_case: CreateTalkUseCase, repository: MockTalkRepository, talk_id: str
):
    """Test that use case properly interacts with repository"""
    print("4. Testing Repository Interaction:")

    if talk_id:
        # Try to retrieve the talk through the repository
        saved_talk = repository.find_by_id(talk_id)
        if saved_talk:
            print(f"   ✅ Talk retrieved: '{saved_talk.title}'")
            print(f"   📊 Talk type: {saved_talk.talk_type}")
            print(f"   👥 Speakers: {saved_talk.speaker_names}")
            print(f"   🏷️  Auto-tags: {saved_talk.auto_tags}")
        else:
            print(f"   ❌ Could not retrieve talk with ID: {talk_id}")
    else:
        print("   ⏭️  Skipping - no valid talk ID available")


def explore_use_case_boundaries():
    """Demonstrate use case boundaries and responsibilities"""
    print("🎯 Use Case Boundaries & Responsibilities:")
    print("=" * 40)
    print("✅ What Use Cases DO (Ring 2):")
    print("  - Orchestrate domain entities and services")
    print("  - Implement application-specific business rules")
    print("  - Coordinate between domain and infrastructure")
    print("  - Handle application workflows")
    print("  - Validate application-level constraints")
    print()
    print("❌ What Use Cases DON'T DO:")
    print("  - Know about databases (Ring 4)")
    print("  - Know about HTTP/web frameworks (Ring 4)")
    print("  - Contain pure business logic (Ring 1)")
    print("  - Handle presentation concerns (Ring 3)")
    print()
    print("🔗 Dependencies:")
    print("  - Ring 1: Domain entities & services (inward)")
    print("  - Ring 3: Repository interfaces (inward)")
    print("  - Ring 4: Nothing! (dependency inversion)")
    print()


def main():
    """Main exploration function"""
    try:
        # Explore structure
        explore_use_case_structure()

        # Set up use case
        use_case, repository = explore_create_talk_use_case()

        # Test various scenarios
        print("🧪 Testing Use Case Scenarios:")
        print("-" * 30)

        valid_talk_id = test_valid_talk_creation(use_case)
        print()

        test_invalid_talk_creation(use_case)
        print()

        ml_talk_id = test_auto_tagging_integration(use_case)
        print()

        test_repository_interaction(use_case, repository, valid_talk_id or ml_talk_id)
        print()

        # Explain boundaries
        explore_use_case_boundaries()

        print("⚙️ Ring 2 Summary:")
        print("  ✅ Application business rules and workflows")
        print("  ✅ Orchestrates Ring 1 domain logic")
        print("  ✅ Uses Ring 3 interfaces (dependency inversion)")
        print("  ✅ Framework-independent application logic")
        print("  ✅ Testable with mock dependencies")

    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
