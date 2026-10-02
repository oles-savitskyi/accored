# PHASE 9 — Reporting

## Slice #5 — Concrete API Design

**Status:** Approved and implemented
**Architecture baseline:** `PHASE_9_REPORTING_ARCHITECTURE_DEFINITION_SCOPE.md`
**Implementation baseline:** `AcCoreD_cur9(5).zip`
**Previous slice:** Slice #4 — Reporting foundation / executable runtime scaffold
**Implementation status:** Completed

---

# 1. Purpose

Slice #5 completes and hardens the executable Reporting Runtime introduced during Slice #4.

This slice does **not** introduce a new Reporting architecture or replace the existing runtime model.

The existing API is retained:

```text
ReportDefinition
      ↓
ValidatedReportDefinition
      ↓
CompiledReport
      ↓
ReportExecutionPlan
      ↓
ReportRuntime
      ↓
ReportDataset
```

Slice #5 makes the runtime semantics explicit and complete for:

* source resolution;
* source read failures;
* filter evaluation;
* grouping;
* aggregation;
* empty-input behavior;
* nullable source values;
* deterministic result ordering;
* dataset/schema integrity;
* runtime error boundaries;
* immutable result semantics.

The resulting API becomes the stable generic Platform Reporting execution foundation for subsequent Standard-specific logical sources.

---

# 2. Existing API Baseline

The following Slice #4 public types are retained.

## 2.1 Values

```python
ReportValue
ReportDataType
```

`ReportValue` remains the immutable wrapper around supported Reporting scalar values:

* `Identifier`;
* `bool`;
* `int`;
* `Decimal`;
* `str`;
* `date`;
* timezone-aware `datetime`;
* `None`.

`float` remains excluded.

No new generic value system is introduced in Slice #5.

---

## 2.2 Schema

```python
ReportField
ReportSchema
```

The existing field contract remains authoritative.

A `ReportField` contains:

```python
name: str
data_type: ReportDataType
```

Slice #5 does **not** add a separate nullable-type hierarchy.

`ReportValue(None)` remains a valid value at the value boundary, but aggregate result semantics are explicitly defined below.

---

## 2.3 Dataset

```python
ReportRow
ReportDataset
```

Both remain immutable public result objects.

`ReportRow` defensively normalizes its mapping.

`ReportDataset` defensively normalizes its rows and verifies that every row has exactly the fields declared by its schema.

No mutable result representation is introduced.

---

# 3. Runtime Contract

The public runtime contract remains:

```python
class ReportRuntime(Protocol):
    def execute(
        self,
        plan: ReportExecutionPlan,
    ) -> ReportDataset:
        ...
```

The reference implementation remains:

```python
class DefaultReportRuntime:
    def __init__(
        self,
        sources: ReportDataSourceRegistry,
    ) -> None:
        ...

    def execute(
        self,
        plan: ReportExecutionPlan,
    ) -> ReportDataset:
        ...
```

No `ReportManager`, `ReportService`, or second orchestration abstraction is introduced.

---

# 4. Execution Pipeline

`DefaultReportRuntime.execute()` performs the following deterministic sequence:

```text
1. Resolve logical source
        ↓
2. Build semantic source request
        ↓
3. Read source rows
        ↓
4. Normalize source rows
        ↓
5. Apply report filters
        ↓
6. Build grouping keys
        ↓
7. Compute measures
        ↓
8. Construct ReportRows
        ↓
9. Canonically order result rows
        ↓
10. Construct ReportDataset
```

The runtime must not mutate:

* the execution plan;
* the compiled report;
* the report definition;
* source rows;
* authoritative Register state;
* authoritative Valuation state.

---

# 5. Logical Data Source Contract

The existing protocol remains:

```python
class ReportDataSource(Protocol):
    identity: ReportDataSourceIdentity

    def schema(self) -> ReportSchema:
        ...

    def consistency(self) -> ReportReadConsistency:
        ...

    def read(
        self,
        request: ReportDataSourceRequest,
    ) -> tuple[ReportRow, ...]:
        ...
```

