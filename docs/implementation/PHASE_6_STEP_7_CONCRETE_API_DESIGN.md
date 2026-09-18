# Phase 6 — Step 7
# Concrete API Design

**Status:** DRAFT
**Phase:** 6 — Posting
**Step:** 7 — Platform Implementation
**Document:** `docs/implementation/PHASE_6_STEP_7_CONCRETE_API_DESIGN.md`

---

## 1. Purpose

This document defines the concrete Python-level API boundaries for the Platform Posting implementation.

The purpose of this step is to translate the approved semantic Posting architecture into explicit implementation contracts without prematurely prescribing implementation mechanisms.

The design progression is:

```text
Semantic Contract
        ↓
Python API Contract
        ↓
Implementation
```

This document defines:

* public Posting entry points;
* Posting Engine boundary;
* Posting Context;
* Posting Handler contract;
* Handler resolution;
* Movement and MovementSet representations;
* Movement validation;
* Register Posting Contract;
* persistent-result coordination boundary;
* Posting result and error semantics;
* event publication boundary;
* runtime composition requirements;
* Unpost and Repost API semantics.

This document does **not** implement the described APIs.

---

# 2. Design Principles

The concrete API MUST preserve the architectural decisions already established by the Posting Architecture and Phase 6 Steps 1–6.

The implementation MUST preserve the following principles.

### 2.1 Posting is an explicit accounting operation

Posting is not equivalent to saving a document or updating arbitrary runtime state.

### 2.2 Public API and Posting Engine are distinct boundaries

The Public Posting API provides the application-facing entry boundary. The Posting Engine owns Posting orchestration. The Public API MUST NOT duplicate Posting lifecycle logic.

### 2.3 Posting Handler owns document-specific accounting semantics

A Posting Handler transforms the semantic state of a source Document into a complete `MovementSet`.

A Handler MUST NOT own persistence, transactions, Persistence Scope, event publication, dependency management, register storage, or totals management.

### 2.4 Register owns register-specific semantics

The Register Posting Contract defines whether generated Movements satisfy the requirements of a target Register.

### 2.5 Persistence remains behind an explicit boundary

Posting MUST NOT depend directly on Storage Providers, databases, SQL, or physical transaction APIs.

### 2.6 Semantic results are more important than implementation mechanisms

The API MUST preserve the distinctions between:

```text
Success
Failure
Indeterminate
```

without requiring those distinctions to map one-to-one onto concrete exception classes.

---

# 3. Package and Module Layout

The initial implementation SHOULD use the existing Platform package structure.

Proposed layout:

```text
src/accore/platform/
├── posting/
│   ├── __init__.py
│   ├── api.py
│   ├── context.py
│   ├── engine.py
│   ├── errors.py
│   ├── handlers.py
│   ├── movement.py
│   ├── result.py
│   ├── validation.py
│   └── events.py
│
└── registers/
    ├── __init__.py
    ├── contracts.py
    ├── movement.py
    └── validation.py
```

The exact module split MAY be adjusted during implementation if an existing Platform convention provides a better location.

The dependency direction SHOULD remain:

```text
posting
    ↓
registers
```

Register infrastructure MUST NOT depend on Posting infrastructure merely to represent or validate a Movement.

---

# 4. Public Posting API

The Public Posting API is the application-level entry boundary for standard Posting operations.

It provides:

* Post;
* Unpost;
* Repost.

A minimal concrete interface is:

```python
class PostingAPI(Protocol):
    def post(
        self,
        document: ObjectInstance,
    ) -> PostingResult:
        ...

    def unpost(
        self,
        document: ObjectInstance,
    ) -> PostingResult:
        ...

    def repost(
        self,
        document: ObjectInstance,
    ) -> PostingResult:
        ...
```

The exact source-document representation remains subject to the existing runtime/application architecture. At the current repository state, `ObjectInstance` is the existing generic runtime representation carrying explicit object identity and runtime object type.

The API MUST preserve explicit source Document identity.

The API MUST NOT:

* generate Movements;
* construct Posting Contexts;
* resolve Handlers directly;
* validate Movements directly;
* persist register effects directly;
* control transactions;
* access Storage Providers directly.

The API delegates operation execution to the Posting Engine.

---

# 5. Posting Engine

The Posting Engine is the central orchestration boundary.

A minimal concrete contract is:

```python
class PostingEngine(Protocol):
    def post(
        self,
        document: ObjectInstance,
    ) -> PostingResult:
        ...

    def unpost(
        self,
        document: ObjectInstance,
    ) -> PostingResult:
        ...

    def repost(
        self,
        document: ObjectInstance,
    ) -> PostingResult:
        ...
```

The Posting Engine owns the lifecycle:

```text
Posting Request
        ↓
Posting Preconditions
        ↓
Handler Resolution
        ↓
Posting Context
        ↓
Handler Execution
        ↓
MovementSet
        ↓
Movement Validation
        ↓
Required Persistent Result
        ↓
Logical Completion
        ↓
Events
```

The Posting Engine MUST NOT expose physical transaction or storage operations as part of its public contract.

---

# 6. Posting Operation

The Posting Engine treats Post, Unpost, and Repost as distinct operations.

They MUST NOT be represented as an unrestricted flag such as `post(document, force=True)` when that flag changes the semantic operation.

The operation identity is explicit:

```text
Post
Unpost
Repost
```

