# MVP Definition

**Project:** AcCoreD
**Product:** Standard Edition
**Stage:** Standard Edition — Design & Implementation Planning
**Status:** Draft
**Architecture Baseline:** `architecture-core-3.0`
**Implementation Strategy:** `IMPLEMENTATION_STRATEGY.md`
**Repository Structure:** `REPOSITORY_STRUCTURE.md`
**Implementation Roadmap:** `IMPLEMENTATION_ROADMAP.md`

---

# 1. Purpose

This document defines the scope, boundaries, and acceptance criteria of the first working AcCoreD Standard Edition MVP.

The purpose of the MVP is not to provide a complete ERP system.

The purpose is to prove that:

> **AcCoreD Platform can execute a real business lifecycle using a metadata-defined Standard Configuration.**

The MVP therefore prioritizes:

* architectural completeness;
* end-to-end execution;
* metadata-driven behavior;
* correctness;
* demonstrability;
* extensibility.

It deliberately does not prioritize breadth of business functionality.

---

# 2. MVP Philosophy

The first MVP must be:

> **Small in breadth, complete in lifecycle.**

A useful MVP is not:

```text
20 catalogs
10 documents
5 registers
3 reports
```

if those objects do not form a coherent working business scenario.

The preferred MVP is:

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

This demonstrates substantially more architectural value than a large number of isolated objects.

---

# 3. MVP Goal

The primary MVP goal is to demonstrate the following chain:

```text
Standard Configuration
        ↓
Configuration Metadata
        ↓
Metadata Runtime
        ↓
Business Objects
        ↓
Document Processing
        ↓
Posting
        ↓
Register Facts
        ↓
Register Totals
        ↓
Valuation
        ↓
Report
```

The MVP is successful if this chain works using generic Platform capabilities.

---

# 4. Primary Business Scenario

The initial MVP will use a simplified inventory-receipt scenario.

Conceptually:

```text
Business Partner
        │
        │
        ▼
Goods Receipt
        │
        │ contains
        ▼
Assortment + Quantity + Measure Unit
        │
        ▼
Posting
        │
        ▼
Inventory Register
        │
        ├───────────────┐
        ▼               ▼
Quantity State      Valuation
                        │
                        ▼
                   Cost State
                        │
                        ▼
                 Inventory Report
```

The scenario is intentionally narrow.

It is sufficient to validate the central accounting lifecycle without requiring a complete purchasing, sales, warehouse, or financial accounting subsystem.

---

# 5. MVP Configuration

The initial Standard Configuration MVP contains the following conceptual object groups.

## 5.1 Catalogs

Initial catalogs:

1. Assortment
2. Employees
3. Business Partners
4. Cash Accounts
5. Measure Units

Not every catalog must participate directly in the first accounting scenario.

Some are included because they establish the minimum reusable Standard Configuration master-data foundation.

---

# 6. Assortment

**Purpose:** define items whose quantities and values can be accounted for.

The initial Assortment object should support at least:

* identity;
* name;
* active/inactive state;
* hierarchy where applicable;
* referenceability from documents;
* measure unit association where required.

The exact final attribute set belongs to the Configuration Definition Model.

---

# 7. Employees

**Purpose:** provide a minimal representation of internal responsible persons.

The MVP requires only the functionality necessary to:

* define an employee;
* reference an employee from supported objects;
* preserve employee identity.

Advanced HR functionality is outside the MVP.

---

# 8. Business Partners

**Purpose:** represent external counterparties.

The MVP should support:

* identity;
* name;
* active/inactive state;
* basic classification if required;
* reference from documents.

Advanced CRM, partner relationship management, contact management, and similar functionality are outside the MVP.

---

# 9. Cash Accounts

**Purpose:** establish the initial Standard Configuration master-data model for cash-related accounts.

The MVP does not require a complete cash-management subsystem.

Cash Accounts are included primarily to establish a reusable configuration object and prepare the Standard Configuration for future financial scenarios.

