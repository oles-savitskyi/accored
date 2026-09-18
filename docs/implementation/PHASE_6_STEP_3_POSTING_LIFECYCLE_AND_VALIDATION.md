# Phase 6 — Step 3: Posting Lifecycle & Validation

**Status:** Draft
**Phase:** 6 — Posting & Register Integration
**Step:** 3 — Posting Lifecycle & Validation

---

# 1. Purpose

This document defines the semantic lifecycle and validation model of a Posting operation.

The purpose of this step is to establish:

* the ordered semantic stages of Posting;
* the distinction between posting preconditions, business validation, and movement validation;
* the boundary between MovementSet generation and persistence;
* Posting success and failure semantics;
* atomicity and consistency guarantees at the semantic level;
* Unposting and Reposting lifecycle semantics;
* the boundary between logical completion and event publication.

This document does not define concrete Python APIs or implementation mechanisms.

---

# 2. Relationship with Posting Architecture

Posting Architecture defines the ownership and responsibilities of the Posting subsystem.

The semantic lifecycle defined here operates within the following architectural boundaries:

```text
Operational Document
        ↓
Posting Engine
        ↓
Posting Context
        ↓
Posting Handler
        ↓
MovementSet
        ↓
Movement Validation
        ↓
Persistence Coordination
        ↓
Logical Completion
        ↓
Posting Events
```

The Posting Engine remains the orchestrator of the Posting operation.

The Posting Handler remains responsible for document-specific accounting semantics and MovementSet generation.

Movement validation remains separate from document/business validation.

Persistence coordination remains outside the accounting semantics of the Posting Handler.

---

# 3. Posting Operation

A Posting operation is an explicit accounting operation applied to an operational document.

Posting transforms the applicable document state into a complete and validated set of accounting movements and establishes the corresponding persistent accounting result.

Posting is distinct from ordinary document persistence.

Saving a document does not implicitly constitute Posting.

The semantic operation is:

```text
Document State
      ↓
Posting
      ↓
Accounting Result
```

The accounting result is represented by the MovementSet and its successfully established persistent effects.

---

# 4. Posting Lifecycle

A successful Posting operation follows this semantic lifecycle:

```text
Posting Request
        ↓
Validate Posting Preconditions
        ↓
Resolve Posting Handler
        ↓
Create Posting Context
        ↓
Execute Posting Handler
        ↓
Generate MovementSet
        ↓
Validate MovementSet
        ↓
Coordinate Required Persistent Result
        ↓
Logical Completion
        ↓
Publish Posting Events
```

The lifecycle defines semantic ordering.

It does not prescribe a concrete transaction, storage, persistence, or event delivery mechanism.

---

# 5. Posting Preconditions

Posting Preconditions are conditions that must be satisfied before Posting execution may proceed.

Examples include:

* the document exists;
* the document is in a state that permits Posting;
* the applicable document type is postable;
* required posting metadata is available;
* the Posting Handler can be resolved;
* required platform capabilities are available;
* required configuration and reference state are available.

Posting Preconditions are evaluated before accounting effects are generated.

A failed precondition prevents Posting execution from producing a successful accounting result.

---

# 6. Business Validation

Business Validation verifies whether the document state is semantically valid for the applicable business operation.

Business Validation may include:

* required document fields;
* business-specific invariants;
* document status requirements;
* quantity or value constraints;
* business-specific reference requirements;
* configuration-specific posting rules.

Business Validation is distinct from Movement Validation.

The Posting Handler may participate in document-specific business validation, but it does not become responsible for the complete Posting lifecycle or persistence process.

---

# 7. Posting Handler Resolution

The Posting Engine resolves the Posting Handler applicable to the document type and posting operation.

Handler resolution is metadata-driven according to the existing Posting Architecture.

Failure to resolve an applicable Handler is a Posting failure.

The Posting Engine remains responsible for Handler resolution.

The Posting Handler does not resolve itself.

---

# 8. Posting Context Creation

The Posting Engine creates the Posting Context for the current Posting operation.

Posting Context provides the controlled runtime capabilities required by Posting logic.

The Posting Context is an execution boundary and is not a general-purpose service locator.

The concrete contents and implementation of Posting Context are outside the scope of this step.

The Posting Handler may use capabilities exposed through the Posting Context but must not bypass the established platform service boundaries.

