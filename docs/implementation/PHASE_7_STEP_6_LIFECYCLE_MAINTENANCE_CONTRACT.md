# Phase 7 — Step 6

# Lifecycle & Maintenance Contract

**Document:** `PHASE_7_STEP_6_LIFECYCLE_MAINTENANCE_CONTRACT.md`
**Phase:** 7 — Register Totals & Balance
**Step:** 6 — Lifecycle & Maintenance
**Status:** Architecture Contract — Final
**Previous Step:** Step 5 — Balance Query
**Next Step:** Step 6 — Concrete API Design

---

## 1. Purpose

This document defines the semantic contract for the lifecycle, maintenance, consistency, visibility, failure handling, idempotency, and recovery of Register Totals.

The purpose of Step 6 is to define how derived Register Totals are maintained and recovered over time while preserving the semantics established by Step 5 — Balance Query.

The contract establishes:

* the distinction between authoritative Movement Facts and derived Totals;
* the lifecycle of Totals maintenance;
* the consistency model;
* incremental maintenance operations;
* full rebuild semantics;
* idempotency requirements;
* failure and indeterminate-operation semantics;
* recovery semantics;
* maintenance visibility rules;
* publication atomicity;
* interaction with Balance Query;
* maintenance isolation requirements.

This document defines semantic behavior only.

Concrete class names, protocols, method signatures, persistence mechanisms, locking mechanisms, versioning strategies, and other implementation details are deferred to the Concrete API Design.

---

# 2. Scope

Step 6 covers:

1. Register Totals lifecycle;
2. lifecycle state and consistency state;
3. incremental Totals maintenance;
4. Movement contribution application;
5. Movement contribution removal;
6. full Totals rebuild;
7. rebuild source of truth;
8. deterministic rebuild semantics;
9. idempotency;
10. incremental/rebuild equivalence;
11. failure semantics;
12. indeterminate operation semantics;
13. recovery;
14. maintenance visibility;
15. atomic semantic publication;
16. maintenance isolation;
17. Balance Query interaction;
18. consistency boundaries.

---

# 3. Non-Goals

Step 6 does not define:

* reporting;
* historical balance queries;
* period closing;
* accounting period management;
* valuation;
* costing;
* General Ledger integration;
* distributed transactions;
* asynchronous maintenance infrastructure;
* background job infrastructure;
* event-driven maintenance infrastructure;
* reconciliation with external accounting systems;
* a new persistence architecture;
* concrete database transactions;
* concrete locking mechanisms;
* concrete snapshot/versioning implementation;
* UI behavior;
* reporting-specific aggregation.

These may be addressed by later phases if required.

---

# 4. Architectural Context

The Phase 7 pipeline is:

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

Step 5 defined the semantic meaning of Balance Query.

Step 6 defines how the derived Totals used by Balance Query are:

* created;
* maintained;
* replaced;
* validated;
* recovered.

Step 6 MUST NOT redefine the semantic meaning of Balance Query established in Step 5.

---

# 5. Core Architectural Principle

Movement Facts are authoritative.

Register Totals are derived state.

Therefore:

```text
Movement Facts
      ↓
  authoritative
      ↓
Totals
      ↓
    derived
```

If authoritative Movement Facts and derived Totals disagree, the Movement Facts determine the correct state.

Totals MUST be reconstructible from the authoritative Movement Facts under the applicable aggregation contract.

---

# 6. Authoritative State

The authoritative state for a Register is the persisted set of Movement Facts belonging to that Register and covered by the applicable aggregation semantics.

A Movement Fact remains authoritative independently of the success or failure of Totals maintenance.

Failure of Totals maintenance MUST NOT cause an authoritative Movement Fact to be silently deleted, invalidated, ignored, or rewritten merely to preserve derived Totals.

---

# 7. Derived State

Register Totals are derived from Movement Facts.

Derived Totals MAY be maintained incrementally.

Derived Totals MAY also be reconstructed through full rebuild.

Both mechanisms MUST produce semantically equivalent results for the same authoritative Movement Fact set.

---

# 8. Rebuild Source of Truth

A rebuild MUST reconstruct Totals from authoritative persisted Movement Facts.

The conceptual rebuild pipeline is:

```text
Persisted Movement Facts
          ↓
        Rebuild
          ↓
     Fresh Totals
          ↓
       Validate
          ↓
       Publish
```

A rebuild MUST NOT use any of the following as its authoritative source:

* old Totals;
* cached Balance Results;
* runtime-only state;
* previously materialized aggregate state;
* external derived state;
* partially reconstructed state.

