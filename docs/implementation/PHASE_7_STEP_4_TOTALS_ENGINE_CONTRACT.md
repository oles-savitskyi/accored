# PHASE 7 — STEP 4 — TOTALS ENGINE CONTRACT

## 1. Document Status

**Phase:** 7 — Register Architecture
**Step:** 4 — Totals Engine Contract
**Status:** Final

This document defines the semantic and architectural contract of the Totals Engine for the Register Architecture.

The document establishes responsibilities, invariants, consistency semantics, and architectural boundaries of the Totals Engine.

This document does **not** define a concrete implementation, storage structure, SQL schema, indexes, ORM, filesystem layout, or final Python API.

---

# 2. Step 4 Objective

The objective of Step 4 is to define the Totals mechanism that maintains Register aggregate derived state based on authoritative Register Movement facts.

The Totals Engine must provide:

* application of a Movement's accounting effect;
* removal of a Movement's accounting effect;
* deterministic totals calculation;
* totals rebuild from persisted Movement facts;
* consistency validation between incremental totals and rebuild;
* operation according to Register-defined aggregation semantics;
* independence from a concrete Storage Provider;
* separation of Totals semantics from Balance Query semantics.

After Step 4, the Register Architecture must unambiguously define:

* what a Total is;
* how a Movement affects a Total;
* how an aggregation key is defined;
* how derived state is maintained;
* how derived state is reconstructed from authoritative facts.

---

# 3. Architectural Position of Totals

Totals are **derived state**.

The authoritative accounting fact remains `Movement`.

```text
Movement
   │
   ├── authoritative accounting fact
   │
   ▼
Totals Engine
   │
   └── derived aggregate state
```

Totals do not replace Movements and are not an independent source of accounting truth.

If persisted Totals and persisted Movement facts diverge:

> Movement facts are the authoritative source for rebuilding Totals.

---

# 4. Source of Truth

The only authoritative source for rebuilding Totals is persisted Register Movement facts.

The Totals Engine must not rebuild totals from:

* previously persisted Totals;
* Balance Query;
* Document state;
* Posting Context;
* runtime objects;
* cached aggregates;
* provider-specific derived state;
* external reporting structures.

Rebuild has the following semantics:

```text
Persisted Movement Facts
        │
        ▼
Totals Engine
        │
        ▼
Rebuilt Totals
```

and not:

```text
Old Totals
    │
    ▼
Totals Engine
    │
    ▼
New Totals
```

---

# 5. Register Scope

Each Totals Engine operates within the scope of a specific Register.

Totals are not a global aggregate across the system.

Each totals state belongs unambiguously to one Register:

```text
Register Identity
```

A Movement may participate only in totals belonging to its Register:

```python
movement.register_identity
```

The Totals Engine must not silently aggregate Movements from different Registers.

---

# 6. Movement as an Input Accounting Fact

The Totals Engine receives `Movement` as a semantic accounting fact.

It must not depend on:

* persistence row identity;
* storage provider;
* database primary key;
* insertion order;
* runtime object identity;
* a particular storage layout.

Totals semantics use the data contained in `Movement`:

* `register_identity`;
* `movement_type`;
* `dimensions`;
* `resources`;
* `accounting_time`;
* other fields when Register configuration defines their participation in aggregation.

---

# 7. Register-Defined Aggregation Semantics

The Totals Engine is a generic platform mechanism, while aggregation semantics are defined by Register configuration/metadata.

The Totals Engine must not globally assume that every Register has:

```text
Product
Warehouse
Quantity
```

These are semantics of a particular Register.

For the Inventory Register, Phase 7 aggregation semantics define:

```text
dimensions:
    Product
    Warehouse

resource:
    Quantity
```

Therefore, an Inventory total conceptually represents:

```text
Register scope
    +
AggregationKey(Product, Warehouse)
    →
Quantity Total
```

The concrete representation of this key is an implementation concern.

---

# 8. Totals Key

