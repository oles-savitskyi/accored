# Phase 6 — Step 6: Public Posting API

## 1. Purpose

This document defines the public architectural boundary through which the rest of the platform requests Posting operations.

The purpose of this step is to establish:

* the public Posting operations;
* the public Posting request boundary;
* the distinction between Posting, Unposting, and Reposting;
* the semantic input required by the Posting operation;
* the public success boundary;
* the public failure boundary;
* the representation of Indeterminate Posting Outcome;
* the relationship between the public API and Posting Engine;
* the boundary between public Posting operations and internal Posting infrastructure;
* the rules preventing callers from bypassing Posting Architecture.

This step defines the semantic public contract.

It does NOT define a concrete Python class hierarchy, exact method signatures, exception classes, dependency injection mechanism, or transport protocol.


## 2. Relationship with Existing Architecture

Step 6 exposes the Posting Architecture established by previous steps through a controlled public boundary.

The architectural flow is:

```text
Operational Document
        ↓
Public Posting API
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
Register Posting Contract
        ↓
Required Persistent Result
        ↓
Logical Completion
        ↓
Posting Result
```

The Public Posting API is an entry boundary.

It does not replace the Posting Engine.

The Posting Engine remains responsible for Posting orchestration.

The Posting API therefore has the following relationship:

```text
Public Posting API
        ↓
request / operation boundary
        ↓
Posting Engine
        ↓
posting orchestration
```

The Public Posting API MUST NOT duplicate Posting Engine responsibilities.

## 3. Public Posting Boundary

Posting MUST be initiated through an explicit public Posting operation.

The public boundary exists to prevent callers from directly coordinating:

Posting Handlers;
Movement generation;
Movement validation;
Register acceptance;
accounting persistence;
Posting events;
consistency handling.

The public architectural boundary is:

```text
Caller
  ↓
Public Posting API
  ↓
Posting Engine
  ↓
Posting Architecture
```

The caller MUST NOT be required to understand the internal Posting lifecycle in order to request a Posting operation.

## 4. Public Posting Operations

The public Posting boundary defines three distinct accounting operations:

Post
Unpost
Repost

They have distinct semantic meanings.

### 4.1 Post

Post establishes the accounting result corresponding to the current semantic state of a source document.

Conceptually:

```text
Document
    ↓
Post
    ↓
MovementSet
    ↓
Required Persistent Result
    ↓
Logical Completion
```

### 4.2 Unpost

Unpost removes the applicable accounting effects previously established by Posting.

Conceptually:

```text
Posted Document
    ↓
Unpost
    ↓
Remove Applicable Accounting Effects
    ↓
Logical Completion
```

### 4.3 Repost

Repost rebuilds the accounting result from the current semantic state of the source document.

Conceptually:

```text
Posted Document
    ↓
Repost
    ↓
Current Document State
    ↓
New MovementSet
    ↓
New Required Persistent Result
    ↓
Logical Completion
```

These operations MUST remain semantically distinct.

The API MUST NOT model Repost as an ordinary Post with an implicit or hidden flag.

## 5. Source Document

The source Document is the primary semantic input to Posting.

Posting semantics are derived from the current state of the source Document and applicable Posting inputs.

The Public Posting API MUST identify the source Document explicitly.

The API MUST NOT require callers to provide a pre-generated MovementSet as the input to Posting.

Conceptually:

```text
Document
    ↓
Posting API
    ↓
Posting Engine
    ↓
Posting Handler
    ↓
MovementSet
```

The MovementSet is an output of Posting semantics, not a caller-provided accounting instruction.

The conceptual notation `Post(Document)`, `Unpost(Document)`, and `Repost(Document)` denotes an operation against an explicitly identified source Document.

This notation does not prescribe whether the concrete public API accepts a runtime Document instance, a persistent Document identity, or another application-level reference representation.

The concrete representation is deferred to implementation design.

## 6. Document Identity

The Public Posting API MUST operate on an explicitly identifiable source Document.

The source Document identity MUST remain stable across the Posting operation.

The identity used by Posting Architecture MUST correspond to the durable identity of the source object.

Runtime object identity MUST NOT be used as the durable accounting identity.

This preserves the identity boundary established by Phase 5 and the Register Movement Contract.

## 7. Posting Request

A Posting request represents the caller's intention to perform a specific Posting operation against a specific source Document.

Conceptually:

```text
Posting Request
├── operation
├── source document identity
└── applicable posting inputs
```

The exact representation of a Posting Request is outside the scope of this step.

