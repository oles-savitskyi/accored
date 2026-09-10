# Phase 5 — Step 12 / пункт 11

# Materialization Mapping

## 1. Status

**Status:** Architecture / Contract Definition

**Phase:** Phase 5 — Persistence

**Step:** Step 12 — Runtime Durable State

**Sub-step:** 11 — Materialization Mapping

Implementation is intentionally out of scope until the architectural contract is accepted.

---

## 2. Purpose

This sub-step defines the mapping boundary from runtime durable state back into persistence representation.

The purpose of Materialization Mapping is to reconstruct the persistence-side durable representation from an already established `RuntimeDurableState`.

Materialization does **not** create or resolve a runtime object graph.

The central principle is:

> **Materialization Mapping restores persistence representation from runtime durable state; it does not create runtime objects or traverse the runtime object graph.**

---

## 3. Architectural Position

The persistence/runtime flow is divided into explicit boundaries.

### Persistence loading

```text
Storage Provider
       ↓
PersistentObject
```

### Persistent → Runtime hydration

```text
PersistentObject
       ↓
PersistentObjectHydrator
       ↓
ObjectInstance
       +
RuntimeDurableState
```

### Runtime → Persistence materialization

```text
ObjectInstance
       +
RuntimeDurableState
       ↓
Materialization Mapping
       ↓
PersistentObjectState
```

The three operations are intentionally separate.

```text
Storage
   │
   ▼
PersistentObject
   │
   │ Hydration
   ▼
Runtime representation
   │
   │ Materialization
   ▼
Persistent representation
```

---

## 4. Scope

Materialization Mapping is responsible only for converting durable runtime state into persistence-side state.

It is responsible for:

* durable field values;
* durable references;
* business state;
* durable system fields;
* explicit absence (`MISSING`);
* explicit null (`NULL`);
* preservation of persistence semantics;
* preservation of reference identity;
* validation of supported durable state.

It is not responsible for runtime object construction.

---

## 5. Non-Goals

Materialization Mapping MUST NOT:

* create `ObjectInstance`;
* resolve runtime object types;
* invoke `RuntimeResolver`;
* create `ObjectContext`;
* modify runtime lifecycle state;
* traverse the runtime object graph;
* recursively materialize referenced runtime objects;
* resolve persistent identifiers into runtime objects;
* access `StorageProvider`;
* read from storage;
* write to storage;
* manage transactions;
* manage identity maps;
* manage object lifetime or garbage collection;
* maintain a global runtime registry;
* infer durable state from arbitrary runtime state;
* silently discard unsupported durable state.

---

## 6. Input Contract

The conceptual input is:

```text
RuntimeDurableState
```

together with the persistence-side object representation required to associate that state with its durable object identity and type identity.

Conceptually:

```text
Runtime Object Representation
├── Object Identity
├── Object Type Identity
└── RuntimeDurableState
```

The materialization boundary operates on **durable state**, not on the runtime object's lifecycle state.

---

## 7. Output Contract

The conceptual output is:

```text
PersistentObjectState
```

or the corresponding persistence-side durable state representation established by the existing persistence contract.

The result MUST preserve all supported durable semantics.

Conceptually:

```text
RuntimeDurableState
        ↓
PersistentObjectState
```

No runtime object is created as a result of this operation.

---

## 8. Object Identity

Object identity is not part of the `RuntimeDurableState` state container.

The existing architecture keeps identity as a structural property of the object representation.

Therefore:

```text
PersistentObject.identity
        ↔
ObjectInstance.identity
```

remains an object-level mapping invariant.

Materialization MUST NOT invent, replace, or derive object identity from durable fields.

The materialization operation must operate against the already established object identity.

---

## 9. Object Type Identity

Object type identity is likewise not a field of `RuntimeDurableState`.

Runtime type resolution belongs to hydration and the established `RuntimeResolver` boundary.

Therefore materialization MUST NOT:

* resolve runtime types;
* infer object type identity;
* perform runtime type discovery;
* introduce a fallback type.

The object type identity used by the persistence representation must come from the established object representation and persistence contract.

