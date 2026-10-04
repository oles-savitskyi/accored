# AcCoreD — Phase 11
# Slice 4 — Processing Enforcement
## Architecture Definition / Scope

**Status:** FINAL — Architecture Definition  
**Phase:** 11 — Security  
**Slice:** 4 — Processing Enforcement  
**Baseline:** `d37e02c` — `feat(security): implement Phase 11 Slice 3 authorization`

---

## 1. Purpose

Slice 3 established the reusable Platform authorization service. Slice 4 integrates that service into the generic Platform Processing runtime and establishes the first protected runtime boundary.

The slice ensures that every protected Processing invocation:

1. carries an explicit security context;
2. maps the requested Processing to a stable security target;
3. requires `SecurityOperation.EXECUTE`;
4. authorizes before the Processing implementation can execute;
5. produces no Processing side effects on denial or security failure;
6. propagates authorization infrastructure failures as security failures;
7. preserves existing Processing semantics after authorization succeeds.

The fundamental flow is:

```text
Caller
  │ explicit SecurityContext
  ▼
ProcessingCommand
  │
  ▼
ProcessingRuntime
  ├── build security target
  ├── AuthorizationService.require(EXECUTE)
  ├── DENY ───────────────► AuthorizationDeniedError
  ├── security failure ───► security infrastructure/configuration error
  ▼
Processing resolution
  ▼
ProcessingContext
  ▼
Processing.execute(...)
```

**Mandatory invariant:** `Authorization ALLOW` must precede `Processing.execute(...)`.

---

## 2. Baseline

Security baseline:

- `Principal`;
- `SecurityContext`;
- `User`;
- `Role`;
- `Permission`;
- `SecurityObjectIdentity`;
- `SecurityOperation`;
- authentication/session boundary;
- `AuthorizationService`;
- `DefaultAuthorizationService`;
- `AuthorizationDecision`;
- `AuthorizationDeniedError`;
- security infrastructure/configuration errors;
- Standard authorization composition.

Processing baseline:

- `ProcessingIdentity`;
- `ProcessingDefinition`;
- `ProcessingCommand`;
- `ProcessingExecutionIdentity`;
- `ProcessingContext`;
- `Processing` protocol;
- `ProcessingRuntime` / `DefaultProcessingRuntime`;
- Processing outcome/result semantics;
- progress observer adaptation.

The existing Processing lifecycle is approximately:

```text
ProcessingCommand
      ↓
resolve Processing
      ↓
validate definition identity
      ↓
create execution identity
      ↓
create ProcessingContext
      ↓
Processing.execute(context)
```

Slice 4 adds the authorization gate without moving business-specific security logic into Processing implementations.

---

## 3. Architectural Position

Processing enforcement belongs at the **Platform Processing Runtime boundary**.

It must not be implemented inside individual Processing implementations, Standard Processing implementations, Inventory, Register, Valuation, Reporting, persistence, or application-specific callers.

Dependency direction:

```text
Platform Processing Runtime
          │
          ├──────────► Platform Security Authorization
          │
          ▼
     Processing
```

Security authorization does not depend on Processing runtime implementation details.

---

## 4. Explicit Security Context

Authorization receives an explicit `SecurityContext`. No ambient security state is introduced.

The architecture rejects:

- module-global current principal;
- thread-local current principal;
- `contextvars`-based implicit authorization;
- service-locator lookup of the current principal;
- hidden runtime authentication state.

The caller explicitly supplies the security context associated with the Processing invocation.

---

## 5. Command Context Contract

`ProcessingCommand` is the explicit boundary between caller intent and runtime execution.

A protected Processing command **MUST carry an explicit, immutable `SecurityContext`** representing the security identity associated with that invocation.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    processing: ProcessingIdentity
    parameters: Mapping[str, object]
    security_context: SecurityContext
```

The exact API representation belongs to Concrete API Design; the architectural contract is fixed here.

`ProcessingRuntime` **MUST use this exact context** when constructing the authorization request and, after successful authorization, **MUST propagate the same immutable context** into `ProcessingContext`.

```text
caller
  │ ProcessingCommand
  │ ├─ ProcessingIdentity
  │ ├─ parameters
  │ └─ SecurityContext
  ▼
