# Phase 12 --- Integration

## Architecture Definition / Scope

**Status:** APPROVED FOR CONCRETE API DESIGN\
**Phase:** 12\
**Predecessors:** Phase 9 --- Reporting; Phase 10 --- Processing; Phase
11 --- Security\
**Primary architectural principle:** Contract-First Integration\
**Secondary principle:** Event-Aware Architecture

------------------------------------------------------------------------

## 1. Purpose

Phase 12 establishes the minimum integration boundary required to make
the Standard Edition externally usable without exposing internal
platform implementation details or bypassing Runtime, Security, business
rules, or persistence boundaries.

The phase converts the existing Integration Architecture into a minimal
executable platform capability.

Phase 12 is not intended to implement the complete long-term integration
ecosystem. It establishes the stable architectural foundation on which
additional protocols, connectors, events, import/export formats, and
external applications can be added later.

------------------------------------------------------------------------

## 2. Objective

Phase 12 establishes the minimum contract-driven external integration
boundary through which authorized external consumers can:

1.  invoke supported Standard Edition operations;
2.  receive stable, documented responses and errors;
3.  access supported analytical data through the Reporting boundary;
4.  observe supported completed business facts through Event
    Infrastructure;
5.  perform basic contract-based import/export where required by the
    MVP.

All external interaction must remain mediated by the platform Runtime
and Security boundaries.

------------------------------------------------------------------------

## 3. Architectural Context

The phase follows:

``` text
Phase 9  — Reporting
    ↓
Phase 10 — Processing
    ↓
Phase 11 — Security
    ↓
Phase 12 — Integration
```

This order is intentional.

Reporting provides stable dataset-oriented analytical output.

Processing provides executable business operations.

Security provides authentication and authorization primitives.

Integration exposes selected capabilities of these existing subsystems
to external consumers.

Integration therefore does not become a second business/runtime layer.

------------------------------------------------------------------------

## 4. Existing Architectural Foundation

The project already defines an Integration Architecture consisting of:

-   Integration Architecture;
-   Integration Model;
-   API Architecture;
-   Event Architecture;
-   Import/Export Architecture;
-   External Connectors;
-   Integration ADRs.

The following architectural decisions are treated as existing
constraints:

-   external systems access platform services rather than storage;
-   integration is contract-driven;
-   commands are the state-changing integration mechanism;
-   queries are read-only;
-   events represent completed facts;
-   events are published after successful transaction completion;
-   publishers are independent from subscribers;
-   APIs publish contracts rather than define business operations;
-   contracts are versioned independently of transport protocols;
-   connectors are adapters;
-   connectors do not own business logic;
-   connector failures must not invalidate core processing;
-   import/export is contract-based rather than file-format-driven.

Phase 12 implements the minimum executable subset of these decisions.

------------------------------------------------------------------------

## 5. Architectural Position

Integration is the external boundary of AcCoreD.

``` text
External Consumer
        ↓
Integration Boundary
        ↓
Security / Authorization
        ↓
Integration Service
        ↓
Runtime Service
        ↓
Business Platform
```

For analytical access:

``` text
External Consumer
        ↓
Integration Boundary
        ↓
Security / Authorization
        ↓
Reporting Runtime
        ↓
Dataset
```

For events:

``` text
Completed Business Operation
        ↓
Committed Business Fact
        ↓
Event Contract
        ↓
Event Infrastructure
        ↓
Subscribers
```

Integration must never provide a direct path to persistence or internal
business structures.

------------------------------------------------------------------------

## 6. Scope

### 6.1 Integration Contracts

Phase 12 introduces the executable contract model required for external
interaction.

Contracts define, as applicable:

-   contract identity;
-   contract version;
-   request/input schema;
-   response/output schema;
-   error semantics;
-   validation requirements;
-   operation semantics;
-   compatibility expectations.

Contracts are independent of:

-   storage schema;
-   persistence implementation;
-   Runtime implementation;
-   transport protocol;
-   physical file format.

Contracts are the source of truth for published integration
capabilities.

------------------------------------------------------------------------

### 6.2 Integration Commands

Commands represent external requests that may modify platform state.

Command execution must follow:

``` text
Command Contract
      ↓
Integration Service
      ↓
Security / Authorization
      ↓
Runtime Service
      ↓
Business Operation
```

Integration code must not implement or duplicate business rules.

Only supported Runtime operations may be exposed.

------------------------------------------------------------------------

### 6.3 Integration Queries

Queries represent external read-only requests.

Queries must not modify platform state.

For analytical scenarios, Reporting datasets are the preferred
integration mechanism.

``` text
Query Contract
      ↓
Integration Service
      ↓
Reporting / Runtime
      ↓
Dataset / Result
```

External consumers must not query accounting storage structures
directly.

------------------------------------------------------------------------

