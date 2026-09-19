# Phase 7 — Step 6.3

# Register Mutation / Totals Consistency Boundary

## Concrete API Design

**Status:** Final
**Phase:** Phase 7 — Registers
**Step:** 6.3
**Depends on:**

* `PHASE_7_STEP_6_LIFECYCLE_MAINTENANCE_ARCHITECTURE_DEFINITION.md`
* `PHASE_7_STEP_6_LIFECYCLE_MAINTENANCE_CONTRACT.md`
* `PHASE_7_STEP_6_CONCRETE_API_DESIGN.md`
* `PHASE_7_STEP_6.3_REGISTER_MUTATION_TOTALS_CONSISTENCY_BOUNDARY_ARCHITECTURE_DEFINITION.md`
* `PHASE_7_STEP_6.3_REGISTER_MUTATION_TOTALS_CONSISTENCY_BOUNDARY_CONTRACT.md`
* Phase 6 Posting architecture and Posting Result integration contracts
* Existing Register Fact Persistence API
* Existing Step 6.2 Totals Maintenance Coordinator API

---

# 1. Purpose

This document defines the concrete API and implementation structure for the Step 6.3 Register Mutation / Totals Consistency Boundary.

Step 6.3 introduces a Register-scoped logical operation domain that coordinates:

* authoritative Movement Fact persistence;
* Totals maintenance;
* Totals rebuild;
* Totals recovery;
* concurrent access to the same Register.

The purpose is to ensure that operations which can affect the consistency relationship between authoritative Movement Facts and derived Totals execute within the same Register-scoped operation boundary.

This document translates the approved Step 6.3 architecture and contract into concrete Python-level interfaces and implementation responsibilities.

---

# 2. Architectural Principle

The central rule is:

> All operations that can change the relationship between authoritative Movement Facts and derived Totals for a given Register must execute within the same Register Operation Domain.

The domain is a logical orchestration boundary.

It is **not**:

* a database transaction;
* a persistence transaction;
* a Totals store;
* a distributed transaction coordinator;
* a replacement for `RegisterFactPersistence`;
* a replacement for `TotalsMaintenanceCoordinator`;
* a Posting lifecycle manager.

The implementation may use a process-local synchronization primitive internally, but:

> Logical Operation Domain ≠ Synchronization Primitive.

The synchronization mechanism is an implementation detail of the logical domain.

---

# 3. Scope

Step 6.3 concretely introduces:

1. an internal `RegisterOperationDomain`;
2. an internal `RegisterOperationDomainRegistry`;
3. a semantic `RegisterMutationOrchestrator`;
4. a shared Register-scoped coordination path for:

   * Movement establishment;
   * Movement removal;
   * Totals rebuild;
   * Totals recovery;
5. deterministic acquisition support for operations involving multiple Registers, only where such a use case actually exists.

Step 6.3 does not introduce:

* a new persistence abstraction;
* a new Totals persistence model;
* persistent idempotency state;
* an event-driven synchronization mechanism;
* asynchronous Totals maintenance;
* distributed locking;
* distributed transactions;
* a new Posting lifecycle;
* a new Posting engine.

---

# 4. Existing APIs Reused

Step 6.3 must build on the existing Phase 7 and Phase 6 APIs.

The implementation must not duplicate concepts already established by Step 6.2.

In particular, Step 6.3 reuses:

* `Movement`;
* `Identifier`;
* `RegisterFactPersistence`;
* `TotalsMaintenanceCoordinator`;
* `MaintenanceResult`;
* `MaintenanceOutcome`;
* Totals lifecycle state;
* Totals consistency state;
* Step 6.2 failure semantics;
* Step 6.2 rebuild semantics;
* Phase 6 `PostingResultCoordinator`.

The new orchestration layer coordinates these existing components.

It does not redefine them.

---

# 5. Existing Movement Persistence Boundary

The existing persistence boundary remains authoritative.

Conceptually:

```text
RegisterFactPersistence
        │
        │ authoritative Movement Facts
        ▼
Movement persistence
```

The persistence component remains responsible for:

* storing Movement Facts;
* removing Movement Facts;
* enumerating Movement Facts;
* finding Movement Facts using its existing API;
* reporting persistence failures.

It does not become responsible for Totals.

Step 6.3 must not add Totals responsibilities to `RegisterFactPersistence`.

---

# 6. Existing Totals Maintenance Boundary

The existing Totals Maintenance Coordinator remains responsible for:

* applying Movement contributions to Totals;
* removing Movement contributions;
* rebuilding Totals from authoritative Movement Facts;
* recovering Totals;
* maintaining Totals lifecycle and consistency state;
* maintaining its runtime `_applied` state;
* reporting Totals maintenance failures.

It does not become responsible for Movement persistence.

Step 6.3 provides orchestration around the existing coordinator.

---

# 7. Public Semantic Boundary

The principal semantic API introduced by Step 6.3 is:

```text
RegisterMutationOrchestrator
```

This is the application-facing mutation boundary.

The intended dependency direction is:

```text
PostingResultCoordinator
        │
        ▼
RegisterMutationOrchestrator
        │
        ├── RegisterOperationDomain
        │
        ├── RegisterFactPersistence
        │
        └── TotalsMaintenanceCoordinator
```

Application code must not need to acquire or manipulate a `RegisterOperationDomain` directly.

This prevents bypassing the consistency boundary.

---

# 8. Internal Register Operation Domain

## 8.1 Responsibility

`RegisterOperationDomain` represents the logical operation boundary for exactly one Register.

Conceptually:

```python
class RegisterOperationDomain:
    register_identity: Identifier

    def execute(self, operation: Callable[[], T]) -> T:
        ...
```

