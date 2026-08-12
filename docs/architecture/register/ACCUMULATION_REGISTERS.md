# Accumulation Registers

## Purpose

Accumulation Registers store accounting movements representing business facts.

Accumulation Registers are the source of balances and turnovers.

---

## Aggregation Principle

Movements are primary data.

Balances and turnovers are derived data.

Accumulation Registers do not store balances as primary facts.

---

## Movement Model

Accumulation Movement

System Fields:

* id
* register_id
* period
* movement_type

Business Fields:

* dimensions
* resources
* attributes

---

## Movement Types

Supported movement types:

* INCOME
* EXPENSE

Movement direction is determined exclusively by movement_type.

Resources are always positive.

---

## Dimensions

Dimensions define aggregation context.

Dimensions determine how resources are grouped.

Dimensions participate in totals generation.

---

## Resources

Resources represent measurable accounting facts.

Resources must be numeric.

Examples:

* Quantity
* Weight
* Volume
* Hours

---

## Attributes

Attributes describe movements but do not participate in aggregation.

---

## Architectural Principle

Totals Engine aggregates resources grouped by dimensions.

Attributes do not participate in aggregation.
