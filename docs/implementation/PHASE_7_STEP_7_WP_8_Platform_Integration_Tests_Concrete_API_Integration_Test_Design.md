# PHASE 7 — WP-8 Platform Integration Tests

## Concrete API / Integration Test Design

---

# 1. Purpose

This document translates the approved WP-8 Architecture Definition / Scope into a concrete integration-test design based on the current implementation.

WP-8 verifies composition of the existing Register Platform components.

No new production API or production abstraction is introduced.

The tests operate through the existing architectural boundaries:

```text
RegisterMutationOrchestrator
RegisterOperationDomain
RegisterOperationDomainRegistry
TotalsMaintenanceCoordinator
RegisterFactPersistence
TotalsEngine
MovementQueryService
BalanceQueryService
```

The primary test boundary is the real Register Platform composition, not isolated implementation methods.

---

# 2. Current Integration Points

The current production composition contains the following concrete integration points.

## 2.1 Mutation

```python
RegisterMutationOrchestrator(
    persistence=...,
    totals=...,
    domains=...,
    validator=...,
)
```

Public operations:

```python
orchestrator.establish(movements)
orchestrator.remove(movements)
```

`RegisterMutationOrchestrator` obtains the Register-specific domain from:

```python
RegisterOperationDomainRegistry.get(register_identity)
```

and executes mutation state changes through:

```python
domain.execute(operation)
```

---

# 3. Operation Domain

The concrete synchronization boundary is:

```python
RegisterOperationDomainRegistry()
```

with:

```python
registry.get(register_identity)
```

returning a stable:

```python
RegisterOperationDomain
```

The domain exposes:

```python
domain.execute(operation)
```

The test design must treat this as the only Register-scoped serialization boundary.

Tests must not directly manipulate:

```text
_lock
RLock
acquire()
release()
```

---

# 4. Maintenance Integration

The current maintenance implementation is:

```python
DefaultTotalsMaintenanceCoordinator(
    engine=engine,
    persistence=persistence,
)
```

Public operations:

```python
coordinator.apply(movement)
coordinator.remove(movement)
coordinator.rebuild(register_identity)
coordinator.recover(register_identity)
coordinator.state(register_identity)
coordinator.ensure_mutation_admitted(register_identity)
```

Maintenance operations are executed through the Register Operation Domain by the composition layer:

```python
domain.execute(
    lambda: coordinator.rebuild(register_identity)
)
```

and:

```python
domain.execute(
    lambda: coordinator.recover(register_identity)
)
```

Recovery remains rebuild semantics.

---

# 5. Persistence Integration

The authoritative persistence boundary is:

```python
RegisterFactPersistence
```

with the relevant operations:

```python
append(movements)
remove(movement_identities)
enumerate(register_identity)
find_by_source_document(
    register_identity,
    source_document_identity,
)
```

WP-8 uses:

```python
enumerate(register_identity)
```

as the authoritative source for rebuild/recovery.

Tests must not use runtime `_applied` as an authoritative reconstruction source.

---

# 6. Totals Integration

The current concrete Totals implementation is:

```python
DefaultTotalsEngine(definitions)
```

with:

```python
apply(movement)
remove(movement)
rebuild(register_identity, movements)
get(register_identity, key)
```

The integration design treats Totals as derived state.

Rebuild must therefore be validated against persisted Movement Facts, not against previous in-memory Totals state.

---

# 7. Query Integration

## 7.1 Movement Query

Concrete implementation:

```python
DefaultMovementQueryService(persistence)
```

Public invocation:

```python
movement_query_service.query(query)
```

The service reads directly from:

```python
RegisterFactPersistence
```

and does not require:

```text
TotalsMaintenanceCoordinator
RegisterOperationDomain
TotalsEngine
```

---

## 7.2 Balance Query

Concrete implementation:

```python
DefaultBalanceQueryService(totals)
```

where `totals` is consumed through the `TotalsReader` capability.

Public invocation:

```python
balance_query_service.query(query)
```

Balance Query reads current Totals.

It does not reconstruct a balance from Movement Facts.

