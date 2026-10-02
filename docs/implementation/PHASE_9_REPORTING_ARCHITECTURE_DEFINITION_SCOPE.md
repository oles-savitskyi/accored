# PHASE 9 — WP-9 Reporting Architecture Definition / Scope

**Status:** Approved and implemented through Slice #7

**Baseline:** AcCoreD `main` after WP-8 completion

**Baseline commits:**

- `5046a9c` — `feat(valuation): complete WP-8 Slice 10.7 repost recovery`
- `1812ad5` — `docs(phase8): finalize WP-8 documentation reconciliation`

**Review status:** Architecture Review completed; amendments incorporated

**Implementation status:** Completed through Slice #7; Slice #8 documentation reconciliation and final quality gate completed

---

## 1. Purpose

This document defines the architectural boundary, scope, responsibilities, invariants, integration points, and first executable vertical slice for **WP-9 — Reporting**.

The document is intentionally an architecture definition rather than an API design. It establishes **what Reporting owns, what it consumes, what it produces, and where its boundaries lie**. Concrete classes, protocols, method signatures, module layout, and implementation sequencing belong to the subsequent Concrete API Design.

WP-9 starts from the completed WP-8 baseline. WP-8 established immutable valuation facts, operation records, reversal/repost semantics, derived-state recovery, and rebuild behavior. Reporting must consume those results without acquiring ownership of valuation mutation or recovery.

---

# 2. Architectural Baseline

## 2.1 Repository baseline

The current repository contains an architectural Reporting documentation set under `docs/architecture/reporting/`, while `src/accore/platform/reporting/` currently contains only the package initializer.

Therefore WP-9 is a new executable Platform subsystem rather than an incremental extension of an already implemented Reporting runtime.

The existing Reporting documents are treated as architectural input, not as evidence that every described runtime component already exists.

## 2.2 Existing domain/platform capabilities

WP-9 integrates with existing semantic read capabilities, including Register query/balance services and Valuation consumption/result structures. Reporting must consume these capabilities through explicit read-oriented contracts or adapters rather than reaching into their persistence or mutation internals.

The following remain outside Reporting ownership:

- register mutation;
- posting;
- valuation calculation;
- valuation operation lifecycle;
- valuation fact persistence;
- valuation recovery;
- derived-state rebuild ownership.

## 2.3 Existing conceptual Reporting architecture

The repository already defines the intended long-term concepts:

- logical data sources;
- declarative dataset definitions;
- dimensions;
- measures;
- report validation and compilation;
- execution plans;
- dataset-oriented execution;
- presentation/dataset separation.

WP-9 adopts these concepts where they are consistent with the executable Platform baseline, but does **not** assume that conceptual infrastructure such as a generic Table Engine or Expression Engine already exists.

---

# 3. Problem Statement

AcCoreD now has accounting-domain state that can be queried semantically, including register movements/balances and valuation-derived cost information. The platform needs a generic, read-only analytical subsystem that can transform those domain results into deterministic, platform-neutral datasets without coupling reports to storage structures or business mutation workflows.

The Reporting subsystem must provide a stable boundary between:

1. domain/platform read semantics;
2. declarative analytical report definitions;
3. runtime execution;
4. analytical datasets;
5. future presentation, export, UI, and integration consumers.

The first implementation must establish this boundary with a real end-to-end vertical slice rather than merely introducing metadata classes.

---

# 4. Architectural Goals

WP-9 has the following goals.

## G-1. Establish a generic Platform Reporting subsystem

Introduce an executable `accore.platform.reporting` subsystem with clear metadata, runtime, data-source, and dataset boundaries.

## G-2. Keep Reporting read-only

Reporting must not create, modify, compensate, reverse, repost, or recover accounting or valuation state.

## G-3. Consume logical data sources

Reports operate on logical analytical data sources rather than physical persistence structures.

## G-4. Establish declarative report execution

Report definitions describe the requested analytical result. Runtime execution translates the definition into executable runtime structures and produces a dataset.

## G-5. Establish Dataset as the output boundary

Every successful report execution produces an immutable, platform-neutral analytical dataset.

## G-6. Integrate Register and Valuation semantically

The first meaningful vertical slice must demonstrate that Reporting can compose existing Register and Valuation read semantics without taking ownership of their domain logic.

## G-7. Preserve Metadata/Runtime separation

Metadata definitions remain independent from executable runtime structures.

## G-8. Preserve Platform/Standard separation