Old Totals MAY be retained as a previously published snapshot, but they MUST NOT be treated as the source of truth for reconstruction.

---

# 9. Lifecycle State

The lifecycle state describes the operational phase of the Totals maintenance subsystem.

The lifecycle states are:

* `Created`;
* `Active`;
* `Maintenance`.

The normal lifecycle is:

```text
Created
   ↓
Active
   ↓
Maintenance
   ↓
Active
```

Lifecycle state is intentionally separate from consistency state.

---

# 10. Consistency State

Consistency state describes whether the currently Published Totals correspond to the current authoritative Movement Fact set.

The consistency states are:

* `Valid`;
* `Indeterminate`;
* `Recovery Required`.

---

# 11. Meaning of `Valid`

`Valid` means that the currently Published Totals represent the complete aggregation of the current authoritative Movement Fact set under the applicable Register aggregation contract.

A previously published snapshot is not `Valid` merely because it is structurally complete.

If the authoritative Movement Fact set has changed and the Published Totals have not been successfully updated to represent that new fact set, the previous Totals MUST NOT be considered current-valid.

---

# 12. Meaning of `Indeterminate`

`Indeterminate` means that the system cannot establish whether the currently Published Totals correspond to the current authoritative Movement Fact set.

This state is used when an operation outcome leaves the completion state of a semantic transition uncertain.

An indeterminate operation MUST NOT be treated as successful merely because the requested operation was initiated.

---

# 13. Meaning of `Recovery Required`

`Recovery Required` means that the system knows that the currently Published Totals cannot be treated as current-valid for the authoritative Movement Fact set, or that explicit recovery is required before current-consistent operation can resume.

Typical causes include:

* authoritative Movement Fact persistence succeeded but Totals maintenance failed;
* a maintenance operation failed after changing the authoritative fact boundary;
* consistency was explicitly invalidated by a known failure;
* a previous indeterminate condition was resolved as inconsistent.

Recovery MUST use authoritative Movement Facts.

---

# 14. Lifecycle and Consistency Are Independent Dimensions

Lifecycle state and consistency state MUST NOT be treated as a single state machine.

For example:

```text
Active + Valid
Active + Recovery Required
Maintenance + Valid
Maintenance + Recovery Required
```

are semantically distinguishable states.

`Active + Valid` is the normal operational state.

A system MUST NOT enter or remain in `Active + Valid` unless current consistency with the authoritative Movement Fact set has been established.

---

# 15. Normal Lifecycle

The normal operational lifecycle is:

```text
Created
   ↓
Active + Valid
```

A successful maintenance operation follows:

```text
Active + Valid
       ↓
Maintenance
       ↓
Active + Valid
```

A failed or indeterminate operation MUST NOT automatically restore `Active + Valid`.

---

# 16. Recovery Lifecycle

When consistency is no longer established:

```text
Active
  ↓
Recovery Required
  ↓
Maintenance
  ↓
successful rebuild
  ↓
Active + Valid
```

The concrete representation of `Recovery Required` in the lifecycle/API is deferred to the Concrete API Design, but the semantic transition is fixed by this contract.

---

# 17. Maintenance Boundary

Entering maintenance establishes a logical boundary around the maintenance operation.

A maintenance operation MUST have a clearly defined authoritative input boundary.

For full rebuild, that boundary defines which authoritative Movement Facts belong to the rebuild input.

The system MUST NOT silently mix facts outside the defined rebuild boundary into the replacement Totals.

---

# 18. Maintenance Operations

Step 6 defines three semantic maintenance operations:

1. apply a Movement contribution;
2. remove a Movement contribution;
3. rebuild Register Totals.

Conceptually:

```text
apply Movement
remove Movement
rebuild Register
```

These operations MUST preserve the invariants defined by this contract.

---

# 19. Movement Contribution

A Movement Fact contributes to Register Totals according to the aggregation semantics defined by Phase 7.

A contribution includes:

* Register identity;
* TotalsKey;
* the applicable contribution value;
* the identity of the Movement Fact.

The contribution MUST be derived from the authoritative Movement Fact according to the Register's aggregation contract.

---

# 20. Contribution Identity

A logical contribution is identified by:

```text
Movement Fact Identity + Register Identity
```

Movement Fact Identity alone is insufficient because the same Movement Fact may participate in different Register contexts where the architecture permits such participation.

Register Identity alone is insufficient because distinct Movement Facts remain distinct contributions.

Two different Movement Facts MUST remain distinct contributions even when they have identical:

* TotalsKey;
* quantity;
* dimensions;
* contribution value;
* other aggregation attributes.

---

# 21. Apply Semantics

Applying a Movement contribution means incorporating the contribution of an authoritative Movement Fact into Register Totals.

Conceptually:

```text
Totals := Totals + contribution(Movement)
```

A successful apply MUST result in Totals semantically representing the authoritative fact set including that Movement Fact.

---

# 22. Remove Semantics

Removing a Movement contribution means removing the contribution of an authoritative Movement Fact from Register Totals.

Conceptually:

```text
Totals := Totals - contribution(Movement)
```

Apply and remove MUST use the same contribution definition.

Removal MUST NOT use a different contribution calculation from the corresponding apply operation.

---

# 23. Apply/Remove Symmetry

For a Movement contribution `C`:

```text
apply(C)
remove(C)
```

MUST restore the semantic aggregate to the state that existed before `apply(C)`, assuming no other authoritative facts changed.

This establishes the symmetry requirement between apply and remove.

---

# 24. Apply Idempotency

Applying the same logical contribution more than once MUST NOT double-count the contribution.

For a contribution identified by:

```text
Movement Fact Identity + Register Identity
```

the semantic effect is:

```text
Not Applied
      ↓
   Applied
```

A repeated apply of the same logical contribution MUST NOT produce:

```text
2 × contribution
```

---

# 25. Remove Idempotency

Removing the same logical contribution more than once MUST NOT subtract the contribution multiple times.

The semantic state is:

```text
Applied
    ↓
Not Applied
```

A repeated remove of the same logical contribution MUST have no additional semantic effect.

---

# 26. Conceptual Contribution State

For each logical contribution:

```text
Not Applied
     ↓
   Apply
     ↓
  Applied
     ↓
   Remove
     ↓
Not Applied
```

Repeated application while already `Applied` MUST be idempotent.

Repeated removal while already `Not Applied` MUST be idempotent.

The concrete representation of contribution state is an implementation concern and is deferred.

---

# 27. Full Rebuild

A full rebuild reconstructs Register Totals from authoritative Movement Facts.

The rebuild pipeline is:

```text
1. Establish authoritative input boundary
2. Read authoritative Movement Facts
3. Calculate fresh Totals
4. Validate the replacement Totals
5. Publish the replacement Totals
6. Establish current consistency
```

A rebuild MUST construct a fresh semantic result.

It MUST NOT incrementally repair or mutate an old Totals snapshot as its reconstruction source.

---

# 28. Rebuild Determinism

For the same:

* authoritative Movement Fact set;
* Register aggregation semantics;
* TotalsKey semantics;
* contribution semantics;

a rebuild MUST produce the same semantic Totals.

Rebuild MUST NOT depend on:

* runtime object identity;
* storage provider layout;
* arbitrary iteration order;
* uncontrolled system time;
* unrelated external state;
* previous derived Totals.

---

# 29. Rebuild Idempotency

Repeated rebuilds over the same authoritative Movement Fact set MUST produce semantically equivalent Totals.

Therefore:

```text
rebuild(F)
rebuild(F)
```

MUST be semantically equivalent to:

```text
rebuild(F)
```

A rebuild MUST NOT accumulate effects from previous rebuilds.

---

# 30. Incremental/Rebuild Equivalence

For an authoritative Movement Fact set:

```text
F = {M1, M2, ..., Mn}
```

incremental maintenance:

```text
apply(M1)
apply(M2)
...
apply(Mn)
```

MUST be semantically equivalent to:

```text
rebuild(F)
```

assuming the same aggregation semantics and successful completion.

This is a core Phase 7 invariant.

---

# 31. Rebuild as Recovery

Rebuild is the authoritative recovery mechanism for derived Totals.

If:

```text
Movement Facts = authoritative
Totals = inconsistent
```

the system MUST be able to recover by reconstructing Totals from Movement Facts.

Recovery MUST NOT depend on the correctness of the previously derived Totals.

---

# 32. Authoritative Movement Persistence Followed by Maintenance Failure

If a Movement Fact has been successfully persisted but the corresponding Totals maintenance operation fails, then:

```text
Authoritative Facts = changed
Published Totals = not successfully updated
```

Therefore:

* the persisted Movement Fact MUST remain authoritative;
* the Movement Fact MUST NOT be deleted merely because Totals maintenance failed;
* the previous Published Totals MUST NOT be treated as current-valid;
* consistency MUST become `Recovery Required`, unless the system can establish that the authoritative fact set was not changed;
* recovery MUST be performed from authoritative Movement Facts;
* old Totals MUST NOT be used as the source of recovery.

