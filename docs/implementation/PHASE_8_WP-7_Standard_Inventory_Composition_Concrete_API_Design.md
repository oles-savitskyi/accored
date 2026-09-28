# AcCoreD — Phase 8 WP-7

# Standard Inventory Composition — Concrete API Design

**Status:** Reconciled — Implemented and Reviewed
**Phase:** 8 — Valuation
**Work Package:** WP-7 — Standard Inventory Composition
**Depends on:** Phase 7 Step 8, Phase 8 WP-6
**Implementation status:** Implemented; implementation review approved without code blockers

---

## 1. Purpose

WP-7 introduces the concrete Standard-layer composition of:

```text
Standard Configuration
        │
        ├── Inventory Register
        │
        ├── Valuation
        │    ├── ValuationKey mapping
        │    ├── ValuationInputProvider
        │    ├── FIFO method
        │    ├── valuation fact persistence
        │    ├── valuation result persistence
        │    └── valuation lifecycle coordinator
        │
        └── Composite Posting Coordinator
```

The purpose of this work package is to make the Standard configuration capable of composing the existing generic accounting platform services into one operational posting path for inventory documents.

WP-7 is a **composition and adapter work package**.

It does not introduce a Standard-specific valuation engine, valuation algorithm, or lifecycle implementation.

---

# 2. API Design Principles

The implementation MUST preserve the following dependency direction:

```text
standard
    │
    ▼
accore.platform
```

The generic platform MUST NOT depend on:

```text
standard
Inventory
product
warehouse
```

The Standard layer is responsible for translating Standard-specific movement semantics into generic valuation inputs.

The generic valuation layer remains responsible for:

* valuation planning;
* layer consumption;
* FIFO;
* valuation plans;
* valuation persistence contracts;
* lifecycle execution.

The posting layer remains responsible for orchestrating posting participants.

---

# 3. Valuation Input Boundary

## 3.1 Generic `ValuationInput`

The current `ValuationInput` couples semantic input with valuation-layer state.

WP-7 replaces it with a pure semantic input:

```python
@dataclass(frozen=True, slots=True)
class ValuationInput:
    valuation_key: ValuationKey
    quantity: Decimal
    document_identity: Identifier
    source_identity: Identifier
    occurred_at: datetime
```

This object represents the information required by valuation planning for one movement.

It MUST NOT contain:

* valuation layers;
* persistence state;
* consumption results;
* `ConsumptionRequest`;
* Standard-specific movement fields.

---

## 3.2 Semantic Ownership

For a Standard Inventory movement, the fields have the following authoritative sources:

| `ValuationInput` field | Source                              |
| ---------------------- | ----------------------------------- |
| `valuation_key`        | `ValuationKeyMapper`                |
| `quantity`             | movement resource `quantity`        |
| `document_identity`    | `movement.source_document_identity` |
| `source_identity`      | `movement.identity`                 |
| `occurred_at`          | `movement.accounting_time`          |

No identity may be reconstructed from valuation operations.

In particular:

```text
document_identity
    =
Movement.source_document_identity
```

and:

```text
source_identity
    =
Movement.identity
```

This preserves the direct document-ownership model introduced by WP-6.

---

# 4. `ValuationKeyMapper`

Generic platform API:

```python
class ValuationKeyMapper(Protocol):
    def map(self, movement: Movement) -> ValuationKey:
        ...
```

The mapper translates movement dimensions into a generic valuation key.

The generic platform MUST NOT know which dimensions are used by Standard Inventory.

---

## 4.1 Standard Inventory Mapper

Standard provides:

```python
class InventoryValuationKeyMapper:
    def map(self, movement: Movement) -> ValuationKey:
        ...
```

For Inventory, the valuation key is derived from:

```text
product
warehouse
```

using the existing Standard Inventory dimension names:

```python
INVENTORY_PRODUCT_DIMENSION
INVENTORY_WAREHOUSE_DIMENSION
```

The mapper MUST validate the required dimensions and MUST NOT introduce alternative dimension semantics.

---

# 5. `ValuationInputProvider`

Generic contract:

```python
class ValuationInputProvider(Protocol):
    def provide(self, movement: Movement) -> ValuationInput:
        ...
```

The provider is the semantic adapter between a movement and the generic valuation engine.

---

## 5.1 Standard Inventory Provider

Standard provides:

```python
class InventoryValuationInputProvider:
    def __init__(
        self,
        key_mapper: ValuationKeyMapper,
    ) -> None:
        ...

    def provide(self, movement: Movement) -> ValuationInput:
        ...
```

The provider MUST:

1. obtain `valuation_key` through `key_mapper`;
2. obtain quantity from the Standard Inventory quantity resource;
3. obtain document identity from `movement.source_document_identity`;
4. obtain source identity from `movement.identity`;
5. obtain occurrence time from `movement.accounting_time`;
6. construct immutable `ValuationInput`.

The Standard quantity resource remains:

```python
INVENTORY_QUANTITY_RESOURCE = "quantity"
```

The provider MUST reject invalid valuation input according to existing valuation/input validation semantics.

---

# 6. `ValuationEngine`

The generic engine constructor becomes:

```python
class ValuationEngine:
    def __init__(
        self,
        input_provider: ValuationInputProvider,
        layer_reader: ValuationLayerReader,
        method: ValuationMethod,
    ) -> None:
        ...
```

The engine MUST no longer extract Standard Inventory semantics directly from `Movement`.

The generic engine workflow becomes:

```text
MovementSet
    │
    ▼
ValuationEngine
    │
    ├── validates movement set
    │
    ├── ValuationInputProvider
    │       │
    │       └── ValuationInput
    │
    ├── obtains valuation layers when required
    │
    ├── constructs valuation operation
    │
    └── invokes ValuationMethod
            │
            └── ValuationPlan
```

The engine remains responsible for generic valuation planning.

---

# 7. FIFO

No Standard FIFO implementation is introduced.

The existing generic:

```python
FIFOValuationMethod
```

remains the implementation of FIFO.

Standard composition simply provides:

```python
FIFOValuationMethod()
```

to the generic `ValuationEngine`.

The following classes MUST NOT be introduced:

```text
StandardFIFOValuationMethod
InventoryFIFOValuationMethod
StandardValuationEngine
InventoryValuationEngine
```

FIFO remains a platform valuation method.

---

# 8. `ValuationPlan`

The WP-6 ownership model remains unchanged:

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    document_identity: Identifier
    operations: tuple[ValuationPlanOperation, ...]
```

`document_identity` is authoritative lifecycle ownership.

The plan MUST NOT require lifecycle ownership to be inferred from individual operations.

No WP-7 changes are made to:

* `LayerEstablishmentPlan`;
* `ConsumptionPlan`;
* `PlannedLayerReference`;
* `PersistedLayerReference`;
* `ValuationPlan`.

---

# 9. Valuation Persistence Contracts

The existing generic contracts remain unchanged.

```python
class ValuationFactPersistence(Protocol):
    def append(self, facts: Sequence[ValuationFact]) -> None:
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

    def enumerate(self) -> tuple[ValuationFact, ...]:
        ...
```

and:

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

    def enumerate_balances(self) -> tuple[CostBalance, ...]:
        ...
```

WP-7 does not change these contracts.

---

# 10. Standard Valuation Persistence

Standard provides concrete implementations:

```python
class StandardValuationFactPersistence:
    ...
```

and:

```python
class StandardValuationResultPersistence:
    ...
```

These are the current concrete Standard composition/test persistence implementations.

They MUST implement the generic valuation persistence protocols.

They MUST NOT introduce Standard-specific protocol variants in `accore.platform.valuation`.

In the current WP-7 implementation both stores are in-memory. They establish the concrete Standard persistence boundary for this composition and do not replace the existing durable AcCoreD persistence infrastructure.

---

# 11. Valuation Lifecycle

The existing generic lifecycle API remains authoritative:

```python
class ValuationLifecycleCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
    ) -> ValuationEstablishmentResult:
        ...

    def remove(
        self,
        document_identity: Identifier,
    ) -> ValuationRemovalResult:
        ...
```

The existing:

```python
DefaultValuationCoordinator
```

remains the concrete implementation.

