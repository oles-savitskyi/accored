# Phase 7 — Step 6

# Lifecycle / Maintenance Architecture Definition

**Status:** Draft — Architecture Definition
**Phase:** 7 — Register Totals and Balance
**Step:** 6 — Lifecycle / Maintenance
**Previous Step:** Step 5 — Balance Query
**Next Stage:** Architecture Review
**Document Type:** Architecture Definition

---

## 1. Purpose

Step 6 defines the lifecycle and maintenance architecture for Register Totals introduced by Phase 7.

The purpose of this step is to define how the derived totals aggregate is:

* created;
* activated;
* maintained;
* rebuilt;
* isolated during maintenance;
* recovered after failure;
* returned to a consistent state.

This step does **not** redefine the semantics of Balance Query established by Step 5.

The architectural objective is to establish a reliable relationship between:

```text
Persisted Movement Facts
        ↓
Totals Maintenance
        ↓
Current Total
        ↓
Balance Query
```

The central architectural principle is:

> Movement Facts are authoritative persisted facts. Register Totals are derived state maintained from those facts.

Therefore, the system must always retain a deterministic path from persisted Movement Facts to a freshly reconstructed Totals state.

---

# 2. Architectural Context

Phase 7 establishes a register-oriented aggregation model.

The currently established processing chain is:

```text
Movement Facts
      ↓
Totals Engine
      ↓
TotalsKey
      ↓
Current Total
      ↓
Balance Query
      ↓
Balance Result
```

Step 5 defined the read-side semantics of Balance Query.

Step 6 defines the lifecycle of the derived aggregate used by that query.

The complete architectural relationship becomes:

```text
                  ┌──────────────────────┐
                  │ Persisted Movement   │
                  │ Facts                │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Totals Maintenance   │
                  │                      │
                  │ apply / remove /     │
                  │ rebuild              │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Current Totals       │
                  │                      │
                  │ Derived State        │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Balance Query        │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Balance Result       │
                  └──────────────────────┘
```

The Totals layer is therefore not an independent source of business truth.

---

# 3. Scope

Step 6 covers the lifecycle and maintenance semantics of Register Totals.

Specifically, it defines:

1. Register lifecycle states.
2. Valid lifecycle transitions.
3. Maintenance and rebuild semantics.
4. Totals maintenance operations.
5. Source-of-truth rules.
6. Logical consistency boundaries.
7. Visibility during maintenance.
8. Failure and indeterminate states.
9. Idempotency requirements.
10. Recovery semantics.
11. Relationship between maintenance and Balance Query.
12. Architectural invariants.
13. Acceptance criteria for lifecycle and maintenance.

---

# 4. Non-Goals

The following are explicitly outside Step 6.

## 4.1 Reporting

Step 6 does not define reporting, reporting snapshots, report generation, or reporting-specific aggregation.

---

## 4.2 Historical Balances

Step 6 does not define historical balance queries, temporal reconstruction of balances, or historical snapshots.

---

## 4.3 Period Closing

Step 6 does not define accounting periods, period closing, reopening, or period locks.

---

## 4.4 Valuation and Costing

Step 6 does not define:

* valuation;
* costing;
* cost layers;
* price calculation;
* inventory valuation methods.

---

## 4.5 Distributed Transactions

Step 6 does not define distributed transaction protocols, two-phase commit, distributed locks, or distributed consensus.

---

## 4.6 Asynchronous Maintenance

Step 6 defines lifecycle and consistency semantics independently of an asynchronous execution model.

It does not introduce a general asynchronous maintenance architecture.

An implementation may later choose a particular execution mechanism, but that mechanism must preserve the contracts defined here.

---

## 4.7 General Ledger

Step 6 does not define General Ledger behavior or financial posting semantics.

---

## 4.8 New Persistence Architecture

Step 6 does not redesign persistence.

Existing persistence boundaries remain authoritative.

The step defines how persisted Movement Facts participate in maintenance and recovery.

---

## 4.9 Balance Query Redesign

The Balance Query contract from Step 5 is not reopened.

Step 6 defines the state that Balance Query is allowed to observe, but does not redefine the meaning of:

* Balance Query;
* TotalsKey;
* Current Total;
* Balance Result.

---

# 5. Architectural Responsibility

The responsibility of Step 6 is to guarantee that derived Totals state has a well-defined lifecycle and a recoverable relationship to persisted Movement Facts.

The architecture must provide:

```text
Authoritative Facts
        ↓
Deterministic Derivation
        ↓
Maintained Derived State
        ↓
Consistent Read State
```

The Totals subsystem is responsible for maintaining derived state.

It is not responsible for creating an alternative source of business truth.

---

# 6. Fundamental State Model

Phase 7 distinguishes two categories of state.

## 6.1 Authoritative State

Persisted Movement Facts constitute authoritative register facts.

They answer:

> What movements exist?

Movement persistence is therefore the authoritative basis from which Register Totals can be reconstructed.

---

## 6.2 Derived State

Register Totals are derived state.

They answer:

> What is the current aggregate implied by the persisted Movement Facts?

Totals may therefore be:

* maintained incrementally;
* invalidated;
* discarded;
* rebuilt.

Their correctness must not depend on the historical correctness of an older Totals representation.

---

# 7. Source-of-Truth Invariant

The primary Step 6 invariant is:

> Persisted Movement Facts are the source of truth for rebuilding Register Totals.

Therefore:

```text
Persisted Movement Facts
        ↓
      Rebuild
        ↓
   Fresh Totals
```

is authoritative.

The following is explicitly prohibited as the semantic basis of rebuild:

```text
Old Totals
   ↓
"repair"
   ↓
New Totals
```

