# Phase 7 Step 8 — Inventory Register Completion

## Architecture Definition / Scope

**Status:** Draft for Architecture Review
**Phase:** Phase 7 — Register Platform Completion
**Step:** Step 8 — Inventory Register Completion
**Document Type:** Architecture Definition / Scope
**Baseline:** `AcCoreD_cur.zip`
**Architectural Baseline:** Phase 7 Step 7 completed
**Implementation Status:** Not started

---

# 1. Purpose

Phase 7 Step 8 completes the first concrete Register Configuration on top of the generic Register Platform by establishing **Inventory as a fully executable Standard Configuration**.

The objective is not to extend the generic Register Platform with Inventory-specific mechanics.

The objective is to demonstrate that the already established generic platform can support a concrete business register through explicit Standard Configuration:

```text
Inventory Register
        ↓
Register Configuration
        ↓
Generic Register Platform
        ↓
Movement Facts
        ↓
Totals
        ↓
Balance
```

The completed result must allow Inventory to participate in the existing register lifecycle without introducing Inventory-specific persistence, mutation orchestration, totals maintenance, recovery, or balance infrastructure.

---

# 2. Architectural Objective

The architectural objective of Step 8 is:

> **Complete Inventory as a concrete Standard Register Configuration whose semantics are explicitly defined and whose operational lifecycle is executed entirely through the generic Register Platform.**

The resulting architecture must preserve the distinction between:

### Standard Configuration

Responsible for:

* Inventory register identity;
* Inventory dimensions;
* Inventory resource semantics;
* Inventory movement semantics;
* Inventory posting constraints;
* Inventory-specific bootstrap/wiring.

### Generic Register Platform

Responsible for:

* movement representation;
* mutation;
* validation pipeline;
* persistence;
* totals maintenance;
* totals calculation;
* rebuild;
* recovery;
* movement querying;
* balance querying;
* lifecycle and consistency guarantees.

The boundary must remain explicit.

---

# 3. Architectural Principle

Step 8 follows the principle:

```text
Business-specific semantics
        ↓
Standard Configuration
        ↓
Generic platform contracts
        ↓
Generic platform execution
```

Inventory must **configure** the generic Register Platform rather than implement a parallel register subsystem.

In particular, Step 8 must not introduce:

```text
InventoryPersistence
InventoryTotalsEngine
InventoryMutationEngine
InventoryOperationDomain
InventoryRecoveryService
InventoryBalanceEngine
```

unless an explicit architecture review demonstrates that an existing generic contract is insufficient.

---

# 4. Existing Generic Register Platform Baseline

Step 8 assumes the following generic capabilities already exist.

## 4.1 Movement Facts

The Register Platform represents operational register facts as movements.

Movement facts are authoritative.

```text
Movement Facts
    ↓
authoritative register state
```

Derived totals must not become the authoritative source of register state.

---

## 4.2 Register Mutation

The generic mutation path provides the lifecycle boundary for applying and removing movements.

Conceptually:

```text
Movement
    ↓
Validation
    ↓
Register Mutation
    ↓
Persistence
    ↓
Totals Maintenance
```

Inventory must enter this pipeline rather than bypassing it.

---

## 4.3 Persistence

`RegisterFactPersistence` is the authoritative persistence boundary for register movement facts.

Inventory must use this generic persistence contract.

No Inventory-specific persistence abstraction is required by this Step.

---

## 4.4 Totals

The generic totals model provides:

```text
TotalsDefinition
TotalsKey
TotalsEngine
```

Totals are derived from authoritative movement facts.

Inventory supplies a concrete `TotalsDefinition`; it does not implement another totals engine.

---

## 4.5 Maintenance

The generic maintenance model provides lifecycle management for totals, including application, removal, rebuild and recovery semantics.

Inventory must use these generic lifecycle facilities.

---

## 4.6 Queries

The generic Register Platform provides movement-level and balance-level query semantics.

Inventory-specific consumers must use these existing contracts.

The Balance API must remain register-generic.

---

# 5. Inventory Register Definition

