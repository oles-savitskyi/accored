# STORAGE_ARCHITECTURE.md

Version: 1.0 (Draft)

Status: Architecture Specification

---

# 1. Introduction

## 1.1 Purpose

The Storage Architecture defines the logical and physical persistence model of the AcCore platform.

Its primary responsibility is to provide reliable, consistent, storage-independent persistence for all metadata-defined business objects while remaining completely transparent to the Runtime and application code.

The Storage subsystem is responsible for:

- persistent data storage;
- object identity management;
- transactions;
- concurrency support;
- version management;
- indexing;
- register persistence;
- document persistence;
- adaptive storage optimization.

The Storage subsystem is **not** responsible for:

- business logic;
- metadata processing;
- query planning;
- user interface;
- document posting logic;
- calculated field evaluation.

These responsibilities belong to other platform subsystems.

---

## 1.2 Scope

This specification defines:

- storage boundaries;
- storage responsibilities;
- storage entities;
- storage providers;
- identity model;
- reference model;
- persistence model;
- transaction model;
- indexing strategy;
- register storage;
- document storage;
- adaptive optimization.

This specification intentionally does not define:

- Metadata Architecture;
- Runtime Architecture;
- Query Engine;
- UI Architecture;
- Processing Engine.

Those subsystems interact with Storage through well-defined interfaces but remain architecturally independent.

---

## 1.3 Design Goals

The Storage subsystem is designed to satisfy the following goals.

### Storage Independence

Business logic MUST NOT depend on a specific database engine.

SQLite, PostgreSQL and future storage providers MUST expose identical logical behavior.

---

### Metadata Driven

Storage structures MUST be generated from Metadata definitions.

Business objects MUST NOT manually define physical database structures.

---

### High Performance

The Storage subsystem SHOULD provide efficient persistence for:

- catalogs;
- documents;
- registers;
- constants;
- sequences.

Performance optimizations MUST remain transparent to application code.

---

### Scalability

The architecture MUST support:

- embedded single-user databases;
- client-server databases;
- large enterprise databases;
- distributed deployments.

Migration between storage providers SHOULD NOT require metadata changes.

---

### Extensibility

New storage providers MAY be added without changing:

- Metadata;
- Runtime;
- business logic;
- object model.

---

### Consistency

All persistent objects MUST follow identical persistence rules.

Object identity, references, transactions and versioning MUST behave consistently across the entire platform.

---

### Adaptive Optimization

The Storage subsystem MAY automatically optimize physical storage structures while preserving logical behavior defined by Metadata.

Automatic optimization MUST remain completely transparent to application code.

---

# 2. Storage Design Principles

The Storage Architecture is based on the following fundamental principles.

---

## Principle 1 — Metadata Defines the Logical Model

Metadata defines:

- object types;
- fields;
- relationships;
- semantics;
- storage requirements.

Storage is responsible only for persistence.

Storage MUST NOT contain business semantics.

---

## Principle 2 — Physical Storage Independence

Business logic MUST NOT depend on:

- SQL dialect;
- table names;
- indexes;
- physical storage layout;
- storage provider implementation.

All physical implementation details are internal to the Storage subsystem.

---

## Principle 3 — Stable Object Identity

Every persistent object MUST have a globally unique identifier.

Object identity MUST remain stable during the entire object lifetime.

Object identifiers MUST NEVER depend on:

- document numbers;
- catalog codes;
- database row identifiers;
- storage provider implementation.

---

## Principle 4 — References Use Object Identity

Every persistent reference MUST point to the unique object identifier.

References MUST NOT depend on:

- names;
- document numbers;
- codes;
- physical database addresses.

---

## Principle 5 — Storage Is Passive

Storage persists data.

Storage MUST NOT execute business logic.

Storage MUST NOT evaluate business rules.

Storage MUST NOT perform document posting.

Storage MUST NOT calculate derived business values.

---

## Principle 6 — Runtime Controls Persistence

Runtime is responsible for:

- object lifecycle;
- validation;
- document posting;
- register generation;
- transaction coordination.

Storage performs persistence requested by Runtime.

---

## Principle 7 — Persistence Is Transactional

Every modification of persistent data MUST occur inside a transaction.

Storage MUST guarantee:

- atomicity;
- consistency;
- isolation;
- durability.

The exact implementation depends on the selected Storage Provider.

---

## Principle 8 — Version-Based Consistency

Every persistent object MUST maintain a version number.

The version number MUST increase only when persistent data changes.

Opening or reading an object MUST NOT modify its version.

---

## Principle 9 — Soft Deletion

Business objects SHOULD use logical deletion.

Logical deletion preserves:

- references;
- historical integrity;
- register consistency;
- auditability.

Physical deletion MAY be performed later by maintenance operations.

---

## Principle 10 — Adaptive Storage

Storage MAY automatically:

- optimize indexes;
- optimize totals;
- reorganize physical structures;
- compact data;
- rebuild storage structures.

These optimizations MUST preserve identical logical behavior.

Application code MUST remain unaware of optimization decisions.

---

# 3. Storage Boundaries

Storage is one of the core platform subsystems.

```
                 +----------------------+
                 |      Metadata        |
                 +----------+-----------+
                            |
                            |
                            v
                 +----------------------+
                 |       Runtime        |
                 +----------+-----------+
                            |
                            |
                            v
                 +----------------------+
                 |       Storage        |
                 +----------+-----------+
                            |
                            |
                            v
                 +----------------------+
                 |  Storage Provider    |
                 +----------------------+
```

Storage forms the boundary between the logical platform model and the physical persistence implementation.

---

## Storage Responsibilities

Storage is responsible for:

- object persistence;
- object loading;
- object updates;
- object deletion;
- reference persistence;
- transaction execution;
- version management;
- storage optimization;
- index management;
- register persistence;
- sequence persistence;
- constant persistence.

---

## Responsibilities Outside Storage

The following responsibilities belong to other subsystems.

### Metadata

- object definitions;
- field definitions;
- type definitions;
- semantics;
- storage metadata.

---

### Runtime

- object lifecycle;
- validation;
- business rules;
- document posting;
- register generation;
- transaction orchestration.

---

### Query Engine

- query planning;
- optimization;
- execution strategy.

---

### UI

- presentation;
- interaction;
- localization.

---

# 4. Storage Components

The Storage subsystem consists of several independent components.

```
Storage
│
├── Storage Manager
├── Storage Provider
├── Transaction Manager
├── Identity Manager
├── Version Manager
├── Index Manager
├── Storage Optimizer
├── Catalog Storage
├── Document Storage
├── Register Storage
├── Constant Storage
└── Sequence Storage
```

---

## Storage Manager

Coordinates all storage operations.

Responsibilities:

- persistence coordination;
- provider abstraction;
- lifecycle coordination.

---

## Storage Provider

Implements physical persistence.

Examples:

- SQLite Provider
- PostgreSQL Provider
- Future Providers

All providers MUST expose identical logical behavior.

---

## Transaction Manager

Responsible for:

- transaction lifecycle;
- commit;
- rollback;
- isolation.

---

## Identity Manager

Responsible for:

- ULID generation;
- identity validation;
- identity consistency.

---

## Version Manager

Responsible for:

- optimistic versioning;
- version updates;
- concurrency validation.

---

## Index Manager

Responsible for:

- system indexes;
- metadata-defined indexes;
- adaptive index optimization.

---

## Storage Optimizer

Responsible for adaptive optimization of physical storage.

Possible optimization tasks include:

- totals optimization;
- index optimization;
- storage compaction;
- statistics collection;
- future adaptive strategies.

Optimization MUST remain transparent to Runtime and application code.

---

## Specialized Storage Components

The Storage subsystem provides specialized persistence services for:

- catalogs;
- documents;
- registers;
- constants;
- sequences.

Each component is responsible only for persistence.

Business behavior remains outside the Storage subsystem.

---

# 5. Storage Providers

## 5.1 Overview

The Storage subsystem SHALL operate through an abstract Storage Provider interface.

A Storage Provider is responsible for implementing the physical persistence layer while preserving the logical behavior defined by the platform architecture.

The Runtime, Metadata subsystem and business logic MUST remain completely independent of the selected Storage Provider.

---

## 5.2 Objectives

The Storage Provider abstraction is designed to achieve the following goals:

- physical storage independence;
- database engine independence;
- transparent migration between providers;
- unified transaction behavior;
- unified object persistence;
- identical logical semantics.

---

## 5.3 Supported Providers

The platform SHALL support multiple Storage Providers.

Typical implementations include:

- SQLite Provider
- PostgreSQL Provider

Additional providers MAY be implemented in the future.

Examples include:

- MariaDB
- Microsoft SQL Server
- Oracle Database
- Distributed storage engines
- Cloud-native storage services

The architecture MUST NOT assume the existence of any specific provider.

---

## 5.4 Provider Responsibilities

Every Storage Provider MUST implement:

- persistent object storage;
- object retrieval;
- object updates;
- object deletion;
- transaction management;
- reference persistence;
- index creation;
- metadata-driven schema generation;
- optimistic concurrency support.

A Storage Provider MUST NOT implement:

- business rules;
- document posting;
- register calculations;
- metadata interpretation;
- UI functionality.

---

## 5.5 Provider Independence

Application code MUST never:

- execute provider-specific SQL;
- reference physical table names;
- depend on provider-specific features;
- rely on implementation details.

All communication SHALL occur through the Storage abstraction.

---

## 5.6 Schema Generation

Physical database structures SHALL be generated automatically from Metadata definitions.

Metadata defines:

- entities;
- fields;
- relationships;
- indexes;
- semantics.

The Storage Provider determines how those definitions are represented physically.

Example:

Metadata:

```
Catalog Product
```

SQLite:

```
product.db
```

PostgreSQL:

```
public.product
```

Future providers MAY choose completely different physical layouts while preserving identical logical behavior.

---

## 5.7 Transactions

Every Storage Provider MUST support transactional persistence.

The implementation MAY differ depending on the capabilities of the underlying database engine.

The Runtime MUST observe identical transactional behavior regardless of the selected provider.

---

## 5.8 Provider Capabilities

Storage Providers MAY expose additional optimization capabilities.

Examples include:

- clustered indexes;
- partial indexes;
- compression;
- partitioning;
- native JSON storage;
- generated columns.

These optimizations MUST remain internal to the Storage Provider.

Metadata and Runtime MUST remain unaffected.

---

## 5.9 Migration

Migration between Storage Providers SHOULD require:

- no Metadata modifications;
- no Runtime modifications;
- no business logic modifications.

Only physical persistence SHALL change.

---

# 6. Identity Model

## 6.1 Purpose

Every persistent object within the platform SHALL possess a globally unique identity.

Object identity exists independently of:

- storage provider;
- document numbering;
- business semantics;
- physical storage.

Identity represents the object itself.

---

## 6.2 ULID

AcCore uses ULID (Universally Unique Lexicographically Sortable Identifier) as the primary identifier for every persistent object.

Every storage entity MUST use ULID as its primary key.

Examples include:

- catalogs;
- documents;
- register records;
- constants;
- sequences;
- table rows.

---

## 6.3 Identity Requirements

An object identifier MUST satisfy the following requirements.

### Globally Unique

No two objects SHALL share the same identifier.

---

### Immutable

The identifier MUST NEVER change during the lifetime of the object.

---

### Provider Independent

Identifiers MUST remain identical regardless of the selected Storage Provider.

---

### Business Independent

Identifiers MUST NOT contain:

- document numbers;
- catalog codes;
- names;
- business meaning.

---

### Stable References

References MUST remain valid throughout the lifetime of the referenced object.

---

## 6.4 Identity Generation

Identity generation SHALL be performed by the Identity Manager.

The Storage Provider MUST NOT generate business object identifiers independently.

This guarantees identical identity behavior across all providers.

---

## 6.5 Root Objects

Objects without a parent SHALL use:

```
parent_id = NULL
```

NULL represents the absence of a parent.

It is not a valid object identifier.

The Root object itself does not exist as a persistent entity.

---

## 6.6 Object Lifetime

The object identity remains unchanged during:

- updates;
- version changes;
- document posting;
- storage optimization;
- migration between providers.

Identity SHALL change only when a new object is created.

---

## 6.7 Identity and Version

Identity and version represent different concepts.

Identity answers:

> Which object is this?

Version answers:

> Which revision of this object is stored?

Changing the version MUST NOT affect object identity.

---

## 6.8 Identity and Business Keys

Business identifiers are independent from object identity.

Examples include:

- document number;
- product code;
- barcode;
- tax identification number.

These values MAY change.

The ULID MUST NOT.

---

## 6.9 Identity and References

All persistent references SHALL store the ULID of the referenced object.

References MUST NEVER depend on:

- document numbers;
- names;
- catalog codes;
- storage row identifiers.

---

## 6.10 Identity Serialization

Object identity MUST be serializable without loss of information.

Serialization format SHALL remain identical across all supported platforms.

This guarantees interoperability between:

- Storage;
- Runtime;
- APIs;
- import/export mechanisms;
- distributed deployments.

---

## 6.11 Future Extensions

Future versions MAY introduce additional identity-related services, including:

- distributed identity generation;
- identity validation;
- identity diagnostics;
- identity tracing.

These extensions MUST preserve full backward compatibility with the existing ULID model.

---

# 7. Reference Model

## 7.1 Purpose

The Reference Model defines how persistent relationships between objects are represented within the AcCore platform.

All persistent references SHALL be based exclusively on object identity.

References provide logical relationships between business objects while remaining completely independent of the underlying Storage Provider.

---

## 7.2 Reference Principles

Every persistent reference MUST satisfy the following principles:

- stable;
- provider-independent;
- metadata-driven;
- type-safe;
- immutable with respect to the referenced object identity.

---

## 7.3 Reference Representation

Every persistent reference SHALL store the ULID of the referenced object.

Example:

```
Document
    Customer → ULID
```

The reference SHALL NOT store:

- object name;
- object code;
- document number;
- physical row identifier.

---

## 7.4 Reference Integrity

The Storage subsystem MUST preserve referential integrity.

A reference MUST either:

- reference an existing object; or
- be NULL when explicitly allowed by Metadata.

Broken references MUST NOT exist.

---

## 7.5 Nullable References

Metadata MAY define a reference as optional.

Optional references SHALL be represented by NULL.

NULL indicates the absence of a referenced object.

NULL is not considered an object identifier.

---

## 7.6 Reference Types

