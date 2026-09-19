# Phase 7 — Step 1: Register Query & Totals — Architecture Definition

**Status:** Architecture Definition — Revised
**Phase:** 7 — Register Query & Totals
**Baseline:** `origin/main @ 9f98c83`
**Previous Phase:** Phase 6 — Posting
**Scope:** Register Storage, Movement Query, Totals, Balance Query, Rebuild, Register Lifecycle
**Standard Configuration:** Inventory Register
**Vertical Slice:** Goods Receipt → Posting → Inventory Movements → Inventory Totals → Inventory Balance

---

# 1. Purpose

Phase 7 completes the first operational implementation of the Register Architecture.

Phase 6 established the ability to:

```text
Business Document
    ↓
Posting
    ↓
MovementSet
    ↓
Movement Validation
    ↓
Register Posting Contract
```

Phase 7 establishes what happens after a valid MovementSet reaches the Register boundary:

```text
Accepted Movement
    ↓
Register Persistence
    ↓
Movement Query
    ↓
Totals Maintenance
    ↓
Balance Query
```

The result is the first complete operational register vertical slice:

```text
Goods Receipt
    ↓
Posting
    ↓
Inventory Movement
    ↓
Inventory Persistence
    ↓
Inventory Totals
    ↓
Inventory Balance
```

The objective is not to build a general reporting system or a fully optimized register engine.

The objective is to establish the smallest complete architecture in which register movements become durable business facts and can be queried both as individual movements and as aggregated balances.

---

# 2. Architectural Objective

Phase 7 must provide the following platform capabilities:

1. persistent register movements;
2. movement queries;
3. temporal filtering;
4. dimension-aware filtering and aggregation;
5. resource aggregation;
6. totals maintenance;
7. balance queries;
8. totals rebuild;
9. consistency verification;
10. register lifecycle participation;
11. Inventory Register implementation in Standard Configuration.

The implementation must remain independent from:

* physical storage technology;
* database schema;
* storage provider;
* SQL query structure;
* index layout;
* serialization format;
* runtime object identity;
* arbitrary execution ordering.

---

# 3. Architectural Model

The fundamental architecture is:

```text
                         ┌────────────────────┐
                         │   Posting Engine    │
                         └─────────┬──────────┘
                                   │
                              MovementSet
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Movement Validation│
                         └─────────┬──────────┘
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │ Logical Consistency        │
                     │ Boundary                   │
                     │                            │
                     │ Movement Persistence       │
                     │            +               │
                     │ Totals Maintenance         │
                     └─────────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          Persisted Movements              Totals Buckets
                    │                             │
                    ▼                             ▼
            Movement Query                  Balance Query
```

The architecture is based on one primary fact model:

> Persisted Movement is the authoritative accounting fact.

Totals are derived state.

Balance is a semantic aggregate exposed by Register Architecture.

---

# 4. Primary Fact and Derived State

The distinction between facts and derived state is fundamental.

## 4.1 Movement

A Movement represents an accepted accounting fact.

A Movement contains, according to the Register Posting Contract:

* register identity;
* movement identity;
* source identity;
* accounting time;
* movement type;
* dimensions;
* resources;
* supported attributes.

Movement contents are immutable after acceptance.

Movement changes are represented through lifecycle operations such as:

* unposting;
* reposting;
* replacement of accounting effects.

A Movement is never modified in place merely to change its quantity, dimensions, or movement type.

---

## 4.2 Totals

Totals are derived state reconstructed from persisted movements.

Conceptually:

```text
Movements
    ↓
Aggregation
    ↓
Totals
```

Totals are therefore not an independent source of accounting truth.

The fundamental invariant is:

```text
Totals = Aggregate(Persisted Movements)
```

Any implementation that cannot reconstruct totals from persisted movements violates the Phase 7 architecture.

---

## 4.3 Balance

Balance is the primary aggregate exposed by the Register Architecture.

This does not make Balance a primary fact.

The semantic relationship is:

```text
Movement
    ↓
Totals
    ↓
Balance
```

Balance is therefore a derived register state exposed through the Register Query Model.

The distinction is:

```text
Movement = primary fact

Totals = persisted/materialized derived aggregation

Balance = semantic aggregate exposed to consumers
```

---

# 5. Register Storage Boundary

Register Architecture owns the semantic requirement that movements are persisted.

It does not own physical storage.

The dependency chain is:

```text
Register Services
        ↓
Register Persistence Contract
        ↓
Persistence Architecture
        ↓
Storage Provider
```

Phase 7 must not introduce a second generic persistence architecture parallel to Phase 5.

The existing Phase 5 persistence boundary, including `RegisterFactPersistence`, remains the persistence integration point.

Phase 7 may extend that contract where required by register semantics, including:

* movement persistence;
* movement querying;
* removal of accounting effects;
* replacement of accounting effects;
* support required by totals rebuild.

Such evolution must remain within the existing Persistence Architecture.

---

# 6. Storage Independence

Register Services must not depend on:

* SQLite;
* PostgreSQL;
* filesystem structures;
* SQL statements;
* table names;
* indexes;
* provider-specific transaction APIs;
* provider-specific serialization.

The Register layer consumes semantic persistence capabilities.

The Storage Provider remains an implementation detail.

Therefore:

```text
Register Query
```

must never mean:

```text
SELECT ...
```

at the architectural level.

Likewise:

```text
Totals Engine
```

must never depend on:

```text
SQL GROUP BY
```

or another physical aggregation mechanism.

---

# 7. Movement Identity

Movement identity is distinct from:

* source document identity;
* register identity;
* dimension identity;
* runtime object identity.

A Movement must have a stable semantic identity for its persisted lifetime.

Runtime object identity must never determine register identity.

The same semantic Movement must retain its identity independently of:

* Runtime instance;
* storage provider;
* storage location;
* process lifetime.

---

# 8. Movement Immutability

Once accepted and persisted, a Movement's semantic contents are immutable.

This means that operations such as:

```text
quantity 10 → quantity 15
```

do not mutate an existing Movement.

Instead, lifecycle operations replace the applicable accounting effect.

For example:

```text
Unpost:
    existing accounting effect
        ↓
    removed

Repost:
    existing accounting effect
        ↓
    removed
        ↓
    new MovementSet
        ↓
    persisted
```

The exact physical removal mechanism remains a Persistence Architecture concern.

---

# 9. Accounting Time

Every persisted Accumulation Movement participating in totals must have a defined accounting time.

The universal Movement model may allow an unset value where required by broader architecture, but an Accumulation Register participating in Phase 7 totals must reject a Movement without a valid accounting time.

Accounting time is the semantic temporal boundary used by:

* period filtering;
* totals bucketing;
* historical balance queries;
* as-of queries.

Runtime/system clock access must not be used implicitly by the Register implementation.

If current time is required, it must be supplied through the already established Posting Context / accounting time boundary.

---

# 10. Period Semantics

Phase 7 uses half-open temporal intervals:

```text
[start, end)
```

Therefore:

```text
start <= accounting_time < end
```

A movement exactly at `start` is included.

A movement exactly at `end` is excluded.

This rule applies consistently to:

* movement queries;
* totals queries;
* balance queries;
* rebuild calculations.

Period semantics must not depend on storage implementation.

---

# 11. Movement Query

Movement Query answers:

> What accounting facts occurred?

It returns persisted Movement facts.

Movement Query is distinct from Balance Query.

Conceptually:

```text
Movement Query
    ↓
individual persisted facts
```

while:

```text
Balance Query
    ↓
aggregated register state
```

Movement Query must support at least:

* register selection;
* period filtering;
* dimension filtering;
* deterministic result ordering.

Query ordering must be semantic and deterministic.

It must not depend on physical insertion order.

---

# 12. Dimension Semantics

Dimensions are metadata-defined classification keys of a Register.

For Inventory:

```text
Product
Warehouse
```

are dimensions.

Dimensions participate in aggregation.

Dimension values must be compared by semantic value, not Python object identity.

---

## 12.1 Full Dimension Context

A query may specify all dimensions:

```text
Product = A
Warehouse = Kyiv
```

This identifies one semantic dimension context.

---

## 12.2 Partial Dimension Filter

A query may specify only a subset:

```text
Product = A
```

This means:

> aggregate all applicable Warehouse values for Product A.

An unspecified dimension is not equivalent to a concrete null value.

---

## 12.3 Aggregation

Balance queries may aggregate across unspecified dimensions.

Therefore:

```text
Product = A
Warehouse = *
```

is semantically different from:

```text
Product = A
Warehouse = NULL
```

unless the Register Definition explicitly defines NULL as a valid dimension value.

Physical totals keys must not leak into this semantic distinction.

