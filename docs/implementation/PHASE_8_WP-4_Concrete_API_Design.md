# Phase 8 — WP-4 Concrete API Design

**Status:** Final — Ready for Architecture Approval
**Phase:** 8 — Valuation
**Work Package:** WP-4 — Valuation Engine / Valuation Plan
**Baseline:** `AcCoreD_cur3.zip`
**Depends on:** Phase 8 Valuation Architecture Definition, WP-1, WP-2, WP-3, approved `PHASE_8_VALUATION_ARCHITECTURE_REVIEW_API_AMENDMENT.md`
**Implementation status:** Not authorized by this document
**Scope:** Concrete public and internal API for deterministic valuation preparation

---

## 1. Purpose

WP-4 introduces the deterministic valuation preparation boundary.

The central responsibility is:

```text
MovementSet
    ↓
ValuationEngine.prepare()
    ↓
ValuationPlan
```

`ValuationEngine.prepare()` determines the valuation operations required by a movement set without performing authoritative persistence or Register mutation.

WP-4 therefore defines:

* `ValuationInput`;
* `LayerEstablishmentPlan`;
* `ConsumptionPlan`;
* `ValuationPlanOperation`;
* `ValuationPlan`;
* `ValuationLayerReader`;
* `ValuationEngine`;
* movement-to-valuation translation rules;
* deterministic validation rules;
* preparation error semantics;
* plan validity and immutability rules.

WP-4 does **not** implement:

* valuation persistence writes;
* Register mutation;
* Posting lifecycle;
* `PostingEngine`;
* `PostingResultCoordinator`;
* unpost/repost compensation;
* valuation queries;
* rebuild/recovery;
* alternative valuation methods.

---

# 2. Existing API Baseline

WP-4 must integrate with the actual Phase 8 baseline rather than introducing parallel domain concepts.

The following existing types are authoritative.

## 2.1 `MovementSet`

```python
@dataclass(frozen=True, slots=True)
class MovementSet:
    movements: tuple[Movement, ...]
```

`MovementSet.movements` is already a canonical immutable tuple.

WP-4 MUST preserve its order.

It MUST NOT sort or otherwise reorder the movement collection globally.

---

## 2.2 `Movement`

The existing Register movement contains:

```python
@dataclass(frozen=True, slots=True)
class Movement:
    identity: Identifier
    source_document_identity: Identifier
    register_identity: Identifier
    movement_type: MovementType
    dimensions: MovementDimensions
    resources: MovementResources
    attributes: MovementAttributes
    accounting_time: datetime | None
```

WP-4 consumes movement semantics but does not modify `Movement`.

The valuation subsystem remains independent from the Register domain.

---

## 2.3 `ValuationLayer`

The authoritative valuation layer is:

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

Consequently, any preparation plan that later establishes a `ValuationLayer` MUST preserve the source document identity, source movement identity, valuation key, quantity, and occurrence time required to establish that fact.

---

## 2.4 `ConsumptionRequest`

The actual WP-3 API is:

```python
@dataclass(frozen=True, slots=True)
class ConsumptionRequest:
    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    source_identity: Identifier
    occurred_at: datetime
```

WP-4 MUST construct this existing request type rather than introduce a second consumption-request model.

---

## 2.5 `ValuationMethod`

The WP-3 strategy boundary is frozen:

```python
class ValuationMethod(Protocol):
    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult: ...
```

WP-4 MUST call `consume()`.

The method name MUST NOT be changed to `value()` or another alternative as part of WP-4.

---

## 2.6 `ConsumptionResult`

WP-3 returns:

```python
@dataclass(frozen=True, slots=True)
class ConsumptionResult:
    consumptions: tuple[ValuationConsumption, ...]
    total_cost: Decimal
    remaining_layers: tuple[ValuationLayer, ...]
```

WP-4 consumes the resulting `ValuationConsumption` semantics and converts them into non-authoritative `ConsumptionPlan` operations.

