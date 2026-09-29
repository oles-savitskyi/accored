# Phase 8 — WP-8

# Reversal / Repost / Recovery

## Amended Architecture Definition / Scope

**Status:** Architecture Definition — Amended
**Stage:** Architecture Review completed — Approved with Required Amendments
**Implementation:** In progress — WP-8 Slice 7 (Fact Recovery / Reconciliation) complete
**Predecessor:** Phase 8 WP-7 — Standard Inventory Composition
**Baseline commit:** `0d94800` — `feat(standard): complete Phase 8 WP-7 inventory composition`

---

## Implementation Reconciliation — WP-8 Slice 7

The current implementation has completed the Fact Recovery / Reconciliation slice defined by the approved WP-8 design.

Implemented in `accore.platform.valuation`:

* `ValuationFactRecoveryOutcome`;
* `ValuationFactRecoveryResult`;
* `ValuationFactRecoveryService`;
* authoritative `ValuationFactPersistence.find(identity)` reconciliation;
* partial fact recovery after an indeterminate append;
* semantic conflict detection during reconciliation;
* append-only recovery of only missing deterministic facts;
* deterministic fact identities for lifecycle facts;
* ESTABLISH integration with operation registration before fact persistence;
* REMOVE integration using the target set captured before operation registration;
* recovery integration tests for ESTABLISH and REMOVE partial fact persistence.

The following WP-8 areas remain later implementation slices and are therefore intentionally not claimed as complete by this reconciliation:

* derived-state recovery/rebuild;
* explicit operation-level `recover(...)`;
* full repost recovery semantics;
* composite posting recovery;
* the remaining full WP-8 acceptance/test matrix.

The approved architecture remains unchanged.

---

# 1. Purpose

WP-8 defines and implements immutable reversal semantics, deterministic repost semantics, and recovery of incomplete or indeterminate valuation lifecycle operations.

The objective is to ensure that valuation history remains immutable and authoritative while effective valuation state and all derived valuation results remain reconstructible.

The architectural model is:

```text
Immutable Valuation History
          ↓
Semantic Effective State
          ↓
Rebuildable Derived State
```

WP-8 does not introduce a new valuation architecture.

It formalizes and extends the existing valuation lifecycle so that:

* unpost is represented by immutable reversal facts;
* repost removes the old effective valuation before preparing the new valuation;
* repeated logical operations are idempotent;
* persistence failures and indeterminate outcomes can be reconciled;
* incomplete derived results can be rebuilt;
* no historical valuation fact is mutated or deleted.

---

# 2. Architectural Baseline

WP-8 builds on the architecture established by WP-6 and WP-7.

The existing boundaries remain authoritative:

```text
PostingEngine
      │
      ▼
PostingResultCoordinator
      │
      ▼
CompositePostingResultCoordinator
      │
      ├── RegisterPostingResultCoordinator
      │
      └── ValuationPostingCoordinator
              │
              ├── ValuationEngine
              └── ValuationLifecycleCoordinator
```

Generic valuation remains in:

```text
accore.platform.valuation
```

Standard inventory composition remains in:

```text
standard.valuation
standard.bootstrap
```

WP-8 must not introduce:

* `PostingEngine → ValuationEngine` dependency;
* Register → Valuation dependency;
* Valuation → Standard dependency;
* Standard-specific valuation semantics in generic valuation;
* a distributed transaction abstraction between Register and Valuation.

---

# 3. Core Architectural Principle

The authoritative source of valuation state is the immutable valuation fact history.

```text
ValuationFact history
        │
        ▼
effective valuation interpretation
        │
        ▼
CostMovement
        │
        ▼
CostTotals / CostBalance
```

The layers have different authority:

## 3.1 Authoritative

```text
ValuationFact
ValuationLayer
ValuationConsumption
ValuationAdjustment
ValuationAllocation
ValuationReversal
```

Historical valuation facts are append-only.

## 3.2 Derived

