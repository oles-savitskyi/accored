# Phase 7 — Step 6.3

# Register Mutation / Totals Consistency Boundary — Architecture Definition

**Status:** Architecture Definition
**Phase:** 7 — Registers
**Step:** 6.3 — Register Mutation / Totals Consistency Boundary
**Depends on:** Phase 7 Steps 1–6.2, Phase 6 Posting Architecture
**Primary concern:** Register-scoped consistency between authoritative Movement Facts and derived Totals

---

## 1. Purpose

This document defines the architecture for the consistency boundary between:

* authoritative Movement Facts persisted for a Register; and
* derived Totals maintained from those Movement Facts.

The purpose of Step 6.3 is to define how Register mutations and Totals maintenance are coordinated so that concurrent mutation and rebuild operations cannot independently establish conflicting derived state.

This document defines architecture only.

It does not define the final concrete Python API, implementation classes, or test code.

---

## 2. Architectural Objective

The objective is to establish a single Register-scoped logical operation boundary through which all operations that can affect the consistency relationship between:

```text
Authoritative Movement Facts
            ↓
       Derived Totals
```

must execute.

The architecture must ensure that:

1. ordinary Movement mutation and corresponding Totals maintenance are serialized for the same Register;
2. full Totals rebuild is serialized against concurrent Register mutation;
3. rebuild reads a stable authoritative Movement Fact set for the duration of its logical operation;
4. Totals are never reported as `VALID` when current consistency has not been established;
5. different Registers remain independently operable;
6. persistence and Totals maintenance remain separate responsibilities;
7. no distributed transaction model is introduced;
8. Phase 6 Posting lifecycle semantics remain unchanged.

---

## 3. Problem Statement

Phase 7 currently contains two independently defined responsibilities:

```text
RegisterFactPersistence
        ↓
authoritative Movement Facts
```

and:

```text
TotalsMaintenanceCoordinator
        ↓
derived Totals
```

Both boundaries are individually valid.

The architectural problem appears when they participate in the same logical operation.

For example:

```text
T1: rebuild Register R
    enumerate Movement Facts

T2: persist Movement M for Register R
    apply M to Totals

T1: rebuild Totals from earlier Movement set
    publish rebuilt Totals
```

The final Totals may no longer represent the authoritative Movement Facts.

Therefore, serialization inside only the Totals maintenance component is insufficient.

The persistence boundary and the Totals boundary must participate in a shared Register-scoped operation boundary.

---

## 4. Architectural Principle

The central architectural principle is:

> All Register operations that can change the relationship between authoritative Movement Facts and derived Totals must execute within the same Register-scoped logical operation domain.

This domain is an orchestration boundary.

It is not itself a persistence mechanism, Totals store, transaction manager, or distributed coordination system.

---

## 5. Existing Architectural Boundaries

The existing architecture contains distinct responsibilities.

### 5.1 Movement persistence

`RegisterFactPersistence` owns persistence of authoritative Movement Facts.

It is responsible for:

* appending Movement Facts;
* finding Movement Facts by source document;
* removing Movement Facts;
* enumerating Movement Facts for a Register.

It does not own Totals.

---

### 5.2 Totals maintenance

`TotalsMaintenanceCoordinator` owns maintenance of derived Totals.

It is responsible for:

* applying Movement-derived contributions;
* removing Movement-derived contributions;
* rebuilding Totals;
* recovering derived state.

It does not own Movement persistence.

---

### 5.3 Posting

Phase 6 Posting owns:

* posting lifecycle;
* Posting Context;
* handler execution;
* Movement generation;
* Movement validation;
* posting result coordination;
* posting event semantics.

Posting does not own Totals calculation.

---

## 6. New Architectural Concept

Step 6.3 introduces the concept:

> **Register Operation Domain**

A Register Operation Domain represents the logical execution boundary for operations affecting the relationship between:

```text
Movement Facts
      ↕
Totals
```

Conceptually:

```text
PostingEngine
      ↓
PostingResultCoordinator
      ↓
Register Operation Domain
      ├── Movement Persistence
      └── Totals Maintenance
```

The same conceptual boundary is used for maintenance:

```text
Maintenance operation
      ↓
Register Operation Domain
      ├── Movement Persistence
      └── Totals Maintenance
```

The domain is Register-scoped.

---

## 7. Ownership

The Register Operation Domain is owned by the orchestration layer.

It is not owned by:

* `RegisterFactPersistence`;
* `TotalsMaintenanceCoordinator`;
* `PostingEngine`.

The orchestration layer is the correct owner because it is the only layer that legitimately coordinates the two independent responsibilities.

---

## 8. Why Persistence Must Not Own the Boundary

`RegisterFactPersistence` must remain responsible for authoritative Movement storage.

Making it responsible for Totals coordination would create an undesirable dependency:

```text
Persistence
    ↓
Totals
```

This would invert the existing architectural separation.

Persistence must not know:

* how Totals are calculated;
* how Totals are rebuilt;
* Totals lifecycle state;
* Totals consistency state;
* Posting lifecycle.

Therefore the Register Operation Domain must remain outside persistence.

---

## 9. Why Totals Maintenance Must Not Own the Entire Boundary

Similarly, `TotalsMaintenanceCoordinator` must not become responsible for Movement persistence.

That would create:

```text
Totals
   ↓
Persistence
```

and would cause derived state management to control authoritative state storage.

Totals maintenance must consume authoritative Movement Facts, but it must not become their owner.

---

## 10. Posting Integration Boundary

Phase 6 already defines `PostingResultCoordinator` as the integration boundary between Posting and persistent posting results.

Step 6.3 does not replace that boundary.

The intended relationship is:

```text
PostingEngine
      ↓
PostingResultCoordinator
      ↓
Register Mutation Orchestration
      ↓
Register Operation Domain
```

The Posting Engine remains responsible for Posting lifecycle.

The Register mutation boundary remains responsible for Register-level consistency.

---

## 11. Mutation Operation Semantics

A normal Register mutation consists conceptually of:

```text
acquire Register Operation Domain
        ↓
perform authoritative Movement mutation
        ↓
perform corresponding Totals mutation
        ↓
determine logical operation result
        ↓
release Register Operation Domain
```

For Movement establishment:

```text
Movement persistence
        ↓
Totals apply
```

For Movement removal:

```text
Movement persistence
        ↓
Totals remove
```

The exact concrete ordering and failure behavior are defined by the Contract and Concrete API Design.

---

## 12. Logical Completion

A Register mutation is logically complete only when both participating responsibilities have reached their required successful state.

Successful completion means:

1. authoritative Movement state has been established;
2. corresponding Totals state has been successfully maintained;
3. the resulting consistency state is known;
4. the operation has reached its defined completion boundary.

The operation domain must not be released before the logical result is determined.

---

## 13. Failure During Mutation

The architecture explicitly recognizes that Movement persistence and Totals maintenance are not a single atomic storage operation.

Therefore partial failure is possible.

For example:

```text
Movement persistence
        ↓
SUCCESS

Totals maintenance
        ↓
FAILURE
```

In this situation:

```text
Movement Facts = authoritative
Totals = not known to be current
```

The system must not report:

```text
ACTIVE + VALID
```

Instead, the Register must enter the appropriate recovery-required or indeterminate state according to the Step 6.2 lifecycle contract.

---

## 14. Unexpected Failure

Unexpected exceptions must not be interpreted as successful completion.

If the final state of the logical operation cannot be established, the resulting consistency state must not be reported as `VALID`.

The architecture therefore follows:

```text
unknown outcome
      ↓
INDTERMINATE
      ↓
recovery
```

rather than attempting speculative reconciliation.

---

## 15. Rebuild Semantics

A full rebuild reconstructs derived Totals from authoritative Movement Facts.

Conceptually:

```text
Register Operation Domain
        ↓
enumerate authoritative Movement Facts
        ↓
rebuild Totals
        ↓
reconstruct required runtime maintenance state
        ↓
publish resulting state
```

