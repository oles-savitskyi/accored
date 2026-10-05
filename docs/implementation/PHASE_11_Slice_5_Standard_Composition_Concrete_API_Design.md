# PHASE 11 — Slice 5 — Standard Composition

## Concrete API Design

**Status:** FINAL — AMENDED — APPROVED FOR IMPLEMENTATION  
**Phase:** 11 — Security  
**Slice:** 5 — Standard Composition  
**Architecture Definition:** `PHASE_11_Slice_5_Standard_Composition_Architecture_Definition_FINAL.md`

---

## 1. Purpose

This document defines the concrete Python API proposed for Phase 11 Security,
Slice 5 — Standard Composition.

It is derived from the approved Slice 5 Architecture Definition and from the
already implemented Platform security and Slice 4 Processing security
boundaries.

The goal is to make the Standard security MVP executable without introducing a
second security model in Standard.

The intended dependency direction is:

```text
Standard security definitions / local state / composition
                    │
                    ▼
        Platform security contracts
                    │
                    ▼
        Processing authorization boundary
```

The API decisions in this document are normative for Slice 5 implementation.
The architecture review that produced this final version is summarized in
Section 26.

---

# Part I — Concrete API Design

## 2. Existing Platform API That Slice 5 Consumes

Slice 5 must consume the existing Platform API rather than redefine it.

### 2.1 User

Existing contract:

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

The `role_ids` field is the sole authoritative user-to-role assignment source.

Slice 5 does not add another assignment repository or mapping.

### 2.2 Role

```python
@dataclass(frozen=True, slots=True)
class Role:
    identity: Identifier
    code: str
    name: str
    permissions: tuple[Permission, ...]
```

Roles contain their permission grants directly.

### 2.3 Permission

```python
@dataclass(frozen=True, slots=True)
class Permission:
    identity: Identifier
    target: SecurityObjectIdentity
    operation: SecurityOperation
    constraints: tuple[AuthorizationConstraint, ...] = ()
```

Slice 5 creates unconstrained permissions for the current MVP.

### 2.4 Security object identity

```python
@dataclass(frozen=True, slots=True)
class SecurityObjectIdentity:
    object_type: str
    object_code: str
```

Standard must use the semantic values established by the architecture:

```text
processing / inventory.rebuild
report     / inventory.balance
system     / security
```

These values are not Python class names.

### 2.5 Operations

The existing `SecurityOperation` enum is reused:

```python
SecurityOperation.EXECUTE
SecurityOperation.READ
SecurityOperation.ADMINISTER
```

No new operation is required for Slice 5.

### 2.6 Authentication contracts

Slice 5 consumes:

```python
class AuthenticationProvider(Protocol):
    def authenticate(
        self,
        credentials: PasswordCredentials,
    ) -> AuthenticationResult: ...

class UserRepository(Protocol):
    def find_by_login(self, login: str) -> User | None: ...
    def get(self, identity: Identifier) -> User: ...

class CredentialRepository(Protocol):
    def get_password_verifier(
        self,
        user_identity: Identifier,
    ) -> PasswordVerifier: ...

class RoleRepository(Protocol):
    def get(self, identity: Identifier) -> Role: ...

class SessionStore(Protocol):
    def create(self, principal: Principal, now: datetime) -> Session: ...
    def get(self, identity: Identifier) -> Session | None: ...
    def invalidate(self, identity: Identifier) -> None: ...

class SecurityContextFactory(Protocol):
    def from_authentication(
        self,
        result: AuthenticationResult,
        request_identity: Identifier | None = None,
    ) -> SecurityContext: ...
```

The Platform `PasswordVerifier` remains opaque to Standard callers except for
being stored and passed through the credential boundary.

### 2.7 Authorization contracts

```python
class SecurityAuthorizationState(Protocol):
    def user_for_principal(self, principal: Principal) -> User: ...
    def role(self, identity: Identifier) -> Role: ...

class AuthorizationService(Protocol):
    def authorize(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision: ...

    def require(self, request: AuthorizationRequest) -> None: ...
```

