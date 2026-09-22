# Phase 7 — Step 7 — WP-5 Bootstrap / Rebuild / Recovery

## Concrete API Design

**Status:** Final — Reconciled with implemented WP-4–WP-8 state
**Phase:** Phase 7 — Register Engine
**Step:** Step 7 — Platform Implementation
**Work Package:** WP-5 — Bootstrap / Rebuild / Recovery

---

# 1. Purpose

This document defines the concrete API and composition model required to implement WP-5 — Bootstrap / Rebuild / Recovery.

WP-5 implements the approved architecture for:

* Register maintenance bootstrap;
* mutation admission before and after reconstruction;
* Totals rebuild from authoritative Movement Facts;
* maintenance recovery;
* Register-scoped serialization of rebuild and recovery;
* deterministic rebuild behavior;
* preservation of existing failure semantics.

This document does not introduce new Register semantics.

It does not introduce a new orchestration abstraction.

The implementation MUST use the existing:

```text
TotalsMaintenanceCoordinator
RegisterFactPersistence
TotalsEngine
RegisterOperationDomain
RegisterOperationDomainRegistry
```

contracts.

---

# 2. API Ownership Model

The WP-5 API ownership model is:

```text
RegisterOperationDomainRegistry
            │
            ▼
RegisterOperationDomain
            │
     ┌──────┴──────┐
     ▼             ▼
  rebuild        recover
     │             │
     └──────┬──────┘
            ▼
TotalsMaintenanceCoordinator
            │
       ┌────┴────┐
       ▼         ▼
Persistence   TotalsEngine
```

Responsibilities remain separated:

| API                               | Responsibility                                 |
| --------------------------------- | ---------------------------------------------- |
| `RegisterOperationDomainRegistry` | Obtain shared Register-scoped operation domain |
| `RegisterOperationDomain`         | Serialize complete Register operations         |
| `TotalsMaintenanceCoordinator`    | Own maintenance semantics and state            |
| `RegisterFactPersistence`         | Provide authoritative Movement Facts           |
| `TotalsEngine`                    | Reconstruct derived Totals                     |
| `RegisterMutationOrchestrator`    | Execute ordinary mutation                      |

WP-5 MUST NOT move semantic state ownership into the Operation Domain.

---

# 3. Existing Public Maintenance API

The existing public maintenance contract remains:

```python
class TotalsMaintenanceCoordinator(Protocol):
    def apply(
        self,
        movement: Movement,
    ) -> MaintenanceResult:
        ...

    def remove(
        self,
        movement: Movement,
    ) -> MaintenanceResult:
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

    def state(
        self,
        register_identity: Identifier,
    ) -> TotalsMaintenanceState:
        ...

    def ensure_mutation_admitted(
        self,
        register_identity: Identifier,
    ) -> None:
        ...
```

WP-5 does not change the meaning of these methods.

In particular:

```text
rebuild()
```

remains a maintenance semantic operation.

```text
recover()
```

remains a semantic recovery operation.

The Operation Domain does not own either operation.

---

# 4. Register Operation Domain Integration

The shared Register Operation Domain remains the serialization boundary.

The concrete composition pattern is:

```python
domain = domains.get(register_identity)

result = domain.execute(
    lambda: totals.rebuild(register_identity)
)
```

For recovery:

```python
domain = domains.get(register_identity)

result = domain.execute(
    lambda: totals.recover(register_identity)
)
```

The same `RegisterOperationDomainRegistry` instance MUST be used by the mutation path and by rebuild/recovery composition.

This guarantees that:

```text
mutation
rebuild
recovery
```

for the same Register use the same serialization boundary.

---

# 5. Rebuild Invocation Boundary

The canonical rebuild invocation is:

```python
def rebuild(
    register_identity: Identifier,
    domains: RegisterOperationDomainRegistry,
    totals: TotalsMaintenanceCoordinator,
) -> MaintenanceResult:
    domain = domains.get(register_identity)

    return domain.execute(
        lambda: totals.rebuild(register_identity)
    )
```

This is an **integration composition pattern**, not a new required public service.

The implementation MUST NOT introduce a new class solely to wrap this sequence.

The existing application/platform composition layer MAY perform this invocation directly.

---

# 6. Recovery Invocation Boundary

The canonical recovery invocation is:

```python
def recover(
    register_identity: Identifier,
    domains: RegisterOperationDomainRegistry,
    totals: TotalsMaintenanceCoordinator,
) -> MaintenanceResult:
    domain = domains.get(register_identity)

    return domain.execute(
        lambda: totals.recover(register_identity)
    )
```

Recovery remains semantically distinct from rebuild.

The Operation Domain only provides serialization.

If:

```python
totals.recover(register_identity)
```

delegates internally to:

```python
totals.rebuild(register_identity)
```

that remains an implementation detail of the maintenance coordinator.

No separate recovery coordinator is required.

---

# 7. Bootstrap State

A newly constructed `DefaultTotalsMaintenanceCoordinator` has no knowledge of previously persisted Movement Facts.

The initial state therefore remains:

```python
TotalsMaintenanceState(
    lifecycle=TotalsLifecycleState.CREATED,
    consistency=TotalsConsistencyState.INDETERMINATE,
)
```

The initial runtime applied set is empty.

Conceptually:

```text
new coordinator
    │
    ├── state = CREATED + INDETERMINATE
    │
    └── _applied = empty
```

This does not imply:

```text
persisted Movement Facts = empty
```

Therefore the coordinator MUST NOT admit ordinary incremental mutation merely because `_applied` is empty.

---

# 8. Mutation Admission API

The existing:

```python
totals.ensure_mutation_admitted(register_identity)
```

remains the authoritative semantic admission check.

The successful admission condition is:

```python
state.lifecycle is TotalsLifecycleState.ACTIVE
and
state.consistency is TotalsConsistencyState.VALID
```

The concrete mutation sequence remains:

```text
RegisterOperationDomain.execute()
        │
        ▼
ensure_mutation_admitted()
        │
        ▼
authoritative mutation
```

Therefore a newly created coordinator produces:

```text
CREATED + INDETERMINATE
        ↓
ensure_mutation_admitted()
        ↓
TotalsMaintenanceAdmissionError
```

No persistence mutation and no Totals mutation may occur after this rejection.

---

# 9. Bootstrap Completion

Bootstrap is completed by successful rebuild.

The canonical sequence is:

```text
new coordinator
      ↓
CREATED + INDETERMINATE
      ↓
rebuild
      ↓
enumerate authoritative Movement Facts
      ↓
fresh Totals reconstruction
      ↓
reconstruct _applied
      ↓
ACTIVE + VALID
```

Only after the final state becomes:

```text
ACTIVE + VALID
```

may ordinary mutation proceed.

WP-5 does not introduce a separate:

```text
bootstrap()
```

method.

Bootstrap is a lifecycle condition achieved through authoritative reconstruction.

---

# 10. Authoritative Rebuild Source

`RegisterFactPersistence.enumerate()` is the authoritative source for rebuild.

The concrete API is:

```python
movements = persistence.enumerate(register_identity)
```

The returned Movement Facts MUST be passed to:

```python
engine.rebuild(
    register_identity,
    movements,
)
```

The rebuild path MUST NOT derive authoritative state from:

* existing Totals;
* `_applied`;
* previous maintenance state;
* query results;
* cached aggregates.

The dependency is therefore:

```text
RegisterFactPersistence.enumerate()
        ↓
Movement Facts
        ↓
TotalsEngine.rebuild()
```

---

# 11. Fresh Totals Reconstruction

The concrete Totals API remains:

```python
engine.rebuild(
    register_identity,
    movements,
)
```

The implementation MUST preserve the existing rebuild semantics:

```text
old Totals
    ↓
discarded/replaced
    ↓
fresh aggregate
    ↓
aggregate(all authoritative Movement Facts)
```

Rebuild MUST NOT be implemented as:

```text
repair(old Totals)
```

or:

```text
apply(missing movements)
```

The resulting Totals MUST depend only on the authoritative Movement Facts returned by persistence.

---

# 12. Runtime `_applied` Reconstruction

After successful Totals reconstruction, the coordinator reconstructs its runtime applied state.

Conceptually:

```python
{
    (movement.identity, movement.register_identity)
    for movement in movements
}
```

The runtime state replacement occurs only after:

```text
persistence.enumerate()
```

and:

```text
engine.rebuild()
```

have both succeeded.

Therefore:

```text
rebuild failure
    ↓
_do not replace _applied_
```

