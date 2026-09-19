# PHASE 7 — STEP 5 — BALANCE QUERY CONTRACT

## 1. Document Status

**Phase:** 7 — Register Implementation
**Step:** 5 — Balance Query Contract
**Status:** Final
**Previous Step:** Step 4 — Totals Engine Contract
**Next Step:** Step 6 — Lifecycle / Maintenance Contract

---

# 2. Objective

This document defines the semantic contract for querying the current aggregate state of a Register.

The contract establishes:

* what a Register Balance means;
* where Balance derives its value from;
* the temporal semantics of Balance;
* the relationship between Movement Facts, Totals, and Balance;
* the aggregation scope of a Balance Query;
* the meaning of zero and negative balances;
* the consistency guarantees visible to callers;
* the error boundary;
* the responsibilities and non-responsibilities of Balance Query.

This document defines **semantic behavior**, not the final Python API.

The concrete API is defined in the next design step.

---

# 3. Architectural Position

The Phase 7 Register architecture is:

```text
Posting
  ↓
Movement Facts
  ↓
Totals Maintenance
  ↓
Current Totals
  ↓
Balance Query
  ↓
Balance Result

Movement Facts ───────────────► Movement Query
```

The responsibilities are intentionally separated:

| Layer              | Responsibility                                    |
| ------------------ | ------------------------------------------------- |
| Movement           | Authoritative accounting fact                     |
| Register Storage   | Persistence of Movement facts                     |
| Movement Query     | Selection of Movement facts                       |
| Totals Engine      | Derived aggregate state                           |
| Totals Maintenance | Establishment and maintenance of current Totals   |
| Balance Query      | Semantic exposure of current aggregate state      |
| Balance Result     | Read-only representation of the requested Balance |

Balance Query is therefore a **read boundary over maintained Totals**, not an independent accounting engine.

---

# 4. Definition of Balance

A **Balance** is the current Register-defined aggregate state exposed through a semantic Balance Query.

Formally:

```text
Balance(Register, AggregationScope)
    =
CurrentTotals(Register, AggregationScope)
```

Balance is therefore:

* a semantic read result;
* derived from current Totals;
* scoped to exactly one Register;
* scoped to one concrete Register-defined aggregation key;
* read-only;
* deterministic;
* provider-independent.

Balance is not an independent accounting fact.

---

# 5. Relationship to Movement and Totals

The architecture establishes the following authority hierarchy:

```text
Movement Facts
      ↓
   authoritative
      ↓
Totals
      ↓
    derived
      ↓
Balance
      ↓
 semantic read
```

## 5.1 Movement

Movement is the authoritative accounting fact.

Movement answers:

> What accounting fact was established?

Movement is persisted and immutable.

---

## 5.2 Totals

Totals are derived state calculated from persisted Movement facts.

Totals answer:

> What is the accumulated aggregate state represented by the applicable Movement facts?

Totals are recoverable from Movement facts.

The Totals contract is defined in:

```text
PHASE_7_STEP_4_TOTALS_ENGINE_CONTRACT.md
```

---

## 5.3 Balance

Balance is the semantic exposure of the current aggregate represented by Totals.

Balance answers:

> What is the current aggregate value for this specific Register aggregation scope?

Balance does not create another accounting state.

---

# 6. No Independent Balance Persistence

Phase 7 does not introduce a separate persistent Balance state.

There is no independent:

```text
Balance Storage
```

and no second accounting persistence mechanism.

The architecture remains:

```text
Register Services
      ↓
Register Persistence
      ↓
Persistence Architecture
      ↓
Storage Provider
```

Balance Query consumes the established Totals state.

Therefore:

```text
Movement Facts
      ↓
Totals
      ↓
Balance
```

not:

```text
Movement Facts ───────► Balance Storage
```

and not:

```text
Movement Facts
      ↓
Independent Balance Engine
```

---

# 7. Register Scope

