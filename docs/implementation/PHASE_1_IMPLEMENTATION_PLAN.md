# Phase 1 — Runtime Foundation Implementation Plan

**Project:** AcCoreD  
**Product:** Standard Edition  
**Stage:** Standard Edition — Design & Implementation  
**Phase:** 1 — Runtime Foundation  
**Status:** Approved for Implementation  
**Architecture Baseline:** `architecture-core-3.0`  
**Implementation Baseline:** `implementation-0.1`

---

# 1. Purpose

This document defines the concrete implementation sequence for Phase 1.

Phase 1 establishes the first executable Platform foundation:

```text
Definition
    ↓
Validation
    ↓
Compilation
    ↓
Metadata
    ↓
Registry
    ↓
Runtime Resolution
````

The purpose of this plan is to prevent premature implementation of business functionality and to establish a small, testable, architecturally correct vertical slice.

---

# 2. Implementation Strategy

Phase 1 is implemented incrementally.

Each step must produce a working and tested result before the next step begins.

The implementation order is:

```text
Step 1   Foundation
    ↓
Step 2   Definition Model
    ↓
Step 3   Metadata Model
    ↓
Step 4   Metadata Compiler
    ↓
Step 5   Metadata Registry
    ↓
Step 6   Runtime Resolution
    ↓
Step 7   Standard Definition
    ↓
Step 8   End-to-End Vertical Test
```

No later step should introduce functionality that is not required by the preceding architectural contract.

---

# 3. Target Package Structure

The initial implementation will use:

```text
src/
├── accore/
│   ├── __init__.py
│   │
│   └── platform/
│       ├── __init__.py
│       │
│       ├── foundation/
│       │   └── ...
│       │
│       ├── metadata/
│       │   └── ...
│       │
│       └── runtime/
│           └── ...
│
└── standard/
    ├── __init__.py
    └── definitions/
        └── ...
```

Only these areas should receive production code during the first implementation cycle.

Other Platform packages remain architectural placeholders.

---

# 4. Step 1 — Foundation

## Objective

Introduce the smallest set of shared primitives required by the Definition, Metadata, and Runtime layers.

## Initial Responsibilities

The Foundation layer may contain:

```text
foundation/
├── identity
├── errors
└── common primitives
```

The exact module decomposition should follow actual implementation needs.

---

## 4.1 Identity

AcCoreD uses ULID as the general identity model.

The implementation must provide a Platform-level identity abstraction rather than scattering raw string handling throughout the code.

The identity abstraction must support:

* creation;
* validation;
* comparison;
* serialization where required.

---

## 4.2 Errors

Introduce the initial error hierarchy:

```text
AcCoreError
├── DefinitionError
├── MetadataError
├── CompilationError
├── RegistryError
└── RuntimeResolutionError
```

The hierarchy may be extended later.

Errors must belong to the architectural layer responsible for detecting the failure.

---

## 4.3 Tests

Add unit tests for:

* valid identifiers;
* invalid identifiers;
* identifier equality;
* basic error hierarchy.

---

## 4.4 Completion Criteria

Step 1 is complete when:

* Foundation imports successfully;
* identity tests pass;
* error types exist;
* `pytest`, `ruff`, `black`, and `mypy` pass.

---

# 5. Step 2 — Definition Model

## Objective

Introduce the generic Definition abstraction.

Definition represents the declarative description of a configuration object.

It is not a runtime object.

---

## 5.1 Base Definition

Introduce a base abstraction conceptually equivalent to:

```python
Definition
```

It must support at least:

* identifier;
* name;
* definition type;
* validation.

The implementation should favour immutable data where practical.

---

## 5.2 Definition Type

The Definition model must be able to distinguish different kinds of configuration definitions.

The first concrete type will be:

```text
CatalogDefinition
```

No DocumentDefinition, RegisterDefinition, or ReportDefinition is required yet.

---

## 5.3 Validation

Definition validation must be explicit.

Invalid definitions must not reach the compiler.

Conceptually:

```text
Definition
    ↓
validate()
    ↓
Valid / DefinitionError
```

---

## 5.4 Tests

Add tests for:

* valid Definition;
* missing identifier;
* invalid identifier;
* missing name;
* valid CatalogDefinition;
* invalid CatalogDefinition.

---

## 5.5 Completion Criteria

Step 2 is complete when a valid `CatalogDefinition` can be created and validated without any Metadata or Runtime dependency.

---

# 6. Step 3 — Metadata Model

## Objective

Introduce the runtime-independent representation of configuration.

Metadata is produced from Definitions.

---

## 6.1 Base Metadata

Introduce:

```text
Metadata
```

It must contain at least:

* identifier;
* metadata type;
* name;
* source definition identity;
* normalized metadata content where applicable.

---

## 6.2 Catalog Metadata

Introduce:

```text
CatalogMetadata
```

as the first concrete metadata type.

It represents the runtime description of a catalog.

It does not represent catalog records.

---

## 6.3 Metadata Immutability

Metadata must be immutable after creation.

The preferred lifecycle is:

```text
Definition
    ↓
