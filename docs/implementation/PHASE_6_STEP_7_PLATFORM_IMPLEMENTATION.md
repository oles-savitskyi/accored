# Phase 6 — Step 7: Platform Implementation

## 1. Purpose

This step defines the concrete platform implementation boundary for the Posting Architecture established by the previous Phase 6 steps.

The purpose of this step is to translate the approved semantic Posting contracts into concrete platform-level runtime components without introducing document-specific accounting semantics.

Step 7 establishes the implementation architecture for:

* Public Posting API;
* Posting Engine;
* Posting Context;
* Posting Handler resolution;
* Posting Handler invocation;
* Movement;
* MovementSet;
* Movement Validation;
* Register Posting Contract integration;
* Posting Result;
* Posting failure and indeterminate outcome handling;
* persistence/application coordination;
* Posting event boundary;
* runtime dependency wiring.

The implementation defined by this step MUST preserve the semantic contracts established by:

* Posting Architecture;
* Posting Semantic Contract;
* Posting Lifecycle & Validation;
* Register Movement Contract;
* Consistency, Failure & Reposting;
* Public Posting API.

Step 7 MUST NOT introduce Goods Receipt-specific or Inventory-specific posting semantics.

---

## 2. Relationship with Existing Architecture

Step 7 is an implementation step.

The semantic contracts defined by previous steps remain authoritative.

The implementation MUST NOT redefine:

* what Posting means;
* what constitutes Logical Completion;
* Movement semantic meaning;
* Register acceptance semantics;
* persistence consistency semantics;
* Reposting semantics;
* event ordering semantics;
* Phase 5 persistence boundaries.

The implementation exists to execute those semantics.

Conceptually:

```text
Phase 6 Semantic Contracts
            ↓
     Step 7 Implementation
            ↓
     Runtime Posting Pipeline
```

Concrete classes, protocols, dependency injection mechanisms, and runtime composition are introduced here because they are implementation concerns rather than semantic contract concerns.

---

## 3. Platform Posting Boundary

The platform Posting implementation consists of a set of cooperating components.

Conceptually:

```text
Public Posting API
        ↓
Posting Engine
        ↓
Posting Context
        ↓
Posting Handler Resolver
        ↓
Posting Handler
        ↓
MovementSet
        ↓
Movement Validator
        ↓
Register Posting Contract
        ↓
Persistence / Application Coordination
        ↓
Logical Completion
        ↓
Posting Result
        ↓
Posting Events
```

The Posting Engine is the central orchestration component.

The other components have explicit responsibilities and MUST NOT silently absorb responsibilities belonging to other architectural boundaries.

---

## 4. Public Posting API

The Public Posting API is the application-level entry boundary for standard Posting operations.

It provides the public operations:

* Post;
* Unpost;
* Repost.

The concrete input representation MUST preserve explicit source Document identity.

Conceptually:

Post(SourceDocumentReference)
Unpost(SourceDocumentReference)
Repost(SourceDocumentReference)

The notation above is conceptual and does not yet prescribe whether the concrete API accepts:

* a runtime Document instance;
* a persistent Document identity;
* another application-level Document reference representation.

The concrete representation MUST be selected according to the existing runtime and application architecture.

The Public Posting API MUST:

* accept an explicitly identified source Document;
* delegate Posting execution to the Posting Engine;
* expose the semantic outcome of the operation;
* preserve the distinction between Success, Failure, and Indeterminate Outcome;
* avoid implementing document-specific accounting semantics;
* avoid implementing Posting orchestration itself.

The Public Posting API MUST NOT:

* generate Movements;
* resolve Posting Handlers directly;
* construct Posting Contexts;
* perform Movement Validation;
* persist register effects;
* control transactions;
* interact directly with Storage Providers.

---

## 5. Posting Engine

The Posting Engine is the concrete orchestration component responsible for executing the Posting lifecycle.

Conceptually:

```text
PostingEngine
    ├── resolve handler
    ├── create context
    ├── execute handler
    ├── validate MovementSet
    ├── coordinate persistent result
    ├── establish Logical Completion
    └── publish Posting events
```

The Posting Engine owns Posting orchestration.

It MUST:

* receive a valid Posting operation request;
* establish applicable Posting preconditions;
* resolve the Posting Handler;
* create the Posting Context;
* execute the Posting Handler;
* obtain the complete MovementSet;
* invoke Movement Validation;
* coordinate establishment of the Required Persistent Result;
* establish Logical Completion only when all mandatory stages have completed successfully;
* return the appropriate semantic outcome;
* publish Posting events only after Logical Completion.