The previously Published Totals MAY remain physically retained as the last complete published snapshot.

Its physical existence MUST NOT cause it to be treated as current-consistent.

---

# 33. Known Failure Before Authoritative State Changes

If an operation fails before the authoritative Movement Fact set changes, then the existing current-valid Totals MAY remain valid.

Conceptually:

```text
Authoritative Facts = unchanged
Published Totals = unchanged
Consistency = Valid
```

This is distinct from a failure occurring after authoritative persistence.

---

# 34. Failure After Authoritative State Changes

If the authoritative Movement Fact set changes successfully and derived Totals maintenance does not complete successfully, the previous Totals MUST NOT remain classified as `Valid`.

The required semantic state is:

```text
Authoritative Facts = new state
Published Totals = old state
Consistency = Recovery Required
```

This rule prevents stale derived state from being mistaken for current-valid state.

---

# 35. Operation Outcomes

Maintenance operation outcomes are:

* `Success`;
* `Failure`;
* `Indeterminate`.

These outcomes are distinct from consistency state.

---

# 36. `Success`

`Success` means:

* the requested operation completed;
* its resulting derived state is known;
* the resulting state satisfies the applicable consistency contract.

A successful operation may establish:

```text
Consistency = Valid
```

where the operation's semantics require current consistency.

---

# 37. `Failure`

`Failure` means the requested operation did not complete successfully and the system can establish the failure condition.

If authoritative state has not changed, existing valid state MAY remain valid.

If authoritative state has changed, the resulting consistency state MUST be `Recovery Required`.

---

# 38. `Indeterminate`

`Indeterminate` means the system cannot establish whether the requested semantic transition completed.

An indeterminate result MUST NOT be treated as `Success`.

The system MUST NOT assume that no state change occurred merely because completion could not be established.

The system MUST enter an explicit non-valid consistency state until the actual state can be established or authoritative recovery is performed.

---

# 39. Failure of Rebuild

If a rebuild fails before replacement publication:

* incomplete replacement Totals MUST NOT be published;
* a partial rebuild MUST NOT become visible;
* the previous complete Published Totals MAY remain physically retained;
* if the previous publication is still current-valid, it MAY remain the current Published Totals;
* if the authoritative fact set has changed relative to that publication, consistency MUST be `Recovery Required`.

---

# 40. Indeterminate Rebuild

If rebuild completion or publication becomes indeterminate:

* the result MUST NOT be treated as successful;
* the system MUST NOT assume that the old publication remains current-valid without establishing that fact;
* the system MUST NOT expose a partially reconstructed Totals state;
* consistency MUST be treated as non-valid until the actual state is established or recovery is performed.

---

# 41. Rebuild Failure MUST NOT Fabricate Data

A failed or incomplete rebuild MUST NOT:

* silently ignore unsupported Movement Facts;
* replace unsupported values with zero;
* drop invalid contributions without explicit contract semantics;
* fabricate missing contributions;
* derive replacement state from stale Totals.

Unsupported or invalid authoritative data MUST result in explicit failure.

---

# 42. Maintenance Visibility

Only complete Published Totals may be exposed as the current derived Totals state.

A partially rebuilt or partially updated Totals state MUST never be externally observable.

The following states are prohibited as visible current Totals:

```text
partial old state
partial new state
mixed old/new state
partially applied contributions
partially removed contributions
incomplete rebuild
```

---

# 43. Previously Published Snapshot

During maintenance, the previous complete Published Totals MAY remain physically available until a replacement snapshot is successfully published.

However:

> physical availability does not imply current semantic validity.

If the authoritative Movement Fact set has changed, the previous snapshot MUST NOT be classified as `Valid`.

---

# 44. Balance Query Consistency Requirement

Balance Query is read-only.

Balance Query MUST NOT:

* perform maintenance;
* perform rebuild;
* repair Totals;
* mutate Totals;
* implicitly recover consistency.

Balance Query MUST read only from a Published Totals state whose consistency is `Valid`.

Therefore:

```text
Valid consistency
      ↓
Balance Result may be produced
```

while:

```text
Indeterminate
      ↓
current Balance Result unavailable
```

and:

```text
Recovery Required
      ↓
current Balance Result unavailable
```

The concrete API representation of this unavailable state is deferred to the Concrete API Design.

---

# 45. Balance Query During Maintenance

During maintenance, Balance Query MUST NOT observe a partial replacement.