---

## 10. Durable Fields

Each supported durable runtime field MUST be represented in persistence state without loss of semantic information.

For every durable field:

```text
Runtime durable value
        ↓
Persistent durable value
```

The mapping MUST preserve the distinction between:

```text
MISSING
NULL
VALUE
```

where these states are part of the established persistence semantics.

The materializer MUST NOT collapse:

```text
MISSING → NULL
```

or:

```text
NULL → MISSING
```

or silently omit an explicitly supported durable value.

---

## 11. Durable References

References are materialized as persistence-level identities.

The runtime durable representation:

```text
reference → Identifier
```

is mapped to the corresponding persistence reference representation.

Materialization MUST preserve reference identity.

It MUST NOT automatically transform:

```text
Identifier
```

into:

```text
ObjectInstance
```

---

## 12. Reference Graphs

Materialization Mapping does not traverse referenced objects.

For example:

```text
Object A
   │
   └── reference → Identifier(B)
```

is materialized as a reference to:

```text
Identifier(B)
```

not by loading or materializing object `B`.

Therefore:

```text
A → B
B → A
```

requires no recursive materialization by this mapping boundary.

Cycles are represented naturally through durable identifiers.

---

## 13. Identity Map

No Identity Map is required by this sub-step.

An Identity Map would be relevant only to an operation that creates or materializes multiple live runtime objects and guarantees runtime-instance identity across a materialization scope.

That is outside the scope of the current persistence materialization boundary.

Therefore:

```text
Materialization Mapping
        ≠
Runtime Object Graph Materializer
```

No global or local runtime Identity Map is introduced by Step 12 / пункт 11.

---

## 14. Materialization Scope

No `MaterializationScope` abstraction is introduced by this sub-step.

The mapping operation does not require:

* recursive runtime object creation;
* runtime graph traversal;
* runtime identity coordination;
* runtime type resolution.

Introducing such an abstraction at this stage would create a new orchestration layer without an architectural requirement.

---

## 15. Runtime Lifecycle State

Runtime lifecycle state is not durable state.

For example:

```text
CREATED
ACTIVE
DISPOSED
```

belongs to the runtime lifecycle model.

Materialization MUST NOT persist or reconstruct lifecycle state unless a future explicit persistence contract declares a particular lifecycle property durable.

Therefore:

```text
Runtime lifecycle state
        ≠
Runtime durable state
```

---

## 16. Runtime-Only State

Runtime-only state MUST NOT be materialized merely because it exists on the runtime object.

Only state explicitly declared durable by the persistence contract may cross the materialization boundary.

Conceptually:

```text
Runtime state
├── durable
│     └── materialize
│
└── runtime-only
      └── do not materialize
```

No heuristic conversion is permitted.

---

## 17. Business State

`BusinessStateSnapshot` is part of `RuntimeDurableState`.

Therefore supported business state MUST be transferred to its persistence representation without semantic loss.

Materialization MUST NOT reinterpret business state merely because its runtime representation differs from its persistence representation.

Any required domain conversion must be defined explicitly by the established persistence mapping contract.

---

## 18. Durable System Fields

`DurableSystemFieldState` is part of the durable state model.

Supported durable system fields MUST be materialized explicitly.

Runtime-only system information MUST NOT become durable merely because it is available during materialization.

---

## 19. Unsupported Durable State

Unsupported durable state is an explicit failure condition.

The materializer MUST NOT silently ignore state that the persistence contract declares durable but cannot represent.

Conceptually:

```text
unsupported durable state
        ↓
explicit MaterializationError
```

rather than:

```text
unsupported durable state
        ↓
silently discarded
```

This preserves the integrity of the persistence contract.

---

## 20. Failure Contract

Materialization failure must be explicit.

The conceptual failure category is:

```text
MaterializationError
```

Possible causes include:

* unsupported durable state;
* invalid durable value;
* invalid reference representation;
* incompatible persistence representation;
* invalid object identity context;
* persistence-state construction failure.

The exact exception hierarchy remains part of the concrete API design and is not fixed by this architectural document.

---

## 21. Completeness

