# PHASE 7 — STEP 5 — CONCRETE API DESIGN

## 1. Document Status

**Phase:** 7 — Register Implementation
**Step:** 5 — Concrete API Design
**Status:** Draft
**Previous Document:** `PHASE_7_STEP_5_BALANCE_QUERY_CONTRACT.md`
**Previous Step:** Step 4 — Totals Engine Contract
**Next Step:** Step 5 Implementation

---

# 2. Objective

This document defines the concrete Python API for the Phase 7 Balance Query boundary.

The purpose of this document is to translate the semantic Balance Query contract into explicit Python-level types, protocols, services, validation rules, and public exports.

The design must preserve all architectural decisions established by:

* Phase 5 Persistence Architecture;
* Phase 6 Posting Architecture;
* Phase 7 Step 2 — Register Storage Contract;
* Phase 7 Step 3 — Movement Query Contract;
* Phase 7 Step 4 — Totals Engine Contract;
* Phase 7 Step 5 — Balance Query Contract.

This document does not define implementation details of concrete storage providers or the final Totals persistence mechanism.

---

# 3. Architectural Principle

The concrete API must preserve the following dependency direction:

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
```

Balance Query is a **read boundary over current Totals**.

It is not:

* a Movement query;
* a Movement aggregation engine;
* a Totals rebuild mechanism;
* a storage repository;
* a posting operation;
* a second persistence architecture.

---

# 4. Core Design Decision

The public Balance Query API is defined around two concepts:

```text
BalanceQuery
BalanceResult
```

with a semantic service boundary:

```text
BalanceQueryService
```

Conceptually:

```python
result = balance_query_service.query(query)
```

where:

```text
BalanceQuery
    ↓
one Register
    +
one concrete aggregation scope
    ↓
one current Total
    ↓
BalanceResult
```

---

# 5. Concrete API Overview

The proposed public API consists of:

```python
class BalanceQuery:
    register_identity: Identifier
    aggregation_scope: TotalsKey
```

```python
@dataclass(frozen=True, slots=True)
class BalanceResult:
    register_identity: Identifier
    aggregation_scope: TotalsKey
    value: object
```

```python
class BalanceQueryService(Protocol):
    def query(self, query: BalanceQuery) -> BalanceResult:
        ...
```

The exact type of `value` must be determined by the Register/Totals abstraction and must not be weakened to arbitrary `Any`.

For the generic Register API, the value type may remain a semantic scalar type.

For Inventory:

```text
value: Decimal
```

---

# 6. Balance Query

## 6.1 Purpose

`BalanceQuery` represents one semantic request for the current aggregate state of one Register aggregation scope.

The query must be immutable.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class BalanceQuery:
    register_identity: Identifier
    aggregation_scope: TotalsKey
```

---

## 6.2 Register Identity

`register_identity` identifies exactly one Register.

It must use the existing platform:

```python
Identifier
```

type.

The Balance API must not introduce a second identity abstraction.

---

## 6.3 Aggregation Scope

`aggregation_scope` identifies exactly one concrete Register-defined aggregation scope.

The preferred abstraction is:

```python
TotalsKey
```

from the Totals Engine contract.

The Balance Query must not accept an arbitrary mapping of dimensions as its primary API.

This prevents ambiguity between:

```text
specific aggregation scope
```

and:

```text
partial selection filter
```

which already belongs to Movement Query.

---

# 7. Why Balance Uses TotalsKey

Movement Query supports partial dimension filtering:

```text
Product = P
Warehouse = unspecified
```

Balance Query does not.

Balance Query requests a specific aggregate state.

Therefore:

```text
Movement Query
    → selection criteria

Balance Query
    → concrete aggregation key
```

This is a deliberate distinction.

For Inventory:

```python
TotalsKey(
    product=P1,
    warehouse=W1,
)
```

identifies one Balance.

The following is not a Phase 7 Balance Query:

```python
{
    "product": P1
}
```

because it could represent multiple warehouse totals.

---

# 8. TotalsKey Dependency

`TotalsKey` is conceptually owned by the Totals Engine contract.