`TotalsKey` is an immutable semantic aggregation key defined by Register configuration.

For Inventory:

```text
AggregationKey:
    Product
    Warehouse
```

Register identity is the Totals Engine scope, rather than necessarily being a business component of every individual aggregation key.

Therefore, two different Movements may affect the same Total.

For example:

```text
Movement A:
    Product = P1
    Warehouse = W1
    Quantity = 10

Movement B:
    Product = P1
    Warehouse = W1
    Quantity = 5
```

Both Movements belong to the same:

```text
AggregationKey(P1, W1)
```

and produce:

```text
Total = 15
```

`Movement.identity` is not part of `TotalsKey`.

---

# 9. Resource Aggregation

The Totals Engine must explicitly know which Movement resources are aggregated according to Register configuration.

For Inventory:

```text
resource = Quantity
```

Quantity is aggregated arithmetically:

```text
Total Quantity =
    Σ signed contribution
```

For Inventory:

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

The Totals Engine must not interpret arbitrary resource fields as totals without Register-defined aggregation semantics.

---

# 10. Movement Contribution

Every Movement participating in aggregation has an unambiguous contribution.

For Inventory:

```text
INCOME:
    contribution = +Quantity

EXPENSE:
    contribution = -Quantity
```

Contribution is defined by:

```text
Movement
+
Register aggregation semantics
    →
Total contribution
```

Contribution does not depend on:

* current system time;
* storage provider;
* persistence layout;
* insertion order;
* runtime identity;
* external mutable state.

---

# 11. Accounting Time

`Movement.accounting_time` is an optional property of the universal `Movement`.

The presence of `accounting_time=None` does not make a Movement invalid by itself.

Totals semantics distinguish two cases.

### 11.1 All-Time Register Totals

For an aggregate that is not period-dependent, `accounting_time` is not inherently required.

If Register aggregation semantics permit all-time accumulation, a Movement with:

```python
accounting_time is None
```

may participate in that aggregate.

### 11.2 Period-Scoped Aggregation

For period-scoped aggregation, `accounting_time` is required because without it the Movement cannot be assigned to a period.

A Movement with:

```python
accounting_time is None
```

cannot participate in a period-scoped aggregate.

Therefore:

> `accounting_time=None` is a valid Movement state, but it is incompatible with aggregation semantics that require temporal membership.

---

# 12. Period Semantics

When a Totals operation uses a period, it uses the same semantics as Movement Query:

```text
[start, end)
```

A Movement belongs to the period if and only if:

```text
accounting_time is not None
and
start <= accounting_time < end
```

The period must satisfy:

```text
start < end
```

Period boundaries must be timezone-aware.

Therefore:

* `start == end` — invalid period;
* `start > end` — invalid period;
* naive datetime — invalid period.

The Totals Engine must not introduce period semantics that differ from Movement Query.

---

# 13. Period-Bucketed Totals Out of Scope

The Phase 7 Totals Engine does **not** maintain separate totals buckets for arbitrary periods.

The primary derived state has the form:

```text
Register scope
+
AggregationKey
→
Total
```

The Totals Engine does not introduce a separate persistent model of:

```text
AggregationKey + Period → Stored Total
```

as an independent state structure.

If Balance Query or another Register operation requires a period-scoped aggregate, that value may be obtained from authoritative Movement facts through the appropriate semantic selection/aggregation path.

This prevents the introduction of a second complex period-bucketed persistence model in Phase 7.

---

# 14. Apply Movement

The Totals Engine must support the semantic operation:

```text
apply(Movement)
```

It means:

> Include the accounting effect of the specified Movement in the derived totals state.

Apply does not modify the `Movement` itself.

The Movement remains an immutable semantic fact.

For the relevant aggregation key, after successful application:

```text
Totals(after)
    =
Totals(before)
+
contribution(Movement)
```

---

# 15. Remove Movement Effect

The Totals Engine must support the semantic operation:

```text
remove(Movement)
```

