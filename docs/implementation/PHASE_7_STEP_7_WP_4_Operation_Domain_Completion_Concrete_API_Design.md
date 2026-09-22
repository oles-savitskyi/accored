# Phase 7 — Step 7 — WP-4 Operation Domain Completion

## Concrete API Design

### 1. Purpose

This document translates the approved WP-4 Architecture Definition, Architecture Contract, and Architecture Scope into a concrete API model.

The API Design defines:

* `RegisterOperationDomain`;
* `RegisterOperationDomainRegistry`;
* mutation integration through `RegisterMutationOrchestrator`;
* maintenance integration through `TotalsMaintenanceCoordinator`;
* the execution model for mutation, rebuild, and recovery;
* the synchronization boundary of `TotalsMaintenanceCoordinator`;
* orchestration ownership;
* required structural and behavioral invariants.

This document does not change any approved Phase 7 semantic contracts.

The central design principle is:

> **The Operation Domain serializes the operation. The Maintenance Coordinator owns the semantic meaning and state of maintenance.**

---

# 2. API Ownership Model

After WP-4, responsibilities are divided as follows:

| Component                         | Owns                                                | Does not own                         |
| --------------------------------- | --------------------------------------------------- | ------------------------------------ |
| `RegisterOperationDomain`         | Register-scoped operation serialization             | semantic lifecycle/consistency state |
| `RegisterOperationDomainRegistry` | stable domain composition                           | maintenance semantics                |
| `RegisterMutationOrchestrator`    | mutation orchestration                              | Register serialization ownership     |
| `TotalsMaintenanceCoordinator`    | maintenance semantic state and maintenance outcomes | Register operation serialization     |
| `RegisterFactPersistence`         | authoritative Movement Facts persistence            | Totals state                         |
| `TotalsEngine`                    | Totals calculation                                  | operation serialization              |

The ownership boundary is therefore:

```text
RegisterOperationDomain
    → "Which consistency-sensitive operation may execute now?"

TotalsMaintenanceCoordinator
    → "What is the semantic maintenance state and result?"
```

No component may assume both responsibilities.

TotalsMaintenanceCoordinator remains the semantic API for rebuild and recovery.

The caller responsible for initiating a maintenance operation is also responsible for obtaining the shared 

RegisterOperationDomain and executing that semantic operation through the domain.

---

# 3. Orchestration API Consistency

## 3.1. Mutation Orchestration

`RegisterMutationOrchestrator` is a mutation-specific orchestration component.

Its semantic API is limited to mutation operations:

```python
class RegisterMutationOrchestrator:
    def establish(...) -> None:
        ...

    def remove(...) -> None:
        ...
```

It MUST NOT expose `rebuild()` or `recover()` as part of its semantic API.

This keeps the responsibility of the component aligned with its name and architectural role.

---

## 3.2. Maintenance Operations

`rebuild()` and `recover()` remain semantic operations of `TotalsMaintenanceCoordinator`.

Conceptually:

```python
class TotalsMaintenanceCoordinator:
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

Their Register-scoped serialization is provided externally through the same:

```text
RegisterOperationDomainRegistry
        │
        ▼
RegisterOperationDomain
```

used by mutation.

The Coordinator therefore owns the **meaning and state transition** of rebuild/recovery, while the Operation Domain owns their **serialization**.

---

## 3.3. No Semantic Operations on the Domain

`RegisterOperationDomain` remains generic.

It MUST NOT expose:

```python
domain.mutate(...)
domain.rebuild(...)
domain.recover(...)
```

because that would transfer semantic operation knowledge into the serialization component.

The Domain only provides:

```python
domain.execute(operation)
```

---

## 3.4. Maintenance Orchestration Without a New Semantic Layer

WP-4 does not require introducing a new `MaintenanceOrchestrator` solely to mirror `RegisterMutationOrchestrator`.

The existing `TotalsMaintenanceCoordinator` remains the semantic maintenance API.

Where an application or platform composition layer needs to invoke `rebuild()` or `recover()`, it obtains the shared Domain from `RegisterOperationDomainRegistry` and executes the Coordinator operation through that Domain.

Conceptually:

```text
Maintenance caller
       │
       ▼
RegisterOperationDomainRegistry
       │
       ▼
RegisterOperationDomain
       │
       ▼