Compiler
    ↓
Metadata
    ↓
Registry
    ↓
Read-only
```

Runtime code must not modify metadata.

---

## 6.4 Tests

Add tests for:

* valid Metadata;
* valid CatalogMetadata;
* metadata identity;
* source definition identity;
* immutability.

---

## 6.5 Completion Criteria

Step 3 is complete when a valid `CatalogDefinition` can be represented by valid `CatalogMetadata`.

The compiler itself is not part of this step.

---

# 7. Step 4 — Metadata Compiler

## Objective

Implement the transformation:

```text
Definition
    ↓
Metadata
```

---

## 7.1 Compiler

Introduce:

```text
MetadataCompiler
```

The compiler must:

* accept a valid Definition;
* validate where necessary;
* produce Metadata;
* avoid persistent side effects;
* remain independent of Standard Configuration.

---

## 7.2 Determinism

Compilation should be deterministic.

For the same valid Definition and compilation context, the resulting metadata must be semantically equivalent.

---

## 7.3 Compiler Contract

The initial conceptual contract is:

```python
metadata = compiler.compile(definition)
```

The final API may differ.

The implementation must not expose unnecessary configuration or runtime concerns.

---

## 7.4 Tests

Add:

* valid Definition → Metadata;
* invalid Definition → failure;
* CatalogDefinition → CatalogMetadata;
* deterministic compilation.

---

## 7.5 Completion Criteria

Step 4 is complete when a CatalogDefinition can be compiled into CatalogMetadata without accessing storage, Standard Runtime, or UI.

---

# 8. Step 5 — Metadata Registry

## Objective

Introduce an explicit in-memory Metadata Registry.

The registry is responsible for storing and resolving compiled metadata.

---

## 8.1 Registry

Introduce:

```text
MetadataRegistry
```

The registry must support:

```text
register(metadata)
get(identifier)
contains(identifier)
```

Additional operations may be added only when required.

---

## 8.2 Duplicate Detection

The registry must reject attempts to register conflicting metadata under the same identity.

Silent replacement is prohibited.

---

## 8.3 Unknown Metadata

Lookup of an unknown identifier must produce an explicit failure.

The implementation must not return `None` silently unless the API explicitly defines an optional lookup operation.

---

## 8.4 Metadata Immutability

The registry must not modify metadata after registration.

---

## 8.5 Tests

Add:

* registration;
* lookup;
* unknown identifier;
* duplicate identifier;
* multiple metadata objects;
* metadata immutability.

---

## 8.6 Completion Criteria

Step 5 is complete when compiled metadata can be registered and resolved independently of the original Definition.

---

# 9. Step 6 — Runtime Resolution

## Objective

Introduce the minimal runtime mechanism capable of resolving Metadata into a runtime object.

---

## 9.1 Runtime Resolver

Introduce:

```text
RuntimeResolver
```

Conceptual flow:

```text
Metadata Identifier
        ↓
MetadataRegistry
        ↓
Metadata
        ↓
RuntimeResolver
        ↓
Runtime Object
```

---

## 9.2 Runtime Factory

A minimal factory mechanism may be introduced if required by the resolver.

Factories must remain Platform components.

Standard Configuration must not provide generic Platform factories.

---

## 9.3 Catalog Runtime

Introduce the smallest possible:

```text
CatalogRuntime
```

It must expose metadata or metadata-derived information sufficient to prove runtime resolution.

It does not implement:

* CRUD;
* persistence;
* queries;
* forms;
* hierarchy;
* posting;
* business operations.

---

## 9.4 Definition Independence

Runtime must not require the original Definition.

Mandatory test:

```text
Definition
    ↓
Compile
    ↓
Metadata
    ↓
Register
    ↓
Discard Definition
    ↓
Resolve Runtime
```

If Runtime requires the Definition instance, the implementation violates the architecture.

---

## 9.5 Tests

Add:

* metadata resolution;
* runtime creation;
* catalog runtime creation;
* runtime metadata access;
* runtime operation without Definition.

---

## 9.6 Completion Criteria

Step 6 is complete when a registered CatalogMetadata can be resolved into a CatalogRuntime without access to the original Definition.

---

# 10. Step 7 — First Standard Definition

## Objective

Prove that Standard Configuration can consume the Platform without modifying it.

The first concrete Standard Configuration definition will be:

```text
Assortment
```

---

## 10.1 Assortment Definition

Introduce:

```text
AssortmentDefinition
```

under:

```text
src/standard/definitions/
```

It should contain only the metadata necessary for the Phase 1 demonstration.

No business behaviour is required.

---

## 10.2 Dependency Direction

The dependency must remain:

```text
standard
    ↓
