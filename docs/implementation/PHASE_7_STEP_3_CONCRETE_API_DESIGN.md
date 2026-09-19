# PHASE 7 — STEP 3 — CONCRETE API DESIGN

## 1. Purpose

This document defines the concrete Python API for the Movement Query contract established by Phase 7 Step 3.

The purpose of this step is to translate the approved semantic Movement Query contract into explicit Python types and interfaces without changing its architectural meaning.

This document defines:

* query period representation;
* dimension-filter representation;
* complete Movement Query representation;
* Movement Query service boundary;
* validation boundaries;
* result representation;
* deterministic ordering;
* public API placement;
* persistence dependency;
* error semantics;
* implementation invariants;
* acceptance criteria.

This document does not define:

* database schemas;
* SQL;
* storage-provider implementations;
* indexes;
* caching;
* pagination;
* aggregation;
* totals maintenance;
* balance calculation;
* reporting;
* optimization strategies.

---

# 2. Architectural Position

Movement Query belongs to the Register semantic layer.

The architecture remains:

```text
Posting
   ↓
MovementSet
   ↓
Logical Consistency Boundary
   ↓
Register Fact Persistence
   ↓
Persisted Movement Facts
   ↓
Movement Query Service
   ├──→ Totals Engine
   └──→ Balance Query
```

The Query Service consumes authoritative persisted `Movement` facts.

It does not become another persistence abstraction.

The dependency boundary is:

```text
Register Query
       │
       ▼
Movement Query Service
       │
       ▼
RegisterFactPersistence
       │
       ▼
Phase 5 Persistence Architecture
       │
       ▼
Storage Provider
```

`RegisterFactPersistence` remains the persistence abstraction.

`MovementQueryService` remains the semantic query abstraction.

---

# 3. Architectural Principles

The concrete API MUST preserve the following principles:

1. Query input is immutable.
2. Query period is explicit.
3. Period semantics are `[start, end)`.
4. A valid period requires `start < end`.
5. Period boundaries must be timezone-aware.
6. Dimension filters are optional in semantic meaning but represented by an explicit immutable filter object.
7. An empty dimension filter means no dimension restriction.
8. Unspecified dimensions are wildcards.
9. Missing requested dimensions are non-matches.
10. Results contain complete `Movement` objects.
11. Query results are immutable from the caller's perspective.
12. Result ordering is deterministic.
13. Query semantics are independent of persistence-provider ordering.
14. Query semantics are independent of insertion order.
15. Query does not calculate totals.
16. Query does not calculate balances.
17. Query does not modify persisted facts.
18. Existing `Movement`, `MovementDimensions`, and `Identifier` types are reused.
19. No second generic persistence architecture is introduced.
20. Provider-specific concepts do not leak into the public query API.

---

# 4. Query Period

## 4.1 Concrete Type

The period is represented by an immutable value object:

```python
@dataclass(frozen=True, slots=True)
class MovementQueryPeriod:
    start: datetime
    end: datetime
```

`MovementQueryPeriod` is a semantic Register Query value object.

---

## 4.2 Construction Invariants

A `MovementQueryPeriod` may exist only in a valid state.

Construction MUST validate:

```text
start < end
```

and:

```text
start is timezone-aware
end is timezone-aware
```

Therefore:

```text
start == end → invalid
start > end  → invalid
naive start  → invalid
naive end    → invalid
```

An empty period is not represented as a valid query.

---

## 4.3 Validation Boundary

Period validation belongs to the value-object construction boundary.

Conceptually:

```text
MovementQueryPeriod(...)
        │
        ├── valid  → MovementQueryPeriod
        │
        └── invalid → MovementQueryValidationError
```

`MovementQueryService.query()` MUST NOT be responsible for discovering an invalid period that was already allowed to exist.

This preserves the value-object invariant:

> A successfully constructed `MovementQueryPeriod` is always semantically valid.

---

## 4.4 Timezone Awareness

Timezone awareness MUST be established semantically.

A datetime is considered suitable for the query period only when it has usable timezone information.

The implementation MUST NOT silently interpret naive datetimes as:

* UTC;
* local time;
* system time;
* storage-provider time.

The query API therefore never introduces an implicit timezone.

---

# 5. Period Semantics

The query period is half-open:

```text
[start, end)
```

A Movement belongs to the period iff:

```text
movement.accounting_time is not None
AND
start <= movement.accounting_time < end
```

Therefore:

```text
accounting_time == start → included
accounting_time == end   → excluded
```

This provides deterministic adjacent-period semantics.

---

# 6. Dimension Filter

## 6.1 Concrete Type

The dimension filter is represented by an immutable value object:

```python
@dataclass(frozen=True, slots=True)
class MovementDimensionFilter:
    values: Mapping[str, MovementScalar]

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, MovementScalar],
    ) -> MovementDimensionFilter:
        ...
```

The public semantic construction path is `from_mapping()`.

The supplied mapping MUST be defensively copied into immutable internal state.

The caller MUST NOT be able to mutate a previously constructed filter by modifying the source mapping.

---

## 6.2 Immutability

The following invariant is mandatory:

```text
MovementDimensionFilter
        ↓
constructed
        ↓
semantic contents cannot change
```

For example:

```python
source = {"product": product_identity}

filter_ = MovementDimensionFilter.from_mapping(source)

source["product"] = another_identity
```

must NOT change the meaning of `filter_`.

The implementation should use the same immutable-mapping strategy already established for Register Movement dimensions where appropriate.

---

# 7. Dimension Matching Semantics

The filter is a partial specification of Movement dimensions.

For every dimension specified by the filter:

```text
query dimension value == movement dimension value
```

must hold.

Dimensions not specified by the filter impose no restriction.

For example:

```python
MovementDimensionFilter.from_mapping(
    {"product": product_identity}
)
```

means:

```text
product == product_identity
```

while all other Movement dimensions remain unrestricted.

---

# 8. Empty Dimension Filter

An empty filter is valid:

```python
MovementDimensionFilter.from_mapping({})
```

Its semantic meaning is:

> Do not restrict the query by dimensions.

It does not mean:

> Match Movements with no dimensions.

This distinction is normative.

---

# 9. Missing Dimensions

If a requested dimension is absent from a Movement, that Movement is a non-match.

For example:

```text
filter:
    product = P1

movement:
    warehouse = W1
    product is absent
```

Result:

```text
non-match
```

Missing dimensions are not interpreted as:

```text
NULL
```

and are not treated as wildcards.

---

# 10. Movement Query

## 10.1 Concrete Type

The complete semantic query is:

```python
@dataclass(frozen=True, slots=True)
class MovementQuery:
    register_identity: Identifier
    period: MovementQueryPeriod
    dimensions: MovementDimensionFilter
```

The object is immutable.

---

## 10.2 Query Inputs

The complete semantic input set is:

```text
Register Identity
+
Period
+
Dimension Filter
```

No implicit semantic inputs participate in the query.

Query results MUST NOT depend on:

* current system time;
* runtime object identity;
* storage provider;
* insertion order;
* database row order;
* filesystem ordering;
* external state;
* previous query execution;
* totals state;
* balance state.

---

# 11. Query Construction

A successfully constructed `MovementQuery` must contain:

1. a valid `Identifier`;
2. a valid `MovementQueryPeriod`;
3. an immutable `MovementDimensionFilter`.

The query object itself does not perform persistence.

The query object does not execute anything.

It is a pure semantic value describing what should be selected.

---

# 12. Movement Query Service

## 12.1 Public Semantic Boundary

The public abstraction is:

```python
class MovementQueryService(Protocol):
    def query(
        self,
        query: MovementQuery,
    ) -> tuple[Movement, ...]:
        """Return persisted movements matching the semantic query."""
```

`MovementQueryService` is the public semantic Protocol.

It is not a concrete implementation class.

---

## 12.2 Concrete Implementations

A concrete implementation may initially be provided as:

```python
class DefaultMovementQueryService:
    def __init__(
        self,
        persistence: RegisterFactPersistence,
    ) -> None:
        self._persistence = persistence

    def query(
        self,
        query: MovementQuery,
    ) -> tuple[Movement, ...]:
        ...
```

The concrete implementation name and module placement are implementation details.

They are not part of the architectural contract.

The architectural contract is the `MovementQueryService` Protocol and its `query()` semantics.

---

# 13. Query Service Responsibilities

`MovementQueryService` is responsible for:

1. receiving a valid semantic query;
2. obtaining authoritative persisted Movement facts;
3. selecting facts belonging to the requested Register;
4. applying `[start, end)` semantics;
5. excluding Movements with `accounting_time=None` from period queries;
6. applying dimension-filter semantics;
7. applying deterministic ordering;
8. returning complete `Movement` objects.

