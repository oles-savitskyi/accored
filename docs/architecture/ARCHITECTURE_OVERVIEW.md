# ARCHITECTURE_OVERVIEW.md

## Purpose

This document provides a high-level overview of the AcCoreD architecture.

It describes the major architectural subsystems, their responsibilities, and relationships.

Detailed implementation rules are defined in dedicated architecture documents.

---

# Architecture Vision

AcCoreD (Accounting Core Development) is a metadata-driven accounting and business application platform.

The platform is designed to support:

* accounting systems;
* ERP systems;
* CRM systems;
* HRMS systems;
* inventory management systems;
* industry-specific business solutions.

The architecture prioritizes:

* metadata-driven configuration;
* extensibility;
* auditability;
* deterministic processing;
* storage independence;
* UI independence.

---

# # Architectural Baseline

Current architecture baseline:

```text
architecture-core-2.8
```

Architecture status:

Architecture Maturity ≈ 9.8 / 10

Status: READY FOR IMPLEMENTATION

Architectural Risk: LOW

Major Redesign Risk: VERY LOW

```text
Foundation Complete

Metadata Architecture Complete

Runtime Architecture Complete

Object Architecture Complete

Storage Architecture Complete

Posting Architecture Complete

Register Architecture Complete

Valuation Architecture Complete

Reporting Architecture Complete

Integration Architecture Complete

Security Architecture Complete

Workflow Architecture Complete

Configuration Architecture Complete
```


---

# # Platform Architecture Model

The AcCoreD platform consists of three major architectural domains:

```text
Transactional Core
        ↓
Business Facts
        ↓
Reporting Layer
        ↓
Datasets
        ↓
Integration Layer
        ↓
External Systems
```
Transactional Core is responsible for creating and maintaining business facts.

Reporting transforms business facts into analytical datasets.

Integration exposes platform capabilities and information to external environments.

Ключевая формула платформы

Platform
      +
Configuration
      +
Extensions
      =
Business Application

Ключевая формула композиции

Platform Metadata
        +
Configuration Metadata
        +
Extension Metadata
        =
Runtime Metadata Model
---

# Architectural Layers

The AcCoreD platform is organized into the following architectural layers.

Metadata Layer
        ↓
Compilation Layer
        ↓
Runtime Layer
        ↓
Business Objects
        ↓
Posting Engine
        ↓
Register Engine
        ↓
Valuation Engine
        ↓
Reporting Engine
        ↓
Integration Layer
        ↓
External Systems

Each layer builds on services provided by lower layers.
---

# Standard Configuration Layer

The AcCore platform includes a reference Standard Configuration intended for small and medium-sized businesses.

The Standard Configuration provides:

* Reference Data Model;
* Standard Documents;
* Register Mapping;
* Standard Workflows;
* Standard Roles;
* Standard Reports;
* Security Configuration.

The Standard Configuration is implemented entirely through metadata and configuration mechanisms and does not require platform modifications.

# Architecture Map

```text
Platform
      +
Configuration
      +
Extensions
      ↓
Runtime Metadata Model
      ↓
Runtime
      ↓
Business Objects
      ↓
Documents
      ↓
Workflows
      ↓
Posting
      ↓
Registers
      ↓
Valuation
      ↓
Reporting
      ↓
Roles & Security
```

---

# Core Architectural Subsystems

## 1. Metadata Architecture

Defines application structure using metadata.

Responsibilities:

* metadata model;
* metadata compilation;
* metadata validation;
* metadata references;
* metadata semantics.

---

## 2. Runtime Architecture

Provides execution infrastructure.

Responsibilities:

* lifecycle management;
* service management;
* dependency resolution;
* execution context;
* runtime services.

---

## 3. Object Architecture

Provides business object model.

Responsibilities:

* catalogs;
* documents;
* business objects;
* object lifecycle;
* object services.

---

## 4. Storage Architecture

Provides persistent data storage.

Responsibilities:

* storage model;
* document storage;
* register storage;
* totals storage;
* persistence infrastructure.

Storage Model:

```text id="ac23b5"
Hybrid Storage Model
```

Identity Model:

```text id="ac23b6"
ULID
```

---

## 5. Posting Architecture

Transforms business events into accounting facts.

Responsibilities:

* posting lifecycle;
* posting handlers;
* posting context;
* posting dependencies;
* movement generation.

Output:

```text id="ac23b7"
Register Movements
```

---

## 6. Register Architecture

Provides quantity and state accounting.

Responsibilities:

* information registers;
* accumulation registers;
* totals engine;
* register query model;
* register dependencies.

Core Artifacts:

```text id="ac23b8"
Register Movement

Register Totals
```

---

## 7. Valuation Architecture

Provides cost accounting and valuation processing.

Valuation Architecture is independent from quantity accounting while operating on the same economic objects.

Responsibilities:

* valuation layers;
* valuation methods;
* valuation adjustments;
* valuation allocations;
* cost movements;
* cost balances;
* valuation rebuild and recovery.

Core Principles:

```text id="ac23b9"
Quantity Is Independent From Cost

Cost Facts May Arrive After Quantity Facts

Cost Is Produced By Valuation Engine

Everything That Has Quantity Must Have Value
```

Core Artifacts:

```text id="ac23c0"
Valuation Layer

Valuation Consumption

Valuation Adjustment

Valuation Allocation

Cost Movement

Cost Balance
```

