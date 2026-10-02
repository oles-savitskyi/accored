# Phase 9 — Slice 6: Standard Inventory Reporting Adapter

## Concrete API Design

**Status:** Approved and implemented
**Implementation status:** Completed
**Scope:** Standard-owned adapter from Inventory Register + Valuation semantic state to generic Reporting `ReportDataSource`.

---

## 1. Purpose

Slice #6 introduces the Standard-specific logical Reporting data source:

```text
InventoryBalanceReportSource
```

The source exposes the current Inventory balance as a normalized Reporting dataset:

| Field       | Reporting type | Authority                          |
| ----------- | -------------- | ---------------------------------- |
| `product`   | `STRING`       | Inventory Register aggregation key |
| `warehouse` | `STRING`       | Inventory Register aggregation key |
| `quantity`  | `DECIMAL`      | Inventory Register current total   |
| `cost`      | `DECIMAL`      | Valuation current cost balance     |

The adapter composes two existing semantic read models:

```text
InventoryBalanceReportSource
        │
        ├── Inventory Register TotalsReader
        │      └── current quantity by (product, warehouse)
        │
        └── Valuation CostTotalsReader
               └── current cost by (product, warehouse)
```

Generic Reporting remains unaware of Inventory, Register, Valuation, FIFO, posting, valuation facts, or persistence.

---

# 2. Architectural Boundary

## 2.1 Generic Reporting owns

Generic Reporting continues to own:

* `ReportDataSource`
* `ReportDataSourceIdentity`
* `ReportDataSourceRequest`
* `ReportReadConsistency`
* `ReportSchema`
* `ReportRow`
* `ReportValue`
* runtime filtering
* grouping
* aggregation
* report definition and execution plan

No Inventory-specific concepts are introduced into `accore.platform.reporting`.

## 2.2 Standard owns

The following are Standard-specific:

* `InventoryBalanceReportSource`
* Inventory schema definition
* mapping from `TotalsKey` to Reporting fields
* mapping from `ValuationKey` to Reporting fields
* Register/Valuation correlation
* handling of missing valuation state for an Inventory scope
* composition of the two semantic readers
* Standard-specific source errors

The implementation belongs under:

```text
src/standard/reporting/
```

Recommended module:

```text
src/standard/reporting/inventory.py
```

with package exports through:

```text
src/standard/reporting/__init__.py
```

---

# 3. Source Identity

The source has one stable logical identity:

```python
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY = ReportDataSourceIdentity(
    "inventory.balance"
)
```

The identity is part of the Standard Reporting contract and must remain stable once published.

The source must not use persistence names, class names, or implementation-specific identifiers as its logical Reporting identity.

---

# 4. Source Schema

The source schema is fixed:

```python
INVENTORY_BALANCE_REPORT_SCHEMA = ReportSchema(
    fields=(
        ReportField("product", ReportDataType.STRING),
        ReportField("warehouse", ReportDataType.STRING),
        ReportField("quantity", ReportDataType.DECIMAL),
        ReportField("cost", ReportDataType.DECIMAL),
    )
)
```

Field order is significant for deterministic schema identity and must be:

```text
product
warehouse
quantity
cost
```

No additional fields are introduced in Slice #6.

In particular, the source does not expose:

* valuation quantity;
* valuation timestamp;
* calculated-at timestamp;
* valuation method;
* movement identity;
* document identity;
* Register identity;
* ValuationKey;
* internal persistence identifiers.

Those are domain/internal concerns rather than Inventory Balance report fields.

---

# 5. Semantic Read Contracts

The source must read **current derived semantic state**, not reconstruct balances from historical facts.

This requires extending the existing generic semantic readers with enumeration.

## 5.1 Register TotalsReader

`TotalsReader` is extended with:

```python
class TotalsReader(Protocol):
    def get(
        self,
        register_identity: Identifier,
        key: TotalsKey,
    ) -> TotalValue:
        """Return the current total for one Register aggregation key."""

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[tuple[TotalsKey, TotalValue], ...]:
        """Return all currently materialized non-zero totals for one Register."""
```

The return value represents the current materialized Totals state.

It does **not** represent historical Movement facts.

### Semantics

For the Inventory Register:

```python
totals.enumerate(INVENTORY_REGISTER_ID)
```

returns all currently materialized Inventory scopes.

Because `DefaultTotalsEngine` removes zero totals, zero balances are absent from the enumeration.

