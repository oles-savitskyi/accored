# AcCoreD — Phase 9 Slice #5

## Architecture Definition / Scope

**Status:** Approved and implemented
**Phase:** Phase 9 — Reporting
**Slice:** #5
**Baseline:** `AcCoreD_cur9(5).zip`
**Previous Slice:** Slice #4 — completed
**Git policy:** no intermediate commit unless technically necessary; otherwise commit and push at Phase 9 completion.

---

# 1. Purpose

Phase 9 introduces the Reporting subsystem as a read-only analytical layer over authoritative application state.

Slice #5 completes and hardens the executable Reporting Runtime already present in the Slice #4 baseline.

The objective is not to introduce a new runtime architecture, but to verify and complete the semantic contract between:

```text
ReportDefinition
      ↓
ValidatedReportDefinition
      ↓
ReportExecutionPlan
      ↓
ReportRuntime
      ↓
ReportDataset
```

The runtime must execute an immutable, validated execution plan against a registered logical data source and produce a deterministic immutable dataset.

Slice #5 therefore establishes the **executable semantic boundary of Reporting** before Standard-specific data-source composition is introduced.

---

# 2. Baseline

The Slice #4 snapshot already contains the Reporting runtime implementation and associated tests.

The relevant platform package is:

```text
src/accore/platform/reporting/
    __init__.py
    values.py
    errors.py
    schema.py
    dataset.py
    filters.py
    definition.py
    datasource.py
    validation.py
    compile.py
    plan.py
    runtime.py
```

The baseline also contains:

```text
tests/unit/reporting/
    test_values.py
    test_definition.py
    test_datasource.py
    test_compile.py
    test_plan.py
    test_runtime.py
```

The existing runtime implementation must therefore be treated as the starting point.

Slice #5 must not duplicate or replace already-established abstractions merely because they belong conceptually to the Runtime layer.

---

# 3. Architectural Objective

Slice #5 establishes the following invariant:

> Given a valid immutable `ReportExecutionPlan` and a valid registered `ReportDataSource`, execution produces a deterministic immutable `ReportDataset` without mutating authoritative application state or depending on Standard-specific composition.

The runtime is therefore:

```text
read-only
deterministic
plan-driven
source-agnostic
immutable at its public result boundary
```

---

# 4. Architectural Position

The resulting architecture is:

```text
                    Reporting Definition
                           │
                           ▼
                  Validated Definition
                           │
                           ▼
                  Execution Plan
                           │
                           ▼
                    Report Runtime
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       Data Source Registry       Execution Semantics
              │                         │
              ▼                         ▼
       Logical Data Source      Filter / Group / Aggregate
              │                         │
              └────────────┬────────────┘
                           ▼
                     Report Dataset
```

The runtime does not know whether the source ultimately represents:

* Inventory;
* Register;
* Valuation;
* a composed Standard source;
* or another future reporting source.

Those concerns belong to the `ReportDataSource` boundary.

---

# 5. Scope

## 5.1 Runtime Contract

Slice #5 verifies and completes the runtime contract represented by:

```text
ReportRuntime
DefaultReportRuntime
```

The runtime accepts an already validated/compiled execution plan.

It must not reimplement report-definition validation.

It must not mutate the execution plan.

It must not mutate the source.

It must not mutate the resulting dataset after materialization.

---

# 6. Execution Pipeline

Runtime execution follows this conceptual pipeline:

```text
ReportExecutionPlan
        │
        ▼
resolve ReportDataSource
        │
        ▼
read source rows
        │
        ▼
apply filters
        │
        ▼
form groups
        │
        ▼
evaluate aggregates
        │
        ▼
materialize ReportRows
        │
        ▼
materialize ReportDataset
```

Each stage operates on data already defined by the immutable execution plan.

The runtime must not introduce a second interpretation of the report definition.

---

# 7. Data Source Boundary

The runtime consumes logical data through the Reporting data-source abstraction.

Conceptually:

```text
ReportRuntime
     │
     ▼
ReportDataSourceRegistry
     │
     ▼
ReportDataSource
     │
     ▼
source records
```

The runtime may resolve and read a source.

The runtime may not:

* access persistence directly;
* access Register internals directly;
* access Valuation persistence directly;
* perform writes;
* rebuild derived state;
* perform recovery;
* depend on Standard-specific adapters.

This preserves Reporting as a platform-level analytical boundary.

---

# 8. Filter Semantics

Slice #5 covers execution of the filter operations already admitted by the Reporting vocabulary.

The runtime must evaluate filters against source rows according to their compiled representation.

Required semantic properties:

* deterministic evaluation;
* explicit treatment of missing fields;
* explicit operand/type handling;
* no implicit mutation;
* no dependence on Python object identity.

The runtime must not silently reinterpret invalid filter expressions.

Invalid execution conditions must result in Reporting-domain errors rather than arbitrary Python exceptions leaking through the public API.

---

# 9. Grouping Semantics

Grouping is performed according to the dimensions contained in the execution plan.

For a dimension set:

```text
[d1, d2, ..., dn]
```

rows having equivalent dimension values belong to the same logical group.

For an empty dimension set:

```text
[]
```

the runtime must use a single logical aggregate group when aggregate measures are present.

Grouping must be deterministic.

The implementation must not expose dictionary/hash iteration order as report ordering.

---

# 10. Aggregation Semantics

Slice #5 covers execution of the executable aggregate vocabulary established by the Reporting API.

This includes:

```text
COUNT
SUM
MIN
MAX
```

`AVG` remains outside the executable vocabulary of this slice.

## COUNT

`COUNT` counts input rows contributing to the logical group according to the established Reporting semantics.

It does not mean:

* count of distinct values;
* count of non-null values;
* count of physical persistence records unless the source defines those as reporting rows.

## SUM

`SUM` must preserve the established numeric semantics.

The runtime must not introduce floating-point accounting semantics.

Where accounting values are represented as `Decimal`, aggregation must preserve `Decimal` semantics.

## MIN / MAX

`MIN` and `MAX` operate only over compatible values admitted by the Reporting type contract.

Unsupported heterogeneous comparisons must not be silently coerced.

---

# 11. Numeric Semantics

Reporting must remain compatible with the accounting-oriented numeric model already established elsewhere in AcCoreD.

In particular:

```text
Decimal
```

is the authoritative representation for accounting quantities.

The runtime must not convert accounting `Decimal` values to `float`.

Mixed numeric inputs are accepted only where the Reporting value contract explicitly permits them.

No new numeric coercion rules are introduced by Slice #5.

---

# 12. Empty Input Semantics

Slice #5 must explicitly define and test runtime behavior for an empty source.

The result must be deterministic.

The runtime must distinguish:

```text
no input rows
```

from:

```text
invalid source
```

and from:

```text
invalid execution plan
```

For aggregate-only execution without dimensions, the empty-input behavior must follow the established aggregate semantics rather than being accidentally determined by implementation details.

The exact public result representation will be finalized during Concrete API Design if the current implementation does not already establish it unambiguously.

---

# 13. Deterministic Output

Determinism is a first-class Reporting invariant.

For the same:

```text
ReportExecutionPlan
+
logical source state
```

the runtime must produce equivalent dataset contents and ordering.

Ordering must not depend on:

* hash randomization;
* dictionary insertion order;
* set iteration;
* database-specific incidental ordering;
* object identity.

Canonical ordering rules must be explicit in the runtime implementation.

---

# 14. Dataset Materialization

The runtime produces:

```text
ReportDataset
```

containing immutable report rows and the corresponding report schema.

The result boundary must protect against accidental mutation.

In particular, callers must not be able to mutate:

* the row collection;
* row mappings;
* nested mutable values;
* schema metadata;

through references retained by the runtime or source.

The runtime therefore follows:

```text
mutable source representation
        ↓
runtime transformation
        ↓
immutable public dataset
```

---

# 15. Immutability

The following objects are considered immutable architectural boundaries:

```text
ReportDefinition
ValidatedReportDefinition
ReportExecutionPlan
ReportDataset
ReportRow
```

Slice #5 must not introduce APIs that mutate these objects.

The runtime may use internal mutable structures during execution where required for implementation, provided those structures do not escape the execution boundary.

---

# 16. Error Boundary

The runtime must expose Reporting-specific errors for invalid execution conditions.

The following classes of failure are distinct:

### Invalid report plan

The execution plan violates its own established invariants.

This should not normally be possible when constructed through the validated compilation path, but defensive runtime behavior may still be required.

### Invalid source interaction

The source cannot satisfy the requested logical read contract.

This remains a data-source concern and must not be silently converted into an empty report.

### Invalid operation

The plan requests an operation unsupported by the runtime vocabulary.

This is a Reporting execution error.

### Invalid value/type

A source row contains a value incompatible with the requested Reporting operation.

This must not result in arbitrary implicit coercion.

The precise error classes and inheritance hierarchy belong to Concrete API Design.

---

# 17. Read-Only Guarantee

The Reporting runtime is strictly read-only.

Execution must not:

```text
create persistence records
update persistence records
delete persistence records
modify Register state
modify Valuation state
trigger posting
trigger reversal
trigger repost
trigger rebuild
```

Reporting observes state; it does not participate in domain mutation workflows.

---

# 18. Platform / Standard Boundary

Slice #5 remains entirely inside:

```text
accore.platform.reporting
```

No Standard-specific import is permitted.

The runtime must not know:

```text
InventoryRegister
InventoryBalance
Valuation
StandardConfiguration
```

as concrete implementation concepts.

Future Standard-specific reporting sources will adapt their domain state to the generic Reporting data-source contract.

---

# 19. Out of Scope

The following are explicitly excluded from Slice #5.

## 19.1 Standard Inventory Source

No implementation of:

```text
InventoryBalanceReportSource
```

or equivalent Standard-specific source belongs here.

## 19.2 Register Integration

No direct Register integration.

## 19.3 Valuation Integration

No direct Valuation integration.

## 19.4 Cross-Domain Composition

No Inventory + Valuation composition.

## 19.5 Presentation

No:

* CSV;
* JSON;
* HTML;
* table rendering;
* UI model;
* presentation formatting.

## 19.6 Export

No report export infrastructure.

## 19.7 Sorting API

Ordering needed for deterministic runtime output is in scope.

A user-facing configurable report sorting feature is not.

## 19.8 Expression Engine

No general-purpose expression language.

## 19.9 Query Optimizer

No cost-based optimization.

## 19.10 Caching

No report result cache.

## 19.11 Persistence

No Reporting persistence layer.

Reports are computed from logical sources.

---

# 20. Required Verification

Slice #5 must add or amend tests covering at minimum:

### Runtime lifecycle

* successful execution;
* source resolution;
* source read;
* execution-plan consumption.

### Filters

* equality;
* inequality;
* membership;
* relational comparisons;
* missing field behavior;
* invalid operands.

### Grouping

* single dimension;
* multiple dimensions;
* no dimensions;
* deterministic group formation.

### Aggregation

* COUNT;
* SUM;
* MIN;
* MAX;
* Decimal values;
* supported integer/numeric combinations;
* unsupported type combinations;
* empty input.

### Dataset

* schema consistency;
* row consistency;
* deterministic ordering;
* immutability;
* defensive copying / isolation where applicable.

### Error behavior

* invalid operation;
* invalid value;
* source failure;
* invalid execution conditions.

### Architectural boundary

Tests must ensure runtime execution does not require Standard-specific dependencies or domain mutation services.

---

# 21. Quality Gate

At completion of Slice #5:

```text
pytest -q
ruff check .
black --check .
mypy src
```

must pass.

