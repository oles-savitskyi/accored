# AcCoreD — Phase 11

# Security Architecture Definition / Scope

**Baseline:** `c19b1e5 — docs(processing): reconcile Phase 10 architecture`

**Project state:** `AcCoreD_cur11.zip`

**Status:** Final Architecture Definition / Scope — Architecture Review amendments incorporated

---

# 1. Purpose

Phase 11 introduces the minimum Platform Security infrastructure required for the first usable AcCoreD Standard Edition.

Security is introduced before the application accumulates substantial application-specific authorization logic. The phase establishes one security boundary that can be reused by Runtime, Processing, Reporting, Posting, future API/Integration layers, and Standard Configuration.

This document defines architectural scope and boundaries only. It does not define the final concrete Python API, storage schemas, authentication-provider implementation, or implementation slices. Those belong to the subsequent Concrete API Design and implementation stages.

---

# 2. Current Baseline Findings

The current repository already contains a substantial declarative security architecture under `docs/architecture/security/`:

* `SECURITY_DOMAIN_MODEL.md` defines User, Role, Permission, SecurityObject, Constraint, Principal, and Session;
* `AUTHENTICATION_MODEL.md` separates authentication from authorization and establishes Principal as the authentication result;
* `AUTHORIZATION_MODEL.md` defines Security Object + Operation = Permission;
* `SECURITY_MODEL.md` defines a centralized authorization pipeline and default-deny behavior;
* `SECURITY_POLICIES.md` defines provider independence, least privilege, fail-closed behavior, centralized authorization, and related policies;
* `STANDARD_ROLES.md` defines the intended Standard role/permission model.

The executable Platform implementation is not yet present. `src/accore/platform/security/` currently contains only the package initializer, and repository-wide source search shows no implemented Principal, SecurityContext, authentication service, authorization service, or role/permission evaluator.

The Phase 11 architecture therefore reconciles the existing security documentation with the actual runtime architecture instead of creating a parallel conceptual model.

---

# 3. Phase 11 Objective

Implement the minimum security foundation necessary to establish the following execution boundary:

```text
Authentication
      ↓
Principal
      ↓
SecurityContext
      ↓
Authorization
      ↓
ALLOW / DENY
      ↓
Protected Operation
```

The phase must make authorization an explicit Platform capability rather than an application convention.

The architecture must support:

1. authenticated user identity;
2. runtime security context;
3. roles;
4. permissions;
5. protected security objects and operations;
6. centralized access evaluation;
7. default-deny behavior;
8. rejection of unauthorized operations;
9. Standard Configuration security composition;
10. deterministic and testable security behavior.

---

# 4. Architectural Position

Security is a Platform subsystem.

```text
accore.platform
├── configuration
├── metadata
├── object
├── persistence
├── posting
├── processing
├── query
├── registers
├── reporting
├── runtime
├── storage
├── validation
├── valuation
└── security
```

The dependency direction is:

```text
Application / Standard
          ↓
       Security
          ↓
   Metadata / Foundation
```

Security must not depend on Standard business modules such as Inventory, Sales, Purchasing, or Valuation.

Standard Configuration composes security definitions and assignments over the generic Platform security contracts.

---

# 5. Architectural Principles

## 5.1 Authentication and authorization are separate

Authentication answers:

> Who is the caller?

Authorization answers:

> May this authenticated principal perform this operation on this security object in this context?

Authentication failure terminates the protected operation before authorization is evaluated.

Authorization must never authenticate credentials itself.

---

## 5.2 SecurityContext is separate from RuntimeConfigurationContext

Phase 10 established `RuntimeConfigurationContext` as the authoritative immutable snapshot of active configuration.

Phase 11 must not place security state into that configuration object and must not create a second configuration context.

Instead:

```text
RuntimeConfigurationContext
        │
        └── configuration identity/version

SecurityContext
        │
        ├── Principal
        ├── Session (when applicable)
        └── request/execution security metadata
```

A protected execution may therefore conceptually carry both:

```text
Execution Context
├── RuntimeConfigurationContext
└── SecurityContext
```