Generic Reporting concepts and runtime contracts belong to `accore.platform.reporting`. Standard-specific reports and adapters belong to the Standard composition layer.

## G-9. Define cross-source consistency explicitly

When a report consumes multiple logical sources, the execution contract must state what read consistency is guaranteed. Reporting must not imply transaction-level atomicity that its sources do not provide.

## G-10. Establish a foundation for future presentation and analytical capabilities

The architecture must remain compatible with future table, pivot, chart, export, dashboard, expression, caching, and OLAP capabilities without requiring those capabilities to be implemented in WP-9.

---

# 5. Non-Goals

The following are explicitly outside the executable scope of WP-9 unless a later approved amendment states otherwise.

## NG-1. Accounting mutation

Reporting does not create or mutate register movements, balances, posting results, or accounting facts.

## NG-2. Valuation calculation

Reporting does not perform FIFO or any other valuation method and does not calculate valuation facts or results.

## NG-3. Valuation recovery/rebuild

Reporting does not repair incomplete or indeterminate valuation state. Recovery and rebuild remain Valuation responsibilities.

## NG-4. Physical persistence abstraction

Reporting does not become a second persistence framework and does not expose storage-provider details to report definitions.

## NG-5. Full presentation/rendering framework

WP-9 does not implement:

- UI rendering;
- Qt/Web rendering;
- PDF generation;
- Excel generation;
- chart rendering;
- dashboards;
- interactive presentation widgets.

## NG-6. Full generic Expression Engine

The architecture may define calculated-measure integration points, but WP-9 does not create a platform-wide expression engine unless a separate approved architectural decision makes it part of scope.

## NG-7. Full generic Table Engine

WP-9 does not assume or require an existing generic Table Engine. Dataset processing required by the first vertical slice may be implemented behind Reporting runtime contracts, without prematurely creating a platform-wide analytical engine.

## NG-8. Cost-based query optimization

Execution plans are explicit runtime artifacts, but WP-9 does not require a cost-based optimizer, physical query planner, or advanced plan optimization.

## NG-9. Distributed analytical execution

No distributed execution, OLAP server, data warehouse, or external analytical backend is part of WP-9.

## NG-10. Reporting security model

Reporting integrates with the existing platform security/authorization architecture but does not invent a parallel security model.

---

# 6. Architectural Boundary

The target boundary is:

```text
Register / Valuation semantic read contracts
                │
                ▼
       Logical Data Sources
                │
                ▼
        Report Definition
        ┌───────┼────────┐
        ▼       ▼        ▼
   Dimensions Measures Filters
        └───────┼────────┘
                ▼
       Validation / Compilation
                │
                ▼
         Execution Plan
                │
                ▼
        Reporting Runtime
                │
                ▼
      Analytical Dataset
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
       UI     Export     API
      future   future   future
```

The most important boundary is between **logical data sources** and their underlying domain/persistence implementations.

Reporting may consume:

- register movements;
- register balances/totals;
- valuation-derived cost movements/results;
- other future logical analytical sources.

Reporting must not depend directly on:

- register persistence implementations;
- valuation fact persistence implementations;
- storage providers;
- mutation orchestrators;
- posting coordinators;
- valuation coordinators.

---

# 7. Ownership Model

## 7.1 Reporting owns

Reporting owns:

- report definition semantics;
- analytical dimensions and measures as report metadata;
- logical data-source contracts;
- report validation;
- report compilation/runtime representation;
- execution-plan representation;
- report execution orchestration;
- analytical dataset representation;
- reporting-specific execution errors/results.

## 7.2 Register owns

Register owns:

- movement facts;
- register totals/balances;
- register mutation;
- register rebuild/maintenance;
- register-specific query semantics.

## 7.3 Valuation owns

Valuation owns:

- valuation facts;
- valuation results;
- valuation operation records;
- valuation lifecycle;
- reversal/repost semantics;
- valuation recovery;
- valuation derived-state rebuild;
- valuation-specific cost semantics.

## 7.4 Standard owns

Standard may own:

- Standard-specific report definitions;
- Standard-specific logical data-source adapters;
- composition of Register + Valuation sources for Standard business reports;
- Standard configuration of Reporting services.

Generic Reporting contracts must remain free of Standard-specific accounting assumptions.

---

# 8. Logical Data Source Architecture

A **Logical Data Source** is the primary integration boundary between Reporting and an underlying domain/platform capability.

