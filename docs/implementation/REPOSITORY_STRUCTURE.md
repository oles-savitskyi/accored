# Repository Structure

**Project:** AcCoreD
**Stage:** Standard Edition — Design & Implementation Planning
**Status:** Draft
**Architecture Baseline:** `architecture-core-3.0`
**Implementation Strategy:** `IMPLEMENTATION_STRATEGY.md`

---

# 1. Purpose

This document defines the physical repository structure of AcCoreD and establishes the boundaries between:

* Platform implementation;
* Standard Configuration;
* configuration metadata;
* runtime components;
* tests;
* documentation;
* development and tooling infrastructure.

The repository structure must support the architectural principles established by `architecture-core-3.0` and the implementation strategy defined in `IMPLEMENTATION_STRATEGY.md`.

In particular, the repository must make the following dependency direction explicit:

```text
Standard Configuration
        ↓
   Platform API
        ↓
   Platform Core
```

The Platform must never depend on Standard Configuration.

---

# 2. Repository Design Principles

The repository structure follows several principles.

## 2.1 Architectural Boundaries Must Be Visible

The physical repository structure should make major architectural boundaries obvious.

A developer should be able to determine from the directory structure:

* which code belongs to Platform;
* which code belongs to Standard Configuration;
* which code is shared infrastructure;
* which code is tests;
* which files define configuration;
* which files describe the architecture.

---

## 2.2 Platform and Configuration Are Separate

Platform implementation and Standard Configuration must have separate top-level locations.

This prevents gradual architectural erosion in which configuration-specific code starts appearing inside Platform modules.

---

## 2.3 Public Platform APIs Are the Configuration Boundary

Standard Configuration should consume Platform functionality through explicit Platform APIs.

Internal Platform modules must not become an implicit extension mechanism for Standard Configuration.

Conceptually:

```text
┌───────────────────────────────┐
│     Standard Configuration    │
│                               │
│ catalogs / documents / etc.   │
└───────────────┬───────────────┘
                │
                │ public API
                ▼
┌───────────────────────────────┐
│        AcCoreD Platform        │
│                               │
│ runtime / metadata / storage  │
│ posting / registers / etc.    │
└───────────────────────────────┘
```

---

## 2.4 Configuration Definitions Are First-Class Artifacts

Configuration definitions are not ordinary application source code.

They represent metadata describing application behavior.

Therefore they must have a recognizable and stable location in the repository.

---

## 2.5 Tests Follow Architectural Boundaries

Tests should be organized so that it is possible to distinguish:

* Platform unit tests;
* Platform component tests;
* configuration tests;
* integration tests;
* vertical-slice tests.

---

## 2.6 Documentation Is Part of the Repository

Architecture and implementation planning documents are maintained together with the implementation.

The repository therefore contains a dedicated documentation hierarchy.

---

# 3. Proposed Top-Level Structure

The initial repository structure is:

```text
ac-core-d/
│
├── src/
│   ├── accore/
│   │   └── platform/
│   │
│   └── standard/
│
├── tests/
│   ├── unit/
│   ├── component/
│   ├── integration/
│   └── vertical/
│
├── config/
│   └── standard/
│
├── docs/
│   ├── architecture/
│   ├── implementation/
│   └── decisions/
│
├── tools/
│
├── examples/
│
├── scripts/
│
├── pyproject.toml
├── README.md
└── ...
```

This is the initial logical structure.

The exact Python package names may be refined during implementation without changing the architectural boundaries established here.

---

# 4. Source Tree

The source tree contains executable Python code.

```text
src/
├── accore/
│   └── platform/
│
└── standard/
```

The two branches have different responsibilities.

---

# 5. Platform Source

The Platform is located under:

```text
src/accore/platform/
```

The Platform contains generic capabilities and runtime infrastructure.

A preliminary internal structure is:

```text
src/accore/platform/
│
├── foundation/
├── metadata/
├── object_model/
├── runtime/
├── storage/
├── query/
├── documents/
├── posting/
├── registers/
├── valuation/
├── reporting/
├── processing/
├── security/
├── integration/
└── events/
```

