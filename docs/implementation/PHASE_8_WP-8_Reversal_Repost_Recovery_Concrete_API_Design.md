# Phase 8 WP-8 — Reversal / Repost / Recovery

## Final Concrete API Design

**Status:** Final WP-8 Concrete API Reconciliation — Complete
**Implementation reconciliation:** WP-8 Slices 1–10.7 are implemented, tested, and quality-gated at commit `5046a9c`.

---

## 1. Purpose

WP-8 introduces the concrete API required to implement:

* immutable valuation reversal;
* idempotent unpost;
* repost as `prepare → prepare_establish → remove → establish`;
* recovery after partial persistence;
* recovery after persistence indeterminate state;
* deterministic logical-operation identity;
* deterministic valuation-fact identity;
* rebuild of derived valuation state from authoritative history;
* preservation of all historical valuation facts.

The design does **not** introduce a new valuation architecture.

It formalizes the lifecycle and recovery semantics of the existing append-only valuation architecture.

---

# 2. Authoritative State Model

The valuation subsystem has three distinct state categories.

### 2.1 Authoritative operation history

```text
ValuationOperationRecord
```

Defines that a logical valuation lifecycle operation exists and identifies its semantic content.

Operation records are immutable and append-only.

---

### 2.2 Authoritative valuation history

```text
ValuationFact
```

Represents immutable valuation facts.

Examples:

```text
ValuationLayer
ValuationConsumption
ValuationReversal
```

Valuation facts are never updated or deleted.

---

### 2.3 Derived state

```text
CostMovement
CostBalance
```

Derived state is reconstructable from authoritative operation records and valuation facts.

Derived state is therefore not historical truth.

It may be replaced or rebuilt.

---

# 3. Unified Lifecycle Outcome

All lifecycle operations use the existing three-state outcome model.

```python
class OperationOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"
```

Semantics:

### SUCCESS

The logical operation has been completely reconciled.

### FAILURE

The system knows that the requested operation did not complete and no unresolved persistence ambiguity remains.

### INDETERMINATE

The system cannot establish whether the requested persistence operation completed.

`INDETERMINATE` must never be treated as `FAILURE`.

It requires reconciliation before retry.

---

# 4. Operation Result

Lifecycle APIs return:

```python
@dataclass(frozen=True, slots=True)
class OperationResult:
    outcome: OperationOutcome
    error: Exception | None = None
```

Invariant:

```text
SUCCESS          → error is None
FAILURE          → error describes deterministic failure
INDETERMINATE   → error describes unresolved persistence state
```

---

# 5. Logical Operation Identity

Each logical lifecycle operation receives its own immutable identity.

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationIdentity:
    value: str
```

An operation identity identifies **one logical lifecycle operation**, not a document.

Therefore:

```text
POST(document A)    → operation O1
REMOVE(document A)  → operation O2
POST(document A)    → operation O3
REMOVE(document A)  → operation O4
```

These are four distinct logical operations.

---

# 6. Operation Type

```python
class ValuationOperationType(StrEnum):
    ESTABLISH = "establish"
    REMOVE = "remove"
```

---

# 7. Authoritative Operation Record

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
```

The operation record is the authoritative declaration that a logical operation exists.

It does **not** contain mutable completion status.

Current completion is derived by reconciliation between:

```text
OperationRecord
+
ValuationFacts
+
DerivedState
```

---

# 8. Operation Persistence

```python
class ValuationOperationPersistence(Protocol):
    def append(
        self,
        operation: ValuationOperationRecord,
    ) -> None:
        ...

    def find(
        self,
        identity: ValuationOperationIdentity,
    ) -> ValuationOperationRecord | None:
        ...

    def find_by_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationOperationRecord, ...]:
        ...

    def enumerate(
        self,
    ) -> tuple[ValuationOperationRecord, ...]:
        ...
```

Operation persistence is append-only.

There is no:

```text
update()
delete()
replace()
```

---

# 9. Operation Persistence Idempotency

Appending an operation record is idempotent by operation identity.

If the same identity already exists:

### Same semantic record

```text
identity equal
fingerprint equal
operation type equal
document equal
```

→ idempotent success.

### Different semantic record

```text
same identity
different fingerprint/type/document
```

