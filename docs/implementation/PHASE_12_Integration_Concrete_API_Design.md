# Phase 12 — Integration
## Concrete API Design

**Status:** FINAL — APPROVED FOR IMPLEMENTATION  
**Phase:** 12 — Integration  
**Architectural prerequisite:** `PHASE_12_Integration_Architecture_Definition_Scope.md`  
**Purpose:** Define the concrete platform-level API model for the minimum Integration capabilities required to make the Standard Edition externally usable.

---

## 1. Purpose

This document translates the approved Phase 12 Integration Architecture Definition into a concrete API design suitable for implementation.

The design establishes:

- first-class Integration Contracts;
- explicit command, query, dataset, event, import, and export contract kinds;
- executable operation bindings separate from contract definitions;
- protocol-independent Integration Services;
- explicit propagation of `SecurityContext`;
- reuse of the existing Phase 11 authorization model without duplicating Runtime authorization;
- in-process event publication and subscription for the MVP;
- contract-driven import/export;
- transport/protocol adapters outside the core Integration execution model;
- stable external error categories;
- explicit contract versioning;
- deterministic request and correlation identities.

The design deliberately avoids prematurely committing the platform to HTTP, REST, gRPC, a message broker, a particular serialization format, or durable distributed infrastructure.

---

# 2. Design Principles

## 2.1 Contract-first

An externally usable capability is represented by an explicit Integration Contract.

A contract defines:

- identity;
- version;
- kind;
- externally visible semantics;
- input/output expectations;
- validation expectations;
- security requirements where applicable.

A contract does **not** define how the operation is executed.

---

## 2.2 Contract and execution are separate concerns

The central distinction is:

> **Contract = what is published. Operation = how that contract is executed.**

Therefore:

```text
IntegrationContract
        |
        | resolved by identity
        v
IntegrationOperation
        |
        | executes through binding
        v
Integration Runtime / Business Runtime
```

This prevents API contracts from becoming coupled to Runtime implementation details.

---

## 2.3 Integration does not implement business logic

Integration is an external boundary.

It:

- resolves contracts;
- validates requests;
- establishes request identity;
- propagates security context;
- invokes appropriate Runtime/business boundaries;
- maps results and errors into stable Integration representations;
- publishes or consumes events;
- orchestrates import/export exchange.

It does not:

- implement posting;
- implement processing algorithms;
- implement reporting algorithms;
- implement valuation;
- own business persistence;
- replace Runtime services.

---

## 2.4 Security context is propagated, not reinvented

Phase 11 already defines:

- `Principal`;
- `Session`;
- `SecurityContext`;
- `AuthorizationRequest`;
- `AuthorizationService`;
- `AuthorizationDecision`;
- `AuthorizationDeniedError`.

Integration must reuse these abstractions.

Authentication remains outside the core `IntegrationService`. A protocol adapter or host environment establishes the authenticated identity and constructs the existing `SecurityContext`.

For Runtime-owned operations, authoritative authorization remains at the Runtime boundary.

For example, Processing already performs authorization in `DefaultProcessingRuntime` before executing a `ProcessingCommand`.

Therefore Integration must **not** create a second independent authorization policy for Processing.

The intended flow is:

```text
Protocol Adapter
    |
    v
SecurityContext
    |
    v
Integration
    |
    v
ProcessingRuntime
    |
    +--> authoritative AuthorizationService check
    |
    v
Processing
```

Integration may enforce authorization directly only for capabilities that do not pass through an existing protected Runtime boundary.

---

## 2.5 Immutable boundary objects

Requests, responses, contract identities, event envelopes, and result objects should be immutable value objects wherever practical.

This reduces accidental mutation across integration boundaries.

---

## 2.6 Protocol independence

The core Integration API does not depend on:

- HTTP;
- REST;
- gRPC;
- CLI;
- message brokers;
- specific serialization formats.

Protocols are adapters over the Integration model.

---

## 2.7 Explicit versioning

Contract identity includes an explicit version.

Versioning policy:

- major version changes represent breaking changes;
- minor version changes represent backward-compatible changes;
- version components are non-negative integers;
- multiple compatible contract versions may coexist;
- resolution must be deterministic.

---

# 3. Package Structure