---

# 9. Handler Execution

The Posting Engine executes the resolved Posting Handler within the applicable Posting Context.

The Posting Handler is responsible for document-specific accounting semantics.

The Posting Handler:

* interprets the applicable document state;
* applies document-specific accounting rules;
* generates the accounting movements;
* produces the MovementSet.

The Posting Handler does not:

* persist movements;
* manage transactions;
* manage Persistence Scope;
* update totals directly;
* manage dependency state directly;
* publish Posting events.

---

# 10. MovementSet Generation

A Posting Handler produces exactly one complete MovementSet for one Posting operation.

The MovementSet represents the complete semantic accounting result generated by the Handler.

The MovementSet is the boundary between document-specific accounting semantics and movement validation/persistence coordination.

The semantic relationship is:

```text
Document State
      ↓
Posting Handler
      ↓
Complete MovementSet
```

The MovementSet must be complete before Movement Validation begins.

---

# 11. MovementSet Completeness

A MovementSet is complete when it contains all movements required to represent the accounting effect of the current Posting operation.

The Posting Handler must not intentionally omit mandatory accounting effects and rely on later lifecycle stages to infer them.

The Posting Engine does not invent missing document-specific movements.

If the Handler cannot produce a complete valid MovementSet, Posting fails.

The MovementSet becomes immutable after Handler execution.

---

# 12. Movement Validation

Movement Validation verifies whether the generated MovementSet is valid for the applicable register contracts.

The semantic flow is:

```text
Posting Handler
      ↓
MovementSet
      ↓
Movement Validation
      ↓
Register Posting Contracts
      ↓
Accepted / Rejected
```

Movement Validation may verify:

* movement structure;
* movement type;
* dimensions;
* resources;
* attributes;
* data types;
* required register fields;
* register-specific constraints;
* applicable Register Posting Contracts.

Movement Validation does not generate accounting intent.

The Handler generates accounting intent; the Validator verifies the resulting movements.

---

# 13. Validation Before Persistence

No generated movement may be persisted as an accepted accounting effect before the applicable Movement Validation has successfully completed.

The required ordering is:

```text
Generate Complete MovementSet
        ↓
Validate Complete MovementSet
        ↓
Allow Persistence Coordination
```

The following sequence is invalid:

```text
Generate MovementSet
        ↓
Persist Partial MovementSet
        ↓
Validate Remaining Movements
```

A MovementSet that fails applicable validation must not be exposed as a successfully posted accounting result.

---

## 14. Persistence Coordination

After successful MovementSet validation, the Posting Engine coordinates establishment of the required persistent Posting result through the applicable persistence and application services.

Posting Engine responsibility at this stage is orchestration and lifecycle coordination.

Posting Engine does not own or define:

* physical persistence mechanisms;
* storage-provider behavior;
* physical transaction mechanisms;
* transaction isolation;
* commit or rollback APIs.

The applicable persistence and application services remain responsible for implementing the persistent effects required by the Posting operation.

A Posting operation is not considered successfully completed merely because the MovementSet has been generated and validated.

Successful Posting requires that the required persistent result has been successfully established according to the applicable consistency contract.

---

# 15. Persistence Scope Boundary

A Posting operation may produce multiple persistent effects that together form one logical accounting result.

Such effects participate in the applicable Persistence Scope according to the Persistence Architecture.

The semantic requirement is:

```text
Posting Operation
      ↓
Required Persistent Effects
      ↓
One Consistent Logical Result
```

The Posting lifecycle does not prescribe whether this is implemented using a database transaction, unit of work, journal, compensation mechanism, or another persistence mechanism.

The applicable Persistence Scope is determined by the logical persistent effects that form part of the Posting result.

Persistent effects that are required to establish one logical Posting result must participate in the applicable consistency boundary.

The semantic contract does not prescribe the physical mechanism used to implement that consistency boundary.

---

# 16. Logical Completion

Logical Completion is reached only when all mandatory stages of the Posting operation have successfully completed according to the applicable consistency contract.

Logical Completion requires, at minimum:

* valid Posting Preconditions;
* successful Handler resolution;
* successful Handler execution;
* complete MovementSet generation;
* successful Movement Validation;
* successful establishment of the required persistent accounting result.

