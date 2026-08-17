# Phase 2 — Runtime Configuration Binding

**Status:** Design  
**Version:** 1.0  
**Scope:** Phase 2 — Configuration Lifecycle  
**Depends on:**
- `PHASE_2_METADATA_LIFECYCLE_MODEL.md`
- `PHASE_2_CONFIGURATION_LOADING_MODEL.md`
- `PHASE_2_CONFIGURATION_CANDIDATE_VALIDATION_MODEL.md`
- `PHASE_2_CONFIGURATION_ACTIVATION_BOUNDARY.md`

---

## 1. Purpose

This document defines the Runtime Configuration Binding boundary for AcCore.

The purpose of this boundary is to provide runtime components with access to the currently active configuration without exposing configuration loading, validation, or activation responsibilities to the runtime.

The runtime must consume configuration through an explicit runtime-facing boundary.

The runtime must not:

- load configuration;
- compile configuration definitions;
- validate configuration candidates;
- activate configuration candidates;
- manage configuration lifecycle.

The resulting architecture is:

    Configuration Definition
            |
            v
    Metadata Compiler
            |
            v
    Configuration Loader
            |
            v
    Configuration Candidate
            |
            v
    Configuration Validator
            |
            v
    VALIDATED Candidate
            |
            v
    Configuration Activator
            |
            v
    ActiveConfiguration
            |
            v
    RuntimeConfigurationBinding
            |
            v
    Runtime

---

## 2. Architectural Objective

The objective is to establish a stable boundary between configuration lifecycle management and runtime execution.

Configuration infrastructure determines which configuration is active.

Runtime consumes the active configuration.

Therefore:

> Runtime consumes configuration; configuration infrastructure manages configuration.

The runtime must depend on the active configuration representation rather than on configuration construction mechanisms.

---

## 3. Responsibility Boundary

### 3.1 Configuration layer

The configuration layer owns:

- configuration loading;
- definition compilation;
- candidate creation;
- candidate validation;
- configuration activation;
- active configuration replacement.

Relevant components include:

- `ConfigurationLoader`;
- `ConfigurationCandidate`;
- `ConfigurationValidator`;
- `ConfigurationActivator`;
- `ActiveConfiguration`.

### 3.2 Runtime layer

The runtime owns:

- business operation execution;
- runtime metadata resolution;
- interaction with runtime services;
- execution against the currently active configuration.

The runtime does not own configuration lifecycle operations.

---

## 4. Runtime Configuration Binding

The runtime-facing boundary is represented by:

    RuntimeConfigurationBinding

Its responsibility is deliberately narrow:

> Provide runtime components with access to the currently active `ActiveConfiguration`.

The binding is an access boundary.

It is not:

- a configuration loader;
- a validator;
- an activator;
- a compiler;
- a metadata registry;
- a configuration lifecycle manager.

Conceptually:

    RuntimeConfigurationBinding
            |
            +-- ActiveConfiguration

---

## 5. Binding Ownership

The configuration lifecycle remains responsible for determining which configuration becomes active.

The binding stores a reference to the currently active configuration.

Conceptually:

    ConfigurationActivator
            |
            | produces
            v
    ActiveConfiguration
            |
            | bound to
            v
    RuntimeConfigurationBinding
            |
            | consumed by
            v
    Runtime

The binding does not assume ownership of the configuration lifecycle.

It only exposes the configuration selected by the lifecycle.

---

## 6. Initial State

A newly created binding has no active configuration.

Conceptually:

    RuntimeConfigurationBinding
            |
            +-- active_configuration = None

Attempting to obtain the active configuration before binding has occurred is an error.

The absence of an active configuration must not be represented as an ordinary successful runtime state.

This makes configuration availability an explicit runtime invariant.

---

## 7. Binding API v1

The minimal API is:

    class RuntimeConfigurationBinding:
        def bind(self, configuration: ActiveConfiguration) -> None:
            ...

        def get(self) -> ActiveConfiguration:
            ...

The API intentionally remains small.

Additional convenience methods should not be introduced until an actual runtime requirement exists.

An optional `is_bound` property may be introduced later if runtime bootstrap requires it.

---

## 8. First Binding

If no configuration is currently bound:

    None
      |
      v
    ActiveConfiguration(v1)

the binding operation succeeds.

After binding:

    RuntimeConfigurationBinding.get()

returns the bound `ActiveConfiguration`.

---

## 9. Configuration Replacement

