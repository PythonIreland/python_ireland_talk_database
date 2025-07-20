#!/usr/bin/env python3
"""
Ring 4 Architecture Exploration: Frameworks & Drivers
Concrete implementations of databases, web frameworks, external APIs, and infrastructure
"""

from typing import Dict, Any, List
import json
from datetime import datetime

# Import from backend package
from backend.domain.entities.talk import Talk, TalkType
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.application.use_cases.create_talk import CreateTalkUseCase
from backend.contracts.repositories import TalkRepository
from backend.contracts.dtos import BaseTalk, TalkSearch

print("🏗️ Ring 4: Frameworks & Drivers")
print("=" * 60)
print("Exploring concrete implementations of infrastructure and frameworks...")
print()

print("✅ Successfully imported dependencies:")
print("  - Ring 1, 2, 3 components for implementation")
print("  - Ready to create concrete Ring 4 implementations")
print()


class PostgreSQLTalkRepository(TalkRepository):
    """
    Concrete PostgreSQL implementation of TalkRepository interface

    This is a RING 4 IMPLEMENTATION of the Ring 3 interface contract.
    It knows about specific database technology (PostgreSQL) and implements
    the repository pattern for actual data persistence.

    CLEAN ARCHITECTURE PATTERN:
    - Ring 4 implements Ring 3 interfaces
    - Contains infrastructure-specific code (SQL, connection handling)
    - Ring 1, 2, 3 don't know this exists - they only know the interface
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.talks_table = {}  # Simulating database table
        self.next_id = 1
        print(f"   🗄️  PostgreSQL Repository: Connected to {connection_string}")

    def save(self, talk: Talk) -> str:
        """PostgreSQL-specific implementation of save"""
        # Simulate SQL INSERT
        talk_id = f"pg-{self.next_id}"
        self.next_id += 1

        # Simulate SQL execution
        sql_insert = f"""
        INSERT INTO talks (id, title, description, speaker_names, talk_type, auto_tags, created_at, updated_at)
        VALUES ('{talk_id}', '{talk.title}', '{talk.description}', ARRAY{talk.speaker_names}, 
                '{talk.talk_type.value}', ARRAY{talk.auto_tags}, NOW(), NOW())
        """

        # Simulate database transaction
        self.talks_table[talk_id] = {
            "id": talk_id,
            "title": talk.title,
            "description": talk.description,
            "speaker_names": talk.speaker_names,
            "talk_type": talk.talk_type.value,
            "auto_tags": talk.auto_tags,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "source_type": talk.source_type,
            "source_id": talk.source_id,
        }

        print(f"   📊 PostgreSQL: Executed INSERT for '{talk.title}' → ID: {talk_id}")
        print(f"   🔍 SQL: {sql_insert.strip()[:100]}...")
        return talk_id

    def find_by_id(self, talk_id: str) -> Talk | None:
        """PostgreSQL-specific implementation of find by ID"""
        # Simulate SQL SELECT
        sql_select = f"SELECT * FROM talks WHERE id = '{talk_id}'"
        print(f"   🔍 PostgreSQL: {sql_select}")

        if talk_id in self.talks_table:
            row = self.talks_table[talk_id]
            talk = Talk(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                talk_type=TalkType(row["talk_type"]),
                speaker_names=row["speaker_names"],
                auto_tags=row["auto_tags"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                source_type=row.get("source_type"),
                source_id=row.get("source_id"),
            )
            print(f"   ✅ PostgreSQL: Found talk '{talk.title}'")
            return talk
        else:
            print(f"   ❌ PostgreSQL: No talk found with ID {talk_id}")
            return None

    def search(self, query: str, filters: Dict[str, Any]) -> tuple[List[Talk], int]:
        """PostgreSQL-specific implementation with full-text search"""
        # Simulate PostgreSQL full-text search
        sql_search = f"""
        SELECT *, ts_rank(to_tsvector(title || ' ' || description), to_tsquery('{query}')) as rank
        FROM talks 
        WHERE to_tsvector(title || ' ' || description) @@ to_tsquery('{query}')
        ORDER BY rank DESC
        LIMIT {filters.get('limit', 20)} OFFSET {filters.get('offset', 0)}
        """

        print(f"   🔍 PostgreSQL Full-Text Search: {query}")
        print(f"   📊 SQL: {sql_search.strip()[:100]}...")

        # Simulate search results
        results = [
            Talk(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                talk_type=TalkType(row["talk_type"]),
                speaker_names=row["speaker_names"],
                auto_tags=row["auto_tags"],
            )
            for row in self.talks_table.values()
            if query.lower() in row["title"].lower()
            or query.lower() in row["description"].lower()
        ]

        print(f"   📈 PostgreSQL: Found {len(results)} matching talks")
        return results, len(results)

    def delete_all(self) -> bool:
        """PostgreSQL-specific implementation of bulk delete"""
        sql_delete = "DELETE FROM talks"
        count = len(self.talks_table)
        self.talks_table.clear()
        print(f"   🗑️  PostgreSQL: {sql_delete} → Deleted {count} rows")
        return True

    def delete(self, talk_id: str) -> bool:
        """PostgreSQL-specific implementation of delete"""
        sql_delete = f"DELETE FROM talks WHERE id = '{talk_id}'"
        if talk_id in self.talks_table:
            del self.talks_table[talk_id]
            print(f"   🗑️  PostgreSQL: {sql_delete} → Deleted 1 row")
            return True
        else:
            print(f"   ❌ PostgreSQL: {sql_delete} → No rows affected")
            return False

    def find_by_source(self, source_type: str, source_id: str) -> Talk | None:
        """PostgreSQL-specific implementation with compound index"""
        sql_select = f"SELECT * FROM talks WHERE source_type = '{source_type}' AND source_id = '{source_id}'"
        print(f"   🔍 PostgreSQL: {sql_select}")

        for row in self.talks_table.values():
            if (
                row.get("source_type") == source_type
                and row.get("source_id") == source_id
            ):
                return Talk(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    talk_type=TalkType(row["talk_type"]),
                    speaker_names=row["speaker_names"],
                    auto_tags=row["auto_tags"],
                )
        return None

    def update(self, talk: Talk) -> bool:
        """PostgreSQL-specific implementation of update"""
        sql_update = f"""
        UPDATE talks SET title = '{talk.title}', description = '{talk.description}', 
        updated_at = NOW() WHERE id = '{talk.id}'
        """

        if talk.id in self.talks_table:
            self.talks_table[talk.id].update(
                {
                    "title": talk.title,
                    "description": talk.description,
                    "updated_at": datetime.now(),
                }
            )
            print(f"   ✏️  PostgreSQL: {sql_update.strip()[:100]}...")
            return True
        else:
            print(f"   ❌ PostgreSQL: No rows to update for ID {talk.id}")
            return False


class FastAPIWebFramework:
    """
    Concrete FastAPI implementation for web framework

    This is RING 4 - it knows about specific web framework (FastAPI)
    and provides HTTP endpoints that delegate to Ring 3 controllers.
    """

    def __init__(self, controller):
        self.controller = controller
        self.routes = {
            "POST /api/talks": self._create_talk_route,
            "GET /api/talks": self._list_talks_route,
            "GET /api/talks/{id}": self._get_talk_route,
        }
        print("   🌐 FastAPI Framework: Initialized with routes")

    def _create_talk_route(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """FastAPI-specific route implementation"""
        print("   🛣️  FastAPI: POST /api/talks route called")

        # FastAPI-specific request parsing
        http_request = {
            "headers": request_data.get("headers", {}),
            "body": request_data.get("json", {}),
        }

        # Delegate to Ring 3 controller
        response = self.controller.create_talk_endpoint(http_request)

        # FastAPI-specific response formatting
        print(f"   📤 FastAPI: Returning {response['status_code']} response")
        return response

    def _list_talks_route(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """FastAPI-specific list route"""
        print("   🛣️  FastAPI: GET /api/talks route called")

        http_request = {"query_params": request_data.get("query_params", {})}

        return self.controller.list_talks_endpoint(http_request)

    def _get_talk_route(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """FastAPI-specific get route"""
        talk_id = request_data.get("path_params", {}).get("id")
        print(f"   🛣️  FastAPI: GET /api/talks/{talk_id} route called")

        # This would delegate to a GetTalkUseCase in a real implementation
        return {
            "status_code": 200,
            "body": {"message": f"Would retrieve talk {talk_id}"},
            "headers": {"Content-Type": "application/json"},
        }

    def handle_request(
        self, method: str, path: str, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """FastAPI request routing"""
        route_key = f"{method} {path}"
        print(f"   🔀 FastAPI: Routing {route_key}")

        if route_key in self.routes:
            return self.routes[route_key](request_data)
        else:
            return {
                "status_code": 404,
                "body": {"error": "Route not found"},
                "headers": {"Content-Type": "application/json"},
            }


class ExternalAPIClient:
    """
    Concrete implementation for external API integration

    This represents Ring 4 integration with external services
    like Sessionize, Meetup API, etc.
    """

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        print(f"   🌍 External API Client: Connected to {api_url}")

    def fetch_talks_from_sessionize(self, event_id: str) -> List[Dict[str, Any]]:
        """Simulate fetching talks from Sessionize API"""
        print(f"   📡 External API: Fetching talks from Sessionize event {event_id}")

        # Simulate HTTP request to external API
        mock_response = [
            {
                "id": "sessionize-001",
                "title": "Advanced Python Patterns",
                "description": "Deep dive into Python design patterns and best practices",
                "speakers": ["Sarah Python Expert"],
                "session_type": "Conference Session",
                "duration": 45,
            },
            {
                "id": "sessionize-002",
                "title": "FastAPI vs Django: Choose Your Framework",
                "description": "Comparison of modern Python web frameworks",
                "speakers": ["Mike Framework"],
                "session_type": "Panel Discussion",
                "duration": 60,
            },
        ]

        print(
            f"   📥 External API: Received {len(mock_response)} talks from Sessionize"
        )
        return mock_response

    def fetch_talks_from_meetup(self, group_id: str) -> List[Dict[str, Any]]:
        """Simulate fetching talks from Meetup API"""
        print(f"   📡 External API: Fetching events from Meetup group {group_id}")

        mock_response = [
            {
                "id": "meetup-001",
                "title": "Python Ireland Monthly Meetup",
                "description": "Monthly gathering of Python developers in Dublin",
                "hosts": ["Python Ireland Organizers"],
                "venue": "TechHub Dublin",
                "attendees": 85,
            }
        ]

        print(f"   📥 External API: Received {len(mock_response)} events from Meetup")
        return mock_response


def explore_ring4_structure():
    """Examine Ring 4 components and their characteristics"""
    print("🔍 Examining Ring 4 Structure:")
    print()

    print("📋 Ring 4 Components:")
    print("  - PostgreSQL Repository: Concrete database implementation")
    print("  - FastAPI Framework: Concrete web framework implementation")
    print("  - External API Clients: Integration with external services")
    print("  - File System: Configuration, logging, file storage")
    print("  - Network: HTTP clients, message queues, etc.")
    print()

    print("🏗️  Ring 4 Characteristics:")
    print("  - Contains framework-specific code (PostgreSQL, FastAPI)")
    print("  - Implements Ring 3 interfaces with concrete technology")
    print("  - Handles infrastructure concerns (connections, protocols)")
    print("  - Most volatile layer - changes when technology changes")
    print("  - Detailed implementation knowledge of external systems")
    print()


def test_postgresql_implementation():
    """Test the concrete PostgreSQL repository implementation"""
    print("🗄️  Testing PostgreSQL Repository Implementation (Ring 4):")
    print("=" * 55)

    # Create PostgreSQL repository with connection
    pg_repo = PostgreSQLTalkRepository("postgresql://localhost:5432/talks_db")

    print("1. Testing PostgreSQL Talk Creation:")

    # Create a talk using the concrete implementation
    sample_talk = Talk(
        id="temp-id",  # Will be overridden by database
        title="PostgreSQL in Production",
        description="Best practices for running PostgreSQL databases in production environments with high availability and performance optimization.",
        talk_type=TalkType.CONFERENCE_TALK,
        speaker_names=["Database Admin", "DevOps Engineer"],
        auto_tags=["PostgreSQL", "Database", "Production"],
        source_type="manual",
        source_id="pg-demo-001",
    )

    talk_id = pg_repo.save(sample_talk)
    print(f"   ✅ PostgreSQL saved talk with ID: {talk_id}")
    print()

    print("2. Testing PostgreSQL Talk Retrieval:")
    retrieved_talk = pg_repo.find_by_id(talk_id)
    if retrieved_talk:
        print(
            f"   📖 Retrieved: '{retrieved_talk.title}' by {retrieved_talk.speaker_names}"
        )
        print(f"   🏷️  Tags: {retrieved_talk.auto_tags}")
    print()

    print("3. Testing PostgreSQL Search:")
    search_results, total = pg_repo.search("PostgreSQL", {"limit": 10})
    print(f"   🔍 Search results: {len(search_results)} talks found")
    print()

    print("4. Testing PostgreSQL Source Lookup:")
    source_talk = pg_repo.find_by_source("manual", "pg-demo-001")
    if source_talk:
        print(f"   🎯 Found by source: '{source_talk.title}'")
    print()

    return pg_repo, talk_id


def test_fastapi_implementation():
    """Test the concrete FastAPI web framework implementation"""
    print("🌐 Testing FastAPI Web Framework Implementation (Ring 4):")
    print("=" * 55)

    # Set up full dependency chain for testing
    domain_service = TalkDomainService()
    pg_repo = PostgreSQLTalkRepository("postgresql://test:5432/talks_test")
    use_case = CreateTalkUseCase(pg_repo, domain_service)

    # Import Ring 3 controller (this would normally be in a separate module)
    class SimpleController:
        def __init__(self, create_use_case):
            self.create_use_case = create_use_case

        def create_talk_endpoint(self, request_data):
            try:
                body = request_data.get("body", {})
                talk_data = {
                    "id": body.get("id"),
                    "title": body.get("title"),
                    "description": body.get("description"),
                    "speaker_names": body.get("speakers", []),
                    "talk_type": body.get("type"),
                    "source_type": "web_api",
                    "source_id": body.get("id"),
                }
                talk_id = self.create_use_case.execute(talk_data)
                return {
                    "status_code": 201,
                    "body": {"message": "Talk created", "talk_id": talk_id},
                    "headers": {"Content-Type": "application/json"},
                }
            except Exception as e:
                return {
                    "status_code": 400,
                    "body": {"error": str(e)},
                    "headers": {"Content-Type": "application/json"},
                }

        def list_talks_endpoint(self, request_data):
            return {
                "status_code": 200,
                "body": {"talks": [], "message": "List endpoint"},
                "headers": {"Content-Type": "application/json"},
            }

    controller = SimpleController(use_case)
    fastapi_app = FastAPIWebFramework(controller)

    print("1. Testing FastAPI POST /api/talks:")

    request_data = {
        "headers": {"Content-Type": "application/json"},
        "json": {
            "id": "fastapi-001",
            "title": "Building APIs with FastAPI",
            "description": "Complete guide to building production-ready APIs with FastAPI framework",
            "speakers": ["FastAPI Expert"],
            "type": "tutorial",
        },
    }

    response = fastapi_app.handle_request("POST", "/api/talks", request_data)
    print(
        f"   📤 FastAPI Response: {response['status_code']} - {response['body']['message']}"
    )
    print()

    print("2. Testing FastAPI GET /api/talks:")

    list_request = {"query_params": {"q": "FastAPI", "limit": "10"}}

    response = fastapi_app.handle_request("GET", "/api/talks", list_request)
    print(
        f"   📤 FastAPI Response: {response['status_code']} - {response['body']['message']}"
    )
    print()

    print("3. Testing FastAPI GET /api/talks/{id}:")

    get_request = {"path_params": {"id": "fastapi-001"}}

    response = fastapi_app.handle_request("GET", "/api/talks/fastapi-001", get_request)
    print(
        f"   📤 FastAPI Response: {response['status_code']} - {response['body'].get('message', 'Response')}"
    )
    print()


def test_external_api_integration():
    """Test external API integration implementations"""
    print("🌍 Testing External API Integration (Ring 4):")
    print("=" * 45)

    # Create external API client
    api_client = ExternalAPIClient("https://sessionize.com/api", "test-api-key")

    print("1. Testing Sessionize API Integration:")
    sessionize_talks = api_client.fetch_talks_from_sessionize("pycon-ireland-2025")
    for talk in sessionize_talks:
        print(f"   📋 Sessionize Talk: '{talk['title']}' by {talk['speakers']}")
    print()

    print("2. Testing Meetup API Integration:")
    meetup_events = api_client.fetch_talks_from_meetup("python-ireland")
    for event in meetup_events:
        print(
            f"   📅 Meetup Event: '{event['title']}' - {event['attendees']} attendees"
        )
    print()

    # Demonstrate how external data would flow through the system
    print("3. Demonstrating Full Integration Flow:")
    print(
        "   📡 External API → Ring 4 Client → Ring 2 Use Case → Ring 3 Repository → Ring 4 Database"
    )
    print("   🔄 This shows how external data flows through all architectural rings")
    print()


def explore_ring4_boundaries():
    """Demonstrate Ring 4 responsibilities and boundaries"""
    print("🎯 Ring 4 Boundaries & Responsibilities:")
    print("=" * 45)

    print("✅ What Ring 4 DOES (Frameworks & Drivers):")
    print("  - Implement Ring 3 repository interfaces with concrete databases")
    print("  - Provide web framework implementations (FastAPI, Flask)")
    print("  - Handle external API integrations and HTTP clients")
    print("  - Manage database connections, transactions, migrations")
    print("  - Handle file system operations, logging, configuration")
    print("  - Implement message queues, caching, monitoring")
    print("  - Deal with framework-specific details and configurations")
    print()

    print("❌ What Ring 4 DOESN'T DO (Boundaries):")
    print("  - Contain business logic (that belongs in Ring 1 & Ring 2)")
    print("  - Make business decisions (Ring 2 responsibility)")
    print("  - Define interface contracts (Ring 3 responsibility)")
    print("  - Know about domain entities directly (uses DTOs)")
    print()

    print("🔄 Ring 4 Dependency Pattern:")
    print("  - Ring 4 IMPLEMENTS interfaces defined in Ring 3")
    print("  - Ring 4 NEVER calls inward to Ring 1, 2, or 3 directly")
    print("  - Ring 4 components can depend on each other")
    print("  - Ring 4 is injected into Ring 3 by dependency injection")
    print()

    print("🏗️  Ring 4 Technology Examples:")
    print("  - Databases: PostgreSQL, MongoDB, Redis")
    print("  - Web Frameworks: FastAPI, Flask, Django")
    print("  - External APIs: Sessionize, Meetup, GitHub API")
    print("  - Infrastructure: Docker, Kubernetes, AWS services")
    print("  - Monitoring: Prometheus, Grafana, logging systems")
    print()

    print("🧩 Testing Strategy:")
    print("  - Integration tests with real databases")
    print("  - API contract tests with external services")
    print("  - Infrastructure tests (Docker, deployment)")
    print("  - Performance tests under load")
    print()


def demonstrate_full_architecture():
    """Demonstrate how all 4 rings work together"""
    print("🎯 Complete Clean Architecture Demonstration:")
    print("=" * 50)

    print("🔗 All 4 Rings Working Together:")
    print()

    # Ring 4: Infrastructure setup
    print("Ring 4 Setup:")
    pg_repo = PostgreSQLTalkRepository("postgresql://prod:5432/talks")
    api_client = ExternalAPIClient("https://api.sessionize.com", "prod-key")
    print()

    # Ring 1: Domain services
    print("Ring 1 Setup:")
    domain_service = TalkDomainService()
    print("   ✅ Domain service created (pure business logic)")
    print()

    # Ring 2: Use cases
    print("Ring 2 Setup:")
    use_case = CreateTalkUseCase(pg_repo, domain_service)
    print("   ✅ Use case created with injected dependencies")
    print()

    # Ring 3: Controllers
    print("Ring 3 Setup:")

    class FullController:
        def __init__(self, create_use_case):
            self.create_use_case = create_use_case

        def create_talk_endpoint(self, request_data):
            body = request_data.get("body", {})
            talk_data = {
                "id": body.get("id"),
                "title": body.get("title"),
                "description": body.get("description"),
                "speaker_names": body.get("speakers", []),
                "talk_type": body.get("type"),
                "source_type": "web_api",
                "source_id": body.get("id"),
            }
            talk_id = self.create_use_case.execute(talk_data)
            return {"status_code": 201, "body": {"talk_id": talk_id}}

    controller = FullController(use_case)
    framework = FastAPIWebFramework(controller)
    print("   ✅ Controller and framework created")
    print()

    # Demonstrate full request flow
    print("🌊 Full Request Flow Demonstration:")
    request = {
        "headers": {"Content-Type": "application/json"},
        "json": {
            "id": "full-demo-001",
            "title": "Clean Architecture Mastery",
            "description": "Master Clean Architecture principles with hands-on examples in Python",
            "speakers": ["Architecture Expert"],
            "type": "workshop",
        },
    }

    print("   📥 Ring 4: FastAPI receives HTTP request")
    print("   ⬇️  Ring 4 → Ring 3: Framework delegates to controller")
    print("   ⬇️  Ring 3 → Ring 2: Controller calls use case")
    print("   ⬇️  Ring 2 → Ring 1: Use case applies domain logic")
    print("   ⬇️  Ring 2 → Ring 3 → Ring 4: Use case saves via repository to PostgreSQL")

    response = framework.handle_request("POST", "/api/talks", request)

    print("   ⬆️  Ring 4 → Ring 3: Repository returns ID")
    print("   ⬆️  Ring 3 → Ring 2: Use case returns ID")
    print("   ⬆️  Ring 2 → Ring 3: Controller formats response")
    print("   ⬆️  Ring 3 → Ring 4: Framework returns HTTP response")
    print("   📤 Ring 4: FastAPI sends HTTP response to client")
    print()

    print(
        f"   🎉 Final Result: {response['status_code']} - Talk ID: {response['body']['talk_id']}"
    )
    print()

    print("✨ Clean Architecture Success!")
    print("   🔒 Business logic protected in inner rings")
    print("   🔄 Dependencies point inward")
    print("   🧩 Each ring has single responsibility")
    print("   🛡️  Framework changes don't affect business logic")
    print("   🧪 Every layer is testable in isolation")


def main():
    """Main exploration function"""
    try:
        # Explore Ring 4 structure
        explore_ring4_structure()

        # Test PostgreSQL implementation
        test_postgresql_implementation()

        # Test FastAPI implementation
        test_fastapi_implementation()

        # Test external API integration
        test_external_api_integration()

        # Explain boundaries
        explore_ring4_boundaries()

        # Demonstrate full architecture
        demonstrate_full_architecture()

        print("🏗️ Ring 4 Summary - FRAMEWORKS & DRIVERS:")
        print("  ✅ Concrete implementations of all infrastructure concerns")
        print("  ✅ PostgreSQL repository implements Ring 3 interface")
        print("  ✅ FastAPI framework provides HTTP endpoints")
        print("  ✅ External API clients handle third-party integrations")
        print("  ✅ Most volatile layer - changes with technology choices")
        print("  ✅ Implements dependency inversion principle")
        print("  ✅ Enables testing with different implementations")
        print()
        print("🎯 CLEAN ARCHITECTURE COMPLETE!")
        print("  All 4 rings working together in harmony! 🎼")

    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
