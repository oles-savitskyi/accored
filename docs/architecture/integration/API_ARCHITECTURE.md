# API_ARCHITECTURE.md

## Purpose

This document defines the API Architecture of AcCore.

The API Architecture is responsible for publishing Integration Contracts through external communication protocols while preserving platform architectural principles and business integrity.

APIs are publication mechanisms.

APIs are not business models.

APIs are not business logic containers.

Business functionality remains owned by Runtime Services and Integration Architecture.

---

# Architectural Position

The API Architecture is positioned between external consumers and the Integration Layer.

```text
External Consumer
         ↓
Communication Protocol
         ↓
API Publication Layer
         ↓
Integration Contract
         ↓
Integration Service
         ↓
Runtime Services
         ↓
Business Platform
```

The API layer exposes platform capabilities without exposing internal implementation details.

---

# API Principles

The API Architecture follows the following principles:

* Contract-First API
* Service-Oriented Integration
* Protocol Independence
* Runtime-Mediated Access
* Storage Independence
* Versioned Contracts
* Event-Driven Extensibility

---

# Contract-First API Model

## Principle

Integration Contracts are the primary API artifact.

Protocols publish contracts.

Protocols do not define contracts.

---

## Architecture

```text
Integration Contract
          ↓
API Publication Layer
          ↓
REST
gRPC
WebSocket
Message Bus
```

The contract is the single source of truth.

---

# API Publication Layer

## Purpose

Transform Integration Contracts into protocol-specific API representations.

---

## Responsibilities

* Contract publication
* Protocol mapping
* Endpoint generation
* Schema publication
* Version exposure

---

## Non-Responsibilities

The API Publication Layer is not responsible for:

* Business logic
* Storage access
* Posting execution
* Register operations
* Valuation processing
* Reporting calculations

These responsibilities remain owned by Runtime Services.

---

# API Categories

AcCore exposes four API categories.

```text
Command APIs

Query APIs

Event APIs

Dataset APIs
```

Each category represents a different interaction model.

---

# Command APIs

## Purpose

Expose operations that modify platform state.

---

## Examples

```text
Create Customer

Update Product

Create Document

Post Document

Delete Document
```

---

## Characteristics

* State changing
* Business logic execution
* Auditable
* Side effects permitted

---

## Architecture

```text
Command Contract
         ↓
Command API
         ↓
Integration Service
         ↓
Runtime Service
```

---

# Query APIs

## Purpose

Expose operations that retrieve information without modifying state.

---

## Examples

```text
Get Customer

Get Product

Get Inventory Balance

Get Cost Balance

Get Report Dataset
```

---

## Characteristics

* Read-only
* Side effect free
* Repeatable
* Cacheable

---

## Architecture

```text
Query Contract
       ↓
Query API
       ↓
Integration Service
       ↓
Runtime Service
```

---

# Event APIs

## Purpose

Expose business facts as external events.

---

## Examples

```text
Customer Created

Document Posted

Inventory Changed

Cost Recalculated
```

---

## Characteristics

* Asynchronous
* Event-driven
* Publish-subscribe
* Fact-oriented

---

## Architecture

```text
Business Event
        ↓
Integration Event
        ↓
Event API
        ↓
Subscribers
```

---

# Dataset APIs

## Purpose

Expose analytical datasets to external consumers.

---

## Architecture

```text
External Consumer
         ↓
Dataset API
         ↓
Reporting Runtime
         ↓
Dataset
```

---

## Examples

```text
Sales Dataset

Inventory Dataset

Cost Analysis Dataset

Financial Dataset
```

Dataset APIs are the preferred mechanism for exposing analytical information.

---

# API Publication Targets

The API Architecture supports multiple publication targets.

Examples include:

```text
REST

gRPC

WebSocket

Message Bus
```

Additional publication targets may be added without modifying Integration Contracts.

---

# REST Publication

## Purpose

Expose contracts through HTTP-based REST endpoints.

---

## Example

