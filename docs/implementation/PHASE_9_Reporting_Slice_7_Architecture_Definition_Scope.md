# PHASE 9 — Reporting Slice 7

# End-to-End Inventory Balance Report

## Final Architecture Definition / Scope

**Status:** Approved for Concrete API Design

**Baseline:** AcCoreD after Phase 9 Slice #6

**Previous slice:** Slice #6 — Standard Inventory Reporting Adapter

**Implementation status:** Not started

---

# 1. Purpose

Slice #7 introduces the first complete end-to-end Reporting vertical report over the Standard Inventory domain.

The slice proves that the existing generic Reporting pipeline can consume a real Standard-owned logical source and produce an immutable analytical dataset:

```text
Standard semantic domain state
        ↓
InventoryBalanceReportSource
        ↓
ReportDataSourceRegistry
        ↓
Inventory Balance ReportDefinition
        ↓
ReportValidator
        ↓
ReportCompiler
        ↓
ReportExecutionPlanBuilder
        ↓
DefaultReportRuntime
        ↓
ReportDataset
```

No new generic Reporting capability is required by the architecture.

---

# 2. Architecture Review Decisions

The following decisions are final for Concrete API Design.

## AR-1 — Dedicated report identity

The Inventory Balance report has its own stable `Identifier`.

It is distinct from:

* `INVENTORY_REGISTER_ID`;
* `INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY`.

The exact stable identifier value is fixed in Concrete API Design.

---

## AR-2 — Dedicated Standard report-definition module

The report definition belongs in:

```text
src/standard/reporting/inventory_balance.py
```

The existing:

```text
src/standard/reporting/inventory.py
```

continues to own the logical Inventory Balance data source.

This keeps:

```text
logical source
```

and:

```text
report definition
```

as separate responsibilities.

---

## AR-3 — Immutable module-level report definition

The Standard report is represented by an immutable module-level definition:

```text
INVENTORY_BALANCE_REPORT_DEFINITION
```

The definition contains:

### Source

```text
inventory.balance
```

### Dimensions

```text
product
warehouse
```

### Measures

```text
quantity = SUM(quantity)
cost     = SUM(cost)
```

### Filters

```text
()
```

The base Inventory Balance report has no embedded business filter.

---

## AR-4 — No Standard report-execution facade

Slice #7 does not introduce an API such as:

```text
execute_inventory_balance_report(...)
```

The end-to-end integration uses the existing generic Reporting boundaries:

```text
ReportValidator
ReportCompiler
ReportExecutionPlanBuilder
ReportRuntime
```

A higher-level application/report execution facade, if later required, is outside Slice #7.

---

## AR-5 — Existing registry remains the source composition boundary

The Standard composition established in Slice #6 remains responsible for:

```text
ReportDataSourceRegistry
```

containing:

```text
inventory.balance
```

The report definition references the logical source identity.

It does not construct or retain an `InventoryBalanceReportSource`.

No second registry or alternative source composition path is introduced.

---

## AR-6 — Vertical fixture uses real semantic domain state

The Slice #7 vertical tests prepare actual semantic derived state through existing Register and Valuation semantic components.

The test path is:

```text
semantic domain state
        ↓
InventoryBalanceReportSource
        ↓
ReportDataSourceRegistry
        ↓
generic Reporting pipeline
```

The tests must not replace the complete path with manually constructed `ReportRow` fixtures.

The tests also do not need to execute the full Goods Receipt → Posting → Valuation lifecycle merely to prepare Reporting state.

Posting, FIFO, persistence, recovery, and historical reconstruction remain outside the Reporting vertical test boundary.

---

## AR-7 — No generic Reporting changes

Slice #7 introduces no changes to:

```text
src/accore/platform/reporting/
```

unless Concrete API Design demonstrates a specific existing contract gap that cannot be solved within Standard.

No Standard-specific abstraction may be introduced into generic Reporting.

---

## AR-8 — Filtering remains generic

`InventoryBalanceReportSource` remains filter-agnostic.

The base report definition contains no filters.

A vertical regression test may construct an immutable filtered report definition to demonstrate:

```text
ReportDefinition
    ↓
ReportExecutionPlan
    ↓
DefaultReportRuntime
    ↓
filtered Dataset
```

Filtering remains the responsibility of generic Reporting runtime.

---

## AR-9 — Read-only execution

Report execution must not mutate domain state.

The vertical test verifies semantic state equivalence before and after execution:

```text
Register state before == Register state after
Valuation state before == Valuation state after
```

No report-specific mutation or write dependency is introduced.

---

## AR-10 — Existing source semantics remain authoritative

The vertical report inherits the semantics already established by Slice #6:

* Register determines Inventory scope;
* valuation provides cost;
* valuation-only scopes do not create Inventory rows;
* missing valuation state is an error;
* explicit zero valuation cost is preserved;
* zero Register totals are not enumerated;
* source failures propagate;
* no historical reconstruction occurs;
* no atomic cross-domain snapshot is claimed.

Slice #7 must not redefine these semantics.

---

# 3. Goals

## G-1

