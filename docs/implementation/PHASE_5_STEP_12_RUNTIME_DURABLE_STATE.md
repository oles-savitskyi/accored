# Phase 5 — Step 12: Runtime Durable State & Persistent Materialization Contract

**Status:** Implemented — Final
**Phase:** 5 — Persistence Architecture
**Step:** 12
**Version:** 3.0
**Date:** 2026-09-10

---

## 1. Purpose

Step 12 defines the semantic runtime representation of an object's durable state and establishes the final contract between:

* Runtime;
* `ObjectInstance`;
* `RuntimeDurableState`;
* Persistence;
* `PersistentObject`;
* `PersistentObjectState`;
* the explicit Persistence Mapping boundary.

The primary objective is to ensure that an object's durable business data is represented explicitly and independently from:

* runtime lifecycle state;
* runtime context;
* runtime services;
* persistence implementation;
* storage implementation;
* serialization;
* transaction state;
* change tracking.

Step 12 completes the semantic persistence boundary introduced in Step 11.

---

# 2. Architectural Principle

The central principle is:

> `ObjectInstance` represents runtime existence of an object, while `RuntimeDurableState` represents the object's durable semantic state.

Therefore:

```text
Runtime
│
├── ObjectInstance
│   ├── identity
│   ├── runtime type
│   ├── context
│   └── lifecycle state
│
└── RuntimeDurableState
    ├── identity
    ├── object type identity
    ├── fields
    ├── references
    ├── business state
    └── durable system fields
```

`RuntimeDurableState` is not a component of `ObjectInstance`.

The two models are associated by Object Identity.

---

# 3. Scope

Step 12 defines:

1. `RuntimeDurableState`;
2. its identity and type identity;
3. durable fields;
4. durable references;
5. business-state snapshot;
6. durable system fields;
7. `MISSING` and `NULL` semantics;
8. semantic exclusivity of durable categories;
9. `RuntimeDurableState` ↔ `PersistentObjectState`;
10. hydration;
11. materialization;
12. durable-state semantic equivalence;
13. semantic round-trip;
14. ownership boundaries;
15. implementation gates.

---

# 4. Explicit Non-Goals

Step 12 does **not** define:

* physical database schema;
* relational tables;
* EAV layout;
* serialized representation;
* JSON encoding;
* Storage Provider behavior;
* transaction implementation;
* Unit of Work;
* repository/query API;
* locking implementation;
* optimistic concurrency implementation;
* metadata compilation implementation;
* migration implementation;
* reference graph loading;
* lazy loading;
* runtime service lifecycle;
* workflow execution;
* authorization;
* posting effects.

Those concerns remain outside the semantic durable-state model.

---

# 5. Runtime Object Model

The existing runtime object remains conceptually:

```text
ObjectInstance
├── identity: Identifier
├── object_type: RuntimeObjectType
├── context: ObjectContext
└── state: ObjectState
```

Its responsibilities are:

* runtime object identity;
* runtime type;
* runtime context;
* runtime lifecycle state.

It does not own the durable field/reference/business-state model.

In particular, materialization must never infer durable state from arbitrary attributes of `ObjectInstance`.

---

# 6. Runtime Durable State

`RuntimeDurableState` is an immutable semantic runtime snapshot of the state that is eligible for persistence.

Conceptual structure:

```text
RuntimeDurableState
│
├── identity: Identifier
├── object_type_identity: Identifier
│
├── fields
│   └── FieldIdentity → NULL | DurableValue
│
├── references
│   └── ReferenceIdentity → ReferenceValue
│
├── business_state
│   └── BusinessStateDefinitionIdentity → StateValueIdentity
│
└── durable_system_fields
    └── SystemFieldIdentity → NULL | DurableValue
```

The four containers are semantically independent.

---

# 7. Durable State Identity

`RuntimeDurableState.identity` is the Object Identity of the runtime object whose durable state is represented.

The identity is preserved across:

```text
PersistentObject
        ↓
PersistentObjectState
        ↓
RuntimeDurableState
```

and:

```text
RuntimeDurableState
        ↓
PersistentObjectState
        ↓
PersistentObject
```

Hydration never creates a replacement identity.

---

# 8. Object Type Identity

`RuntimeDurableState.object_type_identity` identifies the durable object type.

It is an identity value, not a concrete `RuntimeObjectType` instance.

Therefore:

```text
RuntimeDurableState
    └── object_type_identity: Identifier
```

and not:

```text
RuntimeDurableState
    └── object_type: RuntimeObjectType
```

The concrete runtime type is resolved by Runtime.

For a hydrated object:

```text
PersistentObject.object_type_identity
    ==
RuntimeDurableState.object_type_identity
    ==
ObjectInstance.object_type.metadata_identity()
```

A mismatch is a mapping error.

---

# 9. Durable Value

DurableValue is an immutable semantic value that can participate in durable state.

It represents a value that may be persisted without depending on Runtime, Persistence, Storage, or Metadata.

Step 12 base value kinds are:

Scalar
Boolean;
Integer;
Decimal;
String;
Date;
DateTime.
Composite
Structured;
Collection.

float is not part of the base durable-value contract.

Accounting semantics should use Decimal rather than IEEE floating-point values unless a later architectural decision explicitly introduces floating-point semantics.

DurableValue is a semantic value domain, not a generic container for arbitrary Python objects.

The Python representation must therefore satisfy the following rules:

supported scalar values are limited to the defined scalar kinds;
composite values use explicit immutable representations;
arbitrary Python objects do not automatically qualify as DurableValue;
mutable Python containers are not themselves durable values;
composite values must not expose mutable internal state;
nested values must themselves satisfy the DurableValue contract;
Runtime objects, ObjectInstance, ObjectContext, RuntimeObjectType, and other runtime services are never DurableValue.

The Step 12 Python contract intentionally does not introduce a large hierarchy of wrapper classes for every scalar kind.

Native immutable Python representations may be used for scalar values when their semantic kind is unambiguous:

Boolean   → bool
Integer   → int
Decimal   → decimal.Decimal
String    → str
Date      → datetime.date
DateTime  → datetime.datetime

Structured and Collection require explicit immutable semantic representations rather than relying on arbitrary dict, list, set, or tuple values.

Conceptually:

DurableValue
│
├── Scalar
│   ├── bool
│   ├── int
│   ├── Decimal
│   ├── date
│   └── datetime
│
└── Composite
    ├── StructuredValue
    │   └── immutable FieldIdentity → DurableValue
    │
    └── CollectionValue
        └── immutable ordered sequence[DurableValue]

DurableValue does not contain Metadata definitions.

Metadata defines the interpretation, allowed type, constraints, cardinality, nullability, and semantic role of a durable value.

DurableValue itself defines only the semantic value domain and its structural invariants.

Domain concepts such as Money, Quantity, Percentage, Currency, and Enum are not introduced as independent base DurableValue kinds in Step 12. They remain domain or Metadata semantics over the base value domain unless a later architectural decision establishes dedicated semantic value objects.

NULL is not a DurableValue.

MISSING is not a DurableValue.

They are state-presence semantics defined by the containers that use durable values.

---

# 10. `NULL` and `MISSING`

`NULL` is not a `DurableValue`.

A field or system field may nevertheless explicitly contain `NULL`.

`MISSING` is not a value and has no explicit representation.

It is represented by absence of the corresponding key.

Therefore:

```text
key absent
    → MISSING

key present → NULL
    → explicit NULL

key present → DurableValue
    → VALUE
```

This distinction is mandatory for semantic round-trip preservation.

---

# 11. Fields

The fields container is:

FieldIdentity → NULL | DurableValue

where, in the current Metadata model:

FieldIdentity = canonical Metadata field name

FieldIdentity is therefore not an Identifier at this stage.

The current Metadata architecture identifies attributes by their canonical logical names and does not yet provide a separate persistent identity for every field.

This is an intentional Step 12 constraint.

If Metadata later introduces explicit field identity, the Persistence and Runtime durable-state models may adopt that identity through a separate architectural evolution. Step 12 must not create artificial identifiers from field names.

A field is durable object data classified by Metadata with semantic role:

FIELD

Fields characterize object data.

They do not represent:

object relationships;
business lifecycle state;
platform-owned system properties;
runtime lifecycle state.

Field identity is Metadata identity, not an arbitrary Python attribute name.

The field container represents state only.

It does not contain:

field definitions;
Metadata objects;
validation rules;
default-value definitions;
Runtime objects;
change history.

The distinction between MISSING and NULL is significant:

MISSING
    key is absent from the container

NULL
    key is present and explicitly contains null

NULL is permitted only where the corresponding Metadata definition allows nullability.

Required-field validation and other field constraints are Metadata, Validation, or Mapping concerns and are not created by the container itself.

Defaults are not implicitly materialized merely because Metadata defines a default. A default becomes durable state only when the applicable object-creation semantics actually establish that value.

---

# 12. Field Rules

The following rules apply:

1. Field keys identify Metadata-defined fields.
2. Field values are `NULL | DurableValue`.
3. References are not stored as fields.
4. Business state is not stored as fields.
5. Durable system fields are not stored as fields.
6. Runtime objects are not stored as fields.
7. Change-tracking information is not stored as fields.
8. Metadata definitions themselves are not stored as field values.
9. Defaults are not automatically materialized merely because a Metadata definition declares them.
10. Once a default becomes actual object state through object-creation semantics, it is represented as durable state.
11. Field containers are immutable snapshots.
12. Required/nullable/constraint validation remains a Metadata/Validation concern.

---

# 13. References

The references container is:

ReferenceIdentity → ReferenceValue

where, in the current Metadata model:

ReferenceIdentity = canonical Metadata reference name

ReferenceIdentity is therefore not an Identifier at this stage.

The current Metadata architecture represents references through attributes whose semantic type is:

AttributeType.REFERENCE

and whose target is defined by the corresponding Metadata reference target.

A reference is a durable relationship between objects.

Reference values have two conceptual cardinalities:

SINGLE:
    ObjectIdentity | NULL

MANY:
    immutable ordered sequence[ObjectIdentity]

Cardinality itself is defined by Metadata and is not embedded in the reference value.

The distinction between MISSING, NULL, and an empty collection is significant:

MISSING
    reference key is absent

NULL
    explicit absence of a SINGLE reference where nullability permits it

MANY = ()
    reference is present and contains no target objects

An empty MANY reference is therefore distinct from a missing reference.

Reference values contain object identities only.

They do not contain:

resolved ObjectInstance objects;
RuntimeObjectType objects;
ObjectContext;
runtime services;
persistence handles;
storage keys;
serialized representations.

References therefore do not force object graph loading.

A reference may participate in cycles and may point to the same object identity as its owner unless Metadata or Validation explicitly prohibits such a relationship.

There is no universal duplicate prohibition for MANY references at the durable-state level. Duplicate semantics, when relevant, are defined by Metadata or Validation.

Reference state is durable semantic state. Resolution of referenced identities into runtime objects is a separate Runtime concern.