```text
CostMovement
CostTotals
CostBalance
materialized valuation results
```

Derived state may be replaced, rebuilt, or reconstructed.

Therefore:

```text
Historical facts = immutable + authoritative

Derived state = rebuildable + replaceable
```

---

# 4. Historical Immutability

WP-8 establishes the following absolute invariant:

> No historical valuation fact may be mutated, deleted, replaced, or rewritten.

The following operations are prohibited:

```text
UPDATE existing ValuationFact
DELETE existing ValuationFact
REPLACE existing ValuationFact
```

A correction to historical valuation state is represented by additional immutable facts.

---

# 5. Reversal Fact

A reversal is a new immutable valuation fact.

Conceptually:

```text
original fact
      │
      ▼
reversal fact
      │
      ▼
compensated effective state
```

A reversal identifies the specific historical fact that it compensates.

The semantic relationship is:

```text
reversal
    └── reversed_fact_identity
```

The reversal must reference the identity of a concrete historical valuation fact.

It must not use only:

* document identity;
* movement identity;
* valuation key.

This ensures that reversal semantics remain fact-specific.

---

# 6. Unpost Semantics

Unpost follows:

```text
original valuation facts
        ↓
identify unreversed facts
        ↓
append reversal facts
        ↓
derive compensated effective state
```

The operation must:

1. identify valuation facts belonging to the document;
2. determine which facts have already been reversed;
3. create reversal facts only for facts that remain unreversed;
4. persist the reversal facts;
5. materialize the compensated derived state.

The original facts remain unchanged.

---

# 7. Repeated Unpost / Repeated Reversal

Repeated unpost must be idempotent with respect to effective state.

Example:

```text
POST D
    ↓
UNPOST D
    ↓
UNPOST D
```

The second operation must not create a second effective compensation for the same historical fact.

The semantic rule is:

```text
one historical fact
        ↓
at most one effective reversal
```

However:

> The existence of a reversal fact does not by itself prove that derived state is complete.

This distinction is essential for recovery.

---

# 8. Recovery Is a Separate Semantic

Recovery is not defined as:

```text
retry remove()
```

or:

```text
retry establish()
```

Recovery is a distinct operation whose purpose is to reconcile authoritative history with derived state.

Its source is:

```text
ValuationFactPersistence.enumerate()
```

and not:

```text
CostMovementPersistence
CostBalancePersistence
cached derived state
```

The recovery model is:

```text
authoritative valuation history
        ↓
semantic interpretation
        ↓
effective valuation state
        ↓
derived movements
        ↓
totals / balances / results
```

Recovery must be able to operate without creating new historical valuation facts when the authoritative history already contains the required operation.

---

# 9. Rebuild Semantics

Derived-state rebuild is a deterministic reconstruction from immutable history.

Conceptually:

```text
immutable facts
        ↓
determine effective facts
        ↓
derive effective valuation movements
        ↓
rebuild totals
        ↓
rebuild balances/results
```

Rebuild must not:

* create valuation layers;
* create valuation consumptions;
* create reversal facts;
* mutate historical facts;
* delete historical facts.

Rebuild operates only on derived state.

---

# 10. Rebuild Idempotency

Given identical authoritative history:

```text
H
```

repeated rebuilds must produce equivalent derived state:

```text
rebuild(H) = S

rebuild(H) = S
```

Conceptually:

```text
rebuild(rebuild(H)) = rebuild(H)
```

No additional historical facts may appear as a consequence of rebuild.

---

# 11. Reversal Interpretation During Rebuild

Rebuild must interpret reversal relationships before constructing derived state.

Example:

```text
Layer L1
Consumption C1
Reversal R1 → L1
```

must not be interpreted as three unrelated active effects.

The rebuild process must first determine effective historical semantics and only then construct derived results.

Thus:

```text
historical fact set
        ↓
reversal interpretation
        ↓
effective fact set
        ↓
derived state
```

---

# 12. Repost Semantics

