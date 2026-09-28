# AcCoreD — Phase 8 WP-7

# Standard Inventory Composition — Architecture Definition / Scope

**Status:** Reconciled — Implemented and Reviewed
**Phase:** 8 — Valuation
**Work Package:** WP-7 — Standard Inventory Composition
**Depends on:** Phase 7 Inventory Register Completion; Phase 8 WP-1–WP-6
**Implementation status:** Implemented; implementation review approved without code blockers

---

# 1. Purpose

WP-7 introduces the first complete **Standard-level composition** of the Inventory Register and Valuation subsystems.

The target composition is:

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
        │    └── valuation coordinator
        │
        └── Composite Posting Coordinator
```

The architectural objective is to make Standard Configuration provide a complete operational Inventory posting composition while keeping the generic valuation architecture reusable and independent from Standard-specific semantics.

The resulting Standard composition must support:

```text
Operational Document
        ↓
PostingEngine
        ↓
Standard Posting Handler
        ↓
MovementSet
        ↓
Generic Composite Posting Coordinator
        ├── Inventory Register
        └── Valuation
```

WP-7 is therefore primarily a **composition and adapter work package**, not a redesign of the valuation domain.

---

# 2. Scope

WP-7 includes:

1. Standard Inventory valuation-key mapping.
2. Generic `ValuationInputProvider` integration boundary.
3. Standard implementation of the Inventory valuation input provider.
4. Selection/configuration of FIFO as the Standard valuation method.
5. Standard valuation fact persistence implementation.
6. Standard valuation result persistence implementation.
7. Construction of the generic valuation engine.
8. Construction of the generic valuation coordinator.
9. Generic composition infrastructure for multiple posting-result participants.
10. Standard composition of Register and Valuation posting participants.
11. Standard bootstrap integration.
12. Tests proving the complete Standard composition.

WP-7 does **not** introduce:

* a new valuation algorithm;
* new valuation facts;
* new FIFO semantics;
* a Standard-specific valuation engine;
* a Standard-specific valuation coordinator abstraction;
* valuation semantics inside the Inventory Register;
* valuation logic inside posting handlers;
* valuation knowledge inside `PostingEngine`;
* a Standard-specific replacement for generic posting lifecycle orchestration.

---

# 3. Architectural Principle

> **Standard composes generic platform capabilities; it does not redefine generic valuation semantics.**

Standard may provide:

* mappings;
* adapters;
* persistence implementations;
* configuration;
* concrete object construction;
* composition.

Standard must not provide alternative implementations of generic valuation concepts merely because the current Standard configuration happens to use them.

The distinction is:

```text
Standard:
    "Inventory valuation uses FIFO."

Platform:
    "FIFO is a valuation method and this is its generic algorithm."
```

Therefore:

```text
FIFOValuationMethod
    → generic implementation
    → accore.platform.valuation

FIFO selection/configuration
    → Standard composition decision
    → standard
```

---

# 4. Architectural Layers

WP-7 establishes the following three-layer relationship:

```text
                    GENERIC DOMAIN
                          │
                 accore.platform.valuation
                          │
                          ▼
                   GENERIC POSTING
                          │
                  accore.platform.posting
                          │
                          ▼
                 STANDARD COMPOSITION
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
           Inventory             Valuation
```

The dependency direction is:

```text
standard
    ↓
platform contracts / generic implementations
```

and never:

```text
platform
    ↓
standard
```

---

# 5. Existing Integration Points After WP-6

WP-6 provides the following application integration points.

## 5.1 PostingEngine

`PostingEngine` operates through the generic:

```text
PostingResultCoordinator
```

and remains unaware of:

* Inventory;
* FIFO;
* valuation facts;
* valuation persistence;
* cost balances.

Its responsibility remains posting lifecycle orchestration.

WP-7 does not change that responsibility.

---

## 5.2 Generic PostingResultCoordinator

The generic posting boundary provides the lifecycle abstraction:

```text
PostingResultCoordinator
PostingResultPlan
PostingLifecycleResult
```

This boundary remains the integration point between `PostingEngine` and concrete operational effects.

---

## 5.3 RegisterPostingResultCoordinator

The Register coordinator remains responsible for:

```text
Register mutation
Register persistence
Register lifecycle result
```

It remains quantity-oriented and valuation-independent.

No valuation responsibilities are added to it.

---

## 5.4 Valuation Posting Adapter

The generic posting/valuation adapter remains responsible for connecting posting lifecycle semantics with valuation lifecycle semantics.

Conceptually:

```text
ValuationPostingCoordinator
        │
        ├── ValuationEngine
        └── ValuationLifecycleCoordinator
