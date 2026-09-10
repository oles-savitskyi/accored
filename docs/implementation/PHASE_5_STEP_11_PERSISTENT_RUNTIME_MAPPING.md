# Phase 5 — Step 11

# Persistent Object ↔ Runtime Object Mapping

**Status:** Implemented
**Phase:** 5 — Storage & Persistence Boundary
**Step:** 11
**Version:** 1.0
**Date:** 2026-09-10

---

## 1. Purpose

This document defines the architectural boundary between the persistent representation of a business object and its runtime representation.

Phase 5 Step 7 established `PersistentObject` as the semantic durable representation of an object.

Phase 5 Step 8 established the persistent state and logical field model.

Phase 5 Step 9 established reuse of existing domain and metadata types.

Phase 5 Step 10 established the concrete Python representation of `PersistentObject`.

Step 11 defines how these persistent and runtime representations are related without collapsing them into a single model.

The primary architectural principle is:

> `PersistentObject` and `ObjectInstance` are distinct representations connected through an explicit mapping boundary.

This mapping boundary is semantic. It is not a Storage Provider, serializer, transaction manager, repository, or metadata compiler.

---

# 2. Scope

Step 11 defines:

* Persistent Object → Runtime Object hydration;
* Runtime durable state → Persistent Object materialization;
* Object Type Identity resolution;
* Metadata-guided field mapping;
* reference value mapping;
* runtime context ownership;
* separation of runtime lifecycle state from persistent state;
* separation of business state from runtime lifecycle state;
* missing and unknown field semantics;
* mapping and validation responsibilities;
* mapping and migration responsibilities;
* semantic round-trip requirements;
* mapping invariants and acceptance criteria.

Step 11 does not define:

* physical storage schema;
* database tables;
* EAV layout;
* serialization format;
* Storage Provider behavior;
* transactions;
* Persistence Scope implementation;
* object repositories;
* query APIs;
* metadata compilation;
* metadata migration;
* reference graph loading;
* runtime service lifecycle.

---

# 3. Architectural Position

The mapping boundary is positioned between persistence semantics and runtime semantics.

```text
                         Metadata
                            │
                            │ resolution
                            ▼
                    RuntimeObjectType
                            │
                            │
                            ▼
PersistentObject ─── Mapping Boundary ───► ObjectInstance
      │                                         │
      │                                         ├── ObjectContext
      │                                         └── Runtime ObjectState
      │
      ├── Object Identity
      ├── Object Type Identity
      └── Persistent State
            ├── Persistent Fields
            ├── Business State
            └── System Fields


Physical Storage
      │
      ▼
StorageProvider
      │
      ▼
Persistence Implementation
      │
      ▼
PersistentObject
```

The mapping boundary therefore belongs above the Storage Provider and below the runtime object model.

It does not expose physical storage concepts to Runtime.

---

# 4. Two Distinct Operations

Step 11 distinguishes two related but non-identical operations.

## 4.1 Hydration

Hydration reconstructs a runtime representation from durable persistent state.

```text
PersistentObject
       │
       ▼
Metadata / Runtime Resolution
       │
       ▼
RuntimeObjectType
       │
       ▼
ObjectContext
       │
       ▼
ObjectInstance
```

Hydration produces a runtime object suitable for use by Runtime services.

Hydration does not imply persistence, transaction management, or reference graph loading.

---

## 4.2 Materialization

Materialization produces a persistent representation from durable runtime state.

```text
Runtime durable state
       │
       ▼
Persistence Mapping
       │
       ▼
PersistentObject
```

The current `ObjectInstance` model does not itself contain an explicit persistent field collection.

Therefore materialization must not invent a convention that extracts persistent fields from arbitrary Python attributes.

The materialization implementation receives the explicitly defined `RuntimeDurableState` as its authoritative source of durable state.

Consequently:

> Hydration may be implemented before a fully symmetric Runtime → Persistent materialization API exists.

This is an intentional consequence of the current Runtime Object Model.

