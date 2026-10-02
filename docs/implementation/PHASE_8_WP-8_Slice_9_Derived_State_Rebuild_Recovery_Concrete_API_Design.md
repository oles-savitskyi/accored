# PHASE 8 — WP-8 Slice #9: Derived State Rebuild / Recovery

## Concrete API Design

**Status:** Implemented and reconciled with the final Slice #9 implementation
**Scope:** Phase 8 / WP-8 / Slice #9
**Depends on:** Slice #1–#8
**Architectural baseline:** `PHASE_8_WP-8_Slice_9_Derived_State_Rebuild_Recovery_Architecture_Definition_Scope.md`
**Implementation policy:** architecture and Concrete API Design approved; implementation and final reconciliation completed.

---

## 1. Purpose

Slice #9 introduces a concrete API for reconstructing and reconciling derived valuation state from immutable authoritative valuation facts.

The implementation must establish the following equivalence:

```text
incremental lifecycle materialization
        ≡
rebuild(authoritative valuation history)
```

The rebuild source is:

```text
ValuationFact history
```

The derived target is:

```text
CostMovement history
        ↓
CostBalance
```

The rebuild must not:

* create valuation operations;
* create new valuation facts;
* mutate or delete authoritative valuation history;
* depend on existing derived state for reconstruction;
* treat existing `CostMovement` history as authoritative;
* use persistence enumeration order as semantic input.

---

# 2. Concrete API Overview

Slice #9 introduces four principal abstractions:

```text
ValuationFactToCostMovementProjector
        ↓
CostMovement candidates

ValuationDerivedMovementReconciler
        ↓
reconciled CostMovement history

ValuationBalanceRebuilder
        ↓
CostBalance

ValuationRebuilder
        ↓
orchestrates the complete process
```

The public orchestration API is:

```python
class ValuationRebuilder(Protocol):
    def rebuild(self) -> ValuationRebuildResult:
        ...

    def rebuild_for(
        self,
        valuation_key: ValuationKey,
    ) -> ValuationRebuildResult:
        ...
```

The implementation must remain independent from posting, document lifecycle, and valuation operation creation.

---

# 3. Result Model

Rebuild and reconciliation operations use the existing three-outcome model:

```python
class ValuationRebuildOutcome(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    INDETERMINATE = auto()
```

Result:

```python
@dataclass(frozen=True, slots=True)
class ValuationRebuildResult:
    outcome: ValuationRebuildOutcome
    rebuilt_valuation_keys: tuple[ValuationKey, ...] = ()
    error: Exception | None = None
```

The result must distinguish:

### SUCCESS

The requested derived scope has been reconciled and balances reconstructed.

### FAILURE

The system has authoritative evidence that the requested rebuild cannot be completed.

Examples:

* invalid valuation fact;
* unsupported fact semantics;
* duplicate deterministic movement identity with conflicting content;
* reversal references a missing authoritative fact;
* conflicting derived movement with the same deterministic identity;
* invalid balance state.

### INDETERMINATE

The system cannot determine whether the derived state was completely reconciled.

Examples:

* derived movement persistence failed without rollback guarantee;
* derived balance persistence failed after movement persistence succeeded;
* authoritative fact lookup became indeterminate;
* reconciliation after a persistence exception cannot establish final state.

`INDETERMINATE` must not be converted into `FAILURE` merely because the caller would prefer a definitive result.

---

# 4. Deterministic CostMovement Identity

## 4.1 New identity factory

A dedicated factory is introduced:

```python
class ValuationCostMovementIdentityFactory(Protocol):
    def create(
        self,
        fact: ValuationFact,
        role: ValuationCostMovementRole,
    ) -> Identifier:
        ...
```

Default implementation:

```python
class DefaultValuationCostMovementIdentityFactory:
    ...
```

The identity is deterministic.

Conceptually:

```text
CostMovement identity
=
canonical(
    authoritative fact identity,
    movement role
)
```

The identity must not contain:

* `Identifier.new()` output;
* current timestamp;
* persistence order;
* object memory address;
* current derived movement state.

The identity therefore remains stable across:

* incremental materialization;
* rebuild;
* recovery;
* process restart;
* persistence reload.

---

# 5. Movement Role

The deterministic identity requires an explicit semantic role.

```python
class ValuationCostMovementRole(Enum):
    ORIGINAL = "original"
    REVERSAL = "reversal"
```

