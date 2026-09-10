# POSTING_ARCHITECTURE.md

## 1. Purpose

The Posting Architecture defines how business objects are transformed into validated accounting movements and how the resulting accounting effects participate in the platform persistence and dependency model.

Posting is responsible for:

* executing posting business logic;
* generating `MovementSet` instances;
* validating generated movements against Register Posting Contracts;
* coordinating the publication of the resulting accounting facts through the appropriate platform boundaries;
* integrating posting with dependency management and posting events.

Posting does not define or prescribe the physical persistence or transaction mechanism.

---

## 2. Scope and Responsibilities

Responsibilities:

* document posting;
* document unposting;
* document reposting;
* movement generation;
* movement validation;
* coordination of movement persistence;
* coordination with Register Architecture;
* dependency management;
* posting events.

Out of scope:

* physical document storage;
* physical register storage;
* storage-provider implementation;
* physical transaction mechanisms;
* database isolation levels;
* retry policy;
* generic query execution;
* reporting.

Posting Architecture defines the semantic posting lifecycle and its integration boundaries. Physical persistence and transaction mechanisms belong to Storage and Persistence Architecture.

---

## 3. Architectural Principles

### 3.1 Metadata-Driven Design

Posting behavior is defined by metadata and implemented through posting handlers.

### 3.2 Document as Source of Truth

Documents are the authoritative source of their business state.

Movements represent the accounting facts derived from that state.

### 3.3 Posting Result = MovementSet

Posting Handlers never write directly to registers or storage.

The result of posting is always a `MovementSet`.

A `MovementSet` is a posting-domain result and is not itself a persistence entity.

### 3.4 Consistency Through Persistence Scope

Posting does not imply a universal physical transaction.

When a posting operation requires multiple persistent effects to become consistent as one logical result, those effects participate in an appropriate Persistence Scope.

A Persistence Scope is a logical consistency boundary defined by Persistence Architecture.

Depending on the operation, the required persistent result may include:

* the updated persistent object state;
* newly generated register facts;
* required derived register state;
* other persistent state required by the operation's consistency contract.

The physical mechanism used to satisfy the Persistence Scope is implementation-specific.

### 3.5 Contract-Based Validation

All generated movements must satisfy the applicable Register Posting Contracts before they are accepted for persistence.

### 3.6 Dependency Awareness

Posting must support dependency tracking and consistency restoration.

Posting may cause dependent state to become invalid or require subsequent consistency restoration.

### 3.7 Separation of Business Logic and Persistence

Posting Handlers contain accounting business logic.

Posting Handlers do not perform:

* persistence;
* transaction management;
* totals maintenance;
* dependency orchestration.

Persistence and consistency coordination are handled by the appropriate platform/application boundaries.

---

## 4. High-Level Architecture

### 4.1 Core Components

* Posting Engine
* Posting Context
* Posting Handler
* Movement Builder
* Movement Validator
* Dependency Graph
* Event Publisher

### 4.2 Architecture Diagram

Conceptually:

```text
Document
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
Application / Posting Coordination
    ↓
Persistence Scope
    ├── Object Persistence
    ├── Register Fact Persistence
    └── Required Derived State
```

The Persistence Scope is not a Posting-specific transaction object.

It represents the logical consistency boundary required by the operation.

Storage Providers remain below the persistence boundary and provide the physical mechanisms used to store persistent state.

---

## 4.3 Posting Engine

### Purpose

Posting Engine is the central orchestration component of the Posting Architecture.

Its responsibility is to coordinate the semantic posting lifecycle and enforce the posting process.

Posting Engine does not contain business-specific accounting logic.

Business logic is delegated to Posting Handlers.

---

### Responsibilities

Posting Engine is responsible for:

* creating `PostingContext`;
* resolving Posting Handlers;
* executing posting operations;
* managing posting lifecycle execution;
* coordinating movement validation;
* coordinating the handoff of validated posting results to persistence coordination;
* coordinating consistency-related integration with other subsystems;
* managing consistency restoration workflows;
* publishing posting events after successful logical completion.

Posting Engine acts as the entry point for posting operations.

The exact persistence and consistency mechanism used after posting validation is defined outside the Posting Architecture.