---

# 14. Reference Semantics

For a `SINGLE` reference:

```text
key absent
    → MISSING

key → NULL
    → explicit NULL relationship

key → ObjectIdentity
    → relationship exists
```

For a `MANY` reference:

```text
key absent
    → MISSING

key → []
    → explicitly known empty relationship collection

key → [ObjectIdentity, ...]
    → relationship collection
```

`MANY` uses an ordered sequence so that ordering information is not accidentally destroyed.

Duplicate identities are not universally forbidden at the container level. Duplicate policy belongs to Metadata/Validation semantics.

---

# 15. Reference Identity Rule

A durable reference contains Object Identity, not a resolved runtime object.

Valid:

```text
customer → 01K...
```

Invalid as durable state:

```text
customer → ObjectInstance(...)
```

Runtime may resolve an Object Identity to an `ObjectInstance` for navigation.

The resolved runtime object is not part of `RuntimeDurableState`.

---

# 16. Reference Type Rule

The target object type of a reference is defined by the corresponding Metadata reference semantics.

In the current Metadata model, this is represented by the corresponding attribute with:

AttributeType.REFERENCE

and its configured reference_target.

A reference value therefore contains:

ObjectIdentity

but does not contain:

RuntimeObjectType

or a resolved ObjectInstance.

ObjectIdentity does not carry the target runtime type.

The target type is interpreted from Metadata for the corresponding reference.

This preserves the dependency direction:

Metadata
    │
    ├── defines reference semantics
    └── defines target type
             │
             ▼
      RuntimeDurableState
             │
             └── stores ObjectIdentity

Referential integrity is not enforced by RuntimeDurableState itself.

RuntimeDurableState stores the semantic relationship; validation of whether the target exists, is of the permitted type, or satisfies additional business constraints belongs to the appropriate Metadata/Validation/Runtime boundary.

Cycles and self-references are allowed unless Metadata/Validation explicitly prohibits them.

Resolution of a referenced ObjectIdentity into a runtime object is outside the durable-state contract and must not be performed implicitly by the reference value.

---

# 17. Business State

`business_state` is:

```text
BusinessStateDefinitionIdentity
    →
StateValueIdentity
```

It represents the current durable business state of each applicable business-state dimension.

Business state is not ordinary field data.

It represents business lifecycle semantics that can affect:

* allowed operations;
* business transitions;
* business invariants;
* domain behavior.

---

# 18. Business State Snapshot

`BusinessStateSnapshot` is an immutable current-state snapshot.

It does not contain:

* transition history;
* transition graph;
* transition handlers;
* workflow state;
* runtime lifecycle state.

Multiple independent business-state dimensions are allowed.

For example:

```text
approval_status
processing_status
posting_status
```

are independent dimensions.

No Cartesian product is constructed automatically.

Cross-dimension constraints belong to Validation/Business Rules.

---

# 19. Business State `MISSING`

The representation may be structurally partial:

```text
business_state = {}
```

means that no state values are represented in that snapshot.

However, a complete valid runtime object must contain the applicable required business-state dimensions.

`MISSING` must never be interpreted as `initial_state` by Mapping.

The initial state is applied by Runtime during object creation.

Hydration must preserve the actual persisted state.

---

# 20. Business State Vocabulary

Every `StateValueIdentity` must belong to the closed vocabulary of its corresponding `BusinessStateDefinition`.

The following are Metadata/Validation responsibilities:

* state identity validity;
* state vocabulary membership;
* applicable dimensions;
* completeness;
* transition legality.

Runtime executes transitions.

Mapping transfers the resulting state.

---

# 21. Durable System Fields

`durable_system_fields` is:

```text
SystemFieldIdentity → NULL | DurableValue
```

It contains platform-owned properties that are part of durable object state.

Examples include:

```text
created_at
created_by
modified_at
modified_by
```

`version` is intentionally not mandated as a durable system field by Step 12.

Its inclusion depends on the future persistence/concurrency model.

---

# 22. Durable System Field Criteria

A property is a durable system field only when all of the following apply:

1. it is platform-owned;
2. it is a property of the object itself;
3. it has durable semantic meaning;
4. it must survive process restart;
5. it is part of the object's persistent semantic state;
6. its semantics are not merely runtime execution metadata.

Examples:

```text
created_at       → durable
created_by       → durable
modified_at      → durable
modified_by      → durable
```

---

# 23. Runtime State Exclusion

The following are not durable system fields:

```text
is_loaded
is_dirty
is_new
is_deleted
cache_state
loading_state
hydration_state
last_accessed_at
change_set
original_values
dirty_fields
transaction_id
transaction_state
lock_owner
lock_token
```

These belong to Runtime, Persistence orchestration, concurrency, or transaction concerns.

---

# 24. System Field Ownership

Platform-owned does not mean "freely mutable".

A system field such as:

```text
created_at
created_by
```

must not be changed through generic business-field mutation.

Platform/runtime lifecycle mechanisms control such values.

For example:

```text
set_field("created_at", ...)
```

must not be the generic mechanism for changing a platform-managed property.

---

# 25. Semantic Role Exclusivity

Every durable semantic property belongs to exactly one primary category:

```text
FIELD
REFERENCE
BUSINESS_STATE
SYSTEM_FIELD
```

A property cannot simultaneously be:

```text
FIELD + REFERENCE
FIELD + BUSINESS_STATE
FIELD + SYSTEM_FIELD
REFERENCE + BUSINESS_STATE
REFERENCE + SYSTEM_FIELD
BUSINESS_STATE + SYSTEM_FIELD
```

