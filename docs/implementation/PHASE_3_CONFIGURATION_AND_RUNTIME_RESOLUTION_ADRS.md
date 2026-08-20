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
