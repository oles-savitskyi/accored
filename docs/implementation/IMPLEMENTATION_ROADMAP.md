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
Phase 3  Configuration & Runtime Resolution
    ↓
Phase 4  Object Runtime
    ↓
Phase 5  Storage & Persistence Boundary
    ↓
Phase 6  Posting → Register
    ↓
Phase 7  Register Query & Totals
    ↓
Phase 8  Valuation
    ↓
Phase 9  Reporting
    ↓
Phase 10 Processing
    ↓
Phase 11 Security
    ↓
Phase 12 Integration
    ↓
Phase 13 Standard MVP
    ↓
Phase 14 Hardening & Release
```

The sequence is dependency-oriented.

Some phases may overlap once their required interfaces are stable.

The first four phases establish the reusable Platform execution model:

Configuration
    ↓
Metadata
    ↓
Runtime Configuration Context
    ↓
Metadata Resolution
    ↓
Runtime Object Type Resolution
    ↓
Object Instance Creation
    ↓
Object Runtime

Later phases extend this foundation with persistence, accounting, reporting, processing, security and integration capabilities.

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

# 7. Phase 3 — Configuration & Runtime Resolution

## Objective

 Establish the runtime configuration boundary required to resolve metadata-defined runtime types within an explicit active configuration context. Phase 3 connects the configuration lifecycle established in Phase 2 with executable runtime resolution.

 ---

 ## Scope

 Implement the minimum runtime configuration infrastructure required for:

 * active configuration publication;
 * immutable runtime configuration context;
 * metadata resolution from the active configuration;
 * runtime object type resolution;
 * explicit configuration context propagation;
 * separation between metadata resolution and runtime object type resolution.

 ---

 ## Target Flow

 ```text
 Validated Configuration
  ↓
 Active Configuration
  ↓
 RuntimeConfigurationContext
  ↓
 MetadataResolver
  ↓
 RuntimeResolver
  ↓
 Runtime Object Type
```

## Architectural Goal

Runtime consumers must operate against an explicit immutable runtime configuration snapshot.

Runtime resolution must not depend on global mutable configuration state.

Metadata resolution and Runtime Object Type resolution remain separate responsibilities.

## Deliverables
 * active configuration model;
 * runtime configuration context;
 * metadata resolver;
 * runtime resolver;
 * runtime object type contract;
 * public configuration/runtime boundaries;
 * tests.

## Acceptance Criteria

Phase 3 is complete when:

1. a validated configuration can become active;
2. an immutable RuntimeConfigurationContext can be created;
3. metadata can be resolved through the active runtime configuration;
4. Runtime Object Types can be resolved from metadata;
5. Runtime resolution operates through the explicit configuration context;
6. MetadataResolver and RuntimeResolver remain separate concerns;
7. runtime consumers do not require direct access to MetadataRegistry;
8. configuration context boundaries are enforced by tests;
9. all Phase 3 quality gates are satisfied.

## Not Included

This phase does not implement:

 * generic object instance creation;
 * object lifecycle;
 * object state;
 * object registry;
 * persistence;
 * Storage Provider integration;
 * document runtime;
 * posting;
 * register operations.

---

# 8. Phase 4 — Object Runtime

## Objective

Establish the generic Object Runtime boundary that creates and manages executable object instances from resolved Runtime Object Types within an explicit Runtime Configuration Context. Phase 4 is the first phase in which the platform creates a concrete Object Instance independently of any future persistence mechanism.

---

## Platform Scope

Implement the minimum generic Object Runtime required for:
* Object Identity;
* Runtime Object Type dependency;
* Object Instance;
* Object State;
* Object Context;
* object creation boundary;
* object lifecycle;
* explicit runtime configuration context propagation.

---

## Architectural Flow
```text
RuntimeConfigurationContext
 ↓
MetadataResolver
 ↓
RuntimeResolver
 ↓
Runtime Object Type
 ↓
Object Creation Boundary
 ↓
Object Instance
 ↓
Identity / State / Context
 ↓
