# POSTING_HANDLERS.md

## 1. Purpose

This document defines Posting Handlers and their role within the Posting Architecture.

A Posting Handler contains business-specific posting logic and is responsible for transforming a business object into a MovementSet.

Posting Handlers are the primary extension point for accounting logic.

---

## 2. Architectural Principles

### 2.1 Single Responsibility

A Posting Handler is responsible only for movement generation.

A Posting Handler must not perform persistence operations.

A Posting Handler must not update totals.

A Posting Handler must not manage transactions.

---

### 2.2 MovementSet as the Only Result

The only valid result of a Posting Handler is a MovementSet.

Posting Handlers never write directly to registers.

Posting Handlers never write directly to storage.

---

### 2.3 Metadata-Driven Resolution

Posting Handlers are resolved through metadata.

Documents do not directly instantiate posting handlers.

The runtime resolves handlers using metadata definitions.

---

### 2.4 Deterministic Execution

Posting execution should be deterministic.

The same document state and the same environment should produce the same MovementSet.

---

### 2.5 Testability

Posting Handlers should be independently testable.

Business logic should be executable without database access.

---

## 3. Responsibilities

Posting Handlers are responsible for:

* reading document contents;
* reading document tabular sections;
* accessing runtime services through PostingContext;
* generating movements;
* generating movement attributes;
* generating movement resources;
* generating movement dimensions;
* performing business-specific posting checks.

---

## 4. Non-Responsibilities

Posting Handlers must not:

* persist movements;
* persist documents;
* update totals;
* commit transactions;
* rollback transactions;
* execute direct SQL;
* access storage internals;
* modify metadata.

These responsibilities belong to other subsystems.

---

## 5. Handler Lifecycle

Document

→ Posting Engine

→ Posting Context

→ Posting Handler

→ MovementSet

→ Validation

→ Persistence

The Posting Handler participates only in movement generation.

---

## 6. Handler Contract

Conceptual interface:

PostingHandler

post(context)

→ MovementSet

The returned MovementSet becomes the input of the validation stage.

---

## 7. Handler Resolution

Posting Handlers are resolved through metadata.

Example:

Document Metadata

* postable = true
* posting_handler = sales_invoice.posting

Runtime:

sales_invoice.posting

→ SalesInvoicePostingHandler

The resolution mechanism is implementation-specific.

---

## 8. Posting Context Usage

Posting Handlers receive all required runtime access through PostingContext.

Examples:

* document access;
* metadata access;
* register services;
* user context;
* system services;
* clock services.

Handlers should avoid dependencies outside PostingContext.

---

## 9. Movement Generation

Handlers generate movements using MovementBuilder.

Example process:

Document

→ Read document data

→ Build movements

→ Add movements to MovementSet

→ Return MovementSet

Handlers should not manually interact with storage structures.

---

## 10. Business Validation

Posting Handlers may perform business-specific validation.

Examples:

* stock availability checks;
* closed period checks;
* account consistency checks;
* mandatory business rules.

Business validation is distinct from Movement Validation.

Movement Validation verifies structural correctness.

Business Validation verifies business correctness.

---

## 11. Error Handling

Posting Handlers may raise posting exceptions.

Examples:

* insufficient stock;
* invalid business state;
* forbidden operation;
* closed accounting period.

The Posting Engine is responsible for handling posting failures.

---

## 12. Dependency Awareness

Posting Handlers may generate movements that affect other posted documents.

Handlers do not manage dependencies directly.

Dependency tracking is handled by the Posting Dependency subsystem.

---

## 13. Performance Considerations

Handlers should:

* minimize external calls;
* avoid repeated data retrieval;
* avoid unnecessary allocations;
* generate movements efficiently.

Optimization must not compromise determinism or correctness.

---

## 14. Future Extensions

Future versions may support:

* asynchronous posting;
* distributed posting execution;
* batch posting;
* parallel posting pipelines.

These capabilities must remain transparent to Posting Handlers.

---

## 15. Related Documents

* POSTING_ARCHITECTURE.md
* POSTING_CONTEXT.md
* POSTING_LIFECYCLE.md
* MOVEMENT_MODEL.md
* MOVEMENT_VALIDATION.md
* POSTING_DEPENDENCIES.md
