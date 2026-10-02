# AcCoreD → Phase 11
# Security — Concrete API Design

**Status:** Final Concrete API Design — Approved for Implementation

**Baseline:** `c19b1e5 — docs(processing): reconcile Phase 10 architecture`

**Architecture basis:** `PHASE_11_Security_Architecture_Definition_Scope.md`

**Implementation status:** Not started

---

## 1. Purpose

This document translates the approved Phase 11 Architecture Definition / Scope into a concrete Python API suitable for implementation.

The design introduces the first Platform Security contracts required by the Standard Edition while preserving the architecture established through Phase 10.

The design is intentionally explicit:

* no generic service container;
* no security bag passed through arbitrary business code;
* no role checks in business implementations;
* no policy scripting language;
* no transport-specific authentication;
* no security state inside `RuntimeConfigurationContext`;
* no implementation-class-based security identities.

The API is designed for the current repository and must be reconciled against actual integration points during implementation.

---

# 2. Package Structure

Phase 11 adds the following Platform package structure:

```text
src/accore/platform/security/
├── __init__.py
├── identity.py
├── principal.py
├── context.py
├── session.py
├── credentials.py
├── authentication.py
├── user.py
├── role.py
├── permission.py
├── object.py
├── operation.py
├── constraint.py
├── authorization.py
├── errors.py
├── persistence.py
└── events.py
```

The package remains Platform-owned.

Standard-specific composition is placed under:

```text
src/standard/security/
├── __init__.py
├── authentication.py
├── composition.py
├── definitions.py
└── persistence.py
```

The exact number of modules may be reduced during implementation if doing so preserves the contracts below. The public boundary, not file count, is normative.

---

# 3. Existing Integration Points

The current repository provides several relevant boundaries.

## 3.1 Runtime configuration

`RuntimeConfigurationContext` is already the immutable active configuration snapshot.

Phase 11 does **not** extend it with security state.

The protected execution model is:

```text
RuntimeConfigurationContext
        +
SecurityContext
        ↓
protected execution
```

## 3.2 Processing Runtime

The current `DefaultProcessingRuntime.execute(...)` resolves a Processing implementation, validates its identity, creates `ProcessingContext`, and invokes `processing.execute(...)`.

Phase 11 inserts authorization immediately before `ProcessingContext` construction / Processing invocation:

```text
ProcessingCommand
      ↓
resolve Processing
      ↓
resolve SecurityObject
      ↓
authorize
      ↓
create ProcessingContext
      ↓
processing.execute(...)
```

Authorization failure therefore occurs before the protected business operation starts.

## 3.3 Processing Context

The existing `ProcessingContext` contains execution identity, runtime configuration, parameters, and progress observer.

Phase 11 extends it with:

```python
security: SecurityContext
```

The Processing implementation may inspect security context for legitimate contextual information, but it must not perform authorization checks.

## 3.4 Reporting

The current Reporting runtime executes immutable report plans through `ReportRuntime`.

Phase 11 does not redesign Reporting. A future protected report entry point can reuse the same `AuthorizationService` contract.

The first Standard protected report permission is represented as a security permission, while enforcement is limited to an actual integration point selected during implementation if a report execution boundary is exposed as part of the MVP.

## 3.5 Standard Bootstrap

`StandardConfigurationBootstrap` is the existing Standard composition boundary.

Security composition is added there or through a dedicated Standard security composition object called by the bootstrap. Standard must provide definitions and concrete adapters, but must not implement authorization evaluation.

---

# 4. Identity Model

## 4.1 Persistent security identities

Persistent security entities use the existing immutable `Identifier` type directly.

`Identifier` is the authoritative identity type for User, Role, Session, Permission, and
other persisted security records. No additional `SecurityIdentity` wrapper is introduced.

Logical security targets remain represented separately by `SecurityObjectIdentity`, because
they are semantic object/operation targets rather than persistence identities.

---

# 5. User

`User` is the persistent security subject used by the local Standard authentication provider.

```python
@dataclass(frozen=True, slots=True)
class User:
    identity: Identifier
    login: str
    display_name: str
    email: str | None
    active: bool
    role_ids: tuple[Identifier, ...]
```

### Invariants

* `identity` is stable and unique.
* `login` is non-empty and uniquely resolved by the authentication boundary.
* `role_ids` is normalized to a tuple.
* inactive users cannot authenticate successfully.
* a User does not directly contain effective permissions.
* a User does not contain password material.

Role membership is configuration/security data, not business logic.

A User may have zero or more roles.

---

# 6. Principal

`Principal` is the runtime authenticated identity.

```python
class PrincipalType(StrEnum):
    USER = "user"
    SERVICE = "service"
    EXTERNAL = "external"

@dataclass(frozen=True, slots=True)
class Principal:
    identity: Identifier
    identity_type: PrincipalType
    claims: tuple[SecurityClaim, ...] = ()
```

Claims are explicit immutable identity facts. They are opaque authentication attributes in
Phase 11 and have no implicit authorization semantics. Claim-based authorization exists only
if a concrete MVP constraint explicitly consumes a claim.

```python
@dataclass(frozen=True, slots=True)
class SecurityClaim:
    name: str
    value: str
```

The MVP creates `PrincipalType.USER` principals.

Service and external principals remain representable but do not require concrete authentication providers in Phase 11.

### Important separation

`Principal` does not contain:

* password material;
* authorization decisions;
* mutable session state;
* Python user objects;
* business objects.

Role and permission resolution is performed by authorization infrastructure from authoritative security configuration.

---

# 7. Session

A session is a runtime authentication artifact separate from the Principal.

```python
class SessionState(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"

@dataclass(frozen=True, slots=True)
class Session:
    identity: Identifier
    principal_identity: Identifier
    created_at: datetime
    expires_at: datetime
    state: SessionState
```

The MVP uses an in-process session store.

A distributed or durable session subsystem is explicitly deferred.

The session abstraction remains separate so future authentication providers can reuse authorization without changing the Principal contract.

---