If the current Published Totals remain current-valid during a maintenance operation whose authoritative input boundary has not changed, they MAY remain readable.

If authoritative state has already changed and the current Published Totals no longer correspond to that authoritative state, Balance Query MUST NOT treat them as a current-valid Balance Result.

This preserves Step 5 semantics without introducing implicit repair behavior.

---

# 46. Balance Query Does Not Repair

The following behavior is explicitly prohibited:

```text
Balance Query
      ↓
detect inconsistency
      ↓
rebuild
      ↓
return Balance
```

Balance Query is a read operation.

Recovery belongs to the maintenance lifecycle.

---

# 47. Logical Consistency Boundary

The semantic architecture is:

```text
Movement Persistence
        +
Totals Maintenance
        ↓
Logical Consistency Boundary
        ↓
Published Totals
        ↓
Balance Query
```

The consistency boundary means that current-valid Published Totals are established only after the corresponding authoritative Movement Fact state and derived Totals state are known to correspond.

This is a semantic boundary.

It does not require a specific physical database transaction mechanism.

---

# 48. Atomic Semantic Publication

Publication of replacement Totals MUST be atomic at the semantic level.

Externally observable state MUST be either:

```text
previous complete Published Totals
```

or:

```text
new complete Published Totals
```

but never:

```text
partial previous state
partial new state
mixed state
```

The concrete mechanism for atomic publication is deferred.

Possible implementation mechanisms include:

* atomic replacement;
* versioned snapshots;
* transactional publication;
* immutable aggregate snapshots;
* another mechanism satisfying this contract.

No particular mechanism is mandated by Step 6.

---

# 49. Publication Point

A rebuild becomes the current Published Totals only at the publication point.

Before publication:

```text
replacement Totals = private/incomplete
```

After successful publication:

```text
replacement Totals = current Published Totals
```

The publication point MUST NOT expose an intermediate aggregate state.

---

# 50. Maintenance Isolation

For the current Phase 7 scope, a full rebuild establishes an exclusive logical maintenance boundary for the Register.

Movement mutations affecting that Register MUST NOT bypass the rebuild boundary.

During a full rebuild, the active mutation path for the affected Register is therefore blocked or otherwise excluded from accepting authoritative changes that would fall outside the rebuild input boundary.

No concurrent rebuild/mutation reconciliation protocol is defined by Step 6.

Such a protocol is explicitly deferred to a future scope if required.

---

# 51. Rebuild Input Boundary

A rebuild MUST have a deterministic authoritative input boundary.

The rebuild MUST NOT produce a Totals snapshot from an implicitly changing Movement Fact set.

For the current Phase 7 scope, this is achieved by excluding active Register mutation during the full rebuild.

---

# 52. Maintenance Ownership

At most one logically authoritative maintenance lifecycle may control the current Register Totals publication at a time.

Two independent maintenance operations MUST NOT be able to publish competing Totals states without a defined ordering or serialization boundary.

The Concrete API Design MUST define the mechanism that enforces this invariant.

The mechanism itself is not defined by this contract.

---

# 53. Multiple Rebuilds

Multiple rebuild attempts MAY occur sequentially.

They MUST NOT create semantic ambiguity.

For the same authoritative Movement Fact set:

```text
rebuild(F)
rebuild(F)
```

must produce equivalent current-valid Totals.

Two independent rebuilds MUST NOT publish conflicting interpretations of the same authoritative state.

---

# 54. Recovery Procedure

Recovery follows:

```text
Detect non-valid consistency
          ↓
Enter maintenance
          ↓
Read authoritative Movement Facts
          ↓
Rebuild fresh Totals
          ↓
Validate
          ↓
Publish atomically
          ↓
Establish Valid consistency
```

Recovery MUST NOT use stale Totals as its source.

---

# 55. Recovery Success

Successful recovery establishes:

```text
Lifecycle = Active
Consistency = Valid
```

provided that the resulting Published Totals correspond to the current authoritative Movement Fact set.

---

# 56. Recovery Failure

If recovery fails:

* no partial replacement may become current;
* authoritative Movement Facts remain authoritative;
* current-valid consistency MUST NOT be claimed;
* the system remains in a non-valid state;
* another recovery attempt may be required.

The system MUST NOT report successful recovery unless current consistency has actually been established.

---

# 57. Recovery and Balance Query

Balance Query MUST NOT perform recovery.

If recovery is required:

```text
Recovery Required
      ↓
Balance Query
      ↓
no current-valid Balance Result
```