This is a Metadata validation invariant.

Mapping must not guess or resolve ambiguous semantic roles.

---

# 26. Runtime Lifecycle vs Durable State

The separation is strict:

```text
ObjectInstance
├── identity
├── runtime type
├── ObjectContext
└── ObjectState
    ├── lifecycle
    ├── loaded
    ├── dirty
    ├── new
    └── other runtime concerns
```

versus:

```text
RuntimeDurableState
├── identity
├── object type identity
├── fields
├── references
├── business state
└── durable system fields
```

Runtime lifecycle state is never materialized into `PersistentObjectState`.

---

# 27. Runtime Durable State Does Not Own Runtime Lifecycle

`RuntimeDurableState` does not contain:

* `ObjectContext`;
* `ObjectState`;
* Runtime services;
* Runtime resolver;
* Runtime cache;
* transaction;
* Persistence Scope;
* Storage Provider.

Its purpose is limited to durable semantic state.

---

# 28. Ownership

The ownership model is:

```text
Runtime
│
├── ObjectInstance
│
└── RuntimeDurableState
```

Both are runtime semantic models.

They are associated by:

```text
ObjectInstance.identity
    ==
RuntimeDurableState.identity
```

The concrete lifecycle ownership of `RuntimeDurableState` instances belongs to a higher Runtime boundary/service.

The Mapping boundary has no long-lived ownership of either runtime model.

---

# 29. Persistence Representation

The persistence-side semantic model is:

```text
PersistentObject
├── identity
├── object_type_identity
└── persistent state

PersistentObjectState
├── fields
├── references
├── business state
└── durable system fields
```

`PersistentObjectState` is a Persistence semantic representation of the same durable semantic state represented by `RuntimeDurableState`.

They are boundary-specific representations.

Neither inherits from nor contains the other.

---

# 30. Durable State Equivalence

For:

```text
R = RuntimeDurableState
P = PersistentObjectState
```

we define:

```text
R ≡ P
```

when the following are semantically equivalent:

```text
identity
object_type_identity
fields
references
business_state
durable_system_fields
```

Internal Python representation does not need to be identical.

Serialization format does not need to be identical.

Physical storage representation does not need to be identical.

---

# 31. Persistence Independence

`RuntimeDurableState` must not depend directly on:

* `StorageProvider`;
* `StorageKey`;
* database rows;
* table names;
* column names;
* EAV rows;
* serialized bytes;
* transactions.

The dependency direction remains:

```text
Metadata
    ↓
Runtime
    ↓
Mapping Boundary
    ↓
Persistence
    ↓
Storage
```

---

# 32. EAV Boundary

EAV remains a physical persistence concern.

Even if the physical implementation uses:

```text
object_id
field_id
value
```

or equivalent structures, those details must not leak into `RuntimeDurableState`.

The semantic model remains:

```text
FieldIdentity → DurableValue
```

not:

```text
EAVRow
```

---

# 33. Explicit Mapping Boundary

The Mapping boundary performs semantic translation between runtime and persistence representations.

It does not:

* own runtime objects;
* own transactions;
* execute business transitions;
* resolve reference graphs;
* serialize bytes;
* decide Metadata semantics;
* perform persistence;
* implement storage.

Its responsibility is semantic representation translation and compatibility checking.

---

# 34. Hydration Contract

Hydration is the explicit transformation:

```text
PersistentObject
        ↓
PersistentObjectState
        ↓
Persistence Mapping
        ↓
RuntimeDurableState
        +
ObjectInstance
```

The resulting models must satisfy:

```text
PersistentObject.identity
    ==
RuntimeDurableState.identity
    ==
ObjectInstance.identity
```

and:

```text
PersistentObject.object_type_identity
    ==
RuntimeDurableState.object_type_identity
    ==
ObjectInstance.object_type.metadata_identity()
```

---

# 35. Hydration Rules

Hydration must:

1. preserve Object Identity;
2. preserve Object Type Identity;
3. resolve the concrete Runtime Object Type through Runtime resolution;
4. create/associate an `ObjectInstance`;
5. create/associate `RuntimeDurableState`;
6. preserve all four durable-state containers;
7. preserve `MISSING` vs `NULL`;
8. preserve reference identities;
9. preserve business-state values;
10. preserve durable system fields;
11. use the supplied `ObjectContext`;
12. avoid restoring runtime lifecycle state from persistence unless explicitly defined by a separate Runtime contract.

Hydration must not:

* generate a new object identity;
* replace missing business state with `initial_state`;
* resolve the full reference graph;
* infer durable state from runtime attributes.

---

# 36. Materialization Contract

Materialization is the explicit semantic transformation:

```text
RuntimeDurableState
        ↓
Persistence Mapping
        ↓
PersistentObjectState
        ↓
PersistentObject
```

The contract is:

> Materialization preserves Object Identity, Object Type Identity, and the complete durable semantic state represented by `fields`, `references`, `business_state`, and `durable_system_fields`.

Materialization must not read arbitrary attributes from `ObjectInstance`.

---

# 37. Materialization Source of Truth

The authoritative runtime source for durable data is:

```text
RuntimeDurableState
```

not:

```text
ObjectInstance.__dict__
```

and not:

```text
vars(ObjectInstance)
```

and not:

```text
getattr(ObjectInstance, ...)
```

and not arbitrary runtime attributes.

This explicitly closes the ambiguity identified in Step 11.

---

# 38. Materialization of Object Identity

Materialization preserves:

```text
RuntimeDurableState.identity
        ↓
PersistentObjectState.identity
        ↓
PersistentObject.identity
```

No new identity is generated.

---

# 39. Materialization of Object Type Identity

Materialization preserves:

```text
RuntimeDurableState.object_type_identity
        ↓
PersistentObjectState.object_type_identity
        ↓
PersistentObject.object_type_identity
```

The concrete `RuntimeObjectType` instance is not persisted.

---

# 40. Materialization of Fields

Materialization preserves:

```text
FieldIdentity → NULL | DurableValue
```

including:

```text
MISSING
NULL
VALUE
```

semantics.

Metadata determines how values are interpreted and validated.

Mapping does not transform arbitrary Python attributes into persistent fields.

---

# 41. Materialization of References

Materialization preserves:

```text
ReferenceIdentity → ReferenceValue
```

and stores Object Identities, not resolved Runtime Objects.

No reference graph traversal is performed by generic materialization.

---

# 42. Materialization of Business State

Materialization preserves the exact current business-state snapshot.

It must not:

* reset state;
* apply initial state;
* execute transitions;
* derive a state from ordinary fields;
* create transition history.

---

# 43. Materialization of Durable System Fields

Materialization preserves platform-owned durable system fields.

It must not materialize:

* dirty state;
* loaded state;
* cache state;
* transaction state;
* lock state;
* runtime timestamps;
* change tracking.

---

# 44. Mapping Validation

Mapping must detect structural and semantic incompatibilities such as:

* unknown object type;
* mismatched object type identity;
* unknown field identity;
* field/reference role mismatch;
* field/business-state role mismatch;
* system-field/field role mismatch;
* invalid reference cardinality;
* invalid business-state dimension;
* invalid state value;
* unsupported durable value;
* illegal `NULL`;
* illegal durable representation.

These are mapping errors.

---

# 45. Business Validation Boundary

Mapping does not implement general business validation.

For example:

```text
amount > 0
```

or:

```text
posted invoice cannot be cancelled
```

are not generic mapping concerns.

They belong to Metadata/Validation/Runtime business semantics.

Mapping validates representation compatibility, not arbitrary business rules.

---

# 46. Initial State Rule

`BusinessStateDefinition.initial_state` belongs to object-creation semantics.

Runtime applies it when creating a new object.

Mapping does not apply initial state.

Therefore:

```text
missing persisted state
```

must never silently become:

```text
initial_state
```

during hydration.

---

# 47. No Implicit Attribute Persistence

The following pattern is explicitly rejected:

```text
ObjectInstance
    ↓
inspect Python attributes
    ↓
guess durable fields
    ↓
PersistentObject
```

The required pattern is:

```text
ObjectInstance
       │
       │ associated by identity
       │
RuntimeDurableState
       ↓
Explicit Mapping
       ↓
PersistentObjectState
       ↓
PersistentObject
```

---

# 48. Semantic Round Trip

The complete semantic round trip is:

```text
PersistentObject
        ↓
PersistentObjectState
        ↓
hydrate
        ↓
RuntimeDurableState
        +
ObjectInstance
        ↓
Runtime operations
        ↓
RuntimeDurableState'
        ↓
materialize
        ↓
PersistentObjectState'
        ↓
PersistentObject'
```

If no durable state changes occur:

```text
PersistentObjectState'
    ≡
PersistentObjectState
```

If durable state changes occur, the resulting persistent representation must reflect the modified `RuntimeDurableState`.

---

# 49. Runtime State Must Not Pollute Round Trip

The following changes must not affect durable equivalence:

```text
ObjectContext changes
ObjectState changes
loaded state
dirty state
cache state
runtime service state
temporary runtime objects
reference-resolution caches
```

Only durable semantic state participates in durable equivalence.

---

# 50. Metadata Semantic Roles

Metadata remains the source of semantic classification.

The relevant roles are:

```text
FIELD
REFERENCE
BUSINESS_STATE
SYSTEM_FIELD
```

Metadata determines:

* identity;
* value semantics;
* cardinality;
* nullability;
* constraints;
* business-state vocabulary;
* system-field semantics.

RuntimeDurableState contains values, not Metadata definitions.

---

# 51. Reuse of Value Semantics

Step 12 must not introduce redundant independent type hierarchies such as:

```text
RuntimeField
PersistentField
MetadataField
RuntimeValue
PersistentValue
```

unless a later architectural need proves them necessary.

The semantic `DurableValue` contract is shared at the value level.

Metadata defines interpretation.

Runtime and Persistence define their own boundary representations.

---

# 52. Core Invariants

## Durable State

**P5-DUR1 — Durable State Separation**

Durable state is separate from `ObjectInstance`.

**P5-DUR2 — Identity Association**

`ObjectInstance` and `RuntimeDurableState` are associated by Object Identity.

**P5-DUR3 — Runtime Type Separation**

Durable state contains type identity, not a concrete `RuntimeObjectType`.

**P5-DUR4 — Metadata-Governed Durable Fields**

Durable fields are defined by Metadata semantics.

**P5-DUR5 — Reference Identity**

Durable references contain Object Identity rather than Runtime Objects.

**P5-DUR6 — Runtime State Exclusion**

Runtime lifecycle state is excluded from durable state.

**P5-DUR7 — Durable System Field Separation**

Durable system fields are distinct from runtime system/lifecycle state.

**P5-DUR8 — No Storage Leakage**

Storage implementation details do not enter RuntimeDurableState.

**P5-DUR9 — Explicit Persistence Mapping**

Persistence translation is explicit.

