# Phase 5 — Storage Provider Boundary

**Status:** Architecture Approved / Contract v1 Defined
**Phase:** 5
**Step:** 4
**Artifact:** Storage Provider Boundary
**Scope:** Architecture / Contract Boundary

---

## 1. Purpose

This document defines the architectural boundary between the AcCore platform and
physical storage implementations.

The purpose of the boundary is to ensure that platform and domain-facing
components depend on a stable storage contract rather than on a concrete
filesystem, database, object store, or other persistence mechanism.

The Storage Provider is an infrastructure capability.

It is not responsible for domain semantics, metadata lifecycle, configuration
activation, posting, register semantics, valuation, or business rules.

---

## 2. Architectural Context

AcCore uses a layered, metadata-driven architecture in which runtime components
must remain independent from infrastructure implementation details.

The storage boundary exists between:

```text
Platform / Runtime / Domain-facing Consumers
                    │
                    ▼
          Storage Provider Contract
                    │
                    ▼
        Concrete Storage Provider
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Filesystem  Database  Object Store
```

Consumers above the boundary must not depend directly on any concrete storage
technology.

Concrete providers below the boundary may use any appropriate persistence
technology as long as they satisfy the provider contract.

---

## 3. Boundary Definition

The Storage Provider Boundary consists of:

1. a stable provider interface;
2. storage-neutral value types;
3. provider-neutral errors;
4. defined provider semantics;
5. explicit lifecycle and ownership rules;
6. contract tests applicable to every provider implementation.

The boundary does **not** include:

* database-specific APIs;
* filesystem-specific APIs;
* ORM models;
* SQL queries;
* object-store-specific APIs;
* serialization formats tied to a particular backend;
* transaction implementation details;
* connection management details;
* domain-specific repository semantics.

---

## 4. Responsibility of the Storage Provider

A Storage Provider is responsible for physically storing and retrieving opaque
application data.

The provider may:

* persist data;
* retrieve data;
* determine whether data exists;
* remove data according to the provider contract;
* provide provider-specific durability and consistency guarantees.

The provider must not:

* interpret domain meaning;
* validate metadata definitions;
* activate configurations;
* perform posting;
* calculate accounting values;
* enforce business rules;
* construct runtime domain objects;
* resolve metadata;
* decide application-level lifecycle transitions.

The provider stores data.

The caller owns the meaning of that data.

---

## 5. Opaque Data Principle

The Storage Provider treats stored payloads as opaque data.

The provider contract does not require knowledge of:

* metadata definitions;
* runtime object classes;
* accounting documents;
* registers;
* configuration objects;
* business entities.

The intended flow is:

```text
Application object
       │
       ▼
 serialization / encoding
       │
       ▼
 opaque storage payload
       │
       ▼
 Storage Provider
```

On retrieval:

```text
Storage Provider
       │
       ▼
 opaque storage payload
       │
       ▼
 deserialization / decoding
       │
       ▼
 Application object
```

The provider does not interpret the domain meaning of the payload.

---

## 6. Storage Identity and Addressing

Storage identity is explicitly separated from domain identity.

A `StorageKey` identifies a stored payload within the Storage Provider.

It does not automatically imply:

* a domain object identifier;
* a metadata identifier;
* a configuration identifier;
* a register identifier.

The conceptual relationship is:

```text
Domain Identity
      │
      │ application-level mapping
      ▼
StorageKey
      │
      ▼
Storage Provider
```

A provider must not derive domain semantics from a storage key.

### 6.1 StorageKey is not a Path

`StorageKey` represents a logical storage address.

It must not be named or modeled as a filesystem path.

For example:

```text
StorageKey("abc")
```

may map to:

```text
filesystem → /storage/abc
database   → row with key "abc"
object     → object key "abc"
```

The mapping is the responsibility of the concrete provider.

The public contract remains storage-neutral.

---

## 7. Storage Payload

The v1 Storage Provider contract uses:

```python
bytes
```

as the payload type.

The provider therefore operates on:

```text
StorageKey + bytes
```

rather than on:

* `dict`;
* JSON objects;
* domain objects;
* ORM models;
* arbitrary Python objects;
* provider-specific records.

This keeps serialization independent from physical storage.

Serialization and deserialization remain above the Storage Provider Boundary.

