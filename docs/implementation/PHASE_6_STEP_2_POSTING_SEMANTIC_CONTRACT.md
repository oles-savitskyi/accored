# PHASE_6_STEP_2_POSTING_SEMANTIC_CONTRACT.md

# Phase 6 — Step 2: Posting Semantic Contract

## 1. Purpose

This document defines the semantic contract of Posting within Phase 6.

The purpose of this document is to consolidate the existing Posting Architecture into one normative semantic contract for operational posting.

This document defines:

* the semantic meaning of Posting;
* the relationship between a business object and its accounting effects;
* the semantic role of `MovementSet`;
* the relationship between Posting Handlers and Register Posting Contracts;
* source document traceability;
* deterministic posting semantics;
* successful and failed Posting semantics;
* atomicity and persistence-scope semantics;
* unposting and reposting semantics;
* posting-related consistency and event semantics;
* normative Posting invariants.

This document does not introduce a parallel Posting Architecture.

It operationalizes the existing architecture defined by:

* `POSTING_ARCHITECTURE.md`;
* `POSTING_LIFECYCLE.md`;
* `POSTING_HANDLERS.md`;
* `POSTING_CONTEXT.md`;
* `MOVEMENT_MODEL.md`;
* `MOVEMENT_VALIDATION.md`;
* `REGISTER_POSTING_CONTRACTS.md`;
* `POSTING_DEPENDENCIES.md`;
* `POSTING_EVENTS.md`.

---

# 2. Relationship with Existing Posting Architecture

Phase 6 Step 2 does not redefine the architectural components introduced by the existing Posting Architecture.

The existing architecture already establishes:

* Posting as the process of transforming a business object into register movements and applying accounting effects;
* Posting Engine as the central orchestration component;
* Posting Context as the controlled runtime environment for Posting Handlers;
* Posting Handler as the owner of document-specific posting logic;
* MovementSet as the complete result of a posting operation;
* Movement Validator as the validation boundary;
* Register Posting Contract as the integration boundary with Register Architecture;
* Persistence Scope as the logical consistency boundary;
* dependency integration;
* post-success event publication.

Step 2 defines the semantic contract connecting these components.

---

# 3. Posting Semantic Definition

Posting is an explicit accounting operation that transforms the semantic state of a business object into register movements and applies the resulting accounting effects to the system.

Conceptually:

```text
Business Object
      ↓
Posting
      ↓
Accounting Effects
      ↓
Register Facts
```

Posting is distinct from document persistence.

Saving or persisting a document does not imply Posting.

Posting does not replace ordinary document persistence.

Therefore:

```text
Document Persistence
    ≠
Posting
```

A document may be persisted without being posted when its lifecycle permits such a state.

---

# 4. Document as Source of Truth

The business document is the authoritative source of its business state.

Movements are derived accounting facts.

Therefore:

```text
Document State
      ↓
Posting
      ↓
Movements
```

and not:

```text
Movements
      ↓
Document State
```

Generated movements must not become an alternative editable representation of document business state.

Movements must not be manually edited as a substitute for changing the source document and reposting it.

---

# 5. Posting Input

The semantic input to Posting is a business object that is eligible for posting.

The object must:

* exist;
* be postable according to its lifecycle and metadata;
* satisfy required document-level business validation;
* provide the business state required by its Posting Handler.

Posting operates on the semantic business object.

Posting must not depend directly on:

* Storage Provider implementations;
* physical storage structures;
* database-specific APIs;
* persistent-object representation details.

Persistence and runtime boundaries established by Phase 5 remain intact.

---

# 6. Posting Transformation

The core semantic transformation is:

```text
Business Object State
        ↓
Posting Handler
        ↓
MovementSet
```

The Posting Handler determines which accounting facts are produced by the current business object state.

The Posting Engine orchestrates execution of that transformation.

The Posting Engine does not contain document-specific accounting logic.

---

# 7. MovementSet Semantic Contract

A `MovementSet` is the complete result of one Posting operation.

The following invariant applies:

> One Posting operation produces exactly one complete MovementSet.

