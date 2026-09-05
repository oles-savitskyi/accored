# Phase 5 — Persistence Domain Model

**Document:** `PHASE_5_PERSISTENCE_DOMAIN_MODEL.md`
**Phase:** 5 — Storage & Persistence Boundary
**Status:** Architecture Definition
**Version:** 1.0
**Related ADR:** `ADR-P5-001`
**Previous Phase:** Phase 4 — Runtime & Object Boundary
**Next Step:** Step 3 — Persistence Contracts

---

## 1. Purpose

This document defines the **Persistence Domain Model** for AcCoreD.

The purpose of this model is to establish the logical concepts and semantics required to persist durable system state without coupling the application architecture to a particular storage technology.

The model defines:

* what constitutes persistent state;
* what kinds of resources may be persisted;
* the distinction between runtime state and persistent state;
* the distinction between persistent objects and register facts;
* persistence operations and their semantics;
* persistence queries;
* persistence consistency scopes;
* identity and version semantics;
* persistence lifecycle concepts;
* semantic persistence errors;
* concurrency-related semantics;
* architectural invariants.

This document intentionally does **not** define:

* a database technology;
* a physical database schema;
* tables or collections;
* SQL;
* ORM models;
* serialization formats;
* indexes;
* database-specific transactions;
* a concrete storage provider.

Those concerns belong to later implementation stages.

---

# 2. Architectural Context

Phase 5 establishes the boundary between the runtime/domain side of AcCoreD and durable storage.

The architectural relationship is:

```text
┌──────────────────────────────────────────────────────────────┐
│                    Runtime / Domain                          │
│                                                              │
│  Runtime Objects                                             │
│  Documents                                                   │
│  Business Operations                                         │
│  Posting                                                      │
│  Register Processing                                         │
│  Configuration Runtime                                       │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ Persistence Boundary
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Persistence Domain                           │
│                                                              │
│  Persistent Resources                                        │
│  Persistent Objects                                           │
│  Register Facts                                               │
│  Configuration Persistent State                               │
│  Persistence Operations                                       │
│  Persistence Queries                                          │
│  Persistence Scopes                                           │
│  Identity / Version Semantics                                  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ Storage Boundary
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                         Storage                               │
│                                                              │
│  Storage Provider                                             │
│  Physical Storage                                             │
│                                                              │
│  Technology-specific implementation                           │
└──────────────────────────────────────────────────────────────┘
```

The Persistence Domain Model is therefore an intermediate architectural layer.

It describes **what persistence means to AcCoreD**, rather than **how a storage technology implements it**.

---

# 3. Scope

This model covers durable state belonging to the AcCoreD platform and its business domains.

It applies to persistence of:

* business objects;
* document state;
* configuration state;
* register facts;
* other durable domain state introduced by later modules.

It does not make every runtime object persistent.

In particular, temporary or derived runtime state may exist without having persistence semantics.

Examples include:

* runtime resolution context;
* resolver instances;
* compiled metadata;
* caches;
* temporary calculation state;
* transient application state;
* other implementation-level runtime structures.

Whether a particular resource is persistent is an architectural decision and must not be inferred merely from the fact that it exists as a runtime object.

---

# 4. Core Principle

The central principle of the Persistence Domain Model is:

> **Persistence represents durable logical state; it does not define the runtime model or the business model.**

Runtime objects exist to execute application behavior.

Persistent resources exist to preserve durable state.

Storage exists to implement the persistence boundary.

These are related concepts, but they are not interchangeable.

---

# 5. Core Concepts

## 5.1 Persistent Resource

A **Persistent Resource** is a logical AcCoreD resource whose state has persistence semantics and can be stored and subsequently recovered through the Persistence Boundary.

A Persistent Resource:

* has defined persistence semantics;
* has a logical identity where applicable;
* has a defined lifecycle;
* may be written to durable storage;
* may be reconstructed from durable storage;
* is governed by persistence contracts.

Not every runtime resource is a Persistent Resource.

### Examples

Potential Persistent Resources include:

* business objects;
* document state;
* configuration state;
* register facts;
* other durable domain state.

These examples are conceptual. The final list of persistent resource types is established by the relevant domain architecture.

---

## 5.2 Persistent Entity

A **Persistent Entity** is a logical entity that defines a persistence domain and lifecycle for a class of durable resources.

