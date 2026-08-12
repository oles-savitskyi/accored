# POSTING_CONTEXT.md

## 1. Purpose

This document defines PostingContext and its role within the Posting Architecture.

PostingContext provides a controlled runtime environment for Posting Handlers.

It acts as the integration boundary between business posting logic and platform services.

---

## 2. Architectural Principles

### 2.1 Controlled Access

Posting Handlers access platform functionality exclusively through PostingContext.

Direct access to platform internals is prohibited.

---

### 2.2 Runtime Isolation

Posting Handlers should remain independent from runtime implementation details.

PostingContext shields handlers from changes in Runtime Architecture.

---

### 2.3 Testability

PostingContext enables isolated testing of Posting Handlers.

Mock or test implementations may replace runtime services.

---

### 2.4 Stable Contract

PostingContext represents a stable API for posting logic.

Internal runtime changes must not require handler modifications.

---

## 3. Responsibilities

PostingContext provides access to:

* current document;
* metadata information;
* runtime services;
* user context;
* session context;
* time services;
* transaction information.

PostingContext does not perform posting itself.

---

## 4. Conceptual Structure

PostingContext

* document
* metadata
* services
* user
* session
* clock
* transaction

The exact implementation is platform-specific.

---

## 5. Document Access

Provides access to the document being posted.

Examples:

* document identity;
* document attributes;
* tabular sections;
* document state.

Handlers should obtain document information through PostingContext.

---

## 6. Metadata Access

Provides read-only access to metadata definitions.

Examples:

* document metadata;
* register metadata;
* type metadata;
* semantic definitions.

Metadata modification is prohibited.

---

## 7. Runtime Services

Provides access to platform services required during posting.

Examples:

* register services;
* lookup services;
* reference resolution;
* query services.

Services are exposed through well-defined interfaces.

---

## 8. User Context

Provides information about the current user.

Examples:

* user identity;
* permissions;
* roles.

User context may be used for authorization and business rules.

---

## 9. Session Context

Provides information about the current runtime session.

Examples:

* session identifier;
* execution environment;
* execution mode.

Session information is read-only.

---

## 10. Clock Service

Provides access to platform time.

Examples:

* current timestamp;
* business date;
* accounting period date.

Handlers should not access system clocks directly.

Clock access must be centralized.

---

## 11. Transaction Context

Provides information about the current transaction scope.

Examples:

* transaction identifier;
* transaction state;
* execution scope.

Posting Handlers may inspect transaction information.

Posting Handlers must not control transactions.

---

## 12. Register Access

Posting Handlers may require register information.

Examples:

* current balances;
* register lookups;
* analytical queries.

Register access must be performed through dedicated services exposed by PostingContext.

Direct storage access is prohibited.

---

## 13. Query Access

Posting Handlers may execute platform queries through approved query services.

Query execution must remain independent from storage implementation.

Posting Handlers must not use storage-specific APIs.

---

## 14. Error Reporting

PostingContext may provide mechanisms for:

* warnings;
* diagnostics;
* business validation messages.

Handlers should use platform-provided reporting facilities.

---

## 15. Security Considerations

PostingContext enforces runtime boundaries.

Handlers must not:

* modify metadata;
* bypass permissions;
* access storage internals;
* manipulate runtime state.

---

## 16. Example Conceptual Flow

Document

→ Posting Engine

→ PostingContext

→ Posting Handler

→ MovementSet

The PostingContext remains valid only during posting execution.

---

## 17. Lifecycle

PostingContext is created by Posting Engine.

PostingContext exists during posting execution.

PostingContext is disposed after posting completion.

Handlers must not retain references beyond execution scope.

---

## 18. Future Extensions

Future versions may introduce:

* asynchronous posting context;
* distributed execution context;
* background processing context;
* batch posting context.

These extensions should remain compatible with the core PostingContext contract.

---

## 19. Related Documents

* POSTING_ARCHITECTURE.md
* POSTING_HANDLERS.md
* POSTING_LIFECYCLE.md
* MOVEMENT_MODEL.md
* POSTING_DEPENDENCIES.md
* RUNTIME_CONTEXT.md
* RUNTIME_SERVICES.md