Conceptually:

```text
One Document
      ↓
One Posting Operation
      ↓
One MovementSet
```

A MovementSet may contain movements belonging to multiple registers.

For example:

```text
Sales Document
      ↓
MovementSet
   ├── Resource Register movements
   ├── Settlement Register movements
   └── other applicable register movements
```

The internal organization of movements within the MovementSet is an implementation detail.

The semantic contract is the completeness of the result.

---

# 8. Complete Result Invariant

A Posting Handler must produce a complete MovementSet for one Posting operation.

The handler must not expose partially generated accounting results as the Posting result.

Conceptually:

```text
Generate all required movements
            ↓
      Complete MovementSet
            ↓
          Freeze
            ↓
        Validation
```

The Posting Handler must not persist individual movements directly.

The Posting Handler must not progressively apply accounting effects to registers while generating the MovementSet.

---

# 9. Movement Semantics

A Movement represents an atomic accounting fact generated by Posting.

A Movement is:

* an accounting fact;
* associated with a target register;
* associated with its source document;
* associated with an accounting period;
* described by dimensions, resources and attributes as required;
* optionally associated with a source document line.

A Movement is not:

* a document row;
* a runtime object;
* a persistent object representation;
* a storage-provider record.

The Movement model remains register-agnostic.

Register-specific requirements are defined through Register Posting Contracts.

---

# 10. Source Document Identity

Every movement generated by Posting must retain explicit source-document identity.

Conceptually:

```text
Movement
    │
    └── source document identity
```

The source identity must be durable and independent of runtime object identity.

A runtime Python object reference, memory address, or equivalent execution-local identity must never be used as the durable identity of a movement source.

The source document identity is required for:

* traceability;
* auditing;
* movement ownership;
* unposting;
* reposting;
* dependency analysis;
* consistency restoration.

---

# 11. Posting Handler Responsibility

The Posting Handler owns document-specific accounting semantics.

Its semantic responsibility is:

```text
Business Object
      ↓
Document-specific accounting rules
      ↓
MovementSet
```

A Posting Handler may:

* inspect document data;
* inspect document tabular sections;
* perform document-specific business validation;
* use approved Posting Context capabilities;
* generate dimensions;
* generate resources;
* generate attributes;
* generate movements.

A Posting Handler must not:

* persist movements;
* persist documents;
* manage transactions;
* update totals;
* manage dependencies;
* manipulate physical storage;
* access storage-provider internals;
* modify metadata.

The Posting Handler answers:

> What accounting facts does this business object produce?

It does not answer:

> How are those facts persisted?

---

# 12. Register Posting Contract

Register Posting Contracts define whether generated movements are valid for their target registers.

The semantic relationship is:

```text
Posting Handler
      ↓
MovementSet
      ↓
Movement Validation
      ↓
Register Posting Contract
      ↓
Accepted / Rejected
```

Posting is register-agnostic.

The Posting Engine operates on the universal Movement model.

Register-specific requirements belong to Register Architecture and its posting contracts.

Therefore:

* Posting Handler defines accounting intent;
* Register Posting Contract defines register acceptance requirements;
* Movement Validator enforces those requirements.

---

# 13. Validation Semantics

Posting validation consists of two conceptually distinct concerns.

## 13.1 Business Validation

Business validation verifies whether the business object is legally and semantically eligible for Posting.

Examples may include:

* invalid business state;
* forbidden operation;
* insufficient stock;
* closed accounting period;
* violated business rule.

Business-specific validation belongs to the Posting/business layer.

---

## 13.2 Movement Validation

Movement Validation verifies whether the generated MovementSet satisfies structural and register requirements.

Validation includes, where applicable:

* movement identity;
* source document identity;
* register identity;
* period;
* dimensions;
* resources;
* attributes;
* movement type;
* platform types;
* Register Posting Contracts.

The two validation concerns must remain separate.

A document may be business-valid while producing an invalid MovementSet.

A structurally valid MovementSet may still require business validation before Posting is allowed to complete.

---

# 14. Validation Before Persistence