The platform distinguishes logical reference types rather than physical database references.

Typical examples include:

- Reference<Catalog>
- Reference<Document>
- Reference<Constant>

Future platform versions MAY introduce additional specialized reference types.

---

## 7.7 Parent References

Hierarchical objects SHALL use:

```
parent_id
```

Rules:

- NULL represents the root level.
- Parent MUST reference an object of the same catalog.
- Circular references MUST NOT be allowed.

---

## 7.8 Cascading Operations

Deletion SHALL follow logical platform rules rather than database-specific cascading behavior.

Storage Providers MUST NOT perform automatic cascading deletes independently.

Deletion policies SHALL be coordinated by Runtime.

Example:

```
Delete Folder
        │
        ▼
Runtime Validation
        │
        ▼
Storage Transaction
```

---

## 7.9 Reference Resolution

Reference resolution SHALL occur through Runtime.

Storage returns object identities.

Runtime resolves identities into business objects.

This separation preserves Storage independence.

---

## 7.10 Future Extensions

Future versions MAY support:

- lazy reference resolution;
- distributed references;
- cached reference resolution;
- cross-storage references.

These extensions MUST preserve compatibility with the existing Reference Model.

---

# 8. Platform Type System

## 8.1 Purpose

The Storage subsystem persists values defined by the AcCore Platform Type System.

The Platform Type System itself is specified in the separate document:

**TYPE_SYSTEM.md**

This section defines only the storage-related requirements for Platform Types.

---

## 8.2 Storage Independence

Storage SHALL persist Platform Types independently of the underlying database engine.

Application code, Metadata and Runtime MUST operate exclusively on Platform Types.

Storage Providers are responsible for mapping Platform Types to native database types.

---

## 8.3 Type Mapping

Each Storage Provider SHALL provide a deterministic mapping between Platform Types and native storage types.

Example:

```
Platform Type
        │
        ▼
Storage Provider
        │
        ▼
Native Database Type
```

Different Storage Providers MAY choose different native representations.

Logical behavior MUST remain identical.

---

## 8.4 Serialization

Every Platform Type MUST define a deterministic serialization format.

Serialization SHALL remain consistent across:

- Storage Providers;
- Runtime;
- APIs;
- import/export;
- distributed deployments.

Serialization rules are defined by the Platform Type System specification.

---

## 8.5 Persistence Requirements

Storage SHALL preserve:

- value precision;
- value scale;
- type semantics;
- object identity;
- reference integrity.

Storage Providers MUST NOT modify Platform Type semantics.

---

## 8.6 Semantic Types

Semantic Types provide additional business meaning while remaining Storage-independent.

Storage SHALL preserve semantic values without interpreting their business purpose.

Examples include:

- Money
- Quantity
- Barcode
- DocumentNumber

The complete definition of Semantic Types is specified in **TYPE_SYSTEM.md**.

---

## 8.7 References

Reference Types SHALL always be persisted using the Platform Reference Model defined by this specification.

Reference semantics are independent of the physical storage implementation.

---

## 8.8 Compatibility

All Storage Providers MUST provide identical logical behavior for every Platform Type.

Physical representation MAY differ.

Logical semantics MUST remain identical.

---

# 9. Storage Entities

## 9.1 Overview

Storage Entities define the persistent representation of business data within the AcCore platform.

A Storage Entity describes how data is persisted, identified and versioned independently of Runtime objects and Metadata definitions.

Storage Entities are internal to the Storage subsystem.

Business logic MUST NOT interact with Storage Entities directly.

The Runtime subsystem is responsible for translating Runtime Objects into Storage Entities and vice versa.

---

## Storage Entity Hierarchy

```
Storage Entity
        │
        ▼
Persistent Entity
        │
        ├──────────────┐
        │              │
        ▼              ▼
Table Storage     Scalar Storage
Entity            Entity
        │              │
        │              ├── Constant Storage Entity
        │              └── Sequence Storage Entity
        │
        ├── Catalog Storage Entity
        ├── Document Storage Entity
        └── Register Storage Entity
```

Storage Entities define persistence only.

Business semantics remain defined by Metadata.

---

# 9.2 Persistent Entity

## Purpose

Persistent Entity is the abstract base model for every object that participates in persistent storage.

It defines the common persistence contract shared by all Storage Entities.

Persistent Entity is a conceptual model.

It MUST NOT exist as a physical table.

---

## Responsibilities

Every Persistent Entity SHALL provide:

- global identity;
- version management;
- transaction participation;
- lifecycle support.

---

## Identity

Every Persistent Entity MUST possess a globally unique ULID.

Identity SHALL remain immutable throughout the lifetime of the entity.

---

## Version

Every Persistent Entity MUST maintain an optimistic version number.

The version SHALL increase only when persistent data changes.

Read operations MUST NOT modify the version.

---

## Lifecycle

Persistent Entities participate in the following lifecycle:

```
Create
    │
    ▼
Persist
    │
    ▼
Update
    │
    ▼
Delete (Logical)
```

Storage implementations MAY physically remove deleted entities during maintenance operations.

---

## Transactions

Every Persistent Entity MUST participate in Storage transactions.

Creation, modification and deletion SHALL occur only inside an active transaction.

---

## Provider Independence

Persistent Entities MUST remain independent of:

- SQL dialect;
- Storage Provider;
- physical table layout;
- indexing strategy.

---

## Common Properties

Conceptually every Persistent Entity contains:

```
id
version
created_at
updated_at
deleted
```

Specialized Storage Entities MAY extend this property set.

---

# 9.3 Table Storage Entity

## Purpose

Table Storage Entity represents persistent business data organized as rows and columns.

It is the foundation for all table-based business objects.

Examples include:

- catalogs;
- documents;
- registers.

---

## Design Principles

A Table Storage Entity SHALL:

- define a logical table;
- contain multiple rows;
- support indexes;
- support transactions;
- support optimistic versioning.

---

## Row Identity

Every row MUST possess its own ULID.

Rows SHALL remain uniquely identifiable independently of their position within the table.

---

## Field Definitions

Fields are defined by Metadata.

Storage SHALL persist field values without interpreting their business meaning.

The Storage subsystem MUST NOT implement business validation.

---

## Indexes

Table Storage Entities MAY define:

- system indexes;
- metadata-defined indexes;
- provider-specific optimization indexes.

Index implementation is Storage Provider specific.

Logical behavior MUST remain identical.

---

## Relationships

Rows MAY reference:

- rows of the same entity;
- rows of another entity;
- scalar storage entities.

All relationships SHALL use the Platform Reference Model.

---

## Hierarchical Tables

Some Table Storage Entities MAY define hierarchical relationships.

Hierarchy SHALL be represented through:

```
parent_id
```

The existence of hierarchy is determined exclusively by Metadata.

Storage SHALL NOT assume that every table is hierarchical.

---

## Soft Deletion

Rows SHOULD use logical deletion.

Logical deletion preserves:

- references;
- historical integrity;
- register consistency;
- auditability.

Physical removal MAY occur later.

---

## Extensibility

Future versions MAY extend Table Storage Entities with:

- partitioning;
- compression;
- column-oriented storage;
- distributed storage;
- adaptive indexing.

Such extensions MUST remain transparent to Runtime and application code.

---

# 9.4 Scalar Storage Entity

## Purpose

