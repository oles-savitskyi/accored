# Phase 7 — Step 7

# Platform Implementation Scope

**Status:** Final — Reconciled with implemented WP-4–WP-8 state
**Phase:** Phase 7 — Register Engine
**Step:** Step 7 — Platform Implementation
**Depends on:** Phase 7 Steps 1–6.3
**Primary Contract:** `PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_CONTRACT.md`

---

# 1. Purpose

This document defines the implementation scope for **Phase 7 Step 7 — Platform Implementation**.

Step 7 is the implementation and composition stage of the generic Register Platform established by Phase 7 Steps 2–6.3.

The implementation goal is not to introduce new Register semantics.

The goal is to make the existing contracts form one coherent executable platform:

```text
Movement Fact
     ↓
Persistence
     ↓
Register Mutation
     ↓
Totals Maintenance
     ↓
Derived Totals
     ↓
Balance
```

with:

```text
RegisterOperationDomain
        ↓
same-Register serialization
```

and:

```text
TotalsMaintenanceCoordinator
        ↓
single semantic owner of
lifecycle / consistency /
semantic publication state
```

---

# 2. Implementation Authority

Implementation MUST conform to the following authority order:

1. Phase 7 Step 7 Architecture Definition;
2. Phase 7 Step 7 Platform Implementation Contract;
3. Phase 7 Step 6.3 Register Mutation / Totals Consistency Boundary Contract;
4. Phase 7 Step 6 Lifecycle / Maintenance Contract;
5. Phase 7 Steps 2–5 contracts;
6. Phase 5 Persistence Architecture;
7. existing generic Register domain contracts.

Implementation convenience MUST NOT override an established semantic contract.

---

# 3. Repository Baseline Reviewed

The current repository baseline contains:

```text
src/accore/platform/registers/
    contracts.py
    movement.py
    validation.py
    totals.py
    maintenance.py
    mutation.py
    operation_domain.py
    query.py
    balance.py
```

and corresponding Register unit tests:

```text
tests/unit/registers/
    test_movement.py
    test_mutation.py
    test_operation_domain.py
    test_maintenance.py
    test_maintenance_coordinator.py
    test_totals.py
    test_query.py
    test_balance.py
```

The current baseline also contains the established persistence boundary:

```text
accore.platform.persistence.facts.RegisterFactPersistence
```

and the existing persistence error hierarchy.

---

# 4. Current Implementation Baseline

The current repository already contains concrete implementations for:

* Movement;
* Movement validation;
* Totals Definition;
* TotalsKey;
* Totals Engine;
* Totals Maintenance;
* Movement Query;
* Balance Query;
* Register Mutation Orchestration;
* Register Operation Domain;
* Register Operation Domain Registry.

Therefore Step 7 is NOT a greenfield implementation.

The implementation MUST prefer:

> complete and integrate existing Step 2–6 implementations over replacing them.

Existing correct behavior MUST remain stable unless it is necessary to satisfy an approved Step 7 contract.

---

# 5. Current Component Map

The current implementation maps approximately as follows:

| Responsibility                     | Current module         |
| ---------------------------------- | ---------------------- |
| Movement model                     | `movement.py`          |
| Generic Movement validation        | `validation.py`        |
| Totals semantics                   | `totals.py`            |
| Totals maintenance                 | `maintenance.py`       |
| Ordinary mutation orchestration    | `mutation.py`          |
| Register operation coordination    | `operation_domain.py`  |
| Movement query                     | `query.py`             |
| Balance query                      | `balance.py`           |
| Public Register exports            | `__init__.py`          |
| Authoritative Movement persistence | `persistence/facts.py` |

Step 7 MUST preserve this semantic separation.

---

# 6. Primary Implementation Objective

The implementation MUST establish the following complete composition:

```text
                    Register Definition
                           │
                           ▼
                  Register Platform
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Movement Validation       RegisterOperationDomain
                                         │
                                         ▼
                              RegisterMutationOrchestrator
                                         │
                       ┌─────────────────┴─────────────────┐
                       │                                   │
                       ▼                                   ▼
              RegisterFactPersistence       TotalsMaintenanceCoordinator
                       │                                   │
                       ▼                                   ▼
              Movement Facts                     TotalsEngine
                                                           │
                                                           ▼
                                                      Totals
                                                           │
                                                           ▼
                                                     Balance Query
```

The implementation MUST ensure that this is a real composition boundary rather than merely independent classes that happen to coexist.

---

# 7. Scope Area A — Movement Validation Integration

## 7.1 Objective

Ordinary Register mutation MUST integrate the established generic Movement validation contract.

The current `RegisterMutationOrchestrator` does not itself receive a `MovementValidator`.

Step 7 MUST resolve whether validation occurs:

* before the orchestrator;
* inside the orchestrator;
* or through another established platform boundary.

The implementation MUST establish one authoritative validation path.

## 7.2 Required Behavior

Before authoritative Movement persistence:

* the Movement MUST satisfy generic Register validation;
* invalid input MUST NOT be persisted;
* Totals MUST NOT be modified for rejected input.

## 7.3 Boundary

Validation MUST remain generic.

Standard Configuration-specific business validation MUST remain outside the generic Register Platform.

---

# 8. Scope Area B — Authoritative Movement Persistence

## 8.1 Objective

The implementation MUST use:

```text
RegisterFactPersistence
```

as the sole authoritative Movement persistence boundary.

## 8.2 Required Behavior

`establish` MUST:

1. validate accepted input;
2. enter the Register Operation Domain;
3. persist authoritative Movement Facts;
4. coordinate corresponding Totals maintenance;
5. report the established semantic outcome.

`remove` MUST follow the corresponding established removal contract.

## 8.3 Prohibited

No alternative Movement store may be introduced.

No Totals component may persist Movement Facts.

---

# 9. Scope Area C — Register Operation Domain Integration

## 9.1 Objective

All operations capable of affecting Movement/Totals consistency for one Register MUST share the same logical operation boundary.

The current repository already contains:

```text
RegisterOperationDomain
RegisterOperationDomainRegistry
```

and `RegisterMutationOrchestrator` uses the registry.

## 9.2 Required Operations

The same Register-scoped domain MUST cover:

* establish;
* remove;
* rebuild;
* recover.

## 9.3 Critical Integration Requirement

The implementation MUST NOT introduce separate competing operation domains for:

* mutation;
* rebuild;
* recovery.

The current internal locks inside `DefaultTotalsMaintenanceCoordinator` MAY remain as implementation-level protection, but they MUST NOT become an alternative logical operation boundary.

The semantic consistency boundary remains the `RegisterOperationDomain`.

---

# 10. Scope Area D — Totals Maintenance Integration

## 10.1 Objective

`TotalsMaintenanceCoordinator` MUST remain the single semantic owner of:

* lifecycle state;
* consistency state;
* semantic publication state;
* maintenance transitions.

## 10.2 Required Behavior

The implementation MUST preserve:

```text
CREATED
ACTIVE
MAINTENANCE
```

and:

```text
VALID
INDETERMINATE
RECOVERY_REQUIRED
```

according to the Step 6 contracts.

## 10.3 Runtime State

The existing `_applied` runtime structure MAY remain.

It MUST remain:

* non-authoritative;
* non-durable;
* process-local;
* reconstructible from authoritative Movement Facts.

It MUST NOT become a substitute for persistence.

---

# 11. Scope Area E — Mutation Orchestration

The current:

```text
RegisterMutationOrchestrator
```

is the ordinary mutation boundary.

Step 7 MUST make this boundary conform completely to the approved contract.

## 11.1 Establish

The implementation MUST establish:

```text
validation
    ↓
RegisterOperationDomain
    ↓
Movement persistence
    ↓
Totals maintenance
    ↓
semantic outcome
```

## 11.2 Remove

The implementation MUST establish the corresponding:

```text
validation / admissibility
    ↓
RegisterOperationDomain
    ↓
Movement removal
    ↓
Totals removal
    ↓
semantic outcome
```

according to the established removal semantics.

## 11.3 Failure

The implementation MUST preserve the Step 6.3 rule:

> successful persistence followed by Totals failure MUST NOT be reported as successful mutation.

The authoritative Movement Fact remains authoritative and recovery remains possible.

---

# 12. Scope Area F — Mutation Result and Error Surface

The current implementation raises `RuntimeError` when Totals maintenance does not return `SUCCESS`.

Step 7 MUST review this behavior against the approved error/outcome contract.

The implementation MUST preserve the semantic distinction between:

* validation failure;
* expected operational failure;
* indeterminate outcome;
* recovery-required state.

The implementation MUST NOT reduce these states to an undifferentiated `RuntimeError` where doing so would hide the established semantic outcome.

Concrete exception design MUST be determined during Concrete API Design.

---

# 13. Scope Area G — Rebuild

Register-scoped rebuild is a maintenance operation of
`TotalsMaintenanceCoordinator`. `RegisterMutationOrchestrator` does not expose
`rebuild()` or `recover()`.

The required composition is:

```text
RegisterOperationDomainRegistry
        ↓
RegisterOperationDomain
        ↓
TotalsMaintenanceCoordinator.rebuild()
        ↓
RegisterFactPersistence.enumerate()
        ↓
TotalsEngine.rebuild()
```

Step 7 MUST ensure that every Register-scoped rebuild invocation participating
in the operation domain resolves the shared RegisterOperationDomain through
RegisterOperationDomainRegistry and invokes
TotalsMaintenanceCoordinator.rebuild() through that domain.

The Register Operation Domain is the single Register-scoped serialization
boundary for the complete rebuild operation.

Accordingly, the complete rebuild operation MUST execute within the same
operation domain:

authoritative Movement enumeration;
Totals reconstruction;
runtime maintenance-state reconstruction;
final maintenance-state transition.

A successful rebuild MUST establish the terminal maintenance state:

ACTIVE + VALID

A failed rebuild MUST NOT report:

ACTIVE + VALID

Failure semantics remain governed by the approved maintenance lifecycle and
failure contract. The operation domain provides serialization only; it does
not own maintenance state, failure state, or rebuild semantics.

Step 7 MUST verify that no Register-scoped rebuild path bypasses the shared
operation domain.

---

# 14. Scope Area H — Recovery

Recovery is a semantic maintenance operation of
`TotalsMaintenanceCoordinator`.

The current implementation reuses rebuild semantics:

```text
recover()
    ↓
rebuild()
```

This implementation reuse is acceptable only when the recovery invocation is
itself executed through the same Register Operation Domain.

The required composition is:

```text
RegisterOperationDomainRegistry
        ↓
RegisterOperationDomain
        ↓
TotalsMaintenanceCoordinator.recover()
        ↓
rebuild()
        ↓
RegisterFactPersistence.enumerate()
        ↓
TotalsEngine.rebuild()
```

Step 7 MUST ensure that every Register-scoped recovery invocation participating
in the operation domain resolves the shared RegisterOperationDomain through
RegisterOperationDomainRegistry and invokes
TotalsMaintenanceCoordinator.recover() through that domain.

Therefore recovery MUST execute within the same Register-scoped serialization
boundary as mutation and rebuild.

Recovery MUST preserve the approved maintenance failure semantics:

authoritative Movement data remains the recovery source;
Totals reconstruction is performed from that authoritative source;
runtime maintenance state is reconstructed consistently with the
reconstructed Totals state;
successful recovery establishes the appropriate valid terminal state;
a failed recovery MUST NOT report ACTIVE + VALID;
an indeterminate or recovery-required outcome MUST remain distinguishable
from successful recovery.

Recovery MUST remain semantically distinct from ordinary mutation even when
its implementation reuses rebuild().

The operation domain provides only Register-scoped execution serialization.
It does not define recovery semantics, maintenance state, failure state, or
the distinction between recovery and ordinary mutation.

