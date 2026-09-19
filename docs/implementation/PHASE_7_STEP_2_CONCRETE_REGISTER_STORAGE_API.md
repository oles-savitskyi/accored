# PHASE 7 — STEP 2

# CONCRETE REGISTER STORAGE API

**Status:** Architecture Approved — Concrete API
**Phase:** Phase 7 — Register Implementation
**Step:** 2 — Register Storage Contract
**Depends on:** Phase 5 Persistence Architecture, Phase 6 Movement Contract, Phase 7 Step 1 Architecture Definition
**Purpose:** Fix the concrete Python API of Register Fact Persistence.

---

## 1. Final API

The Phase 7 concrete persistence contract is:

```python
from collections.abc import Sequence
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.registers import Movement


class RegisterFactPersistence(Protocol):
    """Persistence boundary for authoritative Register Movement facts."""

    def append(self, movements: Sequence[Movement]) -> None:
        """Persist accepted Movement facts."""

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        """Return persisted movements for a Register and source document."""

    def remove(self, movement_identities: Sequence[Identifier]) -> None:
        """Remove persisted Movement facts by semantic Movement identity."""

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        """Return all persisted Movement facts for a Register."""
```

This is the **concrete Phase 7 API**.

No `update()` method is defined.

No generic `query()` method is defined.

No generic `get()` method is required.

No generic `list()` method is defined.

---

## 2. API Ownership

The API belongs to the existing:

```text
accore.platform.persistence.RegisterFactPersistence
```

boundary.

It does not introduce:

```text
RegisterRepository
MovementRepository
AccountingRepository
RegisterStorageRepository
```

or another persistence abstraction.

The dependency remains:

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

`RegisterFactPersistence` is therefore the existing persistence abstraction extended from its Phase 5 append-only placeholder into the concrete Register fact persistence contract required by Phase 7.

---

## 3. Actual Movement Type

The placeholder:

```python
Movement = Any
```

must be removed.

The persistence contract must use the actual Register domain type:

```python
from accore.platform.registers import Movement
```

The contract therefore persists the same semantic `Movement` object defined by the Register Architecture.

There is no:

```python
PersistentMovement
```

in Phase 7.

---

## 4. `append`

### Signature

```python
def append(
    self,
    movements: Sequence[Movement],
) -> None:
    ...
```

### Semantics

`append()` persists the supplied accepted Movement facts.

It must preserve:

* `identity`;
* `source_document_identity`;
* `register_identity`;
* `movement_type`;
* `dimensions`;
* `resources`;
* `attributes`;
* `accounting_time`.

### Duplicate identity

If a Movement with the same semantic identity already exists, the implementation must not silently overwrite it.

The appropriate existing Phase 5 persistence error must be raised.

The expected semantic category is:

```python
PersistenceAlreadyExistsError
```

or, where the concrete provider detects a different persistence conflict:

```python
PersistenceConflictError
```

The provider-specific error must not leak through the public API.

### Atomicity

`append()` is a persistence operation.

It is **not** the global accounting transaction boundary.

The higher-level Posting/Persistence Scope coordinates:

```text
old accounting effects
+
new Movement facts
+
Totals
```

when they must form one logical accounting result.

---

## 5. `find_by_source_document`

### Signature

```python
def find_by_source_document(
    self,
    register_identity: Identifier,
    source_document_identity: Identifier,
) -> tuple[Movement, ...]:
    ...
```

### Purpose

This method identifies persisted accounting effects belonging to:

```text
Register
+
source document
```

It is required by:

* Unpost;
* Repost;
* accounting-effect replacement;
* consistency verification.

### Important boundary

This is a **fact lookup**, not a general query.

It does not accept:

```python
period=...
dimensions=...
resources=...
group_by=...
order_by=...
```

It therefore does not belong to the Movement Query API.

### Result

The result is an immutable snapshot:

```python
tuple[Movement, ...]
```

rather than a mutable storage-owned collection.

An empty result is represented by:

```python
()
```

and is not an error.

---

## 6. `remove`

### Signature

```python
def remove(
    self,
    movement_identities: Sequence[Identifier],
) -> None:
    ...
```

### Purpose

