# Phase 11 — Slice 3: Authorization
## Concrete API Design

**Status:** Approved for Implementation
**Phase:** 11 — Security
**Slice:** 3 — Authorization
**Scope:** Platform authorization contracts, evaluator, enforcement primitive, and Standard composition

---

## 1. Purpose

This document is the final Concrete API Design for Phase 11 Slice 3 — Authorization.

The slice introduces a reusable authorization engine in `accore.platform.security` and a Standard composition that supplies authoritative security state. Authorization consumes an already prepared `SecurityContext`; authentication, session validation, and request-processing integration remain outside this slice.

Slice 3 must not modify `ProcessingRuntime`. Processing enforcement is the subject of Slice 4.

The design is intentionally narrow:

- exact target + operation permission matching;
- additive role aggregation;
- AND semantics for constraints within a permission;
- OR semantics across matching permissions;
- fail-closed behavior;
- explicit imperative enforcement through `require()`;
- no caching;
- no ambient/global principal;
- no generic policy DSL;
- no wildcard permissions;
- no role hierarchy;
- no business-specific data filtering.

---

## 2. Approved API Review Amendments

The API review produced the following final decisions:

1. Keep `AuthorizationRequest`, `AuthorizationDecision`, `AuthorizationOutcome`, and `AuthorizationDenyReason`.
2. Keep `AuthorizationResource` as a Protocol rather than introducing a mandatory concrete value object.
3. Do not introduce a separate `AuthorizationDecisionOutcome`; use `AuthorizationOutcome`.
4. `AuthorizationRequest` does not contain a separate `claims` field. Claims remain on `request.context.principal.claims`.
5. `AuthorizationDenyReason.INACTIVE_PRINCIPAL` replaces `INACTIVE_USER`.
6. Do not expose infrastructure/configuration failures as ordinary denial reasons.
7. Introduce `SecurityAuthorizationState` as the semantic authoritative-state boundary. The default authorization service does not depend directly on user/role repositories.
8. MVP authorization supports `PrincipalType.USER` only. Other principal types fail closed as unsupported security configuration/state.
9. Every assigned role must resolve before an authorization decision can become `ALLOW`.
10. `AuthorizationConstraint.evaluate()` returns `bool`; `False` is an ordinary constraint failure, while infrastructure/security-state exceptions propagate.
11. `AuthorizationService.require()` is a mandatory public enforcement primitive.
12. `AuthorizationDeniedError` is part of the existing security error hierarchy and retains the denied `AuthorizationDecision`.
13. Standard composes the Platform evaluator and may adapt its existing repositories to `SecurityAuthorizationState`; it must not implement a second authorization evaluator.

---

## 3. Package Structure

The implementation belongs in the existing security package. A representative structure is:

```text
src/accore/platform/security/
    authorization.py
    errors.py
    __init__.py

src/accore/standard/security/
    authorization.py
    composition.py
    __init__.py
```

The exact file split may follow the current repository conventions, but the architectural ownership is fixed:

- Platform owns authorization contracts, algorithm, and generic errors.
- Standard owns configuration, concrete state adapters, and Standard-specific permission/role definitions.

No authorization implementation is duplicated in Processing or Standard.

---

## 4. Existing Domain Contracts

Slice 3 consumes existing security-domain concepts:

- `Principal`
- `PrincipalType`
- `SecurityContext`
- `Session`
- `User`
- `Role`
- `Permission`
- `SecurityObjectIdentity`
- `SecurityOperation`
- `SecurityClaim`
- existing security error hierarchy

The authorization engine does not redefine these concepts.

The existing `Principal` remains the source of identity and claims. The existing `SecurityContext` remains the prepared security context supplied to authorization.

---

## 5. Authorization Resource

`AuthorizationResource` is an optional contextual input.

```python
class AuthorizationResource(Protocol):
    @property
    def identity(self) -> Identifier: ...
```

Its semantics are deliberately limited:

- it does not participate in base permission matching;
- it does not replace `Permission.target`;
- it does not define a second permission key;
- it does not imply ownership, tenancy, or data filtering;
- it exists so future constraints can inspect contextual resource information without changing the core authorization request shape.