Step 7 MUST verify that no Register-scoped recovery path bypasses the shared
operation domain.

---

# 15. Scope Area I — Bootstrap Invariant

The implementation MUST preserve the Step 6.3 bootstrap invariant:

> A coordinator MUST establish derived state from authoritative Movement Facts before performing incremental maintenance against pre-existing Register state not established by that coordinator.

Therefore the implementation MUST explicitly handle the distinction between:

```text
CREATED + INDETERMINATE
```

and:

```text
ACTIVE + VALID
```

An implementation MUST NOT assume that an empty runtime `_applied` structure means the persisted Register has no Movement Facts.

---

# 16. Scope Area J — Totals Engine Integration

The existing `DefaultTotalsEngine` is already a concrete implementation of the approved Totals semantics.

Step 7 MUST NOT redesign:

* TotalsKey;
* TotalsDefinition;
* movement contribution semantics;
* Decimal-only resource semantics;
* Totals calculation rules.

Implementation work is limited to correct composition with maintenance, persistence, mutation, and query layers.

---

# 17. Scope Area K — Movement Query

The existing `DefaultMovementQueryService` already consumes:

```text
RegisterFactPersistence.enumerate()
```

and applies semantic filtering.

Step 7 MUST verify:

* read-only behavior;
* provider independence;
* deterministic result ordering;
* no maintenance side effects;
* no lifecycle/consistency transitions.

No mutation integration belongs in Movement Query.

---

# 18. Scope Area L — Balance Query

The existing Balance Query implementation MUST remain read-only.

Step 7 MUST verify that it:

* consumes Totals;
* respects Balance Query semantics;
* does not rebuild;
* does not recover;
* does not mutate;
* does not transition maintenance state.

No hidden repair behavior is permitted.

---

# 19. Scope Area M — Public Register API

The package-level Register API currently exports:

* Movement;
* Movement queries;
* Balance queries;
* Totals;
* Maintenance;
* Mutation;
* validation contracts.

Step 7 MUST review the final public surface against the Step 7 Contract.

The implementation MUST NOT expose:

* internal locks;
* internal registries unless explicitly required;
* provider-specific objects;
* private maintenance structures;
* implementation-only state.

The exact final public API will be fixed during Concrete API Design.

---

# 20. Scope Area N — State Ownership Verification

The following ownership model is mandatory:

| Component                      | Owns                                        |
| ------------------------------ | ------------------------------------------- |
| `RegisterFactPersistence`      | authoritative Movement persistence          |
| `TotalsEngine`                 | Totals calculation                          |
| `TotalsMaintenanceCoordinator` | lifecycle / consistency / publication state |
| `RegisterOperationDomain`      | execution / serialization                   |
| `RegisterMutationOrchestrator` | ordinary mutation orchestration             |
| `MovementQuery`                | Movement read behavior                      |
| `BalanceQuery`                 | Balance read behavior                       |
| Standard Configuration         | Register semantic definition                |

No implementation change may create another semantic owner.

---

# 21. Scope Area O — Persistence Error Integration

The current maintenance implementation already distinguishes:

```text
PersistenceError
PersistenceIndeterminateError
TotalsError
unexpected exception
```

Step 7 MUST verify that these are mapped to the platform failure taxonomy correctly.

The required semantic distinction is:

```text
deterministic failure
        ≠
indeterminate outcome
```

A provider-specific exception MUST NOT leak through the platform boundary when the established persistence contract requires translation.

---

# 22. Scope Area P — Determinism

The implementation MUST verify deterministic behavior for:

* Totals calculation;
* Totals rebuild;
* Movement Query ordering;
* state transitions;
* recovery.

The implementation MUST NOT introduce dependency on:

* current wall-clock time;
* arbitrary dictionary/set iteration;
* process identity;
* storage-provider ordering;
* external mutable state.

---

# 23. Scope Area Q — Idempotency