This is intentional.

A zero balance must not be reconstructed as an implicit reporting row.

---

# 6. Valuation Cost Read Contract

`CostTotalsReader` is extended with:

```python
class CostTotalsReader(Protocol):
    def get(self, valuation_key: ValuationKey) -> CostBalance:
        """Return the current cost balance for one valuation key."""

    def enumerate(self) -> tuple[CostBalance, ...]:
        """Return all currently materialized valuation balances."""
```

The enumeration represents the current derived valuation state.

It does not expose:

* valuation facts;
* valuation layers;
* FIFO internals;
* operation records;
* recovery state;
* persistence records.

The source therefore remains independent of valuation persistence.

---

# 7. Enumeration Semantics

Both semantic readers return immutable snapshots represented as tuples.

The implementation must not expose mutable internal dictionaries.

For `DefaultTotalsEngine`:

```python
def enumerate(
    self,
    register_identity: Identifier,
) -> tuple[tuple[TotalsKey, TotalValue], ...]:
```

must:

1. validate the Register identity using the same definition boundary as `get`;
2. read the current in-memory totals;
3. return only materialized entries;
4. exclude zero totals;
5. return a tuple;
6. avoid exposing the internal dictionary.

For `DefaultCostTotalsEngine`:

```python
def enumerate(self) -> tuple[CostBalance, ...]:
```

must:

1. return currently materialized balances;
2. return a tuple;
3. avoid exposing `_balances`;
4. preserve each `CostBalance` as immutable state.

No persistence access is required for either enumeration operation.

---

# 8. Inventory/Valuation Correlation

The canonical correlation key is:

```text
(product, warehouse)
```

The Inventory Register already defines these dimensions:

```text
product
warehouse
```

The Standard Valuation key mapper uses the same two semantic dimensions:

```text
product
warehouse
```

Therefore the adapter converts both domain representations into the same internal correlation representation:

```python
type InventoryBalanceScope = tuple[str, str]
```

where:

```text
scope[0] = product
scope[1] = warehouse
```

The implementation may use a private helper/dataclass if that improves readability, but this helper is not part of the public Reporting API.

---

# 9. Register as Authoritative Inventory Scope

The Inventory Register is authoritative for determining which Inventory scopes exist in the report.

Algorithm:

```text
Register enumeration
        │
        ▼
Inventory scopes
        │
        ├── lookup matching Valuation balance
        │
        ├── found → produce row
        │
        └── missing → source failure
```

Valuation-only scopes do not create Inventory rows.

In other words:

```text
Register scopes = report scope
Valuation scopes = supporting cost state
```

This prevents an orphaned valuation balance from becoming an Inventory item that does not exist in the Inventory Register.

---

# 10. Missing Valuation Balance

If the Register contains:

```text
(product=A, warehouse=W)
```

but Valuation enumeration contains no corresponding:

```text
(product=A, warehouse=W)
```

the source must fail.

It must **not** produce:

```text
cost = Decimal(0)
```

The distinction is intentional:

```text
missing materialized valuation state
        !=
materialized zero valuation state
```

`DefaultCostTotalsEngine.get()` currently returns a synthetic zero balance for an arbitrary requested key. The Inventory source must not use that behavior to infer existence.

Instead, existence is determined from `enumerate()`.

Only an explicitly materialized `CostBalance` can contribute a cost value.

---

# 11. Valuation-Only Scopes

If Valuation contains:

```text
(product=A, warehouse=W)
```

but the Inventory Register does not contain that scope, the valuation entry is ignored by the Inventory Balance source.

It must not create a Reporting row.

The Inventory Register remains the authoritative scope boundary.

This does not imply that orphaned valuation state is semantically desirable; it only defines the reporting adapter's responsibility.

Detection or remediation of unrelated valuation consistency problems belongs to the Valuation/maintenance domain, not Reporting.

---

# 12. Zero Balances

The source reports currently materialized non-zero Inventory balances.

If Register Totals contains no entry because its value was reduced to zero, no row is produced.

Likewise, the adapter does not synthesize rows for arbitrary zero-valued scopes.

Therefore:

```text
zero Register total
→ absent Inventory scope
→ absent report row
```

This preserves the existing Totals Engine semantics.

---

# 13. Source Consistency

The source implements:

```python
def consistency(self) -> ReportReadConsistency:
    return ReportReadConsistency.SOURCE_LOCAL
```