A resource may therefore be supplied to a request while the base permission check remains solely:

```text
permission.target == request.target
AND
permission.operation == request.operation
```

---

## 6. Authorization Request

The final request type is:

```python
@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    context: SecurityContext
    target: SecurityObjectIdentity
    operation: SecurityOperation
    resource: AuthorizationResource | None = None
```

### Invariants

- `context` is the prepared security context.
- `target` identifies the protected security object.
- `operation` identifies the requested operation.
- `resource` is optional contextual information.
- There is no `claims` field.
- Claims are obtained from `request.context.principal.claims` when an explicit constraint needs them.

The request is immutable and contains no mutable authorization state.

---

## 7. Authorization Outcome

```python
class AuthorizationOutcome(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
```

Only these two ordinary authorization outcomes exist.

Infrastructure/configuration failures are not encoded as a third outcome. They propagate as exceptions.

---

## 8. Deny Reasons

```python
class AuthorizationDenyReason(StrEnum):
    UNAUTHENTICATED = "unauthenticated"
    INACTIVE_PRINCIPAL = "inactive_principal"
    MISSING_PERMISSION = "missing_permission"
    CONSTRAINT_FAILED = "constraint_failed"
```

These reasons describe ordinary denial only.

The following are deliberately not denial reasons:

- unknown target;
- unknown operation;
- missing role;
- user not found;
- infrastructure failure;
- invalid/unsupported principal type;
- repository failure;
- constraint infrastructure failure.

Those conditions represent either ordinary absence of a matching permission or security infrastructure/configuration failure.

---

## 9. Authorization Decision

```python
@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    outcome: AuthorizationOutcome
    reason: AuthorizationDenyReason | None
```

### Invariants

```text
ALLOW → reason is None
DENY  → reason is not None
```

Infrastructure/configuration failures never produce an `AuthorizationDecision`.

---

## 10. Security Authorization State

The authorization service must depend on a semantic security-state boundary rather than storage-specific repositories.

```python
class SecurityAuthorizationState(Protocol):
    def user_for_principal(self, principal: Principal) -> User: ...

    def role(self, identity: Identifier) -> Role: ...
```

This is an authoritative state boundary, not a new generic persistence framework.

The service asks it for the security state required to evaluate a request. Standard may implement this protocol by adapting existing `UserRepository` and `RoleRepository` implementations.

The Platform evaluator must not know whether the state is backed by memory, persistence, a database, or another storage mechanism.

---

## 11. Principal Resolution

The evaluator begins from `request.context.principal`.

If the principal is absent:

```text
DENY / UNAUTHENTICATED
```

No repository lookup is required for this case.

If the principal exists but its principal type is unsupported by the MVP evaluator, authorization fails closed with a security configuration/infrastructure error.

The MVP supports:

```text
PrincipalType.USER
```

`SERVICE` and `EXTERNAL` remain valid domain principal types but are not authorized by the Slice 3 evaluator.

The evaluator must not silently reinterpret a non-user principal as a user.

---

## 12. User Activity

For a supported user principal, the evaluator resolves the authoritative user state through `SecurityAuthorizationState.user_for_principal()`.

If the user is inactive:

```text
DENY / INACTIVE_PRINCIPAL
```

Inactive users do not proceed to permission evaluation.

Failure to resolve the authoritative user is a security infrastructure/configuration failure, not an ordinary denial.

---

## 13. Role Resolution

The user's assigned role identities are resolved through `SecurityAuthorizationState.role()`.

Every assigned role must resolve before the evaluator may return `ALLOW`.

For example:

```text
User roles = [RoleA, MissingRoleB]
RoleA grants requested permission
RoleB cannot be resolved
```

The result is a security infrastructure/configuration failure, not `ALLOW`.

This rule prevents incomplete security state from being interpreted as a successful authorization decision.

---

## 14. Permission Collection

The evaluator obtains permissions from all resolved roles.

Roles are additive:

```text
Effective permissions = union(all permissions granted by all assigned roles)
```

There is no role hierarchy.

There is no implicit permission inheritance.

Duplicate permissions are harmless and do not alter the result.

---

