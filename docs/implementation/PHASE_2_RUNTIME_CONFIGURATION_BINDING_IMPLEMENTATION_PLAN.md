# Phase 2 — Runtime Configuration Binding Implementation Plan

**Status:** Implementation Plan  
**Version:** 1.0  
**Scope:** Phase 2 — Configuration Lifecycle  
**Design:** `PHASE_2_RUNTIME_CONFIGURATION_BINDING.md`

---

## 1. Purpose

This document defines the implementation sequence for Runtime Configuration Binding v1.

The implementation must remain limited to the boundary defined by the corresponding design document.

No speculative runtime integration should be introduced.

---

## 2. Implementation Objective

Introduce:

    RuntimeConfigurationBinding

which provides runtime access to the currently active:

    ActiveConfiguration

The implementation must preserve the existing configuration lifecycle boundaries.

---

## 3. Implementation Scope

The implementation consists of:

1. runtime binding class;
2. explicit unbound-state error;
3. unit tests;
4. configuration package public API update;
5. public API tests;
6. formatting and static analysis;
7. full regression test.

---

## 4. Step 1 — Implement Runtime Configuration Binding

Create:

    src/accore/platform/configuration/runtime_binding.py

The component should contain the minimum state necessary to represent:

    active_configuration

The initial state is unbound.

Conceptually:

    class RuntimeConfigurationBinding:
        def __init__(self) -> None:
            self._active_configuration = None

---

## 5. Step 2 — Implement Binding Operation

Implement:

    bind(configuration: ActiveConfiguration) -> None

The method must:

- accept only an `ActiveConfiguration`;
- replace the current configuration reference;
- not mutate the supplied configuration;
- not perform validation;
- not perform activation.

---

## 6. Step 3 — Implement Configuration Access

Implement:

    get() -> ActiveConfiguration

The method must:

- return the currently bound `ActiveConfiguration`;
- raise an explicit error when no configuration is bound.

It must never return `None` as a successful result.

---

## 7. Step 4 — Define Unbound Error

Introduce a dedicated error if the existing foundation error model supports an appropriate location.

The error should represent:

    runtime configuration is not bound

The implementation should not conflate this with metadata lookup errors.

If introducing a new foundation error would expand the scope unnecessarily, a configuration-layer error may be used initially.

The selected error must remain semantically specific.

---

## 8. Step 5 — Add Unit Tests

Create:

    tests/unit/configuration/test_runtime_binding.py

Minimum test cases:

### 8.1 Initial state is unbound

Verify that calling `get()` before binding raises the expected error.

### 8.2 First binding succeeds

Bind an `ActiveConfiguration` and verify that `get()` returns it.

### 8.3 Identity is preserved

Verify that the returned configuration retains the original identity.

### 8.4 Version is preserved

Verify that the returned configuration retains the original version.

### 8.5 Metadata registry is preserved

Verify that the returned configuration exposes the same metadata registry.

### 8.6 Replacement succeeds

Bind configuration A, then configuration B.

Verify:

    get() is B

### 8.7 Previous configuration remains unchanged

Verify that replacement does not mutate configuration A.

### 8.8 New configuration remains unchanged

Verify that binding does not mutate configuration B.

### 8.9 Binding does not activate

Verify that the binding accepts an already active configuration rather than performing lifecycle transitions.

This should be expressed through the API rather than by introducing mock activation behavior.

---

## 9. Step 6 — Update Configuration Public API

Update:

    src/accore/platform/configuration/__init__.py

Export:

    RuntimeConfigurationBinding

Only the intended public type should be exported.

Internal implementation details should remain private.

---

## 10. Step 7 — Update Public API Tests

Update:

    tests/unit/configuration/test_configuration_public_api.py

Verify:

- `RuntimeConfigurationBinding` is importable from `accore.platform.configuration`;
- it appears in `configuration.__all__`.

The existing public API ordering should remain deterministic.

---

## 11. Step 8 — Do Not Modify Runtime Resolution

Step 6 must not modify existing runtime resolution behavior unless required by compilation or typing constraints.

In particular, do not:

- introduce binding calls into existing runtime components;
- redesign metadata lookup;
- replace existing runtime dependencies;
- introduce application bootstrap integration.

Concrete runtime consumption will be addressed when the first actual runtime consumer requires it.

---

## 12. Step 9 — Quality Gate

Run:

    pytest tests/unit/configuration -q

Then:

    ruff check .

Then:

    black .

Then:

    black --check .

Then:

    mypy src

Finally:

    pytest

All checks must pass.

---

## 13. Step 10 — Review Changes

Before committing, inspect:

    git status
    git diff --stat
    git diff

Confirm that only the intended files changed.

Expected implementation files:

    docs/implementation/PHASE_2_RUNTIME_CONFIGURATION_BINDING.md
    docs/implementation/PHASE_2_RUNTIME_CONFIGURATION_BINDING_IMPLEMENTATION_PLAN.md
    src/accore/platform/configuration/runtime_binding.py
    src/accore/platform/configuration/__init__.py
    tests/unit/configuration/test_runtime_binding.py
    tests/unit/configuration/test_configuration_public_api.py

Additional changes require explicit justification.

---

## 14. Commit Boundary

The implementation should be committed as one focused change.

Suggested commit message:

    feat(configuration): add runtime configuration binding

The commit should contain:

- runtime binding implementation;
- tests;
- public API update.

The design and implementation-plan documents may be included in the same commit if they were not already committed separately.

---

## 15. Implementation Constraints

The implementation must not introduce:

- global configuration state;
- singleton configuration managers;
- implicit runtime configuration discovery;
- configuration loading from inside runtime;
- automatic activation;
- validation from inside binding;
- metadata compilation;
- persistence;
- migration;
- hot reload;
- compatibility checking.

The binding must remain a small explicit dependency.

---

## 16. Expected Dependency Direction

The implementation must preserve:

    Configuration lifecycle
            |
            v
    ActiveConfiguration
            |
            v
    RuntimeConfigurationBinding
            |
            v
    Runtime

The following dependency direction is prohibited:

    Runtime
        |
        v
    ConfigurationLoader

or:

    Runtime
        |
        v
    ConfigurationActivator

or:

    RuntimeConfigurationBinding
        |
        v
    ConfigurationActivator

---

## 17. Definition of Done

Step 6 Implementation is complete when:

- `RuntimeConfigurationBinding` exists;
- a new binding starts unbound;
- unbound access raises an explicit error;
- an `ActiveConfiguration` can be bound;
- the bound configuration can be retrieved;
- binding replacement works;
- configuration objects are not mutated by binding;
- unit tests cover the defined semantics;
- the public configuration API is updated;
- `pytest` passes;
- `ruff` passes;
- `black --check` passes;
- `mypy` passes;
- the working tree contains only intended changes;
- the implementation is committed and pushed.

---

## 18. Post-Implementation Review

After implementation, perform a short architectural review confirming:

1. Runtime still cannot consume a candidate directly.
2. Binding contains no lifecycle logic.
3. Active configuration remains the lifecycle output.
4. Metadata lookup remains outside the binding.
5. No speculative runtime integration was introduced.
6. The binding can later serve as the configuration source for runtime bootstrap and concrete runtime services.

If these conditions hold, Step 6 is considered complete.