---

# 13. Resources

Resources are quantitative values accumulated by an Accumulation Register.

Inventory uses:

```text
Quantity
```

as its resource.

Resource arithmetic must be determined by the Register Definition / resource contract.

Phase 7 does not introduce accounting valuation or cost calculation.

For Inventory:

```text
Quantity
```

is the only required resource.

Floating-point arithmetic must not be introduced where the platform resource contract requires exact numeric semantics.

---

# 14. Movement Direction

Movement direction is determined exclusively by `movement_type`.

For a resource:

```text
INCOME
    → positive delta

EXPENSE
    → negative delta
```

Resource values themselves remain non-negative unless a future Register Definition explicitly establishes another semantic.

The Totals Engine must not infer direction from:

* quantity sign;
* document type;
* source object type;
* handler implementation;
* arbitrary conventions.

---

# 15. Totals Engine

The Totals Engine is responsible for:

* maintaining aggregate register state;
* calculating resource deltas;
* storing totals buckets;
* serving aggregate queries;
* rebuilding totals;
* verifying totals consistency.

The Totals Engine does not perform:

* posting;
* movement generation;
* business validation;
* valuation;
* reporting;
* dependency propagation.

The dependency is:

```text
Register Definition
        ↓
Dimensions / Resources
        ↓
Totals Engine
        ↓
Totals Strategy
```

The Totals Engine must be generic.

There must be no logic such as:

```python
if register == Inventory:
    ...
```

Inventory is simply the first concrete Register Definition.

---

# 16. Totals Buckets

A Totals Bucket represents an aggregated resource delta for:

* Register;
* period bucket;
* dimension context;
* resource.

Conceptually:

```text
TotalsBucket(
    register,
    period_bucket,
    dimensions,
    resource_deltas
)
```

The physical representation is implementation-defined.

Totals bucket granularity is not a semantic property of Balance.

It is a materialization strategy.

---

# 17. Totals Granularity

The architecture supports configurable/adaptive totals granularity as established by Register Architecture.

Register metadata may define preferred granularity.

The Totals Engine may select or adapt the physical aggregation strategy while preserving identical semantic results.

Existing architecture permits supported granularities such as:

```text
Year
Quarter
Month
Day
```

Phase 7 does not require implementing a workload-driven optimizer.

The initial implementation may use one deterministic supported granularity as the simplest viable implementation.

This is an implementation decision, not a new architectural restriction.

Regardless of physical granularity:

```text
Balance(Movements)
```

must remain semantically identical.

---

# 18. Incremental Totals Maintenance

When an accounting effect is successfully established, corresponding totals must be established within the same logical consistency boundary.

Conceptually:

```text
Accepted Movement
        ↓
Persist Movement
        ↓
Apply Totals Delta
```

but these are not independent externally visible transactions.

The architectural guarantee is:

```text
successful posting
    =>
    persisted movement effects
    +
    corresponding totals
```

within the defined consistency boundary.

If the operation cannot establish the required consistent result, it must not report successful completion.

The physical transaction mechanism remains the responsibility of the underlying application/persistence infrastructure.

Phase 7 does not prescribe a database-specific transaction API.

---

# 19. Posting Consistency Boundary

Posting and register effects preserve the Phase 6 logical consistency model.

Conceptually:

```text
Begin Posting Consistency Boundary
        ↓
Remove existing accounting effects if required
        ↓
Generate MovementSet
        ↓
Validate MovementSet
        ↓
Persist movement effects
        ↓
Update Totals
        ↓
Commit
        ↓
Publish completion events
```

The exact implementation may differ internally, but the semantic guarantee remains:

```text
either

new accounting state + corresponding totals

or

previous accounting state remains unchanged
```

A failed operation must not be reported as successful.

If the infrastructure cannot determine whether the durable operation completed, the operation remains subject to the existing Phase 6 `Indeterminate` semantics.

---

# 20. Rebuild

Totals Rebuild reconstructs derived state exclusively from persisted movements.

The algorithm is conceptually:

```text
Persisted Movements
        ↓
Read applicable facts
        ↓
Aggregate
        ↓
Construct new Totals
        ↓
Replace old Totals
```

The existing totals are never treated as authoritative input.

Therefore:

```text
Rebuild(Totals)
```

does not mean:

```text
repair(Totals)
```

It means:

```text
reconstruct(Totals, Movements)
```

---

# 21. Rebuild Determinism

