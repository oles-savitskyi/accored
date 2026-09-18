# Phase 6 — Posting Architecture Definition

## 1. Status

**Phase:** 6
**Name:** Posting
**Status:** Architecture Definition — Draft
**Previous phase:** Phase 5 — Complete
**Baseline:** `origin/main`

Phase 6 introduces the first operational accounting behavior of AcCoreD.

Its purpose is to connect operational documents with the Posting Architecture and produce register movements.

---

## 2. Objective

The objective of Phase 6 is to make an operational document capable of producing accounting register movements through an explicit posting lifecycle.

The primary vertical slice is:

```text
Goods Receipt
      ↓
Posting
      ↓
Posting Context
      ↓
Register Movement
      ↓
Inventory
```

This is the point at which AcCoreD transitions from a metadata-driven application framework toward an accounting platform.

---

## 3. Architectural Goal

Phase 6 establishes the platform-level posting mechanism independently of a particular register.

The platform must provide the infrastructure necessary to:

* initiate posting;
* validate posting;
* create a posting context;
* resolve the posting handler;
* generate register movements;
* associate movements with their target registers;
* persist the resulting movements;
* represent posting success or failure;
* and define reposting semantics.

The standard configuration then consumes this infrastructure by implementing posting for **Goods Receipt → Inventory**.

---

# 4. Scope

## 4.1 Platform Scope

Phase 6 introduces:

1. Posting Context;
2. posting lifecycle;
3. posting handler infrastructure;
4. posting validation;
5. movement generation;
6. register movement interface;
7. posting failure semantics;
8. reposting semantics for the implemented scenario.

These are platform capabilities.

They must not be implemented as Goods Receipt-specific mechanisms.

---

## 4.2 Standard Configuration Scope

The standard configuration extends Goods Receipt with posting behavior.

For the initial vertical slice:

```text
Goods Receipt
      ↓
      Posting
      ↓
Inventory Register Movement
```

A successfully posted Goods Receipt produces Inventory register movements representing the received quantity facts.

---

## 4.3 Explicit Non-Goals

Phase 6 does not attempt to implement a complete accounting posting engine.

The following are outside the initial scope unless explicitly added by a later ADR:

* arbitrary multi-register accounting;
* generic posting DSL;
* complex dependency graphs between posting handlers;
* period closing;
* accounting adjustments;
* sophisticated reversal strategies;
* historical reposting;
* batch posting;
* background/asynchronous posting;
* distributed transaction processing;
* full accounting ledger semantics;
* optimization of large-scale movement generation.

The architecture must nevertheless avoid preventing these capabilities in future phases.

---

# 5. Relationship to Existing Posting Architecture

AcCoreD already has a Posting Architecture.

Phase 6 therefore treats the existing posting concepts and boundaries as architectural input.

The task is to make those concepts operational.

The implementation must answer:

* how a document enters the posting lifecycle;
* how its posting handler is selected;
* what information the handler receives;
* how movements are produced;
* how movements are associated with registers;
* how posting state is represented;
* how posting failure affects document and register state;
* and how reposting behaves.

Phase 6 must not duplicate posting concepts merely because a new implementation layer is being introduced.

---

# 6. Core Architectural Model

The central abstraction is:

```text
Operational Document
        │
        │ post
        ▼
 Posting Lifecycle
        │
        ▼
 Posting Context
        │
        ▼
 Posting Handler
        │
        │ generate
        ▼
 Register Movements
        │
        ▼
 Register
```

The Posting Handler is responsible for translating the semantic content of an operational document into register facts.

The handler must not directly manipulate physical storage.

---

# 7. Posting Context

Posting Context represents the controlled environment in which posting takes place.

It provides the posting handler with the information and capabilities required to generate movements without exposing unrelated infrastructure.

At minimum, the architecture must define whether the context provides:

* the source document;
* posting identity;
* posting date/time;
* access to required runtime information;
* movement creation;
* register resolution;
* validation facilities;
* and transaction/consistency boundaries.

The exact API is deliberately deferred until the semantic contract is approved.

---

# 8. Posting Handler

A Posting Handler represents the posting behavior of an operational document type.

Conceptually:

```text
Document
    │
    ▼
Posting Handler
    │
    ▼
Posting Context
    │
    ▼
Movement(s)
```

The handler owns **posting semantics**.

It does not own:

* physical storage;
* transaction implementation;
* persistence mechanics;
* runtime object construction;
* register storage internals.

The handler should express *what accounting facts the document produces*, not *how those facts are physically stored*.

---

# 9. Movement Generation

Movement generation is an explicit operation.

A posting handler must produce register movements through the register movement interface.

The architectural flow is:

```text
Document semantic state
        ↓
Posting Handler
        ↓
Movement specification
        ↓
Register Movement
        ↓
Target Register
```

Movement generation must not be implemented as direct mutation of register internals.

---

# 10. Register Movement Boundary

A Register Movement is the boundary between posting logic and register state.

