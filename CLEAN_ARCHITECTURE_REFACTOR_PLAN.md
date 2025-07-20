# Clean Architecture Refactor Plan

## Overview

This plan outlines a 3-phase refactor to improve Clean Architecture adherence in the Python Ireland Talk Database project. Each phase builds on the previous one, allowing for incremental improvements and learning.

**Current Architecture Score: 7/10**
**Target Architecture Score: 9/10**

## Phase 1: Foundation Cleanup (2-3 days)

_Low Risk, High Value - Quick wins that improve clarity_

### 1.1 Rename and Reorganize Packages

#### Current Issues:

- `backend/domain/models.py` contains DTOs, not domain entities
- Business logic scattered in `lib/engine/data_pipeline.py` (violates Entities Layer - Ring 1)
- Naming conventions don't match Clean Architecture

#### Actions:

**Step 1: Create proper Clean Architecture structure**

```bash
# Entities Layer (Ring 1: Enterprise Business Rules)
mkdir -p backend/domain/entities     # Domain entities
mkdir -p backend/domain/services     # Domain services (business logic)

# Use Cases Layer (Ring 2: Application Business Rules)
mkdir -p backend/application/use_cases   # Use cases

# Interface Adapters Layer (Ring 3)
mkdir -p backend/contracts/dtos      # DTOs and interfaces
```

**Step 2: Move and rename files**

```bash
# Move DTOs to Interface Adapters Layer (Ring 3)
mv backend/domain/models.py backend/contracts/dtos.py

# Create Entities Layer (Ring 1) - domain entities
touch backend/domain/entities/__init__.py
touch backend/domain/entities/talk.py
touch backend/domain/entities/taxonomy.py

# Create Use Cases Layer (Ring 2) - application business rules
touch backend/application/__init__.py
touch backend/application/use_cases/__init__.py
```

**Step 3: Extract business logic from data_pipeline.py**

- Create `backend/domain/services/talk_domain_service.py` (Entities Layer - Ring 1)
- Move pure business logic (validation, transformation rules)
- Keep data_pipeline.py as Frameworks & Drivers Layer (Ring 4 - infrastructure coordination)

### 1.2 Update Import Statements

**Files to update:**

- `backend/services/talk_service.py` → import from `backend/contracts/dtos`
- `backend/api/routers/*.py` → import from `backend/contracts/dtos`
- All test files → update imports

### 1.3 Create Domain Entities (Simple Start)

**backend/domain/entities/talk.py:**

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class TalkType(Enum):
    CONFERENCE_TALK = "conference_talk"
    LIGHTNING_TALK = "lightning_talk"
    WORKSHOP = "workshop"
    KEYNOTE = "keynote"

@dataclass
class Talk:
    """Domain entity representing a talk"""
    id: str
    title: str
    description: str
    talk_type: TalkType
    speaker_names: List[str]

    def is_valid(self) -> bool:
        """Business rule: a talk must have a title and at least one speaker"""
        return bool(self.title.strip()) and len(self.speaker_names) > 0

    def get_display_title(self) -> str:
        """Business rule: format title for display"""
        return self.title.strip().title()
```

### 1.4 Extract Business Logic

**backend/domain/services/talk_domain_service.py:**

```python
from typing import Dict, Any, List
from backend.domain.entities.talk import Talk, TalkType

class TalkDomainService:
    """Pure business logic for talks - Entities Layer (Ring 1)"""

    @staticmethod
    def extract_auto_tags(title: str, description: str) -> List[str]:
        """Business rule: extract tags from content"""
        # Move tag extraction logic here from data_pipeline.py
        pass

    @staticmethod
    def determine_talk_type(session_data: Dict[str, Any]) -> TalkType:
        """Business rule: determine talk type from session data"""
        # Move type determination logic here
        pass

    @staticmethod
    def validate_talk_data(talk_data: Dict[str, Any]) -> List[str]:
        """Business rule: validate talk data"""
        errors = []
        if not talk_data.get('title', '').strip():
            errors.append("Title is required")
        if not talk_data.get('speaker_names'):
            errors.append("At least one speaker is required")
        return errors