WP-8 changes the repost lifecycle established in WP-7.

The required order is:

```text
old valuation effect
        ↓
reversal / removal
        ↓
new valuation preparation
        ↓
new valuation effect
```

Therefore:

```text
remove
  ↓
prepare
  ↓
establish
```

is the authoritative repost sequence.

The previous conceptual ordering:

```text
prepare
  ↓
remove
  ↓
establish
```

is not sufficient for WP-8.

---

# 13. Reason for Repost Ordering

Valuation preparation may depend on the current effective valuation state.

With FIFO valuation, removing the old effect may release valuation layers that must be visible to the new preparation.

Therefore:

```text
old effect
    ↓
remove old effect
    ↓
new effective state
    ↓
prepare new valuation
```

is required.

The new preparation must observe the state after old-effect compensation.

---

# 14. Repost Failure Semantics

Repost is not a distributed transaction.

The lifecycle is:

```text
remove
   ↓
prepare
   ↓
establish
```

If `remove` returns:

```text
FAILURE
```

or:

```text
INDETERMINATE
```

then new valuation preparation must not proceed.

If:

```text
remove SUCCESS
prepare SUCCESS
establish FAILURE
```

then the old effect remains removed and the new effect is not established.

The system must not attempt to restore the old historical state by deleting reversal facts.

Recovery must instead reconcile the authoritative history and rebuild derived state.

---

# 15. Persistence Outcome Model

WP-8 preserves three persistence outcomes:

```text
SUCCESS
FAILURE
INDETERMINATE
```

## SUCCESS

The operation is known to have become durable.

## FAILURE

The operation is known not to have become durable.

## INDETERMINATE

The system cannot establish whether the operation became durable.

Indeterminate must never be interpreted as failure.

---

# 16. Recovery After INDETERMINATE

For:

```text
operation
    ↓
persistence INDETERMINATE
```

the system must not blindly append another equivalent historical effect.

Instead:

```text
INDETERMINATE
    ↓
reconcile authoritative history
    ↓
determine persisted logical operation
    ↓
complete/rebuild derived state
```

This prevents duplicate historical effects caused by retry.

---

# 17. Establish Recovery

A critical WP-8 requirement is recovery after:

```text
valuation facts persisted
        ↓
derived result persistence failed / became indeterminate
```

A repeated logical establish operation must not blindly generate another set of valuation facts.

The architecture must allow the existing authoritative facts to be recognized and reconciled.

The resulting effective state must contain one logical valuation effect.

---

# 18. Logical Operation Identity

Document identity alone is insufficient as a universal idempotency identity.

A document may have multiple lifecycle operations:

```text
POST D
UNPOST D
POST D
UNPOST D
```

These are distinct logical operations.

Therefore WP-8 requires an explicit concept of logical operation identity sufficient to distinguish:

```text
same logical operation
```

from:

```text
different lifecycle operation for the same document
```

The exact API representation of this identity is deferred to Concrete API Design.

Architecture requires only the following:

> Repeating the same logical operation must be recognizable as a repeat, while a new lifecycle operation on the same document must remain distinguishable.

---

# 19. Duplicate Logical Operation

For the same logical operation:

```text
operation O
operation O
```

the effective valuation state must be equivalent to executing O once.

A duplicate request must not produce:

```text
duplicate valuation effect
duplicate reversal effect
duplicate effective consumption
```

This requirement applies to:

* establish;
* unpost;
* reversal;
* repost;
* recovery-triggered retry.

---

# 20. Composite Posting Boundary

`CompositePostingResultCoordinator` remains generic.

It coordinates participants but does not understand valuation semantics.

It must not contain knowledge of:

* FIFO;
* valuation layers;
* reversal interpretation;
* inventory dimensions;
* valuation operation identity.

Its responsibility remains:

```text
participant lifecycle orchestration
```

---

# 21. Register / Valuation Partial Completion

The composite remains transaction-neutral.