A Persistent Entity establishes:

* what constitutes one logical persisted resource;
* its identity semantics;
* its lifecycle;
* the operations applicable to it;
* the versioning semantics applicable to it;
* the persistence rules applicable to it.

Persistent Entity is therefore an architectural concept and must not be equated with:

* a database table;
* a database collection;
* an ORM entity;
* a physical record.

One Persistent Entity may be represented using different physical storage structures by different Storage Providers.

---

## 5.3 Persistent Object

A **Persistent Object** is the persistence representation of the durable state of a logical business/domain object.

The Runtime Object and Persistent Object are different representations of the same logical business resource.

Conceptually:

```text
             Logical Business Object
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
      Runtime Object       Persistent Object
            │                     │
            │                     │
      execution state       durable state
```

The Runtime Object exists for execution.

The Persistent Object exists for durability.

A Persistent Object may contain:

* logical identity;
* persistent fields;
* version information;
* lifecycle state;
* references to other logical entities;
* other durable object state.

It must not contain storage-provider-specific implementation details as part of the architectural domain model.

---

## 5.4 Persistent Object Is Not a Physical Record

A Persistent Object must not be defined as a physical storage record.

For example:

```text
Persistent Object
       │
       ▼
Storage Provider
       │
       ▼
Physical Representation
```

The physical representation may differ between Storage Providers.

Therefore:

> A Persistent Object is a logical persistence representation, not a physical database record.

---

# 6. Register Fact

A **Register Fact** is a persisted business fact produced by business processing and accepted by the Register subsystem.

Register Facts are intentionally modeled separately from Persistent Objects.

The distinction is fundamental.

A Persistent Object describes durable **object state**.

A Register Fact describes a durable **business fact/event/movement** recorded by the system.

Conceptually:

```text
Business Operation
       │
       ▼
    Posting
       │
       ▼
  MovementSet
       │
       ▼
Register Validation
       │
       ▼
 Accepted Register Facts
       │
       ▼
   Persistence
```

Persistence does not invent business facts.

Persistence stores accepted facts produced by the appropriate domain/application process.

---

# 7. Persistent Object vs Register Fact

The distinction can be expressed as:

| Concept           | Primary Question                                  |
| ----------------- | ------------------------------------------------- |
| Persistent Object | What is the durable state of this logical object? |
| Register Fact     | What business fact was recorded?                  |

For example, a document may have:

```text
Document Object State
    status = posted
    date = ...
    counterparty = ...
```

while posting the document may produce:

```text
Register Facts
    debit ...
    credit ...
    quantity movement ...
    inventory movement ...
```

The document state and register facts are related but are not the same persistence resource.

This distinction must remain explicit throughout the architecture.

---

# 8. Configuration Persistent State

Configuration requires a specific distinction between persistent configuration state and runtime configuration.

The runtime configuration model established in previous phases includes objects such as:

* `ActiveConfiguration`;
* `RuntimeConfigurationContext`;
* runtime bindings;
* metadata resolution state.

These are runtime representations.

They are not themselves the persistence model.

The Persistence Domain therefore introduces **Configuration Persistent State** as the durable representation from which runtime configuration may be reconstructed.

Conceptually:

```text
Configuration Persistent State
             │
             ▼
      Configuration Load
             │
             ▼
      Candidate / Validation
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

The persistence model must therefore preserve sufficient logical configuration information to reconstruct the required runtime configuration.

The exact physical representation remains outside this model.

---

# 9. Persistence Operation

A **Persistence Operation** is a semantic operation performed against a Persistent Resource.

Persistence operations describe intent, not implementation.

Potential operation categories include:

* Create;
* Read;
* Update;
* Replace;
* Delete;
* Append;
* Exists;
* Query.

Not every Persistent Resource supports every operation.

The allowed operations are defined by the semantics of the corresponding Persistent Entity.

---

## 9.1 Create

`Create` establishes a new persistent resource.

The operation must respect the identity and lifecycle rules of the Persistent Entity.

A Create operation must not silently overwrite an existing logical resource unless that behavior is explicitly defined by the corresponding persistence contract.

---

## 9.2 Read

`Read` retrieves a persistent resource by its logical identity or another explicitly defined lookup criterion.

Read semantics must not expose physical storage identifiers as the architectural identity of the resource.

---

## 9.3 Update

`Update` changes the persistent state of an existing resource.

Update semantics apply where the underlying resource represents mutable state.

An update normally produces a new logical version of the resource state where versioning is part of the entity's semantics.

---

## 9.4 Replace

`Replace` replaces the persistent representation/state of an existing resource according to the contract of the Persistent Entity.

`Replace` and `Update` are conceptually related but are not required to have identical semantics.

A concrete contract may choose one or both operations depending on the resource type.

---

## 9.5 Delete

`Delete` removes or deactivates a persistent resource only where such semantics are explicitly permitted.

Deletion must not be assumed to be universally available.

Some resources may be:

* immutable;
* append-only;
* versioned;
* logically deleted;
* lifecycle-controlled;
* otherwise non-deletable.

In particular, historical Register Facts must not acquire destructive semantics merely because a Storage Provider technically supports deletion.

---

## 9.6 Append

`Append` adds a new persistent fact/resource without replacing existing persisted state.

Append semantics are particularly relevant to:

* Register Facts;
* historical records;
* other append-oriented resources.

`Append` is intentionally distinct from `Update`.

Conceptually:

```text
Update:
    existing state ───────► new state

Append:
    existing facts + new fact
```

The distinction is architectural and must not be erased by a generic storage abstraction.

---

## 9.7 Exists

`Exists` determines whether a logical persistent resource exists according to its identity or lookup semantics.

It does not require loading the resource itself.

---

# 10. Persistence Query

A **Persistence Query** is a logical request for persisted information.

Queries describe the information required by the application/domain layer without exposing the physical query mechanism.

Examples include:

* object lookup;
* object search;
* register movement query;
* register fact query;
* balance query;
* turnover query;
* configuration lookup;
* historical state lookup.

The physical implementation may use:

* indexes;
* SQL;
* document queries;
* key-value lookups;
* files;
* remote services;
* other mechanisms.

Those mechanisms are outside the Persistence Domain Model.

---

# 11. Query Semantics

Persistence Queries must be expressed in terms of logical domain concepts.

For example:

```text
Logical:
    find register facts for account X
    during period Y
```

rather than:

```text
Physical:
    SELECT ...
    FROM ...
    WHERE ...
```

The first belongs to the persistence contract.

The second belongs to a Storage Provider implementation.

---

# 12. Persistence Scope

A **Persistence Scope** defines a logical consistency boundary for a group of persistence operations.

A Persistence Scope exists when several persistence operations must satisfy a common consistency rule.

For example, a posting operation may conceptually require:

```text
Document State
      +
Register Facts
      +
Required Derived State
```

to reach a consistent durable state together.

The exact mechanism used to provide this consistency is deliberately deferred.

A Persistence Scope therefore defines **semantic consistency requirements**, not a concrete transaction implementation.

---

# 13. Persistence Scope and Transactions

Persistence Scope must not currently be equated with:

* database transaction;
* SQL transaction;
* ORM unit of work;
* session;
* connection.

A Storage Provider may implement a Persistence Scope using one or more physical mechanisms.

The architectural contract specifies the required consistency semantics.

The implementation determines how those semantics are achieved.

---

# 14. Identity

Persistence uses **logical identity**.

A logical identity identifies a Persistent Resource independently of its physical storage location.

The architecture already establishes ULID-based identity as a platform identity mechanism.

Therefore physical storage identifiers must not replace logical AcCoreD identities.

Conceptually:

```text
Logical Identity
       │
       ▼
Persistent Resource
       │
       ▼
Storage Provider
       │
       ▼
Physical Storage Identifier
```

The physical identifier, if one exists, is an implementation detail.

---

# 15. Identity vs Version

Identity and version are separate concepts.

### Identity

Answers:

> Which logical resource is this?

### Version

Answers:

> Which state/version of this logical resource is this?

Therefore:

```text
Identity = stable logical resource
Version  = particular state of that resource
```

For mutable Persistent Objects, identity normally remains stable while version may change.

For immutable or append-oriented resources, version semantics may differ or may not apply in the same way.

---

# 16. Version Semantics

Versioning is a persistence concern where required by the lifecycle of the Persistent Entity.

A version may be used to:

* identify a particular persistent state;
* detect conflicting updates;
* preserve historical state;
* coordinate lifecycle transitions;
* support reproducibility of persisted configuration.

The architecture does not currently mandate a specific versioning mechanism.

In particular, the model does not yet require:

* numeric revision counters;
* timestamps as versions;
* database-generated versions;
* optimistic concurrency as the universal strategy.

Those decisions belong to later persistence contract and implementation design.

---

# 17. Lifecycle Semantics

Persistent resources have lifecycle semantics defined by their corresponding Persistent Entity.

Possible lifecycle stages include conceptually:

```text
Created
   │
   ▼
