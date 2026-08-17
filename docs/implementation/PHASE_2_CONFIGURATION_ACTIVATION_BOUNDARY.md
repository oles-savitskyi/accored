# Phase 2 — Configuration Activation Boundary

**Status:** Design  
**Version:** 1.0  
**Phase:** Phase 2 — Metadata Lifecycle / Configuration Loading  
**Step:** Step 5 — Configuration Activation Boundary  
**Depends on:**
- `METADATA_LIFECYCLE_MODEL.md`
- `PHASE_2_METADATA_LIFECYCLE_IMPLEMENTATION_PLAN.md`
- `PHASE_2_CONFIGURATION_LOADING_BOUNDARY.md`
- `PHASE_2_CONFIGURATION_LOADING_IMPLEMENTATION_PLAN.md`
- `PHASE_2_CONFIGURATION_CANDIDATE_VALIDATION_MODEL.md`

---

## 1. Purpose

This document defines the v1.0 architecture of the Configuration Activation Boundary.

The Configuration Activation Boundary is responsible for promoting a validated configuration candidate into the configuration snapshot visible to the runtime.

The boundary establishes a strict separation between:

- configuration definition;
- configuration loading;
- metadata compilation;
- candidate validation;
- configuration activation;
- runtime metadata resolution.

The central principle is:

> Loading and validation prepare a configuration. Activation publishes it to the runtime.

Validation does not activate a configuration.

Loading does not activate a configuration.

Activation creates the runtime snapshot; binding owns the current runtime snapshot; resolution consumes it.
---

## 2. Architectural Position

The configuration lifecycle is:

```text
Configuration Definitions
        │
        ▼
Metadata Compiler
        │
        ▼
Configuration Loader
        │
        ▼
LOADED Candidate
        │
        ▼
Configuration Validator
        │
        ▼
VALIDATED Candidate
        │
        ▼
Configuration Activation Boundary
        │
        ▼
ActiveConfiguration
        │
        ▼
RuntimeConfigurationBinding
        │
        ▼
MetadataResolver
        │
        ▼
Runtime

Each stage has a distinct responsibility.

Configuration Loader

Creates an isolated configuration candidate from configuration definitions.

Configuration Validator

Determines whether the candidate is structurally and semantically valid for activation.

Configuration Activator

Publishes a validated candidate as the active configuration.

Runtime

Consumes the active configuration and does not participate in configuration construction.

3. Core Principles
3.1. Activation Is a Separate Boundary

Activation is an explicit lifecycle operation.

A successful load must not imply activation.

A successful validation must not imply activation.

The following distinction is mandatory:

LOAD      → candidate exists
VALIDATE  → candidate is eligible for activation
ACTIVATE  → candidate becomes runtime-visible
3.2. Only Validated Candidates Can Be Activated

The only valid activation source state in v1.0 is:

VALIDATED

The following transition is prohibited:

LOADED ───────X──────> ACTIVE

Activation of a candidate that has not passed validation must fail.

3.3. Active Configuration Is a Separate Concept

A ConfigurationCandidate represents an isolated configuration artifact prepared for possible activation.

An active configuration represents the configuration snapshot currently published to the runtime.

They therefore have different semantics.

Conceptually:

ConfigurationCandidate
        │
        │ activate
        ▼
ActiveConfiguration

Activation must not require converting a candidate into a permanently mutable active object.

4. Configuration Lifecycle

The v1.0 lifecycle is:

LOADED Candidate
       │
       │ validate
       ▼
VALIDATED Candidate
       │
       │ activate
       ▼
ActiveConfiguration

ACTIVE is not a lifecycle state transition of ConfigurationCandidate. Activation produces a separate ActiveConfiguration representing the runtime-visible configuration snapshot.

The following transitions are not part of v1.0:

LOADED  → ACTIVE
ACTIVE  → VALIDATED
ACTIVE  → LOADED
ACTIVE  → ACTIVE

No additional lifecycle states are introduced by this step.

States such as:

DEACTIVATED;
RETIRED;
FAILED;
ROLLED_BACK;

are outside the scope of this model.

5. Active Configuration

The activation boundary introduces the conceptual ActiveConfiguration.

Its minimum model is:

ActiveConfiguration
    identity
    version
    metadata_registry

The active configuration represents the runtime-visible metadata snapshot.

It does not contain configuration definitions.

It does not perform compilation.

It does not perform validation.

It does not load configuration sources.

Its purpose is to provide a stable configuration snapshot to runtime consumers.


The ConfigurationActivator is responsible for activation and publication of the active configuration. RuntimeConfigurationBinding is responsible for exposing the selected ActiveConfiguration to runtime consumers.

6. Ownership of Active Configuration

The v1.0 configuration lifecycle separates activation from runtime ownership.

`ConfigurationActivator` owns the activation transition. Its responsibility is to
validate activation preconditions and produce a new `ActiveConfiguration`
snapshot.

`ConfigurationActivator` does not own the currently active runtime
configuration and does not serve as the runtime source of truth.

`RuntimeConfigurationBinding` owns the currently active runtime configuration.
Its responsibility is to publish an `ActiveConfiguration` as the current
runtime snapshot and to provide that snapshot to runtime consumers.

Therefore:

- `ConfigurationActivator` owns activation;
- `ActiveConfiguration` represents the immutable runtime snapshot;
- `RuntimeConfigurationBinding` owns the current runtime snapshot;
- runtime consumers obtain the current configuration through
  `RuntimeConfigurationBinding`, directly or through runtime resolution
  services.

The system must not maintain two independent sources of truth for the current
runtime configuration.

The following distinction is normative:

    activate()
        = produce an ActiveConfiguration snapshot

    bind()
        = make an ActiveConfiguration snapshot the current runtime configuration

Binding an `ActiveConfiguration` does not constitute another lifecycle
transition of `ConfigurationCandidate` and does not perform activation again.

ConfigurationCandidate
        │
        │ activate
        ▼
ConfigurationActivator
        │
        │ produces
        ▼
ActiveConfiguration
        │
        │ bind
        ▼
RuntimeConfigurationBinding
        │
        │ current snapshot
        ▼
Runtime Consumers

A separate runtime container is not introduced by Step 5.

This keeps the implementation boundary small while preserving the architectural separation required for later runtime integration.

7. Configuration Activator

The activation operation is represented by a dedicated service:

ConfigurationActivator

Its responsibility is limited to configuration publication.

Conceptual API:

class ConfigurationActivator:


    def activate(
        self,
        candidate: ConfigurationCandidate,
    ) -> ActiveConfiguration:
        ...


    def current(self) -> ActiveConfiguration | None:
        ...

The exact implementation API may evolve, but the responsibility boundary is fixed by this document.

8. Activator Responsibilities

The activator is responsible for:

accepting a configuration candidate;
verifying that the candidate is eligible for activation;
creating/publishing the active configuration snapshot;
replacing the previous active configuration;
returning the newly active configuration;
preserving the previous active configuration when activation fails.

The activator is not responsible for:

loading definitions;
compiling metadata;
validating individual definitions;
constructing metadata definitions;
resolving runtime objects;
persistence;
migrations;
rollback;
distributed synchronization.
9. First Activation

The system may initially have no active configuration:

current = None

A validated candidate may then become the first active configuration.

After successful activation:

current = ActiveConfiguration

No previous configuration is required.

10. Configuration Replacement

An existing active configuration may be replaced by another validated candidate.

For example:

Active = Configuration A


Candidate B
    state = VALIDATED

After:

activate(B)

the state becomes conceptually:

Active = Configuration B

Configuration A is no longer the active configuration.

Configuration A itself is not modified as part of the activation operation.

11. Atomic Publication

Activation is a publication operation.

The runtime must never observe a partially activated configuration.

The following intermediate states are prohibited:

partial A + partial B
empty registry
partially compiled registry
partially replaced registry

The required semantic model is:

Active A
   │
   │ atomic publication
   ▼
Active B

The transition must be observable as a single logical replacement.

The exact synchronization mechanism is an implementation concern and is outside the scope of v1.0.

12. Registry Ownership

A configuration candidate owns its metadata registry.

An active configuration owns the metadata registry exposed to runtime consumers.

Activation does not require copying individual metadata objects from one registry into another.

The intended model is:

Candidate
    │
    └── MetadataRegistry
             │
             │ publish
             ▼
ActiveConfiguration
    │
    └── MetadataRegistry

The activation boundary publishes the complete metadata snapshot.

The question of making MetadataRegistry explicitly immutable/frozen is deferred to a later step.

13. Runtime Isolation

Runtime consumers must not depend directly on:

configuration definitions;
configuration loader;
configuration validator;
configuration candidate construction.

The intended dependency direction is:

Configuration
      │
      ▼
ActiveConfiguration
      │
      ▼
Runtime

Runtime resolution therefore operates against the active configuration snapshot.

This preserves the Runtime/Metadata Separation principle.

14. Activation Failure Semantics

Activation failure must not modify the current active configuration.

Given:

Active = A
Candidate B = not eligible

an unsuccessful activation must leave:

Active = A

unchanged.

This rule applies regardless of the reason for activation failure.

15. Invalid Activation

An activation attempt must fail when the candidate is not in the required state.

For example:

Candidate state = LOADED

must not be activatable.

The failure must occur before the current active configuration is replaced.

16. Candidate and Active Configuration Semantics

The distinction is intentional:

Concept	Meaning
ConfigurationCandidate	Isolated configuration prepared for possible activation
ActiveConfiguration	Configuration snapshot currently published to runtime
ConfigurationActivator	Boundary responsible for publication
MetadataRegistry	Collection of compiled metadata
MetadataResolver	Resolves runtime objects against active metadata

A candidate is therefore not the same thing as the active runtime configuration.

17. Version and Identity

ConfigurationIdentity identifies the logical configuration.

ConfigurationVersion identifies its revision.

The active configuration preserves both values:

ActiveConfiguration
    identity
    version
    metadata_registry

Activation does not alter either identity or version.

Version comparison, upgrade compatibility, migration and downgrade rules are outside the scope of Step 5.

18. Scope of v1.0

The following are included:

validated candidate activation;
first activation;
replacement activation;
current active configuration lookup;
activation failure isolation;
active configuration snapshot;
runtime publication boundary.
19. Out of Scope

The following are explicitly deferred:

persistent active configuration;
configuration package format;
database-backed activation;
rollback;
migration;
downgrade;
multi-tenant configuration;
concurrent activation;
distributed activation;
hot reload;
cache invalidation;
configuration dependency graph;
configuration signatures;
cryptographic verification;
immutable/frozen registry implementation;
configuration history storage.
20. Architectural Invariants

The following invariants are mandatory:

Only validated candidates may be activated.
Loading never activates a configuration.
Validation never activates a configuration.
Runtime consumes only the active configuration.
Activation publishes a complete configuration snapshot.
Activation does not expose partial metadata.
Failed activation does not replace the current active configuration.
The previous active configuration is not mutated during replacement.
Active configuration identity and version come from the activated candidate.
Configuration construction and runtime resolution remain separate concerns.

### Runtime Configuration Ownership Invariant

There is exactly one runtime ownership boundary for the current
`ActiveConfiguration`: `RuntimeConfigurationBinding`.

`ConfigurationActivator` may produce `ActiveConfiguration` instances but must
not maintain an independent current-runtime reference that competes with
`RuntimeConfigurationBinding`.

21. Resulting Model

The complete v1.0 model is:

                  Configuration Definitions
                           │
                           ▼
                    Metadata Compiler
                           │
                           ▼
                    ConfigurationLoader
                           │
                           ▼
                    ┌───────────────┐
                    │   Candidate   │
                    │    LOADED     │
                    └───────┬───────┘
                            │
                            ▼
                    ConfigurationValidator
                            │
                            ▼
                    ┌───────────────┐
                    │   Candidate   │
                    │  VALIDATED    │
                    └───────┬───────┘
                            │
                            ▼
                  ConfigurationActivator
                            │
                   atomic publication
                            │
                            ▼
                    ┌───────────────┐
                    │    Active     │
                    │ Configuration │
                    └───────┬───────┘
                            │
                            ▼
                       Runtime
                            │
                            ▼
                    Runtime Resolution
22. Design Decision

Step 5 establishes the following architectural decision:

Configuration activation is an explicit publication boundary between validated configuration candidates and runtime-visible configuration.

The boundary is intentionally minimal.

It provides the foundation for later runtime integration without introducing persistence, migration, rollback, concurrency or distributed configuration concerns prematurely.