Security identity is execution/session state, not configuration state.

---

## 5.3 Centralized authorization

Only the Security subsystem may produce authorization decisions.

Business components must not implement independent checks such as:

```python
if current_user.role == "Administrator":
    ...
```

or:

```python
if document.owner == current_user:
    ...
```

Such conditions belong to authorization rules and constraints evaluated by the Security subsystem.

---

## 5.4 Default deny

The authorization baseline is:

```text
No applicable permission
        ↓
      DENY
```

Unknown security object, unknown operation, missing role, missing permission, failed constraint evaluation, and unavailable security decision infrastructure must not result in implicit access.

---

## 5.5 Metadata-driven security

Authorization targets metadata-level security objects rather than Python implementation classes, database tables, or UI components.

The preferred target identity is therefore derived from the same stable metadata identity already used by the runtime architecture.

Conceptually:

```text
Metadata identity
      ↓
Security object identity
      ↓
Permission
      ↓
Authorization decision
```

This preserves the existing metadata-driven architecture and prevents security rules from being coupled to concrete runtime implementations.

---

## 5.6 Explicit operations

Operations are semantic security actions such as:

* Read;
* Write;
* Delete;
* Execute;
* Post;
* Unpost;
* Approve;
* Close;
* Configure;
* Administer;
* ManageUsers;
* Import;
* Export;
* Invoke.

The Platform defines operation semantics. Standard Configuration may assign permissions using these operations but must not create incompatible operation semantics inside individual business modules.

Phase 11 does not require every operation above to be implemented. The MVP needs a deliberately small initial operation set, with the architecture remaining extensible.

---

## 5.7 Roles aggregate permissions

A Role is an authorization composition mechanism.

```text
Role
 └── Permission(s)
```

Roles contain no business logic.

A principal may receive permissions through multiple roles. Effective permissions are the union of applicable role permissions, subject to authorization constraints.

---

## 5.8 Constraints refine permissions

A permission establishes that an operation is potentially allowed. A constraint may restrict the applicable context.

The semantic rule is:

```text
Permission exists
AND
All applicable constraints pass
        ↓
      ALLOW
```

Phase 11 must not introduce a general-purpose expression language or arbitrary policy scripting engine merely to support constraints.

The first implementation should use explicit, testable constraint contracts capable of supporting the Standard MVP. A future phase may introduce richer policy expressions if actual requirements justify them.

---

## 5.9 Fail closed

Security infrastructure failures must not silently become access grants.

Examples:

* authentication failure → DENY;
* unknown principal → DENY;
* unknown security object → DENY;
* missing permission → DENY;
* failed constraint evaluation → DENY;
* unavailable authorization state → DENY.

The precise distinction between a normal denial and an infrastructure error belongs to the Concrete API Design, but neither may become an accidental ALLOW.

---

# 6. Security Domain Scope

Phase 11 establishes the following conceptual entities.

## 6.1 User / identity subject

Represents the account or identity that can authenticate to the Standard Edition.

The first Standard Edition requires a concrete user identity model sufficient to support:

* stable identity;
* login/authentication association;
* active/inactive state;
* role assignment.

The Platform security model must not assume that every future Principal is a human user.

Service accounts and external identities remain compatible with the boundary, even if their concrete providers are deferred.

---

## 6.2 Principal

`Principal` is the runtime authenticated identity used by the rest of the system.

Conceptually it contains:

```text
Principal
├── principal identity
├── identity type
└── claims / identity attributes
```

Principal is not a permission record and is not itself an authorization decision.

Authentication creates or resolves the Principal; authorization evaluates the Principal.

---

## 6.3 Session

A Session represents an authenticated runtime session when the selected authentication boundary uses sessions.

The architecture must support:

* session identity;
* principal association;
* creation time;
* expiration/invalidation state.

The first implementation does not need to introduce a distributed session store. The abstraction must nevertheless keep session state separate from Principal identity so later providers can be added without changing authorization contracts.

---

## 6.4 SecurityContext

`SecurityContext` is the immutable execution-level security snapshot supplied to protected operations.