A logical data source exposes analytical semantics, not physical storage.

At minimum, a source must be able to describe its logical schema sufficiently for Reporting to validate a report definition and execute the requested read operation.

The logical schema may describe:

- fields;
- field types;
- dimensions;
- measures;
- source relationships where required;
- supported filtering/grouping semantics where required by the execution model.

Conceptually:

```text
Logical Data Source
    ├── schema
    ├── fields
    ├── dimensions
    ├── measures
    └── read semantics
```

The concrete API must decide the exact protocol boundaries. This document deliberately does not prescribe class names or method signatures.

### Architectural rule

> A report may depend on the semantic schema of a logical source, but never on the physical representation used to obtain that source's data.

---

# 9. Analytical Model

The analytical model is based on **Dimensions** and **Measures**.

```text
Dimensions × Measures → Analytical Dataset
```

## 9.1 Dimensions

A Dimension is an analytical axis used for classification, grouping, filtering, and navigation.

Examples include:

- product;
- warehouse;
- customer;
- period;
- region;
- department;
- project.

Dimensions are metadata concepts and are independent from presentation layout.

## 9.2 Measures

A Measure is an analytical value exposed by a source or calculated from report/runtime data.

Examples include:

- quantity;
- amount;
- cost;
- balance.

Aggregation semantics are part of the measure's analytical meaning.

## 9.3 Hierarchies

The architecture permits dimension hierarchies for future drill-down and roll-up scenarios. Hierarchy navigation is not required for the first executable vertical slice.

---

# 10. Report Definition Model

A Report Definition is declarative metadata describing the desired analytical result.

Conceptually it combines:

```text
Report Definition
    ├── data sources
    ├── filters
    ├── dimensions
    ├── measures
    └── execution-relevant parameters
```

The definition describes **what** is required, not the concrete execution algorithm.

The execution runtime owns the translation from definition to executable runtime structures.

---

# 11. Validation and Compilation

Report execution follows this architectural lifecycle:

```text
Report Definition
        ↓
Validation
        ↓
Compilation
        ↓
Execution Plan
        ↓
Runtime Execution
        ↓
Analytical Dataset
```

## 11.1 Validation

Validation verifies that the requested report is semantically executable, including where applicable:

- source existence;
- field references;
- dimension references;
- measure references;
- filter validity;
- parameter validity;
- aggregation compatibility;
- source compatibility.

Invalid definitions must fail before successful dataset execution.

## 11.2 Compilation

Compilation converts validated metadata into runtime structures.

The initial implementation should keep compilation explicit but lightweight. It does not require an advanced compiler framework.

## 11.3 Execution Plan

An execution plan is an immutable runtime artifact describing the operations required to produce the dataset.

The initial plan may represent operations such as:

```text
Source
Filter
Projection
Group
Aggregate
Calculate
Sort
```

Only operations required by the first vertical slice must be implemented.

---

# 12. Reporting Runtime

The Reporting Runtime is responsible for orchestration of report execution.

Its responsibilities are:

- accept a validated execution request;
- resolve logical data sources;
- execute the compiled plan;
- coordinate dataset processing;
- produce the resulting dataset;
- surface deterministic execution outcomes.

The runtime does not own metadata storage, business state, register state, valuation state, or presentation rendering.

### Runtime principle

> The runtime executes report semantics; it does not become the owner of the business semantics supplied by its data sources.

---

# 13. Dataset Boundary

A successful report execution produces an **Analytical Dataset**.

The dataset is:

- immutable from the consumer's perspective;
- platform-neutral;
- independent from physical storage;
- independent from UI/rendering;
- suitable for deterministic testing;
- suitable for future API/export/presentation consumers.

Conceptually:

```text
Report Runtime
      │
      ▼
Analytical Dataset
      │
      ├── future UI
      ├── future export
      ├── future API
      └── future analytical consumers
```

The dataset is the stable hand-off boundary between report execution and presentation/integration concerns.

---

# 14. Cross-Source Consistency Semantics

A report may consume more than one logical source. WP-9 must not imply stronger consistency than the source contracts can guarantee.

For the initial implementation:

1. each logical source provides a defined read view for an execution;
2. Reporting executes against those source read views;
3. the report result is deterministic for the selected source inputs;
4. cross-source reads are **not** implicitly treated as one atomic transaction unless an explicit source contract provides such a snapshot;
5. Reporting does not create a synthetic transaction over Register and Valuation.

