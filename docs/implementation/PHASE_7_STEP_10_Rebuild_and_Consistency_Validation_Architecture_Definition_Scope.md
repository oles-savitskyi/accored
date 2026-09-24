# Phase 7 Step 10 — Rebuild and Consistency Validation

## Architecture Definition / Scope

**Project:** AcCoreD
**Phase:** Phase 7 — Register Totals and Balance
**Step:** Step 10 — Rebuild and Consistency Validation
**Status:** Final Architecture Definition / Scope
**Architecture change:** None required
**Implementation status:** Not started

---

## 1. Purpose

Phase 7 Step 10 validates that the existing generic Register Platform can reconstruct and validate derived register state from authoritative Movement Facts without introducing a new rebuild subsystem or Inventory-specific recovery infrastructure.

The purpose of this step is to prove that:

* Movement Facts remain authoritative;
* Totals remain fully reconstructible from Movement Facts;
* incremental maintenance and rebuild produce equivalent Totals;
* rebuild replaces stale derived state rather than incrementally repairing it;
* rebuild is idempotent;
* successful rebuild restores a valid maintenance state;
* maintenance failure preserves the existing recovery boundary;
* Current Balance remains equivalent before and after rebuild when authoritative facts are unchanged;
* consistency validation does not mutate authoritative Movement Facts;
* Inventory-specific Product + Warehouse / Quantity semantics survive reconstruction;
* register state remains isolated by register identity.

Step 10 is therefore a **rebuild and consistency validation step**, not a new register infrastructure implementation.

---

# 2. Architectural Context

The current Phase 7 architecture establishes the following chain:

```text
Movement Facts
      ↓
Register Mutation
      ↓
Incremental Totals Maintenance
      ↓
Totals
      ↓
Current Balance
```

The existing architecture also provides:

```text
Movement Facts
      ↓
Rebuild
      ↓
Reconstructed Totals
      ↓
Current Balance
```

Step 10 validates that these two paths are semantically equivalent.

The intended invariant is:

```text
                 AUTHORITATIVE STATE
                 ┌─────────────────┐
                 │ Movement Facts  │
                 └────────┬────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
      Incremental Maintenance      Rebuild
              │                       │
              ▼                       ▼
       ┌──────────────┐        ┌──────────────┐
       │    Totals    │        │    Totals    │
       │      A       │        │      B       │
       └──────┬───────┘        └──────┬───────┘
              │                       │
              └───────────┬───────────┘
                          ▼
                Consistency Validation
                          │
                          ▼
                    Equivalent State
                          │
                          ▼
                     Balance Query
```

---

# 3. Repository Baseline

The current repository already contains the generic infrastructure required for Step 10:

* `RegisterFactPersistence`
* `TotalsEngine`
* `TotalsMaintenanceCoordinator`
* `DefaultTotalsMaintenanceCoordinator`
* `RegisterMutationOrchestrator`
* `DefaultBalanceQueryService`
* `TotalsMaintenanceState`
* `TotalsLifecycleState`
* `TotalsConsistencyState`

The maintenance architecture already supports:

* incremental `apply`;
* incremental `remove`;
* `rebuild`;
* `recover`;
* lifecycle state;
* consistency state;
* maintenance admission;
* recovery-required state.

Inventory is already implemented as a standard register configuration over the generic platform.

Therefore Step 10 does not require another production abstraction for rebuild or consistency validation.

---

# 4. Problem Statement

Derived Totals are maintained incrementally during normal register mutation.

Incremental maintenance is efficient, but derived state must also be recoverable from authoritative persisted Movement Facts.

The architecture therefore requires a semantic guarantee that:

```text
incremental maintenance
```

and

```text
reconstruction from authoritative Movement Facts
```

produce the same register state.

Without this guarantee, a successful rebuild could technically produce a different result from normal operation, making recovery unsafe.

Step 10 establishes the validation boundary for this guarantee.

---

# 5. Architectural Goal

The architectural goal is:

> Given an unchanged set of authoritative Movement Facts, rebuilding a register must reconstruct the same valid Totals state that incremental maintenance would produce from those facts.

Consequently:

```text
Incremental Totals == Rebuilt Totals
```