---

## 8. Provider Contract v1

The initial provider contract is intentionally minimal.

The contract consists of four operations:

```text
put
get
exists
delete
```

The Python contract is:

```python
class StorageProvider(Protocol):
    def put(self, key: StorageKey, payload: bytes) -> None:
        ...

    def get(self, key: StorageKey) -> bytes:
        ...

    def exists(self, key: StorageKey) -> bool:
        ...

    def delete(self, key: StorageKey) -> None:
        ...
```

The contract is deliberately expressed in terms of storage-neutral types.

---

## 8.1. Contract Test Implementation

The Storage Provider v1 contract is now executable through reusable contract tests.

The contract is verified against a test-only `InMemoryStorageProvider` implementation located under:

    tests/contracts/storage/

The test adapter is intentionally kept outside `src/accore/platform/storage/`.
It exists only to verify the provider contract and does not represent a production
storage backend.

### Contract Test Coverage

The contract currently verifies:

- `put()` creates a new payload;
- `put()` replaces an existing payload;
- `get()` returns the stored payload unchanged;
- `get()` raises `StorageNotFoundError` for a missing key;
- `exists()` returns `False` for a missing key;
- `exists()` returns `True` after `put()`;
- `exists()` returns `False` after `delete()`;
- `delete()` removes an existing payload;
- `delete()` raises `StorageNotFoundError` for a missing key;
- arbitrary binary payloads are preserved unchanged.

The contract currently contains 12 tests.

### Contract Boundary

The intended dependency direction is:

    StorageProvider Protocol
            │
            ▼
    Reusable Contract Tests
            │
            ▼
    Provider Implementations

The contract tests are implementation-independent. Any future concrete
`StorageProvider` implementation must satisfy the same behavioral contract.

The current `InMemoryStorageProvider` is a test adapter only and must not be
considered part of the production storage architecture.

---

## 8.2. Step 4A Quality Gate

**Status: CLOSED**

Storage Provider Boundary v1 and its executable contract are validated.

Validation results:

- Storage contract tests: **18 passed**
- Full test suite: **349 passed**
- `ruff check .`: **PASS**
- `black --check .`: **PASS**
- `mypy src`: **PASS**

At this checkpoint, the Storage Provider boundary is considered stable enough
for concrete provider implementation.

No production storage backend is selected or implemented as part of Step 4A.

---

## 8.4. Step 4B — Filesystem Storage Provider v1 Contract

**Status: CLOSED**

Implemented and validated:

- `FilesystemStorageProvider`
- filesystem-backed implementation of `StorageProvider`
- provider-neutral `StorageKey` mapping
- root-contained relative key resolution
- raw `bytes` payload preservation
- atomic file replacement for `put`
- `StorageNotFoundError` translation for missing `get` / `delete`
- `StorageOperationError` translation for filesystem failures
- reusable storage contract executed against both in-memory and filesystem providers
- provider-specific filesystem tests

### 4B.1 Objective

Step 4B introduces the first concrete production implementation of the `StorageProvider` boundary.

The selected provider is a filesystem-backed implementation:

```text
StorageProvider
      │
      ▼
FilesystemStorageProvider
      │
      ▼
Local filesystem
```

The purpose of this step is to prove that the storage boundary is implementable by a real provider without leaking provider-specific concerns into the platform storage contract.

The filesystem provider is an infrastructure adapter. It does not redefine the `StorageProvider` contract and does not introduce repository, serialization, database, or domain-level semantics.

---

### 4B.2 Provider Role

`FilesystemStorageProvider` implements the existing:

```python
class StorageProvider(Protocol):
    def put(self, key: StorageKey, payload: bytes) -> None: ...
    def get(self, key: StorageKey) -> bytes: ...
    def exists(self, key: StorageKey) -> bool: ...
    def delete(self, key: StorageKey) -> None: ...
```

The provider is responsible for translating a logical `StorageKey` into a provider-specific filesystem location.

The architectural boundary is therefore:

```text
StorageKey
    │
    │ logical storage address
    ▼
FilesystemStorageProvider
    │
    │ provider-specific key mapping
    ▼
Filesystem path
    │
    ▼
Filesystem
```

`StorageKey` remains storage-neutral.