---

# 7. Posting Context

`PostingContext` is the controlled runtime capability boundary supplied to a Posting Handler.

A concrete initial representation MAY be:

```python
@dataclass(frozen=True, slots=True)
class PostingContext:
    document: ObjectInstance
    metadata: PublishedMetadataView
    services: PostingServices
    clock: PostingClock
```

`PostingServices` is a controlled capability aggregate whose concrete members are defined by the capabilities required by the implemented Posting vertical slice. It MUST expose only explicitly declared Posting capabilities.

For the initial platform implementation, the aggregate MAY contain only capabilities that are actually required by the first concrete Posting Handler. If no additional Handler capability is required, the aggregate MAY remain empty while preserving the explicit boundary.

`PostingClock` is an explicit capability and is therefore not hidden inside `PostingServices`.

The context MUST NOT become a generic service locator.

Handlers MUST receive only the capabilities required by the Posting Architecture.

The Posting Engine owns Context creation.

A Handler MUST NOT construct its own Context, replace it, retain it after Posting completes, or use uncontrolled global runtime state as an implicit dependency source.

---

# 8. Posting Services Boundary

The `services` component represents explicitly supplied Posting capabilities.

It MUST NOT be an unrestricted container for arbitrary application services.

A service SHOULD be added only when the Handler genuinely requires it, its use belongs to Posting semantics, its lifetime is compatible with Posting, and exposing it does not move persistence or orchestration responsibility into the Handler.

Raw database connections, Storage Providers, transaction controllers, Persistence Scope controllers, event buses, and arbitrary dependency containers MUST NOT be exposed merely for convenience.

---

# 9. Posting Clock

Posting semantics may require controlled temporal input.

A concrete boundary MAY be:

```python
class PostingClock(Protocol):
    def now(self) -> datetime:
        ...
```

The exact temporal API is implementation-dependent.

The architectural requirement is:

```text
Posting Time
    ↓
explicit Posting Context input
```

rather than uncontrolled calls to system time from a Handler.

---

# 10. Posting Handler

The Posting Handler is the document-specific accounting transformation boundary.

The concrete contract is:

```python
class PostingHandler(Protocol):
    def post(
        self,
        context: PostingContext,
    ) -> MovementSet:
        ...
```

The Handler MUST read the source Document through the supplied Context, apply document-specific accounting semantics, generate Movements, and return one complete `MovementSet`.

The Handler MUST NOT persist Movements, remove previous Movements, control transactions or Persistence Scope, publish lifecycle events, update dependency state directly, update register storage directly, or update totals directly.

Business-specific validation MAY be performed by the Handler when intrinsic to the document's accounting semantics. Movement and Register validation remains outside Handler ownership.

---

# 11. Posting Handler Resolution

Handler resolution is an explicit platform dependency.

The concrete contract is:

```python
class PostingHandlerResolver(Protocol):
    def resolve(
        self,
        document: ObjectInstance,
    ) -> PostingHandler:
        ...
```

Resolution MAY use runtime object type identity, metadata identity, registered Handler configuration, or another explicit platform-level mapping.

The resolver MUST NOT require Handlers to discover themselves through uncontrolled global state and MUST NOT become a generic service locator.

A resolution failure MUST produce a Posting failure.

---

# 12. Handler Registration

Handler registration is an application/platform composition concern.

A registration mechanism MAY use an explicit mapping such as:

```python
handler_registry.register(
    object_type_identity,
    handler,
)
```

The concrete registry API is not normative at this stage.

The important requirement is that Handler resolution remains explicit and inspectable.

---

# 13. Movement

`Movement` represents a universal accounting fact generated by Posting and accepted by Register Architecture.

The concrete representation SHOULD be an immutable value object.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class Movement:
    identity: Identifier
    source_document_identity: Identifier
    register_identity: Identifier
    movement_type: MovementType
    dimensions: MovementDimensions
    resources: MovementResources
    attributes: MovementAttributes
    accounting_time: datetime | None
```

This is a proposed concrete shape, not a requirement that every field be implemented exactly as shown.

Temporal representation remains subject to the applicable Register Posting Contract; concrete Movement Type representation remains implementation-defined; dimensions/resources/attributes may use existing project abstractions when available.

`Movement` MUST NOT be owned by the persistence layer.

The existing persistence placeholder `Movement = Any` is expected to be replaced once the concrete Register/Posting Movement boundary is implemented.

---

# 14. Movement Identity

Movement identity uses the existing `Identifier` vocabulary.

It MUST NOT use Python object identity.

Movement identity is distinct from source Document identity, Register identity, and runtime object identity.

The concrete generation strategy is an implementation concern.

Movement identity MUST NOT introduce semantic nondeterminism into Posting.

---

# 15. Source Document Identity

Every Movement generated by Posting MUST contain explicit durable source Document identity.

Conceptually:

```text
ObjectInstance.identity
        ↓