Logical Completion is the semantic success boundary of Posting.

A physical transaction commit is not itself the definition of Logical Completion.

---

# 17. Posting Success

A Posting operation succeeds only after Logical Completion.

Successful Posting means that:

```text
Document
      ↓
Valid Posting
      ↓
Complete MovementSet
      ↓
Validated Accounting Result
      ↓
Required Persistent Result Established
      ↓
Logical Completion
```

A successful result must represent the completed accounting operation.

No Posting stage may report success before all mandatory accounting effects have been successfully established according to the applicable consistency contract.

---

# 18. Posting Failure

A Posting operation fails if any mandatory Posting stage fails.

Examples include:

* failed Posting Preconditions;
* Handler resolution failure;
* Posting Context creation failure;
* Handler execution failure;
* incomplete MovementSet;
* Movement Validation failure;
* Register Posting Contract violation;
* failure to establish required persistent effects;
* failure to establish another mandatory accounting effect.

A failed Posting operation must not be reported as successfully posted.

Failures must remain observable to the caller through the applicable Posting error contract.

The Posting Architecture does not require a particular exception hierarchy in this step.

---

# 19. Partial Accounting Result

A Posting operation must not expose a partially established accounting result as a successful Posting.

If a failure occurs after accounting effects have started to be established, the applicable consistency mechanism must ensure that the resulting state satisfies the Posting consistency contract.

The semantic requirement is:

```text
Failure
   ↓
No Successful Posting
   ↓
No Exposed Partial Accounting Result
```

The concrete mechanism used to achieve this guarantee is outside the scope of this step.

---

# 20. Atomicity

Posting is atomic at the semantic level.

For a successful Posting operation, all required accounting effects belonging to the logical Posting result are established consistently.

For a failed Posting operation, the system must not expose a partially applied accounting result as a successful Posting.

The semantic contract does not prescribe the physical implementation of atomicity.

Possible implementation mechanisms include, but are not limited to:

* database transactions;
* Persistence Scope;
* journals;
* compensation;
* recovery mechanisms.

The choice of mechanism belongs to the applicable platform implementation architecture.

---

# 21. Validation Failure

Validation failure terminates the current Posting operation before successful persistence of the invalid accounting result.

The failure path is:

```text
MovementSet
      ↓
Movement Validation
      ↓
Rejected
      ↓
Posting Failure
```

A validation failure must not be converted into a successful Posting result.

The invalid MovementSet must not become an accepted persistent register result.

---

# 22. Unposting Lifecycle

Unposting removes the accounting effects associated with a previously posted document.

The semantic lifecycle is:

```text
Posted Document
      ↓
Unposting Request
      ↓
Identify Existing Posting Effects
      ↓
Remove Applicable Accounting Effects
      ↓
Logical Completion
      ↓
DocumentUnposted
```

Unposting is an explicit accounting operation.

It is not equivalent to deleting the document.

The exact movement removal and persistence algorithm is outside the scope of this step.

---

# 23. Unposting Consistency

Unposting must preserve accounting consistency.

If Unposting succeeds, the accounting effects associated with the applicable Posting must no longer contribute to the active accounting result.

If Unposting fails, the operation must not be reported as successfully completed.

The system must not expose an accounting state that violates the applicable consistency contract.

---

# 24. Reposting Lifecycle

Reposting rebuilds the accounting effects for an already posted document using its current applicable state.

The semantic flow is:

```text
Already Posted Document
        ↓
Reposting Request
        ↓
Current Document State
        ↓
Generate New MovementSet
        ↓
Validate New MovementSet
        ↓
Establish New Persistent Accounting Result
        ↓
Logical Completion
        ↓
DocumentReposted
```

Reposting is therefore a rebuilding operation rather than manual mutation of existing movements.

The exact implementation sequence for replacing existing movements is outside the scope of this step.

---

# 25. Reposting Consistency

Reposting must produce accounting effects corresponding to the current applicable document state.

The resulting accounting state must not depend on manually modifying existing movements as the primary semantic mechanism.

For equivalent applicable inputs, reposting must produce the same semantic MovementSet according to the Deterministic Posting contract.

If rebuilding the accounting result fails, the system must not expose the operation as successfully reposted.

---

# 26. Event Boundary

Posting events represent successfully completed Posting-related operations.

