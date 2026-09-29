# Phase 8 WP-8 — Slice 8

## REMOVE Recovery

### Architecture Definition / Scope

## 1. Purpose

Slice #8 introduces operation-level recovery for an already registered `REMOVE` valuation operation whose reversal facts were persisted only partially or whose persistence outcome became `INDETERMINATE`.

The slice builds on the fact-level reconciliation mechanism implemented in Slice #7.

The objective is to recover the existing `REMOVE` lifecycle operation without:

* creating a new operation;
* reselecting REMOVE targets from current valuation state;
* mutating historical valuation facts;
* deleting historical valuation facts;
* blindly retrying an indeterminate persistence operation.

---

## 2. Architectural Position

WP-8 currently consists of the following recovery layers:

```text
ValuationOperationRecord
        │
        ├── operation registration
        │
        └── operation-level recovery
                  │
                  ▼
        expected valuation facts
                  │
                  ▼
        ValuationFactRecoveryService
                  │
                  ▼
        authoritative fact persistence
```

Slice #7 established fact-level reconciliation.

Slice #8 establishes operation-level recovery for `REMOVE`.

The slice does not yet provide generic recovery for all valuation operation types.

---

## 3. Scope

Slice #8 covers:

1. locating an existing operation record;
2. validating that the operation is a registered `REMOVE`;
3. obtaining the immutable target fact identities belonging to that operation;
4. resolving those target valuation facts authoritatively;
5. reconstructing deterministic expected reversal facts;
6. reconciling those reversal facts through the Slice #7 recovery service;
7. returning `SUCCESS`, `FAILURE`, or `INDETERMINATE`.

Slice #8 does not cover:

* ESTABLISH recovery;
* CostMovement recovery;
* CostBalance recovery;
* derived-state rebuild;
* repost;
* composite posting recovery;
* distributed transactions;
* compensation;
* mutable operation records.

---

## 4. Core Architectural Invariant

Once a `REMOVE` operation has been registered, its target set is immutable.

Therefore:

```text
registered REMOVE target set
        ≠
current REMOVE target selection
```

Recovery must use the target set captured by the registered operation.

Recovery must never invoke the normal current-state target-selection algorithm.

In particular, recovery must not call:

```python
_select_removal_targets(...)
```

because the valuation history may have changed after the original operation was registered.

---

## 5. Required Operation Representation

The current operation record contains a semantic fingerprint.

For `REMOVE`, the fingerprint is constructed from:

```text
operation_type
document_identity
canonical_target_fact_identities
```

The fingerprint is intentionally one-way.

It cannot be used to reconstruct the target identities.

Therefore the authoritative operation representation must additionally retain the canonical target fact identities.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class ValuationOperationRecord:
    identity: ValuationOperationIdentity
    operation_type: ValuationOperationType
    document_identity: Identifier
    fingerprint: str
    target_fact_identities: tuple[Identifier, ...] = ()
```

The exact concrete field placement and validation rules are defined by the Concrete API amendment.

---

## 6. Meaning of `target_fact_identities`

For `REMOVE`:

```text
target_fact_identities
    =
canonical sorted identities of the valuation facts
selected by the original REMOVE operation
```

The identities are:

* immutable;
* semantically unordered;
* canonically stored in deterministic order;
* part of the authoritative operation representation.

For `ESTABLISH`:

```text
target_fact_identities == ()
```

No target set is introduced for ESTABLISH recovery by this slice.

---

## 7. Fingerprint and Target Set Have Different Responsibilities

The two representations must not be conflated.

### Fingerprint

The fingerprint provides:

* semantic equality;
* deterministic operation comparison;
* conflict detection;
* idempotent operation registration.

### Target identities

The target identities provide:

* operation recovery;
* deterministic reconstruction of reversal facts;
* preservation of the original REMOVE target set.

Therefore:

```text
fingerprint
    = semantic verification

target_fact_identities
    = recovery material
```

Both are required.

---

## 8. REMOVE Registration

Normal REMOVE remains:

```text
enumerate current facts
        ↓
select currently removable targets
        ↓
canonicalize target identities
        ↓
validate removal
        ↓
create REMOVE operation record
        ↓
persist operation record
        ↓
construct reversal facts
        ↓
persist/recover reversal facts
```

The operation record stores the canonical target identities at registration time.

After successful registration, the target set is never recalculated for that operation.

---

## 9. REMOVE Recovery

Recovery is initiated with:

```python
operation_identity: ValuationOperationIdentity
```

The recovery flow is:

```text
find operation
        │
        ├── NOT_FOUND → FAILURE
        │
        ▼
validate operation type
        │
        ├── not REMOVE → FAILURE
        │
        ▼
read immutable target identities
        │
        ▼
resolve each target fact authoritatively
        │
        ├── missing → FAILURE
        ├── indeterminate → INDETERMINATE
        │
        ▼
construct deterministic reversal facts
        │
        ▼
ValuationFactRecoveryService.reconcile(...)
        │
        ├── SUCCESS
        ├── FAILURE
        └── INDETERMINATE