Movement.source_document_identity
```

A runtime Python object reference MUST NOT be used as durable source identity.

---

# 16. Register Identity

A Movement MUST identify the target Register through an explicit Register identity.

Conceptually:

```python
register_identity: Identifier
```

The concrete representation of Register identity may be refined when Register Architecture implementation is established.

Posting Handlers MAY determine the target Register as part of document-specific accounting semantics. The Register MUST validate applicability through its Register Posting Contract.

---

# 17. Movement Type

Movement Type identifies the accounting nature of a Movement.

The universal Movement API SHOULD represent it through an explicit value type or equivalent immutable representation.

The concrete set of Movement Type values is intentionally deferred.

Existing glossary terminology MUST NOT automatically become a universal API enumeration unless the broader Register/Posting architecture explicitly requires it.

---

# 18. Dimensions

Dimensions identify the accounting aggregation context of a Movement.

Conceptually:

```python
MovementDimensions
```

may contain values such as product, warehouse, organization, or other Register-defined dimensions.

Concrete dimension types are Register-specific.

The universal Movement API MUST NOT hard-code Inventory-specific dimensions.

---

# 19. Resources

Resources carry quantitative or accumulated accounting values.

Conceptually:

```python
MovementResources
```

The universal Movement API MUST NOT prescribe a single resource such as `quantity`.

A Register Posting Contract MAY require quantity, amount, cost, weight, or other Register-specific resources.

Accounting values MUST use appropriate domain value representations. Where exact accounting semantics require it, floating-point representation MUST NOT be used as an uncontrolled substitute for exact decimal semantics.

---

# 20. Attributes

Attributes contain additional descriptive accounting fact data.

Conceptually:

```python
MovementAttributes
```

Attributes MUST NOT replace dimensions or resources merely because a value is convenient to store there.

The semantic role of each Movement component MUST remain explicit.

---

# 21. Movement Time

Movement time is optional at the universal Movement level.

A concrete implementation MAY therefore use:

```python
accounting_time: datetime | None
```

A Movement MUST NOT universally require a timestamp or accounting date.

If a Register requires temporal information, that requirement belongs to the applicable Register Posting Contract.

Semantic accounting time MUST NOT be derived from uncontrolled system time.

---

# 22. MovementSet

`MovementSet` represents the complete semantic accounting result of one Posting Handler execution.

The concrete representation SHOULD be immutable.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class MovementSet:
    movements: tuple[Movement, ...]
```

The semantic requirements are:

* one Posting operation produces exactly one MovementSet;
* the MovementSet is complete before validation;
* the MovementSet cannot be silently rewritten downstream;
* equivalent semantic input produces equivalent semantic MovementSet output.

---

# 23. MovementSet Completeness

The Handler MUST return the complete MovementSet for the operation.

The Posting Engine MUST NOT assume it can repeatedly invoke a Handler to complete a partial result.

If required accounting information is missing, the appropriate outcome is failure.

---

# 24. Movement Immutability

The concrete Movement and MovementSet representation SHOULD use immutable Python structures such as frozen dataclasses and tuples.

The architectural requirement is semantic immutability:

```text
Handler result
      ↓
stable accounting meaning
      ↓
validation
      ↓
register processing
```

Downstream components MUST NOT silently mutate accounting semantics.

---

# 25. Movement Validator

Movement validation is an explicit boundary between Movement generation and Register acceptance.

A concrete contract is:

```python
class MovementValidator(Protocol):
    def validate(
        self,
        movement_set: MovementSet,
    ) -> None:
        ...
```

Validation MUST occur before the Required Persistent Result is established.

The validator is responsible for structural validation, Register reference validation, dimension validation, resource validation, attribute validation, applicable Movement Type validation, and Register Posting Contract validation.

The validator MUST NOT persist Movements.

---

# 26. Validation Result

The initial API MAY use exception-based validation failure:

```python
def validate(
    self,
    movement_set: MovementSet,
) -> None:
    ...
```

A validation failure MUST prevent the MovementSet from entering the persistence/application boundary.

A later implementation MAY introduce structured validation results if required by the broader validation architecture, without changing the semantic boundary.

---

# 27. Register Posting Contract

The Register Posting Contract defines Register-specific acceptance requirements.

A concrete contract is:

```python
class RegisterPostingContract(Protocol):
    def validate(
        self,
        movement: Movement,
    ) -> None:
        ...
```

The contract MAY validate Register identity, required dimensions, required resources, required attributes, Movement Type, data types, and Register-specific invariants.

The contract MUST NOT contain document-specific Posting logic.

---

# 28. Register Contract Resolution

The Posting implementation requires an explicit way to obtain the applicable Register Posting Contract.

A minimal boundary is:

```python
class RegisterPostingContractResolver(Protocol):
    def resolve(
        self,
        register_identity: Identifier,
    ) -> RegisterPostingContract:
        ...
```

The concrete resolver mechanism is implementation-defined.

Resolution MAY use Register metadata, explicit configuration, or registered Register contracts. It MUST NOT depend on hidden global service discovery.

---

# 29. Register Acceptance

Register acceptance is represented semantically by successful application of the applicable Register Posting Contract.

The API MUST preserve the distinction:

```text
validated
    ≠
persisted
```

and:

```text
accepted
    ≠
persisted
```

Acceptance confirms that a Movement satisfies Register semantic requirements. It does not mean that the Required Persistent Result has already been established.

---

# 30. Persistence / Application Coordinator

Posting requires an explicit boundary responsible for establishing the Required Persistent Result.

A proposed contract is:

```python
class PostingResultCoordinator(Protocol):
    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> None:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None:
        ...
```

The normal return from `establish()` or `remove()` means that the required persistent accounting result for that operation was established.

