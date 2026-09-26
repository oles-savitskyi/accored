# PHASE 8 — WP-5 Valuation Establishment

## Concrete API Design

**Status:** Final — Implementation Completed and Reviewed
**Phase:** 8 — Valuation
**Work Package:** WP-5 — Valuation Establishment
**Implementation status:** Completed
**Precondition:** Architecture Definition / Scope approved; Concrete API Review completed

---

## 1. Purpose

WP-5 implements the establishment boundary between an already prepared `ValuationPlan` and authoritative persisted valuation state.

The purpose of the component is to:

1. validate the complete valuation plan;
2. resolve references between operations inside the same plan;
3. construct authoritative valuation facts;
4. construct derived `CostMovement` instances;
5. persist authoritative valuation facts;
6. persist derived cost movements;
7. delegate balance aggregation to the Cost Totals Engine;
8. materialize the resulting `CostBalance`;
9. return an explicit establishment outcome.

WP-5 does **not**:

* calculate FIFO;
* prepare valuation plans;
* mutate registers;
* modify `PostingEngine`;
* introduce a distributed transaction;
* make `CostBalance` authoritative;
* implement rebuild or repair workflows;
* introduce exactly-once semantics beyond guarantees already provided by persistence.

---

# 2. Architectural Position

The complete valuation flow is:

```text
MovementSet
    │
    ▼
ValuationEngine.prepare(...)
    │
    ▼
ValuationPlan
    │
    ▼
ValuationCoordinator.establish(...)
    │
    ├── validate complete plan
    │
    ├── resolve intra-plan references
    │
    ├── create authoritative valuation facts
    │
    ├── create CostMovements
    │
    ├── persist valuation facts
    │
    ├── persist CostMovements
    │
    ├── CostTotalsEngine
    │
    └── persist/materialize CostBalance
```

The separation of responsibilities is mandatory:

```text
ValuationEngine
    = preparation

ValuationCoordinator
    = establishment orchestration

ValuationFactPersistence
    = authoritative valuation state

CostTotalsEngine
    = cost aggregation

ValuationResultPersistence
    = derived cost results

PostingEngine
    = posting lifecycle
```

The coordinator must not absorb responsibilities belonging to any of these components.

---

# 3. Existing WP-4 API

WP-5 consumes the following approved WP-4 concepts.

```python
@dataclass(frozen=True, slots=True)
class ValuationInput:
    request: ConsumptionRequest
    layers: tuple[ValuationLayer, ...]
```

```python
class ValuationEngine:
    def prepare(
        self,
        movement_set: MovementSet,
    ) -> ValuationPlan:
        ...
```

The existing plan operations are amended by the intra-plan reference model defined in this document.

---

# 4. Valuation Plan

## 4.1 Planned Layer Reference

A newly established layer does not have its authoritative persistence identity until establishment.

Therefore a plan must distinguish a planning reference from an already persisted layer identity.

```python
@dataclass(frozen=True, slots=True)
class PlannedLayerReference:
    value: Identifier
```

`PlannedLayerReference` is:

* immutable;
* local to the `ValuationPlan`;
* not an authoritative persistence identity;
* resolved only during establishment.

---

## 4.2 Persisted Layer Reference

Existing layers are referenced through their authoritative identity.

```python
@dataclass(frozen=True, slots=True)
class PersistedLayerReference:
    identity: Identifier
```

---

## 4.3 Layer Reference

```python
type LayerReference = (
    PlannedLayerReference
    | PersistedLayerReference
)
```

This distinction explicitly supports both:

```text
existing persisted layer
```

and:

```text
layer created earlier in the same ValuationPlan
```

---

# 5. LayerEstablishmentPlan

Final API:

```python
@dataclass(frozen=True, slots=True)
class LayerEstablishmentPlan:
    reference: PlannedLayerReference
    valuation_key: ValuationKey
    quantity: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime
```

Semantics:

* `quantity > 0`;
* the resulting `ValuationLayer.total_cost` is initially `Decimal(0)`;
* `reference` identifies the planned layer inside the plan;
* authoritative layer identity is generated during establishment;
* source document and movement identities remain authoritative provenance.

No `total_cost` field is added to `LayerEstablishmentPlan`.

This preserves the approved delayed-cost architecture.

A zero-cost layer is valid.

For example:

```text
Receipt
    quantity = 10
    initial cost = 0
```

produces:

```text
ValuationLayer
    quantity   = 10
    total_cost = 0
```

A later valuation adjustment may establish the corresponding cost effect.

---

# 6. ConsumptionPlan

Final API:

```python
@dataclass(frozen=True, slots=True)
class ConsumptionPlan:
    valuation_key: ValuationKey
    layer_reference: LayerReference
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

Semantics:

* `quantity > 0`;
* `cost >= 0`;
* quantity and cost represent the positive semantic consumption fact;
* the referenced layer must belong to the same `valuation_key`;
* a `PlannedLayerReference` must resolve to a layer established earlier in the same plan;
* a `PersistedLayerReference` must resolve to an existing available layer.

The resulting `ValuationConsumption` remains a positive fact.

---

# 7. ValuationPlan

```python
type ValuationPlanOperation = (
    LayerEstablishmentPlan
    | ConsumptionPlan
)
```

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    operations: tuple[ValuationPlanOperation, ...]
```

The tuple order is authoritative for intra-plan dependency resolution.

For example:

```text
1. LayerEstablishmentPlan(reference=P1)
2. ConsumptionPlan(layer_reference=P1)
```

is valid.

The reverse order is invalid because `P1` does not yet exist.

---

# 8. WP-4 API Amendment

The introduction of `PlannedLayerReference` is an explicit amendment to the WP-4 Concrete API.

The former:

```python
ConsumptionPlan.layer_identity: Identifier
```

is replaced by:

```python
ConsumptionPlan.layer_reference: LayerReference
```

The former `LayerEstablishmentPlan` receives:

```python
reference: PlannedLayerReference
```

This amendment is required because authoritative layer identity does not exist until establishment.

No other WP-4 preparation semantics are changed.

---

# 9. Valuation Establishment Result

Establishment outcome is part of the public API because the architecture explicitly distinguishes successful, failed, and indeterminate persistence state.

```python
class ValuationEstablishmentOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"
```

Result:

```python
@dataclass(frozen=True, slots=True)
class ValuationEstablishmentResult:
    outcome: ValuationEstablishmentOutcome
    error: Exception | None = None
```

The result follows the established platform distinction:

```text
SUCCESS
    establishment completed according to persistence guarantees

FAILURE
    establishment did not complete and the applicable persistence
    boundary guarantees that no relevant partial establishment remains

INDETERMINATE
    the system cannot conclusively determine whether the complete
    establishment was committed
```

`INDETERMINATE` must never be converted to `SUCCESS`.

---

# 10. ValuationCoordinator

Final public API:

```python
class ValuationCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...
```

The coordinator owns the logical establishment operation.

It does not own:

* plan preparation;
* FIFO calculation;
* transaction infrastructure;
* register mutation;
* distributed transaction coordination.

---

# 11. Plan Validation

Validation is performed before authoritative persistence.

```python
class ValuationPlanValidator(Protocol):
    def validate(
        self,
        plan: ValuationPlan,
    ) -> None:
        ...
```

Validation includes at least:

### Structural validation

* supported operation types;
* non-empty/valid operation data;
* valid valuation keys;
* valid identities;
* valid timestamps.

### Quantity and cost validation

* layer quantity > 0;
* consumption quantity > 0;
* consumption cost >= 0.

### Reference validation

* every persisted reference is resolvable;
* every planned reference is unique;
* every planned reference is established before consumption;
* references do not cross valuation keys;
* unsupported reference combinations are rejected.

### Semantic validation

* a consumption cannot exceed available quantity;
* consumption cost is consistent with the prepared plan;
* operation ordering is valid;
* all operations can be established without violating valuation invariants.

The coordinator must not persist any authoritative state before complete-plan validation succeeds.

---

# 12. Intra-Plan Reference Resolution

The coordinator maintains an in-memory mapping:

```python
dict[PlannedLayerReference, Identifier]
```

Example:

```text
Plan:

P1 = PlannedLayerReference("planned-1")

1. LayerEstablishmentPlan(reference=P1)
2. ConsumptionPlan(layer_reference=P1)
```

During establishment:

```text
P1
 │
 ▼
authoritative layer identity L1
```

The runtime mapping becomes:

```text
P1 → L1
```

The resulting consumption fact contains:

```text
layer_identity = L1
```

The mapping is not persisted as an independent domain object.

A planning reference never becomes an authoritative persistence identity.

---

# 13. Identity Generation

