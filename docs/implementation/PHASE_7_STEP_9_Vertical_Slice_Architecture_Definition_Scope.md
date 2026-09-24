# Phase 7 Step 9 — Vertical Slice

## Architecture Definition / Scope — Final

**Status:** Approved for implementation
**Phase:** Phase 7 — Register Totals / Inventory
**Step:** 9 — Vertical Slice
**Document type:** Architecture Definition / Scope

---

## 1. Purpose

Phase 7 Step 9 validates the complete production vertical slice connecting an operational document with the resulting Inventory register state:

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

The slice must also demonstrate:

* unposting;
* reposting;
* dimension filtering;
* temporal movement queries;
* consistency between authoritative Movement Facts and derived Totals / Balance state.

Step 9 is an **integration and behavioral proof step**, not the introduction of a new subsystem.

The purpose is to demonstrate that the architecture implemented through Phases 6–7 works as one coherent production path.

---

# 2. Architectural Intent

The vertical slice must prove that:

1. Goods Receipt posting produces the correct Inventory movement.
2. The movement is persisted as an authoritative Movement Fact.
3. Totals are updated from the persisted movement operation.
4. Balance is obtained from Totals.
5. Unposting removes the authoritative movement and its derived effect.
6. Reposting replaces the previous register effect with the newly calculated effect.
7. Movement queries can retrieve authoritative facts by:

   * accounting period;
   * dimensions;
   * combined period and dimension criteria.
8. No Inventory-specific implementation is required inside the generic Register Platform.
9. Production composition is used rather than a test-only substitute for the register posting boundary.

---

# 3. Scope

## 3.1 Included

Step 9 includes:

### Posting

```text
GoodsReceiptPostingHandler
        ↓
PostingEngine
        ↓
MovementValidator
        ↓
RegisterPostingResultCoordinator
        ↓
RegisterMutationOrchestrator
```

### Persistence

```text
RegisterMutationOrchestrator
        ↓
RegisterFactPersistence
```

### Totals

```text
RegisterMutationOrchestrator
        ↓
TotalsMaintenanceCoordinator
        ↓
TotalsEngine
```

### Balance

```text
TotalsEngine
        ↓
BalanceQueryService
        ↓
BalanceResult
```

### Movement Queries

```text
RegisterFactPersistence
        ↓
MovementQueryService
```

The vertical slice must exercise these production components together.

---

# 4. Production Posting Boundary

The primary production integration boundary for Step 9 is:

```text
PostingEngine
    ↓
RegisterPostingResultCoordinator
    ↓
RegisterMutationOrchestrator
```

The Step 9 vertical tests must use the production:

```text
RegisterPostingResultCoordinator
```

and the production Inventory composition supplied by:

```text
StandardConfigurationBootstrap.compose_inventory_register_platform(...)
```

A test-only `PostingResultCoordinator` or Inventory-specific fake coordinator must not be used for the primary Step 9 vertical slice.

Test doubles remain appropriate for isolated unit tests of individual components, but they do not constitute proof of the production vertical path.

---

# 5. Goods Receipt → Posting

The Goods Receipt posting path is:

```text
Goods Receipt
    ↓
GoodsReceiptPostingHandler
    ↓
PostingEngine
    ↓
MovementSet
```

The resulting Inventory movement must conform to the existing Inventory Register Contract.

For Goods Receipt:

```text
MovementType = INCOME
```

The movement must contain the Inventory dimensions:

```text
product
warehouse
```

and the Inventory resource:

```text
quantity
```

with `Decimal` quantity semantics.

The existing Inventory configuration remains the authoritative source for these semantics.

Step 9 must not duplicate or redefine Inventory register semantics.

---

# 6. Inventory Movement

The resulting movement is an authoritative Register Movement / Movement Fact.

The movement must contain at least:

* movement identity;
* register identity;
* movement type;
* source document identity;
* accounting time;
* Inventory dimensions;
* quantity resource.

The vertical slice must verify that the movement reaching the Register Platform is the same logical effect represented in persistence and used by Totals.

Movement Facts are authoritative.

Totals and Balance are derived representations.

---

# 7. Persistence

The production persistence boundary is:

```text
RegisterFactPersistence
```

The Step 9 slice must prove that posting results in a persisted Movement Fact.

Persistence must remain generic.

No Inventory-specific persistence implementation is introduced by Step 9.

For unposting, the authoritative lookup is:

```text
find_by_source_document(
    register_identity,
    source_document_identity,
)
```

