# PHASE 7 — STEP 2

# REGISTER STORAGE CONTRACT

**Status:** Final — Architecture Review Approved
**Phase:** Phase 7 — Register Implementation
**Step:** 2 — Register Storage Contract
**Depends on:** Phase 5 Persistence Architecture, Phase 6 Register Movement Contract, Phase 7 Step 1 Architecture Definition
**Next:** Step 3 — Movement Query Contract

---

## 1. Purpose

This document defines the semantic contract of Register Storage for Phase 7.

The purpose of Register Storage is to establish the Register-specific semantic persistence layer for accounting Movements while preserving the architectural separation between:

* accounting facts;
* Register-specific persistence semantics;
* generic persistence infrastructure;
* Register Query semantics;
* totals and balances;
* Posting consistency.

Register Storage persists accepted `Movement` facts and provides the minimal fact-oriented persistence capabilities required by the Register Architecture.

Register Storage does **not**:

* introduce a second persistence architecture;
* become a generic repository;
* own Register Query semantics;
* own Totals semantics;
* own Posting lifecycle semantics;
* define the global logical accounting consistency boundary.

The dependency direction is:

```text
Register Architecture
        │
        ▼
Register Storage
        │
        ▼
RegisterFactPersistence
        │
        ▼
Phase 5 Persistence Architecture
        │
        ▼
Storage Provider
```

`RegisterFactPersistence` is the persistence abstraction boundary between Register Storage semantics and the generic Phase 5 Persistence Architecture.

---

# 2. Architectural Position

The Phase 7 architecture is:

```text
Posting
    │
    ▼
MovementSet
    │
    ▼
Movement Validation
    │
    ▼
Logical Consistency Scope
    │
    ├── Register Storage
    │       │
    │       ▼
    │   RegisterFactPersistence
    │       │
    │       ▼
    │   Phase 5 Persistence
    │       │
    │       ▼
    │   Persisted Movements
    │
    └── Totals Maintenance
            │
            ▼
        Persisted Totals
```

Read-side:

```text
Persisted Movements
        │
        ▼
Register Services
        │
        ├── Movement Query
        │
        ├── Turnover Query
        │
        └── Balance Query
```

Maintenance:

```text
Persisted Movements
        │
        ▼
Totals Rebuild
        │
        ▼
Persisted Totals
```

Register Storage is therefore part of the Register Architecture and depends on the existing Phase 5 Persistence Architecture through `RegisterFactPersistence`.

It does not access concrete storage providers directly.

---

# 3. Persistence Boundary

Phase 5 established the generic persistence architecture.

Register Storage must consume that architecture through the existing persistence abstraction:

```python
class RegisterFactPersistence(Protocol):
    def append(self, movements: Sequence[Movement]) -> None:
        ...
```

The Phase 7 boundary is therefore:

```text
Register Storage
      │
      │ semantic Register-specific persistence
      ▼
RegisterFactPersistence
      │
      │ persistence abstraction
      ▼
Phase 5 Persistence Architecture
      │
      ▼
Storage Provider
```

This distinction is normative.

### Register Storage owns

Register-specific persistence semantics such as:

* persistence of Movement facts;
* association with a Register;
* association with a source document;
* identification of existing accounting effects;
* removal of identified Movement facts;
* enumeration required for Register maintenance and rebuild.

### Phase 5 Persistence Architecture owns

Generic persistence infrastructure such as:

* persistence contracts;
* persistence errors;
* provider abstraction;
* storage-provider independence;
* generic persistence configuration and infrastructure.

Therefore:

> Register Storage is not a replacement for the Phase 5 Persistence Architecture and is not a second generic persistence layer.

There must be no parallel:

* `RegisterRepository`;
* `MovementRepository`;
* `AccountingRepository`;
* Register-specific persistence framework unrelated to `RegisterFactPersistence`.

---

# 4. Primary Accounting Fact

`Movement` is the primary persisted accounting fact.

Totals and balances are derived state.

Therefore:

```text
Movement
    ↓
primary accounting fact

Totals
    ↓
derived state

Balance
    ↓
derived query result
```

Register Storage must preserve the semantic content of a `Movement`.

It must not transform a Movement into a storage-specific semantic model that becomes a second accounting representation.

---

# 5. Movement Representation

The current `Movement` contract contains:

```python
@dataclass(frozen=True, slots=True)
class Movement:
    identity: Identifier
    source_document_identity: Identifier
    register_identity: Identifier
    movement_type: MovementType
    dimensions: MovementDimensions
    resources: MovementResources
    attributes: MovementAttributes
    accounting_time: datetime | None
```