This is a **logical module structure**, not a requirement that every directory immediately contain a large implementation.

Modules should be created when implementation begins to require them.

---

# 6. Foundation

```text
platform/foundation/
```

Contains fundamental infrastructure that does not belong to a higher-level business subsystem.

Potential responsibilities include:

* identifiers;
* common types;
* result/error abstractions;
* lifecycle primitives;
* common protocols;
* dependency infrastructure;
* shared utilities.

Foundation must remain deliberately small.

Higher-level business semantics must not be placed here merely because they are reused.

---

# 7. Metadata

```text
platform/metadata/
```

Contains generic metadata infrastructure.

Potential responsibilities include:

* metadata definitions;
* metadata registry;
* metadata loading;
* metadata validation;
* metadata identity;
* metadata lifecycle;
* metadata resolution;
* metadata versioning mechanisms.

The module must describe and manage metadata.

It must not contain Standard Configuration definitions.

For example:

```text
platform/metadata/
    → CatalogDefinition infrastructure
```

but:

```text
standard/
    → Assortment definition
```

---

# 8. Object Model

```text
platform/object_model/
```

Contains generic object model infrastructure.

Potential responsibilities include:

* object identity;
* object state;
* object lifecycle;
* references;
* common object behavior;
* object definitions and runtime bindings.

The object model should remain independent from individual Standard Configuration objects.

---

# 9. Runtime

```text
platform/runtime/
```

Contains mechanisms that execute metadata-defined objects.

Potential responsibilities include:

* runtime object creation;
* runtime context;
* lifecycle management;
* command dispatch;
* runtime services;
* dependency resolution;
* extension points.

The Runtime consumes metadata and provides executable behavior.

Conceptually:

```text
Metadata
    ↓
Runtime
    ↓
Object Behavior
```

---

# 10. Storage

```text
platform/storage/
```

Contains persistence infrastructure.

Potential responsibilities include:

* storage abstractions;
* repositories;
* persistence adapters;
* document storage;
* register storage;
* metadata persistence;
* transaction integration;
* storage lifecycle.

Storage implementations must remain behind defined boundaries.

Business objects should not directly depend on database-specific implementation details.

---

# 11. Query

```text
platform/query/
```

Contains generic query infrastructure.

Potential responsibilities include:

* query model;
* query execution;
* filters;
* sorting;
* projections;
* aggregation;
* result materialization;
* operational query support.

The Query subsystem should be reusable by:

* catalogs;
* documents;
* registers;
* reports;
* processings.

---

# 12. Documents

```text
platform/documents/
```

Contains generic document runtime infrastructure.

Potential responsibilities include:

* document definitions;
* document instances;
* requisites;
* tabular parts;
* document lifecycle;
* document numbering;
* posting integration.

A specific Standard Configuration document must not be implemented here.

For example:

```text
Platform:
    Document Runtime

Standard Configuration:
    Goods Receipt
```

---

# 13. Posting

```text
platform/posting/
```

Contains generic posting infrastructure.

Potential responsibilities include:

* posting context;
* posting lifecycle;
* posting handlers;
* movement generation;
* dependency resolution;
* posting validation;
* posting errors;
* reposting support.

Posting must operate on generic definitions and runtime objects rather than hard-coded Standard Configuration objects.

---

# 14. Registers

```text
platform/registers/
```

Contains generic register infrastructure.

Potential responsibilities include:

* register definitions;
* movement model;
* movement storage;
* totals;
* register lifecycle;
* register queries;
* rebuild/recovery mechanisms.

A Standard Configuration register definition belongs outside Platform.

For example:

```text
Platform:
    Register Runtime
    Totals Engine
    Register Query Engine

Standard Configuration:
    Inventory Register
```

---

# 15. Valuation

```text
platform/valuation/
```

Contains generic valuation infrastructure.

Potential responsibilities include:

* valuation engine;
* valuation methods;
* cost movement processing;
* cost totals;
* valuation queries;
* valuation rebuild/recovery.

