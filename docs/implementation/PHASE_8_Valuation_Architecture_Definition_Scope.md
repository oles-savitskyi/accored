# AcCoreD — Phase 8: Valuation

## Architecture Definition / Scope

**Status:** Final — Architecture Approved
**Phase:** 8
**Subsystem:** Valuation Architecture
**Depends on:** Phase 7 — Registers / Posting / Inventory Register
**Primary architectural objective:** introduce Valuation Architecture into the working business lifecycle while preserving strict independence between quantity accounting and valuation.

---

# 1. Phase Objective

Phase 8 introduces the Valuation Architecture into the operational Posting lifecycle.

The phase validates the architectural principle:

> **Quantity accounting and valuation are related but independent concerns.**

The existing Register Architecture remains responsible for authoritative quantity facts.

The Valuation Architecture becomes responsible for:

* valuation ownership;
* cost consumption;
* cost corrections;
* valuation allocation;
* cost movements;
* cost balances;
* deterministic valuation reconstruction;
* valuation compensation for lifecycle reversal.

The phase must demonstrate that valuation can participate in the working business lifecycle without introducing cost into the Inventory Register or changing the semantic responsibility of `Movement`.

---

# 2. Architectural Baseline

Phase 8 starts from the completed Phase 7 architecture.

The existing application lifecycle contains conceptually:

```text
Operational Document
        ↓
PostingEngine
        ↓
Posting Handler
        ↓
MovementSet
        ↓
Movement Validation
        ↓
PostingResultCoordinator
        ↓
Register Coordination
        ↓
Register Mutation
        ↓
Register Movement Facts
        ↓
successful completion
        ↓
Posting Domain Event
```

The current Posting architecture already separates application orchestration from Register-specific mutation.

Phase 8 must preserve that boundary.

The valuation integration therefore occurs at the Posting application coordination level and must not require `PostingEngine` to become aware of Register internals.

---

# 3. Core Architectural Principle

Quantity accounting and valuation are independent concerns.

```text
Quantity Accounting
        │
        │ authoritative quantity facts
        ▼
Register Architecture


Valuation
        │
        │ valuation facts
        ▼
Valuation Architecture
```

The two architectures interact through explicit integration points but neither becomes a hidden extension of the other.

In particular:

* `Movement` does not acquire a cost field;
* Inventory Register does not acquire a cost resource;
* Register totals do not calculate cost;
* Register mutation does not implement valuation algorithms;
* Posting handlers do not calculate cost;
* valuation methods do not modify Register facts.

---

# 4. Architectural Decisions

| Decision                           | Phase 8 architecture                                             |
| ---------------------------------- | ---------------------------------------------------------------- |
| Quantity / Valuation               | Independent concerns                                             |
| First valuation method             | FIFO                                                             |
| Consumption mechanism              | Synthetic consumption                                            |
| Inventory Issue document           | Out of scope                                                     |
| Trigger                            | Synchronous                                                      |
| Trigger location                   | Posting application lifecycle                                    |
| Trigger order                      | Register → Valuation → successful Domain Event                   |
| Register modification by valuation | Prohibited                                                       |
| Valuation facts                    | Immutable                                                        |
| Cost results                       | Materialized                                                     |
| Persistence contracts              | Separate semantic contracts                                      |
| Physical storage                   | May be shared                                                    |
| Rebuild source                     | Valuation facts                                                  |
| Monetary type                      | `Decimal`                                                        |
| Currency / FX                      | Out of scope                                                     |
| Unpost                             | Compensating valuation facts                                     |
| Repost                             | Compensation of previous valuation effect + new valuation effect |
| Partial cross-domain completion    | Existing Posting/Persistence indeterminate semantics             |
| Distributed transaction framework  | Out of scope                                                     |

---

# 5. Quantity / Valuation Independence

The fundamental relationship is:

```text
Quantity Facts ≠ Valuation Facts
```

The existence of a quantity movement may create or affect valuation state, but valuation state is not part of the quantity movement itself.

The following structures remain independent:

```text
Movement
    → quantity semantics

Inventory Register
    → quantity state

Valuation Architecture
    → cost state
```

The architecture must not introduce a combined:

```text
Movement
    ├── quantity
    └── cost
```

model.

---

# 6. First Valuation Method — FIFO