Register Storage must preserve:

* movement identity;
* source document identity;
* register identity;
* movement type;
* dimensions;
* resources;
* attributes;
* accounting time.

The persisted representation may differ physically from the Python representation, but the semantic Movement must remain reconstructible without loss of meaning.

---

# 6. Movement Identity

Movement identity is a semantic identifier of an accounting fact.

It is distinct from:

* source document identity;
* register identity;
* runtime object identity;
* storage-provider identity;
* database primary key;
* filesystem path.

Register Storage must preserve Movement identity exactly.

Storage must not replace semantic Movement identity with a provider-generated identity.

A provider-generated physical identifier may exist internally, but it is not the accounting identity.

---

# 7. Movement Immutability

A persisted Movement represents an accounting fact.

It is immutable.

Register Storage therefore must not provide an `update(movement)` semantic operation.

There is no Phase 7 operation of the form:

```python
update(existing_movement, replacement_movement)
```

Changing accounting effects is represented by a higher-level accounting operation such as:

* Unpost;
* Repost;
* replacement of a previously accepted accounting effect.

Such operations remove or otherwise supersede applicable accounting effects and establish new Movement facts.

They do not mutate an existing Movement.

---

# 8. Source Document Association

Every persisted Movement retains its:

```text
source_document_identity
```

This association is a semantic accounting relationship.

It is required because higher-level Posting/Register orchestration must be able to determine which accounting effects belong to a document.

For example:

```text
Goods Receipt
    │
    ├── Movement A
    ├── Movement B
    └── Movement C
```

The Register Storage boundary must allow these effects to be identified through their source document identity.

---

# 9. Source Document Lookup Is a Fact Primitive

Register Storage may expose a source-document lookup capability:

```python
find_by_source_document(
    register_identity,
    source_document_identity,
)
```

This is a **fact-oriented persistence primitive**.

It is not a general Register Query API.

Its purpose is to support operations such as:

* identifying existing accounting effects for Unpost;
* identifying existing accounting effects for Repost;
* establishing the set of Movement identities that must be removed or replaced.

The storage layer must not interpret business semantics such as:

* whether a document is posted;
* whether a repost is valid;
* whether a Movement should be replaced;
* whether an accounting effect is current.

Those decisions belong to higher-level Register/Posting orchestration.

---

# 10. Register Association

Every persisted Movement has an explicit:

```text
register_identity
```

Register Storage must preserve this association.

A Movement belonging to the Inventory Register must not become indistinguishable from a Movement belonging to another Register.

The storage boundary therefore supports Register-scoped fact persistence.

---

# 11. Append Semantics

The fundamental write operation is append:

```python
append(movements)
```

Its semantic purpose is to persist accepted Movement facts.

Append must:

* preserve Movement identity;
* preserve all semantic Movement fields;
* preserve Register association;
* preserve source document association;
* reject invalid duplicate identities according to the persistence contract;
* report persistence failures through the existing persistence error model.

### Important architectural distinction

`append()` is a persistence operation.

It is **not**, by itself, the Phase 7 logical consistency boundary.

The following are separate concepts:

```text
RegisterFactPersistence.append()
        ↓
persistence operation
```

versus:

```text
Posting / Persistence Scope
        ↓
logical accounting consistency boundary
```

The higher-level consistency scope is responsible for coordinating operations that must succeed or fail as one logical accounting result.

For example:

```text
Logical Consistency Scope
    │
    ├── remove old movements
    ├── append new movements
    └── maintain totals
```

Register Storage must not redefine that larger scope as a property of the individual `append()` method.

---

# 12. Duplicate Movement Identity

Movement identity must be unique within the relevant Register persistence scope.

Attempting to append a Movement whose semantic identity already exists must not silently overwrite the existing Movement.

The implementation must instead report an appropriate persistence conflict according to the Phase 5 persistence error model.

In particular:

```text
append(existing_identity)
        ≠
update(existing_movement)
```

No implicit replacement is permitted.

---

# 13. No Silent Overwrite

Register Storage must never silently replace an existing Movement because another Movement has the same identity.

The following behavior is forbidden:

```text
existing Movement
       ↓
append same identity
       ↓
silent replacement
```

This would violate Movement immutability.

---

# 14. Optional Direct Movement Retrieval

A direct lookup by Movement identity may be useful for concrete Register implementations:

```python
get(movement_identity)
```

However, it is **not a mandatory normative capability of Step 2**.