```

### 1.5 Success Criteria for Phase 1

- [x] All files in correct directories according to Clean Architecture layers
- [x] Import statements follow dependency rules (inner layers don't import from outer layers)
- [x] Business logic extracted from data_pipeline.py to Entities Layer
- [x] Simple domain entities created with basic business rules
- [x] All tests still pass
- [x] Architecture score improves to 8/10

---

## Phase 2: Rich Domain Entities (3-5 days)

_Medium Risk, Very High Value - Where Clean Architecture really shines_

### 2.1 Enhance Domain Entities (Entities Layer - Ring 1)

**backend/domain/entities/talk.py (Enhanced):**

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

@dataclass
class Talk:
    """Rich domain entity with business behavior"""
    id: str
    title: str
    description: str
    talk_type: TalkType
    speaker_names: List[str]
    auto_tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    type_specific_data: Dict[str, Any] = field(default_factory=dict)

    # Business methods
    def is_valid(self) -> bool:
        """Comprehensive validation"""
        return (
            bool(self.title.strip()) and
            len(self.speaker_names) > 0 and
            all(name.strip() for name in self.speaker_names)
        )

    def add_speaker(self, speaker_name: str) -> None:
        """Business rule: add speaker with validation"""
        if speaker_name.strip() and speaker_name not in self.speaker_names:
            self.speaker_names.append(speaker_name.strip())

    def update_content(self, title: str = None, description: str = None) -> None:
        """Business rule: update content and refresh auto-tags"""
        if title is not None:
            self.title = title.strip()
        if description is not None:
            self.description = description.strip()
        self.updated_at = datetime.now()
        # Could trigger auto-tag refresh

    def has_keyword(self, keyword: str) -> bool:
        """Business rule: search for keyword in talk content"""
        search_text = f"{self.title} {self.description}".lower()
        return keyword.lower() in search_text

    def is_by_speaker(self, speaker_name: str) -> bool:
        """Business rule: check if talk is by specific speaker"""
        return any(
            speaker_name.lower() in name.lower()
            for name in self.speaker_names
        )

    def get_duration_minutes(self) -> Optional[int]:
        """Business rule: extract duration from type-specific data"""
        if 'duration' in self.type_specific_data:
            return self.type_specific_data['duration']
        # Default durations by type
        defaults = {
            TalkType.LIGHTNING_TALK: 5,
            TalkType.CONFERENCE_TALK: 30,
            TalkType.WORKSHOP: 180,
            TalkType.KEYNOTE: 45
        }
        return defaults.get(self.talk_type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'talk_type': self.talk_type.value,
            'speaker_names': self.speaker_names,
            'auto_tags': self.auto_tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'type_specific_data': self.type_specific_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Talk':
        """Create from dictionary (from persistence)"""
        # Parse datetime fields
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])

        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])

        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            talk_type=TalkType(data['talk_type']),
            speaker_names=data.get('speaker_names', []),
            auto_tags=data.get('auto_tags', []),
            created_at=created_at,
            updated_at=updated_at,
            source_id=data.get('source_id'),
            source_type=data.get('source_type'),
            type_specific_data=data.get('type_specific_data', {})
        )
```

### 2.2 Create Value Objects

**backend/domain/entities/taxonomy.py:**

```python
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

    def add_value(self, value: str, description: str = "", color: str = "") -> TaxonomyValue:
        """Business rule: add new taxonomy value"""
        # Check for duplicates
        if any(v.value.lower() == value.lower() for v in self.values):
            raise ValueError(f"Value '{value}' already exists in taxonomy '{self.name}'")

        # Generate new ID (in real implementation, this would come from persistence)
        new_id = max((v.id for v in self.values), default=0) + 1
        new_value = TaxonomyValue(new_id, value.strip(), description.strip(), color)
        self.values.append(new_value)
        return new_value

    def find_value_by_name(self, value_name: str) -> Optional[TaxonomyValue]:
        """Business rule: find value by name (case-insensitive)"""
        return next(
            (v for v in self.values if v.value.lower() == value_name.lower()),
            None
        )
```

### 2.3 Create Use Cases (Use Cases Layer - Ring 2)

**backend/application/use_cases/create_talk.py:**

```python
from typing import Dict, Any
from backend.domain.entities.talk import Talk
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.contracts.repositories import TalkRepository

class CreateTalkUseCase:
    """Use case for creating a new talk - Use Cases Layer (Ring 2)"""

    def __init__(self, talk_repository: TalkRepository, domain_service: TalkDomainService):
        self.talk_repository = talk_repository
        self.domain_service = domain_service

    def execute(self, talk_data: Dict[str, Any]) -> str:
        """Create a new talk with business validation"""

        # Validate using domain service
        errors = self.domain_service.validate_talk_data(talk_data)
        if errors:
            raise ValueError(f"Invalid talk data: {', '.join(errors)}")

        # Create domain entity
        talk = Talk.from_dict(talk_data)

        # Apply business rules
        if not talk.is_valid():
            raise ValueError("Talk does not meet business requirements")

        # Enhance with auto-tags
        auto_tags = self.domain_service.extract_auto_tags(talk.title, talk.description)
        talk.auto_tags = auto_tags

        # Persist through repository
        return self.talk_repository.save(talk)
```

