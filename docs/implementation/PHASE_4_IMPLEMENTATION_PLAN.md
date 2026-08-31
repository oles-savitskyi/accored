# Phase 4 — Object Runtime Implementation Plan

**Status:** In progress — Step 10

**Version:** 1.2

**Phase:** 4 — Object Runtime

**Architectural Definition:** `PHASE_4_ARCHITECTURAL_DEFINITION.md` v1.1

**Depends on:** `phase-3-final`

**Architectural baseline:** `architecture-core-3.0`

---

# 1. Purpose

This document defines the implementation sequence for Phase 4.

Phase 4 implements the Object Runtime boundary established by:

* `PHASE_4_ARCHITECTURAL_DEFINITION.md`
* ADR-P4-01 — Object Instance Model
* ADR-P4-02 — Object Identity
* ADR-P4-03 — Runtime Type Resolution vs Object Creation
* ADR-P4-04 — Object Lifecycle
* ADR-P4-05 — Object Context
* ADR-P4-06 — Object State & Storage Boundary

The implementation must remain strictly within the architectural scope
defined by those decisions.

---

# 2. Phase 4 Objective

The objective is to establish a generic executable Object Runtime capable of
creating and operating an individual object instance derived from resolved
metadata.

The Phase 4 implementation must establish:

* Object Identity;
* Object Type / runtime type relationship;
* Object State;
* Object Context;
* Object Lifecycle;
* Object Creation Boundary;
* RuntimeResolver integration;
* Catalog / Assortment vertical slice.

The resulting runtime must remain independent from physical persistence.

---

# 3. Starting Point

Phase 4 starts from the `phase-3-final` baseline.

Phase 3 already provides:

```
Configuration Definition
        ↓
Metadata Compilation
        ↓
Configuration Candidate
        ↓
Validation
        ↓
Activation
        ↓
ActiveConfiguration
        ↓
RuntimeConfigurationBinding
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
CatalogRuntime
```

Phase 4 extends the final boundary:

```
RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance
      ↓
Object Lifecycle
```

---

# 4. Implementation Principles

## P4-P1 — Architecture Before Code

No implementation should introduce an architectural concept that is not
covered by an accepted Phase 4 decision.

---

## P4-P2 — Generic Before Specific

Generic Object Runtime primitives must be implemented before Catalog-specific
extensions.

---

## P4-P3 — Preserve Phase 3 Boundaries

Phase 4 must not regress:

* RuntimeConfigurationContext;
* MetadataResolver;
* RuntimeResolver;
* configuration ownership;
* snapshot semantics.

---

## P4-P4 — Explicit Context

Object execution must use explicit runtime context.

No global configuration discovery is permitted.

---

## P4-P5 — Storage Independence

No Storage implementation is required to establish the Phase 4 runtime
object model.

---

## P4-P6 — Minimal Object Runtime

Implement only the minimum object model required by the Phase 4 vertical
slice.

Avoid speculative abstractions.

---

## P4-P7 — No Premature Registry

Do not introduce Object Registry unless an actual Phase 4 requirement
demonstrates the need.

---

## P4-P8 — Runtime / Object Boundary

The Object Runtime package must not replace the existing Runtime package.

`runtime/` remains responsible for runtime type resolution and runtime-level
execution infrastructure.

`object/` owns individual Object Instance semantics.

The intended dependency direction is:

```
runtime
   ↓
object
```

The Object Runtime must not independently resolve configuration, access
MetadataRegistry, or discover runtime configuration globally.

---

# 5. Target Runtime Model

The target runtime is:

```
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
Runtime Object Type
        ↓
Object Creation Boundary
        ↓
Object Instance
   ┌────┼──────────────┐
   │    │              │
   ▼    ▼              ▼
Identity State       Context
   │
   └────── Lifecycle
```

Storage remains outside the runtime object boundary.

The distinction between runtime type and object instance is explicit:

```
CatalogMetadata
      ↓
CatalogRuntime
(Runtime Object Type)
      ↓
ObjectInstance
(individual runtime object)
```

---

# 6. Implementation Steps

## Step 1 — Object Identity — Implemented

### Objective

Introduce the canonical Object Identity abstraction.

### Scope

Implement:

* object identity semantics;
* ULID-based identity;
* immutability;
* equality semantics;
* representation suitable for future references.

### Requirements

Object Identity must:

* be immutable;
* be independently constructible;
* not depend on Storage;
* not depend on MetadataRegistry;
* not represent Metadata Identity;
* be suitable for use as an Object Instance identifier.

