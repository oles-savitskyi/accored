# Implementation Strategy

**Project:** AcCoreD
**Stage:** Standard Edition — Design & Implementation Planning
**Status:** Draft
**Architecture Baseline:** `architecture-core-3.0`

---

## 1. Purpose

This document defines the implementation strategy for AcCoreD following completion of the core architecture cycle.

The architecture baseline `architecture-core-3.0` defines the structural and behavioral principles of the platform.

The purpose of this document is different.

It defines **how the architecture will be transformed into a working software system**.

The implementation strategy establishes:

* what should be implemented first;
* how Platform and Standard Configuration are developed;
* how implementation dependencies are managed;
* how architectural assumptions are validated through working software;
* how the first working release is defined;
* how implementation progress is measured;
* how the project avoids premature optimization and uncontrolled feature expansion.

This document is therefore the transition point between:

```text
Architecture Design
        ↓
Implementation Strategy
        ↓
Repository Structure
        ↓
Implementation Roadmap
        ↓
Working Software
```

---

# 2. Scope

This strategy covers implementation of:

* AcCoreD Platform;
* Standard Configuration;
* metadata and configuration runtime;
* catalogs;
* documents;
* registers;
* posting;
* valuation;
* reporting;
* processings;
* security;
* integration capabilities required by the first working releases.

It does not redefine the architecture.

Architectural changes discovered during implementation must be handled through the established architecture governance process and documented separately.

---

# 3. Implementation Objectives

The implementation process has five primary objectives.

### 3.1 Architectural Fidelity

The implementation must preserve the principles established by `architecture-core-3.0`.

Implementation convenience must not silently introduce architectural coupling that contradicts the baseline.

---

### 3.2 Executable Architecture

Architecture must be validated through working software.

A component is not considered sufficiently validated merely because:

* its classes are defined;
* its interfaces compile;
* its documentation exists;
* its unit tests pass in isolation.

Important architectural assumptions must be demonstrated through executable vertical slices.

---

### 3.3 Platform / Configuration Separation

AcCoreD Platform and Standard Configuration must remain separate implementation concerns.

The Platform provides generic capabilities.

The Standard Configuration consumes those capabilities through metadata and configuration definitions.

The Standard Configuration must not become a collection of platform-specific hard-coded implementations.

---

### 3.4 Incremental Delivery

Implementation proceeds through small, complete increments.

Each increment should produce a system that is more functional than the previous one.

The project should avoid long periods in which large amounts of infrastructure are implemented without a working end-to-end scenario.

---

### 3.5 Sustainable Complexity

Implementation should favor understandable and maintainable solutions.

The first implementation is not required to solve every possible scalability, distribution, or extensibility problem.

Complexity should be introduced when justified by:

* a concrete requirement;
* an architectural constraint;
* measured performance characteristics;
* a demonstrated need for extensibility.

---

# 4. Core Implementation Principles

## 4.1 Build Capabilities Before Consuming Them

Platform capabilities must normally be implemented before they are extensively consumed by Standard Configuration.

For example:

```text
Catalog Runtime
      ↓
Catalog Definition
      ↓
Assortment
```

rather than:

```text
Hard-coded Assortment
```

Similarly:

```text
Document Runtime
      ↓
Posting Integration
      ↓
Document Definition
      ↓
Goods Receipt
```

rather than implementing a special-purpose Goods Receipt subsystem.

This principle ensures that Standard Configuration validates the Platform rather than replacing it.

---

## 4.2 Implement Vertical Slices

The primary implementation unit should be a **vertical slice**.

A vertical slice crosses the relevant architectural layers and produces observable behavior.

For example:

```text
Metadata
   ↓
Runtime
   ↓
Storage
   ↓
Business Object
   ↓
Posting
   ↓
Register Movement
   ↓
Totals
   ↓
Query
```

A vertical slice is preferred over implementing many horizontal infrastructure layers without an executable scenario.

---

## 4.3 Prefer Generic Runtime Over Object-Specific Code

When implementing a Standard Configuration object, the default question should be:

> What generic Platform capability is missing?

rather than:

> What special code should be written for this object?

If several configuration objects require similar custom code, this is an architectural signal that a generic runtime capability may be missing or insufficient.

---

## 4.4 Configuration Is Executable Metadata