The Posting Engine MUST NOT own:

* document-specific accounting semantics;
* register-specific business semantics;
* physical transaction implementation;
* Storage Provider behavior;
* database access;
* direct SQL;
* document persistence implementation;
* dependency graph implementation;
* event transport implementation.

The Posting Engine is an orchestrator, not an accounting rule engine.

---

## 6. Posting Operation Boundary

Each invocation of the Posting Engine represents one logical Posting operation.

A Posting operation MUST have:

* an explicitly identified source Document;
* applicable Posting Context inputs;
* a resolved Posting Handler;
* a complete MovementSet;
* validated Movements;
* a required persistent result;
* a final semantic outcome.

The Posting Engine MUST NOT expose an operation as successful before Logical Completion.

The implementation MUST preserve the distinction between:

```text
Operation completed successfully
```

and:

```text
Operation was invoked
```

Invocation alone is not success.

---

## 7. Posting Context

Posting Context is the controlled runtime environment supplied to a Posting Handler.

Conceptually:

```text
PostingContext
    ├── document
    ├── metadata
    ├── services
    ├── user/session context
    └── controlled accounting time/environment inputs
```

The concrete structure MAY differ from this conceptual representation.

The implementation MUST preserve the following properties:

* Posting Context is created by the Posting Engine;
* Posting Context belongs to one Posting operation;
* Posting Context is not a global service locator;
* services exposed through the context are explicit capabilities;
* the Handler cannot control the Posting lifecycle through the Context;
* the Handler cannot commit, rollback, or otherwise control physical transactions;
* the Handler cannot bypass Movement Validation;
* the Handler cannot directly establish persistent register state.

The Posting Context MUST contain only capabilities required by the Posting operation.

Its concrete API MUST remain minimal.

---

## 8. Posting Handler Contract

The Posting Handler is the document-specific accounting implementation.

Conceptually:

```text
PostingHandler
    ↓
post(context)
    ↓
MovementSet
```

The concrete Python representation MAY use a protocol, abstract base class, or another explicit interface mechanism.

The Handler MUST:

* read the source Document;
* apply document-specific posting semantics;
* use allowed Posting Context capabilities;
* generate the complete MovementSet;
* perform applicable business-specific posting validation.

The Handler MUST NOT:

* persist Movements;
* persist Documents;
* control transactions;
* control Persistence Scope;
* update register storage directly;
* manage totals directly;
* publish Posting events;
* manage dependency state directly.

The Handler produces accounting facts.

The Posting Engine remains responsible for orchestration.

---

## 9. Posting Handler Resolution

Posting Handler resolution is a platform responsibility.

The Posting Engine MUST obtain the appropriate Handler through an explicit Handler resolution boundary.

Conceptually:

```text
Source Document
      ↓
Handler Resolver
      ↓
Posting Handler
```

Handler resolution MAY use:

* document type identity;
* metadata identity;
* registered handler configuration;
* another explicit platform-level resolution mechanism.

The concrete resolution mechanism is an implementation concern.

The resolution mechanism MUST NOT require the Posting Handler to discover itself through uncontrolled global state.

Handler resolution failure MUST produce a Posting failure.

---

## 10. Movement Representation

Step 7 introduces the concrete runtime representation of the universal Movement contract.

The concrete Movement representation MUST support the semantic elements established in Step 4:

* movement identity;
* source document identity;
* register identity;
* movement type;
* dimensions;
* resources;
* attributes;
* optional temporal information.

The representation MUST remain register-agnostic.

The Movement implementation MUST NOT contain Inventory-specific fields merely because Inventory is the first Register implementation.

For example, the universal Movement model MUST NOT require:

* warehouse;
* product;
* quantity;
* stock location.

Such semantics belong to Register-specific contracts.

---

## 11. Posting Handler Resolution

Posting Handler resolution is a platform responsibility.

The Posting Engine MUST obtain the appropriate Handler through an explicit Handler resolution boundary.

Conceptually:

Source Document
      ↓
Handler Resolver
      ↓
Posting Handler

The Handler Resolver MAY use:

* document type identity;
* metadata identity;
* registered Handler configuration;
* another explicitly defined platform-level resolution mechanism.

The concrete resolution mechanism is an implementation concern.

Handler resolution MUST be explicit in the Posting Engine dependency graph.

The Handler Resolver MUST NOT require the Posting Handler to discover or register itself through uncontrolled global runtime state.

Metadata-driven resolution, where used, MUST operate through the existing metadata and identity boundaries.

Handler resolution failure MUST produce a Posting failure.