```

No new operation record is created.

---

## 10. Authoritative Target Fact Resolution

For every persisted target identity:

```python
fact_persistence.find(target_identity)
```

is authoritative.

### Target exists

The fact participates in reversal reconstruction.

### Target does not exist

Recovery returns deterministic `FAILURE`.

The operation references a historical fact that cannot be resolved.

Recovery must not substitute another fact.

### Target lookup is indeterminate

Recovery returns `INDETERMINATE`.

It must not continue with an incomplete target set.

---

## 11. Deterministic Reversal Reconstruction

Once all target facts are available, recovery reconstructs the expected reversal facts using the same deterministic identity scheme as normal REMOVE.

The inputs include:

```text
operation.identity
target fact identity
target fact semantics
```

The resulting reversal identity must equal the identity produced during the original REMOVE operation.

Recovery does not invent a new identity.

---

## 12. Fact Recovery Delegation

Slice #8 does not duplicate fact persistence reconciliation.

It delegates expected reversal facts to:

```python
ValuationFactRecoveryService.reconcile(...)
```

Slice #7 remains responsible for:

* authoritative fact lookup;
* identical-existing detection;
* semantic conflict detection;
* appending missing facts;
* reconciliation after indeterminate append;
* recovery result classification.

---

## 13. Partial Recovery

Example:

```text
REMOVE operation O2
targets = F1, F2, F3

persisted facts:
F1
F2
F3
R1
R2
```

Expected reversal facts:

```text
R1
R2
R3
```

Recovery determines that only `R3` is missing and delegates:

```text
R3
```

to fact recovery.

It does not recreate `R1` or `R2`.

It does not select another target.

---

## 14. Complete Recovery

If all expected reversal facts already exist with identical semantics:

```text
R1
R2
R3
```

recovery returns:

```text
SUCCESS
```

without changing persistence.

Repeated recovery remains idempotent.

---

## 15. Conflict Recovery

If an expected reversal identity exists with different semantic content:

```text
expected R3 != persisted R3
```

recovery returns:

```text
FAILURE
```

Historical data is not updated or deleted.

---

## 16. Indeterminate Recovery

If authoritative persistence state cannot be established, recovery returns:

```text
INDETERMINATE
```

No blind retry is performed.

The caller must reconcile again once authoritative persistence state is available.

---

## 17. Operation Record Immutability

Recovery never:

* updates the operation record;
* changes its fingerprint;
* changes its target identities;
* creates a replacement operation;
* creates a second operation identity.

The existing operation remains the authoritative lifecycle record.

---

## 18. Operation Lookup

Recovery uses:

```python
ValuationOperationPersistence.find(
    operation_identity,
)
```

If the operation does not exist, recovery returns deterministic `FAILURE`.

Recovery does not create an operation record to compensate for a missing one.

---

## 19. Public Recovery Boundary

Slice #8 introduces operation-level recovery:

```python
recover(
    operation_identity: ValuationOperationIdentity,
) -> ValuationRecoveryResult
```

The supported operation type in this slice is:

```text
REMOVE
```

`ESTABLISH` recovery is explicitly outside the Slice #8 scope.

The exact concrete result type and exception mapping are specified in the Concrete API amendment.

---

## 20. Recovery Outcomes

### SUCCESS

All authoritative facts required to complete the registered REMOVE operation exist with identical semantics.

### FAILURE

A deterministic problem prevents recovery.

Examples:

* operation not found;
* operation has unsupported type;
* target fact not found;
* target fact semantics conflict;
* reversal fact semantics conflict;
* invalid target representation.

### INDETERMINATE

Persistence state cannot currently be established authoritatively.

No historical mutation is performed.

---

## 21. Non-Goals

Slice #8 does not implement:

* ESTABLISH recovery;
* generic recovery for arbitrary operation types;
* CostMovement recovery;
* CostBalance recovery;
* derived-state reconstruction;
* repost;
* composite posting recovery;
* distributed transactions;
* compensation;
* mutable operation status.

---

## 22. Acceptance Criteria

### AC-1 — Operation lookup

An existing operation is located by `ValuationOperationIdentity`.

### AC-2 — REMOVE validation

Only registered `REMOVE` operations are processed.

### AC-3 — Immutable target set

Recovery uses the target identities stored with the operation.

### AC-4 — No target reselection

Recovery never invokes current-state REMOVE target selection.

### AC-5 — Target resolution

Every stored target identity is resolved through authoritative fact persistence.

### AC-6 — Deterministic reversal identity

Recovery reconstructs the same reversal identities as the original REMOVE operation.

### AC-7 — Partial recovery

Only missing reversal facts are appended.

### AC-8 — Complete recovery

Already complete REMOVE operations return `SUCCESS` without additional persistence.

### AC-9 — Semantic conflict

Conflicting semantics return `FAILURE`.

### AC-10 — Target history violation

A missing target fact returns `FAILURE`.

### AC-11 — Indeterminate persistence

Indeterminate authoritative reads return `INDETERMINATE`.

### AC-12 — No historical mutation

Recovery never updates or deletes historical valuation facts.

### AC-13 — No new operation

Recovery never creates another operation record.

### AC-14 — Idempotence

Repeated successful recovery produces no additional valuation facts.

### AC-15 — ESTABLISH boundary

ESTABLISH recovery remains outside Slice #8.

### AC-16 — Derived-state boundary

Derived-state and CostMovement recovery remain outside Slice #8.

---

## 23. Required Test Matrix

The implementation must cover:

1. complete REMOVE recovery;
2. one missing reversal;
3. multiple missing reversals;
4. already-present identical reversals;
5. indeterminate reversal append followed by reconciliation;
6. reversal semantic conflict;
7. missing target fact;
8. indeterminate target lookup;
9. operation not found;
10. wrong operation type;
11. target-order independence;
12. deterministic reversal identity;
13. proof that current target selection is not invoked;
14. proof that no new operation is created;
15. repeated recovery idempotence.

---

## 24. Architecture Decision

The definitive Slice #8 architecture is:

> A registered REMOVE operation persists its canonical target fact identities as immutable recovery material in addition to its semantic fingerprint.

The fingerprint is retained for semantic comparison and conflict detection.

The target identities are retained for deterministic recovery.

A recovery implementation that attempts to reconstruct the target set from current valuation state is not compliant with this architecture.