and therefore:

```text
Incremental Balance == Rebuilt Balance
```

for the same aggregation scope.

---

# 6. Authoritative State

The authoritative state for register reconstruction is the persisted set of Movement Facts.

The architecture treats:

```text
RegisterFactPersistence
```

as the authoritative source for persisted register movements.

Totals are not authoritative.

Balance is not authoritative.

Maintenance bookkeeping is not authoritative.

The rebuild operation must therefore derive its result from Movement Facts rather than from the current Totals state.

---

# 7. Derived State

The following are derived from Movement Facts:

* Totals;
* Current Balance;
* maintenance consistency state;
* maintenance bookkeeping.

Derived state may be discarded and reconstructed.

The architecture must not require historical Totals to reconstruct the current state.

---

# 8. Rebuild Semantics

Rebuild means:

1. obtain the authoritative Movement Facts for the target register;
2. reconstruct the complete Totals state from those facts;
3. replace the existing derived Totals state with the reconstructed state;
4. establish successful maintenance state when reconstruction completes successfully.

Rebuild is therefore a reconstruction operation, not an incremental correction operation.

Conceptually:

```text
Existing Totals
      ↓
   discarded

Movement Facts
      ↓
   rebuild
      ↓
New Totals
```

The existing Totals state must not be treated as authoritative input to reconstruction.

---

# 9. Rebuild Independence

Rebuild must be semantically independent of the current derived Totals state.

Given identical authoritative Movement Facts:

```text
rebuild(Facts)
```

must produce the same Totals regardless of whether the previous derived state was:

* correct;
* stale;
* incomplete;
* empty;
* previously rebuilt.

This property is required for reliable recovery.

---

# 10. Incremental / Rebuild Equivalence

Step 10 validates the following invariant:

```text
Movement Facts
      ↓
incremental maintenance
      ↓
Totals A

Movement Facts
      ↓
rebuild
      ↓
Totals B

A == B
```

The validation must not merely compare two operations that internally reuse the same calculation as their expected value.

Where practical, tests must independently derive expected Totals from Movement Facts using the documented movement-sign semantics.

This prevents the test from simply reproducing the implementation under test.

---

# 11. Inventory Aggregation Semantics

Inventory remains a standard register configuration.

Its aggregation semantics are:

```text
Register:
    INVENTORY_REGISTER_ID

Dimensions:
    product
    warehouse

Resource:
    quantity

Resource type:
    Decimal
```

Movement signs are:

```text
INCOME  → +Quantity
EXPENSE → -Quantity
```

Step 10 must verify that these semantics are preserved by rebuild.

Example:

```text
P1 / W1 / INCOME   / 10
P1 / W1 / EXPENSE  /  3
------------------------
P1 / W1 / total      7
```

Rebuild must produce the same result.

Step 10 does not redefine Inventory aggregation semantics.

---

# 12. Replacement of Stale Derived State

Rebuild must replace stale Totals rather than accumulate corrections on top of them.

A validation scenario should deliberately establish a stale derived state and then perform rebuild.

Conceptually:

```text
Movement Facts:
    P1 / W1 = 10

Current Totals:
    P1 / W1 = 999

rebuild()

Result:
    P1 / W1 = 10
```

The authoritative Movement Facts must remain unchanged throughout this scenario.

---

# 13. Rebuild Idempotence

Rebuild must be idempotent for unchanged authoritative facts.

Therefore:

```text
rebuild(Facts)
rebuild(Facts)
```

must result in equivalent derived state.

The second rebuild must not:

* duplicate movements;
* accumulate totals;
* change the authoritative facts;
* introduce additional aggregate entries;
* alter the semantic balance.

---

# 14. Recovery Semantics

Recovery is reconstruction from authoritative Movement Facts.

The existing maintenance architecture provides:

```text
recover(register)
```

which delegates to the same authoritative reconstruction semantics as rebuild.

Therefore:

```text
RECOVERY_REQUIRED
       ↓
recover()
       ↓
rebuild from Movement Facts
       ↓
ACTIVE / VALID
```

when recovery succeeds.

Recovery does not introduce an alternative calculation model.

---

# 15. Maintenance Failure Boundary