A rebuild must not assume that existing Totals are correct.

---

# 8. Register Lifecycle

A Register has a lifecycle independent of individual Balance Queries.

The conceptual lifecycle is:

```text
Created
   ↓
Active
   ↓
Maintenance / Rebuild
   ↓
Active
```

The lifecycle defines whether the derived Totals state is available for ordinary use.

---

# 9. Lifecycle States

## 9.1 Created

`Created` means that the Register exists as a recognized architectural object but has not yet entered its normal operational state.

Characteristics:

* register identity exists;
* register definition exists;
* normal Balance Query operation is not yet considered active;
* Totals state may be absent or not yet initialized.

`Created` does not imply that Totals are already complete.

---

## 9.2 Active

`Active` is the normal operational state.

In `Active`:

* Movement Facts may be maintained according to the applicable posting/persistence contract;
* Totals maintenance may occur;
* Balance Query may read Current Totals;
* the Totals state exposed to Balance Query is considered consistent with the authoritative Movement Facts under the Step 6 consistency contract.

The normal invariant is:

```text
Active
  ⇒
Totals are valid for Balance Query
```

---

## 9.3 Maintenance / Rebuild

`Maintenance / Rebuild` represents a controlled state in which the existing derived Totals state is being modified or reconstructed.

This state exists to protect the read-side contract from partial derived state.

During this state:

* the previous Totals state is not treated as the state being progressively exposed;
* a rebuild may construct a replacement Totals state;
* the incomplete replacement state is not visible to ordinary Balance Query;
* completion requires an explicit successful transition back to `Active`.

---

# 10. Lifecycle Transition Model

The valid conceptual transitions are:

```text
Created
   │
   │ activate
   ▼
Active
   │
   │ enter maintenance
   ▼
Maintenance / Rebuild
   │
   │ successful completion
   ▼
Active
```

A maintenance failure does not automatically imply successful return to `Active`.

The resulting state depends on whether the previously active Totals state remains valid and available.

---

# 11. Maintenance Entry

Entering maintenance establishes a visibility boundary.

Conceptually:

```text
Active
   ↓
Maintenance / Rebuild
```

means:

> The system is now modifying or reconstructing derived Totals and must not expose a partially constructed replacement state as an ordinary Active state.

Maintenance entry therefore separates:

```text
stable readable state
```

from:

```text
state under reconstruction
```

---

# 12. Successful Maintenance

Successful maintenance establishes a new valid derived state.

The conceptual sequence is:

```text
Maintenance
     ↓
construct / update Totals
     ↓
validate completion
     ↓
publish valid Totals
     ↓
Active
```

Only after successful completion may the rebuilt state become the state observed by normal Balance Query.

---

# 13. Failed Maintenance

Maintenance failure must not result in silent publication of partial Totals.

The architecture distinguishes two cases.

### Case A — Previous valid state remains available

If maintenance fails while the previously published Totals state remains intact and valid, the system may retain that state as the readable state.

The failed maintenance attempt itself must not publish partial state.

Conceptually:

```text
Active
   ↓
Maintenance
   ↓
failure
   ↓
previous valid state retained
```

The exact operational representation of the failure is an implementation concern, but the visibility invariant remains mandatory.

---

### Case B — Previous valid state is no longer trustworthy

If maintenance failure means that the previously published Totals can no longer be trusted, the system must not continue presenting those Totals as a valid Active state.

Conceptually:

```text
Maintenance
     ↓
failure
     ↓
Totals validity uncertain
     ↓
recovery required
     ↓
Rebuild
     ↓
validated Totals
     ↓
Active
```

This is the architectural role of an indeterminate state.

---

# 14. Failure State Model

Step 6 uses three outcome categories:

```text
Success
Failure
Indeterminate
```

These describe operation outcomes and consistency knowledge.

---

## 14.1 Success

`Success` means:

> The requested operation completed and the resulting derived state is known to satisfy the relevant contract.

For maintenance, success permits publication of the resulting Totals state.

---

## 14.2 Failure

`Failure` means:

> The requested operation did not complete, and the system knows that no invalid derived state was published as the new readable state.

Failure may therefore leave the previously valid state intact.

---

## 14.3 Indeterminate

`Indeterminate` means:

> The system cannot establish with sufficient certainty whether the intended derived-state transition completed consistently.

Indeterminate must not be interpreted as success.

The system must not assume that Totals are correct merely because an operation terminated without a definitive success observation.

---

# 15. Movement Persistence and Totals Maintenance Boundary

The critical consistency relationship is:

```text
Movement Persistence
        +
Totals Maintenance
        ↓
Logical Consistency Boundary
```

This boundary defines when a persisted Movement Fact and its corresponding Totals contribution are considered logically synchronized.

The architecture must explicitly address the transition:

```text
Movement persisted
      ↓
Totals update
```

because these are logically related operations.

---

# 16. Persisted Movement / Failed Totals Update

Consider:

```text
Movement persisted
      ↓
Totals update failed
```

The architecture must not treat this as equivalent to:

```text
Movement never existed
```

The Movement Fact remains authoritative if it was successfully persisted.

Therefore, if its Totals contribution was not successfully applied, the derived state may become inconsistent.

The architectural consequence is:

```text
Persisted Movement Fact
        ↓
Totals contribution missing
        ↓
Derived state potentially inconsistent
        ↓
Recovery required
```

The required recovery mechanism is rebuild from persisted Movement Facts.

---

# 17. Rebuild as Recovery

Rebuild is the canonical recovery mechanism for derived Totals.

Its semantic model is:

```text
Persisted Movement Facts
        ↓
      scan
        ↓
   deterministic
    aggregation
        ↓
   Fresh Totals
```

