# AcCoreD — Phase 11
# Slice 4 — Processing Enforcement
## Concrete API Design — Draft

**Status:** APPROVED FOR IMPLEMENTATION  
**Phase:** 11 — Security  
**Slice:** 4 — Processing Enforcement  
**Architecture baseline:** `d37e02c` — `feat(security): implement Phase 11 Slice 3 authorization`  
**Architecture document:** `PHASE_11_Slice_4_Processing_Enforcement_Architecture_Definition_Scope.md`

---

## 1. Purpose

This document translates the approved Slice 4 Architecture Definition into a concrete API and integration design for the existing Processing runtime.

It does not introduce new authorization semantics. Authorization remains the responsibility of the Platform Security `AuthorizationService` established in Slice 3.

The implementation target is the smallest coherent integration that makes the existing generic Processing runtime enforce:

```text
ProcessingCommand.security_context
        ↓
SecurityObjectIdentity(ProcessingIdentity)
        ↓
AuthorizationService.require(EXECUTE)
        ↓
Processing resolution
        ↓
ProcessingContext(same SecurityContext)
        ↓
Processing.execute(...)
```

No implementation should begin until this document has completed Concrete API Review and has been amended to its final approved form.

---

## 2. Design Principles

The concrete API MUST preserve these architectural properties:

1. `ProcessingCommand` carries the caller's explicit immutable `SecurityContext`.
2. `ProcessingRuntime` uses that exact object for authorization.
3. The exact same object is propagated into `ProcessingContext`.
4. Authorization occurs before Processing resolution.
5. Only `SecurityOperation.EXECUTE` is evaluated in this slice.
6. Authorization is delegated to `AuthorizationService`; Processing does not implement permission semantics.
7. `AuthorizationDeniedError` is propagated unchanged as the authorization failure boundary.
8. Security infrastructure/configuration failures are propagated and never converted to a Processing result.
9. Existing Processing result semantics are unchanged after authorization succeeds.
10. No ambient principal, context variable, cache, or generic middleware is introduced.

---

## 3. Existing API Surface to Preserve

The design assumes the existing Phase 10 Processing contracts remain the source of truth for non-security Processing behavior:

- `ProcessingIdentity` — logical identity of a Processing definition;
- `ProcessingDefinition` — declared Processing definition and identity;
- `ProcessingCommand` — caller request to execute a Processing;
- `ProcessingExecutionIdentity` — identity of a concrete execution;
- `ProcessingContext` — execution context supplied to `Processing.execute(...)`;
- `Processing` — execution protocol;
- `ProcessingRuntime` — runtime orchestration boundary;
- `DefaultProcessingRuntime` — default runtime implementation;
- progress observer/adaptation contracts;
- existing Processing outcome/result types and semantics.

Slice 4 changes only the API points required to carry security context and enforce authorization.

No existing Processing outcome is repurposed as a security result.

---

## 4. `ProcessingCommand` Contract

`ProcessingCommand` becomes an explicitly security-aware invocation command.

Conceptual final shape:

```python
@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    processing_identity: ProcessingIdentity
    parameters: object
    runtime_configuration: RuntimeConfigurationContext
    security_context: SecurityContext
    execution_identity: ProcessingExecutionIdentity | None = None
```

### 4.1 Required properties

- The object remains immutable.
- Existing fields and semantics remain unchanged: `processing_identity`, `parameters`, `runtime_configuration`, and optional `execution_identity`.
- `security_context` is mandatory.
- The type is the existing Platform `SecurityContext`.
- No optional/default value is supplied for `security_context`.
- The runtime must not infer it from any other field.
- The runtime must not obtain it from ambient state.

If the existing command is not a dataclass, the same semantic contract is implemented using its existing construction style; the public behavior remains equivalent to the shape above.

### 4.2 Missing context

A protected command without a `security_context` is malformed API state.

It MUST NOT be treated as:

```python
SecurityContext(principal=None)
```

and MUST NOT reach the authorization evaluator as an implicit anonymous request.

Concrete implementation should fail at command construction where the existing command API permits constructor validation. If compatibility requires runtime validation, the runtime must raise the project's established command/API validation error before authorization or Processing resolution.

The exact exception type should reuse an existing Processing command validation error if one exists. Slice 4 must not create a second generic validation hierarchy solely for this field.