**P5-DUR10 — No Implicit Attribute Persistence**

Arbitrary runtime attributes cannot become persistent state.

**P5-DUR11 — Semantic State Equivalence**

Runtime and persistence representations can be compared by durable semantics.

**P5-DUR12 — Durable State Is Not Persistence State**

RuntimeDurableState and PersistentObjectState are distinct boundary representations.

**P5-DUR13 — Boundary Representation Independence**

Neither boundary representation dictates the internal representation of the other.

---

# 53. Field Invariants

**P5-FLD1 — Metadata Identity**

Field keys use Metadata-defined identity.

**P5-FLD2 — Field Role**

Only `FIELD` semantics occur in `fields`.

**P5-FLD3 — Value Domain**

Field values are `NULL | DurableValue`.

**P5-FLD4 — Missing Semantics**

Missing key means `MISSING`.

**P5-FLD5 — Null Semantics**

Explicit `NULL` is distinct from `MISSING`.

**P5-FLD6 — Metadata Typing**

Field value interpretation is Metadata-governed.

**P5-FLD7 — No Runtime Objects**

Runtime objects cannot be field values.

**P5-FLD8 — No References**

Object relationships do not occur in `fields`.

**P5-FLD9 — No Business State**

Business state does not occur in `fields`.

**P5-FLD10 — No Change Tracking**

Dirty/change tracking does not occur in `fields`.

**P5-FLD11 — No Metadata Duplication**

Field definitions are not embedded in field state.

**P5-FLD12 — Snapshot**

Fields form an immutable snapshot.

**P5-FLD13 — Default Separation**

Metadata defaults are not implicitly materialized.

**P5-FLD14 — Validation Separation**

Generic field storage does not implement business validation.

**P5-FLD15 — Round-Trip Semantics**

Missing/null/value distinctions survive mapping.

---

# 54. Reference Invariants

**P5-REF1 — Metadata Identity**

Reference keys use Metadata identity.

**P5-REF2 — Reference Role**

Only `REFERENCE` semantics occur in `references`.

**P5-REF3 — Identity Representation**

References use Object Identity.

**P5-REF4 — Cardinality**

Reference cardinality is Metadata-defined.

**P5-REF5 — Null Semantics**

Explicit NULL is allowed only where Metadata permits it.

**P5-REF6 — Missing Semantics**

Missing key means `MISSING`.

**P5-REF7 — Empty Collection**

An explicit empty `MANY` collection is distinct from `MISSING`.

**P5-REF8 — Ordering Preservation**

Reference collection ordering is preserved.

**P5-REF9 — Duplicate Policy**

Duplicate policy is Metadata/Validation-defined.

**P5-REF10 — Target Type**

Target type is defined by Reference Metadata.

**P5-REF11 — Referential Resolution**

Resolution to Runtime Objects is outside durable state.

**P5-REF12 — Referential Integrity Separation**

Existence/integrity validation is not performed by the container itself.

**P5-REF13 — Cycle Safety**

Cycles are representable unless prohibited by Metadata/Validation.

**P5-REF14 — No Runtime State**

Reference loading/cache/proxy state is excluded.

**P5-REF15 — Snapshot**

References form an immutable snapshot.

**P5-REF16 — No Reference-as-Field**

References are not encoded as ordinary fields.

---

# 55. Business State Invariants

**P5-BSS1 — Definition Identity**

Each value is associated with a Business State Definition identity.

**P5-BSS2 — State Identity**

Each value uses State Value identity.

**P5-BSS3 — Closed Vocabulary**

State values must belong to the declared vocabulary.

**P5-BSS4 — No NULL**

Business-state values cannot be NULL.

**P5-BSS5 — Missing Semantics**

Missing dimension is represented by absence.

**P5-BSS6 — Completeness**

Complete valid objects must contain all required applicable dimensions.

**P5-BSS7 — Initial State Ownership**

Initial-state application belongs to object creation.

**P5-BSS8 — No Implicit Initialization**

Mapping never substitutes initial state.

**P5-BSS9 — Independent Dimensions**

Multiple independent dimensions are supported.

**P5-BSS10 — No Cartesian Product**

Dimensions are not automatically combined.

**P5-BSS11 — No Transition Graph**

Transition definitions are not stored in runtime state.

**P5-BSS12 — No History**

Transition history is not part of the snapshot.

**P5-BSS13 — No Runtime Lifecycle State**

Runtime lifecycle state is excluded.

**P5-BSS14 — Immutable Snapshot**

Business state is immutable within the snapshot.

---

# 56. Durable System Field Invariants

**P5-SYS1 — Platform Ownership**

System fields are platform-owned.

**P5-SYS2 — Durable Semantics**

System fields are part of durable object state.

**P5-SYS3 — Metadata Identity**

System-field identity is stable and semantic.

**P5-SYS4 — Durable Value Domain**

Values are `NULL | DurableValue`.

**P5-SYS5 — Missing Semantics**

Missing key means `MISSING`.

**P5-SYS6 — Runtime Exclusion**

Runtime lifecycle state is excluded.

**P5-SYS7 — Change Tracking Exclusion**

Change tracking is excluded.

**P5-SYS8 — Transaction Exclusion**

Transaction and locking state are excluded.

**P5-SYS9 — Reference Separation**

Domain relationships remain references.

**P5-SYS10 — Business State Separation**

Business lifecycle state remains business state.

**P5-SYS11 — Immutable Snapshot**

System fields form part of the immutable durable snapshot.

**P5-SYS12 — No Implicit Runtime Persistence**

