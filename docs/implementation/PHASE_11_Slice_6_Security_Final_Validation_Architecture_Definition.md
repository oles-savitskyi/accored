# PHASE 11 — Slice 6 — Security Final Validation
## Architecture Definition / Scope

**Status:** FINAL — AMENDED — APPROVED FOR CONCRETE API DESIGN / IMPLEMENTATION

**Phase:** Phase 11 — Security  
**Slice:** Slice 6 — Security Tests / Final Validation

---

## 1. Purpose

Slice 6 is the final validation slice of Phase 11 Security MVP. Its purpose is to prove, through a coherent test boundary, that the security architecture implemented in Slices 1–5 is internally consistent, correctly composed, and correctly enforced at the existing Processing runtime boundary.

Slice 6 is primarily a **validation slice**, not a new security-feature slice. It must not introduce new authorization semantics, new authentication mechanisms, new security objects, new role-assignment mechanisms, or new runtime boundaries merely to increase test coverage.

The desired outcome is confidence that the Phase 11 Security MVP is ready to be treated as a stable platform capability for subsequent phases.

---

## 2. Architectural Context

Phase 11 Security has established the following layers:

```text
Platform Security
    ├── security identities / value objects
    ├── authentication contracts
    ├── authorization contracts and evaluator
    ├── sessions / security context
    └── security errors
             ▲
             │ composed by
             │
Standard Security
    ├── users
    ├── roles
    ├── permissions
    ├── credentials
    ├── repositories / local state
    └── bootstrap composition
             │
             ▼
Processing Runtime
    ├── SecurityContext
    ├── authorization before processing resolution
    └── protected processing execution
```

Slice 6 validates this complete path without changing its architecture.

### 2.1 Slice 4 invariants remain normative

The following previously approved Processing security invariants remain mandatory:

- `ProcessingCommand` carries an explicit `SecurityContext`.
- The same security context is propagated into `ProcessingContext`.
- authorization occurs before Processing resolution/execution;
- the operation used for the protected Processing boundary is `SecurityOperation.EXECUTE`;
- Processing identity is mapped to `SecurityObjectIdentity(object_type="processing", object_code=processing.value)`;
- authorization denial raises `AuthorizationDeniedError`;
- denial produces no Processing side effects;
- authorization infrastructure failures remain infrastructure failures and are not converted into ordinary denials;
- the runtime has no dependency on a concrete security implementation beyond the approved Platform authorization boundary.

Slice 6 may verify these invariants but may not redefine them.

---

## 3. Scope

### 3.1 In scope

Slice 6 covers:

1. final Platform Security behavioral validation;
2. final Standard Security behavioral validation;
3. authentication success and failure paths;
4. authorization allow and deny semantics already defined by Phase 11;
5. role/permission resolution through `User.role_ids`;
6. credential separation and verification behavior;
7. SecurityContext construction and propagation;
8. Standard bootstrap composition;
9. protected Processing vertical validation;
10. denial side-effect guarantees;
11. infrastructure-error propagation at the security boundary;
12. isolation of security state between independently composed Standard security instances;
13. regression coverage for Phase 11 security contracts;
14. final full-project quality gate.

### 3.2 Out of scope

Slice 6 must not introduce:

- new authentication mechanisms;
- MFA;
- password reset workflows;
- password-change workflows;
- authorization policy languages;
- role inheritance;
- wildcard permissions;
- explicit deny permissions;
- data-scope authorization not already required by an existing MVP operation;
- security administration services or UI;
- audit persistence;
- distributed security state;
- database-backed security repositories;
- new report execution boundaries;
- new Processing APIs;
- new security concepts merely for testability;
- test-only production bypasses;
- implicit administrative privileges;
- global or thread-local security context;
- a second user-to-role assignment mechanism.

---

## 4. Architectural Principles

### 4.1 Tests validate architecture; they do not define a second architecture

Tests must consume the public Platform and Standard contracts exactly as production code does. Test helpers may simplify fixture construction, but must not bypass the security boundaries under test.

### 4.2 Existing semantics are authoritative

Slice 6 tests the semantics established by Slices 1–5. If a test appears to require a new security rule, the default conclusion must be that the test requirement is outside Slice 6 rather than silently adding a new rule.