The role is part of the movement identity.

This does **not** require `CostMovement` itself to expose a new public `role` field.

The role is projection metadata used to distinguish semantically different movements.

For normal valuation facts:

```text
fact → ORIGINAL movement
```

For `ValuationReversal`:

```text
reversal fact → REVERSAL movement
```

The existing:

```python
CostMovement.source_identity
```

is not changed in meaning.

It continues to identify the source/provenance of the movement.

---

# 6. CostMovement Identity Semantic Key

The identity factory canonical input is:

```python
{
    "fact_identity": str(fact.identity),
    "movement_role": role.value,
}
```

The canonical representation is hashed using the same deterministic SHA-256 canonicalization convention already established for valuation identities.

The resulting identifier must be stable and reproducible.

No operation identity is included directly.

The operation identity is already represented indirectly through deterministic authoritative fact identity where applicable.

---

# 7. Fact-to-Movement Projection

A separate projector encapsulates valuation semantics:

```python
class ValuationFactToCostMovementProjector(Protocol):
    def project(
        self,
        fact: ValuationFact,
        facts: ValuationFactPersistence,
    ) -> tuple[CostMovement, ...]:
        ...
```

Default implementation:

```python
class DefaultValuationFactToCostMovementProjector:
    ...
```

The projector is deliberately separate from rebuild orchestration.

Its responsibilities are:

1. validate that the fact can be projected;
2. determine the movement role;
3. determine movement quantity;
4. determine movement cost;
5. determine `valuation_key`;
6. preserve source provenance;
7. create deterministic movement identity;
8. reconstruct reversal effects from authoritative facts.

It must not:

* inspect `CostMovement` persistence;
* inspect `CostBalance`;
* modify totals;
* create valuation facts;
* create valuation operations.

---

# 8. Projection of Ordinary Valuation Facts

For every authoritative fact that represents a balance effect, the projector produces an `ORIGINAL` movement.

Conceptually:

```text
ValuationLayer
    ↓
CostMovement(ORIGINAL)

ValuationConsumption
    ↓
CostMovement(ORIGINAL)

ValuationAdjustment
    ↓
CostMovement(ORIGINAL)

ValuationAllocation
    ↓
CostMovement(ORIGINAL)
```

The exact field mapping must use the semantics already established by the existing valuation coordinator and fact models.

The implementation must not invent new valuation semantics as part of Slice #9.

If a currently defined fact type cannot be deterministically projected using its existing semantic fields, the projector must fail explicitly rather than silently producing an incomplete movement.

---

# 9. Reversal Projection

`ValuationReversal` does not replace its reversed fact.

Instead:

```text
original fact
        ↓
original CostMovement

ValuationReversal
        ↓
compensating CostMovement
```

Example:

```text
Layer       +100
Consumption  -30
Reversal     +30
----------------
Balance     +100
```

The original movements remain part of historical derived state.

The reversal movement compensates the effect of the reversed fact.

---

# 10. Reversal Reconstruction

For:

```python
ValuationReversal.reversed_identity
```

the projector performs an authoritative lookup:

```python
facts.find(reversal.reversed_identity)
```

The lookup source is `ValuationFactPersistence`.

The projector must not search `CostMovementPersistence`.

If the reversed fact is absent:

```text
FAILURE
```

If authoritative lookup is indeterminate:

```text
INDETERMINATE
```

The amount of the reversal movement is reconstructed from the authoritative reversed fact.

It is not reconstructed from an existing CostMovement.

This guarantees:

```text
rebuild
```

does not depend on whether the corresponding derived movement currently exists.

---

# 11. Reversal Restrictions

Slice #8 currently prevents reversal of `ValuationReversal`.

Slice #9 preserves that invariant.

Therefore the projector may require:

```text
reversed fact != ValuationReversal
```

If a persisted authoritative history violates this invariant, projection fails deterministically.

No recursive reversal-chain reconstruction is introduced in Slice #9.

---

# 12. CostMovement Construction

The resulting model remains:

```python
@dataclass(frozen=True, slots=True)
class CostMovement:
    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

Construction rules:

### `identity`

Deterministic identity produced by:

```python
ValuationCostMovementIdentityFactory
```

### `valuation_key`

Taken from authoritative valuation semantics.

### `quantity`

Signed balance effect.

### `cost`

Signed cost effect.

### `source_identity`

Existing provenance semantics are preserved.

For an ordinary fact:

```text
source_identity = fact.source_identity
```

For a reversal:

```text
source_identity = reversal.source_identity
```

The source identity is therefore **not** repurposed as the deterministic movement identity.

### `created_at`

Derived deterministically from the authoritative fact.

No rebuild timestamp is introduced into movement semantic content.

---

# 13. Projection Result

The projector may produce zero or more movements:

```python
tuple[CostMovement, ...]
```

For the current supported valuation fact model, ordinary balance-affecting facts produce exactly one movement.

The tuple return type is intentional because it prevents the orchestration layer from encoding an assumption that can later conflict with valuation semantics.

---

# 14. Derived Movement Reconciliation

The existing:

```python
ValuationResultPersistence.append_movements()
```

remains the incremental lifecycle materialization operation. It is intentionally distinct from rebuild reconciliation.

Slice #9 extends the existing cohesive `ValuationResultPersistence` contract with:

```python
def find_movement(
    self,
    identity: Identifier,
) -> CostMovement | None: ...

def enumerate_movements(
    self,
) -> tuple[CostMovement, ...]: ...

def reconcile_movements(
    self,
    movements: Sequence[CostMovement],
) -> None: ...
```

The implementation does not introduce a separate derived-movement persistence object. Reconciliation validates deterministic identity/content conflicts and then replaces the complete materialized movement projection.

# 15. Why `enumerate_movements()` Is Required

The current persistence API has:

```python
find_movements(valuation_key)
```

but no global movement enumeration.

Full rebuild must be able to detect derived state that has no corresponding current projection.

Therefore the persistence contract must provide:

```python
enumerate_movements()
```

This is required for complete full-scope reconciliation.

Without it, the implementation cannot detect a stale derived movement whose valuation key is absent from the authoritative projection.

---

# 16. Reconciliation Semantics

Reconciliation compares:

```text
expected deterministic movement set
```

against:

```text
persisted derived movement set
```

using:

```python
CostMovement.identity
```

as the primary identity.

For each expected movement:

### Missing

Append/persist it.

### Present and semantically identical

Treat as already reconciled.

### Present with same identity but different semantics

Return:

```text
FAILURE
```

This is a derived-state conflict.

The system must never silently overwrite a movement with the same deterministic identity but different content.

---

# 17. Stale Derived Movements

A persisted movement is stale when:

```text
persisted movement identity
```

does not occur in the authoritative expected projection for the rebuilt scope.

Because `CostMovement` is derived rather than authoritative, stale derived state may be physically replaced during reconciliation.

The concrete persistence API therefore supports:

```python
reconcile(movements)
```

as a projection-replacement operation for the requested scope.

The operation must not mutate authoritative valuation facts.

---

# 18. Scope of Reconciliation

For:

```python
rebuild_for(valuation_key)
```

only movements belonging to that valuation key are reconciled.

The implementation must:

1. construct the expected movement set for the key;
2. load persisted movements for the key;
3. compare identities;
4. add missing movements;
5. detect conflicting identities;
6. remove/replace stale derived movements for that key;
7. rebuild the corresponding balance.

For:

```python
rebuild()
```

the entire derived movement projection is reconciled, and all valuation keys represented by authoritative facts, expected movements, or existing materialized balances are rebuilt. Existing balance keys with no authoritative movement projection become explicit zero balances.

---

# 19. Full Rebuild

Full rebuild follows:

```text
enumerate authoritative facts
        ↓
project every fact
        ↓
canonicalize movement set
        ↓
reconcile complete CostMovement history
        ↓
