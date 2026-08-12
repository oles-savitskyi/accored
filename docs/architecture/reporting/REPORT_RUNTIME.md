# REPORT_RUNTIME.md

## Purpose

This document defines the runtime architecture of the Reporting subsystem.

The Reporting Runtime is responsible for executing compiled report definitions and producing analytical datasets.

The runtime layer does not own metadata definitions, business data, register data, valuation data, or presentation logic.

Its responsibility is limited to report execution orchestration.

The Reporting Runtime follows the platform architectural principles:

* Metadata-Driven Architecture
* Runtime/Metadata Separation
* Service-Oriented Runtime
* Execution Plan-Based Processing
* Dataset-Oriented Execution
* Platform Service Reuse

---

# Runtime Responsibilities

The Reporting Runtime is responsible for:

* Report execution coordination
* Metadata compilation
* Execution plan generation
* Data source resolution
* Dataset acquisition
* Dataset processing orchestration
* Runtime context integration
* Dataset delivery

The Reporting Runtime is not responsible for:

* Metadata storage
* Business object storage
* Register storage
* Cost storage
* UI rendering
* Export generation

---

# Runtime Architecture

The Reporting Runtime consists of the following components:

```text id="3n7vrv"
Report Runtime

 ├── Report Manager
 ├── Report Compiler
 ├── Execution Plan Builder
 ├── Report Executor
 ├── Data Source Manager
 ├── Runtime Context Adapter
 └── Dataset Cache
```

Each component has a clearly defined responsibility.

---

# Report Manager

## Purpose

The Report Manager is the primary entry point of the Reporting Runtime.

All report execution requests pass through the Report Manager.

---

## Responsibilities

* Resolve report metadata
* Validate execution requests
* Validate parameters
* Coordinate report execution
* Return resulting datasets

---

## Example Flow

```text id="e3tz3r"
Run Report Request
         ↓
Report Manager
         ↓
Report Dataset
```

The Report Manager acts as a runtime façade.

---

# Report Compiler

## Purpose

Transform report metadata into runtime structures.

---

## Responsibilities

* Compile data sources
* Compile filters
* Compile dimensions
* Compile measures
* Compile calculated expressions

---

## Compilation Flow

```text id="spq8n7"
Report Metadata
        ↓
Report Compiler
        ↓
Compiled Report
```

The compiler operates on metadata definitions only.

---

# Execution Plan Builder

## Purpose

Generate executable runtime plans.

---

## Responsibilities

* Analyze compiled reports
* Build execution pipelines
* Create execution nodes
* Produce execution plans

---

## Planning Flow

```text id="9h16z4"
Compiled Report
        ↓
Execution Plan Builder
        ↓
Execution Plan
```

---

## Typical Plan Structure

```text id="zqf9r0"
Source
Filter
Projection
Group
Aggregate
Calculate
Sort
```

Execution plans are runtime artifacts.

---

# Report Executor

## Purpose

Execute report execution plans.

---

## Responsibilities

* Execute runtime plans
* Coordinate processing stages
* Invoke platform services
* Produce datasets

---

## Execution Flow

```text id="gjqmrz"
Execution Plan
        ↓
Report Executor
        ↓
Dataset
```

The executor operates exclusively on runtime structures.

It does not access report metadata directly.

---

# Data Source Manager

## Purpose

Provide a unified runtime interface for all report data sources.

---

## Responsibilities

* Resolve source providers
* Validate source availability
* Acquire source datasets
* Normalize provider interaction

---

## Supported Source Categories

```text id="9w33hr"
Object Sources

Register Movement Sources

Register Totals Sources

Cost Movement Sources

Cost Balance Sources

Report Dataset Sources
```

---

## Example

```text id="5g2mhp"
Inventory Balance Source
         ↓
Inventory Balance Provider
         ↓
Dataset
```

The Reporting Runtime remains independent from underlying storage implementations.

---

# Runtime Context Adapter

## Purpose

Provide controlled access to platform runtime context.

---

## Responsibilities

