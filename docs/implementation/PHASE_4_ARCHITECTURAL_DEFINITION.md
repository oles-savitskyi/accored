# Phase 4 — Object Runtime Architectural Definition

**Status:** Accepted / Implemented in progress
**Version:** 1.1
**Phase:** 4
**Depends on:** `phase-3-final`
**Architectural baseline:** `architecture-core-3.0`

---

## 1. Purpose

Phase 4 establishes the architectural boundary between:

- resolved runtime types derived from metadata; and
- executable runtime instances of business objects.

Phase 3 established the configuration and runtime resolution pipeline:

    Configuration Definition
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
    RuntimeConfigurationBinding
            ↓
    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Runtime Object

Phase 4 defines what exists at the final boundary of this pipeline:

> an executable Object Runtime instance.

The purpose of Phase 4 is therefore not to implement persistence, documents,
posting, registers, or other business subsystems.

The purpose is to establish a stable and generic Object Runtime model that
those future subsystems can consume.

---

# 2. Architectural Context

At the end of Phase 3, AcCoreD has established:

- metadata compilation;
- configuration lifecycle;
- immutable active configuration;
- runtime configuration binding;
- explicit runtime configuration context;
- metadata resolution;
- runtime type resolution;
- minimal executable runtime representations.

The canonical Phase 3 resolution chain is:

    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Runtime Object

Phase 3 intentionally did not establish:

- a generalized object-instance model;
- a generalized object creation framework;
- persistent object state;
- object repositories;
- object querying;
- document execution;
- posting;
- register interaction.

Phase 4 begins at this boundary.

---

# 3. Problem Statement

The current runtime can resolve metadata-defined runtime objects, but the
architecture does not yet define a complete contract for the lifecycle of an
individual business-object instance.

In particular, the following concepts require explicit architectural
definition:

- Object Identity;
- Object Type;
- Object State;
- Object Runtime Context;
- Object Lifecycle;
- Object Creation Boundary;
- Object/Runtime ownership;
- Object/Storage boundary.

Without these definitions, future implementations could independently
introduce incompatible concepts for:

- catalog instances;
- document instances;
- persistent objects;
- object references;
- object lifecycle;
- object creation;
- object lookup.

Phase 4 establishes one generic Object Runtime model before those business
capabilities are implemented.

---

# 4. Phase 4 Goal

The goal of Phase 4 is:

> Establish a generic Object Runtime boundary in which a metadata-defined
> runtime type can be represented by an executable object instance operating
> within an explicit Runtime Configuration Context.

The resulting architecture must allow:

    Metadata-defined Object Type
            ↓
    Runtime Type Resolution
            ↓
    Object Instance Creation
            ↓
    Executable Runtime Object
            ↓
    Object Lifecycle

The model must remain independent from physical persistence.

---

# 5. Core Architectural Model

Phase 4 establishes the following conceptual model:

    Configuration
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
    Resolved Runtime Object Type
          │
          ▼
    Object Creation Boundary
          │
          ▼
    Runtime Object Instance
       ┌──┼───────────────┐
       │  │               │
       ▼  ▼               ▼
    Identity  State     Object Context
       │                  │
       └────────┬─────────┘
                ▼
           Lifecycle
                │
                ▼
        Future Storage Boundary

The exact implementation form of the creation boundary is intentionally
left open until the relevant ADR is accepted.

---

# 6. Object Instance

An Object Instance represents one executable instance of a metadata-defined
business object type.

An Object Instance is distinct from:

- metadata;
- metadata identity;
- configuration identity;
- runtime type;
- persistent storage representation.

Conceptually:

    Object Type
        │
        ├── Instance A
        ├── Instance B
        └── Instance C

Multiple object instances may therefore exist for one metadata-defined type.

The Object Instance is the primary unit of runtime object lifecycle.

---

# 7. Object Type

An Object Type identifies the metadata-defined type from which an object
instance derives its structure and runtime semantics.

The Object Type is not an Object Instance.

The relationship is:

    Metadata Definition
          ↓
    Metadata Type
          ↓
    Runtime Object Type
          ↓
    Object Instance

The Object Type may reference or expose the corresponding metadata identity,
but must not be confused with an individual object's identity.

---

# 8. Object Identity

## 8.1 Definition