The Phase 7 Vertical Slice does not require direct single-Movement lookup as an architectural prerequisite.

The mandatory capabilities are:

* persist Movement facts;
* identify effects by source document;
* remove identified effects;
* enumerate persisted facts for maintenance/rebuild.

If implementation demonstrates a concrete need for direct retrieval, it may be introduced during Concrete API Design without changing the semantic boundary.

This avoids prematurely expanding Register Storage into a general query repository.

---

# 15. Removal Semantics

Register Storage must support removal of persisted Movement facts when required by accounting lifecycle operations.

The primitive form is conceptually:

```python
remove(movement_identities)
```

The operation receives Movement identities.

It does not receive:

* Documents;
* Posting commands;
* business objects;
* Goods Receipts;
* Unpost requests.

The storage layer therefore remains independent of Posting semantics.

---

# 16. Responsibility for Selecting Movements to Remove

The storage layer does not determine which accounting effects must be removed.

The responsibility belongs to higher-level Register/Posting orchestration.

Conceptually:

```text
Register / Posting orchestration
        │
        ├── find_by_source_document(...)
        │
        ▼
existing Movements
        │
        ▼
Movement identities
        │
        ▼
remove(...)
```

This separation is essential.

Register Storage knows:

> how to persist and remove accounting facts.

Register/Posting orchestration knows:

> which accounting effects belong to a business operation.

---

# 17. Batch Removal

`remove()` may operate on multiple Movement identities.

This is necessary because one accounting operation may produce multiple Movement facts:

```text
Document
    ├── Movement A
    ├── Movement B
    └── Movement C
```

A Repost operation may therefore need to remove:

```text
[A, B, C]
```

as one persistence operation.

However, batch removal does **not** automatically define the overall Posting consistency boundary.

The distinction remains:

```text
remove([A, B, C])
        ↓
one persistence operation
```

versus:

```text
Repost consistency scope
        ↓
remove old effects
        +
append new effects
        +
maintain totals
```

The latter belongs to the higher-level logical consistency scope.

---

# 18. Partial Batch Failure

The Register Storage contract must not silently report a successful logical operation when only part of a requested accounting replacement has been persisted.

Where the underlying provider cannot guarantee the requested persistence result, the existing Phase 5 failure semantics must be used.

In particular, the implementation must distinguish:

```text
Success
Failure
Indeterminate
```

when the persistence contract requires such distinction.

The Register Storage layer must not invent a new failure taxonomy.

---

# 19. Enumeration for Maintenance

Register Storage must provide a fact-oriented way to enumerate persisted Movements for a Register.

Conceptually:

```python
enumerate(register_identity)
```

This capability exists primarily to support:

* totals rebuild;
* consistency verification;
* maintenance;
* recovery;
* deterministic reconstruction of derived state.

Enumeration is not the Register Query Model.

It must not evolve into an API for:

* arbitrary period filtering;
* dimension filtering;
* grouping;
* aggregation;
* balance calculation;
* turnover calculation;
* reporting.

Those semantics belong to Register Services and the Query Model.

---

# 20. Complete Enumeration

A Register totals rebuild must operate from the authoritative persisted Movement facts.

Therefore Register Storage enumeration must not omit persisted accounting facts that belong to the target Register.

Conceptually:

```text
Persisted Movements
        ↓
complete Register enumeration
        ↓
Totals Rebuild
```

The previous totals state is not the authoritative source for rebuilding totals.

---

# 21. Deterministic Enumeration

Enumeration must have deterministic semantic behavior.

If ordering is observable by the consuming Register implementation, the ordering must be explicitly defined rather than left to provider-specific incidental behavior.

However, ordering used by enumeration must not become part of the semantic Register Query Model unless explicitly defined there.

The purpose of deterministic enumeration is reproducible maintenance and testing, not to provide user-facing query ordering semantics.

---

# 22. Append and Consistency Scope

Register Storage operations participate in a larger accounting consistency architecture.

For example:

```text
Posting
   │
   ▼
Consistency Scope
   │
   ├── remove old Movement facts
   ├── append new Movement facts
   └── maintain Totals
```

The consistency scope determines whether these operations form one logical accounting result.

Register Storage itself must not claim:

> `append()` is the atomic transaction boundary for the entire accounting operation.

Likewise, Register Storage must not independently guarantee consistency between Movement persistence and Totals persistence unless that capability is explicitly provided by the higher-level persistence/consistency architecture.

---

# 23. Totals Are Not Stored Movements

Register Storage must not treat totals as Movement records.