Step 7 MUST preserve the operation-specific idempotency semantics already established by Steps 2–6.

The implementation MUST distinguish:

* idempotent mutation semantics;
* runtime `_applied` bookkeeping;
* rebuild repeatability;
* deterministic calculation.

The `_applied` structure MUST NOT be treated as durable idempotency.

---

# 24. Scope Area R — Concurrency

Step 7 MUST validate:

### Same Register

Operations are serialized.

### Different Registers

Operations may execute independently.

### Rebuild

Cannot race with mutation for the same Register.

### Recovery

Cannot race with mutation or rebuild for the same Register.

### Internal Maintenance Lock

Must not contradict the outer logical Register Operation Domain.

---

# 25. Scope Area S — Standard Configuration Boundary

Step 7 MUST NOT introduce:

```text
Inventory
Product
Warehouse
Goods Receipt
Posting
```

specific logic into:

```text
src/accore/platform/registers/
```

Generic Register semantics MAY be parameterized by Register Definition.

No concrete Standard Configuration import is permitted.

---

# 26. Scope Area T — Step 5 / Step 6 Regression Protection

Step 7 MUST preserve all previously accepted behavior from:

* Totals Engine;
* Balance Query;
* Lifecycle/Maintenance;
* Mutation/Totals consistency;
* Movement Query.

Existing tests MUST continue to pass unless a test encodes behavior explicitly superseded by an approved contract.

---

# 27. Reconciled Implementation Status

The implementation gaps identified during the original Step 7 planning baseline have been resolved by WP-4 through WP-8. This section records the final implemented state and replaces the historical gap list.

## GAP-01 — Mutation validation integration

**Resolved.** `RegisterMutationOrchestrator` receives and uses the approved `MovementValidator` boundary before Register-scoped mutation execution.

## GAP-02 — Mutation admission

**Resolved.** Ordinary mutation invokes `TotalsMaintenanceCoordinator.ensure_mutation_admitted(register_identity)` inside the shared `RegisterOperationDomain`. Mutation is admitted only for `ACTIVE + VALID`.

## GAP-03 — Mutation error surface

**Resolved.** Totals maintenance failures are exposed through the approved `RegisterMutationMaintenanceError` semantic boundary rather than an unqualified platform-level `RuntimeError`.

## GAP-04 — Shared logical boundary

**Resolved.** `RegisterOperationDomain` is the Register-scoped serialization boundary. `DefaultTotalsMaintenanceCoordinator` does not own a second Register operation lock; its private synchronization protects coordinator-owned state only.

## GAP-05 — Bootstrap semantics

**Resolved.** A new coordinator starts in `CREATED + INDETERMINATE`. Mutation is blocked until a successful rebuild establishes `ACTIVE + VALID`. Rebuild reconstructs Totals from authoritative persisted Movement Facts.

## GAP-06 — Recovery semantics

**Resolved.** `recover(register_identity)` delegates to rebuild semantics and returns `MaintenanceOperation.REBUILD`; no separate `RECOVER` maintenance operation exists.

## GAP-07 — Public API completion

**Resolved.** The package-level boundary is `accore.platform.registers`, with the explicit `__all__` list defining the authoritative declared public API. No `RegisterService` or `RegisterFacade` abstraction is introduced.

## GAP-08 — Integration tests

**Resolved.** WP-8 integration coverage is implemented and passing. The final repository quality gate recorded for WP-8 includes 27 dedicated operation-domain integration tests, 119 Register tests, and 867 full-project tests, with Ruff, Black, and mypy passing.

# 28. Implementation Work Packages


Implementation SHOULD be organized into the following work packages, aligned with the approved implementation sequence defined by `PHASE_7_STEP_7_CONCRETE_IMPLEMENTATION_PLAN`.

## WP-1 — Mutation Validation Integration

* inspect and integrate the existing mutation validation path;
* verify validation placement at the mutation boundary;
* verify validation failure semantics;
* verify that invalid mutations do not reach persistence or Totals maintenance;
* preserve the existing validation semantics established in previous Steps.

