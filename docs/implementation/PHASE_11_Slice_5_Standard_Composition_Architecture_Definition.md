# PHASE 11 --- Slice 5 --- Standard Composition

## Architecture Definition / Scope

**Status:** FINAL --- AMENDED --- APPROVED FOR CONCRETE API DESIGN /
IMPLEMENTATION\
**Phase:** 11 --- Security\
**Slice:** 5 --- Standard Composition

------------------------------------------------------------------------

## 1. Purpose

Slice 5 completes the Standard-side composition of the Phase 11 Security
MVP.

The Platform security layer already provides reusable security contracts
and runtime authorization semantics. Slice 5 supplies the Standard
Edition configuration and composition required to make those
capabilities usable as a coherent Standard security subsystem.

The slice establishes:

-   Standard security definitions;
-   representative Standard users;
-   Standard roles and permissions;
-   authoritative user-to-role assignment;
-   local credential state;
-   Standard authentication and authorization composition;
-   Standard security-context composition;
-   integration into Standard bootstrap;
-   the Standard-to-Platform vertical path required for protected
    Processing execution.

The architectural boundary remains explicit:

> **Platform owns security semantics and reusable security
> infrastructure. Standard owns security configuration, concrete local
> state, and composition.**

No new authorization semantics are introduced in Standard.

------------------------------------------------------------------------

## 2. Architectural Context

Previous Phase 11 slices established the Platform security model,
authentication boundary, authorization boundary, and Processing
enforcement boundary.

Slice 4 established the protected Processing runtime behavior:

1.  `ProcessingCommand` carries a `SecurityContext`;
2.  the runtime receives and propagates the same security context;
3.  authorization is evaluated before Processing resolution/execution;
4.  the operation is `SecurityOperation.EXECUTE`;
5.  the protected target uses semantic `object_type="processing"`;
6.  the Processing identity is represented by its stable semantic code;
7.  authorization denial raises `AuthorizationDeniedError`;
8.  denied Processing does not execute and produces no Processing side
    effects;
9.  infrastructure failures remain infrastructure failures.

Slice 5 composes actual Standard security state around that existing
Platform boundary. It must not move authorization semantics into
Standard or alter the Slice 4 Processing security boundary.

------------------------------------------------------------------------

## 3. Scope

### 3.1 In Scope

1.  Standard security vocabulary and definitions.
2.  Representative Standard users.
3.  Standard role definitions.
4.  Standard role-to-permission configuration.
5.  Authoritative user-to-role assignment through `User.role_ids`.
6.  Standard local credential state.
7.  Standard local authentication provider composition.
8.  Standard in-memory security state for the MVP.
9.  Composition of the Platform authorization service.
10. Composition of the `SecurityContextFactory`.
11. Integration into Standard bootstrap.
12. Standard security tests.
13. A vertical Processing scenario demonstrating authentication, context
    construction, authorization, and protected Processing execution.
14. Quality-gate validation.

### 3.2 Out of Scope

-   new Platform authentication or authorization algorithms;
-   Standard-specific permission matching;
-   role inheritance, wildcard or explicit-deny permissions;
-   policy languages or policy engines;
-   database/ORM-backed security persistence;
-   distributed security state;
-   security administration UI or general security CRUD framework;
-   audit/event persistence beyond existing Platform boundaries;
-   a new report runtime solely to exercise report permissions;
-   changes to the existing Processing authorization boundary;
-   changes to the established Platform security contracts.

------------------------------------------------------------------------

## 4. Architectural Principles

### 4.1 Platform Owns Security Semantics

Platform owns authentication, principal/session semantics,
authorization, permission matching, constraint evaluation, authorization
decisions, security errors, and security-context semantics.

Standard configures and composes these capabilities.

### 4.2 Standard Owns Security Configuration and Local State

Standard owns users, roles, permission definitions, user role
assignments, local credentials, local security state, and
composition/bootstrap.

Standard must not implement a second authorization model.

### 4.3 Explicit Security State

There is no ambient current-user state, module-level mutable security
singleton, hidden authorization default, or implicit administrator
access.

The `SecurityContext` remains explicit through the Processing path
established by Slice 4.

------------------------------------------------------------------------

## 5. Standard Security Vocabulary

The security object identities below are **semantic values of
`SecurityObjectIdentity.object_type` and `object_code`**. They are not
class names, display labels, module names, or implementation type names.

### 5.1 Protected Processing Permission

``` text
object_type = "processing"
object_code = "inventory.rebuild"
operation   = EXECUTE
```

This exactly matches the semantic identity used by the Slice 4
Processing authorization boundary and remains independent of the
concrete Processing implementation class.

### 5.2 Standard Report Permission

