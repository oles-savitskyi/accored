# Phase 7 — Step 6

# Concrete API Design — Register Totals Lifecycle & Maintenance

**Status:** Draft — Final Architecture Review

---

## 1. Purpose

This document defines the concrete API design for Register Totals lifecycle and maintenance introduced by Phase 7 Step 6.

The purpose of this step is to provide a concrete maintenance boundary for the derived Register Totals state while preserving the architectural contracts already established by:

* Phase 5 Persistence;
* Phase 6 Posting;
* Phase 7 Step 4 — Totals Engine;
* Phase 7 Step 5 — Balance Query.

Step 6 does not redefine the Totals Engine, Totals Key model, Total Value model, or Balance Query contract.

It defines the API through which Totals are:

* incrementally maintained;
* removed;
* rebuilt;
* recovered after an inconsistent or indeterminate state;
* published as a complete derived state;
* protected from partial maintenance visibility.

---

# 2. Architectural Position

Register Totals are derived state.

Persisted Movement Facts remain the authoritative source of register state.

The fundamental dependency direction is:

```text
Persisted Movement Facts
        │
        ▼
   Totals Engine
     [Step 4]
        │
        ▼
 Published Totals
        │
        ▼
  Balance Query
     [Step 5]
```

Step 6 introduces maintenance orchestration around the existing Totals Engine:

```text
Persisted Movement Facts
        │
        ▼
Totals Maintenance Coordinator
        │
        ▼
   Totals Engine
     [Step 4]
        │
        ▼
 Published Totals
        │
        ▼
  Balance Query
     [Step 5]
```

The Totals Maintenance Coordinator does not become a second Totals Engine.

It coordinates lifecycle, maintenance, recovery, idempotency, consistency state and publication.

---

# 3. Scope

Step 6 covers:

* Totals lifecycle state;
* Totals consistency state;
* incremental Totals maintenance;
* Totals rebuild;
* Totals recovery;
* maintenance idempotency;
* maintenance serialization;
* replacement-state isolation;
* semantic publication;
* failure and indeterminate outcomes;
* recovery from authoritative Movement Facts;
* integration with existing Movement persistence;
* integration with the existing Totals Engine;
* preservation of Balance Query semantics.

---

# 4. Out of Scope

Step 6 does not introduce or redefine:

* Movement;
* Movement persistence;
* TotalsKey;
* TotalValue;
* Totals Engine aggregation semantics;
* Balance Query;
* Balance Result;
* Posting Handler contracts;
* Posting Context;
* Posting lifecycle;
* Posting events;
* General Ledger;
* valuation;
* costing;
* period closing;
* historical balances;
* turnover queries;
* distributed transactions;
* asynchronous maintenance;
* cross-register reconciliation;
* a new generic Totals persistence abstraction.

---

# 5. Existing Architectural Dependencies

Step 6 depends on the following already established contracts.

## 5.1. Movement

The existing `Movement` model is the authoritative register fact representation.

Its relevant identity fields are:

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

Step 6 does not redefine or relocate `Movement`.

---

## 5.2. Register Identity

Register identity continues to use the existing platform `Identifier`.

Step 6 does not introduce a separate `RegisterIdentity` type.

---

## 5.3. RegisterFactPersistence

The existing `RegisterFactPersistence` boundary remains the authoritative persistence interface for Movement Facts.

Conceptually:

```python
class RegisterFactPersistence(Protocol):
    def append(self, movements: Sequence[Movement]) -> None:
        ...

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        ...

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
        ...

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        ...
```

Step 6 does not introduce a `MovementFactSource`, `TotalsFactRepository`, or equivalent duplicate abstraction.

Rebuild obtains authoritative Movement Facts through the existing persistence boundary.

---

# 6. Existing Totals Engine Dependency

The Totals Engine is an architectural component established by Phase 7 Step 4.

Step 6 does not redefine its aggregation semantics.

The Totals Engine remains responsible for:

* calculating Totals contributions;
* maintaining derived aggregated state;
* using the established `TotalsKey`;
* using the established `TotalValue`;
* applying the established aggregation semantics;
* supporting the Totals read boundary defined by the earlier Phase 7 steps.

