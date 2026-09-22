# Phase 7 — Step 7

# WP-9 — Documentation Reconciliation — Architecture Definition

**Status:** Draft — Architecture Review  
**Phase:** 7 — Register Query & Totals  
**Step:** 7 — Platform Implementation  
**Work Package:** WP-9 — Documentation Reconciliation  
**Depends on:** WP-4 — Operation Domain Completion; WP-5 — Bootstrap / Rebuild / Recovery; WP-6 — Query / Balance Composition; WP-7 — Public API; WP-8 — Platform Integration Tests  
**Document Type:** Architecture Definition  
**Production Code Changes:** None  

---

## 1. Purpose

WP-9 reconciles the Phase 7 Step 7 architecture documentation with the final approved and implemented Register Platform architecture established through WP-4–WP-8.

The purpose of this work package is **documentation reconciliation, not architectural redesign**.

The implementation has progressed beyond several intermediate repository states that are still described in earlier Step 7 documents. Those documents remain useful as architectural history, but portions of them currently describe implementation gaps, provisional integration points, or future work that has since been completed.

WP-9 establishes a single coherent documentation state in which:

1. the current architecture is described according to the implemented ownership boundaries;
2. historical implementation baselines remain distinguishable from the final architecture;
3. public API documentation agrees with the approved package boundary;
4. bootstrap, rebuild, recovery, mutation admission, and failure semantics agree across documents;
5. Operation Domain ownership is described consistently;
6. query and balance capabilities are documented as read-side capabilities;
7. WP-8 integration evidence is reflected as completed evidence rather than pending work;
8. no documentation implies a production abstraction that does not exist;
9. no documentation omits an architectural boundary that is already normative;
10. Step 7 can be treated as a coherent implemented platform before proceeding to later Phase 7 work.

WP-9 does not introduce new Register semantics, new production abstractions, or new public API capabilities.

---

# 2. Architectural Authority

The reconciliation baseline is the current implementation contained in the latest `AcCoreD_cur.zip` archive, together with the approved WP-4–WP-8 architectural decisions.

The current architecture is authoritative where implementation and approved design agree.

Where an older document describes an intermediate implementation state, the older statement is treated as historical and must not override the final architecture.

The reconciliation hierarchy is therefore:

```text
Approved architectural decisions
            ↓
Current implemented contracts and boundaries
            ↓
Current public API
            ↓
Integration evidence from WP-8
            ↓
Historical implementation documents
```

Historical documents remain valuable evidence of architectural evolution, but they are not authoritative descriptions of the final current state when they contain completed implementation gaps.

---

# 3. Current Architectural Baseline

The final Step 7 Register Platform is composed from the following established capabilities:

```text
                         Register Platform

  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Register Operation Domain                              │
  │  Register Operation Domain Registry                     │
  │              │                                          │
  │      ┌───────┼───────────────┐                          │
  │      │       │               │                          │
  │      ▼       ▼               ▼                          │
  │   Mutation Rebuild       Recovery                        │
  │      │       │               │                          │
  │      └───────┼───────────────┘                          │
  │              ▼                                          │
  │   Totals Maintenance Coordinator                       │
  │              │                                          │
  │       ┌──────┴──────┐                                   │
  │       ▼             ▼                                   │
  │ Persistence      Totals Engine                          │
  │       │             │                                   │
  │       ▼             ▼                                   │
  │ Movement Query  Balance Query                            │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
```

The authoritative / derived relationship is:

```text
RegisterFactPersistence
        │
        │ authoritative Movement Facts
        ▼
   Movement Facts
        │
        │ incremental maintenance / rebuild
        ▼
   Totals Engine
        │
        │ current derived aggregate
        ▼
   Balance Query
```

Movement Query reads authoritative Movement Facts directly:

```text
RegisterFactPersistence
        │
        ▼
Movement Query
```

Movement Query does not derive its result from Totals.

Balance Query reads published Totals through the `TotalsReader` capability and does not reconstruct balances from Movement Facts.

---

# 4. Final Responsibility Ownership

WP-9 establishes the following responsibility matrix as the canonical documentation baseline.