### 2.4 Define Repository Interfaces (Interface Adapters Layer - Ring 3)

**backend/contracts/repositories.py:**

```python
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
```

### 2.5 Update Service Layer (Use Cases Layer - Ring 2)

**Update `backend/services/talk_service.py`:**

- Change from direct database calls to use cases
- Inject repositories and domain services
- Focus on orchestration, not business logic

### 2.6 Success Criteria for Phase 2

- [ ] Rich domain entities with business behavior (Entities Layer)
- [ ] Use cases handle application logic (Use Cases Layer)
- [ ] Repository interfaces define contracts (Interface Adapters Layer)
- [ ] Service layer uses use cases, not direct database access
- [ ] Business logic centralized in Entities Layer
- [ ] All tests still pass
- [ ] Architecture score improves to 8.5/10

---

## Phase 3: Repository Pattern (2-3 days)

_Higher Risk, Learning Value - Explore full Clean Architecture_

### 3.1 Implement Repository Pattern (Frameworks & Drivers Layer - Ring 4)

**backend/infrastructure/repositories/postgres_talk_repository.py:**

```python
from typing import List, Optional, Dict, Any, Tuple
from backend.contracts.repositories import TalkRepository
from backend.domain.entities.talk import Talk
from backend.database.postgres_client import PostgresClient

class PostgresTalkRepository(TalkRepository):
    """Concrete implementation of TalkRepository using Postgres"""

    def __init__(self, postgres_client: PostgresClient):
        self.db = postgres_client

    def save(self, talk: Talk) -> str:
        """Save talk entity to database"""
        # Convert domain entity to database format
        db_data = self._to_database_format(talk)
        return self.db.upsert_talk(db_data)

    def find_by_id(self, talk_id: str) -> Optional[Talk]:
        """Find talk by ID and convert to domain entity"""
        db_data = self.db.get_talk(talk_id)
        if db_data:
            return self._to_domain_entity(db_data)
        return None

    def find_by_source(self, source_id: str, source_type: str) -> Optional[Talk]:
        """Find talk by source and convert to domain entity"""
        db_data = self.db.get_talk_by_source(source_id, source_type)
        if db_data:
            return self._to_domain_entity(db_data)
        return None

    def search(self, query: str, filters: Dict[str, Any]) -> Tuple[List[Talk], int]:
        """Search talks and convert to domain entities"""
        db_results, total = self.db.search_talks(
            query=query,
            **filters
        )

        talks = [self._to_domain_entity(db_data) for db_data in db_results]
        return talks, total

    def _to_database_format(self, talk: Talk) -> Dict[str, Any]:
        """Convert domain entity to database format"""
        return talk.to_dict()

    def _to_domain_entity(self, db_data: Dict[str, Any]) -> Talk:
        """Convert database data to domain entity"""
        return Talk.from_dict(db_data)
```

### 3.2 Dependency Injection Setup (Frameworks & Drivers Layer - Ring 4)

**backend/infrastructure/di_container.py:**

```python
from backend.services.talk_service import TalkService
from backend.application.use_cases.create_talk import CreateTalkUseCase
from backend.domain.services.talk_domain_service import TalkDomainService
from backend.infrastructure.repositories.postgres_talk_repository import PostgresTalkRepository
from backend.database.postgres_client import PostgresClient
from backend.core.config import settings

class DIContainer:
    """Dependency injection container"""

    def __init__(self):
        # Infrastructure layer
        self._postgres_client = PostgresClient(settings.database_url)

        # Repository implementations
        self._talk_repository = PostgresTalkRepository(self._postgres_client)

        # Domain services
        self._talk_domain_service = TalkDomainService()

        # Use cases
        self._create_talk_use_case = CreateTalkUseCase(
            self._talk_repository,
            self._talk_domain_service
        )

    def get_talk_service(self) -> TalkService:
        """Get configured talk service"""
        return TalkService(
            create_talk_use_case=self._create_talk_use_case,
            talk_repository=self._talk_repository
        )

    def get_postgres_client(self) -> PostgresClient:
        """Get postgres client for direct access if needed"""
        return self._postgres_client
```