A known persistence/application failure MUST be raised or otherwise reported through the existing Persistence error boundary and MAY be translated at the Posting boundary. A `PersistenceIndeterminateError` MUST remain distinguishable and MUST result in an Indeterminate Posting outcome.

The coordinator therefore does not need to return a separate Posting result object merely to represent these cases; normal return, known failure, and indeterminate failure are sufficient semantic outcomes at this boundary.

This is a semantic coordination boundary, not a physical persistence API.

Its implementation MAY coordinate removal/replacement of obsolete posting effects, persistence of new register effects, persistent document posting state, other persistent effects belonging to the Posting result, and applicable Persistence Scope.

---

# 31. Persistence Boundary

`PostingResultCoordinator` MUST NOT expose a universal:

```python
begin()
commit()
rollback()
```

Posting contract.

Physical transaction mechanics belong to Persistence Architecture.

The Posting Engine requires only the semantic distinction between established Required Persistent Result, known failure, and indeterminate outcome.

---

# 32. Persistence Errors

The implementation MUST reuse existing Persistence error semantics where appropriate rather than creating parallel persistence hierarchies inside Posting.

Posting MAY wrap or translate persistence errors at the Posting boundary, but the semantic distinction between known failure and indeterminate outcome MUST remain available.

---

# 33. Posting Result

Because Posting has three semantically distinct outcomes, the public API SHOULD expose a tagged immutable result model.

A proposed conceptual model is:

```python
class PostingResult:
    ...
```

with semantic outcomes:

```text
Success
Failure
Indeterminate
```

A concrete implementation MAY use distinct immutable result variants and a union/variant type.

The semantic requirements are:

* Success means Logical Completion;
* Failure means successful Logical Completion was not established;
* Indeterminate means the persistent outcome cannot reliably be determined.

---

# 34. Posting Errors

The implementation SHOULD provide a common Posting error boundary:

```python
class PostingError(Exception):
    ...
```

A minimal taxonomy MAY include:

```python
class PostingValidationError(PostingError):
    ...

class PostingHandlerResolutionError(PostingError):
    ...

class PostingHandlerError(PostingError):
    ...

class PostingMovementValidationError(PostingError):
    ...

class PostingRegisterAcceptanceError(PostingError):
    ...

class PostingPersistenceError(PostingError):
    ...

class PostingIndeterminateError(PostingError):
    ...
```

This taxonomy is provisional at implementation level. The architecture does not require every internal failure category to become a distinct public exception.

---

# 35. Exception vs Result Semantics

The implementation MUST avoid ambiguity in which an exception itself determines whether Posting failed or became indeterminate.

A known persistence failure and an indeterminate persistence outcome are semantically different.

The Public API MUST preserve this distinction.

Event publication failures after Logical Completion are separate from both.

---

# 36. Event Publisher

Posting events are published only after Logical Completion.

A minimal boundary is:

```python
class PostingEventPublisher(Protocol):
    def publish(
        self,
        event: PostingEvent,
    ) -> None:
        ...
```

The concrete event hierarchy is implementation-dependent.

The event boundary MUST preserve:

```text
Required Persistent Result
        ↓
Logical Completion
        ↓
Posting Event
```

A Handler MUST NOT publish Posting lifecycle events.

---

# 37. Event Publication Failure

Event publication failure MUST NOT be interpreted as proof that the accounting result failed.

The implementation MUST distinguish:

```text
Accounting result failure
        ≠
Indeterminate accounting result
        ≠
Post-Logical-Completion event failure
```

If Logical Completion has already been established, failure to publish an event MUST NOT retroactively convert the established accounting result into a Posting Failure.

---

# 38. Posting Events

The initial semantic event set is:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

Concrete event classes SHOULD carry explicit source Document identity and MUST NOT require a runtime object reference as durable identity.

---

# 39. Dependency Boundary

Posting may interact with dependency state or restoration workflows through an explicit integration boundary.

If dependency-related effects form part of the Required Persistent Result, they MUST participate in the applicable consistency boundary.

Posting Handlers MUST NOT directly manage the dependency graph.

No generic dependency service is introduced merely to support this step.

---

# 40. Posting Engine Dependency Graph

The intended dependency graph is:

```text
PostingAPI
    ↓
PostingEngine
    ├── PostingHandlerResolver
    ├── PostingContextFactory
    ├── MovementValidator
    ├── PostingResultCoordinator
    ├── PostingEventPublisher
    └── optional dependency integration boundary

PostingHandlerResolver
    ↓
PostingHandler

PostingHandler
    ↓
MovementSet

MovementValidator
    ├── RegisterPostingContractResolver
    └── RegisterPostingContract

PostingResultCoordinator
    ↓
Persistence / Application Architecture
    ↓
Register / Object persistence boundaries
```

The Posting Engine is the orchestrator. No Handler should depend on the Posting Engine.

---

# 41. Posting Context Factory

Posting Context creation SHOULD have an explicit boundary:

```python
class PostingContextFactory(Protocol):
    def create(
        self,
        document: ObjectInstance,
    ) -> PostingContext:
        ...
```

The factory is owned by the Posting Engine/application composition boundary.

It MAY obtain metadata, controlled services, Posting clock, and other explicitly required context inputs.

---

# 42. Public API Composition

Runtime composition SHOULD conceptually be:

```text
Application Composition
        │
        ├── PostingAPI
        │      ↓
        │   PostingEngine
        │
        ├── HandlerResolver
        ├── ContextFactory
        ├── MovementValidator
        ├── ResultCoordinator
        └── EventPublisher
```

