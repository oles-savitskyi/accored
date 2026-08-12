# POSTING_ARCHITECTURE.md

## 1. Purpose

Purpose of the Posting Architecture.

Definition of posting as the transformation of business objects into register movements.

---

## 2. Scope and Responsibilities

Responsibilities:

* document posting;
* document unposting;
* document reposting;
* movement generation;
* movement validation;
* dependency management;
* posting events.

Out of scope:

* document storage;
* register storage;
* totals calculation;
* query execution;
* reporting.

---

## 3. Architectural Principles

### 3.1 Metadata-Driven Design

Posting behavior is defined by metadata and implemented through posting handlers.

### 3.2 Document as Source of Truth

Documents are the authoritative source of accounting state.

Movements are derived artifacts.

### 3.3 Posting Result = MovementSet

Posting handlers never write directly to registers.

The result of posting is always a MovementSet.

### 3.4 Atomicity

Posting is an atomic operation.

### 3.5 Contract-Based Validation

All generated movements must satisfy register posting contracts.

### 3.6 Dependency Awareness

Posting must support dependency tracking and reposting.

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

Document

→ Posting Engine

→ Posting Handler

→ MovementSet

→ Validation

→ Storage Layer

→ Totals Engine

---

## 4.3 Posting Engine

### Purpose

Posting Engine is the central orchestration component of the Posting Architecture.

Its responsibility is to coordinate the posting process and enforce the posting lifecycle.

Posting Engine does not contain business-specific accounting logic.

Business logic is delegated to Posting Handlers.

---

### Responsibilities

Posting Engine is responsible for:

* creating PostingContext;
* resolving Posting Handlers;
* executing posting operations;
* managing posting lifecycle execution;
* coordinating movement validation;
* coordinating movement persistence;
* coordinating totals updates;
* managing consistency restoration workflows;
* publishing posting events.

Posting Engine acts as the entry point for all posting operations.

---

### Non-Responsibilities

Posting Engine must not:

* contain document-specific business rules;
* generate movements directly;
* perform register-specific validation;
* implement accounting logic;
* modify metadata definitions.

These responsibilities belong to Posting Handlers, Movement Validators, Register Contracts, and Metadata Architecture.

---

### Posting Flow

Conceptually:

Document

→ Posting Engine

→ Posting Context

→ Posting Handler

→ MovementSet

→ Movement Validator

→ Storage Layer

→ Totals Update

→ Event Publication

---

### Handler Resolution

Posting Engine resolves Posting Handlers using metadata definitions.

Example:

Document Metadata

* posting_handler = sales_invoice.posting

Runtime Resolution

sales_invoice.posting

→ SalesInvoicePostingHandler

The resolution mechanism is implementation-specific.

---

### Context Creation

Posting Engine creates a PostingContext instance for each posting operation.

The context provides controlled access to platform services and runtime information.

The PostingContext exists only during posting execution.

---

### Validation Coordination

Posting Engine coordinates movement validation after MovementSet generation.

Validation is performed by Movement Validators.

Posting Engine must not perform validation directly.

---

### Persistence Coordination

Posting Engine coordinates movement persistence through the Storage Architecture.

The persistence implementation is outside the scope of Posting Architecture.

---

### Transaction Coordination

Posting Engine coordinates transaction boundaries.

Typical flow:

Begin Transaction

→ Execute Posting

→ Validate Movements

→ Persist Movements

→ Update Totals

→ Commit Transaction

In case of failure:

Rollback Transaction

---

### Event Publication

Posting Engine publishes posting events after successful transaction completion.

Examples:

* DocumentPosted
* DocumentUnposted
* DocumentReposted

Events must never be published before a successful commit.

---

### Dependency Integration

Posting Engine integrates with the Dependency Management subsystem.

After successful posting, the engine may:

* update dependency information;
* mark dependent objects as DIRTY;
* initiate consistency restoration workflows.

Dependency analysis itself remains the responsibility of the Dependency subsystem.

---

### Architectural Position

Posting Engine is the orchestration layer of the Posting Architecture.

It coordinates posting execution but delegates specialized responsibilities to dedicated components.

Conceptually:

Posting Engine

```
↓
```

Posting Context

```
↓
```

Posting Handler

```
↓
```

Movement Validator

```
↓
```

Storage Layer

```
↓
```

Event Publisher

The Posting Engine is the only component that understands the complete posting lifecycle.

---


## 5. Integration with Other Subsystems

### 5.1 Metadata Architecture

### 5.2 Runtime Architecture

### 5.3 Object Architecture

### 5.4 Storage Architecture

### 5.5 Register Architecture

---

## 6. Posting Lifecycle Overview

Summary of posting lifecycle.

Reference:

* POSTING_LIFECYCLE.md

---

## 7. Movement Model Overview

Summary of Movement and MovementSet concepts.

Reference:

* MOVEMENT_MODEL.md

---

## 8. Validation Overview

Summary of validation strategy.

Reference:

* MOVEMENT_VALIDATION.md

---

## 9. Dependency Management Overview

Summary of dependency graph model.

Reference:

* POSTING_DEPENDENCIES.md

---

## 10. Events Overview

Summary of posting-related events.

Reference:

* POSTING_EVENTS.md

---

## 11. Related Documents

* POSTING_LIFECYCLE.md
* POSTING_CONTEXT.md
* POSTING_HANDLERS.md
* MOVEMENT_MODEL.md
* MOVEMENT_VALIDATION.md
* REGISTER_POSTING_CONTRACTS.md
* POSTING_DEPENDENCIES.md
* POSTING_EVENTS.md