### 4.3 Explicit security state

Security state remains explicit and instance-owned. Tests must not depend on module-level mutable state, process-global registries, or test-order side effects.

### 4.4 Real vertical composition

At least one end-to-end security test must use the real Standard composition and the real Processing runtime authorization boundary. Mocking may be used for underlying business collaborators where necessary, but authorization itself must not be mocked in the principal vertical scenario.

### 4.5 Negative paths are first-class

Security validation must prove both successful and unsuccessful paths. In particular, denial must be demonstrated as a security decision rather than as an incidental downstream failure.

---

## 5. Validation Layers

Slice 6 validation is organized into four complementary layers.

### 5.1 Platform security validation

Validate the already defined Platform contracts and behavior:

- security identities and value objects;
- principal/session/context invariants;
- authentication results and errors;
- authorization request/decision behavior;
- permission matching;
- constraint behavior already defined by the Platform API;
- missing permission / denied semantics;
- infrastructure-error propagation.

No new Platform security behavior is introduced.

### 5.2 Standard security validation

Validate:

- immutable Standard security definitions;
- representative users and roles;
- `User.role_ids` as the authoritative user-to-role relationship;
- Standard credentials;
- password verification;
- local authentication composition;
- Standard authorization composition;
- context factory composition;
- independent composition instances;
- absence of implicit administrator behavior.

### 5.3 Processing vertical validation

The principal vertical scenario is:

```text
StandardConfigurationBootstrap
        │
        ▼
Standard Security Composition
        │
        ├── authenticate operator
        │
        └── create SecurityContext
                │
                ▼
DefaultProcessingRuntime.execute()
                │
                ▼
Platform AuthorizationService
                │
          ┌─────┴─────┐
        ALLOW        DENY
          │            │
          ▼            ▼
    real Processing  AuthorizationDeniedError
```

The vertical tests must demonstrate:

- authorized Standard operator can execute the protected Processing;
- unauthorized Standard auditor cannot execute it;
- the administrator can execute it according to the configured permission set;
- denial occurs before Processing execution;
- Processing collaborators receive no side effects after denial.

### 5.4 Full regression / quality validation

Slice 6 ends with the established project quality gate:

```text
pytest -q
ruff check .
black --check .
mypy src

git diff --check
```

Any project-specific quality command already established by the repository remains applicable.

---

## 6. Authentication Validation

Authentication tests must cover the already defined contract without expanding it.

Required cases:

1. valid credentials authenticate the expected user;
2. invalid password fails authentication;
3. unknown login fails authentication without revealing credential state;
4. successful authentication produces a `Principal` of `PrincipalType.USER`;
5. the principal identity corresponds to the authenticated `User.identity`;
6. a successful authentication result can be converted into a `SecurityContext` through the Standard context factory;
7. credentials are not stored in the resulting `Principal`, `Session`, or `SecurityContext`.

Authentication failure must remain distinguishable from authorization denial.

---

## 7. Authorization Validation

### 7.1 Permission semantics

Tests must confirm the already approved semantics:

- permissions are evaluated according to the Platform authorization service;
- matching permissions are sufficient to allow the requested operation;
- multiple permissions are not interpreted as an implicit deny-all model;
- constraints, where present, are evaluated according to their existing Platform contract;
- an absent required permission results in authorization denial;
- an unknown target is not silently treated as authorized.

### 7.2 Role-based authorization

The Standard role matrix is:

| Role | Processing `inventory.rebuild` | Report `inventory.balance` | Security administration |
|---|---|---|---|
| Administrator | EXECUTE | READ | ADMINISTER |
| Operator | EXECUTE | — | — |
| Auditor | — | READ | — |

The matrix is a Standard MVP composition definition, not a permanent security taxonomy.

Tests must derive user permissions through `User.role_ids` and the configured roles. They must not create a parallel user-permission mapping.

### 7.3 No hidden privilege

Tests must explicitly prove that a user without the required role/permission is denied, even when the user is a valid authenticated `PrincipalType.USER`.

Authentication success must never imply authorization success.

---

## 8. Security Context Validation

Slice 6 validates explicit SecurityContext propagation.

