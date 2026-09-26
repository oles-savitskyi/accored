# Phase 8 — Valuation

## WP-5 — Valuation Establishment

### Architecture Definition / Scope

**Status:** Final — Implementation Completed and Reviewed
**Phase:** 8 — Valuation
**Work Package:** WP-5 — Valuation Establishment

---

## 1. Purpose

WP-5 defines the authoritative establishment boundary between the valuation plan produced by WP-4 and the persisted valuation state of the platform.

WP-4 is responsible for deterministic preparation:

```text
MovementSet
    ↓
ValuationEngine.prepare()
    ↓
ValuationPlan
```

WP-5 is responsible for authoritative establishment:

```text
ValuationPlan
    ↓
ValuationCoordinator.establish()
    ↓
Authoritative Valuation Facts
    ↓
Derived Cost Movements
    ↓
Materialized Cost Balance
```

The purpose of WP-5 is therefore not to recalculate valuation, but to transform an already prepared and validated valuation plan into durable valuation state.

WP-5 establishes the boundary between:

* preparation and establishment;
* calculated plans and authoritative facts;
* authoritative valuation state and derived cost results;
* valuation processing and posting/register mutation.

---

# 2. Architectural Position

The Phase 8 valuation lifecycle is:

```text
Operational Movement
        │
        ▼
   MovementSet
        │
        ▼
 ValuationEngine.prepare()
        │
        ▼
   ValuationPlan
        │
        ▼
 ValuationCoordinator.establish()
        │
        ├───────────────┐
        ▼               ▼
 Valuation Facts    Cost Movements
        │               │
        │               ▼
        │        Cost Totals Engine
        │               │
        │               ▼
        │          Cost Balance
        │
        ▼
Authoritative Valuation State
```

The following architectural distinction is mandatory:

### Authoritative

* `ValuationLayer`
* `ValuationConsumption`
* future valuation fact types such as adjustments and allocations

### Derived / Materialized

* `CostMovement`
* `CostBalance`

`ValuationCoordinator` establishes authoritative facts and produces the derived movement representation required by the cost-result subsystem.

`CostBalance` is not an independent source of truth.

---

# 3. Scope

WP-5 includes:

1. establishment orchestration for `ValuationPlan`;
2. validation of the complete plan before the first authoritative write;
3. transformation of `LayerEstablishmentPlan` into `ValuationLayer`;
4. transformation of `ConsumptionPlan` into `ValuationConsumption`;
5. authoritative generation of valuation fact identities;
6. construction of corresponding `CostMovement` records;
7. persistence through valuation fact persistence;
8. integration with the cost-result materialization boundary;
9. deterministic processing of an already prepared plan;
10. explicit handling of persistence failure and indeterminate establishment;
11. preservation of valuation fact immutability;
12. separation from register mutation and posting lifecycle.

---

# 4. Out of Scope

WP-5 does not include:

* FIFO algorithm changes;
* valuation preparation;
* changes to `ValuationMethod.consume()`;
* changes to `ValuationEngine.prepare()` unless required by an explicitly approved architectural amendment;
* valuation queries;
* valuation rebuild/recovery implementation;
* unposting/reversal/repost orchestration;
* posting event publication;
* register mutation;
* changes to `RegisterMutationOrchestrator`;
* distributed transaction infrastructure;
* cross-system transaction coordination;
* Standard Inventory composition;
* currency or FX architecture;
* accounting-period policy;
* tax valuation;
* alternative valuation methods;
* optimization of persistence;
* replacement of the existing Cost Totals Engine architecture.

---

# 5. Preparation vs Establishment

The architecture strictly separates preparation from authoritative establishment.

## Preparation

Preparation is performed by:

```python
ValuationEngine.prepare(movement_set)
```

Preparation:

* reads existing valuation state;
* applies the approved valuation method;
* determines layer consumption;
* creates a `ValuationPlan`;
* performs no authoritative persistence;
* does not generate authoritative valuation identities.

The resulting `ValuationPlan` is therefore **not authoritative state**.

## Establishment

Establishment is performed by:

```python
ValuationCoordinator.establish(plan)
```

Establishment:

* validates the complete plan;
* creates authoritative valuation facts;
* assigns authoritative identities;
* creates corresponding cost movements;
* persists the resulting state;
* materializes the corresponding cost balance through the cost-result subsystem.

Establishment must not rerun FIFO or otherwise reinterpret the valuation decision made during preparation.

---

# 6. Dedicated Valuation Coordinator

WP-5 introduces a dedicated valuation establishment component:

```python
class ValuationCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...
```

The coordinator is responsible for orchestration, not for implementing the valuation algorithm.

Its responsibilities are limited to:

```text
ValuationPlan
    ↓
validate
    ↓
construct facts
    ↓
construct CostMovements
    ↓
persist/materialize
```

The coordinator must not become a replacement for:

* `ValuationEngine`;
* `ValuationMethod`;
* `CostTotalsEngine`;
* register mutation services;
* posting orchestration.

---

# 7. Authoritative Identity Generation

Authoritative valuation identities are generated during establishment.

A plan operation does not become a persisted valuation fact merely because it has an identity suitable for planning.

For example:

```text
LayerEstablishmentPlan
    ↓
authoritative establishment
    ↓
ValuationLayer.identity
```

The generated identity becomes stable only when the valuation fact is established.

This preserves the distinction between:

```text
planned operation
```

and:

```text
authoritative persisted fact
```

Authoritative valuation identities are generated by the establishment implementation with the existing `Identifier.new()` mechanism. No dedicated public `ValuationIdentityGenerator` is introduced.

The implementation therefore keeps planning references separate from authoritative identities:

```text
PlannedLayerReference
        ↓
ValuationCoordinator.establish()
        ↓
Identifier.new()
        ↓
ValuationLayer.identity
```

---

# 7.1. Intra-Plan Layer References

WP-5 uses two distinct reference types:

```python
@dataclass(frozen=True, slots=True)
class PlannedLayerReference:
    value: Identifier

@dataclass(frozen=True, slots=True)
class PersistedLayerReference:
    identity: Identifier

type LayerReference = PlannedLayerReference | PersistedLayerReference
```

`PlannedLayerReference` identifies a layer established earlier in the same `ValuationPlan`. It is a planning reference, not the authoritative persisted identity. `PersistedLayerReference` identifies an already established authoritative layer.

A consumption operation may therefore consume an inbound layer established earlier in the same `MovementSet`. The reference must resolve in plan order; a planned reference used before its establishment is invalid.

This model is part of the implemented WP-5/WP-4 API amendment.

# 8. Layer Establishment Semantics

A `LayerEstablishmentPlan` establishes a new immutable `ValuationLayer`.

The semantic requirements are:

```text
quantity > 0
total_cost >= 0
```

Cost is explicitly allowed to be zero.

This is required because the existing valuation architecture supports delayed cost.

For example:

```text
Receipt:
    quantity = 10
    cost = 0
```

may establish:

```text
ValuationLayer:
    quantity = 10
    total_cost = 0
```

A later supplier invoice or cost adjustment may then introduce additional cost through a valuation adjustment.

Therefore WP-5 must not require positive cost for layer establishment.

---

# 9. Consumption Establishment Semantics

A `ConsumptionPlan` establishes an immutable `ValuationConsumption`.

The semantic requirements are:

```text
quantity > 0
cost >= 0
```

Consumption quantity is represented as a positive consumed quantity.

Negative balance effects are represented by `CostMovement`, not by making the `ValuationConsumption.quantity` negative.

For example:

```text
ValuationConsumption:
    quantity = 6
    cost = 60
```

produces a cost movement with the balance effect:

```text
CostMovement:
    quantity = -6
    cost = -60
```

---

# 10. Cost Movement Semantics

`CostMovement` represents the effect of an established valuation operation on the cost balance.

The semantic convention is:

### Layer establishment

```text
quantity = +Q
cost     = +C
```

### Consumption

```text
quantity = -Q
cost     = -C
```

Cost may be zero.

For example:

```text
Receipt:
    +10 quantity
    +100 cost

Consumption:
    -6 quantity
    -60 cost

Result:
    +4 quantity
    +40 cost
```

`CostMovement` is therefore a derived balance-effect representation.

