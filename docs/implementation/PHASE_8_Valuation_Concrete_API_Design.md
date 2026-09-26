# Phase 8 — Valuation Architecture

## Concrete API Design

**Status:** Final
**Phase:** 8
**Scope:** Valuation Architecture — FIFO + Synthetic Consumption
**Prerequisite:** Approved Phase 8 Architecture Definition / Scope and completed API Review
**Implementation status:** Not started

---

## 1. Purpose

This document defines the concrete public API for introducing valuation into the AcCoreD working business lifecycle.

The API must preserve the architectural separation established by Phase 8:

* quantity accounting remains the responsibility of the Register subsystem;
* valuation remains an independent subsystem;
* valuation does not become embedded into `RegisterMutationOrchestrator`;
* `PostingEngine` remains an application-level lifecycle orchestrator;
* valuation participates synchronously in posting;
* valuation completion is required before the corresponding posting domain event is published.

The first valuation method implemented by Phase 8 is:

> **FIFO with synthetic consumption.**

Phase 8 does not introduce a new Inventory Issue business document. Consumption is generated explicitly by the valuation subsystem from an application-level valuation request.

---

# 2. Architectural Boundaries

The dependency direction is:

```text
PostingEngine
    │
    ▼
PostingResultCoordinator
    │
    ├── RegisterPostingResultCoordinator
    │
    └── ValuationPostingCoordinator
             │
             ├── ValuationCoordinator
             ├── ValuationMethod
             ├── ValuationFactPersistence
             └── ValuationResultPersistence
```

The following responsibilities remain separate.

### Register subsystem

Responsible for:

* authoritative quantity movements;
* quantity dimensions;
* quantity totals;
* quantity balances;
* register movement persistence.

### Valuation subsystem

Responsible for:

* valuation layers;
* valuation consumption;
* valuation adjustments;
* valuation allocations;
* valuation reversals;
* FIFO layer selection;
* synthetic consumption;
* cost movements;
* cost balances;
* valuation rebuild.

### Posting subsystem

Responsible for:

* document lifecycle;
* handler execution;
* movement validation;
* posting result coordination;
* domain event publication.

`PostingEngine` must not contain FIFO logic, layer selection logic, cost calculation logic, or valuation persistence logic.

---

# 3. Package Structure

The Phase 8 implementation introduces:

```text
src/accore/platform/valuation/
    __init__.py
    facts.py
    key.py
    errors.py
    persistence.py
    results.py
    consumption.py
    fifo.py
    engine.py
    coordinator.py
    reversal.py
```

The exact internal module decomposition may be refined during implementation provided that the public semantic boundaries defined by this document remain unchanged.

---

# 4. Core Valuation Identity

Valuation dimensions are independent from Register dimensions at the API level.

Phase 8 Inventory valuation nevertheless uses the same logical dimensions:

```text
(product, warehouse)
```

This produces the following conceptual relationship:

```text
RegisterKey(product, warehouse)
        │
        │ semantic alignment
        ▼
ValuationKey(product, warehouse)
```

This is alignment, not identity.

The valuation subsystem must not depend on the Register key implementation.

---

# 5. `ValuationKey`

```python
@dataclass(frozen=True, slots=True)
class ValuationKey:
    dimensions: Mapping[str, str]
```

Requirements:

* immutable;
* deterministic;
* semantically comparable;
* suitable for persistence lookup;
* independent of Register-specific key classes.

The canonical representation must provide deterministic dimension ordering.

The implementation must not rely on incidental dictionary insertion order for identity semantics.

---

# 6. Authoritative Valuation Facts

Valuation facts are immutable and append-only.

The Phase 8 fact model consists of:

```text
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal
```

These form:

```python
ValuationFact = (
    ValuationLayer
    | ValuationConsumption
    | ValuationAdjustment
    | ValuationAllocation
    | ValuationReversal
)
```

No valuation fact may be updated or physically deleted as part of normal lifecycle processing.