For the same:

* persisted Movement set;
* Register Definition;
* accounting semantics;
* totals strategy;

rebuild must produce semantically identical totals.

The invariant is:

```text
Incrementally Maintained Totals
        ==
Rebuilt Totals
```

The comparison is semantic, not physical.

Different bucket layouts are acceptable if they produce the same Balance Query results.

---

# 22. Rebuild and Maintenance State

Phase 7 uses Register Maintenance as the initial consistency boundary for rebuild operations.

The simplest valid model is:

```text
Active
    ↓
Maintenance
    ↓
Rebuild
    ↓
Active
```

While a Register is in Maintenance:

* normal writes are blocked unless explicitly allowed by the lifecycle contract;
* rebuild operates against a stable movement set;
* no concurrent posting may invalidate the rebuild input.

Phase 7 does not introduce snapshot-based concurrent rebuild.

Such optimization may be added later without changing Register semantics.

---

# 23. Balance Query

Balance Query answers:

> What is the accumulated register state for the requested context?

Balance is derived from applicable movements.

For an Accumulation Register:

```text
Balance =
    sum(INCOME resources)
    -
    sum(EXPENSE resources)
```

subject to:

* register;
* accounting period/as-of boundary;
* dimension filters.

Balance Query may obtain its result from Totals Engine materialization.

Consumers do not need to know:

* which totals buckets were used;
* how many buckets exist;
* whether aggregation was adaptive;
* how storage is physically organized.

---

# 24. As-Of Semantics

An as-of balance at time `T` includes movements whose accounting time is within the applicable interval up to `T`.

Conceptually:

```text
(-∞, T]
```

for point-in-time balance semantics.

For implementation, this may be translated into the established period/bucket model.

The semantic result must not depend on physical totals granularity.

---

# 25. Empty Balance

If no applicable movements exist, Balance Query returns the semantic zero for every supported resource.

For Inventory:

```text
Quantity = 0
```

An empty balance is not an error.

It is a valid register state.

---

# 26. Unposting

Unposting removes the accounting effect produced by a previous successful Posting operation.

It does not mutate Movement contents.

Conceptually:

```text
Posted
    ↓
Unpost
    ↓
accounting effect removed
    ↓
totals adjusted accordingly
```

No compensating Movement is required for the Phase 7 implementation.

Compensating/reversal movements remain outside the current accounting model unless a later architecture explicitly introduces them.

---

# 27. Reposting

Reposting replaces the accounting effects of the previous Posting.

Example:

```text
Initial document:
    Quantity = 10

Balance:
    +10
```

After document modification:

```text
Quantity = 15
```

Reposting produces:

```text
remove old +10 effect
        ↓
generate new +15 Movement
        ↓
update totals
```

Final Balance:

```text
+15
```

not:

```text
+25
```

The old accounting effect must not remain active.

---

# 28. Failure Semantics

Phase 7 preserves the existing operation outcome model:

```text
Success
Failure
Indeterminate
```

## Success

The requested operation completed and the resulting semantic state is established.

## Failure

The operation did not complete and the defined consistency boundary remains in the previous valid state.

## Indeterminate

The infrastructure cannot establish whether the operation completed durably.

Indeterminate results must not be silently converted into Success or Failure.

This applies especially to:

* movement persistence;
* totals maintenance;
* unposting;
* reposting;
* rebuild.

---

# 29. Register Lifecycle

Phase 7 participates in the existing Register Lifecycle:

```text
Created
    ↓
Registered
    ↓
Initialized
    ↓
Active
    ↓
Maintenance
    ↓
Stopped
```

Phase 7 responsibilities include:

* correct behavior of Register services in Active state;
* controlled transition into Maintenance for rebuild;
* correct rejection of operations in incompatible lifecycle states;
* safe return from Maintenance to Active.

Phase 7 does not redesign Register Manager.

---

# 30. Register Events

Register Events describe completed register state changes.

Relevant events include:

* `MovementCreated`;
* `MovementDeleted`;
* `MovementChanged`;
* `TotalsUpdated`;
* `TotalsRebuilt`;
* `RegisterChanged`.

Events are emitted only after the corresponding logical state transition has been successfully established.

Events do not drive core register execution.

They do not replace the consistency boundary.

The Dependency Graph remains responsible for dependency propagation.

---

# 31. Dependency Graph Boundary

Register Architecture does not directly perform downstream dependency propagation.

