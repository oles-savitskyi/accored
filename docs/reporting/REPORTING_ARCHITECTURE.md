# Reporting Architecture

Reporting Architecture is a subsystem responsible for transforming business objects, register facts, register totals, valuation facts, and cost balances into analytical datasets. The subsystem does not create accounting facts, does not perform posting, does not execute valuation logic, and does not own business state. Its responsibility is limited to data extraction, aggregation, dimensional analysis, and report dataset construction. Report execution produces a platform-neutral dataset that can be consumed by UI, export, or integration layers.

---

## Phase 9 implementation reconciliation

The Phase 9 implementation establishes the currently supported Reporting subset: immutable report values/schema/rows/datasets, logical data-source contracts and registry, report definitions with filters/dimensions/measures, validation, compilation, typed execution plans, and deterministic runtime filter/group/aggregate execution.

The current runtime does not implement every conceptual component described in this document. In particular, Report Manager, dataset cache, generic expression/calculated-measure execution, projection/sort execution nodes, presentation, export, persistence, scheduling, and optimization remain future/deferred capabilities unless separately implemented elsewhere. These references are architectural direction rather than claims about the current executable API.

The first Standard vertical is the Inventory Balance report, backed by the Standard-owned `inventory.balance` logical source.
