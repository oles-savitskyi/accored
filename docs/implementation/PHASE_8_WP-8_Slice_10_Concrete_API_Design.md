# PHASE 8 WP-8 Slice 10 — Concrete API Design

**Status:** Approved for Implementation
**Phase:** Phase 8 — Valuation Lifecycle Completion
**Work Package:** WP-8 — Reversal / Repost / Recovery
**Slice:** #10 — Full Lifecycle, Repost and Recovery Integration

---

## 1. Purpose

Slice #10 completes the valuation lifecycle across:

* Post / Establish;
* Unpost / Remove;
* Repost;
* recovery after `FAILURE` and `INDETERMINATE`;
* operation identity propagation;
* ESTABLISH recovery;
* REMOVE recovery;
* Repost recovery;
* derived-state rebuild;
* composite Posting integration;
* event correctness;
* historical fact immutability.

The implementation must preserve the architectural principles established by WP-8 and Slice #9:

1. valuation facts are append-only historical facts;
2. historical valuation facts are never mutated or deleted;
3. reversal is represented by new immutable facts;
4. derived cost movements and balances are reconstructible from authoritative valuation facts;
5. recovery is deterministic and idempotent;
6. persistence indeterminacy must be explicitly represented;
7. Posting remains generic and valuation-agnostic;
8. no cross-subsystem transaction is assumed;
9. lifecycle state is derived from authoritative operation records and facts rather than stored as mutable parent state.

---

# 2. Architectural Decisions Fixed by This API

## 2.1 Repost ordering

The lifecycle order is:

```text
prepare(new)
    ↓
remove(old)
    ↓
establish(new)
```

This order is authoritative.

The reason for preparing first is that deterministic validation/planning failure for the replacement document must not destroy a successfully posted existing document.

The apparent conflict with FIFO semantics is resolved by introducing a **read-only projected valuation preparation state**.

The replacement plan is therefore prepared against:

```text
current authoritative valuation state
        − effective valuation effect of old document
```

without mutating persistence.

Actual persistence remains:

```text
prepare
remove
establish
```

---

## 2.2 No separate Posting operation persistence

Slice #10 does **not** introduce:

```text
PostingOperationRecord
PostingOperationPersistence
```

The authoritative persistent operation history remains the existing valuation operation history.

A Posting operation identity is a lifecycle correlation identity from which participant-specific operation identities are deterministically derived.

This avoids two competing authoritative operation stores and eliminates a new parent/child persistence consistency problem.

---

## 2.3 No authoritative mutable lifecycle state

Slice #10 does not introduce a persistent:

```text
PostingLifecycleState
```

or equivalent mutable aggregate state.

The effective lifecycle state is derived from:

* participant operation records;
* valuation facts;
* recovery results;
* rebuilt derived state.

---

## 2.4 ESTABLISH must be independently recoverable

An ESTABLISH operation cannot be recovered from a fingerprint alone.

The persistent operation record therefore contains a concrete, persistence-safe recovery descriptor containing the original semantic valuation plan.

The descriptor is sufficient to reconstruct the intended authoritative valuation facts without relying on transient in-memory planning state.

---

# 3. Posting Operation Identity

## 3.1 Value object

```python
@dataclass(frozen=True, slots=True)
class PostingOperationIdentity:
    value: str
```

The value is opaque.

It is not interpreted by Posting participants.

---

## 3.2 Operation types

```python
class PostingOperationType(StrEnum):
    ESTABLISH = "establish"
    REMOVE = "remove"
    REPOST = "repost"
```

The type describes the lifecycle operation initiated at the Posting boundary.

Participant-specific operation types remain participant-owned.

---

# 4. Posting Operation Identity Factory

Identity generation is not embedded in the value object.

```python
class PostingOperationIdentityFactory(Protocol):
    def new(self) -> PostingOperationIdentity: ...
```

The standard implementation generates a fresh opaque identity.

Identity generation is performed exactly once for a logical Posting lifecycle operation.

---

# 5. Deterministic Child Operation Identity

Participant operation identities are derived from the parent Posting operation identity.

A deterministic factory is introduced:

```python
class PostingParticipantOperationIdentityFactory(Protocol):
    def derive(
        self,
        posting_identity: PostingOperationIdentity,
        participant_name: str,
        operation_type: str,
    ) -> ValuationOperationIdentity: ...
```

