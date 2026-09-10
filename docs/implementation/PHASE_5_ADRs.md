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

# ADR-P5-02 — Transaction and Consistency Model

**Status:** Accepted
**Date:** 2026-09-10
**Phase:** Phase 5 — Storage & Persistence Boundary

## Context

Phase 5 establishes the Storage and Persistence Boundary for AcCoreD.

Previous decisions define:

* physical storage as an implementation detail;
* Storage as a platform boundary;
* persistence contracts as semantic contracts;
* logical persistence identity independently from physical storage identity;
* Persistence Scope as a logical consistency boundary;
* Storage Provider as an opaque-data storage mechanism;
* Posting as the producer of accounting facts;
* persistence as responsible for durable storage of those facts.

The existing persistence contracts intentionally do not expose a physical transaction API.

In particular, the architecture does not currently define:

* `begin()`;
* `commit()`;
* `rollback()`;
* database transactions;
* database sessions;
* ORM units of work;
* provider-specific transaction objects;
* universal locking primitives;
* universal isolation levels.

At the same time, some business operations require several persistent changes to become durable as one logical result.

For example, a successful posting operation may require persistent changes corresponding to:

```text
Posted Object State
        +
Register Movements
        +
Required Derived State
```

Publishing only part of this result would leave the persistent state inconsistent with the logical result of the operation.

Therefore Phase 5 requires an explicit architectural definition of transaction and consistency semantics without prematurely selecting a physical transaction mechanism.

---

## Problem

The architecture must define what it means for a group of persistence operations to succeed or fail together.

Without such a definition, different persistence providers could expose different behavior:

* one provider could commit individual operations independently;
* another could use a database transaction;
* another could use journaling or atomic replacement;
* another could use a provider-specific unit-of-work mechanism.

The higher layers must nevertheless observe the same logical persistence semantics.

The architecture therefore needs to answer:

1. What is the logical unit of consistency?
2. When is atomicity required?
3. What does successful completion mean?
4. What happens when persistence fails?
5. What consistency guarantees are required?
6. How is concurrent modification represented?
7. Which isolation guarantees belong to the architecture?
8. Which mechanisms remain provider-specific?

---

## Decision

### 1. Persistence Scope Is the Logical Consistency Boundary

AcCoreD defines **Persistence Scope** as a logical boundary within which related persistence operations are evaluated against a common consistency requirement.

A Persistence Scope expresses:

> These persistent changes together form one logically consistent persistence result.

A Persistence Scope may contain multiple persistence operations.

For example:

```text
Persistence Scope
    ├── persist posted object state
    ├── append register movements
    └── persist required derived state
```

The scope is a semantic architectural concept.

It is not equivalent to:

* a database transaction;
* a database session;
* an ORM unit of work;
* a filesystem transaction;
* a runtime transaction object.

A provider may implement a Persistence Scope using:

* a database transaction;
* a journal;
* an atomic write protocol;
* a provider-specific unit-of-work mechanism;
* another mechanism capable of satisfying the required semantics.

The architecture does not select between these mechanisms.

---

### 2. Atomicity Is a Contract Requirement, Not an Automatic Property of Every Scope

Not every Persistence Scope necessarily requires the same consistency guarantees.

A persistence contract must determine whether the related operations require **atomic consistency**.

Where atomicity is required, the operations belonging to that scope form one logical persistence result.

For example:

```text
Posting Operation
        │
        ▼
Atomic Persistence Scope
        ├── Posted Object State
        ├── Register Movements
        └── Required Derived State
```

If the scope is defined as atomic, successful completion means that the required persistent changes have been established together as one logical result.

The architecture must not permit a successful atomic operation to expose a state such as:

```text
Object = POSTED
Movements = absent
```

when the relevant posting contract requires the object state and its movements to be persisted together.

Conversely, the existence of a Persistence Scope by itself does not imply universal database-style atomicity.

Therefore:

> **Atomicity is an explicitly required semantic property of a Persistence Scope, determined by the relevant persistence contract.**

---

### 3. Persistence Scope Is Not a Runtime Transaction Object

