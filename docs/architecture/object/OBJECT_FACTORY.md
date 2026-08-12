# Object Factory

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Object Factory defines the architectural mechanism responsible for creating Runtime Objects within the AcCore platform.

The Object Factory transforms Metadata-defined Domain Objects into executable Runtime Objects while preserving architectural separation between Metadata, Runtime and Storage.

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

## Runtime owns object creation

Runtime Objects are created exclusively by the Runtime through the Object Factory.

Business logic shall not instantiate Runtime Objects directly.

---

## Metadata defines creation

The Object Factory creates Runtime Objects according to Metadata definitions.

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

The responsibility of the Object Factory ends after successful object creation.

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

- validating Metadata required for creation;
- creating Runtime Objects;
- assigning Object Identity when required;
- initializing Runtime State;
- associating the Runtime Object with the current Runtime Context.

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

The Object Factory is a Runtime Service.

The Runtime invokes the Object Factory whenever a new Runtime Object must be created.

Object creation becomes part of the Runtime lifecycle.

---

# 9. Relationship to Object Identity

The Object Factory establishes the Object Identity of newly created Domain Objects according to platform rules.

Identity generation mechanisms are implementation-specific.

The architectural responsibility for establishing identity belongs to the Object Factory.

---

# 10. Relationship to Runtime Context

Every Runtime Object is associated with a Runtime Context during creation.

The Runtime Context provides the execution environment required by the object.

---

# 11. Relationship to Storage

The Object Factory creates Runtime Objects independently of persistence.

Objects may be:

- newly created;
- restored from persistent storage;
- created for temporary Runtime execution.

Creation semantics remain identical.

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

Runtime Object

      │

 ┌────┼────┐

 ▼    ▼    ▼

Context Registry Storage
```

The Object Factory creates Runtime Objects and delegates subsequent responsibilities to the appropriate Runtime subsystems.

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