rebuild CostBalance for every affected valuation key
```

The expected movement set is constructed independently of the existing derived state.

Existing movements are only comparison/reconciliation input.

They are never reconstruction input.

---

# 20. Persistence Ordering Independence

Fact enumeration order must not affect the resulting derived state.

Before reconciliation:

```python
expected_movements
```

must be canonicalized by deterministic identity:

```python
tuple(
    sorted(
        movements,
        key=lambda movement: str(movement.identity),
    )
)
```

Duplicate deterministic identities must be detected.

Two identical occurrences with identical semantics may be treated idempotently.

The same identity with different semantics is:

```text
FAILURE
```

---

# 21. Duplicate Movement Identity

During projection, if two independently projected facts produce the same movement identity:

### Identical semantics

The duplicate is collapsed idempotently.

### Different semantics

Rebuild returns:

```text
FAILURE
```

The implementation must not choose one arbitrarily.

---

# 22. Balance Reconstruction

After the movement projection has been reconciled, balance is rebuilt from the complete movement history.

The existing totals subsystem remains responsible for aggregation:

```python
CostTotalsEngine.rebuild(
    valuation_key,
    movements,
)
```

The totals engine does not inspect valuation facts.

It receives only:

```text
CostMovement
```

history.

---

# 23. Important Distinction: Historical Movement vs Current Balance

The following must remain true:

```text
CostMovement history
```

contains all materialized balance effects.

`CostBalance` represents the aggregate current result.

Therefore:

```text
Layer +100
Consumption -30
Reversal +30
```

produces:

```text
CostMovement history:
    +100
    -30
    +30

CostBalance:
    +100
```

Rebuild must never reduce the movement history to only:

```text
+100
```

because that would destroy the historical derived representation.

---

# 24. Balance Persistence

The existing balance model remains:

```python
@dataclass(frozen=True, slots=True)
class CostBalance:
    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    calculated_at: datetime
```

`calculated_at` is derived metadata.

It is not part of semantic equality for reconciliation.

Therefore two balances are semantically equivalent when:

```text
valuation_key
quantity
cost
```

are equal.

A rebuild may produce a new `calculated_at` value without constituting a semantic conflict.

---

# 25. Empty Balance Semantics

For a valuation key participating in rebuild but having no effective movements, the totals engine determines the zero balance:

```text
quantity = Decimal("0")
cost = Decimal("0")
```

The balance remains materialized for the requested valuation key.

For full rebuild, an existing materialized balance key also participates in the rebuild scope, so stale derived balances are replaced by deterministic zero balances when no authoritative movement projection exists.

A valuation key that is neither authoritative nor previously materialized is not implicitly created by full rebuild.

---

# 26. Balance Persistence Reconciliation

Balance persistence remains replacement-oriented:

```python
replace_balance(balance)
```

Before replacement, an existing balance is not authoritative.

The rebuilt balance is authoritative for the derived scope.

If balance persistence succeeds:

```text
SUCCESS
```

If it fails and the final state cannot be established:

```text
INDETERMINATE
```

A persistence exception must not be reported as `FAILURE` merely because the operation did not return normally.

---

# 27. Partial Derived Persistence

A rebuild can partially persist derived movements before an exception.

The implementation must therefore be recovery-safe.

On a subsequent rebuild:

```text
authoritative facts
        ↓
deterministic projection
        ↓
reconciliation
```

must converge to the same derived state.

No special recovery operation or new valuation operation is required.

This is the primary recovery mechanism of Slice #9.

---

# 28. Rebuild Idempotency

Repeated execution:

```python
rebuild()
rebuild()
rebuild()
```

must converge to the same semantic derived state.

Repeated execution must not:

* create duplicate movements;
* create duplicate facts;
* create valuation operations;
* change movement identities;
* change movement quantities/costs;
* depend on previous execution order.

`calculated_at` may change because it is non-semantic metadata.

---

# 29. Operation Records Are Not Rebuild Input

`ValuationOperationRecord` is not required to reconstruct derived state.

The authoritative reconstruction source is:

```text
ValuationFactPersistence
```

Operation records may be used by a higher-level audit/consistency facility, but Slice #9 does not require operation-record reconstruction.

In particular:

```text
missing operation record
```

must not prevent rebuilding valid immutable valuation facts.

---

# 30. Proposed Rebuilder API

```python
class ValuationRebuilder(Protocol):
    def rebuild(self) -> ValuationRebuildResult:
        ...

    def rebuild_for(
        self,
        valuation_key: ValuationKey,
    ) -> ValuationRebuildResult:
        ...
```

Implementation:

```python
class DefaultValuationRebuilder:
    def __init__(
        self,
        fact_persistence: ValuationFactPersistence,
        result_persistence: ValuationResultPersistence,
        projector: ValuationFactToCostMovementProjector,
        totals_engine: CostTotalsEngine,
    ) -> None:
        ...