The first valuation method implemented by Phase 8 is:

```text
FIFO
```

FIFO operates on valuation layers.

The method determines how available valuation layers are consumed.

The method does not define the persistent structure of valuation layers.

Conceptually:

```text
Valuation Layers
       ↓
FIFO Selection
       ↓
Consumption
       ↓
ValuationConsumption
```

FIFO is therefore a valuation strategy rather than a storage model.

Future valuation methods must be able to use the same valuation architecture without redesigning the core fact model.

---

# 7. Valuation Domain Facts

Phase 8 uses explicit immutable valuation facts.

The primary valuation fact model is:

```text
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal
```

Materialized valuation results are:

```text
CostMovement
CostBalance
```

The conceptual relationship is:

```text
                    ┌────────────────────┐
                    │   ValuationLayer   │
                    └─────────┬──────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
     ValuationConsumption  Adjustment   Reversal
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                       CostMovement
                              │
                              ▼
                        CostBalance
```

`ValuationAllocation` represents explicit distribution of an adjustment across valuation targets.

All these facts are immutable once persisted.

---

# 8. ValuationLayer

`ValuationLayer` is the primary carrier of valuation ownership.

A layer represents quantity-associated economic value independently from the Inventory Register's quantity state.

Conceptually it contains:

```text
layer identity
valuation key
quantity
remaining quantity
base cost
source reference
creation/provenance information
```

The layer preserves provenance.

The layer itself is immutable.

Its effective remaining quantity is derived from valuation facts rather than by mutating the historical layer.

---

# 9. ValuationConsumption

`ValuationConsumption` represents explicit consumption of valuation ownership.

It records:

* which valuation layer was consumed;
* how much quantity was consumed;
* the resulting cost attribution;
* source/reference information;
* relevant provenance information.

Consumption is an immutable valuation fact.

It does not modify the Inventory Register movement.

---

# 10. ValuationAdjustment

`ValuationAdjustment` represents an explicit change in valuation.

Examples include:

* delayed cost;
* additional supplier cost;
* transportation or similar additional cost;
* price correction;
* revaluation;
* correction of previously supplied cost information.

The architecture does not permit cost to change implicitly.

Conceptually:

```text
Initial Valuation
       +
ValuationAdjustment
       ↓
Updated Valuation Result
```

The original valuation facts remain historically identifiable.

---

# 11. ValuationAllocation

`ValuationAllocation` represents explicit distribution of an adjustment.

This separates:

```text
Adjustment
```

from:

```text
How the adjustment is distributed
```

The allocation is itself an immutable valuation fact.

This prevents adjustment distribution from becoming hidden mutable state inside the valuation engine.

---

# 12. ValuationReversal

`ValuationReversal` represents compensation for a previously established valuation effect.

It is required because valuation facts are immutable.

An Unpost or Repost operation must therefore not:

* delete valuation facts;
* mutate historical valuation facts;
* overwrite historical consumption;
* rewrite historical layers.

Instead, the lifecycle creates explicit compensating valuation facts.

Conceptually:

```text
Original valuation effect
        ↓
ValuationReversal
        ↓
Effective valuation state
```

The reversal references the valuation effect being compensated.

The original facts remain part of the historical valuation record.

This preserves:

* auditability;
* provenance;
* immutability;
* deterministic reconstruction.

---

# 13. CostMovement

`CostMovement` is a materialized valuation result.

It represents the cost effect produced by valuation processing.

It is not the authoritative historical source.

The relationship is:

```text
Valuation Facts
      ↓
Valuation Engine
      ↓
CostMovement
```

Cost movements must therefore be reproducible from valuation facts.

---

# 14. CostBalance

`CostBalance` is materialized valuation state.

It represents the current cost state for a valuation key.

Conceptually:

```text
Valuation Facts
      ↓
Valuation Engine
      ↓
CostMovement
      ↓
CostBalance
```

`CostBalance` is not the primary source of historical valuation truth.

The valuation facts remain the reconstruction source.

---

# 15. Valuation Dimensions

For Phase 8, valuation dimensions align with the corresponding quantity dimensions.

For Inventory:

```text
Quantity Key
    = (product, warehouse)

Valuation Key
    = (product, warehouse)
```

This alignment is intentional but does not make the two models identical.