Runtime attributes cannot become system fields implicitly.

---

# 57. Materialization Invariants

**P5-MAT1 — Explicit Source**

Materialization consumes `RuntimeDurableState`.

**P5-MAT2 — Identity Preservation**

Object Identity is preserved.

**P5-MAT3 — Type Identity Preservation**

Object Type Identity is preserved.

**P5-MAT4 — Field Preservation**

Fields are semantically preserved.

**P5-MAT5 — Reference Preservation**

Reference identities are semantically preserved.

**P5-MAT6 — Business State Preservation**

Business state is semantically preserved.

**P5-MAT7 — System Field Preservation**

Durable system fields are semantically preserved.

**P5-MAT8 — Missing/Null Preservation**

`MISSING` and `NULL` distinctions survive mapping.

**P5-MAT9 — No Runtime Attribute Inspection**

Materialization does not inspect arbitrary `ObjectInstance` attributes.

**P5-MAT10 — No Runtime State Persistence**

Runtime lifecycle state is not materialized.

**P5-MAT11 — No Initial-State Substitution**

Materialization does not generate business state.

**P5-MAT12 — No Reference Graph Traversal**

Materialization stores reference identities only.

---

# 58. Rejected Alternatives

## 58.1 Durable State Inside ObjectInstance

Rejected because it makes `ObjectInstance` simultaneously:

* runtime object;
* durable data model;
* persistence model;
* change-tracking model.

This violates the established Step 11 boundary.

---

## 58.2 Implicit Attribute Persistence

Rejected because persistence would depend on arbitrary Python runtime representation.

This creates hidden persistence semantics.

---

## 58.3 RuntimeDurableState Inherits PersistentObjectState

Rejected because Runtime must not depend on Persistence semantic models.

---

## 58.4 PersistentObjectState Inherits RuntimeDurableState

Rejected because Persistence must not depend on Runtime semantic models.

---

## 58.5 One Shared Mutable State Model

Rejected because it collapses boundary ownership and makes Runtime/Persistence representations coupled.

---

## 58.6 Generic `dict[str, object]`

Rejected as the final semantic architecture contract because it cannot express:

* durable value restrictions;
* identity semantics;
* NULL/MISSING distinction;
* reference semantics;
* business-state semantics;
* system-field semantics.

---

# 59. Final Architecture

```text
                         Metadata
                            │
                            │ semantic definitions
                            ▼
                         Runtime
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
      ObjectInstance               RuntimeDurableState
             │                             │
       runtime existence              durable semantics
             │                             │
       ┌─────┼─────┐             ┌────────┼─────────┐
       │     │     │             │        │         │
   identity type context       fields references business
       │             │                         state
   lifecycle         │                           │
                     │                    durable_system_fields
                     │                           │
                     └────────────┬──────────────┘
                                  │
                           Explicit Mapping
                                  │
                                  ▼
                        PersistentObjectState
                                  │
                                  ▼
                           PersistentObject
                                  │
                                  ▼
                            Persistence
                                  │
                                  ▼
                           StorageProvider
```

---

# 60. Implementation Gate

The Step 12 implementation gates have been satisfied. They are retained here as the final acceptance record for the completed implementation.

## P5-IG1 — Runtime Durable State Model

Define `RuntimeDurableState` as a distinct immutable semantic model.

Required:

* identity;
* object type identity;
* fields;
* references;
* business state;
* durable system fields.

Status: **CLOSED**

---

## P5-IG2 — Durable Value Contract

Define the implementation representation of `DurableValue`.

Required base kinds:

* Boolean;
* Integer;
* Decimal;
* String;
* Date;
* DateTime;
* Structured;
* Collection.

Status: **CLOSED**

---

## P5-IG3 — Field State Contract

Implement semantic representation of:

```text
FieldIdentity → NULL | DurableValue
```

including:

* immutable snapshot;
* MISSING by absent key;
* explicit NULL;
* Metadata identity.

Status: **CLOSED**

---

## P5-IG4 — Reference State Contract

Implement semantic representation of:

```text
ReferenceIdentity → ReferenceValue
```

including:

* SINGLE;
* MANY;
* Object Identity;
* explicit NULL for permitted SINGLE references;
* ordered collections;
* MISSING semantics.

Status: **CLOSED**

---

## P5-IG5 — Business State Snapshot Contract

Implement:

```text
BusinessStateDefinitionIdentity
    →
StateValueIdentity
```

with:

* immutable snapshot;
* closed vocabulary validation boundary;
* no NULL;
* MISSING semantics;
* no implicit initial-state substitution.

Status: **CLOSED**

---

## P5-IG6 — Durable System Field Contract

Implement:

```text
SystemFieldIdentity → NULL | DurableValue
```

with explicit exclusion of:

* runtime lifecycle;
* dirty/change tracking;
* transaction;
* locking;
* cache/loading state.

Status: **CLOSED**

---

## P5-IG7 — PersistentObjectState Boundary

Define/verify the persistence-side semantic representation corresponding to `RuntimeDurableState`.

It must represent the same durable semantics without importing Runtime concepts.

Status: **CLOSED**

---

## P5-IG8 — Explicit Hydration Mapping

Hydration must map:

```text
PersistentObjectState
        ↓
RuntimeDurableState
```

and associate the resulting durable state with:

```text
ObjectInstance
```

by Object Identity.

Status: **CLOSED**

---

## P5-IG9 — Explicit Materialization Mapping

Materialization must map:

```text
RuntimeDurableState
        ↓
PersistentObjectState
```

without reading arbitrary `ObjectInstance` attributes.