Standard Configuration should primarily describe system behavior through metadata.

Conceptually:

```text
Configuration Definition
        ↓
Metadata
        ↓
Runtime
        ↓
Executable Behavior
```

Configuration code may exist where behavior genuinely cannot or should not be expressed declaratively.

However, custom code must remain an extension mechanism rather than the default implementation mechanism.

---

## 4.5 Runtime and Metadata Remain Separate

Metadata describes the system.

Runtime executes the system.

The implementation must preserve this distinction.

For example:

```text
CatalogDefinition
```

describes a catalog, while:

```text
CatalogRuntime
```

provides the generic behavior required to operate a catalog.

The same principle applies to:

* documents;
* registers;
* reports;
* processings;
* forms;
* commands;
* security definitions.

---

## 4.6 Storage Is an Implementation Concern, Not a Business Definition

Business objects and configuration definitions must not become directly coupled to a particular storage implementation.

The storage architecture provides persistence capabilities.

Runtime components consume those capabilities through defined interfaces.

This preserves the architectural separation between:

```text
Business Model
     ↓
Runtime
     ↓
Storage
```

---

## 4.7 Measure Before Optimizing

Performance optimization must be evidence-driven.

The implementation should initially favor:

* correctness;
* architectural clarity;
* testability;
* observability;
* maintainability.

Optimization should be introduced based on measurements.

Important performance-sensitive areas should eventually have explicit benchmarks, particularly:

* metadata loading;
* object creation;
* querying;
* register movements;
* totals calculation;
* valuation;
* reporting;
* large datasets.

---

# 5. Platform and Standard Configuration

AcCoreD consists conceptually of two implementation layers.

```text
┌─────────────────────────────────────┐
│       Standard Configuration        │
│                                     │
│ Catalogs / Documents / Registers    │
│ Reports / Processings / Rules       │
└──────────────────┬──────────────────┘
                   │
                   │ metadata / runtime
                   ▼
┌─────────────────────────────────────┐
│          AcCoreD Platform           │
│                                     │
│ Metadata / Runtime / Storage        │
│ Posting / Registers / Valuation     │
│ Reporting / Security / Integration  │
└─────────────────────────────────────┘
```

---

## 5.1 Platform Responsibilities

The Platform is responsible for generic capabilities such as:

* metadata management;
* object model;
* runtime;
* persistence;
* query execution;
* document runtime;
* posting infrastructure;
* register infrastructure;
* totals;
* valuation;
* reporting runtime;
* processing runtime;
* security infrastructure;
* integration infrastructure;
* event infrastructure;
* configuration lifecycle.

The Platform must not contain Standard Configuration business semantics unless those semantics are explicitly defined as generic platform capabilities.

---

## 5.2 Standard Configuration Responsibilities

Standard Configuration defines the business application using Platform capabilities.

It may define:

* catalogs;
* documents;
* registers;
* reports;
* processings;
* forms;
* commands;
* business rules;
* workflows;
* configuration-specific metadata.

For example:

```text
Platform:
    Catalog Runtime

Standard Configuration:
    Assortment Catalog
    Business Partners Catalog
    Employees Catalog
```

The Platform does not need to know that `Assortment` is a Standard Configuration object.

---

# 6. Implementation Units

Implementation work should be organized around several different units.

## 6.1 Platform Capability

A reusable generic capability provided by the Platform.

Examples:

* Catalog Runtime;
* Document Runtime;
* Register Runtime;
* Query Runtime;
* Metadata Registry.

---

## 6.2 Configuration Definition

A metadata definition consumed by the Platform.

Examples:

* Assortment;
* Business Partner;
* Goods Receipt;
* Inventory Register.

---

## 6.3 Vertical Slice

An end-to-end implementation proving that several capabilities work together.

Example:

```text
Assortment
    ↓
Goods Receipt
    ↓
Posting
    ↓
Inventory
    ↓
Inventory Query
```

---

## 6.4 Architectural Increment

A meaningful implementation milestone that validates an architectural capability.

Examples:

* first metadata-driven catalog;
* first metadata-driven document;
* first posting operation;
* first register query;
* first valuation scenario;
* first metadata-driven report.

---

# 7. Dependency Strategy

Implementation order must follow architectural dependencies.

A simplified dependency chain is:

```text
Foundation
    ↓
Metadata
    ↓
Object Runtime
    ↓
Storage
    ↓
Catalog Runtime
    ↓
Document Runtime
    ↓
Posting
    ↓
Register Runtime
    ↓
Valuation
    ↓
Reporting
    ↓
Processings
    ↓
Security / Integration
```

This is a conceptual dependency graph, not a requirement that every component be completed completely before work on the next component begins.

Implementation may proceed incrementally when a stable subset is sufficient for the next vertical slice.

---

# 8. Horizontal and Vertical Implementation

Two implementation approaches are possible.

### Horizontal implementation

```text
Metadata — complete
Runtime — complete
Storage — complete
Posting — complete
Registers — complete
...
```

### Vertical implementation

```text
Metadata
  ↓
Runtime
  ↓
Storage
  ↓
One Catalog
  ↓
Working UI / Query
```

followed by:

```text
Document
  ↓
Posting
  ↓
Register
```

AcCoreD should primarily use the **vertical implementation approach**, while building the minimum horizontal infrastructure required by each slice.

This provides earlier architectural feedback and reduces the risk of discovering fundamental problems after a large amount of implementation work.

---

# 9. First Vertical Slice

The first major vertical slice should demonstrate that a metadata-defined catalog can become a working application object.

The conceptual flow is:

```text
Catalog Definition
        ↓
Metadata Registration
        ↓
Metadata Validation
        ↓
Runtime Creation
        ↓
Storage
        ↓
CRUD Operations
        ↓
Query
        ↓
Presentation
```

The first Standard Configuration candidate is:

**Assortment**

because it provides a relatively simple but meaningful master-data object.

The first slice should establish the reusable mechanisms required for subsequent catalogs.

---

# 10. Second Vertical Slice

The second major slice should demonstrate document processing.

Conceptually:

```text
Catalog Data
      ↓
Document Definition
      ↓
Document Runtime
      ↓
Document Instance
      ↓
Posting
      ↓
Register Movement
      ↓
Totals
      ↓
Query
```

A suitable first document scenario is a simple goods-receipt operation.

The purpose is not to build a complete purchasing subsystem.

The purpose is to prove that:

> a metadata-defined document can produce register facts through the generic posting architecture.

---

# 11. Third Vertical Slice

The third slice should demonstrate valuation.

Conceptually:

```text
Quantity Facts
      ↓
Register State
      ↓
Valuation Engine
      ↓
Cost Facts
      ↓
Cost Totals
      ↓
Valuation Query
```

The implementation should include at least one scenario where cost information is processed independently from quantity accounting.

This validates the architectural decisions established by the Valuation Architecture.

---

# 12. Fourth Vertical Slice

The fourth slice should demonstrate reporting.

Conceptually:

```text
Operational Data
      ↓
Report Data Source
      ↓
Dataset
      ↓
Dimensions / Measures
      ↓
Report Execution
      ↓
Presentation
```

The report should consume existing register and/or valuation data rather than introducing a separate reporting data model.

---

# 13. Standard Configuration Growth Strategy

The Standard Configuration should grow from a small working core.

The initial catalog set should be deliberately limited.

The currently proposed initial catalog direction is:

| Catalog           | Initial Role                                |
| ----------------- | ------------------------------------------- |
| Assortment        | Core master data                            |
| Employees         | Responsible persons / organizational actors |
| Business Partners | External counterparties                     |
| Cash Accounts     | Cash-related master data                    |
| Measure Units     | Quantity measurement                        |

Additional catalogs should be introduced only when required by a demonstrated business scenario.

The same principle applies to documents, registers, reports, and processings.

---

# 14. MVP Definition

The first MVP should not be defined by the number of implemented objects.

The MVP should be defined by the ability to execute a **complete business lifecycle**.

The target is approximately:

```text
Master Data
     ↓
Operational Document
     ↓
Posting
     ↓
Quantity Register
     ↓
Valuation
     ↓
Report
```

A successful MVP must therefore demonstrate:

1. metadata-defined master data;
2. metadata-defined document;
3. document persistence;
4. document posting;
5. register movement generation;
6. register totals;
7. quantity query;
8. valuation;
9. cost query;
10. report execution.

The MVP may have a very small number of business objects.

