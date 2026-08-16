# Phase 2 Metadata Lifecycle Implementation Plan

**Status:** Proposed
**Version:** 1.0
**Phase:** Phase 2 — Metadata → Runtime
**Prerequisites:**

* Phase 2 Runtime Metadata API Review Gate — completed
* Commit baseline: `6ceef8d`
* Tests: `122 passed`
* `ruff`: OK
* `black`: OK
* `mypy`: OK
* `METADATA_LIFECYCLE_MODEL.md` — v1.0
* `CONFIGURATION_LOADING_MODEL.md` — v1.0

---

# 1. Purpose

This document defines the implementation plan for the Metadata Lifecycle and Configuration Loading portion of Phase 2.

The implementation must introduce a controlled lifecycle for metadata configuration without weakening the boundaries already established by:

* Foundation;
* Metadata;
* Compiler;
* Registry;
* Runtime Metadata API;
* Standard Bootstrap;
* Catalog Runtime.

The implementation must preserve the architectural principle:

> **Loading prepares a candidate configuration; activation publishes it; Runtime consumes only the active configuration.**

---

# 2. Implementation Objective

At the end of this implementation stage, AcCore must be able to:

1. identify a configuration;
2. load its metadata definitions;
3. register and validate definitions;
4. resolve metadata dependencies;
5. compile metadata;
6. construct an immutable candidate configuration;
7. prepare the candidate for runtime publication;
8. mark the candidate READY;
9. atomically activate it;
10. expose only the active configuration to Runtime Metadata API;
11. replace an active configuration with a valid candidate;
12. reject failed candidates without affecting the active configuration.

Standard Configuration must use the same lifecycle path.

---

# 3. Architectural Target

The target architecture is:

```text
Configuration Source
        │
        ▼
Configuration Loader
        │
        ├── materialize definitions
        ├── register definitions
        ├── validate definitions
        ├── resolve dependencies
        ├── compile metadata
        └── build candidate
                │
                ▼
        Candidate Configuration
                │
                ▼
             PREPARED
                │
                ▼
        Lifecycle Manager
                │
                ▼
              READY
                │
        atomic activation
                │
                ▼
              ACTIVE
                │
                ▼
       Runtime Metadata API
                │
                ▼
              Runtime
```

The exact internal class structure may evolve, but these semantic boundaries are mandatory.

---

# 4. Core Design Decisions

## 4.1 Metadata Registry and Active Configuration are separate concepts

The Metadata Registry remains responsible for metadata definition registration and identity.

It must not become the authoritative store of active configuration state.

Active configuration is owned by a configuration/lifecycle layer.

Therefore:

```text
Metadata Registry
    → metadata definitions / identity

Configuration Manager
    → candidate / active configuration
```

---

## 4.2 Candidate metadata is isolated

Candidate metadata must not contaminate active runtime metadata.

The implementation must support semantic separation between:

```text
Active Metadata Context
Candidate Metadata Context
```

The exact mechanism may be:

* immutable metadata snapshots;
* isolated registries;
* candidate-local contexts;
* another equivalent mechanism.

The implementation must not depend on global mutable state shared by active and candidate configurations.

---

## 4.3 `PREPARED` and `READY` are separate states

The lifecycle is:

```text
DISCOVERED
    ↓
LOADED
    ↓
VALIDATED
    ↓
PREPARED
    ↓
READY
    ↓
ACTIVE
    ↓
INACTIVE
```

Meaning:

### VALIDATED

The configuration is semantically valid.

### PREPARED

All runtime-oriented artifacts required for publication have been constructed.

### READY

The candidate has successfully passed lifecycle preparation and is eligible for atomic activation.

### ACTIVE

The configuration is authoritative for Runtime.

---

# 5. Component Responsibilities

## 5.1 Configuration Source

Provides configuration content.

Responsibilities:

* identify source;
* expose configuration content;
* provide configuration identity/version information.

Must not:

* validate runtime semantics;
* activate configuration;
* access Runtime.

---

## 5.2 Configuration Loader

Responsible for candidate construction.

Responsibilities:

* discovery;
* loading;
* materialization;
* definition registration;
* definition validation orchestration;
* dependency resolution;
* configuration validation orchestration;
* compilation orchestration;
* candidate construction.

Must not:

* activate configuration;
* mutate active runtime state;
* expose partially built candidate as active metadata.

---

## 5.3 Metadata Registry

Responsible for metadata definition registration and identity.

Existing functionality should be reused where possible.

The implementation must avoid moving lifecycle responsibility into the Registry.

---

## 5.4 Metadata Validator

Responsible for definition-level metadata validation.

Existing validation functionality should be reused where possible.

Configuration-level validation remains a separate concern.

---

## 5.5 Metadata Compiler

Responsible for producing compiled metadata.

The compiler remains independent of lifecycle management.

Compilation must produce immutable or effectively immutable runtime-oriented metadata.

---

## 5.6 Configuration Validator

New or extended responsibility.

Responsible for validating relationships across definitions.

Examples:

* references;
* dependencies;
* duplicate identities;
* incompatible versions;
* configuration-level constraints.

---

## 5.7 Configuration Candidate

Represents the complete candidate configuration.

Conceptually:

```text
ConfigurationCandidate
├── configuration identity
├── configuration version
├── metadata context
├── definitions
├── compiled metadata
├── resolved dependencies
├── runtime metadata view
└── lifecycle state
```

The candidate must become immutable once preparation is complete.

---

## 5.8 Lifecycle Manager

Owns lifecycle transitions.

Responsibilities:

* accept prepared candidates;
* enforce lifecycle invariants;
* transition candidate to READY;
* atomically activate;
* replace active configuration;
* retain previous active configuration as INACTIVE where required.

Must not:

* load configuration sources;
* materialize definitions;
* compile raw metadata;
* access source-specific formats.

---

## 5.9 Active Configuration Manager

Maintains the currently active configuration.

Responsibilities:

* expose active configuration snapshot;
* provide atomic replacement;
* ensure only one configuration is authoritative per configuration scope;
* provide safe read access to Runtime Metadata API.

The implementation should prefer immutable snapshots over mutable active state.

---

## 5.10 Runtime Metadata API

The existing Runtime Metadata API remains a read-side interface.

It must be extended only as necessary to resolve metadata from the active configuration.

It must not become responsible for:

* loading;
* compilation;
* validation;
* activation;
* lifecycle transitions.

---

# 6. Proposed Domain Objects

The exact naming may be adjusted to existing project conventions, but the following conceptual objects should exist.

## 6.1 ConfigurationIdentity

Identifies the logical configuration.

```text
configuration_id
```

---

## 6.2 ConfigurationVersion

Identifies an immutable revision.

```text
configuration_version
```

---

## 6.3 ConfigurationDescriptor

Describes a configuration before loading.

Conceptually:

```text
ConfigurationDescriptor
├── configuration_id
├── configuration_version
└── source information
```

---

## 6.4 ConfigurationCandidate

Represents a candidate being prepared for activation.

Conceptually:

```text
ConfigurationCandidate
├── descriptor
├── metadata context
├── definitions
├── compiled metadata
├── dependency graph
└── state
```

---

## 6.5 ConfigurationSnapshot

Represents immutable runtime-visible configuration.

Conceptually:

```text
ConfigurationSnapshot
├── configuration_id
├── configuration_version
├── metadata context
└── runtime metadata view
```

A snapshot should be immutable after publication.

---

# 7. Lifecycle State Model

## 7.1 Definition Lifecycle

Existing metadata lifecycle remains:

```text
DEFINED
   ↓
REGISTERED
   ↓
VALIDATED
   ↓
COMPILED
```

No new runtime lifecycle responsibility should be introduced into these states.

---

## 7.2 Configuration Lifecycle

