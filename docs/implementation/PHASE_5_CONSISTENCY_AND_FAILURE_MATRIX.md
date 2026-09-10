# Phase 5 — Consistency & Failure Matrix

**Step:** 5.3 — Consistency & Failure Matrix
**Phase:** 5 — Storage & Persistence Boundary
**Status:** Final
**Date:** 2026-09-10

---

## 1. Purpose

This document defines the consistency and failure semantics for the major persistence scenarios of AcCoreD.

It translates the semantic rules established by:

* `ADR-P5-01 — Establish Storage and Persistence Boundary`;
* `ADR-P5-02 — Transaction and Consistency Model`;
* `Step 5.2 — Persistence Scope Semantic Contract`;

into a concrete scenario matrix.

The purpose is to answer:

> **What persistent result is considered correct for each operation, and what persistent result is allowed when the operation fails?**

This document defines semantic guarantees.

It does **not** define:

* database transactions;
* filesystem transactions;
* transaction APIs;
* ORM sessions;
* Unit of Work;
* locking implementation;
* journal format;
* recovery implementation;
* physical schema.

---

# 2. Architectural Principle

The consistency model follows:

```text
Business / Application Scenario
            │
            ▼
Required Persistent Result
            │
            ▼
Participating Persistence Operations
            │
            ▼
Persistence Scope
            │
            ├── Atomicity Requirement
            ├── Durability Requirement
            └── Concurrency Requirement
            │
            ▼
Failure Semantics
            │
            ▼
Allowed Persistent State
```

The matrix describes the semantic result at the Persistence boundary.

It does not prescribe the physical mechanism used to achieve that result.

---

# 3. Terminology

## 3.1 Primary State

Primary persistent state is state that represents the authoritative result of a business operation.

Examples:

* persisted document state;
* accounting movement facts;
* persisted configuration state.

Primary state is not reconstructed from derived state.

---

## 3.2 Derived State

Derived state is persistent state calculated from primary facts or primary objects.

Examples may include:

* register totals;
* calculated balances;
* indexes;
* materialized summaries;
* other persisted projections.

Derived state must not redefine primary business facts.

Its consistency requirement depends on the operation that produces or changes it.

---

## 3.3 Persistence Scope

A logical consistency boundary covering persistence operations that must be evaluated together to satisfy a required persistence result.

A Persistence Scope is not necessarily a physical transaction.

---

## 3.4 Published State

Persistent state that the system considers part of the successful logical result of an operation.

Physical intermediate data is not automatically published state.

---

## 3.5 Partial Physical Work

Physical writes that occur before a Persistence Scope reaches its final semantic outcome.

Examples:

* temporary files;
* journal entries;
* staged records;
* partially written provider state.

Partial physical work does not automatically constitute successful logical persistence.

---

# 4. General Consistency Rules

The following rules apply to all scenarios in this matrix.

### CFM-01 — Successful Completion Requires Required Result

An operation may be reported as successfully persisted only when its required persistent result has been achieved.

### CFM-02 — Failure Must Be Explicit

A failed persistence operation must not be reported as successfully completed.

### CFM-03 — Atomicity Is Explicit

Atomicity is required only where the scenario's correctness depends on a jointly completed persistence result.

### CFM-04 — No Partial Published State

Where atomicity is required, a failure must not leave the system reporting a partially published logical result.

### CFM-05 — Physical Partial Work Is Not Automatically Published

Physical intermediate work may exist internally without becoming visible as successful logical state.

### CFM-06 — Concurrency Is Explicit

Where concurrent modification can affect correctness, the persistence contract must define the required conflict behavior.

### CFM-07 — No Implicit Last-Write-Wins

Silent overwriting must not be considered a correctness guarantee where concurrent modification matters.

### CFM-08 — Provider Mechanism Is Not the Contract

The matrix specifies semantic outcomes, not provider implementation mechanisms.

### CFM-09 — Primary Facts Remain Authoritative

Derived state must not redefine or replace primary persistent facts.

### CFM-10 — Scope Is Defined by Required Result

A Persistence Scope contains the persistence operations required to satisfy a higher-level operation.

---

# 5. Matrix Legend

The following terms are used in the scenario matrix.

| Value            | Meaning                                                      |
| ---------------- | ------------------------------------------------------------ |
| **Required**     | The guarantee is mandatory for the scenario                  |
| **Explicit**     | Must be defined by the applicable contract                   |
| **Not Required** | The scenario does not require this guarantee                 |
| **Dependent**    | Determined by the specific operation or persistence contract |
| **N/A**          | The dimension does not apply                                 |