Completeness of the lifecycle is more important than breadth of functionality.

---

# 15. Definition of Done

An implementation item is considered complete only when its required layers are operational.

For a generic Platform capability, completion normally requires:

* implementation;
* public/internal API definition;
* metadata integration where applicable;
* storage integration where applicable;
* runtime integration;
* tests;
* error handling;
* documentation;
* observability;
* basic performance validation where relevant.

For a Standard Configuration object, completion normally requires:

* configuration definition;
* metadata validation;
* runtime availability;
* persistence;
* required commands;
* required queries;
* relevant business behavior;
* tests;
* configuration documentation.

A class existing in the repository is not considered an implemented feature.

---

# 16. Testing Strategy

Testing should operate at several levels.

## 16.1 Unit Tests

Used for isolated components and algorithms.

Examples:

* metadata validation;
* expression evaluation;
* totals calculations;
* valuation algorithms.

---

## 16.2 Component Tests

Used to verify interaction between closely related components.

Examples:

```text
Metadata Registry
       +
Catalog Runtime
```

or:

```text
Posting Handler
       +
Register Movement Builder
```

---

## 16.3 Integration Tests

Used to verify interactions across architectural boundaries.

Examples:

```text
Document
   ↓
Posting
   ↓
Register
   ↓
Totals
```

---

## 16.4 Vertical Slice Tests

Used to prove complete business scenarios.

Example:

```text
Create Assortment
      ↓
Create Goods Receipt
      ↓
Post
      ↓
Check Inventory
      ↓
Run Valuation
      ↓
Run Report
```

These tests are especially important because they validate the architecture as a whole.

---

# 17. Architectural Validation During Implementation

Implementation must continuously validate the following assumptions:

### Metadata-driven behavior

Can configuration definitions produce working runtime behavior without object-specific platform code?

### Runtime / Metadata separation

Can metadata evolve without changing generic runtime implementation?

### Storage independence

Can business behavior remain independent from storage details?

### Posting architecture

Can a document produce register facts through generic posting mechanisms?

### Register architecture

Can operational state be derived and queried from register facts and totals?

### Valuation independence

Can valuation process cost facts independently from quantity facts?

### Reporting architecture

Can reports consume operational and valuation data without duplicating business state?

If an implementation repeatedly violates one of these assumptions, the problem should be treated as an architectural issue rather than merely a coding inconvenience.

---

# 18. Handling Architectural Discoveries

Implementation will inevitably reveal problems not visible during architecture design.

Such discoveries must be classified.

### Type A — Implementation defect

The architecture is correct, but the implementation is incorrect.

Action:

```text
Fix implementation
```

### Type B — Missing implementation capability

The architecture already allows the required behavior, but the Platform lacks a concrete capability.

Action:

```text
Extend implementation
```

### Type C — Metadata limitation

The generic runtime exists, but the configuration model cannot express the required behavior.

Action:

```text
Review Configuration Definition Model
```

### Type D — Architectural limitation

The current architecture cannot support the required behavior without violating its principles.

Action:

```text
Architecture review
        ↓
ADR / Architecture update
        ↓
New baseline if required
```

This classification prevents normal implementation problems from unnecessarily destabilizing the architecture.

---

# 19. Performance Strategy

Performance optimization is important for AcCoreD because the Platform is intended to support large datasets and high-performance table-oriented operations.

However, performance work must be staged.

### Stage 1 — Correctness

Implement a clear and correct baseline.

### Stage 2 — Measurement

Introduce benchmarks and representative datasets.

### Stage 3 — Profiling

Identify actual bottlenecks.

### Stage 4 — Optimization

Optimize measured bottlenecks.

### Stage 5 — Regression Protection

Convert important performance characteristics into repeatable benchmarks.

Performance assumptions should not be treated as facts until supported by measurements.

---

# 20. Repository Strategy

The repository should reflect the architectural separation between:

```text
Platform
```

and:

```text
Standard Configuration
```

The exact directory and package structure will be defined in the subsequent repository-structure document.

However, the implementation strategy establishes the following rule:

> Platform implementation must not depend on Standard Configuration definitions.

The dependency direction is:

```text
Standard Configuration
          ↓
      Platform API
          ↓
      Platform Core
```

and not:

```text
Platform
    ↓
Standard Configuration
```

