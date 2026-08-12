# Runtime Context

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

The Runtime Context defines the complete execution environment for every operation performed within the AcCore Runtime.

A Runtime Context encapsulates all information required to execute an operation consistently, securely and deterministically.

Every observable Runtime operation executes within exactly one Runtime Context.

---

# 2. Design Goals

The Runtime Context is designed to provide:

- explicit execution environments;
- deterministic behavior;
- context isolation;
- immutable execution state;
- implementation independence;
- extensibility;
- support for multiple deployment models.

---

# 3. Architectural Principles

## Every operation has a Runtime Context

No Runtime operation executes outside a Runtime Context.

The Runtime Context accompanies every operation throughout its execution.

---

## Runtime Context is immutable

A Runtime Context represents a published execution environment.

After creation it is never modified.

Changes produce a new Runtime Context rather than modifying an existing one.

---

## Runtime Context is explicit

Platform services receive the Runtime Context explicitly.

Services do not rely on hidden global state.

---

## Runtime Context is composable

A Runtime Context is composed from multiple independent context components.

Each component represents a single architectural concern.

---

## Runtime Context is hierarchical

A Runtime Context may derive a child context from an existing parent context.

Derived contexts inherit execution state unless explicitly overridden.

---

# 4. Runtime Context Model

Conceptually:

```
Runtime Context

├── Metadata Context
├── Security Context
├── Session Context
├── Transaction Context
├── Localization Context
├── Organization Context
├── Execution Context
├── Environment Context
└── Service Context
```

Each component contributes information required for execution.

---

# 5. Context Components

Typical Runtime Context components include:

### Metadata Context

Provides access to the Published Semantic Metadata Graph and its version.

---

### Security Context

Defines authentication and authorization information.

---

### Session Context

Represents the current user session when applicable.

Background execution environments may omit this component.

---

### Transaction Context

Defines the active transaction.

Operations without transactional behavior may not include this component.

---

### Localization Context

Defines language, locale, formatting and time zone.

---

### Organization Context

Defines the active business organization or tenant.

---

### Execution Context

Contains execution-specific information such as:

- execution mode;
- execution parameters;
- execution identifier;
- diagnostic information.

---

### Environment Context

Represents Runtime-wide environment information.

Examples include:

- deployment profile;
- platform configuration;
- Runtime version.

---

### Service Context

Provides Runtime Services with infrastructure-specific execution information.

---

# 6. Context Composition

A Runtime Context is created through composition.

Conceptually:

```
Context Components

        │

        ▼

Runtime Context Builder

        │

        ▼

Published Runtime Context
```

Only published Runtime Contexts participate in execution.

---

# 7. Context Derivation

New Runtime Contexts are derived from existing contexts.

Conceptually:

```
Runtime Context A

        │

        ▼

Derivation

        │

        ▼

Runtime Context B
```

Derived contexts inherit the parent execution environment while introducing controlled modifications.

Examples include:

- nested transactions;
- temporary security elevation;
- localization changes;
- background execution;
- service-specific execution.

---

# 8. Context Lifetime

A Runtime Context exists only for the duration of its associated execution scope.

Possible lifetimes include:

- Runtime;
- Session;
- Request;
- Transaction;
- Background Task;
- Command Execution.

Context lifetime is determined during composition.

---

# 9. Context Propagation

The Runtime propagates the Runtime Context through Runtime Services.

Conceptually:

```
Runtime Context

        │

        ▼

Runtime Service

        │

        ▼

Domain Object

        │

        ▼

Result
```

Context propagation remains explicit throughout execution.

---

# 10. Context Isolation

Independent Runtime Contexts are isolated from one another.

Changes made within one Runtime Context do not affect other Runtime Contexts.

Isolation enables:

- concurrent execution;
- background processing;
- independent transactions;
- deterministic behavior.

---

# 11. Thread Safety

Immutable Runtime Contexts may safely be shared between execution threads.

Derived contexts remain independent from their parents.

Thread safety is achieved through immutability rather than synchronization.

---

# 12. Extensibility

Future Runtime implementations may introduce additional context components.

Examples include:

- Workflow Context;
- Cluster Context;
- Replication Context;
- Debug Context;
- Monitoring Context.

Existing Runtime Services should continue operating without modification.

---

# 13. Relationship to Other Subsystems

The Runtime Context provides execution information to all Runtime Services.

Examples include:

- Metadata Service;
- Storage Service;
- Query Service;
- Expression Service;
- Security Service;
- Transaction Service;
- UI Service.

Services consume the Runtime Context but do not own it.

---

# Appendix A. Conceptual Architecture

```
                 Runtime

                    │

                    ▼

          Published Runtime Context

                    │

        ┌───────────┼───────────┐

        ▼           ▼           ▼

   Security     Transaction   Metadata

        │           │           │

        └───────────┼───────────┘

                    ▼

            Runtime Services

                    │

                    ▼

             Domain Objects
```

The Runtime Context defines the execution environment.

Runtime Services consume the Runtime Context.

Domain Objects execute within the environment established by the Runtime Context.

---

# Appendix B. Context Lifecycle

```
Context Components

        │

        ▼

Composition

        │

        ▼

Published Runtime Context

        │

        ▼

Execution

        │

        ▼

Disposal
```

A Runtime Context is composed before execution, remains immutable during execution and is disposed after its execution scope completes.