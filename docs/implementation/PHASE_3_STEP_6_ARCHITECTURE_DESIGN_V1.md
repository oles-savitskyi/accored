PHASE 3 — STEP 6 ARCHITECTURE DESIGN v1.0
1. Document Status

Document: Phase 3 — Step 6 Architecture Design
Version: 1.0
Status: Proposed
Phase: Phase 3 — Runtime Configuration Consumption & Resolution
Step: Step 6 — Published Configuration Immutability

Purpose

This document defines the architecture for immutable published configuration in AcCoreD.

The design establishes the boundary between:

mutable configuration construction;
configuration validation;
configuration activation;
immutable configuration publication;
runtime configuration consumption.

The design is based on the Mutation Surface Inventory performed against the existing metadata model and MetadataRegistry.

2. Architectural Context

Phase 2 established the configuration lifecycle:

Configuration Definition
        ↓
ConfigurationCandidate
        ↓
Validation
        ↓
Validated Candidate
        ↓
ConfigurationActivator
        ↓
ActiveConfiguration

Phase 3 subsequently established runtime consumption:

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

Step 5 demonstrated that these boundaries compose into a complete Standard Configuration vertical slice.

Step 6 addresses the remaining architectural weakness:

ActiveConfiguration is structurally immutable, but its referenced MetadataRegistry is currently mutable.

Therefore:

ActiveConfiguration
        ↓
MetadataRegistry
        ↓
register(...)

currently permits mutation of published configuration.

This violates the intended snapshot semantics of runtime configuration.

3. Architectural Problem

The current architecture has two different semantic states represented by the same registry type.

During configuration construction:

ConfigurationCandidate
        ↓
MetadataRegistry
        ↓
register(metadata)

The registry must be mutable.

After activation:

ActiveConfiguration
        ↓
MetadataRegistry

The same registry must be immutable.

This creates an ambiguity:

MetadataRegistry
    = mutable construction container
    = published runtime configuration storage

These are different responsibilities and should not share the same mutability contract.

4. Design Goals

Step 6 shall establish the following goals.

G1 — Immutable Published Configuration

Once an ActiveConfiguration has been created, its complete runtime-visible configuration graph must be immutable.

G2 — Preserve Mutable Construction

Configuration loading and candidate construction must retain the ability to register compiled metadata.

G3 — Explicit Publication Boundary

The transition from mutable configuration to immutable configuration must occur during activation.

G4 — Snapshot Consistency

An existing ActiveConfiguration and RuntimeConfigurationContext must remain unchanged when another configuration version is published.

G5 — No Runtime Mutation API

Runtime consumers must not have access to configuration mutation operations.

G6 — Preserve Existing Metadata Model

Existing metadata value objects should remain immutable value objects rather than acquiring lifecycle-oriented freezing behavior.

G7 — Avoid Implicit Runtime Configuration

Step 6 must not reintroduce current-configuration discovery into runtime consumers.

5. Non-Goals

Step 6 does not introduce:

configuration persistence;
configuration version storage;
concurrent configuration management;
transactional configuration publication;
configuration rollback;
automatic context propagation;
runtime caching;
metadata mutation APIs;
generalized immutable-object infrastructure;
a new metadata type system.

Step 6 also does not change the Phase 2 configuration lifecycle.

6. Core Decision
Decision

The configuration construction registry and the published runtime registry shall be treated as distinct semantic states.

The construction-time MetadataRegistry remains mutable.

Activation shall create an immutable published metadata registry representation.

Therefore the target lifecycle becomes:

ConfigurationCandidate
        │
        │ mutable
        ▼
MetadataRegistry
        │
        │ publish
        ▼
PublishedMetadataRegistry
        │
        │ immutable
        ▼
ActiveConfiguration

The published registry shall expose only read operations.

It shall not expose register() or any other mutation operation.

7. Target Architecture

The complete configuration lifecycle becomes:

Standard Configuration Definition
            │
            ▼
      MetadataCompiler
            │
            ▼
  ConfigurationCandidate
            │
            │ mutable
            ▼
     MetadataRegistry
            │
         validate
            │
            ▼
   Validated Candidate
            │
            ▼
  ConfigurationActivator
            │
            │ publish
            ▼
 PublishedMetadataRegistry
            │
            ▼
  ActiveConfiguration
            │
         bind
            ▼
RuntimeConfigurationBinding
            │
         acquire
            ▼
RuntimeConfigurationContext
            │
      ┌─────┴─────┐
      ▼           ▼
MetadataResolver RuntimeResolver
      │           │
      └─────┬─────┘
            ▼
       Runtime Object

