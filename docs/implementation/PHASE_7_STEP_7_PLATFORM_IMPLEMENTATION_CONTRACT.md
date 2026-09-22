# Phase 7 — Step 7

# Platform Implementation Contract

**Status:** Final
**Phase:** Phase 7 — Register Engine
**Step:** Step 7 — Platform Implementation
**Depends on:** Phase 7 Steps 1–6.3
**Architectural authority:** Approved Phase 7 architecture and preceding Register contracts

---

## 1. Purpose

This document defines the normative implementation contract for **Phase 7 Step 7 — Platform Implementation**.

Step 7 implements the already approved Register Platform architecture and the contracts established by Phase 7 Steps 2–6.3.

The purpose of Step 7 is to provide a concrete, reusable Register Platform implementation that:

* persists authoritative Movement Facts;
* validates Register mutations;
* queries Movement Facts;
* maintains derived Totals;
* provides Balance queries;
* coordinates ordinary Register mutations;
* provides Register-scoped operation serialization;
* implements lifecycle and consistency maintenance;
* supports rebuild and recovery;
* preserves deterministic and idempotent behavior where defined;
* remains independent of Storage Provider implementation;
* remains independent of Standard Configuration semantics.

Step 7 MUST NOT introduce new Register semantics.

---

# 2. Contract Status and Architectural Authority

This document is normative for the implementation of Phase 7 Step 7.

The implementation MUST conform to:

1. Phase 7 Architecture Definition;
2. Phase 7 Steps 2–6.3 approved contracts;
3. Phase 5 Persistence Architecture;
4. established Register domain contracts.

Where this document describes implementation structure, it MUST NOT contradict the preceding semantic contracts.

Where a semantic rule is already defined by a preceding contract, Step 7 MUST implement that rule rather than redefine it.

---

# 3. Core Implementation Principle

Step 7 is an implementation and composition step.

The implementation MUST:

* realize existing contracts;
* compose existing Register components;
* preserve established semantic boundaries;
* provide a single authoritative mutation path;
* provide a single semantic lifecycle/consistency state owner;
* preserve authoritative Movement Facts;
* maintain Totals as derived state;
* provide deterministic recovery and rebuild behavior.

Step 7 MUST NOT use implementation convenience as justification for changing established semantics.

---

# 4. Scope

Step 7 includes implementation and composition of:

* Register Definition consumption;
* Movement validation;
* Movement persistence;
* Movement enumeration;
* Movement queries;
* Totals calculation;
* Totals maintenance;
* Balance queries;
* ordinary Register mutation;
* Register-scoped operation coordination;
* lifecycle state handling;
* consistency state handling;
* rebuild;
* recovery;
* semantic publication;
* failure propagation;
* idempotency where defined by preceding contracts;
* determinism;
* public API exposure;
* integration between the established Register components;
* tests validating the complete platform composition.

---

# 5. Non-Goals

Step 7 MUST NOT implement:

* Inventory-specific semantics;
* Product semantics;
* Warehouse semantics;
* Quantity-specific business rules;
* Goods Receipt semantics;
* Posting handlers;
* Posting Context semantics;
* costing;
* valuation;
* accounting period closing;
* General Ledger behavior;
* cross-register distributed transactions;
* asynchronous maintenance;
* a new persistence architecture;
* a new Storage Provider;
* historical balance reconstruction;
* reporting architecture;
* Standard Configuration business rules;
* new Totals semantics;
* new Balance semantics.

Those concerns belong to later steps or other architectural layers.

---

# 6. Implementation Baseline

The current repository baseline contains the following Register Platform areas:

```text
src/accore/platform/registers/
    contracts.py
    totals.py
    maintenance.py
    mutation.py
    query.py
    movement.py
    validation.py
    operation_domain.py
    balance.py
```

The implementation MUST preserve the semantic responsibilities of these components.

The current repository implementation MAY evolve structurally during Step 7, but such changes MUST preserve the contracts defined here and in preceding steps.

---

# 7. Platform Component Model

The Register Platform consists conceptually of:

```text
Register Definition
        │
        ▼
Register Platform
        │
        ├── Movement Validation
        │
        ├── Movement Persistence
        │
        ├── Movement Query
        │
        ├── Totals Engine
        │
        ├── Totals Maintenance Coordinator
        │
        ├── Balance Query
        │
        ├── RegisterMutationOrchestrator
        │
        └── RegisterOperationDomain
```