Persistence Scope is a semantic architectural boundary.

It must not be interpreted as requiring a universal runtime object with an API such as:

```text
scope.begin()
scope.commit()
scope.rollback()
```

The architecture distinguishes between:

```text
Persistence Scope
    = semantic consistency requirement
```

and:

```text
Scope Execution
    = concrete execution of that requirement
```

A particular implementation may internally create objects representing an active scope.

Such objects are implementation mechanisms and do not become part of the universal persistence contract unless explicitly introduced by a future architecture decision.

This distinction prevents Persistence Scope from becoming a renamed universal `UnitOfWork`.

---

### 4. Persistence Consistency Is Distinct from Business Consistency

Persistence consistency and business consistency are separate architectural concerns.

#### Business consistency

Business consistency is defined by the appropriate domain-level components.

Examples include:

* debit equals credit;
* a posting satisfies its posting contract;
* register movements satisfy register validation rules;
* stock cannot become negative where the relevant business rule prohibits it;
* a document may transition to `POSTED` only when posting succeeds.

These rules belong to the business, Posting, Register, Workflow, or other appropriate domain/application layers.

#### Persistence consistency

Persistence consistency defines whether the required durable state corresponding to an operation is stored as one coherent logical result.

For example:

```text
Business operation:
    Post document

Business result:
    Document is POSTED
    Register Movements exist
    Required derived state is updated

Persistence requirement:
    Required related changes satisfy
    the consistency boundary of the operation
```

Storage must preserve the persistence requirement.

Storage must not invent or implement the business rules themselves.

Therefore:

> Persistence consistency guarantees durability and consistency of required persistent state; it does not replace domain validation.

---

### 5. Failed Atomic Scope Must Not Be Published as Successful Partial State

When a Persistence Scope declares atomic consistency, failure before successful completion must not result in a partially committed logical result being reported as successful.

Conceptually:

```text
Atomic Scope
      │
      ├── success
      │      └── Completed
      │
      └── failure
             └── Failed / Aborted
```

The architecture therefore requires:

> A failed atomic Persistence Scope must not be published as a successfully completed logical operation with only a partial required result.

This does not require a specific rollback mechanism.

A provider may use:

* transaction rollback;
* journaling;
* temporary state followed by atomic publication;
* compensating mechanisms;
* another provider-specific strategy.

The required property is semantic, not technological.

For scopes that do not require atomic consistency, their failure semantics must be defined by the relevant persistence contract.

---

### 6. Completion Is a Semantic State, Not a Mandatory `commit()` API

The architecture defines **completion** semantically.

Completion means:

> The Persistence Scope has successfully established the required durable logical state according to its persistence contract.

This does not imply that AcCoreD exposes:

```text
commit()
rollback()
```

as universal persistence operations.

A provider may internally use a commit operation.

Another provider may finalize an append-only journal.

Another provider may use atomic filesystem replacement.

These are implementation mechanisms.

The public architecture is concerned with the semantic result:

```text
Scope → Completed
```

rather than the physical mechanism used to reach that state.

---

### 7. Rollback Is Not a Universal Architectural Primitive

AcCoreD does not define rollback as a mandatory universal persistence operation.

The architecture requires semantic failure handling, but deliberately does not prescribe how a provider achieves it.

A provider may achieve failed-scope semantics through:

* transaction rollback;
* write-ahead journaling;
* temporary state followed by atomic publication;
* compensating mechanisms;
* another provider-specific strategy.

Therefore:

> Transaction rollback is a possible implementation technique, not the architectural definition of failure semantics.

A provider must not claim atomic Persistence Scope semantics unless its implementation can actually satisfy them.

---

### 8. Concurrency Semantics Must Be Explicit

Concurrent modification is a persistence concern whenever correctness depends on persistent state not being modified concurrently in an incompatible way.

AcCoreD therefore does not assume that all persistent entities are freely mutable without conflict detection.

Where concurrency matters, the relevant persistence contract must explicitly define the required semantics.

Possible mechanisms include:

* version checks;
* revision numbers;
* compare-and-swap;
* optimistic concurrency;
* provider-specific locking;
* other mechanisms.

These mechanisms are not introduced as universal AcCoreD APIs by this ADR.

The architectural requirement is:

> A persistence operation must not silently overwrite concurrent changes when the relevant persistence contract requires conflict detection.

In particular:

```text
No concurrency contract
        ≠
last-write-wins
        ≠
optimistic concurrency
        ≠
safe concurrent update
```

The absence of an explicitly defined concurrency guarantee must not be interpreted as a guarantee of safe concurrent modification.

Concurrency semantics therefore belong to the contract of the affected persistence operation or Persistent Entity, rather than being inferred from provider behavior.

---

### 9. No Universal Database Isolation Levels

AcCoreD does not adopt database isolation levels such as:

```text
READ UNCOMMITTED
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

as universal platform-level persistence abstractions.

These concepts are tied too closely to particular transaction implementations and do not provide a stable abstraction across all possible persistence providers.

Instead, the architecture defines only the semantic guarantee required by a Persistence Scope.

Operations participating in the same Persistence Scope must observe the logical state required by their persistence contract.

This statement does not imply:

* snapshot isolation;
* repeatable reads;
* serializable execution;
* any particular database isolation level.

Stronger guarantees may be introduced when a particular persistence contract requires them.

Such guarantees must be expressed semantically rather than by exposing database-specific isolation terminology to higher layers.

---

### 10. Storage Provider Remains Below the Transaction / Consistency Boundary

The Storage Provider Contract remains intentionally minimal.

The provider operates on opaque persistent data:

```text
StorageKey + bytes
```

and is responsible for physical storage and retrieval.

The provider contract does not automatically gain:

```text
begin()
commit()
rollback()
transaction()
lock()
```

as a result of this ADR.

A provider may internally expose or use such mechanisms.

However, those mechanisms remain below the architectural persistence boundary.

If the architecture later requires provider-level transactional capabilities to be exposed explicitly, that capability must be introduced as a separate contract decision.

It must not be inferred from the existence of Persistence Scope.

---

### 11. Persistence Scope May Span Multiple Persistence Resources

A Persistence Scope is not limited to a single persistent resource.

A single logical operation may require coordinated persistence of:

* a Persistent Object;
* register facts;
* derived state;
* configuration state;
* other persistence resources required by the operation.

For example:

```text
Posting Operation
        │
        ▼
Persistence Scope
        │
        ├── Posted Object
        ├── MovementSet
        └── Required Register State
```

The scope exists because the logical operation requires these changes to satisfy a common consistency boundary.

The architecture does not require all resources to share the same physical storage.

A future provider architecture may therefore need to coordinate several physical resources while preserving the same logical persistence contract.

Distributed transactions are outside the current Phase 5 scope.

---

### 12. Relationship with Posting

Posting is one of the primary consumers of Persistence Scope semantics.

The Posting Engine coordinates the posting lifecycle and produces the required accounting effects.

The Posting Handler:

* generates the `MovementSet`;
* does not perform persistence;
* does not manage transactions;
* does not implement rollback.

The Posting Engine or appropriate application/service layer coordinates the persistence of the resulting state.

Conceptually:

```text
Posting Handler
      │
      ▼
MovementSet
      │
      ▼
Posting Engine
      │
      ├── validate object state
      ├── validate movements
      └── establish persistence requirements
                │
                ▼
        Persistence Scope
                │
                ├── persist object state
                ├── persist movements
                └── persist required derived state
```

This preserves the architectural separation:

```text
Posting → produces accounting facts
Register → validates and organizes facts
Persistence → establishes durable state
Storage → physically stores data
```

Persistence Scope does not move transaction management into Posting Handlers.

---

### 13. Derived State Must Follow the Applicable Consistency Requirements

Derived state does not redefine primary accounting facts.

Where derived state is required to be persisted as part of a logical operation, it must satisfy the consistency requirements applicable to that operation.

For example:

```text
Primary Facts
    ↓
Register State
    ↓
