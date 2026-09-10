# Phase 5 — Persistence Contract API

**Status:** Final — Architecture Definition
**Phase:** 5 — Storage & Persistence Boundary
**Step:** 5.4 — Persistence Contract Concrete API
**Version:** 1.0
**Date:** 2026-09-10

---

## 1. Purpose

This document defines the concrete Python API shape for the Persistence Contracts established in Phase 5.

The purpose of this step is to translate the semantic persistence model into explicit, technology-independent Python contracts.

This document defines:

* persistence contract interfaces;
* persistence representation boundaries;
* semantic persistence errors;
* operation semantics;
* missing-resource semantics;
* duplicate and concurrency semantics;
* failure semantics;
* the relationship between persistence contracts and `StorageProvider`.

This document does **not** define:

* physical database schemas;
* filesystem layouts;
* serialization formats;
* ORM models;
* database sessions or connections;
* transaction objects;
* `begin()` / `commit()` / `rollback()` APIs;
* generic repositories;
* generic query languages;
* Unit of Work abstractions;
* provider-specific concurrency mechanisms;
* provider-specific transaction mechanisms.

---

# 2. Architectural Position

Persistence Contracts are the semantic boundary between business/runtime components and physical storage.

The architecture is:

```text
Business Operation
        │
        ▼
Required Persistent Result
        │
        ▼
Persistence Scope
        │
        ▼
Persistence Contracts
        │
        ▼
Storage Boundary
        │
        ▼
Storage Provider
        │
        ▼
Physical Storage
```

Persistence Contracts describe **what must be persisted and retrieved**.

The Storage Provider describes **how opaque persistent payloads are physically stored**.

The Persistence Contract layer must not depend on the implementation technology of the Storage Provider.

---

# 3. Design Principles

## 3.1 Semantic API

Persistence APIs express persistence semantics rather than storage technology.

The API must not expose:

* SQL;
* database connections;
* database transactions;
* ORM sessions;
* filesystem paths;
* provider handles;
* storage-specific cursors;
* provider-specific transaction objects.

---

## 3.2 Domain-Specific Contracts

Persistence contracts are defined for meaningful persistence domains.

The architecture does not introduce a universal abstraction such as:

```python
Repository[T]
```

or:

```python
PersistenceService
```

or:

```python
GenericPersistence[T]
```

Persistence semantics differ between:

* business objects;
* accounting facts;
* configuration state;
* other persistence domains.

The contracts must therefore remain explicit and domain-specific.

---

## 3.3 Persistence Scope Neutrality

Individual persistence operations do not own or expose `PersistenceScope`.

A method such as:

```python
create(...)
```

does not receive:

```python
scope=...
```

as a universal argument.

A Persistence Scope is a higher-level logical consistency boundary.

The component coordinating a business operation determines which persistence operations participate in the required scope.

Therefore:

```text
Business Operation
        │
        └── Persistence Scope
                ├── ObjectPersistence
                ├── RegisterFactPersistence
                └── ConfigurationPersistence
```

rather than:

```text
ObjectPersistence.create(scope=...)
RegisterFactPersistence.append(scope=...)
```

as a mandatory universal API pattern.

---

# 4. Persistence Representation Rule

A persistence contract operates on a representation explicitly owned by that contract's domain boundary.

The representation may be:

1. a technology-independent domain type; or
2. a dedicated persistence representation.

The choice must be explicit.

A dedicated persistence representation is introduced **only when persistence semantics differ from the source domain/runtime representation**.

This prevents unnecessary duplication of domain types while preserving the distinction between runtime state and durable state.

---

# 5. Persistence Representation vs Serialized Payload

Persistence representation and physical storage payload are different architectural concepts.

For example:

```text
PersistentObject
       │
       ▼
Serialization / Mapping
       │
       ▼
Opaque bytes
       │
       ▼
StorageProvider
```

The Persistence Contract operates on the technology-independent persistence representation.

The Storage Provider operates on:

```text
StorageKey + bytes
```

The serialization or mapping mechanism between those layers is not defined by this document.

Consequently, this document does not prescribe:

* JSON;
* MessagePack;
* Pickle;
* binary schemas;
* database row mappings;
* filesystem file formats;
* ORM serialization.

---

# 6. Primary Persistence Contracts