Every Balance Query is scoped to exactly one Register.

A Balance Query must identify:

```text
Register Identity
```

Balance Query must never implicitly combine facts from multiple Registers.

A Register defines the semantics of the aggregate it exposes.

For Phase 7:

```text
Balance(Register A) != Balance(Register B)
```

unless the respective Register states happen to have equal aggregate values.

Register identity remains part of the semantic scope even when the numeric result is identical.

---

# 8. Concrete Aggregation Scope

Balance Query in Phase 7 operates on **one concrete Register-defined aggregation scope**.

Conceptually:

```text
Balance Query
    ↓
one TotalsKey
    ↓
one Current Total
    ↓
Balance Result
```

The Balance Query does not aggregate multiple `TotalsKey` values.

For the Inventory Register, the aggregation scope is:

```text
Product + Warehouse
```

Therefore:

```text
TotalsKey(
    product = P,
    warehouse = W
)
```

maps to one Inventory Balance:

```text
Balance(
    product = P,
    warehouse = W
)
```

A query such as:

```text
Product = P
Warehouse = unspecified
```

must **not** implicitly mean:

```text
SUM(
    Balance(P, Warehouse A),
    Balance(P, Warehouse B),
    ...
)
```

unless a future Register aggregation contract explicitly introduces such a higher-level aggregation scope.

Such higher-level aggregation is outside the Phase 7 Balance Query contract.

---

# 9. Aggregation Semantics

Balance does not define its own aggregation rules.

Aggregation semantics belong to the Register and Totals contract.

For Inventory:

```text
Dimensions:
    Product
    Warehouse

Resource:
    Quantity : Decimal
```

Movement contribution is:

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

Therefore:

```text
Inventory Balance(Product, Warehouse)
    =
Current Inventory Total(Product, Warehouse)
```

Balance Query must not reinterpret Movement types or resource semantics.

---

# 10. Current-State Semantics

Phase 7 Balance represents **current aggregate state**.

It is not:

* a period aggregate;
* an opening balance;
* a closing balance;
* an historical snapshot;
* an as-of balance;
* a time-filtered balance.

The word **current** refers to the latest successfully established, logically consistent Register state visible to the Balance Query.

It does **not** mean:

* the Movement with the latest timestamp;
* the latest wall-clock time;
* the current system clock;
* the latest persisted row;
* the latest storage-provider mutation.

Therefore:

```text
Current Balance
```

is a state concept, not a timestamp calculation.

---

# 11. No Period Balance in Phase 7

A Balance Query does not accept a time period.

The following concepts are intentionally distinct:

```text
Movement Query for [start, end)
```

and:

```text
Current Balance
```

A period query answers:

> Which Movement facts occurred during this interval?

A period aggregation answers:

> What is the aggregate contribution of those Movement facts?

A current Balance answers:

> What is the current aggregate Register state?

These are not interchangeable.

---

# 12. No Historical / As-Of Balance

Phase 7 does not define:

```text
Balance(as_of = T)
```

or equivalent historical semantics.

An as-of Balance would require a separate temporal contract defining:

* inclusion rules;
* cutoff semantics;
* timestamp semantics;
* treatment of corrections;
* treatment of unposting/reposting;
* consistency guarantees.

Those concerns are outside Phase 7.

---

# 13. Balance Result

Balance Query returns a semantic Balance Result.

The result must semantically contain at least:

* Register identity;
* the concrete aggregation scope / `TotalsKey`;
* the aggregate value.

The concrete Python representation is intentionally deferred to the Concrete API Design step.

Conceptually:

```text
BalanceResult
    register_identity
    aggregation_scope
    value
```

The result is read-only.

It must not expose mutable internal Totals state.

---

# 14. Zero Balance

Zero is a valid Balance.

For a numeric Inventory aggregate:

```text
Balance = Decimal("0")
```

is a valid result.

