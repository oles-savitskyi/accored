# PHASE 7 — STEP 3 — MOVEMENT QUERY CONTRACT

## 1. Purpose

Step 3 defines the semantic read contract for querying persisted Register `Movement` facts.

The contract establishes how Register Architecture selects authoritative Movement facts by:

* Register;
* accounting period;
* dimensions;
* deterministic ordering.

The contract does not define:

* physical storage;
* storage-provider APIs;
* persistence implementation;
* totals calculation;
* balance calculation;
* reporting;
* pagination;
* arbitrary sorting;
* aggregation.

The purpose of the Movement Query contract is to provide a stable semantic boundary between authoritative Register facts and higher-level Register operations such as Totals and Balance queries.

---

## 2. Architectural Position

The Phase 7 architecture is:

```text
Posting
   │
   ▼
MovementSet
   │
   ▼
Logical Consistency Boundary
   │
   ▼
Register Fact Persistence
   │
   ▼
Persisted Movement Facts
   │
   ▼
Movement Query
   │
   ├──────────────► Totals Engine
   │
   └──────────────► Balance Query
```

The distinction between persistence and querying is fundamental:

```text
RegisterFactPersistence
    = access to authoritative facts

Movement Query
    = semantic selection of authoritative facts
```

`Movement Query` is therefore a Register semantic read boundary. It is not an extension of the generic Phase 5 persistence architecture and must not become a generic Query Repository.

---

## 3. Source of Truth

The authoritative source for Movement Query is the persisted set of `Movement` facts.

Movement Query MUST NOT derive its primary result from:

* Totals;
* Balance;
* document state;
* Posting Context;
* runtime objects;
* storage-provider-specific state;
* non-authoritative caches.

The semantic model is:

```text
Persisted Movement Facts
          │
          ▼
    Movement Query
          │
          ▼
   MovementSet result
```

Totals and Balance are derived Register semantics and MUST NOT become the source of truth for Movement queries.

---

## 4. Register Scope

Every Movement Query MUST be scoped to exactly one `register_identity`.

A Movement belongs to the result only if:

```text
movement.register_identity == query.register_identity
```

A Movement belonging to another Register MUST NOT appear in the result, regardless of whether all other query criteria match.

Register identity is therefore a mandatory part of the query semantic scope.

---

## 5. Period Semantics

A period is represented as a half-open interval:

```text
[start, end)
```

A Movement belongs to the requested period if and only if:

```text
accounting_time is not None
AND
start <= accounting_time < end
```

Therefore:

* `accounting_time == start` is included;
* `accounting_time == end` is excluded;
* `accounting_time < start` is excluded;
* `accounting_time > end` is excluded;
* `accounting_time is None` is excluded.

Half-open intervals allow adjacent periods to be composed without overlap:

```text
[start, middle)
[middle, end)
```

The two periods share a boundary but do not contain the same Movement.

---

## 6. Period Validity

A valid query period MUST satisfy:

```text
start < end
```

The following are invalid query inputs:

```text
start == end
start > end
```

An invalid period MUST NOT be silently interpreted as an empty result.

This distinguishes:

```text
valid query with no matching facts
        → ()

invalid query
        → query validation failure
```

The concrete error type is deferred to the Concrete API Design.

---

## 7. Temporal Semantics and Time Zones

All temporal values participating in period-based Movement Query MUST be timezone-aware.

This applies to:

* period `start`;
* period `end`;
* `Movement.accounting_time` when it participates in period evaluation.

Naive `datetime` values MUST NOT be silently interpreted as:

* UTC;
* local system time;
* application time;
* storage-provider time.

The Query layer MUST NOT invent a timezone for a naive datetime.

Accounting time represents an actual accounting instant, and the query must compare temporal values according to their represented instant rather than according to storage or runtime locality.

For example, two timezone-aware values representing the same instant must compare as the same instant even if their UTC offsets differ.

---

## 8. Movements Without Accounting Time

The universal `Movement` model permits:

```python
accounting_time: datetime | None
```

However, a Movement with:

```text
accounting_time is None
```

does not belong to any period.

Such a Movement:

* remains a valid persisted Movement fact;
* is not itself a persistence error;
* MUST NOT be assigned an implicit timestamp;
* MUST NOT be assigned the current time;
* MUST NOT be included in a period query.

Therefore:

```text
Movement(accounting_time=None)
          │
          ▼
     period query
          │
          ▼
       excluded
```

Inventory accumulation movements are expected to have a defined accounting time and therefore participate normally in period-based querying.

---

## 9. Dimension Filtering

Dimensions are part of the semantic context of a Movement.

A query MAY specify a subset of dimensions.

For example, a Movement may contain:

```text
Product   = product-1
Warehouse = warehouse-1
```

while the query specifies only:

```text
Product = product-1
```

The Movement matches the query.

The semantic rule is:

```text
query dimensions ⊆ movement dimensions
```

with exact equality required for every dimension explicitly specified by the query.

For every specified dimension:

```text
movement contains the dimension
AND
movement value == requested value
```