A failed rebuild must not be represented as a valid derived state.

When rebuild cannot establish a valid Totals state, the maintenance architecture must preserve the existing recovery boundary.

The expected semantic state is:

```text
lifecycle  = ACTIVE
consistency = RECOVERY_REQUIRED
```

This distinction is intentional.

`RECOVERY_REQUIRED` is a **consistency failure state**, not a lifecycle state meaning that the Register is currently undergoing maintenance.

Consequently:

```text
ACTIVE + VALID
        ↓
ordinary mutation admitted
```

whereas:

```text
ACTIVE + RECOVERY_REQUIRED
        ↓
ordinary mutation rejected
```

until successful rebuild/recovery restores:

```text
ACTIVE + VALID
```

Step 10 must validate this existing boundary rather than introduce a new lifecycle state.

---

# 16. Consistency Validation

Step 10 introduces validation scenarios for consistency between:

* authoritative Movement Facts;
* Totals;
* Current Balance;
* maintenance consistency state.

Consistency validation is a **verification/test concern**, not a new production subsystem.

Step 10 must not introduce:

```text
RegisterConsistencyService
InventoryConsistencyService
TotalsConsistencyValidator
```

or an equivalent production abstraction solely for this validation.

The test architecture may independently derive expected Totals from Movement Facts and compare the result with production Totals and Balance APIs.

---

# 17. Independence of Consistency Validation

Consistency validation must avoid simply reproducing the implementation being tested.

In particular, the expected Totals calculation should not use the same production `TotalsDefinition` calculation path as the Totals Engine.

Instead, tests should independently apply the documented movement semantics:

```text
INCOME  → positive contribution
EXPENSE → negative contribution
```

and aggregate by the expected Inventory dimensions:

```text
product + warehouse
```

The purpose is to validate the production derived state against an independent semantic expectation.

---

# 18. Balance Validation

Current Balance is derived from Totals.

For unchanged Movement Facts:

```text
Balance before rebuild
        ==
Balance after rebuild
```

for the same:

* register identity;
* aggregation scope.

Step 10 does not introduce a historical Balance API.

---

# 19. Movement Facts Remain Untouched

Rebuild and consistency validation must not mutate authoritative Movement Facts.

The following must remain unchanged by rebuild:

* movement identity;
* source document identity;
* movement type;
* dimensions;
* resources;
* accounting time.

Rebuild repairs or reconstructs derived state only.

The architecture must therefore preserve:

```text
Movement Facts
      ↓
rebuild
      ↓
Totals
```

and never:

```text
Totals
      ↓
repair
      ↓
Movement Facts
```

---

# 20. Maintenance Bookkeeping Is Not Authoritative

The maintenance coordinator may maintain internal runtime bookkeeping, including the existing `_applied` tracking.

Such bookkeeping is not authoritative register state.

It must not be used as the source for reconstruction.

Rebuild must reconstruct derived state from authoritative Movement Facts and establish the corresponding maintenance bookkeeping as part of successful maintenance.

Step 10 tests must therefore validate externally observable semantic state rather than depend on internal bookkeeping representation.

---

# 21. Register Isolation

Rebuild operates on one register identity at a time.

Rebuilding Register A must not modify:

* Movement Facts of Register B;
* Totals of Register B;
* Balance of Register B;
* maintenance consistency state of Register B.

Validation must include at least one cross-register isolation scenario.

---

# 22. Dimension Isolation

Inventory totals are keyed by:

```text
product + warehouse
```

Rebuild must preserve complete dimension separation.

For example:

```text
P1 / W1 = 10
P1 / W2 = 20
P2 / W1 = 30
```

must remain three distinct aggregation scopes.

Rebuild must not collapse:

* products;
* warehouses;
* Product + Warehouse combinations.

---

# 23. Empty Register Semantics

Rebuilding an empty register is a valid operation.

Expected semantics:

```text
Movement Facts = empty
        ↓
rebuild
        ↓
successful maintenance
        ↓
ACTIVE / VALID
        ↓
no Totals entries
        ↓
Balance = 0
```

An empty register must not require a special Inventory-specific rebuild path.

---

# 24. Negative Consistency Scenario