---

### Non-Responsibilities

Posting Engine must not:

* contain document-specific business rules;
* generate movements directly;
* perform register-specific validation;
* implement accounting logic;
* modify metadata definitions;
* define physical transaction mechanisms;
* require a universal `begin`, `commit`, or `rollback` API;
* define database isolation levels;
* implement provider-specific persistence behavior.

These responsibilities belong to Posting Handlers, Movement Validators, Register Contracts, Persistence Architecture, and Storage Architecture.

---

### Posting Flow

Conceptually:

```text
Document
    ↓
Posting Engine
    ↓
Posting Context
    ↓
Posting Handler
    ↓
MovementSet
    ↓
Movement Validator
    ↓
Validated Posting Result
    ↓
Persistence / Application Coordination
    ↓
Required Persistent Result
    ↓
Logical Completion
    ↓
Posting Events
```

The persistence coordination step may involve a Persistence Scope when the operation requires multiple persistent effects to satisfy one logical consistency requirement.

---

### Handler Resolution

Posting Engine resolves Posting Handlers using metadata definitions.

Example:

```text
Document Metadata

posting_handler = sales_invoice.posting

Runtime Resolution

sales_invoice.posting
        ↓
SalesInvoicePostingHandler
```

The resolution mechanism is implementation-specific.

---

### Context Creation

Posting Engine creates a `PostingContext` instance for each posting operation.

The context provides controlled access to platform services and runtime information.

The `PostingContext` exists only during posting execution.

---

### Validation Coordination

Posting Engine coordinates movement validation after `MovementSet` generation.

Validation is performed by Movement Validators.

Posting Engine must not perform register-specific validation directly.

---

### Persistence Coordination

Posting Engine coordinates the handoff of validated posting results to the persistence/application boundary.

Posting Architecture does not prescribe how validated movements are physically persisted.

The persistence boundary may coordinate:

* persistent object state;
* register fact persistence;
* required derived state.

Where these effects must satisfy one logical consistency requirement, they participate in an appropriate Persistence Scope.

The persistence mechanism may differ between platform editions and Storage Provider implementations without changing Posting semantics.

---

### Consistency Coordination

Posting must distinguish between:

1. the generation of accounting facts;
2. the persistence of those facts;
3. the consistency requirements applicable to the resulting persistent state.

A successful `MovementSet` generation does not by itself mean that posting has successfully completed.

Posting is considered successfully completed only when the required persistent result for the operation has been successfully established according to its consistency contract.

The consistency contract may require joint publication of multiple persistent effects.

For example:

```text
Posted Object State
        +
Register Movements
        +
Required Derived State
        ↓
Required Persistent Result
```

Whether these effects are implemented using a database transaction, filesystem coordination, journal/recovery mechanism, or another mechanism is outside the Posting Architecture.

---

### Event Publication

Posting events are published only after successful logical completion of the posting operation.

Examples:

* `DocumentPosted`
* `DocumentUnposted`
* `DocumentReposted`

Events must not be published while the required persistent result is known to be incomplete.

Event publication is therefore tied to successful logical completion rather than to the existence of a specific physical `commit()` operation.

The physical persistence mechanism may expose a commit operation internally, but Posting Architecture does not require or expose such an API.

---

### Dependency Integration

Posting Engine integrates with the Dependency Management subsystem.

After successful logical completion, the engine may:

* update dependency information;
* mark dependent objects as `DIRTY`;
* initiate consistency restoration workflows.

Dependency analysis itself remains the responsibility of the Dependency subsystem.

Dependency restoration may occur as part of the required consistency workflow or as a subsequent operation, depending on the applicable dependency contract.

---

### Failure Semantics

A posting operation may fail at different stages:

```text
Posting Handler
    ↓
Movement Validation
    ↓
Persistence Coordination
    ↓
Required Persistent Result
    ↓
Logical Completion
```

Failure before persistence completion must not be reported as successful posting.

If the persistence layer cannot determine whether the required persistent result was established, the outcome is indeterminate and must not be silently interpreted as success.

Recovery and retry policy are higher-level concerns and are not defined by Posting Architecture.

---

### Architectural Position

