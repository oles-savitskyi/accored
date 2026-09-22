# Phase 7 — Step 7

# Platform Implementation — Architecture Definition

**Status:** Final — Reconciled with implemented WP-4–WP-8 state
**Phase:** 7 — Register Query & Totals
**Step:** 7 — Platform Implementation
**Previous Steps:** Steps 1–6.3 — Register Storage, Movement Query, Totals, Balance Query, Lifecycle / Maintenance, Mutation / Totals Consistency Boundary
**Next Step:** Step 8 — Inventory Register Completion
**Document Type:** Architecture Definition

---

## 1. Purpose

Step 7 implements the Register Platform contracts established by Phase 7 Steps 2–6.3 and integrates their concrete implementations into one coherent platform boundary.

The architectural objective is:

> **Implement the platform contracts without introducing Standard Configuration-specific logic into the Register Engine.**

Step 7 is therefore an implementation and composition step, not a new Register semantics step.

The contracts defining Register storage, movement query, Totals, Balance Query, lifecycle / maintenance, and the Register Mutation / Totals Consistency Boundary are already established by the preceding steps. Step 7 must make those contracts operational as one platform capability.

The result must be a reusable Register Platform that can support the Inventory Register in Step 8 without embedding Inventory-specific concepts into `accore.platform.registers`.

---

# 2. Architectural Context

Phase 6 established the Posting side of the operational flow:

```text
Business Document
      ↓
Posting
      ↓
MovementSet
      ↓
Movement Validation
      ↓
Register Posting Contract
```

Phase 7 establishes what the Register Platform does with accepted Movement Facts:

```text
Accepted Movement
      ↓
Movement Persistence
      ↓
Movement Query
      ↓
Totals Maintenance
      ↓
Balance Query
```

The complete platform boundary is:

```text
                         Posting Platform
                               │
                               │ accepted MovementSet
                               ▼
                    ┌────────────────────────┐
                    │   Register Platform    │
                    │                        │
                    │ Validation             │
                    │ Mutation               │
                    │ Persistence            │
                    │ Movement Query         │
                    │ Totals                 │
                    │ Balance                │
                    │ Lifecycle / Recovery   │
                    └───────────┬────────────┘
                                │
                                │ generic Register contracts
                                ▼
                    ┌────────────────────────┐
                    │ Standard Configuration │
                    │                        │
                    │ Inventory Register     │
                    └────────────────────────┘
```

The Register Platform owns generic register behavior.

Standard Configuration owns the concrete definition and business meaning of a particular Register.

---

# 3. Step 7 Objective

Step 7 must achieve the following architectural state:

```text
Step 2 contract
       ↓
Step 3 contract
       ↓
Step 4 contract
       ↓
Step 5 contract
       ↓
Step 6 contract
       ↓
Step 6.3 consistency boundary
       ↓
--------------------------------
      Step 7
--------------------------------
       ↓
Coherent Register Platform
```

The implementation must provide:

1. concrete platform implementations for the established contracts;
2. correct composition of those implementations;
3. one authoritative mutation boundary;
4. one Register-scoped operation domain for consistency-sensitive operations;
5. storage-provider independence;
6. Standard Configuration independence;
7. the public Register API established by the preceding contracts;
8. sufficient unit and integration coverage to demonstrate the architectural invariants.

Step 7 does not introduce a new business-level Register type or a new Inventory implementation.

---

# 4. Scope

## 4.1 In Scope

Step 7 includes:

* implementation of established Register platform contracts;
* integration of Movement validation with Register mutation;
* integration with the existing `RegisterFactPersistence` boundary;
* movement query implementation and composition;
* Totals Engine implementation and composition;
* Balance Query implementation and composition;
* Totals lifecycle and maintenance implementation;
* Register Mutation orchestration;
* Register Operation Domain integration;
* failure and indeterminate-result propagation;
* lifecycle / consistency state enforcement;
* public Register platform API;
* platform-level integration tests;
* verification that Register Platform code remains independent of Standard Configuration.

## 4.2 Out of Scope

Step 7 does not introduce or redefine:

* Inventory Register semantics;
* Product semantics;
* Warehouse semantics;
* Quantity semantics specific to Inventory;
* Goods Receipt posting semantics;
* Posting Handler semantics;
* Posting Context semantics;
* new Posting lifecycle behavior;
* new Movement semantics;
* new TotalsKey semantics;
* new Balance Query semantics;
* accounting valuation or costing;
* period closing;
* General Ledger;
* cross-register distributed transactions;
* a new persistence architecture;
* a new storage provider;
* historical balance reconstruction;
* reporting architecture;
* asynchronous maintenance architecture.

Those concerns remain owned by the earlier phase/step or by later Phase 7 steps.

---

# 5. Relationship to Previous Steps

Step 7 must preserve the ownership established by Steps 2–6.3.

| Capability | Established by | Step 7 responsibility |
|---|---|---|
| Register fact persistence | Step 2 / Phase 5 persistence boundary | integrate existing contract |
| Movement query | Step 3 | implement and compose |
| Totals aggregation | Step 4 | implement and compose |
| Balance Query | Step 5 | implement and compose |
| Totals lifecycle / maintenance | Step 6 | implement and compose |
| Movement/Totals consistency | Step 6.3 | enforce through common operation boundary |
| Inventory definition | Step 8 | **not implemented in Step 7** |
| Goods Receipt → Inventory vertical slice | Step 9 | **not implemented in Step 7** |

Step 7 therefore must not reopen the semantic contracts unless implementation analysis discovers a direct contradiction between a concrete implementation and an already approved contract.

Such a contradiction is an Architecture Review issue, not an invitation to silently change the contract in code.

---

# 6. Platform Component Model

The target platform composition is:

```text
                         Register Platform

 ┌───────────────────────────────────────────────────────────┐
 │                                                           │
 │  Register Mutation Boundary                               │
 │        │                                                  │
 │        ├───────────────┐                                  │
 │        ▼               ▼                                  │
 │  Movement Fact     Totals Maintenance                     │
 │  Persistence            │                                 │
 │        │                ▼                                 │
 │        │          Totals Engine                           │
 │        │                │                                 │
 │        ▼                ▼                                 │
 │  Movement Query    Published Totals                       │
 │                         │                                 │
 │                         ▼                                 │
 │                   Balance Query                           │
 │                                                           │
 │  Register Operation Domain surrounds all                  │
 │  consistency-sensitive mutation / rebuild operations.     │
 │                                                           │
 └───────────────────────────────────────────────────────────┘
```

The exact concrete class graph is defined in the Concrete API Design document and implementation work. This architecture document defines the responsibility graph, not Python signatures.

## Register Operation Domain as the Shared Consistency Boundary

`RegisterOperationDomain` is not a downstream component of `RegisterMutationOrchestrator`.

It is the shared consistency boundary within which all consistency-sensitive Register operations execute.

Conceptually:

```text
Register Operation Domain
  ├── ordinary mutation
  │     └── RegisterMutationOrchestrator
  ├── rebuild
  └── recovery
```

The `RegisterMutationOrchestrator` remains the single orchestration boundary for ordinary Movement mutation. Rebuild and recovery are distinct operation classes and do not have to be routed through the mutation orchestrator's method-level API.

The Operation Domain provides the common serialization, lifecycle/consistency enforcement, and failure-state boundary required by all three operation classes.

---

# 7. Responsibility Boundaries

## 7.1 Movement

`Movement` remains the authoritative register fact representation established earlier in Phase 7.

Step 7 must not make Movement mutable for maintenance convenience.

Changes in accounting effect are represented by explicit mutation operations rather than in-place modification of an accepted fact.

---

## 7.2 Movement Validation

Movement validation remains a platform responsibility.

The validator must enforce generic Register invariants only.

Validation must not contain Standard Configuration business rules such as:

```text
Product must exist
Warehouse must exist
Quantity must be positive for Inventory
```

unless such rules are explicitly part of a generic Register contract.

Register-specific business validation belongs to the Register Posting Contract supplied by configuration.

---

## 7.3 Movement Persistence

The Register Platform consumes the existing `RegisterFactPersistence` boundary.

The Register Engine must not know:

* SQL;
* table names;
* filesystem paths;
* database sessions;
* storage provider classes;
* provider-specific transactions;
* serialization formats.

Persistence remains the owner of authoritative Movement Fact durability.

Step 7 must not create a parallel Movement persistence abstraction merely to simplify implementation.

---

## 7.4 Movement Query

Movement Query is a read-side Register Platform capability.

It consumes persisted Movement Facts through the semantic persistence boundary and exposes the query semantics defined in Step 3.