Phase 5.4 defines three primary persistence domains:

1. Object Persistence
2. Register Fact Persistence
3. Configuration Persistence

The contracts are intentionally separate.

---

# 7. Object Persistence

## 7.1 Contract

The Object Persistence boundary provides persistence operations for durable business object state.

```python
class ObjectPersistence(Protocol):
    def create(self, obj: PersistentObject) -> None:
        ...

    def get(self, identity: Identifier) -> PersistentObject:
        ...

    def update(self, obj: PersistentObject) -> None:
        ...
```

The exact Python import location is implementation-defined.

The architectural contract is the semantic interface above.

---

## 7.2 PersistentObject

`PersistentObject` is an architectural persistence representation.

It represents durable object state.

It is **not** defined by this document as a final public dataclass or storage schema.

In particular, this document does not yet prescribe:

```python
@dataclass(frozen=True)
class PersistentObject:
    ...
```

nor does it prescribe:

* concrete fields;
* field serialization;
* version fields;
* revision representation;
* physical storage metadata;
* schema structure.

Those decisions belong to later implementation steps.

---

## 7.3 Identity

The existing `foundation.Identifier` is used directly as the object identity type.

The architecture does not introduce a separate `ObjectIdentity` or
`PersistentObjectIdentity` value type merely because the object is persisted.

Logical object identity remains independent from physical storage identity.

---

## 7.4 Create Semantics

```python
create(obj)
```

Semantics:

* creates the persistent object represented by `obj`;
* logical identity must already exist;
* persistence does not generate the object identity;
* successful completion means the requested persistent result has been accepted according to the applicable Persistence Scope requirements.

If an object with the same logical identity already exists:

```text
PersistenceAlreadyExistsError
```

is raised.

---

## 7.5 Get Semantics

```python
get(identity)
```

Semantics:

* returns the persistent object associated with `identity`;
* retrieval is direct identity-based retrieval.

If the object does not exist:

```text
PersistenceNotFoundError
```

is raised.

The API does not use:

```python
None
```

to represent absence.

---

## 7.6 Update Semantics

```python
update(obj)
```

Semantics:

* updates the persistent state represented by `obj`;
* the object identity is already known;
* update does not implicitly create a missing object.

If the object does not exist:

```text
PersistenceNotFoundError
```

is raised.

If the update violates an explicitly required concurrency condition:

```text
PersistenceConflictError
```

is raised.

The contract does not imply last-write-wins behavior.

---

## 7.7 Delete Semantics

```python
delete(identity)
```

Baseline semantics:

```text
existing object → successful deletion
missing object  → PersistenceNotFoundError
```

Delete is therefore **not implicitly idempotent**.

An idempotent delete may be introduced by a separate explicit contract or extension, but is not the baseline semantics of this API.

Deletion is an explicit capability separate from the base `ObjectPersistence` contract:

```python
class ObjectDeletion(Protocol):
    def delete(self, identity: Identifier) -> None:
        ...
```

This keeps deletion semantics explicit without making deletion a mandatory part of
every object persistence implementation.

---

# 8. Register Fact Persistence

Register persistence is intentionally separate from Object Persistence.

Accounting facts are not generic business objects.

Posting produces accounting facts, and Register accepts and organizes those facts.

The persistence layer persists register facts according to Register-specific semantics.

---

## 8.1 Contract

The concrete API is:

```python
class RegisterFactPersistence(Protocol):
    def append(self, movements: Sequence[Movement]) -> None:
        ...
```

Register fact persistence is append-only at the persistence contract boundary.
Query semantics are owned by the Register domain's query services and are not part
of this persistence contract.

---

## 8.2 Movement

`Movement` represents an accounting fact accepted by the Register domain.

It is not renamed to:

```python
PersistentMovement
```

merely because it is persisted.

The architectural rule is:

> A separate persistence representation is introduced only when persistence semantics differ from the source domain representation.

Therefore `Movement` may be used directly by the Register persistence contract if the current Register model confirms that it is already the appropriate technology-independent representation of the durable accounting fact.

If later architectural analysis demonstrates that durable Register facts have materially different semantics from `Movement`, a dedicated persistence representation may be introduced explicitly.

Such a change must be architectural, not merely naming-driven.

---

## 8.3 MovementSet

`MovementSet` remains a Posting concept.

