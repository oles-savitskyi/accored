# Phase 5 — Persistence Contract: Materialization API

**File:** `docs/implementation/PHASE_5_PERSISTENCE_CONTRACT_MATERIALIZATION_API.md`
**Status:** Architecture / Contract Definition
**Phase:** 5
**Related Steps:** Step 11 — Persistent Runtime Mapping; Step 12 — Runtime Durable State
**Related ADR:** ADR-P5-02 — Transaction and Consistency Model

---

## 1. Purpose

This document defines the semantic and concrete Python API contract for **runtime-to-persistence materialization**.

Materialization is the explicit conversion of:

```text
ObjectInstance
+
RuntimeDurableState
        │
        ▼
PersistentObject
```

The contract establishes:

* ownership of persistent identity;
* ownership of persistent object type identity;
* ownership of durable state;
* preservation of durable state semantics;
* runtime lifecycle isolation;
* reference identity preservation;
* explicit failure behavior;
* the concrete Python API boundary.

Materialization is a persistence mapping operation.

It is not a storage operation, transaction operation, repository operation, or runtime lifecycle operation.

---

# 2. Architectural Context

The runtime model separates object identity, runtime object type, runtime lifecycle, runtime context, and runtime durable state.

```text
Runtime

ObjectInstance                 RuntimeDurableState
├── identity                   ├── fields
├── object_type                ├── references
├── context                    ├── business_state
└── lifecycle state            └── system_fields
        │                              │
        └──────── associated ──────────┘
                       │
                       │ explicit mapping
                       ▼
                Persistence

                 PersistentObject
                 ├── identity
                 ├── object_type_identity
                 └── state
                     ├── fields
                     ├── references
                     ├── business_state
                     └── system_fields
```

The two runtime representations have different responsibilities.

`ObjectInstance` owns runtime object identity and runtime lifecycle.

`RuntimeDurableState` owns runtime durable state.

`PersistentObject` combines persistence identity, persistence object type identity, and persistent durable state.

---

# 3. Governing Principle

The governing principle is:

> Runtime object identity, runtime lifecycle, and runtime durable state are separate concerns. Persistence identity and persistence state are separate concerns as well. Explicit materialization connects these representations without collapsing them into one shared state model.

Materialization MUST preserve this separation.

---

# 4. Materialization Definition

Materialization is defined as:

```text
(ObjectInstance, RuntimeDurableState)
        │
        ▼
Explicit Persistence Mapping
        │
        ▼
PersistentObject
```

The operation consists of two logically distinct mappings:

```text
ObjectInstance
    ├── identity
    └── object_type
             │
             └──► PersistentObject identity/type identity


RuntimeDurableState
    ├── fields
    ├── references
    ├── business_state
    └── system_fields
             │
             └──► PersistentObjectState
```

No other runtime information is implicitly materialized.

---

# 5. Source Ownership

Materialization has two authoritative runtime sources.

## 5.1 Object identity

The authoritative source of persistent identity is:

```python
ObjectInstance.identity
```

Therefore:

```text
PersistentObject.identity
    =
ObjectInstance.identity
```

A materializer MUST NOT:

* generate a new identity;
* derive identity from durable state;
* derive identity from object context;
* derive identity from runtime attributes.

---

## 5.2 Object type identity

The authoritative source of persistent object type identity is the runtime object type:

```python
ObjectInstance.object_type
```

The persistent type identity is obtained through:

```python
ObjectInstance.object_type.metadata_identity()
```

Therefore:

```text
PersistentObject.object_type_identity
    =
ObjectInstance.object_type.metadata_identity()
```

Materialization MUST NOT resolve the type again through `RuntimeResolver`.

Runtime type resolution belongs to the hydration boundary.

---

## 5.3 Durable state

The authoritative source of persistent durable state is:

```python
RuntimeDurableState
```

The materializer MUST NOT obtain durable state from arbitrary attributes of `ObjectInstance`.

In particular, materialization MUST NOT inspect:

```python
instance.__dict__
vars(instance)
```

or equivalent arbitrary runtime attributes.

---

# 6. Target Representation

Materialization produces:

```python
PersistentObject
```

whose state is:

```python
PersistentObjectState
```

The semantic mapping is:

```text
RuntimeDurableState.fields
    → PersistentObjectState.fields

RuntimeDurableState.references
    → PersistentObjectState.references

RuntimeDurableState.business_state
    → PersistentObjectState.business_state

RuntimeDurableState.system_fields
    → PersistentObjectState.system_fields
```

The mapping MUST preserve the semantics of each category.

---

# 7. Persistent Object Construction

The resulting object has the conceptual form:

```python
PersistentObject(
    identity=instance.identity,
    object_type_identity=instance.object_type.metadata_identity(),
    state=PersistentObjectState(...),
)
```

The exact construction mechanism is an implementation detail.

The semantic result is not.

---

# 8. Field State Contract

All runtime durable fields MUST be represented in the persistent field state.

The following distinction MUST remain intact:

```text
missing key
    ≠
explicit NULL
```

Therefore materialization MUST preserve:

```text
MISSING
```

as absence of the corresponding field entry and:

```text
NULL
```

as an explicit `None` value where the persistence representation defines `None` as the null marker.

Materialization MUST NOT:

* convert missing fields into explicit nulls;
* convert explicit nulls into missing fields;
* silently discard unsupported durable field values.

---

# 9. Reference State Contract

References are represented by identity values.

For example:

```text
Runtime:
references["parent"] = Identifier(X)

        ↓

Persistent:
references["parent"] = Identifier(X)
```

Collections of references preserve their identity values and ordering semantics as defined by the reference-state contract.

Materialization MUST preserve reference identity.

---

## 9.1 No reference graph traversal

A reference is materialized as a reference identity.

The materializer MUST NOT load or recursively materialize the referenced object.

Therefore:

```text
Runtime object
    │
    └── reference → Identifier
                       │
                       ▼
                 Persistent reference
```

and not:

```text
Runtime object
    │
    └── reference
          │
          └── recursively materialized object
```

Graph loading is outside the materialization API.

---

# 10. Business State Contract

`RuntimeDurableState.business_state` is the authoritative runtime representation of durable business state.

It MUST map directly to:

```python
PersistentObjectState.business_state
```

Materialization MUST preserve:

* business-state entries;
* their identifiers;
* their values;
* their semantic absence/presence.

Business state MUST NOT be reconstructed from runtime lifecycle state or arbitrary runtime attributes.

---

# 11. Durable System Field Contract

`RuntimeDurableState.system_fields` contains durable system data.

It MUST map to:

```python
PersistentObjectState.system_fields
```

Durable system fields MUST be preserved according to their defined durable-value/reference/null semantics.

Runtime lifecycle information is not part of this mapping.

---

# 12. Runtime Lifecycle Isolation

`ObjectInstance.state` represents runtime lifecycle state.

It is not durable state.

Therefore materialization MUST NOT persist:

```python
ObjectInstance.state
```

as part of:

```python
PersistentObjectState
```

For example:

```text
ObjectInstance.state == CREATED
```

does not imply:

```text
PersistentObjectState contains "CREATED"
```

unless an independently defined durable system field explicitly represents such information.

Runtime lifecycle remains runtime-owned.

---

# 13. Runtime Context Isolation

`ObjectInstance.context` is runtime-owned.

It MUST NOT be materialized into:

```python
PersistentObjectState
```

or `PersistentObject`.

Persistence does not capture runtime context merely because the materializer receives an `ObjectInstance`.

---

# 14. Runtime Object Type Isolation

The runtime object type itself is not persisted as a runtime object.

Only its persistent metadata identity is materialized:

```text
RuntimeObjectType
       │
       └── metadata_identity()
                 │
                 ▼
       PersistentObject.object_type_identity
```