Example:

```text
Register → SUCCESS
Valuation → INDETERMINATE
```

must remain representable.

The composite must not pretend that a global rollback occurred.

Recovery must reconcile the affected participant states independently.

This preserves the architecture established in WP-7.

---

# 22. Operation State Model

WP-8 conceptually distinguishes:

```text
Prepared
Established
Removed
Failed
Indeterminate
Recovered
```

The exact enum/API representation is deferred to Concrete API Design.

The architectural requirement is that persistence uncertainty and lifecycle completion must not be conflated.

In particular:

```text
INDETERMINATE ≠ FAILED
```

and:

```text
REVERSAL EXISTS ≠ DERIVED STATE RECOVERED
```

---

# 23. Recovery Boundaries

Recovery operates at two levels.

## 23.1 Authoritative history reconciliation

Determine what historical facts actually exist and which logical operations they represent.

## 23.2 Derived-state reconstruction

Reconstruct:

```text
CostMovement
CostTotals
CostBalance
materialized results
```

from authoritative history.

Recovery must not repair authoritative history by modifying it.

---

# 24. Failure Matrix

| Operation         | Failure point                      | Required semantic                      |
| ----------------- | ---------------------------------- | -------------------------------------- |
| Establish         | fact persistence FAILURE           | no duplicate retry effect              |
| Establish         | fact persistence INDETERMINATE     | reconcile before retry                 |
| Establish         | result persistence FAILURE         | facts remain authoritative             |
| Establish         | result persistence INDETERMINATE   | rebuild derived state                  |
| Unpost            | reversal persistence FAILURE       | no reversal assumed durable            |
| Unpost            | reversal persistence INDETERMINATE | reconcile reversal history             |
| Unpost            | derived persistence FAILURE        | history remains; rebuild derived state |
| Unpost            | derived persistence INDETERMINATE  | reconcile and rebuild                  |
| Repost            | remove FAILURE                     | stop; no new preparation               |
| Repost            | remove INDETERMINATE               | stop; recover/reconcile first          |
| Repost            | establish FAILURE                  | old effect remains reversed            |
| Repost            | establish INDETERMINATE            | reconcile authoritative history        |
| Rebuild           | derived persistence FAILURE        | retry rebuild from history             |
| Rebuild           | derived persistence INDETERMINATE  | repeat deterministic rebuild           |
| Repeated reversal | already reversed                   | no second effective reversal           |

---

# 25. Required Invariants

## W8-I1 — Historical immutability

No historical valuation fact is mutated or deleted.

## W8-I2 — Reversal is append-only

A correction is represented by a new reversal fact.

## W8-I3 — Fact-specific reversal

A reversal references a concrete historical fact identity.

## W8-I4 — Single effective reversal

A historical fact can have at most one effective reversal.

## W8-I5 — Derived-state rebuildability

Derived state can be reconstructed from authoritative history.

## W8-I6 — Recovery does not mutate history

Recovery never repairs state by changing historical facts.

## W8-I7 — Rebuild idempotency

Repeated rebuild from identical history produces equivalent derived state.

## W8-I8 — Logical-operation idempotency

Repeating one logical operation does not duplicate its effective effect.

## W8-I9 — Indeterminate requires reconciliation

An indeterminate persistence outcome must be reconciled before blind retry.

## W8-I10 — Repost ordering

Repost is:

```text
remove → prepare → establish
```

## W8-I11 — No rollback illusion

Repost and composite posting do not require distributed rollback.

## W8-I12 — Generic composition boundary

Composite posting remains independent of valuation-specific semantics.

---

# 26. Acceptance Criteria

WP-8 is architecturally complete only when the implementation demonstrates:

### AC-1 — Immutable unpost

```text
POST
→ UNPOST
```

creates reversal facts without modifying or deleting original valuation facts.

### AC-2 — Effective compensation

After unpost, effective valuation state is compensated correctly.

### AC-3 — Repeated unpost

