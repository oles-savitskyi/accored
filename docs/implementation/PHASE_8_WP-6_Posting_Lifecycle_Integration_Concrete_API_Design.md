# AcCoreD — Phase 8 WP-6

# Posting Lifecycle Integration — Concrete API Design

**Status:** Approved Concrete API Design
**Phase:** 8 — Valuation
**Work Package:** WP-6 — Posting Lifecycle Integration
**Depends on:** WP-5 Final Architecture and API
**Implementation:** Implemented and verified

---

# 1. Purpose

This document translates the approved WP-6 Final Architecture into concrete Python API contracts.

It defines:

* `PostingResultPlan`;
* `PostingResultCoordinator`;
* register preparation integration;
* valuation posting adapter;
* valuation lifecycle removal/reversal;
* composite result coordination;
* lifecycle outcome types;
* repost failure semantics;
* exception boundaries;
* concrete operation ordering;
* public exports;
* testing obligations.

The design intentionally does not introduce new valuation algorithms.

---

# 2. Existing Integration Points

The existing posting architecture contains:

```text
PostingEngine
    ↓
PostingResultCoordinator
    ↓
RegisterPostingResultCoordinator
```

The existing coordinator currently exposes:

```python
establish(document, movement_set)
remove(document)
```

WP-6 evolves this boundary rather than introducing a second posting lifecycle abstraction.

The valuation side already contains:

```text
ValuationEngine.prepare()
        ↓
ValuationPlan

ValuationCoordinator.establish()
        ↓
ValuationEstablishmentResult
```

WP-6 adds the missing lifecycle reversal boundary and adapts valuation into the generic posting-result lifecycle.

---

# 3. Generic Result Plan

## 3.1 `PostingResultPlan`

`PostingResultPlan` is an immutable aggregate containing the domain-specific prepared plans required for establishment.

The concrete representation is:

```python
@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    register: RegisterPostingPlan
    valuation: ValuationPlan
```

The plan is created exclusively by:

```python
PostingResultCoordinator.prepare(...)
```

and consumed exclusively by:

```python
PostingResultCoordinator.establish(..., plan)
```

---

## 3.2 Plan ownership

`PostingResultPlan` is an orchestration-level object.

It does not contain:

* persisted register movements;
* persisted valuation facts;
* mutable lifecycle state;
* database/session objects;
* coordinator references.

It contains only immutable prepared state.

---

## 3.3 Domain plan ownership

Each domain owns its internal plan type.

```text
PostingResultPlan
├── RegisterPostingPlan
└── ValuationPlan
```

`PostingEngine` must not inspect either child plan.

`CompositePostingResultCoordinator` may pass the child plans to their respective domain coordinators.

---

# 4. Register Posting Plan

The register domain requires a concrete preparation boundary even though its current establishment operation is comparatively simple.

The API is:

```python
@dataclass(frozen=True, slots=True)
class RegisterPostingPlan:
    movements: tuple[Movement, ...]
```

The plan contains the exact register movements that will be established.

No register persistence occurs during preparation.

The plan therefore makes register establishment explicit without introducing additional domain semantics.

---

# 5. Posting Result Coordinator

The generic public contract becomes:

```python
class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> PostingResultPlan:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> PostingResultEstablishmentResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> PostingResultRemovalResult:
        ...
```

The return types are lifecycle results rather than `None`.

This is necessary because the composite coordinator must preserve deterministic failure and indeterminate persistence outcomes.

---

# 6. Preparation Contract

`prepare()` is:

* deterministic;
* non-persistent;
* non-destructive;
* side-effect free with respect to authoritative posting state.

Conceptually:

```python
plan = coordinator.prepare(document, movement_set)
```

Successful preparation guarantees:

> the supplied plan is valid for the corresponding establishment operation, subject to persistence outcomes occurring during establishment.

Preparation does not guarantee establishment success.

---

# 7. Preparation Failure

Deterministic preparation errors are raised rather than represented as successful plans.

Examples include:

```text
Invalid movement set
Invalid valuation input
Insufficient valuation source state
Invalid FIFO transition
Invalid plan construction
```

No `PostingResultPlan` is returned for a failed preparation.

The posting engine therefore cannot proceed to removal during repost.

---

# 8. Establishment Result

The result type is:

```python
class PostingResultEstablishmentState(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    INDETERMINATE = auto()


@dataclass(frozen=True, slots=True)
class PostingResultEstablishmentResult:
    state: PostingResultEstablishmentState
```