Object Identity uniquely identifies an individual Object Instance.

Object Identity is distinct from:

- Configuration Identity;
- Configuration Version;
- Metadata Identity;
- Object Type Identity.

Conceptually:

    Metadata Identity
        = "Assortment"

    Object Identity
        = ULID-1

    Object Identity
        = ULID-2

These represent two different instances of the same metadata-defined type.

## 8.2 Requirements

Object Identity must be:

- unique within its defined identity scope;
- stable for the lifetime of the object instance;
- immutable after assignment;
- independent from the object's mutable state;
- independent from the physical storage mechanism.

## 8.3 Persistence

Phase 4 does not define persistence semantics for Object Identity.

In particular, Phase 4 does not define:

- database identifiers;
- storage keys;
- serialization formats;
- repository identity mapping.

Those belong to the Storage Architecture.

---

# 9. Object State

Object State represents the runtime state associated with an individual
Object Instance.

For the minimum Phase 4 implementation, Object State represents the object's
runtime lifecycle state.

Accordingly, Phase 4 does not introduce a generalized mutable business-state model inside ObjectInstance.

The lifecycle state model is sufficient for the Phase 4 runtime contract. Business values, metadata-defined attributes, dirty tracking, persistence state, and other mutable object data remain concerns of later phases.

Object Runtime State is distinct from:

- persistent state;
- persisted representation;
- storage-managed state.

The current Phase 4 runtime state model is intentionally minimal and does not
define a generalized state engine.

Conceptually:

    Object Instance
          │
          └── Runtime State

Future Object State may include runtime values derived from object semantics,
but Phase 4 does not define a generalized metadata-driven state model.

## 9.1 Separation from Metadata

Metadata defines the structure and semantics of object state.

Metadata does not contain the state of an individual object instance.

Therefore:

    Metadata
       ≠
    Object State

## 9.2 Separation from Persistence

Runtime Object State must not imply a persistence mechanism.

The architecture must permit:

    Runtime Object State
            ↓
       Storage Adapter
            ↓
    Persistent State

without making the Object Runtime dependent on a specific storage provider.

---

# 10. Object Context

Object Context provides the runtime environment required by an Object Instance.

The Object Context must not become an alternative configuration-selection
mechanism.

Phase 3 already established:

    RuntimeConfigurationContext

as the explicit immutable configuration snapshot used by runtime operations.

Therefore:

    Object Context
          │
          └── uses
                 ↓
        RuntimeConfigurationContext

Object Context must not independently:

- discover the active configuration;
- access RuntimeConfigurationBinding directly;
- activate configurations;
- mutate configuration;
- bypass MetadataResolver.

## 10.1 Context Ownership

Object Context is operation/runtime context.

It is not:

- configuration lifecycle state;
- persistent object state;
- object identity;
- global application state.

## 10.2 Context Immutability

The configuration portion of Object Context must preserve the snapshot
semantics established in Phase 3.

An object operation bound to configuration version `V1` must not silently
observe configuration version `V2`.

---

# 11. Object Lifecycle

Phase 4 defines the minimum lifecycle required for executable Object
Instances.

The conceptual lifecycle is:

    Created
       ↓
    Active
       ↓
    Disposed

The exact state representation is an implementation detail, but lifecycle
semantics must be explicit.

## 11.1 Creation

Creation establishes:

- Object Identity;
- Object Type;
- initial Object State;
- Object Context.

Creation does not imply persistence.

## 11.2 Activation

Activation makes the object available for normal runtime use.

Activation must not mean:

- configuration activation;
- persistence;
- posting;
- business transaction commit.

These are separate architectural concepts.

## 11.3 Disposal

Disposal terminates the runtime lifetime of the object instance.

Disposal does not imply deletion from persistent storage.

Persistent deletion, if supported, belongs to Storage/Object business semantics.

---

# 12. Object Creation Boundary

Phase 4 establishes object creation as an explicit architectural concern.

The exact implementation mechanism is intentionally not predetermined.

Possible implementations include:

- dedicated Object Factory;
- runtime object creator;
- type-specific factory registry;
- another explicitly defined creation abstraction.

No implementation choice is accepted merely because the name `ObjectFactory`
appears in existing conceptual documentation.

The architectural requirement is:

> Object creation must have a clear owner and must not be accidentally
> distributed across RuntimeResolver, metadata classes, configuration
> infrastructure, or storage providers.

---

# 13. RuntimeResolver Responsibility

`RuntimeResolver` remains responsible for runtime type resolution.

Its responsibility is conceptually:

    RuntimeConfigurationContext
            +
    Metadata Identity
            ↓
    RuntimeResolver
            ↓
    Resolved Runtime Object Type

Phase 4 must not turn RuntimeResolver into an unrestricted object lifecycle
manager.

In particular, RuntimeResolver must not become responsible for:

- persistence;
- repository management;
- object querying;
- configuration activation;
- storage access;
- document posting.

If Phase 4 requires separation between runtime type resolution and object
instance creation, that separation must be introduced through an explicit ADR.

---

# 14. Catalog Runtime Integration

Catalog is the first consumer of the generic Object Runtime model.

The existing Standard Configuration contains catalog definitions, including
Assortment.

The intended direction is:

    Assortment Definition
            ↓
    Catalog Metadata
            ↓
    Runtime Type Resolution
            ↓
    Catalog Object Instance

Catalog-specific runtime behavior must consume the generic Object Runtime
rather than establish an independent object model.

The generic object model therefore owns:

- Object Identity;
- Object State contract;
- Object Context;
- Object Lifecycle.

Catalog-specific functionality owns only catalog-specific semantics.

---

# 15. Object Registry

An Object Registry is NOT an assumed Phase 4 component.

Phase 4 must first determine whether object lookup, identity-to-instance
association, scoped lifetime, or other requirements justify a registry.

A registry must not be introduced merely because a registry is conceptually
possible.

If introduced, an Object Registry must not:

- create objects;
- persist objects;
- own configuration;
- replace RuntimeConfigurationBinding;
- become an implicit global state container.

The ownership model would be:

    Object Creation Boundary
             ↓
       Runtime Object
             ↓
       Object Registry
             ↓
    identity-based lookup

only if such lookup is explicitly required.

---

# 16. Storage Boundary

Storage remains outside the Object Runtime.

The architectural boundary is:

    Object Runtime
          │
          │ runtime state
          ▼
    Storage Boundary
          │
          ▼
    Persistent Representation

Object Runtime must not depend on:

- database implementation;
- filesystem implementation;
- SQL;
- ORM;
- storage provider;
- repository implementation.

Storage may depend on the object persistence contract defined by the
architecture, but Object Runtime must remain storage-independent.

---

# 17. Persistence Independence

The following concepts are explicitly distinct:

    Object Instance
    Object Runtime State
    Persistent Representation

They must not be collapsed into one abstraction.

An object may exist:

- before persistence;
- independently of persistence;
- during persistence;
- after being loaded from persistence.

The exact persistence lifecycle is deferred to Storage Architecture.

---

# 18. Object References

Object references are not fully implemented by Phase 4.

However, Object Identity must be suitable for future references.

Future architecture may support:

    Object Identity A
          ↓
    Object Reference
          ↓
    Object Identity B

References must not require embedding the complete target object.

Reference resolution semantics are deferred unless explicitly required by
the Phase 4 implementation slice.

---

# 19. Generic Runtime Principle

Phase 4 must preserve the project principle:

> Generic Runtime Over Object-Specific Code.

The runtime must provide generic capabilities for:

- object identity;
- object state;
- object context;
- object lifecycle;
- object creation.

Catalog-specific and document-specific implementations must consume those
capabilities.

The architecture must avoid:

    CatalogRuntime
    DocumentRuntime
    PartnerRuntime
    EmployeeRuntime

becoming independent runtime frameworks.

Instead:

    Generic Object Runtime
          ↑
       Catalog
          ↑
      Assortment

and later:

    Generic Object Runtime
          ↑
       Document
          ↑
    Goods Receipt

---

# 20. Configuration Boundary Invariant

Object Runtime must consume configuration but must not own configuration
lifecycle.

The ownership remains:

    ConfigurationLoader
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

Object Runtime consumes the resulting context.

It must not:

- load configuration;
- validate configuration;
- activate configuration;
- mutate active configuration.

---

# 21. Metadata Boundary Invariant

Object Runtime must consume resolved metadata through the established
runtime resolution boundary.