* User context access
* Company context access
* Session context access
* Localization context access
* Security context access

---

## Context Flow

```text id="d1pr7m"
Runtime Context
        ↓
Context Adapter
        ↓
Reporting Runtime
```

This abstraction simplifies testing and improves runtime isolation.

---

# Dataset Cache

## Purpose

Provide future support for report execution caching.

---

## Potential Cache Layers

```text id="kntrhb"
Compiled Report Cache

Execution Plan Cache

Dataset Cache
```

---

## Responsibilities

* Cache lookup
* Cache storage
* Cache invalidation
* Cache lifecycle management

````

Cache implementation is platform-specific.

Caching does not alter report semantics.

---

# Runtime Lifecycle

The complete report execution lifecycle is:

```text id="eh3i6m"
User Request
        ↓
Report Manager
        ↓
Report Compiler
        ↓
Compiled Report
        ↓
Execution Plan Builder
        ↓
Execution Plan
        ↓
Report Executor
        ↓
Data Source Manager
        ↓
Raw Dataset
        ↓
Table Engine
        ↓
Expression Engine
        ↓
Report Dataset
````

Each stage has a dedicated responsibility and clear boundaries.

---

# Table Engine Integration

## Purpose

Reuse the platform Table Engine for dataset processing.

---

## Integration Model

```text id="x7h7i7"
Report Executor
        ↓
Table Engine
        ↓
Filtering
Projection
Grouping
Aggregation
```

---

## Benefits

* Shared execution model
* Shared optimization mechanisms
* Shared memory management
* Reduced implementation complexity

The Reporting subsystem does not implement a separate analytical processing engine.

---

# Expression Engine Integration

## Purpose

Reuse the platform Expression Engine for calculated measures.

---

## Integration Model

```text id="d8w4x8"
Aggregated Dataset
         ↓
Expression Engine
         ↓
Calculated Measures
```

---

## Benefits

* Single expression language
* Shared dependency tracking
* Shared optimization infrastructure
* Consistent calculation behavior

---

# Metadata Service Integration

The Reporting Runtime depends on Metadata Services for:

* Report definitions
* Data source definitions
* Dimension definitions
* Measure definitions

Metadata remains owned by Metadata Architecture.

---

# Security Service Integration

The Reporting Runtime may use platform security services for:

* Report execution permissions
* Data source permissions
* Dataset visibility rules
* User-specific restrictions

Security remains owned by Runtime and Security Architecture.

---

# Storage Independence

The Reporting Runtime must remain independent from:

* Database technologies
* Storage backends
* Register persistence models
* Cost persistence models

All storage access occurs through providers.

---

# Runtime Independence

The Reporting Runtime must remain independent from:

* Qt
* Web UI
* Mobile UI
* Excel Export
* PDF Export
* Dashboard Rendering

The runtime produces datasets only.

---

# ADR-013: Reporting Is Implemented As Runtime Service

## Status

Accepted

## Decision

Reporting functionality is provided through Runtime Services rather than through standalone report-specific infrastructure.

## Consequences

* Reporting integrates naturally with Runtime Architecture.
* Common service lifecycle is reused.
* Runtime context is reused.
* Security services are reused.

---

# ADR-014: Report Manager Is Runtime Entry Point

## Status

Accepted

## Decision

All report execution requests are handled through Report Manager.

## Consequences

* Single runtime entry point.
* Consistent lifecycle management.
* Consistent validation.
* Consistent monitoring and logging.

---

# ADR-015: Report Executor Operates On Execution Plans

## Status

Accepted

## Decision

Report Executor executes execution plans and does not access report metadata directly.

## Consequences

* Clear Metadata/Runtime separation.
* Easier optimization.
* Easier testing.
* Runtime simplification.

---

# ADR-016: Reporting Runtime Reuses Platform Services

## Status

Accepted

## Decision

Reporting Runtime reuses existing platform services whenever possible.

## Consequences

* Reduced implementation complexity.
* Consistent platform behavior.
* Shared optimization infrastructure.
* Lower maintenance costs.