Query implementation must remain independent of:

* Inventory-specific dimension names;
* storage layout;
* SQL query syntax;
* provider-specific filtering mechanisms.

---

## 7.5 Totals Engine

The Totals Engine owns generic aggregation semantics established by Step 4.

It must operate from Register definitions and Movement data rather than hard-coded business concepts.

The engine must not contain logic equivalent to:

```python
if register == inventory_register:
    ...
```

or special handling for:

```text
product
warehouse
quantity
```

unless those names are supplied as configuration data to a generic engine.

---

## 7.6 Totals Maintenance

The Totals Maintenance boundary owns:

* lifecycle state;
* consistency state;
* incremental application/removal;
* rebuild;
* recovery;
* maintenance outcomes;
* semantic publication state.

It does not become the owner of Movement persistence.

It consumes authoritative Movement Facts for rebuild and coordinates the Totals Engine for derived-state maintenance.

---

## 7.7 Balance Query

Balance Query remains a read-side consumer of the published Totals state.

It must not:

* mutate Movement Facts;
* repair Totals;
* perform hidden rebuilds;
* infer consistency by inspecting unrelated state;
* bypass lifecycle / consistency rules.

A Balance Query must observe only a state that is semantically published as readable according to the Step 5 and Step 6 contracts.

---

# 8. Register Mutation Boundary

Step 7 must establish the `RegisterMutationOrchestrator` as the platform-level orchestration boundary for mutations that affect both:

```text
Authoritative Movement Facts
            +
Derived Totals
```

The conceptual operation is:

```text
Register Mutation
      │
      ▼
Register Operation Domain
      │
      ├── validate / accept Movement
      │
      ├── persist authoritative Movement Fact
      │
      └── maintain derived Totals
```

The precise ordering and failure semantics are inherited from Step 6.3 and must not be changed implicitly by implementation.

The important architectural rule is:

> No other component may independently mutate Movement persistence and Totals in a way that bypasses the shared Register Operation Domain.

---

# 9. Register Operation Domain

The Register Operation Domain is the common consistency boundary established by Step 6.3.

For a Register identity `R`, operations affecting the Movement/Totals relationship must execute within the same logical domain:

```text
Register R
   │
   ▼
RegisterOperationDomain(R)
   │
   ├── Movement mutation
   ├── Totals maintenance
   ├── Totals rebuild
   └── Totals recovery
```

Different Registers remain independently operable:

```text
Register A → Domain A
Register B → Domain B
```

Step 7 must ensure that the concrete implementation does not accidentally create separate, incompatible synchronization mechanisms for the same Register.

In particular, an implementation must not rely on:

```text
Mutation lock A
+
Maintenance lock B
```

when the architecture requires one shared Register-scoped operation boundary.

The existing process-local `RegisterOperationDomain` implementation is therefore treated as the current implementation baseline, while Step 7 must verify that all consistency-sensitive operations actually use it as their common boundary.

The domain is an orchestration/synchronization concept. It is not a distributed transaction manager and does not provide cross-process atomicity.

---

# 10. Authoritative and Derived State

The Step 7 implementation must preserve the following hierarchy:

```text
              AUTHORITATIVE
                    │
                    ▼
        Persisted Movement Facts
                    │
                    ▼
               Totals Engine
                    │
                    ▼
             Derived Totals
                    │
                    ▼
             Balance Query
```

The invariant is:

```text
Totals = Aggregate(Persisted Movement Facts)
```

A successful rebuild must therefore construct a fresh derived state from authoritative Movement Facts.

The implementation must never treat an old Totals representation as authoritative input to rebuild.

---

# 11. Lifecycle and Consistency Enforcement

## Authoritative Lifecycle and Consistency State Ownership

The platform composition must have **one authoritative semantic Register lifecycle/consistency state**.

The lifecycle states are:

* `CREATED`
* `ACTIVE`
* `MAINTENANCE`

The consistency states are:

* `VALID`
* `INDETERMINATE`
* `RECOVERY_REQUIRED`

Individual platform components may observe, validate, or participate in state transitions, but they must not maintain independent semantic copies of the Register state that can diverge.

In particular:

* `RegisterMutationOrchestrator` does not own an independent lifecycle/consistency state;
* `TotalsMaintenanceCoordinator` does not own an independent semantic consistency state;
* `RegisterOperationDomain` does not create a competing semantic state model.

