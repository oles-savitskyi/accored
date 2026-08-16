# Configuration Loading Model

**Status:** Proposed
**Version:** 1.0
**Phase:** Phase 2 — Metadata → Runtime
**Depends on:** Metadata Lifecycle Model 1.0

---

## 1. Purpose

This document defines how AcCore loads metadata configuration and transforms configuration input into a candidate configuration suitable for lifecycle validation and activation.

The model establishes:

* configuration loading stages;
* loader responsibilities;
* loading boundaries;
* definition discovery;
* dependency handling;
* materialization;
* validation handoff;
* candidate configuration construction;
* failure behavior;
* integration with Metadata Lifecycle.

---

# 2. Core Principle

The Configuration Loader is a producer of candidate configuration.

It does not own runtime activation.

The fundamental flow is:

```text
Configuration Source
        ↓
Discovery
        ↓
Loading
        ↓
Materialization
        ↓
Definition Registration
        ↓
Definition Validation
        ↓
Configuration Validation
        ↓
Candidate Preparation
        ↓
READY
        ↓
Lifecycle Manager
        ↓
ACTIVE
```

The Loader must never directly publish metadata to Runtime.

---

# 3. Loading Boundary

The loader is responsible for converting an external or internal configuration source into a platform-understood metadata configuration.

The loader does not decide whether the configuration becomes runtime-authoritative.

Therefore:

```text
Loader → Candidate
Lifecycle Manager → Activation
Runtime → Consumption
```

These responsibilities must remain separate.

---

# 4. Configuration Source

A Configuration Source provides metadata configuration content.

The source may be:

* Standard Configuration package;
* local configuration files;
* embedded platform resources;
* future external repository;
* future database-backed source.

The loading model does not require a particular physical source.

The source abstraction should provide configuration content without exposing source-specific details to Runtime.

---

# 5. Loading Stages

The loading pipeline consists of the following logical stages:

```text
1. DISCOVER
2. LOAD
3. MATERIALIZE
4. REGISTER
5. VALIDATE DEFINITIONS
6. RESOLVE DEPENDENCIES
7. VALIDATE CONFIGURATION
8. COMPILE / PREPARE
9. BUILD CANDIDATE
10. HAND OFF TO LIFECYCLE MANAGER
```

These stages may be internally optimized or combined in implementation, but their architectural responsibilities remain distinct.

---

# 6. Stage 1 — Discovery

Discovery identifies the configuration to be loaded.

Inputs may include:

* configuration identifier;
* configuration version;
* source;
* optional loading context.

Discovery must establish enough information to identify the intended configuration.

Discovery does not validate or activate the configuration.

Output:

```text
ConfigurationDescriptor
```

---

# 7. Stage 2 — Load

The loader reads configuration content from the selected source.

Output:

```text
Raw Configuration
```

The raw representation remains source-oriented.

The Runtime must never consume this representation directly.

Loading errors terminate the candidate build.

---

# 8. Stage 3 — Materialization

Materialization transforms source-oriented configuration content into platform metadata definitions.

Example:

```text
Raw configuration
       ↓
Definition objects
       ↓
Metadata definitions
```

Materialization may create:

* metadata definitions;
* attributes;
* references;
* configuration entries;
* version descriptors;
* source metadata.

Materialization does not imply validity.

---

# 9. Stage 4 — Registration

Materialized definitions are registered with the Metadata Registry.

Registration establishes metadata identity and makes definitions available to subsequent lifecycle operations.

The registration stage must not activate definitions.

A failed registration prevents the candidate from becoming READY.

---

# 10. Stage 5 — Definition Validation

Each definition passes the Metadata Validator.

Validation establishes that definitions conform to the metadata model.

Typical checks include:

* identifier validity;
* required metadata fields;
* attribute validity;
* system field constraints;
* supported metadata types;
* local semantic constraints.

The output is a set of validated definitions suitable for compilation.

---

# 11. Stage 6 — Dependency Resolution

After definitions are available, metadata relationships and dependencies are resolved.

Examples:

```text
Document → Register
Document → Catalog
Field → Attribute
Register → Dimension
Reference → Target Definition
```

Dependency resolution must detect:

* missing definitions;
* invalid references;
* incompatible versions;
* dependency cycles where cycles are prohibited;
* ambiguous targets.

Dependency resolution produces a coherent metadata dependency graph.

---

# 12. Stage 7 — Configuration Validation

Configuration validation operates on the complete candidate configuration.