No generated movement may be persisted before successful MovementSet validation.

The semantic order is:

```text
Business Validation
        ↓
Movement Generation
        ↓
MovementSet
        ↓
Movement Validation
        ↓
Persistence / Application
```

Invalid movements must never become persisted accounting facts.

---

# 15. Deterministic Posting

Posting execution must be deterministic.

Given the same:

* document state;

* relevant metadata;

* relevant reference state;

* applicable posting context;

* accounting time/environment required by the contract;

the Posting Handler must produce the same semantic MovementSet.

Formally:

```text
Same Relevant Input State

        ↓

Same Posting Handler

        ↓

Same Semantic MovementSet
```

Nondeterministic behavior must not be introduced by:

* runtime object identity;

* storage layout;

* storage provider behavior;

* arbitrary collection ordering;

* uncontrolled system time;

* uncontrolled external state.

Where current time is a legitimate posting input, it must be supplied through the Posting Context time boundary.

The semantic contract does not define the concrete contents or implementation of Posting Context. Those details are deferred to the Posting Context and lifecycle/API steps.


---

# 16. Posting Success

Posting is successful only when the complete posting operation has successfully completed its required semantic stages.

At minimum:

```text
Document Validation
        ↓
Movement Generation
        ↓
MovementSet Validation
        ↓
Required Persistent Application
        ↓
Logical Completion
```

A successful Posting means that the accounting effects represented by the complete MovementSet have been accepted and applied according to the applicable persistence and register contracts.

Successful Handler execution alone does not constitute successful Posting.

Successful MovementSet validation alone does not constitute successful Posting.

---

# 17. Posting Failure

A Posting operation is unsuccessful if any mandatory stage fails.

Failure may originate from:

* document/business validation;
* Posting Handler execution;
* MovementSet validation;
* Register Posting Contract violation;
* persistence coordination;
* register fact application;
* consistency coordination;
* other explicitly defined Posting lifecycle constraints.

A failed Posting must not be reported as successful.

---

# 18. Atomicity

Posting is an atomic logical operation.

The semantic invariant is:

> Either all required accounting effects of the Posting operation become part of the required persistent result, or no partial accounting result is exposed as a successful Posting.

Conceptually:

```text
Posting
   │
   ├── success → complete accounting result
   │
   └── failure → no successful partial result
```

Posting Architecture does not prescribe a universal physical transaction API.

Physical transaction and isolation mechanisms remain implementation concerns of Persistence and Storage Architecture.

---

# 19. Persistence Scope

When Posting requires multiple persistent effects to remain consistent as one logical result, those effects participate in the appropriate Persistence Scope.

The required persistent result may include:

* updated persistent document state;
* generated register facts;
* required derived register state;
* other persistent state required by the operation's consistency contract.

The Persistence Scope is a logical consistency boundary.

It is not a Posting-specific transaction abstraction.

Storage Providers remain below the persistence boundary.

Posting must therefore not depend on:

* database transaction APIs;
* filesystem transaction behavior;
* provider-specific commit mechanisms;
* database isolation levels.

---

# 20. Posting Lifecycle Semantics

Posting participates in the existing Posting Lifecycle.

The normative lifecycle is:

```text
Document
    ↓
Validation
    ↓
Begin consistency / persistence scope
    ↓
Remove existing movements where required
    ↓
Create Posting Context
    ↓
Execute Posting Handler
    ↓
Generate MovementSet
    ↓
Validate MovementSet
    ↓
Persist movements
    ↓
Update required totals / derived state
    ↓
Complete persistence scope
    ↓
Publish success events
```

The exact physical transaction implementation is outside the Posting Architecture.

The semantic requirement is that the resulting persistent state satisfies the Posting consistency contract.

---

# 21. Unposting Semantics

Unposting removes the accounting effects previously generated by a posted business object.

Conceptually:

```text
Posted Object
      ↓
Unposting
      ↓
Existing Accounting Effects Removed
      ↓
Object becomes UNPOSTED
```

Unposting must operate on the accounting effects belonging to the source object.

It must not modify unrelated movements.

