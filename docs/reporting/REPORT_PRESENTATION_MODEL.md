# REPORT_PRESENTATION_MODEL.md

## Purpose

This document defines the presentation architecture of the Reporting subsystem.

The Presentation Layer is responsible for transforming analytical datasets into user-consumable representations.

Presentation is intentionally separated from report execution.

Report execution produces datasets.

Presentation consumes datasets.

This separation ensures UI independence, renderer independence, and long-term architectural flexibility.

The presentation model follows the platform principles:

* Dataset-Oriented Reporting
* Runtime/Metadata Separation
* Renderer Independence
* Semantic Type Awareness
* Reusable Presentation Definitions

---

# Presentation Principles

The Reporting subsystem separates data generation from data presentation.

```text
Report Metadata
        ↓
Report Runtime
        ↓
Dataset
        ↓
Presentation Layer
        ↓
User Output
```

Report execution and presentation are independent architectural concerns.

---

# Dataset And Presentation Separation

A dataset represents analytical data.

A presentation represents how analytical data is displayed.

Examples:

Dataset:

```text
Customer | Amount | Cost | Profit
```

Presentation:

```text
Customer | Profit | Amount
```

The presentation may:

* Reorder columns
* Hide columns
* Apply formatting
* Define layouts

The presentation must not modify analytical results.

---

# Presentation Architecture

The Presentation Layer consists of two major components:

```text
Presentation Model
        ↓
Presentation Renderer
```

The Presentation Model defines how information should be displayed.

The Presentation Renderer transforms presentation definitions into technology-specific outputs.

---

# Presentation Model

## Purpose

Describe the visual structure of a report independently from rendering technologies.

---

## Structure

```text
ReportPresentation

    id
    name
    type
    layout
    formatting
```

### Properties

| Property   | Description                    |
| ---------- | ------------------------------ |
| id         | Unique presentation identifier |
| name       | Presentation name              |
| type       | Presentation type              |
| layout     | Layout definition              |
| formatting | Formatting rules               |

---

# Presentation Types

The platform supports multiple presentation categories.

```text
Tabular
Pivot
Chart
Dashboard
Export
```

Additional presentation types may be introduced in future versions.

---

# Presentation Renderer

## Purpose

Transform presentation definitions into concrete outputs.

---

## Renderer Responsibilities

* Render datasets
* Apply formatting
* Apply layouts
* Support user interaction
* Generate export outputs

Renderers must not modify analytical data.

---

## Renderer Independence

Presentation definitions are reusable across renderers.

Example:

```text
Report Dataset
        ↓
Presentation Model
        ↓
Qt Renderer

Report Dataset
        ↓
Presentation Model
        ↓
Web Renderer

Report Dataset
        ↓
Presentation Model
        ↓
Excel Renderer
```

The same presentation definition may be rendered by multiple technologies.

---

# Tabular Presentation

## Purpose

Display datasets as structured tables.

---

## Characteristics

* Rows and columns
* Sorting
* Column visibility
* Totals
* Grouping
* Formatting

---

## Example

```text
Customer | Amount | Cost | Profit
```

Tabular presentation is expected to be the most common report presentation type.

---

# Pivot Presentation

## Purpose

Display analytical datasets through dimension/measure matrices.

---

## Characteristics

* Dimension-based grouping
* Measure aggregation
* Cross-tab analysis
* Multi-dimensional navigation

---

## Example

```text
                    Amount

Customer
Product
Month
```

Pivot presentation reuses the Dimension and Measure model.

---

# Chart Presentation

## Purpose

Display analytical datasets as graphical visualizations.

---

## Supported Concepts

* Categories
* Series
* Values
* Time axes
* Aggregated metrics

---

## Examples

```text
Month → Amount
```

```text
Warehouse → Cost
```

Chart rendering remains independent from report execution.

---

# Dashboard Presentation

## Purpose

Combine multiple analytical views into a single presentation.

---

## Dashboard Components

Possible components include:

* KPI widgets
* Charts
* Tables
* Pivot views
* Summary cards

---

## Architecture

```text
Dashboard
    ├── Dataset View
    ├── Chart View
    ├── KPI View
    └── Pivot View
```

Each component consumes datasets.

---

# Export Presentation

## Purpose

Generate portable report outputs.

---

## Supported Export Targets

Examples:

```text
Excel
PDF
CSV
JSON
```

Export generation is treated as a specialized rendering process.

---

# Layout Model

## Purpose

Define structural organization of report content.

---

## Possible Layout Elements

* Column order
* Column visibility
* Group sections
* Totals sections
* Header areas
* Footer areas

Layouts affect presentation only.

Layouts do not affect analytical results.

---

# Formatting Model

## Purpose

Define visual representation of values.

---

## Formatting Responsibilities

* Number formatting
* Currency formatting
* Percentage formatting
* Date formatting
* Localization

---

## Example

Dataset value:

```text
12345.67
```

Presentation result:

```text
12,345.67 USD
```

or

```text
12 345,67 EUR
```

Formatting never changes the underlying value.

---

# Semantic Type Integration

Presentation formatting should leverage platform semantic types.

Examples:

```text
Money
```

Automatically enables:

```text
Currency Formatting
```

---

```text
Percent
```

Automatically enables:

```text
Percentage Formatting
```

---

```text
Quantity
```

Automatically enables:

```text
Quantity Formatting
```

Semantic types improve consistency across all renderers.

---

# Interactive Capabilities

## Purpose

Support user interaction without violating runtime boundaries.

---

## Supported Capabilities

Examples:

```text
Sorting
Filtering
Drill Down
Expand
Collapse
```

---

## Interaction Model

```text
User Action
        ↓
Presentation Layer
        ↓
Runtime Request
        ↓
Dataset Refresh
```

Presentation does not execute analytical calculations directly.

Runtime remains responsible for dataset generation.

---

# Presentation Independence

The Presentation Layer must remain independent from:

* Storage Architecture
* Register Architecture
* Valuation Architecture
* Database technologies
* Runtime implementation details

Presentation operates exclusively on datasets.

---

# Runtime Independence

The Reporting Runtime must not depend on:

* Qt Presentation
* Web Presentation
* Mobile Presentation
* Excel Rendering
* PDF Rendering

Likewise, Presentation must not depend on Runtime internals.

The dataset forms the architectural boundary.

---

# ADR-017: Dataset And Presentation Are Independent

## Status

Accepted

## Decision

Report execution produces datasets.

Presentation consumes datasets.

Neither side depends on the implementation details of the other.

## Consequences

* Multiple presentation technologies become possible.
* Runtime remains UI-independent.
* Export mechanisms remain independent.
* Dashboards can reuse report datasets.
* APIs can reuse report datasets.

---

# ADR-018: Presentation Model Is Renderer Independent

## Status

Accepted

## Decision

Presentation metadata is independent from rendering technologies.

## Consequences

* Multiple renderers may reuse the same presentation definition.
* UI technologies become replaceable.
* Export mechanisms remain consistent.
* Future presentation technologies require no metadata redesign.

---

# Architectural Summary

The complete reporting flow is:

```text
Report Metadata
        ↓
Report Runtime
        ↓
Dataset
        ↓
Presentation Model
        ↓
Renderer
        ↓
Output
```

This architecture establishes a strict separation between:

* Data generation
* Data presentation

and allows the Reporting subsystem to evolve independently from presentation technologies.