Conceptually:

```text
SecurityContext
├── Principal
├── Session | None
└── request metadata
```

Effective permissions and constraints may be resolved from the Principal/roles rather than permanently copied into every context. The Concrete API Design must choose whether resolved authorization data is represented as a derived immutable view or evaluated through a resolver.

SecurityContext must be safe to pass through Runtime and Processing boundaries without exposing authentication credentials.

---

## 6.5 Role

A Role is a stable security configuration object containing a set of permissions.

```text
Role
├── identity
├── code
├── name
└── permissions
```

Role definitions are configuration/security data, not business logic.

---

## 6.6 Permission

A Permission is the atomic authorization grant.

Its conceptual identity is:

```text
SecurityObject + Operation
```

Canonical representation:

```text
<ObjectType>.<ObjectCode>.<Operation>
```

Examples from the existing architecture include:

```text
Catalog.Products.Read
Document.GoodsReceipt.Read
Document.GoodsReceipt.Post
Register.Inventory.Read
Report.InventoryBalance.Execute
Processing.InventoryRebuild.Execute
```

The final set of MVP permissions must be selected from actual protected operations implemented in the repository rather than defined as a large speculative catalog.

---

## 6.7 SecurityObject

A SecurityObject identifies the resource being protected.

SecurityObject must remain independent from a concrete Python class.

The first implementation should support at least the object categories that already exist in the current architecture and are meaningful for the MVP:

* metadata/catalog objects;
* Processing definitions;
* reports;
* selected business/runtime operations.

Document/Register-specific security objects may be introduced where an actual operation is protected during Phase 11. Security must not require every current domain object to become secured simultaneously.

---

## 6.8 Authorization constraint

A constraint is an optional contextual restriction on an otherwise applicable permission.

Examples already documented by the project include:

* own organization;
* own warehouse;
* own department;
* own documents.

Phase 11 establishes the contract and evaluation boundary, but only constraints required by the MVP are implemented.

---

# 7. Authentication Boundary

The Platform defines an authentication boundary, not a UI-specific login implementation.

Conceptually:

```text
Credentials / external assertion
              ↓
     Authentication boundary
              ↓
          Principal
              ↓
           Session
              ↓
       SecurityContext
```

## 7.1 Provider independence

The rest of the Platform must not depend directly on:

* password database details;
* LDAP APIs;
* OAuth/OIDC SDKs;
* HTTP bearer-token handling;
* UI login forms.

Authentication mechanisms must be replaceable behind an explicit boundary.

## 7.2 MVP authentication

The first usable Standard Edition needs at least one concrete authentication path capable of producing an authenticated Principal.

The Phase 11 MVP shall provide one local authentication provider suitable for the current Standard Edition deployment model. External identity providers remain outside the phase, but the provider boundary must remain replaceable.

The local provider is an authentication composition concern, not the definition of the Platform authorization model. Credential verification must remain behind an explicit authentication-provider contract.

## 7.3 Credential handling

The Platform must never expose or persist clear-text passwords.

Password hashing/storage details belong to the authentication implementation, not to authorization or business modules.

Password policy values remain configuration concerns and must not be hardcoded into unrelated business components.

## 7.4 Authentication failure

Failed authentication produces no usable authenticated SecurityContext and must prevent protected execution.

Authorization must not be used to compensate for failed authentication.

---

# 8. Authorization Model

The authorization pipeline is:

```text
SecurityContext
      ↓
Security Object + Operation Resolution
      ↓
Permission Resolution through Roles
      ↓
Constraint Evaluation (when applicable)
      ↓
Authorization Decision
      ↓
ALLOW / DENY
```

The semantic decision is:

```text
Authenticated principal
AND
Applicable permission
AND
All applicable constraints pass
        ↓
      ALLOW
```

Otherwise:

```text
DENY
```

The authorization evaluator must be deterministic for the same security configuration and security context.

---

# 9. Access Enforcement Boundary

Authorization evaluation alone is insufficient. Protected operations must enforce the result before performing protected work.

The intended boundary is:

```text
Caller
  ↓
Security boundary
  ↓
Authorization
  ↓
Protected operation
```

The architecture must avoid requiring every low-level domain method to understand roles and permissions.

Authorization must be enforced at the public application/runtime operation boundary, before protected business execution begins. Lower-level domain methods must not be required to perform independent role or permission checks.

For Phase 11, the initial protected boundaries should be selected from operations that are already exposed through stable public contracts, with Processing being an especially clear candidate because Phase 10 explicitly deferred security.

---

# 10. Phase 10 Integration

Phase 10 established `ProcessingRuntime` as the public runtime boundary for processing commands and explicitly deferred authorization to Phase 11. Phase 11 therefore uses that boundary as its first mandatory enforcement point.

The required ordering is:

```text
ProcessingCommand
      ↓
ProcessingRuntime
      ↓
Authorization
      ↓
ProcessingContext
      ↓
Processing implementation
```

Authorization must occur before the processing implementation is entered. A denied command must therefore produce no processing-side business mutation.

`ProcessingContext` may carry the already-established `SecurityContext` for legitimate contextual use, but Processing implementations must not become authorization coordinators.


Phase 10 deliberately excluded authorization but preserved a future security boundary.

The Processing architecture currently has:

```text
ProcessingCommand
        ↓
ProcessingRuntime
        ↓
ProcessingContext
        ↓
Processing
```

Phase 11 must add security without turning Processing into a security implementation.

The intended conceptual flow becomes:

```text
ProcessingRuntime
      ↓
SecurityContext
      ↓
Authorization
      ↓
Processing execution
```

The Processing implementation should consume security context only if its execution contract genuinely requires it. It must not resolve users, roles, or permissions itself.

The preferred architecture is that the runtime/application boundary performs the authorization check before invoking the Processing implementation.

This preserves Phase 10's rule that Processing owns orchestration, not cross-cutting security policy.

---

# 11. Standard Configuration Scope

Standard Configuration composes the first usable security model over Platform contracts.

The Standard security composition must define at least:

1. the initial user/account model;
2. the initial roles;
3. the permissions associated with those roles;
4. the security objects protected by the MVP;
5. the authentication provider used by the Standard Edition;
6. the initial access defaults.

The Standard Configuration must not implement its own authorization algorithm.

Conceptually:

```text
Standard Security Configuration
        │
        ├── Users / identities
        ├── Roles
        ├── Permissions
        ├── Security objects
        └── Authentication composition
                ↓
        Platform Security Runtime
```

---

# 12. Standard Role Model Reconciliation

The existing `STANDARD_ROLES.md` defines a broader business role model with domains, object scopes, data scopes, and access modes.

Phase 11 should not implement the entire future Standard authorization matrix merely because it is documented.

The MVP shall establish the generic Platform model necessary to express the Standard role model while implementing only the subset needed to secure selected MVP operations.

The existing Standard concepts map as follows:

```text
Standard Domain/Object
        ↓
Security Object

Access Mode
        ↓
Platform Operation / permission semantics

Data Scope
        ↓
Authorization Constraint

Standard Role
        ↓
Platform Role
```

The distinction is important: Standard Configuration defines business-specific role composition; Platform Security defines the reusable mechanism.

---

# 13. Initial Protected Operations

Phase 11 must choose a small explicit set of protected operations for end-to-end verification.

The initial set should include at least:

### 13.1 Processing execution

Protect the Standard Inventory Derived State Rebuild Processing with an `Execute` permission.

This is the clearest integration point because Phase 10 already provides a stable Processing runtime and explicitly deferred authorization to Phase 11.

Conceptually:

```text
Processing.InventoryRebuild.Execute
```

### 13.2 Read access

Protect at least one stable Standard-readable object or report operation, preferably an existing Inventory Balance reporting operation.

Conceptually:

```text
Report.InventoryBalance.Read
```

or the final operation chosen by the Concrete API Design according to the existing Reporting contract.

### 13.3 Administrative security operation

Protect security administration itself behind an explicit permission.

Conceptually:

```text
System.Security.Administer
```

