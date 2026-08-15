# VALIDATION_MODEL

## Status

Planned

## Baseline

implementation-0.3

---

# 1. Purpose

The purpose of the Validation Model is to define how structural constraints are represented within the Metadata Layer.

Validation rules describe requirements that business data must satisfy.

The Validation Model does not define how validation is executed.

Its responsibility is limited to describing validation constraints as metadata.

Validation execution is a future platform concern.

## Current Implementation Status

The current implementation establishes definition-level validation.

It validates:

* definition structure;
* attribute structure;
* duplicate attribute names;
* reference target requirements;
* semantic compatibility of default values.

Validation rules are not yet compiled into Metadata.

Therefore this document distinguishes:

1. Definition Validation — implemented;
2. Validation Metadata — planned;
3. Validation Execution — outside the current scope.
---

# 2. Architectural Position

The Validation Model is a component of the Metadata Layer.

```text
Definition Layer
        ↓
Compiler Layer
        ↓
Metadata Layer
        ├── Attributes
        ├── System Fields
        └── Validation Rules
        ↓
Runtime Layer
```

Validation rules become part of compiled metadata and are available to all future platform components.

---

# 3. Design Principles

## Validation Is Metadata

Validation rules are represented as metadata objects.

Validation behavior is not embedded in definitions.

---

## Runtime Independence

Validation metadata must exist independently of runtime implementation.

Validation rules may be inspected, documented and registered without creating runtime objects.

---

## Immutability

Compiled validation metadata is immutable.

Any rule modification requires recompilation.

---

## Extensibility

The validation framework must support future rule types without changing the architectural model.

---

## Platform Consistency

The same validation model must be applicable to:

* Catalogs
* Documents
* Registers
* Reports
* Workflows

---

# 4. Validation Architecture

Validation follows the standard AcCoreD compilation pipeline.

```text
Validation Definition
        ↓
Compiler
        ↓
Validation Metadata
        ↓
Registry
        ↓
Runtime Access
```

Runtime components consume validation metadata.

They do not consume validation definitions.

---

# 5. Validation Rule Structure

Conceptually every validation rule consists of:

```text
Validation Rule
    ├── Rule Type
    ├── Target
    ├── Parameters
    └── Metadata
```

Where:

* Rule Type defines the kind of validation.
* Target identifies the validated attribute.
* Parameters define rule-specific settings.
* Metadata contains descriptive information.

---

# 6. Validation Targets

Validation rules may be attached to:

```text
Attribute
```

Implementation-0.3 supports attribute-level validation only.

Future phases may introduce:

```text
Object-Level Rules

Cross-Attribute Rules

Cross-Object Rules
```

---

# 7. Required Rule

Purpose:

Ensure that a value must be provided.

Example:

```text
name
```

must contain a value.

Conceptually:

```text
Required(name)
```

The rule is represented as metadata only.

---

# 8. Unique Rule

Purpose:

Declare that values must be unique within a defined scope.

Example:

```text
code
```

must be unique.

Conceptually:

```text
Unique(code)
```

Uniqueness enforcement is outside the scope of implementation-0.3.

---

# 9. Minimum Length Rule

Purpose:

Define the minimum length of textual values.

Example:

```text
MinLength(code, 3)
```

The rule describes the constraint but does not enforce it.

---

# 10. Maximum Length Rule

Purpose:

Define the maximum length of textual values.

Example:

```text
MaxLength(code, 20)
```

The rule is represented as metadata.

---

# 11. Minimum Value Rule

Purpose:

Define the minimum allowed numeric value.

Example:

```text
MinValue(weight, 0)
```

---

# 12. Maximum Value Rule

Purpose:

Define the maximum allowed numeric value.

Example:

```text
MaxValue(discount, 100)
```

---

# 13. Reference Integrity Rule

Purpose:

Describe integrity requirements for reference attributes.

Example:

```text
unit → MeasureUnits
```

Conceptually:

```text
ReferenceIntegrity(unit)
```

Reference validation behavior is not implemented during implementation-0.3.

---

# 14. Validation Metadata

After compilation every validation rule becomes immutable metadata.

Conceptually:

```text
Validation Metadata
    ├── Rule Type
    ├── Target
    ├── Parameters
    └── Description
```

Runtime components operate exclusively on validation metadata.

---

# 15. Validation Composition

Multiple validation rules may be attached to the same attribute.

Example:

```text
code
    ├── Required
    ├── Unique
    └── MaxLength(20)
```

Validation metadata preserves the complete set of rules associated with the attribute.

---

# 16. Compiler Validation

The Compiler Layer is responsible for validating validation definitions.

Compiler responsibilities include:

* rule structure verification;
* target existence verification;
* parameter verification;
* metadata consistency verification.

Invalid validation definitions must prevent metadata generation.

---

# 17. Runtime Validation

Runtime validation is outside the scope of implementation-0.3.

Future platform components may consume validation metadata for:

* user input validation;
* document validation;
* API validation;
* import validation;
* business rule enforcement.

The Validation Model intentionally remains independent of any specific execution strategy.

---

# 18. Validation Registration

Validation metadata is stored as part of the owning metadata object.

Example:

```text
Catalog Metadata
    ├── Attributes
    └── Validation Rules
```

Validation metadata is not registered independently.

It belongs to the metadata object that owns it.

---

# 19. Validation Lifecycle

Validation metadata follows the standard metadata lifecycle.

```text
Validation Definition
        ↓
Compilation
        ↓
Validation Metadata
        ↓
Registration
        ↓
Runtime Access
```

No mutation is allowed after compilation.

---

# 20. Future Extensions

The Validation Model is expected to support additional rule types.

Potential future extensions include:

```text
Regular Expression Rules

Pattern Matching Rules

Cross-Field Rules

Conditional Rules

Domain Rules

Composite Rules

Custom Validation Rules
```

These extensions must remain compatible with the architectural principles defined in this document.

---

# 21. Architectural Outcome

The Validation Model establishes a platform-wide mechanism for representing structural constraints as metadata.

After implementation-0.3, validation requirements become first-class metadata elements that can be compiled, registered and accessed independently of runtime implementation.

This model provides the foundation for future validation engines while preserving the separation between metadata description and validation execution.
