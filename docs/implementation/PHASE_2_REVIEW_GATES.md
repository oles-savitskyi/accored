# REVIEW_GATES

## Status

Planned

## Baseline

implementation-0.3

---

# 1. Purpose

The purpose of the Review Gates is to define the architectural checks that must be passed during implementation-0.3.

Review Gates protect the architectural boundaries of the AcCoreD Platform and prevent implementation details from violating the Metadata-Driven Architecture.

A feature is not considered architecturally complete merely because its tests pass.

It must also satisfy the applicable Review Gates.

---

# 2. Review Philosophy

Implementation-0.3 introduces a richer Metadata Model.

This creates a risk that:

* runtime behavior begins to depend on definitions;
* compiler responsibilities leak into runtime;
* metadata becomes mutable;
* Standard Configuration knowledge enters Platform code;
* Registry becomes coupled to implementation details.

Review Gates exist specifically to detect and prevent these failures.

---

# 3. RG-1 — Domain Purity

## Objective

Ensure that architectural layers remain independent.

## Required Boundaries

```text id="wq4q8p"
Definition
    ↓
Compiler
    ↓
Metadata
    ↓
Registry
    ↓
Runtime
```

The following dependencies are prohibited:

```text id="0a6qwt"
Definition → Runtime

Metadata → Runtime

Runtime → Compiler

Runtime → Definition
```

## Verification

Review imports and package dependencies.

Confirm that runtime components operate on metadata rather than definitions.

## Pass Criteria

No prohibited dependency exists.

---

# 4. RG-2 — Metadata Immutability

## Objective

Ensure that compiled metadata cannot be modified after compilation.

## Required Property

```text id="k1q5pn"
Definition
    ↓
Compilation
    ↓
Immutable Metadata
```

Once metadata is finalized:

* attributes cannot be added;
* attributes cannot be removed;
* attribute types cannot change;
* validation rules cannot change;
* system fields cannot change;
* metadata identity cannot change.

## Verification

Attempt mutation through all exposed metadata APIs.

Review internal metadata structures for mutable escape paths.

## Pass Criteria

All mutation attempts fail through controlled mechanisms.

No mutable internal structure is exposed.

---

# 5. RG-3 — Compiler Determinism

## Objective

Ensure that compilation produces deterministic metadata.

## Required Property

```text id="u6w7q1"
Definition A
    ↓
Compiler
    ↓
Metadata A

Definition A
    ↓
Compiler
    ↓
Metadata A
```

Equivalent definitions must produce semantically equivalent metadata.

## Compiler Must Not Depend On

* current time;
* process state;
* environment variables;
* registry state;
* runtime state;
* registration order.

## Verification

Compile the same definition repeatedly.

Compare metadata identity and structural content.

## Pass Criteria

Repeated compilation produces deterministic results.

---

# 6. RG-4 — Registry Integrity

## Objective

Ensure that the Metadata Registry remains a reliable source of metadata identity and lookup.

## Required Properties

The Registry must:

* enforce metadata identity uniqueness;
* reject duplicate registration;
* return the correct metadata for a valid identity;
* reject invalid lookups predictably;
* remain independent from compiler implementation.

## Verification

Test:

```text id="a9r6nt"
Register

Duplicate Register

Lookup

Missing Lookup

Resolution
```

## Pass Criteria

Registry behavior is deterministic and consistent.

---

# 7. RG-5 — Runtime Isolation

## Objective

Ensure that Runtime remains independent of Definition and Compiler layers.

## Required Architecture

```text id="xg0dqt"
Compiler
    ↓
Metadata
    ↓
Registry
    ↓
Resolver
    ↓
Runtime
```

Runtime must receive metadata through the established resolution path.

Runtime must not:

* compile definitions;
* inspect definition objects;
* invoke compiler internals;
* modify metadata;
* contain Standard Configuration-specific structures.

## Verification

Review Runtime implementation and dependency graph.

Search for direct imports from Definition and Compiler packages.

## Pass Criteria

Runtime operates exclusively through the Metadata/Runtime contracts.

---

# 8. RG-6 — Standard Configuration Isolation

## Objective

Ensure that Standard Configuration remains a consumer of the Platform rather than part of Platform implementation.

## Required Boundary

```text id="j1f3ma"
Platform
    ↑
Standard Configuration
```