The architectures remain semantically independent:

```text
Inventory Register Key
        ≠
Valuation Layer Identity
```

A valuation layer belongs to one valuation key.

A valuation layer must not span multiple valuation keys.

---

# 16. Monetary Resource

Phase 8 uses `Decimal` for monetary values.

The phase does not introduce:

* currency framework;
* exchange rates;
* FX conversion;
* multi-currency valuation;
* financial ledger integration.

Currency semantics are explicitly deferred.

The Phase 8 monetary model is therefore a deterministic Decimal-based valuation model.

---

# 17. Synthetic Consumption

Phase 8 does not introduce a new Inventory Issue business document.

Consumption is introduced as an explicit platform-level valuation operation.

The conceptual operation is:

```text
ValuationLayer
      ↓
Synthetic Consumption
      ↓
ValuationConsumption
      ↓
CostMovement
```

Synthetic consumption is an explicit valuation-domain operation.

It is **not** automatically inferred from every quantity movement.

For example, a receipt may establish a valuation layer without implying consumption.

This distinction prevents the valuation subsystem from silently interpreting every Register movement as both an establishment and consumption operation.

---

# 18. Posting Lifecycle Integration

Valuation is integrated into the existing Posting application lifecycle.

The authoritative sequence is:

```text
PostingEngine
      ↓
PostingResultCoordinator
      ↓
Register Coordination
      ↓
Register Mutation
      ↓
Authoritative Register Movement
      ↓
Valuation Coordination
      ↓
Valuation Engine
      ↓
CostMovement
      ↓
CostBalance
      ↓
successful Posting completion
      ↓
DocumentPosted
```

The precise composition of the existing `PostingResultCoordinator` with the new valuation coordinator belongs to Concrete API Design.

The architectural boundary is fixed:

> Posting coordinates Register and Valuation; Register mutation does not own Valuation.

---

# 19. Valuation Trigger

The valuation trigger is:

> **synchronous application-level processing inside the Posting lifecycle.**

Valuation occurs after successful Register mutation and before successful Posting event publication.

Therefore:

```text
Register
   ↓
Valuation
   ↓
Domain Event
```

is authoritative.

The architecture does not use `DocumentPosted` as an asynchronous valuation trigger.

---

# 20. Why Valuation Is Not an Event Subscriber

Using `DocumentPosted` as an asynchronous trigger could expose:

```text
Register committed
       ↓
DocumentPosted published
       ↓
Valuation fails
```

This would make successful Posting observable while valuation is incomplete.

Phase 8 requires:

```text
Register success
+
Valuation success
       ↓
successful Posting
       ↓
DocumentPosted
```

Therefore `DocumentPosted` is an outcome event, not the valuation trigger.

---

# 21. ValuationCoordinator Responsibility

A dedicated `ValuationCoordinator` is the lifecycle boundary between Posting and Valuation.

Its responsibility is valuation lifecycle coordination.

It must not become the valuation algorithm.

Responsibilities remain separated:

### PostingEngine

Application orchestration.

### PostingResultCoordinator

Coordinates Posting result application.

### RegisterMutationOrchestrator

Quantity accounting.

### ValuationCoordinator

Valuation lifecycle coordination.

### Valuation Engine

Valuation calculation.

### FIFO Method

Method-specific valuation behavior.

This prevents valuation from leaking into Register mutation.

---

# 22. Persistence Architecture

Valuation uses separate semantic persistence contracts.

The conceptual boundaries are:

```text
RegisterFactPersistence
        ↓
Register Movement facts


ValuationFactPersistence
        ↓
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal


ValuationResultPersistence
        ↓
CostMovement
CostBalance
```

The physical persistence provider may be shared.

Semantic contracts remain separate.

Therefore:

```text
shared physical storage
        ≠
shared semantic persistence contract
```

---

# 23. Why RegisterFactPersistence Is Not Extended

`RegisterFactPersistence` remains responsible for authoritative Register facts.

It is not expanded with valuation-specific operations.

This preserves:

```text
RegisterFactPersistence
    → quantity facts

ValuationFactPersistence
    → valuation facts

ValuationResultPersistence
    → valuation results
```

Valuation reconstruction can therefore remain semantically independent from Register persistence.

---

