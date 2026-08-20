# Phase 3 — Runtime Configuration Consumption & Resolution

**Status:** Architectural Definition
**Version:** 1.0
**Phase:** Phase 3 — Runtime Configuration Consumption & Resolution
**Baseline:** `95af009`
**Predecessor:** Phase 2 — Metadata Lifecycle / Configuration Loading

---

## 1. Purpose

This document defines the architectural model for Phase 3 of AcCoreD.

Phase 2 established the configuration lifecycle:

```text
Candidate
    │
    │ validate
    ▼
Validated Candidate
    │
    │ activate
    ▼
ActiveConfiguration
    │
    │ bind
    ▼
RuntimeConfigurationBinding
```

Phase 3 defines how runtime components consume the active configuration and resolve configuration-defined runtime semantics.

The Phase 3 runtime consumption model is:

```text
ActiveConfiguration
        │
        │ publish
        ▼
RuntimeConfigurationBinding
        │
        │ acquire
        ▼
RuntimeConfigurationContext
        │
        │ resolve
        ▼
MetadataResolver
        │
        ▼
RuntimeResolver
        │
        ▼
Runtime Objects
        │
        ▼
Runtime Consumers
```

The purpose of Phase 3 is therefore not to create another configuration lifecycle, but to establish a stable runtime consumption boundary over the configuration lifecycle already completed in Phase 2.

## Current Implementation Status

Phase 3 implementation is currently complete through Step 2.

Implemented runtime configuration foundation:

```text
ActiveConfiguration
        │
        │ publish
        ▼
RuntimeConfigurationBinding
        │
        │ acquire
        ▼
RuntimeConfigurationContext
```

The implemented `RuntimeConfigurationContext` is an immutable snapshot of one
`ActiveConfiguration`. It exposes the captured configuration together with its
identity and version. Replacing the configuration published by the binding does
not change an already acquired context.

`ConfigurationActivator` is stateless with respect to runtime publication. It
creates `ActiveConfiguration` but does not retain or expose a current runtime
configuration. `RuntimeConfigurationBinding` is the runtime publication owner.

The following Phase 3 target components remain to be implemented:

```text
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver integration
        ↓
Standard Configuration vertical slice
```

Therefore, this document remains the authoritative architectural definition of
the complete Phase 3 target state; it does not imply that the complete target
state has already been implemented.

---

# 2. Architectural Objective

Phase 3 shall provide a runtime-facing configuration model that is:

* version-consistent;
* deterministic;
* storage-independent;
* lifecycle-independent;
* explicitly resolvable;
* safe for multiple runtime consumers;
* compatible with the existing Metadata and Runtime architectures.

The central architectural principle is:

> **Activation creates configuration state. Binding publishes it. Context captures a consistent configuration snapshot. Resolution exposes its semantics. Runtime resolution materializes runtime objects. Consumers execute runtime behavior.**

---

# 3. Scope

Phase 3 includes:

1. runtime configuration consumption;
2. runtime configuration binding semantics;
3. configuration snapshot acquisition;
4. runtime configuration context;
5. metadata resolution through the configuration boundary;
6. integration of metadata resolution with runtime object resolution;
7. configuration-version consistency during runtime operations;
8. explicit resolution failure semantics;
9. elimination of direct configuration bypasses by runtime consumers;
10. a configuration-aware runtime vertical slice.

Phase 3 does not include:

* configuration loading;
* configuration candidate validation;
* configuration activation design;
* configuration editing;
* configuration persistence redesign;
* metadata compiler redesign;
* metadata model redesign;
* storage architecture redesign;
* package management;
* extension management;
* hot reload;
* configuration rollback;
* security context implementation;
* session context implementation;
* transaction context implementation;
* Posting implementation;
* Valuation implementation;
* Reporting implementation;
* Integration implementation.

Those concerns remain separate architectural responsibilities.

---

# 4. Relationship to Phase 2

Phase 2 establishes configuration state.

Phase 3 establishes configuration consumption.

The boundary is:

```text
Phase 2
──────────────────────────────────
Candidate
    ↓
Validated Candidate
    ↓
ActiveConfiguration
    ↓
RuntimeConfigurationBinding
──────────────────────────────────
                  │
                  ▼
Phase 3
──────────────────────────────────
RuntimeConfigurationContext
    ↓
MetadataResolver
    ↓
RuntimeResolver
    ↓
Runtime Objects
──────────────────────────────────
```

Phase 3 must not reimplement Candidate, validation or activation.

The existing Phase 2 lifecycle remains authoritative.

---

# 5. ActiveConfiguration

`ActiveConfiguration` represents an activated configuration snapshot.

It is a configuration-domain concept.

Its responsibilities are:

* represent configuration identity;
* represent configuration version;
* expose the published metadata model;
* provide the state from which runtime configuration contexts are created.

`ActiveConfiguration` does not:

* manage runtime consumers;
* resolve runtime objects;
* perform configuration activation;
* load configuration;
* validate candidates;
* expose storage internals as runtime APIs.

An active configuration is treated as published runtime-visible configuration state.

---

# 6. ConfigurationActivator Ownership

`ConfigurationActivator` owns the activation operation.

Its responsibility is:

```text
Validated Candidate
        │
        │ activate
        ▼
ActiveConfiguration
```

`ConfigurationActivator` does not own the currently published runtime configuration.

The following responsibility is explicitly excluded:

```text
ConfigurationActivator
    ✗ current configuration ownership
    ✗ runtime configuration access
    ✗ runtime resolution
```

The activator must therefore not maintain a competing `_current` configuration state.

There is exactly one runtime ownership boundary for the currently published configuration:

```text
RuntimeConfigurationBinding
```

---

# 7. RuntimeConfigurationBinding

`RuntimeConfigurationBinding` is the runtime publication and access boundary for the currently active configuration.

Its responsibility is:

> Provide runtime infrastructure with access to the configuration currently published for runtime consumption.

The binding is not:

* a loader;
* a validator;
* an activator;
* a compiler;
* a metadata registry;
* a runtime object resolver.

Conceptually:

```text
ConfigurationActivator
        │
        │ produces
        ▼
ActiveConfiguration
        │
        │ publish
        ▼
RuntimeConfigurationBinding
```

The binding may replace the currently published configuration.

Replacing the binding target does not mutate the previously published `ActiveConfiguration`.

---

# 8. RuntimeConfigurationContext

## 8.1 Purpose

A `RuntimeConfigurationContext` represents a consistent configuration snapshot for a runtime scope or operation.

The context solves a problem that cannot be safely solved by treating the binding itself as the operation snapshot.

The binding may move from:

```text
V1
```

to:

```text
V2
```

while a runtime operation is in progress.

A runtime operation must nevertheless observe one coherent configuration.

Therefore:

```text
RuntimeConfigurationBinding
        │
        │ acquire
        ▼
RuntimeConfigurationContext
        │
        ▼
ActiveConfiguration(V1)
```

All configuration-dependent resolution performed through that context uses the same `ActiveConfiguration`.

---

## 8.2 Context Responsibility

The minimal Phase 3 configuration context contains:

* configuration identity;
* configuration version;
* access to the bound configuration snapshot;
* configuration-aware resolution access.

It does not yet own:

* security;
* session;
* transaction;
* user;
* tenant;
* locale;
* integration state.

Those concerns belong to the broader Runtime Context architecture and may be integrated later.

---

# 9. Configuration Snapshot Consistency

The fundamental consistency rule is:

> **One RuntimeConfigurationContext resolves against exactly one ActiveConfiguration snapshot.**

For example:

```text
Binding
   │
   ├── V1
   │
   │ acquire
   ▼
Context(V1)
   │
   ├── resolve A
   ├── resolve B
   └── resolve C
```

If the binding is subsequently replaced:

```text
Binding
   │
   └── V2
```

the existing context remains bound to:

```text
Context(V1)
```

A newly acquired context may use:

```text
Context(V2)
```

This prevents configuration-version mixing inside a runtime operation.

---

# 10. Configuration Version as a Consistency Boundary

Configuration version is a runtime semantic boundary.

Given:

```text
Context(V1)
```

the following operations:

```text
resolve(A)
resolve(B)
resolve(C)
```

must all resolve against V1.

The following situation is prohibited:

```text
resolve(A) → V1
resolve(B) → V2
```

