# Phase 2 — Configuration Candidate Validation / Readiness Model

**Status:** Proposed  
**Version:** 1.0  
**Phase:** Phase 2 — Metadata Lifecycle / Configuration Loading  
**Scope:** Configuration Candidate validation and readiness boundary

---

## 1. Purpose

This document defines the validation and readiness model for
`ConfigurationCandidate`.

It establishes the lifecycle boundary between:

- a successfully loaded configuration candidate;
- a validated configuration candidate;
- a candidate that may subsequently participate in activation.

The purpose of this model is to ensure that configuration loading and
configuration validation remain separate responsibilities.

Loading constructs a candidate.

Validation establishes that the candidate satisfies the configuration-level
invariants required by the next lifecycle stage.

Validation does not activate the candidate and does not create runtime objects.

---

## 2. Scope

This model covers:

- validation of `ConfigurationCandidate`;
- configuration-level validation rules;
- validation ownership;
- lifecycle transition from `LOADED` to `VALIDATED`;
- validation failure semantics;
- readiness semantics;
- repeated validation;
- isolation from runtime activation.

This model does not cover:

- configuration source discovery;
- configuration persistence;
- configuration loading;
- metadata compilation;
- runtime object creation;
- runtime initialization;
- activation;
- runtime health checks;
- user-facing configuration administration;
- database schema validation.

Those concerns belong to other architectural boundaries.

---

## 3. Architectural Context

The current Phase 2 configuration lifecycle is:

    Configuration Definitions
            |
            v
    Metadata Compiler
            |
            v
    Metadata Registry
            |
            v
    Configuration Candidate
            |
            v
    Candidate Validation
            |
            v
    Activation
            |
            v
    Runtime

The important distinction is:

    Loading    = construct candidate
    Validation = establish candidate correctness
    Activation = make candidate operational

These operations must remain separate.

---

## 4. Candidate Lifecycle

The lifecycle defined for Phase 2 is:

    LOADED
      |
      | validate
      v
    VALIDATED
      |
      | activate
      v
    ACTIVE

The following states are therefore explicitly distinguished:

### `LOADED`

The candidate has been successfully constructed by the configuration loading
boundary.

At this point:

- configuration definitions have been compiled;
- compiled metadata has been registered;
- candidate identity is known;
- candidate version is known;
- metadata registry is isolated to the candidate.

`LOADED` does not imply that the candidate is ready for activation.

### `VALIDATED`

The candidate has successfully passed all configuration-level validation rules
required by the current lifecycle boundary.

A `VALIDATED` candidate is considered ready for the next lifecycle stage.

`VALIDATED` does not imply that the candidate is active.

### `ACTIVE`

The candidate has been accepted by the activation boundary and is currently
the operational configuration.

Activation is outside the scope of this document.

---

## 5. Readiness Semantics

Readiness is represented by lifecycle state rather than by a separate mutable
boolean.

Therefore:

    candidate.state == VALIDATED

is the authoritative indication that the candidate has passed the validation
boundary.

The model does not introduce:

    candidate.is_ready

or:

    candidate.ready = True

A separate readiness flag could become inconsistent with lifecycle state.

Lifecycle state is therefore the single source of truth.

---

## 6. Validation Responsibility

Validation is owned by a dedicated configuration-level validation service.

Conceptually:

    ConfigurationCandidate
            |
            v
    ConfigurationValidator
            |
            v
    validated candidate

The validator is responsible for evaluating the candidate as a complete
configuration unit.

The validator must not:

- load definitions;
- compile definitions;
- create a metadata registry;
- create runtime objects;
- activate the candidate;
- mutate runtime state.

The validator consumes an already loaded candidate.

---

## 7. Validation Boundary

Candidate validation operates on compiled metadata rather than on raw
configuration definitions.

The expected flow is:

    Definition
        |
        v
    MetadataCompiler
        |
        v
    Metadata
        |
        v
    MetadataRegistry
        |
        v
    ConfigurationCandidate
        |
        v
    ConfigurationValidator

This preserves the separation between declarative definitions and runtime
metadata.

Validation therefore does not duplicate compilation responsibilities.

---

## 8. Configuration-Level Invariants

The first version of candidate validation establishes only invariants that
can be evaluated from the loaded configuration candidate.

The validation boundary may verify, where applicable:

- candidate identity is valid;
- candidate version is valid;
- candidate lifecycle state permits validation;
- metadata registry contains valid compiled metadata;
- metadata identities are unique;
- metadata types are supported;
- metadata names satisfy required invariants;
- metadata references are structurally valid;
- metadata relationships required by the configuration model are valid;
- required system metadata is present;
- configuration-level cross-object constraints are satisfied.

The validator must not assume runtime storage, runtime services, or an active
application context.

---

## 9. Validation Is Not Compilation

Compilation and validation have different responsibilities.

### Compilation

Compilation transforms a configuration definition into runtime-independent
metadata.

    Definition
        |
        v
    MetadataCompiler
        |
        v
    Metadata

Compilation answers:

> Can this definition be transformed into valid metadata?

### Candidate Validation