The exact concrete typing may use an internal generic implementation.

The important semantic property is:

> One domain instance represents one Register-scoped operation domain.

---

# 9. Domain Identity

Each `RegisterOperationDomain` is associated with exactly one:

```text
register_identity
```

The domain must reject or otherwise prevent execution of operations that belong to another Register.

The domain therefore has a stable identity relationship:

```text
Register Identity
        │
        ▼
Register Operation Domain
```

Different Registers have different operation domains.

---

# 10. Synchronization Implementation

The initial implementation may use:

```python
threading.RLock
```

internally.

The reason for using `RLock` rather than `Lock` is implementation-level reentrancy between internal orchestration paths.

However:

> Reentrancy is not part of the public semantic contract.

The API must not expose the lock itself.

The API must not require callers to understand the locking primitive.

The API must not document `RLock` behavior as application-level semantics.

---

# 11. Domain Execution

The internal domain may expose:

```python
execute(operation: Callable[[], T]) -> T
```

The result of the callback is returned directly.

There is no wrapper result.

For example:

```python
result = domain.execute(operation)
```

returns exactly the result produced by `operation`.

This mechanism is internal infrastructure.

Application code should normally reach it indirectly through `RegisterMutationOrchestrator`.

---

# 12. Domain Registry

The implementation requires stable reuse of the same operation domain for a Register.

An internal:

```text
RegisterOperationDomainRegistry
```

provides this association.

Conceptually:

```python
class RegisterOperationDomainRegistry:
    def get(
        self,
        register_identity: Identifier,
    ) -> RegisterOperationDomain:
        ...
```

The registry guarantees:

```text
same Register Identity
        ↓
same domain instance
```

for the lifetime of the registry.

---

# 13. Registry Visibility

`RegisterOperationDomainRegistry` is internal infrastructure.

It is not a public application API.

It must not be exported as part of the ordinary Registers public surface.

The registry exists so that all relevant components receive the same Register-scoped domain.

The intended construction model is:

```text
Composition Root
        │
        ├── RegisterOperationDomainRegistry
        │
        ├── TotalsMaintenanceCoordinator
        │
        └── RegisterMutationOrchestrator
```

The same registry instance is injected into the relevant orchestration components.

---

# 14. Registry Synchronization

The registry itself requires a small synchronization mechanism for first-use domain creation.

This synchronization must protect only:

```text
identity → domain instance creation
```

It must not serialize Register operations.

Therefore:

```text
Registry creation lock
        ≠
Register operation lock
```

Once a domain exists, operations for that Register use its own domain.

Operations for different Registers remain independently executable.

---

# 15. Register Isolation

For Registers:

```text
R1
R2
R3
```

the implementation creates:

```text
Domain(R1)
Domain(R2)
Domain(R3)
```

Operations against different Registers must not require a single global Register lock.

Therefore:

```text
R1 operation ──> Domain(R1)

R2 operation ──> Domain(R2)

R3 operation ──> Domain(R3)
```

may proceed concurrently.

The design must not introduce a process-wide global lock around all Register operations.

---

# 16. Register Mutation Orchestrator

The semantic orchestration API is:

```text
RegisterMutationOrchestrator
```

Its responsibility is to coordinate authoritative Movement mutation and corresponding Totals maintenance within the same Register Operation Domain.

Conceptually:

```python
class RegisterMutationOrchestrator:
    def establish(
        self,
        movements: Sequence[Movement],
    ) -> None:
        ...

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
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

The exact concrete class name and constructor signature must follow the repository's existing naming conventions.

The semantic responsibilities above are normative.

---

# 17. `establish()` Return Semantics

`establish()` returns:

```python
None
```

It does not introduce a new `MutationResult`.

The reason is architectural consistency with the existing Phase 6 Posting Result boundary:

```python
PostingResultCoordinator.establish(...) -> None
```

Failure is communicated through existing persistence and Totals exceptions.

Step 6.3 must not introduce a second result model that duplicates:

* `MaintenanceOutcome`;
* `MaintenanceResult`;
* persistence exceptions.

---

# 18. `remove()` Return Semantics

`remove()` also returns:

```python
None
```

The existing Step 6.2 and persistence APIs define the relevant failure behavior.

Step 6.3 coordinates them without introducing a new result abstraction.

---

# 19. Establish Input Invariant

`establish()` accepts a sequence of Movements.

All Movements in one call must belong to the same Register.

Conceptually:

```text
M1.register_identity == R
M2.register_identity == R
M3.register_identity == R
```

is valid.

But:

```text
M1.register_identity == R1
M2.register_identity == R2
```

is invalid for one `establish()` call.

Mixed-register input must be rejected rather than silently grouped.

This preserves the semantic boundary:

> One `RegisterMutationOrchestrator` operation is a single-Register operation.

---

# 20. Empty Establishment

An empty Movement sequence is a successful no-op.

However:

> An empty mutation must not establish `ACTIVE + VALID`.

In particular:

```text
establish(())
```

must not be interpreted as proof that Totals correspond to authoritative Movement Facts.

The operation therefore does not replace the bootstrap/rebuild requirement.

---

# 21. Establish Operation Boundary

For a valid single-Register Movement sequence:

```text
Register Operation Domain
        │
        ├── persist Movements
        │
        └── apply corresponding Totals
