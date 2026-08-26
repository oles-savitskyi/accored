# Phase 3 — Step 6 Implementation Plan

## Published Configuration Immutability

Status: Implemented

Phase: Phase 3 — Runtime Configuration Consumption & Resolution

Step: 6

Architecture Baseline: Step 6 Mutation Surface Inventory v1.0


## 1. Purpose

Step 6 establishes the immutability boundary of published runtime
configuration.

The purpose of the step is to ensure that once configuration has been
published as an `ActiveConfiguration`, runtime consumers cannot mutate the
configuration semantics represented by that published state.

Step 6 does not introduce a new configuration lifecycle.

It hardens the publication boundary established by the previous Phase 3
steps.

The architectural objective is:

```text
Configuration Construction
        ↓
Metadata Compilation
        ↓
Configuration Candidate
        ↓
Validation
        ↓
Activation
        ↓
ActiveConfiguration
        ↓
Publication
        ↓
Immutable Published Configuration
        ↓
RuntimeConfigurationContext
        ↓
Runtime Resolution

The published configuration must remain semantically stable for the lifetime
of every runtime context that represents it.

2. Architectural Baseline

Step 6 begins from the following established architecture.

Phase 2 established:

Configuration Definition
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

Phase 3 established:

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

Step 5 established the complete Standard Configuration vertical slice.

Step 6 now establishes the immutability guarantees of the published state
consumed by that runtime path.

3. Mutation Surface Inventory

The Step 6 audit identified the following metadata and configuration objects as
part of the published configuration graph.

ActiveConfiguration
    │
    └── MetadataRegistry
            │
            ├── Metadata
            │     └── normalized_content
            │
            └── CatalogMetadata
                  ├── system_fields
                  │     └── SystemFieldMetadata
                  │
                  └── attributes
                        └── AttributeMetadata
                              └── default_value

The immutability analysis must cover the complete graph rather than only the
top-level dataclasses.

3.1 Metadata

Metadata is declared as:

@dataclass(frozen=True, slots=True)
class Metadata:
    ...

Direct field reassignment is therefore prohibited by the dataclass contract.

The following fields are part of the published semantic state:

identifier;
metadata_type;
name;
source_definition_id;
normalized_content.

normalized_content is represented as a tuple and therefore has immutable
container semantics.

The current structure provides the required structural immutability for this
field.

3.2 CatalogMetadata

CatalogMetadata is also declared as a frozen dataclass.

Its published semantic state includes:

inherited Metadata fields;
system_fields;
attributes.

Both collections are represented as tuples.

Therefore the collection structure itself cannot be modified after
construction.

The Step 6 implementation must preserve this property.

3.3 AttributeMetadata

AttributeMetadata is declared as:

@dataclass(frozen=True, slots=True)
class AttributeMetadata:
    ...

Its fields include:

name;
attribute_type;
nullable;
default_value;
description;
reference_target.

All fields are protected from direct reassignment.

However, default_value is currently typed as Any.

Therefore:

frozen AttributeMetadata
        ≠
deeply immutable AttributeMetadata

if a future or external caller supplies a mutable object as default_value.

Step 6 must therefore explicitly determine whether the current configuration
contract permits mutable values in metadata defaults.

If mutable values are not part of the configuration model, this must become an
explicit invariant.

If mutable values are required in the future, their representation must be
made immutable before publication.

3.4 SystemFieldMetadata

SystemFieldMetadata is a frozen dataclass.

Its fields are scalar enum/value types:

name;
field_type;
nullable;
required.

No nested mutable state is currently present.

The current representation therefore satisfies the structural immutability
requirement.

3.5 MetadataRegistry

MetadataRegistry is the primary mutation surface identified by the audit.

Its internal state is currently:

self._metadata: dict[Identifier, Metadata]

The registry exposes:

register(...)
get(...)
contains(...)
all(...)

register() mutates the registry after construction.

Therefore:

MetadataRegistry

is currently a mutable assembly structure.

This is not inherently an architectural defect.

A mutable registry may legitimately be used while configuration is being
constructed.

The Step 6 architectural question is instead:

Can the mutable registry remain reachable and mutable after the
configuration has been published?

The answer must be no.

3.6 MetadataRegistry.get()

get() returns the registered metadata object directly.

This is acceptable only if the complete returned metadata graph is immutable.

The method must therefore not become an indirect mutation path through mutable
metadata or nested values.

3.7 MetadataRegistry.all()

all() returns:

tuple(self._metadata.values())

The returned collection is immutable structurally.

However, the method currently exposes the registered metadata objects
themselves.

This is acceptable only when those objects and their complete reachable
semantic state are immutable.

The Step 6 implementation must preserve that invariant.

3.8 ActiveConfiguration

ActiveConfiguration is an immutable runtime-visible snapshot.

Its metadata registry is therefore part of the published configuration graph.

Consequently, freezing the ActiveConfiguration object alone is insufficient
if its referenced MetadataRegistry remains mutable.

The following must be prevented:

ActiveConfiguration
        ↓
MetadataRegistry
        ↓
register(...)

after publication.

3.9 RuntimeConfigurationContext

RuntimeConfigurationContext is an immutable snapshot of an
ActiveConfiguration.

Its purpose is to preserve the configuration semantics of a runtime operation.

Therefore:

context_v1
        ↓
ActiveConfiguration_v1

must remain stable even after:

binding.bind(ActiveConfiguration_v2)

The immutability of the context depends on the immutability of the published
configuration graph it references.

4. Step 6 Architectural Invariant

The central invariant of Step 6 is:

A published ActiveConfiguration and every metadata object reachable from
it must be immutable from the runtime consumer's perspective.

This means immutability must be evaluated transitively.

The required property is:

published configuration
        ↓
all reachable semantic state
        ↓
cannot be changed

It is not sufficient that:

ActiveConfiguration

itself rejects attribute assignment.

5. Construction vs Publication

Step 6 shall explicitly distinguish configuration construction from
configuration publication.

During construction, mutable assembly structures may be permitted.

For example:

MetadataCompiler
        ↓
MetadataRegistry
        ↓
register(...)
        ↓
ConfigurationCandidate

The publication boundary must establish an immutable runtime-visible state.

Conceptually:

Mutable Assembly
        ↓
Validation
        ↓
Activation
        ↓
Publication Boundary
        ↓
Immutable Published State

After this boundary, no runtime consumer may obtain a mutable configuration
handle.

6. Publication Boundary

The exact implementation mechanism is intentionally left open at the start of
Step 6.

Candidate mechanisms include:

immutable registry;
immutable mapping;
read-only registry view;
private publication storage;
separate mutable assembly and immutable published registry.

The implementation must be selected according to the following requirement:

The runtime-visible published configuration must not expose a mutation path
back into configuration state.

The selected mechanism must preserve existing configuration lifecycle and
runtime resolution semantics.

### Implementation Boundary Note — Publication View Immutability

`PublishedMetadataView` provides the runtime read-only publication boundary
through its public API.

The view intentionally exposes only read operations:

- `get()`;
- `contains()`;
- `all()`.

Its internal storage remains an implementation detail and is not part of the
runtime contract. Runtime consumers must not access private implementation
state such as `_metadata`.

Step 6 does not require defensive enforcement against deliberate access to
private Python attributes. The architectural requirement is that published
configuration semantics are immutable from the supported runtime API
perspective.

Deep immutability of metadata payloads is also outside the scope of Step 6.
Metadata value objects are currently modeled as immutable dataclasses, while
fields such as `default_value: Any` may theoretically contain mutable values.

If future metadata types introduce mutable payloads or if stronger defensive
immutability guarantees become necessary, deep immutability of the metadata
model should be addressed as a separate architectural hardening task.

This does not block Step 6 completion.

7. Required Dependency Boundaries

Step 6 must preserve the Phase 3 dependency boundaries.

The runtime path remains:

Runtime Consumer
        ↓
RuntimeResolver
        ↓
MetadataResolver
        ↓
RuntimeConfigurationContext
        ↓
ActiveConfiguration

The following remain prohibited:

RuntimeResolver
    ✕→ MetadataRegistry


RuntimeResolver
    ✕→ RuntimeConfigurationBinding


RuntimeResolver
    ✕→ ConfigurationActivator


RuntimeResolver
    ✕→ ConfigurationLoader


Runtime Consumer
    ✕→ direct MetadataRegistry access

Step 6 must not solve immutability by introducing a new runtime dependency on
the registry.

8. Immutability Requirements

The implementation must establish the following guarantees.

8.1 Published Metadata

Published metadata must reject direct field mutation.

Existing frozen dataclass semantics must remain intact.

8.2 Nested Metadata Collections

The following collections must remain structurally immutable:

CatalogMetadata.attributes
CatalogMetadata.system_fields
Metadata.normalized_content

Tuples are currently used for these structures and should remain the default
representation unless the implementation requires a different immutable
representation.

8.3 Published Registry

A registry belonging to a published configuration must not permit:

register(...)
remove(...)
replace(...)
clear(...)

or equivalent mutation through any public or indirect API.

8.4 Metadata Retrieval

Retrieving metadata from the published configuration must not provide a
mutation path into the published state.

8.5 Context Stability

Existing runtime contexts must continue to represent exactly the same
configuration after configuration replacement.

context_v1
    ↓
configuration_v1

must remain unchanged after:

binding.bind(configuration_v2)
8.6 Configuration Replacement

Replacement must create a new published configuration state.

It must not mutate the state represented by an existing context.

configuration_v1
        ↓
context_v1


configuration_v2
        ↓
context_v2

Both states must remain independently valid.

9. Default Value Immutability

The current AttributeMetadata.default_value field requires explicit
architectural treatment.

It is typed as:

Any

and therefore potentially permits mutable values.

Step 6 must determine and document the invariant for this field.

Preferred initial rule:

Published metadata default values must be immutable configuration values.

The implementation must not silently introduce deep-copy semantics as a
substitute for an explicit configuration invariant.

If the supported default-value domain already consists only of immutable
values, the implementation should preserve that domain and add tests proving
the invariant.

If mutable default values are required later, that decision must be handled
as a separate architectural change.

10. Implementation Strategy

Step 6 implementation should proceed in the following order.

Step 6.1 — Confirm Mutation Surface

Review all public and internal mutation paths for:

MetadataRegistry;
metadata classes;
ActiveConfiguration;
RuntimeConfigurationContext;
nested metadata collections;
metadata default values.

No implementation change should be made until the complete mutation surface
is identified.

Step 6.2 — Define Publication Contract

Document the exact distinction between:

assembly registry

and:

published registry

if the selected implementation requires both.

The publication contract must define whether publication:

freezes an existing registry;
creates an immutable registry;
creates an immutable mapping;
or transfers data into private publication storage.
Step 6.3 — Implement Published Immutability

Implement the selected mechanism without changing:

configuration identity semantics;
configuration version semantics;
activation semantics;
runtime context semantics;
metadata resolution semantics;
runtime object resolution semantics.
Step 6.4 — Protect Runtime Graph

Verify that the complete object graph reachable from:

RuntimeConfigurationContext

cannot be mutated through runtime-visible references.

Step 6.5 — Preserve Replacement Semantics

Verify:

v1 → context_v1
v2 → context_v2

remain independent after publication replacement.

11. Tests

Step 6 shall introduce explicit tests for the publication immutability
boundary.

11.1 Metadata Mutation

Verify that direct mutation of:

Metadata;
CatalogMetadata;
AttributeMetadata;
SystemFieldMetadata

is rejected.

11.2 Nested Collection Mutation

Verify that runtime consumers cannot mutate:

CatalogMetadata.attributes
CatalogMetadata.system_fields
Metadata.normalized_content

through returned references.

11.3 Registry Mutation

Verify that a published registry cannot be modified through:

register(...)

or any other exposed mutation operation.

11.4 Retrieved Metadata Mutation

Verify that metadata returned by the published configuration cannot be used
to modify published configuration semantics.

11.5 Default Value Mutation

If mutable values are not supported, verify that published metadata does not
contain mutable default values.

If the current implementation uses only immutable defaults, add regression
coverage for the supported value domain.

11.6 Context Snapshot

Verify:

context_v1.configuration is active_v1

and that replacement with active_v2 does not alter context_v1.

11.7 Configuration Replacement

Verify that:

resolve(context_v1, identifier)

continues to return the version-1 semantics after version 2 is published.

Also verify:

resolve(context_v2, identifier)

returns version-2 semantics.

11.8 Runtime Boundary

Verify that runtime resolution continues to operate only through:

RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver

and does not require direct registry access.

12. Quality Gate
P3-QG6 — Published Configuration Immutability

P3-QG6 closes only when all of the following are true:

the complete mutation surface has been audited;
the publication boundary is explicitly defined;
published metadata is immutable;
nested metadata collections are immutable;
published registry state cannot be mutated;
metadata retrieval does not expose a mutation path;
published configuration is immutable from the runtime consumer's
perspective;
RuntimeConfigurationContext preserves its configuration snapshot;
configuration replacement creates a new published state;
existing contexts remain coherent after replacement;
different contexts resolve against their represented configuration;
default-value semantics are explicitly defined;
no runtime consumer bypasses the Phase 3 resolution boundary;
Step 5 vertical tests remain green;
new Step 6 immutability tests pass;
pytest passes;
ruff check . passes;
black --check . passes;
mypy src passes.
13. Expected Dependency Graph

The completed Step 6 architecture is:

Configuration Definition
        │
        ▼
MetadataCompiler
        │
        ▼
ConfigurationCandidate
        │
        ▼
Validation
        │
        ▼
ConfigurationActivator
        │
        ▼
ActiveConfiguration
        │
        ▼
Publication Boundary
        │
        ▼
Immutable Published Configuration
        │
        ▼
RuntimeConfigurationBinding
        │
        ▼
RuntimeConfigurationContext
        │
        ├───────────────┐
        ▼               ▼
MetadataResolver   RuntimeResolver
        │               │
        └───────┬───────┘
                ▼
          Runtime Object

The critical property is:

RuntimeConfigurationContext
        ↓
Immutable Published Configuration

No runtime-visible reference may lead back to mutable configuration assembly
state.

14. Non-Goals

Step 6 does not introduce:

a new configuration lifecycle;
configuration persistence;
configuration version history;
concurrency management;
distributed configuration publication;
automatic context propagation;
runtime caching;
a generalized immutable object framework;
a generalized dependency injection mechanism;
new metadata types;
new runtime object types;
a new runtime resolution architecture.

Step 6 is specifically concerned with the immutability of published
configuration semantics.

15. Architectural Risks
15.1 False Immutability

Using frozen=True may create the appearance of complete immutability while
nested mutable values remain reachable.

This is why Step 6 evaluates the complete published graph.

15.2 Registry Leakage

An immutable ActiveConfiguration can still reference a mutable
MetadataRegistry.

Therefore top-level dataclass immutability is not sufficient.

15.3 Accidental API Expansion

Adding a new public registry API solely to support publication may create a
second configuration boundary.

The implementation must preserve the existing Phase 3 ownership model.

15.4 Copy-Based Semantics

Deep-copying configuration on every access may hide mutation problems rather
than establish a clear publication contract.

Copy semantics must not be introduced unless explicitly justified.

15.5 Over-Engineering

Step 6 should not introduce a general-purpose immutable collection framework
unless the existing configuration model requires it.

The implementation should solve the actual published configuration mutation
surface.

16. Exit State

When P3-QG6 closes, AcCoreD will have an explicit and enforced immutability
boundary around published configuration.

The resulting architecture will guarantee:

configuration construction
        ≠
configuration publication
        ≠
runtime configuration consumption

and:

published configuration
        ↓
immutable semantic state
        ↓
stable runtime context
        ↓
deterministic runtime resolution

Configuration replacement will create a new published state rather than
mutating the state represented by existing runtime contexts.

The Step 5 Standard Configuration vertical slice will therefore operate on a
configuration model whose published semantics are stable for the lifetime of
the runtime context.

17. Relation to Existing Phase 3 Decisions

Step 6 builds on, but does not replace, the following Phase 3 architectural
decisions.

ADR-CONF-006 establishes that runtime consumers must not bypass the
configuration resolution boundary.

Step 6 extends that principle by establishing that the configuration reached
through that boundary is immutable from the runtime consumer's perspective.

Therefore the combined runtime contract is:

Runtime Consumer
        ↓
RuntimeResolver
        ↓
MetadataResolver
        ↓
RuntimeConfigurationContext
        ↓
Immutable ActiveConfiguration
        ↓
Published Metadata

The runtime consumer has neither an alternative configuration source nor a
mutation path into the published configuration.

18. Reference Principle

The definitive architectural rule introduced by Step 6 is:

Publication is the point at which configuration semantics become
immutable.

Before publication, configuration may be assembled and validated.

After publication, configuration semantics are fixed.

A new configuration version is represented by a new published state rather
than by mutation of an existing published state.