Step 8 establishes Inventory as a concrete register.

The Inventory register has the following semantic model.

## 5.1 Register Identity

The Inventory register has a stable register identity:

```text
INVENTORY_REGISTER_ID
```

The identity is part of Standard Configuration.

---

## 5.2 Dimensions

Inventory is identified by:

```text
Product
Warehouse
```

Conceptually:

```text
InventoryKey =
    Product
    +
    Warehouse
```

The same product in different warehouses represents distinct Inventory balances.

---

## 5.3 Resource

The Inventory resource is:

```text
Quantity
```

with:

```text
type = Decimal
```

Floating-point quantity semantics are not introduced by Step 8.

---

# 6. Inventory Movement Semantics

Inventory movement quantities are represented as positive magnitudes.

Movement direction determines the sign applied to the aggregate.

Conceptually:

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

Therefore:

```text
Receipt  100
Issue     30
----------------
Balance   70
```

The movement itself does not need to store a precomputed signed balance value.

The sign is derived from movement type semantics defined by the Inventory Totals Configuration.

---

# 7. Inventory Totals Configuration

Inventory provides the following concrete totals definition:

```text
Register:
    Inventory

Dimensions:
    Product
    Warehouse

Resource:
    Quantity : Decimal

Movement signs:
    INCOME  = +1
    EXPENSE = -1
```

This configuration is consumed by the generic Totals Engine.

The generic Totals Engine must remain unaware of Inventory.

Conceptually:

```text
Inventory TotalsDefinition
        ↓
Generic TotalsEngine
```

not:

```text
if register == INVENTORY:
    special_inventory_logic()
```

---

# 8. Inventory Posting Semantics

Inventory posting defines which operational movements are valid for the Inventory register.

The existing Goods Receipt flow establishes an initial concrete movement:

```text
Goods Receipt
    ↓
Inventory Movement
    ↓
Inventory Register
```

The Inventory posting contract must establish:

* target register;
* required dimensions;
* required resource;
* resource type;
* valid quantity;
* supported movement semantics.

For the Goods Receipt vertical slice, the resulting movement represents an Inventory income.

The architecture must explicitly determine whether the existing:

```text
GOODS_RECEIPT_MOVEMENT_TYPE
```

is:

1. a concrete Standard movement type mapped to generic `INCOME`; or
2. part of a broader Inventory movement taxonomy.

Step 8 must resolve this distinction before Concrete API Design.

No implicit equivalence is to be introduced merely through implementation.

---

# 9. Goods Receipt Integration

Goods Receipt remains responsible for Goods Receipt business semantics.

The posting handler may create the Inventory movement, but it must not own Register Platform infrastructure.

The intended flow is:

```text
Goods Receipt
        ↓
GoodsReceiptPostingHandler
        ↓
Inventory Movement
        ↓
Inventory Register Contract
        ↓
Generic Register Mutation
        ↓
RegisterFactPersistence
        ↓
Totals Maintenance
        ↓
Inventory Balance
```

The Goods Receipt posting layer must not:

* persist register facts directly;
* update totals directly;
* update balances directly;
* invoke Inventory-specific storage;
* maintain totals lifecycle state.

---

# 10. Standard Configuration Boundary

The Standard Configuration layer owns Inventory-specific declarations.

Conceptually:

```text
standard
    │
    ├── Inventory Register
    ├── Inventory Totals Definition
    ├── Inventory Posting Contract
    └── Inventory Bootstrap / Wiring
             │
             ▼
accore.platform.registers
```

The generic platform owns execution.

This boundary is mandatory.

---

# 11. Register Platform Composition

The completed architecture must compose Inventory with the generic Register Platform as follows:

```text
                   INVENTORY
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
 Register Identity  Totals Def.   Posting Contract
        │              │              │
        └──────────────┼──────────────┘
                       ▼
             Generic Register Platform
                       │
             Register Operation Domain
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
     Mutation       Persistence     Maintenance
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 Movement Facts
                       │
                       ▼
                 Totals Engine
                       │
                       ▼
                 Balance Query
```