```

The domain must be acquired before either operation begins.

The domain must remain held until both logical steps have completed.

Conceptually:

```python
domain.execute(
    lambda: (
        persistence.append(movements),
        totals.apply(movements),
    )
)
```

The actual implementation must use explicit readable code rather than relying on tuple-expression sequencing.

---

# 22. Establish Ordering

The authoritative persistence operation occurs before Totals application:

```text
1. Movement persistence
2. Totals maintenance
```

This ordering reflects the authority model:

```text
Movement Facts = authoritative
Totals = derived
```

Step 6.3 does not claim that these two operations form an atomic storage transaction.

If persistence succeeds and Totals maintenance fails:

```text
Movement Facts exist
Totals are not known to be valid
```

The resulting Totals state must preserve Step 6.2 failure semantics, normally requiring recovery or remaining indeterminate.

---

# 23. Persistence Failure During Establishment

If Movement persistence fails before the Movement mutation is established:

```text
persistence failure
        ↓
do not apply corresponding Totals
```

No Totals contribution may be established for a Movement that was not successfully persisted.

Existing persistence exceptions remain authoritative.

No new generic `RegisterMutationError` is introduced unless implementation evidence demonstrates that the existing exception model cannot preserve the required semantics.

---

# 24. Persistence Indeterminate During Establishment

If persistence reports an indeterminate outcome, the orchestrator must not claim successful consistency.

Conceptually:

```text
Persistence outcome = INDETERMINATE
        ↓
ACTIVE + VALID cannot be established
```

The system must preserve the possibility that the authoritative Movement mutation may have occurred.

The subsequent recovery path is determined by existing persistence and Totals error semantics.

---

# 25. Totals Failure During Establishment

If:

```text
persistence succeeds
Totals maintenance fails
```

then:

```text
Movement Facts remain authoritative
Totals are not valid
```

The Totals lifecycle/consistency state must follow Step 6.2 semantics.

Step 6.3 does not compensate by deleting successfully persisted Movement Facts.

The recovery mechanism is Totals rebuild/recovery from authoritative Movement Facts.

---

# 26. Removal

Movement removal follows the same Register Operation Domain.

Conceptually:

```text
Register Operation Domain
        │
        ├── determine required existing Movement data
        │
        ├── remove authoritative Movement Facts
        │
        └── remove corresponding Totals contribution
```

The exact data-loading sequence must follow the existing Step 6.2 `remove()` API and the existing persistence API.

Step 6.3 must not introduce a new Movement lookup abstraction merely to support removal.

If existing Totals removal requires the complete `Movement`, the orchestrator may obtain that Movement through the existing persistence API before removal.

The implementation must use the actual existing Step 6.2 and persistence contracts rather than reconstructing Movement data independently.

---

# 27. Removal Failure Semantics

The same distinction applies to removal:

### Persistence fails before mutation

Do not remove the corresponding Totals contribution.

### Persistence outcome is indeterminate

Do not claim Totals consistency.

### Persistence succeeds but Totals removal fails

Movement Facts remain authoritative and Totals become non-valid/recovery-required according to Step 6.2 semantics.

The orchestrator must not invent compensating persistence behavior.

---

# 28. Rebuild

`rebuild()` reuses the existing Step 6.2 rebuild contract.

The Step 6.3 addition is synchronization of the complete rebuild operation.

The critical sequence is:

```text
Acquire Register Operation Domain
        │
        ▼
Enumerate authoritative Movement Facts
        │
        ▼
Rebuild Totals
        │
        ▼
Reconstruct runtime maintenance state
        │
        ▼
Publish successful state
        │
        ▼
Release Register Operation Domain
```

---

# 29. Rebuild Domain Boundary

The Register Operation Domain must be acquired:

> before authoritative Movement enumeration begins.

It must remain held:

> through completion and publication of the rebuilt Totals state.

This is the central concurrency guarantee of Step 6.3.

The following is invalid:

```text
acquire domain
enumerate
release domain
rebuild Totals
```

because a Movement mutation could occur between enumeration and publication.

The required boundary is:

```text
acquire
    enumerate
    rebuild
    publish
release
```

---

# 30. Stable Rebuild Input

While the rebuild operation owns the Register Operation Domain:

* no coordinated Movement establishment for that Register may occur;
* no coordinated Movement removal for that Register may occur;
* no competing Totals rebuild may occur;
* no coordinated recovery operation may publish conflicting state.

Therefore the authoritative input consumed by the rebuild is stable relative to the coordinated Register mutation path.

This is a logical/process-local guarantee.

It is not a database snapshot guarantee.

---

# 31. Rebuild Determinism

For a fixed authoritative Movement Fact set:

```text
Movement Facts
+
existing Step 6.2 Totals semantics
```

the rebuild must produce the same semantic Totals state.

The rebuild must not depend on:

* arbitrary thread scheduling;
* storage layout;
* persistence provider implementation details;
* runtime object identity;
* uncontrolled external state.

Existing Step 6.2 deterministic enumeration/rebuild semantics remain authoritative.

---

# 32. Rebuild Failure

If authoritative enumeration fails:

```text
Totals cannot be declared valid
```

If Totals reconstruction fails:

```text
Totals cannot be declared valid
```

If an unexpected exception makes the outcome uncertain:

```text
ACTIVE + VALID
```

must not be claimed.

Existing Step 6.2 lifecycle and consistency states remain authoritative.

Step 6.3 does not introduce a second Totals state machine.

---

# 33. Recovery

`recover()` uses the same underlying rebuild path.

The intended internal structure is:

```text
public rebuild()
        │
        ▼
_rebuild_under_domain()

public recover()
        │
        ▼
_rebuild_under_domain()
```

The public methods must not independently acquire the same domain and then call each other in a way that creates nested orchestration.

Conceptually:

```python
def rebuild(...):
    domain = registry.get(register_identity)

    return domain.execute(
        lambda: self._rebuild_under_domain(register_identity)
    )