Step 10 must include a controlled validation scenario in which derived Totals are intentionally made inconsistent with authoritative Movement Facts.

The purpose is to prove that validation can detect divergence and that rebuild can restore the correct derived state.

Conceptually:

```text
Movement Facts:
    P1 / W1 = 10

Corrupted Totals:
    P1 / W1 = 999

Consistency validation:
    mismatch detected

rebuild:

Totals:
    P1 / W1 = 10
```

This scenario must not corrupt or modify the authoritative Movement Facts.

The mechanism used to create the deliberately invalid derived state is a test concern and must not become a production API.

---

# 25. Rebuild After Unpost

The existing Posting architecture performs unpost by removing the persisted register effect through the generic mutation infrastructure.

Step 10 must validate:

```text
post
 ↓
Movement Facts = movement
Totals = movement effect

unpost
 ↓
Movement Facts = empty
Totals = zero

rebuild
 ↓
Movement Facts = empty
Totals = zero
```

This proves that rebuild follows the current authoritative state rather than stale pre-unpost state.

---

# 26. Rebuild After Repost

The existing Posting architecture performs repost as:

```text
remove old effect
      ↓
establish new effect
```

Step 10 must validate that the resulting authoritative Movement Facts are sufficient to reconstruct the final state.

Example:

```text
post quantity 10
        ↓
repost quantity 15
        ↓
authoritative Movement Facts = 15
        ↓
rebuild
        ↓
Totals = 15
        ↓
Balance = 15
```

The exact persisted representation must continue to follow the existing Posting and Register mutation contracts.

Step 10 does not introduce an alternative repost model.

---

# 27. Temporal State

Step 10 does not introduce historical Totals or historical Balance.

Temporal querying remains a Movement Facts concern:

```text
Movement Facts
      ↓
MovementQuery
      ↓
period filtering
```

with the existing half-open interval semantics:

```text
[start, end)
```

Step 10 may use accounting times when constructing authoritative Movement Fact scenarios, but it must not turn temporal movement queries into a temporal Balance API.

---

# 28. Existing Generic Architecture Reuse

Step 10 reuses the existing generic architecture:

```text
RegisterFactPersistence
        ↓
TotalsMaintenanceCoordinator
        ↓
TotalsEngine
        ↓
BalanceQueryService
```

No new rebuild pipeline is required.

The production path remains generic:

```text
RegisterMutationOrchestrator
        ↓
TotalsMaintenanceCoordinator
        ↓
TotalsEngine
```

and:

```text
TotalsMaintenanceCoordinator.rebuild()
        ↓
TotalsEngine.rebuild()
```

---

# 29. Inventory-Specific Scope

Inventory-specific Step 10 validation is limited to proving the generic platform using the Inventory configuration.

The validation covers:

* `INVENTORY_REGISTER_ID`;
* Product dimension;
* Warehouse dimension;
* Quantity resource;
* Decimal resource semantics;
* `INCOME` positive sign;
* `EXPENSE` negative sign;
* Inventory totals;
* Inventory current balance.

Inventory does not receive:

* a custom rebuild service;
* a custom consistency service;
* a custom recovery service;
* a custom Totals engine;
* a custom Balance engine;
* custom persistence for rebuild.

---

# 30. Explicit Non-Goals

Step 10 does not include:

* a new generic rebuild framework;
* an Inventory rebuild service;
* an Inventory consistency service;
* a new Totals engine;
* a new Balance engine;
* persistent historical Totals;
* historical Balance;
* temporal Balance queries;
* a new persistence model;
* a new Movement Fact model;
* changes to Posting semantics;
* changes to Goods Receipt semantics;
* distributed consistency;
* background reconciliation;
* monitoring infrastructure;
* reconciliation scheduling;
* a new public register runtime abstraction;
* a production consistency-validation service;
* concurrent rebuild/mutation transaction isolation.

Concurrent rebuild/mutation isolation is explicitly outside the scope of Step 10. This step validates deterministic single-runtime rebuild semantics and does not establish transactional guarantees for concurrent rebuild and mutation operations.

---

# 31. Expected Production Architecture Changes

Expected production architecture changes:

```text
NONE
```

The existing architecture already provides the required rebuild and recovery capabilities.