Rebuild therefore does not attempt to calculate a correction from an existing potentially-invalid aggregate.

---

# 18. Rebuild Source

The rebuild input is:

> The set of persisted Movement Facts belonging to the Register and covered by the Register's aggregation contract.

The rebuild must use the same semantic Movement Fact interpretation that defines normal Totals maintenance.

The source is not:

* previous Totals;
* cached Balance Results;
* previously computed aggregates;
* arbitrary external state.

---

# 19. Rebuild Determinism

For the same authoritative Movement Fact set and the same applicable aggregation semantics:

```text
Rebuild(Facts)
```

must produce the same semantic Totals state.

Therefore, rebuild must not depend on:

* storage layout;
* arbitrary iteration ordering;
* runtime object identity;
* uncontrolled current time;
* uncontrolled external state.

Any ordering used internally must not change the resulting semantic aggregate.

---

# 20. Rebuild Isolation

A rebuild must be isolated from ordinary Balance Query visibility.

The system must not expose:

```text
partial rebuild state
```

as:

```text
Current Total
```

during ordinary query execution.

The conceptual model is:

```text
Published Totals
       │
       │  Balance Query
       ▼
stable readable state


Rebuild
       │
       ▼
Private / non-published Totals
       │
       │ successful completion
       ▼
Published Totals
```

---

# 21. Visibility Rule

The central visibility invariant is:

> A Balance Query may observe only a complete published Totals state.

It must never observe an aggregate that is:

* partially rebuilt;
* partially applied;
* partially removed;
* otherwise known to be incomplete.

This prevents transient maintenance state from becoming externally observable as a Balance Result.

---

# 22. Atomic Publication Concept

Step 6 defines an architectural requirement for publication, not a particular storage mechanism.

A rebuild should conceptually operate as:

```text
Existing Published Totals
          │
          │ remains isolated
          │
          ▼
   Build Replacement
          │
          ▼
     Validate Result
          │
          ▼
    Publish Replacement
          │
          ▼
   New Published Totals
```

The publication boundary is the point at which the replacement becomes eligible for ordinary Balance Query.

The architecture does not prescribe whether this is implemented through:

* atomic replacement;
* versioned state;
* snapshot publication;
* transactional storage;
* another mechanism.

The implementation must nevertheless preserve the same semantic visibility guarantee.

---

# 23. Maintenance Isolation

Maintenance isolation has three requirements.

### Requirement 1 — No partial visibility

A partial maintenance result cannot be returned by Balance Query.

### Requirement 2 — No implicit success

Starting maintenance does not make the resulting Totals valid.

### Requirement 3 — Explicit publication

Only successful completion may establish a replacement Totals state as readable.

---

# 24. Apply Operation

`apply Movement` maintains Totals incrementally when a Movement Fact becomes part of the Register's authoritative fact set.

Conceptually:

```text
Movement Fact
     ↓
derive contribution
     ↓
TotalsKey
     ↓
apply contribution
     ↓
Current Total
```

The operation must use the same aggregation semantics as the Totals Engine.

---

# 25. Apply Boundary

Apply is not a general-purpose mutation of Balance.

It is a maintenance operation on derived Totals.

The operation must not:

* create a different Balance semantic;
* bypass TotalsKey;
* introduce alternative aggregation rules;
* mutate unrelated Register state.

---

# 26. Remove Operation

`remove Movement contribution` removes the contribution of a previously applied Movement Fact from derived Totals.

Conceptually:

```text
Movement Fact
     ↓
derive contribution
     ↓
TotalsKey
     ↓
remove contribution
     ↓
Current Total
```

The removal must use the same contribution semantics that would have been applied for that Movement Fact.

---

# 27. Apply / Remove Symmetry

The architecture requires semantic symmetry:

```text
apply(Movement)
```

and:

```text
remove(Movement)
```

must operate on the same contribution definition.

If a Movement contributes:

```text
C
```

then:

```text
apply → +C
remove → -C
```

must restore the corresponding prior aggregate, subject to the Register's contribution semantics.

---

# 28. Rebuild Versus Incremental Maintenance

The architecture defines two complementary maintenance mechanisms.

### Incremental maintenance

```text
Movement
   ↓
apply/remove contribution
   ↓
Totals
```

Used for normal maintenance.

### Full rebuild

```text
Persisted Movement Facts
          ↓
       aggregate
          ↓
    Fresh Totals
```

Used for reconstruction and recovery.

Neither mechanism changes the underlying semantic definition of Balance.

---

# 29. Rebuild as a Semantic Reconciliation Mechanism

Rebuild is more than an optimization or cache refresh.

It is the mechanism by which derived Totals can be reconciled with authoritative Movement Facts.

Therefore:

```text
Movement Facts = authority
Totals = derived representation
Rebuild = reconciliation
```

This relationship is fundamental to the architecture.

---

# 30. Idempotency

Step 6 requires maintenance operations to have explicitly defined repeated-execution semantics.

The central rule is:

> Repeating an operation must not create an unintended additional contribution.

---

# 31. Apply Idempotency

A naïve repeated operation:

```text
apply(Movement)
apply(Movement)
```

must not silently result in:

```text
Contribution × 2
```

unless the architecture explicitly identifies the two operations as two distinct contributions.

For the same logical Movement Fact, the maintenance architecture must distinguish:

```text
first application
```

from:

```text
duplicate application
```

The implementation must therefore have a stable way to establish whether a Movement contribution has already been incorporated.

The exact identity mechanism is a Concrete API / implementation concern.

The invariant is architectural.

---

# 32. Remove Idempotency

Likewise:

```text
remove(Movement)
remove(Movement)
```

