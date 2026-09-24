# Phase 7 Step 9 — Vertical Slice

## Concrete API Design

**Status:** Draft for API Review
**Phase:** Phase 7 — Register Totals / Inventory
**Step:** 9 — Vertical Slice

---

# 1. Purpose

This document defines the concrete API usage for the approved Phase 7 Step 9 vertical slice using the APIs verified in the current repository.

No new production abstraction is required.

The target path is:

```text
Goods Receipt
    ↓
PostingEngine
    ↓
RegisterPostingResultCoordinator
    ↓
RegisterMutationOrchestrator
    ├── RegisterFactPersistence
    └── TotalsMaintenanceCoordinator
            ↓
        TotalsEngine
            ↓
        BalanceQueryService
```

Movement queries use:

```text
RegisterFactPersistence
    ↓
DefaultMovementQueryService
    ↓
MovementQuery
```

---

# 2. Verified API Surface

All scenarios below use the following existing APIs.

## 2.1 Posting

```python
PostingEngine.post(document) -> PostingResult
PostingEngine.unpost(document) -> PostingResult
PostingEngine.repost(document) -> PostingResult
```

Success is checked with:

```python
result.is_success
```

or:

```python
result.outcome is PostingOutcome.SUCCESS
```

`is_success` is a property, not a method.

---

## 2.2 Production Inventory Composition

The verified composition entry point is:

```python
composition = (
    StandardConfigurationBootstrap()
    .compose_inventory_register_platform(persistence)
)
```

The composition provides the production register components required by Step 9, including:

```text
composition.totals_engine
composition.maintenance
composition.mutation
composition.movement_validator
composition.posting_result_coordinator
composition.movement_query
composition.balance_query
```

The primary vertical tests must use:

```text
composition.posting_result_coordinator
```

rather than a test-only posting coordinator.

---

## 2.3 Persistence

The authoritative persistence API is:

```python
persistence.append(movements)
persistence.find_by_source_document(
    register_identity,
    source_document_identity,
)
persistence.remove(movement_identities)
persistence.enumerate(register_identity)
```

Step 9 uses:

```python
persistence.enumerate(INVENTORY_REGISTER_ID)
```

for authoritative state inspection and:

```python
persistence.find_by_source_document(
    INVENTORY_REGISTER_ID,
    document.identity,
)
```

for source-document-specific assertions.

---

## 2.4 Inventory Semantics

Verified constants:

```python
INVENTORY_REGISTER_ID
INVENTORY_PRODUCT_DIMENSION
INVENTORY_WAREHOUSE_DIMENSION
INVENTORY_QUANTITY_RESOURCE
```

Goods Receipt uses:

```python
MovementType.INCOME
```

Inventory totals use:

```text
INCOME  → +1
EXPENSE → -1
```

---

## 2.5 Goods Receipt Input

`GoodsReceiptPostingHandler` consumes document state containing:

```text
lines
    → CollectionValue
        → StructuredValue
            → product
            → warehouse
            → quantity
```

The resulting Inventory Movement contains:

```text
register_identity
source_document_identity
movement_type
dimensions
resources
accounting_time
```

The handler obtains:

```python
accounting_time = context.clock.now()
```

Therefore temporal tests require a deterministic posting clock.

---

## 2.6 Movement Inspection

The verified Movement access pattern is:

```python
movement.register_identity
movement.source_document_identity
movement.movement_type
movement.dimensions.get(key)
movement.resources.get(key)
movement.accounting_time
```

Step 9 must use `.get(...)` for dimensions and resources.

---

## 2.7 Totals

The verified Totals API is:

```python
key = TotalsKey.from_mapping(
    {
        INVENTORY_PRODUCT_DIMENSION: product,
        INVENTORY_WAREHOUSE_DIMENSION: warehouse,
    }
)
```

and:

```python
total = composition.totals_engine.get(
    INVENTORY_REGISTER_ID,
    key,
)
```

The expected aggregate is independently calculated from persisted Movement Facts rather than from the Totals Engine itself.

---

## 2.8 Balance

The verified current-state Balance API is:

```python
balance = composition.balance_query.query(
    BalanceQuery(
        register_identity=INVENTORY_REGISTER_ID,
        aggregation_scope=key,
    )
)
```

The value is:

```python
balance.value
```

The API has no temporal parameter.

Therefore Step 9 does not introduce historical Balance.

---

## 2.9 Movement Query

The verified query API is:

```python
MovementQueryPeriod(
    start=start,
    end=end,
)
```

```python
MovementDimensionFilter.from_mapping(
    {
        ...
    }
)
```

```python
MovementQuery(
    register_identity=INVENTORY_REGISTER_ID,
    period=period,
    dimensions=dimensions,
)
```

and:

```python
composition.movement_query.query(query)
```

Period semantics are:

```text
[start, end)
```

and dimension filters are partial mappings.

---

# 3. Posting Engine Construction

The existing repository pattern is used to connect Goods Receipt to the production register composition:

```python
composition = (
    StandardConfigurationBootstrap()
    .compose_inventory_register_platform(persistence)
)

resolver = MappingPostingHandlerResolver(
    {
        document.object_type.metadata_identity():
            GoodsReceiptPostingHandler()
    }
)

services = PostingServices(
    StateProvider(state)
)

engine = PostingEngine(
    resolver,
    PostingContextFactory(services, clock),
    composition.movement_validator,
    composition.posting_result_coordinator,
)
```

No Step 9-specific Posting Engine wrapper is introduced.

---

# 4. Deterministic Goods Receipt State

The test fixture constructs the existing `RuntimeDurableState` representation:

```python
RuntimeDurableState(
    fields=DurableFieldState(
        {
            "lines": CollectionValue(
                (
                    StructuredValue(
                        {
                            INVENTORY_PRODUCT_DIMENSION: "P1",
                            INVENTORY_WAREHOUSE_DIMENSION: "W1",
                            INVENTORY_QUANTITY_RESOURCE: Decimal("2.5"),
                        }
                    ),
                )
            )
        }
    ),
    references=DurableReferenceState.empty(),
    business_state=BusinessStateSnapshot.empty(),
    system_fields=DurableSystemFieldState.empty(),
)
```

A test `StateProvider` may replace the state before `repost()`.

---

# 5. Deterministic Accounting Time

Temporal tests use an explicit clock:

```python
class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value
```

Example:

```python
clock = FixedClock(
    datetime(
        2026,
        9,
        24,
        12,
        0,
        tzinfo=UTC,
    )
)
```

Tests must not use `datetime.now()` for accounting semantics.

---

# 6. Primary Vertical Scenario

The core scenario is:

```text
Goods Receipt
    ↓
PostingEngine.post()
    ↓
persisted Movement
    ↓
TotalsEngine
    ↓
BalanceQueryService
```

Concrete assertions:

```python
result = engine.post(document)

assert result.is_success

movements = tuple(
    persistence.enumerate(INVENTORY_REGISTER_ID)
)

assert len(movements) == 1

movement = movements[0]

assert movement.register_identity == INVENTORY_REGISTER_ID
assert movement.source_document_identity == document.identity
assert movement.movement_type is MovementType.INCOME
assert movement.dimensions.get(
    INVENTORY_PRODUCT_DIMENSION
) == product
assert movement.dimensions.get(
    INVENTORY_WAREHOUSE_DIMENSION
) == warehouse
assert movement.resources.get(
    INVENTORY_QUANTITY_RESOURCE
) == quantity
```

Then:

```python
key = TotalsKey.from_mapping(
    {
        INVENTORY_PRODUCT_DIMENSION: product,
        INVENTORY_WAREHOUSE_DIMENSION: warehouse,
    }
)

assert composition.totals_engine.get(
    INVENTORY_REGISTER_ID,
    key,
) == quantity

balance = composition.balance_query.query(
    BalanceQuery(
        register_identity=INVENTORY_REGISTER_ID,
        aggregation_scope=key,
    )
)

assert balance.value == quantity
```

This proves the complete production chain.

---

# 7. Unpost

The production boundary is:

```python
result = engine.unpost(document)

assert result.is_success
```

Authoritative state:

```python
assert persistence.find_by_source_document(
    INVENTORY_REGISTER_ID,
    document.identity,
) == ()
```

For the affected scope:

```python
assert composition.totals_engine.get(
    INVENTORY_REGISTER_ID,
    key,
) == Decimal("0")
```

and:

```python
assert composition.balance_query.query(
    BalanceQuery(
        register_identity=INVENTORY_REGISTER_ID,
        aggregation_scope=key,
    )
).value == Decimal("0")
```

The test does not invoke `RegisterMutationOrchestrator.remove()` directly.

---

# 8. Repost

The production boundary is:

```python
result = engine.repost(document)

assert result.is_success
```