The filesystem provider must not redefine `StorageKey` as a filesystem path.

---

### 4B.3 Root Directory

The provider is configured with a filesystem root directory:

```python
FilesystemStorageProvider(root: Path)
```

All provider-managed data must remain below this root.

The root directory represents the physical storage boundary owned by the provider.

The provider must not use arbitrary filesystem locations outside the configured root as a consequence of a normal storage operation.

Parent directories required for a stored key are created automatically by `put()`.

---

### 4B.4 Logical Key Mapping

`StorageKey.value` is a logical storage address.

The filesystem provider maps this logical address to a relative filesystem location.

For example:

```text
StorageKey("objects/001")
        │
        ▼
<root>/objects/001
```

The mapping is provider-specific and must not become part of the `StorageKey` abstraction.

The provider must reject keys that would escape the configured storage root.

At minimum:

* absolute filesystem paths are rejected;
* path traversal using `..` is rejected.

Filesystem-specific key validation belongs to `FilesystemStorageProvider`, not to the provider-neutral `StorageKey`.

---

### 4B.5 Payload Semantics

The filesystem provider stores payloads as opaque bytes.

```python
put(key, payload: bytes)
```

must persist the exact byte sequence supplied by the caller.

`get()` must return the exact byte sequence previously stored.

The provider must not:

* serialize payloads;
* deserialize payloads;
* interpret payload contents;
* convert payloads to text;
* impose JSON, pickle, or other format requirements.

Examples of valid payloads include:

```text
b""
b"hello"
binary data
arbitrary byte sequences
```

---

### 4B.6 Put Semantics

`put()` has upsert semantics.

If the key does not exist:

```text
put(key, payload)
        ↓
create
```

If the key already exists:

```text
put(key, new_payload)
        ↓
replace existing payload
```

No `StorageAlreadyExistsError` is introduced.

The provider should perform replacement in a way that avoids exposing a partially written payload to readers.

For the filesystem implementation, the preferred v1 strategy is:

```text
write temporary file
        │
        ▼
atomic replace
        │
        ▼
target file
```

The temporary file should be created within the same filesystem/storage area so that the final replacement can use filesystem atomic replacement semantics.

---

### 4B.7 Get Semantics

For an existing key:

```python
get(key) -> bytes
```

returns the stored payload.

For a missing key:

```python
get(key)
```

must raise:

```python
StorageNotFoundError
```

The provider must not expose the underlying `FileNotFoundError` as part of its public storage contract.

---

### 4B.8 Exists Semantics

For an existing key:

```python
exists(key) -> True
```

For a missing key:

```python
exists(key) -> False
```

`exists()` does not raise `StorageNotFoundError` for a missing key.

Filesystem failures other than normal absence are provider operation failures and must be translated into the public storage error hierarchy.

---

### 4B.9 Delete Semantics

For an existing key:

```python
delete(key)
```

removes the stored payload successfully.

For a missing key:

```python
delete(key)
```

must raise:

```python
StorageNotFoundError
```

The provider must not expose the underlying `FileNotFoundError`.

---

### 4B.10 Concrete Error Contract

`FilesystemStorageProvider` must expose only the public storage error hierarchy defined by the `StorageProvider` boundary.

The provider must never expose raw filesystem exceptions as part of its public API.

#### Operation-level contract

| Operation  | Condition                             | Required result              |
| ---------- | ------------------------------------- | ---------------------------- |
| `put()`    | target does not exist                 | create and return `None`     |
| `put()`    | target exists                         | replace and return `None`    |
| `put()`    | invalid filesystem key                | `StorageOperationError`      |
| `put()`    | filesystem failure                    | `StorageOperationError`      |
| `get()`    | target exists                         | return exact `bytes` payload |
| `get()`    | target does not exist                 | `StorageNotFoundError`       |
| `get()`    | filesystem failure other than absence | `StorageOperationError`      |
| `exists()` | target exists                         | `True`                       |
| `exists()` | target does not exist                 | `False`                      |
| `exists()` | filesystem failure other than absence | `StorageOperationError`      |
| `delete()` | target exists                         | delete and return `None`     |
| `delete()` | target does not exist                 | `StorageNotFoundError`       |
| `delete()` | filesystem failure other than absence | `StorageOperationError`      |

#### Error hierarchy