Repeated unpost does not produce an additional effective reversal.

### AC-4 — Repeated reversal

A historical fact cannot be effectively reversed twice.

### AC-5 — Repost

```text
old effect
→ reversal
→ new preparation
→ new effect
```

is observable and deterministic.

### AC-6 — FIFO-aware repost

New valuation preparation observes the state after removal of the old effect.

### AC-7 — Persistence failure

Known persistence failure does not result in duplicate logical valuation effects on retry.

### AC-8 — Persistence indeterminate

Indeterminate persistence can be reconciled without blindly duplicating historical facts.

### AC-9 — Duplicate logical operation

Repeating the same logical operation produces one effective logical result.

### AC-10 — Rebuild after incomplete results

Incomplete derived results can be reconstructed from immutable valuation history.

### AC-11 — Rebuild idempotency

Repeated rebuild produces equivalent derived state.

### AC-12 — Historical preservation

All original valuation facts remain available after:

* unpost;
* repost;
* recovery;
* rebuild.

### AC-13 — Composite failure boundary

Register and Valuation partial completion remains representable without distributed rollback.

---

# 27. Explicit Non-Goals

WP-8 does not introduce:

```text
❌ mutation of historical valuation facts
❌ deletion of valuation history
❌ replacement/versioning of historical facts
❌ distributed transaction coordinator
❌ global rollback mechanism
❌ valuation-specific logic in PostingEngine
❌ Register → Valuation dependency
❌ Valuation → Standard dependency
❌ new FIFO implementation
❌ new valuation engine
❌ new Standard valuation architecture
❌ reconstruction of history from CostBalance
```

WP-8 also does not require a new durable storage engine.

Existing persistence boundaries remain authoritative.

---

# 28. Expected Architecture After WP-8

```text
                    PostingEngine
                          │
                          ▼
             PostingResultCoordinator
                          │
                          ▼
            CompositePostingCoordinator
                    /             \
                   /               \
                  ▼                 ▼
        Register Participant   Valuation Participant
                                    │
                                    ▼
                         Valuation Lifecycle
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
           Establish              Remove               Recover
              │                     │                     │
              ▼                     ▼                     ▼
       immutable facts       reversal facts       immutable history
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    ▼
                         Effective Valuation State
                                    │
                                    ▼
                         Derived Valuation Results
                                    │
                                    ▼
                    CostTotals / CostBalance / Results
```

The authoritative path is always:

```text
immutable history → effective interpretation → derived state
```

---

# 29. Architecture Review Decision

**WP-8 Architecture Definition — APPROVED WITH REQUIRED AMENDMENTS**

The following decisions are final for the architecture scope:

1. Historical valuation facts remain immutable.
2. Reversal is an immutable new fact.
3. Reversal addresses a concrete historical fact.
4. Repeated reversal is idempotent.
5. Recovery is a separate semantic from normal lifecycle retry.
6. Recovery starts from authoritative valuation history.
7. Derived state is rebuildable.
8. Rebuild is idempotent.
9. Logical operation identity is required.
10. Repeated logical operations must be idempotent.
11. `INDETERMINATE` requires reconciliation.
12. Repost order is `remove → prepare → establish`.
13. Repost does not use distributed rollback.
14. Composite Posting Coordinator remains transaction-neutral.
15. No historical valuation fact may be mutated or deleted.

---

# 30. Next Stage

The next stage is:

```text
WP-8 Concrete API Design
```

Concrete API Design must define, without changing the above architectural decisions:

* logical operation identity;
* operation/recovery state representation;
* deterministic fact identity or fact reconciliation mechanism;
* recovery API;
* derived-state rebuild API;
* establish reconciliation;
* reversal reconciliation;
* repost lifecycle API changes;
* persistence contracts required for recovery;
* exact ownership of each responsibility;
* failure/result contracts;
* test-level observability of the invariants.

No implementation should begin until the Concrete API Design is separately reviewed and approved.