### 3.3 Update API Layer (Interface Adapters Layer - Ring 3)

**backend/api/routers/talks.py:**

```python
from fastapi import APIRouter, Depends
from backend.infrastructure.di_container import DIContainer
from backend.services.talk_service import TalkService

router = APIRouter()

# Dependency injection
def get_di_container() -> DIContainer:
    return DIContainer()

def get_talk_service(container: DIContainer = Depends(get_di_container)) -> TalkService:
    return container.get_talk_service()

@router.post("/talks")
async def create_talk(
    talk_data: dict,
    talk_service: TalkService = Depends(get_talk_service)
):
    """Create a new talk"""
    return {"id": talk_service.create_talk(talk_data)}
```

### 3.4 Advanced Features

**Domain Events (Optional):**

```python
# backend/domain/events/talk_events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TalkCreated:
    talk_id: str
    title: str
    created_at: datetime

@dataclass
class TalkUpdated:
    talk_id: str
    updated_at: datetime
```

### 3.5 Success Criteria for Phase 3

- [ ] Repository pattern fully implemented (Frameworks & Drivers Layer)
- [ ] Dependency injection container working (Frameworks & Drivers Layer)
- [ ] Clean separation between layers maintained
- [ ] Domain entities are the primary data model (Entities Layer)
- [ ] Infrastructure details hidden behind interfaces (Interface Adapters Layer)
- [ ] All tests still pass
- [ ] Architecture score reaches 9/10

---

## Testing Strategy

### Phase 1 Tests

- Update existing tests to use new import paths
- Add tests for domain services (Entities Layer)
- Verify business logic extraction

### Phase 2 Tests

- Test rich domain entities with business methods (Entities Layer)
- Test use cases independently of infrastructure (Use Cases Layer)
- Mock repository interfaces (Interface Adapters Layer)

### Phase 3 Tests

- Test repository implementations (Frameworks & Drivers Layer)
- Integration tests with dependency injection
- End-to-end tests still pass

## Migration Strategy

### Each Phase:

1. **Create new structure alongside old**
2. **Gradually migrate functionality**
3. **Update tests incrementally**
4. **Remove old code only when new is proven**
5. **Run full test suite after each change**

### Rollback Plan:

- Each phase can be rolled back independently
- Keep old code until new is fully proven
- Git branches for each phase

## Learning Objectives

### Phase 1: Entities & Use Cases Foundation

- Understand Clean Architecture layer separation
- Learn proper dependency direction (inner layers independent of outer layers)
- Practice extracting business logic to Entities Layer

### Phase 2: Rich Domain Design

- Master domain-driven design principles (Entities Layer)
- Understand use case pattern (Use Cases Layer)
- Learn repository interface design (Interface Adapters Layer)

### Phase 3: Full Clean Architecture

- Master dependency injection (Frameworks & Drivers Layer)
- Understand infrastructure abstraction
- Learn event-driven architecture basics

## Expected Benefits

### Phase 1:

- Clearer code organization
- Better testability
- Reduced coupling

### Phase 2:

- Rich business behavior in entities
- Better domain modeling
- More maintainable code

### Phase 3:

- Complete framework independence
- Maximum testability
- Clean separation of concerns

## Time Investment

- **Phase 1:** 2-3 days (quick wins)
- **Phase 2:** 3-5 days (core value)
- **Phase 3:** 2-3 days (exploration)
- **Total:** 7-11 days

## Risk Assessment

- **Phase 1:** Low risk, high value
- **Phase 2:** Medium risk, very high value
- **Phase 3:** Higher risk, learning value

This plan allows for incremental progress while learning Clean Architecture principles deeply through hands-on implementation.

---

## Architecture Score Breakdown

### Why Phase 3 Reaches 9/10 (Not 10/10)

**Current State After Phase 3:**

- ✅ **Entities Layer (Ring 1):** Rich domain entities with business behavior
- ✅ **Use Cases Layer (Ring 2):** Application-specific business rules and orchestration
- ✅ **Interface Adapters Layer (Ring 3):** Clean separation of controllers, repositories, DTOs
- ✅ **Frameworks & Drivers Layer (Ring 4):** Infrastructure isolated behind interfaces
- ✅ **Dependency Rule:** All dependencies point inward
- ✅ **Testability:** Each layer can be tested independently
- ✅ **Framework Independence:** Core business logic doesn't depend on external frameworks

**Missing for 10/10:**