This lookup is performed by the production `RegisterPostingResultCoordinator`.

The resulting movements are then passed to the generic mutation layer for removal.

---

# 8. Totals

Totals are maintained through the existing generic maintenance architecture:

```text
RegisterMutationOrchestrator
        ↓
TotalsMaintenanceCoordinator
        ↓
TotalsEngine
```

For Inventory:

```text
INCOME  → +quantity
EXPENSE → -quantity
```

The Inventory Totals Definition remains:

```text
register = Inventory
dimensions = Product + Warehouse
resource = Quantity
type = Decimal
```

Step 9 must verify that the total resulting from the persisted movement corresponds to the expected Inventory balance.

No Inventory-specific Totals Engine is introduced.

---

# 9. Balance

Balance remains a read projection over the current Totals state:

```text
TotalsEngine
    ↓
BalanceQueryService
    ↓
BalanceResult
```

The Step 9 slice must verify:

```text
persisted movement
        ↓
totals
        ↓
balance
```

The expected balance must correspond to the Inventory movement facts currently represented in Totals.

Balance semantics themselves are not changed by Step 9.

---

# 10. Unposting

Unposting follows:

```text
PostingEngine
    ↓
RegisterPostingResultCoordinator.remove()
    ↓
RegisterFactPersistence.find_by_source_document()
    ↓
RegisterMutationOrchestrator.remove()
    ↓
Persistence + Totals
```

The vertical slice must prove that after successful unposting:

1. the source document no longer has an active Inventory movement;
2. the corresponding Movement Fact has been removed;
3. the corresponding Totals contribution has been removed;
4. the resulting Balance reflects the removal.

The authoritative state used to identify the effect is persisted Movement Facts.

Step 9 must not introduce a separate Inventory posting ledger or effect-tracking subsystem.

---

# 11. Reposting

Reposting follows the existing Posting Engine semantics:

```text
calculate new posting effect
        ↓
remove old register effect
        ↓
establish new register effect
```

Conceptually:

```text
Old Movement
     ↓
remove
     ↓
New Movement
     ↓
establish
```

The vertical slice must include a repost scenario in which the Goods Receipt changes in a way that changes the resulting Inventory quantity.

The test must prove that:

* the previous movement is removed;
* the new movement is persisted;
* the previous Totals contribution is removed;
* the new Totals contribution is established;
* the final Balance corresponds to the new posting;
* only the current posting effect remains active.

No `replace()` operation is required.

The existing generic remove + establish semantics are sufficient.

---

# 12. Dimension Filtering

Step 9 must demonstrate Inventory movement querying by dimensions.

Inventory dimensions are:

```text
product
warehouse
```

The existing generic `MovementDimensionFilter` is used.

Example conceptual query:

```text
product = P1
```

must return movements for `P1` regardless of warehouse, subject to the requested period and register.

A combined filter:

```text
product = P1
warehouse = W1
```

must return only movements matching both dimensions.

No Inventory-specific query service is introduced.

---

# 13. Temporal Queries

Temporal querying in Step 9 applies to **Movement Facts**.

The existing generic:

```text
MovementQueryPeriod
```

is used with the established half-open interval:

```text
[start, end)
```

The vertical slice must demonstrate that movements can be selected by `accounting_time`.

For example:

```text
period = [T1, T2)
```

must include movements satisfying:

```text
T1 <= accounting_time < T2
```

and exclude movements outside that interval.

The query must also preserve the existing timezone-aware boundary requirements.

### Important boundary

Step 9 does **not** introduce historical or temporal Balance.

The current Balance API represents current Totals state and does not accept a temporal period.

Therefore:

```text
Temporal Query
    ↓
Movement Facts
```

not:

```text
Temporal Query
    ↓
Historical Balance
```

Historical balance semantics are outside the scope of Step 9.

---

# 14. Combined Query

The vertical slice should demonstrate the combined use of:

```text
register
+
accounting period
+
partial/full dimensions
```

Conceptually:

```text
Inventory movements
    ↓
period filter
    ↓
dimension filter
    ↓
matching Movement Facts
```

This confirms that temporal and dimensional query semantics operate on the same authoritative persisted movement set.

---

# 15. Consistency Model

Step 9 must verify the following relationship:

```text
Movement Facts
      ↓
   Totals
      ↓
   Balance
```

For a valid current state:

```text
Balance
=
aggregation of applicable Movement Facts
```

