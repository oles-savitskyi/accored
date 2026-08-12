# STANDARD_WORKFLOWS

## Purpose

This document defines the standard operational workflows of the AcCore Standard Configuration.

Standard Workflows describe how users and application processes execute business operations through Standard Configuration documents and processing functions.

Workflows coordinate business activities but do not replace:

* Document Architecture;
* Posting Architecture;
* Register Architecture;
* Valuation Architecture;
* Cost Allocation;
* Security Architecture.

A Workflow determines **what happens next**.

Documents and processing engines determine **what business facts are created**.

---

# Workflow Principles

## 1. Business Operations Are Recorded Immediately

The Standard Configuration follows the Continuous Cost Recognition principle.

Business operations should be recorded:

* at the moment they occur;
* or immediately after the event.

The system should not require users to wait until the end of a reporting period to recognize operational facts that are already known.

---

## 2. Facts And Intentions Are Separated

A workflow may contain planning or informational steps.

Such steps do not create register movements unless and until the corresponding business fact is recorded.

For example:

`Bill To Pay` represents an intention to pay.

The actual payment is recorded through `Cash`.

---

## 3. Workflow Does Not Replace Posting

Workflow controls document processing.

Posting determines register movements.

The relationship is:

```text
User / Process
    ↓
Workflow
    ↓
Document State
    ↓
Posting
    ↓
Register Movements
    ↓
Valuation / Cost Processing
```

---

## 4. Cost Recognition Is Continuous

Salary, depreciation, material consumption, and other costs should be recognized as soon as sufficient operational information becomes available.

Period closing is a fallback mechanism rather than the primary mechanism of cost recognition.

---

# Standard Workflow Categories

The Standard Configuration defines workflows for:

* Purchase;
* Sale;
* Production;
* Salary;
* Depreciation;
* Cash;
* Unidoc.

Reference Documents have simplified maintenance workflows and do not represent ordinary business operations.

---

# Purchase Workflow

## Purpose

Records acquisition of goods, materials, assets, services, and related expenses.

## Main Flow

```text
Create Purchase
    ↓
Enter Requisites
    ↓
Enter Invoice
    ↓
Enter Related Expenses
    ↓
Enter Return Outwards (if applicable)
    ↓
Define Bill To Pay (optional)
    ↓
Validate
    ↓
Post
    ↓
Register Quantity Facts
    ↓
Create / Update Supplier Settlement
    ↓
Create Tax Liabilities
    ↓
Valuation Processing
```

## Purchase Cost Allocation

Related expenses may be allocated to the Purchase document.

Further allocation to individual invoice lines is obligatory for Purchase when a related expense has been allocated to the document.

---

## Bill To Pay

`Bill To Pay` is optional.

It represents a payment intention and may be used for:

* payment planning;
* reminders;
* workflow;
* cash management preparation.

It does not create:

* settlement movements;
* cash movements;
* accounting balances.

Actual payment is recorded only through `Cash`.

---

## Purchase Returns

Returns are recorded within the Purchase document through `Return Outwards`.

The return creates the corresponding quantity and valuation effects.

---

# Sale Workflow

## Purpose

Records sales of goods, materials, products, services, and other economic objects.

## Main Flow

```text
Create Sale
    ↓
Enter Requisites
    ↓
Enter Invoice
    ↓
Enter Related Expenses
    ↓
Enter Return Inwards (if applicable)
    ↓
Define Bill To Pay (optional)
    ↓
Validate
    ↓
Post
    ↓
Register Quantity Facts
    ↓
Create / Update Customer Settlement
    ↓
Create Tax Liabilities
    ↓
Valuation Processing
```

## Sales Cost Allocation

Related expenses may be allocated to the Sale document.

Further allocation to individual invoice lines is optional.

If costs remain unallocated, they may reduce the overall economic result associated with the Sale.

---

## Sales Returns

Returns are recorded within the Sale document through `Return Inwards`.