This ensures that role/permission administration is not implicitly available to every authenticated user.

The exact final identifiers are API-design concerns and must be reconciled against the actual Standard composition.

---

# 14. Unauthorized Operation Semantics

An unauthorized protected operation must not execute its business effect.

The required invariant is:

```text
Authorization = DENY
        ↓
Protected operation is not entered
        ↓
No business mutation
```

For operations that can fail after authorization, authorization denial must remain distinguishable from a normal business failure.

Security denial must not be represented as a successful business result.

The Concrete API Design must define the exact exception/result contract for unauthorized access.

---

# 15. Security and Persistence

Phase 11 requires security state that can survive the lifetime of an application process for a usable Standard Edition, but it does not introduce a generic security database framework.

The architecture separates:

```text
Security configuration/state
        ↓
Security persistence boundary

Runtime authorization
        ↓
In-memory immutable evaluation state
```

At minimum, the architecture must leave explicit persistence boundaries for:

* users/identities;
* role definitions and assignments;
* permission definitions/assignments;
* credential material managed by authentication providers;
* session state where sessions are persistent.

The first implementation may use the simplest repository/composition mechanism compatible with the current Standard Edition deployment model. Storage technology is not part of the Platform security contract.

Security must not reuse business persistence contracts merely because they already exist for Register, Valuation, or other domains.

---

# 16. Audit Boundary

The existing project security architecture defines audit as append-only and independent from business state.

Phase 11 must define security events at the boundary, but it must not turn authorization into an audit-storage implementation.

Security-relevant events include at minimum:

* authentication success;
* authentication failure;
* authorization denial;
* role assignment/removal;
* security administration changes;
* session termination where implemented.

The Security subsystem may emit audit events through an explicit boundary.

Audit storage remains a separate concern.

Because the current repository does not yet contain a general Audit subsystem, Phase 11 must not invent an undocumented audit persistence mechanism solely to satisfy security architecture prose. Security audit integration should therefore be represented as an explicit extension point and tested for event production where practical; durable audit storage may remain outside the phase unless the existing project architecture is extended to support it.

---

# 17. Runtime Propagation

Security must be available at the application/runtime boundary without coupling lower-level components to authentication mechanisms.

Conceptually:

```text
Authenticated request
        ↓
SecurityContext
        ↓
Runtime / application boundary
        ↓
Authorization
        ↓
Subsystem operation
```

For Processing:

```text
ProcessingRuntime
├── RuntimeConfigurationContext
└── SecurityContext
          ↓
     authorization
          ↓
     Processing
```

For future API/Integration:

```text
API boundary
      ↓
Authentication
      ↓
SecurityContext
      ↓
Authorization
      ↓
Runtime operation
```

The same Security contracts must be reusable across entry points.

The first concrete enforcement point is ProcessingRuntime. Future API/Integration entry points must authenticate and construct a SecurityContext before invoking the same authorization boundary rather than introducing transport-specific authorization logic.

---

# 18. Explicit Architectural Boundaries

## 18.1 Security owns

* Principal representation;
* SecurityContext;
* authentication boundary;
* authorization evaluation;
* Role and Permission semantics;
* SecurityObject identity;
* authorization constraints;
* access decision semantics;
* security-related errors/contracts;
* security composition contracts.

## 18.2 Security does not own

* business domain logic;
* document posting semantics;
* register totals;
* valuation algorithms;
* reporting calculations;
* Processing orchestration;
* Runtime configuration resolution;
* metadata compilation;
* generic persistence;
* UI login screens;
* HTTP/API transport;
* external identity-provider protocols.

---

# 19. Explicitly Rejected Approaches

Phase 11 must not introduce the following architectural shortcuts.

## 19.1 Role checks inside business code

Rejected:

```python
if user.role == "Administrator":
    ...
```

Reason: couples business logic to a specific authorization representation.

---

## 19.2 Permission dictionaries embedded in modules

Rejected:

```python
ALLOWED_USERS = {...}
```

or module-local permission tables.

Reason: creates multiple authorization systems and bypasses centralized evaluation.

---

## 19.3 Generic service/security bag