Posting Engine is the orchestration layer of the Posting Architecture.

It coordinates posting execution but delegates specialized responsibilities to dedicated components.

Conceptually:

```text
Posting Engine
      ↓
Posting Context
      ↓
Posting Handler
      ↓
Movement Validator
      ↓
Validated Posting Result
      ↓
Persistence / Application Coordination
      ↓
Persistence Scope
      ↓
Required Persistent Result
```

The Posting Engine understands the complete semantic posting lifecycle.

It does not own the physical transaction mechanism.

---

## 5. Integration with Other Subsystems

### 5.1 Metadata Architecture

Posting behavior is resolved from metadata-defined posting configuration.

Metadata determines which Posting Handler is associated with a business object and provides the definitions required for posting execution.

### 5.2 Runtime Architecture

Posting executes inside the Runtime environment and receives a controlled `PostingContext`.

Runtime provides access to the services required by Posting Handlers without exposing persistence implementation details.

### 5.3 Object Architecture

Posting operates on business objects and their current business state.

The persistent representation of an object is separate from its runtime representation.

### 5.4 Storage Architecture

Posting does not access Storage Providers directly.

Validated posting results cross the Persistence boundary before reaching physical storage.

Storage Providers provide physical storage mechanisms and do not perform posting logic.

### 5.5 Register Architecture

Posting generates `MovementSet` instances containing accounting movements.

Movements are validated against Register Posting Contracts before they are accepted by Register persistence.

Registers remain responsible for storing and organizing accounting facts.

Balances and turnovers are derived from register movements according to Register Architecture.

---

## 6. Posting Lifecycle Overview

The semantic posting lifecycle consists of:

```text
Receive Posting Request
        ↓
Resolve Posting Handler
        ↓
Create Posting Context
        ↓
Execute Posting Handler
        ↓
Generate MovementSet
        ↓
Validate Movements
        ↓
Coordinate Required Persistent Result
        ↓
Logical Completion
        ↓
Publish Posting Events
        ↓
Update Dependency State / Trigger Restoration
```

The lifecycle does not prescribe a physical transaction sequence.

The exact persistence mechanism is determined by Persistence and Storage Architecture.

Reference:

* `POSTING_LIFECYCLE.md`

---

## 7. Movement Model Overview

The `Movement` model defines the atomic accounting fact generated during posting.

A `MovementSet` represents the complete posting result for one posting operation.

`MovementSet` is a posting-domain concept and is not a persistence entity.

Validated movements become register facts through the Register and Persistence boundaries.

Reference:

* `MOVEMENT_MODEL.md`

---

## 8. Validation Overview

Movement validation ensures that generated movements satisfy the applicable Register Posting Contracts and other posting-level invariants.

Validation occurs before the movements are accepted for persistence.

Reference:

* `MOVEMENT_VALIDATION.md`

---

## 9. Dependency Management Overview

Posting participates in the Dependency Management model.

Posting may change the state of objects or register-derived state on which other objects depend.

After successful logical completion, dependency information may be updated and dependent objects may be marked for consistency restoration.

Reference:

* `POSTING_DEPENDENCIES.md`

---

## 10. Events Overview

Posting events describe successfully completed posting operations and provide integration points for other platform subsystems.

Events are published only after the required persistent result has been successfully established.

Reference:

* `POSTING_EVENTS.md`

---

## 11. Related Documents

* `POSTING_LIFECYCLE.md`
* `POSTING_CONTEXT.md`
* `POSTING_HANDLERS.md`
* `MOVEMENT_MODEL.md`
* `MOVEMENT_VALIDATION.md`
* `REGISTER_POSTING_CONTRACTS.md`
* `POSTING_DEPENDENCIES.md`
* `POSTING_EVENTS.md`
* `PHASE_5_STORAGE_AND_PERSISTENCE_BOUNDARY.md`
* `PHASE_5_PERSISTENCE_CONTRACTS.md`
* `PHASE_5_PERSISTENCE_API_MATRIX.md`
* `PHASE_5_PERSISTENCE_CONTRACT_API.md`
* `PHASE_5_PERSISTENCE_CONTRACT_CONCRETE_API.md`
