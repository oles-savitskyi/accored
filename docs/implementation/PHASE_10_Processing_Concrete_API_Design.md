# Phase 10 — Processing

## Concrete API Design


---

# 40. Progress Propagation Amendment

This amendment clarifies the previously underspecified propagation path of
`ProcessingProgressObserver` from `ProcessingRuntime` to an executing
`Processing` implementation.

The amendment does not change the Processing execution model, command model,
result model, or the role of progress as an observational and non-persistent
concern.

## 40.1 Runtime Boundary

The public runtime entry point remains:

```python
def execute(
    self,
    command: ProcessingCommand,
    progress_observer: ProcessingProgressObserver | None = None,
) -> ProcessingResult[object]:
    ...
```

`ProcessingCommand` does not contain a progress observer. The observer remains
a separate runtime concern rather than part of the business command.

## 40.2 Context Propagation

`ProcessingContext` contains a non-optional `progress_observer`. The runtime is
responsible for constructing the context and supplying this observer.

Therefore a Processing implementation can report progress without depending on
`ProcessingRuntime` internals:

```python
context.progress_observer.report(progress)
```

## 40.3 Observer Adaptation

The runtime performs the following adaptation:

```text
ProcessingRuntime.execute(..., progress_observer)
        |
        +-- observer supplied --> runtime-owned safe adapter
        |
        +-- observer absent  --> runtime-owned no-op observer
                                      |
                                      v
                             ProcessingContext
                                      |
                                      v
                                  Processing
```

The safe adapter forwards notifications to the supplied external observer and
catches observer exceptions. Observer failures therefore cannot interrupt the
Processing execution or alter its business result.

The no-op observer produces no externally visible notification and requires no
conditional progress handling inside Processing implementations.

## 40.4 Responsibility Boundary

`ProcessingRuntime` owns observer adaptation and failure isolation.

`Processing` owns the decision of when and what progress to report.

`ProcessingProgressObserver` remains an external observational mechanism.
Progress notifications are not persisted and do not participate in business
outcome calculation.

## 40.5 Required Slice 3 / Platform Tests

The Slice 3 and Platform test coverage must verify:

1. A Processing can report progress through `ProcessingContext`.
2. A supplied observer receives progress notifications.
3. Execution without an observer remains valid.
4. The no-op observer produces no externally visible notification.
5. An observer exception does not interrupt Processing execution.
6. An observer exception does not alter a successful Processing result.
7. Progress reporting remains observational and non-persistent.

This amendment is part of the approved Phase 10 Concrete API and must be
implemented before Slice 3 is considered complete.

**Status: APPROVED FOR IMPLEMENTATION**

---

## 1. Purpose

Phase 10 introduces a generic Platform Processing mechanism for executing
active business operations through explicit runtime contracts.

The first Standard Configuration Processing is:

**Inventory Derived State Rebuild**

It orchestrates two independently owned subsystem operations:

1. Register Totals Rebuild;
2. Valuation Derived State Rebuild.

Processing owns orchestration semantics only. It does not own Register or
Valuation business semantics.

---

# 2. Package Structure

## 2.1 Platform

```text
src/accore/platform/processing/
├── __init__.py
├── command.py
├── context.py
├── definition.py
├── errors.py
├── progress.py
├── result.py
└── runtime.py
```

The Platform package contains only generic Processing contracts and runtime
infrastructure.

It must not contain Inventory-specific logic.

---

## 2.2 Standard

```text
src/standard/processings/
├── __init__.py
└── inventory_rebuild.py
```

The Standard package contains the concrete Inventory Processing and its
Standard-specific parameter/result types.

---

# 3. Processing Identity

Processing identity identifies a Processing definition.

```python
@dataclass(frozen=True, slots=True)
class ProcessingIdentity:
    value: str
```

Properties:

* immutable;
* value-based;
* suitable for resolution through a Processing mapping;
* not an execution identity;
* not an idempotency key.

Processing identity identifies **what Processing is executed**.

---

# 4. Processing Execution Identity

Each Processing invocation has a separate execution identity.

```python
@dataclass(frozen=True, slots=True)
class ProcessingExecutionIdentity:
    value: UUID
```

The execution identity is used for:

* correlation;
* diagnostics;
* progress observation.

It does **not** provide:

* persistence;
* deduplication;
* idempotency;
* retry semantics;
* recovery semantics.

If the caller does not provide an execution identity, the runtime generates
one.

---

# 5. Processing Definition

