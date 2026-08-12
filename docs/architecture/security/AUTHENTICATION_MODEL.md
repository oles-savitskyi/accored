AUTHENTICATION_MODEL.md
Purpose

The Authentication Model defines how identities are verified and converted into runtime Principals.

Authentication is responsible for establishing identity.

Authentication is not responsible for authorization decisions.

Architectural Principles
Authentication And Authorization Are Separate

Authentication answers:

Who are you?

Authorization answers:

What are you allowed to do?

These concerns must remain independent.

Principal Is The Authentication Result

Every successful authentication produces a Principal.

Identity
      ↓
Authentication
      ↓
Principal

The rest of the system operates exclusively with Principals.

Authentication Is Provider-Independent

The Runtime must not depend on a specific authentication mechanism.

Supported mechanisms may evolve without affecting business components.

Authentication Applies To All Entry Points

The same authentication principles apply to:

Desktop UI
Web UI
API
Background Jobs
External Integrations
Event Consumers
Authentication Flow

All authentication mechanisms follow the same conceptual process.

Credentials
        ↓
Authentication Provider
        ↓
Identity Verification
        ↓
Principal Creation
        ↓
Session Creation
Identity Types

AcCore recognizes multiple identity types.

User Identity

Represents a human user.

Examples:

john
mary
accountant

Typical authentication:

Username + Password
Service Account

Represents a non-human actor.

Examples:

inventory_sync
crm_connector
mobile_gateway

Typical authentication:

Service Secret
Token
Certificate
API Identity

Represents external API access.

Examples:

partner_system
ecommerce_platform
mobile_application

Typical authentication:

API Key
Bearer Token
OAuth Token
External Identity

Represents identities managed outside AcCore.

Examples:

LDAP User
OIDC User
OAuth User

Authentication is delegated to an external provider.

Authentication Providers

Authentication Providers verify credentials.

Local Provider

Credentials stored by AcCore.

Examples:

Login
Password Hash

Suitable for:

SMB Deployments
Single-Server Installations
Standalone Systems
LDAP Provider

External directory authentication.

Examples:

Active Directory
OpenLDAP
OAuth2 Provider

External token-based authentication.

Examples:

Corporate Identity Platform
Cloud Identity Provider
OpenID Connect Provider

Federated identity.

Examples:

Microsoft Entra ID
Keycloak
Google Identity
Principal Creation

After successful authentication, the system creates a Principal.

Conceptually:

Identity
      ↓
Principal

Principal contains:

principal_id
identity_id
identity_type
claims

Authorization data is resolved later.

Claims

Claims represent identity attributes.

Examples:

user_id
login
email
department
organization
identity_provider

Claims are identity facts.

Claims are not permissions.

Forbidden:

Claim = Permission

Allowed:

Claim -> Authorization Evaluation

through constraints and policies.

Session Creation

Successful authentication creates a Session.

Principal
      ↓
Session

Session contains:

session_id
principal_id
created_at
expires_at
last_activity_at
client_info
Session Lifecycle
Session Start

Created after successful authentication.

Session Renewal

Expiration may be extended according to security policy.

Session Expiration

Expired sessions become invalid.

Session Termination

May occur through:

Logout
Administrator Action
Security Policy
Credential Revocation
Authentication Failure

Authentication failure immediately terminates the request.

Authentication Failed
        ↓
DENY

Authorization is not evaluated.

Service Authentication

Service Accounts use the same model.

Service Credentials
        ↓
Authentication
        ↓
Principal
        ↓
Authorization

Services are first-class security subjects.

No special bypass mechanism exists.

API Authentication

API requests follow the same authentication pipeline.

API Token
        ↓
Authentication
        ↓
Principal
        ↓
Authorization

This supports the architectural principle:

Integration Never Bypasses Runtime
External Identity Integration

External providers authenticate users.

AcCore performs authorization.

Responsibilities:

External Provider
    ↓
Authentication

AcCore
    ↓
Authorization

This separation prevents security logic from leaking into identity providers.

Audit Integration

Authentication events produce audit records.

Examples:

Login Success
Login Failure
Session Created
Session Terminated
Token Revoked
Provider Failure

Audit storage is defined separately.

Authentication Model Summary

Authentication converts identities into Principals.

Identity
      ↓
Authentication
      ↓
Principal
      ↓
Session

Supported identity categories:

User
Service Account
API Identity
External Identity

Supported provider categories:

Local
LDAP
OAuth2
OpenID Connect

Authentication establishes identity only.

Authorization remains the responsibility of the Security Model and Authorization Model.