```

It remains a generic platform integration component.

Standard supplies the concrete valuation objects required by it.

---

# 6. Generic Composite Posting Coordination

The existing composite mechanism coordinates multiple posting-result participants.

The review establishes an explicit separation between:

### Generic mechanism

Owned by:

```text
accore.platform.posting
```

It is responsible for generic orchestration of multiple participants.

Conceptually:

```text
CompositePostingResultCoordinator
        │
        ├── PostingResultParticipant
        ├── PostingResultParticipant
        └── ...
```

The composite mechanism must not depend directly on:

```text
RegisterPostingResultCoordinator
ValuationPostingCoordinator
```

because those are concrete business participants.

### Concrete composition

Owned by:

```text
standard
```

Standard constructs:

```text
Generic Composite Posting Coordinator
        │
        ├── RegisterPostingResultCoordinator
        │
        └── ValuationPostingCoordinator
```

This preserves generic orchestration while keeping the actual:

```text
Inventory Register + Valuation
```

composition outside the generic platform.

---

# 7. Standard Composition Target

The resulting runtime graph is:

```text
StandardConfigurationBootstrap
            │
            ├─────────────────────────────┐
            │                             │
            ▼                             ▼
 Inventory Register                 Valuation Configuration
 composition                             │
            │                             ├── ValuationKey mapping
            │                             ├── InputProvider
            │                             ├── FIFO
            │                             ├── FactPersistence
            │                             ├── ResultPersistence
            │                             ├── ValuationEngine
            │                             └── ValuationCoordinator
            │
            └──────────────┬──────────────┘
                           ▼
              Generic Composite Posting
                    Result Coordinator
                           │
                           ▼
                    PostingEngine
```

Standard bootstrap is the composition root.

It wires components; it does not implement their domain algorithms.

---

# 8. Ownership Matrix

| Responsibility                              | Owner                       | Standard role    |
| ------------------------------------------- | --------------------------- | ---------------- |
| `ValuationKey` semantic type                | `accore.platform.valuation` | use              |
| Valuation-key mapping contract              | `accore.platform.valuation` | use              |
| Inventory → `ValuationKey` mapping          | `standard`                  | implement        |
| `ValuationInputProvider` contract           | `accore.platform.valuation` | use              |
| Inventory valuation input provider          | `standard`                  | implement        |
| `ValuationEngine`                           | `accore.platform.valuation` | construct        |
| `ValuationMethod` contract                  | `accore.platform.valuation` | use              |
| FIFO algorithm                              | `accore.platform.valuation` | select/configure |
| Valuation facts                             | `accore.platform.valuation` | use              |
| Valuation fact persistence contract         | `accore.platform.valuation` | use              |
| Valuation fact persistence implementation   | `standard`                  | provide          |
| Valuation result persistence contract       | `accore.platform.valuation` | use              |
| Valuation result persistence implementation | `standard`                  | provide          |
| `ValuationLifecycleCoordinator` contract    | `accore.platform.valuation` | use              |
| Generic valuation coordinator               | `accore.platform.valuation` | construct        |
| Standard valuation coordinator composition  | `standard`                  | compose          |
| Generic posting participant contract        | `accore.platform.posting`   | use              |
| Generic composite coordinator               | `accore.platform.posting`   | use              |
| Register posting coordinator                | `accore.platform.posting`   | construct        |
| Valuation posting adapter                   | `accore.platform.posting`   | construct        |
| Register + Valuation composition            | `standard`                  | provide          |
| Posting lifecycle                           | `accore.platform.posting`   | use              |
| `PostingEngine`                             | `accore.platform.posting`   | unchanged        |

---

# 9. ValuationKey Mapping

Inventory-specific valuation identity is a Standard concern.

The intended flow is:

```text
Movement
   ↓
