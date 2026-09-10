Phase 5 / Step 7 — Persistent Object Representation

Document: PHASE_5_PERSISTENT_OBJECT_REPRESENTATION.md
Phase: 5 — Storage & Persistence Boundary
Status: Final — Implemented
Version: 1.0
Previous Step: Step 6 — Persistence Implementation Boundary
Next Step: Finalized in Phase 5

# 1. Purpose

This document defines the canonical Persistent Object Representation for AcCoreD.

The purpose is to establish how the durable state of a business object is represented at the Persistence Boundary without coupling persistence to the Runtime Object implementation.

The Persistent Object Representation defines:

which parts of an Object Instance are durable;
how Object Identity is preserved;
how Object Type identity is represented;
how persistent object state is separated from runtime state;
how logical fields are represented;
how system-managed persistent state is distinguished from runtime state;
the relationship between Persistent Object and ObjectInstance;
the boundary between persistent representation and serialized payload;
invariants required by Object Persistence.

This document does not define:

a physical database schema;
filesystem layout;
SQL tables;
ORM entities;
serialization format;
indexes;
StorageKey structure;
StorageProvider implementation;
transaction mechanism;
concurrency mechanism.

# 2. Architectural Position

The Persistent Object Representation sits between the Object Runtime model and the physical Storage Boundary.

The canonical relationship is:

                 Object Runtime
                       │
                       │
                       ▼
                ObjectInstance
                       │
                       │ persistence mapping
                       ▼
             Persistent Object
                       │
                       │ representation encoding
                       ▼
                 Serialized Payload
                       │
                       ▼
                StorageProvider
                       │
                       ▼
                Physical Storage

These four representations must remain distinct.

ObjectInstance
      ≠
PersistentObject
      ≠
Serialized Payload
      ≠
Physical Storage

# 3. Core Principle

The central principle is:

A Persistent Object represents durable logical object state, not the runtime execution state of an Object Instance.

The persistence representation must therefore contain only information required to reconstruct the durable business state of the object and its persistence identity.

It must not capture runtime implementation details merely because they happen to exist on ObjectInstance.

# 4. Existing Object Runtime Model

The current Object Model defines ObjectInstance conceptually as:

ObjectInstance
    ├── Object Identity
    ├── Object Type
    ├── Object State
    └── Object Context

The current implementation is:

@dataclass(frozen=True, eq=False)
class ObjectInstance:
    identity: Identifier
    object_type: RuntimeObjectType
    context: ObjectContext
    state: ObjectState = ObjectState.CREATED

Object Identity is represented by the existing immutable ULID-backed Identifier. The architecture explicitly states that no separate ObjectIdentity value type is introduced.

The Object Model also explicitly distinguishes:

Object State
      ≠
Persistent State

and states that an Object Instance can exist in runtime without requiring Storage.

Therefore the Persistent Object Representation must not be defined as a serialization of ObjectInstance.

# 5. Persistent Object Concept

A Persistent Object is the durable representation of one logical business object.

Conceptually:

PersistentObject
    ├── Object Identity
    ├── Object Type Identity
    ├── Persistent State
    └── Persistent Fields

The exact concrete Python representation is an implementation concern of the Object Persistence boundary.

The architecture nevertheless defines the semantic components that representation must preserve.

# 6. Object Identity

Object Identity is mandatory for a Persistent Object.

The identity is the same logical identity established by Object Creation.

Object Creation
      │
      ▼
Object Identity
      │
      ├──────────────► ObjectInstance
      │
      └──────────────► PersistentObject

Persistence must preserve this identity.

It must not:

generate a new identity during restoration;
derive identity from business fields;
derive identity from StorageKey;
replace Object Identity with a storage-specific identifier.

The existing architecture explicitly states that Storage may preserve Object Identity but does not own runtime identity.

# 7. Object Type Identity

A Persistent Object must identify which metadata-defined object type it belongs to.

The persisted representation must not contain a concrete runtime object type instance such as:

CatalogRuntime(...)

Instead it preserves the identity of the metadata-defined type.

The current Runtime Object Type contract provides:

def metadata_identity(self) -> Identifier:
    ...

Therefore the conceptual mapping is:

ObjectInstance
    │
    └── RuntimeObjectType
            │
            └── metadata_identity()
                    │
                    ▼
             Object Type Identity
                    │
                    ▼
             PersistentObject

