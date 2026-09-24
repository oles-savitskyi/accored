# Phase 7 Step 10 — Rebuild and Consistency Validation

## Concrete API Design

**Status:** Final Concrete API Design
**Phase:** Phase 7 — Register Totals / Balance
**Step:** Step 10 — Rebuild and Consistency Validation
**Architecture decision:** No production architecture extension
**Production API changes:** None

---

## 1. Purpose

Phase 7 Step 10 validates that the existing Register Platform can reconstruct derived Totals state from authoritative Movement Facts and that the resulting state is consistent with the state maintained incrementally during normal operation.

The step proves the following invariant:

```text
Movement Facts
      ↓
Incremental Maintenance
      ↓
Totals A

Movement Facts
      ↓
Rebuild
      ↓
Totals B

Totals A == Totals B
```

Because Balance is a read projection over Totals:

```text
Totals
   ↓
BalanceQueryService
   ↓
Balance
```

the validation also proves:

```text
Balance A == Balance B
```

The purpose of Step 10 is therefore validation and proof of the existing architecture, not introduction of another rebuild subsystem.

---

# 2. Existing Production APIs

Step 10 uses the existing public contracts without modifying them.

## 2.1 RegisterFactPersistence

Authoritative Movement Facts are accessed through:

```python
RegisterFactPersistence.enumerate(
    register_identity: Identifier,
) -> tuple[Movement, ...]
```

The persistence layer remains the authoritative source for rebuild.

Other existing operations remain unchanged:

```python
append(movements)
find_by_source_document(
    register_identity,
    source_document_identity,
)
remove(movement_identities)
enumerate(register_identity)
```

Step 10 does not introduce another persistence interface.

---

# 3. Totals Maintenance API

The existing maintenance contract is used directly:

```python
class TotalsMaintenanceCoordinator(Protocol):
    def apply(self, movement: Movement) -> MaintenanceResult: ...

    def remove(self, movement: Movement) -> MaintenanceResult: ...

    def rebuild(
        self,
        register_identity: Identifier,
    ) -> MaintenanceResult: ...

    def recover(
        self,
        register_identity: Identifier,
    ) -> MaintenanceResult: ...

    def state(
        self,
        register_identity: Identifier,
    ) -> TotalsMaintenanceState: ...

    def ensure_mutation_admitted(
        self,
        register_identity: Identifier,
    ) -> None: ...
```

No additional Step 10 maintenance API is required.

---

# 4. Rebuild Semantics

The production rebuild path is:

```text
TotalsMaintenanceCoordinator.rebuild()
        ↓
RegisterFactPersistence.enumerate()
        ↓
TotalsEngine.rebuild()
        ↓
Totals state replacement
```

The rebuild operation reconstructs Totals from the complete authoritative Movement Fact set for the requested register.

It does not incrementally modify the previous Totals state.

Conceptually:

```python
movements = persistence.enumerate(register_identity)

totals_engine.rebuild(
    register_identity,
    movements,
)
```

The existing `DefaultTotalsEngine.rebuild()` constructs replacement state from the supplied Movement Facts and replaces the current derived state.

Therefore stale derived entries are removed as part of rebuild.

---

# 5. Maintenance State Validation

`TotalsMaintenanceCoordinator.state()` is a primary validation API for Step 10.

A successful rebuild is not considered fully validated solely from:

```python
result.outcome is MaintenanceOutcome.SUCCESS
```

The resulting maintenance state must also be checked:

```python
state = maintenance.state(register_identity)
```

Expected successful state:

```text
lifecycle = ACTIVE
consistency = VALID
```

Therefore the canonical successful rebuild assertion is:

```python
assert result.outcome is MaintenanceOutcome.SUCCESS

state = maintenance.state(register_identity)

assert state.lifecycle is TotalsLifecycleState.ACTIVE
assert state.consistency is TotalsConsistencyState.VALID
```

This verifies both:

1. the operation completed successfully;
2. the register is admitted to ordinary mutation after the operation.

---

# 6. Recovery Semantics

The public maintenance API exposes:

```python
recover(register_identity)
```