# 8. SecurityContext

`SecurityContext` is the immutable execution-level security snapshot.

```python
@dataclass(frozen=True, slots=True)
class SecurityContext:
    principal: Principal | None
    session: Session | None
    request_identity: Identifier | None = None
```

### Semantics

* authenticated protected execution requires a non-`None` Principal;
* session may be `None` for future non-session authentication mechanisms;
* request identity is correlation metadata, not an authorization credential;
* credentials are never stored in the context;
* the context is immutable;
* effective permissions are not copied into the context.

Anonymous execution is represented by `principal=None` rather than by a fake anonymous Principal.

This makes unauthenticated access naturally default-deny.

---

# 9. Security Objects

A `SecurityObject` identifies a protected logical target.

```python
@dataclass(frozen=True, slots=True)
class SecurityObjectIdentity:
    object_type: str
    object_code: str
```

Validation requires both values to be non-empty.

Examples:

```text
Processing / inventory.rebuild
Report / inventory.balance
System / security
```

The identity is deliberately independent of implementation classes.

A Python class such as `InventoryDerivedStateRebuildProcessing` is never itself the security object.

---

# 10. Operations

Operations are Platform-defined semantic actions.

```python
class SecurityOperation(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    POST = "post"
    UNPOST = "unpost"
    APPROVE = "approve"
    CLOSE = "close"
    CONFIGURE = "configure"
    ADMINISTER = "administer"
    MANAGE_USERS = "manage_users"
    IMPORT = "import"
    EXPORT = "export"
    INVOKE = "invoke"
```

Phase 11 does not require all operations to be used.

Standard initially uses:

```text
Execute
Read
Administer
```

The enum is Platform-owned so Standard cannot redefine operation semantics.

---

# 11. Permission

A Permission is the atomic authorization grant.

```python
@dataclass(frozen=True, slots=True)
class Permission:
    identity: Identifier
    target: SecurityObjectIdentity
    operation: SecurityOperation
    constraints: tuple[AuthorizationConstraint, ...] = ()
```

Its semantic key is:

```text
SecurityObjectIdentity + SecurityOperation
```

The `identity` provides persistent identity for configuration records.

The target/operation pair provides semantic matching.

### Permission equality

Two permissions are semantically equivalent only when their target, operation, and constraint definitions are equivalent. Constraint evaluation order is deterministic, but authorization semantics do not depend on a special ordering between otherwise equivalent constraints.

No wildcard permission is introduced in Phase 11.

No implicit administrative permission exists.

---

# 12. Role

A Role aggregates permissions.

```python
@dataclass(frozen=True, slots=True)
class Role:
    identity: Identifier
    code: str
    name: str
    permissions: tuple[Permission, ...]
```

Role invariants:

* code is non-empty;
* permissions are normalized to a tuple;
* roles contain no business behavior;
* permissions are explicit;
* role inheritance is not introduced;
* wildcard permissions are not introduced.

A Principal receives effective permissions through the roles assigned to its User/security subject.

Effective permission set semantics are the union of all assigned role permissions.

---

# 13. Permission Resolution

Authorization receives a Principal and resolves roles through explicit repository dependencies.

The Platform contract is:

```python
class SecurityAuthorizationState(Protocol):
    def user_for_principal(self, principal: Principal) -> User: ...

    def role(self, identity: Identifier) -> Role: ...
```

The resolver must fail rather than inventing permissions when authoritative security configuration cannot be resolved.

A missing User, missing Role, malformed role assignment, or unavailable state is a security infrastructure failure, not an ALLOW condition.

For `PrincipalType.USER`, the MVP invariant is `Principal.identity == User.identity`.
`user_for_principal()` therefore resolves the persistent User represented by the authenticated
Principal without introducing a second identity-mapping namespace. Other Principal types remain
representable but are not required to have concrete authorization state in Phase 11.

No global registry is introduced.

No service locator is introduced.

---

# 14. Authorization Request

The evaluator receives an explicit immutable request.

```python
@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    context: SecurityContext
    target: SecurityObjectIdentity
    operation: SecurityOperation
    resource: AuthorizationResource | None = None
```

The optional resource carries only explicit contextual data required by an implemented constraint.

It is not a generic service bag. Its `identity` identifies the contextual resource instance,
but it does not participate in basic permission matching: matching remains exactly
`target + operation`.

The Phase 11 MVP does not require a general-purpose resource object hierarchy. The initial Standard configuration may use `None` because the selected MVP permissions are object/operation based.

If a contextual constraint is introduced during implementation, it must define a typed resource contract rather than use `Mapping[str, object]`.

---

# 15. Authorization Resource

The architecture supports contextual constraints without introducing a policy DSL.

The base contract is:

```python
class AuthorizationResource(Protocol):
    @property
    def identity(self) -> SecurityObjectIdentity: ...
```

Concrete resource types are introduced only when an actual MVP constraint requires them.

No generic dictionary-based resource context is part of the public API.

---

# 16. Constraint Contract

Constraints are explicit executable contracts.

```python
class AuthorizationConstraint(Protocol):
    @property
    def code(self) -> str: ...

    def evaluate(self, request: AuthorizationRequest) -> bool: ...
```

A constraint returns only whether its condition is satisfied.

It must not grant access independently of a Permission.

### Constraint semantics

```text
matching Permission
AND
all Permission constraints return True
        ↓
      ALLOW
```

Otherwise:

```text
DENY
```

### Failure semantics

If a constraint cannot evaluate because required contextual data is absent or invalid, it produces DENY rather than ALLOW.

Unexpected infrastructure failures are represented separately by security infrastructure exceptions.

### No DSL

Constraint implementations are Python contracts, not user-supplied expressions.

No `eval`, expression parser, policy compiler, or arbitrary script execution is introduced.

---

# 17. MVP Constraint

The Phase 11 MVP does not require a data-scope constraint for the selected protected operations.

Therefore the initial implementation may contain the constraint contract and tests for:

1. no constraints → permission may allow;
2. a passing constraint → permission may allow;
3. a failed constraint → DENY.