Balance Query consumes it.

Balance Query must not redefine:

* aggregation dimensions;
* dimension ordering;
* aggregation semantics;
* resource semantics.

The dependency is:

```text
Register Configuration
        ↓
TotalsKey semantics
        ↓
Balance Query
```

not:

```text
Balance Query
        ↓
defines its own aggregation model
```

---

# 9. BalanceResult

## 9.1 Purpose

`BalanceResult` is the semantic result returned by Balance Query.

It must be immutable.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class BalanceResult:
    register_identity: Identifier
    aggregation_scope: TotalsKey
    value: BalanceValue
```

---

# 10. TotalsKey Dependency

`TotalsKey` and `TotalValue` are owned by the Step 4 Totals Engine API.

The Balance Query API consumes these types as an already-defined semantic boundary. It does not redefine their aggregation semantics and does not introduce competing Balance-specific equivalents.

The dependency is:

```text
Step 4 — Totals Engine
    │
    ├── TotalsKey
    ├── TotalValue
    └── Totals read boundary
             │
             ▼
Step 5 — Balance Query
```

Balance Query must not redefine:

* aggregation dimensions;
* dimension ordering;
* aggregation semantics;
* resource semantics;
* total value semantics.

The Balance API consumes the Totals abstraction rather than defining its own aggregation model.

Therefore:

```text
Totals Engine
    ↓
defines aggregation semantics

Balance Query
    ↓
requests one already-defined aggregate
```

For Phase 7 Inventory:

```text
TotalsKey
    = Product + Warehouse

TotalValue
    = Decimal Quantity
```

The concrete Python representation of these types belongs to the Step 4 Totals API and must be imported by the Balance implementation rather than duplicated in `balance.py`.


---

# 11. Inventory Balance Result

For the Inventory Register, the semantic result is:

```python
@dataclass(frozen=True, slots=True)
class BalanceResult:
    register_identity: Identifier
    aggregation_scope: TotalsKey
    value: Decimal
```

Example:

```text
Register:
    Inventory

Scope:
    Product = P1
    Warehouse = W1

Value:
    Decimal("125")
```

---

# 12. Zero Balance Representation

A missing applicable Total is represented as a valid zero Balance **when the Register's aggregate semantics define an empty scope as zero**.

For Inventory:

```python
Decimal("0")
```

is the semantic zero.

The Balance API must not return:

```python
None
```

to represent ordinary zero state.

`None` must not be used as an implicit synonym for zero.

---

# 13. Empty Scope vs Zero

The concrete API intentionally does not expose whether zero resulted from:

```text
no applicable Movement facts
```

or:

```text
applicable Movement facts netted to zero
```

Both produce:

```python
BalanceResult.value == Decimal("0")
```

if the Register defines zero as the empty aggregate.

Movement Query is responsible for fact-history inspection.

---

# 14. Missing Register

A query for an unknown Register must fail explicitly.

The Balance API must not:

* create a Register;
* return zero;
* infer a Register;
* fall back to another Register.

The exact error type should reuse the existing Register semantic error vocabulary where one exists.

If no suitable error exists, a dedicated Balance Query error may be introduced.

---

# 15. Invalid Aggregation Scope

An aggregation scope that is not valid for the specified Register must fail explicitly.

Examples:

```text
Inventory + unsupported dimension
Inventory + missing Product
Inventory + missing Warehouse
Inventory + incompatible key representation
```

The API must not silently:

* ignore unsupported fields;
* drop missing required dimensions;
* construct a partial aggregate;
* aggregate multiple scopes.

---

# 16. BalanceQueryValidationError

Input validation failures should have a dedicated semantic error boundary.

Proposed type:

```python
class BalanceQueryValidationError(ValueError):
    """Raised when a Balance Query violates semantic input invariants."""
```

This error is appropriate for failures such as:

* invalid query object construction;
* missing required scope information;
* invalid aggregation key structure;
* invalid Register/scope combination when validation is local and deterministic.

Runtime state failures should not be collapsed into this exception.

---

# 17. BalanceQueryError

The API should have a semantic root error for Balance Query failures if the existing architecture does not already provide a suitable Register-level root error.

Conceptually:

```python
class BalanceQueryError(Exception):
    """Base class for Balance Query failures."""