No Inventory-specific execution engine is introduced.

---

# 12. Persistence Boundary

The authoritative Inventory state is represented by persisted movement facts.

```text
RegisterFactPersistence
        ↓
Inventory Movement Facts
```

Totals are derived.

Balances are derived.

Therefore:

```text
Movement Facts
    = authoritative

Totals
    = derived

Balance
    = derived semantic result
```

Step 8 must preserve this hierarchy.

---

# 13. Mutation Boundary

All Inventory movement mutations must pass through the generic mutation boundary.

The following direct path is prohibited:

```text
Inventory
    ↓
Persistence
```

The required path is:

```text
Inventory Movement
    ↓
Generic Register Mutation
    ↓
Persistence
    ↓
Maintenance
```

This ensures Inventory automatically inherits the generic mutation consistency model.

---

# 14. Totals Maintenance Boundary

Inventory totals are maintained by:

```text
TotalsMaintenanceCoordinator
```

and the generic totals infrastructure.

Inventory-specific code must not maintain aggregate totals independently.

The architecture must therefore guarantee:

```text
Movement Fact
       ↓
Maintenance
       ↓
Totals
```

rather than:

```text
Inventory Handler
       ├── persist movement
       └── manually update quantity
```

---

# 15. Balance Semantics

Inventory balance is a generic Register Balance result.

The semantic query is conceptually:

```text
Product + Warehouse
        ↓
Inventory Balance
        ↓
Decimal Quantity
```

For example:

```text
Product = P1
Warehouse = W1

Income:
    +100

Expense:
     -30

Balance:
     70
```

The Balance Query implementation must remain generic.

Inventory supplies the register and totals semantics; it does not implement a separate balance engine.

---

# 16. Query Boundary

Step 8 must support two conceptually distinct read paths.

## 16.1 Movement Query

Used to inspect authoritative Inventory movement facts.

```text
Register
    ↓
Movement Query
    ↓
Inventory Movement Facts
```

## 16.2 Balance Query

Used to retrieve the derived Inventory quantity.

```text
Register
    ↓
Balance Query
    ↓
Totals
    ↓
Inventory Balance
```

The two queries must not be conflated.

---

# 17. Bootstrap and Wiring

Inventory must be available through the intended Standard Configuration bootstrap/composition path.

The bootstrap boundary is responsible for connecting:

```text
Inventory Register
        ↓
Totals Definition
        ↓
Posting Contract
        ↓
Generic Register Platform
```

The bootstrap layer must not duplicate Register Platform logic.

Its responsibility is composition, not execution.

---

# 18. Lifecycle Semantics

Inventory must inherit the lifecycle semantics of the generic Register Platform.

This includes:

```text
Apply
Remove
Rebuild
Recover
```

The lifecycle model is generic.

Inventory-specific lifecycle state must not be introduced.

---

# 19. Rebuild Semantics

Inventory totals must be rebuildable from authoritative movement facts.

Conceptually:

```text
Inventory Movement Facts
        ↓
Rebuild
        ↓
Inventory Totals
        ↓
Inventory Balance
```

The rebuild result must be semantically equivalent to the result obtained through normal mutation.

The architectural invariant is:

```text
Normal mutation result
        ==
Rebuild result
```

for the same authoritative movement facts.

---

# 20. Recovery Semantics

Inventory must inherit generic recovery semantics.

If totals state becomes unavailable or inconsistent, recovery operates from authoritative movement facts.

Conceptually:

```text
Movement Facts
       ↓
Recovery
       ↓
Totals
       ↓
Balance
```

Inventory-specific recovery logic is outside scope.

---

# 21. Consistency Model

Step 8 must preserve the established consistency hierarchy.

### Authoritative

```text
Register Movement Facts
```

### Derived

```text
Totals
Balance
```

### Lifecycle State

```text
Maintenance State
Consistency State
Recovery State
```

A derived totals failure must not redefine the movement facts as invalid merely because the aggregate state is unavailable.

---

# 22. Failure Semantics

Inventory must inherit generic failure semantics.