WP-4 MUST NOT persist the returned facts.

---

# 3. Design Principles

WP-4 follows these principles.

### 3.1 Preparation is non-authoritative

`ValuationEngine.prepare()` MUST NOT:

* append valuation facts;
* replace valuation balances;
* mutate Register state;
* mutate valuation layers;
* publish posting events;
* call `PostingEngine`;
* call `PostingResultCoordinator`.

---

### 3.2 Preparation is deterministic

For identical:

* `MovementSet`;
* available valuation layers;
* valuation method;
* valuation configuration;

the resulting `ValuationPlan` MUST be semantically identical.

Determinism MUST NOT depend on persistence enumeration order.

---

### 3.3 Plan is not fact

A plan is an instruction for later authoritative establishment.

It is not itself a `ValuationFact`.

Therefore:

* plans have no generated valuation-fact identity;
* plans are not persisted as valuation facts;
* plans do not replace valuation facts;
* plans do not become historical records.

Conceptually:

```text
LayerEstablishmentPlan
        ↓
ValuationLayer

ConsumptionPlan
        ↓
ValuationConsumption
```

The conversion into authoritative facts belongs to the later establishment boundary.

---

### 3.4 Register remains independent

WP-4 MUST NOT introduce cost into:

* `Movement`;
* Register totals;
* Register mutation;
* Register balance queries.

Quantity accounting and valuation remain separate semantic subsystems.

---

# 4. Public API

WP-4 introduces the following public API.

```python
@dataclass(frozen=True, slots=True)
class ValuationInput:
    request: ConsumptionRequest
    layers: tuple[ValuationLayer, ...]
```

```python
@dataclass(frozen=True, slots=True)
class LayerEstablishmentPlan:
    valuation_key: ValuationKey
    quantity: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime
```

```python
@dataclass(frozen=True, slots=True)
class ConsumptionPlan:
    valuation_key: ValuationKey
    layer_identity: Identifier
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

```python
ValuationPlanOperation = LayerEstablishmentPlan | ConsumptionPlan
```

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    operations: tuple[ValuationPlanOperation, ...]
```

```python
class ValuationLayerReader(Protocol):
    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        ...
```

```python
class ValuationEngine:
    def prepare(
        self,
        movement_set: MovementSet,
    ) -> ValuationPlan:
        ...
```

The remainder of this document defines the exact semantics of these contracts.

---

# 5. `ValuationInput`

## 5.1 Definition

```python
@dataclass(frozen=True, slots=True)
class ValuationInput:
    request: ConsumptionRequest
    layers: tuple[ValuationLayer, ...]
```

`ValuationInput` is a consumption-path preparation object.

It groups:

* the immutable consumption request;
* the immutable available layer snapshot supplied to the valuation method.

---

## 5.2 Responsibilities

`ValuationInput` MUST:

* preserve the exact `ConsumptionRequest`;
* preserve the available layers as an immutable tuple;
* provide a stable input boundary for WP-3;
* avoid introducing duplicate request fields.

It MUST NOT:

* contain movement objects;
* contain persistence services;
* contain valuation facts;
* perform FIFO;
* perform persistence reads.

---

## 5.3 Relationship with `ConsumptionRequest`

`ConsumptionRequest` remains the semantic request.

`ValuationInput` is only the engine-level grouping of:

```text
ConsumptionRequest
        +
available ValuationLayer snapshot
```

No field from `ConsumptionRequest` is duplicated in `ValuationInput`.

---

# 6. `LayerEstablishmentPlan`

## 6.1 Definition

```python
@dataclass(frozen=True, slots=True)
class LayerEstablishmentPlan:
    valuation_key: ValuationKey
    quantity: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime
```

---

## 6.2 Purpose

`LayerEstablishmentPlan` represents the future establishment of one valuation layer.

It contains sufficient immutable information to create the corresponding `ValuationLayer` later without reinterpreting the original `Movement`.

