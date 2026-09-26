# Phase 8 — WP-4 Valuation Engine and Plan

## Final Architecture Definition / Scope

**Status:** Architecture Approved
**Phase:** Phase 8 — Valuation
**Work Package:** WP-4 — Valuation Engine and Plan
**Predecessor:** WP-3 — FIFO and Synthetic Consumption
**Next:** WP-5 — Valuation Coordinator

---

## 1. Purpose

WP-4 introduces the valuation preparation layer between inventory movements and the future `ValuationCoordinator`.

The purpose of WP-4 is to transform an already validated `MovementSet` into a deterministic, immutable `ValuationPlan` without changing authoritative valuation state.

The preparation pipeline is:

```text
MovementSet
    ↓
ValuationInputProvider
    ↓
ValuationInput
    ↓
ValuationMethod
    ↓
ValuationPlan
```

WP-4 establishes the **valuation preparation boundary**.

It does not establish authoritative valuation state.

---

## 2. Architectural Objective

The primary architectural objective is to provide a safe preflight operation that can be executed before an existing posting result is removed.

The required lifecycle property is:

```text
prepare(new MovementSet)
        ↓
success
        ↓
remove(old result)
        ↓
establish(new result, prepared plan)
```

If preparation fails:

```text
prepare(new MovementSet)
        ↓
failure
        ↓
old result remains untouched
```

Therefore valuation preparation must be completed before destructive repost operations.

This requirement is inherited from the Phase 8 posting architecture amendment introducing an opaque `PostingResultPlan`.

---

## 3. Scope

### 3.1 In Scope

WP-4 includes:

1. Definition of the valuation preparation boundary.
2. Definition of `ValuationInput`.
3. Definition of `ValuationInputProvider`.
4. Definition of `ValuationPlanItem`.
5. Definition of `ValuationPlan`.
6. Definition of the valuation engine responsible for preparation.
7. Integration of the existing WP-3 `ValuationMethod`.
8. Deterministic transformation from `MovementSet` to `ValuationPlan`.
9. Conversion of inventory movement semantics into valuation operation semantics.
10. Validation of valuation preparation inputs.
11. Propagation of existing valuation-domain errors.
12. Unit tests covering preparation and its architectural boundaries.
13. Public API exposure of approved WP-4 contracts.
14. Documentation reconciliation after implementation.

### 3.2 Explicitly Out of Scope

WP-4 does not include:

* valuation persistence mutation;
* appending authoritative valuation facts;
* materializing valuation balances;
* Inventory Register mutation;
* `PostingEngine` redesign;
* `ValuationCoordinator`;
* unpost compensation;
* repost compensation;
* rebuild/recovery;
* asynchronous valuation processing;
* currency handling;
* FX;
* additional valuation methods;
* changes to `Movement` semantics;
* changes to Inventory Register semantics;
* lifecycle event publication.

---

## 4. Architectural Context

Inventory accounting and valuation remain separate semantic domains.

The Inventory Register remains quantity-only:

```text
Movement
    ├── quantity
    ├── dimensions
    ├── resource
    └── accounting metadata
```

Valuation consumes movement information but does not redefine movement semantics:

```text
MovementSet
    ↓
Valuation preparation
    ├── valuation input
    ├── valuation method
    └── valuation plan
```

Later lifecycle coordination will establish authoritative valuation effects.

WP-4 must not introduce cost into:

* `Movement`;
* `MovementSet`;
* Inventory Register totals;
* register mutation APIs;
* posting handler contracts.

---

## 5. Preparation Boundary

The central WP-4 boundary is:

```text
                    preparation boundary
                           │
                           ▼
MovementSet ──→ ValuationEngine ──→ ValuationPlan
```

Preparation is an immutable planning operation from the perspective of authoritative state.

It must not:

* append valuation facts;
* modify valuation layers;
* modify valuation balances;
* remove an existing valuation effect;
* mutate Inventory Register state;
* publish lifecycle events;
* invoke `PostingEngine`;
* require removal of an existing posting result.

---

## 6. ValuationInput

`ValuationInput` is the normalized immutable input consumed by a valuation method.

Conceptually:

```text
ValuationInput
    ├── valuation key
    ├── valuation quantity
    └── available valuation layers
```

### 6.1 Valuation Key

The valuation key identifies the valuation scope for which layers are consumed.

For inventory valuation it is expected to align with the existing inventory valuation dimensions, while remaining semantically independent from Inventory Register implementation.

---

### 6.2 Valuation Quantity

`ValuationInput` contains the quantity to be valued.

This quantity is expressed using valuation-domain semantics.

The valuation method must not need to interpret Inventory Register movement signs.

The transformation is:

```text
Inventory movement
        ↓
valuation operation
        ↓
positive valuation quantity
        ↓
ValuationMethod
```

For consumption operations, the quantity supplied to the existing WP-3 FIFO consumption logic is positive.

This preserves the WP-3 contract that a consumption request represents an explicit positive quantity to consume.

---

### 6.3 Available Layers

`ValuationInput` contains the valuation layers applicable to the valuation key and operation.

The layers are supplied as immutable domain data.

The valuation method may derive consumption/allocation results from them but must not mutate them.

---

### 6.4 Movement Independence

`ValuationInput` must not require the valuation method to receive the complete `Movement`.

The movement-to-valuation semantic conversion occurs before the method boundary.

This prevents the valuation method from becoming coupled to:

* Inventory Register representation;
* posting representation;
* register mutation;
* application-level movement lifecycle.

---

## 7. ValuationInputProvider

`ValuationInputProvider` is responsible for transforming movement information into normalized valuation inputs.

Conceptually:

```text
MovementSet
    ↓
ValuationInputProvider
    ↓
ValuationInput(s)
```

### 7.1 Responsibilities

The provider is responsible for:

* identifying valuation-relevant movements;
* deriving valuation keys;
* deriving valuation quantities;
* determining the valuation operation represented by each movement;
* obtaining applicable valuation layers;
* grouping or ordering inputs where required;
* producing normalized immutable inputs.

### 7.2 Provider Restrictions

The provider must not:

* perform FIFO layer selection;
* calculate valuation cost;
* create authoritative valuation facts;
* mutate valuation persistence;
* mutate Inventory Register state;
* publish lifecycle events;
* invoke `PostingEngine`.

The provider prepares information for the valuation method; it does not perform valuation.

---

## 8. Valuation State Read Boundary

The `ValuationInputProvider` may require access to current valuation state in order to obtain applicable valuation layers.

That access must occur through a semantic read abstraction.

The intended dependency direction is:

```text
ValuationInputProvider
        ↓
valuation-state read contract
```

and not:

```text
ValuationInputProvider
        ↓
concrete persistence implementation
```

The provider must not prescribe:

* database technology;
* storage/session implementation;
* transaction mechanism;
* persistence lifecycle.

The concrete persistence mechanism remains outside the WP-4 engine boundary.

---

## 9. Non-Valuation Movements

Not every inventory movement necessarily produces a valuation effect.

A movement that has no valuation semantics produces no valuation input:

```text
non-valuation movement
        ↓
no ValuationInput
```

WP-4 does not create zero-effect valuation inputs or zero-effect plan items merely to represent the absence of valuation.

Therefore:

```text
ValuationPlan
```

contains only actual valuation effects.

---

## 10. Movement Ordering

Preparation must be deterministic.

Where `MovementSet` provides canonical ordering, WP-4 must preserve that ordering.

The implementation must not depend on unordered collection iteration.

For valuation operations where multiple movements share a valuation key, the ordering must be explicit and stable.

The existing deterministic FIFO layer ordering from WP-3 remains authoritative:

```text
(created_at, str(layer.identity))
```

WP-4 must not introduce a competing FIFO ordering rule.

---

## 11. ValuationMethod Boundary

WP-3 establishes the `ValuationMethod` abstraction and FIFO implementation.

WP-4 consumes that abstraction.

Conceptually:

```text
ValuationInput
       ↓
ValuationMethod
       ↓
valuation result
```

The valuation method owns valuation-specific algorithms such as:

* FIFO layer selection;
* consumption allocation;
* cost calculation.

WP-4 does not redesign the FIFO algorithm.

Any change to the approved WP-3 method contract requires an explicit architecture amendment.

