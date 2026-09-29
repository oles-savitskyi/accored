# Phase 8 WP-8 — Slice 8 — Concrete API Design Amendment

## 1. Purpose

This amendment makes one targeted correction to the approved Concrete API Design for Phase 8 WP-8 Slice 8 — REMOVE Recovery.

The amendment does **not** change the Slice 8 architecture, recovery boundaries, operation lifecycle, or Slice 7 fact-recovery contract.

It resolves one concrete representation gap:

> The REMOVE recovery process must have authoritative access to the exact valuation fact identities selected by the original REMOVE operation.

The operation fingerprint is not reversible and therefore cannot serve as recovery storage.

---

## 2. Amend `ValuationOperationRecord`

The operation record is amended with an immutable target-fact identity collection:

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
    target_fact_identities: tuple[Identifier, ...] = ()
```

### Semantics

`target_fact_identities` has the following meaning:

* for `REMOVE`, it contains the exact valuation fact identities selected by that REMOVE operation;
* identities are duplicate-free;
* identities are canonically ordered;
* the collection is immutable;
* the collection is part of the persisted semantic operation record;
* the collection is never recomputed during recovery;
* for `ESTABLISH`, the collection is empty.

The default empty tuple is therefore valid for operations that have no REMOVE targets.

---

## 3. Canonical REMOVE Target Representation

The existing canonicalization contract remains authoritative:

```python
def _canonical_remove_target_identities(
    target_identities: tuple[Identifier, ...],
) -> tuple[Identifier, ...]:
    if len(target_identities) != len(set(target_identities)):
        raise ValuationValidationError(
            "REMOVE target selection contains duplicate valuation fact identities."
        )

    return tuple(sorted(target_identities, key=str))
```

The canonical representation is produced exactly once for the logical REMOVE operation before operation registration.

---

## 4. REMOVE Operation Construction

The REMOVE operation must persist the canonical target identities:

```python
canonical_target_identities = _canonical_remove_target_identities(
    tuple(fact.identity for fact in targets)
)

operation = ValuationOperationRecord(
    identity=operation_identity,
    operation_type=ValuationOperationType.REMOVE,
    document_identity=document_identity,
    fingerprint=_remove_fingerprint(
        document_identity=document_identity,
        target_identities=canonical_target_identities,
    ),
    target_fact_identities=canonical_target_identities,
)
```

The same canonical tuple is therefore used for two distinct purposes:

1. `fingerprint` — semantic conflict detection;
2. `target_fact_identities` — authoritative recovery material.

The two representations must not be treated as interchangeable.

---

## 5. Fingerprint Semantics

The REMOVE fingerprint remains:

```text
SHA-256(
    canonical(
        operation_type,
        document_identity,
        target_fact_identities
    )
)
```

The fingerprint remains a one-way semantic representation.

It is **not** a serialization from which target identities can be reconstructed.

Therefore:

```text
fingerprint
```

must never be used as the source of target identities during recovery.

Recovery reads:

```python
operation.target_fact_identities
```

directly from the persisted operation record.

---

## 6. Operation Persistence Contract

No change is made to the existing persistence protocol:

```python
class ValuationOperationPersistence(Protocol):
    def append(self, operation: ValuationOperationRecord) -> None:
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

    def enumerate(self) -> tuple[ValuationOperationRecord, ...]:
        ...
```

There is intentionally no:

```python
update(...)
```

Operation records remain append-only and immutable.

---

## 7. Operation Idempotency and Conflict

Operation equality now includes `target_fact_identities`.

Therefore an operation with the same identity is idempotent only when the complete semantic record is identical.

### Identical operation

```text
same identity
same operation type
same document identity
same fingerprint
same target_fact_identities
```

Result:

```text
idempotent success
```

### Conflicting operation

For example:

```text
same identity
different target_fact_identities
```

Result:

```text
ValuationConflictError
```

No operation record may be mutated to resolve such a conflict.

---

## 8. Operation-Level Recovery API

Introduce the operation-level recovery contract:

```python
class ValuationOperationRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        ...
```

The recovery result is:

```python
class ValuationRecoveryOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationRecoveryResult:
    outcome: ValuationRecoveryOutcome
    error: Exception | None = None