It validates properties that cannot be established from individual definitions.

Examples:

* duplicate identities;
* conflicting definitions;
* incompatible versions;
* invalid cross-definition relationships;
* missing required configuration members;
* configuration-level invariants.

The configuration must not become READY until this stage succeeds.

---

# 13. Stage 8 — Compilation and Preparation

Validated definitions are compiled into runtime-oriented representations.

The preparation stage builds everything required for activation.

This may include:

* compiled metadata;
* resolved references;
* runtime metadata indexes;
* lookup structures;
* configuration snapshots;
* runtime metadata views.

Preparation must produce an internally coherent candidate.

The active runtime configuration is not modified during preparation.

---

# 14. Stage 9 — Candidate Construction

The loader constructs a complete candidate configuration.

Conceptually:

```text
Candidate Configuration
├── Configuration identity
├── Configuration version
├── Definitions
├── Compiled metadata
├── Resolved dependencies
├── Runtime metadata view
└── Validation/preparation result
```

The candidate is immutable after preparation.

A successfully prepared candidate is eligible for:

```text
READY
```

---

# 15. Stage 10 — Lifecycle Handoff

The loader hands the candidate to the Lifecycle Manager.

The Lifecycle Manager is responsible for:

* final lifecycle transition;
* activation eligibility;
* atomic publication;
* active configuration replacement.

The loader does not call Runtime APIs to publish metadata.

---

# 16. Candidate Isolation

The candidate must be isolated from the active configuration.

During loading:

```text
ACTIVE v1
```

continues serving Runtime.

Meanwhile:

```text
CANDIDATE v2
```

is constructed independently.

Only after successful preparation:

```text
CANDIDATE v2
      ↓
READY v2
      ↓
atomic activation
      ↓
ACTIVE v2
```

This guarantees that a failed configuration load cannot corrupt the current runtime state.

---

# 17. Failure Model

Any failure before activation invalidates the candidate operation.

Examples:

```text
Source unavailable
Malformed configuration
Materialization error
Registration conflict
Definition validation error
Missing dependency
Invalid reference
Compilation failure
Configuration validation failure
Preparation failure
```

The expected behavior is:

```text
Candidate build fails
        ↓
Candidate discarded
        ↓
Current ACTIVE configuration unchanged
```

No partial activation is permitted.

---

# 18. Configuration Loading Does Not Mutate Active Runtime State

The following operations must not modify the active runtime metadata configuration:

* discovery;
* loading;
* materialization;
* registration of candidate definitions;
* validation;
* dependency resolution;
* compilation;
* candidate preparation.

Only the explicit activation boundary may change the authoritative runtime configuration.

---

# 19. Registration Isolation

The Metadata Registry must support the distinction between:

```text
Registered Definition
```

and:

```text
Runtime-Active Definition
```

Candidate registration must not imply runtime publication.

If the implementation requires a registry staging area, candidate definitions may be registered there until activation.

The precise storage strategy is an implementation concern, but the semantic separation is mandatory.

---

# 20. Version Selection

The loading operation must have an explicit configuration identity and version.

The loader must not silently select arbitrary versions.

Conceptually:

```text
load(
    configuration_id,
    configuration_version
)
```

If version selection is delegated to a higher-level configuration resolver, the resolved version must still become explicit before loading begins.

---

# 21. Idempotency

Loading the same configuration version multiple times should produce equivalent candidate configurations.

For:

```text
configuration_id = standard
version = 1
```

repeated loading must not create semantic differences.

Idempotency does not require reuse of the same in-memory object.

It requires equivalent metadata semantics.

---

# 22. Determinism

Given the same:

* configuration source;
* configuration version;
* metadata model version;
* applicable loading context;

the loader should produce the same logical candidate configuration.

This is important for:

* testing;
* reproducibility;
* diagnostics;
* future deployment;
* configuration comparison.

---

# 23. Runtime Metadata View

The candidate must contain or be able to construct the metadata view consumed by Runtime.

The view must be:

* internally coherent;
* based on compiled metadata;
* independent from raw source representation;
* immutable after activation.

Runtime should not need to understand the loading process.

---

# 24. Standard Configuration Loading

Standard Configuration uses the same loading pipeline:

```text
Standard Configuration Source
        ↓
Discovery
        ↓
Load
        ↓
Materialize
        ↓
Register
        ↓
Validate
        ↓
Resolve
        ↓
Compile
        ↓
Prepare
        ↓
READY
        ↓
Activate
        ↓
ACTIVE
```