The source remains a **read-only semantic boundary**.

Reporting runtime must not inspect or access:

* persistence providers;
* Register storage;
* Valuation fact persistence;
* mutation orchestrators;
* posting coordinators;
* recovery services.

---

# 6. Source Filter Push-Down

`ReportDataSourceRequest.filters` remains part of the source contract.

The runtime sends the report's filters to the source:

```python
ReportDataSourceRequest(
    filters=plan.filter_operation.filters,
)
```

The source may use those filters for efficient read/push-down.

However, runtime correctness must **not depend on push-down**.

Therefore runtime applies the same semantic filters again to the returned rows.

This establishes two distinct responsibilities:

```text
Source:
    optional/efficient filtering

Runtime:
    authoritative report filter semantics
```

A source returning rows that do not satisfy the requested filter must not cause an incorrect report result.

---

# 7. Filter Semantics

The existing operator vocabulary remains:

```python
class ReportFilterOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN = "in"
```

All filters in one report are combined using logical AND.

For a row:

```text
filter_1 AND filter_2 AND ... AND filter_n
```

A row must satisfy every filter to enter grouping/aggregation.

---

# 8. Filter Null Semantics

`None` is not a valid filter operand in Slice #5.

This is already enforced by `DefaultReportValidator`.

For a nullable source value:

```python
ReportValue(None)
```

all ordinary comparison operators evaluate to **not matched**.

Therefore:

```text
None == X       → false
None != X       → false
None > X        → false
None >= X       → false
None < X        → false
None <= X       → false
None IN (...)   → false
```

There is intentionally no `IS NULL` / `IS NOT NULL` operator in Slice #5.

That is a future filter extension rather than an implicit special case.

---

# 9. Grouping Semantics

The existing `ReportGroupOperation` remains unchanged.

If dimensions exist:

```text
row → dimension values → grouping key
```

Rows with equal dimension values belong to the same group.

Dimension order is significant.

Example:

```python
dimensions = (
    ReportDimension("warehouse", "warehouse"),
    ReportDimension("item", "item"),
)
```

produces keys in exactly that order:

```text
(warehouse_value, item_value)
```

If no dimensions exist, the runtime creates exactly one logical aggregate group.

Therefore:

```text
0 input rows + no dimensions
```

still represents one aggregate group.

This distinction is important for aggregate-only reports.

---

# 10. Empty Input Semantics

Slice #5 fixes and explicitly establishes empty-input behavior.

## 10.1 Dimensioned report

For:

```text
dimensions != ()
```

and zero rows after filtering:

```text
ReportDataset.rows == ()
```

No artificial dimension value is created.

---

## 10.2 Aggregate-only report

For:

```text
dimensions == ()
```

and zero rows after filtering:

```text
exactly one logical aggregate group
```

The resulting dataset therefore contains one row.

This is necessary for deterministic aggregate-only reporting.

---

# 11. Aggregation Vocabulary

The existing first-slice aggregation vocabulary is retained:

```python
class ReportAggregation(StrEnum):
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
```

`AVG` remains outside Slice #5.

No calculated expressions or derived measures are introduced.

---

# 12. COUNT Semantics

`COUNT` counts **input rows in the current group**.

It does not count:

* non-null values;
* distinct values;
* source-field values;
* physical persistence records.

For example:

```text
group contains 3 rows
COUNT → 3
```

For an empty aggregate-only group:

```text
COUNT → 0
```

`COUNT` does not require `source_field`.

Its output type remains:

```python
ReportDataType.INTEGER
```

---

# 13. SUM Semantics

`SUM` is supported only for:

```text
INTEGER
DECIMAL
```

source fields.

This remains validated by `DefaultReportValidator`.

## 13.1 Non-null values

For integer input:

```text
1 + 2 + 3 → 6
```

For Decimal input:

```text
Decimal("1.20") + Decimal("2.30")
→ Decimal("3.50")
```