The components have distinct ownership and responsibility.

No component MAY silently absorb another component's semantic responsibility.

---

# 8. Register Definition Contract

The Register Definition is the semantic definition of a concrete Register.

The semantic ownership of the Register Definition belongs to **Standard Configuration**.

Standard Configuration defines:

* Register meaning;
* dimensions;
* resources;
* movement semantics;
* movement type signs;
* concrete business meaning.

The generic Register Platform consumes the Register Definition.

The Register Platform MUST NOT define Standard Configuration-specific business semantics.

For generic platform purposes, the Register Definition is an input to deterministic Register processing.

---

# 9. Authoritative Movement Fact Contract

A Movement Fact is the authoritative operational fact of the Register.

Movement Facts MUST be treated as immutable after persistence.

A correction to an existing business fact MUST be represented through an explicit supported operation rather than mutation of an existing Movement Fact.

Movement Facts are the authoritative source for:

* Totals rebuild;
* Movement queries;
* derived Balance calculation.

Totals MUST NOT become an independent source of authoritative business state.

---

# 10. Movement Validation Contract

Movement validation MUST enforce only generic Register invariants established by the Register contracts.

Validation MAY include:

* Register compatibility;
* dimension validity;
* resource validity;
* movement type validity;
* required fact fields;
* numeric constraints;
* identity constraints.

Validation MUST NOT contain Standard Configuration-specific business rules.

Concrete business validation belongs to the appropriate Register-specific layer.

---

# 11. Movement Persistence Contract

Step 7 MUST use the established `RegisterFactPersistence` abstraction.

The Register Platform MUST NOT directly depend on:

* SQL;
* database sessions;
* filesystem paths;
* ORM models;
* Storage Provider classes;
* provider-specific transactions;
* provider-specific serialization;
* provider-specific connection management.

The persistence abstraction remains the authoritative boundary between the Register Platform and Storage Provider.

---

# 12. Movement Enumeration Contract

`RegisterFactPersistence.enumerate(register)` MUST return the authoritative Movement Facts belonging to the requested Register.

Enumeration MUST NOT return:

* Totals;
* Balance state;
* cached aggregates;
* provider-specific aggregate state;
* reconstructed summaries;
* Storage Provider internal state.

Rebuild MUST consume authoritative Movement Facts only.

This preserves:

```text
Persistence
    ↓
authoritative Movement Facts
```

as the authoritative source for derived-state reconstruction.

---

# 13. Movement Query Contract

Movement Query is a read-side capability.

It MUST:

* query authoritative Movement Facts;
* respect Register and dimension filters;
* remain provider-independent;
* remain side-effect free.

Movement Query MUST NOT:

* mutate Movement Facts;
* update Totals;
* rebuild Totals;
* repair consistency;
* transition lifecycle state.

---

# 14. Totals Engine Contract

The Totals Engine implements Totals calculation semantics established by Step 4.

The Totals Engine MUST:

* calculate derived Totals deterministically;
* apply Movement Facts according to the Register Definition;
* remove Movement Facts according to the established inverse semantics;
* support construction of fresh Totals for rebuild;
* remain independent of persistence;
* remain independent of lifecycle state.

The Totals Engine MUST NOT:

* persist Movement Facts;
* own lifecycle state;
* own consistency state;
* perform recovery;
* decide whether a Register mutation is semantically admissible;
* introduce Inventory-specific logic.

---

# 15. Totals Maintenance Contract

The `TotalsMaintenanceCoordinator` is the **single semantic owner** of the Register Platform's:

* lifecycle state;
* consistency state;
* semantic publication state;
* transitions between these states;
* maintenance outcomes determining those transitions.

It is the authoritative semantic state owner for Register lifecycle and consistency maintenance.

It does NOT own:

* authoritative Movement Facts;
* Movement persistence;
* Standard Configuration business semantics;
* Storage Provider state.

Other components MUST NOT maintain an independent semantic copy of lifecycle or consistency state.

Specifically:

* `RegisterOperationDomain` owns execution serialization and coordination, not semantic state;
* `RegisterMutationOrchestrator` coordinates ordinary mutations, not semantic state;
* `TotalsEngine` owns Totals calculation semantics, not lifecycle or consistency;
* queries observe state but do not transition it;
* `RegisterFactPersistence` owns authoritative Movement Fact persistence, not lifecycle/consistency semantics.