Standard ValuationKey Mapping
   ↓
ValuationKey
```

For the Inventory composition, the mapping is expected to derive the valuation identity from configured Inventory dimensions such as:

```text
product
warehouse
```

Conceptually:

```text
Inventory Movement
    dimensions
        ├── product
        └── warehouse
              ↓
       ValuationKey
        ├── product
        └── warehouse
```

The generic valuation subsystem must not contain knowledge that:

```text
Inventory uses product + warehouse.
```

That is Standard configuration.

---

# 10. ValuationInputProvider

WP-7 establishes `ValuationInputProvider` as an explicit **generic platform contract**.

Its responsibility is:

> Convert operational Movement semantics into the generic valuation input required by valuation preparation.

The concrete Inventory implementation belongs to Standard.

Conceptually:

```text
Movement
   ↓
ValuationInputProvider
   ↓
ValuationInput
   ├── ValuationKey
   ├── quantity
   ├── source/document identity
   └── occurred_at
```

The exact API is deferred to Concrete API Design.

## 10.1 Provider responsibility

The Standard Inventory provider may use:

* Inventory quantity resource;
* Inventory movement type;
* Inventory dimensions;
* accounting/occurrence time;
* Standard valuation-key mapping;
* source document identity where required by valuation semantics.

## 10.2 Provider non-responsibilities

The provider must not:

* execute FIFO;
* calculate valuation consumption;
* load valuation layers;
* persist valuation facts;
* persist valuation results;
* mutate Inventory Register;
* invoke `PostingEngine`.

## 10.3 Layer ownership

The provider does **not** provide valuation layers.

Layer lookup remains the responsibility of the generic `ValuationEngine`.

The intended architecture is:

```text
Movement
   ↓
ValuationInputProvider
   ↓
ValuationInput
   ↓
ValuationEngine
   ↓
Layer lookup
   ↓
ValuationMethod
   ↓
ValuationPlan
```

This is mandatory because layer state is valuation-engine state rather than Standard input-adapter state.

---

# 11. Valuation Engine Boundary

The generic `ValuationEngine` remains responsible for deterministic valuation preparation.

Conceptually:

```text
MovementSet
    ↓
ValuationInputProvider
    ↓
ValuationInput
    ↓
ValuationEngine
    ↓
ValuationMethod
    ↓
ValuationPlan
```

The engine must not contain Standard-specific conditions such as:

```python
if inventory_register:
    ...
```

or:

```python
if product_dimension and warehouse_dimension:
    ...
```

Standard semantics enter through explicit contracts.

---

# 12. FIFO Ownership

FIFO is the first valuation method selected by Standard.

However:

> **FIFO algorithm ownership remains in `accore.platform.valuation`.**

Standard owns only the configuration decision:

```text
Standard Inventory valuation method
        =
FIFOValuationMethod
```

The dependency remains:

```text
standard
    └── constructs/configures
            ↓
    FIFOValuationMethod
            ↓
accore.platform.valuation
```

and never:

```text
FIFOValuationMethod
    ↓
standard
```

This ensures that future valuation configurations can reuse the same generic FIFO implementation without introducing Standard dependencies into the valuation domain.

---

# 13. Valuation Fact Persistence

The generic platform defines the semantic persistence contract:

```text
ValuationFactPersistence
```

Standard provides its concrete implementation.

The WP-7 concrete Standard persistence implementations are currently in-memory composition/test stores. They implement the generic persistence contracts and establish the Standard composition boundary; they do not constitute a new durable storage engine. Durable persistence remains a responsibility of the existing AcCoreD persistence architecture and may replace these concrete stores in a later integration step.

The semantic distinction must remain:

```text
Valuation facts
    = authoritative historical valuation state
```

and:

```text
Valuation results
    = derived/materialized state
```

The Standard persistence implementation must not reinterpret immutable valuation facts.

---

# 14. Valuation Result Persistence

Standard provides the concrete implementation of:

```text
ValuationResultPersistence
```

This persistence represents derived cost state such as:

```text
CostMovement
CostBalance
```

It remains separate from valuation fact persistence at the semantic level even if both use the same physical storage infrastructure.

The architecture is:

```text
Valuation Coordinator
        │
        ├── Valuation Fact Persistence
        │
        └── Valuation Result Persistence
