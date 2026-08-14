# RUNTIME_METADATA_API

## Status

Planned

## Baseline

implementation-0.3

---

# 1. Purpose

The purpose of the Runtime Metadata API is to define how runtime components access metadata produced by the Metadata Layer.

The Runtime Metadata API provides a stable contract between Runtime and Metadata while preserving the architectural separation established by the AcCoreD Platform.

Runtime components consume metadata.

They never consume definitions directly.

---

# 2. Architectural Position

The Runtime Metadata API is the boundary between Runtime Layer and Metadata Layer.

```text id="3om0oq"
Definition Layer
        ↓
Compiler Layer
        ↓
Metadata Layer
        ↓
Registry Layer
        ↓
Runtime Metadata API
        ↓
Runtime Layer
```

The API provides controlled access to metadata structures without exposing compiler implementation details.

---

# 3. Design Principles

## Metadata-Centric

Runtime operates on metadata.

Definitions are not available through the Runtime Metadata API.

---

## Read-Only Access

Metadata exposed through the Runtime API is immutable.

Runtime components may inspect metadata but may not modify it.

---

## Runtime Independence

Metadata remains independent of runtime implementation.

The API is a consumer contract rather than an ownership boundary.

---

## Stable Contract

The Runtime Metadata API should remain stable even when compiler internals evolve.

---

## Consistency

The same access patterns should apply to all metadata-driven object types.

---

# 4. Runtime Metadata Flow

Metadata reaches runtime through the standard platform pipeline.

```text id="oflkv1"
Definition
        ↓
Compiler
        ↓
Metadata
        ↓
Registry
        ↓
Resolver
        ↓
Runtime
```

The Runtime Metadata API begins after runtime resolution.

---

# 5. Runtime Metadata Access

Runtime objects access metadata through explicit API methods.

Conceptually:

```text id="0w4hr2"
Runtime Object
        ↓
Metadata API
        ↓
Metadata
```

Direct access to compiler artifacts is prohibited.

---

# 6. Metadata Identity Access

Runtime components must be able to access metadata identity information.

Conceptually:

```text id="t2m2md"
runtime.metadata_identity()
```

The returned information may include:

```text id="owq06r"
Object Type

Name

Version
```

Identity access supports diagnostics, tracing and dependency resolution.

---

# 7. Attribute Access

Runtime components must be able to enumerate metadata attributes.

Conceptually:

```text id="h6ctgr"
runtime.attributes()
```

Expected result:

```text id="1ndqu2"
Attribute Metadata Collection
```

The API returns metadata rather than runtime values.

---

# 8. Individual Attribute Access

Runtime components must be able to retrieve a specific attribute.

Conceptually:

```text id="h0j2sp"
runtime.attribute("name")
```

Expected result:

```text id="zw5ngd"
Attribute Metadata
```

If the attribute does not exist the implementation should return a controlled error.

---

# 9. Attribute Discovery

Runtime components must support metadata inspection.

Examples:

```text id="2dgv2d"
List Attributes

Check Attribute Existence

Inspect Attribute Type

Inspect Attribute Metadata
```

The Runtime Metadata API supports introspection.

---

# 10. System Field Access

Runtime components must be able to inspect platform-managed fields.

Conceptually:

```text id="f9v4mk"
runtime.system_fields()
```

Expected result:

```text id="x5sruv"
System Field Metadata Collection
```

System fields are exposed through metadata but remain platform-owned.

---

# 11. Validation Rule Access

Runtime components must be able to inspect validation metadata.

Conceptually:

```text id="m00s0z"
runtime.validation_rules()
```

Expected result:

```text id="pww0o7"
Validation Metadata Collection
```

The API exposes validation descriptions only.

Validation execution remains a separate concern.

---

# 12. Metadata Navigation

Runtime components must be able to navigate metadata structure.

Examples:

```text id="j4dgw5"
Metadata
    ↓
Attributes

Metadata
    ↓
System Fields

Metadata
    ↓
Validation Rules
```

Navigation is read-only.

---

# 13. Reference Metadata Access

Runtime components must be able to inspect reference attributes.

Conceptually:

```text id="elc1bo"
runtime.attribute("unit")
```

Expected metadata may include:

```text id="vpp5rf"
Reference Type

Target Metadata

Reference Information
```

Reference resolution behavior is outside the scope of implementation-0.3.

---

# 14. Runtime Metadata Isolation

Runtime components must never access:

```text id="mqxehd"
Definitions

Compiler Internals

Compiler State

Compilation Context
```

Only compiled metadata is visible.

This separation is mandatory.

---

# 15. Registry Independence

Runtime objects must not interact directly with registry internals.

Conceptually:

```text id="11y5iy"
Registry
        ↓
Resolver
        ↓
Runtime
```

After resolution, runtime operates exclusively through metadata APIs.

---

# 16. Error Handling

Metadata access failures must be deterministic.

Examples:

```text id="c6sx7v"
Unknown Attribute

Missing Metadata

Invalid Metadata Identity
```

Errors must be explicit and predictable.

Silent failures are not permitted.

---

# 17. Extensibility

The Runtime Metadata API is expected to support future metadata types.

Examples:

```text id="ysx20m"
Document Metadata

Register Metadata

Report Metadata

Workflow Metadata
```

The same access patterns should apply wherever possible.

---

# 18. Runtime Responsibilities

Runtime components are responsible for:

* metadata inspection;
* metadata navigation;
* metadata consumption;
* runtime behavior.

Runtime components are not responsible for:

* metadata creation;
* metadata compilation;
* metadata registration;
* metadata mutation.

---

# 19. Architectural Constraints

The following constraints are mandatory:

```text id="0k33av"
Runtime depends on Metadata.

Metadata does not depend on Runtime.

Runtime does not depend on Compiler.

Runtime does not depend on Definitions.

Metadata remains immutable.
```

These constraints preserve architectural separation.

---

# 20. Future Extensions

Future versions of the Runtime Metadata API may introduce:

```text id="wtgkzh"
Metadata Query API

Reference Resolution API

Schema Navigation API

Validation Execution Integration

Dynamic Runtime Services
```

Such extensions must remain compatible with the principles defined in this document.

---

# 21. Architectural Outcome

The Runtime Metadata API establishes a stable and explicit contract between Runtime and Metadata.

After implementation-0.3 runtime components will be capable of inspecting attributes, system fields and validation metadata without any dependency on definitions or compiler internals.

This API becomes the primary mechanism through which runtime behavior is driven by metadata and represents a critical step toward a fully metadata-driven platform architecture.