def recover(...):
    domain = registry.get(register_identity)

    return domain.execute(
        lambda: self._rebuild_under_domain(register_identity)
    )
```

The actual implementation should avoid unnecessary duplication while preserving one domain acquisition per operation.

---

# 34. Recovery Semantics

Recovery means:

```text
authoritative Movement Facts
        ↓
reconstruct Totals
        ↓
reconstruct runtime maintenance state
        ↓
establish valid derived state
```

Recovery does not introduce:

* a new persistence model;
* a second recovery store;
* a persistent repair log;
* asynchronous synchronization.

---

# 35. `CREATED` State

The existing Step 6.2 `CREATED + INDETERMINATE` semantics remain unchanged.

This state means:

> The coordinator/register state exists, but consistency with authoritative Movement Facts has not yet been established.

It is distinct from:

```text
RECOVERY_REQUIRED
```

which indicates that an established/operational state has subsequently lost known consistency.

---

# 36. Bootstrap Invariant

A coordinator instance must establish its derived state from authoritative Movement Facts before performing incremental maintenance against a pre-existing Register whose existing state was not established by that coordinator.

Therefore:

```text
new coordinator
        ↓
existing persistent Movement Facts
        ↓
rebuild
        ↓
incremental apply/remove
```

is the valid initialization path.

The following is not sufficient:

```text
new coordinator
        ↓
apply(new movement)
        ↓
ACTIVE + VALID
```

because the coordinator has no proof that previously existing Movement Facts were represented in its derived state.

Step 6.3 does not introduce a new public `initialize()` or `bootstrap()` API.

Rebuild remains the establishment mechanism.

---

# 37. `_applied` Runtime State

The existing `_applied` state in Step 6.2 remains runtime reconstruction state.

It is not:

* a persistent idempotency store;
* an authoritative Movement record;
* a cross-process synchronization mechanism;
* a durable transaction log.

During rebuild, it is reconstructed from authoritative Movement Facts.

This behavior must not be changed by Step 6.3.

---

# 38. Idempotency

Step 6.3 does not introduce persistent idempotency records.

Repeated mutation semantics continue to be governed by the existing Step 6.2 maintenance contract and the authoritative Movement persistence model.

The Register Operation Domain prevents concurrent conflicting operations from racing.

It does not itself become an idempotency mechanism.

---

# 39. Multi-Register Operations

The primary semantic API remains single-Register.

A single:

```text
RegisterMutationOrchestrator
```

operation must not silently become a multi-Register operation.

If a future logical operation genuinely requires multiple Registers, higher-level orchestration may coordinate several Register domains.

The individual Register domains remain:

```text
Domain(R1)
Domain(R2)
...
```

---

# 40. Deterministic Multi-Register Acquisition

When multiple Register domains must be acquired by one logical operation, they must be acquired in deterministic global order.

For example:

```text
sort(Register identities)
        ↓
acquire Domain(R1)
        ↓
acquire Domain(R2)
        ↓
...
```

The precise ordering key must be deterministic and stable.

This prevents lock-order inversion and reduces deadlock risk.

---

# 41. No `MultiRegisterOperation` Public Abstraction

A dedicated production `MultiRegisterOperation` abstraction is not introduced at this stage.

If implementation requires multi-domain acquisition, it should use a minimal internal helper.

A separate semantic API should be introduced only when an actual application use case requires one.

This keeps Step 6.3 focused on its primary boundary.

---

# 42. No Distributed Atomicity

Acquiring multiple Register Operation Domains does not create distributed transaction semantics.

For:

```text
R1
R2
R3
```

the operation may coordinate:

```text
Domain(R1)
Domain(R2)
Domain(R3)
```

but it does not guarantee:

```text
all Registers commit atomically
```

A partial failure remains possible.

The system must preserve explicit failure semantics rather than implying atomic multi-register commit.

---

# 43. Posting Integration

The intended Phase 6 integration is:

```text
PostingEngine
        │
        ▼
PostingResultCoordinator
        │
        ▼
RegisterMutationOrchestrator
        │
        ├── Movement persistence
        │
        └── Totals maintenance
```

The `PostingResultCoordinator` remains the Posting-to-persistence integration boundary.

Step 6.3 does not move Posting lifecycle responsibilities into Registers.

---

# 44. Posting Lifecycle Preservation

The following remain owned by Phase 6 Posting:

* posting lifecycle;
* Posting Context;
* Posting Handler execution;
* MovementSet generation;
* Movement validation;
* posting result coordination;
* posting events.

Step 6.3 does not redesign these responsibilities.

---

# 45. Posting Event Semantics

The existing Phase 6 event semantics remain unchanged.

`DocumentPosted`, `DocumentUnposted`, and `DocumentReposted` are emitted only after successful logical completion.

If Register mutation or Totals maintenance fails:

```text
posting operation = failed
```

and the corresponding successful event must not be emitted.

Step 6.3 does not create a second event lifecycle.

---

# 46. Posting Adapter Scope

If the current repository requires a concrete `PostingResultCoordinator` implementation to connect Phase 6 to Step 6.3, that adapter must remain minimal.

It should:

1. receive the Posting result;
2. delegate Register mutation to `RegisterMutationOrchestrator`;
3. propagate existing failures;
4. preserve Phase 6 lifecycle and event semantics.

It must not become a general Posting/Registers orchestration framework.

---

# 47. Composition Root

The composition root is responsible for creating shared infrastructure.

Conceptually:

```text
Composition Root
        │
        ├── RegisterFactPersistence
        │
        ├── TotalsMaintenanceCoordinator
        │
        ├── RegisterOperationDomainRegistry
        │
        └── RegisterMutationOrchestrator
