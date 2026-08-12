# VALUATION_ENGINE.md

## Purpose

Valuation Engine is the central execution component of Valuation Architecture.

The engine transforms quantity facts and cost facts into valuation facts and maintains valuation consistency across the system.

Valuation Engine does not perform accounting, reporting, or document processing.

---

# Responsibilities

Valuation Engine is responsible for:

* valuation layer management;
* valuation consumption generation;
* valuation adjustment processing;
* valuation allocation processing;
* cost movement generation;
* cost balance maintenance;
* valuation consistency maintenance.

---

# High-Level Architecture

```text id="p8g1kz"
Triggers
    ↓

Valuation Engine
    ↓

Pipeline Orchestrator

    ├─ Provenance Pipeline
    ├─ Results Pipeline
    └─ Maintenance Operations
```

---

# Provenance Pipeline

## Purpose

Maintain valuation provenance.

## Responsibility

Track cost ownership and cost history.

## Components

### Layer Processor

Produces:

```text id="gmb05d"
ValuationLayer
```

### Consumption Processor

Produces:

```text id="jptg0z"
ValuationConsumption
```

### Adjustment Processor

Produces:

```text id="lhotxu"
ValuationAdjustment
```

### Allocation Processor

Produces:

```text id="t2bw6h"
ValuationAllocation
```

---

# Results Pipeline

## Purpose

Produce materialized valuation results.

## Components

### Cost Movement Processor

Produces:

```text id="56f2e4"
CostMovement
```

### Cost Balance Processor

Produces:

```text id="8jlwm8"
CostBalance
```

---

# Maintenance Operations

## Purpose

Maintain valuation consistency.

## Operations

### Rebuild

Reconstruct valuation facts from source facts.

### Recalculate

Re-run valuation processing.

### Verification

Validate valuation consistency.

### Repair

Restore valuation consistency after failures.

```

---

# Lifecycle Integration

Valuation Engine operates according to VALUATION_LIFECYCLE.md.

All processing stages are deterministic.

All valuation facts are reproducible from source facts.

---

# Architectural Principles

1. Valuation follows posting.

2. Quantity accounting is independent from valuation.

3. Valuation layers are immutable.

4. Cost corrections are represented as adjustments.

5. Valuation methods produce consumption facts.

6. Cost movements are materialized valuation facts.

7. Cost balances are materialized valuation facts.

8. Valuation processing uses pipeline architecture.
```