The conceptual separation is:

```text
Movement Store
    = authoritative accounting facts

Totals Store
    = derived aggregate state
```

The same physical storage provider may persist both, but their semantic responsibilities remain distinct.

---

# 24. Rebuild Source

Totals rebuild must use persisted Movements as its source of truth.

Therefore:

```text
Persisted Movements
        ↓
Totals Rebuild
        ↓
New Totals
```

and not:

```text
Old Totals
        ↓
Totals Rebuild
        ↓
New Totals
```

The purpose of rebuild is to reconstruct derived state from authoritative facts.

---

# 25. Query Boundary

Register Storage must not implement the Phase 7 Movement Query Model.

The following belong to Register Query Services:

* period filtering;
* dimension filtering;
* partial dimension matching;
* ordering;
* grouping;
* aggregation;
* temporal/as-of semantics;
* turnover queries;
* balance queries.

Register Storage provides facts.

Register Services interpret those facts according to the Register Query Model.

Therefore:

```text
RegisterFactPersistence
        ↓
authoritative facts

Register Services
        ↓
semantic queries
```

---

# 26. Fact Persistence vs Query Semantics

This distinction is normative.

### RegisterFactPersistence owns:

* persistence of Movement facts;
* retrieval of persisted facts where required;
* source-document fact lookup;
* removal of identified Movement facts;
* Register-scoped enumeration.

### Register Query Model owns:

* what constitutes a query;
* period semantics;
* dimension semantics;
* resource selection;
* ordering;
* grouping;
* aggregation;
* balance semantics;
* turnover semantics;
* temporal query semantics.

RegisterFactPersistence must not gradually become a query repository.

---

# 27. Period Semantics

Register Storage itself does not define user-facing period-query semantics.

The Phase 7 Query Model uses the established half-open interval:

```text
[start, end)
```

This means:

```text
accounting_time >= start
AND
accounting_time < end
```

Storage may expose Movement facts containing `accounting_time`, but interpretation of periods belongs to the Query Model.

---

# 28. Accounting Time

`Movement.accounting_time` is universally represented as:

```python
datetime | None
```

This does not mean that every Register accepts `None`.

Register-specific semantics may impose stronger requirements.

For an accumulation Register such as Inventory:

> persisted accounting effects participating in accumulation must have a defined accounting time.

Therefore:

```text
Universal Movement contract
    accounting_time may be None

Inventory Register contract
    accounting_time is required for accumulation facts
```

The Inventory implementation must enforce its stronger semantic requirement at the appropriate Register boundary.

---

# 29. Dimensions

Register Storage must preserve the complete Movement dimensions.

For Inventory, the current dimensions include:

* Product;
* Warehouse.

Storage must not collapse dimensions into a provider-specific representation that loses semantic identity.

A dimension value is not equivalent to a storage column merely because it happens to be represented by one.

---

# 30. Partial Dimension Queries

Partial dimension semantics belong to Register Query Services.

For example:

```text
Product = P1
Warehouse unspecified
```

means a partial query context, not automatically:

```text
Warehouse = NULL
```

Register Storage must preserve the actual Movement dimension state without assigning query semantics to missing filter criteria.

---

# 31. Resources

Register Storage must preserve Movement resources without changing their semantic meaning.

For Inventory:

```text
Quantity
```

is a resource.

The stored value must preserve its numeric semantics.

For the current Inventory scenario, quantity is represented using `Decimal`.

Storage must not silently convert:

```text
Decimal → float
```

or otherwise introduce precision loss.

---

# 32. Movement Type

Register Storage must preserve:

```python
MovementType.INCOME
MovementType.EXPENSE
```

The storage layer must not reinterpret movement type as a generic Boolean or provider-specific flag.

Movement type remains part of the semantic accounting fact.

---

# 33. Attributes

Movement attributes must also be preserved.

Attributes may carry semantic information required by later Register processing.

Storage must not silently discard unknown or future-compatible attributes merely because the current totals implementation does not consume them.

---

# 34. Provider Independence

The Register Storage contract is independent of physical storage technology.

It must not depend on:

* SQL;
* a specific database;
* ORM models;
* filesystem layout;
* in-memory dictionaries;
* database transactions as a public semantic concept;
* provider-specific identifiers.

The implementation may use any provider allowed by the existing Persistence Architecture.

---

# 35. No Generic Repository Semantics

Register Storage must not introduce generic CRUD semantics.

In particular, the Phase 7 contract does not include:

```text
create
read
update
delete
```

as a generic object repository abstraction.