TotalsMaintenanceCoordinator
       │
       ├── rebuild()
       └── recover()
```

This preserves a clean distinction between:

* semantic maintenance;
* operation serialization;
* application-level invocation.

### Maintenance Invocation Boundary

Rebuild and recovery remain semantic operations of `TotalsMaintenanceCoordinator`.

Their Register-scoped invocation is composed through the shared
`RegisterOperationDomainRegistry`.

The composition layer MUST:

1. resolve the `RegisterOperationDomain` from the shared registry;
2. execute the maintenance operation through that domain;
3. pass the operation to `TotalsMaintenanceCoordinator` unchanged.

Canonical forms:

    domain = domains.get(register_identity)
    result = domain.execute(
        lambda: totals.rebuild(register_identity),
    )

    domain = domains.get(register_identity)
    result = domain.execute(
        lambda: totals.recover(register_identity),
    )

The `TotalsMaintenanceCoordinator` MUST NOT expose an alternative
Register-scoped serialization entry point.

WP-4 does not introduce a `MaintenanceOrchestrator` solely to wrap these
operations. A new maintenance orchestration abstraction would require a
separate architectural decision if an existing application integration
point later demonstrates a concrete need for one.

The semantic ownership therefore remains:

- `RegisterOperationDomain` — operation serialization;
- `TotalsMaintenanceCoordinator` — rebuild/recovery semantics and
  maintenance state;
- composition/application layer — invocation wiring.

---

# 4. RegisterOperationDomain

## 4.1. Public Contract

`RegisterOperationDomain` represents one Register-scoped execution boundary.

The minimal public API is:

```python
class RegisterOperationDomain:
    @property
    def register_identity(self) -> Identifier:
        ...

    def execute(self, operation: Callable[[], T]) -> T:
        ...
```

where `T` is the return type of the supplied operation.

`execute()` is the only API through which a consistency-sensitive Register operation obtains the Register-scoped serialization boundary.

---

## 4.2. Execute Semantics

`execute(operation)` MUST:

1. acquire the serialization boundary of the corresponding Register;
2. wait until the boundary is available;
3. execute `operation`;
4. return the operation result;
5. release the boundary regardless of operation success or failure;
6. avoid changing maintenance semantic state itself.

Conceptually:

```text
domain.execute(operation)
        │
        ▼
 acquire Register boundary
        │
        ▼
     operation()
        │
        ▼
 release Register boundary
```

An exception raised by `operation` MUST NOT leave the Domain boundary held after the invocation terminates.

---

## 4.3. Generic Return Value

`execute()` supports arbitrary return values:

```python
result = domain.execute(operation)
```

This is required for operations returning:

* `MaintenanceResult`;
* existing operation results;
* internal orchestration values.

The Operation Domain MUST NOT interpret the returned value.

---

# 5. RegisterOperationDomain Reentrancy

Reentrant execution may be supported as an implementation property where required for safe internal delegation.

For example:

```text
domain.execute(...)
    │
    └── coordinator operation
             │
             └── internal delegation
```

Nested delegation within one logical Register operation MUST NOT:

* create a second logical Register Domain;
* create a competing Register serialization boundary;
* bypass the existing Domain;
* introduce deadlock solely because of internal delegation.

The Concrete API MUST NOT expose manual:

```python
acquire()
release()
```

operations for ordinary callers.

Serialization ownership remains encapsulated by `execute()`.

The exact synchronization primitive and reentrancy mechanism are implementation concerns and are not part of the semantic API.

---

# 6. RegisterOperationDomainRegistry

## 6.1. Public API

The Registry provides the stable Operation Domain for a Register:

```python
class RegisterOperationDomainRegistry:
    def get(
        self,
        register_identity: Identifier,
    ) -> RegisterOperationDomain:
        ...
```

---

## 6.2. Identity Stability

For the same Register:

```python
domain_a = registry.get(register_identity)
domain_b = registry.get(register_identity)
```

the calls MUST resolve to the same logical serialization boundary.

The implementation may satisfy this through object identity or an equivalent mechanism.

For different Registers:

```python
domain_a = registry.get(register_a)
domain_b = registry.get(register_b)
```

the Domains MUST provide independent serialization boundaries.

---

# 7. Registry Ownership and Composition

`RegisterOperationDomainRegistry` is a shared composition dependency.

All components participating in Register-scoped consistency-sensitive operations MUST obtain their Domain from the same Registry within the composition graph.

Target composition:

```text
                 Shared Registry
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Mutation      Rebuild      Recovery
          │            │            │
          └────────────┼────────────┘
                       ▼
                same Register
                       │
                       ▼
                 same Domain
