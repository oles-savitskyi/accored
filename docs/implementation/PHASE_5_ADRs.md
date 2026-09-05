# ADR-P5-01 — Establish Storage and Persistence Boundary

**Status:** Accepted
**Date:** 2026-09-02
**Phase:** Phase 5 — Storage & Persistence Boundary

---

## 1. Context

AcCore is a metadata-driven platform in which logical business structures are defined by Metadata and executed by Runtime.

Runtime Objects are executable representations of Domain Objects and maintain runtime state during execution.

At the same time, AcCore must preserve durable business state including Persistent Entities, Persistent Objects, Register Records, configuration state, constants, sequences, and other explicitly persistent information.

Without an explicit architectural boundary, persistence implementation can gradually leak into Runtime and domain architecture.

Such leakage may result in:

* Runtime depending directly on database structures;
* Metadata containing physical storage details;
* business logic depending on SQL or ORM behavior;
* physical identifiers becoming business identities;
* Register or Posting logic becoming coupled to storage;
* storage optimizations becoming visible as business semantics;
* inability to replace the physical storage technology without architectural changes.

The existing AcCore architecture already establishes that Logical Fields are independent of physical storage, Storage Providers are concrete implementations, and Storage is responsible for physical persistence rather than business logic.

Phase 5 formalizes these principles as an explicit Persistence Boundary.

---

## 2. Decision

AcCore establishes a dedicated **Storage and Persistence Boundary** between logical platform state and physical storage.

The architecture is:

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

The following decisions are binding.

### 2.1 Physical Storage Is an Implementation Detail

The AcCore architecture does not depend on a specific database, storage engine, file format, or physical schema.

A Storage Provider may use any suitable physical mechanism provided that it preserves the logical behavior required by the platform.

---

### 2.2 Storage Is a Platform Boundary

Storage is the architectural subsystem responsible for implementing persistence.

Consumers interact with persistence through logical contracts.

They must not depend directly on:

* SQL;
* database-specific APIs;
* ORM models;
* physical tables;
* physical columns;
* storage-specific identifiers;
* provider-specific query syntax.

---

### 2.3 Runtime State Is Not the Persistence Model

Runtime Objects and runtime execution state are distinct from Persistent Objects and persistent state.

Runtime representations may be constructed from persistent state and may be discarded or recreated.

The physical representation of persistent state is determined by Storage.

---

### 2.4 Logical Identity Is Independent of Physical Identity

AcCore Object Identity remains the identity of a business object.

Physical storage identifiers, such as database-generated identifiers or document-store keys, are implementation details.

They must not replace or redefine Object Identity.

---

### 2.5 Persistence Contracts Are Semantic

Persistence contracts describe logical persistence behavior.

They must express concepts such as:

* object persistence;
* object retrieval;
* register fact persistence;
* register fact retrieval;
* configuration persistence;
* query;
* consistency;
* transaction requirements.

They must not encode physical schema details.

---

### 2.6 Storage Does Not Contain Business Logic

Storage persists state.

It does not define:

* accounting rules;
* posting rules;
* valuation rules;
* workflow semantics;
* object business behavior;
* register business meaning.

Business semantics remain owned by the corresponding platform subsystems.

---

### 2.7 Posting Produces Facts; Storage Persists Facts

Posting remains responsible for generating business movements.

Register architecture determines whether generated movements satisfy the Register Posting Contract.

Storage persists accepted register facts.

