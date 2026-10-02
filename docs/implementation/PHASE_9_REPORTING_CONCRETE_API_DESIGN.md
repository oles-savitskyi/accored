# PHASE 9 — WP-9 Reporting Concrete API Design

**Status:** Approved and implemented through Slice #7

**Architecture baseline:** `PHASE_9_REPORTING_ARCHITECTURE_DEFINITION_SCOPE.md`

**Architectural status:** Approved and implemented through Slice #7

**Implementation status:** Completed through Slice #7; Slice #8 documentation reconciliation and final quality gate completed

**Repository baseline:** AcCoreD `main` after WP-8 completion

**Baseline commits:**

- `5046a9c` — `feat(valuation): complete WP-8 Slice 10.7 repost recovery`
- `1812ad5` — `docs(phase8): finalize WP-8 documentation reconciliation`

---

# 1. Purpose

This document translates the approved WP-9 Architecture Definition / Scope into a concrete Python API design.

It defines:

- public domain types;
- immutable report metadata;
- logical data-source contracts;
- schema and row contracts;
- filters and aggregations;
- validation and compilation boundaries;
- execution-plan representation;
- runtime execution contract;
- analytical dataset representation;
- error taxonomy;
- Platform/Standard integration points;
- proposed module layout;
- public exports;
- test boundaries;
- implementation sequencing.

This document is the final API contract for WP-9 implementation. Implementation may begin from the approved slice sequence below; any change to public contracts or semantic invariants requires API amendment and review.

The design deliberately avoids implementing a generic Table Engine, Expression Engine, presentation framework, export framework, or reporting cache in WP-9.

---

# 2. Design Principles

## 2.1 Immutable public values

Report definitions, schemas, filters, execution plans, rows, and datasets are immutable value objects wherever practical.

## 2.2 Protocol-based integration

Logical data sources and runtime boundaries are expressed through `Protocol` contracts so Reporting does not depend on concrete Register, Valuation, or persistence implementations.

## 2.3 Metadata/runtime separation

A `ReportDefinition` is declarative metadata. Compilation produces runtime artifacts. Execution consumes compiled artifacts rather than mutating the definition.

## 2.4 Dataset as the terminal boundary

Successful execution returns one immutable `ReportDataset`.

Presentation, export, UI, and external API layers consume the dataset and are outside the WP-9 execution API.

## 2.5 One logical source per executable first slice

A report definition may refer to one logical `ReportDataSource`.

Cross-domain composition such as Inventory Balance is performed by a logical source adapter in Standard rather than by introducing a generic cross-source join engine in the first WP-9 implementation.

This keeps consistency semantics explicit and prevents Reporting from pretending that Register and Valuation provide an atomic transaction snapshot.

## 2.6 Domain semantics remain domain-owned

Reporting consumes semantic read results. It does not reproduce Register totals logic, valuation logic, FIFO logic, posting logic, or recovery logic.

---

# 3. Proposed Package Layout

```text
src/accore/platform/reporting/
    __init__.py
    definitions.py
    schema.py
    filters.py
    sources.py
    dataset.py
    execution.py
    compilation.py
    validation.py
    errors.py
```

The first implementation should keep the package small. Splitting individual concepts into additional modules is permitted only when the resulting dependency graph remains simple and the public API does not fragment unnecessarily.

Standard-specific adapters belong outside the generic package, for example:

```text
src/standard/reporting/
    __init__.py
    inventory.py
```

The exact Standard module names remain subject to API Review and implementation inspection.

---

# 4. Public Type Vocabulary

## 4.1 Report value

Reporting needs a controlled scalar vocabulary instead of using arbitrary Python objects as a semantic contract.

Proposed alias:

```python
type ReportValue = (
    str
    | int
    | Decimal
    | bool
    | date
    | datetime
    | Identifier
    | None
)
```

`float` is intentionally excluded, consistent with the accounting/valuation architecture's Decimal-only monetary semantics.

`Identifier` remains available because report datasets may need stable business identities while still remaining independent of physical persistence.

## 4.2 Field data type

```python
class ReportFieldType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    IDENTIFIER = "identifier"
```

A field schema declares the expected semantic type of its values.

---

# 5. Schema API

## 5.1 ReportField

```python
@dataclass(frozen=True, slots=True)
class ReportField:
    name: str
    field_type: ReportFieldType
    nullable: bool = False
    description: str | None = None
```

