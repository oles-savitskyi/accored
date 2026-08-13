# Phase 1 — Runtime Foundation

**Project:** AcCoreD
**Product:** Standard Edition
**Stage:** Standard Edition — Design & Implementation
**Status:** Draft
**Architecture Baseline:** `architecture-core-3.0`
**Implementation Baseline:** `implementation-0.1`

**Related Documents:**

* `ARCHITECTURE_OVERVIEW.md`
* `IMPLEMENTATION_STRATEGY.md`
* `REPOSITORY_STRUCTURE.md`
* `IMPLEMENTATION_ROADMAP.md`
* `MVP_DEFINITION.md`
* `CONFIGURATION_DEFINITION_MODEL.md`

---

# 1. Purpose

The purpose of Phase 1 is to implement the minimal generic Platform foundation required to transform configuration definitions into executable runtime metadata.

Phase 1 establishes the following chain:

```text
Configuration Definition
        ↓
Definition Validation
        ↓
Metadata Compilation
        ↓
Metadata Registry
        ↓
Runtime Resolution
```

Phase 1 does **not** implement business functionality.

It does not implement:

* catalogs;
* documents;
* registers;
* posting;
* valuation;
* reporting.

Those capabilities will be implemented on top of the foundation established here.

---

# 2. Phase 1 Goal

The goal of Phase 1 is to prove the first executable Platform lifecycle:

```text
Definition
    ↓
Metadata
    ↓
Registry
    ↓
Runtime
```

A successful Phase 1 implementation must demonstrate that a configuration definition can be:

1. declared;
2. validated;
3. compiled into metadata;
4. registered;
5. resolved by identity;
6. consumed by generic runtime infrastructure.

---

# 3. Architectural Principle

The most important rule of Phase 1 is:

> **Runtime does not execute Definitions. Runtime executes Metadata.**

Therefore:

```text
Standard Configuration
        │
        ▼
Definition Layer
        │
        ▼
Metadata Layer
        │
        ▼
Runtime Layer
```

The following dependency is forbidden:

```text
Platform Runtime
        ↓
Standard Configuration Definition
```

The correct dependency is:

```text
Runtime
   ↓
Metadata
```

---

# 4. Scope

Phase 1 contains six major components:

```text
1. Foundation Types
2. Definition Model
3. Metadata Model
4. Metadata Compiler
5. Metadata Registry
6. Runtime Resolution
```

The implementation should remain deliberately small.

---

# 5. Foundation Types

The first implementation layer provides shared primitives.

Initial candidates include:

* object identifiers;
* definition identifiers;
* metadata identifiers;
* names;
* version information;
* errors;
* result/validation structures where required.

The exact types should be introduced only when they are required by the first implementation.

---

# 6. Identity Model

AcCoreD uses ULID as its general identity model.

The Platform must distinguish between:

```text
Business Object Identity
Definition Identity
Metadata Identity
```

These identities must not be conflated.

---

## 6.1 Business Object Identity

Identifies an actual business object instance.

Example:

```text
Assortment record
Goods Receipt document
Register fact
```

---

## 6.2 Definition Identity

Identifies a configuration definition.

Example:

```text
standard.catalogs.assortment
standard.documents.goods_receipt
```

Definition identity is stable across runtime instances.

---

## 6.3 Metadata Identity

Identifies compiled metadata.

Metadata may retain the identity of the originating definition while having its own internal metadata identity if required by the implementation.

The exact relationship will be determined during implementation.

---

# 7. Definition Model

The first definition model must be generic.

The initial abstraction should support:

```text
Definition
    ├── type
    ├── name
    ├── identifier
    └── configuration metadata
```

A conceptual Python representation:

```python
class Definition:
    ...
```

The exact class structure is an implementation concern.

The architecture requires the following semantic properties:

* stable identity;
* definition type;
* name;
* validation;
* conversion to metadata.

---

# 8. Definition Types

Phase 1 does not implement every definition type.

It implements only the generic mechanism required to prove the architecture.

The first concrete definition type should be intentionally simple.

Recommended first candidate:

```text
Catalog Definition
```

This allows the foundation to be tested with a realistic configuration object without implementing the complete Catalog Runtime.

---

# 9. Definition Validation

Definitions must be validated before compilation.

Validation should detect at least:

* missing identifier;
* invalid identifier;
* missing name;
* duplicate attributes where attributes are introduced;
* invalid definition type;
* invalid references where applicable.

The validation mechanism must be reusable by future definition types.

---

# 10. Metadata Model

Metadata is the canonical runtime-independent representation of configuration.

Metadata must contain enough information for runtime resolution without requiring the original Definition object.

Conceptually:

```text
Definition
     ↓
Metadata
```

After compilation:

```text
Runtime
     ↓
Metadata
```

The original definition is no longer part of the runtime execution path.

---

# 11. Metadata Requirements

Every metadata object must have:

* stable identifier;
* metadata type;
* name;
* version information where required;
* definition origin/reference;
* normalized metadata content.

Metadata must be immutable after registration.

If configuration changes, new metadata must be produced and registered according to the future versioning model.

---

# 12. Metadata Compiler

The Metadata Compiler transforms Definitions into Metadata.

Conceptually:

```text
Definition
    ↓
MetadataCompiler
    ↓
Metadata
```

The compiler is responsible for:

* reading definition declarations;
* validating them;
* resolving definition-level dependencies;
* normalizing metadata;
* producing metadata.

The compiler must not:

* persist business objects;
* create runtime business instances;
* execute business operations;
* access UI;
* perform posting.

---

# 13. Compiler Contract

The compiler should expose a simple conceptual contract:

```python
metadata = compiler.compile(definition)
```

The implementation may use a richer API internally.

The architectural requirement is:

> Compilation is deterministic and side-effect free.

For the same valid definition and compilation context, the compiler should produce equivalent metadata.

---

# 14. Metadata Registry

The Metadata Registry is the central repository for compiled metadata.

Conceptually:

```text
Metadata
    ↓
MetadataRegistry
```

Responsibilities:

* registration;
* lookup;
* duplicate detection;
* type validation;
* dependency availability;
* metadata enumeration.

---

# 15. Registry Contract

The registry must support at least:

```text
register(metadata)
get(identifier)
contains(identifier)
list(...)
```

The exact Python API will be determined during implementation.

---

# 16. Registry Rules

The registry must enforce:

### Rule 1

A metadata identifier cannot silently resolve to two different metadata objects.

### Rule 2

Registration of invalid metadata must fail.

### Rule 3

Lookup of an unknown metadata identifier must produce an explicit error/result.

### Rule 4

Registered metadata must not be modified in place.

---

# 17. Runtime Resolution

Runtime resolution translates an object identity into runtime capability.

Conceptually:

```text
Metadata Identifier
        ↓
Metadata Registry
        ↓
Metadata
        ↓
Runtime Factory / Resolver
        ↓
Runtime Object
```

The first implementation should provide generic resolution infrastructure.

It does not yet need a complete Catalog Runtime.

---

# 18. Runtime Context

A minimal Runtime Context should be introduced if required by runtime resolution.

The context represents execution environment information.

Potential future contents include:

* metadata registry;
* storage;
* security context;
* transaction context;
* services.

Phase 1 should include only dependencies actually required by the first runtime operation.

Avoid creating a large empty `RuntimeContext` object merely for architectural symmetry.

---

# 19. Runtime Factory

Runtime factories create runtime objects from metadata.

Conceptually:

```text
Metadata
   ↓
Factory
   ↓
Runtime
```

Factories belong to Platform.

Standard Configuration must not provide runtime factories for ordinary configuration objects.

---

# 20. First Runtime Object

The first runtime object should be deliberately minimal.

Recommended candidate:

```text
Catalog Runtime
```

However, this should represent only the generic runtime capability required to prove resolution.

It does not yet need:

* persistence;
* CRUD;
* queries;
* forms;
* hierarchy;
* UI.

Those belong to later phases.

---

# 21. End-to-End Phase 1 Scenario

The complete Phase 1 scenario should be:

```text
1. Define a Catalog
        ↓
2. Validate Definition
        ↓
3. Compile Definition
        ↓
4. Produce Catalog Metadata
        ↓
5. Register Metadata
        ↓
6. Resolve Metadata
        ↓
7. Create Generic Catalog Runtime
        ↓
8. Inspect Runtime Metadata
```

This scenario is the primary Phase 1 acceptance test.

---

# 22. Example

Conceptually, Standard Configuration may declare:

```python
class AssortmentDefinition(CatalogDefinition):
    name = "Assortment"
```

