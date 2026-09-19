# Phase 7 — Step 6.3

# Register Mutation / Totals Consistency Boundary Contract

**Document:** `PHASE_7_STEP_6.3_REGISTER_MUTATION_TOTALS_CONSISTENCY_BOUNDARY_CONTRACT.md`
**Phase:** 7 — Registers
**Step:** 6.3 — Register Mutation / Totals Consistency Boundary
**Status:** Final Contract
**Depends on:**

* `PHASE_7_STEP_6_LIFECYCLE_MAINTENANCE_ARCHITECTURE_DEFINITION.md`
* `PHASE_7_STEP_6_LIFECYCLE_MAINTENANCE_CONTRACT.md`
* `PHASE_7_STEP_6_CONCRETE_API_DESIGN.md`
* `PHASE_7_STEP_6.3_REGISTER_MUTATION_TOTALS_CONSISTENCY_BOUNDARY_ARCHITECTURE_DEFINITION.md`
* Phase 6 Posting Architecture and Contracts
* Phase 5 Persistence Architecture and Contracts

---

## 1. Purpose

This document defines the normative contract for the consistency boundary between:

1. authoritative Register Movement Facts; and
2. derived Register Totals.

The contract establishes how Register mutations, Totals maintenance, rebuild, and recovery interact.

The objective is to ensure that:

* authoritative Movement Facts remain the source of truth;
* Totals remain derived state;
* Register mutations and Totals maintenance cannot independently establish contradictory Register state within the same Register operation boundary;
* rebuild cannot race with Register mutation;
* failures are explicitly represented;
* recovery remains possible;
* different Registers remain independently operable;
* the boundary does not introduce a new persistence model or distributed transaction mechanism.

This contract defines semantics and invariants.

Concrete Python APIs and synchronization primitives are specified separately by:

`PHASE_7_STEP_6.3_REGISTER_MUTATION_TOTALS_CONSISTENCY_BOUNDARY_CONCRETE_API_DESIGN.md`

---

## 2. Status

This document is the **final normative Contract** for Step 6.3.

Implementation MUST conform to this document.

Concrete implementation details MAY vary provided that all normative requirements remain satisfied.

---

## 3. Scope

This contract covers:

* Register-scoped mutation coordination;
* Movement establishment;
* Movement removal;
* Totals application;
* Totals removal;
* Totals rebuild;
* recovery;
* authoritative Movement enumeration;
* consistency state transitions;
* operation outcomes;
* partial failure;
* indeterminate failure;
* bootstrap requirements;
* runtime maintenance state;
* multi-register acquisition ordering;
* integration with Posting;
* concurrency boundaries;
* process-local synchronization.

---

## 4. Non-Goals

This contract does not define:

* database transaction semantics;
* distributed transactions;
* distributed locks;
* durable idempotency records;
* event-driven eventual synchronization;
* a new persistence abstraction;
* a Totals persistence model;
* Posting lifecycle redesign;
* Posting Handler responsibilities;
* accounting semantics of Movement Facts;
* Register calculation algorithms;
* a public lock API.

---

## 5. Core Contract

For a given Register:

> All operations that can affect consistency between authoritative Movement Facts and derived Totals MUST execute within the same Register-scoped logical operation domain.

This is the fundamental consistency boundary of Step 6.3.

The boundary applies to:

* Movement establishment;
* Movement removal;
* Totals maintenance;
* rebuild;
* recovery.

---

## 6. Authoritative State

Movement Facts persisted through `RegisterFactPersistence` are authoritative Register state.

The authoritative state consists of the Movement Facts associated with a Register.

Totals MUST NOT become an independent source of truth.

Totals MUST be reconstructible from authoritative Movement Facts.

---

## 7. Derived State

Totals are derived state.

Totals MUST represent the aggregation defined by the Register's Totals semantics over the authoritative Movement Facts.

A Totals state that cannot be established as corresponding to authoritative Movement Facts MUST NOT be reported as:

`ACTIVE + VALID`.

---

## 8. Register Operation Domain