Movement identity MUST be distinct from:

* runtime object identity;
* source Document identity;
* Register identity.

Movement identity exists to identify the accounting fact represented by the Movement.

The implementation MUST NOT use Python object identity as the semantic Movement identity.

The concrete Movement identity mechanism is an implementation concern.

Movement identity MUST NOT introduce nondeterminism into the semantic Posting result.

If the concrete identity representation is regenerated for equivalent Posting operations, the implementation MUST preserve the deterministic semantic identity/equivalence requirements defined by the applicable Posting and persistence architecture.

The concrete strategy for stable or regenerated Movement identity is outside the universal Movement semantic contract unless explicitly required by the applicable persistence boundary.

---

## 12. Source Document Identity

Every Movement generated by Posting MUST contain explicit source Document identity.

The concrete Movement representation MUST therefore expose a semantic source-document reference or equivalent identity value.

The implementation MUST NOT use:

* Python object identity;
* memory address;
* object hash;
* runtime-specific reference identity

as the durable source Document identity.

The source Document identity MUST remain stable across:

* Posting;
* persistence;
* Unposting;
* Reposting;
* runtime reconstruction.

---

## 13. Register Identity

Movement MUST identify the target Register explicitly.

The concrete representation MAY use:

* Register identity;
* Register metadata identity;
* another stable architectural Register reference.

The concrete representation MUST NOT require the universal Movement type to know the internal implementation of a Register.

Register identity identifies the accounting destination.

It does not transfer Register-specific semantics into the universal Movement model.

---

## 14. Movement Type

Movement Type is a semantic description of the accounting effect represented by a Movement.

The universal implementation MUST support a Movement Type without prescribing register-specific meaning.

The concrete set of Movement Type values MUST be defined by the applicable accounting architecture.

Step 7 MUST NOT introduce Goods Receipt or Inventory-specific Movement Type values into the universal Posting implementation unless they are already part of an approved universal domain contract.

---

## 15. Dimensions

The concrete Movement representation MUST support dimensions as defined by the universal Movement contract.

Dimensions identify the accounting aggregation context associated with a Movement.

The implementation MUST allow Register Posting Contracts to define:

* required dimensions;
* optional dimensions;
* allowed dimension identities;
* applicable value constraints.

The universal Movement implementation MUST NOT impose Inventory-specific dimension requirements.

---

## 16. Resources

The concrete Movement representation MUST support resources.

Resources carry quantitative or accumulated accounting values.

The universal implementation MUST support resource identity and resource value without assuming a particular Register.

Concrete resource requirements belong to Register Posting Contracts.

For example, a Register MAY require a quantity resource, but the universal Movement implementation MUST NOT require quantity merely because one Register uses it.

---

## 17. Attributes

The concrete Movement representation MUST support additional descriptive accounting fact data through attributes.

Attributes MUST remain semantically distinct from:

* dimensions;
* resources;
* source Document identity;
* Register identity.

Register-specific contracts MAY define required or optional attributes.

The universal Movement implementation MUST NOT encode document-specific attributes as mandatory universal fields.

---

## 18. Movement Time

Movement temporal information remains optional at the universal Movement level.

The concrete implementation MAY support temporal information.

A Register Posting Contract MAY require a specific temporal value.

The implementation MUST NOT make a temporal field universally mandatory unless that requirement is introduced by the approved universal contract.

The concrete time source MUST be controlled by Posting Context or another explicitly defined Posting input when temporal information participates in deterministic Posting semantics.

Uncontrolled calls to system current time MUST NOT be introduced into Handler logic when they would violate Posting determinism.

---

## 19. MovementSet Representation

Step 7 introduces the concrete representation of MovementSet.

MovementSet represents the complete accounting result generated by one Posting Handler execution.

The implementation MUST enforce:

* association with one Posting operation;
* completeness before validation;
* explicit collection semantics;
* stable iteration semantics where required by deterministic Posting;
* no silent mutation after Handler completion.

Conceptually:

```text
Posting Handler
      ↓
MovementSet
      ↓
Movement Validation
```

MovementSet MUST NOT be treated as a persistence record.

It is the semantic result passed between Posting components before the Required Persistent Result is established.

---

## 20. MovementSet Completeness

The Posting Engine MUST treat MovementSet completeness as a mandatory boundary.

The Handler MUST return a complete MovementSet.

The Posting Engine MUST NOT assume that a partially generated MovementSet represents successful Posting.

The implementation MUST define an explicit boundary after which MovementSet generation is complete.

After that boundary:

* MovementSet contents MUST NOT be silently changed;
* invalid Movements MUST NOT be repaired in place;
* Register-specific corrections MUST NOT be injected by the Posting Engine.

Invalid output is a Posting failure.

---

## 21. Movement Immutability Boundary

The concrete Movement and MovementSet implementation MUST define an explicit semantic immutability boundary.

Once the Handler has completed and returned the MovementSet:

```text
Handler-owned generation
        ↓
Stable semantic result
        ↓
Validation / downstream processing
```

Subsequent platform components MAY inspect and validate the result.

They MUST NOT silently rewrite its accounting semantics.

If a Movement is invalid, the appropriate outcome is validation failure rather than automatic semantic mutation.

The implementation MAY enforce this boundary through concrete Python immutability mechanisms such as immutable value objects, frozen structures, controlled interfaces, or another equivalent mechanism.

The specific Python mechanism is an implementation concern.

The architectural requirement is that downstream components MUST NOT silently alter the semantic accounting result generated by the Handler.

---

## 22. Movement Validation

Movement Validation is a separate platform component.

Conceptually:

```text
MovementSet
      ↓
Movement Validator
      ↓
Validated MovementSet
```

The Validator MUST:

* validate Movement structure;
* validate applicable Register identity;
* validate applicable dimensions;
* validate applicable resources;
* validate applicable attributes;
* validate Movement Type;
* evaluate applicable Register Posting Contract requirements.

The Validator MUST NOT:

* generate accounting facts;
* rewrite invalid Movements;
* implement document-specific posting semantics;
* persist Movements.

Validation failure MUST prevent the Posting operation from establishing a successful Required Persistent Result.

---

## 23. Register Posting Contract Integration

The concrete platform implementation MUST provide an explicit integration boundary between Movement Validation and Register Posting Contracts.

Conceptually:

```text
Movement
    ↓
Generic Movement Validation
    ↓
Register Posting Contract
    ↓
Register Acceptance
```

The Validator MUST obtain the applicable Register Posting Contract through an explicit dependency.

The concrete Register implementation MUST remain responsible for its Register-specific requirements.

The Posting Engine MUST NOT contain Register-specific validation rules.

---

## 24. Register Acceptance Boundary

Register acceptance is represented as a semantic validation/acceptance boundary.

Conceptually:

```text
Generated Movement
      ↓
Validated Movement
      ↓
Register Contract Acceptance
      ↓
Accepted Movement
```

Accepted Movement does not mean persisted Movement.

The concrete implementation MUST preserve the distinction between:

* validation/acceptance;
* establishment of the Required Persistent Result.

This prevents the platform implementation from coupling semantic acceptance to physical persistence.

---

## 25. Persistence / Application Coordination

The Posting Engine MUST coordinate establishment of the Required Persistent Result through an explicit application/persistence boundary.

Conceptually:

```text
Validated Posting Result
        ↓
Persistence / Application Coordinator
        ↓
Required Persistent Result
```

The concrete coordinator MAY integrate:

* Movement persistence;
* replacement of obsolete accounting effects;
* document posting state;
* derived accounting state;
* dependency-related persistent effects.

The coordinator MUST NOT expose physical transaction details to Posting Handlers.

The Posting Engine MUST NOT directly depend on:

* SQL;
* database sessions;
* Storage Providers;
* database transactions;
* filesystem implementation.

The Phase 5 Persistence and Storage boundaries remain authoritative.

---

## 26. Persistence Scope Integration

The concrete Posting implementation MUST integrate with the applicable Persistence Scope boundary where required.

The Posting Engine MAY request that multiple persistent effects participate in one logical consistency boundary.

The implementation MUST NOT redefine Persistence Scope semantics.

The concrete physical mechanism MAY be:

* database transaction;
* another persistence mechanism;
* another consistency implementation.

That mechanism remains outside the Posting Architecture.

Posting depends on the semantic guarantee of the applicable persistence boundary rather than on its physical implementation.

---

## 27. Logical Completion

Logical Completion is the concrete Posting success boundary.

The Posting Engine MUST establish Logical Completion only after:

* Posting Preconditions have passed;
* Handler resolution succeeded;
* Posting Context was created;
* Handler execution completed;
* complete MovementSet was generated;
* MovementSet validation and applicable Register Posting Contract acceptance succeeded;
* Required Persistent Result was established.

Only after this boundary MAY the Posting operation be reported as successful.

Conceptually:

```text
Required Persistent Result
        ↓
Logical Completion
        ↓
Success
```

---

## 28. Posting Result

The concrete platform implementation MUST provide a representation of the semantic Posting outcome.