```

---

# 15. Valuation Coordinator

The generic:

```text
DefaultValuationCoordinator
```

remains owned by `accore.platform.valuation`.

Standard supplies its concrete dependencies.

Conceptually:

```text
DefaultValuationCoordinator
    │
    ├── Standard ValuationFactPersistence
    ├── Standard ValuationResultPersistence
    ├── generic valuation totals
    └── generic valuation planning/validation
```

Standard must not introduce:

```text
StandardValuationCoordinator
```

for WP-7.

The Standard responsibility is composition of the generic coordinator.

---

# 16. Posting Composition

The concrete Standard composition is:

```text
Generic Composite Posting Coordinator
        │
        ├── RegisterPostingResultCoordinator
        │
        └── ValuationPostingCoordinator
```

The Register participant is configured from:

```text
InventoryRegisterConfiguration
```

The Valuation participant is configured from:

```text
Standard Valuation Configuration
```

The composite itself is an orchestration component rather than a new domain model.

---

# 17. PostingEngine Independence

After WP-7, `PostingEngine` must remain unaware of:

```text
InventoryRegister
ValuationKey
FIFO
ValuationInputProvider
ValuationFactPersistence
ValuationResultPersistence
CostMovement
CostBalance
```

Its dependency remains:

```text
PostingEngine
       │
       ▼
PostingResultCoordinator
```

Therefore Standard-specific composition remains hidden behind the generic application boundary.

---

# 18. Posting Handler Independence

Standard posting handlers remain responsible for:

```text
Operational Document
        ↓
MovementSet
```

They must not:

* construct `ValuationKey`;
* invoke FIFO;
* load valuation layers;
* calculate valuation cost;
* persist valuation facts;
* invoke the valuation coordinator directly.

The valuation pipeline begins after MovementSet creation through the posting-result composition.

---

# 19. Register Independence

Inventory Register remains quantity-only:

```text
Inventory Register
    ├── product
    ├── warehouse
    └── quantity
```

Valuation remains separate:

```text
Valuation
    ├── ValuationKey
    ├── valuation layers
    ├── consumption
    ├── cost movements
    └── cost balances
```

The following remain prohibited:

```text
Inventory Register
    └── cost
```

and:

```text
Movement
    ├── quantity
    └── valuation cost
```

---

# 20. Prohibited Leakage

## 20.1 Platform → Standard

Forbidden:

```text
accore.platform.*
        ↓
standard.*
```

Generic platform code must never import Standard configuration or adapters.

---

## 20.2 PostingEngine → Standard

Forbidden:

```text
PostingEngine
    ↓
standard
```

---

## 20.3 PostingEngine → Valuation

Forbidden:

```text
PostingEngine
    ↓
ValuationEngine
```

---

## 20.4 Posting Handler → Valuation

Forbidden:

```text
GoodsReceiptPostingHandler
    ↓
Valuation
```

---

## 20.5 Register → Valuation

Forbidden:

```text
RegisterMutationOrchestrator
    ↓
ValuationCoordinator
```

---

## 20.6 FIFO → Standard

Forbidden:

```text
FIFOValuationMethod
    ↓
standard
```

---

## 20.7 Standard bypassing semantic persistence contracts

Forbidden:

```text
Standard valuation component
        ↓
physical persistence internals
```

when the corresponding semantic platform persistence contract exists.

Standard implementations must use the defined persistence boundary.

---

# 21. Final Dependency Graph

The final WP-7 architecture is:

```text
                         PostingEngine
                              │
                              ▼
                 PostingResultCoordinator
                              │
                              ▼
              Generic Composite Coordinator
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
       Register Participant       Valuation Participant
                 │                         │
                 ▼                         ▼
       Register Mutation          Valuation Lifecycle
                                           │
                                           ▼
                                  DefaultValuationCoordinator
                                           │
                         ┌─────────────────┼─────────────────┐
                         │                 │                 │
                         ▼                 ▼                 ▼
                  Fact Persistence  Result Persistence   Generic Totals
                         ▲                 ▲
                         │                 │
                         └────── Standard ┘