A **Register Operation Domain** is the logical orchestration boundary within which operations affecting one Register's Movement/Totals consistency are serialized.

The domain:

* belongs to exactly one Register;
* coordinates the logical operation boundary;
* does not own authoritative persistence;
* does not own Totals semantics;
* does not replace `RegisterFactPersistence`;
* does not replace `TotalsMaintenanceCoordinator`;
* does not constitute a database transaction;
* does not provide distributed coordination.

The concrete synchronization mechanism is an implementation detail.

---

## 9. Shared-Domain Invariant

For a given Register:

> All operations that can affect consistency between authoritative Movement Facts and derived Totals MUST use the same Register Operation Domain instance or equivalent shared logical domain identity.

Independent locks owned separately by Movement persistence and Totals maintenance are insufficient to satisfy this contract.

---

## 10. Ownership

The Register Operation Domain is owned by the orchestration layer.

Ownership MUST NOT be assigned to:

* `RegisterFactPersistence`;
* `TotalsMaintenanceCoordinator`;
* `PostingEngine`.

The orchestration layer is responsible for composing:

* authoritative Movement persistence;
* Totals maintenance;
* Register-scoped operation coordination.

---

## 11. Logical Boundary

The operation domain is a logical consistency boundary.

It is not required to correspond to:

* a database transaction;
* a filesystem transaction;
* a storage-provider primitive;
* a thread lock;
* an operating-system synchronization primitive.

The implementation MAY use a process-local lock or equivalent synchronization mechanism.

However:

> Logical Operation Domain ≠ Synchronization Primitive.

---

## 12. Same-Register Serialization

Operations affecting the same Register MUST NOT execute concurrently in a way that allows them to observe or publish contradictory Movement/Totals state.

At minimum, the following operations MUST be serialized per Register:

* establish Movement + corresponding Totals maintenance;
* remove Movement + corresponding Totals maintenance;
* rebuild;
* recover.

---

## 13. Different-Register Isolation

Operations on different Registers SHOULD be independently executable.

A Register operation MUST NOT require a global process-wide lock merely to establish consistency for that Register.

The implementation SHOULD therefore permit concurrency between independent Registers.

---

## 14. Mutation Critical Section

The logical operation boundary for a Register mutation MUST encompass the full logical mutation sequence.

The boundary MUST NOT cover only the Totals update.

For example, a successful Movement establishment logically includes:

1. authoritative Movement establishment;
2. corresponding Totals maintenance;
3. successful completion reporting.

Likewise, Movement removal logically includes:

1. authoritative Movement removal;
2. corresponding Totals maintenance;
3. successful completion reporting.

The operation domain serializes execution.

It does **not** make authoritative persistence and derived Totals mutation storage-atomic.

> Serialization MUST NOT be interpreted as atomic commit.

---

## 15. Movement Establishment

A successful Movement establishment operation MUST establish:

* the authoritative Movement Fact; and
* the corresponding Totals contribution.

Logical success MUST NOT be reported unless the respective success postconditions have been satisfied.

If the authoritative Movement is successfully established but Totals maintenance fails, the operation MUST NOT report successful completion.

The resulting Register state MUST require recovery or otherwise remain explicitly non-valid.

---

## 16. Movement Removal

A successful Movement removal operation MUST remove:

* the authoritative Movement Fact; and
* the corresponding Totals contribution.

Logical success MUST NOT be reported unless the respective success postconditions have been satisfied.

If authoritative removal succeeds but Totals removal fails, the operation MUST NOT report successful completion.

The resulting Register state MUST require recovery or otherwise remain explicitly non-valid.

---

## 17. Persistence Failure Before Mutation

If authoritative persistence fails before the corresponding Movement mutation occurs:

* the corresponding Totals mutation MUST NOT be applied as though the Movement had been established or removed;
* the operation MUST report failure according to the failure taxonomy;
* the Register MUST remain in a state consistent with the authoritative state.

---

## 18. Persistence Indeterminate Failure