It represents the collection of movements generated by one posting operation.

It is not a persistence entity.

The persistence API therefore does not define:

```python
PersistentMovementSet
```

merely because a `MovementSet` eventually participates in persistence.

The flow remains:

```text
Posting Handler
      │
      ▼
MovementSet
      │
      ▼
Register Validation
      │
      ▼
RegisterFactPersistence.append(...)
```

---

## 8.4 Append Semantics

```python
append(movements)
```

Semantics:

* persists the supplied accounting facts according to Register persistence rules;
* the operation is append-oriented rather than object replacement;
* existing accounting facts are not implicitly replaced by object-style update semantics.

Atomicity of the append operation itself is **not universally prescribed** by this API.

Where accounting correctness requires:

```text
Posted Object State + Register Facts
```

to be jointly published, the higher-level Persistence Scope must impose the required atomicity.

Therefore:

```text
Register append atomicity
```

and:

```text
Posting scope atomicity
```

are distinct architectural concepts.

---

## 8.5 Query Ownership

Register queries are a Register-domain concern, not a generic Persistence Contract concern.

The Register architecture defines distinct query semantics for movements, balances,
and turnovers. Consumers access those semantics through Register query services.

The Persistence Contract therefore does not define `RegisterFactQuery`,
`PersistenceQuery`, or any generic query language.

No-match behavior is likewise not a universal Persistence Contract rule; it belongs
to the specific Register query contract that defines the query.

---

# 9. Configuration Persistence

Configuration persistence is distinct from runtime configuration activation.

---

## 9.1 Contract

```python
class ConfigurationPersistence(Protocol):
    def create(self, configuration: PersistentConfiguration) -> None:
        ...

    def get(
        self,
        identity: ConfigurationIdentity,
    ) -> PersistentConfiguration:
        ...

    def update(self, configuration: PersistentConfiguration) -> None:
        ...
```

The contract does not define deletion in the baseline API.

Configuration lifecycle semantics may require additional explicit operations in later phases.

---

## 9.2 PersistentConfiguration

`PersistentConfiguration` is an architectural persistence representation.

It represents durable configuration state.

It is **not** the same thing as:

```text
ActiveConfiguration
```

or:

```text
RuntimeConfigurationContext
```

The latter are runtime concepts.

The persistence representation therefore must not be interpreted as the runtime activation state.

As with `PersistentObject`, this document does not prescribe a final dataclass, schema, field set, immutability model, or serialization format.

---

## 9.3 Configuration Identity

`ConfigurationIdentity` is used directly.

The architecture does not introduce:

```python
PersistentConfigurationIdentity
```

solely because configuration is persisted.

Logical configuration identity remains independent of physical storage identity.

---

## 9.4 Configuration Create

```python
create(configuration)
```

Semantics:

* persists the supplied configuration state;
* logical identity must already exist;
* persistence does not generate the configuration identity.

Duplicate identity results in:

```text
PersistenceAlreadyExistsError
```

---

## 9.5 Configuration Get

```python
get(identity)
```

Semantics:

* returns the persistent configuration associated with the identity.

Missing configuration results in:

```text
PersistenceNotFoundError
```

---

## 9.6 Configuration Update

```python
update(configuration)
```

Semantics:

* updates an existing persistent configuration;
* does not implicitly create a missing configuration.

Missing configuration:

```text
PersistenceNotFoundError
```

Concurrency violation:

```text
PersistenceConflictError
```

---

# 10. Mutation Return Semantics

Mutation methods return:

```python
None
```

on successful completion.

Examples:

```python
create(...) -> None
update(...) -> None
delete(...) -> None
append(...) -> None
```

The API does not use boolean success indicators:

```python
bool
```

and does not introduce a universal:

```python
Result[T]
```

wrapper.

Failure is represented through semantic persistence exceptions.

This keeps success and failure semantics explicit without introducing an additional generic result abstraction.

---

# 11. Persistence Error Taxonomy

The Persistence boundary exposes semantic errors.

The proposed hierarchy is:

```python
class PersistenceError(Exception):
    ...


class PersistenceNotFoundError(PersistenceError):
    ...


class PersistenceAlreadyExistsError(PersistenceError):
    ...


class PersistenceConflictError(PersistenceError):
    ...


class PersistenceIntegrityError(PersistenceError):
    ...


class PersistenceUnsupportedError(PersistenceError):
    ...


class PersistenceFailure(PersistenceError):
    ...


class PersistenceIndeterminateError(PersistenceError):
    ...
```

