# Phase 7 — Step 7

# WP-4 — Operation Domain Completion

**Status:** Final — Reconciled with implemented WP-4–WP-8 state
**Phase:** Phase 7 — Register Engine
**Step:** Step 7 — Platform Implementation
**Work Package:** WP-4 — Operation Domain Completion
**Depends on:** Phase 7 Steps 1–6.3 and Step 7 existing architecture
**Document Type:** Architecture Definition

---

# 1. Purpose

WP-4 completes the Register Operation Domain introduced during Phase 7 Step 7.

The purpose of WP-4 is to establish **one Register-scoped serialization boundary** for all consistency-sensitive operations that may affect the relationship between authoritative Movement Facts and derived Totals state.

The required operation classes are:

```text
mutation
rebuild
recovery
```

The architectural objective is:

> For a given Register, all consistency-sensitive operations MUST execute within one shared logical Operation Domain, while different Registers MUST remain independently executable.

WP-4 does not introduce new Register business semantics.

It completes the execution boundary required to enforce the semantics already established by Steps 6–6.3.

---

# 2. Architectural Problem

The current implementation already contains a `RegisterOperationDomain` and a `RegisterOperationDomainRegistry`.

The mutation orchestration path uses this domain:

```text
RegisterMutationOrchestrator
        │
        ▼
RegisterOperationDomain
        │
        ├── establish
        ├── remove
        ├── rebuild
        └── recover
```

The implemented `DefaultTotalsMaintenanceCoordinator` does not own a second per-Register operation lock. Its internal synchronization protects coordinator-owned runtime state only; Register-scoped operation serialization is provided by `RegisterOperationDomain`.

Conceptually, the current structure can therefore become:

```text
                 Register A
                    │
          ┌─────────┴─────────┐
          │                   │
 Operation Domain       Maintenance Coordinator
      lock                     lock
          │                   │
          └─────────┬─────────┘
                    │
                  Totals
```

This creates two distinct serialization mechanisms for the same Register.

Although both mechanisms may individually provide mutual exclusion, they do not represent the same architectural boundary.

The result is an undesirable split between:

```text
logical Register operation serialization
```

and:

```text
Totals maintenance serialization
```

WP-4 removes that split.

---

# 3. Target Architectural State

The target architecture is:

```text
                         Register A
                            │
                 RegisterOperationDomain
                            │
              ┌─────────────┼─────────────┐
              │             │             │
          mutation        rebuild      recovery
              │             │             │
              └─────────────┼─────────────┘
                            │
             TotalsMaintenanceCoordinator
                            │
                     semantic state
                            │
                       Totals Engine
```

For another Register:

```text
                         Register B
                            │
                 RegisterOperationDomain
                            │
              ┌─────────────┼─────────────┐
              │             │             │
          mutation        rebuild      recovery
```

The two domains are independent:

```text
Register A domain  ≠  Register B domain
```

and therefore:

```text
Register A operation
        ║
        ║ does not serialize with
        ▼
Register B operation
```

---

# 4. Core Architectural Invariant

For every Register identity `R`:

> There MUST be exactly one logical Register Operation Domain governing consistency-sensitive operations for `R`.

The domain is responsible for:

* serialization;
* operation admission coordination;
* Register-scoped mutual exclusion.

The domain is **not** responsible for:

* Totals semantic state;
* lifecycle state ownership;
* consistency state ownership;
* authoritative Movement Facts;
* derived Totals;
* persistence.

---

# 5. Ownership Model

WP-4 establishes explicit ownership boundaries.

## 5.1 RegisterOperationDomain

`RegisterOperationDomain` owns:

```text
Register-scoped execution serialization
```

It answers:

> May another consistency-sensitive operation for this Register execute concurrently?

It does not answer:

> What is the semantic state of this Register?

---

## 5.2 RegisterOperationDomainRegistry

`RegisterOperationDomainRegistry` owns:

```text
Register identity → RegisterOperationDomain
```