Step 6 consumes this existing capability.

It does not create a second Totals Engine.

---

# 7. Existing TotalsKey Contract

`TotalsKey` belongs to the Totals Engine architecture established by Step 4.

Step 6 therefore does not define a new `TotalsKey`.

The following principles remain owned by Step 4:

* TotalsKey identity semantics;
* immutability;
* hashability;
* dimension ordering;
* key equality;
* key construction;
* key validation.

Step 6 may use `TotalsKey` values produced according to the Step 4 contract, but does not redefine their representation.

The same rule applies to `TotalValue`.

---

# 8. Existing Totals Read Boundary

Step 6 reuses the existing Totals read boundary established by the earlier Totals/Balance architecture.

Step 6 does not introduce:

```text
TotalsStateReader
PublishedTotalsReader
TotalsSnapshotReader
```

as duplicate public abstractions.

Balance Query remains the consumer-facing read model.

Maintenance is responsible for maintaining the derived state that Balance Query reads.

---

# 9. Architectural Ownership

Responsibilities are divided as follows.

### RegisterFactPersistence

Owns:

* durable Movement Facts;
* Movement persistence;
* authoritative fact enumeration.

### Totals Engine

Owns:

* aggregation semantics;
* TotalsKey;
* TotalValue;
* contribution calculation;
* derived Totals state;
* incremental aggregation semantics.

### TotalsMaintenanceCoordinator

Owns:

* maintenance lifecycle;
* consistency state;
* maintenance orchestration;
* idempotency;
* maintenance serialization;
* rebuild orchestration;
* recovery orchestration;
* replacement publication coordination.

### Balance Query

Owns:

* read-only balance access;
* query semantics;
* balance result construction.

No component may take ownership of another component's responsibilities merely to simplify implementation.

---

# 10. Public Maintenance Boundary

Step 6 exposes one primary public mutation boundary:

```python
class TotalsMaintenanceCoordinator(Protocol):
    def apply(self, movement: Movement) -> MaintenanceResult:
        ...

    def remove(self, movement: Movement) -> MaintenanceResult:
        ...

    def rebuild(
        self,
        register_identity: Identifier,
    ) -> MaintenanceResult:
        ...

    def recover(
        self,
        register_identity: Identifier,
    ) -> MaintenanceResult:
        ...
```

This is the only public API responsible for Totals maintenance semantics.

The caller does not directly manipulate Totals.

---

# 11. Apply

```python
apply(movement: Movement) -> MaintenanceResult
```

`apply()` incorporates the specified Movement Fact into derived Totals state.

The operation:

1. validates that the Movement belongs to a supported register;
2. determines the Movement's Totals contribution using the existing Totals Engine semantics;
3. ensures the contribution is not applied more than once;
4. updates the derived Totals state;
5. publishes the resulting state according to the publication contract;
6. returns the maintenance outcome.

The caller does not specify:

* TotalsKey;
* contribution value;
* whether the Movement is already applied;
* an internal contribution identifier;
* a maintenance mode flag.

All such semantics belong to the Totals subsystem.

---

# 12. Remove

```python
remove(movement: Movement) -> MaintenanceResult
```

`remove()` removes the specified Movement Fact's contribution from derived Totals state.

The operation is based on the Movement's identity and register identity.

The caller does not provide a separate TotalsKey or contribution value.

Repeated removal of an already removed contribution is idempotent.

---

# 13. Rebuild

```python
rebuild(register_identity: Identifier) -> MaintenanceResult
```

`rebuild()` reconstructs the complete derived Totals state for a Register.

The authoritative input is:

```text
RegisterFactPersistence.enumerate(register_identity)
```

The operation must not reconstruct Totals from:

* existing Totals;
* previous Totals snapshots;
* arithmetic compensation;
* cached derived state.

The conceptual sequence is:

```text
RegisterFactPersistence
        │
        ▼
all authoritative Movement Facts
        │
        ▼
existing Totals Engine
        │
        ▼
complete replacement Totals state
        │
        ▼
validation
        │
        ▼
publication
```

