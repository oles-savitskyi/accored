# ATTRIBUTE_MODEL

## Status

Planned

## Baseline

implementation-0.3

---

# 1. Purpose

The purpose of the Attribute Model is to define a universal mechanism for describing business data fields within the metadata system.

Attributes represent the smallest meaningful units of business information.

They are used to describe the structure of Catalogs, Documents, Registers, Reports and other metadata-driven objects.

The Attribute Model provides a common abstraction that allows all business object types to share a consistent data definition mechanism.

---

# 2. Design Principles

## Metadata-Driven

Attributes are defined in metadata and remain independent from runtime implementation.

## Platform-Wide Consistency

The same attribute model must be usable across all platform object types.

## Strong Typing

Every attribute has an explicitly defined data type.

Implicit type inference is not allowed.

## Immutability

Compiled attribute metadata is immutable.

## Extensibility

New attribute types may be introduced without breaking existing definitions.

---

# 3. Attribute Architecture

The Attribute Model consists of two layers:

```text
Attribute Definition
        ↓
Attribute Metadata
```

Definitions are authored by configuration developers.

Metadata is produced by the Compiler Layer.

Runtime components operate exclusively on metadata.

---

# 4. Attribute Identity

Every attribute must have a unique name within its owner object.

Example:

```text
Assortment
    ├── code
    ├── name
    └── unit
```

In this example:

```text
code
name
unit
```

are unique attribute identities inside the Assortment catalog.

The platform does not require global attribute uniqueness.

Identity is scoped to the owning metadata object.

---

# 5. Common Attribute Properties

Every attribute definition contains a common set of properties.

## Name

Logical attribute name.

Example:

```text
name
```

## Type

Attribute data type.

Example:

```text
String
```

## Nullable

Indicates whether the attribute may contain no value.

Example:

```text
True
False
```

## Default Value

Optional default value.

Example:

```text
"Unknown"
```

## Description

Human-readable attribute description.

Used for documentation and future UI generation.

---

# 6. Attribute Lifecycle

Attributes pass through the following lifecycle:

```text
Definition
        ↓
Compilation
        ↓
Metadata
        ↓
Registry
        ↓
Runtime Access
```

The Compiler Layer validates attribute definitions and produces immutable metadata objects.

---

# 7. Attribute Types

Implementation-0.3 introduces the first generation of attribute types.

## String

Text values.

Examples:

```text
name
code
description
```

---

## Integer

Whole numbers.

Examples:

```text
priority
quantity_days
```

---

## Decimal

Fractional numeric values.

Examples:

```text
weight
price
amount
```

The exact storage representation is defined by future platform layers.

---

## Boolean

Logical values.

Examples:

```text
is_active
is_folder
```

---

## Date

Calendar dates without time component.

Examples:

```text
birth_date
posting_date
```

---

## DateTime

Date and time values.

Examples:

```text
created_at
updated_at
```

---

## Reference

References to other metadata objects.

Examples:

```text
unit
currency
business_partner
```

Reference attributes store object identity rather than object content.

---

## Enum

Values selected from a predefined set.

Examples:

```text
status
movement_type
```

Enumeration definitions are introduced in future phases.

Implementation-0.3 defines only the attribute type category.

---

# 8. Reference Attributes

Reference attributes establish relationships between metadata objects.

Example:

```text
Assortment
    └── unit → MeasureUnits
```

Reference attributes must specify:

```text
Attribute Name
Target Object
```

The Compiler Layer validates reference declarations.

Runtime reference resolution is outside the scope of implementation-0.3.

---

# 9. Enumeration Attributes

Enumeration attributes represent a constrained set of allowed values.

Example:

```text
Draft
Approved
Posted
Cancelled
```

Enumeration definition and lifecycle are introduced in future phases.

The current phase defines only the metadata abstraction.

---

# 10. Nullability

Nullability determines whether an attribute may contain no value.

```text
nullable = true
```

means a value may be absent.

```text
nullable = false
```

means a value is required.

Nullability is part of attribute metadata.

Validation execution is not implemented during implementation-0.3.

---

# 11. Default Values

Attributes may define default values.

Examples:

```text
country = "Ukraine"

is_active = true
```

Default value semantics are stored in metadata.

Application of defaults is a future runtime concern.

### Default Value Constraint

An attribute default value is part of the attribute definition and must
eventually be compatible with the declared `AttributeType`.

The current implementation does not perform full default-value type
validation. Such validation belongs to the Definition Validation / Type
Validation stage and must be introduced before default values become
runtime-authoritative.
---

# 12. Attribute Ownership

Attributes always belong to a metadata object.

Examples:

```text
Catalog
    └── Attributes

Document
    └── Attributes

Register
    └── Attributes
```

Attributes cannot exist independently.

---

# 13. Attribute Metadata

After compilation every attribute is represented by immutable metadata.

Conceptually:

```text
Attribute Metadata
    ├── Name
    ├── Type
    ├── Nullable
    ├── Default Value
    └── Description
```

Runtime components access attributes through metadata objects.

Runtime components never access definitions directly.

---

# 14. Future Extensions

The Attribute Model is expected to evolve with additional capabilities.

Potential future extensions include:

```text
Money

Quantity

Calculated Attributes

Composite Attributes

Collections

Multi-Value Attributes

File References

JSON Attributes

Localization Support
```

These extensions must remain compatible with the core Attribute Model defined in this document.

---

# 15. Architectural Outcome

The Attribute Model establishes a universal metadata abstraction for business data fields.

After implementation-0.3 every metadata-driven platform object should be able to describe its structure through attributes.

This model becomes the foundation for:

* Catalog Metadata
* Document Metadata
* Register Metadata
* Report Metadata
* Workflow Metadata

and serves as one of the core building blocks of the AcCoreD metadata architecture.