Implementation target:

```text
DISCOVERED
   ↓
LOADED
   ↓
VALIDATED
   ↓
PREPARED
   ↓
READY
   ↓
ACTIVE
   ↓
INACTIVE
```

---

# 8. Transition Ownership

| Transition           | Owner                                    |
| -------------------- | ---------------------------------------- |
| DISCOVERED → LOADED  | Configuration Loader                     |
| LOADED → VALIDATED   | Configuration Validator / Loader         |
| VALIDATED → PREPARED | Configuration Loader / Preparation layer |
| PREPARED → READY     | Lifecycle Manager                        |
| READY → ACTIVE       | Lifecycle Manager                        |
| ACTIVE → INACTIVE    | Lifecycle Manager                        |

The Runtime has no lifecycle transition authority.

---

# 9. Configuration Loading API

The implementation should expose a narrow configuration-loading boundary.

Conceptually:

```text
load(descriptor) → ConfigurationCandidate
```

The returned candidate must not automatically become ACTIVE.

The loader should return only after:

* materialization;
* definition validation;
* dependency resolution;
* configuration validation;
* compilation;
* preparation.

A successful return therefore produces a candidate capable of entering READY.

---

# 10. Lifecycle API

The lifecycle boundary should remain explicit.

Conceptually:

```text
prepare(candidate) → READY candidate
activate(candidate) → Active Configuration
```

The implementation may combine `prepare` with candidate construction if the semantic boundary remains visible.

Activation must be a separate operation.

---

# 11. Atomic Activation

Activation must replace the active configuration atomically.

Conceptually:

```text
old_active = active_configuration
new_active = ready_candidate

publish(new_active)

old_active → INACTIVE
```

Runtime must never observe:

```text
no configuration
```

or:

```text
partially activated configuration
```

The exact synchronization mechanism is an implementation concern.

The semantic requirement is atomic publication.

---

# 12. Candidate Isolation Strategy

The implementation must choose one concrete mechanism.

Recommended direction:

```text
Candidate Metadata Context
        │
        ├── definitions
        ├── compiled metadata
        ├── resolved references
        └── runtime view
```

The active runtime context remains separate:

```text
Active Metadata Context
```

The candidate may be built completely without changing the active context.

Once activated, the candidate context becomes the active snapshot.

This model is preferable to mutating a global registry in place.

---

# 13. Configuration Loading Pipeline

Implementation target:

```text
discover
   ↓
load
   ↓
materialize
   ↓
register
   ↓
validate definitions
   ↓
resolve dependencies
   ↓
validate configuration
   ↓
compile
   ↓
prepare runtime view
   ↓
build candidate
   ↓
PREPARED
   ↓
READY
   ↓
activate
   ↓
ACTIVE
```

Each step must have a clear failure boundary.

---

# 14. Error Handling

Configuration loading must use explicit failure semantics.

Potential error categories:

* source errors;
* configuration parsing/materialization errors;
* metadata registration errors;
* metadata validation errors;
* dependency resolution errors;
* configuration validation errors;
* compilation errors;
* preparation errors;
* lifecycle transition errors;
* activation errors.

A failed candidate must not affect the active configuration.

---

# 15. Active Configuration Failure Semantics

The implementation must preserve:

```text
ACTIVE v1
```

when:

```text
candidate v2
```

fails.

Therefore:

```text
load v2
   ↓
failure
   ↓
discard v2
   ↓
ACTIVE v1 remains
```

The active configuration is never invalidated merely because a replacement candidate fails.

---

# 16. Runtime Integration

Runtime Metadata API should resolve from:

```text
Active Configuration Snapshot
```

rather than from:

```text
Metadata Registry + arbitrary definitions
```

The API should remain stable for existing Runtime consumers.

The implementation should minimize changes to already completed Runtime Metadata API behavior.

---

# 17. Standard Bootstrap Integration

The existing Standard Bootstrap must eventually become a configuration source/loader path rather than a special runtime initialization mechanism.

