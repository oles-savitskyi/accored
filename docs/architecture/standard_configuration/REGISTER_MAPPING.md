# REGISTER_MAPPING

## Purpose

This document defines the mapping between Standard Configuration business documents and platform registers.

The mapping follows the principles defined by:

* ADR-STD-003 — Continuous Cost Recognition
* ADR-STD-004 — Economic Objects Are Unified
* ADR-STD-006 — Direct And Related Expenses Are Allocation Modes
* ADR-STD-008 — Registers Store Quantities, Valuation Stores Costs
* ADR-STD-009 — Labor And Depreciation Follow The Same Resource Model As Inventory

---

# Architectural Principles

Operational registers store quantitative business facts.

Valuation and cost information are maintained separately by:

* Valuation Engine;
* Cost Totals Engine.

The Standard Configuration does not define a Cost Register.

---

# Register Landscape

The Standard Configuration defines five primary registers.

---

## Resource Register

### Purpose

Stores quantitative movements of economic objects.

### Dimensions

* Assortment
* Location (optional)
* Batch (optional)

### Resources

* Quantity

### Examples

* goods;
* materials;
* products;
* investments;
* inventory assets.

---

## Labor Register

### Purpose

Stores quantitative labor facts.

### Dimensions

* Employee
* Salary Type

### Resources

* Hours

### Examples

* worked hours;
* overtime hours;
* project hours.

---

## Asset Utilization Register

### Purpose

Stores quantitative asset utilization facts.

### Dimensions

* Asset

### Resources

* Operating Hours

### Examples

* machine-hours;
* equipment runtime;
* vehicle operating hours.

---

## Cash Register

### Purpose

Stores monetary movements.

### Dimensions

* Financial Account
* Currency

### Resources

* Amount

### Examples

* cash receipts;
* cash payments;
* bank transactions.

---

## Settlement Register

### Purpose

Stores obligations and receivables.

### Dimensions

* Business Partner
* Currency
* Source Document

### Resources

* Amount

### Examples

* accounts receivable;
* accounts payable;
* payroll liabilities;
* tax liabilities.

---

# Document Mapping

---

## Purchase

### Resource Register

Creates movements for:

* purchased goods;
* purchased materials;
* purchased assets.

### Settlement Register

Creates:
* supplier obligations;
* tax liabilities.

### Valuation Engine

Creates valuation facts for:

* acquisition cost;
* direct expenses;
* related expenses.

### Cash Register

No movements.

Bill To Pay is informational only.

---

## Sale

### Resource Register

Creates outbound quantity movements.

### Settlement Register

Creates:
* customer receivables;
* tax liabilities.

### Valuation Engine

Consumes inventory cost.

Processes:

* direct expenses;
* related expenses.

### Cash Register

No movements.

Bill To Pay is informational only.

---

## Production

### Resource Register

Creates:

* material consumption;
* production output.

### Valuation Engine

Creates production cost flows.

Processes:

* direct expenses;
* related expenses.

### Settlement Register

No movements.

### Cash Register

No movements.

---

## Salary

### Salary Booking

Labor Register:

* records labor quantities.

Valuation Engine:

* recognizes labor costs.

### Salary Sharing

Valuation Engine:

* allocates labor costs.

No labor quantity movement is created.

### Salary Taxation

Settlement Register:

* payroll liabilities;
* tax liabilities.

### Salary Rollout

No register movements.

Reporting only.

---

## Depreciation

### Depreciation Booking

Asset Utilization Register:

* records asset utilization quantities.

Valuation Engine:

* recognizes depreciation cost.

### Depreciation Sharing

Valuation Engine:

* allocates depreciation costs.

No utilization quantity movement is created.

---

## Cash

### Cash Register

Creates:

* cash inflows;
* cash outflows;
* bank inflows;
* bank outflows.

### Settlement Register

May settle:

* receivables;
* payables;
* payroll liabilities;
* tax liabilities.

---

## Unidoc

May create movements in:

* Resource Register;
* Labor Register;
* Asset Utilization Register;
* Cash Register;
* Settlement Register.

Usage should remain exceptional.

---

# Cost Allocation Flow

The Standard Configuration supports multi-stage cost allocation.

Typical allocation sequence:

Resource Quantity
→ Valuation Fact
→ Business Document
→ Document Line
→ Economic Object

---

# Direct Expenses

Direct expenses are assigned immediately to economic objects.

Examples:

* direct labor;
* direct depreciation;
* direct material usage.

---

# Related Expenses

Related expenses are allocated through one or more allocation stages.

Examples:

* shared labor;
* shared depreciation;
* shared operating expenses.

Allocation sequence:

Expense
→ Purchase / Sale / Production
→ Invoice / Product Line
→ Assortment Object

---

# Unallocated Costs

The preferred approach is operational allocation.

Expense
→ Economic Object

If allocation is not possible:

Expense
→ Period Result

This preserves compatibility with traditional accounting practices.

---

# Reference Architecture Status

This document defines the canonical register mapping model of the AcCore Standard Configuration.

It establishes the bridge between:

* Document Architecture;
* Register Architecture;
* Valuation Architecture;
* Cost Totals Architecture.

The model serves as the foundation for future workflow, reporting, and implementation design.