There MUST be one authoritative semantic state representation.

---

# 16. Totals Maintenance Operations

The maintenance layer MUST support the established operations:

* apply;
* remove;
* rebuild;
* recover.

These operations are semantically distinct.

`apply` and `remove` operate on individual Movement mutation semantics.

`rebuild` reconstructs derived Totals from authoritative Movement Facts.

`recover` restores the Register from an invalid or indeterminate maintenance condition according to the Step 6 recovery contract.

No operation MAY be silently substituted for another.

---

# 17. Balance Query Contract

Balance Query is a read-side projection over derived Register state.

Balance Query MUST:

* read current Totals;
* apply the established dimension filter semantics;
* return the established Balance Result;
* remain provider-independent.

Balance Query MUST NOT:

* persist Movement Facts;
* apply Movement Facts;
* remove Movement Facts;
* rebuild Totals;
* recover consistency;
* transition lifecycle or consistency state.

A Balance query encountering an invalid state MUST report that condition according to the established contract rather than silently repairing the Register.

---

# 18. RegisterMutationOrchestrator Contract

`RegisterMutationOrchestrator` is the platform boundary for ordinary Register mutations affecting:

1. authoritative Movement Facts;
2. corresponding derived Totals.

It coordinates mutation execution but does not own lifecycle or consistency semantics.

State transitions are owned by `TotalsMaintenanceCoordinator`.

The orchestrator MUST operate within the applicable `RegisterOperationDomain`.

---

# 19. Mutation Preconditions

An ordinary mutation MAY proceed only when all established preconditions are satisfied.

These include:

* Register exists;
* applicable Register Definition is available;
* Movement Fact is valid;
* operation is admitted by the Register Operation Domain;
* lifecycle and consistency state permit mutation according to the Phase 7 Step 6 Lifecycle / Maintenance Contract.

The Step 7 implementation MUST NOT independently invent additional lifecycle or consistency admission semantics.

The implementation MUST NOT infer mutation admissibility from an implementation-specific state combination that is not defined by Step 6.

---

# 20. Mutation Contract

A successful mutation MUST satisfy all obligations defined by the preceding contracts.

At minimum:

```text
validate Movement
        ↓
persist authoritative Movement Fact
        ↓
maintain corresponding Totals
        ↓
establish required consistency state
        ↓
semantic publication
```

The exact operation ordering MUST preserve the established failure semantics and MUST NOT expose a false successful result.

Semantic publication MUST occur only after all obligations required for successful completion have been satisfied.

---

# 21. Remove Contract

Removal is a distinct Register mutation operation.

The implementation MUST NOT treat removal as an ordinary mutation with an implicit negative Movement unless the established Register contract explicitly defines such semantics.

Where removal is supported:

* the authoritative Movement Fact MUST be handled according to its persistence contract;
* corresponding Totals MUST be updated according to the established inverse semantics;
* lifecycle/consistency state MUST be transitioned through `TotalsMaintenanceCoordinator`;
* semantic publication MUST occur only after successful completion.

---

# 22. RegisterOperationDomain Contract

`RegisterOperationDomain` is the shared execution and consistency boundary for a Register.

It is responsible for:

* Register-scoped serialization;
* operation admission;
* coordination;
* prevention of conflicting concurrent operations;
* coordination of ordinary mutation, rebuild, and recovery.

It is NOT a semantic lifecycle/consistency state owner.

The domain MAY enforce operation admission based on the authoritative lifecycle and consistency state.

However, it MUST NOT:

* define lifecycle semantics;
* define consistency semantics;
* own an independent lifecycle state;
* own an independent consistency state;
* independently transition semantic state.

State decisions and transitions belong to `TotalsMaintenanceCoordinator`.

---

# 23. Register-Scoped Serialization

Operations affecting the same Register MUST be serialized according to the Step 6 concurrency contract.

At minimum, the following operations participate in the same Register-scoped coordination boundary:

* ordinary mutation;
* removal;
* rebuild;
* recovery.

Different Registers MUST NOT be unnecessarily serialized through one global Register lock.

The implementation MUST provide Register isolation.

---

# 24. Lifecycle State Contract

The lifecycle model established by Step 6 consists of:

```text
CREATED
ACTIVE
MAINTENANCE
```