Failures must be distinguishable at the appropriate layer.

Examples:

```text
Invalid Inventory Movement
        ↓
Validation Failure
```

```text
Movement persistence failure
        ↓
Persistence Failure
```

```text
Totals application failure
        ↓
Maintenance / Consistency Failure
```

```text
Unexpected lifecycle failure
        ↓
Recovery Required / Indeterminate
```

Step 8 must not introduce a separate Inventory failure taxonomy unless a concrete Inventory semantic error is required.

---

# 23. Idempotency and Mutation Identity

Inventory must use the generic movement identity and mutation semantics.

Inventory must not invent a separate deduplication mechanism.

If the generic platform establishes that a movement identity determines whether a movement has already been applied, Inventory inherits that rule.

This is essential for:

```text
Apply
Remove
Reapply
Recovery
```

semantics.

---

# 24. Concurrency Boundary

Inventory must inherit the generic per-register mutation/lifecycle coordination.

There must be no Inventory-specific locking model.

Conceptually:

```text
Inventory Register
        ↓
Generic Register Coordinator
        ↓
Serialized lifecycle operations
```

The purpose is to ensure that concurrent Inventory operations cannot bypass the established generic consistency model.

---

# 25. Scope Areas

## Scope A — Inventory Register Definition

Define:

* Inventory register identity;
* dimensions;
* resource;
* register-level semantics.

---

## Scope B — Inventory Totals Configuration

Define:

* Product dimension;
* Warehouse dimension;
* Quantity resource;
* Decimal representation;
* INCOME sign;
* EXPENSE sign.

---

## Scope C — Inventory Posting Contract

Define:

* valid register;
* required dimensions;
* quantity requirements;
* movement type semantics;
* relationship between Goods Receipt movement and Inventory income.

---

## Scope D — Register Platform Composition

Connect Inventory configuration to:

* mutation;
* persistence;
* totals maintenance;
* totals engine;
* movement query;
* balance query.

---

## Scope E — Standard Bootstrap / Wiring

Make the completed Inventory configuration available through the Standard Configuration composition path.

---

## Scope F — Goods Receipt Integration

Complete and verify:

```text
Goods Receipt
    ↓
Posting
    ↓
Inventory Movement
    ↓
Register Mutation
```

---

## Scope G — Inventory Query Semantics

Verify:

```text
Movement Query
```

and:

```text
Product + Warehouse
    ↓
Balance Query
```

---

## Scope H — Lifecycle / Recovery Integration

Verify that Inventory inherits:

* apply;
* remove;
* rebuild;
* recovery;
* consistency;
* maintenance state.

No Inventory-specific lifecycle engine is introduced.

---

## Scope I — Vertical Integration

Demonstrate the complete path:

```text
Goods Receipt
    ↓
Posting
    ↓
Inventory Movement
    ↓
Persistence
    ↓
Totals
    ↓
Balance
```

and lifecycle equivalence:

```text
Mutation
    ==
Rebuild
    ==
Recovery
```

with respect to the resulting Inventory balance for the same authoritative movement facts.

---

# 26. Explicit Non-Goals

The following are outside Step 8:

### Generic Platform redesign

No redesign of:

* Movement;
* Register Mutation;
* Totals Engine;
* Balance Query;
* Persistence;
* Maintenance Coordinator.

### New persistence architecture

No:

```text
InventoryRepository
InventoryPersistence
InventoryTotalsStorage
```

unless explicitly justified by architecture review.

### Inventory valuation

Step 8 does not define:

* monetary valuation;
* FIFO;
* weighted average;
* standard cost;
* COGS;
* cost layers.

### Other business processes

Step 8 does not introduce:

* Sales → Inventory;
* Production → Inventory;
* Transfer → Inventory;
* Stock Adjustment;
* Inventory Count.

These may be later vertical slices.

### Database implementation

No database-specific Inventory persistence is required by the architectural definition.

### Performance optimization

Performance tuning is not part of Step 8 unless implementation exposes a correctness-related issue requiring architectural reconsideration.

---

# 27. Architectural Invariants

