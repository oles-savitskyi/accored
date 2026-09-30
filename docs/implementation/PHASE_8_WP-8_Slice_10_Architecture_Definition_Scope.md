# PHASE 8 — WP-8 Slice 10

**Documentation note:** Historical Slice 10 design baseline. Final repost lifecycle and recovery semantics are defined by Slices 10.6 and 10.7 and the final WP-8 reconciliation document.
# Valuation Lifecycle Completion, Repost Recovery and End-to-End Integration

**Status:** Approved for Concrete API Design
**Phase:** Phase 8 — Valuation
**Work Package:** WP-8 — Reversal / Repost / Recovery
**Slice:** 10
**Document type:** Architecture Definition / Scope — Final

---

## 1. Purpose

Slice 10 completes the lifecycle-level part of WP-8 after implementation of:

* immutable valuation reversal;
* logical valuation operation records;
* operation persistence;
* fact-level recovery;
* deterministic derived-state identities;
* derived-state rebuild and reconciliation.

The purpose of Slice 10 is to make the complete valuation lifecycle operationally recoverable and correctly integrated with the Posting lifecycle.

The slice covers:

1. deterministic Repost ordering;
2. stable logical lifecycle identity;
3. authoritative relationship between lifecycle and valuation operations;
4. ESTABLISH recovery;
5. Repost recovery;
6. integration of authoritative operation recovery with derived-state rebuild;
7. idempotent retry semantics;
8. failure and indeterminate outcome handling;
9. composite Posting integration;
10. event correctness;
11. preservation of historical valuation facts;
12. end-to-end recovery and rebuild equivalence.

No historical valuation fact may be mutated or deleted.

---

# 2. Architectural Decisions

The following decisions are final for Slice 10.

## 2.1 Repost ordering

The authoritative Repost lifecycle is:

```text
handler.post()
    ↓
new MovementSet
    ↓
movement validation
    ↓
prepare(new)
    ↓
remove(old)
    ↓
establish(new)
    ↓
DocumentReposted
```

Formally:

```text
PREPARE(new)
    →
REMOVE(old)
    →
ESTABLISH(new)
```

This order is mandatory.

### Rationale

`prepare()` is deterministic preflight and must not perform authoritative mutation.

A failed preparation must therefore leave the previously established state untouched:

```text
prepare(new) fails
    ⇒
remove(old) is not executed
```

This is especially important for valuation methods such as FIFO, where preparation may inspect the currently effective valuation state.

The prepared plan therefore represents the exact new valuation effect that is to be established after the old effect has been compensated.

`PostingEngine` must remain unaware of valuation-specific semantics.

---

## 2.2 Stable logical operation identity

A random operation identity created inside `ValuationCoordinator.establish()` is insufficient.

The architecture therefore introduces a **stable lifecycle operation identity owned by the Posting lifecycle boundary**.

The identity represents one logical posting lifecycle attempt.

Conceptually:

```text
PostingOperationIdentity
        │
        ├── valuation REMOVE operation identity
        │
        └── valuation ESTABLISH operation identity
```

The exact concrete API representation is deferred to Concrete API Design.

The essential architectural contract is:

* the identity is created outside the valuation persistence implementation;
* retries of the same logical lifecycle operation reuse the same identity;
* a new independent lifecycle operation receives a new identity;
* document identity alone is not an operation identity;
* valuation must never silently generate a new logical identity when retrying an existing operation;
* operation identity is excluded from semantic fingerprints.

This resolves the distinction between:

```text
same document
```

and

```text
same logical operation on that document
```

---

## 2.3 Repost identity model

A Repost is one lifecycle operation containing two independent authoritative valuation operations:

```text
Repost lifecycle
    │
    ├── REMOVE
    │     compensates the previous effective valuation
    │
    └── ESTABLISH
          establishes the prepared new valuation
```

The REMOVE and ESTABLISH operations have distinct valuation operation identities.