Recovery must be performed through the maintenance lifecycle.

---

# 58. Consistency State After Successful Maintenance

After a successful maintenance operation that establishes correspondence with the current authoritative Movement Fact set:

```text
Consistency = Valid
```

The operation MUST NOT report success while leaving the current consistency state unresolved.

---

# 59. Consistency State After Known Failure

After a known failure:

### If authoritative state did not change:

```text
existing valid state MAY remain Valid
```

### If authoritative state changed:

```text
Consistency = Recovery Required
```

This distinction is mandatory.

---

# 60. Consistency State After Indeterminate Outcome

After an indeterminate outcome:

```text
Consistency != Valid
```

until the system establishes the actual state.

The system MUST NOT infer current validity from the absence of an observed error.

---

# 61. Failure Matrix

The semantic failure matrix is:

| Operation / Event                            | Authoritative Movement Facts      | Published Totals       | Consistency                         |
| -------------------------------------------- | --------------------------------- | ---------------------- | ----------------------------------- |
| Apply succeeds                               | updated                           | updated                | Valid                               |
| Apply fails before authoritative change      | unchanged                         | unchanged              | Valid                               |
| Apply fails after authoritative persistence  | updated                           | old                    | Recovery Required                   |
| Apply becomes indeterminate                  | potentially changed               | uncertain              | Indeterminate                       |
| Remove succeeds                              | updated                           | updated                | Valid                               |
| Remove fails before authoritative change     | unchanged                         | unchanged              | Valid                               |
| Remove fails after authoritative persistence | updated                           | old                    | Recovery Required                   |
| Rebuild succeeds                             | unchanged                         | replaced               | Valid                               |
| Rebuild fails before publication             | unchanged                         | old complete snapshot  | prior state retained if still valid |
| Rebuild becomes indeterminate                | unchanged / publication uncertain | uncertain              | Indeterminate                       |
| Recovery rebuild succeeds                    | authoritative                     | replaced               | Valid                               |
| Recovery rebuild fails                       | authoritative                     | no partial replacement | non-valid                           |

The concrete API representation of these states is deferred.

---

# 62. Semantic Invariants

Step 6 MUST preserve the following invariants.

### 62.1 Authoritative Facts

Movement Facts are authoritative.

### 62.2 Derived Totals

Totals are derived.

### 62.3 Reconstructibility

Totals can be reconstructed from authoritative Movement Facts.

### 62.4 Deterministic Rebuild

The same authoritative input produces the same semantic Totals.

### 62.5 Rebuild Idempotency

Repeated rebuilds do not accumulate effects.

### 62.6 Incremental/Rebuild Equivalence

Successful incremental maintenance and rebuild produce equivalent Totals for the same authoritative fact set.

### 62.7 Apply Idempotency

Repeated apply of the same logical contribution does not double-count.

### 62.8 Remove Idempotency

Repeated remove of the same logical contribution does not double-remove.

### 62.9 Contribution Identity

A contribution is identified by:

```text
Movement Fact Identity + Register Identity
```

### 62.10 No Partial Publication

Partial replacement state is never visible as current Published Totals.

### 62.11 Publication Integrity

Only a complete replacement may become current Published Totals.

### 62.12 Recovery

Non-valid derived state can be reconstructed from authoritative Movement Facts.

### 62.13 Query Isolation

Balance Query does not perform maintenance or recovery.

### 62.14 Current Validity

`Valid` means correspondence with the current authoritative Movement Fact set.

### 62.15 Failure Integrity

Authoritative Movement Facts are not deleted merely because derived maintenance fails.

### 62.16 Maintenance Visibility

A stale or partial snapshot MUST NOT be presented as current-valid.

---

# 63. Architectural Prohibitions

Step 6 MUST NOT introduce behavior that violates these rules.

The system MUST NOT:

1. use old Totals as the source for rebuild;
2. publish partial Totals;
3. double-apply a Movement contribution;
4. double-remove a Movement contribution;
5. treat an indeterminate operation as success;
6. delete authoritative Movement Facts because Totals maintenance failed;
7. silently drop unsupported authoritative facts during rebuild;
8. fabricate missing contribution values;
9. perform repair during Balance Query;
10. allow competing independent rebuilds to publish conflicting states;
11. bypass the rebuild mutation boundary;
12. treat stale Published Totals as current-valid;
13. change Step 5 Balance semantics;
14. introduce distributed transaction semantics into Step 6;
15. introduce unrelated reporting or accounting-period behavior.

---

# 64. Deterministic Maintenance