Standard MUST NOT introduce:

```text
StandardValuationCoordinator
InventoryValuationCoordinator
```

Standard constructs the generic coordinator with Standard-provided persistence implementations and existing generic valuation totals/validation services.

---

# 12. `ValuationPostingCoordinator`

The existing posting adapter remains unchanged conceptually:

```python
class ValuationPostingCoordinator:
    def __init__(
        self,
        engine: ValuationEngine,
        lifecycle: ValuationLifecycleCoordinator,
    ) -> None:
        ...
```

It exposes valuation through the generic posting lifecycle contract.

Its responsibilities remain:

* validate posting-document ownership of the movement set;
* prepare `ValuationPlan`;
* translate valuation lifecycle result into `PostingLifecycleResult`;
* remove valuation state by posting document identity.

It MUST NOT contain Standard Inventory semantics.

---

# 13. Generic Posting Participant Boundary

WP-7 generalizes posting-result composition.

Generic participant contract:

```python
class PostingResultParticipant(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> object:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
    ) -> PostingLifecycleResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> PostingLifecycleResult:
        ...
```

The participant abstraction represents one independent posting-result lifecycle participant.

Examples include:

```text
RegisterPostingResultCoordinator
ValuationPostingCoordinator
```

The generic platform MUST NOT encode which participants Standard chooses.

---

# 14. Participant Plan Ownership

A participant instance MUST NOT be stored inside a prepared posting plan.

The following model is explicitly rejected:

```python
@dataclass(frozen=True, slots=True)
class PostingParticipantPlan:
    participant: PostingResultParticipant
    payload: object
```

A prepared plan MUST represent prepared state, not runtime dependency ownership.

The `CompositePostingResultCoordinator` owns the participant sequence.

Its internal prepared state associates prepared payloads with that participant sequence.

The participant ordering is established when the composite coordinator is constructed.

Conceptually:

```text
CompositePostingResultCoordinator
    │
    ├── participant[0]
    ├── participant[1]
    └── ...
         │
         ▼
prepared participant payloads
```

The implementation may use an internal/private immutable structure for this purpose.

The participant instances themselves are not part of the public plan data model.

---

# 15. Generic `PostingResultPlan`

The previous concrete form:

```python
@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    register: RegisterPostingPlan
    valuation: ValuationPlan
```

is removed.

The posting result plan MUST be composition-neutral.

Conceptually it represents:

```text
prepared posting result
    =
ordered opaque participant preparations
```

The public Posting API MUST NOT expose:

```text
register
valuation
inventory
```

as fields of the generic posting result plan.

The concrete representation of prepared participant payloads is owned by the posting composition implementation.

`PostingEngine` must only treat the plan as an opaque result of:

```python
PostingResultCoordinator.prepare(...)
```

and input to:

```python
PostingResultCoordinator.establish(...)
```

---

# 16. `PostingResultCoordinator`

The generic public coordinator remains:

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
    ) -> PostingLifecycleResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> PostingLifecycleResult:
        ...
```

`PostingEngine` remains dependent only on this contract.

It MUST NOT depend directly on:

```text
ValuationEngine
ValuationPostingCoordinator
RegisterPostingResultCoordinator
StandardConfigurationBootstrap
```

---

# 17. `CompositePostingResultCoordinator`

The generic composite becomes:

```python
class CompositePostingResultCoordinator:
    def __init__(
        self,
        participants: Sequence[PostingResultParticipant],
    ) -> None:
        ...
```

It is generic and does not reference:

```text
Register
Valuation
Inventory
Standard
```

by type or semantic special case.

---

## 17.1 Prepare

Conceptual behavior:

```text
prepare(document, movement_set)
        │
        ├── participant 0.prepare(...)
        │
        ├── participant 1.prepare(...)
        │
        └── ...
        │
        ▼
composition-neutral PostingResultPlan
```

Preparation MUST preserve participant ordering.

The resulting plan contains only the opaque prepared states required to invoke the corresponding participants later.

---

## 17.2 Establish

Conceptual behavior:

```text
participant 0.establish(...)
        │
        ├── FAILURE / INDETERMINATE
        │       └── return immediately
        │
        └── SUCCESS
                │
                ▼
