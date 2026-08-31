# Object Model

**Version:** 1.1
**Status:** Architecture Specification
**Phase:** 4 — Object Runtime
**Architecture Baseline:** `architecture-core-3.0`

---

# 1. Purpose

This document defines the canonical Object Runtime model of AcCoreD.

The Object Model establishes the distinction between:

- Metadata;
- Metadata Identity;
- Runtime Object Type;
- Object Instance;
- Object Identity;
- Object State;
- Object Context;
- Object Lifecycle;
- Persistent Representation.

The purpose is to provide one generic model for individual runtime business
objects without coupling Object Runtime to physical persistence.

---

# 2. Architectural Position

The Object Model is positioned between runtime type resolution and future
persistence.

The canonical flow is:

```text
Configuration
      ↓
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
      ↓
Future Persistence Boundary
      ↓
Storage

Object Runtime owns the individual runtime object.

It does not own:

configuration activation;
metadata compilation;
metadata resolution;
physical persistence;
global object registration.
3. Core Distinctions

The Object Model requires the following distinctions to remain explicit.

3.1 Metadata Identity vs Object Identity
Metadata Identity
      ≠
Object Identity

Metadata Identity identifies a metadata-defined type or definition.

Object Identity identifies one individual runtime Object Instance.

A metadata-defined type may therefore produce multiple objects:

Metadata Identity
      ↓
Runtime Object Type
      ↓
Object Instance A
      ↓
Object Instance B
      ↓
Object Instance C

The identity of the metadata definition must never be used as the identity
of an individual object instance.

3.2 Runtime Object Type vs Object Instance
Runtime Object Type
      ≠
Object Instance

A Runtime Object Type represents executable runtime semantics associated with
a resolved metadata-defined type.

An Object Instance represents one individual runtime entity of that type.

Therefore:

CatalogRuntime
      ↓
ObjectInstance A
ObjectInstance B
ObjectInstance C

is valid.

3.3 Object State vs Persistent State
Object State
      ≠
Persistent State

Object State belongs to the runtime object.

Persistent State belongs to the future persistence architecture.

An Object Instance can exist in runtime state without requiring Storage.

3.4 Object Lifecycle vs Configuration Lifecycle
Object Lifecycle
      ≠
Configuration Lifecycle

Object lifecycle operations affect individual Object Instances.

Configuration lifecycle operations affect runtime configuration snapshots.

Object lifecycle operations must not activate, deactivate, or otherwise
mutate configuration.

4. Object Instance

ObjectInstance is the canonical runtime representation of one individual
business object.

Conceptually:

ObjectInstance
    ├── Object Identity
    ├── Object Type
    ├── Object State
    └── Object Context

Object Lifecycle operates on the Object Instance but is a separate
responsibility.

The Object Instance does not itself become a persistence object.

5. Object Identity

Object Identity uniquely identifies an individual Object Instance.

AcCoreD reuses the existing immutable ULID-backed foundation.Identifier as
the technical representation of Object Identity.

No separate ObjectIdentity value type is required.

Architecturally:

Identifier
      ↓
Object Identity
      ↓
Object Instance

This reuse does not collapse Object Identity into Metadata Identity.

The same technical primitive may be used for different architectural
identity concepts while their semantics remain distinct.

Object Identity:

is immutable;
is independently constructible;
does not depend on Storage;
does not depend on MetadataRegistry;
does not represent Metadata Identity;
is not derived from Object State.
6. Object Type

An Object Instance is associated with one resolved Runtime Object Type.

The Runtime Object Type is produced by RuntimeResolver.

For the current vertical slice:

CatalogMetadata
      ↓
RuntimeResolver
      ↓
CatalogRuntime

CatalogRuntime represents a Runtime Object Type.

It does not represent an individual object.

7. Object State

Each Object Instance owns its runtime Object State.

The generic Object Runtime state model is:

CREATED
ACTIVE
DISPOSED

A newly created Object Instance always starts in CREATED.

The initial state is not selected by the caller.

Object State is independent from persistence and does not require Storage.

Object State is also not part of Object Instance identity semantics.

8. Object Context

Object Context represents the explicit runtime context under which an Object
Instance exists and operates.

The Object Context is associated with the Phase 3
RuntimeConfigurationContext.

The intended relationship is:

RuntimeConfigurationContext
        ↓
Object Context
        ↓
Object Instance

Object Context must preserve the configuration snapshot semantics established
by Phase 3.

Object Context must not:

activate configuration;
access configuration binding directly;
resolve metadata independently;
become a service locator;
become a second configuration lifecycle.
9. Object Lifecycle

Object Lifecycle defines the valid runtime transitions of an Object Instance.

The initial lifecycle is:

create
  ↓
CREATED
  ↓
ACTIVE
  ↓
DISPOSED

Creation establishes an Object Instance in CREATED.

Transition to ACTIVE is explicit.

Transition to DISPOSED is explicit.

Disposed objects cannot be used for normal runtime operations.

Lifecycle operations do not affect Configuration Lifecycle.

10. Object Creation Boundary

Runtime type resolution and object creation are separate responsibilities.

The canonical relationship is:

RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance

The Object Creation Boundary consumes an already resolved Runtime Object Type
and an Object Context.

Creation establishes:

Object Identity;
Object Type;
Object State;
Object Context;
CREATED lifecycle state.

Creation does not:

resolve metadata;
discover global configuration;
activate configuration;
access MetadataRegistry directly;
persist the object;
create a global object registry.
11. Object Runtime Dependencies

The intended dependency direction is:

runtime
   ↓
object

The Runtime package remains responsible for runtime type resolution and
runtime-level infrastructure.

The Object package owns individual Object Instance semantics.

The Object package must not independently:

resolve configuration;
resolve metadata through MetadataRegistry;
discover runtime configuration globally;
replace RuntimeResolver;
own configuration activation.
12. Object Instance Equality

Object Instance equality is based on Object Identity.

It is not based on:

Object Type;
Object State;
Object Context;
persistent representation.

Therefore:

Object Identity
      ↓
Object Instance Equality

and:

Object State
      ✕
Object Instance Equality

Two instances of the same Runtime Object Type are distinct unless they carry
the same Object Identity.

Two representations carrying the same Object Identity remain equal even if
their runtime state differs.

13. Object Instance Independence

Every Object Instance represents an individual runtime entity.

For example:

CatalogRuntime
   ├── ObjectInstance A
   │     ├── Identity A
   │     ├── State A
   │     └── Context A
   │
   ├── ObjectInstance B
   │     ├── Identity B
   │     ├── State B
   │     └── Context B
   │
   └── ObjectInstance C
         ├── Identity C
         ├── State C
         └── Context C

The Runtime Object Type may be shared.

Object Identity, runtime state, and object-specific context belong to the
individual Object Instance.

14. Storage Independence

An Object Instance is a runtime object, not a persistence record.

The following operation must be possible without Storage:

Resolve Runtime Object Type
        ↓
Create Object Instance
        ↓
Assign Object Identity
        ↓
Initialize Object State
        ↓
Bind Object Context

Physical persistence is a separate concern:

Object Runtime
      ↓
Future Persistence Boundary
      ↓
Storage

Object Runtime must therefore not depend directly on a Storage provider.

15. Object Runtime and Metadata

Object Runtime consumes resolved runtime types.

The resolution chain is:

Metadata Identity
      ↓
RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance

Object Instance must not directly access MetadataRegistry.

Metadata resolution remains a Runtime / Configuration concern.

16. Object Runtime and Configuration

Object Runtime consumes explicit runtime configuration context.

The canonical relationship is:

ActiveConfiguration
      ↓
RuntimeConfigurationContext
      ↓
Object Context
      ↓
Object Instance

Object Runtime does not own:

configuration definition;
configuration validation;
configuration activation;
runtime configuration binding.

Configuration snapshot semantics established by Phase 3 must remain intact.

An Object Instance must not silently switch to a different configuration
snapshot merely because the globally active configuration changes.

17. Catalog Vertical Slice

The first concrete consumer of the generic Object Model is the Standard
Configuration Assortment catalog.

The target flow is:

Standard Configuration
        ↓
Assortment Metadata
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
CatalogRuntime
        ↓
Object Creation Boundary
        ↓
Assortment ObjectInstance

Assortment-specific code consumes the generic Object Runtime.

It does not introduce:

a separate identity model;
a separate lifecycle model;
a separate context model;
a catalog-specific generic factory;
a catalog-specific registry.
18. Object Registry

The current Object Model does not require a global Object Registry.

Object Instances are created and operated through explicit references.

A registry must not be introduced merely because multiple objects can exist.

A future Object Registry may be introduced only when an explicit architectural
requirement demonstrates the need for centralized object discovery,
ownership, lifecycle coordination, or another justified capability.

Until then:

Object Creation
      ↓
Object Instance

is sufficient.

19. Persistence Boundary

The Object Model deliberately stops before physical persistence.

The boundary is:

Object Instance
      ↓
Future Persistence Boundary
      ↓
Persistent Representation
      ↓
Storage

Persistent Representation is not the Object Instance itself.

The persistence architecture may later define:

mapping;
serialization;
storage identity representation;
loading;
saving;
transactions;
concurrency;
versioning.

Those concerns are outside the Phase 4 Object Runtime model.

20. Explicit Non-Goals

The Object Model does not define:

repositories;
Unit of Work;
dirty tracking;
transactions;
query execution;
object registries;
persistence providers;
database schemas;
document posting;
register updates;
valuation;
reporting;
workflow engines.

These capabilities belong to later architectural layers.

21. Architectural Invariants

I1. Metadata Identity and Object Identity are distinct concepts.

I2. Runtime Object Type and Object Instance are distinct concepts.

I3. Every Object Instance has exactly one Object Identity.

I4. Every Object Instance is associated with one resolved Runtime Object
Type.

I5. Object Identity is represented technically by the existing immutable
foundation.Identifier.

I6. Object State does not define Object Identity.

I7. Object Instance equality is based on Object Identity.

I8. Object State is distinct from persistent state.

I9. Object Lifecycle is distinct from Configuration Lifecycle.

I10. Object Context uses explicit runtime configuration context.

I11. Object Runtime does not independently resolve configuration or access
MetadataRegistry.

I12. RuntimeResolver resolves Runtime Object Types and does not own
Object Instance creation.

I13. Object Creation has one explicit creation boundary.

I14. Object Runtime does not require Storage merely for an Object Instance
to exist.

I15. No global Object Registry is required by the current model.

I16. Catalog / Assortment consumes the generic Object Runtime model.

22. Implementation Correspondence

The current implementation consists conceptually of:

accore.platform.object
    ├── ObjectInstance
    ├── ObjectState
    ├── ObjectContext
    ├── ObjectLifecycle
    └── ObjectCreator

and:

accore.platform.runtime
    ├── RuntimeResolver
    └── CatalogRuntime

The package boundary reflects the architectural responsibility boundary.

runtime resolves runtime types.

object represents and operates on individual runtime objects.

23. Future Evolution

The Object Model is intentionally minimal.

Future capabilities may extend it through explicit architectural decisions.

Potential future concerns include:

persistent object mapping;
object references;
business operations;
documents;
posting;
registers;
valuation;
querying;
concurrency;
repositories;
Unit of Work.

Such extensions must preserve the distinctions and invariants established by
this model.

24. Conclusion

The AcCoreD Object Model establishes one generic runtime representation for
individual business objects.

The canonical model is:

Metadata Identity
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance
   ├── Object Identity
   ├── Object Type
   ├── Object State
   └── Object Context
        ↓
Object Lifecycle

with:

Object Identity
      ≠
Metadata Identity

Runtime Object Type
      ≠
Object Instance

Object State
      ≠
Persistent State

Object Lifecycle
      ≠
Configuration Lifecycle

This establishes the Object Runtime as the stable boundary between runtime
type resolution and future persistence or business-operation subsystems.