Therefore an Inventory-oriented report may compose Register and Valuation data, but its consistency guarantee is the intersection of the guarantees provided by those logical sources.

If a source cannot provide a valid read view because its state is unavailable or otherwise not readable, Reporting must surface an explicit source/execution failure rather than silently reconstructing or repairing the source state.

This is a deliberate architectural boundary inherited from the ownership established in WP-8.

---

# 15. Inventory-Oriented First Vertical Slice

The first executable Reporting vertical slice should demonstrate a meaningful cross-domain analytical result based on existing Register and Valuation read semantics.

The target conceptual flow is:

```text
Register semantic read
        │
        ├── quantity / movement / balance information
        │
        ▼
Valuation semantic read
        │
        ├── cost / valuation result information
        │
        ▼
Logical source composition
        │
        ▼
Report Definition
        │
        ▼
Execution
        │
        ▼
Inventory-oriented Dataset
```

Reporting may correlate and present values from these sources, but it must not reproduce valuation algorithms or invent accounting semantics.

For example, Reporting must not independently implement FIFO cost calculation merely because a report contains quantity and cost information. Cost semantics remain owned by Valuation.

A concrete `InventoryBalance` or equivalent Standard report is a candidate for the first real report, subject to the API Design review.

---

# 16. Derived-State Visibility and Failure Semantics

Reporting does not repair derived state.

If an authoritative or derived source is unavailable, indeterminate, or otherwise cannot satisfy its read contract, Reporting must not:

- rebuild the source;
- rerun valuation;
- compensate facts;
- mutate operation records;
- delete historical facts.

Instead, the logical data source boundary must return an explicit read/execution failure that the Reporting runtime propagates as an unsuccessful report execution.

This preserves the WP-8 ownership model:

```text
Valuation recovery/rebuild → Valuation
Report consumption         → Reporting
```

---

# 17. Immutability Invariants

The following invariants are mandatory.

### I-1. Historical valuation facts are never mutated by Reporting.

### I-2. Reporting never performs accounting mutation.

### I-3. Report definitions are metadata, not mutable runtime state.

### I-4. Execution plans are runtime artifacts and do not mutate report definitions.

### I-5. Successful report execution produces a dataset that is immutable to consumers.

### I-6. Reporting does not repair or rebuild source state.

### I-7. Logical data sources hide physical persistence structures.

### I-8. Presentation cannot mutate analytical results.

### I-9. Standard-specific semantics do not leak into generic Reporting contracts.

### I-10. Reporting must not claim stronger cross-source consistency than its source contracts provide.

---

# 18. Table Engine and Expression Engine Decisions

## 18.1 Table Engine

The existing Reporting architecture documentation describes reuse of a Table Engine. The current executable repository does not provide such a generic engine as an established Platform dependency.

Therefore WP-9 does **not** declare an existing Table Engine as a hard dependency.

Dataset processing required by the first vertical slice may be implemented behind Reporting runtime contracts. A reusable platform-wide table-processing engine may be introduced later if justified by additional use cases.

## 18.2 Expression Engine

The architecture also describes an Expression Engine for calculated measures. The current executable repository does not provide this as an established generic Platform service.

Therefore WP-9 does **not** declare an existing Expression Engine as a hard dependency.

Calculated-measure support in the first slice must remain limited to explicitly approved semantics. A platform-wide Expression Engine remains a future capability unless separately approved.

These decisions prevent WP-9 from creating dependencies on infrastructure that does not yet exist.

---

# 19. Presentation Boundary

Presentation is downstream from dataset execution:

```text
Report Definition
       ↓
Report Runtime
       ↓
Dataset
       ↓
Presentation / Export / API / UI
```

WP-9 establishes the dataset boundary but does not implement full rendering.

Future presentation consumers may include:

- tables;
- pivots;
- charts;
- dashboards;
- PDF/export formats;
- web/UI views;
- API responses.

None of these consumers may change the analytical dataset itself.

---

# 20. Standard Integration Boundary

Generic Platform Reporting belongs to:

```text
accore.platform.reporting
```

Standard-specific composition belongs outside generic Reporting.

The Standard layer may provide:

- concrete report definitions;
- Standard logical data-source adapters;
- Inventory-specific source composition;
- Standard runtime configuration.

Generic Reporting must not import Standard accounting concepts merely to support the first Standard report.

---

# 21. Error Boundary

The Concrete API Design must define explicit reporting failures for at least these categories where applicable:

- invalid report definition;
- unavailable logical data source;
- invalid source schema reference;
- unsupported analytical operation;
- source read failure;
- execution failure.

Reporting errors must preserve the distinction between:

1. an invalid request/definition;
2. an unavailable source;
3. an execution failure.

Reporting must not reinterpret a source recovery problem as a successful empty dataset.

---

# 22. Determinism

For identical report definitions, parameters, and source read inputs, execution should produce equivalent datasets.

Determinism includes:

- stable grouping semantics;
- stable aggregation semantics;
- explicit ordering where ordering is part of the requested result;
- no dependence on incidental dictionary/storage ordering;
- no mutation of source state during execution.

Where a report does not request ordering, the API Design may define whether dataset row order is unspecified, but tests must not accidentally rely on implementation ordering.

---

# 23. Testing Scope

The WP-9 implementation must test architecture boundaries, not only individual classes.

Minimum testing areas:

## 23.1 Metadata

- valid report definition;
- invalid source references;
- invalid field references;
- invalid dimensions/measures;
- invalid aggregation combinations.

## 23.2 Data Sources

- logical schema exposure;
- source read behavior;
- source failure propagation;
- source independence from physical persistence.

## 23.3 Runtime

- validation before execution;
- compilation;
- execution plan creation;
- dataset production;
- deterministic results.

## 23.4 Cross-domain integration

- Register source integration;
- Valuation source integration;
- Inventory-oriented composition;
- cross-source consistency behavior;
- unavailable/invalid source behavior.

## 23.5 Immutability

- report definition is not mutated by execution;
- execution plan is not mutated unexpectedly;
- dataset consumer operations cannot mutate source state;
- Reporting cannot mutate valuation facts.

## 23.6 Boundary tests

Explicit tests must ensure Reporting does not accidentally depend on:

- persistence implementations;
- mutation orchestrators;
- valuation coordinators;
- recovery services.

---

# 24. Documentation Scope

WP-9 documentation must reconcile at least:

- Reporting architecture;
- logical data source contract;
- analytical model;
- execution model;
- dataset contract;
- consistency semantics;
- Standard integration;
- first vertical slice;
- final API design;
- implementation/recovery boundaries where relevant.

Existing conceptual documents must be amended where they describe non-existent infrastructure as though it were already implemented.

The final documentation must distinguish clearly between:

- implemented capability;
- architectural direction;
- future capability.

---

# 25. Initial Implementation Scope

The first executable WP-9 slice is intentionally constrained to:

```text
Logical Data Source
        ↓
Report Definition
        ↓
Validation
        ↓
Compilation
        ↓
Execution Plan
        ↓
Reporting Runtime
        ↓
Analytical Dataset
```

with an actual Register/Valuation-backed analytical use case.

The first slice must prove the entire path from semantic domain read to dataset production.

It does not need to implement every future report feature.

---

# 26. Proposed Work Breakdown

The exact slices will be established during Concrete API Design, but the architecture supports the following progression:

### Slice A — Reporting core contracts

- report definition boundary;
- logical data source boundary;
- dimensions/measures;
- dataset model.

### Slice B — Validation/compilation

- report validation;
- compiled representation;
- execution-plan representation.

### Slice C — Runtime execution

- source resolution;
- plan execution;
- dataset production.

### Slice D — Register integration

- Register logical source adapter;
- movement/balance analytical data.

### Slice E — Valuation integration

- Valuation logical source adapter;
- cost/valuation analytical data.

### Slice F — Inventory-oriented vertical integration

- cross-source composition;
- consistency semantics;
- complete analytical dataset.

### Slice G — Quality and documentation reconciliation

- architecture/API tests;
- full quality gate;
- documentation reconciliation.

The Concrete API Design may reorder or split these slices, but must preserve the architectural boundaries defined here.

---

# 27. Deferred Capabilities

The following remain valid architectural directions but are not WP-9 implementation requirements:

- full Expression Engine;
- generic Table Engine;
- advanced query optimization;
- dataset caching;
- materialized report datasets;
- hierarchical drill-down/roll-up;
- pivot execution;
- dashboards;
- charts;
- PDF/Excel/export renderers;
- interactive report designer;
- OLAP capabilities;
- distributed analytical execution.

Deferral does not prohibit future implementation. It prevents premature coupling of WP-9 to infrastructure that is not currently present or required for the first vertical slice.

---

# 28. Architectural Decisions Resulting From Review

The Architecture Review produced the following decisions.