The authoritative layer identity is intentionally absent.

The identity belongs to the later fact-establishment operation.

---

## 6.3 Required semantics

The plan MUST preserve:

* valuation key;
* positive quantity;
* source document identity;
* source movement identity;
* layer creation/occurrence timestamp.

`quantity` MUST use `Decimal`.

Floating-point values MUST NOT be introduced.

---

## 6.4 Fact establishment

Later establishment conceptually performs:

```python
ValuationLayer(
    identity=Identifier.new(),
    valuation_key=plan.valuation_key,
    quantity=plan.quantity,
    total_cost=<established valuation cost>,
    source_document_identity=plan.source_document_identity,
    source_movement_identity=plan.source_movement_identity,
    created_at=plan.created_at,
)
```

The exact authoritative cost establishment is outside WP-4.

WP-4 therefore does not invent a `total_cost` field for `LayerEstablishmentPlan`.

---

# 7. `ConsumptionPlan`

## 7.1 Definition

```python
@dataclass(frozen=True, slots=True)
class ConsumptionPlan:
    valuation_key: ValuationKey
    layer_identity: Identifier
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

---

## 7.2 Purpose

`ConsumptionPlan` represents one deterministic consumption operation against one existing valuation layer.

It is derived from the WP-3 `ConsumptionResult`.

---

## 7.3 Mapping from `ValuationConsumption`

The semantic mapping is direct:

```text
ValuationConsumption
        ↓
ConsumptionPlan
```

The following fields are preserved:

```text
valuation_key
layer_identity
quantity
cost
source_identity
created_at
```

The generated `ValuationConsumption.identity` is deliberately not copied.

That identity belongs to authoritative fact establishment.

---

# 8. `ValuationPlanOperation`

The plan supports both inbound layer establishment and outbound consumption.

```python
ValuationPlanOperation = LayerEstablishmentPlan | ConsumptionPlan
```

This explicit union is preferred over a generic item containing optional fields.

The two operation types have different semantics:

| Operation                | Meaning                                           |
| ------------------------ | ------------------------------------------------- |
| `LayerEstablishmentPlan` | Establish available valuation quantity            |
| `ConsumptionPlan`        | Consume quantity from an existing valuation layer |

A plan MUST NOT represent an operation using ambiguous optional fields such as:

```python
layer_identity: Identifier | None
cost: Decimal | None
```

Explicit operation types keep the domain contract precise.

---

# 9. `ValuationPlan`

## 9.1 Definition

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    operations: tuple[ValuationPlanOperation, ...]
```

---

## 9.2 Properties

`ValuationPlan` is:

* immutable;
* ordered;
* non-authoritative;
* deterministic;
* operation-specific.

The order of operations corresponds to the order of the source `MovementSet`.

---

## 9.3 No authoritative facts

`ValuationPlan` MUST NOT contain:

* `ValuationLayer` facts;
* `ValuationConsumption` facts;
* generated fact identities;
* persistence records;
* mutable references.

---

## 9.4 Empty plan

An empty `MovementSet` produces:

```python
ValuationPlan(operations=())
```

An empty plan is valid.

---

# 10. `ValuationLayerReader`

## 10.1 Definition

```python
class ValuationLayerReader(Protocol):
    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        ...
```

---

## 10.2 Purpose

This is a semantic read boundary specifically for available valuation layers.

It exists because:

```python
ValuationFactPersistence.find_by_valuation_key(...)
```

returns all `ValuationFact` variants.

That persistence contract is therefore not an appropriate direct input to FIFO.

WP-4 must not reconstruct available-layer state by filtering arbitrary valuation facts.

---

## 10.3 Responsibility

`ValuationLayerReader` provides:

```text
valuation key
    ↓
available valuation layers
```

The reader MUST return only currently available `ValuationLayer` semantics.

It does not:

* perform FIFO;
* calculate consumption;
* mutate valuation state;
* create valuation facts.

---

# 11. `ValuationEngine`

