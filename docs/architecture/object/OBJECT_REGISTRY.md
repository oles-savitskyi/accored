# Object Registry

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Object Registry defines the architectural mechanism responsible for registering and locating Runtime Objects within the AcCore Runtime Environment.

The Object Registry maintains the association between Object Identity and Runtime Objects.

The Registry provides a unified identity-based lookup service for Runtime execution.

---

# 2. Design Goals

The Object Registry is designed to provide:

- unique Runtime Object registration;
- deterministic object lookup;
- identity-based access;
- implementation independence;
- compatibility with Runtime Services;
- extensibility for future Runtime implementations.

---

# 3. Architectural Principles

## Runtime owns the Registry

The Object Registry is a Runtime Service.

Domain Objects do not manage registration.

---

## Registration is identity-based

Every Runtime Object is registered using its Object Identity.

Object lookup is performed exclusively through Object Identity.

---

## One identity — one Runtime Object

Within a Runtime Environment, a single Object Identity shall correspond to at most one active Runtime Object.

This guarantees a consistent view of each Domain Object during execution.

---

## Registry does not create objects

Object creation belongs to the Object Factory.

The Registry only registers existing Runtime Objects.

---

## Registry does not persist objects

Persistence belongs to the Storage subsystem.

The Registry never stores durable object representations.

---

## Registry does not execute business behavior

Business execution remains the responsibility of Runtime Objects.

---

# 4. Architectural Model

Conceptually:

```
Object Identity

        │

        ▼

Object Registry

        │

        ▼

Runtime Object
```

The Object Registry maintains the association between identities and Runtime Objects.

---

# 5. Registry Responsibilities

The Object Registry is responsible for:

- registering Runtime Objects;
- unregistering Runtime Objects;
- locating Runtime Objects by Object Identity;
- preventing duplicate registrations;
- maintaining identity uniqueness within the Runtime Environment.

The Registry owns no business logic.

---

# 6. Registration Lifecycle

Runtime Objects are registered immediately after successful creation.

Registration ends when the Runtime Object leaves the Runtime Environment.

The Registry reflects the current Runtime population only.

---

# 7. Relationship to Object Factory

The Object Factory creates Runtime Objects.

After creation, the Runtime registers the object in the Object Registry.

Creation and registration are separate architectural responsibilities.

---

# 8. Relationship to Runtime Context

Registered Runtime Objects execute within a Runtime Context.

The Registry stores object associations independently of Runtime Context implementation.

---

# 9. Relationship to Object Identity

Object Identity is the primary key of the Object Registry.

The Registry never derives identity from object state.

---

# 10. Relationship to Storage

The Registry is independent of persistent storage.

Loading or saving objects is performed by the Storage subsystem.

The Registry may register objects originating from Storage, but it never performs storage operations itself.

---

# 11. Architectural Boundaries

The Object Registry separates:

- object identity;
- object creation;
- runtime registration;
- persistence;
- business execution.

Each concern belongs to a dedicated subsystem.

---

# 12. Extensibility

Future Runtime implementations may introduce specialized registry implementations while preserving the same architectural contract.

Possible optimizations include:

- partitioned registries;
- distributed registries;
- concurrent registries.

The architectural responsibilities remain unchanged.

---

# 13. Relationship to Other Subsystems

The Object Registry collaborates with multiple Runtime services.

```
Metadata

      │

      ▼

Object Factory

      │

      ▼

Object Registry

      │

 ┌────┼─────────┐

 ▼    ▼         ▼

Runtime Context Storage
```

The Registry provides identity-based access without assuming the responsibilities of neighboring subsystems.

---

# Appendix A. Registration Flow

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

Object Registry

        │

        ▼

Runtime Execution
```

Object creation and object registration are separate architectural stages.

---

# Appendix B. Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Object Factory | Creates Runtime Objects |
| Object Registry | Registers and locates Runtime Objects |
| Object Identity | Provides unique object identity |
| Runtime Context | Supplies execution environment |
| Runtime Object | Executes business behavior |

The Object Registry provides a stable identity-based view of Runtime Objects throughout their execution.