| Responsibility | Authoritative owner |
|---|---|
| Register-scoped serialization | `RegisterOperationDomain` |
| Register operation-domain lookup | `RegisterOperationDomainRegistry` |
| Ordinary Movement mutation orchestration | `RegisterMutationOrchestrator` |
| Mutation validation | `MovementValidator` / configured validator implementation |
| Authoritative Movement Fact persistence | `RegisterFactPersistence` |
| Movement read-side querying | `MovementQueryService` / `DefaultMovementQueryService` |
| Totals aggregation | `TotalsEngine` / `DefaultTotalsEngine` |
| Totals lifecycle and consistency state | `TotalsMaintenanceCoordinator` |
| Mutation admission | `TotalsMaintenanceCoordinator.ensure_mutation_admitted()` |
| Rebuild | `TotalsMaintenanceCoordinator.rebuild()` |
| Recovery | `TotalsMaintenanceCoordinator.recover()` using rebuild semantics |
| Balance read-side | `BalanceQueryService` / `DefaultBalanceQueryService` |
| Package-level public API | `accore.platform.registers` and its declared `__all__` |
| Platform integration evidence | WP-8 integration tests |

No additional Register-wide orchestration owner is introduced by WP-9.

In particular, WP-9 does not introduce a `RegisterService`, `RegisterFacade`, transaction manager, or second Register-scoped synchronization abstraction.

---

# 5. Operation Domain Reconciliation

## 5.1 Final Meaning

`RegisterOperationDomain` is the shared Register-scoped serialization boundary for consistency-sensitive state-changing operations.

The final operation model is:

```text
RegisterOperationDomain
        │
        ├── ordinary mutation
        │       └── RegisterMutationOrchestrator
        │
        ├── rebuild
        │       └── TotalsMaintenanceCoordinator.rebuild()
        │
        └── recovery
                └── TotalsMaintenanceCoordinator.recover()
```

The domain exposes the generic execution boundary:

```python
domain.execute(operation)
```

It does not expose operation-specific methods such as `rebuild()` or `recover()`.

## 5.2 Registry Ownership

`RegisterOperationDomainRegistry` owns lookup and identity of the Register operation domains.

For a given Register identity, repeated lookup returns the same domain instance within the registry lifetime.

Conceptually:

```text
RegisterOperationDomainRegistry
            │
            ├── Register A → Domain A
            ├── Register B → Domain B
            └── Register C → Domain C
```

Different Register identities therefore remain independently serialized.

## 5.3 Coordinator Ownership

`TotalsMaintenanceCoordinator` owns maintenance semantics and state.

It does **not** own a second Register-scoped operation lock map.

An internal state lock used to protect the coordinator's own runtime bookkeeping is not a substitute for the Register Operation Domain and must not be documented as one.

This distinction is normative:

```text
Operation Domain
    → Register-scoped operation serialization

Maintenance Coordinator
    → maintenance lifecycle / consistency semantics
```

## 5.4 Documentation Rule

Any older document stating that `DefaultTotalsMaintenanceCoordinator` owns per-Register operation locks must be amended or explicitly marked as historical implementation context.

---

# 6. Mutation Reconciliation

The final mutation composition is:

```text
RegisterMutationOrchestrator
        │
        ├── validate Movement set
        │
        ├── resolve Register Operation Domain
        │
        └── domain.execute(...)
                 │
                 ├── ensure mutation admitted
                 ├── persist Movement Facts
                 └── maintain Totals
```

The mutation path therefore has the following architectural properties:

1. Movement validation occurs before mutation is committed;
2. all Movements in one mutation operation belong to one Register;
3. mutation state changes execute within the Register Operation Domain;
4. mutation admission is enforced by the maintenance capability;
5. authoritative Movement Facts are persisted through `RegisterFactPersistence`;
6. Totals are maintained as derived state;
7. maintenance failures are surfaced according to the approved failure semantics;
8. no separate mutation lock is introduced outside the Operation Domain.

Documentation must not describe validation integration as a pending Step 7 gap.

---

# 7. Bootstrap Reconciliation

A newly constructed maintenance coordinator does not implicitly assume that its Totals state is valid.

The initial state is:

```text
Lifecycle:   CREATED
Consistency: INDETERMINATE
```

Mutation admission is therefore denied until a successful rebuild publishes:

```text
Lifecycle:   ACTIVE
Consistency: VALID
```

Bootstrap is consequently represented by the same authoritative rebuild mechanism used for later reconstruction.

The canonical conceptual flow is:

```text
new coordinator
      │
      ▼
CREATED + INDETERMINATE
      │
      │ successful rebuild
      ▼
ACTIVE + VALID
      │
      ▼
mutation admitted
```

Documentation must not describe bootstrap as a separate Totals initialization algorithm unless it explicitly states that bootstrap uses the established rebuild semantics.

---

# 8. Rebuild Reconciliation

## 8.1 Authoritative Source

`RegisterFactPersistence.enumerate(register_identity)` is the authoritative source for rebuild.

The rebuild process must not reconstruct Totals from:

- previous in-memory Totals state;
- `_applied` runtime bookkeeping;
- query results;
- a prior derived aggregate.

The authoritative relationship remains:

```text
Persistence
   ↓
Movement Facts
   ↓
Fresh Totals reconstruction
```

## 8.2 Derived State Replacement

Rebuild reconstructs a fresh Totals state from the authoritative Movement Facts.

The purpose is to eliminate stale derived state rather than incrementally repair unknown state.

## 8.3 Runtime `_applied`

The coordinator's `_applied` bookkeeping is runtime-only state.

It may be reconstructed as part of a successful rebuild because it supports runtime maintenance behavior, but it is not authoritative persistence and must not be documented as durable state.

## 8.4 Publication Rule

`ACTIVE + VALID` is published only after successful completion of the rebuild operation.

A failed rebuild does not publish a partially reconstructed valid state.

## 8.5 Determinism

Repeated rebuilds against unchanged authoritative Movement Facts must produce the same logical Totals state.

Rebuild must not double-count because previous derived state is discarded/replaced rather than treated as another source of facts.

---

# 9. Recovery Reconciliation

Recovery is not a third independent maintenance algorithm.

The final semantic rule is:

```text
recover(register_identity)
        │
        ▼
rebuild(register_identity)
```

`MaintenanceOperation` therefore contains:

```text
APPLY
REMOVE
REBUILD
```

and does not contain a separate `RECOVER` operation.

Recovery returns the operation/result semantics of rebuild while providing the lifecycle entry point required to restore a Register from an invalid or indeterminate maintenance state.

A successful recovery restores:

```text
ACTIVE + VALID
```

and consequently restores mutation admission.

Documentation must not describe recovery as a separate Totals reconstruction algorithm.

---

# 10. Failure and Consistency Reconciliation

The final maintenance state model is:

```text
Lifecycle:
    CREATED
    ACTIVE
    MAINTENANCE

Consistency:
    VALID
    INDETERMINATE
    RECOVERY_REQUIRED
```

The architecture distinguishes deterministic known failures from unexpected failures.

### Deterministic maintenance failure

A known domain-level failure results in a failure state requiring recovery according to the approved maintenance contract.

### Unexpected failure

An unexpected exception results in an indeterminate state requiring recovery.

Conceptually:

```text
maintenance failure
       │
       ├── known failure
       │       └── FAILURE + RECOVERY_REQUIRED
       │
       └── unexpected failure
               └── INDETERMINATE + RECOVERY_REQUIRED
```

The exact exception classes and result objects remain governed by the approved concrete API and contract documents.

WP-9 does not redefine those exception semantics.

---

# 11. Read-Side Reconciliation

## 11.1 Movement Query

Movement Query is a read-side capability over authoritative persisted Movement Facts.

It does not:

- invoke mutation;
- invoke maintenance;
- acquire the Register Operation Domain;
- rebuild Totals;
- derive facts from Balance or Totals.

Its dependency direction is:

```text
MovementQueryService
        ↓
RegisterFactPersistence
```

## 11.2 Balance Query

Balance Query is a read-side capability over published Totals.

Its dependency direction is:

```text
BalanceQueryService
        ↓
TotalsReader
```

It does not:

- rebuild Totals;
- enumerate Movement Facts;
- participate in mutation serialization;
- invoke recovery.

## 11.3 Non-Interference

Read-side query capabilities do not become another Register-scoped synchronization mechanism.