The Platform `DefaultAuthorizationService` remains the evaluator.
Standard supplies state through `SecurityAuthorizationState`.

### 2.8 Processing security boundary

Slice 5 must preserve the existing Slice 4 contract:

```python
@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    processing_identity: ProcessingIdentity
    parameters: object
    runtime_configuration: RuntimeConfigurationContext
    security_context: SecurityContext
    execution_identity: ProcessingExecutionIdentity | None = None
```

`DefaultProcessingRuntime` already evaluates:

```text
processing / <processing_identity.value> / EXECUTE
```

before Processing resolution/execution.

Slice 5 does not change this API.

---

## 3. Proposed Standard Module Layout

The preferred Slice 5 implementation layout is:

```text
src/standard/security/
    __init__.py
    authentication.py
    authorization.py
    definitions.py
    persistence.py
```

Existing files are retained where their responsibilities already fit.

### Responsibilities

| Module | Responsibility |
|---|---|
| `definitions.py` | Standard users, roles, permissions, representative security configuration |
| `authentication.py` | Password hashing and local `AuthenticationProvider` |
| `authorization.py` | Standard authorization-state adapter |
| `composition.py` | `StandardSecurityComposition` and composition assembly |
| `persistence.py` | In-memory users, credentials, roles, and sessions |
| `__init__.py` | Public Standard security API |

A separate `context.py` is not required because the Platform
`DefaultSecurityContextFactory` already supplies the concrete context factory.

A separate `role_assignment.py` is explicitly prohibited: `User.role_ids` is
already authoritative.

---

## 4. Standard Security Identity Definitions

### 4.1 Identity policy

Concrete `Identifier` values for Standard users, roles, and permissions are
implementation details of the Standard composition.

Within one composition they must be internally consistent:

```text
User.role_ids → Role.identity
Role.permissions → Permission.identity
```

No external API is required to depend on generated ULIDs.

### 4.2 Standard role codes

The following codes are normative for the MVP:

```python
STANDARD_ADMINISTRATOR_ROLE = "standard.administrator"
STANDARD_OPERATOR_ROLE = "standard.operator"
STANDARD_AUDITOR_ROLE = "standard.auditor"
```

The code is the stable semantic role identifier exposed to Standard
configuration; the underlying `Identifier` remains an internal identity.

### 4.3 Standard security object constants

The definitions module should expose immutable constants or private factories
for the three semantic targets:

```python
PROCESSING_INVENTORY_REBUILD = SecurityObjectIdentity(
    object_type="processing",
    object_code="inventory.rebuild",
)

REPORT_INVENTORY_BALANCE = SecurityObjectIdentity(
    object_type="report",
    object_code="inventory.balance",
)

SYSTEM_SECURITY = SecurityObjectIdentity(
    object_type="system",
    object_code="security",
)
```

Whether these are public constants or private construction helpers is an
implementation detail; their semantic values are normative.

### 4.4 Standard permissions

The MVP creates exactly these representative permissions:

```python
Permission(
    identity=permission_identity,
    target=PROCESSING_INVENTORY_REBUILD,
    operation=SecurityOperation.EXECUTE,
)

Permission(
    identity=permission_identity,
    target=REPORT_INVENTORY_BALANCE,
    operation=SecurityOperation.READ,
)

Permission(
    identity=permission_identity,
    target=SYSTEM_SECURITY,
    operation=SecurityOperation.ADMINISTER,
)
```

No constraints are attached in Slice 5.

### 4.5 Role construction

Role composition should be explicit:

```python
Role(
    identity=administrator_role_identity,
    code="standard.administrator",
    name="Standard Administrator",
    permissions=(
        processing_execute_permission,
        report_read_permission,
        security_administer_permission,
    ),
)
```

```python
Role(
    identity=operator_role_identity,
    code="standard.operator",
    name="Standard Operator",
    permissions=(processing_execute_permission,),
)
```

```python
Role(
    identity=auditor_role_identity,
    code="standard.auditor",
    name="Standard Auditor",
    permissions=(report_read_permission,),
)
```