→ deterministic `FAILURE`.

This is an operation-identity conflict.

---

# 10. Operation Record Reconciliation

`find()` is the authoritative reconciliation read for an operation identity.

Its contract is:

```text
record found
    → operation exists

None
    → operation does not exist

persistence/read error
    → reconciliation is INDETERMINATE
```

A persistence layer must not convert an unknown read failure into `None`.

Therefore:

```text
None ≠ unknown
```

`None` means authoritative `NOT_FOUND`.

A persistence exception means that existence cannot currently be established.

---

# 11. Operation Registration

Every lifecycle operation follows:

```text
create operation identity
        ↓
construct operation fingerprint
        ↓
append OperationRecord
        ↓
persist authoritative valuation facts
        ↓
persist/rebuild derived state
```

The operation record is always the first authoritative persistence step.

---

# 12. Partial Operation-Record Failure

If operation-record persistence returns known `FAILURE`:

```text
OperationRecord does not exist
        ↓
do not create valuation facts
        ↓
return FAILURE
```

If operation-record persistence becomes `INDETERMINATE`:

```text
operation existence unknown
        ↓
reconcile by identity
```

### Reconciliation results

```text
FOUND
    → operation exists
    → continue recovery

NOT_FOUND
    → operation does not exist
    → retry append safely

INDETERMINATE
    → existence still unknown
    → remain INDETERMINATE
```

A retry must never be performed blindly after an indeterminate operation-record append.

---

# 13. Operation Fingerprint

The fingerprint represents the semantic content of the logical operation.

The fingerprint is independent of:

* persistence order;
* database enumeration order;
* operation identity;
* generated fact storage order.

`operation_identity` is deliberately excluded from the fingerprint.

This avoids circular construction:

```text
operation identity
    ↔
fingerprint
```

---

# 14. Fingerprint Determinism

The same semantic operation must always produce the same fingerprint.

All unordered semantic collections must therefore be canonicalized before fingerprint construction.

Canonicalization must be deterministic and independent of persistence enumeration order.

---

# 15. REMOVE Target Set

A REMOVE operation contains a target set of currently effective valuation facts.

Conceptually:

```python
remove_targets: tuple[Identifier, ...]
```

The semantic meaning is:

```text
SET of target fact identities
```

The tuple is only the serialized/canonical representation.

Persistence enumeration order has no semantic meaning.

---

# 16. Canonical REMOVE Target Ordering

Before constructing the REMOVE fingerprint:

```text
target identities
        ↓
stable identity representation
        ↓
deterministic total ordering
        ↓
canonical tuple
        ↓
fingerprint
```

The canonical ordering uses the repository's canonical stable identity representation.

For the current `Identifier` contract this is:

```python
Identifier.value
```

Therefore:

```text
[F1, F2, F3]
[F3, F1, F2]
[F2, F3, F1]
```

all canonicalize to the same ordering:

```text
[F1, F2, F3]
```

provided the identifiers are ordered by their canonical identity value.

---

# 17. Duplicate REMOVE Targets

Duplicate target identities are not silently removed.

Example:

```text
[F1, F2, F1]
```

is invalid.

The operation must return deterministic `FAILURE` because duplicate targets indicate an integrity or construction error.

This prevents accidental semantic changes caused by implicit deduplication.

---

# 18. REMOVE Fingerprint

The REMOVE fingerprint is constructed from:

```text
operation_type
document_identity
canonical_target_fact_identities
```

Conceptually:

```python
fingerprint(
    operation_type=REMOVE,
    document_identity=document_identity,
    targets=canonical_targets,
)
```

`operation_identity` is not included.

Therefore the same document and the same target set always produce the same semantic fingerprint.

---

# 19. Fingerprint Stability During Recovery

Once a REMOVE operation has been registered:

```text
OperationRecord
    fingerprint
        +
    target_fact_identities
        ↓
fixed target set
```

The target set is immutable for that operation.

The fingerprint is a one-way semantic representation used for operation verification and conflict detection.
It is **not** a source from which target identities can be reconstructed.

Operation-level recovery reads:

```python
operation.target_fact_identities
```

directly from the authoritative operation record.

Recovery must **not** reselect targets from the current state and must not attempt to decode the fingerprint.

