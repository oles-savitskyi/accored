# Phase 5 — Persistence Contracts

**Document:** `PHASE_5_PERSISTENCE_CONTRACTS.md`
**Phase:** 5 — Storage & Persistence Boundary
**Step:** 3 — Persistence Contracts
**Status:** Architecture Definition
**Version:** 1.0
**Related ADR:** `ADR-P5-001`
**Related Model:** `PHASE_5_PERSISTENCE_DOMAIN_MODEL.md`
**Previous Step:** Step 2 — Persistence Domain Model
**Next Step:** Step 5 — Transaction / Consistency Model

---

# 1. Purpose

This document defines the **Persistence Contracts** of AcCoreD.

The purpose of the contracts is to translate the logical Persistence Domain Model into explicit application-facing boundaries that can be implemented by one or more Storage Providers.

The contracts define:

* what persistence capabilities are exposed to higher layers;
* how persistent resources are addressed;
* how persistent object state is created, read, and changed;
* how append-only facts are persisted;
* how logical queries are represented;
* how consistency scopes are represented;
* how persistence errors cross the boundary;
* how Storage Providers implement the persistence boundary.

The contracts intentionally do not define:

* database technology;
* physical schema;
* SQL;
* ORM APIs;
* serialization format;
* physical transaction APIs;
* connection management;
* indexes;
* migrations.

---

# 2. Architectural Position

Persistence Contracts form the public architectural boundary between application/domain/runtime code and Storage Providers.

```text
┌───────────────────────────────────────────────┐
│           Runtime / Domain / Application      │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│             Persistence Contracts             │
│                                               │
│  Object Persistence                           │
│  Fact Append                                  │
│  Queries                                      │
│  Persistence Scope                            │
│  Semantic Errors                               │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              Storage Provider                 │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│               Physical Storage               │
└───────────────────────────────────────────────┘
```

The dependency direction is:

```text
Higher Layers
      │
      ▼
Persistence Contracts
      ▲
      │
Storage Provider
```

The Storage Provider implements the contracts.

The higher layers must not depend on the concrete provider.

---

# 3. Contract Principle

The central rule is:

> **Persistence Contracts express semantic persistence capabilities, not storage technology.**

A contract must describe:

* what the caller wants to persist or retrieve;
* what result is returned;
* what semantic failure may occur;
* what consistency guarantees apply.

A contract must not describe:

* how the provider stores the data;
* which physical query language is used;
* which database connection is required;
* which ORM model is involved.

---

# 4. Design Goals

Persistence Contracts must provide:

### 4.1 Technology Independence

The same higher-level code must be able to work with different Storage Providers.

### 4.2 Semantic Clarity

The contract must preserve distinctions established in the Persistence Domain Model.

For example:

```text
Update ≠ Append
Object State ≠ Register Fact
Logical Identity ≠ Physical Storage ID
Persistence Scope ≠ Database Transaction
```

### 4.3 Minimal Surface

Contracts should expose only capabilities that higher layers actually require.

### 4.4 Explicit Failure

Persistence failures must be represented using semantic persistence errors.

### 4.5 Replaceability

A Storage Provider may be replaced without changing domain/application semantics.

---

# 5. Contract Vocabulary

The following concepts are used by the contracts.

| Concept               | Meaning                                  |
| --------------------- | ---------------------------------------- |
| Persistent Resource   | Logical durable resource                 |
| Persistent Entity     | Defines persistence domain and lifecycle |
| Persistent Object     | Durable representation of object state   |
| Register Fact         | Durable accepted business fact           |
| Persistence Operation | Semantic persistence action              |
| Persistence Query     | Logical retrieval request                |
| Persistence Scope     | Logical consistency boundary             |
| Identity              | Stable logical resource identity         |
| Version               | Particular state/version of a resource   |

These definitions are inherited from:

`PHASE_5_PERSISTENCE_DOMAIN_MODEL.md`

---

# 6. Contract Layers

Persistence Contracts are divided into four primary capabilities:

```text
Persistence Contracts
│
├── Object Persistence
│
├── Fact Persistence
│
├── Query
│
└── Persistence Scope
```

A fifth concern crosses all four:

```text
Semantic Persistence Errors
```

These capabilities should remain conceptually distinct even if later implementation chooses to compose them into larger provider interfaces.