```python
@dataclass(frozen=True, slots=True)
class ProcessingDefinition:
    identity: ProcessingIdentity
    name: str
    description: str
```

A Processing definition describes the Processing itself.

The definition is metadata and does not contain runtime dependencies.

---

# 6. Processing Command

```python
@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    processing_identity: ProcessingIdentity
    parameters: object
    runtime_configuration: RuntimeConfigurationContext
    execution_identity: ProcessingExecutionIdentity | None = None
```

The command contains:

* the Processing identity;
* Processing-specific parameters;
* the authoritative runtime configuration snapshot;
* optionally, an execution identity.

`parameters` is intentionally an opaque generic boundary at the runtime level.

Concrete Processings define their own immutable, typed parameter objects.

`Mapping[str, Any]` is not used.

The command does not contain a progress observer.

Progress observation is an execution concern of `ProcessingRuntime`.

The command does not contain subsystem identities such as
`register_identity`.

---

# 7. Runtime Configuration Authority

`RuntimeConfigurationContext` is the authoritative configuration snapshot
for Processing execution.

Processing must not duplicate active configuration state in:

* `ProcessingCommand` parameters;
* Processing-specific configuration fields;
* runtime-owned mutable configuration;
* global state.

The runtime configuration snapshot may contain an immutable, typed
application-specific configuration projection.

This projection is part of the same captured configuration context and is not
a service container.

For Phase 10, Standard Configuration provides:

```python
@dataclass(frozen=True, slots=True)
class StandardRuntimeConfiguration:
    inventory_register_identity: Identifier
```

The exact existing `RuntimeConfigurationContext` construction mechanism is
preserved; the Standard runtime configuration projection is supplied through
that context rather than introducing a second configuration source.

The generic Platform Processing layer does not interpret
`StandardRuntimeConfiguration`.

Only Standard Processing interprets the Standard-specific projection.

For Inventory Derived State Rebuild, the authoritative Register identity is
resolved through:

```text
ProcessingContext
    ↓
RuntimeConfigurationContext
    ↓
StandardRuntimeConfiguration
    ↓
inventory_register_identity
```

The Register identity must not be supplied through
`InventoryDerivedStateRebuildParameters`.

It must not be discovered from a static Standard configuration definition
inside the Processing implementation.

It must not be obtained from a service registry.

---

# 8. Processing Context

```python
@dataclass(frozen=True, slots=True)
class ProcessingContext(Generic[P]):
    execution_identity: ProcessingExecutionIdentity
    runtime_configuration: RuntimeConfigurationContext
    parameters: P
    progress_observer: ProcessingProgressObserver
```

`ProcessingContext` is immutable.

It provides the Processing implementation with:

* execution identity;
* authoritative runtime configuration;
* typed Processing parameters.

The context does not duplicate configuration values already represented by
`RuntimeConfigurationContext`.

The context always contains a valid `ProcessingProgressObserver`. The observer
is supplied by `ProcessingRuntime`; it is never taken from `ProcessingCommand`.
When runtime execution is requested without an external observer, the runtime
provides a no-op observer. When an external observer is supplied, the runtime
provides a runtime-owned safe adapter that isolates observer failures.

---

# 9. Processing Contract

```python
class Processing(Protocol[P, R]):
    @property
    def definition(self) -> ProcessingDefinition:
        ...

    def execute(
        self,
        context: ProcessingContext[P],
    ) -> ProcessingResult[R]:
        ...
```

A Processing:

* exposes its definition;
* receives an immutable execution context;
* performs its business orchestration;
* returns a typed Processing result.

A Processing does not own:

* runtime resolution;
* service registration;
* configuration discovery;
* persistence of generic Processing state;
* scheduling;
* retry infrastructure.

---

# 10. Processing Outcome

```python
class ProcessingOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"
```

The meanings are:

### SUCCESS

The Processing completed successfully according to its business contract.

### FAILURE

The Processing completed with a known unsuccessful business/subsystem
outcome.

### INDETERMINATE

The final state cannot be established with certainty.

`INDETERMINATE` is an execution outcome.

It is not a Processing persistence semantic.

Processing does not introduce a separate persistence state machine.

---

# 11. Processing Result

```python
@dataclass(frozen=True, slots=True)
class ProcessingResult(Generic[R]):
    execution_identity: ProcessingExecutionIdentity
    processing_identity: ProcessingIdentity
    outcome: ProcessingOutcome
    details: R
```

`details` is typed.

