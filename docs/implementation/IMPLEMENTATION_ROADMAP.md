# Implementation Roadmap

**Project:** AcCoreD
**Stage:** Standard Edition — Design & Implementation
**Status:** Active
**Architecture Baseline:** `architecture-core-3.0`
**Implementation Strategy:** `IMPLEMENTATION_STRATEGY.md`
**Repository Structure:** `REPOSITORY_STRUCTURE.md`

---

# 1. Purpose

This document defines the implementation roadmap for AcCoreD following completion of the core architecture cycle.

The roadmap translates the implementation strategy into a sequence of executable implementation phases.

It defines:

* implementation order;
* phase dependencies;
* major deliverables;
* vertical slices;
* acceptance criteria;
* MVP boundaries;
* transition from architectural planning to implementation.

The roadmap is intentionally incremental.

The objective is not to implement the entire Standard Edition as quickly as possible.

The objective is to progressively establish a working AcCoreD Platform and demonstrate that Standard Configuration can be built on top of it without violating the architectural boundaries.

---

# 2. Roadmap Principles

The roadmap follows the following principles.

## 2.1 Architecture Is the Baseline

`architecture-core-3.0` is the current architectural baseline.

Implementation should follow it.

If implementation reveals a genuine architectural limitation, that discovery must be handled explicitly rather than silently changing the architecture.

---

## 2.2 Each Phase Produces a Verifiable Result

A phase is not complete because a collection of source files exists.

A phase is complete when its intended capability:

* exists;
* is integrated;
* is tested;
* is observable;
* satisfies defined acceptance criteria.

---

## 2.3 Vertical Slices Have Higher Validation Value

Whenever practical, implementation should produce an end-to-end scenario.

The preferred progression is:

```text
Platform Capability
        ↓
Configuration Definition
        ↓
Runtime
        ↓
Business Scenario
        ↓
Verification
```

---

## 2.4 Minimize Premature Scope

Only capabilities required to support the next meaningful vertical slice should be implemented.

A feature should not be implemented merely because it is architecturally possible.

---

## 2.5 Preserve Existing Mature Code

Existing stable implementation should be reused whenever it is compatible with the architecture.

The roadmap is not a rewrite plan.

Refactoring should be driven by:

* architectural requirements;
* implementation dependencies;
* correctness;
* maintainability;
* measured performance.

---

# 3. Roadmap Overview

The initial roadmap consists of the following phases:

```text
Phase 0  Repository & Development Baseline
    ↓
Phase 1  Platform Runtime Foundation
    ↓
Phase 2  Metadata → Runtime
    ↓
Phase 3  Catalog Runtime
    ↓
Phase 4  First Document
    ↓
Phase 5  Posting → Register
    ↓
Phase 6  Register Query & Totals
    ↓
Phase 7  Valuation
    ↓
Phase 8  Reporting
    ↓
Phase 9  Processing
    ↓
Phase 10 Security
    ↓
Phase 11 Integration
    ↓
Phase 12 Standard MVP
    ↓
Phase 13 Hardening & Release
```

The sequence is dependency-oriented.

Some phases may overlap once their required interfaces are stable.

---

# 4. Phase 0 — Repository & Development Baseline

## Objective

Prepare the repository for implementation without introducing unnecessary application functionality.

This phase establishes the development baseline from which all subsequent implementation work proceeds.

---

## Scope

Establish:

* source tree;
* Platform package;
* Standard Configuration package;
* test structure;
* documentation structure;
* development tooling;
* packaging configuration;
* basic CI checks if applicable;
* repository-level conventions.

---

## Expected Structure

The repository should approximately conform to:

```text
src/
├── accore/
│   └── platform/
└── standard/

tests/
├── unit/
├── component/
├── integration/
└── vertical/

config/
└── standard/

docs/
├── architecture/
├── implementation/
└── decisions/
```

---

## Deliverables

* repository structure;
* Python package configuration;
* import boundaries;
* basic test runner;
* formatting/linting configuration where appropriate;
* documentation placement;
* baseline development instructions.

---

## Acceptance Criteria

Phase 0 is complete when:

1. Platform code can be imported as a package;
2. Standard Configuration has a separate package boundary;
3. Platform does not depend on Standard Configuration;
4. tests execute successfully;
5. repository documentation has a defined structure;
6. a minimal development workflow is reproducible.