It is not an authoritative replacement for valuation facts.

---

# 11. Cost Balance Responsibility

WP-5 preserves the existing architectural separation:

```text
CostMovement
      ↓
Cost Totals Engine
      ↓
CostBalance
```

`ValuationCoordinator` must not become the owner of cost aggregation logic.

The coordinator may construct and submit `CostMovement` records, but the calculation/materialization of `CostBalance` belongs to the cost totals subsystem.

This separation is required so that the same cost-result machinery can support:

* normal establishment;
* rebuild;
* recovery;
* future maintenance operations.

The exact public API of the Cost Totals component is part of Concrete API Design.

---

# 12. Complete Plan Validation

The entire `ValuationPlan` must be validated before the first authoritative write.

The conceptual sequence is:

```text
ValuationPlan
    │
    ▼
validate entire plan
    │
    ▼
construct all authoritative facts
    │
    ▼
construct all CostMovements
    │
    ▼
persistence/materialization
```

The purpose is to prevent a known-invalid later operation from being discovered only after earlier operations have already been written.

Validation includes, as applicable:

* operation structure;
* valuation-key consistency;
* positive quantities;
* non-negative costs;
* layer references;
* operation ordering constraints;
* identity/reference validity;
* consistency between consumption quantity and planned cost;
* persistence-independent domain invariants.

The exact validation API belongs to Concrete API Design.

---

# 13. Plan Operation Dependencies

The Architecture Definition explicitly recognizes that a single `MovementSet` may contain operations whose valuation semantics depend on an earlier operation in the same plan.

Example:

```text
Movement 1:
    INCOME
    Product A
    quantity = 10

Movement 2:
    EXPENSE
    Product A
    quantity = 6
```

If both operations belong to one prepared `ValuationPlan`, the second operation may consume a layer established by the first operation.

The architectural requirement is:

> A valuation plan must be able to represent valid intra-plan valuation dependencies without requiring the first operation to be independently persisted before the second operation can be prepared.

Because authoritative layer identity is created only during establishment, Concrete API Design must define a transient/reference mechanism for a layer established earlier within the same plan.

Such a reference is planning state, not authoritative persisted identity.

The final WP-5 API must therefore preserve:

```text
planned layer reference
        ≠
authoritative layer identity
```

while allowing:

```text
LayerEstablishmentPlan
        ↓
ConsumptionPlan
```

dependencies inside one plan.

---

# 14. Establishment Does Not Recalculate Valuation

WP-5 must not execute FIFO again.

The following architecture is prohibited:

```text
ValuationPlan
    ↓
ValuationCoordinator
    ↓
run FIFO again
    ↓
create different result
```

The required architecture is:

```text
ValuationEngine
    ↓
ValuationPlan
    ↓
ValuationCoordinator
    ↓
establish exactly that plan
```

This preserves determinism and maintains a single responsibility for valuation-method decisions.

---

# 15. Persistence Boundary

WP-5 preserves the existing separation between authoritative valuation persistence and derived valuation-result persistence.

Authoritative valuation facts are persisted through:

```text
ValuationFactPersistence
```

including, as applicable:

* `ValuationLayer`;
* `ValuationConsumption`;
* future authoritative valuation fact types.

Derived valuation results are handled through the result/cost persistence boundary:

```text
ValuationResultPersistence
```

together with the Cost Totals subsystem.

The conceptual responsibility is:

```text
                 ValuationCoordinator
                         │
                         ▼
                Authoritative Facts
                         │
                         ▼
              ValuationFactPersistence
                         
                         │
                         ▼
                  CostMovements
                         │
                         ▼
                Cost Totals Engine
                         │
                         ▼
                   CostBalance
                         │
                         ▼
              ValuationResultPersistence
```

The architectural distinction is:

```text
ValuationFactPersistence
    → authoritative valuation state

Cost Totals / Result Persistence
    → derived and materialized cost state
```

`ValuationCoordinator` may orchestrate these persistence boundaries, but it does not merge their responsibilities into one persistence abstraction.

The semantic dependency remains:

```text
validate
    →
authoritative valuation facts
    →
derived CostMovements
    →
materialized CostBalance
```