It means:

> Exclude the accounting contribution of the specified Movement from the derived totals state.

This does not mean modifying or deleting the Movement object.

The Movement remains immutable.

For the relevant aggregation key, after successful removal:

```text
Totals(after)
    =
Totals(before)
-
contribution(Movement)
```

---

# 16. Responsibility for Single Application

The Totals Engine is not the owner of the complete Movement lifecycle.

In particular, the Totals Engine is not required to independently detect whether a particular Movement has already been applied, unless this is explicitly provided by its concrete implementation contract.

The guarantee that one accounting effect is not submitted for application more than once belongs to higher-level consistency/lifecycle orchestration.

The architectural model is:

```text
Posting / Unposting / Reposting
        │
        ├── determines additions
        ├── determines removals
        │
        ▼
Totals Maintenance
```

and not:

```text
Totals Engine
    └── independently manages Movement lifecycle
```

At the system level, however, the same accounting effect must not be silently applied more than once.

The concrete mechanism for detecting repeated application or maintaining such state is an implementation concern of the higher-level consistency/lifecycle layer.

---

# 17. Movement Identity and Totals State

`Movement.identity` is not part of the business `TotalsKey`.

It may be used by consistency/lifecycle infrastructure to identify accounting effects, but this does not make Movement identity a component of the business total.

Thus:

```text
Movement.identity
    = identity of accounting fact

TotalsKey
    = identity of aggregate
```

These concepts must remain separate.

---

# 18. Incremental Totals

The primary operational path in Phase 7 is:

```text
New Movement
    │
    ▼
Movement Validation
    │
    ▼
Calculate Contribution
    │
    ▼
Update Totals
```

After successful Movement application:

```text
T' = T + contribution(M)
```

Incremental maintenance avoids recalculating the entire Register after every Movement.

---

# 19. Removal and Incremental Maintenance

When an accounting effect is removed:

```text
T' = T - contribution(M)
```

Removal does not require modifying the Movement.

For Reposting, higher-level orchestration may use:

```text
remove(old Movement effects)
+
apply(new Movement effects)
```

The exact operation boundary is defined by the overall Register consistency architecture.

---

# 20. Rebuild

The Totals Engine must support rebuild.

Rebuild means:

> Construct a new derived totals state exclusively from authoritative persisted Movement facts.

Conceptually:

```text
Persisted Register Movements
            │
            ▼
    select applicable facts
            │
            ▼
   calculate contributions
            │
            ▼
      aggregate totals
            │
            ▼
       rebuilt totals
```

Rebuild does not use the previous totals state as an accounting input.

---

# 21. Rebuild Scope

Phase 7 defines one rebuild scope:

```text
Register
```

Therefore, rebuild reconstructs the totals of the selected Register:

```text
rebuild(register_identity)
```

A period-scoped rebuild is not part of Phase 7.

If partial or period-scoped rebuild is required in the future, it will be a separate architectural extension.

---

# 22. Rebuild Determinism

Given the same persisted Movement facts and the same Register aggregation configuration, rebuild must produce the same semantic totals state.

The result must not depend on:

* insertion order;
* storage provider;
* storage layout;
* runtime identity;
* arbitrary iteration order;
* current system time;
* external mutable state.

When the aggregation operation is commutative/associative, processing order must not change the semantic result.

---

# 23. Incremental vs Rebuild Consistency

For the same authoritative Movement set:

```text
incremental totals
    ==
rebuild totals
```

at the semantic level.

Conceptually:

```text
Persisted Movements
        │
        ├── incremental maintenance ──► Totals A
        │
        └── rebuild ───────────────────► Totals B

Totals A == Totals B
```

This is one of the key consistency invariants of Phase 7.

---

# 24. Zero Totals

If accounting effects for an aggregation key fully offset each other:

```text
INCOME 10
EXPENSE 10
```

the semantic total is:

```text
0
```

Whether a zero-total record physically exists is an implementation detail.