```

The implementation may depend on a more specific derived reconciliation protocol if the existing `ValuationResultPersistence` is extended accordingly.

---

# 31. Full Rebuild Algorithm

Conceptual implementation:

```python
def rebuild(self) -> ValuationRebuildResult:
    facts = self._fact_persistence.enumerate()

    expected_movements = self._project_facts(facts)

    reconciliation = self._reconcile_all(expected_movements)

    if reconciliation.outcome is not SUCCESS:
        return map_result(reconciliation)

    valuation_keys = self._valuation_keys(expected_movements)

    for valuation_key in valuation_keys:
        movements = self._result_persistence.find_movements(
            valuation_key
        )

        balance = self._totals_engine.rebuild(
            valuation_key,
            movements,
        )

        self._result_persistence.replace_balance(balance)

    return success(...)
```

The final implementation must also account for valuation keys whose expected movement set is empty but which are part of the explicitly rebuilt scope.

The actual persistence transaction/error boundaries are defined below.

---

# 32. Scoped Rebuild Algorithm

Conceptual flow:

```text
authoritative facts
        ↓
filter by valuation key
        ↓
project
        ↓
reconcile movements for key
        ↓
load reconciled movements
        ↓
CostTotalsEngine.rebuild()
        ↓
replace CostBalance
```

The filter must be applied to authoritative facts, not to existing derived movements.

---

# 33. Reversal Projection Algorithm

For a `ValuationReversal`:

```text
1. Read reversal.reversed_identity.
2. Find the reversed authoritative fact.
3. If absent → FAILURE.
4. If lookup is indeterminate → INDETERMINATE.
5. Project the reversed fact's balance effect.
6. Invert the projected quantity/cost.
7. Construct a new movement:
       identity = movement identity of reversal fact + REVERSAL role
       valuation_key = reversal valuation key
       source_identity = reversal.source_identity
       created_at = reversal.created_at
8. Return the compensating movement.
```

The reversal movement's deterministic identity is based on the reversal fact itself, not on the identity of the reversed movement.

This guarantees that one reversal fact corresponds to one stable compensating movement.

---

# 34. Why the Reversal Movement Does Not Reuse the Original Identity

The original movement:

```text
identity = f(original fact identity, ORIGINAL)
```

The reversal movement:

```text
identity = f(reversal fact identity, REVERSAL)
```

Therefore:

```text
original movement ≠ reversal movement
```

even though their effects may be equal and opposite.

This preserves both:

* historical representation;
* deterministic idempotency.

---

# 35. Error Mapping

## Authoritative fact lookup

```text
not found
    → FAILURE

indeterminate lookup
    → INDETERMINATE
```

## Projection validation

```text
invalid fact
    → FAILURE
```

## Derived movement conflict

```text
same identity + different semantics
    → FAILURE
```

## Derived movement persistence

```text
successful persistence
    → continue

known rollback-guaranteed failure
    → FAILURE

unknown final state
    → INDETERMINATE
```

## Balance persistence

```text
successful replacement
    → SUCCESS

known rollback-guaranteed failure
    → FAILURE

unknown final state
    → INDETERMINATE
```

---

# 36. Atomicity Boundary

Slice #9 does not introduce a distributed transaction.

The rebuild therefore does not promise atomicity across:

```text
movement persistence
+
balance persistence
```

Instead it guarantees:

1. deterministic reconstruction;
2. idempotent reconciliation;
3. safe retry;
4. explicit `INDETERMINATE` classification when final persistence state cannot be established.

A later rebuild must be sufficient to converge the derived state.

---

# 37. Existing `DefaultValuationCoordinator` Integration

The existing helper:

```python
DefaultValuationCoordinator._rebuild_derived_state(...)
```

must be reviewed during implementation.

It currently means:

```text
apply supplied movements to current totals
replace balances
```

It does **not** implement historical rebuild.

It must therefore not be reused as the Slice #9 rebuild service unless its semantics are changed explicitly.

Preferred boundary:

```text
DefaultValuationCoordinator
    → incremental lifecycle materialization

DefaultValuationRebuilder
    → authoritative-history reconstruction
```

The two paths share:

```text
CostMovement
CostTotalsEngine
ValuationResultPersistence
```

but not rebuild orchestration.

---

# 38. Incremental Lifecycle Compatibility

The existing incremental lifecycle remains responsible for materializing newly established/reversed valuation effects.

It must continue to create deterministic CostMovement identities using the same identity factory as rebuild.

Therefore:

```text
incremental path
    +