No dedicated public `ValuationIdentityGenerator` is introduced.

Authoritative identities are generated during establishment using the existing platform identity mechanism:

```python
Identifier.new()
```

This keeps identity generation an implementation detail of fact construction and avoids adding an unnecessary dependency to the public coordinator API.

The generated identity is authoritative only after the corresponding fact is successfully persisted.

---

# 14. Authoritative Fact Construction

For a `LayerEstablishmentPlan`, the coordinator constructs:

```python
ValuationLayer(
    identity=Identifier.new(),
    valuation_key=plan.valuation_key,
    quantity=plan.quantity,
    total_cost=Decimal(0),
    source_document_identity=plan.source_document_identity,
    source_movement_identity=plan.source_movement_identity,
    created_at=plan.created_at,
)
```

For a `ConsumptionPlan`, the coordinator constructs:

```python
ValuationConsumption(
    identity=Identifier.new(),
    valuation_key=plan.valuation_key,
    layer_identity=resolved_layer_identity,
    quantity=plan.quantity,
    cost=plan.cost,
    source_identity=plan.source_identity,
    created_at=plan.created_at,
)
```

The coordinator does not mutate existing valuation facts.

---

# 15. CostMovement Construction

`CostMovement` represents the balance effect of an authoritative valuation fact.

## 15.1 Layer establishment

A layer establishment produces:

```text
quantity = +Q
cost     = +C
```

For WP-5 layer establishment:

```text
quantity = +Q
cost     = 0
```

because a newly established layer has zero initial cost.

## 15.2 Consumption

A consumption fact:

```text
ValuationConsumption
    quantity = +Q
    cost     = +C
```

produces:

```text
CostMovement
    quantity = -Q
    cost     = -C
```

Therefore:

```text
Valuation fact
    = positive semantic fact

CostMovement
    = signed balance effect
```

This distinction is mandatory.

---

# 16. Cost Totals Engine

Cost aggregation is not implemented inside `ValuationCoordinator`.

It follows the established Totals architecture.

```python
class CostTotalsReader(Protocol):
    def get(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance:
        ...
```

```python
class CostTotalsEngine(CostTotalsReader, Protocol):
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

The engine owns:

* aggregation;
* current cost balance calculation;
* balance maintenance;
* rebuild from authoritative `CostMovement` state.

The coordinator only delegates to this component.

---

# 17. Persistence Contracts

## 17.1 ValuationFactPersistence

Authoritative valuation facts are persisted through:

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
    ) -> Sequence[ValuationFact]:
        ...

    def find_by_source_movement(
        self,
        movement_identity: Identifier,
    ) -> Sequence[ValuationFact]:
        ...

    def find_by_valuation_key(
        self,
        valuation_key: ValuationKey,
    ) -> Sequence[ValuationFact]:
        ...

    def enumerate(self) -> Sequence[ValuationFact]:
        ...
```

These facts are authoritative.

---

## 17.2 ValuationResultPersistence