```

Potential hierarchy:

```text
BalanceQueryError
├── BalanceQueryValidationError
├── BalanceQueryRegisterNotFoundError
├── BalanceQueryScopeError
└── BalanceQueryConsistencyError
```

The final hierarchy should be kept minimal.

A new error type should be introduced only when the existing platform error vocabulary cannot represent the semantic failure cleanly.

---

# 18. Query Service Protocol

The public semantic boundary is:

```python
class BalanceQueryService(Protocol):
    def query(self, query: BalanceQuery) -> BalanceResult:
        """Return the current Balance for one concrete aggregation scope."""
```

The Protocol is the architectural abstraction.

Consumers depend on:

```python
BalanceQueryService
```

rather than a concrete implementation.

---

# 19. Default Implementation

A reference implementation may be named:

```python
DefaultBalanceQueryService
```

Conceptually:

```python
class DefaultBalanceQueryService:
    def __init__(
        self,
        totals: TotalsReader,
    ) -> None:
        self._totals = totals

    def query(
        self,
        query: BalanceQuery,
    ) -> BalanceResult:
        ...
```

The exact Totals dependency is intentionally defined by the Step 4 Totals Engine concrete API.

The Balance Query implementation must depend on a **Totals read boundary**, not on Movement persistence.

---

# 20. Totals Read Boundary

Balance Query needs a read operation over current Totals.

The preferred abstraction is a narrow semantic interface.

Conceptually:

```python
class TotalsReader(Protocol):
    def get(
        self,
        register_identity: Identifier,
        key: TotalsKey,
    ) -> TotalValue:
        ...
```

The exact method name may be adjusted to the finalized Totals API.

The important architectural rule is:

```text
Balance Query
      ↓
Totals Reader
```

not:

```text
Balance Query
      ↓
Movement Persistence
```

---

# 21. No Movement Persistence Dependency

`DefaultBalanceQueryService` must not require:

```python
RegisterFactPersistence
```

as a direct dependency.

The service must not enumerate Movement facts in order to calculate Balance.

This prevents Balance Query from becoming a second Totals Engine.

---

# 22. No Rebuild Dependency

`DefaultBalanceQueryService` must not depend on:

```python
TotalsRebuilder
```

or equivalent maintenance API.

Rebuild is an explicit maintenance operation.

A normal read must remain:

```text
Totals
   ↓
Balance
```

---

# 23. One TotalsKey Rule

The service must resolve exactly one TotalsKey.

Conceptually:

```python
total = totals.get(
    query.register_identity,
    query.aggregation_scope,
)
```

It must not perform:

```python
sum(
    totals.get(key)
    for key in matching_keys
)
```

because that would introduce multi-key aggregation semantics into Balance Query.

---

# 24. Current Total Semantics

The Totals Reader must return the currently established aggregate state.

Balance Query must not interpret timestamps to determine currentness.

It must not perform:

```python
max(movement.accounting_time)
```

or equivalent logic.

Currentness is a property of the maintained Totals state.

---

# 25. Visibility Semantics

Balance Query may only observe the state made visible by the Totals consistency boundary.

The implementation must not expose:

* intermediate Movement state;
* partially applied Totals;
* partially removed Totals;
* partially reposted state.

The exact transaction/atomicity mechanism belongs below the Balance Query boundary.

---

# 26. BalanceResult Immutability

`BalanceResult` must be immutable.

Preferred representation:

```python
@dataclass(frozen=True, slots=True)
class BalanceResult:
    ...