The following invariants are mandatory.

## INV-01 — Inventory is a Standard Configuration

Inventory-specific semantics live outside the generic Register Platform.

## INV-02 — Movement Facts are Authoritative

Inventory balance state is ultimately reconstructible from authoritative movement facts.

## INV-03 — Totals are Derived

Inventory totals must never become the sole authoritative source of Inventory state.

## INV-04 — Balance is Derived

Inventory balance is a semantic result of the generic balance/totals model.

## INV-05 — Generic Mutation Boundary

Every Inventory mutation passes through the generic Register mutation lifecycle.

## INV-06 — Generic Persistence

Inventory uses `RegisterFactPersistence`.

## INV-07 — Generic Totals Engine

Inventory uses the generic `TotalsEngine`.

## INV-08 — Generic Maintenance

Inventory uses the generic totals maintenance lifecycle.

## INV-09 — Generic Recovery

Inventory recovery is based on generic movement-fact recovery semantics.

## INV-10 — No Inventory Branching in Generic Platform

Generic Register Platform code must not contain Inventory-specific conditional behavior merely to support Inventory.

## INV-11 — Decimal Quantity

Inventory quantity uses `Decimal`.

## INV-12 — Positive Movement Magnitude

Inventory movement quantities represent positive magnitudes; movement direction supplies the aggregation sign.

## INV-13 — Dimension Identity

Inventory balance identity is:

```text
Product + Warehouse
```

## INV-14 — Deterministic Aggregation

For the same authoritative movement facts and the same Inventory Totals Definition, the resulting Inventory balance must be deterministic.

## INV-15 — Rebuild Equivalence

Rebuilding Inventory totals from authoritative facts must produce the same semantic balance as normal lifecycle maintenance.

## INV-16 — Standard Posting Does Not Own Register Infrastructure

Goods Receipt posting creates business movements; it does not manage persistence or totals.

---

# 28. Architecture Acceptance Criteria

These criteria evaluate the **architecture itself**, independently of concrete class names, method signatures, file layout, or implementation details.

Step 8 architecture is acceptable when all of the following are true.

### AAC-01 — Standard Configuration Boundary

Inventory-specific semantics are owned by Standard Configuration, while generic Register execution remains owned by the Register Platform.

### AAC-02 — Generic Platform Reuse

Inventory can be represented as a configuration of existing generic Register contracts rather than requiring a parallel Inventory-specific execution architecture.

### AAC-03 — Authoritative State

Movement Facts are the authoritative Inventory state.

### AAC-04 — Derived State

Totals and Balance remain derived representations and are not elevated to authoritative state.

### AAC-05 — Generic Mutation Boundary

Inventory mutations enter the established generic mutation lifecycle.

### AAC-06 — Generic Persistence Boundary

Inventory movement facts are persisted through the generic Register persistence boundary.

### AAC-07 — Generic Totals Boundary

Inventory aggregation is defined through a concrete Inventory Totals Definition consumed by the generic Totals Engine.

### AAC-08 — Generic Maintenance Boundary

Inventory totals lifecycle is governed by the generic maintenance model.

### AAC-09 — Generic Query Boundary

Inventory movement and balance queries use generic query semantics rather than Inventory-specific query engines.

### AAC-10 — Generic Recovery Boundary

Inventory recovery and rebuild are based on the generic movement-fact lifecycle.

### AAC-11 — Inventory Semantics

The architecture explicitly defines:

```text
Product
Warehouse
Quantity : Decimal
INCOME  → +
EXPENSE → -
```

### AAC-12 — Goods Receipt Separation

Goods Receipt owns its business posting semantics but does not own Register persistence, totals, balance, or lifecycle infrastructure.

### AAC-13 — No Generic Inventory Branching

The architecture does not require Inventory-specific conditional logic inside generic Register Platform components.

### AAC-14 — Determinism

The architecture defines deterministic Inventory aggregation for identical authoritative movement facts and identical configuration.

### AAC-15 — Rebuildability

The architecture permits derived Inventory state to be reconstructed from authoritative movement facts.

