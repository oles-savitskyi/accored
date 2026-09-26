# Phase 8 — Valuation Architecture Review + API Amendment

**Status:** Proposed Amendment — Pending Architecture Approval  
**Phase:** 8 — Valuation  
**Scope:** WP-3 preparation + Posting lifecycle integration contract  
**Baseline:** `AcCoreD_cur2.zip`, current Phase 7 Step 11 state  
**Implementation status:** Not authorized by this document

---

## 1. Review Objective

This review validates the Phase 8 Valuation Architecture Definition and Concrete API Design against the current Phase 7 implementation boundary before WP-3 implementation.

The review specifically checks:

1. FIFO determinism;
2. synthetic-consumption API boundaries;
3. valuation preflight semantics;
4. repost safety;
5. compatibility with the existing `PostingResultCoordinator` boundary;
6. preservation of Register/Valuation separation;
7. whether the approved API can actually be implemented without hidden state or valuation-specific knowledge inside `PostingEngine`.

---

## 2. Current Integration Point Findings

### 2.1 Existing Posting contract

The current Phase 7 public contract is:

```python
class PostingResultCoordinator(Protocol):
    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> None: ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None: ...
```

The current `PostingEngine` invokes `establish()` directly after movement validation and invokes `remove()` before `establish()` during repost.

### 2.2 Required Phase 8 invariant

Phase 8 requires the following invariant for repost:

```text
prepare(new)
    BEFORE
remove(old)
```

The reason is architectural, not merely implementation convenience: a deterministic valuation-domain failure for the replacement must not destroy an already successful posting.

### 2.3 Mismatch

The current `PostingResultCoordinator` has no preflight operation and no mechanism for transferring a prepared valuation plan into the later authoritative establishment step.

Therefore the currently documented Phase 8 API cannot be implemented faithfully while simultaneously satisfying all of these conditions:

* preserve the existing `PostingResultCoordinator` contract unchanged;
* perform valuation preparation before old-result removal;
* avoid re-running FIFO after Register mutation;
* avoid storing a hidden plan in mutable coordinator state;
* keep `PostingEngine` independent from valuation-specific types.

This is a **real architecture/API mismatch** and must be amended before integration implementation.

---

# 3. Architecture Review Decision

The review accepts the following architectural principles as sound and retains them unchanged:

* Register remains quantity-only.
* Valuation remains a separate semantic subsystem.
* `RegisterMutationOrchestrator` remains valuation-independent.
* `PostingEngine` remains the application lifecycle boundary.
* Valuation preparation is deterministic and non-authoritative.
* Valuation facts remain immutable and append-only.
* FIFO is a valuation method, not a persistence model.
* Synthetic consumption is explicit in the valuation API.
* `DocumentPosted` / `DocumentReposted` are emitted only after successful coordinated completion.
* Persistence indeterminacy remains distinct from deterministic domain failure.
* Unpost/repost use compensating valuation facts rather than mutation/deletion of historical valuation facts.

The review rejects only the **unchanged `PostingResultCoordinator` contract** as insufficient for the Phase 8 repost invariant.

---

# 4. API Amendment — Generic Posting Result Preparation

## 4.1 Design decision

Introduce a generic, valuation-agnostic `PostingResultPlan` boundary into the existing posting result coordination API.

The amended contract becomes:

```python
class PostingResultPlan(Protocol):
    """Opaque plan produced by posting-result preflight."""


class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> PostingResultPlan: ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> None: ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None: ...
```

`PostingEngine` knows only `PostingResultPlan`. It does **not** know `ValuationPlan`, FIFO, valuation layers, costs, or valuation persistence.

The plan is an opaque application-level hand-off object.

---

## 4.2 Why the amendment is preferable to hidden coordinator state

The alternative of having `prepare()` store a plan internally and having `establish()` retrieve it by document identity is rejected.

Such an approach would introduce:

* mutable cross-call coordinator state;
* lifecycle coupling between separate operations;
* ambiguous handling of concurrent reposts;
* possible stale-plan reuse;
* implicit rather than explicit plan ownership.

The amended API instead makes the hand-off explicit:

```text
prepare()
    ↓
PostingResultPlan
    ↓
remove(old) / establish(new, plan)
```

This is deterministic, testable, and does not require coordinator-local operation state.

---

# 5. Amended PostingEngine Lifecycle

## 5.1 POST

The lifecycle becomes:

```text
handler.post()
    ↓
MovementSet
    ↓
movement validation
    ↓
coordinator.prepare(document, movement_set)
    ↓
PostingResultPlan
    ↓
coordinator.establish(document, movement_set, plan)
    ↓
DocumentPosted
```

`prepare()` performs no authoritative Register or Valuation mutation.

If preparation fails, no result establishment occurs.

## 5.2 UNPOST

Unpost remains:

```text
coordinator.remove(document)
    ↓
DocumentUnposted
```

No preparation is required because unpost compensates an already-established result.