Derived / Aggregated State
```

If the relevant persistence contract requires the derived state to correspond to newly persisted facts at successful completion, the Persistence Scope must establish that relationship according to the declared consistency semantics.

The architecture does not require every derived value to be persisted.

The requirement is determined by the relevant persistence contract.

---

## Architectural Invariants

### P5-TC1 — Scope Atomicity

Where a Persistence Scope declares atomic consistency, its required operations form one logical consistency unit.

### P5-TC2 — No Partial Published State

A failed atomic Persistence Scope must not be reported as a successfully completed logical operation with only a partial required result.

### P5-TC3 — Logical Scope

Persistence Scope describes logical consistency requirements, not physical transaction technology.

### P5-TC4 — Scope Is Not a Universal Transaction Object

Persistence Scope does not imply a mandatory runtime object with `begin`, `commit`, or `rollback` operations.

### P5-TC5 — Business Semantics Above Persistence

Persistence consistency does not replace business-rule validation.

### P5-TC6 — Provider Independence

The same logical consistency contract must be implementable by different storage providers.

### P5-TC7 — Provider Mechanism Is Hidden

Transactions, journals, locks, sessions, rollback mechanisms, and other physical mechanisms remain provider implementation details unless explicitly introduced by a separate architecture decision.

### P5-TC8 — Explicit Failure

Failure of a Persistence Scope is observable and cannot be silently represented as successful completion.

### P5-TC9 — Explicit Concurrency Semantics

Where concurrent modification affects correctness, the relevant persistence contract must explicitly define the required conflict semantics.

### P5-TC10 — No Implicit Last-Write-Wins

Absence of a concurrency contract must not be interpreted as permission to silently overwrite concurrent changes.

### P5-TC11 — No Universal Isolation Level

Database-specific isolation levels are not part of the universal AcCoreD persistence abstraction.

### P5-TC12 — Durable Completion

Completion of a Persistence Scope means that the required logical persistent state satisfies the durability and consistency guarantees defined by the relevant persistence contract.

### P5-TC13 — Posting Does Not Own Persistence Mechanics

Posting logic produces and validates accounting effects but does not own physical transaction management.

### P5-TC14 — Storage Provider Does Not Define Business Atomicity

The existence of atomic provider operations does not automatically establish atomicity for a higher-level business operation.

### P5-TC15 — Scope May Span Resources

A logical Persistence Scope may encompass multiple persistent resources when required by the operation's consistency contract.

### P5-TC16 — Atomicity Must Be Explicit

A Persistence Scope must not be assumed to provide atomicity unless the relevant persistence contract explicitly requires and defines it.

---

## Rejected Alternatives

### Alternative 1 — Expose `begin() / commit() / rollback()` as the Universal Persistence API

Rejected.

This would make the persistence abstraction resemble a database transaction API and would prematurely constrain providers.

It would also expose implementation mechanics rather than semantic requirements.

---

### Alternative 2 — Make Every `put()` / `delete()` Atomic and Treat That as Sufficient

Rejected.

Single-operation atomicity does not guarantee atomicity across multiple related persistence changes.

A posting operation may require several changes to become logically consistent together.

---

### Alternative 3 — Introduce a Universal Unit of Work

Rejected.

A generic Unit of Work abstraction would prematurely introduce lifecycle and transaction semantics that are not required by all persistence providers.

Persistence Scope provides the required semantic boundary without prescribing a specific implementation pattern.

---

### Alternative 4 — Adopt Database Isolation Levels as the Platform Contract

Rejected.

Database isolation terminology is too implementation-specific for the platform-level abstraction.

The architecture requires semantic consistency guarantees rather than a universal mapping to database isolation modes.

---

### Alternative 5 — Put Transaction Management into Posting Handlers

Rejected.

Posting Handlers are responsible for generating accounting facts.

Transaction and persistence coordination belong outside individual business handlers.

This preserves:

```text
Handler → produces facts
Posting Engine → coordinates posting
Persistence → establishes durable state
Storage → implements physical storage
```

---

### Alternative 6 — Let the Storage Provider Define Business Atomicity

Rejected.

The Storage Provider knows about physical storage, not the semantic relationship between domain objects, register movements, and derived state.

Business/application layers must define which operations belong to a logical Persistence Scope.

---

### Alternative 7 — Treat Missing Concurrency Semantics as Last-Write-Wins

Rejected.

Silent overwrite behavior is itself a concurrency policy.

It must not become an accidental consequence of a particular provider implementation.

Where concurrency matters, the relevant contract must explicitly define the allowed behavior.

---

### Alternative 8 — Require Distributed Transactions

Rejected for Phase 5.

Distributed transaction coordination is outside the current architectural scope.

The current decision establishes logical consistency semantics without committing AcCoreD to a distributed transaction model.

---

## Consequences

### Positive

* Transaction semantics become explicit without coupling AcCoreD to a database.
* Persistence Scope becomes the stable abstraction for multi-operation consistency.
* Atomicity is applied where the relevant persistence contract actually requires it.
* Persistence Scope does not become a disguised universal Unit of Work.
* Posting can coordinate durable state without owning storage mechanics.
* Different storage providers can use different implementation strategies.
* Partial successful states become architecturally prohibited where atomicity is required.
* Concurrency requirements can be introduced explicitly where needed.
* Database-specific transaction and isolation concepts remain outside the core abstraction.
* Future transactional provider capabilities can be introduced without redefining the entire persistence model.

### Costs

* The semantic contract is more abstract than a conventional database transaction API.
* Individual persistence contracts must explicitly state when atomicity or concurrency guarantees are required.
* Provider implementations carry responsibility for realizing the required semantic guarantees.
* Some implementation details must remain deferred until concrete persistence providers are designed.
* Testing must verify logical consistency semantics rather than only individual storage operations.

---

## Resulting Architectural Model

Phase 5 therefore adopts the following conceptual relationship:

```text
                    Business Operation
                           │
                           ▼
                ┌─────────────────────┐
                │ Persistence Scope   │
                │                     │
                │ logical consistency │
                │ boundary            │
                └──────────┬──────────┘
                           │
                 Persistence Contract
                           │
                           ▼
                ┌─────────────────────┐
                │ Storage Boundary    │
                └──────────┬──────────┘
                           │
                           ▼
                Provider-specific
                implementation
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           DB tx        Journal       Atomic FS
```

The essential distinction is:

```text
Persistence Scope
        ≠