Invariants:

- `name` is non-empty;
- field names are unique inside a schema;
- `description`, when present, is informational only;
- field type is immutable.

## 5.2 ReportSchema

```python
@dataclass(frozen=True, slots=True)
class ReportSchema:
    fields: tuple[ReportField, ...]
```

The constructor validates uniqueness and provides deterministic field ordering.

Required semantic operations:

```python
class ReportSchema:
    def field(self, name: str) -> ReportField: ...
    def contains(self, name: str) -> bool: ...
```

The schema is the authoritative contract for logical source rows and dataset rows.

---

# 6. Data Row API

## 6.1 ReportRow

```python
@dataclass(frozen=True, slots=True)
class ReportRow:
    values: Mapping[str, ReportValue]
```

Construction validates values against the supplied `ReportSchema`.

The row is exposed as a read-only mapping.

The implementation must not expose a mutable dictionary to callers. The constructor must defensively copy/normalize the mapping into an immutable representation; `frozen=True` on the dataclass alone is insufficient.

## 6.2 Dataset rows

Rows returned by a logical data source are already normalized to the source schema. Runtime processing creates result rows matching the output schema.

---

# 7. Logical Data Source API

## 7.1 Source identity

```python
@dataclass(frozen=True, slots=True)
class ReportDataSourceIdentity:
    value: str
```

The identity is a stable logical name, not a persistence identifier.

Examples:

```text
inventory.balance
inventory_movements
inventory_cost_movements
```

## 7.2 Read request

The first slice does not introduce a generic query language at the source boundary.

```python
@dataclass(frozen=True, slots=True)
class ReportDataSourceRequest:
    filters: tuple[ReportFilter, ...] = ()
```

The source receives only semantic filters that it can evaluate without exposing physical storage. These filters are push-down hints: a source may apply compatible filters, but runtime correctness must not depend on the source having applied them. The runtime therefore preserves report semantics after source read.

## 7.3 Consistency declaration

```python
class ReportReadConsistency(StrEnum):
    SOURCE_LOCAL = "source_local"
```

A logical source declares the strongest consistency semantics it can guarantee.

For WP-9 first slice, `SOURCE_LOCAL` means:

> all rows returned by the logical source are derived from one source-owned read operation; Reporting does not claim an atomic snapshot across independent underlying subsystems.

A future source may expose stronger semantics without changing the Reporting execution model.

## 7.4 ReportDataSource protocol

```python
class ReportDataSource(Protocol):
    identity: ReportDataSourceIdentity

    def schema(self) -> ReportSchema: ...

    def consistency(self) -> ReportReadConsistency: ...

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]: ...
```

The source is read-only.

No `append`, `update`, `delete`, `replace`, `rebuild`, or mutation method is permitted on this protocol.

---

# 8. Filter API

## 8.1 Filter operator

The first executable slice supports a deliberately small operator set:

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

## 8.2 ReportFilter

```python
@dataclass(frozen=True, slots=True)
class ReportFilter:
    field: str
    operator: ReportFilterOperator
    value: ReportValue | tuple[ReportValue, ...]
```

Validation must ensure that `IN` receives a tuple of values and all other operators receive one scalar value.

Filter field existence and type compatibility are validated during report validation/compilation, not by the raw constructor alone. `IN` requires a non-empty tuple of compatible values. `None` is not a filter operand in the first slice; nullable-field filtering with explicit NULL semantics is deferred.

---

# 9. Dimensions

## 9.1 ReportDimension

```python
@dataclass(frozen=True, slots=True)
class ReportDimension:
    name: str
    source_field: str
    description: str | None = None
```

A dimension is an analytical grouping axis over one source field.

WP-9 first slice does not implement hierarchy traversal. Hierarchy metadata remains a future extension.

## 9.2 Dimension semantics

For a source row set:

```text
Dimension fields
        ↓
Group key
        ↓
Aggregation buckets
```

Dimensions must reference fields in the logical source schema.

---

# 10. Measures

## 10.1 Aggregation

```python
class ReportAggregation(StrEnum):
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
```

The first executable slice supports:

- `SUM` for Decimal/integer values;
- `COUNT` as input-row count, without a source field;
- `MIN` / `MAX` for orderable scalar values.

`AVG` is intentionally deferred. It requires an explicit Decimal precision/rounding contract and is not part of the first executable runtime.

## 10.2 ReportMeasure

