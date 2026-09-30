# PHASE 8 — WP-8 Slice 10.7

# Repost Recovery — Concrete API Design

**Status:** Approved for Architecture Review
**Phase:** Phase 8
**Work Package:** WP-8 — Reversal / Repost / Recovery
**Slice:** 10.7 — Repost Recovery
**Baseline:** AcCoreD after Slice 10.6

---

# 1. Purpose

This slice adds recovery of an interrupted Repost lifecycle.

The lifecycle remains:

```text
prepare
    ↓
register ESTABLISH intent
    ↓
remove
    ↓
establish
    ↓
DocumentReposted
```

Recovery is performed against the same:

```text
PostingOperationIdentity
```

and deterministic valuation child identities.

No new Posting persistence model is introduced.

The authoritative history remains:

```text
ValuationOperationRecord
```

---

# 2. Core API Decisions

Slice 10.7 introduces four concrete API changes:

1. durable ESTABLISH intent registration in `ValuationLifecycleCoordinator`;
2. Posting-level `PostingRecoveryService`;
3. deterministic derivation of REMOVE and ESTABLISH valuation identities;
4. recovery-aware `PostingResultCoordinator` integration.

The existing:

```python
ValuationOperationRecoveryService
```

remains unchanged.

The existing:

```python
DefaultValuationRebuilder
```

remains the sole derived-state rebuild mechanism.

---

# 3. Existing Identity Model

One Repost owns one parent:

```python
PostingOperationIdentity
```

The valuation participant derives:

```text
R = derive(P, "valuation", "remove")
E = derive(P, "valuation", "establish")
```

where:

```text
P = parent PostingOperationIdentity
R = REMOVE ValuationOperationIdentity
E = ESTABLISH ValuationOperationIdentity
```

The same derivation factory already used by Slice 10.6 is reused.

No new string-based identity construction is introduced.

---

# 4. Posting Recovery Identity

The public Posting recovery API accepts the parent identity only.

```python
class PostingRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

Concrete implementation:

```python
class DefaultPostingRecoveryService:
    ...