### 4.3 Explicit anonymous context

This remains valid input:

```python
SecurityContext(principal=None)
```

It reaches authorization normally and produces the existing:

```text
DENY / UNAUTHENTICATED
        ↓
AuthorizationDeniedError
```

---

## 5. `ProcessingContext` Contract

`ProcessingContext` gains access to the authorized invocation's security context.

Conceptual shape:

```python
@dataclass(frozen=True, slots=True)
class ProcessingContext[P]:
    execution_identity: ProcessingExecutionIdentity
    runtime_configuration: RuntimeConfigurationContext
    parameters: P
    progress_observer: ProcessingProgressObserver
    security_context: SecurityContext
```

The exact existing field order and names must be preserved where possible. The required addition is:

```python
security_context: SecurityContext
```

The runtime must pass the exact object received in `ProcessingCommand`.

The following is forbidden:

```python
# forbidden
security_context=SecurityContext(principal=command.security_context.principal)
```

or any other reconstruction/enrichment.

The intended invariant is identity equality:

```python
context.security_context is command.security_context
```

where the implementation/test can observe object identity.

This is stronger than merely requiring equivalent principal values because it proves that authorization and execution use one invocation context.

---

## 6. Processing Security Target Mapping

### 6.1 Public helper

The concrete API should expose a small Platform Security/Processing mapping helper rather than embedding target construction throughout the runtime.

Recommended API:

```python
def processing_security_target(
    processing: ProcessingIdentity,
) -> SecurityObjectIdentity:
    return SecurityObjectIdentity(
        object_type="processing",
        object_code=processing.value,
    )
```

If project naming conventions prefer a classmethod/factory, the equivalent API is acceptable; the contract must remain identical.

### 6.2 Mapping contract

The mapping MUST be:

- deterministic;
- pure;
- independent of Processing implementation instance;
- independent of execution identity;
- independent of Standard configuration instance;
- independent of runtime instance;
- stable across invocations.

Conceptually:

```text
ProcessingIdentity
    namespace/name
        ↓
SecurityObjectIdentity
    matching namespace/name
```

The target represents the logical Processing resource.

The final mapping is explicitly: 

```python
SecurityObjectIdentity(
    object_type="processing",
    object_code=processing.value,
)
```

`ProcessingIdentity.value` is therefore the stable security object code. The mapping does not inspect a concrete Processing instance.

### 6.3 No registry

The mapping must not require a runtime registry of security objects.

The runtime can construct the target directly from `command.processing_identity`.

### 6.4 No execution identity

This is explicitly wrong:

```python
processing_security_target(execution_identity)
```

The execution identity does not exist at the authorization boundary and must not participate in permission lookup.

---

## 7. `AuthorizationService` Runtime Dependency

`DefaultProcessingRuntime` receives an `AuthorizationService` dependency explicitly.

Recommended constructor shape:

```python
class DefaultProcessingRuntime:
    def __init__(
        self,
        *,
        ... existing dependencies ...,
        authorization_service: AuthorizationService,
    ) -> None:
        ...
```

The exact existing dependency ordering and naming should follow the current runtime constructor conventions.

### 7.1 Why dependency injection

The runtime must not:

- construct `DefaultAuthorizationService` itself;
- locate authorization through a global registry;
- access Standard security configuration directly;
- create an implicit authorization state;
- authenticate a caller.

Dependency injection keeps the runtime platform-generic and testable.

### 7.2 Interface dependency

The runtime depends on the Platform `AuthorizationService` abstraction, not `DefaultAuthorizationService`.

Tests may inject a deterministic fake/stub implementation of the service protocol.

---

## 8. Authorization Request Construction

For every `ProcessingRuntime.execute(command)` invocation, construct:

```python
AuthorizationRequest(
    context=command.security_context,
    target=processing_security_target(command.processing_identity),
    operation=SecurityOperation.EXECUTE,
)
```

`resource` is omitted (`None`) for Slice 4.

This means Processing authorization is resource-independent at this stage. No data-scope or business-resource authorization is introduced.

### 8.1 Fixed operation

The operation is always:

```python
SecurityOperation.EXECUTE
```

It is not supplied by `ProcessingCommand`.