```

The aggregation scope must also be immutable.

The returned result must not expose a mutable internal Totals object.

---

# 27. Scope Immutability

`TotalsKey` must itself satisfy the immutability contract defined by the Totals Engine.

Balance Query must not mutate it.

If TotalsKey contains mappings or collections, they must not be exposed as mutable internal state.

---

# 28. Resource Type Preservation

Balance Query must preserve the resource type defined by the Register.

For Inventory:

```text
Decimal → Decimal
```

It must not silently convert:

```text
Decimal → float
Decimal → int
Decimal → str
```

or another representation.

This is particularly important for accounting quantities.

---

# 29. Negative Values

Balance Query must return negative totals if the underlying Register permits them.

It must not perform:

```python
max(value, Decimal("0"))
```

or equivalent normalization.

Business validation belongs elsewhere.

---

# 30. Determinism

For identical:

```text
Register state
+
TotalsKey
```

the result must be semantically identical.

The implementation must not depend on:

* current time;
* iteration order;
* object identity;
* storage layout;
* provider-specific behavior;
* unrelated external state.

---

# 31. Public API Surface

The intended public exports from:

```text
src/accore/platform/registers/
```

are:

```python
BalanceQuery
BalanceResult
BalanceQueryService
DefaultBalanceQueryService
BalanceQueryError
BalanceQueryValidationError
```

Additional error types should only be exported if they become part of the stable semantic API.

`TotalsKey` remains owned/exported by the Totals Engine boundary.

---

# 32. Proposed Module Structure

The preferred initial module is:

```text
src/accore/platform/registers/balance.py
```

with tests:

```text
tests/unit/registers/test_balance.py
```

The module should contain:

```text
BalanceQuery
BalanceResult
BalanceQueryService
DefaultBalanceQueryService
Balance Query errors
```

Totals-specific types remain in the Totals module rather than being duplicated in `balance.py`.

---

# 33. Dependency Direction

The intended module dependency is:

```text
register.balance
      ↓
register.totals
      ↓
register.movement
```

and:

```text
register.balance
      ↓
foundation.Identifier
```

The Balance module must not depend directly on:

```text
storage provider
filesystem
database
```

or on concrete persistence implementations.

---

# 34. Dependency on Phase 5 Persistence

Balance Query depends indirectly on Phase 5 Persistence through the Totals subsystem.

The dependency chain is:

```text
Balance Query
      ↓
Totals Reader
      ↓
Totals Maintenance / Persistence
      ↓
Phase 5 Persistence Architecture
      ↓
Storage Provider
```

Balance Query must not bypass the Totals boundary to access generic persistence.

---

# 35. Separation from Movement Query

The APIs must remain distinct.

Movement Query:

```python
MovementQuery(
    register_identity=...,
    period=...,
    dimensions=...,
)
```

Balance Query:

```python
BalanceQuery(
    register_identity=...,
    aggregation_scope=...,
)
```

Movement Query supports selection.

Balance Query resolves one aggregate state.

No shared generic query object should be introduced merely to reduce the number of classes.

---

# 36. Validation Responsibilities

`BalanceQuery` itself should validate only structural invariants that can be checked locally.

Examples:

* Register identity is present;
* aggregation scope is present;
* aggregation scope is structurally valid.

Register-specific semantic validation belongs to the Register/Totals layer where the necessary metadata is available.

This avoids duplicating Register configuration rules inside the generic Balance API.

---

# 37. Result Validation

`BalanceResult` should not duplicate all Totals validation.

The result represents a value already established by the Totals subsystem.

It should enforce only invariants necessary for safe representation.

Examples:

* Register identity exists;
* aggregation scope exists;
* value is not an invalid sentinel;
* value is compatible with the semantic resource contract.

Exact value validation belongs primarily to the Totals layer.

---

# 38. No Optional Value for Ordinary Zero

The API must not use:

```python
BalanceResult | None
```

to represent an ordinary empty/zero aggregate.

For Inventory:

```python
BalanceResult(
    ...,
    value=Decimal("0"),
)
```

is the correct representation.

`None` should only appear if a future Register contract explicitly defines absence as semantically distinct from zero.

That is not the Phase 7 Inventory model.

---

# 39. Error vs Zero

The implementation must distinguish:

```text
valid zero
```

from:

```text
failure to obtain Balance
```

Therefore:

```text
No applicable aggregate
        ↓
Decimal("0")
```

when permitted by Register semantics.

But:

```text
Totals subsystem unavailable
        ↓