```

---

## 9. Recovery Lookup

Recovery begins with the authoritative operation lookup:

```python
operation = operation_persistence.find(operation_identity)
```

### Result mapping

| Condition                                                         | Outcome         |
| ----------------------------------------------------------------- | --------------- |
| operation found                                                   | continue        |
| operation not found                                               | `FAILURE`       |
| operation lookup indeterminate                                    | `INDETERMINATE` |
| operation lookup raises deterministic persistence/domain conflict | `FAILURE`       |

A missing operation is not interpreted as an incomplete operation.

---

## 10. Recovery Operation Type

Slice 8 supports only `REMOVE`.

If the operation exists but is not `REMOVE`:

```text
FAILURE
```

No ESTABLISH recovery is introduced by Slice 8.

---

## 11. Target Resolution

For a registered REMOVE operation:

```python
target_ids = operation.target_fact_identities
```

Each target is resolved through authoritative fact persistence:

```python
fact = fact_persistence.find(target_id)
```

### Resolution rules

| Fact lookup result                       | Recovery meaning        |
| ---------------------------------------- | ----------------------- |
| fact found                               | retain resolved target  |
| `None`                                   | deterministic `FAILURE` |
| `PersistenceIndeterminateError`          | `INDETERMINATE`         |
| `PersistenceError` with unresolved state | `INDETERMINATE`         |

A missing target is a history-integrity failure because the registered REMOVE operation explicitly references that fact.

Recovery must not silently omit the missing target.

---

## 12. No Target Reselection

The following operation is forbidden during Slice 8 recovery:

```python
_select_removal_targets(...)
```

Recovery must never derive a new target set from current valuation history.

The target set was fixed at original operation registration time.

Therefore:

```text
original valuation state
        ↓
REMOVE target selection
        ↓
canonical target identities
        ↓
operation registration
        ↓
immutable target set
```

Recovery starts **after** this point and consumes the persisted target set.

---

## 13. Reversal Reconstruction

After all target facts have been authoritatively resolved, recovery reconstructs the expected reversal facts using the existing deterministic fact identity factory.

The original operation identity is reused:

```python
_build_reversals(
    operation_identity=operation.identity,
    document_identity=operation.document_identity,
    originals=resolved_targets,
)
```

No new `ValuationOperationIdentity` is created.

The reconstructed facts therefore have deterministic identities derived from the original REMOVE operation.

---

## 14. Delegation to Slice 7 Fact Recovery

Slice 8 does not duplicate fact-reconciliation logic.

It delegates to the Slice 7 recovery service:

```python
fact_recovery.reconcile(
    operation,
    reversal_facts,
)
```

The resulting outcome maps directly:

```text
ValuationFactRecoveryOutcome.SUCCESS
        → ValuationRecoveryOutcome.SUCCESS

ValuationFactRecoveryOutcome.FAILURE
        → ValuationRecoveryOutcome.FAILURE

ValuationFactRecoveryOutcome.INDETERMINATE
        → ValuationRecoveryOutcome.INDETERMINATE
```

The existing Slice 7 guarantees therefore remain authoritative for:

* missing fact append;
* idempotent existing facts;
* semantic conflicts;
* partial recovery;
* persistence indeterminacy;
* repeated reconciliation.

---

## 15. Empty REMOVE

An empty target set is valid when it was the actual target set of the registered REMOVE operation.

Therefore:

```python
operation.target_fact_identities == ()
```

means:

```text
no reversal facts are required
```

provided the operation itself is valid and recoverable.

Recovery returns:

```text
SUCCESS
```

without creating reversal facts.

This does not permit recovery to reinterpret a non-empty historical target set as empty.

---

## 16. Public Coordinator API

The valuation coordinator exposes:

```python
def recover(
    self,
    operation_identity: ValuationOperationIdentity,
) -> ValuationRecoveryResult:
    ...