---

# 8. Test Infrastructure

WP-8 integration tests should reuse the existing test infrastructure where appropriate.

Current test helpers include:

```python
make_movement(...)
make_definition(...)
InMemoryRegisterFactPersistence
```

These helpers already model the public persistence contract sufficiently for platform-level tests.

Additional purpose-built doubles may be introduced for:

* blocking persistence;
* failing persistence;
* failing Totals;
* indeterminate failures;
* recording execution boundaries.

These doubles must implement the existing contracts and must not introduce new production semantics.

---

# 9. Test Organization

The preferred implementation location is:

```text
tests/unit/registers/test_operation_domain_integration.py
```

for scenarios that specifically exercise the existing Operation Domain composition.

If the resulting file becomes dominated by broader end-to-end Register Platform scenarios, a dedicated:

```text
tests/unit/registers/test_platform_integration.py
```

may be introduced.

This is a test-organization decision only.

It must not result in a new production abstraction.

---

# 10. Existing Coverage to Preserve

The current integration test suite already covers several WP-8 architectural invariants.

These tests should be retained and considered part of WP-8 coverage.

Existing scenarios include:

```text
same-register operation serialization
different-register isolation
shared registry domain identity
maintenance invocation through shared domain
mutation execution inside operation domain
same-register maintenance serialization
bootstrap admission
rebuild/mutation serialization
Movement Query composition
Balance Query composition
```

WP-8 implementation must extend this coverage rather than replace it.

---

# 11. Integration Test Matrix

## 11.1 Bootstrap and Admission

### Test B1 — Bootstrap blocks mutation

Composition:

```text
new Coordinator
        ↓
CREATED + INDETERMINATE
        ↓
Mutation
        ↓
TotalsMaintenanceAdmissionError
```

Required assertions:

* mutation is rejected;
* no Movement Fact is persisted;
* Totals are not mutated;
* maintenance state remains non-admitted.

---

### Test B2 — Rebuild activates Register

Composition:

```text
Persisted Movement Facts
        ↓
Operation Domain
        ↓
Maintenance.rebuild()
        ↓
Totals reconstruction
        ↓
ACTIVE + VALID
```

Required assertions:

* persisted facts are enumerated;
* Totals match persisted facts;
* mutation becomes admissible only after successful rebuild.

---

# 12. Mutation Composition

## Test M1 — Establish persists and updates Totals

Composition:

```text
Validator
   ↓
Operation Domain
   ↓
Mutation Orchestrator
   ├── Persistence.append()
   └── Maintenance.apply()
          ↓
       Totals Engine
```

Assertions:

```text
Movement Fact persisted
Totals updated
Maintenance state remains valid
```

---

## Test M2 — Remove persists removal and updates Totals

Composition:

```text
Operation Domain
   ↓
Mutation Orchestrator
   ├── Persistence.remove()
   └── Maintenance.remove()
```

Assertions:

* Movement Fact is removed;
* derived Totals reflect removal;
* no stale current balance remains.

---

## Test M3 — Mutation admission occurs inside domain

Use a recording domain to establish that:

```text
ensure_mutation_admitted()
persistence.append/remove()
totals.apply/remove()
```

execute inside the same domain critical section.

Validation may remain outside the critical section because it occurs before mutation admission and authoritative state change.

---

# 13. Rebuild Composition

## Test R1 — Rebuild uses authoritative persistence

Given:

```text
persisted Movement Facts = A + B
runtime Totals = stale/different
```

execute:

```python
domain.execute(
    lambda: coordinator.rebuild(register)
)
```

Assertions:

* `persistence.enumerate(register)` is the reconstruction source;
* resulting Totals equal A + B;
* previous derived state is replaced.

---

## Test R2 — Rebuild reconstructs runtime applied state

After successful rebuild, subsequent mutation of a previously rebuilt Movement must not be treated as an unrelated first application.

The test must observe this through public behavior rather than directly asserting private `_applied` contents unless a specific internal invariant requires it.

---

## Test R3 — Rebuild is deterministic