# 24. Cross-Domain Consistency Model

Phase 8 does not introduce a distributed transaction framework.

The Register and Valuation persistence contracts remain separate semantic boundaries.

The application lifecycle nevertheless treats:

```text
Register mutation
+
Valuation processing
```

as one Posting operation.

Therefore a partial completion must be explicitly represented.

The architecture distinguishes:

### Determinate business/valuation failure

The operation is known not to have completed and there is no ambiguous persistence state.

### Determinate persistence failure

The operation is known not to have committed.

### Indeterminate state

The system cannot establish with certainty whether one or more persistence effects committed.

The existing AcCoreD Posting/Persistence indeterminate semantics remain authoritative for this case.

Phase 8 must not invent a separate valuation-specific meaning of "indeterminate".

---

# 25. Register Success / Valuation Failure

The critical case is:

```text
Register mutation succeeds
        ↓
Valuation processing fails
```

The Posting operation cannot be reported as a successful Posting.

In particular:

```text
DocumentPosted
```

must not be published as successful completion.

However, the architecture must also recognize that Register persistence may already have committed.

Therefore the result is not automatically equivalent to:

```text
everything rolled back
```

unless the underlying persistence composition actually guarantees such atomicity.

If the commit state cannot be established, the operation is represented using the existing:

```text
indeterminate
```

semantics.

This is intentional.

Phase 8 does not introduce a second transaction/recovery model.

---

# 26. Recovery Principle

Recovery must be deterministic and explicit.

The architecture requires enough durable identity/provenance to establish which Posting operation and valuation operation belong together.

The recovery objective is:

```text
Detect incomplete operation
        ↓
Determine persisted effects
        ↓
Complete or compensate valuation state
        ↓
Restore consistency
```

Recovery must not silently reinterpret an indeterminate operation as a successful Posting.

The exact recovery coordinator and persistence API are defined during Concrete API Design.

---

# 27. Valuation Rebuild

Valuation state must be deterministically rebuildable.

The authoritative reconstruction path is:

```text
ValuationFactPersistence
        ↓
Valuation Engine
        ↓
CostMovement
        ↓
CostBalance
```

The rebuild source is valuation facts.

Existing `CostBalance` and `CostMovement` are not authoritative inputs to rebuild.

The Inventory Register is not required as the primary replay source.

Register references may exist for correlation/provenance, but valuation reconstruction must remain based on valuation facts.

---

# 28. Determinism

For the same:

```text
valuation facts
+
valuation configuration
+
valuation method
```

the resulting:

```text
CostMovement
CostBalance
```

must be reproducible.

FIFO ordering must therefore use explicit deterministic layer ordering/provenance.

It must not depend on:

* incidental collection ordering;
* unspecified persistence ordering;
* current materialized balance;
* runtime object identity;
* previous execution order.

---

# 29. Unpost Semantics

Unpost does not mutate or delete historical valuation facts.

The conceptual lifecycle is:

```text
Existing valuation effect
        ↓
ValuationReversal
        ↓
effective valuation state without original effect
```

The original:

```text
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
```

facts remain immutable.

The reversal identifies the effect being compensated.

The resulting valuation state is calculated from the complete valuation fact history.

This establishes:

```text
Unpost ≠ delete historical valuation
```

Instead:

```text
Unpost = compensate previous valuation effect
```

---

# 30. Repost Semantics

Repost consists conceptually of two valuation operations:

```text
Previous valuation effect
        ↓
ValuationReversal
        ↓
New valuation effect
```

The previous valuation facts remain immutable.

The new Posting establishes new valuation facts.

Therefore:

```text
Repost
    ≠ mutate previous valuation facts
```

and:

```text
Repost
    = compensate previous effect
      +
      establish new effect
```

This preserves the historical audit trail while allowing the current valuation state to represent the new Posting result.

---

# 31. Valuation Reversal and Rebuild

The effective valuation state is determined from the complete valuation fact history.

Conceptually:

```text
Original valuation facts
        +
Compensating valuation facts
        +
New valuation facts
        ↓
Valuation Engine
        ↓
Current CostMovement / CostBalance
```

This allows normal processing and rebuild to converge on the same result.

---

# 32. Delayed Cost Scenario

Delayed cost is a mandatory Phase 8 scenario.

Example:

```text
Receipt:
100 units
initial cost = 0
```

Quantity state:

```text
Inventory quantity = 100
```

Valuation state:

```text
ValuationLayer
quantity = 100
base cost = 0
```

Later:

```text
ValuationAdjustment
amount = +100
```

Result:

```text
Inventory quantity = 100
Valuation cost = 100
```

The quantity movement remains unchanged.

The original valuation layer remains historically identifiable.

The later cost is represented explicitly by a valuation adjustment.

---

# 33. FIFO Synthetic Consumption Scenario

Example:

```text
Layer A
100 units
cost = 100

Layer B
50 units
cost = 75
```

Synthetic consumption:

```text
consume 120 units
```

FIFO produces:

```text
Layer A → consume 100
Layer B → consume 20
```

The resulting consumption is represented explicitly through `ValuationConsumption`.

The Inventory Register remains a quantity register.

No Inventory Issue document is required.

---

# 34. Failure Semantics

Valuation failure is part of the Posting operation.

Possible outcomes are:

### Success

```text
Register mutation successful
Valuation successful
DocumentPosted emitted
```

### Determinate failure

```text
Operation rejected
No successful DocumentPosted
No ambiguous persistence state
```

### Indeterminate

```text
Persistence outcome cannot be established
No successful DocumentPosted
Operation enters existing indeterminate/recovery semantics
```

The architecture does not equate:

```text
Posting failure
```

with:

```text
automatic rollback
```

unless the persistence layer explicitly guarantees atomic rollback.

---

# 35. Independence Invariants

The following invariants are mandatory.

### Invariant 1 — Movement has no cost

`Movement` remains quantity-oriented.

### Invariant 2 — Inventory Register has no cost resource

The Inventory Register represents quantity only.

### Invariant 3 — Valuation cannot alter quantity facts

Valuation processing cannot mutate the semantic content of an authoritative Register Movement.

### Invariant 4 — Quantity can exist without final cost

Incomplete cost information must not require changing quantity semantics.

### Invariant 5 — Cost changes are explicit

Every valuation change is represented by an explicit valuation fact.

### Invariant 6 — Valuation facts are immutable

Historical valuation facts cannot be modified or deleted as part of normal lifecycle operations.

### Invariant 7 — Reversal is compensating

Unpost and Repost compensate previous valuation effects through new valuation facts.

### Invariant 8 — Valuation results are reconstructible

`CostMovement` and `CostBalance` can be rebuilt from valuation facts.

### Invariant 9 — Valuation methods are replaceable

FIFO is a method, not the definition of the valuation data model.

### Invariant 10 — Successful Posting includes valuation completion

`DocumentPosted` is emitted only after required valuation processing succeeds.

### Invariant 11 — Register mutation remains valuation-independent

`RegisterMutationOrchestrator` has no valuation responsibility.

### Invariant 12 — Indeterminate semantics remain unified

Valuation does not introduce a separate definition of Posting indeterminacy.

---

# 36. Query Architecture

Operational queries use materialized valuation state:

```text
CostBalance
```

and, where movement-level history is required:

```text
CostMovement
```

Audit/reconstruction queries use valuation facts:

```text
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal
```

Therefore:

```text
Operational Query
    → materialized result

Audit / Reconstruction
    → valuation facts
```

Ordinary balance queries must not require replaying the entire valuation algorithm.

---

# 37. Scope

## In Scope

Phase 8 includes:

1. Valuation Architecture integration with Posting.
2. Valuation layers.
3. Valuation consumption.
4. Valuation adjustments.
5. Valuation allocation.
6. Valuation reversal/compensation semantics.
7. FIFO valuation method.
8. Synthetic consumption.
9. Cost movement materialization.
10. Cost balance materialization.
11. Inventory valuation key aligned with `(product, warehouse)`.
12. Decimal-based monetary valuation.
13. Synchronous valuation in the Posting lifecycle.
14. Separate valuation persistence contracts.
15. Deterministic valuation rebuild.
16. Delayed cost scenario.
17. Unpost valuation compensation.
18. Repost valuation compensation and re-establishment.
19. Cross-domain failure/indeterminate semantics.
20. Posting/Register/Valuation integration tests.
21. Documentation reconciliation for Valuation Architecture.

---