```

The same registry instance must be shared by all Register mutation/rebuild paths that participate in the consistency boundary.

No component should independently construct another registry for the same logical application scope.

Otherwise:

```text
Registry A → Domain(R)
Registry B → Domain(R)
```

would violate the shared-domain invariant.

---

# 48. Dependency Injection

The orchestrator should receive its dependencies explicitly.

Conceptually:

```python
RegisterMutationOrchestrator(
    persistence=...,
    totals=...,
    domains=...,
)
```

The exact constructor syntax follows repository conventions.

The implementation must not silently create:

* a new persistence provider;
* a new Totals coordinator;
* a new registry;
* hidden global synchronization state.

---

# 49. Domain Lifetime

The Register Operation Domain is process-local infrastructure.

Its lifetime is tied to the lifetime of the registry/application composition that owns it.

It is not persisted.

It is not serialized.

It is not reconstructed from Movement Facts as durable state.

If a process restarts, the domain itself is recreated.

The authoritative state remains Movement persistence.

---

# 50. Threading Scope

The synchronization boundary is:

```text
process-local
thread-aware
Register-scoped
```

It is not:

```text
distributed
cross-process
cross-host
database-wide
```

Cross-process coordination is outside Step 6.3.

---

# 51. Storage Provider Independence

The design must work with any valid implementation of:

```text
RegisterFactPersistence
```

The Register Operation Domain must not depend on:

* filesystem-specific behavior;
* database-specific locks;
* in-memory storage implementation;
* a particular transaction API.

The orchestration boundary remains storage-independent.

---

# 52. No Persistence Transaction Abstraction

Step 6.3 does not introduce:

```text
RegisterTransaction
PersistenceTransaction
TotalsTransaction
```

or equivalent abstractions.

The operation domain coordinates logical ordering and exclusion.

It does not provide atomic commit.

---

# 53. No Totals Persistence

Totals remain derived state according to the existing Step 6 architecture.

Step 6.3 does not introduce:

* persistent Totals records;
* Totals snapshots;
* Totals write-ahead logs;
* Totals journals.

Recovery continues to derive Totals from authoritative Movement Facts.

---

# 54. Error Model

Step 6.3 uses existing error categories.

The preferred model is:

```text
Persistence errors
        ↓
existing persistence exceptions

Totals errors
        ↓
existing Totals exceptions/states

unexpected errors
        ↓
existing failure/indeterminate semantics
```

A new `RegisterMutationError` must not be added merely to wrap existing failures.

Wrapping may be considered only if implementation proves that an additional semantic distinction cannot otherwise be represented.

---

# 55. Construction vs Execution Errors

The implementation should distinguish:

### Construction/configuration failures

Examples:

* invalid dependency;
* invalid domain registration;
* incompatible component configuration.

These occur before a mutation operation starts.

### Execution failures

Examples:

* persistence failure;
* Totals failure;
* indeterminate persistence outcome;
* unexpected runtime failure.

Execution failures must preserve the semantics of the underlying component.

The API must not collapse all failures into one generic mutation exception.

---

# 56. Observability

The implementation may provide logging or diagnostics around:

* Register identity;
* operation type;
* success/failure/indeterminate outcome;
* rebuild/recovery;
* persistence failure;
* Totals failure.

Observability is non-normative.

It must not alter the semantic API.

---

# 57. Concurrency Test Boundary

Tests must verify that:

### Same Register

```text
mutation(R)
rebuild(R)
```

cannot overlap in a way that permits stale rebuild publication.

### Different Registers

```text
mutation(R1)
mutation(R2)
```

do not require a global serialization point.

### Rebuild

The domain is held:

```text
before enumeration
through publication
```

### Recovery

Recovery follows the same synchronization path as rebuild.

---

# 58. Required Domain Tests

The internal domain implementation should have tests for:

1. domain identity;
2. same-domain serialization;
3. different-domain isolation;
4. direct result propagation;
5. first-use registry creation;
6. same identity returning the same domain;
7. different identities returning different domains;
8. concurrent first-use registration;
9. exception propagation;
10. internal reentrancy if required by implementation.

Tests must not expose or depend on the specific synchronization primitive as public behavior.

---

# 59. Required Mutation Tests

`RegisterMutationOrchestrator` tests must cover:

1. single-register establishment;
2. mixed-register rejection;
3. empty establishment no-op;
4. persistence-before-Totals ordering;
5. persistence failure;
6. persistence indeterminate outcome;
7. Totals failure;
8. successful removal;
9. removal persistence failure;
10. removal indeterminate outcome;
11. Totals removal failure;
12. same-register mutation/rebuild serialization;
13. different-register isolation;
14. rebuild from authoritative Movement Facts;
15. recovery from the same authoritative source.

---

# 60. Required Rebuild Tests

Rebuild tests must verify:

```text
acquire domain
    ↓
enumerate
    ↓
rebuild
    ↓
publish
    ↓
release
```

The tests should specifically protect against the stale publication race:

```text
rebuild enumeration
        │
        X
concurrent mutation
        │
        ▼
stale rebuild publication
```

The coordinated architecture must make that interleaving impossible within the same Register Operation Domain.

---

# 61. Bootstrap Tests

Tests must preserve:

```text
new coordinator
        ↓
existing Movement Facts
        ↓
incremental apply
```

as an invalid path for establishing known consistency unless derived state was already established by that coordinator.

The valid path is:

```text
new coordinator
        ↓
rebuild
        ↓
