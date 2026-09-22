# Phase 7 — Step 7

# Concrete Implementation Plan

**Status:** Final — Reconciled with implemented WP-4–WP-8 state
**Phase:** Phase 7 — Register Engine
**Step:** Step 7 — Platform Implementation
**Primary Contract:** `PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_CONTRACT.md`
**Implementation Scope:** `PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_SCOPE.md`

---

# 1. Purpose

This document translates the approved Phase 7 Step 7 Platform Implementation Contract and Implementation Scope into a concrete repository implementation plan.

The plan defines:

* exact implementation work packages;
* repository integration points;
* expected code changes;
* expected API changes;
* test changes;
* implementation order;
* intermediate quality gates;
* final acceptance criteria.

This document does not introduce new Register semantics.

---

# 2. Implementation Principle

Step 7 MUST be implemented as a controlled integration of the existing Register Platform components.

The implementation strategy is:

```text
inspect
    ↓
smallest required change
    ↓
targeted tests
    ↓
integration tests
    ↓
quality gate
```

No large speculative refactoring is permitted.

Existing Step 2–6 behavior MUST remain stable unless a change is explicitly required to satisfy the approved Step 7 Contract.

---

# 3. Repository Baseline

The implementation baseline contains:

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
    __init__.py
```

Persistence integration is provided by the established:

```text
RegisterFactPersistence
```

Existing Register tests include:

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

---

# 4. Implementation Dependency Graph

The implementation MUST follow this dependency order:

```text
Register Definition / Contracts
             │
             ▼
       Movement Validation
             │
             ▼
     Movement Persistence
             │
             ▼
 RegisterOperationDomain
             │
             ▼
 RegisterMutationOrchestrator
             │
             ├───────────────┐
             ▼               ▼
 Movement Facts       Totals Maintenance
                             │
                             ▼
                       Totals Engine
                             │
                             ▼
                          Totals
                             │
                             ▼
                       Balance Query
```

Rebuild and recovery use:

```text
RegisterOperationDomain
        ↓
TotalsMaintenanceCoordinator
        ↓
RegisterFactPersistence
        ↓
authoritative Movement Facts
        ↓
fresh Totals
```

---

# 5. Implementation Work Package Overview

Implementation will be performed in the following order:

```text
WP-0  Repository / Integration Verification
  ↓
WP-1  Mutation Validation Integration
  ↓
WP-2  Mutation Admission and State Ownership
  ↓
WP-3  Mutation / Totals Failure Semantics
  ↓
WP-4  Operation Domain Completion
  ↓
WP-5  Bootstrap / Rebuild / Recovery
  ↓
WP-6  Query and Balance Composition Verification
  ↓
WP-7  Public API Completion
  ↓
WP-8  Platform Integration Tests
  ↓
WP-9  Documentation Reconciliation
```

Documentation reconciliation is performed before the final Step 7 checkpoint.

---

# 6. WP-0 — Repository / Integration Verification

## Objective

Before changing code, verify the exact APIs currently present in the repository.

## Files to inspect

```text
src/accore/platform/registers/contracts.py
src/accore/platform/registers/movement.py
src/accore/platform/registers/validation.py
src/accore/platform/registers/totals.py
src/accore/platform/registers/maintenance.py
src/accore/platform/registers/mutation.py
src/accore/platform/registers/operation_domain.py
src/accore/platform/registers/query.py
src/accore/platform/registers/balance.py
src/accore/platform/registers/__init__.py
```

Persistence:

```text
src/accore/platform/persistence/
```

Tests:

```text
tests/unit/registers/
```

## Verification questions

The implementation must establish:

1. exact `Movement` API;
2. exact validator API;
3. exact `RegisterFactPersistence` API;
4. exact `TotalsEngine` API;
5. exact `TotalsMaintenanceCoordinator` API;
6. exact `RegisterMutationOrchestrator` API;
7. exact `RegisterOperationDomain` API;
8. exact query APIs;
9. current package exports;
10. current exception hierarchy.

## Output

No code change is required unless the inspection identifies an already-approved contract violation.

---

# 7. WP-1 — Mutation Validation Integration

## Objective

Establish one authoritative validation path before authoritative Movement persistence.

## Current integration point

```text
RegisterMutationOrchestrator
```

## Required change

The mutation boundary MUST integrate the established Movement validation contract.

The implementation MUST determine the smallest compatible mechanism:

```text
RegisterMutationOrchestrator
        ↓
