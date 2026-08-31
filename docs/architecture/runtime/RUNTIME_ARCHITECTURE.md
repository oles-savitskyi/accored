# Runtime Architecture

**Version:** 1.1
**Status:** Accepted / Implemented in progress

---

# 1. Purpose

The Runtime subsystem provides the execution environment in which an AcCore application operates.

The Runtime is responsible for hosting platform services, managing their lifecycle, and providing the infrastructure required for application execution.

The Runtime does not define the application structure.

Application structure is defined by the Metadata subsystem.

The Runtime consumes the published semantic metadata model and provides the environment in which the application executes.

---

# 2. Design Goals

The Runtime subsystem is designed to provide:

- a stable execution environment;
- deterministic initialization;
- service-oriented architecture;
- clear lifecycle management;
- explicit execution contexts;
- subsystem isolation;
- extensibility;
- support for multiple deployment models.

---

# 3. Architectural Principles

## Runtime is an execution environment

The Runtime provides infrastructure rather than business functionality.

Business logic is implemented by platform services and application components.

---

## Runtime is service-oriented

The Runtime is composed of cooperating services.

Each service has a clearly defined responsibility.

Services communicate through well-defined interfaces.

---

## Runtime consumes metadata

The Runtime never builds or modifies metadata.

It consumes the Published Semantic Metadata Graph produced by the Metadata Compilation subsystem.

---

## Runtime is context-aware

Configuration-dependent Runtime operations use an explicit `RuntimeConfigurationContext`. Object Runtime derives an explicit `ObjectContext` from that snapshot.

The execution context defines the environment in which platform services operate.

---

## Runtime is lifecycle-driven

All Runtime components participate in a managed lifecycle.

Initialization, operation and shutdown follow deterministic rules.

---

## Runtime is extensible

New services may be added without changing the Runtime architecture.

Extensions integrate through service registration rather than Runtime modification.

---

# 4. Runtime Model

The Runtime architecture consists of several conceptual layers.

```
ActiveConfiguration
        │
        │ publish
        ▼
RuntimeConfigurationBinding
        │
        │ acquire
        ▼
RuntimeConfigurationContext
        │
        ▼
MetadataResolver
        │
        ▼
RuntimeResolver
        │
        ▼
Runtime Object Type
        │
        ▼
Object Runtime
```

`RuntimeConfigurationBinding` owns publication of the active runtime
configuration. `RuntimeConfigurationContext` captures an immutable snapshot
of that published configuration.

Runtime components consume configuration through the explicit context and do
not discover the current configuration through the binding themselves.

Each layer has a distinct architectural responsibility.

---

# 5. Runtime Lifecycle

The Runtime follows a well-defined lifecycle.

```
Construction
       │
       ▼
Initialization
       │
       ▼
Service Registration
       │
       ▼
Activation
       │
       ▼
Normal Operation
       │
       ▼
Shutdown
       │
       ▼
Termination
```

Each stage completes before the next stage begins.

---

# 6. Runtime Services

The Runtime hosts a collection of cooperating platform services.

Typical services include:

- Metadata Service;
- Object Service;
- Storage Service;
- Query Service;
- Expression Service;
- Security Service;
- Transaction Service;
- Event Service;
- Session Service;
- UI Service.

Each service is responsible for a single architectural concern.

The Runtime coordinates services but does not implement their functionality.

---

# 7. Runtime Context

Every Runtime operation executes within a Runtime Context.

A Runtime Context represents the complete execution environment for an operation.

Typical context information may include:

- metadata snapshot;
- security context;
- session;
- transaction;
- localization;
- organization;
- execution parameters;
- runtime options.

The Runtime Context is explicitly propagated through Runtime services.

---

# 8. Service Communication

Runtime services communicate through explicit interfaces.

Services should avoid direct dependencies whenever possible.

The Runtime provides the infrastructure required for service discovery and coordination.

Communication should remain:

- explicit;
- deterministic;
- loosely coupled.

---

# 9. Runtime States

The Runtime may exist in several operational states.

Typical states include:

- Initializing;
- Starting;
- Running;
- Stopping;
- Stopped;
- Failed.

State transitions are controlled by the Runtime lifecycle.

---

# 10. Threading Model

The Runtime architecture is independent of any particular threading model.

Possible implementations include:

- single-threaded;
- multi-threaded;
- asynchronous;
- distributed.

Runtime services define their own concurrency guarantees.

The Runtime coordinates lifecycle rather than execution scheduling.

---

# 11. Extensibility

The Runtime architecture supports future extensions through service composition.

New Runtime capabilities are introduced by:

- registering new services;
- extending service interfaces;
- introducing new Runtime contexts.

Existing Runtime architecture remains unchanged.

---

# 12. Relationship to Other Subsystems

The Runtime interacts with all major platform subsystems.

The Metadata subsystem provides the Published Semantic Metadata Graph.

The Runtime hosts services responsible for:

- Storage;
- Security;
- Query Processing;
- Expression Evaluation;
- Transactions;
- User Interface;
- Reporting;
- Integration.

The Runtime itself remains independent from the implementation details of these services.

---

# Appendix A. Conceptual Architecture

```
                Metadata

Published Semantic Metadata Graph
                │
                ▼
         Runtime Environment
                │
      ┌─────────┴─────────┐
      ▼                   ▼
 Runtime Context   Service Registry
                          │
                          ▼
                  Runtime Services
      ┌──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼
   Object     Storage    Security    Query
   Service    Service    Service     Service
      │
      ▼
 Domain Objects
```

The Runtime provides the execution environment.

Services provide platform functionality.

Runtime Context defines the execution conditions.

Domain Objects implement the business application.

Together these components form the execution architecture of the AcCore platform.

---

## Phase 4 Runtime/Object Boundary

The Runtime package remains responsible for Runtime Object Type resolution. The Object package owns individual Object Instance semantics. `RuntimeResolver` does not create Object Instances.