Integer values may be promoted to `Decimal` when combined with Decimal values.

No float conversion is permitted.

---

## 13.2 Null values

`ReportValue(None)` values are ignored by `SUM`.

Example:

```text
10
None
20
```

produces:

```text
30
```

A null value is absence of an input value, not numeric zero.

---

## 13.3 Empty/all-null SUM

When a group contains no non-null numeric values, `SUM` returns the numeric identity appropriate to the source field type:

```text
INTEGER → ReportValue(0)

DECIMAL → ReportValue(Decimal("0"))
```

This keeps the result type consistent with the compiled output schema while providing deterministic aggregate-only results.

---

# 14. MIN / MAX Semantics

`MIN` and `MAX` operate on non-null values.

Null source values are ignored.

Example:

```text
5
None
8
```

produces:

```text
MIN → 5
MAX → 8
```

If a group contains no non-null values, `MIN` and `MAX` are undefined.

Slice #5 therefore raises:

```python
ReportValidationError
```

rather than fabricating a numeric or sentinel result.

This behavior is also used for an empty aggregate-only group.

The runtime must not return `None` for `MIN/MAX`, because the compiled output schema describes the measure using the source field's semantic type and Slice #5 does not introduce nullable output-schema metadata.

---

# 15. MIN / MAX Type Validation

`DefaultReportValidator` must validate that `MIN` and `MAX` are only used with source types having a defined Reporting ordering.

Supported types:

```text
INTEGER
DECIMAL
STRING
DATE
DATETIME
IDENTIFIER
```

`BOOLEAN` is rejected for `MIN/MAX`.

`NULL` is not a source schema type suitable for these aggregations.

This validation occurs before compilation/execution.

---

# 16. Aggregation Type Consistency

Runtime aggregation must not rely on Python's accidental cross-type comparison behavior.

The source schema is authoritative.

For every aggregate measure:

```text
ReportMeasure.source_field
        ↓
ReportSchema.field(...)
        ↓
declared ReportDataType
        ↓
runtime aggregation semantics
```

This prevents Python-specific behavior such as implicit ordering between unrelated scalar types from becoming part of the Reporting API.

---

# 17. Deterministic Ordering

The runtime guarantees deterministic ordering of result rows.

When dimensions exist, rows are ordered by the dimension values in declaration order.

Example:

```python
dimensions = (
    warehouse,
    item,
)
```

canonical ordering is:

```text
warehouse
    then item
```

Measure values do not determine result ordering.

This guarantees that identical source semantics and identical report plans produce the same row ordering.

---

# 18. Canonical Ordering of Values

Ordering must be type-aware.

The runtime must not directly compare arbitrary `ReportValue.value` objects across unrelated semantic types.

The canonical key includes the Reporting semantic type and then its value representation.

For identifiers, their stable string representation is used for ordering.

For null values, a stable null ordering is used.

No locale-dependent sorting or presentation-layer collation is introduced.

---

# 19. Dataset Construction

Every successful execution ends with:

```python
ReportDataset(
    schema=plan.compiled.output_schema,
    rows=result_rows,
)
```

The runtime must guarantee:

```text
every row field set == output schema field set
```

The ordering of fields in the result row must follow output schema construction:

```text
dimensions first
measures second
```

Within those categories, declaration order is preserved.

---

# 20. Dataset Immutability

The public result boundary is immutable.

Required properties:

```text
ReportDataset.rows → tuple
ReportRow.values → immutable mapping
ReportSchema.fields → tuple
ReportField → frozen
ReportValue → frozen
```

Attempting to mutate returned row mappings must not alter the dataset.

The runtime must not return internal mutable aggregation dictionaries.

---

# 21. Error Boundary

The runtime distinguishes between:

1. Reporting semantic/execution errors;
2. logical data-source failures.

## 21.1 Reporting-owned errors

Invalid runtime semantics are reported as:

```python
ReportValidationError
```

Examples:

* unsupported aggregation;
* invalid aggregate input type;
* invalid MIN/MAX operation;
* undefined MIN/MAX over an empty/non-null-free group;
* invalid filter operand semantics;
* inconsistent runtime operation.

---

## 21.2 Source errors

`ReportDataSourceError` and its subclasses remain source-owned.

Runtime must **not** catch every exception and replace it with a generic Reporting error.

In particular:

```python
source.read(...)
```

failure must not become:

```text
empty dataset
```

and must not silently become a generic `ReportValidationError`.

Source failures propagate through the runtime boundary unchanged unless a future explicit source-error translation contract is introduced.

---

# 22. Source Not Found

Source resolution remains:

```python
source = registry.get(plan.compiled.definition.source)
```

Missing sources raise:

```python
ReportDataSourceNotFoundError
```

The runtime does not reinterpret missing source as:

```text
empty report
```

This is an execution failure, not an empty result.

---

# 23. Read Consistency

The runtime may inspect:

```python
source.consistency()
```

for future consistency-aware execution.

Slice #5 does not introduce multi-source execution, joins, or transaction coordination.

For the current:

```python
ReportReadConsistency.SOURCE_LOCAL
```

contract, the runtime guarantees only the consistency semantics provided by that logical source.

Reporting must not strengthen the guarantee implicitly.

---

# 24. Report Execution Plan

The existing immutable plan remains the runtime contract:

```python
@dataclass(frozen=True, slots=True)
class ReportExecutionPlan:
    compiled: CompiledReport
    filter_operation: ReportFilterOperation | None
    group_operation: ReportGroupOperation | None
    aggregate_operation: ReportAggregateOperation
```

No new operation types are introduced in Slice #5.

The plan is already complete for the supported runtime vocabulary.

---

# 25. Plan/Definition Consistency

Runtime execution assumes that the plan has been produced by the approved validation/compilation pipeline.

The runtime must not mutate or repair an invalid plan.

The relationship is:

```text
ReportDefinition
      ↓
DefaultReportValidator
      ↓
ValidatedReportDefinition
      ↓
DefaultReportCompiler
      ↓
CompiledReport
      ↓
DefaultReportExecutionPlanBuilder
      ↓
ReportExecutionPlan
      ↓
DefaultReportRuntime
```

Direct construction of a plan remains technically possible because the dataclasses are public, but correctness guarantees are defined for plans produced from validated/compiled reports.

---

# 26. Compiler Contract

The existing:

```python
DefaultReportCompiler
```

remains responsible for constructing:

```python
CompiledReport.output_schema
```

The output schema contains:

```text
dimensions first
measures second
```

`COUNT` always produces:

```text
INTEGER
```

Other measures inherit their source field's semantic type.

Slice #5 may amend compiler behavior only where necessary to maintain the aggregation semantics defined above.

---

# 27. Validator Responsibilities

`DefaultReportValidator` remains responsible for semantic checks that should happen before execution.

It must validate:

### Filters

* field exists;
* operand is not `None`;
* operand type matches field type;
* `IN` operands all match field type.

### Dimensions

* source field exists.

### Measures

* source field exists where required;
* `COUNT` does not require a source field;
* `SUM` requires INTEGER or DECIMAL;
* `MIN/MAX` require an orderable Reporting type.

Runtime remains responsible for dynamic input validation where the source returns data inconsistent with its declared schema.

---

# 28. Source/Schema Runtime Integrity

Although validation happens before execution, the source is an external logical boundary.

Therefore runtime must defensively reject source rows that violate the source schema rather than producing an invalid dataset.

Examples:

```text
schema says DECIMAL
source returns STRING
```

or:

```text
schema contains fields A, B
source row contains A, C
```

Such conditions are Reporting execution/validation failures.

They must never be silently coerced.

No automatic:

```text
str → Decimal
float → Decimal
int → String
```

conversion is allowed.

---

# 29. No Float Conversion

The following invariant remains absolute:

```text
float
```

is not a valid Reporting semantic value.

Runtime must not introduce floats indirectly through aggregation or ordering.