## 15. Permission Matching

A permission matches the request exactly when both conditions hold:

```python
permission.target == request.target
and permission.operation == request.operation
```

The evaluator must not introduce wildcard matching.

Unknown target or operation therefore results in no matching permission and consequently:

```text
DENY / MISSING_PERMISSION
```

unless another exact matching permission is available.

---

## 16. Permission Combination

Matching permissions use OR semantics.

Conceptually:

```text
permission_1 matches and grants
OR
permission_2 matches and grants
OR
...
```

If at least one matching permission passes all of its constraints, authorization is allowed.

A matching permission whose constraints fail does not veto another matching permission that grants access.

Example:

```text
Role A → matching permission, constraint=False
Role B → matching permission, no constraints

Result → ALLOW
```

---

## 17. Constraint Combination

Constraints within one permission use AND semantics.

For a matching permission:

```text
all constraints evaluate True
    → permission grants
```

If any constraint evaluates `False`:

```text
permission does not grant
```

An empty constraint collection means the permission grants without additional checks.

---

## 18. Constraint Contract

```python
class AuthorizationConstraint(Protocol):
    @property
    def code(self) -> str: ...

    def evaluate(self, request: AuthorizationRequest) -> bool: ...
```

The constraint receives the complete authorization request, allowing it to inspect:

- security context;
- principal;
- principal claims;
- target;
- operation;
- optional resource.

The contract must not use `object` as a generic escape hatch.

---

## 19. Constraint Result Semantics

`True` means the constraint is satisfied.

`False` means the constraint is not satisfied.

A false result is ordinary authorization data and therefore does not represent infrastructure failure.

If a matching permission has one or more failed constraints and no other matching permission grants access, the final decision is:

```text
DENY / CONSTRAINT_FAILED
```

---

## 20. Constraint Infrastructure Failure

Constraint evaluation must distinguish ordinary `False` from infrastructure/security-state failure.

The evaluator must not do either of the following:

```python
except Exception:
    return False
```

or:

```python
except Exception:
    return True
```

Security-state and infrastructure exceptions propagate unchanged according to the existing security error hierarchy.

This preserves fail-closed semantics without hiding operational failures.

---

## 21. Authorization Service

The public service contract is:

```python
class AuthorizationService(Protocol):
    def authorize(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision: ...

    def require(
        self,
        request: AuthorizationRequest,
    ) -> None: ...
```

Both methods are public API.

`authorize()` is the decision-oriented primitive.

`require()` is the imperative enforcement primitive intended for call sites where execution must stop on denial.

---

## 22. AuthorizationDeniedError

`AuthorizationDeniedError` belongs to the existing security error hierarchy.

Its purpose is limited to ordinary imperative denial from `require()`.

It retains the `AuthorizationDecision` that caused the denial so callers can inspect the precise ordinary denial reason.

Conceptually:

```python
try:
    authorization.require(request)
except AuthorizationDeniedError as error:
    decision = error.decision
```

Infrastructure/configuration failures are not wrapped in `AuthorizationDeniedError`.

---

## 23. DefaultAuthorizationService

The default Platform implementation is:

```python
@dataclass(frozen=True, slots=True)
class DefaultAuthorizationService:
    state: SecurityAuthorizationState
```

The service is stateless apart from its reference to the authoritative security-state provider.

It must not contain:

- authorization caches;
- mutable decision state;
- global/current principal state;
- request history;
- role snapshots retained across calls.

---

## 24. Default Algorithm

The canonical algorithm is:

```text
1. Read principal from request.context.
2. If principal is absent:
       return DENY / UNAUTHENTICATED.
3. Verify that the principal type is supported.
   Unsupported type → security configuration/infrastructure failure.
4. Resolve the authoritative user.
   Resolution failure → security infrastructure/configuration failure.
5. If user is inactive:
       return DENY / INACTIVE_PRINCIPAL.
6. Resolve every assigned role.
   Any missing/unavailable role → security infrastructure/configuration failure.
7. Collect permissions from all resolved roles.
8. Select permissions whose target and operation exactly match the request.
9. If there are no matching permissions:
       return DENY / MISSING_PERMISSION.
10. Evaluate each matching permission:
       all constraints True → that permission grants.
11. If any matching permission grants:
       return ALLOW / None.
12. Otherwise:
       return DENY / CONSTRAINT_FAILED.
```

