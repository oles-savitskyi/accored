# AcCoreD — Phase 8 WP-6

# Posting Lifecycle Integration — Final Architecture

**Status:** Approved Architecture
**Phase:** 8 — Valuation
**Work Package:** WP-6 — Posting Lifecycle Integration
**Predecessors:** WP-1 through WP-5
**Architecture State:** Final — architecture approved; Concrete API Design subsequently approved and implemented

---

## 1. Purpose

WP-6 integrates the valuation lifecycle with the existing posting lifecycle without coupling the generic posting engine to valuation-specific concepts.

The architectural objective is to make posting a coordinated platform operation capable of establishing both:

* operational register effects;
* valuation effects.

The integration must preserve the architectural boundaries established by Phase 7 and WP-1–WP-5:

* `PostingEngine` remains domain-neutral;
* `RegisterPostingResultCoordinator` remains register-specific;
* `ValuationEngine` remains responsible for deterministic valuation preflight;
* `ValuationPlan` remains immutable and opaque to the posting engine;
* historical valuation facts remain immutable;
* valuation reversal is represented by compensating facts rather than deletion or mutation;
* cross-domain distributed transactions are not introduced.

WP-6 therefore introduces a generic posting-result lifecycle and composes independent result coordinators behind that lifecycle.

---

# 2. Architectural Principles

## 2.1 Posting remains domain-neutral

`PostingEngine` coordinates the posting lifecycle but does not know:

* registers;
* valuation;
* FIFO;
* cost balances;
* valuation facts;
* valuation-specific persistence;
* valuation-specific errors.

The posting engine operates exclusively through the generic `PostingResultCoordinator` contract.

---

## 2.2 Result domains remain independent

Register posting and valuation are separate result domains.

The architecture must not introduce:

```text
PostingEngine → RegisterPostingResultCoordinator
PostingEngine → ValuationCoordinator
```

Instead:

```text
                    PostingEngine
                          │
                          ▼
              PostingResultCoordinator
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
 Register result domain       Valuation result domain
```

The posting lifecycle is generic; domain-specific behavior is supplied through coordinator implementations.

---

## 2.3 Preparation is distinct from establishment

The architecture explicitly separates:

1. deterministic preparation;
2. destructive or state-changing removal;
3. establishment of the prepared result.

Preparation must occur before any operation that can change an already-established posting result.

This is especially important for reposting.

---

## 2.4 Plans are explicit

Prepared state is represented by an immutable `PostingResultPlan`.

The plan is passed explicitly from preparation to establishment.

No coordinator may depend on hidden mutable state such as:

```text
prepare()
    ↓
internal pending plan
    ↓
establish()
```

Instead:

```text
prepare()
    ↓
PostingResultPlan
    ↓
establish(..., plan)
```

This makes lifecycle state explicit, testable, and deterministic.

---

# 3. Posting Result Lifecycle Boundary

WP-6 establishes the following generic lifecycle boundary:

```text
PostingResultCoordinator
├── prepare(document, movement_set)
├── establish(document, movement_set, plan)
└── remove(document)
```

Conceptually:

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

The exact concrete API is defined separately in the Concrete API Design stage.

The architectural contract is more important than the exact Python signature.

---

# 4. PostingResultPlan

`PostingResultPlan` is the generic representation of prepared posting-result state.

It has the following architectural properties:

* immutable;
* operation-specific;
* created during `prepare()`;
* consumed by `establish()`;
* opaque to `PostingEngine`;
* owned by the result coordinator that created it;
* not stored as mutable coordinator state.

The posting engine may pass the plan through the lifecycle, but must not inspect or interpret its contents.

Conceptually:

```text
MovementSet
     │
     ▼
prepare()
     │
     ▼
PostingResultPlan
     │
     ▼
establish(..., plan)
```

The plan does not represent persisted state.

It represents a deterministic preparation result that is safe to use for establishment.

---

# 5. Register Result Lifecycle

The existing register posting implementation remains responsible exclusively for register effects.

`RegisterPostingResultCoordinator` will participate in the generic lifecycle:

```text
prepare()
    ↓
register-specific prepared state
    ↓
PostingResultPlan

establish()
    ↓
register movements established

remove()
    ↓
existing register movements removed
```

No valuation semantics are introduced into the register coordinator.