No Standard Configuration metadata is hard-coded into Runtime.

---

# 25. Loading and Lifecycle Responsibility Matrix

| Operation               |        Loader | Lifecycle Manager | Runtime |
| ----------------------- | ------------: | ----------------: | ------: |
| Discover source         |             ✓ |                   |         |
| Read configuration      |             ✓ |                   |         |
| Materialize definitions |             ✓ |                   |         |
| Register definitions    |             ✓ |                   |         |
| Validate definitions    | ✓ / Validator |                   |         |
| Resolve dependencies    | ✓ / Validator |                   |         |
| Validate configuration  | ✓ / Validator |                   |         |
| Compile metadata        |  ✓ / Compiler |                   |         |
| Build candidate         |             ✓ |                   |         |
| Determine READY         |               |                 ✓ |         |
| Activate                |               |                 ✓ |         |
| Replace ACTIVE          |               |                 ✓ |         |
| Resolve active metadata |               |                   |       ✓ |
| Consume metadata        |               |                   |       ✓ |

The exact service decomposition may differ in implementation, but ownership must preserve these semantic boundaries.

---

# 26. Loading Model Invariants

### LOAD-INV-001 — Loader does not activate

Configuration loading never makes a configuration ACTIVE.

### LOAD-INV-002 — Candidate isolation

Candidate construction cannot modify the active runtime configuration.

### LOAD-INV-003 — Complete candidate

A candidate must represent a complete coherent configuration before becoming READY.

### LOAD-INV-004 — Validation before activation

A configuration cannot be activated unless all required validation and preparation gates have succeeded.

### LOAD-INV-005 — No partial publication

Individual definitions belonging to a configuration cannot be partially published.

### LOAD-INV-006 — Explicit version

The configuration version being loaded must be deterministic and identifiable.

### LOAD-INV-007 — Failed candidate preservation

A failed candidate must not alter the current ACTIVE configuration.

### LOAD-INV-008 — Runtime/source separation

Runtime never consumes source-oriented configuration data.

### LOAD-INV-009 — Prepared candidate immutability

A READY candidate cannot be mutated after preparation.

### LOAD-INV-010 — Standard configuration follows the same path

Standard Configuration cannot bypass the lifecycle model.

---

# 27. Relationship to Metadata Lifecycle

The relationship is:

```text
Configuration Loading Model
             │
             ▼
       Candidate Build
             │
             ▼
Metadata Lifecycle Model
             │
             ▼
       READY → ACTIVE
```

The loader therefore implements the preparation side of the lifecycle but does not own publication.

---

# 28. Phase 2 Scope

The initial implementation should support:

1. One local configuration source.
2. Explicit configuration identity/version.
3. Definition materialization.
4. Metadata registration.
5. Definition validation.
6. Dependency/reference resolution.
7. Configuration validation.
8. Metadata compilation.
9. Candidate construction.
10. READY/ACTIVE lifecycle boundary.
11. Atomic replacement semantics.
12. Standard Configuration loading through the same path.

The following may remain future work:

* remote configuration sources;
* distributed loading;
* persistent candidate storage;
* rollback;
* migration;
* hot reload;
* deployment orchestration.

---

# 29. Acceptance Criteria

Configuration Loading is considered correctly implemented when:

* a configuration can be discovered and loaded;
* definitions are materialized and registered;
* definition validation is performed;
* cross-definition dependencies are resolved;
* configuration-level validation is performed;
* compiled metadata is prepared;
* a complete candidate configuration is constructed;
* failed candidates are discarded without affecting ACTIVE configuration;
* a valid candidate can reach READY;
* activation occurs only through the Lifecycle Manager;
* activation is atomic;
* Runtime sees only ACTIVE metadata;
* Standard Configuration follows the same loading path;
* repeated loading of the same configuration version is semantically deterministic.

---

# 30. Summary

The Configuration Loading Model establishes a strict separation:

```text
SOURCE
  ↓
LOAD
  ↓
MATERIALIZE
  ↓
REGISTER
  ↓
VALIDATE
  ↓
RESOLVE
  ↓
COMPILE
  ↓
PREPARE
  ↓
CANDIDATE
  ↓
READY
  ↓
ATOMIC ACTIVATION
  ↓
ACTIVE
  ↓
RUNTIME
```

The central architectural rule is:

> **The Configuration Loader prepares a candidate; the Lifecycle Manager publishes it; the Runtime consumes only the published configuration.**
