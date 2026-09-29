# PHASE 8 — WP-8 Slice #9

# Derived State Rebuild / Recovery

## Architecture Definition / Scope

**Status:** Architecture Review Approved with Amendments
**Phase:** Phase 8 — Valuation Lifecycle / Reversal / Repost / Recovery
**Slice:** #9
**Predecessor:** Slice #8 — REMOVE Operation Recovery
**Implementation status:** Implemented; final documentation reconciliation completed

---

# 1. Purpose

Slice #9 formalizes deterministic reconstruction and reconciliation of valuation-derived state from immutable authoritative valuation history.

The architectural model is:

```text
ValuationFact
    ↓
deterministic derived projection
    ↓
CostMovement
    ↓
CostBalance
```

`ValuationFact` remains authoritative.

`CostMovement` and `CostBalance` remain derived/materialized state.

Derived state must therefore be:

* rebuildable;
* deterministic;
* repeatable;
* independent of existing derived-state contents;
* independent of persistence enumeration order;
* recoverable after partial persistence;
* incapable of modifying authoritative valuation history.

---

# 2. Architecture Review Decision

The Slice #9 Architecture Definition is approved with the following mandatory amendments.

## 2.1 CostMovement is historical derived projection

`CostMovement` represents the derived balance effect of valuation facts.

It is not merely a representation of the currently effective valuation state.

Therefore a reversal does not cause the original derived movement to disappear.

Instead:

```text
original fact
    ↓
original CostMovement

reversal fact
    ↓
compensating CostMovement
```

Both movements remain part of the derived movement history.

---

## 2.2 CostBalance is current aggregate

`CostBalance` is the current aggregate derived from the complete relevant `CostMovement` projection.

For example:

```text
Layer        +100
Consumption   -30
Reversal      +30
-----------------
Balance       +100
```

The original movement and compensating movement remain historically materialized.

The balance is the aggregate result.

---

# 3. Current Integration Points

## 3.1 Authoritative facts

The current project provides:

```python
class ValuationFactPersistence(Protocol):

    def find(
        self,
        identity: Identifier,
    ) -> ValuationFact | None:
        ...

    def find_by_valuation_key(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationFact, ...]:
        ...

    def enumerate(
        self,
    ) -> tuple[ValuationFact, ...]:
        ...
```

`enumerate()` is the primary full-rebuild input.

The rebuild service must reconstruct derived state from these facts.

---

## 3.2 Operation records

`ValuationOperationRecord` remains authoritative lifecycle history.

However, Slice #9 does not require operation records as the primary rebuild input.

Operation records may be used by separate consistency/audit validation.

The derived-state rebuild itself must be possible from authoritative valuation facts.

---

## 3.3 Valuation facts

The current fact model contains:

```text
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal
```

Slice #9 must not introduce new valuation fact types.

---

## 3.4 CostMovement

Current model:

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

Current identities are generated using `Identifier.new()`.

This is not sufficient for deterministic rebuild.

Slice #9 must introduce a deterministic derived-movement identity strategy.

The existing meaning of `source_identity` must not be changed merely to solve this problem.

---

## 3.5 CostBalance

Current model:

```python
@dataclass(frozen=True, slots=True)
class CostBalance:
    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    calculated_at: datetime
```

`CostBalance` is a replaceable derived aggregate.

Its semantic identity is the `ValuationKey`.

---

## 3.6 CostTotalsEngine

Current semantic boundary:

```python
class CostTotalsEngine(Protocol):

    def apply(
        self,
        movement: CostMovement,
    ) -> CostBalance:
        ...

    def remove(
        self,
        movement: CostMovement,
    ) -> CostBalance:
        ...

    def rebuild(
        self,
        valuation_key: ValuationKey,
        movements: Sequence[CostMovement],
    ) -> None:
        ...
```

This boundary is retained.

`CostTotalsEngine` remains responsible for aggregation of derived movements.

It must not interpret valuation facts or reversals.

---