error
```

must not become:

```text
Decimal("0")
```

---

# 40. Error Propagation

The Balance Query boundary must preserve semantic failures.

For example:

```text
Storage Provider Failure
        ↓
Persistence Error
        ↓
Totals Error
        ↓
Balance Query Error
```

Provider-specific exceptions must not leak through the public Balance API.

At the same time, the Balance layer must not erase meaningful semantic errors by converting them to generic `Exception`.

---

# 41. No Hidden Mutation

Calling:

```python
balance_service.query(query)
```

must not:

* create Totals;
* update Totals;
* repair Totals;
* rebuild Totals;
* persist Movement;
* delete Movement.

A query must remain a read operation.

---

# 42. Example — Inventory

Assume:

```text
Register = Inventory

Product = P1
Warehouse = W1
```

and the current Total is:

```text
Quantity = Decimal("125")
```

Query:

```python
query = BalanceQuery(
    register_identity=inventory_register_id,
    aggregation_scope=TotalsKey(
        product=product_id,
        warehouse=warehouse_id,
    ),
)
```

Result:

```python
BalanceResult(
    register_identity=inventory_register_id,
    aggregation_scope=query.aggregation_scope,
    value=Decimal("125"),
)
```

---

# 43. Example — Zero Inventory

No applicable Movement facts exist for:

```text
Product = P2
Warehouse = W1
```

Inventory semantics define an empty aggregate as zero.

Result:

```python
BalanceResult(
    register_identity=inventory_register_id,
    aggregation_scope=scope,
    value=Decimal("0"),
)
```

No special `None` state is required.

---

# 44. Example — Negative Inventory

Suppose:

```text
INCOME  = 10
EXPENSE = 15
```

Then:

```text
Balance = -5
```

The Balance API returns:

```python
Decimal("-5")
```

if the Inventory Register permits this state.

Balance Query does not normalize or reject it.

---

# 45. Example — No Implicit Aggregation

Suppose:

```text
Product P1
Warehouse W1 → 10
Warehouse W2 → 20
```

The query:

```text
Product = P1
```

alone is not a valid Phase 7 Balance Query.

The API requires:

```text
Product + Warehouse
```

so that one concrete TotalsKey is selected.

A future aggregate:

```text
Product P1 across all warehouses
```

requires a separate aggregation contract.

---

# 46. Example — Movement Query Remains Separate

To inspect all movements for:

```text
Product = P1
```

across multiple warehouses, the caller uses Movement Query.

That query may use:

```text
dimensions:
    Product = P1
```

with Warehouse unspecified.

This does not imply that Balance Query accepts the same partial filter.

---

# 47. Example — Rebuild

Before rebuild:

```text
Totals(P1, W1) = 100
Balance(P1, W1) = 100
```

Maintenance performs:

```text
Persisted Movements
        ↓
Totals Rebuild
        ↓
Totals(P1, W1) = 100
```

After rebuild:

```text
Balance(P1, W1) = 100
```

The Balance API itself did not perform the rebuild.

---

# 48. Test Boundary

The concrete API requires tests at three levels.

## 48.1 Unit Tests

Test:

* immutable BalanceQuery;
* immutable BalanceResult;
* Register identity preservation;
* aggregation scope preservation;
* zero handling;
* negative value handling;
* validation;
* Totals Reader interaction;
* no Movement persistence interaction;
* no rebuild interaction.

---

## 48.2 Contract Tests

The Balance Query implementation should be tested against a fake/in-memory Totals Reader.

The contract must verify:

```text
one query
    ↓
one TotalsKey
    ↓
one Total
    ↓
one BalanceResult
```

---

## 48.3 Integration Tests

Later integration tests must verify:

```text
Goods Receipt
    ↓
Posting
    ↓
Movement
    ↓
Totals
    ↓
Balance Query
```

For Inventory:

```text
Goods Receipt quantity = 10
        ↓