The responsibility is:

```text
Register
    ↓
RegisterChanged
    ↓
Dependency Graph
    ↓
dependent recalculation
```

The Register implementation must not embed business-specific dependency logic.

---

# 32. Inventory Register

Standard Configuration defines the first Phase 7 Accumulation Register:

```text
Inventory
├── Dimensions
│   ├── Product
│   └── Warehouse
│
└── Resources
    └── Quantity
```

Inventory is not a special-case implementation of Totals Engine.

The Standard Configuration supplies:

* Inventory Register definition;
* dimensions;
* Quantity resource;
* Goods Receipt posting mapping;
* movement type mapping;
* Register Posting Contract;
* required document behavior.

Platform Register Architecture supplies:

* movement persistence;
* movement querying;
* totals maintenance;
* totals rebuild;
* balance querying;
* lifecycle;
* register consistency.

---

# 33. Goods Receipt Vertical Slice

The completed Phase 7 vertical slice is:

```text
Goods Receipt
    ↓
Posting Context
    ↓
Posting Handler
    ↓
MovementSet
    ↓
Register Posting Contract
    ↓
Inventory Movement
    ↓
Movement Persistence
    ↓
Totals Maintenance
    ↓
Inventory Balance Query
```

Example:

```text
Goods Receipt
Product = A
Warehouse = Kyiv
Quantity = 10
```

produces:

```text
Inventory Movement
    Product = A
    Warehouse = Kyiv
    Quantity = 10
    Type = INCOME
```

and therefore:

```text
Inventory Balance
    Product = A
    Warehouse = Kyiv
    Quantity = 10
```

A second receipt:

```text
Quantity = 5
```

produces:

```text
Balance = 15
```

An unpost of the second receipt restores:

```text
Balance = 10
```

A repost changing the second receipt from `5` to `8` results in:

```text
Balance = 18
```

---

# 34. Architectural Invariants

Phase 7 establishes the following invariants.

### REG-07-01 — Movement Is Primary Fact

Persisted Movement is the authoritative accounting fact.

### REG-07-02 — Totals Are Derived

Totals can be reconstructed from persisted movements.

### REG-07-03 — Balance Is Derived Aggregate

Balance is an aggregate derived from applicable register movements.

### REG-07-04 — Storage Independence

Register services do not depend on physical storage implementation.

### REG-07-05 — Persistence Boundary Reuse

Phase 7 does not introduce a second generic persistence architecture parallel to Phase 5.

### REG-07-06 — Movement Immutability

Accepted Movement contents are immutable.

### REG-07-07 — Stable Movement Identity

Movement identity is independent of runtime identity and storage location.

### REG-07-08 — Accounting Time

Accumulation Movements participating in totals have defined accounting time.

### REG-07-09 — Period Boundary

Temporal ranges use deterministic `[start, end)` semantics.

### REG-07-10 — Direction

Movement direction is determined exclusively by `movement_type`.

### REG-07-11 — Dimension Semantics

Dimension equality is semantic and independent of Python object identity.

### REG-07-12 — Partial Dimension Queries

Unspecified dimensions represent aggregation/filtering semantics, not an implicit concrete dimension value.

### REG-07-13 — Resource Semantics

Resource arithmetic follows the Register/resource contract.

### REG-07-14 — Totals Granularity Is Implementation Detail

Physical totals granularity does not alter semantic Balance results.

### REG-07-15 — Totals Engine Genericity

Totals Engine does not special-case Inventory or other specific registers.

### REG-07-16 — Incremental/Rebuild Equivalence

Incrementally maintained totals and rebuilt totals produce equivalent semantic results.

### REG-07-17 — Rebuild From Movements

Rebuild never treats previous totals as authoritative input.

### REG-07-18 — Rebuild Maintenance Boundary

Phase 7 rebuild operates under the defined Register Maintenance consistency rule.

### REG-07-19 — Posting Consistency

Movement persistence and totals maintenance participate in the same logical consistency boundary for Posting.

### REG-07-20 — No Partial Successful Posting

A Posting operation must not report success while leaving movement effects and totals semantically inconsistent.

### REG-07-21 — Unpost Removes Effect

Unposting removes the applicable accounting effect without mutating Movement contents.

### REG-07-22 — Repost Replaces Effect

Reposting removes the old accounting effect before establishing the new one.

### REG-07-23 — Empty Balance

No applicable movements produce the semantic resource zero.