---

# 14. Query Service Non-Responsibilities

The Query Service MUST NOT:

* create Movement facts;
* mutate Movement facts;
* remove Movement facts;
* persist Movement facts;
* post documents;
* unpost documents;
* repost documents;
* calculate totals;
* maintain totals;
* calculate balances;
* maintain balances;
* perform valuation;
* perform accounting aggregation;
* emit posting lifecycle events;
* implement reporting semantics.

---

# 15. Persistence Dependency

The Query Service depends on the existing `RegisterFactPersistence` contract.

The relevant persistence primitive is:

```python
def enumerate(
    self,
    register_identity: Identifier,
) -> tuple[Movement, ...]:
    ...
```

The Query Service may use this primitive to obtain authoritative Register-scoped Movement facts.

The persistence contract MUST NOT be expanded with semantic query operations such as:

```text
find_by_period(...)
find_by_dimensions(...)
search(...)
query(...)
list(...)
```

Those semantics belong to `MovementQueryService`.

---

# 16. Persistence vs Query Boundary

The distinction is normative.

### RegisterFactPersistence

Answers:

> What authoritative Movement facts are persisted for this Register?

Concrete primitive:

```python
enumerate(register_identity)
```

### MovementQueryService

Answers:

> Which persisted Movement facts satisfy this semantic query?

Concrete operation:

```python
query(movement_query)
```

Therefore:

```text
RegisterFactPersistence ≠ MovementQueryService
```

and:

```text
enumerate() ≠ query()
```

---

# 17. Query Execution Semantics

The reference implementation may conceptually execute:

```text
1. Obtain persisted facts for requested Register.
2. Exclude accounting_time=None.
3. Apply [start, end) period filtering.
4. Apply dimension filtering.
5. Order deterministically.
6. Return tuple[Movement, ...].
```

This sequence describes observable semantics.

The implementation may use indexes or another optimized strategy later, provided the observable contract remains identical.

Such optimization is outside Step 3.

---

# 18. Register Scope

Every query targets exactly one Register.

The `register_identity` field is mandatory.

Every returned Movement MUST satisfy:

```python
movement.register_identity == query.register_identity
```

Cross-register queries are outside this API.

---

# 19. Accounting Time

A Movement may legally contain:

```python
accounting_time is None
```

Such a Movement remains a valid persisted Movement fact.

However, it cannot belong to a period query.

Therefore:

```text
accounting_time=None
        ↓
valid persisted Movement
        ↓
excluded from period query
```

The Query Service MUST NOT:

* assign the current time;
* assign storage time;
* assign UTC;
* infer accounting time from document state;
* treat missing accounting time as a persistence error.

---

# 20. Deterministic Ordering

Ordering is normative.

The primary ordering key is:

```text
accounting_time ascending
```

The secondary ordering key is:

```text
Movement identity
```

The identity is the semantic tie-breaker.

The initial concrete implementation may compare the stable string representation of `Identifier`:

```python
(
    movement.accounting_time,
    str(movement.identity),
)
```

Movements with `accounting_time=None` are excluded before ordering.

---

# 21. Result Representation

The result type is:

```python
tuple[Movement, ...]
```

The tuple representation ensures that the returned collection itself does not provide mutation operations.

An empty result is:

```python
()
```

An empty result means:

> The query was valid and no persisted Movement facts matched.

It is not an error.

---

# 22. Complete Movement Preservation

The Query Service returns complete semantic `Movement` objects.

It MUST preserve:

* `identity`;
* `source_document_identity`;
* `register_identity`;
* `movement_type`;
* `dimensions`;
* `resources`;
* `attributes`;
* `accounting_time`.

The Query Service does not create a reduced representation such as:

```text
MovementRow
MovementProjection
MovementResult
MovementRecord
```

for the Step 3 API.

The Query layer selects authoritative facts.

It does not reinterpret them.

---

# 23. Query Immutability

All semantic query inputs are immutable:

```text
MovementQueryPeriod
MovementDimensionFilter
MovementQuery
```

Mutation of source objects after construction MUST NOT alter an already constructed query.

This includes mutation of the mapping originally supplied to `MovementDimensionFilter.from_mapping()`.

---

# 24. Validation Error

The Register Query layer defines:

```python
class MovementQueryValidationError(ValueError):
    """Raised when Movement Query input violates semantic invariants."""
```

This error represents semantic validation failures.

Examples include:

* invalid period;
* naive period boundary;
* invalid query construction input.

---

# 25. Validation Error Boundary

Validation errors are raised at the earliest appropriate semantic boundary.

Therefore:

```text
MovementQueryPeriod(...)
        ↓
invalid temporal semantics
        ↓
MovementQueryValidationError
```

rather than:

```text
MovementQueryService.query(...)
        ↓
discover invalid period
```

Likewise, the dimension filter must be valid and immutable before a query is executed.

This keeps invalid semantic objects from entering the execution layer.

---

# 26. Persistence Error Boundary

Persistence failures remain governed by the existing Phase 5 persistence error architecture.

The Query Service MUST NOT collapse persistence failures into generic:

```text
ValueError
RuntimeError
Exception
```

Provider-specific failures must remain translated through the established persistence boundary.

The following states remain semantically distinct:

```text
valid query + no matches
```

and:

```text
valid query + persistence failure
```

The first returns:

```python
()
```

The second propagates the appropriate persistence failure.

---

# 27. Query vs Totals

Movement Query does not calculate aggregates.

It MUST NOT introduce operations such as:

```python
total_quantity(...)
aggregate(...)
sum(...)
```

Totals are owned by the Totals Engine.

The conceptual relationship is:

```text
Movement Query
      ↓
Movement facts

Totals Engine
      ↓
Derived aggregate state
```

Query may provide authoritative Movement facts to Totals-related maintenance or validation workflows, but this does not transfer ownership of totals semantics to Query.

---

# 28. Query vs Balance

Movement Query does not calculate balances.

Balance semantics belong to the Balance Query layer.

The conceptual relationship is:

```text
MovementQueryService
        ↓
Movement facts

Balance Query
        ↓
Balance result
```

This keeps generic Movement selection independent from register-specific balance semantics.

---

# 29. Public API Placement

The query API belongs to the Register domain layer.

Conceptually:

```text
accore.platform.registers
    └── Movement Query API
```

The exact physical module split is an implementation concern.

The architecture requires only that:

```text
Movement Query API
        ↓
Register layer
```

and:

```text
RegisterFactPersistence
        ↓
Persistence layer
```

The Query API MUST NOT become part of the generic persistence API.

---

# 30. Public Symbols

The concrete public API consists of:

```python
MovementQueryPeriod
MovementDimensionFilter
MovementQuery
MovementQueryService
MovementQueryValidationError
```

Existing symbols reused by the API include:

```python
Identifier
Movement
MovementDimensions
RegisterFactPersistence
```

No duplicate representation of these concepts is introduced.

---

# 31. Example

A concrete semantic query:

```python
query = MovementQuery(
    register_identity=inventory_register_identity,
    period=MovementQueryPeriod(
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 2, 1, tzinfo=UTC),
    ),
    dimensions=MovementDimensionFilter.from_mapping(
        {
            "product": product_identity,
            "warehouse": warehouse_identity,
        }
    ),
)

movements = movement_query_service.query(query)
```

The result is:

```python
tuple[Movement, ...]
```

ordered by:

```text
accounting_time ASC
Movement identity ASC
```

and contains only Movements satisfying:

```text
register_identity == inventory_register_identity
AND
start <= accounting_time < end
AND
product == product_identity
AND
warehouse == warehouse_identity
```

---

# 32. Determinism Invariant

For identical:

```text
persisted Movement facts
+
MovementQuery
```

the Query Service MUST produce the same:

```text
Movement set
+
ordering
```

independent of:

* persistence provider;
* physical storage layout;
* insertion order;
* persistence enumeration order;
* runtime object identity;
* current system time;
* external state.

Determinism is a semantic requirement.

It is not merely an implementation optimization.

---

# 33. Provider Independence

The public Query API MUST NOT expose:

* SQL;
* database connections;
* tables;
* rows;
* filesystem paths;
* file offsets;
* database cursors;
* provider-specific filters;
* provider-specific ordering primitives;
* storage-specific query objects.

The API operates exclusively on Register and Movement semantics.

---

# 34. API Stability Boundary

The following are architectural API:

```text
MovementQueryPeriod
MovementDimensionFilter
MovementQuery
MovementQueryService.query()
MovementQueryValidationError
```