A concrete Standard constraint is added only if the implementation selects an MVP operation whose authorization genuinely requires contextual scope.

This keeps the Phase 11 implementation small while preserving the approved architecture.

---

# 18. Authorization Decision

Authorization returns an explicit immutable decision.

```python
class AuthorizationOutcome(StrEnum):
    ALLOW = "allow"
    DENY = "deny"

class AuthorizationDenyReason(StrEnum):
    UNAUTHENTICATED = "unauthenticated"
    INACTIVE_PRINCIPAL = "inactive_principal"
    MISSING_PERMISSION = "missing_permission"
    CONSTRAINT_FAILED = "constraint_failed"

@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    outcome: AuthorizationOutcome
    reason: AuthorizationDenyReason | None
```

Invariants:

* `ALLOW` has `reason=None`;
* `DENY` has a non-`None` reason;
* an infrastructure failure is not encoded as `ALLOW` or ordinary `DENY`.

This distinction is important for observability and failure handling.

---

# 19. Authorization Service

The central authorization boundary is:

```python
class AuthorizationService(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision: ...

    def require(self, request: AuthorizationRequest) -> None: ...
```

`authorize` is non-throwing for normal access decisions.

`require` is the enforcement-oriented operation used by protected runtime boundaries.

Semantics:

```text
ALLOW → return normally
DENY  → raise AuthorizationDeniedError
```

Infrastructure/security-state failures propagate as security infrastructure errors.

---

# 20. Default Authorization Evaluator

The first implementation is:

```python
@dataclass(frozen=True, slots=True)
class DefaultAuthorizationService:
    state: SecurityAuthorizationState
```

The evaluator performs these steps in order:

1. verify that the SecurityContext contains an authenticated Principal;
2. resolve the authoritative User/security subject;
3. verify the security subject is active;
4. resolve assigned roles;
5. match permissions by exact SecurityObject + Operation;
6. if no matching permission exists, return DENY/MISSING_PERMISSION;
7. evaluate each matching permission independently; all constraints belonging to one
   permission must pass for that permission to grant access;
8. if at least one matching permission passes all of its constraints, return ALLOW;
9. otherwise return DENY/CONSTRAINT_FAILED.

Unknown target/operation has no implicit permission and therefore defaults to
DENY/MISSING_PERMISSION.

If the state resolver itself is unavailable or inconsistent, a `SecurityInfrastructureError` propagates rather than being silently converted to ALLOW.

---

# 21. Multiple Matching Permissions

A Principal may receive the same semantic permission through multiple roles.

Matching semantics are additive and are formally evaluated as:

```text
for each matching Permission:
    permission_grants = all(constraint.evaluate(request) for constraint in permission.constraints)

ALLOW if any(permission_grants) is True
DENY/CONSTRAINT_FAILED otherwise
```

Thus authorization is **OR across matching permissions** and **AND across constraints within
one permission**. A failed constrained permission does not turn an otherwise independent
matching unconstrained permission into DENY.

Example:

```text
Role A → Report.InventoryBalance.Read
Role B → Report.InventoryBalance.Read + OwnWarehouse
```

The unconstrained permission from Role A is sufficient for ALLOW.

This follows the role/permission union model and avoids accidental deny-overrides semantics that were not specified by the architecture.

If multiple matching permissions are semantically identical, duplicate grants are harmless.

---

# 22. Security Errors

The security package defines explicit errors.

```python
class SecurityError(AcCoreError):
    """Base security error."""

class AuthenticationError(SecurityError):
    """Base authentication error."""

class AuthenticationFailedError(AuthenticationError):
    """Credentials or identity verification failed."""

class AuthenticationConfigurationError(AuthenticationError):
    """Authentication configuration is invalid or unavailable."""

class AuthorizationDeniedError(SecurityError):
    """A protected operation was denied."""

class SecurityInfrastructureError(SecurityError):
    """Authoritative security state cannot be evaluated safely."""

class SecurityConfigurationError(SecurityError):
    """Security configuration is invalid or inconsistent."""
```

`AuthorizationDeniedError` contains the immutable `AuthorizationDecision` so callers can distinguish unauthenticated, missing permission, and failed constraint cases.

Security infrastructure errors are never translated into success.

---

# 23. Authentication Credentials

Authentication receives an explicit credential contract.

For the local MVP:

```python
@dataclass(frozen=True, slots=True)
class PasswordCredentials:
    login: str
    password: str
```

The credential object exists only at the authentication boundary.

It must not be placed in:

* `SecurityContext`;
* `Principal`;
* `ProcessingContext`;
* business objects;
* audit events.

The provider must not return password material.

---

# 24. Password Hash Contract

Credential persistence stores a one-way password verifier representation.

```python
@dataclass(frozen=True, slots=True)
class PasswordVerifier:
    value: str
```

`PasswordVerifier` is an opaque persisted one-way representation. The Platform API does not
expose or mandate a concrete password-hashing algorithm. Standard supplies the concrete
production-grade salted password hashing/verification adapter. Clear-text passwords are never
persisted.

The Platform does not prescribe a concrete password hashing algorithm in the authorization contracts.

The Standard local provider must use a production-grade salted, non-reversible password hashing implementation.

Clear-text passwords are never persisted.

A password verifier is never exposed outside authentication infrastructure.

---

# 25. Authentication Provider

The provider boundary is:

```python
class AuthenticationProvider(Protocol):
    def authenticate(
        self,
        credentials: PasswordCredentials,
    ) -> AuthenticationResult: ...
```

The provider is responsible for:

* locating the identity;
* checking active state;
* verifying credentials;
* constructing the Principal;
* creating a Session when the provider uses sessions.

The provider is not responsible for authorization decisions.

---

# 26. Authentication Result

Successful authentication returns an immutable result.

```python
@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    principal: Principal
    session: Session | None
```

Failed authentication raises `AuthenticationFailedError`.

No partially authenticated Principal is returned.

No authorization data is copied into the authentication result.

