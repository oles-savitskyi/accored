# PHASE 11 — Slice 6 — Security Final Validation
## Concrete API Design

**Status:** FINAL — REVIEWED — APPROVED FOR IMPLEMENTATION
**Phase:** 11 — Security
**Slice:** 6 — Security Final Validation

---

## 1. Purpose

Slice 6 is the final validation slice for Phase 11 Security MVP. It adds and consolidates tests proving that the security contracts implemented in Slices 1–5 behave correctly as a coherent system.

Slice 6 does **not** introduce new production security semantics, authorization rules, authentication mechanisms, security state models, processing contracts, or report runtime boundaries.

The primary deliverable is executable validation of the already approved architecture.

---

## 2. Normative Baseline

This document depends on and does not supersede:

1. Phase 11 Security Architecture Definition;
2. Phase 11 Security Concrete API Design;
3. Slice 1–5 approved Architecture Definitions and implementations;
4. Slice 6 Architecture Definition / Scope.

The implemented Slice 4 contract that `ProcessingCommand` carries an explicit `SecurityContext` remains authoritative. Any older design text claiming otherwise is superseded.

---

## 3. Production API Boundary

Slice 6 adds no new public production security API.

Existing production contracts remain authoritative:

- authentication contracts;
- authorization contracts;
- security context/session contracts;
- Standard security definitions;
- Standard security composition;
- Processing runtime security boundary.

Any helper introduced solely for tests must remain test infrastructure unless it is already part of the approved production API.

---

## 4. Test Fixture Boundary

Tests may provide small deterministic factories/builders to avoid repeating setup. They must compose the real production objects rather than replace their semantics.

Recommended test-level concepts:

```python
make_standard_security(...)
make_processing_runtime(...)
make_runtime_configuration(...)
```

These are test helpers, not production services.

A test fixture may allow explicit credentials, users, roles, and processing implementations to be supplied. It must not create implicit administrators or hidden authorization bypasses.

---

## 5. Authentication Validation

The test suite must validate at least:

- valid credentials authenticate the expected Standard user;
- invalid password is rejected;
- unknown login is rejected;
- authenticated principal has `PrincipalType.USER`;
- principal identity corresponds to the authenticated `User.identity`;
- session/context construction succeeds only from successful authentication;
- authentication failures remain authentication failures and are not represented as authorization denials.

No password values are embedded into production security objects.

---

## 6. Authorization Validation

The suite must validate the already implemented authorization semantics:

- a matching permission authorizes the requested operation;
- a missing permission produces `AuthorizationDeniedError` / the established denial semantics;
- matching permissions are sufficient without requiring unrelated permissions;
- constraints retain the established AND-within-constraint semantics;
- independent permissions retain the established OR semantics;
- unknown target/permission state follows the approved `MISSING_PERMISSION` semantics;
- infrastructure failures are not converted into authorization denial.

Slice 6 must not add role inheritance, wildcard permissions, explicit deny policies, or new constraint types.

---

## 7. Role and Standard Composition Validation

The Standard composition tests must prove:

- Administrator receives all three approved Standard permissions;
- Operator receives `processing / inventory.rebuild / EXECUTE`;
- Auditor receives `report / inventory.balance / READ`;
- `User.role_ids` is the authoritative role assignment;
- no second role-assignment mechanism exists;
- all referenced roles exist in the composed role set;
- separate calls to Standard security composition produce independent state;
- mutation of one composition's test-side state cannot silently alter another composition.

The tests must not treat the representative Standard users as permanent product taxonomy.

---

## 8. Credential Validation

The Standard credential implementation must be validated for the established boundary:

- credentials are separate from `User`;
- the verifier is supplied through the Platform `PasswordVerifier` contract;
- correct password verifies successfully;
- incorrect password fails verification;
- generated password material is salted/non-deterministically encoded as required by the Standard hasher;
- plaintext passwords are not stored in `StandardCredential`.

Tests may inspect the concrete Standard verifier where necessary to validate its own contract, but must not make Platform depend on the concrete Standard hashing implementation.

---

## 9. Security Context Validation

The suite must prove that:

- a successful authentication can produce a valid `SecurityContext`;
- the context represents the authenticated user/session;
- the same context instance is propagated through the Processing command/runtime boundary where the approved Slice 4 contract requires identity propagation;
- no thread-local, process-global, or implicit context is required.

A test must not manufacture an authorization result independently of the actual `SecurityContext` path when validating the vertical flow.

---

## 10. Vertical Processing Validation

At least one integration test must exercise the complete real path:

```text
StandardConfigurationBootstrap
        ↓
Standard security composition
        ↓
AuthenticationProvider
        ↓
SecurityContextFactory
        ↓
ProcessingCommand.security_context
        ↓
DefaultProcessingRuntime
        ↓
AuthorizationService
        ↓
Standard Processing
```

### Allow scenario

An Operator authenticates successfully and executes `inventory.rebuild`.

The real Processing implementation is invoked and its expected effects occur.

### Deny scenario

An Auditor authenticates successfully and attempts `inventory.rebuild`.

Authorization is denied before Processing resolution/execution.

The test must prove that the Processing side-effect collaborators are not called.

---

## 11. Authorization Ordering Validation

