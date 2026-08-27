# ADR-P4-01 — Object Instance Model

**Status:** Accepted  
**Date:** 2026-08-27  
**Phase:** 4 — Object Runtime  
**Decision Type:** Architectural

---

## Context

Phase 3 established the runtime resolution pipeline:

    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Runtime Object

Phase 3 intentionally established only the minimum executable runtime
representation required by the vertical slice.

The architecture now requires an explicit definition of what an individual
runtime object instance is.

The following concepts must remain distinct:

- metadata definition;
- metadata identity;
- runtime object type;
- object instance;
- object state;
- object identity;
- runtime context;
- persistent representation.

Without this distinction, future Catalog and Document implementations could
create independent object models.

---

## Decision

AcCoreD defines `Object Instance` as the canonical runtime representation of
one individual business object.

An Object Instance consists conceptually of:

    Object Instance
        ├── Object Identity
        ├── Object Type
        ├── Object State
        └── Object Context

The exact Python class structure is an implementation detail.

The architectural relationship is:

    Metadata Definition
            ↓
    Metadata Type
            ↓
    Runtime Object Type
            ↓
    Object Instance

One Object Type may produce multiple Object Instances.

---

## Object Type vs Object Instance

An Object Type represents the executable semantics associated with a
metadata-defined type.

An Object Instance represents one individual object of that type.

Therefore:

    Object Type
        ≠
    Object Instance

and:

    Object Type
        ├── Instance A
        ├── Instance B
        └── Instance C

is valid.

---

## Object Instance Responsibilities

The Object Runtime owns:

- object identity;
- runtime object state;
- object lifecycle;
- object runtime context;
- execution of object-level runtime behavior.

It does not own:

- configuration lifecycle;
- metadata compilation;
- physical persistence;
- storage provider selection;
- posting;
- register facts;
- reporting.

---

## Metadata Relationship

Object Instances derive their structural and semantic definition from
resolved metadata.

Object Instances must not mutate metadata definitions.

Therefore:

    Metadata
       ↓
    defines
       ↓
    Object Type
       ↓
    instantiated as
       ↓
    Object Instance

---

## Storage Relationship

An Object Instance is a runtime concept.

Its existence does not imply persistence.

Therefore:

    Object Instance
          ≠
    Persistent Record

Persistence is handled through the Storage boundary.

---

## Consequences

### Positive

- establishes one generic object model;
- prevents Catalog and Document from inventing independent instance models;
- provides a stable target for RuntimeResolver integration;
- preserves storage independence;
- makes object lifecycle explicit.

### Negative

- introduces an abstraction that may initially be thin;
- some existing runtime classes may require later refactoring;
- object behavior beyond the minimum runtime contract remains future work.

---

## Invariants

1. Object Type and Object Instance are distinct.
2. One Object Type may have multiple Object Instances.
3. Object Identity belongs to the instance, not the metadata type.
4. Object State belongs to the instance, not the metadata definition.
5. Object Instance does not own physical persistence.
6. Object Instance consumes explicit runtime context.
7. Object Instance does not own configuration lifecycle.

---

## Rejected Alternatives

### Metadata object as object instance

Rejected because one metadata definition may have many runtime instances.

### Persistent record as object instance

Rejected because persistence belongs to Storage Architecture.

### Separate object model per business subsystem

Rejected because it violates the Generic Runtime principle.

---

## Related Decisions

- ADR-P4-02 — Object Identity
- ADR-P4-03 — Runtime Type Resolution vs Object Creation
- ADR-P4-04 — Object Lifecycle
- ADR-P4-05 — Object Context
- ADR-P4-06 — Object State & Storage Boundary

# ADR-P4-02 — Object Identity

**Status:** Accepted  
**Date:** 2026-08-27  
**Phase:** 4 — Object Runtime  
**Decision Type:** Architectural

---

## Context

AcCoreD already distinguishes configuration identity, configuration version
and metadata identity.

