# Object Factory

**Version:** 1.1
**Status:** Accepted / Implemented in progress

---

# 1. Purpose

The Object Factory defines the architectural mechanism responsible for creating Runtime Objects within the AcCore platform.

The Object Creation Boundary creates individual Object Instances from already resolved Runtime Object Types while preserving separation between Metadata, Runtime and Storage.

Object creation is exclusively managed by the Runtime through the Object Factory.

---

# 2. Design Goals

The Object Factory is designed to provide:

- deterministic object creation;
- centralized object instantiation;
- implementation independence;
- compatibility with Metadata and Runtime;
- extensibility for future object categories;
- consistent Runtime initialization.

---

# 3. Architectural Principles

## Object Runtime owns object creation

Object Instances are created through one explicit Object Creation Boundary,
implemented as `ObjectCreator` in Phase 4.

The Runtime package resolves Runtime Object Types, while the Object Runtime
owns individual Object Instance creation.

---

## Metadata defines creation

`ObjectCreator` consumes an already resolved `CatalogRuntime` Runtime Object Type and an explicit `ObjectContext`.

Metadata specifies object structure but does not create object instances.

---

## Creation is deterministic

Equivalent Metadata definitions and equivalent initialization parameters shall produce equivalent Runtime Objects.

---

## Factory is implementation-independent

The Object Factory defines architectural responsibilities rather than implementation mechanisms.

Concrete implementations may vary without affecting the architectural model.

---

## Factory does not own objects

Creation returns an Object Instance in `CREATED` state. Lifecycle transitions are owned by `ObjectLifecycle`.

Lifecycle management belongs to the Runtime.

---

# 4. Architectural Model

Conceptually:

```
Metadata Object

        │

        ▼

Object Factory

        │

        ▼

Runtime Object

        │

        ▼

Runtime Lifecycle
```

The Object Factory performs object creation only.

---

# 5. Factory Responsibilities

The Object Factory is responsible for:

- generating Object Identity;
- associating Runtime Object Type;
- associating Object Context;
- establishing initial CREATED state.

The Object Factory does not execute business behavior.

---

# 6. Object Initialization

Object initialization establishes the executable representation of a Domain Object.

Initialization may include:

- Object Identity assignment;
- Runtime State initialization;
- Runtime Context association;
- Runtime Service binding.

Initialization remains independent of persistence.

---

# 7. Relationship to Metadata

Metadata provides the structural definition used by the Object Factory.

The Object Factory does not modify Metadata.

Metadata remains immutable during object creation.

---

# 8. Relationship to Runtime

The Object Creation Boundary is part of the Object Runtime boundary and does not replace the Runtime package.

The Object Creation Boundary is invoked with a resolved Runtime Object Type and explicit Object Context; it does not perform metadata resolution or configuration discovery.

Object creation becomes part of the Runtime lifecycle.

---

# 9. Relationship to Object Identity

`ObjectCreator` generates a new immutable ULID-backed `foundation.Identifier` for a newly created Object Instance.

Identity generation mechanisms are implementation-specific.

The architectural responsibility for establishing identity belongs to the Object Factory.

---

# 10. Relationship to Runtime Context

Every Object Instance is associated with an explicit `ObjectContext` during creation.

The Runtime Context provides the execution environment required by the object.

---

# 11. Relationship to Storage

The Object Factory creates Object Instances independently of persistence.

Object creation does not:

- access Storage;
- persist the Object Instance;
- restore persistent state;
- create a persistent representation.

Persistence and restoration are deferred to the future persistence architecture.

The Object Creation Boundary therefore remains valid for runtime-only object
creation without requiring Storage.

---

# 12. Architectural Boundaries

The Object Factory separates:

- Metadata definition;
- Runtime creation;
- Runtime execution;
- persistence;
- business behavior.

Each concern belongs to a dedicated architectural subsystem.

---

# 13. Extensibility

Future Runtime implementations may introduce additional object creation strategies without changing the architectural contract of the Object Factory.

The architectural responsibilities remain unchanged.

---

# 14. Relationship to Other Subsystems

The Object Factory collaborates with several Runtime subsystems.

```
Metadata

      │

      ▼

Object Factory

      │

      ▼

RuntimeResolver
      ↓
CatalogRuntime (Runtime Object Type)
      +
ObjectContext
      ↓
ObjectCreator
      ↓
ObjectInstance [CREATED]
```

The Object Factory creates Runtime Objects and delegates subsequent responsibilities to the appropriate Runtime subsystems.

No implicit configuration activation, Metadata Registry access, persistence, or Object Registry registration occurs during creation.

---

# Appendix A. Object Creation Flow

```
Metadata Object

        │

        ▼

Validation

        │

        ▼

Object Factory

        │

        ▼

Object Identity

        │

        ▼

Runtime State Initialization

        │

        ▼

Runtime Context Association

        │

        ▼

Runtime Object
```

Each creation step has a clearly defined architectural responsibility.

---

# Appendix B. Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Metadata | Defines object structure |
| Object Factory | Creates Runtime Objects |
| Runtime Context | Provides execution environment |
| Runtime Object | Executes business behavior |
| Runtime Lifecycle | Manages object existence |

The Object Factory serves as the architectural entry point for Runtime Object creation.