Accounting-relevant numeric operations use:

```python
int
Decimal
```

only.

---

# 30. Public API Stability

The following existing exports remain public:

```text
CompiledReport
DefaultReportCompiler
DefaultReportDataSourceRegistry
DefaultReportExecutionPlanBuilder
DefaultReportRuntime
DefaultReportValidator

ReportAggregateOperation
ReportAggregation
ReportDataSource
ReportDataSourceError
ReportDataSourceIdentity
ReportDataSourceNotFoundError
ReportDataSourceRegistry
ReportDataSourceRequest
ReportDataType
ReportDataset
ReportDefinition
ReportDimension
ReportError
ReportExecutionPlan
ReportExecutionPlanBuilder
ReportField
ReportFilter
ReportFilterOperation
ReportFilterOperator
ReportGroupOperation
ReportMeasure
ReportPlanOperation
ReportReadConsistency
ReportRow
ReportRuntime
ReportSchema
ReportValidationError
ReportValidator
ReportValue
ValidatedReportDefinition
```

Slice #5 should not rename or relocate these public types unless implementation reveals a concrete dependency problem requiring API amendment.

---

# 31. Runtime Internal Structure

The current runtime may retain private helper methods corresponding to:

```text
_normalize_row()
_matches_all()
_matches_relational()
_aggregate()
_compute_aggregate()
_min_value()
_max_value()
_compare_values()
_canonical_key()
_value_sort_key()
```

These are implementation details.

They are not public API.

The implementation may refactor these helpers if behavior remains consistent with this design.

---

# 32. Test Contract

Slice #5 must expand `tests/unit/reporting/test_runtime.py` and related tests.

Required scenarios:

## 32.1 Existing behavior

* filters;
* grouping;
* SUM;
* COUNT;
* deterministic ordering.

## 32.2 Filter coverage

* equals;
* not equals;
* greater than;
* greater than or equal;
* less than;
* less than or equal;
* IN;
* multiple filters;
* nullable actual value;
* invalid filter operand semantics.

## 32.3 Grouping

* one dimension;
* multiple dimensions;
* no dimensions;
* empty dimensioned result;
* empty aggregate-only result.

## 32.4 Aggregation

* COUNT;
* integer SUM;
* Decimal SUM;
* SUM with null source values;
* empty integer SUM;
* empty Decimal SUM;
* MIN;
* MAX;
* MIN/MAX with null source values;
* MIN/MAX with no non-null values;
* invalid aggregate types.

## 32.5 Dataset integrity

* exact output schema;
* exact row fields;
* deterministic row order;
* immutable rows;
* immutable datasets.

## 32.6 Source failures

Tests must verify that:

```python
ReportDataSourceError
```

raised by `read()` is not converted to an empty dataset or an unrelated Reporting error.

## 32.7 Source integrity

Tests must cover source rows violating their declared schema.

---

# 33. Architecture Boundary Tests

The Slice #5 test suite must preserve the Platform boundary.

The runtime tests must not require:

* Register persistence;
* Valuation persistence;
* Standard-specific adapters;
* mutation services;
* posting services;
* recovery services.

A fake logical source remains sufficient for generic runtime tests.

---

# 34. Standard Integration Boundary

Slice #5 does not implement the Standard Inventory Balance logical source.

The runtime must remain generic.

The later Standard adapter may implement:

```python
ReportDataSource
```

and expose inventory-specific semantics through that contract.

The runtime must not import:

```text
accore.standard.*
```

or any Standard-specific inventory/valuation module.

---

# 35. Explicit Non-Goals

Slice #5 does not implement:

* cross-source joins;
* multi-source execution;
* calculated expressions;
* AVG;
* DISTINCT aggregation;
* sorting requested by a report definition;
* pagination;
* presentation;
* export;
* caching;
* query optimization;
* persistence of reports;
* report scheduling;
* authorization;
* dashboards;
* UI integration;
* Standard Inventory Balance source;
* Register/Valuation adapters.

---

# 36. Implementation Sequence

