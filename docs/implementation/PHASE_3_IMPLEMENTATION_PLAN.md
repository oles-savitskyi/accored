# Phase 3 Implementation Plan

**Phase:** Phase 3 — Runtime Configuration Consumption & Resolution

**Status:** Implementation Complete

**Baseline:** `95af009`

**Current Implementation:** Steps 1–7 implemented; final audit completed

**Predecessor:** Phase 2 — Metadata Lifecycle / Configuration Loading

**Architecture:** Phase 3 Architectural Definition v1.0

---

## 1. Purpose

This document defines the implementation plan and final implementation state for
Phase 3.

Phase 3 extends the Phase 2 configuration lifecycle into a
version-consistent runtime configuration consumption and resolution model.

The completed runtime configuration flow is:

```text
Configuration Definition
        ↓
Metadata Compilation
        ↓
ConfigurationCandidate
        ↓
Validation
        ↓
ConfigurationActivator
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

Published metadata is exposed to runtime consumers through an immutable
publication boundary:

MetadataRegistry
        ↓ publish()
PublishedMetadataView
        ↓
ActiveConfiguration
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver

Phase 3 implementation preserves the architectural boundaries established by
the Phase 3 Architectural Definition and the subsequent Step 6 published
metadata design.

Current Implementation Position

Phase 3 implementation is complete through Step 7.

Implemented:

Step 1 — RuntimeConfigurationContext;
Step 2 — Configuration Ownership Cleanup;
Step 3 — MetadataResolver Context Boundary;
Step 4 — RuntimeResolver Integration;
Step 5 — Standard Configuration Vertical Slice;
Step 6 — Published Configuration Immutability;
Step 7 — Final Phase 3 Architectural Audit.

Quality gates:

P3-QG1 — Context Contract: CLOSED;
P3-QG2 — Ownership: CLOSED;
P3-QG3 — Metadata Resolver Context Boundary: CLOSED;
P3-QG4 — Runtime Resolver Boundary: CLOSED;
P3-QG5 — Standard Configuration Vertical Slice: CLOSED;
P3-QG6 — Published Configuration Immutability: CLOSED;
P3-QG7 — Final Phase 3 Architectural Audit: CLOSED.

Final validation:

pytest: 188 passed;
ruff check .: PASS;
black --check .: PASS;
mypy src: PASS.

The final Phase 3 audit also verified that:

ActiveConfiguration is created only by ConfigurationActivator;
runtime consumers do not access MetadataRegistry directly;
PublishedMetadataView forms the read-only publication boundary;
RuntimeConfigurationContext preserves configuration snapshot semantics;
MetadataResolver resolves metadata exclusively from the supplied runtime
context;
RuntimeResolver does not discover or acquire configuration implicitly;
Standard Configuration follows the canonical Phase 3 lifecycle;
configuration replacement preserves existing runtime contexts;
no parallel production configuration lifecycle remains.
Final Architectural State

The canonical Phase 3 composition is:

Standard Configuration Definition
        ↓
MetadataCompiler
        ↓
ConfigurationLoader
        ↓
ConfigurationCandidate
        ↓
ConfigurationValidator
        ↓
ConfigurationActivator
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

The configuration lifecycle, publication boundary, runtime context, metadata
resolution and runtime object resolution are separate but composable
responsibilities.

Standard Configuration provides the reference end-to-end implementation of
this architecture.

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

#### P3-QG4 — Runtime Resolver Boundary

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

#### Exit State

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

Step 5 establishes the first complete end-to-end runtime path through the
Phase 3 configuration architecture using the existing Standard Configuration.

The purpose of this step is not to introduce new runtime infrastructure, but
to demonstrate that the configuration lifecycle established in Phase 2 and
the runtime resolution boundaries established in Steps 3 and 4 operate
together as one coherent architecture.

The vertical slice shall demonstrate that a Standard Configuration definition
can be transformed into an active runtime configuration and subsequently
consumed by runtime resolution through an explicit
RuntimeConfigurationContext.

The slice shall therefore connect:

Standard Configuration Definition
    ↓
MetadataCompiler
    ↓
ConfigurationCandidate
    ↓
Validation
    ↓
ConfigurationActivator
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

### 9.1 Architectural Objective

Step 5 shall establish the Standard Configuration vertical slice as the first
consumer of the complete Phase 3 configuration lifecycle.

The slice must demonstrate a strict separation between:

configuration definition;
metadata compilation;
candidate validation;
configuration activation;
configuration publication;
runtime configuration context creation;
metadata resolution;
runtime object resolution.

No individual layer may bypass the preceding architectural boundary in order
to obtain the data required by the next layer.

In particular:

runtime consumers must not access MetadataRegistry directly;
RuntimeResolver must not acquire configuration from
RuntimeConfigurationBinding;
MetadataResolver remains the only metadata resolution boundary;
configuration activation remains separate from runtime consumption;
runtime resolution must use the explicitly supplied
RuntimeConfigurationContext.

### 9.2 Standard Configuration Input

The vertical slice shall use an existing Standard Configuration definition,
preferably the Assortment catalog, as its representative runtime object.

The definition is the source-level representation of Standard Configuration and
must remain independent of runtime object construction.

The initial stage is therefore:

AssortmentDefinition
    ↓
MetadataCompiler
    ↓
CatalogMetadata

The resulting metadata becomes part of the configuration candidate.

### 9.3 Configuration Candidate Construction

The compiled Standard Configuration metadata shall be assembled into the
Phase 3 configuration candidate.

The candidate represents configuration that is being prepared for activation
and is not yet available as runtime configuration.

The lifecycle boundary is:

Candidate
    ↓
Validation
    ↓
Validated Candidate

A candidate that has not successfully passed validation must not become the
active configuration.

### 9.4 Configuration Activation

The validated Standard Configuration candidate shall be activated through
ConfigurationActivator.

The resulting object is an immutable ActiveConfiguration.

The activation boundary is:

Validated Candidate
    ↓
ConfigurationActivator
    ↓
ActiveConfiguration

ConfigurationActivator owns the transition into the active configuration
state.

Runtime consumers do not participate in this lifecycle transition.

### 9.5 Runtime Configuration Publication

The activated configuration shall be made available to runtime operations
through RuntimeConfigurationBinding.

The binding represents the lifecycle boundary between configuration
publication and runtime consumption.

The conceptual path is:

ActiveConfiguration
    ↓
RuntimeConfigurationBinding
    ↓
RuntimeConfigurationContext

The binding must not be exposed as a configuration dependency of
RuntimeResolver.

Instead, a runtime operation obtains a context from the configuration
consumption boundary and supplies that context explicitly to its runtime
consumers.

### 9.6 Runtime Configuration Context

The vertical slice shall create or acquire a
RuntimeConfigurationContext representing the active configuration.

The context is the immutable snapshot used by a runtime operation.

Once created, the context must remain associated with the configuration it
represents even if the binding subsequently publishes another active
configuration.

Therefore:

context_v1
    ↓
ActiveConfiguration_v1

followed by:

binding.bind(configuration_v2)

must not change:

context_v1
    ↓
ActiveConfiguration_v1

A new runtime operation may explicitly acquire:

context_v2
    ↓
ActiveConfiguration_v2

### 9.7 Runtime Metadata Resolution

The vertical slice shall resolve Standard Configuration metadata through
MetadataResolver.

The resolver receives the explicit runtime context:

MetadataResolver.resolve(
    context,
    identifier,
)

MetadataResolver obtains metadata exclusively from the configuration
represented by that context.

No runtime component in the slice may access the underlying
MetadataRegistry directly.

### 9.8 Runtime Object Resolution

The resolved metadata shall be passed through RuntimeResolver using the same
explicit runtime context:

RuntimeResolver.resolve(
    context,
    identifier,
)

For the Assortment definition the resulting runtime object shall be a
CatalogRuntime.

The resulting runtime object must expose the metadata corresponding to the
Standard Configuration definition from which the active configuration was
constructed.

The runtime path is therefore:

AssortmentDefinition
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
CatalogRuntime

### 9.9 Configuration Replacement Semantics

The vertical slice shall explicitly demonstrate snapshot consistency across
configuration replacement.

At minimum, the test scenario shall contain two configuration versions
containing distinguishable metadata for the same logical identifier:

configuration_v1
    ↓
context_v1
    ↓
resolve(context_v1, identifier)
    ↓
runtime_v1

Then:

configuration_v2
    ↓
binding.bind(configuration_v2)
    ↓
context_v2
    ↓
resolve(context_v2, identifier)
    ↓
runtime_v2

The slice must demonstrate both:

context_v1 continues to resolve against configuration v1;
context_v2 resolves against configuration v2.

This establishes that runtime resolution follows snapshot semantics, not
current-binding semantics.

### 9.10 Runtime Boundary Invariants

The following invariants shall hold throughout the vertical slice:

Standard Configuration definitions are not runtime objects.
Metadata compilation precedes configuration activation.
Only validated configuration candidates may become active.
ActiveConfiguration is immutable from the runtime perspective.
RuntimeConfigurationBinding owns configuration publication, not runtime
object resolution.
RuntimeConfigurationContext represents an immutable configuration
snapshot.
MetadataResolver is the exclusive metadata resolution boundary.
RuntimeResolver receives the context explicitly.
RuntimeResolver has no dependency on MetadataRegistry.
Runtime consumers do not discover the current configuration implicitly.
Replacing the bound configuration does not mutate existing contexts.
A runtime object resolved with a given context reflects that context's
configuration.

### 9.11 Tests

Step 5 shall introduce an explicit vertical integration test for the complete
Standard Configuration lifecycle.

The test suite shall verify at least:

Standard Configuration definition compilation;
candidate construction;
candidate validation;
activation of the validated candidate;
publication through RuntimeConfigurationBinding;
acquisition of a RuntimeConfigurationContext;
metadata resolution through MetadataResolver;
runtime object resolution through RuntimeResolver;
resulting CatalogRuntime;
correspondence between runtime metadata and Standard Configuration
definition;
configuration replacement;
preservation of an existing context after replacement;
resolution of the same identifier against different configuration contexts;
the vertical slice does not introduce any direct runtime dependency on
MetadataRegistry.

The test should exercise the real Phase 3 components rather than mocking the
configuration lifecycle.

The vertical test must demonstrate that configuration replacement changes
the metadata observed through a newly acquired context while preserving the
metadata observed through the previously acquired context.

### 9.12 Validation

Step 5 implementation shall pass:

pytest
ruff check .
black --check .
mypy src

The existing test suite must remain green.

The new vertical slice must be treated as an architectural acceptance test,
not merely as another unit test.

#### P3-QG5 — Standard Configuration Vertical Slice

P3-QG5 closes only when all of the following are true:

Standard Configuration is compiled into metadata;
metadata is assembled into a configuration candidate;
the candidate is successfully validated;
only the validated candidate is activated;
an ActiveConfiguration is produced;
the active configuration is published through
RuntimeConfigurationBinding;
a RuntimeConfigurationContext can be obtained from the published
configuration;
metadata is resolved through MetadataResolver;
runtime objects are resolved through RuntimeResolver;
the resulting Standard Configuration runtime object is correct;
RuntimeResolver has no dependency on MetadataRegistry;
no runtime consumer accesses MetadataRegistry directly;
configuration replacement is supported;
existing runtime contexts preserve their configuration snapshot;
different contexts produce results according to their represented
configuration;
the complete vertical slice is covered by an integration/vertical test;
pytest passes;
ruff check . passes;
black --check . passes;
mypy src passes.
Expected Dependency Graph

The completed Step 5 path is:

Standard Configuration Definition
            │
            ▼
    MetadataCompiler
            │
            ▼
   ConfigurationCandidate
            │
         validate
            │
            ▼
   Validated Candidate
            │
            ▼
  ConfigurationActivator
            │
            ▼
  ActiveConfiguration
            │
         publish
            │
            ▼

RuntimeConfigurationBinding
            │
            acquire
            │
            ▼
RuntimeConfigurationContext
            │
            ├──────► MetadataResolver
            │
            └──────► RuntimeResolver
                        │
                        ▼
                    CatalogRuntime

RuntimeResolver receives the same RuntimeConfigurationContext explicitly and
uses MetadataResolver as its metadata resolution boundary.

RuntimeResolver does not depend on RuntimeConfigurationBinding and does not
discover the active configuration.

### Exit State

When P3-QG5 closes, AcCoreD will have its first complete Standard
Configuration runtime path exercising the Phase 3 architecture from
configuration definition through executable runtime object resolution.

The resulting architecture will demonstrate that configuration lifecycle,
configuration publication, runtime context, metadata resolution, and runtime
object resolution are separate but composable responsibilities.

The Standard Configuration vertical slice will therefore serve as the
reference integration path for subsequent runtime consumers and future
configuration-driven modules.

## 10. Step 6 — Published Configuration Immutability

Objective

Ensure runtime consumers cannot mutate published configuration semantics.

Detailed implementation plan:

`docs/implementation/PHASE_3_STEP_6_IMPLEMENTATION_PLAN.md`

Architecture Baseline:

Step 6 Mutation Surface Inventory v1.0.

Architectural requirement

Published metadata is immutable from the runtime consumer's perspective.

The publication boundary must prevent mutation of the complete published
configuration graph.

Tests

Verify that:

- runtime consumers cannot mutate published metadata;
- nested metadata structures cannot be mutated;
- published registry state cannot be mutated;
- existing contexts remain coherent;
- configuration replacement creates a new published state rather than
  mutating the previous snapshot.

P3-QG6 closes only after the detailed Step 6 implementation plan has been
satisfied and all validation gates pass.

## Step 7 — Final Phase 3 Architectural Audit

Status: Closed

Quality Gate: P3-QG7 — CLOSED

Objective

Step 7 performs the final architectural audit of Phase 3 and verifies that the
configuration lifecycle, runtime configuration consumption model, published
metadata boundary, and runtime resolution architecture operate as one coherent
system.

This step introduces no new runtime functionality.

Its purpose is to verify that all architectural decisions established during
Phase 3 are implemented consistently in production code, composition roots,
runtime consumers, tests, and documentation.

Audit Scope

The audit covers the complete Phase 3 architecture:

Configuration lifecycle

    ConfigurationLoader
        ↓
    ConfigurationCandidate
        ↓
    ConfigurationValidator
        ↓
    ConfigurationActivator
        ↓
    ActiveConfiguration

Configuration publication

    ActiveConfiguration
        ↓
    RuntimeConfigurationBinding
        ↓
    RuntimeConfigurationContext

Runtime consumption

    RuntimeConfigurationContext
        ↓
    MetadataResolver
        ↓
    RuntimeResolver
        ↓
    Runtime Object

Published metadata

    MetadataRegistry
        ↓ publish()
    PublishedMetadataView
        ↓
    ActiveConfiguration

Architectural Invariants

The final audit verifies the following invariants.

P3-I1 — Single Runtime Ownership

Runtime consumers obtain configuration semantics only through
RuntimeConfigurationContext.

P3-I2 — Activation Isolation

Only ConfigurationActivator creates ActiveConfiguration instances.

P3-I3 — Snapshot Consistency

RuntimeConfigurationContext preserves the configuration snapshot captured at
acquisition time.

P3-I4 — Resolution Consistency

MetadataResolver resolves metadata exclusively from the supplied runtime
context.

P3-I5 — Version Isolation

Different runtime contexts resolve metadata according to their represented
configuration versions.

P3-I6 — Consumer Isolation

Runtime consumers do not access MetadataRegistry directly.

P3-I7 — Storage Independence

Runtime resolution remains independent from metadata storage implementation.

P3-I8 — Layered Resolution

RuntimeResolver depends on MetadataResolver and receives
RuntimeConfigurationContext explicitly.

P3-I9 — Lifecycle Isolation

Production composition roots use the canonical configuration lifecycle and do
not construct ActiveConfiguration directly.

P3-I10 — Published Snapshot Semantics

PublishedMetadataView represents an immutable publication snapshot independent
from subsequent MetadataRegistry mutations.

P3-I11 — Deterministic Resolution

Resolving the same identifier within the same runtime context always produces
metadata from that context.

P3-I12 — Explicit Failure Semantics

Missing metadata remains reported through MetadataResolutionError and unsupported
metadata types remain owned by RuntimeResolver.

P3-AUDIT-F1 — Standard Configuration Bootstrap Lifecycle Bypass

Status: Resolved

Finding

The original StandardConfigurationBootstrap compiled Standard Configuration
definitions directly into MetadataRegistry and constructed ActiveConfiguration
without passing through ConfigurationLoader, ConfigurationValidator,
ConfigurationActivator and RuntimeConfigurationBinding.

This represented a second production configuration lifecycle.

Resolution

StandardConfigurationBootstrap now composes the canonical Phase 3 lifecycle:

Standard Configuration Definition
        ↓
ConfigurationLoader
        ↓
ConfigurationCandidate
        ↓
ConfigurationValidator
        ↓
ConfigurationActivator
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

The bootstrap no longer depends on MetadataRegistry directly.

Result

The Standard Configuration composition root is now aligned with the same
configuration lifecycle used by the Phase 3 architectural vertical slice.

Audit Verification

The audit confirms:

- RuntimeResolver has no MetadataRegistry dependency.
- RuntimeResolver has no RuntimeConfigurationBinding dependency.
- MetadataResolver is the exclusive metadata resolution boundary.
- ActiveConfiguration is created only by ConfigurationActivator.
- PublishedMetadataView forms the read-only publication boundary.
- RuntimeConfigurationContext preserves snapshot semantics.
- Configuration replacement produces new contexts without mutating existing
  contexts.
- StandardConfigurationBootstrap follows the canonical lifecycle.
- Phase 1, Phase 2 and Phase 3 vertical slices remain green.
- No production runtime consumer bypasses configuration resolution.

Validation

Final validation completed successfully:

pytest

188 passed

ruff check .

PASS

black --check .

PASS

mypy src

PASS

P3-QG7 — Final Phase 3 Architectural Audit

Status: CLOSED

P3-QG7 closes when all of the following conditions are satisfied:

- configuration lifecycle ownership is unambiguous;
- ConfigurationActivator is the only production creator of ActiveConfiguration;
- RuntimeConfigurationBinding is the publication boundary;
- RuntimeConfigurationContext provides immutable snapshot semantics;
- PublishedMetadataView is the read-only publication boundary;
- MetadataResolver exclusively resolves metadata from runtime context;
- RuntimeResolver depends only on MetadataResolver and explicit context;
- no runtime consumer accesses MetadataRegistry directly;
- StandardConfigurationBootstrap uses the canonical lifecycle;
- configuration replacement preserves existing runtime contexts;
- Phase 3 vertical slice passes;
- the complete test suite passes;
- ruff passes;
- black passes;
- mypy passes.

All Phase 3 architectural invariants are satisfied.

Exit State

Phase 3 is architecturally complete.

The canonical runtime configuration path is:

Configuration Definition
        ↓
Metadata Compilation
        ↓
Configuration Candidate
        ↓
Validation
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
Runtime Object

Published metadata is exposed through an immutable publication boundary, runtime
resolution is context-driven, configuration ownership remains outside runtime
consumers, and Standard Configuration serves as the reference production
composition of the complete Phase 3 architecture.

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