### AAC-16 — Scope Integrity

The architecture does not implicitly expand Step 8 into valuation, costing, additional Inventory processes, or a redesign of the generic Register Platform.

### AAC-17 — Lifecycle Inheritance

Inventory inherits generic apply, remove, maintenance, rebuild, and recovery semantics rather than defining an independent lifecycle.

### AAC-18 — Explicit Unresolved Decisions

Any remaining architectural decisions, including movement-type mapping and configuration composition, are explicitly identified rather than silently determined by implementation.

---

# 29. Implementation Acceptance Criteria

These criteria apply **after Architecture Definition and Concrete API Design have been approved**. They verify that the implementation conforms to the approved architecture.

### IAC-01 — Inventory Configuration

A concrete Inventory Register Configuration is implemented and available through the approved Standard Configuration composition path.

### IAC-02 — Inventory Totals Definition

The implementation provides the approved Inventory totals configuration:

```text
Product
Warehouse
Quantity : Decimal
INCOME  +1
EXPENSE -1
```

### IAC-03 — Posting Integration

Goods Receipt produces the approved Inventory movement representation.

### IAC-04 — Movement Validation

Invalid Inventory movements are rejected according to the approved Inventory posting contract.

### IAC-05 — Generic Mutation

Valid Inventory movements pass through the approved generic Register mutation path.

### IAC-06 — Persistence

Inventory movement facts are persisted through the approved generic persistence boundary.

### IAC-07 — Totals Maintenance

Inventory totals are maintained through the approved generic maintenance mechanism.

### IAC-08 — Balance Query

The implementation returns the expected Inventory balance for:

```text
Product + Warehouse
```

using the approved generic Balance Query.

### IAC-09 — Movement Query

The implementation exposes the authoritative Inventory movement facts through the approved Movement Query.

### IAC-10 — Removal

Removing an Inventory movement produces the expected derived balance.

### IAC-11 — Rebuild

Inventory totals can be rebuilt from authoritative movement facts and produce the expected balance.

### IAC-12 — Recovery

Inventory participates successfully in the approved generic recovery lifecycle.

### IAC-13 — Determinism

Equivalent authoritative Inventory movement facts produce equivalent balances.

### IAC-14 — Separation of Responsibilities

The implementation contains no Inventory-specific replacement for generic persistence, mutation, totals, maintenance, recovery, or balance infrastructure unless separately approved.

### IAC-15 — Vertical Slice

The implementation demonstrates the complete approved flow:

```text
Goods Receipt
    ↓
Posting
    ↓
Inventory Movement
    ↓
Register Mutation
    ↓
Persistence
    ↓
Totals
    ↓
Balance
```

### IAC-16 — Lifecycle Consistency

The implementation demonstrates equivalent Inventory balance semantics after normal mutation, removal/reapplication where applicable, rebuild, and recovery.

### IAC-17 — Regression Safety

Existing Register Platform behavior remains compatible with the approved Step 8 architecture and existing tests remain passing.

### IAC-18 — Quality Gate

The implementation passes the project quality gate established for Phase 7, including applicable:

* unit tests;
* integration tests;
* full test suite;
* Ruff;
* Black;
* mypy.

---

# 30. Architectural Risks

## Risk 1 — Inventory logic leaking into generic platform

**Risk:** generic Register code starts branching on Inventory identity.

**Mitigation:** keep all Inventory semantics in Standard Configuration.

---

## Risk 2 — Totals becoming authoritative

**Risk:** Inventory balance becomes dependent on aggregate state rather than movement facts.

**Mitigation:** retain movement facts as authoritative and preserve rebuild/recovery capability.

---

## Risk 3 — Goods Receipt becoming a register implementation

**Risk:** posting code starts directly managing persistence or totals.

**Mitigation:** enforce generic Register mutation boundary.

---

## Risk 4 — Movement type ambiguity

**Risk:** `GOODS_RECEIPT_MOVEMENT_TYPE` and generic `INCOME` semantics become conflated without an explicit mapping.

**Mitigation:** resolve the relationship during Architecture Review / Concrete API Design.