The architecture does not require physical removal of zero totals.

A semantic result of `0` must not be interpreted as the absence of accounting facts.

---

# 25. Negative Totals

The Totals Engine must not independently prohibit negative aggregate values.

For example:

```text
INCOME 5
EXPENSE 8
```

produces:

```text
Total = -3
```

Whether a negative Inventory balance is permitted or prohibited is a separate business validation policy.

The Totals Engine represents the aggregation result and does not replace the business validation layer.

---

# 26. Inventory Quantity Semantics

For the Inventory Register:

```text
Quantity : Decimal
Quantity > 0
```

Quantity represents the **magnitude of the movement**, not a signed delta.

The sign of the accounting effect is determined exclusively by `MovementType`.

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

For example:

```text
INCOME  Quantity=10 → +10
EXPENSE Quantity=10 → -10
```

Therefore:

```text
INCOME  Quantity=-10
EXPENSE Quantity=-10
```

are not valid Inventory Movement contributions.

Inventory-specific validation must reject `Quantity <= 0`.

This prevents double encoding of the sign.

---

# 27. Missing Resource

If Register aggregation semantics require a resource:

```text
Quantity
```

and the Movement does not contain that resource, the Movement cannot be correctly aggregated.

This is a semantic validation failure.

The Totals Engine must not:

* treat a missing resource as zero;
* silently skip the Movement;
* substitute a default value;
* convert a missing resource into a NULL total.

The failure must be explicit and deterministic.

---

# 28. Invalid Resource Type

If Register aggregation semantics require a particular resource type and the Movement contains an incompatible value, aggregation must be rejected.

For example:

```text
Quantity = "10"
```

must not automatically be converted to:

```text
Decimal("10")
```

unless such coercion is explicitly defined by the Register contract.

The Totals Engine must not perform implicit business conversions.

---

# 29. Missing Aggregation Dimension

If the aggregation key requires:

```text
Product
Warehouse
```

and the Movement lacks one of these dimensions, the Movement cannot unambiguously participate in the Inventory total.

This is an explicit semantic validation failure.

The Totals Engine must not:

* treat a missing dimension as a wildcard;
* use `None` as an implicit dimension;
* combine Movements with unknown Product/Warehouse values;
* silently skip the Movement.

This differs from Movement Query semantics:

```text
unspecified query dimension
    →
wildcard
```

For Totals aggregation, a dimension that is part of the aggregation key is a required part of accounting semantics.

---

# 30. Movement Type Semantics

The Totals Engine must not invent the meaning of `MovementType`.

For Inventory aggregation configuration:

```text
INCOME  → positive contribution
EXPENSE → negative contribution
```

If Register configuration supports additional movement types in the future, their contribution semantics must be explicitly defined.

An unknown or unsupported `MovementType` must not silently map to zero.

---

# 31. Atomicity Boundary

Totals update is not itself the global consistency boundary.

The architectural consistency boundary is higher:

```text
Posting / Unposting / Reposting
        │
        ▼
Logical Consistency Boundary
        │
        ├── Movement Persistence
        └── Totals Maintenance
```

Therefore, a successful call to:

```text
apply(Movement)
```

does not by itself mean that the complete Register operation has successfully completed.

If Movement persistence succeeds while totals maintenance fails, the higher-level consistency mechanism determines the final operation state.

---

# 32. Failure Semantics

The Totals Engine must distinguish at least:

### Success

The derived totals state was successfully updated and corresponds to the semantic operation.

### Failure

The totals state was not successfully updated.

### Indeterminate

It cannot be established reliably whether the derived totals state was fully applied.

An Indeterminate state must not silently be treated as success.

Recovery and reconciliation policy belongs to Register lifecycle/maintenance architecture.

---

# 33. Persistence Independence

The Totals Engine does not depend on a particular:

* database backend;
* filesystem layout;
* SQL query;
* ORM;
* Storage Provider.

The architecture remains:

```text
Totals Engine
      │
      ▼
Register / Persistence abstractions
      │
      ▼
Phase 5 Persistence Architecture
      │
      ▼
Storage Provider
```

The Totals Engine does not create a second generic persistence architecture.

---

# 34. Relation to Movement Query

Movement Query and Totals Engine have different responsibilities.

### Movement Query

```text
selection of Movement facts
```

### Totals Engine

```text
aggregation of Movement facts
```

Movement Query does not return totals.

The Totals Engine does not become a general-purpose query engine.

Totals rebuild may obtain authoritative Movement facts directly through the appropriate Register/Persistence abstraction.

Movement Query is not the source of truth for Totals.

---

# 35. Relation to Balance Query

Totals and Balance are different semantic concepts.

```text
Movement
   │
   ├──► Totals
   │
   └──► Balance Query semantics
```

Totals are derived aggregate state.

Balance Query defines how aggregate state is exposed and queried as a balance.

The Totals Engine is not the public Balance API.

---

# 36. Totals as Recoverable Derived State

The following is a normative rule:

> Totals can be completely destroyed and reconstructed from persisted Movement facts without loss of authoritative accounting information.

Therefore:

```text
Movement facts
    = accounting truth

Totals
    = recoverable derived state
```

This is a fundamental architectural distinction.

---

# 37. Maintenance Isolation

Rebuild is a maintenance operation.

In Phase 7, rebuild must not be silently performed inside an ordinary Posting operation.

Operational path:

```text
Posting
    └── incremental totals maintenance
```

Maintenance path:

```text
Rebuild
    └── full reconstruction from persisted Movement facts
```

These paths must remain semantically distinguishable.

---

# 38. No Reporting Semantics

The Totals Engine is not a reporting engine.

It is not responsible for:

* grouping by arbitrary dimensions;
* presentation sorting;
* report layouts;
* drill-down;
* pagination;
* charts;
* export formats;
* OLAP cubes;
* arbitrary user-defined aggregations.

The aggregation key is defined by Register semantics, not by a user report query.

---

# 39. No Valuation Semantics

The Phase 7 Totals Engine does not define:

* monetary valuation;
* average cost;
* FIFO;
* weighted average;
* cost layers;
* currency conversion;
* accounting valuation.

Phase 7 Inventory aggregates physical Quantity.

Valuation is a separate future concern.

---

# 40. No Period Closing

The Totals Engine is not responsible for:

* period closing;
* locked periods;
* reopening closed periods;
* carry-forward balances;
* opening balances.

Such semantics belong to a separate lifecycle/period architecture.

---

# 41. No Ledger Semantics

The Totals Engine is not a General Ledger.

It does not define:

* debit/credit;
* double-entry accounting;
* account hierarchy;
* journal entries;
* ledger posting.

Register movement aggregation remains within Phase 7 scope.

---

# 42. Inventory Register Baseline

The standard Inventory configuration for Phase 7 is:

```text
Register:
    Inventory

Dimensions:
    Product
    Warehouse

Resource:
    Quantity : Decimal

Quantity constraint:
    Quantity > 0

MovementType:
    INCOME  → +Quantity
    EXPENSE → -Quantity
```

Aggregation:

```text
InventoryTotal(
    Product,
    Warehouse
)
=
Σ signed Quantity
```

where:

```text
signed Quantity =
    +Quantity for INCOME
    -Quantity for EXPENSE
```

---

# 43. Inventory Example

Given:

```text
Movement 1:
    Product = P1
    Warehouse = W1
    Type = INCOME
    Quantity = 100

Movement 2:
    Product = P1
    Warehouse = W1
    Type = EXPENSE
    Quantity = 30

Movement 3:
    Product = P2
    Warehouse = W1
    Type = INCOME
    Quantity = 20
```

Totals:

```text
(P1, W1) → 70
(P2, W1) → 20
```

Movement identity does not appear in the totals key.

---

# 44. Inventory Rebuild Example

Persisted facts:

```text
P1 / W1 / INCOME  100
P1 / W1 / EXPENSE  30
P2 / W1 / INCOME   20
```

Rebuild must produce:

```text
P1 / W1 → 70
P2 / W1 → 20
```

regardless of:

* original insertion order;
* storage provider;
* physical storage layout.

---

# 45. Empty Register

If a Register has no applicable Movement facts:

```text
Totals = empty semantic aggregate
```

This is not an error.

An empty Register is a valid state.

---

# 46. Movement Identity Uniqueness

Uniqueness of persisted `Movement.identity` is the responsibility of the persistence/consistency architecture.

The Totals Engine must not independently deduplicate persisted facts.

If the authoritative persisted fact set violates the uniqueness invariant, this is a consistency failure.

The Totals Engine must not hide the problem through automatic deduplication.

---

# 47. Ordering Independence

Totals aggregation must be independent of Movement enumeration order.

Given:

```text
[M1, M2, M3]
```

and:

```text
[M3, M1, M2]
```

the same authoritative fact set must produce the same semantic totals state.

This is important because the persistence provider determines physical enumeration order, while Totals semantics must not depend on that order.

---

# 48. Deterministic Contribution

For fixed:

```text
Movement
+
Register aggregation configuration
```

the calculated contribution must always be the same.

Contribution calculation must not depend on:

* current time;
* random values;
* runtime identity;
* mutable global state;
* Storage Provider;
* network state.

---

# 49. Error Boundary

Totals-specific semantic validation errors must have a Register/Totals-level error boundary.

They must not be converted into generic `ValueError` or silently swallowed.

At minimum, the architecture distinguishes:

* invalid aggregation configuration;
* missing required dimension;
* missing required resource;
* incompatible resource value;
* invalid Inventory Quantity;
* unsupported MovementType;
* invalid period-scoped aggregation input;
* inconsistent totals state;
* persistence/execution failure.

The concrete exception hierarchy is defined by Concrete API Design.

---

# 50. Conceptual API

The architecture requires the following semantic capabilities:

```text
apply(Movement)
remove(Movement)
rebuild(Register)
```

Conceptually:

```text
apply:
    include Movement accounting effect

remove:
    exclude Movement accounting effect

rebuild:
    reconstruct Register totals from authoritative persisted Movement facts
```

Exact Python signatures, value objects, result types, and persistence dependencies are defined by Concrete API Design.

---

# 51. Conceptual State Transitions

For Movement `M`:

```text
Before:
    Totals = T

Apply(M):
    T' = T + contribution(M)
```

For removal:

```text
Before:
    Totals = T

Remove(M):
    T' = T - contribution(M)
```

For rebuild:

```text
Rebuild(Register):
    T' =
        aggregate(
            all authoritative applicable Movement facts
            belonging to Register
        )
```

---

# 52. Consistency Invariant

For any valid authoritative Movement set `M`:

```text
Totals(M)
=
aggregate(M)
```

Incremental totals:

```text
incremental_totals(M)
=
aggregate(M)
```

Rebuilt totals:

```text
rebuilt_totals(M)
=
aggregate(M)
```

Therefore:

```text
incremental_totals(M)
=
rebuilt_totals(M)
```

---

# 53. Architecture Invariants

The following invariants are normative.

### T-INV-01 — Movement Authority

Movement facts are authoritative; Totals are derived state.

### T-INV-02 — Register Scope

Totals never aggregate Movements from different Registers.

### T-INV-03 — Determinism

The same Movement facts plus the same Register aggregation configuration produce the same semantic Totals.

### T-INV-04 — Rebuild Independence

Rebuild depends on persisted Movement facts, not on previous Totals state.

### T-INV-05 — Incremental/Rebuild Equivalence

Incremental maintenance and rebuild produce semantically equivalent totals.

### T-INV-06 — Immutable Movement

Totals maintenance never mutates Movement.

### T-INV-07 — Explicit Contribution