This is essential because the current state may have changed after a partial operation.

---

# 20. Facts Without Operation Record

An authoritative valuation fact containing an operation identity must have a corresponding authoritative operation record.

Therefore:

```text
operation record exists
    + facts exist
        → valid

operation record absent
    + facts absent
        → safe to retry

operation record absent
    + facts exist
        → history-integrity violation
```

The last case must not be silently repaired by creating a new operation record.

---

# 21. Deterministic Fact Identity

Lifecycle facts require deterministic identities.

```python
class ValuationFactIdentityFactory(Protocol):
    def for_operation_fact(
        self,
        operation_identity: ValuationOperationIdentity,
        fact_kind: ValuationFactType,
        semantic_key: tuple[object, ...],
    ) -> Identifier:
        ...
```

The identity is derived from:

```text
operation identity
+
fact kind
+
semantic key
```

Therefore:

```text
same operation
+
same fact kind
+
same semantic key
```

produces the same fact identity.

---

# 22. Fact Persistence Idempotency

`ValuationFactPersistence` remains append-only.

Existing contract:

```python
class ValuationFactPersistence(Protocol):
    def append(
        self,
        facts: tuple[ValuationFact, ...],
    ) -> None:
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

    def enumerate(
        self,
    ) -> tuple[ValuationFact, ...]:
        ...
```

Appending a fact with an already existing identity is idempotent if its complete semantic content is identical.

If the same identity contains different semantic content, the result is deterministic `FAILURE` due to identity conflict.

---

# 23. Operation Identity on Facts

Lifecycle-generated valuation facts carry the operation identity that produced them.

Conceptually:

```python
operation_identity: ValuationOperationIdentity
```

This permits recovery to reconcile:

```text
operation record
        ↓
expected facts
        ↓
actual facts
```

without relying on persistence order.

---

# 24. Establish API

The coordinator exposes:

```python
def establish(
    plan: ValuationPlan,
) -> OperationResult:
    ...
```

The operation performs:

```text
prepare
    ↓
create operation identity
    ↓
construct ESTABLISH fingerprint
    ↓
register OperationRecord
    ↓
derive expected valuation facts
    ↓
persist missing facts
    ↓
persist/reconcile derived results
```

---

# 25. ESTABLISH Idempotency

Repeated execution of the same logical ESTABLISH operation must not create duplicate historical effects.

If the operation identity already exists:

```text
same identity
same fingerprint
```

the operation is reconciled instead of creating another logical operation.

If some expected facts are already present:

```text
expected: F1 F2 F3
actual:   F1 F2
```

recovery persists only:

```text
F3
```

No replacement or deletion is performed.

---

# 26. REMOVE API

The coordinator exposes:

```python
def remove(
    document_identity: Identifier,
) -> OperationResult:
    ...
```

The implementation creates a distinct logical REMOVE operation.

Repeated calls are therefore distinct operations at the lifecycle level.

However, the immutable reversal invariant prevents the same historical fact from being reversed more than once.

---

# 27. REMOVE Target Selection

A new REMOVE operation selects the currently effective valuation facts for the document.

Selection is based on authoritative valuation history.

Derived balances are not authoritative input for determining what must be reversed.

Once selected and registered:

```text
target set
```

becomes immutable for that REMOVE operation.

---

# 28. Reversal Fact

The reversal fact is immutable:

```python
@dataclass(frozen=True, slots=True)
class ValuationReversal:
    identity: Identifier
    reversed_identity: Identifier
    valuation_key: ValuationKey
    document_identity: Identifier
    source_identity: Identifier
    operation_identity: ValuationOperationIdentity
    created_at: datetime
```

It identifies the exact historical fact being reversed.

A reversal never modifies the original fact.

---

# 29. Single Effective Reversal Invariant

A historical valuation fact may have at most one effective reversal.

Formally:

```text
fact F
    →
zero or one effective reversal R(F)
```

A second reversal for the same historical fact is never created.

---

# 30. Repeated Reversal

If a REMOVE operation encounters a historical fact that is already reversed:

```text
F
↓
R(F)
```

it does not create:

```text
F
↓
R(F)
↓
R2(F)
```

Instead, the existing reversal remains authoritative.