Active
   │
   ├────► Updated / Versioned
   │
   ├────► Deactivated
   │
   └────► Archived / Historical
```

The actual lifecycle is domain-specific.

Persistence must preserve lifecycle state but must not invent business lifecycle rules.

For example:

* a document's posting lifecycle belongs to document/business architecture;
* configuration activation belongs to configuration architecture;
* register fact acceptance belongs to register/posting architecture.

Storage merely persists the resulting state.

---

# 18. Runtime State vs Persistent State

Runtime state and persistent state are explicitly different architectural concepts.

### Runtime State

Runtime state exists while the system is executing.

Examples:

* runtime object instances;
* resolver state;
* runtime configuration context;
* caches;
* temporary calculation state;
* execution context.

### Persistent State

Persistent state exists to survive process termination and allow the system to reconstruct required durable state.

Examples:

* persisted object state;
* configuration persistent state;
* accepted register facts;
* other durable domain state.

Conceptually:

```text
                 Application Execution
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Runtime State        Persistent State
              │                     │
       process lifetime       durable lifetime
```

Persistent State must not be defined as a serialized copy of Runtime State.

---

# 19. Persistence Is Not Serialization

Serialization is a mechanism for representing data.

Persistence is an architectural capability for preserving durable logical state.

Therefore:

```text
Serialization ≠ Persistence
```

A serialization format may be used by a Storage Provider, but the persistence architecture must remain independent of that format.

---

# 20. Persistent Object Reconstruction

A Runtime Object may be reconstructed from Persistent State.

Conceptually:

```text
Persistent Object
       │
       ▼
Persistence Mapping
       │
       ▼
Runtime Object
```

The mapping is part of the persistence architecture/application integration.

The Storage Provider must not become responsible for domain behavior.

Persistence may provide data required to construct or restore runtime objects, but domain/application layers remain responsible for interpreting that data according to domain semantics.

---

# 21. Register Facts and Persistence

Register Facts follow a distinct persistence path.

The architectural flow is:

```text
Business Operation
       │
       ▼
      Posting
       │
       ▼
   MovementSet
       │
       ▼
Register Validation
       │
       ▼
 Accepted Register Facts
       │
       ▼
Persistence Operation
       │
       ▼
     Storage
```

The Storage subsystem does not:

* calculate postings;
* determine debit/credit semantics;
* create movements;
* decide whether a business operation is valid;
* interpret accounting meaning.

Its responsibility is to durably persist accepted state/facts according to the persistence contract.

---

# 22. Derived State

Derived state may be persisted for performance, operational convenience, or other architectural reasons.

Examples may include:

* cached balances;
* indexes;
* materialized totals;
* search projections;
* other derived representations.

However:

> Derived state must not redefine the primary business facts.

The authoritative source must remain the logically defined persistent business state/facts.

If derived state becomes inconsistent, the architecture must retain a conceptual path to reconstruct it from authoritative state.

This principle prevents storage optimization from becoming an accidental replacement for domain truth.

---

# 23. Storage Has No Business Semantics

The Persistence Domain Model explicitly separates storage mechanics from business meaning.

Storage must not decide:

* whether a document is valid;
* whether an operation should be posted;
* which register facts should be produced;
* whether a business transaction is economically correct;
* how accounting rules are interpreted;
* whether a configuration is semantically valid.

Those responsibilities belong to the appropriate domain/application/metadata/runtime layers.

Storage persists the result of those decisions.

---

# 24. Persistence Errors

Persistence operations expose **semantic persistence errors**, not provider-specific exceptions.

The architectural error model may include the following categories:

```text
PersistenceError
├── NotFound
├── AlreadyExists
├── Conflict
├── InvalidState
├── ConstraintViolation
└── StorageFailure
```

These categories are conceptual.

The exact class hierarchy belongs to the Persistence Contracts implementation.

---

## 24.1 NotFound

The requested logical persistent resource does not exist.

---

## 24.2 AlreadyExists

A create operation attempted to establish a logical resource whose identity already exists.

---

## 24.3 Conflict

The requested operation conflicts with the current persistent state.

A conflict may include, for example:

* concurrent modification;
* stale version;
* incompatible state transition.

The exact conflict-detection mechanism remains implementation-independent.

---

## 24.4 InvalidState

The persistence operation is not valid for the current lifecycle/state of the resource.

This represents a persistence contract violation rather than a business-rule evaluation.

---

## 24.5 ConstraintViolation

The operation violates a persistence-level invariant explicitly defined by the persistence contract.

A constraint violation must not be used as a substitute for domain validation.

---

## 24.6 StorageFailure

The Storage Provider could not complete an otherwise valid persistence operation because of an underlying storage/infrastructure failure.

Provider-specific errors must be translated into the semantic persistence error model before crossing the Persistence Boundary.

---

# 25. Provider Error Isolation

Provider-specific exceptions must not leak into higher architectural layers.

Conceptually:

```text
Physical Storage Error
        │
        ▼