No role inherits from another role.

---

## 5. Standard User Definitions

The architecture requires representative users for the three roles.

The concrete API should provide:

```python
def standard_security_users(
    *,
    administrator_role_id: Identifier,
    operator_role_id: Identifier,
    auditor_role_id: Identifier,
) -> tuple[User, ...]: ...
```

The function returns immutable `User` values whose `role_ids` refer only to
the role identities supplied to it. In production composition those role
identities come from the single role definition set described in Section 6.

Representative logins may be implementation details, for example:

```text
administrator
operator
auditor
```

The exact login strings should not become a broader public Standard API unless
another subsystem needs them.

### User invariants

For every returned user:

```text
identity is unique
login is unique
active == True for MVP representative users
role_ids references existing Standard roles
```

No password or credential verifier is placed in `User`.

---

## 6. Standard Role Definitions

The concrete API exposes:

```python
def standard_security_roles() -> tuple[Role, ...]: ...
```

The function owns construction of role and permission identities and returns
an immutable tuple. Users are derived from that exact role tuple; independent
role-ID generation is prohibited.

The preferred internal assembly is:

```python
@dataclass(frozen=True, slots=True)
class _StandardSecurityDefinitions:
    users: tuple[User, ...]
    roles: tuple[Role, ...]
    credentials: tuple[StandardCredential, ...]
```

A private assembler constructs the roles once, derives users from those exact
role identities, and then derives credentials. The bundle is internal and is
not a second repository or role-assignment model.

---

## 7. Standard Credential Model

### 7.1 StandardCredential

Add:

```python
@dataclass(frozen=True, slots=True)
class StandardCredential:
    user_identity: Identifier
    verifier: PasswordVerifier
```

This value belongs to Standard and intentionally contains no plaintext
password.

### 7.2 Credential definition factory

The Standard definitions/composition layer should create credential state from
bootstrap passwords without exposing plaintext after composition.

Preferred boundary:

```python
def standard_security_credentials(
    *,
    users: tuple[User, ...],
    password_hasher: StandardPasswordHasher,
    initial_passwords: Mapping[str, str],
) -> tuple[StandardCredential, ...]: ...
```

The exact bootstrap-password source is deliberately an implementation
boundary. It must not become a persisted `User` property.

For the default local MVP, passwords are converted immediately into
`PasswordVerifier` values using `StandardPasswordHasher`.

Tests may use the same production hasher.

### 7.3 In-memory credential repository

Replace the current mutable public dictionary API with an immutable input
collection:

```python
@dataclass(frozen=True, slots=True)
class InMemoryCredentialRepository(CredentialRepository):
    credentials: tuple[StandardCredential, ...]

    def get_password_verifier(
        self,
        user_identity: Identifier,
    ) -> PasswordVerifier: ...
```

Construction validates:

- unique `user_identity`;
- no missing verifier;
- no duplicate credential record.

The repository itself does not mutate during authentication.

---

## 8. Standard User Repository

Existing implementation is retained conceptually:

```python
@dataclass(slots=True)
class InMemoryUserRepository:
    users: tuple[User, ...]

    def find_by_login(self, login: str) -> User | None: ...
    def get(self, identity: Identifier) -> User: ...
```

Its constructor validates unique login and identity.

Because users are immutable values and the repository has no mutation methods,
it is a read-only composition repository for Slice 5.

The internal lookup dictionaries may remain an implementation optimization;
they are not exposed as mutable security state.

---

## 9. Standard Role Repository

Existing implementation is retained conceptually:

```python
@dataclass(slots=True)
class InMemoryRoleRepository:
    roles: tuple[Role, ...]

    def get(self, identity: Identifier) -> Role: ...
```

The repository validates unique role identities.

No role assignment methods are added.

---

## 10. Standard Authorization State Adapter

The Standard adapter remains:

```python
@dataclass(frozen=True, slots=True)
class StandardSecurityAuthorizationState(SecurityAuthorizationState):
    users: UserRepository
    roles: RoleRepository

    def user_for_principal(self, principal: Principal) -> User: ...
    def role(self, identity: Identifier) -> Role: ...
```