The register coordinator therefore remains reusable independently of valuation.

---

# 6. Valuation Result Lifecycle

WP-6 introduces an explicit valuation lifecycle boundary.

The existing `ValuationEngine.prepare()` remains the deterministic valuation preflight mechanism.

The existing `ValuationCoordinator.establish()` remains responsible for establishing the valuation result represented by a `ValuationPlan`.

WP-6 additionally defines the complementary lifecycle operation required to reverse an already-established valuation result.

Conceptually:

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

The exact API and result types belong to Concrete API Design.

The important architectural distinction is:

```text
establish()
    establishes a prepared valuation result

remove()
    reverses an already-established valuation result
```

`remove()` is not another form of `prepare()` and must not be folded into valuation preparation.

---

# 7. Valuation Removal Semantics

Valuation removal must **not** delete or mutate historical valuation facts.

The semantic model is:

```text
Historical valuation facts
        │
        │ immutable
        ▼
Existing valuation effect
        │
        ▼
Compensating valuation facts
        │
        ▼
Reversed derived valuation state
```

Therefore:

```text
remove(old document)
```

means:

> establish the compensating valuation effect required to reverse the currently established valuation result associated with the document.

It does **not** mean:

```text
DELETE valuation facts
UPDATE historical valuation facts
REBUILD history by mutation
```

This preserves the historical fact model established in WP-4 and WP-5.

---

# 8. Valuation Reversal and Derived State

The valuation lifecycle must maintain the consistency of derived valuation state when a result is reversed.

The architectural responsibility includes:

* identifying the established valuation effect associated with the document;
* producing the corresponding compensating valuation facts;
* applying the compensating result to derived cost state;
* preserving historical facts;
* reporting whether the reversal completed successfully, failed deterministically, or became indeterminate.

The exact representation of compensating facts and persistence operations is an implementation/API concern and must be specified in Concrete API Design.

The architectural invariant is:

> Reversal is an append-only semantic operation over valuation history.

---

# 9. Composite Posting Result Coordinator

WP-6 introduces a composite coordinator responsible for coordinating the independent result domains.

Conceptually:

```text
CompositePostingResultCoordinator
│
├── RegisterPostingResultCoordinator
│
└── ValuationPostingCoordinator
        │
        └── ValuationLifecycleCoordinator
```

The composite coordinator implements the generic:

```text
prepare()
establish()
remove()
```

lifecycle.

Its purpose is orchestration, not domain logic.

---

# 10. ValuationPostingCoordinator

`ValuationPostingCoordinator` is the adapter between the generic posting-result lifecycle and the valuation subsystem.

Its responsibilities are:

### Preparation

Delegate valuation preparation to:

```text
ValuationEngine.prepare()
```

and wrap the resulting valuation plan in the appropriate generic posting-result plan.

### Establishment

Extract the valuation-specific prepared state from the generic plan and delegate establishment to the valuation lifecycle coordinator.

### Removal

Delegate reversal/removal to the valuation lifecycle coordinator.

It must not duplicate FIFO, synthetic consumption, valuation fact construction, cost calculation, or persistence logic.

---

# 11. Composite Preparation

Preparation must be non-destructive.

Conceptually:

```text
MovementSet
     │
     ▼
Composite.prepare()
     │
     ├── Register.prepare()
     │
     └── Valuation.prepare()
     │
     ▼
PostingResultPlan
```

If preparation fails:

```text
prepare(new)
    ↓
failure
```

then:

* no existing result is removed;
* no new result is established;
* no lifecycle event is published.

This property is mandatory for safe reposting.

---

# 12. POST Lifecycle

The resulting POST lifecycle is:

```text
PostingEngine
    │
    ▼
Resolve posting handler
    │
    ▼
Handler produces MovementSet
    │
    ▼
Validate MovementSet
    │
    ▼
PostingResultCoordinator.prepare()
    │
    ▼
PostingResultPlan
    │
    ▼
PostingResultCoordinator.establish(plan)
    │
    ▼
DocumentPosted
```

The event is published only after successful logical completion of the result establishment lifecycle.

---

# 13. REPOST Lifecycle

The resulting REPOST lifecycle is explicitly ordered:

```text
PostingEngine
    │
    ▼
Resolve posting handler
    │
    ▼
Handler produces new MovementSet
    │
    ▼
Validate MovementSet
    │
    ▼
prepare(new)
    │
    ├── failure → old state untouched
    │
    ▼
PostingResultPlan
    │
    ▼
remove(old)
    │
    ├── failure/indeterminate → do not establish new
    │
    ▼
establish(new, plan)
    │
    ├── failure after successful removal
    │
    ▼
DocumentReposted
```

The key invariant is:

> New posting preparation must complete successfully before the previously established posting result is removed.

This replaces the current unsafe order:

```text
remove(old)
    ↓
establish(new)
```

with:

```text
prepare(new)
    ↓
remove(old)
    ↓
establish(new)
```

---

# 14. Repost Failure Semantics

WP-6 distinguishes three materially different failure points.

## 14.1 Preparation failure

```text
prepare(new) → failure
```

Result:

* old register state remains;
* old valuation state remains;
* no new state is established;
* no `DocumentReposted` event;
* operation returns a deterministic posting failure.

This is the safe preflight failure case.

---

## 14.2 Removal failure or indeterminate removal

```text
prepare(new) → success
remove(old) → failure/indeterminate
```

Result:

* new result must not be established automatically;
* `DocumentReposted` is not published;
* the lifecycle reports the removal outcome;
* indeterminate persistence state must not be guessed.

Automatic recovery is outside the posting engine's responsibility unless explicitly introduced by a later architecture.

---

## 14.3 Establishment failure after successful removal

This is a distinct state:

```text
prepare(new) → success
remove(old) → success
establish(new) → failure
```

At this point the old result has already been reversed.

Therefore the system cannot represent this as an ordinary preflight failure.

The resulting semantic state is:

```text
old result: reversed
new result: not established
```

The architecture must expose this distinction explicitly through lifecycle result/error semantics.

The Concrete API Design must define the exact result type and error taxonomy.

In particular, this case must not be silently converted into:

```text
repost failed; old state remains
```

because that would be factually incorrect.

---

# 15. Indeterminate Persistence

The architecture preserves the existing persistence-indeterminacy model.

If persistence reports:

```text
operation failed
rollback guaranteed
```

the coordinator may classify the operation as deterministic failure.

If persistence reports:

```text
operation failed
rollback not guaranteed
```

the result is indeterminate.

The system must not infer success or failure beyond the information supplied by the persistence boundary.

This applies independently to:

* register result establishment/removal;
* valuation establishment/removal.

The composite coordinator must preserve the strongest relevant lifecycle state rather than hiding indeterminacy.

---

# 16. Composite Failure Model

The composite coordinator does not introduce a distributed transaction.

Therefore:

```text
Register domain
       │
       ├── success
       │
       └── failure/indeterminate

Valuation domain
       │
       ├── success
       │
       └── failure/indeterminate
```

cannot be assumed to share one atomic transaction.

The coordinator is an orchestration boundary, not a two-phase commit coordinator.

No 2PC, distributed transaction manager, or cross-domain rollback protocol is introduced by WP-6.

---

# 17. Cross-Domain Ordering

The composite coordinator must define a deterministic ordering for domain operations.

The ordering must satisfy:

1. all deterministic preparation occurs before destructive removal;
2. removal occurs before establishment of the replacement;
3. domain operation failures are not hidden;
4. events are published only after the required lifecycle completion;
5. indeterminate state is surfaced rather than guessed.

The exact domain ordering during `remove()` and `establish()` must be specified in Concrete API Design together with the corresponding partial-failure semantics.

The architecture does not claim atomicity that the persistence boundaries do not provide.

---

# 18. Event Semantics

Posting lifecycle events remain downstream of successful logical lifecycle completion.

For POST:

```text
establish(new)
    ↓
success
    ↓
DocumentPosted
```

For REPOST:

```text
prepare(new)
    ↓
remove(old)
    ↓
establish(new)
    ↓
successful lifecycle completion
    ↓
DocumentReposted
```

No event may be published when the lifecycle is known to have failed.

No event may falsely represent a successful repost when establishment is indeterminate.

---

# 19. PostingEngine Responsibilities

After WP-6, `PostingEngine` remains responsible for:

* resolving the posting handler;
* constructing posting context;
* obtaining `MovementSet`;
* validating movements;
* invoking the generic posting-result lifecycle;
* publishing lifecycle events according to coordinator outcomes;
* translating generic lifecycle failures into posting-level errors.