Events are published only after Logical Completion.

Core Posting events include:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

Events must not be emitted for failed operations.

Event data must represent the completed operation and must remain immutable after publication.

Event publication must not expose a Posting operation as successful before all required accounting effects have been successfully established according to the applicable consistency contract.

The semantic contract does not prescribe a physical transaction or commit mechanism.

The exact event delivery mechanism is implementation-specific.

---

## 27. Dependency Boundary

Posting may interact with dependency state and restoration workflows through the Posting Architecture integration boundary.

Dependency-related effects that form part of the required logical Posting result must participate in the applicable consistency boundary.

Dependency management itself remains outside the responsibility of the Posting Handler.

The concrete dependency update, restoration, and consistency mechanisms are implementation concerns and are deferred to the applicable dependency and persistence architecture.

---

# 28. Validation Responsibilities

Validation responsibilities are divided as follows:

```text
Posting Preconditions
        ↓
Posting Engine / Applicable Posting Lifecycle

Business Validation
        ↓
Document-specific Posting Logic

Movement Validation
        ↓
Movement Validator

Register Acceptance
        ↓
Register Posting Contract
```

No single component is required to own all forms of validation.

This separation prevents document-specific accounting logic from becoming responsible for register infrastructure concerns.

---

# 29. Lifecycle Invariants

The following invariants are normative.

### PST-LCV-01 — Explicit Posting

Posting is an explicit accounting operation and is distinct from ordinary document persistence.

### PST-LCV-02 — Ordered Lifecycle

Posting stages execute according to the semantic lifecycle defined by this document.

### PST-LCV-03 — Preconditions Before Accounting

Posting Preconditions must be satisfied before successful accounting effects can be generated.

### PST-LCV-04 — Complete MovementSet

Each Posting operation produces exactly one complete MovementSet.

### PST-LCV-05 — Immutable MovementSet

The MovementSet is immutable after Handler execution.

### PST-LCV-06 — Validation Before Persistence

A generated MovementSet must successfully pass applicable Movement Validation before it can be accepted for persistence.

### PST-LCV-07 — Handler Boundary

The Posting Handler owns document-specific accounting semantics and does not own persistence, transaction, totals, dependency, or event management.

### PST-LCV-08 — Logical Completion

Posting success is defined by Logical Completion, not by a particular physical transaction mechanism.

### PST-LCV-09 — Failure Is Not Success

A failed Posting operation must never be reported as successfully completed.

### PST-LCV-10 — No Successful Partial Result

A partially established accounting result must not be exposed as a successful Posting.

### PST-LCV-11 — Semantic Atomicity

All required accounting effects belonging to one logical Posting result participate in the applicable consistency boundary.

### PST-LCV-12 — Event Boundary

Posting success events are emitted only after Logical Completion.

### PST-LCV-13 — Unposting

Successful Unposting removes the applicable accounting effects of the previous Posting.

### PST-LCV-14 — Reposting

Reposting rebuilds accounting effects from the current applicable document state.

### PST-LCV-15 — Reposting Consistency

A failed Reposting operation must not be reported as successfully completed.

### PST-LCV-16 — Register Independence

Posting lifecycle semantics remain register-agnostic. Register-specific acceptance rules belong to Register Posting Contracts.

### PST-LCV-17 — Dependency Boundary

Posting Handlers do not directly manage dependency graph state.

### PST-LCV-18 — Phase 5 Boundary Preservation

Posting lifecycle semantics do not bypass the persistence, runtime, storage, identity, or materialization boundaries established by Phase 5.

---

# 30. Failure Invariants

The following failure rules are normative.

```text
Precondition Failure
        ↓
Posting Failure

Handler Failure
        ↓
Posting Failure

Movement Validation Failure
        ↓
Posting Failure

Persistence Failure
        ↓
Posting Failure

Required Consistency Failure
        ↓
Posting Failure
```

In all cases:

```text
Posting Failure
      ↓
No Successful Posting Event
      ↓
No Exposed Successful Partial Accounting Result
```

The concrete recovery or rollback mechanism is implementation-specific.

---

# 31. Deterministic Lifecycle

The lifecycle itself must not introduce nondeterministic behavior.

Given the same applicable:

* document state;
* metadata;
* reference state;
* Posting Context;
* accounting time/environment;

