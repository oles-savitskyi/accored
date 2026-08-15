# Phase 2 — Metadata Compiler v2

## Status

Implemented

## Implementation Status

Metadata Compiler v2 has been implemented and passed the Compiler v2
Review Gate.

The compiler currently supports:

* definition validation delegation;
* CatalogDefinition compilation;
* AttributeDefinition → AttributeMetadata transformation;
* standard catalog system-field injection;
* deterministic metadata construction;
* unsupported-definition rejection.

Validation metadata compilation is not implemented yet.

## Baseline

`implementation-0.2`

## Phase

Phase 2 — Metadata → Runtime

---

# 1. Purpose

Metadata Compiler v2 establishes the formal transformation boundary between
validated configuration definitions and runtime-independent metadata.

The compiler is responsible for deterministic transformation.

It is not responsible for defining validation rules, runtime behavior,
Standard Configuration semantics, or persistence.

The compiler transforms a validated Definition Model into an immutable
Metadata Model.

---

# 2. Architectural Position

The compiler participates in the following flow:

```text
Configuration Definition
        │
        ▼
Definition Validator
        │
        │ validated definition
        ▼
Metadata Compiler
        │
        │ deterministic transformation
        ▼
Metadata
        │
        ▼
Metadata Registry
        │
        ▼
Runtime Resolver
        │
        ▼
Runtime Object

3. Core Principle

The fundamental compiler rule is:

Metadata Compiler transforms validated definitions into immutable metadata
without introducing business semantics that are not present in the
Definition Model.

The compiler must not become a second validation layer.

Validation belongs to the Validation Model.

Compilation belongs to the Metadata Model.

Runtime behavior belongs to the Runtime Model.

4. Responsibilities

Metadata Compiler v2 is responsible for:

accepting supported Definition objects;
delegating definition validation to DefinitionValidator;
resolving the identity required for compilation;
transforming Definition fields into Metadata fields;
transforming attribute definitions into attribute metadata;
attaching standard system-field metadata through the System Fields provider;
preserving definition ordering where ordering is semantically observable;
producing immutable metadata;
producing deterministic compilation results.
5. Non-Responsibilities

Metadata Compiler v2 must not:

implement structural validation rules;
implement semantic validation rules;
duplicate Definition.validate() calls;
validate individual attributes independently;
contain Standard Configuration-specific business logic;
create runtime objects;
access persistence/storage;
register metadata in the registry;
resolve references between runtime objects;
execute workflows;
perform reporting logic;
calculate accounting values;
normalize metadata through undocumented rules.
6. Validation Boundary

Validation is performed before transformation.

The compiler delegates validation to:

DefinitionValidator

The intended flow is:

Definition
    │
    ▼
DefinitionValidator.validate()
    │
    ▼
MetadataCompiler

The compiler must not subsequently call:

definition.validate()

or:

attribute.validate()

as part of compilation.

This prevents duplicate validation and preserves a clear architectural boundary.

7. Supported Definitions

The current compiler supports:

CatalogDefinition

No additional Definition types are introduced by Compiler v2.

Unsupported definitions must fail explicitly.

The current expected behavior is:

TypeError

for unsupported definition types.

Future definition types may be added through explicit compiler support.

8. Compiler API

The public compiler contract is:

class MetadataCompiler:
    def compile(self, definition: Definition) -> CatalogMetadata:
        ...

The return type remains CatalogMetadata while Catalog is the only supported
metadata type.

The return type must not be generalized prematurely merely to anticipate
future Document, Register, or Report metadata.

9. Compilation Pipeline

For a CatalogDefinition, compilation follows:

CatalogDefinition
        │
        ▼
DefinitionValidator
        │
        ▼
require_identifier()
        │
        ▼
compile attributes
        │
        ▼
attach system fields
        │
        ▼
CatalogMetadata

Each stage has a distinct responsibility.

10. Identity Mapping

The definition identifier is preserved.

For a definition:

definition.identifier

the resulting metadata must satisfy:

metadata.identifier == definition.identifier

and:

metadata.source_definition_id == definition.identifier

The compiler must not generate a new identifier for metadata during compilation.

11. Name Mapping

The catalog name is preserved:

metadata.name == definition.name

The compiler must not modify, normalize, or otherwise reinterpret the name.

12. Attribute Mapping

Each:

AttributeDefinition

is transformed into:

AttributeMetadata

The following fields must be preserved:

name
attribute_type
nullable
default_value
description
reference_target

The transformation is one-to-one.

Example:

AttributeDefinition
        │
        ▼
AttributeMetadata

No business semantics are added during this transformation.

13. Attribute Ordering

The compiler must preserve the declaration order of attributes.

Given:

A
B
C

the resulting metadata must contain:

A
B
C

in the same order.

The compiler must not sort attributes alphabetically or by any other
criterion.

This guarantees that compilation does not silently change the declarative
configuration structure.

14. System Fields

Catalog system fields are supplied by:

default_catalog_system_fields()

The compiler does not hard-code the system-field definitions.

The compiler therefore depends on the System Fields Model rather than
duplicating it.

The resulting CatalogMetadata must contain the standard catalog system
fields defined by the current System Fields provider.

15. Normalized Content

Metadata.normalized_content is currently part of the metadata model.

Compiler v2 does not introduce an implicit normalization algorithm.

Unless a dedicated normalization mechanism is introduced, compilation leaves
the field at its defined default:

()

No undocumented canonicalization, sorting, serialization, or hashing is
performed merely to populate this field.

A future normalization mechanism must be specified separately.

16. Immutability

The compiler must produce immutable metadata objects.

The current metadata implementation uses:

@dataclass(frozen=True, slots=True)

Compiler v2 must not return mutable intermediate structures as part of the
public metadata model.

Collections exposed by metadata must use immutable representations such as:

tuple

where required by the Metadata Model.

17. Determinism

Compilation must be deterministic.

For the same definition:

Definition D

repeated compilation must produce equivalent metadata:

compile(D) == compile(D)

Determinism means:

no generated metadata identity;
no time-dependent values;
no random values;
no dependency on dictionary iteration order where semantic ordering
matters;
no hidden global state;
no environment-dependent transformation.
18. Standard Configuration Independence

The compiler belongs to the Platform.

It must not contain knowledge of Standard Configuration objects such as:

Assortment
Measure Units
Business Partners
Employees
Sales
Purchases

Standard Configuration provides Definitions.

The Platform compiler consumes Definitions generically.

The dependency direction is:

Standard Configuration
        │
        │ provides Definition
        ▼
Platform Metadata Compiler

not:

Platform Compiler
        │
        └── knows Standard Configuration
19. Compiler Structure

The implementation should separate type dispatch from type-specific
transformation.

Conceptually:

def compile(self, definition: Definition) -> CatalogMetadata:
    self._validator.validate(definition)


    if isinstance(definition, CatalogDefinition):
        return self._compile_catalog(definition)


    raise TypeError(...)

Catalog-specific transformation belongs to:

_compile_catalog()

Attribute transformation belongs to:

_compile_attribute()

The helper methods perform transformation only.

They must not perform validation.

20. Validation Delegation

MetadataCompiler accepts an optional validator:

MetadataCompiler(
    validator=...
)

This dependency injection mechanism is part of the testable compiler boundary.

The compiler must call:

validator.validate(definition)

exactly once per compilation attempt.

This permits validation behavior to be tested independently from transformation.

21. Error Semantics

Unsupported definitions must raise:

TypeError

Validation failures must propagate the validation error raised by the
DefinitionValidator.

The compiler must not silently convert validation failures into successful
metadata.

The compiler must not swallow validation exceptions.

22. Unit Test Requirements

Compiler v2 must provide tests for:

Validation delegation

The injected validator is called exactly once.

Unsupported definition

Unsupported definition types raise TypeError.

Identity preservation
identifier
source_definition_id

are preserved.

Name preservation

Catalog name is preserved.

Attribute mapping

All supported attribute fields are preserved.

Attribute ordering

Declaration order is preserved.

System fields

Default catalog system fields are attached.

Normalized content

Compilation does not introduce undocumented normalized content.

Determinism

Repeated compilation produces equivalent metadata.

Immutability

The resulting metadata remains immutable according to the Metadata Model.

23. Vertical Integration Requirement

Compiler v2 must remain compatible with the existing Phase 1 vertical flow:

Standard Definition
        ↓
Metadata Compiler
        ↓
Metadata Registry
        ↓
Runtime Resolver
        ↓
Catalog Runtime

Compiler v2 must not break the existing Phase 1 vertical slice.

A new Phase 2 vertical test may extend this flow with explicit validation and
metadata assertions.

24. Acceptance Criteria

Compiler v2 is complete when:

MetadataCompiler delegates validation to DefinitionValidator.
Validation is performed exactly once per compilation.
The compiler does not call Definition.validate() after delegation.
The compiler does not call AttributeDefinition.validate() directly.
CatalogDefinition compiles successfully.
Unsupported definitions raise TypeError.
Definition identity is preserved.
Definition name is preserved.
All supported attribute properties are preserved.
Attribute ordering is preserved.
Standard system fields are attached through the System Fields provider.
normalized_content is not populated through undocumented logic.
Metadata remains immutable.
Compilation is deterministic.
Standard Configuration-specific knowledge is absent from the compiler.
Existing Phase 1 tests remain green.
All new Compiler v2 tests pass.
ruff, black, and mypy remain clean.
25. Architectural Outcome

After Compiler v2 the platform has a clean transformation boundary:

Definition Model
       │
       │ validated
       ▼
DefinitionValidator
       │
       ▼
Metadata Compiler
       │
       │ deterministic transformation
       ▼
Metadata Model
       │
       ▼
Metadata Registry

This boundary becomes the foundation for future metadata types:

Catalog
Document
Register
Report
Workflow
Integration

without requiring the Runtime layer to understand configuration definitions
directly.