Object Runtime requires identity for individual business object instances.

Reusing metadata identity for object instances would prevent multiple
instances of one object type from being represented correctly.

---

## Decision

Every Object Instance has a distinct immutable Object Identity.

Object Identity is separate from:

- Configuration Identity;
- Configuration Version;
- Metadata Identity;
- Object Type Identity;
- physical storage identity.

Conceptually:

    Metadata Identity
        = "Assortment"

    Object Instance A
        = Object Identity ULID-A

    Object Instance B
        = Object Identity ULID-B

Both instances may have the same Object Type while having different Object
Identities.

---

## Identity Model

The project-wide ULID identity model is retained.

Object Identity therefore uses ULID-compatible identity semantics.

Object Identity is:

- unique;
- immutable;
- stable during object lifetime;
- independent of object state;
- independent of physical storage.

---

## Identity Assignment

Object Identity is assigned when the Object Instance is created.

Creation therefore establishes:

    Object Type
        +
    Object Identity
        +
    Initial State
        +
    Object Context

The exact implementation mechanism for ULID generation is an implementation
detail.

---

## Persistence Independence

Object Identity exists independently from persistence.

An object may receive its identity before being persisted.

Persistence may store or map that identity, but does not define its semantic
meaning.

---

## Identity Scope

Object Identity must be globally unique within the AcCoreD object identity
model.

No business object type may redefine the identity semantics for its own
instances.

---

## Immutability

Once assigned, Object Identity must never change.

Operations such as:

- state mutation;
- persistence;
- reload;
- lifecycle transition;

must not replace Object Identity.

---

## Consequences

### Positive

- clean separation of metadata and instance identity;
- supports multiple instances of one type;
- supports future object references;
- compatible with ULID architecture;
- independent from Storage.

### Negative

- introduces an additional identity concept;
- future persistence mappings must explicitly preserve object identity.

---

## Rejected Alternatives

### Metadata identity as instance identity

Rejected because metadata identifies a type, not an individual instance.

### Database primary key as Object Identity

Rejected because Object Runtime must remain independent of Storage.

### Business-specific natural keys

Rejected as the generic identity model.

Natural/business keys may exist as object state or business attributes, but
they do not replace Object Identity.

---

## Invariants

1. Every Object Instance has exactly one Object Identity.
2. Object Identity is immutable.
3. Object Identity is distinct from Metadata Identity.
4. Object Identity is distinct from Configuration Identity.
5. Object Identity does not depend on physical persistence.
6. Object Identity follows the project ULID identity model.

---

## Related Decisions

- ADR-P4-01 — Object Instance Model
- ADR-P4-04 — Object Lifecycle
- ADR-P4-06 — Object State & Storage Boundary

# ADR-P4-03 — Runtime Type Resolution vs Object Creation

**Status:** Accepted  
**Date:** 2026-08-27  
**Phase:** 4 — Object Runtime  
**Decision Type:** Architectural

---

## Context

Phase 3 introduced `RuntimeResolver`.

Its responsibility is to resolve metadata into a supported executable runtime
representation.

Phase 3 explicitly did not introduce a generalized runtime factory framework.

Phase 4 now requires Object Instance creation.

Without an explicit boundary, RuntimeResolver could gradually become
responsible for:

- type resolution;
- object creation;
- lifecycle;
- persistence;
- registry;
- business behavior.

This would collapse distinct architectural responsibilities.

---

## Decision

Runtime type resolution and Object Instance creation are separate
architectural responsibilities.

The conceptual flow is:

    RuntimeConfigurationContext
            ↓
    MetadataResolver
            ↓
    RuntimeResolver
            ↓
    Runtime Object Type
            ↓
    Object Creation Boundary
            ↓
    Object Instance

`RuntimeResolver` owns type resolution.

The Object Runtime creation boundary owns object instance creation.

---

## RuntimeResolver Responsibility