```python
@dataclass(frozen=True, slots=True)
class ReportMeasure:
    name: str
    aggregation: ReportAggregation
    source_field: str | None = None
    description: str | None = None
```

The first WP-9 API intentionally does not expose an `expression` field.

Calculated measures such as:

```text
Profit = Amount - Cost
```

remain a future expression-engine integration point and must not cause a private formula engine to appear inside Reporting.

## 10.3 Measure validation

Validation must check:

- `SUM`, `MIN`, and `MAX` require a source field;
- `COUNT` does not require a source field and counts input rows;
- aggregation is compatible with the source field type when a source field is present;
- measure names are unique;
- a measure name does not collide with a dimension output name.

---

# 11. Report Definition

## 11.1 ReportDefinition

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

Optional metadata such as description may be added if required by existing definition conventions, but must not affect execution semantics.

## 11.2 Definition invariants

- identity is required;
- name is non-empty;
- source identity is required;
- dimension names are unique;
- measure names are unique;
- dimension/measure names do not collide;
- a report must contain at least one dimension or measure;
- all source fields are validated against the source schema during compilation.

---

# 12. Validation API

## 12.1 ValidatedReportDefinition

Validation produces an immutable validated artifact rather than a boolean result.

```python
@dataclass(frozen=True, slots=True)
class ValidatedReportDefinition:
    definition: ReportDefinition
    source_schema: ReportSchema
```

## 12.2 ReportValidator protocol

```python
class ReportValidator(Protocol):
    def validate(
        self,
        definition: ReportDefinition,
        source: ReportDataSource,
    ) -> ValidatedReportDefinition: ...
```

Validation must reject:

- unknown fields;
- duplicate names;
- incompatible aggregations;
- invalid filters;
- invalid report structure;
- unsupported source/schema combinations.

Validation errors are deterministic and side-effect free.

---

# 13. Compilation API

## 13.1 CompiledReport

```python
@dataclass(frozen=True, slots=True)
class CompiledReport:
    definition: ReportDefinition
    source_schema: ReportSchema
    output_schema: ReportSchema
```

Compilation determines the output schema before execution.

The first implementation does not require a separate expression compiler.

## 13.2 ReportCompiler

```python
class ReportCompiler(Protocol):
    def compile(
        self,
        validated: ValidatedReportDefinition,
    ) -> CompiledReport: ...
```

The compiler must not execute the data source and must not mutate source state.

---

# 14. Execution Plan

## 14.1 Typed plan operations

The execution plan contains immutable operation specifications, not bare operation enums. The first executable plan supports filtering, grouping, and aggregation. Ordering is intentionally not a public report operation in WP-9 first slice.

```python
@dataclass(frozen=True, slots=True)
class ReportFilterOperation:
    filters: tuple[ReportFilter, ...]

@dataclass(frozen=True, slots=True)
class ReportGroupOperation:
    dimensions: tuple[ReportDimension, ...]

@dataclass(frozen=True, slots=True)
class ReportAggregateOperation:
    measures: tuple[ReportMeasure, ...]

ReportPlanOperation = (
    ReportFilterOperation
    | ReportGroupOperation
    | ReportAggregateOperation
)
```

Projection is implicit in the compiled output schema for the first slice. Calculated expression nodes are intentionally absent.

## 14.2 ReportExecutionPlan

```python
@dataclass(frozen=True, slots=True)
class ReportExecutionPlan:
    compiled: CompiledReport
    filter_operation: ReportFilterOperation | None
    group_operation: ReportGroupOperation | None
    aggregate_operation: ReportAggregateOperation
```

The plan is immutable and contains the parameters required for deterministic execution.

## 14.3 Plan builder

```python
class ReportExecutionPlanBuilder(Protocol):
    def build(
        self,
        compiled: CompiledReport,
    ) -> ReportExecutionPlan: ...
```

For the first slice, the plan builder may use a fixed deterministic operation order:

```text
source read
    ↓
filter
    ↓
group
    ↓
aggregate
    ↓
materialize dataset
```

No cost-based optimization is required.

---

# 15. Report Execution API

## 15.1 Execution request

```python
@dataclass(frozen=True, slots=True)
class ReportExecutionRequest:
    definition: ReportDefinition
```

Runtime dependencies such as source registry, validator, compiler, and plan builder are injected into the runtime service rather than placed in the request.