It does **not** become responsible for:

* valuation;
* FIFO;
* cost calculations;
* valuation facts;
* register movement persistence;
* compensating valuation facts;
* valuation balances;
* domain-specific recovery.

---

# 20. Explicit Architectural Non-Responsibilities

WP-6 does not introduce:

* valuation algorithms;
* new FIFO semantics;
* changes to synthetic consumption rules;
* changes to `ValuationEngine.prepare()`;
* mutation of historical valuation facts;
* distributed transactions;
* 2PC;
* hidden coordinator state;
* valuation-specific logic in `PostingEngine`;
* valuation-specific logic in `RegisterPostingResultCoordinator`.

WP-6 also does not redefine the existing valuation mathematics.

---

# 21. Data and Ownership Boundaries

The resulting ownership model is:

```text
PostingEngine
    owns lifecycle orchestration

PostingResultCoordinator
    owns generic result lifecycle coordination

CompositePostingResultCoordinator
    owns cross-domain orchestration

RegisterPostingResultCoordinator
    owns register-result lifecycle

ValuationPostingCoordinator
    owns adaptation between posting lifecycle and valuation lifecycle

ValuationEngine
    owns deterministic valuation preparation

ValuationLifecycleCoordinator
    owns establishment and reversal of valuation effects

ValuationPlan
    owns immutable prepared valuation state

PostingResultPlan
    owns immutable generic prepared result state
```

No component may take ownership of another domain's internal state.

---

# 22. Architectural Invariants

The following invariants are mandatory.

### Invariant 1 — Posting neutrality

`PostingEngine` contains no valuation-specific dependency.

### Invariant 2 — Register isolation

`RegisterPostingResultCoordinator` contains no valuation-specific dependency.

### Invariant 3 — Deterministic preflight

`ValuationEngine.prepare()` remains deterministic and non-authoritative.

### Invariant 4 — Immutable plan

`ValuationPlan` remains immutable.

### Invariant 5 — Explicit generic plan

`PostingResultPlan` is passed explicitly from preparation to establishment.

### Invariant 6 — No hidden pending state

Coordinators do not store prepared plans in mutable instance state between lifecycle calls.

### Invariant 7 — Safe repost preflight

A failed `prepare(new)` cannot alter the existing established result.

### Invariant 8 — Historical immutability

Historical valuation facts are never deleted or mutated as part of reversal.

### Invariant 9 — Compensating reversal

Valuation removal is represented by compensating valuation facts and corresponding derived-state maintenance.

### Invariant 10 — Event correctness

Posting lifecycle events are emitted only after the required lifecycle operation has completed successfully.

### Invariant 11 — Indeterminacy preservation

An indeterminate persistence result remains indeterminate at the lifecycle boundary.

### Invariant 12 — No distributed atomicity claim

The composite coordinator does not claim atomic cross-domain rollback.

### Invariant 13 — Explicit partial failure

Successful removal followed by failed/indeterminate establishment is represented as a distinct lifecycle outcome.

---

# 23. Target Architecture

The complete target architecture is:

```text
                           PostingEngine
                                │
                                ▼
                   PostingResultCoordinator
                                │
                                ▼
                 CompositePostingResultCoordinator
                         /                  \
                        /                    \
                       ▼                      ▼
        RegisterPostingResultCoordinator   ValuationPostingCoordinator
                    │                              │
                    ▼                              ▼
          Register result domain       ValuationLifecycleCoordinator
                                                   │
                                  ┌────────────────┴────────────────┐
                                  ▼                                 ▼
                         ValuationEngine.prepare()          Valuation persistence
                                  │
                                  ▼
                           ValuationPlan
```

Lifecycle:

```text
POST
────

MovementSet
    │
    ▼
prepare()
    │
    ▼
PostingResultPlan
    │
    ▼
establish(plan)
    │
    ▼
DocumentPosted
```

```text
REPOST
──────

New MovementSet
    │
    ▼
prepare(new)
    │
    ▼
PostingResultPlan
    │
    ▼
remove(old)
    │
    ▼
establish(new, plan)
    │
    ▼
DocumentReposted
```

Failure during preparation never crosses into removal.

Failure after removal is represented explicitly and is not falsely reported as if the old state still existed.