The concrete implementation must be deterministic.

For identical:

```text
posting identity
+ participant identity
+ participant operation type
```

it must produce the same child operation identity.

This is required for recovery.

---

# 6. Posting Lifecycle API

The existing lifecycle result remains:

```python
class PostingLifecycleOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class PostingLifecycleResult:
    outcome: PostingLifecycleOutcome
    error: Exception | None = None
```

The result does not contain the operation identity.

The caller already owns the identity used for the lifecycle invocation.

---

# 7. Posting Participant API

The generic participant contract is extended to receive the parent lifecycle identity.

```python
class PostingResultParticipant(Protocol):
    def prepare(
        self,
        document: object,
        movement_set: MovementSet,
        operation_identity: PostingOperationIdentity,
    ) -> object: ...

    def establish(
        self,
        document: object,
        movement_set: MovementSet,
        plan: object,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...

    def remove(
        self,
        document: object,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...
```

The operation identity is generic.

A participant may ignore it if its implementation does not require durable operation identity.

Valuation uses it to derive participant-specific valuation operation identities.

---

# 8. Posting Coordinator API

```python
class PostingResultCoordinator(Protocol):
    def prepare(
        self,
        document: object,
        movement_set: MovementSet,
        operation_identity: PostingOperationIdentity,
    ) -> PostingResultPlan: ...

    def establish(
        self,
        document: object,
        movement_set: MovementSet,
        plan: PostingResultPlan,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...

    def remove(
        self,
        document: object,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...
```

The composite coordinator preserves:

* participant order;
* short-circuit-on-failure semantics;
* no transaction assumptions.

---

# 9. Posting Engine Lifecycle

## 9.1 Post

```text
generate PostingOperationIdentity
        ↓
handler.post()
        ↓
validate movement
        ↓
coordinator.prepare(..., identity)
        ↓
coordinator.establish(..., identity)
        ↓
DocumentPosted
```

A `DocumentPosted` event is emitted only after successful lifecycle completion.

---

## 9.2 Unpost

```text
generate PostingOperationIdentity
        ↓
coordinator.remove(..., identity)
        ↓
DocumentUnposted
```

The event is emitted only after successful removal.

---

## 9.3 Repost

```text
generate PostingOperationIdentity
        ↓
handler.post()
        ↓
validate replacement movement
        ↓
coordinator.prepare(..., identity)
        ↓
coordinator.remove(..., identity)
        ↓
coordinator.establish(..., identity)
        ↓
DocumentReposted
```

If preparation fails:

```text
old state remains untouched
```

If removal fails:

```text
establish is not executed
```

If removal is indeterminate:

```text
establish is not executed
recovery is required
```

If establish fails or becomes indeterminate after successful removal:

```text
recovery resumes establish
remove is not repeated
```

---

# 10. Valuation Preparation Context

A new immutable preparation context is introduced:

```python
@dataclass(frozen=True, slots=True)
class ValuationPreparationContext:
    operation_identity: ValuationOperationIdentity
    replacement_document_identity: Identifier | None = None
```

### Normal Post

```text
replacement_document_identity = None
```

Preparation reads the current authoritative state.

### Repost

```text
replacement_document_identity = old_document_identity
```

Preparation must use a read-only projected state equivalent to:

```text
authoritative current state
− effective valuation effect of old document
```

No persistence mutation is allowed during projection.

---

# 11. Projected Valuation Preparation State

The valuation engine must not directly perform a removal during preparation.

Instead, preparation receives a read-only valuation-layer view.

Conceptually:

```python
class ValuationPreparationState(Protocol):
    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]: ...
```

The state is constructed from authoritative valuation facts.

For Repost, the projected state excludes the effective contribution of the document being replaced.

The projection must account for both:

* layers established by the old document;
* consumption effects attributable to the old document.

The projected state must be semantically equivalent to the state obtained after successful removal, while remaining completely non-mutating.

The exact internal implementation may reuse existing fact-selection and valuation-layer reconstruction mechanisms.

It must not create authoritative valuation facts.

---

# 12. Valuation Engine API

The preparation API becomes:

```python
class ValuationEngine(Protocol):
    def prepare(
        self,
        movement_set: MovementSet,
        context: ValuationPreparationContext,
    ) -> ValuationPlan: ...
```

The returned plan must be deterministic for identical:

```text
movement set
+
preparation context
+
authoritative source state
```