Its purpose is to guarantee stable domain identity for a Register within the composition boundary.

Conceptually:

```text
Registry
   │
   ├── Register A → Domain A
   ├── Register B → Domain B
   └── Register C → Domain C
```

Repeated resolution of the same Register MUST return the same logical domain.

Different Registers MUST resolve to different domains.

---

## 5.3 TotalsMaintenanceCoordinator

`TotalsMaintenanceCoordinator` remains the **single semantic state owner**.

It owns:

```text
TotalsMaintenanceState
```

including:

```text
lifecycle
consistency
```

and any internal semantic bookkeeping required to maintain Totals correctness.

The coordinator does not own Register-scoped operation serialization.

In particular, its semantic responsibility MUST NOT be expanded to include a competing per-Register operation lock.

---

# 6. Single Serialization Boundary

All consistency-sensitive operations MUST enter the same Register Operation Domain.

The target model is:

```text
                RegisterOperationDomain
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
       mutation        rebuild        recovery
          │              │              │
          └──────────────┼──────────────┘
                         ▼
             TotalsMaintenanceCoordinator
```

This means that the following pairs MUST be mutually exclusive for the same Register:

```text
mutation ↔ mutation
mutation ↔ rebuild
mutation ↔ recovery
rebuild  ↔ rebuild
rebuild  ↔ recovery
recovery ↔ recovery
```

The exact scheduling order remains an implementation concern.

The architectural requirement is only that overlapping consistency-sensitive operations for the same Register cannot execute concurrently.

---

# 7. Different Register Isolation

Serialization is Register-scoped, not globally scoped.

Therefore:

```text
Register A
    mutation
       │
       │ may execute concurrently with
       ▼
Register B
    rebuild
```

provided that both operations use independent Register Operation Domains.

The architecture MUST NOT introduce a single global lock that serializes all Registers.

Such a mechanism would violate the intended Register isolation model.

---

# 8. Mutation Domain

Ordinary Movement mutation remains under the Operation Domain.

The conceptual flow is:

```text
Movement input
      │
      ▼
generic validation
      │
      ▼
Register Operation Domain
      │
      ├── mutation admission
      │
      ├── authoritative persistence
      │
      └── Totals maintenance
```

The Operation Domain surrounds the consistency-sensitive portion of the mutation.

Validation that can safely occur before domain admission MAY remain outside the domain.

The architectural requirement is that authoritative persistence and corresponding Totals maintenance participate in the same Register-scoped serialization boundary.

---

# 9. Rebuild Domain

Rebuild is a consistency-sensitive operation.

Its conceptual flow is:

```text
Register Operation Domain
        │
        ▼
TotalsMaintenanceCoordinator
        │
        ▼
authoritative Movement Facts
        │
        ▼
Totals Engine rebuild
        │
        ▼
new derived Totals state
```

A rebuild for Register `R` MUST serialize with mutation and recovery for `R`.

A rebuild MUST NOT rely on a separate maintenance-specific lock to establish that serialization.

The Operation Domain is the authoritative serialization boundary.

---

# 10. Recovery Domain

Recovery is also a consistency-sensitive operation.

Recovery may be implemented through rebuild semantics where that is already established by the Step 6 contract.

Conceptually:

```text
Register Operation Domain
        │
        ▼
Recovery
        │
        ▼
re-establish derived Totals
        │
        ▼
valid or explicitly recoverable state
```

Recovery MUST use the same Register Operation Domain as mutation and rebuild.

Recovery MUST NOT establish an independent serialization boundary.

---

# 11. Semantic State Ownership

WP-4 does not change the state ownership established by Step 6.

The following remains true:

```text
TotalsMaintenanceCoordinator
        │
        └── TotalsMaintenanceState
```

The Operation Domain MUST NOT introduce a second semantic representation such as:

```text
OperationDomainState
    lifecycle
    consistency
```

that competes with:

```text
TotalsMaintenanceState
```

The Operation Domain may coordinate execution based on established admission rules, but the semantic truth remains owned by `TotalsMaintenanceCoordinator`.

