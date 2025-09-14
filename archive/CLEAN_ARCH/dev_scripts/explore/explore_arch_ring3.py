#!/usr/bin/env python3
"""
Ring 3 Architecture Exploration: Interface Adapters
Controllers, presenters, and repository interfaces that adapt between application and infrastructure
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod

# Import from backend package
from backend.domain.entities.talk import Talk, TalkType
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.application.use_cases.create_talk import CreateTalkUseCase
from backend.contracts.repositories import TalkRepository
from backend.contracts.dtos import BaseTalk, TalkSearch

print("🔌 Ring 3: Interface Adapters")
print("=" * 60)
print("Exploring controllers, presenters, and interface contracts...")
print()

print("✅ Successfully imported Ring 3 components:")
print("  - TalkRepository (interface contract)")
print("  - BaseTalk, TalkSearch (data transfer objects)")
print("  - Ring 1 & Ring 2 dependencies for adaptation")
print()


class MockWebController:
    """
    Mock web controller demonstrating Ring 3 interface adapter pattern

    This adapter converts HTTP requests into use case calls and formats responses.
    It sits between the web framework (Ring 4) and use cases (Ring 2).

    CLEAN ARCHITECTURE PATTERN:
    - Ring 3 adapts external interfaces (HTTP) to application interfaces (use cases)
    - Controller doesn't contain business logic - that's in Ring 1 & Ring 2
    - Controller formats data and delegates to use cases
    """

    def __init__(self, create_talk_use_case: CreateTalkUseCase):
        self.create_talk_use_case = create_talk_use_case

    def create_talk_endpoint(self, http_request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP endpoint for creating talks - demonstrates Ring 3 adaptation

        This method:
        1. Extracts data from HTTP request format
        2. Validates HTTP-level concerns (auth, format)
        3. Delegates business logic to Ring 2 use case
        4. Formats response for HTTP
        """
        try:
            # Ring 3 responsibility: Extract and validate HTTP request format
            if "Content-Type" not in http_request_data.get("headers", {}):
                return {
                    "status_code": 400,
                    "body": {"error": "Content-Type header required"},
                    "headers": {"Content-Type": "application/json"},
                }

            request_body = http_request_data.get("body", {})

            # Ring 3 responsibility: Convert HTTP data to use case format
            talk_data = {
                "id": request_body.get("id"),
                "title": request_body.get("title"),
                "description": request_body.get("description"),
                "speaker_names": request_body.get("speakers", []),
                "talk_type": request_body.get("type"),
                "source_type": "web_api",
                "source_id": request_body.get("id"),
            }

            # Ring 3 responsibility: Delegate to Ring 2 use case
            talk_id = self.create_talk_use_case.execute(talk_data)

            # Ring 3 responsibility: Format success response for HTTP
            return {
                "status_code": 201,
                "body": {
                    "message": "Talk created successfully",
                    "talk_id": talk_id,
                    "resource_url": f"/api/talks/{talk_id}",
                },
                "headers": {"Content-Type": "application/json"},
            }

        except ValueError as e:
            # Ring 3 responsibility: Convert business errors to HTTP format
            return {
                "status_code": 400,
                "body": {"error": f"Validation failed: {str(e)}"},
                "headers": {"Content-Type": "application/json"},
            }
        except Exception as e:
            # Ring 3 responsibility: Handle unexpected errors for HTTP
            return {
                "status_code": 500,
                "body": {"error": "Internal server error"},
                "headers": {"Content-Type": "application/json"},
            }

    def list_talks_endpoint(self, http_request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock endpoint demonstrating query parameter handling"""
        # In a real implementation, this would use a SearchTalksUseCase
        query_params = http_request_data.get("query_params", {})
        search_term = query_params.get("q", "")

        # Mock response for demonstration
        return {
            "status_code": 200,
            "body": {
                "talks": [],
                "total": 0,
                "search_term": search_term,
                "message": "This would use a SearchTalksUseCase in real implementation",
            },
            "headers": {"Content-Type": "application/json"},
        }


class MockPresenter:
    """
    Presenter for formatting use case outputs into specific presentation formats

    Presenters are Ring 3 components that take raw data from use cases
    and format it for specific output formats (JSON, HTML, XML, etc.)
    """

    @staticmethod
    def present_talk_creation_success(
        talk_id: str, talk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format successful talk creation for presentation"""
        return {
            "success": True,
            "data": {
                "id": talk_id,
                "title": talk_data.get("title"),
                "speakers": talk_data.get("speaker_names", []),
                "type": talk_data.get("talk_type"),
                "created_at": "2025-07-20T10:30:00Z",  # Mock timestamp
                "links": {
                    "self": f"/api/talks/{talk_id}",
                    "edit": f"/api/talks/{talk_id}/edit",
                    "delete": f"/api/talks/{talk_id}",
                },
            },
            "message": "Talk has been successfully created",
        }

    @staticmethod
    def present_validation_error(errors: List[str]) -> Dict[str, Any]:
        """Format validation errors for presentation"""
        return {
            "success": False,
            "errors": [{"field": "general", "message": error} for error in errors],
            "message": "Please correct the validation errors and try again",
        }

    @staticmethod
    def present_talk_list(
        talks: List[Talk], total: int, search_term: str = ""
    ) -> Dict[str, Any]:
        """Format talk list for presentation"""
        return {
            "success": True,
            "data": {
                "talks": [
                    {
                        "id": talk.id,
                        "title": talk.title,
                        "speakers": talk.speaker_names,
                        "type": talk.talk_type.value,
                        "auto_tags": talk.auto_tags,
                    }
                    for talk in talks
                ],
                "meta": {
                    "total": total,
                    "search_term": search_term,
                    "count": len(talks),
                },
            },
        }


def explore_ring3_structure():
    """Examine Ring 3 components and their responsibilities"""
    print("🔍 Examining Ring 3 Structure:")
    print()

    print("📋 Ring 3 Components:")
    print("  - Controllers: Adapt HTTP requests to use case calls")
    print("  - Presenters: Format use case outputs for presentation")
    print("  - Repository Interfaces: Define contracts for Ring 4 implementations")
    print("  - DTOs: Data Transfer Objects for cross-boundary communication")
    print()

    # Examine TalkRepository interface
    repository_methods = [
        method
        for method in dir(TalkRepository)
        if not method.startswith("_")
        and callable(getattr(TalkRepository, method, None))
    ]
    print("📋 TalkRepository interface methods:")
    for method in sorted(repository_methods):
        print(f"  - {method}")
    print()

    # Check DTO structure
    dto_attributes = [attr for attr in dir(BaseTalk) if not attr.startswith("_")]
    print("📋 BaseTalk DTO attributes:")
    for attr in sorted(dto_attributes):
        print(f"  - {attr}")
    print()

    # Check TalkSearch DTO
    search_attributes = [attr for attr in dir(TalkSearch) if not attr.startswith("_")]
    print("📋 TalkSearch DTO attributes:")
    for attr in sorted(search_attributes):
        print(f"  - {attr}")
    print()


def test_controller_adaptation():
    """Test how controllers adapt HTTP requests to use cases"""
    print("🧪 Testing Controller Adaptation (Ring 3):")
    print("=" * 45)

    # Set up dependencies (Ring 1 & Ring 2)
    domain_service = TalkDomainService()

    # Mock repository for testing
    class MockRepository(TalkRepository):
        def save(self, talk: Talk) -> str:
            return f"ctrl-test-{talk.title[:10]}"

        def find_by_id(self, talk_id: str) -> Talk | None:
            pass

        def search(self, query: str, filters: Dict[str, Any]) -> tuple[List[Talk], int]:
            pass

        def delete_all(self) -> bool:
            pass

        def delete(self, talk_id: str) -> bool:
            pass

        def find_by_source(self, source_type: str, source_id: str) -> Talk | None:
            pass

        def update(self, talk: Talk) -> bool:
            pass

    repository = MockRepository()
    use_case = CreateTalkUseCase(repository, domain_service)
    controller = MockWebController(use_case)

    print("1. Testing Valid HTTP Request Adaptation:")

    # Simulate HTTP request
    http_request = {
        "headers": {"Content-Type": "application/json"},
        "body": {
            "id": "http-001",
            "title": "Building REST APIs with FastAPI",
            "description": "Learn how to build scalable REST APIs using FastAPI framework with best practices.",
            "speakers": ["Jane API Developer"],
            "type": "tutorial",
        },
    }

    response = controller.create_talk_endpoint(http_request)
    print(f"   📥 HTTP Request: {http_request['body']['title']}")
    print(
        f"   📤 HTTP Response: {response['status_code']} - {response['body']['message']}"
    )
    print(f"   🆔 Generated ID: {response['body']['talk_id']}")
    print()

    print("2. Testing Invalid HTTP Request Handling:")

    # Simulate invalid HTTP request
    invalid_request = {
        "headers": {},  # Missing Content-Type
        "body": {"title": "", "speakers": []},  # Invalid data
    }

    response = controller.create_talk_endpoint(invalid_request)
    print(f"   📥 Invalid Request: Missing Content-Type")
    print(
        f"   📤 HTTP Response: {response['status_code']} - {response['body']['error']}"
    )
    print()

    print("3. Testing Query Parameter Handling:")

    list_request = {"query_params": {"q": "FastAPI", "limit": "10"}}

    response = controller.list_talks_endpoint(list_request)
    print(f"   📥 Query: {list_request['query_params']}")
    print(f"   📤 Response: {response['status_code']} - {response['body']['message']}")
    print()


def test_presenter_formatting():
    """Test how presenters format data for different output formats"""
    print("🎨 Testing Presenter Formatting (Ring 3):")
    print("=" * 45)

    presenter = MockPresenter()

    print("1. Testing Success Response Formatting:")

    success_data = presenter.present_talk_creation_success(
        "presenter-001",
        {
            "title": "Clean Architecture in Python",
            "speaker_names": ["Bob Architect"],
            "talk_type": "workshop",
        },
    )

    print(f"   ✅ Success Format: {success_data['message']}")
    print(f"   🔗 Generated Links: {list(success_data['data']['links'].keys())}")
    print()

    print("2. Testing Error Response Formatting:")

    error_data = presenter.present_validation_error(
        ["Title is required", "At least one speaker is required"]
    )

    print(f"   ❌ Error Format: {error_data['message']}")
    print(f"   📝 Error Count: {len(error_data['errors'])}")
    print()

    print("3. Testing List Response Formatting:")

    # Create sample talks for list presentation
    sample_talks = [
        Talk(
            id="sample-1",
            title="Python Best Practices",
            description="Learn Python coding standards",
            talk_type=TalkType.CONFERENCE_TALK,
            speaker_names=["Alice Pythonista"],
            auto_tags=["Python", "Best Practices"],
        )
    ]

    list_data = presenter.present_talk_list(sample_talks, 1, "Python")
    print(f"   📊 List Format: {list_data['data']['meta']}")
    print(f"   🏷️  Sample Talk Tags: {list_data['data']['talks'][0]['auto_tags']}")
    print()


def explore_interface_contracts():
    """Explore how Ring 3 defines contracts between layers"""
    print("📜 Ring 3 Interface Contracts:")
    print("=" * 35)

    print("🔗 Repository Interface Contract (Ring 3 → Ring 4):")
    print("  - Defines what Ring 4 implementations must provide")
    print("  - Ring 2 use cases depend on these interfaces")
    print("  - Ring 4 infrastructure implements these contracts")
    print()

    print("🌐 HTTP Interface Contract (Ring 4 → Ring 3):")
    print("  - Controllers define expected HTTP request/response format")
    print("  - Ring 4 web frameworks call these controller methods")
    print("  - Ring 3 adapts between HTTP and application concerns")
    print()

    print("🎯 DTO Contracts (Cross-boundary data transfer):")
    print("  - Define data structure for crossing architectural boundaries")
    print("  - Prevent Ring 1 entities from leaking to external systems")
    print("  - Allow different representations for different contexts")
    print()


def explore_ring3_dependency_injection():
    """Demonstrate Ring 3 dependency injection patterns"""
    print("💉 Ring 3 Dependency Injection Patterns:")
    print("=" * 45)

    print("🔄 TWO-WAY INJECTION in Ring 3:")
    print()

    print("1️⃣ FROM Ring 4 TO Ring 3 (Ring 4 injects controllers):")
    print("   🌐 Web Framework (Ring 4) creates and injects Ring 3 controllers")
    print("   📝 Example: FastAPI router injects MockWebController")
    print("   💡 Ring 4 manages controller lifecycle and dependencies")
    print()

    print("2️⃣ FROM Ring 3 TO Ring 2 (Ring 3 injects use cases):")
    print("   🔌 Controller (Ring 3) receives and uses Ring 2 use cases")
    print("   📝 Example: MockWebController receives CreateTalkUseCase")
    print("   💡 Ring 3 adapts use case calls to HTTP responses")
    print()

    print("🏗️  INJECTION HIERARCHY:")
    print("   Ring 4 Web Framework")
    print("   ├── injects → Ring 3 Controller")
    print("   │   ├── receives → Ring 2 Use Case")
    print("   │   │   ├── receives → Ring 1 Domain Service")
    print("   │   │   └── receives → Ring 3 Repository Interface")
    print("   │   └── adapts responses via → Ring 3 Presenter")
    print("   └── implements → Ring 3 Repository Interface")
    print()

    # Demonstrate the pattern with mock Ring 4 framework
    print("🧪 DEMONSTRATION - Ring 4 Framework injecting Ring 3:")

    class MockWebFramework:
        """Simulates a Ring 4 web framework (like FastAPI, Flask)"""

        def __init__(self):
            self.routes = {}

        def register_controller(self, path: str, controller: MockWebController):
            """Ring 4 responsibility: Inject and register Ring 3 controllers"""
            self.routes[path] = controller
            print(f"   🌐 Ring 4 Framework: Injected controller for {path}")

        def handle_request(
            self, path: str, request_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Ring 4 responsibility: Route requests to Ring 3 controllers"""
            if path in self.routes:
                controller = self.routes[path]
                print(f"   🔀 Ring 4 Framework: Routing request to {path}")
                return controller.create_talk_endpoint(request_data)
            else:
                return {"status_code": 404, "body": {"error": "Not found"}}

    # Set up the injection chain
    print("   Building injection chain...")

    # Ring 1 & Ring 2 setup (bottom of chain)
    domain_service = TalkDomainService()

    class MockRepo(TalkRepository):
        def save(self, talk: Talk) -> str:
            return f"injection-demo-{talk.title[:8]}"

        def find_by_id(self, talk_id: str) -> Talk | None:
            pass

        def search(self, query: str, filters: Dict[str, Any]) -> tuple[List[Talk], int]:
            pass

        def delete_all(self) -> bool:
            pass

        def delete(self, talk_id: str) -> bool:
            pass

        def find_by_source(self, source_type: str, source_id: str) -> Talk | None:
            pass

        def update(self, talk: Talk) -> bool:
            pass

    repository = MockRepo()
    use_case = CreateTalkUseCase(repository, domain_service)
    print("   ✅ Ring 1 & Ring 2: Domain service and use case created")

    # Ring 3 setup (receives Ring 2 dependencies)
    controller = MockWebController(use_case)  # Ring 3 receives Ring 2
    print("   ✅ Ring 3: Controller created with injected use case")

    # Ring 4 setup (injects Ring 3 dependencies)
    framework = MockWebFramework()
    framework.register_controller("/api/talks", controller)  # Ring 4 injects Ring 3
    print("   ✅ Ring 4: Framework registered controller")
    print()

    # Test the full injection chain
    print("📡 Testing Full Injection Chain:")
    request = {
        "headers": {"Content-Type": "application/json"},
        "body": {
            "id": "injection-001",
            "title": "Dependency Injection Demo",
            "description": "Shows how DI works across rings",
            "speakers": ["DI Expert"],
            "type": "workshop",
        },
    }

    response = framework.handle_request("/api/talks", request)
    print(f"   📥 Request: {request['body']['title']}")
    print(f"   📤 Response: {response['status_code']} - {response['body']['message']}")
    print()

    print("🎯 KEY INSIGHT:")
    print("   Ring 3 is BOTH an injection receiver AND an injection provider!")
    print("   ⬇️  Ring 3 RECEIVES dependencies from Ring 4")
    print("   ⬆️  Ring 3 PROVIDES adapted interfaces to Ring 2")
    print()


def explore_ring3_boundaries():
    """Demonstrate Ring 3 responsibilities and boundaries"""
    print("🎯 Ring 3 Boundaries & Responsibilities:")
    print("=" * 45)

    print("✅ What Ring 3 DOES (Interface Adapters):")
    print("  - Adapt external interfaces to application interfaces")
    print("  - Handle protocol-specific concerns (HTTP, messaging)")
    print("  - Format data for presentation (JSON, HTML, XML)")
    print("  - Define contracts for Ring 4 implementations")
    print("  - Convert between DTOs and domain entities")
    print("  - Handle framework-specific validation (HTTP headers)")
    print()

    print("❌ What Ring 3 DOESN'T DO (Boundaries):")
    print("  - Contain business logic (that belongs in Ring 1 & Ring 2)")
    print("  - Know about specific databases or frameworks (Ring 4 concern)")
    print("  - Make business decisions (Ring 2 responsibility)")
    print("  - Implement infrastructure details (Ring 4 responsibility)")
    print()

    print("🔄 Ring 3 Data Flow:")
    print("  Inbound: Ring 4 → Ring 3 Controller → Ring 2 Use Case")
    print("  Outbound: Ring 2 Use Case → Ring 3 Presenter → Ring 4")
    print()

    print("🧩 Testing Strategy:")
    print("  - Mock Ring 2 use cases for controller testing")
    print("  - Mock Ring 4 implementations for integration testing")
    print("  - Test data transformation and format adaptation")
    print()


def main():
    """Main exploration function"""
    try:
        # Explore Ring 3 structure
        explore_ring3_structure()

        # Test controller adaptation
        test_controller_adaptation()

        # Test presenter formatting
        test_presenter_formatting()

        # Explore interface contracts
        explore_interface_contracts()

        # Explore dependency injection patterns
        explore_ring3_dependency_injection()

        # Explain boundaries
        explore_ring3_boundaries()

        print("🔌 Ring 3 Summary - INTERFACE ADAPTERS:")
        print("  ✅ Adapts between application core and external systems")
        print("  ✅ Controllers handle incoming requests and delegate to use cases")
        print("  ✅ Presenters format outgoing responses for specific formats")
        print("  ✅ Repository interfaces define contracts for Ring 4")
        print("  ✅ DTOs enable clean data transfer across boundaries")
        print("  ✅ Framework-agnostic interface definitions")
        print("  ✅ Testable with mocked dependencies from adjacent rings")

    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
