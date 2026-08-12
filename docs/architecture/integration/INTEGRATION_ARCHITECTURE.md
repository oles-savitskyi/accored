# INTEGRATION_ARCHITECTURE.md

## Purpose

This document defines the architectural boundaries, responsibilities, principles, and high-level structure of the AcCore Integration Architecture.

Integration Architecture is responsible for controlled interaction between AcCore and external systems, services, applications, and users.

The Integration Architecture enables interoperability while preserving platform integrity, consistency, security, and architectural independence.

---

# Architectural Position

Integration Architecture forms the boundary between AcCore and the external world.

```text
External World
        ↓
Integration Architecture
        ↓
Runtime Services
        ↓
Business Platform
```

All external interactions must pass through Integration Architecture.

External systems must not directly access internal platform storage structures.

---

# Purpose Of Integration

Integration Architecture exists to:

* Exchange data with external systems
* Expose platform functionality
* Receive external requests
* Publish platform events
* Support synchronization processes
* Support import and export operations
* Support mobile and distributed applications

---

# Responsibilities

Integration Architecture is responsible for:

* Service integration
* Event integration
* File integration
* Dataset integration
* External communication
* Integration protocol abstraction
* Connector management
* Data exchange orchestration

---

# Non-Responsibilities

Integration Architecture is not responsible for:

* Business logic execution
* Posting execution
* Register processing
* Valuation processing
* Report execution
* Presentation rendering
* Data persistence

These responsibilities remain owned by their respective architectural subsystems.

---

# Core Architectural Principle

External systems interact with platform services.

External systems do not interact with platform storage.

```text
External System
        ↓
Integration Service
        ↓
Runtime Service
        ↓
Business Objects
```

This principle protects platform integrity and business rules.

---

# Integration Categories

AcCore supports multiple integration categories.

```text
Service Integration

Event Integration

File Integration

Dataset Integration
```

Each category serves a distinct integration purpose.

---

# Service Integration

## Purpose

Provide request-response interaction between external systems and AcCore.

---

## Examples

```text
Create Customer

Create Document

Post Document

Get Inventory Balance

Get Business Object
```

---

## Characteristics

* Synchronous
* Request-response based
* Service-oriented
* Runtime mediated

---

## Architecture

```text
External System
        ↓
Service Endpoint
        ↓
Integration Service
        ↓
Runtime Service
```

---

# Event Integration

## Purpose

Provide asynchronous communication between AcCore and external systems.

---

## Examples

```text
Document Posted

Customer Created

Inventory Changed

Cost Recalculated
```

---

## Characteristics

* Event-driven
* Asynchronous
* Publisher-subscriber model
* Decoupled communication

---

## Architecture

```text
Business Event
        ↓
Integration Event
        ↓
Subscribers
```

---

# File Integration

## Purpose

Support exchange of structured information through files.

---

## Examples

```text
CSV

Excel

JSON

XML
```

---

## Typical Scenarios

```text
Import Customers

Import Products

Export Inventory

Export Reports
```

---

## Characteristics

* Batch-oriented
* Offline capable
* Technology independent

---

# Dataset Integration

## Purpose

Expose analytical datasets to external consumers.

---

## Architecture

```text
External System
        ↓
Dataset Request
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

Dataset Integration allows external systems to consume analytical information without direct access to internal accounting structures.

---

# Connector Framework

## Purpose

Provide extensible integration mechanisms for external platforms and services.

---

## Examples

```text
CRM Connectors

ERP Connectors

E-Commerce Connectors

Payment Connectors

Messaging Connectors
```

---

## Responsibilities

* Protocol adaptation
* Authentication handling
* Data mapping
* Integration lifecycle management

---

# External Consumers

Typical consumers include:

```text
ERP Systems

CRM Systems

HRMS Systems

BMS Systems

Mobile Applications

Web Applications

Third-Party Services
```

The architecture remains independent from specific vendors and products.

---

# Integration Principles

The Integration Architecture follows the following principles.

---

## Service-Oriented Integration

All external access occurs through services.

External systems do not access storage structures directly.

---

## Runtime-Mediated Access

Integration components interact with Runtime Services rather than business storage.

---

## Storage Independence

Integration Architecture must remain independent from:

* Database technologies
* Storage implementations
* Register persistence mechanisms
* Valuation persistence mechanisms

---

## Protocol Independence

Integration logic must remain independent from communication protocols.

Possible protocols may include:

```text
HTTP

REST

gRPC

Message Queues

WebSockets
```

Protocol selection must not affect business logic.

---

## Dataset Reuse

Analytical information should be exposed through Reporting Architecture whenever possible.

Integration Architecture should reuse existing datasets rather than implement duplicate reporting logic.

---

## Event-Driven Extensibility

Platform events should be publishable to external consumers without modifying business logic.

---

# High-Level Architecture

```text
Integration Architecture

 ├── Service Integration
 ├── Event Integration
 ├── File Integration
 ├── Dataset Integration
 └── Connector Framework
```

Each integration category may evolve independently.

---

# Runtime Integration

Integration Architecture relies on existing Runtime Services.

```text
Integration Layer
        ↓
Runtime Services
        ↓
Business Objects
Posting
Registers
Valuation
Reporting
```

Integration Architecture does not bypass runtime boundaries.

---

# Reporting Integration

Reporting Architecture remains the preferred mechanism for exposing analytical information.

```text
Reporting Runtime
        ↓
Dataset
        ↓
Integration Architecture
        ↓
External Consumer
```

This guarantees consistent analytical results across all consumers.

---

# Future Extensions

The architecture is designed to support future additions such as:

```text
REST APIs

Message Buses

Event Streams

Webhooks

Mobile Synchronization

Partner Integrations
```

without requiring redesign of the Integration Architecture.

---

# ADR-019: External Access Uses Services

## Status

Accepted

## Decision

External systems interact with AcCore through Integration Services rather than through direct access to internal storage structures.

## Consequences

* Storage remains encapsulated.
* Business rules remain enforced.
* Security remains centralized.
* Internal implementations remain replaceable.
* Platform integrity is preserved.

---

# ADR-020: Reporting Is The Preferred Analytical Integration Mechanism

## Status

Accepted

## Decision

External analytical consumers should obtain information through Reporting Architecture datasets rather than direct access to accounting structures.

## Consequences

* Reporting logic is centralized.
* Analytical consistency is preserved.
* Duplicate reporting implementations are avoided.
* Dataset reuse is encouraged.

---

# Architectural Summary

Integration Architecture provides a controlled boundary between AcCore and external systems.

It enables service interaction, event delivery, file exchange, dataset exposure, and connector-based interoperability while preserving the architectural principles of the platform.

The architecture ensures that all external interactions remain mediated by Runtime Services and never bypass platform business rules.