Removes persisted Movement facts identified by their semantic identities.

The method deliberately accepts:

```python
Sequence[Identifier]
```

rather than:

```python
Sequence[Movement]
```

because the operation is removal of existing facts, not modification of Movement objects.

### Responsibility boundary

The caller determines which Movements must be removed:

```text
Register / Posting orchestration
        │
        ▼
find_by_source_document(...)
        │
        ▼
Movement identities
        │
        ▼
remove(...)
```

Register Storage does not decide:

* whether a document is posted;
* whether reposting is valid;
* whether a Movement should be removed;
* what business operation caused the removal.

### Empty input

For:

```python
remove(())
```

the operation is a successful no-op.

No provider interaction is required.

### Missing identity

For a non-empty request containing an identity that does not exist, the concrete implementation must follow the Phase 5 persistence semantics.

Phase 7 does not silently convert an unexpected missing fact into success.

The exact behavior is therefore:

```text
known existence requirement
        ↓
missing fact
        ↓
PersistenceNotFoundError
```

unless a future higher-level contract explicitly defines idempotent removal.

---

## 7. Batch Removal

The API deliberately supports:

```python
remove(
    [movement_a, movement_b, movement_c]
)
```

because a single accounting operation may produce multiple Movement facts.

However:

```python
remove(...)
```

does not define the global accounting transaction boundary.

The distinction is:

```text
remove([A, B, C])
        │
        ▼
one persistence operation
```

versus:

```text
Repost Consistency Scope
        │
        ├── remove old movements
        ├── append new movements
        └── maintain totals
```

The second responsibility belongs to the higher-level consistency architecture.

---

## 8. `enumerate`

### Signature

```python
def enumerate(
    self,
    register_identity: Identifier,
) -> tuple[Movement, ...]:
    ...
```

### Purpose

Returns the complete authoritative Movement fact set for one Register.

The primary consumers are:

* Totals rebuild;
* consistency verification;
* recovery;
* maintenance.

### Why `enumerate`

The name is intentional.

It communicates:

> enumerate authoritative persisted facts

rather than:

> execute an arbitrary Register query.

Therefore this method must not grow parameters such as:

```python
period
dimensions
resources
group_by
order_by
limit
offset
```

Those belong to Step 3 Movement Query.

### Result

The result is:

```python
tuple[Movement, ...]
```

This provides a deterministic immutable snapshot for maintenance operations.

### Completeness

For a given Register:

```python
persistence.enumerate(register_identity)
```

must contain every persisted Movement belonging to that Register.

The result is the authoritative source for totals rebuild.

---

## 9. Ordering

The concrete API returns a `tuple`, but tuple ordering must not accidentally become Query semantics.

The implementation must establish deterministic ordering.

Recommended Phase 7 ordering:

```text
Movement.identity ascending
```

This provides:

* reproducible tests;
* deterministic rebuild input;
* provider-independent observable behavior;
* stable maintenance behavior.

The ordering is an implementation contract of fact enumeration, not a user-facing query-ordering mechanism.

Step 3 may define a different semantic ordering for Movement Query results.

---

## 10. No `get()`

The following is intentionally absent:

```python
def get(
    self,
    movement_identity: Identifier,
) -> Movement:
    ...
```

It is not required by the Phase 7 Vertical Slice.

The current required operations are:

```text
append
find_by_source_document
remove
enumerate
```

If a later concrete consumer requires direct lookup by Movement identity, it can be added as a narrow fact primitive after demonstrating the requirement.

It must not be introduced merely to imitate CRUD repository conventions.

---

## 11. No `update()`

The API must never contain:

```python
update(...)
```

Movement is immutable.

Accounting change is represented through lifecycle operations such as:

```text
Unpost
Repost
Replacement of accounting effects
```

Conceptually:

```text
old Movement facts
        ↓
remove
        ↓
new Movement facts
        ↓
append
```

There is no in-place mutation of an existing Movement.

---

## 12. No Generic Query API

The API must not contain:

```python
query(...)
search(...)
find(...)
list(...)
```

as generic query abstractions.

The only lookup method is:

```python
find_by_source_document(...)
```

because it is a specific fact-persistence primitive required by accounting lifecycle operations.