```

The valuation input side is:

```text
Movement
   ↓
Standard ValuationKey Mapping
   ↓
Standard ValuationInputProvider
   ↓
Generic ValuationEngine
   ↓
Layer lookup
   ↓
Generic FIFO
   ↓
ValuationPlan
```

The complete Standard dependency direction is:

```text
                         STANDARD
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Register config   Valuation      Composition
                            │
                 ┌──────────┼──────────┐
                 ▼          ▼          ▼
              Mapping   InputProvider FIFO
                 │          │          │
                 └──────────┼──────────┘
                            ▼
                       PLATFORM
```

---

# 22. Standard Bootstrap Responsibility

`StandardConfigurationBootstrap` is the composition root for the Standard Inventory valuation slice.

It constructs and wires:

```text
Inventory Register
    ↓
Register coordinator

Valuation
    ↓
ValuationKey mapping
    ↓
ValuationInputProvider
    ↓
FIFO
    ↓
Fact persistence
    ↓
Result persistence
    ↓
Valuation engine
    ↓
Valuation coordinator

Posting
    ↓
Generic Composite Coordinator
    ↓
Register participant
    +
Valuation participant
```

Bootstrap must not contain:

* FIFO algorithm;
* valuation calculation;
* Register mutation algorithm;
* valuation lifecycle algorithm.

It performs object construction and dependency wiring only.

---

# 23. Configuration Boundary

The Standard configuration conceptually consists of:

```text
Inventory Register Configuration
        +
Inventory Valuation Configuration
        +
Posting Composition Configuration
```

The valuation configuration describes:

```text
valuation key mapping
valuation input provider
valuation method
valuation persistence
valuation result persistence
```

The posting composition configuration describes:

```text
Register participant
+
Valuation participant
```

Neither configuration layer redefines generic platform contracts.

---

# 24. Lifecycle Semantics

WP-7 preserves the lifecycle semantics established by WP-6.

## POST

```text
MovementSet
    ↓
prepare
    ↓
PostingResultPlan
    ↓
establish
    ↓
DocumentPosted
```

## UNPOST

```text
remove
    ↓
Register reversal
+
Valuation reversal
    ↓
DocumentUnposted
```

## REPOST

```text
new MovementSet
    ↓
prepare(new)
    │
    ├── failure
    │      ↓
    │   old result untouched
    │
    ▼
remove(old)
    ↓
establish(new)
    ↓
DocumentReposted
```

The invariant is:

```text
prepare(new) failure
        ⇒
old established result remains untouched
```

No Standard-specific composition may weaken this guarantee.

---

# 25. Composite Lifecycle Semantics

The generic composite coordinator operates over generic posting participants.

Conceptually:

```text
prepare:
    participant A.prepare
    participant B.prepare

establish:
    participant A.establish
    participant B.establish

remove:
    participant A.remove
    participant B.remove
```

For Standard:

```text
participant A = Inventory Register
participant B = Valuation
```

The generic mechanism must not encode this Standard-specific identity.

This permits future compositions such as:

```text
Register + Valuation + Tax
```

without changing the generic composite abstraction.

---

# 26. Failure Semantics

WP-7 introduces no distributed transaction mechanism.

The existing distinction remains:

```text
FAILURE
    deterministic / rollback-guaranteed failure

INDETERMINATE
    persistence state cannot be established with certainty
```

The Standard composition must preserve these outcomes across:

```text
Register
+
Valuation
```

and expose the resulting lifecycle status through the existing posting contract.

A component must not report successful completion when its persisted state is known to be incomplete or indeterminate.

---

# 27. Architectural Invariants

The following invariants are mandatory.

### Invariant 1 — Generic valuation independence

```text
accore.platform.valuation
    must not depend on standard
```

### Invariant 2 — Generic posting independence

```text
accore.platform.posting
    must not depend on Standard business configuration
```

### Invariant 3 — Generic composite

```text
CompositePostingResultCoordinator
    depends on generic participants,
    not concrete Register/Valuation classes.
