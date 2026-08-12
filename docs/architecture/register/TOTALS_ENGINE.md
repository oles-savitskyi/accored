# Totals Engine

## Purpose

The Totals Engine maintains aggregated register state derived from movements.

---

## Responsibilities

* Maintain balance totals;
* Support balance queries;
* Support incremental updates;
* Support totals rebuild;
* Support adaptive totals strategy.

---

## Non-Responsibilities

The Totals Engine does not perform:

* Posting;
* Business logic;
* Valuation;
* Reporting.

---

## Aggregation Model

Movements
↓
Totals Buckets
↓
Balance Calculation

---

## Balance Model

Balances represent aggregated resource state for a specific dimension set and period bucket.

Balance Record:

* register_id
* bucket_period
* dimensions
* resources

---

## Storage Model

Totals are stored as aggregated period deltas.

Current balances are derived from totals buckets.

---

## Adaptive Totals Strategy

Supported granularities:

* Yearly
* Quarterly
* Monthly
* Daily

The Totals Engine may adapt granularity according to workload and data volume.

---

## Maintenance Strategy

Hybrid Strategy:

* Incremental Maintenance
* Rebuild Support

Totals rebuild is a normal maintenance operation.