The key architectural boundary is:

mutable construction graph
            ↓
       ACTIVATION
            ↓
immutable published graph
8. Published Metadata Registry
8.1 Responsibility

PublishedMetadataRegistry represents metadata belonging to an activated configuration.

Its responsibility is exclusively metadata lookup.

It shall support operations conceptually equivalent to:

get(identifier)
contains(identifier)
all()

It shall not support:

register(...)
remove(...)
replace(...)
clear(...)
update(...)
8.2 Construction Registry vs Published Registry

The semantic distinction is:

Property	MetadataRegistry	PublishedMetadataRegistry
Lifecycle	construction	runtime
Mutable	yes	no
register()	yes	no
get()	yes	yes
contains()	yes	yes
all()	yes	yes
Used by loader	yes	no
Used by active configuration	no	yes
Runtime-visible	no	yes

The names are intentionally semantic.

The architecture must make it difficult to accidentally use the mutable registry as published runtime state.

9. Publication Semantics

Publication shall create a new immutable registry representation from the candidate registry.

Conceptually:

candidate.metadata_registry
        │
        │ publish
        ▼
published_metadata_registry

The original candidate registry remains associated with the candidate.

The candidate is not converted into an immutable object.

Therefore:

Candidate
    └── mutable registry


ActiveConfiguration
    └── immutable published registry

are separate ownership domains.

10. Ownership Model

The ownership model shall be explicit.

ConfigurationLoader owns construction
ConfigurationLoader
        ↓
MetadataRegistry

The loader populates the registry.

ConfigurationCandidate owns preparation state
ConfigurationCandidate
        ↓
MetadataRegistry

The candidate represents configuration that may still be rejected or discarded.

ConfigurationActivator owns publication
ConfigurationActivator
        ↓
PublishedMetadataRegistry
        ↓
ActiveConfiguration

Activation creates the runtime-visible snapshot.

RuntimeConfigurationBinding owns publication of active configuration
RuntimeConfigurationBinding
        ↓
ActiveConfiguration

Binding does not mutate the configuration.

RuntimeConfigurationContext owns operation snapshot
RuntimeConfigurationContext
        ↓
ActiveConfiguration

The context does not mutate the active configuration.

11. ActiveConfiguration Contract

ActiveConfiguration remains:

@dataclass(frozen=True, slots=True)
class ActiveConfiguration:
    ...

Its semantic contract becomes stronger.

It is not merely structurally frozen.

It represents:

An immutable published configuration snapshot.

Therefore all objects reachable through its runtime-visible fields must satisfy the publication immutability contract.

Specifically:

ActiveConfiguration
    ├── identity              immutable
    ├── version               immutable
    └── metadata_registry     immutable
          └── metadata        immutable
12. Metadata Immutability

The existing metadata model already provides a strong foundation.

Metadata

Current design:

frozen dataclass
slots
immutable scalar fields
tuple normalized_content

Status:

Accepted.

No lifecycle-specific freeze mechanism is required.

CatalogMetadata

Current design:

frozen dataclass
tuple system_fields
tuple attributes

Status:

Accepted.

The nested metadata graph is immutable at the container level.

SystemFieldMetadata

Current design:

frozen dataclass
scalar / enum fields

Status:

Accepted.

AttributeMetadata

Current design:

frozen dataclass

is accepted structurally, with one open semantic issue:

default_value: Any

A frozen object does not guarantee that an arbitrary value stored in default_value is immutable.

Therefore Step 6 establishes the following constraint:

default_value must represent an immutable semantic value in published metadata.

The current architecture does not yet require a new implementation for this constraint.

The exact domain of supported default values shall be formalized before any future feature introduces structured mutable defaults.

13. Deep Immutability Contract

Step 6 defines runtime-visible metadata immutability as:

No supported runtime operation can mutate any object reachable from an ActiveConfiguration.

This includes:

ActiveConfiguration
    ↓
PublishedMetadataRegistry
    ↓
Metadata
    ↓
CatalogMetadata
    ↓
AttributeMetadata
    ↓
default_value

and:

CatalogMetadata
    ↓
SystemFieldMetadata

The contract is therefore transitive.

14. Registry API Boundary

The mutable registry API remains available only during configuration construction.

Allowed
ConfigurationLoader
    ↓
MetadataRegistry.register()
Prohibited
ActiveConfiguration
    ↓
PublishedMetadataRegistry.register()

because the published registry has no such operation.

This is preferable to runtime guards such as:

if self._frozen:
    raise RuntimeError(...)