The initial Integration package is:

```text
src/accore/platform/integration/
    __init__.py
    contract.py
    request.py
    response.py
    errors.py
    service.py
    registry.py
    event.py
    import_export.py
    adapter.py
```

The exact internal decomposition may be refined during implementation, provided the public architectural contracts remain stable.

---

# 4. Contract Model

## 4.1 ContractVersion

```python
@dataclass(frozen=True, slots=True)
class ContractVersion:
    major: int
    minor: int
```

Validation:

- `major >= 0`
- `minor >= 0`

Version semantics:

```text
1.0 -> 1.1
```

is backward-compatible.

```text
1.x -> 2.0
```

may contain breaking changes.

---

## 4.2 IntegrationContractKind

```python
class IntegrationContractKind(StrEnum):
    COMMAND = "command"
    QUERY = "query"
    DATASET = "dataset"
    EVENT = "event"
    IMPORT = "import"
    EXPORT = "export"
```

`DATASET` remains a distinct API/contract kind because the platform architecture explicitly identifies Dataset APIs.

However, Phase 12 does **not** introduce a separate Dataset Runtime.

Dataset operations use query-like execution and may return existing logical dataset models such as `ReportDataset`.

---

## 4.3 IntegrationContractIdentity

```python
@dataclass(frozen=True, slots=True)
class IntegrationContractIdentity:
    namespace: str
    name: str
    version: ContractVersion
    kind: IntegrationContractKind
```

Validation:

- `namespace` must be non-empty;
- `name` must be non-empty;
- `version` must be valid;
- `kind` must be explicit.

The identity is the stable key used for contract/operation resolution.

---

## 4.4 IntegrationContract

Conceptually:

```python
class IntegrationContract(Protocol):
    @property
    def identity(self) -> IntegrationContractIdentity:
        ...

    @property
    def description(self) -> str:
        ...
```

Concrete contract types may provide additional schema and validation metadata.

The contract describes the external capability. It does not contain executable business behavior.

---

# 5. Request Model

Public request types are semantic rather than unnecessarily generic.

The design uses explicit:

```python
CommandRequest
QueryRequest
```

rather than exposing a redundant generic `IntegrationRequest` hierarchy.

A common internal/base representation may be used if implementation convenience requires it, but it is not part of the required public API.

---

## 5.1 CommandRequest

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class CommandRequest(Generic[P]):
    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier
```

A command represents a requested state-changing operation.

Examples:

- execute Processing;
- post a document;
- invoke a supported business operation;
- import business data.

---

## 5.2 QueryRequest

```python
@dataclass(frozen=True, slots=True)
class QueryRequest(Generic[P]):
    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier
```

A query requests information without expressing a state-changing business command.

Examples:

- obtain a report dataset;
- retrieve a supported external view;
- execute a read-oriented platform capability.

---

## 5.3 Request Identity

`request_identity` uses the existing platform `Identifier`.

It provides:

- operation identity;
- correlation anchor;
- external request tracking;
- a future basis for idempotency.

Phase 12 does **not** introduce a generic durable idempotency store.

---

# 6. Response Model

## 6.1 CommandResponse

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class CommandResponse(Generic[R]):
    request_identity: Identifier
    result: R
```

---

## 6.2 QueryResponse

```python
@dataclass(frozen=True, slots=True)
class QueryResponse(Generic[R]):
    request_identity: Identifier
    result: R
```

The response model is intentionally independent of a wire protocol.

Protocol adapters may transform it into HTTP, JSON, gRPC, CLI, or another representation.

---

# 7. Executable Operation Model

The central execution abstraction is `IntegrationOperation`.

```python
class IntegrationOperation(Protocol):
    @property
    def contract(self) -> IntegrationContract:
        ...

    @property
    def binding(self) -> IntegrationOperationBinding:
        ...
```

The binding contains the executable integration behavior.

Conceptually:

```python
class IntegrationOperationBinding(Protocol):
    def execute(self, request: object) -> object:
        ...
```

Typed specializations should be used for concrete command/query operations.

The important architectural rule is:

```text
Contract
    describes the capability

Operation
    binds the capability to executable behavior
```

---

# 8. Operation Registry

The registry resolves an external contract identity into an executable operation.