for the Inventory register and requested dimension scope.

The slice should explicitly verify consistency after:

* posting;
* unposting;
* reposting.

The test suite must not treat Totals as the authoritative source of movement history.

Movement Facts remain authoritative.

---

# 16. Recovery / Maintenance Boundary

Step 9 does not introduce a new recovery mechanism.

The existing maintenance architecture remains responsible for:

* lifecycle state;
* consistency state;
* rebuild;
* recovery admission;
* maintenance failure semantics.

Production Inventory composition already initializes Totals through the generic maintenance mechanism.

Step 9 may verify that the production composition starts in the expected active/valid maintenance state, but it does not redesign maintenance behavior.

Maintenance architecture was established in Phase 7 Step 6 and is outside the implementation scope of Step 9.

---

# 17. Production Composition

The production composition used by the vertical slice is the existing:

```text
StandardConfigurationBootstrap.compose_inventory_register_platform(...)
```

It must provide the production chain:

```text
Inventory configuration
        ↓
TotalsEngine
        ↓
TotalsMaintenanceCoordinator
        ↓
MovementValidator
        ↓
RegisterMutationOrchestrator
        ↓
RegisterPostingResultCoordinator
        ↓
MovementQueryService
        ↓
BalanceQueryService
```

The composition must remain generic at the platform level and Inventory-specific only at the configuration boundary.

No new public `StandardRegisterRuntime` abstraction is introduced.

---

# 18. Existing Step 8 Tests

Step 8 already contains focused production-composition tests covering:

* posting;
* unposting;
* reposting;
* initial maintenance state.

Step 9 must **not duplicate those tests merely to increase test count**.

Instead, Step 9 adds a dedicated vertical suite whose purpose is broader integration proof:

```text
document
→ posting
→ movement
→ persistence
→ totals
→ balance
→ queries
```

The Step 8 tests remain focused composition tests.

The Step 9 tests become the explicit end-to-end behavioral proof of the complete production slice.

---

# 19. Error Semantics

Step 9 does not redefine existing Posting or Register error semantics.

The vertical slice may verify existing behavior where relevant, but implementation must preserve the established distinctions between:

* successful posting;
* ordinary posting failure;
* persistence failure;
* indeterminate persistence outcome;
* maintenance failure.

No new Step 9-specific exception hierarchy is introduced.

---

# 20. Event Semantics

Step 9 preserves the established Posting Engine event semantics.

Events are emitted only after successful logical completion:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

Step 9 does not introduce register-specific events.

The vertical tests may verify event behavior where it is part of the production posting contract, but event architecture is not otherwise changed.

---

# 21. Determinism

The vertical slice must preserve existing deterministic behavior.

The resulting register state must not depend on:

* uncontrolled runtime identity;
* iteration order;
* implicit storage order;
* external mutable state;
* uncontrolled time.

Accounting time used in tests must be explicit.

Movement queries must use deterministic ordering already defined by the generic query service.

---

# 22. Explicit Non-Goals

The following are outside Step 9:

### No new Inventory infrastructure

Do not create:

* Inventory-specific persistence;
* Inventory-specific mutation orchestrator;
* Inventory-specific Totals Engine;
* Inventory-specific maintenance coordinator;
* Inventory-specific recovery service;
* Inventory-specific Balance Engine;
* Inventory-specific temporal Balance service.

### No historical Balance

Step 9 does not define:

```text
BalanceAt(time)
```

or any equivalent historical balance API.

### No new generic abstraction without necessity

Step 9 must not introduce generic abstractions merely to support tests.

### No new persistence model

Existing Movement Facts remain the authoritative persisted representation.

### No change to approved Inventory semantics

Register identity, dimensions, resource, movement signs, and validation remain those established in Step 8.

### No replacement operation

Reposting continues to use:

```text
remove + establish
```

rather than adding a new replacement primitive.

---

# 23. Required Vertical Scenarios

The Step 9 implementation must provide production-composition tests for at least the following scenarios.

## Scenario A — Goods Receipt Posting

Given a valid Goods Receipt:

```text
post(document)
```

verify:

* posting succeeds;
* one Inventory movement exists;
* movement contains expected source document;
* movement contains expected product;
* movement contains expected warehouse;
* movement contains expected quantity;
* movement is persisted;
* Inventory Totals are updated;
* Inventory Balance is updated.

---

## Scenario B — Multiple Goods Receipt Effects

Post multiple documents affecting:

* different products;
* different warehouses;
* potentially the same product/warehouse combination.

Verify that:

* all movements are persisted;
* Totals aggregate correctly;
* Balance aggregation is correct;
* independent dimensions remain distinguishable.

---

## Scenario C — Unpost

Post a Goods Receipt and then unpost it.

Verify:

```text
before:
movement exists
totals include movement
balance includes movement

after:
movement absent
totals exclude movement
balance excludes movement
```

---

## Scenario D — Repost With Changed Quantity

Post a Goods Receipt.

Modify its quantity.

Repost.

Verify:

```text
old movement removed
new movement established
new movement persisted
old total removed
new total applied
final balance = new quantity
```

and that only the current effect remains.

---

## Scenario E — Dimension Query

Create movements for different:

```text
product / warehouse
```

combinations.

Query by:

```text
product
```

and:

```text
product + warehouse
```

Verify the returned Movement Facts.

---

## Scenario F — Temporal Query

Create movements with explicit accounting times.

Query a period:

```text
[start, end)
```

Verify:

* start boundary included;
* end boundary excluded;
* movements outside the interval excluded;
* missing accounting time excluded;
* timezone-aware boundaries are respected.

---

## Scenario G — Combined Temporal + Dimension Query

Query:

```text
period + dimensions
```

and verify that only Movement Facts satisfying all predicates are returned.

---

## Scenario H — Authoritative / Derived Consistency

After posting, unposting, and reposting scenarios, compare:

```text
persisted Movement Facts
```

against:

```text
Totals
```

and:

```text
Balance
```

to verify that the derived state represents the current authoritative movement set.

---

# 24. Acceptance Criteria

Step 9 architecture is accepted when:

1. Goods Receipt reaches the production Posting Engine.
2. Posting reaches the production `RegisterPostingResultCoordinator`.
3. Inventory movements are persisted through `RegisterFactPersistence`.
4. Totals are maintained through the existing generic maintenance path.
5. Balance is obtained from Totals.
6. Unposting removes the authoritative movement effect.
7. Reposting replaces the previous effect using remove + establish.
8. Dimension queries operate against persisted Movement Facts.
9. Temporal queries operate against persisted Movement Facts.
10. Combined temporal + dimension queries work correctly.
11. Current Balance remains a current-state query and is not given historical semantics.
12. Movement Facts remain authoritative.
13. No Inventory-specific generic infrastructure is introduced.
14. Step 8 semantics remain unchanged.
15. Production composition is used by the primary vertical slice.
16. Existing error and event semantics remain intact.
17. The implementation remains deterministic.
18. Existing unit tests remain green.
19. New Step 9 vertical tests pass.
20. Documentation accurately reflects the resulting implementation.

---

# 25. Quality Gate

Before completion of Step 9:

```text
pytest -q
ruff check .
black --check .
mypy src
```

must pass.

Additionally:

* Step 9 vertical tests must pass using production composition.
* No unintended architectural duplication may remain.
* Documentation must be reconciled with the final implementation.
* `git diff` and `git status` must be reviewed before commit.
* The final commit must contain only the intended Step 9 changes.

---

# 26. Definition of Done

Phase 7 Step 9 is complete when:

```text
Architecture
    ↓
Production Integration
    ↓
Vertical Tests
    ↓
Quality Gate
    ↓
Documentation Reconciliation
    ↓
Final Review
    ↓
Commit
    ↓
Push
```

has been completed successfully.

The resulting implementation must demonstrate the complete production path:

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

together with:

```text
Unpost
Repost
Dimension Query
Temporal Movement Query
Combined Query
Consistency Verification
```

without introducing new architectural layers that are not required by the approved Register Platform design.

---

# 27. Final Architecture Review Decision

**Status: APPROVED**

The repository inspection confirms that the existing architecture already provides the required production integration points.

Step 9 therefore proceeds as a **vertical integration proof**, not as a platform redesign.

The primary implementation objective is to prove the behavior of the existing architecture as one production slice and to expose any integration defects through executable tests rather than introducing additional abstractions.

The three architectural clarifications incorporated into this final document are mandatory:

1. **Temporal queries target Movement Facts, not historical Balance.**
2. **Step 9 extends rather than duplicates the focused Step 8 production-composition tests.**
3. **The primary vertical boundary is the production `RegisterPostingResultCoordinator`, not a test-only coordinator.**

This document is the final approved Architecture Definition / Scope for Phase 7 Step 9.
