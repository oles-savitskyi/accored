# SYSTEM_FIELDS_MODEL

## Status

Planned

## Baseline

implementation-0.3

---

# 1. Purpose

The purpose of the System Fields Model is to define platform-managed fields that are automatically available in metadata-driven business objects.

System fields provide a common foundation for identity, lifecycle management, auditing and version control across the AcCoreD Platform.

Unlike business attributes, system fields are not defined by configuration developers.

They are introduced by the platform during metadata compilation.

---

# 2. Architectural Position

System fields are a component of the Metadata Layer.

```text id="p61z4m"
Definition
        ↓
Compiler
        ↓
System Field Injection
        ↓
Metadata
```

System fields become part of the compiled metadata structure and are available to all runtime components.

---

# 3. Design Principles

## Platform Ownership

System fields are owned and managed by the platform.

Configuration definitions cannot create, remove or redefine system fields.

---

## Consistency

The same system field model must be applied consistently across all metadata-driven object types.

---

## Immutability

Compiled system field metadata is immutable.

Any change requires recompilation.

---

## Runtime Independence

System field structure is represented in metadata and remains independent of runtime implementation.

---

## Extensibility

Additional system fields may be introduced in future platform versions without changing the underlying model.

---

# 4. System Field Architecture

System fields are represented using the same metadata principles as business attributes.

Conceptually:

```text id="mtt2w9"
Metadata
    ├── System Fields
    └── Business Attributes
```

From the Runtime perspective both are accessible through metadata.

The distinction exists at the ownership and lifecycle levels.

---

# 5. Categories of System Fields

Implementation-0.3 introduces four categories:

```text id="9z3g9r"
Identity Fields

Audit Fields

Lifecycle Fields

Version Fields
```

---

# 6. Identity Fields

Identity fields uniquely identify an object instance.

Identity fields are mandatory.

Implementation-0.3 defines:

```text id="1b44ah"
id
```

Purpose:

* object identity;
* references;
* runtime lookup;
* persistence integration;
* audit tracking.

The exact identity format is defined elsewhere by platform architecture.

---

# 7. Audit Fields

Audit fields track object creation and modification history.

Implementation-0.3 defines:

```text id="z8yx8x"
created_at

updated_at
```

Purpose:

* traceability;
* diagnostics;
* synchronization;
* future audit functionality.

Audit behavior is outside the scope of implementation-0.3.

This document defines structure only.

---

# 8. Lifecycle Fields

Lifecycle fields describe the operational state of an object.

Implementation-0.3 defines:

```text id="d3l0d2"
deleted
```

Purpose:

* soft deletion;
* object visibility control;
* lifecycle tracking.

The field does not imply a specific deletion strategy.

It only defines the metadata representation.

---

# 9. Version Fields

Version fields support future concurrency and metadata evolution scenarios.

Implementation-0.3 defines:

```text id="6s3v9k"
version
```

Purpose:

* optimistic locking;
* change tracking;
* synchronization support;
* future migration scenarios.

Version management behavior is outside the scope of this phase.

---

# 10. Default System Field Set

The default system field set for implementation-0.3 is:

```text id="f98b8l"
id

created_at

updated_at

deleted

version
```

Every metadata-driven business object receives this set automatically unless explicitly excluded by future architectural rules.

---

# 11. System Field Injection

System fields are introduced by the Compiler Layer.

Conceptually:

```text id="7mwgki"
Definition
        ↓
Compiler
        ↓
Inject System Fields
        ↓
Metadata
```

Configuration definitions remain focused on business structure.

Platform concerns are added automatically.

---

# 12. System Fields and Attributes

System fields are not business attributes.

However, they are represented using the same metadata abstractions.

Conceptually:

```text id="2q6q9n"
Field Metadata
    ├── System Field
    └── Business Attribute
```

This allows runtime components to work with a unified field model.

---

# 13. System Field Visibility

System fields are part of metadata.

Runtime components may inspect them through metadata APIs.

Example:

```text id="u1df5q"
catalog.system_fields()
```

Visibility does not imply editability.

Ownership remains with the platform.

---

# 14. System Field Lifecycle

System fields follow the metadata lifecycle.

```text id="bjlwmh"
Definition
        ↓
Compilation
        ↓
System Field Injection
        ↓
Metadata
        ↓
Registration
        ↓
Runtime Access
```

No modification is allowed after metadata compilation.

---

# 15. System Field Metadata

After compilation each system field is represented as immutable metadata.

Conceptually:

```text id="mpd5to"
System Field Metadata
    ├── Name
    ├── Type
    ├── Category
    └── Description
```

Runtime components consume metadata rather than compiler artifacts.

---

# 16. System Field Ownership

System fields belong to the platform.

Ownership boundaries:

```text id="15myxt"
Platform
        ↓
System Fields

Configuration
        ↓
Business Attributes
```

This separation prevents configuration definitions from modifying platform infrastructure.

---

# 17. Applicability

The System Fields Model is intended to be shared by:

```text id="7jznv7"
Catalog Metadata

Document Metadata

Register Metadata

Report Metadata

Workflow Metadata
```

Future metadata types should reuse the same system field architecture whenever applicable.

---

# 18. Future Extensions

The System Fields Model is expected to evolve.

Potential future additions include:

```text id="0z20k0"
created_by

updated_by

tenant_id

owner_id

archived

row_version

security_stamp
```

Such extensions must preserve backward compatibility with the core model.

---

# 19. Architectural Constraints

The following constraints apply:

* system fields are platform-owned;
* system fields are injected by compilers;
* system fields are immutable after compilation;
* runtime does not create system fields;
* definitions do not redefine system fields.

These constraints are mandatory for all metadata implementations.

---

# 20. Architectural Outcome

The System Fields Model establishes a uniform platform-wide mechanism for representing identity, audit, lifecycle and version information.

After implementation-0.3 every metadata-driven business object will contain a consistent set of platform-managed fields represented through immutable metadata.

This model provides the structural foundation for future persistence, auditing, synchronization and lifecycle management capabilities while preserving the separation between business definitions and platform infrastructure.