## 11.1 Definition

```python
class ValuationEngine:
    def prepare(
        self,
        movement_set: MovementSet,
    ) -> ValuationPlan:
        ...
```

---

## 11.2 Primary responsibility

`ValuationEngine.prepare()` translates the movement set into deterministic valuation operations.

The high-level flow is:

```text
MovementSet
    ↓
movement semantics
    ↓
valuation applicability
    ↓
INCOME → LayerEstablishmentPlan
EXPENSE → ValuationInput
              ↓
        ValuationMethod.consume()
              ↓
        ConsumptionPlan(s)
    ↓
ValuationPlan
```

---

# 12. Movement Processing

`MovementSet.movements` MUST be processed in its existing tuple order.

For each movement:

```text
Movement
    ↓
valuation applicability
    ↓
valuation operation
```

WP-4 MUST NOT globally sort movements.

The following are independent ordering rules:

### Movement ordering

```text
MovementSet.movements
```

Existing order is authoritative.

### FIFO layer ordering

```python
(layer.created_at, str(layer.identity))
```

FIFO ordering applies only inside a consumption operation.

---

# 13. INCOME Semantics

An `INCOME` movement establishes available valuation quantity.

The engine creates:

```python
LayerEstablishmentPlan(
    valuation_key=<derived from movement>,
    quantity=<movement quantity>,
    source_document_identity=movement.source_document_identity,
    source_movement_identity=movement.identity,
    created_at=<valuation occurrence time>,
)
```

The plan contains no generated layer identity and no authoritative cost.

---

## 13.1 Valuation key

For the standard inventory valuation slice, the valuation key aligns semantically with the quantity dimensions:

```text
product
warehouse
```

The key remains a valuation-domain object.

The engine MUST construct `ValuationKey` explicitly rather than reusing Register dimension objects as valuation state.

---

## 13.2 Quantity

The valuation quantity is positive.

The Register's movement sign is not copied into the valuation quantity.

Therefore:

```text
INCOME
    Register semantic effect: +quantity
    Valuation layer quantity: positive quantity
```

No negative valuation layer is created.

---

## 13.3 Timestamp

`LayerEstablishmentPlan.created_at` represents the valuation occurrence time.

The exact source timestamp must be resolved according to the approved inventory valuation configuration and existing movement semantics.

If the required valuation timestamp is unavailable, preparation MUST fail deterministically rather than silently inventing one.

---

# 14. EXPENSE Semantics

An `EXPENSE` movement represents valuation consumption.

The engine:

1. derives the valuation key;
2. derives the positive consumption quantity;
3. obtains available layers using `ValuationLayerReader`;
4. constructs `ConsumptionRequest`;
5. invokes `ValuationMethod.consume()`;
6. converts the resulting consumptions into `ConsumptionPlan` operations.

Conceptually:

```text
Movement
    ↓
ValuationKey
    ↓
positive quantity
    ↓
ConsumptionRequest
    +
ValuationLayerReader
    ↓
ValuationInput
    ↓
ValuationMethod.consume()
    ↓
ConsumptionResult
    ↓
ConsumptionPlan(s)
```

---

# 15. Consumption Request Construction

For an expense movement:

```python
ConsumptionRequest(
    identity=Identifier.new(),
    valuation_key=valuation_key,
    quantity=positive_quantity,
    source_identity=movement.identity,
    occurred_at=valuation_occurrence_time,
)
```

The request source identity is the movement identity.

The request quantity MUST remain positive.

The Register sign:

```text
EXPENSE → -quantity
```

MUST NOT be transferred into `ConsumptionRequest.quantity`.

---

# 16. FIFO Integration

WP-4 delegates consumption calculation to the existing WP-3 method.

```python
result = valuation_method.consume(
    layers=input.layers,
    request=input.request,
)
```

WP-4 MUST NOT duplicate FIFO logic.

It MUST NOT:

* sort layers itself;
* manually calculate proportional cost;
* select layers independently;
* recreate `remaining_layers`;
* re-run consumption during establishment.

---

# 17. FIFO Determinism

The existing WP-3 ordering rule is authoritative:

```python
(layer.created_at, str(layer.identity))
```

The engine first selects layers for the requested valuation key through:

```python
ValuationLayerReader.find_available_layers(
    valuation_key,
)
```

The valuation method then applies FIFO ordering.

The persistence enumeration order is therefore irrelevant.

Equal timestamps remain deterministic because the layer identity string is the tie-breaker.

---

# 18. Conversion of `ConsumptionResult`

For each:

```python
ValuationConsumption
```

returned by WP-3, WP-4 creates:

```python
ConsumptionPlan(
    valuation_key=consumption.valuation_key,
    layer_identity=consumption.layer_identity,
    quantity=consumption.quantity,
    cost=consumption.cost,
    source_identity=consumption.source_identity,
    created_at=consumption.created_at,
)
```

The order returned by `ConsumptionResult.consumptions` MUST be preserved.

---

# 19. Insufficient Quantity

If FIFO raises:

```python
ValuationInsufficientQuantityError
```

the engine MUST fail preparation.

No `ValuationPlan` containing authoritative or partial results is returned.

No persistence mutation occurs.

For repost:

```text
prepare(new)
    ↓
insufficient quantity
    ↓
failure
    ↓
remove(old) is NOT executed
```

This is a mandatory Phase 8 invariant.

---

# 20. Other Deterministic Validation Failures

WP-4 must propagate or translate deterministic valuation-domain validation failures according to the approved integration boundary.

Examples include:

* invalid valuation key;
* invalid quantity;
* layer/key mismatch;
* unavailable required valuation input;
* invalid movement-to-valuation translation.

Preparation MUST fail before authoritative result establishment.

---

# 21. Persistence Errors During Preparation

A layer read is part of deterministic preparation, but its persistence operation may fail.

The distinction remains:

```text
deterministic domain failure
        ≠
persistence failure
        ≠
persistence indeterminacy
```

WP-4 MUST NOT collapse these categories.

Mapping into posting-level errors belongs to the later posting integration boundary.

In particular, `ValuationEngine` MUST NOT import or depend on `PostingEngine` error types merely to perform this mapping.

---

# 22. Plan Validity

A `ValuationPlan` is valid only for the movement generation from which it was prepared.

The plan MUST be bound semantically to:

* the relevant movement identities;
* the movement ordering;
* the source document identity;
* the valuation inputs used for consumption.

A later establishment boundary MUST reject a plan that does not correspond to its supplied movement set.

This prevents:

```text
prepare(A)
    ↓
plan A
    ↓
establish(B, plan A)
```

from being accepted accidentally.

The exact concrete plan-binding mechanism is part of the later coordinator integration API.

---

# 23. Plan Immutability

All WP-4 plan objects MUST be immutable.

Required form:

```python
@dataclass(frozen=True, slots=True)
```

Collections MUST use immutable tuples:

```python
tuple[...]
```

Mutable lists MUST NOT be exposed by the public API.

---

# 24. Identifier Policy

All identity fields MUST use:

```python
Identifier
```

and MUST NOT use:

```python
str
```

This applies to:

* source document identity;
* source movement identity;
* layer identity;
* consumption source identity.

String conversion is permitted only for deterministic ordering:

```python
str(layer.identity)
```

It does not change the underlying identity type.

---

# 25. Decimal Policy

All valuation quantities and monetary amounts MUST use:

```python
Decimal
```

This applies to:

* layer quantity;
* layer total cost;
* consumption quantity;
* consumption cost;
* plan quantity;
* plan cost.

Floating-point valuation arithmetic is prohibited.

---

# 26. Public Export Policy

The WP-4 public API should expose only concepts intended as stable valuation-domain boundaries.

The following are public:

```text
ValuationInput
LayerEstablishmentPlan
ConsumptionPlan
ValuationPlanOperation
ValuationPlan
ValuationLayerReader
ValuationEngine
```

Existing WP-3 public types remain public:

```text
ConsumptionRequest
ConsumptionResult
ValuationMethod
FIFOValuationMethod
SyntheticConsumptionService
```

Internal translation helpers should remain private unless a later architecture review identifies a stable external use case.

---

# 27. Dependency Direction

The dependency direction is:

```text
ValuationEngine
    │
    ├── ValuationLayerReader
    │
    ├── ValuationMethod
    │
    ├── ValuationKey
    │
    ├── ConsumptionRequest
    │
    └── Movement / MovementSet
```

The engine MUST NOT depend on:

```text
PostingEngine
RegisterMutationOrchestrator
PostingResultCoordinator
ValuationFactPersistence writes
Document events
```

The engine is therefore usable independently of the posting lifecycle.

---

# 28. Posting Integration Boundary

The approved Phase 8 posting amendment introduces:

```python
class PostingResultPlan(Protocol):
    ...
```

and:

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

`ValuationPlan` is contained inside the concrete posting-level plan.

`PostingEngine` knows only the opaque:

```text
PostingResultPlan
```

It does not know:

```text
ValuationPlan
FIFO
ValuationLayer
ValuationConsumption
valuation persistence
```

---

# 29. Repost Safety

The required lifecycle is:

```text
new MovementSet
      ↓
movement validation
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

The mandatory invariant is:

```text
prepare(new) fails
        ⇒
remove(old) is not executed
```

WP-4 contributes to this invariant by guaranteeing that `ValuationEngine.prepare()` is deterministic and non-authoritative.

---

# 30. No Hidden State

WP-4 MUST NOT store pending valuation plans internally.

Rejected design:

```text
engine.prepare(document)
    ↓
engine stores plan by document identity
    ↓
engine.establish(document)
```

This is prohibited because it introduces:

* mutable lifecycle state;
* concurrency ambiguity;
* stale-plan risk;
* implicit ownership;
* hidden coupling between calls.

The plan MUST be returned explicitly.

---

# 31. Establishment Boundary

WP-4 ends at:

```python
ValuationPlan
```

Later establishment consumes the plan.

Conceptually:

```text
ValuationPlan
    │
    ├── LayerEstablishmentPlan
    │       ↓
    │   ValuationLayer
    │
    └── ConsumptionPlan
            ↓
        ValuationConsumption
```

The establishment boundary is responsible for:

* generating authoritative fact identities;
* establishing authoritative timestamps where required;
* persisting facts;
* applying the plan exactly once according to the later coordination contract.

WP-4 does not perform these actions.

---

# 32. Deterministic Operation Ordering

For a movement set:

```text
M1, M2, M3
```

the plan operations correspond to:

```text
valuation(M1)
valuation(M2)
valuation(M3)
```

The engine MUST preserve this order.

If one movement produces multiple consumption operations:

```text
M2
 ↓
C1
C2
C3
```

the returned operation order MUST preserve the order returned by the valuation method.

Therefore:

```text
MovementSet order
    +
FIFO result order
        ↓
ValuationPlan order
```

---

# 33. Multiple Movements

WP-4 MUST support a `MovementSet` containing multiple movements.

Each movement is processed independently within the deterministic preparation pass.

The plan may therefore contain:

```text
LayerEstablishmentPlan
ConsumptionPlan
ConsumptionPlan
LayerEstablishmentPlan
...
```

No global aggregation of valuation operations is introduced by WP-4.

Aggregation, if required later, must be explicitly defined by a separate architecture decision.

---

# 34. Transactional Meaning of Preparation

Preparation is logically transactional in the sense that it either produces a complete deterministic plan or fails.

It is not a database transaction.

The engine MUST NOT:

* open a persistence transaction;
* partially persist facts;
* roll back persistence;
* mutate authoritative state.

Therefore:

```text
prepare()
    ├── success → complete ValuationPlan
    └── failure → no authoritative valuation mutation