```

A component MUST NOT create its own Registry for the same composition graph.

In particular, an independent Registry MUST NOT be created inside:

* `RegisterMutationOrchestrator`;
* `TotalsMaintenanceCoordinator`;
* another Register operation component.

The Registry is therefore a structural composition boundary, not merely a lock cache.

---

# 8. RegisterMutationOrchestrator

## 8.1. Constructor

`RegisterMutationOrchestrator` receives the shared Registry:

```python
class RegisterMutationOrchestrator:
    def __init__(
        self,
        persistence: RegisterFactPersistence,
        totals: TotalsMaintenanceCoordinator,
        domains: RegisterOperationDomainRegistry,
        validator: MovementValidator,
    ) -> None:
        ...
```

The existing dependency shape is preserved.

`domains` is a required architectural dependency because mutation serialization is no longer owned by the Coordinator.

---

# 9. Mutation Execution

## 9.1. Preliminary Validation

Non-mutating validation MAY execute before entering the Register Operation Domain:

```text
movements
    │
    ▼
pre-validation
    │
    ▼
domain lookup
```

Such validation does not violate the serialization contract because it does not change authoritative or derived Register state.

---

## 9.2. State-Changing Mutation

After preliminary validation, all state-changing parts of the mutation execute within the Domain:

```python
domain = self._domains.get(register_identity)

def operation() -> None:
    self._totals.ensure_mutation_admitted(register_identity)
    self._persistence.append(movements_tuple)

    for movement in movements_tuple:
        result = self._totals.apply(movement)
        self._ensure_totals_success(register_identity, result)

domain.execute(operation)
```

The exact existing mutation semantics remain unchanged.

The architectural change is that the Domain becomes the sole Register-scoped serialization boundary.

---

## 9.3. Complete Mutation Boundary

The following actions MUST belong to the same `domain.execute(...)` invocation:

* semantic mutation admission;
* authoritative Movement Facts mutation;
* corresponding Totals mutation;
* operation-level consistency checks required by the existing contract.

Authoritative persistence mutation and corresponding Totals mutation MUST NOT be divided between different Register serialization contexts.

The target boundary is:

```text
pre-validation
      │
      ▼
RegisterOperationDomain
      │
      ├── mutation admission
      ├── authoritative Movement Facts mutation
      └── corresponding Totals mutation
```

---

# 10. Remove Mutation

`remove()` follows the same operation-domain model:

```text
pre-validation
      │
      ▼
RegisterOperationDomain
      │
      ├── mutation admission
      ├── authoritative removal
      └── Totals removal
```

The public `remove()` API and its semantic contract remain unchanged.

---

# 11. Rebuild Integration

`rebuild()` remains a semantic operation of `TotalsMaintenanceCoordinator`.

The caller responsible for Register-scoped execution obtains the shared Domain:

```python
domain = domains.get(register_identity)

result = domain.execute(
    lambda: totals.rebuild(register_identity)
)
```

This guarantees that rebuild:

* uses the same Domain as mutation for the same Register;
* is mutually exclusive with mutation;
* is mutually exclusive with another rebuild;
* is mutually exclusive with recovery.

The Coordinator MUST NOT perform an additional Register-scoped locking step.

The semantic meaning of rebuild remains unchanged.

---

# 12. Recovery Integration

`recover()` follows the same model:

```python
domain = domains.get(register_identity)

result = domain.execute(
    lambda: totals.recover(register_identity)
)
```

Recovery:

* uses the same Domain as mutation and rebuild;
* remains a distinct semantic maintenance operation;
* is mutually exclusive with mutation;
* is mutually exclusive with rebuild;
* is mutually exclusive with another recovery.

If the semantic implementation of recovery delegates to rebuild, that remains a Coordinator-level semantic decision.

The Operation Domain does not distinguish between mutation, rebuild, and recovery.

For the Domain, all three are consistency-sensitive Register operations.

---

# 13. TotalsMaintenanceCoordinator API

The Coordinator retains its semantic maintenance API:

```python
class TotalsMaintenanceCoordinator:
    def apply(...):
        ...

    def remove(...):
        ...

    def rebuild(...):
        ...

    def recover(...):
        ...

    def state(...):
        ...

    def ensure_mutation_admitted(...):
        ...