A request MUST contain sufficient semantic information for the Posting Engine to:

identify the source Document;
determine the requested operation;
establish the applicable Posting Context;
execute the Posting lifecycle.

The request MUST NOT contain internal orchestration state that belongs to Posting Engine.

## 8. Posting Inputs

The Public Posting API MAY accept inputs that are legitimately part of the Posting operation.

Such inputs MAY include:

source Document identity;
applicable accounting time boundary;
caller/session context;
explicitly supplied Posting options defined by the Posting contract.

Posting inputs MUST be semantically meaningful.

The API MUST NOT expose infrastructure controls such as:

physical transaction control;
storage provider selection;
rollback commands;
database connections;
persistence implementation details;
Register storage details.

Concrete Posting Context contents remain an internal architectural concern unless explicitly promoted to a public semantic input.

## 9. Posting Context Boundary

Posting Context is created and owned by the Posting Engine.

The Public Posting API does not create or manage Posting Context directly.

Conceptually:

```text
Public Posting API
        ↓
Posting Engine
        ↓
Create Posting Context
        ↓
Posting Handler
```

The caller MUST NOT be required to construct a Posting Context manually.

The caller MUST NOT control the lifecycle of Posting Context.

Posting Context therefore remains an internal runtime capability boundary.

## 10. Posting Engine Boundary

The Posting Engine is the implementation owner of Posting orchestration.

The Public Posting API delegates the requested operation to the Posting Engine.

The Posting Engine is responsible for coordinating:

Posting Handler resolution;
Posting Context creation;
Handler execution;
MovementSet generation;
Movement validation;
Register acceptance;
Required Persistent Result;
Logical Completion;
Posting events;
applicable dependency integration.

The Public Posting API MUST NOT duplicate these responsibilities.

## 11. Posting Handler Boundary

The Public Posting API MUST NOT expose Posting Handler as a caller-facing extension point for ordinary Posting operations.

The caller requests:

Post(Document)

rather than:

Handler.post(Context)

Handler resolution remains a Posting Engine responsibility.

This prevents callers from bypassing:

Posting validation;
consistency coordination;
Register acceptance;
lifecycle semantics;
event boundaries.

## 12. MovementSet Boundary

The Public Posting API MUST NOT require callers to construct the MovementSet used by Posting.

The MovementSet is generated by Posting Handler and validated by Posting Architecture.

Conceptually:

```text
Public Request
      ↓
Posting Engine
      ↓
Posting Handler
      ↓
MovementSet
      ↓
Movement Validation
```

The Public API therefore exposes Posting as an accounting operation rather than as a low-level movement insertion mechanism.

## 13. Register Boundary

The Public Posting API MUST NOT expose direct Register movement submission as an alternative to Posting.

The caller MUST NOT need to know:

which Register accepts the generated Movement;
how Register Posting Contracts are resolved;
how Register acceptance is performed;
how accepted movements become persistent accounting state.

Those concerns remain inside Posting and Register Architecture.

## 14. Posting Success

A successful public Posting result means that the Posting operation reached Logical Completion.

Success therefore implies that:

Posting preconditions succeeded;
Posting Handler execution completed;
the complete MovementSet was generated;
applicable validation succeeded;
applicable Register acceptance succeeded;
the Required Persistent Result was established;
all mandatory Posting stages completed.

Conceptually:

```text
Required Persistent Result
        ↓
Logical Completion
        ↓
Public Posting Success
```

Generation of a MovementSet MUST NOT by itself be represented as successful Posting.

## 15. Posting Failure

A public Posting failure means that the requested Posting operation did not reach successful Logical Completion.

Failure MAY originate from:

Posting preconditions;
Handler resolution;
Handler execution;
Movement validation;
Register acceptance;
persistence/application coordination;
dependency/consistency handling.

The public API MUST preserve the semantic distinction between failure categories where that distinction is required by the caller or higher-level application logic.

The concrete error representation is outside the scope of this step.

## 16. Indeterminate Outcome

The Public Posting API MUST distinguish an Indeterminate Outcome from a known failure when the system cannot determine whether the Required Persistent Result was established.

Conceptually:

Known Success
Known Failure
Indeterminate Outcome

An Indeterminate Outcome MUST NOT be silently converted into:

Success

or:

Known Failure

when the actual persistent accounting state remains uncertain.

The public representation of this outcome MUST preserve the semantic distinction.

The exact result type or exception mechanism is outside the scope of this step.

## 17. Public Result Boundary