The Public API MUST NOT become the owner of the complete dependency graph.

Dependency injection/composition technology is implementation-specific. No external DI framework is required by this design.

---

# 43. Posting Flow — Post

The concrete Post flow is:

```text
PostingAPI.post(document)
        ↓
PostingEngine.post(document)
        ↓
validate preconditions
        ↓
resolve Handler
        ↓
create PostingContext
        ↓
Handler.post(context)
        ↓
MovementSet
        ↓
MovementValidator.validate(...)
        ↓
PostingResultCoordinator.establish(...)
        ↓
Logical Completion
        ↓
publish DocumentPosted
        ↓
PostingResult.Success
```

Event publication occurs after Logical Completion.

---

# 44. Posting Flow — Unpost

The concrete Unpost flow is:

```text
PostingAPI.unpost(document)
        ↓
PostingEngine.unpost(document)
        ↓
validate unposting preconditions
        ↓
identify applicable existing posting effects
        ↓
coordinate removal of accounting effects
        ↓
Logical Completion
        ↓
publish DocumentUnposted
        ↓
PostingResult.Success
```

Identification and removal of persistent accounting effects belong to the Persistence/Application boundary. The Posting API MUST NOT expose direct Movement deletion mechanics.

---

# 45. Posting Flow — Repost

The concrete Repost flow is:

```text
PostingAPI.repost(document)
        ↓
PostingEngine.repost(document)
        ↓
validate reposting preconditions
        ↓
resolve current Handler
        ↓
create PostingContext
        ↓
Handler.post(context)
        ↓
new MovementSet
        ↓
validate new MovementSet
        ↓
establish new Required Persistent Result
        ↓
Logical Completion
        ↓
publish DocumentReposted
        ↓
PostingResult.Success
```

Reposting rebuilds accounting effects from the current semantic state of the source Document.

---

# 46. Reposting and Existing Movements

The Posting layer MUST NOT directly mutate obsolete Movements as its primary semantic mechanism.

Replacement/removal of obsolete persistent accounting effects belongs to the Posting Result Coordinator and applicable persistence/application boundary.

The semantic requirement is that the resulting accounting state is derived from the current document state.

---

# 47. Reposting and Idempotency

The API MUST distinguish:

```text
Retry
Repost
Idempotency
```

A retry repeats an operation after an execution failure. Repost explicitly rebuilds accounting effects from current document state. Idempotency is a property of repeated equivalent operations.

These concepts MUST NOT be collapsed into one API flag.

---

# 48. Determinism

Equivalent semantic Posting inputs MUST produce equivalent semantic Movement results.

Relevant inputs include source Document semantic state, relevant metadata, relevant reference state, Posting Context inputs, and accounting time/environment inputs.

The implementation MUST NOT derive semantic accounting results from Python object identity, arbitrary collection ordering, storage layout, uncontrolled system time, or uncontrolled external state.

Movement identity generation MUST NOT undermine semantic determinism.

---

# 49. Identity Preservation

The implementation MUST preserve the Phase 5 identity boundaries.

For the source Document:

```text
ObjectInstance.identity
        ↓
Movement.source_document_identity
```

Posting MUST NOT introduce a parallel identity abstraction where the existing `Identifier` vocabulary is sufficient.

---

# 50. Phase 5 Integration

Phase 5 remains closed.

Posting MUST use existing persistence boundaries rather than bypassing them.

The implementation MUST NOT:

* store runtime objects directly in register persistence;
* pass Storage Providers into Posting Handlers;
* persist runtime-only state implicitly;
* use runtime object identity as durable accounting identity;
* introduce a second Storage Provider boundary;
* introduce a second generic persistence abstraction.

The existing Persistence Architecture remains authoritative for durable state.

---

# 51. Register Persistence Integration

The existing persistence layer currently contains a placeholder Movement type and a `RegisterFactPersistence` boundary.

Once the concrete Movement API is established, the placeholder SHOULD be replaced by the actual universal Movement representation.

The persistence contract SHOULD consume the concrete Movement type without taking ownership of its semantic definition.

Conceptually:

```text
Register Movement
        ↓
RegisterFactPersistence
        ↓
Persistence implementation
```

---

# 52. Storage Boundary

No Posting component may depend directly on a Storage Provider.

The dependency direction remains:

```text
Posting
    ↓
Persistence / Application boundary
    ↓
Persistence contracts
    ↓
Storage implementation
```

Posting code MUST NOT contain SQL, filesystem paths, provider-specific APIs, or database-specific transaction code.

---

# 53. Concrete API Surface

The initial public Platform surface SHOULD be limited to the contracts actually required by the vertical slice.

Expected public concepts include:

```python
PostingAPI
PostingEngine
PostingContext
PostingHandler
PostingHandlerResolver
Movement
MovementSet
MovementValidator
RegisterPostingContract
PostingResult
PostingError
```

Supporting concepts MAY remain internal until their public exposure is justified.

---

# 54. Proposed Posting Package API

A proposed `posting/__init__.py` surface is:

```python
from .api import PostingAPI
from .context import PostingContext
from .engine import PostingEngine
from .handlers import PostingHandler, PostingHandlerResolver
from .context import PostingServices
from .movement_set import MovementSet
from ..registers.movement import Movement
from .result import PostingResult
```

