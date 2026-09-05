# Phase 5 — Persistence Contract API

**Phase:** 5 — Storage & Persistence Boundary
**Step:** 3A — Concrete Python Contract Design
**Status:** Architecture Definition
**Version:** 1.0
**Related ADR:** `ADR-P5-001`
**Related Model:** `PHASE_5_PERSISTENCE_DOMAIN_MODEL.md`
**Related API Matrix:** `PHASE_5_PERSISTENCE_API_MATRIX.md`
**Next Step:** Step 5 — Transaction / Consistency Model

---

## 1. Purpose

This document defines the concrete Python-level shape of the AcCoreD Persistence Contracts.

It translates the architectural persistence capabilities into Python protocols, value types, result types, and semantic exceptions.

This document defines **contracts only**.

It does not define:

* a storage provider;
* a database;
* a physical schema;
* serialization;
* ORM models;
* SQL;
* transaction implementation;
* a universal repository;
* a universal query language.

---

# 2. Design Principles

The Python API MUST preserve the following architectural properties:

1. Persistence contracts are provider-independent.
2. Persistent Object persistence and Register Fact persistence are separate capabilities.
3. Append semantics are distinct from update semantics.
4. Query is a separate capability.
5. Persistence Scope is a semantic consistency boundary.
6. Logical AcCoreD identity is used instead of physical storage identifiers.
7. Provider-specific exceptions do not cross the persistence boundary.
8. Resource-specific contracts expose only supported operations.
9. Persistence contracts do not contain business logic.
10. Runtime objects are not implicitly persistence objects.

---

# 3. Package Structure

The initial platform package is:

```text
src/accore/platform/persistence/
├── __init__.py
├── errors.py
├── objects.py
├── facts.py
├── queries.py
└── scope.py
```

Responsibilities:

| Module        | Responsibility                         |
| ------------- | -------------------------------------- |
| `errors.py`   | Semantic persistence exceptions        |
| `objects.py`  | Persistent Object persistence contract |
| `facts.py`    | Register Fact append contract          |
| `queries.py`  | Logical query contracts                |
| `scope.py`    | Persistence Scope contract             |
| `__init__.py` | Public persistence API                 |

No provider implementation belongs in this package.

---

# 4. Common Type Requirements

Persistence contracts operate on logical persistence representations.

They MUST NOT require concrete database records, ORM objects, cursors, sessions, or provider-specific identifiers.

Where an existing AcCoreD identity/value type already provides the required semantics, that type MUST be reused.

A new persistence-specific identity type MUST NOT be introduced merely to represent a physical storage identifier.

---

# 5. Persistent Object Contract

## 5.1 Purpose

`ObjectPersistence` provides persistence operations for durable object state.

The contract represents state-oriented persistence.

It does not define business object behavior.

---

## 5.2 Protocol

Conceptually:

```python
from typing import Protocol, TypeVar

ObjectT = TypeVar("ObjectT")
IdentityT = TypeVar("IdentityT")


class ObjectPersistence(Protocol[ObjectT, IdentityT]):
    def create(self, obj: ObjectT) -> None:
        ...

    def read(self, identity: IdentityT) -> ObjectT:
        ...

    def exists(self, identity: IdentityT) -> bool:
        ...

    def update(self, obj: ObjectT) -> None:
        ...

    def replace(self, obj: ObjectT) -> None:
        ...
```

The exact generic constraints may be tightened during implementation if the existing AcCoreD type system provides a better representation.

---

## 5.3 Create

```python
def create(self, obj: ObjectT) -> None:
    ...
```

Semantics:

* creates persistent state for a new logical object;
* the logical identity is part of the object representation;
* an existing identity MUST result in a semantic persistence error;
* physical identifiers are provider-internal.

Expected error:

```text
PersistenceAlreadyExistsError
```

---

## 5.4 Read

```python
def read(self, identity: IdentityT) -> ObjectT:
    ...
```

Semantics:

* retrieves persistent state by logical identity;
* returns the persistence representation;
* does not construct or activate a runtime object automatically.

Expected error:

```text
PersistenceNotFoundError
```

---

## 5.5 Exists

```python
def exists(self, identity: IdentityT) -> bool:
    ...
```

Semantics:

* determines whether persistent state exists for the logical identity;
* MUST NOT raise `PersistenceNotFoundError`;
* provider-specific lookup details remain hidden.

---

## 5.6 Update

```python
def update(self, obj: ObjectT) -> None:
    ...
```

Semantics:

* modifies an existing persistent object;
* represents mutation semantics;
* the exact mutation granularity is defined by the object-specific contract;
* absence of the object MUST be reported semantically.

Concurrency conflict MAY result in:

```text
PersistenceConflictError
```

---

## 5.7 Replace

```python
def replace(self, obj: ObjectT) -> None:
    ...
```

Semantics:

* replaces the complete persistent representation of an existing object;
* replacement is distinct from partial or mutation-oriented update;
* lifecycle restrictions remain resource-specific.

`Replace` MUST NOT be interpreted as unconditional creation.

---

# 6. Delete

Deletion is deliberately absent from the base `ObjectPersistence` protocol.

A persistent resource that supports deletion MAY define a more specific capability:

```python
class ObjectDeletion(Protocol[IdentityT]):
    def delete(self, identity: IdentityT) -> None:
        ...
```

This prevents deletion from becoming an implicit capability of every persistent resource.

Deletion semantics must be explicitly defined by the owning resource.

---

# 7. Register Fact Persistence

## 7.1 Purpose

Register Facts are historical business facts accepted by the Register.

Their persistence semantics are append-oriented.

They MUST NOT be represented by the object-state CRUD contract.

---

## 7.2 Protocol

The conceptual contract is:

```python
from typing import Protocol, TypeVar

MovementSetT = TypeVar("MovementSetT")


class FactPersistence(Protocol[MovementSetT]):
    def append(self, movement_set: MovementSetT) -> None:
        ...
```

The concrete `MovementSet` type MUST be aligned with the existing AcCoreD Posting/Register model during implementation.

---

## 7.3 Append

```python
def append(self, movement_set: MovementSetT) -> None:
    ...
```

Semantics:

* persists accepted Register Facts;
* preserves append-oriented semantics;
* does not modify previously accepted facts;
* does not perform Posting;
* does not validate business rules belonging to Register;
* does not generate facts.

Architectural flow remains:

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
FactPersistence.append(...)
```

Persistence is responsible only for durable storage of the accepted facts.

---

# 8. Query Contract

## 8.1 Principle

Query is a separate persistence capability.

The persistence API MUST NOT introduce a universal query language.

The following style is explicitly avoided:

```python
query(
    entity="...",
    filters=[...],
    ordering=[...],
    projection=[...],
)
```

Such an API would effectively create a provider-independent SQL-like language inside AcCoreD.

---

## 8.2 Query Protocol

The platform-level query boundary is:

```python
from typing import Protocol, TypeVar

QueryT = TypeVar("QueryT")
ResultT = TypeVar("ResultT")


class PersistenceQuery(Protocol[QueryT, ResultT]):
    def execute(self, query: QueryT) -> ResultT:
        ...
```

The `QueryT` type is expected to be a domain-specific query request.

Examples:

```python
RegisterFactsQuery
ConfigurationStateQuery
ObjectLookupQuery
```

These are examples of the architectural pattern, not mandatory platform types.

---

## 8.3 Query Ownership

Query request types SHOULD be owned by the domain/application capability that defines their meaning.

The persistence layer provides execution capability.

Therefore:

```text
Domain/Application
       │
       │ defines
       ▼
Typed Query Request
       │
       ▼
Persistence Query Contract
       │
       ▼