### Identity Representation

Phase 4 reuses the existing `foundation.Identifier` as the technical
representation of Object Identity.

No separate `ObjectIdentity` value type is introduced.

`Identifier` remains a generic immutable ULID-backed primitive.

Object Runtime gives that primitive Object Identity semantics by using it as
the identity of an Object Instance.

This keeps Object Identity distinct at the architectural level without
introducing redundant identity wrappers.

### Tests

At minimum:

* identity generation;
* uniqueness expectations;
* equality;
* inequality;
* immutability;
* representation.

### Quality Gate

**P4-QG1 — Object Identity — CLOSED**

Object Identity is explicit at the Object Instance boundary, uses the
existing immutable ULID-backed `Identifier`, and remains distinct from
Configuration Identity and Metadata Identity at the architectural level.

---

# 7. Step 2 — Object Type / Object Instance Contract — Implemented

### Objective

Introduce the canonical Object Instance abstraction.

### Scope

Implement the minimum runtime object contract containing:

* Object Identity;
* Object Type;
* Object State.

Object Context and lifecycle operations are introduced by subsequent
implementation steps and are not part of the initial ObjectInstance
construction contract.

The implementation must not introduce persistence.

### Requirements

The object instance must:

* represent one individual business object;
* have exactly one Object Identity;
* be associated with one runtime object type;
* hold runtime state;
* not require Storage access merely to exist.

### Current Contract

The current Object Instance contract is:

```
ObjectInstance

    identity: Identifier

    object_type: CatalogRuntime

    state: ObjectState
```

`CatalogRuntime` represents a resolved runtime object type.

`ObjectInstance` represents one individual runtime entity of that type.

### Architectural Invariants

I1. Every ObjectInstance has exactly one Object Identity.

I2. Object Identity is independent from Metadata Identity.

I3. Every ObjectInstance is associated with exactly one resolved Object Type.

I4. CatalogRuntime represents an Object Type, not an Object Instance.

I5. RuntimeResolver resolves Object Types and does not own instance creation.

I6. Object Runtime depends on `RuntimeObjectType`, not on concrete Runtime
Object Type implementations.

The generic Object Runtime may consume any implementation satisfying the
`RuntimeObjectType` contract. It must not require `CatalogRuntime` or another
concrete Runtime Object Type implementation.

I7. ObjectInstance does not require Storage access merely to exist.

I8. ObjectInstance equality is based on Object Identity, not Object State.

### Tests

At minimum:

* instance creation;
* identity association;
* type association;
* initial state association;
* separation of two instances of the same type;
* equality by identity.

### Quality Gate

**P4-S2 — Object Type / Object Instance Contract — CLOSED**

CatalogRuntime represents a resolved runtime object type.

ObjectInstance represents one individual runtime entity of that type.

Metadata Identity and Object Identity are separate concepts.

RuntimeResolver resolves runtime object types and does not create ObjectInstance
objects.

---

# 8. Step 3 — Object State — Implemented

### Objective

Define the runtime representation of object state.

### Scope

Implement the minimum generic state model required by an Object Instance.

The initial implementation must establish object state representation
and initial-state semantics without introducing a generalized state engine.

### Requirements

Object State must:

* belong to an Object Instance;
* be independent from persistence;
* preserve Object Identity independently from state;
* define the minimum runtime lifecycle states required by Phase 4:
  * `CREATED`;
  * `ACTIVE`;
  * `DISPOSED`;
* ensure that every newly created Object Instance enters the runtime in
  `CREATED` state;
* prevent the initial state from being selected by the Object Instance
  constructor.

State transition operations are outside the current Step 3 implementation
scope and will be introduced through a dedicated lifecycle boundary.

These values represent the current Object Runtime lifecycle state model.
Phase 4 does not introduce a generalized state machine or a separate
metadata-defined state engine.

### Current Initial-State Contract

`ObjectInstance` establishes `ObjectState.CREATED` internally.

The constructor does not expose an argument allowing callers to select the
initial state.

Therefore:

```
ObjectInstance(...)
      ↓
state == ObjectState.CREATED
```

### Explicit Non-Goals

Do not implement:

* generalized state machines;
* state transition orchestration;
* dirty tracking;
* Unit of Work;
* repositories;
* automatic persistence;
* transactions;
* optimistic locking.

### Tests

At minimum:

* Object State values;
* initial state;
* constructor cannot select the initial state;
* each Object Instance owns its own Object State;
* state is not shared between Object Instances;
* identity remains independent from state;
* Object Instances with the same identity remain equal regardless of state.

### Quality Gate

**P4-QG3 — Object State / Persistence Separation — CLOSED**

Object State has no direct dependency on Storage or persistence mechanisms.

---

# 9. Step 4 — Object Context — Implemented

### Objective

Introduce the explicit context required by Object Runtime.

### Scope

Integrate Object Context with the Phase 3
`RuntimeConfigurationContext`.

### Requirements

Object Context must:

* carry the relevant runtime configuration context;
* preserve configuration snapshot semantics;
* be explicit;
* not activate configuration;
* not access configuration binding directly;
* not become a service locator.

Object Context represents the runtime context under which an Object Instance
exists and operates.

It must not become a replacement for `RuntimeConfigurationContext` and must
not introduce a second configuration lifecycle.

### Required Relationship

The intended relationship is:

```
RuntimeConfigurationContext
          ↓
    Object Context
          ↓
    Object Instance
```

The implementation uses a dedicated `ObjectContext` abstraction.

`ObjectContext` represents the runtime context of an individual Object
Instance and carries the relevant `RuntimeConfigurationContext`.

It does not own configuration activation, configuration publication or
configuration discovery.

### Tests

At minimum:

* context creation;
* configuration context association;
* context immutability where applicable;
* object retains its configuration snapshot;
* changing active configuration does not silently change object context.

### Quality Gate

**P4-QG4 — Context Boundary — CLOSED**

Object Context is compatible with Phase 3 context semantics.

---

# 10. Step 5 — Object Lifecycle — Implemented

### Objective

Implement the generic Object Runtime lifecycle.

### Lifecycle

```
create → Created

Created → Active

Active → Disposed
```

Object creation produces an Object Instance in the Created state.

Transition to Active is a separate lifecycle operation.

Disposed objects cannot be used for normal runtime operations.

### Requirements

Implement:

* lifecycle state;
* legal transitions;
* invalid transition errors;
* disposed-object protection.

Lifecycle operations must remain independent from Configuration Lifecycle.

Object lifecycle must not activate, deactivate, or otherwise mutate runtime
configuration.

### Tests

At minimum:

* create → Created;
* Created → Active;
* Active → Disposed;
* invalid Created → Disposed if prohibited by the implementation contract;
* invalid operations on Disposed;
* repeated disposal behavior;
* lifecycle isolation between instances.

### Quality Gate

**P4-QG5 — Lifecycle — CLOSED**

Lifecycle transitions are explicit and deterministic.

---

# 11. Step 6 — Object Creation Boundary — Implemented

### Objective

Introduce the explicit owner of Object Instance creation.

### Scope

Separate:

```
Runtime Type Resolution
```

from:

```
Object Instance Creation
```

The implementation mechanism may be:

* dedicated creator;
* factory;
* type-bound creation capability;
* another explicit abstraction.

The exact class name is not architecturally mandated.

### Requirements

Creation must establish:

* Object Identity;
* Object Type;
* initial Object State;
* Object Context;
* Created lifecycle state.

Creation must not:

* persist;
* activate configuration;
* mutate MetadataRegistry;
* implicitly use global configuration;
* create a global object registry.

### Creation Dependency

The intended flow is:

```
Runtime Object Type
        +
Object Context
        ↓
Object Creation Boundary
        ↓
ObjectInstance
```

Creation consumes an already resolved runtime type.

It must not perform independent metadata resolution or configuration
discovery.

### Tests

At minimum:

* creation from a resolved runtime type;
* unique identity per created instance;
* correct context;
* correct initial state;
* correct lifecycle state;
* failure for unsupported runtime types.

### Quality Gate

**P4-QG6 — Creation Ownership — CLOSED**

One explicit creation boundary owns Object Instance creation.

---

# 12. Step 7 — RuntimeResolver → Object Runtime Integration — Implemented

### Objective

Integrate the Phase 4 Object Runtime with the Phase 3 RuntimeResolver
without collapsing responsibilities.

### Current Responsibility

RuntimeResolver resolves:

```
Metadata Identity
      +
RuntimeConfigurationContext
      ↓
Runtime Object Type
```

Phase 4 must preserve that responsibility.

### Target Responsibility

```
RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance
```

RuntimeResolver remains a type resolver.

Object creation remains a separate operation.

### Requirements

RuntimeResolver must not become responsible for:

* object persistence;
* lifecycle management;
* global registry;
* configuration activation;
* repository management;
* Object Instance ownership.

### Tests

At minimum:

* metadata identity resolves to runtime object type;
* unsupported metadata fails correctly;
* resolved type can be passed to creation boundary;
* resolver remains context-explicit;
* no direct MetadataRegistry dependency is introduced into Object Runtime.

### Quality Gate

**P4-QG7 — RuntimeResolver Boundary — CLOSED**

Runtime type resolution and Object Instance creation remain distinct.

---

# 13. Step 8 — Catalog / Assortment Integration — Implemented

### Objective

Use the generic Object Runtime with a real Standard Configuration catalog.

### Representative Object

The initial representative object is:

```
Standard Configuration
        ↓
    Assortment
        ↓
   Catalog Object
```

### Target Flow

```
Standard Configuration
        ↓
Catalog Metadata
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
Catalog Runtime Type
        ↓
Object Creation Boundary
        ↓
Assortment Object Instance
```

### Requirements

Catalog-specific code must consume the generic Object Runtime contract.

It must not introduce:

* a separate identity model;
* a separate lifecycle model;
* a separate object context;
* a catalog-specific generic factory;
* a catalog-specific registry.

### Quality Gate

**P4-QG8 — Generic Catalog Consumer — CLOSED**

Assortment is represented as a consumer of the generic Object Runtime.

---

# 14. Step 9 — Public API Alignment — Implemented

### Objective

Expose only the stable Phase 4 abstractions through the intended package
boundaries.

### Scope

Review:

* `src/accore/platform/object/`;
* existing runtime packages;
* configuration package exports;
* public API tests.

### Requirements

Internal implementation details must not accidentally become public API.

The public API must expose only abstractions that are architecturally
stable enough for Phase 4.

### Tests

* import tests;
* public API contract tests;
* forbidden/internal import checks where applicable.

### Quality Gate

**P4-QG9 — Public API — CLOSED**

Phase 4 public API is explicit and minimal.

---

# 15. Step 10 — Documentation Alignment

### Objective

Synchronize implementation and architecture documentation.

### Documents to Review

* `ARCHITECTURE_OVERVIEW.md`;
* `GLOSSARY.md`;
* Object Architecture documentation;
* Runtime Architecture documentation;
* Storage Architecture documentation;
* Standard Configuration documentation;
* Phase 4 ADRs;
* `PHASE_4_ARCHITECTURAL_DEFINITION.md`;
* `PHASE_4_IMPLEMENTATION_PLAN.md`.

### Required Alignment

The documentation must consistently distinguish:

* Metadata Identity;
* Object Identity;
* Runtime Object Type;
* Object Instance;
* Object State;
* Object Context;
* Object Lifecycle;
* Persistent Representation.

The documentation must also explicitly preserve the following distinction:

```
Metadata Identity
      ≠
Object Identity
```

and:

```
Runtime Object Type
      ≠
Object Instance
```

and:

```
Object State
      ≠
Persistent State
```

### Quality Gate

**P4-QG10 — Documentation Alignment**

No architectural terminology conflict remains between implementation and
documentation.

---

# 16. Step 11 — Full Regression

### Objective

Verify that Phase 4 does not regress earlier phases.

### Required Checks

```
pytest

ruff check

black --check

mypy src
```

All existing Phase 3 tests must remain green.

New Phase 4 tests must be included in the full suite.

### Quality Gate

**P4-QG11 — Regression**

All project quality checks pass.

---

# 17. Step 12 — Final Architectural Audit

Before Phase 4 is tagged, perform a final audit against:

* Phase 4 Architectural Definition;
* ADR-P4-01;
* ADR-P4-02;
* ADR-P4-03;
* ADR-P4-04;
* ADR-P4-05;
* ADR-P4-06.

The audit must verify:

1. Object Identity is distinct from Metadata Identity.
2. Object Type is distinct from Object Instance.
3. Object State is distinct from persistent state.
4. Object Context uses explicit runtime configuration context.
5. Object lifecycle is independent of configuration lifecycle.
6. Object creation has one explicit owner.
7. RuntimeResolver remains a type resolver.
8. Storage remains outside Object Runtime.
9. Catalog uses the generic Object Runtime.
10. No premature Object Registry exists.
11. Phase 3 invariants remain intact.
12. No redundant ObjectIdentity abstraction has been introduced.
13. Object Instance equality is based on Object Identity rather than mutable
    runtime state.

### Quality Gate

