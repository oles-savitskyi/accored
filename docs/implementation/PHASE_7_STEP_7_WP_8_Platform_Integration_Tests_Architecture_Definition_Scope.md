# PHASE 7 — WP-8 Platform Integration Tests

## Architecture Definition / Scope

---

# 1. Purpose

WP-8 validates that the approved Register Platform architecture composes correctly at the platform integration level.

WP-8 does not introduce new Register semantics.

Its purpose is to verify that the independently implemented and tested capabilities from previous work packages operate correctly when composed through their real public and architectural boundaries.

The integration scope covers:

* Register-scoped operation serialization;
* mutation admission;
* persisted Movement Facts;
* Totals maintenance;
* Totals lifecycle and consistency state;
* rebuild;
* recovery;
* Movement Query;
* Balance Query;
* interaction between mutation and read-side capabilities;
* interaction between ordinary mutation and maintenance operations;
* Register isolation.

The primary goal is to demonstrate that the Register Platform behaves as one coherent platform composition rather than merely as a collection of independently passing unit-tested components.

---

# 2. Architectural Context

WP-8 follows the completion of:

```text
WP-4  Operation Domain Completion
WP-5  Bootstrap / Rebuild / Recovery
WP-6  Query / Balance Composition
WP-7  Public API
```

The resulting Register Platform contains the following architectural capabilities:

```text
Movement
   │
   ├── Validation
   │
   └── Mutation
          │
          ├── Register Operation Domain
          │
          ├── RegisterFactPersistence
          │
          └── Totals Maintenance
                  │
                  └── Totals Engine
```

Read-side composition:

```text
RegisterFactPersistence
        │
        └── Movement Query

TotalsReader
        │
        └── Balance Query
```

Maintenance composition:

```text
Register Operation Domain
        │
        ├── Mutation
        ├── Rebuild
        └── Recovery
```

The Operation Domain is therefore the shared Register-scoped serialization boundary for all state-changing operations.

---

# 3. Architectural Goal

WP-8 must establish evidence that:

1. public Register capabilities compose through their intended interfaces;
2. mutation and maintenance use the same Register Operation Domain;
3. persisted Movement Facts remain authoritative;
4. Totals remain derived state;
5. rebuild reconstructs Totals from persisted Movement Facts;
6. recovery uses rebuild semantics;
7. mutation admission follows published maintenance state;
8. read-side queries observe the appropriate published state;
9. read-side queries do not participate in mutation serialization;
10. different Registers remain isolated;
11. failures preserve the approved lifecycle/consistency semantics;
12. no hidden second orchestration or synchronization mechanism is required.

WP-8 is therefore an architectural composition verification step.

---

# 4. Scope Boundary

## 4.1 In Scope

WP-8 covers platform-level integration scenarios involving:

### Mutation

* establishing Movement Facts;
* removing Movement Facts;
* mutation validation;
* persistence;
* Totals maintenance;
* mutation admission.

### Operation Domain

* shared Register-scoped serialization;
* mutation/rebuild serialization;
* mutation/recovery serialization;
* same-register exclusion;
* different-register isolation.

### Bootstrap

* newly constructed maintenance coordinator;
* initial non-admitted state;
* rebuild-based activation;
* mutation admission after successful rebuild.

### Rebuild

* rebuilding from authoritative persistence;
* replacing derived Totals;
* reconstructing runtime maintenance state;
* reconstructing `_applied`;
* successful publication of `ACTIVE + VALID`.

### Recovery

* recovery after deterministic maintenance failure;
* recovery after indeterminate failure;
* recovery through rebuild semantics;
* restoration of mutation admission after successful recovery.

### Query

* Movement Query over persisted Movement Facts;
* Balance Query over published Totals;
* composition after mutation;
* composition after rebuild/recovery.

### Register Isolation

* independent persistence facts;
* independent Totals;
* independent maintenance state;
* independent operation domains.

### Failure Integration

* persistence failure;
* Totals failure;
* unexpected failure;
* state publication constraints;
* recovery requirement.

---

# 5. Out of Scope

WP-8 does not introduce or validate:

* Inventory-specific behavior;
* Posting pipeline integration outside the already-defined Register boundaries;
* external databases;
* external infrastructure;
* network integration;
* transaction managers;
* distributed locking;
* multi-process concurrency;
* performance benchmarking;
* load testing;
* persistence implementation internals beyond their public contract;
* new Register semantics;
* new lifecycle states;
* new consistency states;
* new recovery abstractions;
* new query semantics;
* new Balance semantics;
* new public API symbols.

WP-8 is platform integration testing, not infrastructure integration testing.

---

# 6. Integration Architecture

The canonical state-changing composition is:

```text
                    ┌─────────────────────────┐
                    │ RegisterOperationDomain │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
          Mutation            Rebuild           Recovery
              │                  │                  │
              ▼                  ▼                  │
       Movement Facts      Movement Facts           │
              │                  │                  │
              ▼                  ▼                  │
       Totals Maintenance ───────┴──────────────────┘
              │
              ▼
         Totals Engine
```

The authoritative/derived relationship is:

```text
RegisterFactPersistence
        │
        │ authoritative Movement Facts
        ▼
     Movement Facts
        │
        │ rebuild
        ▼
    Totals Engine
        │
        │ current aggregate
        ▼
   Balance Query
```

Movement Query reads the authoritative Movement Facts directly:

```text
RegisterFactPersistence
        │
        ▼
Movement Query
```

It must not derive Movement Query results from Totals.

---

# 7. Integration Ownership

WP-8 preserves the ownership model established by WP-4 and WP-5.

| Component                         | Integration responsibility                 |
| --------------------------------- | ------------------------------------------ |
| `RegisterOperationDomain`         | Register-scoped serialization              |
| `RegisterOperationDomainRegistry` | stable domain per Register                 |
| `RegisterMutationOrchestrator`    | ordinary mutation coordination             |
| `TotalsMaintenanceCoordinator`    | Totals lifecycle and consistency semantics |
| `RegisterFactPersistence`         | authoritative Movement Facts               |
| `TotalsEngine`                    | derived Totals                             |
| `MovementQueryService`            | read Movement Facts                        |
| `BalanceQueryService`             | read current Totals                        |
| `MovementValidator`               | mutation validation                        |

No integration test may imply ownership different from this table.

---

# 8. Primary Integration Invariants

## 8.1 Authoritative Facts Invariant

Persisted Movement Facts are authoritative.

After a successful mutation:

```text
Persistence == authoritative Movement Facts
```

After rebuild:

```text
Totals == function(Persisted Movement Facts)
```

The test must not treat `_applied` as authoritative state.

---

## 8.2 Derived Totals Invariant

Totals are derived state.

A successful rebuild must produce the same logical Totals as applying all authoritative persisted Movement Facts through the approved Totals semantics.

---

## 8.3 Mutation Admission Invariant

Mutation is admitted only when:

```text
Lifecycle == ACTIVE
Consistency == VALID
```

A newly created coordinator must not admit mutation merely because its runtime `_applied` set is empty.

---

## 8.4 Shared Serialization Invariant

For one Register:

```text
Mutation
Rebuild
Recovery
```

must use the same `RegisterOperationDomain`.

Therefore conflicting state-changing operations cannot interleave within one Register.

---

## 8.5 Register Isolation Invariant

For different Registers:

```text
Register A != Register B
```

operations remain isolated.

A blocked operation for Register A must not block an independent operation for Register B.

---

## 8.6 Recovery Invariant

Recovery does not constitute a separate reconstruction algorithm.

It delegates to rebuild semantics.

Therefore:

```text
Recovery(register)
    ==
Rebuild(register)
```

with respect to authoritative source, Totals reconstruction, runtime state reconstruction, and successful state publication.

---

## 8.7 Query Isolation Invariant

Movement Query and Balance Query are read-side operations.

They must not:

* acquire Register Operation Domain locks;
* mutate maintenance state;
* mutate persistence;
* mutate Totals.

---

# 9. Integration Scenario Group A — Bootstrap

## Scenario A1 — New Coordinator Is Not Admitted

Given a new maintenance coordinator:

```text
Lifecycle = CREATED
Consistency = INDETERMINATE
```

mutation must be rejected.

The test must establish that an empty runtime `_applied` collection does not imply mutation admission.

---