Recovery is a semantic maintenance operation, but the current implementation realizes recovery through rebuild:

```python
def recover(self, register_identity):
    return self.rebuild(register_identity)
```

Consequently:

```python
recover(...)
```

returns a `MaintenanceResult` whose:

```python
result.operation
```

is:

```python
MaintenanceOperation.REBUILD
```

There is intentionally no:

```python
MaintenanceOperation.RECOVER
```

value.

Step 10 must therefore not assert a separate `RECOVER` operation type.

The semantic model is:

```text
recover()
   ↓
rebuild()
   ↓
reconstruct derived state
   ↓
ACTIVE / VALID
```

This preserves the existing production API and implementation.

---

# 7. Recovery Test Scenario

Recovery validation must model an actual recoverable failure boundary.

The scenario is:

```text
1. Establish valid state
2. Trigger maintenance failure
3. State becomes ACTIVE / RECOVERY_REQUIRED
4. Remove the failure condition
5. Call recover()
6. recover() performs rebuild()
7. State becomes ACTIVE / VALID
```

The failure condition must be removed before recovery is attempted.

Otherwise `recover()` delegates to the same rebuild path and will encounter the same failure again.

Canonical validation:

```python
failure_result = ...
assert failure_result.outcome is expected_failure_outcome

failed_state = maintenance.state(register_identity)

assert failed_state.lifecycle is TotalsLifecycleState.ACTIVE
assert failed_state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED

# Fault condition is removed here.

recovery_result = maintenance.recover(register_identity)

assert recovery_result.outcome is MaintenanceOutcome.SUCCESS
assert recovery_result.operation is MaintenanceOperation.REBUILD

recovered_state = maintenance.state(register_identity)

assert recovered_state.lifecycle is TotalsLifecycleState.ACTIVE
assert recovered_state.consistency is TotalsConsistencyState.VALID
```

No separate production recovery service is introduced.

---

# 8. Incremental vs Rebuild Equivalence

The principal Step 10 scenario compares two derived states generated from the same Movement Facts.

## 8.1 Incremental path

Normal production mutation establishes the derived Totals state:

```text
Posting
  ↓
RegisterMutationOrchestrator
  ↓
Persistence.append()
  ↓
TotalsMaintenanceCoordinator.apply()
  ↓
TotalsEngine.apply()
```

The resulting Totals state is:

```text
Totals A
```

## 8.2 Rebuild path

The same authoritative Movement Facts are then used to reconstruct Totals:

```text
Movement Facts
  ↓
maintenance.rebuild()
  ↓
TotalsEngine.rebuild()
  ↓
Totals B
```

The required invariant is:

```text
Totals A == Totals B
```

The test must compare observable Totals values, not internal implementation structures.

---

# 9. Independent Expected Totals

The test must independently validate the result of rebuild.

The expected Totals value is calculated in test code from authoritative Movement Facts using the already-approved Inventory register semantics.

The test must use the actual public Movement access API.

For example:

```python
product = movement.dimensions.get("product")
warehouse = movement.dimensions.get("warehouse")
quantity = movement.resources.get("quantity")
```

The test must not use unsupported mapping syntax such as:

```python
movement.dimensions["product"]
movement.resources["quantity"]
```

because `MovementDimensions` and `MovementResources` expose `get()` rather than `__getitem__`.

The independent calculation is conceptually:

```text
for each Movement Fact:
    determine TotalsKey
    determine signed quantity
    accumulate Decimal value
```

The expected result is then compared with the actual Totals Engine state.

This gives the validation chain:

```text
Movement Facts
      ↓
Independent Expected Totals
      ↓
      ==
      ↓
TotalsEngine state
      ↓
BalanceQueryService
      ↓
BalanceResult.value
```

The independent calculation is a test verification mechanism only. It does not become a second production Totals engine.

---

# 10. Stale Derived-State Validation

Step 10 must prove that rebuild replaces stale derived state rather than preserving obsolete entries.

The stale-state scenario is test-only.

It may deliberately manipulate the derived Totals state through the concrete `TotalsEngine` in a controlled negative test, for example by applying a synthetic movement directly to the engine without establishing the corresponding Movement Fact.

