# PHASE 2 — RUNTIME METADATA API

## Status

Implemented

## Scope

Phase 2 — Runtime Metadata API

The current implementation provides the Runtime Metadata API for `CatalogRuntime`.

The implemented API covers metadata identity, attribute enumeration, individual attribute lookup, and system field access.

Additional metadata inspection capabilities may be introduced in later phases.

## Baseline

Phase 2 Runtime Metadata API

## Purpose

The Runtime Metadata API defines the metadata contract consumed by
runtime objects after metadata compilation and runtime resolution.

The API establishes the boundary between Runtime and Metadata.

Runtime components consume compiled metadata.

They do not consume configuration definitions or compiler internals.

---

# 1. Architectural Position

The Runtime Metadata API is positioned after metadata compilation and
runtime resolution.

```text
Configuration Definition
        ↓
MetadataCompiler
        ↓
CatalogMetadata
        ↓
MetadataRegistry
        ↓
RuntimeResolver
        ↓
CatalogRuntime
        ↓
CatalogMetadata
The runtime object operates on compiled metadata.

The registry and resolver belong to the metadata-to-runtime binding
process and are not part of the runtime object's metadata contract.

# 2. Current Runtime Metadata Contract

The current Phase 2 runtime metadata contract is represented by
CatalogMetadata.

CatalogRuntime
      │
      ▼
CatalogMetadata
      │
      ├── identifier
      ├── metadata_type
      ├── name
      ├── source_definition_id
      ├── normalized_content
      ├── system_fields
      └── attributes

CatalogMetadata is immutable.

Runtime components may inspect the metadata but must not modify it.

# 3. Metadata Identity

CatalogMetadata provides metadata identity information through the
following metadata fields:

identifier;
metadata_type;
name;
source_definition_id.

These values identify the metadata object and its source definition.

The runtime does not use the original definition object.

# 4. Attribute Metadata

CatalogMetadata.attributes contains the compiled attribute metadata
for the catalog.

Each item is represented by AttributeMetadata.

CatalogMetadata
      ↓
attributes
      ↓
AttributeMetadata

AttributeMetadata currently exposes:

name;
attribute_type;
nullable;
default_value;
description;
reference_target.

The metadata describes the attribute.

It does not contain runtime attribute values.

# 5. Runtime Metadata Access

Runtime objects access metadata through explicit runtime-facing API methods.

For the current Phase 2 implementation, `CatalogRuntime` provides the Runtime Metadata API.

Conceptually:

```text
Runtime Object
        ↓
Runtime Metadata API
        ↓
CatalogMetadata

The Runtime Metadata API exposes compiled metadata only.

Direct access to Definitions, compiler artifacts, compiler state, compilation context, and registry internals is prohibited.

# 6. Metadata Identity Access

Runtime components must be able to access metadata identity information.

The current implementation provides:

```text
runtime.metadata_identity()

For CatalogRuntime, the method returns the identifier of the compiled metadata.

Identity access supports diagnostics, tracing, and dependency resolution.

The current API does not expose a separate runtime-owned identity for the metadata object.

# 7. Attribute Access

Runtime components must be able to enumerate metadata attributes.

The current implementation provides:

```text
runtime.attributes()

Expected result:

tuple[AttributeMetadata, ...]

The returned objects describe metadata and do not contain runtime business values.

The returned collection is read-only.

# 8. Individual Attribute Access

Runtime components must be able to retrieve a specific attribute.

The current implementation provides:

```text
runtime.attribute("name")

Expected result:

AttributeMetadata

If the requested attribute does not exist, the implementation raises MetadataLookupError.

Metadata lookup failures are explicit and deterministic.

# 9. Attribute Ordering

Attribute order is preserved during compilation.

The order of CatalogDefinition.attributes is transferred to
CatalogMetadata.attributes.

Therefore metadata consumers may rely on deterministic attribute
ordering within a compiled metadata object.

Therefore metadata consumers may rely on deterministic attribute
ordering within a compiled metadata object.

Attribute lookup by name is part of the current Runtime Metadata API
and is provided by `CatalogRuntime.attribute(name)`.

# 10. System Field Access

Runtime components must be able to inspect platform-managed fields.

The current implementation provides:

```text
runtime.system_fields()

Expected result:

tuple[SystemFieldMetadata, ...]

System fields are exposed through metadata but remain platform-owned.

The Runtime Metadata API provides read-only access to system-field metadata.

# 11. Validation Metadata Access

Validation metadata access is not part of the currently implemented Runtime Metadata API.

The metadata model currently provides validation through the Validation Layer rather than through a dedicated runtime validation-metadata collection.

A future Runtime Metadata API may expose validation metadata through an operation such as:

```text
runtime.validation_rules()

Such an API is outside the current Phase 2 implementation scope.

Validation execution remains a separate concern.


# 12. Reference Metadata Access

Runtime components must be able to inspect reference attributes through normal attribute metadata access.

For example:

```text
runtime.attribute("unit")

may return:

AttributeMetadata(
    attribute_type=REFERENCE,
    reference_target="MeasureUnits"
)

Reference metadata inspection is part of the current metadata model.

Reference resolution behavior is outside the scope of the current Runtime Metadata API implementation.

# 13. Runtime Metadata Isolation

Runtime objects must not depend on:

Definition
MetadataCompiler
Compiler State
Compilation Context

The runtime receives compiled metadata.

The architectural dependency is:

Runtime
   ↓
Metadata

and not:

Runtime
   ↓
Compiler
   ↓
Definition

This separation is mandatory.

# 14. Registry Independence

Runtime objects must not interact directly with registry internals.

The runtime resolution flow is:

```text
Registry
    ↓
Resolver
    ↓
Runtime

After resolution, CatalogRuntime operates on the resolved CatalogMetadata.

The runtime object does not retain or expose the MetadataRegistry.

# 15. Runtime Object Contract

The current Phase 2 runtime object for catalogs is:

CatalogRuntime

Its metadata contract is:

CatalogRuntime.metadata

which contains a CatalogMetadata instance.

The runtime object does not recreate, transform, or reinterpret the
definition.

The compiled metadata is the authoritative metadata representation
available to the runtime object.

# 16. Read-Only Metadata

Metadata objects are immutable.

The current metadata model uses immutable dataclasses.

This applies to:

Metadata;
CatalogMetadata;
AttributeMetadata;
SystemFieldMetadata.

Runtime components therefore consume metadata as read-only structures.

Metadata mutation is outside the Runtime Metadata API.

# 17. Current API Surface

The currently implemented runtime metadata surface is intentionally
minimal.

CatalogRuntime
    └── metadata: CatalogMetadata


CatalogMetadata
    ├── identifier
    ├── metadata_type
    ├── name
    ├── source_definition_id
    ├── normalized_content
    ├── system_fields
    └── attributes

The current runtime metadata surface is intentionally minimal.

CatalogRuntime
    ├── metadata: CatalogMetadata
    ├── metadata_identity()
    ├── attributes()
    ├── attribute(name)
    └── system_fields()

The following operations are explicitly outside the current Phase 2
contract:

runtime.has_attribute(name)
runtime.validation_rules()

The underlying metadata collections are available through the implemented
Runtime Metadata API operations.

The underlying metadata collections already exist where implemented,
but dedicated runtime convenience methods are not yet part of the
Phase 2 contract.

# 18. Implemented API Surface

The following Runtime Metadata API operations are implemented for `CatalogRuntime`:

| Operation | Status |
|---|---|
| `metadata_identity()` | Implemented |
| `attributes()` | Implemented |
| `attribute(name)` | Implemented |
| `system_fields()` | Implemented |
| `validation_rules()` | Planned |
| Reference resolution | Out of scope |

The implemented operations are read-only.

This table defines the current Phase 2 implementation boundary.

Future runtime object types may expose the same metadata access pattern while providing object-specific metadata capabilities.

# 19. Error Handling

Metadata and runtime resolution errors must remain explicit and
deterministic.

The current runtime boundary includes controlled handling of:

missing metadata;
unsupported metadata/runtime types;
invalid runtime resolution requests.

Attribute-level lookup failures are part of the current runtime API.

If `CatalogRuntime.attribute(name)` cannot find the requested attribute,
it raises `MetadataLookupError`.

Lookup failures are explicit and deterministic.

Current runtime metadata lookup errors include:

* missing attribute;
* invalid metadata lookup request.

Future lookup APIs must define explicit behavior for unknown attributes.

# 20. Extensibility

The Runtime Metadata API is designed to support future metadata types.

Potential future metadata types include:

DocumentMetadata
RegisterMetadata
ReportMetadata
WorkflowMetadata

The same architectural principle should remain applicable:

Metadata
    ↓
Runtime Object

Runtime objects consume compiled metadata without depending on the
configuration definition or compiler implementation.

# 21. Responsibilities
Runtime is responsible for
consuming metadata;
exposing runtime behavior;
using metadata to drive runtime behavior;
preserving metadata/runtime separation.
Runtime is not responsible for
creating metadata;
compiling definitions;
registering metadata;
validating definitions;
mutating metadata.

# 22. Architectural Constraints

The following constraints are mandatory:

Runtime depends on Metadata.


Metadata does not depend on Runtime.


Runtime does not depend on Compiler.


Runtime does not depend on Definitions.


Runtime does not depend on Registry internals.


Metadata remains immutable.

These constraints preserve the separation established by the Metadata
and Runtime architectures.

# 23. Phase 2 Boundary

The current Runtime Metadata API intentionally stops at the metadata
consumption boundary.

Phase 2 establishes:

Definition
    ↓
Compilation
    ↓
Metadata
    ↓
Registration
    ↓
Resolution
    ↓
Runtime

It does not yet establish:

Runtime Validation API
Reference Resolution API
Runtime Schema Query API
Runtime Data Access API

Those capabilities belong to subsequent implementation stages.

# 24. Acceptance Criteria

The Runtime Metadata API is considered implemented for the current
Phase 2 scope when:

a catalog definition can be compiled into CatalogMetadata;
the metadata can be registered;
the metadata can be resolved into CatalogRuntime;
CatalogRuntime exposes its compiled metadata;
attributes are available through CatalogMetadata.attributes;
system fields are available through CatalogMetadata.system_fields;
CatalogRuntime exposes metadata identity;
CatalogRuntime can enumerate attributes;
CatalogRuntime can retrieve an attribute by name;
CatalogRuntime can enumerate system fields;
unknown attribute lookup raises MetadataLookupError;
reference metadata is preserved;
reference metadata is preserved;
runtime has no dependency on definitions;
runtime has no dependency on compiler internals;
metadata remains immutable;
the Phase 2 vertical slice passes.

# 25. Architectural Outcome

Phase 2 establishes the first concrete metadata-driven runtime boundary.

The resulting architecture is:

Configuration Definition
        ↓
MetadataCompiler
        ↓
CatalogMetadata
        ↓
MetadataRegistry
        ↓
RuntimeResolver
        ↓
CatalogRuntime
        ↓
CatalogMetadata

The runtime no longer requires knowledge of the configuration definition
that produced it.

Compiled metadata becomes the authoritative contract between the
metadata layer and the runtime layer.

This provides the foundation for future runtime APIs for attributes,
validation, references, documents, registers and reporting.