The movement interface must provide enough information to represent a register fact while remaining independent of a concrete register implementation.

At minimum, the architecture must preserve:

* source/document identity;
* target register identity;
* movement dimensions required by the target register;
* quantity/value facts required by the register;
* posting context required for traceability;
* and movement lifecycle semantics.

The concrete Inventory register determines the exact domain fields of its movement.

---

# 11. Inventory Vertical Slice

The first standard implementation is Inventory.

For Goods Receipt, posting must produce quantity facts in the Inventory register.

Conceptually:

```text
Goods Receipt
    │
    ├── item
    ├── quantity
    └── posting date
          │
          ▼
   Posting Handler
          │
          ▼
 Inventory Movement
          │
          ├── item
          ├── quantity
          └── source document
          │
          ▼
      Inventory
```

The Inventory register becomes the first consumer proving that the platform posting infrastructure works end-to-end.

---

# 12. Posting Lifecycle

Phase 6 introduces an explicit posting lifecycle.

At minimum the lifecycle must distinguish:

```text
Unposted
   │
   │ post
   ▼
Posting
   │
   ├── validation failure ──► Failed / remains unposted
   │
   ├── posting failure ─────► Failed / consistency-defined state
   │
   └── success ─────────────► Posted
```

The exact state model must be established before implementation.

In particular, the architecture must define whether `Posting` is an observable persistent state or an internal lifecycle state.

---

# 13. Posting Validation

Validation occurs before register movements are committed.

Validation must determine whether the document is eligible for posting.

For the Goods Receipt vertical slice, validation must include at least the invariants required to safely generate Inventory quantity facts.

Examples include:

* required document data is present;
* quantities are valid;
* required register dimensions are available;
* the document is in a postable lifecycle state;
* and the posting operation is not violating the defined reposting policy.

Validation failure must be explicit.

It must not be represented as an empty set of movements.

---

# 14. Posting Atomicity

Posting is a cross-boundary operation.

At minimum it involves:

```text
Document
   +
Posting Handler
   +
Register Movements
   +
Register
```

Therefore Phase 6 must define an atomicity boundary.

The intended invariant is:

> A successful posting must not leave the system with only a partial set of movements for that posting operation.

Likewise:

> A failed posting must not silently leave behind movements that appear to represent a successful posting.

The concrete transaction mechanism is an implementation decision and must not be assumed prematurely.

---

# 15. Posting Failure Semantics

Posting failures must be classified explicitly.

At minimum:

### Validation failure

The document is not eligible for posting.

Expected semantic result:

```text
document remains unposted
no committed movements
explicit posting error
```

### Handler failure

Posting logic cannot produce the required movements.

Expected semantic result:

```text
posting does not succeed
no partial successful posting is exposed
explicit error
```

### Persistence/register failure

Movement generation succeeded semantically, but durable registration failed.

Expected semantic result:

```text
posting does not become successfully posted
partial durable state must be prevented or explicitly recovered
```

The exact recovery semantics must be defined before implementation.

---

# 16. Reposting

Reposting is part of the Phase 6 contract.

For the implemented Goods Receipt scenario, the architecture must define what happens when a document that has already been posted is posted again.

The minimum question is:

```text
Posted document
      ↓
    repost
      ↓
replace existing posting?
reject?
reverse + repost?
```

Phase 6 does not require a universal reposting strategy for every future document type.

It does require one explicit, tested policy for Goods Receipt.

The policy must prevent duplicate Inventory facts.

---

# 17. Idempotency

Posting must be designed so that repeated execution cannot accidentally create duplicate register facts.

For the initial implementation:

```text
same document
+
same posting state
+
same semantic data
        ↓
same effective register result
```

The exact mechanism—replacement, identity-based movement ownership, rejection, reversal, or another strategy—is an architectural decision that must be recorded separately.

---

# 18. Document / Register Relationship

The register must be able to determine which posting produced a movement.

Therefore register movements require explicit source identity.

Conceptually:

```text
Movement
   │
   └── source document identity
```

This is necessary for:

* traceability;
* reposting;
* duplicate prevention;
* future reversal;
* diagnostics.

The source identity must not depend on an in-memory object reference.

---

# 19. Persistence Relationship

Phase 5 provides the persistence foundation consumed by Phase 6.

Posting must use persistence through explicit contracts.

The posting architecture must not depend directly on:

* filesystem paths;
* concrete storage providers;
* serialization details;
* persistent object implementation details.

The dependency direction remains:

```text
Posting
   ↓
Persistence Contract
   ↓
Storage Provider
```

rather than:

```text
Posting
   ↓
Filesystem
```

---

# 20. Runtime Relationship

Posting operates on live runtime objects but must distinguish runtime state from durable posting state.

In particular:

* posting does not make arbitrary runtime state durable;
* runtime object identity is not the register movement identity;
* a runtime object reference must not be used as durable movement ownership;
* posting state that must survive process termination belongs to the appropriate durable representation.