This dependency rule is fundamental.

---

# 21. Implementation Sequence

The initial implementation sequence is:

```text
Phase I
Platform Foundation
        ↓
Phase II
Metadata → Runtime
        ↓
Phase III
Catalog Runtime + Assortment
        ↓
Phase IV
Document Runtime + First Document
        ↓
Phase V
Posting + Register Integration
        ↓
Phase VI
Register Query + Totals
        ↓
Phase VII
Valuation
        ↓
Phase VIII
Reporting
        ↓
Phase IX
Processings
        ↓
Phase X
Security / Integration
        ↓
Phase XI
Standard MVP
        ↓
Phase XII
Hardening and Release
```

This sequence is intentionally approximate.

The actual roadmap will be refined after the repository structure and Configuration Definition Model are established.

---

# 22. Implementation Priorities

When competing implementation tasks arise, priority should generally be determined by:

1. architectural dependency;
2. ability to unlock a vertical slice;
3. validation value;
4. reuse across Standard Configuration;
5. correctness;
6. observability and testability;
7. performance;
8. breadth of functionality.

A capability that unlocks several future components should normally be implemented before a feature that serves only one configuration object.

---

# 23. Avoiding Premature Feature Expansion

The first implementation phase must resist several forms of scope expansion.

The project should not prematurely attempt to implement:

* every possible catalog;
* every possible document;
* every possible accounting scenario;
* complete workflow automation;
* all integrations;
* all deployment models;
* distributed execution;
* advanced UI customization;
* every valuation method;
* every reporting feature.

The objective of the first release is to establish a **small but architecturally complete system**.

---

# 24. First Working Release Philosophy

The first working release should answer one fundamental question:

> Can AcCoreD execute a real business scenario using metadata-defined Standard Configuration on top of the generic Platform?

A successful first release should therefore demonstrate:

```text
Configuration
     ↓
Metadata
     ↓
Runtime
     ↓
Storage
     ↓
Business Object
     ↓
Document
     ↓
Posting
     ↓
Register
     ↓
Valuation
     ↓
Report
```

If this chain works, AcCoreD has crossed the boundary from architectural design into a functioning application platform.

---

# 25. Relationship to Architecture Baseline

`architecture-core-3.0` remains the current architectural baseline.

This document does not replace or modify it.

The relationship is:

```text
architecture-core-3.0
        │
        │ defines WHAT and WHY
        ▼
IMPLEMENTATION_STRATEGY.md
        │
        │ defines HOW
        ▼
Repository Structure
        │
        ▼
Implementation Roadmap
        │
        ▼
Software
```

Any implementation decision that contradicts the architecture baseline must be explicitly reviewed.

---

# 26. Expected Next Documents

Following this strategy, the next planning documents should be:

### 1. `REPOSITORY_STRUCTURE.md`

Defines:

* repository layout;
* Platform modules;
* Standard Configuration modules;
* package boundaries;
* dependency direction;
* test structure;
* documentation structure.

### 2. `IMPLEMENTATION_ROADMAP.md`

Defines:

* implementation phases;
* milestones;
* dependencies;
* deliverables;
* acceptance criteria.

### 3. `MVP_DEFINITION.md`

Defines:

* first working business scenario;
* included objects;
* excluded functionality;
* acceptance criteria.

### 4. `CONFIGURATION_DEFINITION_MODEL.md`

Defines:

* configuration;
* metadata definitions;
* object definitions;
* runtime binding;
* versioning;
* validation;
* extension mechanisms.

These documents together form the initial **Standard Edition implementation planning baseline**.

---

# 27. Summary

The implementation strategy can be summarized by the following principles:

> **Architecture before implementation.**

> **Capabilities before configuration objects.**

> **Vertical slices before broad feature coverage.**

> **Metadata before hard-coded business objects.**

> **Platform before Standard Configuration.**

> **Correctness before optimization.**

> **Measurement before performance claims.**

> **A small complete lifecycle before a large incomplete system.**

The immediate implementation goal is therefore not to build a large ERP-like application.

It is to prove that AcCoreD can transform:

```text
Configuration Definition
        ↓
Metadata
        ↓
Generic Platform Runtime
        ↓
Working Business Behavior
```

and then extend that mechanism into a complete Standard Edition.