---

# 12. Relationship Between Serialization and State

Serialization and semantic state are deliberately separate concerns.

```text
Operation Domain
    = "who may execute now?"

Maintenance Coordinator
    = "what is the semantic state?"
```

This distinction is fundamental.

A Register may be:

```text
ACTIVE / VALID
```

while an operation is currently executing.

The existence of an operation lock does not itself represent a lifecycle state.

Likewise:

```text
RECOVERY_REQUIRED
```

is semantic state owned by the maintenance coordinator and is not an Operation Domain state.

---

# 13. No Nested Competing Serialization

WP-4 MUST eliminate the architecture in which:

```text
Operation Domain lock
        ↓
Maintenance Coordinator lock
```

represents two independent Register-scoped serialization mechanisms.

The desired structure is:

```text
Operation Domain
        │
        ▼
Maintenance Coordinator
```

with the coordinator performing semantic state transitions and Totals operations without introducing another competing Register operation boundary.

This does not prohibit internal synchronization required for purely local implementation safety where such synchronization does not establish an alternative Register operation domain.

However, no internal synchronization mechanism may become a second semantic serialization boundary for Register operations.

---

# 14. Composition Requirement

The Operation Domain must be shared by all relevant platform components.

The composition boundary is conceptually:

```text
                 RegisterOperationDomainRegistry
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
      RegisterMutationOrchestrator   Totals maintenance
                 │                         │
                 └────────────┬────────────┘
                              ▼
                    same Register Domain
```

For a given Register identity, mutation, rebuild, and recovery MUST resolve to the same logical domain.

It is insufficient for the components merely to contain independently equivalent locking implementations.

There must be one shared logical domain.

---

# 15. Operation Domain Does Not Own Persistence

The Operation Domain does not become a persistence abstraction.

Persistence remains owned by:

```text
RegisterFactPersistence
```

The Operation Domain only determines when consistency-sensitive access may execute.

Therefore:

```text
Operation Domain
       │
       ├── coordinates
       │
       ▼
RegisterFactPersistence
```

rather than:

```text
Operation Domain
       └── persistence implementation
```

---

# 16. Operation Domain Does Not Own Totals

Likewise, the Operation Domain does not become a Totals abstraction.

Totals semantics remain owned by:

```text
TotalsEngine
```

and maintenance semantics remain owned by:

```text
TotalsMaintenanceCoordinator
```

The Operation Domain only provides the execution boundary in which those components participate.

All state-changing actions that participate in a Register mutation and must remain consistent with authoritative Movement Facts and derived Totals are executed within the same Register Operation Domain. Preliminary validation that does not mutate state may execute outside the domain.

---

# 17. Failure Semantics

WP-4 does not change the failure semantics established by Step 6 / Step 6.3.

If an operation produces:

```text
SUCCESS
```

the resulting semantic state MUST be reported according to the existing maintenance contract.

If an operation produces:

```text
FAILURE
```

or:

```text
INDETERMINATE
```

the existing lifecycle and consistency semantics remain authoritative.

Serialization MUST NOT convert:

```text
failure
```

into:

```text
success
```

or hide:

```text
recovery_required
```

state.

The Operation Domain is an execution boundary, not a failure-state authority.

---

# 18. Determinism

For identical authoritative Movement Facts and identical Register configuration:

```text
rebuild(R)
```

must remain deterministic according to the established Totals contract.

WP-4 must not introduce:

* timing-dependent semantic state;
* ordering based on lock acquisition;
* nondeterministic Totals state;
* dependence on which concurrent operation happened to acquire a lock first beyond the already-defined operation semantics.

Serialization determines execution order.

It does not redefine Totals semantics.

---

# 19. Concurrency Model

The target concurrency model is:

```text
                 Register A
                     │
                  Domain A
                 /       \
           mutation      rebuild
              │              │
              └── serialized┘


                 Register B
                     │
                  Domain B
                 /       \
           mutation      rebuild
              │              │
              └── serialized┘
```