| ID | Decision | Status |
|---|---|---|
| AR-1 | Reporting is read-only | Accepted |
| AR-2 | Logical Data Source is the domain integration boundary | Accepted with amendment |
| AR-3 | Register and Valuation are consumed through semantic read contracts | Accepted |
| AR-4 | Inventory-oriented report is the first cross-domain vertical slice | Accepted |
| AR-5 | Dataset is the stable execution output boundary | Accepted |
| AR-6 | Compilation and Execution Plan are explicit runtime concepts | Accepted, reduced initial scope |
| AR-7 | Existing Table Engine is not a WP-9 hard dependency | Accepted |
| AR-8 | Existing Expression Engine is not a WP-9 hard dependency | Accepted |
| AR-9 | Presentation/rendering is deferred | Accepted |
| AR-10 | Cross-source consistency must be explicit and source-derived | Accepted |
| AR-11 | Reporting does not perform recovery/rebuild | Accepted |
| AR-12 | Standard-specific report composition remains outside generic Reporting | Accepted |
| AR-13 | Reporting must not access physical persistence directly | Accepted |

---

# 29. Open Questions For Concrete API Design

The architecture is considered resolved enough to proceed, but the following questions belong to the API Design stage rather than reopening the architectural boundary.

1. Exact `LogicalDataSource` protocol shape.
2. Exact schema representation and field/type model.
3. Exact `ReportDefinition` representation.
4. Whether dimensions/measures are reusable metadata objects or embedded definitions in the first API.
5. Exact compilation artifact shape.
6. Exact execution-plan node representation.
7. Dataset row/column representation and typing.
8. Exact source snapshot/read-view contract.
9. Exact representation of cross-source execution context.
10. First Register adapter source shape.
11. First Valuation adapter source shape.
12. Exact Inventory-oriented report definition.
13. Error/result contract for invalid, unavailable, and failed sources.
14. Exact scope of calculated measures in the first implementation.
15. Public export surface from `accore.platform.reporting`.

These are API-level questions and must not be resolved by introducing implementation-specific assumptions into the architecture.

---

# 30. Acceptance Criteria For Architecture

This Architecture Definition / Scope is considered complete when all of the following hold:

- Reporting has a clear read-only ownership boundary;
- logical data sources isolate Reporting from physical persistence;
- Register and Valuation remain owners of their respective semantics;
- WP-8 recovery/rebuild ownership remains unchanged;
- Dataset is the stable output boundary;
- cross-source consistency semantics are explicit;
- Inventory-oriented reporting is defined as the first meaningful vertical slice;
- Table Engine and Expression Engine are not assumed to already exist;
- presentation/rendering is explicitly deferred;
- Standard-specific semantics remain outside generic Platform Reporting;
- the document distinguishes implemented baseline from future architectural direction;
- Concrete API Design can proceed without reopening the core architectural boundary.

---

# 31. Final Architectural Position

## Implementation reconciliation

The architecture defined by this document is now implemented through Phase 9 Slice #7.
The implemented subset consists of the generic read-only Reporting contracts, validation, compilation, execution planning, runtime filtering/grouping/aggregation, deterministic immutable datasets, the Standard Inventory logical source, and the Standard Inventory Balance report definition and vertical execution tests.

The following capabilities remain intentionally deferred as stated by the original architecture: presentation/rendering, export, generic expression/calculated-measure execution, generic cross-source joins, persistence/scheduling/security, caching, optimization, and distributed execution.

The final Phase 9 Slice #8 reconciliation is recorded in `PHASE_9_Slice_8_Final_Implementation_Review_and_Documentation_Reconciliation.md`.


WP-9 establishes **Reporting as a generic, read-only Platform analytical subsystem**.

Its fundamental contract is:

```text
Semantic Domain Read
        ↓
Logical Data Source
        ↓
Declarative Report Definition
        ↓
Validation / Compilation
        ↓
Execution Plan
        ↓
Reporting Runtime
        ↓
Immutable Analytical Dataset
```

Reporting is deliberately positioned **above** Register and Valuation semantic read services and **below** future presentation/integration consumers.

It does not become an accounting subsystem, a valuation subsystem, a persistence framework, or a UI framework.

The first implementation must prove the architecture through a real Register + Valuation analytical vertical slice while preserving the ownership and immutability guarantees established by WP-8.

**Architecture status: APPROVED AND IMPLEMENTED THROUGH SLICE #7.**

---