This direct engine manipulation must not be described as a normal production mutation path.

The scenario is:

```text
Authoritative Movement Facts
        ↓
correct Totals state

Test-only direct derived-state mutation
        ↓
stale / divergent Totals state

maintenance.rebuild()
        ↓
Movement Facts
        ↓
replacement Totals state
```

After rebuild:

```text
stale entry is absent
expected entries are present
Totals == independently calculated expected state
state == ACTIVE / VALID
```

No new production API for injecting stale state is introduced.

---

# 11. Rebuild Idempotence

Rebuild must be idempotent with respect to the same authoritative Movement Fact set.

Scenario:

```text
Movement Facts
      ↓
rebuild()
      ↓
Totals A

rebuild()
      ↓
Totals B
```

Required result:

```text
Totals A == Totals B
```

The second rebuild must not accumulate the first rebuild's result.

The test must also verify:

```text
ACTIVE / VALID
```

after both successful rebuilds.

---

# 12. Empty Register

An empty register is a valid rebuild input.

Scenario:

```text
Movement Facts = ∅
        ↓
maintenance.rebuild()
        ↓
Totals = empty
```

Expected result:

```text
MaintenanceOutcome.SUCCESS
ACTIVE / VALID
```

and every queried Total for the register is zero / absent according to the existing `TotalsEngine` semantics.

No special Inventory-specific empty-register API is introduced.

---

# 13. Failure Classification

Step 10 validates the existing maintenance failure boundaries.

Failure tests should not depend exclusively on the production Inventory composition because the production composition performs successful initialization rebuild during construction.

Instead, controlled failure scenarios should instantiate the existing concrete maintenance implementation directly:

```python
DefaultTotalsMaintenanceCoordinator(
    engine,
    persistence,
)
```

with controlled/fault-injecting test dependencies.

This allows the tests to deterministically exercise:

* persistence failure;
* persistence indeterminate failure;
* totals failure;
* unexpected failure;
* transition to `RECOVERY_REQUIRED`;
* subsequent recovery.

These tests validate the existing generic maintenance implementation rather than introducing a production fault-injection abstraction.

---

# 14. Production Composition

Successful vertical and Inventory-specific scenarios must use production composition:

```python
composition = (
    StandardConfigurationBootstrap()
    .compose_inventory_register_platform(persistence)
)
```

The composition already creates:

```text
Inventory Configuration
        ↓
DefaultTotalsEngine
        ↓
DefaultTotalsMaintenanceCoordinator
        ↓
Register Mutation / Posting / Query services
```

and performs initial:

```python
maintenance.rebuild(
    configuration.register_identity
)
```

Successful composition therefore establishes:

```text
ACTIVE / VALID
```

before the test proceeds.

Step 10 must reuse this production composition rather than recreating the production dependency graph in tests.

---

# 15. Balance Validation

Balance is not an independent Totals calculator.

The existing production path is:

```text
TotalsEngine
      ↓
DefaultBalanceQueryService
      ↓
BalanceResult.value
```

Therefore Step 10 validates Balance as a projection over the rebuilt Totals state.

For an aggregation scope:

```python
BalanceQuery(
    register_identity=register_identity,
    aggregation_scope=totals_key,
)
```

the test queries:

```python
balance = composition.balance_query.query(query)
```

and compares:

```python
balance.value
```

with:

```python
composition.totals_engine.get(
    register_identity,
    totals_key,
)
```

The required invariant is:

```text
Independent Expected Totals
          ==
TotalsEngine state
          ↓
BalanceQueryService.value
          ==
TotalsEngine.get(...)
```

No separate Balance reconstruction algorithm is introduced.

---

# 16. Movement Facts Preservation

Rebuild must not mutate or replace authoritative Movement Facts.

The test must capture the persisted Movement Facts before rebuild:

```python
before = persistence.enumerate(register_identity)
```

perform rebuild, and then verify:

```python
after = persistence.enumerate(register_identity)

assert after == before
```

The exact comparison should use the existing `Movement` equality semantics and must not depend on persistence implementation internals.