## 15.2 ReportRuntime protocol

```python
class ReportRuntime(Protocol):
    def execute(
        self,
        request: ReportExecutionRequest,
    ) -> ReportDataset: ...
```

The runtime lifecycle is:

```text
ReportDefinition
      ↓
resolve logical source
      ↓
validate
      ↓
compile
      ↓
build execution plan
      ↓
read source
      ↓
apply filters
      ↓
group / aggregate
      ↓
materialize dataset
```

## 15.3 Runtime implementation

Proposed implementation:

```python
class DefaultReportRuntime:
    def __init__(
        self,
        sources: ReportDataSourceRegistry,
        validator: ReportValidator,
        compiler: ReportCompiler,
        plan_builder: ReportExecutionPlanBuilder,
    ) -> None: ...
```

The runtime is orchestration, not a domain engine.

---

# 16. Data Source Registry

A small registry is required to resolve the logical source identity from a report definition.

```python
class ReportDataSourceRegistry(Protocol):
    def get(
        self,
        identity: ReportDataSourceIdentity,
    ) -> ReportDataSource: ...
```

Reference implementation:

```python
class DefaultReportDataSourceRegistry:
    def __init__(
        self,
        sources: Sequence[ReportDataSource],
    ) -> None: ...
```

The registry must reject duplicate logical source identities.

No dynamic discovery or persistence-backed source registry is part of WP-9.

---

# 17. Dataset API

## 17.1 ReportDataset

```python
@dataclass(frozen=True, slots=True)
class ReportDataset:
    schema: ReportSchema
    rows: tuple[ReportRow, ...]
```

The dataset is immutable.

The row sequence is deterministic according to the canonical group-key ordering defined in Section 30.

## 17.2 Dataset identity

WP-9 does not assign a persistent identity to a dataset. A dataset is an execution result, not a persisted business object.

## 17.3 Dataset semantics

The dataset must:

- match its schema;
- contain no mutable row mappings;
- preserve deterministic ordering;
- contain only values from the declared `ReportValue` vocabulary;
- remain independent from presentation/rendering.

---

# 18. Sorting

Explicit sorting is not part of the first WP-9 public API. The execution plan therefore has no `ORDER` operation.

The runtime must nevertheless produce deterministic output ordering using a canonical type-aware ordering of the compiled group key fields. A future explicit `ReportSort` value may be introduced with a separate API amendment.

---

# 19. Source Adapter Contract for Register

Reporting must not depend directly on `RegisterFactPersistence`.

A Register adapter may implement `ReportDataSource` by consuming the existing semantic query service:

```python
class RegisterMovementReportSource:
    def __init__(
        self,
        query_service: MovementQueryService,
    ) -> None: ...
```

The adapter maps `Movement` into `ReportRow` values.

The mapping is responsible for exposing only an intentional logical schema, for example:

```text
movement_identity
source_document_identity
register_identity
movement_type
accounting_time
<selected dimensions>
<selected resources>
```

The adapter must not expose arbitrary persistence fields merely because they happen to exist internally.

---

# 20. Source Adapter Contract for Valuation

A valuation report source must consume semantic valuation read results through a narrow read-only reporting adapter/protocol. It must not expose the full `ValuationResultPersistence` contract to Reporting.

Reporting itself must not import or use valuation mutation/recovery APIs.

The logical schema may expose:

```text
valuation_key dimensions
quantity
cost
source_identity
created_at
```

where those values are derived from `CostMovement` or `CostBalance` according to the specific logical source contract.

The adapter must explicitly define whether it exposes:

- movement-level data;
- balance-level data;
- both as distinct logical sources.

They must not be conflated into one ambiguous schema.

---

# 21. Standard Inventory Logical Source

The first cross-domain vertical slice should be implemented as a Standard logical source rather than as a generic Reporting join engine.

Proposed concept:

```python
class InventoryBalanceReportSource:
    ...
```

Its responsibility is to compose:

```text
Register semantic balance read
        +
Valuation semantic cost-balance read
        ↓
Inventory logical rows
```

For an Inventory Balance report, the valuation side consumes `CostBalance` semantics. Reporting must not reconstruct current cost by summing historical `CostMovement` records.

The source owns the mapping between Standard Inventory semantics and generic Reporting schema.

Generic Reporting must know nothing about:

- Inventory Product dimension constants;
- Inventory Warehouse dimension constants;
- FIFO;
- goods receipt;
- Standard posting contracts.

