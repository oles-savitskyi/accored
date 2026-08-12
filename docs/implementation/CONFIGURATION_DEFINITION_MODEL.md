# Configuration Definition Model

**Project:** AcCoreD
**Product:** Standard Edition
**Stage:** Standard Edition — Design & Implementation Planning
**Status:** Draft
**Architecture Baseline:** `architecture-core-3.0`
**Related Documents:**

* `IMPLEMENTATION_STRATEGY.md`
* `REPOSITORY_STRUCTURE.md`
* `IMPLEMENTATION_ROADMAP.md`
* `MVP_DEFINITION.md`

---

# 1. Purpose

This document defines how application configurations are represented inside AcCoreD.

It establishes the bridge between:

```text
Business Configuration
        ↓
Metadata
        ↓
Runtime
```

and defines the responsibilities of each layer.

The primary objective is to ensure that:

> Business applications are defined through configuration definitions while execution remains the responsibility of the generic Platform runtime.

---

# 2. Core Principle

AcCoreD follows a Hybrid Configuration Model.

Configuration objects are defined using Python-based definitions.

Those definitions are transformed into metadata.

Runtime components execute metadata.

The runtime never executes configuration definitions directly.

Conceptually:

```text
Definition
     ↓
Metadata
     ↓
Runtime
```

This separation is mandatory.

---

# 3. Configuration Ownership

The following ownership model applies.

## Standard Configuration Owns

* business definitions;
* business object declarations;
* business object relationships;
* posting definitions;
* report definitions;
* processing definitions;
* security definitions.

---

## Platform Owns

* metadata model;
* metadata registry;
* runtime objects;
* storage;
* query execution;
* posting infrastructure;
* register infrastructure;
* valuation infrastructure;
* reporting infrastructure;
* security runtime;
* integration runtime.

---

# 4. Architectural Layers

AcCoreD configuration is represented through five layers.

```text
Level 1  Definition Layer
Level 2  Metadata Layer
Level 3  Runtime Layer
Level 4  Storage Layer
Level 5  Presentation Layer
```

---

# 5. Definition Layer

## Purpose

The Definition Layer provides a developer-friendly way to describe business objects.

Definitions are the source code representation of a configuration.

Examples:

```text
Assortment
Business Partner
Goods Receipt
Inventory
Inventory Balance
```

Definitions belong to a configuration package.

Example:

```text
standard/
 └── definitions/
```

Definitions are not runtime objects.

Definitions are not storage objects.

Definitions are not metadata.

They are declarations.

---

# 6. Metadata Layer

The Metadata Layer is the canonical representation of a configuration.

All definitions are transformed into metadata.

Conceptually:

```text
AssortmentDefinition
        ↓
CatalogMetadata
```

```text
GoodsReceiptDefinition
        ↓
DocumentMetadata
```

Runtime components consume metadata.

Metadata therefore becomes the central contract between configuration and runtime.

---

# 7. Runtime Layer

The Runtime Layer executes metadata.

Examples:

```text
CatalogMetadata
        ↓
CatalogRuntime
```

```text
DocumentMetadata
        ↓
DocumentRuntime
```

```text
ReportMetadata
        ↓
ReportRuntime
```

Runtime never depends on configuration definitions.

---

# 8. Storage Layer

Storage persists runtime state.

Storage does not persist definition classes.

Storage does not persist runtime objects.

Storage persists business data and metadata-derived structures.

Examples:

```text
Catalog Records
Document Instances
Register Movements
Register Totals
Cost Facts
```

---

# 9. Presentation Layer

Presentation consumes runtime services.

Presentation must not consume definitions directly.

Conceptually:

```text
UI
 ↓
Runtime
 ↓
Metadata
```

not:

```text
UI
 ↓
Definitions
```

---

# 10. Configuration Lifecycle

Configuration loading follows the following lifecycle.

```text
Definition Discovery
          ↓
Definition Validation
          ↓
Metadata Compilation
          ↓
Metadata Validation
          ↓
Metadata Registration
          ↓
Runtime Availability
```

This lifecycle applies to all configuration objects.

---

# 11. Definition Discovery

The Platform discovers definitions from configuration packages.

Conceptually:

```text
standard/
 └── definitions/
```

Discovery must be deterministic.