## WP-2 — Mutation Admission / State Ownership

* integrate mutation admission with maintenance lifecycle state;
* verify that mutation is admitted only when the Register is operationally valid;
* verify lifecycle and consistency state ownership;
* complete the establish path;
* complete the remove path;
* preserve the separation between mutation orchestration and maintenance state ownership;
* normalize mutation outcome and error behavior without introducing a second semantic state owner.

## WP-3 — Mutation / Totals Failure Semantics

* verify persistence failure behavior;
* verify persistence indeterminate failure behavior;
* verify Totals failure behavior;
* verify compensation and recovery-required transitions;
* verify that successful lifecycle state is never published after an unsuccessful mutation;
* preserve deterministic versus indeterminate failure distinction.

## WP-4 — Operation Domain Completion

* verify the shared `RegisterOperationDomain` boundary;
* verify that mutation uses the shared operation domain;
* verify same-register serialization;
* verify different-register isolation;
* eliminate semantic duplication between operation-domain orchestration and maintenance coordination;
* verify that the operation domain owns Register-scoped serialization while the maintenance coordinator owns maintenance semantics;
* preserve the approved WP-4 architecture without introducing additional orchestration abstractions.

## WP-5 — Bootstrap / Rebuild / Recovery

* establish the bootstrap invariant for a newly created or reconstructed maintenance coordinator;
* verify that mutation is rejected while maintenance state is not `ACTIVE + VALID`;
* verify that successful rebuild establishes `ACTIVE + VALID`;
* rebuild Totals exclusively from authoritative persisted Movement Facts;
* reconstruct runtime maintenance state from the rebuilt authoritative state;
* execute rebuild inside the shared `RegisterOperationDomain` critical section;
* verify deterministic and idempotent rebuild semantics;
* implement recovery through the rebuild semantics without introducing a separate recovery state owner;
* execute recovery through the same `RegisterOperationDomain` used by ordinary mutation;
* preserve deterministic failure versus indeterminate failure semantics during rebuild and recovery;
* ensure failed rebuild or recovery never publishes `ACTIVE + VALID`;
* verify stale-rebuild protection by serializing rebuild/recovery against mutation for the same Register;
* preserve `_applied` as runtime-only maintenance state and not as a persistent idempotency or recovery source.

## WP-6 — Query / Balance Composition

* verify Movement Query composition;
* verify Balance Query composition;
* verify read-only behavior;
* verify that queries do not mutate persistence;
* verify that queries do not mutate Totals maintenance state;
* verify that queries do not implicitly trigger rebuild or recovery;
* verify that Balance composition consumes the established Totals / movement semantics without introducing hidden repair behavior.

## WP-7 — Public API

* finalize package exports;
* verify public versus internal API boundaries;
* verify public construction and invocation paths;
* remove accidental implementation leakage;
* preserve the established separation between platform contracts and implementation details.

## WP-8 — Platform Integration Tests

Add platform-level tests covering:

* successful establish;
* successful remove;
* mutation validation failure;
* persistence failure;
* persistence indeterminate failure;
* Totals failure;
* mutation admission;
* bootstrap;
* rebuild;
* deterministic and idempotent rebuild;
* recovery;
* rebuild / mutation serialization;
* recovery / mutation serialization;
* same-register serialization;
* different-register isolation;
* Movement Query behavior;
* Balance Query behavior;
* read-only query guarantees;
* absence of hidden rebuild or repair during query operations.

## WP-9 — Documentation Reconciliation

* reconcile implementation documentation with the final implementation;
* reconcile Architecture Definition, Scope, Concrete API Design, and Implementation Plan documents;
* verify terminology and lifecycle-state descriptions;
* verify public API documentation against actual exports;
* document final failure, rebuild, recovery, and serialization semantics;
* remove obsolete or superseded implementation assumptions;
* ensure that all WP-1 through WP-8 architectural decisions are reflected consistently across the documentation set.

## WP-10 — Quality Gate