Expected Step 10 implementation should primarily consist of:

* integration/vertical tests;
* consistency validation tests;
* rebuild/recovery scenarios;
* documentation reconciliation.

Any proposed production change discovered during implementation must be reviewed separately against this architecture before being introduced.

---

# 32. Test Architecture

The primary Step 10 tests must use the production Register Platform composition.

For Inventory this means using:

```python
composition = (
    StandardConfigurationBootstrap()
    .compose_inventory_register_platform(persistence)
)
```

The tests should exercise the production:

* `RegisterFactPersistence`;
* `DefaultTotalsMaintenanceCoordinator`;
* `DefaultTotalsEngine`;
* `RegisterMutationOrchestrator`;
* `DefaultBalanceQueryService`.

The validation must not replace production rebuild or maintenance behavior with a test-only implementation.

Test helpers may exist for:

* constructing Movement Facts;
* creating documents;
* calculating independent expected Totals;
* creating deliberately stale derived state where necessary.

Such helpers must not redefine the production architecture.

---

# 33. Proposed Validation Scenarios

Step 10 should cover at least the following scenarios.

### A. Incremental vs rebuild

```text
post/apply movements
        ↓
capture incremental Totals

rebuild
        ↓
capture rebuilt Totals

assert equivalent
```

### B. Rebuild idempotence

```text
rebuild
rebuild
```

assert equivalent derived state.

### C. Stale Totals replacement

Create intentionally stale derived state and verify rebuild replaces it with the state reconstructed from Movement Facts.

### D. Empty register

Rebuild a register with no Movement Facts and verify:

```text
ACTIVE / VALID
Totals empty
Balance zero
```

### E. Recovery

Cause a maintenance failure, verify:

```text
RECOVERY_REQUIRED
```

then recover/rebuild and verify:

```text
ACTIVE / VALID
```

### F. Independent consistency validation

Independently calculate expected Totals from Movement Facts and compare with production Totals and Balance.

### G. Register isolation

Rebuild one register and verify another register remains unchanged.

### H. Unpost followed by rebuild

Verify that removing authoritative Movement Facts is reflected after rebuild.

### I. Repost followed by rebuild

Verify that the final authoritative reposted state is reconstructed correctly.

### J. Inventory dimension preservation

Verify Product + Warehouse aggregation remains separated after rebuild.

---

# 34. Consistency Invariants

Step 10 establishes the following invariants.

### Invariant 1 — Authoritative Facts

Movement Facts are authoritative.

### Invariant 2 — Reconstructibility

Totals are fully reconstructible from Movement Facts.

### Invariant 3 — Incremental/Rebuild Equivalence

```text
Incremental Totals == Rebuilt Totals
```

for identical authoritative facts.

### Invariant 4 — Idempotence

```text
Rebuild(Rebuild(Facts)) == Rebuild(Facts)
```

semantically.

### Invariant 5 — No Unsupported Aggregate

Rebuild must not leave Totals entries that cannot be derived from current Movement Facts.

### Invariant 6 — Balance Preservation

For unchanged facts:

```text
Balance before rebuild == Balance after rebuild
```

### Invariant 7 — Recovery

A successful recovery/rebuild transforms:

```text
RECOVERY_REQUIRED
```

into:

```text
ACTIVE / VALID
```

### Invariant 8 — Facts Never Repaired from Derived State

Totals and Balance never modify Movement Facts as part of rebuild or validation.

### Invariant 9 — Register Isolation

Rebuild of Register A does not modify Register B.

### Invariant 10 — Inventory Dimension Preservation

Product + Warehouse remain independent aggregation dimensions.

---

# 35. Failure and Recovery Model

The existing maintenance state machine remains authoritative for Step 10.

Normal state:

```text
ACTIVE / VALID
```

Maintenance failure:

```text
ACTIVE / RECOVERY_REQUIRED
```

Successful recovery:

```text
ACTIVE / VALID
```

The architecture deliberately does not introduce another lifecycle state for rebuild failure.

`RECOVERY_REQUIRED` expresses that the derived Totals state cannot currently be trusted for ordinary mutation admission.

---

# 36. Documentation Boundary