because the prohibited operation does not exist in the published abstraction.

15. Why Not freeze() on MetadataRegistry?

The design explicitly rejects:

registry.freeze()

as the primary publication model.

A boolean freeze flag would produce:

one mutable object
        ↓
runtime state flag
        ↓
mutation conditionally prohibited

This has several disadvantages:

construction and runtime semantics remain combined;
the mutable API remains visible;
accidental retention of the construction object remains possible;
immutability depends on runtime checks;
the type itself does not communicate its lifecycle role.

The preferred architecture is:

Mutable Registry
        ↓
Immutable Published Registry

This represents the semantic transition in the object model itself.

16. Why Not Mutate Candidate Registry During Activation?

The design also rejects:

candidate.metadata_registry.freeze()

as the publication mechanism.

The candidate represents configuration preparation.

Activation should produce a new runtime-visible representation.

Therefore:

Candidate
    └── construction state


ActiveConfiguration
    └── published state

remain conceptually separate.

This preserves the already established lifecycle rule:

Activation does not mutate the candidate into an active configuration.

It creates the active configuration.

17. Snapshot Semantics

Step 6 strengthens the snapshot semantics established by Step 5.

Given:

candidate_v1
    ↓
active_v1
    ↓
context_v1

and later:

candidate_v2
    ↓
active_v2
    ↓
context_v2

the following must always hold:

context_v1.configuration is active_v1
context_v2.configuration is active_v2

and:

published_registry_v1 is not mutated

when version 2 is created.

Therefore:

resolve(context_v1, identifier)

continues to observe version 1.

And:

resolve(context_v2, identifier)

observes version 2.

18. Replacement Model

Configuration replacement is therefore:

Configuration V1
       │
       ▼
Published Registry V1
       │
       ▼
ActiveConfiguration V1
       │
       ▼
Context V1




Configuration V2
       │
       ▼
Published Registry V2
       │
       ▼
ActiveConfiguration V2
       │
       ▼
Context V2

It is not:

Registry V1
    ↓
mutate
    ↓
Registry V2

The latter would violate snapshot semantics.

19. Runtime Dependency Rules

The following dependency rules remain mandatory.

Allowed
MetadataResolver
    → RuntimeConfigurationContext


RuntimeResolver
    → MetadataResolver
    → RuntimeConfigurationContext


RuntimeConfigurationContext
    → ActiveConfiguration


ActiveConfiguration
    → PublishedMetadataRegistry
Prohibited
RuntimeResolver
    ✕→ MetadataRegistry


RuntimeResolver
    ✕→ RuntimeConfigurationBinding


RuntimeResolver
    ✕→ ConfigurationActivator


RuntimeResolver
    ✕→ ConfigurationLoader

Runtime consumers must never acquire the mutable construction registry.

20. Error Semantics

Step 6 does not introduce a new generalized exception hierarchy.

Construction-time mutation errors remain construction concerns.

Published registry operations are read-only by API design.

Existing resolution errors remain owned by:

MetadataResolver

Activation errors remain owned by:

ConfigurationActivator

Validation errors remain owned by:

ConfigurationValidator
21. Required API Direction

The desired public model is conceptually:

MutableMetadataRegistry
    register()
    get()
    contains()
    all()


PublishedMetadataRegistry
    get()
    contains()
    all()

Whether the implementation uses these exact names or another internal representation is an implementation detail.

The architectural requirement is:

The runtime-visible registry abstraction must not expose mutation.

22. Testing Architecture

Step 6 shall add tests at three levels.

22.1 Published Registry Tests

Verify:

published registry contains all metadata;
get() works;
contains() works;
all() returns immutable collection;
published registry exposes no mutation operation.
22.2 Activation Tests

Verify:

validated candidate
        ↓
activate
        ↓
ActiveConfiguration

produces a published immutable registry.

Also verify that:

candidate.metadata_registry

is not the mutable runtime registry representation.

22.3 Snapshot Tests

The strongest acceptance test should be:

configuration_v1
    ↓
context_v1

then:

configuration_v2
    ↓
context_v2

and verify:

context_v1 → v1 metadata
context_v2 → v2 metadata

The test must use distinguishable metadata for the same identifier.

This continues the replacement scenario already established in the Step 5 vertical slice.

23. Architectural Acceptance Criteria

Step 6 is complete only when all of the following hold:

Construction-time metadata registry remains mutable.
Published metadata registry is immutable.
ActiveConfiguration contains only published metadata state.
MetadataRegistry.register() cannot mutate published configuration.
Published registry exposes only read operations.
Metadata remains immutable.
CatalogMetadata remains immutable.
AttributeMetadata remains structurally immutable.
SystemFieldMetadata remains immutable.
Metadata collections remain immutable.
No mutable internal collection is exposed through read APIs.
Activation creates the published metadata representation.
Candidate construction remains independent from runtime publication.
Configuration replacement creates a new published snapshot.
Existing runtime contexts remain unchanged after replacement.
RuntimeResolver remains independent of MetadataRegistry.
RuntimeResolver remains independent of RuntimeConfigurationBinding.
MetadataResolver remains the metadata resolution boundary.
Existing Step 5 vertical slice remains green.
New Step 6 immutability tests pass.
pytest passes.
ruff check . passes.
black --check . passes.
mypy src passes.
24. Quality Gate
P3-QG6 — Published Configuration Immutability

Status: CLOSED

P3-QG6 closes only when:

mutable construction state
        ↓
activation
        ↓
immutable published state

is enforced by the architecture and verified by tests.

In particular:

No supported runtime operation may mutate any object reachable from an ActiveConfiguration.

25. Consequences
Positive
Strong runtime snapshot semantics

Published configuration cannot change underneath an existing runtime context.

Clear lifecycle ownership
Loader       → construction
Validator    → validation
Activator    → publication
Binding      → active configuration publication
Context      → runtime snapshot
Resolver     → runtime resolution
Better type-level architecture

The published registry abstraction does not expose mutation.

Reduced coupling

Runtime consumers do not need to understand configuration construction.

Safer configuration replacement

New configuration versions cannot mutate old published state.

Negative
Additional registry representation

There will be a distinction between construction-time and published registry state.

Activation performs publication work

ConfigurationActivator becomes responsible not only for lifecycle transition but also for creation of the immutable metadata snapshot.

Potential future treatment of default values

AttributeMetadata.default_value: Any requires a future semantic constraint if structured defaults are introduced.

26. Rejected Alternatives
A1 — Keep MetadataRegistry mutable

Rejected.

Would violate published configuration immutability.

A2 — Add _frozen flag to MetadataRegistry

Rejected as primary design.

Would retain mutable construction semantics in the runtime-visible object.

A3 — Call freeze() on candidate registry

Rejected.

Would mutate the candidate during activation and conflate preparation and publication.

A4 — Deep-copy metadata at every runtime access

Rejected.

Would introduce unnecessary runtime cost and obscure ownership semantics.

Immutability must be established at publication time.

A5 — Use copy.deepcopy() during activation

Rejected as the architectural mechanism.

Deep copying does not establish an explicit immutable abstraction and can become fragile as metadata types evolve.

A6 — Use MappingProxyType as the public architecture

Rejected as the primary abstraction.

It is an implementation mechanism, not a domain-level representation of published metadata.

A dedicated read-only published registry abstraction communicates the architecture more clearly.

27. Reference Architecture After Step 6

The resulting architecture becomes:

                    CONSTRUCTION
                         │
                         ▼
              Standard Configuration
                         │
                         ▼
                  MetadataCompiler
                         │
                         ▼
             ConfigurationCandidate
                         │
                         ▼
                MetadataRegistry
                  [MUTABLE]
                         │
                      validate
                         │
                         ▼
                 VALIDATED CANDIDATE
                         │
                         ▼
              ConfigurationActivator
                         │
                    PUBLISH
                         │
                         ▼
           PublishedMetadataRegistry
                    [IMMUTABLE]
                         │
                         ▼
                ActiveConfiguration
                    [IMMUTABLE]
                         │
                       bind
                         │
                         ▼
           RuntimeConfigurationBinding
                         │
                     acquire
                         │
                         ▼
            RuntimeConfigurationContext
                    [IMMUTABLE]
                         │
                ┌────────┴────────┐
                ▼                 ▼
        MetadataResolver    RuntimeResolver
                │                 │
                └────────┬────────┘
                         ▼
                   Runtime Object
28. Final Architectural Principle

Step 6 establishes the following invariant as a permanent AcCoreD architectural rule:

Configuration is mutable while being constructed and immutable once published.

More formally:

Mutable Candidate
        ↓
Validated Candidate
        ↓
Activation / Publication Boundary
        ↓
Immutable Active Configuration
        ↓
Immutable Runtime Context

And:

No runtime consumer may mutate, replace, or otherwise alter any state reachable from an ActiveConfiguration.

This is the architectural completion of the configuration snapshot model introduced in Phase 2 and exercised by the Step 5 Standard Configuration vertical slice.