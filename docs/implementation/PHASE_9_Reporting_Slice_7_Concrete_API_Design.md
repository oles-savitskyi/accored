# PHASE 9 — Reporting Slice 7

# End-to-End Inventory Balance Report

## Concrete API Design

**Status:** Approved for Implementation

**Architecture baseline:** Phase 9 Slice #7 — Final Architecture Definition / Scope

**Previous slice:** Slice #6 — Standard Inventory Reporting Adapter

**Implementation status:** Not started

---

# 1. Design Summary

Slice #7 adds one Standard-owned immutable `ReportDefinition` for the Inventory Balance report.

No generic Reporting API is changed.

The complete public design consists of:

```text
src/standard/reporting/inventory_balance.py
src/standard/reporting/__init__.py
```

The new Standard API is:

```text
INVENTORY_BALANCE_REPORT_IDENTITY
INVENTORY_BALANCE_REPORT_DEFINITION
```

The report consumes the already existing:

```text
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
```

through the already existing:

```text
ReportDataSourceRegistry
```

Execution continues to use the existing generic APIs:

```text
DefaultReportValidator
DefaultReportCompiler
DefaultReportExecutionPlanBuilder
DefaultReportRuntime
```

No convenience execution facade is introduced.

---

# 2. Existing Generic API Used Unchanged

The implementation consumes the following existing generic contracts.

## ReportDefinition

```python
@dataclass(frozen=True, slots=True)
class ReportDefinition:
    identity: Identifier
    name: str
    source: ReportDataSourceIdentity
    filters: tuple[ReportFilter, ...]
    dimensions: tuple[ReportDimension, ...]
    measures: tuple[ReportMeasure, ...]
```

## ReportDimension

```python
@dataclass(frozen=True, slots=True)
class ReportDimension:
    name: str
    source_field: str
    description: str | None = None
```

## ReportMeasure

```python
@dataclass(frozen=True, slots=True)
class ReportMeasure:
    name: str
    aggregation: ReportAggregation
    source_field: str | None = None
    description: str | None = None
```

## ReportAggregation

The report uses:

```python
ReportAggregation.SUM
```

No new aggregation is introduced.

---

# 3. Report Identity

Introduce a dedicated stable identity:

```python
INVENTORY_BALANCE_REPORT_IDENTITY = Identifier.from_str(
    "01ARZ3NDEKTSV4RRFFQ69G5FB0"
)
```

This identity belongs to the report definition.

It is distinct from:

```python
INVENTORY_REGISTER_ID
```

and:

```python
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
```

The identity is deterministic and must not be generated dynamically.

The report identity is not persisted by Slice #7.

---

# 4. Report Name

The canonical report name is:

```python
"Inventory Balance"
```

This is the human-readable `ReportDefinition.name`.

The name is metadata only and has no execution semantics.

---

# 5. Report Source

The definition references:

```python
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
```

from:

```text
standard.reporting.inventory
```

Therefore:

```python
source=INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
```

The definition does not contain:

* `InventoryBalanceReportSource`;
* `TotalsReader`;
* `CostTotalsReader`;
* `ReportDataSourceRegistry`;
* Register engine;
* Valuation engine.

Source resolution remains the responsibility of `ReportDataSourceRegistry`.

---

# 6. Dimensions

The report has exactly two dimensions.

## Product

```python
ReportDimension(
    name="product",
    source_field=INVENTORY_PRODUCT_DIMENSION,
)
```

## Warehouse

```python
ReportDimension(
    name="warehouse",
    source_field=INVENTORY_WAREHOUSE_DIMENSION,
)
```

The declaration order is:

```python
dimensions=(
    ReportDimension(
        name="product",
        source_field=INVENTORY_PRODUCT_DIMENSION,
    ),
    ReportDimension(
        name="warehouse",
        source_field=INVENTORY_WAREHOUSE_DIMENSION,
    ),
)
```

This order is part of the report definition and therefore contributes to deterministic grouping/output semantics.

---

# 7. Measures

The report has exactly two measures.

## Quantity

```python
ReportMeasure(
    name="quantity",
    aggregation=ReportAggregation.SUM,
    source_field="quantity",
)
```

## Cost

```python
ReportMeasure(
    name="cost",
    aggregation=ReportAggregation.SUM,
    source_field="cost",
)
```

The declaration order is:

```python
measures=(
    ReportMeasure(
        name="quantity",
        aggregation=ReportAggregation.SUM,
        source_field="quantity",
    ),
    ReportMeasure(
        name="cost",
        aggregation=ReportAggregation.SUM,
        source_field="cost",
    ),
)
```

Both source fields are Decimal according to:

```python
INVENTORY_BALANCE_REPORT_SCHEMA
```