The preferred dependency direction remains:

    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Object Runtime

Object Runtime must not bypass these boundaries to access:

- MetadataRegistry;
- ConfigurationLoader;
- ConfigurationActivator;
- physical configuration storage.

---

# 22. Snapshot Semantics

A runtime object created under a particular Runtime Configuration Context
must preserve the configuration semantics of that context.

For example:

    Context V1
       ↓
    Object A

Later:

    Context V2
       ↓
    Object B

Object A must not silently switch to V2 because V2 became the currently
published configuration.

This preserves the snapshot semantics established by Phase 3.

---

# 23. Error Semantics

Phase 4 must distinguish at least the following classes of failure:

### Object Type Resolution Failure

The requested metadata identity cannot be resolved to a supported runtime
object type.

### Object Creation Failure

A resolved runtime type cannot produce a valid object instance.

### Invalid Object State

The requested object state violates object-level invariants.

### Invalid Lifecycle Operation

An operation is attempted in an invalid lifecycle state.

### Invalid Context

The object is invoked without a valid required runtime context.

### Persistence Failure

Persistence-related failures are outside the Object Runtime and belong to
Storage.

Errors must not collapse unrelated architectural failures into one generic
exception.

---

# 24. Ownership Model

Phase 4 ownership is:

| Concern | Owner |
|---|---|
| Configuration definition | Configuration |
| Configuration validation | Configuration |
| Configuration activation | Configuration |
| Published configuration | Runtime Configuration Binding |
| Runtime configuration snapshot | Runtime Configuration Context |
| Metadata resolution | Metadata Resolver |
| Runtime type resolution | Runtime Resolver |
| Object instance creation | Object Runtime creation boundary |
| Object identity | Object Runtime |
| Object runtime state | Object Runtime |
| Object lifecycle | Object Runtime |
| Object context | Object Runtime |
| Persistence | Storage |
| Document semantics | Document/Object layer |
| Posting | Posting |
| Registers | Register |
| Valuation | Valuation |
| Reporting | Reporting |

---

# 25. Architectural Invariants

Phase 4 establishes the following invariants.

## P4-I1 — Object Identity Independence

Object Identity is distinct from Metadata Identity and Configuration Identity.

## P4-I2 — Object Identity Immutability

Object Identity does not change during the lifetime of an Object Instance.

## P4-I3 — Object Type / Instance Separation

An Object Type may have multiple Object Instances.

## P4-I4 — Runtime State / Persistence Separation

Runtime Object State is not itself a persistence mechanism.

## P4-I5 — Explicit Object Context

Object operations receive or own an explicit runtime context.

## P4-I6 — Configuration Snapshot Preservation

Object Runtime respects the Runtime Configuration Context supplied to the
operation/object.

## P4-I7 — Configuration Ownership Preservation

Object Runtime does not load, validate, activate, or mutate configuration.

## P4-I8 — Metadata Boundary Preservation

Object Runtime does not bypass MetadataResolver / RuntimeResolver boundaries.

### Runtime Object Type Boundary

Object Runtime consumes Runtime Object Types through the
`RuntimeObjectType` architectural contract.

The contract is intentionally independent from concrete Runtime
implementations. `RuntimeResolver` produces resolved `RuntimeObjectType`
instances, while Object Runtime consumes them through the published
contract.

The dependency is therefore:

```text
RuntimeResolver
      │
      ▼
RuntimeObjectType
      │
      ▼
Object Runtime
```

and not a dependency on a concrete implementation such as CatalogRuntime.

Object Runtime MUST NOT import or otherwise require a concrete Runtime Object
Type implementation.

A concrete implementation such as CatalogRuntime MAY implement
RuntimeObjectType and MAY be used by integration or vertical-slice tests,
but it is not part of the generic Object Runtime dependency boundary.

This ensures that the generic Object Runtime remains reusable for future
catalog, document, reference-data and other Runtime Object Type
implementations.

## P4-I9 — Storage Independence

Object Runtime does not depend on physical persistence.

## P4-I10 — Generic Runtime

Catalog and future document objects consume generic Object Runtime
capabilities.

## P4-I11 — Lifecycle Ownership

Object lifecycle is owned by Object Runtime and is distinct from
configuration lifecycle and persistence lifecycle.