The Public Posting API MUST communicate the semantic outcome of the requested operation.

At minimum, the public contract MUST preserve the distinction between:

* successful Logical Completion;
* known failure;
* Indeterminate Outcome.

A successful outcome MUST indicate Logical Completion.

A failed outcome MUST indicate that successful Logical Completion was not established.

An Indeterminate Outcome MUST indicate that the persistent outcome cannot be reliably determined.

The concrete representation of these outcomes is deferred to the implementation stage.

## 18. Posting vs Document Persistence

The Public Posting API MUST NOT be interpreted as a document persistence API.

The following operations remain distinct:

```text
Save Document
        ≠
Post Document
```

Saving a Document MUST NOT implicitly mean that the Document has been posted unless a higher-level application contract explicitly defines such behavior.

Likewise, Posting MUST NOT be interpreted as merely saving the current Document state.

Posting establishes accounting effects.

## 19. Post Preconditions

A public Post operation MUST be subject to the applicable Posting preconditions before accounting effects are established.

The Public Posting API MUST ensure that the requested operation enters the Posting lifecycle through the appropriate validation boundary.

The evaluation of Posting preconditions remains a Posting Architecture responsibility and MUST NOT be duplicated as document-specific business logic in the Public API.

Examples MAY include:

* source Document exists;
* source Document is in a postable state;
* required metadata is available;
* required Posting Handler can be resolved;
* required Posting Context inputs are available.

Concrete business preconditions belong to the applicable document/posting semantics.

## 20. Unpost API Semantics

Unpost is a distinct public accounting operation.

The semantic request is:

Unpost(Document)

rather than:

Post(Document, mode="remove")

Unpost MUST identify the source Document whose applicable accounting effects are to be removed.

A successful Unpost means:

```text
Applicable Posting Effects Removed
        ↓
Logical Completion
```

The Public API MUST NOT expose the physical mechanism by which existing effects are identified or removed.

## 21. Repost API Semantics

Repost is a distinct public accounting operation.

The semantic request is:

Repost(Document)

rather than:

Post(Document, force=True)

or:

Post(Document, replace=True)

Repost MUST cause the accounting result to be rebuilt from the current semantic state of the source Document.

The public operation therefore expresses a semantic intention, not a persistence shortcut.

## 22. Reposting and Current Document State

Repost MUST use the current semantic state of the source Document.

The Public API MUST NOT require the caller to provide:

the previous MovementSet;
existing register records;
manually modified movements;
previous posting output.

Conceptually:

```text
Current Document
        ↓
Repost
        ↓
Posting Semantics
        ↓
New MovementSet
```

The caller requests Reposting; Posting Architecture determines the resulting accounting facts.

## 23. Reposting and Idempotency

The Public Posting API MUST NOT treat Repost as an idempotency mechanism.

The concepts remain distinct:

Retry
    → repeat execution of a logical request

Idempotency
    → repeated equivalent request does not create an additional logical effect

Repost
    → rebuild accounting result from current document state

Concrete idempotency guarantees, keys, or request deduplication mechanisms are outside the scope of this step.

## 24. Public API and Retry

The Public Posting API MAY be invoked again after a known failure when the caller determines that retry is appropriate.

However, retry behavior MUST NOT be inferred from the semantic meaning of Repost.

In particular:

```text
Retry after known failure
        ≠
Repost
```

An Indeterminate Outcome requires special handling because the persistent state may already contain the requested accounting result.

The Public API MUST preserve that distinction so that higher-level infrastructure can apply an appropriate retry or reconciliation strategy.

## 25. Event Boundary

Posting events are internal consequences of successful logical Posting operations.

The Public Posting API MUST NOT report Posting success before Logical Completion.

Conceptually:

```text
Logical Completion
        ↓
Posting Success
        ↓
Posting Event
```

Event publication is not itself the definition of Posting success.

Failure to publish or deliver an event MUST NOT automatically imply that the Required Persistent Result was not established.

The concrete event delivery mechanism is outside the scope of this step.

## 26. Dependency Boundary

The Public Posting API MUST NOT expose direct dependency-management operations as part of ordinary Posting.

Dependency-related behavior remains an internal integration responsibility of Posting Architecture.

If dependency effects form part of the Required Persistent Result, they remain covered by the applicable consistency boundary.

The caller requests Posting semantics rather than individual dependency updates.

## 27. Persistence Boundary

The Public Posting API MUST NOT expose physical persistence controls.

The caller MUST NOT control:

Persistence Scope;
transaction boundaries;
commit;
rollback;
storage provider;
register storage;
database connections;
persistence implementation.

Conceptually:

```text
Caller
  ↓
Public Posting API
  ↓
Posting Engine
  ↓
Persistence / Application Boundary
```

This preserves the Phase 5 Persistence Architecture.

## 28. Storage Boundary

The Public Posting API MUST NOT expose Storage Provider semantics.

The Posting caller MUST remain independent of:

filesystem storage;
database storage;
in-memory storage;
storage provider selection;
storage layout.

The public Posting operation expresses accounting intent.

Physical storage remains an infrastructure concern.

## 29. Standard Application Entry Boundary

For standard platform Posting operations, the Public Posting API is the supported application-level entry boundary.

Application-level Posting flows MUST NOT bypass the semantic guarantees provided by the Public Posting API and Posting Engine.

Internal infrastructure and testing mechanisms MAY use lower-level components when explicitly required by their architectural role.

Such internal mechanisms MUST NOT become alternative application-level Posting paths that bypass:

* Posting lifecycle;
* validation;
* consistency coordination;
* Register acceptance;
* Logical Completion;
* Posting event boundaries.

## 30. Operation Atomicity at Public Boundary

The Public Posting API MUST expose one logical outcome for one requested Posting operation.

It MUST NOT report:

success

when the Required Persistent Result is known to be incomplete.

Likewise, an Indeterminate Outcome MUST remain distinguishable from successful completion.

The public boundary therefore preserves the semantic atomicity established by Step 5.

## 31. Public API and Runtime Identity

The Public Posting API MUST NOT make runtime object identity part of the durable accounting contract.

A runtime Document object MAY be used internally to execute Posting.

However:

```text
runtime object identity
        ≠
durable source document identity
```

This preserves the identity rules established by Phase 5 and Step 4.

## 32. Public API and Determinism

The Public Posting API MUST preserve the deterministic Posting contract.

For equivalent relevant semantic inputs, equivalent Posting requests MUST produce equivalent semantic accounting results.

The public API MUST NOT introduce uncontrolled sources of nondeterminism.

In particular, Posting behavior MUST NOT depend on:

runtime object identity;
storage layout;
arbitrary collection ordering;
uncontrolled system time;
uncontrolled external state.

Applicable accounting time/environment inputs MUST be explicitly controlled by the Posting architecture.

## 33. Public API Error Boundary

The Public Posting API MUST preserve the semantic distinction necessary to determine the outcome of the requested Posting operation.

The public contract MUST allow the appropriate higher-level caller to distinguish, where relevant:

* invalid Posting request;
* business/document validation failure;
* Movement validation failure;
* Register acceptance failure;
* persistence/consistency failure;
* Indeterminate Outcome.

The Public API MUST NOT require every internal failure category to become a separate public exception or result type.

The exact error taxonomy and concrete exception/result representation are implementation concerns.

The semantic distinction required by the Posting Architecture MUST remain available at the appropriate architectural boundary.

## 34. Public API and Internal Architecture

The Public Posting API is a facade over Posting Architecture, not a second Posting implementation.

Its responsibilities are limited to:

accepting the public Posting operation;
validating public request-level requirements;
invoking the Posting Engine;
returning the semantic Posting outcome.

It MUST NOT own:

document-specific accounting semantics;
Movement generation;
Movement validation;
Register semantics;
persistence orchestration;
transaction control;
dependency management;
event transport.

## 35. Public API Invariants

The following invariants are normative.

### PST-API-01 — Explicit Operation

Posting MUST be an explicit public accounting operation.

### PST-API-02 — Document Identity

The source Document MUST be explicitly identifiable.

### PST-API-03 — Posting Engine Boundary

Public Posting operations MUST delegate Posting orchestration to the Posting Engine.

### PST-API-04 — Handler Encapsulation

Posting Handler MUST NOT be the ordinary application-level Posting entry point.

### PST-API-05 — Movement Encapsulation

The caller MUST NOT be required to construct the MovementSet for ordinary Posting.

### PST-API-06 — Register Encapsulation

The caller MUST NOT directly submit Posting movements to Registers as an alternative standard Posting path.

### PST-API-07 — Success Boundary

Public Posting success MUST imply Logical Completion.

### PST-API-08 — Failure Boundary

Known Posting failure MUST NOT be reported as successful Posting.

### PST-API-09 — Indeterminate Outcome

Indeterminate Outcome MUST remain distinguishable from both known success and known failure.