The following are implementation details:

```text
concrete Query Service class name
module/file decomposition
iteration strategy
filtering algorithm
sorting implementation
database/index usage
storage traversal
caching
```

Implementation changes to these details MUST NOT alter the semantic API.

---

# 35. Initial Test Contract

The implementation MUST support tests for at least the following.

## Period

* valid `[start, end)` period;
* `start == end` rejected;
* `start > end` rejected;
* naive start rejected;
* naive end rejected;
* start boundary included;
* end boundary excluded.

## Dimension Filter

* empty filter matches all dimensions;
* partial filter matches;
* multiple dimensions match;
* mismatched dimension does not match;
* missing requested dimension does not match;
* unspecified Movement dimensions remain unrestricted;
* source mapping mutation does not alter an existing filter.

## Register

* only requested Register is returned;
* Movements belonging to another Register are excluded.

## Accounting Time

* `accounting_time=None` is excluded;
* timestamp inside period is included;
* timestamp before period is excluded;
* timestamp at period end is excluded.

## Ordering

* ascending accounting time;
* deterministic identity tie-breaker;
* insertion order does not affect result order.

## Results

* result type is `tuple[Movement, ...]`;
* empty result is `()`;
* complete Movement fields are preserved.

## Determinism

Repeated execution against identical persisted facts and identical query input produces identical results.

## Read-only Behavior

Query execution does not modify persisted Movement facts.

## Error Boundary

Persistence failures remain distinguishable from valid empty results.

---

# 36. Acceptance Criteria

Step 3 Concrete API Design is accepted when:

1. A concrete immutable `MovementQueryPeriod` exists.
2. Period construction requires `start < end`.
3. Period construction requires timezone-aware boundaries.
4. `[start, end)` semantics are explicit.
5. Invalid periods fail at the value-object construction boundary.
6. A concrete immutable `MovementDimensionFilter` exists.
7. The filter defensively copies caller-provided mappings.
8. Empty dimension filter means no dimension restriction.
9. Missing requested dimensions are non-matches.
10. A concrete immutable `MovementQuery` exists.
11. Register identity is mandatory.
12. A public `MovementQueryService` Protocol exists.
13. Concrete service implementations remain implementation details.
14. Query results are `tuple[Movement, ...]`.
15. Query returns complete Movement facts.
16. Query ordering is deterministic.
17. `accounting_time=None` is excluded from period queries without invalidating the Movement.
18. Query validation failures are distinct from persistence failures.
19. Query does not become a generic persistence API.
20. Query does not introduce aggregation semantics.
21. Query does not introduce balance semantics.
22. Query does not expose provider-specific concepts.
23. Existing `Movement`, `Identifier`, and `RegisterFactPersistence` abstractions are reused.
24. Query semantics remain unchanged from the approved Step 3 Contract.
25. The API is suitable for a storage-provider-independent implementation.

---

# 37. Final API Target

The intended public shape is:

```python
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.registers import Movement
from accore.platform.registers.movement import MovementScalar


@dataclass(frozen=True, slots=True)
class MovementQueryPeriod:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class MovementDimensionFilter:
    values: Mapping[str, MovementScalar]

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, MovementScalar],
    ) -> "MovementDimensionFilter":
        ...


@dataclass(frozen=True, slots=True)
class MovementQuery:
    register_identity: Identifier
    period: MovementQueryPeriod
    dimensions: MovementDimensionFilter


class MovementQueryService(Protocol):
    def query(
        self,
        query: MovementQuery,
    ) -> tuple[Movement, ...]:
        ...


class MovementQueryValidationError(ValueError):
    ...
```

The exact imports and module locations must follow the existing repository structure.

The semantic API above is the architectural target.

---

# 38. Final Architectural Statement

Phase 7 Step 3 Concrete API Design establishes a strict separation between:

```text
semantic query input
        ↓
MovementQuery
        ↓
MovementQueryService
        ↓
authoritative Movement facts
        ↓
deterministically ordered result
```

while preserving the existing boundary:

```text
MovementQueryService
        ↓
RegisterFactPersistence
        ↓
Phase 5 Persistence Architecture
```

The API does not introduce a second persistence model, a second Movement representation, aggregate semantics, balance semantics, or storage-provider semantics.

The Concrete API is therefore considered architecturally complete and ready for implementation.