The invariant is:

```text
rebuild changes derived Totals state
but does not change Movement Facts
```

---

# 17. Unpost → Rebuild

Step 10 validates that rebuild remains consistent after document removal.

Scenario:

```text
Goods Receipt
      ↓
Post
      ↓
Movement Fact exists
      ↓
Totals contains effect

Unpost
      ↓
Movement Fact removed
      ↓
Totals incrementally updated

Rebuild
      ↓
remaining Movement Facts
      ↓
Totals reconstructed
```

Required result:

```text
Incremental Totals == Rebuilt Totals
```

and:

```text
ACTIVE / VALID
```

after rebuild.

The authoritative removal path remains:

```text
source document
      ↓
RegisterFactPersistence.find_by_source_document()
      ↓
RegisterMutationOrchestrator.remove()
```

No Step 10-specific unpost mechanism is introduced.

---

# 18. Repost → Rebuild

Step 10 validates consistency after reposting.

Scenario:

```text
Initial Post
      ↓
Movement Fact A
      ↓
Totals A

Repost
      ↓
remove old effect
      ↓
establish new effect
      ↓
Movement Fact B
      ↓
Totals B

Rebuild
      ↓
Movement Facts B
      ↓
Totals C
```

Required invariant:

```text
Totals B == Totals C
```

The existing repost semantics remain unchanged:

```text
remove old effect
+
establish new effect
```

No replacement-specific persistence API is introduced.

---

# 19. Inventory Register Semantics

The production Inventory configuration remains the semantic authority for the register:

```text
Register:
    INVENTORY_REGISTER_ID

Dimensions:
    product
    warehouse

Resource:
    quantity

Type:
    Decimal

Movement signs:
    INCOME  → +1
    EXPENSE → -1
```

Step 10 must verify that rebuild preserves these semantics.

For example:

```text
INCOME quantity 10
EXPENSE quantity 3
```

must result in:

```text
Quantity = 7
```

for the corresponding Product + Warehouse TotalsKey.

The test must obtain the register configuration from the existing production configuration rather than duplicate production constants where practical.

---

# 20. Dimension Isolation

Step 10 must validate that rebuild preserves TotalsKey dimensional separation.

For example:

```text
Product A / Warehouse 1
Product A / Warehouse 2
Product B / Warehouse 1
```

must remain independent Totals scopes after rebuild.

The test should verify that:

```text
Totals(Product A, Warehouse 1)
```

is unaffected by movements belonging to the other dimension combinations.

This validates the generic TotalsKey and Inventory configuration interaction.

No Inventory-specific aggregation implementation is introduced.

---

# 21. Register Isolation

Register isolation must be tested at the generic Register Platform level.

The production Inventory composition configures a single Inventory register and therefore is not, by itself, sufficient to prove cross-register isolation.

The isolation test should therefore construct a generic test scenario with at least two register identities and corresponding Totals definitions.

The required invariant is:

```text
rebuild(Register A)
```

must not alter:

```text
Totals(Register B)
```

and vice versa.

This validates the generic register-scoped behavior of:

* persistence enumeration;
* TotalsEngine state;
* maintenance state;
* rebuild.

No new multi-register production composition is required for Step 10.

---

# 22. `_applied` Bookkeeping

The coordinator's internal `_applied` bookkeeping is not authoritative state.

It must not be used as the source of truth for rebuild validation.

The authoritative reconstruction source is:

```text
RegisterFactPersistence.enumerate(register_identity)
```

After a successful rebuild, internal bookkeeping is synchronized with the authoritative Movement Fact set.

Tests must therefore validate observable behavior:

```text
Movement Facts
→ Totals
→ Balance
→ Maintenance State
```

rather than asserting the internal structure or contents of `_applied`.

---

# 23. Proposed Test Structure

The primary Step 10 test file is:

```text
tests/vertical/phase7/test_phase7_step10_rebuild_consistency.py
```

The test suite should be organized around behavioral invariants rather than implementation methods.

Recommended scenarios:

### 23.1 Incremental vs rebuild