```

The precise return types and arguments remain those defined by the existing maintenance contracts.

WP-4 does not change their semantic meaning.

The key change is that these methods no longer own Register-scoped operation serialization.

The Coordinator MUST NOT expose a new operation-domain API such as:

```python
execute(...)
acquire(...)
release(...)
lock_for(...)
```

---

# 14. Coordinator Internal Synchronization Boundary

The `TotalsMaintenanceCoordinator` MAY retain private synchronization required to protect its own semantic state.

Conceptually:

```text
TotalsMaintenanceCoordinator
        │
        ├── semantic maintenance state
        │
        └── private state synchronization
```

This synchronization is permitted only as an implementation mechanism for protecting Coordinator-owned state.

It MUST NOT:

* constitute the Register Operation Domain;
* reproduce the Register Operation Domain;
* serialize complete Register operations;
* serve as an operation admission boundary;
* define operation ordering;
* replace or supplement `RegisterOperationDomain`;
* create a competing per-Register operation lock map.

The mere existence of a synchronization primitive inside the Coordinator is therefore not an architectural violation.

Its **role** as a competing Register-scoped operation boundary would be.

### Design Rule

> **Do not retain synchronization merely because the previous implementation had a lock. Retain or introduce synchronization only when required to protect Coordinator-owned semantic state.**

If no additional synchronization is required after removal of the pre-WP-4 per-Register operation locking model, no replacement lock should be introduced.

---

# 15. Removal from the Coordinator

The current Register-operation serialization model in `DefaultTotalsMaintenanceCoordinator` MUST be removed where it exists solely to serialize Register operations.

This includes structures such as:

```python
_locks_guard
_locks
_lock_for(...)
```

when their purpose is Register-scoped operation serialization.

The Coordinator MUST NOT independently construct:

```text
Register identity
      │
      ▼
RLock
```

for the purpose of serializing:

* `apply`;
* `remove`;
* `rebuild`;
* `recover`.

Any remaining private synchronization must protect Coordinator-owned semantic state only.

---

# 16. State Read Semantics

If `state(register_identity)` requires synchronization to obtain a consistent view of Coordinator-owned semantic state, such synchronization MAY remain internal to the Coordinator.

However:

```python
coordinator.state(register_identity)
```

MUST NOT become an alternative entry point into the Register Operation Domain.

Therefore:

```text
Coordinator state synchronization
        ≠
Register operation serialization
```

These are separate concerns.

---

# 17. Mutation Admission

`ensure_mutation_admitted(register_identity)` remains a semantic admission decision owned by the Coordinator.

The responsibilities are deliberately distinct:

```text
RegisterOperationDomain
    → "May this Register operation execute concurrently with another?"

TotalsMaintenanceCoordinator
    → "Is this mutation semantically admissible in the current state?"
```

Therefore:

```text
domain.execute(...)
        │
        ▼
ensure_mutation_admitted(...)
```

The first establishes serialization.

The second evaluates semantic admission.

Neither component takes ownership of the other's responsibility.

---

# 18. Failure Semantics

The Operation Domain MUST NOT introduce its own maintenance failure-state model.

For example, the Domain MUST NOT create or own:

```python
TotalsConsistencyState(...)
TotalsLifecycleState(...)
MaintenanceResult(...)
```

or independently modify Coordinator state transitions.

Maintenance failure semantics remain owned by the Coordinator.

If the supplied operation raises an exception:

```text
RegisterOperationDomain
        │
        └── operation raises
                 │
                 ▼
             propagate
```

unless an existing higher-level contract explicitly requires different handling.

The Domain is responsible for releasing its serialization boundary correctly, not for interpreting maintenance failures.

---

# 19. Operation Domain State

`RegisterOperationDomain` MUST NOT own semantic maintenance state such as:

```text
lifecycle state
consistency state
recovery state
applied movements
maintenance outcomes
```

Any Domain-internal state is limited to technical execution/serialization concerns.

The architectural separation is therefore:

```text
RegisterOperationDomain
    → technical execution state