The return creates the corresponding quantity and valuation effects.

---

# Production Workflow

## Purpose

Records production and formation of the cost of produced economic objects.

## Main Flow

```text
Create Production
    ↓
Enter Requisites
    ↓
Enter Product List
    ↓
Enter Direct Expenses
    ↓
Enter Related Expenses
    ↓
Validate
    ↓
Post
    ↓
Consume Resources
    ↓
Create Production Output
    ↓
Apply Available Cost Information
    ↓
Valuation
```

## Direct Expenses

Direct expenses are assigned directly to identifiable production objects.

They may include:

* materials;
* goods;
* services;
* labor;
* depreciation.

---

## Related Expenses

Related expenses are allocated to the Production document and may subsequently be allocated to individual Product List lines.

If allocation cannot be performed immediately, the expense may remain unallocated. If a related expense is allocated to the Production document, its allocation to Product List lines must be completed before the document is closed.

---

# Salary Workflow

Salary processing is divided into three independent economic activities:

* Salary Booking;
* Salary Sharing;
* Salary Taxation.

`Salary Rollout` is a consolidated result of Salary Booking and Salary Taxation and does not create register movements.

---

## Salary Booking

### Purpose

Recognizes labor quantities and corresponding labor costs continuously. Salary Booking recognizes salary accruals and associated Rollout Fees used to determine the total labor cost.

### Flow

```text
Employee Activity
    ↓
Salary Booking
    ↓
Record Labor Quantity
    ↓
Determine Labor Cost
    ↓
Valuation
```

Salary Booking may operate:

* daily;
* hourly;
* or at another operational frequency supported by the configuration and determined by accountant.

The objective is to have accrued salary available before the end of the month.

---

## Salary Sharing

### Purpose

Allocates accrued labor cost to business operations.

### Flow

Salary may be:

* fully allocated;
* partially allocated;
* temporarily unallocated.

Unallocated salary may remain until a suitable allocation becomes possible or until period closing.

Allocated salary leads to the schema:
```text
Accrued Labor Cost
    ↓
Salary Sharing
    ↓
Purchase / Sale / Production
    ↓
Document-Line Allocation
    ↓
Economic Object
```

Document-line allocation is optional for Sale and obligatory for Purchase and Production.

---

## Salary Taxation

### Purpose

Creates the statutory payroll deductions and liabilities.

### Flow

```text
Accrued Salary
    ↓
Salary Taxation
    ↓
Employee Deductions
    ↓
Payroll Tax Liabilities
    ↓
Settlement Register
```

Salary Taxation is normally performed monthly.

---

## Salary Rollout

Salary Rollout consolidates:

* salary accruals;
* employer obligations;
* employee deductions;
* taxes;
* other withholdings.

It provides the traditional payroll statement while keeping accounting facts in their specialized processing documents.

`Salary Rollout` does not create register movements.

---

# Depreciation Workflow

Depreciation follows the same resource-oriented model as labor.

## Main Flow

```text
Asset Utilization
    ↓
Depreciation Booking
    ↓
Record Utilization Quantity
    ↓
Determine Depreciation Cost
    ↓
Valuation
    ↓
Depreciation Sharing
    ↓
Purchase / Sale / Production
    ↓
Document-Line Allocation
    ↓
Economic Object
```

Document-line allocation is optional for Sale and obligatory for Purchase and Production.

---

## Depreciation Rate Plan

The hourly depreciation rate is established when the asset is commissioned.

The rate is stored in `Depreciation Rate Plan`.

The plan is a time-dependent reference document and does not itself create accounting movements.

---

## Depreciation Sharing

Depreciation may be:

* directly assigned to an identifiable business object;
* allocated to a Purchase;
* allocated to a Sale;
* allocated to Production;
* temporarily left unallocated.

Unallocated depreciation may remain until a suitable allocation becomes possible or until period closing.
---

