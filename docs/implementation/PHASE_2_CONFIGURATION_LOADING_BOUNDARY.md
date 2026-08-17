# Phase 2 — Configuration Loading Boundary

**Status:** Design  
**Version:** 1.0  
**Phase:** Phase 2 — Metadata → Runtime  
**Step:** Step 3 — Configuration Loading Boundary

---

## 1. Purpose

This document defines the architectural boundary responsible for transforming
a set of configuration definitions into an isolated `ConfigurationCandidate`.

The loading boundary connects the existing metadata pipeline with the
Configuration Lifecycle Model:

```text
Definitions
    ↓
MetadataCompiler
    ↓
MetadataRegistry
    ↓
ConfigurationCandidate

2. Architectural Principle

The fundamental rule of the loading boundary is:

Configuration Loading is a construction boundary, not a lifecycle boundary.

Therefore:

ConfigurationLoader
    ↓
ConfigurationCandidate(state=LOADED)

is valid, while:

ConfigurationLoader
    ↓
READY
    ↓
ACTIVE

is outside the responsibility of the loader.

Lifecycle transitions are owned by the future Configuration Lifecycle
orchestration layer.

3. Scope
In scope

Step 3 defines:

ConfigurationLoader;
loader input contract;
metadata compilation during loading;
candidate-local MetadataRegistry construction;
ConfigurationCandidate construction;
loading atomicity;
registry isolation;
loading error boundaries;
dependency direction between configuration and metadata layers.
Out of scope

Step 3 does not define:

configuration activation;
runtime creation;
runtime replacement;
lifecycle orchestration;
persistent configuration storage;
filesystem configuration sources;
database configuration sources;
JSON/YAML configuration formats;
Standard Configuration-specific loading logic;
configuration editing;
configuration migration;
configuration version upgrade.
4. Loading Pipeline

The target loading pipeline is:

Configuration Definitions
        │
        ▼
ConfigurationLoader
        │
        ▼
MetadataCompiler
        │
        ▼
Compiled Metadata
        │
        ▼
Candidate-local MetadataRegistry
        │
        ▼
ConfigurationCandidate
        │
        ▼
LOADED

The candidate is created only after the complete input set has been
successfully processed.

5. Configuration Candidate

The output of loading is:

ConfigurationCandidate
├── identity
├── version
├── state = LOADED
└── metadata_registry

The candidate does not contain a reference to the original source.

The candidate represents the loaded configuration state, not the source
from which that state was obtained.

6. Loader Contract

The conceptual loader contract is:

candidate = loader.load(
    definitions,
    identity=identity,
    version=version,
)

The result is:

ConfigurationCandidate

with:

candidate.state == ConfigurationLifecycleState.LOADED

The loader must not return:

MetadataRegistry;
individual Metadata;
runtime objects;
runtime resolvers;
lifecycle states other than LOADED.
7. Loader Dependencies

The loader depends on the existing metadata compiler.

The dependency is injected rather than constructed implicitly:

ConfigurationLoader
        │
        └── MetadataCompiler

This keeps the loader independent of compiler implementation details and
makes the boundary testable.

The loader must not directly depend on:

RuntimeResolver
CatalogRuntime
Standard Configuration
Storage
Posting
Reporting
8. Candidate-local Registry

Every loading operation creates a new MetadataRegistry.

Conceptually:

load(configuration A)
        ↓
Registry A
        ↓
Candidate A

and:

load(configuration B)
        ↓
Registry B
        ↓
Candidate B

The registries must not be shared between candidates unless such sharing is
explicitly introduced by a future architecture decision.

The loader must therefore not use a global metadata registry.

9. Registry Population

For each supplied definition:

Definition
    ↓
MetadataCompiler
    ↓
Metadata
    ↓
MetadataRegistry.register()

The existing MetadataCompiler remains responsible for compilation.

The existing MetadataRegistry remains responsible for metadata identity
registration and duplicate detection.

The loader orchestrates these existing components; it does not duplicate
their responsibilities.

10. Atomic Loading

Loading is atomic from the perspective of the resulting candidate.

If any definition fails compilation or registration:

Definitions
    ↓
partial processing
    ↓
error

the loader must not return a partially populated candidate.

The expected result is:

LOAD FAILURE
    ↓
no ConfigurationCandidate

A candidate is created only after all supplied definitions have been
successfully compiled and registered.

11. Duplicate Metadata Identity

Duplicate metadata identity is detected by the existing
MetadataRegistry.register() contract.

The loader must not implement a second duplicate-detection mechanism.

The responsibility chain is:

ConfigurationLoader
    ↓
MetadataRegistry.register()
    ↓
duplicate detection

If registration fails, loading fails.

The exact configuration-level error mapping is implementation-defined and
must preserve the existing platform error architecture.

12. Error Boundary

The loader may encounter errors originating from:

Definition validation
Metadata compilation
Metadata registration

The loader must not silently suppress these errors.

The initial implementation should preserve the existing exception hierarchy
unless a dedicated configuration loading error is proven necessary.

A new error type must not be introduced merely for symmetry.

13. Source Boundary

A concrete configuration source is intentionally not introduced in Step 3.

The future architecture may contain:

Configuration Source
        ↓
Definitions
        ↓
ConfigurationLoader

Possible sources may eventually include:

package resources;
filesystem;
database;
remote configuration service;
in-memory definitions.

However, no concrete source abstraction is required for Step 3.

The first implementation uses already available Definition objects directly.

14. Configuration Descriptor

A future ConfigurationDescriptor may represent:

identity
version
source reference

However, its implementation is deferred.

Step 3 does not introduce a descriptor unless the concrete loader contract
requires one.

The distinction remains:

Descriptor
    = what configuration should be loaded


Candidate
    = configuration that has been loaded
15. Standard Configuration

Standard Configuration must not receive special treatment inside
ConfigurationLoader.

The intended future architecture is:

Standard Definitions
        ↓
Configuration Loading
        ↓
ConfigurationCandidate

Standard Configuration is therefore treated as a configuration source/content
set rather than as a special runtime bootstrap path.

Existing Standard Bootstrap implementation is not replaced in Step 3.

Its migration to the new loading boundary is a later integration task.

16. Dependency Direction

The intended dependency direction is:

configuration
      │
      ├──────────→ metadata
      │
      └──────────→ definitions

The following dependencies are prohibited:

metadata ───────→ configuration
definitions ────→ configuration
runtime ────────→ configuration

In particular:

ConfigurationLoader
        X
        ↓
RuntimeResolver

is prohibited.

17. Lifecycle Boundary

Loading produces exactly one lifecycle state:

LOADED

The lifecycle remains:

             Configuration Loading
                     │
                     ▼
                   LOADED
                     │
                     ▼
                 VALIDATED
                     │
                     ▼
                  PREPARED
                     │
                     ▼
                    READY
                     │
                     ▼
                   ACTIVE

Step 3 implements only:

Definitions → LOADED

The transitions after LOADED belong to the Configuration Lifecycle
orchestration layer.

18. Architectural Invariants

The following invariants apply to Step 3.

Invariant 1 — Complete loading

A candidate exists only after all supplied definitions have been successfully
compiled and registered.

Invariant 2 — Candidate isolation

Each loading operation owns its own metadata registry.

Invariant 3 — No partial candidate

Failed loading does not produce a partially populated candidate.

Invariant 4 — No runtime dependency

Configuration loading does not create or resolve runtime objects.

Invariant 5 — No activation

Configuration loading never activates a candidate.

Invariant 6 — Compiler reuse

The existing MetadataCompiler remains the only compilation mechanism.

Invariant 7 — Registry reuse

The existing MetadataRegistry remains the metadata registration mechanism.

Invariant 8 — Standard independence

The generic loader contains no Standard Configuration-specific logic.

19. Target Architecture

After Step 3 the configuration layer should conceptually look like:

                    Definitions
                         │
                         ▼
              ┌─────────────────────┐
              │ ConfigurationLoader │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ MetadataCompiler    │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ MetadataRegistry    │
              │ candidate-local     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Configuration       │
              │ Candidate           │
              │                     │
              │ state = LOADED      │
              └─────────────────────┘
20. Design Decision

Step 3 adopts the following architectural decision:

ConfigurationLoader is a construction service that compiles a complete
set of definitions into a new candidate-local metadata registry and returns
a ConfigurationCandidate in the LOADED state.

No lifecycle transition beyond LOADED occurs during loading.