A successful Unposting removes the object's applicable posting effects according to the register and persistence contracts.

---

# 22. Reposting Semantics

Reposting rebuilds accounting effects for an already posted object.

The canonical semantic model is:

```text
Current Document State
        ↓
      Unpost
        ↓
 Remove Previous Effects
        ↓
       Post
        ↓
Generate New MovementSet
        ↓
Apply New Accounting Effects
```

Therefore:

> Reposting is not an incremental edit of existing movements.

It is a rebuilding of accounting effects from the current document state.

This preserves the document-as-source-of-truth principle.

---

# 23. Reposting Consistency

After successful Reposting:

```text
Current Document State
        ↔
Current Generated Accounting Effects
```

The resulting accounting effects must correspond to the current semantic state of the document.

Old movements that no longer correspond to the current document state must not remain as active posting effects of that document.

---

# 24. Dependency Semantics

Posting participates in the platform dependency model.

Movements provide the register-centric facts through which dependencies may be detected.

Posting Handlers do not directly construct or maintain dependency graph edges.

The Dependency subsystem is responsible for:

* dependency detection;
* dependency tracking;
* consistency state;
* consistency restoration workflows.

The purpose of dependency management is preservation and restoration of accounting consistency.

Reposting is one possible consistency-restoration mechanism.

---

# 25. Event Semantics

Posting events represent successfully completed posting-related operations.

Events are published only after successful logical completion of the corresponding operation.

Core events include:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

Events must not be emitted for failed operations.

Event data must represent the completed operation and must remain immutable after publication.

Event publication must not expose a posting operation as successful before all required accounting effects have been successfully established according to the applicable consistency contract.

The semantic contract does not prescribe a physical transaction or commit mechanism.

The exact delivery mechanism is implementation-specific.

---

# 26. Accounting Effect Ownership

The following ownership model is normative:

```text
Posting Engine
    → posting orchestration

Posting Context
    → controlled runtime capabilities

Posting Handler
    → document-specific accounting semantics

MovementSet
    → complete posting result

Movement Validator
    → movement validation

Register Posting Contract
    → register acceptance semantics

Movement Service / Register Services
    → movement management and persistence

Register
    → authoritative accounting facts

Totals Engine
    → derived register state
```

No component may silently absorb another component's responsibility.

---

# 27. Phase 5 Boundary Preservation

Posting must consume the persistence and runtime boundaries established by Phase 5.

Posting must not:

* bypass Persistence Contracts;
* access Storage Providers directly;
* treat Persistent Objects as Runtime Objects;
* use runtime object identity as durable persistence identity;
* reconstruct durable state through storage-specific assumptions;
* introduce persistence responsibilities into Posting Handlers.

Posting is an upper-layer consumer of the existing persistence/runtime architecture.

No Phase 5 boundary is reopened by Step 2.

---

# 28. Semantic Invariants

The following invariants are normative for Phase 6.

### PST-SEM-01

Posting is an explicit accounting operation and is distinct from document persistence.

### PST-SEM-02

The business document is the source of truth for the business state from which accounting effects are derived.

### PST-SEM-03

One Posting operation produces exactly one complete MovementSet.

### PST-SEM-04

A Posting Handler must produce a complete MovementSet for one Posting operation.

### PST-SEM-05

Generated MovementSets become immutable after Posting Handler execution.

### PST-SEM-06

Every generated movement must contain explicit durable source document identity.

### PST-SEM-07

Runtime object identity must not be used as durable movement source identity.

### PST-SEM-08

Posting Handlers own document-specific accounting semantics.

### PST-SEM-09

Posting Handlers must not perform persistence, transaction management, totals maintenance, or dependency management.

### PST-SEM-10

All generated movements must satisfy the applicable Register Posting Contracts before persistence.

### PST-SEM-11

No invalid movement may reach persistent register storage.

### PST-SEM-12

Posting is deterministic for equivalent relevant semantic input state.

### PST-SEM-13

Successful Posting requires successful completion of all mandatory posting stages.

### PST-SEM-14

A failed Posting must not be reported as successfully completed.