Candidate validation evaluates the complete loaded configuration.

    MetadataRegistry
        |
        v
    ConfigurationValidator
        |
        v
    VALIDATED candidate

Validation answers:

> Does this complete configuration satisfy the invariants required for the
> next lifecycle stage?

A successful compilation therefore does not imply successful candidate
validation.

---

## 10. Validation Is Not Runtime Validation

Configuration validation and runtime validation must remain separate.

Configuration validation verifies metadata and configuration semantics.

Runtime validation may later verify:

- storage availability;
- runtime service availability;
- external integration availability;
- operational dependencies;
- runtime-specific initialization constraints.

Those checks do not belong to the candidate validation boundary.

Therefore:

    ConfigurationValidator
        !=
    RuntimeValidator

---

## 11. Validation Transition

A successful validation performs the lifecycle transition:

    LOADED -> VALIDATED

The transition must occur only after all validation rules have completed
successfully.

Conceptually:

    candidate = LOADED

    validate(candidate)

    candidate = VALIDATED

No intermediate state is exposed as a successfully validated candidate.

---

## 12. Validation Failure

If validation fails:

    LOADED -> validation failure

The candidate must not transition to `VALIDATED`.

The candidate therefore remains non-ready.

The validation operation must raise a configuration-level validation error.

The error must provide enough information to identify the violated invariant.

Validation failure must not:

- activate the candidate;
- modify the active configuration;
- create runtime objects;
- partially transition the candidate.

---

## 13. Validation Error Model

Candidate validation should use a dedicated configuration validation error
rather than exposing implementation-specific exceptions from individual
validation rules.

Conceptually:

    ConfigurationValidator
            |
            +--> valid
            |       |
            |       v
            |   VALIDATED
            |
            +--> invalid
                    |
                    v
            ConfigurationValidationError

The first implementation may keep the error model intentionally small.

Detailed validation diagnostics, error codes, paths, and aggregation may be
introduced later when the validation rules become more complex.

---

## 14. Validation Atomicity

Validation is atomic from the lifecycle perspective.

A candidate is either:

- still `LOADED`; or
- successfully transitioned to `VALIDATED`.

The validator must not expose a partially validated state.

For a candidate containing multiple metadata objects:

    metadata A -> valid
    metadata B -> valid
    metadata C -> invalid

the candidate must not become `VALIDATED`.

The complete validation operation must succeed before the lifecycle transition
is committed.

---

## 15. Repeated Validation

Validation of a `LOADED` candidate may be repeated.

A successful validation produces:

    LOADED -> VALIDATED

Once a candidate is `VALIDATED`, repeated validation is not required to
produce another lifecycle transition.

The first implementation should treat validation of an already validated
candidate as idempotent.

Therefore:

    VALIDATED + validate() -> VALIDATED

No duplicate lifecycle transition should be created.

This keeps validation safe for orchestration code that may invoke validation
more than once.

---

## 16. Validation and Candidate Mutability

The candidate currently represents lifecycle state explicitly.

Its metadata registry is isolated from other candidates.

Candidate validation must not mutate the metadata definitions or compiled
metadata in order to make validation succeed.

Validation is therefore observational with respect to metadata content.

The only lifecycle mutation performed by the validation boundary is the
transition:

    LOADED -> VALIDATED

No metadata repair, normalization, or automatic correction is performed.

Invalid configuration must be rejected rather than silently modified.

---

## 17. Candidate Isolation

Validation operates exclusively on the supplied candidate.

It must not:

- inspect another candidate;
- modify another registry;
- access the active configuration;
- access global metadata state;
- register metadata outside the candidate.

This preserves candidate isolation established by the Configuration Loading
Boundary.

The lifecycle remains:

    load candidate A
        |
        v
    validate candidate A

    load candidate B
        |
        v
    validate candidate B

Candidate A and candidate B remain independent.

---

## 18. Active Configuration Isolation

Candidate validation must not depend on the currently active configuration.

This allows a new configuration to be validated before activation.

Therefore:

    Active Configuration
            |
            | remains unchanged
            |
            +--------------------+
                                 |
    Candidate -> Validation ----+
                                 |
                                 v
                         Candidate VALIDATED

A validation failure must have no effect on the active configuration.

---

## 19. Runtime Boundary

Candidate validation must not create or resolve runtime objects.

In particular, validation must not invoke:

- `RuntimeResolver`;
- `CatalogRuntime`;
- runtime storage;
- posting runtime;
- register runtime;
- reporting runtime;
- security runtime.

The runtime boundary begins only after activation.

This preserves:

    Metadata
        !=
    Runtime

and:

    Candidate Validation
        !=
    Runtime Initialization

---

## 20. Validator Interface

The initial conceptual API is:

    ConfigurationValidator.validate(candidate)

The method:

- accepts a `ConfigurationCandidate`;
- validates configuration-level invariants;
- returns the validated candidate or performs the lifecycle transition;
- raises a configuration validation error on failure.

The exact return-type convention may be finalized during implementation.

The validator should remain stateless unless a future validation rule requires
explicit dependencies.

---

## 21. Dependency Injection