---

# 7. Persistent Resource Identity

Persistence contracts use logical AcCoreD identity.

The contract must not require a physical storage identifier.

Conceptually:

```text
Logical Identity
      │
      ▼
Persistence Contract
      │
      ▼
Storage Provider
      │
      ▼
Physical Identifier
```

The provider is responsible for mapping logical identity to physical storage.

---

# 8. Resource Type / Entity Identity

A persistence operation must be able to identify **what kind of persistent resource** is being addressed.

Conceptually, a persistence address contains:

```text
Persistent Entity Identity
+
Logical Resource Identity
```

For example:

```text
Document
+
Document Identity
```

or:

```text
Register Fact Set
+
Register Identity / Query Scope
```

The exact Python representation is an implementation concern for the contract implementation stage.

The architectural requirement is that resource type and logical identity remain distinct.

---

# 9. Persistent Object Contract

Persistent Objects represent durable object state.

The persistence contract must provide semantic operations appropriate to mutable object state.

The conceptual contract is:

```text
Object Persistence
├── Create
├── Read
├── Update / Replace
└── Exists
```

Delete is not assumed to be universally supported.

---

# 10. Create Contract

The Create capability establishes a new Persistent Object.

Conceptually:

```text
create(resource) -> persisted state
```

The contract must guarantee:

1. The logical identity is preserved.
2. An existing resource is not silently overwritten.
3. The resulting state is durably accepted according to the provider's persistence semantics.
4. Semantic errors are returned through the Persistence Error Model.

Possible failures include:

* `AlreadyExists`;
* `InvalidState`;
* `ConstraintViolation`;
* `StorageFailure`.

---

# 11. Read Contract

The Read capability retrieves an existing Persistent Object.

Conceptually:

```text
read(identity) -> persistent object
```

The contract must operate on logical identity.

A missing resource results in:

```text
NotFound
```

rather than a provider-specific "row not found", "document missing", or equivalent exception.

---

# 12. Exists Contract

The Exists capability determines whether a logical Persistent Object exists.

Conceptually:

```text
exists(identity) -> bool
```

The operation does not require returning the complete object.

It must use the same logical identity semantics as Read.

---

# 13. Update Contract

The Update capability modifies an existing Persistent Object.

Conceptually:

```text
update(resource) -> updated resource
```

Update semantics are applicable only where the Persistent Entity permits mutable state.

The contract must preserve:

* logical identity;
* valid lifecycle state;
* applicable version semantics.

If version/concurrency control is required and the supplied state is stale, the operation may fail with:

```text
Conflict
```

---

# 14. Replace Contract

Replace is a semantic capability for replacing the persisted representation/state of an existing resource.

Conceptually:

```text
replace(identity, state) -> persisted state
```

Replace may be useful where the caller has an authoritative complete representation of the resource.

The architecture does not require every Persistent Entity to support Replace.

Where both Update and Replace exist, their semantics must be explicitly distinguished by the corresponding contract.

---

# 15. Update vs Replace

The architecture must not assume that:

```text
Update == Replace
```

Possible semantic distinction:

```text
Update
    expresses modification of existing state

Replace
    expresses replacement of the complete persisted representation
```

The final contract for a particular Persistent Entity determines whether one or both operations are exposed.

---

# 16. Delete Contract

Delete is an optional persistence capability.

A generic persistence contract must not assume that every Persistent Resource can be deleted.

For a resource that supports deletion:

```text
delete(identity)
```

may be defined.

For a resource that is:

* immutable;
* historical;
* append-only;
* audit-sensitive;
* lifecycle-controlled;

delete may be prohibited.

The absence of a Delete capability is therefore a valid architectural design.

---

# 17. Append Contract

Append represents persistence of a new fact/resource without modifying existing persisted facts.

Conceptually:

```text
append(fact) -> persisted fact
```

Append is intentionally separate from Update.

The distinction is:

```text
Update:
    Existing State
         │
         ▼
    New State

Append:
    Existing Facts
         +
    New Fact
```

This is especially important for Register Facts.

---

# 18. Register Fact Persistence Contract

The Register subsystem produces accepted Register Facts.

The persistence contract receives those facts after they have passed the appropriate domain/register processing.

Conceptually:

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
Fact Persistence Contract
   │
   ▼