The result represents the aggregate outcome of establishing all configured posting-result domains.

---

# 9. Removal Result

The removal result is separate from establishment:

```python
class PostingResultRemovalState(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    INDETERMINATE = auto()


@dataclass(frozen=True, slots=True)
class PostingResultRemovalResult:
    state: PostingResultRemovalState
```

The distinction is intentional.

Removal is not establishment with a negative flag.

---

# 10. Valuation Lifecycle API

The valuation lifecycle contract becomes:

```python
class ValuationLifecycleCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...

    def remove(
        self,
        document_identity: Identifier,
    ) -> ValuationRemovalResult:
        ...
```

`establish()` consumes an immutable prepared `ValuationPlan`.

`remove()` identifies an already-established valuation result and establishes its compensating reversal.

---

# 11. Valuation Removal Result

The valuation removal result is:

```python
class ValuationRemovalState(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    INDETERMINATE = auto()


@dataclass(frozen=True, slots=True)
class ValuationRemovalResult:
    state: ValuationRemovalState
```

The semantic meaning is:

### `SUCCESS`

The existing valuation effect has been successfully reversed.

### `FAILURE`

The operation failed and the persistence boundary guarantees rollback.

### `INDETERMINATE`

The operation may have partially completed and persistence cannot guarantee rollback.

---

# 12. Valuation Reversal Semantics

`ValuationLifecycleCoordinator.remove()` must never delete historical valuation facts.

The operation is:

```text
find established valuation effect
        ↓
derive compensating valuation facts
        ↓
persist compensating facts
        ↓
apply compensating cost movements
        ↓
maintain cost balances
```

The original valuation facts remain immutable.

---

# 13. Valuation Posting Adapter

The concrete adapter is:

```python
class ValuationPostingCoordinator:
    def __init__(
        self,
        engine: ValuationEngine,
        lifecycle: ValuationLifecycleCoordinator,
    ) -> None:
        ...
```

Responsibilities:

### `prepare()`

```python
valuation_plan = engine.prepare(movement_set)
```

and returns the valuation component of `PostingResultPlan`.

### `establish()`

Delegates:

```python
lifecycle.establish(plan)
```

### `remove()`

Delegates:

```python
lifecycle.remove(document.identity)
```

The adapter does not implement FIFO or valuation persistence.

---

# 14. Composite Coordinator

The concrete coordinator is:

```python
class CompositePostingResultCoordinator:
    def __init__(
        self,
        register: RegisterPostingResultCoordinator,
        valuation: ValuationPostingCoordinator,
    ) -> None:
        ...
```

It implements the generic posting-result lifecycle.

---

# 15. Composite Preparation

The composite preparation sequence is:

```text
MovementSet
    │
    ├── Register.prepare()
    │
    └── Valuation.prepare()
    │
    ▼
PostingResultPlan
```

Concrete behavior:

```python
register_plan = register.prepare(document, movement_set)
valuation_plan = valuation.prepare(document, movement_set)

return PostingResultPlan(
    register=register_plan,
    valuation=valuation_plan,
)
```

No persistence is permitted during either preparation operation.

If either preparation fails, the composite operation fails and no plan is returned.

---

# 16. Preparation Ordering

The concrete ordering is:

```text
Register prepare
        ↓
Valuation prepare
        ↓
PostingResultPlan
```

Register preparation must remain non-authoritative.

Valuation preparation must remain non-authoritative.

The architecture therefore obtains all deterministic preparation before any existing result is removed.

---

# 17. Composite Establishment

The establishment order is:

```text
Register establish
        ↓
Valuation establish
```

The rationale is to preserve the existing operational posting semantics while adding valuation as the downstream result domain.

Concrete operation:

```python
register_result = register.establish(
    document,
    movement_set,
    plan.register,
)

if register_result.state is not SUCCESS:
    return aggregate_register_failure(register_result)

valuation_result = valuation.establish(
    document,
    movement_set,
    plan.valuation,
)

return aggregate_results(
    register_result,
    valuation_result,
)
```

The exact aggregate failure mapping is defined in Section 22.

---

# 18. Composite Removal

The concrete removal order is:

```text
Register remove
        ↓
Valuation remove
```

This is the inverse lifecycle order of establishment.

The operation is:

```python
register_result = register.remove(document)

if register_result.state is not SUCCESS:
    return aggregate_register_removal_failure(register_result)

valuation_result = valuation.remove(document.identity)

return aggregate_removal_results(
    register_result,
    valuation_result,
)
```

The new result must not be established by `PostingEngine` if removal does not complete successfully.

---

# 19. Why Removal Is Not Automatically Compensated

WP-6 does not introduce automatic cross-domain rollback.

For example:

```text
Register.remove()
    SUCCESS

Valuation.remove()
    INDETERMINATE
```

must not be silently converted into:

```text
Register.remove()
    SUCCESS
Register.restore()
    ...
```

because that would constitute a new distributed recovery protocol.

The composite coordinator reports the resulting lifecycle state.

Recovery remains a separate concern.

---

# 20. PostingEngine POST API

The posting engine changes from:

```python
coordinator.establish(document, movement_set)
```

to:

```python
plan = coordinator.prepare(document, movement_set)

result = coordinator.establish(
    document,
    movement_set,
    plan,
)
```

The engine does not inspect the plan.

---

# 21. PostingEngine REPOST API

The concrete repost lifecycle becomes:

```python
plan = coordinator.prepare(document, movement_set)

removal = coordinator.remove(document)

if removal.state is not PostingResultRemovalState.SUCCESS:
    raise map_removal_failure(removal)

establishment = coordinator.establish(
    document,
    movement_set,
    plan,
)

handle_repost_establishment(establishment)

publish(DocumentReposted(...))
```

The critical ordering invariant is:

```text
prepare(new)
    ↓
remove(old)
    ↓
establish(new)
```

---

# 22. Repost Failure Taxonomy

The API distinguishes three categories.

## 22.1 Preparation failure

State:

```text
old result: unchanged
new result: absent
```

This is a deterministic posting failure.

No event is emitted.

---

## 22.2 Removal failure

State:

```text
old result: not known to be reversed successfully
new result: absent
```

No new establishment is attempted.

No event is emitted.

---

## 22.3 Removal indeterminate

State:

```text
old result: indeterminate
new result: absent
```

No new establishment is attempted.

The posting lifecycle raises an indeterminate posting error.

---

## 22.4 Removal successful, establishment failed

State:

```text
old result: reversed
new result: absent
```

This is **not** the same as preparation failure.

A dedicated lifecycle error/result is required.

---

## 22.5 Removal successful, establishment indeterminate

State:

```text
old result: reversed
new result: indeterminate
```

This is the strongest failure condition.

The API must expose this state explicitly.

---

# 23. Lifecycle Failure Type

The concrete posting layer introduces:

```python
class PostingLifecycleError(PostingError):
    ...
```

with specialized semantic categories:

```python
class PostingLifecycleFailure(Enum):
    PREPARATION_FAILED = auto()
    REMOVAL_FAILED = auto()
    REMOVAL_INDETERMINATE = auto()
    ESTABLISHMENT_FAILED_AFTER_REMOVAL = auto()
    ESTABLISHMENT_INDETERMINATE_AFTER_REMOVAL = auto()
```

A lifecycle error carries the relevant failure category.

The API must not collapse all failures into the existing generic posting handler/persistence errors.

---

# 24. Establishment Aggregate Result

The aggregate result must preserve both domain outcomes when required.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class PostingResultEstablishmentResult:
    register: RegisterEstablishmentResult
    valuation: ValuationEstablishmentResult
    state: PostingResultEstablishmentState
```

Likewise:

```python
@dataclass(frozen=True, slots=True)
class PostingResultRemovalResult:
    register: RegisterRemovalResult
    valuation: ValuationRemovalResult
    state: PostingResultRemovalState
```

The exact register-specific result types may reuse the existing maintenance/mutation outcome model where appropriate.

---

# 25. Result Aggregation Rules

Aggregation follows this precedence:

```text
INDETERMINATE
    >
FAILURE
    >
SUCCESS
```

Therefore:

```text
SUCCESS + SUCCESS
    → SUCCESS

SUCCESS + FAILURE
    → FAILURE

SUCCESS + INDETERMINATE
    → INDETERMINATE

FAILURE + anything
    → FAILURE unless another operation is already indeterminate

INDETERMINATE + anything
    → INDETERMINATE