---

# 27. Local Authentication Provider

Standard supplies:

```python
@dataclass(frozen=True, slots=True)
class LocalAuthenticationProvider:
    users: UserRepository
    credentials: CredentialRepository
    sessions: SessionStore
```

The provider flow is:

```text
PasswordCredentials
      ↓
UserRepository.find_by_login
      ↓
active user?
      ↓
CredentialRepository.verifier
      ↓
password verification
      ↓
Principal
      ↓
SessionStore.create
      ↓
AuthenticationResult
```

For a failed login, the external contract is a single authentication failure outcome. The implementation must not reveal whether the login exists, whether the user is inactive, or whether the password was incorrect through separate public exception types.

This prevents credential-enumeration information from becoming part of the authentication API.

---

# 28. Authentication Persistence Boundaries

Security persistence is explicit and independent from business persistence.

```python
class UserRepository(Protocol):
    def find_by_login(self, login: str) -> User | None: ...

    def get(self, identity: Identifier) -> User: ...


class CredentialRepository(Protocol):
    def get_password_verifier(self, user_identity: Identifier) -> PasswordVerifier: ...


class RoleRepository(Protocol):
    def get(self, identity: Identifier) -> Role: ...


class SessionStore(Protocol):
    def create(self, principal: Principal, now: datetime) -> Session: ...

    def get(self, identity: Identifier) -> Session | None: ...

    def invalidate(self, identity: Identifier) -> None: ...
```

The MVP may implement these repositories in memory.

The contracts intentionally do not reuse `RegisterFactPersistence`, valuation persistence, object persistence, or other business persistence interfaces.

---

# 29. Session Validation

The authentication/session boundary owns session validation. Before an authenticated
`AuthenticationResult` is exposed to a protected caller, the authentication boundary must
ensure that the associated session is valid according to the active session policy.

`SecurityContextFactory` is deliberately a construction boundary only: it copies the
authenticated Principal and Session into an immutable context and does not perform repository
lookups or session validation.

The resulting `SecurityContext` is an authenticated snapshot for the protected execution.
If a future durable session model requires live revocation checks, that behavior belongs to
the authentication/security boundary rather than business operations.

---

# 30. Security Context Construction

The security boundary exposes an explicit factory/service:

```python
class SecurityContextFactory(Protocol):
    def from_authentication(
        self,
        result: AuthenticationResult,
        request_identity: Identifier | None = None,
    ) -> SecurityContext: ...
```

The Standard MVP can use a simple implementation that copies the authenticated Principal and Session references into an immutable context.

No credentials enter the context.

---

# 31. Processing Authorization Integration

The current Processing API must be extended minimally.

Current conceptual signature:

```python
ProcessingRuntime.execute(command, progress_observer=None)
```

Concrete Phase 11 signature:

```python
class ProcessingRuntime(Protocol):
    def execute(
        self,
        command: ProcessingCommand,
        security: SecurityContext,
        progress_observer: ProcessingProgressObserver | None = None,
    ) -> ProcessingResult[object]: ...
```

`SecurityContext` is explicit and mandatory for protected runtime execution.

No implicit global security context is introduced.

`SecurityContext` is an execution-boundary concern and is **not** added to
`ProcessingCommand`; the command remains a description of the requested Processing operation,
while the caller supplies the authenticated execution context separately.

---

# 32. Processing Runtime Authorization Sequence

`DefaultProcessingRuntime.execute(...)` performs:

```text
1. resolve Processing by command.processing_identity
2. validate Processing definition identity
3. resolve protected SecurityObject
4. construct AuthorizationRequest
5. authorization.require(...)
6. create ProcessingContext including SecurityContext
7. invoke Processing.execute(...)
```

The critical invariant is:

```text
authorization.require(...)
        ↓
ProcessingContext creation
        ↓
processing.execute(...)
```

not:

```text
ProcessingContext
        ↓
processing.execute(...)
        ↓
authorize
```

Authorization denial therefore cannot execute the protected business operation.

---

# 33. Processing Security Object Mapping

Processing security objects are derived from `ProcessingIdentity`.

For the existing Standard processing:

```text
ProcessingIdentity.value
    inventory.rebuild

becomes

SecurityObjectIdentity(
    object_type="Processing",
    object_code="inventory.rebuild",
)
```

The mapping is deterministic and does not inspect the Python implementation class.

The mapping must be centralized in the Processing runtime/security integration rather than repeated inside individual Processing implementations.

---

# 34. ProcessingContext Extension

The concrete context becomes:

```python
@dataclass(frozen=True, slots=True)
class ProcessingContext[P]:
    execution_identity: ProcessingExecutionIdentity
    runtime_configuration: RuntimeConfigurationContext
    security: SecurityContext
    parameters: P
    progress_observer: ProcessingProgressObserver
```

No security service is added to the context.

No authorization method is added to ProcessingContext.

No role or permission collections are copied into ProcessingContext.

---

# 35. Processing Identity and Security Identity

The existing `ProcessingIdentity` remains the authoritative Processing identity.

Security creates a stable mapping:

```text
ProcessingIdentity
        ↓
SecurityObjectIdentity
```

The security subsystem must not replace Processing identity with a second unrelated identifier.

This preserves Phase 10's metadata/runtime identity model.

---

# 36. Standard Protected Processing Permission

The first concrete Standard protected permission is:

```text
Processing.inventory.rebuild.Execute
```

represented by:

```python
Permission(
    identity=Identifier.new(),
    target=SecurityObjectIdentity("Processing", "inventory.rebuild"),
    operation=SecurityOperation.EXECUTE,
)
```

The persistent Permission identity is configuration data; the semantic target/operation pair is the authorization key.

---

# 37. Standard Report Permission

The Standard configuration also defines a report read/execute permission for the inventory balance report where an actual report execution boundary is exposed.

Canonical target:

```text
Report.inventory.balance
```

with:

```text
SecurityOperation.READ
```

or `EXECUTE` if the actual protected operation is report execution rather than resource reading.

