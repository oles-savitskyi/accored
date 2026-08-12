# Architectural Patterns

**Version:** 1.0  
**Status:** Living Document

---

# 1. Purpose

This document describes the recurring architectural patterns used throughout the AcCore platform.

Unlike subsystem-specific documents, these patterns represent general architectural principles that apply across multiple platform components.

The purpose of this document is to preserve architectural consistency as the platform evolves.

---

# 2. Model-Driven Architecture

Every major subsystem is defined by an explicit architectural model.

A model describes the structure of a subsystem independently from its implementation.

Typical lifecycle:

```
Definition
    │
    ▼
Model
    │
    ▼
Composition / Compilation
    │
    ▼
Published Model
    │
    ▼
Execution
```

The model is the primary architectural artifact.

Implementation follows the model rather than defining it.

---

# 3. Published Model Principle

Major subsystems publish immutable models that serve as architectural contracts.

Dependent subsystems never interact with internal implementation details.

Instead, they consume published models.

Examples:

| Subsystem | Published Model |
|------------|-----------------|
| Metadata | Published Semantic Metadata Graph |
| Runtime | Published Runtime Service Graph *(planned)* |
| Query Engine | Compiled Query Plan *(future)* |
| Expression Engine | Compiled Expression Plan *(future)* |

Published models are:

- immutable;
- validated;
- versioned;
- deterministic.

---

# 4. Compilation Pipeline

Whenever possible, information is transformed through explicit compilation stages.

Typical pipeline:

```
Definitions
    │
    ▼
Model
    │
    ▼
Analysis
    │
    ▼
Validation
    │
    ▼
Publication
```

Compilation separates source definitions from executable runtime structures.

---

# 5. Composition Before Execution

Runtime structures are composed before becoming operational.

Examples include:

- metadata compilation;
- runtime service composition;
- query compilation;
- expression compilation.

Execution never operates on incomplete structures.

---

# 6. Immutable Published State

Once published, architectural models become immutable.

Runtime components never modify published models.

Changes always produce new published models rather than modifying existing ones.

Benefits include:

- deterministic behavior;
- thread safety;
- simpler reasoning;
- predictable dependency management.

---

# 7. Explicit Context

Every operation executes within an explicitly defined context.

Context is propagated through the execution pipeline rather than accessed implicitly.

Examples include:

- Runtime Context;
- Security Context;
- Transaction Context;
- Localization Context;
- Execution Context.

Explicit context improves clarity, testability and scalability.

---

# 8. Ownership vs References

Structural relationships and semantic relationships are distinct concepts.

Ownership defines:

- hierarchy;
- lifecycle;
- containment.

References define:

- semantic relationships;
- dependencies;
- cross-links.

Ownership forms trees.

References form graphs.

The two concepts are independent.

---

# 9. Graph-Based Architecture

Complex subsystem relationships are represented as graphs rather than arbitrary object networks.

Examples include:

- Metadata Graph;
- Dependency Graph;
- Runtime Service Graph *(planned)*;
- Query Plan *(future)*.

Graphs provide:

- deterministic traversal;
- dependency analysis;
- optimization opportunities;
- visualization.

---

# 10. Service-Oriented Runtime

The Runtime is composed of cooperating services.

Each service:

- has a single responsibility;
- exposes explicit contracts;
- declares dependencies;
- participates in the Runtime lifecycle.

The Runtime coordinates services rather than implementing business functionality.

---

# 11. Separation of Models and Execution

Architectural models describe the system.

Runtime executes the system.

Models are never modified during execution.

Execution consumes published models.

---

# 12. Layered Transformation

Subsystems evolve through well-defined architectural layers.

Typical progression:

```
Definitions
    │
    ▼
Objects / Services
    │
    ▼
Relationships
    │
    ▼
Semantic Model
    │
    ▼
Published Model
    │
    ▼
Execution
```

Each layer adds semantic meaning without changing previous layers.

---

# 13. Single Responsibility of Architectural Components

Each architectural component should have one clearly defined responsibility.

Examples:

- Metadata Compiler compiles metadata.
- Validation verifies semantic correctness.
- Runtime manages service lifecycle.
- Storage persists data.
- Query Engine executes queries.

Responsibilities should not overlap.

---

# 14. Extensibility Through Composition

Platform evolution should occur primarily through composition rather than modification.

Examples include:

- new Runtime Services;
- new Metadata types;
- new Validation rules;
- new Query operators;
- new Expression functions.

Existing architectural contracts remain stable.

---

# 15. Architecture Before Implementation

Architectural decisions are documented before implementation.

Subsystem design follows documented architectural principles.

Implementation details must not redefine architecture.

---

# 16. Evolution

This document is intentionally incomplete.

New architectural patterns should be added only after they emerge naturally across multiple independent subsystems.

Patterns should describe recurring architectural solutions rather than implementation techniques.