No cash document lifecycle is required for MVP completion unless later implementation demonstrates that it is necessary for another MVP requirement.

---

# 10. Measure Units

**Purpose:** provide standardized quantity measurement.

The MVP should support:

* unit identity;
* name;
* abbreviation/symbol;
* basic quantity semantics;
* reference from Assortment and document lines.

The complete unit-conversion system is not required unless it becomes necessary for the first business scenario.

---

# 11. First Operational Document

The MVP requires one operational document.

Initial candidate:

**Goods Receipt**

The document represents the receipt of assortment quantities from a Business Partner.

---

## 11.1 Goods Receipt Header

The minimum conceptual header includes:

* document identity;
* date/time;
* Business Partner;
* responsible Employee where required;
* document state;
* posting state.

---

## 11.2 Goods Receipt Tabular Part

The minimum line model includes:

* Assortment;
* quantity;
* Measure Unit;
* unit cost/value information required by the selected valuation scenario.

The exact financial attributes will be defined by the Configuration Definition Model and Valuation implementation.

---

# 12. Document Lifecycle

The MVP must demonstrate at least:

```text
Draft
  ↓
Posted
```

and the ability to reverse or repost the document according to the implemented Posting Architecture.

The MVP does not require a complete workflow engine.

---

# 13. Posting

Goods Receipt must be capable of producing accounting facts through the generic Posting Architecture.

The conceptual flow is:

```text
Goods Receipt
      ↓
Posting Context
      ↓
Posting Handler
      ↓
Register Movements
```

Posting must not directly manipulate register totals.

It produces movements.

The Register/Totals infrastructure remains responsible for maintaining register state.

---

# 14. Inventory Register

The MVP requires one quantity register:

**Inventory**

Its purpose is to represent quantity state.

The initial register should contain the minimum dimensions and resources necessary for:

* Assortment;
* relevant organizational/storage dimension if required;
* quantity.

The exact dimensional model will be finalized during implementation.

---

# 15. Inventory Facts

The MVP must establish the architectural principle:

> **Registers are the source of quantity state.**

The quantity state visible to operational queries must be derived from register facts and/or their materialized totals according to the Register Architecture.

The application must not maintain a separate hidden quantity state outside the register model.

---

# 16. Register Totals

The MVP must support materialized register totals sufficient for operational balance queries.

The initial implementation may use a simple totals strategy.

The full adaptive totals optimization strategy does not need to be completely implemented in the first MVP.

The important requirement is correctness and compatibility with the established Register Architecture.

---

# 17. Inventory Query

The MVP must provide an operational query capable of answering at least:

> What quantity of a particular Assortment item is currently available according to the Inventory Register?

The query should support the relevant dimensions established by the register definition.

---

# 18. Valuation

The MVP must demonstrate that quantity accounting and valuation are separate concerns.

The conceptual flow is:

```text
Inventory Facts
      ↓
Valuation Engine
      ↓
Cost Facts
      ↓
Cost Totals
      ↓
Cost Query
```

The MVP requires at least one working valuation method.

The implementation should initially select the simplest valuation method that:

* is architecturally representative;
* supports the first inventory scenario;
* can demonstrate delayed cost processing.

The exact valuation method is an implementation decision and must not be allowed to distort the broader architecture.

---

# 19. Delayed Cost Scenario

The MVP should include at least one test scenario demonstrating delayed cost information.

Conceptually:

```text
Receive 100 units
       ↓
Quantity fact exists
       ↓
20 units consumed/sold
       ↓
Additional cost information arrives
       ↓
Valuation recalculates affected cost
       ↓
Cost history remains consistent
```

If the first MVP business scenario does not yet require consumption/sale, the valuation test may use a smaller synthetic scenario specifically for validating the delayed-cost architecture.

This distinction is important:

> The MVP does not need a complete Sales subsystem merely to validate delayed valuation.

---

# 20. Cost State

The MVP must distinguish:

```text
Quantity State
```

from:

```text
Cost State
```

Quantity is provided by the Register subsystem.

Cost is produced and maintained by the Valuation subsystem.

