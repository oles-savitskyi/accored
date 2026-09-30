# WP-8 Slice 10.5 — Unified Valuation Recovery

## Concrete API Design

**Status:** Proposed for Architecture/API Review

---

## 1. Purpose

Slice 10.5 completes the unified valuation recovery lifecycle by combining:

1. authoritative `ValuationOperationRecord` recovery;
2. valuation fact reconciliation;
3. existing derived-state rebuild from Slice #9.

The public recovery entry point remains:

```python
class ValuationOperationRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        ...
```

No separate public recovery service is introduced for ESTABLISH, REMOVE, or derived state.

The recovery lifecycle becomes:

```text
ValuationOperationRecord
        │
        ▼
authoritative operation recovery
        │
        ▼
valuation fact reconciliation
        │
        ├── FAILURE / INDETERMINATE
        │        └── stop
        │
        ▼
DefaultValuationRebuilder
        │
        ▼
derived-state reconciliation
        │
        ▼
ValuationRecoveryResult
```

---

# 2. Architectural Constraints

Slice 10.5 MUST preserve the following invariants.

### 2.1 Historical valuation facts are immutable

Recovery MUST NOT:

* mutate an existing historical valuation fact;
* delete a historical valuation fact;
* replace a historical valuation fact in place.

### 2.2 Operation record remains authoritative

Recovery MUST anchor on the existing:

```python
ValuationOperationIdentity
```

and MUST NOT create a second operation record for the same recovery.

### 2.3 Slice #9 remains the sole derived-state rebuild implementation

No new rebuild algorithm is introduced.

Existing:

```python
DefaultValuationRebuilder
```

remains responsible for reconstructing derived valuation state from authoritative valuation facts.

### 2.4 No cross-subsystem transaction is introduced

The design does not assume atomic persistence across:

* operation records;
* valuation facts;
* derived valuation state.

Recovery exists precisely because those writes can become partially persisted.

### 2.5 Recovery is convergent

Repeated recovery of the same operation MUST converge to the same valid state and MUST NOT duplicate authoritative or derived state.

---

# 3. Existing Recovery Result Contract

Slice 10.5 does not replace the existing recovery result model.

The existing:

```python
ValuationRecoveryResult
```

remains the public result of:

```python
ValuationOperationRecoveryService.recover(...)
```

Its outcome semantics continue to distinguish at least:

```text
SUCCESS
FAILURE
INDETERMINATE
```

The unified service maps failures from both authoritative fact recovery and derived-state recovery into this existing result contract.

No new top-level recovery result hierarchy is introduced.

---

# 4. Derived-State Rebuild Boundary

The existing Slice #9 rebuilder is the integration boundary.

Conceptually:

```python
class ValuationRebuilder(Protocol):
    def rebuild(self) -> ValuationRebuildResult:
        ...
```

If the current repository already exposes an equivalent protocol/contract, Slice 10.5 MUST reuse that contract rather than introduce a parallel one.

The concrete implementation remains:

```python
DefaultValuationRebuilder
```

The rebuilder is responsible for:

* reading authoritative valuation facts;
* reconstructing the expected derived valuation state;
* reconciling persisted derived state;
* reporting its existing rebuild outcome.

It is NOT responsible for:

* finding `ValuationOperationRecord`;
* deciding whether an operation is recoverable;
* reconstructing an ESTABLISH `ValuationPlan`;
* creating valuation operation records;
* creating recovery-specific facts.

---

# 5. Recovery Service Dependencies

`DefaultValuationOperationRecoveryService` receives the existing fact-recovery dependencies plus the derived-state rebuild boundary.

Conceptually:

```python
class DefaultValuationOperationRecoveryService:
    def __init__(
        self,
        operation_persistence: ValuationOperationPersistence,
        fact_recovery: ValuationFactRecoveryService,
        fact_builder: ValuationFactBuilder,
        rebuilder: ValuationRebuilder,
    ) -> None:
        ...
```

The exact constructor ordering should follow the repository's existing dependency-injection/composition conventions.

