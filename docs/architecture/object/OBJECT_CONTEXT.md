# Object Context

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Object Context defines the execution environment associated with a Runtime Object within the AcCore platform.

It provides Runtime Objects with controlled access to Runtime services, execution information and environmental parameters while preserving the separation between business logic and infrastructure.

Object Context is created and managed by the Runtime.

---

# 2. Design Goals

The Object Context is designed to provide:

- controlled access to Runtime infrastructure;
- separation between business logic and execution environment;
- implementation independence;
- deterministic object execution;
- compatibility with Runtime Services;
- extensibility for future execution environments.

---

# 3. Architectural Principles

## Runtime owns Object Context

Object Context is created and managed exclusively by the Runtime.

Domain Objects do not create or manage Object Contexts.

---

## Object Context is local

Each Runtime Object executes within its own Object Context.

Object Context represents the execution environment of a single Runtime Object.

---

## Runtime Context creates Object Contexts

Object Contexts are derived from the current Runtime Context.

The Runtime determines which contextual information becomes available to each Runtime Object.

---

## Context exposes contracts

Object Context provides access through architectural Service Contracts.

Runtime implementation details remain encapsulated.

---

## Business logic remains independent

Business behavior depends only on architectural contracts exposed through the Object Context.

Business logic does not depend on Runtime implementation.

---

# 4. Architectural Model

Conceptually:

```
Runtime Context

        │

creates

        ▼

Object Context

        │

assigned to

        ▼

Runtime Object
```

Object Context bridges Runtime infrastructure and business execution.

---

# 5. Object Context Responsibilities

The Object Context is responsible for:

- exposing Runtime Services;
- providing execution parameters;
- exposing transaction information;
- exposing security information;
- providing localization settings;
- maintaining execution consistency.

Object Context does not execute business behavior.

---

# 6. Context Components

An Object Context may conceptually include:

- Runtime Service access;
- Transaction information;
- Security information;
- Localization settings;
- Execution parameters;
- Diagnostic information.

The concrete implementation remains architecture-independent.

---

# 7. Relationship to Runtime Context

Runtime Context defines the global execution environment.

Object Context represents the Runtime Environment as seen by a single Runtime Object.

Multiple Object Contexts may originate from the same Runtime Context.

---

# 8. Relationship to Runtime Services

Runtime Services are consumed through the Object Context.

Runtime Objects access services using published Service Contracts.

Service discovery remains independent of business behavior.

---

# 9. Relationship to Runtime Objects

Every Runtime Object executes within exactly one Object Context.

The Runtime associates Object Contexts with Runtime Objects during object creation.

---

# 10. Relationship to Transactions

Transaction information is exposed through the Object Context.

Transaction management remains the responsibility of the Transactions subsystem.

---

# 11. Relationship to Security

Security information is provided through the Object Context.

Authorization decisions remain the responsibility of the Security subsystem.

---

# 12. Architectural Boundaries

The Object Context separates:

- business behavior;
- Runtime infrastructure;
- transaction management;
- security;
- localization;
- diagnostics.

Each concern belongs to its dedicated subsystem.

---

# 13. Extensibility

Future Runtime implementations may introduce additional contextual services without changing the architectural contract of the Object Context.

The architectural model remains stable.

---

# 14. Relationship to Other Subsystems

```
Runtime Context

      │

      ▼

Object Context

      │

 ┌────┼──────────┬──────────┐

 ▼    ▼          ▼          ▼

Runtime Services Transactions Security Localization

      │

      ▼

Runtime Object
```

Object Context provides a unified architectural interface between Runtime infrastructure and Domain Objects.

---

# Appendix A. Context Creation

```
Runtime Context

        │

        ▼

Object Context

        │

        ▼

Runtime Object

        │

        ▼

Business Behavior
```

The Runtime creates and associates Object Contexts before business execution begins.

---

# Appendix B. Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Runtime Context | Global execution environment |
| Object Context | Local execution environment |
| Runtime Services | Infrastructure capabilities |
| Runtime Object | Business execution |
| Domain Object | Business model |

Object Context provides the architectural boundary between Runtime infrastructure and business behavior.