## P4-I12 — Creation Ownership

Object instance creation has one explicit architectural owner.

## P4-I13 — No Implicit Global Object State

Object Runtime must not require an implicit global registry or current-object
state.

## P4-I14 — No Premature Registry

An Object Registry is introduced only when an explicit runtime requirement
justifies it.

---

# 26. Non-Goals

Phase 4 does NOT implement:

- persistent storage;
- storage providers;
- repositories;
- CRUD APIs;
- query engine;
- document processing;
- posting;
- register facts;
- valuation;
- reporting;
- security;
- integration;
- UI;
- transaction engine;
- generalized behavior/scripting engine;
- distributed object identity;
- caching;
- synchronization;
- event sourcing.

These remain future architectural or implementation work.

---

# 27. ADR Candidates

Phase 4 should produce explicit ADRs for decisions that cannot be safely
left implicit.

At minimum:

### ADR-P4-01 — Object Instance Model

Defines the canonical Object Instance abstraction and its relationship to
runtime type, identity, state and context.

### ADR-P4-02 — Object Identity

Defines Object Identity semantics and its separation from metadata and
persistence identity.

### ADR-P4-03 — Runtime Type Resolution vs Object Creation

Defines the responsibility boundary between RuntimeResolver and object
instance creation.

### ADR-P4-04 — Object Lifecycle

Defines creation, activation, active state and disposal semantics.

### ADR-P4-05 — Object Context

Defines the relationship between Object Context and
RuntimeConfigurationContext.

### ADR-P4-06 — Object State and Persistence Boundary

Defines runtime state without coupling Object Runtime to Storage.

### ADR-P4-07 — Object Registry

Only if inventory and implementation requirements demonstrate that a registry
is required.

---

# 28. Implementation Strategy

Implementation must proceed from the generic boundary toward a representative
catalog object.

The preferred sequence is:

    Step 1
    Object Identity
          ↓
    Step 2
    Object Type / Instance Contract
          ↓
    Step 3
    Object State
          ↓
    Step 4
    Object Context
          ↓
    Step 5
    Object Lifecycle
          ↓
    Step 6
    Object Creation Boundary
          ↓
    Step 7
    Catalog Runtime Integration
          ↓
    Step 8
    End-to-end vertical slice

The implementation must not introduce Storage merely to demonstrate that an
object exists.

---

# 29. Phase 4 Vertical Slice

The minimum vertical slice is:

    Standard Configuration
            ↓
    Assortment Definition
            ↓
    Assortment Metadata
            ↓
    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Assortment Runtime Type
            ↓
    Object Creation Boundary
            ↓
    Assortment Object Instance
            ↓
    Object Identity
    Object State
    Object Context
    Object Lifecycle

The slice is successful when a real metadata-defined Standard Configuration
catalog can be instantiated as a valid executable Object Runtime instance.

Persistence is not required for the Phase 4 vertical slice.

---

# 30. Quality Gates

Phase 4 must not proceed to implementation completion unless:

### P4-QG1 — Object Contract

Object Instance, Object Type, Identity and State semantics are explicit.

### P4-QG2 — Context Boundary

Object Context is compatible with RuntimeConfigurationContext and does not
introduce an alternative configuration ownership model.

### P4-QG3 — Lifecycle

Object lifecycle states and legal transitions are explicit.

### P4-QG4 — Creation Ownership

The owner of object instance creation is explicit.

### P4-QG5 — Storage Independence

Object Runtime has no dependency on physical persistence.

### P4-QG6 — Generic Runtime

Catalog-specific runtime code does not establish a separate object model.

### P4-QG7 — Phase 3 Compatibility

All Phase 3 invariants remain valid.

### P4-QG8 — Vertical Slice

A Standard Configuration catalog can be instantiated as an executable
Object Runtime instance.

---

# 31. Compatibility with Existing Architecture

Phase 4 preserves the established architectural sequence:

    Definition
        ↓
    Metadata
        ↓
    Configuration
        ↓
    Runtime Resolution
        ↓
    Object Runtime
        ↓
    Storage
        ↓
    Documents / Posting / Registers
        ↓
    Valuation
        ↓
    Reporting

Phase 4 does not redefine:

- configuration lifecycle;
- metadata compilation;
- metadata publication;
- runtime configuration binding;
- runtime configuration context;
- metadata resolution.

It extends the final boundary established by Phase 3.

---

# 32. Architectural Risks

## R1 — RuntimeResolver Becomes Too Powerful

If RuntimeResolver owns resolution, creation, lifecycle and persistence, the
runtime boundary collapses.

Mitigation:

Keep runtime type resolution distinct from object lifecycle ownership.

## R2 — Catalog-Specific Runtime

CatalogRuntime could become a special-case object implementation.

Mitigation:

Use Catalog as the first consumer of the generic Object Runtime.

## R3 — Persistence Leakage

Object Runtime could become coupled to Storage.

Mitigation:

Keep runtime state and persistent representation separate.

## R4 — Global Object Registry

A registry could become implicit global state.

Mitigation:

Registry is optional and requires explicit justification.

## R5 — Identity Conflation

Metadata identity could be reused as object instance identity.

Mitigation:

Maintain separate identity domains.

## R6 — Context Conflation

Object Context could become an alternative configuration mechanism.

Mitigation:

RuntimeConfigurationContext remains the authoritative configuration
snapshot.

## R7 — Premature Generalization

Phase 4 could attempt to implement the complete Object Architecture.

Mitigation:

Implement only the minimum generic runtime contract required by the
vertical slice.

---

# 33. Relationship to Future Phases

Phase 4 enables:

    Object Runtime
          │
          ├───────────────→ Storage
          │
          ├───────────────→ Catalog Persistence
          │
          └───────────────→ Documents

Future document execution becomes:

    Document Definition
          ↓
    Document Metadata
          ↓
    Runtime Object Type
          ↓
    Document Object Instance
          ↓
    Document Lifecycle
          ↓
    Posting

Storage becomes:

    Object Runtime State
          ↓
    Persistence Boundary
          ↓
    Storage Provider

Posting remains downstream from document/business operation semantics.

---

# 34. Exit Condition

Phase 4 is architecturally complete when:

1. Object Instance semantics are explicitly defined.
2. Object Identity is explicitly defined.
3. Object State semantics are explicitly defined.
4. Object Context is explicitly defined.
5. Object Lifecycle is explicitly defined.
6. Object creation ownership is explicit.
7. RuntimeResolver responsibility remains bounded.
8. Storage independence is preserved.
9. Catalog Runtime consumes the generic Object Runtime.
10. Phase 3 invariants remain valid.
11. The Phase 4 vertical slice is executable.
12. All Phase 4 quality gates are closed.

---

# 35. Final Architectural Statement

Phase 4 establishes the following architectural principle:

> Metadata defines what an object is.
> Runtime resolves how that object type is executed.
> Object Runtime owns the lifetime and runtime state of an object instance.
> Future Storage Architecture will define how Object State is persisted and mapped to a persistent representation.
Persistence is outside the scope of Phase 4 implementation. Object Runtime does not depend on persistence.
> Configuration owns configuration lifecycle.

The canonical boundary is therefore:

    Configuration
          ↓
    Runtime Configuration Context
          ↓
    Metadata Resolution
          ↓
    Runtime Type Resolution
          ↓
    Object Runtime
          ↓
    Storage

The Object Runtime is the first layer in AcCoreD that represents an individual
business object instance.

It must remain generic, explicit, configuration-aware, metadata-driven and
storage-independent.

This boundary is the foundation for future Catalog, Document, Posting and
other business capabilities.

---

# Phase 4 Implementation Alignment

The accepted Phase 4 architecture is now partially implemented.

The current implementation establishes:

- `CatalogRuntime` as the Runtime Object Type for the catalog vertical slice;
- `ObjectInstance` as the individual runtime object;
- immutable Object Identity using `foundation.Identifier`;
- immutable `ObjectContext` retaining `RuntimeConfigurationContext`;
- `ObjectState.CREATED`, `ACTIVE`, and `DISPOSED`;
- explicit `ObjectLifecycle` transition rules;
- `ObjectCreator` as the sole Object Instance creation boundary;
- RuntimeResolver as a type resolver only;
- no Object Registry;
- no Storage dependency in Object Runtime creation or lifecycle.

The remaining Phase 4 work is documentation alignment, full regression, and final architectural audit.