```text
CreateCustomerContract
            ↓
POST /customers
```

---

## Characteristics

* Human-friendly
* Widely supported
* Integration-oriented

REST is a publication mechanism.

REST is not the primary architectural model.

---

# gRPC Publication

## Purpose

Expose contracts through service-oriented RPC endpoints.

---

## Example

```text
CreateCustomerContract
            ↓
CustomerService.CreateCustomer()
```

---

## Characteristics

* High performance
* Strong typing
* Service-oriented communication

gRPC is a publication mechanism.

gRPC is not the primary architectural model.

---

# WebSocket Publication

## Purpose

Support real-time communication and event delivery.

---

## Examples

```text
Inventory Changed

Document Posted

Cost Recalculated
```

---

## Characteristics

* Real-time
* Bidirectional
* Event-friendly

---

# Message Bus Publication

## Purpose

Support asynchronous integration through messaging systems.

---

## Examples

```text
Document Posted

Customer Created

Inventory Changed
```

---

## Characteristics

* Decoupled communication
* Reliable delivery
* Event distribution

---

# Protocol Independence

Integration Contracts remain independent from communication protocols.

A single contract may be published through multiple protocols.

Example:

```text
CustomerContract
       ↓
REST

CustomerContract
       ↓
gRPC

CustomerContract
       ↓
Message Bus
```

Contract definitions remain unchanged.

---

# Versioning Model

## Purpose

Support long-term evolution of public interfaces.

---

## Versioning Principle

Versioning applies to contracts.

Versioning does not apply primarily to protocols.

---

## Example

```text
CustomerContract v1

CustomerContract v2
```

Protocol publications reflect contract versions.

---

## Benefits

* Backward compatibility
* Controlled evolution
* Consumer stability

---

# Security Integration

The API Architecture integrates with platform security mechanisms.

---

## Security Flow

```text
External Consumer
         ↓
Authentication
         ↓
Authorization
         ↓
Contract Execution
```

---

## Responsibilities

API Architecture:

* Identity propagation
* Access control integration
* Contract protection

Security Architecture remains responsible for:

* Authentication models
* Authorization models
* Permission management
* Security policies

---

# Runtime Integration

API requests ultimately execute Runtime Services.

```text
API
 ↓
Integration Service
 ↓
Runtime Service
 ↓
Business Platform
```

The API layer never bypasses Runtime boundaries.

---

# Reporting Integration

Analytical information should be exposed through Reporting Architecture whenever possible.

```text
Dataset API
      ↓
Reporting Runtime
      ↓
Dataset
```

This guarantees consistent analytical behavior across all consumers.

---

# Architectural Boundaries

The API Architecture must remain independent from:

* Storage technologies
* Database schemas
* Register persistence models
* Valuation persistence models
* UI technologies

The API Architecture publishes contracts.

It does not own business functionality.

---

# ADR-025: API Is Contract Publication

## Status

Accepted

## Decision

APIs are generated from Integration Contracts.

Contracts are not derived from APIs.

## Consequences

* Single source of truth.
* Protocol independence.
* Consistent interfaces.
* Easier versioning.

---

# ADR-026: Contracts Are Versioned

## Status

Accepted

## Decision

Versioning is applied to contracts rather than communication protocols.

## Consequences

* Stable integrations.
* Backward compatibility.
* Controlled evolution.
* Reduced protocol coupling.

---

# ADR-027: API Does Not Define Business Operations

## Status

Accepted

## Decision

Business operations are defined by Runtime Services and Integration Contracts.

APIs only expose those operations.

## Consequences

* Business logic remains transport-independent.
* Multiple protocols may expose identical functionality.
* API redesign does not require business redesign.
* Internal architecture remains stable.

---

# Architectural Summary

The API Architecture provides a contract-first publication model for external interaction.

Contracts define capabilities.

APIs publish contracts.

Protocols transport contracts.

Runtime Services execute business functionality.

This architecture ensures protocol independence, long-term maintainability, and alignment with the overall AcCore architectural principles.