Storage Provider
```

The persistence layer MUST NOT interpret business semantics that belong to the query owner.

---

# 9. Persistence Scope

## 9.1 Purpose

`PersistenceScope` represents the logical consistency boundary defined by the persistence architecture.

It is intentionally not called `UnitOfWork`.

No specific transaction mechanism is implied.

---

## 9.2 Minimal Protocol

The initial contract is:

```python
from typing import Protocol


class PersistenceScope(Protocol):
    def __enter__(self) -> "PersistenceScope":
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        ...
```

The initial scope contract intentionally does not expose:

```text
commit()
rollback()
begin()
transaction()
session()
flush()
```

Those operations would prematurely couple the architectural contract to a particular transaction model.

---

## 9.3 Scope Semantics

A Persistence Scope establishes the boundary within which participating persistence operations share the required consistency semantics.

For example:

```python
with persistence_scope:
    object_persistence.update(obj)
    fact_persistence.append(movement_set)
```

The exact durability, atomicity, isolation, and rollback mechanism is provider-specific unless later architectural decisions require stronger guarantees.

---

# 10. Semantic Errors

## 10.1 Base Error

All persistence errors crossing the Persistence Boundary derive from:

```python
class PersistenceError(Exception):
    """Base class for semantic persistence errors."""
```

---

## 10.2 Error Hierarchy

The initial hierarchy is:

```text
PersistenceError
├── PersistenceNotFoundError
├── PersistenceAlreadyExistsError
├── PersistenceConflictError
├── PersistenceInvalidStateError
├── PersistenceConstraintViolationError
└── PersistenceStorageError
```

---

## 10.3 Not Found

```python
class PersistenceNotFoundError(PersistenceError):
    ...
```

Used when requested persistent state does not exist.

Typical operation:

```text
read()
```

---

## 10.4 Already Exists

```python
class PersistenceAlreadyExistsError(PersistenceError):
    ...
```

Used when creation conflicts with an already existing logical identity.

Typical operation:

```text
create()
```

---

## 10.5 Conflict

```python
class PersistenceConflictError(PersistenceError):
    ...
```

Used when an operation cannot be safely applied because the persistent state conflicts with the caller's expected state.

This category leaves the concrete concurrency mechanism intentionally undefined.

---

## 10.6 Invalid State

```python
class PersistenceInvalidStateError(PersistenceError):
    ...
```

Used when persistence operation is incompatible with the lifecycle/state of the persistent resource.

---

## 10.7 Constraint Violation

```python
class PersistenceConstraintViolationError(PersistenceError):
    ...
```

Used when a persistence-level constraint prevents an operation.

The error MUST expose semantic information rather than provider-specific constraint names where practical.

---

## 10.8 Storage Failure

```python
class PersistenceStorageError(PersistenceError):
    ...
```

Used for provider/storage failures that cannot be represented by a more specific semantic persistence error.

Provider-specific exceptions MUST be translated before crossing the Persistence Boundary.

---

# 11. Configuration Persistence

Configuration Persistent State is intentionally not introduced as part of the generic `ObjectPersistence` contract at this stage.

Its exact API will be defined when the concrete Configuration persistence requirement is implemented.

The architectural requirement remains:

```text
Configuration Persistent State
        │
        ▼
Persistence
        │
        ▼
Configuration Loader
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

Persistence MUST NOT:

* compile configuration;
* validate configuration;
* activate configuration;
* resolve runtime metadata;
* create `RuntimeConfigurationContext`.

---

# 12. Public API

The package-level public API should expose only stable platform contracts.

Conceptually:

```python
from accore.platform.persistence import (
    FactPersistence,
    ObjectPersistence,
    PersistenceError,
    PersistenceAlreadyExistsError,
    PersistenceConflictError,
    PersistenceConstraintViolationError,
    PersistenceInvalidStateError,
    PersistenceNotFoundError,
    PersistenceQuery,
    PersistenceScope,
    PersistenceStorageError,
)
```

The final export list is subject to the actual module implementation and existing AcCoreD public API conventions.

---

# 13. Explicit Non-Goals

The Step 3A API MUST NOT introduce:

### 13.1 Universal Repository