# 38. Explicitly Out of Scope

The following are not part of Phase 8:

* full Sales subsystem;
* new Inventory Issue business document;
* Purchasing cost subsystem;
* accounting ledger;
* financial accounting;
* currency framework;
* exchange rates;
* FX;
* multi-currency valuation;
* LIFO;
* Standard Cost;
* complex production costing;
* period closing;
* financial reporting;
* authorization;
* distributed transaction framework;
* asynchronous valuation infrastructure;
* performance optimization;
* every possible valuation method;
* generalized cost-resource framework beyond Phase 8.

---

# 39. Architecture Acceptance Criteria

Architecture is approved when all of the following are explicitly accepted.

## A. Separation

* [x] Quantity accounting and valuation are separate architectural concerns.
* [x] `Movement` remains cost-free.
* [x] Inventory Register remains quantity-only.
* [x] Valuation cannot modify authoritative Register facts.
* [x] Register mutation remains unaware of valuation.

## B. Valuation Model

* [x] `ValuationLayer` is the primary valuation ownership fact.
* [x] `ValuationConsumption` represents consumption explicitly.
* [x] `ValuationAdjustment` represents valuation corrections.
* [x] `ValuationAllocation` represents explicit adjustment distribution.
* [x] `ValuationReversal` represents lifecycle compensation.
* [x] `CostMovement` is a materialized valuation result.
* [x] `CostBalance` is materialized valuation state.
* [x] Valuation facts are immutable.

## C. Method

* [x] FIFO is the first valuation method.
* [x] FIFO operates on valuation layers.
* [x] FIFO does not define the persistence model.
* [x] Synthetic consumption is accepted as the Phase 8 consumption mechanism.
* [x] Synthetic consumption is explicit and is not inferred from every Register movement.

## D. Lifecycle

* [x] Valuation is triggered synchronously inside the Posting application lifecycle.
* [x] Register mutation occurs before valuation.
* [x] Valuation completes before successful Posting event publication.
* [x] Domain events are not the primary valuation trigger.
* [x] Integration occurs through the existing Posting coordination boundary.

## E. Consistency

* [x] Register/Valuation partial completion has explicit semantics.
* [x] Existing Posting/Persistence indeterminate semantics are reused.
* [x] Valuation failure cannot produce a successful `DocumentPosted`.
* [x] Recovery semantics are explicitly defined.
* [x] Phase 8 does not introduce a distributed transaction framework.

## F. Persistence

* [x] Register and valuation persistence contracts remain separate.
* [x] Valuation facts have an explicit persistence boundary.
* [x] Valuation results have an explicit persistence boundary.
* [x] Physical storage may be shared without merging semantic contracts.

## G. Immutable Lifecycle

* [x] Unpost does not mutate historical valuation facts.
* [x] Repost does not mutate historical valuation facts.
* [x] Reversal is represented by compensating valuation facts.
* [x] Rebuild includes compensating valuation facts in effective state calculation.

## H. Recovery

* [x] Valuation is deterministically rebuildable from valuation facts.
* [x] Materialized results are not the reconstruction source.
* [x] Delayed cost is represented through valuation adjustment.

---

# 40. Implementation Acceptance Criteria

Implementation will be considered complete only when the approved architecture is reflected in the working system.

## A. Domain Model

* [ ] Valuation facts exist according to the approved model.
* [ ] Valuation facts are immutable after persistence.
* [ ] Required invariants are enforced.
* [ ] Monetary values use `Decimal`.
* [ ] Valuation facts preserve provenance and deterministic identity.
* [ ] Compensating valuation facts can reference the effects they reverse.

## B. FIFO

* [ ] FIFO selects valuation layers deterministically.
* [ ] Synthetic consumption creates explicit consumption facts.
* [ ] Partial layer consumption is supported.
* [ ] Multiple-layer consumption is supported.
* [ ] Insufficient valuation quantity is handled explicitly.

## C. Posting Integration

* [ ] Posting successfully establishes quantity and valuation.
* [ ] Valuation failure prevents successful Posting completion.
* [ ] `DocumentPosted` is emitted only after successful valuation.
* [ ] Unposting compensates the previous valuation effect.
* [ ] Reposting compensates the previous valuation effect and establishes the new valuation effect.
* [ ] `RegisterMutationOrchestrator` remains valuation-independent.
* [ ] `PostingEngine` does not acquire Register-internal knowledge.

