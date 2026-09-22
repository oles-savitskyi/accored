# PHASE 7 — WP-7 Public API

## Architecture Definition / Scope

**Status:** Final — Reconciled with implemented WP-7 state
**Phase:** Phase 7 — Register Totals / Balance
**Work Package:** WP-7 — Public API
**Predecessor:** WP-6 — Query / Balance Composition

---

# 1. Purpose

WP-7 defines and verifies the public API boundary of the Register Platform established during Phase 7.

The purpose of WP-7 is to ensure that the Register Platform exposes a deliberate, stable package-level API for platform consumers while keeping implementation details, synchronization mechanisms, lifecycle internals, and infrastructure-specific details outside that boundary.

WP-7 is therefore primarily an **API boundary definition and verification work package**, not a new Register abstraction or orchestration layer.

The intended public entry point is:

```python
accore.platform.registers
```

Consumers should be able to use the approved Register Platform contracts and concrete implementations through this package boundary without importing internal implementation modules merely to perform normal platform operations.

---

# 2. Architectural Context

The Register Platform currently consists of several already-established architectural areas:

```text
Register Platform
│
├── Movement Model
├── Movement Validation
├── Mutation Orchestration
├── Register Operation Domain
├── Totals
├── Totals Maintenance
├── Movement Query
├── Balance Query
└── Posting Contracts
```

The preceding work packages have already established the semantics and responsibilities of these components.

WP-7 does not redefine those responsibilities.

Instead, it establishes how the existing capabilities are exposed to external consumers.

The resulting boundary is:

```text
External Consumer
        │
        ▼
accore.platform.registers
        │
        ├── Movement
        ├── Validation
        ├── Mutation
        ├── Operation Domain
        ├── Totals
        ├── Maintenance
        ├── Movement Query
        ├── Balance Query
        └── Posting Contracts
```

Internal implementation modules remain implementation details behind that boundary.

---

# 3. Architectural Goal

The goal of WP-7 is to establish a public API that is:

1. explicit;
2. intentional;
3. complete for approved Register Platform capabilities;
4. stable at package level;
5. independent of internal module layout;
6. free of accidental implementation leakage;
7. consistent with the ownership boundaries established by WP-1 through WP-6.

The public API must expose **capabilities and contracts**, not implementation mechanics.

---

# 4. Primary Public Boundary

The canonical Register Platform public boundary is:

```python
accore.platform.registers
```

The package-level API is authoritative for consumers.

Direct imports from implementation modules such as:

```python
accore.platform.registers.mutation
accore.platform.registers.maintenance
accore.platform.registers.totals
accore.platform.registers.query
accore.platform.registers.balance
```

remain implementation-level paths unless a type is explicitly intended as a public package contract.

Normal consumers must not be required to know the internal module layout of the Register Platform.

---

# 5. Public API Areas

The public API is divided into the following capability areas.

## 5.1 Movement Model

Public movement-domain types include the approved representation of Register Movement Facts and their supporting value structures.

This includes the public types required to construct and inspect movement facts.

The public API must not expose internal construction helpers or private storage representations.

---

## 5.2 Movement Validation

The Register Platform exposes the validation contract and its approved default implementation.

The public boundary includes:

* validation protocol/contract;
* validation errors;
* default validation implementation where intentionally exposed.

Validation remains a distinct responsibility and is not absorbed into a new public facade.

---

## 5.3 Mutation

The public API exposes the approved mutation orchestration boundary.

The mutation API is responsible for ordinary Register movement mutation.

It does not become responsible for:

* rebuild;
* recovery;
* balance querying;
* movement querying;
* persistence implementation;
* synchronization primitive management.

The existing mutation orchestration contract remains authoritative.

---

## 5.4 Register Operation Domain

The public API exposes Register-scoped operation serialization through the approved Operation Domain abstraction.

The public abstraction is:

```python
RegisterOperationDomain
```

and its registry:

```python
RegisterOperationDomainRegistry
```

The public operation is:

```python
domain.execute(operation)
```

The public API must not expose lower-level locking operations such as:

```text
acquire()
release()
```

The Operation Domain is a semantic serialization boundary, not a public synchronization primitive.

---

## 5.5 Totals

The public API exposes the approved Totals contracts and implementations required to maintain and read derived Register totals.

This includes the public concepts established in the Totals architecture:

* Totals Definition;
* Totals Key;
* Totals Engine;
* Totals Reader;
* relevant public errors/results.

Totals remain derived state.

The public API must not imply that Totals are the authoritative source of Movement Facts.

---

## 5.6 Maintenance

The public API exposes the approved maintenance contract.

The existing maintenance responsibilities remain owned by:

```python
TotalsMaintenanceCoordinator
```

## Maintenance Public API

The public maintenance contract is:

    apply(movement)
    remove(movement)
    rebuild(register_identity)
    recover(register_identity)
    state(register_identity)
    ensure_mutation_admitted(register_identity)

`recover()` is a public semantic operation of the maintenance coordinator,
but it delegates directly to `rebuild()`.

Therefore `MaintenanceOperation` intentionally contains:

    APPLY
    REMOVE
    REBUILD

and does not contain `RECOVER`.

A successful or failed recovery invocation therefore returns a
`MaintenanceResult` whose `operation` is `MaintenanceOperation.REBUILD`.

This is intentional and preserves the established recovery model:

    recover(register_identity)
            │
            ▼
    rebuild(register_identity)
            │
            ▼
    authoritative Movement Facts
            │
            ▼
       Totals reconstruction

WP-7 must not introduce a separate `RECOVER` operation enum value,
recovery result type, or second recovery abstraction.

In particular, WP-7 does not introduce:

```text
BootstrapCoordinator
RebuildService
RecoveryCoordinator
RegisterService
RegisterFacade
```

or equivalent duplicate abstractions.

---

## 5.7 Movement Query

The public API exposes the approved read-side Movement Query capability.

The public boundary includes:

```text
MovementQuery
MovementQueryPeriod
MovementDimensionFilter
MovementQueryService
DefaultMovementQueryService
```

and associated public validation/error types where applicable.

Movement Query remains read-only.

It does not:

* mutate Movement Facts;
* modify maintenance state;
* rebuild Totals;
* calculate Balance;
* acquire Register operation serialization.

---

## 5.8 Balance Query

The public API exposes the approved Balance Query capability.

The public boundary includes:

```text
BalanceQuery
BalanceResult
BalanceQueryService
DefaultBalanceQueryService
```

and associated public validation/error types.

Balance Query reads already-published Totals through the approved `TotalsReader` capability.

It does not:

* reconstruct Totals from Movement Facts;
* invoke maintenance;
* mutate lifecycle state;
* perform mutation;
* use Register Operation Domain serialization.

---

## 5.9 Posting Contracts

The existing Register Posting contract remains part of the Register Platform public boundary where already established.

WP-7 does not redefine Posting semantics.

Posting continues to depend on Register contracts rather than on internal Register implementation details.

---

# 6. Public vs Internal Boundary

The following distinction is mandatory.

## Public

Public types are intentionally exported from:

```python
accore.platform.registers
```

and form part of the supported Register Platform API.

Examples include:

```text
Movement
MovementDimensions
MovementResources
MovementAttributes

MovementValidator
DefaultMovementValidator

RegisterMutationOrchestrator

RegisterOperationDomain
RegisterOperationDomainRegistry

TotalsDefinition
TotalsKey
TotalsEngine
TotalsReader
DefaultTotalsEngine

TotalsMaintenanceCoordinator
DefaultTotalsMaintenanceCoordinator

MovementQuery
MovementQueryPeriod
MovementDimensionFilter
MovementQueryService
DefaultMovementQueryService

BalanceQuery
BalanceResult
BalanceQueryService
DefaultBalanceQueryService
```

The exact export inventory will be verified against the current repository during Concrete API Design.

---

## Internal

Internal helpers and implementation mechanisms remain outside the package-level public API.

Examples include:

```text
_MovementSet
internal immutable-mapping helpers
private state reconstruction helpers
private synchronization implementation details
internal persistence helpers
internal error-classification helpers
```

The exact internal inventory will be determined from the current implementation during API verification.

The architectural rule is:

> Internal implementation details must not become public merely because they are imported into an implementation module.

---

# 7. `__all__` as Explicit API Declaration

The package-level `__all__` is the explicit declaration of the intended public Register API.

WP-7 must verify:

1. every intentionally public symbol is exported;
2. no unintended internal symbol is exported;
3. exports correspond to approved architectural responsibilities;
4. exports do not create circular dependencies;
5. exports do not expose infrastructure implementation accidentally.