must not silently remove the same logical contribution twice.

Once the contribution is known to have been removed, repeating the removal must not create an invalid negative contribution.

Again, the concrete tracking mechanism is implementation-specific.

---

# 33. Apply / Remove State Transition

The conceptual contribution lifecycle is:

```text
Not Applied
     │
     │ apply
     ▼
Applied
     │
     │ remove
     ▼
Not Applied
```

Repeated operations must preserve this logical state machine.

Invalid transitions must not silently corrupt Totals.

---

# 34. Rebuild Idempotency

Rebuild must be idempotent with respect to the same authoritative Movement Fact set.

Conceptually:

```text
Rebuild(Facts)
      ↓
Totals A

Rebuild(Facts)
      ↓
Totals B
```

must produce:

```text
semantic(A) == semantic(B)
```

provided that the authoritative input and applicable aggregation semantics are unchanged.

Rebuild must never accumulate on top of its own previous result.

It always reconstructs from authoritative Movement Facts.

---

# 35. Rebuild Must Not Double-Apply

The following model is prohibited:

```text
Existing Totals
      ↓
Rebuild
      ↓
Existing Totals + all Movement contributions
```

because this can produce double contributions.

The required model is:

```text
Existing Totals
      │
      │ ignored as source of truth
      ▼
Persisted Movement Facts
      ↓
Fresh aggregation
      ↓
Replacement Totals
```

---

# 36. Recovery Model

Recovery is defined as returning the Register from a state where derived Totals cannot be trusted to a state where they are once again valid.

The conceptual recovery sequence is:

```text
Inconsistent / Indeterminate
          ↓
      Maintenance
          ↓
       Rebuild
          ↓
   Validate Totals
          ↓
       Publish
          ↓
        Active
```

The authoritative Movement Facts remain the recovery input.

---

# 37. Recovery Invariant

A successful recovery must establish:

```text
Current Totals
      =
Totals derived from
authoritative Movement Facts
```

according to the applicable Totals Engine semantics.

Recovery must not depend on knowing exactly which incremental maintenance operation previously failed.

This is an important property.

Even when the exact history of maintenance failure is uncertain, the system can recover by reconstructing derived state from authoritative facts.

---

# 38. Failure Recovery After Persisted Movement

Consider:

```text
Movement persisted
      ↓
apply failed
      ↓
Totals inconsistent
```

Recovery is:

```text
Persisted Movement Facts
        ↓
      rebuild
        ↓
Fresh Totals
```

No manual compensating contribution is required as the semantic recovery mechanism.

This prevents recovery logic from depending on assumptions about the exact failure point.

---

# 39. Failure Recovery During Rebuild

Consider:

```text
Rebuild started
      ↓
Rebuild failed
```

The failed intermediate result must not be published.

Conceptually:

```text
Published State
      │
      ├──── remains isolated if valid
      │
      ▼
Rebuild Attempt
      │
      └── failure
             │
             ▼
      no partial publication
```

If the previous published state remains valid, it may remain the readable state.

If it is no longer trustworthy, the Register remains in a state requiring successful recovery before ordinary Active visibility is restored.

---

# 40. No Silent Recovery

A failed maintenance operation must not be silently interpreted as successful recovery.

The system must retain enough lifecycle information to distinguish:

```text
successfully maintained
```

from:

```text
maintenance attempted but not completed
```

and:

```text
state validity is uncertain
```

---

# 41. Balance Query During Maintenance

Balance Query remains a read operation.

It does not:

* start maintenance;
* perform rebuild;
* repair Totals;
* infer missing contributions;
* inspect Movement Facts to compensate for derived-state inconsistency.

The query therefore depends on the lifecycle visibility contract.

---

# 42. Balance Query Visibility Semantics

When the Register is `Active` and its published Totals are valid:

```text
Balance Query
      ↓
Current Total
      ↓
Balance Result
```

is permitted.

During maintenance, the query must not observe a partially constructed replacement.

The architecture therefore requires a defined maintenance visibility policy.

The default Step 6 semantic policy is:

> A Register under maintenance does not expose an incomplete replacement Totals state as an ordinary Balance Result.

If the existing published state remains valid and the architecture permits continued reads from that stable publication, those reads may continue against that published state.

If no valid published state exists, the query must not fabricate a Balance Result from incomplete or indeterminate Totals.

The exact public error/status representation belongs to the Concrete API stage.

---

# 43. Maintenance Does Not Change Balance Semantics

Maintenance isolation must not introduce a second definition of Balance.

For example, the architecture does not permit:

```text
Active Balance
```

to mean one thing and:

```text
Maintenance Balance
```

to mean another.

The only difference is whether a valid published Totals state is currently available for observation.

---

# 44. Logical Consistency Boundary

The architecture defines a logical consistency boundary around the relationship between Movement persistence and Totals maintenance.

Conceptually:

```text
┌─────────────────────────────────────────────┐
│       Logical Consistency Boundary          │
│                                             │
│  Movement Persistence + Totals Maintenance  │
│                                             │
└─────────────────────────────────────────────┘
                      │
                      ▼
              Published Totals
                      │
                      ▼
               Balance Query
```

Balance Query operates after this boundary.

It does not participate in establishing consistency.

---

# 45. Boundary Responsibility

The consistency boundary is responsible for ensuring that after successful completion:

```text
Persisted Movement Facts
        ↔
Published Totals
```

are semantically aligned.

If the boundary cannot establish this relationship, it must not claim successful completion.

---

# 46. Consistency Is Logical, Not Necessarily Physical

The phrase "logical consistency boundary" does not prescribe a particular physical transaction mechanism.

It does not require:

* one database transaction;
* a specific storage provider;
* a distributed transaction;
* a particular locking model.

It defines the semantic point at which the system can state:

> The persisted facts and the published derived state satisfy the Register Totals contract.

---

# 47. Atomicity of Publication

The architecture requires semantic atomicity of publication.

This means:

```text
old valid state
```

or:

```text
new valid state
```

may be visible.

The system must not expose:

```text
partially old + partially new
```

as the result of a rebuild.

The implementation mechanism is intentionally left open.

---

# 48. Maintenance and Movement Ordering

Step 6 does not introduce a universal global ordering across all Movement operations.

However, within the scope of one Register, maintenance must preserve the semantic relationship between:

* authoritative Movement Facts;
* contribution state;
* published Totals.

The implementation must prevent an operation ordering from producing an observable state that violates the defined lifecycle invariants.

---

# 49. Concurrent Maintenance

This Architecture Definition does not establish a general distributed concurrency model.

However, it does establish one architectural restriction:

> Multiple maintenance operations must not independently publish conflicting Totals states.

Concrete concurrency control may later use:

* serialization;
* exclusive maintenance ownership;
* version checks;
* optimistic publication;
* another mechanism.

The mechanism is deferred.

The invariant is not deferred.

---

# 50. Maintenance Ownership

A Register must have a single logically authoritative maintenance state at a time.

Conceptually:

```text
Register
   ↓
Maintenance
   ↓
one active maintenance lifecycle
```

This prevents:

```text
Rebuild A
     +
Rebuild B
     +
independent publication
```

from producing ambiguous final state.

---

# 51. Incremental Maintenance During Rebuild

The interaction between normal `apply/remove` operations and a full rebuild must be explicitly controlled.

The architecture does not permit an uncontrolled situation where:

```text
Rebuild reads Facts
        +
new Movement applied
        +
rebuild publishes old snapshot
```

and thereby silently loses the new contribution.

The implementation must establish a consistent relationship between the rebuild input and the resulting published Totals.

Possible implementation mechanisms are deferred, but the semantic requirement is mandatory.

---

# 52. Rebuild Input Boundary

A rebuild must have a well-defined logical input boundary.

Conceptually:

```text
Movement Fact Set S
        ↓
Rebuild(S)
        ↓
Totals T
```

The published `T` must correspond to the authoritative facts represented by the rebuild's defined input boundary.

The implementation must therefore prevent ambiguous publication where the input fact set and publication point cannot be related.

---

# 53. Register Lifecycle Invariants

The following invariants are mandatory.

### Invariant L1 — Authoritative facts

Persisted Movement Facts are the source of truth for rebuild.

### Invariant L2 — Derived totals

Register Totals are derived state.

### Invariant L3 — No partial visibility

Partial maintenance state is never exposed as a normal Balance Result.

### Invariant L4 — Rebuild independence

Rebuild does not depend on previous Totals being correct.

### Invariant L5 — Deterministic rebuild

The same authoritative Movement Fact set produces the same semantic Totals.

### Invariant L6 — Idempotent rebuild

Repeating rebuild for the same input does not accumulate contributions.

### Invariant L7 — Apply protection

Repeated application of the same logical Movement contribution must not double-count it.

### Invariant L8 — Remove protection

Repeated removal of the same logical Movement contribution must not remove it multiple times.

### Invariant L9 — Explicit failure

Maintenance failure must not be represented as successful completion.

### Invariant L10 — Recovery

An invalid or indeterminate derived state can be recovered by rebuilding from authoritative Movement Facts.

### Invariant L11 — Query isolation

Balance Query does not perform maintenance or recovery.

### Invariant L12 — Publication integrity

Only a complete valid Totals state may become the published readable state.

---

# 54. Architectural State Machine

The lifecycle can be represented as:

```text
                    ┌───────────────┐
                    │    Created    │
                    └───────┬───────┘
                            │
                         activate
                            │
                            ▼
                    ┌───────────────┐
              ┌────►│     Active    │◄────┐
              │     └───────┬───────┘     │
              │             │              │
              │       maintenance          │
              │             │              │
              │             ▼              │
              │     ┌─────────────────┐    │
              │     │ Maintenance /   │    │
              │     │ Rebuild         │    │
              │     └───────┬─────────┘    │
              │             │              │
              │          success           │
              │             │              │
              └─────────────┘              │
                                            │
                          recovery success ─┘
```

Failure does not automatically create a successful transition.

---

# 55. Extended Failure State Model

For architectural reasoning, the lifecycle may be understood as:

```text
Created
   ↓
Active
   ↓
Maintenance
   ├──────── success ───────► Active
   │
   ├──────── failure ───────► previous valid state
   │
   └────── indeterminate ───► Recovery Required
                                      │
                                      ▼
                                   Rebuild
                                      │
                                      ▼
                                    Active
```

`Recovery Required` is a logical condition rather than necessarily a separately persisted public lifecycle state.

The concrete representation is deferred to API and implementation design.

---

# 56. Maintenance Operations

Step 6 establishes exactly three conceptual maintenance operations:

```text
apply Movement
remove Movement contribution
rebuild Register totals
```

Their responsibilities are distinct.

| Operation | Purpose                                      | Source                                |
| --------- | -------------------------------------------- | ------------------------------------- |
| Apply     | Incrementally add a Movement contribution    | Movement Fact                         |
| Remove    | Incrementally remove a Movement contribution | Movement Fact / contribution identity |
| Rebuild   | Reconstruct complete Totals                  | Persisted Movement Facts              |

---

# 57. Apply Semantics

Apply:

1. identifies the logical Movement contribution;
2. derives its TotalsKey;
3. derives the contribution;
4. incorporates that contribution into derived Totals;
5. establishes the contribution as incorporated.