RuntimeResolver answers:

> Which executable runtime object type corresponds to this metadata identity
> in this runtime configuration context?

It may:

- resolve metadata;
- validate supported runtime type;
- identify the runtime object type;
- provide the runtime type required for creation.

It does not own:

- object lifecycle;
- persistent state;
- repositories;
- global object registry;
- configuration activation.

---

## Object Creation Responsibility

The Object Runtime creation boundary answers:

> How is an Object Instance of this resolved runtime type created?

Creation establishes:

- Object Identity;
- Object Type;
- initial Object State;
- Object Context;
- initial lifecycle state.

---

## API Shape

The architecture does not mandate the name or exact class structure of the
creation mechanism.

Possible implementation forms include:

- ObjectFactory;
- ObjectCreator;
- type-bound `create()` capability;
- another explicit creation abstraction.

The implementation must preserve the architectural separation.

---

## Resolver Must Not Become a Global Factory

The following architecture is rejected:

    RuntimeResolver
        ├── resolve()
        ├── create()
        ├── save()
        ├── load()
        ├── register()
        └── dispose()

Instead:

    RuntimeResolver
        ↓
    Runtime Type
        ↓
    Creation Boundary
        ↓
    Object Instance
        ↓
    Lifecycle

---

## Catalog Compatibility

Existing `CatalogRuntime` may remain the initial executable runtime
representation.

Phase 4 may refactor its role as necessary, but the refactoring must preserve
the Phase 3 contract.

The first consumer of the generic creation boundary is the Standard
Configuration catalog / Assortment path.

---

## Consequences

### Positive

- preserves Phase 3 responsibility boundaries;
- prevents RuntimeResolver from becoming a god object;
- enables future Catalog and Document object creation;
- leaves implementation form open.

### Negative

- introduces an additional conceptual boundary;
- may require refactoring of the current `CatalogRuntime` construction path.

---

## Rejected Alternatives

### RuntimeResolver creates and owns all objects

Rejected because resolution and lifecycle are different responsibilities.

### Metadata classes construct their own runtime instances

Rejected because metadata is declarative and must not own runtime lifecycle.

### Storage creates runtime objects

Rejected because persistence must remain downstream from Object Runtime.

---

## Invariants

1. RuntimeResolver resolves runtime type.
2. Object Runtime owns object instance creation.
3. RuntimeResolver does not own object lifecycle.
4. Object creation does not imply persistence.
5. Object creation uses explicit runtime context.
6. No generalized global factory framework is required unless future
   requirements justify it.

---

## Related Decisions

- ADR-P4-01 — Object Instance Model
- ADR-P4-02 — Object Identity
- ADR-P4-04 — Object Lifecycle
- ADR-P4-05 — Object Context

# ADR-P4-04 — Object Lifecycle

**Status:** Accepted  
**Date:** 2026-08-27  
**Phase:** 4 — Object Runtime  
**Decision Type:** Architectural

---

## Context

Object lifecycle is an explicit responsibility of Object Architecture.

It must remain distinct from:

- Configuration Lifecycle;
- runtime configuration publication;
- persistence lifecycle;
- business document lifecycle.

Phase 4 requires a minimal lifecycle sufficient for executable Object
Instances.

---

## Decision

Phase 4 defines the following generic Object Runtime lifecycle:

    create → Created
    Created → Active
    Active → Disposed

Object creation produces an Object Instance in the Created state.
Transition to Active is a separate lifecycle operation.

Disposed objects cannot be used for normal runtime operations.

---

## Created

The Created state means:

- Object Identity exists;
- Object Type is known;
- initial Object State exists;
- Object Context exists;
- the object has not yet been disposed.

Creation does not imply persistence.

---

## Active

The Active state means:

- object operations are permitted;
- object state may be changed according to object semantics;
- the object participates in normal runtime execution.

---

## Disposed

The Disposed state means:

- the runtime lifetime of the object has ended;
- normal object operations are prohibited.

Disposal does not mean:

- deletion from Storage;
- cancellation of a business document;
- deletion of business data.

---

## Configuration Lifecycle Independence

Object lifecycle must not be confused with configuration lifecycle.

For example:

    Configuration Candidate
        → Validated
        → Active
        → Retired

is a different lifecycle from:

    Object Instance
        → Created
        → Active
        → Disposed

Object Runtime does not activate configurations.

---

## Persistence Independence

Object lifecycle does not define persistence lifecycle.

For example:

    Object Created
        ↓
    Object Active
        ↓
    Object Persisted

or:

    Object Created
        ↓
    Object Active
        ↓
    Object Disposed

may both be valid.

Storage semantics are defined separately.

---

## Lifecycle Ownership

Object Runtime owns runtime object lifecycle.

Business-specific lifecycle may extend this model in future phases.

For example, a Document may eventually define:

    Draft
      ↓
    Posted
      ↓
    Cancelled

but such business lifecycle is not part of the generic Object Runtime
lifecycle.

---

## Consequences

### Positive

- clear ownership;
- avoids configuration/object lifecycle conflation;
- allows future business-specific lifecycle models;
- preserves storage independence.

### Negative

- generic lifecycle is intentionally minimal;
- future business objects may require additional lifecycle semantics.

---

## Invariants

1. Every Object Instance has a defined lifecycle state.
2. Disposed objects cannot be normally operated.
3. Object lifecycle is independent from configuration lifecycle.
4. Object lifecycle is independent from persistence lifecycle.
5. Generic Object Runtime does not define business-specific document states.

---

## Related Decisions

- ADR-P4-01 — Object Instance Model
- ADR-P4-03 — Runtime Type Resolution vs Object Creation
- ADR-P4-05 — Object Context
- ADR-P4-06 — Object State & Storage Boundary

# ADR-P4-05 — Object Context

**Status:** Accepted  
**Date:** 2026-08-27  
**Phase:** 4 — Object Runtime  
**Decision Type:** Architectural

---

## Context

Phase 3 established `RuntimeConfigurationContext` as an immutable explicit
snapshot of runtime configuration.

Object Runtime requires contextual information for object execution.

A new independent configuration mechanism must not be introduced.

---

## Decision

Object Runtime uses an explicit Object Context.

Object Context contains or references the `RuntimeConfigurationContext`
required by the object.

Conceptually:

    Object Context
        ├── RuntimeConfigurationContext
        └── Object Runtime Context

The exact implementation structure is deferred.

---

## Configuration Authority

`RuntimeConfigurationContext` remains the authoritative configuration
snapshot.

Object Context must not:

- query RuntimeConfigurationBinding;
- select the current configuration;
- activate configuration;
- mutate configuration.

---

## Context Snapshot

An Object Instance created with configuration context `V1` remains associated
with the semantics of `V1`.

A later active configuration `V2` must not silently replace the context of an
existing object operation.

---

## Context vs Object State

Object Context is not Object State.

Object State represents the state of the object.

Object Context represents the environment in which the object executes.

Therefore:

    Object State
        ≠
    Object Context

---

## Context vs Configuration Lifecycle

Object Context does not own configuration lifecycle.

The configuration lifecycle remains:

    Candidate
      ↓
    Validate
      ↓
    Activate
      ↓
    ActiveConfiguration
      ↓
    RuntimeConfigurationContext

Object Runtime consumes the resulting context.

---

## Explicit Context Passing

Object operations should receive the relevant context explicitly rather than
discovering it implicitly from global runtime state.

This preserves the Phase 3 snapshot and testability principles.

---

## Consequences

### Positive

- preserves Phase 3 context architecture;
- prevents hidden global configuration dependencies;
- enables deterministic object execution;
- supports multiple configuration snapshots.

### Negative

- context may need to be threaded through several APIs;
- exact object-context contents may grow in future phases.

