# Phase 5 — Persistence API Matrix

**Phase:** 5 — Storage & Persistence Boundary
**Step:** 3 — Persistence Contracts
**Status:** Architecture Definition
**Version:** 1.0
**Related ADR:** `ADR-P5-001`
**Related Model:** `PHASE_5_PERSISTENCE_DOMAIN_MODEL.md`

---

## 1. Purpose

This matrix defines which persistence operations are architecturally applicable to the principal persistent resource categories of AcCoreD.

The matrix is a **contract-design constraint**, not a requirement that every implementation expose a single universal CRUD interface.

The architecture distinguishes persistence semantics first. Individual persistence contracts expose only the operations supported by the corresponding resource and lifecycle.

---

## 2. Persistence API Matrix

| Persistent Resource / Capability   | Create | Read | Update | Replace |  Delete  | Append | Query | Scope |
| ---------------------------------- | :----: | :--: | :----: | :-----: | :------: | :----: | :---: | :---: |
| **Persistent Object**              |    ✓   |   ✓  |   ✓*   |    ✓*   | optional |    —   |   —   |   ✓   |
| **Register Fact**                  |    —   |   —  |    —   |    —    |     —    |    ✓   |   ✓   |   ✓   |
| **Configuration Persistent State** |   ✓*   |   ✓  |   ✓*   |    ✓*   |     —    |    —   |   ✓   |   ✓   |

### Interpretation

* `✓` — operation is architecturally supported.
* `✓*` — operation may be supported depending on the lifecycle semantics of the specific resource.
* `optional` — operation is not universally applicable and must be explicitly supported by the resource contract.
* `—` — operation is not part of the corresponding persistence semantics.

---

## 3. Persistent Object

Persistent Objects represent durable state belonging to logical domain objects.

Their persistence semantics are generally state-oriented.

### Supported capabilities

| Operation |  Status  | Meaning                                                                                                                            |
| --------- | :------: | ---------------------------------------------------------------------------------------------------------------------------------- |
| Create    |     ✓    | Create persistent state for a new logical object.                                                                                  |
| Read      |     ✓    | Retrieve persistent state by logical identity.                                                                                     |
| Update    |    ✓*    | Modify selected persistent state where lifecycle permits mutation.                                                                 |
| Replace   |    ✓*    | Replace the complete persistent representation where lifecycle permits replacement.                                                |
| Delete    | Optional | Remove persistent state only where the object's lifecycle explicitly permits deletion.                                             |
| Append    |     —    | Persistent Object state is not append-only fact storage.                                                                           |
| Query     |     —    | Generic querying is not defined as part of the object persistence primitive. Domain-specific query contracts may exist separately. |
| Scope     |     ✓    | Object operations may participate in a Persistence Scope.                                                                          |

### Update vs Replace

`Update` and `Replace` remain architecturally distinct:

* **Update** changes selected or defined portions of existing state.
* **Replace** substitutes the complete persistent representation.

An individual object persistence contract does not have to expose both operations.

---

## 4. Register Fact

Register Facts represent accepted business facts produced by Posting and accepted by the Register.

Their persistence semantics are **append-oriented and historical**.

### Supported capabilities

| Operation | Status | Meaning                                                                                  |
| --------- | :----: | ---------------------------------------------------------------------------------------- |
| Create    |    —   | A fact is not created through generic object creation semantics.                         |
| Read      |    —   | Individual fact retrieval is not a primitive requirement of the fact-append contract.    |
| Update    |    —   | Accepted historical facts are not mutable through ordinary persistence update semantics. |
| Replace   |    —   | Historical facts are not replaced as object state.                                       |
| Delete    |    —   | Deletion is not a default fact persistence operation.                                    |
| Append    |    ✓   | Persist an accepted set of Register Facts.                                               |
| Query     |    ✓   | Retrieve facts through logical, domain-specific query contracts.                         |
| Scope     |    ✓   | Fact append operations may participate in a Persistence Scope.                           |

### Architectural flow

```text
Posting
   │
   ▼
MovementSet
   │
   ▼
Register
   │
   ▼
Accepted Register Facts
   │
   ▼
Fact Persistence
   │
   ▼
Persistent Storage
```

Storage and persistence do not produce business facts.

---

## 5. Configuration Persistent State

Configuration persistence stores the durable state required to reconstruct a logical configuration.

It does **not** persist the runtime `ActiveConfiguration` object itself.

