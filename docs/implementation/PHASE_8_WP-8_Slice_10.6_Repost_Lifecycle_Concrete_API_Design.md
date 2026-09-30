# WP-8 Slice 10.6 — Repost Lifecycle

## Concrete API Design

**Status:** Approved for Implementation

---

## 1. Purpose

Slice 10.6 completes the successful Repost lifecycle across the generic Posting layer and the Valuation layer.

The authoritative lifecycle order is:

```text
prepare → remove → establish
```

The lifecycle is correlated by one parent:

```python
PostingOperationIdentity
```

Valuation operations receive deterministic child identities derived from that parent:

```text
Posting P
 ├── Valuation REMOVE R
 └── Valuation ESTABLISH E
```

The lifecycle remains transaction-neutral.

No cross-subsystem transaction, rollback protocol, persistent Posting operation record, or mutable Posting lifecycle state is introduced.

---

# 2. Existing Public Posting Contract

The existing public engine API remains:

```python
class PostingEngine:
    def post(self, document: ObjectInstance) -> PostingResult:
        ...

    def unpost(self, document: ObjectInstance) -> PostingResult:
        ...

    def repost(self, document: ObjectInstance) -> PostingResult:
        ...
```

No new public method is introduced for Repost.

`repost()` remains the public entry point.

---

# 3. Parent Operation Identity

`PostingEngine.repost()` creates exactly one:

```python
PostingOperationIdentity
```

at the beginning of the lifecycle.

Conceptually:

```python
operation_identity = self._operation_identity_factory.new()
```

The same identity is passed through:

```text
prepare(P)
remove(P)
establish(P)
```

The identity is not regenerated between phases.

---

# 4. Repost Lifecycle

The implementation MUST execute:

```text
resolve handler
    ↓
produce replacement MovementSet
    ↓
validate MovementSet
    ↓
prepare(P, replacement)
    ↓
remove(P)
    ↓
establish(P, prepared plan)
```

The establishment phase MUST NOT execute if removal did not complete successfully.

---

# 5. Preparation Must Know This Is a Replacement

A critical distinction exists between:

```text
post(document)
```

and:

```text
repost(document)
```

Both prepare a plan for the same document type, but Repost preparation must use:

```text
ProjectedValuationPreparationState
```

rather than the authoritative current state.

Therefore the preparation boundary must explicitly carry:

```python
replacement_document_identity: Identifier | None
```

This is generic lifecycle context, not valuation-specific semantics.

---

# 6. Posting Preparation Context

Introduce an immutable generic preparation context:

```python
@dataclass(frozen=True, slots=True)
class PostingPreparationContext:
    operation_identity: PostingOperationIdentity
    replacement_document_identity: Identifier | None = None
```

Semantics:

### Normal Post

```python
PostingPreparationContext(
    operation_identity=P,
    replacement_document_identity=None,
)
```

### Repost

```python
PostingPreparationContext(
    operation_identity=P,
    replacement_document_identity=document.identity,
)
```

The context does not contain valuation concepts.

---

# 7. PostingResultParticipant API

The existing participant contract is extended only with the generic preparation context:

```python
class PostingResultParticipant(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        context: PostingPreparationContext,
    ) -> object:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

`establish()` and `remove()` remain unchanged.

The context is deliberately generic so Register and other Posting participants can ignore:

```python
context.replacement_document_identity
```

when it has no semantic meaning for them.

---

# 8. PostingResultCoordinator API

The generic coordinator receives the preparation context:

```python
class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        context: PostingPreparationContext,
    ) -> PostingResultPlan:
        ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...

    def remove(
        self,
        document: ObjectInstance,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

No valuation-specific type appears in the generic Posting coordinator.

---

# 9. CompositePostingResultCoordinator

`CompositePostingResultCoordinator.prepare()` forwards the same immutable context to every participant:

```python
return PostingResultPlan(
    participant_plans=tuple(
        participant.prepare(
            document,
            movement_set,
            context,
        )
        for participant in self._participants
    )
)
```

The participant order remains the configured order.

No transaction semantics are added.

---

# 10. PostingEngine.post()

Normal Post constructs:

```python
preparation_context = PostingPreparationContext(
    operation_identity=operation_identity,
)
```

and calls:

```python
plan = self._coordinator.prepare(
    document,
    movement_set,
    preparation_context,
)
```

The effective semantics are unchanged:

```text
post
 ↓
authoritative preparation state
 ↓
establish
```

---

# 11. PostingEngine.repost()

Repost constructs:

```python
preparation_context = PostingPreparationContext(
    operation_identity=operation_identity,
    replacement_document_identity=document.identity,
)
```

Then:

```python
plan = self._coordinator.prepare(
    document,
    movement_set,
    preparation_context,
)
```

followed by:

```python
removal = self._coordinator.remove(
    document,
    operation_identity,
)
```

and only after successful removal:

```python
establishment = self._coordinator.establish(
    document,
    movement_set,
    plan,
    operation_identity,
)
```

---

# 12. Exact Repost Control Flow

The resulting control flow is:

```text
PostingEngine.repost()
        │
        ▼
create PostingOperationIdentity P
        │
        ▼
resolve handler
        │
        ▼
build replacement MovementSet
        │
        ▼
validate MovementSet
        │
        ▼
prepare(
    operation=P,
    replacement_document=document.identity
)
        │
        ▼
ValuationPostingCoordinator
        │
        ▼
ProjectedValuationPreparationState
        │
        ▼
ValuationPlan
        │
        ▼
remove(P)
        │
        ├── FAILURE ────────> return
        │
        ├── INDETERMINATE ──> return
        │
        ▼
establish(P, plan)
        │
        ├── FAILURE ────────> return
        │
        ├── INDETERMINATE ──> return
        │
        ▼
DocumentReposted
```

---

# 13. ValuationPostingCoordinator

The valuation adapter changes its preparation signature to consume the generic Posting preparation context:

```python
class ValuationPostingCoordinator:
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        context: PostingPreparationContext,
    ) -> ValuationPlan:
        ...
```

The coordinator extracts:

```python
context.operation_identity
context.replacement_document_identity
```

and constructs the already-approved:

```python
ValuationPreparationContext
```

---

# 14. ValuationPreparationContext

The existing valuation context remains:

```python
@dataclass(frozen=True, slots=True)
class ValuationPreparationContext:
    operation_identity: ValuationOperationIdentity
    replacement_document_identity: Identifier | None = None
```

For normal Post:

```text
replacement_document_identity = None
```

For Repost:

```text
replacement_document_identity = document.identity
```

The Posting layer does not construct this valuation-specific context.

`ValuationPostingCoordinator` is responsible for the translation.

---

# 15. Valuation State Selection

`ValuationPostingCoordinator` selects the preparation state.

### Normal Post

```text
replacement_document_identity == None
        ↓
state_factory.authoritative()
```

### Repost

```text
replacement_document_identity != None
        ↓
state_factory.for_replacement(document.identity)
```

No mutable state is installed into `ValuationEngine`.

---

# 16. ValuationEngine API

The existing deterministic preparation API remains:

```python
class ValuationEngine:
    def prepare(
        self,
        movement_set: MovementSet,
        context: ValuationPreparationContext,
    ) -> ValuationPlan:
        ...
```

The engine uses the preparation context to derive deterministic opaque planning identities.

It does not itself decide whether the state is authoritative or projected.

The selected `ValuationPreparationState` remains a composition dependency of the engine.

---

# 17. Projected State Semantics

For Repost:

```text
ProjectedState =
    AuthoritativeEffectiveState
    − effective valuation effect(old document)
```

Projection is read-only.

It does not:

* append facts;
* delete facts;
* create reversal facts;
* modify balances;
* modify CostMovements;
* modify operation records.

It exists only for deterministic preparation.

---

# 18. Child Valuation Operation Identities

`ValuationPostingCoordinator` MUST NOT construct child identities using string interpolation directly.

The existing deterministic identity factory is used:

```python
PostingParticipantOperationIdentityFactory
```

with the existing concrete implementation:

```python
DefaultPostingParticipantOperationIdentityFactory
```

The valuation participant derives:

```python
remove_identity = factory.derive(
    operation_identity,
    "valuation",
    "remove",
)
```

and:

```python
establish_identity = factory.derive(
    operation_identity,
    "valuation",
    "establish",
)
```

The resulting strings are wrapped as:

```python
ValuationOperationIdentity(...)
```

---

# 19. Identity Semantics

For one parent:

```text
P = PostingOperationIdentity(...)
```

the child identities are deterministic:

```text
R = derive(P, "valuation", "remove")
E = derive(P, "valuation", "establish")
```

Therefore:

```text
same P
    → same R
    → same E
```

and:

```text
different P
    → different R/E
```

The semantic fingerprint of valuation operations remains independent from this persistence identity derivation.

---

# 20. Valuation Remove

The existing lifecycle contract remains:

```python
self._lifecycle.remove(
    document.identity,
    valuation_remove_identity,
)
```

The removal identity is derived from the parent Posting identity.

No new removal API is introduced.

---

# 21. Valuation Establish

The existing lifecycle contract remains:

```python
self._lifecycle.establish(
    plan,
    valuation_establish_identity,
)
```

The establishment identity is derived from the same parent Posting identity.

The prepared plan is the plan generated before removal against the projected preparation state.

---

# 22. Critical Plan Ownership Rule

The `ValuationPlan` produced during:

```text
prepare
```

belongs to the Repost lifecycle.

After successful preparation:

```text
plan
```

is immutable and becomes the input to the later establishment phase.

The plan MUST NOT be regenerated after removal.

Therefore:

```text
prepare
    ↓
Plan A
    ↓
remove
    ↓
establish(Plan A)
```

and NOT:

```text
prepare
    ↓
remove
    ↓
prepare again
    ↓
establish
```

---

# 23. Why the Plan Is Prepared Before Remove

The projected state makes the preparation semantically equivalent to preparing against:

```text
current state - old document effect
```

without physically modifying persistence.

This ensures:

* FIFO sees the correct available layers;
* old layers can be reused by the replacement;
* old consumptions are virtually restored;
* no historical mutation is needed during preparation.

---

# 24. Remove Failure

If:

```text
prepare == SUCCESS
remove == FAILURE
```

then:

```text
establish
```

MUST NOT execute.

The prepared plan is discarded.

No event is emitted.

Result:

```text
PostingOutcome.FAILURE
```

---

# 25. Remove Indeterminate

If:

```text
prepare == SUCCESS
remove == INDETERMINATE
```

then:

```text
establish
```

MUST NOT execute.

Result:

```text
PostingOutcome.INDETERMINATE
```

No `DocumentReposted` event is emitted.

Recovery of this state belongs to Slice 10.7.

---

# 26. Establish Failure

If:

```text
prepare == SUCCESS
remove == SUCCESS
establish == FAILURE
```

then the Posting result is:

```text
PostingOutcome.FAILURE
```

The REMOVE operation is not rolled back.

Historical valuation facts remain immutable.

No `DocumentReposted` event is emitted.

Recovery belongs to Slice 10.7.

---

# 27. Establish Indeterminate

If:

```text
prepare == SUCCESS
remove == SUCCESS
establish == INDETERMINATE
```

then:

```text
PostingOutcome.INDETERMINATE
```

is returned.

No `DocumentReposted` event is emitted.

No rollback of historical valuation facts occurs.

---

# 28. Successful Repost

Only this sequence is successful:

```text
prepare  → SUCCESS
remove   → SUCCESS
establish → SUCCESS
```

Then:

```python
DocumentReposted(document.identity)
```

is published.

The final result is:

```python
PostingResult.success()
```

---

# 29. Event Boundary

`PostingEngine._result_from_lifecycle()` remains the single event publication boundary.

For Repost:

```python
return self._result_from_lifecycle(
    establishment,
    DocumentReposted(document.identity),
)
```

The event is published only if the final lifecycle result is `SUCCESS`.

Therefore:

```text
prepare failure
    → no event

remove failure
    → no event

remove indeterminate
    → no event

establish failure
    → no event

establish indeterminate
    → no event

all success
    → DocumentReposted
```

No separate event coordinator is introduced.

---

# 30. Register Participant

The Register participant receives:

```python
PostingPreparationContext
```

but ignores:

```python
replacement_document_identity
```

because Register semantics are independent from valuation projection.

Its preparation remains based on:

```python
movement_set
```

and existing register configuration.

No valuation-specific logic is introduced into Register.

---

# 31. Composite Participant Order

`CompositePostingResultCoordinator` preserves configured participant order.

No new transaction semantics are introduced.

For each lifecycle phase:

```text
prepare
establish
remove
```

participants are called in the configured order.

A participant failure stops the current phase.

The coordinator does NOT compensate already-completed participants.

---

# 32. Standard Composition

Standard composition must wire:

```text
ValuationPostingCoordinator
```

with:

* `ValuationEngine`;
* `ValuationLifecycleCoordinator`;
* `ValuationPreparationStateFactory`;
* `PostingParticipantOperationIdentityFactory`.

The same deterministic child identity factory abstraction is used for valuation REMOVE and ESTABLISH.

The Standard composition must not implement valuation lifecycle semantics itself.

---

# 33. No New Posting Persistence

Slice 10.6 does NOT introduce:

```text
PostingOperationRecord
PostingOperationPersistence
PostingLifecycleState
```

The authoritative operation records remain valuation-level records:

```text
ValuationOperationRecord(REMOVE)
ValuationOperationRecord(ESTABLISH)
```

The Posting identity is only the parent lifecycle correlation/idempotency identity.

---

# 34. No Cross-Subsystem Transaction

The following is explicitly NOT assumed:

```text
Register REMOVE
+
Valuation REMOVE
+
Register ESTABLISH
+
Valuation ESTABLISH
```

as one atomic transaction.

If one participant succeeds and a later participant fails, the already-completed effects are not rolled back by Slice 10.6.

Recovery semantics are addressed by later Slice 10.7.

---

# 35. Repost and Operation Records

A successful Repost produces:

```text
PostingOperationIdentity P

ValuationOperationRecord:
    identity = R
    type = REMOVE
    document = D

ValuationOperationRecord:
    identity = E
    type = ESTABLISH
    document = D
```

The two records remain immutable.

No single mutable record representing the entire Posting lifecycle is introduced.

---

# 36. Idempotency Boundary

The public `PostingEngine.repost()` continues to create a fresh parent identity for each new invocation.

Therefore:

```text
repost(document)
```

is a new logical Posting lifecycle.

Recovery of an already-started lifecycle does NOT invoke `repost()` again.

It is handled by the recovery mechanisms introduced in Slice 10.7.

---

# 37. Tests — Posting Engine

Add/extend tests for:

### Successful repost

```text
prepare → establish/remove/establish success
```

with final:

```text
SUCCESS
```

and exactly one:

```text
DocumentReposted
```

---

### Prepare failure

Verify:

```text
prepare = FAILURE
remove not called
establish not called
event not published
```

---

### Remove failure

Verify:

```text
prepare = SUCCESS
remove = FAILURE
establish not called
event not published
```

---

### Remove indeterminate

Verify:

```text
prepare = SUCCESS
remove = INDETERMINATE
establish not called
event not published
```

---

### Establish failure

Verify:

```text
prepare = SUCCESS
remove = SUCCESS
establish = FAILURE
event not published
```

---

### Establish indeterminate

Verify:

```text
prepare = SUCCESS
remove = SUCCESS
establish = INDETERMINATE
event not published
```

---

# 38. Tests — Preparation Context

Verify:

### Normal Post

```python
replacement_document_identity is None
```

### Repost

```python
replacement_document_identity == document.identity
```

Verify Register ignores the field.

Verify Valuation uses the field.

---

# 39. Tests — Projected Preparation

Repost preparation must verify:

1. old document layer is virtually removed;
2. old document consumptions are virtually restored;
3. new consumption can reuse the old layer where semantics permit;
4. preparation does not mutate persistence;
5. FIFO ordering remains deterministic;
6. external dependency conflicts still fail using existing valuation validation;
7. the plan is generated before REMOVE.

---

# 40. Tests — Child Identity

For one:

```python
PostingOperationIdentity("P")
```

verify:

```text
derive(P, valuation, remove)
```

is stable.

Verify:

```text
derive(P, valuation, establish)
```

is stable.

Verify:

```text
remove_identity != establish_identity
```

Verify different Posting identities produce different child identities.

Verify no direct random identity generation occurs in the valuation Posting adapter.

---

# 41. Tests — Plan Reuse

Verify the exact plan object returned from:

```text
prepare
```

is passed to:

```text
establish
```

without a second preparation call.

This protects the critical:

```text
prepare → remove → establish
```

contract.

---

# 42. Tests — Valuation Lifecycle

Verify successful Repost creates:

```text
REMOVE operation record
ESTABLISH operation record
```

with:

```text
REMOVE.identity == derive(P, valuation, remove)
ESTABLISH.identity == derive(P, valuation, establish)
```

Verify both records refer to the same document.

---

# 43. Tests — Historical Immutability

After successful Repost:

```text
old valuation facts remain immutable
```

The old effect is compensated through reversal semantics.

The old facts are not:

* edited;
* deleted;
* replaced.

---

# 44. Tests — Derived State

Successful Repost must leave derived valuation state equivalent to:

```text
old effective state
    − old document effect
    + new document effect
```

using the existing Slice #9 rebuild semantics.

Slice 10.6 does not introduce a new derived-state algorithm.

---

# 45. Regression Tests

The following existing areas must remain green:

* normal Posting;
* Unpost;
* valuation Establish;
* valuation Remove;
* Slice 9 rebuild;
* Slice 10.1 identity propagation;
* Slice 10.2 deterministic preparation;
* Slice 10.3 projected preparation;
* Slice 10.4 ESTABLISH recovery;
* Slice 10.5 unified recovery;
* Standard Inventory composition.

---

# 46. Explicitly Out of Scope

Slice 10.6 does NOT implement:

* Posting recovery;
* Repost recovery;
* Posting operation persistence;
* mutable Posting lifecycle state;
* event persistence;
* event idempotency storage;
* cross-subsystem transactions;
* rollback of successful REMOVE;
* changes to `DefaultValuationRebuilder`;
* new valuation fact semantics;
* new reversal semantics.

These remain outside Slice 10.6.

---

# 47. Acceptance Criteria

Slice 10.6 is complete when:

1. `PostingEngine.repost()` uses one parent `PostingOperationIdentity`.
2. Repost order is exactly `prepare → remove → establish`.
3. Repost preparation explicitly identifies the document as a replacement.
4. Normal Post continues to use authoritative preparation state.
5. Repost uses projected preparation state.
6. Prepared plan is not regenerated after REMOVE.
7. Valuation REMOVE identity is deterministic.
8. Valuation ESTABLISH identity is deterministic.
9. REMOVE and ESTABLISH identities are distinct.
10. REMOVE failure prevents ESTABLISH.
11. REMOVE indeterminate prevents ESTABLISH.
12. ESTABLISH failure does not rollback REMOVE.
13. ESTABLISH indeterminate does not rollback REMOVE.
14. `DocumentReposted` is emitted only after complete lifecycle success.
15. Register remains valuation-agnostic.
16. No Posting operation persistence is introduced.
17. No mutable Posting lifecycle state is introduced.
18. Historical valuation facts remain immutable.
19. Existing Slice #9 rebuild remains the sole derived-state rebuild.
20. All existing Slice 10.1–10.5 behavior remains regression-free.

---

# 48. Quality Gate

Implementation is accepted only after:

```bash
pytest -q
ruff check .
black --check .
mypy src
```

all pass in the project's Python 3.14 environment.

---

# 49. Final Lifecycle Architecture

After Slice 10.6:

```text
                    PostingOperationIdentity P
                              │
                              ▼
                    ┌───────────────────┐
                    │     PREPARE       │
                    │                   │
                    │ replacement=D    │
                    └─────────┬─────────┘
                              │
                              ▼
                 projected valuation state
                              │
                              ▼
                       ValuationPlan
                              │
                              ▼
                    ┌───────────────────┐
                    │      REMOVE       │
                    │                   │
                    │ R = derive(P,     │
                    │   valuation,      │
                    │   remove)         │
                    └─────────┬─────────┘
                              │
                         SUCCESS
                              │
                              ▼
                    ┌───────────────────┐
                    │    ESTABLISH      │
                    │                   │
                    │ E = derive(P,     │
                    │   valuation,      │
                    │   establish)     │
                    └─────────┬─────────┘
                              │
                         SUCCESS
                              │
                              ▼
                     DocumentReposted
```

The essential invariant is:

> **Repost prepares the replacement against a read-only projection that excludes the old document's effective valuation effect, then removes the old effect and establishes the already-prepared replacement plan.**

This preserves deterministic preparation, immutable historical valuation facts, explicit operation identities, and the transaction-neutral Posting architecture.