## 3.7 ValuationResultPersistence

Current boundary:

```python
class ValuationResultPersistence(Protocol):

    def append_movements(...):
        ...

    def replace_balance(...):
        ...

    def find_movements(...):
        ...

    def find_balance(...):
        ...

    def enumerate_balances(...):
        ...
```

`append_movements()` is sufficient for incremental lifecycle materialization.

It is not sufficient to express complete derived-state reconciliation.

Slice #9 must therefore add a rebuild/reconciliation capability without conflating it with normal append semantics.

---

# 4. Core Architectural Model

The correct projection is:

```text
                 authoritative
                     facts
                       │
                       ▼
             fact → movement mapping
                       │
             ┌─────────┴─────────┐
             │                   │
       positive effect     compensating effect
             │                   │
             └─────────┬─────────┘
                       ▼
                 CostMovement
                       │
                       ▼
                 CostBalance
```

There is no requirement to first construct an "effective fact set" by removing reversed facts.

A reversal is itself an authoritative fact that produces a compensating derived movement.

---

# 5. Fact-to-Movement Projection

Slice #9 establishes a deterministic projection from authoritative valuation facts to derived movements.

For currently implemented valuation semantics:

## 5.1 Layer

A `ValuationLayer` produces a positive movement:

```text
quantity = +layer.quantity
cost     = +layer.total_cost
```

---

## 5.2 Consumption

A `ValuationConsumption` produces a negative movement:

```text
quantity = -consumption.quantity
cost     = -consumption.cost
```

---

## 5.3 Reversal

A `ValuationReversal` produces the compensating movement corresponding to the fact it reverses.

Conceptually:

```text
reverse(Layer +100)
    → +? compensation for the layer's balance effect

reverse(Consumption -30)
    → +30
```

The exact reconstruction algorithm for deriving the compensating amount belongs to Concrete API Design.

The essential architectural invariant is:

> A reversal remains an immutable authoritative fact and contributes a new compensating derived movement. The reversed movement is not deleted.

---

## 5.4 Adjustment / Allocation

`ValuationAdjustment` and `ValuationAllocation` are part of the existing valuation architecture.

Slice #9 must preserve their existing semantics.

No new adjustment/allocation semantics are introduced by this Slice.

Their inclusion in the derived projection must be explicitly covered by Concrete API Design and tests.

---

# 6. Historical Projection vs Current Balance

This distinction is mandatory.

### Historical derived projection

```text
ValuationFact history
        ↓
CostMovement history
```

### Current derived state

```text
CostMovement history
        ↓
CostBalance
```

Therefore:

```text
CostMovement != current effective state
```

and:

```text
CostBalance = aggregate of derived movement history
```

This distinction prevents rebuild from accidentally deleting historical compensating movements.

---

# 7. Deterministic CostMovement Identity

Every movement generated from authoritative history must have deterministic identity.

The identity must not depend on:

* `Identifier.new()`;
* rebuild invocation time;
* persistence enumeration order;
* existing derived-state contents;
* previous derived movement identity.

The identity must be derived from authoritative semantic provenance.

The expected conceptual model is:

```text
authoritative fact identity
        +
derived movement role
        ↓
deterministic CostMovement identity
```

The exact identity factory and semantic key are deferred to Concrete API Design.

The existing `source_identity` field retains its established provenance semantics.

---

# 8. Persistence Ordering Independence

Persistence enumeration order has no semantic meaning.

Therefore:

```text
facts = (A, B, C)
```

and:

```text
facts = (C, A, B)
```

must produce equivalent derived state.

If deterministic output ordering is required, the rebuild implementation must establish an explicit canonical ordering.

Enumeration order itself must never define semantics.

---

# 9. Full Rebuild

Full rebuild reconstructs all derived valuation state from authoritative valuation facts.

Conceptually:

```text
ValuationFactPersistence.enumerate()
        ↓
deterministic fact ordering
        ↓
fact → CostMovement projection
        ↓
CostMovement reconciliation
        ↓
CostBalance reconstruction
        ↓
CostBalance reconciliation
```