Target:

```text
Standard Configuration
       ↓
Configuration Loader
       ↓
Candidate
       ↓
Lifecycle Manager
       ↓
ACTIVE
       ↓
Runtime
```

The Bootstrap must not bypass:

* validation;
* compilation;
* candidate construction;
* activation semantics.

---

# 18. Implementation Sequence

Implementation should proceed through small vertical increments.

## Step 1 — Lifecycle Domain Types

Introduce:

* configuration identity;
* configuration version;
* lifecycle states;
* configuration descriptor;
* candidate/snapshot concepts.

### Gate

* types are coherent;
* no Runtime behavior changes;
* existing tests remain green.

---

## Step 2 — Configuration Candidate

Implement candidate construction and immutable/prepared representation.

### Gate

Candidate can represent:

* identity;
* version;
* metadata context;
* compiled metadata;
* dependency information.

No activation yet.

---

## Step 3 — Configuration Validation Boundary

Introduce configuration-level validation separate from definition validation.

### Gate

Tests demonstrate:

* individually valid definitions may form invalid configuration;
* invalid references are rejected;
* duplicate identities are rejected;
* valid configuration passes.

---

## Step 4 — Configuration Loader

Implement the loading pipeline.

Target:

```text
source → candidate
```

### Gate

A valid configuration can be loaded into a candidate without changing active Runtime state.

---

## Step 5 — Preparation

Build compiled metadata and runtime metadata view.

Target:

```text
VALIDATED → PREPARED
```

### Gate

Prepared candidate is internally complete and immutable.

---

## Step 6 — Lifecycle Manager

Implement:

```text
PREPARED → READY
```

and lifecycle invariants.

### Gate

Only valid prepared candidates can become READY.

---

## Step 7 — Active Configuration

Introduce immutable active configuration snapshot.

### Gate

Runtime Metadata API can resolve from active configuration.

---

## Step 8 — Atomic Activation

Implement:

```text
READY → ACTIVE
```

and replacement:

```text
ACTIVE v1 → ACTIVE v2
             +
          INACTIVE v1
```

### Gate

Runtime never observes a partially activated configuration.

---

## Step 9 — Failure Preservation

Verify:

```text
ACTIVE v1
```

survives failures of:

* loading;
* validation;
* compilation;
* preparation;
* activation candidate construction.

---

## Step 10 — Standard Configuration Integration

Route Standard Configuration through the new lifecycle.

### Gate

Standard Configuration reaches Runtime exclusively through:

```text
Loader → Candidate → Lifecycle → Active Configuration → Runtime
```

---

# 19. Testing Strategy

Testing must operate at several levels.

## 19.1 Unit Tests

Test:

* lifecycle states;
* transition rules;
* candidate immutability;
* configuration identity/version;
* validation;
* dependency resolution;
* activation rules.

---

## 19.2 Loader Tests

Test:

* successful loading;
* malformed configuration;
* missing definitions;
* invalid references;
* duplicate definitions;
* failed compilation;
* candidate isolation.

---

## 19.3 Lifecycle Tests

Test:

* PREPARED → READY;
* READY → ACTIVE;
* replacement;
* inactive previous configuration;
* invalid transition rejection;
* failed candidate preservation.

---

## 19.4 Runtime Integration Tests

Test:

```text
Active configuration
       ↓
Runtime Metadata API
       ↓
Runtime object resolution
```

Verify that candidate metadata is invisible until activation.

---

## 19.5 Standard Configuration Vertical Slice

At least one complete Standard Configuration vertical slice must prove:

```text
Standard Source
    ↓
Loader
    ↓
Candidate
    ↓
Validation
    ↓
Preparation
    ↓
READY
    ↓
ACTIVE
    ↓
Runtime Metadata API
    ↓
Runtime object
```

---

# 20. Quality Gates

Each implementation step must satisfy:

```text
pytest
ruff
black
mypy
```

