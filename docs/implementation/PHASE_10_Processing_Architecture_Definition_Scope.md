# AcCoreD — Phase 10

# Processing Architecture Definition / Scope

**Status:** Reconciled with implementation
**Phase:** 10
**Architectural Area:** Processing
**Document Type:** Architecture Definition / Scope
**Baseline:** Phase 10 implementation through Slice 8
**Baseline Commit:** `588fdb9` — `feat(processing): implement Phase 10 processing runtime foundation`

---

## 1. Purpose

Phase 10 introduces a generic **Processing** mechanism into AcCoreD.

The purpose of Processing is to provide an explicit Platform-level boundary for executing **active business operations** that orchestrate already-existing Platform capabilities.

AcCoreD currently contains substantial domain and infrastructure capabilities:

* Register maintenance and derived totals;
* Valuation rebuild and derived valuation state;
* posting;
* reporting;
* persistence and recovery;
* runtime configuration resolution.

These capabilities are currently exposed through their own explicit contracts.

Phase 10 adds a higher-level operational mechanism capable of invoking such capabilities as one explicit business operation.

Processing is therefore an **orchestration and execution boundary**, not a replacement for existing domain services.

---

# 2. Phase 10 Objective

Phase 10 has two objectives.

### 2.1 Generic Platform Processing

Introduce a generic Platform mechanism that allows a Processing to be:

1. defined;
2. identified;
3. invoked through an explicit command;
4. executed through an explicit runtime;
5. provided with an explicit runtime context;
6. provided with explicitly defined dependencies;
7. observed through execution results and, where appropriate, progress;
8. reported as `SUCCESS`, `FAILURE`, or `INDETERMINATE`.

### 2.2 Standard Configuration Processing

Provide at least one meaningful Processing in Standard Configuration that exercises multiple existing Platform capabilities.

The Phase 10 MVP Processing is:

> **Inventory Derived State Rebuild**

Its purpose is to provide an explicit operational boundary for rebuilding independently owned derived state related to inventory.

The Processing orchestrates:

* Register Totals rebuild;
* Valuation Derived State rebuild.

These are treated as **independent owned operations**, not as a hard-coded sequential dependency.

---

# 3. Architectural Position

Processing belongs to the generic Platform layer.

```text
Application / external caller
            │
            ▼
     Processing Command
            │
            ▼
     Processing Runtime
            │
            ▼
   Processing Definition
            │
            ▼
   Processing Implementation
            │
            ├──────────────► Register Maintenance
            │
            └──────────────► Valuation Rebuilder
```

The Processing layer coordinates existing semantic contracts.

It does not own the algorithms implemented by:

* Register;
* Totals;
* Valuation;
* Posting;
* Persistence;
* Reporting.

---

# 4. Architectural Principles

Phase 10 follows the existing AcCoreD architectural principles.

## 4.1 Explicit contracts

Processing dependencies must be represented by explicit contracts.

Processing must **not** receive an unrestricted generic service container.

The architecture explicitly rejects abstractions such as:

```text
ProcessingServices
ServiceContainer
ApplicationServices
ServiceBag
RuntimeServices
```

or equivalent generic dictionaries of services.

A Processing receives only the capabilities it actually requires.

For the MVP Processing these capabilities are expected to include the existing contracts for:

* Register derived-state maintenance;
* Valuation derived-state rebuilding.

The exact API form is defined in the Concrete API Design phase.

---

## 4.2 Existing runtime context remains authoritative

AcCoreD already defines:

```text
RuntimeConfigurationContext
```

as the immutable runtime configuration snapshot.

Processing must not introduce a second competing configuration context.

Instead:

```text
ProcessingContext
        │
        └── RuntimeConfigurationContext
```

`ProcessingContext` may contain execution-specific information, but configuration identity and version remain owned by the existing `RuntimeConfigurationContext`.

Processing must not duplicate:

* active configuration;
* configuration identity;
* configuration version;
* configuration resolution semantics.

---

## 4.3 Processing is orchestration, not domain logic

A Processing may coordinate domain operations.

It must not reimplement them.

For example, Inventory Derived State Rebuild must invoke:

```text
TotalsMaintenanceCoordinator.rebuild(...)
```

and:

```text
ValuationRebuilder.rebuild(...)
```

rather than implementing:

* totals reconstruction;
* valuation reconstruction;
* valuation algorithms;
* persistence logic;
* recovery logic.

The existing subsystem remains the owner of its own semantics.

---

## 4.4 Processing does not own persistence

