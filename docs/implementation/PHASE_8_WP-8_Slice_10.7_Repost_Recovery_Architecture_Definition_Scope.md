# PHASE 8 — WP-8 Slice 10.7

# Repost Recovery — Architecture Definition / Scope

**Status:** Final Architecture Reconciliation — Implemented and Verified
**Phase:** Phase 8
**Work Package:** WP-8 — Reversal / Repost / Recovery
**Slice:** 10.7 — Repost Recovery
**Baseline:** AcCoreD after Slice 10.6

---

# 1. Purpose

Slice 10.7 introduces recovery for an interrupted Posting Repost lifecycle.

The completed Repost lifecycle is:

```text
prepare
    ↓
remove
    ↓
establish
    ↓
DocumentReposted
```

The lifecycle intentionally has no cross-subsystem transaction.

Therefore the following state is possible:

```text
prepare  = SUCCESS
remove   = SUCCESS
establish = FAILURE / INDETERMINATE
```

At this point:

* the historical valuation facts of the old posting remain immutable;
* the old valuation effect has been compensated by REMOVE;
* the new valuation effect may be absent or partially persisted;
* the Posting lifecycle has not completed successfully;
* `DocumentReposted` must not have been published.

Slice 10.7 provides a deterministic recovery path from such states.

The central architectural requirement is:

> Recovery MUST continue the already-started logical Repost operation. It MUST NOT invoke `PostingEngine.repost()` as a new lifecycle.

---

# 2. Current Architecture Baseline

Slice 10.6 established:

```text
PostingOperationIdentity P
```

as the identity of one logical Posting lifecycle.

For Repost, deterministic valuation child identities are derived:

```text
R = derive(P, "valuation", "remove")
E = derive(P, "valuation", "establish")
```

The lifecycle is:

```text
prepare(new)
    ↓
remove(old, R)
    ↓
establish(new, E)
```

The authoritative valuation operation history is represented by immutable:

```text
ValuationOperationRecord
```

records.

No:

```text
PostingOperationRecord
PostingOperationPersistence
PostingLifecycleState
```

exists.

This architecture remains valid and MUST be preserved.

---

# 3. Recovery Problem

There are several possible interruption points.

## 3.1 Before REMOVE

```text
prepare = FAILURE
```

or:

```text
prepare = SUCCESS
remove = FAILURE
```

The old valuation effect remains effective.

No recovery of the new valuation is required.

---

## 3.2 REMOVE indeterminate

```text
prepare = SUCCESS
remove = INDETERMINATE
```

The caller cannot determine whether REMOVE fully completed.

Recovery MUST inspect the authoritative valuation operation:

```text
R
```

and reconcile its facts using the existing:

```text
ValuationOperationRecoveryService
```

REMOVE MUST NOT be blindly executed again.

---

## 3.3 REMOVE succeeded, ESTABLISH not started

This is the critical architectural case:

```text
prepare = SUCCESS
remove = SUCCESS
establish = not started
```

The old valuation effect has already been compensated.

The new valuation effect must now be established.

However, the current Slice 10.6 implementation creates the ESTABLISH `ValuationOperationRecord` during `establish()`.

Therefore, after a process interruption between:

```text
REMOVE success
```

and:

```text
ESTABLISH invocation
```

there may be:

```text
REMOVE operation record = present
ESTABLISH operation record = absent
```

The original in-memory `ValuationPlan` is lost.

Reconstructing it merely from the document is not generally sufficient because the original preparation may contain values determined during Posting preparation, including movement preparation context such as accounting time.

Therefore:

> Slice 10.7 MUST make the ESTABLISH recovery payload durable before the lifecycle reaches the point where REMOVE can succeed without it.

This is the principal architectural requirement of this Slice.

---

## 3.4 ESTABLISH indeterminate

```text
REMOVE = SUCCESS
ESTABLISH = INDETERMINATE
```

The ESTABLISH operation record should already identify the semantic plan.

Recovery must:

1. locate `E`;
2. validate its descriptor;
3. deterministically reconstruct expected facts;
4. reconcile partial fact persistence;
5. rebuild derived valuation state.

This is already supported by Slice 10.5 unified valuation recovery.

---

## 3.5 ESTABLISH already completed

Recovery may be invoked after the logical ESTABLISH has actually completed but before the caller observed the successful result.

