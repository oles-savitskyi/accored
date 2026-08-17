# Phase 2 — Runtime Configuration Consumption & Metadata Resolution v1

## Status

Design baseline.

## Purpose

This document defines the v1 runtime boundary for consuming the currently bound
configuration and resolving metadata through that configuration.

The purpose of this step is to establish a stable runtime-facing access model
between:

- the active runtime configuration;
- configuration metadata;
- metadata lookup;
- runtime consumers.

This step does not introduce a new metadata model.

It defines how already available metadata becomes consumable by runtime code
through the active configuration boundary.

---

# 1. Scope

Step 7 introduces the runtime consumption and metadata resolution boundary.

The scope includes:

1. access to the currently bound configuration;
2. explicit metadata resolution through the active configuration;
3. separation between configuration lifecycle and metadata consumption;
4. stable runtime-facing lookup semantics;
5. failure semantics for missing metadata;
6. preservation of metadata identity;
7. prevention of runtime consumers bypassing the active configuration boundary.

The scope does not include:

- metadata definition design;
- metadata compilation;
- metadata validation;
- configuration loading;
- configuration activation;
- configuration persistence;
- database access;
- dynamic metadata mutation;
- metadata caching;
- metadata version migration;
- dependency injection framework;
- application service architecture;
- document runtime;
- catalog runtime;
- register runtime;
- authorization.

Those concerns remain outside this step.

---

# 2. Architectural Context

The Phase 2 configuration lifecycle is:

LOADED Candidate
       │
       │ validate
       ▼
VALIDATED Candidate
       │
       │ activate
       ▼
ActiveConfiguration

`ACTIVE` is not a lifecycle state transition of `ConfigurationCandidate`.

Activation produces a separate `ActiveConfiguration` representing the
runtime-visible configuration snapshot.

The runtime binding boundary introduced by Step 6 establishes which
`ActiveConfiguration` is currently available to runtime code.

Step 7 defines how runtime code consumes that configuration.

The resulting conceptual chain is:

ConfigurationCandidate
        │
        │ validation
        ▼
Validated Candidate
        │
        │ activation
        ▼
ActiveConfiguration
        │
        │ runtime binding
        ▼
RuntimeConfigurationBinding
        │
        │ consumption
        ▼
Metadata Resolution
        │
        ▼
Runtime Consumer

Runtime consumers must resolve metadata through this boundary.

---

# 3. Problem Statement

A runtime configuration may contain a metadata registry, but exposing the
registry itself as the primary runtime API would couple runtime code to the
configuration storage representation.

That would create several problems:

- runtime code would know how metadata is stored;
- lookup semantics would become duplicated across consumers;
- configuration lifecycle concerns would leak into runtime code;
- future changes to metadata storage would affect runtime consumers;
- consumers could potentially access metadata that is not part of the
  currently bound configuration.

The platform therefore requires a dedicated runtime-facing resolution
boundary.

The runtime should ask for metadata by logical identity rather than directly
accessing the underlying registry.

---

# 4. Design Goals

The v1 design has the following goals.

## 4.1 Single Runtime Configuration Source

Runtime metadata resolution must use the configuration currently exposed by the
runtime configuration binding boundary.

There must be one authoritative runtime configuration source.

---

## 4.2 Explicit Metadata Resolution

Runtime consumers must explicitly request metadata using its logical identity.

Conceptually:

    metadata = resolver.resolve(identifier)

The resolver determines the metadata from the currently bound configuration.

---

## 4.3 Configuration Boundary Preservation

Runtime consumers must not access the internal metadata registry directly.

The intended dependency direction is:

    Runtime Consumer
          │
          ▼
    Metadata Resolver
          │
          ▼
    Runtime Configuration Binding
          │
          ▼
    Active Configuration
          │
          ▼
    Metadata Registry

The registry remains an implementation detail of the configuration model.

---

## 4.4 Stable Metadata Identity

Metadata resolution must preserve the existing metadata identity model.

The resolver must operate on the existing logical `Identifier` type.

It must not introduce a second identifier representation.

---

## 4.5 Deterministic Failure

If requested metadata is not present in the active configuration, resolution
must fail explicitly.

A missing metadata object must not result in:

- `None`;
- an empty placeholder;
- implicit fallback;
- lookup in another configuration;
- creation of metadata.

---

# 5. Runtime Configuration Consumption Model

The runtime configuration binding established in Step 6 exposes the currently
bound `ActiveConfiguration`.

Step 7 introduces a consumption layer above that binding.