The Register Query Model belongs above persistence:

```text
RegisterFactPersistence
        │
        ▼
authoritative Movement facts
        │
        ▼
Register Query Service
        │
        ▼
MovementQuery
```

---

## 13. Return Type Decision

The Phase 7 API uses:

```python
tuple[Movement, ...]
```

for fact collections.

This is deliberate.

It provides:

* immutable result snapshots;
* deterministic comparison in tests;
* no exposure of provider-owned mutable collections;
* clear separation from lazy query execution;
* simple semantics for the initial Phase 7 implementation.

`append()` and `remove()` return:

```python
None
```

because their success is represented by normal completion and their failure by the existing persistence exception hierarchy.

No result object is introduced in Phase 7.

---

## 14. Exception Contract

The API reuses the existing Phase 5 persistence errors.

### `append`

Potential failures:

```python
PersistenceAlreadyExistsError
PersistenceConflictError
PersistenceIntegrityError
PersistenceUnsupportedError
PersistenceFailure
PersistenceIndeterminateError
```

### `find_by_source_document`

Potential failures:

```python
PersistenceUnsupportedError
PersistenceFailure
PersistenceIndeterminateError
```

An empty result is not an exception.

### `remove`

Potential failures:

```python
PersistenceNotFoundError
PersistenceConflictError
PersistenceIntegrityError
PersistenceUnsupportedError
PersistenceFailure
PersistenceIndeterminateError
```

### `enumerate`

Potential failures:

```python
PersistenceUnsupportedError
PersistenceFailure
PersistenceIndeterminateError
```

No new Register-specific persistence exception hierarchy is introduced.

---

## 15. Public Module API

`accore.platform.persistence.__init__` continues to expose:

```python
from accore.platform.persistence import RegisterFactPersistence
```

The implementation module becomes:

```text
src/accore/platform/persistence/facts.py
```

with:

```python
from collections.abc import Sequence
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.registers import Movement


class RegisterFactPersistence(Protocol):
    """Persistence boundary for authoritative Register Movement facts."""

    def append(self, movements: Sequence[Movement]) -> None:
        """Persist accepted Movement facts."""

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        """Return persisted movements for a Register and source document."""

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
        """Remove persisted Movement facts by semantic identity."""

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        """Return all persisted Movement facts for a Register."""
```

---

## 16. Dependency Direction

The concrete imports must remain:

```text
persistence
    │
    ▼
registers.Movement
```

and not:

```text
registers
    │
    ▼
persistence
```

The Movement domain type is therefore defined by the Register subsystem.

Persistence consumes it.

This prevents the persistence layer from becoming the owner of accounting fact semantics.

---

## 17. In-Memory Reference Implementation

For Phase 7 tests, the minimal reference implementation can be:

```python
class InMemoryRegisterFactPersistence:
    def __init__(self) -> None:
        self._movements: dict[Identifier, Movement] = {}

    def append(self, movements: Sequence[Movement]) -> None:
        for movement in movements:
            if movement.identity in self._movements:
                raise PersistenceAlreadyExistsError(
                    f"Movement already exists: {movement.identity}"
                )

        for movement in movements:
            self._movements[movement.identity] = movement

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            sorted(
                (
                    movement
                    for movement in self._movements.values()
                    if movement.register_identity == register_identity
                    and movement.source_document_identity
                    == source_document_identity
                ),
                key=lambda movement: movement.identity,
            )
        )

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
        identities = tuple(movement_identities)

        missing = [
            identity
            for identity in identities
            if identity not in self._movements
        ]

        if missing:
            raise PersistenceNotFoundError(
                f"Movement not found: {missing[0]}"
            )

        for identity in identities:
            del self._movements[identity]

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            sorted(
                (
                    movement
                    for movement in self._movements.values()
                    if movement.register_identity == register_identity
                ),
                key=lambda movement: movement.identity,
            )
        )
```

This is a **reference implementation for Phase 7 tests**, not a requirement that the final storage provider use a dictionary.

---

## 18. Important Atomicity Detail in the Reference Implementation

The reference `append()` validates all duplicate identities before inserting any Movement:

```python
for movement in movements:
    if movement.identity in self._movements:
        ...
```

