# AcCoreD — Phase 11
# Slice 3 — Authorization Architecture Definition / Scope

**Status:** Final Architecture Definition / Scope — Approved for Concrete API Design

**Phase:** 11 — Security

**Slice:** 3 — Authorization

**Baseline:** `AcCoreD_cur11(2).zip` / commit `7862abd` — `feat(security): implement Phase 11 Slice 2 authentication`

---

# 1. Purpose

This document defines the architectural scope for Phase 11 Slice 3 — Authorization.

The slice introduces the Platform authorization boundary required to answer one question safely and deterministically:

> Given an explicit `SecurityContext`, a protected security object, and an operation, may the current principal perform that operation?

The slice implements the authorization model already approved by the Phase 11 Architecture Definition / Scope. It does **not** introduce runtime enforcement into Processing; that belongs to Slice 4.

The objective is to establish a reusable Platform authorization engine with explicit contracts for:

- authorization requests;
- security-state resolution;
- permission matching;
- constraint evaluation;
- authorization decisions;
- normal denial;
- security infrastructure failure;
- protected-boundary enforcement through an authorization service.

No implementation is approved by this document. Concrete class names, method signatures, module placement, and exact test fixtures are resolved in the subsequent Concrete API Design.

---

# 2. Baseline

The current baseline contains the Phase 11 security domain and authentication boundary.

Already implemented:

- `User`;
- `Principal` and `PrincipalType`;
- `SecurityClaim`;
- `Session` and `SessionState`;
- `SecurityContext`;
- `SecurityObjectIdentity`;
- `SecurityOperation`;
- `Permission`;
- `Role`;
- `AuthorizationConstraint` contract;
- security error hierarchy;
- `PasswordCredentials`;
- `PasswordVerifier` boundary;
- authentication provider contract;
- authentication result;
- security repositories;
- local Standard authentication provider;
- Standard in-memory user/credential/session persistence.

The latest committed baseline is:

```text
7862abd feat(security): implement Phase 11 Slice 2 authentication
```

Slice 2 passed its unit tests and repository quality gate before commit.

The current repository already contains the approved Phase 11 Architecture Definition / Scope and Concrete API Design. This Slice 3 document narrows that approved architecture to the authorization implementation boundary.

---

# 3. Architectural Objective

Slice 3 must establish authorization as a first-class Platform service rather than as role checks embedded in business code.

The resulting architecture is:

```text
SecurityContext
      │
      ▼
Authorization Request
      │
      ▼
Authoritative Security State
      │
      ▼
Role → Permission Resolution
      │
      ▼
Exact SecurityObject + Operation Matching
      │
      ▼
Constraint Evaluation
      │
      ▼
Authorization Decision
      │
      ├── ALLOW
      └── DENY
```

A protected application boundary will later call the same authorization service through Slice 4. Slice 3 itself does not modify `ProcessingRuntime`.

---

# 4. Architectural Position

Authorization belongs to `accore.platform.security`.

It is a Platform concern because:

1. authorization semantics are independent of business domains;
2. permission matching is based on stable security metadata;
3. roles aggregate permissions without containing business behavior;
4. authorization must be reusable by Processing and future application/API boundaries;
5. Standard configuration supplies security state but must not implement a second authorization engine.

The dependency direction remains:

```text
Platform Security
      ↑
Standard Security Composition
      ↑
Application / Runtime boundaries
```

Business modules do not own authorization policy evaluation.

---

# 5. Mandatory Architectural Principles

## 5.1 Explicit security context

Authorization receives an explicit immutable `SecurityContext`.

The authorization layer consumes the security snapshot prepared by the authentication/session boundary. Authorization does not validate sessions, consult `SessionStore`, refresh sessions, or mutate session state.

There is no module-global current principal and no implicit authorization context.

`contextvars`-based ambient security state is not introduced by this slice.

## 5.2 Authentication and authorization remain separate