If authoritative persistence produces an indeterminate result, the system cannot establish whether the authoritative Movement mutation occurred.

In this case:

* the operation MUST NOT claim successful consistency;
* Totals MUST NOT be assumed to correspond to the intended mutation;
* the Register MUST NOT be reported as `ACTIVE + VALID` solely because the operation returned;
* recovery MUST remain possible.

The resulting state SHOULD be represented as `INDETERMINATE` or `RECOVERY_REQUIRED` according to the applicable lifecycle semantics.

---

## 19. Totals Failure

If authoritative Movement mutation succeeds but corresponding Totals maintenance fails:

* authoritative Movement state remains authoritative;
* Totals MUST NOT be considered valid;
* the operation MUST NOT report successful completion;
* the Register MUST enter or remain in a recovery-required/non-valid state.

The authoritative Movement Facts MUST NOT be silently altered merely to conceal a Totals failure.

---

## 20. Mutation Failure Ordering

The implementation MAY choose an internal failure-handling strategy, provided that:

* authoritative Movement Facts remain authoritative;
* Totals are never falsely reported as valid;
* successful operations satisfy both authoritative and derived postconditions;
* failures remain observable;
* recovery remains possible.

No storage-level atomicity assumption may be introduced by this contract.

---

## 21. Rebuild

A rebuild reconstructs derived Totals from authoritative Movement Facts.

Conceptually:

```text
Register Operation Domain
        ↓
authoritative Movement enumeration
        ↓
Totals reconstruction
        ↓
runtime maintenance-state reconstruction
        ↓
publication of established derived state
```

Rebuild MUST execute within the Register Operation Domain.

---

## 22. Rebuild Input

The input to rebuild MUST come from authoritative Movement Facts.

The rebuild MUST NOT use the current Totals state as authoritative input.

The rebuild MAY use runtime maintenance state only as implementation state, never as the authoritative source of Register facts.

---

## 23. Stable Rebuild Boundary

A rebuild MUST establish a stable logical boundary with respect to Register mutations.

A competing Register mutation MUST NOT be allowed to modify the authoritative Movement set while the rebuild is consuming that set and publishing the corresponding Totals state.

Therefore:

> Rebuild MUST acquire the same Register Operation Domain used by ordinary Register mutation before authoritative enumeration and MUST retain that domain through Totals publication.

---

## 24. Rebuild Validity

After successful rebuild:

`ACTIVE + VALID`

MUST mean that the published Totals correspond to the authoritative Movement Facts consumed by that rebuild operation, and that no competing Register mutation was allowed to establish state within the same Register operation boundary during the rebuild.

This requirement derives from Register-scoped serialization.

It does not imply a generic storage snapshot guarantee beyond the operation boundary.

---

## 25. Rebuild Determinism

For a fixed authoritative Movement set and fixed Register Totals semantics:

> Rebuild MUST produce the same semantic Totals result.

Rebuild MUST NOT depend on:

* arbitrary iteration order;
* storage-provider layout;
* runtime object identity;
* uncontrolled system time;
* unrelated external state.

---

## 26. Rebuild Failure

If rebuild fails before publication of a valid reconstructed state:

* the previous Totals state MUST NOT be falsely marked valid;
* the failure MUST be observable;
* the Register MUST remain explicitly non-valid or recovery-required;
* recovery MUST remain possible.

An implementation MUST NOT report `ACTIVE + VALID` after an unsuccessful rebuild.

---

## 27. Recovery

Recovery MUST be able to re-establish Totals from authoritative Movement Facts.

Recovery SHOULD use the same logical boundary as rebuild.

Conceptually:

```text
recover()
    ↓
rebuild()
```

The exact implementation MAY differ provided the semantic result is equivalent.

---

## 28. Recovery Authority

Recovery MUST derive its result from authoritative Movement Facts.

Recovery MUST NOT rely on potentially corrupted or stale Totals state as authoritative input.

---

## 29. Recovery Success

Successful recovery MUST establish:

* Totals corresponding to authoritative Movement Facts consumed by recovery;
* reconstructed runtime maintenance state;
* a valid lifecycle state.

Successful recovery MAY transition the Register to:

`ACTIVE + VALID`.

---

## 30. Recovery Failure

Failed recovery MUST NOT produce:

`ACTIVE + VALID`.

The Register MUST remain explicitly non-valid or recovery-required.

---

## 31. Bootstrap Invariant

A coordinator instance MUST establish derived state from authoritative Movement Facts before performing incremental maintenance against a pre-existing Register whose existing state was not established by that coordinator.

Therefore:

> Rebuild MUST precede incremental maintenance when a coordinator instance encounters pre-existing Register state that it has not established itself.

This is a runtime lifecycle invariant.

---

## 32. CREATED State

`CREATED + INDETERMINATE` represents a recognized Register for which the coordinator has not yet established current derived-state consistency.

This state is distinct from:

`RECOVERY_REQUIRED`.

`CREATED + INDETERMINATE` means:

* the coordinator exists;
* current consistency has not yet been established.

It does not by itself imply that corruption or failure has occurred.

---

## 33. ACTIVE + VALID

`ACTIVE + VALID` MUST be reported only when:

* authoritative Movement Facts have been established as the relevant input;
* corresponding Totals state has been successfully derived;
* no competing Register operation invalidated that relationship within the same operation boundary.

---

## 34. Maintenance Runtime State

Runtime maintenance state MAY track information needed for efficient incremental maintenance.

Such state MUST NOT become authoritative Register state.

---

## 35. `_applied` Semantics

The Step 6.2 `_applied` structure is runtime state.

It represents the coordinator's knowledge of contributions established during its active runtime.

It is:

* not durable;
* not authoritative;
* not a persistence record;
* not a cross-process idempotency mechanism.

---

## 36. Rebuild and `_applied`

A successful rebuild MUST reconstruct runtime contribution state from authoritative Movement Facts as required by the Step 6.2 implementation.

This ensures that subsequent incremental operations can be evaluated against the rebuilt runtime state.

---

## 37. No Persistent Idempotency Requirement

Step 6.3 MUST NOT introduce a durable idempotency store merely to support `_applied`.

Idempotency across coordinator recreation remains outside this contract.

The bootstrap invariant provides the required runtime boundary.

---

## 38. Duplicate Establishment

Duplicate Movement establishment MUST preserve the semantics defined by authoritative persistence and existing Step 6.2 maintenance contracts.

The consistency boundary MUST NOT silently reinterpret persistence identity rules.

---

## 39. Unknown Removal

Removal of an unknown Movement MUST follow existing persistence and maintenance semantics.

Step 6.3 MUST NOT introduce a separate authoritative identity model.

---

## 40. Multi-Register Operations

A Register Operation Domain represents exactly one Register.

A logical operation involving multiple Registers therefore requires orchestration above individual Register Operation Domains.

The multi-register orchestration layer is responsible for acquisition ordering.

---

## 41. Deterministic Multi-Register Ordering

When one logical operation requires multiple Register Operation Domains:

> Domains MUST be acquired in a deterministic global order.

The ordering MUST be based on stable Register identity or another deterministic architecture-defined ordering key.

The purpose is to prevent circular acquisition and deadlock.

---

## 42. No Multi-Register Distributed Atomicity

Multi-register coordination MUST NOT imply distributed transaction semantics.

If a multi-register operation partially succeeds:

* successful authoritative mutations remain authoritative;
* failed or indeterminate portions remain explicitly observable;
* recovery MUST remain possible;
* no distributed rollback guarantee is implied.

---

## 43. Posting Integration

The Step 6.3 boundary integrates with Phase 6 through the Posting result integration layer.

Conceptually:

```text
PostingEngine
      ↓
PostingResultCoordinator
      ↓
Register Mutation Orchestration
      ↓
Register Operation Domain
     ↙                    ↘
Movement Persistence     Totals Maintenance
```

`PostingEngine` remains responsible for Posting lifecycle.