Maintenance MUST NOT depend on uncontrolled external state.

For the same:

* authoritative Movement Fact state;
* Register identity;
* aggregation semantics;
* TotalsKey semantics;
* contribution semantics;

maintenance MUST produce the same semantic result.

Runtime identity, storage layout, arbitrary collection ordering, and uncontrolled system time MUST NOT alter the result.

---

# 65. Time Semantics

Step 6 introduces no new independent time semantics.

If a Movement Fact's contribution depends on accounting time or other temporal inputs, those inputs MUST already be part of the authoritative Movement Fact and/or the applicable Phase 7 aggregation contract.

Maintenance MUST NOT silently introduce a new notion of current time.

---

# 66. Persistence Independence

This contract is independent of the concrete persistence provider.

The semantics MUST hold regardless of whether the underlying persistence implementation uses:

* in-memory storage;
* filesystem storage;
* database storage;
* another supported persistence mechanism.

Storage layout MUST NOT alter the semantic lifecycle.

---

# 67. Runtime Independence

Maintenance semantics MUST NOT depend on runtime object identity.

Rebuild correctness MUST be based on authoritative persisted Movement Facts and their semantic identities.

---

# 68. Provider Independence

A different persistence provider MUST NOT change:

* contribution identity;
* aggregation semantics;
* rebuild determinism;
* idempotency;
* failure semantics;
* publication semantics;
* Balance Query semantics.

---

# 69. Error Semantics

Concrete error types are deferred to the Concrete API Design.

However, the following semantic distinction is mandatory:

```text
known failure
      ≠
indeterminate outcome
      ≠
successful completion
```

Concrete exceptions or result objects MUST preserve this distinction where necessary.

---

# 70. Concrete API Deferrals

The following decisions are intentionally deferred:

* concrete class names;
* concrete protocol names;
* method names;
* method signatures;
* return types;
* exception hierarchy;
* enum implementation;
* contribution-state storage;
* Totals snapshot representation;
* publication mechanism;
* versioning mechanism;
* locking mechanism;
* transaction mechanism;
* persistence implementation;
* recovery API shape;
* maintenance ownership mechanism.

These MUST be designed in:

```text
PHASE_7_STEP_6_CONCRETE_API_DESIGN.md
```

without changing the semantics defined here.

---

# 71. Concrete API Must Preserve the Contract

The Concrete API Design MUST NOT weaken or reinterpret:

* authoritative Movement Facts;
* current-valid consistency;
* rebuild source of truth;
* idempotency;
* incremental/rebuild equivalence;
* atomic publication;
* maintenance isolation;
* Balance Query isolation;
* recovery semantics.

Concrete API decisions are implementation mechanisms for this contract, not alternative semantics.

---

# 72. Acceptance Criteria

Step 6 is architecturally complete when all of the following are true.

### Lifecycle

* lifecycle states are defined;
* lifecycle and consistency are separate;
* successful maintenance returns to `Active + Valid`;
* failed/indeterminate maintenance cannot silently restore `Active + Valid`.

### Authoritative State

* Movement Facts are authoritative;
* Totals are derived;
* failure of Totals maintenance does not invalidate authoritative Movement Facts.

### Incremental Maintenance

* apply semantics are defined;
* remove semantics are defined;
* apply/remove are symmetric;
* apply is idempotent;
* remove is idempotent;
* contribution identity is defined.

### Rebuild

* rebuild source is authoritative Movement Facts;
* old Totals are not a rebuild source;
* rebuild is deterministic;
* rebuild is idempotent;
* rebuild and incremental maintenance are semantically equivalent.

### Failure

* known failure is distinguished from indeterminate outcome;
* authoritative state change followed by maintenance failure produces `Recovery Required`;
* indeterminate outcomes are non-valid until resolved;
* partial replacement is never published.

### Visibility

* only complete Published Totals are visible;
* stale snapshots are not considered current-valid;
* partial rebuilds are never visible.

### Balance Query

* Balance Query remains read-only;
* Balance Query does not repair;
* current Balance Result requires `Valid` consistency;
* Step 5 semantics remain unchanged.

### Recovery

* rebuild is the recovery mechanism;
* recovery uses authoritative Movement Facts;
* successful recovery establishes `Valid`;
* failed recovery does not fabricate consistency.

### Isolation

* full rebuild has a defined authoritative input boundary;
* Register mutation does not bypass that boundary;
* competing maintenance publication is prevented semantically.

---

# 73. Architectural Completion Condition