The semantic ownership of lifecycle state belongs exclusively to `TotalsMaintenanceCoordinator`.

The implementation MUST use only lifecycle transitions established by the Step 6 contract.

Step 7 MUST NOT introduce additional lifecycle states.

`RegisterOperationDomain` MAY enforce admission according to lifecycle state but MUST NOT define lifecycle transitions.

---

# 25. Consistency State Contract

The consistency model established by Step 6 consists of:

```text
VALID
INDETERMINATE
RECOVERY_REQUIRED
```

The semantic ownership of consistency state belongs exclusively to `TotalsMaintenanceCoordinator`.

The implementation MUST preserve the distinction between:

* valid state;
* indeterminate state;
* recovery-required state.

A failed operation MUST NOT be reported as successful when the resulting state is semantically indeterminate.

Step 7 MUST NOT introduce an alternative consistency model.

---

# 26. Failure Contract

The platform MUST preserve the semantic distinction between:

1. validation failure;
2. expected operational failure;
3. indeterminate outcome;
4. recovery-required state.

Concrete exception classes MAY vary only where such variation does not change the established semantic classification.

An implementation MUST NOT collapse an indeterminate outcome into an ordinary success or ordinary deterministic failure.

---

# 27. Rebuild Contract

Rebuild reconstructs derived Totals from authoritative Movement Facts.

The normative dependency is:

```text
RegisterFactPersistence.enumerate(register)
                    ↓
        authoritative Movement Facts
                    ↓
             Fresh Totals
                    ↓
        consistency validation
                    ↓
          semantic publication
```

Rebuild MUST NOT depend on the previous Totals state.

Rebuild MUST be capable of reconstructing derived state even when the previous Totals state is unavailable, invalid, or inconsistent.

Rebuild MUST be deterministic for the same authoritative Movement Fact set and Register Definition.

---

# 28. Recovery Contract

Recovery is distinct from ordinary mutation.

Recovery MAY use rebuild or other established maintenance mechanisms, but it MUST follow the recovery semantics defined by Step 6.

Successful recovery MUST transition the authoritative maintenance state to the terminal state defined by the Step 6 contract.

If Step 6 defines successful recovery as `VALID`, Step 7 MUST transition to `VALID`.

Recovery MUST NOT report success while the authoritative state remains `INDETERMINATE` or `RECOVERY_REQUIRED`.

Step 7 MUST NOT introduce an alternative recovery terminal state.

---

# 29. Semantic Publication Boundary

Semantic publication means that the Register Platform exposes the completed operation as successful to its caller or downstream consumer.

Publication MUST occur only after all obligations required by the operation's contract have completed successfully.

For ordinary mutation this includes the required relationship between:

* authoritative Movement persistence;
* derived Totals maintenance;
* lifecycle/consistency state.

For rebuild and recovery it includes the corresponding maintenance and state obligations.

No implementation MAY publish success before the required semantic obligations are complete.

---

# 30. Failure Must Not Masquerade as Success

The following invariant is mandatory:

> A platform operation MUST NOT report successful semantic completion when the authoritative Register state cannot be established as successful according to its contract.

In particular:

```text
unexpected failure
        ↓
NOT success
```

and:

```text
indeterminate outcome
        ↓
NOT success
```

The implementation MUST preserve the distinction between deterministic failure and uncertainty about resulting state.

---

# 31. Authoritative and Derived State Invariant

The Register Platform has the following authority hierarchy:

```text
Persisted Movement Facts
            ↓
       Totals Engine
            ↓
     Derived Totals
            ↓
      Balance Query
```

Movement Facts are authoritative.

Totals are derived.

Balance is a projection.

No derived representation MAY become an independent authoritative source of Register business facts.

---

# 32. Idempotency Contract

Idempotency is defined per operation by the underlying Phase 7 Steps 2–6 contracts.

Step 7 MUST preserve those semantics.

The implementation MUST NOT invent new idempotency behavior.

The implementation MUST distinguish:

* operation idempotency;
* deterministic execution;
* repeatable rebuild.

Where an operation is defined as idempotent by its preceding contract, repeated execution MUST produce the established idempotent result.

Where an operation is not defined as idempotent, Step 7 MUST NOT silently make it idempotent through implementation shortcuts.

Rebuild MUST produce the same derived state for the same authoritative Movement Fact set and Register Definition.

---

# 33. Determinism Contract