```python
Repository[T]
```

is not part of the architecture.

### 13.2 Generic Persistence Resource

A generic:

```python
PersistentResource
```

type is not required merely because Persistent Resource exists as an architectural concept.

### 13.3 Universal Query Language

No generic filter/order/projection language is introduced.

### 13.4 Unit of Work

No `UnitOfWork` abstraction is introduced at this stage.

### 13.5 Physical Storage ID

No `PersistenceId`, `RowId`, `DatabaseId`, or equivalent abstraction is introduced.

### 13.6 ORM Types

Persistence contracts MUST NOT expose ORM entities, sessions, models, or query objects.

### 13.7 Database Types

Persistence contracts MUST NOT expose database-specific connection, cursor, transaction, or driver types.

---

# 14. Contract-to-Matrix Mapping

| API Contract        | Create | Read | Update | Replace | Delete | Append | Query | Scope |
| ------------------- | :----: | :--: | :----: | :-----: | :----: | :----: | :---: | :---: |
| `ObjectPersistence` |    ✓   |   ✓  |    ✓   |    ✓    |    —   |    —   |   —   |   ✓   |
| `ObjectDeletion`    |    —   |   —  |    —   |    —    |    ✓   |    —   |   —   |   ✓   |
| `FactPersistence`   |    —   |   —  |    —   |    —    |    —   |    ✓   |   —   |   ✓   |
| `PersistenceQuery`  |    —   |   —  |    —   |    —    |    —   |    —   |   ✓   |   ✓*  |
| `PersistenceScope`  |    —   |   —  |    —   |    —    |    —   |    —   |   —   |   ✓   |

`*` Query execution MAY participate in a Persistence Scope where the provider and query semantics require it.

The matrix defines architectural capabilities. It does not require every provider or resource to implement every possible capability.

---

# 15. Architectural Invariants

### P5-API-I1 — Capability-Specific Contracts

Persistence MUST be expressed through capability-specific contracts rather than a universal repository.

### P5-API-I2 — Logical Identity

Persistence contracts MUST operate on AcCoreD logical identity.

### P5-API-I3 — Provider Independence

No provider-specific type may cross the Persistence Boundary.

### P5-API-I4 — Object/Fact Separation

`ObjectPersistence` and `FactPersistence` MUST remain separate contracts.

### P5-API-I5 — Append Semantics

Register Fact persistence MUST use append semantics.

### P5-API-I6 — Query Separation

Query execution MUST remain separate from object CRUD semantics.

### P5-API-I7 — Scope Independence

Persistence Scope MUST remain independent of a particular transaction implementation.

### P5-API-I8 — Semantic Errors

Provider-specific exceptions MUST be translated into Persistence semantic errors before crossing the boundary.

### P5-API-I9 — No Implicit Delete

Deletion MUST NOT be a mandatory capability of all persistent resources.

### P5-API-I10 — No Runtime Persistence Leakage

Persistence contracts MUST NOT require runtime objects such as `ActiveConfiguration` or `RuntimeConfigurationContext`.

---

# 16. Implementation Readiness

The Persistence Contract API is considered ready for implementation when:

* [ ] Existing AcCoreD identity/value types have been identified and reused.
* [ ] `ObjectPersistence` is implemented as a protocol.
* [ ] `FactPersistence` is implemented as a protocol.
* [ ] `PersistenceQuery` is implemented as a protocol.
* [ ] `PersistenceScope` is implemented as a protocol.
* [ ] Semantic persistence errors are implemented.
* [ ] Public package exports are defined.
* [ ] Contract-level tests are defined.
* [ ] No provider-specific dependency exists in `platform.persistence`.
* [ ] No physical storage decision has been introduced.

---

## 17. Decision

This document defines the Python-level Persistence Contract API baseline for Phase 5.

Implementation MAY now begin.

The next architectural step is **Step 5 — Transaction / Consistency Model**, where the consistency boundary between persistence contracts and storage operations will be defined without introducing database-specific semantics.
