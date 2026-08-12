# POSTING_DEPENDENCIES.md

## 1. Purpose

This document defines the dependency model used by the Posting Architecture.

The purpose of posting dependencies is to identify relationships between posted objects and to support consistency restoration when accounting data changes.

Posting dependencies are used for:

* impact analysis;
* consistency tracking;
* reposting;
* dependency visualization;
* future cost calculation mechanisms;
* future accounting mechanisms;
* future period closing mechanisms.

The dependency subsystem is not responsible for posting itself.

Its responsibility is to detect and manage accounting dependencies between posted objects.

---

## 2. Architectural Principles

### 2.1 Consistency-Oriented Design

The goal of dependency management is not reposting.

The goal is preservation and restoration of accounting consistency.

Reposting is one possible consistency restoration mechanism.

---

### 2.2 Metadata-Driven Dependencies

Dependencies are derived from metadata and accounting activity.

Dependency rules must not be hardcoded inside Posting Handlers.

---

### 2.3 Register-Centric Model

Dependencies are established through registers.

Dependencies are not modeled as direct document-to-document relationships.

Conceptually:

Posted Object

→ Register

→ Posted Object

---

### 2.4 Explicit Consistency State

A posted object may be:

* CONSISTENT
* DIRTY

Changes affecting accounting consistency must be explicitly tracked.

---

### 2.5 Scalable Design

The dependency model must support:

* selective reposting;
* batch reposting;
* future background processing;
* future distributed execution.

---

## 3. Dependency Model

### 3.1 Posted Object

A Posted Object is any business object that generates movements.

Examples:

* Purchase Invoice
* Sales Invoice
* Goods Transfer
* Payment Receipt

Posted Objects are nodes of the dependency graph.

---

### 3.2 Dependency

A dependency represents potential accounting influence.

Conceptually:

Change(A)

may require

Consistency Restoration(B)

A dependency does not automatically imply incorrect data.

A dependency indicates a possible need for consistency verification or reposting.

---

## 4. Dependency Graph

### 4.1 Definition

Dependency Graph is a directed graph describing influence relationships between posted objects.

Nodes:

* Posted Objects

Edges:

* Dependency Relationships

---

### 4.2 Conceptual Structure

Posted Object

→ Affected Register

→ Dependent Object

Example:

Purchase Invoice

→ Inventory Register

→ Sales Invoice

---

### 4.3 Graph Purpose

The graph is used to:

* locate affected objects;
* determine reposting scope;
* identify consistency violations;
* support future accounting analysis.

---

## 5. Dependency Types

### 5.1 Direct Dependency

A direct dependency exists when one posted object directly influences another.

Example:

Purchase Invoice

→ Sales Invoice

---

### 5.2 Indirect Dependency

An indirect dependency exists when influence propagates through multiple objects.

Example:

Purchase Invoice

→ Sales Invoice

→ Cost Calculation

---

### 5.3 Future Dependency Types

Future versions may introduce:

* aggregation dependencies;
* accounting dependencies;
* calculation dependencies;
* period-closing dependencies.

These extensions must remain compatible with the core dependency model.

---

## 6. Dependency Detection

### 6.1 Detection Responsibility

Dependency detection is performed by the platform.

Posting Handlers must not manage dependencies directly.

---

### 6.2 Detection Sources

Dependencies may be derived from:

* register usage;
* movement relationships;
* metadata definitions;
* accounting analysis services.

---

### 6.3 Handler Independence

Posting Handlers must not:

* create dependency links;
* modify dependency graphs;
* manage consistency states.

Dependency management is a platform responsibility.

---

## 7. Metadata-Driven Dependencies

### 7.1 Register Usage Model

Document metadata defines registers used during posting.

Example:

Purchase Invoice

Uses:

* Inventory Register

Sales Invoice

Uses:

* Inventory Register
* Sales Register

---

### 7.2 Dependency Inference

Dependencies may be inferred from shared register participation.

Example:

Purchase Invoice

→ Inventory Register

Sales Invoice

→ Inventory Register

Potential dependency:

Purchase Invoice

→ Sales Invoice

---

### 7.3 Metadata as Dependency Source

Metadata provides the structural basis for dependency analysis.

Runtime services may provide additional dependency information.

---

## 8. Consistency States

### 8.1 CONSISTENT

The posted object is considered synchronized with current accounting data.

No known dependency violations exist.

---

### 8.2 DIRTY

The posted object may be affected by external changes.

Accounting consistency is not guaranteed.

The object may require reposting.

---

### 8.3 State Transitions

CONSISTENT

→ DIRTY

→ CONSISTENT

State restoration typically occurs through reposting or consistency restoration procedures.

---

## 9. Dirty Object Tracking

### 9.1 Purpose

Dirty tracking identifies objects potentially affected by changes in accounting data.

---

### 9.2 Change Propagation

Example:

Purchase Invoice modified

↓

Inventory Register affected

↓

Sales Invoice marked DIRTY

---

### 9.3 Tracking Scope

Dirty tracking may operate on:

* individual objects;
* groups of objects;
* dependency chains.

Implementation details are platform-specific.

---

## 10. Reposting Strategies

### 10.1 Manual Reposting

A user explicitly initiates reposting.

Example:

Repost Selected Document

---

### 10.2 Batch Reposting

The platform reposts a collection of affected objects.

Example:

Repost All Dirty Objects

---

### 10.3 Background Reposting (Future)

Future versions may support asynchronous consistency restoration.

Background reposting must preserve accounting correctness.

---

## 11. Consistency Restoration

### 11.1 Purpose

Consistency restoration returns affected objects to a consistent state.

---

### 11.2 Restoration Methods

Possible methods:

* reposting;
* recalculation;
* dependency resolution procedures.

The exact mechanism depends on the affected subsystem.

---

### 11.3 Restoration Result

Successful restoration returns the object to:

CONSISTENT

state.

---

## 12. Public Operations

Conceptual operations:

mark_dirty()

Marks an object as potentially inconsistent.

---

find_dependents()

Returns objects affected by a change.

---

repost()

Performs reposting of a posted object.

---

restore_consistency()

Restores accounting consistency for affected objects.

---

## 13. Future Extensions

Future versions may introduce:

* dependency priorities;
* dependency categories;
* sequence-based restoration;
* accounting dependency analysis;
* cost calculation dependency analysis;
* distributed dependency processing.

Future extensions must remain compatible with the core dependency graph model.

---

## 14. Relationship with Other Subsystems

### Posting Architecture

Provides posted objects and movement information.

### Register Architecture

Provides register-level dependency information.

### Runtime Architecture

Provides services required for dependency analysis.

### Storage Architecture

Provides persistence for dependency state information.

---

## 15. Related Documents

* POSTING_ARCHITECTURE.md
* POSTING_LIFECYCLE.md
* POSTING_HANDLERS.md
* POSTING_CONTEXT.md
* MOVEMENT_MODEL.md
* MOVEMENT_VALIDATION.md
* REGISTER_POSTING_CONTRACTS.md
* REGISTER_ARCHITECTURE.md