the Posting operation must produce the same semantic accounting result.

Nondeterminism must not be introduced by:

* runtime object identity;
* storage layout;
* storage provider behavior;
* arbitrary collection ordering;
* uncontrolled system time;
* uncontrolled external state.

Where current time is a legitimate Posting input, it must be supplied through the Posting Context time boundary.

---

# 32. Explicit Non-Goals

This step does not define:

* concrete Posting Engine Python APIs;
* concrete Posting Context APIs;
* concrete Posting Handler APIs;
* transaction APIs;
* database transaction implementation;
* Persistence Scope APIs;
* Movement Service APIs;
* Register Movement APIs;
* concrete rollback implementation;
* journal or recovery implementation;
* idempotency mechanism;
* exact Reposting algorithm;
* exact dependency processing algorithm;
* event transport or delivery infrastructure;
* Standard Configuration register mapping.

These concerns are deferred to subsequent Phase 6 steps or their respective architecture boundaries.

---

# 33. Relationship with Phase 5

Step 3 does not reopen or modify the persistence architecture established in Phase 5.

Posting uses persistence capabilities through their published contracts.

Posting does not directly depend on:

* physical storage structures;
* storage provider internals;
* persistent object implementation details;
* runtime object reconstruction mechanisms.

The Posting lifecycle remains above the Persistence and Storage implementation boundaries.

The following architectural direction remains mandatory:

```text
Posting
   ↓
Persistence Contract
   ↓
Storage / Persistence Implementation
```

and not:

```text
Posting
   ↓
Storage Provider Internals
```

---

# 34. Step 3 Acceptance Criteria

Step 3 is accepted when all of the following are true:

* [ ] Posting lifecycle is explicitly defined.
* [ ] Posting Preconditions are distinguished from Business Validation.
* [ ] Business Validation is distinguished from Movement Validation.
* [ ] Handler resolution belongs to Posting orchestration.
* [ ] Posting Context creation belongs to Posting orchestration.
* [ ] Handler execution is explicitly bounded.
* [ ] One Posting operation produces one complete MovementSet.
* [ ] MovementSet completeness is defined.
* [ ] MovementSet validation precedes persistence acceptance.
* [ ] Register Posting Contracts remain the register acceptance boundary.
* [ ] Persistence coordination is separated from Handler responsibilities.
* [ ] Logical Completion is explicitly defined.
* [ ] Posting success is defined independently from a physical transaction mechanism.
* [ ] Posting failure semantics are defined.
* [ ] Partial accounting results cannot be exposed as successful Posting.
* [ ] Semantic atomicity is defined without prescribing implementation.
* [ ] Unposting lifecycle is defined.
* [ ] Reposting lifecycle is defined.
* [ ] Reposting is based on rebuilding accounting effects from current document state.
* [ ] Event publication occurs only after Logical Completion.
* [ ] Dependency management remains outside the Posting Handler.
* [ ] Lifecycle invariants are explicitly documented.
* [ ] Failure invariants are explicitly documented.
* [ ] Phase 5 boundaries remain preserved.
* [ ] Concrete implementation APIs remain deferred to later steps.

---

# 35. Architecture Review

Architecture Review: APPROVED

Review result:

Blockers: 0
Major architectural issues: 0
Minor alignment issues: 0
Required alignments: completed

The Step 3 semantic lifecycle and validation model are consistent with the Posting Architecture, Posting Handler boundary, Movement Validation boundary, Persistence Scope model, Dependency boundary, Event boundary, and Phase 5 persistence/storage architecture.

No physical transaction mechanism, concrete persistence API, reposting algorithm, or dependency implementation is prescribed by this step.

# 36. Related Architecture

docs/architecture/posting/POSTING_ARCHITECTURE.md
docs/architecture/posting/POSTING_LIFECYCLE.md
docs/architecture/posting/POSTING_HANDLERS.md
docs/architecture/posting/POSTING_CONTEXT.md
docs/architecture/posting/MOVEMENT_VALIDATION.md
docs/architecture/posting/REGISTER_POSTING_CONTRACTS.md
Phase 5 Persistence Architecture
Phase 5 Storage Provider Boundary

# 37. Step 3 Status

Step 3 — Posting Lifecycle & Validation

Status: CLOSED