The caller cannot request a different security operation through the Processing API.

---

## 9. Required Runtime Ordering

The final runtime orchestration must have the following security-visible order:

```text
1. validate/obtain ProcessingCommand security context
2. construct SecurityObjectIdentity from ProcessingIdentity
3. build AuthorizationRequest
4. authorization_service.require(request)
5. resolve Processing
6. validate resolved Processing definition identity
7. establish ProcessingExecutionIdentity
8. adapt/prepare progress observer
9. construct ProcessingContext using the same SecurityContext
10. invoke Processing.execute(context)
11. return existing Processing result
```

### 9.1 Security context validation

If the command does not contain the mandatory security context, stop immediately.

No authorization, Processing resolution, or progress notification occurs.

### 9.2 Authorization

Authorization must be the first operation that can establish permission to know/resolve the requested Processing.

A denial stops execution immediately.

### 9.3 Processing resolution

Only after `require(...)` returns successfully may the runtime resolve the Processing implementation.

This ordering is deliberate. It prevents unauthorized callers from distinguishing a valid Processing from a nonexistent/unavailable Processing through resolution errors.

### 9.4 Definition validation

After resolution, existing definition identity validation remains mandatory.

A successful authorization does not imply that the resolved implementation is valid for the requested logical identity.

### 9.5 Execution identity

`ProcessingExecutionIdentity` is established only after authorization and successful resolution/definition validation, following the existing Processing lifecycle.

### 9.6 Progress

No progress observer notification may occur before authorization succeeds.

Observer construction that has no externally visible side effect may occur after authorization; for simplicity and testability, the preferred implementation constructs/adapts the observer after authorization.

---

## 10. Authorization Failure Semantics

### 10.1 Denial

`AuthorizationService.require(...)` is expected to raise the existing `AuthorizationDeniedError` on denial.

The Processing runtime must not catch and convert it to:

- `ProcessingOutcome.FAILURE`;
- `ProcessingOutcome.INDETERMINATE`;
- a synthetic Processing result;
- a generic Processing exception.

The error propagates to the caller unchanged unless the existing runtime contract has a clearly defined transparent exception boundary.

### 10.2 Infrastructure/configuration failure

Security failures such as missing authoritative security state, evaluator/configuration failure, or unsupported security infrastructure must propagate as their existing security exceptions.

The runtime must not interpret them as Processing outcomes.

### 10.3 No retry

Slice 4 does not retry authorization automatically.

A caller may invoke Processing again explicitly, subject to fresh authorization.

---

## 11. `AuthorizationService.require` Call

The runtime should use the existing Slice 3 convenience method:

```python
authorization_service.require(request)
```

rather than duplicating:

```python
decision = authorization_service.authorize(request)
if decision.outcome is DENY:
    ...
```

This preserves one canonical denial-to-exception conversion point.

The runtime therefore owns only request construction and enforcement placement, not authorization semantics.

---

## 12. Runtime Pseudocode

The intended implementation shape is:

```python
def execute(self, command: ProcessingCommand) -> ProcessingResult:
    security_context = command.security_context

    if security_context is None:
        raise ProcessingCommandValidationError(...)

    target = processing_security_target(command.processing_identity)

    request = AuthorizationRequest(
        context=security_context,
        target=target,
        operation=SecurityOperation.EXECUTE,
    )

    self._authorization_service.require(request)

    processing = self._resolve_processing(command.processing_identity)
    self._validate_definition(processing, command.processing_identity)

    execution = command.execution_identity or ProcessingExecutionIdentity(uuid4())
    observer = self._adapt_progress_observer(...)

    context = ProcessingContext(
        execution_identity=execution,
        runtime_configuration=command.runtime_configuration,
        parameters=command.parameters,
        progress_observer=observer,
        security_context=security_context,
    )

    return processing.execute(context)
```

This is pseudocode only. Existing runtime method signatures, result types, and helper names must be retained.

---

## 13. Processing Resolution API

The existing Processing resolver/registry remains responsible for locating the implementation.

No security-specific resolver is introduced.

The runtime must invoke the existing resolver only after authorization.

If the existing runtime currently performs resolution before entering its main execution method, the implementation must move that resolution behind the authorization gate rather than adding a second authorization gate later.