`SOURCE_LOCAL` must not be interpreted as an atomic transaction spanning Register and Valuation.

The source performs a semantic read composed from two domain read boundaries.

There is no new cross-domain transaction protocol in Slice #6.

Consequently the source guarantees:

* no mutation;
* deterministic transformation;
* domain-reader semantics;
* propagation of read failures.

It does not guarantee an atomic snapshot across Register and Valuation.

---

# 14. Source Read Contract

The concrete class has:

```python
class InventoryBalanceReportSource:
    identity: ReportDataSourceIdentity

    def __init__(
        self,
        totals: TotalsReader,
        cost_totals: CostTotalsReader,
    ) -> None:
        ...

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

Constructor dependencies are semantic readers only.

The constructor must not accept:

* `RegisterFactPersistence`;
* `ValuationFactPersistence`;
* `ValuationResultPersistence`;
* `ValuationOperationPersistence`;
* `MovementQueryService`;
* `DefaultValuationCoordinator`;
* FIFO engine;
* posting coordinator.

This keeps the adapter above domain semantic read boundaries and below persistence/lifecycle internals.

---

# 15. Request Handling

Slice #6 does not introduce filter pushdown.

`InventoryBalanceReportSource.read()` receives:

```python
ReportDataSourceRequest
```

because that is the generic `ReportDataSource` contract.

However, the Standard adapter reads the complete current Inventory state and does not implement Reporting filter semantics itself.

The effective flow is:

```text
ReportRuntime
    │
    ├── source.read(request)
    │       └── complete current Inventory source state
    │
    └── Reporting filter evaluation
            └── final filtered rows
```

This prevents duplication of generic Reporting filter semantics inside Standard.

The source must therefore return the same logical source state regardless of `request.filters` in Slice #6.

Future source-level optimization may be introduced separately without changing the logical source contract.

---

# 16. Row Construction

For every Register scope:

```python
TotalsKey
```

must contain:

```text
product
warehouse
```

The source constructs:

```python
ReportRow(
    {
        "product": ReportValue(product),
        "warehouse": ReportValue(warehouse),
        "quantity": ReportValue(quantity),
        "cost": ReportValue(cost),
    }
)
```

All values are concrete, non-null values for a valid Inventory row.

No `NULL` values are produced by this source in Slice #6.

---

# 17. Domain-to-Reporting Mapping

## Register

From:

```python
TotalsKey
```

extract:

```text
product
warehouse
```

From:

```python
TotalValue
```

extract:

```text
quantity
```

The Inventory Totals definition already guarantees Decimal resource semantics.

## Valuation

From:

```python
CostBalance
```

extract:

```text
valuation_key["product"]
valuation_key["warehouse"]
cost
```

The `cost` field is already a Decimal.

No conversion through strings or floats is permitted.

---

# 18. Error Contract

A Standard-specific source error is introduced:

```python
class InventoryBalanceReportSourceError(ReportDataSourceError):
    """Raised when Inventory Balance cannot be composed from domain state."""
```

It is used for source-level composition failures such as:

* Register scope missing required Inventory dimensions;
* Valuation scope missing for a Register scope;
* incompatible Register/Valuation correlation state;
* invalid semantic state exposed by the domain readers.

Domain errors raised by the underlying readers must not be silently converted into empty results.

The source may wrap a domain error only when additional Standard-specific context is required and must preserve the original exception as its cause.

---

# 19. Failure Semantics

The following behavior is mandatory:

| Condition                                                     | Result                              |
| ------------------------------------------------------------- | ----------------------------------- |
| Register enumeration succeeds, valuation enumeration succeeds | produce rows                        |
| Register has no scopes                                        | empty tuple                         |
| Register scope has valuation balance                          | produce row                         |
| Register scope has no valuation balance                       | `InventoryBalanceReportSourceError` |
| Valuation has additional scope absent from Register           | ignore                              |
| Register reader fails                                         | propagate/wrap failure              |
| Valuation reader fails                                        | propagate/wrap failure              |
| Invalid Register key                                          | source error                        |
| Invalid Valuation key                                         | source error                        |
| Persistence failure underneath a semantic reader              | never convert to empty result       |
| Zero Register total                                           | no row                              |
| Zero materialized Valuation cost                              | valid row if balance exists         |

The adapter must never use:

```python
except Exception:
    return ()