Scalar Storage Entity represents persistent values that are not naturally modeled as tables.

Scalar Storage Entities store a single logical value rather than collections of rows.

Examples include:

- platform constants;
- numbering sequences.

---

## Design Principles

Scalar Storage Entities SHALL:

- possess a unique identity;
- participate in transactions;
- support optimistic versioning;
- remain provider-independent.

---

## Value Representation

A Scalar Storage Entity contains a single logical value.

Examples:

```
Constant

VATRate = 20%
```

```
Sequence

InvoiceNumber = 15427
```

The physical representation is Storage Provider specific.

---

## Versioning

Scalar values SHALL participate in optimistic versioning using the same rules as all Persistent Entities.

---

## Transactions

Updates of scalar values MUST occur inside Storage transactions.

---

## Extensibility

Future platform versions MAY introduce additional Scalar Storage Entities without modifying the Storage architecture.

Possible examples include:

- platform settings;
- runtime statistics;
- storage configuration values.

---

# 9.5 Catalog Storage Entity

## Purpose

Catalog Storage Entity defines the persistent representation of catalog objects.

Catalogs represent long-lived business entities referenced by documents, registers and other business objects.

Examples include:

- Products
- Customers
- Suppliers
- Warehouses
- Employees
- Currencies
- Measure Units

Catalog Storage Entity defines persistence only.

Business behavior remains defined by Metadata and Runtime.

---

## Design Principles

Every Catalog Storage Entity SHALL:

- inherit Persistent Entity;
- inherit Table Storage Entity;
- support optimistic versioning;
- support transactions;
- support references;
- optionally support hierarchy.

---

## System Fields

Every Catalog Storage Entity SHALL contain the following system fields.

| Field | Description |
|---------|-------------|
| id | Object identity (ULID) |
| version | Optimistic version |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |
| deleted | Logical deletion flag |

If hierarchy is enabled by Metadata, the following additional fields SHALL exist.

| Field | Description |
|---------|-------------|
| parent_id | Parent catalog item |
| is_folder | Folder indicator |

Hierarchy support SHALL be determined exclusively by Metadata.

---

## Required Business Fields

Every catalog SHALL contain at least one mandatory business field.

| Field | Description |
|---------|-------------|
| name | Primary business name |

The exact set of required fields SHALL be defined by Metadata.

---

## Metadata-Defined Fields

Additional catalog fields SHALL be defined by Metadata.

Metadata specifies:

- field name;
- platform type;
- semantic type;
- default value;
- constraints;
- indexing requirements.

Storage SHALL persist these values without interpreting their business meaning.

---

## Semantic Fields

Metadata MAY define semantic fields.

Examples include:

- CODE
- BARCODE
- EMAIL
- PHONE
- URL

Semantic fields provide additional meaning to Runtime while remaining ordinary persisted values for Storage.

Storage MUST NOT interpret semantic values.

---

## User-Defined Fields

Metadata MAY allow user-defined fields.

User-defined fields SHALL be persisted using the Entity-Attribute-Value (EAV) model.

The EAV implementation SHALL remain transparent to Runtime and application code.

Metadata determines whether user-defined fields are permitted.

---

## Hierarchy

Catalog hierarchy SHALL be optional.

If hierarchy is enabled:

- parent_id SHALL reference another catalog item;
- NULL indicates the root level;
- circular references MUST NOT be allowed.

Storage SHALL NOT assume hierarchy unless Metadata explicitly enables it.

---

## Deletion

Catalog objects SHOULD use logical deletion.

Before logical deletion, Runtime SHALL validate:

- existing references;
- child objects;
- business rules.

Storage SHALL perform only the persistence operation.

---

## References

Catalogs MAY be referenced by:

- documents;
- registers;
- other catalogs;
- constants;
- application objects.

All references SHALL use the Platform Reference Model.

---

# 9.6 Document Storage Entity

## Purpose

Document Storage Entity defines the persistent representation of business documents.

Documents represent business events that may generate register movements.

Examples include:

- Sales Invoice
- Purchase Invoice
- Goods Receipt
- Payment
- Inventory Adjustment

Persistence and business behavior remain separate responsibilities.

---

## Design Principles

Every Document Storage Entity SHALL:

- inherit Persistent Entity;
- inherit Table Storage Entity;
- support optimistic versioning;
- support transactions;
- support document numbering;
- support posting.

---

## System Fields

Every Document Storage Entity SHALL contain:

| Field | Description |
|---------|-------------|
| id | Object identity (ULID) |
| version | Optimistic version |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |
| deleted | Logical deletion flag |

---

## Document Fields

Every document SHALL define:

| Field | Description |
|---------|-------------|
| document_date | Business date |
| document_number | Business number |
| posted | Posting state |

Additional document fields SHALL be defined by Metadata.

---

## Document Number

Document numbers are business identifiers.

Document numbers:

- MAY change;
- MUST remain independent of object identity;
- SHALL be generated by the platform numbering subsystem.

Object identity SHALL always be represented by ULID.

---

## Document Structure

A document SHALL consist of:

- document header;
- one or more tabular sections.

Header fields and tabular sections are defined by Metadata.

---

## Tabular Sections

Each tabular section SHALL be represented as an independent Table Storage Entity.

Each row SHALL possess:

- its own ULID;
- optimistic version;
- transaction participation.

Rows SHALL reference the owning document through object identity.

---

## Posting

Documents MAY exist in either state:

- Posted
- Unposted

Posting state SHALL be represented by the field:

```
posted
```

Posting logic belongs to the Posting Engine.

Storage persists only the posting state.

---

## Register Movements

Storage SHALL NOT generate register movements.

Register movements are produced by the Posting Engine.

Storage persists generated movements inside Storage transactions.

---

## Versioning

Document version SHALL increase only when persistent document data changes.

Repeated posting without data modifications MUST NOT increment the document version.

---

## References

Documents MAY reference:

- catalogs;
- documents;
- constants;
- registers (indirectly through posting);
- other business objects.

All references SHALL use ULID identities.

---

## Deletion

Documents SHOULD use logical deletion.

Runtime SHALL determine whether deletion is permitted.

Storage performs only persistence.

---

# 9.7 Register Storage Entity

## Purpose

Register Storage Entity defines the persistent representation of platform registers.

Registers store business facts generated by documents or maintained independently of document posting.

Register Storage Entity is an abstract storage model.

Concrete register implementations SHALL inherit from this entity.

---

## Register Types

The platform defines two register categories.

```
Register Storage Entity
        │
        ├──────────────┐
        │              │
        ▼              ▼
Accumulation      Information
Register          Register
```

Additional register types MAY be introduced in future platform versions without modifying the Storage architecture.

---

## Common Design Principles

Every Register Storage Entity SHALL:

- inherit Persistent Entity;
- inherit Table Storage Entity;
- support optimistic versioning;
- support transactions;
- support references;
- support adaptive optimization.

Register behavior is defined by Metadata and Runtime.

Storage is responsible only for persistence.

---

## Common System Fields

Every register record SHALL contain:

| Field | Description |
|---------|-------------|
| id | Record identity (ULID) |
| version | Optimistic version |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |

Additional fields are determined by the concrete register type.

---

# 9.7.1 Accumulation Register Storage Entity

## Purpose

Accumulation Registers store business movements that affect balances.

Typical examples include:

- Inventory
- Cash
- Accounts Receivable
- Accounts Payable

---

## Movement Model

Every movement SHALL contain:

| Field | Description |
|---------|-------------|
| period | Business timestamp |
| document_id | Source document |
| line_no | Source line number |
| movement_type | INCOME or EXPENSE |

Movement type SHALL explicitly define the business direction.

Resource values SHALL remain positive.

---

## Dimensions

Dimensions identify the balance being affected.

Examples:

- Product
- Warehouse
- Customer
- Currency

Dimensions are defined by Metadata.

---

## Resources

Resources represent accumulated values.

Examples:

- Quantity
- Amount
- Weight

Resources SHALL use Platform Types.

---

## Totals

Accumulation Registers SHALL maintain totals separately from movement records.

Totals SHALL be managed by the Totals Engine.

Storage persists both movements and totals.

---

## Adaptive Totals

Metadata defines the logical totals policy.

Storage MAY automatically optimize the physical totals strategy.

Possible physical strategies include:

- Yearly
- Quarterly
- Monthly
- Daily

Automatic optimization MUST preserve identical logical behavior.

---

## Posting

Register movements SHALL be generated exclusively by the Posting Engine.

Storage MUST NOT calculate movements independently.

---

# 9.7.2 Information Register Storage Entity

## Purpose

Information Registers store business facts that do not represent accumulation.

Typical examples include:

- Exchange Rates
- Product Prices
- User Settings
- Tax Rates

---

## Record Structure

Information Register records SHALL contain:

- dimensions;
- attributes;
- optional period.

The exact structure is defined by Metadata.

---

## Periodicity

Metadata MAY define an Information Register as:

- non-periodic;
- periodic.

If periodic, every record SHALL contain:

```
period
```

---

## Versioning

Information Register records participate in optimistic versioning using the same rules as all Persistent Entities.

---

## References

Information Registers MAY reference:

- catalogs;
- documents;
- constants;
- other registers.

All references SHALL use the Platform Reference Model.

---

# 9.8 Constant Storage Entity

## Purpose

Constant Storage Entity represents persistent platform constants.

Constants store global configuration values shared across the platform.

Examples include:

- Default Currency
- Company Name
- VAT Rate
- Accounting Start Date

---

## Design Principles

Every Constant Storage Entity SHALL:

- inherit Persistent Entity;
- inherit Scalar Storage Entity;
- support transactions;
- support optimistic versioning.

---

## Storage

Each constant stores exactly one logical value.

The value type is defined by Metadata.

Storage SHALL preserve the value without interpreting its business meaning.

---

## References

Constants MAY reference any Platform Type, including object references.

Reference integrity SHALL be preserved by Storage.

---

# 9.9 Sequence Storage Entity

## Purpose

Sequence Storage Entity provides persistent numbering sequences.

Sequences generate business identifiers while remaining independent from object identity.

Examples include:

- Invoice Numbers
- Order Numbers
- Payment Numbers

---

## Design Principles

Every Sequence Storage Entity SHALL:

- inherit Persistent Entity;
- inherit Scalar Storage Entity;
- support transactions;
- guarantee uniqueness.

---

## Identity

Generated sequence values SHALL NOT be used as object identity.

Object identity is always represented by ULID.

---

## Concurrency

Sequence generation MUST remain transaction-safe.

Concurrent requests MUST NOT produce duplicate values.

---

## Numbering Policies

Metadata MAY define numbering policies.

Examples include:

- Continuous
- Yearly
- Monthly
- User-defined

Storage persists sequence state.

Number generation rules belong to the Numbering subsystem.

---

## Future Extensions

Future versions MAY support:

- distributed sequences;
- cached sequence allocation;
- high-performance sequence generators.

Such extensions MUST preserve logical numbering semantics.

---
# Preview — Logical Storage Models

The previous sections of this specification define the architectural contracts of the Storage subsystem, including Storage Providers, Identity Model, Reference Model and Storage Entities.

This part defines the logical storage models used to persist business data.

A Logical Storage Model specifies how a particular category of business objects is represented within the Storage subsystem while remaining independent of any physical database implementation.

Logical Storage Models define:

- persistent structure;
- storage responsibilities;
- lifecycle participation;
- relationships;
- versioning;
- transaction behavior.

Logical Storage Models do not define:

- business rules;
- business validation;
- user interface behavior;
- query optimization;
- document posting logic.

These responsibilities belong to other platform subsystems.

Every Logical Storage Model SHALL:

- inherit the common persistence rules defined by this specification;
- remain independent of the selected Storage Provider;
- preserve identical logical behavior across all supported database engines;
- expose a stable contract to the Runtime subsystem.

The following Logical Storage Models are defined by the AcCore platform:

- Catalog Storage Model;
- Document Storage Model;
- Register Storage Model.

# 10. Catalog Storage Model

## 10.1 Overview

Catalog Storage Model defines the logical persistence model for catalog entities.

Catalogs represent long-lived business objects that are referenced throughout the platform.

Typical examples include:

- Products
- Customers
- Suppliers
- Employees
- Warehouses
- Currencies
- Measure Units

Catalog Storage Model defines how catalog data is persisted, versioned and referenced.

Business behavior, validation rules and user interaction remain outside the scope of Storage.

---

## 10.2 Design Goals

The Catalog Storage Model is designed to satisfy the following goals.

### Metadata Driven

Catalog structure SHALL be defined entirely by Metadata.

Storage MUST NOT require manual schema definition.

---

### Provider Independence

Catalog persistence MUST remain independent of the selected Storage Provider.

Catalog behavior SHALL remain identical across all supported providers.

---

### Extensibility

Catalogs MUST support extension through Metadata without requiring Storage architecture changes.

---

### Scalability

The model SHALL support:

- small embedded databases;
- medium business installations;
- large enterprise deployments.

---

### Transparency

Runtime and application code MUST interact with logical fields only.

Physical storage details SHALL remain hidden inside the Storage subsystem.

---

## 10.3 Logical Structure

Every catalog consists of the following logical layers.

```
Catalog
│
├── System Fields
│
├── Metadata Fields
│
├── Semantic Fields
│
└── User-defined Fields
```

Each layer serves a different purpose.

Storage SHALL expose a unified logical view regardless of physical implementation.

---

## 10.4 Logical Field Model

### Purpose

The Logical Field Model defines the relationship between Metadata, Runtime and Storage.

For Metadata and Runtime there exists only one concept:

```
Field
```

Storage determines how the field is physically persisted.

---

### Logical Field Principle

Metadata defines fields.

Runtime consumes fields.

Storage persists fields.

Neither Metadata nor Runtime SHALL depend on the physical storage strategy.

---

### Physical Storage Transparency

A logical field MAY be stored in:

```
Main Storage
```

or

```
EAV Storage
```

The choice is an internal Storage implementation detail.

Runtime MUST NOT distinguish between these storage mechanisms.

---

### Unified Access Model

All fields SHALL be accessed through a unified logical interface.

Examples:

```
Product.Name
```

```
Product.Barcode
```

```
Product.CustomAttribute
```

Runtime SHALL observe identical behavior regardless of physical storage location.

---

### Future Compatibility

Future Storage implementations MAY introduce additional persistence strategies.

Examples include:

- column-oriented storage;
- compressed storage;
- distributed storage;
- external storage providers.