The platform composition therefore has one authoritative state model, while individual components expose the behavior required to enforce or observe that model.

This invariant prevents inconsistent interpretations of Register availability and guarantees that mutation, rebuild, recovery, and query behavior operate against the same semantic lifecycle/consistency state.

Step 7 must make the Step 6 lifecycle and consistency states observable and enforceable at the platform boundary.

The implementation must distinguish at minimum:

```text
Lifecycle:
    CREATED
    ACTIVE
    MAINTENANCE

Consistency:
    VALID
    INDETERMINATE
    RECOVERY_REQUIRED
```

The following semantic rule is mandatory:

> A successful operation may publish a state as `ACTIVE / VALID` only after the operation's logical completion has been established.

A failed or indeterminate operation must not silently return the Register to `ACTIVE / VALID`.

Where the outcome is indeterminate, the platform must preserve the Step 6 recovery semantics rather than guessing whether the derived state is correct.

---

# 12. Failure and Indeterminate Semantics

Step 7 must preserve the distinction between:

```text
FAILURE
```

and:

```text
INDETERMINATE
```

A known operation failure means the implementation knows that the requested operation did not complete successfully.

An indeterminate outcome means the implementation cannot establish the final semantic state with sufficient certainty.

The latter must not be converted into ordinary success merely because an exception was caught.

The platform must preserve `RECOVERY_REQUIRED` where established by Step 6.

Recovery must use authoritative Movement Facts and the existing rebuild semantics.

---

# 13. Mutation Ordering

Step 7 must implement the mutation ordering defined by the consistency contract.

For an accepted Movement mutation, the architecture distinguishes:

```text
Authoritative Movement mutation
        ↓
Derived Totals maintenance
        ↓
Successful semantic completion
```

The implementation must not publish an operation as successfully completed merely because one component completed while the other failed.

If authoritative persistence succeeds but Totals maintenance cannot be established as successful, the platform must expose the appropriate failure / recovery semantics defined by Step 6.3.

It must not silently pretend that the two states are synchronized.

---

# 14. Rebuild Semantics

## Rebuild Source of Truth

Rebuild reconstructs derived Totals exclusively from authoritative Movement Facts.

The rebuild boundary is:

```text
RegisterFactPersistence
        │
        │ authoritative Movement Facts only
        ▼
Fresh Totals construction
        │
        ▼
Semantic publication
```

`RegisterFactPersistence.enumerate(register)` returns authoritative Movement Facts only.

It must not return:

* persisted aggregate Totals as an input to reconstruction;
* storage-provider-specific representations;
* provider-specific metadata required to interpret Movement semantics;
* previously calculated derived state.

Movement Facts remain the sole source of truth for rebuilding Totals.

Therefore, successful rebuild does not depend on the previous Totals state and does not use previous derived state as an input to reconstruction.


Rebuild must:

1. execute inside the Register Operation Domain;
2. obtain authoritative Movement Facts through the persistence boundary;
3. construct replacement derived state independently of the previous Totals state;
4. avoid partial publication of the replacement state;
5. publish the replacement only after successful logical completion;
6. mark the Register as requiring recovery if the outcome cannot be established.

The previous Totals state is not an authoritative input to rebuild.

---

# 15. Storage Provider Independence

The Register Platform depends only on semantic persistence contracts.

The implementation must remain valid when the underlying provider changes between:

```text
In-memory
Filesystem
Database
Other provider
```

provided that the provider satisfies the existing persistence contract.

No Register component may branch on provider type.

---

# 16. Standard Configuration Boundary

The most important Step 7 architectural boundary is:

```text
src/accore/platform/registers/
        ↓
Generic Register Platform

src/standard/
        ↓
Concrete Register configuration
```

### Register Definition Ownership

Register Definition is a semantic input to the generic Register Platform.

Ownership is divided as follows:

```text
Register Definition
  owned semantically by Standard Configuration
  supplied to Register Platform
  consumed/interpreted by generic Register Engine
  persisted Movement Facts managed by Register Platform
```

Standard Configuration owns the semantic definition and business meaning of a concrete Register.

The Register Platform does not create, own, or redefine the business meaning of a Register. It consumes the supplied Register Definition through the established generic contracts.

The generic Register Engine may interpret Register Definition fields required by generic platform behavior, but must not contain Standard Configuration-specific knowledge.