The result MUST preserve the distinction between:

```text
Success
Failure
Indeterminate
```

Success means Logical Completion was established.

Failure means successful Logical Completion was not established and the operation outcome is known.

Indeterminate means the implementation cannot reliably determine whether the Required Persistent Result was established.

The concrete result representation is an implementation concern.

It MAY use:

* result objects;
* typed outcomes;
* exceptions plus explicit indeterminate handling;
* another explicit representation.

The implementation MUST NOT collapse Indeterminate Outcome into ordinary Failure when that would lose semantic information.

---

## 29. Failure Handling

The Posting Engine MUST classify failures according to the semantic stage at which they occur.

Failures that occur before Logical Completion MUST NOT be reported as successful Posting.

Failures that occur while establishing the Required Persistent Result MUST be classified according to whether the persistent outcome is known or indeterminate.

If the Required Persistent Result cannot be reliably determined, the Posting operation MUST produce an Indeterminate Outcome.

Once Logical Completion has been established, subsequent failures such as event publication failure MUST NOT be converted into a Posting Failure that implies that the Required Persistent Result was not established.

The implementation MUST therefore distinguish:

```text
Known failure before Logical Completion
        ≠
Indeterminate persistent outcome
        ≠
Post-Logical-Completion integration failure
```

The concrete error/result representation is an implementation concern.

---

## 30. Event Boundary

Posting events MUST be emitted only after Logical Completion.

Conceptually:

```text
Logical Completion
        ↓
Posting Event
```

The Posting Engine MUST NOT publish `DocumentPosted` before the Required Persistent Result has been established.

Similarly, Unposting and Reposting events MUST be published only after their corresponding logical operations have completed successfully.

The concrete event transport is outside the scope of this implementation step unless required for platform wiring.

Event publication failure MUST remain semantically distinct from failure to establish the accounting result.

If Logical Completion has already been established, a later event publication failure MUST NOT be represented as proof that the accounting result was not established.

---

## 31. Dependency Boundary

The concrete Posting implementation MAY integrate with dependency state and restoration workflows.

Such integration MUST occur through an explicit boundary.

The Posting Handler MUST NOT directly manage dependency state.

If dependency-related persistent effects form part of the Required Persistent Result, they MUST participate in the applicable consistency boundary.

Concrete dependency mechanisms remain outside the Posting Engine's accounting semantics.

---

## 32. Unposting Implementation Boundary

Step 7 introduces the platform execution boundary for Unposting without defining a new accounting algorithm.

Conceptually:

```text
Unpost Request
      ↓
Posting Engine
      ↓
Identify Existing Posting Effects
      ↓
Coordinate Removal of Applicable Effects
      ↓
Logical Completion
      ↓
DocumentUnposted
```

The implementation MUST preserve the semantic requirement that Unposting removes applicable accounting effects associated with the source Document.

The exact mechanism for identifying and removing obsolete effects is an application/persistence concern.

The Posting Handler MUST NOT directly delete persisted Movements.

---

## 33. Reposting Implementation Boundary

Step 7 introduces the platform orchestration boundary for Reposting.

Conceptually:

```text
Repost Request
      ↓
Current Document State
      ↓
Resolve Handler
      ↓
Generate New MovementSet
      ↓
Validate
      ↓
Establish New Required Persistent Result
      ↓
Logical Completion
      ↓
DocumentReposted
```

Reposting MUST use the current semantic state of the source Document.

The implementation MUST NOT rely on mutating the existing MovementSet as the primary semantic mechanism.

Replacement or removal of obsolete accounting effects belongs to the persistence/application coordination boundary.

---

## 34. Reposting and Determinism

Reposting MUST preserve the deterministic Posting contract.

Equivalent relevant semantic inputs MUST produce equivalent MovementSet semantics.

The implementation MUST NOT introduce nondeterminism through:

* runtime object identity;
* uncontrolled system time;
* arbitrary collection ordering;
* storage-provider behavior;
* uncontrolled external state.

Any required current time MUST enter the Posting operation through a controlled Posting input or Posting Context boundary.

---

## 35. Public API Wiring

The Public Posting API MUST depend on the Posting Engine rather than reimplementing Posting orchestration.

The Public Posting API MUST NOT become the owner of the internal Posting dependency graph or lifecycle orchestration.

Runtime composition MUST establish Posting dependencies through the appropriate application/platform composition boundary.

The concrete dependency injection or composition mechanism is an implementation concern.

---

## 36. Runtime Dependency Graph

The platform implementation SHOULD establish an explicit dependency graph similar to:

```text
Public Posting API
        ↓
Posting Engine
        ├── Document Access
        ├── Handler Resolver
        ├── Context Factory
        ├── Movement Validator
        ├── Register Contract Resolver
        ├── Persistence/Application Coordinator
        └── Event Publisher
```

Each dependency MUST have a defined architectural responsibility.

Global mutable registries, hidden service locators, or implicit runtime lookups MUST NOT be introduced merely for convenience.

Where metadata-driven resolution is required, the resolution boundary MUST remain explicit.

A registry used as explicit configuration or metadata-driven resolution is not itself prohibited.

The prohibited pattern is using a registry as an implicit service locator through which Posting components discover arbitrary runtime services or dependencies outside their declared architectural boundary.

---

## 37. Concrete API Scope

Step 7 permits concrete APIs for:

* Posting Engine;
* Posting Context;
* Posting Handler;
* Handler Resolver;
* Movement;
* MovementSet;
* Movement Validator;
* Register Posting Contract;
* Posting Result;
* Posting Errors;
* Persistence/Application Coordinator;
* Public Posting API.

However, the APIs MUST remain minimal and directly reflect the approved semantic responsibilities.

Concrete APIs MUST NOT introduce unrelated responsibilities merely because they are convenient to expose.

---

## 38. Error Representation

Step 7 MAY introduce concrete Posting error types.

Errors SHOULD preserve:

* semantic failure category;
* source operation;
* relevant source Document identity where available;
* relevant Movement/Register context where available;
* underlying failure information where appropriate.

The implementation MUST preserve Indeterminate Outcome as a distinct semantic condition.

Concrete exception hierarchy is an implementation concern.

The public API MUST NOT require every internal error to become a separate public exception type.

---

## 39. Transaction Boundary

Step 7 MUST NOT introduce transaction control into Posting Handlers.

Posting Engine MAY depend on a consistency/persistence boundary.

Posting Engine MUST NOT require the semantic architecture to expose a universal:

```text
begin()
commit()
rollback()
```

API.

If a physical transaction exists, it is owned by the applicable persistence/application infrastructure.

The Posting implementation depends on the semantic result of that boundary.

---

## 40. Storage Boundary

Posting implementation MUST NOT bypass the Phase 5 Storage Provider boundary.

Posting components MUST NOT directly depend on:

* filesystem operations;
* database drivers;
* SQL;
* storage-provider-specific APIs.

Register and persistence implementations remain responsible for their storage concerns.

The Posting implementation communicates through approved persistence/application boundaries.

---

## 41. Phase 5 Boundary Preservation

Step 7 MUST preserve all Phase 5 architectural boundaries.

In particular:

* runtime state MUST NOT become durable merely because it is present in Posting Context;
* persistent identity MUST remain distinct from runtime identity;
* storage providers MUST remain behind their provider boundary;
* persistence APIs MUST remain explicit;
* unsupported durable state MUST remain explicit;
* materialization boundaries MUST NOT be bypassed;
* infrastructure implementation details MUST NOT leak into domain semantics.

Posting implementation MUST build on Phase 5 rather than replacing or weakening it.

---

## 42. Implementation Ownership Matrix

The concrete platform responsibilities are:

| Component                           | Owns                             | Must Not Own                  |
| ----------------------------------- | -------------------------------- | ----------------------------- |
| Public Posting API                  | application entry boundary       | posting semantics             |
| Posting Engine                      | orchestration                    | document accounting rules     |
| Posting Context                     | controlled capabilities          | lifecycle control             |
| Handler Resolver                    | Handler resolution               | posting execution             |
| Posting Handler                     | document accounting semantics    | persistence                   |
| Movement                            | accounting fact representation   | persistence                   |
| MovementSet                         | complete posting result          | persistence                   |
| Movement Validator                  | movement validation              | movement generation           |
| Register Contract                   | register acceptance requirements | document posting logic        |
| Persistence/Application Coordinator | persistent accounting result     | document accounting semantics |
| Event Publisher                     | event delivery                   | posting success determination |
| Register                            | register semantics               | document-specific posting     |

---

## 43. Platform Posting Flow

The concrete platform flow SHOULD correspond to:

```text
Public Posting API
        ↓
Posting Engine
        ↓
Posting Preconditions
        ↓
Handler Resolution
        ↓
Posting Context Creation
        ↓
Handler Execution
        ↓
Complete MovementSet
        ↓
Movement Validation
        ↓
Register Contract Acceptance
        ↓
Persistence / Application Coordination
        ↓
Required Persistent Result
        ↓
Logical Completion
        ↓
Posting Result
        ↓
Posting Event
```