The binding supports replacement of the currently bound configuration.

Conceptually:

    ActiveConfiguration(v1)
            |
            v
    ActiveConfiguration(v2)

After replacement, future calls to `get()` return `v2`.

The binding does not determine whether the replacement is architecturally or operationally permissible.

That decision belongs to the configuration activation/application lifecycle.

---

## 10. Binding Does Not Activate Configuration

`RuntimeConfigurationBinding` must never activate a candidate.

The following dependency is prohibited:

    RuntimeConfigurationBinding
            |
            v
    ConfigurationActivator

Activation must already have occurred before an `ActiveConfiguration` reaches the binding.

Therefore:

    VALIDATED Candidate
            |
            X
            |
    RuntimeConfigurationBinding

is invalid.

The valid path is:

    VALIDATED Candidate
            |
            v
    ConfigurationActivator
            |
            v
    ActiveConfiguration
            |
            v
    RuntimeConfigurationBinding

---

## 11. Binding Does Not Validate Configuration

The binding must not validate:

- candidates;
- metadata;
- configuration identity;
- configuration version.

Validation is completed before activation.

The binding accepts only `ActiveConfiguration`.

---

## 12. Binding Does Not Compile or Load Configuration

The binding must not depend on:

- `MetadataCompiler`;
- `ConfigurationLoader`;
- configuration definition objects.

This preserves the dependency direction:

    Configuration lifecycle
            |
            v
    Runtime binding
            |
            v
    Runtime

and prevents runtime configuration access from becoming a second configuration lifecycle mechanism.

---

## 13. Candidate Isolation

A `ConfigurationCandidate` must never become visible to runtime before activation.

The following states are not runtime-consumable:

- `LOADED`;
- `VALIDATED`.

Only `ActiveConfiguration` is runtime-consumable.

This preserves the lifecycle boundary established by previous Phase 2 steps.

---

## 14. Active Configuration Stability

`ActiveConfiguration` is treated as a stable runtime configuration snapshot.

The binding must not mutate the active configuration.

For example:

    bind(A)

does not modify `A`.

Later:

    bind(B)

does not modify `A` or `B`.

Only the reference maintained by the binding changes.

---

## 15. Snapshot Semantics

A runtime component may obtain an `ActiveConfiguration` reference:

    configuration = binding.get()

If the binding is subsequently replaced:

    binding:
        v1 -> v2

the previously obtained `ActiveConfiguration(v1)` remains unchanged.

Therefore:

> Rebinding changes future configuration resolution but does not mutate an already obtained active configuration.

This provides deterministic snapshot semantics for consumers that retain the active configuration reference during an operation.

---

## 16. Metadata Resolution

The binding must not duplicate metadata lookup functionality.

The binding exposes the complete `ActiveConfiguration`.

Metadata resolution remains the responsibility of the existing metadata registry and runtime resolution mechanisms.

Conceptually:

    Runtime
        |
        v
    RuntimeConfigurationBinding
        |
        v
    ActiveConfiguration
        |
        v
    MetadataRegistry
        |
        v
    Metadata

The binding therefore establishes configuration context rather than becoming another metadata abstraction layer.

---

## 17. Existing Runtime Resolution

This step does not replace or redesign the existing runtime metadata resolution API.

The initial responsibility of Step 6 is limited to establishing the source of the active configuration.

Existing runtime resolution may continue to operate against metadata structures already available in the platform.

Integration of concrete runtime components with `RuntimeConfigurationBinding` should occur when an actual runtime consumer requires it.

This prevents Step 6 from introducing speculative runtime coupling.

---

## 18. Error Semantics

The binding must distinguish between:

1. no active configuration is bound;
2. an active configuration exists but requested metadata cannot be resolved.

These are different failure conditions.

Conceptually:

    No active configuration
        !=
    Metadata not found

The first condition belongs to the runtime configuration binding boundary.

The second condition belongs to metadata resolution.

A dedicated error type may be introduced for the first condition, consistent with the existing foundation error model.

---

## 19. Startup Ordering

The intended application startup sequence is:

    1. Load configuration
    2. Validate candidate
    3. Activate candidate
    4. Bind ActiveConfiguration
    5. Start runtime

The runtime must not begin normal execution before an active configuration is available.

The broader application bootstrap mechanism may enforce this invariant later.

Step 6 provides the primitive required for that enforcement.

---

## 20. Runtime Configuration Invariant

