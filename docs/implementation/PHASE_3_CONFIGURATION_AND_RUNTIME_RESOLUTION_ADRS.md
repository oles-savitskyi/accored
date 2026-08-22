# Phase 3 — Configuration and Runtime Resolution ADRs

## ADR-CONF-002

### Runtime Configuration Ownership

**Status:** Accepted

### Context

Phase 2 introduced `ActiveConfiguration` and `RuntimeConfigurationBinding`.

The implementation initially retained current configuration state inside `ConfigurationActivator`, creating two possible runtime owners of the current configuration.

This conflicts with the intended lifecycle boundary.

### Decision

`RuntimeConfigurationBinding` is the sole runtime ownership boundary for the currently published `ActiveConfiguration`.

`ConfigurationActivator` owns only the activation operation.

It must not retain a competing current configuration state.

The intended ownership model is:

```text
ConfigurationActivator
    │
    │ activate
    ▼
ActiveConfiguration
    │
    │ publish
    ▼
RuntimeConfigurationBinding
```

### Consequences

Positive:

* one authoritative runtime configuration source;
* no ambiguity between activation and runtime publication;
* configuration lifecycle remains isolated from runtime consumption;
* runtime components have a stable access boundary.

Negative:

* the existing activator implementation must remove its competing current-state storage;
* tests that treat `ConfigurationActivator.current()` as an API must be revised.

---

## ADR-CONF-003

### Runtime Configuration Snapshot Context

**Status:** Accepted

### Context

`RuntimeConfigurationBinding` may replace the currently published active configuration.

A runtime operation may span such a replacement.

Allowing individual resolution calls to observe the binding independently could produce configuration-version mixing within one operation.

### Decision

Runtime operations obtain a `RuntimeConfigurationContext` from the current `RuntimeConfigurationBinding`.

The context represents exactly one `ActiveConfiguration` snapshot for its lifetime.

All configuration-dependent resolution performed through one context uses that snapshot.

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

Replacing the binding with V2 does not change an existing V1 context.

### Consequences

Positive:

* deterministic configuration semantics within an operation;
* no configuration-version mixing;
* binding may remain a replaceable publication point;
* existing `ActiveConfiguration` instances remain coherent snapshots.

Negative:

* runtime operations need an explicit configuration context;
* context lifetime must eventually be integrated with the broader Runtime Context model.

---

## ADR-CONF-004

### Layered Runtime Resolution

**Status:** Accepted

### Context

The platform already contains both:

* `MetadataResolver`;
* `RuntimeResolver`.

The existing `RuntimeResolver` can access `MetadataRegistry` directly, bypassing the runtime configuration boundary.

Replacing both with one universal resolver would combine configuration resolution and runtime-object materialization responsibilities.

### Decision

Runtime resolution is layered.

```text
RuntimeResolver
        ↓
MetadataResolver
        ↓
RuntimeConfigurationContext
        ↓
ActiveConfiguration
```

`MetadataResolver` resolves configuration metadata.

`RuntimeResolver` transforms resolved metadata into runtime objects.

`RuntimeResolver` must not directly depend on `MetadataRegistry`.

### Consequences

Positive:

* clear separation between configuration resolution and runtime materialization;
* preservation of the existing `RuntimeResolver` responsibility;
* configuration-aware runtime resolution;
* no universal resolver abstraction.

Negative:

* runtime resolution gains one additional dependency layer;
* existing direct registry access must be refactored.

---

## ADR-CONF-005

### Published Configuration as Immutable Runtime State

**Status:** Accepted

### Context

`ActiveConfiguration` is represented as immutable configuration state, but its metadata registry may remain technically mutable.

Runtime consumers must not be able to mutate published configuration semantics.

### Decision

Metadata exposed by `ActiveConfiguration` is treated as immutable published runtime state.

The concrete implementation mechanism for registry immutability is deferred.

Possible mechanisms include:

* immutable registry;
* read-only registry view;
* immutable mapping;
* private published storage.

### Consequences

Positive:

* runtime consumers cannot alter active configuration semantics;
* configuration snapshots remain coherent;
* implementation remains free to choose the appropriate immutable representation.

Negative:

* the registry publication mechanism must be resolved during implementation;
* existing mutable registry APIs may require separation between construction and runtime access.

---

## ADR-CONF-006

### Runtime Consumers Must Not Bypass Configuration Resolution

**Status:** Accepted

### Context

