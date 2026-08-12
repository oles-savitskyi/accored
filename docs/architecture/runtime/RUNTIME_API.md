# Runtime API

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Runtime API defines the public architectural contract between the AcCore Runtime Environment and its consumers.

The Runtime API provides controlled access to Runtime capabilities while hiding the internal implementation of the Runtime Environment.

The Runtime API is independent of programming languages, frameworks and implementation technologies.

---

# 2. Design Goals

The Runtime API is designed to provide:

- stable architectural contracts;
- explicit Runtime interaction;
- deterministic behavior;
- implementation independence;
- compatibility across Runtime versions;
- extensibility.

---

# 3. Architectural Principles

## API is contract-based

The Runtime API exposes architectural Contracts rather than implementation details.

Consumers depend on Contracts, not on Runtime internals.

---

## API hides implementation

Internal Runtime organization remains private.

Changes to Runtime implementation must not affect the published Runtime API.

---

## API is explicit

Every Runtime interaction is performed through explicitly defined Contracts.

Hidden entry points are prohibited.

---

## API is deterministic

Identical inputs within the same Runtime Context produce deterministic behavior.

---

## API is Runtime Context-aware

Every Runtime operation executes within a Runtime Context.

The Runtime API never operates outside an explicit Runtime Context.

---

## API is implementation-independent

The Runtime API describes architectural behavior.

Programming language constructs belong to SDK implementations.

---

# 4. Runtime API Model

Conceptually:

```
Application

        │

        ▼

   Runtime API

        │

        ▼

Runtime Contracts

        │

        ▼

Runtime Services

        │

        ▼

Platform Infrastructure
```

The Runtime API represents the public architectural surface of the Runtime.

---

# 5. Runtime Contracts

The Runtime API is composed of Runtime Contracts.

Typical Runtime Contracts include:

- Runtime lifecycle;
- service discovery;
- context management;
- execution;
- diagnostics;
- event publication.

The exact implementation is language-specific.

---

# 6. Service Discovery

Applications access Runtime functionality through Runtime Contracts.

Service discovery is performed through the Runtime rather than by creating service instances directly.

Consumers never depend on implementation classes.

---

# 7. Runtime Context Access

Runtime operations receive an explicit Runtime Context.

The Runtime Context defines the execution environment for every operation.

The Runtime API propagates the Runtime Context without exposing Runtime internals.

---

# 8. Service Invocation

Runtime Services are invoked through published Service Contracts.

The Runtime API does not expose service implementations.

Invocation mechanisms may vary between SDK implementations.

---

# 9. Compatibility

The Runtime API is designed for long-term stability.

Compatible Runtime versions preserve existing Runtime Contracts.

Behavioral changes require explicit contract evolution.

---

# 10. Versioning

Runtime Contracts are versioned independently from their implementations.

Applications depend on contract compatibility rather than implementation versions.

---

# 11. Extensibility

New Runtime capabilities are introduced by publishing additional Runtime Contracts.

Existing Runtime Contracts remain unchanged whenever possible.

Platform evolution should preserve backward compatibility.

---

# 12. Relationship to SDKs

The Runtime API is an architectural specification.

SDKs are technology-specific implementations of the Runtime API.

Examples include:

- Python SDK;
- Java SDK (future);
- Rust SDK (future);
- JavaScript SDK (future).

Multiple SDKs may implement the same Runtime API.

---

# 13. Relationship to Other Subsystems

The Runtime API provides access to platform capabilities including:

- Metadata;
- Storage;
- Object Management;
- Query Processing;
- Expression Evaluation;
- Transactions;
- Security;
- Sessions;
- Events;
- User Interface.

Subsystem interaction occurs through published Runtime Contracts.

---

# Appendix A. Conceptual Architecture

```
                 Application

                       │

                       ▼

                 Runtime API

                       │

                       ▼

              Runtime Contracts

                       │

                       ▼

          Published Runtime Service Graph

                       │

                       ▼

              Runtime Service Registry

                       │

                       ▼

               Runtime Services

                       │

                       ▼

              Platform Infrastructure
```

The Runtime API defines the public architectural contract of the Runtime.

SDK implementations provide language-specific access to the Runtime API while preserving architectural compatibility.

---

# Appendix B. Runtime API and SDK

```
Architecture

      │

      ▼

 Runtime API

      │

      ▼

 Language SDK

      │

      ▼

 Application
```

The Runtime API is architecture.

The SDK is implementation.

Multiple SDKs may implement the same Runtime API without affecting the architectural model.