Authentication establishes a `Principal` and optionally a `Session`.

Authorization consumes the resulting security context and evaluates access.

The authorization service must not authenticate credentials or create sessions.

## 5.3 Centralized authorization

All authorization decisions are made through the Platform authorization boundary.

Business/domain methods must not contain independent role or permission checks merely to enforce Phase 11 security.

## 5.4 Default deny

A principal receives access only when an explicit matching permission grants it.

No matching permission means denial.

Unknown security objects and operations therefore fail closed without requiring a global security-object registry.

## 5.5 Exact target and operation matching

A permission matches only when both are equal:

```text
Permission.target == Request.target
AND
Permission.operation == Request.operation
```

There is no wildcard expansion, prefix matching, implicit inheritance, or fuzzy matching.

## 5.6 Roles are additive

A user's effective permissions are the union of permissions supplied by the user's assigned roles.

There is no role hierarchy.

There are no deny permissions.

A failed permission does not negate an independent matching permission that grants access.

## 5.7 Constraints refine permissions

Constraints can further restrict an individual permission.

For one permission:

```text
matching permission
AND
all of that permission's constraints pass
        ↓
permission grants
```

Across multiple matching permissions:

```text
Permission A grants
OR
Permission B grants
OR
...
        ↓
ALLOW
```

This is **OR across matching permissions and AND across constraints within one permission**.

## 5.8 No policy language

Constraints are explicit executable Platform contracts.

Slice 3 does not introduce:

- `eval`;
- expression parsing;
- policy scripting;
- policy compilation;
- user-supplied authorization programs;
- a general policy DSL.

## 5.9 Fail closed

Missing or invalid authoritative security state must never produce `ALLOW`.

A security infrastructure failure is distinct from an ordinary authorization denial and must remain observable as such.

---

# 6. Authorization Scope

Slice 3 owns the following concerns.

## 6.1 Authorization request

An immutable request must contain:

- `SecurityContext`;
- target `SecurityObjectIdentity`;
- `SecurityOperation`;
- optional contextual authorization resource for a concrete constraint, if required.

The request is a value object, not a service locator or dependency bag.

## 6.2 Authoritative security-state resolution

Authorization needs access to authoritative state sufficient to resolve:

```text
Principal → User/security subject → assigned Role → Permissions
```

For `PrincipalType.USER`, the existing Phase 11 invariant remains:

```text
Principal.identity == User.identity
```

No second user/principal identity-mapping namespace is introduced for the MVP.

The state boundary must be replaceable and must not depend on a particular database, ORM, or transport framework.

## 6.3 Permission resolution

The evaluator resolves every role assigned to the authoritative user and considers the union of their permissions.

Missing role state is not interpreted as an empty role. It is a security-state problem and therefore fails safely.

## 6.4 Permission matching

Matching is exact on:

```text
SecurityObjectIdentity + SecurityOperation
```

The permission's persistent `identity` is not the semantic matching key.

## 6.5 Constraint evaluation

For every matching permission, all of its constraints must pass for that permission to grant access.

A constraint failure produces ordinary denial unless the constraint cannot safely evaluate because required authoritative infrastructure is unavailable; such infrastructure failure remains distinct.

## 6.6 Authorization decision

The evaluator returns an explicit decision representing:

- `ALLOW`;
- `DENY` with a meaningful denial reason.

The decision must not encode infrastructure failure as an ordinary allow/deny outcome.

## 6.7 Enforcement helper

Slice 3 provides the authorization boundary required by future protected operations.

The architecture requires two semantic modes:

1. **decision mode** — evaluate access without throwing for an ordinary denial;
2. **enforcement mode** — allow returns normally; denial raises the dedicated authorization-denied error.

The exact API names are deferred to Concrete API Design.

---

# 7. Security State Resolution

The authorization engine must not embed persistence logic.

Conceptually:

```text
Authorization Service
        │
        ▼
Security Authorization State
        │
        ├── User resolution
        └── Role resolution
```

The state provider is responsible for authoritative configuration lookup.

The evaluator is responsible for authorization semantics.

This separation allows Standard to use in-memory persistence in Phase 11 without making in-memory storage part of Platform authorization semantics.

## 7.1 User resolution

For a user principal, the authoritative user must resolve successfully.

An absent or unavailable user cannot grant access.

An authenticated context with `principal is None` is handled as a normal authorization denial with the `UNAUTHENTICATED` semantic reason. It is not an infrastructure failure.

## 7.2 Active-state check

For a USER principal, the authoritative `User.active` state must be active for authorization to proceed to permission evaluation.

An inactive user receives denial.

The inactive state is not converted into a permission configuration error.

Session state is deliberately not re-evaluated here. `Session.ACTIVE`, `EXPIRED`, and `INVALIDATED` are validated by the authentication/session boundary before the `SecurityContext` reaches authorization.

## 7.3 Role resolution

Every role identity assigned to the user must resolve.

A missing assigned role indicates inconsistent/unavailable authoritative security state and must not silently reduce or expand permissions.

## 7.4 No role caching

The principal does not cache roles or effective permissions.

Role assignment changes therefore affect subsequent authorization calls without rebuilding the principal.

Authorization caching is explicitly outside Phase 11.

---

# 8. Authorization Decision Semantics

The semantic flow is:

```text
No Principal
    → DENY / UNAUTHENTICATED

Inactive User
    → DENY / INACTIVE_PRINCIPAL

No matching permission
    → DENY / MISSING_PERMISSION

Matching permission + failed constraints
    → DENY / CONSTRAINT_FAILED

At least one matching permission with all constraints passing
    → ALLOW

Security state cannot be resolved safely
    → Security Infrastructure Failure
```

The exact enum/type names are a Concrete API concern, but the semantic distinctions above are mandatory.

An `ALLOW` decision must never carry a denial reason.

A normal `DENY` decision must carry a reason.

Infrastructure failure must not be represented as `ALLOW`.

---

# 9. Multiple Matching Permissions

The following rule is mandatory:

```text
For each matching Permission:
    permission_grants = every constraint passes

ALLOW if any permission_grants is true
DENY otherwise
```

Example:

```text
Role A:
    Report.InventoryBalance.Read

Role B:
    Report.InventoryBalance.Read + contextual constraint
```

If Role B's constraint fails, Role A's unconstrained permission can still grant access.

Slice 3 does not introduce deny-overrides semantics.

---

# 10. Constraint Scope

The constraint contract is part of the authorization architecture because `Permission` already carries constraints.

However, Slice 3 does not require a concrete Standard data-scope constraint.

The initial implementation must prove only the contract semantics:

1. no constraints can grant when the permission matches;
2. a passing constraint can grant;
3. a failing constraint prevents that permission from granting;
4. contextual data is explicit rather than supplied through a generic service bag;
5. constraint failure cannot independently grant access.

A concrete data-scope constraint is introduced only if a selected Phase 11 MVP protected operation genuinely requires it.

---

# 11. Authorization Resource Boundary

The architecture supports a contextual resource for future constraints.

The resource must remain narrow:

- it identifies the contextual protected resource instance;
- it exposes only data explicitly required by a concrete constraint;
- it does not become a generic application context;
- it does not alter the base target+operation matching rule.

A generic `Mapping[str, object]` authorization bag is not part of the public architecture.

`AuthorizationResource.identity` is contextual resource identity only. It does not participate in basic permission matching and does not replace the permission target. The base matching key remains exactly `SecurityObjectIdentity + SecurityOperation`.

---

# 12. Unknown Security Objects and Operations

The evaluator does not require a global registry of every security object.

Therefore an unknown target or operation is simply unmatched unless an explicit permission exists for that exact target and operation.

Semantically:

```text
unknown target/operation
        ↓
no matching permission
        ↓
DENY / MISSING_PERMISSION
```

There is no separate `UNKNOWN_TARGET` outcome in the MVP architecture.

---

# 13. Error Boundary

Slice 3 distinguishes two fundamentally different cases.

## 13.1 Normal authorization denial

The security system successfully evaluated the request and determined that access is not granted.

Examples:

- no authenticated principal;
- inactive user;
- missing permission;
- failed constraint.

Normal denial is represented by an authorization decision and, at an enforcement boundary, by `AuthorizationDeniedError`.

## 13.2 Security infrastructure failure

The security system cannot safely determine authorization because authoritative security state is unavailable or inconsistent.

Examples:

- required user state cannot be resolved;
- assigned role cannot be resolved;
- authoritative security repository fails;
- security configuration is inconsistent.

A constraint that evaluates to `false` is a normal authorization outcome and produces constraint-based denial. A constraint is an infrastructure failure only when it cannot safely evaluate because required authoritative security infrastructure is unavailable or inconsistent.

Such failures propagate as security infrastructure/configuration failures.

They must never become `ALLOW`.

---

# 14. Enforcement Boundary for This Slice

Slice 3 establishes the reusable authorization enforcement service but does **not** modify the Processing runtime.

The intended future sequence is:

```text
Caller
  ↓
ProcessingRuntime       ← Slice 4
  ↓
AuthorizationService    ← Slice 3
  ↓
Processing
```

The authorization service itself must not know how Processing executes.

It receives a generic security request and returns/enforces the authorization result.

This preserves the Platform security boundary and prevents business-specific coupling.

---

# 15. Processing Boundary Is Deferred

The following changes are explicitly deferred to Slice 4:

- adding `SecurityContext` to `ProcessingRuntime.execute(...)`;
- propagating `SecurityContext` through `ProcessingContext`;
- mapping a `ProcessingIdentity` to its security object;
- requiring authorization before Processing execution;
- proving that denial prevents protected side effects.

Slice 3 may include generic authorization tests, but it must not alter Processing contracts merely to prove the authorization engine.

---

# 16. Standard Boundary

Standard owns security configuration, not authorization semantics.

Standard may provide:

- users;
- role definitions;
- permissions assigned to those roles;
- concrete persistence adapters;
- configuration/composition of the Platform authorization service.

Standard must not provide:

- a second authorization evaluator;
- Standard-only permission matching rules;
- a Standard-specific deny/allow algorithm;
- role hierarchy;
- wildcard expansion.

The existing Standard authentication provider remains unchanged by Slice 3 except where composition requires a dependency to the new authorization service.

Such composition changes belong to the later Standard slice unless strictly required for constructing the authorization state provider.

---

# 17. Persistence Boundary

Slice 3 defines authorization state contracts, not a database schema.

The architecture requires persistence independence:

```text
Authorization Evaluator
        ↓
Security Authorization State contract
        ↓
Security persistence adapter
```

The existing business persistence subsystem must not be reused merely because it already exists.

An in-memory Standard implementation is acceptable for Phase 11 MVP testing.

Durable security persistence design remains a separate concern.

---

# 18. Security Events

Slice 3 does not implement the durable audit subsystem.

Authorization decisions must remain observable enough for the later security-event boundary to distinguish:

- authorization allowed;
- authorization denied;
- security infrastructure failure.

Event emission and durable audit storage remain in the later Phase 11 event/documentation slice.

The authorization engine must therefore avoid coupling itself to an audit database or event transport.

---

# 19. Explicitly Out of Scope

The following are not part of Slice 3:

1. Processing runtime enforcement;
2. API/HTTP transport authorization;
3. external identity providers;
4. enterprise identity lifecycle;
5. groups;
6. role hierarchy;
7. wildcard permissions;
8. deny permissions;
9. policy/expression DSL;
10. authorization caching;
11. multi-tenancy;
12. complete row-level/data-filtering framework;
13. security administration CRUD framework;
14. durable audit storage;
15. UI security;
16. database-specific authorization schema;
17. service-locator based security context;
18. implicit global current-user state.

