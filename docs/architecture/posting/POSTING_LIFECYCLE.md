# POSTING_LIFECYCLE.md

## 1. Purpose

This document defines the lifecycle of posting operations.

Posting Lifecycle describes how the platform transforms a business object into persisted register movements.

The lifecycle guarantees:

* consistency;
* validation;
* atomicity;
* traceability.

---

## 2. Architectural Principles

### 2.1 Atomic Operation

Posting is an atomic operation.

Either all posting stages complete successfully or no changes are persisted.

---

### 2.2 Deterministic Execution

The same document state must produce the same MovementSet.

---

### 2.3 Validation Before Persistence

No movement may be persisted before successful validation.

---

### 2.4 Event Publication After Success

Posting events are published only after successful completion of posting.

---

## 3. Posting Lifecycle

Document

→ Validation

→ Begin Transaction

→ Remove Existing Movements

→ Create PostingContext

→ Execute PostingHandler

→ Generate MovementSet

→ Validate MovementSet

→ Persist Movements

→ Update Totals

→ Commit Transaction

→ Publish Events

---

## 4. Post Operation

### 4.1 Preconditions

The object must:

* exist;
* be postable;
* satisfy document-level validation.

---

### 4.2 Execution

Posting generates a MovementSet and persists resulting movements.

---

### 4.3 Result

Document state:

POSTED

---

## 5. Unpost Operation

### 5.1 Purpose

Removes accounting effects of a posted object.

---

### 5.2 Execution

Load Existing Movements

→ Remove Movements

→ Update Totals

→ Commit

---

### 5.3 Result

Document state:

UNPOSTED

---

## 6. Repost Operation

### 6.1 Purpose

Rebuilds movements from the current document state.

---

### 6.2 Execution

Unpost

→ Post

---

### 6.3 Result

Accounting data reflects the latest document contents.

---

## 7. Error Handling

Any failure causes:

Rollback Transaction

Posting must never leave partially applied movements.

---

## 8. Transaction Boundaries

Transaction begins before movement replacement.

Transaction ends after successful persistence and totals update.

---

## 9. Event Publication

Examples:

* DocumentPosted
* DocumentUnposted
* DocumentReposted

Events are published after successful commit.

---

## 10. Related Documents

* POSTING_ARCHITECTURE.md
* POSTING_HANDLERS.md
* POSTING_CONTEXT.md
* MOVEMENT_MODEL.md
* POSTING_EVENTS.md