within one configuration context.

Activation of a new configuration does not retroactively change an existing context.

---

# 11. Configuration Consumption Boundary

The Configuration Consumption Boundary separates configuration infrastructure from runtime behavior.

```text
Configuration Domain
──────────────────────────────
Candidate
Validated Candidate
ActiveConfiguration
Metadata Registry
Configuration Lifecycle
──────────────────────────────
          │
          │ Consumption Boundary
          ▼
Runtime Domain
──────────────────────────────
Runtime Configuration Context
Metadata Resolution
Runtime Object Resolution
Runtime Consumers
──────────────────────────────
```

Runtime consumers must consume configuration through this boundary.

They must not directly access:

* configuration loaders;
* configuration validators;
* configuration activators;
* configuration files;
* configuration storage;
* `MetadataRegistry` internals.

---

# 12. MetadataResolver

`MetadataResolver` is the first configuration-aware resolution layer.

Its responsibility is:

> Resolve metadata by logical identity within the configuration snapshot represented by the runtime configuration context.

Conceptually:

```text
RuntimeConfigurationContext
        │
        ▼
MetadataResolver
        │
        ▼
Metadata
```

The resolver operates using the existing `Identifier` model.

No separate metadata identity model is introduced.

---

# 13. RuntimeResolver

`RuntimeResolver` remains a separate responsibility.

Its responsibility is:

> Transform configuration-defined metadata into runtime objects.

The resulting resolution chain is:

```text
RuntimeResolver
        │
        ▼
MetadataResolver
        │
        ▼
RuntimeConfigurationContext
        │
        ▼
ActiveConfiguration
        │
        ▼
Metadata
        │
        ▼
Runtime Object
```

For example:

```text
Catalog Identity
        │
        ▼
MetadataResolver
        │
        ▼
Catalog Metadata
        │
        ▼
RuntimeResolver
        │
        ▼
CatalogRuntime
```

`RuntimeResolver` must not independently access `MetadataRegistry`.

---

# 14. Layered Resolution

Phase 3 explicitly separates two resolution levels.

## 14.1 Metadata Resolution

```text
Logical Identity
        ↓
Metadata Definition
```

Responsibility:

```text
MetadataResolver
```

## 14.2 Runtime Object Resolution

```text
Metadata Definition
        ↓
Runtime Object
```

Responsibility:

```text
RuntimeResolver
```

The two layers must not be collapsed into one universal resolver.

---

# 15. MetadataRegistry

`MetadataRegistry` remains an internal metadata/configuration infrastructure component.

It may provide the physical lookup mechanism used by metadata resolution.

However:

> `MetadataRegistry` is not the runtime consumer API.

The intended dependency direction is:

```text
Runtime Consumer
      ↓
RuntimeResolver
      ↓
MetadataResolver
      ↓
RuntimeConfigurationContext
      ↓
ActiveConfiguration
      ↓
MetadataRegistry
```

Runtime consumers must not bypass this chain.

---

# 16. Published Metadata Semantics

An `ActiveConfiguration` represents published configuration state.

Its metadata must therefore be treated as immutable for runtime consumption.

The architectural requirement is:

> **Published metadata exposed by an ActiveConfiguration must not be mutated by runtime consumers.**

The exact implementation mechanism for registry immutability is intentionally deferred.

Possible implementation mechanisms include:

* immutable registry;
* read-only registry view;
* immutable mapping;
* private published storage.

Phase 3 defines the semantic requirement, not the physical mechanism.

---

# 17. Runtime Consumer Contract

Runtime consumers are downstream users of the runtime configuration model.

Examples include:

* Catalog Runtime;
* Document Runtime;
* Posting;
* Valuation;
* Reporting;
* Integration;
* Application Runtime.

A consumer may:

* resolve required configuration semantics;
* inspect runtime definitions;
* execute its own runtime responsibility.

A consumer may not:

* activate configuration;
* validate candidates;
* replace runtime configuration;
* mutate active configuration;
* access configuration storage directly;
* bypass the resolution boundary.

---

# 18. Resolution Determinism

Resolution is deterministic relative to a runtime configuration context.

Given:

```text
same RuntimeConfigurationContext
+
same Resolution Request
```

the result must be the same.