```text
StorageError
├── StorageNotFoundError
└── StorageOperationError
```

Only these exceptions are part of the public storage contract.

---

#### `StorageNotFoundError`

`StorageNotFoundError` means that the requested logical storage object does not exist.

It is raised only by operations whose contract explicitly defines missing data as an error:

```text
get()
delete()
```

Therefore:

```python
provider.get(missing_key)
# → StorageNotFoundError

provider.delete(missing_key)
# → StorageNotFoundError

provider.exists(missing_key)
# → False
```

`StorageNotFoundError` must not be used for permission failures, invalid keys, I/O failures, or other infrastructure errors.

---

#### `StorageOperationError`

`StorageOperationError` represents a failure to perform a storage operation for a reason other than normal object absence.

Examples include:

* permission denied;
* I/O failure;
* inability to create a directory;
* inability to create or replace a file;
* invalid filesystem-specific key mapping;
* unexpected filesystem error;
* other provider-level operational failures.

For example:

```text
PermissionError
OSError
invalid provider-specific key
        │
        ▼
StorageOperationError
```

The original underlying exception should be preserved as the exception cause where applicable:

```python
raise StorageOperationError("Storage operation failed") from exc
```

This allows infrastructure diagnostics without leaking backend-specific exception types through the public contract.

---

#### Missing-vs-failure distinction

The provider must distinguish **normal absence** from **failure to determine or perform the operation**.

```text
                    filesystem result
                           │
              ┌────────────┴────────────┐
              │                         │
        object absent             other failure
              │                         │
              ▼                         ▼
   operation-specific             StorageOperationError
       semantics
       │
       ├── get/delete → StorageNotFoundError
       └── exists      → False
```

In particular, `exists()` must not silently convert arbitrary filesystem failures into `False`.

For example, a permission error while inspecting the storage location is an operational failure:

```python
provider.exists(key)
# → StorageOperationError
```

not:

```python
False
```

---

#### Exception Leakage Prohibition

The following backend-specific exceptions must not escape the public `StorageProvider` API:

```text
FileNotFoundError
PermissionError
IsADirectoryError
NotADirectoryError
OSError
```

They may be used internally to determine the appropriate storage-level result, but must be translated before crossing the provider boundary.

The public consumer must therefore be able to operate against any `StorageProvider` implementation without depending on filesystem-specific exception types.

---

#### Error Messages

Error messages are diagnostic information and are not part of the stable semantic contract.

Consumers must branch on exception type, not on message text.

The provider may include useful context such as the logical storage key or underlying operation, provided that doing so does not expose sensitive filesystem information unnecessarily.

The stable contract is:

```text
exception type + operation semantics
```

not:

```text
exception message text
```

---

#### Error Contract Invariant

**SP-INV-26 — Concrete Error Translation**

`FilesystemStorageProvider` must translate filesystem-specific failures into the public storage error hierarchy and must preserve the semantic distinction between object absence and operational failure.

Consequently:

```text
normal missing object
        ≠
storage operation failure
```

and no raw backend exception may become part of the `StorageProvider` public contract.

---

### 4B.11 No Additional Storage Semantics

Step 4B does not introduce additional storage guarantees.

The filesystem provider must not introduce:

* transactions;
* locking;
* compare-and-swap;
* versioning;
* optimistic concurrency;
* TTL;
* caching;
* checksums;
* compression;
* serialization;
* repositories;
* ORM abstractions;
* database semantics.

These concerns remain outside the v1 storage provider boundary.

---

### 4B.12 Contract Test Reuse

The filesystem provider must satisfy the same reusable storage contract tests established in Step 4A.

The contract is therefore validated independently of the provider implementation:

```text
                    StorageProvider Contract
                             │
                ┌────────────┴────────────┐
                │                         │
       InMemoryStorageProvider   FilesystemStorageProvider
            test-only                  production
                │                         │
                └────────────┬────────────┘
                             │
                    same contract tests
```

The existing contract coverage includes:

1. `put()` followed by `get()`;
2. replacement through `put()`;
3. missing `get()`;
4. missing `exists()`;
5. existence after `put()`;
6. existence after `delete()`;
7. successful `delete()`;
8. missing `delete()`;
9. empty payload;
10. textual byte payload;
11. arbitrary binary payload;
12. full byte-range payload.