Two situations may both produce zero:

1. no applicable Movement facts exist;
2. applicable Movement facts exist but their net contribution is zero.

The numeric Balance value alone does not distinguish these cases.

Existence or history of Movement facts must be obtained through Movement Query if required.

Balance Query must not introduce an additional semantic distinction between:

```text
zero because empty
```

and:

```text
zero because netted
```

unless a future contract explicitly adds such metadata.

---

# 15. Negative Balance

A negative Balance is not automatically invalid at the Balance layer.

For example:

```text
Inventory Balance = -5
```

may be represented if the underlying Register and Totals semantics permit it.

Whether negative inventory is allowed operationally is a separate business or Register-level validation concern.

Balance Query must not silently reject a negative value merely because it is negative.

---

# 16. Resource Semantics

Balance values must use the resource semantics defined by the Register and Totals contracts.

For Inventory:

```text
Quantity : Decimal
```

is the aggregate resource.

Balance Query must not:

* silently convert resource types;
* infer missing resources;
* substitute another resource;
* silently coerce incompatible values.

The value returned by Balance must preserve the semantic type established by the Register.

---

# 17. Read-Only Boundary

Balance Query is strictly read-only.

A Balance Query must not:

* append Movement facts;
* remove Movement facts;
* mutate Movement facts;
* mutate Totals;
* establish accounting state;
* trigger posting;
* trigger unposting;
* trigger reposting.

Conceptually:

```text
query(...)
```

is a pure semantic read operation.

---

# 18. No Implicit Totals Rebuild

Balance Query must not rebuild Totals.

If Totals are missing, stale, inconsistent, or otherwise unavailable, Balance Query must not silently perform:

```text
Movement Facts
      ↓
Rebuild Totals
      ↓
Balance
```

as part of an ordinary read.

Rebuild is a Maintenance operation defined by the Totals / Lifecycle architecture.

This separation is important because an ordinary Balance read must not secretly become a potentially expensive state-reconstruction operation.

---

# 19. Totals Consistency Dependency

Balance Query assumes that the Totals state it consumes satisfies the Totals consistency contract.

Balance Query does not independently reconstruct or re-verify all Movement facts.

Therefore:

```text
Movement Facts
      ↓
Totals Maintenance
      ↓
Current Totals
      ↓
Balance Query
```

is the normal read path.

If Totals are inconsistent, the failure must be surfaced according to the Register/Totals consistency contract.

Balance Query must not silently substitute an independently calculated value.

---

# 20. Visibility and Logical Completion

Balance Query must not expose partially completed accounting operations.

The observable state must correspond to the latest successfully established logical Register state.

Therefore, during a posting operation:

```text
Posting started
      ↓
Movement / Totals changes in progress
```

an externally visible Balance must not represent a partially completed operation.

After successful logical completion:

```text
Posting completed successfully
      ↓
Movement + Totals state established
      ↓
Balance becomes visible
```

Failed operations must not produce a new visible Balance state.

This follows the Phase 6 event and logical consistency semantics.

---

# 21. Determinism

For the same logically consistent Register state and the same concrete aggregation scope, Balance Query must return the same semantic result.

Balance Query must not depend on:

* runtime object identity;
* storage-provider implementation details;
* filesystem layout;
* database row ordering;
* arbitrary iteration order;
* current wall-clock time;
* unrelated external state.

Balance is a function of:

```text
Register State
+
Aggregation Scope
```

not of the execution environment.

---

# 22. Provider Independence

Balance Query must not depend on a concrete persistence provider.

The architecture remains:

```text
Balance Query
      ↓
Register / Totals abstraction
      ↓
Persistence abstraction
      ↓
Storage Provider
```

Balance Query must not contain assumptions about:

* filesystem storage;
* in-memory dictionaries;
* SQL;
* a specific database engine;
* serialization format;
* storage paths.

Provider-specific behavior belongs below the Persistence Architecture boundary.

