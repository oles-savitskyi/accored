# REPORT_EXECUTION_MODEL.md

## Purpose

This document defines the execution model of Reporting Architecture.

The execution model describes how report metadata is transformed into an analytical dataset during runtime execution.

The model follows the architectural principles adopted by AcCore:

* Metadata-Driven Architecture
* Runtime/Metadata Separation
* Compiler-Based Runtime Model
* Dataset-Oriented Execution
* Table Engine Reuse
* Expression Engine Reuse

The purpose of the execution model is to ensure:

* Deterministic report execution
* Runtime optimization
* Metadata independence
* Execution plan reuse
* Future scalability

---

# Execution Principles

Report execution is a multi-stage process.

Reports are not executed directly from metadata definitions.

Instead, report metadata is compiled into executable runtime structures.

```text id="m51rqs"
Report Metadata
        ↓
Validation
        ↓
Compilation
        ↓
Execution Plan
        ↓
Runtime Execution
        ↓
Report Dataset
```

This approach keeps metadata immutable and allows runtime optimizations.

---

# Execution Lifecycle

The report execution lifecycle consists of the following phases:

```text id="8b8dtx"
Report Metadata
        ↓
Validation
        ↓
Compilation
        ↓
Execution Planning
        ↓
Data Acquisition
        ↓
Dataset Processing
        ↓
Dataset Materialization
```

Each phase has a distinct responsibility.

---

# Validation Phase

## Purpose

Validation verifies that report metadata is internally consistent.

---

## Validation Scope

The validation phase verifies:

* Data Sources
* Parameters
* Filters
* Dimensions
* Measures
* Calculated Measures
* Expressions
* Hierarchies

Examples:

```text id="ib8p7q"
Amount - Cost
```

Valid.

```text id="mb55tr"
Amount - UnknownField
```

Invalid.

---

## Validation Result

```text id="91t8p8"
Validated Report Definition
```

Validation failures prevent report compilation.

---

# Compilation Phase

## Purpose

Compilation transforms metadata definitions into runtime structures.

---

## Compilation Responsibilities

Compilation creates:

* Compiled Data Sources
* Compiled Filters
* Compiled Dimensions
* Compiled Measures
* Compiled Expressions

Example:

```text id="b25fcj"
Customer
```

becomes:

```text id="hl1zt5"
CompiledDimension
```

---

## Compilation Result

```text id="l1n55d"
Compiled Report
```

Compiled reports are runtime-independent artifacts.

---

# Execution Planning Phase

## Purpose

Execution planning converts a compiled report into an executable plan.

---

## Execution Plan Structure

```text id="t3h6qa"
ReportExecutionPlan
```

The plan defines the sequence of dataset operations required to produce the report result.

---

## Execution Nodes

A plan may contain:

```text id="l7h7hv"
SourceNode
FilterNode
ProjectionNode
GroupNode
AggregateNode
CalculateNode
SortNode
```

Additional node types may be introduced in future versions.

---

## Execution Planning Result

```text id="s2r1un"
Report Execution Plan
```

Execution plans are runtime artifacts.

---

# Data Acquisition Phase

## Purpose

Acquire source data through the configured Data Source Provider.

---

## Provider Interaction

Example:

```text id="x55m3e"
InventoryBalanceSource
```

uses:

```text id="0q0f2s"
InventoryBalanceProvider
```

The provider retrieves the source dataset.

---

## Acquisition Result

```text id="y7xv0d"
Raw Dataset
```

No filtering, aggregation, or calculations occur during acquisition.

---

# Dataset Processing Pipeline

## Purpose

Transform the raw dataset into the final analytical dataset.

---

## Processing Sequence

```text id="6jlwmq"
Raw Dataset
      ↓
Filtering
      ↓
Projection
      ↓
Grouping
      ↓
Aggregation
      ↓
Calculated Measures
      ↓
Ordering
      ↓
Result Dataset
```

The processing pipeline materializes the Dataset Definition.

---

# Filtering Stage

Applies report filters and parameter constraints.

Examples:

```text id="6tvmds"
Date >= DateFrom
Date <= DateTo
Warehouse = WarehouseParam
```