Existing derived state is not an input to the calculation of the expected result.

---

# 10. Scoped Rebuild

A scoped rebuild may target a specific `ValuationKey`.

However, the scoped rebuild must still derive the complete expected movement set for that scope from authoritative facts.

It must not derive the expected result by inspecting the existing materialized movements.

The exact scoped API is deferred to Concrete API Design.

---

# 11. Derived Movement Reconciliation

Rebuild is not equivalent to:

```python
append_movements(expected)
```

because append-only materialization would accumulate duplicates across repeated rebuilds.

The rebuild boundary must support semantic reconciliation:

```text
existing derived movements
            ↕
expected derived movements
```

The reconciliation must detect:

* missing movement;
* already-present identical movement;
* stale movement;
* conflicting identity/semantics.

The exact persistence API is deferred to Concrete API Design.

---

# 12. Derived Movement History Must Remain Complete

A successful rebuild must reproduce all derived movements represented by authoritative valuation history.

For:

```text
Layer
Consumption
Reversal
```

the expected movement projection contains all three corresponding effects.

It is incorrect for rebuild to discard the original movement merely because the original fact has subsequently been reversed.

This is the key correction from the initial Slice #9 draft.

---

# 13. Balance Reconstruction

For every affected `ValuationKey`:

```text
expected balance
    =
aggregate(expected CostMovements)
```

The existing balance must not be treated as an input.

A missing or stale balance must be replaced by the rebuilt balance.

---

# 14. Empty Derived Scope

If a valuation key has no derived movements, the resulting balance semantics must be explicitly defined.

Slice #9 adopts explicit zero-balance materialization for every valuation key participating in the rebuild scope.

For full rebuild, stale persisted balance keys are also included in the rebuild scope and are reconstructed as zero balances when no authoritative facts produce movements for them.

This preserves a deterministic materialized balance for every key represented by the rebuild scope.

---

# 15. Idempotency

Rebuild must be idempotent.

For unchanged authoritative history:

```text
rebuild(H)
rebuild(H)
```

must produce equivalent derived state.

In particular:

* no duplicate movements;
* no new identities;
* no accumulated balances;
* no new valuation operations;
* no new valuation facts.

---

# 16. Partial Derived Persistence

The following states are recoverable:

```text
facts complete
movements partial
balance missing
```

or:

```text
facts complete
movements complete
balance stale
```

or:

```text
facts complete
movements partial
balance stale
```

The rebuild must calculate expected derived state independently and reconcile the persisted projection to it.

---

# 17. Conflicting Derived Persistence

A derived movement with an existing deterministic identity but different semantics is a derived-state integrity failure.

The authoritative fact must not be changed to accommodate the conflict.

The rebuild result classifies the condition as `FAILURE`.

Unknown persistence state remains `INDETERMINATE`.

---

# 18. SUCCESS / FAILURE / INDETERMINATE

Slice #9 uses the established outcome model.

### SUCCESS

Expected derived state has been completely reconciled.

### FAILURE

The system knows that reconciliation cannot produce a valid derived state.

Examples:

* invalid authoritative fact relationship;
* deterministic movement identity conflict;
* contradictory authoritative valuation data.

### INDETERMINATE

The persistence outcome cannot be authoritatively established.

Examples:

* write outcome unknown;
* reconciliation read unavailable;
* persistence failure with unknown commit state.

`INDETERMINATE` must not be silently converted into successful completion.

---

# 19. No New Valuation Operations

Rebuild creates no:

```text
ValuationOperationRecord
```

It must not invoke:

```text
ESTABLISH
REMOVE
```

as a means of reconstructing state.

---

# 20. No New Valuation Facts

Rebuild creates no:

```text
ValuationFact
```

It must not repair authoritative history by inventing missing facts.

If authoritative history is invalid, rebuild reports the problem.

---

# 21. No Historical Mutation