Register Platform operations MUST be deterministic wherever the preceding contracts require deterministic behavior.

Determinism MUST NOT depend on:

* uncontrolled current time;
* process ordering;
* object identity unrelated to semantic identity;
* uncontrolled iteration order;
* external mutable state;
* Storage Provider implementation details.

The Register Definition is part of the semantic input required for deterministic Totals calculation.

---

# 34. Time Boundary

Step 7 MUST NOT introduce implicit dependence on wall-clock time.

If time is semantically required by an established contract, it MUST be supplied through an explicit contract-defined boundary.

The implementation MUST NOT silently use:

```python
datetime.now()
```

or equivalent uncontrolled time access as part of Register semantic calculation.

---

# 35. Persistence Independence

The Register Platform MUST depend only on persistence abstractions.

The platform MUST remain independent of:

* relational database implementation;
* document database implementation;
* filesystem implementation;
* in-memory provider implementation;
* ORM;
* database transaction API;
* provider-specific serialization.

Storage Provider changes MUST NOT require changes to Register semantics.

---

# 36. Dependency Direction

The architectural dependency direction is:

```text
Standard Configuration
        ↓
Register Platform
        ↓
Persistence Abstraction
        ↓
Storage Provider
```

The arrows denote **code dependency / import dependency direction**.

Therefore:

* Standard Configuration MAY depend on Register Platform;
* Register Platform MAY depend on Persistence Abstraction;
* Persistence Abstraction MAY be implemented by Storage Provider;
* Register Platform MUST NOT import Standard Configuration;
* Register Platform MUST NOT import concrete Storage Provider implementations.

---

# 37. Standard Configuration Boundary

The generic Register Platform MUST remain free of Standard Configuration-specific semantics.

The platform MAY consume:

* Register identity;
* Register Definition;
* dimensions;
* resources;
* movement types;
* movement signs;
* other generic semantic configuration defined by the Register contracts.

The platform MUST NOT contain logic such as:

```text
if register == INVENTORY:
    ...
```

or equivalent hard-coded Standard Configuration branching.

---

# 38. Public API Contract

The public API MUST expose only the intended Register Platform capabilities.

Public API exposure MUST correspond to established platform contracts.

The public surface MUST NOT expose:

* provider-specific implementation details;
* internal locks;
* internal caches;
* private maintenance state;
* Storage Provider implementation classes;
* internal orchestration helpers.

Public API naming MAY evolve during implementation only when semantic contracts remain unchanged.

---

# 39. Internal Implementation Boundary

Internal implementation details MAY include:

* locks;
* state storage;
* operation bookkeeping;
* internal helper objects;
* caches;
* private coordination structures.

These MUST remain internal.

Internal implementation MUST NOT create a second semantic model of lifecycle or consistency state.

---

# 40. Composition Contract

The Register Platform MUST have:

* one authoritative Movement persistence boundary;
* one Totals calculation boundary;
* one Totals maintenance boundary;
* one semantic lifecycle/consistency state owner;
* one Register-scoped operation domain per Register;
* one ordinary mutation orchestration boundary.

The components MUST compose without hidden duplicate state or duplicate persistence paths.

---

# 41. No Hidden Persistence

No Register component other than the established persistence boundary MAY silently persist Movement Facts.

In particular:

* Totals Engine MUST NOT persist;
* Totals Maintenance MUST NOT create an alternative Movement store;
* Balance Query MUST NOT persist;
* Movement Query MUST NOT persist;
* Operation Domain MUST NOT persist;
* Mutation Orchestrator MUST use the established persistence boundary.

---

# 42. No Hidden Maintenance

No Register component other than the established maintenance boundary MAY silently mutate Totals or lifecycle/consistency state.

In particular:

* Balance Query MUST NOT repair;
* Movement Query MUST NOT repair;
* Totals Engine MUST NOT transition lifecycle;
* Operation Domain MUST NOT independently transition consistency;
* Mutation Orchestrator MUST NOT maintain an independent state representation.

All semantic maintenance transitions belong to `TotalsMaintenanceCoordinator`.

---

# 43. Mutation and Totals Coordination

Ordinary mutation MUST coordinate authoritative Movement persistence and derived Totals maintenance according to the established failure contract.

The implementation MUST NOT expose a successful mutation if required Totals maintenance has failed in a way that invalidates the operation's success semantics.