**P4-QG12 — Final Architectural Audit**

All Phase 4 architectural invariants are satisfied.

---

# 18. Dependency Graph

The implementation order is intentionally linear:

```
Step 1
Object Identity
    ↓
Step 2
Object Instance / Object Type Contract
    ↓
Step 3
Object State Semantics
    ↓
Step 4
Object Context
    ↓
Step 5
Object Lifecycle
    ↓
Step 6
Object Creation Boundary
    ↓
Step 7
RuntimeResolver Integration
    ↓
Step 8
Catalog Integration
    ↓
Step 9
Public API
    ↓
Step 10
Documentation
    ↓
Step 11
Regression
    ↓
Step 12
Final Audit
```

Step 3 refines the state semantics of the Object Instance introduced by
Step 2. It does not introduce a separate object identity or persistence
model.

---

# 19. Expected Package Structure

Phase 4 introduces the Object Runtime package as a new architectural
boundary.

The current minimal implementation is:

```
src/accore/platform/

    object/

        instance.py

        state.py
```

No separate `identity.py` module is required.

Object Identity is represented by the existing
`foundation.Identifier` at the `ObjectInstance` boundary.

Additional modules such as:

```
context.py

lifecycle.py

creation.py
```

may be introduced when implementation cohesion or public API boundaries
justify them.

The package must not duplicate responsibilities already owned by:

```
configuration/

metadata/

runtime/
```

The exact module decomposition remains an implementation decision, provided
the Phase 4 ADRs and architectural invariants remain satisfied.

---

# 20. Testing Strategy

Phase 4 testing is divided into four levels.

## 20.1 Unit Tests

Test individual:

* identity semantics;
* state;
* context;
* lifecycle;
* object instance;
* creation boundary.

---

## 20.2 Boundary Tests

Test:

* RuntimeResolver → Object Runtime Type → Object Creation;
* Object Runtime → RuntimeConfigurationContext;
* Object Runtime → Storage boundary;
* Catalog → Generic Object Runtime.

### P4-CROSS-01 — Object Runtime → Runtime Boundary

**Status:** CLOSED

The Phase 4 Object Runtime depends on the Runtime subsystem only through
the `RuntimeObjectType` architectural contract.

`RuntimeResolver` produces resolved `RuntimeObjectType` instances, while
`ObjectCreator` and `ObjectInstance` consume that contract without depending
on concrete Runtime implementations such as `CatalogRuntime`.

Validation confirms that:

- Object Runtime does not import `CatalogRuntime`;
- Object Runtime does not import `RuntimeResolver`;
- Object Runtime does not access `MetadataRegistry` directly;
- Object Runtime has no direct Storage dependency;
- Object Runtime receives configuration through the explicit
  `RuntimeConfigurationContext` carried by `ObjectContext`;
- `RuntimeObjectType` is a `Protocol` and therefore represents an
  architectural dependency boundary rather than a concrete Runtime
  implementation.

The concrete `CatalogRuntime` implementation is used only as a Runtime Object
Type implementation and may be replaced without changing the generic Object
Runtime.

Therefore the Runtime → Object Runtime boundary is considered architecturally
closed for Phase 4.

---

## 20.3 Vertical Slice Tests

Verify:

```
Standard Configuration
    ↓
Assortment Metadata
    ↓
Runtime Resolution
    ↓
Object Creation
    ↓
Assortment Object Instance
```

---

## 20.4 Regression Tests

All pre-Phase-4 tests must remain green.

---

# 21. Error Model

Phase 4 should introduce explicit object-level failures where necessary.

At minimum, distinguish:

* object creation failure;
* unsupported runtime object type;
* invalid object state;
* invalid lifecycle transition;
* invalid object context;
* operation on disposed object.

Storage failures must not be represented as generic Object Runtime failures.

Configuration activation failures must remain configuration-level failures.

Metadata resolution failures must remain metadata/runtime-resolution failures.

---

# 22. Explicitly Deferred Work

The following work is intentionally deferred.

### Object Registry

Only introduce if an explicit requirement appears.

### Persistence

Deferred to Storage/Object persistence architecture.

### Repository

Deferred.

### Unit of Work

Deferred.

### Dirty Tracking

Deferred.

### Transactions

Deferred.

### Query Engine

Deferred.

### Object References

Only minimal identity compatibility is required.

### Documents

Future consumer of Object Runtime.

### Posting

Future business operation layer.

### Registers

Future downstream subsystem.

### Valuation