Rebuild is therefore a Register-scoped logical operation.

---

## 16. Rebuild Input Boundary

The authoritative input for rebuild is:

```text
RegisterFactPersistence.enumerate(register_identity)
```

The Movement Fact set returned by persistence is the authoritative input.

The rebuild operation must not combine:

* partially rebuilt Totals;
* stale `_applied` state;
* arbitrary incremental assumptions;
* independently changing Movement state.

The rebuild result must be based on the authoritative Movement Facts observed inside the rebuild operation boundary.

---

## 17. No Concurrent-Rebuild Merge Protocol

The architecture does not introduce a protocol for:

```text
rebuild
   +
concurrent mutations
   +
post-rebuild reconciliation
```

Such a protocol would introduce additional distributed-style consistency complexity.

Instead, the Register Operation Domain serializes the operations.

Therefore:

```text
mutation(R)
```

and:

```text
rebuild(R)
```

cannot concurrently establish competing Register state.

---

## 18. Rebuild Publication Boundary

The critical rebuild sequence is:

```text
acquire domain(R)
        ↓
enumerate authoritative Movement Facts
        ↓
rebuild Totals
        ↓
reconstruct runtime maintenance state
        ↓
publish resulting lifecycle/consistency state
        ↓
release domain(R)
```

The operation domain remains active for the entire logical rebuild.

The domain must not be released immediately after enumeration.

Doing so would recreate the original race.

---

## 19. Recovery Semantics

Recovery uses the authoritative Movement Facts to re-establish derived state.

Conceptually:

```text
recover(R)
    ↓
rebuild(R)
    ↓
ACTIVE + VALID
```

Recovery is therefore not a second source of truth.

It is a controlled re-establishment of derived state from authoritative state.

---

## 20. Bootstrap Semantics

A newly created coordinator instance does not automatically know the current state of an existing Register.

Therefore:

```text
CREATED + INDETERMINATE
```

means:

> The coordinator exists, but current consistency with authoritative Movement Facts has not yet been established.

For an existing Register, incremental maintenance must not be treated as a substitute for bootstrap.

The required sequence is:

```text
existing Register
        ↓
rebuild
        ↓
ACTIVE + VALID
        ↓
incremental maintenance
```

---

## 21. Bootstrap Invariant

The following invariant is mandatory:

> A coordinator must establish derived state from authoritative Movement Facts before performing incremental maintenance against a Register whose existing state was not established by that coordinator.

This invariant avoids interpreting the runtime `_applied` state as durable idempotency information.

---

## 22. CREATED State

`CREATED` is a legitimate initial lifecycle state.

It does not mean:

> The Register contains no Movement Facts.

It means:

> The maintenance runtime has not yet established current derived-state consistency for the Register.

Therefore:

```text
CREATED + INDETERMINATE
```

is distinct from:

```text
RECOVERY_REQUIRED
```

The former is initialization state.

The latter represents an operational consistency problem requiring recovery.

---

## 23. Runtime Idempotency State

Step 6.2 may maintain runtime state representing already-applied Movement contributions.

This state is not authoritative persistence.

It is not:

* a durable idempotency store;
* an application journal;
* a source of truth;
* a recovery record.

Rebuild reconstructs the required runtime state from authoritative Movement Facts.

---

## 24. Register-Scoped Serialization

Serialization is scoped to an individual Register.

Conceptually:

```text
Domain(R1)
Domain(R2)
Domain(R3)
```

Operations on `R1` must not unnecessarily block operations on `R2`.

Therefore a single global process-wide lock is not the intended architecture.

---

## 25. Concurrency Invariant

For any Register `R`:

> At most one logical Register mutation/rebuild/recovery operation may establish or modify the relationship between authoritative Movement Facts and derived Totals at a time.

This includes:

* Movement establishment;
* Movement removal;
* Totals rebuild;
* Totals recovery.

---

## 26. Mutation Ordering