If the outcome becomes indeterminate, the implementation MUST preserve that indeterminate classification and transition the authoritative maintenance state according to Step 6.

The exact rollback/recovery behavior MUST follow the preceding persistence and maintenance contracts.

Step 7 MUST NOT invent distributed atomicity.

---

# 44. Rebuild Independence from Totals

Rebuild MUST NOT use the existing Totals as an input source.

The implementation MUST construct a fresh derived state from authoritative Movement Facts.

This guarantees that rebuild can correct derived-state corruption.

The existing Totals MAY be replaced after the fresh result has been validated according to the maintenance contract.

---

# 45. Recovery Independence from Normal Mutation

Recovery is a maintenance operation, not an ordinary Movement mutation.

Recovery MUST NOT be implemented merely as a normal `apply()` operation with special flags.

Recovery MAY reuse internal components, but its semantic contract remains distinct.

Recovery MUST follow:

* recovery admission;
* recovery execution;
* failure classification;
* terminal-state semantics;

defined by Step 6.

---

# 46. Register Isolation

Each Register has an independent operation domain.

Operations on one Register MUST NOT unnecessarily block operations on another Register.

A failure or recovery requirement in one Register MUST NOT automatically transition another Register into an equivalent semantic state.

Cross-register coordination is outside Step 7 unless explicitly defined by a preceding contract.

---

# 47. Error Surface

The platform MUST preserve semantic error classification.

At minimum, implementation behavior MUST allow callers to distinguish:

```text
validation failure
expected operational failure
indeterminate outcome
recovery-required state
```

Concrete Python exception hierarchy MAY be structured according to implementation needs, but the public semantic distinction MUST remain observable.

Provider-specific exceptions MUST NOT leak through the public Register Platform boundary when the persistence contract requires translation into platform-level errors.

---

# 48. Observability Contract

The semantic result of a maintenance or mutation operation MUST be observable through its platform result/outcome surface.

Where applicable, the observable result MUST allow determination of:

* operation outcome;
* success/failure;
* lifecycle state;
* consistency state;
* indeterminate condition;
* recovery-required condition.

Logging, metrics, tracing, and diagnostic infrastructure are implementation concerns.

They are NOT part of the Step 7 semantic contract unless explicitly required by a preceding contract.

---

# 49. Testing Contract

Step 7 implementation MUST include tests covering:

### Composition

* Mutation → Movement Persistence → Totals Maintenance;
* Rebuild → Movement Enumeration → Fresh Totals;
* Recovery → maintenance state restoration;
* Balance Query over maintained Totals.

### State

* lifecycle transitions;
* consistency transitions;
* single semantic state owner;
* invalid transition rejection.

### Failure

* validation failure;
* expected operational failure;
* indeterminate outcome;
* recovery-required state;
* no false success.

### Concurrency

* same-Register serialization;
* independent Register execution.

### Independence

* Storage Provider independence;
* Standard Configuration independence.

### Determinism

* repeated calculation;
* rebuild reproducibility;
* deterministic Totals.

---

# 50. Contract Test Invariants

The following invariants MUST hold.

### INV-01 — Movement Authority

Movement Facts are authoritative Register operational facts.

### INV-02 — Derived Totals

Totals are derived state.

### INV-03 — Balance Projection

Balance is a read-side projection.

### INV-04 — Persistence Boundary

Movement persistence occurs only through the established persistence abstraction.

### INV-05 — Maintenance Boundary

Lifecycle and consistency transitions occur only through `TotalsMaintenanceCoordinator`.

### INV-06 — Single Semantic State Owner

`TotalsMaintenanceCoordinator` is the single semantic owner of lifecycle, consistency, and semantic publication state.

### INV-07 — Operation Domain

Register operations are coordinated through the Register-scoped Operation Domain.

### INV-08 — Register Isolation

Different Registers have independent operation domains and semantic state.

### INV-09 — Rebuild Independence

Rebuild does not depend on existing Totals.

### INV-10 — No False Success

An indeterminate or failed operation MUST NOT be reported as successful semantic completion.

### INV-11 — Standard Independence

Generic Register Platform code MUST NOT depend on Standard Configuration-specific business logic.

### INV-12 — Provider Independence

Generic Register Platform code MUST NOT depend on concrete Storage Provider implementations.

### INV-13 — Single Lifecycle/Consistency State Owner