---

# 24. Implementation Boundary

The following implementation work is authorized by this architecture, subject to Concrete API Design:

1. evolve the generic `PostingResultCoordinator` contract;
2. introduce immutable `PostingResultPlan`;
3. adapt the register result coordinator to the preparation boundary;
4. introduce `ValuationPostingCoordinator`;
5. introduce the valuation lifecycle removal/reversal boundary;
6. introduce `CompositePostingResultCoordinator`;
7. change `PostingEngine` POST/REPOST ordering to use preparation;
8. implement explicit lifecycle result/error semantics;
9. add tests for deterministic failure and indeterminate persistence;
10. add tests for successful valuation reversal through compensating facts;
11. add integration tests covering register + valuation posting lifecycle;
12. reconcile architecture/API documentation after implementation.

No implementation should begin until the Concrete API Design defines the exact interfaces, result objects, error taxonomy, operation ordering, and persistence interactions.

---

# 25. Required Concrete API Design Decisions

Before implementation, Concrete API Design must explicitly settle:

### 25.1 `PostingResultPlan` structure

* generic representation;
* immutability mechanism;
* domain-plan ownership;
* validation of plan/domain compatibility.

### 25.2 `PostingResultCoordinator` result semantics

* return values;
* exception taxonomy;
* deterministic versus indeterminate outcomes.

### 25.3 Valuation removal API

* document identity versus richer removal context;
* exact `ValuationRemovalResult`;
* lookup of established valuation effect;
* representation of compensating facts.

### 25.4 Composite operation ordering

* exact register/valuation order for `prepare`;
* exact register/valuation order for `remove`;
* exact register/valuation order for `establish`;
* partial-failure semantics for every ordering point.

### 25.5 Repost failure after removal

The API must explicitly represent:

```text
old reversed
new not established
```

and:

```text
old reversed
new establishment indeterminate
```

as states distinct from:

```text
old unchanged
new not established
```

### 25.6 Event publication

The API must provide sufficient lifecycle information for `PostingEngine` to determine whether an event may be published.

---

# 26. Acceptance Criteria

The architecture is considered correctly implemented only when all of the following hold.

* `PostingEngine` remains valuation-agnostic.
* `RegisterPostingResultCoordinator` remains valuation-agnostic.
* `PostingResultPlan` is immutable and explicitly passed.
* No coordinator uses hidden pending-plan state.
* `ValuationEngine.prepare()` remains deterministic.
* Repost preparation occurs before removal.
* Failed preparation leaves existing state untouched.
* Valuation reversal does not mutate or delete historical facts.
* Valuation reversal uses compensating facts.
* Derived valuation state remains consistent with the reversal semantics.
* Composite coordination preserves domain failures.
* Persistence indeterminacy is surfaced.
* No distributed transaction or 2PC is introduced.
* `DocumentPosted` is emitted only after successful POST establishment.
* `DocumentReposted` is emitted only after successful REPOST lifecycle completion.
* Successful removal followed by establishment failure is represented explicitly.
* Successful removal followed by indeterminate establishment is represented explicitly.
* Register-only posting remains functional independently of valuation.
* Existing valuation behavior remains unchanged outside lifecycle integration.
* Integration tests demonstrate the complete register + valuation lifecycle.

---

# 27. Final Architectural Decision

WP-6 adopts a **generic posting-result lifecycle with explicit preparation, establishment, and removal**, implemented through composable domain coordinators.

The final architecture is:

```text
PostingEngine
     │
     ▼
Composite Posting Result Lifecycle
     │
     ├────────────── Register Result
     │
     └────────────── Valuation Result
                          │
                          ├── deterministic preparation
                          ├── immutable valuation plan
                          ├── establishment
                          └── compensating reversal
```

The central safety property is:

```text
prepare(new)
     ↓
only if successful
     ↓
remove(old)
     ↓
establish(new)
```

rather than:

```text
remove(old)
     ↓
establish(new)
```

The architecture deliberately does not promise atomicity that the underlying persistence mechanisms cannot provide.

The architecture also deliberately preserves the historical valuation model: **valuation reversal is a new compensating fact, not deletion of history**.

The remaining design work is therefore limited to the Concrete API Design of these already-approved architectural boundaries. Implementation begins only after that API design is reviewed and approved.