`__all__` is therefore treated as an architectural boundary, not merely a convenience for wildcard imports.

---

# 8. Construction Boundary

A public consumer must be able to construct the approved Register Platform components through the package API.

For example, the intended construction model is conceptually:

```python
from accore.platform.registers import (
    DefaultTotalsEngine,
    DefaultTotalsMaintenanceCoordinator,
    RegisterOperationDomainRegistry,
    RegisterMutationOrchestrator,
    DefaultMovementQueryService,
    DefaultBalanceQueryService,
)
```

The consumer should not need to import an internal module solely because a required public implementation is defined there.

However, public construction does not mean that every concrete implementation in the repository must become public.

Only intentionally supported construction paths are included.

---

# 9. Invocation Boundary

The package API must support the approved operation paths without requiring knowledge of internal implementation structure.

### Mutation

```text
Public Mutation API
        ↓
Register Operation Domain
        ↓
Mutation Orchestration
        ↓
Persistence / Totals
```

### Rebuild / Recovery

```text
Public Maintenance API
        ↓
Register Operation Domain
        ↓
Maintenance Coordinator
        ↓
Persistence → Totals
```

### Movement Query

```text
Public Movement Query API
        ↓
Movement Query Service
        ↓
RegisterFactPersistence
```

### Balance Query

```text
Public Balance Query API
        ↓
Balance Query Service
        ↓
TotalsReader
```

These paths must remain semantically separate.

---

# 10. Ownership Preservation

WP-7 must preserve all ownership decisions established previously.

| Concern                           | Owner                          |
| --------------------------------- | ------------------------------ |
| Register operation serialization  | `RegisterOperationDomain`      |
| Ordinary mutation                 | `RegisterMutationOrchestrator` |
| Lifecycle / maintenance semantics | `TotalsMaintenanceCoordinator` |
| Authoritative Movement Facts      | `RegisterFactPersistence`      |
| Derived Totals                    | `TotalsEngine`                 |
| Movement read-side composition    | `MovementQueryService`         |
| Balance read-side composition     | `BalanceQueryService`          |
| Public package boundary           | `accore.platform.registers`    |

No new owner is introduced by WP-7.

---

# 11. No Public Facade

WP-7 explicitly rejects introduction of a generic Register facade.

The following are out of architectural scope:

```text
RegisterService
RegisterFacade
RegisterAPI
RegisterApplicationService
RegisterPlatformService
```

Such an abstraction would combine independently owned capabilities without providing a new semantic responsibility.

The package itself is the public composition boundary.

---

# 12. Dependency Direction

The public API must preserve existing dependency direction.

The intended direction is:

```text
Consumer
   ↓
Register Public API
   ↓
Register Contracts / Services
   ↓
Platform Infrastructure
```

The Register public API must not reverse this direction by exposing:

* storage provider implementations;
* persistence internals;
* database-specific objects;
* runtime synchronization primitives;
* unrelated Inventory or storage details.

---

# 13. Stability Rule

Once a symbol is intentionally exposed through:

```python
accore.platform.registers
```

it is considered part of the public API and must not be casually renamed, removed, or repurposed.

Conversely, implementation symbols that are intentionally kept outside the package boundary remain free to change internally without requiring public API changes.

This distinction is one of the primary purposes of WP-7.

---

# 14. Error Boundary

Public errors that represent meaningful public contract violations or public operation outcomes may be exported.

Internal exception classes used only for implementation mechanics must remain internal.

The public error surface must therefore be deliberate rather than automatically exposing every exception defined in Register modules.

WP-7 must verify that error exports correspond to actual consumer-facing contracts.

---

# 15. Testing Scope

WP-7 requires focused public API verification tests.

The tests should establish at least:

### 15.1 Export completeness

Every intentionally public symbol is importable from:

```python
accore.platform.registers
```

---

### 15.2 Export absence

Internal symbols are not available through the package's declared public API.

---

### 15.3 Construction

Approved concrete implementations can be constructed through their intended public import paths.

---

### 15.4 Invocation

Approved public services can be invoked without importing internal implementation helpers.

---

### 15.5 API composition

The public API supports the already-approved flows:

```text
Mutation
Movement Query
Balance Query
Maintenance
Operation Domain
```