The exact persistence APIs, batching behavior, call structure, and transaction integration are deferred to Concrete API Design.

Transaction ownership and physical transaction boundaries are defined separately by the **Establishment Transaction Boundary**.

---

# 16. Failure and Indeterminate State

Establishment must distinguish between successful completion, failed establishment, and an establishment whose durable state cannot be determined conclusively.

The system therefore recognizes the following semantic outcomes:

```text
SUCCESS
FAILURE
INDETERMINATE
```

### SUCCESS

The establishment operation completed according to the persistence guarantees available to the implementation.

The resulting authoritative valuation state and required derived state are considered established.

### FAILURE

The establishment did not produce an established valuation result, and the persistence boundary guarantees that no relevant partial establishment remains within the applicable transaction scope.

The exact failure mapping belongs to Concrete API Design.

### INDETERMINATE

The system cannot conclusively determine whether the complete establishment was committed.

For example:

```text
Valuation Facts
    ↓
committed
    ↓
Cost Results
    ↓
failure / connection loss / unknown commit outcome
```

may leave the system unable to determine the complete durable state from the immediate operation result.

An indeterminate establishment must not be reported as ordinary success.

It must remain compatible with later recovery, reconciliation, or rebuild.

The exact outcome representation and failure mapping belong to Concrete API Design.

The physical transaction model is defined by the **Establishment Transaction Boundary** and is not redefined here.

---

# 17. Establishment Transaction Boundary

WP-5 defines `ValuationCoordinator.establish(plan)` as the **logical transaction boundary of one valuation establishment attempt**.

This means that one invocation of:

```python
ValuationCoordinator.establish(plan)
```

represents one attempt to transform a valid `ValuationPlan` into authoritative valuation state and its corresponding derived cost state.

The logical establishment boundary is:

```text
ValuationPlan
    │
    ▼
validate entire plan
    │
    ▼
construct authoritative facts
    │
    ▼
construct CostMovements
    │
    ▼
persist/materialize
    │
    ▼
establishment outcome
```

This logical boundary must not be confused with a database transaction boundary.

## Persistence Transaction

The concrete persistence implementation may execute establishment within one local persistence transaction when the relevant state is covered by the same transactional resource.

For example:

```text
BEGIN
    persist Valuation Facts
    persist CostMovements
    materialize CostBalance
COMMIT
```

If the persistence layer provides such atomicity, a failure before commit must leave no committed partial establishment within that transaction.

However, WP-5 does not require that all establishment state be covered by one physical database transaction. The exact transaction capability belongs to Concrete API Design and the persistence implementation.

## No Distributed Transaction

WP-5 does not introduce or require a distributed transaction.

In particular, establishment must not require a transaction spanning:

* valuation persistence;
* register persistence;
* posting state;
* external systems;
* independent transaction resources.

The valuation subsystem therefore does not coordinate a distributed commit.

## Indeterminate Establishment

If the persistence boundaries do not provide atomicity across all establishment outputs, a failure may occur after part of the establishment has been durably persisted.

For example:

```text
Valuation Facts
    ↓
COMMIT
    ↓
CostMovements / CostBalance
    ↓
FAILURE
```

This produces an **indeterminate establishment state**.

Such a state must not be reported as ordinary success.

The establishment outcome must distinguish:

```text
SUCCESS
FAILURE
INDETERMINATE
```

The exact representation of these outcomes belongs to Concrete API Design.

## Architectural Rule

The architectural rule is therefore:

> **`ValuationCoordinator.establish(plan)` is one logical establishment attempt. Physical transaction atomicity is provided only by the persistence boundaries available to the implementation. WP-5 does not introduce distributed transaction coordination.**

This preserves a clear distinction between:

```text
Logical establishment boundary
        ≠
Physical database transaction
        ≠
Distributed transaction
```

and leaves the concrete transaction/locking strategy to the persistence API design.

---

# 18. Immutability

Valuation facts remain immutable after establishment.

In particular:

```text
ValuationLayer
ValuationConsumption
```

are facts, not mutable working records.

Cost corrections are represented by additional valuation facts rather than mutation of historical layer state.

For example:

```text
Initial receipt:
    Layer:
        quantity = 10
        cost = 0

Later invoice:
    Adjustment:
        +100 cost
```

This preserves an auditable valuation history.

---

# 19. Delayed Cost

WP-5 explicitly supports delayed-cost valuation.

The architecture permits:

```text
Receipt:
    quantity = 10
    cost = 0
```

followed later by:

```text
Cost Adjustment:
    +100
```

Therefore:

* layer cost may be zero;
* cost movement cost may be zero;
* positive cost is not a prerequisite for establishment;
* cost corrections must be represented through valuation facts.

This is consistent with the existing Phase 8 valuation model.

---

# 20. Register Independence

`ValuationCoordinator` does not mutate operational register state.

The separation is:

```text
Posting
   │
   ├── Register Result
   │
   └── Valuation Result
```

rather than:

```text
ValuationCoordinator
    ↓
RegisterMutationOrchestrator
```

The valuation subsystem must not directly call:

* `RegisterMutationOrchestrator`;
* register maintenance services;
* register balance services.

Register state remains the responsibility of the posting/register subsystem.

---

# 21. Posting Independence

The valuation subsystem does not publish posting lifecycle events.

In particular, WP-5 does not own:

* `DocumentPosted`;
* `DocumentUnposted`;
* `DocumentReposted`.

Those events remain part of the posting lifecycle.

The valuation coordinator is invoked as part of the appropriate higher-level posting orchestration but remains internally focused on valuation establishment.

The future composite posting-result boundary may coordinate register and valuation establishment, but that integration is outside the direct implementation scope of WP-5.

---

# 22. Posting Result Integration Boundary

The approved Phase 8 architectural amendment establishes the future integration shape:

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

The composite plan may contain:

```text
RegisterPlan
ValuationPlan
```

The posting engine remains valuation-agnostic.

The important lifecycle invariant is:

```text
prepare(new)
    ↓
if prepare fails:
    old state remains untouched
```

Therefore repost must not remove the previous established result until preparation of the replacement result has succeeded.

The concrete posting integration is not part of WP-5 implementation unless explicitly included in a later approved work package.

---

# 23. Recovery Compatibility

WP-5 must produce durable state that can support future rebuild/recovery.

The authoritative recovery source is valuation facts.

Conceptually:

```text
Valuation Facts
      ↓
CostMovements
      ↓
Cost Totals Engine
      ↓
CostBalance
```

Recovery must not depend on an opaque internal state held by `ValuationCoordinator`.

This requirement is one reason why:

* facts are persisted explicitly;
* cost movements are derived explicitly;
* balance aggregation is delegated to the Cost Totals Engine.

Actual recovery implementation remains outside WP-5.

---

# 24. Determinism

Given the same valid `ValuationPlan`, establishment must produce semantically equivalent authoritative state.

Establishment must not depend on:

* current mutable FIFO state;
* repeated valuation-method execution;
* incidental collection ordering;
* non-deterministic operation selection.

Where authoritative identifiers require generated values, Concrete API Design must define the identity contract without changing the semantic contents of the plan.

---

# 25. Testing Scope

WP-5 tests must cover at minimum:

### Establishment

* layer establishment;
* consumption establishment;
* mixed plans;
* multiple operations;
* intra-plan dependencies;
* zero-cost layers;
* zero-cost movements.

### Validation

* invalid quantity;
* invalid cost;
* invalid references;
* inconsistent operations;
* invalid complete plans rejected before persistence.

### Persistence

* facts persisted;
* derived cost movements created;
* balance materialization invoked through the appropriate cost subsystem;
* persistence failures mapped correctly;
* indeterminate state represented correctly.

### Immutability

* established facts are immutable;
* corrections use additional facts.

### Separation

* valuation coordinator does not mutate registers;
* valuation coordinator does not execute FIFO;
* valuation coordinator does not own cost aggregation;
* valuation coordinator does not publish posting lifecycle events.

### Determinism

* identical plans produce equivalent valuation state;
* operation order is preserved where semantically relevant.

---

# 26. Acceptance Criteria

WP-5 Architecture is considered correctly implemented when all of the following hold.

## A. Preparation Boundary