---

# 14. Rebuild Does Not Accept Caller-Provided Facts

The public API intentionally does not expose:

```python
rebuild(
    register_identity,
    movements,
)
```

or:

```python
rebuild(
    register_identity,
    snapshot,
)
```

The caller identifies the Register only.

The maintenance subsystem obtains authoritative facts through the established persistence boundary.

This prevents a caller from accidentally supplying a fact set that differs from the persisted authoritative state.

---

# 15. Recover

```python
recover(register_identity: Identifier) -> MaintenanceResult
```

`recover()` restores a Register whose derived Totals state is known to require recovery.

Recovery is reconstruction from authoritative Movement Facts.

Conceptually:

```text
Recovery Required
       │
       ▼
    recover()
       │
       ▼
    rebuild()
       │
       ▼
Movement Facts
       │
       ▼
Totals Engine
       │
       ▼
validated replacement
       │
       ▼
publication
       │
       ▼
Active + Valid
```

Recovery does not attempt to repair Totals through compensating arithmetic.

Recovery does not treat existing Totals as authoritative.

---

# 16. Maintenance Operation

The maintenance operation enumeration is:

```python
class MaintenanceOperation(Enum):
    APPLY = "apply"
    REMOVE = "remove"
    REBUILD = "rebuild"
```

`RECOVER` is intentionally not a separate aggregation operation.

Recovery is an orchestration operation whose implementation ultimately performs a rebuild from authoritative facts.

---

# 17. Lifecycle State

Lifecycle and consistency are separate dimensions.

The lifecycle state is:

```python
class TotalsLifecycleState(Enum):
    CREATED = "created"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
```

### CREATED

Totals have been initialized but have not yet reached normal operational state.

### ACTIVE

The Totals subsystem is available for normal operation.

### MAINTENANCE

A maintenance operation is currently controlling the Totals state.

---

# 18. Consistency State

The consistency state is:

```python
class TotalsConsistencyState(Enum):
    VALID = "valid"
    INDETERMINATE = "indeterminate"
    RECOVERY_REQUIRED = "recovery_required"
```

### VALID

The published derived Totals correspond to the authoritative Movement Fact state at the relevant consistency boundary.

### INDETERMINATE

The system cannot establish whether the published derived state corresponds to the authoritative fact state.

### RECOVERY_REQUIRED

The system has established that the derived state must be reconstructed from authoritative Movement Facts.

---

# 19. Combined Maintenance State

The externally meaningful state is represented by:

```python
@dataclass(frozen=True, slots=True)
class TotalsMaintenanceState:
    lifecycle: TotalsLifecycleState
    consistency: TotalsConsistencyState
```

The normal operating state is:

```text
ACTIVE + VALID
```

Lifecycle and consistency must not be collapsed into a single enumeration.

---

# 20. Published Totals During Maintenance

Maintenance may retain the last successfully published Totals while replacement state is being constructed.

However, the existence of a readable previous publication does not automatically mean that it remains semantically current.

For example:

```text
Movement Facts
     │
     │ changed
     ▼
authoritative state = new
     │
     │ Totals update failed
     ▼
published Totals = old
```

In this situation the previous publication may remain externally readable as the last complete published state, but it must not be represented as `VALID` if it no longer corresponds to the authoritative fact boundary.

The system must therefore distinguish:

```text
last published state
```

from:

```text
currently valid derived state
```

This distinction is mandatory.

---

# 21. Maintenance Result

Expected maintenance outcomes are represented by:

```python
class MaintenanceOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"
```

The result object is:

```python
@dataclass(frozen=True, slots=True)
class MaintenanceResult:
    operation: MaintenanceOperation
    outcome: MaintenanceOutcome
    state: TotalsMaintenanceState
```

The result communicates expected operational outcomes.

It does not replace infrastructure exceptions where the platform's established error contract requires an exception.

---

# 22. Outcome vs Consistency State

Operation outcome and resulting consistency state are independent concepts.

For example:

```text
operation = APPLY
outcome = INDETERMINATE
consistency = RECOVERY_REQUIRED
```

is valid.

Likewise:

```text
operation = REBUILD
outcome = FAILURE
consistency = RECOVERY_REQUIRED
```

may be valid when the rebuild could not establish a valid replacement state.

The API must not encode consistency solely through operation success/failure.

---

# 23. Idempotency

All public maintenance operations are idempotent.

## Apply

Repeated application of the same Movement Fact must not duplicate its contribution.

```text
apply(M)
apply(M)
```

must have the same semantic effect as:

```text
apply(M)
```

after successful completion.

## Remove

Repeated removal must not subtract the same contribution multiple times.

```text
remove(M)
remove(M)
```

must have the same semantic result as:

```text
remove(M)
```

after successful completion.

## Rebuild

Repeated rebuild operations over the same authoritative Movement Fact set must produce the same semantic Totals state.

## Recover

Repeated recovery after successful recovery must not introduce additional changes.

---

# 24. Caller Flags Are Forbidden

The public API must not expose flags such as:

```python
apply(movement, already_applied=True)
```

or:

```python
remove(movement, already_removed=True)
```

The caller must not declare the current Totals state.

Idempotency and state detection are responsibilities of the maintenance subsystem.

---

# 25. Movement Contribution Identity

A logical contribution is identified by:

```text
Movement Identity + Register Identity
```

It is not identified by:

```text
TotalsKey
```

or:

```text
TotalsKey + TotalValue
```

Two distinct Movement Facts may have identical:

* Register Identity;
* TotalsKey;
* contribution value.

They remain distinct authoritative facts and distinct logical contributions.

This identity is an internal maintenance concept and is not required to become a public API type.

---

# 26. Contribution Calculation

Contribution calculation belongs to the Totals Engine architecture.

Step 6 does not redefine:

* Movement type interpretation;
* resource sign semantics;
* dimension extraction;
* TotalsKey construction;
* TotalValue construction;
* aggregation operators.

Maintenance invokes the existing Totals Engine semantics.

This ensures there is exactly one owner of aggregation behavior.

---

# 27. Publication Boundary

Publication is a semantic state transition.

A maintenance operation may construct a replacement Totals state privately.

That replacement must not become externally visible until it has successfully completed the required validation and publication conditions.

The external state is therefore always one of:

```text
previously published complete state
```

or:

```text
newly published complete state
```

It must never expose:

```text
partially rebuilt state
```

---

# 28. Replacement State Isolation

Rebuild must operate on isolated replacement state.

Conceptually:

```text
Published Totals
       │
       │ remains isolated
       │
       ▼
Replacement Totals
       │
       ├── enumerate Movement Facts
       ├── calculate contributions
       ├── aggregate
       └── validate
              │
              ▼
          publish
```

If any rebuild stage fails before publication:

```text
Replacement Totals
       │
       X
   discarded
```

The incomplete replacement must never become visible.

---

# 29. Publication Is Atomic at the Semantic Level

Step 6 requires semantic atomicity of publication.

This means consumers observe:

```text
old complete published state
```

or:

```text
new complete published state
```

but never an intermediate state.

The physical mechanism is intentionally implementation-defined.

Possible mechanisms include:

* atomic replacement;
* versioned snapshots;
* transactional replacement;
* storage-level atomic publication.

The Concrete API does not mandate a specific storage mechanism.

---

# 30. Maintenance Serialization

Only one competing maintenance operation may control publication for a given Register at a time.

An implementation may use an internal coordination mechanism such as:

```text
MaintenanceGuard
```

or an equivalent mechanism.

This is an infrastructure concern.

`MaintenanceGuard`, `MaintenanceLease`, or `MaintenanceSession` are not public domain/application APIs.

---

# 31. No Public Maintenance Session

The Concrete API does not expose:

```python
MaintenanceSession
```

to consumers.

Consumers invoke operations through:

```python
TotalsMaintenanceCoordinator
```

The coordinator owns the lifecycle of the maintenance operation.

---

# 32. Concurrent Movement Mutation