No conversion to float is introduced.

---

# 8. Filters

The base report definition contains no filters:

```python
filters=()
```

This is intentional.

Filtering is supplied by a concrete report execution definition when required and is handled by the generic Reporting runtime.

The base Inventory Balance report therefore represents the complete current logical Inventory Balance state.

---

# 9. Complete Definition

The implementation is conceptually:

```python
from accore.platform.foundation import Identifier
from accore.platform.reporting import (
    ReportAggregation,
    ReportDefinition,
    ReportDimension,
    ReportMeasure,
)
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_WAREHOUSE_DIMENSION,
)
from standard.reporting.inventory import (
    INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY,
)


INVENTORY_BALANCE_REPORT_IDENTITY = Identifier.from_str(
    "01ARZ3NDEKTSV4RRFFQ69G5FB0"
)


INVENTORY_BALANCE_REPORT_DEFINITION = ReportDefinition(
    identity=INVENTORY_BALANCE_REPORT_IDENTITY,
    name="Inventory Balance",
    source=INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY,
    filters=(),
    dimensions=(
        ReportDimension(
            name="product",
            source_field=INVENTORY_PRODUCT_DIMENSION,
        ),
        ReportDimension(
            name="warehouse",
            source_field=INVENTORY_WAREHOUSE_DIMENSION,
        ),
    ),
    measures=(
        ReportMeasure(
            name="quantity",
            aggregation=ReportAggregation.SUM,
            source_field="quantity",
        ),
        ReportMeasure(
            name="cost",
            aggregation=ReportAggregation.SUM,
            source_field="cost",
        ),
    ),
)
```

The definition is immutable because `ReportDefinition`, `ReportDimension`, and `ReportMeasure` are frozen dataclasses.

---

# 10. Module Location

Create:

```text
src/standard/reporting/inventory_balance.py
```

Responsibilities:

* report identity;
* report definition.

It must not contain:

* source implementation;
* source reading;
* execution logic;
* filtering;
* aggregation;
* domain mutation;
* persistence.

---

# 11. Package Exports

Update:

```text
src/standard/reporting/__init__.py
```

to export:

```python
INVENTORY_BALANCE_REPORT_DEFINITION
INVENTORY_BALANCE_REPORT_IDENTITY
```

The existing exports from `inventory.py` remain unchanged.

The resulting public package surface is conceptually:

```python
from standard.reporting import (
    INVENTORY_BALANCE_REPORT_DEFINITION,
    INVENTORY_BALANCE_REPORT_IDENTITY,
    INVENTORY_BALANCE_REPORT_SCHEMA,
    INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY,
    InventoryBalanceReportSource,
    InventoryBalanceReportSourceError,
)
```

No generic Reporting API is re-exported through `standard.reporting`.

---

# 12. No New Execution API

Do not introduce:

```python
execute_inventory_balance_report(...)
```

or:

```python
InventoryBalanceReportService
```

or:

```python
InventoryBalanceReportRunner
```

The vertical integration uses the existing generic contracts directly.

The intended execution sequence is:

```python
validated = validator.validate(
    INVENTORY_BALANCE_REPORT_DEFINITION,
    registry.get(INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY),
)

compiled = compiler.compile(validated)

plan = plan_builder.build(compiled)

dataset = runtime.execute(plan)
```

This is the canonical Slice #7 execution path.

---

# 13. Registry Integration

Slice #7 does not modify the source registry implementation.

The existing Standard composition creates a registry containing:

```text
inventory.balance
```

The vertical test obtains the registry through the existing Standard composition boundary.

The report definition resolves its source indirectly:

```text
ReportDefinition.source
        ↓
ReportDataSourceRegistry.get(...)
        ↓
InventoryBalanceReportSource
```

No direct source construction occurs in the report definition.

---

# 14. Vertical Test Composition

The primary vertical test fixture should use:

```python
DefaultTotalsEngine
DefaultCostTotalsEngine
```

or the existing Standard semantic composition where appropriate.

The source is then composed through:

```python
StandardConfigurationBootstrap.compose_inventory_reporting(...)
```

or the exact equivalent already established by Slice #6.

The test must not replace the source with a fake `ReportDataSource`.

The purpose is to test:

```text
semantic Register state
+
semantic Valuation state
        ↓
InventoryBalanceReportSource
        ↓
ReportDataSourceRegistry
        ↓
ReportDefinition
        ↓
Validator
        ↓
Compiler
        ↓
PlanBuilder
        ↓
Runtime
        ↓
Dataset
```

---

# 15. Test Helpers

Test-only helper functions may be introduced under:

```text
tests/unit/standard/reporting/
```