---

# 6. Object Create

## Scenario

Creation of a new persistent business object.

Examples:

```text
Create Customer
Create Product
Create Document
```

## Required Persistent Result

A new persistent object exists with the required identity and valid persistent state.

## Matrix

| Dimension              | Requirement                                         |
| ---------------------- | --------------------------------------------------- |
| Persistence Operations | Persist object state                                |
| Persistence Scope      | One logical scope                                   |
| Atomicity              | Dependent on the applicable persistence contract    |
| Durability             | Required for successful completion                  |
| Concurrency            | Explicit where identity or uniqueness can conflict  |
| Failure                | Object must not be reported as successfully created |
| Partial Physical Work  | Must not be treated as published object state       |

A single persistence operation does not automatically imply an independently defined atomic Persistence Scope.

If object creation participates in a larger logical operation, the larger scope determines the applicable atomicity requirement.

## Correct Result

```text
Create succeeds
    ↓
Object exists as valid persistent state
```

## Failure Result

```text
Create fails
    ↓
No successfully published object
```

An implementation may have temporary physical data after failure, but such data must not be interpreted as a successfully created object.

---

# 7. Object Update

## Scenario

Modification of an existing persistent business object.

## Required Persistent Result

The object contains the complete intended persistent state corresponding to the successful operation.

## Matrix

| Dimension              | Requirement                                                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| Persistence Operations | Update object state                                                                                        |
| Persistence Scope      | One logical scope                                                                                          |
| Atomicity              | Dependent on the applicable persistence contract                                                           |
| Durability             | Required for successful completion                                                                         |
| Concurrency            | Explicit when concurrent modification can affect correctness                                               |
| Failure                | Previous valid published state remains authoritative unless the contract explicitly defines another result |
| Partial Physical Work  | Must not become an unintended published state                                                              |

## Correct Result

```text
Previous State
      │
      ▼
Successful Update
      │
      ▼
New Valid State
```

## Concurrency

If two operations modify the same object concurrently and correctness depends on detecting the conflict, the persistence contract must define the conflict behavior.

Possible semantic result:

```text
Concurrent modification
        ↓
Conflict
        ↓
Update rejected
```

The mechanism used to detect the conflict is provider-specific.

---

# 8. Register Movement Append

## Scenario

Appending accounting facts to an accumulation register.

A `MovementSet` generated by posting is persisted as register facts.

## Required Persistent Result

The required movement facts are persisted according to the applicable Register persistence contract.

## Matrix

| Dimension              | Requirement                                                      |
| ---------------------- | ---------------------------------------------------------------- |
| Persistence Operations | Append register movements                                        |
| Persistence Scope      | Determined by the higher-level operation                         |
| Atomicity              | Dependent                                                        |
| Durability             | Required for posting-related successful completion               |
| Concurrency            | Explicit according to the Register contract                      |
| Failure                | Required movement persistence must not be reported as successful |
| Partial Physical Work  | Must not create unintended logical movements                     |

Register movement append semantics are defined by the Register persistence contract.

When movement persistence participates in a larger Posting Persistence Scope, the larger scope's consistency requirements additionally apply.

Therefore:

```text
Movement Append
      │
      └── has Register persistence semantics

Posting Scope
      │
      └── may impose additional atomicity requirements
```

The atomicity of an individual movement append must not be interpreted as automatically making the entire Posting operation atomic.

---

# 9. Posting

## Scenario

Posting a business object and producing its accounting effects.

Conceptually:

```text
Posting
   │
   ├── Persist Posted Object State
   ├── Append MovementSet
   └── Persist Required Derived State
```

## Required Persistent Result

Posting requires an atomic Persistence Scope **when accounting correctness depends on the posted object state and its accounting facts being jointly published as one logical result**.

Atomicity is therefore derived from the required persistent result, not merely from the fact that the operation is called "Posting".

## Matrix

| Dimension              | Requirement                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| Persistence Operations | Object state + MovementSet + required derived state                                              |
| Persistence Scope      | One logical cross-resource scope when joint publication is required                              |
| Atomicity              | Required when joint publication is required                                                      |
| Durability             | Required for successful posting completion                                                       |
| Concurrency            | Explicit                                                                                         |
| Failure                | Posting must not be reported as successfully persisted with incomplete required accounting state |
| Partial Physical Work  | Must not become a partially published posting result                                             |

## Required Semantic Result