## Scenario A2 — Successful Bootstrap Through Rebuild

Given persisted Movement Facts:

```text
Persistence = authoritative facts
```

a rebuild must:

1. enumerate persisted facts;
2. reconstruct Totals;
3. reconstruct runtime applied state;
4. publish:

```text
ACTIVE + VALID
```

only after all reconstruction steps succeed.

Mutation must then be admitted.

---

# 10. Integration Scenario Group B — Ordinary Mutation

## Scenario B1 — Establish

A successful establish operation must compose:

```text
Validation
→ Persistence
→ Totals Maintenance
→ Totals
```

and leave:

```text
Movement Fact persisted
Totals updated
Maintenance state valid
```

---

## Scenario B2 — Remove

A successful remove operation must compose:

```text
Validation / mutation admission
→ Persistence
→ Totals Maintenance
→ Totals
```

and leave the persisted and derived states consistent.

---

## Scenario B3 — Mutation and Balance Query

After successful mutation:

```text
Movement Fact
    ↓
Persistence

Movement Fact
    ↓
Totals
    ↓
Balance Query
```

Balance Query must return the published current aggregate.

The query must not change maintenance state.

---

## Scenario B4 — Mutation and Movement Query

After successful mutation:

```text
Movement Fact
    ↓
Persistence
    ↓
Movement Query
```

Movement Query must observe the persisted Movement Fact.

The result must not be reconstructed from Totals.

---

# 11. Integration Scenario Group C — Rebuild

## Scenario C1 — Deterministic Rebuild

Given the same persisted Movement Facts, repeated rebuilds must produce the same logical Totals.

The test must verify that rebuild is replacement/reconstruction semantics, not incremental accumulation.

---

## Scenario C2 — Rebuild Ignores Runtime `_applied`

The test must establish that rebuild derives its result from:

```text
RegisterFactPersistence.enumerate(register)
```

and does not rely on the previous runtime `_applied` collection.

---

## Scenario C3 — Rebuild Removes Stale Derived State

Given:

```text
Persisted facts = authoritative state
Totals = stale derived state
```

successful rebuild must replace stale Totals with Totals reconstructed from persistence.

---

## Scenario C4 — Rebuild Publishes State Only After Success

If any reconstruction stage fails:

```text
enumeration
Totals rebuild
runtime state reconstruction
```

the coordinator must not publish:

```text
ACTIVE + VALID
```

---

# 12. Integration Scenario Group D — Recovery

## Scenario D1 — Deterministic Recovery

After a deterministic maintenance failure:

```text
Consistency = RECOVERY_REQUIRED
```

recovery must execute rebuild semantics and, after success, restore:

```text
ACTIVE + VALID
```

---

## Scenario D2 — Indeterminate Recovery

After an unexpected failure:

```text
Consistency = RECOVERY_REQUIRED
```

recovery must reconstruct from authoritative persistence rather than relying on partially applied runtime state.

---

## Scenario D3 — Recovery Does Not Introduce a Second State Machine

Recovery must use:

```text
TotalsMaintenanceCoordinator.recover()
```

and the existing maintenance state model.

No separate RecoveryCoordinator or recovery lifecycle is introduced.

---

# 13. Integration Scenario Group E — Serialization

## Scenario E1 — Mutation vs Rebuild

For the same Register:

```text
rebuild(register)
mutation(register)
```

must serialize.

The mutation must not persist or publish derived state in the middle of rebuild.

---

## Scenario E2 — Mutation vs Recovery

For the same Register:

```text
recover(register)
mutation(register)
```

must serialize.

Mutation must not execute against a Register while recovery is reconstructing its derived state.

---

## Scenario E3 — Rebuild vs Rebuild

Two rebuild operations for the same Register must serialize through the same domain.

No overlapping reconstruction of the same Register is permitted.

---

## Scenario E4 — Different Register Isolation

Operations for:

```text
Register A
Register B
```

must not share a serialization boundary.

A blocked operation for A must not prevent B from making progress.

---

# 14. Integration Scenario Group F — Failure Composition

WP-8 must verify failure behavior across component boundaries.

## F1 — Persistence Failure

If authoritative persistence fails during rebuild:

```text
ACTIVE + VALID
```