The repeated REMOVE operation becomes idempotent with respect to the already-reversed fact.

---

# 31. Multiple REMOVE Operations

Multiple REMOVE operations are permitted.

They do not imply multiple reversals of the same fact.

Example:

```text
POST
    ↓
F1
    ↓
REMOVE #1
    ↓
R1(F1)
```

A repeated REMOVE:

```text
REMOVE #2
```

does not create:

```text
R2(F1)
```

because `F1` is already reversed.

---

# 32. Multiple REMOVE Operations With Re-establishment

A new ESTABLISH creates new valuation facts.

Therefore:

```text
POST #1
    ↓
F1
    ↓
REMOVE #1
    ↓
R1(F1)
    ↓
POST #2
    ↓
F2
    ↓
REMOVE #2
    ↓
R2(F2)
```

is valid.

The second REMOVE reverses the newly established effective facts.

This preserves immutable historical lifecycle semantics.

---

# 33. Empty REMOVE Target Set

If a REMOVE operation selects no currently effective valuation facts:

```text
target set = ()
```

the empty set is canonical and has a deterministic fingerprint.

No reversal facts are created.

The operation is still a valid logical lifecycle operation and may be recorded as successful once fully reconciled.

---

# 34. Reversal Plan

For each selected valuation fact:

```text
original fact
        ↓
reversal fact
        ↓
compensating derived movement
```

For valuation layers:

```text
quantity → negative
cost     → negative
```

For valuation consumptions:

```text
quantity → positive
cost     → positive
```

The exact sign semantics remain governed by the existing valuation model.

---

# 35. Derived Movement Identity

Derived `CostMovement` identities must also be deterministic.

They are derived from the authoritative reversal/fact identity and semantic movement information.

The same reversal must therefore never produce two distinct derived movements during recovery.

---

# 36. Result Persistence

Derived valuation results remain rebuildable.

Persistence of derived results must be idempotent where possible.

If a derived result is partially persisted:

```text
some results exist
some results absent
```

recovery reconciles existing results and creates only missing results.

No historical valuation fact is removed to repair derived state.

---

# 37. Recovery API

The following operation-level recovery API is implemented by WP-8 Slice 8 for registered `REMOVE` operations.
It builds on the fact-level reconciliation mechanism established by Slice 7.

The valuation coordinator exposes an explicit recovery operation:

```python
def recover(
    operation_identity: ValuationOperationIdentity,
) -> OperationResult:
    ...
```

Recovery is distinct from:

```python
remove()
establish()
```

and must not be implemented merely as another blind invocation of those methods.

---

# 38. Recovery Semantics

Slice 8 operation recovery always starts from authoritative state:

```text
OperationRecord
        ↓
immutable target_fact_identities
        ↓
authoritative target facts
        ↓
deterministic expected reversal facts
        ↓
Slice 7 fact reconciliation
```

The operation fingerprint remains available for semantic verification but is not used to reconstruct target identities.

Slice 8 does not rebuild derived state; CostMovement/CostBalance recovery and derived-state rebuild remain later WP-8 scope.

Recovery never starts by trusting:

```text
CostBalance
CostMovement
```

as the source of truth.

---

# 39. Partial ESTABLISH Recovery

Example:

```text
OperationRecord O1 persisted

Expected:
F1
F2
F3

Actual:
F1
F2
```

Recovery determines:

```text
missing = {F3}
```

and appends only `F3`.

It does not:

```text
delete F1
delete F2
replace history
create F4
```

---

# 40. Partial REMOVE Recovery

Example:

```text
OperationRecord O2 persisted

Expected:
R1
R2

Actual:
R1
R2 unknown
```

Recovery reconciles `R2`.

If `R2` is confirmed absent:

```text
append R2
```

If `R2` is confirmed present:

```text
do not append R2 again
```

If existence cannot be determined:

```text
INDETERMINATE
```

No blind duplicate append is permitted.

---

# 41. Recovery of Derived State

After authoritative facts are complete:

```text
authoritative history
        ↓
interpret reversals
        ↓
construct expected derived movements
        ↓
rebuild/reconcile CostMovement
        ↓
rebuild/reconcile CostBalance
```

Derived state is therefore repairable independently of historical persistence.

---

# 42. Recovery Outcome

