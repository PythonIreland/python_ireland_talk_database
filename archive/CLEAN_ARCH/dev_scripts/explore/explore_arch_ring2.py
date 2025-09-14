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
    """
    Mock repository implementation for testing Ring 2 use cases in isolation

    This is a MOCK IMPLEMENTATION of the TalkRepository interface (Ring 3).
    It's injected into use cases to test Ring 2 logic without Ring 4 dependencies.

    CLEAN ARCHITECTURE PATTERN:
    - Ring 2 depends on Ring 3 INTERFACE (TalkRepository)
    - This mock provides that interface for testing
    - Real implementation would be in Ring 4 (infrastructure)
    - Use case doesn't know which implementation it gets (dependency inversion)
    """

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
    """Test the CreateTalkUseCase with proper dependency injection"""
    print("🧪 Testing CreateTalkUseCase (Ring 2) - Dependency Injection Pattern")
    print("=" * 60)

    # DEPENDENCY INJECTION: Set up dependencies to inject (Ring 1 & Ring 3 interfaces)
    # These are the dependencies that Ring 2 needs, but we inject them from outside
    injected_domain_service = TalkDomainService()  # Ring 1 dependency
    injected_repository = MockTalkRepository()  # Ring 3 interface implementation

    # DEPENDENCY INJECTION: Create the use case by injecting its dependencies
    # This is the CORRECT pattern - use case doesn't create its own dependencies
    create_talk_use_case = CreateTalkUseCase(
        talk_repository=injected_repository,  # Injected Ring 3 interface
        domain_service=injected_domain_service,  # Injected Ring 1 service
    )

    print("✅ Use case created with INJECTED dependencies (Clean Architecture):")
    print("  - TalkDomainService (Ring 1) - INJECTED from outside")
    print("  - MockTalkRepository (Ring 3 interface) - INJECTED mock implementation")
    print("  - Use case doesn't know about concrete implementations!")
    print()

    return create_talk_use_case, injected_repository


def test_valid_talk_creation(use_case: CreateTalkUseCase):
    """Test creating a valid talk through the use case"""
    print("1. Creating Valid Talk:")

    valid_talk_data = {
        "id": "test-001",  # Required by current use case implementation
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
        "id": "test-002",  # Required by current use case implementation
        "title": "Machine Learning with scikit-learn",
        "description": "Introduction to machine learning algorithms using Python's scikit-learn library. Cover classification, regression, and clustering techniques with practical examples.",
        "speaker_names": ["Dr. ML Expert"],
        "talk_type": "workshop",
        "source_type": "manual",
        "source_id": "manual-002",
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
    use_case: CreateTalkUseCase, injected_repository: MockTalkRepository, talk_id: str
):
    """Test that use case properly interacts with INJECTED repository dependency"""
    print("4. Testing Repository Interaction via Dependency Injection:")

    if talk_id:
        # The use case used the INJECTED repository to save the talk
        # Now we can verify through the same injected instance
        saved_talk = injected_repository.find_by_id(talk_id)
        if saved_talk:
            print(f"   ✅ Talk retrieved via INJECTED repository: '{saved_talk.title}'")
            print(f"   📊 Talk type: {saved_talk.talk_type}")
            print(f"   👥 Speakers: {saved_talk.speaker_names}")
            print(f"   🏷️  Auto-tags: {saved_talk.auto_tags}")
            print("   🔄 Use case and test use SAME injected repository instance")
        else:
            print(f"   ❌ Could not retrieve talk with ID: {talk_id}")
    else:
        print("   ⏭️  Skipping - no valid talk ID available")