---

## Risk 5 — Premature Inventory expansion

**Risk:** Step 8 grows into a complete inventory-management subsystem.

**Mitigation:** restrict the Step to Register Completion and the Goods Receipt vertical integration.

---

# 31. Target Architectural Result

After Step 8 the system should conceptually support:

```text
                    GOODS RECEIPT
                          │
                          ▼
                 Posting Handler
                          │
                          ▼
                 Inventory Movement
                          │
                          ▼
              Inventory Register Config
                          │
                          ▼
              Generic Register Platform
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
         Persistence   Maintenance   Queries
             │            │            │
             ▼            ▼            ├── Movement Query
        Movement Facts  Totals         └── Balance Query
                          │
                          ▼
                 Inventory Balance
```

The critical architectural property is:

```text
Inventory-specific semantics
        +
Generic register execution
        =
Completed Inventory Register
```

not:

```text
Inventory-specific register engine
```

---

# 32. Architecture Definition — Definition of Done

The **Architecture Definition / Scope** is complete when:

1. Inventory register semantics are explicitly defined.
2. Inventory totals semantics are explicitly defined.
3. Inventory posting semantics are explicitly bounded.
4. Generic vs Standard responsibilities are explicit.
5. Persistence ownership is explicit.
6. Mutation ownership is explicit.
7. Totals maintenance ownership is explicit.
8. Query boundaries are explicit.
9. Lifecycle and recovery inheritance is explicit.
10. Scope and non-goals are explicit.
11. Architectural invariants are explicit.
12. Architecture Acceptance Criteria are explicit and implementation-independent.
13. Implementation Acceptance Criteria are separated from architectural criteria.
14. Remaining architectural questions are explicitly identified.
15. No concrete API or implementation decision is silently introduced as an architectural requirement.

Completion of this section permits **Architecture Review**. It does not constitute approval for implementation.

---

# 33. Open Questions for Architecture Review

The following points should be resolved during the Architecture Review before Concrete API Design.

### OQ-01 — Movement Type Mapping

Should:

```text
GOODS_RECEIPT_MOVEMENT_TYPE
```

be explicitly mapped to:

```text
INCOME
```

within Standard Configuration?

---

### OQ-02 — Inventory Movement Vocabulary

Should Step 8 define only the Goods Receipt movement required by the current vertical slice, or establish the complete Inventory movement vocabulary?

The recommended architectural constraint is to define only what is necessary for the current scope while keeping the model extensible.

---

### OQ-03 — Inventory Configuration Shape

Should Inventory configuration be represented as:

```text
several explicit configuration objects
```

or:

```text
one aggregate Inventory Register Configuration
```

This should be decided during Concrete API Design rather than implementation by convention.

---

### OQ-04 — Bootstrap Ownership

The Architecture Review should confirm the exact composition boundary at which the Inventory configuration is registered with the generic Register Platform.

---

### OQ-05 — Balance Resource Naming

The architecture currently uses:

```text
Quantity
```

as the Inventory resource.

Concrete API Design should confirm the exact public identifier and its relationship to the generic resource abstraction.

---

# 34. Final Architectural Statement

Phase 7 Step 8 completes the Inventory Register by proving that Inventory can be expressed entirely as a concrete Standard Configuration over the already established generic Register Platform.

The intended final boundary is:

```text
                    STANDARD
                       │
             Inventory semantics
                       │
                       ▼
             Generic Register API
                       │
                       ▼
              Register Platform
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
 Persistence       Maintenance       Query
       │               │               │
       ▼               ▼               ▼
 Movement Facts      Totals         Balance
```

The architectural success criterion is therefore not merely that Inventory can calculate a quantity.

The success criterion is that:

> **Inventory behaves as a first-class concrete Register Configuration while all persistence, mutation, aggregation, maintenance, recovery and query mechanics remain provided by the generic Register Platform.**

This preserves the architectural objective of Phase 7: a reusable Register Platform capable of supporting concrete accounting and operational registers without embedding business-specific semantics into the platform itself.