---

## Not Included

This phase does not implement:

* catalogs;
* documents;
* registers;
* valuation;
* reporting;
* Standard business logic.

---

# 5. Phase 1 — Platform Runtime Foundation

## Objective

Establish the minimum runtime foundation required to execute metadata-defined objects.

This is the first actual Platform implementation phase.

---

## Scope

Initial capabilities should include:

* identity;
* common types;
* lifecycle primitives;
* runtime context;
* object identity;
* basic object lifecycle;
* dependency boundaries;
* error handling;
* service resolution where required.

---

## Architectural Goal

The Platform should be able to represent and manage a generic runtime object without knowing any Standard Configuration object.

Conceptually:

```text
Object Definition
        ↓
Runtime Object
        ↓
Lifecycle
```

---

## Deliverables

* foundation package;
* object model primitives;
* runtime context;
* basic runtime lifecycle;
* tests;
* initial public Platform contracts.

---

## Acceptance Criteria

Phase 1 is complete when:

1. a generic runtime object can be created;
2. the object has a stable identity;
3. lifecycle operations are defined;
4. runtime context can be supplied;
5. Platform code remains independent of Standard Configuration;
6. unit and component tests pass.

---

# 6. Phase 2 — Metadata → Runtime

## Objective

Establish the fundamental mechanism by which metadata definitions become executable runtime objects.

This phase is one of the most important milestones in the entire project.

---

## Scope

Implement the minimum metadata infrastructure required for:

* definition registration;
* definition identity;
* definition validation;
* metadata lookup;
* runtime binding;
* metadata lifecycle;
* basic configuration loading.

---

## Target Flow

```text
Configuration Definition
        ↓
Metadata
        ↓
Metadata Registry
        ↓
Runtime Resolution
        ↓
Runtime Object
```

---

## First Architectural Proof

The system should demonstrate that a runtime object can be created from metadata without hard-coded knowledge of the eventual Standard Configuration object.

---

## Deliverables

* metadata definitions;
* metadata registry;
* metadata validation;
* runtime resolution;
* metadata-to-runtime binding;
* tests.

---

## Acceptance Criteria

Phase 2 is complete when:

1. a metadata definition can be registered;
2. the definition can be validated;
3. the runtime can resolve the definition;
4. a runtime object can be created from it;
5. the Platform does not contain Standard Configuration-specific knowledge;
6. metadata and runtime remain separate concerns.

---

# 7. Phase 3 — Catalog Runtime

## Objective

Implement the generic catalog capability and use it to create the first Standard Configuration catalog.

---

## Platform Scope

Implement the minimum Catalog Runtime required for:

* catalog definition;
* catalog records;
* identity;
* required system fields;
* parent-child hierarchy;
* folders;
* CRUD;
* persistence;
* query;
* basic validation.

---

## Standard Configuration Scope

Implement:

**Assortment**

as the first metadata-defined Standard Configuration catalog.

---

## Vertical Slice #1

```text
Assortment Definition
        ↓
Metadata
        ↓
Catalog Runtime
        ↓
Storage
        ↓
Assortment Record
        ↓
Query
```

---

## Deliverables

Platform:

* Catalog Runtime;
* catalog persistence;
* catalog query support;
* hierarchy support.

Standard:

* Assortment definition;
* Assortment metadata;
* initial forms/query representation as required.

Tests:

* catalog unit tests;
* metadata integration tests;
* Assortment vertical test.

---

## Acceptance Criteria

Phase 3 is complete when:

1. Assortment is defined through configuration metadata;
2. the generic Catalog Runtime executes it;
3. records can be created;
4. records can be updated;
5. records can be queried;
6. hierarchy works where applicable;
7. persistence works;
8. no Assortment-specific logic exists inside generic Catalog Runtime;
9. the first vertical slice passes.

---

# 8. Phase 4 — First Document

## Objective

Implement the generic Document Runtime and create the first operational Standard Configuration document.

---

## Platform Scope

Implement the minimum document infrastructure required for:

* document definition;
* document identity;
* requisites;
* tabular parts;
* lifecycle;
* numbering;
* persistence;
* posting integration boundary.

---

## Standard Configuration Scope