This is a critical separation.

The persistent representation stores identity of the type, not the runtime implementation of that type.

# 8. Runtime Object Type Is Not Persisted

The following must not become part of Persistent Object state:

RuntimeObjectType instance
CatalogRuntime instance
Runtime service references
Runtime resolver references
MetadataRegistry references
Python class identity
Runtime implementation details

For example, this is architecturally invalid:

PersistentObject(
    identity=...,
    object_type=CatalogRuntime(...),
    context=...,
)

because it makes persistence depend on runtime objects.

The valid conceptual form is:

PersistentObject(
    identity=...,
    object_type_identity=...,
    ...
)

The concrete representation remains to be defined.

# 9. Object Context Is Not Persistent State

ObjectContext is explicitly runtime context.

It contains:

ObjectContext(
    runtime_context=RuntimeConfigurationContext(...)
)

This information must not be persisted as part of the business object's durable state.

Therefore:

ObjectContext
      ≠
PersistentObject

The following must not be persisted:

RuntimeConfigurationContext;
ActiveConfiguration;
runtime service references;
runtime configuration snapshot objects;
runtime binding objects.

On restoration, an Object Instance receives an appropriate runtime context from the current execution environment.

# 10. Runtime State vs Persistent State

The current Object Runtime defines:

CREATED
ACTIVE
DISPOSED

These are runtime lifecycle states.

They are not automatically equivalent to persistent object state.

In particular:

ACTIVE

does not mean:

persistent state = ACTIVE

and:

DISPOSED

does not necessarily mean:

persistent object deleted

The two lifecycles must remain separate.

# 11. Persistent State

A Persistent Object may contain persistent business state required by its domain.

Examples may eventually include:

business fields
document fields
reference values
business lifecycle state
posting-related state
consistency-related state
system-managed persistent attributes

However, the exact set is determined by the Object Domain Model and relevant business configuration.

Step 7 therefore defines the category, not a premature universal schema.

# 12. Logical Fields

Persistent business fields must correspond to the Logical Field Model.

The architecture already establishes that Runtime and Metadata interact with Logical Fields while Storage determines physical persistence.

Therefore:

Logical Field
      │
      ▼
Persistent Object Representation
      │
      ▼
Storage implementation

A logical field must not be identified by:

SQL column name;
filesystem filename;
database-specific type;
EAV table name;
physical storage location.

Those are implementation details.

# 13. Metadata-Driven Field Representation

AcCoreD is metadata-driven.

Therefore a Persistent Object must be able to represent fields defined by the applicable metadata model without making the persistence contract depend on a fixed physical schema.

Conceptually:

Metadata Definition
       │
       ▼
Logical Fields
       │
       ▼
Persistent Object
       │
       ▼
Storage Representation

This does not require EAV.

EAV remains a possible Storage implementation detail and must not leak into Persistent Object semantics. The existing architecture explicitly treats EAV as a Storage implementation detail.

# 14. Persistent Representation vs Serialized Payload

The architecture requires three separate levels:

Persistent Object
      │
      │ encoding
      ▼
Serialized Payload
      │
      │ storage
      ▼
StorageProvider

For example, the architecture does not define:

PersistentObject = bytes

and does not define:

PersistentObject = dict[str, Any]

merely because one serializer may eventually use either representation.

The Persistent Object is a semantic representation.

Serialization is a separate technical operation.

# 15. No Physical Schema

Step 7 does not define:

table objects
column object_id
column object_type
column state
column fields

Nor does it define:

objects/<id>.json

Nor:

object:{type}:{id}

These are physical storage decisions.

The Persistent Object must remain valid regardless of whether the eventual implementation uses:

relational storage;
document storage;
key-value storage;
filesystem storage;
another provider.

# 16. Persistent Object Identity and Storage Identity

The architecture distinguishes:

Object Identity
      ≠
Storage Identity

The Persistent Object has Object Identity.

The Persistence Implementation maps it to a StorageKey.

Object Identity
      │
      ▼
Persistence Implementation
      │
      ▼
StorageKey

Therefore:

StorageKey

must not become a field of the Persistent Object itself.

# 17. Restoration

Restoring a runtime object from persistence is a reconstruction process.

Conceptually:

PersistentObject
      │
      ├── Object Identity
      ├── Object Type Identity
      ├── Persistent State
      └── Persistent Fields
              │
              ▼
       Runtime Resolution
              │
              ▼
       Runtime Object Type
              │
              ▼
        Object Context
              │
              ▼
        ObjectInstance

Restoration therefore requires runtime dependencies that are intentionally absent from Persistent Object.

This preserves the architecture:

Persistent Object
        ↓
Runtime reconstruction
        ↓
Object Instance

rather than:

Persistent Object
        ↓
deserialize ObjectInstance directly

# 18. Runtime Context During Restoration

A restored object must receive an explicit runtime context.

The Persistent Object does not store:

RuntimeConfigurationContext

Instead:

Persistence
     │
     ▼
PersistentObject
     │
     ▼
Object Restoration Boundary
     │
     ├── resolve object type
     ├── provide runtime context
     └── reconstruct ObjectInstance

This preserves the Phase 3 runtime configuration snapshot model.

# 19. Object Lifecycle During Restoration

Persistence restoration does not automatically imply that the restored object is immediately ACTIVE.

The Object Lifecycle remains responsible for runtime lifecycle transitions.

Therefore restoration must not silently bypass:

CREATED
    ↓
ACTIVE

unless a later Object Restoration contract explicitly defines such behavior.

Step 7 only establishes that persistence representation and runtime lifecycle state are distinct.

# 20. Persistent Deletion

Deletion of a Persistent Object is a persistence capability.

It does not imply that:

ObjectState == DISPOSED

nor does:

ObjectState == DISPOSED

automatically imply persistent deletion.

The two operations belong to different boundaries:

Object Lifecycle
      │
      └── dispose runtime object

Persistence
      │
      └── delete persistent object
# 21. Required Persistent Components

At the semantic level, a Persistent Object must provide:

## 21.1 Object Identity

Immutable logical identity.

## 21.2 Object Type Identity

Identity of the metadata-defined object type.

## 21.3 Persistent State

Domain-defined durable state.

## 21.4 Persistent Fields

Values of durable logical fields.

These are the minimum conceptual components.

No additional universal fields are introduced at Step 7.

# 22. What Is Explicitly Excluded

The Persistent Object Representation must not contain:

Runtime infrastructure
ObjectContext
RuntimeConfigurationContext
ActiveConfiguration
RuntimeObjectType instance
MetadataRegistry
RuntimeResolver
services
Physical storage details
StorageKey
filesystem path
filename
database table
database connection
row identifier
EAV location
Serialization details
JSON bytes
pickle bytes
MessagePack bytes
binary storage format
Transaction details
transaction
session
commit marker
rollback marker
lock
Provider details
StorageProvider instance
filesystem handle
database connection
provider-specific metadata

# 23. Persistent System Fields

The representation may eventually require system-managed persistent fields.

Examples could include:

created_at
updated_at
version
revision

However, Step 7 does not automatically introduce any of them.

This is intentional.

For example, a version field would imply a concurrency model. Concurrency has already been defined as contract-specific and not universal.

Therefore:

A system field enters Persistent Object Representation only when its semantic ownership and behavior have been explicitly defined by the relevant architecture.

# 24. Business Lifecycle State

A business object may eventually have a persistent business lifecycle state such as:

DRAFT
APPROVED
POSTED
CANCELLED

Such state is conceptually different from runtime:

CREATED
ACTIVE
DISPOSED

The distinction is:

Runtime Object Lifecycle
        ≠
Business Object Lifecycle

If business lifecycle state becomes persistent, it belongs to Persistent Object Representation as business state.

It must not be confused with ObjectState.

# 25. Posting-Related State

Persistence of accounting-related state requires additional care.

A Persistent Object may eventually need persistent state describing its accounting status, for example whether its posting effects are current or require restoration.

However:

Movement
MovementSet
Register Fact

remain Register/Posting concepts.

They do not become embedded inside a generic Persistent Object.

The relationship remains:

Persistent Object
       │
       │ participates in
       ▼
Posting
       │
       ▼
MovementSet
       │
       ▼
Register Facts

The object persistence representation does not replace Register Fact persistence.

# 26. Persistent Object Is Not a Snapshot of Runtime Object

This distinction is mandatory.

A runtime object may contain:

identity
runtime type
runtime context
runtime state
runtime services
temporary calculation state
cached values

A Persistent Object contains:

identity
type identity
durable business state
durable logical fields

Therefore:

PersistentObject

is a projection of durable state, not a complete runtime snapshot.

# 27. Mapping Rules

The canonical mapping is:

Runtime Object	Persistent Representation
identity	Object Identity
object_type.metadata_identity()	Object Type Identity
persistent business fields	Persistent Fields
persistent business state	Persistent State
object_type runtime instance	not persisted
context	not persisted
runtime_context	not persisted
runtime lifecycle state	not automatically persisted
runtime services	not persisted
caches / temporary state	not persisted
StorageKey	not part of representation

This table defines semantic mapping, not serialization.

# 28. Persistence Representation Lifecycle

The lifecycle of a Persistent Object is conceptually:

Runtime Object
      │
      ▼
Persistence Projection
      │
      ▼
Persistent Object
      │
      ▼
Encoded Payload
      │
      ▼
Storage

Restoration reverses this:

Storage
      │
      ▼
Encoded Payload
      │
      ▼
Persistent Object
      │
      ▼
Runtime Reconstruction
      │
      ▼
Runtime Object

# 29. Validation

A Persistent Object must be structurally valid before it reaches Storage.

Validation must establish at least:

Object Identity is present;
Object Type Identity is present;
persistent fields conform to the applicable representation;
persistent state conforms to the applicable domain rules;
no forbidden runtime-only state is embedded in the representation.

Invalid persisted data discovered during retrieval must be distinguishable from a missing object.

Conceptually:

missing object
      ↓
PersistenceNotFoundError

versus:

object exists
      ↓
representation invalid
      ↓
PersistenceIntegrityError

This follows the persistence error semantics already established in Phase 5.

# 30. Versioning

Step 7 does not introduce a universal persistence representation version.

A future representation migration mechanism may be required, but that is distinct from:

Object Identity
Object business version
Concurrency version
Configuration Version

These concepts must not be conflated.

If representation versioning becomes necessary, it must be explicitly defined as part of the persistence representation/migration architecture.

# 31. Compatibility

Persistent representation should be designed so that runtime implementation changes do not necessarily invalidate existing persistent state.

In particular, changing:

RuntimeObjectType implementation
ObjectContext implementation
Runtime services
Runtime resolver internals

must not inherently require rewriting persistent business state.

The persistent representation should depend on stable semantic identities and durable logical state.

# 32. Dependency Direction

The allowed dependency direction is:

Object Runtime
      │
      │ produces / consumes
      ▼
Persistent Object Representation
      │
      ▼
Persistence Implementation
      │
      ▼
StorageProvider

The reverse dependency is prohibited.

Storage must not require:

ObjectInstance
RuntimeObjectType
ObjectContext
RuntimeConfigurationContext

in order to store a payload.

# 33. Architectural Invariants

The following invariants are mandatory.

POR-INV-1 — Identity Preservation

Persistent Object preserves Object Identity.

POR-INV-2 — Type Identity Preservation

Persistent Object preserves the identity of the metadata-defined object type.

POR-INV-3 — Runtime Type Separation

Persistent Object does not contain a runtime RuntimeObjectType instance.

POR-INV-4 — Runtime Context Separation

Persistent Object does not contain ObjectContext or RuntimeConfigurationContext.

POR-INV-5 — Runtime State Separation

Runtime ObjectState is not automatically treated as Persistent State.

POR-INV-6 — Durable State Only

Persistent Object represents durable logical state.

POR-INV-7 — Logical Field Independence

Persistent fields are defined in terms of logical fields, not physical storage fields.

POR-INV-8 — Storage Identity Separation

StorageKey is not part of Persistent Object semantic identity.

POR-INV-9 — Serialization Separation

Persistent Object is distinct from serialized bytes.

POR-INV-10 — Provider Independence

Persistent Object does not depend on a concrete Storage Provider.

POR-INV-11 — Runtime Reconstruction

Runtime Object restoration is a reconstruction process, not direct deserialization of ObjectInstance.

POR-INV-12 — Lifecycle Separation

Runtime object lifecycle is separate from persistent object lifecycle.

POR-INV-13 — Business State Separation

Persistent business lifecycle state is distinct from runtime ObjectState.

POR-INV-14 — No Premature Schema

Step 7 does not define a physical persistence schema.

POR-INV-15 — No Premature Concurrency

Step 7 does not introduce versioning, revision, ETag, CAS or locking semantics.