The filesystem provider must pass these tests without modifying the provider-neutral contract.

---

### 4B.13 Public API

The concrete provider is an infrastructure implementation of the existing storage boundary.

The intended production structure is:

```text
src/accore/platform/storage/
├── __init__.py
├── key.py
├── errors.py
├── provider.py
└── filesystem.py
```

The provider implementation may depend on:

* `StorageKey`;
* `StorageProvider`;
* public storage exceptions;
* Python standard-library filesystem facilities.

It must not introduce dependencies from the storage infrastructure layer into higher-level domain or application abstractions.

---

### 4B.14 Architectural Invariants

Step 4B preserves the following invariants:

**SP-INV-16 — Provider Boundary Preservation**

`FilesystemStorageProvider` implements `StorageProvider`; it does not redefine the contract.

**SP-INV-17 — Logical Key Preservation**

`StorageKey` remains a logical, storage-neutral address.

**SP-INV-18 — Root Containment**

Filesystem storage operations remain within the configured provider root.

**SP-INV-19 — Opaque Payload**

The provider stores and returns payloads as exact `bytes`.

**SP-INV-20 — Upsert Semantics**

`put()` creates or replaces the payload associated with a key.

**SP-INV-21 — Missing Object Semantics**

Missing `get()` and `delete()` operations raise `StorageNotFoundError`.

**SP-INV-22 — Error Boundary**

Underlying filesystem failures are translated into the public storage error hierarchy.

**SP-INV-23 — Contract Reuse**

The same storage contract tests validate both test and production provider implementations.

**SP-INV-24 — No Domain Leakage**

The filesystem provider contains no repository, domain-object, serialization, or business semantics.

**SP-INV-25 — Provider Replaceability**

Higher-level consumers depend on `StorageProvider`, not on filesystem-specific implementation details.

---

### Step 4B Quality Gate

**Status: CLOSED**

Validation completed:

- Storage contract tests: **24 passed**
- Filesystem provider unit tests: **47 passed**
- Combined storage tests: **71 passed**
- Full test suite: **349 passed**
- `ruff check .`: **PASS**
- `black --check .`: **PASS**
- `mypy src`: **PASS**

The `StorageProvider` contract is now validated against two independent implementations:

1. `InMemoryStorageProvider`
2. `FilesystemStorageProvider`

This establishes the first concrete production storage provider while preserving the provider-neutral storage boundary.

---

### 4B.15 Scope Boundary

Step 4B proves the first concrete storage backend.

It does not select the final persistence technology for the complete accounting platform.

The filesystem provider is intentionally a minimal production adapter that demonstrates:

```text
logical storage contract
        ↓
concrete infrastructure implementation
        ↓
real persistent bytes
```

Future providers may implement the same `StorageProvider` boundary without requiring changes to higher-level consumers.

Backend selection beyond this first provider remains a separate architectural decision.


## 9. StorageKey v1

`StorageKey` is an immutable value object representing a logical storage
address.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class StorageKey:
    value: str
```

### 9.1 Validation

The v1 contract requires a non-empty storage key.

The following values are invalid:

```text
""
"   "
```

The v1 contract does not impose a particular key format.

A key is not required to be:

* a ULID;
* a UUID;
* a filesystem path;
* a database identifier;
* an object-store path.

The format remains storage-neutral.

---

## 10. `put` Semantics

`put` has **upsert semantics**.

```text
put(existing key, payload)
    → replace existing payload

put(missing key, payload)
    → create payload
```

The operation therefore does not distinguish between create and replace.

The initial contract does not define conditional writes or compare-and-swap
behavior.

`put` does not imply any concurrency guarantee beyond the guarantees explicitly
provided by a concrete provider.

---

## 11. `get` Semantics

```python
get(key: StorageKey) -> bytes
```

If the key exists, the provider returns the exact stored payload.

If the key does not exist, the provider raises:

```text
StorageNotFoundError
```

A provider must not silently return:

```text
None
b""
```

for a missing object.

An empty payload is valid data and must remain distinguishable from absence.

---

## 12. `exists` Semantics

```python
exists(key: StorageKey) -> bool
```

The operation returns:

```text
True  → payload exists
False → payload does not exist
```

`exists` does not return a payload.

The contract does not define `exists` as an atomic synchronization primitive.

The following pattern therefore has no implied atomicity:

```python
if not provider.exists(key):
    provider.put(key, payload)
