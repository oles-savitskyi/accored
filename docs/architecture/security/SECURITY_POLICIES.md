SECURITY_POLICIES.md
Purpose

Security Policies define mandatory security rules governing authentication, authorization, sessions, credentials, integrations, and auditing within AcCore.

Security Policies establish platform-wide security requirements.

Implementations may strengthen these requirements but must not weaken them.

Architectural Principles
Security By Default

Security features must be enabled by default.

Insecure configurations must require explicit administrative action.

Default Deny

Access is denied unless explicitly granted.

No Permission
    ↓
DENY

This rule applies to:

users;
service accounts;
API clients;
external identities.
Least Privilege

Principals should receive only permissions required for their responsibilities.

Permissions must not be granted preemptively.

Separation Of Duties

Critical business operations should be separable between different roles.

Examples:

Create Document
Post Document

Configure Security
Audit Security

Import Data
Approve Data

The platform shall support such separation.

Credential Policy
Credential Confidentiality

Credentials must never be stored in plain text.

Passwords must be stored as secure password hashes.

Password Storage

Passwords must be:

Salted
Hashed
Non-Reversible

Plain text storage is prohibited.

Password Transmission

Passwords must never be transmitted in clear text.

Secure transport is mandatory.

Credential Revocation

Compromised credentials must be revocable without system restart.

Password Policy

The platform supports configurable password policies.

Typical controls include:

Minimum Length
Maximum Length
Complexity Rules
Expiration Rules
History Rules

Specific values are deployment-dependent.

The architecture must not hardcode password requirements.

Authentication Policy
Authentication Required

Protected operations require successful authentication.

Unauthenticated requests must be denied.

Provider Independence

Authentication policies apply equally to:

Local Authentication
LDAP
OAuth2
OpenID Connect
Future Providers
Identity Verification Before Authorization

Authorization must never be evaluated before authentication.

Required flow:

Authenticate
      ↓
Create Principal
      ↓
Authorize
Session Policy
Session Ownership

Every active session belongs to exactly one Principal.

Session Expiration

Sessions must have finite lifetime.

Unlimited sessions are prohibited.

Session Invalidation

Sessions may be invalidated through:

Logout
Administrative Action
Credential Revocation
Security Event
Idle Session Control

Inactive sessions may expire according to deployment policy.

Authorization Policy
Centralized Authorization

Authorization decisions must be performed only by the Security subsystem.

Business components must not implement independent authorization logic.

Metadata-Based Authorization

Permissions are evaluated against metadata objects.

Authorization must not depend on implementation classes.

Constraint Enforcement

Constraints are mandatory.

A granted permission does not bypass constraint evaluation.

Required rule:

Permission
AND
Constraint

not

Permission
OR
Constraint
Service Account Policy
No Security Bypass

Service Accounts are security subjects.

They must pass through the same authorization process as users.

Explicit Permissions

Service Accounts receive explicitly assigned permissions.

Implicit administrative access is prohibited.

Traceability

Actions performed by Service Accounts must be auditable.

API Security Policy
Integration Never Bypasses Runtime

All external requests must pass through:

Authentication
Authorization
Audit

before business execution.

Authenticated APIs

Protected APIs require authentication.

Anonymous API access is disabled by default.

Principle Of Explicit Exposure

Only explicitly published APIs are externally accessible.

Event Security Policy
Controlled Publication

Event publication may be restricted by permissions.

Controlled Subscription

Event subscriptions may be restricted by permissions.

Replay Protection

Event replay capabilities require explicit authorization.

Audit Policy
Mandatory Audit

Security-relevant actions must produce audit records.

Immutable Audit

Audit records are append-only.

Existing records must never be modified.

Audit Independence

Audit data is independent from business data.

Deleting business objects must not delete audit records.

Security Event Auditing

Mandatory examples:

Login Success
Login Failure
Permission Denied
Role Assignment
Role Removal
Session Termination
Credential Revocation
Administrative Security Policy
Administrative Operations Require Explicit Permissions

Administrative access is not implied by any role name.

Administrative capabilities are granted through permissions.

Security Administration Audit

Security configuration changes must be auditable.

Examples:

User Created
Role Assigned
Role Removed
Permission Modified
Security Policy Changed
Data Protection Policy
Minimum Disclosure

Users should receive only information required to perform authorized tasks.

Authorization Before Data Access

Data access must never occur before authorization evaluation.

Required order:

Authorize
      ↓
Access Data
Failure Policy
Fail Closed

Security failures result in denial.

Examples:

Authorization Failure
Authentication Failure
Constraint Evaluation Failure
Security Service Failure

Result:

DENY
Audit Failure Handling

Audit failures must not silently disappear.

Deployments may choose between:

Fail Operation
or
Queue Audit Event

but the policy must be explicit.

Policy Hierarchy

Policies are applied in the following order:

Authentication Policy
        ↓
Session Policy
        ↓
Authorization Policy
        ↓
Integration Policy
        ↓
Audit Policy

Lower-level policies must not weaken higher-level policies.

Security Policies Summary

AcCore Security Policies enforce the following platform-wide requirements:

Default Deny
Least Privilege
Separation Of Duties
Provider Independence
Centralized Authorization
Metadata-Based Security
No Runtime Bypass
Immutable Audit
Fail Closed

These policies define the mandatory security baseline for all AcCore deployments and future platform extensions.