Introduce the first operational document.

Initial candidate:

**Goods Receipt**

The exact final name may be adjusted when the Standard Configuration model is formalized.

---

## Vertical Slice #2

```text
Assortment
      ↓
Goods Receipt
      ↓
Document Runtime
      ↓
Persistence
```

At this stage posting may exist only as an integration boundary.

The actual register movement generation belongs to the next phase.

---

## Acceptance Criteria

Phase 4 is complete when:

1. a document can be defined through metadata;
2. document instances can be created;
3. requisites work;
4. tabular parts work;
5. document lifecycle works;
6. documents can be persisted;
7. document numbering works according to the selected strategy;
8. Goods Receipt uses generic Document Runtime;
9. document-specific runtime is not hard-coded into Platform.

---

# 9. Phase 5 — Posting → Register

## Objective

Connect operational documents with the Posting Architecture and produce register movements.

This is the point where the system begins to behave as an accounting platform rather than merely a metadata-driven application framework.

---

## Platform Scope

Implement:

* posting context;
* posting lifecycle;
* posting handler infrastructure;
* movement generation;
* posting validation;
* register movement interface.

---

## Standard Configuration Scope

Extend Goods Receipt so that posting produces Inventory register movements.

---

## Vertical Slice #3

```text
Goods Receipt
      ↓
Posting
      ↓
Posting Context
      ↓
Register Movement
      ↓
Inventory
```

---

## Acceptance Criteria

Phase 5 is complete when:

1. a document can be posted;
2. posting context is available;
3. posting produces register movements;
4. movements are associated with the correct register;
5. posting failures are handled correctly;
6. reposting behavior is defined for the implemented scenario;
7. Inventory receives quantity facts;
8. the full posting vertical slice passes.

---

# 10. Phase 6 — Register Query & Totals

## Objective

Complete the first usable register implementation.

---

## Platform Scope

Implement the minimum:

* register storage;
* movement queries;
* totals;
* balance queries;
* period filtering;
* dimensions;
* resources;
* register lifecycle.

The adaptive totals strategy defined by Register Architecture should initially use the simplest viable implementation.

---

## Standard Configuration Scope

Complete the Inventory Register definition.

---

## Vertical Slice #4

```text
Goods Receipt
      ↓
Posting
      ↓
Inventory Movements
      ↓
Inventory Totals
      ↓
Inventory Balance Query
```

---

## Acceptance Criteria

Phase 6 is complete when:

1. register movements can be persisted;
2. register movements can be queried;
3. totals can be maintained;
4. balances can be queried;
5. Inventory balance after Goods Receipt is correct;
6. rebuilding totals produces the same result;
7. register tests pass.

---

# 11. Phase 7 — Valuation

## Objective

Introduce the Valuation Architecture into the working business lifecycle.

This phase validates the architectural principle:

> Quantity accounting and valuation are related but independent concerns.

---

## Platform Scope

Implement the minimum valuation infrastructure required for:

* valuation facts;
* valuation processing;
* cost movement;
* cost totals;
* valuation queries;
* one supported valuation method.

---

## Standard Configuration Scope

Configure valuation for the Inventory scenario.

---

## Vertical Slice #5

```text
Quantity Facts
      ↓
Inventory Register
      ↓
Valuation Engine
      ↓
Cost Facts
      ↓
Cost Totals
      ↓
Cost Query
```

---

## Required Scenario

The first valuation implementation should support a scenario where quantity facts exist independently from cost processing.

The implementation should be capable of representing delayed cost information according to the Valuation Architecture.

---

## Acceptance Criteria

Phase 7 is complete when:

1. quantity accounting remains functional independently;
2. valuation can consume quantity-related facts;
3. cost facts can be produced;
4. cost totals can be maintained;
5. at least one valuation method works;
6. valuation results can be queried;
7. the basic delayed-cost scenario is supported;
8. valuation tests pass.

---

# 12. Phase 8 — Reporting

## Objective

Introduce the generic reporting runtime and produce the first Standard Configuration report.

---

## Platform Scope

Implement the minimum:

* report data source;
* dataset;
* dimensions;
* measures;
* report execution;
* result materialization;
* basic presentation model.

---

## Standard Configuration Scope

Implement an initial report such as:

**Inventory Balance**

---

## Vertical Slice #6

```text
Inventory Register
      +
Valuation
      ↓
Report Data Source
      ↓
Dataset
      ↓
Dimensions / Measures
      ↓
Report Execution
      ↓
Inventory Balance Report
```

---

## Acceptance Criteria

Phase 8 is complete when:

1. a report is defined through metadata;
2. data sources can be configured;
3. dimensions work;
4. measures work;
5. report execution works;
6. Inventory Balance can be produced;
7. report execution does not maintain an independent copy of accounting state.

---

# 13. Phase 9 — Processing

## Objective

Introduce the generic Processing mechanism and use it to implement at least one meaningful Standard Configuration operation.

Processings are important because they represent active business behavior beyond passive data objects.

---

## Platform Scope

Implement:

* Processing Definition;
* Processing Runtime;
* Processing Context;
* command execution;
* progress/error handling where required.

---

## Standard Configuration Scope

Implement one processing that exercises multiple existing capabilities.

Possible examples include:

* inventory recalculation;
* valuation rebuild;
* data validation;
* controlled recalculation.

The exact processing should be selected based on the first MVP scenario.

---

## Acceptance Criteria

Phase 9 is complete when:

1. a processing can be defined;
2. the processing can be executed;
3. it receives runtime context;
4. it can interact with Platform services;
5. errors are observable;
6. at least one Standard Configuration processing works end-to-end.

---

# 14. Phase 10 — Security

## Objective

Introduce sufficient security infrastructure for the first usable Standard Edition.

Security should not be postponed until after the application has accumulated large amounts of application-specific authorization logic.

---

## Platform Scope

Implement the minimum required for:

* security context;
* authentication boundary;
* authorization;
* roles;
* permissions;
* access evaluation.

---

## Standard Configuration Scope

Define the initial security model required by the MVP.

---

## Acceptance Criteria

Phase 10 is complete when:

1. a user security context exists;
2. permissions can be evaluated;
3. roles can be defined;
4. access to selected objects/operations can be controlled;
5. unauthorized operations are rejected;
6. security behavior is tested.

---

# 15. Phase 11 — Integration

## Objective

Implement the minimum integration capabilities required to make the Standard Edition externally usable.

---

## Platform Scope

Priorities:

1. API contracts;
2. API runtime;
3. event infrastructure;
4. import/export mechanisms;
5. integration adapters where required.

The implementation should follow the Contract-first API principle and Event-Aware architecture.

---

## Acceptance Criteria

Phase 11 is complete when:

1. a defined API contract can expose a supported operation;
2. API requests reach the appropriate runtime boundary;
3. API responses are stable and documented;
4. supported events can be published/consumed;
5. basic import/export works where required by the MVP.

---

# 16. Phase 12 — Standard MVP

## Objective

Assemble the previously implemented capabilities into the first coherent Standard Edition release.

This phase is not primarily about introducing new architecture.

It is about integrating and hardening the already implemented vertical slices into one usable product scenario.

---

## MVP Core

The initial MVP should demonstrate:

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

The minimum initial configuration is expected to contain approximately:

### Catalogs

* Assortment;
* Employees;
* Business Partners;
* Cash Accounts;
* Measure Units.

### Documents

At least one operational document required by the first business lifecycle.

### Registers

At least one quantity register.

### Valuation

At least one working valuation method.

### Reports

At least one operational/accounting report.

### Processings

At least one meaningful processing.

The exact final object list belongs to `MVP_DEFINITION.md`.

---

## MVP Acceptance Criteria

The MVP is complete when a clean environment can execute a complete scenario from configuration loading to report generation.

For example:

```text
Load Standard Configuration
        ↓
Create Assortment
        ↓
Create Business Partner
        ↓
Create Goods Receipt
        ↓
Post Goods Receipt
        ↓
Generate Inventory Movement
        ↓
Update Inventory Totals
        ↓
Run Valuation
        ↓
Generate Inventory Report
```

The scenario must work without manually modifying Platform internals.

---

# 17. Phase 13 — Hardening & Release

## Objective

Prepare the first working release for broader use.

This phase focuses on quality rather than major new capabilities.

---

## Scope

### Correctness

* regression testing;
* edge cases;
* recovery;
* transaction behavior;
* error handling.