The Platform provides valuation capabilities.

Standard Configuration defines which valuation behavior is required for a particular business scenario.

---

# 16. Reporting

```text
platform/reporting/
```

Contains generic reporting runtime.

Potential responsibilities include:

* report data sources;
* datasets;
* dimensions;
* measures;
* report execution;
* report runtime;
* presentation model;
* report queries.

A concrete Standard Configuration report must not be placed here.

---

# 17. Processing

```text
platform/processing/
```

Contains generic Processing infrastructure.

A Processing represents an executable business operation that may orchestrate multiple platform capabilities.

Potential responsibilities include:

* processing definitions;
* processing runtime;
* command execution;
* processing context;
* long-running processing support;
* progress reporting.

Specific Standard Configuration processings belong in Standard Configuration.

---

# 18. Security

```text
platform/security/
```

Contains generic security infrastructure.

Potential responsibilities include:

* authentication integration;
* authorization;
* permissions;
* roles;
* access evaluation;
* security context;
* policy enforcement.

Standard Configuration may define roles, permissions, and security metadata consumed by the Platform.

---

# 19. Integration

```text
platform/integration/
```

Contains generic integration infrastructure.

Potential responsibilities include:

* API infrastructure;
* integration contracts;
* adapters;
* import/export framework;
* external system integration mechanisms.

Concrete integrations should be separated from generic integration infrastructure.

---

# 20. Events

```text
platform/events/
```

Contains the generic event infrastructure defined by Event-Aware Architecture.

The Platform provides:

* event definitions;
* event publication;
* event consumption;
* event context;
* event lifecycle;
* event infrastructure.

The Platform does not assume that the Standard Configuration is event-driven internally.

Events are an architectural integration and extension mechanism.

---

# 21. Standard Configuration Source

Standard Configuration is located under:

```text
src/standard/
```

Its purpose is to define the first AcCoreD business application using Platform capabilities.

A preliminary structure is:

```text
src/standard/
│
├── catalogs/
├── documents/
├── registers/
├── valuation/
├── reports/
├── processings/
├── security/
└── configuration/
```

The exact substructure will be refined after the Configuration Definition Model is designed.

---

# 22. Standard Catalogs

```text
src/standard/catalogs/
```

Contains Standard Configuration catalog definitions and configuration-specific behavior.

The initial catalog direction is:

```text
catalogs/
├── assortment/
├── employees/
├── business_partners/
├── cash_accounts/
└── measure_units/
```

These directories represent configuration objects.

They must use Platform catalog capabilities rather than reimplementing catalog runtime behavior.

---

# 23. Standard Documents

```text
src/standard/documents/
```

Contains concrete Standard Configuration document definitions.

The initial implementation should contain only the documents required by the first vertical slices.

For example:

```text
documents/
└── goods_receipt/
```

Additional documents should be added as required by the implementation roadmap.

---

# 24. Standard Registers

```text
src/standard/registers/
```

Contains concrete register definitions.

For the first MVP, an initial register may be:

```text
registers/
└── inventory/
```

The directory defines the configuration.

The generic register engine remains in:

```text
src/accore/platform/registers/
```

---

# 25. Standard Valuation

```text
src/standard/valuation/
```

Contains Standard Configuration valuation definitions and configuration-specific valuation rules.

Generic valuation mechanisms remain in:

```text
src/accore/platform/valuation/
```

This separation is especially important because valuation architecture explicitly separates the generic valuation engine from the business configuration that uses it.

---

# 26. Standard Reports

```text
src/standard/reports/
```

Contains concrete report definitions.

An initial report might be:

```text
reports/
└── inventory_balance/
```

The generic reporting runtime remains in:

```text
src/accore/platform/reporting/
```

---

# 27. Standard Processings

```text
src/standard/processings/
```

Contains concrete Standard Configuration processings.

The generic Processing runtime remains in:

```text
src/accore/platform/processing/
```

This distinction preserves the principle that Processings are central application behavior while keeping their execution infrastructure generic.

---

# 28. Standard Security