```text
Posting
   │
   ├── Object State
   ├── Movement Facts
   └── Required Derived State
          │
          ▼
    Required Consistent Result
```

If the required posting scope fails:

```text
Posting Failure
      ↓
No successful partial posting result
```

This does **not** require all physical writes to disappear.

It requires that the logical result not be falsely reported as successfully completed.

---

# 10. Posting Handler Boundary

The Posting Handler is not a persistence coordinator.

The Posting Handler:

```text
Business Input
      ↓
Posting Logic
      ↓
MovementSet
```

It does not:

* begin a transaction;
* commit a transaction;
* rollback a transaction;
* manage a Persistence Scope;
* call Storage Providers directly.

The higher-level Posting Engine or application operation determines the required persistence result and coordinates persistence.

---

# 11. Derived State Update

## Scenario

Persistence of state derived from primary objects or facts.

Examples:

* register totals;
* balances;
* materialized summaries;
* persisted projections.

## Matrix

| Dimension              | Requirement                                        |
| ---------------------- | -------------------------------------------------- |
| Persistence Operations | Persist derived state                              |
| Persistence Scope      | Dependent                                          |
| Atomicity              | Dependent                                          |
| Durability             | Dependent                                          |
| Concurrency            | Dependent                                          |
| Failure                | Must follow the applicable consistency requirement |
| Primary Facts          | Remain authoritative                               |

Derived state participates in an atomic Persistence Scope **only when it is part of the required persistent result of the operation**.

If derived state is reconstructible and explicitly allowed to lag behind primary state, its persistence may have independent semantics.

---

# 12. Derived State Failure

A failure while persisting derived state must be classified according to the business consistency requirement.

Two semantic models are possible.

## Model A — Derived State Is Required for Completion

```text
Primary State
+
Required Derived State
        ↓
Atomic Persistence Scope
```

Failure means the required persistence result is not completed.

## Model B — Derived State Is Reconstructible

```text
Primary State
        ↓
Successful Completion

Derived State
        ↓
May be rebuilt / refreshed
```

In this case, failure of derived-state persistence does not necessarily invalidate the primary result.

This is valid only when the derived state is explicitly defined as reconstructible and independently recoverable.

The applicable operation must define which model applies.

There must be no implicit assumption that all derived state is either always atomic or always independently persistent.

---

# 13. Configuration Persistence

## Scenario

Persistence of configuration state required by the Configuration subsystem.

Possible participating state includes:

```text
Configuration State
+
Required Configuration Metadata
```

Where configuration activation requires joint publication of multiple persistent components, those components may form one logical Persistence Scope.

## Matrix

| Dimension              | Requirement                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Persistence Operations | Configuration-related persistence operations                                                                                    |
| Persistence Scope      | One logical scope where state must be jointly published                                                                         |
| Atomicity              | Required where joint publication is required                                                                                    |
| Durability             | Required for successful configuration persistence                                                                               |
| Concurrency            | Explicit                                                                                                                        |
| Failure                | New configuration must not be reported as successfully persisted when required persistent configuration state was not completed |
| Previous Valid State   | Must remain authoritative when required by activation semantics                                                                 |

The exact relationship between configuration persistence and runtime activation remains governed by the Configuration architecture.

Persistence does not itself define runtime activation semantics.

---

# 14. Multi-Resource Persistence

## Scenario

One business/application operation modifies multiple persistence resources.

Example:

```text
Document
+
Register
+
Derived State
```

## Matrix

| Dimension              | Requirement                                      |
| ---------------------- | ------------------------------------------------ |
| Persistence Operations | Multiple persistence contracts                   |
| Persistence Scope      | One logical scope                                |
| Atomicity              | Explicit                                         |
| Durability             | Explicit                                         |
| Concurrency            | Explicit                                         |
| Failure                | Must preserve the semantic contract of the scope |
| Provider Count         | May be greater than one                          |

A logical Persistence Scope may span multiple physical providers.

The architecture does not require:

```text
One Scope = One Provider
```

nor:

```text
One Scope = One Database
```

---

# 15. Provider Failure

## Scenario

A Storage Provider fails while executing an operation participating in a Persistence Scope.

Examples:

* filesystem error;
* database error;
* network failure;
* provider unavailable;
* write failure;
* read failure.

## Matrix

| Dimension         | Requirement                                                 |
| ----------------- | ----------------------------------------------------------- |
| Persistence Scope | Existing scope semantics remain authoritative               |
| Provider Error    | Translated into persistence-level semantic failure          |
| Atomicity         | Must preserve required scope semantics                      |
| Completion        | Must not report success unless required result was achieved |
| Recovery          | Implementation-dependent                                    |
| Retry             | Contract-dependent                                          |