* `ValuationEngine.prepare()` remains the valuation decision boundary.
* `ValuationCoordinator` does not rerun FIFO.
* Preparation performs no authoritative persistence.

## B. Establishment

* A valid `ValuationPlan` can be authoritatively established.
* `LayerEstablishmentPlan` becomes an immutable `ValuationLayer`.
* `ConsumptionPlan` becomes an immutable `ValuationConsumption`.
* Authoritative identities are established at establishment time.

## C. Cost Semantics

* layer quantity is positive;
* layer cost is non-negative;
* consumption quantity is positive;
* consumption cost is non-negative;
* layer establishment produces positive balance-effect movement;
* consumption produces negative balance-effect movement;
* zero cost is supported.

## D. Dependencies

* valid intra-plan valuation dependencies are representable;
* a consumption operation may reference a layer established earlier in the same plan;
* transient planning references are not confused with authoritative persisted identities.

## E. Derived Results

* `CostMovement` is treated as derived balance-effect state;
* `CostBalance` remains the responsibility of the Cost Totals subsystem;
* aggregation logic is not embedded in `ValuationCoordinator`.

## F. Validation

* the complete plan is validated before the first authoritative write;
* known-invalid plans do not produce partial successful establishment.

## G. Persistence

* authoritative facts use `ValuationFactPersistence`;
* derived result state uses the appropriate result/cost persistence boundary;
* persistence failure cannot be silently reported as success;
* indeterminate state is explicitly represented.

## H. Architectural Separation

* valuation does not directly mutate registers;
* valuation does not own posting lifecycle events;
* posting remains valuation-agnostic;
* no distributed transaction is introduced.

## I. Recovery Compatibility

* persisted valuation facts are sufficient as the authoritative basis for future rebuild/recovery;
* cost results can be reconstructed from the authoritative valuation state.

---

# 27. Concrete API Design Boundary

The following Concrete API decisions are now reconciled with the implementation:

1. `ValuationCoordinator.establish(plan) -> ValuationEstablishmentResult`;
2. `PlannedLayerReference`, `PersistedLayerReference`, and `LayerReference`;
3. authoritative identities generated with `Identifier.new()`;
4. complete-plan validation before authoritative persistence;
5. signed `CostMovement` construction;
6. `CostTotalsEngine` delegation for cost aggregation;
7. explicit `SUCCESS / FAILURE / INDETERMINATE` outcomes;
8. `ValuationPersistenceError.rollback_guaranteed` mapping to `FAILURE` or `INDETERMINATE`;
9. infrastructure-owned physical transaction boundaries;
10. reconciliation/rebuild compatibility from authoritative valuation facts;
11. no distributed transaction and no exactly-once guarantee.

The Architecture Definition is therefore fully reconciled with the implemented Concrete API.

# 28. Architectural Summary

WP-5 establishes the following authoritative model:

```text
                 MovementSet
                      │
                      ▼
              ValuationEngine
                      │
                      ▼
                ValuationPlan
                      │
                      ▼
             ValuationCoordinator
                      │
             ┌────────┴────────┐
             ▼                 ▼
      Valuation Facts     CostMovements
             │                 │
             │                 ▼
             │          Cost Totals Engine
             │                 │
             │                 ▼
             │            CostBalance
             │
             ▼
       Authoritative
       Valuation State
```

The central architectural rule is:

> **WP-5 establishes the valuation plan; it does not recalculate valuation. Authoritative valuation facts are the source of truth, while CostMovement and CostBalance are derived/materialized representations maintained through the cost-result subsystem.**

This preserves:

* deterministic valuation;
* immutable valuation history;
* delayed-cost support;
* explicit consumption facts;
* recovery compatibility;
* separation of valuation and registers;
* separation of establishment and aggregation;
* and a clean future boundary for composite posting-result orchestration.

**Architecture Definition / Scope: Final — Implementation Completed and Reviewed.**

Final validation:

- valuation unit tests: 52 passed
- full project tests: 948 passed
- Ruff: PASS
- Black: PASS
- mypy: PASS

Architecture review: PASS
Implementation review: PASS
Documentation reconciliation: completed

No unresolved WP-5 architectural deviations remain.