```

Concurrency-sensitive operations require a separate architectural capability if
they become necessary.

---

## 13. `delete` Semantics

```python
delete(key: StorageKey) -> None
```

If the key exists, its payload is removed.

If the key does not exist, the provider raises:

```text
StorageNotFoundError
```

The v1 contract intentionally does not define delete as a silent idempotent
operation.

A caller requiring idempotent deletion may explicitly handle
`StorageNotFoundError`.

---

## 14. Error Model v1

The public Storage Provider error hierarchy is:

```text
StorageError
├── StorageNotFoundError
└── StorageOperationError
```

### 14.1 StorageError

Base exception for provider-level failures crossing the Storage Provider
Boundary.

### 14.2 StorageNotFoundError

Indicates that the requested storage key does not contain a stored payload.

Used by:

* `get`;
* `delete`.

### 14.3 StorageOperationError

Represents a provider/backend failure that prevents the requested operation from
completing.

Examples include:

* I/O failure;
* database failure;
* connection failure;
* permission failure;
* backend availability failure.

Concrete backend exceptions must be translated into this provider-neutral error
model.

The following must not cross the public boundary directly:

```text
FileNotFoundError
sqlite3.Error
psycopg.Error
S3-specific exception
other backend-specific exceptions
```

---

## 15. Error Translation Boundary

The concrete provider owns translation from backend-specific failures to
provider-neutral errors.

Conceptually:

```text
Physical Backend
      │
      │ backend exception
      ▼
Concrete Storage Provider
      │
      │ provider-neutral exception
      ▼
Storage Provider Consumer
```

This prevents infrastructure implementation details from leaking into
application code.

---

## 16. Lifecycle and Ownership

The component that creates and configures a Storage Provider owns its lifecycle.

Consumers receive an already-configured provider through dependency injection or
an equivalent composition mechanism.

Consumers must not:

* instantiate concrete providers internally;
* open database connections directly;
* manage filesystem roots directly;
* manage object-store clients directly;
* close resources they do not own.

The v1 `StorageProvider` contract does **not** include:

```text
open()
close()
connect()
disconnect()
```

Provider lifecycle remains an infrastructure/composition concern.

---

## 17. Configuration

Storage configuration belongs outside the provider contract.

Examples include:

* filesystem path;
* database URL;
* credentials;
* object-store bucket;
* connection pool settings.

The composition/configuration layer creates the provider using these settings.

The intended flow is:

```text
Configuration
      │
      ▼
Provider Factory / Composition Root
      │
      ▼
Configured Storage Provider
      │
      ▼
Consumer
```

Consumers do not need to know how the provider was configured.

---

## 18. Transactions

Transactions are **not part of Storage Provider Contract v1**.

The v1 contract does not expose:

```text
begin()
commit()
rollback()
transaction()
```

A database provider must not force database-specific transaction semantics onto
other storage implementations.

If transactional storage becomes an architectural requirement, it should be
introduced explicitly as a separate capability or contract extension.

---

## 19. Concurrency and Versioning

Storage Provider Contract v1 does not define:

* optimistic concurrency;
* versions;
* revisions;
* ETags;
* compare-and-swap;
* conditional writes;
* locks;
* atomic multi-operation batches.

The following are therefore intentionally outside the v1 contract:

```text
expected_version
revision
etag
compare_and_swap
lock
```

These capabilities may be introduced later as explicit architectural
extensions.

---

## 20. Durability

Durability is a provider concern.

The core Storage Provider contract does not prescribe:

* filesystem durability;
* database durability;
* replication;
* backup;
* synchronous persistence;
* object-store durability guarantees.

Concrete providers may document their actual guarantees.

Application code must not depend on undocumented backend behavior.

---

## 21. Storage Provider vs Repository

The distinction between Storage Provider and Repository is intentional.

### Storage Provider

Answers:

> How do I persist and retrieve opaque data?

### Repository

Answers:

> How do I persist and retrieve a particular domain concept?

Therefore:

```text
Domain Repository
       │
       ▼
Storage Provider
       │
       ▼