Given unchanged authoritative Movement Facts:

```python
rebuild(register)
rebuild(register)
```

must produce equivalent logical Totals.

The second rebuild must not double-count the first rebuild.

---

# 14. Recovery Composition

## Test C1 — Recovery delegates to rebuild semantics

After a Register reaches:

```text
RECOVERY_REQUIRED
```

execute:

```python
domain.execute(
    lambda: coordinator.recover(register)
)
```

Assertions:

* authoritative persistence is enumerated;
* Totals are reconstructed;
* successful result uses:

```python
MaintenanceOperation.REBUILD
```

* no `MaintenanceOperation.RECOVER` is introduced;
* final state is:

```text
ACTIVE + VALID
```

---

## Test C2 — Recovery restores mutation admission

After successful recovery:

```python
orchestrator.establish((movement,))
```

must succeed.

The test therefore verifies the full composition:

```text
failure
  ↓
RECOVERY_REQUIRED
  ↓
recover()
  ↓
rebuild()
  ↓
ACTIVE + VALID
  ↓
mutation admitted
```

---

# 15. Failure Composition

## Test F1 — Persistence failure during rebuild

A persistence double raises the existing persistence failure.

Execute:

```python
domain.execute(
    lambda: coordinator.rebuild(register)
)
```

Assertions:

* rebuild does not publish `ACTIVE + VALID`;
* resulting state indicates recovery is required according to the existing failure contract;
* stale/partially reconstructed state is not reported as valid.

---

## Test F2 — Totals failure during rebuild

A Totals Engine double raises the existing Totals failure.

Assertions:

* rebuild result is failure;
* `RECOVERY_REQUIRED` is published;
* `ACTIVE + VALID` is not published.

---

## Test F3 — Unexpected failure during rebuild

An unexpected exception is raised from the reconstruction path.

Assertions:

```text
outcome = INDETERMINATE
consistency = RECOVERY_REQUIRED
```

The Register must remain non-admitted.

---

## Test F4 — Mutation failure composition

When authoritative persistence has completed but Totals maintenance returns a non-success result, the mutation orchestration must expose the existing:

```python
RegisterMutationMaintenanceError
```

with the maintenance result attached.

The test must verify that the failure is observable without introducing a second mutation failure abstraction.

---

# 16. Serialization Composition

## Test S1 — Mutation vs Rebuild

This is a true cross-component concurrency test.

The rebuild path is blocked during:

```python
persistence.enumerate(register)
```

A concurrent mutation for the same Register attempts:

```python
orchestrator.establish(...)
```

Required behavior:

```text
rebuild holds domain
        ↓
mutation waits
        ↓
rebuild completes
        ↓
mutation executes
```

Final persistence and Totals must agree.

This test must use explicit `Event` synchronization rather than arbitrary timing.

---

## Test S2 — Mutation vs Recovery

Same-register recovery is blocked during reconstruction.

Concurrent mutation must not enter its state-changing section until recovery releases the shared domain.

---

## Test S3 — Rebuild vs Rebuild

Two rebuilds for the same Register must not overlap.

A tracking persistence/engine implementation should record maximum concurrent reconstruction activity.

Required result:

```text
maximum concurrent rebuilds == 1
```

---

## Test S4 — Different-register isolation

A blocked operation for Register A must not prevent a state-changing operation for Register B.

The test should use independent:

```text
RegisterOperationDomain
Persistence facts
Totals definition
Maintenance state
```

for the two Registers.

---

# 17. Query Composition

## Test Q1 — Movement Query after establish

Composition:

```text
Mutation
    ↓
Persistence
    ↓
Movement Query
```

Assertions:

* the newly persisted Movement is returned;
* query does not use Totals;
* maintenance state is unchanged by the query.

---

## Test Q2 — Balance Query after establish

Composition:

```text
Mutation
    ↓
Totals
    ↓
Balance Query
```

Assertions:

* Balance equals current Totals;
* query does not mutate maintenance state.

---

## Test Q3 — Movement Query after remove

After successful removal:

```python
movement_query_service.query(...)
```

must not return the removed Movement.

---

## Test Q4 — Balance Query after remove

After successful removal:

```python
balance_query_service.query(...)
```

must return the updated Totals.

---

# 18. Cross-Capability Platform Scenario

At least one test must exercise the complete composition:

```text
Bootstrap
    ↓
Establish
    ↓
Movement Query
    ↓
Balance Query
    ↓
Remove
    ↓
Movement Query
    ↓
Balance Query
    ↓
Rebuild
    ↓
Balance Query
```

The test must use the actual public/concrete components:

```python
persistence = InMemoryRegisterFactPersistence(...)
engine = DefaultTotalsEngine(...)
coordinator = DefaultTotalsMaintenanceCoordinator(...)
domains = RegisterOperationDomainRegistry()
orchestrator = RegisterMutationOrchestrator(...)
movement_query = DefaultMovementQueryService(...)
balance_query = DefaultBalanceQueryService(...)
```

No test-only facade may hide the composition.

---

# 19. Read-Side Non-Interference

The following invariant requires explicit integration evidence:

```text
Movement Query
Balance Query
```

do not alter:

```text
TotalsMaintenanceState
Persistence
Totals
Operation Domain
```

A useful test pattern is:

```python
state_before = coordinator.state(register)

movement_query.query(...)
balance_query.query(...)

state_after = coordinator.state(register)

assert state_after == state_before
```

The query test must not require entering the Operation Domain.

---

# 20. Register Isolation Scenario

A dedicated integration scenario should create:

```text
Register A
Register B
```

and independently compose:

```text
Persistence A
Totals A
Maintenance A
Domain A

Persistence B
Totals B
Maintenance B
Domain B
```

The test must establish that:

* A's Movement Facts do not appear in B;
* A's Totals do not affect B;
* A's maintenance state does not affect B;
* A's blocked state-changing operation does not block B;
* Balance Query for A only observes A;
* Movement Query for B only observes B.

---

# 21. Public API Usage in Integration Tests

Where practical, integration tests should import public Register symbols from:

```python
from accore.platform.registers import ...
```

The WP-7 public API boundary must therefore be exercised by WP-8 rather than bypassed.

The following internal import remains acceptable only where the test explicitly targets an internal test-only type:

```python
from accore.platform.registers.validation import MovementSetLike
```

It must not be treated as public API.

---

# 22. Assertions Must Prefer Observable Semantics

Integration tests should primarily assert:

* persisted Movement Facts;
* Totals values;
* MaintenanceResult;
* MaintenanceState;
* query results;
* admission behavior;
* serialization behavior;
* Register isolation.

They should not primarily assert private implementation details.

Private fields such as:

```text
_coordinator._applied
_coordinator._states
_domain._lock
_registry._domains
```

must not become the normal assertion surface.

Private inspection is justified only when the specific architecture invariant cannot be observed otherwise.

---

# 23. Concurrency Test Rules

Concurrency tests must be deterministic.

Preferred synchronization:

```python
Event
```

or equivalent explicit synchronization primitives.

Avoid:

```python
sleep(...)
```

as the mechanism that establishes correctness.

A small bounded wait may be used only for test coordination where an explicit event cannot express the required condition.

Every spawned thread must:

* be joined;
* have a bounded timeout;
* be asserted not alive after completion;
* propagate test failure through a deterministic shared result or assertion mechanism.

---

# 24. Expected Test File Changes

The preferred implementation is to extend:

```text
tests/unit/registers/test_operation_domain_integration.py
```

with scenarios not already covered.

If broader cross-capability tests justify separation, add:

```text
tests/unit/registers/test_platform_integration.py
```

The implementation should not duplicate existing tests merely to increase test count.

The final WP-8 test set should provide a traceable mapping:

```text
Architecture Invariant
        ↓
Integration Scenario
        ↓
Test
```

---

# 25. Coverage Matrix

