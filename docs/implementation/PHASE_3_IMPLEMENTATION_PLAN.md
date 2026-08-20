# Phase 3 Implementation Plan

**Phase:** Phase 3 — Runtime Configuration Consumption & Resolution
**Status:** In Progress
**Baseline:** `95af009`
**Predecessor:** Phase 2 — Metadata Lifecycle / Configuration Loading
**Architecture:** Phase 3 Architectural Definition v1.0

---

## 1. Purpose

This document defines the implementation plan for Phase 3.

Phase 3 extends the completed Phase 2 configuration lifecycle into a
version-consistent runtime configuration consumption and resolution model.

The target runtime flow is:

```text
Candidate
    ↓
Validated Candidate
    ↓
ActiveConfiguration
    ↓
RuntimeConfigurationBinding
    ↓ acquire
RuntimeConfigurationContext
    ↓
MetadataResolver
    ↓
RuntimeResolver
    ↓
Runtime Objects
    ↓
Runtime Consumers

Phase 3 implementation must preserve the architectural boundaries established
by the Phase 3 Architectural Definition.

### Current Implementation Position

Phase 3 implementation is complete through Step 2.

Implemented:

* Step 1 — RuntimeConfigurationContext;
* Step 2 — Configuration Ownership Cleanup.

Quality gates closed:

* P3-QG1 — Context Contract: **CLOSED**;
* P3-QG2 — Ownership: **CLOSED**.

Validation at the Step 2 checkpoint:

* `pytest`: **178 passed**;
* `ruff check .`: **PASS**;
* `black --check .`: **PASS**;
* `mypy src`: **PASS**.

The next implementation step is Step 3 — MetadataResolver. Step 3 has not
yet been implemented.

## 2. Implementation Objectives

Phase 3 implementation shall establish:

explicit runtime configuration snapshot semantics;
RuntimeConfigurationContext;
single runtime ownership through RuntimeConfigurationBinding;
removal of competing current-configuration ownership from
ConfigurationActivator;
configuration-aware metadata resolution;
integration of RuntimeResolver with MetadataResolver;
elimination of direct runtime bypasses to MetadataRegistry;
immutable published configuration semantics;
configuration-consistent Standard Configuration runtime flow;
regression coverage for all Phase 3 architectural invariants.
## 3. Implementation Principles
### 3.1 Preserve Phase 2 Lifecycle


Phase 3 must not redesign:

Candidate
    ↓
Validated Candidate
    ↓
ActiveConfiguration

The existing Phase 2 lifecycle remains authoritative.

### 3.2 One Runtime Owner


The runtime publication owner is:

RuntimeConfigurationBinding

ConfigurationActivator must not maintain a competing current configuration.

### 3.3 Snapshot-Based Runtime Consumption


Runtime consumers do not resolve configuration directly from the mutable
publication point.

Instead:

RuntimeConfigurationBinding
        ↓ acquire
RuntimeConfigurationContext
        ↓
ActiveConfiguration snapshot
### 3.4 Layered Resolution


Metadata resolution and runtime object resolution remain separate:

MetadataResolver
    ↓
metadata


RuntimeResolver
    ↓
runtime object
### 3.5 No Runtime Registry Bypass


Runtime consumers and RuntimeResolver must not directly access
MetadataRegistry.

The registry remains an infrastructure implementation detail.

## 4. Implementation Sequence

Phase 3 is implemented in the following order.

Step 1
RuntimeConfigurationContext
        ↓
Step 2
Configuration ownership cleanup
        ↓
Step 3
MetadataResolver
        ↓
Step 4
RuntimeResolver integration
        ↓
Step 5
Standard Configuration vertical slice
        ↓
Step 6
Published configuration immutability
        ↓
Step 7
Phase 3 audit and quality gate

The sequence is intentional.

Runtime context must exist before runtime resolution is refactored to consume
configuration through it.

## 5. Step 1 — RuntimeConfigurationContext

**Status:** Implemented

**Quality Gate:** P3-QG1 — CLOSED

Objective

Introduce an explicit runtime configuration snapshot.

Target model
RuntimeConfigurationBinding
        │
        │ acquire()
        ▼
RuntimeConfigurationContext
        │
        ▼
ActiveConfiguration
Responsibilities

RuntimeConfigurationContext shall:

represent one active configuration snapshot;
expose configuration identity;
expose configuration version;
provide access to the captured ActiveConfiguration;
remain independent from subsequent changes to the binding.
Non-responsibilities

It shall not:

activate configuration;
validate candidates;
replace the active configuration;
load configuration;
resolve runtime objects;
access physical storage directly.
Required tests

At minimum:

context can be acquired from binding;
context contains the currently published configuration;
context exposes configuration identity;
context exposes configuration version;
replacing the binding does not change an existing context;
a newly acquired context observes the newly published configuration;
context cannot be used to mutate the active configuration.
## 6. Step 2 — Configuration Ownership Cleanup

**Status:** Implemented

**Quality Gate:** P3-QG2 — CLOSED

Objective

Eliminate duplicate current-configuration ownership.

Required result
ConfigurationActivator
    → creates ActiveConfiguration


RuntimeConfigurationBinding
    → owns current published ActiveConfiguration
Required changes

Remove any activator state equivalent to:

_current
current()

when that state represents the currently published runtime configuration.

Tests

Update existing activator tests so that they verify activation rather than
runtime ownership.

Add tests proving that:

activation creates an ActiveConfiguration;
binding owns publication;
activator has no competing runtime current state.
## 7. Step 3 — MetadataResolver

**Status:** Next

**Quality Gate:** P3-QG3 — OPEN

Objective

Introduce an explicit configuration-aware metadata resolution layer.

Target contract
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
Metadata
Responsibilities

MetadataResolver shall:

accept a runtime configuration context;
resolve metadata by logical identity;
resolve only within the context's configuration snapshot;
raise explicit errors when metadata cannot be resolved.
Prohibited behavior

It must not:

select an arbitrary active configuration;
access a global current configuration;
silently fall back to another configuration;
load configuration;
activate configuration.
Tests

At minimum:

metadata is resolved from the supplied context;
resolution uses the context's configuration version;
missing metadata produces an explicit error;
changing the binding does not affect resolution through an existing context.
## 8. Step 4 — RuntimeResolver Integration
Objective

Remove direct runtime dependency on MetadataRegistry.

Current conceptual path
RuntimeResolver
    ↓
MetadataRegistry
Target path
RuntimeResolver
    ↓
MetadataResolver
    ↓
RuntimeConfigurationContext
Responsibilities

RuntimeResolver remains responsible for runtime object materialization.

It does not become responsible for configuration lifecycle or metadata storage.

Tests

Verify:

runtime object resolution uses metadata from the supplied configuration
context;
runtime resolver does not bypass metadata resolution;
configuration replacement does not alter an existing resolution context;
resolution failures remain explicit.
## 9. Step 5 — Standard Configuration Vertical Slice
Objective

Demonstrate the complete Phase 3 architecture through an existing Standard
Configuration runtime object.

Required flow
Standard Definition
        ↓
Compiler
        ↓
Candidate
        ↓
Validation
        ↓
Activation
        ↓
ActiveConfiguration
        ↓
RuntimeConfigurationBinding
        ↓
RuntimeConfigurationContext
        ↓
MetadataResolver
        ↓
RuntimeResolver
        ↓
CatalogRuntime
Acceptance criteria

The vertical slice demonstrates that:

Standard Configuration can become active;
runtime acquires a configuration context;
metadata is resolved through that context;
runtime object resolution uses the resolved metadata;
no runtime consumer directly accesses MetadataRegistry;
configuration replacement preserves existing context consistency.
## 10. Step 6 — Published Configuration Immutability
Objective

Ensure runtime consumers cannot mutate published configuration semantics.

Architectural requirement

Published metadata is immutable from the runtime consumer's perspective.

The exact mechanism remains an implementation decision.

Possible mechanisms:

immutable registry;
read-only view;
immutable mapping;
private publication storage.
Tests

Verify that:

runtime consumers cannot mutate published metadata;
existing contexts remain coherent;
configuration replacement creates a new published state rather than mutating
the previous snapshot.
## 11. Step 7 — Phase 3 Audit

The final audit shall verify:

Architecture
ownership is unambiguous;
context snapshot semantics are correct;
resolution layers are separated;
registry bypasses are removed;
published state is immutable.
Code
pytest
ruff
black
mypy
Documentation

The implementation must match:

PHASE_3_ARCHITECTURAL_DEFINITION.md;
Phase 3 ADRs;
updated Configuration Architecture;
updated Runtime Architecture;
updated Metadata Architecture.
## 12. Quality Gates
Gate P3-QG1 — Context Contract

Required before Step 2.

Criteria:

context exists;
snapshot semantics work;
tests pass.
Gate P3-QG2 — Ownership

Required before Step 3.

Criteria:

activator no longer owns current runtime configuration;
binding is the sole publication owner;
tests pass.
Gate P3-QG3 — Metadata Resolution

Required before Step 4.

Criteria:

metadata resolver exists;
resolution is context-bound;
explicit errors exist;
tests pass.
Gate P3-QG4 — Runtime Resolution

Required before Step 5.

Criteria:

runtime resolver uses metadata resolver;
direct registry bypass is removed;
tests pass.
Gate P3-QG5 — Vertical Slice

Required before Step 6.

Criteria:

Standard Configuration reaches runtime object resolution;
full configuration-aware path is operational;
regression suite passes.
Gate P3-QG6 — Publication Semantics

Required before final audit.

Criteria:

published state is immutable to runtime consumers;
snapshot isolation is verified.
## 13. Review Gates
P3-RG1 — Runtime Context Review

Review:

context ownership;
snapshot semantics;
lifetime;
API minimality.
P3-RG2 — Resolution Boundary Review

Review:

MetadataResolver responsibility;
RuntimeResolver responsibility;
registry isolation;
dependency direction.
P3-RG3 — Vertical Slice Review

Review:

Standard Configuration integration;
end-to-end runtime flow;
architectural bypasses.
P3-RG4 — Final Architectural Review

Review all Phase 3 invariants:

P3-I1  Single Runtime Ownership
P3-I2  Activation Isolation
P3-I3  Snapshot Consistency
P3-I4  Resolution Consistency
P3-I5  Version Isolation
P3-I6  Consumer Isolation
P3-I7  Storage Independence
P3-I8  Layered Resolution
P3-I9  Lifecycle Isolation
P3-I10 Published Snapshot Semantics
P3-I11 Deterministic Resolution
P3-I12 Explicit Failure
## 14. Testing Strategy

Testing shall be layered.

Unit Tests

Test:

context;
binding;
activator;
metadata resolver;
runtime resolver.
Integration Tests

Test:

ActiveConfiguration
    ↓
Binding
    ↓
Context
    ↓
MetadataResolver
    ↓
RuntimeResolver
Vertical Slice Tests

Test Standard Configuration runtime resolution.

Regression Tests

The complete existing suite must remain green.

No Phase 3 implementation may weaken existing Phase 1 or Phase 2 contracts.

## 15. Expected Module Evolution

The exact file structure shall be determined from the existing repository before
implementation.

The expected conceptual modules are:

configuration/
    identity.py
    lifecycle.py
    candidate.py
    loader.py
    runtime_binding.py
    context.py


runtime/
    resolver.py
    ...


metadata/
    resolver.py
    ...

Existing modules should be reused where their current responsibility already
matches the Phase 3 contract.

New modules must not be introduced merely to rename existing responsibilities.

## 16. Compatibility Requirements

Phase 3 must preserve:

existing identifiers;
ActiveConfiguration;
existing candidate lifecycle;
existing metadata definitions;
existing compiler behavior;
existing runtime object contracts;
Standard Configuration bootstrap semantics.

Breaking changes are permitted only where they are required to enforce the
Phase 3 architectural boundary.

## 17. Documentation Requirements

During implementation:

implementation decisions must remain consistent with the Phase 3 ADRs;
implementation-specific details must not be promoted to architecture without
architectural review;
Phase 2 documents must remain historical rather than being repurposed.

At completion:

implementation documentation reflects the final code;
architecture documentation remains implementation-independent;
ADRs record all architectural decisions that changed during implementation.
## 18. Completion Definition

Phase 3 is complete when:

RuntimeConfigurationContext exists;
binding snapshot semantics are implemented;
activator has no competing runtime ownership;
MetadataResolver is configuration-aware;
RuntimeResolver uses the configuration-aware resolution path;
direct runtime registry bypasses are removed;
Standard Configuration vertical slice passes;
published configuration is immutable from runtime consumers;
all Phase 3 tests pass;
ruff, black, and mypy pass;
all Phase 3 architectural invariants pass;
Phase 3 Architectural Review Gate is closed.
## 19. Final Target Architecture
                    Phase 2
                      │
                      ▼
              ActiveConfiguration
                      │
                      │ publish
                      ▼
          RuntimeConfigurationBinding
                      │
                      │ acquire
                      ▼
          RuntimeConfigurationContext
                      │
                      ▼
               MetadataResolver
                      │
                      ▼
                RuntimeResolver
                      │
                      ▼
               Runtime Objects
                      │
                      ▼
              Runtime Consumers

The central invariant is:

Runtime consumers resolve configuration through a single, version-consistent
runtime configuration context and never bypass the configuration consumption
boundary.