This boundary is required for Step 8, where Inventory Register semantics will be supplied by Standard Configuration without modifying the generic Register Engine.

The platform may consume configuration such as:

```text
Register identity
Dimension definitions
Resource definitions
Movement type semantics
Register Posting Contract
```

It must not contain concrete Standard Configuration knowledge.

### Forbidden examples

```python
from standard import InventoryRegister
```

```python
if register_identity == INVENTORY_REGISTER_ID:
    ...
```

```python
if "quantity" in movement.resources:
    ...
```

when the behavior is intended specifically for Inventory.

### Allowed model

```text
Standard Configuration
        ↓
Register Definition
        ↓
Generic Register Engine
```

This allows Inventory to configure generic Register behavior without becoming a dependency of the platform implementation.

---

# 17. Dependency Direction

The following diagram describes **code dependency / import direction**. An arrow means that the component on the left may depend on or import contracts exposed by the component on the right.

```text
Standard Configuration
        │
        ▼
Register Platform
        │
        ▼
Persistence Abstraction
        │
        ▼
Storage Provider
```

In particular:

* Standard Configuration may depend on the Register Platform;
* Register Platform may depend on persistence abstractions;
* persistence abstractions may be implemented by storage providers;
* Register Platform must not import Standard Configuration;
* Register Platform must not import a concrete storage provider;
* generic Register components must not contain Standard Configuration-specific business semantics.

This diagram describes source-code dependency direction only. It must not be interpreted as a statement about runtime call order, data flow, or transaction ownership.

At runtime, concrete Standard Configuration definitions and concrete persistence implementations may be supplied to the platform through the established contracts and composition boundaries.


The dependency must never become:

```text
Register Platform
       ↓
Standard Configuration
```

or:

```text
Persistence
       ↓
Standard Configuration
```

The Register Platform may be imported by Standard Configuration. It must not import Standard Configuration.

---

# 18. Public API Boundary

Step 7 must expose the established Register platform surface through the package-level public API.

Consumers should not need to import implementation modules merely to use supported platform capabilities.

The public API must distinguish between:

* public platform contracts;
* public result/value models;
* supported concrete implementations;
* internal coordination details.

Internal synchronization helpers and provider-specific details should remain internal unless explicitly required by an earlier public contract.

Step 7 must not expand the public API merely because a concrete implementation class happens to exist.

---

# 19. Idempotency

The platform implementation must preserve the idempotency guarantees established by Step 6.

Repeated application of the same logical Movement contribution must not duplicate its effect.

Repeated removal of an already removed contribution must not create an additional negative effect.

Repeated rebuild of the same authoritative Movement Fact set must produce the same semantic Totals state.

Idempotency must be based on stable semantic identity, not Python object identity or incidental runtime state.

---

# 20. Determinism

For the same:

* Register definition;
* authoritative Movement Fact set;
* relevant lifecycle state;
* maintenance operation;
* accounting inputs;

Step 7 implementation must produce the same semantic result.

The implementation must not depend on:

* arbitrary dictionary/set iteration order;
* object memory identity;
* storage layout;
* provider-specific ordering;
* uncontrolled wall-clock time;
* uncontrolled external state.

Where ordering is not semantically meaningful, the result must not become order-dependent.

### Register Definition as a Deterministic Input

Register Definition is part of the semantic input to Register operations.

For a given:

* Register Definition;
* authoritative Movement Facts;
* requested operation;
* relevant operation parameters;
* relevant lifecycle/consistency state;

the platform must produce the same semantic result.

Therefore, Register Definition must not be treated as incidental runtime metadata when it affects Movement validation, Totals calculation, rebuild, or other established Register semantics.

Determinism does not require identical object identities, storage layouts, provider implementations, or in-memory representations. It requires identical semantic outcomes for equivalent semantic inputs.

---

# 21. Concurrency Model

Step 7 adopts the consistency boundary established in Step 6.3:

> Consistency-sensitive operations are serialized per Register, while different Registers remain independently operable.

Conceptually:

```text
Register A
    └── serialized operations

Register B
    └── serialized operations
```

This is a logical Register-scoped boundary.

The current implementation is process-local. Step 7 must not claim stronger guarantees such as cross-process or distributed serialization.

If a future storage provider requires stronger coordination, that is a future architectural extension and is outside Step 7.