Required invariants:

- `ProcessingCommand.security_context` is present;
- the runtime passes the same `SecurityContext` instance into `ProcessingContext`;
- authorization evaluates the context associated with the command;
- no ambient or global context is consulted;
- a context belonging to one authenticated user cannot be silently replaced by another user's context.

Identity consistency must remain enforced by the existing Platform contracts.

---

## 9. Processing Authorization Ordering

The vertical test suite must prove the following order:

```text
command validation
      ↓
authorization
      ↓
processing resolution
      ↓
processing execution
```

For a denied request:

```text
command
  ↓
authorization DENY
  ↓
AuthorizationDeniedError
  ↓
STOP
```

The test must prove that denied execution does not invoke the underlying Processing implementation or its business collaborators.

---

## 10. Infrastructure Failure Validation

Security infrastructure failures must not be converted into ordinary authorization denials.

Where a test substitutes a failing authorization dependency, it must demonstrate that the original infrastructure/security exception propagates according to the existing Platform contract.

The test must not require a new exception type or new failure classification for Slice 6.

---

## 11. State Isolation Validation

Standard security composition must be independently instantiable.

At minimum, validation should prove:

1. two independently composed Standard security instances do not share mutable credential state;
2. modifying test-local state in one composition cannot authorize a principal in another composition;
3. bootstrap does not depend on a process-global security registry;
4. tests can run independently and in arbitrary order.

This validates the architectural decision that security configuration/state is explicit and instance-owned.

---

## 12. Standard Definitions and Configuration Validation

Tests should verify the stable semantic identities of the Standard security vocabulary:

- `processing / inventory.rebuild / EXECUTE`;
- `report / inventory.balance / READ`;
- `system / security / ADMINISTER`.

These are semantic security identities, not Python class names, display labels, or module names.

The tests must not import concrete Processing implementation classes merely to construct security definitions.

---

## 13. Test Fixture Boundary

Test fixtures may provide:

- deterministic user identities;
- deterministic role identities;
- deterministic credential values;
- test password inputs;
- mocked business collaborators;
- isolated in-memory repositories.

Fixtures must not provide:

- a fake authorization evaluator in place of the real Platform evaluator for the principal vertical scenario;
- implicit administrator privileges;
- a global authenticated user;
- direct mutation of internal authorization caches to force an allow decision;
- bypass flags;
- test-only production APIs.

Production code must not expose APIs solely to make Slice 6 tests easier.

---

## 14. Regression Expectations

Slice 6 is complete only when the security additions remain compatible with the rest of AcCoreD.

The full project test suite must continue to pass. Security tests must not rely on ordering relative to unrelated tests.

Any regression caused by the security implementation must be treated as an implementation defect unless it reveals a genuine architectural conflict requiring explicit review.

---

## 15. Architectural Invariants

The following invariants are normative for Slice 6:

**A.** Slice 6 introduces no new security semantics.

**B.** Platform remains the semantic owner of authentication, authorization, principal, session, and security-context behavior.

**C.** Standard remains the owner of Standard users, roles, permissions, credentials, local state, and composition.

**D.** `User.role_ids` remains the sole authoritative user-to-role assignment source.

**E.** Security credentials remain separate from users, principals, sessions, and contexts.

**F.** `PasswordVerifier` remains an opaque Platform boundary; Standard owns its concrete password hashing implementation.

**G.** SecurityContext remains explicit and is not ambient/global/thread-local state.

**H.** Authentication success does not imply authorization success.

**I.** Authorization occurs before protected Processing execution.

**J.** Authorization denial is side-effect free with respect to Processing execution.

**K.** Infrastructure/security failures are not converted into ordinary authorization denials.

**L.** Standard role and permission tests use the real Platform authorization semantics.

**M.** The principal vertical test uses real Standard security composition and the real Processing runtime authorization boundary.

**N.** Tests must not introduce a second authorization or role-assignment implementation.

**O.** Tests must not create a new report runtime or security administration framework.

**P.** Independent security compositions remain isolated from one another.

**Q.** The full project quality gate remains green.

---

## 16. Acceptance Criteria

Slice 6 is accepted when all of the following are true:

1. Platform Security regression tests pass.
2. Standard Security tests pass.
3. Authentication success and failure paths are covered.
4. Role-based authorization behavior is covered.
5. `User.role_ids` is validated as the sole user-to-role assignment source.
6. Standard credentials remain separate from user/principal/session/context objects.
7. SecurityContext construction and propagation are validated.
8. Authorized Processing execution is validated through real Standard composition.
9. Unauthorized Processing execution is denied through the real authorization service.
10. Denied Processing produces no underlying Processing side effects.
11. Authentication success is not treated as authorization success.
12. Security infrastructure failure propagation is validated.
13. Independent security composition instances are isolated.
14. No test requires a new production security API or bypass.
15. No new security semantics are introduced by Slice 6.
16. Full project tests pass.
17. Ruff passes.
18. Black check passes.
19. Mypy passes.
20. `git diff --check` passes.

---

## 17. Implementation Boundary

Concrete API / implementation work for Slice 6 may:

- add or refine tests;
- add test-only helper functions or fixtures;
- add regression cases against existing public APIs;
- add narrowly scoped assertions required to prove existing invariants;
- adjust production code only if a test exposes a genuine implementation defect already within the approved Slice 1–5 architecture.

It may not:

- add new security concepts;
- change Platform contracts;
- change the Standard role model;
- introduce a second role-assignment source;
- add implicit privileges;
- add ambient security state;
- create a report runtime solely for testing;
- create a security administration service solely for testing;
- weaken production validation to make tests pass;
- add test-only production bypasses.

If a proposed implementation change cannot be justified as a correction of an existing Slice 1–5 invariant, it is outside Slice 6 and requires a separate architectural decision.

---

## 18. Architecture Review

### Review basis

This Architecture Definition was reviewed against:

- the approved Phase 11 Security architecture;
- the final Slice 5 Architecture Definition;
- the final Slice 5 Concrete API Design;
- the implemented Slice 4 Processing authorization boundary;
- the completed Slice 5 Standard composition;
- the established Phase 11 security invariants.

### Findings

**Finding 1 — Slice purpose is correctly constrained.**  
Slice 6 is explicitly validation-only and does not create a new security feature boundary.

**Finding 2 — Platform/Standard ownership is preserved.**  
The document does not move authorization semantics into Standard or test infrastructure.

**Finding 3 — Slice 4 Processing contract is preserved.**  
The document explicitly retains `ProcessingCommand.security_context`, explicit context propagation, authorization ordering, `EXECUTE`, and side-effect-free denial.

**Finding 4 — Standard role assignment is preserved.**  
`User.role_ids` remains authoritative and no parallel role-assignment abstraction is introduced.

**Finding 5 — Security state isolation is explicitly validated.**  
This is an appropriate final validation concern and does not require a new runtime architecture.

**Finding 6 — Vertical validation is sufficiently strong.**  
The principal integration scenario uses real Standard composition and the real Processing authorization boundary rather than mocking away the feature being tested.

**Finding 7 — Test fixtures are appropriately constrained.**  
Fixtures may isolate collaborators but may not bypass authentication/authorization semantics.

**Finding 8 — No artificial report/security-administration boundary is introduced.**  
Existing vocabulary is validated without inventing runtime services that are outside the MVP.

**Finding 9 — Failure semantics remain stable.**  
Authentication failure, authorization denial, and infrastructure failure remain distinct categories.

**Finding 10 — Quality gate is correctly treated as the final acceptance boundary.**  
The full project regression suite is required rather than only security-local tests.

### Review verdict

**APPROVED FOR CONCRETE API DESIGN / IMPLEMENTATION**

No architectural amendments are required before proceeding to Slice 6 Concrete API Design.

---

## 19. Slice 6 Outcome

At completion, Phase 11 Security MVP will have:

- Platform security semantics;
- authentication boundary;
- authorization boundary;
- Standard users, roles, permissions, and credentials;
- Standard security composition;
- protected Processing execution;
- comprehensive regression and vertical validation;
- a clean project-wide quality gate.

Slice 6 therefore closes the implementation/validation cycle of Phase 11 Security without expanding the MVP beyond its approved architectural scope.