Storage Provider
```

The Fact Persistence Contract must not:

* generate movements;
* validate accounting semantics;
* calculate postings;
* decide debit/credit meaning;
* modify business facts.

It persists facts that have already been accepted by the responsible subsystem.

---

# 19. Fact Immutability

Register Facts are conceptually historical facts.

Therefore the default persistence semantic is:

```text
Append
```

rather than:

```text
Update
```

If a future domain explicitly requires correction, reversal, or supersession semantics, those must be represented as domain-level facts or lifecycle operations rather than silently mutating historical facts.

The persistence layer must preserve the semantics selected by the Register architecture.

---

# 20. Persistence Query Contract

The Query Contract provides logical access to persisted information.

Conceptually:

```text
query(request) -> result
```

The request expresses logical requirements.

The contract must not expose:

* SQL;
* SQL fragments;
* ORM query objects;
* database-specific filters;
* physical table names;
* collection names.

---

# 21. Query Request

A Query Request represents a logical retrieval requirement.

Conceptually it may contain:

```text
Query Identity / Type
+
Criteria
+
Ordering
+
Range / Pagination
```

The exact structure depends on the query domain.

The architecture does not require one universal query language.

---

# 22. Query Result

A Query Result represents data returned according to the logical query contract.

The result may contain:

* zero or more logical resources;
* selected persistent state;
* register facts;
* projections;
* aggregate results.

A query result does not expose the physical storage representation.

---

# 23. Domain-Specific Queries

Persistence Contracts should allow domain-specific queries without turning the Persistence Boundary into a physical query language.

For example:

```text
Register:
    facts_for_period(...)

Object:
    find_by_identity(...)

Configuration:
    load_configuration_state(...)
```

These are logical operations.

The Storage Provider determines how they are implemented physically.

---

# 24. Query and Business Semantics

A query may express business-relevant information, but it must not implement business rules that belong to higher layers.

For example:

```text
Query:
    retrieve register facts for a period
```

is persistence behavior.

Whereas:

```text
Business Rule:
    determine whether the resulting balance satisfies a domain rule
```

belongs outside the Storage Provider.

The boundary must remain explicit.

---

# 25. Persistence Scope Contract

Persistence Scope represents a logical consistency boundary.

Conceptually:

```text
scope:
    operation A
    operation B
    operation C

    commit / complete
```

The contract expresses the requirement that a group of persistence operations must satisfy a common consistency boundary.

The implementation mechanism is deferred.

---

# 26. Persistence Scope Lifecycle

A Persistence Scope may conceptually follow:

```text
Created
   │
   ▼
Active
   │
   ├────► Completed
   │
   └────► Failed / Aborted
```

The exact implementation is not defined by this document.

The important requirement is that higher layers can express:

> These persistence operations belong to one logical consistency scope.

---

# 27. Persistence Scope Does Not Define Transaction Technology

The contract must not expose:

* database transaction objects;
* connections;
* sessions;
* cursors;
* ORM units of work.

A provider may internally implement a Persistence Scope using such mechanisms.

Those details remain below the contract boundary.

---

# 28. Example Persistence Scope

A posting operation may require:

```text
Persistence Scope
│
├── Persist Document State
│
├── Append Register Facts
│
└── Persist Required Derived State
```

The architectural requirement is:

> The resulting durable state must satisfy the consistency semantics defined for posting.

Whether this is implemented using one physical transaction or another mechanism is a Storage Provider concern.

---

# 29. Semantic Persistence Errors

All contracts use semantic persistence errors.

The conceptual hierarchy is:

```text
PersistenceError
├── NotFound
├── AlreadyExists
├── Conflict
├── InvalidState
├── ConstraintViolation
└── StorageFailure
```

The exact Python exception hierarchy will be established during implementation.

---

# 30. Error: NotFound

`NotFound` indicates that the requested logical resource does not exist.

Example:

```text
read(document_id)
        │
        ▼
    NotFound