Recovery returns:

```text
SUCCESS
```

only when authoritative history and required derived state are reconciled.

It returns:

```text
FAILURE
```

for known deterministic integrity or validation failures.

It returns:

```text
INDETERMINATE
```

when persistence state cannot be established.

---

# 43. Rebuild API

The valuation coordinator exposes:

```python
def rebuild(
    valuation_key: ValuationKey | None = None,
) -> OperationResult:
    ...
```

The rebuild operation reconstructs derived state from authoritative valuation history.

---

# 44. Rebuild Source

Rebuild starts from:

```python
ValuationFactPersistence.enumerate()
```

not from:

```text
CostMovement
CostBalance
```

Historical valuation facts are therefore the source of truth.

---

# 45. Rebuild Pipeline

The rebuild algorithm is conceptually:

```text
enumerate valuation facts
        ↓
group by valuation key
        ↓
identify reversal relationships
        ↓
exclude reversed effective facts
        ↓
apply active valuation layers
        ↓
apply active valuation consumptions
        ↓
construct expected CostMovements
        ↓
construct CostBalance
        ↓
replace/reconcile derived state
```

The exact layer/consumption interpretation remains the responsibility of the existing valuation domain model.

---

# 46. Rebuild Idempotency

Running rebuild twice without authoritative history changes must produce equivalent derived state.

```text
rebuild()
rebuild()
```

must not accumulate duplicate:

```text
CostMovement
```

or alter:

```text
CostBalance
```

semantics.

---

# 47. Reversal Interpretation

A reversal does not erase the historical fact.

Instead:

```text
original fact
+
reversal fact
```

are interpreted together.

The effective state therefore excludes the reversed effect while preserving both historical records.

Example:

```text
F1 = +100
R1 = -100
```

Effective state:

```text
0
```

History:

```text
F1
R1
```

Both remain permanently preserved.

---

# 48. Posting Repost

`PostingEngine.repost()` must use:

```text
remove
    ↓
prepare
    ↓
establish
```

and not:

```text
prepare
    ↓
remove
    ↓
establish
```

This is required because preparation, including FIFO valuation preparation, must observe the effective state after the previous valuation effect has been removed.

---

# 49. Repost Failure Boundary

If REMOVE returns:

```text
FAILURE
```

or:

```text
INDETERMINATE
```

then:

```text
prepare
```

must not execute.

The repost operation stops at the removal boundary.

No new valuation effect is prepared against unresolved old state.

---

# 50. Repost Operations

Successful repost:

```text
old valuation facts
        ↓
read-only projected state excluding old effect
        ↓
new preparation
        ↓
ESTABLISH intent registration
        ↓
REMOVE operation
        ↓
reversal facts
        ↓
new ESTABLISH operation
        ↓
new valuation facts
```

If new ESTABLISH fails after successful removal:

```text
old effect remains reversed
```

There is no rollback of historical facts.

Recovery is used to reconcile the resulting state.

---

# 51. Generic Posting Boundary

`CompositePostingResultCoordinator` remains generic and transaction-neutral.

It must be able to represent:

```text
Register SUCCESS
Valuation INDETERMINATE
```

without attempting distributed rollback.

The generic posting layer does not acquire valuation-specific recovery semantics.

---

# 52. Required Test Matrix

WP-8 implementation must cover at minimum:

### Immutable history

* original valuation facts remain unchanged;
* original valuation facts are never deleted;
* reversal is appended as a new fact.

### Unpost

* successful reversal;
* repeated unpost;
* repeated reversal;
* multiple REMOVE operations;
* REMOVE after re-establishment;
* empty REMOVE target set.

### Repost

* prepare against a projected state equivalent to old-effect removal;
* FIFO preparation observes the projected post-removal state;
* ESTABLISH-intent failure blocks REMOVE;
* REMOVE failure or indeterminate blocks ESTABLISH;
* new establish creates new facts.

### Persistence failure

* operation-record failure;
* operation-record indeterminate;
* fact persistence failure;
* fact persistence indeterminate;
* derived-state persistence failure;
* derived-state persistence indeterminate.

### Recovery