# Cash Workflow

## Purpose

Records actual monetary movements.

Cash combines several traditional operational scenarios:

* bank transactions;
* cash transactions;
* employee advances;
* expense reports.

## Main Flow

```text
Create Cash
    ↓
Enter Requisites
    ↓
Enter Cash / Bank Operation
    ↓
Identify Settlement (if applicable)
    ↓
Validate
    ↓
Post
    ↓
Cash Register
    ↓
Settlement Register (if applicable)
```

Cash is the authoritative source of payment facts.

A planned payment recorded elsewhere does not become an actual payment until a Cash operation is recorded.

---

# Unidoc Workflow

## Purpose

Provides a generic mechanism for business operations not covered by specialized documents.

## Main Flow

```text
Create Unidoc
    ↓
Define Operation
    ↓
Enter Required Facts
    ↓
Validate
    ↓
Post
    ↓
Register Movements
```

Unidoc may operate on:

* Resource Register;
* Labor Register;
* Asset Utilization Register;
* Cash Register;
* Settlement Register.

Unidoc should not be used when a specialized Standard Configuration document provides an appropriate business model.

---

# Cross-Document Cost Allocation Workflow

Related expenses may be distributed across several documents.

The standard allocation sequence is:

```text
Cost Source
    ↓
Related Expense
    ↓
Purchase / Sale / Production
    ↓
Document Line
    ↓
Economic Object
```

Not every cost requires all stages.

For example:

```text
Salary
    ↓
Production
```

may be sufficient when the Production document itself is the required cost receiver.

If several products are produced:

```text
Salary
    ↓
Production
    ↓
Product A
Product B
Product C
```

the second allocation stage may be performed.

Direct expenses do not require cross-document allocation because their cost receiver is known at the time of recognition.
---

# Unallocated Cost Workflow

The system supports costs that cannot yet be assigned to a specific economic object.

```text
Cost
    ↓
Unallocated
```

The preferred next step is operational allocation:

```text
Unallocated
    ↓
Purchase / Sale / Production
    ↓
Economic Object
```

If operational allocation is impossible or economically inappropriate, the cost may be recognized against the period result during period closing.

This preserves compatibility with traditional accounting while maintaining the operational-first design of AcCore.

---

# Period Closing

Period closing is not the primary mechanism for recognizing ordinary operational costs.

Its responsibilities are limited to activities that genuinely require period-level processing, including:

* final allocation of unresolved costs;
* reconciliation;
* statutory calculations;
* period reporting;
* exceptional corrections.

Operational facts that were already known during the period should not be recreated solely during closing.

---

# Workflow And Register Responsibility

| Workflow             | Primary Register Effects | Cost Processing      |
| -------------------- | ------------------------ | -------------------- |
| Purchase             | Resource, Settlement     | Valuation            |
| Sale                 | Resource, Settlement     | Valuation            |
| Production           | Resource                 | Valuation            |
| Salary Booking       | Labor                    | Valuation            |
| Salary Sharing       | —                        | Valuation            |
| Salary Taxation      | Settlement               | —                    |
| Depreciation Booking | Asset Utilization        | Valuation            |
| Depreciation Sharing | —                        | Valuation            |
| Cash                 | Cash, Settlement         | —                    |
| Unidoc               | Depends on operation     | Depends on operation |

---

# Workflow Design Principle

The Standard Configuration shall prefer:

```text
Immediate Business Fact
    ↓
Immediate Register Movement
    ↓
Immediate Valuation
    ↓
Immediate Cost Availability
```

over:

```text
End-of-Period Processing
    ↓
Mass Calculation
    ↓
Mass Posting
```

Period closing remains available where required, but it is not the normal path for information that can be captured operationally.

---

# Status

This document defines the initial canonical workflow model for the AcCore Standard Configuration.

Detailed user interface flows, approval workflows, exception handling, and role-specific permissions are defined separately.