A successful rebuild replaces the runtime state with the reconstructed set.

---

# 13. Rebuild State Publication

The coordinator MUST NOT publish:

```text
ACTIVE + VALID
```

before all reconstruction steps succeed.

The required sequence is:

```text
MAINTENANCE
    ↓
enumerate
    ↓
Totals rebuild
    ↓
_applied replacement
    ↓
ACTIVE + VALID
```

If any reconstruction step fails:

```text
MAINTENANCE
    ↓
failure classification
    ↓
RECOVERY_REQUIRED
```

or:

```text
MAINTENANCE
    ↓
indeterminate classification
    ↓
RECOVERY_REQUIRED
```

according to the existing failure contract.

---

# 14. Rebuild Critical Section

The following operations MUST execute inside one shared Register Operation Domain critical section:

```text
persistence.enumerate()
        ↓
TotalsEngine.rebuild()
        ↓
runtime _applied reconstruction
        ↓
maintenance state publication
```

The required composition is:

```python
domain.execute(
    lambda: totals.rebuild(register_identity)
)
```

The coordinator's internal implementation MUST NOT release the Register Operation Domain between these stages.

This prevents:

```text
T1: enumerate M1, M2
T2: persist M3 + apply M3
T1: rebuild M1, M2
```

from producing stale derived Totals.

---

# 15. Rebuild / Mutation Serialization

The following operations for the same Register MUST be mutually exclusive:

```text
mutation
rebuild
recovery
```

The serialization owner is:

```text
RegisterOperationDomain
```

The maintenance coordinator MUST NOT create a second Register-scoped operation lock.

Its private synchronization, if retained, is limited to protecting its own state representation.

---

# 16. Rebuild / Recovery Serialization

Rebuild and recovery also use the same domain:

```python
domain = domains.get(register_identity)
```

Therefore:

```text
rebuild
    ↕
recovery
```

cannot execute concurrently for the same Register.

The Operation Domain does not distinguish their semantics.

Both are simply Register-scoped consistency-sensitive operations.

---

# 17. Different Register Isolation

The registry provides one domain per Register identity:

```python
domain_a = domains.get(register_a)
domain_b = domains.get(register_b)
```

Therefore operations on:

```text
Register A
Register B
```

remain independently serializable.

WP-5 MUST NOT introduce a global rebuild/recovery lock.

---

# 18. Recovery API Semantics

The public API remains:

```python
totals.recover(register_identity)
```

The recommended semantic implementation remains:

```python
def recover(
    self,
    register_identity: Identifier,
) -> MaintenanceResult:
    return self.rebuild(register_identity)
```

This is acceptable because recovery uses authoritative reconstruction.

However, the public semantic meaning remains:

```text
recover
    = restore valid derived state
```

not:

```text
recover
    = ordinary mutation
```

No `MaintenanceOperation.RECOVER` is required.

The `MaintenanceResult.operation` may therefore remain:

```text
MaintenanceOperation.REBUILD
```

when recovery delegates directly to rebuild.

---

# 19. Failure Classification

WP-5 MUST preserve the existing failure hierarchy.

### Persistence deterministic failure

```python
PersistenceError
```

results in:

```text
MaintenanceOutcome.FAILURE
ACTIVE + RECOVERY_REQUIRED
```

### Persistence indeterminate failure

```python
PersistenceIndeterminateError
```

results in:

```text
MaintenanceOutcome.INDETERMINATE
ACTIVE + RECOVERY_REQUIRED
```

### Totals failure

```python
TotalsError
```

results in:

```text
MaintenanceOutcome.FAILURE
ACTIVE + RECOVERY_REQUIRED
```

### Unexpected failure

Unexpected exceptions remain:

```text
MaintenanceOutcome.INDETERMINATE
ACTIVE + RECOVERY_REQUIRED
```

No failure path may return:

```text
SUCCESS
ACTIVE + VALID
```

---

# 20. Rebuild Result Contract

Successful rebuild:

```python
MaintenanceResult(
    operation=MaintenanceOperation.REBUILD,
    outcome=MaintenanceOutcome.SUCCESS,
    state=TotalsMaintenanceState(
        lifecycle=TotalsLifecycleState.ACTIVE,
        consistency=TotalsConsistencyState.VALID,
    ),
)
```