MovementValidator
        ↓
RegisterFactPersistence
```

or an equivalent already-established abstraction.

## Required invariant

For invalid Movement:

```text
validation failure
        ↓
NO persistence
        ↓
NO Totals mutation
```

## Tests

Extend:

```text
tests/unit/registers/test_mutation.py
```

with:

* invalid Movement rejected;
* persistence not called;
* Totals maintenance not called;
* validation failure remains distinguishable.

## Acceptance

`P7-IMP-01`, `P7-IMP-03`, `P7-IMP-07`.

---

# 8. WP-2 — Mutation Admission and State Ownership

## Objective

Ensure ordinary mutation is admitted according to the authoritative maintenance state without creating a second state owner.

## Authoritative owner

```text
TotalsMaintenanceCoordinator
```

## Execution boundary

```text
RegisterOperationDomain
```

## Mutation boundary

```text
RegisterMutationOrchestrator
```

The three responsibilities MUST remain separate.

## Required behavior

Mutation admission MUST depend on the state defined by Step 6.

The implementation MUST NOT add a new state model.

The implementation MUST NOT duplicate lifecycle or consistency state inside:

* `RegisterMutationOrchestrator`;
* `RegisterOperationDomain`.

## Important distinction

```text
RegisterOperationDomain
    = execution / serialization / admission coordination

TotalsMaintenanceCoordinator
    = semantic lifecycle / consistency state
```

The Operation Domain may consult the authoritative state but does not own it.

## Tests

Add or extend:

```text
tests/unit/registers/test_mutation.py
tests/unit/registers/test_operation_domain.py
tests/unit/registers/test_maintenance_coordinator.py
```

Cases:

* mutation admitted in permitted state;
* mutation rejected in prohibited state;
* rejection does not mutate Movement;
* rejection does not mutate Totals;
* no second state representation is introduced.

---

# 9. WP-3 — Mutation / Totals Failure Semantics

## Objective

Make ordinary mutation conform to the Step 6.3 consistency boundary.

## Required successful flow

```text
validate
    ↓
Operation Domain admission
    ↓
persist Movement Fact
    ↓
maintain Totals
    ↓
establish valid semantic state
    ↓
publish success
```

## Persistence failure

```text
validation
    ↓
persistence failure
    ↓
NO Totals mutation
    ↓
failure
```

## Totals failure

If persistence succeeds and Totals maintenance fails:

```text
Movement Fact
    = authoritative persisted fact

Totals
    = may be inconsistent

Result
    = NOT success
```

The implementation MUST preserve the recovery path.

## Indeterminate outcome

If the persistence or maintenance contract produces an indeterminate outcome:

```text
Result
    = indeterminate

Consistency state
    = according to Step 6
```

The implementation MUST NOT convert this into a successful mutation.

## Current issue to resolve

The current mutation implementation uses a generic `RuntimeError` for certain Totals failures.

Concrete implementation MUST verify whether the existing error hierarchy can express the required semantics.

If not, the smallest platform-level error/result change should be introduced.

## Tests

Extend:

```text
tests/unit/registers/test_mutation.py
tests/unit/registers/test_maintenance_coordinator.py
```

Add integration coverage for:

* persistence failure;
* Totals failure;
* indeterminate persistence failure;
* indeterminate maintenance failure;
* no false success.

---

# 10. WP-4 — Operation Domain Completion

## Objective

Ensure that the same Register-scoped operation domain protects all consistency-sensitive operations.

## Required operations

```text
establish
remove
rebuild
recover
```

All MUST use the same logical Register Operation Domain.

## Current baseline

The current mutation path already uses:

```text
RegisterOperationDomainRegistry
```

The implementation MUST extend the same mechanism to rebuild/recovery if not already complete.

## Internal coordinator lock

`DefaultTotalsMaintenanceCoordinator` uses internal synchronization only to protect coordinator-owned runtime state; it does not provide a second Register-scoped operation domain.

This MAY remain.

However:

```text
internal coordinator lock
        ≠
