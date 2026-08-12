# Metadata Architecture

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Metadata subsystem defines the complete structural description of an AcCore application.

Metadata describes **what the application is**, while the Runtime determines **how the application behaves**.

The Metadata subsystem provides a unified, immutable and platform-independent representation of:

- business objects;
- data models;
- application structure;
- user interface definitions;
- security model;
- business modules;
- configuration composition.

Metadata is the architectural foundation upon which all other platform subsystems operate.

---

# 2. Goals

The Metadata subsystem is designed to achieve the following goals.

## Complete application description

Every business application can be fully described using metadata.

No structural information exists outside the metadata model.

---

## Platform independence

Metadata is independent from:

- storage engine;
- user interface technology;
- execution engine;
- deployment model.

The same metadata may be executed by different runtime implementations.

---

## Declarative architecture

Metadata describes system structure only.

It does not execute business logic and does not contain runtime state.

---

## Strong consistency

Metadata forms a complete and internally consistent model of the application.

All references are validated before publication.

---

## Extensibility

The architecture allows new metadata object types to be introduced without redesigning the subsystem.

---

## Deterministic loading

The same metadata source always produces the same metadata model.

---

## Immutability

After successful loading and validation, metadata becomes read-only.

All runtime subsystems operate on immutable metadata.

---

# 3. Responsibilities

The Metadata subsystem is responsible for:

- describing application structure;
- defining metadata object types;
- object hierarchy;
- attributes;
- commands;
- forms;
- relationships;
- security definitions;
- localization resources;
- configuration composition;
- metadata validation;
- reference resolution;
- metadata publication.

---

The Metadata subsystem is NOT responsible for:

- data storage;
- business logic execution;
- UI rendering;
- query execution;
- transaction processing;
- runtime object lifecycle.

These responsibilities belong to other architectural subsystems.

---

# 4. Architectural Principles

## Metadata is declarative

Metadata describes the system.

It does not execute the system.

---

## Metadata is immutable

After publication metadata cannot be modified.

Configuration changes always produce a new metadata model.

---

## Metadata is hierarchical

Metadata is organized as a hierarchical object tree.

The hierarchy provides logical organization of application components.

---

## Metadata is strongly typed

Every metadata object has a well-defined type.

The type determines:

- available properties;
- child objects;
- validation rules;
- runtime behavior.

---

## Metadata is platform independent

Metadata contains no implementation-specific logic.

It does not depend on:

- Qt;
- SQL;
- Python runtime;
- storage engine.

---

## Metadata is isolated from Runtime

Metadata describes the application.

Runtime executes the application.

Dependencies exist only from Runtime to Metadata.

The Metadata subsystem never depends on Runtime.

---

## Metadata is validated before use

Incomplete or inconsistent metadata cannot be published.

Runtime always operates on validated metadata.

---

## Metadata is deterministic

Metadata loading always produces identical results for identical sources.

The loading process contains no non-deterministic behavior.

---

# 5. Metadata Lifecycle

The lifecycle of metadata consists of several well-defined stages.

```
Metadata Sources
        │
        ▼
     Loading
        │
        ▼
     Parsing
        │
        ▼
 Object Construction
        │
        ▼
Reference Resolution
        │
        ▼
    Validation
        │
        ▼
     Freezing
        │
        ▼
Metadata Publication
        │
        ▼
      Runtime
```

Each stage must complete successfully before the next stage begins.

---

# 6. Metadata Object Model

Metadata is organized as a logical hierarchy.

```
Configuration

├── Catalogs
├── Documents
├── Registers
├── Reports
├── Enumerations
├── Roles
├── Common Modules
├── Data Types
├── UI Components
└── System Objects
```

Each node represents a metadata object with its own properties and children.

The hierarchy provides organization only.

Object relationships are not limited to the hierarchy.

---

# 7. Metadata Graph

Although metadata is organized as a tree, the complete metadata model is a graph.

```
              Metadata Tree
                     │
                     ▼
          Reference Resolution
                     │
                     ▼
             Metadata Graph
```

The graph consists of:

- ownership relationships;
- object references;
- inheritance;
- dependencies;
- extension relationships.

This graph becomes the primary representation used by Runtime.

The hierarchical tree remains a logical organization mechanism.

---

# 8. Internal Components

The Metadata subsystem consists of several logical components.

```
Metadata Manager

├── Loader
├── Parser
├── Object Factory
├── Reference Resolver
├── Validator
├── Registry
├── Serializer
├── Extension Manager
└── Publication Manager
```

Each component has a single responsibility and communicates through well-defined interfaces.

---

# 9. Loading Pipeline

Metadata loading follows a deterministic processing pipeline.

```
Read Sources
      │
      ▼
Parse Definitions
      │
      ▼
Create Objects
      │
      ▼
Resolve References
      │
      ▼
Validate Model
      │
      ▼
Freeze Objects
      │
      ▼
Publish Metadata
```

No runtime subsystem may access metadata before publication.

---

# 10. Configuration Composition

An application configuration may consist of multiple metadata sources.

Typical composition includes:

- platform metadata;
- standard configuration;
- optional extensions;
- plugins.

The Metadata subsystem combines these sources into a single unified metadata model.

Composition rules are deterministic and validated.

---

# 11. Versioning

Each metadata model has its own version.

Versioning enables:

- compatibility verification;
- migration support;
- extension compatibility;
- platform evolution.

Runtime always operates on a single published metadata version.

---

# 12. Performance Considerations

The Metadata subsystem is optimized for:

- fast startup;
- efficient reference lookup;
- low memory overhead;
- immutable shared objects;
- cache-friendly traversal.

Since metadata is immutable, multiple runtime components may safely share the same object instances.

---

# 13. Thread Safety

Published metadata is immutable.

Therefore:

- concurrent reads require no synchronization;
- metadata objects may be safely shared between threads;
- no runtime locking is required for metadata access.

Synchronization is only required during metadata construction.

---

# 14. Future Evolution

The architecture allows future extensions without breaking existing principles.

Possible future capabilities include:

- incremental metadata loading;
- distributed metadata repositories;
- remote configuration deployment;
- metadata hot reload;
- metadata snapshots;
- metadata compilation;
- metadata optimization.

These features extend the architecture without changing its fundamental design.

---

# 15. Relationship to Other Subsystems

The Metadata subsystem provides structural information to:

- Runtime;
- Object Model;
- Storage;
- Security;
- UI;
- Query Engine;
- Expression Engine;
- Reporting;
- Extension Framework.

Metadata itself has no dependencies on these subsystems.

---

# 16. Metadata Compilation Principle

The Metadata subsystem is architecturally treated as a compiler that transforms configuration sources into a published semantic metadata graph.

Runtime subsystems never operate directly on metadata sources or partially constructed metadata objects. Instead, they consume a fully resolved, validated, immutable and published metadata graph.

This one-way dependency is a fundamental architectural principle of AcCore.