Resolution must not depend on:

* global current configuration;
* physical storage implementation;
* call ordering;
* another runtime consumer;
* implicit fallback;
* arbitrary metadata version selection.

---

# 19. Resolution Failure Semantics

Resolution failures must be explicit.

At minimum, the runtime configuration layer must distinguish:

```text
Configuration unavailable
Metadata not found
Invalid resolution request
Unsupported resolution
```

A missing metadata object must not silently become:

```text
None
```

and must not trigger:

* fallback to another configuration;
* fallback to another version;
* metadata creation;
* implicit default resolution.

The precise exception hierarchy is an implementation concern, but the architectural behavior is fixed.

---

# 20. Storage Independence

Runtime configuration consumption must remain independent of physical storage.

The architecture is:

```text
Runtime Consumer
       ↓
Runtime Resolution
       ↓
Configuration Model
       ↓
Metadata Infrastructure
       ↓
Physical Storage
```

The inverse dependency is prohibited:

```text
Runtime Consumer
       ↓
Storage Representation
```

This preserves the Hybrid Storage Model and Runtime/Metadata Separation principles.

---

# 21. Configuration Replacement

Configuration replacement occurs through the existing lifecycle:

```text
Candidate
    ↓
Validate
    ↓
Activate
    ↓
ActiveConfiguration(V2)
    ↓
Publish
    ↓
Binding
```

Runtime consumers do not participate in this process.

An existing:

```text
RuntimeConfigurationContext(V1)
```

continues to represent V1.

A newly acquired context may represent:

```text
RuntimeConfigurationContext(V2)
```

---

# 22. Runtime Dependency Graph

The target dependency graph is:

```text
ConfigurationActivator
        │
        ▼
ActiveConfiguration
        ▲
        │
RuntimeConfigurationBinding
        │
        ▼
RuntimeConfigurationContext
        │
        ▼
MetadataResolver
        │
        ▼
RuntimeResolver
        │
        ▼
Runtime Objects
        │
        ▼
Runtime Consumers
```

`RuntimeResolver` must not depend directly on `MetadataRegistry`.

---

# 23. Standard Configuration Integration

The existing Standard Configuration runtime path historically uses:

```text
MetadataCompiler
      ↓
MetadataRegistry
      ↓
RuntimeResolver
      ↓
CatalogRuntime
```

Phase 3 shall converge this path toward:

```text
Standard Configuration Definition
      ↓
Configuration Candidate
      ↓
Validation
      ↓
Activation
      ↓
ActiveConfiguration
      ↓
RuntimeConfigurationBinding
      ↓
RuntimeConfigurationContext
      ↓
MetadataResolver
      ↓
RuntimeResolver
      ↓
CatalogRuntime
```

This integration is required to demonstrate that the standard runtime path does not bypass the configuration consumption boundary.

---

# 24. Phase 3 Vertical Slice

The minimum architectural proof for Phase 3 is:

```text
Standard Definition
        ↓
Metadata Compiler
        ↓
Configuration Candidate
        ↓
Configuration Validation
        ↓
Configuration Activation
        ↓
ActiveConfiguration
        ↓
RuntimeConfigurationBinding
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
CatalogRuntime
```

The vertical slice must demonstrate:

1. one configuration becomes active;
2. runtime acquires a configuration context;
3. metadata is resolved through that context;
4. runtime object resolution uses the resolved metadata;
5. no runtime consumer directly accesses `MetadataRegistry`;
6. configuration replacement does not corrupt an existing context.

---

# 25. Architectural Invariants

### P3-I1 — Single Runtime Ownership

`RuntimeConfigurationBinding` is the sole runtime ownership boundary for the currently published configuration.

### P3-I2 — Activation Isolation

`ConfigurationActivator` creates `ActiveConfiguration` but does not retain current runtime configuration state.

### P3-I3 — Snapshot Consistency

Each `RuntimeConfigurationContext` is bound to exactly one `ActiveConfiguration` snapshot.

### P3-I4 — Resolution Consistency

All configuration-dependent resolution performed through one context uses the same configuration snapshot.

### P3-I5 — Version Isolation

Activation of a new configuration does not modify an existing runtime configuration context.

### P3-I6 — Consumer Isolation