logical Register Operation Domain
```

The coordinator lock MUST NOT become a competing semantic operation boundary.

## Tests

Add:

```text
tests/unit/registers/test_operation_domain.py
```

and integration tests verifying:

* mutation vs rebuild serialization;
* mutation vs recovery serialization;
* rebuild vs recovery serialization;
* different Register independence.

---

# 11. WP-5 — Bootstrap / Rebuild / Recovery

## 11.1 Bootstrap

The current coordinator may begin in:

```text
CREATED + INDETERMINATE
```

and maintain an in-memory `_applied` structure.

This creates an important invariant:

> Empty `_applied` does not mean that the persisted Register has no Movement Facts.

Therefore incremental maintenance MUST NOT be performed against unknown pre-existing persisted state.

## Required rule

Before incremental maintenance against pre-existing Register data:

```text
authoritative Movement Facts
        ↓
rebuild
        ↓
ACTIVE + VALID
```

must be established according to the Step 6 bootstrap contract.

---

## 11.2 Rebuild

Rebuild MUST use:

```text
RegisterFactPersistence.enumerate(register)
```

as its authoritative source.

It MUST create fresh Totals.

It MUST NOT depend on existing Totals.

It MUST establish the correct maintenance state only after successful reconstruction.

## Expected successful result

```text
ACTIVE + VALID
```

when that is the terminal state defined by Step 6.

---

## 11.3 Recovery

Recovery MUST remain semantically distinct from ordinary mutation.

The current implementation:

```text
recover() → rebuild()
```

may be retained if it satisfies the complete Recovery Contract.

The implementation MUST verify:

* correct admission;
* correct serialization;
* authoritative Movement source;
* correct failure classification;
* correct terminal state;
* correct semantic publication.

## Tests

Extend:

```text
tests/unit/registers/test_maintenance_coordinator.py
```

and add integration tests for:

* empty Register rebuild;
* populated Register rebuild;
* corrupted/invalid Totals recovery;
* indeterminate recovery;
* recovery after Totals failure;
* recovery serialization;
* repeated rebuild determinism.

---

# 12. WP-6 — Query and Balance Composition Verification

## Objective

Verify that read-side components remain strictly read-side.

## Movement Query

Verify:

```text
Movement Facts
    ↓
Movement Query
    ↓
Result
```

with no:

* Totals mutation;
* lifecycle transition;
* consistency repair;
* persistence mutation.

## Balance Query

Verify:

```text
Totals
    ↓
Balance Query
    ↓
Balance Result
```

with no:

* rebuild;
* recovery;
* Movement mutation;
* state transition.

## Tests

Existing:

```text
test_query.py
test_balance.py
```

must continue to pass.

Add composition-level tests if necessary.

---

# 13. WP-7 — Public API Completion

## Objective

Finalize the public Register Platform surface.

## Review

Inspect:

```text
src/accore/platform/registers/__init__.py
```

and all public classes/functions.

The public surface MUST expose only intended Register Platform capabilities.

## Candidate public components

The final API is expected to include established public contracts and implementations for:

* Movement;
* Movement validation;
* Movement Query;
* Totals;
* Totals Maintenance;
* Mutation;
* Operation Domain;
* Balance.

The exact exported symbols MUST be determined from the current repository API and preceding contracts rather than invented during this work package.

## Prohibited exports

Do not expose:

* private locks;
* internal state dictionaries;
* provider implementation details;
* internal helper functions;
* hidden persistence mechanisms.

---

# 14. WP-8 — Platform Integration Tests

Step 7 requires tests that exercise the platform as a composition rather than only isolated units.

## INT-01 — Successful Establish

```text
Movement
    ↓
validation
    ↓
Operation Domain
    ↓
Movement persistence
    ↓