---

## 12. ValuationPlanItem

`ValuationPlanItem` is an immutable application-level description of one prepared valuation effect.

It is intentionally distinct from `ValuationFact`.

The semantic distinction is:

```text
ValuationPlanItem
    = what should be established

ValuationFact
    = what was established as an authoritative valuation fact
```

A plan item is therefore not authoritative state.

### 12.1 Plan Item Requirements

A plan item must contain sufficient information for later establishment without rerunning valuation calculation.

The exact field-level API is intentionally deferred to Concrete API Design.

At minimum, its semantics must preserve:

* valuation identity/scope;
* source movement identity;
* prepared valuation operation;
* prepared quantity/cost information;
* required layer/source references;
* deterministic identity information where required.

---

## 13. ValuationPlan

`ValuationPlan` is the immutable result of valuation preparation.

Conceptually:

```text
ValuationPlan
    └── ordered immutable ValuationPlanItem(s)
```

### 13.1 Plan Properties

A valid plan is:

* immutable;
* deterministic;
* self-contained;
* independent of concrete persistence;
* independent of PostingEngine;
* independent of Inventory Register mutation;
* non-authoritative;
* safe to retain between `prepare()` and `establish()`.

---

## 14. Plan Self-Containment

Once created:

```text
plan = prepare(movement_set)
```

the plan must contain all information required by later establishment.

Establishment must not need to:

* rerun FIFO;
* rediscover consumed layers;
* recalculate costs;
* reinterpret movement signs;
* reconstruct valuation inputs merely to determine the valuation effect.

The intended lifecycle is:

```text
prepare()
    ↓
calculate and freeze valuation effect
    ↓
establish(plan)
    ↓
apply prepared effect
```

This is a mandatory architectural property.

---

## 15. ValuationPlan Is Not Authoritative State

`ValuationPlan` is an application-level preparation artifact.

It is not:

* a persisted valuation fact;
* a valuation balance;
* a replacement for valuation persistence;
* a source of truth.

Conceptually:

```text
ValuationPlan
    ↓
temporary immutable application artifact
```

while:

```text
ValuationFact
    ↓
authoritative valuation history
```

and:

```text
CostBalance / CostMovement
    ↓
materialized valuation result
```

remain separate persistence/result concepts.

WP-4 must not introduce persistence of `ValuationPlan` itself.

---

## 16. ValuationEngine

The valuation engine is the orchestration boundary for preparation.

Conceptually:

```text
ValuationEngine
    ↓
ValuationInputProvider
    ↓
ValuationMethod
    ↓
ValuationPlan
```

The engine is responsible for coordinating these components.

It is not responsible for:

* persistence;
* register mutation;
* posting lifecycle;
* document events;
* recovery;
* rebuilding.

The concrete method signature is defined in the subsequent Concrete API Design.

---

## 17. Single Preparation Boundary

WP-4 intentionally provides one preparation operation:

```text
prepare(MovementSet) → ValuationPlan
```

The engine must not expose separate lifecycle-specific methods such as:

```text
prepare_consumption()
prepare_adjustment()
prepare_reversal()
```

unless a later architectural requirement establishes a genuinely different preparation semantic.

Valuation operation differences belong below the engine boundary.

---

## 18. Determinism

For equivalent authoritative valuation state and equivalent `MovementSet`:

```text
prepare(movement_set)
```

must produce semantically equivalent plans.

Determinism includes:

* movement processing order;
* valuation-key grouping;
* layer selection;
* consumption allocation;
* cost allocation;
* plan-item ordering;
* generated identities where applicable.

The engine must not depend on:

* hash/set iteration order;
* object memory identity;
* nondeterministic persistence enumeration;
* unspecified ordering from infrastructure.

---

## 19. Error Boundary

Preparation errors remain valuation-domain errors.

Existing WP-3 errors, including:

```text
ValuationInsufficientQuantityError
```

must remain semantically recognizable at the WP-4 boundary.

Errors should not be wrapped merely for the purpose of creating a generic "preparation error".

A new preparation-specific error should only be introduced if it represents a distinct semantic category not covered by the existing valuation error hierarchy.