Rebuild must not:

* update valuation facts;
* delete valuation facts;
* update operation records;
* delete operation records.

Authoritative history remains immutable.

---

# 22. Relationship to Slice #8

Slice #8:

```text
registered REMOVE operation
        ↓
recover missing authoritative reversal facts
```

Slice #9:

```text
complete authoritative fact history
        ↓
recover/rebuild derived CostMovement / CostBalance
```

These are different recovery layers.

Slice #9 must not duplicate operation recovery.

---

# 23. Relationship to Incremental Lifecycle

Normal lifecycle processing may continue to materialize movements incrementally:

```text
ESTABLISH
    ↓
append facts
    ↓
append CostMovements
    ↓
update balance
```

and:

```text
REMOVE
    ↓
append reversal facts
    ↓
append compensating CostMovements
    ↓
update balance
```

Slice #9 establishes the invariant:

```text
incremental materialization
        ≡
rebuild from authoritative facts
```

for the same authoritative history.

This is the principal correctness criterion of the Slice.

---

# 24. Relationship to CostTotalsEngine

`CostTotalsEngine` remains an aggregation component.

Its responsibility is:

```text
CostMovement
    ↓
CostBalance
```

It must not:

* inspect `ValuationFactPersistence`;
* interpret `ValuationReversal`;
* construct valuation facts;
* generate valuation operation identities;
* determine lifecycle semantics.

---

# 25. Proposed Service Boundary

Slice #9 introduces the following dedicated semantic service boundary:

```text
ValuationDerivedStateRebuildService
```

Its responsibility is:

```text
authoritative valuation facts
        ↓
deterministic movement projection
        ↓
derived movement reconciliation
        ↓
balance reconstruction
        ↓
derived balance reconciliation
```

It must not own:

* posting;
* valuation planning;
* operation registration;
* REMOVE target selection;
* authoritative fact recovery;
* database transaction management.

---

# 26. Proposed API Shape

The exact API is deferred to Concrete API Design.

The semantic boundary must support at least:

```text
rebuild()
```

and, if scoped rebuild is retained:

```text
rebuild(valuation_key)
```

The result must expose:

```text
SUCCESS
FAILURE
INDETERMINATE
```

plus sufficient diagnostic information to support recovery and testing.

---

# 27. Scope — Included

Slice #9 includes:

1. Derived-state rebuild boundary.
2. Authoritative-fact-only reconstruction.
3. Fact-to-movement projection.
4. Reversal movement reconstruction.
5. Deterministic CostMovement identity.
6. Persistence-order independence.
7. Full rebuild.
8. Optional scoped rebuild.
9. Derived movement reconciliation.
10. Balance reconstruction.
11. Balance reconciliation.
12. Missing derived-state recovery.
13. Detection of conflicting derived state.
14. SUCCESS / FAILURE / INDETERMINATE outcomes.
15. Rebuild idempotency.
16. Incremental/rebuild equivalence tests.
17. Partial-persistence tests.
18. Repeated-rebuild tests.
19. Documentation reconciliation.

---

# 28. Scope — Explicitly Excluded

Slice #9 does not include:

* new valuation lifecycle operations;
* new valuation fact types;
* mutation/deletion of valuation history;
* operation recovery redesign;
* REMOVE target reselection;
* distributed transactions;
* two-phase commit;
* saga/compensation;
* generic Posting changes;
* database-specific implementation;
* new valuation method;
* FIFO redesign;
* reconstruction of authoritative facts from derived state.

---

# 29. Architecture Acceptance Criteria

## AC-1 — Authoritative source

The expected derived result is calculated from authoritative valuation facts.

---

## AC-2 — Immutable history

Rebuild does not modify or delete authoritative history.

---

## AC-3 — Historical projection

Every valuation fact that produces a derived balance effect is represented by the corresponding deterministic CostMovement.

---

## AC-4 — Reversal projection

A `ValuationReversal` produces a compensating CostMovement.