The same configuration package must always produce the same metadata graph.

---

# 12. Definition Compilation

Definitions are compiled into metadata.

Example:

```text
AssortmentDefinition
```

↓

```text
CatalogMetadata
```

Compilation produces runtime-independent metadata.

After compilation, the runtime no longer requires the original definition object.

This is a key architectural requirement.

---

# 13. Metadata Graph

Metadata objects form a graph.

Example:

```text
Goods Receipt
        │
        ├── Business Partner
        │
        ├── Employee
        │
        └── Assortment
```

Metadata relationships must be explicit.

Runtime should never infer relationships through convention.

---

# 14. Metadata Registry

Compiled metadata is stored inside a Metadata Registry.

Responsibilities:

* registration;
* lookup;
* validation;
* dependency resolution;
* metadata discovery.

Conceptually:

```text
Metadata
     ↓
Registry
     ↓
Runtime
```

---

# 15. Definition Categories

The Configuration Definition Model supports several definition categories.

Initial categories:

```text
Catalog
Document
Register
Report
Processing
Role
Permission
Valuation
```

Future categories may be added without changing existing runtime contracts.

---

# 16. Catalog Definition Model

Catalog definitions describe master data objects.

Examples:

```text
Assortment
Employees
Business Partners
Cash Accounts
Measure Units
```

A catalog definition contains:

* identity;
* name;
* attributes;
* hierarchy settings;
* constraints;
* forms/views metadata where applicable.

Conceptually:

```text
Catalog Definition
        ↓
Catalog Metadata
        ↓
Catalog Runtime
```

---

# 17. Document Definition Model

Document definitions describe operational business objects.

Examples:

```text
Goods Receipt
```

Document definitions contain:

* header attributes;
* tabular parts;
* lifecycle rules;
* numbering configuration;
* posting configuration.

Conceptually:

```text
Document Definition
        ↓
Document Metadata
        ↓
Document Runtime
```

---

# 18. Tabular Part Definition

Tabular Parts are independent metadata structures.

Example:

```text
Goods Receipt Lines
```

A tabular part contains:

* attributes;
* references;
* validation rules;
* ordering information.

Tabular Parts belong to documents but are modeled independently.

---

# 19. Register Definition Model

Register definitions describe accounting fact storage.

Examples:

```text
Inventory Register
```

A register definition contains:

* dimensions;
* resources;
* totals strategy;
* rebuild strategy.

Conceptually:

```text
Register Definition
        ↓
Register Metadata
        ↓
Register Runtime
```

---

# 20. Posting Definition Model

Posting behavior belongs to configuration.

A document does not contain hard-coded posting logic.

Instead:

```text
Document Definition
         +
Posting Definition
```

produce:

```text
Posting Metadata
```

which is executed by the Posting Runtime.

This preserves Platform/Configuration separation.

---

# 21. Valuation Definition Model

Valuation behavior is configurable.

Examples:

```text
FIFO
Average Cost
Specific Cost
```

A valuation definition specifies:

* valuation method;
* valuation dimensions;
* supported resources;
* rebuild behavior.

Runtime executes the selected valuation model.

---

# 22. Report Definition Model

Reports are configuration objects.

Examples:

```text
Inventory Balance
```

A report definition contains:

* data sources;
* datasets;
* dimensions;
* measures;
* presentation metadata.

Runtime executes the report.

---

# 23. Processing Definition Model

Processings are executable business operations.

Examples:

```text
Valuation Rebuild
Inventory Validation
```

A processing definition specifies:

* execution entry point;
* parameters;
* permissions;
* execution context requirements.

Runtime provides execution infrastructure.

---

# 24. Security Definition Model

Security definitions describe authorization structures.

Examples:

```text
Administrator
Accountant
Operator
```

Definitions contain:

* permissions;
* roles;
* assignments.

Runtime evaluates access.

---

# 25. Attribute Model

Attributes are reusable metadata components.

Examples:

```text
String
Integer
Boolean
Date
DateTime
Money
Quantity
Reference
Enum
```

Definitions reference attributes.

Metadata stores normalized attribute information.

Runtime executes attribute behavior.

---

# 26. Reference Model

References define relationships between metadata objects.

Example:

```text
Goods Receipt
       ↓
Business Partner
```