Conceptually:

    RuntimeConfigurationBinding
                │
                │ current()
                ▼
       ActiveConfiguration
                │
                │ metadata access
                ▼
        Metadata Resolution

The consumption layer does not own the active configuration.

It does not activate configurations.

It does not validate configurations.

It only consumes the currently bound configuration.

---

# 6. Proposed Runtime API

The v1 runtime-facing abstraction is:

    MetadataResolver

Its primary responsibility is resolving metadata from the currently bound
runtime configuration.

Conceptually:

    resolver = MetadataResolver(binding)

    metadata = resolver.resolve(identifier)

The resolver must obtain the current configuration from the supplied runtime
configuration binding.

It must not maintain an independent configuration reference that can diverge
from the binding.

---

# 7. Resolver Responsibility

`MetadataResolver` is responsible for:

1. obtaining the currently bound `ActiveConfiguration`;
2. locating metadata by logical `Identifier`;
3. returning the corresponding metadata object;
4. raising a deterministic error when metadata cannot be resolved.

It is not responsible for:

- loading configurations;
- validating configurations;
- activating configurations;
- modifying configurations;
- registering metadata;
- compiling metadata;
- persisting metadata.

---

# 8. Active Configuration Dependency

The resolver depends on the runtime configuration binding boundary.

It must not depend directly on:

- `ConfigurationCandidate`;
- `ConfigurationLoader`;
- `ConfigurationValidator`;
- `ConfigurationActivator`.

The intended dependency is:

    MetadataResolver
          │
          ▼
    RuntimeConfigurationBinding
          │
          ▼
    ActiveConfiguration

This preserves the lifecycle boundaries established in previous steps.

---

# 9. Metadata Resolution Semantics

Given an identifier `I` and currently bound configuration `C`:

    resolve(I, C)

returns the metadata object associated with `I` in `C.metadata_registry`.

If the identifier is registered:

    resolve(I, C) → Metadata

If the identifier is not registered:

    resolve(I, C) → MetadataResolutionError

No fallback resolution is performed.

---

# 10. Missing Active Configuration

Runtime metadata resolution requires an active runtime configuration.

If no configuration is currently bound, resolution must fail explicitly.

The resolver must not:

- create an implicit configuration;
- use a default configuration;
- access a configuration candidate;
- access a previously bound configuration;
- access global metadata.

The absence of a bound configuration is therefore a runtime configuration
error.

Conceptually:

    no active configuration
            │
            ▼
    RuntimeConfigurationError

The exact exception type may be defined during implementation, but the
semantic distinction must remain explicit.

---

# 11. Missing Metadata

If an active configuration exists but the requested identifier is not present
in its metadata registry, resolution must fail explicitly.

Conceptually:

    active configuration
            │
            ▼
    metadata lookup
            │
       ┌────┴────┐
       │         │
     found      absent
       │         │
       ▼         ▼
    Metadata   MetadataResolutionError

The error must identify the requested metadata identity sufficiently for
diagnostics.

---

# 12. No Fallback Resolution

v1 explicitly prohibits fallback resolution.

The resolver must not search:

- another active configuration;
- configuration candidates;
- standard configuration;
- global metadata;
- previously active configuration;
- application-specific registries.

The currently bound configuration is the only source of runtime metadata.

This rule is important for deterministic runtime behavior.

---

# 13. Configuration Replacement

Runtime configuration binding may replace the currently active configuration.

The resolver must always resolve against the configuration currently exposed
by the binding boundary.

Therefore:

    bind(C1)
    resolve(I) → metadata from C1

followed by:

    bind(C2)
    resolve(I) → metadata from C2

provided that `I` exists in both configurations.

The resolver must not retain a stale reference to `C1`.

---

# 14. Resolver Does Not Mutate Configuration

Metadata resolution is read-only.

The resolver must not modify:

- `ActiveConfiguration`;
- metadata objects;
- metadata registry;
- runtime configuration binding.

Resolution is therefore observational only.

---

# 15. Metadata Object Identity

If metadata is resolved successfully, the resolver returns the metadata
object belonging to the active configuration.

The resolver must not:

- clone metadata;
- reconstruct metadata;
- transform metadata into another representation;
- compile metadata again.

This preserves metadata identity and keeps resolution separate from metadata
compilation.

---

# 16. Registry Encapsulation

The existing `MetadataRegistry` remains the metadata storage abstraction.

Its internal storage must not become part of the runtime consumer contract.