Generic `Any`/`object` diagnostic payloads are not introduced.

For Phase 10, Standard Processing returns a typed result containing the
original Register and Valuation subsystem results.

Processing must preserve those results rather than flattening them into
strings or generic diagnostics.

---

# 12. Progress Observation

## 12.1 Progress

```python
@dataclass(frozen=True, slots=True)
class ProcessingProgress:
    completed: int
    total: int
    description: str
```

Progress is:

* observational;
* synchronous;
* optional;
* non-persistent.

Progress reporting must not alter business state.

---

## 12.2 Observer

```python
class ProcessingProgressObserver(Protocol):
    def report(self, progress: ProcessingProgress) -> None:
        ...
```

The observer is supplied separately to runtime execution.

It is not part of `ProcessingCommand`.

Observer failures must not alter the Processing business result.

A Processing implementation reports progress through the observer supplied in
its execution context:

```python
context.progress_observer.report(progress)
```

The observer remains an observational mechanism and is never authoritative
business state.

---

# 13. Processing Runtime

```python
class ProcessingRuntime(Protocol):
    def execute(
        self,
        command: ProcessingCommand,
        progress_observer: ProcessingProgressObserver | None = None,
    ) -> ProcessingResult[object]:
        ...
```

The runtime is responsible for:

1. resolving the Processing;
2. validating Processing identity;
3. validating definition identity;
4. determining execution identity;
5. constructing the typed execution context;
6. invoking the Processing;
7. returning its result.

The runtime does not own `RuntimeConfigurationContext`.

The runtime receives the configuration context through the command for each
execution.

---

## 13.1 Default Runtime

```python
class DefaultProcessingRuntime:
    def __init__(
        self,
        processings: Mapping[ProcessingIdentity, Processing[object, object]],
    ) -> None:
        ...
```

The runtime uses a simple mapping for Processing resolution.

No `ProcessingRegistry` is introduced in Phase 10.

No generic service container is introduced.

The mapping is an explicit composition dependency.

---

# 14. Runtime Resolution and Validation

The runtime validates that:

1. the requested Processing identity exists;
2. the resolved Processing definition has the expected identity.

A mismatch is a runtime configuration/integration error.

Runtime validation errors are not business `FAILURE` or
`INDETERMINATE` outcomes.

---

# 15. Processing Errors

```python
class ProcessingError(Exception):
    ...
```

```python
class ProcessingNotFoundError(ProcessingError):
    ...
```

```python
class ProcessingDefinitionMismatchError(ProcessingError):
    ...
```

```python
class ProcessingExecutionError(ProcessingError):
    ...
```

These exceptions represent Processing/runtime boundary failures.

Expected business and subsystem outcomes are represented by
`ProcessingResult`.

Unexpected implementation exceptions are allowed to propagate.

The generic Processing runtime must not automatically convert arbitrary
unexpected exceptions into `FAILURE` or `INDETERMINATE`.

---

# 16. Standard Processing

## 16.1 Processing Identity

Standard defines a Processing identity for:

**Inventory Derived State Rebuild**

The identity is a Standard-owned constant.

The exact string value follows the existing Standard identity conventions.

---

# 17. Standard Parameters

```python
@dataclass(frozen=True, slots=True)
class InventoryDerivedStateRebuildParameters:
    pass
```

The Processing currently requires no caller-supplied business parameters.

In particular, it does not contain:

```text
register_identity
valuation_key
configuration identity
```

Those values are resolved from authoritative runtime configuration where
required by the Processing contract.

---

# 18. Standard Result

```python
@dataclass(frozen=True, slots=True)
class InventoryDerivedStateRebuildResult:
    register_result: MaintenanceResult
    valuation_result: ValuationRebuildResult
```

The result preserves the complete subsystem results.

No generic diagnostics field is introduced.

---

# 19. Inventory Derived State Rebuild Processing

```python
class InventoryDerivedStateRebuildProcessing:
    def __init__(
        self,
        register_maintenance: TotalsMaintenanceCoordinator,
        valuation_rebuilder: ValuationRebuilder,
    ) -> None:
        ...
```

Dependencies are explicit semantic contracts.

The Processing does not receive:

* persistence providers;
* repositories;
* generic service containers;
* domain engines that it does not directly orchestrate.

---

# 20. Register Rebuild

The Processing resolves:

```text
inventory_register_identity
```

from the authoritative Standard runtime configuration projection.

It invokes:

```python
register_maintenance.rebuild(register_identity)
```

The Processing does not implement Register rebuild semantics.

Register maintenance remains responsible for:

* authoritative Register fact enumeration;
* totals rebuilding;
* persistence handling;
* consistency-state transitions;
* `MaintenanceResult`.

---

# 21. Valuation Rebuild

The Processing invokes the existing Valuation rebuild contract:

```python
valuation_rebuilder.rebuild()
```

This represents rebuilding the configured valuation derived state.

The Processing does not implement:

* valuation algorithms;
* valuation fact reconstruction;
* cost calculation;
* valuation result persistence;
* valuation consistency semantics.

Those responsibilities remain owned by the Valuation subsystem.

`rebuild_for(valuation_key)` remains available as a Valuation-specific API but
is not required by the Phase 10 Standard Processing.

---

# 22. Independent Execution

Register and Valuation rebuild operations are independent.

The Processing must not introduce a dependency:

```text
Register rebuild
    ↓
Valuation rebuild
```

or:

```text
Valuation rebuild
    ↓
Register rebuild
```

When both operations are admissible, both are executed independently.

An unsuccessful result from one operation must not automatically suppress
execution of the other operation.

This ensures that the Processing observes the actual state of both derived
subsystems.

---

# 23. Outcome Aggregation

The Processing aggregates the two subsystem outcomes using the following
precedence:

```text
INDETERMINATE
    >
FAILURE
    >
SUCCESS
```

Therefore:

| Register      | Valuation     | Processing    |
| ------------- | ------------- | ------------- |
| SUCCESS       | SUCCESS       | SUCCESS       |
| FAILURE       | SUCCESS       | FAILURE       |
| SUCCESS       | FAILURE       | FAILURE       |
| FAILURE       | FAILURE       | FAILURE       |
| INDETERMINATE | SUCCESS       | INDETERMINATE |
| SUCCESS       | INDETERMINATE | INDETERMINATE |
| INDETERMINATE | FAILURE       | INDETERMINATE |
| FAILURE       | INDETERMINATE | INDETERMINATE |
| INDETERMINATE | INDETERMINATE | INDETERMINATE |

The complete subsystem results remain available in
`InventoryDerivedStateRebuildResult`.

---

# 24. Configuration Composition

Standard Bootstrap remains responsible for composition.

Conceptually:

```text
Standard Bootstrap
    │
    ├── Register platform
    │     └── TotalsMaintenanceCoordinator
    │
    ├── Valuation platform
    │     └── ValuationRebuilder
    │
    ├── StandardRuntimeConfiguration
    │     └── inventory_register_identity
    │
    └── InventoryDerivedStateRebuildProcessing
          ├── register_maintenance
          └── valuation_rebuilder
```

Processing receives already-composed semantic services.

Processing does not construct those services.

---

# 25. Bootstrap-Time Rebuild vs Explicit Processing

Existing bootstrap-time Register rebuild remains unchanged.

Bootstrap-time initialization:

```text
Standard Bootstrap
    ↓
Register composition
    ↓
initial Register rebuild
```

Explicit Processing execution:

```text
ProcessingRuntime
    ↓
InventoryDerivedStateRebuildProcessing
    ├── Register rebuild
    └── Valuation rebuild
```

These are separate lifecycle concerns.

Phase 10 must not replace or silently alter existing bootstrap initialization
semantics.

---

# 26. Public Platform Exports

The Platform Processing package publicly exports the approved Processing API:

```text
Processing
ProcessingCommand
ProcessingContext
ProcessingDefinition
ProcessingExecutionIdentity
ProcessingIdentity
ProcessingOutcome
ProcessingProgress
ProcessingProgressObserver
ProcessingResult
ProcessingRuntime
DefaultProcessingRuntime
ProcessingError
ProcessingNotFoundError
ProcessingDefinitionMismatchError
ProcessingExecutionError
```

No internal implementation classes are exposed unnecessarily.

---

# 27. Public Standard Exports

Standard Processing exports:

```text
InventoryDerivedStateRebuildProcessing
InventoryDerivedStateRebuildParameters
InventoryDerivedStateRebuildResult
```

Standard-specific configuration projection types are exported according to the
existing Standard configuration API conventions.

---

# 28. Testing Requirements

## 28.1 Platform tests

Tests must cover:

* `ProcessingIdentity`;
* `ProcessingExecutionIdentity`;
* `ProcessingDefinition`;
* `ProcessingCommand`;
* `ProcessingContext`;
* Processing resolution;
* missing Processing;
* definition identity mismatch;
* execution identity generation;
* supplied execution identity preservation;
* Processing invocation;
* result preservation;
* progress observer propagation through `ProcessingContext`;
* progress observer invocation;
* absent progress observer and no-op observer behavior;
* observer failure isolation;
* runtime error boundaries.

---

## 28.2 Standard tests

Tests must cover:

* successful Register + Valuation rebuild;
* Register failure + Valuation success;
* Register success + Valuation failure;
* both failures;
* Register indeterminate + Valuation success;
* Register success + Valuation indeterminate;
* all remaining INDETERMINATE combinations;
* independent invocation of both rebuild operations;
* preservation of `MaintenanceResult`;
* preservation of `ValuationRebuildResult`;
* resolution of Register identity from runtime configuration;
* absence of Register identity in Processing parameters.

---

# 29. Architecture Boundary Tests

Architecture boundary tests are implemented as part of Slice 8. They verify
that Phase 10 Processing does not introduce:

* direct persistence access;
* Register algorithm implementation;
* Valuation algorithm implementation;
* generic service containers;
* workflow abstractions;
* pipeline abstractions;
* command buses;
* schedulers;
* durable job infrastructure;
* generic transaction managers;
* authorization/security mechanisms.

---

# 30. Error Handling Rules

The following distinction is mandatory.

### Runtime boundary errors

Examples:

* Processing not found;
* Processing definition mismatch;
* invalid runtime configuration.

These are raised as Processing/runtime exceptions.

### Expected subsystem outcomes

Examples:

* Register rebuild `FAILURE`;
* Register rebuild `INDETERMINATE`;
* Valuation rebuild `FAILURE`;
* Valuation rebuild `INDETERMINATE`.

These are returned as part of the Processing result.

### Unexpected implementation exceptions

Unexpected exceptions propagate.

They are not silently converted into a business Processing outcome.

---

# 31. Progress Rules

Progress reporting is strictly observational.

The observer:

* receives progress notifications;
* does not control execution;
* does not modify business state;
* does not participate in outcome calculation;
* is not persisted.

If an observer raises an exception, the Processing business result remains
unchanged.

`ProcessingRuntime` is responsible for observer failure isolation. It supplies
Processing with a runtime-owned safe observer adapter. The adapter catches
exceptions raised by the external observer and prevents them from interrupting
Processing execution.

When no observer is supplied, the runtime provides a no-op observer so that the
Processing implementation always receives a valid observer through its context.

---

# 32. No Idempotency Contract

`ProcessingExecutionIdentity` is not an idempotency key.

Phase 10 does not define:

* durable Processing execution records;
* duplicate detection;
* retry semantics;
* exactly-once execution;
* at-least-once execution;
* resumable Processing.

Such behavior requires a separate architecture decision.

---

# 33. No Generic Workflow Abstraction

Phase 10 does not introduce:

```text
ProcessingStep
ProcessingPipeline
Workflow
WorkflowStep
Job
Scheduler
CommandBus
```

The Standard Processing directly orchestrates the two existing subsystem
contracts.

This is intentional.

A future workflow abstraction requires independent architectural justification.

---

# 34. No Generic Service Container

Processing dependencies are explicit constructor dependencies.

For example:

```python
InventoryDerivedStateRebuildProcessing(
    register_maintenance=...,
    valuation_rebuilder=...,
)
```

No:

```text
ServiceProvider
ServiceContainer
DependencyRegistry
```

is introduced.

---

# 35. No Authorization

Authorization and security policy are outside Phase 10 scope.

Processing does not:

* authenticate users;
* authorize execution;
* inspect permissions;
* enforce roles;
* contain security policy.

Those concerns are deferred to the appropriate future phase.

---

# 36. Generic Platform / Standard Separation

The generic Platform Processing layer knows only about:

* Processing definitions;
* commands;
* contexts;
* runtime;
* results;
* progress;
* runtime errors.

It does not know about:

* Inventory;
* Registers;
* Valuation;
* Goods Receipt;
* accounting-specific concepts.

Standard provides:

* Inventory Processing;
* Standard parameters;
* Standard results;
* Standard runtime configuration projection;
* Standard composition.

---

# 37. Architectural Invariants

The implementation must preserve the following invariants.

1. **Processing is an orchestration boundary, not a domain engine.**

2. **Processing dependencies are explicit.**

3. **No generic service bag or service container is introduced.**