Rejected:

```text
SecurityServices
ApplicationServices
ServiceContainer
```

as an unrestricted dependency passed to every operation.

Reason: violates the explicit dependency model established in Phase 10.

---

## 19.4 Authentication inside business operations

Rejected:

```text
Processing -> Password verification
Posting -> Token parsing
Report -> Session lookup
```

Authentication belongs to the security boundary.

---

## 19.5 General-purpose policy scripting engine

Rejected for Phase 11.

Reason: the MVP requires access evaluation, not a full policy programming language. Explicit constraints are sufficient for the first implementation.

---

## 19.6 Security tied to Python classes

Rejected:

```text
Class -> permission
```

Security targets metadata/security identities, not implementation classes.

---

## 19.7 Security bypass for internal calls

Rejected:

```text
External call -> authorize
Internal call -> implicit trust
```

Internal composition may use trusted lower-level contracts where explicitly defined, but the public protected operation boundary must not silently bypass authorization.

---

# 19.8 Security model granularity for Phase 11

Phase 11 implements authorization at the `SecurityObject + Operation` level as the primary MVP mechanism. The architecture permits contextual constraints, but it does not require a universal row-level or record-filtering framework.

The initial model is therefore:

```text
Principal
  ↓
Role
  ↓
Permission
  ↓
SecurityObject + Operation
  ↓
optional explicit Constraint
  ↓
Decision
```

Standard role concepts such as Domain, Object Scope, Data Scope, and Access Mode are mapped onto these Platform primitives during Standard composition; they do not create a second authorization engine.

# 20. Testing Scope

Security behavior must be tested at three levels.

## 20.1 Unit tests

At minimum:

* Principal creation;
* SecurityContext immutability/semantics;
* Role permission aggregation;
* permission matching;
* default deny;
* constraint evaluation;
* authorization decisions;
* authentication success/failure boundary;
* security failure behavior.

## 20.2 Platform integration tests

Verify:

* authenticated Principal reaches a protected runtime boundary;
* an allowed permission permits execution;
* a missing permission prevents execution;
* a failed constraint prevents execution;
* authorization is evaluated before protected business work;
* authentication failure prevents authorization/execution;
* Security remains independent from concrete business implementations.

## 20.3 Standard integration tests

Verify at least:

1. a Standard user can be assigned a role;
2. the role grants the selected MVP permission;
3. the permitted Processing/report operation executes;
4. a user without the permission is denied;
5. role/permission changes affect subsequent access evaluation;
6. security behavior remains deterministic.

---

# 21. Phase 11 Scope

## In Scope — Platform

* Security package foundation;
* Principal;
* SecurityContext;
* authentication boundary;
* at least one concrete MVP authentication provider;
* Role;
* Permission;
* SecurityObject;
* Operation representation;
* authorization evaluator/service;
* default-deny access decisions;
* an explicit authorization-constraint boundary with only the minimum MVP constraint behavior required by selected protected operations;
* no general-purpose expression language or policy DSL;
* security-specific failure/denial contract;
* security context propagation at the selected protected runtime boundary;
* explicit composition contracts;
* tests of authentication and authorization behavior.

## In Scope — Standard Configuration

* initial Standard security configuration;
* initial users/identities needed by MVP tests/runtime;
* initial roles;
* initial permission assignments;
* initial protected Standard operations, including at least one execute operation, one read operation, and one security-administration operation;
* Standard authentication composition;
* role-to-permission composition;
* end-to-end unauthorized-operation rejection.

## In Scope — Documentation

* reconciliation of the existing security architecture documents with the implemented contracts;
* explicit mapping between Platform security concepts and Standard roles;
* documentation of protected MVP operations;
* security architectural boundary tests where appropriate.

---

# 22. Explicitly Out of Scope

The following are deferred unless required by an implementation dependency discovered during Concrete API Design.

## 22.1 External identity providers

No mandatory LDAP, OAuth2, OIDC, Entra, Keycloak, or similar integration.

The provider boundary must remain compatible with them.

## 22.2 Full enterprise identity lifecycle

