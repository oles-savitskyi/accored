# Phase 2 — Runtime Configuration Consumption & Metadata Resolution v1
# Implementation Plan

## Status

Implementation plan.

## Purpose

This document defines the implementation sequence for Step 7:

**Runtime Configuration Consumption & Metadata Resolution v1**

The implementation must preserve the architectural boundaries established by
the previous Phase 2 steps.

---

# 1. Starting Point

Step 7 starts from the completed configuration lifecycle:

    LOADED Candidate
          │
          │ validate
          ▼
    VALIDATED Candidate
          │
          │ activate
          ▼
    ActiveConfiguration

and the runtime binding boundary:

    ActiveConfiguration
            │
            ▼
    RuntimeConfigurationBinding

Step 7 adds:

    RuntimeConfigurationBinding
            │
            ▼
    MetadataResolver
            │
            ▼
    Metadata

---

# 2. Implementation Scope

Implementation should introduce the smallest runtime-facing abstraction
necessary to:

1. obtain the currently bound configuration;
2. resolve metadata by `Identifier`;
3. report missing active configuration;
4. report missing metadata;
5. preserve metadata identity;
6. prevent stale configuration references;
7. expose the new API through the configuration package.

No unrelated runtime infrastructure should be introduced.

---

# 3. Proposed Files

Create:

    src/accore/platform/configuration/resolver.py

    tests/unit/configuration/test_resolver.py

Depending on the final naming chosen during implementation, the resolver may
instead be named:

    metadata_resolver.py

The implementation should use one consistent name across:

- source;
- tests;
- documentation;
- public API.

The preferred v1 name is:

    resolver.py

with the primary type:

    MetadataResolver

---

# 4. Public API Changes

Update:

    src/accore/platform/configuration/__init__.py

Export:

    MetadataResolver
    MetadataResolutionError

If a dedicated runtime configuration error is introduced, also export:

    RuntimeConfigurationError

Update:

    tests/unit/configuration/test_configuration_public_api.py

to verify:

- imports;
- `__all__`;
- public availability.

---

# 5. Step 1 — Inspect Existing Runtime Binding

Before implementing the resolver, verify the existing
`RuntimeConfigurationBinding` API.

The resolver must consume the existing binding rather than extending or
duplicating its state.

The implementation should identify the existing operation that returns the
currently bound `ActiveConfiguration`.

If the binding does not expose such an operation, add the smallest necessary
read-only accessor.

Do not redesign runtime binding as part of this step.

---

# 6. Step 2 — Define Runtime Resolution Errors

Introduce explicit runtime-facing errors.

At minimum:

    MetadataResolutionError

If the existing binding error model does not already provide an appropriate
error for missing active configuration, introduce:

    RuntimeConfigurationError

The errors should be small domain-level exceptions.

They should provide useful diagnostic information without exposing internal
storage details.

---

# 7. Step 3 — Implement MetadataResolver

Implement:

    class MetadataResolver:
        ...

Constructor dependency:

    RuntimeConfigurationBinding

Primary operation:

    resolve(identifier: Identifier) -> Metadata

The resolver must:

1. obtain the current active configuration from the binding;
2. fail if no active configuration exists;
3. perform metadata lookup;
4. fail if metadata does not exist;
5. return the metadata object unchanged.

---

# 8. Step 4 — Preserve Binding as Source of Truth

Do not store:

    self._configuration

inside the resolver.

The resolver should retain only the binding dependency.

Conceptually:

    class MetadataResolver:
        def __init__(self, binding):
            self._binding = binding

        def resolve(self, identifier):
            configuration = self._binding.current()
            ...

This ensures that configuration replacement is automatically reflected in
future resolution calls.

---

# 9. Step 5 — Use Existing Metadata Identity

The resolver must accept:

    Identifier

from:

    accore.platform.foundation.identity

Do not introduce:

- `MetadataIdentifier`;
- string-only lookup;
- resolver-specific identity;
- duplicate identity types.

The existing identity model remains authoritative.

---

# 10. Step 6 — Use Existing Metadata Registry

The resolver should use the existing:

    MetadataRegistry

lookup capabilities.

Do not add a second metadata storage structure.

If the existing registry does not expose the required lookup operation, use
the existing public registry API or add the smallest missing operation.

Do not expose registry internals through the resolver.

---

# 11. Step 7 — Define Missing Metadata Semantics

When the active configuration exists but the metadata identifier is absent,
raise:

    MetadataResolutionError

The exception should contain enough context to identify the requested
identifier.

Do not return `None`.

Do not silently fallback.

---

# 12. Step 8 — Define Missing Configuration Semantics

When the binding contains no active configuration, raise the designated
runtime configuration error.

Do not:

- instantiate a default configuration;
- access candidates;
- access a previous configuration;
- access global metadata.

The resolver must fail explicitly.

---

# 13. Step 9 — Unit Tests

Create:

    tests/unit/configuration/test_resolver.py

Minimum test set:

### Test 1

`test_resolve_returns_metadata`

Verify successful resolution.

### Test 2

`test_resolve_uses_identifier`

Verify resolution uses the existing `Identifier`.

### Test 3

`test_resolve_raises_when_metadata_missing`

Verify missing metadata produces `MetadataResolutionError`.

### Test 4

`test_resolve_raises_when_configuration_not_bound`

Verify missing active configuration produces the expected runtime error.

### Test 5

`test_resolve_uses_current_configuration`

Bind configuration C1, resolve metadata, then bind C2 and resolve again.

Verify C2 is used.

### Test 6

`test_resolver_does_not_keep_stale_configuration`