TotalsMaintenanceCoordinator
    → semantic maintenance state
```

---

# 20. Register Isolation

The Registry MUST provide independent logical Domains for different Registers.

For example:

```python
domain_a = domains.get(register_a)
domain_b = domains.get(register_b)
```

An operation executed through:

```python
domain_a.execute(...)
```

MUST NOT block:

```python
domain_b.execute(...)
```

solely because of operation-domain serialization.

The Registry MUST NOT introduce a hidden global lock that serializes unrelated Registers.

---

# 21. Public Exports

If `RegisterOperationDomain` and `RegisterOperationDomainRegistry` are public platform concepts, they MUST be exported from the appropriate `registers` package according to existing package conventions.

Implementation-private synchronization primitives MUST NOT become public exports.

No new public semantic abstraction is introduced solely for WP-4 unless required by the approved architecture.

---

# 22. Required Tests

Concrete implementation MUST provide both behavioral and structural verification.

## 22.1. Registry Identity

Verify:

* same Register → same logical Domain;
* different Registers → independent Domains.

---

## 22.2. Domain Serialization

Verify mutual exclusion for:

* mutation ↔ mutation;
* mutation ↔ rebuild;
* mutation ↔ recovery;
* rebuild ↔ rebuild;
* rebuild ↔ recovery;
* recovery ↔ recovery.

For each pair, the second operation MUST NOT enter its consistency-sensitive body while the first operation is still executing.

---

## 22.3. Register Isolation

Verify at minimum:

* Register A mutation ↔ Register B mutation;
* Register A rebuild ↔ Register B rebuild;
* Register A recovery ↔ Register B recovery.

The tests MUST demonstrate absence of unnecessary cross-Register serialization.

---

## 22.4. Coordinator Structural Ownership

Verify that the Coordinator:

* does not retain a competing per-Register operation lock model;
* does not create its own Operation Domain;
* remains the owner of maintenance semantic state;
* does not expose operation-domain management APIs.

---

## 22.5. Shared Registry Composition

Verify that mutation, rebuild, and recovery use the same Registry and resolve to the same logical Domain for the same Register.

This test is important because equivalent independent locks do not satisfy the structural architecture.

---

## 22.6. Mutation Boundary

Verify that authoritative Movement Facts mutation and corresponding Totals mutation execute inside the same Register Operation Domain boundary.

The test MUST verify the execution boundary itself, not only the final state.

---

## 22.7. Coordinator Synchronization

If private Coordinator synchronization remains after implementation, verify that it protects only Coordinator-owned semantic state and does not serialize complete Register operations.

---

## 22.8. Regression

Existing WP-3 tests MUST continue to verify:

* maintenance lifecycle semantics;
* failure semantics;
* consistency states;
* rebuild/recovery behavior;
* mutation admission behavior.

---

# 23. Implementation Constraints

Implementation MUST follow these constraints:

1. Do not add a new global lock.
2. Do not move semantic maintenance state into the Domain.
3. Do not move mutation, rebuild, or recovery semantics into the Domain.
4. Do not retain a competing Register-scoped operation lock in the Coordinator.
5. Do not create a second Registry for the same composition graph.
6. Do not change public semantic contracts without a separate architectural decision.
7. Do not add transaction infrastructure.
8. Do not perform unrelated refactoring.
9. Do not change the Totals algorithm.
10. Do not change the persistence model.
11. Do not introduce a new maintenance orchestration abstraction unless an existing integration point proves that it is architecturally necessary.
12. Do not make `RegisterMutationOrchestrator` responsible for rebuild or recovery.

---

# 24. Target Composition

The target composition after WP-4 is:

```text
                 RegisterOperationDomainRegistry
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
 RegisterMutationOrchestrator       Maintenance caller
               │                             │
               │                    ┌────────┴────────┐
               │                    │                 │
               ▼                    ▼                 ▼
          mutation               rebuild           recovery
               │                    │                 │
               └────────────────────┼─────────────────┘
                                    ▼
                         RegisterOperationDomain
                                    │
                                    ▼
                    consistency-sensitive operation
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                    Persistence      TotalsMaintenanceCoordinator
                                               │
                                               ▼
                                  semantic maintenance state