### 6.4 API Publication Boundary

Phase 12 defines a protocol-independent API publication boundary.

The core integration model must not depend on HTTP, REST, gRPC,
WebSocket, message brokers, or another transport.

Transport-specific publication is an adapter responsibility.

The architecture therefore separates:

``` text
Integration Contract
        ↓
Integration Runtime
        ↓
Protocol Adapter
```

from:

``` text
HTTP / REST / gRPC / Message Transport / Other
```

Phase 12 does not require a complete multi-protocol API ecosystem.

At least one supported external publication path must demonstrate that a
defined contract can reach the appropriate Runtime boundary.

------------------------------------------------------------------------

### 6.5 Event Infrastructure

Phase 12 establishes a minimal event infrastructure capable of
publishing and consuming supported event contracts.

Events:

-   represent completed facts;
-   are immutable;
-   are versioned;
-   are published after successful originating transaction completion;
-   do not drive core accounting execution;
-   do not cause the originating transaction to depend on subscriber
    success.

The event infrastructure must support publisher/subscriber decoupling.

Existing business event sources, including posting-related events, must
be integrated into the common event boundary rather than duplicated by a
second event mechanism.

The MVP may use an in-process event mechanism. A distributed broker is
not required for Phase 12.

------------------------------------------------------------------------

### 6.6 Import / Export

Phase 12 provides the minimum contract-based import/export capability
required by the MVP.

Import:

``` text
External Representation
        ↓
Import Adapter / Runtime
        ↓
Import Contract
        ↓
Integration Service
        ↓
Runtime Service
```

Export:

``` text
Runtime / Reporting
        ↓
Export Contract
        ↓
Export Runtime / Adapter
        ↓
External Representation
```

Business semantics belong to contracts and Runtime services, not to CSV,
JSON, XML, Excel, or another physical format.

Phase 12 does not implement a universal ETL or synchronization engine.

------------------------------------------------------------------------

### 6.7 Security Integration

All externally initiated operations are subject to the Security
architecture established in Phase 11.

The integration boundary must propagate or establish the required
security context and invoke authorization before execution of protected
operations.

Integration must not:

-   implement a second authorization model;
-   bypass authorization;
-   access security repositories directly;
-   reinterpret permission semantics.

The intended flow is:

``` text
External Request
        ↓
Integration Contract Resolution
        ↓
Security Context
        ↓
Authorization
        ↓
Runtime Operation
```

Unauthenticated or unauthorized requests must terminate at the
appropriate security boundary.

------------------------------------------------------------------------

### 6.8 Standard Edition Composition

Phase 12 exposes only a deliberately small representative subset of
Standard Edition functionality.

The MVP should demonstrate at least:

-   one supported state-changing command;
-   one supported read-only query;
-   one Reporting/dataset-oriented query where applicable;
-   one published business event;
-   one consumable event;
-   one basic import scenario where required;
-   one basic export scenario where required.

The goal is vertical architectural validation, not a large number of
endpoints.

------------------------------------------------------------------------

## 7. Responsibilities

Integration Architecture owns:

-   external contract definition;
-   contract versioning;
-   integration request/response orchestration;
-   integration service boundaries;
-   API publication boundary;
-   event publication/consumption infrastructure;
-   import/export orchestration;
-   connector adaptation;
-   external error translation;
-   external compatibility boundaries.

Runtime and business subsystems own:

-   business rules;
-   state transitions;
-   posting;
-   processing;
-   valuation;
-   register operations;
-   report execution;
-   business object behavior;
-   persistence.

Security owns:

-   authentication;
-   security context;
-   authorization;
-   roles;
-   permissions;
-   access decisions.

Integration must consume these capabilities rather than duplicate them.

------------------------------------------------------------------------

## 8. Dependency Rules

Phase 12 follows these dependency rules:

``` text
Integration
    ↓
Security
    ↓
Runtime
    ↓
Business / Persistence
```

Integration may depend on published Runtime and Security contracts.

Integration must not depend directly on persistence implementation.

Integration must not make business subsystems depend on external
transport implementations.

Business logic must not depend on a specific API protocol.

Event subscribers must not become dependencies of the originating
business operation.

------------------------------------------------------------------------

## 9. External Boundary Rules

The following are mandatory:

1.  External consumers never access storage directly.
2.  External consumers never invoke internal business objects through
    undocumented interfaces.
3.  Commands are the only external interaction category allowed to
    modify state.
4.  Queries are side-effect free.
5.  Events are facts, not commands.
6.  APIs publish contracts rather than define business behavior.
7.  Contract versions are independent from transport versions.
8.  Connectors adapt; they do not implement business logic.
9.  Import/export uses contracts rather than file-format-specific
    business semantics.
10. Security authorization cannot be bypassed by choosing another
    integration path.