Totals maintenance
    ↓
ACTIVE + VALID
```

Verify:

* Movement persisted;
* Totals updated;
* result successful;
* state valid.

---

## INT-02 — Successful Remove

Verify:

* Movement removal;
* corresponding Totals removal;
* valid final state.

---

## INT-03 — Invalid Movement

Verify:

```text
invalid
    ↓
validation failure
    ↓
no persistence
    ↓
no Totals mutation
```

---

## INT-04 — Persistence Failure

Verify:

```text
persistence failure
    ↓
no Totals mutation
```

---

## INT-05 — Totals Failure

Verify:

```text
persistence success
    ↓
Totals failure
    ↓
NOT successful mutation
```

and that the state remains recoverable.

---

## INT-06 — Indeterminate Failure

Verify:

```text
indeterminate
    ↓
indeterminate/recovery-required state
    ↓
NOT success
```

according to the established Step 6 contract.

---

## INT-07 — Rebuild

Verify:

```text
Movement Facts
    ↓
fresh Totals
    ↓
ACTIVE + VALID
```

---

## INT-08 — Recovery

Verify recovery from a non-valid maintenance state.

---

## INT-09 — Bootstrap

Verify that a coordinator cannot incorrectly perform incremental maintenance against unknown pre-existing persisted Movement Facts.

---

## INT-10 — Same Register Serialization

Verify that conflicting operations on one Register cannot execute concurrently.

---

## INT-11 — Different Register Isolation

Verify that operations on independent Registers are not unnecessarily serialized.

---

## INT-12 — Query Isolation

Verify that Movement Query and Balance Query do not mutate Register state.

---

## INT-13 — Deterministic Rebuild

Run rebuild repeatedly against identical authoritative Movement Facts and verify identical derived Totals.

---

## INT-14 — Standard Independence

Verify that generic Register Platform tests do not require Standard Configuration-specific logic.

---

## INT-15 — Persistence Independence

Verify that Register Platform depends on the persistence abstraction rather than a concrete provider.

---

# 15. WP-9 — Documentation Reconciliation

The repository baseline currently lacks the Step 7 documentation files that were prepared during architecture work.

Before the final Step 7 checkpoint, the following files MUST be present in the repository:

```text
docs/implementation/
    PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_ARCHITECTURE_DEFINITION.md
    PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_CONTRACT.md
    PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_SCOPE.md
    PHASE_7_STEP_7_CONCRETE_IMPLEMENTATION_PLAN.md
```

The repository documents MUST match the final approved versions.

No documentation file may describe a state owner, API, failure rule, or integration boundary that differs from the implementation.

---

# 16. WP-10 — Quality Gate

After implementation:

```text
ruff check
black --check
mypy
tests/unit/registers
full pytest
```

must pass.

Additionally:

```text
git diff
git status
```

must be reviewed for:

* unintended files;
* architecture document drift;
* accidental provider dependencies;
* Standard Configuration leakage;
* debugging code;
* dead code;
* unrelated refactoring.

---

# 17. Exact File Change Strategy

The first implementation pass SHOULD focus on:

```text
src/accore/platform/registers/mutation.py
src/accore/platform/registers/maintenance.py
src/accore/platform/registers/operation_domain.py
tests/unit/registers/test_mutation.py
tests/unit/registers/test_maintenance_coordinator.py
tests/unit/registers/test_operation_domain.py
```

Then, only if required:

```text
src/accore/platform/registers/__init__.py
src/accore/platform/registers/validation.py
src/accore/platform/registers/query.py
src/accore/platform/registers/balance.py
```

New integration tests should be placed according to the repository's existing test organization.

No unrelated source files should be modified.

---

# 18. Implementation Order Inside Mutation

The mutation implementation SHOULD be approached in this order:

```text
1. Validate Movement
        ↓
2. Resolve Register Operation Domain
        ↓
3. Enter Register-scoped operation
        ↓
4. Check authoritative maintenance admission
        ↓
5. Persist Movement Fact
        ↓
6. Apply Totals maintenance
        ↓
