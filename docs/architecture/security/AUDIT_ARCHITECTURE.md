AUDIT_ARCHITECTURE.md
Purpose

The Audit Architecture provides a complete and reliable history of security-relevant and business-relevant actions performed within AcCore.

The primary goal of auditing is traceability.

Audit records provide evidence of:

who performed an action;
what action was performed;
when it happened;
what object was affected;
whether the operation succeeded or failed.
Architectural Principles
Audit Is Independent

Audit records are independent from business data.

Deleting or modifying business objects must not remove audit history.

Audit Is Append-Only

Audit records are immutable.

Existing records must never be updated or deleted.

Create Only
Never Update
Never Delete
Audit Is Fact-Based

Audit records describe facts.

Audit does not store interpretations.

Allowed:

User X posted document Y

Not:

User X made a mistake
Audit Is Universal

The same audit model applies to:

UI operations;
Runtime operations;
Posting operations;
Report execution;
API calls;
Event operations;
Security operations.
Audit Never Affects Business Logic

Business execution must not depend on audit queries.

Audit is observational.

Audit never becomes a source of business state.

Audit Model

Audit Architecture is based on Audit Events.

Action
      ↓
Audit Event
      ↓
Audit Trail
Audit Event

An Audit Event represents an immutable fact.

AuditEvent
├── id
├── timestamp
├── event_type
├── actor
├── target
├── operation
├── result
└── details
Actor

Represents the identity that initiated the action.

Examples:

User
Service Account
API Client
External Identity

Reference:

Principal

from the Security subsystem.

Target

Represents the affected object.

Examples:

Document.SalesOrder

Catalog.Products

Register.Inventory

Report.InventoryBalance

API.Customer

Audit targets follow the same metadata-driven model as authorization.

Operation

Represents the executed action.

Examples:

Read
Write
Delete
Post
Unpost
Execute
Import
Export
Publish
Subscribe
Login
Logout
Result

Represents execution outcome.

Values:

Success
Failure
Denied
Audit Categories

To simplify analysis, events are grouped into categories.

Authentication Audit

Examples:

Login Success
Login Failure
Logout
Session Expired
Authorization Audit

Examples:

Permission Granted
Permission Denied
Role Assigned
Role Removed
Business Audit

Examples:

Document Created
Document Modified
Document Deleted
Document Posted
Document Unposted
Register Audit

Examples:

Register Movement Created
Register Query Executed
Totals Recalculated
Valuation Audit

Examples:

Valuation Started
Valuation Rebuilt
Cost Adjustment Applied
Reporting Audit

Examples:

Report Executed
Dataset Generated
Export Produced
Integration Audit

Examples:

API Request
API Failure
Import Started
Import Completed
Export Completed
Event Audit

Examples:

Event Published
Event Delivered
Event Replay Started
Audit Trail

Audit Events are stored in an Audit Trail.

Conceptually:

Audit Event
      ↓
Audit Trail
      ↓
Historical Record

The Audit Trail is append-only.

Audit Correlation

Complex operations may generate multiple audit events.

Example:

Post Document
        ↓
Permission Check
        ↓
Posting
        ↓
Register Movements
        ↓
Valuation Trigger

All generated events should share a common:

correlation_id

This enables complete traceability.

Audit Context

Every Audit Event should contain contextual information.

Examples:

Session ID
Principal ID
Request ID
Correlation ID
Client Information
Audit Retention

Audit retention policy is configuration-dependent.

However:

Audit retention
must never be shorter
than business retention

For accounting deployments audit retention is typically long-term.

Security Integration

Security operations must always produce audit records.

Mandatory examples:

Login Success
Login Failure
Permission Denied
Role Change
User Lockout
Session Termination
Reporting Integration

Audit data itself may be queried through Reporting Architecture.

However:

Audit Trail
≠
Business Data

Audit remains a separate domain.

Audit Flow
Request
      ↓
Authentication
      ↓
Authorization
      ↓
Business Operation
      ↓
Audit Event
      ↓
Audit Trail
Audit Architecture Summary

Audit Architecture provides immutable traceability across the entire platform.

Core model:

Actor
      ↓
Operation
      ↓
Target
      ↓
Result
      ↓
Audit Event

Key properties:

Metadata-Driven
Append-Only
Immutable
Fact-Based
Correlatable
Independent