These names define semantic categories.

Concrete provider exceptions must not leak through the Persistence Contract boundary.

---

# 12. Error Semantics

## 12.1 PersistenceNotFoundError

Used when a direct persistence operation requires an existing logical resource but that resource does not exist.

Examples:

```text
get(missing)
update(missing)
delete(missing)
```

This error does not apply to a query returning no matches.

---

## 12.2 PersistenceAlreadyExistsError

Used when creation attempts to establish a logical identity that already exists.

Example:

```text
create(existing_identity)
```

Duplicate logical identity is therefore distinct from:

* provider failure;
* integrity failure;
* concurrency conflict.

---

## 12.3 PersistenceConflictError

Used when an explicitly defined concurrency requirement is violated.

Examples may include:

* stale revision;
* failed compare-and-swap condition;
* stale version;
* equivalent contract-specific concurrency mechanism.

The exact mechanism is contract-specific.

There is no universal persistence concurrency API.

---

## 12.4 PersistenceIntegrityError

`PersistenceIntegrityError` represents a persistence-level invariant violation that is not more precisely classified by another semantic persistence error.

The classification boundary is:

```text
Duplicate logical identity
        → PersistenceAlreadyExistsError

Concurrency conflict
        → PersistenceConflictError

Other persistence-level invariant violation
        → PersistenceIntegrityError

Provider/storage failure without a more specific semantic category
        → PersistenceFailure
```

This prevents different providers from mapping the same semantic condition inconsistently.

---

## 12.5 PersistenceUnsupportedError

Used when the persistence contract explicitly requires an operation or capability that the implementation does not support.

An unsupported provider capability must not silently weaken a required business consistency guarantee.

For example, an implementation must not silently downgrade a required atomic persistence result merely because the underlying provider lacks the necessary mechanism.

---

## 12.6 PersistenceFailure

`PersistenceFailure` represents a persistence failure that does not have a more precise semantic classification.

It remains deliberately technology-independent.

The name `PersistenceFailure` is preferred over names such as:

```text
PersistenceStorageError
DatabaseError
FilesystemError
```

because the Persistence boundary must not be tied to a particular physical storage mechanism.

---

## 12.7 PersistenceIndeterminateError

`PersistenceIndeterminateError` represents an operation for which the final persistence outcome cannot be determined reliably.

Example:

```text
provider operation issued
        │
        ├── provider reports success → known success
        ├── provider reports failure → known failure
        └── communication failure / unknown result
                 → indeterminate outcome
```

An indeterminate outcome is not automatically interpreted as:

* success;
* failure;
* safe to retry.

The error does **not** define a retry mechanism.

Recovery and retry semantics belong to the higher-level operation coordinating the persistence scope.

---

# 13. Provider Error Isolation

Physical provider errors must not cross the Persistence Contract boundary.

For example, the Persistence layer must not expose:

```python
sqlite3.Error
OSError
sqlalchemy.exc.*
```

or equivalent provider-specific exceptions.

The boundary maps physical failures into semantic persistence errors.

Conceptually:

```text
Provider Failure
      │
      ▼
Persistence Error Mapping
      │
      ▼
Semantic Persistence Exception
```

The mapping must preserve meaningful distinctions such as:

* missing resource;
* duplicate identity;
* concurrency conflict;
* integrity violation;
* unsupported operation;
* generic provider failure;
* indeterminate outcome.

---

# 14. Concurrency Semantics

Concurrency is explicit where correctness requires it.

The architecture does not define a universal mechanism such as:

```python
version: int
```

or:

```python
etag: str
```

or:

```python
compare_and_swap(...)
```

for every persistence contract.

A specific contract may choose an appropriate concurrency mechanism when required.

Possible mechanisms include:

* revision;
* version;
* compare-and-swap;
* ETag-like token;
* another explicitly defined contract mechanism.

The mechanism must remain below the appropriate semantic contract boundary.

---

## 14.1 No Implicit Last-Write-Wins

Persistence contracts must not implicitly define:

```text
last write wins
```

where such behavior could violate business correctness.