No persistence implementation is created inside the recovery service.

---

# 6. Unified Recovery Algorithm

The public operation is:

```python
def recover(
    self,
    operation_identity: ValuationOperationIdentity,
) -> ValuationRecoveryResult:
    ...
```

The algorithm is:

```text
1. find operation record
2. validate operation record
3. recover authoritative valuation facts
4. if fact recovery != SUCCESS:
       return corresponding recovery result
5. rebuild/reconcile derived valuation state
6. map rebuild outcome
7. return unified recovery result
```

The important ordering is:

```text
operation
    ↓
facts
    ↓
derived state
```

Never:

```text
operation
    ↓
derived state
    ↓
facts
```

---

# 7. Operation Lookup

Recovery starts with:

```python
operation = operation_persistence.find(operation_identity)
```

If no record exists:

```text
find(...) == None
```

the operation remains authoritative `NOT_FOUND`.

Recovery MUST NOT:

* infer an ESTABLISH operation from valuation facts;
* infer a REMOVE operation from reversal facts;
* create a replacement operation record.

The result uses the existing recovery failure semantics.

---

# 8. Operation Dispatch

After lookup and validation:

```text
operation.operation_type
        │
        ├── ESTABLISH
        │      └── _recover_establish(...)
        │
        └── REMOVE
               └── _recover_remove(...)
```

The internal dispatch methods remain implementation details.

Public API does not expose:

```python
recover_establish(...)
recover_remove(...)
```

---

# 9. ESTABLISH Recovery

ESTABLISH recovery follows the Slice 10.4 design.

```text
ValuationOperationRecord
        │
        ▼
establish_descriptor
        │
        ▼
ValuationPlan
        │
        ▼
ValuationFactBuilder
        │
        ▼
expected valuation facts
        │
        ▼
ValuationFactRecoveryService
```

The operation record MUST contain:

```python
establish_descriptor
```

for an ESTABLISH operation.

Malformed records are failures.

Examples:

```text
ESTABLISH + descriptor=None
    → FAILURE

ESTABLISH + invalid descriptor
    → FAILURE

ESTABLISH + descriptor document != operation document
    → FAILURE
```

---

# 10. REMOVE Recovery

REMOVE continues to use the existing Slice 10 recovery semantics.

The operation record contains the target fact identities:

```python
target_fact_identities
```

The recovery service reconstructs the required reversal facts deterministically and reconciles them through:

```python
ValuationFactRecoveryService
```

No new REMOVE recovery algorithm is introduced in Slice 10.5.

---

# 11. Fact Recovery Gate

The derived-state rebuild is executed only after authoritative fact recovery succeeds.

Conceptually:

```python
fact_result = self._recover_operation_facts(operation)

if fact_result.outcome is not ValuationRecoveryOutcome.SUCCESS:
    return fact_result

return self._recover_derived_state(...)
```

This gives the following invariant:

> Derived valuation state is never rebuilt as the recovery step for an operation whose authoritative valuation facts are known to be incomplete or indeterminate.

---

# 12. Derived-State Recovery

After successful fact reconciliation:

```python
rebuild_result = rebuilder.rebuild()
```

The existing Slice #9 rebuild implementation is invoked.

The rebuilder reconstructs derived valuation state from authoritative facts rather than from the operation descriptor.

This distinction is important:

```text
ESTABLISH descriptor
    → reconstruct expected authoritative facts

authoritative facts
    → reconstruct derived state
```

The descriptor is NOT used to directly generate:

* CostMovements;
* balances;
* register totals;
* other derived persistence.

---

# 13. Why Rebuild Is Not Operation-Specific

The rebuilder operates over authoritative valuation facts.

Therefore:

```text
ESTABLISH recovery
    ─┐
REMOVE recovery
    ├──> authoritative facts ──> rebuilder
REPEAT recovery
    ─┘
```

This avoids creating separate derived-state recovery paths for every operation type.

It also preserves Slice #9's architectural role as the single source of derived-state reconstruction logic.