The validator may receive explicit validation rules or supporting services
through its constructor.

However, the first implementation should avoid introducing an abstraction
framework before it is required.

The intended dependency direction is:

    ConfigurationValidator
            |
            +--> validation rules
            |
            +--> metadata registry inspection

The validator must not depend on runtime components.

---

## 22. Relationship to Metadata Registry

The candidate's `MetadataRegistry` remains the source of compiled metadata
for validation.

Validation may inspect the registry through its public API.

The validator must not reach into registry implementation details.

The registry therefore remains responsible for:

- metadata identity lookup;
- metadata registration;
- metadata containment.

The validator is responsible for:

- evaluating configuration-level invariants over registered metadata.

This preserves separation of responsibilities.

---

## 23. Lifecycle Ownership

Lifecycle state belongs to `ConfigurationCandidate`.

The validator does not become the lifecycle owner merely because it performs
the `LOADED -> VALIDATED` transition.

The conceptual ownership remains:

    ConfigurationCandidate
        = lifecycle state owner

    ConfigurationValidator
        = validation rule owner

This distinction is important for future lifecycle operations.

---

## 24. Activation Boundary

Candidate validation terminates immediately before activation.

The resulting boundary is:

    Configuration Loading
            |
            v
        ConfigurationCandidate
            |
            v
    Candidate Validation
            |
            v
        VALIDATED
            |
            v
        Activation
            |
            v
          ACTIVE

Activation is intentionally not part of this model.

The activation design must be specified separately.

---

## 25. State Transition Rules

The following transitions are defined by this model:

| Current State | Operation | Result |
|---|---|---|
| `LOADED` | validate successfully | `VALIDATED` |
| `LOADED` | validation fails | remains `LOADED` |
| `VALIDATED` | validate | remains `VALIDATED` |
| `ACTIVE` | validate | outside current boundary |

No implicit transition to `ACTIVE` is permitted.

---

## 26. Forbidden Behaviors

The following behaviors are explicitly prohibited:

### Validation must not activate

    validate(candidate)
        !=
    activate(candidate)

### Validation must not compile

    validate(candidate)
        !=
    compile(definition)

### Validation must not load

    validate(candidate)
        !=
    load(definitions)

### Validation must not repair

    invalid metadata
        !=
    automatically corrected metadata

### Validation must not mutate the active configuration

    validate(candidate)
        !=
    modify(active_configuration)

### Validation must not create runtime

    validate(candidate)
        !=
    create_runtime(candidate)

---

## 27. First-Version Non-Goals

The following are intentionally deferred:

- validation rule plugin architecture;
- validation severity levels;
- warning vs error classification;
- aggregated diagnostic trees;
- validation reports;
- localized validation messages;
- runtime dependency validation;
- storage validation;
- activation preflight;
- migration validation;
- compatibility validation between configuration versions;
- configuration upgrade validation.

These may be introduced when the corresponding architectural boundaries
become necessary.

---

## 28. Architectural Invariants

The following invariants are normative for v1.0:

### Invariant 1 — Loading and validation are separate

A successfully loaded candidate is not automatically validated.

### Invariant 2 — Validation precedes activation

A candidate must be `VALIDATED` before activation.

### Invariant 3 — Validation does not activate

Validation never transitions a candidate to `ACTIVE`.

### Invariant 4 — Validation is candidate-local

Validation operates only on the supplied candidate.

### Invariant 5 — Validation is atomic

A candidate becomes `VALIDATED` only after all required validation succeeds.

### Invariant 6 — Metadata is not repaired

Validation rejects invalid configuration rather than modifying it.

### Invariant 7 — Runtime remains outside validation

Candidate validation does not create or access runtime objects.

### Invariant 8 — Lifecycle state is the readiness source of truth

`VALIDATED` represents readiness for the next lifecycle stage.

---

## 29. Target Lifecycle Model

After this step the intended lifecycle is:

    Definitions
        |
        v
    Compilation
        |
        v
    Loading
        |
        v
    ConfigurationCandidate
        |
        | LOADED
        v
    Candidate Validation
        |
        | VALIDATED
        v
    Activation
        |
        | ACTIVE
        v
    Runtime

The important architectural distinction is:

    compile != load != validate != activate

Each operation has one clearly defined responsibility.

---

## 30. Implementation Direction

The implementation following this design should introduce the smallest
possible validation boundary.

Expected initial components:

    configuration/
        candidate.py
        identity.py
        lifecycle.py
        loader.py
        validator.py

and corresponding unit tests.

The implementation should initially validate only invariants that can be
demonstrated from the existing metadata model.

New metadata concepts or runtime dependencies must not be introduced solely
to make the validator appear more complete.

---

## 31. Review Gate

Step 4 is considered complete when:

- candidate validation responsibilities are explicitly defined;
- `VALIDATED` is established as the readiness state;
- validation is separated from compilation and loading;
- validation is separated from activation;
- validation failure semantics are defined;
- candidate isolation is preserved;
- runtime remains outside the validation boundary;
- implementation scope is sufficiently constrained for the next step.

No implementation is implied by this document until the design is accepted.