They must remain test-only.

A useful helper may compose the generic pipeline:

```python
def execute_inventory_balance_report(
    registry: ReportDataSourceRegistry,
) -> ReportDataset:
    ...
```

This helper is **not** a production API.

Its purpose is to keep vertical tests concise without introducing a Standard runtime facade.

---

# 16. Required Test Cases

## T-1 — Definition metadata

Verify:

```text
identity == INVENTORY_BALANCE_REPORT_IDENTITY
name == "Inventory Balance"
source == INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
filters == ()
```

Verify exactly two dimensions:

```text
product
warehouse
```

and exactly two measures:

```text
quantity = SUM(quantity)
cost = SUM(cost)
```

---

## T-2 — Definition validation

Resolve the source from the actual Standard registry.

Validate:

```python
DefaultReportValidator().validate(...)
```

Assert successful validation.

This proves that the report definition matches the actual source schema.

---

## T-3 — Basic end-to-end execution

Prepare:

```text
product = P1
warehouse = W1
quantity = Decimal(...)
cost = Decimal(...)
```

Execute the complete pipeline.

Assert one resulting dataset row with:

```text
product
warehouse
quantity
cost
```

matching the semantic domain state.

---

## T-4 — Multiple scopes

Prepare multiple scopes, for example:

```text
(P2, W2)
(P1, W1)
(P1, W2)
```

Execute the report.

Assert:

* one row per Register scope;
* correct quantity;
* correct cost;
* deterministic `(product, warehouse)` ordering.

---

# 17. Filtered Vertical Execution

Filtering is tested using a derived report definition.

The test may construct:

```python
filtered_definition = dataclasses.replace(
    INVENTORY_BALANCE_REPORT_DEFINITION,
    filters=(
        ReportFilter(
            field=INVENTORY_WAREHOUSE_DIMENSION,
            operator=ReportFilterOperator.EQUALS,
            value=ReportValue("W1"),
        ),
    ),
)
```

The exact construction must use the existing `ReportFilter` API.

The test then executes the same:

```text
validate
→ compile
→ build
→ execute
```

pipeline.

Expected result:

* only `W1` rows remain;
* no source implementation change;
* no Standard-specific filtering logic.

The original module-level definition remains unchanged.

---

# 18. Explicit Zero Cost

Prepare a materialized valuation balance:

```python
CostBalance(
    ...,
    cost=Decimal(0),
    ...
)
```

Execute the report.

Assert:

```python
row.values["cost"].value == Decimal(0)
```

This test ensures the end-to-end pipeline does not confuse:

```text
explicit zero
```

with:

```text
missing valuation
```

---

# 19. Missing Valuation

Prepare a Register scope without a matching valuation balance.

Execute the complete report pipeline.

Assert:

```python
InventoryBalanceReportSourceError
```

is propagated.

The test must verify that execution does not return:

```text
empty dataset
```

or:

```text
cost = 0
```

---

# 20. Valuation-only Scope

Prepare valuation state for a scope absent from Register totals.

Execute the report.

Assert that no dataset row exists for that valuation-only scope.

The report obtains its scope exclusively from Register enumeration.

---

# 21. Empty Inventory

Prepare no Register Inventory totals.

Execute the dimensioned report.

Assert:

```python
len(dataset.rows) == 0
```

No synthetic aggregate row is expected.

---

# 22. Read-only Regression

Before execution, capture:

```text
Register totals
Valuation balances
```

Execute the report.

After execution, compare both states.

Expected:

```text
before == after
```

The test must not rely exclusively on mocks to prove read-only behavior.

---

# 23. Deterministic Output

Prepare multiple scopes in an order different from canonical output ordering.

Example preparation order:

```text
(P2, W2)
(P1, W2)
(P1, W1)
```

Expected output ordering:

```text
(P1, W1)
(P1, W2)
(P2, W2)
```

The test verifies the generic runtime's deterministic ordering.

---

# 24. Source Request Boundary

The vertical test must not require the source to implement report filtering.

The report's filter reaches the source as part of the existing:

```python
ReportDataSourceRequest(filters=...)
```

contract.

`InventoryBalanceReportSource` continues to return its complete logical source state.

The generic runtime remains responsible for filter application.

---

# 25. API Compatibility

No modifications are made to:

```text
src/accore/platform/reporting/
```

The following existing APIs remain unchanged:

```text
ReportDefinition
ReportDimension
ReportMeasure
ReportAggregation
ReportFilter
ReportDataSource
ReportDataSourceRegistry
ReportValidator
ReportCompiler
ReportExecutionPlanBuilder
ReportRuntime
ReportDataset
```

No new generic protocol or enum is required.

---

# 26. Error API

No new error class is required.