------------------------------------------------------------------------

## 10. Failure and Transaction Semantics

Integration failures must not corrupt or partially redefine core
business state.

For synchronous commands:

``` text
Request
  ↓
Validation / Authorization
  ↓
Runtime Transaction
  ↓
Success / Failure
  ↓
Response
```

The integration layer must not commit business state independently from
Runtime.

For events:

``` text
Business Transaction
        ↓
Successful Completion
        ↓
Event Publication
        ↓
Subscriber Processing
```

Subscriber failure must not roll back a completed originating business
transaction.

For connectors:

Connector failure must remain isolated from core processing unless a
specific business contract explicitly defines the external dependency as
part of the operation. Such a dependency is outside the default Phase 12
model.

------------------------------------------------------------------------

## 11. Versioning and Compatibility

Integration contracts are independently versioned.

Transport versions must not define contract versions.

A contract version governs:

-   request shape;
-   response shape;
-   error semantics;
-   event payload semantics;
-   compatibility expectations.

The initial Phase 12 implementation must establish a clear policy for:

-   compatible evolution;
-   breaking changes;
-   version coexistence;
-   deprecated contracts.

The policy may initially be minimal, but it must be explicit.

------------------------------------------------------------------------

## 12. Observability and Audit Boundary

Integration operations must preserve sufficient information to
distinguish:

-   external request identity;
-   contract identity/version;
-   operation;
-   security context;
-   authorization result;
-   runtime result;
-   failure category.

Detailed audit implementation may evolve later, but the Integration
Contract and Runtime boundaries must not make observability impossible.

Security-sensitive information must not be exposed in external errors.

------------------------------------------------------------------------

## 13. Explicit Non-Goals

The following are outside Phase 12 unless required to demonstrate the
MVP:

-   complete REST API for the entire platform;
-   complete gRPC API;
-   WebSocket infrastructure;
-   production message broker deployment;
-   universal connector framework implementation;
-   arbitrary third-party connector ecosystem;
-   universal ETL engine;
-   generalized synchronization engine;
-   bidirectional replication;
-   workflow engine;
-   event-sourced accounting;
-   replacing Runtime Services with Integration Services;
-   direct database API;
-   exposing internal persistence models;
-   implementing new business domains solely for integration;
-   building a UI/API gateway as a separate business layer.

These remain future capabilities.

------------------------------------------------------------------------

## 14. Proposed Phase Structure

The following is the preliminary implementation decomposition. It is
intentionally not an API commitment and must be refined during Concrete
API Design.

### Slice 1 --- Integration Foundation

Establish Integration domain boundaries, contracts, shared errors,
identity/version primitives, and dependency rules.

### Slice 2 --- Integration Contracts

Implement representative command/query/event contract abstractions and
stable response/error semantics.

### Slice 3 --- Integration Runtime

Implement contract resolution, request routing, security integration,
Runtime invocation, and response mapping.

### Slice 4 --- Event Infrastructure

Implement event contracts, publisher/subscriber boundaries, in-process
event delivery, and integration of an existing business event source.

### Slice 5 --- Import / Export

Implement the minimum contract-based import/export path required by the
MVP.

### Slice 6 --- Standard Integration Composition

Expose a representative Standard Edition
command/query/report/event/import/export set.

### Slice 7 --- Validation and Closure

Run architectural validation, full test suite, quality gates,
documentation reconciliation, and Phase 12 closure.

This structure remains subject to change after Concrete API Design.

------------------------------------------------------------------------

## 15. Acceptance Criteria

Phase 12 is complete when all of the following are satisfied.

### AC-1 --- Defined API Contract

At least one supported operation is represented by a versioned
Integration Contract.

### AC-2 --- Runtime Routing

An external request reaches the appropriate Runtime boundary through
Integration.

### AC-3 --- Security Enforcement

Protected external operations are authenticated and authorized through
the Phase 11 Security boundary.

### AC-4 --- Stable Responses

Supported operations expose stable, documented success and error
responses.

### AC-5 --- Event Publication

At least one supported completed business fact is published through
Event Infrastructure.

### AC-6 --- Event Consumption

A supported subscriber can receive a published event without being
coupled to the publisher implementation.

### AC-7 --- Import

A minimum supported import scenario passes through contract validation
and Runtime execution without direct state manipulation.

### AC-8 --- Export

A minimum supported export scenario obtains data through an approved
Runtime/Reporting boundary.

### AC-9 --- Protocol Independence

Core Integration Contracts do not depend on a concrete communication
protocol.

### AC-10 --- Failure Isolation

Event subscriber and connector failures cannot corrupt or roll back
completed core business transactions under the default integration
model.

### AC-11 --- Storage Isolation

No supported integration path accesses persistence structures directly.

### AC-12 --- Documentation