The Logical Field Model MUST remain unchanged.

---

## 10.5 System Fields

### Purpose

System Fields provide platform-level functionality required by all catalog entities.

System Fields are defined by the platform and SHALL exist independently of Metadata.

---

### Core System Fields

Every Catalog Storage Entity SHALL contain the following fields.

| Field | Description |
|---------|-------------|
| id | Object identity (ULID) |
| version | Optimistic version |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |
| deleted | Logical deletion flag |

These fields SHALL be managed by the platform.

Application code MUST NOT modify them directly.

---

### Hierarchy Fields

If hierarchy is enabled by Metadata, the following additional fields SHALL exist.

| Field | Description |
|---------|-------------|
| parent_id | Parent catalog item |
| is_folder | Folder indicator |

If hierarchy is disabled, these fields MAY be omitted by the Storage implementation.

---

### Identity

The field:

```
id
```

SHALL contain the unique ULID of the catalog object.

Identity MUST remain immutable during the entire object lifetime.

---

### Version

The field:

```
version
```

SHALL support optimistic concurrency control.

The version SHALL increase only when persistent data changes.

---

### Timestamps

The fields:

```
created_at
updated_at
```

SHALL be managed automatically by the platform.

Storage Providers MAY use provider-specific timestamp implementations.

Logical behavior MUST remain identical.

---

### Logical Deletion

The field:

```
deleted
```

SHALL indicate logical deletion status.

Logical deletion preserves:

- references;
- historical integrity;
- auditability.

Physical deletion MAY occur later.

---

## 10.6 Metadata Fields

### Purpose

Metadata Fields define the business structure of a catalog.

Metadata determines:

- field names;
- types;
- semantics;
- constraints;
- indexes;
- default values.

Storage SHALL persist Metadata Fields without interpreting their business meaning.

---

### Field Definitions

Every Metadata Field SHALL be defined by Metadata.

Typical properties include:

- field_name;
- platform_type;
- semantic;
- nullable;
- default_value;
- indexed.

Additional properties MAY be introduced by future Metadata versions.

---

### Business Fields

Examples of Metadata Fields include:

```
name
```

```
full_name
```

```
description
```

```
manufacturer
```

```
weight
```

Storage SHALL treat these fields as ordinary persisted values.

---

### Required Fields

Metadata MAY define fields as mandatory.

Validation of required fields belongs to Runtime.

Storage SHALL persist values provided by Runtime.

---

### Constraints

Metadata MAY define constraints.

Examples include:

- uniqueness;
- maximum length;
- value range.

Storage MAY assist in constraint enforcement.

The authoritative validation logic belongs to Runtime.

---

### Type Preservation

Storage SHALL preserve:

- platform type;
- value precision;
- value scale;
- serialization format.

Type semantics are defined by the Platform Type System.

---

## 10.7 Semantic Fields

### Purpose

Semantic Fields are Metadata Fields with predefined platform meaning.

Semantic Fields allow Runtime and platform services to provide specialized behavior while preserving Storage independence.

Storage SHALL persist Semantic Fields as ordinary field values.

Storage MUST NOT interpret semantic meaning.

---

### Semantic Definition

Metadata MAY assign a semantic identifier to a field.

Examples include:

- CODE
- BARCODE
- EMAIL
- PHONE
- URL

Additional semantic identifiers MAY be introduced by future platform versions.

---

### Semantic Contracts

Semantic identifiers define platform-level expectations.

Example:

```
BARCODE
```

indicates that the field contains barcode values.

Runtime MAY provide:

- barcode search;
- barcode validation;
- barcode scanning integration.

Storage remains unaware of these behaviors.

---

### Field Names

Field names and semantic identifiers are independent concepts.

Example:

```
field_name = product_barcode
semantic   = BARCODE
```

or

```
field_name = barcode
semantic   = BARCODE
```

Runtime behavior SHALL be determined by the semantic identifier rather than the field name.

---

### Storage Requirements

Storage SHALL:

- persist semantic identifiers;
- preserve semantic metadata;
- remain independent of semantic interpretation.

---

## 10.8 User-defined Fields (EAV)

### Purpose

User-defined Fields provide catalog extensibility without requiring schema modifications.

User-defined Fields SHALL be implemented using the Entity-Attribute-Value (EAV) model.

---

### Design Goals

The EAV model is intended to support:

- customer-specific extensions;
- industry-specific attributes;
- configuration-level customization;
- future schema evolution.

---

### Logical Model

For Runtime and Metadata, a User-defined Field is indistinguishable from any other logical field.

Example:

```
Product.CustomAttribute
```

Runtime SHALL access the field using the same mechanisms as Metadata Fields.

---

### Physical Transparency

Storage MAY persist User-defined Fields separately from the primary catalog structure.

Example:

```
Catalog Item
        │
        ▼
User-defined Field Values
```

This separation SHALL remain invisible outside the Storage subsystem.

---

### Metadata Definition

Each User-defined Field SHALL possess Metadata describing:

- field_name;
- platform_type;
- semantic (optional);
- default value;
- indexing requirements.

---

### Future Optimization

Storage MAY optimize EAV persistence using:

- caching;
- denormalization;
- materialization;
- adaptive indexing.

Logical behavior MUST remain unchanged.

---

## 10.9 Hierarchy

### Purpose

Catalogs MAY support hierarchical organization.

Hierarchy support SHALL be enabled or disabled through Metadata.

---

### Hierarchical Fields

Hierarchical catalogs SHALL contain:

| Field | Description |
|---------|-------------|
| parent_id | Parent catalog item |
| is_folder | Folder indicator |

---

### Root Objects

Objects located at the root level SHALL contain:

```
parent_id = NULL
```

NULL indicates the absence of a parent object.

---

### Folder Semantics

Objects with:

```
is_folder = true
```

represent grouping nodes.

Objects with:

```
is_folder = false
```

represent ordinary catalog items.

Metadata MAY restrict allowed hierarchy combinations.

---

### Hierarchy Integrity

Storage SHALL preserve hierarchy integrity.

The following conditions MUST NOT occur:

- circular references;
- self-references;
- invalid parent references.

Runtime SHALL perform business validation.

Storage SHALL preserve structural consistency.

---

### Deletion Behavior

Deletion of a folder containing child objects SHALL require explicit Runtime approval.

Typical behavior MAY include:

- deletion rejection;
- recursive logical deletion;
- user confirmation workflow.

Storage performs only persistence operations.

---

## 10.10 References

### Purpose

Catalog objects participate extensively in platform relationships.

References SHALL use the Platform Reference Model.

---

### Reference Representation

References SHALL store:

```
Referenced Object ULID
```

References MUST NOT depend on:

- names;
- codes;
- document numbers;
- physical storage identifiers.

---

### Reference Integrity

Storage SHALL preserve referential integrity.

A reference MUST either:

- reference an existing object; or
- contain NULL when allowed by Metadata.

---

### Cross-Catalog References

Catalogs MAY reference:

- other catalogs;
- documents;
- constants;
- registers.

Storage SHALL remain agnostic regarding business meaning.

---

## 10.11 Indexing

### Purpose

Indexes improve retrieval performance.

Indexing strategy SHALL remain independent of Runtime and application code.

---

### System Indexes

Storage SHALL automatically create indexes required for:

- object identity;
- versioning;
- hierarchy support;
- referential integrity.

