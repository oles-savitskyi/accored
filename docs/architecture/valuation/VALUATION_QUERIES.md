# VALUATION_QUERIES.md

## Purpose

This document defines the query model used by the AcCoreD Valuation Architecture.

Valuation queries provide access to current valuation state, valuation history, valuation provenance, and valuation analysis.

---

# Query Model

Valuation Architecture supports two categories of queries:

```text id="q1r4tp"
Operational Queries

Audit Queries
```

---

# Operational Queries

## Purpose

Provide efficient access to current valuation information.

Operational queries use materialized valuation results.

---

## Data Sources

```text id="j8c5az"
CostBalance

CostMovement
```

---

## Typical Queries

### Current Cost

Returns current valuation balance.

Example:

```text id="x5u8lb"
Current Cost
(Item A, Warehouse B)
```

---

### Cost Turnover

Returns valuation movement history.

Example:

```text id="f7m2cv"
Cost Turnover
(January 2026)
```

---

### Balance Snapshot

Returns valuation state at a specified point in time.

Example:

```text id="t4k9pq"
Cost Balance
(2026-01-31)
```

---

# Audit Queries

## Purpose

Provide complete valuation traceability.

Audit queries use valuation facts.

---

## Data Sources

```text id="w6r2ny"
ValuationLayer

ValuationConsumption

ValuationAdjustment

ValuationAllocation
```

---

## Typical Queries

### Cost Provenance

Explains where cost originated.

Example:

```text id="u8v4ex"
Why does Sale #17 have Cost = 120 USD?
```

---

### Layer Analysis

Returns layer structure.

Example:

```text id="k5z3rw"
Which layers form the current inventory value?
```

---

### Adjustment Analysis

Returns cost corrections and allocations.

Example:

```text id="s7m1fd"
Which adjustments affected Layer L1?
```

---

### Consumption Analysis

Returns layer consumption history.

Example:

```text id="n2p8ka"
Which documents consumed Layer L1?
```

---

# Query Paths

## Operational Path

```text id="y4t6cz"
CostBalance
        ↑
CostMovement
```

Optimized for speed.

---

## Audit Path

```text id="g8w3lt"
Layer
    ↓
Consumption
    ↓
Adjustment
    ↓
Allocation
```

Optimized for traceability.

---

# Provenance Queries

Valuation Architecture shall support complete cost provenance.

The following chain shall be navigable:

```text id="m9r5vd"
Layer
        ↓
Consumption
        ↓
Adjustment
        ↓
Allocation
        ↓
CostMovement
```

---

# Dimensional Queries

Queries operate using valuation keys.

According to VALUATION_DIMENSIONS.md:

```text id="h3x8pw"
Valuation Key
=
Quantity Key
```

---

# Historical Queries

Valuation Architecture shall support historical reconstruction.

Historical queries may operate on:

* layers;
* consumptions;
* adjustments;
* allocations;
* cost movements;
* cost balances.

---

# Query Consistency

Operational and audit queries shall produce consistent results.

Materialized valuation results shall be derived from valuation facts.

---

# Architectural Principles

1. Operational queries use materialized results.

2. Audit queries use valuation facts.

3. Cost provenance shall be fully traceable.

4. Historical valuation state shall be reconstructable.

5. Valuation queries operate on valuation keys.

6. Materialized results shall remain consistent with valuation facts.