### 13.1 Missing Processing

If an authorized request references a missing Processing, the existing Processing resolution error is returned/raised according to the existing runtime contract.

An unauthorized request must never reach this resolution path.

---

## 14. Definition Identity Validation

Existing definition validation remains in place after resolution.

The validation verifies that the resolved Processing implementation corresponds to the requested `ProcessingIdentity`.

Authorization does not replace this validation.

The security target is derived from the requested identity; the resolved definition is then independently validated against that identity.

This creates two separate guarantees:

```text
Authorization guarantee:
    caller may execute requested ProcessingIdentity

Definition guarantee:
    resolved implementation really represents requested ProcessingIdentity
```

---

## 15. Standard Composition

Standard configuration remains responsible for composing the runtime with the authoritative authorization service.

Conceptually:

```text
Standard security state/configuration
              ↓
DefaultAuthorizationService
              ↓
DefaultProcessingRuntime
```

The runtime does not import or construct Standard security state.

Standard must not create a wrapper evaluator such as:

```python
StandardAuthorizationService
```

whose purpose is to reinterpret Processing permissions.

The Platform service remains authoritative.

---

## 16. Dependency Direction

Expected dependency direction:

```text
standard composition
       │
       ├──► platform.security.AuthorizationService
       │
       └──► platform.processing.DefaultProcessingRuntime
                         │
                         └──► platform.security.AuthorizationService
```

There must be no dependency:

```text
platform.security ──► platform.processing.runtime
```

solely for authorization.

The Security package may define the target-mapping helper only if doing so does not create an import cycle. If project package boundaries make that undesirable, the pure mapping function may live in the Processing package while returning the Platform Security `SecurityObjectIdentity`. The architectural contract is the mapping, not a forced package location.

---

## 17. Import / Circular Dependency Constraint

The implementation must preserve the existing security import boundaries.

In particular:

- Processing runtime may import Security contracts;
- Security authorization must not import Processing runtime;
- target mapping must not require importing a concrete Processing implementation;
- no runtime import of Standard is permitted from Platform Processing or Platform Security.

This is important because Slice 3 already established a clean Platform Security dependency boundary.

---

## 18. Public Exports

The implementation should export only APIs that are intended for callers/composition/tests.

Likely public additions:

```text
ProcessingCommand.security_context
ProcessingContext.security_context
processing_security_target (if the mapping helper is public)
```

No new public authorization evaluator is introduced.

`AuthorizationRequest`, `AuthorizationService`, `SecurityOperation`, `SecurityContext`, and `AuthorizationDeniedError` remain owned/exported by their existing Security modules.

Do not expose a private runtime authorization hook merely for testing.

---

## 19. Construction-Site Adaptation

Every existing `ProcessingCommand` construction site must be updated to supply an explicit `SecurityContext`.

The implementation must not add a default merely to avoid changing callers.

For application/test callers that intentionally represent anonymous access:

```python
security_context = SecurityContext(principal=None)
```

For authorized tests/callers, construct the appropriate existing principal/context according to the established Security test fixtures.

The Slice 4 implementation must inventory all command construction sites before changing the dataclass/constructor.

Expected categories:

1. Platform Processing unit tests;
2. Standard Processing composition/tests;
3. application-facing fixtures/examples, if present;
4. integration tests invoking the runtime directly.

No unrelated business code should gain a hard-coded principal merely to satisfy the new constructor.

---

## 20. Testability

`DefaultProcessingRuntime` must accept an injected `AuthorizationService` so authorization behavior can be tested without requiring the full Standard security composition for every unit test.

Two complementary test levels are required:

### 20.1 Runtime unit tests

Use a fake/stub authorization service that records the `AuthorizationRequest` and either returns or raises the desired outcome.

These tests prove:

- exact context object passed;
- exact target;
- exact operation `EXECUTE`;
- ordering before resolver;
- no execution on denial;
- no progress before authorization;
- same context propagated to Processing.

### 20.2 Security integration tests

Use the real `DefaultAuthorizationService` and existing security state fixtures to prove:

- authenticated authorized principal executes;
- unauthenticated principal is denied;
- inactive principal is denied;
- missing permission is denied;
- failed constraint is denied;
- security-state/configuration failure does not execute Processing.

