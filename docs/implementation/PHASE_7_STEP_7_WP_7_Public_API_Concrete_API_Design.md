# PHASE 7 — WP-7 Public API — Concrete API Design

## 1. Purpose

This document defines the concrete public API of the Register Platform for Phase 7 WP-7.

The purpose is to translate the approved WP-7 Architecture Definition / Scope into an exact, testable API contract based on the current implementation.

The document defines:

* the authoritative public import boundary;
* the complete public symbol set;
* package-level exports;
* public concrete implementations;
* public protocols, value objects, results, states, and errors;
* allowed construction and invocation paths;
* intentionally internal implementation symbols;
* the public API regression test matrix.

This document does **not** introduce a new runtime facade or service layer.

The public API boundary remains:

```python
from accore.platform.registers import ...
```

---

# 2. Current Implementation Baseline

The current Register Platform package contains:

```text
accore.platform.registers
├── contracts.py
├── movement.py
├── validation.py
├── mutation.py
├── operation_domain.py
├── totals.py
├── maintenance.py
├── query.py
├── balance.py
└── __init__.py
```

The package-level `__init__.py` already explicitly imports and declares the public API through `__all__`.

WP-7 therefore formalizes the existing boundary rather than creating a new one.

The authoritative public boundary is:

```python
accore.platform.registers
```

Implementation modules remain implementation locations.

---

# 3. Public API Principle

The public Register API is defined by the package-level exports in:

```text
src/accore/platform/registers/__init__.py
```

A symbol is part of the intended public API when:

1. it is explicitly imported into `accore.platform.registers`;
2. it is included in `accore.platform.registers.__all__`;
3. its ownership and lifecycle are defined by the corresponding architecture;
4. it is not an implementation-only helper.

The package-level export list is therefore an architectural boundary, not merely a convenience import list.

Consumers of the Register Platform should depend on:

```python
from accore.platform.registers import Symbol
```

rather than relying on implementation-module imports such as:

```python
from accore.platform.registers.mutation import RegisterMutationOrchestrator
```

Implementation-module imports may exist internally, but they are not the canonical public dependency path.

---

# 4. Complete Public Symbol Set

The following symbols constitute the WP-7 public API.

## 4.1 Movement Model

Public symbols:

```python
Movement
MovementType
MovementAttributes
MovementDimensions
MovementResources
```

### `MovementType`

```python
class MovementType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
```

Purpose:

* identifies the semantic movement type;
* participates in Totals contribution semantics.

### `Movement`

`Movement` is the immutable Register Movement fact model.

It is the primary domain object consumed by:

* validation;
* mutation;
* totals;
* maintenance;
* movement queries.

### `MovementDimensions`

Immutable movement dimension container.

Construction:

```python
MovementDimensions.from_mapping(values)
```

### `MovementResources`

Immutable movement resource container.

Construction:

```python
MovementResources.from_mapping(values)
```

### `MovementAttributes`

Immutable movement attribute container.

Construction:

```python
MovementAttributes.from_mapping(values)
```

The three mapping-backed value objects are public because they form part of the construction and interpretation of the public `Movement` model.

---

# 5. Movement Validation API

Public symbols:

```python
MovementValidationError
MovementValidator
DefaultMovementValidator
```

## 5.1 `MovementValidator`

Protocol defining the validation capability:

```python
class MovementValidator(Protocol):
    def validate(self, movement_set: MovementSetLike) -> None: ...
```

The protocol is public because mutation orchestration depends on validation as a replaceable capability.

## 5.2 `DefaultMovementValidator`

Concrete implementation:

```python
DefaultMovementValidator(contracts: RegisterPostingContractResolver)
```

It resolves Register Posting Contracts and validates a movement set against them.

## 5.3 `MovementValidationError`

Public validation error representing Register Movement validation failure.

---

# 6. Mutation API

Public symbols:

```python
RegisterMutationOrchestrator
RegisterMutationMaintenanceError
```

## 6.1 `RegisterMutationOrchestrator`

Concrete mutation orchestration component.