If concurrent modification matters, the contract must explicitly define the required behavior.

---

# 15. Atomicity

Atomicity is a property of a Persistence Scope, not a universal property of every persistence method.

Therefore this document does not state:

```text
create() is always atomic
update() is always atomic
append() is always atomic
```

in isolation.

Instead:

```text
Business Operation
        │
        ▼
Required Persistent Result
        │
        ▼
Persistence Scope
        │
        ▼
Atomicity Requirement
```

Where atomicity is required, successful completion means the required logical result is published consistently.

A failed atomic scope must not be reported as successful partial state.

---

# 16. Persistence Scope

The concrete persistence methods remain independent of transaction management.

The architecture does not require:

```python
scope.begin()
scope.commit()
scope.rollback()
```

and does not introduce a mandatory transaction object.

Persistence Scope is a logical consistency boundary defined by the operation coordinating the persistence work.

A scope may include:

```text
ObjectPersistence.create/update
RegisterFactPersistence.append
ConfigurationPersistence.create/update
```

or other persistence operations.

A scope may span multiple persistence resources and, where required, multiple Storage Providers.

---

# 17. Completion Semantics

Successful completion is semantic.

The Persistence Contract does not expose physical completion mechanisms such as:

```python
commit()
flush()
fsync()
```

Durability requirements are expressed semantically.

Where a Persistence Scope requires durable completion, successful completion means that the required persistent result satisfies the applicable durability guarantee.

The exact mechanism remains provider-specific.

---

# 18. No Universal Transaction API

This API deliberately does not define:

```python
begin()
commit()
rollback()
```

nor:

```python
Transaction
UnitOfWork
Session
```

as universal persistence abstractions.

Different providers may implement consistency through:

* database transactions;
* journaling;
* atomic replacement;
* append-only mechanisms;
* provider-specific coordination;
* other mechanisms.

Those mechanisms remain below the Persistence boundary.

---

# 19. Posting and Persistence

Posting and persistence have separate responsibilities.

The Posting Handler:

```text
generates MovementSet
```

It does not:

* persist objects;
* append register facts directly;
* manage transactions;
* perform rollback;
* update derived totals;
* coordinate persistence resources.

The higher-level Posting Engine or application/service layer coordinates the required Persistence Scope.

The conceptual flow is:

```text
Posting Handler
      │
      ▼
MovementSet
      │
      ▼
Posting Engine / Application Coordination
      │
      ├── persist posted object state
      │
      ├── append register facts
      │
      └── persist required derived state
```

If accounting correctness requires these results to be jointly published, the coordinating Persistence Scope must impose the corresponding atomicity and durability requirements.

---

# 20. Derived State

Derived state does not redefine primary accounting facts or primary object state.

The persistence contract must distinguish:

### Primary State

Examples:

* primary object state;
* primary register facts.

These are authoritative.

### Derived State

Examples:

* aggregated register state;
* materialized projections;
* caches;
* other reconstructible state.

Derived state may have different consistency and durability requirements where explicitly allowed by the architecture.

Therefore derived-state persistence must not automatically be treated as equally authoritative as primary facts.

However, if a particular derived state is part of the required persistent result of a business operation, its required consistency guarantees must be explicitly included in the relevant Persistence Scope.

---

# 21. Query Ownership

Query semantics are owned by the domain that defines the query.

The Persistence Contract API does not introduce a universal `PersistenceQuery` or
`Query[T]` abstraction. In particular, Register movement, balance, and turnover
queries remain part of the Register domain rather than the generic persistence layer.

A future persistence domain may define an explicit query contract if its own
architecture requires one. Such a contract must remain domain-specific.

---

# 22. Identity Generation

Persistence does not generate domain identities.

Logical identities are established outside the persistence implementation.

For example:

```text
Object Identity
Configuration Identity
```

must already exist when passed to persistence operations.

This preserves the separation between:

```text
Logical Identity
```

and:

```text
Physical Storage Identity
```

---

# 23. Storage Boundary Relationship

The Persistence Contract layer depends on the Storage Boundary, not on a particular Storage Provider implementation.

Conceptually:

```text
ObjectPersistence
       │
       ▼
Persistence Mapping / Serialization
       │
       ▼
StorageProvider
       │
       ▼
Physical Storage
```

The Storage Provider remains responsible for opaque physical storage.