They are nevertheless associated with the same parent lifecycle operation.

Therefore:

* successful REMOVE must not be repeated merely because ESTABLISH later failed;
* successful ESTABLISH must not cause REMOVE to be repeated;
* retry logic must resume from the durable operation state;
* recovery must determine which lifecycle steps have already become authoritative.

The exact persisted relationship between parent lifecycle identity and child valuation operation identities is part of Concrete API Design.

---

# 3. Authoritative Operation Record

The valuation operation record remains the authoritative record of a logical valuation operation.

Its purpose is not merely auditing.

It is the durable basis for:

* idempotency;
* duplicate-operation detection;
* retry;
* recovery;
* reconstruction of incomplete authoritative state.

The following semantic rules remain mandatory.

### Same identity + same semantics

```text
append(operation)
+
existing identical operation
=
idempotent success
```

### Same identity + different semantics

```text
append(operation)
+
existing different operation
=
conflict / FAILURE
```

### `find(identity) == None`

This is authoritative `NOT_FOUND`.

No absence ambiguity is permitted at the semantic layer.

---

# 4. ESTABLISH Recovery

Slice 10 extends the current operation recovery model.

Recovery must support both:

```text
REMOVE
ESTABLISH
```

A recovery service that supports only REMOVE is insufficient for WP-8.

## 4.1 ESTABLISH recovery requirement

An ESTABLISH operation may reach an indeterminate state after:

1. operation record persistence;
2. valuation fact persistence;
3. result persistence;
4. derived-state update.

Recovery must be able to determine what authoritative state already exists and complete the operation without duplicating historical facts.

## 4.2 Recovery input

The operation record must contain, directly or through an authoritative recovery descriptor, enough information to reconstruct the expected ESTABLISH result.

A fingerprint alone is insufficient.

A fingerprint can establish semantic identity:

```text
same operation
```

but cannot reconstruct missing valuation facts.

Therefore the authoritative operation representation must preserve a deterministic recovery description sufficient to derive the expected facts again.

The exact representation is an API/persistence design decision, but the architectural requirement is:

> after process restart, ESTABLISH recovery must not depend on an in-memory `ValuationPlan` that may no longer exist.

---

# 5. Fact Persistence and Recovery

Valuation facts remain append-only historical facts.

Recovery uses reconciliation rather than mutation.

For an expected set of facts:

```text
expected facts
    ↓
authoritative fact persistence
    ↓
identity + semantic comparison
    ↓
missing facts appended
    ↓
existing identical facts accepted
    ↓
conflicting facts rejected
```

Repeated recovery must converge.

Formally:

```text
recover(operation)
+
recover(operation)
+
recover(operation)
...
=
same authoritative state
```

No recovery path may delete or modify an existing historical valuation fact.

---

# 6. REMOVE Semantics

REMOVE compensates currently effective historical valuation facts.

It does not mutate the original facts.

For each selected effective fact:

```text
historical valuation fact
        ↓
deterministic reversal fact
        ↓
effective state compensation
```

The original fact remains permanently persisted.

Repeated REMOVE recovery must never create a second reversal for the same historical target.

The persisted REMOVE operation must therefore preserve the canonical target fact identities.

The canonical ordering of target identities is part of the operation fingerprint and recovery semantics.

---

# 7. Repost Recovery

Repost recovery is lifecycle-aware.

The following states are possible.

### State A — preparation failed

```text
prepare(new) = FAILURE
```

Result:

```text
old valuation remains effective
```

No REMOVE is executed.

---

### State B — REMOVE failed deterministically

```text
prepare(new) = SUCCESS
remove(old) = FAILURE
```

Result:

```text
old valuation remains authoritative/effective
new valuation is not established
```

The prepared plan may be discarded.

---

### State C — REMOVE indeterminate

```text
prepare(new) = SUCCESS
remove(old) = INDETERMINATE
```

The system must not automatically assume either:

```text
REMOVE did not happen
```

or:

```text
REMOVE happened
```

Recovery must inspect the durable operation state.

---

### State D — REMOVE succeeded, ESTABLISH not started

```text
REMOVE = SUCCESS
ESTABLISH = not started
```

Recovery must continue with ESTABLISH.

REMOVE must not be repeated.

---

### State E — ESTABLISH indeterminate

```text
REMOVE = SUCCESS
ESTABLISH = INDETERMINATE
```

Recovery must reconcile the ESTABLISH operation.

REMOVE must not be executed again.

---

### State F — ESTABLISH succeeded

```text
REMOVE = SUCCESS
ESTABLISH = SUCCESS
```

The Repost is complete.

Only then may:

```text
DocumentReposted
```

be published.

---

# 8. Repost Retry Invariant

A retry of an interrupted Repost is not a new Repost.

It is recovery of the same logical lifecycle operation.

Therefore:

```text
same lifecycle identity
+
same operation semantics
=
same logical Repost
```

A retry must resume from durable state.

It must not blindly execute:

```text
remove()
```

again.

This requirement is one of the principal reasons stable logical operation identity is part of the architecture rather than merely an API convenience.

---

# 9. Prepared Plan Contract

`prepare()` remains a pure deterministic preflight operation.

It may inspect:

* current effective valuation state;
* currently available FIFO layers;
* movement identities;
* valuation inputs.

It may create an immutable in-memory plan.

It must not perform authoritative mutation.

The prepared plan is bound to the exact posting generation for which it was produced.

At minimum, its semantic validity is tied to:

* document identity;
* movement identities / movement generation;
* valuation operation identity where required.

An ESTABLISH operation must reject a plan prepared for another movement generation or another logical operation.

No coordinator may maintain an implicit pending plan keyed only by document identity.

The plan is an explicit hand-off between:

```text
prepare
```

and:

```text
establish
```

---

# 10. No FIFO Recalculation During ESTABLISH

Once a valid valuation plan has been prepared:

```text
prepare()
    ↓
ValuationPlan
    ↓
establish()
```

ESTABLISH must consume the prepared plan.

It must not rerun FIFO selection or otherwise recalculate valuation against potentially changed state.

This is required to preserve deterministic semantics between preflight and authoritative establishment.

---

# 11. Derived State

Slice #9 established deterministic derived-state reconstruction and reconciliation.

Slice #10 integrates that mechanism into lifecycle recovery.

Derived state is not authoritative.

Therefore:

```text
authoritative valuation facts
+
authoritative operation records
    ↓
derived-state rebuild/reconciliation
    ↓
current valuation results
    ↓
register/totals derived state
```

A missing or incomplete result must never cause historical valuation facts to be rewritten.

After successful recovery, derived state must be equivalent to the state produced by a clean complete execution.

---

# 12. Recovery and Rebuild Equivalence

The following invariant is mandatory:

```text
clean execution
```

and

```text
partial execution
→ recovery
→ derived-state rebuild
```

must produce semantically equivalent authoritative and derived state.

For equivalent inputs:

```text
facts(clean) == facts(recovered)
```

and:

```text
derived(clean) == derived(recovered)
```

up to explicitly non-authoritative persistence ordering where applicable.

---

# 13. Result Persistence

Valuation result persistence remains derived/rebuildable.

Result persistence failures must therefore not cause mutation or deletion of authoritative valuation facts.

The lifecycle distinguishes:

```text
authoritative operation/fact state
```

from:

```text
derived valuation result state
```

If authoritative operation and facts are complete but derived results are incomplete, recovery must rebuild/reconcile the derived state.

---

# 14. Failure and Indeterminate Semantics

The lifecycle retains three semantic outcomes:

```text
SUCCESS
FAILURE
INDETERMINATE
```

### FAILURE

The system knows that the requested authoritative transition did not complete.

### INDETERMINATE

