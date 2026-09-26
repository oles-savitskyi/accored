# Phase 8 — Valuation Architecture

## API Design Approval / Implementation Plan

**Status:** Approved for Implementation
**Phase:** 8
**Implementation:** Not started
**Baseline:** Final Concrete API Design
**Implementation mode:** Incremental, architecture-preserving

---

# 1. Approval Decision

The Phase 8 Concrete API Design is approved for implementation.

The API has passed the required architecture and API reviews.

The implementation may now begin, provided that:

1. the approved architectural boundaries are preserved;
2. the public API remains consistent with the Concrete API Design;
3. no new architectural responsibility is introduced during implementation;
4. implementation does not silently weaken persistence consistency semantics;
5. deterministic valuation-domain failures remain confined to preflight;
6. immutable valuation facts remain append-only;
7. Register and Valuation remain independent semantic concerns.

Any implementation discovery requiring a change to these principles requires a documented design amendment before continuing implementation.

---

# 2. Implementation Objective

Implement the first working valuation slice:

```text
Inventory Receipt
      ↓
Register Movement
      ↓
Valuation Layer
      ↓
FIFO
      ↓
Synthetic Consumption
      ↓
Valuation Consumption
      ↓
Cost Movement
      ↓
Cost Balance
```

with support for:

* zero initial cost;
* delayed additional cost;
* immutable valuation facts;
* reversal-based unpost/repost;
* synchronous posting integration;
* deterministic preflight;
* rebuildable derived results.

---

# 3. Implementation Strategy

Implementation follows the dependency direction:

```text
Domain Facts
    ↓
Persistence Contracts
    ↓
FIFO / Valuation Engine
    ↓
Coordinator
    ↓
Posting Integration
    ↓
Standard Inventory Composition
    ↓
Integration Tests
    ↓
Quality Gate
    ↓
Documentation Reconciliation
```

No top-level PostingEngine redesign is planned.

The existing posting lifecycle remains the application orchestration boundary.

---

# 4. Work Package Structure

Implementation is divided into the following work packages:

```text
WP-0  Integration Verification
WP-1  Valuation Domain Model
WP-2  Valuation Persistence Contracts
WP-3  FIFO and Synthetic Consumption
WP-4  Valuation Engine and Plan
WP-5  Valuation Coordinator
WP-6  Posting Lifecycle Integration
WP-7  Standard Inventory Composition
WP-8  Reversal / Repost / Recovery
WP-9  Queries and Rebuild
WP-10 Integration and Architectural Tests
WP-11 Documentation Reconciliation
WP-12 Final Quality Gate
WP-13 Final Review
```

The work packages are intentionally sequential where architectural dependencies exist.

---

# 5. WP-0 — Integration Verification

## Objective

Verify the current Phase 7 baseline before introducing Phase 8 code.

## Required checks

Inspect:

```text
src/accore/platform/posting/
src/accore/platform/registers/
src/accore/platform/persistence/
src/standard/
tests/unit/posting/
tests/unit/registers/
tests/unit/standard/
```

Confirm:

* `PostingEngine` current API;
* `PostingResultCoordinator`;
* `RegisterPostingResultCoordinator`;
* `RegisterMutationOrchestrator`;
* `RegisterFactPersistence`;
* existing persistence errors;
* Standard Inventory composition;
* current posting integration tests.

## Acceptance

No implementation starts until the actual repository integration points match the approved API assumptions.

---

# 6. WP-1 — Valuation Domain Model

Implement immutable domain types:

```text
ValuationKey
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal
ValuationFact
```

and:

```text
ValuationInput
ConsumptionRequest
ConsumptionResult
ValuationPlan
```

## Requirements

* frozen/immutable objects;
* Decimal-only monetary values;
* no mutable valuation facts;
* deterministic identity semantics;
* validation of positive quantities;
* zero cost accepted;
* no `unknown/deferred` cost state.

## Tests

Create focused unit tests for:

* construction;
* immutability;
* invalid values;
* zero cost;
* deterministic equality;
* fact union semantics.

---

# 7. WP-2 — Valuation Persistence Contracts

Implement protocols:

```text
ValuationFactPersistence
ValuationResultPersistence
```

No concrete storage implementation should be introduced before the semantic contract is stable.

## Fact persistence

Must support:

```text
append
find_by_source_document
find_by_source_movement
find_by_valuation_key
enumerate
```

## Result persistence

Must support:

```text
append_movements
replace_balance
find_movements
find_balance
enumerate_balances
```

## Key invariant

The implementation must preserve:

```text
Valuation facts = authoritative
Cost results = derived
```

---

# 8. WP-3 — FIFO and Synthetic Consumption

Implement:

```text
ValuationMethod
FIFOValuationMethod
SyntheticConsumptionService
```

## FIFO requirements

Support:

* one layer;
* multiple layers;
* partial consumption;
* exact consumption;
* multi-layer consumption;
* insufficient quantity;
* zero-cost layers;
* deterministic ordering.

FIFO must not:

* persist data;
* mutate layers;
* access PostingEngine;
* access RegisterMutationOrchestrator.

## Acceptance