Inventory Balance = 10
```

---

# 49. Negative Test Cases

The implementation must test at least:

1. Unknown Register.
2. Invalid aggregation scope.
3. Missing required Inventory Product.
4. Missing required Inventory Warehouse.
5. Unsupported dimension.
6. Totals read failure.
7. Totals consistency failure.
8. Provider failure translated below the Balance boundary.
9. Invalid query construction.
10. Attempted partial scope.
11. Attempted multi-key aggregation.
12. Attempted implicit rebuild.
13. Negative result.
14. Zero result.
15. No applicable facts resulting in zero.

---

# 50. Immutability Tests

Tests must verify that:

```python
BalanceQuery
```

cannot be mutated after creation.

Likewise:

```python
BalanceResult
```

cannot be mutated.

The underlying aggregation scope must not expose mutable state.

---

# 51. Interaction Test

The default service should be tested with a fake Totals Reader.

Example conceptual interaction:

```text
query(...)
    ↓
totals.get(register_id, totals_key)
    ↓
one call
    ↓
BalanceResult
```

The test must verify that no additional calls are made to:

* Movement persistence;
* Totals rebuild;
* unrelated Totals keys.

---

# 52. Architectural Test

A dedicated architecture test should ensure that the Balance module does not import concrete storage implementations.

Forbidden dependencies include direct imports of:

```text
FilesystemStorageProvider
InMemoryStorageProvider
database implementation
filesystem implementation
```

Balance depends on semantic interfaces only.

---

# 53. Public API Test

A public API test should verify that the intended types are importable from:

```python
accore.platform.registers
```

For example:

```python
from accore.platform.registers import (
    BalanceQuery,
    BalanceResult,
    BalanceQueryService,
    DefaultBalanceQueryService,
)
```

Only intentionally public symbols should be exported.

---

# 54. Type Checking Requirements

The implementation must satisfy:

```text
mypy src/accore/platform/registers
```

without introducing:

* `Any`;
* unchecked casts;
* untyped public methods;
* weak generic typing solely for convenience.

The value type should remain as precise as the Totals abstraction permits.

---

# 55. Formatting and Linting Requirements

The implementation must satisfy:

```text
ruff check
black --check
```

for the affected source and test files.

No formatting exception should be introduced for the Balance module.

---

# 56. No Generic Repository

The Concrete Balance API must not introduce:

```python
BalanceRepository
```

as a generic CRUD repository.

Balance is a semantic read operation.

It does not require:

```text
create
update
delete
list
search
```

operations.

---

# 57. No Generic Aggregate Query

The API must not introduce an abstraction such as:

```python
AggregateQuery(
    filters=...
)
```

for the purpose of making Balance and Movement Query share infrastructure.

The two operations have different semantics.

---

# 58. No Generic Dimension Filter Reuse

`MovementDimensionFilter` must not automatically become the Balance input type.

Movement Query requires partial filtering.

Balance Query requires one complete concrete aggregation scope.

The API should make this distinction visible in the type system.

---

# 59. No Register-Specific Logic in Generic Query

The generic Balance Query layer must not contain hard-coded logic such as:

```python
if register == INVENTORY:
    ...
```

Inventory-specific semantics belong to the Inventory Register configuration / Totals implementation.

The generic Balance service consumes the Register-defined Totals contract.

---

# 60. Inventory-Specific API

If the generic TotalsKey abstraction is not sufficiently expressive for static typing of Inventory, a Register-specific constructor/helper may be introduced.

For example:

```python
InventoryTotalsKey(
    product=product_id,
    warehouse=warehouse_id,
)
```

However, such a type should only be introduced if required by the concrete Totals design.

The default preference is to keep the generic Balance API small:

```text
BalanceQuery
    +
TotalsKey
```

---

# 61. Ownership of Types

The intended ownership is:

| Type                         | Owner             |
| ---------------------------- | ----------------- |
| `Identifier`                 | Foundation        |
| `Movement`                   | Register Movement |
| `MovementQuery`              | Movement Query    |
| `TotalsKey`                  | Totals            |
| `BalanceQuery`               | Balance Query     |
| `BalanceResult`              | Balance Query     |
| `BalanceQueryService`        | Balance Query     |
| `DefaultBalanceQueryService` | Balance Query     |

No type should be duplicated merely to avoid imports.

---

# 62. Module Boundary

Preferred structure:

```text
src/accore/platform/registers/
    __init__.py
    movement.py
    query.py
    totals.py
    balance.py
