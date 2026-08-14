# METADATA_MODEL

## Status

Planned

## Baseline

implementation-0.3

---

# 1. Purpose

The purpose of the Metadata Model is to define the canonical representation of business object structure within the AcCoreD Platform.

Metadata acts as the boundary between Definitions and Runtime.

Definitions describe intent.

Metadata describes structure.

Runtime provides behavior.

The Metadata Model establishes a stable, immutable and runtime-independent representation of business objects that can be consumed by all platform components.

---

# 2. Architectural Position

The Metadata Layer occupies the central position within the platform architecture.

```text
Definition Layer
        ↓
Compiler Layer
        ↓
Metadata Layer
        ↓
Registry Layer
        ↓
Runtime Resolver
        ↓
Runtime Layer
```

Metadata is produced by compilers and consumed by runtime objects.

Metadata never depends on runtime implementation.

---

# 3. Design Principles

## Metadata Is the Source of Structure

The structural description of a business object is represented exclusively by metadata.

Runtime objects must not introduce structural information independently.

---

## Runtime Independence

Metadata must be usable without any runtime implementation.

Metadata objects may be inspected, validated, registered and documented without creating runtime objects.

---

## Immutability

Compiled metadata objects are immutable.

Any structural change requires recompilation from definitions.

---

## Determinism

Identical definitions must always produce identical metadata.

Compiler execution must not depend on external state.

---

## Platform Consistency

All business object types use the same metadata principles.

Catalogs, Documents, Registers and Reports differ by metadata composition rather than by architectural approach.

---

# 4. Metadata Architecture

Metadata is produced through compilation.

```text
Definition
        ↓
Compiler
        ↓
Metadata
```

Metadata becomes the canonical representation of the object for the remainder of its lifecycle.

Neither Runtime nor Registry operate directly on definitions.

---

# 5. Metadata Composition

Every metadata object consists of a common set of structural components.

```text
Metadata
    ├── Identity
    ├── System Fields
    ├── Attributes
    ├── Validation Rules
    └── Version Information
```

Specific metadata object types may introduce additional components.

---

# 6. Metadata Identity

Every metadata object possesses a unique identity within the Metadata Registry.

Identity is used for:

* registration;
* lookup;
* runtime resolution;
* dependency tracking;
* reference validation.

Conceptually:

```text
Metadata Identity
    ├── Object Type
    ├── Name
    └── Version
```

The exact implementation is defined by the Registry Layer.

---

# 7. Catalog Metadata

Implementation-0.3 introduces Catalog Metadata as the first rich metadata object.

Conceptually:

```text
Catalog Metadata
    ├── Identity
    ├── System Fields
    ├── Attributes
    ├── Validation Rules
    └── Version Information
```

Catalog Metadata serves as the reference implementation for future metadata object types.

---

# 8. Attributes

Attributes describe business data fields.

Attributes are defined through the Attribute Model.

Examples:

```text
code
name
unit
weight
price
```

Metadata stores compiled attribute descriptions rather than definition objects.

Attributes are part of metadata composition.

---

# 9. System Fields

System fields are platform-managed attributes automatically injected during compilation.

Examples:

```text
id
created_at
updated_at
deleted
version
```

System fields are not authored by configuration developers.

They are introduced by the platform.

The complete model is described in SYSTEM_FIELDS_MODEL.md.

---

# 10. Validation Rules

Validation rules describe structural constraints associated with metadata.

Examples:

```text
Required

Unique

MaxLength

ReferenceIntegrity
```

Validation rules are represented as metadata.

Validation execution is outside the scope of implementation-0.3.

The complete model is described in VALIDATION_MODEL.md.

---

# 11. Metadata Lifecycle

Metadata follows a controlled lifecycle.

```text
Definition
        ↓
Compilation
        ↓
Metadata
        ↓
Registration
        ↓
Runtime Resolution
        ↓
Runtime Consumption
```

Metadata remains unchanged throughout this lifecycle.

Any modification requires recompilation.

---

# 12. Metadata Registration

Metadata objects are registered in the Metadata Registry.

The Registry provides:

* identity management;
* uniqueness enforcement;
* lookup services;
* dependency discovery;
* runtime resolution support.

The Registry stores metadata rather than definitions.

---

# 13. Metadata Resolution

Runtime objects are resolved from metadata identities.

Conceptually:

```text
Metadata Identity
        ↓
Registry Lookup
        ↓
Metadata Object
        ↓
Runtime Resolver
        ↓
Runtime Object
```

Runtime resolution is based entirely on metadata.

Runtime must not depend on definition artifacts.

---

# 14. Metadata Dependencies

Metadata objects may depend on other metadata objects.

Example:

```text
Assortment
    └── unit → MeasureUnits
```

Such dependencies are expressed through metadata references.

Dependency resolution is performed through the Registry Layer.

Metadata objects must not contain direct runtime references.

---

# 15. Metadata Immutability

Immutability is a core architectural requirement.

Once compiled:

* attributes cannot be added;
* attributes cannot be removed;
* validation rules cannot be modified;
* identities cannot be changed.

Structural changes require creation of a new metadata instance through recompilation.

---

# 16. Metadata Versioning

Metadata supports version information.

Versioning exists to support:

* future migrations;
* compatibility checks;
* deployment control;
* metadata evolution.

Implementation-0.3 introduces version awareness only.

Full metadata migration support is outside the scope of this phase.

---

# 17. Metadata Ownership

Metadata objects belong to the platform.

Runtime objects consume metadata.

Definitions generate metadata.

Ownership boundaries:

```text
Definitions
        ↓
produce
        ↓
Metadata
        ↓
consumed by
        ↓
Runtime
```

Metadata is never owned by Runtime.

---

# 18. Future Metadata Types

The Metadata Model is designed to support additional metadata categories.

Future metadata types include:

```text
Document Metadata

Register Metadata

Report Metadata

Workflow Metadata

Integration Metadata

Security Metadata
```

All future metadata types should reuse the principles established by this document.

---

# 19. Metadata Layer Responsibilities

The Metadata Layer is responsible for:

* structural representation;
* object identity;
* attribute description;
* validation description;
* dependency declaration;
* version information.

The Metadata Layer is not responsible for:

* runtime behavior;
* persistence;
* user interface;
* business execution;
* validation execution.

---

# 20. Architectural Outcome

The Metadata Model establishes a common structural language for the entire AcCoreD Platform.

After implementation-0.3, business objects should be represented as immutable metadata structures independent of runtime implementation details.

This model becomes the foundation for all future platform object types and serves as the central architectural contract between Definitions, Registry and Runtime.