Across Registers:

```text
Domain A  ║  Domain B
```

may execute concurrently.

Within one Register:

```text
Domain A
    mutation
       ║
    rebuild
       ║
    recovery
```

is serialized.

---

# 20. Architectural Non-Goals

WP-4 MUST NOT:

1. redesign Totals semantics;
2. redesign Movement persistence;
3. introduce Inventory-specific behavior;
4. introduce a global Register lock;
5. move semantic state ownership into `RegisterOperationDomain`;
6. introduce a second lifecycle state model;
7. introduce a second consistency state model;
8. change the established failure taxonomy;
9. make `recovery` a new Totals aggregation operation;
10. make Operation Domain responsible for persistence;
11. make Operation Domain responsible for Totals calculation;
12. introduce speculative transaction infrastructure.

---

# 21. Required Architectural Invariants

The implementation is architecturally compliant only if all of the following are true.

### Invariant A — One domain per Register

For a given Register identity:

```text
resolve(R) is stable
```

and all consistency-sensitive operations use that logical domain.

### Invariant B — Different Registers are isolated

```text
resolve(A) is not resolve(B)
```

for distinct Register identities.

### Invariant C — Mutation uses the domain

Authoritative mutation and corresponding Totals maintenance execute under the Register Operation Domain.

### Invariant D — Rebuild uses the same domain

Rebuild for Register `R` uses the same domain as mutation for `R`.

### Invariant E — Recovery uses the same domain

Recovery for Register `R` uses the same domain as mutation and rebuild for `R`.

### Invariant F — No competing maintenance lock

`TotalsMaintenanceCoordinator` does not establish an independent per-Register operation serialization boundary.

### Invariant G — Single semantic state owner

`TotalsMaintenanceCoordinator` remains the only owner of Totals maintenance lifecycle and consistency state.

### Invariant H — Register-scoped serialization

Operations for Register A do not unnecessarily serialize operations for Register B.

### Invariant I — Failure semantics preserved

Existing Step 6 / Step 6.3 failure and recovery semantics remain unchanged.

### Invariant J — Totals remain derived

Rebuild and recovery continue to derive Totals from authoritative Movement Facts.

### Invariant K - Operation Domain ownership is structural, not merely behavioral.

All Register-scoped consistency-sensitive operations must obtain their domain from the same RegisterOperationDomainRegistry composition boundary. Independent per-component locks, even if they serialize the same Register identity, do not satisfy the architecture.

---

# 22. Integration Boundary

The final platform composition should be understood as:

```text
                    Register Operation Domain
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
         mutation          rebuild          recovery
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
              TotalsMaintenanceCoordinator
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             Movement Facts        Totals Engine
                    │                   │
                    └─────────┬─────────┘
                              ▼
                           Totals
                              │
                              ▼
                       Balance / Query
```

This diagram describes responsibility and serialization, not a requirement that all calls pass through one concrete class.

---

# 23. Expected Result

After WP-4, the Register Platform must have one clear answer to the question:

> **What serializes consistency-sensitive operations for a Register?**

The answer is:

```text
RegisterOperationDomain
```

and one clear answer to:

> **Who owns the semantic lifecycle and consistency state of Totals?**

The answer remains:

```text
TotalsMaintenanceCoordinator
```

These responsibilities must not overlap.

---

# 24. Historical Architecture Review Decision

Before implementation, architecture review should confirm:

1. `RegisterOperationDomain` is the sole Register-scoped serialization boundary;
2. `RegisterOperationDomainRegistry` is the shared composition boundary;
3. `mutation`, `rebuild`, and `recovery` belong to the same logical domain;
4. `TotalsMaintenanceCoordinator` remains the sole semantic state owner;
5. its existing per-Register operation lock is removed or otherwise eliminated as a competing boundary;
6. different Registers remain independently serializable;
7. no new semantic behavior is introduced by WP-4.

Only after these points are approved should WP-4 Concrete API Design and implementation begin.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