Physical Storage
```

A repository may depend on a Storage Provider.

A Storage Provider must not depend on a domain repository.

The Storage Provider must not evolve into a generic domain repository abstraction.

---

## 22. Serialization Boundary

Serialization is not a responsibility of the Storage Provider.

The provider receives already-encoded opaque data.

```text
Domain object
      │
      ▼
Serializer / Encoder
      │
      ▼
bytes
      │
      ▼
Storage Provider
```

Retrieval follows the reverse direction:

```text
Storage Provider
      │
      ▼
bytes
      │
      ▼
Deserializer / Decoder
      │
      ▼
Domain object
```

The serialization format remains an independent architectural concern.

---

## 23. Provider Independence

The platform must be able to replace one concrete provider with another without
changing consumer logic.

For example:

```text
                    ┌── FileStorageProvider
                    │
StorageProvider ────┼── DatabaseStorageProvider
                    │
                    └── ObjectStorageProvider
```

Consumers depend only on:

```text
StorageProvider
StorageKey
StorageError hierarchy
```

They do not depend on concrete backend APIs.

---

## 24. Dependency Direction

The following dependency is prohibited:

```text
Runtime
  │
  └── SQLite / PostgreSQL / filesystem / S3
```

The allowed dependency direction is:

```text
Runtime / Application
        │
        ▼
Storage Provider Contract
        ▲
        │
Concrete Provider
        │
        ▼
Physical Backend
```

Concrete infrastructure depends on the contract.

Consumers do not depend directly on concrete infrastructure.

---

## 25. Architectural Invariants

The following invariants are mandatory for Storage Provider Contract v1.

### SP-INV-1 — Opaque Payload

The provider stores and retrieves opaque `bytes` payloads.

### SP-INV-2 — Explicit Storage Identity

Storage identity is represented by `StorageKey`.

### SP-INV-3 — Domain Identity Separation

`StorageKey` does not imply or encode domain identity.

### SP-INV-4 — Upsert

`put` creates or replaces the payload associated with a key.

### SP-INV-5 — Missing Read

`get` raises `StorageNotFoundError` when the key is absent.

### SP-INV-6 — Missing Delete

`delete` raises `StorageNotFoundError` when the key is absent.

### SP-INV-7 — Boolean Existence

`exists` returns only whether a payload exists.

### SP-INV-8 — Backend Encapsulation

Backend-specific APIs and exceptions do not cross the Storage Provider Boundary.

### SP-INV-9 — Provider-Neutral Errors

Public provider failures use the provider error hierarchy.

### SP-INV-10 — No Domain Semantics

The provider does not interpret domain meaning.

### SP-INV-11 — Explicit Lifecycle Ownership

Provider lifecycle is owned by the composition/infrastructure layer.

### SP-INV-12 — Provider Replaceability

A conforming provider can replace another conforming provider without changing
consumer logic.

### SP-INV-13 — No Implicit Transactions

The v1 contract provides no transaction semantics.

### SP-INV-14 — No Implicit Concurrency Guarantees

The v1 contract provides no versioning, locking, or conditional-write semantics.

### SP-INV-15 — Minimal Contract

The provider contract contains only capabilities required by the current
architecture.

---

## 26. Contract v1 — Approved Surface

The approved public surface is:

```text
StorageKey
StorageProvider
StorageError
StorageNotFoundError
StorageOperationError
```

The approved provider operations are:

```text
put(key, payload)
get(key)
exists(key)
delete(key)
```

The approved primitive payload type is:

```text
bytes
```

The approved storage address type is:

```text
StorageKey
```

No additional provider capability is implied by Contract v1.

---

## 27. Explicitly Excluded from Contract v1

The following are intentionally excluded:

* `StorageAlreadyExistsError`;
* create-only semantics;
* update-only semantics;
* `open`;
* `close`;
* `connect`;
* `disconnect`;
* transactions;
* versions;
* revisions;
* ETags;
* compare-and-swap;
* locking;
* conditional writes;
* atomic batches;
* TTL;
* caching;
* serialization;
* domain repositories;
* ORM integration;
* SQL schemas;
* migrations;
* backup/restore;
* replication;
* domain-specific metadata.

Each future capability requires an explicit architectural decision.

---

## 28. Contract Testing

Every concrete Storage Provider implementation must satisfy the same contract
tests.

Contract tests must verify behavior rather than implementation details.

At minimum, the contract test suite must cover:

1. storing a payload;
2. retrieving a stored payload;
3. payload integrity;
4. replacing an existing payload;
5. existence of a stored payload;
6. non-existence of a missing payload;
7. missing `get` behavior;
8. deleting an existing payload;
9. missing `delete` behavior;
10. empty payload handling;
11. provider-neutral error behavior.

Concrete-provider tests may verify backend-specific behavior, but they do not
replace the shared contract tests.

---

## 29. Implementation Boundary

The implementation phase must preserve the following separation:

```text
accore/
    platform/
        storage/
            contract
            errors
            key
