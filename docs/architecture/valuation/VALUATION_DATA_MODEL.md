# VALUATION_DATA_MODEL.md

## Purpose

This document defines the core data model of the AcCoreD Valuation Architecture.

The valuation model is responsible for representing cost ownership, cost consumption, cost adjustments, cost allocation, and materialized valuation results.

The model is independent from quantity accounting and operates on valuation facts produced by the Valuation Engine.

---

# Design Principles

The valuation data model is based on the following principles:

* Quantity accounting is independent from valuation.
* Cost ownership is represented through valuation layers.
* Consumption is represented through explicit valuation facts.
* Cost corrections are represented through valuation adjustments.
* Adjustment distribution is represented through explicit allocations.
* Cost movements are materialized valuation facts.
* Cost balances are materialized valuation facts.
* All valuation results are reproducible from valuation facts.

---

# Entity Overview

```text
ValuationLayer
        │
        ├─────────────┐
        │             │
        ▼             ▼

ValuationConsumption   ValuationAdjustment
        │             │
        │             ▼
        │      ValuationAllocation
        │             │
        └──────┬──────┘
               │
               ▼

         CostMovement
               │
               ▼

          CostBalance
```

---

# ValuationLayer

## Purpose

Represents ownership of quantity and base cost.

ValuationLayer is the primary cost carrier within the valuation subsystem.

---

## Responsibilities

* represent valuation ownership;
* store acquired quantity;
* store remaining quantity;
* store base cost;
* preserve valuation provenance.

---

## Conceptual Structure

```text
ValuationLayer
├─ id
├─ asset_key
├─ quantity_total
├─ quantity_remaining
├─ base_cost
├─ source_reference
├─ created_at
```

---

## Relationships

```text
ValuationLayer
    ├─ 1:N ValuationConsumption
    └─ 1:N ValuationAdjustment
```

---

## Invariants

```text
quantity_total > 0

quantity_remaining >= 0

quantity_remaining <= quantity_total
```

---

# ValuationConsumption

## Purpose

Represents explicit consumption of valuation layers.

ValuationConsumption is produced by valuation methods.

---

## Responsibilities

* represent layer consumption;
* preserve consumption history;
* connect economic events with valuation ownership.

---

## Conceptual Structure

```text
ValuationConsumption
├─ id
├─ layer_id
├─ source_reference
├─ quantity
├─ base_cost
├─ consumed_at
├─ created_at
```

---

## Relationships

```text
ValuationConsumption
    └─ N:1 ValuationLayer
```

---

## Invariants

```text
quantity > 0
```

---

# ValuationAdjustment

## Purpose

Represents any change affecting layer valuation.

All valuation corrections are represented through adjustments.

---

## Responsibilities

* represent cost corrections;
* represent delayed costs;
* represent revaluations;
* preserve adjustment history.

---

## Conceptual Structure

```text
ValuationAdjustment
├─ id
├─ layer_id
├─ amount
├─ adjustment_type
├─ source_reference
├─ created_at
```

---

## Relationships

```text
ValuationAdjustment
    ├─ N:1 ValuationLayer
    └─ 1:N ValuationAllocation
```

---

# ValuationAllocation

## Purpose

Represents explicit distribution of valuation adjustments.

---

## Responsibilities

* distribute adjustment value;
* preserve allocation history;
* connect adjustments with their targets.

---

## Conceptual Structure

```text
ValuationAllocation
├─ id
├─ adjustment_id
├─ target_type
├─ target_id
├─ amount
├─ created_at
```

---

## Target Types

Supported targets:

```text
CONSUMPTION

REMAINING_LAYER
```

---

## Relationships

```text
ValuationAllocation
    └─ N:1 ValuationAdjustment
```

---

# CostMovement

## Purpose

Represents a materialized valuation result.

CostMovement describes a change in cost value.

---

## Responsibilities

* represent cost movement;
* provide auditable valuation history;
* serve as source for cost balances.

---

## Conceptual Structure

```text
CostMovement
├─ id
├─ asset_key
├─ amount
├─ movement_type
├─ source_reference
├─ valuation_date
├─ created_at
```

---

## Sources

Cost movements may originate from:

* valuation consumptions;
* valuation allocations;
* revaluation operations.

---

# CostBalance

## Purpose

Represents materialized valuation balances.

CostBalance provides efficient access to current inventory valuation.

---

## Responsibilities

* represent current cost value;
* support valuation reporting;
* support valuation queries.

---

## Conceptual Structure

```text
CostBalance
├─ asset_key
├─ balance_amount
├─ calculated_at
```

---

# Core Relationships

```text
ValuationLayer
    ├─ ValuationConsumption
    └─ ValuationAdjustment

ValuationAdjustment
    └─ ValuationAllocation

ValuationConsumption
    └─ CostMovement

ValuationAllocation
    └─ CostMovement

CostMovement
    └─ CostBalance
```

---

# Effective Cost Model

Effective layer valuation is defined as:

```text
Effective Cost =
Base Cost +
Σ Valuation Adjustments
```

No special valuation states exist.

Missing cost information, delayed cost information, and corrected cost information are represented through the same adjustment mechanism.

---

# Materialized Facts

The following entities are materialized valuation artifacts:

```text
CostMovement

CostBalance
```

These entities are maintained by the Valuation Engine.

---

# Immutable Facts

The following entities represent immutable valuation history:

```text
ValuationLayer

ValuationConsumption

ValuationAdjustment

ValuationAllocation
```

Valuation history must remain auditable and reproducible.

---

# Architectural Invariants

1. Quantity accounting is independent from valuation.

2. Valuation layers are the primary carriers of cost ownership.

3. Consumption is represented through explicit valuation facts.

4. All cost corrections are represented through adjustments.

5. Adjustment distribution is represented through allocations.

6. Cost movements are materialized valuation facts.

7. Cost balances are materialized valuation facts.

8. Valuation methods produce consumption facts.

9. Effective Cost = Base Cost + Σ Adjustments.

10. All valuation results are reproducible from valuation facts.
