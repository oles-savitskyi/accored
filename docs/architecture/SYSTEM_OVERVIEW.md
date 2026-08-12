# System Overview

**Version:** 1.0  
**Status:** Draft

---

# 1. Purpose

This document provides a high-level architectural overview of the AcCore platform as an integrated system.

Unlike subsystem-specific documents, the System Overview focuses on how the major architectural subsystems cooperate to provide a coherent execution environment.

The purpose of this document is to present the overall architectural picture of AcCore rather than the internal details of individual components.

---

# 2. Architectural Vision

AcCore is a model-driven enterprise application platform.

Every major subsystem is defined by explicit architectural models.

Execution is based on published architectural artifacts rather than mutable source definitions.

Subsystems cooperate through well-defined architectural contracts while remaining independently evolvable.

---

# 3. Major Architectural Subsystems

The platform consists of several major architectural subsystems.

Current subsystems include:

- Metadata
- Runtime

Planned subsystems include:

- Storage
- Object Model
- Query Engine
- Expression Engine
- User Interface
- Transactions
- Security
- Events
- Reporting
- Integration

Each subsystem has a clearly defined architectural responsibility.

---

# 4. Architectural Layers

Conceptually, the platform is organized into architectural layers.

```
Business Definitions

        │

        ▼

Architectural Models

        │

        ▼

Published Architectural Artifacts

        │

        ▼

Execution Environment

        │

        ▼

Business Execution
```

Each layer builds upon the previous one without violating architectural boundaries.

---

# 5. Metadata

Metadata describes the business structure of the application.

Metadata defines:

- business object types;
- relationships;
- behavior definitions;
- configuration structure.

Metadata is transformed into the Published Semantic Metadata Graph.

---

# 6. Runtime

The Runtime provides the execution environment.

The Runtime is responsible for:

- composing Runtime Services;
- managing Runtime Contexts;
- coordinating lifecycle;
- exposing Runtime Contracts.

The Runtime publishes the Runtime Service Graph before execution begins.

---

# 7. Published Architectural Artifacts

Published artifacts represent the architectural contracts between subsystems.

Examples include:

- Published Semantic Metadata Graph;
- Published Runtime Service Graph;
- Published Runtime Context;
- Compiled Query Plan (future);
- Compiled Expression Plan (future);
- Published Storage Model (future);
- Published UI Model (future).

Published artifacts are immutable.

Execution consumes published artifacts rather than mutable subsystem state.

---

# 8. System Pipelines

Architectural information flows through explicit system pipelines.

Typical progression:

```
Definitions

↓

Models

↓

Composition

↓

Validation

↓

Publication

↓

Execution
```

Each subsystem participates in one or more architectural pipelines.

---

# 9. Runtime Execution

Runtime execution consumes published architectural artifacts.

Conceptually:

```
Published Metadata Graph

+

Published Runtime Service Graph

+

Published Runtime Context

↓

Platform Services

↓

Business Execution

↓

Results
```

The Runtime never executes directly on source definitions.

---

# 10. Architectural Contracts

Subsystem interaction occurs through published architectural contracts.

Subsystems do not access each other's internal implementation.

Architectural contracts provide:

- compatibility;
- isolation;
- replaceability;
- extensibility.

---

# 11. Extensibility

The architecture supports gradual platform evolution.

New subsystems may be introduced by defining:

- architectural models;
- published artifacts;
- architectural contracts;
- execution pipelines.

Existing subsystem contracts should remain stable.

---

# 12. Architectural Consistency

All major subsystems follow common architectural principles.

These include:

- Model-Driven Architecture;
- Published Model Principle;
- Composition Before Execution;
- Immutable Published State;
- Explicit Context;
- Contract-Based Interaction.

Architectural consistency enables independent subsystem evolution.

---

# 13. Relationship to Other Documents

This document serves as the architectural entry point for the platform.

Detailed subsystem descriptions are provided in dedicated documents.

Examples include:

- Architecture Overview;
- Architectural Patterns;
- System Pipelines;
- Metadata Architecture;
- Runtime Architecture.

---

# Appendix A. High-Level Architecture

```
                 Business Definitions

                          │

                          ▼

                    Metadata Pipeline

                          │

                          ▼

         Published Semantic Metadata Graph

                          │

                          ▼

                    Runtime Pipeline

                          │

                          ▼

         Published Runtime Service Graph

                          │

                          ▼

              Published Runtime Context

                          │

                          ▼

                  Platform Services

                          │

                          ▼

                 Business Execution

                          │

                          ▼

                     Business Results
```

The platform transforms business definitions into executable business behavior through a sequence of architectural models and published artifacts.

---

# Appendix B. Architectural View

```
                Architecture

                       │

        ┌──────────────┼──────────────┐

        ▼              ▼              ▼

   Metadata        Runtime        Future Systems

        │              │

        └──────────────┼──────────────┐

                       ▼

          Published Architectural Artifacts

                       │

                       ▼

              Platform Execution

                       │

                       ▼

                Business Applications
```

Every subsystem contributes architectural artifacts to the platform.

Execution is based on the cooperation of these published artifacts rather than direct subsystem integration.