incremental maintenance
```

A successful empty mutation must not satisfy this bootstrap invariant.

---

# 62. `_applied` Tests

Tests must verify that rebuild reconstructs the Step 6.2 runtime maintenance state from authoritative Movement Facts.

They must not treat `_applied` as durable state.

Coordinator recreation must therefore continue to require rebuild when operating against pre-existing persistent state.

---

# 63. Multi-Register Tests

If implementation contains multi-domain acquisition support, tests must verify:

1. deterministic ordering;
2. no lock-order inversion for the supported acquisition helper;
3. independent Register domains;
4. absence of distributed atomicity assumptions.

No test should imply that acquiring multiple domains provides a distributed transaction.

---

# 64. Public API Surface

The intended public semantic surface is minimal.

The primary new application-facing abstraction is:

```text
RegisterMutationOrchestrator
```

The following remain internal:

```text
RegisterOperationDomain
RegisterOperationDomainRegistry
multi-domain acquisition helpers
synchronization primitives
```

The public Registers package should not expose implementation synchronization machinery unless an existing repository convention requires it.

---

# 65. Module Layout

The preferred implementation structure is:

```text
src/accore/platform/registers/
    maintenance.py
    operation_domain.py
    mutation.py
```

Responsibilities:

### `maintenance.py`

Existing Step 6.2 Totals maintenance.

### `operation_domain.py`

Internal Register Operation Domain and Registry.

### `mutation.py`

Register Mutation Orchestration.

This separation keeps:

```text
Totals maintenance
Register synchronization
Register mutation orchestration
```

as distinct implementation responsibilities.

---

# 66. No Modification of Step 6.2 Semantics

Step 6.3 must not redesign `DefaultTotalsMaintenanceCoordinator`.

Existing Step 6.2 semantics remain authoritative.

Step 6.3 adds:

```text
coordination around Step 6.2
```

rather than replacing:

```text
Step 6.2 Totals maintenance
```

Any change to Step 6.2 behavior must be justified independently and must not be introduced merely because Step 6.3 needs an orchestration boundary.

---

# 67. API Stability Rule

The implementation must prefer the smallest API necessary to satisfy the approved contract.

In particular, do not introduce public APIs for:

* lock acquisition;
* lock release;
* domain context managers;
* persistent mutation sessions;
* transaction objects;
* mutation result wrappers;
* multi-register transaction objects;
* persistent idempotency records.

The semantic operation API is sufficient.

---

# 68. Candidate Internal API

The concrete implementation should converge on a shape equivalent to:

```python
class RegisterOperationDomain:
    def __init__(
        self,
        register_identity: Identifier,
    ) -> None:
        ...

    @property
    def register_identity(self) -> Identifier:
        ...

    def execute(
        self,
        operation: Callable[[], T],
    ) -> T:
        ...
```

and:

```python
class RegisterOperationDomainRegistry:
    def get(
        self,
        register_identity: Identifier,
    ) -> RegisterOperationDomain:
        ...
```

and:

```python
class RegisterMutationOrchestrator:
    def establish(
        self,
        movements: Sequence[Movement],
    ) -> None:
        ...

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
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

These are concrete design targets, not permission to expose all infrastructure as public API.

---

# 69. Internal Rebuild API

The implementation should provide one internal operation equivalent to:

```python
_rebuild_under_domain(
    register_identity: Identifier,
) -> MaintenanceResult
```

This method assumes that the caller already owns the appropriate Register Operation Domain.

It must not independently acquire another domain.

This prevents:

```text
domain acquisition
    ↓
public rebuild
    ↓
internal rebuild
    ↓
second domain acquisition
```

and keeps the critical section explicit.

---

# 70. Mutation Execution Shape

The establishment path should conceptually be:

```python
register_identity = validate_single_register(movements)

domain = domains.get(register_identity)

return domain.execute(
    lambda: establish_under_domain(movements)
)
```

where `_under_domain` logic:

1. performs authoritative Movement persistence;
2. applies corresponding Totals maintenance;
3. propagates existing failures.

The implementation must not perform either step outside the Register Operation Domain.

---

# 71. Removal Execution Shape

Removal follows the same model:

```python
register_identity = determine_register(movement_identities)

domain = domains.get(register_identity)

return domain.execute(
    lambda: remove_under_domain(...)
)
```

The implementation must use the actual repository APIs to determine the relevant Register and Movement data.

It must not introduce an invented persistence lookup abstraction.

---

# 72. Register Identity Resolution

The orchestrator must have a deterministic way to determine the Register affected by an operation.

For establishment:

```text
Movement.register_identity
```

is authoritative.

For removal, the implementation must use the existing persistence API and/or existing Movement information available through the repository contract.

If the existing API cannot determine a unique Register for the requested removal operation, implementation must stop at the architecture boundary rather than silently infer it.

---

# 73. Mixed Register Rejection

The orchestrator must reject:

```text
establish(
    M1(register=R1),
    M2(register=R2),
)
```

because there is no single Register Operation Domain for that operation.

The rejection occurs before any persistence mutation.

Therefore:

```text
mixed input
    ↓
validation failure
    ↓
no persistence mutation
    ↓
no Totals mutation
```

---

# 74. Empty Mutation

For:

```python
establish(())
```

the result is a successful no-op.

No domain needs to be selected because there is no Register identity.

The operation must not alter lifecycle state.

In particular:

```text
CREATED + INDETERMINATE
```

must remain so if no independent rebuild has established consistency.

---

# 75. Rebuild and Existing Movement Persistence

The rebuild path must use:

```python
RegisterFactPersistence.enumerate(register_identity)
```

or the exact existing equivalent.

It must not use:

* Totals as the source of truth;
* `_applied` as the source of truth;
* cached Movement lists;
* a second persistence abstraction.