---

# 23. Movement Query vs Balance Query

Movement Query and Balance Query are intentionally separate APIs.

### Movement Query

Answers:

> Which Movement facts match these selection criteria?

Example:

```text
Register
+
Period
+
Partial Dimensions
```

Result:

```text
Movement[]
```

### Balance Query

Answers:

> What is the current aggregate value for this concrete aggregation scope?

Example:

```text
Register
+
Concrete TotalsKey
```

Result:

```text
BalanceResult
```

The two APIs must not be collapsed into a single generic query abstraction.

---

# 24. Totals Maintenance vs Balance Query

The responsibilities are:

### Totals Maintenance

Responsible for:

* applying Movement contributions;
* removing Movement contributions;
* rebuilding Totals;
* maintaining derived aggregate state;
* detecting Totals-level inconsistencies.

### Balance Query

Responsible for:

* identifying the requested Register scope;
* identifying the concrete aggregation scope;
* reading current Totals;
* exposing the corresponding semantic Balance Result.

Balance Query must not take over Totals Maintenance responsibilities.

---

# 25. Lifecycle Relationship

The logical accounting lifecycle is:

```text
Post
  ↓
Movement Facts established
  ↓
Totals maintained
  ↓
Balance changes
```

Unposting:

```text
Unpost
  ↓
Applicable Movement effects removed
  ↓
Totals maintained
  ↓
Balance changes
```

Reposting:

```text
Repost
  ↓
Old accounting effects removed
  ↓
New MovementSet established
  ↓
Totals maintained
  ↓
Balance reflects new state
```

Balance itself is not posted, unposted, or reposted.

Only the underlying accounting facts and derived Totals change.

---

# 26. Consistency Boundary

The logical consistency boundary is above individual persistence operations.

Conceptually:

```text
Logical Register Operation
        │
        ├── Movement Persistence
        │
        └── Totals Maintenance
```

Balance Query observes the state produced by this consistency boundary.

Therefore:

```text
Balance Query
```

is not itself a consistency mechanism.

It is a read boundary over the established state.

---

# 27. Failure Semantics

Balance Query must fail explicitly when the requested semantic result cannot be established.

Possible failures include:

* unknown Register;
* invalid aggregation scope;
* missing required Totals state;
* inconsistent Totals;
* incompatible resource type;
* persistence failure;
* provider failure translated through the appropriate abstraction boundary.

Balance Query must not:

* silently return an arbitrary default;
* silently rebuild Totals;
* silently aggregate unrelated scopes;
* silently coerce incompatible values;
* silently hide consistency failures.

A numeric zero is valid only when zero is the actual semantic Balance, not as a generic fallback for an error.

---

# 28. Error Boundary

The architectural rule is:

```text
Provider Error
      ↓
Persistence Error
      ↓
Register / Totals Error
      ↓
Balance Query Error
```

Each lower-level abstraction must translate errors into the semantic error vocabulary of its own boundary where required.

Balance Query must not expose storage-provider implementation details as part of its public semantic contract.

---

# 29. Inventory Register Baseline

Phase 7 uses Inventory as the standard Register implementation.

Inventory aggregation scope:

```text
Product + Warehouse
```

Resource:

```text
Quantity : Decimal
```

Movement contribution:

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

Therefore:

```text
Inventory Balance(Product, Warehouse)
=
Current Inventory Total(Product, Warehouse)
```

Example:

```text
Goods Receipt:
    Product = P1
    Warehouse = W1
    Quantity = 10

Inventory Balance(P1, W1)
    = 10
```

After an applicable expense movement:

```text
INCOME  = +10
EXPENSE = -3

Balance(P1, W1)
    = 7
```

---

# 30. Rebuild Relationship

The authoritative recovery path is:

```text
Persisted Movement Facts
        ↓
Totals Rebuild
        ↓
Current Totals
        ↓
Balance Query
        ↓
Balance Result
```