```

### Invariant 4 — Standard mapping

```text
Inventory → ValuationKey
```

is Standard-owned.

### Invariant 5 — Standard input adaptation

```text
Inventory Movement → ValuationInput
```

is Standard-owned through the generic `ValuationInputProvider` contract.

### Invariant 6 — Layer lookup

```text
ValuationInputProvider
    does not provide layers.

ValuationEngine
    owns layer lookup.
```

### Invariant 7 — FIFO

```text
FIFO algorithm
    belongs to platform.valuation.
```

### Invariant 8 — Register/Valuation separation

```text
Register
    remains quantity-only.
```

### Invariant 9 — PostingEngine abstraction

```text
PostingEngine
    knows only generic posting-result coordination.
```

### Invariant 10 — Lifecycle preservation

```text
prepare
    precedes
remove
    precedes
establish
```

for successful repost processing.

---

# 28. Architectural Acceptance Criteria

WP-7 architecture is accepted when all of the following remain true.

## A. Ownership

1. Generic valuation contracts and semantics remain in `accore.platform.valuation`.
2. Standard owns Standard-specific mapping, adapters, persistence implementations, and composition.
3. FIFO algorithm remains generic platform code.
4. Standard selects/configures FIFO rather than reimplementing it.
5. Generic Composite Posting coordination remains platform infrastructure.
6. Concrete Register + Valuation composition belongs to Standard.

## B. Valuation input

7. `ValuationInputProvider` is a generic platform contract.
8. Inventory implementation of `ValuationInputProvider` belongs to Standard.
9. Provider derives valuation input from Movement and Standard mapping.
10. Provider does not load valuation layers.
11. Layer lookup remains inside `ValuationEngine`.
12. Generic valuation engine contains no Inventory-specific assumptions.

## C. Integration

13. `PostingEngine` remains unchanged in semantic responsibility.
14. Register posting remains quantity-only.
15. Posting handlers remain valuation-independent.
16. Standard composition provides both Register and Valuation posting participants.

## D. Persistence

17. Standard provides concrete valuation fact persistence.
18. Standard provides concrete valuation result persistence.
19. Historical valuation facts remain authoritative and immutable.
20. Derived cost results remain distinct from valuation facts.
21. Existing document ownership and reversal traceability remain supported.

## E. Lifecycle

22. Standard composition preserves `prepare → remove → establish` repost ordering.
23. Valuation preparation occurs before destructive removal.
24. No hidden mutable preparation state is introduced.
25. Domain events remain emitted only after successful coordinated completion.

## F. Dependency direction

26. `accore.platform.valuation` does not import Standard.
27. Generic Posting infrastructure does not import Standard configuration.
28. Generic Composite Coordinator does not depend on concrete Register or Valuation coordinators.
29. Standard depends on platform contracts and generic implementations, never the reverse.
30. No valuation implementation leaks into Inventory Register mutation.

---

# 29. Out of Scope

The following remain outside WP-7:

```text
New valuation methods
Currency / FX
Multi-currency valuation
Accounting valuation policies beyond FIFO
Inventory Issue document
Advanced valuation adjustments
Distributed transactions
Persistent storage technology redesign
Generic PostingEngine redesign
New valuation fact types
Cost query API redesign
Rebuild architecture redesign
```

These may be addressed by subsequent work packages.

---

# 30. Architecture Review Decisions

The Architecture Review produced the following decisions.

## ADR-WP7-01 — Standard owns valuation composition, not valuation semantics

`standard` owns concrete Inventory valuation mapping, adapters, persistence implementations and composition.

Generic valuation semantics remain in `accore.platform.valuation`.

**Decision: ACCEPTED**

---

## ADR-WP7-02 — ValuationKey mapping is an explicit Standard boundary

Inventory-specific mapping from Movement dimensions to `ValuationKey` belongs to Standard.

Generic valuation does not encode Inventory dimension semantics.

**Decision: ACCEPTED**

---

## ADR-WP7-03 — ValuationInputProvider is a generic contract

`ValuationInputProvider` is defined by `platform.valuation`.

The Inventory-specific implementation is supplied by Standard.

The provider supplies valuation semantics derived from Movement.

It does not supply valuation layers.

Layer lookup remains inside `ValuationEngine`.

**Decision: ACCEPTED**

---

## ADR-WP7-04 — FIFO remains generic

`FIFOValuationMethod` remains in `accore.platform.valuation`.

Standard selects/configures FIFO.

**Decision: ACCEPTED**

---

## ADR-WP7-05 — Persistence implementations belong to Standard

Generic valuation persistence contracts remain in `platform.valuation`.

Concrete Standard persistence implementations belong to `standard`.

**Decision: ACCEPTED**

---

## ADR-WP7-06 — Generic Composite, Standard composition

Generic composite posting orchestration remains in `platform.posting`.

The generic composite depends on generic posting-result participants rather than concrete Register and Valuation classes.

Standard creates the concrete composition:

```text
RegisterPostingResultCoordinator
+
ValuationPostingCoordinator
+
Generic Composite Coordinator
```

**Decision: ACCEPTED**

---

# 31. Implementation Reconciliation

The architecture was implemented without changing its approved dependency boundaries. The implementation review found no code blockers.

## 31.1 Implemented Composition

`StandardConfigurationBootstrap.compose_inventory_posting_platform(...)` now composes:

```text
Inventory Register
        +