### PST-SEM-15

Posting must not expose partially applied accounting effects as a successful result.

### PST-SEM-16

When multiple persistent effects form one logical Posting result, they participate in the appropriate Persistence Scope.

### PST-SEM-17

Physical transaction mechanisms remain outside the Posting Architecture contract.

### PST-SEM-18

Unposting removes the applicable accounting effects generated by the source object.

### PST-SEM-19

Reposting rebuilds accounting effects from the current document state.

### PST-SEM-20

Reposting must not rely on manual mutation of existing movements as its primary semantic mechanism.

### PST-SEM-21

Posting Handlers must not directly manage dependency graph state.

### PST-SEM-22

Posting success events are published only after successful logical completion.

### PST-SEM-23

Posting must not bypass Phase 5 persistence, runtime, or storage boundaries.

---

# 29. Explicit Non-Goals

Step 2 does not define:

* Python interfaces;
* concrete Posting Engine classes;
* concrete Posting Handler classes;
* concrete Posting Context APIs;
* concrete Movement or MovementSet Python representations;
* persistence implementation;
* transaction implementation;
* database isolation;
* storage-provider behavior;
* retry policy;
* concurrency control implementation;
* concrete dependency graph algorithms;
* concrete event delivery mechanism;
* Goods Receipt posting logic.

These concerns are handled by later Phase 6 steps or by the existing platform architecture.

---

# 30. Step 2 Acceptance Criteria

Step 2 is complete when all of the following are true:

* [ ] Posting has an explicit semantic definition.
* [ ] Posting is explicitly distinguished from document persistence.
* [ ] Document-as-source-of-truth semantics are fixed.
* [ ] Posting input semantics are defined.
* [ ] MovementSet is defined as the complete result of one Posting operation.
* [ ] Complete MovementSet generation is a Handler invariant.
* [ ] Movement source-document identity is explicitly required.
* [ ] Runtime identity is excluded from durable movement identity.
* [ ] Handler accounting responsibility is explicitly separated from persistence.
* [ ] Register Posting Contract responsibility is explicitly separated from Handler responsibility.
* [ ] Business validation and Movement Validation are explicitly distinguished.
* [ ] Validation-before-persistence semantics are fixed.
* [ ] Deterministic Posting semantics are fixed.
* [ ] Successful Posting semantics are fixed.
* [ ] Failure semantics are fixed.
* [ ] Atomicity semantics are aligned with the existing Persistence Scope model.
* [ ] Unposting semantics are aligned with the existing Posting Lifecycle.
* [ ] Reposting semantics are aligned with the existing architecture.
* [ ] Dependency ownership is explicit.
* [ ] Event publication semantics are explicit.
* [ ] Phase 5 boundaries remain unchanged.
* [ ] No premature Python API or implementation decision is introduced.

---

# 31. Related Architecture

Posting Architecture:

* `docs/architecture/posting/POSTING_ARCHITECTURE.md`
* `docs/architecture/posting/POSTING_LIFECYCLE.md`
* `docs/architecture/posting/POSTING_HANDLERS.md`
* `docs/architecture/posting/POSTING_CONTEXT.md`
* `docs/architecture/posting/MOVEMENT_MODEL.md`
* `docs/architecture/posting/MOVEMENT_VALIDATION.md`
* `docs/architecture/posting/REGISTER_POSTING_CONTRACTS.md`
* `docs/architecture/posting/POSTING_DEPENDENCIES.md`
* `docs/architecture/posting/POSTING_EVENTS.md`

Register Architecture:

* `docs/architecture/register/REGISTER_ARCHITECTURE.md`

Standard Configuration:

* `docs/architecture/standard_configuration/REGISTER_MAPPING.md`

Persistence and Storage Architecture:

* existing Phase 5 Persistence Architecture;
* existing Storage Architecture;
* existing Persistence Scope contracts.

---

# 32. Step 2 Status

**Status: DRAFT — pending Architecture Review**

Step 2 must be reviewed against the existing Posting Architecture and Phase 5 persistence boundaries before being marked CLOSED.