participant 1.establish(...)
                │
                └── ...
```

The first non-success lifecycle result terminates establishment.

No implicit rollback is introduced.

The composite MUST preserve the distinction between:

```text
SUCCESS
FAILURE
INDETERMINATE
```

---

## 17.3 Remove

Removal uses the same participant ordering as the configured composition unless a future architecture decision explicitly changes this.

Conceptually:

```text
participant 0.remove(document)
        │
        ├── non-success → return
        │
        └── success
             ↓
participant 1.remove(document)
             ↓
            ...
```

The composite does not infer ownership from valuation plans or register movements.

Removal is explicitly document-scoped.

---

# 18. Partial Failure Semantics

The composite is not a distributed transaction coordinator.

If:

```text
Register.establish → SUCCESS
Valuation.establish → INDETERMINATE
```

the composite result is:

```text
INDETERMINATE
```

It MUST NOT convert the result to `FAILURE`.

It MUST NOT pretend that the Register effect has been rolled back.

It MUST NOT introduce compensating transactions as part of WP-7.

Recovery remains governed by the existing subsystem lifecycle and recovery architecture.

---

# 19. Standard Inventory Valuation Configuration

The implemented composition root uses a private aggregate that keeps the assembled Standard posting stack explicit:

```python
@dataclass(frozen=True, slots=True)
class _InventoryPostingPlatformComposition:
    register: _InventoryRegisterPlatformComposition
    valuation_engine: ValuationEngine
    valuation_lifecycle: DefaultValuationCoordinator
    valuation_posting: ValuationPostingCoordinator
    posting_result_coordinator: CompositePostingResultCoordinator
```

The aggregate is private. It is a composition artifact rather than a new domain abstraction.

---

# 20. Standard Valuation Composition

The Standard layer constructs:

```text
InventoryValuationKeyMapper
        │
        ▼
InventoryValuationInputProvider
        │
        ▼
ValuationEngine
        │
        ├── LayerReader
        └── FIFOValuationMethod
```

and:

```text
StandardValuationFactPersistence
StandardValuationResultPersistence
        │
        ▼
DefaultValuationCoordinator
        │
        ▼
ValuationPostingCoordinator
```

The resulting Standard valuation component is then passed to the generic posting composite.

---

# 21. Standard Inventory + Valuation + Posting Composition

The final Standard composition is:

```text
StandardConfigurationBootstrap
        │
        ├── Inventory Register
        │     │
        │     ├── TotalsEngine
        │     ├── Maintenance
        │     ├── Mutation
        │     ├── Validator
        │     ├── MovementQuery
        │     ├── BalanceQuery
        │     └── RegisterPostingResultCoordinator
        │
        ├── Valuation
        │     │
        │     ├── InventoryValuationKeyMapper
        │     ├── InventoryValuationInputProvider
        │     ├── ValuationEngine
        │     ├── FIFOValuationMethod
        │     ├── StandardValuationFactPersistence
        │     ├── StandardValuationResultPersistence
        │     ├── DefaultValuationCoordinator
        │     └── ValuationPostingCoordinator
        │
        └── CompositePostingResultCoordinator
              │
              ├── RegisterPostingResultCoordinator
              └── ValuationPostingCoordinator
```

This composition is owned entirely by Standard configuration.

---

# 22. Bootstrap API

The implemented Standard bootstrap remains the composition root for Standard Inventory posting. It preserves the existing Register composition method and adds the following concrete composition method:

```python
class StandardConfigurationBootstrap:
    def compose_inventory_register_platform(
        self,
        persistence: RegisterFactPersistence,
    ) -> _InventoryRegisterPlatformComposition:
        ...

    def compose_inventory_posting_platform(
        self,
        register_persistence: RegisterFactPersistence,
        valuation_fact_persistence: StandardValuationFactPersistence,
        valuation_result_persistence: StandardValuationResultPersistence,
    ) -> _InventoryPostingPlatformComposition:
        ...
```

The implementation constructs:

```text
Inventory Register composition
        ↓
InventoryValuationKeyMapper
        ↓