def demonstrate_resilience_benefit():
    """Demonstrate how dependency injection makes code resilient to implementation failures"""
    print("🛡️  Dependency Injection Resilience Demonstration:")
    print("=" * 55)
    print("Scenario: What happens when different repository implementations fail?")
    print()

    # Create the same use case but with different repository implementations
    domain_service = TalkDomainService()

    # Working implementation
    working_repo = MockTalkRepository()

    # Broken implementation (simulates a database that's down)
    class BrokenDatabaseRepository(TalkRepository):
        """Simulates a database repository that's currently failing"""

        def save(self, talk: Talk) -> str:
            raise Exception("Database connection failed! Network timeout.")

        def find_by_id(self, talk_id: str) -> Talk | None:
            raise Exception("Database connection failed! Network timeout.")

        def search(self, query: str, filters: Dict[str, Any]) -> tuple[list[Talk], int]:
            raise Exception("Database connection failed! Network timeout.")

        def delete_all(self) -> bool:
            raise Exception("Database connection failed! Network timeout.")

        def delete(self, talk_id: str) -> bool:
            raise Exception("Database connection failed! Network timeout.")

        def find_by_source(self, source_type: str, source_id: str) -> Talk | None:
            raise Exception("Database connection failed! Network timeout.")

        def update(self, talk: Talk) -> bool:
            raise Exception("Database connection failed! Network timeout.")

    broken_repo = BrokenDatabaseRepository()

    print("📊 Testing Multiple Callers with Different Implementations:")
    print()

    # Caller 1: Uses working repository
    print("🟢 Caller 1 (Web API): Using MockTalkRepository")
    try:
        use_case_1 = CreateTalkUseCase(
            talk_repository=working_repo, domain_service=domain_service
        )
        talk_data = {
            "id": "resilience-001",  # Required by current use case implementation
            "title": "FastAPI Tutorial",
            "description": "A comprehensive guide to building APIs with FastAPI framework.",
            "speaker_names": ["API Expert"],
            "talk_type": "tutorial",
            "source_type": "web_form",
            "source_id": "form-123",
        }
        result = use_case_1.execute(talk_data)
        print(f"   ✅ SUCCESS: Talk created with ID {result}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
    print()

    # Caller 2: Uses broken repository
    print("🔴 Caller 2 (Background Job): Using BrokenDatabaseRepository")
    try:
        use_case_2 = CreateTalkUseCase(
            talk_repository=broken_repo,  # This one is broken!
            domain_service=domain_service,
        )
        talk_data = {
            "id": "resilience-002",  # Required by current use case implementation
            "title": "Machine Learning Basics",
            "description": "Introduction to ML concepts and practical applications.",
            "speaker_names": ["ML Researcher"],
            "talk_type": "workshop",
            "source_type": "import",
            "source_id": "import-456",
        }
        result = use_case_2.execute(talk_data)
        print(f"   ✅ SUCCESS: Talk created with ID {result}")
    except Exception as e:
        print(f"   ❌ FAILED (expected): {e}")
    print()

    # Caller 3: Uses working repository again
    print("🟢 Caller 3 (Mobile App): Using MockTalkRepository")
    try:
        use_case_3 = CreateTalkUseCase(
            talk_repository=working_repo,  # Same working repo as Caller 1
            domain_service=domain_service,
        )
        talk_data = {
            "id": "resilience-003",  # Required by current use case implementation
            "title": "React Native Deep Dive",
            "description": "Advanced techniques for building mobile apps with React Native.",
            "speaker_names": ["Mobile Dev"],
            "talk_type": "conference_talk",
            "source_type": "mobile_app",
            "source_id": "mobile-789",
        }
        result = use_case_3.execute(talk_data)
        print(f"   ✅ SUCCESS: Talk created with ID {result}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
    print()

    print("🎯 KEY INSIGHT - Your Observation:")
    print("  💡 Caller 1 (Web API) ✅ WORKS - uses working repository")
    print("  💡 Caller 2 (Background Job) ❌ FAILS - database is down")
    print("  💡 Caller 3 (Mobile App) ✅ WORKS - uses working repository")
    print()
    print("🛡️  RESILIENCE BENEFIT:")
    print("  ✅ Each caller is ISOLATED from others' implementation problems")
    print("  ✅ Working callers continue working even when others fail")
    print("  ✅ No shared global state that could break everything")
    print("  ✅ Easy to swap implementations per caller")
    print("  ✅ Ring 2 use case code is IDENTICAL across all callers")
    print()
    print("🚫 WITHOUT Dependency Injection (Anti-pattern):")
    print("  ❌ If use case had: repository = DatabaseRepository() inside")
    print("  ❌ ALL callers would fail when database goes down")
    print("  ❌ No way to give different callers different implementations")
    print("  ❌ Hard to test with mocks")
    print("  ❌ Tight coupling makes system fragile")
    print()


def compare_ring1_vs_ring2_behaviors():
    """Compare behaviors we explored in Ring 1 vs Ring 2"""
    print("🔄 Ring 1 vs Ring 2: Behavior Comparison")
    print("=" * 50)
    print()

    print("🎯 RING 1 BEHAVIORS (Enterprise Business Rules):")
    print("  📊 WHAT: Pure business logic and domain entities")
    print("  🏗️  WHERE: Talk entity, TalkDomainService")
    print("  🔍 EXAMPLES from Ring 1 exploration:")
    print("    • talk.is_valid() - Entity validates itself")
    print("    • talk.has_keyword('Python') - Entity searches its own content")
    print("    • talk.is_by_speaker('Alice') - Entity checks its own speakers")
    print("    • TalkDomainService.extract_auto_tags() - Pure business logic")
    print("    • TalkDomainService.validate_talk_data() - Domain validation rules")
    print("    • TalkDomainService.normalize_speaker_names() - Data normalization")
    print("  ✅ CHARACTERISTICS:")
    print("    • No external dependencies (databases, HTTP, etc.)")
    print("    • Framework-agnostic")
    print("    • Immediate execution (no I/O operations)")
    print("    • Self-contained business rules")
    print("    • Each entity manages its OWN behavior independently")
    print("    • Cross-references only for properties/inheritance, NOT behavior")
    print()

    print("⚙️ RING 2 BEHAVIORS (Application Business Rules):")
    print("  📊 WHAT: Use case workflows and orchestration")
    print("  🏗️  WHERE: CreateTalkUseCase.execute()")
    print("  🔍 EXAMPLES from Ring 2 exploration:")
    print("    • use_case.execute(talk_data) - Orchestrates entire workflow")
    print("    • Validates data using Ring 1 domain service")
    print("    • Creates domain entities using Ring 1 factories")
    print("    • Applies business rules via Ring 1 services")
    print("    • Persists data via Ring 3 repository interface")
    print("    • Coordinates multiple Ring 1 objects together")
    print("  ✅ CHARACTERISTICS:")
    print("    • Depends on Ring 1 + Ring 3 interfaces")
    print("    • Application-specific workflows")
    print("    • I/O operations (save to repository)")
    print("    • Dependencies injected from outside")
    print()

    print("🔗 KEY DIFFERENCES:")
    print()
    print("1. 🎯 SCOPE & PURPOSE:")
    print("   Ring 1: 'How does a Talk behave?' (individual entity logic)")
    print("   Ring 2: 'How do we create a Talk?' (application workflow)")
    print()

    print("2. 📦 DEPENDENCIES:")
    print("   Ring 1: ZERO external dependencies")
    print("   Ring 1: Cross-references only for properties (Talk → TalkType)")
    print("   Ring 1: Each entity's behavior is self-contained")
    print("   Ring 2: Depends on Ring 1 + Ring 3 interfaces")
    print("   Ring 2: Orchestrates multiple Ring 1 entities together")
    print()

    print("3. 🧪 EXECUTION STYLE:")
    print("   Ring 1: talk.is_valid() → Immediate boolean result")
    print("   Ring 2: use_case.execute() → Complex workflow with I/O")
    print()

    print("4. 🎭 BEHAVIOR EXAMPLES:")
    print("   Ring 1: talk.has_keyword('Python') → Simple boolean check")
    print(
        "   Ring 2: CreateTalkUseCase.execute() → Validate → Create → Save → Return ID"
    )
    print()

    print("5. 🔄 ORCHESTRATION:")
    print("   Ring 1: Individual methods (validate, normalize, extract)")
    print("   Ring 2: Combines multiple Ring 1 methods into workflows")
    print()

    print("6. 🧩 TESTABILITY:")
    print("   Ring 1: Unit tests, no mocks needed (pure functions)")
    print("   Ring 2: Integration tests, requires mock dependencies")
    print()

    print("💡 PRACTICAL EXAMPLE:")
    print("   Ring 1: domain_service.validate_talk_data(data) → ['Title required']")
    print(
        "   Ring 2: use_case.execute(data) → Validates → Creates → Saves → 'talk-123'"
    )
    print()

    print("🎯 SUMMARY:")
    print("   Ring 1: 'WHAT the business rules are'")
    print("   Ring 2: 'HOW to apply business rules in workflows'")
    print()


def explore_use_case_boundaries():
    """Demonstrate use case boundaries and Clean Architecture dependency injection"""
    print("🎯 Use Case Boundaries & Dependency Injection Pattern:")
    print("=" * 55)
    print("✅ What Use Cases DO (Ring 2):")
    print("  - Orchestrate domain entities and services")
    print("  - Implement application-specific business rules")
    print("  - Coordinate between domain and infrastructure")
    print("  - Handle application workflows")
    print("  - Validate application-level constraints")
    print()
    print("❌ What Use Cases DON'T DO (Anti-patterns):")
    print("  - Create their own dependencies (no 'new DatabaseRepository()')")
    print("  - Know about concrete implementations (no imports from Ring 4)")
    print("  - Know about databases, HTTP, or framework details")
    print("  - Contain pure business logic (that belongs in Ring 1)")
    print("  - Handle presentation concerns (that belongs in Ring 3)")
    print()
    print("🔗 DEPENDENCY INJECTION PATTERN:")
    print("  - Ring 1: Domain entities & services (injected dependencies)")
    print("  - Ring 3: Repository interfaces (injected as abstractions)")
    print("  - Ring 4: NOTHING! Use case never imports from Ring 4")
    print("  - Constructor: Receives all dependencies from outside")
    print("  - Testing: Easy to inject mocks and stubs")
    print()
    print("🏗️  CLEAN ARCHITECTURE PRINCIPLE:")
    print("  'Dependencies point INWARD, but we INJECT from OUTSIDE'")
    print("  - Use case depends on INTERFACES (Ring 3)")
    print("  - Concrete implementations provided by dependency injection")
    print("  - Use case testable in isolation with mocks")
    print()


def main():
    """Main exploration function"""
    try:
        # Explore structure
        explore_use_case_structure()

        # Set up use case
        use_case, injected_repository = explore_create_talk_use_case()

        # Test various scenarios
        print("🧪 Testing Use Case Scenarios:")
        print("-" * 30)

        valid_talk_id = test_valid_talk_creation(use_case)
        print()

        test_invalid_talk_creation(use_case)
        print()

        ml_talk_id = test_auto_tagging_integration(use_case)
        print()

        test_repository_interaction(
            use_case, injected_repository, valid_talk_id or ml_talk_id
        )
        print()

        # Demonstrate resilience benefit
        demonstrate_resilience_benefit()

        # Compare Ring 1 vs Ring 2 behaviors
        compare_ring1_vs_ring2_behaviors()

        # Explain boundaries
        explore_use_case_boundaries()

        print("⚙️ Ring 2 Summary - DEPENDENCY INJECTION PATTERN:")
        print("  ✅ Application business rules and workflows")
        print("  ✅ Orchestrates Ring 1 domain logic via injection")
        print("  ✅ Uses Ring 3 interfaces via injection (dependency inversion)")
        print("  ✅ Framework-independent application logic")
        print("  ✅ Testable with injected mock dependencies")
        print("  ✅ Never creates its own dependencies (Clean Architecture)")
        print("  ✅ Constructor receives all dependencies from outside")

    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