### To Reach 10/10: Advanced Clean Architecture Patterns

#### 1. **Domain Events & Event-Driven Architecture**

```python
# backend/domain/events/domain_event.py
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import List

class DomainEvent(ABC):
    """Base class for all domain events"""
    occurred_at: datetime

@dataclass
class TalkCreated(DomainEvent):
    talk_id: str
    title: str
    speaker_names: List[str]
    occurred_at: datetime

@dataclass
class TalkTagsUpdated(DomainEvent):
    talk_id: str
    old_tags: List[str]
    new_tags: List[str]
    occurred_at: datetime

# Rich entities that emit events
class Talk:
    def __init__(self, ...):
        self._domain_events: List[DomainEvent] = []

    def add_tags(self, new_tags: List[str]) -> None:
        """Business rule with event emission"""
        old_tags = self.auto_tags.copy()
        self.auto_tags.extend(new_tags)

        # Emit domain event
        self._domain_events.append(
            TalkTagsUpdated(
                talk_id=self.id,
                old_tags=old_tags,
                new_tags=self.auto_tags,
                occurred_at=datetime.now()
            )
        )

    def get_domain_events(self) -> List[DomainEvent]:
        """Get uncommitted domain events"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

#### 2. **Aggregate Roots & Domain-Driven Design Patterns**

```python
# backend/domain/aggregates/talk_aggregate.py
from typing import List, Optional
from backend.domain.entities.talk import Talk
from backend.domain.entities.taxonomy import TaxonomyValue
from backend.domain.events.domain_event import DomainEvent

class TalkAggregate:
    """Aggregate root ensuring consistency across related entities"""

    def __init__(self, talk: Talk, taxonomy_values: List[TaxonomyValue] = None):
        self.talk = talk
        self._taxonomy_values = taxonomy_values or []
        self._domain_events: List[DomainEvent] = []

    def apply_taxonomy_rules(self) -> None:
        """Complex business rule spanning multiple entities"""
        # Example: Auto-assign difficulty based on content analysis
        if self.talk.has_keyword("advanced") or self.talk.has_keyword("expert"):
            self._assign_taxonomy_value("difficulty", "advanced")
        elif self.talk.has_keyword("beginner") or self.talk.has_keyword("intro"):
            self._assign_taxonomy_value("difficulty", "beginner")
        else:
            self._assign_taxonomy_value("difficulty", "intermediate")

    def _assign_taxonomy_value(self, taxonomy_name: str, value: str) -> None:
        """Business rule: assign taxonomy value with validation"""
        # Complex business logic ensuring data consistency
        pass
```

#### 3. **Command Query Responsibility Segregation (CQRS)**

```python
# backend/application/commands/create_talk_command.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CreateTalkCommand:
    """Command for creating a talk"""
    title: str
    description: str
    speaker_names: List[str]
    talk_type: str
    source_data: Dict[str, Any]

# backend/application/queries/talk_search_query.py
@dataclass
class TalkSearchQuery:
    """Query for searching talks"""
    text_query: Optional[str] = None
    taxonomy_filters: Dict[str, List[str]] = None
    speaker_filter: Optional[str] = None
    limit: int = 20
    offset: int = 0

# Separate read and write models
class TalkCommandHandler:
    """Handles commands (writes)"""
    def handle(self, command: CreateTalkCommand) -> str:
        # Complex business logic for creating talks
        pass

class TalkQueryHandler:
    """Handles queries (reads) - optimized for performance"""
    def handle(self, query: TalkSearchQuery) -> TalkSearchResult:
        # Optimized read operations, possibly from read-optimized store
        pass
```

#### 4. **Specification Pattern for Complex Business Rules**

```python
# backend/domain/specifications/talk_specifications.py
from abc import ABC, abstractmethod
from backend.domain.entities.talk import Talk

class Specification(ABC):
    """Base specification for business rules"""

    @abstractmethod
    def is_satisfied_by(self, talk: Talk) -> bool:
        pass

    def and_(self, other: 'Specification') -> 'AndSpecification':
        return AndSpecification(self, other)

    def or_(self, other: 'Specification') -> 'OrSpecification':
        return OrSpecification(self, other)

class TalkIsEligibleForFeatured(Specification):
    """Business rule: what makes a talk eligible for featuring"""

    def is_satisfied_by(self, talk: Talk) -> bool:
        return (
            talk.is_valid() and
            len(talk.speaker_names) > 0 and
            talk.get_duration_minutes() >= 20 and
            len(talk.description) > 100
        )