Movement Facts remain authoritative.

---

# 76. Recovery and Existing Movement Persistence

Recovery uses the same authoritative enumeration path.

Therefore:

```text
recover(R)
```

must semantically be equivalent to:

```text
rebuild(R)
```

with respect to the authoritative source and resulting Totals consistency, while preserving the public operation semantics established by Step 6.2.

---

# 77. Failure Publication

A successful operation may publish:

```text
ACTIVE + VALID
```

only after the complete logical operation has completed successfully.

The implementation must not publish:

```text
ACTIVE + VALID
```

after:

* persistence indeterminate;
* Totals failure;
* incomplete rebuild;
* unexpected exception;
* an operation whose authoritative input was not fully established.

---

# 78. Recovery After Indeterminate Outcome

If a mutation reaches an indeterminate state:

```text
authoritative Movement state = uncertain
```

the system must not assume that a compensating Totals operation is safe.

The recovery path is based on authoritative Movement Facts once their persistence state can be enumerated reliably.

The resulting Totals state is established by rebuild.

---

# 79. Critical Section Definition

The critical section is the complete logical Register operation.

For mutation:

```text
domain acquisition
    ↓
Movement persistence
    ↓
Totals maintenance
    ↓
operation completion
    ↓
domain release
```

For rebuild:

```text
domain acquisition
    ↓
Movement enumeration
    ↓
Totals rebuild
    ↓
runtime state reconstruction
    ↓
state publication
    ↓
domain release
```

For recovery:

```text
domain acquisition
    ↓
same rebuild path
    ↓
domain release
```

---

# 80. What the Domain Does Not Guarantee

The Register Operation Domain does not guarantee:

* database atomicity;
* rollback;
* cross-process exclusion;
* cross-host exclusion;
* distributed transaction semantics;
* persistence durability;
* external-system consistency;
* crash recovery by itself.

It guarantees only the process-local orchestration boundary defined by this contract.

---

# 81. Crash Semantics

A process crash may occur between:

```text
Movement persistence
```

and:

```text
Totals maintenance
```

The operation domain cannot prevent this.

After restart:

```text
Movement Facts remain authoritative
```

and Totals can be rebuilt.

This is another reason the design must not treat Totals as an independent authoritative source.

---

# 82. Rebuild as Recovery Mechanism

The architecture deliberately uses:

```text
authoritative Movement Facts
        ↓
deterministic rebuild
        ↓
derived Totals
```

as the primary recovery model.

No durable synchronization journal is required by Step 6.3.

---

# 83. Concurrency Model

The expected concurrency model is:

```text
same Register:
    serialized

different Registers:
    independently executable
```

For example:

```text
Thread A → R1 mutation
Thread B → R1 rebuild
```

must serialize.

But:

```text
Thread A → R1 mutation
Thread B → R2 mutation
```

may execute concurrently.

---

# 84. Rebuild Race Explicitly Eliminated

Without Step 6.3:

```text
T1: enumerate R
T2: mutate R
T1: publish rebuilt Totals
```

could produce stale derived state.

With Step 6.3:

```text
T1: acquire Domain(R)
T1: enumerate R
T1: rebuild Totals
T1: publish
T1: release Domain(R)

T2: acquire Domain(R)
T2: mutate R
```

The mutation cannot intersect the rebuild's critical section.

---

# 85. No Concurrent Rebuild Merge

Step 6.3 does not introduce a mechanism for:

```text
rebuild A
+
concurrent mutation B
=
merge A and B
```

Instead, the operation domain prevents the concurrent mutation from entering the Register mutation boundary until rebuild publication is complete.

This is intentionally simpler and deterministic.

---

# 86. Fairness

No fairness or starvation guarantee is part of the API contract.

The implementation must provide correct mutual exclusion and isolation.

Scheduler-specific fairness behavior is outside the architectural contract.

---

# 87. Reentrancy

Internal reentrancy may be supported through `RLock`.

However:

```text
reentrant domain execution
```

is not a public semantic guarantee.

Higher-level code should not rely on recursive domain acquisition as application behavior.

---

# 88. Callback Constraints

The internal `execute()` callback is an implementation mechanism.

The implementation should keep callback behavior simple and bounded.

The public API must not expose arbitrary lock-callback semantics to application code.

The semantic public operations remain:

```text
establish
remove
rebuild
recover
```

---

# 89. Testing the Composition Boundary

Integration tests must construct:

```text
one RegisterOperationDomainRegistry
        │
        ├── Posting/Register mutation path
        │
        └── Totals rebuild/recovery path
```

to prove that both paths use the same Register Operation Domain.

Creating separate registries in an integration test would invalidate the very invariant being tested.

---

# 90. Architecture Invariants

The implementation must preserve all of the following:

### Invariant 1 — Shared Domain

For one Register, all consistency-affecting operations use the same Register Operation Domain.

### Invariant 2 — Single Register

A semantic Register mutation operation belongs to one Register.

### Invariant 3 — Stable Rebuild Boundary

Rebuild owns the domain from authoritative enumeration through Totals publication.

### Invariant 4 — Authoritative Movement Facts

Movement persistence remains authoritative.

### Invariant 5 — Derived Totals

Totals remain derived state.

### Invariant 6 — Bootstrap

Pre-existing state requires rebuild before incremental maintenance.

### Invariant 7 — Runtime `_applied`

`_applied` remains runtime state, not durable idempotency.

### Invariant 8 — Failure Honesty

`ACTIVE + VALID` is never claimed without established consistency.

### Invariant 9 — Register Isolation

Different Registers do not share a global operation lock.

### Invariant 10 — No Distributed Transaction