Construction dependencies:

```python
RegisterMutationOrchestrator(
    persistence=...,
    totals=...,
    domains=...,
    validator=...,
)
```

Public operations:

```python
establish(movements: Sequence[Movement]) -> None
remove(movements: Sequence[Movement]) -> None
```

The orchestrator owns ordinary mutation coordination.

It does not own:

* Register operation serialization;
* Totals lifecycle state;
* persistence implementation;
* query semantics.

## 6.2 `RegisterMutationMaintenanceError`

Public runtime error representing failure of Totals maintenance during mutation orchestration.

---

# 7. Register Operation Domain API

Public symbols:

```python
RegisterOperationDomain
RegisterOperationDomainRegistry
```

## 7.1 `RegisterOperationDomain`

Construction:

```python
RegisterOperationDomain(register_identity)
```

Public property:

```python
register_identity
```

Public operation:

```python
execute(operation: Callable[[], T]) -> T
```

`execute()` is the sole public operation-domain execution boundary.

The implementation deliberately does not expose lock acquisition/release operations.

The following are not public API:

```text
acquire()
release()
lock
RLock
```

The operation domain therefore exposes semantic execution rather than synchronization primitives.

## 7.2 `RegisterOperationDomainRegistry`

Construction:

```python
RegisterOperationDomainRegistry()
```

Public operation:

```python
get(register_identity) -> RegisterOperationDomain
```

The registry provides stable per-register operation domains.

It is the public composition mechanism used by:

* mutation;
* rebuild;
* recovery.

The registry does not own maintenance semantics.

---

# 8. Totals API

Public symbols:

```python
TotalsKey
TotalsDefinition
TotalsReader
TotalsEngine
DefaultTotalsEngine
TotalValue
TotalsError
TotalsDefinitionError
TotalsAggregationError
TotalsRegisterMismatchError
TotalsKeyError
TotalsResourceError
TotalsMovementTypeError
```

## 8.1 `TotalValue`

Public type alias representing the Decimal-based total value contract.

Totals remain Decimal-only.

---

## 8.2 `TotalsKey`

Immutable aggregation key.

Construction:

```python
TotalsKey.from_mapping(values)
```

Read operations include:

```python
values()
get(...)
__getitem__(...)
__iter__(...)
__len__(...)
items()
```

`TotalsKey` is public because it is required to address a current aggregate through the Balance Query API.

---

## 8.3 `TotalsDefinition`

Immutable Register Totals definition.

It defines:

* Register identity;
* aggregation dimensions;
* resource name;
* movement-type signs.

Public semantic operations:

```python
key_for(movement) -> TotalsKey
contribution_for(movement) -> TotalValue
```

`TotalsDefinition` is public because it defines the aggregation contract and is required to construct aggregation keys for Balance queries.

---

## 8.4 `TotalsReader`

Read-only Totals capability:

```python
class TotalsReader(Protocol):
    def get(
        self,
        register_identity: Identifier,
        key: TotalsKey,
    ) -> TotalValue: ...
```

This is the intended dependency boundary for read-side Balance composition.

`BalanceQueryService` depends on `TotalsReader`, not on `TotalsEngine`.

---

## 8.5 `TotalsEngine`

Mutation/rebuild Totals capability:

```python
class TotalsEngine(TotalsReader, Protocol):
    def apply(self, movement: Movement) -> TotalValue: ...
    def remove(self, movement: Movement) -> TotalValue: ...
    def rebuild(
        self,
        register_identity: Identifier,
        movements: Sequence[Movement],
    ) -> None: ...
```

The protocol is public because maintenance and mutation depend on Totals behavior rather than on one concrete implementation.

---

## 8.6 `DefaultTotalsEngine`

Concrete implementation.

Construction:

```python
DefaultTotalsEngine(definitions)
```

Public operations:

```python
get(register_identity, key)
apply(movement)
remove(movement)
rebuild(register_identity, movements)
```

The concrete implementation is public because the current platform has an explicit default Totals implementation and tests/integration composition construct it directly.