If the Totals state is rebuilt from the same persisted Movement fact set, the resulting Balance must be semantically identical to the Balance obtained before the rebuild, assuming the Register state represented by those facts is unchanged.

Formally:

```text
Rebuild(Facts) = ExistingTotals(Facts)
```

therefore:

```text
Balance_after_rebuild
=
Balance_before_rebuild
```

for the same logical fact set.

Balance Query itself does not perform the rebuild.

---

# 31. Maintenance Isolation

Maintenance operations such as Totals rebuild are separate from ordinary Balance reads.

A future Maintenance API may provide:

```text
rebuild(register)
```

but:

```text
balance.query(...)
```

must not invoke it implicitly.

This ensures that:

* reads remain predictable;
* expensive maintenance is explicit;
* failure semantics remain separated;
* operational state changes are not hidden inside queries.

---

# 32. Conceptual API

The following is conceptual only.

It does not define the final Python representation.

```python
class BalanceQuery:
    def query(
        self,
        register_identity: Identifier,
        aggregation_scope: TotalsKey,
    ) -> BalanceResult:
        ...
```

The important semantic properties are:

```text
Register Identity
+
One Concrete Aggregation Scope
        ↓
One Current Balance
```

The concrete API, validation types, result object, and error classes are defined in the next design step.

---

# 33. Architectural Invariants

## B-INV-01 — Balance Is Not an Accounting Fact

Balance must never become an alternative representation of Movement.

---

## B-INV-02 — Movement Authority

Movement facts remain the authoritative accounting facts.

---

## B-INV-03 — Totals Are Derived

Totals are derived state recoverable from Movement facts.

---

## B-INV-04 — Register Scope

Every Balance belongs to exactly one Register.

---

## B-INV-05 — Register-Defined Semantics

Balance aggregation semantics come from the Register and Totals contract.

---

## B-INV-06 — No Independent Balance State

Phase 7 does not introduce independently persisted Balance accounting state.

---

## B-INV-07 — Current-State Semantics

Balance represents the current successfully established Register aggregate state.

---

## B-INV-08 — No Period Balance

Phase 7 Balance Query does not define period-scoped Balance.

---

## B-INV-09 — No Historical Balance

Phase 7 Balance Query does not define as-of or historical Balance.

---

## B-INV-10 — Read-Only

Balance Query must not mutate accounting or derived state.

---

## B-INV-11 — No Implicit Rebuild

Balance Query must never silently rebuild Totals.

---

## B-INV-12 — Determinism

The same logical Register state and aggregation scope produce the same semantic Balance.

---

## B-INV-13 — Zero Is Valid

Zero is a valid numeric Balance.

---

## B-INV-14 — Negative Values Are Not Silently Rejected

Negative values are not invalid solely because they are negative.

---

## B-INV-15 — No Silent Coercion

Balance Query must not silently coerce incompatible resource values or missing semantics.

---

## B-INV-16 — Provider Independence

Balance Query must not depend on a concrete storage provider.

---

## B-INV-17 — No Reporting Semantics

Balance Query is not a reporting engine.

---

## B-INV-18 — Totals / Balance Consistency

Balance reflects the current Totals state established by the Totals consistency contract.

---

## B-INV-19 — Maintenance Isolation

Maintenance operations remain explicit and separate from Balance reads.

---

## B-INV-20 — No Second Persistence Architecture

Balance must use the existing Phase 5 Persistence Architecture.

---

## B-INV-21 — Concrete Aggregation Scope

Phase 7 Balance Query resolves exactly one concrete Register-defined aggregation scope corresponding to one `TotalsKey`.

---

## B-INV-22 — No Implicit Multi-Key Aggregation

Phase 7 Balance Query must not aggregate multiple `TotalsKey` values into a higher-level Balance.

---

## B-INV-23 — Successful-State Visibility