### Supported capabilities

| Operation | Status | Meaning                                                                                                  |
| --------- | :----: | -------------------------------------------------------------------------------------------------------- |
| Create    |   ✓*   | Persist a new configuration state where the configuration lifecycle permits creation.                    |
| Read      |    ✓   | Retrieve configuration persistent state.                                                                 |
| Update    |   ✓*   | Modify configuration state where lifecycle semantics permit mutation.                                    |
| Replace   |   ✓*   | Replace a complete configuration representation where supported.                                         |
| Delete    |    —   | Configuration deletion is not a generic persistence capability.                                          |
| Append    |    —   | Configuration state is not append-only fact storage.                                                     |
| Query     |    ✓   | Locate configuration state by logical configuration identity, version, or other domain-defined criteria. |
| Scope     |    ✓   | Configuration persistence may participate in a Persistence Scope.                                        |

Configuration lifecycle remains outside the persistence layer:

```text
Persistent Configuration State
          │
          ▼
       Loading
          │
          ▼
      Validation
          │
          ▼
       Activation
          │
          ▼
 ActiveConfiguration
          │
          ▼
RuntimeConfigurationContext
```

Persistence does not validate, compile, activate, or resolve configuration.

---

## 6. Scope Is Cross-Cutting

`Persistence Scope` is not a resource-specific operation.

It defines the logical consistency boundary within which multiple persistence operations may participate.

Conceptually:

```text
Persistence Scope
      │
      ├── Object Persistence
      │      ├── Create
      │      └── Update
      │
      └── Fact Persistence
             └── Append
```

The architecture does not currently prescribe whether a Persistence Scope is implemented using:

* a database transaction;
* a session;
* a unit-of-work mechanism;
* a journal;
* a distributed transaction;
* or another provider-specific mechanism.

Those decisions belong to the Storage Provider layer.

---

## 7. Query Is Not CRUD

Query is intentionally separated from the primitive object persistence operations.

The architecture does not define a universal query language such as:

```text
Query(entity, filters, ordering, projection)
```

Instead, higher-level components may define typed, domain-specific query contracts such as:

```text
RegisterFactsQuery
ConfigurationStateQuery
ObjectLookupQuery
```

These contracts must remain independent of physical query technologies.

---

## 8. Delete Is Capability-Based

Deletion is not a universal persistence operation.

A resource may be:

* immutable;
* append-only;
* lifecycle-controlled;
* logically retired rather than physically deleted;
* or otherwise non-deletable.

Therefore:

> The existence of a persistence boundary does not imply that every persistent resource supports deletion.

---

## 9. Contract Design Rule

The API Matrix defines **architectural applicability**, not a universal interface.

The implementation MUST NOT introduce a mandatory interface equivalent to:

```python
class Repository:
    create(...)
    read(...)
    update(...)
    replace(...)
    delete(...)
    append(...)
    query(...)
```

Instead, persistence contracts should be capability-specific.

For example:

```text
ObjectPersistence
FactPersistence
ConfigurationPersistence
PersistenceScope
```

Each contract exposes only the semantics relevant to its resource category.

---

## 10. Architectural Invariants

The API Matrix establishes the following invariants:

### P5-API-I1 — No Universal CRUD Contract

Persistence MUST NOT be represented by one universal CRUD interface.

### P5-API-I2 — Object and Fact Persistence Are Distinct

Persistent Object state and Register Facts MUST remain separate persistence semantics.

### P5-API-I3 — Append Is Distinct from Update

Appending a Register Fact MUST NOT be modeled as an ordinary object update.

### P5-API-I4 — Delete Is Not Universal

Deletion MUST be capability-based and lifecycle-dependent.

### P5-API-I5 — Query Is a Separate Capability

Query MUST NOT be reduced to generic CRUD operations.

### P5-API-I6 — Scope Is Cross-Cutting

Persistence Scope MUST remain independent of individual resource types.

### P5-API-I7 — Physical Implementation Is Hidden

No matrix entry implies a particular database, schema, ORM, transaction mechanism, or serialization format.

### P5-API-I8 — Architecture Precedes Interface Shape

The matrix defines persistence semantics before concrete Python method signatures are introduced.

---

## 11. Decision

The Phase 5 Persistence API Matrix is accepted as the architectural baseline for implementation.

The next design activity is to translate these capabilities into **concrete Python persistence contracts** without introducing a universal repository, query language, or premature transaction abstraction.