Processing Model:

```text id="ac23c1"
Valuation Engine
        ↓
Cost Movement

Cost Totals Engine
        ↓
Cost Balance
```

---

## 8. Reporting Architecture

Reporting Architecture is responsible for transforming business, register, and valuation information into analytical datasets and user-consumable representations.

The subsystem consists of:

Report Metadata Model
Data Source Model
Dataset Definition Model
Dimension & Measure Model
Report Execution Model
Report Runtime Model
Report Presentation Model

Reporting follows the platform-wide Metadata → Compilation → Runtime architecture.


### Reporting Principles
Reports are Metadata Objects.
Reports are Compiled Before Execution.
Report Execution Produces Datasets.
Dataset And Presentation Are Independent.
Reporting Reuses Platform Runtime Services.
Reporting Reuses Table Engine.
Reporting Reuses Expression Engine.
Presentation Is Renderer Independent.

## 9. Integration Architecture

Integration Architecture provides controlled interaction between AcCoreD and external environments.

The subsystem consists of:

Integration Architecture

Integration Model

API Architecture

Event Architecture

Import/Export Architecture

External Connectors

Integration follows the platform-wide Metadata → Compilation → Runtime architecture.

### Responsibilities

* integration contracts;
* integration services;
* API publication;
* event publication;
* import operations;
* export operations;
* connector management;
* external system integration.

### Core Principles

Contract-First Integration

Event-Aware Architecture

Integration Never Bypasses Runtime

File Formats Are Transport Mechanisms

Connectors Adapt External Systems

### Core Artifacts

```text
Integration Contract

Integration Service

API Contract

Event Contract

Import Contract

Export Contract

External Connector
```

## 10. Security Architecture

## 11. Workflow Architecture 

## 12. Configuration Architecture

## 13. Standard Configuration

### Continuous Cost Recognition

Business costs should be recognized and allocated as soon as the underlying business event occurs.

Period closing is a fallback mechanism rather than the primary cost recognition mechanism.

---

### Economic Objects Are Unified

All business resources, including inventory, labor, depreciation, and services, ultimately contribute costs to Economic Objects through a unified allocation model.

---

### Registers Store Quantities, Valuation Stores Costs

Registers record quantitative facts.

Valuation Architecture is responsible for cost calculation, cost allocation, and cost balances.

---

### Labor And Depreciation Follow The Same Resource Model As Inventory

Labor and asset utilization are treated as quantitative resources.

Their costs are calculated and allocated through the same valuation principles used for inventory resources.

---

### Role Permissions Are Business-Object-Oriented

Permissions are defined against business domains and business objects rather than technical CRUD operations.

---

### Access Rights Are Defined Through Access Modes

The Standard Configuration defines three access modes:

* View;
* Execute;
* Administer.


Configuration Architecture Maturity
≈ 9.9 / 10

# Cross-Cutting Architectural Principles

The following principles apply to all subsystems:

1. Metadata-Driven Architecture

2. Runtime/Metadata Separation

3. Deterministic Processing

4. Explicit Facts

5. Reproducible Results

6. Auditability

7. Separation Of Concerns

8. Storage Independence

9. UI Independence

10. Extensibility Through Metadata

11. Incremental Evolution

12. Posting Produces Register Facts

13. Registers Are Source Of Quantity State

14. Valuation Is Independent From Quantity Accounting

15. Cost Facts May Arrive After Quantity Facts

16. Cost Is Produced By Valuation Engine

17. Everything That Has Quantity Must Have Value

18. Cost Balances Are Maintained By Cost Totals Engine

19. Operational Queries Use Materialized Results

20. Audit Queries Use Valuation Facts

21. Reports Produce Datasets

22. Dataset And Presentation Are Independent

23. Presentation Is Renderer Independent

24. Contract-First Integration

25. Events Describe Facts, Not Commands

26. Integration Never Bypasses Runtime

27. APIs Publish Contracts

28. File Formats Are Transport Mechanisms

29. Connectors Adapt External Systems

30. Event Processing Does Not Affect Business Transactions

31. Security Is Metadata-Driven

32. Default Deny

33. Least Privilege

34. Fail Closed

35. Audit Is Append-Only

36. Authentication And Authorization Are Separate

37. Workflow Is Metadata-Driven

38. Workflow Is State-Based

39. Workflow Does Not Bypass Security

40. Workflow Is Audit-Aware

41. Workflow Definitions And Workflow Instances Are Separate

42. Platform And Configuration Are Separate

43. Runtime Executes Unified Metadata

44. Configuration Is Metadata-Based

45. Extensions Are Additive

46. Runtime Metadata Model Is Immutable

47. Configuration Defines, Platform Executes
```
---

# # Current Architecture Status

Completed architectural stages:

```text
Architecture Foundation

Metadata Architecture

Runtime Architecture

Object Architecture

Storage Architecture

Posting Architecture

Register Architecture

Valuation Architecture

Reporting Architecture

Integration Architecture

Security Architecture

Workflow Architecture

Configuration Architecture
```

Planned architectural stages:

```text
Deployment Architecture

UI Architecture

Extension Architecture
```

---

# Architecture Maturity

Current maturity estimate:

```text
≈ 10.0 / 10
```

Current status:

```text
READY FOR NEXT ARCHITECTURAL STAGE
```

