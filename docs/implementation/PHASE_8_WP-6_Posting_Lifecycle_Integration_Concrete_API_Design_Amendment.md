# AcCoreD — Phase 8 WP-6

# Posting Lifecycle Integration — Concrete API Design

**Status:** Approved Concrete API Design Amendment
**Phase:** 8 — Valuation
**Work Package:** WP-6 — Posting Lifecycle Integration
**Depends on:** WP-5 Final Architecture and API
**Implementation:** Implemented and verified

---

# 1. Amendment Summary

During implementation verification of the approved WP-6 API, a traceability gap was identified in the existing valuation fact model.

`ValuationLayer` already carries the originating document identity, while `ValuationConsumption` currently identifies its source through movement/source identity only.

This is insufficient for lifecycle reversal:

```text
remove(document)
```

because valuation reversal must be able to identify **all valuation effects belonging to the posted document**, including consumption effects.

The amendment therefore introduces an explicit document ownership identity into every valuation fact participating in posting lifecycle reversal.

The key rule is:

> Every persisted valuation fact that contributes to a document's established valuation effect must be traceable directly to that posting document.

This amendment does **not** change FIFO semantics or valuation calculation.

---

# 2. Problem Being Corrected

The current model permits:

```text
ValuationLayer
    └── source_document_identity

ValuationConsumption
    └── source_identity
```

where `source_identity` identifies the source movement/layer relationship but does not necessarily identify the posting document whose valuation effect contains the consumption.

Consequently:

```text
remove(document)
```

cannot reliably reconstruct:

```text
all valuation facts established by document
```

without introducing inference through unrelated domain relationships.

Such inference is explicitly rejected.

---

# 3. New Valuation Fact Ownership Rule

Every persisted valuation fact participating in posting lifecycle reversal

must carry direct posting-document ownership metadata representing the posting document responsible for establishing that fact.

This metadata is lifecycle ownership metadata.

It is not a replacement for existing source identities.

The concrete ownership field depends on the valuation fact type. Therefore, the common ownership rule does not require every valuation fact to expose a field named `document_identity`.

A valuation fact may contain both posting-document ownership metadata and source identity metadata, where the two identities answer different questions.

### Document ownership

> Which posting document established this valuation fact?

### Source identity

> Which movement, layer, resource, or other valuation relationship does this valuation fact describe?

The ownership metadata must be sufficient to identify the posting document whose lifecycle is responsible for the fact and therefore whose reversal must include that fact.

---

# 4. ValuationLayer

`ValuationLayer` retains its existing posting-document ownership through `source_document_identity`:

```python
@dataclass(frozen=True, slots=True)
class ValuationLayer:

    source_document_identity: Identifier

    ...
```

No semantic change is required.

`source_document_identity` identifies the posting document that established the valuation layer.

The existing `source_movement_identity` remains unchanged and continues to identify the movement from which the valuation layer was created.

Therefore:

```text
ValuationLayer

├── source_document_identity
│      └── posting document responsible for establishing the layer
│
└── source_movement_identity
       └── movement that established the layer
```

This existing field satisfies the posting-document ownership requirement for `ValuationLayer`.

---

# 5. ValuationConsumption

`ValuationConsumption` is amended to carry direct posting-document ownership.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class ValuationConsumption:

    document_identity: Identifier
    source_identity: Identifier

    ...
```

The existing `source_identity` remains unchanged.

The new `document_identity` identifies the posting document that produced the consumption fact.

Therefore:

```text
ValuationConsumption

├── document_identity
│      └── posting document responsible for establishing the consumption fact
│
└── source_identity
       └── source movement/layer relationship
```

This is additive lifecycle ownership metadata.

It does not change FIFO consumption semantics, layer selection, quantity allocation, or valuation mathematics.

The distinction is therefore:

```text
ValuationLayer
    source_document_identity → posting-document ownership

ValuationConsumption
    document_identity        → posting-document ownership
    source_identity          → source valuation relationship