```python
class IntegrationOperationRegistry(Protocol):
    def register(self, operation: IntegrationOperation) -> None:
        ...

    def resolve(
        self,
        identity: IntegrationContractIdentity,
    ) -> IntegrationOperation:
        ...
```

Registration must reject conflicting registrations for the same identity.

Resolution failure maps to the stable Integration contract error model.

A separate contract-only registry is not required for the MVP because the externally useful lookup is ultimately:

```text
Contract Identity -> Executable Operation
```

A separate metadata registry may be introduced later if discovery/catalog functionality requires it.

---

# 9. Integration Service

The protocol-independent entry point is:

```python
class IntegrationService(Protocol):
    def execute_command(
        self,
        request: CommandRequest[P],
    ) -> CommandResponse[R]:
        ...

    def execute_query(
        self,
        request: QueryRequest[P],
    ) -> QueryResponse[R]:
        ...
```

Responsibilities:

1. resolve operation;
2. validate contract/request;
3. preserve request identity;
4. propagate `SecurityContext`;
5. execute the operation binding;
6. map known failures to Integration errors;
7. return a stable response.

It does not own business execution logic.

---

# 10. Security Integration

## 10.1 Security Requirement

Operations may declare a security requirement:

```python
@dataclass(frozen=True, slots=True)
class IntegrationSecurityRequirement:
    target: SecurityObjectIdentity
    operation: SecurityOperation
```

The requirement identifies the authorization semantics expected by the operation.

---

## 10.2 Authorization Boundary

The implementation must distinguish two cases.

### Runtime-owned operation

For a capability delegated to an existing Runtime that already performs authoritative authorization:

```text
Integration
    |
    | SecurityContext
    v
Runtime
    |
    | AuthorizationService.require(...)
    v
Business execution
```

Integration does not perform a duplicate authorization check.

This is the required model for the existing Processing Runtime.

### Integration-owned capability

If an Integration capability does not pass through a protected Runtime boundary, the Integration binding may invoke:

```python
AuthorizationService.require(
    AuthorizationRequest(...)
)
```

using the existing Phase 11 security types.

Integration must not introduce a parallel authorization model.

---

## 10.3 Authentication

Authentication is outside the core Integration service.

Protocol adapters or host environments are responsible for establishing:

```python
SecurityContext
```

from the authenticated request.

Integration consumes that context.

---

# 11. Command Execution

A representative Processing command follows:

```text
External Command
    |
    v
Protocol Adapter
    |
    v
CommandRequest
    |
    v
Contract Resolution
    |
    v
Payload Validation
    |
    v
Integration Operation
    |
    v
ProcessingCommand
    |
    v
ProcessingRuntime
    |
    +--> AuthorizationService
    |
    v
Business Processing
    |
    v
ProcessingResult
    |
    v
CommandResponse
    |
    v
Protocol Adapter
    |
    v
External Response
```

The Integration binding maps external command payloads to the existing `ProcessingCommand`.

It does not duplicate Processing behavior.

---

# 12. Query Execution

Representative reporting flow:

```text
External Query
    |
    v
QueryRequest
    |
    v
Contract Resolution
    |
    v
Payload Validation
    |
    v
Integration Operation
    |
    v
ReportExecutionPlan
    |
    v
ReportRuntime
    |
    v
ReportDataset
    |
    v
QueryResponse
```

A Dataset contract may use the same execution path while retaining `DATASET` as its externally visible contract kind.

---

# 13. Dataset API

Dataset APIs are first-class contract identities:

```python
IntegrationContractKind.DATASET
```

but do not require a separate Dataset Runtime.

A Dataset operation may therefore:

- resolve as a Dataset contract;
- validate Dataset-specific input;
- invoke Reporting Runtime or another appropriate query-oriented Runtime;
- return a stable dataset model.

For example:

```text
Dataset Contract
      |
      v
Dataset Operation
      |
      v
ReportRuntime
      |
      v
ReportDataset
```

This preserves the architecture's distinction between Query APIs and Dataset APIs without introducing unnecessary runtime duplication.

---

# 14. Error Model

Integration exposes a stable error taxonomy.

## 14.1 Categories

