# PHASE 9 — Reporting Slice 6

# Standard Inventory Adapter

## Architecture Definition / Scope

**Status:** Approved and implemented

---

## 1. Purpose

Slice #6 introduces the Standard-specific read adapter that exposes Inventory state through the generic Platform Reporting logical data-source boundary.

The slice connects:

```text
Standard Inventory
      │
      ├── Register semantic balance state
      │
      └── Valuation semantic cost-balance state
              │
              ▼
   Inventory Reporting Adapter
              │
              ▼
   ReportDataSource boundary
```

The purpose of the slice is to make existing Inventory Register and Valuation state consumable by Reporting without introducing Reporting-specific business logic into the generic Platform layer.

Slice #6 does not implement the complete Inventory Balance report. That remains Slice #7.

---

# 2. Architectural Position

The dependency direction remains:

```text
accore.platform.reporting
        ▲
        │
        │ generic ReportDataSource contract
        │
standard.reporting / Standard adapter
        │
        ├── accore.platform.registers
        └── accore.platform.valuation
```

The generic Reporting package must remain unaware of:

* Inventory;
* Product;
* Warehouse;
* FIFO;
* Goods Receipt;
* Register posting;
* Valuation lifecycle;
* valuation recovery;
* Standard configuration.

All Standard-specific semantics remain under `src/standard`.

---

# 3. Existing Baseline Contracts

Slice #6 builds on existing semantic read capabilities.

## 3.1 Register

The existing Register layer provides:

```python
BalanceQueryService
BalanceQuery
BalanceResult
TotalsReader
TotalsKey
```

A balance is identified by:

```text
Register identity
+
TotalsKey
```

For Standard Inventory, the canonical dimensions are:

```text
product
warehouse
```

and the balance value is a Decimal quantity.

The Inventory Register configuration already establishes:

```text
register = INVENTORY_REGISTER_ID
dimensions = ("product", "warehouse")
resource = "quantity"
resource_type = Decimal
```

---

## 3.2 Valuation

The existing Valuation layer provides:

```python
CostTotalsReader
CostBalance
ValuationKey
```

`CostBalance` contains:

```text
valuation_key
quantity
cost
calculated_at
```

The Standard Inventory valuation key is already defined by:

```text
product
warehouse
```

through `InventoryValuationKeyMapper`.

For Inventory reporting, current cost must be consumed from `CostBalance`.

Reporting must not reconstruct current valuation cost by summing historical valuation facts or `CostMovement` records.

---

# 4. Standard Inventory Logical Source

Slice #6 introduces the Standard-owned logical source:

```python
InventoryBalanceReportSource
```

The source implements the generic:

```python
ReportDataSource
```

contract.

Its logical identity is:

```text
inventory.balance
```

using a dedicated:

```python
ReportDataSourceIdentity
```

The identity is a Reporting logical-source identity and is not a Register identity, Valuation identity, persistence identifier, or schema field.

---

# 5. Logical Schema

The Inventory Balance logical source exposes the following semantic fields:

| Field       | Reporting type | Meaning                                |
| ----------- | -------------- | -------------------------------------- |
| `product`   | STRING         | Standard Inventory product dimension   |
| `warehouse` | STRING         | Standard Inventory warehouse dimension |
| `quantity`  | DECIMAL        | Current Inventory Register balance     |
| `cost`      | DECIMAL        | Current Valuation `CostBalance.cost`   |

The source owns the mapping from Standard Inventory semantics to these generic Reporting fields.

Generic Reporting does not know where these fields originated.

---

# 6. Source Composition

The source conceptually performs:

```text
Inventory Register semantic balance
              +
Inventory Valuation semantic cost balance
              │
              ▼
       canonical Inventory key
              │
              ▼
        ReportRow
```

For one canonical Inventory scope:

```text
(product, warehouse)
```

the source obtains:

```text
quantity ← Register BalanceResult.value
cost     ← Valuation CostBalance.cost
```

The valuation `CostBalance.quantity` is not used as a substitute for the Register Inventory quantity.

The Register remains authoritative for Inventory quantity.

Valuation remains authoritative for valuation cost.

---

# 7. No Generic Reporting Join Engine

Slice #6 does not introduce:

* cross-source joins;
* generic join keys;
* generic join algorithms;
* generic source composition;
* multi-source execution plans.

