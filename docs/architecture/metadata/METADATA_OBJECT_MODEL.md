# Metadata Object Model

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Metadata Object Model defines the universal structural model used to represent every metadata element within the AcCore platform.

All metadata objects share a common architectural foundation regardless of their functional purpose.

The object model provides:

- a unified type system;
- hierarchical organization;
- ownership semantics;
- reference semantics;
- extensibility;
- consistent traversal and validation.

---

# 2. Design Goals

The Metadata Object Model is designed to provide:

- consistency across all metadata types;
- minimal architectural complexity;
- strong typing;
- deterministic behavior;
- extensibility;
- efficient traversal;
- immutable runtime representation.

---

# 3. Architectural Principles

## Universal object model

Every metadata element is represented as a Metadata Object.

There are no special-case objects outside the object model.

---

## Strong typing

Every metadata object has exactly one metadata type.

Object behavior is determined by its type.

---

## Hierarchical ownership

Metadata objects form an ownership hierarchy.

Each object has exactly one owner except the root configuration object.

Ownership defines lifecycle.

---

## Reference independence

References never imply ownership.

Objects may reference any compatible metadata object without affecting its lifecycle.

---

## Immutable identity

Each metadata object has a stable identity throughout its lifetime.

Object identity never changes after publication.

---

## Immutable structure

After publication the metadata hierarchy cannot be modified.

---

# 4. Core Object Hierarchy

The Metadata Object Model consists of a small number of fundamental abstractions.

```
MetadataObject
        │
        ▼
MetadataDefinition
        │
 ┌──────┼───────────────┐
 │      │               │
 ▼      ▼               ▼
Container Definition  Member
```

Concrete metadata types derive from these abstractions.

---

# 5. MetadataObject

MetadataObject is the root abstraction of the entire metadata system.

Every metadata object provides a common set of capabilities.

Typical responsibilities include:

- identity;
- metadata type;
- owner;
- qualified name;
- annotations;
- documentation;
- lifecycle state.

MetadataObject contains no business-specific behavior.

---

# 6. MetadataDefinition

MetadataDefinition represents any named metadata definition.

Examples include:

- Catalog
- Document
- Register
- Report
- Enumeration
- Role

Definitions may own other metadata objects.

---

# 7. Containers

Containers organize child metadata objects.

Examples:

```
Configuration

Catalogs

Documents

Reports

Registers
```

Containers provide organization but contain little or no business behavior.

---

# 8. Members

Members describe components belonging to another metadata object.

Examples include:

- attributes;
- commands;
- forms;
- indexes;
- actions;
- parameters.

Members cannot exist independently.

Their lifecycle is determined by the owning definition.

---

# 9. Ownership Model

Ownership forms the structural hierarchy.

```
Configuration
        │
        ▼
Catalog
        │
        ▼
Attribute
```

Properties of ownership:

- exactly one owner;
- recursive lifecycle;
- unique position in hierarchy;
- deterministic traversal.

Ownership is represented as a tree.

---

# 10. Reference Model

References connect metadata objects without ownership.

```
Document

    │

references

    ▼

Catalog
```

Reference properties:

- independent lifecycle;
- cross-tree links;
- validated during loading;
- immutable after publication.

References transform the ownership tree into a metadata graph.

---

# 11. Object Identity

Every metadata object has a unique identity.

Identity is independent from:

- display name;
- localization;
- storage representation;
- runtime object instances.

Identity remains stable throughout the object's lifetime.

---

# 12. Object Naming

Metadata objects may expose multiple naming mechanisms.

Typical names include:

- internal name;
- qualified name;
- display name;
- localized name.

Only internal identity is used for structural consistency.

---

# 13. Metadata Types

Each object has exactly one metadata type.

Examples include:

```
Configuration

Catalog

Document

Register

Report

Role

Enumeration

Attribute

Form

Command
```

Metadata types define:

- allowed children;
- allowed references;
- validation rules;
- runtime interpretation.

---

# 14. Object Relationships

The model defines several relationship categories.

### Ownership

Structural containment.

---

### Reference

Logical dependency.

---

### Inheritance

Behavior reuse.

Optional.

---

### Association

Semantic relationship.

Optional.

---

Only ownership is mandatory.

Other relationship types depend on metadata type.

---

# 15. Traversal Model

Metadata supports deterministic traversal.

Traversal may follow:

- ownership hierarchy;
- reference graph;
- dependency graph.

Traversal algorithms are independent from concrete metadata types.

---

# 16. Validation Constraints

Every metadata object satisfies common constraints.

Examples:

- valid identity;
- valid owner;
- valid metadata type;
- unique name within owner;
- valid references.

Additional constraints are defined by specific metadata types.

---

# 17. Runtime Representation

After publication:

- all objects become immutable;
- references are resolved;
- ownership hierarchy is fixed;
- object identity is stable.

Runtime never modifies metadata objects.

---

# 18. Extensibility

New metadata types may be introduced by extending the object model.

Existing abstractions remain unchanged.

This allows platform evolution without architectural redesign.

---

# 19. Relationship to Other Subsystems

The Metadata Object Model is used by:

- Metadata Compiler;
- Validator;
- Runtime;
- Storage;
- Security;
- UI;
- Query Engine;
- Reporting;
- Extension Framework.

All platform subsystems interact with metadata through this common object model.