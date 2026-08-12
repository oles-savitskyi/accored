# DOCUMENT_ARCHITECTURE

## Purpose

This document defines the document architecture of the AcCore Standard Configuration.

Documents represent business operations, cost recognition activities, planning information, and accounting adjustments.

The architecture follows the principles defined by:

* ADR-STD-001 — SMB-Oriented Standard Configuration;
* ADR-STD-002 — Process-Oriented User Experience;
* ADR-STD-003 — Continuous Cost Recognition;
* ADR-STD-004 — Economic Objects Are Unified;
* ADR-STD-005 — Business Operations Are Consolidated Into Universal Operational Documents;
* ADR-STD-006 — Direct And Related Expenses Are Allocation Modes;
* ADR-STD-007 — Business Facts And Business Intentions Are Separated.

---

# Document Categories

The Standard Configuration defines four document categories:

* Operational Documents;
* Cost Recognition Documents;
* Reference Documents;
* Generic Documents.

---

# Operational Documents

Operational documents capture primary business activities.

---

## Purchase

### Purpose

Records purchasing operations.

### Structure

#### Requisites

Common document attributes.

#### Invoice

Purchased economic objects.

#### Related Expenses

Expenses requiring allocation.

#### Return Outwards

Supplier return operations.

#### Bill To Pay

Planned payment information.

Bill To Pay represents a business intention and never creates register movements.

### Responsibilities

* purchasing;
* inventory acquisition;
* supplier interaction;
* purchase cost formation.

---

## Sale

### Purpose

Records sales operations.

### Structure

#### Requisites

Common document attributes.

#### Invoice

Sold economic objects.

#### Related Expenses

Expenses requiring allocation.

#### Return Inwards

Customer return operations.

#### Bill To Pay

Planned customer payment information.

Bill To Pay represents a business intention and never creates register movements.

### Responsibilities

* sales operations;
* customer interaction;
* revenue generation;
* sales cost formation.

---

## Production

### Purpose

Records production activities.

### Structure

#### Requisites

Common document attributes.

#### Product List

Produced economic objects.

#### Direct Expenses

Expenses directly assigned to produced objects.

#### Related Expenses

Expenses requiring allocation.

### Responsibilities

* manufacturing operations;
* production costing;
* inventory creation;
* cost accumulation.

---

## Cash

### Purpose

Records all cash and banking operations.

### Structure

#### Requisites

Common document attributes.

#### Operations

Cash and banking transactions.

### Responsibilities

* cash receipts;
* cash payments;
* bank transactions;
* employee advances;
* financial settlements.

Cash is the only operational document that records payment facts.

---

# Cost Recognition Documents

Cost recognition documents implement the Continuous Cost Recognition principle.

---

## Salary

### Purpose

Recognizes, distributes, and settles labor costs.

### Structure

#### Salary Booking

Records labor cost recognition.

May include employer payroll obligations.

#### Salary Sharing

Distributes labor costs among business documents.

Allocation targets may include:

* Purchase;
* Sale;
* Production.

Allocated amounts may subsequently be distributed to economic objects within document lines.

#### Salary Taxation

Calculates:

* payroll taxes;
* employee deductions;
* statutory withholdings.

#### Salary Rollout

Consolidated payroll statement.

Salary Rollout serves reporting and reconciliation purposes and does not create register movements.

### Responsibilities

* labor cost recognition;
* labor cost allocation;
* payroll taxation;
* payroll settlement support.

---

## Depreciation

### Purpose

Recognizes and distributes asset consumption costs.

### Structure

#### Depreciation Booking

Records depreciation cost recognition.

#### Depreciation Sharing

Distributes depreciation costs among business documents and economic objects.

### Responsibilities

* depreciation recognition;
* depreciation allocation;
* production costing support;
* operational cost visibility.

---

# Reference Documents

Reference documents maintain time-dependent reference information.

---

## Currency Rate History

Maintains exchange rates.

Used by:

* purchasing;
* sales;
* valuation;
* reporting.

---

## Tax Rate History

Maintains tax rates.

Used by:

* payroll;
* taxation;
* reporting;
* compliance.

---

## Depreciation Rate Plan

Maintains planned depreciation rates.

Typically includes:

* Asset;
* Planned Hourly Cost;
* Effective Date.

Used by Depreciation Booking.

---

# Generic Documents

---

## Unidoc

### Purpose

Provides a universal document for operations not covered by specialized business documents.

### Responsibilities

* generic register operations;
* accounting adjustments;
* exceptional business events;
* migration support;
* advanced operational scenarios.

### Principle

Unidoc should be used only when no specialized document is appropriate.

---

# Cost Allocation Model

The Standard Configuration supports two allocation modes.

---

## Direct Expenses

Direct expenses are assigned immediately to specific economic objects.

Examples:

* labor cost assigned to a production order;
* material consumption assigned to a product;
* depreciation assigned to a specific operation.

---

## Related Expenses

Related expenses are allocated through one or more allocation stages.

Typical allocation flow:

Expense
→ Business Document
→ Document Line
→ Economic Object

Related expenses may remain temporarily unallocated.

---

# Unallocated Costs

The system supports temporary unallocated costs.

Preferred approach:

Expense
→ Economic Object

Fallback approach:

Expense
→ Period Result

This preserves compatibility with traditional accounting models while prioritizing operational cost allocation.

---

# Business Facts And Intentions

The document architecture distinguishes between:

### Business Facts

Documents capable of creating register movements.

Examples:

* Purchase;
* Sale;
* Production;
* Cash;
* Salary Booking;
* Salary Taxation;
* Salary Sharing;
* Depreciation Booking;
* Depreciation Sharing;
* Unidoc.

### Business Intentions

Documents or sections that provide planning information.

Examples:

* Bill To Pay;
* payment proposals;
* allocation proposals.

Business intentions never create register movements.

---

# Reference Architecture Status

This document defines the canonical document model of the AcCore Standard Configuration and serves as the foundation for:

* Register Mapping;
* Cost Allocation Architecture;
* User Interface Architecture;
* Workflow Design;
* Reporting Design.