WP-8 integration evidence confirms that queries compose with mutation and maintenance without becoming part of the state-changing operation boundary.

---

# 12. Public API Reconciliation

The canonical public Register API boundary is:

```text
accore.platform.registers
```

The package-level `__all__` is the authoritative declared public API inventory.

The final architecture does not introduce a facade above this package merely to group capabilities.

The public API exposes approved capabilities and contracts, including:

- Movement types and value objects;
- Movement validation;
- mutation orchestration;
- Operation Domain and registry;
- Totals contracts and implementation;
- maintenance contracts and implementation;
- lifecycle and consistency states;
- Movement Query;
- Balance Query;
- approved error types.

Internal implementation helpers remain outside the declared package API.

In particular, internal helper classes such as `_MovementSet` and `_ImmutableMapping` are not public API symbols.

Documentation must not treat internal module import paths as the canonical public API.

---

# 13. Public API Inventory Reconciliation

The current approved package boundary contains 49 declared public symbols.

The final inventory is:

```text
BalanceQuery
BalanceQueryError
BalanceQueryService
BalanceQueryValidationError
BalanceResult
DefaultBalanceQueryService
DefaultMovementQueryService
DefaultMovementValidator
DefaultTotalsEngine
DefaultTotalsMaintenanceCoordinator
MaintenanceOperation
MaintenanceOutcome
MaintenanceResult
Movement
MovementAttributes
MovementDimensionFilter
MovementDimensions
MovementQuery
MovementQueryPeriod
MovementQueryService
MovementQueryValidationError
MovementResources
MovementType
MovementValidationError
MovementValidator
RegisterMutationMaintenanceError
RegisterMutationOrchestrator
RegisterOperationDomain
RegisterOperationDomainRegistry
RegisterPostingContract
RegisterPostingContractResolver
TotalValue
TotalsAggregationError
TotalsConsistencyState
TotalsDefinition
TotalsDefinitionError
TotalsEngine
TotalsError
TotalsKey
TotalsKeyError
TotalsLifecycleState
TotalsMaintenanceAdmissionError
TotalsMaintenanceCoordinator
TotalsMaintenanceState
TotalsMovementTypeError
TotalsReader
TotalsRegisterMismatchError
TotalsResourceError
```

The inventory above is the reconciliation baseline for documentation.

WP-9 does not add a new symbol to this list.

---

# 14. Enum and State Naming Reconciliation

Documentation and tests must distinguish enum member names from enum values.

The architectural member names are:

```text
MaintenanceOperation:
    APPLY
    REMOVE
    REBUILD

TotalsLifecycleState:
    CREATED
    ACTIVE
    MAINTENANCE

TotalsConsistencyState:
    VALID
    INDETERMINATE
    RECOVERY_REQUIRED
```

Their serialized/internal values are not the architectural names used when documenting the public state model.

This distinction prevents documentation and public API tests from accidentally treating implementation values as the normative member identifiers.

---

# 15. WP-4 Documentation Reconciliation

WP-4 established the Operation Domain completion architecture.

Its architectural target remains valid:

```text
one Register-scoped operation domain
        ↓
shared serialization boundary
        ↓
mutation / rebuild / recovery coordination
```

However, WP-4 documents may contain statements describing the earlier baseline in which `DefaultTotalsMaintenanceCoordinator` maintained its own per-Register locking mechanism.

Those statements must be treated as historical baseline statements.

The final documentation must state that the completed architecture uses the shared `RegisterOperationDomain` rather than parallel Register-scoped operation locks.

WP-4 documentation must also use the actual operation-domain API:

```python
domain.execute(operation)
```

rather than describing operation-specific methods on the domain.

---

# 16. WP-5 Documentation Reconciliation

WP-5 established bootstrap, rebuild, recovery, and mutation-admission semantics.

Those semantics are retained as normative.

The reconciliation requirements are:

1. bootstrap is successful rebuild;
2. initial coordinator state is `CREATED + INDETERMINATE`;
3. mutation requires `ACTIVE + VALID`;
4. persistence is authoritative for rebuild;
5. rebuild reconstructs fresh Totals state;
6. `_applied` is runtime-only;
7. recovery delegates to rebuild;
8. recovery does not require a separate `RECOVER` maintenance operation;
9. successful rebuild/recovery publishes `ACTIVE + VALID` only after completion;
10. failure and indeterminate-state transitions remain consistent with the maintenance contract.

