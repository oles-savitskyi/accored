# APPLICATION_ARCHITECTURE

## Purpose

This document defines the business application architecture of the AcCore Standard Configuration.

The architecture organizes the application into business domains that support daily operations, continuous cost recognition, reporting, and integration.

---

# Architectural Vision

The AcCore Standard Configuration is a business management system designed for small and medium-sized organizations.

The system is built around:

* business processes;
* business documents;
* continuous cost recognition;
* operational visibility;
* management reporting.

Users interact with business operations while the platform manages accounting, posting, valuation, and reporting mechanisms internally.

---

# Architectural Layers

The application consists of four logical layers.

---

# Foundation Layer

Provided by the AcCore Platform.

Includes:

* Metadata Architecture
* Runtime Architecture
* Storage Architecture
* Security Architecture
* Workflow Architecture
* Posting Architecture
* Register Architecture
* Valuation Architecture
* Reporting Architecture
* Integration Architecture

The Standard Configuration depends on this layer but does not implement it.

---

# Reference Data Layer

Provides master data shared across the application.

Examples:

* Products
* Services
* Business Partners
* Customers
* Suppliers
* Employees
* Warehouses
* Fixed Assets
* Cost Centers
* Expense Categories
* Units of Measure
* Currencies

All business domains depend on this layer.

---

# Operational Layer

Captures primary business events.

Modules:

* Sales
* Purchasing
* Inventory
* Production
* Cash Management

Operational modules create the business facts that drive accounting and costing.

---

# Cost Allocation Layer

Recognizes and distributes business costs.

Modules:

* Salary Booking
* Salary Sharing
* Salary Rollout
* Depreciation Sharing
* Expense Sharing

This layer implements continuous cost recognition.

---

# Management Layer

Provides visibility, analysis, and control.

Modules:

* Reporting
* Dashboards
* Analytics
* Monitoring
* Accounts Receivable Workspace
* Accounts Payable Workspace

---

# Business Modules

---

# Reference Data

## Purpose

Maintains master data used by all business processes.

## Responsibilities

* product management;
* partner management;
* employee management;
* warehouse management;
* cost center management;
* measurement standards.

---

# Sales

## Purpose

Manages customer-facing business operations.

## Responsibilities

* customer orders;
* shipments;
* sales invoices;
* customer sales transactions.

---

# Purchasing

## Purpose

Manages supplier-facing business operations.

## Responsibilities

* purchase orders;
* goods receipts;
* supplier invoices;
* purchasing transactions.

---

# Inventory

## Purpose

Manages stock and warehouse operations.

## Responsibilities

* inventory receipts;
* inventory issues;
* transfers;
* adjustments;
* stock control.

---

# Production

## Purpose

Manages manufacturing activities.

## Responsibilities

* production orders;
* material consumption;
* production output;
* work-in-progress tracking.

---

# Cash Management

## Purpose

Manages cash and bank operations.

## Responsibilities

* incoming payments;
* outgoing payments;
* cash operations;
* bank operations;
* cash flow management.

---

# Cost Allocation Modules

---

# Salary Booking

## Purpose

Recognizes labor costs during the accounting period.

## Responsibilities

* labor cost accumulation;
* payroll accrual generation;
* continuous salary recognition.

Salary Booking records labor costs as work is performed.

---

# Salary Sharing

## Purpose

Distributes labor costs to cost objects.

## Responsibilities

* cost allocation;
* production labor distribution;
* sales labor distribution;
* purchasing labor distribution.

---

# Salary Rollout

## Purpose

Finalizes payroll settlements.

## Responsibilities

* deductions;
* payroll settlements;
* payroll payments;
* payroll reconciliation.

---

# Depreciation Sharing

## Purpose

Distributes asset consumption costs.

## Responsibilities

* depreciation allocation;
* cost center distribution;
* production asset cost distribution.

Monthly Depreciation serves as a planning and reconciliation mechanism.

Depreciation Sharing performs actual cost recognition.

---

# Expense Sharing

## Purpose

Distributes indirect expenses.

## Responsibilities

* overhead allocation;
* acquisition cost distribution;
* selling expense distribution;
* operating expense distribution.

---

# Reporting

## Purpose

Provides operational and management reporting.

## Responsibilities

* operational reports;
* management reports;
* dashboards;
* KPI analysis;
* business monitoring.

---

# Accounts Receivable Workspace

## Purpose

Provides customer debt management.

## Responsibilities

* receivable analysis;
* debt settlement support;
* overdue monitoring.

---

# Accounts Payable Workspace

## Purpose

Provides supplier debt management.

## Responsibilities

* payable analysis;
* settlement support;
* overdue monitoring.

---

# Integration

## Purpose

Supports communication with external systems.

## Responsibilities

* API integration;
* import;
* export;
* event exchange.

---

# Architectural Principles

## Process-Oriented Design

Users interact with business processes.

---

## Continuous Cost Recognition

Costs are recognized as close as possible to the moment they are incurred.

---

## Document-Centric Operations

Business documents represent operational events.

---

## Allocation-Driven Cost Formation

Cost allocation modules transform operational facts into business costs.

---

## Operational Visibility

Management reporting should reflect the current state of the business rather than month-end estimates.

---

# Future Expansion Areas

The architecture allows future addition of:

* CRM;
* Project Management;
* Service Management;
* Budgeting;
* E-Commerce;
* Mobile Operations.

Such extensions should preserve the principles defined by this document.

---

# Reference Architecture Status

This document defines the canonical business architecture of the AcCore Standard Configuration and serves as the foundation for:

* Catalog Architecture;
* Document Architecture;
* Register Mapping;
* Standard Workflows;
* Standard Roles;
* User Interface Architecture.