Storage Provider
        │
        ▼
Semantic Persistence Error
        │
        ▼
Persistence Contract
        │
        ▼
Application / Domain
```

This preserves Storage Provider substitutability.

A caller should not need to know whether persistence is implemented using one database, another database, files, or a remote service.

---

# 26. Concurrency Semantics

Persistence must be capable of expressing conflicts caused by concurrent changes where the Persistent Entity requires such protection.

The architecture recognizes concurrency as a persistence concern but does not yet select a universal implementation strategy.

Possible mechanisms include:

* version comparison;
* locking;
* compare-and-update;
* provider-specific concurrency controls;
* other mechanisms.

The Persistence Domain Model therefore defines the **semantic requirement**:

> A persistence operation must not silently overwrite a conflicting state when the Persistent Entity requires conflict detection.

The concrete concurrency strategy belongs to a later design stage.

---

# 27. Persistence Domain Model

The complete conceptual model is:

```text
                         Persistence Domain
                                │
                ┌───────────────┼────────────────┐
                │               │                │
                ▼               ▼                ▼
       Persistent Resource   Persistence     Persistence
                              Operation         Query
                │               │                │
        ┌───────┴───────┐       │                │
        │               │       │                │
        ▼               ▼       ▼                ▼
 Persistent Object  Register Fact       Query Semantics
        │               │
        │               │
        └───────┬───────┘
                │
                ▼
       Persistence Scope
                │
                ▼
       Persistence Boundary
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

Configuration Persistent State is a specialized Persistent Resource:

```text
Configuration Persistent State
              │
              ▼
       Configuration Loading
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

---

# 28. Architectural Decisions

The following decisions define the Phase 5 Persistence Domain Model.

## P5-DM1 — Persistent Resource

A Persistent Resource is a logical resource whose state has persistence semantics.

---

## P5-DM2 — Persistent Object

A Persistent Object is the logical persistence representation of durable state belonging to a business/domain object.

It is not a physical storage record.

---

## P5-DM3 — Persistent Entity

A Persistent Entity defines the persistence domain and lifecycle of a class of Persistent Resources.

It is not equivalent to a database table, collection, or ORM entity.

---

## P5-DM4 — Register Fact

Register Fact is a persistence concept distinct from Persistent Object.

Register Facts represent accepted business facts produced by Posting/Register processing.

---

## P5-DM5 — Semantic Persistence Operations

Persistence operations describe logical intent and must not expose physical storage operations as the architectural contract.

---

## P5-DM6 — Append vs Update

Append and Update/Replace represent distinct persistence semantics.

Append must not be reduced to a generic Update operation.

---

## P5-DM7 — Logical Persistence Queries

Persistence Queries are expressed in logical/domain terms and hide the physical query mechanism.

---

## P5-DM8 — Persistence Scope

Persistence Scope defines a logical consistency boundary.

It is not currently defined as a specific transaction, session, or Unit of Work implementation.

---

## P5-DM9 — Identity and Version

Logical identity and version are separate concepts.

Identity identifies a logical resource; version identifies a particular state/version where versioning applies.

---

## P5-DM10 — Provider Error Isolation

Storage-provider-specific exceptions must not cross the Persistence Boundary.

---

# 29. Architectural Invariants

The following invariants apply to Phase 5.

### P5-I1 — Physical Storage Independence

The Persistence Domain Model must not depend on a specific physical storage technology.

---

### P5-I2 — Storage Has No Business Semantics

Storage must not define or interpret business rules.

---

### P5-I3 — Runtime Is Not the Persistence Model

Runtime objects and runtime state must not automatically become the persistence model.

---

### P5-I4 — Persistent Identity Is Logical

Logical AcCoreD identity must remain independent of physical storage identifiers.

---

### P5-I5 — Persistence Contracts Are Semantic

Persistence contracts must express logical persistence semantics rather than provider-specific mechanics.

---

### P5-I6 — Register Facts Are Produced Outside Storage

Storage does not produce business movements or register facts.

---

### P5-I7 — Derived State Is Not Primary Business Fact

Derived/materialized state must not redefine authoritative business state or facts.

---

### P5-I8 — Physical Schema Is Deferred

No physical schema is fixed by the Persistence Domain Model.

---

### P5-I9 — Provider Substitutability

A Persistence Contract must be implementable by different Storage Providers without changing the higher-level architectural semantics.

---

### P5-I10 — Logical Fields Remain Storage Independent

Logical fields and their semantics must not be defined by the physical storage representation.

---

### P5-I11 — Persistent Resource Semantics Are Explicit

A resource must not become persistent merely because it happens to be represented in memory.

Its persistence semantics must be explicitly defined.

---

### P5-I12 — Persistence Does Not Create Domain Truth

Persistence stores accepted domain/application state and facts; it does not determine what constitutes valid business state or truth.

---

# 30. Explicit Non-Decisions

The following decisions are intentionally deferred.

## 30.1 Database Technology

No decision has been made regarding:

* PostgreSQL;
* SQLite;
* another relational database;
* document database;
* key-value storage;
* file-based storage;
* distributed storage;
* other technologies.

---

## 30.2 Physical Schema

No decisions have been made regarding:

* tables;
* columns;
* collections;
* document structures;
* indexes;
* foreign keys;
* partitions;
* physical identifiers.

---

## 30.3 ORM

No ORM has been selected.

The architecture does not require an ORM.

---

## 30.4 Serialization Format

No persistence serialization format is defined.

Examples such as JSON, MessagePack, binary formats, or database-native representations remain implementation concerns.

---

## 30.5 Transaction Mechanism

No concrete transaction mechanism has been selected.

Persistence Scope defines semantic consistency requirements only.

---

## 30.6 Concurrency Strategy

No universal concurrency mechanism has been selected.

The architecture defines conflict semantics; implementation strategy is deferred.

---

## 30.7 Caching

No persistence cache architecture is defined here.

Caching may be introduced later without changing the logical persistence model.

---

## 30.8 Replication

No replication or distributed-storage semantics are defined here.

---

# 31. Relationship to Previous Phases

Phase 5 depends on architectural boundaries established by earlier phases.

In particular:

```text
Configuration
     │
     ▼
Metadata
     │
     ▼
Runtime Configuration
     │
     ▼
Runtime Objects
     │
     ▼
Domain/Application Processing
     │
     ▼
Posting / Register
     │
     ▼
Persistence
     │
     ▼
Storage
```

Persistence therefore consumes the results of higher-level processing.

It does not replace:

* Metadata;
* Runtime;
* Configuration;
* Object behavior;
* Posting;
* Register semantics.

---

# 32. Relationship to ADR-P5-001

`ADR-P5-001` establishes the architectural Storage & Persistence Boundary.

This document refines that boundary into a logical Persistence Domain Model.

The relationship is:

```text
ADR-P5-001
    │
    │ establishes boundary
    ▼
Persistence Domain Model
    │
    │ defines logical concepts
    ▼
Persistence Contracts
    │
    │ defines executable interfaces
    ▼
Storage Provider
    │
    │ implements contracts
    ▼