This keeps authorization semantics tested by Security while runtime tests prove integration/enforcement placement.

---

## 21. Required Test Matrix

| Case | Authorization | Processing resolution | Execute | Expected result |
|---|---|---|---|---|
| Authorized user | ALLOW | reached | yes | existing Processing result |
| Unauthenticated | DENY | not reached | no | `AuthorizationDeniedError(UNAUTHENTICATED)` |
| Inactive principal | DENY | not reached | no | existing authorization denial |
| Missing permission | DENY | not reached | no | existing authorization denial |
| Constraint failure | DENY | not reached | no | existing authorization denial |
| Missing security context | not evaluated | not reached | no | command/API validation error |
| Security infrastructure failure | error | not reached | no | security exception propagated |
| Missing Processing, authorized | ALLOW | error | no | existing resolution error |
| Definition mismatch, authorized | ALLOW | reached | no | existing definition validation error |
| Processing returns SUCCESS | ALLOW | reached | yes | SUCCESS preserved |
| Processing returns FAILURE | ALLOW | reached | yes | FAILURE preserved |
| Processing returns INDETERMINATE | ALLOW | reached | yes | INDETERMINATE preserved |

---

## 22. Ordering Tests

At least one test must record an ordered event trace such as:

```text
authorization
resolution
validation
context
execute
```

and assert:

```text
authorization < resolution < execute
```

A stronger test should prove that resolution is not invoked when authorization denies:

```python
authorization_service.require(...)
# raises

resolver.resolve.assert_not_called()
processing.execute.assert_not_called()
```

This is a core security regression test.

---

## 23. Context Identity Test

A dedicated test must prove that the exact `SecurityContext` object from the command reaches both authorization and Processing execution.

Conceptually:

```python
context = SecurityContext(principal=principal)
command = ProcessingCommand(..., security_context=context)

captured_request = ...
captured_processing_context = ...

assert captured_request.context is context
assert captured_processing_context.security_context is context
```

This test protects against accidental reconstruction of context during runtime orchestration.

---

## 24. No-Progress Tests

For all pre-execution failures:

- authorization denial;
- security infrastructure failure;
- missing command context;

the runtime must produce no Processing progress notifications.

The preferred implementation places observer adaptation and first notification after successful authorization.

A test should use an observer spy and assert zero events.

---

## 25. Security Failure Boundary Tests

A test must inject an authorization service that raises a representative security infrastructure exception.

Assertions:

```text
security exception propagated
resolver not called
Processing.execute not called
progress events == 0
```

The test must explicitly reject conversion to:

```text
ProcessingOutcome.FAILURE
ProcessingOutcome.INDETERMINATE
```

---

## 26. Resolution Confidentiality Test

Because authorization precedes resolution, a denied request for a nonexistent Processing must still result in authorization denial rather than a resolution error.

Test sequence:

```text
command → deny authorization → resolver not called
```

This proves the architectural ordering is actually enforced rather than documented only.

---

## 27. Definition Validation Test

A separate authorized test should supply a resolved Processing whose definition identity does not match the requested `ProcessingIdentity`.

Expected:

```text
authorization succeeds
resolution succeeds
identity validation fails
Processing.execute not called
```

This confirms that authorization does not weaken existing Processing definition integrity checks.

---

## 28. Principal Semantics

Slice 4 does not reinterpret Slice 3 principal semantics.

The runtime passes the supplied `SecurityContext` through unchanged.

Therefore:

- `principal=None` → existing unauthenticated denial;
- inactive user → existing inactive-principal denial;
- missing permission → existing missing-permission denial;
- failed constraint → existing constraint denial;
- unsupported/infrastructure security state → existing security failure.

No Processing-specific principal rules are added.

---

## 29. Resource Semantics

`AuthorizationRequest.resource` remains `None` in Slice 4.

Processing authorization is therefore based on:

```text
SecurityContext
+ Processing SecurityObjectIdentity
+ SecurityOperation.EXECUTE
```

No business resource is introduced merely because a Processing command contains parameters.

Parameters are not authorization resources in this slice.

---

## 30. Parameter Handling

The authorization gate must not inspect or interpret Processing parameters.

For example, the runtime must not add rules such as:

```text
warehouse_id
product_id
amount
period
```

to generic authorization.