rebuild path
```

must produce semantically identical movement identity and movement content for the same authoritative fact.

This is the central integration requirement.

---

# 39. Required Coordinator Change

Where the existing coordinator currently does:

```python
Identifier.new()
```

for `CostMovement.identity`, it must be replaced by:

```python
ValuationCostMovementIdentityFactory.create(...)
```

with the appropriate role.

This is required to make incremental materialization and rebuild converge.

No other existing `Identifier.new()` usage should be changed merely for stylistic consistency.

---

# 40. Public API Placement

The new public abstractions should live within the existing valuation package rather than creating a separate top-level subsystem.

Expected public surface:

```python
ValuationCostMovementRole
ValuationCostMovementIdentityFactory
DefaultValuationCostMovementIdentityFactory

ValuationFactToCostMovementProjector
DefaultValuationFactToCostMovementProjector

ValuationRebuildOutcome
ValuationRebuildResult

ValuationRebuilder
DefaultValuationRebuilder
```

Exact module placement must follow the existing valuation package organization.

Internal helpers should remain private.

---

# 41. Persistence API Amendment

The existing result persistence contract must be extended to support deterministic reconciliation.

At minimum:

```python
def find(
    self,
    identity: Identifier,
) -> CostMovement | None:
    ...

def enumerate_movements(
    self,
) -> tuple[CostMovement, ...]:
    ...

def reconcile_movements(
    self,
    movements: Sequence[CostMovement],
) -> None:
    ...
```

The existing methods remain:

```python
append_movements(...)
replace_balance(...)
find_movements(...)
find_balance(...)
enumerate_balances(...)
```

unless implementation review demonstrates that a cohesive renamed/restructured interface is cleaner.

The important architectural requirement is that incremental append and rebuild reconciliation remain semantically distinct.

---

# 42. Reconciliation Contract

The reconciliation operation:

```python
reconcile_movements(...)
```

must have these semantics:

```text
Input:
    complete expected derived projection

Effect:
    persisted movement projection becomes equivalent
    to expected projection for the selected scope
```

It must be:

* deterministic;
* idempotent;
* order-independent;
* conflict-detecting;
* retry-safe.

It must not use append-only semantics blindly.

---

# 43. Stale Movement Replacement

For a scoped rebuild:

```text
expected movement identities
```

replace the movement projection for that valuation key.

For a full rebuild:

```text
expected movement identities
```

replace the complete movement projection.

The implementation may internally optimize this into:

```text
append missing
remove stale
retain identical
```

but the public semantic contract is projection reconciliation.

---

# 44. No Authoritative Deletion

The word “remove” in derived movement reconciliation refers only to:

```text
derived CostMovement persistence
```

It must never mean:

```text
delete ValuationFact
delete ValuationReversal
delete ValuationOperationRecord
```

Authoritative history remains immutable.

---

# 45. Tests — Identity

Required tests:

1. identical fact produces identical movement identity;
2. repeated projection produces identical identity;
3. same fact with different persistence order produces identical identity;
4. original and reversal roles produce different identities;
5. `Identifier.new()` is not involved;
6. `source_identity` remains unchanged;
7. identity does not depend on `created_at`;
8. identity does not depend on current derived state.

---

# 46. Tests — Projection

Required tests:

1. Layer projection;
2. Consumption projection;
3. Adjustment projection;
4. Allocation projection;
5. Reversal projection;
6. missing reversed fact;
7. indeterminate reversed-fact lookup;
8. unsupported reversal target;
9. signed reversal effect;
10. deterministic projection independent of fact enumeration order.

---

# 47. Tests — Reconciliation

Required tests:

1. missing movement is appended;
2. identical movement is idempotently accepted;
3. conflicting movement identity produces `FAILURE`;
4. stale movement is removed/replaced;
5. complete projection remains complete after reconciliation;
6. duplicate expected identity with identical semantics is accepted;
7. duplicate expected identity with conflicting semantics fails;
8. reconciliation is order-independent;
9. partial persistence followed by retry converges.

---

# 48. Tests — Balance

Required tests:

1. balance rebuilt from complete movement history;
2. reversal movement compensates original movement;
3. original reversed movement remains present;
4. zero balance is materialized for an explicitly rebuilt empty key;
5. `calculated_at` does not create semantic conflict;
6. repeated rebuild produces equivalent balance values;
7. movement history and balance remain consistent.

---

# 49. Tests — Full Rebuild

At minimum:

```text
Layer +100
Consumption -30
Reversal +30
```

must result in:

```text
CostMovement history:
    +100
    -30
    +30