```

or equivalent fallback behavior.

---

# 20. Deterministic Row Ordering

The source must return rows deterministically.

Ordering is:

```text
product ASC
warehouse ASC
```

using the canonical textual values of the Inventory dimensions.

This guarantees stable source output independently of dictionary iteration order.

Reporting runtime may subsequently group and sort according to report dimensions, but the source itself remains deterministic.

---

# 21. No Historical Reconstruction

The source must not implement:

```text
MovementQuery
    → reconstruct quantity
```

nor:

```text
ValuationFactPersistence
    → reconstruct cost
```

The reasons are architectural:

1. Register Totals already define current quantity semantics.
2. Valuation Cost Totals already define current cost semantics.
3. Reconstructing quantity duplicates Register accounting semantics.
4. Reconstructing cost duplicates Valuation projection semantics.
5. Historical facts are not the Reporting source of truth for current derived balances.
6. Recovery/rebuild semantics remain owned by their respective domains.

---

# 22. Standard Composition

The Standard bootstrap/composition layer becomes responsible for constructing:

```python
InventoryBalanceReportSource(
    totals=inventory_register_totals_engine,
    cost_totals=inventory_valuation_totals_engine,
)
```

The source should be registered in the generic:

```python
ReportDataSourceRegistry
```

by the Standard composition layer.

The Reporting package itself must not instantiate Standard sources.

Conceptually:

```text
StandardConfigurationBootstrap
        │
        ├── Inventory Register TotalsEngine
        │
        ├── Valuation CostTotalsEngine
        │
        └── InventoryBalanceReportSource
                    │
                    ▼
          ReportDataSourceRegistry
```

The exact bootstrap method modification is part of Slice #6 implementation.

---

# 23. Public Exports

Standard Reporting exports:

```python
InventoryBalanceReportSource
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
INVENTORY_BALANCE_REPORT_SCHEMA
InventoryBalanceReportSourceError
```

No generic Reporting exports are added for Inventory concepts.

The generic platform exports only the reader enumeration additions:

```python
TotalsReader
CostTotalsReader
```

Their existing public identities remain unchanged.

---

# 24. Proposed File Structure

```text
src/
├── accore/
│   └── platform/
│       ├── registers/
│       │   └── totals.py
│       │       └── TotalsReader.enumerate(...)
│       │
│       └── valuation/
│           └── totals.py
│               └── CostTotalsReader.enumerate()
│
└── standard/
    └── reporting/
        ├── __init__.py
        └── inventory.py
```

Tests:

```text
tests/
├── unit/
│   ├── registers/
│   │   └── test_totals.py
│   ├── valuation/
│   │   └── test_totals.py
│   └── reporting/
│       └── ...
│
└── unit/
    └── standard/
        └── reporting/
            └── test_inventory.py
```

If the repository's existing test organization establishes a different Standard-specific convention, the implementation should follow that existing convention rather than introducing a second layout.

---

# 25. Required Tests

## 25.1 Register Totals enumeration

Test:

1. empty Register → empty tuple;
2. one non-zero total → one entry;
3. multiple totals → all entries;
4. zero total removed from enumeration;
5. unknown Register → existing Totals error;
6. returned collection is immutable;
7. internal state cannot be mutated through enumeration result.

## 25.2 Valuation Cost Totals enumeration

Test:

1. empty valuation state → empty tuple;
2. one balance → one balance;
3. multiple balances → all balances;
4. returned collection is immutable;
5. internal state cannot be mutated through enumeration result.

## 25.3 InventoryBalanceReportSource

Required scenarios:

### Empty state

```text
Register = {}
Valuation = {}
→ ()
```

### One valid scope

```text
Register:
(product=A, warehouse=W) → 10

Valuation:
(product=A, warehouse=W) → cost 125.00

→
A | W | 10 | 125.00
```

### Multiple scopes

Verify deterministic `(product, warehouse)` ordering.

### Missing valuation

```text
Register:
(A, W) → 10

Valuation:
{}

→ InventoryBalanceReportSourceError
```

### Valuation-only scope

```text
Register:
{}

Valuation:
(A, W) → 125