Those remain Standard responsibilities.

---

# 22. Cross-Source Consistency Contract

The first WP-9 implementation does not claim atomic transaction consistency between independently owned Register and Valuation state. `InventoryBalanceReportSource` performs deterministic semantic composition:

1. read Register balance state for the requested logical scope;
2. read Valuation `CostBalance` state for the same logical scope;
3. map both through the Standard-owned dimension/valuation-key mapping;
4. correlate by the canonical Inventory logical key;
5. fail execution if either source cannot provide semantically valid data;
6. never initiate rebuild, recovery, mutation, or persistence writes.

The adapter must document that the result is a composed read, not an atomic cross-subsystem snapshot. The generic Reporting API must not introduce a Register + Valuation transaction coordinator.

---

# 23. Error Taxonomy

Proposed base exception:

```python
class ReportingError(Exception):
    """Base error for Reporting failures."""
```

Validation:

```python
class ReportValidationError(ReportingError, ValueError):
    """Raised when a report definition is semantically invalid."""
```

Source resolution:

```python
class ReportDataSourceError(ReportingError):
    """Raised when a logical report data source cannot be resolved or read."""

class ReportDataSourceNotFoundError(ReportDataSourceError):
    """Raised when a logical report data source is not registered."""
```

Compilation:

```python
class ReportCompilationError(ReportingError):
    """Raised when a validated report cannot be compiled."""
```

Execution:

```python
class ReportExecutionError(ReportingError):
    """Raised when a compiled report cannot be executed."""
```

Dataset materialization:

```python
class ReportDatasetError(ReportingError):
    """Raised when an execution result violates dataset invariants."""
```

The implementation must preserve the original cause when wrapping domain/source errors.

Reporting must not translate a Valuation recovery state into a false successful dataset.

---

# 24. Failure Semantics

## 24.1 Validation failure

No source read is performed.

## 24.2 Compilation failure

No source read is performed.

## 24.3 Source read failure

Execution fails. No partial `ReportDataset` is returned.

## 24.4 Unsupported aggregation

Compilation/validation fails before source execution where the incompatibility can be detected from schema metadata.

## 24.5 Dataset invariant failure

Execution fails with `ReportDatasetError`. No partially materialized dataset is returned to callers.

## 24.6 Valuation recovery state

Reporting does not initiate recovery. If the logical valuation source cannot provide valid semantic data under its contract, the report execution fails explicitly.

---

# 25. Public API Surface

The first WP-9 public surface is intentionally small and limited to semantic contracts and immutable values:

```python
ReportAggregation
ReportDataSource
ReportDataSourceIdentity
ReportDataSourceRegistry
ReportDataSourceRequest
ReportDefinition
ReportDimension
ReportExecutionRequest
ReportField
ReportFieldType
ReportFilter
ReportFilterOperator
ReportReadConsistency
ReportMeasure
ReportRow
ReportRuntime
ReportSchema
ReportValue
ReportDataset
ReportingError
ReportValidationError
ReportDataSourceError
ReportDataSourceNotFoundError
ReportCompilationError
ReportExecutionError
ReportDatasetError
```

`ValidatedReportDefinition`, `CompiledReport`, typed execution-plan operation classes, and default service implementations may remain module-level implementation artifacts unless an external integration requires them. They must not be exported merely for convenience.

Only types actually required by the implementation should be promoted to public exports.

# 26. Dependency Direction

The intended dependency direction is:

```text
accore.platform.reporting
        │
        ├── foundation.Identifier
        └── standard-independent abstractions

Register ───────────────► reporting adapters
Valuation ──────────────► reporting adapters
Standard ───────────────► reporting adapters / concrete reports
```

The generic Reporting package must not import `standard`.

The generic Reporting package must not import Register persistence or Valuation persistence implementations merely to define its public API.

Adapters may depend on domain contracts.

---

# 27. Inventory Vertical Slice API Shape

The first end-to-end test should be expressible conceptually as:

```python
source = InventoryBalanceReportSource(...)

runtime = DefaultReportRuntime(
    sources=DefaultReportDataSourceRegistry([source]),
    validator=DefaultReportValidator(),
    compiler=DefaultReportCompiler(),
    plan_builder=DefaultReportExecutionPlanBuilder(),
)

report = ReportDefinition(
    identity=Identifier.new(),
    name="Inventory Balance",
    source=ReportDataSourceIdentity("inventory.balance"),
    filters=(),
    dimensions=(
        ReportDimension(
            name="Product",
            source_field="product",
        ),
        ReportDimension(
            name="Warehouse",
            source_field="warehouse",
        ),
    ),
    measures=(
        ReportMeasure(
            name="Quantity",
            source_field="quantity",
            aggregation=ReportAggregation.SUM,
        ),
        ReportMeasure(
            name="Cost",
            source_field="cost",
            aggregation=ReportAggregation.SUM,
        ),
    ),
)

dataset = runtime.execute(ReportExecutionRequest(report))
```

The exact Standard source construction and field names are deliberately subject to API Review and existing Standard naming conventions.

---

# 28. First-Slice Execution Semantics

For the Inventory Balance vertical slice:

1. resolve `inventory.balance` logical source;
2. validate report definition against source schema;
3. compile report;
4. build deterministic execution plan;
5. read logical inventory rows;
6. apply report filters;
7. group by Product + Warehouse;
8. aggregate Quantity and Cost;
9. materialize immutable dataset;
10. return dataset.

No posting, valuation calculation, rebuild, mutation, or persistence write occurs during any step.

---

# 29. Testing API Contracts

## Unit tests

Required unit coverage:

- field validation;
- schema validation;
- immutable rows;
- filter validation;
- aggregation compatibility;
- dimension/measure name uniqueness;
- report definition validation;
- compilation;
- typed execution-plan construction;
- deterministic aggregation and canonical output ordering;
- dataset materialization;
- error wrapping.

## Contract tests

Required contracts:

- `ReportDataSource` schema/read consistency;
- `ReportDataSourceRegistry` identity resolution;
- `ReportValidator` rejects unknown fields;
- `ReportCompiler` does not read sources;
- `ReportRuntime` returns schema-consistent datasets.

## Vertical tests

At least one Standard Inventory vertical test must prove:

```text
Register + Valuation semantic state
        ↓
Inventory logical source
        ↓
Report runtime
        ↓
Inventory analytical dataset
```

The test must also prove that Reporting does not mutate either subsystem.

## Recovery-related test

A valuation source that refuses to provide valid semantic data while in an unrecoverable/indeterminate state must cause report execution failure rather than trigger recovery.

---

# 30. Determinism Requirements

Given equivalent source rows and the same report definition:

- output schema must be identical;
- row grouping must be identical;
- aggregate values must be identical;
- output ordering must be deterministic;
- no implementation-dependent dictionary iteration may define externally observable ordering.

The first WP-9 runtime establishes deterministic canonical ordering for grouped output by comparing group-key values in compiled dimension order, using type-aware comparison and the existing semantic value ordering rules. Dictionary insertion order is never an externally observable ordering contract.

---

# 31. Decimal and Temporal Semantics

All monetary and accounting quantities exposed through Reporting must preserve `Decimal` values.

Reporting must not convert `Decimal` values to `float`.

`AVG` is not part of the first executable aggregation vocabulary. It will require a separate precision/rounding contract before being introduced.

`datetime` values must be timezone-aware. Naive datetimes are rejected by schema/value validation. `date` and `datetime` remain distinct semantic types.

Boolean values are validated as boolean before integer compatibility is considered; `bool` must never be accepted merely because it is a Python subclass of `int`.

---

# 32. Persistence Boundary

The generic Reporting API contains no persistence protocol.

A source adapter may internally consume an existing semantic read contract, but the Reporting runtime only sees `ReportDataSource`.

This prevents the architecture from creating:

```text
ReportRuntime → Persistence → Register/Valuation internals
```

and instead enforces:

```text
ReportRuntime → ReportDataSource → Domain semantic read
```

---

# 33. Standard Composition Boundary

Standard owns concrete business reports and domain-specific source adapters.

The first implementation should therefore keep the generic API free of names such as:

- InventoryBalance;
- Product;
- Warehouse;
- GoodsReceipt;
- FIFO.

Those concepts may appear in `src/standard/reporting/` and its tests.

---

# 34. Explicitly Deferred API Surfaces

The following are intentionally not public in the first WP-9 API:

```text
Expression
CalculatedMeasure
DimensionHierarchy
JoinDefinition
PivotDefinition
PresentationDefinition
Renderer
Exporter
DatasetCache
QueryOptimizer
OLAPCube
Dashboard
```