---

# 22. Composition Rules

The final platform composition must obey the following rules.

### Rule 1 — One authoritative Movement persistence boundary

All authoritative Movement Fact mutations use the established persistence contract.

### Rule 2 — One Totals maintenance boundary

All derived Totals lifecycle changes use the established maintenance boundary.

### Rule 3 — One shared Register operation domain

Movement/Totals consistency-sensitive operations for the same Register use the same operation domain.

### Rule 4 — No hidden maintenance

Balance Query and Movement Query do not silently repair Totals.

### Rule 5 — No hidden persistence

Totals Engine does not persist Movement Facts.

### Rule 6 — No hidden Standard Configuration dependency

Generic Register code does not import or branch on Standard Configuration.

### Rule 7 — No duplicate persistence architecture

Step 7 uses the existing Phase 5 persistence boundary.

### Rule 8 — No semantic contract drift

Concrete implementation must conform to the already defined contracts.

---

# 23. Current Implementation Baseline

The current repository baseline already contains concrete implementations for the major Register components, including:

```text
src/accore/platform/registers/
    movement.py
    validation.py
    query.py
    totals.py
    balance.py
    maintenance.py
    mutation.py
    operation_domain.py
```

The existence of these modules does not by itself constitute completion of Step 7.

Step 7 must verify that the implementations are correctly composed.

In particular, the baseline currently contains:

* `RegisterMutationOrchestrator` coordinating Movement persistence and Totals maintenance;
* `RegisterOperationDomain` and `RegisterOperationDomainRegistry` providing process-local Register-scoped serialization;
* `DefaultTotalsMaintenanceCoordinator` implementing Totals lifecycle / maintenance;
* the existing Movement Query, Totals Engine, and Balance Query implementations;
* package-level Register exports.

The architectural issue to verify during implementation is that the same Register Operation Domain is the effective consistency boundary for all relevant operations.

A component-local lock must not accidentally become a second semantic synchronization boundary for the same Register.

---

# 24. Implementation Gap to Resolve

The principal Step 7 implementation question is therefore not whether individual classes exist.

It is whether the existing classes form one coherent platform composition that satisfies the architecture.

The implementation review must explicitly verify:

1. whether `RegisterMutationOrchestrator` is the unique mutation orchestration boundary;
2. whether `TotalsMaintenanceCoordinator` participates in the shared Register Operation Domain rather than maintaining an independent synchronization model;
3. whether rebuild and recovery use the same domain as ordinary Movement mutation;
4. whether Movement persistence and Totals maintenance have the required failure ordering;
5. whether public API exports match the intended platform surface;
6. whether no Standard Configuration dependency exists in `accore.platform.registers`;
7. whether persistence provider details remain outside Register implementation;
8. whether current in-memory implementation state is sufficient for the intended process-local semantics and is not being mistaken for durable lifecycle state.

These are implementation verification questions, not reasons to alter the established architecture without review.

---

# 25. Testing Architecture

Step 7 tests must verify both component contracts and composition.

## 25.1 Unit tests

Existing component-level tests remain valid and must continue to pass.

They cover, among other concerns:

* Movement validation;
* Movement Query;
* Totals aggregation;
* Balance Query;
* Totals maintenance;
* mutation orchestration;
* operation-domain behavior.

## 25.2 Platform integration tests

Step 7 must add or complete tests proving that the components work together through the platform boundaries.

At minimum:

```text
Movement
   ↓
Mutation Orchestrator
   ↓
Persistence
   ↓
Totals Maintenance
   ↓
Totals
   ↓
Balance Query
```

must be demonstrably coherent.

## 25.3 Boundary tests

Tests must verify:

* no Standard Configuration import from Register Platform;
* storage-provider independence;
* Register-scoped operation isolation;
* rebuild serialization against mutation;
* failure / indeterminate propagation;
* recovery behavior;
* idempotency;
* public API availability.

---

# 26. Acceptance Criteria

Step 7 is complete only when all of the following are satisfied.

### P7-01 — Platform Contracts Implemented

All required platform contracts from Steps 2–6.3 have concrete, tested implementations.

### P7-02 — Coherent Composition

The implementations operate through the intended platform boundaries as one coherent Register subsystem.

### P7-03 — Mutation Boundary

Movement mutation affecting both authoritative facts and derived Totals passes through the established Register mutation orchestration boundary.

