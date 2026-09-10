# Phase 5 — Step 9: Existing Domain Type Reuse / Mapping

**Status:** Final — Implemented
**Phase:** 5 — Storage & Persistence Boundary
**Step:** 9
**Version:** 1.0
**Date:** 2026-09-10

---

## 1. Purpose

This document defines how the Persistent Object representation reuses existing AcCoreD domain and metadata concepts.

The goal is to avoid introducing a second parallel type system inside Persistence while preserving the distinction between Runtime state and durable state.

---

## 2. Existing Types and Reuse Decisions

| Existing concept | Persistence mapping | Decision |
|---|---|---|
| `foundation.Identifier` | Object Identity | Reuse directly |
| `RuntimeObjectType.metadata_identity()` | Object Type Identity | Persist returned metadata identity |
| `AttributeDefinition.name` / `AttributeMetadata.name` | Logical field identity | Reuse canonical logical field name |
| `AttributeType` | Metadata-declared field type | Reuse as metadata/type authority; do not duplicate it |
| Platform Type System | Field value semantics | Persistence representation remains independent of physical storage |
| Object Reference | Reference field value | Preserve target Object Identity semantics; do not persist runtime object instances |
| `SystemFieldMetadata` | System field definition | Reuse metadata definition; persistence stores corresponding durable value |
| `ObjectState` | Runtime lifecycle state | Do not persist automatically |
| Business State | Durable business state | Represent separately from runtime `ObjectState` |

---

## 3. Attribute Identity

The current Metadata model identifies attributes by their canonical logical names.

Persistence therefore uses:

```text
PersistentField.name
```

as the logical field identity.

No new universal `PersistentFieldId` is introduced at this stage.

If Metadata later acquires an explicit field identity, Persistence may adopt that identity without changing the semantic role of `PersistentField`.

---

## 4. Attribute Types

The existing `AttributeType` enum already describes the attribute categories currently supported by the implementation:

```text
STRING
INTEGER
DECIMAL
BOOLEAN
DATE
DATETIME
REFERENCE
ENUM
```

Persistence does not introduce another enum or duplicate type hierarchy.

`AttributeType` remains Metadata vocabulary. Persistent values must obey the semantics declared by the applicable Metadata.

The physical representation of those values remains below the Persistence representation boundary.

---

## 5. Platform Type System

The architecture already defines a platform-wide Type System including String, Text, Boolean, Integer, Decimal, Date, DateTime, Binary, Money, Quantity, Reference and Enum concepts.

The current Python implementation has not yet introduced a standalone runtime `PlatformType` value hierarchy.

Therefore Step 9 does **not** manufacture one inside Persistence.

The Persistent Object representation remains type-neutral at the Python boundary while Metadata remains authoritative for value semantics.

This is an intentional temporary implementation boundary, not a second type system.

---

## 6. Object References

An object reference is semantically a relationship based on Object Identity.

Persistence must therefore retain the target identity, not:

* a Runtime Object;
* an `ObjectInstance`;
* a `ResolvedReference`;
* a Runtime service;
* a provider-specific foreign key.

The exact concrete Python value class for reference values remains deferred until the platform reference value model is implemented.

---

## 7. System Fields

`SystemFieldMetadata` remains the authoritative description of platform-managed system fields.

Persistence does not redefine system field metadata.

The current implementation contains system-field definitions such as:

```text
id
created_at
updated_at
deleted
version
```

Their presence in a particular persistent object remains governed by applicable Metadata and system-field rules.

A future concurrency/versioning contract may give `version` additional semantics, but Step 9 does not invent such semantics.

---

## 8. Runtime State Separation

The existing runtime `ObjectState` enum is:

```text
CREATED
ACTIVE
DISPOSED
```

It is not part of the Persistent Object representation.

Persistence stores durable business state and durable system state only when those concepts have an explicit persistence contract.

---

## 9. Canonical Mapping

```text
Runtime Object
    │
    ├── ObjectInstance.identity
    │        ↓
    │   PersistentObject.identity
    │
    ├── RuntimeObjectType.metadata_identity()
    │        ↓
    │   PersistentObject.object_type_identity
    │
    └── Durable business/system values
             ↓
        PersistentObjectState
             ├── PersistentField
             ├── business_state
             └── system_fields
```

Runtime-only context and behavior do not cross this boundary.

---

## 10. EAV Position

EAV is not part of this mapping.

The semantic model remains:

```text
PersistentField
```

rather than an EAV row or attribute-value storage record.

EAV remains an eligible physical persistence strategy below this boundary.

---

## 11. Acceptance Criteria

- [x] Existing `Identifier` is reused for object identity.
- [x] Runtime Object Type is reduced to metadata identity.
- [x] Existing logical attribute names are reused as current field identity.
- [x] Existing `AttributeType` remains Metadata vocabulary.
- [x] Persistence does not introduce a second Platform Type hierarchy.
- [x] References retain Object Identity semantics.
- [x] Runtime `ObjectState` is not persisted automatically.
- [x] System field definitions remain owned by Metadata.
- [x] EAV is not exposed by the semantic persistence representation.
- [x] Physical storage strategy remains deferred.