---

# 5. Object Identity

`PersistentObject.identity` reuses the existing platform `Identifier`.

Object Identity is preserved across persistence and runtime representations.

```text
PersistentObject.identity
          │
          ▼
ObjectInstance.identity
```

The mapping process must not generate a new identity during hydration.

Therefore:

> Hydration preserves Object Identity.

An object loaded from persistence represents the same logical object identity rather than a newly created object.

---

# 6. Object Type Identity

`PersistentObject.object_type_identity` is the durable identifier of the object's metadata/runtime type.

The existing runtime contract provides:

```python
RuntimeObjectType.metadata_identity() -> Identifier
```

Therefore the mapping relationship is:

```text
PersistentObject.object_type_identity
                │
                ▼
       Metadata / Runtime Resolution
                │
                ▼
        RuntimeObjectType
                │
                ▼
RuntimeObjectType.metadata_identity()
```

For a valid hydrated object:

```text
persistent.object_type_identity
==
runtime.object_type.metadata_identity()
```

The mapping layer does not generate or invent Object Type Identity.

It also does not persist the `RuntimeObjectType` instance itself.

---

# 7. Runtime Type Resolution

A `PersistentObject` contains only the identity of its object type.

It does not contain:

* a `RuntimeObjectType` instance;
* a runtime class;
* a `CatalogRuntime`;
* a metadata registry;
* runtime services;
* runtime configuration;
* provider-specific type information.

Therefore hydration requires resolution through the existing Metadata/Runtime resolution boundary.

Conceptually:

```text
PersistentObject
       │
       │ object_type_identity
       ▼
Metadata / Runtime Resolver
       │
       ▼
RuntimeObjectType
```

The mapping layer consumes the resolved runtime type.

It does not become a second Metadata Resolver.

---

# 8. Persistent Field Mapping

Persistent fields are logical metadata-defined fields.

They are not:

* Python attributes;
* database columns;
* EAV rows;
* JSON properties;
* Storage Provider records.

Mapping therefore proceeds through metadata semantics.

```text
PersistentField
      │
      ▼
Metadata Field Definition
      │
      ├── name
      ├── AttributeType
      ├── nullable
      ├── reference target
      └── applicable constraints
      │
      ▼
Runtime field/value representation
```

The mapping layer must preserve the semantic identity and value of a persistent field.

It must not introduce a second field type system.

Existing `AttributeType` and metadata definitions remain authoritative.

---

# 9. Metadata Is the Field Authority

Metadata defines the valid logical field set and its semantic properties.

Persistence Mapping consumes those definitions.

It does not redefine:

* attribute types;
* reference targets;
* field nullability;
* domain metadata;
* metadata lifecycle;
* metadata compilation rules.

Therefore:

> Persistence Mapping is not a second Metadata or Validation Engine.

Where validation is required, it must be delegated to the appropriate Metadata/Runtime/domain boundary.

Persistence remains responsible for persistence-level integrity.

---



# 10. Missing Fields

Missing fields have different meanings depending on metadata semantics.

## 10.1 Missing Required Field

If a required field is absent from persistent state, the object cannot be validly reconstructed.

Conceptually:

```text
Required metadata field
        +
Missing persistent value
        ↓
Invalid durable state
```

Such a condition is a persistence integrity failure.

---

## 10.2 Missing Optional Field

A field that is absent from stored state may be accepted only where current metadata semantics define the absence as valid.

For example, a nullable or otherwise optional field may be absent without making the object invalid.

The mapping layer must not invent universal defaulting behavior.

If a default value is semantically defined by the applicable metadata/domain model, that semantic may be applied.

Otherwise the field remains absent.

---

# 11. Unknown Persistent Fields

A persistent field that is not recognized by the current metadata is not silently discarded.

```text
Persistent Field
       │
       ▼
Current Metadata
       │
       └── field not defined
              │
              ▼
       Mapping / Integrity Failure
```