A full rebuild must not race with Movement mutation affecting the same Register.

For Step 6, the active mutation path must exclude or serialize concurrent Movement mutation for the Register until the rebuild has completed its publication boundary.

Step 6 does not introduce a concurrent-rebuild reconciliation protocol.

The following architecture is explicitly out of scope:

```text
rebuild
   +
concurrent Movement mutation
   +
delta reconciliation
   +
version merge
```

If such a mechanism is required in the future, it must be defined as a separate architectural step.

---

# 33. Rebuild Determinism

Given the same authoritative Movement Fact set and the same applicable Register definition, rebuild must produce the same semantic Totals state.

The result must not depend on:

* physical storage layout;
* storage provider implementation;
* runtime object identity;
* arbitrary iteration order;
* uncontrolled system time;
* external mutable state.

The Totals Engine's established deterministic aggregation semantics remain authoritative.

---

# 34. Incremental/Rebuild Equivalence

For the same authoritative Movement Fact set:

```text
incremental maintenance
```

and:

```text
full rebuild
```

must produce semantically equivalent Totals.

Conceptually:

```text
apply(M1)
apply(M2)
remove(M3)
...
```

must converge to the same derived state as:

```text
rebuild(register)
```

over the resulting authoritative Movement Fact set.

This is a fundamental correctness invariant.

---

# 35. Failure After Movement Persistence

A Movement persistence operation and Totals maintenance operation may cross a consistency boundary.

For example:

```text
1. Movement persisted
2. Totals maintenance fails
```

After step 1:

```text
authoritative Movement Facts = new state
```

After step 2:

```text
published Totals = potentially old state
```

The system must not incorrectly classify this as:

```text
ACTIVE + VALID
```

if the published Totals no longer represent the authoritative Movement Fact state.

The appropriate state may be:

```text
ACTIVE + INDETERMINATE
```

or:

```text
ACTIVE + RECOVERY_REQUIRED
```

depending on what the system can establish.

This is a semantic consistency boundary.

It does not require Step 6 to introduce a new generic transaction abstraction.

---

# 36. Recovery

Recovery always reconstructs from authoritative Movement Facts.

The recovery source is:

```text
RegisterFactPersistence
```

not:

```text
previous Totals
```

and not:

```text
compensating arithmetic
```

Recovery therefore follows the same authoritative path as rebuild.

---

# 37. Rebuild Failure

If rebuild fails before publication:

* the incomplete replacement state is discarded;
* the incomplete state is not exposed to Balance Query;
* the maintenance operation reports the appropriate failure or indeterminate outcome;
* the resulting consistency state reflects whether the current published Totals can still be considered valid;
* recovery remains possible through authoritative Movement Facts.

A failed rebuild must never publish partial totals.

---

# 38. Totals Validation

Validation of a candidate replacement state may be performed internally before publication.

An internal validator may verify:

* key validity;
* contribution aggregation invariants;
* absence of invalid negative/unsupported states where prohibited by the Totals contract;
* internal consistency;
* equivalence with the expected aggregation semantics.

The validator is not a public maintenance API.

---

# 39. Internal Rebuilder

An internal implementation component may encapsulate rebuild orchestration.

For example:

```text
TotalsRebuilder
```

may:

1. enumerate authoritative Movement Facts;
2. invoke the existing Totals Engine;
3. construct isolated replacement state;
4. validate it;
5. pass it to the publication boundary.

`TotalsRebuilder` is not a public API.

---

# 40. Internal Publisher

An internal component may encapsulate publication.

For example:

```text
TotalsPublisher
```

may be responsible for replacing the currently published derived state.

Its responsibility is limited to publication.

It must not expose generic operations such as:

```python
add(...)
subtract(...)
update(...)
```

as an alternative Totals API.

Aggregation remains the responsibility of the Totals Engine.

---

# 41. Balance Query Integration

Balance Query remains read-only.

Step 6 does not add:

```text
rebuild-on-read
repair-on-read
lazy-maintenance
```

behavior.

Balance Query must never mutate Totals.