```

The caller does not need to know how the provider determined that the resource was missing.

---

# 31. Error: AlreadyExists

`AlreadyExists` indicates that a Create operation attempted to establish a logical resource whose identity is already present.

This prevents silent overwrites.

---

# 32. Error: Conflict

`Conflict` indicates that the requested operation cannot safely proceed because persistent state has changed or otherwise conflicts with the caller's expected state.

Potential causes include:

* stale version;
* concurrent update;
* incompatible persistent state.

The concrete conflict-detection mechanism remains provider-independent.

---

# 33. Error: InvalidState

`InvalidState` indicates that the persistence operation is not valid for the current persistence lifecycle/state.

This is a persistence lifecycle concern.

It must not become a general-purpose replacement for domain validation.

---

# 34. Error: ConstraintViolation

`ConstraintViolation` indicates violation of a constraint explicitly belonging to the persistence contract.

Examples may include:

* required persistence field missing;
* identity constraint;
* persistence-level uniqueness requirement.

Domain/business validation remains outside this error category unless explicitly defined as a persistence constraint.

---

# 35. Error: StorageFailure

`StorageFailure` represents an infrastructure/provider failure preventing an otherwise valid persistence operation from completing.

Examples may include:

* unavailable storage;
* connectivity failure;
* provider-level failure;
* physical I/O failure.

Provider-specific exceptions must be translated before crossing the Persistence Boundary.

---

# 36. Provider Error Translation

The Storage Provider is responsible for translating physical/provider errors into semantic persistence errors.

Conceptually:

```text
Physical Provider Exception
          │
          ▼
    Storage Provider
          │
          ▼
 Semantic Persistence Error
          │
          ▼
 Persistence Contract
```

No higher layer should need to import a provider-specific exception type.

---

# 37. Concurrency Contract

Persistence Contracts must allow a Persistent Entity to define whether concurrent modification detection is required.

Where required, the contract must support sufficient information to detect a conflicting state.

Version is the preferred architectural concept for expressing the expected state:

```text
Identity
+
Expected Version
+
New State
```

However, this document does not mandate a specific concurrency algorithm.

---

# 38. Optimistic Concurrency Is Not Yet Mandated

The architecture does not currently mandate optimistic concurrency for every Persistent Resource.

A future contract may use:

* expected version;
* compare-and-update;
* locking;
* another mechanism.

The semantic requirement is:

> Where concurrency protection is required, conflicting state must not be silently overwritten.

---

# 39. Configuration Persistence Contract

Configuration persistence is a specialized persistence capability.

Its conceptual responsibility is to load and store **Configuration Persistent State**.

The flow remains:

```text
Persistent Configuration State
            │
            ▼
     Configuration Loader
            │
            ▼
        Candidate
            │
            ▼
        Validation
            │
            ▼
        Activation
            │
            ▼
   ActiveConfiguration
```

The Persistence Contract must not return `ActiveConfiguration` directly.

`ActiveConfiguration` remains a runtime concept.

---

# 40. Configuration Persistence Boundary

The configuration persistence contract should provide the durable configuration state required by the Configuration subsystem.

It must not perform:

* metadata compilation;
* configuration validation;
* activation;
* runtime binding;
* runtime resolution.

Those responsibilities remain in the existing Configuration/Runtime architecture.

---

# 41. Persistence Contract Composition

The contracts should be composable.

Conceptually:

```text
Persistence Provider
│
├── Object Persistence
│
├── Fact Persistence
│
├── Query
│
└── Scope
```

A provider may implement all capabilities or only the capabilities required by a particular application configuration.

This supports modularity and avoids forcing unrelated persistence operations into a single interface.

---

# 42. No Universal Repository Contract

AcCoreD does not introduce a universal:

```text
Repository
```

abstraction at this stage.

A generic repository often hides important semantic differences between:

* mutable object state;
* append-only facts;
* configuration state;
* queries;
* historical data.

The architecture therefore prefers explicit persistence capabilities.

A repository-like abstraction may be introduced later for a specific domain if it provides genuine semantic value.

---

# 43. Contract Dependency Direction

The dependency direction must remain:

```text
Application / Domain
       │
       ▼
Persistence Contracts
       ▲
       │
Storage Provider
```

The reverse dependency is forbidden:

```text
Application
     │
     └──► PostgreSQL / SQLite / ORM / Provider API
```

unless explicitly introduced outside the architectural Persistence Boundary.

---

# 44. Contract Ownership

Persistence Contracts belong to the AcCoreD platform architecture.

They are not owned by a particular Storage Provider.

Conceptually:

```text
AcCoreD Platform
      │
      ▼
Persistence Contracts
      ▲
      │