WP-5 documents should not introduce a second synchronization boundary or imply that recovery has an independent reconstruction algorithm.

---

# 17. WP-6 Documentation Reconciliation

WP-6 established read-side composition.

The final documentation must preserve the distinction:

```text
Movement Query
    → authoritative persisted Movement Facts

Balance Query
    → published Totals
```

Neither capability participates in the Register Operation Domain used by state-changing operations.

The documentation must not describe queries as maintenance operations or as alternate mutation paths.

---

# 18. WP-7 Documentation Reconciliation

WP-7 established the package-level public API boundary.

The final documentation must treat:

```text
accore.platform.registers
```

as the canonical public import boundary.

There is no requirement for:

```text
RegisterService
RegisterFacade
```

and WP-9 must not introduce either abstraction merely for documentation symmetry.

The package `__all__` remains the authoritative declared public surface.

Public API verification is complete and therefore must not be described as pending implementation work.

---

# 19. WP-8 Documentation Reconciliation

WP-8 established integration evidence for the completed platform composition.

The current evidence is:

```text
tests/unit/registers/test_operation_domain_integration.py
    27 passed

tests/unit/registers/
    119 passed

full test suite
    867 passed

ruff check .
    passed

black --check .
    passed

mypy src
    passed
```

These results are evidence from the current working state and are not themselves architectural contracts.

The documentation implication is nevertheless important: platform integration testing is **completed evidence**, not a pending Step 7 gap.

The integration tests demonstrate composition across:

- bootstrap;
- mutation;
- rebuild;
- recovery;
- failure behavior;
- Register-scoped serialization;
- Register isolation;
- Movement Query;
- Balance Query;
- cross-capability flows.

WP-9 should reference these tests as verification evidence without duplicating their entire test design into architecture documents.

---

# 20. Legacy Step 7 Scope Gap Reconciliation

The earlier Step 7 scope document contains a section titled:

```text
Current Gaps Identified During Repository Review
```

Several entries describe work that has now been completed.

The following gap categories must no longer be represented as current gaps:

### GAP-01 — Mutation validation integration

The current mutation orchestrator integrates a Movement Validator.

This is a completed implementation state.

### GAP concerning parallel maintenance locks

The current architecture uses the shared Register Operation Domain for Register-scoped serialization.

The maintenance coordinator does not own a second per-Register operation lock map.

### Public API completion gap

WP-7 completed the package-level public API boundary and verification.

The final inventory is defined by `accore.platform.registers.__all__`.

### Platform integration-test gap

WP-8 completed the platform integration test work package.

The integration suite now provides evidence for the approved composition.

### Documentation gap

WP-9 itself addresses the remaining documentation divergence between historical Step 7 material and the completed architecture.

These former gaps may remain in historical documents if clearly labelled as historical baseline observations, but they must not be presented as unresolved current architecture issues.

---

# 21. Historical vs Current Documentation Rule

Step 7 contains documents produced at different points in the architecture and implementation lifecycle.

WP-9 does not require rewriting every historical document as though the intermediate states never existed.

Instead, documentation must use one of the following classifications:

| Classification | Meaning |
|---|---|
| **Current / Normative** | Describes the approved final architecture and must agree with implementation |
| **Historical Baseline** | Describes an earlier implementation state and is retained for architectural history |
| **Superseded** | No longer defines current behavior and should not be used as an implementation authority |
| **Verification Evidence** | Records tests or implementation evidence without defining architecture |

A historical document may retain statements such as “the baseline currently contains X” when that statement is explicitly understood as describing the baseline at the time the document was authored.

A current architecture or contract document must not retain such statements without qualification.

---

# 22. Documentation Ownership Model

The reconciled documentation set should follow this ownership model:

```text
Architecture Definition
    ↓
responsibility and boundary ownership

Contract
    ↓
semantic invariants and normative behavior

Concrete API Design
    ↓
public signatures / composition details

Implementation Plan
    ↓
historical implementation sequence / repository integration

WP-specific Architecture Definition / Scope
    ↓
work-package boundary

WP-specific Concrete API / Test Design
    ↓
implementation or verification detail
```