```

The lifecycle reversal mechanism uses the appropriate ownership field for each valuation fact type rather than assuming a universal `document_identity` field across all `ValuationFact` implementations.

---

# 6. FIFO Semantics Remain Unchanged

The amendment must not alter:

* FIFO ordering;
* layer selection;
* synthetic consumption;
* quantity allocation;
* valuation cost calculation;
* Decimal arithmetic;
* valuation movement generation.

The only new information propagated through valuation preparation is:

```text
document_identity
```

for lifecycle traceability.

Therefore:

```text
ValuationEngine.prepare()
```

continues to produce the same valuation result for the same document/movement input, with the additional explicit ownership identity attached to generated facts.

---

# 7. ValuationPlan Ownership

The `ValuationPlan` must carry enough information for every generated valuation fact to retain document ownership.

The preferred shape is:

```python
@dataclass(frozen=True, slots=True)
class ValuationPlan:
    document_identity: Identifier
    ...
```

The document identity is therefore established at preparation time.

Every fact materialized from the plan must use:

```python
plan.document_identity
```

rather than attempting to infer document ownership later during persistence.

---

# 8. Establishment Traceability

The establishment flow becomes:

```text
Posting document
      │
      ▼
ValuationEngine.prepare()
      │
      ▼
ValuationPlan
      │
      ├── document_identity
      │
      ├── valuation layers
      │
      └── consumption facts
             │
             ▼
       Valuation establishment
             │
             ▼
       persisted valuation facts
```

All persisted facts produced from one plan therefore retain the same posting-document identity.

---

# 9. Persistence Contract

The valuation fact persistence boundary must support direct lookup by document identity for **all valuation fact types** participating in reversal.

Conceptually:

```python
class ValuationFactPersistence(Protocol):
    def append(...):
        ...

    def find_by_source_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        ...
```

The existing method name may remain if it already expresses this semantic contract.

Its implementation must now cover:

* valuation layers;
* valuation consumption facts;
* any additional persisted valuation fact types introduced before or by WP-6.

No caller should need to reconstruct document ownership through source-movement relationships.

---

# 10. Reversal Lookup

`ValuationLifecycleCoordinator.remove()` uses:

```python
document_identity
```

as the authoritative lifecycle lookup key.

The removal algorithm is conceptually:

```text
document_identity
       │
       ▼
find all valuation facts owned by document
       │
       ▼
classify established valuation effects
       │
       ▼
construct compensating valuation facts
       │
       ▼
persist compensating facts
       │
       ▼
apply compensating cost movements
       │
       ▼
update derived cost state
```

No indirect graph traversal is required.

---

# 11. Consumption Reversal

Consumption facts require explicit reversal semantics.

A consumption fact established by a document represents a reduction of available valuation-layer quantity.

Its compensating reversal must restore the corresponding derived valuation effect without modifying the original consumption fact.

Therefore:

```text
Original:
    ValuationConsumption(document=A, source=L, quantity=Q)

Reversal:
    compensating fact representing:
        restore quantity Q from source L
```

The original fact remains immutable.

The exact concrete compensating fact representation belongs to the valuation reversal API, but it must preserve:

* original document identity;
* original source identity;
* quantity;
* valuation cost information required to restore derived state.

---

## 12. Reversal Traceability

Every reversal fact must remain traceable to both:

* the original valuation fact being reversed;
* the posting document responsible for the reversal.

The implemented representation is:

```python
@dataclass(frozen=True, slots=True)
class ValuationReversal:
    identity: Identifier
    reversed_identity: Identifier
    valuation_key: ValuationKey
    document_identity: Identifier
    source_identity: Identifier
    created_at: datetime
```

reversed_identity identifies the original valuation fact being compensated.

document_identity identifies the posting document whose lifecycle produced the reversal.

source_identity preserves the source relationship required by the resulting compensating cost movement.

The original valuation fact remains immutable. The reversal is represented as a separate historical fact.

For example:

```text
original ValuationConsumption
        │
        │ identity
        ▼
ValuationReversal
    ├── reversed_identity
    ├── document_identity
    └── source_identity
```

This provides an auditable relation between the original valuation fact and its lifecycle reversal without mutating historical valuation history.

---

# 13. Removal Idempotency

The amendment also makes idempotency semantics explicit.

A document's established valuation effect must be identifiable independently of whether it contains:

* only layers;
* only consumption;
* both layers and consumption;
* multiple consumption facts;
* multiple valuation movements.

`remove(document_identity)` must operate on the complete set of established facts belonging to that document.

The API must not assume that every posting produces a layer.

---

# 14. No Inference Through Movement History

The implementation must not perform reversal using logic such as:

```text
document
  → movements
  → source movement
  → valuation layer
  → infer consumption