Failure and indeterminate results retain the existing `MaintenanceResult` structure.

WP-5 does not introduce a new result type.

---

# 21. No Rebuild API on RegisterMutationOrchestrator

`RegisterMutationOrchestrator` remains responsible for ordinary mutation:

```text
establish
remove
```

WP-5 MUST NOT add:

```python
mutation.rebuild(...)
mutation.recover(...)
```

to this class.

Doing so would combine ordinary mutation orchestration and maintenance recovery semantics.

The composition boundary remains:

```text
RegisterMutationOrchestrator
    → ordinary mutation

TotalsMaintenanceCoordinator
    → maintenance semantics

RegisterOperationDomain
    → Register-scoped serialization
```

---

# 22. No New Rebuild / Recovery Service

WP-5 MUST NOT introduce a class such as:

```python
RegisterRebuildService
RegisterRecoveryService
BootstrapCoordinator
MaintenanceRecoveryCoordinator
```

unless a concrete repository integration requirement appears that cannot be satisfied through the existing contracts.

The current architecture provides sufficient composition:

```text
Registry
    ↓
Operation Domain
    ↓
Maintenance Coordinator
```

---

# 23. Coordinator Internal Synchronization

The coordinator MAY retain private synchronization for:

```text
_states
_applied
```

if required to protect Coordinator-owned state.

This synchronization MUST NOT:

* replace `RegisterOperationDomain`;
* serialize complete Register operations;
* establish operation ordering;
* become mutation admission;
* create a second Register operation boundary.

The distinction is:

```text
Coordinator private synchronization
    = protect internal state

RegisterOperationDomain
    = serialize Register operations
```

---

# 24. Required Integration Composition

The intended complete composition is:

```text
                 RegisterOperationDomainRegistry
                              │
                              ▼
                   RegisterOperationDomain
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
      mutation            rebuild             recovery
          │                   │                   │
          ▼                   └────────┬──────────┘
 RegisterMutation                      │
 Orchestrator                          ▼
                              TotalsMaintenance
                                 Coordinator
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                RegisterFactPersistence       TotalsEngine
                         │                         │
                         ▼                         ▼
                  Movement Facts                Totals
```

The composition introduces no additional semantic layer.

---

# 25. Required Test API Boundaries

WP-5 tests MUST test both:

### Coordinator-level semantics

```python
totals.rebuild(register_identity)
totals.recover(register_identity)
totals.state(register_identity)
totals.ensure_mutation_admitted(register_identity)
```

and:

### Operation-domain integration

```python
domain.execute(
    lambda: totals.rebuild(register_identity)
)

domain.execute(
    lambda: totals.recover(register_identity)
)
```

This distinction is important.

Coordinator unit tests verify maintenance semantics.

Integration tests verify the Register-scoped serialization boundary.

---

# 26. Required Test Cases

The implementation MUST cover at least:

### Bootstrap

```text
new coordinator
→ CREATED + INDETERMINATE
→ mutation rejected
```

### Empty Register rebuild

```text
enumerate() → ()
rebuild()
→ ACTIVE + VALID
```

### Populated Register rebuild

```text
enumerate() → M1, M2, M3
rebuild()
→ Totals(M1, M2, M3)
→ ACTIVE + VALID
```

### Deterministic rebuild

```text
rebuild()
rebuild()
→ same Totals
→ same maintenance state
```

### Recovery

```text
RECOVERY_REQUIRED
recover()
→ ACTIVE + VALID
```

### Persistence failure

```text
enumerate()
→ PersistenceError
→ FAILURE + RECOVERY_REQUIRED
```

### Persistence indeterminate failure

```text
enumerate()
→ PersistenceIndeterminateError
→ INDETERMINATE + RECOVERY_REQUIRED
```

### Totals failure

```text
engine.rebuild()
→ TotalsError
→ FAILURE + RECOVERY_REQUIRED
```

### Unexpected failure

```text
unexpected exception
→ INDETERMINATE + RECOVERY_REQUIRED
```

### Mutation / rebuild race

Both operations use the same:

```text
RegisterOperationDomain
```

and cannot concurrently produce stale derived state.

### Recovery / mutation race

Same requirement as rebuild / mutation.

### Different Registers

Operations on different Registers remain independent.

---

