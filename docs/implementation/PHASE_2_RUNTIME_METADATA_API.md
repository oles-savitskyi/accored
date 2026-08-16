# PHASE 2 — RUNTIME METADATA API

## Status

Implementation

## Current Implementation Scope

The first implementation increment provides read-only access to:

* catalog metadata;
* metadata attributes;
* individual attributes;
* attribute existence;
* system fields.

Validation metadata, reference resolution, metadata versioning and
runtime data access are outside this implementation increment.

## Baseline

implementation-0.2

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

2. Current Runtime Metadata Contract

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

3. Metadata Identity

CatalogMetadata provides metadata identity information through the
following metadata fields:

identifier;
metadata_type;
name;
source_definition_id.

These values identify the metadata object and its source definition.

The runtime does not use the original definition object.

4. Attribute Metadata

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

5. Attribute Ordering

Attribute order is preserved during compilation.

The order of CatalogDefinition.attributes is transferred to
CatalogMetadata.attributes.

Therefore metadata consumers may rely on deterministic attribute
ordering within a compiled metadata object.

Attribute lookup by name is not currently a separate runtime API.

Such an API may be introduced later without changing the underlying
metadata model.

6. System Field Metadata

CatalogMetadata.system_fields contains the platform-defined system
fields of the catalog.

CatalogMetadata
      ↓
system_fields
      ↓
SystemFieldMetadata

System fields are platform-owned metadata.

They are not supplied by the Standard Configuration definition.

The current Phase 2 compiler provides the default catalog system field
set during metadata compilation.

7. Validation Metadata

Validation is currently performed during definition validation and
metadata compilation.

The current CatalogMetadata model does not yet expose a dedicated
validation metadata collection.

Therefore validation rules are not part of the current Runtime Metadata
API.

Future phases may introduce explicit validation metadata.

Such an extension must preserve the separation between:

Validation Metadata
        ≠
Validation Execution
8. Reference Metadata

Reference attributes are represented by AttributeMetadata.

For a reference attribute:

attribute_type = REFERENCE
reference_target = <target metadata name>

The current runtime metadata contract therefore exposes reference
information as metadata.

Reference resolution itself is outside the current Phase 2 scope.

The Runtime Metadata API must not imply that reference resolution is
already implemented.

9. Runtime Metadata Isolation

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

10. Registry and Resolver Independence

The runtime object does not interact directly with the metadata registry.

The current flow is:

MetadataRegistry
        ↓
RuntimeResolver
        ↓
CatalogRuntime

The resolver obtains metadata from the registry and creates the
appropriate runtime object.

After construction, CatalogRuntime operates through its metadata
reference.

Registry internals are not exposed through the runtime object.

11. Runtime Object Contract

The current Phase 2 runtime object for catalogs is:

CatalogRuntime

Its metadata contract is:

CatalogRuntime.metadata

which contains a CatalogMetadata instance.

The runtime object does not recreate, transform, or reinterpret the
definition.

The compiled metadata is the authoritative metadata representation
available to the runtime object.

12. Read-Only Metadata

Metadata objects are immutable.

The current metadata model uses immutable dataclasses.

This applies to:

Metadata;
CatalogMetadata;
AttributeMetadata;
SystemFieldMetadata.

Runtime components therefore consume metadata as read-only structures.

Metadata mutation is outside the Runtime Metadata API.

13. Current API Surface

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

No additional runtime metadata navigation API is required at this
stage.

In particular, the following are future extensions rather than current
contract requirements:

runtime.attribute(name)
runtime.has_attribute(name)
runtime.attributes()
runtime.system_fields()
runtime.validation_rules()

The underlying metadata collections already exist where implemented,
but dedicated runtime convenience methods are not yet part of the
Phase 2 contract.

14. Error Handling

Metadata and runtime resolution errors must remain explicit and
deterministic.

The current runtime boundary includes controlled handling of:

missing metadata;
unsupported metadata/runtime types;
invalid runtime resolution requests.

Attribute-level lookup errors are not currently part of the runtime API
because dedicated attribute lookup methods have not yet been introduced.

Future lookup APIs must define explicit behavior for unknown attributes.

15. Extensibility

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

16. Responsibilities
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
17. Architectural Constraints

The following constraints are mandatory:

Runtime depends on Metadata.


Metadata does not depend on Runtime.


Runtime does not depend on Compiler.


Runtime does not depend on Definitions.


Runtime does not depend on Registry internals.


Metadata remains immutable.

These constraints preserve the separation established by the Metadata
and Runtime architectures.

18. Phase 2 Boundary

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

Runtime Attribute API
Runtime Validation API
Reference Resolution API
Runtime Schema Query API
Runtime Data Access API

Those capabilities belong to subsequent implementation stages.

19. Acceptance Criteria

The Runtime Metadata API is considered implemented for the current
Phase 2 scope when:

a catalog definition can be compiled into CatalogMetadata;
the metadata can be registered;
the metadata can be resolved into CatalogRuntime;
CatalogRuntime exposes its compiled metadata;
attributes are available through CatalogMetadata.attributes;
system fields are available through CatalogMetadata.system_fields;
reference metadata is preserved;
runtime has no dependency on definitions;
runtime has no dependency on compiler internals;
metadata remains immutable;
the Phase 2 vertical slice passes.
20. Architectural Outcome

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