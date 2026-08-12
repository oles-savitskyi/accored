# VALUATION_RESOURCES.md

## Purpose

This document defines valuation resources used by the AcCoreD Valuation Architecture.

Valuation resources represent measurable economic value associated with quantity-carrying assets.

---

# Core Principle

Everything that has quantity shall have value.

Valuation Architecture maintains value using valuation resources.

---

# Valuation Resource

A valuation resource represents an economic measure maintained by the valuation subsystem.

Examples:

```text id="zj0w2o"
Money
Energy Cost
Carbon Cost
Labor Cost
Machine Cost
```

Valuation resources participate in:

* valuation layers;
* valuation adjustments;
* valuation allocations;
* cost movements;
* cost balances.

---

# Standard Valuation Resource

The standard valuation resource provided by the platform is:

```text id="dd47yk"
Money
```

Money shall be supported by every AcCoreD installation.

---

# Relationship To Money

Money is a specialized valuation resource.

```text id="9ayq2h"
Valuation Resource
        │
        ▼
      Money
```

All standard valuation processing operates on monetary values.

---

# Resource Identity

A valuation resource is identified by:

```text id="z3q4wa"
Resource Type
+
Measurement Unit
```

Examples:

```text id="qv39jv"
Money + USD

Money + EUR

Money + UAH

Carbon Cost + kg CO₂
```

---

# Resource Consistency

All valuation facts participating in the same valuation calculation shall use compatible valuation resources.

Incompatible valuation resources shall not be mixed within a single valuation result.

---

# Valuation Layers

Valuation layers carry valuation resources.

Example:

```text id="frp0z8"
Layer

Quantity = 100 pcs

Value = 500 USD
```

---

# Valuation Adjustments

Valuation adjustments modify valuation resources.

Example:

```text id="4x8j8m"
Transportation Cost

Adjustment = +50 USD
```

---

# Valuation Allocations

Valuation allocations distribute valuation resources.

Example:

```text id="14hpgp"
Adjustment

+50 USD

        ↓

Consumed Part = 10 USD

Remaining Part = 40 USD
```

---

# Cost Movements

Cost movements represent changes in valuation resources.

Example:

```text id="x8a1ep"
Sale

Cost Movement = -120 USD
```

---

# Cost Balances

Cost balances represent accumulated valuation resources.

Example:

```text id="x7zq4e"
Inventory

Cost Balance = 2,500 USD
```

---

# Extensibility

The platform may support additional valuation resources in the future.

Examples:

```text id="k3q6k9"
Carbon Cost

Energy Cost

Labor Cost

Machine Cost
```

Such resources shall use the same valuation architecture:

```text id="gjw29q"
Layer

Adjustment

Allocation

Movement

Balance
```

---

# Architectural Principles

1. Everything that has quantity shall have value.

2. Valuation resources represent economic value.

3. Money is the standard valuation resource.

4. Money is a specialization of valuation resource.

5. Valuation layers carry valuation resources.

6. Valuation adjustments modify valuation resources.

7. Valuation allocations distribute valuation resources.

8. Cost movements materialize valuation resource changes.

9. Cost balances materialize valuation resource balances.

10. Future valuation resources shall use the same valuation model.