```

---

# 35. Error Boundary

WP-4 domain errors remain valuation-domain errors.

Examples:

```text
ValuationValidationError
ValuationInsufficientQuantityError
ValuationNotFoundError
ValuationConflictError
```

The posting integration layer may later translate applicable errors into posting-level preparation failures.

WP-4 itself MUST NOT make `PostingPreparationError` part of the valuation-domain API.

---

# 36. Testing Contract

WP-4 implementation MUST include tests for at least:

### API construction

* immutable `ValuationInput`;
* immutable `LayerEstablishmentPlan`;
* immutable `ConsumptionPlan`;
* immutable `ValuationPlan`;
* tuple-based operation storage.

### INCOME

* creates one layer-establishment operation;
* preserves source document identity;
* preserves source movement identity;
* preserves positive quantity;
* preserves valuation key;
* preserves valuation occurrence time;
* does not generate authoritative layer identity.

### EXPENSE

* constructs `ConsumptionRequest`;
* uses positive quantity;
* reads available layers through `ValuationLayerReader`;
* delegates consumption to `ValuationMethod`;
* converts `ConsumptionResult` to `ConsumptionPlan`;
* preserves consumption ordering.

### FIFO integration

* FIFO is not duplicated in the engine;
* equal timestamps remain deterministic;
* layer persistence order does not affect results.

### Failure

* insufficient quantity fails preparation;
* invalid valuation input fails preparation;
* no authoritative mutation occurs on preparation failure.

### Movement ordering

* source movement order is preserved;
* multiple movements produce operations in movement order.

### Plan integrity

* plan cannot be reused for a different movement generation at establishment;
* no hidden engine state is required.

---

# 37. Acceptance Criteria

WP-4 implementation is accepted only if all of the following are true.

## API

* [ ] `ValuationInput` exists with exactly the consumption-input responsibility.
* [ ] `LayerEstablishmentPlan` contains sufficient source information to establish a `ValuationLayer`.
* [ ] `ConsumptionPlan` maps the existing `ValuationConsumption` semantics.
* [ ] `ValuationPlanOperation` is an explicit union.
* [ ] `ValuationPlan` is immutable.
* [ ] `ValuationLayerReader` is a separate semantic read boundary.
* [ ] `ValuationEngine.prepare()` is the sole WP-4 preparation entry point.

## Domain separation

* [ ] Register remains quantity-only.
* [ ] WP-4 does not mutate Register state.
* [ ] WP-4 does not persist valuation facts.
* [ ] WP-4 does not publish events.
* [ ] WP-4 does not depend on `PostingEngine`.
* [ ] WP-4 does not depend on `PostingResultCoordinator`.

## Determinism

* [ ] MovementSet order is preserved.
* [ ] FIFO ordering remains `(created_at, str(layer.identity))`.
* [ ] Persistence enumeration order does not determine FIFO results.
* [ ] Equal timestamps remain deterministic.
* [ ] No hidden mutable preparation state exists.

## WP-3 integration

* [ ] `ValuationMethod.consume()` remains unchanged.
* [ ] `ConsumptionRequest` remains unchanged.
* [ ] `ConsumptionResult` remains unchanged.
* [ ] WP-4 does not duplicate FIFO logic.
* [ ] WP-4 does not re-run valuation during establishment.

## Repost invariant

* [ ] A failed valuation preparation cannot cause old-result removal.
* [ ] Prepared valuation state is transferred explicitly through the later posting plan.
* [ ] `PostingEngine` remains unaware of valuation-specific types.

---

# 38. Implementation Scope

The following files/concepts are expected to be introduced or amended during implementation:

```text
src/accore/platform/valuation/
    input.py
    plan.py
    engine.py
    __init__.py