The MVP must not collapse these into one generic numeric balance.

---

# 21. Inventory Report

The MVP requires at least one report.

Initial candidate:

**Inventory Balance**

The report should demonstrate:

* data source definition;
* dataset;
* dimensions;
* measures;
* report execution;
* presentation result.

At minimum, it should expose relevant inventory quantities and, where valuation is already available, corresponding values.

---

# 22. Processing

The MVP requires at least one meaningful Processing.

The Processing should exercise existing Platform capabilities rather than merely demonstrate that a button can invoke a function.

A suitable initial candidate is:

**Inventory / Valuation Rebuild or Validation Processing**

Potential responsibilities include:

* validation;
* controlled rebuild;
* recalculation;
* diagnostic execution.

The exact Processing should be selected during implementation based on the first operational scenario.

---

# 23. Security

The MVP requires basic security infrastructure.

At minimum:

* security context;
* authenticated actor representation;
* authorization check;
* basic role/permission model;
* rejection of unauthorized operations.

The MVP does not require:

* enterprise identity federation;
* complex organizational security;
* advanced segregation-of-duties rules;
* full administrative security UI.

---

# 24. Integration

The MVP requires only minimal integration support.

At least one stable external boundary should be demonstrable.

The preferred first integration surface is a contract-first API capable of exposing a supported read or business operation.

The MVP does not require a large integration catalog.

The objective is to validate that Platform functionality can be exposed through a stable contract without bypassing the application runtime.

---

# 25. User Interface

The MVP UI should be deliberately limited.

The UI exists to demonstrate and operate the runtime.

It is not the primary architectural validation target.

The minimum usable UI should allow, where applicable:

1. view/create Assortment;
2. view/create Business Partner;
3. create Goods Receipt;
4. post Goods Receipt;
5. inspect Inventory;
6. run Inventory Balance report.

The presentation layer must consume runtime capabilities rather than implement independent business logic.

---

# 26. Configuration-Driven Requirement

A central MVP acceptance criterion is that Standard Configuration objects must be represented as configuration definitions/metadata.

The MVP should therefore avoid implementing:

```text
Assortment
Goods Receipt
Inventory
Inventory Balance
```

as isolated hard-coded application subsystems.

Instead:

```text
Configuration Definition
        ↓
Metadata
        ↓
Generic Runtime
        ↓
Object Behavior
```

must be the dominant mechanism.

---

# 27. Platform Requirements for MVP

The following Platform capabilities are required.

### Foundation

* identity;
* common types;
* lifecycle;
* error handling.

### Metadata

* definitions;
* registry;
* validation;
* resolution.

### Runtime

* runtime context;
* object creation;
* lifecycle;
* service access.

### Storage

* persistence;
* transactions where required;
* object storage;
* register storage.

### Query

* filtering;
* sorting;
* projection;
* aggregation where required.

### Catalog Runtime

* definition;
* CRUD;
* hierarchy;
* query.

### Document Runtime

* definition;
* requisites;
* tabular parts;
* lifecycle;
* numbering.

### Posting

* posting context;
* handlers;
* movement generation;
* validation.

### Registers

* movements;
* totals;
* balance queries.

### Valuation

* valuation engine;
* one method;
* cost movements;
* cost totals;
* queries.

### Reporting

* data sources;
* datasets;
* dimensions;
* measures;
* execution.

### Processing

* definition;
* runtime;
* execution context.

### Security

* context;
* authorization;
* permissions.

### Integration

* minimum API contract/runtime.

---

# 28. Explicitly Excluded From MVP

The following functionality is explicitly outside the first MVP unless implementation proves that a particular item is required by the core scenario.

## Business Functionality

* complete sales subsystem;
* complete purchasing subsystem;
* complete warehouse management;
* complete cash management;
* payroll;
* HR management;
* CRM;
* budgeting;
* fixed assets;
* production management;
* advanced tax accounting.

---

## Advanced Documents