Balance Query must not expose partially completed accounting operations.

---

## B-INV-24 — Zero Does Not Encode Fact Existence

A zero Balance does not imply either absence or presence of Movement facts.

---

# 34. Relationship to Previous Contracts

### Step 2 — Register Storage Contract

Provides persisted Movement facts.

```text
RegisterFactPersistence
```

Balance does not bypass this architecture.

---

### Step 3 — Movement Query Contract

Provides selection of Movement facts.

Balance does not replace Movement Query.

---

### Step 4 — Totals Engine Contract

Defines:

* aggregation semantics;
* TotalsKey;
* contribution rules;
* incremental maintenance;
* rebuild;
* Totals consistency.

Balance consumes the resulting current Totals.

---

### Step 5 — Balance Query Contract

Defines:

* current aggregate semantics;
* concrete aggregation scope;
* read-only behavior;
* Balance Result semantics;
* consistency dependency;
* temporal limitations.

---

# 35. Acceptance Criteria

The Balance Query architecture is accepted when all of the following are true.

### AC-01 — Register Scope

Balance Query always identifies exactly one Register.

### AC-02 — Concrete Scope

Balance Query identifies exactly one concrete Register-defined aggregation scope.

### AC-03 — TotalsKey Relationship

The concrete scope corresponds to one `TotalsKey`.

### AC-04 — No Multi-Key Aggregation

Balance Query does not aggregate multiple TotalsKey values.

### AC-05 — Current State

Balance represents current aggregate state.

### AC-06 — No Period Semantics

Balance Query does not accept or interpret a period.

### AC-07 — No Historical Semantics

Balance Query does not define as-of or historical state.

### AC-08 — Totals Source

Balance derives from current Totals.

### AC-09 — No Independent Balance Persistence

No separate Balance accounting state is introduced.

### AC-10 — Movement Authority

Movement remains authoritative.

### AC-11 — Totals Recoverability

Totals remain rebuildable from Movement facts.

### AC-12 — No Implicit Rebuild

Balance Query does not rebuild Totals.

### AC-13 — Read-Only

Balance Query performs no accounting mutation.

### AC-14 — Successful-State Visibility

Partially completed operations are not visible as completed Balance state.

### AC-15 — Determinism

Same logical state and same scope produce the same Balance.

### AC-16 — Provider Independence

Balance behavior is independent of the storage provider.

### AC-17 — Register Semantics

Balance uses Register-defined aggregation semantics.

### AC-18 — Inventory Scope

Inventory uses Product + Warehouse as its concrete aggregation scope.

### AC-19 — Inventory Resource

Inventory Balance uses Quantity as Decimal.

### AC-20 — Inventory Contribution

INCOME contributes positive Quantity.

### AC-21 — Inventory Contribution

EXPENSE contributes negative Quantity.

### AC-22 — Zero Balance

Zero is a valid Balance.

### AC-23 — Zero Semantics

Zero does not indicate whether Movement facts exist.

### AC-24 — Negative Balance

Negative Balance is not rejected solely because it is negative.

### AC-25 — No Silent Defaults

Errors are not hidden by returning zero or another default.

### AC-26 — Resource Preservation

Balance preserves Register-defined resource semantics.

### AC-27 — No Silent Coercion

Incompatible resource values are not silently converted.

### AC-28 — Error Translation

Provider-specific failures do not leak through the semantic Balance boundary.

### AC-29 — Totals Consistency

Balance reflects the Totals consistency contract.

### AC-30 — Rebuild Consistency

Rebuilding Totals from the same Movement facts produces the same Balance.

### AC-31 — Maintenance Isolation

Rebuild remains an explicit maintenance operation.

### AC-32 — No Reporting

Balance Query does not become a reporting abstraction.

### AC-33 — No Second Persistence Architecture

Balance uses the existing Persistence Architecture.

---

# 36. Non-Goals

