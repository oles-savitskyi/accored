# STANDARD_ROLES

## Purpose

This document defines the role model used by the AcCore Standard Configuration.

The Standard Configuration does not enforce a fixed set of business roles.

Instead, it provides a configurable role framework that allows organizations to define roles according to their own structure and responsibilities.

---

# Architectural Principles

The role system follows:

* ADR-STD-010 — Role Permissions Are Business-Object-Oriented
* ADR-STD-011 — Access Rights Are Defined Through Access Modes

Roles are built from permissions.

Permissions are built from:

* Domain;
* Object;
* Object Scope;
* Data Scope;
* Access Mode.

---

# Role Structure

```text
Role
 └── Permission
      ├── Domain
      ├── Object
      ├── Object Scope (optional)
      ├── Data Scope (optional)
      └── Access Mode
```

---

# Domains

The Standard Configuration defines the following business domains.

## Reference Data

Reference catalogs and supporting master data.

Examples:

* Employees
* Assortment
* Business Partners
* Financial Accounts
* Currencies
* Taxes

---

## Purchasing

Purchase-related business operations.

Examples:

* Purchase
* Purchase-related Processings

---

## Sales

Sales-related business operations.

Examples:

* Sale
* Sales-related Processings

---

## Production

Production-related business operations.

Examples:

* Production
* Production-related Processings

---

## Salary

Payroll and labor accounting.

Examples:

* Salary Booking
* Salary Sharing
* Salary Taxation
* Salary Rollout

---

## Depreciation

Asset utilization and depreciation.

Examples:

* Depreciation Booking
* Depreciation Sharing
* Depreciation Rate Plan

---

## Cash

Financial operations.

Examples:

* Cash
* Financial Accounts

---

## Reporting

Reports and analytical views.

---

## Administration

Configuration and platform administration.

Examples:

* Global Settings
* Roles
* Security Settings
* Period Management

---

# Objects

Objects represent concrete business entities within a domain.

Examples:

```text
Purchasing
    Purchase

Sales
    Sale

Salary
    Salary Booking
    Salary Sharing
    Salary Taxation

Reference Data
    Employees
    Assortment
```

---

# Object Scope

Object Scope provides permissions for specific parts of a business object.

---

## Documents

Examples:

```text
Purchase
    Requisites
    Invoice
    Bill To Pay
    Related Expenses

Sale
    Requisites
    Invoice
    Related Expenses

Production
    Product List
    Direct Expenses
    Related Expenses
```

---

## Reference Data

Examples:

```text
Assortment
    Folder
    Element

Business Partners
    Folder
    Element
```

Object Scope is optional.

If omitted, the permission applies to the entire object.

---

# Data Scope

Data Scope limits access to subsets of data.

Examples:

```text
Business Partner Type = Supplier
```

```text
Currency = EUR
```

```text
Department = Sales
```

```text
Financial Account = Main Bank Account
```

```text
Employee Group = Production Team A
```

Data Scope is optional.

If omitted, the permission applies to all available data.

---

# Access Modes

The Standard Configuration defines three access modes.

---

## View

Read-only access.

Examples:

* open documents;
* view catalogs;
* print reports;
* browse historical data.

---

## Execute

Operational access.

Examples:

* create documents;
* edit documents;
* post documents;
* execute processings;
* perform workflow actions.

---

## Administer

Administrative access.

Examples:

* delete objects;
* modify role definitions;
* manage security;
* modify global settings;
* reopen periods.

---

# Role Assignment

Users may have multiple roles.

Example:

```text
User
 ├── Sales Role
 └── Cash Role
```

Permissions are accumulated across assigned roles.

---

# Predefined Roles

The Standard Configuration may provide predefined roles as examples and starting templates.

Examples:

```text
Standard Accountant
Standard Sales User
Standard Purchasing User
Standard Production User
Standard Payroll User
Standard Cash User
Standard Manager
```

These predefined roles are not mandatory.

Organizations may:

* modify them;
* replace them;
* create their own roles.

---

# Role Administration

Creation and modification of roles shall be restricted to:

* System Administrator;
* Configuration Administrator.

Ordinary users may be assigned roles but cannot modify role definitions.

---

# Reporting Permissions

Reports use a simplified permission model.

```text
Report
    ↓
Access
```

Examples:

```text
Sales Analysis
    View
```

```text
Accounts Receivable
    View
```

```text
Profitability Analysis
    View
```

Report permissions are independent from document permissions.

---

# Security Principle

Permissions should be granted according to the principle of least privilege.

Users should receive only the permissions required to perform their responsibilities.

Administrative permissions should be assigned only when operational permissions are insufficient.

---

# Status

This document defines the canonical role model for the AcCore Standard Configuration.

Specific business roles are configuration artifacts built upon this model and are not part of the platform architecture itself.