```

The exact file decomposition may follow the repository's established module conventions, provided the public API defined in this document remains unchanged.

Tests should be placed under:

```text
tests/unit/valuation/
```

Integration tests for posting coordination belong to the later posting-integration work package and MUST NOT be pulled into WP-4 prematurely.

---

# 39. Explicitly Out of Scope

The following are not part of WP-4:

1. `PostingResultCoordinator` implementation amendment.
2. `PostingEngine` lifecycle modification.
3. Register coordinator changes.
4. Valuation persistence implementation.
5. Valuation fact establishment.
6. Unpost compensation.
7. Repost compensation.
8. Valuation recovery.
9. Valuation balance queries.
10. Rebuild.
11. Alternative valuation methods.
12. Currency or FX.
13. Cost accounting inside Register.
14. Asynchronous valuation events.
15. Distributed transactions.

---

# 40. Implementation Order

After approval of this document:

```text
WP-4 API approval
      ↓
implement input.py
      ↓
implement plan.py
      ↓
implement layer-reader boundary
      ↓
implement ValuationEngine.prepare()
      ↓
unit tests
      ↓
ruff
      ↓
black
      ↓
mypy
      ↓
valuation quality gate
      ↓
implementation review
```

No posting integration implementation is part of this sequence.

---

# 41. Final API Summary

The final WP-4 public contract is:

```python
@dataclass(frozen=True, slots=True)
class ValuationInput:
    request: ConsumptionRequest
    layers: tuple[ValuationLayer, ...]
```

```python
@dataclass(frozen=True, slots=True)
class LayerEstablishmentPlan:
    valuation_key: ValuationKey
    quantity: Decimal
    source_document_identity: Identifier
    source_movement_identity: Identifier
    created_at: datetime
```

```python
@dataclass(frozen=True, slots=True)
class ConsumptionPlan:
    valuation_key: ValuationKey
    layer_identity: Identifier
    quantity: Decimal
    cost: Decimal
    source_identity: Identifier
    created_at: datetime
```

```python
ValuationPlanOperation = LayerEstablishmentPlan | ConsumptionPlan
```

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    operations: tuple[ValuationPlanOperation, ...]
```

```python
class ValuationLayerReader(Protocol):
    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        ...
```

```python
class ValuationEngine:
    def prepare(
        self,
        movement_set: MovementSet,
    ) -> ValuationPlan:
        ...
```

The frozen WP-3 contract remains:

```python
class ValuationMethod(Protocol):
    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult: ...
```

---

# 42. Final Architecture Boundary

The complete Phase 8 preparation boundary is:

```text
                    MovementSet
                         │
                         ▼
                 ValuationEngine
                         │
              ┌──────────┴──────────┐
              │                     │
           INCOME                 EXPENSE
              │                     │
              ▼                     ▼
   LayerEstablishmentPlan    ValuationLayerReader
                                    │
                                    ▼
                             ValuationInput
                                    │
                                    ▼
                           ValuationMethod
                                    │
                                    ▼
                           ConsumptionResult
                                    │
                                    ▼
                             ConsumptionPlan
              │                     │
              └──────────┬──────────┘
                         ▼
                  ValuationPlan
                         │
                         ▼
              opaque PostingResultPlan
                         │
                         ▼
               later authoritative
                   establishment
```

The key architectural invariant is:

```text
ValuationEngine.prepare()
        ↓
complete deterministic plan
        ↓
NO authoritative mutation
```

and, for repost:

```text
prepare(new)
        ↓
success
        ↓
remove(old)
        ↓
establish(new, plan)
```

Therefore a failed deterministic valuation preparation cannot destroy the previously established posting result.

---

# 43. Approval Status

This document is the final WP-4 Concrete API Design.

**Implementation is not authorized until this document is explicitly approved.**

After approval, implementation may proceed strictly against this API. Any deviation affecting:

* public signatures;
* plan semantics;
* movement ordering;
* FIFO delegation;
* source identity semantics;
* persistence boundaries;
* posting integration boundaries;

requires a new architecture/API review before implementation.