```

The service does not persist Posting state.

It derives participant operation identities and delegates recovery to the configured Posting participants.

---

# 5. Posting Recovery Service Responsibilities

`DefaultPostingRecoveryService` is responsible for:

1. deriving participant recovery identities;
2. recovering participants in configured lifecycle order;
3. enforcing `REMOVE → ESTABLISH` ordering for valuation;
4. stopping after `FAILURE` or `INDETERMINATE`;
5. returning the final `PostingLifecycleResult`.

It does **not**:

* reconstruct valuation plans;
* inspect valuation facts directly;
* mutate valuation state;
* rebuild valuation totals;
* persist Posting lifecycle state.

---

# 6. Posting Recovery Participant Contract

The generic Posting participant API is extended with recovery.

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

    def recover(
        self,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

The additional method is intentionally generic.

A participant that has no persistent recoverable lifecycle may implement it as an immediate success.

---

# 7. PostingResultCoordinator Recovery API

The coordinator gains:

```python
class PostingResultCoordinator(Protocol):
    ...

    def recover(
        self,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

`CompositePostingResultCoordinator` delegates recovery to participants in the same configured participant order.

Conceptually:

```text
PostingResultCoordinator.recover(P)
        │
        ├── Register participant
        │
        └── Valuation participant
```

The generic coordinator does not know valuation-specific identities.

---

# 8. Valuation Posting Coordinator Recovery

`ValuationPostingCoordinator` implements:

```python
def recover(
    self,
    operation_identity: PostingOperationIdentity,
) -> PostingLifecycleResult:
    ...
```

It derives:

```python
remove_identity = self._operation_identity_factory.derive(
    operation_identity,
    "valuation",
    "remove",
)

establish_identity = self._operation_identity_factory.derive(
    operation_identity,
    "valuation",
    "establish",
)
```

and wraps them as:

```python
ValuationOperationIdentity(remove_identity)
ValuationOperationIdentity(establish_identity)
```

The existing `ValuationOperationRecoveryService` is then used.

---

# 9. Valuation Recovery Ordering

The valuation participant MUST recover:

```text
REMOVE
    ↓
ESTABLISH
```

in that order.

Pseudo-flow:

```python
remove_result = self._lifecycle.recover(remove_identity)

if remove_result.outcome is not PostingLifecycleOutcome.SUCCESS:
    return remove_result

establish_result = self._lifecycle.recover(establish_identity)

return establish_result
```

The important rule is:

> ESTABLISH recovery is never attempted until REMOVE recovery has returned SUCCESS.

---

# 10. The ESTABLISH Intent Registration API

The existing:

```python
ValuationLifecycleCoordinator.establish(...)
```

currently registers the operation record immediately before writing facts.

Slice 10.7 extracts this registration into a separate explicit API:

```python
class ValuationLifecycleCoordinator(Protocol):
    def prepare_establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishResult:
        ...

    def establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishmentResult:
        ...

    def remove(
        self,
        document_identity: Identifier,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRemovalResult:
        ...

    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        ...
```

The exact result naming is intentionally aligned with existing valuation result types.

---

# 11. `prepare_establish()` Semantics

`prepare_establish()` performs:

1. plan validation;
2. document identity extraction;
3. recovery descriptor construction;
4. semantic fingerprint calculation;
5. creation of `ValuationOperationRecord`;
6. idempotent operation-record persistence.

It does **not**:

* create valuation facts;
* append cost movements;
* update balances;
* rebuild derived state.

Conceptually:

```text
ValuationPlan
    ↓
validate
    ↓
ValuationEstablishRecoveryDescriptor
    ↓
fingerprint
    ↓
ValuationOperationRecord(ESTABLISH)
    ↓
append()
```

---

# 12. Why `prepare_establish()` Is Required

The operation record must exist before REMOVE can succeed.

Therefore Repost becomes:

```text
prepare valuation plan
        ↓
prepare_establish(plan, E)
        ↓
remove(R)
        ↓
establish(plan, E)
```

If the process terminates after:

```text
remove(R) == SUCCESS
```

the durable record:

```text
E
```

already contains the recovery descriptor.

Recovery can therefore continue without the original in-memory `ValuationPlan`.

---

# 13. Idempotency of `prepare_establish()`

`prepare_establish()` uses the existing operation persistence semantics.

For identity `E`:

```text
E absent
    → append

E exists + same semantics
    → SUCCESS

E exists + different semantics
    → FAILURE / ValuationConflictError
```

No operation record is overwritten.

No descriptor is mutated.

---

# 14. Existing `establish()` Becomes Execution

`establish()` remains the operation that performs valuation fact persistence.

Its new internal sequence is:

```text
validate plan
    ↓
ensure ESTABLISH operation record
    ↓
build facts
    ↓
reconcile facts
    ↓
persist derived movements
    ↓
persist balances
```

The "ensure operation record" step is idempotent.

If `prepare_establish()` already created the record, `establish()` finds the same record and continues.

Therefore normal Repost does not create two operation records.

---

# 15. Shared Operation Construction

To prevent divergence between:

```text
prepare_establish()
```

and:

```text
establish()
```

the construction of the authoritative operation record is factored into one private method:

```python
def _build_establish_operation(
    self,
    plan: ValuationPlan,
    operation_identity: ValuationOperationIdentity,
) -> ValuationOperationRecord:
    ...
```

This method creates:

```python
ValuationEstablishRecoveryDescriptor(
    document_identity=document_identity,
    operations=plan.operations,
)
```

and:

```python
ValuationOperationRecord(
    identity=operation_identity,
    operation_type=ValuationOperationType.ESTABLISH,
    document_identity=document_identity,
    fingerprint=_establish_fingerprint(plan),
    establish_descriptor=descriptor,
)
```

The same operation-construction logic is used by both APIs.

---

# 16. Result Type for `prepare_establish()`

A dedicated result type is used rather than exposing the persistence record as the public result:

```python
class ValuationEstablishPreparationOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationEstablishPreparationResult:
    outcome: ValuationEstablishPreparationOutcome
    error: Exception | None = None
```

The caller does not need the operation record because its identity is already known.

---

# 17. Normal Repost Flow

`PostingEngine.repost()` becomes conceptually:

```python
operation_identity = self._operation_identity_factory.new()

plan = self._coordinator.prepare(
    document,
    movement_set,
    PostingPreparationContext(
        operation_identity=operation_identity,
        replacement_document_identity=document.identity,
    ),
)

prepared = self._coordinator.prepare_establish(
    document,
    movement_set,
    plan,
    operation_identity,
)

if prepared.outcome is not PostingLifecycleOutcome.SUCCESS:
    return self._result_from_lifecycle(prepared, None)

removal = self._coordinator.remove(
    document,
    operation_identity,
)

if removal.outcome is not PostingLifecycleOutcome.SUCCESS:
    return self._result_from_lifecycle(removal, None)

establishment = self._coordinator.establish(
    document,
    movement_set,
    plan,
    operation_identity,
)

return self._result_from_lifecycle(
    establishment,
    DocumentReposted(document.identity),
)
```

The actual generic coordinator API therefore gains:

```python
def prepare_establish(
    self,
    document: ObjectInstance,
    movement_set: MovementSet,
    plan: PostingResultPlan,
    operation_identity: PostingOperationIdentity,
) -> PostingLifecycleResult:
    ...
```

---

# 18. Generic Posting Coordinator API

The complete protocol becomes:

```python
class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        context: PostingPreparationContext,
    ) -> PostingResultPlan:
        ...

    def prepare_establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
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

    def recover(
        self,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

---

# 19. Generic Participant `prepare_establish()`

The participant contract gains:

```python
class PostingResultParticipant(Protocol):
    ...

    def prepare_establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        ...
```

Participants that have no durable establishment intent return:

```python
PostingLifecycleResult(
    PostingLifecycleOutcome.SUCCESS
)
```

This keeps the API generic.

---

# 20. Valuation Participant `prepare_establish()`

`ValuationPostingCoordinator` implements:

```python
def prepare_establish(
    self,
    document: ObjectInstance,
    movement_set: MovementSet,
    plan: object,
    operation_identity: PostingOperationIdentity,
) -> PostingLifecycleResult:
    ...
```

It validates the plan type:

```python
if not isinstance(plan, ValuationPlan):
    raise TypeError(...)
```

Then derives:

```python
establish_identity = self._operation_identity_factory.derive(
    operation_identity,
    "valuation",
    "establish",
)
```

and invokes:

```python
self._lifecycle.prepare_establish(
    plan,
    ValuationOperationIdentity(establish_identity),
)
```

---

# 21. Composite Coordinator Semantics

`CompositePostingResultCoordinator.prepare_establish()` forwards the same:

```text
PostingOperationIdentity
```

and participant plan to every participant.

Participant order remains the existing configured order.

There is no compensation mechanism.

There is no cross-participant transaction.

If a participant returns:

```text
FAILURE
```

or:

```text
INDETERMINATE
```

the lifecycle stops.

---

# 22. Important Consequence of Pre-registration

After:

```text
prepare_establish(E) == SUCCESS
```

but before:

```text
remove(R)
```

the ESTABLISH operation record may already exist.

This is intentional.

The record represents:

> durable semantic intent to establish the replacement valuation.

It does **not** mean that ESTABLISH facts have already been applied.

---

# 23. Distinguishing Intent From Completion

The architecture deliberately does not add an operation status field.

Completion is derived from authoritative facts.

For ESTABLISH:

```text
operation record exists
+
expected facts reconciled
```

means the operation has been applied.

The record itself is the durable semantic intent.

This preserves the append-only operation model.

---

# 24. Recovery of an ESTABLISH Intent

`DefaultValuationOperationRecoveryService.recover(E)` already has the necessary ESTABLISH path:

```text
find E
    ↓
read establish_descriptor
    ↓
reconstruct ValuationPlan
    ↓
build expected facts
    ↓
reconcile facts
    ↓
rebuild derived state
```

No new valuation recovery API is required.

This is an important reuse boundary.

---

# 25. Recovery of REMOVE

For:

```python
recover(P)
```

the valuation participant first derives:

```python
R
```

and calls:

```python
self._lifecycle.recover(R)
```

The existing unified valuation recovery service handles:

* operation lookup;
* REMOVE reversal-fact recovery;
* fact reconciliation;
* derived-state rebuild.

---

# 26. Recovery of ESTABLISH

Only after:

```text
recover(R) == SUCCESS
```

does the participant derive:

```python
E
```

and call:

```python
self._lifecycle.recover(E)
```

This allows recovery to handle all of:

```text
REMOVE success
ESTABLISH never executed
```

```text
REMOVE success
ESTABLISH operation registered
ESTABLISH facts absent
```

```text
REMOVE success
ESTABLISH facts partially persisted
```

```text
REMOVE success
ESTABLISH fully persisted
```

with one recovery path.

---

# 27. Recovery When ESTABLISH Is Already Complete

If `E` has already been fully reconciled:

```python
recover(E)
```

returns:

```text
SUCCESS
```

without appending duplicate facts.

The parent recovery service then returns:

```text
SUCCESS
```

for the Repost lifecycle.

---

# 28. Recovery When ESTABLISH Intent Exists but Facts Do Not

This is the key new recovery case.

State:

```text
E operation record = present
E facts = absent
R = SUCCESS
```

Recovery calls:

```python
recover(E)
```

The existing descriptor reconstructs the plan.

Expected facts are generated deterministically.

Facts are appended idempotently.

Derived state is rebuilt.

Result:

```text
SUCCESS
```

---

# 29. Recovery When ESTABLISH Intent Registration Is Indeterminate

If:

```text
prepare_establish(E)
```

returns:

```text
INDETERMINATE
```

the Repost does not proceed to REMOVE.

The caller must not assume that `E` does or does not exist.

A later explicit recovery can inspect:

```text
E
```

using authoritative operation persistence.

If `E` exists with the expected semantics, recovery may continue once REMOVE status is established.

If `E` does not exist, there is no valid durable replacement intent.

This state is returned as a recovery failure/indeterminate condition according to the existing persistence semantics.

---

# 30. Recovery When REMOVE Fails

If:

```text
R = FAILURE
```

recovery stops.

`E` is not recovered.

No new REMOVE is executed.

No ESTABLISH facts are created.

The durable ESTABLISH intent may remain present, but it is not executable until the required REMOVE lifecycle state has been successfully recovered.

---

# 31. Recovery When REMOVE Is Indeterminate

If:

```text
R = INDETERMINATE
```

recovery returns:

```text
INDETERMINATE
```

unless the existing valuation recovery service can reconcile `R` to SUCCESS.

The ESTABLISH phase is never started before that.

---

# 32. Recovery Result Mapping

The valuation participant maps:

```python
ValuationRecoveryOutcome
```

to:

```python
PostingLifecycleOutcome
```

using the same value semantics:

```text
SUCCESS       → SUCCESS
FAILURE       → FAILURE
INDETERMINATE → INDETERMINATE
```

The original exception is preserved.

---

# 33. `PostingEngine.recover()`

The public Posting engine gains:

```python
def recover(
    self,
    operation_identity: PostingOperationIdentity,
) -> PostingResult:
    ...
```

Implementation:

```python
def recover(
    self,
    operation_identity: PostingOperationIdentity,
) -> PostingResult:
    try:
        result = self._coordinator.recover(operation_identity)
        return self._result_from_lifecycle(result, None)
    except PersistenceIndeterminateError as exc:
        return PostingResult.indeterminate(
            PostingIndeterminateError(str(exc))
        )
    except PersistenceError as exc:
        return PostingResult.failure(
            PostingPersistenceError(str(exc))
        )
    except Exception as exc:  # noqa: BLE001
        return PostingResult.failure(
            PostingPersistenceError(str(exc))
        )
```

Recovery does not create a new Posting identity.

---

# 34. Event Semantics for Recovery

`PostingEngine.recover()` does not automatically publish:

```text
DocumentReposted
```

because the recovery API receives only the operation identity.

There is deliberately no:

```python
document: ObjectInstance
```

requirement for recovery.

The lifecycle event boundary remains tied to the original successful Posting invocation.

If the original invocation did not publish an event because the process terminated after durable completion, event publication requires a separate concrete event-delivery guarantee.

Slice 10.7 does not introduce an event outbox or event persistence subsystem.

---

# 35. No Duplicate Lifecycle

Calling:

```python
posting_engine.recover(P)
```

must never create:

```text
new PostingOperationIdentity
```

and must never invoke:

```python
posting_engine.repost(document)
```

Recovery is continuation, not a new posting.

---

# 36. Valuation Lifecycle Protocol — Final Form

The final protocol is:

```python
class ValuationLifecycleCoordinator(Protocol):
    def prepare_establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishPreparationResult:
        ...

    def establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishmentResult:
        ...

    def remove(
        self,
        document_identity: Identifier,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRemovalResult:
        ...

    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        ...
```

---

# 37. Valuation Coordinator Internal API

`DefaultValuationCoordinator` gains:

```python
def prepare_establish(
    self,
    plan: ValuationPlan,
    operation_identity: ValuationOperationIdentity,
) -> ValuationEstablishPreparationResult:
    ...
```

and a shared private helper:

```python
def _build_establish_operation(
    self,
    plan: ValuationPlan,
    operation_identity: ValuationOperationIdentity,
) -> ValuationOperationRecord:
    ...
```

The existing `_register_operation()` remains the single persistence/reconciliation boundary.

---

# 38. Operation Registration Error Semantics

`prepare_establish()` uses exactly the existing registration semantics.

### `ValuationConflictError`

Return:

```text
FAILURE
```

### `PersistenceIndeterminateError`

Attempt authoritative lookup.

If the operation exists and equals the requested record:

```text
SUCCESS
```

If it exists with different semantics:

```text
FAILURE
```

If existence cannot be established:

```text
INDETERMINATE
```

### `ValuationPersistenceError`

Preserve:

```python
rollback_guaranteed
```

mapping.

### Generic `PersistenceError`

Return:

```text
INDETERMINATE
```

No new error hierarchy is introduced.

---

# 39. `ValuationOperationRecord` — No Structural Change

The existing record remains:

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
    target_fact_identities: tuple[Identifier, ...] = ()
    establish_descriptor: ValuationEstablishRecoveryDescriptor | None = None
```

No:

```python
status
phase
completed
started_at
posting_operation_identity
```

fields are added.

---

# 40. `ValuationEstablishRecoveryDescriptor` — No Structural Change

The existing descriptor remains:

```python
@dataclass(frozen=True, slots=True)
class ValuationEstablishRecoveryDescriptor:
    document_identity: Identifier
    operations: tuple[ValuationPlanOperation, ...]
```

It remains:

* immutable;
* semantic;
* sufficient to reconstruct the plan;
* independent of generated fact identities;
* independent of derived balances.

---

# 41. Fingerprint Semantics

`prepare_establish()` computes the same fingerprint used by normal `establish()`.

Therefore:

```text
prepare_establish(plan, E)
```

and:

```text
establish(plan, E)
```

must produce exactly the same:

```text
fingerprint
descriptor
document_identity
```

for the same semantic plan.

Operation identity does not participate in semantic fingerprint calculation.

---

# 42. Plan Reuse

Normal Repost continues to use the same immutable prepared plan:

```text
plan
 ├── prepare_establish
 └── establish
```

No second preparation occurs.

Recovery does not use the original in-memory plan.

Instead:

```text
E.descriptor
    ↓
reconstructed plan
```

is used.

---

# 43. Register Participant

Register has no independent valuation-style durable operation history.

Therefore its implementation of:

```python
prepare_establish(...)
```

returns:

```python
PostingLifecycleResult(
    PostingLifecycleOutcome.SUCCESS
)
```

and its:

```python
recover(...)
```

returns success according to its existing stateless/rebuild semantics.

No Register-specific recovery persistence is introduced in Slice 10.7.

---

# 44. Composite Coordinator

`CompositePostingResultCoordinator` adds:

```python
def prepare_establish(...):
    ...
```

and:

```python
def recover(...):
    ...
```

Both use existing participant ordering.

The composite coordinator remains orchestration-only.

It does not:

* persist state;
* compensate previous participants;
* inspect valuation facts;
* create transactions.

---

# 45. Standard Composition

Standard composition must wire:

```text
PostingEngine
    ↓
CompositePostingResultCoordinator
    ├── Register participant
    └── ValuationPostingCoordinator
             ↓
        ValuationLifecycleCoordinator
             ↓
        ValuationOperationRecoveryService
             ↓
        DefaultValuationRebuilder
```

No separate Standard-specific recovery implementation is required.

---

# 46. Public Exports

The following public APIs must be exported from their appropriate package boundaries.

### Posting

```python
PostingRecoveryService
DefaultPostingRecoveryService
```

if concrete implementation is part of the public Standard composition surface.

### Valuation

```python
ValuationEstablishPreparationOutcome
ValuationEstablishPreparationResult
```

The existing:

```python
ValuationOperationRecoveryService
ValuationRecoveryResult
ValuationEstablishRecoveryDescriptor
```

remain publicly available where already established by previous slices.

---

# 47. Recovery Matrix

The final API must support:

| State                                  | `R`     | `E`            | Recovery                                                 |
| -------------------------------------- | ------- | -------------- | -------------------------------------------------------- |
| Before REMOVE                          | absent  | intent present | do not establish; lifecycle not recoverable as completed |
| REMOVE indeterminate                   | present | intent present | recover `R`                                              |
| REMOVE success, ESTABLISH not executed | success | intent present | recover `E`                                              |
| ESTABLISH indeterminate                | success | present        | recover `E`                                              |
| ESTABLISH partial                      | success | present        | reconcile `E`                                            |
| ESTABLISH complete                     | success | present        | return SUCCESS                                           |
| Both complete                          | success | success        | return SUCCESS                                           |
| Repeated recovery                      | success | success        | idempotent SUCCESS                                       |

---

# 48. Critical Invariant

The following invariant becomes explicit:

> `ValuationOperationRecord(E)` must exist before `ValuationOperationRecord(R)` can successfully represent a completed Repost REMOVE phase.

In implementation terms:

```text
prepare_establish(E)
    MUST precede
remove(R)
```

for Repost.

---

# 49. Failure Matrix

| Operation          | Failure       | Continue? | Recovery             |
| ------------------ | ------------- | --------: | -------------------- |
| prepare            | FAILURE       |        No | Not required         |
| prepare_establish  | FAILURE       |        No | No REMOVE            |
| prepare_establish  | INDETERMINATE |        No | Inspect `E` later    |
| remove             | FAILURE       |        No | No ESTABLISH         |
| remove             | INDETERMINATE |        No | Recover `R`          |
| establish          | FAILURE       |        No | Recover `E`          |
| establish          | INDETERMINATE |        No | Recover `E`          |
| recovery REMOVE    | FAILURE       |        No | Retry recovery later |
| recovery REMOVE    | INDETERMINATE |        No | Retry recovery later |
| recovery ESTABLISH | FAILURE       |        No | Retry recovery later |
| recovery ESTABLISH | INDETERMINATE |        No | Retry recovery later |

---

# 50. Historical Immutability

No API introduced by this slice may mutate or delete:

```text
ValuationFact
```

The only authoritative mutation is append-only persistence of new facts.

Derived state remains rebuildable.

---

# 51. Derived State

No new:

```text
RecoveryRebuilder
PostingRebuilder
RepostRebuilder
```

is introduced.

Recovery ultimately invokes:

```python
DefaultValuationRebuilder.rebuild()
```

through the existing unified valuation recovery path.

---

# 52. Recovery Idempotency

The following sequence must converge:

```python
posting.recover(P)
posting.recover(P)
posting.recover(P)
```

After successful completion:

```text
R facts = exactly expected
E facts = exactly expected
derived state = deterministic
operation records = unchanged
historical facts = unchanged
```

---

# 53. No Event Duplication

The recovery API itself does not publish:

```text
DocumentReposted
```

Therefore:

```python
recover(P)
```

is not an event-publication API.

Existing successful synchronous `repost()` remains the event boundary.

A future event-delivery slice may address crash-after-success-before-publication if concrete persistence guarantees require it.

---

# 54. Test API Requirements

The implementation must add tests for:

## Operation registration

* ESTABLISH intent record created before REMOVE;
* identical registration is idempotent;
* conflicting registration fails;
* registration indeterminate semantics;
* descriptor equals prepared plan semantics.

## Repost

* normal repost registers ESTABLISH before REMOVE;
* successful repost still creates exactly one ESTABLISH record;
* prepared plan is reused by establish;
* REMOVE failure prevents ESTABLISH execution;
* REMOVE indeterminate prevents ESTABLISH execution.

## Recovery

* recover REMOVE;
* recover ESTABLISH;
* recover after REMOVE success and ESTABLISH not executed;
* recover partial ESTABLISH facts;
* recover indeterminate ESTABLISH;
* repeated recovery;
* already-completed recovery;
* missing REMOVE operation;
* missing ESTABLISH operation;
* conflicting operation semantics.

## Immutability

* old valuation facts unchanged;
* reversal facts remain immutable;
* new valuation facts are append-only.

## Derived state

* recovery rebuild produces the same state as successful normal Repost;
* repeated recovery does not alter the final state.

## Events

* recovery does not publish a second `DocumentReposted`;
* normal successful Repost event behavior remains unchanged.

---

# 55. Implementation Order

Implementation should proceed in this order:

### Step 1 — Valuation operation preparation

Add:

```python
ValuationEstablishPreparationOutcome
ValuationEstablishPreparationResult
```

and:

```python
DefaultValuationCoordinator.prepare_establish()
```

Refactor operation construction so both `prepare_establish()` and `establish()` share it.

---

### Step 2 — Posting participant API

Add:

```python
prepare_establish()
```

to:

```text
PostingResultParticipant
PostingResultCoordinator
CompositePostingResultCoordinator
```

---

### Step 3 — Valuation Posting Coordinator

Implement:

```python
ValuationPostingCoordinator.prepare_establish()
```

using deterministic ESTABLISH child identity.

---

### Step 4 — Repost lifecycle

Change:

```text
prepare → remove → establish
```

to:

```text
prepare
→ prepare_establish
→ remove
→ establish
```

while preserving the same prepared plan.

---

### Step 5 — Recovery API

Add:

```python
recover()
```

to Posting participant/coordinator layers.

---

### Step 6 — Valuation recovery delegation

Implement:

```python
ValuationPostingCoordinator.recover()
```

using:

```text
R → E
```

and the existing `ValuationOperationRecoveryService`.

---

### Step 7 — Public Posting recovery

Add:

```python
PostingEngine.recover(operation_identity)
```

without generating a new operation identity.

---

### Step 8 — Tests

Implement the complete recovery matrix and regression suite.

---

# 56. Quality Gate

Slice 10.7 is complete only when:

```text
pytest -q
ruff check .
black --check .
mypy src
```

all pass.

Additionally:

* no historical valuation facts are modified/deleted;
* repeated recovery converges;
* normal Repost remains deterministic;
* ESTABLISH intent is durable before REMOVE;
* no Posting operation persistence exists;
* no mutable Posting lifecycle state exists;
* no second derived-state rebuild mechanism exists.

---

# 57. Final API Summary

The resulting public lifecycle is:

```text
PostingEngine.post()
PostingEngine.unpost()
PostingEngine.repost()
PostingEngine.recover(operation_identity)
```

Posting coordination:

```python
prepare(...)
prepare_establish(...)
establish(...)
remove(...)
recover(...)
```

Valuation lifecycle:

```python
prepare_establish(...)
establish(...)
remove(...)
recover(...)
```

Valuation recovery remains:

```python
ValuationOperationRecoveryService.recover(...)
```

and derived-state recovery remains:

```python
DefaultValuationRebuilder.rebuild()
```

---

# 58. Final Architecture

```text
                         PostingEngine
                              │
                ┌─────────────┴─────────────┐
                │                           │
             repost(P)                  recover(P)
                │                           │
                ▼                           ▼
             prepare                 PostingRecoveryService
                │                           │
                ▼                           ▼
       prepare_establish              Composite Coordinator
                │                           │
                ▼                           ▼
      ESTABLISH intent                    participants
                │                           │
                ▼                           ▼
             remove                   ValuationParticipant
                │                           │
                ▼                           ├──────────────┐
             establish                     │              │
                                           ▼              ▼
                                      recover(R)      recover(E)
                                           │              │
                                           └──────┬───────┘
                                                  ▼
                              ValuationOperationRecoveryService
                                                  │
                                                  ▼
                                   authoritative valuation facts
                                                  │
                                                  ▼
                                    DefaultValuationRebuilder
```

The authoritative persistence remains:

```text
ValuationOperationRecord
ValuationFact
```

There is no:

```text
PostingOperationRecord
PostingOperationPersistence
PostingLifecycleState
```

---

# 59. Approval Criteria

This Concrete API Design is ready for implementation when the following are explicitly accepted:

1. `prepare_establish()` as a new lifecycle operation;
2. durable ESTABLISH intent before REMOVE;
3. unchanged `ValuationOperationRecord` structure;
4. unchanged `ValuationEstablishRecoveryDescriptor` structure;
5. Posting-level `recover(operation_identity)`;
6. valuation recovery order `REMOVE → ESTABLISH`;
7. reuse of existing `ValuationOperationRecoveryService`;
8. reuse of `DefaultValuationRebuilder`;
9. no Posting persistence;
10. no mutable Posting lifecycle state;
11. no event persistence addition;
12. no cross-subsystem transaction semantics;
13. `PostingEngine.recover()` does not generate a new operation identity;
14. normal Repost remains `prepare → prepare_establish → remove → establish`;
15. historical valuation facts remain immutable.

**Status after approval:** Approved for Implementation.
