# Metadata References

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Metadata References subsystem defines how metadata objects establish logical relationships within the AcCore platform.

While ownership organizes metadata into a hierarchical structure, references create semantic connections between otherwise independent objects.

Reference resolution transforms the metadata ownership tree into a complete semantic metadata graph.

---

# 2. Design Goals

The Metadata References subsystem is designed to provide:

- deterministic reference resolution;
- strong consistency;
- stable object identity;
- efficient lookup;
- immutable resolved references;
- dependency analysis;
- extensibility.

---

# 3. Architectural Principles

## Ownership and references are independent

Ownership defines structure.

References define semantics.

A reference never changes object ownership.

---

## References do not affect lifecycle

Creating or removing a reference does not create or destroy metadata objects.

Object lifetime is determined solely by ownership.

---

## Reference resolution is deterministic

The same metadata sources always produce identical resolved references.

---

## Runtime never resolves references

All references are resolved before metadata publication.

Runtime operates exclusively on resolved references.

---

## References are immutable

After publication every reference is fixed.

No runtime component may modify reference relationships.

---

# 4. Reference Model

The Metadata subsystem defines three relationship categories.

```
Ownership Tree
        │
        ▼
Reference Graph
        │
        ▼
Dependency Graph
```

Each level enriches the semantic model without modifying the previous one.

---

# 5. Ownership

Ownership represents structural containment.

Example:

```
Configuration
    └── Catalog
            └── Attribute
```

Ownership characteristics:

- exactly one owner;
- hierarchical;
- recursive lifecycle;
- deterministic traversal.

Ownership always forms a tree.

---

# 6. References

References connect metadata objects across the ownership hierarchy.

Example:

```
Invoice.Customer
        │
        ▼
Customers
```

Reference characteristics:

- no ownership;
- independent lifecycle;
- immutable after publication;
- validated during compilation.

References transform the ownership tree into a graph.

---

# 7. Dependencies

Dependencies describe semantic relationships derived from references.

Example:

```
Invoice

depends on

Customers

depends on

Country Enumeration
```

Dependencies are used for:

- validation;
- compilation order;
- extension analysis;
- impact analysis;
- optimization.

Dependencies may exist even when no direct reference is present.

---

# 8. Symbol Resolution

Reference resolution is performed in several stages.

```
Source Identifier
        │
        ▼
Symbol
        │
        ▼
Metadata Object
        │
        ▼
Resolved Reference
```

The Symbol Resolver is responsible for mapping identifiers to metadata objects.

Resolution is performed during metadata compilation.

---

# 9. Reference Resolution Pipeline

The reference resolution process follows a deterministic sequence.

```
Metadata Objects
        │
        ▼
Collect Symbols
        │
        ▼
Resolve References
        │
        ▼
Validate References
        │
        ▼
Build Dependency Graph
        │
        ▼
Publish Metadata Graph
```

Publication occurs only after all references have been successfully resolved.

---

# 10. Reference Validation

Every resolved reference must satisfy the following constraints:

- target object exists;
- target type is compatible;
- reference is unambiguous;
- visibility rules are satisfied;
- extension rules are satisfied.

Invalid references prevent metadata publication.

---

# 11. Cyclic References

Reference cycles are evaluated according to their semantic meaning.

Possible categories include:

- allowed cycles;
- prohibited cycles;
- deferred resolution;
- dependency cycles.

Validation rules determine whether a cycle is acceptable.

---

# 12. Runtime Representation

Published metadata contains only resolved references.

Runtime never performs:

- name lookup;
- symbol resolution;
- reference validation.

Runtime accesses metadata objects directly through immutable resolved references.

---

# 13. Performance Considerations

Reference resolution is optimized for:

- single-pass symbol lookup;
- immutable object references;
- efficient dependency traversal;
- cache-friendly graph navigation.

Reference lookup during runtime requires no additional resolution.

---

# 14. Future Evolution

The architecture allows future enhancements, including:

- incremental reference resolution;
- cross-configuration references;
- distributed metadata repositories;
- dependency visualization;
- semantic analysis tools;
- graph optimization.

These capabilities extend the existing architecture without changing the reference model.

---

# 15. Relationship to Other Subsystems

The Metadata References subsystem provides semantic relationships for:

- Metadata Validator;
- Runtime;
- Storage;
- Security;
- Query Engine;
- Expression Engine;
- Extension Framework;
- Development Tools.

Reference resolution is completed before any of these subsystems access metadata.

---

# Appendix A. Conceptual Model

```
                 Ownership

Configuration
      │
      ▼
Document
      │
      ▼
Attribute


                 References

Invoice.Customer ───────────────► Customers

Invoice.Currency ───────────────► Currency

Customer.Country ───────────────► Countries


                Dependencies

Invoice
   │
   ├────────────► Customers
   │
   ├────────────► Products
   │
   └────────────► Currency
```

Ownership defines the structure.

References define semantic relationships.

Dependencies define compilation and analysis relationships.

Together they form the complete semantic metadata model.