Its responsibilities are intentionally narrow:

1. resolve the Platform `Principal` to a `User`;
2. resolve a role identity to a `Role`.

It must not:

- decide whether a permission matches;
- traverse roles itself;
- evaluate constraints;
- create `AuthorizationDecision` values;
- implement `require()`.

All such semantics remain in `DefaultAuthorizationService`.

### Principal invariant

Slice 5 MVP supports only:

```python
PrincipalType.USER
```

The Standard adapter therefore expects:

```text
principal.identity == user.identity
principal.identity_type == PrincipalType.USER
```

The Platform authorization service remains responsible for rejecting
unsupported principal types according to its existing contract.

---

## 11. Standard Password Hasher

The existing `StandardPasswordHasher` is retained as the concrete Standard
implementation of the Platform `PasswordVerifier` boundary:

```python
@dataclass(frozen=True, slots=True)
class StandardPasswordHasher:
    n: int = 2**14
    r: int = 8
    p: int = 1
    dklen: int = 32
    salt_length: int = 16

    def hash(self, password: str) -> PasswordVerifier: ...

    def verify(
        self,
        password: str,
        verifier: PasswordVerifier,
    ) -> bool: ...
```

The current salted scrypt representation is acceptable for the MVP.

The Platform API must remain unaware of scrypt parameters.

Authentication failure must not expose whether a login exists or whether the
password alone was incorrect.

---

## 12. Local Authentication Provider

The existing provider remains the Standard adapter:

```python
@dataclass(frozen=True, slots=True)
class LocalAuthenticationProvider:
    users: UserRepository
    credentials: CredentialRepository
    sessions: SessionStore
    password_hasher: StandardPasswordHasher

    def authenticate(
        self,
        credentials: PasswordCredentials,
    ) -> AuthenticationResult: ...
```

Authentication sequence:

```text
login
  ↓
UserRepository.find_by_login
  ↓
active user check
  ↓
CredentialRepository.get_password_verifier
  ↓
StandardPasswordHasher.verify
  ↓
Principal(USER, user.identity)
  ↓
SessionStore.create
  ↓
AuthenticationResult
```

Failure is represented by the existing `AuthenticationFailedError`.

No authorization decision is made here.

---

## 13. Session Store

The existing `InMemorySessionStore` is retained for the MVP:

```python
@dataclass(slots=True)
class InMemorySessionStore:
    lifetime: timedelta = timedelta(hours=8)

    def create(self, principal: Principal, now: datetime) -> Session: ...
    def get(self, identity: Identifier) -> Session | None: ...
    def invalidate(self, identity: Identifier) -> None: ...
```

Session state is runtime state and is distinct from immutable user/role
configuration.

No session state is placed into `User` or `SecurityContext` beyond the
explicit `Session` reference already defined by Platform.

---

## 14. Security Context Factory

Slice 5 should use the existing Platform implementation directly:

```python
DefaultSecurityContextFactory()
```

Its contract remains:

```python
def from_authentication(
    self,
    result: AuthenticationResult,
    request_identity: Identifier | None = None,
) -> SecurityContext: ...
```

No Standard subclass is required.

No Standard context factory should add implicit user, role, or authorization
state to `SecurityContext`.

---

## 15. Authorization Service Composition

The Standard composition constructs the Platform evaluator:

```python
state = StandardSecurityAuthorizationState(
    users=user_repository,
    roles=role_repository,
)

authorization = DefaultAuthorizationService(state)
```

The type exposed by the composition remains:

```python
AuthorizationService
```

The concrete object is Platform's `DefaultAuthorizationService`.

No `StandardAuthorizationService` is introduced.

### Evaluation semantics

The existing Platform evaluator remains authoritative:

```text
principal authenticated?
        ↓
principal supported?
        ↓
user active?
        ↓
resolve User.role_ids
        ↓
resolve roles
        ↓
collect matching permissions
        ↓
OR across matching permissions
        ↓
AND across constraints within a permission
```