FIFO is independently testable as a pure valuation algorithm.

---

# 9. WP-4 — Valuation Engine and Plan

Implement the deterministic valuation preparation layer.

Primary responsibility:

```text
MovementSet
    ↓
ValuationInputProvider
    ↓
ValuationMethod
    ↓
ValuationPlan
```

The engine must:

1. resolve valuation inputs;
2. identify applicable valuation keys;
3. load relevant layers;
4. perform FIFO calculation;
5. validate all deterministic valuation constraints;
6. construct immutable valuation facts;
7. construct `ValuationPlan`.

## Critical invariant

`prepare()` must not persist authoritative valuation facts.

All deterministic valuation failures must occur here.

---

# 10. WP-5 — Valuation Coordinator

Implement:

```text
ValuationCoordinator
```

with:

```python
prepare(document, movement_set) -> ValuationPlan

establish(document, movement_set, plan) -> None

remove(document) -> None
```

## Establish

`establish()` receives the already prepared plan.

It must not silently rerun nondeterministic valuation logic.

Responsibilities:

* persist valuation facts;
* establish derived results;
* preserve persistence error semantics.

## Remove

`remove()`:

* never deletes historical facts;
* creates compensating reversal facts;
* updates derived results as required.

---

# 11. WP-6 — Posting Lifecycle Integration

Integrate valuation through the existing:

```text
PostingResultCoordinator
```

rather than modifying `PostingEngine` with valuation-specific logic.

Target composition:

```text
CompositePostingResultCoordinator
    ├── RegisterPostingResultCoordinator
    └── ValuationPostingCoordinator
```

## Establish sequence

```text
Valuation prepare
      ↓
Register establish
      ↓
Valuation establish
      ↓
success
      ↓
DocumentPosted
```

## Failure rules

### Preflight failure

```text
Register unchanged
Valuation unchanged
No event
```

### Register persistence failure

```text
Valuation unchanged
No event
Existing Posting persistence mapping
```

### Valuation persistence failure

```text
Register may already be committed
No DocumentPosted
Existing persistence failure semantics
```

### Valuation indeterminate failure

```text
Register committed
Valuation state uncertain
No DocumentPosted
PostingIndeterminateError
```

The implementation must not claim atomic cross-domain transaction semantics.

---

# 12. WP-7 — Standard Inventory Composition

Extend the Standard configuration to compose:

```text
Inventory Register
        +
Valuation
        +
FIFO
        +
Composite Posting Coordinator
```

The Standard layer provides:

* Inventory `ValuationKey` mapping;
* `ValuationInputProvider`;
* FIFO method;
* valuation persistence implementation;
* valuation result persistence;
* valuation coordinator;
* posting coordinator composition.

The Standard layer must not move generic valuation responsibilities into `standard`.

---

# 13. WP-8 — Reversal / Repost / Recovery

Implement and test immutable reversal semantics.

## Unpost

```text
original valuation facts
        ↓
reversal facts
        ↓
compensated effective state
```

## Repost

```text
old valuation effect
        ↓
reversal
        ↓
new valuation preparation
        ↓
new valuation effect
```

## Recovery

Test:

* persistence failure;
* persistence indeterminate state;
* repeated operation;
* duplicate logical operation;
* repeated reversal;
* rebuild after incomplete derived results.

No historical valuation fact may be mutated or deleted.

---

# 14. WP-9 — Queries and Rebuild

Implement:

```text
ValuationFactQueryService
ValuationQueryService
ValuationRebuilder
```

## Rebuild source

Only:

```text
ValuationFactPersistence
```

is authoritative.

Rebuild must not depend on:

```text
CostBalance
```

as authoritative input.

Target:

```text
facts
  ↓
valuation engine
  ↓
CostMovement
  ↓
CostBalance
```

## Tests

Verify:

* empty rebuild;
* normal rebuild;
* rebuild after adjustment;
* rebuild after reversal;
* discarded derived results reconstructed correctly;
* repeated rebuild is deterministic.

---

# 15. WP-10 — Integration and Architectural Tests

Add platform-level tests proving the architectural boundaries.

## Required scenarios

### Normal receipt

```text
Goods Receipt
    ↓
Register Movement
    ↓
Valuation Layer
```

### Zero-cost receipt

```text
quantity > 0
cost = 0
```

must produce valid quantity and valuation state.

### FIFO consumption

Multiple layers must be consumed in deterministic FIFO order.

### Delayed cost

```text
Layer = 100 qty / 0 cost
Adjustment = +100
Allocation = +100
```

must result in effective cost of 100 while quantity remains 100.

### Synthetic consumption independence

Synthetic consumption must not change Register totals.

### Unpost

Quantity and valuation effects must both be compensated.

### Repost

Old valuation effects must be reversed and new effects established.

### Failure

No domain event may be emitted before successful completion.

### Indeterminate persistence

Existing Posting indeterminate semantics must remain intact.

---

# 16. Architectural Invariant Tests

The implementation should include explicit tests for the following invariants.