Runtime consumers access configuration only through the runtime consumption/resolution boundary.

### P3-I7 — Storage Independence

Runtime consumers do not depend directly on physical configuration or metadata storage.

### P3-I8 — Layered Resolution

Metadata resolution and runtime-object resolution are separate responsibilities.

### P3-I9 — Lifecycle Isolation

Runtime resolution does not load, validate or activate configuration.

### P3-I10 — Published Snapshot Semantics

Metadata exposed through an active configuration is treated as immutable published state.

### P3-I11 — Deterministic Resolution

The same resolution request against the same configuration context produces the same semantic result.

### P3-I12 — Explicit Failure

Configuration and metadata resolution failures are explicit and deterministic.

---

# 26. Ownership Matrix

| Concern                                | Owner                       |
| -------------------------------------- | --------------------------- |
| Candidate loading                      | Configuration Loader        |
| Candidate validation                   | Configuration Validator     |
| Activation                             | Configuration Activator     |
| Active configuration state             | ActiveConfiguration         |
| Current runtime publication            | RuntimeConfigurationBinding |
| Runtime configuration snapshot         | RuntimeConfigurationContext |
| Metadata resolution                    | MetadataResolver            |
| Runtime object resolution              | RuntimeResolver             |
| Metadata storage/lookup infrastructure | MetadataRegistry            |
| Runtime behavior                       | Runtime Consumer            |
| Physical persistence                   | Storage Architecture        |
| Metadata compilation                   | Metadata Compiler           |

---

# 27. Architectural Decisions Introduced by Phase 3

Phase 3 establishes the following decisions:

1. `ConfigurationActivator` does not own current runtime configuration state.
2. `RuntimeConfigurationBinding` is the single runtime publication boundary.
3. `RuntimeConfigurationContext` captures one coherent configuration snapshot.
4. Configuration version is a runtime consistency boundary.
5. `MetadataResolver` resolves metadata through the runtime configuration context.
6. `RuntimeResolver` consumes configuration-aware metadata resolution rather than accessing the registry directly.
7. `MetadataRegistry` remains an internal infrastructure component.
8. Runtime consumers cannot bypass the configuration consumption boundary.
9. Published metadata is treated as immutable runtime-visible state.
10. Runtime resolution is deterministic relative to its configuration context.

---

# 28. Relationship to Existing Phase 2 Documentation

The existing Phase 2 document:

`PHASE_2_RUNTIME_CONFIGURATION_CONSUMPTION_AND_METADATA_RESOLUTION.md`

describes the initial v1 metadata consumption boundary introduced during Phase 2.

That document remains valid as implementation history.

This Phase 3 document supersedes it as the architectural definition of runtime configuration consumption by extending the model with:

* runtime configuration context;
* configuration snapshot semantics;
* version consistency;
* layered runtime resolution;
* integration with `RuntimeResolver`;
* explicit prevention of the runtime resolver bypass;
* runtime consumer convergence.

The existing Phase 2 implementation plan remains historical implementation documentation and should not be reused as the Phase 3 implementation plan.

---

# 29. Phase 3 Completion Criteria

Phase 3 architectural completion requires:

* configuration ownership is unambiguous;
* runtime configuration context semantics are implemented;
* runtime resolution uses one configuration snapshot per context;
* `RuntimeResolver` no longer bypasses configuration resolution;
* metadata resolution remains configuration-aware;
* standard runtime path uses the configuration consumption boundary;
* published configuration state cannot be mutated by runtime consumers;
* resolution failures are explicit;
* the Phase 3 vertical slice passes;
* architectural invariants are covered by tests.

---

# 30. Summary

Phase 3 extends the completed configuration lifecycle into a coherent runtime consumption architecture.

The final model is:

```text
Candidate
    ↓
Validated Candidate
    ↓
ActiveConfiguration
    ↓
RuntimeConfigurationBinding
    ↓ acquire
RuntimeConfigurationContext
    ↓
MetadataResolver
    ↓
RuntimeResolver
    ↓
Runtime Objects
    ↓
Runtime Consumers
```

The central architectural rule is:

> **Runtime consumes configuration through a version-consistent runtime context; runtime resolution never bypasses that boundary.**