```python
class IntegrationErrorCategory(StrEnum):
    CONTRACT = "contract"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    EXECUTION = "execution"
    CONFLICT = "conflict"
    INTERNAL = "internal"
```

---

## 14.2 Errors

Conceptual types include:

```text
IntegrationError
IntegrationContractNotFoundError
IntegrationContractVersionError
IntegrationContractValidationError
IntegrationRequestValidationError
IntegrationMalformedRequestError
IntegrationAuthorizationError
IntegrationExecutionError
```

`IntegrationAuthorizationError` is an external Integration representation of authorization failure, not a replacement for Phase 11 authorization semantics.

When Runtime authorization raises an existing security authorization exception, Integration maps it into the stable external Integration error representation.

Internal implementation details must not leak through the protocol boundary.

---

# 15. Event Model

## 15.1 Event Contract

Events are immutable facts describing completed business events.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class EventContract:
    identity: IntegrationContractIdentity
    security_requirement: IntegrationSecurityRequirement | None
```

Events are not commands.

---

## 15.2 Event Envelope

```python
@dataclass(frozen=True, slots=True)
class EventEnvelope(Generic[E]):
    event_identity: IntegrationContractIdentity
    event_id: Identifier
    occurred_at: datetime
    payload: E
    source: str
    correlation_identity: Identifier | None
```

Fields:

- `event_identity` identifies the published event contract;
- `event_id` uniquely identifies the event;
- `occurred_at` records event occurrence;
- `payload` contains the immutable event data;
- `source` identifies the originating subsystem;
- `correlation_identity` optionally associates the event with an initiating request.

---

# 16. Event Publication

The MVP publisher is:

```python
class EventPublisher(Protocol):
    def publish(self, event: EventEnvelope[object]) -> None:
        ...
```

The Phase 12 MVP is:

- in-process;
- non-durable;
- synchronous unless implementation constraints require otherwise;
- subscriber-isolated;
- without broker infrastructure.

The originating business transaction completes before event publication is considered successful.

Subscriber failure does not roll back the already completed business transaction.

The MVP does not promise:

- durable delivery;
- replay;
- dead-letter queues;
- distributed retries;
- broker persistence;
- exactly-once delivery.

These remain future infrastructure concerns.

---

# 17. Event Subscription

Routing is conceptually:

```text
Event Identity
      |
      v
Subscription Registry / Dispatcher
      |
      +--> Subscriber A
      |
      +--> Subscriber B
      |
      +--> Subscriber C
```

A subscriber consumes an event:

```python
class EventSubscriber(Protocol):
    def handle(self, event: EventEnvelope[object]) -> None:
        ...
```

Subscription matching is handled by the dispatcher/registry rather than requiring each subscriber to implement routing logic.

The MVP does not require a general broker abstraction.

---

# 18. Existing Posting Events

Phase 12 must reuse the existing Posting event mechanism.

The platform already defines:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

and:

```python
PostingEventPublisher
```

with:

```python
publish(event: object) -> None
```

Integration must provide an adapter/bridge from `PostingEventPublisher` to the Integration `EventPublisher`.

The Posting subsystem must not be rewritten to introduce a second event mechanism.

The intended architecture is:

```text
PostingEngine
    |
    v
PostingEventPublisher
    |
    v
Integration Event Adapter
    |
    v
EventPublisher
    |
    v
Integration subscribers
```

This preserves the existing Phase 9/10/11 architecture and makes Phase 12 an integration layer rather than a competing event framework.

---

# 19. Import Model

Import is contract-driven.

The contract defines:

- accepted logical input;
- validation rules;
- semantic expectations;
- result expectations.

The contract does not execute business logic.

Therefore an import contract must not contain a general `execute()` method.

Conceptually:

```python
class ImportContract(Protocol):
    @property
    def identity(self) -> IntegrationContractIdentity:
        ...

    def validate(self, payload: object) -> None:
        ...
```

Execution belongs to the Integration operation/binding.

---

# 20. Import Request and Result

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class ImportRequest(Generic[P]):
    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier
```

and:

```python
@dataclass(frozen=True, slots=True)
class ImportResult(Generic[R]):
    request_identity: Identifier
    result: R
    metadata: Mapping[str, str]
```