Derived valuation results are persisted through:

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
    ) -> Sequence[CostMovement]:
        ...

    def find_balance(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance | None:
        ...

    def enumerate_balances(self) -> Sequence[CostBalance]:
        ...
```

`CostBalance` is derived state and is never the source of truth.

---

# 18. DefaultValuationCoordinator

Concrete implementation:

```python
class DefaultValuationCoordinator:
    def __init__(
        self,
        *,
        fact_persistence: ValuationFactPersistence,
        result_persistence: ValuationResultPersistence,
        totals_engine: CostTotalsEngine,
        validator: ValuationPlanValidator,
    ) -> None:
        ...
```

No identity generator is injected.

The coordinator depends only on the abstractions required for establishment.

---

# 19. Establishment Algorithm

The logical algorithm is:

```text
ValuationPlan
    │
    ▼
PlanValidator.validate(plan)
    │
    ├── failure → FAILURE
    │
    ▼
resolve intra-plan references
    │
    ▼
construct all authoritative facts
    │
    ▼
construct all CostMovements
    │
    ▼
persist authoritative facts
    │
    ▼
persist CostMovements
    │
    ▼
CostTotalsEngine.apply(...)
    │
    ▼
persist resulting CostBalance
    │
    ▼
SUCCESS
```

“persist authoritative facts → persist CostMovements → CostTotalsEngine → persist CostBalance” describes the semantic sequence, not necessarily four separately committed transactions. The transaction section above makes that distinction explicit.

The exact physical persistence call ordering may be adapted to the concrete persistence transaction mechanism, but the semantic dependency is fixed:

```text
validation
    ↓
authoritative facts
    ↓
derived CostMovements
    ↓
materialized CostBalance
```

---

# 20. Complete-Plan Validation Rule

The following sequence is prohibited:

```text
persist operation #1
persist operation #2
validate operation #3
fail
```

Instead:

```text
validate complete plan
    ↓
construct complete establishment state
    ↓
persist
```

This rule prevents a known-invalid later operation from producing avoidable partial authoritative state.

It does not imply distributed atomicity.

---

# 21. Persistence Transaction Contract

`ValuationCoordinator.establish(plan)` defines a **logical establishment boundary**. It does not itself define or own a database transaction.

The persistence transaction contract is:

```text
ValuationCoordinator
    │
    │ logical establishment attempt
    ▼
Persistence/Application Infrastructure
    │
    │ physical transaction boundary
    ├── ValuationFactPersistence
    ├── ValuationResultPersistence
    └── CostTotals / balance materialization
```

## 21.1 Transaction ownership

The physical transaction is owned by the concrete persistence/application infrastructure.

`DefaultValuationCoordinator` must therefore **not**:

* begin a database transaction;
* commit a database transaction;
* rollback a database transaction;
* depend directly on a database session/connection;
* implement distributed transaction coordination.

The coordinator orchestrates the establishment operation through persistence abstractions.

A concrete application composition root may provide transaction-aware implementations behind those abstractions.

---

## 21.2 Atomicity contract

When authoritative valuation facts, `CostMovement`s and `CostBalance` are backed by the **same transaction resource**, the concrete persistence implementation should establish them atomically.

The intended atomic unit is:

```text
BEGIN
    validate / prepare establishment state

    persist ValuationLayer / ValuationConsumption
    persist CostMovement
    materialize CostBalance
COMMIT
```

Therefore the externally visible durable state is either:

```text
complete establishment
```

or:

```text
no establishment
```

provided the underlying persistence transaction guarantees atomic commit/rollback.

This is a **local transaction guarantee**, not a distributed transaction guarantee.

---

## 21.3 Semantic dependency

Regardless of the physical transaction implementation, the domain dependency remains:

```text
validate complete plan
        ↓
authoritative valuation facts
        ↓
derived CostMovements
        ↓
materialized CostBalance
```

A derived result must not become durable as if its authoritative source facts had never existed.

`CostBalance` remains derived state even when it participates in the same physical transaction.

---

## 21.4 Shared transaction resource

If the implementation uses one transaction resource, the persistence/application layer may expose a transaction-scoped unit of work internally.

For example, conceptually:

```text
transaction
    ├── ValuationFactPersistence.append(...)
    ├── ValuationResultPersistence.append_movements(...)
    ├── CostTotalsEngine.apply(...)
    └── ValuationResultPersistence.replace_balance(...)
```

The exact unit-of-work API is **not part of the WP-5 public domain API**.

It may be introduced by the infrastructure layer without changing:

```python
ValuationCoordinator.establish(
    plan,
) -> ValuationEstablishmentResult
```

---

## 21.5 Separate persistence resources

If authoritative facts and derived results use different persistence resources, WP-5 does not provide atomicity across them.

For example:

```text
Resource A
    ValuationFactPersistence
        ↓
    committed

Resource B
    ValuationResultPersistence
        ↓
    commit unknown / failed
```

The resulting state may be:

```text
authoritative facts exist
derived CostMovements or CostBalance do not fully exist
```

This is a valid **indeterminate persistence state** under the WP-5 architecture.

The coordinator must return:

```python
ValuationEstablishmentOutcome.INDETERMINATE
```

when it cannot conclusively determine that the complete establishment was committed.

---

## 21.6 Failure classification

The physical transaction outcome maps to the public establishment result.

### Known rollback

```text
transaction begins
    ↓
persistence fails
    ↓
rollback confirmed
    ↓
FAILURE
```

The caller can rely on the applicable transaction guarantee that the attempted establishment did not remain durably established.

### Successful commit

```text
transaction begins
    ↓
all required state persisted
    ↓
commit confirmed
    ↓
SUCCESS
```

### Unknown commit

```text
persistence operation fails / connection lost
    ↓
commit state cannot be determined
    ↓
INDETERMINATE
```

The implementation must never convert an unknown commit state into `FAILURE` merely because an exception was raised.

An exception describes the observation available to the caller; it does not necessarily prove that the transaction rolled back.

---

## 21.7 Partial persistence

Partial durable state is possible only where the physical infrastructure does not provide a transaction spanning the affected persistence operations.

Example:

```text
ValuationFactPersistence
    committed successfully

ValuationResultPersistence
    commit status unknown
```

The resulting state must be treated as:

```text
INDETERMINATE
```

not:

```text
SUCCESS
```

and not automatically:

```text
FAILURE
```

Recovery/reconciliation must operate from the persisted authoritative facts and/or persisted `CostMovement`s rather than assuming that the materialized balance is authoritative.

---

## 21.8 Register boundary

The transaction contract does **not** extend to register persistence.

Even if register and valuation persistence happen to use the same physical database, WP-5 does not define them as one atomic domain transaction.

Architecturally:

```text
Posting / Register
    │
    │ independent establishment boundary
    ▼
Register persistence


Valuation
    │
    │ independent establishment boundary
    ▼
Valuation persistence
```

Sharing a database connection or transaction-capable infrastructure does not by itself change this domain contract.

A future posting-level transaction design may coordinate these domains, but that is outside WP-5.

---

## 21.9 Reconciliation requirement

Because WP-5 does not provide distributed atomicity, persistence implementations must preserve enough authoritative state to support reconciliation.

The recovery model is:

```text
authoritative valuation facts
        ↓
CostMovements
        ↓
CostTotalsEngine.rebuild(...)
        ↓
CostBalance
```

Therefore a stale or missing `CostBalance` does not invalidate the authoritative valuation facts.

A reconciliation process may rebuild derived results without rerunning valuation preparation.

---

## 21.10 Public API consequence

No transaction object is added to the public valuation API.

The public contract remains:

```python
class ValuationCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...
```

The following remain infrastructure concerns:

```text
transaction begin
transaction commit
transaction rollback
connection/session lifetime
unit-of-work implementation
transaction propagation
database isolation level
retry policy
distributed transaction coordination
```

These details must not leak into the valuation domain API.

---

## 21.11 Final transaction invariant

The WP-5 transaction contract can therefore be stated precisely as:

> `ValuationCoordinator.establish(plan)` is one logical establishment attempt. The concrete persistence infrastructure determines the physical transaction boundary. When all required valuation state shares one atomic transaction resource, authoritative valuation facts, derived `CostMovement`s, and the materialized `CostBalance` should be committed atomically. When they do not share such a boundary, partial durable state is possible and an uncertain completion must be reported as `INDETERMINATE`. WP-5 provides no distributed transaction across valuation and register domains.

This is the complete transaction guarantee exposed by WP-5.

---

# 22. Failure Semantics

## 22.1 Validation failure

```text
validation fails
    ↓
no authoritative persistence
    ↓
FAILURE
```

## 22.2 Persistence failure with known rollback

```text
persistence fails
    ↓
transaction guarantees rollback
    ↓
FAILURE
```

## 22.3 Unknown commit state

```text
persistence operation fails
    ↓
commit state cannot be determined
    ↓
INDETERMINATE
```

## 22.4 Independent persistence boundary failure

If authoritative facts are durably committed but a later independent result persistence operation fails without a conclusive rollback guarantee:

```text
partial durable state
    ↓
INDETERMINATE
```

The coordinator must not reinterpret such a state as `SUCCESS`.

---

# 23. Cost Balance Materialization

The coordinator does not perform cost arithmetic.

Instead:

```text
CostMovement
    ↓
CostTotalsEngine
    ↓
CostBalance
```

The resulting `CostBalance` is then materialized through:

```python
result_persistence.replace_balance(balance)
```

The balance is derived state.

Normal establishment does not rebuild the entire valuation history.

---

# 24. Rebuild and Recovery

Rebuild and recovery are separate responsibilities.

Normal establishment:

```text
new facts
    ↓
new CostMovements
    ↓
CostTotalsEngine
```

Recovery/rebuild:

```text
persisted CostMovements
    ↓
CostTotalsEngine.rebuild(...)
    ↓
CostBalance
```

This separation allows recovery to operate from persisted derived movements without rerunning FIFO preparation.

---

# 25. Idempotency

WP-5 does not introduce a separate idempotency key.

Existing source identities remain the basis for duplicate detection and uniqueness where supported by concrete persistence.

Relevant identities include:

```text
source_document_identity
source_movement_identity
source_identity
```

However, WP-5 does not claim exactly-once semantics unless the concrete persistence implementation provides the necessary uniqueness guarantees.

Append-only authoritative facts remain authoritative.

---

# 26. Register Independence

WP-5 does not mutate registers.

There is no dependency from:

```text
ValuationCoordinator
```

to:

```text
RegisterMutationOrchestrator
```

and no direct dependency from valuation establishment to register totals.

The two domains remain independently established.

---

# 27. Posting Integration

WP-5 does not modify `PostingEngine`.

The approved future posting integration is:

```text
PostingResultPlan
    ├── RegisterPlan
    └── ValuationPlan
```

with:

```python
class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> PostingResultPlan:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> None:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None:
        ...
```

This is outside the WP-5 implementation boundary.

`PostingEngine` remains valuation-agnostic.

---

# 28. Package Placement

The expected valuation package structure is:

```text
src/accore/platform/valuation/
    __init__.py
    coordinator.py
    validation.py
    input.py
    plan.py
    engine.py
    consumption.py
    facts.py
    results.py
    persistence.py
```

A separate:

```text
totals.py
```

may be introduced only if the existing Cost Totals implementation is not already located in an appropriate module.

The package should not duplicate existing platform totals infrastructure.

---

# 29. Public API Exports

The following concepts are public API candidates:

```text
ValuationCoordinator
ValuationEstablishmentOutcome
ValuationEstablishmentResult
ValuationPlanValidator
PlannedLayerReference
PersistedLayerReference
LayerReference
LayerEstablishmentPlan
ConsumptionPlan
ValuationPlan
CostTotalsReader
CostTotalsEngine
```

The following remain implementation details:

```text
runtime planned-reference mapping
Identifier.new() invocation
fact-construction helpers
failure translation helpers
persistence sequencing helpers
```

---

# 30. Testing Contract

The primary unit under test is:

```python
coordinator.establish(plan)
```

Test doubles must exist for:

```text
ValuationFactPersistence
ValuationResultPersistence
CostTotalsEngine
ValuationPlanValidator
```

No identity-generator double is required.

---

# 31. Required Test Scenarios

## 31.1 Layer establishment

```text
LayerEstablishmentPlan
    quantity = 10
```

Expected:

```text
ValuationLayer
    quantity = 10
    total_cost = 0

CostMovement
    quantity = +10
    cost = 0

CostBalance
    quantity = +10
    cost = 0
```

---

## 31.2 Consumption

Given an existing layer:

```text
quantity = 10
cost = 100
```

consumption:

```text
quantity = 6
cost = 60
```

Expected:

```text
ValuationConsumption
    quantity = +6
    cost = +60
```

and:

```text
CostMovement
    quantity = -6
    cost = -60
```

---

## 31.3 Zero-cost establishment

A zero-cost layer must establish successfully.

```text
quantity = 10
cost = 0
```

is valid.

---

## 31.4 Intra-plan establishment and consumption

Plan:

```text
1. LayerEstablishmentPlan(P1, quantity=10)
2. ConsumptionPlan(P1, quantity=6, ...)
```

Expected:

```text
P1 → authoritative layer identity

ValuationConsumption.layer_identity
    = authoritative layer identity
```

---

## 31.5 Invalid later operation

Plan:

```text
1. valid operation
2. valid operation
3. invalid operation
```

Expected:

```text
validator failure
    ↓
no persistence
    ↓
FAILURE
```

---

## 31.6 Invalid reference ordering

Plan:

```text
1. ConsumptionPlan(P1)
2. LayerEstablishmentPlan(P1)
```

Expected:

```text
validation failure
```

No persistence occurs.

---

## 31.7 Persistence rollback

Persistence fails and transaction guarantees rollback.

Expected:

```text
FAILURE
```

---

## 31.8 Unknown commit

Persistence outcome cannot determine whether the write committed.

Expected:

```text
INDETERMINATE
```

---

## 31.9 Cost totals delegation

The coordinator must delegate aggregation to:

```text
CostTotalsEngine
```

and must not calculate balances itself.

---

## 31.10 Register independence

No register mutation occurs during direct valuation establishment.

---

# 32. Explicit Non-Goals

WP-5 does not implement:

* FIFO calculation;
* valuation plan preparation;
* register mutation;
* PostingEngine lifecycle changes;
* distributed transactions;
* global transaction coordinator;
* valuation repair;
* historical rebuild orchestration;
* exactly-once processing;
* query API;
* valuation adjustment lifecycle;
* valuation reversal lifecycle.

---

# 33. Final API Summary

The approved public establishment boundary is:

```python
class ValuationCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...
```

Validation:

```python
class ValuationPlanValidator(Protocol):
    def validate(
        self,
        plan: ValuationPlan,
    ) -> None:
        ...
```

Layer references:

```python
@dataclass(frozen=True, slots=True)
class PlannedLayerReference:
    value: Identifier


@dataclass(frozen=True, slots=True)
class PersistedLayerReference:
    identity: Identifier


type LayerReference = (
    PlannedLayerReference
    | PersistedLayerReference
)
```

Layer plan:

```python
@dataclass(frozen=True, slots=True)
class LayerEstablishmentPlan:
    reference: PlannedLayerReference
    valuation_key: ValuationKey
    quantity: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime
```

Consumption plan:

```python
@dataclass(frozen=True, slots=True)
class ConsumptionPlan:
    valuation_key: ValuationKey
    layer_reference: LayerReference
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

Establishment result:

```python
class ValuationEstablishmentOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"
```

```python
@dataclass(frozen=True, slots=True)
class ValuationEstablishmentResult:
    outcome: ValuationEstablishmentOutcome
    error: Exception | None = None
```

Cost totals:

```python
class CostTotalsReader(Protocol):
    def get(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance:
        ...
```

```python
class CostTotalsEngine(CostTotalsReader, Protocol):
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

---

# 34. API Review Decisions

The following decisions are final for WP-5:

| Decision                                    | Status             |
| ------------------------------------------- | ------------------ |
| Explicit establishment result               | **Approved**       |
| `SUCCESS / FAILURE / INDETERMINATE`         | **Approved**       |
| Dedicated `ValuationIdentityGenerator`      | **Rejected**       |
| Existing `Identifier.new()` mechanism       | **Approved**       |
| `LayerEstablishmentPlan.total_cost`         | **Rejected**       |
| Zero-cost initial layer                     | **Approved**       |
| `PlannedLayerReference`                     | **Approved**       |
| `PersistedLayerReference`                   | **Approved**       |
| `LayerReference` union                      | **Approved**       |
| WP-4 amendment for references               | **Approved**       |
| Complete-plan validation before persistence | **Approved**       |
| `CostMovement` signed balance semantics     | **Approved**       |
| Separate `CostTotalsEngine`                 | **Approved**       |
| Coordinator performs no balance arithmetic  | **Approved**       |
| Coordinator owns physical transaction       | **Rejected**       |
| Distributed transaction                     | **Out of scope**   |
| Register mutation inside valuation          | **Rejected**       |
| PostingEngine changes in WP-5               | **Out of scope**   |
| Exactly-once guarantee                      | **Not introduced** |
| `CostBalance` as authoritative state        | **Rejected**       |

---

# 35. Implementation Gate

WP-5 implementation has been completed against this final Concrete API Design and the approved Architecture Review amendments.

Final validation:

- valuation unit tests: 52 passed
- full project tests: 948 passed
- Ruff: PASS
- Black: PASS
- mypy: PASS

Architecture review: PASS
Implementation review: PASS
Documentation reconciliation: completed

The implementation conforms to the approved API and architectural boundaries. No unresolved WP-5 architectural deviations remain.

The final implementation sequence was:

```text
Final Architecture Definition
        ↓
Final Concrete API Design
        ↓
WP-4 API amendment
        ↓
WP-5 implementation
        ↓
tests
        ↓
quality gate
        ↓
documentation reconciliation
        ↓
final review
        ↓
commit
```

The following implemented constraints are final:

* planned layer references are distinct from persisted layer identities;
* complete-plan validation occurs before authoritative writes;
* valuation facts are authoritative;
* `CostMovement` and `CostBalance` are derived/materialized state;
* `CostTotalsEngine` owns balance arithmetic;
* physical transaction ownership remains with persistence/application infrastructure;
* known rollback maps to `FAILURE`; unknown commit state maps to `INDETERMINATE`;
* no distributed transaction is introduced;
* no exactly-once guarantee is introduced by WP-5;
* `PostingEngine` remains unchanged by WP-5.