The exact persistence and Totals mutation sequence must preserve the following architectural rule:

> A successful operation must never publish `ACTIVE + VALID` until both authoritative Movement state and corresponding derived Totals state satisfy their required postconditions.

Failure before authoritative mutation must not cause a corresponding derived mutation.

Failure after authoritative mutation must result in recovery-required or indeterminate semantics rather than false validity.

---

## 27. Cross-Register Operations

A logical operation may potentially affect more than one Register.

Step 6.3 does not introduce distributed transaction semantics for such operations.

Each Register remains independently scoped.

When multiple Register Operation Domains are required, they must be acquired in a deterministic global order.

---

## 28. Multi-Register Ordering Invariant

The following invariant is mandatory:

> When one logical operation requires multiple Register Operation Domains, the domains must be acquired in a deterministic global order.

This prevents lock-order inversion such as:

```text
Operation A:
    acquire A
    acquire B

Operation B:
    acquire B
    acquire A
```

The architecture does not require or imply distributed atomicity across those Registers.

---

## 29. Persistence Failure

If Movement persistence fails before the authoritative mutation is established, the corresponding Totals mutation must not be performed.

Conceptually:

```text
persist Movement
      ↓
FAILURE
      ↓
do not apply Totals
```

The operation reports failure according to the persistence and maintenance contracts.

---

## 30. Persistence Indeterminate Failure

If Movement persistence reports an indeterminate result, the system must not assume whether the authoritative Movement mutation occurred.

For example:

```text
append()
   ↓
PersistenceIndeterminateError
```

The system cannot safely infer:

```text
Movement exists
```

or:

```text
Movement does not exist
```

Therefore corresponding incremental Totals mutation must not be based on an unverified assumption.

The Register must enter an appropriate indeterminate/recovery state.

Recovery uses authoritative persistence.

---

## 31. Totals Failure After Successful Persistence

If Movement persistence succeeds but Totals maintenance fails:

```text
authoritative Movement
        ↓
SUCCESS

Totals maintenance
        ↓
FAILURE
```

the Movement Fact remains authoritative.

The Register must not be reported as:

```text
ACTIVE + VALID
```

Recovery must reconstruct Totals from authoritative Movement Facts.

---

## 32. Failure During Rebuild

If rebuild cannot establish a valid derived state:

```text
enumerate
    ↓
rebuild
    ↓
FAILURE
```

the resulting state must not be reported as valid.

The existing derived state must not be falsely represented as current merely because rebuild was attempted.

Recovery remains available through another rebuild attempt.

---

## 33. No False `VALID` State

The following invariant is fundamental:

> `ACTIVE + VALID` means that current consistency between authoritative Movement Facts and derived Totals has actually been established.

It must not mean:

* the operation was attempted;
* the operation probably succeeded;
* the persistence operation succeeded;
* the Totals operation succeeded independently;
* no exception was observed.

Validity must be earned by successful logical completion.

---

## 34. Event Semantics

Step 6.3 does not introduce new Register consistency events.

Phase 6 event semantics remain unchanged.

In particular:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

are emitted only after the relevant Posting operation has successfully completed according to the Phase 6 contract.

Failed or indeterminate Register maintenance must not be represented as successful Posting lifecycle completion.

---

## 35. Recovery Events

Step 6.3 does not require a new event model for recovery.

Recovery is an internal consistency operation.

If a future phase introduces explicit operational recovery events, that must be a separate architectural decision.

---

## 36. Query Semantics

Step 6.3 does not introduce a new balance or Totals query API.

Existing query semantics remain governed by the Register and Totals architecture.

The operation domain exists to protect mutation/rebuild consistency, not to become a query abstraction.

---

## 37. Storage Independence

The Register Operation Domain must remain independent of the storage provider implementation.

The same logical model must work with:

* in-memory persistence;
* filesystem persistence;
* future storage providers.

The domain must not depend on:

* filesystem locks;
* database-specific locks;
* provider-specific transaction APIs.

---

## 38. In-Memory Implementation