No stage may silently bypass an earlier mandatory semantic boundary.

---

## 44. Success Invariants

The implementation MUST satisfy:

### PST-IMP-01

Public Posting operations execute through the Posting Engine.

### PST-IMP-02

Posting Engine owns Posting orchestration.

### PST-IMP-03

Posting Context is operation-scoped and controlled.

### PST-IMP-04

Posting Handler owns document-specific accounting semantics.

### PST-IMP-05

Handler does not own persistence or physical transaction control.

### PST-IMP-06

One Posting operation produces one complete MovementSet.

### PST-IMP-07

MovementSet is validated before persistent accounting effects are established.

### PST-IMP-08

Register-specific requirements are enforced through Register Posting Contracts.

### PST-IMP-09

Accepted Movement is not treated as persisted Movement.

### PST-IMP-10

Logical Completion occurs only after the Required Persistent Result is established.

### PST-IMP-11

Success is reported only after Logical Completion.

### PST-IMP-12

Indeterminate Outcome is not silently converted into Failure or Success.

### PST-IMP-13

Posting events are emitted only after Logical Completion.

### PST-IMP-14

Reposting uses the current semantic state of the source Document.

### PST-IMP-15

Posting implementation does not bypass Phase 5 persistence/storage boundaries.

### PST-IMP-16

Universal Movement implementation remains Register-agnostic.

### PST-IMP-17

Step 7 does not introduce Goods Receipt or Inventory-specific accounting semantics.

---

## 45. Failure Invariants

The implementation MUST ensure:

* Handler resolution failure prevents successful Posting;
* Handler failure prevents successful Posting;
* incomplete MovementSet prevents successful Posting;
* Movement validation failure prevents successful Posting;
* Register acceptance failure prevents successful Posting;
* known persistence failure prevents successful Posting;
* unknown persistent outcome produces Indeterminate Outcome;
* event publication failure after Logical Completion does not retroactively invalidate established accounting state;
* invalid Movement is not silently repaired;
* physical transaction failures are not hidden as successful Posting.

---

## 46. Determinism Invariants

The implementation MUST preserve deterministic Posting semantics.

For equivalent relevant inputs:

```text
Document State
+
Metadata
+
Reference State
+
Posting Context Inputs
+
Accounting Time/Environment Inputs
```

the resulting MovementSet MUST be semantically equivalent.

The implementation MUST NOT introduce nondeterminism through:

* runtime memory identity;
* storage layout;
* provider implementation;
* arbitrary collection ordering;
* uncontrolled system time;
* uncontrolled external state.

---

## 47. Testing Strategy

Step 7 implementation MUST be accompanied by tests at multiple architectural boundaries.

### 47.1 Posting Engine Tests

Tests SHOULD cover:

* successful Post;
* Handler resolution failure;
* Handler execution failure;
* Movement validation failure;
* Register acceptance failure;
* persistence failure;
* Indeterminate Outcome;
* event publication boundary;
* Logical Completion boundary.

### 47.2 Posting Context Tests

Tests SHOULD verify:

* operation-scoped lifetime;
* required capabilities;
* absence of transaction-control capability;
* controlled access to services;
* deterministic time/context inputs where applicable.

### 47.3 Handler Contract Tests

Tests SHOULD verify:

* Handler returns MovementSet;
* Handler receives Posting Context;
* Handler cannot directly establish persistence;
* document-specific semantics remain inside Handler.

### 47.4 Movement Tests

Tests SHOULD verify:

* explicit Movement identity;
* explicit source Document identity;
* explicit Register identity;
* dimensions;
* resources;
* attributes;
* optional temporal information;
* immutability boundary.

### 47.5 MovementSet Tests

Tests SHOULD verify:

* complete result semantics;
* deterministic ordering where required;
* immutability after generation;
* association with one Posting operation.

### 47.6 Validation Tests

Tests SHOULD verify:

* structural validation;
* Register Contract validation;
* rejection of invalid Movements;
* no persistence before successful validation.

### 47.7 Reposting Tests

Tests SHOULD verify:

* current Document state is used;
* new MovementSet is generated;
* obsolete effects are handled through the application/persistence boundary;
* failed Reposting does not report success;
* deterministic Reposting.

### 47.8 Public API Tests

Tests SHOULD verify:

* Post;
* Unpost;
* Repost;
* semantic Success;
* semantic Failure;
* semantic Indeterminate Outcome;
* standard application entry boundary.

---

## 48. Integration Test Boundary