The Storage Provider does not decide whether the business operation succeeded.

The Persistence boundary interprets provider failure according to the applicable persistence contract.

---

# 16. Concurrency Conflict

## Scenario

A persistence operation detects that the state it is modifying has changed concurrently.

## Matrix

| Dimension        | Requirement                                                 |
| ---------------- | ----------------------------------------------------------- |
| Detection        | Required only where concurrency correctness requires it     |
| Result           | Explicit conflict or other contract-defined semantic result |
| Silent Overwrite | Not permitted as an implicit correctness guarantee          |
| Retry            | Higher-level operation may retry if permitted               |
| Mechanism        | Provider-specific                                           |

Example:

```text
Read State V1
      │
      ├── Other Operation → State V2
      │
      ▼
Attempt Update
      │
      ▼
Conflict
```

The persistence contract must define the semantic result.

It must not silently convert the conflict into an unconditional last-write-wins update where correctness depends on detecting the conflict.

---

# 17. Retry Constraint

Retry semantics are not defined by this step as a separate persistence subsystem.

However, any future retry mechanism must preserve the persistence semantics established by this document.

In particular, retry must not unintentionally duplicate a logical business effect.

Example:

```text
Append MovementSet
```

must not silently become:

```text
MovementSet
+
MovementSet
```

simply because the caller cannot determine whether the previous attempt physically completed.

Operations that are retry-sensitive may therefore require explicit semantic guarantees such as:

* idempotency;
* stable operation identity;
* deduplication;
* explicit conflict handling;
* another contract-defined mechanism.

The mechanism itself is outside the scope of Step 5.3.

---

# 18. Indeterminate Persistence Outcome

A persistence operation may fail in a way that leaves its physical outcome unknown.

Example:

```text
Operation sent to provider
        ↓
Provider failure / connection lost
        ↓
Physical outcome cannot be determined
```

The semantic result is not automatically:

```text
Definitely Not Persisted
```

nor:

```text
Definitely Persisted
```

The operation has an **indeterminate persistence outcome**.

The applicable persistence contract or higher-level recovery logic must determine how such a case is handled.

Phase 5 recognizes indeterminate persistence outcomes but does not define a universal recovery protocol.

Any future recovery or retry mechanism must preserve the persistence semantics defined by this document.

---

# 19. Partial Scope Failure

When a scope contains multiple persistence operations:

```text
Operation A
Operation B
Operation C
```

and `B` fails, the semantic result depends on the scope requirements.

## Atomic Scope

```text
A ── success
B ── failure
C ── not completed
       ↓
Scope Failed
       ↓
No partially published logical result
```

## Non-Atomic Requirement

If the higher-level operation explicitly does not require atomicity:

```text
A ── success
B ── failure
C ── success
```

may be a valid semantic result.

However, this must be explicitly allowed by the applicable persistence contract.

It must not be inferred merely because the underlying provider can perform operations independently.

---

# 20. Persistence Scope Scenario Matrix

The consolidated matrix is:

| Scenario                   | Scope                                      | Atomicity                                    | Durability                      | Concurrency        | Failure Semantics                                                         |
| -------------------------- | ------------------------------------------ | -------------------------------------------- | ------------------------------- | ------------------ | ------------------------------------------------------------------------- |
| Object Create              | Single logical scope                       | Dependent                                    | Required                        | Explicit if needed | No successful partial object                                              |
| Object Update              | Single logical scope                       | Dependent                                    | Required                        | Explicit if needed | Previous valid state remains authoritative unless contract says otherwise |
| Movement Append            | Higher-level dependent                     | Dependent                                    | Required for posting completion | Explicit           | No unintended logical movement                                            |
| Posting                    | Cross-resource logical scope when required | Required when joint publication is required  | Required                        | Explicit           | No partially successful posting result                                    |
| Derived State              | Dependent                                  | Dependent                                    | Dependent                       | Dependent          | Governed by primary/derived consistency model                             |
| Configuration Persistence  | Logical scope                              | Required where joint publication is required | Required                        | Explicit           | No false successful persistence/activation                                |
| Multi-Resource Persistence | Logical cross-resource scope               | Explicit                                     | Explicit                        | Explicit           | Must preserve scope semantics                                             |
| Provider Failure           | Existing scope                             | Preserve requirement                         | Preserve requirement            | N/A                | Semantic persistence failure                                              |
| Concurrency Conflict       | Existing scope                             | Contract-dependent                           | Contract-dependent              | Explicit           | Conflict / explicitly defined result                                      |
| Retry                      | Higher-level operation                     | Contract-dependent                           | Contract-dependent              | Explicit           | Must not duplicate logical effect                                         |
| Indeterminate Outcome      | Existing operation                         | Contract-dependent                           | Contract-dependent              | Contract-dependent | Outcome requires explicit recovery handling                               |

