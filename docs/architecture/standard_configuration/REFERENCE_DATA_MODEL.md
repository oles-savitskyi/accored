# REFERENCE_DATA_MODEL

## Purpose

This document defines the reference data architecture of the AcCore Standard Configuration.

Reference data provides stable business information used throughout operational, costing, reporting, and integration processes.

The model is designed according to the following principles:

* SMB-oriented design;
* process-oriented business operations;
* continuous cost recognition;
* unified economic object model;
* metadata-driven extensibility.

---

# Reference Data Architecture

The Standard Configuration organizes reference data into five logical groups:

* Organization
* Economic Objects
* Commercial Data
* Financial Data
* Ownership Data

In addition, a special category of time-dependent reference information is maintained through Reference Documents.

---

# Organization

Provides information about the internal structure of the organization.

---

## Employees

Maintains employee records.

Used by:

* Salary Booking;
* Salary Sharing;
* Salary Rollout;
* Workflow assignments;
* Reporting.

---

## Departments

Defines the organizational structure of the company.

Used for:

* personnel management;
* workflow routing;
* security;
* reporting;
* organizational analytics.

Departments are organizational entities and are not used as cost centers.

---

## Positions

Defines employee positions and job roles.

Used by:

* human resource management;
* payroll processing;
* reporting.

---

## Teams

Defines temporary or permanent working groups.

Examples:

* production teams;
* installation teams;
* sales teams;
* project teams.

Used for operational coordination and reporting.

---

# Economic Objects

Provides the core economic model of the application.

---

## Assortment

The central catalog of economic objects.

Supported object categories include:

* Products
* Goods
* Materials
* Services
* Fixed Assets
* Intangible Assets
* Investments
* Expenses
* Revenues

Assortment serves as the primary business object catalog for:

* purchasing;
* sales;
* inventory;
* production;
* valuation;
* reporting;
* cost allocation.

Economic objects are the primary receivers of allocated costs.

---

## Measure Units

Defines measurement units used by economic objects.

Examples:

* pieces;
* kilograms;
* liters;
* hours;
* square meters.

---

## Depreciation Methods

Defines available depreciation methods for fixed and intangible assets.

Examples:

* straight-line;
* declining balance;
* production-based depreciation.

---

# Commercial Data

Provides reference information required for commercial operations.

---

## Business Partners

Unified catalog of external business entities.

Supported partner types include:

* Customer;
* Supplier;
* Customer and Supplier;
* Bank;
* Government Agency;
* Other.

Business Partner type is defined by attributes rather than separate catalogs.

---

## Price Categories

Defines commercial pricing groups.

Examples:

* Retail;
* Wholesale;
* Distributor;
* VIP.

Used by sales and pricing processes.

---

## Sale Prices

Maintains commercial prices for Assortment items.

A Sale Price typically includes:

* Assortment Item;
* Price Category;
* Currency;
* Price;
* Valid From.

Supports category-based and customer-specific pricing strategies.

---

# Financial Data

Provides financial reference information.

---

## Financial Accounts

Unified catalog of financial accounts.

Supported account types include:

* Cash Accounts;
* Bank Accounts;
* Card Accounts;
* Electronic Money Accounts.

Used by Cash Management processes.

---

## Currencies

Defines currencies supported by the application.

Examples:

* USD;
* EUR;
* UAH;
* GBP.

---

## Taxes

Defines taxes supported by the organization.

Examples:

* VAT;
* Sales Tax;
* Payroll Tax;
* Withholding Tax.

Tax rates are maintained separately through Reference Documents.

---

# Ownership Data

Provides ownership-related information.

---

## Owners

Maintains company ownership information.

Examples:

* founders;
* shareholders;
* investors.

Owners are separate from Business Partners because ownership relationships differ from commercial relationships.

---

# Reference Documents

Some reference information changes over time and cannot be modeled as static catalogs.

Such information is maintained through Reference Documents.

Reference Documents behave similarly to business documents but primarily provide reference data for operational processes.

---

## Currency Rate History

Maintains currency exchange rates.

Typical attributes:

* Currency;
* Exchange Rate;
* Valid From.

Used by:

* purchasing;
* sales;
* valuation;
* reporting.

---

## Tax Rate History

Maintains historical tax rates.

Typical attributes:

* Tax;
* Tax Rate;
* Valid From.

Used by:

* taxation;
* payroll;
* reporting;
* compliance processes.

---

# Cost Allocation Principles

The Standard Configuration does not use a dedicated Cost Center catalog.

Costs are allocated directly to business operations and economic objects.

Examples include:

* products;
* materials;
* production output;
* purchased inventory;
* sales operations.

This approach supports the Continuous Cost Recognition principle defined by ADR-STD-003.

---

# Reference Data Status

This document defines the canonical reference data model of the AcCore Standard Configuration.

It serves as the foundation for:

* Document Architecture;
* Pricing Architecture;
* Cost Allocation Architecture;
* Reporting Architecture;
* User Interface Architecture.