Introduce one concrete Standard Inventory Balance report definition.

## G-2

Execute the report through the existing generic Reporting pipeline.

## G-3

Resolve the logical source through `ReportDataSourceRegistry`.

## G-4

Produce an immutable `ReportDataset`.

## G-5

Demonstrate correct Register quantity + Valuation cost composition.

## G-6

Demonstrate generic report-level filtering.

## G-7

Demonstrate deterministic output.

## G-8

Demonstrate that report execution is read-only.

---

# 4. Non-Goals

Slice #7 does not implement:

* generic join engine;
* new cross-source composition;
* calculated expressions;
* calculated measures;
* AVG;
* presentation;
* export;
* dashboards;
* pagination;
* caching;
* scheduling;
* authorization;
* report persistence;
* dataset persistence;
* report designer UI;
* generic report catalog;
* report parameter framework;
* query optimization;
* application-level report execution facade.

No Register or Valuation business semantics are changed.

---

# 5. Ownership

## Generic Reporting

Owns:

* report definition semantics;
* validation;
* compilation;
* execution planning;
* filtering;
* grouping;
* aggregation;
* deterministic output;
* dataset materialization.

## Standard

Owns:

* Inventory Balance report identity;
* Inventory Balance report definition;
* Standard report metadata;
* source registry composition;
* vertical integration tests.

## Inventory Register

Owns:

```text
product
warehouse
quantity
```

## Valuation

Owns:

```text
cost
```

---

# 6. Report Definition

The report is declarative metadata.

Conceptually:

```text
Inventory Balance Report
    source:
        inventory.balance

    dimensions:
        product
        warehouse

    measures:
        quantity = SUM(quantity)
        cost     = SUM(cost)

    filters:
        none
```

The definition contains no domain services.

It must not depend on:

* Register engines;
* Valuation engines;
* persistence;
* posting;
* FIFO;
* recovery;
* mutation services.

---

# 7. Report Source

The report consumes the existing logical source:

```text
inventory.balance
```

Source schema:

| Field       | Type    | Meaning                   |
| ----------- | ------- | ------------------------- |
| `product`   | STRING  | Inventory product scope   |
| `warehouse` | STRING  | Inventory warehouse scope |
| `quantity`  | DECIMAL | Current Register quantity |
| `cost`      | DECIMAL | Current Valuation cost    |

No second Inventory Balance source is introduced.

---

# 8. Dimensions

The report groups by:

```text
product
warehouse
```

The declaration order is:

```text
product
warehouse
```

The resulting report grouping key is:

```text
(product, warehouse)
```

---

# 9. Measures

## Quantity

```text
SUM(quantity)
```

## Cost

```text
SUM(cost)
```

Both source fields are Decimal.

The report does not calculate:

```text
quantity × unit cost
```

Cost is consumed from the authoritative valuation-derived source field.

---

# 10. Output Dataset

The logical report output is:

```text
Product
Warehouse
Quantity
Cost
```

The generic compiler creates the final output schema from the report definition.

No Standard-specific dataset implementation is required.

---

# 11. End-to-End Execution

The complete execution path is:

```text
InventoryBalanceReportDefinition
        ↓
ReportValidator
        ↓
ReportCompiler
        ↓
ReportExecutionPlanBuilder
        ↓
DefaultReportRuntime
        ↓
ReportDataSourceRegistry
        ↓
InventoryBalanceReportSource
        ↓
Register + Valuation semantic state
        ↓
ReportDataset
```

The runtime remains the only generic execution engine.

---

# 12. Required Vertical Scenarios

## VS-1 — Basic Inventory Balance

Prepare one or more Inventory scopes with matching valuation balances.

Execute the actual generic Reporting pipeline.

Assert:

* dataset schema;
* row count;
* product;
* warehouse;
* quantity;
* cost.

---

## VS-2 — Multiple Inventory Scopes

Prepare multiple distinct:

```text
(product, warehouse)
```

scopes.

Assert:

* one row per current Inventory scope;
* correct grouping;
* deterministic ordering.

---

## VS-3 — Generic Filtering

Construct an immutable report definition with a filter such as:

```text
warehouse == <value>
```

Execute through the same generic runtime.

Assert:

* only matching rows remain;
* filtering occurs through generic Reporting;
* source implementation remains unchanged.

---

## VS-4 — Explicit Zero Cost

Prepare a materialized valuation balance with:

```text
cost = Decimal(0)
```

Assert that the final dataset contains:

```text
Decimal(0)
```

for Cost.

---

## VS-5 — Missing Valuation

Prepare a Register Inventory scope with no corresponding valuation balance.

Assert that execution fails with the existing Standard source error.

The runtime must not:

* produce zero;
* omit the row;
* return an empty dataset.

---

## VS-6 — Valuation-only Scope

Prepare valuation state for a scope absent from Register totals.

Assert that the report produces no Inventory row for that valuation-only scope.

---

## VS-7 — Empty Inventory

Prepare no current Register Inventory scopes.

Assert that the dimensioned report returns:

```text
0 rows
```

and does not create a synthetic aggregate row.

---

