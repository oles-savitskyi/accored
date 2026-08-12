# Object Identity

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Object Identity architecture defines the immutable identity of Domain Objects within the AcCore platform.

Object Identity provides a stable architectural identity shared by all representations of a Domain Object, including Metadata, Runtime and Storage.

Identity enables references, persistence, transactions and distributed execution while remaining independent of implementation details.

---

# 2. Design Goals

The Object Identity architecture is designed to provide:

- stable object identity;
- implementation independence;
- deterministic object equality;
- compatibility across architectural subsystems;
- support for distributed environments;
- long-term identity stability.

---

# 3. Architectural Principles

## Identity is immutable

Object Identity never changes during the lifetime of a Domain Object.

Changes to Object State do not affect Object Identity.

---

## Identity is architecture, not implementation

Object Identity is an architectural concept.

The concrete identifier format is an implementation decision.

---

## Identity is shared by all representations

Metadata Objects, Runtime Objects and Persistent Objects represent the same Domain Object through a common Object Identity.

---

## Identity is unique

Every Domain Object possesses exactly one Object Identity.

No two Domain Objects share the same identity.

---

## Identity is independent of persistence

Object Identity exists regardless of whether the Domain Object is persistent.

Temporary Runtime Objects may also possess Object Identity.

---

# 4. Architectural Identity Model

Conceptually:

```
                Object Identity

                       │

      ┌────────────────┼────────────────┐

      ▼                ▼                ▼

Metadata Object   Runtime Object   Persistent Object
```

Object Identity connects all architectural representations of the same Domain Object.

---

# 5. Identity Creation

Object Identity is established when a Domain Object is created.

The Runtime is responsible for assigning Object Identity according to platform rules.

The identity creation mechanism is implementation-independent.

---

# 6. Identity Lifetime

Object Identity exists for the complete lifetime of the Domain Object.

Identity remains valid throughout:

- object creation;
- runtime execution;
- persistence;
- object restoration;
- object disposal.

---

# 7. Identity Ownership

Object Identity belongs to the Domain Object.

Neither Runtime nor Storage owns Object Identity.

They only maintain representations associated with it.

---

# 8. Identity Equality

Two Domain Objects are considered identical only if they share the same Object Identity.

Equality based on Object State or business attributes is outside the scope of Object Identity.

---

# 9. Identity and References

Object References connect Domain Objects through Object Identity.

Reference Resolution uses Object Identity to obtain an accessible runtime representation of the target Domain Object.

---

# 10. Identity and Persistence

Storage preserves Object Identity independently of the storage implementation.

Persistent representations shall not redefine or replace Object Identity.

---

# 11. Identity Across Runtime Contexts

A Domain Object preserves its Object Identity regardless of the Runtime Context in which it executes.

Runtime Context influences execution but never alters identity.

---

# 12. Extensibility

The architecture permits different identifier implementations while preserving a common Object Identity model.

Possible implementations include:

- UUID;
- ULID;
- sequential identifiers;
- distributed identifiers.

The architectural model remains unchanged regardless of the chosen implementation.

---

# 13. Relationship to Other Subsystems

Object Identity is a foundational architectural concept used throughout the platform.

```
Metadata

      │

      ▼

Object Identity

 ┌────┼────┬────┬────┐

 ▼    ▼    ▼    ▼    ▼

Runtime Storage Query Events Transactions
```

Each subsystem relies on Object Identity without owning it.

---

# Appendix A. Identity Lifecycle

```
Domain Object Created

        │

        ▼

Object Identity Assigned

        │

        ▼

Runtime Execution

        │

        ▼

Persistent Representation

        │

        ▼

Object Disposal
```

Object Identity remains unchanged throughout the lifetime of the Domain Object.

---

# Appendix B. Architectural Responsibilities

| Concept | Responsibility |
|---------|----------------|
| Object Identity | Immutable architectural identity |
| Domain Object | Business entity owning the identity |
| Runtime Object | Executable representation using the identity |
| Persistent Object | Durable representation preserving the identity |
| Object Reference | Architectural relationship based on identity |

Object Identity provides the stable foundation connecting every architectural representation of a Domain Object.