The materializer MUST NOT serialize or persist the runtime type object itself.

---

# 15. No Implicit Attribute Persistence

Materialization is explicitly state-driven.

The only durable source is:

```python
RuntimeDurableState
```

Therefore arbitrary attributes on `ObjectInstance` or its runtime type are not persistence candidates.

The following model is prohibited:

```text
ObjectInstance
    │
    ├── arbitrary Python attribute
    ├── arbitrary Python attribute
    └── arbitrary Python attribute
             │
             ▼
       Persistence
```

The required model is:

```text
RuntimeDurableState
    │
    ├── fields
    ├── references
    ├── business_state
    └── system_fields
             │
             ▼
       Persistence
```

---

# 16. No Storage Dependency

The materializer MUST NOT depend on a storage provider.

It MUST NOT:

* open files;
* write blobs;
* read from storage;
* select a storage key;
* perform persistence I/O.

Materialization produces a persistence representation.

A separate persistence/storage boundary is responsible for storing that representation.

---

# 17. No Transaction Dependency

The materializer MUST NOT own:

* transactions;
* commit;
* rollback;
* concurrency control;
* transaction scopes;
* persistence consistency scopes.

This is consistent with ADR-P5-02.

The materializer is a pure representation mapping boundary.

---

# 18. No Repository Dependency

The materializer MUST NOT require:

* repository access;
* object lookup;
* query execution;
* identity-map access;
* graph loading.

A repository may use the materializer, but the materializer does not depend on a repository.

---

# 19. No Identity Map

Materialization does not introduce an Identity Map.

The operation maps one explicitly supplied runtime object representation to one persistence representation.

```text
ObjectInstance + RuntimeDurableState
                  │
                  ▼
          PersistentObject
```

No global or scoped identity registry is required.

Identity Map architecture is deferred until a later requirement introduces multi-object runtime graph coordination.

---

# 20. No Materialization Scope

The first materialization API does not introduce a `MaterializationScope`.

No scope object is required to:

* preserve identity;
* resolve object types;
* load references;
* coordinate graph traversal.

Such a scope would introduce architectural machinery that is not required by the current single-object mapping contract.

---

# 21. Failure Contract

Materialization MUST fail explicitly when the runtime representation cannot be converted into a valid persistence representation.

The public failure type is:

```python
PersistentObjectMaterializationError
```

The materializer MUST NOT silently discard information.

Examples of materialization failure include:

* unsupported durable state representation;
* invalid durable value;
* invalid reference representation;
* inconsistent runtime representation;
* inability to construct a valid persistent representation.

The error MUST identify the operation as a materialization failure.

Underlying exceptions MAY be retained as the cause.

---

# 22. Error Translation

Implementation-specific exceptions MUST NOT leak through the public materialization boundary when they represent a materialization failure.

Conceptually:

```python
try:
    ...
except SomeInternalError as exc:
    raise PersistentObjectMaterializationError(
        "Runtime object cannot be materialized."
    ) from exc
```

The exact internal exception set is implementation-defined.

The public contract is:

```text
materialization failure
        ↓
PersistentObjectMaterializationError
```

---

# 23. Semantic Round Trip

The materialization contract participates in the semantic round trip:

```text
PersistentObject
        │
        │ hydration
        ▼
ObjectInstance
+
RuntimeDurableState
        │
        │ materialization
        ▼
PersistentObject'
```

For a supported persistent representation:

```text
PersistentObject ≈ PersistentObject'
```

where semantic equality includes:

* persistent identity;
* persistent object type identity;
* fields;
* missing/null semantics;
* references;
* business state;
* durable system fields.

The round trip does not require preservation of:

* runtime lifecycle state;
* runtime context identity;
* runtime object instance identity;
* runtime object implementation details.

---

# 24. Runtime Identity Is Not Python Object Identity

Materialization preserves domain object identity:

```python
instance.identity
```

It does not preserve Python object identity:

```python
id(instance)
```

A new `PersistentObject` is expected to be a distinct Python object.