Their absence is intentional and does not invalidate the long-term Reporting architecture.

---

# 35. Implementation Sequence Proposed for API Review

After API approval, implementation should proceed in small slices:

### Slice 1 — Reporting foundation

- package;
- errors;
- scalar/value types;
- schema;
- row;
- dataset.

### Slice 2 — Definition model

- filters;
- dimensions;
- measures;
- report definition;
- validation.

### Slice 3 — Logical data source boundary

- source identity;
- source request;
- source protocol;
- source registry;
- contract tests.

### Slice 4 — Compilation and execution plan

- validated definition;
- compiled report;
- plan;
- plan builder.

### Slice 5 — Runtime

- runtime orchestration;
- filter/group/aggregate execution;
- deterministic dataset materialization.

### Slice 6 — Standard Inventory adapter

- Inventory logical source;
- Register read integration;
- Valuation read integration;
- consistency semantics.

### Slice 7 — End-to-end vertical report

- Inventory Balance report definition;
- component/vertical tests;
- regression tests proving no domain mutation.

### Slice 8 — Documentation reconciliation and quality gate

- API documentation;
- architecture reconciliation;
- pytest;
- ruff;
- black;
- mypy.

The exact slice boundaries may be amended after API Review but implementation must not begin before API approval.

---

# 36. Final API Decisions

The API Review has resolved the following questions and these decisions are binding for WP-9 implementation.

## API-Q1 — ReportDefinition identity

Use the existing platform `Identifier`. No second report identity primitive is introduced.

## API-Q2 — Source identity

Use dedicated immutable `ReportDataSourceIdentity`. It is a logical source name and is not a persistence identifier or field name.

## API-Q3 — Report value vocabulary

`Identifier` remains part of `ReportValue`. Boolean validation is type-aware and `datetime` must be timezone-aware.

## API-Q4 — Ordering

No public `sorts` field in the first slice. Output ordering is deterministic through canonical type-aware ordering of compiled group keys.

## API-Q5 — AVG

`AVG` is deferred and is not part of the first executable aggregation vocabulary.

## API-Q6 — Valuation source boundary

Standard introduces a narrow read-only valuation reporting adapter/protocol. Reporting does not depend on `ValuationResultPersistence` or valuation mutation/recovery APIs.

## API-Q7 — Inventory Balance source semantics

Inventory Balance is one Standard-owned composed logical source. Generic Reporting joins remain deferred. The balance report consumes Register balance semantics plus Valuation `CostBalance` semantics.

## API-Q8 — Report manager

`ReportRuntime` is the first executable boundary. No `ReportManager` façade is introduced in WP-9.

## API-Q9 — COUNT

`COUNT` means count of input rows and therefore does not require `source_field`. `COUNT DISTINCT` is deferred.

## API-Q10 — Execution plan representation

Execution plans contain typed immutable operation specifications, not only enum names. The first plan contains filter, group, and aggregate operations.

## API-Q11 — Cross-source consistency

Inventory Balance uses deterministic semantic composition and explicitly does not claim atomic cross-subsystem snapshot semantics.

## API-Q12 — Dataset immutability

Rows and dataset mappings/sequences are defensively normalized to immutable representations; `frozen=True` alone is not considered sufficient.

# 37. Implementation Reconciliation

The approved API design has been implemented through Slice #7. The concrete Standard vertical uses:

- source identity `inventory.balance`;
- report identity `01ARZ3NDEKTSV4RRFFQ69G5FB0`;
- report name `Inventory Balance`;
- dimensions `product` and `warehouse`;
- measures `SUM(quantity)` and `SUM(cost)`;
- immutable base definition with no filters;
- generic runtime filtering through immutable derived definitions;
- Standard-owned source composition over Register `TotalsReader` and Valuation `CostTotalsReader`.

No additional generic Reporting API was introduced by Slice #7.

# 38. Approval Criteria

The Concrete API Design is ready for implementation only after API Review confirms:

1. public type names and module boundaries;
2. source/schema/row contract;
3. definition/validation/compilation contract;
4. execution-plan contract;
5. dataset contract;
6. first-slice aggregation semantics;
7. Standard Inventory adapter boundary;
8. cross-source consistency semantics;
9. error taxonomy;
10. implementation slice order.

All approval criteria have been reviewed and resolved. This document is **Approved and implemented through Slice #7**.