The initial implementation is process-local.

A practical implementation may use an in-memory mapping:

```text
Register Identity
        ↓
operation synchronization state
```

The exact synchronization primitive is an implementation detail.

The architecture does not prescribe a specific Python lock type.

---

## 39. Process Boundary

The Register Operation Domain is process-local.

It does not coordinate:

* separate Python processes;
* separate application instances;
* separate hosts;
* distributed workers.

Therefore the architecture explicitly does not claim cross-process serialization.

---

## 40. Transaction Boundary

The operation domain is not a database transaction.

It does not provide:

```text
atomic commit
```

across:

```text
Movement persistence
+
Totals maintenance
```

It provides:

```text
logical serialization
+
controlled failure semantics
+
recovery path
```

This distinction is mandatory.

---

## 41. Atomicity Model

The architecture intentionally uses logical atomicity rather than storage-level atomicity.

A successful logical operation produces:

```text
authoritative state
        +
derived state
```

that satisfy the defined consistency invariant.

A failed operation may leave authoritative state changed while derived state requires recovery.

The architecture handles this through explicit lifecycle/consistency states and rebuild-based recovery.

---

## 42. Determinism

For a fixed authoritative Movement Fact set and fixed relevant configuration:

```text
rebuild(R)
```

must deterministically establish the same semantic Totals state.

The operation domain itself must not introduce nondeterminism into Totals calculation.

---

## 43. Relationship to Step 6.2

Step 6.3 builds on the Step 6.2 maintenance model.

Step 6.2 owns:

* maintenance lifecycle;
* consistency lifecycle;
* apply;
* remove;
* rebuild;
* recover;
* maintenance outcomes.

Step 6.3 owns:

* Register-scoped orchestration;
* serialization across persistence and maintenance;
* stable rebuild boundary;
* mutation/rebuild coordination.

Step 6.3 does not redefine Step 6.2 semantics.

---

## 44. Relationship to Phase 6

Phase 6 Posting remains responsible for:

* Posting Context;
* Posting lifecycle;
* handler execution;
* Movement generation;
* Posting validation;
* Posting result coordination;
* Posting events.

Step 6.3 provides the Register-side mutation boundary consumed by Posting integration.

There is no redesign of Posting lifecycle in Step 6.3.

---

## 45. Relationship to Persistence

The persistence layer remains authoritative for Movement Facts.

The Register Operation Domain coordinates persistence participation but does not replace it.

The architecture therefore remains:

```text
Operation Domain
      │
      ├── Persistence
      │
      └── Totals Maintenance
```

rather than:

```text
Persistence
      └── Totals
```

or:

```text
Totals
      └── Persistence
```

---

## 46. Relationship to Totals Engine

The Totals engine remains responsible for Totals calculation.

The operation domain does not calculate Totals.

It only ensures that the relevant Totals operation executes within the correct Register-scoped logical boundary.

---

## 47. Forbidden Designs

The following designs are explicitly outside Step 6.3:

### 47.1 Distributed transactions

No distributed transaction protocol is introduced.

### 47.2 Persistent idempotency store

No new durable application journal or applied-Movement store is introduced.

### 47.3 Event-driven Totals synchronization

No asynchronous event-driven Movement → Totals synchronization is introduced.

### 47.4 Persistence-owned Totals

Persistence does not own Totals.

### 47.5 Totals-owned persistence

Totals maintenance does not own authoritative Movement persistence.

### 47.6 Global process lock

A single global lock for all Registers is not the intended design.

### 47.7 Concurrent rebuild merge protocol

No concurrent mutation merge/reconciliation protocol is introduced.

### 47.8 New generic transaction framework

Step 6.3 does not introduce a generic Unit of Work or transaction framework.

### 47.9 New Totals persistence layer

No separate Totals persistence architecture is introduced.

### 47.10 Posting lifecycle redesign

Phase 6 Posting semantics are not redesigned.

---

## 48. Synchronous Requirement

Register mutation and Totals maintenance remain synchronous.