Status: **CLOSED**

---

## P5-IG10 — Metadata Compatibility Validation

Mapping must validate:

* object type identity;
* field identity;
* semantic role;
* reference cardinality;
* business-state vocabulary;
* durable value compatibility;
* system-field identity.

Status: **CLOSED**

---

## P5-IG11 — Semantic Round-Trip Tests

Tests must prove:

```text
PersistentObject
    →
PersistentObjectState
    →
RuntimeDurableState
    →
PersistentObjectState
    →
PersistentObject
```

preserves durable semantic equivalence.

Status: **CLOSED**

---

## P5-IG12 — Runtime State Isolation Tests

Tests must prove that changes to:

* ObjectContext;
* ObjectState;
* dirty state;
* loaded state;
* cache state;
* transaction state;
* runtime-only attributes

do not become durable state.

Status: **CLOSED**

---

## P5-IG13 — Missing/Null Tests

Tests must explicitly distinguish:

```text
MISSING
NULL
VALUE
```

for:

* fields;
* references;
* durable system fields.

Business state must additionally prove:

```text
MISSING
VALUE
```

with NULL rejected.

Status: **CLOSED**

---

## P5-IG14 — No Implicit Attribute Persistence Test

A runtime object containing arbitrary Python attributes must not cause those attributes to appear in materialized persistent state.

Status: **CLOSED**

---

## P5-IG15 — Reference Identity Test

Tests must prove that materialization/hydration preserves Object Identities without resolving them into `ObjectInstance` objects.

Status: **CLOSED**

---

## P5-IG16 — Business State Initialization Test

Tests must prove that:

```text
initial_state
```

is applied only by object creation semantics and is never substituted by Mapping during hydration.

Status: **CLOSED**

---

## P5-IG17 — Public API Boundary

Determine the intended public API exposure for:

* `RuntimeDurableState`;
* `DurableValue`;
* field/reference/business-state value contracts;
* mapping contracts.

No implementation type should become public merely because it exists internally.

Status: **CLOSED**

---

## P5-IG18 — Quality Gates

Before Step 12 implementation is considered complete:

```text
pytest
ruff check
black --check
mypy src
```

must pass.

Additional targeted semantic tests must cover all P5-DUR, P5-FLD, P5-REF, P5-BSS, P5-SYS and P5-MAT invariants relevant to the implemented scope.

Status: **CLOSED**

---

# 61. Implementation Sequence

The implementation sequence was completed in the following order:

```text
1. DurableValue semantic contract
       ↓
2. DurableValue Python implementation
       ↓
3. RuntimeDurableState
       ↓
4. Field state
       ↓
5. Reference state
       ↓
6. BusinessStateSnapshot
       ↓
7. Durable system fields
       ↓
8. PersistentObjectState alignment
       ↓
9. HydratedRuntimeObject
       ↓
10. Hydration mapping
       ↓
11. Materialization mapping
       ↓
12. Semantic round-trip tests
       ↓
13. Runtime isolation tests
       ↓
14. Public API
       ↓
15. Full quality gates
```

---

# 62. Definition of Done

Step 12 implementation is complete when:

1. `RuntimeDurableState` exists as a distinct immutable semantic model;
2. its four durable categories are explicitly represented;
3. `DurableValue` has a defined semantic and Python implementation
   contract;
4. all supported scalar and composite value kinds have immutable
   representations;
5. arbitrary Python objects cannot enter durable state as values;
6. NULL and MISSING remain distinct from DurableValue;
7. fields preserve Metadata identity and MISSING/NULL semantics;
8. references preserve Object Identity and cardinality semantics;
9. business state preserves declared state values without implicit initialization;
10. durable system fields are separated from runtime state;
11. `PersistentObjectState` represents the corresponding persistence-side durable semantics;
12. hydration is explicit;
13. materialization is explicit;
14. materialization does not inspect arbitrary runtime attributes;
15. runtime lifecycle state cannot leak into durable state;
16. semantic round-trip tests pass;
17. mapping incompatibilities are explicitly rejected;
18. no Storage-specific concepts leak into RuntimeDurableState;
19. project quality gates pass.

---

# 63. Final Validation

Step 12 and its materialization sub-sequence are complete. The final project-wide quality gate is:

```text
pytest
711 passed in 4.72s

ruff check .
All checks passed!

black --check .
All done! 152 files would be left unchanged.

mypy src
Success: no issues found in 79 source files
```

The completed implementation covers:

* Runtime Durable State;
* explicit hydration mapping;
* explicit materialization mapping;
* semantic round-trip preservation;
* runtime isolation;
* MISSING / NULL / VALUE preservation;
* reference identity preservation without graph traversal;
* public persistence API exposure;
* explicit materialization failure semantics.

The materialization boundary is implemented by `PersistentObjectMaterializer`;
`PersistentObjectMaterializationError` is part of the public persistence error
contract.

---

# 64. Final Principle

> **`RuntimeDurableState` is the Runtime semantic representation of an object's durable state. It is independent from `ObjectInstance`, Persistence and Storage, contains only explicitly classified durable semantics, and is converted to and from `PersistentObjectState` exclusively through an explicit mapping boundary.**

The final durable boundary is:

```text
ObjectInstance
    │
    │ associated by Object Identity
    ▼
RuntimeDurableState
    │
    │ explicit semantic mapping
    ▼
PersistentObjectState
    │
    ▼
PersistentObject
```

No implicit attribute persistence, no runtime-state persistence, no storage leakage, and no hidden transformation of business semantics are permitted.