The accounting model is fact-oriented.

The required operations are semantic persistence operations for Movement facts.

---

# 36. Persistence Errors

Register Storage must use the existing Phase 5 persistence error model.

Relevant categories include:

```text
PersistenceError
PersistenceNotFoundError
PersistenceAlreadyExistsError
PersistenceConflictError
PersistenceIntegrityError
PersistenceUnsupportedError
PersistenceFailure
PersistenceIndeterminateError
```

Phase 7 must not create a parallel Register-specific persistence hierarchy unless a genuinely new semantic failure is discovered that cannot be represented by the existing contract.

---

# 37. Missing Movement

If a requested Movement does not exist and the concrete operation requires existence, the implementation must use the established persistence semantics for missing facts.

The storage layer must not silently fabricate a Movement or treat absence as successful removal unless the concrete contract explicitly defines idempotent removal.

The exact idempotency behavior of removal must be fixed during Concrete API Design and implementation.

---

# 38. Lifecycle Interaction

Register lifecycle controls when Register Storage operations are permitted.

The Register Lifecycle defines states including:

```text
Created
Registered
Initialized
Active
Maintenance
Stopped
```

Phase 7 Register Storage must respect lifecycle constraints.

In particular:

```text
Maintenance
    ↓
controlled writes / rebuild / consistency operations
```

The exact allowed operation matrix belongs to the Lifecycle/Maintenance Contract of Step 6.

Step 2 establishes only that lifecycle is an external semantic boundary and that Storage must not independently invent lifecycle semantics.

---

# 39. Maintenance

Maintenance operations include:

* totals rebuild;
* consistency verification;
* recovery;
* future migration operations.

During Phase 7, totals rebuild is explicitly a maintenance operation.

Register Storage provides the authoritative Movement facts required by maintenance.

It does not itself become the owner of the maintenance workflow.

---

# 40. Events

Register Architecture defines semantic Register events.

Register Storage does not independently redefine those events.

In particular, the existence of a semantic event such as:

```text
MovementChanged
```

must not be interpreted as permission to add:

```python
update(movement)
```

to Register Storage.

Because Movement is immutable, a change in accounting effects is represented by a higher-level replacement/reposting lifecycle.

If `MovementChanged` is retained in the architecture, its Phase 7 meaning must be understood as a Register-level semantic event describing a change in effective accounting state, not an in-place mutation of an existing Movement fact.

---

# 41. Event Ownership

The following separation applies:

```text
Register Storage
    ↓
persists facts

Register Services / Register Architecture
    ↓
owns Register event semantics

Posting
    ↓
owns Posting lifecycle semantics
```

Storage must not publish business-level Posting events merely because a persistence operation succeeded.

---

# 42. Unposting

Unposting does not mutate Movement facts.

Conceptually:

```text
existing accounting effects
        ↓
identify applicable Movements
        ↓
remove / reverse according to Register semantics
```

The exact accounting treatment of unposting remains a higher-level Register/Posting concern.

Register Storage only provides the persistence primitives required to execute the resulting fact operation.

---

# 43. Reposting

Reposting is conceptually:

```text
old MovementSet
      ↓
remove old effects
      ↓
generate new MovementSet
      ↓
append new effects
```

Register Storage does not own Reposting semantics.

It provides the primitives required by the higher-level consistency scope.

The implementation must avoid a state in which the old accounting effects have been successfully removed, new effects have only partially been persisted, and the operation is nevertheless reported as successfully completed.

That responsibility belongs to the logical consistency architecture.

---

# 44. Movement Query Independence

Step 3 will define:

```text
MovementQuery
```

and associated semantics.

Step 2 must remain independent of that API.

In particular, this document intentionally does not define:

```python
query_movements(...)
```

or:

```python
find(
    period=...,
    dimensions=...,
    resources=...,
)
```

as persistence methods.

Such methods would incorrectly move Register Query semantics into the persistence boundary.

---

# 45. Candidate Semantic API

The target capability set for Register Storage is conceptually:

```python
class RegisterFactPersistence(Protocol):
    def append(
        self,
        movements: Sequence[Movement],
    ) -> None:
        ...

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> Sequence[Movement]:
        ...

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
        ...

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> Iterable[Movement]:
        ...
```

This is a **semantic target**, not yet the final concrete API.

Exact method names, return types, iterable/sequence guarantees, exception behavior, and provider implementation remain subject to Concrete API Design.

The final implementation must preserve the architectural boundary defined by this document regardless of the concrete method names selected.

---