This prevents an obvious partial mutation in the in-memory implementation.

However, this does **not** change the architectural statement that:

> `append()` is not the global accounting consistency boundary.

The higher-level consistency scope remains responsible for coordinating:

```text
Movement persistence
+
Totals
+
Posting state
```

when joint atomicity is required.

---

## 19. Phase 7 Vertical Slice Compatibility

The concrete API is sufficient for:

```text
Goods Receipt
      ↓
Posting
      ↓
MovementSet
      ↓
Movement validation
      ↓
append(...)
      ↓
enumerate(...)
      ↓
Totals rebuild
      ↓
Balance
```

and for future unposting/reposting:

```text
source document
      ↓
find_by_source_document(...)
      ↓
Movement identities
      ↓
remove(...)
```

No additional persistence API is required for the planned Phase 7 Vertical Slice.

---

## 20. API Invariants

### API-01

`RegisterFactPersistence` uses the real `Movement` type.

### API-02

`Movement` remains the persisted accounting fact.

### API-03

Movement identity is semantic and preserved.

### API-04

`append()` persists facts and does not mutate existing facts.

### API-05

Duplicate Movement identity is never silently overwritten.

### API-06

`find_by_source_document()` is Register/source-document fact lookup.

### API-07

`find_by_source_document()` is not a general query API.

### API-08

`remove()` accepts Movement identities.

### API-09

`remove()` does not accept business documents or Posting commands.

### API-10

`remove()` may operate on a batch.

### API-11

Batch removal is not the global accounting transaction boundary.

### API-12

`enumerate()` returns the complete Movement fact set for a Register.

### API-13

`enumerate()` is a maintenance/fact primitive, not a Query API.

### API-14

Collection results are immutable tuples.

### API-15

Fact enumeration is deterministic.

### API-16

No `update()` operation exists.

### API-17

No generic `query()` operation exists.

### API-18

No generic `list()` operation exists.

### API-19

No mandatory `get()` operation exists.

### API-20

Existing Phase 5 persistence errors are reused.

### API-21

Provider-specific errors do not cross the semantic API boundary.

### API-22

Indeterminate persistence outcomes remain distinguishable.

### API-23

Register Storage does not own Totals.

### API-24

Register Storage does not own Movement Query semantics.

### API-25

Register Storage does not own Posting lifecycle semantics.

---

## 21. Final Concrete Contract

The final Phase 7 API is therefore exactly:

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
    ) -> tuple[Movement, ...]:
        ...

    def remove(
        self,
        movement_identities: Sequence[Identifier],
    ) -> None:
        ...

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        ...
```

This is the API to implement.

No additional Register Storage methods should be added during the implementation of Step 2 without an explicit architectural review.

---

## 22. Implementation Boundary

Implementation of this API belongs to the next concrete implementation task.

The implementation must:

1. replace the `Movement = Any` placeholder;
2. update `RegisterFactPersistence`;
3. update the persistence public API if required;
4. update existing tests that currently assert the old append-only shape;
5. add tests for:

   * append;
   * duplicate identity;
   * source-document lookup;
   * empty source-document lookup;
   * batch removal;
   * missing removal;
   * Register-scoped enumeration;
   * deterministic enumeration;
   * preservation of Movement identity and semantic fields;
6. keep the working tree and existing Phase 5 tests green.

After this API is implemented and validated, Step 3 can define `MovementQuery` on top of this boundary.

---

# Architectural Decision

**The Phase 7 concrete Register Storage API consists of four fact-oriented operations:**

```text
append
find_by_source_document
remove
enumerate
```

This is intentionally the smallest API that supports the planned Vertical Slice and Register lifecycle without turning persistence into a generic repository or query engine.

The resulting boundary is:

```text
                Register Services
                       │
          ┌────────────┴────────────┐
          │                         │
     Movement Query           Totals Engine
          │                         │
          └────────────┬────────────┘
                       │
              authoritative facts
                       │
                       ▼
             RegisterFactPersistence
                       │
                       ▼
          Phase 5 Persistence Layer
                       │
                       ▼
                Storage Provider
```

**Concrete API is now fixed for Phase 7 Step 2.**