Corrections are represented by additional facts.

---

# 7. `ValuationLayer`

A valuation layer represents a quantity available for valuation consumption.

Proposed API:

```python
@dataclass(frozen=True, slots=True)
class ValuationLayer:
    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    total_cost: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime
```

## Invariants

* `quantity > 0`;
* `total_cost >= 0`;
* monetary values are `Decimal`;
* no floating-point monetary values;
* source identities are immutable;
* the layer cannot be updated.

### Zero initial cost

`Decimal("0")` is a valid and complete valuation value.

The API deliberately does **not** distinguish between:

* genuinely zero-cost goods;
* goods whose initial cost information is not available at receipt time.

Both are represented identically.

For example:

```text
quantity = 100
total_cost = 0
```

creates a normal valuation layer.

Later additional acquisition-related costs may be represented through:

```text
ValuationAdjustment
        ↓
ValuationAllocation
```

No separate "unknown cost" or "deferred cost" state is introduced.

---

# 8. Monetary Representation

Phase 8 uses:

```python
Decimal
```

for all monetary values.

No:

* `float`;
* currency;
* FX rate;
* multi-currency amount;
* implicit binary floating-point conversion

is introduced.

The authoritative monetary representation of a valuation layer is:

```text
total_cost
```

rather than `unit_cost`.

This avoids introducing an implicit rounding contract for:

```text
quantity × unit_cost
```

and provides an unambiguous representation for delayed cost adjustments.

---

# 9. `ValuationConsumption`

A consumption fact records the valuation consumption of quantity from a specific layer.

```python
@dataclass(frozen=True, slots=True)
class ValuationConsumption:
    identity: Identifier
    valuation_key: ValuationKey
    layer_identity: Identifier
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

Invariants:

* `quantity > 0`;
* `cost >= 0`;
* `layer_identity` identifies an existing valuation layer;
* the fact is immutable;
* consumption never creates a Register Movement.

The `source_identity` identifies the valuation operation that caused the consumption.

---

# 10. `ValuationAdjustment`

An adjustment represents an additional valuation amount.

```python
@dataclass(frozen=True, slots=True)
class ValuationAdjustment:
    identity: Identifier
    valuation_key: ValuationKey
    amount: Decimal
    source_identity: Identifier
    reason: str
    created_at: datetime
```

An adjustment:

* does not change Register quantity;
* does not modify an existing `ValuationLayer`;
* does not modify an existing `ValuationConsumption`;
* is itself immutable.

The adjustment may subsequently be allocated to one or more valuation layers.

---

# 11. `ValuationAllocation`

An allocation connects an adjustment with valuation layers.

```python
@dataclass(frozen=True, slots=True)
class ValuationAllocation:
    identity: Identifier
    adjustment_identity: Identifier
    layer_identity: Identifier
    valuation_key: ValuationKey
    amount: Decimal
    created_at: datetime
```

The allocation is also immutable.

The effective valuation of a layer is therefore derived from:

```text
original layer cost
+
allocated adjustments
-
applicable reversals
```

without modifying the original layer.

---

# 12. `ValuationReversal`

Unpost and repost must remain compatible with immutable valuation facts.

Therefore valuation removal is implemented through compensating facts.

```python
@dataclass(frozen=True, slots=True)
class ValuationReversal:
    identity: Identifier
    reversed_identity: Identifier
    valuation_key: ValuationKey
    source_identity: Identifier
    created_at: datetime