### REG-07-24 — Lifecycle Enforcement

Register operations respect Register lifecycle state.

### REG-07-25 — Events Describe Completed State

Register events are emitted only after successful logical state transitions.

### REG-07-26 — Dependency Separation

Dependency Graph owns propagation; Register does not.

### REG-07-27 — Runtime Identity Independence

Runtime object identity does not determine persistent register identity.

### REG-07-28 — Deterministic Query Semantics

Equivalent semantic queries produce equivalent results independently of physical storage ordering.

### REG-07-29 — Outcome Semantics

Register operations preserve Success / Failure / Indeterminate semantics.

### REG-07-30 — Inventory Genericity

Inventory behavior is provided by metadata/configuration rather than Register Engine special cases.

---

# 35. Acceptance Criteria

Phase 7 is architecturally complete when:

### AC-07-01 — Movement Persistence

Accepted register movements are durably persisted through the existing Persistence Architecture.

### AC-07-02 — Movement Query

Persisted movements can be queried through Register services.

### AC-07-03 — Temporal Filtering

Movement queries support deterministic `[start, end)` period filtering.

### AC-07-04 — Dimension Filtering

Movement and balance queries support semantic dimension filtering.

### AC-07-05 — Partial Dimensions

Queries correctly aggregate across unspecified dimensions.

### AC-07-06 — Resource Aggregation

Register resources are aggregated according to their resource contract.

### AC-07-07 — Totals Maintenance

Successful register operations maintain corresponding totals.

### AC-07-08 — Balance Query

Balances can be queried through Register services without exposing storage implementation.

### AC-07-09 — Empty Balance

Empty register state returns semantic zero.

### AC-07-10 — Inventory Balance

Goods Receipt produces the expected Inventory balance.

### AC-07-11 — Unpost

Unposting removes the accounting effect and restores the correct balance.

### AC-07-12 — Repost

Reposting replaces the previous accounting effect and does not double-count.

### AC-07-13 — Rebuild

Totals can be rebuilt exclusively from persisted movements.

### AC-07-14 — Rebuild Equivalence

Rebuilt totals produce the same semantic balance results as incrementally maintained totals.

### AC-07-15 — Lifecycle

Register operations and rebuild respect lifecycle state.

### AC-07-16 — Failure Semantics

Register failures do not falsely report successful completion and preserve Success / Failure / Indeterminate semantics.

### AC-07-17 — Atomic Register Effect

Within the Posting consistency boundary, persisted movement effects and corresponding totals are established together.

### AC-07-18 — Persistence Architecture Boundary

Phase 7 uses the existing Persistence Architecture rather than introducing a parallel generic persistence layer.

### AC-07-19 — Accounting Time

Accumulation movements participating in totals have valid accounting time.

### AC-07-20 — Query Determinism

Equivalent semantic queries produce deterministic results independently of physical storage order.

### AC-07-21 — Rebuild Isolation

Rebuild operates under the defined Maintenance consistency boundary.

### AC-07-22 — Inventory Genericity

Inventory is implemented through Register metadata/configuration rather than Totals Engine special cases.

---

# 36. Non-Goals

The following are explicitly outside Phase 7:

* reporting;
* arbitrary analytical query language;
* Reporting Architecture;
* OLAP;
* distributed storage;
* sharding;
* replication;
* distributed transactions;
* workload-driven totals optimization beyond the minimum viable strategy;
* full adaptive totals optimizer;
* valuation;
* cost accounting;
* ledger;
* period closing;
* multi-register joins;
* financial statement generation;
* advanced historical reconstruction beyond the defined balance semantics;
* snapshot-based concurrent rebuild;
* compensating/reversal accounting model.

---

# 37. Phase 7 Step Sequence

The implementation proceeds through the following steps.

## Step 1 — Architecture Definition

Define:

* register storage boundary;
* movement query semantics;
* totals semantics;
* balance semantics;
* rebuild semantics;
* lifecycle participation;
* consistency boundary;
* Inventory scope.

**Status:** completed after Architecture Review revision.

---

## Step 2 — Register Storage Contract

Define the concrete Register-side persistence contract built on the existing Phase 5 Persistence Architecture.

Scope includes:

* movement persistence;
* movement retrieval;
* accounting-effect removal;
* replacement;
* query requirements;
* rebuild input;
* persistence failure semantics.

---

## Step 3 — Movement Query Contract