ProcessingRuntime
  ├─ construct SecurityObjectIdentity
  ├─ authorize using same SecurityContext
  ├─ resolve Processing
  └─ construct ProcessingContext
          └─ same SecurityContext
                ▼
          Processing.execute(...)
```

The runtime **MUST NOT** derive another principal, replace/enrich/mutate the context, authenticate credentials, or substitute an ambient context. In particular, a missing command security context MUST NOT be silently converted into `SecurityContext(principal=None)`: missing context is an API contract violation, while an explicitly supplied context with `principal=None` is an ordinary unauthenticated invocation.

A missing `SecurityContext` is an invalid protected command state. Unauthenticated invocation is represented by `SecurityContext(principal=None)` and is handled by existing authorization semantics:

```text
missing command security context
    → invalid command state / API contract violation

SecurityContext(principal=None)
    → DENY / UNAUTHENTICATED
    → AuthorizationDeniedError
```

---

## 6. Runtime Enforcement

The runtime is the single generic Processing authorization enforcement boundary.

Processing implementations are not required to contain generic authorization checks. The runtime delegates permission, role, principal, activity, and constraint semantics to the existing `AuthorizationService`.

Processing runtime constructs the authorization request; Platform Security evaluates it.

---

## 7. Processing Security Identity

Slice 4 establishes a deterministic mapping:

```text
ProcessingIdentity
        ↓
SecurityObjectIdentity
```

The mapping is deterministic, immutable, independent of concrete Processing instance, Standard configuration, object identity, memory address, and execution identity. The same logical `ProcessingIdentity` MUST always map to the same `SecurityObjectIdentity` namespace/key representation. The mapping contract is stable; its concrete helper/type is resolved by Concrete API Design.

The security target identifies **what Processing is being invoked**, not a particular invocation.

Example:

```text
Processing:
    inventory.rebuild

Security target:
    Processing / inventory.rebuild

Operation:
    EXECUTE
```

`ProcessingExecutionIdentity` is not part of the authorization target.

---

## 8. Protected Operation

Slice 4 protects exactly:

```text
SecurityOperation.EXECUTE
```

No Processing-specific operations such as `REBUILD`, `RETRY`, `CANCEL`, `RESUME`, or `ADMINISTER` are introduced.

The complete authorization key is:

```text
Processing target + EXECUTE
```

---

## 9. Authentication Boundary

Slice 4 does not merge authentication and authorization.

Processing runtime must not:

- authenticate credentials;
- create, refresh, or invalidate sessions;
- validate passwords;
- resolve login credentials;
- query `SessionStore` merely to authorize Processing.

The runtime consumes the prepared context:

```text
Authentication/session boundary
        ↓
prepared SecurityContext
        ↓
Authorization
        ↓
Processing Runtime enforcement
```

Authorization does not reimplement session validation.

---

## 10. Authorization Gate Ordering

The intended lifecycle is:

```text
1. receive ProcessingCommand
2. obtain explicit SecurityContext
3. construct Processing security target
4. require EXECUTE authorization
5. resolve Processing implementation
6. validate Processing definition
7. establish execution identity
8. adapt progress observer
9. construct ProcessingContext
10. invoke Processing.execute(...)
```

The exact ordering of steps 5–9 may be refined in Concrete API Design, but authorization must precede Processing execution and all Processing side effects.

---

## 11. Denial Semantics

A normal authorization denial is not a Processing business failure.

```text
DENY
  ↓
AuthorizationDeniedError
```

The error retains the authorization decision.

Denial must **not** become `ProcessingOutcome.FAILURE`, and there is no Processing result for an authorization-denied invocation.

---

## 12. Security Infrastructure Failure

If authorization cannot safely determine access because authoritative security state is unavailable, inconsistent, or misconfigured, the security failure propagates.

It must not become:

```text
ProcessingOutcome.FAILURE
```

or:

```text
ProcessingOutcome.INDETERMINATE
```

Therefore:

```text
Authorization DENY
    → AuthorizationDeniedError

Authorization infrastructure/configuration failure
    → propagate security error

Authorization ALLOW
    → Processing may execute