Parameter-level authorization is explicitly outside this slice.

The parameters are passed unchanged according to the existing Processing contract.

---

## 31. No Duplicate Authorization

Processing implementations must not be modified to call:

```python
authorization_service.require(...)
```

for the same generic EXECUTE gate.

The runtime owns this gate once.

If a future business-specific operation requires an additional authorization decision, that belongs to a separate architectural decision and must not be silently introduced during Slice 4.

---

## 32. No Authorization Cache

Every `ProcessingRuntime.execute()` invocation calls the injected authorization service.

The runtime stores no authorization decision between calls.

Even if two commands contain equivalent identities and contexts, authorization is evaluated independently against current authoritative security state.

---

## 33. No Ambient Context

The implementation must not introduce:

```python
current_principal()
get_current_security_context()
SecurityContext.current()
```

or equivalents.

The only security context for the invocation is:

```python
command.security_context
```

and the same object is passed to `ProcessingContext`.

---

## 34. Error Taxonomy

Slice 4 should use the existing error taxonomy wherever possible.

| Condition | Error/result boundary |
|---|---|
| Missing command security context | existing command/API validation error |
| Unauthenticated | `AuthorizationDeniedError` |
| Inactive principal | `AuthorizationDeniedError` |
| Missing permission | `AuthorizationDeniedError` |
| Constraint failure | `AuthorizationDeniedError` |
| Missing authoritative security state | existing security infrastructure error |
| Security configuration failure | existing security configuration error |
| Unsupported principal type | existing security failure |
| Processing not found after authorization | existing Processing resolution error |
| Definition mismatch after authorization | existing Processing definition validation error |
| Processing business failure | existing Processing result/error semantics |

Do not add a Processing-specific `UnauthorizedProcessingError`; the existing Security denial type is the canonical boundary.

---

## 35. Compatibility Strategy

This is an intentional API contract change: callers constructing `ProcessingCommand` must now provide security context.

Do not introduce a temporary default such as:

```python
security_context: SecurityContext | None = None
```

merely for backward compatibility.

Such a default would blur the architectural distinction between malformed command state and explicit anonymous invocation.

The implementation slice should update all repository-owned construction sites in one coherent change.

External compatibility is not defined by this internal Platform slice.

---

## 36. Standard Configuration Contract

Standard composition must provide the authoritative `AuthorizationService` to the Processing runtime.

The composition boundary should resemble:

```python
authorization_service = DefaultAuthorizationService(security_state)
processing_runtime = DefaultProcessingRuntime(
    ...,
    authorization_service=authorization_service,
)
```

The exact Standard configuration object names remain those already established by the project.

The runtime must not construct security state itself.

---

## 37. Test Fixtures

Existing Slice 3 security fixtures should be reused wherever possible.

The test suite should provide reusable fixtures for:

- authorized user/context;
- anonymous context;
- inactive user/context;
- missing permission;
- constraint failure;
- security infrastructure failure;
- fake authorization service capturing requests.

Do not duplicate security-state construction logic in Processing tests when an established security fixture can be reused.

---

## 38. File-Level Change Scope

Expected implementation changes are limited to the Processing/security integration surface and tests.

Likely files include:

```text
src/accore/platform/processing/command.py
src/accore/platform/processing/context.py
src/accore/platform/processing/runtime.py
src/accore/platform/processing/__init__.py          # only if required

src/accore/platform/security/...                    # mapping helper only if package placement requires it

src/standard/...                                    # composition adaptation only

tests/unit/processing/...
tests/unit/security/...
tests/integration/...                               # only where existing runtime composition is tested
```

The exact list must be established from the baseline before implementation. No unrelated domain files should be changed.

---

## 39. Public API Stability Rules

The implementation must not expose internal orchestration helpers merely because tests need them.

Prefer testing the public `ProcessingRuntime` contract with injected dependencies.

The following remain implementation details:

- authorization request construction helper if not otherwise useful;
- ordering helper methods;
- private resolver invocation;
- private context construction helper.

Only the target-mapping helper may be public if it is independently useful and aligns with project package conventions.

---

## 40. Type Checking and Protocols

The runtime should type against the existing `AuthorizationService` protocol/abstraction.

No `Any` escape hatch should be introduced for security integration.

