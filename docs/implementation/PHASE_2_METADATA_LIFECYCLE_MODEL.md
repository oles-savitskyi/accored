# Metadata Lifecycle Model

**Status:** Proposed
**Version:** 1.0
**Phase:** Phase 2 — Metadata → Runtime
**Scope:** Metadata Definition Lifecycle, Configuration Lifecycle, Runtime Availability

---

## 1. Purpose

This document defines the lifecycle model for metadata definitions and metadata configurations in AcCore.

The lifecycle model establishes:

* metadata definition states;
* configuration states;
* valid state transitions;
* lifecycle ownership;
* activation semantics;
* candidate configuration semantics;
* runtime visibility rules;
* failure semantics;
* version and identity rules;
* architectural invariants.

The model is designed to provide a strict boundary between:

* metadata definition and runtime representation;
* configuration loading and configuration activation;
* candidate configuration and active configuration;
* lifecycle management and runtime metadata consumption.

---

## 2. Scope

This model covers:

1. Metadata Definition Lifecycle.
2. Metadata Configuration Lifecycle.
3. Configuration activation.
4. Configuration replacement.
5. Runtime metadata availability.
6. Lifecycle-related validation and failure semantics.

This model does not define:

* distributed metadata coordination;
* deployment pipelines;
* schema migration;
* configuration migration;
* multi-tenant lifecycle;
* remote configuration repositories;
* cryptographic signing;
* persistent lifecycle event sourcing;
* rollback implementation;
* hot reload implementation.

These concerns may be introduced by later architectural layers.

---

## 3. Architectural Principle

The fundamental lifecycle principle is:

> Metadata Loading is not Metadata Activation.

Loading prepares a candidate configuration.

Activation publishes a validated candidate configuration as the authoritative runtime configuration.

The Runtime must never consume partially loaded or unvalidated metadata.

---

# 4. Lifecycle Domains

The lifecycle model consists of three related but distinct domains.

## 4.1 Metadata Definition Lifecycle

The definition lifecycle describes the lifecycle of an individual metadata definition.

```text
DEFINED
   │
   ▼
REGISTERED
   │
   ▼
VALIDATED
   │
   ▼
COMPILED
```

## 4.2 Configuration Lifecycle

The configuration lifecycle describes a coherent set of metadata definitions and their resolved relationships.

```text
DISCOVERED
   │
   ▼
LOADED
   │
   ▼
VALIDATED
   │
   ▼
READY
   │
   ▼
ACTIVE
   │
   ▼
INACTIVE
```

## 4.3 Runtime Availability

Runtime availability is not an independent compilation or loading state.

A metadata configuration becomes runtime-authoritative only when it reaches:

```text
ACTIVE
```

Therefore:

> Runtime metadata availability is a consequence of configuration activation, not configuration loading.

---

# 5. Metadata Definition Lifecycle

## 5.1 DEFINED

A metadata definition exists as a declarative metadata artifact.

At this stage:

* the definition may exist outside the Metadata Registry;
* no runtime availability is implied;
* no validity guarantee is implied.

## 5.2 REGISTERED

The definition has been accepted by the Metadata Registry and assigned or recognized by its metadata identity.

Guarantee:

> The platform can identify and retrieve the definition through the metadata registry.

Registration does not imply successful validation.

## 5.3 VALIDATED

The definition has passed metadata-level validation.

Validation may include:

* structural validation;
* required field validation;
* metadata type validation;
* identifier validation;
* attribute validation;
* local semantic validation.

Guarantee:

> The definition satisfies the metadata model and may be passed to compilation.

## 5.4 COMPILED

The definition has been transformed into its compiled/runtime-oriented representation.

Guarantee:

> Runtime-oriented metadata can be produced without reinterpreting the original declarative definition.

Compiled metadata is immutable.

A modification of a definition produces a new metadata version and therefore a new compiled representation.

---

# 6. Configuration Lifecycle

A configuration is a coherent metadata context composed of definitions and their resolved relationships.

## 6.1 DISCOVERED

The configuration source has been identified and its configuration content is available for loading.

Discovery does not imply that the configuration is valid.

## 6.2 LOADED

The configuration content has been read and materialized into an internal candidate representation.

At this stage:

* definitions may be individually available;
* cross-definition validity is not yet guaranteed;
* runtime availability is not implied.

## 6.3 VALIDATED

The complete candidate configuration has passed configuration-level validation.

Configuration validation may include:

* duplicate identity detection;
* reference resolution;
* dependency validation;
* compatibility validation;
* definition relationship validation;
* configuration-level invariants;
* standard configuration consistency.

Definition validation and configuration validation are separate gates.

A configuration can consist entirely of individually valid definitions and still be invalid as a configuration.

## 6.4 READY

The configuration has passed all preparation gates required for activation.

A READY configuration must have:

* valid definitions;
* resolved metadata dependencies;
* valid compiled representations;
* valid configuration relationships;
* a complete runtime metadata view;
* no known activation-blocking errors.

READY means:

> The configuration is eligible for atomic activation.

READY does not yet mean runtime-authoritative.

## 6.5 ACTIVE

The configuration has been atomically published as the authoritative runtime metadata configuration.

Guarantee:

> Runtime Metadata API resolves metadata only from the ACTIVE configuration.

At most one configuration is authoritative within a given runtime configuration scope.

## 6.6 INACTIVE

A previously active configuration has been replaced by another configuration.

An inactive configuration is retained only according to the applicable configuration retention policy.

INACTIVE metadata is not available to normal Runtime metadata resolution.

---

# 7. Candidate Configuration

A candidate configuration is a configuration being prepared for activation.

Typical lifecycle:

```text
DISCOVERED
    │
    ▼
LOADED
    │
    ▼
VALIDATED
    │
    ▼
READY
    │
    │ atomic activation
    ▼
ACTIVE
```

A candidate configuration must not alter the currently active configuration during loading or validation.

This provides isolation between:

```text
Active Configuration
```

and:

```text
Candidate Configuration
```

---

# 8. Atomic Activation

Activation is the publication boundary between candidate metadata and runtime metadata.

The required sequence is:

```text
Load
  ↓
Validate
  ↓
Resolve
  ↓
Compile / prepare
  ↓
Build candidate
  ↓
READY
  ↓
Atomic activation
  ↓
ACTIVE
```

The Runtime must not observe intermediate states.

The platform must not activate individual definitions independently when they belong to the same logical configuration activation.

Therefore:

> Configuration activation is atomic at the configuration boundary.

---

# 9. Configuration Replacement

Configuration replacement follows:

```text
ACTIVE v1
     │
     │ prepare
     ▼
READY v2
     │
     │ atomic activation
     ▼
ACTIVE v2
     │
     ▼
INACTIVE v1
```

The previous active configuration must remain authoritative until the replacement configuration has successfully reached the activation boundary.

An unsuccessful candidate must never cause the active configuration to become unavailable.

---

# 10. Failure Semantics

Lifecycle failures before activation are candidate failures.

Examples:

```text
Definition validation failure
Compilation failure
Missing dependency
Invalid reference
Duplicate metadata identity
Configuration invariant violation
```

The expected behavior is:

```text
Candidate → failure → discarded
```

rather than:

```text
Active → broken
```

The currently active configuration remains unchanged.

Failure states such as `INVALID` or `COMPILATION_FAILED` are not required as persistent lifecycle states in v1.0.

Failures are results of attempted transitions.

---

# 11. State Transition Rules

## 11.1 Definition transitions

| Current State | Operation | Result     |
| ------------- | --------- | ---------- |
| DEFINED       | register  | REGISTERED |
| REGISTERED    | validate  | VALIDATED  |
| VALIDATED     | compile   | COMPILED   |

Any failed transition leaves the current valid state unchanged.

## 11.2 Configuration transitions

| Current State | Operation | Result    |
| ------------- | --------- | --------- |
| DISCOVERED    | load      | LOADED    |
| LOADED        | validate  | VALIDATED |
| VALIDATED     | prepare   | READY     |
| READY         | activate  | ACTIVE    |
| ACTIVE        | replace   | INACTIVE  |

A failed candidate transition does not modify the currently ACTIVE configuration.

---

# 12. Identity and Version

Metadata identity and metadata version have different responsibilities.

```text
Identity = stable logical identity
Version  = immutable definition/configuration revision
```

Example:

```text
definition_id = catalog.assortment
version       = 1
```

A subsequent revision is:

```text
definition_id = catalog.assortment
version       = 2
```

The identity remains stable.

The compiled representation must be uniquely attributable to:

```text
definition identity + definition version
```

The same principle applies to configuration versions.

---

# 13. Immutability

The following artifacts are immutable after their respective lifecycle boundaries:

* validated definition representation;
* compiled metadata;
* READY configuration;
* ACTIVE configuration snapshot.