Error exports MAY be added according to the final public error policy.

The exact import layout is subject to existing project public-API conventions.

---

# 55. Proposed Register Package API

A proposed `registers/__init__.py` surface is:

```python
from .contracts import RegisterPostingContract
from .movement import Movement
```

`Movement` is owned and publicly defined by the Register/Accounting Fact boundary. The Posting package MAY re-export it as a convenience alias only if existing project public-API conventions justify that convenience; it MUST NOT define a second Movement type or module.

The semantic ownership decision is:

```text
Register Architecture
    owns the universal accounting-fact meaning of Movement

Posting Architecture
    generates Movement
```

---

# 56. Movement Ownership Decision

The universal Movement representation is owned by the Register/Accounting Fact boundary rather than by the Posting Engine.

The dependency direction is therefore:

```text
Posting
    imports
Register Movement
```

and not:

```text
Register
    imports
Posting Movement
```

This avoids a circular dependency and keeps Movement reusable by future Posting and Register implementations.

---

# 57. Validation Ownership Decision

Movement validation is conceptually part of the Posting lifecycle but depends on Register-specific contracts.

Therefore the initial implementation SHOULD place the validator on the Posting side while consuming Register contracts through an explicit boundary.

Conceptually:

```text
posting.validation
        ↓
registers.contracts
```

A later refactoring MAY move reusable validation components if the dependency direction remains equivalent.

---

# 58. Document Representation Decision

The current repository does not contain a concrete Posting-specific Document hierarchy.

The existing runtime representation is:

```python
ObjectInstance
```

Therefore Step 7 MUST NOT introduce a new abstract `Document` hierarchy solely to satisfy the Posting API.

If a future Document Architecture introduces a stronger application-level Document abstraction, Posting may adopt it through a separate architectural change.

---

# 59. Object State Boundary

The current generic `ObjectInstance.state` model MUST NOT be expanded merely to encode Posting state without architectural justification.

Posting state such as `posted` or `unposted` is a business/accounting lifecycle concern unless the broader Object Architecture explicitly defines it otherwise.

The Posting implementation MUST NOT infer Posting lifecycle solely from generic runtime object state.

---

# 60. API Invariants

The following invariants are normative for the concrete API.

### API-POST-01

The Public Posting API delegates Posting execution to the Posting Engine.

### API-POST-02

Post, Unpost, and Repost are distinct semantic operations.

### API-POST-03

The source Document has explicit identity.

### API-POST-04

The caller does not supply a MovementSet to Post.

### API-POST-05

The Handler generates exactly one complete MovementSet per Posting operation.

### API-POST-06

Every Movement contains explicit source Document identity.

### API-POST-07

Movement identity is distinct from runtime object identity.

### API-POST-08

MovementSet semantics are immutable after Handler completion.

### API-POST-09

Movement validation precedes establishment of the Required Persistent Result.

### API-POST-10

Register acceptance is distinct from physical persistence.

### API-POST-11

Posting Handler does not own persistence or transaction control.

### API-POST-12

Posting Engine does not expose a universal physical transaction API.

### API-POST-13

Success means Logical Completion.

### API-POST-14

Failure does not imply successful Logical Completion.

### API-POST-15

Indeterminate Outcome is distinct from known Failure.

### API-POST-16

Event publication occurs only after Logical Completion.

### API-POST-17

Event publication failure does not imply accounting-result failure after Logical Completion.

### API-POST-18

Repost rebuilds accounting effects from current Document state.

### API-POST-19

Posting does not bypass Phase 5 Persistence or Storage boundaries.

### API-POST-20

Equivalent semantic Posting inputs produce equivalent semantic Movement results.

---

# 61. Testing Strategy

The Concrete API Design implies the following test boundaries.

## 61.1 Public API Tests

Test that Post, Unpost, and Repost delegate to Posting Engine and preserve semantic outcome.

## 61.2 Posting Engine Tests

Test lifecycle ordering, Handler resolution, Context creation, Handler execution, Movement validation, persistent-result coordination, Logical Completion, and event publication.

## 61.3 Handler Contract Tests

Test that a Handler receives Posting Context, returns MovementSet, does not require persistence, and produces a complete MovementSet.

## 61.4 Movement Tests

Test identity preservation, source Document identity, Register identity, immutability, and deterministic semantic representation.

## 61.5 Movement Validation Tests

Test invalid structure, invalid Register identity, missing required dimensions/resources, invalid Movement Type, and Register Contract rejection.

## 61.6 Failure Tests

Test precondition failure, Handler resolution failure, Handler failure, Movement validation failure, Register acceptance failure, known persistence failure, indeterminate persistence outcome, and event publication failure after Logical Completion.

## 61.7 Reposting Tests

Test repost from current Document state, replacement of obsolete effects through the persistence/application boundary, failed repost, indeterminate repost, and deterministic repost result.

---

# 62. Proposed Test Layout

The initial test structure SHOULD be:

```text
tests/
├── unit/
│   └── posting/
│       ├── test_api.py
│       ├── test_context.py
│       ├── test_engine.py
│       ├── test_handlers.py
│       ├── test_movement.py
│       ├── test_result.py
│       └── test_validation.py
│
├── contracts/
│   ├── posting/
│   │   ├── test_posting_handler.py
│   │   ├── test_posting_engine.py
│   │   └── test_movement.py
│   │
│   └── registers/
│       └── test_register_posting_contract.py
│
└── integration/
    └── posting/
        └── ...
```