InventoryValuationInputProvider
        ↓
ValuationEngine + FIFOValuationMethod
        ↓
DefaultValuationCoordinator
        ↓
ValuationPostingCoordinator
        ↓
CompositePostingResultCoordinator
        ├── RegisterPostingResultCoordinator
        └── ValuationPostingCoordinator
```

The exact persistence objects are supplied by the caller. In the current implementation the Standard valuation persistence classes are in-memory concrete stores.

> Standard bootstrap is the composition root for Standard Inventory posting.

# 23. Posting Engine Integration

No architectural change is made to `PostingEngine`.

The dependency remains:

```text
PostingEngine
    ↓
PostingResultCoordinator
```

The runtime object supplied by Standard is:

```text
CompositePostingResultCoordinator
```

Therefore:

```text
PostingEngine
      │
      ▼
PostingResultCoordinator
      │
      ▼
CompositePostingResultCoordinator
      │
      ├── Register
      └── Valuation
```

`PostingEngine` remains unaware of the number and type of posting participants.

---

# 24. Posting Lifecycle

The established lifecycle remains:

```text
prepare
   ↓
remove existing posting result
   ↓
establish new posting result
```

For repost:

```text
prepare new plan
      ↓
remove document-owned existing effects
      ↓
establish new effects
```

The composite does not alter this lifecycle.

It only makes the posting result contain multiple independent lifecycle participants.

---

# 25. Public API Exposure

## Generic platform

The following are platform-level APIs:

```text
ValuationInput
ValuationInputProvider
ValuationKeyMapper
ValuationEngine
ValuationMethod
FIFOValuationMethod
ValuationPlan
ValuationFactPersistence
ValuationResultPersistence
ValuationLifecycleCoordinator
ValuationPostingCoordinator
PostingResultParticipant
PostingResultPlan
PostingResultCoordinator
CompositePostingResultCoordinator
```

Only APIs that are already intended as public platform contracts should be exported from package `__init__.py` files.

Internal composite implementation structures remain private.

---

## Standard layer

Standard exposes only Standard-specific configuration/adapters that are intended for application composition.

Expected Standard APIs include:

```text
InventoryValuationKeyMapper
InventoryValuationInputProvider
StandardValuationFactPersistence
StandardValuationResultPersistence
```

Internal composition artifacts use a leading underscore where appropriate.

No Standard-specific generic-platform subclass is required.

---

# 26. Error Handling

WP-7 does not introduce a new error taxonomy unless required by an existing contract.

Standard adapters SHOULD translate invalid Standard movement semantics into the existing appropriate valuation/input validation errors.

The following principle applies:

```text
Standard adapter errors
        ↓
generic valuation contract errors
        ↓
