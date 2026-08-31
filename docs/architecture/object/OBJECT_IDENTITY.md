# Object Identity

**Version:** 1.1
**Status:** Accepted / Implemented in progress

---

# 1. Purpose

The Object Identity architecture defines the immutable identity of Domain Objects within the AcCore platform.

Object Identity provides the immutable identity of an individual Object Instance. It is distinct from Metadata Identity and Configuration Identity. Storage may preserve Object Identity in a persistent representation, but does not own runtime identity.

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

Phase 4 uses the existing immutable ULID-backed `foundation.Identifier` as the technical representation. No separate `ObjectIdentity` value type is introduced.

---

## Identity is distinct from Metadata Identity

Metadata Identity identifies a metadata definition. Object Identity identifies an individual Object Instance. A Persistent Object may preserve Object Identity without redefining it.

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

The Object Creation Boundary is responsible for assigning Object Identity to newly created Object Instances.

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

Object Identity belongs to the Object Instance boundary.

`RuntimeResolver` resolves Object Types; `ObjectCreator` establishes identity for a new instance; Storage may preserve that identity in a Persistent Object.

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

The Phase 4 implementation intentionally standardizes on the existing ULID-backed `Identifier`. A separate identity wrapper is deferred unless a future requirement demonstrates the need.

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

Disposal terminates the runtime lifecycle of the Object Instance but does not redefine the Object Identity of the represented business object.

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

---

## Phase 4 Implementation Alignment

- `ObjectInstance.identity` is an immutable `Identifier`.
- Object Instance equality is based on identity, not state.
- Object Identity is independent of Metadata Identity and persistence.
- `ObjectCreator` generates identity for newly created instances.