The exact test organization MAY follow existing repository conventions.

---

# 63. Concrete API Example

The intended usage is conceptually:

```python
result = posting_api.post(document)

if result.is_success:
    ...
elif result.is_failure:
    ...
else:
    ...
```

The exact result inspection API is not yet normative.

The important semantic requirement is that callers can distinguish Success, Failure, and Indeterminate.

---

# 64. Concrete Handler Example

A Handler implementation is conceptually:

```python
class GoodsReceiptPostingHandler:
    def post(
        self,
        context: PostingContext,
    ) -> MovementSet:
        ...
```

The Handler reads Goods Receipt semantic state from the Context and produces a complete MovementSet.

It does not persist Movements, control transactions, or publish lifecycle events.

---

# 65. Concrete Movement Example

A future concrete Movement may conceptually look like:

```python
Movement(
    identity=movement_identity,
    source_document_identity=document.identity,
    register_identity=inventory_register_identity,
    movement_type=movement_type,
    dimensions=dimensions,
    resources=resources,
    attributes=attributes,
    accounting_time=accounting_time,
)
```

The example does not prescribe Inventory-specific fields.

Inventory-specific requirements belong to the Inventory Register Posting Contract.

---

# 66. Runtime Composition Example

A complete runtime composition may conceptually be:

```python
posting_engine = PostingEngineImpl(
    handler_resolver=handler_resolver,
    context_factory=context_factory,
    movement_validator=movement_validator,
    result_coordinator=result_coordinator,
    event_publisher=event_publisher,
)

posting_api = PostingAPIImpl(
    engine=posting_engine,
)
```

This is composition pseudocode. No specific DI framework is required.

---

# 67. Standard Configuration Boundary

Step 7 implements Platform Posting infrastructure.

It MUST NOT make the Platform depend on Standard Configuration.

The dependency direction remains:

```text
Standard Configuration
        ↓
Platform Posting / Register APIs
```

Goods Receipt → Inventory semantics are implemented in the later vertical-slice step.

Step 7 only provides the platform contracts required for that integration.

---

# 68. Vertical Slice Preparation

Step 7 MUST provide enough concrete infrastructure for the later vertical slice:

```text
Goods Receipt
      ↓
Posting API
      ↓
Posting Engine
      ↓
Posting Context
      ↓
Goods Receipt Posting Handler
      ↓
MovementSet
      ↓
Movement Validation
      ↓
Inventory Register Contract
      ↓
Required Persistent Result
      ↓
Inventory
```

Step 7 MUST NOT hard-code Goods Receipt or Inventory semantics into universal Posting APIs.

---

# 69. Explicit Non-Goals

This document does not define:

* concrete database schema;
* Storage Provider implementation;
* physical transaction mechanism;
* transaction isolation;
* rollback mechanism;
* Persistence Scope implementation;
* recovery subsystem;
* event bus implementation;
* event delivery retry policy;
* idempotency implementation;
* exact Repost replacement algorithm;
* dependency graph implementation;
* totals implementation;
* Inventory-specific Movement fields;
* Goods Receipt posting rules;
* concrete Movement Type vocabulary;
* concrete Register implementation;
* concrete application DI framework;
* serialization format;
* network/HTTP API;
* persistence query API.

---

# 70. Relationship with Previous Steps

Step 7 depends on the approved semantic decisions of Steps 1–6:

```text
Step 1 — Posting Architecture Boundary
        ↓
Step 2 — Posting Semantic Contract
        ↓
Step 3 — Posting Lifecycle & Validation
        ↓
Step 4 — Register Movement Contract
        ↓
Step 5 — Consistency, Failure & Reposting
        ↓
Step 6 — Public Posting API
        ↓
Step 7 — Concrete API Design
```

Step 7 translates those semantic decisions into Python-level contracts. It MUST NOT redefine them.

---

# 71. Relationship with Phase 5

Phase 5 remains closed.

Step 7 integrates with `ObjectInstance`, `Identifier`, metadata identity, Persistence contracts, Persistence error semantics, Storage Provider boundary, and runtime/persistent representation boundaries.

No Phase 5 semantic contract is reopened by this design.

---

# 72. Implementation Sequence

Once this Concrete API Design is approved, implementation SHOULD proceed in the following order:

```text
1. Movement representation
2. MovementSet
3. Register Posting Contract boundary
4. Movement Validator
5. Posting Context
6. Posting Handler / Resolver contracts
7. Posting Result / Error model
8. Posting Result Coordinator boundary
9. Posting Engine
10. Public Posting API
11. Event boundary
12. Runtime composition
13. Contract/unit tests
14. Integration tests
```

The sequence MAY be adjusted where dependency ordering requires it. Semantic boundaries MUST remain unchanged.

---

# 73. API Review Checklist

Before implementation begins, verify:

### Public API

* [ ] Post exists.
* [ ] Unpost exists.
* [ ] Repost exists.
* [ ] API delegates to Posting Engine.
* [ ] API does not contain accounting semantics.

### Engine

* [ ] lifecycle orchestration is explicit;
* [ ] Handler resolution is explicit;
* [ ] Context creation is explicit;
* [ ] Movement validation is explicit;
* [ ] persistent-result coordination is explicit;
* [ ] Logical Completion is explicit.