The existing runtime path allows consumers such as `CatalogRuntime` to obtain metadata through `MetadataRegistry` without going through `RuntimeConfigurationBinding`.

This creates a second runtime configuration source.

### Decision

All runtime consumers must access configuration-defined semantics through the Phase 3 runtime resolution chain:

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
```

Direct consumer access to `MetadataRegistry` is prohibited.

### Consequences

Positive:

* one configuration consumption boundary;
* consistent configuration-version semantics;
* storage independence;
* easier future changes to metadata infrastructure.

Negative:

* existing Standard Configuration bootstrap/runtime paths must be migrated;
* direct registry-based tests must be reviewed and replaced where they represent runtime behavior.

---

# ADR Summary

| ADR          | Decision                                                          |
| ------------ | ----------------------------------------------------------------- |
| ADR-CONF-002 | Runtime configuration is owned by `RuntimeConfigurationBinding`   |
| ADR-CONF-003 | Runtime operations use a configuration snapshot context           |
| ADR-CONF-004 | Metadata and runtime-object resolution remain layered             |
| ADR-CONF-005 | Published configuration is immutable from the runtime perspective |
| ADR-CONF-006 | Runtime consumers must not bypass configuration resolution        |

## ADR-004 — RuntimeResolver Uses Explicit Runtime Configuration Context

**Status:** Accepted

**Phase:** Phase 3 — Runtime Configuration Consumption & Resolution

**Decision:** RuntimeResolver shall resolve runtime objects using an explicit RuntimeConfigurationContext supplied for each resolution operation and shall obtain metadata exclusively through MetadataResolver.

### Context

The initial runtime implementation introduced RuntimeResolver as a component
directly dependent on MetadataRegistry:

    RuntimeResolver
        ↓
    MetadataRegistry
        ↓
    Metadata

This model was sufficient for the early vertical slice, but it bypasses the
runtime configuration architecture established by Phase 2 and Phase 3.

In particular, direct MetadataRegistry dependency causes RuntimeResolver to
implicitly assume that the registry supplied to it represents the runtime
configuration against which an operation is executed.

Phase 3 established a different configuration consumption model:

    ActiveConfiguration
        ↓
    RuntimeConfigurationBinding
        ↓
    RuntimeConfigurationContext
        ↓
    Runtime Consumers

RuntimeConfigurationBinding participates in configuration publication and
lifecycle management. RuntimeResolver does not depend on the binding and
receives RuntimeConfigurationContext explicitly.

Phase 3 Step 3 further established MetadataResolver as the metadata resolution
boundary. MetadataResolver resolves metadata from an explicitly supplied
RuntimeConfigurationContext and does not retain or discover the current
configuration itself.

RuntimeResolver must therefore integrate with these boundaries without
reintroducing direct ownership or discovery of runtime configuration.

### Decision

RuntimeResolver shall:

1. depend on MetadataResolver rather than MetadataRegistry;
2. receive RuntimeConfigurationContext explicitly for each resolve operation;
3. remain stateless with respect to runtime configuration and retain only its
   MetadataResolver dependency;
4. never acquire configuration from RuntimeConfigurationBinding;
5. never retain ActiveConfiguration or RuntimeConfigurationContext as mutable
   current state;
6. obtain metadata exclusively through MetadataResolver;
7. remain responsible for converting supported metadata into executable runtime
   objects;
8. preserve existing runtime-object construction semantics.

The target contract is:

    RuntimeResolver
        │
        ├── MetadataResolver
        │
        └── RuntimeConfigurationContext
                    │
                    ↓
             ActiveConfiguration
                    │
                    ↓
             MetadataRegistry

Conceptually:

    resolver = RuntimeResolver(metadata_resolver)

    runtime_object = resolver.resolve(
        context,
        identifier,
    )

The RuntimeConfigurationContext is an operation-level input, not resolver
state.

### Responsibilities

RuntimeConfigurationBinding is responsible for determining which active
configuration is available to new runtime operations.

RuntimeConfigurationContext is responsible for representing the immutable
configuration snapshot against which a runtime operation executes.

MetadataResolver is responsible for resolving metadata from that snapshot.

RuntimeResolver is responsible for converting resolved metadata into the
appropriate executable runtime object.

Therefore:

    configuration selection
        ≠
    metadata resolution
        ≠
    runtime object resolution

### Dependency Boundary

The following dependency is explicitly allowed:

    RuntimeResolver
        → MetadataResolver

RuntimeConfigurationContext is an explicit operation-level input:

    RuntimeResolver.resolve(...)
        → RuntimeConfigurationContext

RuntimeConfigurationContext is not retained as resolver state.

RuntimeConfigurationContext is an explicit operation-level input to
RuntimeResolver.resolve(), not retained resolver state.

The following dependencies are explicitly prohibited:

    RuntimeResolver
        ✕→ MetadataRegistry
        ✕→ RuntimeConfigurationBinding
        ✕→ ConfigurationActivator
        ✕→ ConfigurationLoader

RuntimeResolver must not bypass MetadataResolver in order to access the
metadata registry directly.

### Context Semantics

Runtime resolution shall use the configuration represented by the explicitly
supplied RuntimeConfigurationContext.

For example:

    context_v1
        ↓
    resolve(context_v1, identifier)
        ↓
    runtime object based on configuration v1

A subsequent binding change:

    RuntimeConfigurationBinding
        ↓
    configuration v2

must not change the configuration represented by an already-created RuntimeConfigurationContext.

Likewise:

    resolve(context_v2, identifier)
        ↓
    runtime object based on configuration v2

The resolver therefore follows snapshot semantics rather than current-binding
semantics.

### Error Ownership

Metadata lookup errors remain owned by MetadataResolver.

If metadata is absent from the supplied configuration:

    MetadataRegistry
        ↓ KeyError
    MetadataResolver
        ↓
    MetadataResolutionError
        ↓
    RuntimeResolver

RuntimeResolver shall not replace or reinterpret MetadataResolutionError.

RuntimeResolver remains responsible for errors caused by unsupported metadata
types or unsupported runtime object mappings.

The existing unsupported-metadata behavior is therefore preserved:

    unsupported metadata type
        ↓
    TypeError

A future dedicated RuntimeResolutionError may be introduced if runtime
resolution grows beyond simple metadata-type dispatch, but such an error is
outside the scope of this step.

### Statelessness

RuntimeResolver shall not retain:

    _registry
    _binding
    _context
    _active_configuration

as runtime configuration state.

A RuntimeResolver instance may be reused for multiple contexts:

    resolver.resolve(context_v1, identifier)
    resolver.resolve(context_v2, identifier)

Each operation must use exactly the context supplied to that operation.

### Compatibility

This decision changes the RuntimeResolver constructor and resolve method
contract from:

    RuntimeResolver(registry)
    resolver.resolve(identifier)

to:

    RuntimeResolver(metadata_resolver)
    resolver.resolve(context, identifier)

Existing tests, vertical slices, and composition roots such as
StandardConfigurationBootstrap that construct RuntimeResolver directly must
therefore be migrated.

This migration is an intentional architectural change and is not considered
a compatibility-preserving refactoring.

### Consequences

#### Positive

- RuntimeResolver becomes independent from storage details.
- Runtime configuration selection is separated from runtime object resolution.
- MetadataResolver becomes the single metadata resolution boundary.
- Runtime operations obtain explicit configuration snapshots.
- Binding changes cannot silently alter an already-created context.
- RuntimeResolver becomes stateless and reusable.
- Future runtime consumers can follow the same context-based contract.

#### Negative

- Existing RuntimeResolver callers must be migrated.
- Standard bootstrap must be adapted to construct the new dependency graph.
- Existing vertical tests must explicitly create or obtain a runtime context.
- RuntimeResolver tests become slightly more elaborate because configuration
  context is now part of the operation contract.

### Scope

This ADR covers only the integration of RuntimeResolver with the Phase 3
configuration consumption model.

It does not introduce:

- new runtime object types;
- new metadata types;
- runtime caching;
- configuration lifecycle changes;
- concurrent configuration management;
- persistence changes;
- a generalized runtime factory framework.

### Quality Gate

Step 4 is complete only when P3-QG4 confirms:

- RuntimeResolver has no direct MetadataRegistry dependency;
- RuntimeResolver has no RuntimeConfigurationBinding dependency;
- RuntimeResolver receives RuntimeConfigurationContext explicitly;
- metadata resolution goes through MetadataResolver;
- snapshot semantics are preserved;
- unsupported metadata behavior remains correct;
- existing runtime object semantics remain correct;
- standard bootstrap and vertical consumers are migrated;
- public APIs are aligned;
- pytest, ruff, black and mypy pass.