The following are explicitly outside this Phase 7 contract:

* historical balances;
* as-of balances;
* opening/closing balances;
* period balances;
* multi-period comparisons;
* higher-level aggregation over multiple TotalsKey values;
* reporting;
* dashboards;
* valuation;
* costing;
* financial statements;
* general ledger;
* period closing;
* distributed aggregation;
* OLAP;
* snapshots;
* independent Balance persistence;
* automatic Totals rebuild during reads;
* cross-register aggregation.

---

# 37. Resulting Architecture

The resulting Phase 7 architecture is:

```text
                         ┌──────────────────────┐
                         │      Posting         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Movement Facts     │
                         │   Authoritative      │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴───────────┐
                         │                      │
                         ▼                      ▼
                ┌─────────────────┐    ┌─────────────────┐
                │ Movement Query  │    │ Totals Engine   │
                └─────────────────┘    └────────┬────────┘
                                                 │
                                                 ▼
                                      ┌────────────────────┐
                                      │    TotalsKey       │
                                      │  one concrete key  │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │  Current Total     │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │   Balance Query    │
                                      └─────────┬──────────┘
                                                │
                                                ▼
                                      ┌────────────────────┐
                                      │   Balance Result   │
                                      └────────────────────┘
```

For Inventory:

```text
Product + Warehouse
        │
        ▼
Inventory TotalsKey
        │
        ▼
Inventory Total
        │
        ▼
Inventory Balance
```

The important architectural property is:

```text
Movement
    ↓
Totals
    ↓
Balance
```

with no independent accounting state introduced between these layers.

---

# 38. Final Architectural Decision

Phase 7 Balance is defined as the **current Register aggregate state exposed through a semantic read operation**.

The final architectural decisions are:

1. Movement remains the authoritative accounting fact.
2. Totals remain derived and recoverable state.
3. Balance is a semantic query result, not an accounting fact.
4. Balance is derived from current Totals.
5. Balance has exactly one Register scope.
6. Balance Query operates on exactly one concrete Register-defined aggregation scope.
7. That scope corresponds to one `TotalsKey`.
8. Balance Query does not aggregate multiple `TotalsKey` values.
9. Higher-level aggregation scopes are outside Phase 7 unless explicitly introduced by a future Register aggregation contract.
10. Inventory uses Product + Warehouse as its aggregation scope.
11. Inventory Balance uses Decimal Quantity.
12. INCOME contributes positive Quantity.
13. EXPENSE contributes negative Quantity.
14. Zero is a valid Balance.
15. Zero does not encode Movement fact existence.
16. Negative values are not rejected merely because they are negative.
17. Balance Query is read-only.
18. Balance Query does not rebuild Totals.
19. Balance Query does not independently reconstruct Movement facts.
20. Balance reflects the latest successfully established logically consistent Register state visible to the query.
21. Partially completed accounting operations must not become visible Balance state.
22. Balance has no period semantics in Phase 7.
23. Balance has no historical or as-of semantics in Phase 7.
24. Balance is deterministic.
25. Balance is provider-independent.
26. Balance uses the existing Phase 5 Persistence Architecture.
27. Balance does not introduce a second persistence architecture.
28. Balance is not a reporting, valuation, ledger, or period-closing mechanism.
29. Totals Maintenance and Balance Query remain separate responsibilities.
30. Rebuilding Totals from the same Movement fact set must reproduce the same Balance.

---

# 39. Next Step

The semantic Balance Query contract is now complete.

The next architectural step is:

```text
PHASE 7 — STEP 5 — CONCRETE API DESIGN
```

That step will define:

* concrete `BalanceQuery` input types;
* concrete aggregation-scope representation;
* `BalanceResult`;
* service/protocol boundaries;
* validation errors;
* interaction with the Totals Engine;
* public exports;
* unit-test boundaries;
* implementation constraints.

The concrete API must preserve every invariant defined by this document.