┌─────┴──────────────┐
│                    │
▼                    ▼
Provider A         Provider B
```

This ensures that the provider implements an existing platform contract rather than defining the contract itself.

---

# 45. Contract Stability

Persistence Contracts form an architectural boundary and therefore require greater stability than provider internals.

Changes to contracts may affect:

* Runtime;
* Domain;
* Application;
* Configuration;
* Register;
* Storage Providers;
* tests.

Therefore contract changes should be deliberate and accompanied by corresponding architectural documentation.

---

# 46. Conceptual Contract Model

The resulting contract model is:

```text
                     Persistence Contracts
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
       Object Persistence  Fact Append       Query
              │               │                │
              └───────────────┼────────────────┘
                              │
                              ▼
                    Persistence Scope
                              │
                              ▼
                       Storage Provider
```

Cross-cutting:

```text
              Semantic Persistence Errors
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Objects          Facts         Queries
```

---

# 47. Conceptual Python Shape

The implementation should eventually express the contracts using Python abstractions such as:

```text
Protocol
Abstract semantic types
Dataclasses where appropriate
Domain-specific result types
Semantic exception types
```

However, the exact Python API is intentionally not fixed by this architecture document.

The implementation must derive from the semantics defined here.

---

# 48. Implementation Constraints

When implementing the contracts:

### Must

* use logical identity;
* preserve semantic operation differences;
* isolate provider-specific errors;
* keep provider dependencies below the contract boundary;
* keep domain/business rules outside storage;
* make unsupported operations explicit;
* test contract behavior independently of physical storage.

### Must Not

* import a database driver into the contract layer;
* expose SQL;
* expose ORM models;
* expose physical IDs;
* expose database transactions;
* make Register Facts mutable merely for storage convenience;
* make every runtime object persistent.

---

# 49. Contract Testability

Persistence Contracts must be testable independently of a concrete production Storage Provider.

A contract test suite should eventually be applicable to multiple provider implementations.

Conceptually:

```text
Contract Tests
      │
      ├────────► Provider A
      │
      ├────────► Provider B
      │
      └────────► In-Memory Provider
```

The purpose is to verify that providers satisfy the same semantic contract.

An in-memory provider may be used for tests, but its implementation must not become the architectural definition of persistence.

---

# 50. In-Memory Provider

An in-memory implementation may be introduced as a development/test provider.

Its purpose is:

* contract testing;
* fast unit tests;
* development;
* experimentation.

It must not be treated as the canonical persistence architecture.

The production Storage Provider remains an independent implementation decision.

---

# 51. Persistence Mapping

The Persistence Contract separates logical state from physical representation.

Conceptually:

```text
Logical Persistent State
          │
          ▼
Persistence Contract
          │
          ▼
Provider Mapping
          │
          ▼
Physical Representation
```

The provider mapping may perform:

* serialization;
* deserialization;
* field mapping;
* identifier mapping;
* physical query construction.

These are provider implementation responsibilities.

---

# 52. No Physical Leakage

The following concepts must never appear in the public Persistence Contract merely because a provider happens to use them:

```text
table
column
row
collection
document ID
SQL
cursor
connection
database session
ORM model
```

Provider-specific implementation may use them internally.

---

# 53. Persistence Contract and Metadata

Persistence Contracts may consume metadata-defined information where required by higher architecture.

However, persistence must not become responsible for compiling or interpreting metadata business semantics.

The dependency direction remains:

```text
Metadata
   │
   ▼
Runtime / Domain Semantics
   │
   ▼
Persistence Contracts
   │
   ▼
Storage Provider
```

Persistence may store metadata-related durable state, but it does not replace the Metadata subsystem.

---

# 54. Persistence Contract and Object Model

The Object subsystem owns object behavior and lifecycle semantics.

Persistence provides durable state access.

Conceptually:

```text
Object Model
     │
     ├── behavior
     ├── lifecycle
     └── business semantics
             │
             ▼
     Persistence Contract
             │
             ▼
          Storage
```

Persistence must not become the owner of Object behavior.

---

# 55. Persistence Contract and Posting

Posting produces Register Facts.

Persistence stores them.

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
Accepted Facts
   │
   ▼
Fact Persistence Contract
```

The persistence contract must not introduce an alternative posting path.

---

# 56. Persistence Contract and Reporting