The operation must not alter the meaning of the Movement Fact itself.

---

# 58. Remove Semantics

Remove:

1. identifies the logical Movement contribution;
2. derives the same semantic contribution;
3. removes that contribution from derived Totals;
4. establishes that the contribution is no longer incorporated.

The operation must not delete or mutate the authoritative Movement Fact merely because its contribution is removed.

---

# 59. Rebuild Semantics

Rebuild:

1. establishes a maintenance boundary;
2. determines the authoritative Movement Fact input;
3. creates a fresh Totals state;
4. processes the Movement Facts using the Totals Engine;
5. validates the resulting derived state;
6. publishes the replacement state;
7. exits maintenance successfully.

At no point does rebuild incrementally modify the old published aggregate as its semantic source.

---

# 60. Rebuild and Empty Registers

A Register with no applicable persisted Movement Facts is a valid rebuild input.

The result is a valid empty Totals state according to the Register's aggregation semantics.

Conceptually:

```text
No Movement Facts
        ↓
Rebuild
        ↓
Empty / zero aggregate state
```

The exact representation of an empty Current Total remains governed by the Step 5 Balance semantics.

Step 6 does not redefine that representation.

---

# 61. Rebuild and Deleted / Removed Movements

If a Movement Fact is no longer part of the authoritative persisted fact set, rebuild must not include it.

Therefore:

```text
Current Totals
```

is not repaired by attempting to remember whether an old contribution had previously been applied.

Instead:

```text
Authoritative Movement Fact Set
        ↓
Rebuild
```

determines the resulting state.

---

# 62. Rebuild as a Trust Boundary

After successful rebuild publication:

```text
Published Totals
```

may again be trusted as derived state for Balance Query.

This creates a useful architectural trust model:

```text
Authoritative Movement Facts
          ↓
       Rebuild
          ↓
Validated Totals
          ↓
Published Totals
          ↓
Balance Query
```

---

# 63. What Rebuild Does Not Do

Rebuild does not:

* modify Movement Facts;
* reinterpret Balance semantics;
* repair arbitrary business data;
* create missing Movement Facts;
* consult old Totals as authoritative input;
* silently ignore unsupported Movement Facts;
* compensate for malformed authoritative state by inventing values.

If authoritative Movement Facts cannot be processed according to the Totals contract, rebuild fails rather than fabricating a result.

---

# 64. Unsupported or Invalid Movement Facts

A Movement Fact that cannot be interpreted according to the established Totals contract must not silently disappear from rebuild.

The architecture requires an explicit failure.

Conceptually:

```text
Unsupported / invalid fact
        ↓
Rebuild cannot establish valid Totals
        ↓
Failure
```

This preserves the distinction between:

```text
zero contribution
```

and:

```text
unknown / invalid contribution
```

---

# 65. Error Semantics

Step 6 distinguishes semantic error classes.

### Maintenance Failure

The requested maintenance operation did not establish the intended derived state.

### Rebuild Failure

The system could not construct a valid Totals state from authoritative Movement Facts.

### Indeterminate Maintenance Outcome

The system cannot establish whether the resulting Totals state is valid.

### Recovery Failure

A rebuild or other recovery operation failed to restore a valid derived state.

Concrete exception and error types are deferred to Concrete API Design.

---

# 66. No Implicit Compensation

If:

```text
Movement persisted
```

but:

```text
Totals update failed
```

the architecture does not require a compensating deletion of the Movement Fact.

The authoritative fact remains authoritative.

Instead:

```text
Movement Fact
        ↓
Recovery / Rebuild
        ↓
correct Totals
```

is the preferred semantic recovery path.

---

# 67. Failure Matrix

The initial architectural failure matrix is:

| Situation                                  | Movement Facts | Published Totals                      | Outcome             |
| ------------------------------------------ | -------------- | ------------------------------------- | ------------------- |
| Apply succeeds                             | valid          | updated                               | Active              |
| Apply fails before publication             | valid          | previous valid state                  | Failure             |
| Apply outcome indeterminate                | valid          | validity uncertain                    | Recovery required   |
| Movement persisted, Totals update failed   | valid          | potentially stale                     | Rebuild required    |
| Rebuild succeeds                           | valid          | replaced with fresh state             | Active              |
| Rebuild fails, old state valid             | valid          | old state retained if safely isolated | Maintenance failure |
| Rebuild fails, old state invalid/uncertain | valid          | not trusted                           | Recovery required   |
| Rebuild outcome indeterminate              | valid          | validity uncertain                    | Recovery required   |
| Rebuild repeated                           | same facts     | same semantic result                  | Idempotent          |

---

# 68. Recovery Guarantees

The architecture guarantees recoverability under the following condition:

> The authoritative Movement Facts remain available and interpretable according to the Register Totals contract.

If that condition holds, derived Totals can be reconstructed independently of their previous state.

This is the fundamental recoverability property of Step 6.

---

# 69. Loss of Authoritative Facts

Step 6 does not define recovery from loss or corruption of the authoritative Movement Facts themselves.

If the source of truth is unavailable or invalid, Totals cannot be reconstructed according to the guarantees of this step.

That situation belongs to the persistence and data-integrity architecture.

---

# 70. Relationship to Step 5

Step 5 established:

```text
TotalsKey
      ↓
Current Total
      ↓
Balance Query
      ↓
Balance Result
```

Step 6 establishes how `Current Total` is maintained.

The relationship is therefore:

```text
Step 5:
"What does Balance mean?"

Step 6:
"How is the derived state used by Balance kept valid and recoverable?"
```

Step 6 must not alter the answer established by Step 5.