Modification must result in a new version/candidate rather than mutation of an active artifact.

This prevents hidden runtime state changes.

---

# 14. Lifecycle Ownership

| Component               | Responsibility                           |
| ----------------------- | ---------------------------------------- |
| Definition Source       | Provides metadata definitions            |
| Metadata Registry       | Definition registration and identity     |
| Metadata Validator      | Definition-level validation              |
| Metadata Compiler       | Definition compilation                   |
| Configuration Loader    | Loads configuration content              |
| Configuration Validator | Validates cross-definition configuration |
| Lifecycle Manager       | Controls lifecycle transitions           |
| Configuration Manager   | Maintains candidate/active configuration |
| Runtime Metadata API    | Read-only access to active metadata      |
| Runtime                 | Consumes active metadata                 |

The Runtime Metadata API does not own lifecycle transitions.

The Runtime does not perform metadata activation.

---

# 15. Runtime Boundary

Runtime metadata resolution must satisfy:

> Runtime resolves metadata only from an ACTIVE configuration.

Runtime must not:

* read raw definitions;
* read loader state;
* read candidate configuration;
* compile metadata;
* select arbitrary metadata versions;
* activate metadata;
* partially activate a configuration.

The Runtime receives already published metadata.

---

# 16. Lifecycle Invariants

The following invariants are normative.

### INV-001 — Registration is not validation

```text
REGISTERED ≠ VALIDATED
```

Registration alone does not establish metadata validity.

### INV-002 — Compilation follows validation

A definition must not become COMPILED unless it has successfully passed definition validation.

### INV-003 — Compiled metadata is immutable

A compiled metadata artifact cannot be modified in place.

### INV-004 — Configuration validation is independent

A configuration must pass configuration-level validation even when all individual definitions are valid.

### INV-005 — READY is not ACTIVE

A READY configuration is eligible for activation but is not runtime-authoritative.

### INV-006 — Activation is atomic

A configuration becomes ACTIVE as one coherent unit.

### INV-007 — Failed candidates cannot damage active configuration

Failure of a candidate configuration must leave the current ACTIVE configuration unchanged.

### INV-008 — Runtime sees only ACTIVE metadata

Runtime metadata resolution cannot use candidate or inactive configuration.

### INV-009 — Active configuration is coherent

Runtime must not observe a partially activated configuration.

### INV-010 — Version changes create new artifacts

Changing metadata or configuration creates a new version rather than mutating an existing active artifact.

---

# 17. Lifecycle and Configuration Loading Boundary

Configuration Loading is responsible for:

```text
Source
  ↓
Discovery
  ↓
Loading
  ↓
Materialization
```

Lifecycle management is responsible for:

```text
Validation
  ↓
Preparation
  ↓
READY
  ↓
Activation
```

The loader must not publish metadata directly to Runtime.

The Lifecycle Manager must not know how configuration content is physically obtained.

This separation allows configuration sources to evolve independently.

---

# 18. Standard Configuration

Standard Configuration follows the same lifecycle as any other metadata configuration.

It must not receive a special runtime activation path.

Conceptually:

```text
Standard Definitions
       ↓
Registration
       ↓
Validation
       ↓
Compilation
       ↓
Configuration Loading
       ↓
Configuration Validation
       ↓
READY
       ↓
Atomic Activation
       ↓
ACTIVE
       ↓
Runtime
```

This preserves the principle that Standard Configuration is configuration, not hard-coded Runtime knowledge.

---

# 19. Future Extensions

The lifecycle model intentionally allows future introduction of:

* configuration rollback;
* historical configuration retention;
* hot reload;
* deployment lifecycle;
* configuration migration;
* signed configuration artifacts;
* multi-tenant configurations;
* distributed configuration coordination.

These capabilities must extend the lifecycle model rather than bypass it.

---

# 20. Summary

The Phase 2 metadata lifecycle is based on the following architecture:

```text
Definition
    │
    ├── Register
    ├── Validate
    └── Compile
            │
            ▼
      Configuration
            │
            ├── Load
            ├── Validate
            ├── Resolve
            └── Prepare
                    │
                    ▼
                  READY
                    │
             Atomic Activation
                    │
                    ▼
                  ACTIVE
                    │
                    ▼
                 Runtime
```

The central rule is:

> **Loading prepares metadata; activation publishes metadata.**

The Runtime consumes only the published ACTIVE configuration.
