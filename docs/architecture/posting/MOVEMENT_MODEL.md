# MOVEMENT_MODEL.md

## 1. Purpose

This document defines the movement model used by the Posting Architecture.

A movement represents an atomic accounting fact generated during document posting.

The movement model serves as the foundation for register updates, totals calculation, dependency tracking, auditing, and reposting.

---

## 2. Core Concepts

### 2.1 Movement

A Movement is the smallest accounting unit produced by the posting process.

A movement represents a single change in a register state.

Examples:

* receipt of goods into inventory;
* issue of goods from inventory;
* creation of a receivable;
* registration of a price value.

A movement is not a document row.

A movement is not a storage record.

A movement is an accounting fact.

---

### 2.2 MovementSet

A MovementSet is the complete result of a posting operation.

A single document posting generates exactly one MovementSet.

A MovementSet may contain movements belonging to multiple registers.

Example:

Sales Invoice

→ Inventory Register movements

→ Sales Register movements

→ Receivable Register movements

---

## 3. Architectural Principles

### 3.1 Document as Source of Truth

Documents are authoritative.

Movements are derived from documents.

Movements must never be edited manually.

Reposting always regenerates movements from the document.

---

### 3.2 One Document → One MovementSet

Each posting operation produces exactly one MovementSet.

---

### 3.3 Immutable After Generation

Generated MovementSets become immutable after posting handler execution.

Subsequent stages must not modify movement contents.

---

### 3.4 Register-Agnostic Design

The Movement model is independent of register types.

Register-specific requirements are defined by register posting contracts.

---

## 4. Movement Structure

### 4.1 Identity

movement_id

Type:

ULID

Purpose:

Global movement identity.

---

### 4.2 Source Document

document_id

Type:

ULID

Purpose:

Reference to the document that generated the movement.

---

### 4.3 Target Register

register_id

Type:

Register Reference

Purpose:

Reference to the destination register.

---

### 4.4 Period

period

Type:

DateTime

Purpose:

Accounting timestamp of the movement.

Period is independent from document creation time.

---

### 4.5 Movement Type

movement_type

Type:

MovementType

Possible values:

* INCOME
* EXPENSE

Used primarily by accumulation registers.

May be absent for register types that do not require direction.

---

### 4.6 Dimensions

dimensions

Type:

Dictionary<String, Value>

Purpose:

Defines the accounting context of the movement.

Examples:

* product
* warehouse
* organization
* customer

Dimensions identify the slice of data affected by the movement.

---

### 4.7 Resources

resources

Type:

Dictionary<String, Value>

Purpose:

Defines measurable values modified by the movement.

Examples:

* quantity
* amount
* vat_amount

Resources represent the values being accumulated or recorded.

---

### 4.8 Attributes

attributes

Type:

Dictionary<String, Value>

Purpose:

Additional information associated with the movement.

Examples:

* project
* department
* manager

Attributes provide analytical information without affecting aggregation logic.

---

### 4.9 Source Line

line_id

Type:

ULID | null

Purpose:

Optional reference to the document line that generated the movement.

This field improves:

- traceability;
- auditing;
- diagnostics;
- cost calculation;
- movement analysis.

The field is optional because some movements may be generated at document level or by system operations rather than individual document lines.

---

## 5. Conceptual Model

Movement

* movement_id
* document_id
* register_id
* period
* movement_type
* dimensions
* resources
* attributes

---

## 6. MovementSet Structure

### 6.1 Identity

MovementSet is associated with a single document.

document_id

Type:

ULID

---

### 6.2 Collection of Movements

movements

Type:

List<Movement>

Contains all movements generated during posting.

---

### 6.3 Internal Organization

Implementations may organize movements by register.

Example:

Inventory Register

→ movement[]

Sales Register

→ movement[]

Receivable Register

→ movement[]

This organization is an implementation detail and not part of the public model.

---

## 7. Movement Lifecycle

### 7.1 Creation

Posting Handler

→ Movement Builder

→ Mutable MovementSet

---

### 7.2 Freeze

Mutable MovementSet

→ Immutable MovementSet

---

### 7.3 Validation

Movement Validator verifies:

* required dimensions;
* required resources;
* data types;
* register contracts.

---

### 7.4 Persistence

Validated movements are persisted through the storage layer.

---

### 7.5 Removal

Movements may be removed only through:

* unposting;
* reposting;
* maintenance operations.

---

## 8. Relationship with Register Contracts

The Movement model defines a universal movement structure.

Register-specific rules are defined by Register Posting Contracts.

Examples:

* accumulation registers require movement_type;
* information registers may omit movement_type;
* accounting registers may require account dimensions.

---

## 9. Relationship with Dependency Tracking

Every movement maintains a link to its source document.

This allows the platform to:

* identify affected documents;
* build dependency chains;
* perform selective reposting;
* restore accounting consistency.

---

## 10. Related Documents

* POSTING_ARCHITECTURE.md
* POSTING_HANDLERS.md
* MOVEMENT_VALIDATION.md
* REGISTER_POSTING_CONTRACTS.md
* POSTING_DEPENDENCIES.md