A successful materialization result MUST contain all durable state required by the persistence contract.

Partial durable-state success is not permitted.

For example:

```text
fields       ✓
references   ✓
business     ✗
```

MUST NOT produce a successful `PersistentObjectState`.

The operation must either:

```text
complete → success
```

or:

```text
cannot complete → explicit failure
```

---

## 22. Persistence Isolation

Materialization Mapping MUST remain independent of the storage backend.

It MUST NOT depend on:

* filesystem paths;
* storage keys;
* filesystem providers;
* database connections;
* storage transactions;
* serialization format of a particular storage provider.

The architectural dependency is:

```text
Runtime durable representation
        ↓
Persistence durable representation
```

not:

```text
Runtime durable representation
        ↓
Storage Provider
```

---

## 23. Separation from Storage

The complete persistence pipeline remains:

```text
Runtime
  │
  │ Materialization
  ▼
PersistentObjectState
  │
  │ Persistent Object Construction
  ▼
PersistentObject
  │
  │ Storage Mapping
  ▼
Storage Provider
```

Each boundary has a distinct responsibility.

Materialization does not perform the final storage operation.

---

## 24. Separation from Hydration

Hydration and materialization are inverse-direction mappings but are not required to be implementation-level inverses.

### Hydration

```text
PersistentObject
        ↓
ObjectInstance
+
RuntimeDurableState
```

### Materialization

```text
RuntimeDurableState
+
Object identity/type context
        ↓
PersistentObjectState
```

Hydration restores runtime representation.

Materialization restores persistence representation.

Neither operation owns storage.

---

## 25. Round-Trip Semantics

Where the persistence contract permits it, the following semantic round-trip should hold:

```text
Persistent durable state
        ↓
Hydration
        ↓
Runtime durable state
        ↓
Materialization
        ↓
Persistent durable state
```

The round-trip requirement is semantic rather than byte-for-byte.

Equivalent persistence representations are acceptable when they preserve the defined persistence semantics.

The following distinctions MUST survive the round-trip where supported:

* value vs `NULL`;
* `NULL` vs `MISSING`;
* reference identity;
* supported business state;
* supported durable system state.

---

## 26. Ownership Model

| Concept                 | Owner                                |
| ----------------------- | ------------------------------------ |
| `PersistentObject`      | Persistence                          |
| `PersistentObjectState` | Persistence                          |
| `RuntimeDurableState`   | Persistence/runtime mapping boundary |
| `ObjectInstance`        | Runtime                              |
| `ObjectContext`         | Runtime                              |
| Runtime lifecycle state | Runtime                              |
| Runtime type resolution | Runtime / RuntimeResolver            |
| Storage Provider        | Storage                              |
| Materialization Mapping | Persistence mapping boundary         |

No new ownership domain is introduced by this sub-step.

---

## 27. Architectural Invariants

### M-INV-01 — Durable State Preservation

Supported durable runtime state MUST be represented in persistence state without semantic loss.

### M-INV-02 — Explicit Absence Semantics

`MISSING`, `NULL`, and concrete values MUST remain distinguishable where required by the persistence contract.

### M-INV-03 — Reference Identity

Durable references MUST preserve persistent identity.

### M-INV-04 — No Graph Traversal

Materialization MUST NOT recursively materialize referenced objects.

### M-INV-05 — No Runtime Construction

Materialization MUST NOT create `ObjectInstance` or `ObjectContext`.

### M-INV-06 — No Runtime Type Resolution

Materialization MUST NOT invoke or replace `RuntimeResolver`.

### M-INV-07 — Lifecycle Isolation

Runtime lifecycle state MUST NOT be materialized implicitly.

### M-INV-08 — Explicit Unsupported State

Unsupported durable state MUST produce explicit failure.

### M-INV-09 — Complete Success

A successful materialization result MUST contain all required durable state.

### M-INV-10 — Persistence Isolation

Materialization MUST NOT depend on a particular storage provider.

### M-INV-11 — Object Identity Stability

Materialization MUST NOT invent or replace object identity.

### M-INV-12 — Deterministic Mapping