posting lifecycle result
```

The Standard layer MUST NOT expose persistence implementation exceptions directly as a substitute for the existing lifecycle result model.

---

# 27. Implementation Verification

The implementation covered the following verification areas.

## 27.1 Valuation input and Standard adapters

Tests verify:

* Inventory valuation-key mapping from Product and Warehouse;
* missing required Inventory dimensions;
* positive Decimal quantity extraction;
* invalid quantity rejection;
* document identity preservation;
* source identity preservation;
* accounting-time preservation.

## 27.2 Generic valuation engine

Tests verify the engine's use of `ValuationInputProvider` and preserve the generic semantic boundary rather than extracting Inventory-specific movement fields inside the engine.

## 27.3 Composite coordinator

Tests verify:

* preparation order;
* establishment order;
* removal behavior;
* termination on participant failure;
* termination on participant indeterminate result;
* participant-count mismatch rejection;
* rejection of an empty participant sequence.

The implementation review additionally confirmed that participant instances are owned by the composite and are not stored in `PostingResultPlan`; the current test suite does not require a dedicated structural assertion for this invariant.

## 27.4 Standard composition

Integration tests verify the complete Inventory Register + Valuation composition and repost behavior, including reversal/removal of the prior valuation effect and establishment of the new effect.

## 27.5 Quality gate

The completed implementation passed:

```text
pytest -q                 963 passed
ruff check .             All checks passed
black --check .          221 files unchanged
mypy src                 Success: no issues found in 121 source files
```

The implementation review was approved without code blockers.

# 28. Non-Goals

WP-7 MUST NOT introduce:

```text
StandardValuationEngine
InventoryValuationEngine
StandardFIFOValuationMethod
InventoryFIFOValuationMethod
StandardValuationCoordinator
InventoryValuationCoordinator
Inventory-aware PostingEngine
Inventory-aware CompositePostingResultCoordinator
Register → Valuation dependency
Valuation → Standard dependency
PostingEngine → ValuationEngine dependency
```

WP-7 does not redesign:

* valuation persistence architecture;
* valuation totals;
* valuation queries;
* FIFO algorithm;
* posting engine lifecycle;
* register mutation architecture;
* persistence infrastructure.

---

# 29. Implementation Record

The approved API was implemented in the following logical sequence:

```text
1. Generic valuation input boundary
2. Standard valuation adapters
3. Generic composite posting API
4. Standard valuation persistence
5. Standard valuation composition
6. Full Standard posting composition
7. Integration tests
8. Quality gate
9. Implementation review
10. Documentation reconciliation
```

This section is historical: implementation is complete.

# 30. API Acceptance and Reconciliation

The approved API invariants were verified against the implementation.

## Generic valuation

* `ValuationInput` contains only semantic valuation input.
* `ValuationInputProvider` and `ValuationKeyMapper` are generic contracts.
* `ValuationEngine` no longer extracts Inventory-specific dimensions or resources.
* FIFO remains generic.
* `ValuationPlan` ownership remains document-based.

## Standard

* Inventory dimensions and quantity-resource semantics remain Standard-owned.
* Standard provides the Inventory valuation adapters.
* Standard provides concrete valuation persistence implementations.
* Standard constructs the generic valuation engine and lifecycle coordinator.

## Posting

* `PostingEngine` remains dependent only on `PostingResultCoordinator`.
* `PostingResultParticipant` is generic.
* `PostingResultPlan` is composition-neutral and contains ordered opaque participant preparations.
* Participant instances are owned by `CompositePostingResultCoordinator`, not by the prepared plan.
* The composite does not reference Register or Valuation concrete types by generic mechanism.
* Partial failure and indeterminate outcomes remain distinguishable.
* No distributed transaction or implicit rollback semantics were introduced.

## Architecture

* No dependency from generic platform to Standard.
* No dependency from generic valuation to Inventory.
* No dependency from Register to Valuation.
* Standard remains the composition root.
* No Standard-specific generic-service subclasses were introduced.

## Non-blocking implementation notes

The implementation review identified two non-blocking observations:

1. The current Standard valuation persistence is in-memory and should be understood as the current concrete composition/test persistence boundary, not as the final durable storage implementation.
2. Additional explicit tests for a second participant failure/indeterminate result and for the absence of participant instances inside `PostingResultPlan` could strengthen the suite, although the implementation behavior itself was verified during review.

**API reconciliation status: COMPLETE.**

# 31. Final API Shape

The resulting architecture is:

```text
                         PostingEngine
                              │
                              ▼
                  PostingResultCoordinator
                              │
                              ▼
             CompositePostingResultCoordinator
                    │                    │
                    ▼                    ▼
       RegisterPostingResult      ValuationPosting
          Coordinator                Coordinator
                                       │
                            ┌──────────┴──────────┐
                            ▼                     ▼
                    ValuationEngine        LifecycleCoordinator
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
          ValuationInputProvider    FIFO
                   │
                   ▼
        InventoryValuation adapters
```

Dependency direction:

```text
                 Standard
                    │
                    ▼
              accore.platform
```

Composition ownership:

```text
StandardConfigurationBootstrap
              │
              ├── Inventory Register
              ├── Valuation
              └── Composite Posting
```

Runtime lifecycle:

```text
prepare
   ↓
remove
   ↓
establish
```

Document ownership:

```text
Posting document identity
        │
        ├── Register effects
        └── Valuation effects
```

This is the reconciled Concrete API Design for Phase 8 WP-7 and records the implemented API after API Review, Implementation Review, and Documentation Reconciliation.