Multi-register coordination does not imply atomic distributed commit.

### Invariant 11 — Posting Ownership

Posting lifecycle remains owned by Phase 6.

### Invariant 12 — Persistence Boundary

`RegisterFactPersistence` remains storage-only.

### Invariant 13 — Totals Boundary

`TotalsMaintenanceCoordinator` remains responsible for Totals maintenance.

### Invariant 14 — Minimal Public API

Synchronization infrastructure remains internal.

---

# 91. Acceptance Criteria

Step 6.3 Concrete API Design is considered correctly implemented when:

1. A single Register has one shared operation domain.
2. The same domain is reused by mutation and rebuild/recovery paths.
3. Different Registers can operate independently.
4. `RegisterMutationOrchestrator` is the semantic application boundary.
5. Domain and registry are not exposed as unnecessary public application APIs.
6. `establish()` returns `None`.
7. `remove()` returns `None`.
8. No redundant `MutationResult` exists.
9. Mixed-register establishment is rejected before mutation.
10. Empty establishment is a successful no-op.
11. Empty establishment does not establish Totals validity.
12. Movement persistence precedes Totals maintenance.
13. Persistence failure prevents corresponding Totals mutation.
14. Persistence indeterminate outcome cannot establish `ACTIVE + VALID`.
15. Totals failure preserves authoritative Movement Facts.
16. Rebuild acquires the domain before enumeration.
17. Rebuild holds the domain through Totals publication.
18. Recovery uses the same rebuild path.
19. Step 6.2 lifecycle and consistency semantics remain unchanged.
20. Bootstrap invariant remains enforced.
21. `_applied` remains runtime-only.
22. No persistent idempotency mechanism is introduced.
23. No new persistence abstraction is introduced.
24. No new Totals persistence model is introduced.
25. No distributed transaction is introduced.
26. Multi-register acquisition, if required, is deterministic.
27. Posting lifecycle semantics remain unchanged.
28. Posting events remain success-only.
29. The same domain instance is shared through composition-root dependency injection.
30. No global Register lock serializes unrelated Registers.
31. The implementation is process-local.
32. Existing persistence and Totals exceptions remain authoritative.
33. Tests prove the rebuild/mutation race is excluded.
34. Full repository quality gates pass.

---

# 92. Implementation Boundary

Implementation should proceed in the following order.

## Step 1 — Internal operation domain

Implement:

```text
RegisterOperationDomain
RegisterOperationDomainRegistry
```

with:

* Register identity;
* process-local synchronization;
* deterministic first-use creation;
* direct callback result propagation.

No public application API should depend directly on these classes.

## Step 2 — Register mutation orchestrator

Implement:

```text
RegisterMutationOrchestrator
```

with:

* `establish`;
* `remove`;
* `rebuild`;
* `recover`.

Reuse existing Step 6.2 APIs.

## Step 3 — Rebuild critical section

Ensure:

```text
domain acquisition
    ↓
enumerate
    ↓
rebuild
    ↓
publish
    ↓
release
```

is one uninterrupted Register-scoped logical operation.

## Step 4 — Posting integration

Only if required by the current repository, implement the minimal concrete `PostingResultCoordinator` adapter that delegates Register mutation to the orchestrator.

Do not redesign Phase 6.

## Step 5 — Tests

Add unit and integration tests for:

* domain behavior;
* registry behavior;
* mutation;
* removal;
* rebuild;
* recovery;
* concurrency;
* bootstrap;
* multi-register ordering where applicable;
* Posting integration.

## Step 6 — Quality gate

Run:

```text
ruff check .
black --check .
mypy src
pytest
```

The full repository suite must remain green.

---

# 93. Explicit Non-Goals During Implementation

The implementation must not introduce unrelated changes to:

* PostingEngine;
* Posting Context;
* Posting Handler architecture;
* Movement model;
* Register Fact persistence contract;
* Totals persistence;
* Runtime object model;
* persistence provider architecture;
* event infrastructure.

Any such change requires an independent architecture decision.

---

# 94. Final API Boundary

The final intended architecture is:

```text
                         PostingEngine
                              │
                              ▼
                  PostingResultCoordinator
                              │
                              ▼
                 RegisterMutationOrchestrator
                              │
                              ▼
              RegisterOperationDomainRegistry
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        RegisterOperationDomain     RegisterOperationDomain
                 │                         │
              Register R1               Register R2
                 │
          ┌──────┴──────┐
          ▼             ▼
Movement Persistence   Totals Maintenance
 authoritative           derived
```

The critical architectural relationship is:

```text
same Register
      │
      ├── Movement mutation
      ├── Totals mutation
      ├── rebuild
      └── recovery
             │
             ▼
      same Operation Domain
```

while:

```text
different Registers
        │
        ▼
independent Operation Domains
```

---

# 95. Final Design Statement

Step 6.3 does not make Totals transactional.

It establishes a stronger and more precise property:

> For each Register, every coordinated operation that can affect the consistency relationship between authoritative Movement Facts and derived Totals executes inside one shared Register-scoped logical operation domain.

The implementation therefore provides:

```text
authoritative Movement persistence
            +
derived Totals maintenance
            +
Register-scoped serialization
            +
stable rebuild boundary
            +
explicit recovery
```

without introducing:

```text
distributed transactions
persistent idempotency
new persistence abstractions
new Totals persistence
event-driven synchronization
Posting lifecycle redesign
```

The public semantic API remains intentionally small:

```text
RegisterMutationOrchestrator
```

while synchronization infrastructure remains internal.

This closes the Concrete API Design for Step 6.3 and establishes the implementation boundary for the next phase of work.