---

# 21. Primary vs Derived State Matrix

The following distinction is mandatory for consistency analysis.

| State Type              | Examples                    | Authoritative? |                              Can Failure Be Tolerated? |
| ----------------------- | --------------------------- | -------------: | -----------------------------------------------------: |
| Primary Object State    | Document, Product, Customer |            Yes |                  Only according to operation semantics |
| Primary Register Facts  | Movements                   |            Yes |           Only according to posting/register semantics |
| Derived Register State  | Totals, balances            |             No | Potentially, if reconstructible and explicitly allowed |
| Materialized Projection | Reporting projection        |             No |                                            Potentially |
| Cache                   | Derived cached data         |             No |                     Generally yes, subject to contract |
| Recovery/Journal Data   | Implementation-specific     |             No |                          Depends on recovery mechanism |

The classification must be established by the responsible architectural layer.

---

# 22. Consistency Requirements by Business Operation

The following principle applies:

> The business operation determines the required persistent result; the required persistent result determines the Persistence Scope; the Persistence Scope determines the consistency guarantees required from persistence.

Therefore:

```text
Business Operation
        ↓
What must be true after success?
        ↓
Required Persistent Result
        ↓
What must become jointly visible?
        ↓
Persistence Scope
        ↓
Atomicity / Durability / Concurrency
```

This prevents Storage from determining business semantics.

---

# 23. Failure Classification

Failures should be classified semantically rather than by physical provider terminology.

| Failure Class         | Semantic Meaning                                              |
| --------------------- | ------------------------------------------------------------- |
| Not Found             | Required persistent resource does not exist                   |
| Already Exists        | Required creation conflicts with existing persistent identity |
| Storage Failure       | Persistence mechanism failed to perform required operation    |
| Concurrency Conflict  | Required state changed concurrently                           |
| Integrity Failure     | Persistent result violates required contract                  |
| Unsupported Operation | Provider/boundary cannot satisfy requested operation          |
| Indeterminate Outcome | Physical outcome cannot currently be determined               |

Physical exceptions may be mapped into these semantic categories.

---

# 24. Recovery and Retry Boundary

Recovery is intentionally separated from basic consistency semantics.

This document establishes:

```text
Failure
  ↓
Semantic Failure Result
```

It does not establish:

```text
Failure
  ↓
Automatic Retry
  ↓
Recovery Workflow
  ↓
Compensation
```

Automatic retry may be introduced later where a concrete operation requires it.

Any retry mechanism must preserve the operation's persistence semantics and must not create duplicate logical effects.

---

# 25. Forbidden Consistency Assumptions

The following assumptions are explicitly forbidden unless introduced by a future contract.

### FCA-01

Every persistence operation is automatically transactional.

### FCA-02

Every Persistence Scope is a database transaction.

### FCA-03

Every Persistence Scope has `begin/commit/rollback`.

### FCA-04

Every operation is automatically atomic.

### FCA-05

Failure means all physical writes disappeared.

### FCA-06

Physical intermediate state is automatically published state.

### FCA-07

Last-write-wins is always acceptable.

### FCA-08

All derived state must always be atomically persisted with primary state.

### FCA-09

All persistence operations in one application request belong to one scope.

### FCA-10

One Persistence Scope must use one physical provider.

### FCA-11

One Persistence Scope must use one physical database transaction.

### FCA-12

Provider capabilities define business consistency requirements.

---

# 26. Architectural Invariants

### P5-CFM1 — Required Result First

Consistency analysis begins with the required persistent result of the higher-level operation.

### P5-CFM2 — Scope Follows Required Result

A Persistence Scope is defined by the persistence operations required to achieve that result.

### P5-CFM3 — Explicit Atomicity

Atomicity is required only where the scenario explicitly requires joint completion.

### P5-CFM4 — No Partial Published Result

An atomic scope must not report a partially published logical result as successful.

### P5-CFM5 — Physical State Is Not Logical State

Physical intermediate work does not automatically constitute published persistent state.

