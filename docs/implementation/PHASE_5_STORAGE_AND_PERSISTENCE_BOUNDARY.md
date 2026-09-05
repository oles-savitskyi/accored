# Phase 5 — Storage & Persistence Boundary

**Status:** Architectural Definition
**Phase:** 5 — Storage & Persistence Boundary
**Version:** 1.0
**Date:** 2026-09-02

---

## 1. Purpose

This document defines the architectural boundary between AcCore Runtime and persistent system state.

The purpose of Phase 5 is to establish how AcCore represents, accesses, and preserves durable state without coupling Runtime, Metadata, Object, Posting, Register, Valuation, Reporting, or other platform subsystems to a particular physical storage technology.

Phase 5 defines the logical Storage and Persistence architecture.

It does **not** define a concrete database, file format, ORM, physical schema, indexing strategy, or storage engine.

---

## 2. Architectural Context

AcCore is a metadata-driven platform.

Metadata defines logical business structures, while Runtime interprets those definitions and executes business functionality.

Runtime Objects are executable representations of Domain Objects. Their runtime state exists for execution and is not itself the physical persistence model.

The Storage subsystem provides the persistence boundary between logical platform state and physical storage.

The fundamental relationship is:

```text
Logical Platform State
        │
        ▼
Persistence Boundary
        │
        ▼
Storage Subsystem
        │
        ▼
Storage Provider
        │
        ▼
Physical Storage
```

The physical representation is an implementation concern of Storage and must remain invisible to Runtime.

---

## 3. Scope

Phase 5 establishes:

* the Storage and Persistence boundary;
* the distinction between logical persistent state and runtime state;
* the responsibility of Storage;
* the responsibility of Persistence contracts;
* the relationship between Runtime and persistent representations;
* persistence responsibilities for business objects;
* persistence responsibilities for register facts;
* the role of configuration persistence;
* transaction and consistency boundaries at the architectural level;
* physical storage independence;
* rules governing Storage Providers;
* architectural invariants;
* deferred architectural decisions.

---

## 4. Non-Goals

Phase 5 does not yet define:

* PostgreSQL, SQLite, or another database;
* a database schema;
* table names;
* column layouts;
* indexes;
* ORM selection;
* SQL generation;
* serialization format;
* migration implementation;
* connection pooling;
* caching implementation;
* sharding;
* replication;
* physical partitioning;
* a universal Repository abstraction;
* a concrete Unit of Work implementation.

These decisions may be addressed by later Storage implementation phases.

---

# 5. Persistence and Storage

## 5.1 Persistence

Persistence is the architectural capability that makes logical system state durable and allows that state to be recovered.

Persistence is concerned with semantic operations such as:

* create;
* load;
* update;
* version;
* delete, where permitted;
* append;
* query;
* existence;
* consistency;
* transaction coordination.

Persistence contracts describe what the platform needs to preserve or retrieve.

They must not describe the physical representation used to accomplish those operations.

---

## 5.2 Storage

Storage is the platform subsystem responsible for implementing persistence.

Storage determines how logical persistent state is represented physically.

Storage may use:

* relational storage;
* document storage;
* embedded storage;
* file-based storage;
* hybrid storage;
* future storage technologies.

The choice of physical mechanism is not part of the logical Storage contract.

---

## 5.3 Storage Provider

A Storage Provider is a concrete implementation of the Storage subsystem.

A Storage Provider must implement the logical behavior required by the platform while remaining replaceable.

For example:

```text
Storage Contract
      │
      ├── SQLite Provider
      ├── PostgreSQL Provider
      ├── Embedded Provider
      └── Future Provider
```

Provider-specific behavior must not leak into Runtime or domain semantics.

---

# 6. Persistence Boundary

The Persistence Boundary separates logical platform state from physical storage.

The architectural dependency direction is:

```text
Runtime / Domain / Application
            │
            ▼
    Persistence Contracts
            │
            ▼
        Storage
            │
            ▼
    Storage Provider
            │
            ▼
    Physical Storage
```

The reverse dependency is prohibited:

```text
Physical Storage
       X
       │
       ▼
Runtime semantics
```

Runtime must not derive its business semantics from:

* database tables;
* storage-specific identifiers;
* SQL expressions;
* document layouts;
* EAV implementation details;
* provider-specific query APIs.

---

# 7. Logical State and Physical Representation

AcCore distinguishes between logical state and physical representation.

A logical business field is defined by Metadata.

Its physical representation is determined by Storage.

For example:

```text
Logical Field
      │
      ├── primary representation
      ├── EAV representation
      └── future representation
```

The Logical Field Model therefore remains independent of physical storage.

EAV, indexes, partitioning, denormalization, materialization, and similar mechanisms are Storage implementation details.

---

# 8. Runtime State vs Persistent State

Runtime state and persistent state are different architectural concepts.

## Runtime State

Runtime state exists to support execution.

Examples include:

* Runtime Object instances;
* resolved references;
* compiled metadata;
* runtime bindings;
* resolver state;
* execution context;
* caches;
* temporary calculations.