Silent removal is prohibited because it can cause durable state loss during a round trip.

Therefore:

> Unknown persistent fields must not be silently ignored.

Handling of historical fields, compatibility layers, or migrations belongs to a future migration/versioning mechanism.

---

# 12. Incompatible Field Types

If a persistent field exists but its durable value is incompatible with the current metadata semantics, the mapping process must not silently coerce it into an unrelated value.

For example:

```text
Stored field
    type/value incompatible
          ↓
Current Metadata
          ↓
Mapping failure
```

The appropriate error must preserve the semantic distinction between:

* invalid durable state;
* unsupported conversion;
* metadata evolution;
* physical storage failure.

The mapping layer must not hide such incompatibility.

---

# 13. Reference Fields

Reference attributes preserve Object Identity.

A persistent reference therefore contains the identity of the target object rather than an embedded runtime object.

Conceptually:

```text
Persistent Field
    name = "customer"
    value = Identifier(...)
             │
             ▼
       Reference semantics
             │
             ▼
     Runtime Reference
```

A reference must not persist:

* `ObjectInstance`;
* `RuntimeObjectType`;
* runtime context;
* provider-specific foreign keys;
* an embedded object graph.

The semantic value of a reference is the target Object Identity.

---

# 14. No Implicit Reference Graph Hydration

Hydrating an object must not recursively load all referenced objects.

For example:

```text
Invoice
   │
   └── Customer
         │
         └── Company
```

must not automatically become:

```text
Invoice
   └── Customer
        └── Company
             └── ...
```

The mapping boundary reconstructs the reference value.

Reference resolution/loading is a separate runtime concern.

Therefore:

> Object hydration does not imply recursive reference graph hydration.

This prevents uncontrolled object graphs, hidden storage access, and persistence/runtime coupling.

---

# 15. Object Context

`ObjectContext` is runtime state and is not part of `PersistentObject`.

Therefore:

```text
PersistentObject
    ❌ ObjectContext
```

Instead:

```text
PersistentObject
       │
       ▼
RuntimeObjectType
       │
       ▼
ObjectContext
       │
       ▼
ObjectInstance
```

The runtime context is supplied or constructed by the runtime boundary.

The mapping layer must not persist:

* `ObjectContext`;
* `RuntimeConfigurationContext`;
* `ActiveConfiguration`;
* runtime services;
* runtime caches;
* provider/session handles.

---

# 16. Runtime Object State

The existing runtime lifecycle model defines:

```python
ObjectState.CREATED
ObjectState.ACTIVE
ObjectState.DISPOSED
```

This state is runtime lifecycle state.

It is not automatically equivalent to persistent business state.

Therefore:

```text
Runtime ObjectState
        ≠
Persistent Object State
        ≠
Business State
```

Hydration must not infer runtime lifecycle state from arbitrary persistent business state.

For example:

```text
business_state = POSTED
```

does not automatically mean:

```text
ObjectState.ACTIVE
```

unless a separate domain/runtime contract explicitly defines such a relationship.

---

# 17. Business State

Persistent business state, when present, belongs to durable object state.

Example conceptual values include:

```text
DRAFT
APPROVED
POSTED
CANCELLED
```

These values must remain semantically separate from runtime lifecycle state.

Mapping preserves business state but does not reinterpret it as runtime lifecycle state.

```text
PersistentObjectState.business_state
                 │
                 ▼
        Runtime business state
```

The exact runtime representation of business state remains governed by the corresponding domain model.

---

# 18. System Fields

System fields are metadata-defined platform fields.

Where applicable, their durable values are part of persistent state.

The mapping layer must use the existing system field definitions.

It must not universally invent additional fields such as:

```text
version
created_at
updated_at
deleted
```

unless the applicable metadata/persistence contract requires them.

In particular, `version` must not be introduced merely for mapping convenience because versioning can imply concurrency semantics.

---

# 19. Mapping vs Validation

The responsibilities are separated.

### Metadata / Runtime / Domain validation