---

# 20. Required Tests

Slice 3 must prove the authorization semantics independently of Processing.

## 20.1 Basic decisions

At minimum:

1. authenticated principal + matching permission → ALLOW;
2. no principal → DENY / unauthenticated;
3. inactive user → DENY / inactive principal;
4. no matching permission → DENY / missing permission;
5. unknown target → DENY / missing permission;
6. unknown operation → DENY / missing permission.

## 20.2 Role aggregation

At minimum:

1. permissions from multiple assigned roles form a union;
2. duplicate permission grants are harmless;
3. role assignment changes affect subsequent evaluations;
4. a missing assigned role fails safely rather than granting or silently altering access.

## 20.3 Constraints

At minimum:

1. matching permission without constraints → ALLOW;
2. matching permission with passing constraint → ALLOW;
3. matching permission with failing constraint → DENY / constraint failed;
4. one failed constrained permission does not override another independent matching permission;
5. all constraints within one permission must pass for that permission to grant;
6. constraint evaluation failure cannot grant access.

## 20.4 Infrastructure failure

At minimum:

1. user-resolution failure propagates as security infrastructure failure;
2. role-resolution failure propagates as security infrastructure failure;
3. infrastructure failure is never converted to ALLOW;
4. infrastructure failure is distinguishable from ordinary authorization denial.

## 20.5 Enforcement helper

At minimum:

1. ALLOW returns normally;
2. DENY raises the dedicated authorization-denied error;
3. the denial error retains the authorization decision/reason;
4. infrastructure errors remain infrastructure errors.

---

# 21. Architectural Tests

Where practical, Slice 3 should include architecture-oriented tests preventing prohibited coupling.

Examples:

- Platform security authorization does not import Inventory/Valuation/Register implementations;
- authorization does not import Processing runtime implementation;
- Standard security does not define an independent evaluator;
- security contracts do not depend on HTTP/API frameworks;
- security contracts do not depend on ORM/database implementation types;
- authorization does not use module-global mutable principal state.

---

# 22. Acceptance Criteria

## AC-1 — Explicit Request

Authorization can evaluate an immutable request containing security context, target, operation, and optional contextual resource.

## AC-2 — Authoritative Resolution

Authorization resolves the user and assigned roles through explicit security-state contracts.

## AC-3 — Exact Permission Matching

Only exact target + operation matches are considered.

## AC-4 — Role Union

Effective permissions are the union of permissions from all assigned roles.

## AC-5 — Constraint Semantics

Constraints are AND within a permission and permissions are OR across matching grants.

## AC-6 — Default Deny

Missing permissions and unknown targets/operations are denied.

## AC-7 — Explicit Decision

Authorization exposes ALLOW/DENY semantics with explicit denial reasons.

## AC-8 — Fail Closed

Security infrastructure failures cannot produce ALLOW.

## AC-9 — Enforcement Boundary

An enforcement-oriented authorization operation converts ordinary DENY into the dedicated authorization-denied error while preserving infrastructure failures.

## AC-10 — No Processing Coupling

Processing runtime and Processing contracts remain unchanged in Slice 3.

## AC-11 — Standard Independence

Standard supplies configuration/state adapters but does not implement a second evaluator.

## AC-12 — Test Coverage

The required authorization semantics and architectural boundaries are covered by unit tests and quality checks.

---

# 23. Architectural Invariants

The following invariants are mandatory.

### Invariant 1

No explicit matching permission means no ALLOW.

### Invariant 2

Authorization never authenticates credentials.

### Invariant 3

Authorization never validates, creates, refreshes, invalidates, or otherwise mutates sessions.

### Invariant 4

Principal identity and authorization role state remain distinct.