No document should silently redefine a responsibility owned by another document.

In particular:

- architecture documents define ownership;
- contracts define semantics;
- concrete API documents define concrete interfaces;
- implementation plans define execution sequence;
- integration-test documents define verification scenarios.

---

# 23. Documentation Consistency Invariants

After WP-9, the following statements must be true across the Step 7 documentation set.

## Invariant D-01 — One Register Operation Boundary

All consistency-sensitive state-changing operations for one Register are serialized through the same `RegisterOperationDomain`.

## Invariant D-02 — Coordinator Owns Maintenance Semantics

`TotalsMaintenanceCoordinator` owns lifecycle and consistency state and mutation admission, but not a second Register operation lock map.

## Invariant D-03 — Persistence Is Authoritative

Persisted Movement Facts are authoritative. Totals are derived state.

## Invariant D-04 — Rebuild Is Authoritative Reconstruction

Rebuild reconstructs Totals from `RegisterFactPersistence.enumerate()`.

## Invariant D-05 — Recovery Uses Rebuild

Recovery delegates to rebuild semantics and does not introduce an independent reconstruction algorithm.

## Invariant D-06 — Admission Is State-Based

Mutation is admitted only when maintenance state is:

```text
ACTIVE + VALID
```

## Invariant D-07 — Queries Are Read-Side

Movement Query and Balance Query do not participate in state-changing operation serialization.

## Invariant D-08 — Public API Has One Package Boundary

`accore.platform.registers` is the canonical public API boundary.

## Invariant D-09 — No Extra Facade

No `RegisterService` or `RegisterFacade` is required by the architecture.

## Invariant D-10 — WP-8 Is Completed Evidence

Platform integration tests are completed verification evidence, not an unresolved implementation gap.

---

# 24. Reconciliation Target Document Set

WP-9 should review and reconcile the following Step 7 documentation groups.

## Core Step 7 documents

```text
PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_ARCHITECTURE_DEFINITION.md
PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_CONTRACT.md
PHASE_7_STEP_7_PLATFORM_IMPLEMENTATION_SCOPE.md
PHASE_7_STEP_7_CONCRETE_IMPLEMENTATION_PLAN.md
```

## WP-4 documents

```text
PHASE_7_STEP_7_WP_4_Operation_Domain_Completion_Architecture_Definition.md
PHASE_7_STEP_7_WP_4_Operation_Domain_Completion_Architecture_Scope.md
PHASE_7_STEP_7_WP_4_Operation_Domain_Completion_Architecture_Contract.md
PHASE_7_STEP_7_WP_4_Operation_Domain_Completion_Concrete_API_Design.md
```

## WP-5 document

```text
PHASE_7_STEP_7_WP_5_Bootstrap_Rebuild_Recovery_Concrete_API_Design.md
```

## WP-7 documents

pre-WP-9 names:

```text
PHASE_7_WP_7_Public_API_Architecture_Definition_Scope.md
PHASE_7_WP_7_Public_API_Concrete_API_Design.md
```

## WP-8 documents

pre-WP-9 names:

```text
PHASE_7_WP_8_Platform_Integration_Tests_Architecture_Definition_Scope.md
PHASE_7_WP_8_Platform_Integration_Tests_Concrete_API_Integration_Test_Design.md
```

The list is a reconciliation scope, not a commitment that every document requires substantive rewriting.

A document that already agrees with the final architecture may require only a status/current-state clarification.

---

# 25. Required Reconciliation Actions

The implementation phase of WP-9, after approval of this Architecture Definition, shall perform the following documentation actions.

## Action R-01 — Remove or qualify completed-gap statements

Current-state gap lists must be updated so completed WP-4–WP-8 work is no longer described as pending.

## Action R-02 — Normalize Operation Domain terminology

All current documentation must describe:

```python
domain.execute(operation)
```

as the generic execution boundary.

## Action R-03 — Normalize ownership language

Replace any current-state claim that the maintenance coordinator owns Register-scoped operation serialization with the final ownership model.

## Action R-04 — Normalize rebuild semantics

All current documents must identify `RegisterFactPersistence.enumerate()` as the authoritative rebuild source.