* operation record exists, facts partially exist;
* operation record exists, facts complete, derived state incomplete;
* missing fact recovery;
* already-present fact reconciliation;
* indeterminate fact reconciliation;
* derived-state rebuild after incomplete results;
* repeated recovery.

### Duplicate logical operation

* same identity + same fingerprint;
* same identity + different fingerprint;
* duplicate fact identity with identical content;
* duplicate fact identity with conflicting content.

### Fingerprint

* different target ordering produces same fingerprint;
* persistence enumeration order does not affect fingerprint;
* duplicate target identity produces deterministic failure;
* empty target set is deterministic;
* same semantic REMOVE produces same fingerprint across retries.

### Rebuild

* rebuild from complete history;
* rebuild after incomplete derived results;
* repeated rebuild;
* rebuild with reversals;
* rebuild after multiple establish/remove cycles.

### Composite posting

* register success + valuation success;
* register success + valuation failure;
* register success + valuation indeterminate;
* valuation recovery after composite partial completion.

---

# 53. Acceptance Criteria Mapping

| Acceptance Criterion             | Concrete API Mechanism                    |
| -------------------------------- | ----------------------------------------- |
| AC-1 Immutable unpost            | `ValuationReversal` + append-only facts   |
| AC-2 Effective compensation      | reversal interpretation during rebuild    |
| AC-3 Repeated unpost             | single-effective-reversal invariant       |
| AC-4 Repeated reversal           | fact-specific reversal idempotency        |
| AC-5 Repost lifecycle            | `prepare → prepare_establish → remove → establish`            |
| AC-6 FIFO-aware repost           | preparation against projected post-removal state |
| AC-7 Persistence failure         | explicit `FAILURE` / no blind retry       |
| AC-8 Persistence indeterminate   | reconciliation before retry               |
| AC-9 Duplicate logical operation | operation identity + fingerprint          |
| AC-10 Incomplete derived results | rebuild/recovery                          |
| AC-11 Rebuild idempotency        | deterministic derived reconstruction      |
| AC-12 Historical preservation    | no fact update/delete                     |
| AC-13 Composite failure boundary | transaction-neutral composite coordinator |

---

# 54. Explicit Invariants

The implementation must preserve:

### W8-I1 — Historical Immutability

No historical valuation fact is updated or deleted.

### W8-I2 — Append-Only Reversal

A reversal is always a new valuation fact.

### W8-I3 — Fact-Specific Reversal

A reversal references the exact historical fact it compensates.

### W8-I4 — Single Effective Reversal

A historical valuation fact has at most one effective reversal.

### W8-I5 — Derived-State Rebuildability

Derived valuation state can be reconstructed from authoritative history.

### W8-I6 — Recovery Does Not Mutate History

Recovery only appends missing authoritative facts and repairs derived state.

### W8-I7 — Rebuild Idempotency

Repeated rebuild produces equivalent derived state.

### W8-I8 — Logical-Operation Idempotency

The same logical operation cannot create duplicate semantic effects.

### W8-I9 — Indeterminate Requires Reconciliation

An indeterminate persistence operation cannot be retried blindly.

### W8-I10 — Repost Ordering

Repost is:

```text
prepare → prepare_establish → remove → establish
```

### W8-I11 — No Rollback Illusion

Failure after successful historical persistence does not imply historical rollback.

### W8-I12 — Generic Composition Boundary

Generic posting coordination remains transaction-neutral.

### W8-I13 — Canonical REMOVE Fingerprint

REMOVE target identities are canonicalized before fingerprint construction.

### W8-I14 — Persistence Order Has No Semantic Meaning

Enumeration order never changes operation identity or fingerprint.

### W8-I15 — Duplicate Targets Are Invalid

Duplicate REMOVE target identities result in deterministic failure.

### W8-I16 — Operation Record Precedes Facts

Authoritative valuation facts cannot legitimately exist without their operation record.

---

# 55. API Changes Summary

The final WP-8 public API surface is implemented and reconciled. It includes:

```text
ValuationOperationIdentity
ValuationOperationType
ValuationOperationRecord
ValuationOperationPersistence
ValuationEstablishRecoveryDescriptor

ValuationFactIdentityFactory
ValuationReversal.operation_identity

ValuationFactRecoveryOutcome
ValuationFactRecoveryResult
ValuationFactRecoveryService

ValuationOperationRecoveryService
ValuationRecoveryOutcome
ValuationRecoveryResult

ValuationLifecycleCoordinator.prepare_establish(...)
ValuationLifecycleCoordinator.establish(...)
ValuationLifecycleCoordinator.remove(...)
ValuationLifecycleCoordinator.recover(...)

PostingEngine.post(...)
PostingEngine.unpost(...)
PostingEngine.repost(...)
PostingEngine.recover(...)
```

`ValuationOperationRecord.target_fact_identities` is authoritative immutable recovery material for registered REMOVE operations. `ValuationOperationRecord.establish_descriptor` is authoritative immutable recovery material for ESTABLISH operations.

No mutable operation-status model, operation-record update API, or operation-record delete API is introduced.

---

# 56. Non-Goals

WP-8 does not introduce:

* distributed transactions;
* two-phase commit;
* rollback of immutable valuation history;
* mutation of historical valuation facts;
* deletion of reversal facts;
* a mutable operation-status table;
* valuation-specific transaction logic inside generic posting coordination;
* a new valuation algorithm;
* a new FIFO algorithm;
* a new register architecture.

---

# 57. Implementation Order

Implementation and review completed in the following sequence:

```text
1. Operation identity and operation record
2. Operation persistence and fingerprinting
3. Canonical REMOVE target representation
4. Deterministic fact identity and fact persistence idempotency
5. Immutable reversal semantics
6. REMOVE recovery
7. Unified valuation recovery
8. Derived-state rebuild / reconciliation
9. Posting lifecycle identity propagation
10. Deterministic projected Repost preparation
11. Repost lifecycle: prepare → prepare_establish → remove → establish
12. Durable ESTABLISH recovery intent
13. Posting recovery: REMOVE → ESTABLISH
14. Composite recovery integration and vertical tests
15. Final documentation reconciliation
16. Final quality gate
```

The final implementation state is commit `5046a9c`.

---

# 58. Final API Decisions

The final WP-8 API decisions are:

1. `ValuationOperationIdentity` identifies one logical lifecycle operation.
2. `ValuationOperationRecord` is immutable authoritative operation history.
3. Operation records are append-only.
4. Same operation identity + same semantic record is idempotent.
5. Same operation identity + different semantic record is `FAILURE`.
6. `SUCCESS` means complete logical reconciliation.
7. `FAILURE` means known deterministic failure.
8. `INDETERMINATE` means unresolved persistence state.
9. `INDETERMINATE` requires reconciliation.
10. `find()` is the authoritative operation-existence reconciliation read.
11. Authoritative `None` means the operation does not exist.
12. An unknown read failure is `INDETERMINATE`, not `None`.
13. Operation-record persistence precedes valuation-fact persistence.
14. Facts without an operation record constitute a history-integrity violation.
15. Lifecycle facts have deterministic identities.
16. Fact persistence is idempotent by fact identity.
17. REMOVE selects currently effective valuation facts.
18. The selected REMOVE target set becomes immutable once the operation is registered.
19. REMOVE targets are semantically unordered.
20. REMOVE target identities are canonically sorted before fingerprint construction.
21. Persistence enumeration order has no semantic meaning.
22. Duplicate REMOVE target identities are deterministic `FAILURE`.
23. `operation_identity` is excluded from the semantic fingerprint.
24. A historical valuation fact has at most one effective reversal.
25. Repeated REMOVE does not create a second reversal for an already-reversed fact.
26. A later REMOVE may reverse newly established facts.
27. Partial fact recovery appends only missing deterministic facts.
28. Derived state is rebuildable from authoritative history.
29. Rebuild is idempotent.
30. Repost order is `prepare → prepare_establish → remove → establish`.
31. `prepare_establish` is completed before REMOVE; REMOVE `FAILURE` or `INDETERMINATE` blocks ESTABLISH.
32. Failure after successful removal does not restore the old valuation effect.
33. Recovery repairs state without mutating historical facts.
34. Generic posting coordination remains transaction-neutral.
35. No historical valuation fact is updated or deleted.

**WP-8 Concrete API Design is fully implemented and reconciled against commit `5046a9c`. It is the authoritative API reference for the completed WP-8 lifecycle and recovery architecture.**