```text
src/standard/security/
```

Contains configuration-specific security definitions.

Examples may include:

* roles;
* permission sets;
* access policies;
* security metadata.

The underlying authorization infrastructure remains in Platform.

---

# 29. Configuration Definitions

Configuration definitions should have a dedicated location.

The initial proposal is:

```text
config/
└── standard/
```

with a conceptual structure such as:

```text
config/
└── standard/
    ├── catalogs/
    ├── documents/
    ├── registers/
    ├── reports/
    ├── processings/
    └── security/
```

However, the exact relationship between:

```text
src/standard/
```

and:

```text
config/standard/
```

is intentionally left open until `CONFIGURATION_DEFINITION_MODEL.md` is designed.

This is an important unresolved design point.

The repository structure must not prematurely hard-code a distinction between:

* executable configuration code;
* declarative configuration metadata;
* generated metadata;
* packaged configuration.

The Configuration Definition Model will establish that boundary.

---

# 30. Tests

Tests are organized by architectural purpose.

```text
tests/
├── unit/
├── component/
├── integration/
└── vertical/
```

---

## 30.1 Unit Tests

```text
tests/unit/
```

Tests isolated algorithms and components.

Examples:

```text
tests/unit/metadata/
tests/unit/valuation/
tests/unit/query/
tests/unit/registers/
```

Unit tests should not require the complete application runtime.

---

## 30.2 Component Tests

```text
tests/component/
```

Tests interactions within a Platform subsystem.

Examples:

```text
tests/component/metadata/
tests/component/storage/
tests/component/posting/
tests/component/registers/
```

---

## 30.3 Integration Tests

```text
tests/integration/
```

Tests architectural boundaries.

Examples:

```text
tests/integration/metadata_runtime/
tests/integration/storage_runtime/
tests/integration/posting_registers/
tests/integration/valuation_registers/
tests/integration/reporting/
```

---

## 30.4 Vertical Tests

```text
tests/vertical/
```

Tests complete business scenarios.

For example:

```text
tests/vertical/
└── inventory/
    └── test_goods_receipt_to_inventory.py
```

A vertical test should exercise as much of the actual runtime as practical.

The first vertical test should eventually demonstrate:

```text
Assortment
    ↓
Goods Receipt
    ↓
Posting
    ↓
Inventory
    ↓
Valuation
    ↓
Report
```

---

# 31. Documentation

Documentation is organized into:

```text
docs/
├── architecture/
├── implementation/
└── decisions/
```

---

## 31.1 Architecture

```text
docs/architecture/
```

Contains the architectural documentation forming the architecture baseline.

Examples include:

* Architecture Overview;
* Metadata Architecture;
* Runtime Architecture;
* Object Architecture;
* Storage Architecture;
* Posting Architecture;
* Register Architecture;
* Valuation Architecture;
* Reporting Architecture;
* Security Architecture;
* Integration Architecture.

---

## 31.2 Implementation

```text
docs/implementation/
```

Contains implementation planning and development documentation.

The initial documents are:

```text
docs/implementation/
├── IMPLEMENTATION_STRATEGY.md
├── REPOSITORY_STRUCTURE.md
├── IMPLEMENTATION_ROADMAP.md
├── MVP_DEFINITION.md
└── CONFIGURATION_DEFINITION_MODEL.md
```

Additional implementation documents may be added as the project progresses.

---

## 31.3 Decisions

```text
docs/decisions/
```

Contains implementation-level decisions that do not belong in the architectural baseline.

Architecturally significant decisions should continue to use ADRs.

The distinction is:

```text
Architecture decision
        ↓
ADR

Implementation decision
        ↓
Implementation documentation / decision record
```

---

# 32. Examples

```text
examples/
```

Contains small examples demonstrating Platform usage.

Examples should preferably demonstrate generic Platform capabilities without introducing Standard Configuration dependencies.

For example:

```text
examples/
├── metadata/
├── catalog/
├── document/
├── register/
└── reporting/
```

Examples are not part of the Standard Configuration.

---

# 33. Tools

