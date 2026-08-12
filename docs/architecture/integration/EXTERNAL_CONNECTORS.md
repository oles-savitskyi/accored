# EXTERNAL_CONNECTORS.md

## Purpose

This document defines the Connector Framework of AcCore.

External Connectors provide integration between AcCore and external systems while preserving platform architectural boundaries, business rules, and runtime integrity.

Connectors adapt external environments to AcCore.

Connectors do not implement business logic.

---

# Architectural Position

External Connectors are part of Integration Architecture.

```text
External System
        ↓
Connector
        ↓
Integration Contract
        ↓
Integration Service
        ↓
Runtime Services
        ↓
Business Platform
```

Connectors isolate external technologies from internal platform architecture.

---

# Connector Purpose

The Connector Framework exists to:

* Integrate external applications
* Integrate external services
* Integrate partner platforms
* Support data synchronization
* Support event delivery
* Support command execution
* Support dataset consumption

---

# Architectural Principle

Connectors adapt.

Connectors do not own business behavior.

Business logic remains inside:

* Business Objects
* Runtime Services
* Posting Engine
* Register Engine
* Valuation Engine
* Reporting Runtime

---

# Connector Categories

AcCore supports multiple connector categories.

```text
Application Connectors

Service Connectors

Messaging Connectors

Dataset Connectors

Synchronization Connectors
```

---

# Application Connectors

## Purpose

Integrate external business applications.

---

## Examples

```text
CRM Systems

ERP Systems

HRMS Systems

BMS Systems

E-Commerce Platforms
```

---

## Typical Operations

```text
Create Customer

Update Product

Create Order

Receive Inventory Data
```

---

# Service Connectors

## Purpose

Integrate external services.

---

## Examples

```text
Payment Services

Tax Services

Currency Services

Email Providers

SMS Providers
```

---

## Characteristics

* Service-oriented
* Request-response based
* Contract-driven

---

# Messaging Connectors

## Purpose

Integrate external messaging infrastructure.

---

## Examples

```text
Message Queues

Event Brokers

Streaming Platforms
```

---

## Responsibilities

* Event publication
* Event consumption
* Message translation
* Contract mapping

---

# Dataset Connectors

## Purpose

Expose analytical information to external consumers.

---

## Architecture

```text
Reporting Runtime
        ↓
Dataset
        ↓
Dataset Connector
        ↓
External Consumer
```

---

## Examples

```text
BI Platforms

Data Warehouses

Analytics Systems

Executive Dashboards
```

---

# Synchronization Connectors

## Purpose

Synchronize information between AcCore and external systems.

---

## Examples

```text
Mobile Clients

Field Applications

Remote Warehouses

Partner Systems
```

---

# Connector Responsibilities

Connectors may perform:

* Protocol adaptation
* Schema mapping
* Authentication integration
* Contract translation
* Event delivery
* Error translation

---

# Connector Non-Responsibilities

Connectors must not perform:

* Posting
* Register updates
* Valuation calculations
* Report calculations
* Business rule enforcement

These operations remain owned by the platform.

---

# Connector Runtime Model

Connectors are runtime-managed components.

```text
Connector
        ↓
Contract
        ↓
Integration Service
        ↓
Runtime Service
```

Connectors never bypass Integration Services.

---

# Connector Lifecycle

```text
Registration
        ↓
Initialization
        ↓
Activation
        ↓
Operation
        ↓
Deactivation
        ↓
Removal
```

The lifecycle is managed by Connector Runtime.

---

# Connector Manager

## Purpose

Centralized management of all connector instances.

---

## Responsibilities

* Registration
* Discovery
* Configuration
* Activation
* Monitoring
* Shutdown

---

## Architecture

```text
Connector Manager
        ↓
Connector Runtime
        ↓
Connector Instances
```

---

# Connector Metadata Model

Connectors are metadata-defined platform objects.

Examples:

```text
ConnectorDefinition

ConnectorConfiguration

ConnectorMappingDefinition
```

---

## Metadata Lifecycle

```text
Metadata
        ↓
Compiler
        ↓
Runtime Connector
```

Connector Architecture follows the platform Metadata → Compilation → Runtime model.

---

# Connector Configuration

Connectors must be configurable without code modifications.

Typical configuration includes:

* Endpoints
* Credentials
* Mapping Rules
* Synchronization Policies
* Retry Policies

Configuration remains separate from implementation.

---

# Event Integration

Connectors may subscribe to Integration Events.

```text
Business Event
        ↓
Event Runtime
        ↓
Connector
        ↓
External System
```

Connectors consume events through Event Architecture.

---

# API Integration

Connectors may invoke Commands and Queries through Integration Services.

```text
Connector
        ↓
Contract
        ↓
Integration Service
```

Connectors remain consumers of public integration contracts.

---

# Security Integration

Connectors participate in platform security.

Security Architecture remains responsible for:

* Authentication
* Authorization
* Credential Management
* Access Policies

Connectors must not implement independent security models.

---

# Fault Isolation

Connector failures must not affect core platform execution.

```text
Connector Failure
        ↓
Connector Disabled
```

Core business execution continues.

---

# Versioning

Connectors depend on Integration Contracts rather than internal implementations.

```text
Connector
        ↓
Contract v1

Connector
        ↓
Contract v2
```

Versioning remains contract-driven.

---

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

---

# Architectural Summary

The Connector Framework provides a standardized mechanism for integrating external applications, services, messaging platforms, synchronization systems, and analytical consumers.

Connectors adapt external environments to AcCore Contracts and Runtime Services while preserving platform integrity, business consistency, and architectural independence.

Connectors extend the platform.

Connectors do not redefine the platform.