The target invariant is:

> A running AcCore runtime has an active configuration available through the runtime configuration binding.

This invariant is stronger than merely having a loaded or validated candidate.

The runtime requires an activated configuration.

---

## 21. Configuration Identity

The binding does not impose configuration identity rules.

Identity remains a property of `ActiveConfiguration`.

For example:

    identity = standard

is preserved by the binding.

The binding does not decide whether one configuration identity may replace another.

Such rules belong to configuration lifecycle management.

---

## 22. Configuration Version

The binding does not compare configuration versions.

Version remains a property of `ActiveConfiguration`.

For example:

    standard v1
        |
        v
    standard v2

is represented by replacing one active configuration reference with another.

Version compatibility, migration, and upgrade policy are outside the scope of the binding.

---

## 23. Replacement Semantics

For v1, replacement is intentionally simple:

- the new `ActiveConfiguration` becomes the current binding;
- the previous configuration is not mutated;
- the binding does not perform migration;
- the binding does not perform compatibility checks;
- the binding does not coordinate runtime restart.

More advanced replacement semantics may be introduced by later architecture work.

---

## 24. Thread-Safety

The v1 design does not introduce an elaborate concurrency mechanism.

The binding must not expose a partially updated configuration reference.

A binding operation replaces the complete `ActiveConfiguration` reference.

More sophisticated synchronization may be introduced later if concurrent configuration replacement becomes a supported operational scenario.

---

## 25. Explicit Non-Goals

Step 6 does not introduce:

- configuration persistence;
- configuration migration;
- configuration compatibility checking;
- hot reload;
- automatic configuration discovery;
- configuration dependency resolution;
- runtime restart;
- configuration rollback;
- distributed configuration synchronization;
- multi-tenant configuration selection;
- transaction coordination;
- speculative runtime metadata APIs.

These concerns remain outside the v1 boundary.

---

## 26. Component Model

The expected configuration package becomes conceptually:

    configuration/
        activation.py
        candidate.py
        identity.py
        lifecycle.py
        loader.py
        validator.py
        runtime_binding.py

The corresponding unit test is:

    tests/unit/configuration/test_runtime_binding.py

---

## 27. Public API

The configuration package may expose:

    RuntimeConfigurationBinding

alongside the existing configuration lifecycle types.

The public API should remain intentionally small.

The binding should not expose internal implementation state.

---

## 28. Core Invariants

### RCB-1 — Runtime sees only active configuration

Runtime must never consume `ConfigurationCandidate`.

### RCB-2 — Unbound configuration is an error

A binding without an active configuration cannot satisfy runtime configuration requests.

### RCB-3 — Binding does not activate

The binding must never perform configuration activation.

### RCB-4 — Binding does not validate

The binding must never validate configuration candidates.

### RCB-5 — Binding does not compile

The binding must never invoke `MetadataCompiler`.

### RCB-6 — Binding does not load

The binding must never invoke `ConfigurationLoader`.

### RCB-7 — Binding does not mutate active configuration

The binding only changes its configuration reference.

### RCB-8 — Replacement preserves configuration stability

Replacing the binding does not mutate the previous or new active configuration.

### RCB-9 — Metadata registry remains the metadata source

The binding does not duplicate metadata storage or lookup.

### RCB-10 — Runtime depends on the binding boundary

Runtime should not depend on configuration loading, validation, or activation internals.

---

## 29. Architectural Decision

AcCore adopts an explicit runtime configuration binding boundary.

The runtime consumes configuration exclusively through `RuntimeConfigurationBinding`.

Configuration lifecycle responsibilities remain outside the runtime.

The resulting dependency direction is:

    Configuration Lifecycle
            |
            v
    ActiveConfiguration
            |
            v
    RuntimeConfigurationBinding
            |
            v
    Runtime

This boundary preserves the separation between configuration lifecycle management and runtime execution.

---

## 30. Acceptance Criteria

Step 6 Design is considered satisfied when:

- `ActiveConfiguration` is the only configuration representation visible to runtime;
- runtime obtains the active configuration through an explicit binding;
- an unbound binding fails explicitly;
- first binding is supported;
- replacement is supported;
- replacement does not mutate either configuration;
- binding does not validate;
- binding does not activate;
- binding does not compile;
- binding does not load;
- metadata lookup remains outside the binding;
- existing runtime resolution is not unnecessarily redesigned;
- no hot reload or migration semantics are introduced.

---