```

The exact Totals module name may follow the implementation resulting from Step 4.

The important boundary is semantic ownership, not filename preference.

---

# 63. Dependency Graph

The desired dependency graph is:

```text
foundation.Identifier
        ↑
        │
register.movement
        ↑
        │
register.totals
        ↑
        │
register.balance
```

Movement Query may independently depend on Movement and Persistence abstractions.

Balance Query should not depend on Movement Query.

---

# 64. Concrete Service Algorithm

The reference implementation algorithm is intentionally minimal:

```text
1. Receive BalanceQuery.
2. Validate query structure.
3. Resolve/validate Register aggregation semantics through Totals boundary.
4. Request one Total using Register Identity + one TotalsKey.
5. Receive current aggregate value.
6. Construct immutable BalanceResult.
7. Return result.
```

There must be no hidden:

```text
enumerate movements
filter movements
sum movements
rebuild totals
persist state
```

inside this algorithm.

---

# 65. Complexity

The intended Balance Query complexity depends on the Totals storage implementation.

The Balance layer itself should perform:

```text
O(1)
```

semantic operations with respect to the number of Movement facts.

It must not scale with total Movement count merely to answer one current Balance query.

The Totals implementation determines the actual storage lookup complexity.

---

# 66. Consistency Requirement

A Balance Query must observe a logically consistent Totals state.

The API does not itself establish transactional guarantees.

Those guarantees belong to the logical consistency boundary around:

```text
Movement Persistence
+
Totals Maintenance
```

Balance Query consumes the resulting state.

---

# 67. Reposting Semantics

Balance Query does not distinguish:

* original posting;
* unposting;
* reposting.

It exposes only the current resulting aggregate.

For example:

```text
Old MovementSet
    ↓
Unpost
    ↓
New MovementSet
    ↓
Totals
    ↓
Balance
```

The Balance API sees the resulting current state.

Movement Query remains available when accounting history is required.

---

# 68. Event Semantics

Balance Query does not emit:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

events.

Events belong to the posting lifecycle.

Balance Query is a read operation.

---

# 69. API Stability Rule

Once implemented and accepted, the following are considered stable semantic properties:

* one Register per query;
* one concrete aggregation scope;
* one TotalsKey;
* current-state semantics;
* Totals as source;
* no Movement reaggregation;
* no implicit rebuild;
* immutable result;
* deterministic behavior;
* provider independence.

Future API changes must not silently weaken these guarantees.

---

# 70. Acceptance Criteria

The Concrete API Design is accepted when:

### API-AC-01

`BalanceQuery` represents exactly one Register.

### API-AC-02

`BalanceQuery` represents exactly one concrete aggregation scope.

### API-AC-03

The aggregation scope is represented by `TotalsKey` or an explicitly compatible Totals-owned abstraction.

### API-AC-04

Partial dimension filters are not accepted as Balance scope.

### API-AC-05

`BalanceResult` contains Register identity.

### API-AC-06

`BalanceResult` contains the requested aggregation scope.

### API-AC-07

`BalanceResult` contains the current aggregate value.

### API-AC-08

`BalanceQueryService` is the public semantic boundary.

### API-AC-09

The default implementation depends on a Totals read boundary.

### API-AC-10

The default implementation does not directly depend on Movement persistence.

### API-AC-11

The default implementation does not depend on Totals rebuild.

### API-AC-12

One query resolves one TotalsKey.

### API-AC-13

The service does not aggregate multiple TotalsKey values.

### API-AC-14

Zero is represented as a valid aggregate value.

### API-AC-15

Zero is not represented by `None`.

### API-AC-16

Negative values are preserved.

### API-AC-17

Resource types are preserved.

### API-AC-18

Balance results are immutable.

### API-AC-19

Balance queries are immutable.

### API-AC-20

Invalid queries fail explicitly.

### API-AC-21

Totals failures are not converted to zero.

### API-AC-22

Provider failures do not leak through the public Balance API.

### API-AC-23

The API is provider-independent.

### API-AC-24

The API introduces no second persistence architecture.

### API-AC-25

Public exports are explicit and minimal.

### API-AC-26

The implementation can satisfy strict static typing.

### API-AC-27

The API can be tested independently using a fake Totals Reader.

### API-AC-28

Inventory can expose Product + Warehouse → Decimal Quantity through the generic Balance boundary.

---

# 71. Implementation Boundary

The next implementation step must implement only the API defined here.

The implementation must not simultaneously introduce:

* reporting;
* historical Balance;
* as-of queries;
* period Balance;
* cross-register aggregation;
* multi-key aggregation;
* valuation;
* costing;
* general ledger;
* distributed storage;
* asynchronous query infrastructure.

Such additions would expand the Phase 7 scope without architectural approval.

---

# 72. Open Design Dependency

One dependency must be resolved against the finalized Step 4 Totals Concrete API:

```text
Exact Totals Reader interface
Exact TotalsKey representation
Exact TotalValue representation
```

Balance Query should consume those types rather than create competing equivalents.

This is an implementation dependency, not a reason to change the Balance semantic contract.

---

# 73. Recommended Initial Concrete API

Subject to final alignment with the Step 4 Totals concrete API, the intended shape is:

```python
from dataclasses import dataclass