without introducing additional facade/orchestration objects.

---

### 15.6 Regression

Existing Register semantics remain unchanged.

WP-7 tests must not replace or weaken the existing unit and integration suites.

---

# 16. Implementation Scope

WP-7 implementation is limited to:

1. auditing the current package exports;
2. reconciling `registers/__init__.py` where necessary;
3. adjusting `__all__` where necessary;
4. adding focused public API tests;
5. correcting accidental public/internal leakage if found;
6. correcting import paths required to establish the intended package boundary.

No semantic production behavior should change unless such a change is strictly required to expose an already-approved public contract.

---

# 17. Explicitly Out of Scope

WP-7 does not include:

* new Register domain semantics;
* new mutation semantics;
* mutation admission changes;
* Totals algorithm changes;
* maintenance lifecycle changes;
* rebuild changes;
* recovery changes;
* persistence model changes;
* query semantics changes;
* balance semantics changes;
* Operation Domain semantics changes;
* Inventory integration;
* storage implementation;
* database integration;
* posting semantics;
* new lifecycle state machines;
* new recovery coordinators;
* new Register facade/service;
* persistence of runtime `_applied` state;
* new synchronization mechanisms.

---

# 18. Acceptance Criteria

WP-7 is complete when all of the following are true:

### API boundary

* `accore.platform.registers` is the canonical Register public API boundary.
* The intended public API inventory is explicitly defined.
* Internal implementation details are not accidentally exported.

### Existing contracts

* Mutation API remains unchanged.
* Operation Domain API remains unchanged.
* Maintenance API remains unchanged.
* Movement Query API remains unchanged.
* Balance Query API remains unchanged.
* Totals contracts remain unchanged.

### Construction and usage

* Approved concrete implementations are importable through intended public paths.
* Consumers do not need to know internal module layout for normal usage.
* No new facade/service is required.

### Testing

* Public export tests pass.
* Public construction/invocation tests pass.
* Existing Register unit tests pass.
* Existing full test suite remains green.

### Quality

* `ruff check .` passes.
* `black --check .` passes.
* `mypy src` passes.
* Full `pytest -q` passes.

---

# 19. Architectural Invariants

The following invariants are established for WP-7.

### Invariant 1 — Package Boundary

```text
accore.platform.registers
```

is the canonical public Register API boundary.

### Invariant 2 — No Facade

The package boundary does not imply a new aggregate Register service/facade.

### Invariant 3 — Capability Ownership

Each public capability remains owned by its existing component.

### Invariant 4 — Internal Encapsulation

Implementation details are not public solely because they are imported internally.

### Invariant 5 — Serialization Encapsulation

Register operation serialization is exposed through `RegisterOperationDomain.execute(...)`, not through locking primitives.

### Invariant 6 — Read/Write Separation

Movement Query and Balance Query remain read-side capabilities and do not acquire mutation/rebuild orchestration responsibilities.

### Invariant 7 — Derived State Boundary

Balance remains a read of published Totals and does not become a recomputation service.

### Invariant 8 — Authoritative Fact Boundary

Movement Facts remain authoritative in persistence; the public API must not imply that Totals replace them.

### Invariant 9 — No Semantic Change

WP-7 does not change previously approved Register semantics.

### Invariant 10 — Internal Freedom

Symbols not intentionally exposed by the package boundary remain implementation details and may evolve without constituting public API changes.

---

# 20. Final Architectural Decision

WP-7 establishes **Public API as an explicit package boundary, not as a new runtime abstraction**.

The architecture is therefore:

```text
                    External Consumers
                           │
                           ▼
              ┌─────────────────────────┐
              │ accore.platform.registers│
              │       Public API         │
              └────────────┬────────────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
      Mutation        Maintenance       Read Side
          │                │            ┌────┴────┐
          ▼                ▼            ▼         ▼
   Operation Domain   Totals Engine   Movement   Balance
          │                │           Query      Query
          │                │
          └────────────────┴──────┐
                                   ▼
                         Platform Infrastructure
                                   │
                                   ▼
                       RegisterFactPersistence
```

No additional public orchestration layer is introduced.

## Historical Planning Statement

The next architectural step after approval of this document is **Concrete API Design**, which will specify the exact export inventory, import paths, `__all__` reconciliation, and focused public API test matrix before implementation.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