The integration suite should prove the established Slice 4 ordering:

```text
validate security context
        ↓
authorize EXECUTE
        ↓
resolve processing
        ↓
execute processing
```

A denied command must not resolve or execute the protected Processing operation.

The test should use observable collaborators or an equivalent deterministic mechanism; it must not rely only on the exception type.

---

## 12. Failure Taxonomy Validation

Tests must preserve the distinction between:

1. authentication failure;
2. authorization denial;
3. infrastructure failure.

In particular, a repository/provider/runtime infrastructure exception must not be silently transformed into `AuthorizationDeniedError`.

This is validation of existing behavior, not a new error-handling API.

---

## 13. Composition Isolation

A dedicated test should create two independent Standard security compositions.

The test must establish that:

- users/roles/credentials are not shared through mutable global state;
- authenticating a user in one composition does not modify the other;
- changing test-local repository state in one composition does not authorize a principal in the other;
- context/session state is composition-local.

This validates the architectural prohibition on mutable global security state.

---

## 14. Test Organization

Recommended organization:

```text
tests/unit/security/
    test_authentication.py
    test_authorization.py
    test_context.py
    test_definitions.py
    test_composition.py
    ...

tests/integration/
    test_processing_runtime.py
```

Existing tests should be extended where the behavior already belongs to an existing test module. New test modules should be introduced only when they improve a clear boundary.

No production module should be created merely to make a test easier to write.

---

## 15. Test Helpers

Test helpers should prefer explicit inputs and deterministic behavior.

Example conceptual fixture:

```python
def make_standard_security(
    *,
    initial_passwords: Mapping[str, str] | None = None,
) -> StandardSecurityComposition:
    ...
```

If such a helper is introduced, it must call the real `compose_standard_security()` path.

It must not:

- bypass authentication;
- construct privileged contexts directly for ordinary vertical tests;
- replace `AuthorizationService` with a permissive mock when testing authorization behavior;
- create hidden default credentials.

---

## 16. What Must Not Be Added

Slice 6 must not introduce:

- new security production services;
- role inheritance;
- wildcard permissions;
- deny rules;
- policy engines;
- security administration CRUD;
- audit persistence;
- database-backed security repositories;
- report execution runtime solely for testing `READ` permission vocabulary;
- new Processing security boundaries;
- alternate role assignment repositories;
- ambient security context;
- test-only production bypasses.

---

## 17. Quality Gate

Before Slice 6 completion, run:

```bash
pytest -q tests/unit/security/
pytest -q tests/integration/
pytest -q
ruff check .
black --check .
mypy src
git diff --check
```

The full suite must pass, not only the newly added security tests.

The implementation must leave the working tree reviewable and free from accidental generated artifacts.

---

## 18. Acceptance Criteria

Slice 6 is complete when:

1. all existing Phase 11 security tests remain green;
2. authentication success/failure semantics are covered;
3. authorization allow/deny semantics are covered;
4. role-based Standard composition is covered;
5. credential isolation is covered;
6. SecurityContext construction/propagation is covered;
7. the real Standard → Platform → Processing vertical allow path is covered;
8. the real vertical deny path is covered;
9. deny is proven side-effect-free;
10. authorization ordering is observable;
11. authentication, authorization, and infrastructure failures remain distinct;
12. independent Standard security compositions are isolated;
13. no new production security semantics are introduced;
14. no new public production API is introduced unless explicitly required by an already approved contract;
15. full quality gate passes;
16. implementation review confirms conformance with the Phase 11 architecture.

---

# Architecture Review

## Review Scope

The proposed Concrete API Design was reviewed against the final Slice 6 Architecture Definition and the approved Phase 11/Slices 1–5 contracts.

## Findings

### Finding 1 — Production API expansion

**Status: PASS.**

The design explicitly prohibits new production security semantics and treats fixtures as test infrastructure.

### Finding 2 — Slice 4 compatibility

**Status: PASS.**

The design explicitly preserves `ProcessingCommand.security_context` and the established authorization-before-processing ordering.

### Finding 3 — Standard/Platform ownership

**Status: PASS.**

Tests exercise the real Platform authorization service and Standard composition. No Standard authorization evaluator is introduced.

### Finding 4 — Role assignment

**Status: PASS.**

Validation explicitly treats `User.role_ids` as the sole authoritative user-to-role assignment mechanism.

### Finding 5 — Security state isolation

**Status: PASS.**

Composition-isolation tests are explicitly required, matching the prohibition on mutable global security state.

### Finding 6 — Vertical validation

**Status: PASS.**

The design requires a real end-to-end Processing path and explicitly prohibits replacing authorization with a permissive mock in the vertical test.

### Finding 7 — Failure semantics

**Status: PASS.**

Authentication failure, authorization denial, and infrastructure failure remain distinct.

### Finding 8 — Scope control

**Status: PASS.**

The design explicitly excludes role inheritance, wildcards, deny policies, administration framework, persistence, report runtime, and other future features.

## Architecture Review Verdict

**APPROVED FOR IMPLEMENTATION.**

No architecture amendments are required before implementation.

The Slice 6 implementation should remain test-focused and should not alter the approved Phase 11 production security architecture.