---

## Invariants

1. Object Context is explicit.
2. RuntimeConfigurationContext remains authoritative for configuration.
3. Object Context does not activate configuration.
4. Object Context does not access physical storage directly.
5. Object State and Object Context remain distinct.
6. Existing objects do not silently switch configuration snapshots.

---

## Rejected Alternatives

### Object reads current active configuration globally

Rejected because it violates Phase 3 snapshot semantics.

### Object owns configuration lifecycle

Rejected because Configuration Architecture owns activation.

### Object Context as mutable global service locator

Rejected because it would introduce hidden dependencies.

---

## Related Decisions

- Phase 3 Runtime Configuration Context
- ADR-P4-01 — Object Instance Model
- ADR-P4-03 — Runtime Type Resolution vs Object Creation
- ADR-P4-04 — Object Lifecycle

# ADR-P4-06 — Object State & Storage Boundary

**Status:** Accepted  
**Date:** 2026-08-27  
**Phase:** 4 — Object Runtime  
**Decision Type:** Architectural

---

## Context

AcCoreD defines Storage Architecture as the owner of physical persistence.

Object Runtime requires state for executable object instances.

If runtime state and persistent representation are treated as the same
abstraction, Object Runtime becomes coupled to Storage.

This would violate the existing architectural separation.

---

## Decision

Object Runtime owns the semantic runtime state of an Object Instance.

Storage owns persistent representation of object state.

The conceptual boundary is:

    Object Instance
          │
          ▼
    Runtime Object State
          │
          ▼
    Persistence Boundary
          │
          ▼
    Persistent Representation

---

## Runtime Object State

Runtime Object State represents values and runtime state belonging to an
individual object instance.

It may include:

- metadata-defined attributes;
- runtime-managed values;
- object-level state required for execution.

The exact state model is implementation-defined within the constraints of
this ADR.

---

## Persistent Representation

Persistent Representation is a Storage concern.

It may use:

- relational storage;
- document storage;
- files;
- another storage provider.

Object Runtime must not depend on the physical representation.

---

## State Synchronization

Phase 4 does not define a persistence synchronization protocol.

In particular, Phase 4 does not establish:

- Unit of Work;
- repository pattern;
- dirty tracking;
- automatic persistence;
- transactions;
- optimistic locking;
- change tracking.

Those are future architectural decisions.

---

## State Mutation

Object Runtime may mutate runtime state according to object semantics.

Such mutation does not automatically persist the object.

Persistence requires an explicit future Storage/Object persistence boundary.

---

## Loading

Loading a persisted representation into an Object Instance is outside the
minimum Phase 4 implementation.

Future loading must reconstruct:

- Object Identity;
- Object Type;
- Object State;
- appropriate Object Context.

The loading mechanism belongs to the future persistence architecture.

---

## Consequences

### Positive

- preserves Storage independence;
- enables in-memory object execution;
- prevents ORM/database concepts from leaking into Object Runtime;
- leaves persistence architecture open.

### Negative

- persistence is intentionally incomplete;
- future phases must define state synchronization.

---

## Invariants

1. Runtime Object State is distinct from persistent representation.
2. Object Runtime does not depend on a storage provider.
3. State mutation does not imply persistence.
4. Object Identity survives persistence mapping.
5. Persistence semantics are owned by Storage Architecture.
6. Phase 4 does not introduce repositories or transactions.

---

## Rejected Alternatives

### Object directly owns a database record

Rejected because it couples Object Runtime to Storage.

### Every state mutation is automatically persisted

Rejected because persistence semantics belong to a future architecture.

### ORM entity as the canonical Object Instance

Rejected because the Object Runtime must remain storage-independent.

---

## Related Decisions

- ADR-P4-01 — Object Instance Model
- ADR-P4-02 — Object Identity
- ADR-P4-04 — Object Lifecycle
- Storage Architecture