The resolver may use registry operations internally.

Runtime consumers should depend on:

    MetadataResolver

rather than:

    MetadataRegistry

This preserves the runtime/metadata separation.

---

# 17. Relationship with MetadataRegistry

The conceptual responsibility split is:

### MetadataRegistry

Owns:

- metadata registration;
- metadata storage;
- metadata lookup primitives;
- metadata collection.

### MetadataResolver

Owns:

- runtime configuration access;
- runtime-facing metadata resolution;
- runtime resolution failure semantics.

### RuntimeConfigurationBinding

Owns:

- currently bound active configuration;
- configuration replacement;
- runtime configuration visibility.

These responsibilities must not be merged.

---

# 18. Relationship with Metadata Compiler

The metadata compiler remains responsible for transforming definitions into
metadata.

The resolver consumes the resulting metadata.

The dependency direction is:

    Definition
        │
        ▼
    Metadata Compiler
        │
        ▼
    Metadata Registry
        │
        ▼
    Active Configuration
        │
        ▼
    Metadata Resolver
        │
        ▼
    Runtime Consumer

The resolver must never invoke the metadata compiler.

---

# 19. Relationship with Configuration Activation

Activation and resolution remain separate concerns.

Activation:

    Validated Candidate
            │
            ▼
    ActiveConfiguration

Resolution:

    ActiveConfiguration
            │
            ▼
    Metadata

Resolution must only consume already activated configuration.

It must never activate a candidate as a side effect of resolution.

---

# 20. Relationship with Runtime Binding

Runtime binding establishes which active configuration is visible.

Metadata resolution consumes that visibility.

Therefore:

    RuntimeConfigurationBinding
            │
            ▼
    MetadataResolver

The resolver should not duplicate binding semantics.

For example, it must not maintain its own `current_configuration` state
independent from `RuntimeConfigurationBinding`.

---

# 21. Runtime Consumer Contract

A runtime consumer requiring metadata should depend on a resolver abstraction.

Conceptually:

    class RuntimeConsumer:
        def __init__(self, resolver: MetadataResolver):
            ...

        def execute(self, identifier: Identifier):
            metadata = self._resolver.resolve(identifier)

The runtime consumer should not know:

- how configuration was loaded;
- how configuration was validated;
- how configuration was activated;
- how metadata was registered;
- where metadata is physically stored.

This establishes a clean runtime dependency boundary.

---

# 22. Error Model

v1 distinguishes at least two runtime resolution failures.

## 22.1 No Active Configuration

Condition:

    no active configuration is bound

Semantic error:

    RuntimeConfigurationError

Meaning:

    Runtime metadata resolution cannot proceed because no active
    configuration is available.

---

## 22.2 Metadata Not Found

Condition:

    active configuration exists
    requested identifier is absent

Semantic error:

    MetadataResolutionError

Meaning:

    The requested metadata object is not part of the active configuration.

---

# 23. Error Boundary

Resolution errors must occur at the resolution boundary.

Runtime consumers should not need to inspect:

- configuration binding internals;
- registry internals;
- dictionary membership;
- internal storage structures.

The resolver translates lower-level lookup conditions into the runtime-facing
resolution contract.

---

# 24. Determinism

For a fixed active configuration `C` and identifier `I`:

    resolve(I, C)

must always return the same metadata object or the same semantic failure.

There must be no implicit environmental dependency.

Resolution must not depend on:

- filesystem state;
- database state;
- network state;
- configuration candidates;
- previous runtime configurations.

---

# 25. Thread-Safety / Concurrency

Explicit concurrency support is outside the scope of Step 7.

The v1 resolver does not introduce:

- locks;
- synchronization primitives;
- concurrent configuration snapshots;
- transactional resolution.

The implementation must nevertheless avoid introducing mutable resolver state
that would make future concurrency support unnecessarily difficult.

---

# 26. Caching

Metadata resolution caching is explicitly outside the scope of v1.

The resolver must perform logical resolution against the currently bound
configuration.

No cache invalidation model is introduced.

This is intentional.

Caching may be introduced later after runtime consumption semantics are
stable.

---

# 27. Lifecycle Semantics

Step 7 does not modify the configuration lifecycle.

The lifecycle remains:

    LOADED Candidate
          │
          │ validate
          ▼
    VALIDATED Candidate
          │
          │ activate
          ▼
    ActiveConfiguration

Runtime resolution begins only after an `ActiveConfiguration` has been bound
to the runtime.

There is no:

    Candidate → Runtime Metadata