Expected strict typing properties:

- `ProcessingCommand.security_context` is exactly `SecurityContext`;
- `ProcessingContext.security_context` is exactly `SecurityContext`;
- authorization request has exact target/operation/context types;
- injected authorization service satisfies the existing protocol;
- no circular type imports are introduced.

`TYPE_CHECKING` imports may be used where required by the established Security import structure, consistent with the Slice 3 solution.

---

## 41. Formatting / Quality Constraints

The implementation must satisfy the repository quality gate:

```text
pytest
ruff check .
black --check .
mypy ...
git diff --check
```

The Slice 4 focused tests should run before the full suite.

No generated `__pycache__` or unrelated files belong in the change archive.

---

## 42. Required Acceptance Tests

The final implementation is acceptable only if tests prove all of the following:

### AC-1 — Explicit Context
Every protected `ProcessingCommand` contains an explicit `SecurityContext`.

### AC-2 — Exact Context Reuse
The exact command context is used for authorization and Processing execution context.

### AC-3 — Stable Target
Target is deterministically derived from `ProcessingIdentity`.

### AC-4 — EXECUTE Only
Authorization always uses `SecurityOperation.EXECUTE`.

### AC-5 — Authorization Before Resolution
Resolver is never called for a denied request.

### AC-6 — No Unauthorized Execute
`Processing.execute()` is never called after authorization denial or security infrastructure failure.

### AC-7 — No Progress Before Authorization
No Processing progress is emitted before authorization succeeds.

### AC-8 — Denial Boundary
Authorization denial propagates as `AuthorizationDeniedError`.

### AC-9 — Security Failure Boundary
Security infrastructure/configuration errors propagate unchanged through the runtime boundary and are not Processing outcomes.

### AC-10 — Existing Processing Semantics
SUCCESS/FAILURE/INDETERMINATE results remain unchanged after successful authorization.

### AC-11 — Definition Validation
Definition identity mismatch remains independently detected.

### AC-12 — Anonymous Semantics
Explicit `principal=None` produces existing unauthenticated denial.

### AC-13 — Missing Context Semantics
Missing context is not converted to anonymous context.

### AC-14 — Standard Composition
Standard composes the authoritative Platform authorization service into the Processing runtime.

### AC-15 — No Duplicate Evaluator
No second Standard authorization evaluator is introduced.

### AC-16 — No Ambient State
No current-principal/global/contextvar security mechanism is introduced.

### AC-17 — Fresh Decision
Authorization is invoked for every Processing command; no decision cache exists.

---

## 43. Concrete API Summary

The final API changes are intentionally minimal and preserve the existing Processing model.

```python
@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    processing_identity: ProcessingIdentity
    parameters: object
    runtime_configuration: RuntimeConfigurationContext
    security_context: SecurityContext
    execution_identity: ProcessingExecutionIdentity | None = None


@dataclass(frozen=True, slots=True)
class ProcessingContext[P]:
    execution_identity: ProcessingExecutionIdentity
    runtime_configuration: RuntimeConfigurationContext
    parameters: P
    progress_observer: ProcessingProgressObserver
    security_context: SecurityContext


def processing_security_target(
    processing: ProcessingIdentity,
) -> SecurityObjectIdentity:
    return SecurityObjectIdentity(
        object_type="processing",
        object_code=processing.value,
    )


class DefaultProcessingRuntime:
    def __init__(
        self,
        processings: Mapping[ProcessingIdentity, Processing[object, object]],
        authorization_service: AuthorizationService,
    ) -> None:
        ...

    def execute(
        self,
        command: ProcessingCommand,
        progress_observer: ProcessingProgressObserver | None = None,
    ) -> ProcessingResult[object]:
        ...
```

The existing `processings` dependency remains unchanged. `AuthorizationService` is the only new runtime dependency.

The enforcement operation is exactly:

```python
request = AuthorizationRequest(
    context=command.security_context,
    target=processing_security_target(command.processing_identity),
    operation=SecurityOperation.EXECUTE,
)
self._authorization_service.require(request)
```

No Processing implementation receives or chooses the authorization operation.

## 44. Review Questions

Concrete API Review should explicitly confirm:

1. Is making `ProcessingCommand.security_context` mandatory compatible with all current command construction sites?
2. Is `SecurityContext` already the correct immutable value passed through Processing, or does its existing API require an adapter?
3. Does the proposed `processing_security_target()` mapping match the existing `SecurityObjectIdentity` construction conventions?
4. Is `AuthorizationService` already exported from the expected Platform Security package for constructor typing/imports?
5. Does `DefaultProcessingRuntime` currently receive dependencies through constructor injection, and where should the new dependency be inserted?
6. Is the existing Processing resolution API callable only after the authorization gate without changing unrelated behavior?
7. What is the exact existing command/API validation error to use if a malformed command can bypass constructor validation?
8. Are all Standard and test construction sites covered by the mandatory context change?
9. Does `ProcessingContext` have any existing serialization/copy semantics affected by adding `SecurityContext`?
10. Are any public exports or documentation indices required for the new fields/helper?

These questions are implementation-facing review questions, not unresolved architectural decisions.

---

## 45. Non-Goals

This API design does not authorize implementation of:

- authentication;
- login/session APIs;
- HTTP authorization;
- authorization caching;
- role hierarchy;
- wildcard or deny permissions;
- policy DSL;
- resource/data authorization;
- multitenancy;
- audit logging;
- administrative security UI;
- additional Processing lifecycle operations;
- business-specific authorization.

---

## 45. Concrete API Review Resolution

The Concrete API Review amendments are incorporated in this final document.

Resolved points:

1. Existing `ProcessingCommand` field names and types are preserved; only mandatory `security_context` is added.
2. Existing `ProcessingContext` field names and generic parameter type are preserved; only mandatory `security_context` is added.
3. `ProcessingIdentity → SecurityObjectIdentity` mapping is deterministic and explicit: `object_type="processing"`, `object_code=processing.value`.
4. `AuthorizationService` is injected into `DefaultProcessingRuntime`; the runtime never constructs security infrastructure.
5. Authorization occurs before Processing resolution.
6. Existing `execution_identity` semantics are preserved.
7. Existing progress-observer semantics are preserved.
8. Existing Processing outcomes and exceptions remain unchanged after successful authorization.
9. Explicit anonymous security context remains an ordinary authorization denial; omitted security context is malformed command state.
10. No generic middleware, ambient security state, decision cache, or duplicate evaluator is introduced.

**Concrete API Review verdict: APPROVED FOR IMPLEMENTATION.**

## 46. Implementation Sequence

After API approval, implementation should proceed in this order:

1. update `ProcessingCommand` contract;
2. update `ProcessingContext` contract;
3. introduce/implement deterministic Processing security target mapping;
4. inject `AuthorizationService` into `DefaultProcessingRuntime`;
5. move/establish Processing resolution behind the authorization gate;
6. propagate the exact command security context into `ProcessingContext`;
7. adapt Standard composition;
8. update repository-owned command construction sites;
9. add focused runtime enforcement tests;
10. add/update integration tests using real authorization service;
11. run focused quality gate;
12. run full quality gate;
13. reconcile documentation;
14. commit Slice 4.

No implementation step should introduce behavior outside the approved Architecture Definition.

---

## 47. Final API Contract

For every protected runtime invocation:

```text
ProcessingCommand
  ├─ processing = logical ProcessingIdentity
  ├─ parameters = existing command parameters
  └─ security_context = explicit immutable caller context
                 │
                 ▼
processing_security_target(processing)
                 │
                 ▼
AuthorizationRequest(
    context=same security_context,
    target=derived target,
    operation=EXECUTE,
)
                 │
                 ▼
AuthorizationService.require(...)
                 │
       ┌─────────┴─────────┐
       │                   │
      DENY               ALLOW
       │                   │
       ▼                   ▼
AuthorizationDenied   Processing resolution
                            │
                            ▼
                       definition validation
                            │
                            ▼
                       execution identity
                            │
                            ▼
                     ProcessingContext
                       └─ same security_context
                            │
                            ▼
                       Processing.execute
```

This is the complete security enforcement contract for Slice 4.

---

## 48. Status

**DRAFT — READY FOR CONCRETE API REVIEW.**

The document is intentionally implementation-ready in structure but does not authorize coding until the Concrete API Review resolves any repository-specific API compatibility issues and a final approved version is produced.