must not be published.

The resulting state must indicate recovery is required according to the approved failure classification.

---

## F2 — Totals Failure

If Totals reconstruction fails:

```text
ACTIVE + VALID
```

must not be published.

---

## F3 — Unexpected Failure

Unexpected exceptions during rebuild/recovery must produce:

```text
INDETERMINATE
+
RECOVERY_REQUIRED
```

according to the existing maintenance contract.

---

## F4 — Failed Mutation Does Not Publish False Validity

A failed mutation must not leave the maintenance state claiming a successfully maintained Register when the existing contract requires recovery.

---

# 15. Integration Scenario Group G — Query Composition

## G1 — Movement Query Uses Persistence

Movement Query must observe the authoritative Movement Facts.

No Totals dependency is introduced.

---

## G2 — Balance Query Uses Totals

Balance Query must observe the published Totals.

No Movement Query dependency is introduced.

---

## G3 — Query Independence

Movement Query and Balance Query must remain usable without invoking:

```text
RegisterOperationDomain
TotalsMaintenanceCoordinator
```

---

## G4 — Query Does Not Change Maintenance State

Before and after each read-side query:

```text
TotalsMaintenanceState_before
==
TotalsMaintenanceState_after
```

---

# 16. Integration Scenario Group H — Cross-Capability Composition

WP-8 must include at least one complete platform-level scenario:

```text
Bootstrap
   ↓
Establish Movement
   ↓
Movement Query
   ↓
Balance Query
   ↓
Remove Movement
   ↓
Movement Query
   ↓
Balance Query
   ↓
Rebuild
   ↓
Balance Query
   ↓
Recovery
   ↓
Balance Query
```

The purpose is not to introduce a new workflow API.

The purpose is to verify that existing capabilities preserve their contracts when executed as one Register Platform.

The scenario must use public/architectural composition points rather than bypassing components through private internals.

---

# 17. Test Infrastructure

WP-8 may use controlled in-memory test implementations already present in the test suite, including:

```text
InMemoryRegisterFactPersistence
```

and purpose-built test doubles for:

* blocking persistence;
* failing persistence;
* failing Totals;
* indeterminate failure;
* validators.

Test doubles must model the relevant public contract only.

They must not introduce behavior that the production architecture does not define.

Concurrency tests may use:

```text
threading.Event
threading.Thread
```

to create deterministic coordination points.

Tests must not rely on arbitrary timing where an explicit synchronization primitive can be used.

---

# 18. Public Boundary Requirement

Integration tests must prefer the approved public package boundary:

```python
from accore.platform.registers import ...
```

where practical.

Tests that verify internal composition may use implementation modules when necessary, but such usage must be limited to testing the specific internal integration mechanism.

WP-8 must not accidentally redefine internal module paths as public API.

---

# 19. Production-Code Scope

WP-8 is primarily a test/integration verification work package.

Expected production-code change:

```text
none
```

unless integration testing exposes an actual architectural inconsistency between:

* approved Architecture Definition;
* approved Concrete API Design;
* current production implementation.

If such a mismatch is discovered, implementation must stop and the architecture/API document must be reconciled before introducing production changes.

No production abstraction should be added merely to make an integration test easier to write.

---

# 20. Explicitly Prohibited Test Shortcuts

WP-8 tests must not:

1. mutate `_applied` directly;
2. mutate maintenance state directly;
3. inject fake Totals values into production state;
4. bypass Operation Domain serialization when testing mutation/rebuild/recovery composition;
5. reconstruct Balance by querying Movement Facts;
6. reconstruct Movement Query from Totals;
7. treat private implementation fields as authoritative state;
8. introduce a test-only facade that hides the actual architecture;
9. depend on arbitrary sleeps for synchronization where Events/Barriers can be used;
10. assert implementation details that are not part of an approved contract.

Private implementation inspection is allowed only when the test specifically verifies an internal invariant that cannot be observed through the public contract, and such tests must remain clearly scoped as integration/infrastructure tests.

---

# 21. Acceptance Criteria

WP-8 is complete when:

### Composition

* mutation composes persistence, validation, maintenance, and Totals correctly;
* rebuild composes persistence and Totals reconstruction correctly;
* recovery composes through rebuild semantics;
* Movement Query composes with persisted Movement Facts;
* Balance Query composes with published Totals.