Every participating Movement has an explicitly defined contribution.

### T-INV-08 — Required Aggregation Dimensions

Every dimension included in the Register aggregation key is required for the corresponding Movement.

### T-INV-09 — Required Resources

Every resource required by aggregation semantics must be present and valid.

### T-INV-10 — Period Semantics

Period-scoped operations use `[start, end)` and timezone-aware boundaries.

### T-INV-11 — No Silent Coercion

Missing or incompatible aggregation inputs are explicit failures.

### T-INV-12 — Provider Independence

Totals semantics do not depend on a concrete Storage Provider.

### T-INV-13 — No Silent Double Application

The system as a whole must not silently apply the same accounting effect more than once.

Ownership of duplicate-application detection is above the Totals Engine.

### T-INV-14 — Failure Visibility

Indeterminate totals maintenance cannot silently be considered successful.

### T-INV-15 — Maintenance Isolation

Rebuild is a maintenance operation distinct from ordinary incremental maintenance.

### T-INV-16 — Quantity Magnitude

For Inventory, Quantity is a positive magnitude:

```text
Quantity > 0
```

and the sign is determined by MovementType.

### T-INV-17 — No Stored Period Buckets

The Phase 7 Totals Engine does not maintain a separate persistent totals state for arbitrary periods.

---

# 54. Consistency Boundary

The architectural relationship is:

```text
                 Posting / Unposting / Reposting
                              │
                              ▼
                  Logical Consistency Boundary
                     ┌────────┴────────┐
                     │                 │
                     ▼                 ▼
             Movement Persistence   Totals Maintenance
                     │                 │
                     ▼                 ▼
                Movement facts      Derived Totals
```

The Totals Engine is not the global transaction coordinator.

Its contract defines the semantic state transition that must execute within a higher-level consistency boundary.

---

# 55. Relationship to Phase 7 Step 2

Step 2 established:

```text
RegisterFactPersistence
```

as the persistence boundary for authoritative Movement facts.

The Totals Engine uses this architecture for rebuild.

It does not create a second generic persistence architecture.

Conceptually:

```text
Totals Engine
      │
      ▼
Register persistence abstraction
      │
      ▼
RegisterFactPersistence
      │
      ▼
Phase 5 Persistence Architecture
```

---

# 56. Relationship to Phase 7 Step 3

Step 3 established Movement Query semantics.

The Totals Engine may obtain persisted Movement facts for rebuild, but Movement Query does not become the source of truth.

Therefore:

```text
Movement Query
    =
semantic selection API

Totals Engine
    =
aggregation / derived-state API
```

These boundaries must remain separate.

---

# 57. Acceptance Criteria

Step 4 is complete when all of the following are satisfied.

### AC-01

Movement is explicitly defined as the authoritative accounting fact.

### AC-02

Totals are explicitly defined as derived state.

### AC-03

Register scope is mandatory.

### AC-04

Aggregation semantics are defined by Register configuration rather than global platform assumptions.

### AC-05

TotalsKey is defined as a semantic aggregation key.

### AC-06

Movement contribution is explicitly defined.

### AC-07

Inventory contribution semantics are:

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

### AC-08

Inventory Quantity is defined as a positive magnitude:

```text
Quantity : Decimal
Quantity > 0
```

### AC-09

Required aggregation dimensions are explicitly validated.

### AC-10

Required resources are explicitly validated.

### AC-11

Missing/incompatible resources are explicit failures.

### AC-12

Missing aggregation dimensions are explicit failures.

### AC-13

`accounting_time=None` remains a valid Movement state and does not prohibit all-time aggregation when Register semantics permit it.

### AC-14

Period-scoped aggregation requires a defined `accounting_time`.

### AC-15

Period semantics use `[start, end)`.

### AC-16

Apply semantics are defined.

### AC-17

Remove semantics are defined.

### AC-18

Single-application responsibility is explicitly assigned above the Totals Engine.

### AC-19