If Totals are in a maintenance or recovery state, the behavior visible to Balance Query is determined by the existing Balance Query contract.

Step 6 must not silently change that contract.

---

# 42. Balance Query API Is Unchanged

Step 6 does not redefine:

* Balance Query request;
* Balance Query result;
* Totals read semantics;
* TotalsKey semantics;
* resource aggregation semantics;
* visibility rules already established by Step 5.

The purpose of Step 6 is to maintain the derived state consumed by Balance Query.

---

# 43. Posting Integration

Phase 6 Posting remains the owner of posting lifecycle semantics.

The conceptual integration is:

```text
Posting Handler
      │
      ▼
MovementSet
      │
      ▼
Movement Validation
      │
      ▼
Posting Result Coordination
      │
      ▼
Movement persistence
      │
      ▼
Totals maintenance
```

Posting Handlers do not directly manipulate Totals.

Posting Handlers do not know about:

* TotalsKey;
* TotalsPublisher;
* Totals maintenance state;
* Totals storage;
* maintenance locks.

---

# 44. PostingResultCoordinator

The existing Phase 6 `PostingResultCoordinator` remains the Posting integration boundary.

Conceptually:

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

Step 6 does not redefine this contract.

The Posting subsystem remains responsible for orchestrating the relationship between posting results and register effects.

---

# 45. Reposting

Reposting remains a Phase 6 Posting concern.

Conceptually:

```text
repost(document)
    │
    ├── remove previous Movement Facts
    │
    ├── generate new MovementSet
    │
    └── establish new posting result
```

Totals maintenance reacts to the resulting Movement Fact changes.

Step 6 does not introduce a second reposting mechanism.

---

# 46. Events

Step 6 does not introduce new public events such as:

```text
TotalsMaintenanceStarted
TotalsMaintenanceCompleted
TotalsMaintenanceFailed
TotalsRebuilt
TotalsRecovered
```

No event is required to establish the Step 6 maintenance contract.

If future event-driven maintenance requires such events, that must be defined as a separate architectural decision.

---

# 47. Persistence Error Integration

Step 6 reuses the existing persistence error hierarchy.

It does not introduce a parallel Totals persistence error hierarchy.

Existing persistence failures may include categories such as:

```text
PersistenceError
PersistenceNotFoundError
PersistenceAlreadyExistsError
PersistenceConflictError
PersistenceIntegrityError
PersistenceUnsupportedError
PersistenceFailure
PersistenceIndeterminateError
```

The maintenance layer maps expected infrastructure outcomes to `MaintenanceResult` where appropriate.

Exceptions remain available for violations of the established API or infrastructure contracts where the existing architecture requires them.

---

# 48. Error Outcome Principle

The following distinction is mandatory:

```text
expected operational outcome
        ↓
MaintenanceResult
```

versus:

```text
programming/API/invariant/infrastructure contract violation
        ↓
existing exception hierarchy
```

MaintenanceResult is not a generic replacement for exceptions.

---

# 49. Lifecycle Transition Model

The expected lifecycle is:

```text
CREATED
   │
   ▼
ACTIVE + VALID
   │
   │ maintenance
   ▼
MAINTENANCE
   │
   ├───────────────┐
   │               │
 success          failure
   │               │
   ▼               ▼
ACTIVE + VALID   appropriate
                 consistency
                 state
```

A recovery path is:

```text
ACTIVE + RECOVERY_REQUIRED
          │
          ▼
       recover()
          │
          ▼
       rebuild()
          │
          ▼
    validated replacement
          │
          ▼
    publish replacement
          │
          ▼
     ACTIVE + VALID
```

The actual implementation may use more granular internal transitions, but externally observable lifecycle and consistency semantics must preserve the contract above.

---

# 50. Public API Surface

The Step 6 public API consists of the following newly defined maintenance contracts:

```python
TotalsLifecycleState
TotalsConsistencyState
TotalsMaintenanceState
MaintenanceOutcome
MaintenanceOperation
MaintenanceResult
TotalsMaintenanceCoordinator
```

The following are not Step 6 public API additions:

```text
TotalsKey
TotalValue
TotalsEngine
TotalsReader
Movement
RegisterFactPersistence
MaintenanceGuard
MaintenanceLease
MaintenanceSession
TotalsPublisher
TotalsRebuilder
TotalsValidator
MovementContributionIdentity
```

The first group is the public Step 6 maintenance contract.

The second group consists of existing contracts or internal implementation concepts.

---

# 51. No Duplicate Totals Abstractions

Step 6 must not introduce duplicate abstractions for responsibilities already owned by earlier steps.

The following are explicitly prohibited as new public contracts:

```text
NewTotalsKey
TotalsStateReader
TotalsStore
MovementFactSource
TotalsFactRepository
PublishedTotalsReader
TotalsAggregationService
```

unless a future architectural step establishes a separate responsibility that cannot be satisfied by the existing contracts.

---

# 52. Implementation Module Placement

Step 6 may introduce a dedicated maintenance implementation module inside the existing Register architecture.

For example:

```text
register/
    ...
    maintenance.py
```

The exact repository placement remains an implementation decision subject to the existing source tree.

Step 6 does not require relocation of existing:

* Movement definitions;
* persistence definitions;
* Totals Engine implementation;
* Balance Query implementation.

Existing modules must not be moved solely to satisfy this document.

---

# 53. Internal Component Model

A concrete implementation may contain components conceptually equivalent to:

```text
TotalsMaintenanceCoordinator
        │
        ├── MaintenanceGuard
        │
        ├── TotalsRebuilder
        │       │
        │       └── RegisterFactPersistence
        │
        ├── existing TotalsEngine
        │
        ├── TotalsValidator
        │
        └── TotalsPublisher
```

These are implementation boundaries.

Only the Coordinator is the primary public maintenance mutation API.

---

# 54. No Generic Totals Store

Step 6 does not define:

```python
TotalsMaintenanceStore
```

or an equivalent generic persistence interface.

The authoritative Movement Facts already have a persistence contract.

Derived Totals publication remains an internal concern of the Totals implementation.

Introducing a generic Totals Store at this stage would duplicate persistence architecture without adding an independently justified contract.

---

# 55. Semantic Atomicity vs Physical Transaction

The Step 6 contract requires semantic atomicity of publication.

It does not require a particular physical transaction model.

Therefore:

```text
semantic publication boundary
```

must be specified independently from:

```text
database transaction implementation
```

The concrete storage provider may implement semantic publication using the mechanism appropriate to its capabilities.

---

# 56. Deterministic Maintenance

For the same:

* authoritative Movement Fact set;
* applicable Register definition;
* applicable Totals Engine configuration;

maintenance must produce the same semantic result.

Maintenance must not depend on:

* arbitrary collection ordering;
* physical storage order;
* process identity;
* runtime object identity;
* uncontrolled system clock;
* uncontrolled external state.

---

# 57. Architectural Invariants

The following invariants are mandatory.

### Invariant 1 — Authoritative Facts

Persisted Movement Facts are authoritative.

### Invariant 2 — Derived Totals

Totals are derived state.

### Invariant 3 — Rebuild Source

Rebuild always starts from authoritative Movement Facts.

### Invariant 4 — Single Aggregation Owner

The Totals Engine owns aggregation semantics.

### Invariant 5 — Single Maintenance Boundary

TotalsMaintenanceCoordinator owns public maintenance semantics.

### Invariant 6 — Idempotency

Apply, remove, rebuild and recover are idempotent.

### Invariant 7 — Contribution Identity

Distinct Movement Facts remain distinct even when their TotalsKey and contribution values are equal.

### Invariant 8 — Publication Isolation

Partial replacement Totals are never externally visible.

### Invariant 9 — Semantic Publication Atomicity

Consumers observe either the previous complete publication or the new complete publication.

### Invariant 10 — Recovery

Recovery reconstructs from authoritative Movement Facts.

### Invariant 11 — Balance Query Read-Only

Balance Query never performs maintenance.

### Invariant 12 — Posting Separation

Posting Handlers do not manipulate Totals directly.