### P5-CFM6 — Primary Facts Remain Authoritative

Derived state cannot redefine primary object state or accounting facts.

### P5-CFM7 — Explicit Concurrency

Concurrency guarantees are explicit where correctness depends on them.

### P5-CFM8 — No Implicit Last-Write-Wins

Concurrent correctness must not depend on an implicit last-write-wins assumption.

### P5-CFM9 — Provider Independence

The matrix defines semantic guarantees independently of physical storage technology.

### P5-CFM10 — Semantic Failure

Provider failures are translated into persistence-level semantic outcomes.

### P5-CFM11 — No False Completion

An operation must not be reported as successfully persisted unless its required persistence result has been achieved.

### P5-CFM12 — Retry Must Preserve Semantics

Retries must not introduce unintended duplicate logical effects.

### P5-CFM13 — Cross-Resource Scope Is Valid

A logical Persistence Scope may span multiple persistence resources.

### P5-CFM14 — No Implicit Global Scope

Persistence operations do not automatically belong to one global or request-wide scope.

### P5-CFM15 — Derived State Requirement Is Explicit

Derived state participates in an atomic Persistence Scope only when it is part of the required persistent result.

If derived state is reconstructible and explicitly permitted to lag behind primary state, its persistence may have independent semantics.

---

# 27. Relationship to Storage Provider

The matrix establishes requirements **above** the Storage Provider.

For example:

```text
Posting
   ↓
Atomic Persistence Scope Required
   ↓
Persistence Contracts
   ↓
Storage Boundary
   ↓
Provider
```

The provider may implement the required guarantee using:

```text
Database Transaction
```

or:

```text
Journal + Atomic Replacement
```

or:

```text
Provider-specific mechanism
```

or another implementation.

The architecture does not select between these mechanisms at this stage.

If a provider cannot satisfy the required guarantee, the system must not silently weaken the guarantee.

---

# 28. Relationship to Existing Phase 5 Architecture

The matrix preserves the established responsibility chain:

```text
Metadata
    ↓
defines

Runtime
    ↓
executes

Posting
    ↓
produces facts

Register
    ↓
accepts and organizes facts

Persistence
    ↓
defines semantic persistence requirements

Storage
    ↓
defines storage boundary

Provider
    ↓
implements physical storage
```

Transaction and consistency mechanisms remain below the semantic persistence contract.

---

# 29. Final Architectural Model

Step 5.3 establishes the following final model:

```text
                 Business / Application Operation
                              │
                              ▼
                    Required Persistent Result
                              │
                              ▼
                     Persistence Scope
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
          Atomicity       Durability       Concurrency
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                    Persistence Contracts
                              │
                              ▼
                       Storage Boundary
                              │
                              ▼
                      Storage Provider
```

Failure follows the same semantic boundary:

```text
Storage / Persistence Failure
            │
            ▼
     Semantic Failure
            │
            ▼
     Scope Outcome
            │
       ┌────┴────┐
       ▼         ▼
  Completed   Failed/Aborted
```

For atomic scopes:

```text
Required Persistent Result
            │
       ┌────┴────┐
       ▼         ▼
    Complete   Failure
       │         │
       ▼         ▼
 Published    No partially
   Result      published
               logical result
```

---

# 30. Conclusion

Step 5.3 establishes how the Persistence Scope semantic contract applies to concrete AcCoreD persistence scenarios.

The key architectural rule is:

> **Consistency is defined by the required persistent result of the higher-level operation, not by the capabilities or transaction model of the underlying storage technology.**

Therefore:

```text
Business Correctness
        ↓
Required Persistent Result
        ↓
Persistence Scope
        ↓
Explicit Consistency Guarantees
        ↓
Persistence Contracts
        ↓
Storage Boundary
        ↓
Provider Mechanism
```

This keeps business semantics, persistence semantics, and physical storage mechanisms independently evolvable.

---

# 31. Finalization Status

Step 5.3 is complete. The consistency and failure semantics defined by this document have been translated into the concrete persistence contracts and remain the governing semantic layer above provider-specific mechanisms.

The following Phase 5 work is now aligned with this matrix:

* Persistence Scope semantic contract;
* concrete Persistence Contract API;
* semantic persistence errors and indeterminate outcomes;
* Storage Provider boundary;
* persistent object representation;
* explicit runtime hydration and materialization mapping.

No universal transaction object, Unit of Work, Repository, Query abstraction, or provider-specific transaction API is introduced by this document.

**Status: Final.**