Database Transaction
```

Instead:

```text
Persistence Scope
        =
Logical consistency boundary
```

where the actual atomicity, durability, concurrency, and failure guarantees are determined by the applicable persistence contract.

A database transaction, journal, atomic replacement protocol, or another mechanism may be used to implement those guarantees.

The mechanism remains an implementation detail unless a future architecture decision explicitly promotes a provider capability into the platform contract.

---

## Relationship to Phase 5 Architecture

This ADR extends `ADR-P5-01 — Establish Storage and Persistence Boundary`.

The resulting responsibility chain is:

```text
Metadata
    → defines

Runtime
    → executes

Posting
    → produces accounting facts

Register
    → validates and organizes facts

Persistence Scope
    → defines logical consistency boundary

Persistence Contracts
    → define semantic persistence operations
      and required consistency guarantees

Storage
    → owns persistence representation

Storage Provider
    → implements physical storage
```

No layer is permitted to bypass the boundary by depending directly on database or filesystem transaction APIs.

---

## Implementation Implication

The decision is reflected in the completed Phase 5 persistence architecture and implementation boundaries.

The following artifacts establish the concrete consequences of this ADR:

1. **Persistence Scope Semantic Contract**
2. **Consistency & Failure Matrix**
3. **Persistence Contract Concrete API**
4. **Storage Provider Boundary**
5. **Persistent Object Representation and Runtime Mapping**

The implementation remains technology-independent at the Persistence Contract and Mapping boundaries. Concrete storage mechanisms remain below the Storage boundary.

---

## Status

**Accepted — implementation and architectural alignment completed.**