### PST-API-10 — Persistence Independence

The Public Posting API MUST NOT expose physical persistence mechanisms.

### PST-API-11 — Storage Independence

The Public Posting API MUST NOT expose Storage Provider semantics.

### PST-API-12 — Context Ownership

Posting Context MUST be created and owned by Posting Engine.

### PST-API-13 — Operation Distinction

Post, Unpost, and Repost MUST remain semantically distinct operations.

### PST-API-14 — Repost Source of Truth

Repost MUST derive its accounting result from the current source Document state.

### PST-API-15 — Retry Distinction

Retry MUST remain semantically distinct from Repost.

### PST-API-16 — Idempotency Distinction

Idempotency MUST remain semantically distinct from Repost.

### PST-API-17 — Event Boundary

Posting events MUST NOT precede Logical Completion.

### PST-API-18 — Dependency Encapsulation

Dependency management MUST NOT become part of the public Posting operation contract.

### PST-API-19 — Runtime Identity

Runtime object identity MUST NOT become durable Posting identity.

### PST-API-20 — Determinism

Equivalent relevant Posting inputs MUST produce equivalent semantic Posting results.

### PST-API-21 — Phase 5 Boundary

The Public Posting API MUST NOT bypass Phase 5 Persistence or Storage Provider boundaries.

## 36. Explicit Non-Goals

This step does NOT define:

concrete Python classes;
exact method signatures;
concrete request DTOs;
concrete result classes;
concrete exception classes;
HTTP or RPC transport;
dependency injection mechanism;
service locator;
concrete Posting Engine implementation;
concrete Posting Context implementation;
concrete Posting Handler implementation;
concrete MovementSet implementation;
concrete Register Service implementation;
transaction API;
rollback API;
Persistence Scope API;
Storage Provider API;
event transport;
outbox;
retry scheduler;
idempotency-key mechanism;
reconciliation mechanism;
recovery mechanism;
database schema;
serialization format.

## 37. Step 6 Acceptance Criteria

Step 6 is complete when:

A public Posting boundary is explicitly defined.
Post, Unpost, and Repost are defined as distinct operations.
The source Document is explicitly identified.
The source Document remains the semantic source of truth.
Posting Request semantics are defined.
Public Posting inputs are distinguished from internal Posting Context state.
Posting Context ownership remains with Posting Engine.
Posting Handler remains behind the Posting Engine boundary.
MovementSet generation remains behind the Posting boundary.
Register movement submission is not exposed as an alternative standard Posting path.
Public Posting success is tied to Logical Completion.
Public failure semantics are defined.
Indeterminate Outcome is explicitly preserved.
Document persistence and Posting remain distinct operations.
Unpost has explicit public semantics.
Repost has explicit public semantics.
Repost is explicitly based on current Document state.
Retry and Repost are distinguished.
Idempotency and Repost are distinguished.
Posting event ordering remains after Logical Completion.
Persistence and Storage Provider mechanisms remain hidden.
Dependency management remains behind the Posting integration boundary.
Runtime object identity is excluded from durable Posting identity.
Deterministic Posting semantics are preserved.
No concrete implementation API is prescribed prematurely.
Phase 5 Persistence and Storage Provider boundaries remain intact.

## 38. Architecture Review

Architecture Review: PENDING

Review result:

Blockers: TBD
Major architectural issues: TBD
Minor alignment issues: TBD
Required alignments: TBD

This section is intentionally left pending until the architecture review of Step 6 is completed.

## 39. Related Architecture

docs/architecture/posting/POSTING_ARCHITECTURE.md
docs/architecture/posting/POSTING_LIFECYCLE.md
docs/architecture/posting/POSTING_HANDLERS.md
docs/architecture/posting/POSTING_CONTEXT.md
docs/architecture/posting/MOVEMENT_VALIDATION.md
docs/architecture/posting/REGISTER_POSTING_CONTRACTS.md
docs/implementation/PHASE_6_STEP_2_POSTING_SEMANTIC_CONTRACT.md
docs/implementation/PHASE_6_STEP_3_POSTING_LIFECYCLE_AND_VALIDATION.md
docs/implementation/PHASE_6_STEP_4_REGISTER_MOVEMENT_CONTRACT.md
docs/implementation/PHASE_6_STEP_5_CONSISTENCY_FAILURE_AND_REPOSTING.md
Phase 5 Persistence Architecture
Phase 5 Storage Provider Boundary

## 40. Step 6 Status

Step 6 — Public Posting API

Status: DRAFT