---

### Metadata Indexes

Metadata MAY define additional indexes.

Examples include:

- CODE
- BARCODE
- EMAIL
- custom business fields

Storage Providers SHALL implement indexes using native capabilities.

---

### Adaptive Indexing

Storage MAY automatically create, modify or remove physical indexes.

Such optimizations MUST preserve identical logical behavior.

---

## 10.12 Lifecycle

### Purpose

Catalog objects participate in a standardized persistence lifecycle.

---

### Lifecycle States

Catalog objects SHALL follow the lifecycle:

```
Create
    │
    ▼
Persist
    │
    ▼
Update
    │
    ▼
Logical Delete
```

---

### Creation

Creation SHALL generate:

- ULID identity;
- version;
- timestamps.

Creation MUST occur within a transaction.

---

### Modification

Updates SHALL preserve:

- object identity;
- reference integrity;
- version consistency.

---

### Logical Deletion

Logical deletion SHALL preserve:

- references;
- history;
- register consistency.

Storage MAY physically remove deleted objects later.

---

## 10.13 Versioning

### Purpose

Catalogs SHALL use optimistic concurrency control.

---

### Version Increment

Version SHALL increase only when persistent data changes.

Examples:

```
Name changed
```

→ version increases

```
Object loaded
```

→ version unchanged

---

### Concurrent Updates

Storage SHALL detect version conflicts.

Conflict resolution belongs to Runtime.

---

### Identity Independence

Version and identity represent different concepts.

Changing version MUST NOT affect identity.

---

## 10.14 Transactions

### Purpose

All catalog modifications SHALL occur inside transactions.

---

### Transaction Scope

The following operations SHALL require transactions:

- create;
- update;
- delete;
- hierarchy modification;
- reference modification.

---

### Consistency

Transactions SHALL guarantee:

- atomicity;
- consistency;
- isolation;
- durability.

Provider-specific implementations MAY differ.

Logical behavior MUST remain identical.

---

## 10.15 Extensibility

The Catalog Storage Model SHALL support future extensions without requiring architectural redesign.

Possible future extensions include:

- distributed catalogs;
- column-oriented persistence;
- catalog partitioning;
- adaptive storage layouts;
- advanced search indexes.

Such extensions MUST preserve compatibility with the logical model defined by this specification.

---

# 11. Document Storage Model

## 11.1 Overview

Document Storage Model defines the logical persistence model for business documents.

Documents represent business events occurring at a specific point in time.

Typical examples include:

- Sales Invoice
- Purchase Invoice
- Goods Receipt
- Payment Order
- Inventory Adjustment
- Production Order

Documents may generate register movements through the Posting Engine.

The Storage subsystem is responsible only for document persistence.

Document behavior, validation rules and posting logic remain outside the scope of Storage.

---

## 11.2 Design Goals

The Document Storage Model is designed to satisfy the following goals.

### Event Representation

Documents SHALL represent business events.

A document records the state of a business operation at a specific moment.

---

### Metadata Driven

Document structure SHALL be defined entirely by Metadata.

Storage MUST NOT require manual schema definition.

---

### Provider Independence

Document persistence SHALL remain independent of the selected Storage Provider.

Logical behavior MUST remain identical across all supported providers.

---

### Transactional Consistency

Documents SHALL participate in transactional persistence.

Document data MUST remain internally consistent.

---

### Posting Independence

Storage SHALL persist document state.

Storage MUST NOT implement posting logic.

---

## 11.3 Logical Structure

Every document consists of two logical parts:

```
Document
│
├── Header
│
└── Tabular Sections
        │
        ├── Row
        ├── Row
        └── Row
```

The Header stores document-level information.

Tabular Sections store collections of business records associated with the document.

---

## 11.4 Document Header

### Purpose

The Header contains document attributes describing the business event.

Examples include:

- document date;
- customer;
- supplier;
- warehouse;
- currency;
- comments.

The exact structure is defined by Metadata.

---

### System Fields

Every document SHALL contain the following system fields.

| Field | Description |
|---------|-------------|
| id | Object identity (ULID) |
| version | Optimistic version |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |
| deleted | Logical deletion flag |

---

### Document Fields

Every document SHALL additionally contain:

| Field | Description |
|---------|-------------|
| document_date | Business date |
| document_number | Business number |
| posted | Posting state |

Additional fields SHALL be defined by Metadata.

---

## 11.5 Tabular Sections

### Purpose

Tabular Sections store collections of business records associated with the document.

Examples include:

- products;
- services;
- accounting entries;
- inventory movements;
- payment allocations.

---

### Definition

Tabular Sections SHALL be defined by Metadata.

A document MAY contain:

- no tabular sections;
- one tabular section;
- multiple tabular sections.

---

### Row Identity

Every tabular section row SHALL possess its own ULID.

Row identity remains independent of:

- row position;
- document number;
- physical storage implementation.

---

### Ownership

Every row SHALL reference its owning document.

Ownership SHALL be represented through object identity.

---

### Fields

Rows MAY contain:

- Metadata Fields;
- Semantic Fields;
- References.

The Logical Field Model defined by this specification applies equally to tabular section rows.

---

### Versioning

Tabular section modifications SHALL participate in document versioning.

Changes to tabular section data SHALL increment the document version.

---

## 11.6 Document Numbering

### Purpose

Document numbers provide business identification.

Document numbers are intended for:

- user interaction;
- reporting;
- printed forms;
- business communication.

---

### Identity Independence

Document numbers MUST NOT be used as object identity.

The following concepts are independent:

```
ULID
```

and

```
Document Number
```

ULID identifies the object.

Document Number identifies the business document.

---

### Number Generation

Document numbers SHALL be generated by the Numbering subsystem.

Storage persists generated numbers.

Storage MUST NOT implement numbering logic.

---

### Numbering Policies

Supported numbering policies MAY include:

- continuous numbering;
- yearly numbering;
- monthly numbering;
- custom numbering.

Number generation rules are outside the scope of Storage.

---

## 11.7 Posting State

### Purpose

Documents MAY participate in posting.

Posting transforms document data into register movements.

---

### State Representation

Posting state SHALL be represented by:

```
posted
```

Possible values include:

```
true
false
```

---

### Storage Responsibilities

Storage SHALL:

- persist posting state;
- version posting state changes;
- include posting state in transactions.

Storage MUST NOT:

- calculate register movements;
- validate posting rules;
- determine posting eligibility.

---

## 11.8 Register Integration

### Purpose

Documents may serve as sources of register movements.

---

### Responsibility Separation

The following responsibilities belong to the Posting Engine:

- movement generation;
- movement recalculation;
- movement reversal;
- register updates.

Storage persists the resulting data.

---

### Traceability

Register movements SHOULD maintain references to:

- source document;
- source tabular section row (when applicable).

This allows complete traceability between documents and registers.

---

## 11.9 Lifecycle

Documents SHALL participate in the standard persistence lifecycle.

```
Create
    │
    ▼
Persist
    │
    ▼
Modify
    │
    ▼
Post / Unpost
    │
    ▼
Logical Delete
```

Posting state changes SHALL NOT affect document identity.

---

## 11.10 Versioning

### Purpose

Documents SHALL use optimistic concurrency control.

---

### Version Increment

Document version SHALL increase when:

- header fields change;
- tabular section data changes;
- posting state changes.