The Storage Provider does not:

* interpret accounting facts;
* perform posting;
* validate business invariants;
* calculate valuation;
* manage workflow;
* activate configuration;
* define business-level atomicity.

---

# 24. Capability Limitations

A provider may lack a mechanism required by a Persistence Contract.

Such a limitation must be explicit.

The implementation must not silently weaken the required semantic guarantee.

For example:

```text
Required:
Posted Object State + Register Facts
must be jointly published atomically.

Provider cannot guarantee this.

Invalid behavior:
silently persist them independently and report success.

Valid behavior:
explicitly report that the required capability is unsupported
or use another implementation mechanism capable of satisfying
the contract.
```

This preserves the architecture's business consistency requirements independently of provider capability.

---

# 25. Retry Semantics

Retry is not part of the baseline Persistence Contract API.

In particular, the contract does not define:

```python
retry(...)
```

or automatic retry behavior.

Retry is a higher-level operation concern.

Where retry is introduced, it must preserve:

* logical identity;
* idempotency where required;
* atomicity requirements;
* concurrency semantics;
* avoidance of duplicate logical effects.

`PersistenceIndeterminateError` must not automatically trigger retry.

An operation with an indeterminate persistence outcome requires explicit higher-level recovery semantics.

---

# 26. Explicit Operation Semantics

The baseline semantic matrix is:

| Operation                         | Success                   | Missing                    | Duplicate                       | Conflict                                   |
| --------------------------------- | ------------------------- | -------------------------- | ------------------------------- | ------------------------------------------ |
| `ObjectPersistence.create`        | `None`                    | N/A                        | `PersistenceAlreadyExistsError` | contract-dependent                         |
| `ObjectPersistence.get`           | `PersistentObject`        | `PersistenceNotFoundError` | N/A                             | N/A                                        |
| `ObjectPersistence.update`        | `None`                    | `PersistenceNotFoundError` | N/A                             | `PersistenceConflictError`                 |
| `ObjectDeletion.delete`           | `None`                    | `PersistenceNotFoundError` | N/A                             | contract-dependent                         |
| `RegisterFactPersistence.append`  | `None`                    | contract-dependent         | contract-dependent              | `PersistenceConflictError` when applicable |
| `ConfigurationPersistence.create` | `None`                    | N/A                        | `PersistenceAlreadyExistsError` | contract-dependent                         |
| `ConfigurationPersistence.get`    | `PersistentConfiguration` | `PersistenceNotFoundError` | N/A                             | N/A                                        |
| `ConfigurationPersistence.update` | `None`                    | `PersistenceNotFoundError` | N/A                             | `PersistenceConflictError`                 |

The exact concurrency and integrity semantics of Register operations remain owned by the Register persistence contract.

---

# 27. Error Classification Matrix

| Condition                                                      | Persistence Error               |
| -------------------------------------------------------------- | ------------------------------- |
| Direct retrieval of missing resource                           | `PersistenceNotFoundError`      |
| Update of missing resource                                     | `PersistenceNotFoundError`      |
| Delete of missing resource                                     | `PersistenceNotFoundError`      |
| Duplicate logical identity on create                           | `PersistenceAlreadyExistsError` |
| Explicit concurrency condition violated                        | `PersistenceConflictError`      |
| Persistence-level invariant violation not otherwise classified | `PersistenceIntegrityError`     |
| Required capability unsupported                                | `PersistenceUnsupportedError`   |
| Provider failure with known failed outcome                     | `PersistenceFailure`            |
| Final persistence outcome cannot be determined                 | `PersistenceIndeterminateError` |

The mapping must be semantically stable across provider implementations.

---

# 28. Architectural Invariants

## P5-API1 — Semantic Contracts

Persistence APIs express persistence semantics, not physical storage technology.

## P5-API2 — Domain-Specific Contracts

Persistence domains have explicit contracts; no universal repository abstraction is introduced.

## P5-API3 — Scope Neutrality

Individual persistence methods do not universally receive or manage Persistence Scope.

## P5-API4 — No Transaction Object

Persistence Contracts do not expose a universal transaction or Unit of Work object.

## P5-API5 — Explicit Failure

Persistence failures are represented by semantic persistence exceptions.

## P5-API6 — Explicit Concurrency