```

This prevents an indeterminate persistence state from being downgraded to deterministic failure or success.

---

# 26. Domain Exception Mapping

Domain-specific exceptions remain inside their domain adapters.

Examples:

```text
ValuationPersistenceError
ValuationEstablishmentError
ValuationRemovalError
RegisterMutationError
RegisterPersistenceError
```

are not exposed directly by `PostingEngine` unless they already belong to the public posting error contract.

The adapter maps domain failures into lifecycle results.

Unexpected programming errors are not converted into domain failure results.

---

# 27. Preparation Exceptions

Preparation exceptions remain deterministic.

For valuation:

```text
ValuationEngine.prepare()
    ↓
ValuationError
```

is propagated/mapped as a deterministic posting preparation failure.

No persistence compensation is required because preparation has not modified authoritative state.

---

# 28. Valuation Establishment Reuse

`DefaultValuationCoordinator.establish(plan)` remains the authoritative valuation establishment implementation.

WP-6 must not duplicate its internal logic.

The existing sequence remains conceptually:

```text
validate ValuationPlan
    ↓
construct valuation facts
    ↓
persist facts
    ↓
construct cost movements
    ↓
persist movements
    ↓
apply cost balances
    ↓
return ValuationEstablishmentResult
```

The only new concern is exposing it through the lifecycle adapter.

---

# 29. Valuation Removal Implementation Boundary

The removal implementation must be introduced at the valuation lifecycle layer, not inside `ValuationEngine`.

`ValuationEngine` remains a preparation/calculation component.

Therefore:

```text
ValuationEngine
    prepare()

ValuationLifecycleCoordinator
    establish()
    remove()
```

This prevents lifecycle persistence/reversal semantics from contaminating the deterministic valuation engine.

---

# 30. Removal Lookup Boundary

`remove(document)` uses document identity as the lifecycle key.

The valuation lifecycle coordinator is responsible for resolving the established valuation effect associated with that identity.

It must not require `MovementSet` for removal because removal operates on the already-established historical result rather than recalculating the new result.

---

# 31. Compensating Valuation Facts

The concrete implementation must represent reversal using a dedicated semantic representation.

The preferred API shape is:

```python
@dataclass(frozen=True, slots=True)
class ValuationReversal:
    source_document_identity: Identifier
    original_fact_identity: Identifier
    compensating_facts: tuple[ValuationFact, ...]
```

The exact final structure may be simplified if the existing persistence model already provides equivalent identity linkage.

The essential invariant is that the reversal retains traceability to the original valuation effect.

---

# 32. No Historical Mutation

The implementation must not introduce methods such as:

```python
delete_fact(...)
update_fact(...)
```

for ordinary posting reversal.

Historical valuation facts remain append-only.

---

# 33. Persistence Requirements

WP-6 may extend valuation persistence interfaces only where required to support lifecycle reversal.

Required capabilities are conceptually:

```text
find valuation facts by source document
find established valuation movements by source document
append compensating valuation facts
append compensating cost movements
maintain/recalculate derived balances
```

Existing `CostTotalsEngine.remove()` and `rebuild()` semantics may be reused where appropriate.

The Concrete API implementation must not bypass the existing persistence abstractions.

---

# 34. Public API Placement

The proposed modules are:

```text
src/accore/platform/posting/
    coordinator.py
    engine.py
    plans.py
    results.py
    composite_coordinator.py
```

Valuation:

```text
src/accore/platform/valuation/
    coordinator.py
    lifecycle.py
    plans.py
    results.py
    reversal.py