```

---

## 13. Fail-Closed Boundary

The following must never result in `Processing.execute(...)`:

```text
missing principal
inactive principal
missing permission
failed authorization constraint
unsupported principal type
missing assigned role
security state resolution failure
security configuration failure
authorization evaluator failure
```

Normal denial and security infrastructure failure remain distinct, but both prevent execution.

---

## 14. Security Context Propagation

The authorized `SecurityContext` remains available through the immutable `ProcessingContext`.

This preserves explicit security identity for future downstream protected calls; it does not move generic authorization responsibility into Processing implementations.

```text
ProcessingCommand
      │
      └── SecurityContext
              │
              ▼
       ProcessingContext
              │
              ▼
        Processing
```

Processing must not mutate or replace the caller's context.

Future nested protected operations receive explicitly propagated context rather than ambient state.

---

## 15. No Duplicate Authorization

The runtime gate is authoritative for:

```text
May this principal invoke this Processing?
```

Processing implementations may perform domain/business validation, but that is distinct from authorization.

```text
Authorization:
    may principal execute inventory.rebuild?

Business validation:
    is the requested rebuild configuration valid?
```

---

## 16. Processing Resolution

The security target can be constructed directly from `ProcessingIdentity`; no global security-object registry is required.

Preferred flow:

```text
command.processing_identity
        ↓
security target
        ↓
authorization
        ↓
processing resolution
```

Authorization is evaluated before Processing resolution. The runtime MUST NOT resolve, instantiate, or otherwise disclose a requested Processing to an unauthorized caller. Therefore the architectural order is:

```text
ProcessingIdentity
      ↓
SecurityObjectIdentity
      ↓
Authorization(EXECUTE)
      ↓
Processing resolution
      ↓
Definition validation
      ↓
Execution identity / context
      ↓
Processing.execute(...)
```

This ordering is an architectural security boundary, not an implementation detail. An unauthorized request therefore produces an authorization denial rather than a Processing-not-found result.

---

## 17. Processing Definition Validation

Authorization does not replace the existing definition identity check:

```text
ProcessingDefinition.identity == command.processing_identity
```

The checks remain distinct:

```text
Authorization
    → may this principal invoke the requested Processing?

Definition validation
    → is the resolved implementation the requested Processing?
```

Both remain mandatory.

---

## 18. Progress Observation

Authorization occurs before Processing execution and therefore before any Processing-generated progress notification.

Unauthorized requests and authorization infrastructure failures produce no Processing progress.

Authorized execution retains existing progress observer semantics.

The progress observer is observational and is not a security context transport.

---

## 19. Processing Result Boundary

After successful authorization, existing Processing outcomes remain unchanged:

```text
Authorization ALLOW
        ↓
Processing executes
        ↓
SUCCESS / FAILURE / INDETERMINATE
```

Authorization denial and security infrastructure failure are not represented by `ProcessingOutcome`.

---

## 20. Standard Boundary

Standard provides Processing implementations, Standard security configuration/state, and composition of Platform services. It does not implement a second authorization evaluator.

Required direction:

```text
Standard Processing
        ↓
Platform Processing Runtime
        ↓
Platform Authorization Service
```

not:

```text
Standard Processing
        ↓
Standard authorization evaluator
```

A Standard Processing must not bypass the Platform runtime security gate.

---

## 21. Direct and Nested Invocation

Slice 4 protects the `ProcessingRuntime` boundary.

The supported protected entry point is:

```text
ProcessingRuntime.execute(...)
```

Slice 4 does not establish generic enforcement for arbitrary direct Python method calls and does not introduce a second interceptor framework.

A caller directly invoking a concrete Processing implementation outside the runtime is outside this runtime security boundary.

---

## 22. No Generic Security Middleware

Slice 4 does not introduce:

- middleware pipelines;
- decorator authorization frameworks;
- generic authorization interceptors;
- policy engines;
- dependency-injection security hooks;
- global execution guards.

The enforcement mechanism remains deliberately narrow:

```text
DefaultProcessingRuntime
        ↓
AuthorizationService.require(...)
```

---

## 23. Failure Atomicity

Authorization completes before Processing starts, so an authorization failure has no Processing side effects to compensate.

```text
authorization failure
        ↓