The implementation must choose the operation that corresponds to the actual runtime boundary and must not create a permission that is never enforceable.

This permission is part of the Standard security vocabulary, but the first vertical enforcement test may use Processing because its runtime boundary already exists.

---

# 38. Standard Security Administration Permission

The Standard security model defines:

```text
System.security.Administer
```

with:

```text
SecurityOperation.ADMINISTER
```

This permission is used to validate the administrative authorization model in unit/integration tests.

Phase 11 does not implement a full security administration UI.

---

# 39. Standard Roles

The first Standard role set is intentionally small.

### Standard Administrator

```text
Role code: standard.administrator
```

Permissions:

```text
Processing.inventory.rebuild.Execute
Report.inventory.balance.Read
System.security.Administer
```

### Standard Operator

```text
Role code: standard.operator
```

Permissions:

```text
Processing.inventory.rebuild.Execute
```

### Standard Auditor

```text
Role code: standard.auditor
```

Permissions:

```text
Report.inventory.balance.Read
```

These are composition examples for the MVP, not a permanent Standard role taxonomy.

Standard may add or rename roles during implementation if the actual protected operation set requires it, but the authorization algorithm remains Platform-owned.

---

# 40. Standard Security Composition

The Standard bootstrap must compose security explicitly.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class StandardSecurityComposition:
    authentication: AuthenticationProvider
    authorization: AuthorizationService
    context_factory: SecurityContextFactory
```

A concrete composition function may be:

```python
class StandardConfigurationBootstrap:
    def compose_security(self) -> StandardSecurityComposition: ...
```

The composition creates:

* Standard users;
* Standard roles;
* Standard permissions;
* local authentication provider;
* in-memory security repositories;
* authorization service;
* context factory.

No Standard evaluator is created.

---

# 41. Standard Security Definitions

Standard security definitions are configuration data.

A dedicated module may expose:

```python
def standard_security_users() -> tuple[User, ...]: ...

def standard_security_roles() -> tuple[Role, ...]: ...
```

These functions return immutable definitions.

They do not execute authorization.

They do not inspect business state.

They do not import Processing implementation classes merely to define permissions.

Where a protected operation identity is needed, Standard uses the stable semantic identity already exposed by the corresponding Platform contract.

---

# 42. Security Configuration State

The Standard in-memory authorization state can be represented by an explicit object:

```python
@dataclass(frozen=True, slots=True)
class InMemorySecurityAuthorizationState:
    users: tuple[User, ...]
    roles: tuple[Role, ...]
```

Lookup indexes are implementation details.

The public authorization contract remains `SecurityAuthorizationState`.

No mutable global singleton is permitted.

---

# 43. Standard Credential State

Standard test/bootstrap users require credentials, but credential state remains separate from User.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class StandardCredential:
    user_identity: Identifier
    verifier: PasswordVerifier
```

A Standard in-memory `CredentialRepository` supplies verifiers to the local authentication provider.

No password appears in `User`, `Role`, `Principal`, or `SecurityContext`.

Test fixtures may create password verifiers using the same production hashing boundary rather than storing clear-text fixture credentials as repository state.

---

# 44. Authentication and Authorization Composition

The complete protected flow is:

```text
Credentials
    ↓
AuthenticationProvider
    ↓
AuthenticationResult
    ↓
SecurityContextFactory
    ↓
SecurityContext
    ↓
ProcessingRuntime
    ↓
AuthorizationService.require
    ↓
ProcessingContext
    ↓
Processing.execute
```

The two security responsibilities remain distinct:

```text
Authentication → establishes identity
Authorization → evaluates permission
```

---

# 45. Security Event Boundary

Phase 11 provides an explicit event-emission boundary without implementing durable Audit persistence.

```python
class SecurityEventSink(Protocol):
    def emit(self, event: SecurityEvent) -> None: ...
```

Events are immutable.

```python
class SecurityEventType(StrEnum):
    AUTHENTICATION_SUCCEEDED = "authentication_succeeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_DENIED = "authorization_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    SECURITY_ADMINISTRATION_CHANGED = "security_administration_changed"
    SESSION_INVALIDATED = "session_invalidated"
```

The base event uses a typed outcome:

```python
class SecurityEventOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"

@dataclass(frozen=True, slots=True)
class SecurityEvent:
    event_type: SecurityEventType
    timestamp: datetime
    actor: Principal | None
    target: SecurityObjectIdentity | None
    operation: SecurityOperation | None
    outcome: SecurityEventOutcome
```

No credentials are included.

No durable audit repository is introduced by this phase.

A no-op sink may be used where no audit integration is configured.

---

# 46. Audit Event Semantics

Security events are observational.

They must never become business state.

Authorization must not query audit history to make a decision.

Authentication failure events must not contain password values.

Authorization denial events should contain the target, operation, principal identity where available, and denial outcome/reason through structured event fields or a dedicated typed event subtype.

The final event payload must remain explicit; no unrestricted `details: object` field is introduced.

---

# 47. Error vs Denial Boundary

The implementation must preserve this distinction:

### Normal denial

```text
unauthenticated
inactive user
missing permission
failed constraint
unknown protected target
        ↓
AuthorizationDecision.DENY
        ↓
AuthorizationDeniedError at enforcement boundary
```

### Security infrastructure failure

```text
security state unavailable
corrupt security configuration
repository failure
invalid internal security invariant
        ↓
SecurityInfrastructureError / SecurityConfigurationError
```

Neither path can produce ALLOW.

This distinction is required so callers can distinguish an expected access-control rejection from a security subsystem failure.

---

# 48. Unknown Security Objects

Unknown objects and operations are fail-closed.

The evaluator does not require a separate registry containing every possible security object.
A request matches a permission only if an explicit permission exists with exactly matching target
and operation.

Therefore:

```text
unknown target + no matching permission
        ↓
DENY / MISSING_PERMISSION
```

The MVP does not define a separate `UNKNOWN_TARGET` denial reason and does not require a
global target registry.

---