Responsible for:

* field definitions;
* field type semantics;
* reference targets;
* domain constraints;
* business rules;
* metadata validity.

### Persistence

Responsible for:

* persistence representation integrity;
* structural persistence invariants;
* preserving durable state;
* translating persistence failures.

### Mapping

Responsible for:

* translating between persistent and runtime representations;
* preserving semantic identity;
* applying metadata-defined field interpretation;
* preserving reference identity;
* reconstructing runtime representation.

Therefore:

> Mapping must not become a second validation engine.

---

# 20. Mapping vs Migration

Mapping and migration are separate concerns.

Mapping answers:

> How does a valid persistent representation correspond to the current runtime representation?

Migration answers:

> How is persistent data transformed when its representation or metadata semantics have changed?

Therefore the following are outside Step 11:

* automatic field renaming;
* automatic type conversion;
* historical schema migration;
* version-specific data transformations;
* obsolete-field cleanup;
* metadata-version migration.

Conceptually:

```text
Persistent Data
      │
      ├── current-compatible ──► Mapping
      │
      └── historical/incompatible
                │
                ▼
           Migration
```

No migration engine is introduced by Step 11.

---

# 21. Persistent Representation Is Not Serialization

The mapping boundary operates on semantic representations.

```text
PersistentObject
      │
      ▼
Mapping
      │
      ▼
ObjectInstance
```

Serialization is a separate concern:

```text
PersistentObject
      │
      ▼
Persistence Implementation
      │
      ▼
Encoded Representation
      │
      ▼
StorageProvider
```

Therefore the mapping layer has no knowledge of:

* JSON;
* pickle;
* database rows;
* filesystem files;
* binary formats;
* EAV rows;
* Storage Keys.

---

# 22. EAV Boundary

EAV is not part of the semantic mapping model.

The mapping model remains:

```text
PersistentObject
    └── PersistentField
```

not:

```text
PersistentObject
    └── EAV Row
```

A future physical Persistence Implementation may represent logical fields using EAV or another physical strategy.

Such a strategy remains below the semantic persistence boundary.

```text
Logical Persistent Field
          │
          ▼
Persistence Implementation
          │
          ├── structured storage
          ├── EAV
          ├── document storage
          └── other physical strategy
```

The Mapping Boundary remains independent of the chosen physical representation.

---

# 23. Materialization Constraints

The current `ObjectInstance` is:

```python
@dataclass(frozen=True, eq=False)
class ObjectInstance:
    identity: Identifier
    object_type: RuntimeObjectType
    context: ObjectContext
    state: ObjectState
```

It does not contain a persistent field collection.

Therefore the following is explicitly rejected:

```python
PersistentObject.from_runtime(instance)
```

if its implementation assumes that arbitrary runtime attributes constitute persistent fields.

Materialization requires an explicit durable-state source.

The materialization contract therefore defines `RuntimeDurableState` as the authoritative source of persistent field values.

This preserves the distinction between:

```text
Runtime Object Model
```

and:

```text
Persistent Object Model
```

rather than making Python object layout an accidental persistence schema.

---

# 24. Semantic Round Trip

For a valid durable state, hydration and subsequent materialization must preserve persistent semantics.

Conceptually:

```text
PersistentObject
       │
       ▼
    Hydrate
       │
       ▼
Runtime Representation
       │
       ▼
 Materialize
       │
       ▼
PersistentObject'
```

The invariant is:

```text
PersistentObject' ≡ PersistentObject
```

with respect to durable semantic state.

This does not require:

* byte-for-byte equality;
* identical serialization;
* identical physical storage layout;
* preservation of runtime context;
* preservation of runtime lifecycle state;
* preservation of caches;
* preservation of resolved reference instances.

The round-trip invariant applies to durable semantic state only.

---

# 25. Object Graph Boundary

The persistent representation is intentionally shallow.

```text
PersistentObject
    ├── identity
    ├── object_type_identity
    └── persistent state
          └── reference → target Object Identity
```