```text
INV-01 Register does not depend on Valuation
INV-02 Valuation facts are immutable
INV-03 Valuation facts are append-only
INV-04 Zero cost is valid
INV-05 No deferred-cost state exists
INV-06 Synthetic consumption creates no Register Movement
INV-07 FIFO is persistence-independent
INV-08 Deterministic valuation failures occur in preflight
INV-09 No distributed transaction is assumed
INV-10 Existing persistence error semantics are preserved
INV-11 Domain events occur only after successful completion
INV-12 Derived results are rebuildable
INV-13 Reversal does not mutate history
INV-14 Logical operation identity is deterministic
INV-15 Monetary values use Decimal
```

These are architecture tests, not merely implementation tests.

---

# 17. WP-11 — Documentation Reconciliation

After implementation, reconcile:

* Phase 8 Architecture Definition / Scope;
* Phase 8 Concrete API Design;
* Phase 8 Implementation documentation;
* persistence semantics;
* lifecycle diagrams;
* acceptance criteria;
* architecture invariants;
* project roadmap.

Documentation must describe the actual final implementation.

Any deviation from the approved API must be explicitly documented and reviewed.

Known roadmap/documentation inconsistencies from earlier phases should be corrected during this pass rather than copied forward.

---

# 18. WP-12 — Final Quality Gate

The quality gate must include:

```text
pytest
ruff
black --check
mypy
```

plus the complete architectural invariant suite.

The final test run must cover:

* unit tests;
* integration tests;
* posting tests;
* register tests;
* valuation tests;
* standard composition tests.

No implementation commit is considered complete while the quality gate is failing.

---

# 19. WP-13 — Final Review

Final review must inspect:

### Architecture

* separation of Register and Valuation;
* Posting boundary;
* persistence semantics;
* immutable facts;
* rebuild model.

### API

* public exports;
* protocol contracts;
* type signatures;
* error mapping;
* lifecycle semantics.

### Implementation

* no accidental coupling;
* no duplicated FIFO logic;
* no mutation of immutable facts;
* no hidden persistence behavior;
* deterministic operation identity.

### Documentation

* architecture matches implementation;
* API documentation matches implementation;
* acceptance criteria are demonstrably satisfied.

---

# 20. Commit Strategy

Implementation should remain reviewable through incremental commits or a controlled implementation sequence.

Recommended logical commit boundaries:

```text
1. valuation domain contracts
2. valuation persistence contracts
3. FIFO / consumption engine
4. valuation coordinator / plan
5. posting integration
6. standard inventory composition
7. reversal / rebuild / query
8. tests
9. documentation reconciliation
```

The exact commit grouping may be adjusted if repository workflow requires a smaller or larger atomic unit.

The final Phase 8 implementation commit must not contain unrelated refactoring.

---

# 21. Stop Conditions

Implementation must stop and return to Architecture/API Review if any of the following becomes necessary:

### A. Register API modification

If valuation requires changing the semantic Register Movement model.

### B. PostingEngine valuation knowledge

If `PostingEngine` must understand FIFO, valuation layers, costs, or valuation persistence.

### C. Mutable valuation facts

If implementation requires updating or deleting historical valuation facts.

### D. Cross-domain transaction

If implementation requires claiming atomic transaction semantics across independent persistence providers.

### E. New business document

If synthetic consumption begins requiring an Inventory Issue document.

### F. New valuation state

If implementation requires `unknown`, `deferred`, `pending`, or equivalent initial-cost states.

### G. New monetary model

If implementation requires currency, FX, or multi-currency.

### H. New valuation method

If implementation requires LIFO, Standard Cost, production costing, or another Phase 8-external valuation method.

---

# 22. Implementation Order Summary

The approved implementation sequence is:

```text
WP-0
Integration Verification
        ↓
WP-1
Domain Model
        ↓
WP-2
Persistence Contracts
        ↓
WP-3
FIFO + Synthetic Consumption
        ↓
WP-4
Valuation Engine + ValuationPlan
        ↓
WP-5
Valuation Coordinator
        ↓
WP-6
Posting Integration
        ↓
WP-7
Standard Composition
        ↓
WP-8
Reversal / Repost / Recovery
        ↓
WP-9
Query + Rebuild
        ↓
WP-10
Integration + Architectural Tests
        ↓
WP-11
Documentation Reconciliation
        ↓
WP-12
Quality Gate
        ↓
WP-13
Final Review
        ↓
Phase 8 Completion
```

---

# 23. First Implementation Slice

The first implementation action is **WP-0 only**.

Before creating valuation implementation files:

1. inspect the current repository;
2. verify actual Phase 7 integration points;
3. verify current posting coordinator API;
4. verify persistence contracts;
5. verify Standard Inventory composition;
6. verify existing test conventions;
7. record any discrepancy between repository and approved API.

Only after WP-0 confirms the baseline should WP-1 begin.

---

# 24. Final Approval Statement

The Phase 8 Concrete API Design is:

> **APPROVED FOR IMPLEMENTATION**

The implementation may proceed according to this plan.

The first authorized activity is:

> **WP-0 — Integration Verification.**

No valuation implementation code should be introduced before WP-0 confirms the actual repository baseline and integration points.