Rebuild semantics are defined.

### AC-20

Rebuild uses persisted Movement facts rather than previous Totals.

### AC-21

The Phase 7 rebuild scope is the complete selected Register.

### AC-22

Rebuild is deterministic.

### AC-23

Incremental totals and rebuild are semantically equivalent.

### AC-24

Totals do not become a second source of accounting truth.

### AC-25

The Totals Engine is independent of the concrete Storage Provider.

### AC-26

Failure and Indeterminate states are explicitly defined.

### AC-27

Maintenance/rebuild is separated from ordinary posting flow.

### AC-28

Phase 7 does not introduce separate persisted period buckets for Totals.

### AC-29

Totals do not become a general-purpose query/reporting engine.

### AC-30

Concrete API Design can define the Python representation without changing the approved semantics.

---

# 58. Non-Goals

Step 4 does not define:

* SQL schema;
* database indexes;
* filesystem storage;
* ORM models;
* caching strategy;
* distributed totals;
* replication;
* sharding;
* OLAP;
* arbitrary report aggregation;
* pagination;
* valuation;
* currency conversion;
* FIFO/LIFO;
* cost accounting;
* General Ledger;
* period closing;
* opening balances;
* carry-forward balances;
* distributed transactions;
* asynchronous totals processing;
* event-sourcing architecture;
* historical snapshots;
* period-bucketed persistent totals.

---

# 59. Resulting Architecture

After Step 4, the Phase 7 architecture is:

```text
                    Posting
                       │
                       ▼
                  MovementSet
                       │
                       ▼
               Movement Validation
                       │
                       ▼
          ┌───────────────────────────┐
          │ Logical Consistency      │
          │ Boundary                 │
          │                           │
          │  Movement Persistence     │
          │          │                │
          │          ▼                │
          │    Movement Facts         │
          │                           │
          │  Totals Maintenance       │
          │          │                │
          │          ▼                │
          │      Derived Totals       │
          └───────────────────────────┘
                       │
              ┌────────┴─────────┐
              ▼                  ▼
       Movement Query       Balance Query
```

Source-of-truth hierarchy:

```text
Movement
   │
   ├── authoritative accounting fact
   │
   ├──► Movement Query
   │
   └──► Totals
           │
           └──► Balance Query
```

Totals remain fully recoverable from persisted Movement facts.

---

# 60. Final Architectural Decision

Phase 7 Totals Architecture adopts the following decisions:

1. **Movement is the authoritative accounting fact.**
2. **Totals are recoverable derived state.**
3. **Totals aggregation is Register-defined.**
4. **TotalsKey represents aggregation semantics, not Movement identity.**
5. **Inventory Quantity is a positive Decimal magnitude.**
6. **MovementType determines the sign of the Inventory contribution.**
7. **All-time totals do not require `accounting_time` when Register semantics do not require it.**
8. **Period-scoped operations require `accounting_time`.**
9. **Phase 7 does not maintain separate arbitrary period totals buckets.**
10. **Incremental maintenance and rebuild must be semantically equivalent.**
11. **Rebuild operates exclusively from authoritative persisted Movement facts.**
12. **The Totals Engine does not own Movement lifecycle or the global consistency boundary.**
13. **The guarantee against duplicate application of an accounting effect belongs to the higher-level lifecycle/consistency layer.**
14. **The Totals Engine is independent of the concrete Storage Provider.**
15. **Reporting, valuation, ledger, period closing, and distributed persistence remain outside Step 4 scope.**

---

# 61. Next Step

After approval of this contract, the next stage is:

**Step 5 — Balance Query Contract**

Step 5 will define:

* the semantic meaning of Balance;
* the relationship between Balance and Totals;
* balance dimensions;
* Register scope;
* period semantics;
* zero and negative balances;
* deterministic balance results;
* rules for using Totals;
* boundaries between aggregate state and the public Balance Query API.

Concrete Totals API and implementation should begin only after this contract has been architecturally approved.