* run the complete test suite;
* run targeted platform and register tests;
* run Ruff;
* run Black;
* run mypy;
* verify that no unintended files or architectural artifacts remain modified;
* verify repository state and implementation/documentation consistency;
* confirm that all approved WP-1 through WP-9 scope items are complete;
* prepare the implementation for the final Architecture / Code / Documentation Review.

The final review and commit remain outside WP-10:

```text
WP-10 Quality Gate
        ↓
Final Architecture / Code / Documentation Review
        ↓
Step 7 Commit
```

Run:

```text
ruff
black --check
mypy
tests/unit/registers
full pytest
```

and verify the Step 7 acceptance criteria.

---

# 29. Files Expected to Change

The implementation is expected to concentrate changes in:

```text
src/accore/platform/registers/
    mutation.py
    maintenance.py
    operation_domain.py
    __init__.py
```

Potentially:

```text
src/accore/platform/registers/
    validation.py
    query.py
    balance.py
    contracts.py
```

only where required to complete an already established contract.

Tests are expected to change/add under:

```text
tests/unit/registers/
tests/integration/
```

if the repository's established test organization supports an integration layer.

No Standard Configuration implementation should be required for Step 7.

No new persistence provider should be required.

---

# 30. Files That MUST NOT Be Changed Without Explicit Architectural Reason

Step 7 SHOULD NOT modify:

* Totals semantic definitions merely for convenience;
* Balance semantics;
* Movement identity semantics;
* Persistence architecture;
* Storage Provider contracts;
* Phase 5 persistence implementation;
* Posting architecture;
* Standard Configuration business semantics.

Any change to these areas requires explicit architectural justification.

---

# 31. Required Integration Tests

The following integration scenarios are mandatory.

### INT-01 — Establish

```text
Movement
  ↓
validation
  ↓
persistence
  ↓
Totals maintenance
  ↓
ACTIVE + VALID
```

### INT-02 — Remove

```text
Movement
  ↓
persistence removal
  ↓
Totals removal
  ↓
ACTIVE + VALID
```

### INT-03 — Persistence Failure

Persistence failure MUST prevent corresponding Totals mutation.

### INT-04 — Totals Failure

Persistence success + Totals failure MUST NOT produce successful semantic completion.

### INT-05 — Indeterminate Failure

Indeterminate outcome MUST remain distinguishable from deterministic failure.

### INT-06 — Rebuild

```text
Movement Facts
  ↓
fresh Totals
  ↓
ACTIVE + VALID
```

### INT-07 — Recovery

Recovery MUST establish valid derived state from authoritative Movement Facts.

### INT-08 — Bootstrap

A newly created coordinator MUST rebuild before incremental maintenance against pre-existing persisted Movement Facts.

### INT-09 — Same Register

Mutation and rebuild MUST serialize.

### INT-10 — Different Registers

Independent Registers MUST remain independently executable.

### INT-11 — Movement Query

Query MUST not alter state.

### INT-12 — Balance Query

Balance MUST not alter or repair state.

### INT-13 — Provider Independence

Register Platform tests MUST use a persistence abstraction rather than concrete provider details.

### INT-14 — Standard Independence

Generic Register Platform tests MUST NOT require Standard Configuration business logic.

---

# 32. Acceptance Criteria

Implementation Scope is considered fulfilled when:

### S7-01

Every Step 2–6.3 contract has a concrete implementation boundary.

### S7-02

Ordinary mutation has one authoritative orchestration path.

### S7-03

Movement validation occurs before authoritative persistence.

### S7-04

Movement persistence uses only `RegisterFactPersistence`.

### S7-05

Totals maintenance uses only `TotalsEngine` for calculation.

### S7-06

`TotalsMaintenanceCoordinator` is the sole semantic lifecycle/consistency state owner.

### S7-07

`RegisterOperationDomain` is the shared same-Register logical operation boundary.

### S7-08

Mutation, rebuild, and recovery cannot establish contradictory same-Register state through concurrent execution.