```

when direct document ownership is available.

This would create a fragile dependency between posting history and valuation persistence.

The direct ownership field is the authoritative lifecycle link.

---

# 15. PostingResultPlan — unchanged

The generic posting plan remains:

```python
@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    register: RegisterPostingPlan
    valuation: ValuationPlan
```

The amendment does not change the generic posting lifecycle.

`PostingEngine` still treats this plan as opaque.

---

# 16. PostingResultCoordinator — unchanged

The generic contract remains:

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
    ) -> PostingResultEstablishmentResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> PostingResultRemovalResult:
        ...
```

No valuation-specific information is introduced into this interface.

---

# 17. Valuation Lifecycle API — unchanged

The valuation lifecycle remains:

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

The amendment changes the **data available to the lifecycle implementation**, not the generic lifecycle boundary.

---

# 18. Valuation Posting Adapter — unchanged

`ValuationPostingCoordinator` remains:

```python
class ValuationPostingCoordinator:
    def __init__(
        self,
        engine: ValuationEngine,
        lifecycle: ValuationLifecycleCoordinator,
    ) -> None:
        ...
```

Preparation:

```text
MovementSet
    ↓
ValuationEngine.prepare()
    ↓
ValuationPlan(document_identity=...)
```

Establishment:

```text
ValuationPlan
    ↓
ValuationLifecycleCoordinator.establish()
```

Removal:

```text
document.identity
    ↓
ValuationLifecycleCoordinator.remove()
```

---

# 19. Composite Coordinator — unchanged

The composite coordinator remains responsible for:

```text
prepare()
establish()
remove()
```

The amendment does not introduce valuation knowledge into the composite coordinator.

Its valuation child remains isolated behind `ValuationPostingCoordinator`.

---

# 20. Repost Lifecycle — unchanged

The safe repost sequence remains:

```text
prepare(new)
    ↓
PostingResultPlan
    ↓
remove(old)
    ↓
establish(new, plan)
```

The amendment ensures that:

```text
remove(old)
```

can now identify **all** valuation effects of `old`.

---

# 21. Repost Safety Improvement

The previous lifecycle risk was:

```text
remove(old)
    ↓
partial valuation reversal
    ↓
unknown remaining valuation effects
```

After the amendment:

```text
old document identity
    ↓
complete valuation-fact lookup
    ↓
all owned valuation effects
    ↓
complete compensating reversal
```

The reversal operation therefore has an explicit, deterministic discovery boundary.

Persistence may still become indeterminate, but the system no longer has an ambiguity about **which facts belong to the document**.

---

# 22. Failure Semantics — unchanged

The previously approved failure states remain.

### Preparation failure

```text
old unchanged
new absent
```

### Removal failure

```text
old not successfully reversed
new absent
```

### Removal indeterminate

```text
old indeterminate
new absent
```

### Removal success + establishment failure

```text
old reversed
new absent
```

### Removal success + establishment indeterminate

```text
old reversed
new indeterminate
```

The amendment does not alter these lifecycle semantics.

---

# 23. Persistence Indeterminacy

Direct document ownership does not eliminate persistence indeterminacy.

For example:

```text
find facts
    SUCCESS

append compensating facts
    INDETERMINATE
```

still produces:

```text
ValuationRemovalState.INDETERMINATE
```

The lifecycle must not infer successful reversal merely because the correct facts were identified.

---

# 24. Required Changes to Existing Types

The implementation must therefore update the valuation model at minimum as follows:

```text
ValuationLayer
    existing document identity retained

ValuationConsumption
    + document_identity

ValuationPlan
    + document_identity if not already present

ValuationFactPersistence
    find_by_source_document()
    must include consumption facts
```

Any other persisted valuation fact type introduced before WP-6 must undergo the same ownership review.

---

# 25. Required Changes to Fact Construction

All construction paths for `ValuationConsumption` must receive document identity explicitly.

The preferred source is:

```text
ValuationPlan.document_identity
```

rather than:

```text
infer from Movement
infer from source layer
infer from persistence
```

This ensures ownership is established once and propagated consistently.