```text
post movements
→ incremental Totals

rebuild
→ rebuilt Totals

assert equal
```

### 23.2 Rebuild idempotence

```text
rebuild
→ snapshot A

rebuild
→ snapshot B

assert A == B
```

### 23.3 Stale derived state

```text
create valid state
→ deliberately diverge Totals in test-only setup
→ rebuild
→ assert divergence removed
```

### 23.4 Empty register

```text
empty Movement Facts
→ rebuild
→ empty Totals
→ ACTIVE / VALID
```

### 23.5 Recovery

```text
fault
→ RECOVERY_REQUIRED

remove fault
→ recover()
→ rebuild()
→ ACTIVE / VALID
```

### 23.6 Failure classification

Use direct:

```python
DefaultTotalsMaintenanceCoordinator(...)
```

with controlled test dependencies.

Validate the existing failure boundaries without changing production APIs.

### 23.7 Independent consistency validation

```text
Movement Facts
→ independently calculated expected Totals

compare with:
TotalsEngine.get()
```

### 23.8 Balance projection

```text
TotalsEngine.get()
==
BalanceQueryService.query().value
```

### 23.9 Movement Facts preservation

```text
facts_before == facts_after
```

### 23.10 Register isolation

Use generic register-platform setup.

### 23.11 Dimension isolation

Use Inventory Product + Warehouse combinations.

### 23.12 Unpost → rebuild

```text
post
→ unpost
→ rebuild
→ compare
```

### 23.13 Repost → rebuild

```text
post
→ repost
→ rebuild
→ compare
```

---

# 24. Explicitly Excluded APIs

The following APIs must not be introduced in Step 10:

```text
HistoricalBalanceQuery
TemporalBalanceQuery
HistoricalTotalsQuery
TotalsReconciliationService
BackgroundReconciliationService
TotalsConsistencyService
RegisterRebuildService
InventoryRebuildService
InventoryRecoveryService
StandardRegisterRuntime
ConcurrentRebuildCoordinator
```

No additional production abstraction is justified by the Step 10 requirements.

---

# 25. Concurrency Boundary

Concurrent rebuild and mutation transaction isolation are outside the Step 10 API boundary.

Step 10 validates deterministic sequential behavior.

It does not introduce:

```text
locks around persistence transactions
versioning
optimistic concurrency
snapshot isolation
background rebuild jobs
distributed coordination
```

Such concerns may be addressed by a future architecture decision if required.

They must not be implicitly introduced by Step 10 tests.

---

# 26. Historical and Temporal Balance

Step 10 does not extend Balance semantics.

The existing Balance API represents current derived state:

```text
Totals
  ↓
Balance
```

Temporal Movement Queries remain available through the existing generic Movement Query API.

Therefore Step 10 may combine:

```text
MovementQueryPeriod
+
MovementDimensionFilter
```

when validating Movement Facts, but must not introduce a historical Balance API.

The distinction remains:

```text
Movement Facts
    → temporal / dimensional movement queries

Totals
    → current aggregate state

Balance
    → current aggregate read projection
```

---

# 27. Production API Change Summary

| Area                         | Change         |
| ---------------------------- | -------------- |
| RegisterFactPersistence      | None           |
| TotalsEngine                 | None           |
| TotalsMaintenanceCoordinator | None           |
| MaintenanceResult            | None           |
| MaintenanceOperation         | None           |
| TotalsMaintenanceState       | None           |
| BalanceQueryService          | None           |
| RegisterMutationOrchestrator | None           |
| Inventory configuration      | None           |
| PostingEngine                | None           |
| Persistence model            | None           |
| Movement model               | None           |
| Recovery API                 | None           |
| Historical Balance           | Not introduced |
| Temporal Balance             | Not introduced |
| Reconciliation service       | Not introduced |
| Runtime abstraction          | Not introduced |

The only clarification required by Step 10 is semantic:

```text
recover()
```

is implemented by:

```text
rebuild()
```

and therefore returns:

```text
MaintenanceOperation.REBUILD
```

---

# 28. Acceptance Criteria

Step 10 is complete when all of the following are demonstrated.

### Core consistency