The evaluator must resolve all assigned roles before returning `ALLOW`.

---

## 25. No Partial Evaluation

The evaluator must not return `ALLOW` after finding one granting role while another assigned role cannot be resolved.

All assigned roles form part of the authoritative security state relevant to the request.

Therefore:

```text
valid granting role + missing assigned role
    → security infrastructure/configuration failure
```

This is an explicit fail-closed invariant.

---

## 26. Repeated Evaluation

Each call to `authorize()` evaluates the current authoritative state.

No effective-permission cache is permitted.

Therefore, if role state changes between two calls, the second call observes the changed state.

Example:

```text
call 1 → role grants → ALLOW
role state changes
call 2 → role no longer grants → DENY
```

No cache invalidation mechanism is required because no authorization cache exists.

---

## 27. Resource Semantics

The optional `resource` is contextual input only.

It does not participate in base permission matching.

This means that two requests with identical context, target, and operation but different resource objects have the same base permission result unless an explicit constraint examines the resource.

Slice 3 does not define:

- ownership rules;
- tenant isolation rules;
- row-level authorization;
- object-specific permission inheritance;
- data filtering.

Such semantics may be introduced later through explicit constraints or later architectural work.

---

## 28. Claims Semantics

Claims are already part of `Principal`.

The request therefore does not duplicate them:

```python
request.context.principal.claims
```

Claims are otherwise inert.

The authorization engine does not automatically interpret a claim as a permission or denial.

A constraint may explicitly inspect claims and use them in its own evaluation.

Example conceptual behavior:

```text
claim present + explicit constraint satisfied
    → permission may grant
```

Without such a constraint, the claim has no effect on authorization.

---

## 29. Error Boundary

The boundary between ordinary denial and infrastructure/configuration failure is explicit.

### Ordinary denial

These are represented as `AuthorizationDecision`:

- unauthenticated principal;
- inactive principal;
- no matching permission;
- all matching permissions fail their constraints.

### Infrastructure/configuration failure

These propagate as exceptions:

- unsupported principal type;
- inability to resolve the authoritative user;
- missing/unavailable assigned role;
- security repository/state failure;
- constraint infrastructure/security-state failure;
- other existing security configuration failures.

The evaluator must never turn an infrastructure failure into `ALLOW`.

It also must not silently turn a security-state failure into an ordinary `DENY` where the failure means the evaluator cannot establish the authoritative security state.

---

## 30. Existing Security Error Hierarchy

Slice 3 reuses the existing security error hierarchy.

No parallel generic `AuthorizationError` hierarchy is introduced.

The main new authorization-specific imperative error is:

```text
AuthorizationDeniedError
```

It represents only an ordinary denied decision raised by `require()`.

Existing security infrastructure/configuration errors remain distinct and retain their existing semantics.

---

## 31. Standard State Adapter

Standard may retain its existing user and role repository implementations.

An adapter implements:

```python
SecurityAuthorizationState
```

and translates repository operations into the semantic state contract required by Platform authorization.

The adapter is responsible for mapping storage/domain state into the authorization boundary. The Platform evaluator remains unaware of repository implementation details.

---

## 32. Standard Composition

Standard exposes authorization through a composition object:

```python
@dataclass(frozen=True, slots=True)
class StandardSecurityComposition:
    authorization: AuthorizationService
```

Composition creates the Platform evaluator using the Standard state adapter.

Conceptually:

```text
Standard repositories
        ↓
SecurityAuthorizationState adapter
        ↓
DefaultAuthorizationService
        ↓
StandardSecurityComposition.authorization
```

Standard must not implement a second evaluator.

---

## 33. Standard Permission Definitions

Standard may define application/domain-specific permissions using the generic Platform permission model.

A Standard permission consists of the existing security concepts:

```text
Permission(target, operation, constraints)
```

Standard configuration may provide predefined permissions and roles, but it must not alter the Platform matching algorithm.

---

## 34. Standard Roles