Concurrency behavior is explicit where correctness requires it.

## P5-API7 — No Implicit Last-Write-Wins

The persistence API does not silently overwrite concurrent changes where correctness depends on conflict detection.

## P5-API8 — Identity Independence

Logical identity is independent from physical storage identity.

## P5-API9 — Representation Discipline

A dedicated persistence representation is introduced only when persistence semantics differ from the source domain/runtime representation.

## P5-API10 — Serialization Separation

Persistence representations are distinct from serialized storage payloads.

## P5-API11 — Provider Error Isolation

Provider-specific exceptions do not cross the Persistence Contract boundary.

## P5-API12 — Error Classification

Duplicate identity, concurrency conflict, integrity violation, provider failure, unsupported capability, and indeterminate outcome remain semantically distinguishable.

## P5-API13 — Mutation Return Simplicity

Successful mutation operations return `None`.

## P5-API14 — Retrieval Semantics

Direct missing-resource retrieval raises `PersistenceNotFoundError`.

## P5-API15 — Query Ownership

Query semantics are defined by the owning domain and are not introduced as a universal persistence query contract.

## P5-API16 — Delete Semantics

Baseline deletion of a missing resource raises `PersistenceNotFoundError`; deletion is an explicit capability separate from the base `ObjectPersistence` contract.

## P5-API17 — Atomicity Is Scope-Level

Atomicity is defined by Persistence Scope requirements and is not universally implied by an individual method.

## P5-API18 — Durability Is Semantic

Durability is a semantic completion requirement, not a physical `commit`, `flush`, or `fsync` API.

## P5-API19 — Posting Separation

Posting Handlers generate `MovementSet` and do not perform persistence coordination.

## P5-API20 — Facts Are Not Generic Objects

Accounting facts are persisted through Register-specific contracts rather than generic object persistence.

## P5-API21 — MovementSet Is Not a Persistence Entity

`MovementSet` remains a Posting concept.

## P5-API22 — Derived State Does Not Redefine Primary State

Derived state may have separate persistence semantics but does not become authoritative merely because it is persisted.

## P5-API23 — No Silent Capability Downgrade

Provider limitations must not silently weaken required business consistency guarantees.

## P5-API24 — Indeterminate Outcome Is Explicit

An indeterminate persistence outcome is distinct from known success and known failure.

## P5-API25 — No Automatic Retry

`PersistenceIndeterminateError` does not imply automatic retry.

---

# 29. Out of Scope

The following remain explicitly outside this API definition:

### Transaction Mechanisms

* database transactions;
* filesystem transactions;
* `begin`;
* `commit`;
* `rollback`;
* savepoints;
* transaction handles.

### Unit of Work

No universal:

```python
UnitOfWork
```

is defined.

### Isolation

No universal database isolation-level abstraction is defined.

Examples intentionally excluded:

```text
READ UNCOMMITTED
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

### Concurrency Mechanism

No universal:

* version field;
* revision field;
* ETag;
* compare-and-swap;
* lock;
* mutex;
* lease.

### Query Language

No universal persistence query language is defined.

### Physical Schema

No:

* database tables;
* columns;
* indexes;
* filesystem directories;
* filenames;
* physical keys.

### Serialization

No serialization format is selected.

### Provider Implementation

No provider-specific implementation is defined here.

### Recovery Protocol

No universal recovery protocol for indeterminate outcomes is defined.

### Distributed Transactions

The following remain outside Phase 5.4:

* distributed transactions;
* two-phase commit;
* saga;
* compensation protocols;
* distributed recovery protocols.

These may be considered in a future architecture step if required.

---

# 30. Architectural Flow

The final Phase 5.4 API model is:

```text
                    Business Operation
                           │
                           ▼
                  Required Persistent Result
                           │
                           ▼
                  ┌─────────────────────┐
                  │  Persistence Scope  │
                  │                     │
                  │ Atomicity           │
                  │ Durability          │
                  │ Concurrency         │
                  │ Completion          │
                  │ Failure semantics   │
                  └─────────┬───────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
      ObjectPersistence  RegisterFact  Configuration
                           Persistence   Persistence
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                 Persistence Mapping /
                     Serialization
                            │
                            ▼
                  ┌──────────────────┐
                  │ Storage Boundary │
                  └────────┬─────────┘
                           │
                           ▼
                    StorageProvider
                           │
                           ▼
                   Physical Storage
