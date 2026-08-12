# Object Lifecycle

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Object Lifecycle defines the architectural existence of Runtime Objects within the AcCore Runtime Environment.

It specifies how Runtime Objects are created, become active and are eventually disposed.

The Object Lifecycle describes object existence only.

Business state, persistence state and transaction state are defined by separate architectural models.

---

# 2. Design Goals

The Object Lifecycle is designed to provide:

- deterministic object creation;
- explicit object existence;
- predictable object disposal;
- implementation independence;
- compatibility with Runtime execution.

---

# 3. Architectural Principles

## Lifecycle describes existence

The Object Lifecycle defines whether a Runtime Object exists.

It does not describe business state or persistence state.

---

## Objects are created from Metadata

Every Runtime Object is instantiated according to a Metadata Object.

---

## Runtime owns object lifetime

Runtime is responsible for object creation and disposal.

Business logic does not manage object existence directly.

---

## Lifecycle is deterministic

The same creation process always produces equivalent Runtime Objects from equivalent Metadata and initial state.

---

# 4. Lifecycle Model

Conceptually:

```
Metadata Object

        │

Instantiation

        ▼

Runtime Object

        │

Activation

        ▼

Active Object

        │

Disposal

        ▼

Disposed
```

Only Active Objects participate in Runtime execution.

---

# 5. Lifecycle Stages

## Instantiation

The Runtime creates a Runtime Object from its Metadata definition.

Object Identity is established during this stage.

---

## Activation

The Runtime Object becomes available for business execution.

Object State may now change.

---

## Active Lifetime

The Runtime Object:

- executes business behavior;
- participates in Runtime Contexts;
- consumes Runtime Services;
- interacts with other Runtime Objects.

---

## Disposal

The Runtime releases the Runtime Object.

After disposal, the Runtime Object no longer participates in execution.

---

# 6. Lifecycle Ownership

The Runtime Environment owns the lifecycle of Runtime Objects.

Subsystems may use Runtime Objects but do not control their lifetime.

---

# 7. Relationship to Object State

The Object Lifecycle is independent from Object State.

An Active Object may experience many Object State changes during its lifetime.

---

# 8. Relationship to Persistence

Persistence is independent from object existence.

A Runtime Object may represent:

- a newly created business entity;
- an object loaded from storage;
- an object never intended for persistence.

---

# 9. Relationship to Runtime Context

Every Active Object exists within a Runtime Context.

Context changes do not alter the Object Lifecycle.

---

# 10. Extensibility

Future Runtime implementations may introduce additional lifecycle phases without changing the architectural model.

The fundamental lifecycle remains:

Instantiation → Activation → Disposal.

---

# 11. Relationship to Other Subsystems

The Object Lifecycle interacts with:

- Metadata;
- Runtime;
- Storage;
- Transactions;
- Events.

Each subsystem contributes to object execution while respecting Runtime ownership of object lifetime.

---

# Appendix A. Conceptual Lifecycle

```
Metadata

      │

      ▼

Instantiation

      │

      ▼

Runtime Object

      │

      ▼

Activation

      │

      ▼

Business Execution

      │

      ▼

Disposal
```

The Runtime manages the complete existence of Runtime Objects.