The import operation:

```text
External Source
    |
    v
Format Adapter
    |
    v
Logical Import Payload
    |
    v
Import Contract
    |
    v
Integration Operation
    |
    v
Runtime / Business Service
```

Business semantics remain independent of the physical input format.

---

# 21. Export Model

Export is also contract-driven.

An export contract describes:

- logical output;
- semantics;
- required data;
- validation expectations.

It does not implement serialization or business execution.

Conceptually:

```python
class ExportContract(Protocol):
    @property
    def identity(self) -> IntegrationContractIdentity:
        ...

    def validate(self, payload: object) -> None:
        ...
```

Execution belongs to the Integration operation/binding.

---

## 21.1 ExportResult

The result is typed:

```python
@dataclass(frozen=True, slots=True)
class ExportResult(Generic[T]):
    request_identity: Identifier
    content: T
    metadata: Mapping[str, str]
```

`T` may be an existing logical platform representation such as `ReportDataset`.

The result does not require a physical serialization format.

---

# 22. Format Adapters

Physical formats are represented by adapters.

## 22.1 ExportFormatAdapter

```python
class ExportFormatAdapter(Protocol):
    @property
    def format_name(self) -> str:
        ...

    def serialize(self, result: ExportResult[object]) -> bytes:
        ...
```

## 22.2 ImportFormatAdapter

```python
class ImportFormatAdapter(Protocol):
    @property
    def format_name(self) -> str:
        ...

    def deserialize(self, content: bytes) -> object:
        ...
```

These adapters are responsible for:

- parsing;
- serialization;
- physical format concerns.

They are not responsible for:

- business rules;
- authorization policy;
- persistence;
- Runtime execution.

Phase 12 should select the smallest concrete format needed for the Standard Edition MVP rather than introducing a universal format framework.

---

# 23. Protocol Adapters

Protocol adapters sit outside the core Integration execution model.

Conceptually:

```text
External Protocol
       |
       v
Protocol Adapter
       |
       v
IntegrationService
       |
       v
Runtime / Event / Import / Export
```

An adapter is responsible for:

- transport parsing;
- authentication handoff;
- serialization/deserialization;
- transport-level error mapping;
- invocation of `IntegrationService`;
- serialization of Integration responses.

It is not responsible for:

- business logic;
- Runtime behavior;
- authorization policy;
- persistence.

Potential future protocols include:

- HTTP/REST;
- gRPC;
- message transport;
- CLI;
- embedded/native API.

No protocol is hard-coded into the core Integration package.

---

# 24. Request Lifecycle

The general lifecycle is:

```text
Protocol Adapter
    |
    v
Deserialize
    |
    v
Authenticate / establish SecurityContext
    |
    v
Integration Request
    |
    v
Contract / Operation Resolution
    |
    v
Payload Validation
    |
    v
SecurityContext propagation
    |
    v
Runtime or Integration-owned Authorization
    |
    v
Runtime Invocation
    |
    v
Result Mapping
    |
    v
Integration Response
    |
    v
Serialize
    |
    v
External Consumer
```

The security step is intentionally expressed as:

> SecurityContext propagation + authoritative authorization at the owning boundary

rather than implying that Integration always performs authorization itself.

---

# 25. Event Lifecycle

```text
Business Runtime
    |
    | successful business operation
    v
Business Event
    |
    v
Event Adapter
    |
    v
EventEnvelope
    |
    v
Event Dispatcher
    |
    +--> Subscriber
    +--> Subscriber
    +--> Subscriber
```

The event describes a completed fact.

It does not replace the command that caused the fact.

---

# 26. Import Lifecycle

```text
External Source
    |
    v
Format Adapter
    |
    v
Logical Payload
    |
    v
Import Contract
    |
    v
Validation
    |
    v
Integration Operation
    |
    v
Runtime / Business Service
    |
    v
ImportResult
```

---

# 27. Export Lifecycle

```text
External Request
    |
    v
Export Contract
    |
    v
Validation
    |
    v
Integration Operation
    |
    v
Runtime / Business Service
    |
    v
ExportResult[T]
    |
    v
Format Adapter
    |
    v
Serialized Output
```

---

# 28. Standard Integration Examples