Recovery MUST recognize the durable authoritative state and converge to:

```text
SUCCESS
```

without producing duplicate valuation facts.

---

# 4. Architectural Principle

The authoritative state of a Repost is still represented by valuation operation records.

The architecture remains:

```text
Posting identity
       │
       ├── REMOVE valuation operation
       │
       └── ESTABLISH valuation operation
```

There is no parent lifecycle persistence.

The important extension is that the ESTABLISH operation's semantic recovery descriptor must become available **before REMOVE is allowed to complete**.

This descriptor remains a valuation-level artifact.

No Posting-specific persistence record is introduced.

---

# 5. Durable ESTABLISH Intent

The existing:

```text
ValuationEstablishRecoveryDescriptor
```

already contains the semantic information required to reconstruct an ESTABLISH plan:

```text
document_identity
operations
```

It deliberately excludes:

* generated valuation fact identities;
* generated reversal identities;
* balances;
* derived movements;
* mutable execution state.

That design remains correct.

Slice 10.7 extends its lifecycle role:

> The ESTABLISH operation record, containing the recovery descriptor, must be durably registered before a Repost REMOVE may create an irreversible lifecycle boundary.

Conceptually:

```text
prepare
   ↓
register ESTABLISH intent
   ↓
REMOVE
   ↓
ESTABLISH
```

The registration is not execution of valuation facts.

It is durable recording of the semantic ESTABLISH operation that the lifecycle intends to perform.

---

# 6. Why No Posting Operation Record Is Needed

It may appear that the missing state could be solved by introducing:

```text
PostingOperationRecord
```

This is explicitly rejected.

The Posting layer does not need to persist a second copy of valuation semantics.

The valuation operation record already contains:

* operation identity;
* operation type;
* document identity;
* semantic fingerprint;
* ESTABLISH recovery descriptor.

The Posting identity provides the deterministic parent correlation:

```text
P
```

and the valuation identities provide:

```text
R
E
```

Therefore recovery can derive and inspect the required child operations without introducing a second authoritative lifecycle state.

---

# 7. Recovery Authority

The recovery architecture is:

```text
PostingOperationIdentity P
          │
          ├── derive R
          │      │
          │      └── ValuationOperationRecoveryService
          │
          └── derive E
                 │
                 └── ValuationOperationRecoveryService
```

The Posting recovery layer coordinates lifecycle order.

The Valuation recovery layer owns valuation operation recovery.

Responsibilities remain separated.

### Posting recovery owns

* lifecycle sequencing;
* determining whether REMOVE recovery is required;
* determining whether ESTABLISH recovery is required;
* ensuring REMOVE completes before ESTABLISH;
* mapping valuation outcomes to Posting lifecycle outcomes;
* final successful lifecycle completion.

### Valuation recovery owns

* operation lookup;
* operation validation;
* deterministic fact reconstruction;
* partial fact reconciliation;
* derived-state rebuild.

---

# 8. Recovery State Model

No mutable lifecycle state is introduced.

The effective state is derived from authoritative operation records and valuation facts.

The conceptual state machine is:

```text
                 ┌─────────────────────┐
                 │ No completed REMOVE │
                 └──────────┬──────────┘
                            │
                       recover R
                            │
                            ▼
                 ┌─────────────────────┐
                 │   REMOVE SUCCESS   │
                 └──────────┬──────────┘
                            │
                     recover / execute E
                            │
                            ▼
                 ┌─────────────────────┐
                 │ ESTABLISH SUCCESS  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Repost SUCCESS      │
                 └─────────────────────┘
```

Failure or indeterminate outcomes stop recovery at the affected phase.

Recovery may subsequently be invoked again.

---

# 9. REMOVE Recovery

If:

```text
R = not found
```

the recovery service must distinguish between:

* an operation that genuinely never started;
* an invalid recovery request;
* a lifecycle state for which recovery has insufficient authoritative information.

Slice 10.7 MUST NOT interpret absence of `R` as permission to execute an ordinary new REMOVE blindly.

The parent Posting recovery flow must use the lifecycle context to determine whether recovery is applicable.

If `R` exists:

```text
recover(R)
```

uses the existing unified valuation recovery service.

Repeated recovery must be idempotent.

No historical fact may be mutated or deleted.