Inventory Valuation
        +
Composite Posting Result Coordinator
```

The resulting private composition structure contains:

```text
register
valuation_engine
valuation_lifecycle
valuation_posting
posting_result_coordinator
```

The implemented method accepts:

```python
def compose_inventory_posting_platform(
    self,
    register_persistence: RegisterFactPersistence,
    valuation_fact_persistence: StandardValuationFactPersistence,
    valuation_result_persistence: StandardValuationResultPersistence,
) -> _InventoryPostingPlatformComposition:
    ...
```

## 31.2 Implemented Generic Boundaries

The implementation confirms the approved generic boundaries:

* `ValuationInput` contains only semantic valuation input.
* `ValuationKeyMapper` and `ValuationInputProvider` are generic contracts.
* Inventory mapping and input extraction are implemented in Standard.
* `ValuationEngine` no longer extracts Inventory-specific dimensions or resources.
* FIFO remains `accore.platform.valuation.FIFOValuationMethod`.
* `PostingResultParticipant` is generic.
* `PostingResultPlan` contains ordered opaque participant preparations and does not contain participant instances.
* `CompositePostingResultCoordinator` is generic and does not reference Register or Valuation concrete types.
* `PostingEngine` remains dependent only on `PostingResultCoordinator`.

## 31.3 Ownership and Repost Semantics

The WP-6 document-ownership model is preserved. Valuation input receives:

```text
document_identity = movement.source_document_identity
source_identity   = movement.identity
```

Valuation removal is document-scoped, and repost remains:

```text
prepare → remove → establish
```

No inference-based ownership or distributed rollback semantics were introduced.

## 31.4 Standard Persistence Clarification

`StandardValuationFactPersistence` is an append-only in-memory valuation-fact store and `StandardValuationResultPersistence` is an in-memory materialized result store in the current WP-7 implementation. They are concrete Standard composition implementations for the current runtime/test boundary, not a replacement for AcCoreD's durable persistence infrastructure.

This is an implementation-level clarification and does not change the approved semantic persistence contracts.

## 31.5 Verification

The implementation passed the project quality gate:

```text
pytest -q                 963 passed
ruff check .             All checks passed
black --check .          221 files unchanged
mypy src                 Success: no issues found in 121 source files
```

The final implementation review was **APPROVED — no code blockers**. Two non-blocking observations remain documented for future refinement: additional composite failure/opaque-plan assertions could strengthen test coverage, and durable Standard valuation persistence can be connected to the existing persistence infrastructure when that integration is scheduled.

# 32. Definition of Done — Architecture and Reconciliation

The architecture stage and reconciliation stage are complete:

```text
WP-7 Architecture Definition / Scope
        ↓
Architecture Review
        ↓
Review amendments
        ↓
Final Architecture Definition
        ↓
Concrete API Design
        ↓
API Review / Approval
        ↓
Implementation
        ↓
Implementation Review
        ↓
Documentation Reconciliation
        ↓
COMPLETE
```

The companion Concrete API Design document is the reconciled implementation baseline for the public and composition APIs described by WP-7.