The existing implementation semantics are:

```text
remove old effect
    ↓
establish new effect
```

The test therefore verifies the resulting authoritative state rather than movement identity reuse.

For a changed quantity:

```python
state_provider.state = make_state(
    product=product,
    warehouse=warehouse,
    quantity=Decimal("15"),
)

result = engine.repost(document)

assert result.is_success
```

Then:

```python
movements = persistence.find_by_source_document(
    INVENTORY_REGISTER_ID,
    document.identity,
)

assert len(movements) == 1

assert movements[0].resources.get(
    INVENTORY_QUANTITY_RESOURCE
) == Decimal("15")
```

Totals and Balance must reflect `Decimal("15")`.

---

# 9. Multiple-Movement Fixture

The recommended fixture contains:

```text
Document A → P1 / W1 → 10
Document B → P1 / W2 → 20
Document C → P2 / W1 → 30
Document D → P1 / W1 → 5
```

Each document is posted with an explicit accounting time.

This dataset supports all required query scenarios.

---

# 10. Dimension Queries

## Product

```python
query = MovementQuery(
    register_identity=INVENTORY_REGISTER_ID,
    period=full_period,
    dimensions=MovementDimensionFilter.from_mapping(
        {
            INVENTORY_PRODUCT_DIMENSION: "P1",
        }
    ),
)
```

Expected documents:

```text
A, B, D
```

## Warehouse

```python
MovementDimensionFilter.from_mapping(
    {
        INVENTORY_WAREHOUSE_DIMENSION: "W1",
    }
)
```

Expected:

```text
A, C, D
```

## Product + Warehouse

```python
MovementDimensionFilter.from_mapping(
    {
        INVENTORY_PRODUCT_DIMENSION: "P1",
        INVENTORY_WAREHOUSE_DIMENSION: "W1",
    }
)
```

Expected:

```text
A, D
```

Assertions should identify movements/source documents rather than rely only on counts.

---

# 11. Temporal Query

Use:

```python
T1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)
T3 = datetime(2026, 9, 3, 10, 0, tzinfo=UTC)
T4 = datetime(2026, 9, 4, 10, 0, tzinfo=UTC)
```

Query:

```python
query = MovementQuery(
    register_identity=INVENTORY_REGISTER_ID,
    period=MovementQueryPeriod(
        start=T2,
        end=T4,
    ),
    dimensions=MovementDimensionFilter.from_mapping({}),
)
```

Semantics:

```text
[T2, T4)

T2 → included
T3 → included
T4 → excluded
```

The test explicitly verifies both boundaries.

---

# 12. Combined Temporal + Dimension Query

Example:

```python
query = MovementQuery(
    register_identity=INVENTORY_REGISTER_ID,
    period=MovementQueryPeriod(
        start=T2,
        end=T4,
    ),
    dimensions=MovementDimensionFilter.from_mapping(
        {
            INVENTORY_PRODUCT_DIMENSION: "P1",
            INVENTORY_WAREHOUSE_DIMENSION: "W2",
        }
    ),
)

movements = composition.movement_query.query(query)
```

The expected result is derived from the explicit fixture data.

The test must not reproduce the implementation's internal filtering logic.

---

# 13. Authoritative / Derived Consistency

A test-only helper may verify:

```text
Persisted Movement Facts
        ↓
independent signed aggregate
        ↓
TotalsEngine.get(...)
        ↓
BalanceQueryService.query(...)
```

The independent aggregate is calculated from persisted movements:

```python
expected = Decimal("0")

for movement in movements:
    quantity = movement.resources.get(
        INVENTORY_QUANTITY_RESOURCE
    )

    if movement.movement_type is MovementType.INCOME:
        expected += quantity
    elif movement.movement_type is MovementType.EXPENSE:
        expected -= quantity
```

The test then asserts:

```python
assert composition.totals_engine.get(
    INVENTORY_REGISTER_ID,
    key,
) == expected
```

and:

```python
assert composition.balance_query.query(
    BalanceQuery(
        register_identity=INVENTORY_REGISTER_ID,
        aggregation_scope=key,
    )
).value == expected
```

The helper must not use `TotalsDefinition` to calculate `expected`.

---

# 14. Test Structure

Preferred location:

```text
tests/vertical/phase7/
    test_phase7_step9_vertical_slice.py
```

Fixtures may provide:

```text
persistence
composition
state_provider
clock
posting_engine
movement_query_service
balance_query_service
```