# 27. Concrete Implementation Changes Expected

WP-5 implementation SHOULD be minimal.

Expected changes are primarily:

```text
1. Verify current maintenance rebuild semantics.
2. Verify rebuild/recovery composition through Registry.
3. Add or adjust the required platform-level invocation path.
4. Add integration tests for the shared operation domain.
5. Add bootstrap admission integration tests.
6. Add rebuild/recovery concurrency tests.
```

The implementation SHOULD NOT require a new public abstraction.

If current `DefaultTotalsMaintenanceCoordinator.rebuild()` remains semantically correct, it SHOULD NOT be rewritten merely for WP-5.

---

# 28. API Invariants

### A. Bootstrap Safety

```text
CREATED + INDETERMINATE
    → mutation rejected
```

### B. Authoritative Rebuild

```text
RegisterFactPersistence
    → authoritative Movement Facts
```

### C. Fresh Reconstruction

```text
TotalsEngine.rebuild()
    → fresh derived Totals
```

### D. Runtime State Reconstruction

```text
successful rebuild
    → replace _applied
```

### E. Atomic Register Operation Boundary

```text
enumerate
→ rebuild
→ _applied reconstruction
→ state publication
```

must occur inside one Register Operation Domain critical section.

### F. Shared Serialization

```text
mutation
rebuild
recovery
```

for the same Register use the same domain.

### G. Register Isolation

Different Registers use different operation domains.

### H. Recovery Semantics

```text
recover()
→ authoritative reconstruction
```

### I. Failure Preservation

Failure MUST NOT publish:

```text
ACTIVE + VALID
```

### J. No Second Semantic Owner

Maintenance lifecycle and consistency state remain owned by:

```text
TotalsMaintenanceCoordinator
```

### K. Runtime-only `_applied`

`_applied` is never authoritative persistence.

### L. No New Orchestration Abstraction

Existing composition boundaries are sufficient.

---

# 29. Acceptance Criteria

WP-5 Concrete API Design is considered satisfied when:

1. Bootstrap admission is explicitly defined.
2. Rebuild uses `RegisterFactPersistence.enumerate()`.
3. Rebuild uses fresh `TotalsEngine.rebuild()`.
4. Runtime `_applied` is reconstructed only after successful rebuild.
5. Rebuild executes inside the shared `RegisterOperationDomain`.
6. Recovery uses the same operation domain.
7. Recovery remains semantically distinct from ordinary mutation.
8. No `MaintenanceOperation.RECOVER` is introduced.
9. Failure and indeterminate semantics remain unchanged.
10. `ACTIVE + VALID` is published only after successful reconstruction.
11. Same-register mutation/rebuild/recovery are serialized.
12. Different Registers remain isolated.
13. `_applied` remains runtime-only.
14. `RegisterMutationOrchestrator` remains focused on ordinary mutation.
15. No new orchestration abstraction is introduced.
16. Required integration tests can be implemented against the existing public APIs.

---

# 30. Final API Principle

The concrete WP-5 API model is:

```text
RegisterOperationDomainRegistry
            │
            ▼
RegisterOperationDomain
            │
            ├── mutation
            ├── rebuild
            └── recovery
                     │
                     ▼
          TotalsMaintenanceCoordinator
                     │
              ┌──────┴──────┐
              ▼             ▼
 RegisterFactPersistence  TotalsEngine
              │             │
              ▼             ▼
       authoritative       derived
          facts            Totals
```

The essential implementation rule is:

> **The Operation Domain owns Register-scoped execution serialization; the Maintenance Coordinator owns Bootstrap, Rebuild, Recovery, and maintenance state semantics; Persistence owns authoritative Movement Facts; TotalsEngine owns derived aggregation.**

No layer may assume responsibility belonging to another layer.

This completes the WP-5 Concrete API Design boundary without changing the approved WP-5 architecture.

The implemented production composition resolves the shared `RegisterOperationDomain` from `RegisterOperationDomainRegistry` and executes the corresponding `TotalsMaintenanceCoordinator` operation inside that domain. No additional orchestration abstraction is required or introduced.

Direct calls to TotalsMaintenanceCoordinator.rebuild() / recover() remain valid at the coordinator semantic/unit-test boundary, but every platform-level Register-scoped invocation MUST pass through the shared RegisterOperationDomain.

---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