Verify the resolver does not retain C1 after C2 is bound.

### Test 7

`test_resolve_does_not_mutate_configuration`

Verify resolution does not change configuration state or registry contents.

### Test 8

`test_resolved_metadata_identity_is_preserved`

Verify the returned object is the same metadata object registered in the active
configuration.

---

# 14. Step 10 — Public API Tests

Extend:

    tests/unit/configuration/test_configuration_public_api.py

Verify:

    MetadataResolver
    MetadataResolutionError

and any additional public runtime configuration error type.

The test must keep the existing `__all__` ordering convention.

---

# 15. Step 11 — Static and Formatting Checks

Run:

    ruff check .

    black .

    black --check .

    mypy src

All must pass.

---

# 16. Step 12 — Configuration Test Suite

Run:

    pytest tests/unit/configuration -q

The complete configuration test suite must pass.

---

# 17. Step 13 — Full Test Suite

Run:

    pytest

The complete repository test suite must pass.

No existing tests should be weakened or removed to accommodate the new
resolver.

---

# 18. Expected Test Growth

The exact test count is not fixed by this plan.

The implementation should add tests sufficient to cover the defined runtime
resolution contract.

Existing configuration, metadata, runtime, standard configuration, validation,
and vertical tests must remain unchanged unless a genuine public API update
requires an explicit adjustment.

---

# 19. Implementation Constraints

The implementation must not introduce:

- caching;
- global singleton state;
- service locator;
- dependency injection framework;
- metadata fallback;
- metadata merging;
- metadata inheritance;
- metadata cloning;
- metadata mutation;
- configuration activation;
- configuration validation;
- configuration loading.

The implementation should remain small and domain-focused.

---

# 20. Dependency Direction

The final dependency direction should be:

    MetadataResolver
          │
          ▼
    RuntimeConfigurationBinding
          │
          ▼
    ActiveConfiguration
          │
          ▼
    MetadataRegistry
          │
          ▼
    Metadata

The reverse dependency is prohibited.

In particular:

    MetadataRegistry
        X→ MetadataResolver

and:

    ActiveConfiguration
        X→ MetadataResolver

---

# 21. Runtime Consumer Boundary

Step 7 does not require implementing a real application runtime consumer.

A test-level consumer or direct resolver usage is sufficient to establish the
boundary.

Actual consumers such as:

- catalog runtime;
- document runtime;
- register runtime;

will be introduced later.

---

# 22. Integration with Existing Metadata Runtime

The existing metadata runtime components must remain intact.

The resolver is an additional consumption layer.

It does not replace:

- `Metadata`;
- `MetadataRegistry`;
- metadata compiler;
- metadata definitions;
- catalog metadata;
- attribute metadata.

The resolver composes these existing components.

---

# 23. Integration with Existing Configuration Lifecycle

The resolver must respect:

    LOADED
      ↓
    VALIDATED
      ↓
    ActiveConfiguration

No lifecycle changes are introduced.

The resolver must never accept a `ConfigurationCandidate` as its runtime
configuration source.

---

# 24. Integration with Runtime Binding

The runtime binding remains the sole source of the current active configuration.

The resolver consumes it.

Therefore configuration replacement should require no resolver update.

Example:

    binding.bind(configuration_v1)

    resolver.resolve(identifier)
        → metadata_v1

    binding.bind(configuration_v2)

    resolver.resolve(identifier)
        → metadata_v2

The resolver itself remains unchanged.

---

# 25. Failure Safety

Resolution failures must not alter the runtime binding.

If resolution fails because metadata is missing:

    current configuration remains unchanged

If resolution fails because no configuration is bound:

    binding remains unchanged

The resolver is read-only with respect to configuration lifecycle.

---

# 26. Implementation Completion Criteria

Step 7 implementation is complete when all of the following are true:

- `MetadataResolver` exists;
- resolver consumes `RuntimeConfigurationBinding`;
- resolver resolves metadata by existing `Identifier`;
- successful resolution returns the registered metadata object;
- missing metadata raises an explicit resolution error;
- missing active configuration raises an explicit runtime error;
- resolver does not retain a stale configuration;
- resolver does not mutate configuration;
- public API is updated;
- unit tests cover the defined contract;
- `ruff check .` passes;
- `black --check .` passes;
- `mypy src` passes;
- `pytest tests/unit/configuration -q` passes;
- `pytest` passes.

---

# 27. Commit Boundary

The implementation should be committed as one focused feature commit after
all checks pass.

Suggested commit message:

    feat(configuration): add runtime metadata resolution

Documentation changes defining Step 7 should be committed separately before
implementation if they have not already been committed.

---

# 28. Resulting Architecture

After Step 7, the Phase 2 runtime configuration path becomes:

    ConfigurationLoader
            │
            ▼
    ConfigurationCandidate
            │
            ▼
    ConfigurationValidator
            │
            ▼
    ConfigurationActivator
            │
            ▼
    ActiveConfiguration
            │
            ▼
    RuntimeConfigurationBinding
            │
            ▼
    MetadataResolver
            │
            ▼
    Runtime Consumer

This completes the first end-to-end path from configuration loading to
runtime metadata consumption.

---

# 29. Next Step

After Step 7 implementation and consistency review, the next architectural
question is not another configuration lifecycle transition.

The next logical boundary is runtime use of resolved metadata by actual
metadata-driven runtime components.

Candidates include:

- catalog runtime metadata consumption;
- document runtime metadata consumption;
- runtime field access;
- metadata-driven validation;
- runtime object construction.

These should be designed only after Step 7 is implemented and audited.