The logical operation must complete before its result is reported to the caller.

Step 6.3 does not introduce:

* background maintenance;
* asynchronous reconciliation;
* eventual Totals synchronization.

---

## 49. Register State Machine Integration

The Register Operation Domain integrates with the Step 6.2 lifecycle model.

Conceptually:

```text
CREATED + INDETERMINATE
        │
        │ rebuild
        ▼
MAINTENANCE + INDETERMINATE
        │
        │ successful completion
        ▼
ACTIVE + VALID
```

Failure paths may lead to:

```text
RECOVERY_REQUIRED
```

or:

```text
INDETERMINATE
```

depending on the known outcome.

The operation domain does not replace the lifecycle state machine.

---

## 50. Operation Result Semantics

The result of a Register operation must distinguish at least:

```text
success
failure
indeterminate
```

The exact public result representation belongs to the Contract/API design.

The architecture requires that:

> An unknown outcome must never be silently represented as success.

---

## 51. Recovery as Normal Resolution

Recovery is not an exceptional architectural afterthought.

Because authoritative Movement persistence and derived Totals are separate responsibilities, explicit recovery is a normal part of the architecture.

The standard recovery path is:

```text
detect failure/inconsistency
        ↓
rebuild from authoritative Movement Facts
        ↓
re-establish derived state
```

---

## 52. Observability

The architecture should permit identification of:

* Register identity;
* operation type;
* success/failure/indeterminate outcome;
* lifecycle state;
* consistency state;
* recovery requirement.

Observability must not introduce a new authoritative state store.

---

## 53. Testing Architecture

The implementation must test at least:

### Register isolation

Operations on different Registers may proceed independently.

### Same-Register serialization

Concurrent operations for the same Register cannot establish conflicting state.

### Rebuild serialization

Rebuild cannot race with Register mutation within the same domain.

### Stable rebuild input

Movement enumeration and Totals publication belong to one protected logical operation.

### Failure propagation

Persistence failure does not produce false Totals success.

### Indeterminate persistence

Indeterminate persistence does not produce false validity.

### Totals failure

Successful authoritative persistence followed by Totals failure requires recovery.

### Recovery

Recovery rebuilds from authoritative Movement Facts.

### Bootstrap

Incremental maintenance is not treated as proof of consistency for an uninitialized existing Register.

### Multi-register ordering

Multiple Register domains are acquired deterministically.

---

## 54. Acceptance Criteria

Step 6.3 Architecture is complete when all of the following are true:

1. A Register-scoped logical operation boundary is explicitly defined.
2. The operation boundary is owned by orchestration.
3. Movement persistence remains authoritative for Movement Facts.
4. Totals maintenance remains responsible for derived Totals.
5. Both participate in the same Register operation domain.
6. Same-Register mutations are serialized.
7. Rebuild is serialized against same-Register mutation.
8. Rebuild input is authoritative Movement persistence.
9. Rebuild publication occurs inside the same logical operation boundary.
10. `ACTIVE + VALID` cannot be claimed without established consistency.
11. Persistence failure is explicitly represented.
12. Persistence indeterminate outcomes are explicitly represented.
13. Totals failure after successful persistence leads to recovery semantics.
14. Recovery is rebuild-based.
15. Coordinator bootstrap semantics are explicit.
16. `_applied` remains runtime state rather than durable truth.
17. Different Registers can operate independently.
18. Multi-register acquisition order is deterministic.
19. No distributed transaction is introduced.
20. No persistent idempotency store is introduced.
21. No event-driven Totals synchronization is introduced.
22. No new Totals persistence layer is introduced.
23. Phase 6 Posting lifecycle semantics remain unchanged.
24. The architecture remains storage-provider independent.
25. The operation domain remains synchronous and process-local.

---

## 55. Non-Goals

Step 6.3 does not define:

* historical balance queries;
* period closing;
* valuation;
* General Ledger integration;
* accounting reports;
* distributed locking;
* cross-process coordination;
* distributed transactions;
* durable operation journals;
* asynchronous maintenance;
* event-sourced Totals;
* a new Totals persistence model;
* a generic application transaction framework;
* new Posting lifecycle semantics.

---

## 56. Architectural Dependency Graph

The intended dependency direction is:

```text
Phase 6 Posting
       │
       ▼
Posting Result Coordination
       │
       ▼
Register Mutation Orchestration
       │
       ▼
Register Operation Domain
      / \
     /   \
    ▼     ▼
Movement  Totals
Persistence Maintenance
```

The reverse dependencies are forbidden:

```text
Persistence → Totals
Totals → Persistence
```

---

## 57. Responsibility Matrix

| Responsibility                  | Owner                                    |
| ------------------------------- | ---------------------------------------- |
| Posting lifecycle               | PostingEngine                            |
| Movement generation             | Posting Handler                          |
| Movement validation             | Posting infrastructure                   |
| Posting result coordination     | PostingResultCoordinator                 |
| Authoritative Movement storage  | RegisterFactPersistence                  |
| Totals calculation              | Totals engine                            |
| Totals maintenance lifecycle    | TotalsMaintenanceCoordinator             |
| Register mutation serialization | Register Operation Domain                |
| Rebuild/mutation coordination   | Register Operation Domain                |
| Recovery orchestration          | Register maintenance/orchestration layer |
| Durable source of truth         | Movement persistence                     |
| Process-local synchronization   | Register Operation Domain                |

---

## 58. Proposed Internal Architecture

The conceptual internal architecture is:

```text
                 PostingEngine
                      │
                      ▼
          PostingResultCoordinator
                      │
                      ▼
          Register Mutation Boundary
                      │
                      ▼
           Register Operation Domain
                 /           \
                /             \
               ▼               ▼
    RegisterFactPersistence   TotalsMaintenanceCoordinator
               │               │
               ▼               ▼
       Movement Facts         Derived Totals
```

The same operation domain is used by rebuild and recovery.

---

## 59. Dependency Injection Requirement

The runtime composition root must ensure that all components participating in a Register's mutation/maintenance lifecycle share the same Register Operation Domain.

For a given Register:

```text
Posting integration
        │
        ├── Domain(R)
        │
Maintenance
        │
        └── Domain(R)
```

They must not independently construct unrelated domains.

---

## 60. Runtime Ownership

The runtime composition layer owns the lifetime of Register Operation Domains.

A domain is runtime infrastructure.

It is not persisted as business data.

It must not become part of:

* Movement serialization;
* Register Fact persistence;
* Totals persistence;
* domain entity state.

---

## 61. Lifecycle of Operation Domain

The operation domain itself does not represent business lifecycle.

It represents availability of a Register-scoped logical execution boundary.

Therefore:

```text
Domain exists
```

does not imply:

```text
Totals are valid
```

and:

```text
Domain acquired
```

does not imply:

```text
operation succeeded
```

The domain and Register maintenance lifecycle remain separate concepts.

---

## 62. Important Invariant: One Register, One Domain

For a given process and Register identity:

> There must be one shared Register Operation Domain participating in the Register mutation/maintenance boundary.

Equivalent implementations must preserve this semantic invariant even if the internal representation changes.

---

## 63. Important Invariant: Domain Identity Is Not Movement Identity

A Register Operation Domain is scoped by:

```text
Register Identity
```

not:

```text
Movement Identity
```

Its purpose is to serialize operations affecting the Register as a whole.

---

## 64. Important Invariant: Domain Identity Is Not Storage Identity

The domain is not keyed by:

* filesystem path;
* persistence provider instance;
* database connection;
* storage record identity.

It is logically scoped to the Register identity.

This preserves storage-provider independence.

---

## 65. Architecture Review Questions

Before implementation, the following questions must be answered by the Contract/API design:

1. What is the minimal public/internal interface of the Register Operation Domain?
2. How is a domain obtained for a Register?
3. How is the shared domain injected into Posting integration?
4. How is the same domain shared with maintenance operations?
5. What exact operation body executes inside the domain?
6. How are multiple domains acquired deterministically?
7. How are failures represented at the orchestration boundary?
8. How does recovery interact with the domain?
9. What guarantees are process-local versus persistence-level?
10. Which APIs remain public and which remain internal?

These questions are deliberately deferred to the Contract and Concrete API Design.

---

## 66. Implementation Constraint

The implementation must preserve the following distinction:

```text
Logical Operation Domain
        ≠
Synchronization Primitive
```

The domain is an architectural boundary.

A lock, `RLock`, monitor, or equivalent mechanism is only an implementation mechanism for realizing its process-local serialization requirement.

The implementation must not expose the synchronization primitive as the architectural API.

---

## 67. Recommended Implementation Shape

The recommended implementation shape is intentionally minimal:

```text
Register Operation Domain
        │
        ├── Register identity
        ├── operation serialization
        └── logical operation execution
```

The domain should coordinate existing components rather than duplicate their responsibilities.

Conceptually:

```text
domain.execute(R, operation)
```

or an equivalent minimal API may be considered during Concrete API Design.

No specific Python API is mandated by this Architecture Definition.

---

## 68. Compatibility Requirements

Step 6.3 must preserve compatibility with:

* existing `RegisterFactPersistence`;
* existing `Movement`;
* existing Totals APIs;
* existing Step 6.2 lifecycle semantics;
* Phase 6 Posting APIs;
* existing storage-provider boundaries;
* existing public package boundaries unless a minimal export is explicitly justified.

The implementation must avoid unnecessary changes to completed Phase 5 and Phase 6 architecture.

---

## 69. Migration Strategy

The implementation should be incremental.

### Stage 1

Introduce the Register Operation Domain abstraction.

### Stage 2

Integrate Totals maintenance operations with the domain.

### Stage 3

Integrate Movement persistence + Totals maintenance orchestration.

### Stage 4

Integrate Posting result coordination.

### Stage 5

Add concurrency and failure tests.

Existing Step 6.2 behavior should remain intact until the new orchestration boundary is established.

---

## 70. Architectural Completion Definition

Step 6.3 Architecture Definition is complete when the system has an unambiguous answer to the following question:

> How can a Register mutation and a Totals rebuild execute concurrently without allowing the rebuild to publish a state that excludes an authoritative Movement mutation participating in the same Register?

The answer is:

> They cannot concurrently establish conflicting state because both operations execute through the same Register-scoped logical operation domain, which serializes their critical sections.

This is the core architectural result of Step 6.3.

---

## 71. Summary

Step 6.3 introduces a narrow orchestration boundary between authoritative Movement Facts and derived Totals.

The essential architecture is:

```text
                   PostingEngine
                        │
                        ▼
             PostingResultCoordinator
                        │
                        ▼
             Register Operation Domain
                  /             \
                 /               \
                ▼                 ▼
      Movement Persistence   Totals Maintenance
           authoritative          derived
              facts                state
```

The essential invariants are:

1. authoritative Movement Facts remain the source of truth;
2. Totals remain derived state;
3. both participate in the same Register-scoped logical operation boundary;
4. same-Register mutation and rebuild are serialized;
5. rebuild reads authoritative Movement Facts within that boundary;
6. rebuild publication occurs before the boundary is released;
7. `ACTIVE + VALID` requires established consistency;
8. bootstrap is required before incremental maintenance for an existing uninitialized Register;
9. multi-register operations acquire domains deterministically;
10. the domain is process-local and storage-independent;
11. the domain is not a transaction manager;
12. no distributed transaction or persistent idempotency mechanism is introduced;
13. Phase 6 Posting lifecycle remains unchanged;
14. recovery is rebuild from authoritative Movement Facts.

The architectural responsibility is therefore deliberately narrow:

> **Register Operation Domain coordinates the logical consistency boundary; Movement persistence owns authoritative facts; Totals maintenance owns derived state; Posting remains responsible for Posting lifecycle.**