The system cannot safely determine whether the authoritative transition completed.

An indeterminate result must never be converted into deterministic failure merely because the original persistence call raised an exception.

Recovery is the mechanism for resolving indeterminate state.

---

# 15. Operation Ordering

The authoritative ordering is:

### Initial Post

```text
prepare
    ↓
ESTABLISH
```

### Unpost

```text
REMOVE
```

### Repost

```text
prepare(new)
    ↓
REMOVE(old)
    ↓
ESTABLISH(new)
```

This ordering is consistent across Posting and Valuation boundaries.

---

# 16. Composite Posting Boundary

The composite Posting coordinator remains transaction-neutral.

It orchestrates independent participants:

```text
Register
Valuation
...
```

It does not introduce an artificial distributed transaction.

Each participant retains responsibility for:

* authoritative persistence;
* idempotency;
* recovery;
* indeterminate outcomes;
* derived-state reconciliation.

The composite coordinator is responsible only for ordered lifecycle orchestration and outcome propagation.

---

# 17. Event Semantics

Posting events are published only after the corresponding lifecycle operation is known to have completed successfully.

Therefore:

### Post

```text
ESTABLISH SUCCESS
    ↓
DocumentPosted
```

### Unpost

```text
REMOVE SUCCESS
    ↓
DocumentUnposted
```

### Repost

```text
REMOVE SUCCESS
+
ESTABLISH SUCCESS
    ↓
DocumentReposted
```

No event is published for:

* FAILURE;
* INDETERMINATE;
* incomplete recovery.

A retry that discovers an already successfully completed logical operation may return SUCCESS without publishing a duplicate lifecycle event.

Event deduplication semantics are part of the lifecycle operation identity contract.

---

# 18. Historical Immutability

The following invariant is absolute:

> No historical valuation fact may be mutated or deleted.

This applies to:

* normal REMOVE;
* repeated REMOVE;
* Repost;
* failed Repost;
* indeterminate Repost;
* ESTABLISH recovery;
* REMOVE recovery;
* derived-state rebuild;
* repeated recovery.

The only authoritative modification permitted to valuation fact persistence is appending a new fact.

---

# 19. Idempotency

Slice 10 must demonstrate idempotency at three levels.

## 19.1 Operation level

Repeated append of the same operation record is idempotent.

## 19.2 Fact level

Repeated recovery of the same expected fact set is idempotent.

## 19.3 Lifecycle level

Retrying the same logical Post/Unpost/Repost operation must not duplicate its authoritative effects.

These are separate guarantees and must not be conflated.

---

# 20. Duplicate Logical Operations

Two different lifecycle operation identities represent two different logical operations even if:

```text
document identity
```

is identical.

Therefore:

```text
same document + new operation identity
```

is not automatically a duplicate.

Conversely:

```text
same operation identity + different semantics
```

is a conflict.

This prevents document identity from being incorrectly used as an idempotency key.

---

# 21. Concurrent / Conflicting Operations

The architecture must reject conflicting reuse of an existing operation identity.

It must also prevent a prepared plan from being applied to a different logical operation.

Concurrency coordination beyond operation-record conflict detection is outside the scope of Slice 10 unless required by the existing persistence contract.

No in-memory lock is considered an authoritative concurrency mechanism.

---

# 22. Scope of Implementation

Slice 10 includes:

### Lifecycle identity

* introduce stable logical lifecycle operation identity;
* propagate it through the relevant Posting/Valuation boundaries;
* preserve it across retry/recovery.

### Operation model

* establish explicit parent/child relationship between lifecycle and valuation operations;
* support REMOVE and ESTABLISH operation recovery;
* preserve immutable operation records.

### ESTABLISH recovery

* reconstruct expected valuation facts from durable recovery information;
* reconcile authoritative facts;
* reconcile result/derived state;
* make repeated recovery convergent.

### Repost