The existing:

```python
InventoryBalanceReportSourceError
```

continues to represent failure to compose the Inventory logical source.

Generic validation failures continue to use:

```python
ReportValidationError
```

No wrapper error is introduced solely for the vertical report.

---

# 27. Public API Surface

The only new production symbols are:

```python
INVENTORY_BALANCE_REPORT_IDENTITY
INVENTORY_BALANCE_REPORT_DEFINITION
```

Both are module-level immutable values.

No new classes are introduced.

No new Protocol is introduced.

No new runtime service is introduced.

---

# 28. File Changes

Expected production changes:

```text
src/standard/reporting/inventory_balance.py
src/standard/reporting/__init__.py
```

Expected tests:

```text
tests/unit/standard/reporting/test_inventory_balance.py
```

Additional test files may be introduced only if separation improves clarity.

No changes expected in:

```text
src/accore/platform/reporting/
```

unless an implementation-time discrepancy with the existing API is discovered.

---

# 29. Documentation Changes

Implementation must be reconciled with:

```text
docs/implementation/
```

The final Slice #7 Concrete API Design remains the authoritative API contract.

Any implementation deviation must be reviewed before acceptance.

No intermediate API variants should be retained as competing designs.

---

# 30. Acceptance Criteria

Implementation is accepted when:

1. `inventory_balance.py` exists.
2. `INVENTORY_BALANCE_REPORT_IDENTITY` exists and is stable.
3. `INVENTORY_BALANCE_REPORT_DEFINITION` exists.
4. The definition references `inventory.balance`.
5. The definition contains exactly two dimensions: product and warehouse.
6. The definition contains exactly two measures: quantity SUM and cost SUM.
7. The base definition contains no filters.
8. The definition is exported through `standard.reporting`.
9. No generic Reporting API is modified.
10. The definition validates against the actual Inventory Balance source schema.
11. The complete generic execution pipeline executes the report successfully.
12. Basic Inventory Balance output is correct.
13. Multiple scopes are grouped correctly.
14. Output ordering is deterministic.
15. Generic filtering works through a derived report definition.
16. Explicit zero valuation cost remains zero.
17. Missing valuation state remains an error.
18. Valuation-only scopes do not create rows.
19. Empty Register state produces zero dimensioned rows.
20. Register and Valuation semantic state is unchanged by report execution.
21. No persistence/posting/FIFO/recovery dependency is introduced.
22. Full quality gate passes.

---

# 31. Implementation Order

Implementation should proceed in this order:

### Step 1

Create:

```text
src/standard/reporting/inventory_balance.py
```

with the report identity and immutable definition.

### Step 2

Export the two new symbols from:

```text
src/standard/reporting/__init__.py
```

### Step 3

Add definition/metadata tests.

### Step 4

Add the vertical execution fixture using the existing Standard source registry and semantic state.

### Step 5

Add end-to-end scenarios:

* basic balance;
* multiple scopes;
* filtering;
* zero cost;
* missing valuation;
* valuation-only scope;
* empty inventory;
* read-only state.

### Step 6

Run the targeted Reporting/Standard tests.

### Step 7

Run:

```text
pytest -q
ruff check .
black --check .
mypy src
```

### Step 8

Reconcile documentation.

No intermediate commit is required.

---

# 32. Final API Boundary

The final production API introduced by Slice #7 is intentionally minimal:

```python
INVENTORY_BALANCE_REPORT_IDENTITY
INVENTORY_BALANCE_REPORT_DEFINITION
```

Everything else is existing infrastructure.

The resulting dependency direction is:

```text
standard.reporting.inventory_balance
        │
        ├── ReportDefinition
        ├── ReportDimension
        ├── ReportMeasure
        ├── ReportAggregation
        │
        └── inventory.balance identity
                    │
                    ▼
          ReportDataSourceRegistry
                    │
                    ▼
       InventoryBalanceReportSource
                    │
              ┌─────┴─────┐
              ▼           ▼
          Register    Valuation
              │           │
              └─────┬─────┘
                    ▼
            Generic Runtime
                    │
                    ▼
              ReportDataset
```

No dependency points from generic Reporting back into Standard.

---

# 33. Final Design Decision

**Concrete API Design: Approved for Implementation.**

The implementation should remain deliberately small.

The architectural objective of Slice #7 is not to create a new Reporting framework layer. It is to prove that the existing generic Reporting framework can execute a real Standard Inventory report without acquiring domain-specific knowledge.

Therefore:

* one immutable Standard report definition;
* two new public symbols;
* zero generic Reporting changes;
* zero domain semantic changes;
* one vertical integration test boundary;
* no new production execution facade.

This is the complete public API for Slice #7.