Physical Storage
```

The Persistence Domain Model must remain consistent with `ADR-P5-001`.

If a future design requires changing the fundamental boundary established by `ADR-P5-001`, the ADR must be revisited rather than silently overridden by implementation details.

---

# 33. Relationship to Storage

The Persistence Domain Model defines the semantic requirements that Storage must satisfy.

Storage is responsible for implementing those requirements.

The separation is:

| Persistence Domain    | Storage                           |
| --------------------- | --------------------------------- |
| Persistent Resource   | Physical representation           |
| Persistent Object     | Serialization/mapping             |
| Register Fact         | Physical storage                  |
| Persistence Operation | Provider implementation           |
| Persistence Query     | Physical query mechanism          |
| Persistence Scope     | Transaction/consistency mechanism |
| Logical Identity      | Physical key mapping              |
| Semantic Error        | Provider error translation        |

The right-hand column is implementation territory.

---

# 34. Relationship to Domain Logic

Persistence must remain below the domain/application semantic boundary.

For example:

```text
Domain:
    "This document should produce these movements."

Posting:
    MovementSet

Register:
    Accepted Register Facts

Persistence:
    Persist accepted state/facts

Storage:
    Store physical representation
```

The Persistence subsystem must not move upward in this chain and begin making domain decisions.

---

# 35. Design Rule: Persistence Should Be Boring

A useful architectural test for the Storage/Persistence subsystem is:

> **Persistence should be boring.**

It should reliably:

* accept valid persistence operations;
* preserve durable state;
* retrieve durable state;
* maintain required consistency;
* report semantic persistence errors;
* remain independent of physical technology.

It should not contain hidden business logic.

If business meaning starts appearing inside a Storage Provider, the architectural boundary should be reviewed.

---

# 36. Design Rule: Logical First, Physical Later

All persistence design should proceed in the following order:

```text
Logical Domain Semantics
          │
          ▼
Persistence Domain Model
          │
          ▼
Persistence Contracts
          │
          ▼
Provider Mapping
          │
          ▼
Physical Storage
```

The reverse direction must not drive the architecture.

In particular, a limitation or convenience of a selected database must not redefine the logical persistence model unless that decision is explicitly accepted as an architectural change.

---

# 37. Step 2 Completion Criteria

Step 2 is considered architecturally complete when:

* Persistent Resource is defined;
* Persistent Entity is defined;
* Persistent Object is defined;
* Register Fact is explicitly separated from Persistent Object;
* Configuration Persistent State is defined;
* Persistence Operations are defined semantically;
* Append semantics are separated from Update semantics;
* Persistence Query is defined;
* Persistence Scope is defined;
* Identity and Version semantics are separated;
* runtime state is explicitly separated from persistent state;
* persistence error semantics are defined;
* concurrency requirements are identified without prematurely fixing an implementation;
* physical storage remains deferred;
* Storage Provider remains replaceable;
* the model is consistent with `ADR-P5-001`.

---

# 38. Next Step

The next architectural step is:

> **Step 3 — Persistence Contracts**

Step 3 will translate the logical Persistence Domain Model into explicit application-facing contracts.

Step 3 should determine:

* which persistence concepts require interfaces/protocols;
* which operations are represented by contracts;
* how Persistent Resources are addressed;
* how queries are expressed;
* how Persistence Scope is represented;
* how persistence errors cross the boundary;
* how Storage Providers implement the contracts;
* which contracts belong to the platform and which belong to domain modules.

Step 3 must continue to preserve the architectural rule:

```text
Application / Domain
        │
        ▼
Persistence Contracts
        │
        ▼
Storage Provider
        │
        ▼
Physical Storage
```

No concrete database or physical schema should be introduced merely as part of defining the contracts.

---

# 39. Final Architectural Statement

Phase 5 defines persistence as a **logical architectural capability for durable state**, not as a database abstraction.

The Persistence Domain Model establishes:

```text
Logical State
     │
     ▼
Persistent Resource
     │
     ├──────────────► Persistent Object
     │
     ├──────────────► Register Fact
     │
     └──────────────► Configuration Persistent State
     │
     ▼
Persistence Contracts
     │
     ▼
Storage Provider
     │
     ▼
Physical Storage
```

The essential architectural boundary is:

> **AcCoreD defines what must be persisted and what persistence means. Storage defines how that state is physically stored.**

This separation preserves the independence of the runtime/domain architecture from storage technology and provides the foundation for the Persistence Contracts defined in Step 3.