shortcut.

---

# 28. Immutability Boundary

The resolver treats `ActiveConfiguration` as a runtime snapshot.

Resolution does not mutate the snapshot.

If the runtime binding is replaced:

    C1 → C2

future resolutions use `C2`.

Previously returned metadata objects remain objects belonging to `C1`.

The resolver does not migrate or rewrite previously returned objects.

---

# 29. Version Semantics

The resolver does not interpret configuration versions.

For example, it does not implement:

- version comparison;
- upgrade;
- downgrade;
- compatibility checking;
- migration.

Those concerns belong to configuration lifecycle and future version management
boundaries.

The resolver simply consumes the active snapshot selected by the runtime
binding.

---

# 30. Identity Semantics

Metadata resolution uses the existing logical metadata identity.

No new runtime-specific metadata identifier is introduced.

The identity flow remains:

    Identifier
        │
        ▼
    MetadataRegistry
        │
        ▼
    Metadata

This maintains consistency with the existing metadata architecture.

---

# 31. Public API

The configuration package should expose the runtime resolution abstraction
through its public API.

The intended public surface is conceptually:

    MetadataResolver
    MetadataResolutionError

If a separate runtime configuration error type is introduced, it should also
be exposed where appropriate.

The internal registry remains an implementation-level abstraction.

---

# 32. Testing Requirements

The implementation must test at least the following scenarios.

## 32.1 Successful Resolution

A bound configuration contains metadata.

Resolution returns the expected metadata object.

---

## 32.2 Resolution by Identifier

The resolver accepts the existing `Identifier` type.

---

## 32.3 Missing Metadata

An active configuration exists but does not contain the requested identifier.

Resolution raises the expected resolution error.

---

## 32.4 No Active Configuration

No configuration is bound.

Resolution raises the expected runtime configuration error.

---

## 32.5 Configuration Replacement

After replacing the bound configuration, resolution uses the new configuration.

---

## 32.6 No Stale Configuration

The resolver must not continue resolving against a previously bound
configuration after replacement.

---

## 32.7 Read-Only Behavior

Resolution does not mutate the active configuration or its registry.

---

## 32.8 Public API

The new runtime resolution types are exported through the configuration
package public API.

---

# 33. Explicit Non-Goals

The following are not introduced by Step 7:

- metadata caching;
- metadata fallback;
- metadata inheritance;
- metadata overlays;
- metadata merging;
- metadata compilation;
- metadata mutation;
- configuration activation;
- configuration validation;
- configuration loading;
- configuration persistence;
- dependency injection framework;
- runtime service locator;
- database-backed metadata;
- concurrency management;
- authorization-aware metadata resolution;
- metadata version negotiation.

---

# 34. Architectural Invariants

The following invariants are established by Step 7.

### Invariant 1

Runtime metadata is resolved only from the currently bound configuration.

### Invariant 2

Runtime consumers do not access `MetadataRegistry` directly.

### Invariant 3

Metadata resolution does not activate or validate configurations.

### Invariant 4

Metadata resolution does not mutate configuration state.

### Invariant 5

A missing active configuration is an explicit runtime failure.

### Invariant 6

A missing metadata identity is an explicit resolution failure.

### Invariant 7

The resolver does not maintain an independent active configuration state.

### Invariant 8

Metadata identity is preserved.

### Invariant 9

Configuration replacement changes the source of future metadata resolution.

### Invariant 10

Metadata resolution does not introduce a new metadata lifecycle.

---

# 35. Result of Step 7

After Step 7, the configuration/runtime architecture provides the following
complete path:

    Configuration Loading
            │
            ▼
    Configuration Candidate
            │
            ▼
    Candidate Validation
            │
            ▼
    Configuration Activation
            │
            ▼
    ActiveConfiguration
            │
            ▼
    Runtime Configuration Binding
            │
            ▼
    Metadata Resolution
            │
            ▼
    Runtime Consumer

This establishes the first complete runtime-facing configuration consumption
path without introducing application-specific runtime behavior.

---

# 36. Out of Scope for Phase 2

The following remain candidates for later phases:

- runtime object instantiation;
- catalog runtime binding;
- document runtime binding;
- register runtime binding;
- runtime field access;
- runtime validation against metadata;
- metadata-driven persistence;
- configuration hot reload;
- configuration migration;
- configuration compatibility;
- configuration rollback;
- multi-tenant configuration resolution.

These should be designed only after the v1 runtime configuration consumption
boundary has been validated.