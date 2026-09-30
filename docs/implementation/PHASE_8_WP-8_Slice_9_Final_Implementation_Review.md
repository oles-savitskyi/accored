# PHASE 8 — WP-8 Slice #9

# Final Implementation Review

**Status:** Final Slice 9 review complete; subsequent WP-8 slices preserved the reviewed architecture
**Scope:** Derived State Rebuild / Recovery
**Baseline:** `AcCoreD_cur9.zip`
**Architecture baseline:** `PHASE_8_WP-8_Slice_9_Derived_State_Rebuild_Recovery_Architecture_Definition_Scope.md`
**API baseline:** `PHASE 8_WP-8_Slice_9_Derived_State_Rebuild_Recovery_Concrete_API_Design.md`

---

## 1. Review Objective

Verify that the implemented Slice #9:

1. conforms to the approved architecture;
2. conforms to the Concrete API Design;
3. preserves the authoritative/derived-state boundary;
4. provides deterministic rebuild semantics;
5. preserves historical CostMovement projection semantics;
6. reconstructs compensating reversal movements from authoritative facts;
7. reconciles stale/conflicting derived state deterministically;
8. preserves incremental/rebuild equivalence;
9. does not duplicate Slice #8 operation/fact recovery;
10. is documented consistently with the final implementation.

---

## 2. Review Result

### Decision

**APPROVED**, with the two implementation corrections recorded in Section 6 applied to the reviewed snapshot.

The remaining release gate is the user's final local execution of the full quality-gate commands against the corrected snapshot.

---

## 3. Architecture Conformance

### 3.1 Authoritative source

Confirmed.

Rebuild reconstruction starts from `ValuationFactPersistence.enumerate()` for full rebuild and `find_by_valuation_key()` for scoped rebuild.

Existing `CostMovement` and `CostBalance` state is used only for reconciliation/materialization, never as the authoritative reconstruction source.

### 3.2 Historical derived movement model

Confirmed.

A reversal produces a compensating `CostMovement`; it does not remove or replace the original movement.

Therefore:

```text
original fact       → original movement
reversal fact       → compensating movement
complete projection → CostBalance
```

### 3.3 Reversal reconstruction

Confirmed.

`ValuationReversal.reversed_identity` is resolved through `ValuationFactPersistence`.

The reversal movement is reconstructed from the authoritative reversed fact, not from an existing derived movement.

Reversal-of-reversal remains rejected.

### 3.4 Deterministic movement identity

Confirmed.

`DefaultValuationCostMovementIdentityFactory` derives movement identity from authoritative fact identity plus movement role using canonical SHA-256 input.

The identity is independent of:

- timestamps;
- persistence order;
- process state;
- existing derived movement state;
- `Identifier.new()` output.

### 3.5 Provenance

Confirmed.

`CostMovement.source_identity` retains its established provenance meaning and is not repurposed as the deterministic movement identity.

### 3.6 Derived-state reconciliation

Confirmed.

`ValuationResultPersistence` now exposes:

- `find_movement()`;
- `enumerate_movements()`;
- `reconcile_movements()`;
- `enumerate_balances()`.

Incremental `append_movements()` remains semantically distinct from rebuild reconciliation.

### 3.7 Balance reconstruction

Confirmed after final correction.

Balances are rebuilt from the complete reconciled movement history through `CostTotalsEngine.rebuild()`.

Full rebuild also includes existing materialized balance keys in the rebuild scope, so stale balances for keys without an authoritative movement projection become explicit zero balances.

Scoped rebuild remains limited to the requested valuation key.

### 3.8 Authoritative history safety

Confirmed.

Rebuild creates no valuation operations, creates no authoritative facts, and does not update or delete authoritative history.

### 3.9 Slice boundary

Confirmed.

Slice #8 remains responsible for registered REMOVE operation recovery and authoritative reversal-fact recovery.

Slice #9 is responsible for reconstruction/reconciliation of derived CostMovement and CostBalance state.

---

## 4. Concrete API Conformance

The implementation provides the approved public abstractions:

```text
ValuationCostMovementRole
ValuationCostMovementIdentityFactory
DefaultValuationCostMovementIdentityFactory
ValuationFactToCostMovementProjector
DefaultValuationFactToCostMovementProjector
ValuationRebuilder
DefaultValuationRebuilder
ValuationRebuildOutcome
ValuationRebuildResult
```

The implemented orchestration boundary is:

```python
rebuild() -> ValuationRebuildResult
rebuild_for(valuation_key) -> ValuationRebuildResult
```

The existing cohesive `ValuationResultPersistence` contract was extended instead of introducing a parallel persistence abstraction.

---

## 5. Fact Projection Review

The current fact model is reconciled as follows:

| Authoritative fact | Derived projection |
|---|---|
| `ValuationLayer` | one `ORIGINAL` movement with layer quantity/cost |
| `ValuationConsumption` | one `ORIGINAL` movement with signed negative quantity/cost |
| `ValuationAdjustment` | no movement by itself; its effect is represented through allocation |
| `ValuationAllocation` | one `ORIGINAL` cost-effect movement with zero quantity |
| `ValuationReversal` | one `REVERSAL` movement compensating the authoritative reversed fact |

This mapping uses existing valuation semantics and does not introduce a new valuation method.

---

## 6. Final Review Corrections

Two implementation discrepancies were identified during final review.

### 6.1 Consumption movement identity

The initial Slice #9 implementation still constructed the incremental `ValuationConsumption` movement with `Identifier.new()`.

That violated the approved incremental/rebuild equivalence invariant.

Correction applied:

```python
self._movement_identity_factory.create(
    facts[-1],
    ValuationCostMovementRole.ORIGINAL,
)
```

The coordinator now uses the same deterministic identity strategy for layer and consumption movements as rebuild.

A test was added to compare the incrementally materialized consumption movement identity with the projector-generated identity.

### 6.2 Stale full-rebuild balances

The initial implementation rebuilt balances only for keys discovered from authoritative facts and expected movements.

That left a stale materialized balance untouched when its valuation key disappeared from the expected projection.

Correction applied:

```python
keys.update(
    balance.valuation_key
    for balance in self._result_persistence.enumerate_balances()
)
```

The full rebuild therefore reconstructs stale balance keys as deterministic zero balances when no authoritative movement projection exists.

A regression test was added for this case.

These corrections do not alter the approved architecture; they complete its intended semantics.

---

## 7. Reconciliation Semantics Review

### SUCCESS

Used when the requested derived projection and balances are successfully reconstructed/reconciled.

### FAILURE

Used for deterministic integrity/semantic failures, including:

- invalid authoritative fact relationships;
- unsupported fact semantics;
- deterministic identity conflicts;
- conflicting persisted derived movement semantics;
- missing authoritative reversed fact.

### INDETERMINATE

Used when persistence outcome cannot be authoritatively established.

This preserves the established valuation failure model and does not collapse unknown persistence state into deterministic failure.

---

## 8. Idempotency and Ordering Review

The implementation canonicalizes expected movements by deterministic movement identity before reconciliation.

Repeated rebuild therefore does not create new movement identities or duplicate derived history.

Fact enumeration order does not determine movement identity or semantic content.

`StandardValuationResultPersistence.reconcile_movements()` validates identity/content conflicts before replacing the materialized projection, so a deterministic conflict does not silently overwrite existing derived state.

---

## 9. Test Coverage Review

The Slice #9 test suite covers:

- deterministic movement identity;
- distinction between ORIGINAL and REVERSAL roles;
- reversal compensation;
- reversal-of-reversal rejection;
- missing authoritative reversal target;
- rebuild idempotency;
- persistence-order independence;
- stale derived movement reconciliation;
- conflicting derived movement detection;
- empty scoped balance reconstruction;
- stale full-rebuild balance reconstruction;
- allocation projection;
- incremental/rebuild movement identity equivalence;
- persistence contract extensions.

Before the two final review corrections, the user reported:

```text
pytest -q       → 1015 passed
ruff check .    → All checks passed
black --check . → 229 files unchanged
mypy src        → Success: no issues found in 125 source files
```

The reviewed snapshot contains two additional regression tests and two corresponding implementation corrections. The full quality gate must therefore be rerun locally after these changes.

---

## 10. Documentation Reconciliation

The Architecture Definition and Concrete API Design have been reconciled to the implementation.

Resolved documentation points include:

- implementation status changed from pre-implementation wording to implemented/reconciled status;
- persistence reconciliation is documented as an extension of `ValuationResultPersistence`;
- explicit zero-balance semantics are documented;
- stale full-rebuild balances are documented;
- `ValuationAdjustment` / `ValuationAllocation` projection semantics are documented;
- deterministic incremental consumption identity is documented;
- implementation-time API ambiguity has been removed.

---

## 11. Final Quality Gate

Required local commands after the final review corrections:

```bash
pytest -q
ruff check .
black --check .
mypy src
```

Expected outcome:

```text
pytest: PASS
ruff: PASS
black: PASS
mypy: PASS
```

No final commit should be created until all four commands pass against the corrected working tree.

---

## 12. Final Review Invariant

The reviewed Slice #9 satisfies the intended direction:

```text
immutable ValuationFact history
            ↓
 deterministic projection
            ↓
 historical CostMovement projection
            ↓
    CostTotalsEngine
            ↓
       CostBalance
```

and never:

```text
CostBalance / CostMovement
            ↓
 authoritative ValuationFact history
```

Subject to the final local quality-gate rerun, Slice #9 is ready for completion and commit as a coherent implementation/documentation unit.