except for intentionally opaque persistence identities.

---

# 13. Deterministic Planned Identities

The current use of random:

```python
Identifier.new()
```

inside valuation preparation is not permitted for operation-sensitive planned identities.

Planned layer references and other operation-sensitive identities must be derived deterministically from:

```text
ValuationOperationIdentity
+
semantic position/source identity
```

The identity derivation must not change the semantic fingerprint.

This produces two deliberately separate concepts:

### Semantic identity

Determines whether two operations mean the same thing.

### Persistence identity

Determines the stable identity of the resulting authoritative fact.

The operation identity may participate in persistence identity derivation but must not make semantically identical plans appear semantically different merely because they belong to different lifecycle attempts.

---

# 14. Valuation Lifecycle API

The lifecycle interface becomes:

```python
class ValuationLifecycleCoordinator(Protocol):
    def establish(
        self,
        plan: ValuationPlan,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationEstablishmentResult: ...

    def remove(
        self,
        document_identity: Identifier,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRemovalResult: ...

    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult: ...
```

---

# 15. Valuation Operation Identity

The existing value object remains:

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationIdentity:
    value: str
```

No lifecycle semantics are embedded in the value itself.

The identity is opaque and stable across retries.

---

# 16. Valuation Operation Types

```python
class ValuationOperationType(StrEnum):
    ESTABLISH = "establish"
    REMOVE = "remove"
```

A Posting `REPOST` operation therefore maps to two valuation child operations:

```text
PostingOperationIdentity
        │
        ├── valuation REMOVE identity
        │
        └── valuation ESTABLISH identity
```

The identities are derived deterministically.

---

# 17. Valuation Operation Record

The existing record is extended with a concrete ESTABLISH recovery descriptor.

```python
@dataclass(frozen=True, slots=True)
class ValuationEstablishRecoveryDescriptor:
    document_identity: Identifier
    operations: tuple[ValuationPlanOperation, ...]
```

The operation record becomes conceptually:

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

Rules:

### ESTABLISH

```text
establish_descriptor != None
target_fact_identities may be empty
```

### REMOVE

```text
establish_descriptor == None
target_fact_identities contains canonical removal targets
```

The descriptor is persisted as part of the authoritative operation record.

---

# 18. Operation Persistence Semantics

Existing persistence semantics remain authoritative:

### Same identity + same semantics

```text
idempotent success
```

### Same identity + different semantics

```text
conflict
```

### `find(identity) == None`

```text
authoritative NOT_FOUND
```

No recovery implementation may infer that an absent operation record represents a successful operation.

---

# 19. ESTABLISH Fingerprint

The ESTABLISH semantic fingerprint is derived from the canonical semantic content of:

```text
document identity
+
plan operations
```

It must not include the randomly generated Posting or Valuation operation identity.

Equivalent semantic plans therefore have equivalent fingerprints.

---

# 20. REMOVE Fingerprint

The REMOVE fingerprint is derived from the canonical ordered set of target valuation fact identities.

Target identity ordering is deterministic.

The canonical representation must not depend on:

* persistence enumeration order;
* hash-map order;
* database ordering;
* incidental object ordering.

---

# 21. Establish Lifecycle

`DefaultValuationCoordinator.establish(...)` performs:

```text
validate plan
    ↓
derive / validate operation identity
    ↓
build ESTABLISH operation record
    ↓
persist operation record
    ↓
construct authoritative valuation facts
    ↓
reconcile / append facts
    ↓
derive cost movements
    ↓
persist / reconcile cost movements
    ↓
rebuild / reconcile balances
    ↓
SUCCESS
```

The operation record is the durable description of the intended operation.

---

# 22. ESTABLISH Failure Semantics

If failure is known before authoritative persistence:

```text
FAILURE
```

If fact persistence reports an indeterminate result:

```text
INDETERMINATE
```

Recovery must inspect authoritative persistence rather than assume whether the fact append succeeded.

Repeated recovery must converge.

---

# 23. ESTABLISH Recovery

The unified recovery service remains:

```python
class ValuationOperationRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult: ...
```

Recovery dispatches by:

```python
operation_record.operation_type
```

For `ESTABLISH`:

```text
load operation record
        ↓
load establish descriptor
        ↓
reconstruct intended valuation facts
        ↓
reconcile facts
        ↓
rebuild / reconcile derived state
        ↓