class TalkIsByExpertSpeaker(Specification):
    """Business rule: is this talk by an expert speaker"""

    def __init__(self, expert_speakers: List[str]):
        self.expert_speakers = expert_speakers

    def is_satisfied_by(self, talk: Talk) -> bool:
        return any(
            speaker in self.expert_speakers
            for speaker in talk.speaker_names
        )

# Usage in domain services
class TalkDomainService:
    def get_featured_talks(self, talks: List[Talk]) -> List[Talk]:
        featured_spec = TalkIsEligibleForFeatured()
        return [talk for talk in talks if featured_spec.is_satisfied_by(talk)]
```

#### 5. **Hexagonal Architecture Ports & Adapters**

```python
# backend/ports/notification_port.py (defined in Use Cases Layer)
from abc import ABC, abstractmethod

class NotificationPort(ABC):
    """Port for sending notifications"""

    @abstractmethod
    async def send_talk_created_notification(self, talk_id: str, title: str) -> bool:
        pass

# backend/adapters/email_notification_adapter.py (Frameworks & Drivers Layer)
class EmailNotificationAdapter(NotificationPort):
    """Email implementation of notification port"""

    async def send_talk_created_notification(self, talk_id: str, title: str) -> bool:
        # Send email notification
        pass

# backend/adapters/slack_notification_adapter.py (Frameworks & Drivers Layer)
class SlackNotificationAdapter(NotificationPort):
    """Slack implementation of notification port"""

    async def send_talk_created_notification(self, talk_id: str, title: str) -> bool:
        # Send Slack notification
        pass
```

#### 6. **Advanced Testing Strategies**

```python
# tests/acceptance/test_talk_creation_journey.py
class TestTalkCreationJourney:
    """Acceptance tests using domain language"""

    def test_expert_speaker_talk_gets_featured_automatically(self):
        # Given an expert speaker
        expert_speaker = "Uncle Bob"

        # When they create a comprehensive talk
        talk_data = {
            "title": "Clean Architecture in Practice",
            "description": "A comprehensive guide to implementing clean architecture...",
            "speaker_names": [expert_speaker],
            "talk_type": "conference_talk"
        }

        # Then the talk should be automatically featured
        talk_id = self.create_talk_use_case.execute(talk_data)
        talk = self.talk_repository.find_by_id(talk_id)

        assert self.featured_talk_spec.is_satisfied_by(talk)

# tests/architecture/test_dependency_rules.py
class TestArchitectureCompliance:
    """Tests that enforce architectural rules"""

    def test_entities_layer_has_no_outward_dependencies(self):
        """Entities Layer should not import from outer layers"""
        # Static analysis to ensure dependency rule compliance
        pass

    def test_use_cases_only_depend_on_entities_and_interfaces(self):
        """Use Cases Layer should only depend on inner layers"""
        pass
```

### **10/10 Architecture Characteristics:**

1. **✅ Rich Domain Model** (entities with behavior)
2. **✅ Use Case Driven** (application business rules)
3. **✅ Infrastructure Independence** (framework agnostic)
4. **✅ Testable Architecture** (dependency injection)
5. **✅ Interface Segregation** (clean contracts)
6. **🔶 Domain Events** (decoupled communication)
7. **🔶 CQRS** (optimized read/write separation)
8. **🔶 Specification Pattern** (composable business rules)
9. **🔶 Hexagonal Ports** (true framework independence)
10. **🔶 Architecture Testing** (automated compliance verification)

### **Pragmatic Decision: Why Stop at 9/10**

**Reasons to stick with 9/10 for this project:**

1. **Diminishing Returns:** Items 6-10 add complexity without proportional business value
2. **Team Size:** These patterns shine in larger teams/systems
3. **Domain Complexity:** Your domain isn't complex enough to warrant CQRS/Event Sourcing
4. **Maintenance Overhead:** Advanced patterns require more expertise to maintain

**When to go to 10/10:**

- Large team (8+ developers)
- Complex business domain with many invariants
- High-performance requirements
- Event-driven integrations with external systems
- Regulatory/audit requirements for change tracking

### **Recommended Path:**

**Phase 3 Achievement: 9/10**

- Excellent Clean Architecture implementation
- All major benefits realized
- Maintainable and extensible
- Perfect for your project scope

**Future Evolution to 10/10:**

- Add domain events when you need decoupled notifications
- Implement CQRS if read/write performance becomes an issue
- Use specifications when business rules become more complex