### P7-04 — Shared Operation Domain

Mutation, rebuild, and recovery operations for one Register use the same Register-scoped operation domain.

### P7-05 — Authoritative Facts

Persisted Movement Facts remain the sole authoritative source for Totals reconstruction.

### P7-06 — Totals Consistency

Successful operations can publish `ACTIVE / VALID` only after successful logical completion.

### P7-07 — Failure Semantics

Failure and indeterminate outcomes preserve the lifecycle / consistency semantics established by Step 6.

### P7-08 — Recovery

Recovery reconstructs derived Totals from authoritative Movement Facts.

### P7-09 — Query Separation

Movement Query and Balance Query remain read-side capabilities and do not perform hidden repair.

### P7-10 — Storage Independence

Register implementation contains no provider-specific persistence logic.

### P7-11 — Standard Configuration Independence

`accore.platform.registers` contains no dependency on `src.standard` or concrete Inventory concepts.

### P7-12 — Public API

Supported Register platform capabilities are available through the intended package-level public API.

### P7-13 — Determinism

Equivalent semantic inputs produce equivalent Register results independently of incidental runtime/storage ordering.

### P7-14 — Register Isolation

Operations for different Registers do not unnecessarily serialize each other.

### P7-15 — Tests

All existing tests pass, and platform-level integration tests cover the composition and critical architectural boundaries.

### P7-16 — No Step 8 Leakage

No Inventory-specific implementation is introduced into the Register Engine as part of Step 7.

### P7-17 — Single Semantic State Owner

The completed Register Platform composition has one authoritative lifecycle/consistency state model.

Individual components may observe or participate in state transitions but do not maintain independent semantic copies of Register lifecycle/consistency state that can diverge.

Mutation, rebuild, recovery, and query behavior therefore operate against the same authoritative Register state.

---

# 27. Architecture Review Questions

Before implementation is declared complete, the following questions must receive explicit answers.

1. Is `RegisterMutationOrchestrator` the single platform mutation boundary for Movement/Totals consistency?
2. Do all consistency-sensitive operations for one Register use one shared `RegisterOperationDomain`?
3. Does Totals Maintenance avoid owning Movement persistence?
4. Does Movement persistence remain authoritative and independent of Totals?
5. Can Totals be rebuilt without relying on previous Totals state?
6. Can Balance Query observe a state that is not semantically published as valid?
7. Are `FAILURE` and `INDETERMINATE` distinguished correctly?
8. Does recovery use authoritative Movement Facts?
9. Does any Register Platform module depend on Standard Configuration?
10. Does any Register Platform module contain Inventory-specific concepts?
11. Does any Register implementation depend on a particular storage provider?
12. Are public exports limited to the intended platform surface?
13. Are process-local concurrency guarantees clearly distinguished from distributed guarantees?
14. Do tests verify composition rather than only individual classes?
15. Can Step 8 introduce the Inventory Register without modifying generic Register Engine semantics?

---

# 28. Step 7 Exit Criteria

Step 7 may be declared complete when:

```text
All established Register contracts
          ↓
Concrete implementations
          ↓
Shared orchestration boundaries
          ↓
Register-scoped consistency
          ↓
Platform integration tests
          ↓
No Standard Configuration leakage
```

have been demonstrated by code and tests.

The resulting platform must be ready for Step 8 to define and complete the Inventory Register without changing the generic Register Engine architecture.

---

# 29. Architectural Summary

The intended result of Step 7 is:

```text
                     Register Platform

        ┌──────────────────────────────────┐
        │                                  │
        │   Register Mutation Boundary     │
        │            │                     │
        │            ▼                     │
        │   Register Operation Domain      │
        │        │           │              │
        │        ▼           ▼              │
        │  Movement      Totals             │
        │ Persistence    Maintenance        │
        │        │           │              │
        │        ▼           ▼              │
        │ Movement Query   Totals            │
        │                    │              │
        │                    ▼              │
        │               Balance             │
        │                                  │
        └──────────────────┬───────────────┘
                           │
                           │ generic contracts
                           ▼
                  Standard Configuration
                           │
                           ▼
                    Inventory Register
```

The architectural rule governing the entire step is:

> **Step 7 implements and composes the generic Register Platform. It must not encode the business semantics of the Inventory Register.**

Inventory-specific Register definition and behavior belong to Step 8.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