```text
Goods Receipt Line
       ↓
Assortment
```

References must be explicitly declared.

Implicit runtime relationships are prohibited.

---

# 27. Validation Model

Validation occurs at multiple levels.

## Definition Validation

Verifies definition correctness.

Example:

```text
Unknown attribute type
Duplicate attribute
Invalid reference
```

---

## Metadata Validation

Verifies compiled metadata.

Example:

```text
Broken dependency
Missing target object
Invalid register definition
```

---

## Runtime Validation

Verifies runtime behavior.

Example:

```text
Required value missing
Posting constraint violated
```

---

# 28. Runtime Resolution Model

Runtime objects are resolved through metadata.

Conceptually:

```text
Object Identifier
        ↓
Metadata Registry
        ↓
Metadata
        ↓
Runtime Factory
        ↓
Runtime Object
```

The runtime must not instantiate configuration definitions.

---

# 29. Factory Model

Runtime objects should be created through factories.

Examples:

```text
Catalog Factory
Document Factory
Report Factory
```

Factories consume metadata.

This guarantees runtime independence from configuration source code.

---

# 30. Extensibility Model

New configuration objects should be introduced through definitions.

Example:

```text
Sales Order Definition
```

↓

```text
Sales Order Metadata
```

↓

```text
Document Runtime
```

No runtime modifications should be required if the object fits existing metadata contracts.

---

# 31. Configuration Package Structure

A configuration package should follow a predictable structure.

Example:

```text
standard/
│
├── definitions/
│   ├── catalogs/
│   ├── documents/
│   ├── registers/
│   ├── reports/
│   ├── processings/
│   └── security/
│
├── metadata/
│
└── resources/
```

The exact implementation may evolve.

The architectural separation must remain.

---

# 32. MVP Mapping

The MVP object set maps to the model as follows.

```text
Catalog Definitions
 ├── Assortment
 ├── Employees
 ├── Business Partners
 ├── Cash Accounts
 └── Measure Units

Document Definitions
 └── Goods Receipt

Register Definitions
 └── Inventory

Report Definitions
 └── Inventory Balance

Processing Definitions
 └── Validation/Rebuild Processing

Security Definitions
 └── MVP Roles
```

---

# 33. Architectural Constraints

The following constraints are mandatory.

## Constraint 1

Runtime must not depend on definition classes.

---

## Constraint 2

Definitions must compile into metadata.

---

## Constraint 3

Metadata must be sufficient to execute runtime behavior.

---

## Constraint 4

Business behavior belongs to configuration.

---

## Constraint 5

Technical behavior belongs to platform.

---

## Constraint 6

Storage must not require definition objects.

---

## Constraint 7

Presentation must consume runtime contracts.

---

# 34. Anti-Patterns

The following approaches are prohibited.

## Direct Definition Execution

```text
UI
 ↓
Definition
 ↓
Business Logic
```

---

## Runtime Depending on Configuration Classes

```text
Runtime
 ↓
import standard.goods_receipt
```

---

## Hard-Coded Business Objects

```text
if object_type == "GoodsReceipt":
```

inside generic Platform components.

---

## Configuration Bypassing Metadata

```text
Definition
 ↓
Runtime
```

without metadata compilation.

---

# 35. Success Criteria

The Configuration Definition Model is considered successful when:

1. Standard Configuration can be expressed entirely through definitions;
2. definitions compile into metadata;
3. metadata registers successfully;
4. runtime executes metadata;
5. Platform remains independent from Standard Configuration;
6. new configuration objects can be added without modifying generic runtime;
7. MVP objects are fully representable through the model.

---

# 36. Final Principle

The central principle of the Configuration Definition Model is:

> Definitions describe business intent.
>
> Metadata describes structure.
>
> Runtime executes behavior.

Conceptually:

```text
Business Intent
       ↓
Definitions
       ↓
Metadata
       ↓
Runtime
       ↓
Business Execution
```

This separation allows AcCoreD to remain simultaneously:

* metadata-driven;
* strongly typed;
* extensible;
* testable;
* configuration-oriented;
* independent of any specific business application.

It is the primary mechanism by which Standard Configuration becomes an application built on top of the AcCoreD Platform rather than part of the Platform itself.