Implementation should proceed in this order:

### Step 1 — Runtime semantic hardening

Align `DefaultReportRuntime` with:

* empty-input semantics;
* null aggregate semantics;
* integer/Decimal SUM identity;
* MIN/MAX type constraints;
* source-schema integrity;
* deterministic ordering.

### Step 2 — Validator/compiler reconciliation

Update validation and output-schema behavior only where required by Step 1.

### Step 3 — Dataset immutability/integrity

Complete defensive guarantees and tests.

### Step 4 — Error semantics

Add explicit tests for:

* source propagation;
* source-not-found;
* runtime validation failures.

### Step 5 — Runtime test matrix

Expand unit tests to cover the full semantic contract.

### Step 6 — Public export reconciliation

Verify `reporting/__init__.py` exposes only the approved public vocabulary.

### Step 7 — Documentation reconciliation

Update the Slice #5 Architecture Definition / Scope and Concrete API Design if implementation reveals only factual documentation drift.

No architectural redesign is permitted during implementation without returning to review.

---

# 37. Quality Gate

Slice #5 is complete only when all of the following pass:

```bash
pytest -q
ruff check .
black --check .
mypy src
```

Additionally:

```bash
git diff --check
```

must report no whitespace errors.

The Reporting-specific test suite must explicitly cover all semantics defined in this document.

---

# 38. Completion Criteria

Slice #5 is complete when:

1. `DefaultReportRuntime` executes the existing `ReportExecutionPlan` contract end-to-end.
2. Empty-input semantics are explicit and tested.
3. COUNT/SUM/MIN/MAX semantics are explicit and tested.
4. Nullable source values have deterministic aggregate behavior.
5. Integer and Decimal SUM preserve semantic numeric types.
6. MIN/MAX type constraints are validated.
7. Source failures remain distinguishable from empty results.
8. Source/schema violations cannot silently produce invalid datasets.
9. Result ordering is deterministic.
10. `ReportDataset` remains immutable.
11. Runtime remains read-only.
12. Runtime remains independent of Standard-specific composition.
13. No cross-source/query-engine/presentation framework is introduced.
14. Full project quality gate passes.
15. Documentation reflects the actual implemented API.

---

# 39. Final API Decisions

The following decisions are considered closed for Slice #5:

| ID       | Decision                                                                             |
| -------- | ------------------------------------------------------------------------------------ |
| API-5.1  | Existing Slice #4 runtime is completed, not redesigned                               |
| API-5.2  | `ReportExecutionPlan` remains the sole executable plan contract                      |
| API-5.3  | Runtime re-applies filters after source read                                         |
| API-5.4  | Source failures propagate; they are never interpreted as empty results               |
| API-5.5  | Dimensioned empty result contains zero rows                                          |
| API-5.6  | Aggregate-only empty input produces one logical aggregate group                      |
| API-5.7  | COUNT over empty group is `0`                                                        |
| API-5.8  | SUM uses type-appropriate numeric identity for empty/all-null input                  |
| API-5.9  | MIN/MAX ignore null values but fail when no non-null value exists                    |
| API-5.10 | MIN/MAX are restricted to explicitly orderable Reporting types                       |
| API-5.11 | Runtime never introduces float conversion                                            |
| API-5.12 | Result ordering is deterministic and dimension-driven                                |
| API-5.13 | Dataset and rows remain defensively immutable                                        |
| API-5.14 | Source/schema contract violations are execution failures, not coercion opportunities |
| API-5.15 | No Standard-specific code enters `accore.platform.reporting`                         |
| API-5.16 | No cross-source execution is introduced in Slice #5                                  |

---

# 40. Approval Gate

This document is the Concrete API Design for Slice #5.

Implementation may begin against this contract.

Any proposed change affecting:

* public types;
* method signatures;
* aggregation semantics;
* empty-result semantics;
* null semantics;
* source error semantics;
* dataset immutability;
* Platform/Standard boundary

requires an explicit API amendment before implementation proceeds.