`TotalsMaintenanceCoordinator` is the single semantic owner of Register lifecycle state, consistency state, and semantic publication state.

Other components MUST NOT maintain independent semantic copies of those states.

All lifecycle and consistency transitions MUST be transitions of the same authoritative semantic state.

---

# 51. Acceptance Criteria

Step 7 implementation is accepted only if all of the following are satisfied.

### P7-IMP-01 — Movement Persistence

Authoritative Movement Facts are persisted through `RegisterFactPersistence`.

### P7-IMP-02 — Movement Enumeration

Enumeration returns authoritative Movement Facts only.

### P7-IMP-03 — Movement Query

Movement queries operate read-only over authoritative Movement Facts.

### P7-IMP-04 — Totals Engine

Totals are calculated according to the established Totals contract.

### P7-IMP-05 — Totals Maintenance

Incremental maintenance, rebuild, and recovery are implemented.

### P7-IMP-06 — Balance Query

Balance queries use derived Totals and remain read-only.

### P7-IMP-07 — Mutation Boundary

Ordinary mutations pass through `RegisterMutationOrchestrator`.

### P7-IMP-08 — Operation Domain

Ordinary mutation, rebuild, and recovery are coordinated by the Register Operation Domain.

### P7-IMP-09 — Register Serialization

Operations on the same Register are serialized according to the concurrency contract.

### P7-IMP-10 — Register Isolation

Independent Registers do not unnecessarily share serialization.

### P7-IMP-11 — Lifecycle State

Lifecycle semantics follow the Step 6 contract.

### P7-IMP-12 — Consistency State

Consistency semantics follow the Step 6 contract.

### P7-IMP-13 — Failure Semantics

Expected failure and indeterminate outcomes remain distinguishable.

### P7-IMP-14 — Rebuild

Rebuild reconstructs Totals from authoritative Movement Facts.

### P7-IMP-15 — Recovery

Recovery follows the established recovery contract and terminal-state semantics.

### P7-IMP-16 — Provider Independence

No generic Register Platform implementation depends on concrete Storage Provider code.

### P7-IMP-17 — Standard Independence

No generic Register Platform implementation depends on Standard Configuration-specific business logic.

### P7-IMP-18 — Semantic State Ownership

`TotalsMaintenanceCoordinator` is the sole semantic lifecycle/consistency state owner.

### P7-IMP-19 — No Hidden Mutation

Queries and calculation components do not perform hidden persistence or maintenance.

### P7-IMP-20 — No Step 8 Leakage

No Inventory-specific implementation is introduced into the generic Register Platform.

---

# 52. Implementation Mapping

The following mapping is normative for the current repository baseline at the semantic level.

| Semantic Component     | Current Implementation Area                       |
| ---------------------- | ------------------------------------------------- |
| Register contracts     | `accore.platform.registers.contracts`             |
| Movement               | `accore.platform.registers.movement`              |
| Movement validation    | `accore.platform.registers.validation`            |
| Totals Engine          | `accore.platform.registers.totals`                |
| Totals Maintenance     | `accore.platform.registers.maintenance`           |
| Mutation Orchestration | `accore.platform.registers.mutation`              |
| Operation Domain       | `accore.platform.registers.operation_domain`      |
| Movement Query         | `accore.platform.registers.query`                 |
| Balance Query          | `accore.platform.registers.balance`               |
| Persistence boundary   | established `RegisterFactPersistence` abstraction |

The concrete class/module mapping MAY evolve during implementation only if semantic responsibilities remain unchanged.

Repository implementation mapping MUST NOT be interpreted as permission to move semantic ownership between components.

---

# 53. Implementation Rules

The Step 7 implementation MUST follow these rules.

### Rule 1 — No New Semantics

Do not invent new Register semantics.

### Rule 2 — One Authority

Movement Facts remain authoritative.

### Rule 3 — One State Owner

`TotalsMaintenanceCoordinator` remains the sole semantic lifecycle/consistency state owner.

### Rule 4 — One Persistence Boundary

Movement persistence occurs through the established persistence abstraction.

### Rule 5 — One Mutation Boundary

Ordinary mutations pass through `RegisterMutationOrchestrator`.

### Rule 6 — One Operation Domain

Register-scoped operations are coordinated through `RegisterOperationDomain`.

### Rule 7 — Rebuild from Facts

