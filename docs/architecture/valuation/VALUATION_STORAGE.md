# VALUATION_STORAGE.md

## Purpose

This document defines the storage model used by the AcCoreD Valuation Architecture.

Valuation storage is responsible for persisting valuation facts and materialized valuation results.

Valuation storage is built on top of the AcCoreD Storage Architecture and does not introduce an independent storage subsystem.

---

# Design Principles

Valuation storage is based on the following principles:

* valuation facts are stored explicitly;
* valuation history is auditable;
* valuation history is reproducible;
* materialized results are separated from source facts;
* cost balances are derived from cost movements;
* valuation storage follows the same architectural patterns as Register Storage.

---

# Storage Architecture Integration

Valuation Architecture uses the standard AcCoreD storage infrastructure.

Valuation storage is not a separate storage engine.

Valuation entities are persisted using the same storage mechanisms as:

* documents;
* registers;
* metadata objects;
* totals structures.

---

# Storage Layers

Valuation storage consists of two logical layers.

```text id="v3k8qm"
Valuation Facts
        ↓
Materialized Results
```

---

# Valuation Facts Layer

The valuation facts layer contains immutable valuation history.

Valuation facts represent the source of truth for valuation processing.

---

## Stored Fact Types

```text id="s2u8nh"
ValuationLayer

ValuationConsumption

ValuationAdjustment

ValuationAllocation

CostMovement
```

---

# Materialized Results Layer

The materialized results layer contains derived valuation state.

Materialized results may always be rebuilt from valuation facts.

---

## Stored Result Types

```text id="j1z6rc"
CostBalance
```

---

# Storage Structure

## valuation_layers

Stores valuation ownership facts.

### Contents

```text id="e5k2va"
ValuationLayer
```

### Characteristics

* persistent;
* auditable;
* immutable history.

---

## valuation_consumptions

Stores valuation consumption facts.

### Contents

```text id="h4x7yf"
ValuationConsumption
```

### Characteristics

* persistent;
* auditable;
* immutable history.

---

## valuation_adjustments

Stores valuation correction facts.

### Contents

```text id="b8w3ul"
ValuationAdjustment
```

### Characteristics

* persistent;
* auditable;
* immutable history.

---

## valuation_allocations

Stores adjustment allocation facts.

### Contents

```text id="y6c5rt"
ValuationAllocation
```

### Characteristics

* persistent;
* auditable;
* immutable history.

---

## cost_movements

Stores materialized valuation movement facts.

### Contents

```text id="w1r4co"
CostMovement
```

### Characteristics

* persistent;
* materialized;
* rebuildable.

---

## cost_balances

Stores materialized valuation totals.

### Contents

```text id="p9v3aj"
CostBalance
```

### Characteristics

* persistent;
* derived;
* rebuildable.

---

# Storage Flow

```text id="g5t1fn"
Valuation Facts
        ↓
Cost Movements
        ↓
Cost Totals Engine
        ↓
Cost Balances
```

---

# Cost Totals Engine

## Purpose

Maintain materialized valuation balances.

Cost Totals Engine consumes cost movements and produces cost balances.

---

## Responsibilities

* aggregate cost movements;
* maintain cost balances;
* rebuild balances;
* verify balance consistency.

---

## Scope

Cost Totals Engine operates only on:

```text id="v7n8up"
CostMovement

CostBalance
```

It does not process:

```text id="k2m4ye"
ValuationLayer

ValuationConsumption

ValuationAdjustment

ValuationAllocation
```

---

# Balance Maintenance

Cost balances are maintained incrementally.

```text id="a3f8zw"
Cost Movement
        ↓
Cost Totals Engine
        ↓
Cost Balance Update
```

---

# Rebuild Strategy

Cost balances shall be fully rebuildable.

Rebuild source:

```text id="x4d2gl"
CostMovement
```

Rebuild target:

```text id="h8m1ba"
CostBalance
```

---

# Reproducibility

Valuation storage shall support complete valuation reconstruction.

The following chain shall be reproducible:

```text id="n5v6qy"
Layer
        ↓
Consumption
        ↓
Adjustment
        ↓
Allocation
        ↓
Cost Movement
        ↓
Cost Balance
```

---

# Storage Identity

All valuation entities use the standard AcCoreD identity model.

```text id="c7q4np"
ULID
```

shall be used as the primary identifier where applicable.

---

# Dimensional Consistency

Valuation storage uses valuation keys.

According to VALUATION_DIMENSIONS.md:

```text id="z8w5mf"
Valuation Key
=
Quantity Key
```

Valuation storage does not introduce independent dimensional models.

---

# Indexing Guidelines

Valuation storage should support efficient access by:

```text id="d3p7ul"
valuation_key

layer_id

source_reference

valuation_date
```

Additional indexes may be introduced by implementation-specific optimizations.

---

# Archival Policy

Valuation facts represent audit history and shall be retained.

Materialized balances may be rebuilt and therefore do not represent the primary audit source.

---

# Architectural Invariants

1. Valuation storage uses the standard AcCoreD storage infrastructure.

2. Valuation facts are stored explicitly.

3. Valuation history is immutable and auditable.

4. Cost movements are materialized valuation facts.

5. Cost balances are materialized valuation totals.

6. Cost balances are maintained by Cost Totals Engine.

7. Cost balances are rebuildable from cost movements.

8. Valuation keys are identical to quantity keys.

9. All valuation results are reproducible.

10. Valuation storage does not introduce an independent storage engine.