CostBalance:
    quantity = +100
    cost = corresponding aggregate
```

The original Layer and Consumption movements must remain persisted.

---

# 50. Tests — Incremental/Rebuild Equivalence

A mandatory integration scenario:

```text
1. establish valuation
2. materialize incrementally
3. capture derived state
4. discard derived state
5. rebuild from immutable facts
6. compare states
```

Expected:

```text
incremental derived state
==
rebuilt derived state
```

Comparison must use semantic movement identity/content and semantic balance fields.

`calculated_at` is excluded from semantic equality.

---

# 51. Tests — Rebuild After Partial Persistence

Scenario:

```text
projection
    ↓
partial movement persistence
    ↓
failure / INDETERMINATE
    ↓
rebuild()
```

Expected:

```text
complete deterministic derived state
```

No duplicate movement identities may result.

---

# 52. Tests — Persistence Order

Authoritative fact persistence order must be permuted.

Example:

```text
A, B, C
C, A, B
B, C, A
```

All rebuilds must produce equivalent:

```text
CostMovement history
CostBalance
```

The persistence order itself must have no semantic effect.

---

# 53. Tests — Full Rebuild Stale State

Persist a movement that has no corresponding authoritative projection.

Run:

```python
rebuild()
```

Expected:

```text
stale movement no longer belongs to derived projection
```

No authoritative fact is modified.

---

# 54. Tests — Empty State

For a valid empty derived scope:

```python
rebuild_for(valuation_key)
```

must result in:

```text
no CostMovement
zero CostBalance
```

where the valuation key is explicitly part of the rebuild scope.

For completely unknown valuation keys, the implementation must not invent valuation history.

---

# 55. Non-Goals

Slice #9 does not implement:

* database transactions;
* distributed transactions;
* 2PC;
* saga orchestration;
* mutable valuation history;
* valuation fact deletion;
* operation record creation during rebuild;
* new valuation algorithms;
* FIFO redesign;
* costing-method redesign;
* posting semantics;
* register semantics;
* generic persistence transaction framework.

---

# 56. Implementation Constraints

Implementation must preserve:

```text
authoritative facts
    immutable

derived movements
    deterministic

balances
    rebuildable
```

No shortcut is allowed that reconstructs state from existing `CostMovement` records instead of authoritative facts.

In particular, this is prohibited:

```python
existing_movements
    → infer missing facts
    → rebuild
```

The permitted direction is:

```python
facts
    → movements
    → balance