from accore.platform.foundation import Identifier
from accore.platform.registers.totals import TotalsKey, TotalValue


@dataclass(frozen=True, slots=True)
class BalanceQuery:
    register_identity: Identifier
    aggregation_scope: TotalsKey


@dataclass(frozen=True, slots=True)
class BalanceResult:
    register_identity: Identifier
    aggregation_scope: TotalsKey
    value: TotalValue


class BalanceQueryService(Protocol):
    def query(self, query: BalanceQuery) -> BalanceResult:
        ...


class DefaultBalanceQueryService:
    def __init__(self, totals: TotalsReader) -> None:
        self._totals = totals

    def query(self, query: BalanceQuery) -> BalanceResult:
        value = self._totals.get(
            query.register_identity,
            query.aggregation_scope,
        )

        return BalanceResult(
            register_identity=query.register_identity,
            aggregation_scope=query.aggregation_scope,
            value=value,
        )
```

This is the target shape, not yet the implementation.

---

# 74. Dependency on Step 4

The Balance Query API has a direct semantic dependency on the Step 4 Totals Engine API.

The following types and boundary are owned by Step 4:

```text
TotalsKey
TotalValue
Totals read boundary
```

Step 5 consumes these definitions without redefining them.

The dependency is therefore resolved at the architectural level:

```text
Step 4 — Totals Engine
        │
        ├── TotalsKey
        ├── TotalValue
        └── Totals read API
                │
                ▼
Step 5 — Balance Query
        │
        ├── BalanceQuery
        ├── BalanceResult
        └── BalanceQueryService
```

The Balance implementation must import and use the Step 4 types.

It must not introduce:

```text
BalanceTotalsKey
BalanceTotalValue
Balance-specific aggregation key
Balance-specific aggregate value
```

as competing abstractions.

For the Phase 7 Inventory implementation, the established relationship is:

```text
TotalsKey
    Product + Warehouse

TotalValue
    Decimal Quantity
```

The exact module path is an implementation detail of the Step 4 Totals API. The ownership boundary is not.

This is a dependency on the existing Step 4 Totals API, not a deferred design decision and not a new Phase 7 step.

---

# 75. Next Step

Using the Step 4 Totals API, the intended Balance API shape is:

whether TotalsKey is the correct dependency boundary;
whether the proposed TotalsReader abstraction belongs to Step 4 or Step 5;
whether BalanceResult.value can be typed without weakening the existing Totals type model;
whether zero/absence semantics are correctly represented;
whether the error hierarchy is minimal;
whether the module dependency direction is correct;
whether the public API is sufficiently small;
whether the proposed implementation algorithm preserves all Step 5 invariants.

Implementation must begin only after the Concrete API Design receives architectural approval.