No step should introduce temporary architectural exceptions merely to make tests pass.

The implementation must preserve the current Phase 2 baseline.

---

# 21. Backward Compatibility

The existing Runtime Metadata API behavior must remain compatible unless a change is explicitly required by lifecycle semantics.

Existing consumers should not need to understand:

* candidate configuration;
* loading;
* lifecycle states;
* activation.

Lifecycle concerns remain behind the Runtime Metadata API boundary.

---

# 22. Explicit Non-Goals

This implementation does not include:

* distributed configuration;
* multi-process synchronization;
* remote configuration loading;
* configuration migration;
* database persistence of lifecycle state;
* rollback implementation;
* hot reload;
* deployment orchestration;
* configuration signing;
* multi-tenant activation.

These may be addressed by later phases.

---

# 23. Architectural Invariants

The implementation must preserve the following invariants.

### IMPL-INV-001

The loader never activates configuration.

### IMPL-INV-002

Runtime never consumes candidate configuration.

### IMPL-INV-003

Active configuration is immutable.

### IMPL-INV-004

Candidate configuration is isolated from active configuration.

### IMPL-INV-005

Activation is atomic.

### IMPL-INV-006

A failed candidate cannot invalidate the active configuration.

### IMPL-INV-007

Runtime Metadata API remains a read-side interface.

### IMPL-INV-008

Standard Configuration follows the same lifecycle path.

### IMPL-INV-009

Configuration identity and version are explicit.

### IMPL-INV-010

Lifecycle state transitions are explicit and validated.

---

# 24. Phase 2 Completion Criteria

The Metadata Lifecycle / Configuration Loading stage is complete when:

* Metadata Definition lifecycle is preserved;
* Configuration lifecycle is implemented;
* candidate configuration exists as an isolated artifact;
* definition validation and configuration validation are distinct;
* dependency resolution is implemented;
* compiled metadata is part of prepared candidate;
* PREPARED and READY are distinct semantic states;
* Lifecycle Manager owns activation;
* Active Configuration is immutable;
* activation is atomic;
* replacement is supported;
* failed candidates cannot affect active configuration;
* Runtime Metadata API resolves only active metadata;
* Standard Configuration uses the same path;
* tests cover all lifecycle transitions and failure boundaries;
* `pytest`, `ruff`, `black`, and `mypy` pass;
* documentation reflects the final implementation.

---

# 25. Recommended Implementation Order

The recommended order is:

```text
1. Lifecycle Domain Types
          ↓
2. Configuration Candidate
          ↓
3. Configuration Validation
          ↓
4. Configuration Loader
          ↓
5. Preparation
          ↓
6. Lifecycle Manager
          ↓
7. Active Configuration Snapshot
          ↓
8. Atomic Activation
          ↓
9. Failure / Replacement Tests
          ↓
10. Standard Configuration Integration
          ↓
11. Phase 2 Lifecycle Review Gate
```

The implementation should be committed in small, reviewable increments.

Each increment should leave the repository in a passing state.

---

# 26. Final Architectural Target

The completed Phase 2 lifecycle should provide the following separation:

```text
                     METADATA
                        │
          ┌─────────────┴─────────────┐
          │                           │
      Registry                    Compiler
          │                           │
          └─────────────┬─────────────┘
                        │
                        ▼
                Configuration Loader
                        │
                        ▼
                Candidate Context
                        │
                  VALIDATED
                        │
                  PREPARED
                        │
                        ▼
                Lifecycle Manager
                        │
                     READY
                        │
                Atomic Activation
                        │
                        ▼
                Active Configuration
                        │
                        ▼
              Runtime Metadata API
                        │
                        ▼
                     Runtime
```

The architectural contract is:

> **Metadata infrastructure creates and validates metadata; Configuration Loading assembles it; Lifecycle Management publishes it; Runtime consumes only the published configuration.**

This boundary is the implementation foundation for the remainder of Phase 2.