---

# 71. Boundary Between Read and Maintenance

The architecture establishes a strict separation:

```text
                 ┌─────────────────────┐
                 │ Maintenance Side    │
                 │                     │
Movement Facts → │ apply/remove/rebuild│
                 └──────────┬──────────┘
                            │
                     Published Totals
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Read Side           │
                 │                     │
                 │ Balance Query       │
                 └─────────────────────┘
```

Balance Query does not cross back into the maintenance side.

---

# 72. No Read-Time Repair

Balance Query must not contain logic equivalent to:

```text
if totals_missing:
    rebuild()
```

or:

```text
if totals_suspect:
    reconstruct()
```

Read-time repair would blur the consistency boundary and make query semantics dependent on maintenance behavior.

Recovery is an explicit lifecycle operation.

---

# 73. Maintenance and Determinism

Maintenance must preserve the deterministic aggregation semantics already established for Totals.

For the same:

* Movement Facts;
* TotalsKey semantics;
* contribution semantics;
* relevant Register configuration;

the resulting Totals must be semantically identical regardless of whether they were obtained through:

```text
incremental maintenance
```

or:

```text
full rebuild
```

where both operate over the same authoritative fact set.

---

# 74. Incremental / Rebuild Equivalence

The core consistency property is:

```text
apply all applicable Movement contributions
```

and:

```text
rebuild from all applicable persisted Movement Facts
```

must converge to the same semantic Totals state.

Conceptually:

```text
          ┌── incremental apply ──┐
Facts ────┤                       ├──► Totals
          └────── rebuild ────────┘
```

The two paths must not define different Balance semantics.

---

# 75. Maintenance as Derived-State Infrastructure

Step 6 treats Totals maintenance as infrastructure supporting Balance.

It is not itself a business operation equivalent to posting.

The business-level Movement Fact remains the semantic input.

Totals maintenance is responsible for preserving an efficient derived representation of those facts.

---

# 76. Architectural Dependency Direction

The intended dependency direction is:

```text
Movement Facts
      ↓
Totals Engine
      ↓
Totals Maintenance
      ↓
Current Totals
      ↓
Balance Query
```

The reverse dependency is prohibited at the semantic level:

```text
Balance Query
      ↓
Movement mutation
```

or:

```text
Balance Query
      ↓
Totals repair
```

---

# 77. Lifecycle Independence from Balance Queries

Register lifecycle transitions must not be triggered implicitly by ordinary reads.

For example:

```text
Balance Query
```

must not:

* activate a Register;
* enter maintenance;
* exit maintenance;
* trigger rebuild.

Lifecycle transitions belong to lifecycle and maintenance operations.

---

# 78. Maintenance Isolation from Business Semantics

Maintenance must not reinterpret business meaning.

For example, a rebuild must not decide:

```text
"This Movement looks unusual, therefore ignore it."
```

The Totals Engine and established Movement semantics determine contribution.

Maintenance preserves those semantics.

---

# 79. Architectural Invariants Summary

The complete Step 6 invariant set is:

```text
I1  Movement Facts are authoritative.
I2  Totals are derived state.
I3  Rebuild uses Movement Facts, not old Totals.
I4  Rebuild is deterministic.
I5  Rebuild is idempotent.
I6  Apply cannot double-count a logical contribution.
I7  Remove cannot double-remove a logical contribution.
I8  Incremental and rebuild paths converge semantically.
I9  Partial maintenance state is never published.
I10 Balance Query sees only a valid published Totals state.
I11 Maintenance failure is not success.
I12 Indeterminate state requires explicit recovery.
I13 Rebuild is the canonical derived-state recovery mechanism.
I14 Recovery does not require knowledge of the exact failed incremental step.
I15 Published Totals are atomically replaced at the semantic level.
I16 Balance Query does not perform maintenance.
I17 Lifecycle transitions are explicit.
I18 Authoritative Movement Facts are not compensated away merely because
    derived Totals maintenance failed.
```

---

# 80. Architectural Acceptance Criteria

Step 6 Architecture Definition is complete when the architecture can answer all of the following questions without ambiguity.

### Register lifecycle

* What does `Created` mean?
* What does `Active` mean?
* What does `Maintenance / Rebuild` mean?
* Which transitions are valid?
* What happens after maintenance failure?

### Totals maintenance

* How is a Movement contribution applied?
* How is a Movement contribution removed?
* How is a Register rebuilt?
* What prevents duplicate contributions?

### Rebuild

* What is the rebuild source of truth?
* Can rebuild operate without trusting old Totals?
* Is rebuild deterministic?
* Is rebuild idempotent?
* What happens if rebuild fails?

### Consistency

* What constitutes the logical consistency boundary?
* What happens if Movement persistence succeeds but Totals maintenance fails?
* How is an indeterminate state represented semantically?
* How is consistency restored?

### Visibility

* Can Balance Query observe partial rebuild state?
* Can a replacement Totals state become visible before successful completion?
* What happens when no valid published Totals state exists?

### Recovery

* What is the canonical recovery mechanism?
* Can recovery succeed without reconstructing the exact failed maintenance history?
* Does successful rebuild restore Active semantics?

---

# 81. Open Questions for Architecture Review

The following points should be explicitly reviewed before moving to the final Contract document.

## 81.1 Maintenance visibility policy

Confirm whether the intended policy is:

```text
Maintenance with valid previous publication
        ↓
Balance Query may continue reading previous published state
```

versus:

```text
Maintenance
        ↓
Balance Query always unavailable
```

The current definition favors preserving a valid published snapshot where possible, because it avoids exposing partial state without unnecessarily invalidating an already valid publication.

---