## D. Consistency / Recovery

* [ ] Determinate valuation failure is distinguished from persistence indeterminacy.
* [ ] Existing Posting/Persistence indeterminate semantics are reused.
* [ ] Partial Register/Valuation completion can be detected.
* [ ] Recovery can reconcile the affected valuation state.
* [ ] Recovery does not require mutation of historical valuation facts.
* [ ] Recovery does not treat an indeterminate operation as successful without reconciliation.

## E. Persistence

* [ ] Valuation fact persistence is independent from Register fact persistence.
* [ ] Valuation result persistence is independent from valuation facts.
* [ ] Rebuild can reconstruct valuation results from valuation facts.
* [ ] Compensating valuation facts participate in rebuild.

## F. Delayed Cost

* [ ] Quantity can be established without final cost.
* [ ] Later cost can be introduced through `ValuationAdjustment`.
* [ ] Quantity remains unchanged after the adjustment.
* [ ] Resulting valuation is deterministic.

## G. Queries

* [ ] Cost balances are available from materialized state.
* [ ] Cost movement history is queryable.
* [ ] Valuation facts remain available for audit/reconstruction.
* [ ] Reversal history remains observable.

## H. Quality

* [ ] Unit tests cover valuation domain invariants.
* [ ] FIFO tests cover normal, partial, multi-layer and insufficient-quantity cases.
* [ ] Integration tests cover Posting → Register → Valuation.
* [ ] Tests cover delayed cost.
* [ ] Tests cover synthetic consumption.
* [ ] Tests cover Unpost compensation.
* [ ] Tests cover Repost compensation and re-establishment.
* [ ] Tests cover rebuild determinism.
* [ ] Tests cover Register-success / Valuation-failure behavior.
* [ ] Tests cover indeterminate/recovery semantics.
* [ ] Ruff passes.
* [ ] Black check passes.
* [ ] Mypy passes.
* [ ] Full test suite passes.

---

# 41. Required Architecture-Level Test Scenarios

## Scenario 1 — Quantity Without Final Cost

```text
Receipt
100 units
cost unavailable
```

Expected:

```text
Register quantity = 100
ValuationLayer exists
No non-zero cost is required
Posting can complete
```

---

## Scenario 2 — FIFO Synthetic Consumption

```text
Layer A = 100 units / 100 cost
Layer B = 50 units / 75 cost

Synthetic consume = 120
```

Expected:

```text
A consumed = 100
B consumed = 20
```

The consumption is explicit and deterministic.

---

## Scenario 3 — Delayed Cost

```text
Receipt = 100 units
initial cost = 0

later adjustment = +100
```

Expected:

```text
quantity = 100
valuation cost = 100
```

No Register Movement is modified.

---

## Scenario 4 — Quantity/Valuation Independence

A valuation operation must not change:

```text
Movement identity
Movement quantity
Register totals
Register dimensions
```

---

## Scenario 5 — Unpost

Given:

```text
Original Posting
    ↓
Register effect
    +
valuation effect
```

Unpost must result in:

```text
Register effect compensated
valuation effect compensated
historical valuation facts preserved
```

---

## Scenario 6 — Repost

Given:

```text
Original Posting
```

Repost must result in:

```text
old Register effect compensated
old valuation effect compensated
new Register effect established
new valuation effect established
```

Historical valuation facts remain immutable.

---

## Scenario 7 — Rebuild

Given identical valuation facts:

```text
Normal processing
```

and:

```text
Rebuild
```

must produce equivalent:

```text
CostMovement
CostBalance
```

including all compensating valuation facts.

---

## Scenario 8 — Register Success / Valuation Failure

If:

```text
Register mutation succeeds
Valuation fails
```

then:

```text
DocumentPosted
```

must not be emitted as successful completion.

The operation must either:

```text
fail deterministically
```

or:

```text
enter existing indeterminate/recovery semantics
```

depending on whether persistence state can be established.

---

## Scenario 9 — Recovery

Given an indeterminate operation:

```text
Posting operation
Register state = committed/unknown
Valuation state = committed/unknown
```

recovery must:

```text
identify operation
        ↓
establish persisted effects
        ↓
complete or compensate valuation
        ↓
restore deterministic state
```

without mutating historical valuation facts.

---

# 42. Dependency Direction

The intended dependency direction is:

```text
                    PostingEngine
                         │
                         ▼
              Posting application boundary
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      Register coordination    Valuation coordination
             │                       │
             ▼                       ▼
      Register architecture    Valuation architecture
             │                       │
             ▼                       ▼
      Quantity facts           Valuation facts
             │                       │
             ▼                       ▼
      Quantity results         Cost results
```

The key architectural rule is:

```text
Valuation
    must not depend on Register mutation implementation.

Register mutation
    must not depend on Valuation implementation.

Posting/application lifecycle
    coordinates both.
```

---

# 43. Architectural Boundaries

The following boundaries are permanent Phase 8 constraints.

## Boundary 1 — Movement

`Movement` represents quantity movement semantics only.

## Boundary 2 — Register

Inventory Register represents quantity state only.

## Boundary 3 — Valuation

Valuation represents cost ownership and valuation state.

## Boundary 4 — Application

Posting coordinates Register and Valuation.

## Boundary 5 — Persistence

Register and Valuation retain separate semantic persistence contracts.

## Boundary 6 — History

Valuation facts are immutable and lifecycle compensation is explicit.

---

# 44. Phase 8 Architectural Target

At the end of Phase 8 the platform should conceptually support:

```text
Operational Document
        ↓
     Posting
        ↓
 Register Movement
        ↓
 Valuation
        ↓
 ┌───────────────────────┐
 │ CostMovement          │
 │ CostBalance           │
 └───────────────────────┘
        ↓
 successful Posting Event
```

while preserving:

```text
Inventory Register
    → quantity only

Valuation Architecture
    → cost only
```

The essential architectural result is:

> **A quantity movement can participate in valuation without becoming a cost-bearing movement, and valuation can evolve without redesigning the quantity Register.**

---

# 45. Phase 8 Definition of Done

Phase 8 architecture is complete when:

1. FIFO is implemented as a valuation method over valuation layers.
2. Synthetic consumption produces explicit valuation consumption facts.
3. Quantity and valuation remain separate domains.
4. Valuation is integrated synchronously into Posting.
5. Valuation completes before successful Posting events.
6. Valuation persistence is semantically separate from Register persistence.
7. Cost movements and balances are materialized.
8. Valuation can be deterministically rebuilt from valuation facts.
9. Delayed cost is represented by explicit adjustment.
10. Inventory quantity remains unchanged by valuation corrections.
11. No Inventory Issue document is required for Phase 8.
12. Unpost is represented by compensating valuation facts.
13. Repost compensates the previous valuation effect and establishes a new one.
14. Historical valuation facts remain immutable.
15. Cross-domain partial completion uses the existing indeterminate/recovery semantics.
16. No distributed transaction framework is introduced.
17. The implementation satisfies the approved Architecture and subsequent Concrete API Design.
18. Full quality gates pass.
19. Architecture documentation is reconciled with the final implementation.

---

# 46. Next Phase 8 Workflow

The Architecture Definition is now considered final and approved.

The next workflow is:

```text
Final Architecture Definition
        ↓
Concrete API Design
        ↓
API Review
        ↓
Implementation
        ↓
Tests / Quality Gate
        ↓
Documentation Reconciliation
        ↓
Final Review
        ↓
Commit / Push
```

Implementation must not begin before Concrete API Design has been reviewed and approved.

---

# 47. Final Architectural Statement

Phase 8 does not extend the Inventory Register into a costing register.

It introduces a parallel valuation architecture coordinated by the application lifecycle.

The resulting platform model is:

```text
                 ┌───────────────────────┐
                 │     Posting Engine    │
                 └───────────┬───────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
        Register Architecture    Valuation Architecture
                 │                       │
                 ▼                       ▼
          Quantity Facts          Valuation Facts
                 │                       │
                 ▼                       ▼
        Quantity State          CostMovement / CostBalance
                 │                       │
                 └───────────┬───────────┘
                             ▼
                    Successful Posting
                             │
                             ▼
                     DocumentPosted
```

The central invariant remains:

> **Quantity accounting and valuation are related through the business lifecycle, but they remain independent architectural concerns.**
