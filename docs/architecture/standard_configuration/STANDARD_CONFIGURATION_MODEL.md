# STANDARD_CONFIGURATION_MODEL

## Purpose

This document defines the canonical business model of the AcCore Standard Configuration.

The Standard Configuration represents a complete SMB-oriented accounting and business management solution built entirely on top of the AcCore platform.

The model serves as the implementation baseline for the first production-ready Standard Edition.

---

# Architecture Position

The Standard Configuration is implemented through metadata and configuration mechanisms.

```text
AcCore Platform
        +
Standard Configuration
        =
AcCore Standard Edition
```

The Standard Configuration does not require modifications of platform architecture.

---

# Reference Data Model

## Catalogs

### Assortment

Unified catalog of economic objects.

May contain:

* Products;
* Goods;
* Materials;
* Services;
* Fixed Assets;
* Intangible Assets;
* Investments;
* Expense Items;
* Revenue Items.

---

### Employees

Personnel master data.

---

### Business Partners

Unified catalog of external entities.

Partner type is stored as an attribute.

Examples:

* Customer;
* Supplier;
* Bank;
* Government Institution;
* Other Partner.

---

### Cash Accounts

Financial accounts used for cash and banking operations.

---

### Measure Units

Measurement units used throughout the system.

---

### Price Categories

Categories used to group pricing policies.

---

### Sale Prices

Standard selling prices by category.

---

### Individual Prices

Partner-specific or object-specific prices.

---

### Taxes

Tax definitions used by documents and taxation processes.

---

### Currencies

Currency definitions.

---

### Departments

Organizational structure units.

Departments are not cost centers.

---

### Positions

Employee positions.

---

### Salary Types

Definitions of salary and compensation components.

---

# Reference Documents

Reference Documents are time-dependent business definitions.

Unlike ordinary catalogs, they maintain historical validity periods.

---

## Tax Rate History

Historical tax rates.

---

## Prices History

Historical sales and pricing information.

---

## Labour Tariff History

Historical labor rates.

---

## Depreciation Tariff Plan

Planned depreciation rates used for depreciation booking.

---

## Currency Rate History

Historical currency exchange rates.

---

# Documents

The Standard Configuration defines seven primary business documents.

---

## Purchase

Records acquisition operations.

Tabs:

* Requisites;
* Bill To Pay;
* Invoice;
* Related Expenses;
* Return Outwards.

---

## Sale

Records sales operations.

Tabs:

* Requisites;
* Bill To Pay;
* Invoice;
* Related Expenses;
* Return Inwards.

---

## Production

Records production operations.

Tabs:

* Requisites;
* Product List;
* Direct Expenses;
* Related Expenses.

---

## Salary

Records labor recognition, allocation, and payroll processing.

Components:

* Salary Booking;
* Salary Sharing;
* Salary Taxation;
* Salary Rollout.

---

## Depreciation

Records asset utilization and depreciation allocation.

Components:

* Depreciation Booking;
* Depreciation Sharing.

---

## Cash

Records actual financial movements.

Supports:

* bank operations;
* cash operations;
* employee advances;
* expense reports.

---

## Unidoc

Generic document used for business operations not covered by specialized documents.

---

# Registers

The Standard Configuration defines five primary registers.

---

## Resource Register

Stores quantitative movements of inventory and economic resources.

---

## Labor Register

Stores recognized labor quantities.

---

## Asset Utilization Register

Stores quantitative asset utilization.

---

## Settlement Register

Stores:

* receivables;
* payables;
* payroll liabilities;
* tax liabilities.

---

## Cash Register

Stores actual cash and bank movements.

---

# Valuation Components

The Standard Configuration uses the platform Valuation Architecture.

Valuation responsibilities include:

* cost determination;
* cost allocation;
* cost adjustments;
* cost balances.

Registers do not store costs.

Costs are maintained by the Valuation Engine and Cost Totals Engine.

---

# Processings

The Standard Configuration defines the following user processings.

---

## Salary Processing

Includes:

* Salary Booking;
* Salary Sharing;
* Salary Taxation.

---

## Depreciation Processing

Includes:

* Depreciation Booking;
* Depreciation Sharing.

---

## Expenses Sharing

Allocates related expenses to business documents and Economic Objects.

---

## Accounts Receivable

Provides receivable analysis and settlement operations.

---

## Accounts Payable

Provides payable analysis and settlement operations.

---

# Reports

## Financial Reports

### Trade, Profit and Loss Account

Financial result statement.

---

### Balance Sheet

Statement of financial position.

---

### Trial Balance

Balance verification report.

---

### Account Turnover Sheet

Account movement and turnover report.

---

## Operational Reports

### Inventory Balances

Current inventory balances.

---

### Inventory Turnover

Inventory movement analysis.

---

### Accounts Receivable

Outstanding customer receivables.

---

### Accounts Payable

Outstanding supplier liabilities.

---

### Cash Balances

Cash and bank balances.

---

### Salary Rollout

Payroll summary report.

---

### Production Cost Analysis

Production cost structure and allocation report.

---

### Cost Allocation Analysis

Analysis of direct, related, and unallocated costs.

---

# Security Model

The Standard Configuration uses:

* Roles;
* Domains;
* Objects;
* Object Scope;
* Data Scope;
* Access Modes.

Access Modes:

* View;
* Execute;
* Administer.

---

# Workflow Model

Business workflows are defined separately in:

* STANDARD_WORKFLOWS.md

The Standard Configuration follows the Continuous Cost Recognition principle.

Operational facts should be recognized and allocated as early as possible.

---

# Implementation Baseline

This document defines the canonical implementation baseline for the first release of the AcCore Standard Edition.

Future versions may extend the model while preserving compatibility with the architectural principles defined by the AcCore platform.