→ ()
```

### Zero Register balance

No Register entry exists after Totals removes the zero value.

Verify no report row is generated.

### Explicit zero valuation balance

If a `CostBalance` exists with:

```text
cost = Decimal(0)
```

for a known Register scope, verify the row is produced with zero cost.

This test establishes the distinction between:

```text
missing balance
```

and:

```text
existing zero balance
```

### Request filters

Pass a non-empty `ReportDataSourceRequest(filters=...)`.

Verify the source still exposes the complete logical source state and leaves filter evaluation to the Reporting runtime.

### Reader failure

Verify Register and Valuation reader failures do not become empty datasets.

### No mutation

After `read()` verify:

* Register totals unchanged;
* Valuation balances unchanged;
* no persistence methods invoked;
* no posting/lifecycle methods invoked.

---

# 26. Architectural Regression Tests

The implementation must prove that the Standard adapter does not depend on:

```text
RegisterFactPersistence
ValuationFactPersistence
ValuationResultPersistence
ValuationOperationPersistence
MovementQueryService
DefaultValuationCoordinator
ValuationEngine
FIFOValuationMethod
Posting coordinators
```

The preferred mechanism is constructor-level dependency tests rather than brittle source-text inspection.

The source should be constructible using only:

```python
TotalsReader
CostTotalsReader
```

test doubles.

---

# 27. Explicit Non-Goals

Slice #6 does not implement:

* Inventory Balance report definition;
* Report filters specific to Inventory;
* grouping/aggregation;
* Inventory Balance end-to-end execution;
* joins;
* generic join framework;
* historical Inventory reports;
* historical valuation reports;
* valuation layer reporting;
* FIFO reporting;
* movement-level reporting;
* report persistence;
* caching;
* pagination;
* export;
* presentation;
* dashboard integration;
* atomic Register/Valuation snapshots;
* consistency repair;
* recovery;
* reconciliation workflows.

Those remain outside this slice.

---

# 28. Slice #7 Boundary

Slice #6 ends when the Standard source is available as a valid generic:

```python
ReportDataSource
```

and can expose:

```text
product
warehouse
quantity
cost
```

from the two semantic domain readers.

Slice #7 will consume this source and introduce the actual vertical Inventory Balance report:

```text
ReportDefinition
    ↓
InventoryBalanceReportSource
    ↓
Reporting compilation
    ↓
Reporting runtime
    ↓
ReportDataset
```

Slice #7, rather than Slice #6, owns the end-to-end report definition and regression proving the complete vertical.

---

# 29. Final API Summary

The resulting API surface is intentionally small.

### Generic Register

```python
class TotalsReader(Protocol):
    def get(
        self,
        register_identity: Identifier,
        key: TotalsKey,
    ) -> Decimal:
        ...

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[tuple[TotalsKey, Decimal], ...]:
        ...
```

### Generic Valuation

```python
class CostTotalsReader(Protocol):
    def get(self, valuation_key: ValuationKey) -> CostBalance:
        ...

    def enumerate(self) -> tuple[CostBalance, ...]:
        ...
```

### Standard Reporting

```python
INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY = ReportDataSourceIdentity(
    "inventory.balance"
)

INVENTORY_BALANCE_REPORT_SCHEMA = ReportSchema(
    fields=(
        ReportField("product", ReportDataType.STRING),
        ReportField("warehouse", ReportDataType.STRING),
        ReportField("quantity", ReportDataType.DECIMAL),
        ReportField("cost", ReportDataType.DECIMAL),
    )
)


class InventoryBalanceReportSource:
    identity: ReportDataSourceIdentity

    def __init__(
        self,
        totals: TotalsReader,
        cost_totals: CostTotalsReader,
    ) -> None:
        ...

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

### Standard error

```python
class InventoryBalanceReportSourceError(ReportDataSourceError):
    ...
```

---

# 30. Approval Criteria

Slice #6 Concrete API Design is considered implementation-ready when the following are accepted:

1. Register `TotalsReader` gains semantic enumeration.
2. Valuation `CostTotalsReader` gains semantic enumeration.
3. Enumeration represents current derived state, not historical facts.
4. Inventory Register is authoritative for report scope.
5. Missing valuation for a known Inventory scope is an error, not zero.
6. Valuation-only scopes do not create Inventory rows.
7. Zero Register totals do not create rows.
8. Explicitly materialized zero valuation balances remain valid.
9. The Standard source depends only on semantic readers.
10. Generic Reporting receives no Inventory-specific concepts.
11. Filters remain owned by the generic Reporting runtime.
12. No cross-domain atomicity is claimed.
13. Slice #7 remains responsible for the actual Inventory Balance report vertical.
14. No persistence, posting, valuation lifecycle, FIFO, or recovery logic enters the adapter.
15. The implementation remains read-only and deterministic.