---

### Version Stability

Document version SHALL NOT change when:

- document is loaded;
- document is read;
- document is referenced by another object.

---

### Identity Independence

Version and identity represent independent concepts.

Changing the version MUST NOT affect document identity.

---

## 11.11 Transactions

### Purpose

All document modifications SHALL occur inside transactions.

---

### Transaction Scope

The following operations SHALL require transactional execution:

- document creation;
- document modification;
- tabular section modification;
- posting state changes;
- document deletion.

---

### Atomicity

Document updates SHALL be atomic.

Header and tabular section modifications MUST be committed together.

Partial document updates MUST NOT be observable.

---

### Register Consistency

When posting generates register movements, document persistence and movement persistence SHOULD participate in the same logical transaction.

The exact implementation depends on the Storage Provider.

---

## 11.12 Extensibility

The Document Storage Model SHALL support future extensions without architectural redesign.

Possible future extensions include:

- document attachments;
- document version history;
- distributed document storage;
- document partitioning;
- document snapshots.

Such extensions MUST preserve compatibility with the logical model defined by this specification.

---

# 12. Register Storage Model

## 12.1 Overview

Register Storage Model defines the logical persistence model for platform registers.

Registers store business facts and system state derived from business operations.

Registers provide the foundation for balances, totals, historical analysis and operational reporting.

The platform defines two register categories:

- Accumulation Registers
- Information Registers

Register behavior is defined by Metadata and Runtime.

Storage is responsible only for persistence.

---

## 12.2 Design Goals

The Register Storage Model is designed to satisfy the following goals.

### State Representation

Registers SHALL represent business state rather than business events.

Documents describe events.

Registers describe resulting state.

---

### Provider Independence

Register persistence SHALL remain independent of the selected Storage Provider.

Logical behavior MUST remain identical across all supported providers.

---

### Transactional Consistency

Register updates SHALL participate in transactions.

Register state MUST remain internally consistent.

---

### Historical Preservation

Registers SHALL preserve historical information.

Past register state MUST remain available for analysis and reporting.

---

### Performance

The model SHALL support efficient:

- balance calculation;
- aggregation;
- filtering;
- reporting.

---

## 12.3 Register Categories

The platform defines two register categories.

```
Register
│
├── Accumulation Register
│
└── Information Register
```

Additional register categories MAY be introduced in future platform versions.

---

# 12.4 Accumulation Register Model

## Purpose

Accumulation Registers store movements that affect balances.

Typical examples include:

- Inventory
- Cash
- Accounts Receivable
- Accounts Payable
- Production Resources

---

## Logical Structure

An Accumulation Register consists of:

```
Accumulation Register
│
├── Movements
│
└── Totals
```

Movements store business history.

Totals store aggregated state.

---

## Movement Records

Every movement SHALL contain:

| Field | Description |
|---------|-------------|
| id | Movement identity (ULID) |
| period | Business timestamp |
| document_id | Source document |
| movement_type | INCOME or EXPENSE |

Additional fields SHALL be defined by Metadata.

---

## Dimensions

Dimensions identify the balance being affected.

Examples include:

- Product
- Warehouse
- Customer
- Currency
- Project

Dimensions SHALL be defined by Metadata.

---

## Resources

Resources represent accumulated values.

Examples include:

- Quantity
- Amount
- Weight
- Volume

Resources SHALL use Platform Types.

Resource values SHALL remain non-directional.

Movement direction SHALL be represented exclusively through:

```
movement_type
```

---

## Movement Types

The platform defines two movement types.

```
INCOME
```

```
EXPENSE
```

Direction MUST NOT be encoded through negative resource values.

This guarantees consistent aggregation behavior.

---

## Historical Integrity

Movements SHALL remain immutable after successful posting.

Corrections SHALL be represented through additional movements rather than direct modification.

---

# 12.5 Totals Model

## Purpose

Totals provide accelerated access to accumulated balances.

Totals are derived from movements.

Totals SHALL NOT replace movements.

---

## Separation Principle

Movements and totals SHALL be stored independently.

```
Register
│
├── Movements
│
└── Totals
```

Movement history remains the authoritative source of truth.

Totals serve as an optimization mechanism.

---

## Rebuild Capability

Totals MUST be fully reconstructible from movement history.

Loss of totals MUST NOT result in loss of business data.

---

## Granularity

Totals MAY be maintained at different granularities.

Examples include:

- yearly;
- quarterly;
- monthly;
- daily.

The selected strategy SHALL remain transparent to Runtime.

---

## Adaptive Totals

The platform MAY automatically optimize totals granularity.

Possible progression:

```
Yearly
    ↓
Quarterly
    ↓
Monthly
    ↓
Daily
```

Optimization decisions MAY be based on:

- movement volume;
- query patterns;
- reporting requirements;
- storage characteristics.

Logical behavior MUST remain unchanged.

---

## Required Baseline

Every Accumulation Register SHALL support yearly totals.

Yearly totals represent the minimum guaranteed optimization level.

---

# 12.6 Information Register Model

## Purpose

Information Registers store business facts that do not represent accumulation.

Examples include:

- Exchange Rates
- Product Prices
- Tax Rates
- User Settings
- Configuration Values

---

## Logical Structure

Information Registers consist solely of records.

```
Information Register
│
└── Records
```

No balance calculation is required.

---

## Dimensions

Information Registers MAY define dimensions.

Examples include:

- Currency
- Product
- Customer
- Region

Dimensions are defined by Metadata.

---

## Attributes

Information Registers MAY define attributes.

Examples include:

- Rate
- Price
- Description
- Status

Attributes are defined by Metadata.

---

## Periodicity

Information Registers MAY be:

- periodic;
- non-periodic.

---

## Periodic Registers

Periodic registers SHALL contain:

```
period
```

The period defines record validity in time.

---

## Non-Periodic Registers

Non-periodic registers store only the latest state.

Historical tracking is optional.

---

# 12.7 References

Registers MAY reference:

- catalogs;
- documents;
- constants;
- other registers.

All references SHALL use the Platform Reference Model.

---

# 12.8 Lifecycle

Registers participate in the standard persistence lifecycle.

```
Create
    │
    ▼
Persist
    │
    ▼
Update
    │
    ▼
Logical Delete
```

Accumulation Register movements MAY impose additional immutability rules.

---

# 12.9 Versioning

Registers SHALL use optimistic concurrency control.

Versioning rules defined by this specification apply to:

- movement records;
- totals records;
- information register records.

Version changes SHALL occur only when persistent data changes.

---

# 12.10 Transactions

All register modifications SHALL occur inside transactions.

---

## Atomicity

Register updates SHALL be atomic.

Partial register updates MUST NOT be observable.

---

## Posting Consistency

When document posting generates register movements:

```
Document Update
        +
Register Update
```

SHOULD participate in the same logical transaction.

---

## Totals Consistency

Movement persistence and totals updates SHALL remain transactionally consistent.

Totals MUST NOT reflect uncommitted movements.

---

# 12.11 Extensibility

The Register Storage Model SHALL support future extensions without architectural redesign.

Possible future extensions include:

- distributed registers;
- adaptive partitioning;
- column-oriented storage;
- incremental aggregation;
- advanced analytical indexes.

Such extensions MUST preserve compatibility with the logical model defined by this specification.

---