### S7-09

Rebuild consumes authoritative Movement Facts only.

### S7-10

Recovery consumes authoritative Movement Facts only.

### S7-11

Failure and indeterminate semantics remain distinguishable.

### S7-12

No false `ACTIVE + VALID` state is published.

### S7-13

Bootstrap semantics are preserved.

### S7-14

Movement Query remains read-only.

### S7-15

Balance Query remains read-only.

### S7-16

Different Registers remain isolated.

### S7-17

No Storage Provider implementation leaks into generic Register Platform code.

### S7-18

No Standard Configuration-specific logic leaks into generic Register Platform code.

### S7-19

The public Register API is coherent and intentional.

### S7-20

Platform-level integration tests cover the complete mutation/rebuild/recovery chain.

---

# 33. Explicit Non-Goals for Implementation

The following MUST NOT appear as incidental Step 7 work:

```text
Inventory Register implementation
Product Register semantics
Warehouse Register semantics
Goods Receipt integration
Posting integration
costing
valuation
period closing
General Ledger
distributed transactions
persistent idempotency infrastructure
async maintenance
new Storage Provider
new persistence architecture
```

If implementation discovers that any of these are required for Step 7, work MUST stop and the architecture boundary MUST be reviewed.

---

# 34. Implementation Sequence

The implementation sequence MUST be:

```text
WP-01 Integration Baseline
        ↓
WP-02 Mutation Boundary
        ↓
WP-03 Operation Domain
        ↓
WP-04 Maintenance Integration
        ↓
WP-05 Query Composition
        ↓
WP-06 Public API
        ↓
WP-07 Integration Tests
        ↓
WP-08 Quality Gate
```

Within each work package:

```text
inspect
  ↓
smallest required change
  ↓
targeted tests
  ↓
full relevant tests
  ↓
review
```

Large speculative refactoring is prohibited.

---

# 35. Repository Integration-Point Review Result

The repository review establishes the following:

### Already structurally present

* Movement model;
* Movement validation;
* Totals Engine;
* Totals Maintenance;
* Mutation Orchestrator;
* Operation Domain;
* Movement Query;
* Balance Query;
* persistence abstraction;
* unit test coverage.

### Requires Step 7 completion

* validation integration into mutation path;
* exact mutation admission behavior;
* complete mutation outcome/error surface;
* bootstrap enforcement;
* shared operation-domain semantics;
* final recovery semantics;
* public API verification;
* platform-level integration tests.

Therefore:

> Step 7 is primarily a **platform composition and correctness completion task**, not a greenfield Register Engine implementation.

---

# 36. Step 7 Implementation Boundary

The implementation boundary is:

```text
                 ┌──────────────────────────┐
                 │   Standard Configuration │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │     Register Platform    │
                 │                          │
                 │  Validation              │
                 │  Mutation                │
                 │  Operation Domain        │
                 │  Persistence abstraction │
                 │  Totals                  │
                 │  Maintenance             │
                 │  Movement Query          │
                 │  Balance Query           │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Persistence Abstraction  │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │    Storage Provider      │
                 └──────────────────────────┘
```

Step 7 ends at the reusable Register Platform boundary.

The next step, Phase 7 Step 8, may consume this platform to implement concrete Inventory Register semantics.

---

# 37. Exit Criteria

Step 7 Implementation Scope is complete when:

* all implementation gaps are understood;
* all integration points are identified;
* no new architecture is required;
* no Step 8 semantics are required;
* mutation boundary is explicit;
* operation boundary is explicit;
* state ownership is explicit;
* persistence authority is explicit;
* rebuild/recovery authority is explicit;
* required integration tests are identified;
* implementation work packages are ordered;
* Concrete API Design can be prepared without architectural ambiguity.

The implementation plan referenced by this original scope has now been executed through WP-4–WP-8. For WP-9, this section is retained only as historical sequencing context. The current implementation state is documented by the reconciled WP-4–WP-8 artifacts and verified by the WP-8 integration and project quality gates.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