accore.platform
```

Platform must not import:

```text
standard
```

---

## 10.3 Tests

Verify that:

* AssortmentDefinition is valid;
* Platform compiler accepts it;
* resulting CatalogMetadata can be registered;
* runtime can resolve it.

---

## 10.4 Completion Criteria

Step 7 is complete when Standard Configuration successfully defines an object using only Platform abstractions.

---

# 11. Step 8 — End-to-End Vertical Test

## Objective

Prove the complete Phase 1 architecture.

The vertical test must execute:

```text
AssortmentDefinition
        ↓
Validation
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
```

---

## 11.1 Mandatory Test

The test must verify:

1. Standard Definition is created.
2. Definition is validated.
3. Definition is compiled.
4. Metadata is produced.
5. Metadata is registered.
6. Definition is no longer required.
7. Runtime is resolved.
8. Runtime exposes correct metadata.

---

## 11.2 Platform Independence

The test suite must also demonstrate that Platform code can be tested without Standard Configuration.

---

# 12. Test Structure

The Phase 1 tests should follow:

```text
tests/
├── unit/
│   ├── foundation/
│   ├── metadata/
│   └── runtime/
│
├── component/
│   ├── metadata/
│   └── runtime/
│
├── integration/
│   └── configuration/
│
└── vertical/
    └── phase1/
```

The exact number of test files should remain small.

Do not create empty test files merely to mirror the directory structure.

---

# 13. Commit Strategy

Phase 1 should be implemented through small architectural commits.

Recommended sequence:

```text
1. Add Platform foundation
2. Add Definition model
3. Add Metadata model
4. Add Metadata compiler
5. Add Metadata registry
6. Add Runtime resolver
7. Add first Standard definition
8. Add Phase 1 vertical test
```

Each commit should:

* contain one coherent architectural change;
* pass the test suite;
* pass Ruff;
* pass Black;
* pass mypy;
* leave the repository in a working state.

---

# 14. Code Quality Gate

Before every Phase 1 commit, run:

```bash
pytest
ruff check .
black --check .
mypy src
```

If Black reports formatting changes:

```bash
black .
```

Then run the complete quality gate again.

---

# 15. Architectural Review Gates

Three explicit review gates are required.

## Gate A — Definition / Metadata Boundary

After Step 4 verify:

```text
Definition
    ↓
Compiler
    ↓
Metadata
```

and confirm that Metadata does not depend on Definition instances at runtime.

---

## Gate B — Registry Boundary

After Step 5 verify:

```text
Metadata
    ↓
Registry
```

and confirm that Registry does not know about Standard Configuration.

---

## Gate C — Runtime Boundary

After Step 6 verify:

```text
Metadata
    ↓
Runtime
```

and confirm that Runtime does not import or depend on Standard Definitions.

---

# 16. Explicit Non-Goals

The following are explicitly outside Phase 1:

* database storage;
* persistent metadata registry;
* catalog records;
* CRUD;
* query engine;
* document engine;
* register engine;
* posting;
* valuation;
* reporting;
* security enforcement;
* workflow;
* UI;
* API;
* event infrastructure;
* import/export.

If implementation begins requiring one of these, stop and reassess the scope.

---

# 17. Design Constraints

The implementation must preserve the following constraints.

### Constraint 1

Platform is generic.

### Constraint 2

Standard Configuration is declarative.

### Constraint 3

Definitions are not runtime objects.

### Constraint 4

Metadata is the runtime contract.

### Constraint 5

Metadata is immutable after registration.

### Constraint 6

Registry is an explicit dependency.

### Constraint 7

Runtime does not import Standard Configuration.

### Constraint 8

Phase 1 implementation remains in-memory.

### Constraint 9

The first vertical slice must remain minimal.

---

# 18. Expected Result

At the end of Phase 1 the repository should contain a minimal executable architecture:

```text
src/
│
├── accore/
│   └── platform/
│       ├── foundation/
│       ├── metadata/
│       └── runtime/
│
└── standard/
    └── definitions/
```

with the following logical flow:

```text
                 STANDARD
                    │
                    ▼
          AssortmentDefinition
                    │
                    ▼
             ┌─────────────┐
             │   Compiler  │
             └──────┬──────┘
                    │
                    ▼
             CatalogMetadata
                    │
                    ▼
             MetadataRegistry
                    │
                    ▼
             RuntimeResolver
                    │
                    ▼
              CatalogRuntime
```

---

# 19. Definition of Done

Phase 1 is complete when:

* all eight implementation steps are complete;
* unit tests pass;
* component tests pass;
* integration tests pass;
* vertical test passes;
* Platform does not depend on Standard;
* Standard depends only on Platform;
* Runtime does not depend on Definition instances;
* Metadata is immutable;
* Registry is explicit;
* the entire quality gate passes.

The final verification command is:

```bash
pytest
ruff check .
black --check .
mypy src
```

All commands must complete successfully.

---

# 20. Phase 1 Baseline

After successful completion, create a new implementation tag:

```text
implementation-0.2
```

This tag represents:

> The first executable Platform Runtime Foundation.

It is the baseline for the next implementation phase.

```