---

# 26. Required Changes to Tests

Existing valuation tests must be amended to verify:

### Consumption ownership

```text
ValuationConsumption.document_identity
```

is populated correctly.

### Persistence lookup

A document lookup returns:

```text
ValuationLayer
+
ValuationConsumption
```

facts belonging to that document.

### Isolation

Facts belonging to another document are not returned.

### Reversal completeness

A document containing both:

```text
layer facts
consumption facts
```

has both effects reversed.

### Historical immutability

Original layer and consumption facts remain unchanged after reversal.

---

# 27. New Required WP-6 Tests

At minimum:

```text
Document A
    establishes:
        Layer A
        Consumption A1
        Consumption A2

Document B
    establishes:
        Consumption B1
```

Then:

```text
remove(Document A)
```

must reverse:

```text
Layer A
Consumption A1
Consumption A2
```

and must not reverse:

```text
Consumption B1
```

This test is mandatory because it validates the new ownership boundary directly.

---

# 28. Required Repost Test

A repost test must establish an original document containing consumption effects:

```text
Document A
    ↓
ValuationPlan A
    ↓
Consumption A
```

Then repost:

```text
Document A
    ↓
new MovementSet
    ↓
prepare(new)
    ↓
remove(old)
    ↓
compensate Consumption A
    ↓
establish(new)
```

The final valuation state must contain:

* original historical facts;
* compensating reversal facts;
* new valuation facts.

It must not contain the old established effect as an active derived state.

---

# 29. Documentation Amendment

The following documentation must explicitly state:

> `ValuationConsumption` carries the identity of the posting document that established the fact so that valuation lifecycle reversal can locate and compensate all valuation effects belonging to that document without mutating historical facts.

This requirement must be reconciled into the relevant WP-5/WP-6 valuation model documentation during documentation reconciliation.

---

# 30. Architectural Boundary Preserved

This amendment does **not** move lifecycle responsibility into `ValuationEngine`.

The final ownership remains:

```text
ValuationEngine
    deterministic calculation/preparation

ValuationLifecycleCoordinator
    establishment and reversal lifecycle

ValuationFactPersistence
    authoritative historical fact storage

CostTotalsEngine
    derived cost-state calculation
```

The new posting-document ownership metadata is data required to connect these boundaries; it is not lifecycle logic.

---

# 31. Final Amended API Decision

The resulting concrete API remains:

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
    ) -> PostingResultEstablishmentResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> PostingResultRemovalResult:
        ...
```

```python
@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    register: RegisterPostingPlan
    valuation: ValuationPlan
```

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

with the amended valuation fact ownership:

```python
@dataclass(frozen=True, slots=True)
class ValuationConsumption:
    document_identity: Identifier
    source_identity: Identifier
    ...
```

and the invariant:

```text
Every persisted valuation fact contributing to a posting's
valuation effect is directly traceable to that posting's
document identity.
```

---

# 32. Implementation Gate

The approval gate described below has been completed.

The amended API has been implemented and verified as part of WP-6. The implementation order below is retained solely as the historical implementation sequence for this amendment and does not represent remaining implementation work.

The implementation proceeded in the following historical order:

1. amend `ValuationConsumption`;
2. propagate `document_identity` through valuation preparation;
3. update valuation fact persistence lookup;
4. implement valuation lifecycle removal/reversal;
5. implement generic posting result plan/result contracts;
6. adapt register coordinator;
7. implement valuation posting adapter;
8. implement composite coordinator;
9. integrate POST/REPOST lifecycle into `PostingEngine`;
10. add targeted valuation reversal tests;
11. add register + valuation integration tests;
12. run full quality gate;
13. reconcile documentation;
14. perform final review;
15. create the separate WP-6 implementation commit.

The completed implementation does not use any workaround based on inferred ownership or movement-graph traversal. Direct posting-document ownership is the authoritative lifecycle traceability boundary.

---

# 33. Final Amendment Decision

The amendment is therefore:

> **Approved API direction:** valuation lifecycle reversal is keyed by posting-document identity, and every persisted valuation fact participating in that lifecycle carries direct document ownership metadata.

This closes the traceability gap discovered during implementation verification without changing valuation mathematics, FIFO semantics, historical immutability, or the generic posting lifecycle.
