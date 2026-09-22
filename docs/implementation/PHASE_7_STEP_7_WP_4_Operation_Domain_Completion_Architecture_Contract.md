# Phase 7 — Step 7 — WP-4 Operation Domain Completion

## Architecture Contract

## 1. Purpose

This contract defines the externally observable architectural guarantees of the completed Register Operation Domain.

The purpose of WP-4 is to establish one and only one Register-scoped serialization boundary for consistency-sensitive operations while preserving the existing semantic ownership of totals maintenance.

WP-4 does not redefine Totals semantics, persistence semantics, or maintenance state semantics.

It completes the operation boundary around the already approved architecture.

---

## 2. Architectural Responsibilities

### 2.1 Register Operation Domain

The Register Operation Domain is responsible for:

* Register-scoped serialization;
* mutual exclusion of consistency-sensitive operations for the same Register;
* admission of operations into the Register-scoped execution boundary;
* isolation between different Registers.

The Operation Domain is not responsible for:

* Totals lifecycle state;
* Totals consistency state;
* maintenance semantic state;
* ownership of authoritative Movement Facts;
* calculation of Totals;
* recovery semantics.

---

### 2.2 Register Operation Domain Registry

The Registry is responsible for providing the stable logical Operation Domain associated with a Register identity.

The following contract applies:

```text
same Register identity
    → same logical Operation Domain

different Register identities
    → different logical Operation Domains
```

The Registry therefore represents a structural composition boundary, not merely a collection of equivalent locks.

All components participating in Register-scoped consistency-sensitive operations must obtain their domain through the same Registry boundary.

Independent per-component locks do not satisfy this contract.

---

### 2.3 Totals Maintenance Coordinator

The Totals Maintenance Coordinator remains the sole semantic owner of maintenance state.

It owns:

* `TotalsMaintenanceState`;
* lifecycle state;
* consistency state;
* semantic maintenance bookkeeping;
* maintenance outcomes;
* mutation admission semantics;
* rebuild semantics;
* recovery semantics.

The coordinator must not own a competing Register-scoped serialization boundary.

Its semantic state must remain independent from the implementation mechanism used to serialize operations.

---

## 3. Operation Classes Covered by the Contract

The following operations participate in the Register Operation Domain:

1. Register mutation;
2. Totals rebuild;
3. Totals recovery.

For a given Register, these operations are mutually exclusive.

The contract therefore applies to all pairs:

```text
mutation  ↔ mutation
mutation  ↔ rebuild
mutation  ↔ recovery
rebuild   ↔ rebuild
rebuild   ↔ recovery
recovery  ↔ recovery
```

No pair may execute concurrently when both operations target the same Register.

---

## 4. Register Isolation Contract

Serialization is scoped to a single Register.

Operations targeting different Registers must not be serialized by a shared global Register lock.

Conceptually:

```text
Register A
    └── Domain A
          ├── mutation
          ├── rebuild
          └── recovery

Register B
    └── Domain B
          ├── mutation
          ├── rebuild
          └── recovery
```

The existence of an active operation for Register A must not, by itself, prevent a consistency-sensitive operation for Register B from executing.

This isolation is an architectural guarantee, not merely an optimization.

---

## 5. Mutation Contract

A Register mutation consists of all state-changing actions that must remain consistent between authoritative Movement Facts and derived Totals.

Preliminary validation that does not mutate state may execute before entering the Operation Domain.

Once mutation begins, all state-changing actions participating in the mutation must execute within the same Register Operation Domain.

Conceptually:

```text
pre-validation
      │
      ▼
Register Operation Domain
      │
      ├── authoritative Movement Facts mutation
      │
      └── corresponding Totals maintenance mutation
```

The Operation Domain therefore defines the serialization boundary for the complete Register mutation.

A mutation must not be split into:

```text
persist outside domain
    +
totals mutation inside domain
```

when those actions participate in the same consistency-sensitive operation.

---

## 6. Rebuild Contract

A Totals rebuild for a Register must execute within the same Register Operation Domain used by mutation.

Rebuild must therefore be mutually exclusive with:

* mutation;
* another rebuild;
* recovery.

Rebuild remains a maintenance operation owned semantically by the Totals Maintenance Coordinator.

The Operation Domain does not acquire ownership of rebuild semantics.

The domain only guarantees that rebuild executes in the correct Register-scoped serialization context.

---

## 7. Recovery Contract

Recovery for a Register must execute within the same Register Operation Domain used by mutation and rebuild.

Recovery must therefore be mutually exclusive with:

* mutation;
* rebuild;
* another recovery.

Recovery remains a distinct semantic operation.

The fact that recovery and rebuild share the same serialization boundary does not make them the same operation.

In particular:

```text
rebuild ≠ recovery
```

and recovery semantics remain governed by the existing maintenance contract.

---

## 8. Single Serialization Boundary

For a given Register, there must be exactly one logical serialization boundary for the operations covered by this contract.

The following architecture is prohibited:

```text
Operation Domain
    └── Register lock

Totals Maintenance Coordinator
    └── Register lock
```

Even if both locks happen to use the same Register identity, they represent competing serialization mechanisms.

The required architecture is:

```text
Register Operation Domain
    └── single serialization boundary
          │
          └── Totals Maintenance Coordinator
                └── semantic maintenance state
```

The Maintenance Coordinator may perform internal synchronization required for its own implementation, but it must not introduce a second logical Register operation boundary.

---

## 9. Semantic State Ownership Contract

There must be exactly one semantic owner for Register totals maintenance state.

That owner is `TotalsMaintenanceCoordinator`.

The Operation Domain must not introduce a parallel representation of:

* lifecycle;
* consistency;
* recovery-required state;
* maintenance outcome;
* applied movement state;
* totals validity.

The following distinction is normative:

```text
Operation Domain
    = serialization and execution boundary

Totals Maintenance Coordinator
    = semantic maintenance state owner
```

No implementation detail may collapse these two responsibilities into one architectural concept.

---

## 10. Failure Contract

WP-4 must preserve the failure semantics established by the previous maintenance architecture.

In particular, WP-4 must not alter the meaning of:

* successful maintenance;
* ordinary maintenance failure;
* indeterminate maintenance outcome;
* recovery-required consistency state.

An Operation Domain execution failure must not independently create or replace Totals semantic state.

Semantic failure state must continue to be determined by the operation owner and existing maintenance rules.

The Operation Domain is therefore not a second failure-state machine.

---

## 11. Ordering Contract

For operations targeting the same Register, mutual exclusion is established by entry into the Register Operation Domain.

Only one covered operation may hold the domain's execution boundary at a time.

The contract does not require a specific fairness policy or scheduling order between waiting operations unless explicitly introduced by a later API contract.

Therefore WP-4 guarantees:

```text
mutual exclusion
```

but does not introduce:

```text
fairness
priority
queue ordering
```

as semantic requirements.

---

## 12. Reentrancy Contract

The Operation Domain must not introduce a semantic distinction between nested calls that belong to the same logical operation and independently competing operations.

Nested internal delegation within one logical Register operation must not create a second competing Register serialization boundary or allow an independently executing operation to bypass the existing boundary.

In particular, internal delegation such as:

```text
recover()
    → rebuild()
```

must not create a second competing Register operation boundary.

---

## 13. Composition Contract

The shared Registry is part of the platform composition boundary.

The following components must participate in the same domain model:

* Register mutation orchestration;
* Register totals rebuild;
* Register totals recovery;
* any future consistency-sensitive Register operation introduced under this architecture.

A component must not create a private Register-specific lock as an alternative serialization mechanism.

Adding a new consistency-sensitive operation therefore requires it to enter the existing Register Operation Domain rather than defining a new synchronization boundary.

---

## 14. Authoritative Data Contract

WP-4 does not change the authoritative source of Register movement facts.

Authoritative Movement Facts remain the source from which Totals may be reconstructed.

Therefore:

```text
Movement Facts
      │
      ▼
Totals
```

remains the approved architectural relationship.

Operation Domain serialization protects the consistency-sensitive execution of mutations and maintenance operations; it does not make Totals authoritative.