SUCCESS
```

No original transient `ValuationPlan` object is required.

---

# 24. REMOVE Lifecycle

Removal remains reversal-based.

The coordinator:

1. enumerates authoritative valuation facts;
2. selects active removable facts;
3. excludes historical reversal facts;
4. excludes facts already reversed;
5. canonicalizes target identities;
6. persists the REMOVE operation record;
7. creates reversal facts;
8. reconciles reversal facts;
9. reconciles derived cost movements;
10. rebuilds balances.

No original fact is mutated or deleted.

---

# 25. REMOVE Recovery

REMOVE recovery uses the existing deterministic fact recovery service.

```text
load REMOVE operation record
        ↓
load canonical target identities
        ↓
load target facts
        ↓
construct reversal facts
        ↓
reconcile reversal facts
        ↓
rebuild / reconcile derived state
        ↓
SUCCESS
```

Repeated recovery must not create duplicate reversal facts.

---

# 26. Reversal Semantics for Multiple Targets

A single REMOVE operation may target multiple historical valuation facts.

The operation record therefore stores:

```python
target_fact_identities: tuple[Identifier, ...]
```

in canonical order.

Each target fact receives its own deterministic reversal fact.

The reversal identity is derived from the original fact identity and the removal operation semantics.

This guarantees:

* one reversal per target;
* deterministic retry;
* no duplicate reversal;
* no historical mutation.

---

# 27. Repost Child Operation Identities

For a Posting `REPOST` identity:

```text
P
```

the valuation participant derives:

```text
R = derive(P, "valuation", "remove")
E = derive(P, "valuation", "establish")
```

The identities are deterministic.

Therefore recovery can determine:

```text
REMOVE already successful?
ESTABLISH already successful?
ESTABLISH indeterminate?
```

without a separate persistent Posting operation record.

---

# 28. Repost Preparation

The valuation Posting coordinator receives the parent Posting operation identity.

It derives the ESTABLISH valuation identity before preparation.

It then constructs:

```python
ValuationPreparationContext(
    operation_identity=establish_identity,
    replacement_document_identity=old_document_identity,
)
```

The engine prepares the replacement plan against the projected post-removal state.

This ensures FIFO and other state-dependent valuation algorithms see the state that will exist after the old valuation effect is removed.

---

# 29. Repost Establishment

After successful REMOVE:

```text
old valuation effect no longer contributes
```

The already prepared replacement plan is established.

The establishment operation uses the same valuation ESTABLISH identity generated before preparation.

This guarantees that:

```text
prepare
```

and:

```text
recover establish
```

refer to the same logical operation.

---

# 30. Repost Recovery

Recovery derives the two child identities from the parent Posting identity.

### Case A — REMOVE incomplete

Recover REMOVE.

Do not establish replacement state until REMOVE reaches `SUCCESS`.

### Case B — REMOVE successful, ESTABLISH absent/incomplete

Skip REMOVE.

Recover ESTABLISH directly.

### Case C — both successful

Return:

```text
SUCCESS
```

### Case D — conflicting operation semantics

Return:

```text
FAILURE
```

and preserve authoritative historical state.

---

# 31. Posting Recovery API

A generic recovery boundary may be introduced:

```python
class PostingRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...
```

The service does not persist parent lifecycle state.

It derives participant operation identities and delegates recovery to participant-specific recovery mechanisms.

---

# 32. Valuation Posting Coordinator

The valuation participant becomes conceptually:

```python
class ValuationPostingCoordinator:
    def prepare(
        self,
        document: Document,
        movement_set: MovementSet,
        operation_identity: PostingOperationIdentity,
    ) -> ValuationPlan: ...

    def establish(
        self,
        document: Document,
        movement_set: MovementSet,
        plan: ValuationPlan,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...

    def remove(
        self,
        document: Document,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult: ...
```

Responsibilities:

* validate document/movement relationship;
* derive valuation child identities;
* construct preparation context;
* delegate planning to `ValuationEngine`;
* delegate lifecycle operations to `ValuationLifecycleCoordinator`;
* map valuation lifecycle outcomes into generic Posting lifecycle outcomes.

It does not expose valuation internals to `PostingEngine`.

---

# 33. Register Participant

The register participant receives the generic Posting operation identity but does not require valuation semantics.

Its implementation remains focused on:

```text
register movement persistence
+
register mutation
+
register recovery
```

No valuation dependency is introduced into the register subsystem.

---

# 34. Composite Posting Coordinator

The composite coordinator remains transaction-neutral.

For `establish`:

```text
participant 1
    ↓
participant 2
    ↓
...
```

Processing stops at the first non-success result.

For `remove` the same short-circuit rule applies.

The coordinator does not attempt rollback.

Recovery is a separate lifecycle operation.

---

# 35. Derived-State Recovery

Slice #10 must reuse the Slice #9 rebuild implementation.

The authoritative source remains:

```text
valuation facts
```

Derived state remains:

```text
valuation facts
    ↓
CostMovement projection
    ↓
CostMovement persistence reconciliation
    ↓
balance rebuild
```

The implementation must reuse:

```python
DefaultValuationRebuilder
```

and its existing deterministic projection/reconciliation mechanisms.

No second derived-state rebuild algorithm is introduced.

---

# 36. Derived-State Invariants

After successful lifecycle completion:

```text
persisted derived state
==
deterministic projection(authoritative valuation facts)
```

After recovery:

```text
recovered derived state
==
fresh rebuild(authoritative valuation facts)
```

A recovery implementation must therefore never rely on an assumed previous derived-state state.

---

# 37. Historical Immutability

The following operations are forbidden:

```text
UPDATE valuation fact
DELETE valuation fact
UPDATE historical valuation meaning
```

Unpost and Repost operate exclusively through:

```text
new reversal facts
new establishment facts
```

---

# 38. Event Semantics

Existing Posting events remain lifecycle completion events.

### Post

```text
DocumentPosted
```

only after successful establishment.

### Unpost

```text
DocumentUnposted
```

only after successful removal.

### Repost

```text
DocumentReposted
```

only after:

```text
REMOVE == SUCCESS
+
ESTABLISH == SUCCESS
```

No lifecycle event represents an intermediate `INDETERMINATE` state.

No event is emitted merely because recovery was attempted.

The existing event publisher remains unchanged unless implementation inspection demonstrates a concrete duplicate-publication problem that cannot be solved at the existing Posting lifecycle boundary.

Slice #10 does not introduce a speculative event persistence subsystem.

---

# 39. Idempotency Rules

## 39.1 Establish

Repeated establish with the same operation identity:

```text
same semantics → idempotent
different semantics → conflict
```

## 39.2 Remove

Repeated remove with the same operation identity:

```text
same target set → idempotent
different target set → conflict
```

## 39.3 Recovery

Repeated recovery:

```text
converges to SUCCESS
```

when authoritative persistence contains sufficient information to complete the operation.

---

# 40. Failure Model

The implementation distinguishes:

### FAILURE

The operation is known not to have completed.

Examples:

* invalid plan;
* semantic conflict;
* deterministic validation error.

### INDETERMINATE

Persistence outcome cannot be established.

Examples:

* append timeout;
* transport failure after write may have occurred;
* storage provider cannot establish whether a write committed.

### SUCCESS

Authoritative persistence and required derived state are reconciled successfully.

---

# 41. Recovery Does Not Guess

Recovery must never interpret:

```text
missing operation record
```

as:

```text
operation succeeded
```

Nor may it interpret:

```text
missing fact
```

as proof that an earlier indeterminate append did not occur.

The authoritative persistence contract determines whether the operation can be safely reconciled.

---

# 42. Rebuild Equivalence

For any authoritative valuation fact set `F`:

```text
rebuild(F)
```

must produce the same derived valuation state as successful lifecycle processing over `F`.

Therefore:

```text
lifecycle success
==
facts + deterministic derived state
```

and:

```text
recovery success
==
facts + deterministic derived state
```

---

# 43. Recovery State Matrix

| Situation                                             | Required action                       |
| ----------------------------------------------------- | ------------------------------------- |
| Establish failed before persistence                   | return `FAILURE`                      |
| Establish persistence indeterminate                   | return `INDETERMINATE`, recover later |
| Establish operation exists, facts partially persisted | reconcile missing facts               |
| Establish facts complete, derived state incomplete    | rebuild derived state                 |
| Remove failed before persistence                      | return `FAILURE`                      |
| Remove persistence indeterminate                      | return `INDETERMINATE`                |
| Remove operation exists, reversals partial            | reconcile missing reversals           |
| Remove reversals complete, derived state incomplete   | rebuild derived state                 |
| Repost prepare fails                                  | old state unchanged                   |
| Repost remove fails                                   | do not establish replacement          |
| Repost remove indeterminate                           | recover remove first                  |
| Repost remove successful, establish incomplete        | recover establish only                |
| Repost both children successful                       | return success                        |
| Operation identity conflict                           | `FAILURE`                             |

---

# 44. Public API Surface

The following types are public API where they cross package boundaries:

```text
PostingOperationIdentity
PostingOperationType
PostingOperationIdentityFactory
PostingParticipantOperationIdentityFactory
PostingLifecycleOutcome
PostingLifecycleResult
PostingRecoveryService

ValuationPreparationContext
ValuationOperationIdentity
ValuationOperationType
ValuationEstablishRecoveryDescriptor
ValuationOperationRecord
ValuationOperationPersistence
ValuationLifecycleCoordinator
ValuationOperationRecoveryService
ValuationEstablishmentOutcome
ValuationEstablishmentResult
ValuationRemovalOutcome
ValuationRemovalResult
ValuationRecoveryResult
```

Internal projection/reconciliation helpers remain internal unless required by an existing package boundary.

---

# 45. Compatibility Requirements

Slice #10 must preserve existing public semantics unless explicitly changed above.

In particular:

* existing valuation persistence protocols remain valid;
* existing immutable fact representation remains valid;
* existing Slice #9 rebuild APIs remain valid;
* existing register APIs remain valuation-agnostic;
* generic Posting APIs remain free of valuation-specific types;
* existing lifecycle outcome semantics remain `SUCCESS / FAILURE / INDETERMINATE`.

---

# 46. Implementation Sequence

Implementation must proceed in the following order.

## Slice 10.1 — Identity propagation

Implement:

* Posting operation identity;
* identity factory;
* deterministic child identity factory;
* Posting coordinator API propagation;
* participant API propagation.

Gate:

```text
pytest
ruff
black
mypy
```

---

## Slice 10.2 — Deterministic valuation preparation

Implement:

* `ValuationPreparationContext`;
* deterministic planned identities;
* operation-sensitive identity derivation;
* preparation context propagation.

Gate:

```text
pytest
ruff
black
mypy
```

---

## Slice 10.3 — Projected Repost preparation state

Implement:

* read-only projected valuation state;
* exclusion of old document's effective valuation contribution;
* FIFO correctness under `prepare → remove → establish`.

Tests must demonstrate:

```text
prepare(new)
```

produces the same effective valuation plan that would be produced after:

```text
remove(old)
```

without mutating persistence.

---

## Slice 10.4 — ESTABLISH recovery descriptor

Implement:

* `ValuationEstablishRecoveryDescriptor`;
* operation record extension;
* persistence serialization;
* establish recovery reconstruction.

---

## Slice 10.5 — Unified valuation recovery

Implement:

* ESTABLISH dispatch;
* existing REMOVE recovery;
* derived-state reconciliation through `DefaultValuationRebuilder`;
* repeated recovery convergence.

---

## Slice 10.6 — Repost lifecycle

Implement:

```text
prepare
→ remove
→ establish
```

with deterministic child identities.

Test:

* successful repost;
* preparation failure preserving old state;
* removal failure;
* removal indeterminate;
* establish failure;
* establish indeterminate.

---

## Slice 10.7 — Repost recovery

Implement:

* child identity derivation;
* remove-first recovery;
* establish-only recovery after successful remove;
* already-completed detection;
* conflict handling.

---

## Slice 10.8 — Posting integration

Integrate:

* generic Posting lifecycle identity;
* valuation participant;
* register participant;
* composite coordinator;
* PostingEngine.

Verify Posting remains valuation-agnostic.

---

## Slice 10.9 — Events

Verify:

* exactly one success event per successful logical lifecycle;
* no event for failed/indeterminate intermediate lifecycle;
* retry/recovery does not produce a duplicate lifecycle completion event under the existing event boundary.

Only introduce additional event persistence/idempotency machinery if a concrete architectural gap is demonstrated.

---

## Slice 10.10 — Full integration and documentation

Verify:

* Post;
* Unpost;
* Repost;
* recovery;
* rebuild;
* register integration;
* valuation integration;
* historical immutability;
* event behavior.

Then reconcile all WP-8 documentation.

---

# 47. Required Test Matrix

## Establish

* successful establish;
* repeated establish;
* semantic conflict;
* persistence failure;
* persistence indeterminate;
* partial fact persistence;
* derived-state failure;
* recovery;
* repeated recovery.

## Remove

* successful remove;
* repeated remove;
* multiple target removal;
* repeated reversal;
* persistence failure;
* persistence indeterminate;
* partial reversal persistence;
* derived-state recovery.

## Repost

* successful repost;
* FIFO replacement;
* preparation failure preserves old state;
* removal failure;
* removal indeterminate;
* establishment failure;
* establishment indeterminate;
* remove succeeded / establish incomplete;
* recovery after partial establish;
* repeated recovery;
* conflicting child operation identity.

## Rebuild

* rebuild after successful Post;
* rebuild after Unpost;
* rebuild after Repost;
* rebuild after incomplete derived persistence;
* rebuild equivalence after recovery.

## Integration

* Register + Valuation successful Post;
* Register + Valuation successful Unpost;
* Register + Valuation successful Repost;
* participant short-circuit;
* partial participant completion;
* recovery without transaction assumptions.

## Immutability

Tests must explicitly verify:

```text
historical valuation facts remain byte-for-byte / semantically unchanged
```

after:

* Unpost;
* Repost;
* recovery;
* rebuild.

---

# 48. Non-Goals

Slice #10 does not introduce:

* distributed transactions;
* transaction managers;
* two-phase commit;
* a persistent Posting aggregate state;
* a second operation-history store;
* speculative event persistence;
* generic valuation abstractions outside `accore.platform.valuation`;
* mutation or deletion of historical valuation facts;
* a second derived-state rebuild implementation.

---

# 49. Final Invariants

The implementation is considered complete only if all of the following hold.

### I1 — Historical immutability

```text
No historical valuation fact is mutated or deleted.
```

### I2 — Deterministic operation identity

```text
Same logical lifecycle
→ same operation identity across retries.
```

### I3 — Deterministic child identity

```text
Same Posting identity + participant + operation type
→ same participant operation identity.
```

### I4 — Idempotency

```text
Repeated operation with identical semantics
→ no duplicate authoritative effect.
```

### I5 — Conflict detection

```text
Same identity + different semantics
→ explicit conflict.
```

### I6 — Repost ordering

```text
prepare → remove → establish
```

is the only supported lifecycle ordering.

### I7 — Repost planning correctness

```text
Repost preparation
```

must observe a read-only state equivalent to:

```text
state after removal of old document
```

### I8 — Recovery completeness

```text
Every persisted ESTABLISH and REMOVE operation
```

contains enough authoritative information to recover its intended effect.

### I9 — Derived-state determinism

```text
derived state
==
projection(authoritative valuation facts)
```

### I10 — Recovery convergence

```text
recovery(recovery(...recovery(operation)))
```

converges to the same successful authoritative state.

### I11 — Posting neutrality

```text
PostingEngine
```

contains no valuation-specific logic.

### I12 — No transaction assumption

Correctness does not depend on a transaction spanning:

```text
Posting
Register
Valuation
Persistence
Events
```

### I13 — Event correctness

Lifecycle completion events are emitted only after successful logical completion.

### I14 — Rebuild equivalence

```text
successful lifecycle
==
recovered lifecycle
==
fresh rebuild from authoritative valuation facts
```

---

# 50. Approval

This Concrete API Design supersedes the earlier Slice #10 draft API where they conflict.

The following decisions are final for implementation:

1. `prepare → remove → establish` is authoritative for Repost.
2. Repost preparation uses a read-only projected valuation state.
3. No separate persistent Posting operation record is introduced.
4. Posting operation identity is a correlation/idempotency identity.
5. Participant operation identities are deterministically derived from the Posting identity.
6. ESTABLISH recovery uses a concrete persisted `ValuationEstablishRecoveryDescriptor`.
7. Valuation operation records remain the authoritative durable operation history.
8. ESTABLISH and REMOVE use the unified valuation recovery service.
9. Slice #9 `DefaultValuationRebuilder` remains the sole derived-state rebuild mechanism.
10. Historical valuation facts remain immutable.
11. Posting lifecycle state is derived, not persisted as mutable parent state.
12. Event persistence/idempotency is not expanded without a demonstrated architectural requirement.

**Status: APPROVED FOR IMPLEMENTATION**