---

# 14. Rebuild Outcome Mapping

The existing rebuild result is mapped into the existing `ValuationRecoveryResult`.

Conceptually:

```text
ValuationRebuildOutcome.SUCCESS
    → ValuationRecoveryOutcome.SUCCESS

ValuationRebuildOutcome.FAILURE
    → ValuationRecoveryOutcome.FAILURE

ValuationRebuildOutcome.INDETERMINATE
    → ValuationRecoveryOutcome.INDETERMINATE
```

No new recovery outcome is introduced.

The mapping must preserve uncertainty.

In particular:

```text
INDETERMINATE ≠ SUCCESS
```

---

# 15. Partial Derived Persistence

Example:

```text
operation record       persisted
valuation facts        complete
CostMovement A         persisted
CostMovement B         missing
```

Recovery:

```text
find operation
    ↓
fact reconciliation
    ↓
SUCCESS
    ↓
rebuilder.rebuild()
    ↓
reconcile derived state
    ↓
SUCCESS
```

The recovery service MUST NOT create a second valuation operation or regenerate historical valuation facts.

---

# 16. Indeterminate Derived Persistence

Example:

```text
operation record       persisted
valuation facts        complete
derived append         persistence indeterminate
```

The rebuilder reports:

```python
INDETERMINATE
```

The unified recovery result is:

```python
ValuationRecoveryOutcome.INDETERMINATE
```

The authoritative facts remain persisted.

A subsequent recovery retries derived-state reconciliation.

---

# 17. Repeated Recovery

Given:

```python
recover(identity)
```

called multiple times:

```text
first recovery
    → SUCCESS

second recovery
    → SUCCESS

third recovery
    → SUCCESS
```

Repeated recovery MUST NOT produce:

* duplicate valuation facts;
* duplicate reversal facts;
* duplicate CostMovements;
* duplicate balances;
* additional operation records.

The existing reconciliation mechanisms are responsible for detecting already-existing equivalent state.

---

# 18. Failure During Fact Recovery

If fact recovery returns:

```text
FAILURE
```

then:

```text
rebuilder.rebuild()
```

MUST NOT be invoked as part of this recovery attempt.

Result:

```text
operation
    ↓
fact recovery
    ↓
FAILURE
    ↓
return
```

This prevents a rebuild from masking an unresolved authoritative-state failure.

---

# 19. Indeterminate Fact Recovery

If fact recovery returns:

```text
INDETERMINATE
```

the recovery MUST stop.

The result remains:

```text
INDETERMINATE
```

The rebuilder is not invoked by that recovery attempt.

The next recovery attempt starts from persisted authoritative facts and retries reconciliation.

---

# 20. No Rollback of Historical Facts

Slice 10.5 does not introduce compensating rollback for a derived-state failure.

Example:

```text
facts = successfully persisted
derived state = FAILURE
```

The system does NOT:

```text
delete facts
```

or:

```text
mutate facts into a rollback state
```

The correct state is:

```text
authoritative facts preserved
derived state requires recovery/rebuild
```

This follows the immutable historical-fact invariant.

---

# 21. Idempotency

There are two independent idempotency boundaries.

### Operation/fact idempotency

Controlled by:

```text
ValuationOperationIdentity
ValuationFactRecoveryService
```

### Derived-state idempotency

Controlled by:

```text
DefaultValuationRebuilder
```

Slice 10.5 composes these boundaries; it does not replace either one.

---

# 22. `ValuationFactBuilder` Integration

The `ValuationFactBuilder` introduced in Slice 10.4 remains the only fact-construction path for ESTABLISH.

Normal execution:

```text
ValuationPlan
    ↓
ValuationFactBuilder
    ↓
facts
```

Recovery:

```text
ESTABLISH descriptor
    ↓
ValuationPlan
    ↓
ValuationFactBuilder
    ↓
facts
```

This guarantees that recovery does not duplicate the ESTABLISH fact-construction algorithm.

---

# 23. Operation Record Is Not Recreated