Runtime state may be reconstructed, discarded, or recreated.

It is not automatically persistent merely because it exists in memory.

## Persistent State

Persistent state represents durable system information.

Examples include:

* Persistent Entities;
* Persistent Objects;
* business documents;
* catalog records;
* register records;
* configuration definitions and versions;
* constants;
* sequences;
* other explicitly persistent platform state.

Persistent state must have a defined persistence contract.

---

# 9. Persistent Objects

A Persistent Object is the persistence representation of a Runtime Object.

The relationship is:

```text
Metadata
    │
    ▼
Runtime Object
    │
    │ persistence mapping
    ▼
Persistent Object
```

The Persistent Object exists for durability rather than execution.

The mapping between Runtime Object and Persistent Object belongs to the Storage architecture.

Runtime must not depend on the physical representation of a Persistent Object.

Object Identity remains the logical identity of the business object.

Physical storage identifiers, if any, are implementation details.

---

# 10. Persistent Entities

Persistent Entities are logical storage entities that participate in persistence lifecycle operations.

AcCore recognizes Persistent Entities such as:

* Catalogs;
* Documents;
* Registers;
* Constants;
* Sequences.

A Persistent Entity has a logical identity and defined persistence lifecycle.

Its physical representation is determined by Storage.

A Persistent Entity may be implemented as one or more physical structures.

Therefore:

```text
1 Logical Entity
        ≠
1 Physical Table
```

The mapping is a Storage concern.

---

# 11. Configuration Persistence

Configuration is metadata-driven and participates in a lifecycle that includes definition, validation, activation, upgrade, and retirement.

The Runtime representation of an active configuration is not itself the physical persistence format.

The architectural flow is:

```text
Persistent Configuration State
            │
            ▼
Configuration Loading
            │
            ▼
Validation / Composition
            │
            ▼
Active Configuration
            │
            ▼
Runtime Configuration Context
```

Persistence must preserve the information required to reconstruct the logical configuration state.

The exact serialized or physical representation is deferred.

Configuration persistence must remain compatible with:

* configuration identity;
* configuration version;
* lifecycle state;
* metadata composition;
* activation semantics.

---

# 12. Object Persistence

Object persistence preserves the durable state of business objects.

At the logical level:

```text
Object Identity
Object Type
Object State
Object References
System Fields
Version Information
```

may participate in persistence according to the object's metadata and lifecycle.

Storage determines how these elements are physically represented.

Object persistence must preserve Object Identity independently of:

* business numbering;
* names;
* physical row identifiers;
* storage provider;
* physical schema.

---

# 13. Register Persistence

Registers are persistent structures representing business facts.

A Register Record is a persistent fact stored within a register.

Posting produces validated movements.

The architectural flow is:

```text
Business Object
      │
      ▼
Posting Handler
      │
      ▼
MovementSet
      │
      ▼
Register
      │
      ▼
Register Persistence
```

Storage does not generate accounting meaning.

Storage persists register facts accepted by the Register architecture.

In particular:

```text
Posting
   ──produces──► Facts

Storage
   ──persists──► Facts
```

Storage must not:

* calculate posting logic;
* interpret accounting rules;
* generate business movements;
* decide which movements are valid;
* implement valuation logic.

---

# 14. Register Movements and Totals

Accumulation Registers contain historical movements and derived totals.

Movements are primary business facts.

Totals are derived state maintained for efficient access.

The logical relationship is:

```text
Register Movements
        │
        ▼
   Totals Engine
        │
        ▼
 Materialized Totals
```

Whether totals are physically stored, rebuilt, partially materialized, indexed, or otherwise optimized is a Storage/Runtime implementation concern.

The logical behavior must remain equivalent.

A Storage optimization must never change:

* register semantics;
* balances;
* turnovers;
* temporal query meaning;
* historical facts.

---

# 15. Transaction and Consistency Boundary

Phase 5 establishes that persistence operations may require atomic consistency across related persistent state.

A business operation must not expose partially committed persistent state where the architecture requires atomicity.

For example, posting may conceptually require coordinated persistence of:

```text
Posted Object State
        +
Register Movements
        +
Required Derived State
```

The exact transaction mechanism is deferred.

The architecture therefore defines the **consistency requirement**, not the transaction technology.

A transaction may eventually be implemented through:

* database transactions;
* journaled persistence;
* command logs;
* other mechanisms.

The selected mechanism must preserve the logical consistency guarantees.

---

# 16. Query Boundary

Logical queries must be expressed in terms of logical platform concepts.

Examples include:

* object lookup;
* register movement query;
* balance query;
* turnover query;
* temporal query.

Queries must not expose physical storage layout.

Therefore:

```text
Register Query
      │
      ▼
logical query execution
      │
      ▼
Storage
```

rather than:

```text
Runtime
      │
      ▼
SQL / physical schema
```

This preserves the existing Register Query model, which is explicitly independent of storage layout and aggregation implementation details.

---

# 17. Storage and References

Object References are based on logical Object Identity.