| Architecture requirement                   | Existing / new test      |
| ------------------------------------------ | ------------------------ |
| Bootstrap blocks mutation                  | existing                 |
| Successful rebuild activates Register      | existing / verify        |
| Mutation composition                       | new or existing coverage |
| Remove composition                         | new                      |
| Rebuild from persistence                   | existing / strengthen    |
| Rebuild deterministic                      | new                      |
| Recovery through rebuild                   | existing / strengthen    |
| Recovery restores admission                | new                      |
| Persistence failure                        | new                      |
| Totals failure                             | new                      |
| Unexpected failure                         | new                      |
| Mutation vs rebuild                        | existing                 |
| Mutation vs recovery                       | existing / strengthen    |
| Rebuild vs rebuild                         | new                      |
| Different-register isolation               | existing                 |
| Movement Query composition                 | existing                 |
| Balance Query composition                  | existing                 |
| Query non-interference                     | existing / strengthen    |
| Full cross-capability flow                 | new                      |
| Register isolation across read/write sides | new                      |

---

# 26. Production API Changes

WP-8 requires no new production API.

The following existing APIs are sufficient:

```python
RegisterOperationDomain.execute(...)
RegisterOperationDomainRegistry.get(...)
RegisterMutationOrchestrator.establish(...)
RegisterMutationOrchestrator.remove(...)

TotalsMaintenanceCoordinator.apply(...)
TotalsMaintenanceCoordinator.remove(...)
TotalsMaintenanceCoordinator.rebuild(...)
TotalsMaintenanceCoordinator.recover(...)
TotalsMaintenanceCoordinator.state(...)
TotalsMaintenanceCoordinator.ensure_mutation_admitted(...)

MovementQueryService.query(...)
BalanceQueryService.query(...)
```

If implementation reveals that an approved scenario cannot be expressed through these boundaries, that is an architecture/API discrepancy and must be reviewed before production changes are made.

---

# 27. Acceptance Criteria

WP-8 implementation is accepted when:

1. all required architectural composition scenarios have executable tests;
2. existing WP-4–WP-7 integration tests remain valid;
3. mutation, rebuild, and recovery are verified through the shared Operation Domain;
4. authoritative persistence is verified as the rebuild/recovery source;
5. Totals are verified as derived state;
6. bootstrap/admission is verified;
7. deterministic and indeterminate failure semantics are verified;
8. recovery restores mutation admission only after successful reconstruction;
9. same-register serialization is verified for actual platform operations;
10. different-register isolation is verified;
11. Movement Query is verified against persisted Movement Facts;
12. Balance Query is verified against published Totals;
13. read-side queries are verified not to mutate maintenance state;
14. at least one complete cross-capability platform scenario exists;
15. tests use the approved public/architectural boundaries;
16. no new production abstraction is introduced;
17. no existing public API semantics change.

---

# 28. Quality Gate

After implementation:

```bash
pytest -q tests/unit/registers/
pytest -q
ruff check .
black .
black --check .
mypy src
```

Expected result:

* all Register tests pass;
* all project tests pass;
* Ruff passes;
* Black produces no remaining changes;
* Mypy reports no source errors.

---

# 29. Final Design Decision

WP-8 is implemented as integration tests over the existing Register Platform composition.

The canonical state-changing path remains:

```text
RegisterOperationDomain
        ↓
Mutation / Rebuild / Recovery
        ↓
Totals Maintenance
        ↓
Totals Engine
```

The authoritative source remains:

```text
RegisterFactPersistence
```

The read-side paths remain:

```text
RegisterFactPersistence
        ↓
Movement Query
```

and:

```text
TotalsReader
        ↓
Balance Query
```

No new facade, coordinator, recovery service, orchestration service, or synchronization mechanism is introduced.

The tests are intended to prove that the existing architecture composes correctly under ordinary operation, reconstruction, failure, concurrency, and read-side observation.

---

# 30. Next Step

After approval:

1. implement the missing WP-8 integration scenarios;
2. retain existing valid integration coverage;
3. run the Register test suite;
4. run the full project test suite;
5. run Ruff, Black, and Mypy;
6. review any implementation-discovered architectural mismatch before modifying production code.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
