# Phase 3 Documentation Alignment — Required Updates

**Status:** In Progress
**Scope:** Phase 3 documentation alignment beyond the implementation checkpoint
**Current implementation checkpoint:** Steps 1–2 complete; Steps 3–7 pending

## Status Legend

* `[x]` — aligned and complete
* `[~]` — partially aligned; implementation or broader documentation work remains
* `[ ]` — not yet aligned

## Current Phase 3 Implementation Documentation

The following Phase 3 implementation documents are aligned with the current
Step 1–2 implementation checkpoint:

* `[x]` `PHASE_3_IMPLEMENTATION_PLAN.md` — Steps 1–2 marked implemented; P3-QG1 and P3-QG2 closed.
* `[x]` `PHASE_3_RUNTIME_CONFIGURATION_CONSUMPTION.md` — implemented runtime configuration foundation documented; remaining target state explicitly identified.
* `[x]` `PHASE_3_CONFIGURATION_AND_RUNTIME_RESOLUTION_ADRS.md` — architectural decisions remain authoritative and are not being marked as implementation-complete.

The broader architecture-document updates listed below are intentionally not
part of the Step 1–2 implementation checkpoint. They should be completed as a
separate documentation-alignment activity so that implementation commits do
not mix unrelated architecture-wide documentation changes.

---

## 1. Configuration Runtime

**Status:** `[ ]`

Update:

`docs/architecture/configuration/CONFIGURATION_RUNTIME.md`

Add the Phase 3 runtime consumption chain:

```text
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
Runtime Objects
```

Clarify that `ConfigurationActivator` creates active configuration but does not own the currently published runtime configuration.

Clarify that `RuntimeConfigurationBinding` is the runtime publication boundary.

---

## 2. Runtime Context

**Status:** `[ ]`

Update:

`docs/architecture/runtime/RUNTIME_CONTEXT.md`

Add configuration snapshot semantics to the existing Runtime Context model.

The configuration portion of a Runtime Context shall represent:

* configuration identity;
* configuration version;
* access to one coherent active configuration snapshot.

The document should explicitly state:

> Every runtime operation that depends on configuration executes against one configuration-consistent runtime context.

Do not add security, session or transaction implementation details as part of Phase 3.

Those remain separate Runtime Context concerns.

---

## 3. Runtime Architecture

**Status:** `[ ]`

Update:

`docs/architecture/runtime/RUNTIME_ARCHITECTURE.md`

Clarify the dependency direction:

```text
Runtime Consumer
      ↓
Runtime Resolver
      ↓
Metadata Resolver
      ↓
Runtime Configuration Context
      ↓
Active Configuration
```

State explicitly that runtime consumers must not access configuration storage or `MetadataRegistry` directly.

The existing broader Runtime Context architecture remains authoritative; Phase 3 only defines its configuration-consumption portion.

---

## 4. Metadata Architecture

**Status:** `[ ]`

Update:

`docs/architecture/metadata/METADATA_ARCHITECTURE.md`

Clarify that metadata resolution performed by runtime consumers is configuration-aware.

The runtime does not resolve metadata from an arbitrary global registry.

Instead:

```text
Runtime Configuration Context
        ↓
Metadata Resolution
        ↓
Metadata
```

The metadata registry remains infrastructure behind the resolution boundary.

---

## 5. Configuration Lifecycle

**Status:** `[ ]`

Update:

`docs/architecture/configuration/CONFIGURATION_LIFECYCLE.md`

Clarify the boundary after activation:

```text
Validated Candidate
        ↓ activate
ActiveConfiguration
        ↓ publish
RuntimeConfigurationBinding
        ↓ acquire
RuntimeConfigurationContext
```

Activation itself does not execute runtime consumption.

---

## 6. Existing Phase 2 Runtime Consumption Document

**Status:** `[ ]`

Update:

`docs/implementation/PHASE_2_RUNTIME_CONFIGURATION_CONSUMPTION_AND_METADATA_RESOLUTION.md`

Change status to:

```text
Status: Historical / Superseded
Superseded by:
PHASE_3_ARCHITECTURAL_DEFINITION.md
```

Preserve the document as Phase 2 implementation history.

Do not delete it.

Its original v1 metadata-resolution contract remains useful for tracing the evolution of the implementation.

---

## 7. Existing Phase 2 Runtime Consumption Implementation Plan

**Status:** `[ ]`

Update:

`docs/implementation/PHASE_2_RUNTIME_CONFIGURATION_CONSUMPTION_AND_METADATA_RESOLUTION_IMPLEMENTATION_PLAN.md`

Change status to:

```text
Status: Historical / Completed
Superseded for further implementation by:
Phase 3 Implementation Plan
```

Do not extend this document with Phase 3 work.

Phase 3 implementation work must have its own implementation plan.

---

## 8. Architecture Overview

**Status:** `[ ]`

Update:

`docs/architecture/ARCHITECTURE_OVERVIEW.md`

Add the Phase 3 runtime configuration consumption relationship:

```text
Configuration Architecture
        │
        ▼
ActiveConfiguration
        │
        ▼
RuntimeConfigurationBinding
        │
        ▼
Runtime Configuration Context
        │
        ▼
Runtime Architecture
```

The overview should emphasize that configuration does not directly execute runtime behavior.

Configuration provides runtime-consumable semantics through an explicit boundary.

---

## 9. Glossary

**Status:** `[ ]`

Add the following terms to the architecture glossary.

### Runtime Configuration Binding

The runtime publication and access boundary for the currently active configuration.

### Runtime Configuration Context

A runtime-scoped configuration snapshot representing exactly one `ActiveConfiguration` version for consistent configuration-dependent resolution.

### Configuration Consumption Boundary

The architectural boundary through which runtime consumers access configuration-defined semantics without depending on configuration lifecycle or physical storage.

### Metadata Resolution

The process of resolving a logical metadata identity into its metadata definition within a specific runtime configuration context.

### Runtime Object Resolution

The process of transforming configuration-defined metadata into a runtime-consumable runtime object.

### Configuration Snapshot

A coherent, version-specific representation of active configuration state used by a runtime context.

---

## 10. Documentation Dependency Direction

**Status:** `[ ]`

After these updates, the documentation should express the following dependency direction consistently:

```text
Configuration Lifecycle
        ↓
Active Configuration
        ↓
Runtime Configuration Binding
        ↓
Runtime Configuration Context
        ↓
Metadata Resolution
        ↓
Runtime Object Resolution
        ↓
Runtime Consumers
```

No runtime architecture document should imply that runtime consumers directly obtain configuration from loaders, activators, registries or physical storage.