Reference resolution occurs through Runtime.

Storage is responsible for making the persistent object state available, but Storage does not own reference semantics.

Therefore:

```text
Reference
   │
   ▼
Runtime Resolution
   │
   ▼
Object Identity
   │
   ▼
Persistent Object lookup
```

The physical identifier of a stored object must never become the architectural identity of that object.

---

# 18. Storage and Metadata

Metadata defines logical structures.

Storage provides their durable representation.

The dependency is:

```text
Metadata
   │
   ▼
Logical Model
   │
   ▼
Storage Mapping
   │
   ▼
Physical Representation
```

Metadata must not contain physical storage instructions such as:

* table names;
* SQL types;
* indexes;
* partition names;
* provider-specific syntax.

Metadata may define logical properties required by persistence.

Storage determines the physical realization.

---

# 19. Storage and Business Logic

Storage contains no business logic.

Business semantics belong to the appropriate architectural subsystem.

Examples:

| Responsibility          | Owner            |
| ----------------------- | ---------------- |
| Metadata semantics      | Metadata         |
| Object behavior         | Runtime / Domain |
| Posting rules           | Posting          |
| Register acceptance     | Register         |
| Valuation rules         | Valuation        |
| Reporting semantics     | Reporting        |
| Persistence             | Storage          |
| Physical representation | Storage Provider |

Storage may enforce technical integrity required to preserve the platform contract, but it must not become a hidden business rules engine.

---

# 20. Storage Independence

The logical platform must remain functionally equivalent across Storage Providers.

For a given logical operation:

```text
Logical Input
      │
      ▼
Persistence Contract
      │
      ├── Provider A
      ├── Provider B
      └── Provider C
```

the provider may differ in implementation but must preserve the required logical result and guarantees.

This permits future support for different deployment models without changing business architecture.

---

# 21. Architectural Invariants

### P5-I1 — Physical Storage Independence

The platform architecture does not depend on a specific physical storage technology.

### P5-I2 — Storage Has No Business Semantics

Storage persists and retrieves state but does not define business meaning.

### P5-I3 — Runtime Is Not the Persistence Model

Runtime objects and runtime execution state are distinct from persistent representations.

### P5-I4 — Persistent Identity Is Logical

Object identity is independent of physical storage identifiers.

### P5-I5 — Persistence Contracts Are Semantic

Persistence contracts express logical persistence requirements rather than physical storage mechanisms.

### P5-I6 — Register Facts Are Produced Outside Storage

Posting and Register architecture determine business facts. Storage only persists accepted facts.

### P5-I7 — Derived State Is Reconstructible

Derived state such as totals must not redefine the meaning of primary business facts.

### P5-I8 — Physical Schema Is Deferred

Physical schema decisions are implementation decisions and are not fixed by this architectural definition.

### P5-I9 — Provider Substitutability

A Storage Provider may be replaced without changing the logical semantics of the platform.

### P5-I10 — Logical Fields Remain Physical-Storage Independent

Runtime and Metadata operate on Logical Fields; Storage determines their physical persistence.

---

# 22. Architectural Boundary Summary

The Phase 5 boundary can be represented as:

```text
┌──────────────────────────────────────────┐
│              AcCore Runtime              │
│                                          │
│ Metadata │ Objects │ Posting │ Registers│
│ Valuation│ Reporting │ Configuration    │
└────────────────────┬─────────────────────┘
                     │
                     │ Logical persistence
                     │ contracts
                     ▼
┌──────────────────────────────────────────┐
│          Persistence Boundary            │
│                                          │
│ Object Persistence                       │
│ Register Persistence                     │
│ Configuration Persistence                │
│ Query / Retrieval                        │
│ Consistency / Transaction Semantics      │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│                 Storage                  │
│                                          │
│ Entity Mapping                           │
│ Physical Representation                  │
│ Provider Coordination                    │
│ Storage Optimization                     │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│            Storage Provider               │
│                                          │
│ Concrete persistence technology          │
└────────────────────┬─────────────────────┘
                     │
                     ▼
             Physical Storage
```

---

# 23. Deferred Decisions

The following decisions remain intentionally open:

1. Concrete Storage Provider technology.
2. Physical schema.
3. Primary vs EAV representation strategy.
4. Serialization format.
5. Repository shape.
6. Unit of Work or equivalent transaction abstraction.
7. Connection/session model.
8. Query execution model.
9. Physical indexing.
10. Partitioning and sharding.
11. Persistence caching.
12. Migration mechanism.
13. Physical totals representation.
14. Storage-level concurrency strategy.

These decisions must be evaluated against the contracts established by Phase 5.

---

# 24. Next Step

The next architectural step is:

**Phase 5 — Step 2: Persistence Domain Model**

Step 2 will define the logical persistence concepts and contracts required by AcCore, including the distinction between:

* persistent entities;
* persistent objects;
* register records;
* configuration state;
* queries;
* persistence operations;
* consistency boundaries.

No concrete database implementation should be introduced before those contracts are defined.