The MVP should demonstrate at least the following representative capabilities.

## 28.1 Processing Command

A Standard Processing operation maps an Integration command to:

```python
ProcessingCommand
```

and invokes:

```python
ProcessingRuntime.execute(...)
```

Authorization remains authoritative at the Processing Runtime boundary.

---

## 28.2 Reporting Query

A Standard reporting operation maps an Integration query to:

```python
ReportExecutionPlan
```

and invokes:

```python
ReportRuntime.execute(...)
```

The resulting `ReportDataset` is returned through a `QueryResponse` or `ExportResult`, depending on the published contract.

---

## 28.3 Business Event

A Standard posting operation publishes:

```text
DocumentPosted
DocumentUnposted
DocumentReposted
```

through the existing Posting event publisher and the new Integration event adapter.

---

## 28.4 Standard Import

At least one small Standard import capability should be exposed through the contract-driven import model.

The concrete business object and physical format are implementation decisions for the corresponding slice.

---

## 28.5 Standard Export

At least one Standard export capability should be exposed through the export model.

The concrete format should be the smallest useful MVP format.

---

# 29. Version Resolution

The registry must resolve contract identity deterministically.

A lookup includes:

```text
namespace
name
version
kind
```

Compatibility rules:

- exact version match is preferred;
- if compatible minor-version resolution is supported, selection must be deterministic;
- major-version compatibility must never be assumed;
- ambiguous resolution must fail explicitly.

The initial MVP may require exact version matching and introduce richer negotiation later.

---

# 30. Correlation and Identity

`request_identity` is the primary external operation identity.

Events may carry:

```python
correlation_identity: Identifier | None
```

Normally:

```text
Request Identity
      |
      v
Business Operation
      |
      v
Event correlation_identity
```

Distributed tracing identifiers are outside the Phase 12 core API.

---

# 31. Validation

Validation occurs at multiple levels.

## 31.1 Contract validation

Checks:

- known contract;
- correct contract kind;
- supported version.

## 31.2 Request validation

Checks:

- required request fields;
- request identity;
- security context;
- payload shape.

## 31.3 Payload validation

Checks business-facing contract input constraints before Runtime invocation.

Business semantics that belong to the Runtime remain there.

Integration must not duplicate Runtime validation unnecessarily.

---

# 32. Dependency Direction

The intended dependency direction is:

```text
Protocol Adapter
       |
       v
Integration
       |
       +--> Security Contracts
       |
       +--> Runtime Contracts
       |
       v
Business / Runtime Services
       |
       v
Infrastructure
```

The Integration layer must not depend directly on:

- database repositories;
- storage implementation details;
- transport implementation details;
- UI code.

Business Runtime code should not depend on a specific external transport.

---

# 33. Testing Model

## 33.1 Unit tests

Required unit coverage includes:

- `ContractVersion`;
- `IntegrationContractIdentity`;
- contract kind;
- request validation;
- registry registration/resolution;
- duplicate registration;
- error mapping;
- event envelope;
- event dispatch;
- import/export contracts;
- format adapters.

---

## 33.2 Integration tests

Required integration coverage includes:

1. Integration → Security → Runtime;
2. representative Processing command;
3. representative Reporting query;
4. existing Posting event → Integration event;
5. event subscription;
6. representative import;
7. representative export.

---

## 33.3 Protocol tests

Protocol-specific tests are required only when a concrete protocol adapter is introduced.

The core Integration tests must remain transport-independent.

---

# 34. Implementation Slices

Implementation should proceed in the following order.

## Slice 1 — Integration Domain Foundation

Implement:

- contract identity;
- version;
- contract kinds;
- request/response foundations;
- Integration errors;
- validation primitives.

## Slice 2 — Contract and Operation Registry

Implement:

- `IntegrationOperation`;
- executable bindings;
- registry;
- deterministic resolution;
- duplicate/conflict handling.

## Slice 3 — Integration Runtime

Implement:

- `IntegrationService`;
- command execution;
- query execution;
- Runtime invocation;
- SecurityContext propagation;
- error mapping.

Representative vertical path:

```text
Integration Command
    -> ProcessingRuntime
    -> ProcessingResult
    -> Integration Response
```

## Slice 4 — Event Infrastructure