```text
tools/
```

Contains development and maintenance tools that are not part of the Platform runtime.

Potential examples:

* metadata inspection;
* configuration validation;
* code generation;
* documentation generation;
* repository analysis;
* benchmark utilities.

Tools must not be imported by production Platform code merely for convenience.

---

# 34. Scripts

```text
scripts/
```

Contains repository-level scripts.

Examples:

* development environment setup;
* test execution;
* linting;
* packaging;
* release preparation;
* repository checks.

Scripts are development infrastructure and are not part of the Platform API.

---

# 35. Dependency Direction

The most important repository-level architectural rule is the dependency direction.

Allowed:

```text
Standard Configuration
        ↓
Platform Public API
        ↓
Platform Implementation
```

Also allowed:

```text
Tests
   ↓
Platform
```

and:

```text
Tests
   ↓
Standard Configuration
   ↓
Platform
```

Not allowed:

```text
Platform
    ↓
Standard Configuration
```

and not allowed:

```text
Platform
    ↓
standard.catalogs
```

The Platform must remain usable without loading Standard Configuration.

---

# 36. Import Boundary

The dependency rule must be enforced at the Python package level.

Conceptually:

```text
accore.platform.*
```

must never import:

```text
standard.*
```

Standard Configuration may import the public Platform API.

Where practical, Standard Configuration should not depend directly on deep internal Platform modules.

Preferred:

```text
standard
   ↓
accore.platform.public_api
```

rather than:

```text
standard
   ↓
accore.platform.storage.internal
```

The exact API packaging mechanism will be determined during implementation.

---

# 37. Public API Boundary

The Platform should eventually expose an explicit public API boundary.

A possible future structure is:

```text
accore/platform/
├── api/
└── internal/
```

or an equivalent package-level API mechanism.

The important architectural requirement is not the exact directory name.

The requirement is:

> Standard Configuration must depend on stable Platform contracts rather than Platform implementation details.

This should be implemented before Standard Configuration becomes large enough to create significant coupling.

---

# 38. Configuration Dependency Rule

Standard Configuration should depend on Platform capabilities, not on Platform implementation details.

For example:

```text
Standard:
    Assortment Definition
          ↓
    Catalog API
          ↓
    Catalog Runtime
```

not:

```text
Standard:
    Assortment
          ↓
    StorageRepositoryImpl
          ↓
    DatabaseAdapter
```

The second form would destroy the intended separation.

---

# 39. Generated Artifacts

Generated artifacts should not normally be treated as authoritative source.

If metadata generation is introduced, the repository must distinguish:

```text
Source Definition
        ↓
Generated Artifact
```

The source definition remains authoritative.

Generated artifacts should be:

* reproducible;
* disposable;
* clearly identified;
* excluded from manual modification.

The exact generation strategy will be determined by `CONFIGURATION_DEFINITION_MODEL.md`.

---

# 40. Packaging Strategy

The repository should eventually support independent conceptual packaging of:

```text
AcCoreD Platform
```

and:

```text
Standard Configuration
```

The exact Python distribution/package strategy will be decided during implementation planning.

The architectural requirement is that Standard Configuration must be replaceable or extensible without modifying Platform source.

This supports the long-term product model:

```text
Platform
   +
Standard Configuration
   +
Optional Configuration Extensions
```

---

# 41. Initial Repository Layout

Combining the preceding sections, the initial target layout is:

```text
ac-core-d/
│
├── src/
│   │
│   ├── accore/
│   │   └── platform/
│   │       ├── foundation/
│   │       ├── metadata/
│   │       ├── object_model/
│   │       ├── runtime/
│   │       ├── storage/
│   │       ├── query/
│   │       ├── documents/
│   │       ├── posting/
│   │       ├── registers/
│   │       ├── valuation/
│   │       ├── reporting/
│   │       ├── processing/
│   │       ├── security/
│   │       ├── integration/
│   │       └── events/
│   │
│   └── standard/
│       ├── catalogs/
│       ├── documents/
│       ├── registers/
│       ├── valuation/
│       ├── reports/
│       ├── processings/
│       ├── security/
│       └── configuration/
│
├── config/
│   └── standard/
│
├── tests/
│   ├── unit/
│   ├── component/
│   ├── integration/
│   └── vertical/
│
├── docs/
│   ├── architecture/
│   ├── implementation/
│   └── decisions/
│
├── examples/
│
├── tools/
│
├── scripts/
│
├── pyproject.toml
├── README.md
└── ...
```

