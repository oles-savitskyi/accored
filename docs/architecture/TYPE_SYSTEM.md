# TYPE_SYSTEM.md

## Purpose

Platform Type System defines the canonical data types used by:

* Metadata Architecture
* Runtime Architecture
* Object Architecture
* Storage Architecture
* Query Engine
* UI Layer
* Serialization Layer

The same type must have identical semantics throughout the platform.

---

# Type Categories

## Primitive Types

### String

Short text value.

Parameters:

* max_length
* regex (optional)

Examples:

```text
Product
ABC123
```

---

### Text

Long text value.

Examples:

```text
Description
Comment
Notes
```

---

### Boolean

Logical value.

Allowed values:

```text
true
false
```

---

### Integer

Signed integer value.

Examples:

```text
1
100
-50
```

---

### Decimal

Fixed-point decimal value.

Used for:

* calculations
* accounting values
* quantities requiring exact precision

Examples:

```text
12.5
100.25
0.001
```

---

### Date

Calendar date.

Example:

```text
2026-08-01
```

---

### DateTime

Date and time.

Example:

```text
2026-08-01 14:30:00
```

---

### Binary

Binary data.

Examples:

* files
* images
* attachments

---

# Business Types

## Money

Represents monetary values.

Money is not merely a Decimal value.

Money behavior is determined by Currency metadata.

Currency defines:

* currency code
* symbol
* decimal precision
* smallest monetary unit
* rounding rules

Examples:

```text
USD -> precision 2
EUR -> precision 2
JPY -> precision 0
```

Money calculations must follow currency-specific rules.

---

## Quantity

Represents measurable quantities.

Examples:

```text
10 pcs
12.500 kg
1.250 m
```

Quantity supports configurable precision.

Unit of measure is defined separately through metadata references.

---

# Reference Types

## Reference<T>

Typed reference to another metadata object.

Examples:

```text
Reference<Customer>
Reference<Product>
Reference<Warehouse>
```

Storage representation:

```text
ULID
```

Reference type is determined by Metadata.

---

## Enum<T>

Reference to enumeration value.

Examples:

```text
PaymentType
DocumentStatus
```

---

# Technical Types

## ULID

Platform-wide object identifier.

Characteristics:

* globally unique
* time sortable
* storage independent
* suitable for distributed systems

Used as the primary object identity type.

---

## JSON

Structured technical data.

Used for:

* settings
* UI layouts
* cached metadata
* service data

Not intended for core business data.

---

# Type Parameters

Types may define additional parameters.

Examples:

```text
String(max_length=255)

Decimal(precision=18, scale=4)

Quantity(precision=18, scale=6)
```

---

# Design Principles

## Type Consistency

A type must have identical behavior across:

* Metadata
* Runtime
* Storage
* Queries
* UI

---

## Storage Independence

Type definitions must not depend on a specific database engine.

---

## Metadata Driven

All type definitions originate from Metadata.

Storage and Runtime implementations are generated from Metadata definitions.

---

## Extensibility

New types may be added without modifying existing type semantics.

---

# Runtime Object Identity

Platform Types define metadata field/value types. They do not define Object Identity. Phase 4 represents Object Identity with the immutable ULID-backed `foundation.Identifier`, distinct from Metadata Identity.

## Runtime Object Type vs Object Instance

The Type System distinguishes a resolved runtime object type from an individual
runtime object instance.

`CatalogRuntime` is a Runtime Object Type.

It represents the executable runtime semantics of a metadata-defined Catalog
type within a specific `RuntimeConfigurationContext`.

It does not represent an individual business object.

An `ObjectInstance` is an individual runtime object created from a resolved
Runtime Object Type.

The relationship is:

    Catalog Metadata
          ↓
    CatalogRuntime
    (Runtime Object Type)
          ↓
    ObjectInstance
    (individual object)

Therefore:

    CatalogRuntime ≠ ObjectInstance

One resolved Runtime Object Type may be used to create multiple independent
Object Instances:

    CatalogRuntime
       ├── ObjectInstance A
       ├── ObjectInstance B
       └── ObjectInstance C

`RuntimeResolver` is responsible for resolving `CatalogRuntime` from metadata
and runtime configuration context.

The Object Creation Boundary is responsible for creating `ObjectInstance`
objects from an already resolved Runtime Object Type.

`CatalogRuntime` MUST NOT own Object Instance identity, object lifecycle, or
individual object state.

`ObjectInstance` MUST NOT independently resolve metadata or discover runtime
configuration.

This distinction is fundamental to the Runtime / Object boundary:

    Runtime Type Resolution
            ↓
    Runtime Object Type
            ↓
    Object Instance Creation