---

## 10. Unspecified Dimensions

A dimension not specified by the query is a wildcard.

For example:

```text
query:
    Product = product-1
```

matches:

```text
Product = product-1
Warehouse = warehouse-1
```

and:

```text
Product = product-1
Warehouse = warehouse-2
```

provided all other query criteria match.

The absence of a dimension from the query MUST NOT be interpreted as:

```text
dimension == NULL
```

or as a requirement that the Movement not contain that dimension.

---

## 11. Missing Required Dimension

If the query specifies a dimension and the Movement does not contain that dimension, the Movement does not match.

For example:

```text
query:
    Warehouse = warehouse-1
```

does not match:

```text
Movement:
    Product = product-1
```

The absence of a required dimension is therefore a non-match, not a query error.

---

## 12. Empty Dimension Filter

An empty dimension filter imposes no dimension restrictions.

Therefore:

```text
dimensions = {}
```

means:

```text
match any dimensions
```

subject to the other query criteria, especially Register and Period.

The concrete API SHOULD avoid introducing unnecessary distinction between an empty filter and an omitted filter unless such a distinction is required by another semantic boundary.

---

## 13. Dimension Value Semantics

Movement Query uses the existing `MovementDimensions` model.

The Query layer MUST NOT:

* redefine dimension value semantics;
* convert dimension values;
* normalize values;
* infer business meaning;
* introduce Register-specific business rules.

For example, the Query layer does not need to know that:

```text
Product
```

represents a product or that:

```text
Warehouse
```

represents a warehouse.

Those meanings belong to Register metadata and the relevant Register definition.

The Query contract is concerned only with semantic equality of the dimension values supplied by the query and stored on the Movement.

---

## 14. Result Type

A successful Movement Query returns a sequence of authoritative `Movement` facts.

The concrete API target is:

```python
tuple[Movement, ...]
```

The result MUST preserve the complete Movement semantic object.

The Query layer MUST NOT replace Movement with a persistence-specific representation.

---

## 15. Empty Results

A valid query with no matching Movement facts returns:

```python
()
```

An empty result is not an error.

This distinction is mandatory:

```text
valid query + no matches
        → ()

invalid query
        → validation failure
```

---

## 16. Deterministic Ordering

Movement Query results MUST be deterministically ordered.

The semantic ordering is:

1. `accounting_time` ascending;
2. Movement identity as deterministic tie-breaker.

Conceptually:

```text
accounting_time ASC
Movement identity ASC
```

The second key is a semantic Movement identity ordering. Its concrete Python representation is an implementation detail and must not become an architectural dependency.

For the current `Identifier` implementation, the concrete API may use its stable string representation as the ordering key.

The ordering MUST NOT depend on:

* insertion order;
* dictionary iteration order;
* storage layout;
* storage provider;
* database execution plan;
* runtime object identity.

---

## 17. Determinism

For the same authoritative Movement facts and the same query inputs, Movement Query MUST produce the same semantic result and deterministic ordering.

Formally:

```text
same facts
+
same register
+
same period
+
same dimensions
        │
        ▼
same MovementSet
        +
same ordering
```

The result MUST NOT depend on:

* current system time;
* runtime identity;
* storage provider;
* storage layout;
* arbitrary collection ordering;
* uncontrolled external state.

Movement Query is therefore deterministic with respect to its explicit inputs and authoritative persisted facts.

---

## 18. Persistence Boundary

`RegisterFactPersistence` remains the persistence boundary defined by Step 2.

Its responsibilities remain fact-oriented:

```python
append(...)
find_by_source_document(...)
remove(...)
enumerate(...)
```

Movement Query MUST NOT cause query-specific methods to be added to `RegisterFactPersistence`, such as:

```python
find_by_period(...)
find_by_dimensions(...)
search(...)
query(...)
list(...)
```

Such methods would move Register semantic query responsibilities into the persistence layer.

The intended architecture is:

```text
RegisterFactPersistence
        │
        ▼
authoritative facts
        │
        ▼
Movement Query
        │
        ▼
semantic MovementSet
```

---

## 19. Relationship to `enumerate()`

The `enumerate(register_identity)` operation defined in Step 2 provides access to the complete authoritative fact set for a Register.

It is primarily a fact/maintenance primitive.

It MUST NOT be interpreted as the public Movement Query API.

A concrete Movement Query implementation MAY internally use `enumerate()` during the initial implementation.

However, this is an implementation choice, not an architectural requirement.

A future implementation MAY use a more efficient provider-specific mechanism as long as the semantic Movement Query contract remains unchanged.

---

## 20. No Aggregation

Movement Query returns Movement facts.

It MUST NOT aggregate them.

For example, given:

```text
+10
+20
-5
```

the Movement Query result contains three Movement facts.

It MUST NOT return:

```text
25
```

Aggregation belongs to the Totals Engine defined in Step 4.

The boundary is:

```text
Movement Query
    → Movement facts

Totals Engine
    → derived aggregate state
```

---

## 21. No Balance Calculation

Movement Query MUST NOT calculate:

* opening balance;
* closing balance;
* turnover;
* resource balance;
* dimension balance;
* as-of balance.

Even when such a value could technically be calculated by iterating over Movement facts, doing so would cross the architectural boundary into Balance Query semantics.

The intended architecture is:

```text
Movement Query
       │
       ▼
Movement facts
       │
       ├──► Totals Engine
       │
       └──► Balance Query
```

---

## 22. Read-Only Semantics

Movement Query is a read-only operation.

A successful query MUST NOT:

* create Movement;
* remove Movement;
* mutate Movement;
* modify Totals;
* modify Balance;
* initiate Posting;
* initiate Unposting;
* initiate Reposting;
* emit accounting lifecycle events.

Query execution has no accounting side effects.

---

## 23. Consistency Semantics

Movement Query reads authoritative persisted facts.

Movement generated by Posting MUST NOT be considered query-visible until the relevant logical consistency boundary has completed successfully.

The Query layer MUST NOT attempt to reconstruct partially persisted accounting state from:

* Posting state;
* in-memory MovementSet;
* document state;
* pending persistence operations.

After successful completion of the relevant consistency boundary, persisted Movement facts become available to Movement Query according to the persistence consistency semantics.

---

## 24. Failure Semantics

The absence of matching facts is not a failure:

```python
()
```

Query failure means that the query itself could not be executed successfully.

Possible failures include existing Phase 5 persistence failures such as:

* persistence failure;
* integrity failure;
* unsupported operation;
* indeterminate persistence state.

The Query layer SHOULD reuse the existing persistence/error architecture where appropriate.

It MUST NOT introduce an independent parallel persistence error hierarchy merely for query execution.

Invalid query input, such as an invalid period, is a semantic validation failure and will receive its concrete error type in the Concrete API Design.

---

## 25. Separation from Totals and Balance

The three responsibilities are explicitly separated:

```text
Movement Query
    ↓
select authoritative Movement facts

Totals Engine
    ↓
maintain / rebuild derived aggregate state

Balance Query
    ↓
expose semantic balance information
```

Neither Totals nor Balance semantics may be pushed downward into Movement Query merely for implementation convenience.

---

## 26. Inventory Relevance

The first concrete Register implementation is Inventory.

Inventory Movement facts use dimensions such as:

```text
Product
Warehouse
```

and resources such as:

```text
Quantity
```

The Movement Query contract itself remains Register-generic.

It does not hard-code:

* Product;
* Warehouse;
* Quantity;
* Inventory-specific movement types.

Inventory-specific semantics belong to the Inventory Register definition and its concrete configuration.

---

## 27. Non-Goals

Step 3 explicitly does not define:

* database indexes;
* storage schemas;
* SQL;
* filesystem layout;
* query optimization;
* caching;
* pagination;
* arbitrary ordering;
* grouping;
* aggregation;
* totals;
* balances;
* reporting;
* OLAP;
* distributed query execution;
* cross-register queries;
* cross-register joins;
* period closing;
* valuation;
* accounting ledger semantics.

These concerns remain outside the Step 3 boundary.

---

## 28. Architectural Invariants

The following invariants are normative for Phase 7 Step 3:

1. Every query is scoped to exactly one Register.
2. Period semantics are `[start, end)`.
3. A valid period requires `start < end`.
4. `start == end` is invalid.
5. `start > end` is invalid.
6. Period boundaries MUST be timezone-aware.
7. Naive temporal values MUST NOT be silently interpreted.
8. `accounting_time is None` excludes a Movement from period queries.
9. An empty dimension filter imposes no dimension restriction.
10. Every explicitly specified dimension requires exact match.
11. A missing required Movement dimension is a non-match.
12. Unspecified Movement dimensions are not restrictions.
13. Successful queries return `tuple[Movement, ...]`.
14. No matching facts return `()`.
15. Results are deterministically ordered by accounting time and Movement identity.
16. Query execution is read-only.
17. Query does not aggregate Movement facts.
18. Query does not calculate Balance.
19. Query does not access concrete Storage Providers directly.
20. Query semantics do not expand `RegisterFactPersistence` into a generic query repository.
21. Query results depend only on authoritative facts and explicit query inputs.
22. The same facts and query inputs produce the same semantic MovementSet and ordering.

---

## 29. Acceptance Criteria

Step 3 is architecturally complete when:

* Register scope is explicitly defined;
* period semantics are explicitly defined;
* period validity is explicitly defined;
* timezone semantics are explicitly defined;
* `accounting_time=None` semantics are explicitly defined;
* dimension filtering semantics are explicitly defined;
* empty dimension filter semantics are defined;
* deterministic ordering is defined;
* empty result semantics are defined;
* query/persistence boundaries are preserved;
* aggregation remains outside Query;
* balance remains outside Query;
* read-only semantics are explicit;
* failure semantics are compatible with Phase 5 persistence architecture;
* Inventory-specific concepts remain outside the generic Query contract.

The Concrete API Design may now define the Python representation of these semantics without changing the architectural contract.
