# Phase 3 Implementation Plan

**Phase:** Phase 3 — Runtime Configuration Consumption & Resolution
**Status:** In Progress
**Baseline:** `95af009`
**Predecessor:** Phase 2 — Metadata Lifecycle / Configuration Loading
**Architecture:** Phase 3 Architectural Definition v1.0

---

## 1. Purpose

This document defines the implementation plan for Phase 3.

Phase 3 extends the completed Phase 2 configuration lifecycle into a
version-consistent runtime configuration consumption and resolution model.

The target runtime flow is:

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

Phase 3 implementation must preserve the architectural boundaries established
by the Phase 3 Architectural Definition.

### Current Implementation Position

Phase 3 implementation is complete through Step 2.

Implemented:

* Step 1 — RuntimeConfigurationContext;
* Step 2 — Configuration Ownership Cleanup.

Quality gates closed:

* P3-QG1 — Context Contract: **CLOSED**;
* P3-QG2 — Ownership: **CLOSED**.
* P3-QG3 — Metadata Resolver Context Boundary: **CLOSED**.

Validation at the Step 2 checkpoint:

* `pytest`: **177 passed**;
* `ruff check .`: **PASS**;
* `black --check .`: **PASS**;
* `mypy src`: **PASS**.

## 2. Implementation Objectives

Phase 3 implementation shall establish:

explicit runtime configuration snapshot semantics;
RuntimeConfigurationContext;
single runtime ownership through RuntimeConfigurationBinding;
removal of competing current-configuration ownership from
ConfigurationActivator;
configuration-aware metadata resolution;
integration of RuntimeResolver with MetadataResolver;
elimination of direct runtime bypasses to MetadataRegistry;
immutable published configuration semantics;
configuration-consistent Standard Configuration runtime flow;
regression coverage for all Phase 3 architectural invariants.
## 3. Implementation Principles
### 3.1 Preserve Phase 2 Lifecycle


Phase 3 must not redesign:

Candidate
    ↓
Validated Candidate
    ↓
ActiveConfiguration

The existing Phase 2 lifecycle remains authoritative.

### 3.2 One Runtime Owner


The runtime publication owner is:

RuntimeConfigurationBinding

ConfigurationActivator must not maintain a competing current configuration.

### 3.3 Snapshot-Based Runtime Consumption


Runtime consumers do not resolve configuration directly from the mutable
publication point.

Instead:

RuntimeConfigurationBinding
        ↓ acquire
RuntimeConfigurationContext
        ↓
ActiveConfiguration snapshot
### 3.4 Layered Resolution


Metadata resolution and runtime object resolution remain separate:

MetadataResolver
    ↓
metadata


RuntimeResolver
    ↓
runtime object
### 3.5 No Runtime Registry Bypass


Runtime consumers and RuntimeResolver must not directly access
MetadataRegistry.

The registry remains an infrastructure implementation detail.

## 4. Implementation Sequence

Phase 3 is implemented in the following order.

Step 1
RuntimeConfigurationContext
        ↓
Step 2
Configuration ownership cleanup
        ↓
Step 3
MetadataResolver
        ↓
Step 4
RuntimeResolver integration
        ↓
Step 5
Standard Configuration vertical slice
        ↓
Step 6
Published configuration immutability
        ↓
Step 7
Phase 3 audit and quality gate

The sequence is intentional.

Runtime context must exist before runtime resolution is refactored to consume
configuration through it.

## 5. Step 1 — RuntimeConfigurationContext

**Status:** Implemented

**Quality Gate:** P3-QG1 — CLOSED

Objective

Introduce an explicit runtime configuration snapshot.

Target model
RuntimeConfigurationBinding
        │
        │ acquire()
        ▼
RuntimeConfigurationContext
        │
        ▼
ActiveConfiguration
Responsibilities

RuntimeConfigurationContext shall:

represent one active configuration snapshot;
expose configuration identity;
expose configuration version;
provide access to the captured ActiveConfiguration;
remain independent from subsequent changes to the binding.
Non-responsibilities

It shall not:

activate configuration;
validate candidates;
replace the active configuration;
load configuration;
resolve runtime objects;
access physical storage directly.
Required tests

At minimum:

context can be acquired from binding;
context contains the currently published configuration;
context exposes configuration identity;
context exposes configuration version;
replacing the binding does not change an existing context;
a newly acquired context observes the newly published configuration;
context cannot be used to mutate the active configuration.
## 6. Step 2 — Configuration Ownership Cleanup

**Status:** Implemented

**Quality Gate:** P3-QG2 — CLOSED