```

---

# 31. Final API Surface

The intended conceptual Python API surface for Phase 5.4 is therefore:

Object identity uses the existing `foundation.Identifier`; no separate `ObjectIdentity` type is introduced.

```python
class ObjectPersistence(Protocol):
    def create(self, obj: PersistentObject) -> None:
        ...

    def get(self, identity: Identifier) -> PersistentObject:
        ...

    def update(self, obj: PersistentObject) -> None:
        ...


class ObjectDeletion(Protocol):
    def delete(self, identity: Identifier) -> None:
        ...
```

```python
class RegisterFactPersistence(Protocol):
    def append(self, movements: Sequence[Movement]) -> None:
        ...
```

```python
class ConfigurationPersistence(Protocol):
    def create(self, configuration: PersistentConfiguration) -> None:
        ...

    def get(
        self,
        identity: ConfigurationIdentity,
    ) -> PersistentConfiguration:
        ...

    def update(self, configuration: PersistentConfiguration) -> None:
        ...
```

Semantic errors:

```python
class PersistenceError(Exception):
    ...


class PersistenceNotFoundError(PersistenceError):
    ...


class PersistenceAlreadyExistsError(PersistenceError):
    ...


class PersistenceConflictError(PersistenceError):
    ...


class PersistenceIntegrityError(PersistenceError):
    ...


class PersistenceUnsupportedError(PersistenceError):
    ...


class PersistenceFailure(PersistenceError):
    ...


class PersistenceIndeterminateError(PersistenceError):
    ...
```

These interfaces define the **semantic Persistence Contract API**.

They do not define the physical persistence implementation.

---

# 32. Phase 5.4 Acceptance Criteria

Phase 5.4 is architecturally complete when:

* [x] Object Persistence contract is concrete.
* [x] Register Fact Persistence contract is concrete.
* [x] Configuration Persistence contract is concrete.
* [x] Persistence representations are explicitly separated from serialized payloads.
* [x] `PersistentObject` is treated as an architectural representation, not a premature schema.
* [x] `PersistentConfiguration` is treated as an architectural representation, not a premature schema.
* [x] `Movement` is used only if confirmed appropriate by the Register domain model.
* [x] `MovementSet` remains a Posting concept.
* [x] Mutation methods return `None`.
* [x] Direct missing-resource operations raise `PersistenceNotFoundError`.
* [x] Query semantics are owned by domain-specific query contracts; no universal query result rule is introduced.
* [x] Duplicate identity maps to `PersistenceAlreadyExistsError`.
* [x] Concurrency conflicts map to `PersistenceConflictError`.
* [x] Persistence integrity violations have a defined boundary.
* [x] Provider failures map to `PersistenceFailure`.
* [x] Indeterminate outcomes map to `PersistenceIndeterminateError`.
* [x] Unsupported capabilities map to `PersistenceUnsupportedError`.
* [x] Delete semantics are explicit and deletion is a separate object capability.
* [x] Concurrency remains contract-specific.
* [x] Atomicity remains a Persistence Scope property.
* [x] Durability remains a semantic requirement.
* [x] No universal transaction API is introduced.
* [x] No universal Unit of Work is introduced.
* [x] No universal Repository is introduced.
* [x] No universal Query abstraction is introduced.
* [x] Posting Handler remains independent of persistence coordination.
* [x] Provider-specific exceptions remain below the Persistence boundary.
* [x] Provider capability limitations cannot silently weaken required consistency.
* [x] Retry remains outside the persistence contract.
* [x] Indeterminate persistence outcome does not imply automatic retry.

---

# 33. Implementation Alignment and Finalization

The concrete persistence contract architecture has been implemented and validated.

The implementation alignment is complete for the currently defined Phase 5 persistence boundary:

* core persistence contracts are implemented under `accore.platform.persistence`;
* semantic persistence errors are explicit;
* object, register-fact, and deletion capabilities remain separate;
* runtime/persistence mapping is explicit;
* provider-specific mechanisms remain below the Persistence boundary;
* no universal transaction, Unit of Work, Repository, or Query abstraction has been introduced.

The implementation and tests are now the realization of this architecture rather than an unreviewed implementation candidate.

**Status: Final — implementation aligned.**