* complex sales documents;
* payment documents;
* bank operations;
* inventory transfer scenarios;
* inventory adjustment suite;
* complex procurement lifecycle.

---

## Advanced Registers

* large register families;
* complex accumulation models;
* advanced periodic snapshots;
* highly optimized adaptive totals strategies.

---

## Advanced Valuation

* every possible valuation method;
* complex multi-stage cost allocation;
* advanced parallel valuation scenarios;
* all correction/rebuild strategies.

One correct representative valuation method is sufficient for the MVP.

---

## Advanced Reporting

* report designer;
* dashboards;
* advanced visualization;
* OLAP-style analytical tooling;
* scheduled reporting;
* report subscriptions.

---

## Advanced Security

* enterprise SSO;
* federated identity;
* advanced organizational access structures;
* sophisticated segregation of duties.

---

## Advanced Integration

* large connector ecosystem;
* enterprise message brokers;
* complex external synchronization;
* mobile-specific integration;
* third-party ERP connectors.

---

## Advanced UI

* full application designer;
* extensive personalization;
* advanced themes;
* complex dashboards;
* mobile UI.

---

# 29. MVP Architecture Validation

The MVP must validate the following architectural principles.

| Principle                                         | MVP Validation                                                  |
| ------------------------------------------------- | --------------------------------------------------------------- |
| Metadata-Driven Architecture                      | Standard objects are metadata-defined                           |
| Runtime / Metadata Separation                     | Definitions are executed by generic runtime                     |
| Hybrid Storage Model                              | Business objects and registers use defined storage architecture |
| ULID Identity Model                               | Runtime/business identities use ULID                            |
| Posting Produces Register Facts                   | Goods Receipt generates movements                               |
| Registers Are Source of Quantity State            | Inventory comes from register facts/totals                      |
| Valuation Is Independent From Quantity Accounting | Cost processing is separate                                     |
| Cost Facts May Arrive After Quantity Facts        | Delayed cost scenario                                           |
| Cost Is Produced By Valuation Engine              | Valuation creates cost facts                                    |
| Operational Queries Use Materialized Results      | Inventory balance uses totals                                   |
| Audit Queries Use Valuation Facts                 | Cost history remains queryable                                  |
| Processings Are Central                           | At least one meaningful processing                              |
| Contract-first API                                | At least one external operation uses a contract                 |
| Event-Aware Architecture                          | Event infrastructure is demonstrable where required             |

---

# 30. MVP Vertical Scenario

The primary acceptance scenario is:

```text
1. Load Standard Configuration
             ↓
2. Create Measure Unit
             ↓
3. Create Assortment
             ↓
4. Create Business Partner
             ↓
5. Create Goods Receipt
             ↓
6. Add Assortment lines
             ↓
7. Save document
             ↓
8. Post document
             ↓
9. Generate Inventory movements
             ↓
10. Update Inventory totals
             ↓
11. Query Inventory balance
             ↓
12. Run Valuation
             ↓
13. Query Cost state
             ↓
14. Execute Inventory Balance report
```

This is the primary MVP demonstration scenario.

---

# 31. MVP Validation Scenario for Delayed Cost

A separate architectural validation scenario should demonstrate:

```text
Initial Quantity Fact
        ↓
Initial Cost
        ↓
Quantity Consumption
        ↓
Delayed Additional Cost
        ↓
Valuation Adjustment
        ↓
Updated Cost State
```

This scenario may use test fixtures rather than additional Standard Configuration documents if implementing a full consumption document would unnecessarily expand the MVP.

The objective is to validate Valuation Architecture, not to introduce a complete Sales subsystem.

---

# 32. MVP Data Lifecycle

The MVP must demonstrate the following lifecycle:

```text
Definition
    ↓
Metadata
    ↓
Instance
    ↓
Persistence
    ↓
Business Event
    ↓
Posting
    ↓
Register Fact
    ↓
Materialized State
    ↓
Valuation Fact
    ↓
Report
```

Each stage must have an identifiable owner.

---

# 33. MVP Error Handling

The MVP must handle at least:

* invalid metadata;
* invalid object data;
* missing required fields;
* invalid document state;
* posting failure;
* invalid register movement;
* valuation failure;
* unauthorized operation.

Errors should be explicit and diagnosable.

Silent failure is not acceptable.

---

# 34. MVP Transaction Boundaries

The MVP must define transaction behavior for the primary lifecycle.

At minimum, the implementation must prevent a successful document posting from producing only a partial set of required register facts.

Conceptually:

```text
Document Posting
      │
      ├── Movement A
      ├── Movement B
      └── Movement C
             │
             ▼
       Atomic Outcome
```

The exact transaction mechanism belongs to Storage/Posting implementation.

The business requirement is consistency.

---

# 35. MVP Rebuild and Recovery

The MVP must demonstrate at least basic rebuild/recovery capabilities for:

* register totals;
* valuation-derived state where applicable.

A rebuild should be capable of reconstructing derived state from authoritative facts.

Conceptually:

```text
Authoritative Facts
        ↓
      Rebuild
        ↓
Derived State
```

This is especially important because totals and valuation state must not become unrecoverable sources of truth.

---

# 36. MVP Observability

The MVP must provide enough observability to diagnose the primary lifecycle.

At minimum, it should be possible to identify:

* configuration loading errors;
* metadata validation errors;
* document lifecycle failures;
* posting failures;
* register movement errors;
* valuation errors;
* report execution errors.

The implementation should establish a consistent logging/error model before the MVP becomes large.

---

# 37. MVP Performance Expectations

The MVP is not a performance benchmark release.

However, it must establish a measurable baseline.

At minimum, benchmarks should eventually cover:

* configuration loading;
* metadata resolution;
* object creation;
* document posting;
* register balance query;
* valuation execution;
* report execution.

The purpose is to establish baseline measurements rather than to optimize prematurely.

---

# 38. MVP Acceptance Criteria

The MVP is accepted only when all of the following are true.

## Configuration

* Standard Configuration loads successfully;
* metadata validates successfully;
* configuration objects are resolvable by runtime.

## Master Data

* Assortment works;
* Business Partners work;
* Measure Units work;
* required Employee functionality works.

## Documents

* Goods Receipt works;
* requisites work;
* tabular parts work;
* lifecycle works;
* persistence works.

## Posting

* Goods Receipt can be posted;
* posting produces register movements;
* posting errors are handled.

## Registers

* Inventory movements are stored;
* totals are maintained;
* inventory balances can be queried.

## Valuation

* at least one valuation method works;
* cost facts are produced;
* cost state can be queried;
* delayed-cost scenario is represented.

## Reporting

* Inventory Balance report executes successfully.

## Processing

* at least one meaningful Processing executes successfully.

## Security

* authorization is enforced for at least the primary business operations.

## Integration

* at least one contract-first API operation works.

## Recovery

* derived register state can be rebuilt;
* relevant valuation state can be rebuilt or reconstructed.

## Testing

* unit tests pass;
* component tests pass;
* integration tests pass;
* vertical MVP scenario passes.

---

# 39. MVP Non-Goals

The following are explicitly not MVP success criteria:

* number of catalogs;
* number of documents;
* number of reports;
* visual completeness;
* support for every accounting scenario;
* enterprise deployment;
* maximum performance;
* complete ERP functionality;
* complete mobile support.

The MVP succeeds by proving the architecture and the complete business lifecycle.

---

# 40. MVP Definition of Done

The MVP is considered complete when a fresh environment can perform:

```text
Install
   ↓
Load Configuration
   ↓
Create Master Data
   ↓
Create Document
   ↓
Post
   ↓
Inspect Register
   ↓
Run Valuation
   ↓
Run Report
```

without:

* manually modifying Platform internals;
* inserting undocumented database records;
* bypassing runtime;
* implementing Standard Configuration behavior directly inside Platform.

---

# 41. MVP Release Boundary

The MVP represents the first **working Standard Edition**, not the final Standard Edition product.

The expected product evolution is:

```text
MVP
 ↓
Standard Edition 1.x
 ↓
Standard Edition 2.x
 ↓
Expanded Business Configuration
```

The Platform should evolve in parallel where generic capabilities are required.

---

# 42. Relationship to the Platform

The MVP must prove that Standard Configuration is a consumer of Platform capabilities.

The intended architecture is:

```text
┌────────────────────────────────────┐
│       Standard Edition MVP         │
│                                    │
│ Assortment                         │
│ Business Partners                  │
│ Goods Receipt                      │
│ Inventory                          │
│ Valuation                          │
│ Inventory Report                   │
└─────────────────┬──────────────────┘
                  │
                  │ configuration
                  │ + public APIs
                  ▼
┌────────────────────────────────────┐
│          AcCoreD Platform           │
│                                    │
│ Metadata                           │
│ Runtime                            │
│ Storage                            │
│ Documents                          │
│ Posting                            │
│ Registers                          │
│ Valuation                          │
│ Reporting                          │
│ Processing                         │
│ Security                           │
│ Integration                       │
└────────────────────────────────────┘
```

The MVP should therefore be considered a **Platform validation application** as well as a product prototype.

---

# 43. Relationship to Configuration Definition Model

This document defines **what objects the MVP needs**.

`CONFIGURATION_DEFINITION_MODEL.md` will define **how those objects are represented**.

The relationship is:

```text
MVP_DEFINITION.md
        │
        │ defines required objects
        ▼
CONFIGURATION_DEFINITION_MODEL.md
        │
        │ defines representation
        ▼
Standard Configuration
        │
        ▼
Platform Runtime
```

The Configuration Definition Model must therefore be capable of representing at least:

* Catalog;
* Document;
* Tabular Part;
* Register;
* Report;
* Processing;
* Security definition;
* relevant valuation configuration.

---

# 44. First MVP Object Set

The initial object set is intentionally small:

```text
Catalogs
├── Assortment
├── Employees
├── Business Partners
├── Cash Accounts
└── Measure Units

Documents
└── Goods Receipt

Registers
└── Inventory

Valuation
└── One initial valuation method

Reports
└── Inventory Balance

Processings
└── One operational/rebuild/validation processing
```

This object set is the current MVP target.

It may be adjusted only if implementation demonstrates a concrete dependency that cannot be satisfied without an additional object.

---

# 45. Scope Change Rule

Any proposed addition to the MVP should answer three questions:

1. **Which required MVP scenario needs it?**
2. **Which existing Platform capability cannot provide it?**
3. **What is the smallest alternative?**

If the feature is not required for the primary lifecycle or architectural validation, it should normally be deferred.

This rule protects the MVP from uncontrolled scope expansion.

---

# 46. Success Beyond the MVP

The ultimate purpose of the MVP is to prove that additional Standard Configuration objects can be added without redesigning the Platform.

After the MVP, adding a new catalog should conceptually look like:

```text
New Catalog Definition
        ↓
Metadata
        ↓
Existing Catalog Runtime
```

Adding a new document:

```text
New Document Definition
        ↓
Metadata
        ↓
Existing Document Runtime
        ↓
Existing Posting Infrastructure
```

Adding a new report:

```text
New Report Definition
        ↓
Existing Reporting Runtime
```

If each new feature requires modifying Platform internals, the MVP should be considered architecturally incomplete even if its business scenario works.

---

# 47. Final MVP Statement

The AcCoreD Standard Edition MVP is defined as:

> **A small metadata-driven Standard Configuration capable of executing a complete inventory business lifecycle — from master data and an operational document through posting, quantity accounting, valuation, and reporting — on top of the generic AcCoreD Platform.**

The MVP is intentionally not a complete ERP.

Its purpose is to demonstrate that the AcCoreD architecture can produce a real, executable, extensible business application.

The primary proof is:

```text
Configuration
      ↓
Metadata
      ↓
Runtime
      ↓
Master Data
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

This lifecycle is the principal acceptance criterion for the first Standard Edition release.