Step 10 documentation must describe:

* why rebuild is required;
* what state is authoritative;
* what state is derived;
* rebuild semantics;
* incremental/rebuild equivalence;
* recovery semantics;
* consistency validation boundary;
* validation scenarios;
* invariants;
* explicit non-goals.

It must not redefine:

* Posting architecture;
* Inventory configuration;
* Totals semantics;
* Balance API;
* Movement Query API;

unless an actual architectural inconsistency is discovered during implementation.

---

# 37. Concrete API Design Boundary

Concrete API Design for Step 10 must be derived from the existing repository APIs.

The Concrete API Design should not invent a new public rebuild abstraction merely to make the Step 10 tests convenient.

The primary API surface is expected to be the already existing:

```text
TotalsMaintenanceCoordinator
    apply()
    remove()
    rebuild()
    recover()
```

together with:

```text
TotalsEngine
BalanceQueryService
RegisterFactPersistence
```

Any test-only helper APIs must remain outside the production public API.

---

# 38. Definition of Done

Step 10 is complete when:

1. Architecture Definition / Scope is approved.
2. Concrete API Design is reviewed and approved.
3. Existing rebuild/recovery APIs are used without unnecessary production redesign.
4. Incremental and rebuilt Totals are proven equivalent.
5. Rebuild replacement of stale derived state is proven.
6. Rebuild idempotence is proven.
7. Recovery from `RECOVERY_REQUIRED` to `ACTIVE / VALID` is proven.
8. Independent consistency validation is implemented.
9. Balance equivalence is proven.
10. Movement Facts are proven unchanged by rebuild and validation.
11. Register isolation is proven.
12. Empty-register rebuild is proven.
13. Unpost → rebuild is proven.
14. Repost → rebuild is proven.
15. Inventory Product + Warehouse semantics are proven.
16. No historical Balance API is introduced.
17. No Inventory-specific rebuild infrastructure is introduced.
18. No production consistency-validation subsystem is introduced.
19. Concurrent rebuild/mutation isolation remains explicitly outside Step 10.
20. Tests pass.
21. `ruff check .` passes.
22. `black --check .` passes.
23. `mypy src` passes.
24. Documentation is reconciled with the final implementation.
25. Final architecture/code/docs review is completed.
26. Changes are committed and pushed to `origin/main`.

---

# 39. Architectural Decision

**Decision: APPROVED WITH AMENDMENTS**

Phase 7 Step 10 will validate the existing generic Register Platform rather than extend it with a new rebuild or consistency subsystem.

The architecture remains:

```text
                 Movement Facts
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
       Incremental          Rebuild
       Maintenance             │
             │                 │
             ▼                 ▼
          Totals A          Totals B
             │                 │
             └────────┬────────┘
                      ▼
             Consistency Validation
                      │
                      ▼
              Equivalent State
                      │
                      ▼
                 Balance
```

The four explicit architectural clarifications are:

1. `RECOVERY_REQUIRED` is a consistency state, not a separate lifecycle state; ordinary mutation remains inadmissible until `ACTIVE / VALID` is restored.
2. Consistency validation is a test/verification concern, not a new production service.
3. Internal maintenance bookkeeping such as `_applied` is not authoritative and must not be used as the source for reconstruction.
4. Concurrent rebuild/mutation transaction isolation is outside the scope of Step 10.

---

# 40. Final Scope Statement

Phase 7 Step 10 establishes confidence in the durability of the Register Platform by proving that derived Totals and Current Balance can be reconstructed consistently from authoritative Movement Facts.

The step does not expand the production architecture.

Its architectural purpose is to prove:

```text
Authoritative Movement Facts
          ↓
   Incremental Maintenance
          ↓
       Totals A

Authoritative Movement Facts
          ↓
        Rebuild
          ↓
       Totals B

             A == B
```

and consequently:

```text
Balance A == Balance B
```

for unchanged authoritative facts.

Successful completion of Step 10 establishes that the existing generic Register Platform has a validated reconstruction path for derived register state and that Inventory remains a pure standard-register configuration over that platform.

**Next stage:** Concrete API Design for Step 10, derived from the approved existing repository APIs and the validation scenarios defined above.
