SECURITY_DOMAIN_MODEL.md
Purpose

The Security Domain Model defines the core security entities used by AcCore and the relationships between them.

The model is independent from business applications, metadata configurations, storage implementation, and authentication mechanisms.

The Security Domain is responsible for representing:

security subjects;
permissions and roles;
protected resources;
authorization constraints;
runtime security context.
Architectural Principles
Security Is Metadata-Driven

Security rules are applied to metadata objects rather than implementation classes.

Authorization must not depend on Python classes, database tables, or UI components.

Security Is Runtime-Independent

Business components must not implement authorization logic internally.

All authorization decisions are delegated to the Security subsystem.

Permissions Describe Actions

Permissions represent allowed operations.

Permissions are not users, roles, or objects.

Roles Aggregate Permissions

Roles simplify administration by grouping permissions.

Roles do not contain business logic.

Constraints Refine Permissions

Constraints provide contextual restrictions for permissions.

Constraints never replace permissions.

Domain Entities
User

Represents a security subject capable of interacting with the system.

Responsibilities
identity ownership;
role assignment;
account lifecycle.
Attributes
User
├── id
├── login
├── display_name
├── email
├── is_active
├── created_at
└── updated_at
Notes

A User does not directly own permissions.

Permissions are obtained through roles.

Role

Represents a collection of permissions.

Responsibilities
permission aggregation;
administrative simplification.
Attributes
Role
├── id
├── code
├── name
└── description
Examples
Administrator
Accountant
SalesManager
WarehouseOperator
Auditor
Permission

Represents an allowed operation.

Responsibilities
define executable actions;
serve as the atomic authorization unit.
Attributes
Permission
├── id
├── code
├── name
└── description
Examples
Catalog.Products.Read

Catalog.Products.Write

Document.SalesOrder.Read

Document.SalesOrder.Post

Report.InventoryBalance.Run

API.Customer.Create
SecurityObject

Represents a protected metadata object.

Responsibilities
define authorization target;
connect security model with metadata model.
Attributes
SecurityObject
├── id
├── object_type
├── object_code
└── metadata_reference
Examples
Catalog.Products

Catalog.Customers

Document.SalesOrder

Register.Inventory

Report.InventoryBalance

API.Customer
Notes

Security Objects are metadata entities.

Authorization must not depend on implementation classes.

Constraint

Represents a contextual restriction applied to a permission.

Responsibilities
restrict permission scope;
support contextual authorization.
Attributes
Constraint
├── id
├── code
├── expression
└── parameters
Examples
OwnDocuments

OwnOrganization

OwnWarehouse

OwnDepartment
Example Expression
document.created_by == current_user

or

document.organization_id == current_user.organization_id
Principal

Represents the runtime security identity.

Responsibilities
runtime authorization;
security context propagation.
Attributes
Principal
├── user_id
├── roles
├── permissions
├── constraints
└── claims
Notes

After authentication the system works with Principal rather than User.

All authorization decisions are performed against Principal.

Session

Represents an authenticated runtime session.

Responsibilities
session lifecycle;
session expiration;
activity tracking.
Attributes
Session
├── id
├── principal_id
├── created_at
├── expires_at
├── last_activity_at
├── client_info
└── state
Relationships
User ↔ Role
User
    M:N
Role

Users may have multiple roles.

Roles may be assigned to multiple users.

Role ↔ Permission
Role
    M:N
Permission

Roles aggregate permissions.

Permissions may belong to multiple roles.

Permission → SecurityObject
Permission
      N:1
SecurityObject

Every permission targets a security object.

Permission ↔ Constraint
Permission
      0:N
Constraint

Permissions may have zero or more constraints.

User → Principal
User
  1:1
Principal

A Principal is created after successful authentication.

Principal → Session
Principal
      1:N
Session

A Principal may own multiple active sessions.

Domain Diagram
User
  |
  +-------------------+
  |                   |
  v                   |
Role -----------------+
  |
  v
Permission
  |
  +-------------> SecurityObject
  |
  +-------------> Constraint

User
  |
Authentication
  |
  v
Principal
  |
  v
Session
Out Of Scope

The following concepts are intentionally excluded from the first version of the Security Domain Model:

Group
Policy
Tenant
Organization
Security Claims Model
Authentication Providers
External Identity Providers

These concepts may be introduced by future architecture decisions if required.

Summary

The first version of the Security Domain Model consists of seven core entities:

User
Role
Permission
SecurityObject
Constraint
Principal
Session

This model provides the foundation for Authentication, Authorization, Audit, API Security, and future Security Architecture extensions.