Persistence failures must remain distinguishable from valuation calculation/validation failures.

---

## 20. Repost Safety

WP-4 directly supports the amended posting architecture.

The mandatory invariant is:

```text
old authoritative state
        │
        ├── prepare(new)
        │       │
        │       ├── failure → old state remains untouched
        │       │
        │       └── success → ValuationPlan
        │
        └── only after success:
                remove(old)
                establish(new, plan)
```

No WP-4 operation may require mutation or removal of the existing valuation result in order to determine whether the new valuation can be prepared.

---

## 21. Dependency Direction

The intended dependency direction is:

```text
Application / Posting Layer
          ↓
    ValuationEngine
          ↓
ValuationInputProvider
          ↓
valuation state read abstraction
```

The valuation method remains a domain-level abstraction:

```text
ValuationEngine
      ↓
ValuationMethod
```

The following dependencies are prohibited:

```text
ValuationMethod
      X→ RegisterMutation

ValuationMethod
      X→ PostingEngine

ValuationMethod
      X→ concrete persistence

ValuationEngine
      X→ PostingEngine
```

This preserves separation between valuation, quantity accounting, persistence, and document lifecycle.

---

## 22. Relationship with Synthetic Consumption

Synthetic consumption remains an explicit valuation-domain operation.

WP-4 does not introduce an Inventory Issue document or a new Inventory Register movement solely to represent synthetic valuation consumption.

The conceptual flow is:

```text
valuation-relevant movement
        ↓
ValuationInput
        ↓
FIFO valuation method
        ↓
ValuationPlan
        ↓
prepared valuation consumption effect
```

The corresponding quantity accounting remains governed by Inventory Register semantics.

---

## 23. Relationship with PostingResultPlan

The WP-4 `ValuationPlan` is an internal valuation-domain preparation artifact.

The amended posting boundary remains generic:

```text
PostingResultPlan
```

The posting layer must not depend directly on:

* `ValuationPlan`;
* FIFO types;
* valuation layers;
* valuation cost algorithms.

Conceptually:

```text
PostingResultCoordinator.prepare()
        ↓
opaque PostingResultPlan
        ├── Register preparation
        └── Valuation preparation
```

This keeps `PostingEngine` valuation-agnostic while allowing valuation preflight to occur before destructive repost operations.

---

## 24. Architectural Invariants

### INV-01 — No authoritative mutation

Preparation does not mutate authoritative valuation or register state.

### INV-02 — Deterministic preparation

Equivalent inputs and authoritative state produce equivalent plans.

### INV-03 — Immutable input

`ValuationInput` cannot be mutated by valuation methods.

### INV-04 — Immutable plan

`ValuationPlan` and its items cannot be mutated after preparation.

### INV-05 — Plan self-containment

Establishment does not require valuation recalculation.

### INV-06 — Plan is non-authoritative

`ValuationPlan` is not persisted as authoritative valuation state.

### INV-07 — Quantity/valuation separation

No valuation cost semantics are introduced into `Movement` or Inventory Register contracts.

### INV-08 — FIFO ownership

FIFO selection remains owned by the WP-3 valuation method.

### INV-09 — Persistence independence

The engine does not depend on a concrete persistence implementation.

### INV-10 — Lifecycle independence

WP-4 does not publish document lifecycle events.

### INV-11 — Repost safety

Preparation failure cannot remove the existing posting result.

### INV-12 — No hidden mutable state

The engine does not retain implicit mutable valuation state between calls.

### INV-13 — Canonical ordering

Preparation does not depend on unspecified collection ordering.

### INV-14 — Semantic error preservation

Existing valuation-domain errors retain their meaning through the preparation boundary.

---

## 25. Acceptance Criteria

WP-4 Architecture is considered complete when:

1. `MovementSet → ValuationInput → ValuationMethod → ValuationPlan` is explicitly defined.
2. `ValuationInput` semantics include valuation key, valuation quantity, and applicable layers.
3. Movement sign semantics are converted before the valuation method boundary.
4. `ValuationInputProvider` responsibility is explicitly separated from valuation calculation.
5. The provider uses a semantic valuation-state read boundary.
6. Non-valuation movements do not produce zero-effect valuation inputs.
7. `ValuationPlanItem` is distinct from `ValuationFact`.
8. `ValuationPlan` is immutable and non-authoritative.
9. `ValuationPlan` is self-contained.
10. Establishment does not require FIFO recalculation.
11. Deterministic movement ordering is defined.
12. Existing WP-3 FIFO ordering remains authoritative.
13. Existing valuation-domain errors remain semantically recognizable.
14. Preparation does not mutate authoritative state.
15. Preparation failure preserves the old result.
16. Concrete persistence remains outside the valuation engine.
17. Register mutation remains outside the valuation engine.
18. Posting lifecycle remains outside WP-4.
19. The API is sufficiently stable for WP-5 `ValuationCoordinator`.
20. Unit-test boundaries are defined before implementation.

---

## 26. Testing Scope

WP-4 tests must verify architectural behavior.

### 26.1 Input Preparation

Test:

* empty `MovementSet`;
* one valuation-relevant movement;
* multiple valuation-relevant movements;
* multiple valuation keys;
* non-valuation movements;
* conversion of movement semantics to valuation quantity;
* deterministic input ordering.

### 26.2 FIFO Integration

Test:

* FIFO method invocation through `ValuationMethod`;
* single-layer consumption;
* partial-layer consumption;
* multi-layer consumption;
* zero-cost layers;
* insufficient quantity propagation.

Existing WP-3 FIFO behavior must remain unchanged.

### 26.3 Plan

Test:

* immutable plan;
* immutable plan items;
* deterministic plan ordering;
* complete prepared valuation effect;
* no dependency on recomputation during establishment.

### 26.4 Determinism

Repeated preparation against equivalent inputs and state must produce semantically equivalent plans.

### 26.5 Failure Safety

Test:

* invalid valuation input;
* insufficient quantity;
* provider failure;
* valuation method failure;
* unsupported valuation scenario.

### 26.6 Architectural Boundaries

Verify that preparation does not:

* mutate valuation persistence;
* mutate Inventory Register state;
* publish lifecycle events;
* invoke `PostingEngine`;
* remove an existing valuation result.

---

## 27. Deliverables

WP-4 deliverables are:

1. Final approved architecture definition.
2. Concrete API Design.
3. `ValuationInput`.
4. `ValuationInputProvider`.
5. `ValuationPlanItem`.
6. `ValuationPlan`.
7. `ValuationEngine`.
8. Integration with existing WP-3 `ValuationMethod`.
9. Unit tests covering preparation and architectural boundaries.
10. Public API exports.
11. Documentation reconciliation.

No implementation begins before Concrete API Design is approved.

---

## 28. Exit Condition

WP-4 is complete only after the following sequence:

```text
Architecture Definition
        ↓
Architecture Review
        ↓
Concrete API Design
        ↓
API Approval
        ↓
Implementation
        ↓
Unit Tests
        ↓
Quality Gate
        ↓
Documentation Reconciliation
        ↓
Final Review
```

The resulting WP-4 API must provide a stable preparation boundary for WP-5 `ValuationCoordinator`.

WP-5 must not introduce compensating changes to the WP-4 preparation semantics unless an explicit architecture amendment is approved.

---

## 29. Architecture Decision Summary

WP-4 establishes the following architectural decisions:

1. Valuation preparation is separate from valuation establishment.
2. `ValuationInputProvider` converts movement semantics into valuation inputs.
3. `ValuationMethod` owns valuation algorithms.
4. `ValuationPlan` captures the complete prepared valuation effect.
5. `ValuationPlanItem` is distinct from authoritative `ValuationFact`.
6. Plans are immutable, deterministic, self-contained, and non-authoritative.
7. Preparation performs no authoritative mutation.
8. Preparation failure cannot destroy an existing posting result.
9. FIFO remains the valuation method introduced in WP-3.
10. Inventory Register remains quantity-only.
11. Persistence remains behind semantic read/write contracts.
12. Posting lifecycle remains outside the valuation engine.
13. `PostingResultPlan` remains opaque to `PostingEngine`.
14. The WP-4 preparation boundary is the foundation for WP-5 `ValuationCoordinator`.