## VS-8 — Read-only execution

Capture semantic Register and Valuation state.

Execute the report.

Assert that both states remain unchanged.

---

# 13. Determinism

Equivalent semantic state and equivalent report definition must produce equivalent:

* schema;
* row count;
* grouping;
* aggregate values;
* row ordering.

The vertical test must use multiple scopes whose preparation order does not correspond to the expected canonical output order.

---

# 14. Error Boundaries

Source errors propagate.

Validation errors occur before execution where possible.

Compilation errors do not mutate domain state.

No failure is converted into:

```text
empty dataset
```

or:

```text
zero values
```

unless that behavior is explicitly defined by the generic Reporting contract.

---

# 15. Consistency

The Inventory logical source remains:

```text
SOURCE_LOCAL
```

No atomic snapshot guarantee across Register and Valuation is introduced.

Slice #7 does not add synchronization, transaction coordination, or snapshot infrastructure.

---

# 16. Module Boundary

Standard report definition:

```text
src/standard/reporting/inventory_balance.py
```

Existing logical source remains:

```text
src/standard/reporting/inventory.py
```

The Standard reporting package exports the report definition.

No Inventory report implementation is added to:

```text
src/accore/platform/reporting/
```

---

# 17. Generic Reporting Boundary

The following existing APIs are consumed unchanged:

```text
ReportDefinition
ReportValidator
ReportCompiler
ReportExecutionPlanBuilder
ReportRuntime
ReportDataSourceRegistry
ReportDataset
```

No generic Reporting extension is planned.

---

# 18. Explicit Architectural Invariants

## I-1

Generic Reporting has no dependency on Standard Inventory.

## I-2

The report definition contains metadata only.

## I-3

Register remains authoritative for Inventory scope and quantity.

## I-4

Valuation remains authoritative for cost.

## I-5

Reporting does not reconstruct historical state.

## I-6

Reporting does not access persistence.

## I-7

Report execution does not mutate domain state.

## I-8

`InventoryBalanceReportSource` remains the cross-domain Inventory source boundary.

## I-9

Generic runtime owns filtering, grouping, and aggregation.

## I-10

The output dataset is immutable.

## I-11

Output ordering is deterministic.

## I-12

Missing valuation state is not interpreted as zero.

## I-13

Valuation-only state does not create Inventory rows.

## I-14

No atomic cross-domain snapshot is claimed.

## I-15

No new generic analytical capability is introduced solely for this report.

---

# 19. Acceptance Criteria

Slice #7 is complete when:

1. A stable Standard Inventory Balance report identity exists.
2. An immutable `INVENTORY_BALANCE_REPORT_DEFINITION` exists.
3. The definition references `inventory.balance`.
4. Product and Warehouse are dimensions.
5. Quantity and Cost are Decimal SUM measures.
6. The definition is resolved through the existing source registry.
7. Validation succeeds.
8. Compilation succeeds.
9. Execution plan construction succeeds.
10. Generic runtime executes the report.
11. The resulting dataset contains the expected Inventory Balance state.
12. Generic filtering works.
13. Explicit zero cost is preserved.
14. Missing valuation fails.
15. Valuation-only state is ignored.
16. Empty Inventory produces zero dimensioned rows.
17. Output is deterministic.
18. Register and Valuation semantic state is unchanged by execution.
19. No generic Reporting API is made Standard-specific.
20. No domain persistence, posting, FIFO, recovery, or mutation dependency is introduced.
21. Full quality gate passes.

---

# 20. Implementation Sequence

After approval of this architecture and the Concrete API Design:

### Step 1 — Report identity and definition

Add:

```text
standard/reporting/inventory_balance.py
```

with the stable report identity and immutable definition.

### Step 2 — Standard exports

Expose the report definition through the Standard reporting package.

### Step 3 — Vertical integration

Compose the existing:

```text
registry
validator
compiler
plan builder
runtime
```

and execute the actual Inventory Balance report.

### Step 4 — Vertical regression tests

Implement the required scenarios.

### Step 5 — Documentation reconciliation

Update Slice #7 implementation/API documentation.

### Step 6 — Quality gate

Run:

```text
pytest
ruff check .
black --check .
mypy src
```

No intermediate commit is required.

---

# 21. Final Architectural Position

Slice #7 is a vertical integration slice, not a generic Reporting feature-development slice.

Its architectural result is:

```text
                  STANDARD
                     │
                     ▼
       Inventory Balance Report
                     │
                     ▼
          ReportDefinition
                     │
                     ▼
          Generic Reporting
                     │
                     ▼
              ReportDataset
```

with domain state entering Reporting only through:

```text
Register + Valuation
        ↓
InventoryBalanceReportSource
        ↓
ReportDataSourceRegistry
```

The generic Reporting subsystem remains domain-neutral.

The Standard report remains declarative.

The Inventory logical source remains the only cross-domain composition boundary.

No mutation, persistence coupling, posting logic, FIFO logic, recovery logic, or historical reconstruction enters the Reporting execution path.

**Architecture status: APPROVED FOR CONCRETE API DESIGN.**