Phase 10 does not introduce persistent Processing execution history.

Processing may invoke persistent domain operations whose persistence is already owned by those subsystems.

For example:

```text
Processing
   │
   ├── Register Maintenance
   │      └── Register persistence
   │
   └── Valuation Rebuild
          └── Valuation persistence
```

Processing itself does not persist:

* commands;
* execution records;
* progress;
* Processing history;
* Processing state machines.

---

## 4.5 Processing does not own recovery semantics

Recovery remains the responsibility of the subsystem performing the operation.

For example:

* Register maintenance owns Register consistency and recovery semantics;
* Valuation rebuild owns Valuation consistency and recovery semantics.

Processing may surface an `INDETERMINATE` result returned by a child operation.

It must not reinterpret that state into a new persistence protocol.

---

# 5. Processing Definition

A **Processing Definition** describes a Processing that can be executed.

It represents the stable identity and declarative metadata of a Processing.

Conceptually:

```text
Processing Definition
├── processing identity
├── processing metadata
└── execution contract
```

The definition must be immutable.

A Processing identity must be stable and suitable for identifying the operation independently from an individual execution.

The architecture distinguishes:

```text
Processing Identity
```

from:

```text
Processing Execution Identity
```

A Processing may therefore be executed multiple times while retaining the same Processing identity.

---

# 6. Processing Command

A **Processing Command** represents an explicit request to execute a Processing.

The command is immutable.

Conceptually:

```text
Processing Command
├── processing identity
├── execution identity
└── parameters
```

The exact command structure is deferred to Concrete API Design.

The command must not itself contain arbitrary runtime services.

Dependencies are supplied by the Processing composition/runtime boundary.

---

# 7. Processing Context

A **Processing Context** represents the execution context of one Processing invocation.

It is execution-specific and must remain explicit.

Conceptually:

```text
Processing Context
├── execution identity
├── parameters
├── RuntimeConfigurationContext
└── explicitly defined execution information
```

The context may provide information required to execute the Processing, but it must not become a generic service locator.

In particular, the following design is rejected:

```text
context.services["anything"]
```

or an equivalent unrestricted service lookup mechanism.

Processing dependencies are explicit.

---

# 8. Processing Runtime

The **Processing Runtime** is responsible for executing Processing commands.

Its responsibilities are limited to execution orchestration.

Conceptually:

```text
Processing Runtime
    │
    ├── validate command
    │
    ├── resolve Processing Definition
    │
    ├── create execution context
    │
    ├── invoke Processing
    │
    └── return Processing Result
```

The Processing Runtime does not implement the business semantics of individual Processings.

It is not:

* a workflow engine;
* a scheduler;
* a command bus;
* a transaction manager;
* a dependency injection container.

---

# 9. Processing Execution Result

Processing execution must expose an explicit outcome.

The architectural outcome states are:

```text
SUCCESS
FAILURE
INDETERMINATE
```

## 9.1 SUCCESS

The Processing completed successfully according to its defined semantics.

## 9.2 FAILURE

The Processing completed with a known failure.

The system has sufficient information to state that the requested operation did not complete successfully.

## 9.3 INDETERMINATE

The Processing cannot establish successful completion with sufficient certainty.

This state may be propagated from an underlying subsystem operation.

For example:

```text
Register rebuild       SUCCESS
Valuation rebuild      INDETERMINATE
-------------------------------------
Processing              INDETERMINATE
```

`INDETERMINATE` in Phase 10 is therefore an **execution outcome**, not a new Processing persistence state.

---

# 10. Preservation of Subsystem Results

Processing must not discard the semantic result returned by an underlying subsystem.

For the Inventory Derived State Rebuild Processing, the execution result should preserve sufficient information to identify the outcomes of:

```text
Register Totals Rebuild
Valuation Derived State Rebuild
```

The Processing result therefore acts as an aggregation boundary while retaining step-level diagnostics.

The exact result model is deferred to Concrete API Design.

---

# 11. Inventory Derived State Rebuild

## 11.1 Purpose

The first Standard Configuration Processing is:

> **Inventory Derived State Rebuild**

It provides an explicit operational mechanism for rebuilding independently owned derived state used by inventory functionality.

The Processing coordinates:

```text
Inventory Derived State Rebuild
    │
    ├── Register Totals Rebuild
    │
    └── Valuation Derived State Rebuild
```

---

## 11.2 Register Totals Rebuild

Register rebuild is owned by the existing:

```text
TotalsMaintenanceCoordinator
```

The Processing invokes the existing Register maintenance contract.

The Processing does not:

* enumerate Register facts itself;
* reconstruct totals;
* manipulate Register persistence;
* modify Register consistency state directly.

---

## 11.3 Valuation Derived State Rebuild

Valuation rebuild is owned by the existing:

```text
ValuationRebuilder
```

The Processing invokes the existing Valuation rebuild contract.

The Processing does not:

* enumerate valuation facts itself;
* reconstruct valuation results;
* manipulate valuation persistence directly;
* implement valuation algorithms;
* modify valuation recovery state directly.

---

# 12. Independence of Rebuild Operations

Register Totals Rebuild and Valuation Derived State Rebuild are architecturally independent operations.

The architecture does **not** define:

```text
Register Rebuild
       ↓
Valuation Rebuild
```

as a required dependency.

Instead:

```text
Inventory Derived State Rebuild
       │
       ├── Register Totals Rebuild
       │
       └── Valuation Derived State Rebuild
```

Each subsystem remains responsible for determining whether its own rebuild operation may proceed.

The Processing orchestrates both operations.

---

# 13. Failure Aggregation

Because the two rebuild operations are independent, the Processing must not stop merely because one operation returns a non-success result, provided the other operation can still be safely executed according to its own admission rules.

Conceptually:

```text
Register Result       Valuation Result       Processing Result
----------------------------------------------------------------
SUCCESS               SUCCESS                SUCCESS
SUCCESS               FAILURE                FAILURE
SUCCESS               INDETERMINATE          INDETERMINATE
FAILURE               SUCCESS                FAILURE
INDETERMINATE         SUCCESS                INDETERMINATE
FAILURE               FAILURE                FAILURE
FAILURE               INDETERMINATE          INDETERMINATE
INDETERMINATE         FAILURE                INDETERMINATE
INDETERMINATE         INDETERMINATE          INDETERMINATE
```

The exact aggregation implementation belongs to Concrete API Design.

The architectural rule is:

> A failed or indeterminate independent step does not automatically prevent execution of another independent step.

However, each underlying subsystem retains authority over whether its operation is admissible.

---

# 14. Progress Observation

Phase 10 may expose Processing progress as an **observational** mechanism.

Progress is useful because the first Processing contains multiple independently executed operations.

Progress must be:

* synchronous;
* optional;
* non-persistent;
* observational;
* incapable of changing business semantics.

Progress observation must not become:

* a job system;
* a scheduler;
* a durable progress store;
* a workflow state machine.

The exact progress contract is deferred to Concrete API Design.

If no observer is supplied, Processing execution must remain fully functional.

---

# 15. Error Observability

Processing errors must be observable through the Processing result and/or defined execution error contract.

The architecture distinguishes:

### Known business/subsystem failure

Example:

```text
ValuationRebuildResult.FAILURE
```

### Indeterminate subsystem state

Example:

```text
ValuationRebuildResult.INDETERMINATE
```

### Unexpected Processing execution error

An unexpected exception must not be silently converted into successful completion.

The exact exception/result boundary is deferred to Concrete API Design.

---

# 16. Composition Boundary

Processing dependencies are composed by the owning configuration.

For Standard Configuration:

```text
StandardConfigurationBootstrap
          │
          ├── Register components
          ├── Valuation components
          └── Processing components
```

The Standard Processing must receive already-composed services.

It must not instantiate its own:

```text
DefaultTotalsMaintenanceCoordinator
DefaultValuationRebuilder
```

or equivalent infrastructure/domain implementations.

This preserves the existing composition model.

---

# 17. Bootstrap and Processing Are Distinct Concerns

Current Standard Configuration composition performs Register maintenance during bootstrap.

That existing behavior is not replaced by Phase 10 Processing.

The architecture distinguishes:

### Bootstrap initialization

Responsible for bringing the composed runtime into a valid initial state.

### Explicit Processing execution

Responsible for exposing a deliberate operational recalculation boundary.

Therefore:

```text
Bootstrap
    └── existing startup initialization/rebuild semantics


Explicit Processing
    └── Inventory Derived State Rebuild
          ├── Register Totals Rebuild
          └── Valuation Derived State Rebuild
```

Phase 10 must not conflate these responsibilities.

Concrete API Design must determine the precise composition and invocation wiring without turning Processing into a substitute for bootstrap initialization.

---

# 18. Generic Processing vs Standard Processing

## 18.1 Platform

Generic Processing infrastructure belongs under:

```text
src/accore/platform/processing/
```

Expected architectural responsibilities include:

* Processing Definition;
* Processing Command;
* Processing Context;
* Processing Runtime;
* Processing Result;
* optional progress observation;
* generic execution contracts.

The exact module structure is deferred to Concrete API Design.

---

## 18.2 Standard Configuration

Standard-specific Processing belongs under:

```text
src/standard/processings/
```

The Standard layer provides:

* Standard Processing implementation;
* Standard-specific parameters;
* composition;
* adapters where required.

The Standard layer must not move generic Processing abstractions into the Standard package.

---

# 19. Dependency Direction

The intended dependency direction is:

```text
Standard Processing
        │
        ▼
Platform Processing contracts
        │
        ├──────────────► Register contracts
        │
        └──────────────► Valuation contracts
```

The Processing mechanism itself must not depend on Standard Configuration.

Therefore:

```text
accore.platform.processing
```

must remain independent from:

```text
standard.processings
```

and other Standard-specific packages.

---

# 20. Explicitly Rejected Architectural Approaches

The following approaches are outside Phase 10.

## 20.1 Generic service bag

Rejected:

```text
ProcessingServices
```

or equivalent universal service locator.

Reason:

* hides dependencies;
* weakens contracts;
* conflicts with the existing explicit-contract architecture.

---

## 20.2 Generic workflow engine

Rejected:

```text
WorkflowEngine
ProcessingPipeline
ProcessingStepEngine
```

Phase 10 requires one meaningful multi-operation Processing, not a generalized workflow framework.

---

## 20.3 Command bus

A Processing Command does not imply a generic command bus.

Phase 10 does not introduce:

* command routing infrastructure;
* message bus;
* distributed command dispatch.

---

## 20.4 Scheduler

Phase 10 does not introduce scheduled Processing execution.

No:

* cron abstraction;
* scheduler;
* recurring execution;
* job queue.

---

## 20.5 Durable Processing jobs

Phase 10 does not introduce durable jobs or execution history.

No Processing execution persistence is required.

---

## 20.6 Generic transaction manager

Processing does not own transactions.

Transaction and persistence semantics remain with the underlying subsystems.

---

## 20.7 Generic rollback

Processing does not define a universal rollback mechanism.

If an underlying subsystem supports recovery or reversal, that subsystem owns its semantics.

Processing only orchestrates the existing contracts.

---

## 20.8 Security / authorization mechanism

Processing does not introduce authorization in Phase 10.

Security and authorization requirements are deferred to Phase 11.

The Processing architecture must not prevent a future authorization boundary from being added.

---

## 20.9 UI

No Processing UI is introduced.

---

# 21. Phase 10 Scope

## In Scope

### Platform

* Processing Definition;
* Processing Identity;
* Processing Command;
* Processing Execution Identity;
* Processing Context;
* Processing Runtime;
* Processing Result;
* explicit Processing dependency model;
* Processing outcome semantics;
* error observability;
* optional observational progress.

### Standard Configuration

* Inventory Derived State Rebuild Processing;
* Register Totals rebuild integration;
* Valuation Derived State rebuild integration;
* Standard composition/wiring.

### Tests

Tests must verify at minimum:

* Processing definition;
* command execution;
* runtime context propagation;
* explicit dependency injection/composition;
* successful execution;
* known failure;
* indeterminate outcome;
* independent execution of Register and Valuation rebuilds;
* aggregated result semantics;
* progress observation where implemented;
* Standard end-to-end execution.

---

# 22. Explicitly Out of Scope

The following are not part of Phase 10:

* asynchronous execution;
* background workers;
* job queues;
* scheduling;
* recurring processing;
* durable Processing execution history;
* workflow engine;
* generic pipeline framework;
* command bus;
* distributed execution;
* generic transaction manager;
* generic rollback framework;
* authorization;
* UI;
* API transport layer;
* persistence of progress;
* Processings implementing domain algorithms themselves.

These may be considered in later phases if justified by concrete requirements.

---

# 23. Acceptance Criteria

Phase 10 architecture and implementation are considered complete when all of the following are satisfied.

### AC-1 — Processing Definition

A Processing can be defined through an explicit immutable definition.

### AC-2 — Processing Execution

A Processing can be executed through an explicit command and runtime.

### AC-3 — Runtime Context

A Processing receives an explicit execution context containing the authoritative:

```text
RuntimeConfigurationContext
```

without duplicating configuration state.

### AC-4 — Explicit Dependencies