The result is a filtered dataset.

---

# Projection Stage

Selects fields required by the report.

Example:

Source fields:

```text id="d7vzlx"
Date
Customer
Warehouse
Product
Quantity
Amount
Cost
```

Projection:

```text id="bnyh3e"
Customer
Product
Quantity
Amount
```

Unused fields are removed.

---

# Grouping Stage

Groups records according to configured dimensions.

Example:

```text id="j9fglh"
Customer
Month
```

Grouping creates analytical buckets used for aggregation.

---

# Aggregation Stage

Calculates base measures.

Supported core aggregations:

```text id="4g5q7j"
SUM
COUNT
MIN
MAX
AVG
```

Additional aggregations may be introduced by future extensions.

---

# Calculated Measure Stage

Calculates derived analytical measures.

Examples:

```text id="tqkp5k"
Profit = Amount - Cost
```

```text id="2k0mlo"
Margin = Profit / Amount * 100
```

Calculated measures are evaluated after aggregation.

---

# Ordering Stage

Applies dataset ordering rules.

Examples:

```text id="i0v7nh"
Amount DESC
```

```text id="yvxkwm"
Month ASC
```

Ordering affects dataset structure but does not alter analytical values.

---

# Dataset Materialization

## Purpose

Produce a platform-neutral analytical dataset.

The materialized dataset becomes the final output of report execution.

---

## Result

```text id="9hjsb6"
Report Dataset
```

The dataset is independent from presentation technologies.

---

# Table Engine Integration

## Purpose

Reuse the platform Table Engine for dataset processing.

---

## Architecture

```text id="e6cf6e"
Raw Dataset
      ↓
Table Engine
      ↓
Filtering
Projection
Grouping
Aggregation
      ↓
Result Dataset
```

The Reporting subsystem does not implement a separate analytical processing engine.

---

## Benefits

* Shared execution infrastructure
* Shared memory model
* Shared optimization logic
* Reduced implementation complexity

---

# Expression Engine Integration

## Purpose

Reuse the platform Expression Engine for calculated measures.

---

## Architecture

```text id="knaxfd"
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
* Shared optimization mechanisms
* Consistent calculation behavior

---

# Execution Result

The result of report execution is always a dataset.

```text id="lq1mop"
Report Execution
        ↓
Report Dataset
```

The execution result is never:

* UI controls
* Tables
* Charts
* Dashboards
* PDF documents
* Excel files

These concerns belong to Presentation Architecture.

---

# Caching Considerations

The execution model supports future caching layers.

Potential cache levels:

```text id="r4hm2o"
Compiled Report Cache

Execution Plan Cache

Dataset Cache
```

Caching strategies are implementation-specific and do not affect the execution model.

---

# Runtime Independence

Execution plans must remain independent from:

* UI technologies
* Export mechanisms
* Storage backends
* Database engines

This allows alternative runtime implementations without changing report metadata.

---

# ADR-009: Reports Are Compiled Before Execution

## Status

Accepted

## Decision

Reports are compiled into execution plans before runtime execution.

## Consequences

* Metadata remains immutable.
* Runtime execution becomes deterministic.
* Optimization becomes possible.
* Caching becomes possible.
* Multiple runtime implementations become possible.

---

# ADR-010: Report Execution Uses Execution Plans

## Status

Accepted

## Decision

Report Runtime executes compiled execution plans rather than report metadata.

## Consequences

* Runtime becomes independent from metadata structure.
* Execution optimizations become possible.
* Alternative runtimes become possible.

---

# ADR-011: Report Runtime Reuses Table Engine

## Status

Accepted

## Decision

Report Runtime delegates dataset processing to the platform Table Engine whenever possible.

## Consequences

* No duplicate analytical engine exists.
* Shared optimization infrastructure is reused.
* Shared memory management is reused.
* Shared execution model is reused.

---

# ADR-012: Report Execution Produces Dataset

## Status

Accepted

## Decision

The output of report execution is always a platform-neutral analytical dataset.

## Consequences

* UI independence.
* Export independence.
* Dashboard compatibility.
* API compatibility.
* Deterministic testing.
