# ADR-019: External Access Uses Services
Status

Accepted

Decision

External systems interact with AcCore through Integration Services rather than through direct access to internal storage structures.

Consequences
Storage remains encapsulated.
Business rules remain enforced.
Security policies remain centralized.
Internal architecture remains replaceable.

# ADR-020: Reporting Is The Preferred Analytical Integration Mechanism
Status

Accepted

Decision

External analytical consumers should obtain information through Reporting Architecture datasets rather than direct access to accounting structures.

Consequences
Reporting logic is centralized.
Analytical consistency is preserved.
Duplicate reporting implementations are avoided.
Dataset reuse is encouraged.

# ADR-021: Integration Is Contract-Driven
Decision

External interaction is defined by contracts rather than implementation details.

Consequences
Versioning becomes possible.
Backward compatibility becomes manageable.
Protocol independence becomes possible.

# ADR-022: Commands Modify State
Decision

Integration Commands are the only integration mechanism allowed to modify platform state.

Consequences
Consistent business rule enforcement.
Clear auditability.
Predictable side effects.

# ADR-023: Queries Do Not Modify State
Decision

Integration Queries must not change platform state.

Consequences
Predictable behavior.
Easier caching.
Easier scaling.

# ADR-024: Events Describe Facts
Decision

Integration Events describe completed facts rather than requested actions.

Consequences
Loose coupling.
Event-driven extensibility.
Independent subscribers.

# ADR-025: API Is Contract Publication
Decision

APIs are generated from Integration Contracts.

Contracts are not derived from APIs.

Consequences
Single source of truth.
Protocol independence.
Consistent external interfaces.
Easier versioning.

# ADR-026: Contracts Are Versioned
Decision

Versioning is applied to contracts rather than transport protocols.

Example
CustomerContract v1
CustomerContract v2

а не:

/api/v1/customer
/api/v2/customer

# ADR-027: API Does Not Define Business Operations
Decision

Business operations are defined by Runtime Services and Integration Contracts.

APIs only expose those operations.

Consequences
Business logic remains transport-independent.
Multiple protocols may expose identical functionality.
API redesign does not require business redesign.
Internal architecture remains stable.

# ADR-028: AcCore Is Event-Aware
Status

Accepted

Decision

AcCore uses events as a mechanism for observation, integration, notification, and extension.

Events do not drive core business execution.

Consequences
Business execution remains deterministic.
Posting, Registers, Valuation, and Reporting remain pipeline-driven.
Events become optional consumers of completed business facts.
Event processing failures do not invalidate completed business transactions.

# ADR-029: Events Are Published After Transaction Completion
Status

Accepted

Decision

Events are published only after successful completion of the originating business transaction.

Consequences
Events never describe failed operations.
Subscribers observe committed facts.
Event failures do not rollback business transactions.

# ADR-030: Publishers Are Independent From Subscribers
Status

Accepted

Decision

Event publishers remain unaware of subscriber implementations.

Consequences
Loose coupling.
Independent evolution.
Easier extensibility.

# ADR-031: Events Are Contract-Based
Status

Accepted

Decision

Published events are defined through Event Contracts.

Consequences
Versioning support.
Consumer stability.
Consistent integration model.

# ADR-032: Connectors Are Adapters

## Status

Accepted

## Decision

Connectors adapt external systems to AcCore contracts and services.

## Consequences

* Clear architectural boundaries.
* Protocol independence.
* Easier maintenance.
* Improved extensibility.

---

# ADR-033: Connectors Do Not Contain Business Logic

## Status

Accepted

## Decision

Business logic remains owned by Runtime Services and business subsystems.

Connectors perform adaptation only.

## Consequences

* Single source of business behavior.
* Reduced duplication.
* Consistent platform behavior.
* Easier testing.

---

# ADR-034: Connector Failures Must Not Affect Core Processing

## Status

Accepted

## Decision

Connector execution is isolated from business transaction execution.

## Consequences

* Improved reliability.
* Stable accounting behavior.
* Safe external integration.
* Better operational resilience.
 

# ADR-035: Import/Export Is Contract-Based

## Status

Accepted

## Decision

Import and Export operations are defined through Integration Contracts rather than file formats.

## Consequences

* Format independence.
* Protocol independence.
* Consistent validation.
* Reusable integration model.
* Stable business semantics.

---

# ADR-036: Import Does Not Bypass Runtime

## Status

Accepted

## Decision

Imported information must enter the platform exclusively through Runtime Services.

## Consequences

* Business rules remain enforced.
* Register integrity is preserved.
* Valuation consistency is preserved.
* Reporting consistency is preserved.
* Platform behavior remains predictable.

---

# ADR-037: File Formats Are Transport Mechanisms

## Status

Accepted

## Decision

File formats are transport representations and must not define business semantics.

## Consequences

* Business meaning remains contract-driven.
* Multiple formats may publish identical contracts.
* Long-term maintainability improves.
* Integration flexibility increases.

# ADR-038: Integration Never Bypasses Runtime
Status

Accepted

Decision

All external interactions must be executed through Integration Contracts, Integration Services, and Runtime Services.

No integration mechanism may directly manipulate storage, registers, valuation state, or reporting state.

Consequences
Architectural consistency.
Business rule enforcement.
Auditability.
Long-term maintainability.