```

The exact module structure is an implementation decision and must not weaken the
architectural contract.

Concrete providers belong below the boundary and must depend on the public
Storage Provider contract.

The first implementation must not introduce backend-specific concepts into
the public API.

---

## 30. Non-Goals

This step does not define:

* a concrete database provider;
* a filesystem provider implementation;
* an object-store provider implementation;
* domain repositories;
* ORM integration;
* SQL schemas;
* migration infrastructure;
* transaction orchestration;
* distributed locking;
* caching;
* event sourcing;
* backup/restore policy;
* replication;
* domain serialization formats.

Those concerns may be addressed by later architectural steps.

---

## 31. Step 4 Deliverables

Step 4 consists of the following artifacts:

### A. Architecture

Storage Provider Boundary definition.

**Status:** Completed.

### B. Architectural Review

Reviewed and resolved:

* boundary ownership;
* provider responsibilities;
* storage identity;
* payload representation;
* operation semantics;
* error model;
* lifecycle ownership;
* repository distinction;
* transaction boundary;
* concurrency boundary.

**Status:** Completed.

### C. API / Contract

Storage Provider Contract v1.

**Status:** Implemented.

### D. Implementation

Provider-neutral Storage Provider contract implemented together with the first
concrete production provider, `FilesystemStorageProvider`.

The implementation preserves the provider boundary and does not commit the
architecture to a broader persistence model.

**Status:** Completed.

### E. Contract Tests

Reusable provider-neutral contract tests implemented and executed against:

* the test-only `InMemoryStorageProvider`;
* `FilesystemStorageProvider`.

**Status:** Completed.

---

## 32. Completion Criteria

Step 4 is complete:

* the Storage Provider Boundary is documented;
* Contract v1 is implemented;
* `StorageKey` is implemented;
* provider-neutral errors are implemented;
* concrete backend exceptions cannot leak through the public boundary;
* consumer dependency direction is correct;
* lifecycle ownership is explicit;
* shared contract tests exist;
* `FilesystemStorageProvider` implements the contract;
* the full test suite passes with 349 tests;
* `ruff check .` passes;
* `black --check .` passes;
* `mypy src` passes.

**Step 4A — Storage Provider Boundary:** CLOSED.

**Step 4B — Filesystem Storage Provider:** CLOSED.

## 33. Architectural Decision

The AcCore platform treats physical persistence as an infrastructure capability
behind an explicit Storage Provider Boundary.

The initial boundary is intentionally minimal and storage-neutral.

The approved Contract v1 consists of:

```text
StorageKey
StorageProvider
StorageError
StorageNotFoundError
StorageOperationError
```

with the following operations:

```text
put
get
exists
delete
```

using:

```text
StorageKey → logical storage address
bytes      → opaque storage payload
```

`put` uses upsert semantics.

Missing `get` and `delete` operations raise `StorageNotFoundError`.

Concrete backend exceptions do not cross the public boundary.

Transactions, concurrency/versioning, serialization, repositories, and other
higher-level capabilities remain outside Contract v1.

This preserves provider replaceability and keeps the AcCore platform independent
from any particular persistence technology.

---

## 34. Review Result

**Storage Provider Boundary — APPROVED**

**Contract v1 — APPROVED**

Step 4A and Step 4B are both complete.

The provider-neutral Storage Provider contract is implemented and verified,
and the first concrete production provider,
`FilesystemStorageProvider`, is implemented behind that boundary.

The next architectural concern is the transaction / consistency model.
No additional storage backend is selected by Step 4.