Reporting may consume persisted data through appropriate Query Contracts.

Conceptually:

```text
Persistent State / Facts
           │
           ▼
      Query Contract
           │
           ▼
        Reporting
```

Reporting must not need to know the physical storage implementation.

---

# 57. Persistence Contract and Valuation

Valuation may consume persistent facts/state through appropriate queries or domain-specific persistence capabilities.

The persistence boundary provides data access.

Valuation remains responsible for valuation semantics.

---

# 58. Explicit Non-Decisions

The following remain intentionally undefined:

## 58.1 Database

No database technology is selected.

## 58.2 ORM

No ORM is selected.

## 58.3 Serialization

No serialization format is selected.

## 58.4 Transaction API

No physical transaction API is exposed.

## 58.5 Unit of Work

No generic Unit of Work abstraction is introduced.

## 58.6 Repository

No universal Repository abstraction is introduced.

## 58.7 Query Language

No universal query language is introduced.

## 58.8 Connection Management

Connection pooling, sessions, and connection lifecycle are provider concerns.

## 58.9 Migration System

Schema migration is outside the current Persistence Contract definition.

## 58.10 Distributed Persistence

Replication, sharding, distributed transactions, and consensus mechanisms are outside the current scope.

---

# 59. Architectural Invariants

The following invariants govern Persistence Contracts.

### P5-CI1 — Contracts Are Technology Independent

Persistence Contracts must not depend on a concrete storage technology.

### P5-CI2 — Logical Identity Only

Contracts address resources using logical identity, not physical identifiers.

### P5-CI3 — Semantic Operations

Contracts expose semantic operations rather than physical storage operations.

### P5-CI4 — Append Is Distinct

Append semantics must remain distinct from Update semantics.

### P5-CI5 — Facts Are Not Objects

Register Facts must remain conceptually distinct from Persistent Objects.

### P5-CI6 — Runtime State Is Not Persistence State

Contracts must not require persistence of runtime implementation state.

### P5-CI7 — Provider Error Isolation

Provider-specific exceptions must not cross the Persistence Boundary.

### P5-CI8 — Business Semantics Stay Above Storage

Persistence contracts must not become a container for business rules.

### P5-CI9 — Scope Is Logical

Persistence Scope expresses consistency semantics without requiring a specific transaction technology.

### P5-CI10 — Provider Replaceability

Different Storage Providers must be able to implement the same logical contracts.

### P5-CI11 — Unsupported Operations Are Explicit

A Persistent Entity is not required to support every generic persistence operation.

### P5-CI12 — No Universal Repository

A single generic repository abstraction is not part of the Phase 5 architecture unless later evidence establishes a clear semantic need.

---

# 60. Step 3 Completion Criteria

Step 3 is architecturally complete when:

* Persistence Contracts are explicitly defined;
* object persistence semantics are defined;
* fact append semantics are defined;
* query semantics are defined;
* Persistence Scope is defined;
* semantic persistence errors are defined;
* logical identity is used throughout;
* version/conflict semantics are acknowledged;
* provider errors are isolated;
* provider-specific APIs are excluded;
* configuration persistence is distinguished from runtime configuration;
* contract testability is established as a requirement;
* no concrete database or physical schema is introduced.

---

# 61. Next Step

The next architectural step is:

> **Step 5 — Transaction / Consistency Model**

Step 5 will define the consistency boundary between Persistence Contracts and
Storage Provider operations, without introducing database-specific semantics.

The completed Step 4 Storage Provider Boundary remains below the Persistence
Contracts and provides the physical storage implementation boundary.

---

# 62. Final Architectural Statement

Phase 5 Step 3 establishes the following boundary:

```text
┌─────────────────────────────────────────────┐
│       Domain / Application / Runtime        │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
              Persistence Contracts
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       Objects       Facts        Queries
          │            │            │
          └────────────┼────────────┘
                       │
                       ▼
              Persistence Scope
                       │
                       ▼
                Storage Provider
                       │
                       ▼
               Physical Storage
```

The essential rule is:

> **Persistence Contracts define what durable-state access means to AcCoreD. Storage Providers define how those semantics are implemented.**

The contracts therefore become the stable architectural boundary through which AcCoreD interacts with persistence, while allowing physical storage technology to remain replaceable and deferred.