* enforce `prepare → remove → establish`;
* prevent remove after preparation failure;
* prevent repeated remove during establish recovery;
* resume interrupted lifecycle from durable operation state.

### Derived state

* integrate Slice #9 rebuild/reconciliation with lifecycle recovery;
* verify clean-execution/recovery equivalence.

### Posting integration

* update composite coordinator boundaries as required;
* keep PostingEngine free of valuation-specific logic;
* preserve opaque PostingResultPlan semantics.

### Events

* ensure events are emitted only after successful completion;
* prevent duplicate lifecycle events on idempotent retries.

---

# 23. Explicit Non-Goals

Slice 10 does not introduce:

* distributed transactions;
* two-phase commit;
* rollback of persisted historical valuation facts;
* mutation of historical valuation facts;
* deletion of valuation facts;
* implicit in-memory pending-operation registries;
* document identity as a substitute for logical operation identity;
* valuation-specific branching inside `PostingEngine`;
* recalculation of FIFO during ESTABLISH;
* a second independent recovery architecture for ESTABLISH.

---

# 24. Required Test Matrix

Implementation is not complete until the following scenarios are covered.

## Establish

1. successful ESTABLISH;
2. deterministic fact persistence failure;
3. indeterminate fact persistence;
4. deterministic result persistence failure;
5. indeterminate result persistence;
6. recovery after operation record persistence succeeds;
7. recovery after partial fact persistence;
8. recovery after complete facts but incomplete results;
9. repeated ESTABLISH recovery;
10. conflicting operation identity.

## Remove

11. successful REMOVE;
12. deterministic REMOVE failure;
13. indeterminate REMOVE;
14. repeated REMOVE recovery;
15. duplicate reversal prevention;
16. canonical target ordering.

## Repost

17. preparation failure leaves old state untouched;
18. successful prepare followed by REMOVE failure;
19. indeterminate REMOVE;
20. successful REMOVE followed by ESTABLISH failure;
21. indeterminate ESTABLISH;
22. recovery after REMOVE success;
23. recovery after ESTABLISH indeterminate;
24. repeated Repost recovery;
25. no repeated REMOVE after successful REMOVE;
26. no duplicate ESTABLISH facts;
27. final `DocumentReposted` only after complete success.

## Plan integrity

28. plan/document mismatch;
29. plan/movement-generation mismatch;
30. plan/logical-operation mismatch;
31. plan reuse for another Repost generation rejected.

## Derived state

32. rebuild after incomplete result persistence;
33. rebuild after interrupted Repost;
34. clean execution versus recovery equivalence;
35. stale derived movement reconciliation.

## Composite Posting

36. Register + Valuation successful lifecycle;
37. participant failure propagation;
38. participant indeterminate propagation;
39. no valuation-specific logic in PostingEngine;
40. event publication only after complete lifecycle success.

---

# 25. Acceptance Criteria

Slice 10 is architecturally complete when all of the following are true.

### Repost

* [ ] Repost executes `prepare(new) → remove(old) → establish(new)`.
* [ ] Failed deterministic preparation leaves the old successful state untouched.
* [ ] Preparation performs no authoritative mutation.
* [ ] ESTABLISH consumes the prepared plan without rerunning FIFO.
* [ ] REMOVE is not repeated after successful REMOVE.

### Identity

* [ ] Logical lifecycle identity is stable across retries.
* [ ] Document identity is not used as the lifecycle idempotency key.
* [ ] REMOVE and ESTABLISH have distinct valuation operation identities.
* [ ] Their relationship to the parent lifecycle operation is durable.
* [ ] Same identity + same semantics is idempotent.
* [ ] Same identity + different semantics is a conflict.

### Recovery

* [ ] REMOVE recovery is supported.
* [ ] ESTABLISH recovery is supported.
* [ ] Recovery works after process restart without relying on an in-memory plan.
* [ ] Repeated recovery converges.
* [ ] Recovery never mutates or deletes historical valuation facts.