```

Slice 8 supports REMOVE recovery only.

The coordinator must not expose a separate target-selection argument:

```python
recover(operation_identity, target_ids)  # forbidden
```

The target set is authoritative data belonging to the registered operation.

---

## 17. Legacy Operation Records

The amended schema applies to operation records created under the Slice 8-compatible representation.

Pre-amendment REMOVE records do not contain the persisted target identity set required for deterministic recovery. No migration mechanism is introduced in Slice 8.

The domain record uses:

```python
target_fact_identities: tuple[Identifier, ...] = ()
```

Therefore the domain object alone cannot distinguish a genuinely registered empty REMOVE from a legacy record whose target field was absent before this amendment. The Slice 8 domain API must not claim that such legacy records can always be identified and returned as `FAILURE`.

A persistence adapter that retains schema/version information may reject an incompatible legacy record as deterministic `FAILURE`; otherwise compatibility handling is outside the Slice 8 domain contract. In no case may recovery:

* re-run target selection;
* reconstruct targets from the fingerprint;
* guess an empty target set for a known legacy record;
* create a replacement operation;
* mutate the historical operation record.

---

## 18. Recovery Invariants

The following invariants are mandatory:

1. Recovery never creates a new operation.
2. Recovery never changes an existing operation record.
3. Recovery never changes `target_fact_identities`.
4. Recovery never re-runs REMOVE target selection.
5. Recovery never derives target identities from the fingerprint.
6. Recovery never deletes historical valuation facts.
7. Recovery never updates historical valuation facts.
8. Recovery reconstructs reversal facts deterministically.
9. Recovery reuses the original operation identity.
10. Recovery delegates fact reconciliation to Slice 7.
11. Repeated recovery is idempotent.
12. `INDETERMINATE` remains distinguishable from deterministic `FAILURE`.

---

## 19. Required Test Matrix

The implementation must include tests for:

### Operation lookup

* operation not found → `FAILURE`;
* operation lookup indeterminate → `INDETERMINATE`;
* ESTABLISH operation → `FAILURE`.

### Target resolution

* all targets found;
* target missing → `FAILURE`;
* target lookup indeterminate → `INDETERMINATE`;
* target identities remain canonical.

### Complete recovery

* all reversals already present → `SUCCESS`;
* no additional fact append occurs.

### Partial recovery

* one reversal missing → only that reversal is appended;
* multiple reversals missing → only missing reversals are appended;
* all missing reversals become present → `SUCCESS`.

### Conflict

* existing reversal with same identity but different semantics → `FAILURE`.

### Persistence indeterminacy

* append indeterminate, authoritative reconciliation finds all facts → `SUCCESS`;
* append indeterminate, some facts remain missing → `INDETERMINATE`.

### Determinism

* same operation produces identical reversal identities;
* persistence enumeration order does not affect recovery;
* target identity order in persisted input is canonical.

### Architectural invariants

* `_select_removal_targets()` is never called by recovery;
* recovery does not create a new operation;
* recovery does not mutate the existing operation;
* recovery does not mutate historical facts;
* repeated recovery is idempotent.

---

## 20. Implementation Order

The implementation sequence is:

1. amend `ValuationOperationRecord`;
2. persist canonical REMOVE target identities;
3. update operation persistence/idempotency tests;
4. introduce `ValuationRecoveryOutcome`;
5. introduce `ValuationRecoveryResult`;
6. introduce `ValuationOperationRecoveryService`;
7. implement operation lookup;
8. implement immutable target resolution;
9. implement deterministic reversal reconstruction;
10. delegate to `ValuationFactRecoveryService`;
11. expose coordinator `recover()`;
12. implement the complete test matrix;
13. perform integration verification;
14. reconcile architecture and API documentation;
15. run the final quality gate.

---

## 21. Explicit Non-Goals

This amendment does not introduce:

* ESTABLISH recovery;
* CostMovement recovery;
* CostBalance recovery;
* derived-state rebuild;
* repost recovery;
* composite operation recovery;
* distributed transactions;
* two-phase commit;
* compensation;
* operation-record mutation;
* historical fact mutation;
* migration of pre-amendment operation records.

---

## 22. Final API Decision

The authoritative Slice 8 representation is:

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
    target_fact_identities: tuple[Identifier, ...] = ()
```

and:

```python
class ValuationOperationRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        ...
```

with:

```python
class ValuationRecoveryOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationRecoveryResult:
    outcome: ValuationRecoveryOutcome
    error: Exception | None = None
```

The central rule is:

> **The REMOVE fingerprint verifies the semantic operation; `target_fact_identities` preserves the immutable recovery material.**

No other part of the approved Slice 8 architecture is changed by this amendment.