All implemented contracts and their supported integration semantics are
documented.

------------------------------------------------------------------------

## 16. Architectural Invariants

The following invariants are introduced or reinforced by Phase 12:

``` text
External Access → Integration Boundary

Integration → Security → Runtime

Commands → State Change

Queries → No State Change

Events → Completed Facts

Events → After Successful Completion

API → Contract Publication

Contracts → Protocol Independent

Connectors → Adaptation Only

Import/Export → Contract Based

Integration → No Direct Storage Access
```

These invariants must remain true as future protocols and connectors are
added.

------------------------------------------------------------------------

## 17. Architecture Decision Summary

Phase 12 adopts the following decisions:

1.  Integration is an external boundary, not a business layer.
2.  Integration is contract-first.
3.  Integration Contracts are protocol-independent.
4.  APIs publish contracts rather than define business operations.
5.  Commands are the only state-changing external interaction category.
6.  Queries are read-only.
7.  Reporting datasets are preferred for analytical integration.
8.  Events describe completed facts.
9.  Events are published after successful business transaction
    completion.
10. Event publishers are independent from subscribers.
11. Event processing is not part of core business execution.
12. Import/export is contract-based.
13. Connectors are adapters and contain no business logic.
14. Integration is mediated by Security and Runtime.
15. Integration never accesses persistence directly.
16. Phase 12 implements only the minimum representative subset required
    for Standard Edition external usability.

------------------------------------------------------------------------

## 18. Architecture Review --- Final

### Review result

**APPROVED FOR CONCRETE API DESIGN**

The architecture is consistent with the existing AcCoreD Integration
Architecture and with the completed Reporting, Processing, and Security
phases.

No blocking architectural contradiction was identified.

### Review findings

#### R1 --- Scope alignment: PASS

The scope directly implements the roadmap priorities:

1.  API contracts;
2.  API runtime;
3.  event infrastructure;
4.  import/export;
5.  required adapters.

The broader existing Integration Architecture is preserved as the
long-term architecture rather than incorrectly treated as the Phase 12
implementation requirement.

#### R2 --- Runtime ownership: PASS

Integration does not become a second Runtime.

Business execution remains owned by existing Runtime Services.

#### R3 --- Security boundary: PASS

Phase 11 is correctly treated as a mandatory dependency.

Integration cannot provide an alternate authorization path.

#### R4 --- Event semantics: PASS

The definition is consistent with the Event Architecture:

-   events are facts;
-   events are immutable;
-   events follow successful transaction completion;
-   subscribers are decoupled;
-   subscriber failure does not invalidate completed business
    processing.

Existing posting event mechanisms are to be reused rather than
duplicated.

#### R5 --- API/protocol separation: PASS

The contract-first principle is preserved and HTTP/REST is not made part
of the core integration model.

#### R6 --- Import/export boundary: PASS WITH SCOPE CONTROL

The architecture is sound, provided implementation remains limited to
the MVP scenarios and does not expand into ETL, synchronization, mapping
DSLs, or universal transformation infrastructure.

#### R7 --- Standard Edition scope: PASS

The representative operation set is appropriate for validating vertical
integration without attempting to expose the entire platform.

#### R8 --- Failure isolation: PASS

Event and connector failures are explicitly separated from core business
transaction success.

#### R9 --- Versioning: PASS

Contract versioning is explicitly separated from transport versioning.

Concrete API Design must define the exact versioning primitives and
compatibility rules.

#### R10 --- Observability: PASS

The architecture preserves the minimum identity, contract, security,
authorization, and result information necessary for meaningful
integration observability without prematurely designing a complete
distributed tracing system.

------------------------------------------------------------------------

## 19. Concrete API Design Gate

The following items are intentionally deferred to Concrete API Design:

1.  Exact `IntegrationContract` identity/version value objects.
2.  Exact command/query request and response abstractions.
3.  Error taxonomy and external error mapping.
4.  Exact Integration Service interface.
5.  Contract resolution mechanism.
6.  Security context propagation contract.
7.  Authorization invocation boundary.
8.  Event identity, envelope, metadata, and version model.
9.  Subscriber failure semantics and delivery guarantees for the MVP.
10. Import/export contract interfaces.
11. Format adapter abstraction.
12. Representative Standard operations.
13. Protocol adapter boundary.
14. Request correlation/operation identity.
15. Compatibility/deprecation mechanics.

These decisions must not be implemented before the Concrete API Design
has been reviewed and approved.

------------------------------------------------------------------------

## 20. Approval Status

**Architecture Definition / Scope: APPROVED FOR CONCRETE API DESIGN**

Phase 12 may proceed to the next architectural artifact:

**`PHASE_12_Integration_Concrete_API_Design.md`**

Implementation is explicitly deferred until the Concrete API Design has
been completed and approved.