### Invariant 5

For USER principals, Principal identity equals User identity.

### Invariant 6

Permission matching is exact on SecurityObjectIdentity + SecurityOperation.

### Invariant 7

Roles are additive and have no inheritance.

### Invariant 8

There are no deny permissions in Phase 11.

### Invariant 9

Wildcard permissions are not interpreted.

### Invariant 10

All constraints of one matching permission must pass before that permission grants access.

### Invariant 11

A failed permission does not deny an independent matching permission that grants access.

### Invariant 12

Unknown targets and operations fail closed through missing-permission semantics.

### Invariant 13

Security infrastructure failure can never become ALLOW.

### Invariant 14

`principal is None` is a normal `UNAUTHENTICATED` denial; it is not a security infrastructure failure.

### Invariant 15

Authorization does not revalidate `Session.state`; session validation belongs to the authentication/session boundary.

### Invariant 16

Authorization state is resolved from authoritative state; principals do not cache permissions.

### Invariant 17

Authorization does not depend on Processing implementation details.

### Invariant 18

No module-global mutable current-principal state is introduced.

### Invariant 19

No general-purpose policy DSL is introduced.

### Invariant 20

Standard configuration cannot replace or fork the Platform authorization algorithm.

# 24. Implementation Decomposition Guidance

After Architecture Review approval, the Concrete API Design should resolve the following implementation pieces as one coherent API:

```text
Authorization request/value objects
        ↓
Security authorization state contract
        ↓
Permission resolution
        ↓
Constraint evaluation
        ↓
Authorization decision
        ↓
Authorization service / enforcement operation
        ↓
Unit and architectural tests
```

The Concrete API Design must decide exact module boundaries and exports without reopening the approved semantics above.

No implementation should begin before that API design is reviewed and approved.

---

# 25. Architecture Review Questions

The Architecture Review should explicitly confirm:

1. Is the authorization state boundary sufficiently independent from existing business persistence?
2. Is the distinction between normal denial and infrastructure failure precise enough for later runtime enforcement and events?
3. Does OR-across-permissions / AND-within-constraints correctly preserve the approved additive role model?
4. Is exact target + operation matching sufficient for the Phase 11 MVP without a global security-object registry?
5. Is the optional authorization resource sufficiently narrow to avoid becoming a generic context bag?
6. Are role changes correctly visible without rebuilding principals?
7. Is the enforcement helper appropriately generic while leaving Processing enforcement to Slice 4?
8. Does the design preserve the boundary that Standard configures security but does not implement authorization semantics?
9. Are there any accidental policy-engine, caching, hierarchy, wildcard, deny-rule, transport-security, or business-domain semantics?
10. Does the proposed Slice 3 API leave the existing Slice 2 authentication boundary unchanged?

---

# 26. Architecture Review Decision

**Architecture Review complete — Approved for Concrete API Design**

The Architecture Review confirms that Slice 3 is consistent with the approved Phase 11 security architecture and the implemented Slice 1–2 boundaries.

The following amendments are incorporated into this final version:

1. Authorization consumes a prepared `SecurityContext` and does not validate or mutate session state.
2. `principal is None` produces normal `UNAUTHENTICATED` denial.
3. `User.active` is distinct from `Session.state`; session validation remains outside authorization.
4. Infrastructure failure is limited to inability to safely resolve or evaluate authoritative security state; ordinary constraint failure remains normal denial.
5. OR-across-permissions / AND-within-constraints is an explicit architectural invariant.
6. `AuthorizationResource.identity` is contextual only and does not participate in base target + operation matching.

The approved architecture is therefore ready for the next workflow stage: **Concrete API Design**.

Implementation remains prohibited until the Concrete API Design has been reviewed and approved.


**Pending Architecture Review.**

This document is the Slice 3 architectural basis for the subsequent Concrete API Design. Any review amendments must be incorporated here before concrete implementation contracts are finalized.