``` text
object_type = "report"
object_code = "inventory.balance"
operation   = READ
```

This is Standard security vocabulary and role configuration.

Slice 5 does **not** introduce a new report runtime or report
authorization boundary merely to exercise this permission. It may
participate in role definitions and authorization-state tests without
requiring a new report execution implementation.

### 5.3 Standard Security Administration Permission

``` text
object_type = "system"
object_code = "security"
operation   = ADMINISTER
```

This is permission vocabulary and representative authorization
configuration only. It does not imply a security administration service,
CRUD framework, administration UI, or persistent security-management
workflow.

------------------------------------------------------------------------

## 6. Standard Roles

The MVP defines three representative Standard roles.

### `standard.administrator`

-   `processing / inventory.rebuild / EXECUTE`
-   `report / inventory.balance / READ`
-   `system / security / ADMINISTER`

### `standard.operator`

-   `processing / inventory.rebuild / EXECUTE`

### `standard.auditor`

-   `report / inventory.balance / READ`

These are Standard configuration examples for the MVP, not an
irreversible enterprise-wide role taxonomy.

There is no role inheritance or implicit permission expansion.

------------------------------------------------------------------------

## 7. Authoritative User-to-Role Assignment

The authoritative assignment of roles to users is the existing
`User.role_ids` field.

Slice 5 must **not** introduce a separate role-assignment object,
repository, second mapping, or duplicated assignment state.

``` text
User.role_ids
    ↓
Role identities
    ↓
Role permissions
    ↓
Platform authorization evaluation
```

`User.role_ids` is the single authoritative source for Standard user
role assignment.

------------------------------------------------------------------------

## 8. Representative Standard Users

Standard composition provides representative users for the three MVP
roles:

``` text
administrator user → standard.administrator
operator user      → standard.operator
auditor user       → standard.auditor
```

These users make the subsystem executable and testable as a complete
composition.

Their concrete identifiers may remain implementation details unless an
external API requires stable identifiers.

Representative users are composition/test configuration; they do not
establish a permanent Standard user taxonomy.

Users must not contain plaintext passwords, credential material owned by
the credential boundary, session state, or cached authorization
decisions.

------------------------------------------------------------------------

## 9. Local Credential State

Standard supplies local credential state for the MVP, separate from
`User`, `Role`, `Principal`, and `SecurityContext`.

Conceptually:

``` text
StandardCredential
    user_identity
    verifier
```

The Platform `PasswordVerifier` remains an opaque contract.

Standard owns the concrete production implementation of password
verification, including the salted password-hashing strategy used by the
local MVP.

Slice 5 must not store plaintext passwords, expose passwords through
`User`, place passwords into `Principal` or `SecurityContext`, or
redesign the Platform authentication contract.

Test fixtures may construct credential verifiers through the same
production hashing/verifier boundary.

------------------------------------------------------------------------

## 10. Standard In-Memory Security State

For the Phase 11 MVP, Standard may use immutable in-memory security
configuration/state containing users and roles.

The state is configuration/composition state, not a mutable global
registry.

The design must avoid module-level mutable repositories, hidden
singleton state, cross-test mutation, and state changes caused merely by
authorization evaluation.

A future persistent security implementation may replace the storage
mechanism without changing Platform security semantics.

------------------------------------------------------------------------

## 11. Standard Authentication Composition

Standard composes Platform authentication contracts with local
credential state:

``` text
credentials
    ↓
Standard local credential repository
    ↓
Platform AuthenticationProvider
    ↓
authenticated Principal / Session
    ↓
SecurityContextFactory
    ↓
SecurityContext
```

The Standard authentication provider is an adapter/composition
component. It does not redefine authentication success/failure
semantics.

Authentication failures continue to use the Platform security error
model.

------------------------------------------------------------------------

## 12. Standard Authorization Composition

Standard composes the existing Platform `AuthorizationService` using
Standard users, roles, permission definitions, authoritative
`User.role_ids` assignments, and Platform authorization semantics.

The resulting authorization service remains a Platform abstraction.

Standard supplies authoritative state; Platform performs evaluation.

Standard does not implement permission matching, role traversal
semantics, constraint evaluation, missing-permission semantics, or
authorization decision generation.

Established Platform behavior remains authoritative: unknown targets are
not implicitly allowed, missing permission results in denial, and
authentication/session failures remain distinct from authorization
denial.

------------------------------------------------------------------------

## 13. Standard Security Composition

The Standard security composition exposes:

``` text
authentication
authorization
context_factory
```

Conceptually:

``` python
@dataclass(frozen=True, slots=True)
class StandardSecurityComposition:
    authentication: AuthenticationProvider
    authorization: AuthorizationService
    context_factory: SecurityContextFactory
```