Objective

Eliminate duplicate current-configuration ownership.

Required result
ConfigurationActivator
    → creates ActiveConfiguration


RuntimeConfigurationBinding
    → owns current published ActiveConfiguration
Required changes

Remove any activator state equivalent to:

_current
current()

when that state represents the currently published runtime configuration.

Tests

Update existing activator tests so that they verify activation rather than
runtime ownership.

Add tests proving that:

activation creates an ActiveConfiguration;
binding owns publication;
activator has no competing runtime current state.
## 7. Step 3 — MetadataResolver

**Status:** Implemented

**Quality Gate:** P3-QG3 — CLOSED

Objective

Introduce an explicit configuration-aware metadata resolution layer.

Target contract
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
Metadata
Responsibilities

MetadataResolver shall:

accept a runtime configuration context;
resolve metadata by logical identity;
resolve only within the context's configuration snapshot;
raise explicit errors when metadata cannot be resolved.
Prohibited behavior

It must not:

select an arbitrary active configuration;
access a global current configuration;
silently fall back to another configuration;
load configuration;
activate configuration.
Tests

At minimum:

metadata is resolved from the supplied context;
resolution uses the context's configuration version;
missing metadata produces an explicit error;
changing the binding does not affect resolution through an existing context.
## 8. Step 4 — RuntimeResolver Integration

**Status:** Completed

**Quality Gate:** P3-QG4 — Closed

Step 4 integrates RuntimeResolver with the Phase 3 runtime configuration
consumption model.

The legacy RuntimeResolver depended directly on MetadataRegistry:

    RuntimeResolver
        ↓
    MetadataRegistry

This bypassed RuntimeConfigurationContext and the MetadataResolver boundary
established by Step 3.

Step 4 migrates RuntimeResolver to the Phase 3 configuration consumption
model:

    RuntimeResolver
        ↓
    MetadataResolver
        ↓
    RuntimeConfigurationContext
        ↓
    ActiveConfiguration
        ↓
    MetadataRegistry

The migration is divided into implementation substeps so that the runtime
resolution boundary can be introduced without weakening the existing runtime
contracts.

### 8.1 Step 4A — RuntimeResolver Contract Migration

**Status:** Implemented

**Quality Gate:** P3-QG4A — CLOSED

#### Objective

Replace the legacy MetadataRegistry-oriented RuntimeResolver contract with an
explicit MetadataResolver and RuntimeConfigurationContext based contract.

The RuntimeResolver constructor is now:

    resolver = RuntimeResolver(metadata_resolver)

Runtime resolution is now performed as:

    runtime_object = resolver.resolve(
        context,
        identifier,
    )

RuntimeConfigurationContext is supplied explicitly for every resolution
operation.

#### Established Contract

RuntimeResolver:

- depends on MetadataResolver;
- receives RuntimeConfigurationContext explicitly through `resolve()`;
- does not acquire configuration from RuntimeConfigurationBinding;
- does not retain RuntimeConfigurationContext as runtime state;
- does not retain ActiveConfiguration;
- does not retain MetadataRegistry;
- delegates metadata lookup exclusively to MetadataResolver;
- remains responsible for converting supported metadata types into runtime
  objects.

The resolver is therefore reusable across multiple runtime configuration
contexts:

    resolver.resolve(context_v1, identifier)
    resolver.resolve(context_v2, identifier)

The selected context determines the metadata used for the current resolution
operation.

#### Implementation

RuntimeResolver now follows:

    def __init__(self, metadata_resolver: MetadataResolver) -> None:
        ...

    def resolve(
        self,
        context: RuntimeConfigurationContext,
        identifier: Identifier,
    ) -> CatalogRuntime:
        ...

Metadata lookup is performed through:

    metadata = self._metadata_resolver.resolve(
        context,
        identifier,
    )

RuntimeResolver does not access MetadataRegistry directly.

#### Error Contract

Metadata lookup failures remain owned by MetadataResolver.

`MetadataResolutionError` is therefore propagated without introducing a
RuntimeResolver-specific metadata lookup exception.

Unsupported metadata types continue to produce the existing `TypeError`
behavior.

#### Tests

RuntimeResolver tests were migrated to the explicit context contract.

The test suite covers:

- resolution of registered catalog metadata;
- resolution through an explicitly supplied runtime context;
- resolution of multiple metadata objects;
- resolution using different configuration contexts;
- absence of stale configuration state;
- propagation of MetadataResolutionError;
- rejection of unsupported metadata types;
- non-mutation of metadata/configuration state.

### 8.2 Step 4B — Standard Configuration Bootstrap Migration