### Derived state

* [ ] Incomplete derived state can be rebuilt.
* [ ] Recovery integrates with Slice #9 reconciliation.
* [ ] Clean execution and recovery produce equivalent state.

### Posting

* [ ] `PostingResultPlan` remains opaque to `PostingEngine`.
* [ ] No coordinator stores an implicit pending plan keyed only by document identity.
* [ ] Composite orchestration remains transaction-neutral.
* [ ] PostingEngine contains no valuation-specific recovery logic.

### Events

* [ ] `DocumentPosted` is emitted only after successful Post.
* [ ] `DocumentUnposted` is emitted only after successful Unpost.
* [ ] `DocumentReposted` is emitted only after successful REMOVE + ESTABLISH.
* [ ] Recovery/retry cannot emit duplicate lifecycle events for the same completed logical operation.

### Quality

* [ ] Unit tests cover the complete failure matrix.
* [ ] Integration tests cover Post → Unpost → Repost lifecycle.
* [ ] Recovery tests cover persistence failure and indeterminate states.
* [ ] `pytest` passes.
* [ ] `ruff` passes.
* [ ] `black --check` passes.
* [ ] `mypy` passes.
* [ ] Documentation is reconciled with the final implementation.

---

# 26. Architectural Consequences

The selected architecture deliberately makes one distinction explicit:

```text
Lifecycle identity
        ≠
Document identity
        ≠
Valuation fact identity
        ≠
Valuation operation identity
```

These identities serve different purposes.

### Document identity

Identifies the business document.

### Lifecycle operation identity

Identifies one logical Post/Unpost/Repost attempt and provides the stable retry boundary.

### Valuation operation identity

Identifies one authoritative valuation transition, such as REMOVE or ESTABLISH.

### Valuation fact identity

Identifies one immutable historical valuation fact.

This separation is required for correct recovery.

---

# 27. Final Architectural Model

The resulting lifecycle is:

```text
                       Posting Lifecycle Identity
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     Repost      │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
              prepare(new)                lifecycle state
                    │
                    ▼
             immutable Plan
                    │
                    ▼
              REMOVE operation
                    │
                    ▼
        immutable reversal facts
                    │
                    ▼
            effective old state
             is compensated
                    │
                    ▼
            ESTABLISH operation
                    │
                    ▼
          immutable valuation facts
                    │
                    ▼
           derived-state reconcile
                    │
                    ▼
            DocumentReposted
```

For recovery:

```text
Authoritative Operation Record
            │
            ├── REMOVE
            │     ↓
            │  expected reversal facts
            │
            └── ESTABLISH
                  ↓
              recovery descriptor
                  ↓
              expected facts
                  ↓
          fact reconciliation
                  ↓
          derived-state rebuild
```

The key invariant is:

```text
authoritative history is append-only
```

while:

```text
current effective state
```

is reconstructed from that immutable history.

---

# 28. Transition to Concrete API Design

With this document approved, the next step is **Concrete API Design**.

The API Design must define, without reopening the architectural decisions above:

1. concrete `PostingOperationIdentity` representation;
2. lifecycle identity propagation;
3. concrete parent/child operation identity model;
4. changes to Posting coordinator protocols;
5. concrete `ValuationPlan` identity binding;
6. durable ESTABLISH recovery descriptor;
7. operation-record state/recovery representation;
8. concrete recovery APIs;
9. Repost retry API;
10. event idempotency handling;
11. persistence contracts;
12. exact test fixtures and failure-injection interfaces.

The Concrete API Design must not change the following architectural decisions:

```text
Repost:
prepare → remove → establish

Historical valuation facts:
append-only

Recovery:
durable and convergent

Operation identity:
stable across retry

ESTABLISH:
recoverable after process restart

PostingEngine:
valuation-agnostic
```

**Status after this document:** Architecture approved; ready for Concrete API Design.