4. **`RuntimeConfigurationContext` is authoritative for execution
   configuration.**

5. **Processing-specific parameters do not duplicate authoritative
   configuration state.**

6. **Standard-specific configuration is exposed through an immutable typed
   configuration projection.**

7. **The generic Platform Processing layer does not interpret
   Standard-specific configuration.**

8. **Register rebuild remains owned by Register Maintenance.**

9. **Valuation rebuild remains owned by the Valuation subsystem.**

10. **Register and Valuation rebuild operations remain independently
    executable.**

11. **Processing aggregates subsystem outcomes but preserves complete subsystem
    results.**

12. **`INDETERMINATE` is an execution outcome, not a Processing persistence
    state.**

13. **Progress is observational, synchronous, optional, and non-persistent.**

14. **Progress observer failures do not change business outcomes.**

15. **Execution identity provides correlation only.**

16. **Bootstrap-time Register rebuild remains distinct from explicit Processing
    execution.**

17. **Unexpected implementation exceptions are not silently converted into
    business outcomes.**

18. **No generic workflow, pipeline, scheduler, command bus, or durable job
    abstraction is introduced.**

19. **No authorization mechanism is introduced in Phase 10.**

20. **No direct persistence access is introduced into Processing.**

---

# 38. Implementation Order

Implementation should proceed in the following order.

### Slice 1 — Runtime configuration projection

Introduce the immutable Standard runtime configuration projection and integrate
it with the existing `RuntimeConfigurationContext` construction path.

### Slice 2 — Platform Processing contracts

Implement:

* identity;
* definition;
* command;
* context;
* result;
* outcome;
* progress;
* errors.

### Slice 3 — Processing Runtime

Implement:

* Processing resolution;
* identity validation;
* execution identity handling;
* context construction;
* Processing invocation;
* progress observation.

### Slice 4 — Standard Processing

Implement:

* `InventoryDerivedStateRebuildParameters`;
* `InventoryDerivedStateRebuildResult`;
* `InventoryDerivedStateRebuildProcessing`.

### Slice 5 — Standard composition

Integrate the Processing into Standard Bootstrap using already-composed
Register and Valuation services.

### Slice 6 — Tests

Add Platform unit tests, Standard unit tests, and the required integration
coverage.

### Slice 7 — Quality Gate

Run:

```text
pytest
ruff check .
black --check .
mypy src
```

All checks must pass before documentation reconciliation.

### Slice 8 — Architecture Boundary Tests

Add architecture-focused tests that verify the approved Phase 10 boundaries,
including:

* no direct persistence, storage, Register, Valuation, Posting, runtime, or
  Standard dependencies in generic Platform Processing;
* no registry, pipeline, workflow, scheduler, command bus, service container,
  or transaction manager abstraction in the public Platform Processing surface;
* no direct persistence, storage, or runtime dependencies in the Standard
  Inventory rebuild Processing;
* explicit semantic constructor dependencies for Register Maintenance and
  Valuation Rebuilder.

The implemented tests use source-level architecture inspection so that these
boundary checks do not depend on unrelated runtime imports.

---

# 39. Final API Decision

This document supersedes the previous Phase 10 Concrete API Design.

The approved API was implemented through Slice 8 without an architectural or
API contract change. The Slice 8 additions are tests only and enforce the
boundaries already defined by this document.

The approved API consists of:

```text
Platform
    ProcessingIdentity
    ProcessingExecutionIdentity
    ProcessingDefinition
    ProcessingCommand
    ProcessingContext
    Processing
    ProcessingOutcome
    ProcessingResult
    ProcessingProgress
    ProcessingProgressObserver
    ProcessingRuntime
    DefaultProcessingRuntime
    ProcessingError
    ProcessingNotFoundError
    ProcessingDefinitionMismatchError
    ProcessingExecutionError

Standard
    StandardRuntimeConfiguration
    InventoryDerivedStateRebuildParameters
    InventoryDerivedStateRebuildResult
    InventoryDerivedStateRebuildProcessing
```

The configuration amendment is limited to introducing the immutable typed
Standard runtime configuration projection required to expose the authoritative
Inventory Register identity through the existing runtime configuration
boundary.

No other previously approved Phase 10 API decision is changed.

The Progress Propagation Amendment in Section 40 is part of the approved API
and is limited to making the progress propagation and observer failure-isolation
mechanism explicit.

**Status: APPROVED FOR IMPLEMENTATION**
