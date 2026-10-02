# Phase 9 — Slice 7: End-to-End Inventory Balance Report

## Concrete API Design

**Status:** Approved and implemented  
**Architecture Definition:** `PHASE_9_Slice_7_Inventory_Balance_Report_Architecture_Definition_Scope.md`

---

## 1. Public API

Production code adds the following Standard Reporting symbols:

```python
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

The existing `standard.reporting` package exports both symbols.

---

## 2. Source Identity

The definition references the existing Standard-owned logical source:

```python
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
# ReportDataSourceIdentity("inventory.balance")
```

The report identity and source identity are intentionally distinct.

---

## 3. No New Generic API

Slice #7 does not add or modify any generic Reporting class, protocol, registry, runtime, compiler, plan operation, or dataset type.

Existing APIs are used unchanged:

```text
DefaultReportValidator
DefaultReportCompiler
DefaultReportExecutionPlanBuilder
DefaultReportRuntime
ReportDataSourceRegistry
```

---

## 4. No Production Execution Facade

No method such as:

```python
execute_inventory_balance_report()
```

is introduced.

Callers use the existing generic Reporting execution pipeline with the Standard report definition and a Standard-composed source registry.

---

## 5. Standard Composition

The existing Standard bootstrap provides the Reporting composition boundary:

```python
registry = bootstrap.compose_inventory_reporting(
    totals,
    cost_totals,
)
```

The registry contains the `InventoryBalanceReportSource` for `inventory.balance`.

`compose_inventory_balance_report_source()` remains a lower-level Standard composition helper; neither method belongs to generic Reporting.

---

## 6. Output Shape

The report output has the following fields in definition order:

| Field | Type | Role |
|---|---|---|
| `product` | STRING | dimension |
| `warehouse` | STRING | dimension |
| `quantity` | DECIMAL | `SUM` measure |
| `cost` | DECIMAL | `SUM` measure |

The resulting `ReportDataset` is immutable.

---

## 7. Filtered Execution

A filtered execution derives a new immutable definition rather than modifying the production definition:

```python
filtered = replace(
    INVENTORY_BALANCE_REPORT_DEFINITION,
    filters=(
        ReportFilter(
            "warehouse",
            ReportFilterOperator.EQUALS,
            ReportValue("W2"),
        ),
    ),
)
```

The generic runtime applies the filter semantics. Slice #7 does not add Standard-specific filter logic.

---

## 8. Test Contract

The vertical test suite verifies:

1. stable report metadata;
2. validation against the real composed source;
3. one-scope end-to-end execution;
4. deterministic multi-scope ordering;
5. generic filtering;
6. explicit zero valuation cost;
7. empty Inventory output;
8. semantic state immutability after execution.

The test fixture constructs semantic derived state using the existing Register Totals and Cost Totals engines rather than creating fake `ReportRow` values.

---

## 9. Implementation Boundary

Only Standard Reporting production code is added by Slice #7:

```text
src/standard/reporting/inventory_balance.py
```

and its public exports are updated in:

```text
src/standard/reporting/__init__.py
```

Tests are located under:

```text
tests/unit/standard/reporting/test_inventory_balance.py
```

No generic Reporting production source is changed by Slice #7.

---

## 10. Approval / Completion

The Concrete API Design is implemented as specified. The Slice #7 implementation has passed the project's full Python 3.14 quality gate:

- `pytest -q` — 1104 passed;
- `ruff check .` — PASS;
- `black --check .` — 262 files unchanged;
- `mypy src` — no issues, 143 source files.

Slice #7 is therefore closed and ready for Slice #8 documentation reconciliation.