Rebuild starts from authoritative Movement Facts.

### Rule 8 — No Hidden Repair

Queries MUST NOT repair Register state.

### Rule 9 — No Provider Leakage

Provider-specific implementation MUST remain below the persistence abstraction.

### Rule 10 — No Standard Leakage

Standard Configuration-specific business semantics MUST remain outside the generic Register Platform.

---

# 54. Architecture Review Questions

Before implementation begins, the following questions MUST have explicit answers in the implementation plan.

1. Is every existing Register contract represented by one concrete implementation boundary?
2. Is Movement persistence performed only through `RegisterFactPersistence`?
3. Is `TotalsMaintenanceCoordinator` the only semantic lifecycle/consistency state owner?
4. Does `RegisterOperationDomain` coordinate without owning semantic state?
5. Does `RegisterMutationOrchestrator` remain the ordinary mutation boundary?
6. Are mutation preconditions exactly those established by Step 6?
7. Are lifecycle transitions exactly those established by Step 6?
8. Are consistency transitions exactly those established by Step 6?
9. Are recovery terminal states exactly those established by Step 6?
10. Are operation-specific idempotency semantics preserved?
11. Is determinism independent of uncontrolled time and iteration order?
12. Can rebuild operate from authoritative Movement Facts alone?
13. Can Balance Query remain completely read-only?
14. Can different Registers operate independently?
15. Can Storage Providers be replaced without changing Register semantics?
16. Is Standard Configuration absent from generic Register Platform dependencies?
17. Can no failure path produce false semantic success?
18. Is there exactly one semantic representation of lifecycle and consistency state?

---

# 55. Step 7 Contract Exit Criteria

The Step 7 Platform Implementation Contract is considered complete when:

* all architecture review corrections are incorporated;
* lifecycle/consistency ownership is unambiguous;
* mutation admission is governed by Step 6;
* recovery terminal semantics are governed by Step 6;
* operation-specific idempotency semantics are preserved;
* failure classification is normative;
* semantic observability is defined;
* repository implementation mapping is explicit;
* no unresolved architectural ambiguity remains.

After this Contract is approved, the next stage is:

```text
Step 7 Platform Implementation Contract
                ↓
Implementation Scope
                ↓
Concrete Implementation Plan
                ↓
Repository Integration-Point Review
                ↓
Implementation
                ↓
Tests / Quality Gate
```

For the original Step 7 planning sequence, implementation was gated by review of the Implementation Scope and Concrete Implementation Plan. That planning gate has been completed; this reconciled contract records the resulting implemented architecture.

---

# Architectural Summary

Phase 7 Step 7 implements the Register Platform as a composition of already approved contracts.

The resulting architecture is:

```text
                         Standard Configuration
                                  │
                                  │ semantic definition
                                  ▼
                         Register Platform
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
 Movement Persistence       Totals Engine          Query Layer
          │                       │                 ┌─────┴─────┐
          │                       │                 │           │
          │                       ▼                 ▼           ▼
          │               Totals Maintenance   Movement     Balance
          │               Coordinator          Query        Query
          │                       │
          │                       │ owns
          │                       ▼
          │               Lifecycle /
          │               Consistency /
          │               Publication State
          │
          └───────────────┐
                          │
                          ▼
                RegisterMutationOrchestrator
                          │
                          ▼
                 RegisterOperationDomain
                          │
                          ├── serialization
                          ├── admission
                          └── coordination
```

The authoritative state hierarchy remains:

```text
Authoritative Movement Facts
            ↓
       Totals Engine
            ↓
     Derived Totals
            ↓
      Balance Query
```

The semantic state ownership remains:

```text
TotalsMaintenanceCoordinator
            │
            ├── Lifecycle State
            ├── Consistency State
            └── Semantic Publication State
```

The execution boundary remains:

```text
RegisterOperationDomain
            │
            ├── ordinary mutation
            ├── rebuild
            └── recovery
```

The platform therefore provides a coherent implementation boundary for the Register Engine while preserving:

* authoritative Movement Facts;
* derived Totals;
* explicit lifecycle and consistency semantics;
* Register-scoped serialization;
* deterministic rebuild;
* recovery capability;
* persistence-provider independence;
* Standard Configuration independence;
* and a single semantic owner for Register maintenance state.

This completes the normative implementation contract for **Phase 7 Step 7 — Platform Implementation**.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