### Performance

* benchmark suite;
* profiling;
* query performance;
* register performance;
* valuation performance;
* report performance.

### Reliability

* rebuild/recovery;
* configuration validation;
* startup validation;
* corrupted-data handling where relevant.

### Documentation

* installation;
* development setup;
* configuration development;
* Standard Edition usage;
* architecture references.

### Packaging

* versioning;
* build;
* release artifact;
* reproducibility.

---

## Acceptance Criteria

The release candidate should:

* pass the complete test suite;
* pass the MVP vertical scenarios;
* satisfy defined performance baselines;
* install reproducibly;
* load Standard Configuration reproducibly;
* provide sufficient diagnostics;
* have complete required documentation.

---

# 18. Vertical Slice Map

The roadmap can be summarized by the following vertical slices.

| Slice | Scenario                  | Main Architecture Validated  |
| ----- | ------------------------- | ---------------------------- |
| VS-1  | Assortment                | Metadata → Runtime → Storage |
| VS-2  | Goods Receipt             | Document Runtime             |
| VS-3  | Goods Receipt → Inventory | Posting                      |
| VS-4  | Inventory Balance         | Register + Totals            |
| VS-5  | Inventory Valuation       | Valuation                    |
| VS-6  | Inventory Report          | Reporting                    |
| VS-7  | Standard Processing       | Processing                   |
| VS-8  | Secured Operation         | Security                     |
| VS-9  | External Operation        | Integration                  |
| VS-10 | Complete MVP              | Full architecture lifecycle  |

---

# 19. Milestone Model

Each major phase should produce a milestone.

```text
M0  Development Baseline
M1  Runtime Foundation
M2  Metadata Runtime
M3  First Catalog
M4  First Document
M5  Posting
M6  Register
M7  Valuation
M8  Reporting
M9  Processing
M10 Security
M11 Integration
M12 Standard MVP
M13 Release Candidate
```

Milestones are cumulative.

Each milestone should preserve the working state of previous milestones.

---

# 20. Dependency Graph

The main dependency chain is:

```text
M0
 │
 ▼
M1
 │
 ▼
M2
 │
 ▼
M3
 │
 ▼
M4
 │
 ▼
M5
 │
 ▼
M6
 │
 ▼
M7
 │
 ▼
M8
 │
 ├──────────────► M9
 │
 ├──────────────► M10
 │
 └──────────────► M11
                       │
                       ▼
                      M12
                       │
                       ▼
                      M13
```

Security and Integration may begin earlier if their interfaces are needed by implementation, but they should not block the first core accounting vertical slice unless a specific requirement makes them necessary.

---

# 21. Parallel Work

Once the core Platform boundaries become stable, selected work can proceed in parallel.

For example:

```text
                ┌── Reporting
                │
Register ───────┼── Valuation
                │
                └── Processing
```

However, parallel development must not introduce competing definitions of the same architectural contract.

Shared interfaces should be stabilized before multiple subsystems depend on them.

---

# 22. Phase Completion Rules

A phase should not automatically be marked complete because all planned coding tasks are finished.

A phase is complete only when:

```text
Implementation
     +
Tests
     +
Integration
     +
Documentation
     +
Acceptance Criteria
     =
Completed Phase
```

If an architectural question remains unresolved, the phase should be marked accordingly rather than silently closed.

---

# 23. Handling Discovered Problems

During implementation, discovered issues should be classified as:

### Implementation Bug

Fix the implementation.

### Missing Capability

Extend the Platform according to the existing architecture.

### Configuration Model Limitation

Review `CONFIGURATION_DEFINITION_MODEL.md`.

### Architectural Limitation

Trigger architecture review and, if necessary, an ADR and new architecture baseline.

The roadmap itself should not be used to bypass architecture governance.

---

# 24. What Must Not Happen

The roadmap explicitly prohibits several implementation patterns.

## 24.1 Building the Entire Platform Before Testing It

The Platform must be validated incrementally.

---

## 24.2 Building Standard Configuration Independently

Standard Configuration must not become an alternative implementation of Platform capabilities.

---

## 24.3 Implementing All Catalogs First

Catalog breadth is less valuable than a complete vertical slice.

---

## 24.4 Implementing UI Before Runtime Contracts