POR-INV-16 — No Duplicate Domain Identity

Persistent Object does not introduce a second object identity type.

# 34. Conceptual Python Shape

The architecture now permits us to replace:

PersistentObject = Any

with a real semantic representation, but only at the next implementation stage after the representation contract is accepted.

The intended conceptual shape is approximately:

@dataclass(frozen=True)
class PersistentObject:
    identity: Identifier
    object_type_identity: Identifier
    state: ...
    fields: ...

However, the state and fields types are intentionally not finalized by Step 7.

In particular, we should not invent:

dict[str, Any]

as the final field model simply to make the code compile.

The field model must follow the existing Metadata / Logical Field architecture.

# 35. Why ObjectInstance Must Not Be Reused

It may be tempting to change:

ObjectPersistence.get(...) -> ObjectInstance

or make:

PersistentObject = ObjectInstance

This is explicitly rejected.

ObjectInstance contains runtime-specific concepts:

RuntimeObjectType
ObjectContext
ObjectState

while persistence requires:

Object Identity
Object Type Identity
Persistent State
Persistent Fields

Therefore:

ObjectInstance
      ≠
PersistentObject

is a permanent architectural distinction.

# 36. Relationship to ObjectPersistence

The existing persistence contract remains:

class ObjectPersistence(Protocol):
    def create(self, obj: PersistentObject) -> None:
        ...

    def get(self, identity: Identifier) -> PersistentObject:
        ...

    def update(self, obj: PersistentObject) -> None:
        ...

Step 7 gives semantic meaning to PersistentObject.

It does not change the operation surface.

Therefore:

Step 5.4
    ↓
ObjectPersistence API
    ↓
Step 7
    ↓
meaning of PersistentObject

# 37. Relationship to Step 6

Step 6 established:

Persistence Contract
       ↓
Persistence Implementation
       ↓
StorageProvider

Step 7 fills in the representation used at the top of that implementation:

ObjectPersistence
       ↓
PersistentObject
       ↓
Persistence Implementation
       ↓
StorageProvider

The complete Object persistence path therefore becomes:

ObjectInstance
      │
      ▼
Persistent Object Projection
      │
      ▼
PersistentObject
      │
      ▼
ObjectPersistence
      │
      ▼
Persistence Implementation
      │
      ▼
Serialization
      │
      ▼
StorageProvider
      │
      ▼
Physical Storage

# 38. Acceptance Criteria

Step 7 is complete when:

 Persistent Object is defined as a semantic durable representation.
 Object Identity preservation is defined.
 Object Type Identity preservation is defined.
 Runtime Object Type is explicitly excluded from persistence representation.
 Object Context is explicitly excluded from persistence representation.
 Runtime Configuration Context is explicitly excluded.
 Runtime ObjectState is explicitly separated from Persistent State.
 Persistent business state is defined as a separate category.
 Persistent logical fields are defined.
 StorageKey is excluded from the representation.
 Serialized payload is explicitly separated from Persistent Object.
 Runtime restoration is defined as reconstruction.
 Runtime lifecycle and persistent lifecycle remain separate.
 Business lifecycle state is distinguished from runtime ObjectState.
 Register Movement remains outside generic Persistent Object.
 No physical schema is introduced.
 No serialization format is selected.
 No concurrency mechanism is introduced.
 No second Object Identity type is introduced.
 The relationship to ObjectPersistence is established.
 A concrete Python representation can be implemented without inventing runtime dependencies.

# 39. Architectural Decision

AcCoreD adopts a dedicated Persistent Object Representation distinct from ObjectInstance.

A Persistent Object preserves:

Object Identity
Object Type Identity
Persistent State
Persistent Fields

while excluding runtime-specific state:

RuntimeObjectType instance
ObjectContext
RuntimeConfigurationContext
runtime lifecycle state
runtime services
temporary state

Persistent Object Representation is distinct from serialized payload and physical storage.

The representation is technology-independent and is consumed by ObjectPersistence.

# 40. Result

                 OBJECT DOMAIN
                      │
                      ▼
                ObjectInstance
                      │
             persistence mapping
                      │
                      ▼
             PersistentObject
                      │
                      ▼
              ObjectPersistence
                      │
                      ▼
          Persistence Implementation
                      │
                serialization
                      │
                      ▼
               StorageProvider
                      │
                      ▼
               Physical Storage