The Register consistency boundary does not replace Posting lifecycle ownership.

---

## 44. Posting Result Semantics

Posting result integration MUST ensure that a successful logical Posting does not bypass the Register consistency boundary.

For a Posting that establishes Register Movements:

1. the relevant Register operation domain is entered;
2. authoritative Movement state is established;
3. corresponding Totals state is maintained;
4. the logical operation completes successfully;
5. Posting success is reported.

The exact API sequence is defined by Concrete API Design.

---

## 45. Posting Failure Semantics

If Register mutation or Totals maintenance fails:

* Posting MUST NOT report successful logical completion;
* failure MUST be propagated according to Phase 6 semantics;
* Register recovery requirements MUST remain observable.

If a Register persistence operation is indeterminate:

* Posting MUST NOT claim successful Register consistency;
* the system MUST preserve the ability to recover.

---

## 46. Posting Event Semantics

Step 6.3 MUST NOT change Phase 6 event semantics.

`DocumentPosted`, `DocumentUnposted`, and `DocumentReposted` MUST remain emitted only after successful logical completion.

No such event may be emitted for a failed operation.

---

## 47. Persistence Boundary Preservation

`RegisterFactPersistence` remains responsible for authoritative Movement persistence.

It MUST NOT become responsible for:

* Totals calculation;
* Totals lifecycle;
* Register Operation Domain ownership;
* Posting lifecycle.

---

## 48. Totals Boundary Preservation

`TotalsMaintenanceCoordinator` remains responsible for derived Totals maintenance.

It MUST NOT become responsible for:

* authoritative Movement persistence;
* Posting lifecycle;
* ownership of the Register Operation Domain.

---

## 49. Posting Engine Boundary Preservation

`PostingEngine` remains responsible for:

* Posting Context;
* Posting lifecycle;
* Handler execution;
* Movement generation and validation;
* Posting events.

It MUST NOT become the owner of Totals maintenance semantics.

---

## 50. Storage Independence

The consistency boundary MUST remain independent of the concrete persistence provider.

It MUST work with the existing `RegisterFactPersistence` abstraction.

No filesystem-specific, database-specific, or provider-specific synchronization semantics may be required by this contract.

---

## 51. Process Scope

The Step 6.3 operation domain is process-local.

The contract does not guarantee coordination between:

* multiple processes;
* multiple application instances;
* distributed workers;
* separate runtime deployments.

Cross-process coordination is outside the scope of Step 6.3.

---

## 52. Synchronous Semantics

The logical Register operation is synchronous from the caller's perspective.

A successful operation MUST NOT be reported before its required authoritative and derived postconditions have been established.

Asynchronous eventual Totals synchronization is outside this contract.

---

## 53. Outcome Model

Operations MUST distinguish at least:

* `SUCCESS`;
* `FAILURE`;
* `INDETERMINATE`.

### SUCCESS

The required authoritative and derived postconditions were established.

### FAILURE

The operation is known not to have established the requested successful state.

### INDETERMINATE

The system cannot establish whether the requested authoritative mutation completed.

---

## 54. Success Postcondition

A successful mutation MUST satisfy:

```text
authoritative Movement state
        +
corresponding Totals state
        =
required semantic Register state
```

before logical success is reported.

---

## 55. Failure Postcondition

A failed operation MUST NOT be represented as successful.

The Register MUST remain either:

* consistent with its authoritative state; or
* explicitly non-valid/recovery-required.

---

## 56. Indeterminate Postcondition

An indeterminate operation MUST NOT claim:

`ACTIVE + VALID`.

The system MUST preserve a recovery path.

---

## 57. Error Propagation

Errors from:

* authoritative persistence;
* Totals maintenance;
* rebuild;
* recovery

MUST remain distinguishable at the semantic level necessary to determine whether the resulting state is:

* failed;
* indeterminate;
* recovery-required.

The implementation MAY translate low-level exceptions into domain-specific errors, provided semantic information is preserved.

---

## 58. Error Translation