```

A reversal:

* never deletes the reversed fact;
* never mutates the reversed fact;
* records the compensating relationship explicitly;
* participates in rebuild and effective-state calculation.

The architecture therefore remains append-only.

---

# 13. Valuation Fact Persistence

```python
class ValuationFactPersistence(Protocol):

    def append(
        self,
        facts: Sequence[ValuationFact],
    ) -> None:
        ...

    def find_by_source_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        ...

    def find_by_source_movement(
        self,
        movement_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
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

The semantic contract is append-only.

The physical persistence provider may use:

* a common table;
* separate tables;
* indexes;
* another storage representation.

That implementation detail must not alter the semantic API.

---

# 14. Derived Valuation Results

Valuation facts are authoritative.

Cost results are derived and rebuildable.

The derived result model consists of:

```text
CostMovement
CostBalance
```

This distinction is fundamental:

```text
ValuationFactPersistence
    authoritative

ValuationResultPersistence
    derived / materialized / rebuildable
```

---

# 15. `CostMovement`

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

`CostMovement` is a derived valuation result.

It is not a replacement for valuation facts.

---

# 16. `CostBalance`

```python
@dataclass(frozen=True, slots=True)
class CostBalance:
    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    calculated_at: datetime
```

`CostBalance` is a materialized result.

It may be replaced/rebuilt because it is not an authoritative immutable valuation fact.

---

# 17. `ValuationResultPersistence`

```python
class ValuationResultPersistence(Protocol):

    def append_movements(
        self,
        movements: Sequence[CostMovement],
    ) -> None:
        ...

    def replace_balance(
        self,
        balance: CostBalance,
    ) -> None:
        ...

    def find_movements(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[CostMovement, ...]:
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

`replace_balance()` is permitted specifically because `CostBalance` is derived state.

It must not be interpreted as permission to update authoritative valuation facts.

---

# 18. Valuation Input Boundary

Existing Register `Movement` deliberately has no valuation-specific cost field.

Valuation therefore receives an explicit input representation.

```python
@dataclass(frozen=True, slots=True)
class ValuationInput:
    valuation_key: ValuationKey
    quantity: Decimal
    cost: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    occurred_at: datetime
```

Provider:

```python
class ValuationInputProvider(Protocol):

    def for_movement(
        self,
        movement: Movement,
    ) -> ValuationInput:
        ...
```

For Phase 8 Inventory:

```text
cost = Decimal("0")
```

is valid.

The provider does not need to identify why the cost is zero.

Later additional acquisition-related cost is handled independently through valuation adjustment.

---

# 19. Valuation Method

The valuation method is isolated behind a strategy interface.

```python
class ValuationMethod(Protocol):

    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult:
        ...
```

The method must not know about:

* PostingEngine;
* RegisterMutationOrchestrator;
* domain events;
* persistence implementation.

---

# 20. `ConsumptionRequest`

```python
@dataclass(frozen=True, slots=True)
class ConsumptionRequest:
    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    source_identity: Identifier
    occurred_at: datetime
```

Requirements:

* quantity must be positive;
* valuation key must be valid;
* source identity must be deterministic;
* request is immutable.

---

# 21. `ConsumptionResult`

```python
@dataclass(frozen=True, slots=True)
class ConsumptionResult:
    consumptions: tuple[ValuationConsumption, ...]
    total_cost: Decimal
    remaining_layers: tuple[ValuationLayer, ...]
```

This is an algorithm-level result.

It is not itself an application lifecycle operation.

It must not persist anything.

---

# 22. FIFO Valuation

Phase 8 provides:

```python
class FIFOValuationMethod:
    ...
```

FIFO consumes available valuation layers in deterministic creation order.

Conceptually:

```text
Layer 1
    ↓
Layer 2
    ↓
Layer 3
    ↓
consume requested quantity
```

The algorithm must:

1. identify layers for the requested `ValuationKey`;
2. order them deterministically;
3. consume the oldest available quantity first;
4. calculate consumption cost;
5. produce immutable `ValuationConsumption` facts;
6. report insufficient quantity when applicable.

FIFO must not mutate persisted layers.

---

# 23. Synthetic Consumption

Synthetic consumption is an explicit valuation operation.

```python
class SyntheticConsumptionService(Protocol):

    def consume(
        self,
        request: ConsumptionRequest,
    ) -> ConsumptionResult:
        ...
```

Synthetic consumption:

* is not a business document;
* does not create a Register Movement;
* does not modify quantity accounting;
* operates entirely inside valuation;
* produces valuation consumption facts and cost results.

The explicitness requirement means that synthetic consumption must be visible in the API and implementation rather than hidden inside a generic cost calculation.

---

# 24. `ValuationPlan`

A central Phase 8 API object is the deterministic valuation plan.

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    operation_identity: Identifier
    source_document_identity: Identifier
    valuation_inputs: tuple[ValuationInput, ...]
    layers: tuple[ValuationLayer, ...]
    consumption: ConsumptionResult
    facts: tuple[ValuationFact, ...]
```

The plan represents the result of valuation preflight.

It is:

* immutable;
* deterministic;
* not persisted by `prepare()`;
* safe to use after Register authoritative mutation.

The plan contains all deterministic valuation-domain decisions that could otherwise fail after Register commit.

---

# 25. Valuation Preflight

The valuation coordinator exposes a preparation step:

```python
class ValuationCoordinator(Protocol):

    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> ValuationPlan:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: ValuationPlan,
    ) -> None:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None:
        ...
```

`prepare()`:

* performs valuation input resolution;
* validates valuation applicability;
* loads relevant layers;
* executes FIFO;
* validates sufficient valuation quantity;
* constructs the deterministic valuation plan;
* performs no authoritative persistence.

This prevents a deterministic valuation-domain failure from occurring after Register facts have already been committed.

---

# 26. Establish Lifecycle

The complete posting flow is:

```text
PostingEngine.post()
        │
        ├── handler.post()
        │
        ├── movement validation
        │
        ├── valuation.prepare()
        │       │
        │       └── ValuationPlan
        │
        ├── RegisterCoordinator.establish()
        │
        ├── ValuationCoordinator.establish(plan)
        │
        ├── posting result success
        │
        └── DocumentPosted
```

The authoritative lifecycle order is therefore:

```text
deterministic valuation preparation
        ↓
Register authoritative mutation
        ↓
Valuation authoritative mutation
        ↓
success
        ↓
DocumentPosted
```

This preserves the architectural requirement that valuation is applied after successful register mutation while preventing predictable valuation-domain failure from occurring between the two authoritative commits.

---

# 27. Partial Commit Semantics

AcCoreD Phase 8 does not introduce a distributed transaction between Register and Valuation.

Therefore the API must explicitly recognize:

```text
Register facts
+
Valuation facts
```

as separate persistence boundaries.

The following states are possible.

### State A — preflight failure

```text
Register = unchanged
Valuation = unchanged
```

The posting operation fails normally.

### State B — Register persistence failure

```text
Register = unchanged
Valuation = unchanged
```

Posting maps the persistence error through existing Posting error semantics.

### State C — Register committed, valuation persistence succeeds

```text
Register = applied
Valuation = applied
```

Posting succeeds and `DocumentPosted` is emitted.

### State D — Register committed, valuation persistence fails deterministically

This state must be prevented by `prepare()` for all deterministic valuation-domain errors.

Only persistence-related failures are allowed to remain after authoritative Register mutation.

### State E — valuation persistence is indeterminate

```text
Register = applied
Valuation = unknown
```

This is an indeterminate posting state.

Existing:

```text
PersistenceIndeterminateError
```

semantics must be preserved.

`PostingEngine` maps this to:

```text
PostingIndeterminateError
```

and must not publish `DocumentPosted`.

Recovery/reconciliation is required before the operation can be considered complete.

---

# 28. Error Boundary

The valuation subsystem may expose domain-specific errors such as:

```python
class ValuationError(Exception):
    ...

class ValuationValidationError(ValuationError):
    ...

class ValuationConflictError(ValuationError):
    ...

class ValuationInsufficientQuantityError(ValuationError):
    ...

class ValuationNotFoundError(ValuationError):
    ...
```

These represent deterministic domain failures.

Persistence failures must reuse the existing persistence semantics:

```text
PersistenceError
PersistenceIndeterminateError
```

rather than creating parallel persistence error hierarchies.

The Posting layer remains responsible for mapping:

```text
PersistenceError
    ↓
PostingPersistenceError

PersistenceIndeterminateError
    ↓
PostingIndeterminateError
```

---

# 29. `PostingResultCoordinator` Integration

The existing public posting contract remains:

```python
class PostingResultCoordinator(Protocol):

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> None:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None:
        ...
```

The existing `PostingEngine` must not be changed to understand valuation-specific types.

Instead, the standard configuration composes the existing Register coordinator with the new valuation coordinator.

Conceptually:

```text
CompositePostingResultCoordinator
    │
    ├── RegisterPostingResultCoordinator
    │
    └── ValuationPostingCoordinator
```

The composite coordinator remains compatible with:

```python
PostingEngine(..., result_coordinator=...)
```

---

# 30. Composite Establish

The composite coordinator performs:

```text
prepare valuation
        ↓
register establish
        ↓
valuation establish
```

The valuation plan must be retained for the same operation.

No second nondeterministic FIFO calculation may occur between Register and Valuation establishment.

Therefore:

```text
prepare()
    → ValuationPlan
        ↓
establish(plan)
```

must be used.

---

# 31. Composite Remove

For unpost:

```text
PostingEngine.unpost()
        ↓
CompositePostingResultCoordinator.remove()
        │
        ├── Register removal
        │
        └── Valuation reversal
```

Valuation removal does not delete historical valuation facts.

Instead:

```text
historical facts
      +
ValuationReversal
```

produce the compensated effective state.

The exact ordering and recovery semantics must preserve the same indeterminate-state contract as establish.

---

# 32. Repost

The existing Phase 7 `PostingEngine.repost()` lifecycle replaces the previous posting result by removing the old result before establishing the new result. Phase 8 must preserve that public lifecycle while adding a mandatory valuation preflight for the replacement operation.

The critical ordering invariant is:

```text
prepare(new)
    BEFORE
remove(old)
```

Therefore the Phase 8 repost lifecycle is:

```text
new MovementSet generation
        ↓
new Movement validation
        ↓
valuation.prepare(new MovementSet)
        ↓
ValuationPlan
        ↓
remove(old result)
        │
        ├── Register removal
        └── Valuation reversal
        ↓
establish(new result)
        │
        ├── Register establish
        └── Valuation establish(ValuationPlan)
        ↓
DocumentReposted
```

`valuation.prepare(new MovementSet)` MUST complete before the old result is removed. This prevents a deterministic valuation failure from destroying the previously established successful state.

If preparation fails deterministically:

```text
old Register state   = unchanged
old Valuation state  = unchanged
new Register state   = not established
new Valuation state  = not established
DocumentReposted     = not published
```

No removal MUST have occurred in this case.

The prepared `ValuationPlan` is the immutable hand-off between replacement preflight and the subsequent establishment. `establish()` MUST consume that plan rather than re-running FIFO against changed state.

Historical valuation facts remain immutable. Valuation removal is represented by compensating reversal facts rather than deletion.

---

# 33. Operation Identity and Idempotency

Valuation operations must be deterministic and repeatable.

An operation identity must be derived from stable business/application identities.

At minimum it must distinguish:

```text
document identity
source movement identity
operation kind
```

The exact concrete representation may reuse the existing `Identifier` abstraction.

The important invariant is:

> Repeating the same logical valuation operation must not accidentally create a second independent valuation effect.

This applies to:

* establish;
* reversal;
* repost;
* recovery;
* rebuild.

---

# 34. Adjustment API

Additional valuation costs are represented explicitly.

Conceptual API:

```python
class ValuationAdjustmentService(Protocol):

    def adjust(
        self,
        adjustment: ValuationAdjustment,
    ) -> tuple[ValuationAllocation, ...]:
        ...
```

The service must:

1. validate the adjustment;
2. identify applicable valuation layers;
3. determine allocations;
4. persist immutable adjustment/allocation facts;
5. update/rebuild derived cost results as required.

The original valuation layer remains unchanged.

---

# 35. Reversal API

Conceptual API:

```python
class ValuationReversalService(Protocol):

    def reverse(
        self,
        fact_identity: Identifier,
        source_identity: Identifier,
    ) -> ValuationReversal:
        ...
```

The service creates a new immutable reversal fact.

It must not delete or update the reversed fact.

Repeated reversal of the same logical fact must be detected as a conflict or idempotent operation according to the final persistence implementation.

---

# 36. Rebuild

Valuation rebuild is based exclusively on authoritative valuation facts.

```text
ValuationFactPersistence
        ↓
valuation engine
        ↓
CostMovement
        ↓
CostBalance
        ↓
ValuationResultPersistence
```

Existing `CostBalance` must never be treated as authoritative input to rebuild.

Conceptual API:

```python
@dataclass(frozen=True, slots=True)
class ValuationRebuildResult:
    processed_facts: int
    generated_movements: int
    generated_balances: int
    consistent: bool
```

And:

```python
class ValuationRebuilder(Protocol):

    def rebuild(self) -> ValuationRebuildResult:
        ...
```

Rebuild must be deterministic.

---

# 37. Query API

Valuation query APIs must distinguish facts from derived results.

Conceptual interfaces:

```python
class ValuationFactQueryService(Protocol):

    def find_by_valuation_key(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationFact, ...]:
        ...

    def find_by_source_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        ...
```

And:

```python
class ValuationQueryService(Protocol):

    def get_balance(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance | None:
        ...

    def get_movements(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[CostMovement, ...]:
        ...
```

---

# 38. Independence from Quantity Accounting

The following invariant is mandatory:

> Removing or changing valuation must not require changing the semantic Register Movement model.

In particular:

```text
Register Movement
    ≠
Cost Movement
```

and:

```text
ValuationConsumption
    ≠
Register Movement
```

Synthetic consumption must never enter quantity accounting.

Likewise:

```text
Register quantity
```

must remain correct even when:

```text
initial valuation cost = 0
```

or valuation is later adjusted.

---

# 39. Delayed Cost

Phase 8 explicitly supports:

```text
Receipt:
    quantity = 100
    initial cost = 0

Later:
    additional cost = 100
```

The lifecycle is:

```text
ValuationLayer
    quantity = 100
    total_cost = 0

        ↓

ValuationAdjustment
    amount = 100

        ↓

ValuationAllocation
    amount = 100
    layer = original layer
```

The resulting effective valuation becomes:

```text
quantity = 100
effective cost = 100
```

The original layer remains unchanged.

No special "deferred" state is required.

---

# 40. Persistence Consistency

Phase 8 deliberately does not require distributed transactions.

Instead it uses:

1. deterministic preflight;
2. authoritative append-only facts;
3. explicit indeterminate persistence semantics;
4. rebuildable derived results;
5. explicit reversal facts;
6. recovery/reconciliation.

This follows the existing AcCoreD persistence philosophy.

The API must never claim atomicity across independent Register and Valuation persistence providers unless such atomicity is actually provided by the infrastructure.

---

# 41. Standard Inventory Composition

The Standard layer is responsible for composing the concrete Phase 8 platform.

Conceptually:

```text
StandardConfigurationBootstrap
        │
        ├── Register platform
        │
        ├── Valuation persistence
        │
        ├── FIFO valuation engine
        │
        ├── Valuation coordinator
        │
        └── Composite PostingResultCoordinator
```

The Standard layer supplies the initial:

```text
Inventory ValuationKey
ValuationInputProvider
FIFOValuationMethod
```

The generic platform remains independent of the Standard Inventory implementation.

---

# 42. Phase 8 Public API Surface

The public API should expose only the concepts required by platform/application integration.

Expected public concepts include:

```text
ValuationKey

ValuationFact
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal

ValuationInput
ValuationPlan

CostMovement
CostBalance

ConsumptionRequest
ConsumptionResult

ValuationMethod
FIFOValuationMethod

ValuationCoordinator
ValuationPostingCoordinator

ValuationFactPersistence
ValuationResultPersistence

ValuationQueryService
ValuationFactQueryService

ValuationRebuilder
ValuationRebuildResult
```

Implementation helpers remain private unless a concrete integration point requires otherwise.

---

# 43. API Invariants

The implementation must preserve all of the following.

### INV-01 — Register independence

Valuation does not own quantity accounting.

### INV-02 — Immutable facts

Valuation facts are never updated or deleted.

### INV-03 — Append-only correction

Corrections use additional facts.

### INV-04 — Zero cost is valid

`Decimal("0")` is a normal valuation cost.

### INV-05 — No deferred-cost state

The API does not distinguish why initial cost is zero.

### INV-06 — Synthetic consumption isolation

Synthetic consumption never creates Register Movement.

### INV-07 — FIFO isolation

FIFO logic does not depend on PostingEngine or persistence implementation.

### INV-08 — Deterministic preparation

All deterministic valuation-domain failures occur during preflight. For repost, replacement valuation preparation completes before removal of the previously established result.

### INV-09 — No cross-domain transaction claim

Register and Valuation are separate persistence boundaries.

### INV-10 — Existing persistence semantics

`PersistenceError` and `PersistenceIndeterminateError` remain the cross-layer persistence failure semantics.

### INV-11 — Event ordering

`DocumentPosted`, `DocumentUnposted`, and `DocumentReposted` are published only after the corresponding logical operation has completed successfully.

### INV-12 — Rebuildability

Derived cost results can be reconstructed from authoritative valuation facts.

### INV-13 — Immutable reversal

Unpost/repost does not mutate historical valuation facts.

### INV-14 — Deterministic operation identity

Repeated logical operations must be identifiable and must not accidentally produce duplicate effects.

### INV-15 — Decimal-only monetary values

All valuation monetary values use `Decimal`.

---

# 44. Required Test Surface

Implementation must provide tests for the following groups.

## 44.1 Domain facts

* immutable `ValuationLayer`;
* immutable `ValuationConsumption`;
* immutable `ValuationAdjustment`;
* immutable `ValuationAllocation`;
* immutable `ValuationReversal`;
* zero-cost layer;
* Decimal-only monetary semantics.

## 44.2 FIFO

* one layer;
* multiple layers;
* partial layer consumption;
* exact layer consumption;
* multiple-layer consumption;
* insufficient quantity;
* deterministic ordering;
* zero-cost layers.

## 44.3 Synthetic consumption

* produces valuation facts;
* does not produce Register Movement;
* produces deterministic operation identity.

## 44.4 Delayed cost

* zero-cost layer;
* adjustment;
* allocation;
* effective cost calculation;
* unchanged original layer.

## 44.5 Reversal

* original fact remains;
* reversal is appended;
* effective state is compensated;
* repeated reversal is handled deterministically.

## 44.6 Posting integration

* successful post;
* valuation preflight failure;
* Register failure;
* valuation persistence failure;
* valuation persistence indeterminate state;
* no event on failure;
* event after complete success.

## 44.7 Repost

* new valuation is prepared before old result removal;
* deterministic preparation failure leaves the old result untouched;
* old valuation effect is compensated;
* new valuation effect is established from the prepared plan;
* historical facts are retained;
* movement/valuation identity remains deterministic;
* no `DocumentReposted` event is published when replacement preparation fails.

## 44.8 Rebuild

* facts are sufficient to reconstruct results;
* derived results may be discarded and rebuilt;
* rebuild does not use existing balances as authoritative input;
* repeated rebuild is deterministic.

## 44.9 Independence

* quantity balance remains correct for zero-cost goods;
* valuation adjustment does not alter quantity;
* synthetic consumption does not alter Register totals.

---

# 45. Acceptance Criteria

Phase 8 Concrete API Design is considered implementation-ready when:

1. the valuation API is isolated from Register quantity semantics;
2. FIFO is represented as a replaceable valuation method;
3. synthetic consumption is explicit;
4. zero initial cost is fully supported;
5. no known-zero/unknown-cost distinction exists in the API;
6. valuation facts are immutable and append-only;
7. delayed cost is represented by adjustment/allocation facts;
8. unpost/repost use immutable reversal semantics;
9. deterministic valuation errors are resolved during preflight;
10. `ValuationPlan` bridges preflight and authoritative establishment;
11. Register and Valuation partial-commit semantics are explicit;
12. existing persistence indeterminate semantics are reused;
13. `PostingEngine` remains valuation-agnostic;
14. integration uses the existing `PostingResultCoordinator` boundary;
15. `CostMovement` and `CostBalance` are explicitly derived results;
16. valuation rebuild operates from authoritative facts;
17. operation identity is deterministic;
18. the complete test surface defined above is covered;
19. no Phase 9+ functionality is introduced;
20. documentation is reconciled with the implemented API after completion.

---

# 46. Explicit Non-Goals

The Phase 8 API does not introduce:

* Sales documents;
* Inventory Issue business documents;
* purchasing cost subsystem;
* accounting ledger;
* currency;
* FX;
* multi-currency;
* LIFO;
* Standard Cost;
* production costing;
* period closing;
* financial reporting;
* authorization;
* distributed transactions;
* asynchronous valuation infrastructure;
* performance optimization framework;
* generalized multi-method valuation configuration beyond the abstraction required by FIFO.

---

# 47. Implementation Constraint

This document is the final Concrete API Design.

**Implementation must not introduce additional architectural responsibilities merely because they are convenient during coding.**

If implementation reveals a requirement that changes:

* persistence semantics;
* lifecycle ordering;
* immutable fact model;
* Register/Valuation boundary;
* PostingResultCoordinator integration;
* error semantics;
* reversal semantics;

then implementation must stop and the architecture/API documentation must be amended and reviewed before proceeding.

---

# 48. Final API Model

The resulting Phase 8 architecture can be summarized as:

```text
                    PostingEngine
                         │
                         ▼
             PostingResultCoordinator
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
        Register Coordinator   Valuation Coordinator
              │                     │
              │              ┌──────┴──────┐
              │              │             │
              │          prepare()      establish()
              │              │             │
              │              ▼             │
              │       ValuationPlan        │
              │              │             │
              ▼              │             ▼
       Register Facts        │      Valuation Facts
              │              │             │
              │              └──────┬──────┘
              │                     │
              ▼                     ▼
       Quantity Results       Cost Results
                                  │
                         CostMovement / CostBalance
```

The lifecycle contract is:

```text
POST

MovementSet
    │
    ├── deterministic valuation preflight
    │       ↓
    │   ValuationPlan
    │
    ├── Register authoritative mutation
    │
    ├── Valuation authoritative mutation
    │
    └── success
            ↓
       DocumentPosted
```

For `REPOST`, the preflight has an additional ordering requirement:

```text
new MovementSet
    ↓
new Movement validation
    ↓
valuation.prepare(new)
    ↓
ValuationPlan
    ↓
remove(old)
    ↓
establish(new, ValuationPlan)
    ↓
DocumentReposted
```

The mandatory invariant is:

```text
prepare(new) fails
        ⇒
remove(old) is not executed
```

The valuation principle remains:

```text
Quantity accounting
        │
        │ independent
        ▼
Valuation
        │
        ├── FIFO
        ├── Synthetic Consumption
        ├── Adjustments
        ├── Allocations
        └── Reversals
```

This completes the **Phase 8 Concrete API Design** and establishes the API boundary for implementation.