```

---

# 57. Required Integration Points

Before implementation, verify the following concrete points in the current repository:

### Valuation facts

* `ValuationFactPersistence.enumerate()`
* `ValuationFactPersistence.find()`
* all current fact dataclasses;
* fact identity factory.

### Derived results

* `CostMovement`;
* `CostBalance`;
* `ValuationResultPersistence`;
* `StandardValuationResultPersistence`.

### Totals

* `CostTotalsEngine.apply()`;
* `CostTotalsEngine.remove()`;
* `CostTotalsEngine.rebuild()`.

### Incremental coordinator

* `DefaultValuationCoordinator._construct()`;
* `DefaultValuationCoordinator._build_reversals()`;
* `_rebuild_derived_state()`.

### Public exports

* valuation package `__init__`;
* existing persistence exports;
* existing coordinator exports.

---

# 58. Implementation Order

Implementation should proceed in this order:

### Step 1 — Movement identity

Add:

```text
ValuationCostMovementRole
ValuationCostMovementIdentityFactory
DefaultValuationCostMovementIdentityFactory
```

and migrate incremental movement construction to deterministic identities.

### Step 2 — Projection

Implement:

```text
ValuationFactToCostMovementProjector
```

including reversal reconstruction.

### Step 3 — Persistence reconciliation

Extend result persistence with:

```text
find movement
enumerate movements
reconcile movement projection
```

### Step 4 — Rebuild service

Implement:

```text
ValuationRebuildOutcome
ValuationRebuildResult
ValuationRebuilder
DefaultValuationRebuilder
```

### Step 5 — Balance reconstruction

Integrate:

```text
CostTotalsEngine.rebuild()
```

with reconciled movement history.

### Step 6 — Incremental/rebuild equivalence

Verify that incremental and rebuild paths use the same deterministic identity semantics.

### Step 7 — Integration tests

Add full rebuild, scoped rebuild, reversal, stale-state, partial-persistence, and equivalence tests.

---

# 59. Acceptance Criteria

Slice #9 is complete only when all of the following are true.

## Identity

* [ ] CostMovement identities are deterministic.
* [ ] Identity is independent of persistence order.
* [ ] Identity is independent of current derived state.
* [ ] Original and reversal roles are distinguishable.
* [ ] `source_identity` semantics are preserved.

## Projection

* [ ] Every supported authoritative fact has deterministic projection semantics.
* [ ] Reversal projection uses authoritative reversed fact.
* [ ] Reversal does not delete or replace original movement.
* [ ] Unsupported/corrupt authoritative state fails deterministically.

## Reconciliation

* [ ] Missing movements are materialized.
* [ ] Identical movements are idempotent.
* [ ] Conflicting identities produce `FAILURE`.
* [ ] Stale derived movements are reconciled.
* [ ] Full reconciliation is order-independent.

## Balance

* [ ] Balance is rebuilt from complete movement history.
* [ ] Reversal effects are included.
* [ ] Historical movements remain complete.
* [ ] Empty explicit scopes produce deterministic zero balances.
* [ ] `calculated_at` is non-semantic.

## Recovery

* [ ] Partial derived persistence is retry-safe.
* [ ] `INDETERMINATE` is preserved where final state cannot be established.
* [ ] Rebuild converges after retry.
* [ ] No new valuation operations are created.
* [ ] No new valuation facts are created.

## Architectural integrity

* [ ] `CostTotalsEngine` remains valuation-agnostic.
* [ ] `ValuationFact` remains authoritative.
* [ ] Derived state never becomes authoritative input.
* [ ] Incremental and rebuild paths produce equivalent derived state.
* [ ] Existing Slice #8 recovery semantics remain unchanged.

---

# 60. Final API Shape

The intended public API after Slice #9 is conceptually:

```python
class ValuationCostMovementIdentityFactory(Protocol):
    def create(
        self,
        fact: ValuationFact,
        role: ValuationCostMovementRole,
    ) -> Identifier:
        ...


class ValuationFactToCostMovementProjector(Protocol):
    def project(
        self,
        fact: ValuationFact,
        facts: ValuationFactPersistence,
    ) -> tuple[CostMovement, ...]:
        ...


class ValuationRebuilder(Protocol):
    def rebuild(self) -> ValuationRebuildResult:
        ...

    def rebuild_for(
        self,
        valuation_key: ValuationKey,
    ) -> ValuationRebuildResult:
        ...


class ValuationResultPersistence(Protocol):
    def append_movements(
        self,
        movements: Sequence[CostMovement],
    ) -> None:
        ...

    def find_movement(
        self,
        identity: Identifier,
    ) -> CostMovement | None:
        ...

    def find_movements(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[CostMovement, ...]:
        ...

    def enumerate_movements(
        self,
    ) -> tuple[CostMovement, ...]:
        ...

    def reconcile_movements(
        self,
        movements: Sequence[CostMovement],
    ) -> None:
        ...

    def replace_balance(
        self,
        balance: CostBalance,
    ) -> None:
        ...

    def find_balance(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance | None:
        ...

    def enumerate_balances(
        self,
    ) -> tuple[CostBalance, ...]:
        ...
```

The method names above are the implemented public contract; no implementation-time API variation remains.

---

# 61. Final Concrete Invariant

After Slice #9:

```text
ValuationFact
    ↓
deterministic projection
    ↓
CostMovement history
    ↓
CostTotalsEngine
    ↓
CostBalance
```

must be reproducible at any time.

More precisely:

```text
same immutable valuation facts
        +
same projection rules
        ↓
same CostMovement identities/content
        ↓
same CostBalance values
```

regardless of:

* process restart;
* persistence enumeration order;
* previous derived-state contents;
* partial previous rebuild;
* previous incremental materialization.

The authoritative direction remains strictly:

```text
ValuationFact
    ↓
CostMovement
    ↓
CostBalance
```

and never:

```text
CostBalance
    ↓
CostMovement
    ↓
ValuationFact
```

or:

```text
CostMovement
    ↓
ValuationFact
```

This is the implemented and reconciled concrete API boundary for Slice #9.