Therefore:

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
Persistence
```

Storage does not generate movements and does not perform posting logic.

---

### 2.8 Derived State Does Not Redefine Primary Facts

Register movements remain the authoritative historical facts.

Balances, turnovers, totals, indexes, caches, and other derived structures may be materialized or optimized.

Such derived structures must preserve the same logical behavior as the underlying facts.

---

### 2.9 Physical Schema Is Deferred

No physical database schema is established by this ADR.

The following remain implementation decisions:

* tables;
* collections;
* EAV structures;
* indexes;
* partitions;
* serialization;
* physical totals structures;
* provider-specific optimizations.

---

## 3. Rationale

This decision preserves the architectural properties required by AcCore.

### Metadata-driven architecture

Metadata remains a logical model rather than a description of a particular database.

### Runtime independence

Runtime can execute against different persistence implementations without changing its business semantics.

### Provider substitutability

Different Storage Providers can support different deployment models while implementing the same logical contract.

### Long-term evolution

The platform can evolve its physical storage architecture without forcing changes into Metadata, Runtime, Posting, Register, or business configurations.

### Separation of responsibilities

Each subsystem retains a clearly defined responsibility:

```text
Metadata  → defines
Runtime   → executes
Posting   → produces
Register  → accepts and organizes facts
Storage   → persists
Provider  → implements physical storage
```

---

## 4. Consequences

### Positive

* Physical storage technology remains replaceable.
* Runtime remains independent from persistence implementation.
* Business logic cannot accidentally migrate into Storage.
* Object Identity remains stable across storage implementations.
* Register persistence has a clear architectural boundary.
* Future Storage Providers can be introduced without redesigning Runtime.
* Physical optimization can evolve independently from logical semantics.

### Negative

* Persistence requires explicit contracts rather than direct database access.
* Additional mapping between logical and physical representations is required.
* Some implementation decisions must be deferred until persistence contracts are sufficiently defined.
* Storage implementation may be more complex than a direct ORM-based design.

These costs are accepted because architectural independence is a core requirement of AcCore.

---

## 5. Rejected Alternatives

### 5.1 Runtime Directly Uses Database APIs

Rejected.

This would couple Runtime to a physical persistence technology and violate the Storage Boundary.

---

### 5.2 Metadata Defines Physical Schema

Rejected.

Metadata defines logical business structures.

Physical realization belongs to Storage.

---

### 5.3 Universal CRUD Repository as the Primary Architectural Abstraction

Rejected at this stage.

Different persistent structures have different semantics.

For example:

```text
Object persistence
Register fact persistence
Configuration persistence
```

cannot safely be reduced to identical CRUD semantics without losing architectural meaning.

A suitable persistence contract model will be defined in a later Phase 5 step.

---

### 5.4 Storage Generates Register Movements

Rejected.

Posting produces movements.

Storage only persists accepted facts.

---

### 5.5 Physical Database Identity Becomes Object Identity

Rejected.

AcCore Object Identity must remain independent of physical storage identifiers.

---

## 6. Architectural Invariants

This ADR establishes:

**P5-I1 — Physical Storage Independence**

The logical platform is independent of physical storage technology.

**P5-I2 — Storage Has No Business Semantics**

Storage does not define business meaning.

**P5-I3 — Runtime Is Not the Persistence Model**

Runtime state and persistent state are separate architectural concepts.

**P5-I4 — Persistent Identity Is Logical**

Physical identifiers do not replace Object Identity.

**P5-I5 — Persistence Contracts Are Semantic**

Persistence contracts describe logical requirements rather than physical implementation.

**P5-I6 — Register Facts Are Produced Outside Storage**

Posting/Register architecture determines facts; Storage persists them.

**P5-I7 — Derived State Is Not Primary Business Fact**

Derived structures may optimize access but cannot redefine primary facts.

**P5-I8 — Physical Schema Is Deferred**

No physical schema is fixed by this ADR.

**P5-I9 — Provider Substitutability**

Storage Providers must preserve logical platform behavior.

**P5-I10 — Logical Fields Remain Storage Independent**

Logical Fields remain independent of their physical persistence representation.

---

## 7. Relationship to Existing Architecture

This ADR reinforces existing AcCore architectural principles:

* Metadata-driven Architecture;
* Runtime/Metadata Separation;
* Hybrid Storage Model;
* ULID Identity Model;
* Posting Produces Register Facts;
* Register Query abstraction;
* Logical Field Model;
* Storage Provider independence;
* Totals as derived register state.

The ADR does not redefine those principles.

It establishes the Persistence Boundary through which they interact with physical storage.

---

## 8. Scope of This ADR

This ADR establishes the boundary only.

It does not define the detailed persistence contracts.

The following remain subsequent architectural work:

```text
Phase 5
   │
   ├── Step 1 — Storage & Persistence Boundary
   │       └── this ADR
   │
   ├── Step 2 — Persistence Domain Model
   │
   ├── Step 3 — Persistence Contracts
   │
   ├── Step 4 — Storage Provider Boundary
   ├── Step 5 — Transaction / Consistency Model
   │
   └── later — Physical Storage Implementation
```

---

## 9. Decision Outcome

**Accepted.**

AcCore formally separates logical persistence semantics from physical storage implementation.

The Storage subsystem is the sole architectural boundary responsible for translating persistence requirements into physical storage operations.

No concrete storage technology is selected by this ADR.