Error translation MUST NOT convert an indeterminate operation into a deterministic failure or success without sufficient evidence.

For example:

```text
PersistenceIndeterminateError
```

MUST NOT be silently translated into an ordinary successful completion.

---

## 59. Recovery After Indeterminate Failure

An indeterminate operation MUST leave the system in a state from which authoritative Movement enumeration and rebuild can re-establish the Register.

Recovery MUST NOT depend on knowing which uncertain intermediate step occurred if authoritative Movement Facts can be enumerated and used as the recovery source.

---

## 60. Enumeration Contract

Register enumeration for rebuild MUST return the authoritative Movement Facts associated with the requested Register according to the existing `RegisterFactPersistence` contract.

The consistency boundary MUST NOT reinterpret enumeration results as Totals state.

---

## 61. Totals Reconstruction

Totals reconstruction MUST operate over authoritative Movement Facts.

The reconstruction algorithm MUST be semantically equivalent to applying the Register's defined Movement contributions to an empty derived state.

---

## 62. Publication

Rebuilt Totals and associated runtime maintenance state MUST be published only after successful reconstruction.

Partial reconstruction MUST NOT be exposed as `ACTIVE + VALID`.

---

## 63. Concurrency

Concurrent operations affecting the same Register MUST obey the same Register Operation Domain.

The implementation MUST NOT expose a public mechanism allowing callers to bypass the domain for ordinary Register mutation.

---

## 64. Rebuild / Mutation Interaction

A rebuild and an ordinary Register mutation MUST NOT overlap in a way that allows:

1. rebuild to consume Movement state;
2. mutation to change authoritative Movement state;
3. rebuild to publish Totals based on an earlier state.

The shared Register Operation Domain prevents this stale-publication race.

---

## 65. Recovery / Mutation Interaction

Recovery is subject to the same Register-scoped serialization requirement as rebuild.

A recovery operation MUST NOT race with ordinary mutation of the same Register.

---

## 66. Domain Identity and Lifetime

For a given Register, the application composition root MUST ensure that participating components use the same logical Register Operation Domain.

Creating independent domains for the same Register inside the same orchestration scope would violate the shared-domain invariant.

The exact lifetime and registry mechanism are implementation concerns.

---

## 67. No Public Synchronization Primitive

The contract MUST NOT require callers to manipulate:

* locks;
* mutexes;
* semaphores;
* synchronization tokens.

Synchronization remains an internal implementation concern.

---

## 68. Implementation Independence

The implementation MAY use:

* locks;
* reentrant locks;
* keyed lock registries;
* serialized executors;
* another process-local mechanism.

The chosen mechanism MUST preserve all semantic guarantees of this contract.

Specific reentrancy behavior is an implementation/API-design concern and is defined separately by Concrete API Design.

---

## 69. Ordering

Where operation ordering affects correctness, ordering MUST be deterministic.

This applies especially to:

* multi-register domain acquisition;
* deterministic rebuild input interpretation;
* any runtime state reconstruction that depends on iteration order.

The contract does not require a particular fairness policy for the underlying synchronization mechanism.

---

## 70. Deadlock Avoidance

The implementation MUST avoid introducing circular Register Operation Domain acquisition.

For multi-register operations this is achieved through deterministic global acquisition ordering.

Single-register operations MUST NOT require acquisition of unrelated Register domains.

---

## 71. Composition Root

The runtime composition root is responsible for constructing the shared operation-domain infrastructure and ensuring that:

* Posting integration;
* Totals maintenance;
* Register mutation orchestration

participate in the same logical domain for each Register.

---

## 72. Public API Stability

Step 6.3 MUST NOT expose synchronization internals as public domain API.

The public API SHOULD expose semantic operations rather than locks.

Concrete public/internal export decisions belong to Concrete API Design.

---

## 73. Compatibility with Step 6.2

Step 6.3 MUST preserve the Step 6.2 maintenance semantics.

In particular:

* `ACTIVE + VALID` remains the established consistent state;
* `CREATED + INDETERMINATE` remains a valid initial state;
* rebuild establishes derived state;
* recovery is rebuild-equivalent;
* `_applied` remains runtime state;
* Totals failures do not silently disappear;
* indeterminate operations do not become successful.

Step 6.3 adds orchestration and consistency-boundary semantics; it does not replace the Totals maintenance model.

---

## 74. Compatibility with Phase 6

Step 6.3 MUST preserve Phase 6 Posting semantics.

It MUST NOT alter:

* Posting Context ownership;
* Posting Handler responsibilities;
* deterministic Movement generation;
* Posting lifecycle;
* Posting event timing.

Step 6.3 provides the Register-side consistency boundary required when Posting results mutate Register state.

---

## 75. Testing Contract

The implementation MUST provide tests proving at least:

### Same Register

* mutation serialization;
* rebuild serialization;
* recovery serialization;
* no stale rebuild publication;
* Totals failure handling;
* persistence failure handling;
* persistence indeterminate handling.

### Different Registers

* independent operation;
* absence of unnecessary global serialization.

### Bootstrap

* incremental maintenance against an uninitialized pre-existing Register is rejected or otherwise prevented;
* rebuild establishes the required runtime state.

### Rebuild

* deterministic reconstruction;
* authoritative enumeration as input;
* successful publication;
* failure leaves state non-valid;
* runtime contribution state is reconstructed.

### Recovery

* successful recovery;
* failed recovery;
* recovery after indeterminate operation.

### Multi-Register

* deterministic domain acquisition order;
* deadlock avoidance;
* absence of distributed atomicity assumptions.

### Posting

* successful Posting establishes Register state through the consistency boundary;
* Register failure prevents successful Posting completion;
* Posting events are emitted only after successful logical completion.

---

## 76. Acceptance Criteria

Step 6.3 satisfies this contract when all of the following are true:

1. A single shared Register Operation Domain exists for each Register.
2. Movement mutation and Totals maintenance participate in the same domain.
3. Rebuild participates in the same domain.
4. Recovery participates in the same domain.
5. Same-Register mutation and rebuild cannot race.
6. Rebuild consumes authoritative Movement Facts.
7. Rebuild publishes only successfully reconstructed Totals state.
8. `ACTIVE + VALID` is never reported without established consistency.
9. `CREATED + INDETERMINATE` remains distinct from recovery-required state.
10. Bootstrap requires rebuild before incremental maintenance against pre-existing unestablished state.
11. `_applied` remains runtime state rather than durable idempotency state.
12. Persistence failures are represented correctly.
13. Persistence indeterminate outcomes remain recoverable and non-valid.
14. Totals failures remain observable and recovery-capable.
15. Different Registers can operate independently.
16. Multi-register domain acquisition is deterministic.
17. No distributed transaction is introduced.
18. `RegisterFactPersistence` remains storage-only.
19. `TotalsMaintenanceCoordinator` remains Totals-only.
20. Posting lifecycle remains owned by Phase 6.
21. Posting events remain success-only.
22. The design remains storage-provider independent.
23. The design remains process-local.
24. No public synchronization primitive is exposed.
25. No new persistent idempotency model is introduced.
26. No asynchronous eventual-consistency mechanism is introduced.
27. Concrete API details remain isolated in the Concrete API Design document.
28. All required tests pass.

---

## 77. Architectural Invariants

The following invariants are normative.

### INV-6.3-01 — Shared Register Domain

For each Register, all consistency-affecting operations use the same logical Register Operation Domain.

### INV-6.3-02 — Authoritative Movement State

Movement Facts are authoritative.

### INV-6.3-03 — Derived Totals

Totals are derived from authoritative Movement Facts.

### INV-6.3-04 — Same-Register Serialization

Consistency-affecting operations for one Register are serialized.

### INV-6.3-05 — Stable Rebuild Boundary

Rebuild is serialized with Register mutation from authoritative enumeration through Totals publication.

### INV-6.3-06 — Validity

`ACTIVE + VALID` means established consistency.

