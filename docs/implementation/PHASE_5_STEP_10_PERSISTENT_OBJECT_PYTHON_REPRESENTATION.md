# Phase 5 — Step 10: Persistent Object Python Representation

**Status:** Implemented
**Phase:** 5 — Storage & Persistence Boundary
**Step:** 10
**Version:** 1.0
**Date:** 2026-09-10

---

## 1. Purpose

This document defines the concrete immutable Python representation of a Persistent Object established by Steps 7–9.

The representation is a semantic persistence type. It is not a database row, EAV record, serialized payload, or Runtime Object snapshot.

---

## 2. Canonical Representation

```python
@dataclass(frozen=True, slots=True)
class PersistentField:
    name: str
    value: object | None = None


@dataclass(frozen=True, slots=True)
class PersistentObjectState:
    fields: tuple[PersistentField, ...] = ()
    business_state: object | None = None
    system_fields: tuple[PersistentField, ...] = ()


@dataclass(frozen=True, slots=True)
class PersistentObject:
    identity: Identifier
    object_type_identity: Identifier
    state: PersistentObjectState
```

The concrete implementation is located in:

```text
src/accore/platform/persistence/objects.py
```

---

## 3. PersistentField

`PersistentField` represents one logical durable field value.

Its identity is the canonical logical field name from the current Metadata model.

The value is represented as `object | None` at this implementation stage because the repository does not yet contain a standalone Platform Value hierarchy.

This does not mean arbitrary values are semantically valid. Applicable Metadata and Platform Type semantics remain authoritative.

---

## 4. PersistentObjectState

`PersistentObjectState` groups durable object state into:

* business fields;
* optional business state;
* system fields.

Business and system field names must be unique within their respective groups and may not collide with one another.

Field order has no semantic meaning.

The tuple representation prevents accidental mutation of the collection itself.

---

## 5. PersistentObject

`PersistentObject` contains exactly the durable structural identity required by the Object Persistence boundary:

```text
Object Identity
Object Type Identity
Persistent State
```

Object identity uses the existing `foundation.Identifier`.

Object type identity is the metadata identity obtained from the resolved `RuntimeObjectType`.

No Runtime Object Type instance is persisted.

---

## 6. Immutability

All three representation types are frozen and use tuples for collections.

`ObjectPersistence.update()` therefore receives a complete replacement representation.

There is no implicit PATCH or partial-update semantics.

Deep immutability of individual platform values remains the responsibility of the future concrete Platform Value model.

---

## 7. Validation Boundary

The representation performs only structural checks required to keep the representation coherent:

* field name must be non-empty;
* business field names must be unique;
* system field names must be unique;
* business and system field names must not collide.

It does not become a second Metadata Validation Engine.

Type validity, required fields, nullable rules, reference targets and other metadata constraints remain outside this representation.

---

## 8. Deliberately Excluded

The representation does not contain:

* `ObjectInstance`;
* `RuntimeObjectType` instances;
* `ObjectContext`;
* `RuntimeConfigurationContext`;
* `ActiveConfiguration`;
* Runtime services;
* caches;
* `StorageKey`;
* serialized bytes;
* transaction/session/provider handles;
* register movements;
* `MovementSet`;
* balances or turnovers;
* a universal version field.

---

## 9. EAV Boundary

The representation is deliberately EAV-neutral.

A physical implementation may map `PersistentField` values to EAV storage, fixed columns, JSON/document storage, or a hybrid strategy.

None of those choices changes the Python persistence contract.

---

## 10. Acceptance Criteria

- [x] Concrete immutable `PersistentField` exists.
- [x] Concrete immutable `PersistentObjectState` exists.
- [x] Concrete immutable `PersistentObject` exists.
- [x] Existing `Identifier` is reused.
- [x] Object Type Identity is represented by metadata identity.
- [x] Runtime Object Type instances are excluded.
- [x] Runtime Object State is excluded.
- [x] Business and system state remain distinct.
- [x] Complete replacement semantics are preserved.
- [x] No physical storage schema is introduced.
- [x] No EAV semantics leak into the persistence API.