---

# 10. ESTABLISH Recovery

Once REMOVE is authoritative and successful:

```text
recover(E)
```

must be attempted.

If `E` already exists, its persisted:

```text
ValuationEstablishRecoveryDescriptor
```

is authoritative for recovery.

The descriptor is converted back into the semantic `ValuationPlan`.

The existing Slice 10.5 recovery mechanism then:

```text
descriptor
    ↓
ValuationPlan
    ↓
expected valuation facts
    ↓
fact reconciliation
    ↓
derived-state rebuild
```

No new fact-recovery mechanism is required.

---

# 11. ESTABLISH Intent Must Exist Before REMOVE Completion

The following sequence is required:

```text
prepare
    ↓
durable ESTABLISH intent
    ↓
REMOVE
    ↓
ESTABLISH
```

The key invariant is:

> Once a Repost can leave the old valuation state removed, enough durable information must already exist to reconstruct the replacement valuation state.

This removes the recovery gap:

```text
REMOVE = SUCCESS
ESTABLISH = absent
prepared plan = lost
```

The durable ESTABLISH descriptor closes that gap.

---

# 12. Normal ESTABLISH Semantics

The architecture must preserve the existing idempotency contract.

If an ESTABLISH operation with identity `E` already exists:

```text
same identity
+
same semantics
```

means:

```text
idempotent continuation
```

If:

```text
same identity
+
different semantics
```

then:

```text
conflict
```

must be returned.

Recovery MUST never overwrite an existing operation record.

---

# 13. Relationship Between Fingerprint and Identity

The existing distinction remains mandatory.

The semantic fingerprint describes:

```text
what valuation operation means
```

The operation identity describes:

```text
which logical operation this is
```

The parent Posting identity may influence deterministic child identity:

```text
P → E
```

but must not make semantically identical valuation plans semantically different merely because a different opaque lifecycle identity was used.

Recovery must preserve this distinction.

---

# 14. Prepared Plan Reuse

For the original successful Repost:

```text
prepare
    ↓
plan
    ↓
remove
    ↓
same plan
    ↓
establish
```

No second preparation is performed.

For recovery after process interruption, the original in-memory plan may no longer exist.

In that case:

```text
persisted ESTABLISH descriptor
```

is used to reconstruct the equivalent plan.

Thus:

```text
normal execution → reuse prepared plan
recovery         → reconstruct from durable descriptor
```

Both paths must produce the same semantic valuation facts.

---

# 15. Derived State

Slice 10.7 does not introduce a new derived-state recovery mechanism.

The existing Slice 10.5 contract remains:

```text
authoritative valuation facts
        ↓
DefaultValuationRebuilder
        ↓
derived valuation state
```

After successful REMOVE recovery:

```text
rebuild
```

must reflect the compensated old state.

After successful ESTABLISH recovery:

```text
rebuild
```

must reflect the replacement valuation state.

`DefaultValuationRebuilder` remains the sole derived-state rebuild implementation.

---

# 16. Historical Immutability

Recovery MUST NOT mutate historical valuation facts.

For the old Repost valuation:

```text
old Layer
old Consumption
```

remain immutable.

REMOVE continues to compensate them using reversal facts.

ESTABLISH creates new valuation facts.

The lifecycle therefore remains:

```text
old facts
   ↓
reversal facts
   ↓
new facts
```

not:

```text
old facts modified
```

---

# 17. Repeated Recovery

Recovery must converge.

For any recovery phase:

```text
recover()
recover()
recover()
```

must not produce additional logical effects after the first successful reconciliation.

In particular:

* no duplicate REMOVE reversal facts;
* no duplicate ESTABLISH valuation facts;
* no duplicate operation records;
* no modification of historical facts;
* no repeated semantic mutation of derived state beyond deterministic rebuild.

---

# 18. Failure and Indeterminate Semantics

Recovery must preserve the distinction:

```text
FAILURE
```

versus:

```text
INDETERMINATE
```

### FAILURE

The operation is known not to have completed and the failure is safely attributable.

### INDETERMINATE

Persistence or execution state cannot be established with certainty.

Recovery must not convert an indeterminate state into an assumed failure.

The existing persistence semantics remain authoritative.

---

# 19. Recovery Ordering

For a Repost parent identity `P`:

```text
R = derive(P, "valuation", "remove")
E = derive(P, "valuation", "establish")
```

the required recovery order is:

```text
1. inspect/recover R
2. require R == SUCCESS
3. inspect/recover E
4. require E == SUCCESS
5. complete Posting lifecycle
```

`E` MUST NOT be recovered before the old valuation removal is authoritative.

This preserves the semantic requirement:

```text
old effect removed
        ↓
new effect established
```

---

# 20. Already Completed Repost

If both:

```text
R = SUCCESS
E = SUCCESS
```

are authoritative, recovery must return:

```text
PostingLifecycleOutcome.SUCCESS
```

without re-executing either valuation operation.

The caller may safely treat recovery as confirmation of lifecycle completion.

---

# 21. Event Boundary

Slice 10.7 does not introduce a new event persistence subsystem.

The existing event rule remains:

```text
DocumentReposted
```

is published only after the lifecycle has reached successful completion.

Recovery itself must not create a second logical lifecycle.

Therefore the architecture must explicitly prevent:

```text
successful repost
+
recovery
```

from becoming:

```text
two DocumentReposted events
```

The existing `_result_from_lifecycle()` event boundary remains the baseline.

If implementation reveals that event idempotency cannot be guaranteed with the existing architecture, that is a concrete architectural gap to be addressed separately rather than introducing speculative event persistence now.

---

# 22. Posting Layer Remains Valuation-Agnostic

The generic Posting layer knows:

```text
PostingOperationIdentity
```

and lifecycle recovery.

It must not know:

* FIFO;
* valuation layers;
* valuation consumptions;
* valuation reversals;
* valuation facts.

The valuation participant remains responsible for translating:

```text
PostingOperationIdentity
```

into deterministic valuation child identities.

---

# 23. Standard Composition

Standard configuration may wire the concrete recovery implementation.

However:

```text
accore.platform.posting
```

must remain generic.

Standard-specific valuation semantics remain under:

```text
accore.platform.valuation
standard.valuation
```

according to existing boundaries.

No generic valuation logic is moved into Standard.

---

# 24. No Cross-Subsystem Transaction

Slice 10.7 does not introduce:

```text
distributed transaction
database transaction
transaction coordinator
rollback framework
```

across:

```text
Register
Valuation
Posting
```

Recovery remains explicit and deterministic.

If another Posting participant has already completed while valuation recovery is required, its recovery semantics remain its own responsibility.

---

# 25. Scope

Slice 10.7 includes:

### Recovery identity

* deterministic derivation of REMOVE and ESTABLISH child identities;
* validation of parent/child identity relationship.

### Durable ESTABLISH recovery information

* ensuring the ESTABLISH descriptor is durable before REMOVE can leave the lifecycle without the old effect;
* preserving the existing immutable operation-record model.

### Posting recovery coordination

* inspect lifecycle state from authoritative operation records;
* recover REMOVE first;
* recover ESTABLISH second;
* stop on FAILURE/INDETERMINATE;
* recognize already-completed lifecycle.

### Valuation recovery integration

* reuse `ValuationOperationRecoveryService`;
* reuse `DefaultValuationRebuilder`;
* reuse deterministic fact reconstruction and reconciliation.

### Idempotency

* repeated REMOVE recovery;
* repeated ESTABLISH recovery;
* repeated complete Repost recovery;
* operation conflict handling.

### Tests

* every interruption state;
* repeated recovery;
* partial persistence;
* indeterminate persistence;
* successful recovery;
* already-completed recovery;
* historical immutability;
* derived-state equivalence.

---

# 26. Explicitly Out of Scope

The following are not part of Slice 10.7:

* `PostingOperationRecord`;
* `PostingOperationPersistence`;
* mutable `PostingLifecycleState`;
* cross-subsystem transactions;
* compensation of Register operations;
* changes to FIFO semantics;
* new valuation fact types;
* mutation/deletion of historical valuation facts;
* new derived-state rebuild implementation;
* event persistence infrastructure unless a concrete gap is demonstrated;
* public business-document model changes;
* unrelated Posting API redesign;
* generic transaction framework.

---

# 27. Required Architectural Invariants

The implementation must preserve:

### Invariant 1 — One logical lifecycle

One:

```text
PostingOperationIdentity P
```