No SCIM, directory synchronization, federation management, or enterprise provisioning.

## 22.3 Advanced policy engine

No general expression language, policy compiler, policy scripting, or arbitrary policy DSL.

## 22.4 Multi-tenancy security

Tenant isolation is not introduced by Phase 11.

## 22.5 Groups

Group-based permission assignment is deferred. Roles remain the primary permission aggregation mechanism.

## 22.6 Full data-filtering framework

The architecture permits contextual constraints, but Phase 11 does not implement a universal row-level/data-filter security engine. If a selected MVP operation does not require contextual constraints, no artificial data-scope engine is introduced merely to satisfy the model.

## 22.7 API security transport

Phase 12 owns API transport/security integration. Phase 11 provides the reusable authentication/authorization contracts required by that phase.

## 22.8 Complete audit subsystem

Security audit event production is an integration boundary. A full durable Audit subsystem is not introduced unless an existing project contract requires it.

## 22.9 UI security

No login UI, role administration UI, permission administration UI, or security screens are required.

## 22.10 Advanced session infrastructure

No distributed session store, SSO session federation, or cluster-wide session management.

## 22.11 Authorization caching

No complex distributed permission cache is required. Any in-process derived authorization state must remain invalidatable or reconstructible from authoritative security configuration.

---

# 23. Acceptance Criteria

## AC-1 — User Security Context

An authenticated user can be represented by a Principal and SecurityContext at a protected execution boundary.

## AC-2 — Authentication Boundary

Authentication is separated from authorization and produces an authenticated Principal on success.

Authentication failure prevents protected execution.

## AC-3 — Permission Evaluation

A permission can be resolved for a Principal through assigned roles and evaluated against a SecurityObject and Operation.

## AC-4 — Role Definition

Roles can be defined and can aggregate permissions.

## AC-5 — Access Control

At least one Standard object/operation is protected by a permission.

## AC-6 — Unauthorized Rejection

A Principal without the required permission receives a denial and the protected operation does not execute its business effect.

## AC-7 — Constraint Evaluation

Where the MVP uses a contextual constraint, a permission with a failed constraint is denied. The constraint mechanism is explicit and bounded; no general-purpose policy expression language is required.

## AC-8 — Default Deny

Missing or unresolved permissions do not grant access.

## AC-9 — Standard Composition

Standard Configuration can compose users/identities, roles, permissions, authentication, and selected protected operations without implementing its own authorization algorithm.

## AC-10 — Security Tests

Authentication, authorization, role aggregation, denial, constraint behavior where applicable, and at least one end-to-end Standard protected operation are covered by automated tests. Tests must verify that denial occurs before protected business execution.

## AC-11 — Architectural Independence

Security does not depend on Inventory, Valuation, Register, Reporting, or Processing implementation details.

## AC-12 — Documentation Reconciliation

The existing security architecture documents are reconciled with the implemented Phase 11 contracts; obsolete claims are corrected rather than silently preserved.

---

# 24. Architectural Invariants

### Invariant 1

Authentication and authorization remain separate responsibilities.

### Invariant 2

Only authenticated principals may execute authenticated protected operations.

### Invariant 3

No permission means DENY.

### Invariant 4

Security failures cannot become implicit ALLOW decisions.

### Invariant 5

Authorization decisions are produced centrally by Platform Security.

### Invariant 6

Business components do not contain role-specific authorization logic.

### Invariant 7

Security targets stable security/metadata identities, not Python implementation classes.

### Invariant 8

Roles aggregate permissions; roles do not contain business behavior.

### Invariant 9

Constraints refine permissions; constraints do not replace permission grants.

### Invariant 10

SecurityContext is separate from RuntimeConfigurationContext.

### Invariant 11

Standard Configuration composes security but does not implement the authorization algorithm.

### Invariant 12

Authentication providers are replaceable behind an explicit boundary.

### Invariant 13

Credentials are never exposed to business operations or stored as clear text.

### Invariant 14

An unauthorized operation produces no protected business side effect.

### Invariant 15

Security behavior is deterministic and testable.

### Invariant 16