```

The exact filenames may follow the existing package structure where an equivalent module already exists.

The important requirement is that generic posting contracts remain in the posting package and valuation-specific contracts remain in the valuation package.

---

# 35. Public Exports

The posting package should publicly expose:

```python
PostingResultCoordinator
PostingResultPlan
PostingResultEstablishmentResult
PostingResultRemovalResult
PostingResultEstablishmentState
PostingResultRemovalState
CompositePostingResultCoordinator
```

The valuation package should publicly expose the lifecycle contract and result types required by external composition:

```python
ValuationLifecycleCoordinator
ValuationRemovalResult
ValuationRemovalState
ValuationReversal
```

Internal implementation classes remain private unless already part of the public API.

---

# 36. Compatibility Strategy

The API change intentionally replaces the existing two-method coordinator boundary.

The old contract:

```python
establish(document, movement_set)
remove(document)
```

becomes:

```python
prepare(document, movement_set)
establish(document, movement_set, plan)
remove(document)
```

No compatibility shim should preserve the old lifecycle internally while the new architecture is being implemented.

The implementation should migrate all in-repository callers and tests to the final contract in one coherent change.

---

# 37. Test Contract — Preparation

Tests must prove:

1. register preparation is deterministic;
2. valuation preparation is deterministic;
3. preparation performs no authoritative persistence;
4. preparation produces immutable plans;
5. a failed valuation preparation produces no posting plan;
6. a failed preparation leaves existing posting state untouched.

---

# 38. Test Contract — Establishment

Tests must prove:

1. the supplied plan is used;
2. valuation FIFO is not recalculated during establishment;
3. register and valuation establishment receive their respective child plans;
4. successful establishment returns `SUCCESS`;
5. deterministic persistence failure returns `FAILURE`;
6. non-rollback-guaranteed persistence failure returns `INDETERMINATE`.

---

# 39. Test Contract — Removal

Tests must prove:

1. register removal remains functional;
2. valuation removal does not delete historical facts;
3. valuation removal creates compensating facts;
4. derived valuation state is correctly reversed;
5. deterministic rollback failure is reported as `FAILURE`;
6. non-guaranteed rollback is reported as `INDETERMINATE`.

---

# 40. Test Contract — Repost

At minimum:

```text
prepare(new) fails
    → old remains unchanged

prepare(new) succeeds
remove(old) fails
    → new not established

prepare(new) succeeds
remove(old) indeterminate
    → new not established

prepare(new) succeeds
remove(old) succeeds
establish(new) succeeds
    → DocumentReposted

prepare(new) succeeds
remove(old) succeeds
establish(new) fails
    → old reversed, new absent

prepare(new) succeeds
remove(old) succeeds
establish(new) indeterminate
    → old reversed, new indeterminate
```

These cases are mandatory because they define the core safety semantics of WP-6.

---

# 41. Integration Test

A complete integration test must exercise:

```text
Operational document
    ↓
Posting handler
    ↓
MovementSet
    ↓
Register preparation
    ↓
Valuation preparation
    ↓
PostingResultPlan
    ↓
Register establishment
    ↓
Valuation establishment
    ↓
DocumentPosted
```

and then:

```text
Updated operational document
    ↓
New MovementSet
    ↓
New preparation
    ↓
Old result removal
    ↓
Valuation compensation
    ↓
New result establishment
    ↓
DocumentReposted
```

The final assertions must verify both:

* register state;
* valuation state.

---

# 42. Architectural Non-Goals Preserved

This API design does not introduce:

* distributed transactions;
* 2PC;
* hidden pending plans;
* valuation logic in `PostingEngine`;
* register logic in `ValuationEngine`;
* mutation of historical valuation facts;
* recalculation of valuation during establishment;
* automatic recovery after indeterminate cross-domain state.

---

# 43. Concrete API Decision Summary

The final proposed API is:

```python
class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> PostingResultPlan:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> PostingResultEstablishmentResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> PostingResultRemovalResult:
        ...
```

with:

```python
@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    register: RegisterPostingPlan
    valuation: ValuationPlan
```

and valuation lifecycle:

```python
class ValuationLifecycleCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...

    def remove(
        self,
        document_identity: Identifier,
    ) -> ValuationRemovalResult:
        ...
```

The lifecycle is:

```text
POST
    prepare
      ↓
    establish
      ↓
    DocumentPosted
```

and:

```text
REPOST
    prepare(new)
      ↓
    remove(old)
      ↓
    establish(new, plan)
      ↓
    DocumentReposted
```

with the mandatory invariant:

```text
prepare(new) failure
    ⇒ remove(old) is never called
```

and the explicit post-removal failure states:

```text
remove(old) SUCCESS
    +
establish(new) FAILURE
    ⇒ old reversed / new absent
```

```text
remove(old) SUCCESS
    +
establish(new) INDETERMINATE
    ⇒ old reversed / new indeterminate
```

---

# 44. Implementation Gate

Implementation may begin only after approval of this Concrete API Design.

Upon approval, implementation should proceed in this order:

1. generic posting plan/result contracts;
2. register coordinator adaptation;
3. valuation lifecycle removal/reversal API;
4. valuation posting adapter;
5. composite coordinator;
6. `PostingEngine` POST/REPOST integration;
7. unit tests;
8. integration tests;
9. quality gate;
10. documentation reconciliation;
11. final review;
12. separate WP-6 implementation commit.

No implementation detail outside this API should be decided implicitly during coding.