Slice 5 does not alter this behavior.

---

## 16. Standard Security Composition

The architecture requires all three security boundaries to be returned:

```python
@dataclass(frozen=True, slots=True)
class StandardSecurityComposition:
    authentication: AuthenticationProvider
    authorization: AuthorizationService
    context_factory: SecurityContextFactory
```

This is a deliberate expansion of the current Slice 4-era implementation,
which currently exposes only `authorization`.

The composition object is immutable and contains references to already
constructed services/repositories. It is the single Standard-side composition
result for the three security boundaries.

It does not own business state and does not expose mutation methods.

---

## 17. Standard Security Bootstrap API

The existing `StandardConfigurationBootstrap` gains:

```python
def compose_security(
    self,
    *,
    initial_passwords: Mapping[str, str],
) -> StandardSecurityComposition: ...
```

`initial_passwords` is an explicit composition input for the representative
Standard users. Slice 5 must not embed well-known production-default passwords
or silently manufacture credentials. Test fixtures provide known test
passwords explicitly.

The architecture does not require a credential provisioning UI or external
secret-management system in Slice 5; those are later concerns.

### Recommended internal sequence

```text
create Standard roles
        ↓
create Standard users referencing role identities
        ↓
create password verifiers
        ↓
create user repository
        ↓
create role repository
        ↓
create credential repository
        ↓
create session store
        ↓
create StandardSecurityAuthorizationState
        ↓
create DefaultAuthorizationService
        ↓
create LocalAuthenticationProvider
        ↓
create DefaultSecurityContextFactory
        ↓
return StandardSecurityComposition
```

The bootstrap must use one coherent definition set so that user role IDs and
repository contents cannot diverge.

---

## 18. Bootstrap Integration with Processing Runtime

The existing Processing composition remains:

```python
def compose_processing_runtime(
    self,
    processings: Mapping[ProcessingIdentity, Processing[object, object]],
    authorization_service: AuthorizationService,
) -> ProcessingRuntime: ...
```

The caller supplies:

```python
security = bootstrap.compose_security()

runtime = bootstrap.compose_processing_runtime(
    processings,
    security.authorization,
)
```

The Processing runtime remains Platform-owned.

The Standard bootstrap does not wrap or replace `DefaultProcessingRuntime`.

---

## 19. Protected Processing Usage

A caller authenticates and creates a context explicitly:

```python
result = security.authentication.authenticate(
    PasswordCredentials(
        login="operator",
        password="...",
    )
)

context = security.context_factory.from_authentication(result)
```

The protected Processing command then carries the same context:

```python
command = ProcessingCommand(
    processing_identity=ProcessingIdentity("inventory.rebuild"),
    parameters=parameters,
    runtime_configuration=runtime_configuration,
    security_context=context,
)
```

The runtime evaluates authorization before Processing execution.

No Standard caller performs a separate `authorize()` call as a substitute for
runtime enforcement.

---

## 20. Representative Authorization Expectations

The Standard definitions must produce these outcomes through the Platform
evaluator.

| User | Target | Operation | Expected |
|---|---|---|---|
| administrator | processing / inventory.rebuild | EXECUTE | allow |
| operator | processing / inventory.rebuild | EXECUTE | allow |
| auditor | processing / inventory.rebuild | EXECUTE | deny / MISSING_PERMISSION |
| administrator | report / inventory.balance | READ | allow |
| auditor | report / inventory.balance | READ | allow |
| operator | report / inventory.balance | READ | deny / MISSING_PERMISSION |
| administrator | system / security | ADMINISTER | allow |
| operator | system / security | ADMINISTER | deny / MISSING_PERMISSION |
| auditor | system / security | ADMINISTER | deny / MISSING_PERMISSION |

The report and system permissions are authorization vocabulary tests; they do
not create new report or security-administration runtime boundaries.

---

## 21. Error Boundaries

Slice 5 preserves the existing error model.

### Authentication

Invalid credentials:

```python
AuthenticationFailedError
```