# 49. Permission Matching Algorithm

The exact algorithm is:

```text
Input:
    SecurityContext
    target
    operation

1. principal must exist
2. principal's User must resolve
3. User must be active
4. every assigned Role must resolve
5. collect all Role.permissions
6. select permissions where:
       permission.target == target
       AND
       permission.operation == operation
7. if none:
       DENY(MISSING_PERMISSION)
8. for each matching permission:
       if all constraints pass:
           ALLOW
9. otherwise:
       DENY(CONSTRAINT_FAILED)
```

This is deterministic for a fixed security state and request.

No permission inheritance, wildcard expansion, role hierarchy, or deny rules are evaluated.

---

# 50. Role Assignment Changes

Because effective permissions are resolved from authoritative role state during authorization, role changes apply to subsequent authorization calls without rebuilding Principals.

The Principal therefore does not cache roles or permissions.

This satisfies the requirement that role/permission changes affect subsequent access evaluation.

A future optimized cache must preserve the same observable semantics and is outside Phase 11.

---

# 51. SecurityContext Immutability

`SecurityContext`, `Principal`, `Session`, `User`, `Role`, `Permission`, and authorization decisions are all frozen dataclasses with tuple-based collections.

No security object exposes mutable role or permission lists.

The implementation must defensively normalize incoming sequences to tuples.

This prevents a caller from changing authorization inputs after a protected execution begins.

---

# 52. Thread/Execution Safety

Security contracts are immutable and therefore safe to pass across execution boundaries as snapshots.

The implementation must not use module-level mutable current-user state.

No `contextvars`-based implicit global Principal is required by Phase 11.

Explicit context passing remains the project-wide dependency model.

---

# 53. API Exports

`accore.platform.security.__init__` should expose the public security contracts needed by callers.

At minimum:

```text
AuthenticationProvider
AuthenticationResult
AuthorizationConstraint
AuthorizationDecision
AuthorizationDeniedError
AuthorizationOutcome
AuthorizationRequest
AuthorizationService
DefaultAuthorizationService
PasswordCredentials
PasswordVerifier
Permission
Principal
PrincipalType
Role
SecurityAuthorizationState
SecurityClaim
SecurityContext
SecurityContextFactory
SecurityEvent
SecurityEventSink
SecurityEventType
SecurityEventOutcome
SecurityInfrastructureError
SecurityObjectIdentity
SecurityOperation
SecurityError
Session
SessionState
User
```

Internal repository implementations and Standard composition helpers need not be re-exported from Platform package root unless they are intentionally public.

---

# 54. API Compatibility Rules

The implementation must preserve the existing architecture conventions:

* frozen/slot dataclasses for immutable value objects;
* explicit typed dependencies;
* Protocols for replaceable infrastructure boundaries;
* dedicated domain errors;
* no `Mapping[str, Any]` security API;
* no generic `details: object` diagnostics;
* no unrestricted service bags;
* no global registries as hidden dependencies.

Any unavoidable compatibility change to existing Processing signatures must be explicit and covered by tests.

---

# 55. Processing Runtime Constructor

The current constructor accepts only the Processing mapping.

Concrete Phase 11 design:

```python
class DefaultProcessingRuntime:
    def __init__(
        self,
        processings: Mapping[ProcessingIdentity, Processing[object, object]],
        authorization: AuthorizationService,
    ) -> None: ...
```

The runtime therefore owns an explicit authorization dependency.

It does not own authentication.

Authentication is performed by the entry point that creates the `SecurityContext`.

This preserves separation of responsibilities.

---

# 56. Processing Runtime Failure Ordering

The runtime must retain existing Processing lookup/definition validation semantics.

The ordering is:

```text
resolve processing
    ↓
validate definition identity
    ↓
authorize
    ↓
create context
    ↓
execute
```

This means an invalid Processing identity remains a Processing resolution error, while a valid Processing requested by an unauthorized Principal produces an authorization denial.

No business execution occurs after denial.

---

# 57. Authentication Entry Point Ownership

Phase 11 does not create a general Application Runtime.

A caller responsible for authentication must:

1. obtain credentials;
2. invoke `AuthenticationProvider.authenticate`;
3. create `SecurityContext`;
4. invoke the protected runtime with that context.

Future API transport integration may perform the same sequence.

The transport itself is outside Phase 11.

---

# 58. Anonymous Calls

An anonymous caller may construct:

```python
SecurityContext(
    principal=None,
    session=None,
)
```

Passing this context to a protected Processing operation results in:

```text
AuthorizationDecision(
    outcome=DENY,
    reason=UNAUTHENTICATED,
)
```

and then `AuthorizationDeniedError` at the enforcement boundary.

No special anonymous role exists.

---

# 59. Inactive Users

An inactive User cannot authenticate successfully.

If an already-created authenticated context refers to an inactive subject due to a security-state change, the authorization state resolver must return DENY/INACTIVE_PRINCIPAL or raise a security-state error according to the authoritative repository state.

The implementation must not continue to grant permissions to a known inactive subject.

---

# 60. Credential Revocation

Credential revocation in the MVP is represented by User active state and credential replacement/invalidation in the authentication repository.

No password history or advanced policy engine is required.

Changing a credential does not require changes to authorization contracts.

---

# 61. Password Policy Boundary

The architecture permits configurable password policy, but Phase 11 does not require a broad policy subsystem.

If Standard needs password validation for user creation, it should be a small authentication/configuration contract rather than logic embedded in User or authorization code.

No password policy values are hardcoded into business modules.

---

# 62. Security Persistence Evolution

The persistence protocols are intentionally narrow so a future durable provider can replace in-memory implementations without changing authorization semantics.

The expected future mapping is:

```text
UserRepository
CredentialRepository
RoleRepository
SessionStore
        ↓
Durable Security Storage
```

The authorization evaluator remains unchanged.

Phase 11 does not prescribe a database schema.

---

# 63. Security Administration Boundary

No full administration service is required, but the permission vocabulary must support administrative actions.

