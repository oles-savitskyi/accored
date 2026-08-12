AUTHORIZATION_MODEL.md
Purpose

The Authorization Model defines how access permissions are represented and evaluated in AcCore.

The model is metadata-driven and independent from implementation classes, storage structures, and user interface technologies.

Authorization is performed against metadata objects and operations.

Authorization Principle

Authorization is based on the combination of:

Security Object
+
Operation
=
Permission

Example:

Document.SalesOrder
+
Read
=
Document.SalesOrder.Read
Authorization Hierarchy
Security Object
        ↓
Operation
        ↓
Permission
        ↓
Constraint
        ↓
Authorization Decision
Security Objects

Security Objects represent protected metadata entities.

Authorization must always target a Security Object.

Catalog

Examples:

Catalog.Products
Catalog.Customers
Catalog.Warehouses
Catalog.Employees
Document

Examples:

Document.SalesOrder
Document.PurchaseInvoice
Document.GoodsReceipt
Register

Examples:

Register.Inventory
Register.GeneralLedger
Register.CashFlow
Report

Examples:

Report.InventoryBalance
Report.SalesAnalysis
Report.TrialBalance
Processing

Examples:

Processing.DataImport
Processing.MonthEndClosing
Processing.InventoryRebuild
API Endpoint

Examples:

API.Customer
API.SalesOrder
API.Inventory
Event

Examples:

Event.DocumentPosted
Event.InventoryChanged
Event.CostRecalculated
Operations

Operations represent actions that may be performed on Security Objects.

Operations are platform-defined.

Configurations may use them but do not define new operation semantics.

Core Operations
Read

View data.

Examples:

Open document
View catalog
Run query
Read API resource

Permission:

Document.SalesOrder.Read
Write

Create or modify data.

Examples:

Edit document
Edit catalog
Update API resource

Permission:

Document.SalesOrder.Write
Delete

Remove data.

Permission:

Document.SalesOrder.Delete
Execute

Run logic.

Examples:

Run report
Execute processing
Invoke operation

Permission:

Report.InventoryBalance.Execute
Business Operations

These operations are specific to business workflows.

Post

Perform document posting.

Permission:

Document.SalesOrder.Post
Unpost

Reverse posting.

Permission:

Document.SalesOrder.Unpost
Approve

Approve business object.

Permission:

Document.PurchaseInvoice.Approve
Close

Close period or object.

Permission:

Document.PeriodClosing.Close
Administrative Operations
Administer

Modify security or system settings.

Permission:

System.Security.Administer
Configure

Modify metadata configuration.

Permission:

System.Metadata.Configure
ManageUsers

Manage users and roles.

Permission:

System.Users.Manage
Integration Operations
Import

Permission:

Processing.DataImport.Import
Export

Permission:

Report.InventoryBalance.Export
Invoke

Call API operation.

Permission:

API.Customer.Invoke
Event Operations
Publish

Permission:

Event.InventoryChanged.Publish
Subscribe

Permission:

Event.InventoryChanged.Subscribe
Replay

Permission:

Event.InventoryChanged.Replay
Permission Structure

Permissions use a canonical naming convention.

Format:

<ObjectType>.<ObjectCode>.<Operation>

Examples:

Catalog.Products.Read

Catalog.Products.Write

Document.SalesOrder.Read

Document.SalesOrder.Post

Report.InventoryBalance.Execute

API.Customer.Invoke
Permission Granularity

Permissions are assigned at metadata object level.

Not:

Document

But:

Document.SalesOrder

Not:

Catalog

But:

Catalog.Products

This keeps the model consistent with Metadata-Driven Architecture.

Constraints

Permissions may contain constraints.

Example:

Document.SalesOrder.Read

Constraint:

OwnOrganization

Effective authorization:

Read SalesOrder
within OwnOrganization
Authorization Evaluation

Authorization succeeds only when:

Permission Exists
AND
All Constraints Pass

Otherwise:

DENY
Metadata Integration

Every Security Object references a metadata definition.

Conceptually:

Metadata Object
        ↓
Security Object
        ↓
Permissions

This guarantees:

security independence from implementation code;
automatic participation of new metadata objects in authorization;
consistent behavior across Runtime, Reporting, and Integration layers.
Authorization Model Summary

Authorization in AcCore is based on:

Security Object
+
Operation
=
Permission

Permissions are assigned through roles and evaluated against contextual constraints.

The model provides:

metadata-driven authorization;
fine-grained access control;
centralized security enforcement;
integration with Runtime, Reporting, API, and Event subsystems.