Standard roles are additive collections of permissions.

Role hierarchy is not introduced.

A role does not inherit another role unless a later architecture explicitly introduces such a concept.

Multiple assigned roles contribute permissions through union semantics.

---

## 35. Persistence Boundary

Authorization does not introduce a new persistence subsystem.

The evaluator depends only on `SecurityAuthorizationState`.

Any persistence required for users, roles, or permissions remains behind the existing security state/repository architecture.

The semantic rule is:

```text
authorization algorithm → SecurityAuthorizationState
SecurityAuthorizationState → repository/storage implementation
```

not:

```text
authorization algorithm → concrete repository
```

---

## 36. Caching

No caching is permitted in Slice 3.

Specifically prohibited:

- effective permission cache;
- role-resolution cache;
- decision cache;
- principal authorization cache;
- global memoization of authorization results.

This makes repeated authorization calls observe the current authoritative security state.

---

## 37. Thread Safety / Immutability

The value objects are immutable.

`AuthorizationRequest` and `AuthorizationDecision` are frozen dataclasses with slots.

`DefaultAuthorizationService` is also frozen and contains no mutable authorization state.

Thread safety therefore depends only on the underlying `SecurityAuthorizationState` implementation and existing repository guarantees; the authorization evaluator itself introduces no shared mutable state.

---

## 38. Public Platform Exports

The Platform security package publicly exports the following Slice 3 symbols:

```text
AuthorizationConstraint
AuthorizationDecision
AuthorizationDenyReason
AuthorizationOutcome
AuthorizationRequest
AuthorizationResource
AuthorizationService
DefaultAuthorizationService
SecurityAuthorizationState
```

Existing Slice 1 and Slice 2 public security exports remain available.

Internal helper functions/classes are not public API.

---

## 39. Public Standard Exports

Standard publicly exposes the composition required by its existing security integration conventions, including:

```text
StandardSecurityComposition
```

Concrete state adapters and internal evaluator helpers remain implementation details unless already part of an established public Standard API.

---

## 40. Test Matrix Decision

The test suite must directly encode the architectural invariants.

Required unit coverage includes:

### Principal state

- unauthenticated request → `UNAUTHENTICATED`;
- inactive principal → `INACTIVE_PRINCIPAL`;
- unsupported principal type fails closed.

### Permission matching

- exact target + operation → `ALLOW`;
- different target → `MISSING_PERMISSION`;
- different operation → `MISSING_PERMISSION`;
- unknown target → `MISSING_PERMISSION`;
- unknown operation → `MISSING_PERMISSION`.

### Role aggregation

- permission from one role grants;
- permissions from multiple roles are unioned;
- duplicate permissions are harmless;
- changed role state is observed on repeated evaluation.

### Role integrity

- missing assigned role fails closed;
- valid granting role + missing role still fails closed;
- all assigned roles are resolved before `ALLOW`.

### Constraints

- no constraints → `ALLOW`;
- all constraints true → `ALLOW`;
- one false constraint → permission does not grant;
- all matching permissions fail → `CONSTRAINT_FAILED`;
- one failed matching permission + one granting matching permission → `ALLOW`;
- `False` is not treated as infrastructure failure;
- infrastructure exception from constraint propagates.

### Resource and claims

- resource does not affect base permission matching;
- explicit constraint may inspect resource;
- claims do not automatically grant/deny;
- explicit constraint may inspect claims.

### Failure behavior

- user/state infrastructure failure propagates;
- role/state infrastructure failure propagates;
- unsupported principal type fails closed;
- authorization never converts infrastructure failure to `ALLOW`.

### Enforcement

- `authorize(ALLOW)` returns a decision;
- `authorize(DENY)` returns a decision;
- `require(ALLOW)` returns `None`;
- `require(DENY)` raises `AuthorizationDeniedError` containing the decision;
- infrastructure failures from `require()` propagate unchanged.

---

## 41. Role Aggregation

Role aggregation is a pure union.

Given roles:

```text
R1 → {P1, P2}
R2 → {P2, P3}
```

the effective permission set is conceptually:

```text
{P1, P2, P3}
```