The Slice #5 test suite must not reduce existing coverage or break existing Reporting tests.

The final Phase 9 quality gate will remain the authoritative gate for the eventual commit/push.

---

# 22. Documentation Impact

Slice #5 may require updates to:

```text
PHASE_9_REPORTING_ARCHITECTURE_DEFINITION_SCOPE.md
PHASE_9_REPORTING_CONCRETE_API_DESIGN.md
```

only where implementation reveals a necessary clarification or where an existing documented invariant is completed.

Documentation must describe the final architecture rather than merely the implementation mechanics.

No separate implementation guide is required unless the architecture review identifies a genuine need.

---

# 23. Architectural Invariants

The following invariants are authoritative for Slice #5.

### R1 — Read-only

Reporting runtime never mutates authoritative application state.

### R2 — Plan-driven

Runtime executes a compiled execution plan rather than independently interpreting a report definition.

### R3 — Source abstraction

Runtime reads through `ReportDataSource`; it does not access domain persistence directly.

### R4 — Determinism

Equivalent input state and execution plan produce deterministic output.

### R5 — Immutable result

Public report datasets are immutable.

### R6 — Numeric integrity

Accounting `Decimal` values remain `Decimal`.

### R7 — Explicit semantics

Unsupported operations and invalid values are rejected rather than silently coerced.

### R8 — Platform isolation

Generic Reporting runtime contains no Standard-specific domain knowledge.

### R9 — No mutation workflow coupling

Reporting execution cannot trigger posting, reversal, repost, rebuild, or other domain mutation workflows.

### R10 — Stable boundary

The runtime consumes the existing execution-plan model and produces the existing dataset model; Slice #5 does not redesign the entire Reporting architecture.

---

# 24. Slice #5 Completion Criteria

Slice #5 is complete when:

1. The runtime contract is fully aligned with the approved Reporting architecture.
2. All executable operations have explicit runtime semantics.
3. Filter, grouping, and aggregation behavior is deterministic.
4. Empty-input behavior is explicit.
5. Dataset materialization is immutable.
6. Reporting-specific execution errors are explicit.
7. Runtime remains strictly read-only.
8. Runtime remains Standard-independent.
9. Required edge cases are covered by tests.
10. Existing Phase 9 tests remain green.
11. `ruff`, `black`, and `mypy` pass.
12. Documentation reflects the final runtime semantics.
13. No intermediate Git commit is required unless an implementation risk makes a checkpoint necessary.

---

# 25. Architectural Review Questions

Before proceeding to Concrete API Design, the following points require explicit review:

### Q1

Is **Runtime completion/hardening** the correct architectural scope for Slice #5 given that the Slice #4 baseline already contains `runtime.py`?

### Q2

Should empty-input aggregate semantics be fixed now as part of Slice #5, or deferred to a later reporting semantics slice?

### Q3

Is the executable aggregation vocabulary definitively:

```text
COUNT
SUM
MIN
MAX
```

with `AVG` remaining outside scope?

### Q4

Is deterministic output ordering a runtime invariant only, or should it also become an explicit part of the public `ReportDataset` contract?

### Q5

Should source-level errors be wrapped into Reporting-specific exceptions, or should the data-source exception contract propagate unchanged through the runtime boundary?

### Q6

Does the current `ReportExecutionPlan` contain all information required by the runtime, or is any additional runtime-only information needed?

### Q7

Should Slice #5 introduce any explicit distinction between:

```text
empty result
```

and:

```text
no aggregate group
```

or is the current dataset model sufficient?

### Q8

Are there any additional runtime semantics that must be frozen before the first Standard-specific `ReportDataSource` is implemented?

---

# 26. Approval Gate

No implementation changes belonging specifically to Slice #5 should be treated as final until this Architecture Definition / Scope has been reviewed and approved.

After approval, the next artifact is:

```text
Phase 9 Slice #5
Concrete API Design
```

Only after that API Design is reviewed and approved should implementation proceed.