## 5.3 REPOST

The amended repost lifecycle is:

```text
handler.post()
    ↓
new MovementSet
    ↓
movement validation
    ↓
coordinator.prepare(document, new_movement_set)
    ↓
PostingResultPlan
    ↓
coordinator.remove(document)
    ↓
coordinator.establish(document, new_movement_set, plan)
    ↓
DocumentReposted
```

The mandatory invariant is:

```text
prepare(new) fails
        ⇒
remove(old) is not executed
```

The plan returned by `prepare()` is the explicit hand-off between preflight and authoritative establishment.

---

# 6. Composite Coordinator

The standard Phase 8 composition remains:

```text
CompositePostingResultCoordinator
    ├── RegisterPostingResultCoordinator
    └── ValuationPostingCoordinator
```

The amended responsibilities are:

### `prepare()`

```text
Composite.prepare(document, movement_set)
        │
        ├── Register.prepare(...)
        │
        └── Valuation.prepare(...)
                    ↓
             ValuationPlan
```

The composite returns an opaque composite `PostingResultPlan` containing the plans required by its child coordinators.

The Register coordinator has no valuation knowledge. For the current Register implementation its preparation can be a no-op plan.

### `establish()`

```text
Composite.establish(document, movement_set, plan)
        │
        ├── Register.establish(..., register_plan)
        │
        └── Valuation.establish(..., valuation_plan)
```

The valuation coordinator consumes the already-prepared `ValuationPlan`.

It must not re-run FIFO during `establish()`.

---

# 7. Error Semantics Amendment

Preparation errors are divided into two semantic classes.

### Deterministic preflight failure

Examples:

* valuation not applicable;
* insufficient valuation quantity;
* invalid valuation input;
* deterministic FIFO/domain validation failure.

These failures occur before authoritative result mutation.

The posting layer should expose a generic posting-level preparation failure, not a valuation-specific error type.

Recommended addition:

```python
class PostingPreparationError(PostingError):
    pass
```

`PostingEngine` therefore remains valuation-agnostic.

### Persistence indeterminacy

If preflight performs a read and the persistence layer reports an indeterminate condition, the operation must remain unsuccessful and must not proceed to authoritative establishment.

Existing mappings remain applicable:

```text
PersistenceError
    ↓
PostingPersistenceError

PersistenceIndeterminateError
    ↓
PostingIndeterminateError
```

The exact mapping of deterministic valuation-domain errors to `PostingPreparationError` is performed at the posting/valuation integration boundary, not inside `PostingEngine`.

---

# 8. Plan Validity Contract

A `PostingResultPlan` is valid only for the operation for which it was prepared.

At minimum, the concrete composite plan must bind to:

* document identity;
* movement identities / movement set generation;
* operation identity where required by the valuation plan.

`establish()` must reject a plan that does not correspond to its supplied document and movement set.

This prevents accidental reuse of a plan prepared for a different repost generation.

The generic `PostingResultPlan` remains opaque to `PostingEngine`.

---

# 9. FIFO Ordering Amendment

FIFO ordering must be explicit and deterministic.

For Phase 8 Inventory valuation, the canonical ordering is:

```text
1. valuation_key
2. created_at
3. layer identity string
```

Within one valuation request, layers are first restricted to the requested `ValuationKey` and then ordered by:

```python
(layer.created_at, str(layer.identity))
```

`valuation_key` is a selection criterion rather than a competing FIFO sequence when a request targets one key.

The identity tie-breaker is mandatory because two layers may have the same `created_at` value.

FIFO must never depend on:

* persistence enumeration order;
* dictionary insertion order;
* incidental collection ordering;
* runtime object identity;
* materialized cost balance;
* previous execution order.

This ordering rule is part of the public semantic contract and must be covered by unit tests.

---

# 10. WP-3 API Boundary

The generic posting-plan amendment does **not** expand WP-3 responsibilities.

WP-3 remains a pure valuation-domain work package.

The intended API boundary is:

```python
class ValuationMethod(Protocol):
    def value(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult: ...
```

and:

```python
class SyntheticConsumptionService:
    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult: ...
```

The exact final names may follow the existing foundation conventions, but the semantic rules are fixed here.

WP-3 must not:

* access `PostingEngine`;
* access `RegisterMutationOrchestrator`;
* persist valuation facts;
* mutate Register state;
* depend on `PostingResultPlan`;
* perform posting lifecycle coordination.

Those concerns belong to later work packages.

---

# 11. FIFO / Synthetic Consumption Semantics

For a consumption request of quantity `Q`, FIFO consumes available layer quantity in deterministic order.

For each consumed portion:

```text
consumed_cost = layer.total_cost × consumed_quantity / layer.quantity
```

The resulting consumption cost is the proportional cost attributable to the consumed quantity.

Example:

```text
Layer A: 10 units, total cost 100
Layer B: 20 units, total cost 300

Consume: 15 units
```