---

## 8.7 Totals errors

The following errors are public:

```python
TotalsError
TotalsDefinitionError
TotalsAggregationError
TotalsRegisterMismatchError
TotalsKeyError
TotalsResourceError
TotalsMovementTypeError
```

They form the public Totals failure hierarchy.

Consumers may use these errors when handling Totals failures without depending on implementation-only exception types.

---

# 9. Totals Maintenance API

Public symbols:

```python
MaintenanceOperation
MaintenanceOutcome
MaintenanceResult
TotalsConsistencyState
TotalsLifecycleState
TotalsMaintenanceState
TotalsMaintenanceCoordinator
DefaultTotalsMaintenanceCoordinator
TotalsMaintenanceAdmissionError
```

## 9.1 `MaintenanceOperation`

The public operation enum contains exactly:

```python
APPLY
REMOVE
REBUILD
```

There is intentionally **no**:

```python
RECOVER
```

Recovery is represented by the existing `recover()` API but delegates directly to rebuild semantics.

Consequently:

```python
coordinator.recover(register_identity)
```

returns a `MaintenanceResult` whose operation is:

```python
MaintenanceOperation.REBUILD
```

This is intentional and preserves the approved WP-5 semantic model.

---

## 9.2 `MaintenanceOutcome`

Public result classification:

```python
SUCCESS
FAILURE
INDETERMINATE
```

---

## 9.3 `TotalsLifecycleState`

Public lifecycle states:

```python
CREATED
ACTIVE
MAINTENANCE
```

Recovery requirement is not represented as an additional lifecycle state.

---

## 9.4 `TotalsConsistencyState`

Public consistency states:

```python
VALID
INDETERMINATE
RECOVERY_REQUIRED
```

Recovery requirement is represented through:

```python
TotalsConsistencyState.RECOVERY_REQUIRED
```

rather than a separate lifecycle state.

---

## 9.5 `TotalsMaintenanceState`

Immutable published maintenance state.

It exposes the lifecycle and consistency state of a Register's Totals maintenance.

---

## 9.6 `MaintenanceResult`

Immutable result of a maintenance operation.

The result communicates:

* operation;
* outcome;
* relevant maintenance state/error information defined by the current contract.

The result is the public observation mechanism for maintenance execution.

---

## 9.7 `TotalsMaintenanceCoordinator`

Public maintenance capability:

```python
class TotalsMaintenanceCoordinator(Protocol):
    def apply(self, movement: Movement) -> MaintenanceResult: ...
    def remove(self, movement: Movement) -> MaintenanceResult: ...
    def rebuild(self, register_identity: Identifier) -> MaintenanceResult: ...
    def recover(self, register_identity: Identifier) -> MaintenanceResult: ...
    def state(self, register_identity: Identifier) -> TotalsMaintenanceState: ...
    def ensure_mutation_admitted(self, register_identity: Identifier) -> None: ...
```

This protocol is the semantic owner of Totals lifecycle and consistency state.

---

## 9.8 `DefaultTotalsMaintenanceCoordinator`

Concrete implementation.

Construction dependencies:

```python
DefaultTotalsMaintenanceCoordinator(
    engine=...,
    persistence=...,
)
```

Public operations:

```python
apply(movement)
remove(movement)
rebuild(register_identity)
recover(register_identity)
state(register_identity)
ensure_mutation_admitted(register_identity)
```

Important boundary:

`DefaultTotalsMaintenanceCoordinator` does not expose or own the Register operation lock.

Register-scoped serialization is supplied by:

```python
RegisterOperationDomain
```

and:

```python
RegisterOperationDomainRegistry
```

The maintenance coordinator owns semantic maintenance state, not operation serialization.

---

## 9.9 `TotalsMaintenanceAdmissionError`

Public error raised when mutation is not admitted because Totals maintenance state does not satisfy the admission contract.

The admission contract is:

```text
lifecycle == ACTIVE
and
consistency == VALID
```

---

# 10. Movement Query API

Public symbols:

```python
MovementQueryPeriod
MovementDimensionFilter
MovementQuery
MovementQueryService
DefaultMovementQueryService
MovementQueryValidationError
```

## 10.1 `MovementQueryPeriod`

Immutable period definition.

It validates:

* timezone-aware datetimes;
* `start < end`.

The period semantics are half-open:

```text
[start, end)
```

---

## 10.2 `MovementDimensionFilter`

Immutable partial dimension filter.

Construction:

```python
MovementDimensionFilter.from_mapping(values)
```

The filter performs defensive mapping capture and is safe to use as a query value object.

---

## 10.3 `MovementQuery`

Immutable Movement query.

It defines:

* Register identity;
* optional period;
* optional dimension filter.

---

## 10.4 `MovementQueryService`

Public read capability:

```python
class MovementQueryService(Protocol):
    def query(self, query: MovementQuery) -> tuple[Movement, ...]: ...
```

---

## 10.5 `DefaultMovementQueryService`

Concrete implementation.

Construction:

```python
DefaultMovementQueryService(persistence)
```

The service reads persisted Movement Facts through:

```python
RegisterFactPersistence
```

It does not:

* call Totals;
* invoke maintenance;
* acquire Register operation domains;
* mutate state;
* recompute balances.

Returned movements are deterministicly ordered according to the approved query contract.

---

## 10.6 `MovementQueryValidationError`

Public query validation error.

---

# 11. Balance Query API

Public symbols:

```python
BalanceQuery
BalanceResult
BalanceQueryService
DefaultBalanceQueryService
BalanceQueryError
BalanceQueryValidationError
```

## 11.1 `BalanceQuery`

Immutable Balance query.

It defines:

```text
register_identity
aggregation_scope
```

where `aggregation_scope` is a `TotalsKey`.

---

## 11.2 `BalanceResult`

Immutable Balance result.

It contains:

```text
register_identity
aggregation_scope
value
```

The value is Decimal-based.

---

## 11.3 `BalanceQueryService`

Public read capability:

```python
class BalanceQueryService(Protocol):
    def query(self, query: BalanceQuery) -> BalanceResult: ...
```

---

## 11.4 `DefaultBalanceQueryService`

Concrete implementation.

Construction:

```python
DefaultBalanceQueryService(totals)
```

The dependency type is:

```python
TotalsReader
```

not:

```python
TotalsEngine
```

and not:

```python
TotalsMaintenanceCoordinator
```

The service performs a direct current-total lookup.

It does not recompute a balance from Movement Facts.

It does not invoke maintenance.

It does not acquire a Register Operation Domain.

---

## 11.5 Balance errors

Public errors:

```python
BalanceQueryError
BalanceQueryValidationError
```

`BalanceQueryValidationError` is a specialized `BalanceQueryError` and `ValueError`.

---

# 12. Register Posting Contract API

Public symbols:

```python
RegisterPostingContract
RegisterPostingContractResolver
```

## 12.1 `RegisterPostingContract`

Protocol:

```python
class RegisterPostingContract(Protocol):
    def validate(self, movement: Movement) -> None: ...
```

It defines the Register-specific posting validation capability.

## 12.2 `RegisterPostingContractResolver`

Protocol:

```python
class RegisterPostingContractResolver(Protocol):
    def resolve(
        self,
        register_identity: Identifier,
    ) -> RegisterPostingContract: ...
```

These protocols are public because the public movement-validation construction path depends on them.

---

# 13. Complete `__all__` Contract

The package-level `__all__` must contain exactly the approved public symbol set.

The current implementation provides the following declaration:

```python
__all__ = [
    "BalanceQuery",
    "BalanceQueryError",
    "BalanceQueryService",
    "BalanceQueryValidationError",
    "BalanceResult",
    "DefaultBalanceQueryService",
    "DefaultMovementQueryService",
    "DefaultMovementValidator",
    "DefaultTotalsEngine",
    "DefaultTotalsMaintenanceCoordinator",
    "MaintenanceOperation",
    "MaintenanceOutcome",
    "MaintenanceResult",
    "Movement",
    "MovementAttributes",
    "MovementDimensionFilter",
    "MovementDimensions",
    "MovementQuery",
    "MovementQueryPeriod",
    "MovementQueryService",
    "MovementQueryValidationError",
    "MovementResources",
    "MovementType",
    "MovementValidationError",
    "MovementValidator",
    "RegisterMutationMaintenanceError",
    "RegisterMutationOrchestrator",
    "RegisterOperationDomain",
    "RegisterOperationDomainRegistry",
    "RegisterPostingContract",
    "RegisterPostingContractResolver",
    "TotalValue",
    "TotalsAggregationError",
    "TotalsConsistencyState",
    "TotalsDefinition",
    "TotalsDefinitionError",
    "TotalsEngine",
    "TotalsError",
    "TotalsKey",
    "TotalsKeyError",
    "TotalsLifecycleState",
    "TotalsMaintenanceAdmissionError",
    "TotalsMaintenanceCoordinator",
    "TotalsMaintenanceState",
    "TotalsMovementTypeError",
    "TotalsReader",
    "TotalsRegisterMismatchError",
    "TotalsResourceError",
]
```

This list is the concrete public API declaration for WP-7.

The implementation must not silently add new public symbols to this list without an explicit architecture/API decision.

---

# 14. Public Import Paths

## 14.1 Canonical public imports

Consumers should use:

```python
from accore.platform.registers import Movement
```

```python
from accore.platform.registers import RegisterMutationOrchestrator
```

```python
from accore.platform.registers import RegisterOperationDomainRegistry
```

```python
from accore.platform.registers import DefaultTotalsEngine
```

```python
from accore.platform.registers import DefaultTotalsMaintenanceCoordinator
```

```python
from accore.platform.registers import DefaultMovementQueryService
```

```python
from accore.platform.registers import DefaultBalanceQueryService
```

and equivalent package-level imports for all symbols in `__all__`.

## 14.2 Implementation-module imports

Imports such as:

```python
from accore.platform.registers.mutation import RegisterMutationOrchestrator
```

or:

```python
from accore.platform.registers.totals import DefaultTotalsEngine
```

are implementation-location imports.

They must not be treated as the architectural public contract.

The public contract is the package boundary:

```python
accore.platform.registers
```

This distinction allows internal module organization to evolve without requiring consumers to follow internal layout changes.

---

# 15. Intentionally Internal Symbols

The following implementation symbols are intentionally not public:

```python
_MovementSet
_ImmutableMapping
```

as well as all other names beginning with `_` that are implementation helpers.

In particular, the following must remain internal:

* `_MovementSet`;
* `_ImmutableMapping`;
* internal maintenance state-management helpers;
* internal Totals lookup helpers;
* internal mutation validation helpers;
* internal serialization implementation details;
* internal locks;
* internal persistence interaction helpers.

The public API must expose semantic capabilities, not internal mechanics.

---

# 16. No Public Aggregate Facade

The following abstractions are explicitly not part of the API:

```text
RegisterService
RegisterFacade
RegisterAPI
RegisterApplicationService
RegisterPlatformService
RegisterManager
```

No such class should be introduced merely to provide a single entry point.

The package itself is the public composition boundary.

The API remains capability-oriented:

```text
Movement
Validation
Mutation
Operation Domain
Totals
Maintenance
Movement Query
Balance Query
Posting Contracts
```

This preserves the ownership boundaries already established by Phase 7.

---

# 17. Construction Rules

Public concrete implementations may be directly constructed when their dependency contracts are satisfied.

Examples:

```python
DefaultTotalsEngine(definitions)
```

```python
DefaultTotalsMaintenanceCoordinator(
    engine=engine,
    persistence=persistence,
)
```

```python
RegisterOperationDomainRegistry()
```

```python
DefaultMovementQueryService(
    persistence=persistence,
)
```

```python
DefaultBalanceQueryService(
    totals=totals_reader,
)
```