Recovery MUST NOT execute:

```python
operation_persistence.append(...)
```

for the recovered operation.

The existing record is authoritative.

Recovery is:

```text
find → reconcile → rebuild
```

not:

```text
find → create replacement operation → reconcile
```

---

# 24. Public API

Slice 10.5 does not require a new public recovery interface.

The existing API remains:

```python
class ValuationOperationRecoveryService(Protocol):
    def recover(
        self,
        operation_identity: ValuationOperationIdentity,
    ) -> ValuationRecoveryResult:
        ...
```

The following remain public where already established:

```python
ValuationRecoveryResult
ValuationRecoveryOutcome
ValuationOperationIdentity
ValuationOperationRecord
ValuationOperationType
ValuationEstablishRecoveryDescriptor
ValuationFactBuilder
ValuationFactRecoveryService
```

The rebuilder protocol should be public only if it is already an established composition boundary in the current API.

Otherwise it should remain an internal dependency abstraction.

---

# 25. No New Public API

The following MUST NOT be added:

```python
EstablishRecoveryService
RemoveRecoveryService
DerivedStateRecoveryService
ValuationRecoveryCoordinator
PostingRecoveryPersistence
PostingOperationRecord
```

The unified recovery service is sufficient.

---

# 26. Dependency Direction

The intended dependency graph is:

```text
ValuationOperationRecoveryService
        │
        ├── ValuationOperationPersistence
        │
        ├── ValuationFactRecoveryService
        │
        ├── ValuationFactBuilder
        │
        └── ValuationRebuilder
```

The rebuilder does NOT depend on the operation recovery service.

Therefore:

```text
Recovery → Rebuilder
```

and never:

```text
Rebuilder → Recovery
```

This prevents a cyclic recovery architecture.

---

# 27. Recovery State Machine

Conceptually:

```text
                  ┌───────────────────┐
                  │ operation missing │
                  └─────────┬─────────┘
                            │
                         FAILURE

┌──────────┐
│ operation│
└────┬─────┘
     │
     ▼
┌────────────────────┐
│ recover facts      │
└────┬───────────────┘
     │
     ├──────── FAILURE ────────> FAILURE
     │
     ├──── INDETERMINATE ──────> INDETERMINATE
     │
     ▼
┌────────────────────┐
│ rebuild derived    │
│ state              │
└────┬───────────────┘
     │
     ├──────── FAILURE ────────> FAILURE
     │
     ├──── INDETERMINATE ──────> INDETERMINATE
     │
     ▼
   SUCCESS
```

---

# 28. Test Design

## 28.1 Unified success

Test:

```text
operation exists
facts complete
derived state complete
```

Expected:

```text
SUCCESS
```

---

## 28.2 ESTABLISH with missing facts

```text
operation exists
descriptor exists
facts partially persisted
```

Expected:

```text
missing facts appended
derived state rebuilt
SUCCESS
```

---

## 28.3 ESTABLISH with all facts already persisted

Expected:

```text
no duplicate facts
derived state reconciled
SUCCESS
```

---

## 28.4 REMOVE recovery

Existing REMOVE recovery tests MUST remain green.

Expected:

```text
reversal facts reconciled
derived state rebuilt
SUCCESS
```

---

## 28.5 Missing derived state

```text
operation = persisted
facts = complete
derived state = absent
```

Expected:

```text
fact reconciliation = SUCCESS
rebuild = SUCCESS
overall = SUCCESS
```

---

## 28.6 Partial derived state

```text
facts = complete
derived state = partial
```

Expected:

```text
rebuilder reconciles missing derived state
SUCCESS
```

---

## 28.7 Derived persistence failure

Expected:

```text
facts preserved
rebuild = FAILURE
overall = FAILURE
```

---

## 28.8 Derived persistence indeterminate

Expected:

```text
facts preserved
rebuild = INDETERMINATE
overall = INDETERMINATE
```

---

## 28.9 Repeated recovery

Run recovery multiple times.

Expected:

```text
first  → SUCCESS
second → SUCCESS
third  → SUCCESS
```

and verify no duplication.

---

## 28.10 Fact recovery failure prevents rebuild

Inject authoritative fact recovery failure.

Verify:

```text
rebuilder.rebuild()
```

was not called.

---

## 28.11 Fact recovery indeterminate prevents rebuild

Inject authoritative fact recovery indeterminate outcome.

Verify rebuild is not called.

---

## 28.12 No new operation record

After recovery:

```text
operation_persistence.find(identity)
```

must still return the original operation record.

Verify append/create was not invoked.

---

## 28.13 Historical immutability

Capture existing historical valuation facts before recovery.

After recovery:

```text
before == after
```

for all historical facts.

No deletion or mutation is permitted.

---

## 28.14 Rebuild equivalence

Compare:

```text
clean establish
```

against:

```text
partial establish
    +
recovery
```

The final authoritative and derived states must be equivalent.

---

# 29. Regression Tests

The following existing areas MUST remain green:

* Slice 9 derived-state rebuild;
* Slice 10.1 identity propagation;
* Slice 10.2 deterministic preparation;
* Slice 10.3 projected preparation state;
* Slice 10.4 ESTABLISH descriptor recovery;
* existing REMOVE recovery;
* existing valuation coordinator tests;
* standard composition tests.

No change to the Slice #9 rebuild algorithm is expected.

---

# 30. Explicitly Out of Scope

Slice 10.5 does NOT implement:

* Repost lifecycle;
* projected preparation state;
* Posting recovery;
* Posting operation persistence;
* Posting lifecycle state;
* event persistence;
* event publication;
* cross-subsystem transactions;
* changes to `DefaultValuationRebuilder` algorithm;
* new valuation fact semantics;
* new reversal semantics.

These belong to later Slice 10 stages or are explicitly excluded from Slice 10.

---

# 31. Acceptance Criteria

Slice 10.5 is complete when:

1. `ValuationOperationRecoveryService` remains the single public recovery entry point.
2. ESTABLISH recovery reconciles authoritative facts.
3. REMOVE recovery remains regression-free.
4. Derived state is rebuilt only after authoritative recovery succeeds.
5. `DefaultValuationRebuilder` remains the sole derived-state rebuild implementation.
6. Rebuild failures propagate as recovery failures.
7. Rebuild indeterminate outcomes propagate as recovery indeterminate outcomes.
8. Repeated recovery converges successfully.
9. No new operation record is created during recovery.
10. Historical valuation facts remain immutable.
11. Partial derived persistence is recoverable.
12. Authoritative fact failure prevents derived rebuild.
13. ESTABLISH continues to use `ValuationFactBuilder`.
14. No operation-specific derived-state reconstruction is introduced.
15. No Posting persistence/state model is introduced.
16. Existing Slice 9–10.4 tests remain green.

---

# 32. Quality Gate

The implementation is accepted only after:

```bash
pytest -q
ruff check .
black --check .
mypy src
```

all pass in the project's Python 3.14 environment.

---

# 33. Final Architecture

After Slice 10.5 the valuation recovery architecture is:

```text
                    ┌─────────────────────────────┐
                    │ ValuationOperationRecord    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
              ┌──────────────────────────────────────┐
              │ DefaultValuationOperationRecovery    │
              │ Service                              │
              └──────────────┬───────────────────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
          ESTABLISH                  REMOVE
                 │                       │
                 ▼                       ▼
       ValuationFactBuilder      reversal fact logic
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
               ValuationFactRecoveryService
                             │
                             ▼
                  authoritative facts
                             │
                             ▼
                  DefaultValuationRebuilder
                             │
                             ▼
                    derived valuation state
                             │
                             ▼
                   ValuationRecoveryResult
```

The central architectural property is:

> **Operation recovery restores authoritative valuation facts; the existing rebuilder restores all derived valuation state from those facts.**

This keeps recovery deterministic, idempotent, and layered without introducing a second derived-state implementation.