Future downstream subsystem.

### Reporting

Future downstream subsystem.

---

# 23. Phase 4 Definition of Done

Phase 4 is complete when all architectural, implementation, boundary, and
validation requirements of the Object Runtime have been satisfied.

## 23.1 Object Runtime Implementation

* [x] Object Identity is implemented.
* [x] Object Instance contract is implemented.
* [x] Object State is implemented.
* [x] Object Context is implemented.
* [x] Object Lifecycle is implemented.
* [x] Object Creation Boundary is implemented.

## 23.2 Runtime Integration

* [x] RuntimeResolver integration is complete.
* [x] RuntimeResolver resolves Runtime Object Types and does not create
  Object Instances.
* [x] Object Runtime depends on Runtime only through `RuntimeObjectType`.
* [x] Object Runtime has no dependency on concrete `CatalogRuntime`.
* [x] Object Runtime does not resolve configuration independently.
* [x] Object Runtime consumes an explicit `ObjectContext`.
* [x] `ObjectContext` preserves the supplied `RuntimeConfigurationContext`
  snapshot.

## 23.3 Storage and Infrastructure Boundaries

* [x] No Storage dependency exists in Object Runtime.
* [x] Object Runtime does not require Storage for Object Instance creation.
* [x] Object Runtime does not depend on persistence mechanisms.
* [x] Storage remains downstream from Object Runtime.
* [x] No Object Registry has been introduced.

## 23.4 Generic Runtime and Catalog Integration

* [x] Catalog / Assortment uses the generic Object Runtime.
* [x] Catalog-specific runtime behavior does not redefine the generic
  Object Runtime lifecycle.
* [x] `CatalogRuntime` remains a Runtime Object Type rather than an
  Object Instance.
* [x] Generic Object Runtime semantics are independent of Catalog-specific
  implementation details.

## 23.5 Public API and Documentation

* [x] Public APIs are aligned.
* [x] Object Runtime documentation is aligned with the implemented
  architecture.
* [x] Runtime/Object architectural boundaries are explicitly documented.
* [x] Storage independence is explicitly documented.
* [x] Object Registry remains explicitly deferred.

## 23.6 Validation

* [x] Unit tests pass.
* [x] Boundary tests pass.
* [x] Vertical slice passes.
* [x] Full regression passes.
* [x] `ruff check .` passes.
* [x] `black --check .` passes.
* [x] `mypy src` passes.
* [ ] Final architectural audit passes.

Phase 4 is considered complete only after the final architectural audit
confirms that the implemented system remains consistent with the Phase 4
architectural definition and ADRs.

---

# 24. Phase 4 Success Criterion

The Phase 4 implementation is successful when AcCoreD can perform the
following operation without accessing physical persistence:

```
Resolve Standard Configuration
        ↓
Resolve Assortment Metadata
        ↓
Resolve Assortment Runtime Type
        ↓
Create Assortment Object Instance
        ↓
Assign Object Identity
        ↓
Initialize Object State
        ↓
Bind Object Context
        ↓
Transition Object to Active
        ↓
Execute a valid object operation
```

while preserving all Phase 3 configuration and runtime boundaries.

The `Transition Object to Active` operation is a Phase 4 end-state
criterion and is not expected to be available before the Object Lifecycle
step is implemented.

---

# 25. Final Architectural Boundary

At the end of Phase 4 the canonical runtime flow is:

```
Configuration
      ↓
RuntimeConfigurationContext
      ↓
MetadataResolver
      ↓
RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance
   ├── Identity
   ├── Type
   ├── State
   ├── Context
   └── Lifecycle
      ↓
Future Persistence Boundary
      ↓
Storage
```

The Object Runtime is therefore established as a stable architectural
boundary between runtime type resolution and future persistence/business
subsystems.

The Object Runtime does not own metadata resolution, configuration
activation, persistence, or global object registration.

Object Identity is represented by the existing immutable
`foundation.Identifier`, while remaining architecturally distinct from
Metadata Identity and Configuration Identity.

---

# Phase 4 Implementation Alignment

As of the current implementation baseline (`0208966`), Steps 1–9 are implemented and Step 10 is in progress.

Implemented runtime boundaries:

```text
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
CatalogRuntime
        ↓
ObjectCreator
        ↓
ObjectInstance
        ↓
ObjectLifecycle
```

The current test baseline includes the Object and Runtime unit suites, the Object Lifecycle integration test, the Assortment vertical slice, and the Runtime public API test.