Phase 6 must therefore reuse the identity and state ownership rules established in Phase 5.

---

# 21. Domain Relationship

Posting is an accounting behavior attached to operational documents.

The domain defines the semantic meaning of the document.

The posting infrastructure translates that meaning into register facts.

Therefore:

```text
Domain semantics
      ↓
Posting behavior
      ↓
Register facts
```

Posting must not redefine the domain model merely to simplify movement persistence.

---

# 22. Architecture Boundaries

Phase 6 establishes the following boundaries:

```text
┌─────────────────────────────┐
│ Operational Document        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Posting Lifecycle           │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Posting Context              │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Posting Handler              │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Register Movement Interface  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Inventory Register           │
└─────────────────────────────┘
```

Persistence remains an infrastructure dependency rather than part of the posting semantic chain.

---

# 23. Proposed Phase 6 Step Decomposition

The following decomposition is provisional.

## Step 1 — Posting Architecture Boundary

Define:

* posting responsibility;
* ownership;
* posting lifecycle boundary;
* relationship to operational documents;
* relationship to existing Posting Architecture.

**No implementation yet.**

---

## Step 2 — Posting Semantic Contract

Define:

* posting operation;
* validation;
* successful posting;
* failed posting;
* posting context semantics;
* movement generation;
* lifecycle semantics.

---

## Step 3 — Register Movement Contract

Define:

* movement identity;
* source document identity;
* target register;
* movement dimensions;
* quantity/value semantics;
* movement ownership and lifecycle.

---

## Step 4 — Posting Consistency and Failure Model

Define:

* atomicity;
* transaction boundary;
* validation failures;
* handler failures;
* persistence failures;
* partial completion;
* retry;
* idempotency;
* reposting.

---

## Step 5 — Platform Posting API

Define the concrete public interfaces for:

* posting;
* posting context;
* posting handlers;
* movement creation;
* register movement access.

---

## Step 6 — Platform Posting Implementation

Implement the platform infrastructure against the accepted contracts.

---

## Step 7 — Goods Receipt Posting

Implement:

```text
Goods Receipt
      ↓
Posting Handler
      ↓
Inventory Movement
```

---

## Step 8 — Reposting and Lifecycle Completion

Implement and validate the selected Goods Receipt reposting policy.

---

## Step 9 — Full Vertical Slice Validation

Validate:

```text
Goods Receipt
      ↓
Posting
      ↓
Posting Context
      ↓
Register Movement
      ↓
Inventory
```

including success and failure scenarios.

---

# 24. Architectural Deliverables

The Phase 6 documentation should include, at minimum:

* `PHASE_6_ARCHITECTURE.md`;
* Posting semantic contract;
* Posting lifecycle/state model;
* Register Movement contract;
* Posting consistency/failure matrix;
* Posting API contract;
* ADRs for decisions that materially constrain implementation.

Existing Posting Architecture documentation should be amended only where Phase 6 introduces an operational refinement or resolves an existing architectural gap.

---

# 25. Phase 6 Acceptance Criteria

Phase 6 is complete when:

1. a document can be posted;
2. posting context is available;
3. posting produces register movements;
4. movements are associated with the correct register;
5. posting failures are handled according to the defined failure contract;
6. reposting behavior is explicitly defined and implemented for Goods Receipt;
7. Inventory receives the correct quantity facts;
8. the complete Goods Receipt → Posting → Posting Context → Register Movement → Inventory vertical slice passes.

---

# 26. Architectural Quality Gate

Phase 6 architecture is considered ready for implementation only when:

* Posting ownership is explicit;
* Posting Context semantics are defined;
* Posting Handler responsibility is defined;
* Register Movement boundary is defined;
* document-to-movement identity is defined;
* lifecycle semantics are defined;
* validation semantics are defined;
* atomicity requirements are defined;
* failure semantics are defined;
* reposting semantics are defined for Goods Receipt;
* persistence remains behind its existing Phase 5 boundary;
* runtime and durable state remain distinct;
* Inventory movement semantics are defined;
* the public API can be derived from the semantic contracts;
* and no unresolved architectural contradiction remains.

---

# 27. Phase 6 Architectural Principle

The central architectural rule of Phase 6 is:

> **Posting translates operational document semantics into explicit register facts through a controlled posting context and an explicit register movement boundary.**

Posting is therefore neither persistence nor register storage.

It is the **accounting transformation between an operational document and register facts**.

---

# 28. Current Decision

Phase 6 capability is fixed:

> **Posting**

The primary implementation target is fixed:

> **Goods Receipt → Inventory**

The architectural direction is fixed:

```text
Operational Document
        ↓
      Posting
        ↓
 Posting Context
        ↓
 Posting Handler
        ↓
 Register Movement
        ↓
     Inventory
```

The detailed contracts, lifecycle semantics, consistency model, reposting policy, and public API remain to be defined in subsequent architectural steps.