---

# 42. What This Structure Intentionally Does Not Decide

Several implementation details should remain unresolved at this stage.

### 42.1 Exact Configuration Representation

We have not yet decided whether configuration definitions will primarily be represented as:

* Python structures;
* YAML/JSON/TOML;
* a dedicated DSL;
* database metadata;
* a hybrid approach.

This belongs to:

`CONFIGURATION_DEFINITION_MODEL.md`

---

### 42.2 Exact Package Boundaries

The Platform module list is a starting point.

Some modules may later be merged or split based on implementation dependencies.

The architecture boundary must remain stable even if the package structure changes.

---

### 42.3 Plugin / Extension Mechanism

The exact mechanism for external configuration extensions is intentionally postponed.

The architectural requirement is that extensions must not require modification of Platform core.

---

### 42.4 Deployment Packaging

Desktop, server, mobile-client, and other deployment models are not defined by this document.

Repository structure must support them without forcing premature implementation.

---

# 43. Migration From the Current Repository

The repository should not be reorganized into this structure in one large operation.

The migration should follow implementation milestones.

Recommended sequence:

```text
Current Repository
        ↓
Establish Platform package
        ↓
Establish Standard package
        ↓
Move / preserve existing mature Platform code
        ↓
Establish tests
        ↓
Establish documentation structure
        ↓
Introduce first metadata runtime
        ↓
Introduce first Standard Configuration object
```

Existing mature implementation should be preserved where it already satisfies the architecture.

Repository restructuring must not become an excuse for rewriting stable code without a technical reason.

---

# 44. Repository Structure and Vertical Slices

The repository structure should support vertical development.

For example, the first vertical slice may touch:

```text
src/accore/platform/metadata/
src/accore/platform/runtime/
src/accore/platform/storage/
src/standard/catalogs/assortment/
tests/integration/
tests/vertical/
```

This is expected.

A vertical slice does not require placing all related code into one directory.

The architecture remains layered while implementation proceeds vertically across those layers.

---

# 45. Definition of Done for Repository Structure

The repository structure is considered established when:

* Platform and Standard Configuration have separate source roots;
* dependency direction is enforceable;
* Platform modules have clear ownership;
* Standard Configuration objects have clear ownership;
* tests have architectural categories;
* architecture and implementation documentation have dedicated locations;
* configuration definitions have an identified location;
* generated artifacts can be distinguished from source;
* repository tooling is separated from production code.

The exact package-level structure may evolve during implementation.

---

# 46. Relationship to Implementation Strategy

`IMPLEMENTATION_STRATEGY.md` defines the principles.

This document translates those principles into repository boundaries.

```text
IMPLEMENTATION_STRATEGY.md
        │
        ├── Platform / Configuration separation
        │
        ├── Vertical slices
        │
        ├── Capability-first implementation
        │
        └── Dependency direction
                │
                ▼
       REPOSITORY_STRUCTURE.md
                │
                ├── src/accore/platform
                ├── src/standard
                ├── tests
                ├── config
                └── docs
```

---

# 47. Next Step

The next planning document is:

**`IMPLEMENTATION_ROADMAP.md`**

It should convert the implementation strategy and repository structure into a concrete sequence of milestones.

The roadmap should answer:

* what we implement first;
* what depends on what;
* what constitutes completion;
* which vertical slice validates each milestone;
* when Standard Configuration objects are introduced;
* when the MVP becomes runnable.

After that, `MVP_DEFINITION.md` and `CONFIGURATION_DEFINITION_MODEL.md` can establish the exact boundaries and representation of the first Standard Edition.