The reversed movement is not deleted.

---

## AC-5 — Deterministic identity

The same authoritative fact history produces the same CostMovement identities.

---

## AC-6 — Enumeration-order independence

Changing persistence enumeration order does not change derived semantics or identities.

---

## AC-7 — Idempotency

Repeated rebuild does not create duplicate derived movements or balances.

---

## AC-8 — Partial-state recovery

Missing derived movements and balances can be reconstructed.

---

## AC-9 — Conflict detection

Conflicting derived state is detected rather than silently accepted.

---

## AC-10 — Balance correctness

Rebuilt balances equal aggregation of the complete expected CostMovement projection.

---

## AC-11 — Incremental equivalence

Incrementally materialized derived state equals state reconstructed from authoritative history.

---

## AC-12 — No lifecycle side effects

Rebuild creates no valuation operations and no valuation facts.

---

## AC-13 — Outcome semantics

Known deterministic errors produce `FAILURE`.

Unknown persistence state produces `INDETERMINATE`.

Successful reconciliation produces `SUCCESS`.

---

## AC-14 — Slice boundary

Slice #9 does not duplicate Slice #8 authoritative operation/fact recovery.

---

# 30. Resolved Concrete API Decisions

The following decisions are resolved by the implemented Concrete API Design:

1. deterministic `CostMovement` identity factory;
2. movement identity semantic key;
3. whether movement role/type becomes explicit;
4. exact mapping of every current `ValuationFact` type to `CostMovement`;
5. exact reversal reconstruction algorithm;
6. derived movement reconciliation protocol;
7. handling of stale movements;
8. handling of conflicting movement identities;
9. full vs scoped rebuild API;
10. empty-balance semantics;
11. balance reconciliation semantics;
12. `SUCCESS` / `FAILURE` / `INDETERMINATE` result model;
13. persistence failure classification;
14. interaction with `CostTotalsEngine.rebuild()`;
15. interaction with `DefaultValuationCoordinator`;
16. treatment of the existing `_rebuild_derived_state()` helper;
17. public exports;
18. test persistence contracts.

---

# 31. Final Architectural Invariant

The final Slice #9 invariant is:

```text
                    immutable
                 valuation facts
                       │
                       ▼
              deterministic projection
                       │
                       ▼
                CostMovement history
                       │
                       ▼
                  CostBalance
```

and:

```text
incremental lifecycle materialization
                ≡
rebuild(authoritative history)
```

while:

```text
derived state
      ↓
never
      ↓
authoritative history
```

This makes valuation-derived state a deterministic, recoverable projection of immutable valuation history.


---

# 32. Final Documentation Reconciliation

The Architecture Definition is reconciled with the implemented Slice #9 as follows:

1. `ValuationFact` remains the sole authoritative rebuild source.
2. `CostMovement` remains historical derived projection; reversal never removes the original movement.
3. `ValuationCostMovementRole` distinguishes deterministic ORIGINAL and REVERSAL movement identities.
4. `CostMovement.source_identity` retains its existing provenance meaning.
5. `ValuationResultPersistence.reconcile_movements()` is the implemented complete-projection reconciliation boundary; no separate derived-movement persistence object was introduced.
6. Full rebuild reconciles the complete movement projection and rebuilds all relevant balances, including stale persisted balance keys as explicit zero balances.
7. Scoped rebuild reconciles only the selected valuation key and materializes its resulting balance, including zero when the scoped projection is empty.
8. `ValuationAdjustment` remains non-materialized by itself; `ValuationAllocation` materializes its cost effect, matching the existing valuation fact semantics.
9. Incremental `DefaultValuationCoordinator` uses the same deterministic movement identity factory as rebuild for both layer and consumption movements, establishing incremental/rebuild identity equivalence.
10. Rebuild creates no operations or authoritative facts and does not mutate authoritative history.

The architecture therefore remains unchanged in boundary while the implementation now satisfies the approved Slice #9 projection and reconciliation model.