---

## 15. Determinism Contract

The Operation Domain must not introduce nondeterministic business semantics.

Register operation results must remain independent of:

* thread scheduling;
* lock acquisition timing;
* incidental execution order between different Registers;
* runtime object identity;
* uncontrolled external state.

Concurrency determines when an operation executes, not what its domain semantics mean.

---

## 16. Public Semantic Boundary

WP-4 does not require the Operation Domain to become a new business-facing API.

The domain is an infrastructure/platform boundary supporting the existing Register operations.

Existing public semantic contracts remain owned by their respective components:

```text
Register mutation
    → RegisterMutationOrchestrator

Totals maintenance
    → TotalsMaintenanceCoordinator

Register serialization
    → RegisterOperationDomain
```

No new public Totals semantic model is introduced by WP-4.

---

## 17. Non-Goals

This contract does not authorize:

* redesign of Totals aggregation;
* redesign of `TotalsKey`;
* changes to Balance semantics;
* changes to authoritative Movement Facts;
* changes to persistence contracts;
* introduction of global Register locking;
* introduction of a second lifecycle state machine;
* introduction of transaction infrastructure;
* introduction of distributed locking;
* Inventory-specific synchronization;
* changes to recovery semantics;
* changes to mutation failure semantics.

Any such change requires a separate architectural decision.

---

## 18. Required Invariants

The completed implementation must satisfy all of the following:

### A — One Domain per Register

A Register identity maps to one stable logical Operation Domain.

### B — Register Isolation

Different Registers have independent Operation Domains.

### C — Mutation Serialization

Register mutation executes inside its Register Operation Domain.

### D — Rebuild Serialization

Register rebuild executes inside the same Register Operation Domain.

### E — Recovery Serialization

Register recovery executes inside the same Register Operation Domain.

### F — No Competing Register Lock

The Totals Maintenance Coordinator does not define a second logical Register serialization boundary.

### G — Single Semantic State Owner

The Totals Maintenance Coordinator remains the sole owner of Totals maintenance semantic state.

### H — Register-Scoped Mutual Exclusion

Covered operations targeting the same Register cannot execute concurrently.

### I — Failure Semantics Preservation

WP-4 does not alter the approved maintenance failure and recovery semantics.

### J — Derived Totals

Totals remain derived from authoritative Movement Facts.

### K — Shared Registry Composition Boundary

All relevant consistency-sensitive operations obtain their Register Operation Domain through the same Registry composition boundary.

### L — Complete Mutation Boundary

All state-changing actions participating in one consistency-sensitive Register mutation execute within the same Register Operation Domain.

---

## 19. Verification Expectations

The implementation must provide evidence for the architectural guarantees through tests.

At minimum, tests must demonstrate:

1. repeated lookup of one Register returns the same logical domain;
2. different Registers receive isolated domains;
3. mutation and mutation are serialized for one Register;
4. mutation and rebuild are serialized for one Register;
5. mutation and recovery are serialized for one Register;
6. rebuild and recovery are serialized for one Register;
7. different Registers can proceed independently;
8. the Maintenance Coordinator does not retain a competing Register lock;
9. semantic maintenance state remains owned by the Maintenance Coordinator;
10. existing WP-3 failure semantics remain unchanged;
11. mutation state changes occur within the domain boundary.

Concurrency tests should verify observable serialization rather than depend on incidental thread timing where deterministic coordination primitives can express the condition directly.

---

## 20. Acceptance Condition

WP-4 is architecturally complete when:

* there is one logical Register-scoped serialization boundary;
* mutation, rebuild, and recovery use that boundary;
* different Registers remain isolated;
* the Maintenance Coordinator no longer owns a competing Register operation boundary;
* the Maintenance Coordinator remains the sole semantic state owner;
* the shared Registry is the structural composition boundary;
* existing maintenance, persistence, Totals, and failure semantics remain unchanged;
* the required concurrency and ownership invariants are covered by tests.

At that point, Step 7 has a single coherent operation domain for Register-scoped consistency-sensitive operations.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