Existing test helpers and fixture patterns should be reused where available.

---

# 15. Required Vertical Scenarios

The minimum suite is:

```text
test_goods_receipt_posting_persists_inventory_movement
test_posting_updates_inventory_totals_and_balance
test_unpost_removes_inventory_effect_from_persistence_totals_and_balance
test_repost_replaces_inventory_effect_with_new_quantity

test_inventory_movement_query_filters_by_product
test_inventory_movement_query_filters_by_warehouse
test_inventory_movement_query_filters_by_product_and_warehouse
test_inventory_movement_query_filters_by_accounting_period
test_inventory_movement_query_uses_half_open_period
test_inventory_movement_query_combines_period_and_dimensions

test_inventory_persisted_movements_match_current_totals_and_balance
```

Tests may be parametrized where that improves maintainability without reducing diagnostics.

---

# 16. Production API Changes

Verified repository inspection shows:

```text
Required production API changes: NONE
```

Step 9 is therefore primarily an integration/vertical testing task.

No changes are currently required to:

```text
PostingEngine
RegisterPostingResultCoordinator
RegisterMutationOrchestrator
RegisterFactPersistence
TotalsEngine
BalanceQueryService
MovementQueryService
InventoryRegisterConfiguration
StandardConfigurationBootstrap
```

---

# 17. Explicit Non-Goals

Do not introduce:

```text
InventoryMovementService
InventoryBalanceService
InventoryQueryService
InventoryTotalsService
InventoryPostingCoordinator
HistoricalBalanceQuery
InventoryRegisterRuntime
RegisterReplacementService
```

Step 9 does not add historical Balance semantics.

Temporal behavior remains a Movement Facts query concern.

---

# 18. Error and Event Assertions

Success is asserted through the existing `PostingResult` contract.

Where event verification is included, use the existing:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

No Step 9-specific error or event type is introduced.

---

# 19. API Ownership

| Responsibility          | Existing API                             | Step 9    |
| ----------------------- | ---------------------------------------- | --------- |
| Goods Receipt posting   | `GoodsReceiptPostingHandler`             | indirect  |
| Post                    | `PostingEngine.post()`                   | direct    |
| Unpost                  | `PostingEngine.unpost()`                 | direct    |
| Repost                  | `PostingEngine.repost()`                 | direct    |
| Persistence             | `RegisterFactPersistence`                | inspect   |
| Totals                  | `TotalsEngine.get()`                     | inspect   |
| Totals key              | `TotalsKey.from_mapping()`               | construct |
| Balance                 | `BalanceQueryService.query()`            | query     |
| Movement query          | `MovementQueryService.query()`           | query     |
| Temporal period         | `MovementQueryPeriod`                    | construct |
| Dimensions              | `MovementDimensionFilter.from_mapping()` | construct |
| Inventory configuration | `InventoryRegisterConfiguration`         | consume   |
| Production composition  | `compose_inventory_register_platform()`  | construct |

---

# 20. Implementation Boundary

After API approval, expected changes are primarily:

```text
tests/vertical/phase7/
```

No production API redesign is planned.

If implementation exposes an actual mismatch between the verified API and the approved architecture, that mismatch must be reviewed before changing production code.

---

# 21. Concrete API Completion Criteria

The API design is considered complete when:

* every Step 9 scenario maps to an existing repository API;
* the production composition is explicit;
* Goods Receipt input construction is explicit;
* persistence inspection is explicit;
* Totals construction/query is explicit;
* Balance construction/query is explicit;
* Movement Query construction is explicit;
* `[start, end)` semantics are explicit;
* dimension filtering is explicit;
* repost semantics are explicit;
* authoritative/derived consistency verification is explicit;
* no unnecessary production API changes remain.

---

# 22. Final API Decision

The repository-verified design confirms:

```text
Concrete API changes required: NONE
```

The implementation target is the production vertical test path:

```text
Goods Receipt
    ↓
GoodsReceiptPostingHandler
    ↓
PostingEngine
    ↓
RegisterPostingResultCoordinator
    ↓
RegisterMutationOrchestrator
    ├── RegisterFactPersistence
    └── TotalsMaintenanceCoordinator
            ↓
        TotalsEngine
            ↓
        BalanceQueryService
```

with:

```text
RegisterFactPersistence
    ↓
DefaultMovementQueryService
    ↓
MovementQuery
```

for temporal and dimension queries.

**Status:** Ready for Concrete API Review.