7. Evaluate maintenance outcome
        ↓
8. Establish semantic state
        ↓
9. Publish success
```

Any failure before persistence:

```text
NO Movement Fact
NO Totals mutation
```

Persistence failure:

```text
NO Totals mutation
```

Post-persistence Totals failure:

```text
Movement Fact remains authoritative
operation is NOT successful
maintenance state reflects failure
recovery remains possible
```

---

# 19. Implementation Order Inside Rebuild

Rebuild SHOULD follow:

```text
1. Resolve Register Operation Domain
        ↓
2. Enter Register-scoped operation
        ↓
3. Enter maintenance mode if required
        ↓
4. Enumerate authoritative Movement Facts
        ↓
5. Construct fresh Totals
        ↓
6. Validate reconstructed Totals
        ↓
7. Replace derived Totals
        ↓
8. Establish terminal lifecycle/consistency state
        ↓
9. Publish success
```

No existing Totals may be required as an input.

---

# 20. Implementation Order Inside Recovery

Recovery SHOULD follow:

```text
1. Resolve Register Operation Domain
        ↓
2. Enter Register-scoped operation
        ↓
3. Verify recovery admission
        ↓
4. Reconstruct derived state
        ↓
5. Validate reconstructed state
        ↓
6. Establish terminal lifecycle/consistency state
        ↓
7. Publish recovery success
```

If recovery fails, the resulting state MUST follow the Step 6 failure contract.

---

# 21. Error Mapping Strategy

The implementation MUST preserve semantic categories.

Conceptually:

```text
ValidationError
    ↓
deterministic validation failure

PersistenceError
    ↓
expected operational failure

PersistenceIndeterminateError
    ↓
indeterminate / recovery-required

TotalsError
    ↓
maintenance failure according to outcome

Unexpected Exception
    ↓
indeterminate unless the contract explicitly classifies it otherwise
```

The exact final Python exception hierarchy MUST be verified against the existing persistence and Register contracts before implementation.

No implementation may silently downgrade an indeterminate condition.

---

# 22. State Ownership Verification

Every implementation change MUST pass the following ownership test:

### Does this component own Movement Facts?

Only:

```text
RegisterFactPersistence
```

### Does this component calculate Totals?

Only:

```text
TotalsEngine
```

### Does this component own lifecycle/consistency state?

Only:

```text
TotalsMaintenanceCoordinator
```

### Does this component serialize Register operations?

Only:

```text
RegisterOperationDomain
```

### Does this component orchestrate ordinary mutation?

Only:

```text
RegisterMutationOrchestrator
```

### Does this component perform read-only Movement queries?

```text
MovementQuery
```

### Does this component perform read-only Balance projection?

```text
BalanceQuery
```

Any implementation that violates this matrix requires review before proceeding.

---

# 23. Definition of Done Per Work Package

Each work package is complete only when:

1. implementation is complete;
2. targeted tests pass;
3. existing relevant tests pass;
4. no semantic contract changed unintentionally;
5. diff is reviewed;
6. no new architectural dependency was introduced.

Only then may the next work package begin.

---

# 24. Intermediate Checkpoints

The implementation SHOULD use these checkpoints.

## Checkpoint A

After WP-1:

```text
validation → mutation
```

works correctly.

## Checkpoint B

After WP-3:

```text
mutation → persistence → Totals
```

has correct failure semantics.

## Checkpoint C

After WP-5:

```text
mutation / rebuild / recovery
```

share the same Register Operation Domain and correct state ownership.

## Checkpoint D

After WP-8:

all platform-level integration tests pass.

## Checkpoint E

After WP-10:

full quality gate passes.

---

# 25. Prohibited Implementation Shortcuts

The following shortcuts are explicitly prohibited.

### Shortcut 1

Using `_applied` as durable persistence.

### Shortcut 2

Using existing Totals as the authoritative source during rebuild.

### Shortcut 3

Allowing Balance Query to repair invalid state.

### Shortcut 4

Allowing Operation Domain to maintain a second lifecycle/consistency state.

### Shortcut 5

Allowing Mutation Orchestrator to maintain a second lifecycle/consistency state.

### Shortcut 6

Catching every exception and returning success/failure without preserving indeterminate semantics.

### Shortcut 7

Adding Storage Provider-specific logic to Register Platform.

### Shortcut 8

Adding Inventory-specific logic to Register Platform.

### Shortcut 9

Adding a second persistence mechanism.

### Shortcut 10

Performing broad refactoring unrelated to Step 7.

---

# 26. Step 7 Final Acceptance Matrix

| ID    | Requirement                            | Verification                 |
| ----- | -------------------------------------- | ---------------------------- |
| S7-01 | All contracts implemented              | Code review + tests          |
| S7-02 | Single mutation boundary               | Integration test             |
| S7-03 | Validation before persistence          | Unit/integration test        |
| S7-04 | Persistence abstraction only           | Code review                  |
| S7-05 | Totals Engine remains calculation-only | Code review                  |
| S7-06 | Single semantic state owner            | Code review + tests          |
| S7-07 | Shared Operation Domain                | Integration/concurrency test |
| S7-08 | Same-Register serialization            | Concurrency test             |
| S7-09 | Rebuild from Movement Facts            | Integration test             |
| S7-10 | Recovery from authoritative facts      | Integration test             |
| S7-11 | Failure classification                 | Failure tests                |
| S7-12 | No false success                       | Failure tests                |
| S7-13 | Bootstrap invariant                    | Bootstrap test               |
| S7-14 | Movement Query read-only               | Query test                   |
| S7-15 | Balance Query read-only                | Balance test                 |
| S7-16 | Register isolation                     | Concurrency test             |
| S7-17 | Provider independence                  | Architecture/code review     |
| S7-18 | Standard independence                  | Architecture/code review     |
| S7-19 | Public API coherent                    | API review                   |
| S7-20 | Platform integration coverage          | Integration suite            |

---

# 27. Final Implementation Sequence

The complete implementation sequence is:

```text
WP-0 Repository / Integration Verification
                ↓