* Incrementally maintained Totals equal rebuilt Totals.
* Rebuild is idempotent.
* Rebuild replaces stale derived state.
* Empty-register rebuild succeeds.
* Successful rebuild leaves the register `ACTIVE / VALID`.

### Recovery

* A maintenance failure produces the existing failure/consistency state.
* `RECOVERY_REQUIRED` is treated as a consistency state.
* Ordinary mutation is not admitted while the state is not `ACTIVE / VALID`.
* After the failure condition is removed, `recover()` successfully rebuilds the register.
* Successful recovery results in `ACTIVE / VALID`.
* Recovery result correctly reports `MaintenanceOperation.REBUILD`.

### Independent verification

* Expected Totals are independently calculated from Movement Facts.
* Public `.get()` APIs are used for Movement dimensions/resources.
* No test relies on `_applied` as authoritative state.
* Balance values correspond to the rebuilt Totals state.
* Movement Facts are unchanged by rebuild.

### Inventory

* Product dimension is preserved.
* Warehouse dimension is preserved.
* Quantity resource is preserved.
* Decimal arithmetic is preserved.
* INCOME / EXPENSE signs are preserved.

### Lifecycle operations

* Unpost followed by rebuild produces the same Totals state as incremental maintenance.
* Repost followed by rebuild produces the same Totals state as incremental maintenance.

### Isolation

* Generic register isolation is preserved.
* Inventory dimension combinations remain isolated.

### Architecture

* No new production subsystem is introduced.
* No new production API is introduced.
* No historical or temporal Balance API is introduced.
* No concurrency model is introduced.
* Production success paths use the existing Inventory composition.
* Failure-boundary tests use controlled generic maintenance dependencies.

---

# 29. Definition of Done

Step 10 is complete when:

1. The Step 10 vertical consistency tests are implemented.
2. The tests use the existing production Register Platform APIs.
3. Successful Inventory scenarios use `compose_inventory_register_platform()`.
4. Failure/recovery scenarios use controlled generic maintenance dependencies where necessary.
5. Incremental Totals and rebuilt Totals are proven equivalent.
6. Rebuild idempotence is proven.
7. Stale derived-state replacement is proven.
8. Recovery semantics are proven.
9. Independent Totals validation is proven.
10. Balance projection consistency is proven.
11. Movement Facts preservation is proven.
12. Unpost → rebuild consistency is proven.
13. Repost → rebuild consistency is proven.
14. Inventory dimension and resource semantics are proven.
15. Generic register isolation is proven.
16. `pytest -q` passes.
17. `ruff check .` passes.
18. `black --check .` passes.
19. `mypy src` passes.
20. Architecture and Concrete API documentation are reconciled with the final implementation.
21. No production API changes are introduced unless an implementation-level contradiction is discovered during coding and explicitly reviewed before proceeding.

---

# 30. Final API Decision

The final Step 10 API decision is:

```text
NO PRODUCTION API EXTENSION
```

The existing Register Platform already provides all required capabilities:

```text
RegisterFactPersistence.enumerate()
        ↓
TotalsMaintenanceCoordinator.rebuild()
        ↓
TotalsEngine.rebuild()
        ↓
Totals
        ↓
BalanceQueryService
```

Recovery is already represented by:

```text
recover()
    → rebuild()
```

and maintenance state is already represented by:

```text
ACTIVE / VALID
ACTIVE / INDETERMINATE
ACTIVE / RECOVERY_REQUIRED
```

Therefore Step 10 should add **verification coverage and architectural proof**, not another production subsystem.

The final validation invariant is:

```text
                  Movement Facts
                 /              \
                /                \
       Incremental              Rebuild
        Maintenance               |
              ↓                   ↓
          Totals A            Totals B
              |                   |
              +-------- == -------+
                       |
                    Balance
                       |
                 Current Result
```

with the authoritative principle:

```text
Movement Facts are authoritative.
Totals are derived.
Balance is a projection over Totals.
Rebuild reconstructs derived state from Movement Facts.
Recovery is rebuild-based.
```

This completes the Concrete API Design boundary for Phase 7 Step 10.