**Status:** Implemented

**Quality Gate:** P3-QG4B — CLOSED

#### Objective

Migrate StandardConfigurationBootstrap from the legacy MetadataRegistry-oriented
composition model to the Phase 3 runtime configuration model.

The bootstrap is a composition root and must construct the runtime dependency
graph without transferring configuration ownership to RuntimeResolver.

The resulting composition is:

    ActiveConfiguration
        ↓
    RuntimeConfigurationContext
        ↓
    MetadataResolver
        ↓
    RuntimeResolver

The bootstrap returns the runtime configuration context together with the
RuntimeResolver:

    context, resolver = StandardConfigurationBootstrap().initialize()

The returned RuntimeConfigurationContext contains the ActiveConfiguration
whose MetadataRegistry contains the compiled Standard Configuration metadata.

RuntimeResolver remains unaware of how the context was created.

#### Bootstrap Responsibilities

StandardConfigurationBootstrap is responsible for:

1. compiling Standard Configuration definitions;
2. registering the resulting metadata;
3. constructing the ActiveConfiguration;
4. constructing the RuntimeConfigurationContext;
5. constructing MetadataResolver;
6. constructing RuntimeResolver;
7. returning the runtime consumption components required by callers.

The bootstrap must not:

- make RuntimeResolver responsible for configuration acquisition;
- introduce a second active-configuration state;
- make RuntimeResolver depend on MetadataRegistry;
- make RuntimeResolver depend on RuntimeConfigurationBinding.

#### Public Contract

The Standard Configuration bootstrap contract is:

    context, resolver = StandardConfigurationBootstrap().initialize()

where:

- `context` is a `RuntimeConfigurationContext`;
- `resolver` is a `RuntimeResolver`.

Standard Configuration callers resolve runtime objects explicitly through the
returned context:

    runtime = resolver.resolve(context, identifier)

#### Tests

Standard Configuration tests verify:

- bootstrap initialization contract;
- creation of RuntimeConfigurationContext;
- creation of RuntimeResolver;
- registration of all Standard Configuration catalogs;
- metadata correspondence with Standard Configuration definitions;
- deterministic bootstrap behavior;
- successful runtime resolution through the explicit context.

### 8.3 Step 4C — Vertical Slice Migration

**Status:** Implemented

**Quality Gate:** P3-QG4C — CLOSED

#### Objective

Migrate existing Phase 1 and Phase 2 vertical slices from the legacy:

    RuntimeResolver(registry)

contract to the explicit Phase 3 context-based contract.

The vertical slices now construct:

    ActiveConfiguration
        ↓
    RuntimeConfigurationContext
        ↓
    MetadataResolver
        ↓
    RuntimeResolver

and perform runtime resolution through:

    resolver.resolve(context, identifier)

#### Requirements

The vertical slices must continue to verify the existing runtime behavior while
also exercising the Phase 3 configuration consumption boundary.

Phase 1 verifies:

    Definition
        ↓
    Validation
        ↓
    Compilation
        ↓
    Registration
        ↓
    ActiveConfiguration
        ↓
    RuntimeConfigurationContext
        ↓
    MetadataResolver
        ↓
    RuntimeResolver
        ↓
    CatalogRuntime

Phase 2 verifies the same runtime resolution boundary using the metadata model
introduced by Phase 2.

No legacy direct Registry → RuntimeResolver path remains in the vertical
slices.

### 8.4 Public API Alignment

**Status:** Implemented

**Quality Gate:** P3-QG4D — CLOSED

RuntimeResolver public usage has been aligned with the Phase 3 contract.

The public API exposes the resolver without exposing or requiring a
MetadataRegistry dependency.

No unrelated public API changes are introduced by Step 4.

### 8.5 Step 4 Validation

The completed Step 4A–4C implementation has been validated with:

    pytest
    ruff check .
    black --check .
    mypy src

Current validation result:

- `pytest`: **177 passed**
- `ruff check .`: **PASS**
- `black --check .`: **PASS**
- `mypy src`: **PASS**

The complete test suite remains green.

### P3-QG4 — Runtime Resolver Boundary

**Status:** Closed

P3-QG4 closes only when all Step 4 architectural requirements are satisfied
and the complete validation suite remains green.

The following invariants must hold:

- RuntimeResolver has no direct MetadataRegistry dependency;
- RuntimeResolver depends on MetadataResolver;
- RuntimeResolver receives RuntimeConfigurationContext explicitly;
- RuntimeResolver has no RuntimeConfigurationBinding dependency;
- RuntimeResolver has no ConfigurationActivator dependency;
- RuntimeResolver has no ConfigurationLoader dependency;
- RuntimeResolver does not retain ActiveConfiguration as state;
- RuntimeResolver does not retain RuntimeConfigurationContext as state;
- RuntimeResolver does not retain MetadataRegistry as state;
- metadata lookup goes exclusively through MetadataResolver;
- MetadataResolutionError remains owned by MetadataResolver;
- unsupported metadata behavior remains unchanged;
- runtime object construction behavior remains unchanged;
- Standard Configuration bootstrap uses the Phase 3 runtime configuration
  model;
- Phase 1 and Phase 2 vertical slices use the explicit context contract;
- public API tests are aligned;
- `pytest` passes;
- `ruff check .` passes;
- `black --check .` passes;
- `mypy src` passes.

P3-QG4 is closed. All RuntimeResolver boundary requirements are satisfied,
the legacy MetadataRegistry-oriented resolution contract has been removed,
and the complete validation suite passes.

### 8.6 Expected Dependency Graph

After the completed Step 4A–4C migration:

    ActiveConfiguration
            │
            ▼
    RuntimeConfigurationContext
            │
            ├──────────────────────┐
            ▼                      │
    MetadataResolver               │
            │                      │
            │ metadata             │
            ▼                      │
    RuntimeResolver ◄──────────────┘
            │
            ▼
      CatalogRuntime

Configuration publication remains outside RuntimeResolver.

Where a runtime component obtains its context through the configuration
lifecycle, the lifecycle remains responsible for publication and ownership:

    ConfigurationLoader
            ↓
    ConfigurationActivator
            ↓
    RuntimeConfigurationBinding
            ↓
    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Runtime Object

RuntimeResolver itself does not depend on the binding and does not discover
the current configuration.

### 8.7 Architectural Boundary Established by Step 4

Step 4 establishes a strict separation between configuration consumption and
runtime object construction.

MetadataResolver owns:

- metadata lookup;
- metadata resolution errors;
- access to metadata within the supplied runtime context.

RuntimeResolver owns:

- runtime object resolution;
- supported metadata type checks;
- construction of executable runtime objects.

RuntimeConfigurationContext owns:

- the immutable runtime configuration snapshot supplied to a resolution
  operation.

RuntimeConfigurationBinding owns:

- publication and replacement of the current runtime configuration for
  lifecycle-aware consumers.

No runtime resolution component bypasses these boundaries to access the
MetadataRegistry directly.

### Exit State

When P3-QG4 closes, the runtime resolution path shall be:

    Configuration Definition
        ↓
    Metadata
        ↓
    ActiveConfiguration
        ↓
    RuntimeConfigurationContext
        ↓
    MetadataResolver
        ↓
    RuntimeResolver
        ↓
    Runtime Object

The runtime layer therefore consumes configuration explicitly and does not
discover configuration through storage, registry ownership, or binding
dependencies.

The legacy:

    RuntimeResolver(MetadataRegistry)
    RuntimeResolver.resolve(identifier)

contract is removed from the architecture.

The Phase 3 runtime consumption model becomes the only supported runtime
resolution path.

## 9. Step 5 — Standard Configuration Vertical Slice
Objective

Demonstrate the complete Phase 3 architecture through an existing Standard
Configuration runtime object.

Required flow
Standard Definition
        ↓
Compiler
        ↓
Candidate
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
Acceptance criteria

The vertical slice demonstrates that:

Standard Configuration can become active;
runtime acquires a configuration context;
metadata is resolved through that context;
runtime object resolution uses the resolved metadata;
no runtime consumer directly accesses MetadataRegistry;
configuration replacement preserves existing context consistency.
## 10. Step 6 — Published Configuration Immutability
Objective

Ensure runtime consumers cannot mutate published configuration semantics.

Architectural requirement

Published metadata is immutable from the runtime consumer's perspective.

The exact mechanism remains an implementation decision.

Possible mechanisms:

immutable registry;
read-only view;
immutable mapping;
private publication storage.
Tests

Verify that:

runtime consumers cannot mutate published metadata;
existing contexts remain coherent;
configuration replacement creates a new published state rather than mutating
the previous snapshot.
## 11. Step 7 — Phase 3 Audit

The final audit shall verify:

Architecture
ownership is unambiguous;
context snapshot semantics are correct;
resolution layers are separated;
registry bypasses are removed;
published state is immutable.
Code
pytest
ruff
black
mypy
Documentation

The implementation must match:

PHASE_3_ARCHITECTURAL_DEFINITION.md;
Phase 3 ADRs;
updated Configuration Architecture;
updated Runtime Architecture;
updated Metadata Architecture.
## 12. Quality Gates
Gate P3-QG1 — Context Contract

Required before Step 2.

Criteria:

context exists;
snapshot semantics work;
tests pass.
Gate P3-QG2 — Ownership

Required before Step 3.

Criteria:

activator no longer owns current runtime configuration;
binding is the sole publication owner;
tests pass.
Gate P3-QG3 — Metadata Resolution

Required before Step 4.

Criteria:

metadata resolver exists;
resolution is context-bound;
explicit errors exist;
tests pass.
Gate P3-QG4 — Runtime Resolution

Required before Step 5.

Criteria:

runtime resolver uses metadata resolver;
direct registry bypass is removed;
tests pass.
Gate P3-QG5 — Vertical Slice

Required before Step 6.

Criteria:

Standard Configuration reaches runtime object resolution;
full configuration-aware path is operational;
regression suite passes.
Gate P3-QG6 — Publication Semantics

Required before final audit.

Criteria:

published state is immutable to runtime consumers;
snapshot isolation is verified.
## 13. Review Gates
P3-RG1 — Runtime Context Review

Review:

context ownership;
snapshot semantics;
lifetime;
API minimality.
P3-RG2 — Resolution Boundary Review

Review:

MetadataResolver responsibility;
RuntimeResolver responsibility;
registry isolation;
dependency direction.
P3-RG3 — Vertical Slice Review

Review:

Standard Configuration integration;
end-to-end runtime flow;
architectural bypasses.
P3-RG4 — Final Architectural Review

Review all Phase 3 invariants:

P3-I1  Single Runtime Ownership
P3-I2  Activation Isolation
P3-I3  Snapshot Consistency
P3-I4  Resolution Consistency
P3-I5  Version Isolation
P3-I6  Consumer Isolation
P3-I7  Storage Independence
P3-I8  Layered Resolution
P3-I9  Lifecycle Isolation
P3-I10 Published Snapshot Semantics
P3-I11 Deterministic Resolution
P3-I12 Explicit Failure
## 14. Testing Strategy

Testing shall be layered.

Unit Tests

Test:

context;
binding;
activator;
metadata resolver;
runtime resolver.
Integration Tests

Test:

ActiveConfiguration
    ↓
Binding
    ↓
Context
    ↓
MetadataResolver
    ↓
RuntimeResolver
Vertical Slice Tests

Test Standard Configuration runtime resolution.

Regression Tests

The complete existing suite must remain green.

No Phase 3 implementation may weaken existing Phase 1 or Phase 2 contracts.

## 15. Expected Module Evolution

The exact file structure shall be determined from the existing repository before
implementation.

The expected conceptual modules are:

configuration/
    identity.py
    lifecycle.py
    candidate.py
    loader.py
    runtime_binding.py
    context.py


runtime/
    resolver.py
    ...


metadata/
    resolver.py
    ...

Existing modules should be reused where their current responsibility already
matches the Phase 3 contract.

New modules must not be introduced merely to rename existing responsibilities.

## 16. Compatibility Requirements

Phase 3 must preserve:

existing identifiers;
ActiveConfiguration;
existing candidate lifecycle;
existing metadata definitions;
existing compiler behavior;
existing runtime object contracts;
Standard Configuration bootstrap semantics.

Breaking changes are permitted only where they are required to enforce the
Phase 3 architectural boundary.

## 17. Documentation Requirements

During implementation:

implementation decisions must remain consistent with the Phase 3 ADRs;
implementation-specific details must not be promoted to architecture without
architectural review;
Phase 2 documents must remain historical rather than being repurposed.

At completion:

implementation documentation reflects the final code;
architecture documentation remains implementation-independent;
ADRs record all architectural decisions that changed during implementation.
## 18. Completion Definition

Phase 3 is complete when:

RuntimeConfigurationContext exists;
binding snapshot semantics are implemented;
activator has no competing runtime ownership;
MetadataResolver is configuration-aware;
RuntimeResolver uses the configuration-aware resolution path;
direct runtime registry bypasses are removed;
Standard Configuration vertical slice passes;
published configuration is immutable from runtime consumers;
all Phase 3 tests pass;
ruff, black, and mypy pass;
all Phase 3 architectural invariants pass;
Phase 3 Architectural Review Gate is closed.
## 19. Final Target Architecture
                    Phase 2
                      │
                      ▼
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

The central invariant is:

Runtime consumers resolve configuration through a single, version-consistent
runtime configuration context and never bypass the configuration consumption
boundary.