`InventoryBalanceReportSource` is a Standard-owned composed source.

This preserves the API Design decision:

> Inventory Balance is one Standard-owned logical source.

The generic Reporting runtime continues to execute one logical source.

---

# 8. Register Read Boundary

The Standard adapter must consume Register state through a semantic read-oriented boundary.

The adapter must not:

* mutate Register state;
* apply or remove movements;
* rebuild Totals;
* invoke posting;
* access Register mutation orchestration;
* calculate Inventory balances independently from Movement facts.

The source must treat Register balance as an already established domain result.

---

# 9. Valuation Read Boundary

The Standard adapter must consume valuation state through a narrow read-only reporting-facing boundary.

Reporting must not depend directly on:

```python
ValuationResultPersistence
ValuationFactPersistence
ValuationOperationPersistence
DefaultValuationCoordinator
ValuationEngine
DefaultValuationRebuilder
```

The adapter must not:

* calculate FIFO;
* establish valuation;
* remove valuation;
* reverse valuation;
* repost valuation;
* rebuild valuation;
* mutate valuation facts;
* mutate derived valuation results;
* initiate recovery.

The current `CostBalance` result is the semantic valuation read model required by Inventory reporting.

---

# 10. Canonical Correlation Key

The Standard Inventory correlation key is:

```text
product + warehouse
```

The Register side represents this through `TotalsKey`.

The Valuation side represents it through `ValuationKey`.

The adapter is responsible for translating both into the same canonical Standard Inventory logical key.

The generic Reporting layer must never perform this translation.

---

# 11. Important Architecture Gap — Enumeration

The current platform contracts expose:

```python
BalanceQueryService.query(BalanceQuery)
```

and:

```python
TotalsReader.get(register_identity, totals_key)
```

Both provide lookup of one known balance key.

They do not provide a semantic operation equivalent to:

```text
enumerate all current Register balance keys
```

Likewise, `CostTotalsReader` provides:

```python
get(valuation_key)
```

but not enumeration.

The existing valuation persistence contains `enumerate_balances()`, but using that persistence directly from the Reporting adapter would violate the intended semantic ownership boundary.

Therefore Slice #6 must explicitly resolve how a Standard Inventory source obtains the set of logical Inventory scopes.

This is an architectural issue, not an implementation detail.

---

# 12. Required Enumeration Decision

Before Concrete API Design, Architecture Review must select one of the following strategies.

## Option A — Requested-scope source

The Inventory source requires sufficient equality filters to identify:

```text
product
warehouse
```

and performs semantic lookup for that one scope.

Unfiltered `inventory.balance` reads are supported by Slice #6; the source enumerates the current Register-derived Inventory scopes and the generic runtime applies report filters.

Advantages:

* no new generic Register API;
* no persistence access;
* minimal architectural change.

Limitation:

* the source cannot independently enumerate all Inventory balances;
* Slice #7 must explicitly define a report scope through filters.

---

## Option B — Standard-owned balance enumeration adapter

Introduce Standard-specific read adapters capable of exposing the current set of Inventory balance scopes while still hiding persistence internals.

Conceptually:

```python
InventoryBalanceReadAdapter
```

could provide a Standard-specific read view containing:

```text
product
warehouse
quantity
cost
```

The adapter may internally coordinate existing domain read state, but its public contract remains read-only and semantic.

Advantages:

* natural fit for a logical reporting source;
* source can produce the complete Inventory dataset;
* persistence details remain hidden.

Risk:

* existing Register semantic APIs currently do not provide the required enumeration capability;
* implementation would need a carefully defined source of authoritative balance keys.

---

## Option C — Extend generic Register/Valuation read contracts

Introduce explicit semantic enumeration APIs into the generic domains.

For example:

```text
Register balance scope enumeration
Cost balance scope enumeration
```

The Standard adapter would then use only those generic semantic contracts.

Advantages:

* semantically clean long-term model;
* reusable for future reporting and analytical consumers.

Risk:

* expands Slice #6 beyond a pure Standard adapter;
* changes already completed Register/Valuation contracts;
* requires additional architecture/API review outside the immediate Reporting slice.

This was a pre-approval review constraint. The choice has now been approved and implemented as recorded in the final decision above.

---

# 13. Final Architecture Review Decision