The same supported runtime durable representation and persistence configuration MUST produce semantically equivalent persistence state.

---

## 28. Conceptual API Boundary

The architectural operation is intentionally expressed without fixing Python class or protocol names.

Conceptually:

```text
materialize(
    runtime_durable_state,
    persistence_context
) → persistent_object_state
```

The persistence context may provide the already-established object identity/type information required to construct the persistence representation.

The exact concrete API is deferred.

---

## 29. Contract Test Requirements

The future implementation MUST have contract coverage for at least:

### Basic state mapping

* empty durable state;
* ordinary durable fields;
* multiple fields;
* business state;
* durable system fields.

### Presence semantics

* `MISSING`;
* `NULL`;
* concrete value;
* preservation of distinctions between them.

### References

* single reference;
* collection of references;
* null reference;
* reference identity preservation.

### Graph behavior

* no recursive loading;
* no recursive materialization;
* references remain identifiers.

### Runtime isolation

* lifecycle state is not materialized;
* runtime-only state is not materialized;
* no `ObjectInstance` creation;
* no `ObjectContext` creation;
* no `RuntimeResolver` invocation.

### Failure behavior

* unsupported durable state;
* invalid durable representation;
* invalid reference;
* incomplete materialization.

### Storage isolation

* materialization works without a storage provider;
* no filesystem/database access is required.

### Round-trip

Where applicable:

```text
PersistentObjectState
    → hydration
    → RuntimeDurableState
    → materialization
    → PersistentObjectState
```

must preserve the defined durable semantics.

---

## 30. Explicitly Deferred

The following are deliberately deferred and MUST NOT be introduced as part of this sub-step:

* runtime object graph materialization;
* Identity Map;
* `MaterializationScope`;
* recursive reference resolution;
* global runtime object registry;
* runtime graph caching;
* garbage-collection policy;
* transaction orchestration;
* storage orchestration;
* new runtime type-resolution mechanisms.

These may become valid architectural concerns in a later step if an explicit requirement establishes them.

---

## 31. Acceptance Criteria

Step 12 / пункт 11 is architecturally accepted when:

* [ ] Materialization is explicitly defined as Runtime → Persistence mapping.
* [ ] Materialization is distinct from hydration.
* [ ] `RuntimeDurableState` remains a state container and does not acquire identity/type fields merely for materialization.
* [ ] Object identity remains an object-level property.
* [ ] Runtime type resolution remains outside materialization.
* [ ] Durable fields are preserved.
* [ ] `MISSING` and `NULL` semantics are preserved.
* [ ] Durable references preserve identifier identity.
* [ ] Reference graph traversal is explicitly excluded.
* [ ] No Identity Map is required.
* [ ] No `MaterializationScope` is required.
* [ ] Runtime lifecycle state remains runtime-owned.
* [ ] Runtime-only state is not implicitly persisted.
* [ ] Unsupported durable state produces explicit failure.
* [ ] Successful materialization is complete.
* [ ] Storage Provider remains outside the mapping boundary.
* [ ] Round-trip semantics are explicitly defined where applicable.
* [ ] Contract-test requirements are defined.
* [ ] Concrete Python API is deferred until the architectural contract is accepted.

---

## 32. Architectural Decision

The project adopts the following boundary:

```text
PersistentObject
        │
        │ Hydration
        ▼
ObjectInstance
+
RuntimeDurableState
        │
        │ Materialization
        ▼
PersistentObjectState
```

`RuntimeDurableState` remains a durable-state container.

Object identity, object type identity, runtime context, and lifecycle state remain properties of their respective object/runtime representations.

Materialization does not construct runtime objects and does not traverse object references.

Reference values remain persistence identities.

The architecture therefore deliberately avoids introducing a runtime graph materializer, Identity Map, or `MaterializationScope` at this stage.

The core principle is:

> **Hydration reconstructs runtime representation from persistence representation. Materialization reconstructs persistence representation from runtime durable state. Neither boundary owns storage, runtime graph traversal, or lifecycle management.**

Implementation may proceed only after this contract is accepted.