Define:

* query request;
* period filtering;
* dimension filtering;
* deterministic ordering;
* result model;
* empty result semantics.

---

## Step 4 — Totals Engine Contract

Define:

* totals request;
* bucket semantics;
* resource aggregation;
* dimension aggregation;
* granularity strategy;
* incremental update;
* rebuild;
* consistency validation.

---

## Step 5 — Balance Query Contract

Define:

* balance request;
* as-of semantics;
* dimension filtering;
* resource result;
* zero semantics;
* interaction with Totals Engine.

---

## Step 6 — Lifecycle / Maintenance Contract

Define:

* Active operations;
* Maintenance transition;
* rebuild rules;
* write restrictions;
* failure recovery;
* lifecycle validation.

---

## Step 7 — Platform Implementation

Implement the platform contracts without introducing Standard Configuration-specific logic into the Register Engine.

---

## Step 8 — Inventory Register Completion

Complete the Standard Configuration Inventory Register definition:

```text
Product
Warehouse
Quantity
```

and its integration with Goods Receipt posting.

---

## Step 9 — Vertical Slice

Complete:

```text
Goods Receipt
    ↓
Posting
    ↓
Inventory Movement
    ↓
Persistence
    ↓
Totals
    ↓
Balance
```

including:

* unpost;
* repost;
* dimension filtering;
* temporal queries.

---

## Step 10 — Rebuild and Consistency Validation

Verify:

```text
incremental totals
        ==
rebuilt totals
```

and validate:

* failure behavior;
* maintenance behavior;
* consistency boundary;
* Inventory balances.

---

## Step 11 — Final Validation

Run:

* unit tests;
* contract tests;
* integration tests;
* Vertical Slice tests;
* Ruff;
* Black;
* Mypy;
* full Pytest suite.

Final Phase 7 acceptance requires all defined architectural invariants and acceptance criteria to hold.

---

# 38. Architecture Review Decision

The revised Step 1 architecture is considered aligned with the existing AcCore architecture when the following decisions remain normative:

1. Movement is the primary accounting fact.
2. Totals are derived state.
3. Balance is a primary aggregate exposed by Register Architecture, but never a primary fact.
4. Phase 5 Persistence Architecture remains the persistence boundary.
5. `RegisterFactPersistence` is evolved rather than replaced by a parallel persistence abstraction.
6. Movement persistence and totals maintenance participate in the same logical Posting consistency boundary.
7. Unposting removes accounting effects without mutating Movement contents.
8. Reposting replaces old accounting effects with newly generated movements.
9. Accumulation movements participating in totals have defined accounting time.
10. Temporal queries use `[start, end)` semantics.
11. Dimension semantics explicitly support full and partial dimension contexts.
12. Totals granularity remains an implementation/materialization concern.
13. Rebuild reconstructs totals from persisted movements.
14. Rebuild initially uses Register Maintenance as its consistency boundary.
15. Success / Failure / Indeterminate semantics remain intact.
16. Inventory is a metadata-defined Register, not a Totals Engine special case.

---

# 39. Final Architectural Boundary

The final Phase 7 architecture is:

```text
                    STANDARD CONFIGURATION
                    ──────────────────────

                    Goods Receipt
                          │
                          ▼
                    Posting Handler
                          │
                          ▼
                    MovementSet
                          │
                          ▼
                 Register Posting Contract
                          │
                          ▼
                 ┌───────────────────┐
                 │ Register Runtime  │
                 └─────────┬─────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Movement Persistence          Totals Engine
             │                           │
             ▼                           ▼
      Persisted Movements          Totals Buckets
             │                           │
             ▼                           ▼
      Movement Query              Balance Query
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
                    Register State
                           │
                           ▼
                    RegisterChanged
                           │
                           ▼
                   Dependency Graph


                    PERSISTENCE BOUNDARY
                    ────────────────────

                    Register Services
                           │
                           ▼
                 RegisterFactPersistence
                           │
                           ▼
                 Persistence Architecture
                           │
                           ▼
                    Storage Provider
```

The fundamental architectural rule is:

> Register Architecture owns the semantic meaning of register facts, queries, totals, and balances. Persistence Architecture owns durable storage. Totals Engine owns derived aggregate state. Posting Architecture owns generation and lifecycle of accounting effects. No subsystem crosses another subsystem's semantic boundary.

This completes the revised Architecture Definition for Phase 7 Step 1.