The Architecture Review resolved the enumeration question in favor of extending the existing semantic read contracts. `InventoryBalanceReportSource` performs an unfiltered read of current Register-derived Inventory scopes, correlates them with enumerated Valuation `CostBalance` state, ignores valuation-only scopes, and lets generic Reporting apply filters after source acquisition.

This section supersedes the earlier alternatives presented for review below.

# 14. Consistency Semantics

The Inventory logical source combines two independently owned semantic states:

```text
Register balance
+
Valuation cost balance
```

The source does not claim atomic transaction consistency across those states.

The source consistency is therefore:

```text
composed semantic read
```

rather than:

```text
atomic cross-domain snapshot
```

Reporting must not introduce a transaction coordinator between Register and Valuation.

---

# 15. Read Failure Semantics

If Register cannot provide a valid semantic balance read:

```text
source execution fails
```

If Valuation cannot provide a valid semantic cost balance:

```text
source execution fails
```

The adapter must never:

* interpret a read failure as zero;
* reconstruct missing valuation state;
* rebuild derived state;
* retry through mutation/recovery APIs;
* silently omit an affected logical scope.

A valid zero balance is distinct from an unavailable balance.

---

# 16. Missing Valuation State

The architecture must distinguish:

```text
known CostBalance with cost = Decimal(0)
```

from:

```text
no valid valuation read result
```

Slice #6 must not silently convert an unavailable valuation state into:

```text
cost = Decimal(0)
```

The exact missing-state behavior belongs in Concrete API Design after the enumeration strategy is approved.

---

# 17. Reporting Schema Responsibility

The Standard adapter owns:

```text
product → Reporting product field
warehouse → Reporting warehouse field
Register quantity → Reporting quantity field
Valuation cost → Reporting cost field
```

The generic Reporting package owns only:

```text
ReportSchema
ReportField
ReportRow
ReportValue
```

No Standard-specific field constants or domain objects may be added to `accore.platform.reporting`.

---

# 18. Source Request Handling

`InventoryBalanceReportSource` receives:

```python
ReportDataSourceRequest
```

The source may interpret compatible report filters needed to establish its semantic read scope.

It must not:

* implement generic Reporting filter semantics;
* duplicate the runtime filter engine;
* mutate the request;
* introduce Standard-specific filter operators.

The generic runtime remains responsible for final report filter application.

---

# 19. Immutability

Rows returned by the source must satisfy the existing immutable Reporting dataset contracts.

The source must not expose:

* mutable Register objects;
* mutable Valuation persistence objects;
* internal dictionaries;
* persistence collections.

All domain state is translated into `ReportRow` / `ReportValue`.

---

# 20. No Domain Mutation

The strongest Slice #6 invariant is:

```text
Reporting execution is observational only.
```

Executing an Inventory report must not alter:

* Register Movement facts;
* Register Totals;
* Valuation facts;
* Valuation operation records;
* CostMovements;
* CostBalances;
* recovery state;
* persistence state.

This invariant must be tested directly.

---

# 21. Standard Composition

The Standard adapter must be composable with the existing Standard configuration infrastructure.

It must not alter:

* Inventory Register posting composition;
* Valuation posting composition;
* valuation lifecycle composition;
* persistence semantics.

The adapter is a consumer of established domain state, not a new domain coordinator.

---

# 22. Proposed Module Boundary

The preferred location is Standard-owned reporting infrastructure:

```text
src/
└── standard/
    └── reporting/
        ├── __init__.py
        └── inventory.py
```

The exact module split may be refined during Concrete API Design.

The generic source contract remains:

```text
accore.platform.reporting.datasource.ReportDataSource
```

---

# 23. Testing Scope

Slice #6 must provide unit and integration coverage for:

### Source contract

* source identity;
* source schema;
* source consistency;
* successful read.

### Register integration

* correct Inventory register identity;
* correct Product/Warehouse correlation;
* correct Decimal quantity;
* semantic Register read only.

### Valuation integration

* correct ValuationKey mapping;
* correct CostBalance lookup;
* correct Decimal cost;
* no historical-fact reconstruction.

### Composition

* matching Register and Valuation scope produces one logical row;
* quantity comes from Register;
* cost comes from Valuation;
* mismatched/unavailable state fails explicitly according to the final API contract.

### Immutability