There is no priority ordering between roles.

There is no deny permission that can override another role.

There is no role hierarchy.

---

## 42. Permission / Constraint Semantics

The complete logical structure is:

```text
ALLOW if
    principal exists
    AND principal is supported
    AND user is active
    AND every assigned role resolves
    AND there exists a permission such that
        permission.target == request.target
        AND permission.operation == request.operation
        AND every permission constraint evaluates True
```

If the principal is absent, the result is ordinary unauthenticated denial.

If there is no matching permission, the result is missing-permission denial.

If matching permissions exist but none passes its constraints, the result is constraint-failed denial.

Security-state failures interrupt evaluation with an exception.

---

## 43. Resource / Claims

Resource and claims are deliberately secondary to the base permission model.

```text
Base authorization:
    target + operation

Optional contextual evaluation:
    explicit constraints
```

This keeps the core authorization model deterministic and reusable without introducing a generic policy language.

---

## 44. Principal Types

Slice 3 explicitly supports:

```text
USER
```

The domain may already define:

```text
USER
SERVICE
EXTERNAL
```

but Slice 3 does not infer user semantics for SERVICE or EXTERNAL principals.

Unsupported types fail closed as security configuration/infrastructure failures.

A future slice may define authorization semantics for additional principal types without changing the USER contract.

---

## 45. Infrastructure Failure

Security infrastructure failures are not authorization denials.

This distinction is essential for recovery, observability, and correctness.

Examples include:

```text
role assigned but cannot be resolved
user state cannot be loaded
security state provider unavailable
constraint cannot obtain required security state
unsupported principal type in current authorization configuration
```

These conditions propagate through the authorization service.

No such condition may produce `ALLOW`.

---

## 46. Enforcement

`require()` is the canonical imperative enforcement primitive.

Its contract is:

```text
ALLOW → return None
DENY  → raise AuthorizationDeniedError(decision)
ERROR → propagate original security/infrastructure error
```

This gives callers a single direct operation when execution must not continue after denial.

`authorize()` remains available for callers that need to inspect the decision without immediately raising.

---

## 47. Architectural Tests

The test suite must also enforce architecture, not only behavior.

Required architectural checks include:

- Platform authorization does not import Standard implementation modules.
- Platform authorization does not depend directly on concrete repositories.
- Standard uses `DefaultAuthorizationService` rather than a second evaluator.
- ProcessingRuntime is unchanged by Slice 3.
- No ambient/global current-principal mechanism is introduced.
- No authorization cache is introduced.
- No wildcard permission matching is introduced.
- No role hierarchy is introduced.
- No generic policy DSL is introduced.
- No business-specific data-scope framework is introduced.
- Claims are not duplicated into `AuthorizationRequest`.

---

## 48. Explicitly Out of Scope

The following are not implemented in Slice 3:

- authentication;
- credential verification;
- session validation;
- token validation;
- ProcessingRuntime enforcement;
- request middleware;
- wildcard permissions;
- deny permissions;
- role hierarchy;
- policy DSL;
- policy scripting language;
- ownership/tenancy framework;
- row-level/data filtering;
- automatic claim-to-permission mapping;
- authorization caching;
- distributed authorization decisions;
- SERVICE principal authorization;
- EXTERNAL principal authorization.

These boundaries prevent Slice 3 from becoming a general policy platform.

---

## 49. Implementation Decomposition

Implementation proceeds in the following controlled slices.

### Slice 3.1 — Value Objects

Implement:

- `AuthorizationRequest`;
- `AuthorizationOutcome`;
- `AuthorizationDenyReason`;
- `AuthorizationDecision`;
- `AuthorizationResource`.

### Slice 3.2 — Contracts and Errors

Implement:

- `AuthorizationConstraint`;
- `SecurityAuthorizationState`;
- `AuthorizationService`;
- `AuthorizationDeniedError` integration with the existing hierarchy.

### Slice 3.3 — Default Evaluator

Implement:

- `DefaultAuthorizationService`;
- exact permission matching;
- role aggregation;
- constraint evaluation;
- fail-closed state resolution;
- `authorize()`;
- `require()`.

### Slice 3.4 — Standard Composition

