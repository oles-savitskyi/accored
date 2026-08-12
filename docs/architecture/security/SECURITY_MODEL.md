SECURITY_MODEL.md
Purpose

The Security Model defines how AcCore evaluates access requests and produces authorization decisions.

The model is independent from:

business applications;
metadata configurations;
UI technologies;
storage implementation;
integration protocols.

The Security Model provides a unified authorization process for all system interactions.

Architectural Principles
Single Authorization Pipeline

All access requests must be evaluated using the same authorization process.

There must be no alternative authorization mechanisms.

Security Is Centralized

Authorization decisions are performed exclusively by the Security subsystem.

Business code must not perform security checks directly.

Forbidden:

if current_user.role == "Administrator":
    ...

or

if document.owner == current_user:
    ...

Such logic belongs to the Security subsystem.

Default Deny

All requests are denied unless explicitly allowed.

No Permission
    =>
DENY

This rule applies to:

UI operations;
business operations;
reports;
API requests;
event subscriptions.
Runtime Authorization

Authorization decisions are evaluated at runtime.

Permissions are never hardcoded into business components.

Metadata-Based Authorization

Authorization targets metadata objects.

Examples:

Catalog.Products
Document.SalesOrder
Register.Inventory
Report.InventoryBalance
API.Customer

Authorization must not depend on implementation classes.

Authorization Pipeline

Every request passes through the same security flow.

Request
    ↓
Authentication
    ↓
Principal Creation
    ↓
Permission Resolution
    ↓
Constraint Evaluation
    ↓
Authorization Decision
Step 1. Authentication

The caller identity is established.

Examples:

User Login
API Token
Service Account
OAuth Identity

Result:

Authenticated Identity

If authentication fails:

DENY
Step 2. Principal Creation

The authenticated identity is converted into a Principal.

Example:

User
    ↓
Principal

The Principal contains:

Roles
Permissions
Constraints
Claims

The rest of the system works exclusively with Principal.

Step 3. Security Object Resolution

The requested operation is mapped to a Security Object.

Example:

Open Sales Order

becomes:

SecurityObject:
Document.SalesOrder

Another example:

Run Inventory Report

becomes:

SecurityObject:
Report.InventoryBalance
Step 4. Permission Resolution

The Security subsystem determines whether the Principal possesses the required permission.

Example:

Required:

Document.SalesOrder.Read

Principal permissions:

Document.SalesOrder.Read
Document.SalesOrder.Write

Result:

Permission Found

If permission is absent:

DENY
Step 5. Constraint Evaluation

If the permission contains constraints, they are evaluated.

Example:

Permission:
Document.SalesOrder.Read

Constraint:
OwnOrganization

Document:

organization_id = 15

User:

organization_id = 15

Result:

Constraint Satisfied

If the values differ:

Constraint Failed

Result:

DENY
Step 6. Authorization Decision

The final result is produced.

Permission Found
AND
All Constraints Satisfied

Result:

ALLOW

Otherwise:

DENY
Authorization Formula

Conceptually:

ALLOW =
Authenticated
AND
Permission Exists
AND
All Constraints Pass

Otherwise:

DENY
Security Context

Every protected operation executes within a Security Context.

SecurityContext
├── principal
├── session
├── permissions
├── constraints
└── request_metadata

The Security Context accompanies execution through Runtime.

Authorization Targets

The model applies uniformly to all platform resources.

Metadata Objects
Catalog
Document
Register
Report
Processing
Runtime Operations
Read
Write
Delete
Post
Execute
Approve
Integration Operations
API Calls
Import Operations
Export Operations
Event Operations
Publish Event
Subscribe Event
Replay Event
Security Decision Service

Authorization decisions are performed by a dedicated service.

Conceptually:

AuthorizationService

Interface:

authorize(
    principal,
    security_object,
    operation,
    context
)

Result:

ALLOW
or
DENY

No other component may issue security decisions.

Audit Integration

Every authorization decision may be audited.

Examples:

Login Success
Login Failure
Permission Denied
Permission Granted
Role Changed

The Security Model produces audit events but does not define audit storage.

Security Flow
Request
    ↓
Authenticate
    ↓
Create Principal
    ↓
Resolve Security Object
    ↓
Resolve Permission
    ↓
Evaluate Constraints
    ↓
ALLOW / DENY
    ↓
Execute Operation
Security Model Summary

AcCore uses a centralized authorization pipeline based on:

Principal
      ↓
Permission
      ↓
Constraint
      ↓
ALLOW / DENY

The model guarantees:

Default Deny behavior;
Metadata-based authorization;
Runtime authorization decisions;
Centralized security enforcement;
Uniform security across UI, Runtime, Reporting, and Integration layers.