# 46. Why `get()` Is Not Mandatory

A direct:

```python
get(movement_identity)
```

operation is intentionally not part of the minimum normative contract.

The Phase 7 Vertical Slice does not require direct single-Movement lookup as an architectural prerequisite.

The mandatory capabilities are:

```text
append
find_by_source_document
remove
enumerate
```

Adding `get()` prematurely would provide repository-style capabilities without an established concrete consumer.

If later implementation requires it, the operation can be introduced as a narrow fact lookup without changing the overall architecture.

---

# 47. Why `list()` Is Not Used

A generic:

```python
list(register_identity)
```

name is deliberately avoided in the semantic contract.

The required capability is enumeration of authoritative Register facts for maintenance and reconstruction.

The term:

```text
enumerate
```

makes the architectural purpose explicit and discourages future expansion into a generic query API.

---

# 48. Determinism

Register Storage must not introduce nondeterminism through:

* arbitrary provider ordering;
* unstable serialization;
* runtime object identity;
* storage layout;
* generated semantic Movement identities;
* uncontrolled external state.

Given the same persisted semantic Movement facts, maintenance and subsequent Register computations must be reproducible.

---

# 49. Acceptance of Persisted Facts

A Movement may be persisted only after it has passed the appropriate semantic validation boundary.

Storage does not determine whether a Movement is valid for Posting.

The architecture is:

```text
Movement validation
        ↓
accepted Movement
        ↓
Register Storage
```

Storage is therefore not the primary accounting validation engine.

---

# 50. Separation of Validation

The following responsibilities remain separate.

### Movement Contract

Defines:

* semantic shape;
* immutability;
* identity;
* source document;
* Register;
* dimensions;
* resources;
* accounting time.

### Register Validation

Defines:

* whether a Movement is valid for a particular Register;
* Register-specific dimensions;
* Register-specific resources;
* required accounting time;
* applicable movement types.

### Register Storage

Defines:

* persistence of already accepted facts.

---

# 51. Inventory Implications

For the Phase 7 Inventory Register:

```text
Register
    Inventory

Dimensions
    Product
    Warehouse

Resource
    Quantity

Movement Type
    Income / Expense

Accounting Time
    required for accumulation
```

Register Storage must therefore preserve all information required for later:

* Movement Query;
* totals calculation;
* balance calculation;
* rebuild;
* consistency verification.

---

# 52. Vertical Slice Dependency

The Phase 7 Vertical Slice is:

```text
Goods Receipt
      ↓
Posting
      ↓
Posting Context
      ↓
MovementSet
      ↓
Inventory Movement Validation
      ↓
Register Storage
      ↓
Inventory Totals
      ↓
Inventory Balance Query
```

Step 2 provides the persistence foundation for the middle of this chain.

It does not implement:

* Movement Query;
* Totals Engine;
* Balance Query;
* Register lifecycle;
* Goods Receipt posting.

Those are later steps.

---

# 53. Rebuild Requirement

The final Phase 7 architecture must be able to execute:

```text
Persisted Inventory Movements
        ↓
Rebuild Inventory Totals
        ↓
Persisted Inventory Totals
        ↓
Inventory Balance
```

The result must be semantically equivalent to totals maintained incrementally from the same Movement facts.

Register Storage is responsible only for ensuring that the authoritative Movement facts needed for this process can be recovered completely.

---

# 54. Consistency Requirement

The following invariant must hold at the architecture level:

> Totals are derived from the same authoritative Movement facts that Register Query Services can observe.

The architecture must not permit a hidden second source of accounting truth.

Therefore:

```text
Movement persistence
        ↓
authoritative facts
        ├── Query
        └── Totals rebuild
```

---

# 55. Storage and Query Source Alignment

Movement Query and Totals Rebuild may use different internal execution strategies, but their semantic source must be the same persisted Movement fact set.

This prevents:

```text
Query → Movement Store A
Totals → hidden Store B
```

unless both are explicitly proven to represent the same authoritative fact set.

For Phase 7 the intended model is:

```text
one authoritative Movement fact source
```

---

# 56. No Direct Totals Mutation Through Storage

Register Storage must not expose operations such as:

```python
set_balance(...)
set_total(...)
increment_balance(...)
```

as part of the Movement persistence contract.

Totals maintenance belongs to the Totals Engine.

This prevents the Movement persistence boundary from becoming coupled to one particular derived-state implementation.

---

# 57. Logical Atomicity Boundary

The architecture must explicitly distinguish three levels:

```text
1. Persistence operation
   append / remove

2. Register-level derived-state operation
   totals maintenance

3. Logical accounting consistency scope
   coordinated result of the accounting operation
```

For example:

```text
Repost Scope
    │
    ├── remove old Movements
    ├── append new Movements
    └── update/rebuild applicable totals
```

The scope determines whether these operations form one logical success/failure result.

This is not defined by `RegisterFactPersistence.append()` alone.

---

# 58. Failure Semantics

At the architecture level, failures must be distinguishable as:

### Failure

The operation is known not to have completed successfully.

### Success

The operation completed according to the contract.

### Indeterminate

The implementation cannot establish whether the operation completed.

Indeterminate outcomes must not be silently converted into success.

The higher-level consistency architecture must determine the resulting accounting state and recovery requirements.

---

# 59. Provider Failure Independence

Register Storage must not expose provider-specific failure semantics such as:

```text
SQLIntegrityConstraintViolation
FilesystemWriteError
ORMTransactionError
```

as the public semantic contract.

Provider failures must be translated through the existing persistence abstraction.

---

# 60. Architecture Invariants

The following invariants are normative for Step 2.

### REG-ST-01

Movement is the primary persisted accounting fact.

### REG-ST-02

Totals are derived state.

### REG-ST-03

Movement identity is preserved exactly.

### REG-ST-04

Source document identity is preserved.

### REG-ST-05

Register identity is preserved.

### REG-ST-06

Movement is immutable.

### REG-ST-07

No `update()` operation exists in Register Storage.

### REG-ST-08

Duplicate Movement identities are not silently overwritten.

### REG-ST-09

Register Storage uses the existing Phase 5 persistence architecture through `RegisterFactPersistence`.

### REG-ST-10

No parallel generic repository abstraction is introduced.

### REG-ST-11

`RegisterFactPersistence` is the persistence abstraction boundary between Register Storage and Phase 5 Persistence Architecture.

### REG-ST-12

Source-document lookup is a fact-oriented persistence primitive.

### REG-ST-13

Source-document lookup does not implement Movement Query semantics.

### REG-ST-14

Removal receives Movement identities, not business documents.

### REG-ST-15

Batch removal is a persistence operation, not the global accounting transaction boundary.

### REG-ST-16

Append is a persistence operation, not the global accounting transaction boundary.

### REG-ST-17

Logical accounting atomicity belongs to the higher-level consistency scope.

### REG-ST-18

Persisted Movement facts are available for totals rebuild.

### REG-ST-19

Enumeration is complete for the target Register.

### REG-ST-20

Enumeration is deterministic where its ordering is observable.

### REG-ST-21

Register Query semantics belong to Register Services.

### REG-ST-22

Period filtering belongs to the Query Model.

### REG-ST-23

Dimension filtering belongs to the Query Model.

### REG-ST-24

Grouping and aggregation do not belong to Register Storage.

### REG-ST-25

Balance calculation does not belong to Register Storage.

### REG-ST-26

Turnover calculation does not belong to Register Storage.

### REG-ST-27

Movement resources are preserved without precision loss.

### REG-ST-28

Movement type is preserved.

### REG-ST-29

Movement attributes are preserved.

### REG-ST-30

Accounting time is preserved.

### REG-ST-31

Register-specific requirements may strengthen the universal Movement contract.

### REG-ST-32

Inventory accumulation requires defined accounting time.

### REG-ST-33

Totals are not stored as Movement facts.

### REG-ST-34

Totals are not directly mutated through Register Storage.

### REG-ST-35

Register Storage is provider-independent.

### REG-ST-36

Register Storage uses the existing Phase 5 persistence error model.

### REG-ST-37

Indeterminate persistence outcomes are not silently reported as success.

### REG-ST-38

Register Storage does not own Posting lifecycle semantics.

### REG-ST-39

Register Storage does not own Register event semantics.

### REG-ST-40

`MovementChanged` does not imply in-place Movement mutation.

### REG-ST-41

Rebuild uses persisted Movement facts rather than previous totals.

### REG-ST-42

Movement Query and Totals Rebuild share the same authoritative Movement fact source.

### REG-ST-43

The storage contract does not become a generic query repository.

---

# 61. Acceptance Criteria

Step 2 is architecturally complete when all of the following are true.

### AC-ST-01

The Register Storage layer is explicitly defined as a Register-specific semantic persistence layer.

### AC-ST-02

`RegisterFactPersistence` is explicitly defined as the abstraction boundary between Register Storage and the existing Phase 5 Persistence Architecture.

### AC-ST-03