Implement:

- Standard state adapter;
- `StandardSecurityComposition`;
- Standard exports/configuration;
- Standard permission/role definitions where required by existing composition conventions.

### Slice 3.5 — Tests and Exports

Implement:

- complete unit matrix;
- architectural tests;
- public exports;
- regression coverage;
- final documentation reconciliation.

No ProcessingRuntime modification is included.

---

## 50. Quality Gate

The final implementation must pass:

```bash
pytest -q tests/unit/security/
pytest -q
ruff check .
black --check .
mypy src
git diff --check
git status
```

Any failure must be resolved before the slice is considered complete.

---

## 51. Acceptance Criteria

Slice 3 is complete when all of the following hold:

1. The Platform authorization API matches this document.
2. Authorization consumes `SecurityContext` rather than performing authentication.
3. Exact target + operation matching is implemented.
4. Roles are additive.
5. Constraints are AND within a permission.
6. Matching permissions are OR.
7. No match means denial.
8. Unauthenticated principals are denied ordinarily.
9. Inactive users are denied ordinarily.
10. Missing assigned roles fail closed as security state failure.
11. All assigned roles resolve before `ALLOW`.
12. Unsupported principal types fail closed.
13. Infrastructure failures never become `ALLOW`.
14. Resource is contextual only.
15. Claims remain on the principal and have no implicit authorization effect.
16. No caching is introduced.
17. `require()` provides imperative enforcement.
18. Standard composes the Platform evaluator rather than duplicating it.
19. ProcessingRuntime remains unchanged.
20. The complete test matrix passes.
21. Full repository quality gates pass.
22. Public exports are limited to the approved API.

---

## 52. Architectural Invariants

The implementation must preserve these invariants:

### Invariant A — Fail closed

No incomplete, unsupported, or failed security state can result in `ALLOW`.

### Invariant B — Complete role resolution

An authorization decision cannot become `ALLOW` until every assigned role has been resolved.

### Invariant C — Exact permission semantics

Permission matching is exactly target + operation.

### Invariant D — Additive roles

Roles only add permissions; there are no deny permissions or hierarchy semantics.

### Invariant E — Constraint semantics

Constraints within one permission are ANDed; matching permissions are ORed.

### Invariant F — Explicit context

Authorization receives an explicit `SecurityContext`; no ambient principal exists.

### Invariant G — No cache

Each authorization call evaluates current authoritative state.

### Invariant H — Separation of concerns

Platform owns the evaluator; Standard supplies configuration and state adapters; Processing enforcement is later work.

### Invariant I — Error distinction

Ordinary denial is distinct from security infrastructure/configuration failure.

### Invariant J — No hidden policy language

Slice 3 remains an explicit contract-based authorization engine, not a generic policy DSL.

---

## 53. Final API Summary

```python
class AuthorizationResource(Protocol):
    @property
    def identity(self) -> Identifier: ...


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    context: SecurityContext
    target: SecurityObjectIdentity
    operation: SecurityOperation
    resource: AuthorizationResource | None = None


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


class SecurityAuthorizationState(Protocol):
    def user_for_principal(self, principal: Principal) -> User: ...
    def role(self, identity: Identifier) -> Role: ...


class AuthorizationConstraint(Protocol):
    @property
    def code(self) -> str: ...

    def evaluate(self, request: AuthorizationRequest) -> bool: ...


class AuthorizationService(Protocol):
    def authorize(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision: ...

    def require(
        self,
        request: AuthorizationRequest,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class DefaultAuthorizationService:
    state: SecurityAuthorizationState
```

Standard composition:

```python
@dataclass(frozen=True, slots=True)
class StandardSecurityComposition:
    authorization: AuthorizationService
```

---

## 54. Final Status

**Approved for Implementation.**

This document is the final Concrete API Design for Phase 11 Slice 3 — Authorization. Implementation may proceed directly from this contract.

The next architectural boundary is Slice 4, where authorization enforcement is integrated into Processing. Slice 3 itself must remain independent of `ProcessingRuntime`.

**Suggested implementation commit:**

```text
feat(security): implement Phase 11 Slice 3 authorization
```