Implement:

- EventContract;
- EventEnvelope;
- EventPublisher;
- dispatcher/subscription;
- Posting event bridge;
- event tests.

## Slice 5 — Import / Export

Implement:

- import/export contracts;
- operation bindings;
- request/result models;
- format adapters;
- one MVP import;
- one MVP export.

## Slice 6 — Standard Integration Composition

Implement:

- Standard contract definitions;
- Standard operation bindings;
- Standard registry composition;
- representative external-use paths.

## Slice 7 — Validation and Closure

Perform:

- full test suite;
- Integration targeted tests;
- quality checks;
- architecture reconciliation;
- documentation reconciliation;
- final Phase 12 closure.

---

# 35. Explicit Non-Goals

Phase 12 does not implement:

- complete REST/OpenAPI surface;
- OAuth/OIDC framework;
- a generic identity provider;
- database repositories for integration;
- durable event broker infrastructure;
- distributed event replay;
- dead-letter infrastructure;
- distributed tracing;
- universal workflow orchestration;
- universal import mapping DSL;
- generic data synchronization engine;
- every possible Standard API;
- a separate Dataset Runtime;
- a second authorization framework.

These may be addressed by later phases when concrete requirements justify them.

---

# 36. Architectural Decisions Incorporated

The following decisions are final for implementation.

### D1 — Typed requests

**Decision:** Use explicit semantic request types such as `CommandRequest` and `QueryRequest`.

### D2 — Security requirement

**Decision:** Operations may declare a security target and operation. Integration reuses Phase 11 security types. Authoritative authorization remains at the owning Runtime boundary.

### D3 — Event infrastructure

**Decision:** MVP uses in-process event publication and subscription.

### D4 — Event timing

**Decision:** Events represent successfully completed business operations. Existing business transactions are not rolled back because of subscriber failure.

### D5 — Dataset API

**Decision:** `DATASET` remains a distinct contract kind, but uses query-like execution and existing Runtime capabilities.

### D6 — Import/export formats

**Decision:** Physical formats are independent adapters. The MVP introduces only the smallest concrete format required.

### D7 — Protocol

**Decision:** Core Integration remains protocol-independent. The smallest concrete external protocol adapter required for Standard Edition usability is introduced later in implementation.

### D8 — Idempotency

**Decision:** Request identity exists now. A generic durable idempotency mechanism is not part of Phase 12.

### D9 — Authentication

**Decision:** Authentication is outside `IntegrationService`. Adapters or host environments construct the existing `SecurityContext`.

### D10 — Contract versus execution

**Decision:** Contracts define published semantics; executable `IntegrationOperation` bindings define execution. Import/Export contracts therefore do not contain business execution methods.

### D11 — Posting events

**Decision:** Existing `PostingEventPublisher` remains the source-side event mechanism. Integration provides an adapter rather than introducing a second Posting event system.

---

# 37. Final Approval Criteria

Phase 12 implementation may begin when:

- this Concrete API Design is accepted as the implementation contract;
- Slice 1 can be implemented without architectural reinterpretation;
- all operation resolution paths are explicit;
- Runtime authorization boundaries remain unchanged;
- Dataset remains a first-class API kind without a separate Runtime;
- import/export contracts are separated from execution;
- event integration reuses existing Posting events.

This document is the concrete implementation baseline for Phase 12.

---

## 38. Summary

The Phase 12 Integration API establishes a deliberately small external boundary:

```text
                 External World
                       |
                Protocol Adapter
                       |
                IntegrationService
                       |
             Contract / Operation
                  Resolution
                       |
          +------------+------------+
          |            |            |
       Command       Query       Dataset
          |            |            |
          v            v            v
       Runtime       Runtime      Runtime
          |
          v
     Business Platform
          |
          +------> Event Adapter ------> Event Infrastructure
          |
          +------> Import / Export
```

The design preserves the architecture already established in AcCoreD:

- Security remains a platform concern owned by Phase 11;
- Processing remains a Runtime concern;
- Reporting remains a Runtime concern;
- Posting remains the source of Posting business events;
- Integration becomes the externally usable boundary without absorbing business logic.

**Status: FINAL — APPROVED FOR IMPLEMENTATION**