Register Storage does not access concrete storage providers directly.

### AC-ST-04

No parallel generic persistence architecture is introduced.

### AC-ST-05

Movement is explicitly defined as the primary persisted accounting fact.

### AC-ST-06

Movement immutability is preserved.

### AC-ST-07

No `update()` semantic operation is introduced.

### AC-ST-08

Movement identity is preserved.

### AC-ST-09

Source document identity is preserved.

### AC-ST-10

Register identity is preserved.

### AC-ST-11

Accepted Movements can be appended.

### AC-ST-12

Duplicate Movement identities cannot silently overwrite existing facts.

### AC-ST-13

Existing Movement effects can be identified by source document and Register.

### AC-ST-14

Identified Movement effects can be removed by identity.

### AC-ST-15

Multiple Movement effects can be removed as a batch operation.

### AC-ST-16

Batch persistence operations are not incorrectly presented as the global accounting transaction boundary.

### AC-ST-17

Persisted Movement facts can be enumerated for totals rebuild.

### AC-ST-18

Register Storage does not expose period/dimension/grouping/aggregation query semantics.

### AC-ST-19

Register Query semantics remain owned by Register Services.

### AC-ST-20

Existing Phase 5 persistence error semantics are reused.

### AC-ST-21

Indeterminate persistence outcomes remain distinguishable.

### AC-ST-22

Movement accounting time, dimensions, resources, type, and attributes are preserved.

### AC-ST-23

Inventory-specific accounting-time requirements can be enforced above the universal Movement representation.

### AC-ST-24

Totals remain derived state and are not exposed as Movement persistence operations.

### AC-ST-25

Register Storage remains independent of physical storage technology.

### AC-ST-26

The contract provides all persistence capabilities required by the Phase 7 Vertical Slice without prematurely introducing generic repository or query semantics.

---

# 62. Explicit Non-Goals

Step 2 does not define:

* Movement Query API;
* Balance Query API;
* Turnover Query API;
* Totals Engine;
* Balance calculation;
* Register lifecycle implementation;
* maintenance workflow;
* Posting implementation;
* Unposting business semantics;
* Reposting business semantics;
* distributed transactions;
* replication;
* sharding;
* OLAP;
* reporting;
* valuation;
* ledger behavior;
* period closing;
* multi-register query semantics.

These belong to later architecture steps or future phases.

---

# 63. Architectural Decision

The Phase 7 Register Storage Contract is therefore defined as:

> **Register Storage is the Register-specific semantic persistence layer for immutable accounting Movement facts. It depends on the existing Phase 5 Persistence Architecture through `RegisterFactPersistence`, which forms the abstraction boundary to generic persistence infrastructure. Register Storage provides the minimal capabilities required to persist, identify, remove, and enumerate Register Movement facts without taking ownership of Register Query semantics, Totals semantics, Posting semantics, or the global logical accounting consistency boundary.**

The essential separation is:

```text
                  ACCOUNTING OPERATION
                           │
                           ▼
                Logical Consistency Scope
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Register Storage              Totals Engine
             │                           │
             ▼                           ▼
   RegisterFactPersistence        Totals Persistence
             │
             ▼
   Phase 5 Persistence Architecture
             │
             ▼
       Storage Provider
```

Read-side:

```text
Persisted Movement Facts
          │
          ▼
   Register Services
          │
     ┌────┼────┐
     ▼    ▼    ▼
 Movement Turnover Balance
  Query    Query   Query
```

The architectural dependency direction is:

```text
Register Architecture
        │
        ▼
Register Storage
        │
        ▼
RegisterFactPersistence
        │
        ▼
Phase 5 Persistence Architecture
        │
        ▼
Storage Provider
```

Register Storage remains deliberately narrow.

Its responsibility is to make authoritative Movement facts durable and recoverable through the existing persistence architecture.

It does not become the owner of the accounting semantics that consume those facts.

---

# 64. Transition to Step 3

With this contract established, Step 3 can define the semantic Movement Query Contract.

Step 3 should establish:

* `MovementQuery`;
* Register selection;
* period semantics;
* dimension filters;
* partial dimension matching;
* resource selection;
* deterministic result ordering;
* temporal/as-of semantics;
* query result semantics;
* interaction with Register Storage without leaking query semantics into persistence.

The key architectural boundary entering Step 3 is:

```text
RegisterFactPersistence
        │
        │ authoritative Movement facts
        ▼
Register Services
        │
        ▼
Movement Query Model
```

This boundary must remain intact throughout Phase 7.