WP-1 Mutation Validation Integration
                ↓
WP-2 Mutation Admission / State Ownership
                ↓
WP-3 Mutation / Totals Failure Semantics
                ↓
WP-4 Operation Domain Completion
                ↓
WP-5 Bootstrap / Rebuild / Recovery
                ↓
WP-6 Query / Balance Composition
                ↓
WP-7 Public API
                ↓
WP-8 Platform Integration Tests
                ↓
WP-9 Documentation Reconciliation
                ↓
WP-10 Quality Gate
                ↓
Final Architecture / Code / Documentation Review
                ↓
Step 7 Commit
```

---

# 28. Final Implementation Boundary

The completed Step 7 platform MUST provide:

```text
                 Register Definition
                         │
                         ▼
              ┌─────────────────────┐
              │   Register Platform │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     Movement        Mutation        Queries
     Validation      Boundary       / Balance
                         │
                         ▼
                Register Operation
                     Domain
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Movement Persistence    Totals Maintenance
              │                     │
              ▼                     ▼
       Movement Facts         Totals Engine
                                    │
                                    ▼
                                  Totals
```

with:

```text
TotalsMaintenanceCoordinator
        │
        ├── Lifecycle State
        ├── Consistency State
        └── Semantic Publication State
```

and:

```text
RegisterOperationDomain
        │
        ├── establish
        ├── remove
        ├── rebuild
        └── recover
```

This is the concrete implementation target for Phase 7 Step 7.

---

# 29. Exit Criteria

Concrete Implementation Plan is complete when:

* every identified integration gap has an implementation work package;
* implementation order is explicit;
* exact source integration points are identified;
* required tests are identified;
* state ownership is explicit;
* failure semantics are explicit;
* rebuild/recovery semantics are explicit;
* public API work is bounded;
* no Step 8 work is required;
* no new architecture is required.

After approval of this plan, implementation may begin with **WP-0 — Repository / Integration Verification**, followed by **WP-1 — Mutation Validation Integration**.

No implementation outside the defined scope should be performed without revisiting the architecture.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