### Context

* [ ] source Document is explicit;
* [ ] metadata is explicit;
* [ ] capabilities are controlled;
* [ ] uncontrolled service locator is avoided;
* [ ] time is controlled.

### Handler

* [ ] Handler returns MovementSet;
* [ ] Handler owns document-specific accounting semantics;
* [ ] Handler does not persist;
* [ ] Handler does not control transactions;
* [ ] Handler does not publish events.

### Movement

* [ ] explicit Movement identity;
* [ ] explicit source Document identity;
* [ ] explicit Register identity;
* [ ] Movement Type boundary;
* [ ] dimensions boundary;
* [ ] resources boundary;
* [ ] attributes boundary;
* [ ] optional temporal semantics;
* [ ] semantic immutability.

### Register

* [ ] Register Posting Contract is explicit;
* [ ] acceptance is distinct from persistence;
* [ ] Register does not own document-specific Posting logic.

### Persistence

* [ ] Required Persistent Result boundary is explicit;
* [ ] Persistence Scope remains behind Persistence Architecture;
* [ ] physical transaction API is not exposed by Posting;
* [ ] Storage Provider is not exposed to Posting.

### Result

* [ ] Success is distinct from Failure;
* [ ] Failure is distinct from Indeterminate;
* [ ] event failure after Logical Completion is distinct.

### Reposting

* [ ] Repost is explicit;
* [ ] current Document state is used;
* [ ] replacement of obsolete effects belongs to persistence/application coordination;
* [ ] Repost is not confused with Retry or Idempotency.

---

# 74. Step 7 Acceptance Criteria

Step 7 Concrete API Design is ready for implementation when:

1. Public Post, Unpost, and Repost boundaries are explicitly defined.
2. Posting Engine responsibility is explicit.
3. Posting Context boundary is explicit.
4. Posting Handler contract is explicit.
5. Handler resolution boundary is explicit.
6. Movement has an explicit concrete Python-level representation.
7. MovementSet has an explicit concrete Python-level representation.
8. Movement identity uses the existing `Identifier` vocabulary.
9. Source Document identity is explicit and durable.
10. Movement validation has an explicit API boundary.
11. Register Posting Contract has an explicit API boundary.
12. Register acceptance is distinct from persistence.
13. Required Persistent Result has an explicit application-level coordination boundary.
14. Posting Result preserves Success, Failure, and Indeterminate semantics.
15. Posting errors preserve known failure versus indeterminate outcome.
16. Event publication has an explicit boundary.
17. Event publication failure is distinct from accounting-result failure.
18. Repost semantics are represented by a distinct API operation.
19. Phase 5 persistence/storage boundaries remain intact.
20. No universal physical transaction API is introduced.
21. No Standard Configuration dependency is introduced into Platform Posting.
22. The design is sufficient to implement Platform Posting infrastructure without architectural guessing.
23. The design remains sufficiently open to defer implementation-specific mechanisms.

---

# 75. Architecture Review

**Architecture Review: APPROVED**

Review result:

* Blockers: 0
* Major architectural issues: 0
* Minor alignment issues: 0
* Required alignments: completed

The Concrete API Design is consistent with the approved Phase 6 Steps 1–6 and preserves the established Posting, Register, Persistence, Storage, and Standard Configuration boundaries.

The required alignments are explicitly resolved:

* universal `Movement` has one concrete owner in `registers/movement.py`;
* `PostingResultCoordinator` distinguishes normal completion, known failure, and indeterminate persistence outcomes through its error boundary;
* Unpost has an explicit symmetric `remove()` coordination operation;
* `PostingServices` is defined as a controlled capability aggregate rather than an unrestricted service locator.

No physical transaction API, Storage Provider dependency, database schema, DI framework, recovery mechanism, idempotency algorithm, or Standard Configuration dependency is introduced by this design.

Implementation may proceed within the concrete API boundaries defined by this document.

---

# 76. Related Architecture

* `docs/architecture/posting/POSTING_ARCHITECTURE.md`
* `docs/architecture/posting/POSTING_LIFECYCLE.md`
* `docs/architecture/posting/POSTING_HANDLERS.md`
* `docs/architecture/posting/POSTING_CONTEXT.md`
* `docs/architecture/posting/MOVEMENT_VALIDATION.md`
* `docs/architecture/posting/REGISTER_POSTING_CONTRACTS.md`
* `docs/implementation/PHASE_6_STEP_2_POSTING_SEMANTIC_CONTRACT.md`
* `docs/implementation/PHASE_6_STEP_3_POSTING_LIFECYCLE_AND_VALIDATION.md`
* `docs/implementation/PHASE_6_STEP_4_REGISTER_MOVEMENT_CONTRACT.md`
* `docs/implementation/PHASE_6_STEP_5_CONSISTENCY_FAILURE_AND_REPOSTING.md`
* `docs/implementation/PHASE_6_STEP_6_PUBLIC_POSTING_API.md`
* Phase 5 Persistence Architecture
* Phase 5 Storage Provider Boundary
* `docs/implementation/REPOSITORY_STRUCTURE.md`

---

# 77. Step 7 Concrete API Design Status

**Step 7 — Concrete API Design**

**Status: CLOSED**

The semantic architecture is inherited from the approved Phase 6 Steps 1–6.

The concrete API boundary has passed Architecture Review and is ready for implementation.
