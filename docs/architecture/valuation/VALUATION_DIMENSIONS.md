# VALUATION_DIMENSIONS.md

## Purpose

This document defines valuation dimensions used by the AcCoreD Valuation Architecture.

---

# Core Principle

Everything that has quantity shall have value.

Valuation is maintained for the same economic objects that participate in quantity accounting.

---

# Valuation Dimension Model

Valuation Architecture does not introduce independent valuation dimensions.

Valuation dimensions are inherited from quantity accounting.

```text
Valuation Dimensions
=
Quantity Dimensions
```

---

# Valuation Key

The valuation key is identical to the quantity key.

```text
Valuation Key
=
Quantity Key
```

---

# Examples

## Example 1

Quantity dimensions:

```text
Item
Warehouse
```

Valuation dimensions:

```text
Item
Warehouse
```

---

## Example 2

Quantity dimensions:

```text
Item
Warehouse
Batch
```

Valuation dimensions:

```text
Item
Warehouse
Batch
```

---

## Example 3

Quantity dimensions:

```text
Item
Warehouse
Serial Number
```

Valuation dimensions:

```text
Item
Warehouse
Serial Number
```

---

# Layer Ownership

Valuation layers belong to valuation keys.

A valuation layer cannot span multiple valuation keys.

---

# Cost Balances

Cost balances are maintained for valuation keys.

The granularity of valuation balances is identical to the granularity of quantity balances.

---

# Architectural Consequences

## Positive

* No separate valuation dimension model.
* No valuation-specific keys.
* Full consistency between quantity and cost accounting.
* Simplified reconciliation.
* Simplified configuration model.

## Neutral

Changes in quantity dimensions automatically affect valuation dimensions.

---

# Architectural Invariants

1. Everything that has quantity shall have value.

2. Valuation dimensions are inherited from quantity accounting.

3. Valuation keys are identical to quantity keys.

4. Valuation layers belong to valuation keys.

5. Cost balances are maintained by valuation keys.

6. Quantity and cost use identical dimensional granularity.