The Platform must provide generic mechanisms.

Standard Configuration provides:

* definitions;
* business object declarations;
* configuration-specific metadata.

## Prohibited

Platform code must not contain:

```text id="5p7qqe"
Assortment-specific logic

MeasureUnits-specific logic

Standard Configuration object names

Standard Configuration business rules
```

unless explicitly required by an architectural contract.

## Pass Criteria

VS-002 works without hard-coded Standard Configuration behavior in the Platform.

---

# 9. RG-7 — System Field Ownership

## Objective

Ensure that system fields remain platform-owned.

## Required Boundary

```text id="0kn4e2"
Platform
    ↓
System Fields

Configuration
    ↓
Business Attributes
```

Configuration definitions must not be able to:

* redefine system fields;
* remove system fields;
* change system field types;
* override system field semantics.

## Verification

Attempt conflicting definitions.

Review compiler injection logic.

## Pass Criteria

System field ownership remains exclusively with the Platform.

---

# 10. RG-8 — Metadata Completeness

## Objective

Ensure that compiled metadata contains all required structural components.

For a rich Catalog Metadata object:

```text id="jz1t3s"
CatalogMetadata
    ├── Identity
    ├── System Fields
    ├── Attributes
    ├── Validation Rules
    └── Version Information
```

## Verification

Inspect compiled metadata from VS-002.

## Pass Criteria

All mandatory components are present and internally consistent.

---

# 11. RG-9 — Attribute Integrity

## Objective

Ensure that attribute metadata faithfully represents the source definition.

The compiler must preserve:

* attribute identity;
* type;
* nullability;
* default value;
* description;
* reference information.

## Verification

Compare source definition with compiled metadata.

## Pass Criteria

No structural information is lost or silently changed during compilation.

---

# 12. RG-10 — Validation Metadata Integrity

## Objective

Ensure that validation definitions are correctly represented as metadata.

The compiler must verify:

* rule type;
* target attribute;
* rule parameters;
* rule consistency.

## Verification

Use valid and invalid validation definitions.

## Pass Criteria

Valid rules compile correctly.

Invalid rules prevent metadata generation.

Validation rules are not executed during compilation.

---

# 13. RG-11 — Reference Boundary

## Objective

Ensure that metadata references remain metadata-level relationships.

Example:

```text id="6gq6j3"
Assortment.unit
        ↓
MeasureUnits
```

Metadata must represent the target identity.

It must not contain instantiated runtime objects.

## Pass Criteria

References remain declarative metadata relationships.

---

# 14. RG-12 — Public API Boundary

## Objective

Ensure that public APIs expose stable contracts rather than implementation details.

Public APIs should expose:

* metadata identity;
* attributes;
* system fields;
* validation rules.

They should not expose:

* compiler internals;
* mutable collections;
* registry internals;
* definition objects.

## Pass Criteria

Public API consumers can inspect metadata without depending on internal implementation structures.

---

# 15. Review Gate Execution

Review Gates are evaluated at three levels.

## Development Review

Performed during implementation.

## Vertical Slice Review

Performed after VS-002.

## Phase Completion Review

Performed before tagging implementation-0.3.

All mandatory gates must pass before phase completion.

---

# 16. Gate Result

Each gate receives one of the following statuses:

```text id="f6m7rq"
PASS

FAIL

WAIVED
```

A `WAIVED` status requires an explicit architectural justification.

A failed mandatory gate prevents phase completion.

---

# 17. Phase Completion Requirement

Implementation-0.3 cannot be considered complete until:

```text id="3d8l1m"
RG-1  PASS
RG-2  PASS
RG-3  PASS
RG-4  PASS
RG-5  PASS
RG-6  PASS
RG-7  PASS
RG-8  PASS
RG-9  PASS
RG-10 PASS
RG-11 PASS
RG-12 PASS
```

All deviations must be documented before the phase is finalized.

---

# 18. Architectural Outcome

The Review Gates ensure that implementation-0.3 expands Metadata capabilities without weakening the architectural boundaries established by implementation-0.2.

The central requirement remains:

```text id="r3qv5k"
Definitions describe.

Compiler transforms.

Metadata represents.

Registry resolves.

Runtime executes.
```

No layer may assume responsibilities belonging to another layer.