```

For one Register, all consistency-sensitive operations resolve to the same Domain.

For different Registers:

```text
Register A → Domain A
Register B → Domain B
```

with independent serialization boundaries.

---

# 25. API Invariants

The concrete implementation MUST preserve the following invariants.

### A. Stable Domain

One Register resolves to one logical serialization boundary.

### B. Shared Domain

Mutation, rebuild, and recovery for one Register use the same logical Domain.

### C. Single Serialization Owner

`RegisterOperationDomain` is the sole owner of Register-scoped operation serialization.

### D. Semantic State Owner

`TotalsMaintenanceCoordinator` is the sole owner of maintenance semantic state.

### E. No Competing Coordinator Boundary

The Coordinator does not provide an alternative Register-scoped serialization mechanism.

### F. Complete Mutation Boundary

Authoritative Movement Facts mutation and corresponding Totals mutation execute inside one Domain boundary.

### G. Register Isolation

Different Registers do not block each other through a shared operation lock.

### H. Failure Preservation

The Operation Domain does not change existing maintenance failure semantics.

### I. Generic Execution

The Domain does not know the semantic meaning of mutation, rebuild, or recovery.

### J. Shared Composition

All consistency-sensitive components use the shared `RegisterOperationDomainRegistry`.

### K. Orchestration Consistency

`RegisterMutationOrchestrator` is responsible only for mutation orchestration. Rebuild and recovery remain maintenance operations of `TotalsMaintenanceCoordinator`.

### L. Synchronization Boundary Separation

Any private synchronization retained by `TotalsMaintenanceCoordinator` protects only its own semantic state and is not a competing Register operation boundary.

### M. Maintenance Invocation Boundary

Every Register-scoped rebuild or recovery invocation participating in the operation domain must resolve the shared RegisterOperationDomain and invoke the corresponding TotalsMaintenanceCoordinator operation through it. No direct Register-scoped invocation may bypass the shared domain.

---

# 26. Migration from the Current Implementation

WP-4 implementation should follow this minimal migration path:

1. finalize the `RegisterOperationDomain` API;
2. finalize the `RegisterOperationDomainRegistry` API;
3. confirm shared Registry composition;
4. restrict `RegisterMutationOrchestrator` to mutation orchestration;
5. confirm the mutation state-changing boundary;
6. integrate rebuild through the shared Domain;
7. integrate recovery through the shared Domain;
8. remove the competing per-Register operation lock model from the Coordinator;
9. determine whether any private Coordinator state synchronization remains necessary;
10. add structural tests;
11. add serialization and isolation tests;
12. run the existing regression suite;
13. run the complete quality gate.

No semantic redesign is part of this migration.

---

# 27. Acceptance Criteria

The Concrete API Design is considered implemented when all of the following are true:

* `RegisterOperationDomain.execute()` is the sole Register-scoped serialization API;
* the shared Registry provides a stable logical Domain per Register;
* the mutation state-changing boundary is inside the Domain;
* `RegisterMutationOrchestrator` exposes mutation operations only;
* rebuild remains a Coordinator semantic operation and executes through the shared Domain;
* recovery remains a Coordinator semantic operation and executes through the shared Domain;
* the Coordinator no longer owns a competing Register-scoped operation lock;
* any remaining Coordinator synchronization protects only Coordinator-owned semantic state;
* the Coordinator remains the semantic maintenance state owner;
* different Registers remain independently executable;
* WP-3 semantics are preserved;
* structural and concurrency tests confirm the approved invariants.

---

# 28. Final API Principle

WP-4 should result in a simple and verifiable model:

```text
One Register
    │
    ▼
One Operation Domain
    │
    ├── mutation
    ├── rebuild
    └── recovery
    │
    ▼
Semantic operation owners
    │
    ├── RegisterMutationOrchestrator
    │       └── mutation
    │
    └── TotalsMaintenanceCoordinator
            ├── rebuild
            └── recovery
```

with:

```text
Register A → Domain A
Register B → Domain B
```

and:

```text
Operation Domain
    → serialization

Mutation Orchestrator
    → mutation orchestration

Totals Maintenance Coordinator
    → maintenance semantics and semantic state
```

The final architectural principle is:

> **The Operation Domain serializes the operation. Semantic components own the meaning of the operation. The Maintenance Coordinator owns maintenance state. No component owns both serialization and semantic maintenance state.**


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