Step 6 is complete at the architecture-contract level when the system has a precise semantic answer to all of the following:

1. What state is authoritative?
2. What state is derived?
3. What does `Valid` mean?
4. What does `Indeterminate` mean?
5. What does `Recovery Required` mean?
6. When does maintenance begin?
7. When does maintenance complete?
8. What constitutes a Movement contribution?
9. What identifies a contribution?
10. How is apply performed semantically?
11. How is remove performed semantically?
12. Why are apply and remove idempotent?
13. How is rebuild performed?
14. What is the rebuild source of truth?
15. Why is rebuild deterministic?
16. Why is rebuild idempotent?
17. Why is incremental maintenance equivalent to rebuild?
18. What happens if authoritative persistence succeeds but Totals maintenance fails?
19. What happens if operation completion becomes indeterminate?
20. What is visible during maintenance?
21. Can partial Totals be observed?
22. What does atomic publication mean?
23. What happens during recovery?
24. Can Balance Query repair state?
25. When may Balance Query return a current-valid Balance Result?
26. How is rebuild isolated from concurrent Register mutation?
27. How are competing maintenance operations prevented from publishing conflicting states?

This contract provides a deterministic answer to all of these questions.

---

# 74. Final Semantic Model

The complete Step 6 model is:

```text
                 Authoritative State
                 ------------------
                 Movement Facts
                        │
                        │
                        ▼
               ┌─────────────────┐
               │ Totals          │
               │ Maintenance     │
               └─────────────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
        Incremental             Rebuild
        apply/remove               │
             │                     │
             └──────────┬──────────┘
                        ▼
                Fresh / Updated
                  Totals State
                        │
                        ▼
                   Validation
                        │
                        ▼
              Atomic Publication
                        │
                        ▼
              Published Totals
                        │
                 Consistency=Valid
                        │
                        ▼
                  Balance Query
                        │
                        ▼
                  Balance Result
```

Failure path:

```text
Authoritative Movement Facts
            │
            ▼
       Maintenance
            │
       ┌────┴─────┐
       │          │
    Success    Failure /
       │       Indeterminate
       │          │
       ▼          ▼
     Valid    Non-valid
                  │
          ┌───────┴────────┐
          │                │
     Indeterminate   Recovery Required
          │                │
          └───────┬────────┘
                  ▼
               Rebuild
                  │
                  ▼
             Validate
                  │
                  ▼
         Atomic Publication
                  │
                  ▼
               Valid
```

---

# 75. Final Contract Principles

The Step 6 contract can be reduced to the following principles:

1. **Movement Facts are authoritative.**
2. **Totals are derived.**
3. **`Valid` means current correspondence with authoritative Movement Facts.**
4. **Old Totals are never the source of rebuild.**
5. **Apply and remove are idempotent.**
6. **A contribution is identified by Movement Fact Identity + Register Identity.**
7. **Rebuild is deterministic and idempotent.**
8. **Incremental maintenance and rebuild are semantically equivalent.**
9. **A known authoritative-state change followed by maintenance failure requires recovery.**
10. **Indeterminate outcomes are never treated as success.**
11. **Partial Totals are never published.**
12. **Publication is atomic at the semantic level.**
13. **Rebuild is the recovery mechanism.**
14. **Balance Query never repairs state.**
15. **A current-valid Balance Result requires `Valid` consistency.**
16. **Full rebuild has an explicit authoritative input boundary.**
17. **Competing maintenance operations cannot publish conflicting current states.**
18. **Step 6 does not redefine Step 5 Balance semantics.**

---

# 76. Final Architectural Boundary

Step 6 defines **what must be true** about Totals lifecycle and maintenance.

It does not define **how the implementation makes it true**.

Therefore:

```text
Step 6 Contract
      ↓
semantic invariants
      ↓
Concrete API Design
      ↓
implementation mechanism
```

The next document may therefore define the concrete interfaces required to implement this contract without reopening the semantic architecture.

---

# 77. Status

**Phase 7 — Step 6 Lifecycle & Maintenance Contract: COMPLETE**

The semantic contract for:

* lifecycle;
* consistency;
* incremental maintenance;
* contribution identity;
* apply/remove;
* rebuild;
* determinism;
* idempotency;
* failure;
* indeterminate outcomes;
* recovery;
* visibility;
* publication;
* isolation;
* Balance Query interaction

is now defined.

The next architectural artifact is:

```text
PHASE_7_STEP_6_CONCRETE_API_DESIGN.md
```

This document MUST treat the present contract as authoritative and MUST NOT redefine its semantics.