### Serialization

* same-register mutation/rebuild serialization is verified;
* same-register mutation/recovery serialization is verified;
* same-register rebuild/rebuild serialization is verified;
* different-register isolation is verified.

### Lifecycle

* bootstrap admission is verified;
* successful rebuild publishes `ACTIVE + VALID`;
* failed rebuild does not publish `ACTIVE + VALID`;
* recovery restores admission only after successful reconstruction.

### Failure

* persistence failures are verified;
* Totals failures are verified;
* unexpected failures are verified;
* recovery-required semantics are preserved.

### Read Side

* Movement Query does not mutate state;
* Balance Query does not mutate state;
* read-side capabilities do not require operation-domain serialization;
* Balance Query uses Totals rather than recomputing from Movement Facts.

### Regression

* existing Register tests remain green;
* full project tests remain green;
* quality tools remain green.

---

# 22. Expected Test Coverage

WP-8 should add focused integration tests rather than duplicate the existing unit-test suite.

The expected new test areas are approximately:

```text
Bootstrap / Admission
        2–3 tests

Mutation Composition
        2–3 tests

Rebuild Composition
        3–4 tests

Recovery Composition
        2–3 tests

Serialization
        4 tests

Failure Composition
        3–4 tests

Query Composition
        3–4 tests

Cross-Capability Scenario
        1–2 tests
```

The exact number is intentionally not fixed.

Coverage is determined by architectural scenarios, not by an arbitrary test count.

---

# 23. Quality Gate

After WP-8 implementation:

```bash
pytest -q tests/unit/registers/
pytest -q
ruff check .
black .
black --check .
mypy src
```

All checks must pass.

The full Register suite must remain green.

The full project suite must remain green.

---

# 24. Architectural Invariants Preserved

WP-8 must not change the following invariants.

### Invariant 1 — Persistence Authority

```text
Movement Facts in RegisterFactPersistence
=
authoritative operational Register state
```

### Invariant 2 — Totals Derivation

```text
Totals
=
derived state from Movement Facts
```

### Invariant 3 — Register Serialization

```text
one Register
=
one Operation Domain
```

for state-changing operations.

### Invariant 4 — Maintenance Ownership

```text
TotalsMaintenanceCoordinator
=
owner of lifecycle/consistency semantics
```

### Invariant 5 — Runtime Applied State

```text
_applied
=
runtime optimization/state reconstruction aid
```

not persistent authority.

### Invariant 6 — Query Separation

```text
Movement Query
→ Persistence

Balance Query
→ TotalsReader
```

with no cross-dependency.

### Invariant 7 — Recovery

```text
Recovery
→ Rebuild semantics
```

not a second recovery algorithm.

### Invariant 8 — Public API

```text
accore.platform.registers
=
canonical public boundary
```

---

# 25. Final Architectural Decision

WP-8 is defined as a **platform composition verification layer**.

It does not add a new service, facade, coordinator, state machine, persistence layer, or synchronization mechanism.

The integration architecture remains:

```text
                    RegisterOperationDomain
                             │
             ┌───────────────┼───────────────┐
             │               │               │
          Mutation         Rebuild        Recovery
             │               │               │
             └───────────────┼───────────────┘
                             │
                    Totals Maintenance
                             │
                       Totals Engine
                             │
              ┌──────────────┴──────────────┐
              │                             │
       Movement Query                 Balance Query
              │                             │
        Persistence                    TotalsReader
```

The authoritative source remains persisted Movement Facts.

The derived source remains Totals.

The shared Register-scoped serialization boundary remains the Operation Domain.

The maintenance coordinator remains the semantic owner of lifecycle and consistency.

WP-8 therefore provides the final integration evidence that these independently defined capabilities form one coherent Register Platform.

---

# 26. Next Step

After approval of this Architecture Definition / Scope:

1. inspect the exact integration points in the current implementation once more;
2. produce the WP-8 Concrete API / Integration Test Design;
3. review and approve that design;
4. implement the integration tests;
5. run the WP-8 quality gate;
6. reconcile documentation if implementation reveals a genuine architectural mismatch.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