Presentation should consume stable runtime behavior.

The first implementation should not hide unresolved runtime architecture behind UI code.

---

## 24.5 Optimizing Before Measuring

Performance work should be supported by benchmarks and profiling.

---

## 24.6 Adding Business Logic to Platform for Convenience

If a Standard Configuration feature requires special handling, first determine whether:

* metadata is insufficient;
* runtime capability is missing;
* an extension point is required.

Hard-coding the business rule into Platform should be the last option.

---

# 25. First Implementation Target

The current implementation sequence has reached Phase 4:

```text
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
```

Phase 4 establishes the generic Object Runtime boundary between Runtime Object Type resolution and future persistence.

resulting in:

> **A metadata-defined Assortment catalog running on the generic AcCoreD Platform.**

This is the first concrete proof that the architecture has successfully transitioned into implementation.

The current Phase 4 target flow is:

```text
Assortment Definition
        ↓
Configuration Metadata
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
CatalogRuntime
        ↓
ObjectCreator
        ↓
Assortment ObjectInstance
```

Physical Storage remains outside this Phase 4 flow.

The first implementation should deliberately remain small.

Its purpose is not to make Standard Edition useful yet.

Its purpose is to prove that the fundamental mechanism works.

---

# 26. Transition From Planning to Implementation

The planning stage is considered complete when the following documents exist and are mutually consistent:

```text
architecture-core-3.0
        │
        ▼
IMPLEMENTATION_STRATEGY.md
        │
        ▼
REPOSITORY_STRUCTURE.md
        │
        ▼
IMPLEMENTATION_ROADMAP.md
        │
        ├──────────────┐
        ▼              ▼
MVP_DEFINITION.md   CONFIGURATION_DEFINITION_MODEL.md
        │              │
        └──────┬───────┘
               ▼
        First Implementation
```

The next implementation work should begin only after the boundaries of the Configuration Definition Model are sufficiently clear.

---

# 27. Initial Implementation Order

The practical order is therefore:

### Step 1

Establish repository baseline.

### Step 2

Establish Platform runtime foundation.

### Step 3

Implement metadata registration and resolution.

### Step 4

Implement generic Catalog Runtime.

### Step 5

Define and run Assortment.

### Step 6

Validate the first vertical slice.

Only after this point should we proceed to the first document implementation.

---

# 28. Roadmap Success Criteria

The roadmap is successful if it leads to a system where:

1. Platform capabilities are reusable;
2. Standard Configuration is metadata-driven;
3. Platform remains independent of Standard Configuration;
4. vertical business scenarios work end-to-end;
5. quantity accounting works;
6. valuation works independently from quantity accounting;
7. reporting consumes platform-managed data;
8. Processings can orchestrate business operations;
9. security can control access;
10. external integration can use stable contracts;
11. the first Standard Edition can be installed and executed reproducibly.

The ultimate goal is not merely to complete the listed phases.

The goal is to establish a repeatable mechanism for building additional configurations on top of AcCoreD.

---

# 29. Long-Term Extension

After the first Standard Edition release, the same implementation model should support:

```text
AcCoreD Platform
       │
       ├── Standard Configuration
       │
       ├── Custom Configuration A
       │
       ├── Custom Configuration B
       │
       └── Industry Configuration
```

The Platform therefore becomes the reusable technical foundation, while configurations provide application-specific behavior.

This is the final validation of the architectural strategy.

---

# 30. Summary

The implementation roadmap follows one central idea:

> **Build the smallest complete system first, then expand it.**

The sequence is:

```text
Repository
    ↓
Runtime
    ↓
Metadata
    ↓
Catalog
    ↓
Document
    ↓
Posting
    ↓
Register
    ↓
Valuation
    ↓
Reporting
    ↓
Processing
    ↓
Security
    ↓
Integration
    ↓
Standard MVP
    ↓
Hardening
```

The first meaningful implementation milestone is not a large Standard Configuration.

It is:

> **A metadata-defined Assortment running through the generic Platform runtime.**

The first complete business milestone is:

> **Master Data → Document → Posting → Register → Valuation → Report.**

This sequence provides progressively stronger evidence that the AcCoreD architecture is not only theoretically coherent but implementable as a reusable application platform.