## Action R-05 — Normalize recovery semantics

All current documents must state that recovery uses rebuild semantics.

## Action R-06 — Normalize lifecycle / consistency terminology

Current documents must use the approved state names and distinguish member names from enum values.

## Action R-07 — Normalize public API boundary

Current documents must identify `accore.platform.registers` as the canonical package-level public API.

## Action R-08 — Remove facade implications

No current document may imply the need for `RegisterService` or `RegisterFacade`.

## Action R-09 — Record WP-8 as completed evidence

Current Step 7 status material must reflect completion of platform integration verification.

## Action R-10 — Preserve historical context where useful

Historical implementation plans and baseline observations may remain where they provide useful architectural history, but their status must be unambiguous.

---

# 26. Out of Scope

WP-9 does not:

- change production Python code;
- change public API symbols;
- change lifecycle states;
- change consistency states;
- change Totals semantics;
- change Movement semantics;
- change persistence contracts;
- introduce a transaction manager;
- introduce distributed locking;
- introduce asynchronous maintenance;
- introduce a Register facade;
- redesign queries;
- redesign recovery;
- redesign rebuild;
- modify Inventory-specific architecture;
- modify Posting architecture;
- add new integration tests unless reconciliation reveals an actual missing architectural verification requirement.

If documentation review reveals a genuine implementation/architecture contradiction rather than documentation drift, that contradiction must be raised for separate Architecture Review instead of being silently resolved through WP-9 wording.

---

# 27. Acceptance Criteria

WP-9 Architecture Definition is ready for implementation when the following are approved:

1. the final ownership matrix;
2. the Operation Domain responsibility boundary;
3. the bootstrap/rebuild/recovery model;
4. the persistence-authoritative model;
5. the query read-side boundaries;
6. the package-level public API boundary;
7. the historical/current documentation distinction;
8. the list of documents within reconciliation scope;
9. the explicit prohibition on production-code changes during documentation reconciliation.

WP-9 implementation is complete when:

1. current Step 7 documents no longer contain unqualified obsolete implementation-gap claims;
2. current documents consistently describe the shared Operation Domain;
3. current documents consistently describe rebuild and recovery semantics;
4. current documents consistently describe mutation admission;
5. current documents consistently describe Movement Facts as authoritative;
6. current documents consistently describe Totals as derived state;
7. current documents consistently describe Movement Query and Balance Query as read-side capabilities;
8. current public API documentation matches the package-level API;
9. WP-8 is recorded as completed verification evidence;
10. no current document introduces an unimplemented or unapproved production abstraction.

---

# 28. Review Gate

The next step after approval of this Architecture Definition is **Documentation Reconciliation Implementation**.

That step must first produce the exact amended document set and proposed changes for review before editing the repository documentation.

No production implementation work is authorized by this document.

The intended sequence remains:

```text
WP-9 Architecture Definition
        ↓
Architecture Review
        ↓
Approved reconciliation scope
        ↓
Documentation reconciliation
        ↓
Final document review
        ↓
WP-9 completion
```

---

# 29. Final Architectural Position

WP-9 does not create a new architecture.

It establishes that the final Step 7 architecture already exists and that the documentation must now accurately describe it.

The final architectural position is:

```text
                 Register Platform

 Authoritative facts
        │
        ▼
 RegisterFactPersistence
        │
        ├──────────────► Movement Query
        │
        ▼
 Register Mutation / Maintenance
        │
        │ serialized by
        ▼
 RegisterOperationDomain
        │
        ├── Mutation
        ├── Rebuild
        └── Recovery
                │
                ▼
        TotalsMaintenanceCoordinator
                │
                ▼
           TotalsEngine
                │
                ▼
          Balance Query

 Public boundary:
     accore.platform.registers
```

The architecture deliberately keeps the following distinctions explicit:

```text
Movement Facts  ≠ Totals
Persistence     ≠ Totals Engine
Mutation        ≠ Maintenance
Operation Domain ≠ Maintenance Coordinator
Movement Query  ≠ Balance Query
Historical docs ≠ Current architecture
```

This separation is the basis for the final Step 7 documentation state and provides the documentation baseline for the subsequent Phase 7 work.