zero Processing side effects
```

Slice 4 does not introduce rollback of already executed Processing operations based on later authorization state.

---

## 24. Per-Invocation Authorization

No authorization decision cache is introduced.

Each runtime invocation performs a fresh authorization evaluation using the supplied `SecurityContext` and current authoritative security state.

```text
call 1 → state at call 1
security state changes
call 2 → state at call 2
```

No cached effective permissions or prior decisions may be reused.

---

## 25. Security Context Immutability

The security context is the caller's explicit security snapshot for one invocation.

Processing runtime must not:

- replace its principal;
- add claims;
- modify session state;
- elevate permissions;
- alter role assignments.

Authorization state resolution remains the responsibility of Platform Security.

---

## 26. No Data-Scope Authorization

Slice 4 asks only:

```text
May this principal execute this Processing?
```

It does not introduce authorization for particular inventory records, register instances, valuation data, tenants, ownership, or row-level filtering.

Future resource/data-scope constraints remain explicit Security concerns and are not embedded in Processing runtime logic.

---

## 27. Architectural Tests

The slice must prove the enforcement boundary, including at minimum:

1. authorized execution;
2. missing permission → `AuthorizationDeniedError` and no `Processing.execute()`;
3. `principal=None` → denial and no execution;
4. inactive principal → denial and no execution;
5. failed authorization constraint → denial and no execution;
6. security infrastructure failure → security error and no execution;
7. no progress before authorization;
8. authorized `SUCCESS`, `FAILURE`, and `INDETERMINATE` semantics unchanged;
9. the same immutable security context reaches `ProcessingContext`;
10. definition mismatch remains distinct;
11. missing Processing remains a Processing resolution error and never invokes Processing.

---

## 28. Architectural Boundary Tests

Tests must also verify that:

- Processing runtime depends only on Platform Security contracts;
- Processing runtime does not depend on Standard security implementation;
- Platform Security does not import Processing runtime;
- Processing implementations do not need Standard security repositories;
- no global current principal exists;
- no authorization cache exists;
- no generic service container is introduced;
- no HTTP/API framework is introduced;
- no persistence implementation is introduced into Processing enforcement.

---

## 29. Acceptance Criteria

### AC-1 — Explicit Security Context
Every protected Processing invocation receives an explicit `SecurityContext`.

### AC-2 — Deterministic Security Target
Every Processing identity maps deterministically to a `SecurityObjectIdentity`.

### AC-3 — Execute Permission
Processing invocation is authorized using `SecurityOperation.EXECUTE`.

### AC-4 — Central Enforcement
Authorization is enforced by Platform Processing Runtime rather than individual Processing implementations.

### AC-5 — Pre-Execution Gate
Authorization succeeds before `Processing.execute(...)` can be called.

### AC-6 — Default Deny
Unauthenticated and unauthorized callers cannot execute Processing.

### AC-7 — Fail Closed
Security infrastructure/configuration failures cannot result in Processing execution.

### AC-8 — Distinct Failure Semantics
Authorization denial and security infrastructure failure remain distinct from Processing business outcomes.

### AC-9 — Context Propagation
The authorized security context remains available through immutable Processing execution context.

### AC-10 — Existing Processing Semantics
Definition validation, execution identity, progress observation, and result semantics remain intact.

### AC-11 — No Standard Evaluator
Standard does not implement a second authorization evaluator or bypass the Platform runtime.

### AC-12 — No Ambient Security State
No global or implicit current principal is introduced.

### AC-13 — No Authorization Cache
Authorization is evaluated for each invocation against supplied context and current authoritative state.

### AC-14 — No Business-Specific Security Logic
No Inventory, Register, Valuation, Reporting, or other business-specific authorization rules are embedded in the generic Processing runtime.

---

## 30. Architectural Invariants

1. A Processing implementation cannot execute through the standard Processing runtime unless authorization has first succeeded.
2. `SecurityOperation.EXECUTE` is the only authorization operation introduced for Processing in this slice.
3. Processing security target identity is derived from `ProcessingIdentity`, not `ProcessingExecutionIdentity`.
4. Authorization denial never becomes `ProcessingOutcome.FAILURE`.
5. Security infrastructure/configuration failure never becomes a successful Processing execution.
6. Security infrastructure/configuration failure is not converted into `ProcessingOutcome.INDETERMINATE`.
7. A missing principal is handled through existing authorization denial semantics.
8. Processing runtime never authenticates credentials.
9. Processing runtime never mutates `SecurityContext`.
10. Processing implementations do not own the generic Processing authorization gate.
11. Processing runtime does not implement permission or role semantics.
12. No ambient current-principal state is introduced.
13. No authorization decision cache is introduced.
14. No generic middleware/interceptor/policy framework is introduced.
15. Existing Processing `SUCCESS`, `FAILURE`, and `INDETERMINATE` semantics remain unchanged after successful authorization.
16. An unauthorized invocation produces no Processing side effects and no Processing progress notifications.
17. Processing definition validation remains independent from authorization, but occurs only after authorization has succeeded.
18. Standard does not fork or replace the Platform authorization evaluator.
19. `ProcessingCommand` carries the explicit security context for the invocation.
20. The same immutable `SecurityContext` is used for authorization and propagated into `ProcessingContext`.
21. A missing command security context is an invalid protected command state, not an implicit unauthenticated or authenticated context.

---

## 31. Explicitly Out of Scope

1. HTTP/API endpoint authorization;
2. authentication implementation;
3. session management;
4. session refresh/invalidation;
5. durable security audit events;
6. authorization decision persistence;
7. authorization caching;
8. role hierarchy;
9. wildcard permissions;
10. deny permissions;
11. policy DSL;
12. multi-tenancy;
13. row-level/data filtering;
14. resource ownership framework;
15. security administration UI;
16. security administration CRUD;
17. external identity providers;
18. service-principal authorization;
19. generic middleware/interceptor infrastructure;
20. authorization for arbitrary direct Python method calls;
21. new Processing lifecycle operations beyond `EXECUTE`;
22. business-specific authorization rules;
23. Processing rollback/recovery semantics;
24. Processing persistence;
25. changes to Register, Valuation, Reporting, or other domain authorization semantics.

---

## 32. Implementation Scope

After Architecture Review approval, the Concrete API Design resolves the following as one coherent integration:

```text
Processing command
        │
        ├── ProcessingIdentity
        ├── parameters
        └── SecurityContext
                │
                ▼