This is an application composition result. It introduces no new security
semantics.

The `AuthorizationService` is the Platform implementation, not a
Standard evaluator.

------------------------------------------------------------------------

## 14. Standard Bootstrap Composition

Standard bootstrap is the security composition boundary.

``` text
StandardConfigurationBootstrap
        │
        ├── Standard users
        ├── Standard roles
        ├── Standard permissions
        ├── local credentials
        │
        ├── AuthenticationProvider
        ├── AuthorizationService
        └── SecurityContextFactory
```

The bootstrap creates and wires these components together.

It must not implement authorization rules, bypass authentication, grant
implicit administrative access, mutate Platform security semantics, or
create ambient security state.

The resulting composition is supplied to the application/runtime
composition that already contains the Slice 4 Processing authorization
boundary.

------------------------------------------------------------------------

## 15. Processing Vertical Scenario

The successful path is:

``` text
Standard credentials
        ↓
local credential verification
        ↓
Platform authentication
        ↓
authenticated principal/session
        ↓
SecurityContextFactory
        ↓
SecurityContext
        ↓
ProcessingCommand
        ↓
DefaultProcessingRuntime
        ↓
authorization
        ↓
processing / inventory.rebuild / EXECUTE
        ↓
Processing execution
```

The denial path is:

``` text
authenticated principal
        ↓
SecurityContext
        ↓
ProcessingCommand
        ↓
DefaultProcessingRuntime
        ↓
authorization
        ↓
AuthorizationDeniedError
        ↓
no Processing execution
        ↓
no Processing side effects
```

The vertical test uses the actual Standard composition and Processing
runtime boundary, not a mocked authorization decision.

------------------------------------------------------------------------

## 16. Security Context Propagation

Slice 5 introduces no alternative context mechanism.

The `SecurityContext` is produced by the composed Platform security
boundary and explicitly supplied to Processing.

The Slice 4 invariant remains:

> The security context is explicit, and the same `SecurityContext`
> instance propagates through the Processing command/runtime path.

No ambient context, thread-local identity, module-global current user,
or hidden context lookup is permitted.

------------------------------------------------------------------------

## 17. Authorization Ordering

The Slice 4 ordering remains unchanged:

``` text
SecurityContext
    ↓
authorization
    ↓
Processing resolution/execution
```

Authorization occurs before Processing resolution/execution.

Slice 5 must not introduce Standard bootstrap behavior that bypasses
this ordering.

An authorization denial prevents execution and its side effects.

Infrastructure failures remain infrastructure failures and are not
silently converted into authorization denial.

------------------------------------------------------------------------

## 18. Configuration and Business-State Separation

Standard security definitions are configuration.

They must not depend on inspection of live business state merely to
define users, roles, permissions, or credentials.

Security configuration must not import concrete Processing
implementations merely to construct the semantic Processing permission
identity.

The permission:

``` text
processing / inventory.rebuild / EXECUTE
```

is a stable security vocabulary value. Its runtime relationship to
Processing is established through the semantic identity mapping defined
by Slice 4, not through a dependency on a concrete Processing class.

------------------------------------------------------------------------

## 19. Testing Scope

### 19.1 Standard Security Definitions

Verify:

-   Standard users are defined;
-   Standard roles are defined;
-   role identifiers are stable within the composition;
-   permissions have expected semantic object identities and operations;
-   `User.role_ids` contains intended assignments;
-   there is no duplicate authoritative role-assignment mechanism.

### 19.2 Credential State

Verify:

-   credentials are associated with user identity;
-   plaintext passwords are not stored in user/role/principal/context
    objects;
-   valid credentials authenticate;
-   invalid credentials fail through the Platform authentication
    boundary.

### 19.3 Role-Based Authorization

Verify at least:

-   administrator can execute `inventory.rebuild`;
-   operator can execute `inventory.rebuild`;
-   auditor cannot execute `inventory.rebuild`;
-   administrator can read `inventory.balance`;
-   auditor can read `inventory.balance`;
-   operator does not implicitly receive `inventory.balance`;
-   administrator has `security/administer`;
-   permissions are not granted merely by the existence of a user.

### 19.4 Standard Composition

Verify:

-   bootstrap creates the expected security composition;
-   authentication, authorization, and context factory are wired
    consistently;
-   the composed authorization service uses Standard security state;
-   no Standard authorization evaluator exists.

### 19.5 Vertical Processing Test

At minimum:

1.  authenticate a Standard operator;
2.  create its security context;
3.  construct the protected Processing command;
4.  execute through the real Processing runtime;
5.  verify authorization succeeds;
6.  verify Processing executes.

Then:

1.  authenticate a Standard auditor;
2.  create its security context;
3.  submit the same protected Processing operation;
4.  verify `AuthorizationDeniedError`;
5.  verify the Processing implementation is not executed;
6.  verify no Processing side effects occur.

The vertical test exercises the real composition path rather than
replacing authorization with a test double.

------------------------------------------------------------------------

## 20. Architectural Invariants

### A. Platform remains the security semantic owner

Standard does not implement authorization semantics.

### B. Standard owns configuration and local composition

Users, roles, permissions, local credentials, and wiring are Standard
concerns.

### C. `User.role_ids` is authoritative

No separate role-assignment state is introduced.

### D. Semantic security identities are stable

The protected Processing permission uses:

``` text
object_type = "processing"
object_code = "inventory.rebuild"
operation   = EXECUTE
```

These are semantic identifiers, not implementation class names.

### E. No implicit administrator

No user receives administrative access unless the configured role
explicitly grants it.

### F. Credentials remain separate

Credential material does not become part of User, Principal, Role, or
SecurityContext.

### G. No ambient security state

SecurityContext and authentication state remain explicit.

### H. Authorization precedes Processing execution

The Slice 4 ordering is preserved.

### I. Denial is side-effect free

A denied Processing operation must not execute the Processing
implementation or produce Processing side effects.

### J. Report permission does not create a new report boundary

`report / inventory.balance / READ` is Standard vocabulary/configuration
in this slice. No report runtime is introduced solely for permission
testing.

### K. Administration permission does not create an administration framework

`system / security / ADMINISTER` is permission vocabulary/configuration
only.

### L. Platform authentication contract remains opaque

Standard supplies concrete credential verification behind the existing
Platform `PasswordVerifier` contract.

### M. Security state is explicit and non-global

No mutable module-level security registry or hidden singleton is
introduced.

------------------------------------------------------------------------

## 21. Acceptance Criteria

Slice 5 is architecturally complete when:

1.  Standard security users are defined.
2.  Standard roles are defined.
3.  Standard permissions are defined using stable semantic identities.
4.  `User.role_ids` is the sole authoritative user-to-role assignment
    mechanism.
5.  Local credential state is defined separately from users.
6.  Standard composes the Platform authentication provider.
7.  Standard composes the Platform authorization service.
8.  Standard composes the Platform security-context factory.
9.  Standard bootstrap exposes a coherent security composition.
10. No Standard authorization evaluator exists.
11. Administrator, operator, and auditor behavior is covered by tests.
12. A real vertical Processing scenario demonstrates allow and deny
    behavior.
13. Authorization occurs before Processing execution.
14. Denied Processing produces no Processing side effects.
15. Security state is explicit and non-global.
16. Standard security tests pass.
17. The vertical Processing test passes.
18. The project quality gate passes.

------------------------------------------------------------------------

## 22. Implementation Boundary

Concrete API Design may define:

-   exact Standard security module/file structure;
-   exact Standard user definitions;
-   exact role/permission construction;
-   exact credential implementation;
-   repository implementations;
-   exact `StandardSecurityComposition` construction;
-   bootstrap method signatures;
-   test fixture structure;
-   integration points with existing Processing composition.

Concrete API Design must not change the architectural boundaries defined
here.

Implementation must not introduce:

-   Standard authorization semantics;
-   a second role-assignment source;
-   implicit administrative privileges;
-   ambient security state;
-   a new report runtime solely for permission testing;
-   a security administration framework.

------------------------------------------------------------------------

## 23. Slice 5 Outcome

Upon completion, Standard provides a coherent, executable security
composition over reusable Platform security infrastructure.

``` text
                 STANDARD
 ┌──────────────────────────────────────────┐
 │ Users                                    │
 │ Roles                                    │
 │ Permissions / security vocabulary        │
 │ User.role_ids                            │
 │ Local credentials                        │
 │ Standard bootstrap                       │
 └────────────────────┬─────────────────────┘
                      │ composition
                      ▼
                 PLATFORM
 ┌──────────────────────────────────────────┐
 │ Authentication contracts                 │
 │ Credential verification boundary         │
 │ Principal / Session                      │
 │ SecurityContext                          │
 │ AuthorizationService                     │
 │ Permission evaluation                    │
 │ SecurityContextFactory                   │
 └────────────────────┬─────────────────────┘
                      │ explicit SecurityContext
                      ▼
                PROCESSING RUNTIME
 ┌──────────────────────────────────────────┐
 │ authorize EXECUTE                        │
 │ target: processing / inventory.rebuild   │
 │                                          │
 │ allow → execute                          │
 │ deny  → no execution / no side effects  │
 └──────────────────────────────────────────┘
```

This completes the architectural scope for Slice 5 and provides the
stable boundary for its Concrete API Design and implementation.