### Invariant 13 — No Duplicate Persistence Boundary

Step 6 does not create a second authoritative Movement persistence abstraction.

### Invariant 14 — No Duplicate Totals Contract

Step 6 does not redefine TotalsKey, TotalValue, Totals Engine or Balance Query semantics.

### Invariant 15 — Consistency Honesty

The system must not represent stale published Totals as `VALID` when authoritative Movement Facts have advanced beyond the publication boundary.

---

# 58. Acceptance Criteria

Step 6 Concrete API Design is acceptable for implementation when all of the following are satisfied.

1. `TotalsMaintenanceCoordinator` is the primary public maintenance boundary.

2. `apply(movement)` is defined.

3. `remove(movement)` is defined.

4. `rebuild(register_identity)` is defined.

5. `recover(register_identity)` is defined.

6. Idempotency semantics are explicit.

7. Caller state flags are forbidden.

8. Movement Contribution Identity is defined as an internal semantic concept.

9. TotalsKey is reused from Step 4 rather than redefined.

10. TotalValue is reused from Step 4 rather than redefined.

11. Totals Engine remains the single owner of aggregation semantics.

12. RegisterFactPersistence remains the authoritative Movement Fact source.

13. Rebuild does not accept caller-provided Movement collections.

14. Replacement state is isolated from published state.

15. Partial rebuild state is never visible.

16. Publication is semantically atomic.

17. Lifecycle state is separated from consistency state.

18. `MaintenanceResult` distinguishes outcome from resulting consistency state.

19. Recovery is defined as reconstruction from authoritative facts.

20. Existing persistence error hierarchy is reused.

21. Balance Query API and semantics remain unchanged.

22. Posting lifecycle and Phase 6 Posting contracts remain unchanged.

23. Posting Handlers do not directly manipulate Totals.

24. No duplicate Totals persistence abstraction is introduced.

25. No new public Totals read abstraction is introduced.

26. No new Totals maintenance events are required.

27. Concurrent Movement mutation during full rebuild is excluded or serialized.

28. Incremental maintenance and full rebuild are semantically equivalent for the same authoritative fact set.

29. Deterministic maintenance semantics are preserved.

30. The API does not prescribe relocation of existing repository modules.

---

# 59. Final Architectural Boundary

The resulting architecture is:

```text
                 AUTHORITATIVE STATE
                         │
                         ▼
              RegisterFactPersistence
                         │
                         │ Movement Facts
                         ▼
             TotalsMaintenanceCoordinator
                         │
              ┌──────────┼──────────┐
              │          │          │
            apply      remove     rebuild
              │          │          │
              └──────────┼──────────┘
                         │
                         ▼
                 Existing Totals Engine
                       Step 4
                         │
                  TotalsKey / Value
                         │
                         ▼
                  Published Totals
                         │
                         ▼
                   Balance Query
                       Step 5
```

Recovery follows:

```text
Recovery Required
       │
       ▼
    recover()
       │
       ▼
    rebuild()
       │
       ▼
RegisterFactPersistence
       │
       ▼
 Existing Totals Engine
       │
       ▼
Validated Replacement
       │
       ▼
Semantic Publication
       │
       ▼
 Active + Valid
```

---

# 60. Architectural Statement

Phase 7 Step 6 establishes the lifecycle and maintenance boundary for Register Totals without changing the ownership model established by earlier steps.

The final ownership model is:

```text
Movement persistence
    → authoritative facts

Totals Engine
    → aggregation semantics and derived Totals

Totals Maintenance Coordinator
    → lifecycle, consistency, idempotency, recovery and publication orchestration

Balance Query
    → read-only access to the published derived state
```

The essential architectural rule is:

> Movement Facts are authoritative. Totals are derived. The existing Totals Engine owns aggregation semantics. The Totals Maintenance Coordinator owns lifecycle and maintenance orchestration. Balance Query only reads the published derived state.

Step 6 therefore extends the Register architecture without introducing a second Totals model, a second authoritative fact source, or a second Balance Query model.

---

# 61. Status

**Ready for Final Architecture Review.**