It does not contain an embedded runtime object graph.

Runtime object graphs may be constructed by higher-level runtime services when required.

This keeps object persistence independent of:

* graph traversal;
* lazy loading;
* eager loading;
* cache policy;
* query strategy.

---

# 26. Responsibility Matrix

| Concern                 | Mapping                 | Metadata         | Runtime               | Persistence             | Storage   |
| ----------------------- | ----------------------- | ---------------- | --------------------- | ----------------------- | --------- |
| Object Identity         | preserve                | —                | consume               | persist                 | store     |
| Object Type Identity    | preserve/use            | define/resolve   | consume               | persist                 | store     |
| Field semantics         | apply                   | own              | consume               | preserve                | opaque    |
| Field validation        | no                      | yes              | domain/runtime        | integrity               | no        |
| Reference identity      | preserve                | define target    | resolve when needed   | persist                 | opaque    |
| Reference graph loading | no                      | no               | possible higher layer | no                      | no        |
| ObjectContext           | consume/supply boundary | no               | own                   | no                      | no        |
| ObjectState             | preserve separation     | no               | own                   | no                      | no        |
| Business State          | preserve                | define semantics | consume               | persist                 | opaque    |
| Migration               | no                      | no               | no                    | no                      | no        |
| Serialization           | no                      | no               | no                    | implementation          | no        |
| EAV                     | no                      | no               | no                    | physical implementation | possible  |
| Transactions            | no                      | no               | no                    | Persistence Scope       | no        |
| Storage Provider        | no                      | no               | no                    | use                     | implement |

---

# 27. Error Boundary

Mapping failures must not expose physical storage details.

A failure caused by invalid durable state may ultimately be surfaced through the persistence error taxonomy as:

```python
PersistenceIntegrityError
```

Examples include:

* missing required persistent field;
* unknown persistent field;
* incompatible field value;
* invalid persistent object structure;
* invalid reference representation.

A physical storage failure remains distinct:

```python
PersistenceFailure
```

An unsupported physical capability remains:

```python
PersistenceUnsupportedError
```

An unknown operation outcome remains:

```python
PersistenceIndeterminateError
```

The mapping layer must therefore preserve the distinction between semantic mapping failure and physical storage failure.

---

# 28. Explicit Non-Responsibilities

The Persistent ↔ Runtime Mapping boundary must not:

* persist objects;
* read from StorageProvider directly;
* generate StorageKey values;
* encode storage bytes;
* decode physical storage formats;
* manage transactions;
* manage Persistence Scope;
* implement retry;
* implement concurrency control;
* compile metadata;
* register metadata;
* perform migrations;
* implement a repository;
* implement a query engine;
* load referenced object graphs;
* persist runtime object instances;
* persist ObjectContext;
* persist runtime services;
* persist runtime caches;
* expose EAV structures.

---

# 29. Canonical Mapping Model

The canonical architecture for Step 11 is:

```text
                         METADATA
                            │
                            │ resolve
                            ▼
                    RuntimeObjectType
                            │
                            │
                            ▼
PersistentObject ─── Mapping Boundary ───► ObjectInstance
      │                                         │
      │                                         ├── ObjectContext
      │                                         └── Runtime ObjectState
      │
      ├── Object Identity
      ├── Object Type Identity
      └── Persistent State
            ├── Persistent Fields
            ├── Business State
            └── System Fields


Reference Field
      │
      ▼
Target Object Identity
      │
      ▼
Runtime Reference
      │
      └── resolve on demand
```

Physical storage remains below the persistence boundary:

```text
Physical Storage
      │
      ▼
StorageProvider
      │
      ▼
Persistence Implementation
      │
      ▼
PersistentObject
      │
      ▼
Mapping Boundary
      │
      ▼
Runtime Object
```

---

# 30. Architectural Invariants

## P5-MAP1 — Explicit Mapping Boundary