## 81.2 Public representation of Recovery Required

The architecture currently treats `Recovery Required` as a logical condition.

Architecture Review should determine whether the lifecycle contract needs a first-class persisted lifecycle state or whether it can remain an operational condition.

---

## 81.3 Exact apply/remove contribution identity

Architecture Review should confirm what constitutes:

```text
same logical Movement contribution
```

This is necessary for precise idempotency semantics.

The mechanism should remain outside this Architecture Definition.

---

## 81.4 Concurrent Movement and Rebuild

Architecture Review should confirm the required semantic ordering between:

```text
Movement persistence
```

and:

```text
Rebuild input snapshot
```

The implementation mechanism remains deferred.

---

## 81.5 Publication mechanism

The architecture intentionally requires semantic atomic publication without selecting a physical mechanism.

Concrete API / implementation work may determine whether the implementation uses:

* replacement;
* versioning;
* snapshotting;
* transaction boundaries;
* another mechanism.

---

# 82. Recommended Contract-Level Model

The resulting conceptual model is:

```text
                  AUTHORITATIVE
                  ─────────────
                  Movement Facts
                        │
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
        apply/remove            rebuild
             │                     │
             └──────────┬──────────┘
                        │
                        ▼
                Derived Totals
                        │
                 publication
                        │
                        ▼
                Published Totals
                        │
                        ▼
                 Balance Query
                        │
                        ▼
                 Balance Result
```

The lifecycle surrounding this model is:

```text
Created
   ↓
Active
   ↓
Maintenance / Rebuild
   ├── success ───────────────► Active
   │
   ├── failure + valid state ─► previous publication
   │
   └── indeterminate/invalid ─► Recovery Required
                                      │
                                      ▼
                                   Rebuild
                                      │
                                      ▼
                                    Active
```

---

# 83. Architectural Decision

Step 6 establishes the following architectural position:

> Register Totals are maintained derived state, not authoritative register facts.

> Persisted Movement Facts are the authoritative source for reconstruction.

> Incremental apply/remove operations maintain the derived state during normal operation.

> Full rebuild reconstructs Totals exclusively from authoritative Movement Facts and is the canonical recovery mechanism for derived-state inconsistency.

> Maintenance must be isolated from Balance Query visibility so that no partial derived state can be observed as a Balance Result.

> Successful maintenance publishes a complete valid Totals state. Failed or indeterminate maintenance must not be represented as successful completion.

> Repeated maintenance operations must not create duplicate contributions, and repeated rebuilds over the same authoritative fact set must produce the same semantic Totals.

> The Movement Persistence + Totals Maintenance boundary is the logical consistency boundary. Balance Query operates strictly after that boundary and does not perform repair or recovery.

---

# 84. Step 6 Architectural Boundary

The resulting architectural boundary is:

```text
┌────────────────────────────────────────────────────┐
│              REGISTER MAINTENANCE                  │
│                                                    │
│  Persisted Movement Facts                          │
│          │                                         │
│          ├── apply                                  │
│          ├── remove                                 │
│          └── rebuild                                │
│                    │                               │
│                    ▼                               │
│              Derived Totals                        │
│                    │                               │
│             publication boundary                  │
└────────────────────┼───────────────────────────────┘
                     │
                     ▼
              Published Totals
                     │
                     ▼
               Balance Query
                     │
                     ▼
              Balance Result
```

The maintenance side owns:

```text
lifecycle
consistency
derived-state maintenance
rebuild
recovery
publication
```

The read side owns:

```text
query
```

and does not repair the maintenance side.

---

# 85. Step 6 Exit Criteria

Step 6 may proceed from Architecture Definition to Architecture Review when:

* the Register lifecycle is explicitly defined;
* maintenance states are defined;
* valid transitions are defined;
* apply/remove/rebuild responsibilities are separated;
* Movement Facts are explicitly identified as rebuild source of truth;
* rebuild does not depend on previous Totals;
* maintenance visibility semantics are defined;
* partial state cannot be exposed;
* Success / Failure / Indeterminate semantics are defined;
* apply idempotency is addressed;
* remove idempotency is addressed;
* rebuild idempotency is addressed;
* Movement persistence / Totals maintenance consistency boundary is defined;
* recovery from derived-state inconsistency is defined;
* Balance Query remains unchanged;
* non-goals are explicit;
* remaining open questions are isolated for Architecture Review rather than silently decided during implementation.

---

# 86. Relationship to Future Concrete API Design

This document intentionally does not define concrete implementation symbols.

The following are deferred:

* class names;
* protocol names;
* method signatures;
* exception hierarchy;
* persistence schema;
* locking primitives;
* transaction implementation;
* versioning mechanism;
* snapshot representation;
* exact lifecycle enum;
* exact maintenance result types.

Those decisions belong to the next stage only after the architecture is approved.

The architectural contract established here must remain stable while the Concrete API is designed.

---

# 87. Final Architectural Principle

The essential Step 6 model is:

```text
                 FACTS ARE AUTHORITATIVE
                          │
                          ▼
                ┌──────────────────┐
                │     Movement     │
                │      Facts       │
                └────────┬─────────┘
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
          Incremental             Rebuild
        apply / remove               │
             │                       │
             └───────────┬───────────┘
                         ▼
                  Derived Totals
                         │
                   publication
                         ▼
                 Valid Published
                     Totals
                         │
                         ▼
                   Balance Query
                         │
                         ▼
                  Balance Result
```

And the recovery principle is:

```text
Derived state may become invalid.
Authoritative facts must remain authoritative.
Therefore derived state must always be reconstructible.
```

This is the fundamental lifecycle and maintenance guarantee introduced by Phase 7, Step 6.