The compiler produces:

```text
CatalogMetadata
    identifier = "standard.catalog.assortment"
    name = "Assortment"
```

The registry stores it:

```text
MetadataRegistry
    └── standard.catalog.assortment
```

The runtime resolves it:

```text
standard.catalog.assortment
        ↓
CatalogRuntime
```

The runtime does not import `AssortmentDefinition`.

---

# 23. Definition / Metadata Separation Test

A mandatory architectural test must demonstrate that Runtime can operate after the original Definition object is unavailable.

Conceptually:

```text
Definition
    ↓
Compile
    ↓
Metadata
    ↓
Destroy Definition
    ↓
Runtime
```

If Runtime fails because it requires the original Definition, the separation is incorrect.

---

# 24. Metadata Immutability

Registered metadata should be treated as immutable.

The preferred model is:

```text
Definition
     ↓
Compile
     ↓
Metadata
     ↓
Register
     ↓
Read-only
```

Runtime components may read metadata.

They must not mutate it.

---

# 25. Dependency Resolution

Metadata definitions may depend on other metadata.

Example:

```text
Goods Receipt
      ↓
Business Partner
      ↓
Catalog Metadata
```

Phase 1 should establish the infrastructure required to detect and resolve metadata dependencies.

Complex dependency graphs are not required yet.

The mechanism should nevertheless be designed to support them.

---

# 26. Configuration Loading

Phase 1 should introduce the concept of Configuration Loading.

Conceptually:

```text
Configuration Package
        ↓
Definition Discovery
        ↓
Compilation
        ↓
Validation
        ↓
Registry
```

The loader should be generic.

It must not contain knowledge such as:

```python
if definition == "Assortment":
```

---

# 27. Configuration Loader

The Configuration Loader is responsible for:

* discovering definitions;
* loading definitions;
* invoking validation;
* invoking compilation;
* registering metadata.

It must not execute business operations.

---

# 28. Errors

Phase 1 should establish a basic error hierarchy.

At minimum:

```text
AcCoreError
    ├── DefinitionError
    ├── MetadataError
    ├── CompilationError
    ├── RegistryError
    └── RuntimeError
```

The exact hierarchy may change during implementation.

The important requirement is that failures are distinguishable by architectural layer.

---

# 29. Testing Strategy

Phase 1 testing should follow four levels.

## Unit Tests

Test:

* identifiers;
* definitions;
* validation;
* metadata;
* compiler;
* registry.

---

## Component Tests

Test:

```text
Definition
    ↓
Compiler
    ↓
Metadata
```

and:

```text
Metadata
    ↓
Registry
    ↓
Resolution
```

---

## Integration Test

Test:

```text
Configuration Package
        ↓
Loader
        ↓
Registry
        ↓
Runtime
```

---

## Vertical Test

Execute the complete Phase 1 scenario.

---

# 30. Required Tests

At minimum:

### Definition

* valid definition accepted;
* invalid definition rejected.

### Compilation

* valid definition compiles;
* invalid definition does not compile;
* compilation is deterministic.

### Registry

* metadata can be registered;
* duplicate identifiers are rejected;
* metadata can be resolved;
* unknown identifiers fail explicitly.

### Runtime

* metadata resolves to runtime;
* runtime does not require Definition object.

### Loader

* configuration can be loaded end-to-end.

---

# 31. Serialization

Phase 1 does not require persistent serialization of metadata.

Metadata may remain in memory.

However, metadata structures must be designed so that future serialization is possible.

The implementation must not depend on Python object identity for metadata semantics.

---

# 32. Persistence

Phase 1 does not implement business-data persistence.

The Metadata Registry may initially be in-memory.

Persistent metadata storage is a later concern.

---

# 33. Concurrency

Phase 1 does not require advanced concurrency.

The initial Metadata Registry may be single-process and in-memory.

Thread-safety should be considered only where the implementation naturally requires it.

---

# 34. Performance

Phase 1 is not a performance optimization phase.

The primary goals are:

* correctness;
* separation;
* determinism;
* testability.

Performance benchmarks may be added later.

---

# 35. Package Mapping

The first implementation should primarily occupy:

```text
src/accore/platform/
│
├── foundation/
├── metadata/
└── runtime/
```

Potential responsibility:

```text
foundation/
    identity
    errors
    common primitives

metadata/
    definitions
    metadata models
    compiler
    registry
    loader

runtime/
    context
    resolver
    factories
```

The exact module names should be determined during implementation.

Do not create excessive files before actual responsibilities emerge.

---

# 36. Standard Configuration

Standard Configuration participates in Phase 1 only as a consumer of the Platform foundation.

The first Standard Configuration implementation should contain the smallest possible definition.

Recommended candidate:

```text
Assortment
```

Its purpose is to prove:

```text
Standard Definition
        ↓
Platform Compiler
        ↓
Platform Metadata
        ↓
Platform Registry
        ↓
Platform Runtime
```

No business functionality is required.

---

# 37. Platform Independence Test

A critical Phase 1 test is:

> Platform must load and operate without importing Standard Configuration.

The Platform test suite must therefore be executable without:

```text
src/standard/
```

being imported.

This establishes the dependency direction:

```text
Standard
    ↓
Platform
```

and prevents:

```text
Platform
    ↓
Standard
```

---

# 38. Anti-Patterns

The following are explicitly prohibited.

## Anti-Pattern 1 — Runtime Imports Definitions

```python
from standard.definitions import Assortment
```

inside Platform runtime.

---

## Anti-Pattern 2 — Hard-Coded Configuration

```python
if metadata.name == "Assortment":
    ...
```

inside generic runtime.

---

## Anti-Pattern 3 — Definition as Runtime Object

Using a Definition instance directly as the executable business object.

---

## Anti-Pattern 4 — Mutable Metadata

Allowing runtime components to modify registered metadata.

---

## Anti-Pattern 5 — Global Hidden Registry

Using an implicit global registry that makes dependencies and lifecycle impossible to test.

The registry should be an explicit dependency.

---

# 39. Phase 1 Deliverables

Phase 1 must produce:

```text
Foundation Types
Definition Model
Metadata Model
Metadata Compiler
Metadata Registry
Configuration Loader
Runtime Resolver
Minimal Runtime Object
Standard Configuration Test Definition
Unit Tests
Component Tests
Integration Test
Vertical Test
```

---

# 40. Definition of Done

Phase 1 is complete when the following scenario executes successfully:

```text
Standard Configuration Definition
             ↓
       Definition Validation
             ↓
       Metadata Compilation
             ↓
       Metadata Registry
             ↓
        Runtime Resolution
             ↓
        Runtime Object
```

and all of the following are true:

* Platform does not depend on Standard;
* Definitions are not runtime objects;
* Metadata is independent from Definition instances;
* metadata can be registered and resolved;
* duplicate metadata identities are rejected;
* invalid definitions are rejected;
* runtime can operate without original definitions;
* the complete vertical test passes.

---

# 41. Phase 1 Boundary

Phase 1 ends here.

It does **not** include:

```text
Catalog CRUD
Document CRUD
Storage implementation
Query engine
Posting
Registers
Valuation
Reporting
UI
```

These belong to subsequent phases.

The purpose of Phase 1 is to establish the executable metadata foundation upon which all of them will be built.

---

# 42. Architectural Success Criterion

The ultimate success criterion is:

> A new Standard Configuration object can be introduced by defining metadata through the Definition Layer without modifying the generic Metadata Registry or Runtime Resolution infrastructure.

Conceptually:

```text
New Configuration Definition
            ↓
Existing Compiler
            ↓
Existing Registry
            ↓
Existing Runtime
```

If adding the first Standard Configuration object requires hard-coded changes inside the Platform, the Phase 1 design must be reconsidered.

---

# 43. Final Architecture

At the completion of Phase 1, the first executable AcCoreD architecture should look like:

```text
┌─────────────────────────────────────────┐
│          Standard Configuration         │
│                                         │
│      Assortment Definition              │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│          Definition Layer               │
│                                         │
│     Validation / Definition Model       │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│           Metadata Layer                │
│                                         │
│ Compiler → Metadata → Registry          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│            Runtime Layer                │
│                                         │
│ Resolver → Runtime Object               │
└─────────────────────────────────────────┘
```

This becomes the foundation for all subsequent Platform implementation.

---

# 44. Final Principle

Phase 1 establishes one fundamental rule for the entire AcCoreD implementation:

> **Configuration describes what the application is. Metadata represents that description. Platform Runtime executes it.**

The implementation must preserve this separation from the very first line of production code.