represents one Repost lifecycle.

---

### Invariant 2 — Deterministic child identities

```text
R = derive(P, valuation, remove)
E = derive(P, valuation, establish)
```

are deterministic.

---

### Invariant 3 — REMOVE precedes ESTABLISH

```text
R SUCCESS
```

is a prerequisite for:

```text
E recovery/execution
```

---

### Invariant 4 — ESTABLISH recovery information is durable

Once REMOVE may complete, the semantic replacement plan must be recoverable without the original process memory.

---

### Invariant 5 — Historical immutability

No historical valuation fact is modified or deleted.

---

### Invariant 6 — Recovery is idempotent

Repeated recovery converges to the same authoritative state.

---

### Invariant 7 — Derived state follows authoritative facts

Derived state is rebuilt from authoritative valuation facts.

---

### Invariant 8 — No new parent persistence

Valuation operation records remain the authoritative operation history.

---

### Invariant 9 — No recovery by calling Repost again

Recovery continues the existing lifecycle identity.

---

### Invariant 10 — Events follow successful completion

`DocumentReposted` is emitted only after successful lifecycle completion.

---

# 28. Required Recovery Matrix

| State                             | Authoritative situation        | Recovery action           | Expected result                   |
| --------------------------------- | ------------------------------ | ------------------------- | --------------------------------- |
| Prepare failure                   | old state untouched            | none                      | no recovery required              |
| Remove failure                    | old state remains effective    | no retry as new lifecycle | FAILURE                           |
| Remove indeterminate              | REMOVE outcome uncertain       | recover `R`               | SUCCESS / FAILURE / INDETERMINATE |
| Remove success, establish pending | old effect compensated         | recover `E`               | SUCCESS / FAILURE / INDETERMINATE |
| Establish indeterminate           | `E` may be partially persisted | recover `E`               | SUCCESS / FAILURE / INDETERMINATE |
| Establish partial facts           | operation + descriptor exist   | reconcile `E` facts       | SUCCESS                           |
| Both operations successful        | lifecycle already complete     | no mutation               | SUCCESS                           |
| Repeated recovery                 | state already reconciled       | no duplicate facts        | SUCCESS                           |

---

# 29. Main Architectural Decision

The central decision proposed for Slice 10.7 is:

> **The ESTABLISH operation record and its recovery descriptor become the durable semantic intent for the replacement valuation operation, and this intent must exist before Repost REMOVE can leave the old valuation effect compensated.**

This allows recovery to remain:

```text
operation-record driven
```

without introducing:

```text
PostingOperationPersistence
```

or mutable lifecycle state.

The resulting architecture is:

```text
                  PostingOperationIdentity P
                              │
                 ┌────────────┴────────────┐
                 │                         │
          valuation REMOVE          valuation ESTABLISH
                 │                         │
                 R                         E
                 │                         │
        immutable operation       immutable operation
             record                    record
                 │                         │
          reversal facts            recovery descriptor
                 │                         │
                 └────────────┬────────────┘
                              │
                    authoritative facts
                              │
                              ▼
                    DefaultValuationRebuilder
                              │
                              ▼
                     derived valuation state
```

---

# 30. Final Architecture Review Result

The architecture questions listed during design review were resolved by the implemented Slice 10.7 design:

1. Durable ESTABLISH intent is registered before Repost REMOVE.
2. No `PostingOperationRecord` or Posting persistence boundary is introduced.
3. Valuation operation records remain authoritative for valuation lifecycle recovery.
4. Recovery order is REMOVE → ESTABLISH.
5. `ValuationEstablishRecoveryDescriptor` is the recovery source; Posting preparation is not rerun during recovery.
6. `DefaultValuationRebuilder` remains the sole derived-state rebuild implementation.
7. No event persistence/idempotency layer is introduced.
8. Register recovery remains a no-op in this slice; cross-subsystem transactions remain out of scope.

## 31. Definition of Done — Satisfied

Slice 10.7 architecture is implemented and verified at commit `5046a9c`. The final Python 3.14 quality gate was:

```text
pytest -q       → 1051 passed
ruff check .    → PASS
black --check . → PASS (237 files unchanged)
mypy src        → PASS (129 source files)
```

The corresponding Concrete API Design is implemented; no further architecture approval is pending for Slice 10.7.