Invalid authentication configuration/state may surface as the existing
Platform security configuration error boundary where appropriate.

### Authorization

A denied authorization request:

```python
AuthorizationDeniedError
```

with a concrete `AuthorizationDecision` and deny reason.

### Configuration/state failure

Examples such as missing role referenced by `User.role_ids` remain configuration
failures rather than being converted into ordinary permission denial.

This distinction is important: incomplete authoritative security state must not
silently behave as “not authorized”.

---

## 22. Public API Export Policy

`src/standard/security/__init__.py` should export only the Standard security
API needed by composition and tests.

Expected public exports after Slice 5 include:

```text
InMemoryCredentialRepository
InMemoryRoleRepository
InMemorySessionStore
InMemoryUserRepository
LocalAuthenticationProvider
StandardCredential
StandardPasswordHasher
StandardSecurityAuthorizationState
StandardSecurityComposition
standard_security_roles
standard_security_users
```

Permission/object constants may remain private if they are only construction
helpers.

No internal repository indexes or definition-assembly helpers are exported.

---

## 23. Test API and Fixtures

Tests should construct security state through the same Standard factories and
repositories used by production composition wherever practical.

### 23.1 Unit test fixture

A fixture may provide:

```python
security = bootstrap.compose_security(...)
```

rather than rebuilding a second authorization implementation.

### 23.2 Credential tests

Verify:

- hash output is not plaintext;
- two hashes of the same password use different salts;
- valid password verifies;
- invalid password does not verify;
- malformed verifier fails safely.

### 23.3 Definition tests

Verify:

- exactly three representative roles;
- expected permission sets;
- correct semantic object identities;
- expected `User.role_ids` assignments;
- unique users/roles/permissions.

### 23.4 Authorization tests

Use the actual `DefaultAuthorizationService` and Standard state adapter.

Do not mock the authorization evaluator.

### 23.5 Vertical Processing test

The test should exercise:

```text
Standard bootstrap
 → authentication
 → context factory
 → ProcessingCommand
 → DefaultProcessingRuntime
 → Platform authorization
 → real Standard Processing
```

Success path:

```text
operator → inventory.rebuild → executes
```

Denial path:

```text
auditor → inventory.rebuild → AuthorizationDeniedError
                                  ↓
                           no Processing execute
```

The denial test must assert that the Processing implementation is not called
and that no Processing side effect occurs.

---

## 24. Suggested Slice 5 File Changes

The expected implementation set is approximately:

```text
src/standard/security/__init__.py
src/standard/security/authentication.py
src/standard/security/authorization.py
src/standard/security/definitions.py          # new
src/standard/security/persistence.py
src/standard/bootstrap.py

tests/unit/security/test_definitions.py       # new
 tests/unit/security/test_composition.py      # new
 tests/unit/security/test_authentication.py   # amend as needed
 tests/unit/security/test_authorization.py    # amend as needed
 tests/integration/...                        # vertical Processing test, exact path TBD
```

The exact test path may follow the repository's existing integration-test
layout.

No Platform security source file should need modification for Slice 5 unless
implementation reveals an already-existing contract defect. Such a change
would require a separate architecture decision rather than being smuggled into
Standard composition.

---

## 25. Implementation Constraints

Implementation must not:

1. add a second role-assignment source;
2. add Standard permission matching;
3. add implicit administrator access;
4. bypass authentication in bootstrap;
5. place password material in `User`, `Principal`, or `SecurityContext`;
6. create a Standard authorization evaluator;
7. introduce ambient security context;
8. add a report runtime merely for permission testing;
9. add a security administration service/UI;
10. modify the Slice 4 Processing authorization ordering;
11. change `ProcessingCommand.security_context`;
12. make `DefaultProcessingRuntime` Standard-specific;
13. convert security configuration failures into ordinary denial;
14. introduce mutable module-level security state.

---

# Part II — Final Architecture Review and Approval

## 26. Review Basis

This final API design was reviewed against:

1. the final amended Slice 5 Architecture Definition;
2. the existing Phase 11 Platform security contracts;
3. the current Standard authentication, authorization, and persistence code;
4. the implemented Slice 4 Processing security boundary;
5. the previously approved Phase 11 security API decisions.

The review explicitly checked ownership boundaries, identity semantics, role
assignment authority, credential separation, composition direction, bootstrap
coherence, and Processing integration.

## 27. Amendments Incorporated

The following review findings were incorporated into this final version:

1. **Three-part Standard composition** — `StandardSecurityComposition` now
   contains `authentication`, `authorization`, and `context_factory`.
2. **Explicit credential state** — `StandardCredential` is the immutable
   Standard credential value object.
3. **Immutable credential repository input** — the public repository state is
   `tuple[StandardCredential, ...]`; lookup indexes, if used, remain private.
4. **Single role identity source** — roles are constructed once and users derive
   their authoritative `User.role_ids` from that exact definition set.
5. **Explicit credential provisioning** — `compose_security()` requires an
   `initial_passwords` input for the MVP and does not create hidden default
   passwords.
6. **Composition module clarity** — `StandardSecurityComposition` is placed in
   `standard/security/composition.py`.

The optional naming recommendation from the draft review was therefore also
adopted.

## 28. Final Architecture Review Verdict

### **APPROVED FOR IMPLEMENTATION**

No unresolved architecture conflict remains in the Slice 5 Concrete API Design.

The design preserves the approved ownership model:

```text
Standard configuration / local state
              │
              ▼
Platform security contracts and semantics
              │
              ▼
Existing Processing authorization boundary
```

In particular:

- Standard does not implement permission matching;
- `User.role_ids` is the sole authoritative user-to-role assignment source;
- credentials remain separate from `User`, `Principal`, and `SecurityContext`;
- `PasswordVerifier` remains an opaque Platform boundary;
- no ambient security context is introduced;
- no implicit administrator access is introduced;
- the report and security-admin permissions remain vocabulary/configuration only;
- no new report runtime or security-administration framework is introduced;
- Slice 4 `ProcessingCommand.security_context` and authorization ordering remain
  unchanged;
- authorization infrastructure failures are not converted into ordinary deny;
- security configuration remains explicit and non-global.

## 29. Implementation Gate

Implementation of Slice 5 may begin from this document. The implementation
gate is:

```text
pytest -q tests/unit/security/
pytest -q <vertical Processing/security tests>
ruff check src tests
black --check src tests
mypy src
git diff --check
```

Functional coverage must include:

```text
Standard definitions
Credential hashing and verification
Authentication
Role-based authorization
Three-part security composition
Bootstrap coherence
Protected Processing allow
Protected Processing deny
No denied Processing side effects
```

## 30. Superseded API Note

Any earlier Phase 11 API text stating that `SecurityContext` is not part of
`ProcessingCommand` is superseded for implementation purposes. The approved
Slice 4 implementation and contract are normative:

```python
@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    processing_identity: ProcessingIdentity
    parameters: object
    runtime_configuration: RuntimeConfigurationContext
    security_context: SecurityContext
    execution_identity: ProcessingExecutionIdentity | None = None
```

Slice 5 composes against this existing boundary and does not modify it.

## 31. Final Summary

Slice 5 introduces no new security semantics. It completes the Standard-side
composition required to make the already implemented Platform security model
usable by the Standard configuration and by the protected Processing runtime.

The final implementation shape is deliberately small:

```text
Standard definitions
      │
      ├── Users ── role_ids ──► Roles ──► Permissions
      │
      └── Credentials ──► LocalAuthenticationProvider
                                  │
                                  ▼
                         AuthenticationResult
                                  │
                                  ▼
                    DefaultSecurityContextFactory
                                  │
                                  ▼
                         SecurityContext
                                  │
                                  ▼
                       ProcessingCommand
                                  │
                                  ▼
                    DefaultProcessingRuntime
                                  │
                                  ▼
                    DefaultAuthorizationService
```

> **Standard provides security configuration and local state; Platform
> provides security semantics; Processing remains protected by the existing
> Platform runtime boundary.**