* source does not mutate Register state;
* source does not mutate Valuation state;
* source does not mutate persistence collections.

### Consistency

* source documents composed-read semantics;
* no atomic cross-domain consistency is claimed.

### Failure behavior

* Register read failure is propagated;
* Valuation read failure is propagated;
* unavailable state is not converted to zero.

---

# 24. Out of Scope

Slice #6 does not include:

* Inventory Balance report definition;
* report-specific filters beyond source-read requirements;
* end-to-end ReportRuntime vertical execution;
* presentation;
* export;
* CSV/JSON/HTML;
* dashboards;
* report persistence;
* scheduling;
* caching;
* generic joins;
* generic cross-source execution;
* FIFO calculation;
* valuation mutation;
* valuation recovery;
* Register mutation;
* Register rebuild;
* new accounting semantics.

These belong either to existing domain phases or to Slice #7 and later work.

---

# 25. Slice #7 Boundary

Slice #7 begins only after Slice #6 provides a stable `InventoryBalanceReportSource`.

Slice #7 will define and execute:

```text
Inventory Balance ReportDefinition
        │
        ▼
InventoryBalanceReportSource
        │
        ▼
ReportRuntime
        │
        ▼
ReportDataset
```

Slice #7 will also provide the vertical regression proving that reporting execution does not mutate Register or Valuation state.

---

# 26. Acceptance Criteria

Slice #6 Architecture Definition is considered complete when:

1. the Standard Inventory logical source boundary is approved;
2. the source schema is approved;
3. Register read semantics are approved;
4. Valuation read semantics are approved;
5. canonical Product/Warehouse correlation is approved;
6. cross-domain consistency semantics are approved;
7. source failure semantics are approved;
8. the balance-scope enumeration strategy is explicitly approved;
9. the Standard/generic Reporting dependency direction is preserved;
10. mutation/recovery ownership remains unchanged;
11. Slice #7 boundary is explicit.

---

# 27. Architecture Review Questions

The following questions require explicit review before Concrete API Design.

### AR-Q1 — Inventory source scope

Should `InventoryBalanceReportSource` support an unfiltered read returning all current Inventory balances, or should Slice #6 define a requested-scope source requiring Product/Warehouse equality filters?

### AR-Q2 — Balance enumeration

If an unfiltered read is required, where should the authoritative set of current Inventory balance keys come from without exposing persistence internals?

### AR-Q3 — Missing valuation state

Should a missing `CostBalance` for a known Inventory scope be:

* an execution failure;
* a valid zero-cost balance;
* or another explicitly defined semantic state?

### AR-Q4 — Register/Valuation mismatch

If Register contains a current Inventory balance for a scope for which Valuation has no corresponding current `CostBalance`, what is the authoritative reporting behavior?

### AR-Q5 — Zero balances

Register Totals currently removes keys when their total becomes zero. Should zero Inventory balances therefore disappear from the source, or should the source preserve zero-valued scopes from another authoritative key set?

### AR-Q6 — Read adapter placement

Should Standard expose one composed `InventoryBalanceReadAdapter`, or separate Register and Valuation reporting adapters composed by `InventoryBalanceReportSource`?

---

# 28. Architectural Invariants

The following invariants are binding for implementation:

```text
I-1
Reporting is read-only.

I-2
Register remains authoritative for Inventory quantity.

I-3
Valuation remains authoritative for Inventory cost.

I-4
Reporting never reconstructs FIFO or valuation state.

I-5
Reporting never accesses valuation persistence directly.

I-6
Reporting never accesses Register persistence directly.

I-7
Generic Reporting contains no Standard-specific knowledge.

I-8
Inventory Balance composition is Standard-owned.

I-9
No atomic Register + Valuation consistency is implied.

I-10
Read failure is never converted into an empty or zero state.

I-11
Historical valuation facts remain immutable.

I-12
Slice #6 does not implement the final Inventory Balance report.
```

---

# 29. Proposed Implementation Sequence After Approval

After Architecture Definition approval:

1. finalize Concrete API Design;
2. review and approve the API;
3. implement narrow semantic read adapters;
4. implement `InventoryBalanceReportSource`;
5. add source/adapter unit tests;
6. add Standard composition tests;
7. run targeted quality checks;
8. reconcile documentation;
9. proceed to Slice #7.

No implementation begins before Architecture and Concrete API approval.