Persistent and runtime object models are connected through an explicit mapping boundary.

---

## P5-MAP2 — Type Identity Preservation

`PersistentObject.object_type_identity` identifies the corresponding runtime object type through the existing metadata/runtime resolution mechanism.

---

## P5-MAP3 — No Runtime Type Persistence

`RuntimeObjectType` instances are never persisted as part of `PersistentObject`.

---

## P5-MAP4 — Metadata-Governed Fields

Persistent fields are interpreted according to applicable Metadata definitions.

---

## P5-MAP5 — No Silent Field Loss

Unknown or incompatible persistent fields must not be silently discarded.

---

## P5-MAP6 — Optional Field Evolution

Missing optional fields may be accepted only according to established metadata/domain semantics.

---

## P5-MAP7 — Reference Identity Preservation

Reference fields preserve target Object Identity and do not embed runtime object instances.

---

## P5-MAP8 — No Implicit Graph Hydration

Mapping a PersistentObject does not recursively load referenced objects.

---

## P5-MAP9 — Runtime Context Separation

`ObjectContext` is runtime-only and is supplied or constructed by the runtime boundary.

---

## P5-MAP10 — Lifecycle Separation

Runtime `ObjectState` is not inferred from Persistent Business State.

---

## P5-MAP11 — Mapping Is Not Migration

Schema, metadata, and historical data evolution are outside the mapping boundary.

---

## P5-MAP12 — Semantic Round Trip

Hydration and materialization preserve durable semantic state independently of physical representation.

---

## P5-MAP13 — No Storage Leakage

Mapping has no dependency on `StorageKey`, Storage Provider, filesystem, database, EAV, or serialized bytes.

---

## P5-MAP14 — No Persistence Orchestration

Mapping does not own transactions, Persistence Scope, retries, or persistence coordination.

---

# 31. Relationship to Previous Phase 5 Decisions

Step 11 depends on and preserves the following decisions:

## Step 7 — Persistent Object Representation

`PersistentObject` is a durable semantic representation, not a serialized `ObjectInstance`.

## Step 8 — Persistent State & Field Model

Persistent state consists of logical fields and optional business/system state.

## Step 9 — Existing Domain Type Reuse

Existing `Identifier`, `AttributeType`, metadata definitions, and system field definitions remain authoritative.

## Step 10 — Python Representation

`PersistentField`, `PersistentObjectState`, and `PersistentObject` remain immutable semantic Python representations.

Step 11 does not redefine any of these models.

---

# 32. Acceptance Criteria

Step 11 is architecturally complete when all of the following are satisfied:

* [x] Explicit PersistentObject ↔ Runtime Object mapping boundary is defined.
* [x] Object Type Identity source is defined.
* [x] Metadata/Runtime type resolution responsibility is defined.
* [x] Persistent field mapping rules are defined.
* [x] Missing required field semantics are defined.
* [x] Missing optional field semantics are defined.
* [x] Unknown persistent field behavior is defined.
* [x] Incompatible field behavior is defined.
* [x] Reference mapping is defined.
* [x] Implicit reference graph hydration is explicitly prohibited.
* [x] ObjectContext ownership is defined.
* [x] Runtime ObjectState separation is preserved.
* [x] Business State separation is preserved.
* [x] System field handling is defined without introducing universal system fields.
* [x] Mapping vs Validation responsibility is defined.
* [x] Mapping vs Migration responsibility is defined.
* [x] Mapping vs Serialization responsibility is defined.
* [x] EAV remains below the semantic persistence boundary.
* [x] Semantic round-trip invariant is defined.
* [x] Mapping does not depend on StorageProvider.
* [x] Mapping does not expose physical storage.
* [x] Mapping does not own transaction or Persistence Scope semantics.
* [x] Mapping does not introduce repository or query abstractions.
* [x] Current asymmetry between hydration and materialization is explicitly documented.

---

# 33. Final Decision

Phase 5 Step 11 establishes the following architectural rule:

> **PersistentObject is the durable semantic representation of an object. ObjectInstance is its runtime representation. They are not the same model and must not be serialized into one another implicitly. An explicit mapping boundary connects them.**

The mapping boundary:

* preserves Object Identity;
* resolves Object Type Identity through existing Metadata/Runtime mechanisms;
* interprets fields according to Metadata;
* preserves reference identities;
* does not recursively hydrate reference graphs;
* keeps ObjectContext and runtime lifecycle state outside persistence;
* preserves business state without conflating it with runtime state;
* does not perform migrations;
* does not perform physical serialization;
* does not depend on Storage Provider implementation;
* does not expose EAV or other physical storage strategies.

The resulting architectural flow is:

```text
PersistentObject
      │
      ▼
Metadata / Runtime Resolution
      │
      ▼
Explicit Mapping Boundary
      │
      ▼
ObjectInstance
```

and, where an explicit durable-state source exists:

```text
Runtime Durable State
      │
      ▼
Explicit Mapping Boundary
      │
      ▼
PersistentObject
```

This closes the semantic boundary between durable persistence representation and runtime object representation without introducing premature ORM, repository, query, transaction, or physical schema abstractions.

# 34. Implemented Python API

The Step 11 implementation provides the following mapping types in
`accore.platform.persistence.mapping`:

```python
class PersistentObjectMappingError(RuntimeError):
    """Raised when a persistent object cannot be mapped to runtime safely."""


class PersistentObjectHydrator:
    def __init__(self, runtime_resolver: RuntimeResolver) -> None:
        ...

    def hydrate(
        self,
        persistent: PersistentObject,
        context: ObjectContext,
    ) -> HydratedRuntimeObject:
        ...
```

The implementation provides explicit hydration from `PersistentObject` to
`HydratedRuntimeObject`, preserving the separation between `ObjectInstance`
and `RuntimeDurableState`.

The hydrator:

preserves PersistentObject.identity;
resolves object_type_identity through RuntimeResolver;
verifies that the resolved runtime type has the expected metadata identity;
supplies the runtime ObjectContext;
does not infer or restore ObjectState;
rejects persistent fields, system fields, or business state that cannot
currently be represented by the Runtime Object Model;
translates runtime type resolution failures into
PersistentObjectMappingError.

The mapping implementation is currently located in:

src/accore/platform/persistence/mapping.py

The public persistence API exports the materialization mapping types and
the persistence mapping error contract. Runtime mapping remains explicit
and technology-independent.

# 35. Validation

The Step 11 implementation is part of the completed Phase 5 persistence
quality gate. The final repository validation after subsequent persistence
work is:

## Tests

```text
pytest
711 passed in 4.72s
```

### Static Analysis

```text
ruff check .
All checks passed!
```

### Formatting

```text
black --check .
All done! 152 files would be left unchanged.
```

### Type Checking

```text
mypy src
Success: no issues found in 79 source files
```

These final project-wide results supersede the earlier Step 11 checkpoint
values recorded before Steps 12 and materialization were completed.

## Step 11 Acceptance Criteria

* [x]  Explicit PersistentObject → ObjectInstance mapping boundary.
* [x]  Object identity is preserved.
* [x]  Object type identity is resolved through RuntimeResolver.
* [x]  Resolved runtime type identity is verified.
* [x]  Runtime ObjectContext remains runtime-owned.
* [x]  Runtime ObjectState is not inferred from persistent state.
* [x]  Persistent state is not silently discarded.
* [x]  Unsupported durable state produces an explicit mapping failure.
* [x]  Reference values remain identity-based; no implicit graph hydration.
* [x]  Mapping does not introduce storage-provider dependencies.
* [x]  Mapping does not perform persistence orchestration.
* [x]  Mapping does not become a migration or validation engine.
* [x]  Full project quality gate passes.
* [x]  The mapping API is integrated with the final persistence public API.
* [x]  Materialization is implemented as the reverse explicit mapping direction.

