# VALUATION_LIFECYCLE.md

## Purpose

This document describes the lifecycle of valuation processing within AcCoreD.

The valuation subsystem transforms quantity facts into cost facts and maintains inventory valuation consistency.

Valuation processing is deterministic and based on explicit valuation facts.

---

# Lifecycle Overview

```text
Document
    ↓
Posting
    ↓
Register Movements
    ↓
Valuation Trigger
    ↓
Layer Processing
    ↓
Consumption Processing
    ↓
Adjustment Processing
    ↓
Allocation Processing
    ↓
Cost Movement Processing
    ↓
Cost Balance Processing
```

---

# Lifecycle Principles

## Valuation Follows Posting

Valuation processing begins only after successful posting.

Registers remain the source of quantity facts.

Valuation never creates or modifies register movements.

---

## Valuation Produces Cost Facts

Valuation does not store accounting results.

Valuation produces:

* valuation layers;
* valuation consumptions;
* valuation adjustments;
* valuation allocations;
* cost movements;
* cost balances.

---

## Deterministic Processing

Identical inputs shall always produce identical valuation results.

Valuation processing shall not depend on user interface state, session state, or execution order.

---

# Stage 1. Valuation Trigger

## Purpose

Start valuation processing.

## Input

Register movements produced by Posting Engine.

## Output

Valuation processing request.

## Sources

Typical trigger sources:

* document posting;
* delayed cost fact;
* valuation rebuild;
* revaluation operation.

---

# Stage 2. Layer Processing

## Purpose

Create valuation layers representing valuation ownership.

## Input

Register movements affecting inventory acquisition.

Examples:

* purchase receipt;
* production receipt;
* opening balance;
* inventory gain.

## Output

ValuationLayer records.

## Result

```text
Inventory Receipt
        ↓
Valuation Layer
```

---

# Stage 3. Consumption Processing

## Purpose

Determine how inventory consumption uses valuation layers.

## Input

Register movements affecting inventory reduction.

Examples:

* sales;
* transfers;
* write-offs;
* production consumption.

## Processing

Valuation Method selects source layers.

Examples:

* FIFO;
* Average Cost;
* Specific Identification.

## Output

ValuationConsumption records.

## Result

```text
Issue Movement
        ↓
Valuation Method
        ↓
Valuation Consumptions
```

---

# Stage 4. Adjustment Processing

## Purpose

Register valuation corrections.

## Input

Cost-affecting facts.

Examples:

* transportation costs;
* customs duties;
* supplier corrections;
* production allocations;
* revaluations.

## Output

ValuationAdjustment records.

## Result

```text
Cost Fact
        ↓
Valuation Adjustment
```

---

# Stage 5. Allocation Processing

## Purpose

Distribute adjustment values across layer history.

## Input

Valuation adjustments.

Valuation consumptions.

## Processing

Adjustment values are allocated proportionally according to layer consumption history.

## Output

ValuationAllocation records.

## Result

```text
Adjustment
        ↓
Allocations
        ↓
Consumed Part
Remaining Part
```

---

# Stage 6. Cost Movement Processing

## Purpose

Generate materialized cost facts.

## Input

Valuation consumptions.

Valuation allocations.

## Output

CostMovement records.

## Result

```text
Consumption
+
Allocations
        ↓
Cost Movement
```

---

# Stage 7. Cost Balance Processing

## Purpose

Maintain materialized inventory valuation balances.

## Input

Cost movements.

## Output

CostBalance records.

## Result

```text
Cost Movements
        ↓
Cost Balances
```

---

# Delayed Cost Facts

The valuation subsystem supports delayed cost information.

Missing or incorrect cost information does not require special valuation states.

All cost corrections are represented through valuation adjustments.

Example:

```text
Receipt
Base Cost = 0

Supplier Invoice
Adjustment = +100
```

The same processing pipeline applies regardless of when cost information becomes available.

---

# Revaluation Lifecycle

Revaluation does not modify existing valuation layers.

Revaluation creates valuation adjustments.

Adjustments generate allocations.

Allocations generate cost movements.

Cost balances are updated accordingly.

---

# Lifecycle Invariants

The following rules shall always hold:

1. Quantity accounting is independent from valuation.

2. Valuation layers are immutable.

3. Cost corrections are represented through adjustments.

4. Consumption is represented through explicit valuation facts.

5. Allocations are explicit valuation facts.

6. Cost movements are materialized valuation facts.

7. Cost balances are materialized valuation facts.

8. Effective Cost = Base Cost + Σ Adjustments.

9. Valuation methods produce consumption facts.

10. Valuation processing follows posting.