Object Lifecycle
```

## Object Type Boundary

The Object Runtime depends on the architectural RuntimeObjectType contract.

It must not depend on a specific concrete runtime implementation.

For the current catalog vertical slice:

Catalog Metadata
        ↓
RuntimeResolver
        ↓
CatalogRuntime
        ↓
ObjectCreator
        ↓
Assortment ObjectInstance

CatalogRuntime is a concrete implementation of RuntimeObjectType, not the generic Object Runtime itself.

Future runtime types may include other object categories without introducing independent object-runtime frameworks.

## Object Creation

Object instance creation is owned by the Object Runtime creation boundary.

The creation boundary:

* receives a resolved Runtime Object Type;
* receives an explicit Object Context;
* assigns Object Identity;
* creates the Object Instance;
* establishes the initial Object State;
* preserves the Runtime Configuration Context snapshot.

RuntimeResolver resolves Runtime Object Types but does not create Object Instances.

## Object Lifecycle

The minimum Phase 4 lifecycle is:

CREATED
   ↓
ACTIVE
   ↓
DISPOSED

Lifecycle is owned by Object Runtime and is independent of Configuration Lifecycle.

## Object State

For the minimum Phase 4 implementation, Object State is limited to runtime lifecycle state.

Phase 4 does not introduce a generalized mutable business-state model.

Business values, metadata-defined attributes, dirty tracking, persistence state, and other mutable object data remain outside the Phase 4 implementation scope.

## Storage Boundary

Persistence is outside the scope of Phase 4.

Phase 4 establishes the runtime representation independently of physical storage.

Future Storage Architecture will define:

* persistent representation;
* runtime-to-storage mapping;
* loading and persistence boundaries;
* storage provider interaction.

Object creation in Phase 4 must not imply automatic persistence.

Standard Configuration Vertical Slice

The Phase 4 vertical slice uses the existing Assortment catalog:

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

The purpose of this slice is to demonstrate that a metadata-defined object can be resolved and instantiated through the generic Object Runtime.

## Acceptance Criteria

Phase 4 is complete when:

1. Object Identity is immutable and independent of configuration identity;
2. Object Instance is distinct from Runtime Object Type;
3. Object Runtime depends on the RuntimeObjectType contract;
4. RuntimeResolver resolves types but does not create instances;
5. ObjectCreator provides the object creation boundary;
6. Object Context preserves an explicit RuntimeConfigurationContext snapshot;
7. Object lifecycle follows the defined lifecycle transitions;
8. Object State remains independent of persistence;
9. no Storage implementation is required for object creation;
10. the Assortment vertical slice creates a concrete Object Instance;
11. generic Object Runtime boundaries are enforced by tests;
12. Phase 3 invariants remain intact.

---

# 9. Phase 5 — Storage & Persistence Boundary

## Objective

Establish the persistence boundary between Runtime Objects and physical Storage without exposing storage implementation details to Runtime.

## Scope

Implement the minimum Storage capability required to:

* represent persistent object data;
* map Runtime Object state to persistent representation;
* load persisted objects into Runtime;
* persist object changes through an explicit Storage boundary;
* preserve Runtime independence from the physical storage provider.

## Architectural Goal

Runtime and Storage remain separate architectural concerns.

Runtime Object
      ↕
Storage Boundary
      ↕
Persistent Representation
      ↕
Storage Provider

Runtime must not depend on:

* SQL schemas;
* database-specific APIs;
* EAV implementation details;
* physical table layout;
* Storage Provider-specific identifiers.

## Acceptance Criteria

Phase 5 is complete when:

1. Runtime Objects can be loaded through the Storage boundary;
2. Runtime Objects can be persisted through the Storage boundary;
3. Runtime remains independent of the concrete Storage Provider;
4. persistent representation is distinct from Runtime Object representation;
5. Storage-specific implementation details do not leak into Runtime;
6. persistence behavior is covered by tests.

## Not Included

This phase does not implement:

* posting;
* register movements;
* valuation;
* reporting;
* document-specific accounting logic.

---

# 10. Phase 6 — Posting

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


# 11. Phase 7 — Register Query & Totals

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

# 12. Phase 8 — Valuation

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

# 13. Phase 9 — Reporting

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

# 14. Phase 10 — Processing

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

# 15. Phase 11 — Security

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

# 16. Phase 12 — Integration

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

# 17. Phase 13 — Standard MVP

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

# 18. Phase 14 — Hardening & Release

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

# 19. Vertical Slice Map

The roadmap can be summarized by the following vertical slices.

| Slice | Scenario                   | Main Architecture Validated                         |
| ----- | -------------------------- | --------------------------------------------------- |
| VS-1  | Assortment Object Creation | Configuration → Metadata → Runtime → Object Runtime |
| VS-2  | Assortment Persistence     | Object Runtime → Storage                            |
| VS-3  | Goods Receipt              | Document Runtime                                    |
| VS-4  | Goods Receipt → Inventory  | Posting                                             |
| VS-5  | Inventory Balance          | Register + Totals                                   |
| VS-6  | Inventory Valuation        | Valuation                                           |
| VS-7  | Inventory Report           | Reporting                                           |
| VS-8  | Standard Processing        | Processing                                          |
| VS-9  | Secured Operation          | Security                                            |
| VS-10 | External Operation         | Integration                                         |
| VS-11 | Complete MVP               | Full architecture lifecycle                         |

---

# 20. Milestone Model

Each major phase should produce a milestone.

```text
M0 Development Baseline
M1 Runtime Foundation
M2 Metadata Runtime
M3 Configuration & Runtime Resolution
M4 Object Runtime
M5 Storage Boundary
M6 Posting
M7 Register
M8 Valuation
M9 Reporting
M10 Processing
M11 Security
M12 Integration
M13 Standard MVP
M14 Release Candidate
```

Milestones are cumulative.

Each milestone should preserve the working state of previous milestones.

The catalog and document capabilities are introduced as concrete Runtime Object Type implementations and vertical slices rather than as independent architectural foundations.

---

# 21. Dependency Graph

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

# 22. Parallel Work

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

# 23. Phase Completion Rules

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

# 24. Handling Discovered Problems

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

# 25. What Must Not Happen

The roadmap explicitly prohibits several implementation patterns.

## 25.1 Building the Entire Platform Before Testing It

The Platform must be validated incrementally.

---

## 25.2 Building Standard Configuration Independently

Standard Configuration must not become an alternative implementation of Platform capabilities.

---

## 25.3 Implementing All Catalogs First

Catalog breadth is less valuable than a complete vertical slice.

---

## 25.4 Implementing UI Before Runtime Contracts

Presentation should consume stable runtime behavior.

The first implementation should not hide unresolved runtime architecture behind UI code.

---

## 25.5 Optimizing Before Measuring

Performance work should be supported by benchmarks and profiling.

---

## 25.6 Adding Business Logic to Platform for Convenience

If a Standard Configuration feature requires special handling, first determine whether:

* metadata is insufficient;
* runtime capability is missing;
* an extension point is required.

Hard-coding the business rule into Platform should be the last option.

---

# 26. First Implementation Target

The current implementation sequence has reached Phase 4:

```text
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
```

Phase 4 establishes the generic Object Runtime boundary between Runtime Object Type resolution and Object Instance creation.

The current architectural flow is:

RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
Runtime Object Type
        ↓
ObjectCreator
        ↓
ObjectInstance

The current concrete catalog vertical slice is:

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

Here CatalogRuntime is the current concrete implementation of the generic RuntimeObjectType contract.

It is not the generic Object Runtime itself.

Physical Storage remains outside the Phase 4 implementation boundary.

The purpose of the current implementation is to prove that a metadata-defined object can be resolved and instantiated through the generic Platform runtime without introducing object-type-specific runtime frameworks.

The first implementation should deliberately remain small.

Its purpose is not to make Standard Edition useful yet.

Its purpose is to prove that the fundamental runtime mechanism works.
---

# 27. Transition From Planning to Implementation

The planning stage has transitioned into active implementation.

The architectural baseline is:

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
        Active Implementation

The roadmap is now used as an implementation coordination document rather than as a prerequisite for beginning implementation.

When implementation reveals an architectural limitation, the issue must be handled through the architecture governance process described in this roadmap and the relevant ADRs.

---

# 28. Current Implementation Order

The practical implementation order is:

Step 1

Establish repository and development baseline.

Step 2

Establish Platform runtime foundation.

Step 3

Implement metadata registration, validation and runtime binding.

Step 4

Establish Configuration Lifecycle → Active Configuration → Runtime Configuration Context.

Step 5

Implement MetadataResolver and RuntimeResolver.

Step 6

Establish the generic RuntimeObjectType contract.

Step 7

Implement the generic Object Runtime creation boundary.

Step 8

Create an Assortment Object Instance through the concrete CatalogRuntime vertical slice.

Step 9

Validate Object Identity, Object State, Object Context and Object Lifecycle.

Step 10

Establish the Storage & Persistence Boundary.

Only after the Runtime and Storage boundaries are stable should implementation proceed to operational documents and accounting flows.

---

# 29. Roadmap Success Criteria

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

# 30. Long-Term Extension

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

# 31. Summary

The implementation roadmap follows one central idea:

> **Build the smallest complete system first, then expand it.**

The sequence is:

```text
Repository
    ↓
Runtime Foundation
    ↓
Metadata
    ↓
Configuration & Runtime Resolution
    ↓
Object Runtime
    ↓
Storage
    ↓
Document Runtime
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

The first meaningful implementation milestone is:

A metadata-defined Assortment Object Instance created through the generic Object Runtime.

The first persistence milestone is:

A Runtime Object mapped through the Storage Boundary to a persistent representation.

The first complete business milestone is:

Master Data → Document → Posting → Register → Valuation → Report.
