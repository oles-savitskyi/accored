# Register Query Model

## Purpose

The Register Query Model defines how register data is accessed by platform consumers.

---

## Query Independence

Consumers query register services.

Consumers do not access totals storage directly.

Storage implementation details remain hidden.

---

## Query Types

### Movement Query

Answers:

What happened?

Source:

Movement Store.

---

### Balance Query

Answers:

What is the current or historical state?

Source:

Totals Engine.

---

### Turnover Query

Answers:

What changed during a period?

Source:

Movements or materialized turnover aggregates.

---

## Temporal Queries

Register state is queried as of a specified moment in time.

Balances and information facts support temporal access.

---

## Aggregation Model

Queries aggregate resources grouped by dimensions.

Dimensions define grouping context.

---

## Architectural Principle

Register queries remain independent from:

* Storage layout;
* Index strategy;
* Totals granularity;
* Materialization strategy.