```python
DefaultMovementValidator(
    contracts=contract_resolver,
)
```

```python
RegisterMutationOrchestrator(
    persistence=persistence,
    totals=maintenance_coordinator,
    domains=operation_domain_registry,
    validator=validator,
)
```

The public API does not prescribe a global dependency container or factory.

Application/platform composition remains outside the Register package.

---

# 18. Invocation Rules

## Mutation

Mutation is invoked through:

```python
orchestrator.establish(movements)
orchestrator.remove(movements)
```

The operation is serialized through the Register Operation Domain internally by the orchestrator.

## Rebuild

Rebuild is invoked through:

```python
domain.execute(
    lambda: coordinator.rebuild(register_identity)
)
```

The operation-domain boundary is required for Register-scoped serialization.

## Recovery

Recovery uses the same boundary:

```python
domain.execute(
    lambda: coordinator.recover(register_identity)
)
```

`recover()` delegates to rebuild semantics.

## Movement Query

Movement Query is read-only:

```python
query_service.query(query)
```

No operation domain is required.

## Balance Query

Balance Query is read-only:

```python
balance_service.query(query)
```

No operation domain or maintenance coordinator is required.

---

# 19. Dependency Boundary Matrix

| Public capability | Primary dependency boundary                              | Must not depend on        |
| ----------------- | -------------------------------------------------------- | ------------------------- |
| Movement          | domain model                                             | maintenance               |
| Validation        | Posting Contract Resolver                                | Totals state              |
| Mutation          | Persistence + Maintenance + Operation Domain + Validator | query services            |
| Operation Domain  | Register identity                                        | maintenance semantics     |
| Totals            | Totals definitions                                       | query services            |
| Maintenance       | Persistence + Totals Engine                              | query services            |
| Movement Query    | RegisterFactPersistence                                  | Totals / maintenance      |
| Balance Query     | TotalsReader                                             | Persistence / maintenance |
| Posting Contracts | Movement                                                 | Totals / query            |
| Package API       | all approved public capabilities                         | internal helper symbols   |

---

# 20. Public Error Boundary

The following error families are intentionally public:

### Movement

```python
MovementValidationError
```

### Mutation

```python
RegisterMutationMaintenanceError
```

### Operation Domain

No additional public synchronization error is introduced by WP-7.

### Totals

```python
TotalsError
TotalsDefinitionError
TotalsAggregationError
TotalsRegisterMismatchError
TotalsKeyError
TotalsResourceError
TotalsMovementTypeError
```

### Maintenance

```python
TotalsMaintenanceAdmissionError
```

### Movement Query

```python
MovementQueryValidationError
```

### Balance Query

```python
BalanceQueryError
BalanceQueryValidationError
```

Internal implementation exceptions remain internal unless explicitly promoted by architecture.

---

# 21. Public API Stability Rules

The following changes require an explicit architecture/API decision:

1. adding a new symbol to `__all__`;
2. removing a symbol from `__all__`;
3. changing the semantic meaning of an existing public symbol;
4. changing public method signatures;
5. introducing a new public facade;
6. exposing currently internal implementation types;
7. changing the ownership of a public capability;
8. changing the public maintenance state model;
9. changing the public Totals error hierarchy;
10. changing the canonical package import boundary.

Internal refactoring that preserves the package-level API does not by itself require a public API change.

---

# 22. Public API Test Matrix

WP-7 implementation must provide focused tests for the following categories.

## 22.1 Export completeness

Verify that every approved public symbol is available from:

```python
accore.platform.registers
```

and is included in:

```python
accore.platform.registers.__all__
```

## 22.2 Export absence

Verify that implementation-only helpers are not exported.

At minimum:

```python
_MovementSet
_ImmutableMapping
```

must not be package-level public API.

## 22.3 Import construction

Verify that public concrete implementations can be imported and constructed through package-level imports.

Required areas:

* Movement model;
* Validator;
* Mutation Orchestrator;
* Operation Domain;
* Totals Engine;
* Maintenance Coordinator;
* Movement Query;
* Balance Query.