### INV-6.3-07 — Bootstrap

Incremental maintenance requires established runtime state for pre-existing Register state.

### INV-6.3-08 — Runtime `_applied`

`_applied` is runtime state and is not durable idempotency.

### INV-6.3-09 — Recovery

Recovery derives from authoritative Movement Facts.

### INV-6.3-10 — Indeterminate Safety

Indeterminate operations cannot produce `ACTIVE + VALID`.

### INV-6.3-11 — Register Isolation

Different Registers do not require a global serialization domain.

### INV-6.3-12 — Multi-Register Ordering

Multiple Register domains are acquired in deterministic global order.

### INV-6.3-13 — No Distributed Atomicity

Multi-register operations do not imply distributed transaction semantics.

### INV-6.3-14 — Boundary Preservation

Persistence, Totals maintenance, Register orchestration, and Posting retain separate responsibilities.

### INV-6.3-15 — Process Scope

The consistency boundary is process-local.

### INV-6.3-16 — Storage Independence

The consistency model does not depend on a particular storage provider.

---

## 78. Reference Flow — Successful Movement Establishment

```text
Posting / Register Mutation Request
            ↓
Register Operation Domain
            ↓
Persist Movement
            ↓
Apply Totals
            ↓
Publish successful logical result
```

Both authoritative and derived postconditions must be satisfied before success.

---

## 79. Reference Flow — Totals Failure

```text
Register Operation Domain
            ↓
Persist Movement
            ↓
Apply Totals
            ↓
Totals Failure
            ↓
No logical success
            ↓
Recovery Required
```

The persisted Movement remains authoritative.

---

## 80. Reference Flow — Rebuild

```text
Register Operation Domain
            ↓
Enumerate authoritative Movements
            ↓
Rebuild Totals
            ↓
Reconstruct runtime maintenance state
            ↓
Publish
            ↓
ACTIVE + VALID
```

No competing mutation of the same Register may establish state inside this boundary.

---

## 81. Reference Flow — Indeterminate Persistence

```text
Register Operation Domain
            ↓
Persistence operation
            ↓
Indeterminate result
            ↓
No VALID state
            ↓
Recovery / Rebuild
            ↓
Authoritative enumeration
            ↓
Re-establish Totals
```

---

## 82. Reference Flow — Multi-Register Operation

```text
Logical Multi-Register Operation
            ↓
Determine Register set
            ↓
Sort by deterministic Register ordering
            ↓
Acquire Register domains in order
            ↓
Execute Register operations
            ↓
Release domains
```

This provides deadlock avoidance but does not provide distributed atomicity.

---

## 83. Architectural Boundary Summary

The Step 6.3 architecture establishes the following separation:

```text
                    PostingEngine
                         │
                         ▼
               PostingResultCoordinator
                         │
                         ▼
            Register Mutation Orchestration
                         │
                         ▼
              Register Operation Domain
                    /            \
                   /              \
                  ▼                ▼
     RegisterFactPersistence   TotalsMaintenanceCoordinator
             │                         │
             ▼                         ▼
   Authoritative Movements       Derived Totals
```

The essential rule is:

> Movement persistence and Totals maintenance remain separate responsibilities, but consistency-affecting operations involving them share one Register-scoped logical operation domain.

---

## 84. Final Contract Statement

Step 6.3 establishes a Register-scoped consistency boundary between authoritative Movement Facts and derived Totals.

The boundary guarantees:

* same-Register serialization;
* stable rebuild semantics;
* explicit failure and indeterminate handling;
* recoverability;
* correct lifecycle validity;
* Register isolation;
* deterministic multi-register acquisition;
* preservation of persistence and Totals boundaries;
* compatibility with Phase 6 Posting;
* storage-provider independence;
* process-local operation.

The boundary does not provide:

* storage atomicity;
* distributed transactions;
* durable idempotency;
* eventual event-driven synchronization;
* cross-process coordination.

The implementation MUST preserve these semantics regardless of the concrete synchronization mechanism or API structure chosen.

**End of Contract**