Phase 11 does not introduce a generic service container, policy scripting engine, or enterprise identity platform.

---

# 25. Concrete API Design Boundary

The subsequent Concrete API Design must resolve, without reopening the architectural scope unless new repository evidence requires it:

1. exact Principal representation;
2. exact SecurityContext fields and immutability semantics;
3. exact authentication provider protocol;
4. exact authentication result/error contract;
5. exact Session representation;
6. exact Role and Permission representations;
7. exact SecurityObject and Operation identities;
8. exact permission matching rules;
9. exact constraint protocol and MVP constraint set;
10. exact AuthorizationService/evaluator contract;
11. exact ALLOW/DENY result representation;
12. exact unauthorized exception/result contract;
13. exact runtime/Processing authorization integration point;
14. exact Standard bootstrap/composition boundary;
15. exact persistence boundaries for security configuration;
16. exact security event/audit emission boundary;
17. exact MVP protected operations;
18. exact unit/integration/vertical test matrix.

The Concrete API Design must not expand Phase 11 into external identity integration, a general policy engine, or a complete security administration UI.

---

# 26. Implementation Decomposition Guidance

The implementation should be decomposed into small architectural slices, but the exact slice boundaries belong to the approved Concrete API Design.

A likely decomposition is:

```text
Slice 1 — Domain contracts
    Principal / Role / Permission / SecurityObject / Operation

Slice 2 — Authentication boundary
    provider / authentication result / session / security context

Slice 3 — Authorization engine
    permission resolution / constraints / decisions

Slice 4 — Runtime enforcement
    selected protected operation boundary

Slice 5 — Standard composition
    users / roles / permissions / protected MVP operations

Slice 6 — Integration tests and documentation reconciliation
```

This is implementation guidance, not an approval of concrete API names.

---

# 27. Architecture Review Decision

The Architecture Review identified no fundamental architectural conflict with the current AcCoreD baseline. The following decisions are mandatory amendments incorporated into this final document:

1. `SecurityContext` remains separate from `RuntimeConfigurationContext`.
2. ProcessingRuntime is the first mandatory authorization enforcement point.
3. Authorization occurs before `Processing` execution and therefore before protected business side effects.
4. `SecurityContext` may propagate through `ProcessingContext`, but Processing does not perform its own authorization.
5. Phase 11 provides a local MVP authentication provider behind a replaceable provider boundary.
6. `User` and runtime `Principal` remain distinct concepts.
7. Role → Permission → SecurityObject + Operation is the primary MVP authorization model.
8. Constraints are represented by an explicit contract; no general-purpose policy/expression DSL is introduced.
9. Data-scope authorization remains a supported architectural extension, not a mandatory full row-level security engine.
10. Standard roles remain configuration/composition; Standard does not implement a second authorization evaluator.
11. The initial protected operation set includes execute, read, and security-administration scenarios.
12. Authorization denial must prevent protected operation entry and business side effects.
13. Security audit is an event boundary; durable audit storage is not part of Phase 11.
14. Security failure semantics distinguish authorization denial from security infrastructure failure while both remain fail-closed.
15. Security persistence contracts remain independent of existing business persistence contracts.

These decisions close the Architecture Review findings and form the required input for the Concrete API Design.

# 27. Final Architectural Decision

Phase 11 shall introduce Security as a first-class Platform subsystem built around:

```text
Authentication
      ↓
Principal
      ↓
SecurityContext
      ↓
Role → Permission → SecurityObject + Operation
      ↓
Constraint Evaluation
      ↓
Authorization Decision
      ↓
Protected Operation
```

The architecture deliberately separates:

* configuration state from runtime security state;
* authentication from authorization;
* generic Platform security from Standard role composition;
* authorization evaluation from business execution;
* security events from audit storage.

The first implementation is intentionally narrow: it must make the Standard Edition securely usable for selected operations, establish a reusable authorization boundary, and prove that unauthorized operations cannot execute.

It must not attempt to complete the future enterprise security architecture in one phase.

**Status: Architecture Review complete — Approved as the basis for Concrete API Design**