The semantic invariant is:

```text
persistent.identity == instance.identity
```

not:

```text
persistent is instance
```

---

# 25. Concrete Python API

The materialization boundary is represented by a protocol.

```python
from typing import Protocol


class PersistentObjectMaterializationError(RuntimeError):
    """Raised when a runtime object cannot be materialized safely."""


class PersistentObjectMaterializer(Protocol):
    def materialize(
        self,
        instance: ObjectInstance,
        durable_state: RuntimeDurableState,
    ) -> PersistentObject:
        ...
```

The protocol defines the public API.

The implementation class is not prescribed by the architecture beyond satisfying this contract.

---

# 26. API Input Contract

The `instance` argument MUST provide:

```text
identity
object_type
```

The `durable_state` argument MUST provide:

```text
fields
references
business_state
system_fields
```

The materializer MUST treat these as separate sources with separate ownership.

It MUST NOT infer one from the other.

---

# 27. API Output Contract

The result MUST be a:

```python
PersistentObject
```

with:

```text
identity
object_type_identity
state
```

where:

```text
identity
    ← instance.identity

object_type_identity
    ← instance.object_type.metadata_identity()

state
    ← explicit conversion of durable_state
```

---

# 28. API Purity

At the architectural level, `materialize()` is a representation transformation.

Conceptually:

```text
materialize(
    ObjectInstance,
    RuntimeDurableState,
)
        →
PersistentObject
```

The operation MUST NOT have hidden persistence side effects.

In particular, calling `materialize()` MUST NOT itself:

* modify storage;
* mutate the supplied runtime state;
* mutate the supplied `ObjectInstance`;
* resolve references;
* alter runtime lifecycle state.

---

# 29. Immutability and Ownership

The existing runtime and persistence state containers are immutable representations.

Materialization therefore creates the persistent representation without transferring mutable ownership of runtime state.

Conceptually:

```text
RuntimeDurableState
        │
        │ semantic conversion
        ▼
PersistentObjectState
```

The resulting persistent state is independently represented.

The materializer MUST NOT create an alias that violates the immutability contract of either representation.

---

# 30. Required Mapping Invariants

The implementation MUST satisfy all of the following invariants.

### MAT-INV-01 — Identity Preservation

```text
PersistentObject.identity
    ==
ObjectInstance.identity
```

### MAT-INV-02 — Type Identity Preservation

```text
PersistentObject.object_type_identity
    ==
ObjectInstance.object_type.metadata_identity()
```

### MAT-INV-03 — Field Preservation

All supported durable fields are preserved semantically.

### MAT-INV-04 — Missing Preservation

Missing fields remain missing.

### MAT-INV-05 — Null Preservation

Explicit null remains explicit null.

### MAT-INV-06 — Reference Preservation

Reference identities are preserved semantically.

### MAT-INV-07 — No Graph Traversal

Referenced objects are not loaded or materialized recursively.

### MAT-INV-08 — Business State Preservation

Durable business state is preserved semantically.

### MAT-INV-09 — System Field Preservation

Durable system fields are preserved semantically.

### MAT-INV-10 — Lifecycle Isolation

Runtime lifecycle state is not persisted implicitly.

### MAT-INV-11 — Context Isolation

Runtime context is not persisted implicitly.

### MAT-INV-12 — Attribute Isolation

Arbitrary runtime attributes are not inspected as durable state.

### MAT-INV-13 — Explicit Failure

Unsupported or invalid materialization fails with:

```python
PersistentObjectMaterializationError
```

rather than silently losing information.

---

# 31. Contract Test Matrix

The first contract test suite SHOULD cover at least:

| Test                                                   | Requirement         |
| ------------------------------------------------------ | ------------------- |
| `test_materialize_preserves_identity`                  | MAT-INV-01          |
| `test_materialize_preserves_object_type_identity`      | MAT-INV-02          |
| `test_materialize_preserves_fields`                    | MAT-INV-03          |
| `test_materialize_preserves_missing_fields`            | MAT-INV-04          |
| `test_materialize_preserves_explicit_null`             | MAT-INV-05          |
| `test_materialize_preserves_reference_identity`        | MAT-INV-06          |
| `test_materialize_does_not_traverse_references`        | MAT-INV-07          |
| `test_materialize_preserves_business_state`            | MAT-INV-08          |
| `test_materialize_preserves_system_fields`             | MAT-INV-09          |
| `test_materialize_does_not_persist_lifecycle_state`    | MAT-INV-10          |
| `test_materialize_does_not_persist_context`            | MAT-INV-11          |
| `test_materialize_does_not_inspect_runtime_attributes` | MAT-INV-12          |
| `test_materialize_rejects_unsupported_state`           | MAT-INV-13          |
| `test_hydration_materialization_semantic_round_trip`   | Round-trip contract |

---

# 32. Test for No Implicit Attribute Persistence

The implementation MUST explicitly demonstrate that durable state comes from `RuntimeDurableState`.

A runtime object MAY contain implementation-specific attributes.

Those attributes MUST NOT appear in the resulting `PersistentObjectState` unless they are already represented by the supplied `RuntimeDurableState`.

Conceptually:

```text
ObjectInstance
    └── private/runtime-only attribute
              │
              X
              │
              ▼
       PersistentObject
```

This test protects the architecture against accidental ORM-style attribute persistence.

---

# 33. Test for Lifecycle Isolation

A contract test MUST demonstrate that changing runtime lifecycle state does not become a durable field.

The test MUST distinguish:

```text
ObjectInstance.state
```

from:

```text
RuntimeDurableState.system_fields
```

Only the latter is materialized as durable system state.

---

# 34. Test for Reference Identity

A reference test MUST verify that:

```text
Identifier(X)
```

remains:

```text
Identifier(X)
```

across materialization.

The test MUST NOT require construction or loading of the referenced runtime object.

---

# 35. Test for Semantic Round Trip

A round-trip contract test SHOULD establish:

```text
P
 │
 │ hydrate
 ▼
(R, D)
 │
 │ materialize
 ▼
P'
```

and verify:

```text
P.identity
    == P'.identity

P.object_type_identity
    == P'.object_type_identity

P.state.fields
    == P'.state.fields

P.state.references
    == P'.state.references

P.state.business_state
    == P'.state.business_state

P.state.system_fields
    == P'.state.system_fields
```

subject to the equality semantics of the corresponding state containers.

---

# 36. Relationship to Hydration

Hydration and materialization are distinct mapping operations.

## Hydration

```text
PersistentObject
        │
        ▼
RuntimeResolver
        │
        ▼
ObjectInstance
+
RuntimeDurableState
```

Hydration is responsible for resolving persistence object type identity into a runtime object type.

## Materialization

```text
ObjectInstance
+
RuntimeDurableState
        │
        ▼
PersistentObject
```

Materialization uses the already-resolved runtime object type to obtain its metadata identity.

It MUST NOT repeat runtime type resolution.

---

# 37. Relationship to RuntimeDurableState

`RuntimeDurableState` contains only durable runtime state:

```text
fields
references
business_state
system_fields
```

It does not contain:

```text
identity
object_type_identity
ObjectInstance
ObjectContext
ObjectState
RuntimeObjectType
```

Therefore materialization receives identity/type information from `ObjectInstance` and durable state from `RuntimeDurableState`.

This is intentional.

---

# 38. Relationship to PersistentObjectState

`PersistentObjectState` is the persistence-side representation of the same four durable state domains:

```text
RuntimeDurableState
        │
        │ materialization
        ▼
PersistentObjectState
```

Identity and object type identity remain outside the state object:

```text
PersistentObject
├── identity
├── object_type_identity
└── state
```

This prevents identity and type metadata from becoming accidental members of durable state.

---

# 39. Deferred Concerns

The following are explicitly deferred:

* multi-object graph materialization;
* Identity Map;
* Materialization Scope;
* repository orchestration;
* transaction orchestration;
* storage persistence;
* query-based materialization;
* lazy reference loading;
* metadata compilation;
* schema migration;
* version negotiation;
* conflict resolution.

These may introduce additional architecture later, but they are not part of the first materialization API.

---

# 40. Implementation Boundary

The implementation following this contract SHOULD introduce:

```python
PersistentObjectMaterializer
```

or a concrete implementation satisfying:

```python
PersistentObjectMaterializer
```

The implementation MUST:

1. take `ObjectInstance`;
2. take `RuntimeDurableState`;
3. obtain identity from `ObjectInstance.identity`;
4. obtain object type identity from `ObjectInstance.object_type.metadata_identity()`;
5. convert the four durable state containers explicitly;
6. construct `PersistentObjectState`;
7. construct `PersistentObject`;
8. translate materialization failures into the public materialization error;
9. avoid storage and transaction dependencies.

No additional architectural abstraction is required for the first implementation.

---

# 41. Acceptance Criteria

The Materialization API Contract is satisfied when:

* [ ] `PersistentObjectMaterializer` has an explicit public protocol.
* [ ] `PersistentObjectMaterializationError` is defined as the public failure boundary.
* [ ] identity comes exclusively from `ObjectInstance.identity`;
* [ ] object type identity comes from `ObjectInstance.object_type.metadata_identity()`;
* [ ] runtime type is not resolved again during materialization;
* [ ] all four durable state domains are explicitly mapped;
* [ ] MISSING and explicit NULL semantics are preserved;
* [ ] reference identities are preserved;
* [ ] reference graph traversal does not occur;
* [ ] business state is preserved;
* [ ] durable system fields are preserved;
* [ ] runtime lifecycle state is not persisted implicitly;
* [ ] runtime context is not persisted implicitly;
* [ ] arbitrary runtime attributes are not inspected;
* [ ] no storage provider dependency exists;
* [ ] no transaction dependency exists;
* [ ] no repository dependency exists;
* [ ] no Identity Map is introduced;
* [ ] no Materialization Scope is introduced;
* [ ] unsupported representation fails explicitly;
* [ ] semantic hydration → materialization round trip is covered by contract tests.

---

# 42. Final API Contract

The canonical first-generation materialization API is:

```python
class PersistentObjectMaterializer(Protocol):
    def materialize(
        self,
        instance: ObjectInstance,
        durable_state: RuntimeDurableState,
    ) -> PersistentObject:
        ...
```

with the public failure boundary:

```python
class PersistentObjectMaterializationError(RuntimeError):
    """Raised when a runtime object cannot be materialized safely."""
```

The canonical mapping is:

```text
ObjectInstance.identity
        │
        ▼
PersistentObject.identity


ObjectInstance.object_type.metadata_identity()
        │
        ▼
PersistentObject.object_type_identity


RuntimeDurableState
        │
        ▼
PersistentObjectState
├── fields
├── references
├── business_state
└── system_fields
```

The complete operation is therefore:

```text
                RUNTIME

        ObjectInstance
        ├── identity
        ├── object_type
        ├── context
        └── lifecycle state
                 │
                 │ identity + type identity
                 │
                 │
        RuntimeDurableState
        ├── fields
        ├── references
        ├── business_state
        └── system_fields
                 │
                 │ explicit materialization mapping
                 ▼
             PERSISTENCE

        PersistentObject
        ├── identity
        ├── object_type_identity
        └── PersistentObjectState
            ├── fields
            ├── references
            ├── business_state
            └── system_fields
```

The architectural rule is:

> Materialization is an explicit, side-effect-free representation mapping from runtime object identity plus runtime durable state to a persistent object representation. It preserves durable semantics, isolates runtime lifecycle and context, preserves reference identity without graph traversal, and introduces no storage, transaction, repository, Identity Map, or Materialization Scope concerns.