Result:

```text
Layer A: 10 units → cost 100
Layer B:  5 units → cost  75

Total quantity = 15
Total cost     = 175
```

Zero-cost layers are valid:

```text
Layer: 10 units, total cost 0
Consume: 4 units
Cost: 0
```

If the available quantity is insufficient, the operation fails deterministically with `ValuationInsufficientQuantityError` and produces no authoritative valuation mutation.

---

# 12. Revised Architecture Diagram

```text
                         PostingEngine
                              │
                              ▼
                 PostingResultCoordinator
                              │
                 ┌────────────┴────────────┐
                 │                         │
              prepare()                 remove()
                 │                         │
                 ▼                         ▼
        PostingResultPlan            compensation
                 │
                 ▼
             establish()
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
 Register Coordinator  Valuation Coordinator
        │                 │
        │             prepare()
        │                 │
        │                 ▼
        │           ValuationPlan
        │                 │
        └────────┬────────┘
                 ▼
          authoritative facts
```

For repost:

```text
new MovementSet
      ↓
validation
      ↓
prepare(new)
      ↓
PostingResultPlan
      ↓
remove(old)
      ↓
establish(new, plan)
      ↓
DocumentReposted
```

---

# 13. Impact on Existing Phase 7 API

This amendment intentionally changes the public `PostingResultCoordinator` contract.

The change is limited to the posting result coordination boundary:

### Before

```python
establish(document, movement_set)
remove(document)
```

### After

```python
prepare(document, movement_set) -> PostingResultPlan
establish(document, movement_set, plan)
remove(document)
```

The semantic responsibilities of Register coordination do not change.

`RegisterPostingResultCoordinator` remains responsible only for Register mutation and persistence lookup.

The Phase 7 tests that exercise the coordinator contract must therefore be amended as part of the Phase 8 integration work, rather than preserving an incompatible legacy signature through overloads or hidden state.

No compatibility shim is required unless the project later declares a separate external compatibility requirement.

---

# 14. Work Package Impact

| Work package | Impact |
|---|---|
| WP-0 Integration Verification | Update posting integration contract findings |
| WP-1 Domain Model | No semantic change |
| WP-2 Persistence Contracts | No semantic change |
| WP-3 FIFO / Synthetic Consumption | No dependency on posting amendment |
| WP-4 Valuation Engine / Plan | `ValuationPlan` remains the valuation-specific plan |
| WP-5 Valuation Coordinator | `prepare()` / `establish(plan)` remain required |
| WP-6 Posting Lifecycle Integration | **Amended:** introduce generic `PostingResultPlan` |
| WP-7 Standard Inventory Composition | Compose amended coordinator contract |
| WP-8 Reversal / Repost / Recovery | Repost safety now enforceable explicitly |
| WP-9 Queries / Rebuild | No semantic change |
| WP-10 Integration Tests | Add generic preflight/repost-plan tests |
| WP-11 Documentation | Reconcile Phase 8 and affected Phase 7 API docs |
| WP-12 Quality Gate | No change in gate criteria |
| WP-13 Final Review | Verify amendment is fully reconciled |

---

# 15. Architecture Acceptance Criteria for This Amendment

The amendment is accepted only if all of the following are true:

- [ ] `PostingResultCoordinator.prepare()` exists as a generic posting-level contract.
- [ ] `PostingResultPlan` is opaque to `PostingEngine`.
- [ ] `PostingResultCoordinator.establish()` receives the prepared plan explicitly.
- [ ] `PostingEngine` contains no valuation-specific types or logic.
- [ ] `prepare(new)` executes before `remove(old)` during repost.
- [ ] A failed deterministic preflight leaves the previous successful repost state untouched.
- [ ] No coordinator stores an implicit pending plan keyed only by document identity.
- [ ] The concrete plan cannot be reused for a different movement generation.
- [ ] Register coordination remains valuation-independent.
- [ ] Valuation `establish()` consumes its prepared `ValuationPlan` and does not re-run FIFO.
- [ ] FIFO ordering uses `(created_at, str(layer.identity))` after valuation-key selection.
- [ ] FIFO tests prove deterministic results for equal timestamps and reordered input collections.
- [ ] WP-3 remains independent from Posting and Register infrastructure.

---

# 16. Review Outcome

**Architecture review result:** `AMENDMENT REQUIRED BEFORE PHASE 8 POSTING INTEGRATION IMPLEMENTATION`

The valuation architecture itself remains approved in principle.

The blocking issue is the Phase 8 integration API mismatch with the actual Phase 7 posting boundary.

After approval of this amendment, implementation may proceed in the following order:

```text
Approve amendment
      ↓
Amend Concrete API Design
      ↓
Amend Implementation Plan status/scope
      ↓
WP-3 implementation
      ↓
WP-4+ implementation
      ↓
Phase 8 integration
```

No implementation change is authorized by this review document itself.