## 22.4 Public invocation

Verify representative invocation of each capability through its public API.

## 22.5 Maintenance API consistency

Verify:

* `MaintenanceOperation` contains `APPLY`, `REMOVE`, `REBUILD`;
* `MaintenanceOperation.RECOVER` does not exist;
* `recover()` remains public;
* recovery returns rebuild semantics;
* lifecycle states remain `CREATED`, `ACTIVE`, `MAINTENANCE`;
* recovery requirement remains represented by `RECOVERY_REQUIRED`.

## 22.6 Read-side isolation

Verify:

* Movement Query does not mutate maintenance state;
* Balance Query does not mutate maintenance state;
* Balance Query depends only on TotalsReader semantics;
* read-side APIs do not require Operation Domain execution.

## 22.7 Operation-domain boundary

Verify:

* `RegisterOperationDomain.execute()` is public;
* per-register domain identity is stable;
* synchronization primitives are not exposed as public API.

## 22.8 Regression

Run the complete existing Register test suite after public API tests.

---

# 23. Acceptance Criteria

WP-7 Concrete API Design is satisfied when:

1. `accore.platform.registers` is the sole canonical public Register package boundary.
2. The complete public symbol set is explicitly documented.
3. accore.platform.registers.__all__ is the authoritative declared package-level public API. Implementation-module imports are not canonical public API paths, even though Python technically permits them.
4. Public concrete implementations are explicitly identified.
5. Public protocols are explicitly identified.
6. Public result/value/state types are explicitly identified.
7. Public error families are explicitly identified.
8. Internal helpers are explicitly excluded.
9. No aggregate Register facade is introduced.
10. Maintenance API reflects the approved WP-5 recovery semantics.
11. `MaintenanceOperation.RECOVER` is not introduced.
12. `recover()` remains a public coordinator capability.
13. Read-side query services remain independent from Operation Domain and maintenance.
14. Balance Query depends on `TotalsReader`, not on the concrete Totals Engine.
15. Public construction paths use package-level imports.
16. Public API tests verify completeness and absence of accidental exports.
17. Existing Register behavior remains unchanged.
18. No new semantic behavior is introduced solely for WP-7.

---

# 24. Explicitly Out of Scope

WP-7 does not include:

* new Register domain semantics;
* new mutation semantics;
* new Totals semantics;
* new maintenance semantics;
* new recovery semantics;
* new query semantics;
* new Balance semantics;
* new persistence abstractions;
* new operation-domain abstractions;
* aggregate Register facade;
* dependency injection framework;
* global service locator;
* package reorganization;
* public exposure of internal helpers;
* changes to existing public method behavior.

---

# 25. Architectural Decision

The Register Platform public API is the package:

```python
accore.platform.registers
```

The package-level `__all__` is the explicit architectural API declaration.

The API exposes the existing capability-oriented Register Platform without introducing an aggregate facade.

The public surface consists of:

```text
Movement Model
Movement Validation
Mutation
Register Operation Domain
Totals
Totals Maintenance
Movement Query
Balance Query
Register Posting Contracts
```

Each capability exposes only the semantic contracts and concrete implementations required by consumers.

Internal implementation helpers remain behind the boundary.

Maintenance recovery remains represented by:

```python
TotalsMaintenanceCoordinator.recover(...)
```

while `MaintenanceOperation` remains limited to:

```python
APPLY
REMOVE
REBUILD
```

Read-side queries remain independent from operation serialization and maintenance.

This Concrete API Design therefore preserves the approved architecture while making the public Register Platform boundary explicit, stable, testable, and independent of internal module layout.

---

# 26. Next Step

After approval of this Concrete API Design, WP-7 implementation consists of:

1. verify/reconcile `__all__` against this document;
2. add focused public API boundary tests;
3. verify package-level construction and invocation paths;
4. verify absence of accidental/internal exports;
5. run the Register test suite;
6. run the project quality gate.

No production abstraction should be added unless implementation reveals a concrete mismatch with this approved API contract.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
