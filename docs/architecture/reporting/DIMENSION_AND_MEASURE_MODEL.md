# DIMENSION_AND_MEASURE_MODEL.md

## Purpose

This document defines the analytical model used by Reporting Architecture.

The model is based on explicit Dimensions and Measures that describe analytical meaning independently from report presentation, storage structures, or UI technologies.

The goal of the model is to provide a stable foundation for:

* Tabular reports
* Analytical reports
* Pivot reports
* Dashboards
* Charts
* Future OLAP capabilities
* Drill-down and roll-up navigation

The model follows the Metadata-Driven Architecture principles adopted by AcCore.

---

# Analytical Model

The analytical model consists of two fundamental concepts:

* Dimensions
* Measures

A report dataset is represented as a combination of analytical dimensions and analytical measures.

```text
Dimensions × Measures → Analytical Dataset
```

Dimensions define analytical axes.

Measures define analytical values.

---

# Dimension Definition

## Overview

A Dimension is an analytical axis used to classify, group, filter, and navigate business facts.

Dimensions answer the question:

> What are we analyzing by?

Examples:

* Customer
* Product
* Warehouse
* Period
* Region
* Department
* Project
* Manager

---

## Dimension Structure

A dimension is defined by metadata.

```text
ReportDimension
    id
    name
    source_field
    data_type
    hierarchy
```

### Properties

| Property     | Description                            |
| ------------ | -------------------------------------- |
| id           | Unique dimension identifier            |
| name         | Dimension name                         |
| source_field | Dataset field used as dimension source |
| data_type    | Dimension value type                   |
| hierarchy    | Optional analytical hierarchy          |

---

## Dimension Sources

Dimensions may originate from:

* Catalog references
* Document fields
* Register dimensions
* Cost dimensions
* Calculated dataset fields

Examples:

```text
Customer
Product
Warehouse
Manager
Period
```

---

# Dimension Hierarchies

## Purpose

Hierarchies define navigation paths inside dimensions.

They support:

* Drill-down
* Roll-up
* Aggregation navigation
* Future OLAP scenarios

---

## Time Hierarchy

Example:

```text
Year
 └─ Quarter
     └─ Month
         └─ Day
```

---

## Geographic Hierarchy

Example:

```text
Region
 └─ City
     └─ Customer
```

---

## Organizational Hierarchy

Example:

```text
Company
 └─ Department
     └─ Employee
```

---

## Hierarchy Definition

```text
DimensionHierarchy
    id
    name
    levels
```

A hierarchy may contain any number of levels.

Support for hierarchy navigation is implementation-dependent and may be introduced incrementally.

---

# Measure Definition

## Overview

A Measure is a numerical value used to quantify business facts.

Measures answer the question:

> What are we measuring?

Examples:

* Quantity
* Amount
* Cost
* Profit
* Margin
* Balance
* Turnover

---

## Measure Structure

```text
ReportMeasure
    id
    name
    expression
    aggregation
    format
```

### Properties

| Property    | Description                    |
| ----------- | ------------------------------ |
| id          | Unique measure identifier      |
| name        | Measure name                   |
| expression  | Measure calculation expression |
| aggregation | Aggregation function           |
| format      | Display format hint            |

---

# Aggregation Functions

The following aggregation functions are part of the core analytical model:

```text
SUM
COUNT
MIN
MAX
AVG
```

Additional aggregation functions may be introduced by future extensions.

---

# Base Measures

A Base Measure directly references a dataset field.

Example:

```text
Quantity
```

```text
expression = Quantity
aggregation = SUM
```

---

Example:

```text
Amount
```

```text
expression = Amount
aggregation = SUM
```

---

Base Measures do not require additional calculations.

---

# Calculated Measures

A Calculated Measure derives its value from one or more measures.

Example:

```text
Profit
```

```text
Amount - Cost
```

---

Example:

```text
Margin
```

```text
Profit / Amount * 100
```

---

Calculated Measures are evaluated after dataset extraction and aggregation.

---

# Expression Engine Integration

Calculated Measures are executed through the platform Expression Engine.

```text
Measure Expression
        ↓
Expression Engine
        ↓
Measure Value
```

This approach guarantees consistency between Reporting Architecture and the rest of the platform.

Benefits:

* Single expression language
* Shared optimization infrastructure
* Shared dependency tracking
* Shared validation logic
* No duplicate formula engine

---

# Semantic Types

Measures should use platform semantic types whenever possible.

Examples:

```text
Quantity
Money
Cost
Percent
Rate
```

Semantic types allow Presentation Layer to automatically apply:

* Currency formatting
* Percentage formatting
* Quantity formatting
* Localization rules

The reporting subsystem remains independent from concrete presentation technologies.

---

# Dimension/Measure Matrix

Any analytical report may be represented as a dimension/measure matrix.

Example:

```text
                    Measures

                Qty     Amount     Cost

Customer
Product
Warehouse
Month
```

Dimensions define analytical coordinates.

Measures define analytical values.

---

# Future OLAP Compatibility

The analytical model is intentionally designed to remain compatible with future OLAP-style functionality.

Potential future capabilities include:

* Pivot analysis
* Drill-down
* Roll-up
* Slice-and-dice
* Dashboard analytics
* KPI systems
* Interactive exploration

No changes to the core Reporting Architecture should be required to support these capabilities.

---

# ADR-006: Dimensions And Measures Are First-Class Metadata Objects

## Status

Accepted

## Decision

Dimensions and Measures are explicit metadata objects and are not inferred from report layout or presentation.

## Consequences

* Analytical semantics become part of metadata.
* Dashboards can reuse report definitions.
* Future OLAP capabilities become possible.
* Drill-down and pivot operations become metadata-driven.

---

# ADR-007: Dimensions May Define Hierarchies

## Status

Accepted

## Decision

Dimensions may expose analytical hierarchies.

## Consequences

* Drill-down becomes possible.
* Roll-up becomes possible.
* Hierarchical navigation becomes metadata-driven.
* Future analytical extensions require no architectural redesign.

---

# ADR-008: Measures Use Expression Engine

## Status

Accepted

## Decision

Calculated Measures are evaluated through the platform Expression Engine.

## Consequences

* No second formula engine exists.
* Report calculations remain consistent with the rest of the platform.
* Optimization and dependency tracking are reused.
* Reporting Architecture remains aligned with Runtime Architecture.