A Processing can interact with required Platform capabilities through explicit contracts.

No generic service bag is required.

### AC-5 — Error Observability

Known failure and indeterminate outcomes are observable through the Processing execution result.

### AC-6 — Progress Observation

Where implemented, Processing progress is observable without becoming durable execution state.

### AC-7 — Standard Processing

Standard Configuration provides:

> Inventory Derived State Rebuild

which exercises both:

* Register Totals Rebuild;
* Valuation Derived State Rebuild.

### AC-8 — Independent Operations

Register and Valuation rebuilds remain independently owned operations.

A non-success result from one does not automatically prevent execution of the other when the latter is independently admissible.

### AC-9 — Result Aggregation

The Processing returns an aggregate outcome while preserving sufficient step-level results for diagnostics.

### AC-10 — Architectural Boundaries

Processing does not:

* implement Register algorithms;
* implement Valuation algorithms;
* own subsystem persistence;
* own subsystem recovery;
* introduce a generic service container;
* introduce a workflow engine;
* introduce scheduling;
* introduce authorization.

---

# 24. Concrete API Design Boundary

After approval of this Architecture Definition / Scope, the next phase is:

> **Phase 10 — Concrete API Design**

The Concrete API Design must define, at minimum:

1. exact Processing Definition API;
2. Processing identity representation;
3. Processing Command API;
4. Processing Execution Identity;
5. Processing Context structure;
6. Processing Runtime protocol;
7. Processing implementation protocol;
8. Processing Result and outcome types;
9. failure/exception semantics;
10. progress observer contract, if retained;
11. dependency injection/composition model;
12. Standard Inventory Derived State Rebuild API;
13. aggregation of Register and Valuation results;
14. Standard Bootstrap integration;
15. public exports;
16. test boundaries.

The Concrete API Design must not introduce abstractions rejected by this document.

---

# 25. Architectural Invariants

The following invariants are binding for Phase 10 implementation.

### Invariant 1

Processing is an orchestration boundary, not a domain engine.

### Invariant 2

Processing dependencies are explicit.

### Invariant 3

No generic service bag is introduced.

### Invariant 4

`RuntimeConfigurationContext` remains the authoritative runtime configuration context.

### Invariant 5

`ProcessingContext` does not duplicate configuration state.

### Invariant 6

Processing does not own Register semantics.

### Invariant 7

Processing does not own Valuation semantics.

### Invariant 8

Register and Valuation rebuild operations remain independently owned.

### Invariant 9

Processing may aggregate subsystem outcomes but must preserve their semantic results.

### Invariant 10

`INDETERMINATE` is an execution outcome propagated from underlying operations, not a new Processing persistence protocol.

### Invariant 11

Progress, if implemented, is observational and non-persistent.

### Invariant 12

Processing composition is performed by the owning configuration.

### Invariant 13

Bootstrap initialization and explicit Processing execution remain distinct concerns.

### Invariant 14

No authorization mechanism is introduced in Phase 10.

### Invariant 15

No generic workflow, pipeline, scheduler, command bus, or durable job infrastructure is introduced without a separately approved architectural requirement.

### Implementation Reconciliation

The approved architecture has been implemented through Phase 10 Slice 8.
The implementation now includes:

* generic Platform Processing contracts and runtime;
* observational progress propagation with runtime-owned no-op/safe observers;
* Standard Inventory Derived State Rebuild Processing;
* Standard runtime configuration projection;
* explicit Standard composition;
* Platform, Standard, and integration test coverage;
* architecture boundary tests verifying the approved dependency and abstraction boundaries.

No architectural scope expansion was introduced during implementation. The remaining Phase 10 work is the final quality gate and review.

---

# 26. Final Architectural Decision

Phase 10 introduces **Processing** as a generic Platform orchestration boundary.

The first Standard Configuration Processing is:

> **Inventory Derived State Rebuild**

It coordinates two independently owned existing capabilities:

```text
Register Totals Rebuild
Valuation Derived State Rebuild
```

The Processing layer provides:

* explicit definition;
* explicit command;
* explicit execution context;
* explicit dependencies;
* explicit runtime;
* explicit outcome;
* observable diagnostics/progress.

It does not become a service locator, workflow engine, persistence layer, recovery framework, or domain engine.

The architecture therefore preserves the existing AcCoreD separation of responsibilities while providing a new explicit mechanism for executing active business operations.

**Architecture Definition / Scope: RECONCILED WITH IMPLEMENTATION**