If implementation tests need to exercise administration, a minimal explicit contract may be introduced:

```python
class SecurityAdministrationService(Protocol):
    def assign_role(
        self,
        actor: SecurityContext,
        user_identity: Identifier,
        role_identity: Identifier,
    ) -> None: ...
```

Its first statement must be an authorization requirement for:

```text
System.security.Administer
```

This service is optional until an actual Phase 11 test or Standard bootstrap integration needs it.

It must not become a generic CRUD security administration framework.

---

# 64. Protected Operation Test Fixture

The core vertical test uses a Processing implementation whose execution has an observable side effect in the test fixture.

Example:

```text
authorized Principal
    ↓
ProcessingRuntime.execute
    ↓
side effect occurs
```

and:

```text
unauthorized Principal
    ↓
ProcessingRuntime.execute
    ↓
AuthorizationDeniedError
    ↓
side effect count remains zero
```

The test must prove enforcement ordering, not merely inspect the returned decision.

---

# 65. Authentication Tests

At minimum:

1. valid credentials produce Principal + Session;
2. invalid credentials raise `AuthenticationFailedError`;
3. inactive user cannot authenticate;
4. authentication result contains no credentials;
5. Principal contains identity/claims but no permissions;
6. session is associated with the returned Principal;
7. failed authentication does not create a usable authenticated context.

---

# 66. Authorization Unit Tests

At minimum:

1. authenticated Principal + matching permission → ALLOW;
2. no Principal → DENY/UNAUTHENTICATED;
3. missing permission → DENY/MISSING_PERMISSION;
4. matching permission with passing constraint → ALLOW;
5. matching permission with failed constraint → DENY/CONSTRAINT_FAILED;
6. multiple roles union permissions;
7. duplicate grants do not change the result;
8. role change affects subsequent evaluation;
9. unknown target is denied;
10. security repository failure raises infrastructure error;
11. infrastructure error never becomes ALLOW;
12. unconstrained matching permission can allow even if another matching constrained permission fails.

---

# 67. Processing Integration Tests

At minimum:

1. runtime accepts explicit SecurityContext;
2. authorized context reaches Processing;
3. unauthorized context raises before Processing execution;
4. unauthorized execution produces no protected side effect;
5. SecurityContext reaches ProcessingContext;
6. Processing implementation can inspect security context without an authorization service;
7. runtime does not perform authentication itself;
8. Processing resolution errors retain existing semantics.

---

# 68. Standard Integration Tests

At minimum:

1. Standard security composition creates users, roles, permissions, and local authentication provider;
2. Standard Administrator authenticates successfully;
3. Standard Operator authenticates successfully;
4. Standard Auditor authenticates successfully;
5. Operator can execute `inventory.rebuild`;
6. Auditor cannot execute `inventory.rebuild`;
7. Auditor can receive the inventory balance read permission;
8. Administrator can receive the security administration permission;
9. a user without the permission is denied;
10. role assignment changes affect the next authorization call;
11. Standard contains no independent authorization evaluator.

---

# 69. Security Architectural Tests

The implementation should include architectural tests where practical to prevent prohibited coupling.

Examples:

* Security package does not import Inventory/Valuation/Register implementation modules;
* Processing implementation modules do not import authorization evaluator classes;
* Standard security composition imports Platform security contracts but does not implement evaluator logic;
* no security contract depends on concrete HTTP/API framework types;
* no security contract depends on a database ORM;
* no credential-bearing type is imported by business Processing modules.

These tests protect the architecture rather than individual business behavior.

---

# 70. Test Matrix

| Area | Unit | Platform Integration | Standard Vertical |
|---|---:|---:|---:|
| Principal | yes | yes | yes |
| SecurityContext | yes | yes | yes |
| Local authentication | yes | yes | yes |
| User/role resolution | yes | yes | yes |
| Permission matching | yes | yes | yes |
| Constraint evaluation | yes | yes | optional MVP path |
| Default deny | yes | yes | yes |
| Authorization errors | yes | yes | yes |
| Processing enforcement | — | yes | yes |
| Security event emission | yes | yes | optional |
| Security persistence boundary | yes | yes | yes |
| Architectural independence | — | yes | yes |

---

# 71. No Authorization Cache in Phase 11

The default implementation performs permission resolution from authoritative in-memory security state for each decision.

No distributed cache, permission cache, invalidation protocol, or compiled authorization graph is introduced.

This is intentional.

The resulting semantics are simple and deterministic:

```text
current security state
        ↓
authorization request
        ↓
decision
```

---

# 72. No Role Hierarchy

Role inheritance is not part of the API.

If an administrator requires operator permissions, those permissions are explicitly included in the administrator role.

This avoids introducing inheritance semantics that would complicate permission resolution without an MVP requirement.

---

# 73. No Deny Permissions

Phase 11 defines only positive permissions.

There is no explicit DENY permission.

The access rule is:

```text
matching positive permission
AND
passing constraints
        ↓
ALLOW
```

otherwise DENY.

This keeps the evaluator deterministic and avoids deny-overrides precedence rules.

---

# 74. No Wildcards

Permissions match exactly:

```text
SecurityObjectIdentity
+
SecurityOperation
```

There is no:

```text
Processing.*.Execute
System.*.Administer
*.Read
```

in Phase 11.

If broader permission grouping becomes necessary, it should be designed explicitly in a later phase.

---

# 75. No Security Logic in Processing

The following is prohibited:

```python
if context.security.principal.role == ...:
    ...
```

or:

```python
if authorization_service.authorize(...):
    ...
```

inside a Processing implementation.

The runtime is the enforcement point.

The Processing receives the already-authorized execution context.

---

# 76. No Authentication in Processing

The following is prohibited:

```text
Processing → password verification
Processing → session lookup
Processing → token parsing
```

Processing receives `SecurityContext` only.

Authentication remains an entry-boundary responsibility.

---

# 77. Security Event Integration

Security components may receive an optional `SecurityEventSink` dependency.

Where provided:

* successful authentication emits `AUTHENTICATION_SUCCEEDED`;
* failed authentication emits `AUTHENTICATION_FAILED`;
* authorization denial emits `AUTHORIZATION_DENIED`;
* role administration emits role-change events;
* session invalidation emits `SESSION_INVALIDATED`.

The event sink must not be allowed to turn a successful authentication/authorization operation into a business failure merely because an observational sink failed, unless the future audit architecture explicitly changes that guarantee.

The MVP may use a safe no-op/event-isolating sink.

---

# 78. Event Ordering

For a protected Processing execution:

```text
Authentication success
        ↓
SecurityContext creation
        ↓
Authorization decision
        ↓
Authorization denied event OR
        ↓
Processing execution
```

A denied operation emits a denial event, if an event sink is configured, and does not enter Processing.

A successful authorization event is not required as a separate event type in Phase 11.

---

# 79. API Review Questions

The following points are the intended review checklist before implementation:

1. Are `User` and `Principal` sufficiently separated?
2. Is `SecurityContext` correctly independent from `RuntimeConfigurationContext`?
3. Is the authentication boundary sufficiently replaceable?
4. Is the local credential contract sufficiently isolated?
5. Are `SecurityObjectIdentity` and `SecurityOperation` stable and explicit?
6. Is exact target + operation matching appropriate for the MVP?
7. Is the union-of-role-permissions model unambiguous?
8. Are constraint semantics sufficiently explicit without a DSL?
9. Is the distinction between denial and security infrastructure failure correct?
10. Is `ProcessingRuntime` the correct first enforcement point?
11. Does authorization occur before any Processing business effect?
12. Does `ProcessingContext.security` provide useful context without creating a service bag?
13. Is Standard composition sufficiently thin?
14. Are security persistence boundaries independent from business persistence?
15. Are the MVP protected operations concrete enough to test?
16. Is the audit/event boundary explicit without inventing durable audit persistence?
17. Are the proposed exports and module boundaries consistent with AcCoreD conventions?
18. Are there any accidental policy-engine, caching, role-hierarchy, wildcard, or transport-security semantics?

---

# 80. Implementation Slices

After API Review approval, implementation should proceed in small verified slices.

## Slice 1 — Security domain contracts

Implement:

* User;
* Principal;
* claims;
* Session;
* SecurityContext;
* SecurityObjectIdentity;
* SecurityOperation;
* Permission;
* Role;
* errors.

Gate:

* unit tests;
* ruff;
* black;
* mypy.

## Slice 2 — Authentication boundary

Implement:

* credentials;
* password verifier boundary;
* repositories;
* local provider;
* session store;
* context factory.

Gate:

* authentication tests;
* quality checks.

## Slice 3 — Authorization

Implement:

* authorization request;
* constraint protocol;
* authorization state;
* evaluator;
* decisions;
* `require` enforcement;
* denial/infrastructure semantics.

Gate:

* authorization unit tests;
* quality checks.

## Slice 4 — Processing enforcement

Implement:

* runtime authorization dependency;
* ProcessingContext security propagation;
* Processing security-object mapping;
* unauthorized side-effect tests.

Gate:

* Processing integration tests;
* full relevant test suite;
* quality checks.

## Slice 5 — Standard composition

Implement:

* Standard security definitions;
* local credentials;
* Standard roles;
* Standard permissions;
* Standard bootstrap composition.

Gate:

* Standard security tests;
* vertical Processing test;
* quality checks.

## Slice 6 — Security events and documentation

Implement:

* event contracts;
* event emission where required;
* architecture/documentation reconciliation.

Gate:

* complete Phase 11 test suite;
* documentation reconciliation;
* final quality gate.

---

# 81. Final API Summary

The Phase 11 public security model is:

```text
User
  │
  │ authentication
  ▼
Principal
  │
  ▼
SecurityContext
  │
  │ AuthorizationRequest
  ▼
AuthorizationService
  │
  ├── UserRepository
  ├── RoleRepository
  └── Permission / Constraint evaluation
  │
  ▼
AuthorizationDecision
  │
  ├── ALLOW
  └── DENY → AuthorizationDeniedError

ProcessingRuntime
  │
  ├── SecurityContext
  ├── AuthorizationService
  └── Processing
```

The key enforcement invariant is:

```text
ProcessingCommand
      ↓
Processing resolution
      ↓
Authorization
      ↓
ProcessingContext
      ↓
Processing execution
```

The key security invariant is:

```text
Authentication establishes identity.
Authorization establishes access.
Business code performs neither.
```

---

# 82. API Review Status

**Concrete API Design Review complete — Approved for Implementation.**

The following review decisions are incorporated into this final document:

1. matching permissions use OR semantics across permissions and AND semantics across
   constraints within one permission;
2. `UNKNOWN_TARGET` is not an MVP denial reason; an unmatched target defaults to
   `MISSING_PERMISSION`;
3. session validation belongs to the authentication/session boundary;
   `SecurityContextFactory` only constructs the immutable context;
4. `SecurityContext` is an explicit `ProcessingRuntime.execute(...)` argument and is not
   added to `ProcessingCommand`;
5. `User.role_ids` is the authoritative role assignment; no separate role-assignment
   repository is introduced;
6. `PasswordVerifier` remains an opaque Platform boundary while Standard owns the concrete
   production-grade salted hashing implementation;
7. claims remain opaque unless an explicit constraint consumes them;
8. `AuthorizationResource.identity` is contextual-resource identity and does not alter basic
   target+operation matching;
9. no concrete Standard data-scope constraint is required unless an actual MVP operation
   needs one;
10. Standard role definitions are Standard configuration, not a Platform authorization
   contract;
11. `Report.inventory.balance.Read` is the concrete Standard report permission;
12. security event outcomes use `SecurityEventOutcome`;
13. `PrincipalType.USER` uses the invariant `Principal.identity == User.identity`;
14. the redundant `SecurityIdentity` wrapper is removed in favor of the existing `Identifier`.

**Implementation may begin from this document.**