Processing security target mapping
                │
                ▼
ProcessingRuntime authorization dependency
                │
                ▼
Authorization gate
                │
                ▼
Processing resolution
                │
                ▼
ProcessingContext
        └── same SecurityContext
                │
                ▼
Processing execution
                │
                ▼
enforcement tests
```

Concrete API Design must specifically resolve:

1. exact `ProcessingCommand.security_context` representation;
2. existing command construction-site adaptations;
3. exact `ProcessingContext.security_context` representation;
4. exact target-mapping API;
5. how `AuthorizationService` is supplied to `DefaultProcessingRuntime`;
6. exact authorization-before-resolution ordering (authorization precedes Processing resolution);
7. error propagation semantics;
8. public exports;
9. Standard composition changes;
10. unit and integration test boundaries.

No implementation begins before Concrete API Design is reviewed and approved.

---

## 33. Architecture Review Resolution

The following architectural decisions are final for Slice 4:

1. `ProcessingRuntime` is the generic Processing authorization enforcement boundary.
2. `ProcessingCommand` carries a mandatory explicit `SecurityContext`.
3. The command security context is immutable and represents the caller security identity for that invocation.
4. The exact same security context is used for authorization and propagated into `ProcessingContext`.
5. Missing security context is an invalid protected command state; `principal=None` represents ordinary unauthenticated context.
6. Authorization targets logical `ProcessingIdentity`, not execution identity.
7. `SecurityOperation.EXECUTE` is the only protected operation in this slice.
8. Authorization occurs before `Processing.execute(...)` and before any Processing side effect.
9. Platform `AuthorizationService` remains responsible for authorization semantics.
12. Processing runtime does not authenticate, mutate, enrich, or replace security context.
13. Authorization denial remains `AuthorizationDeniedError`.
14. Security infrastructure/configuration failures propagate as security failures.
15. Neither denial nor security infrastructure failure is converted into a Processing result.
16. Authorized Processing executions preserve existing Processing semantics.
17. No ambient security state, cache, or generic middleware framework is introduced.
18. Standard does not implement a second authorization evaluator.

These decisions define the architectural contract for Concrete API Design.

---

## 34. Proposed Workflow After Review

```text
Architecture Definition / Scope
        ↓
Architecture Review
        ↓
Final amended Architecture Definition
        ↓
Concrete API Design
        ↓
Concrete API Review
        ↓
Final Approved API Design
        ↓
Implementation
        ↓
Tests / Quality Gate
        ↓
Documentation Reconciliation
        ↓
Commit
```

**Implementation is not authorized by this document.**

The next formal artifact is the reviewed and approved **Concrete API Design**.