Step 7 MAY establish platform-level integration tests using a minimal synthetic Document and synthetic Register.

These tests MUST verify the Posting pipeline without introducing Goods Receipt semantics.

A synthetic vertical flow MAY be:

```text
Synthetic Document
        ↓
Synthetic Posting Handler
        ↓
MovementSet
        ↓
Synthetic Register Contract
        ↓
Persistence/Application Boundary
        ↓
Logical Completion
```

Goods Receipt → Inventory integration remains deferred to Step 8.

---

## 49. Explicit Non-Goals

Step 7 does NOT define:

* Goods Receipt posting rules;
* Inventory posting rules;
* warehouse semantics;
* product semantics;
* quantity semantics;
* Inventory Register schema;
* concrete accounting dimensions for Inventory;
* Inventory-specific Movement Types;
* totals calculation;
* dependency graph implementation;
* physical transaction implementation;
* database schema;
* Storage Provider implementation;
* event transport implementation;
* recovery subsystem;
* retry subsystem;
* idempotency algorithm;
* complete audit subsystem;
* reporting/query architecture.

These concerns belong to later steps or other architectural boundaries.

---

## 50. Relationship with Phase 6 Steps

Step 7 implements the contracts established by:

```text
Step 1 — Posting Architecture Boundary
        ↓
Step 2 — Posting Semantic Contract
        ↓
Step 3 — Posting Lifecycle & Validation
        ↓
Step 4 — Register Movement Contract
        ↓
Step 5 — Consistency, Failure & Reposting
        ↓
Step 6 — Public Posting API
        ↓
Step 7 — Platform Implementation
```

Step 7 MUST NOT redefine the semantic contracts of Steps 1–6.

---

## 51. Step 7 Acceptance Criteria

Step 7 is complete when:

1. concrete Posting Engine boundary is defined;
2. concrete Public Posting API boundary is defined;
3. concrete Posting Context boundary is defined;
4. Posting Handler interface is defined;
5. Handler resolution boundary is defined;
6. concrete Movement representation is defined;
7. concrete MovementSet representation is defined;
8. Movement Validation integration is defined;
9. Register Posting Contract integration is defined;
10. persistence/application coordination boundary is defined;
11. Logical Completion boundary is implemented;
12. Success / Failure / Indeterminate outcomes are represented;
13. event boundary is implemented consistently;
14. Unpost orchestration boundary is defined;
15. Repost orchestration boundary is defined;
16. Phase 5 persistence/storage boundaries remain intact;
17. universal Movement remains Register-agnostic;
18. deterministic Posting semantics remain intact;
19. platform tests cover the mandatory lifecycle and failure boundaries;
20. no Goods Receipt or Inventory-specific posting semantics are introduced.

---

## 52. Architecture Review

**Architecture Review: COMPLETED**

This section is reserved for the architecture review of the Step 7 implementation design.

The review MUST verify:

* consistency with Steps 1–6;
* correct ownership of concrete components;
* absence of semantic leakage between Posting and Register;
* absence of persistence/storage leakage into Posting;
* preservation of Phase 5 boundaries;
* correct Success / Failure / Indeterminate semantics;
* correct Logical Completion boundary;
* correct event boundary;
* deterministic implementation;
* adequate testing boundaries;
* absence of premature Goods Receipt / Inventory semantics.

---

## 53. Related Architecture

* `docs/architecture/posting/POSTING_ARCHITECTURE.md`
* `docs/architecture/posting/POSTING_LIFECYCLE.md`
* `docs/architecture/posting/POSTING_HANDLERS.md`
* `docs/architecture/posting/POSTING_CONTEXT.md`
* `docs/architecture/posting/MOVEMENT_VALIDATION.md`
* `docs/architecture/posting/REGISTER_POSTING_CONTRACTS.md`
* `docs/implementation/PHASE_6_STEP_2_POSTING_SEMANTIC_CONTRACT.md`
* `docs/implementation/PHASE_6_STEP_3_POSTING_LIFECYCLE_AND_VALIDATION.md`
* `docs/implementation/PHASE_6_STEP_4_REGISTER_MOVEMENT_CONTRACT.md`
* `docs/implementation/PHASE_6_STEP_5_CONSISTENCY_FAILURE_AND_REPOSTING.md`
* `docs/implementation/PHASE_6_STEP_6_PUBLIC_POSTING_API.md`
* Phase 5 Persistence Architecture
* Phase 5 Storage Provider Boundary

---

## 54. Step 7 Status

**Step 7 — Platform Implementation**

**Status: APPROVED**

Architecture review is required before implementation begins.
