# Step 5.2 — Persistence Scope Semantic Contract

**Phase:** 5 — Storage & Persistence Boundary
**Step:** 5.2 — Persistence Scope Semantic Contract
**Status:** Final
**Date:** 2026-09-10

---

## 1. Purpose

This document defines the semantic contract of a **Persistence Scope** within the AcCoreD architecture.

The purpose of a Persistence Scope is to define a logical boundary within which multiple persistence changes may require coordinated consistency, completion, failure handling, durability, or concurrency guarantees.

The Persistence Scope is an architectural concept.

It is **not**:

* a database transaction;
* a database connection;
* a session;
* a Unit of Work;
* an ORM transaction object;
* a filesystem transaction;
* a distributed transaction;
* a mandatory runtime object;
* a universal persistence API.

The contract defines **what persistence result must be guaranteed**, not **how the guarantee is physically implemented**.

---

# 2. Architectural Position

The dependency direction is:

```text
Business / Application Operation
            │
            ▼
Required Persistence Result
            │
            ▼
Persistence Scope
            │
            ├── Consistency Requirements
            │     ├── Atomicity
            │     └── Durability
            │
            ├── Completion Semantics
            │
            ├── Failure Semantics
            │
            └── Concurrency Requirements
            │
            ▼
Persistence Contracts
            │
            ▼
Storage Boundary
            │
            ▼
Storage Provider
```

The direction is intentionally one-way.

A Persistence Scope does not determine which business operation exists.

The higher-level business or application operation determines which persistence changes require coordination and therefore which Persistence Scope semantics are required.

---

# 3. Definition

A **Persistence Scope** is a logical consistency boundary covering a set of related persistence operations whose semantic outcome must be evaluated together.

A Persistence Scope may contain:

* persistence of one or more objects;
* persistence of register facts;
* persistence of configuration state;
* persistence of required derived state;
* multiple persistence contracts;
* multiple logical persistence resources;
* multiple physical storage resources.

The existence of a Persistence Scope does not imply that all participating operations must use the same physical storage mechanism.

The scope defines the **required semantic relationship** between participating persistence operations.

---

# 4. Scope Composition

A Persistence Scope is conceptually defined by:

```text
Persistence Scope
├── Participating Persistence Operations
├── Consistency Requirements
│   └── Atomicity Requirement, when applicable
├── Completion Semantics
├── Failure Semantics
└── Concurrency Requirements
```

Durability is considered part of the consistency/completion requirements applicable to the scope.

The architecture does not require every scope to have identical guarantees.

Different business operations may require different persistence semantics.

---

# 5. Participating Persistence Operations

A Persistence Scope encompasses the persistence operations that must be evaluated together to satisfy the required persistence result of the higher-level operation.

Examples include:

```text
Persist Document State
+
Append Register Movements
+
Persist Required Derived State
```

or:

```text
Persist Configuration State
+
Persist Configuration Metadata
```

The exact participating operations are determined by the higher-level operation and the applicable persistence contracts.

A Persistence Scope must not automatically include unrelated persistence operations merely because they occur during the same execution.

---

# 6. Scope Identity

A Persistence Scope does not require a mandatory architectural identity.

The semantic contract does not require:

* a Scope ID;
* a scope object;
* a globally unique transaction identifier;
* a persistent scope record.

A Persistence Scope **may** be associated with a correlation identifier for diagnostics, tracing, logging, or observability.

Such an identifier is not part of the mandatory persistence semantics.

---

# 7. Consistency Requirement

Consistency requirements define the logical relationship that must hold between participating persistence operations.

A consistency requirement may specify that:

* related persistent state must represent one completed logical operation;
* required primary facts and dependent state must correspond;
* a failed operation must not be reported as successfully persisted;
* related persistence changes must satisfy an explicitly required atomicity guarantee;
* concurrent modifications must satisfy an explicitly required conflict policy.

Consistency requirements are defined at the persistence contract and higher-level operation boundaries.

They are not inferred from a particular storage technology.

---

# 8. Atomicity Requirement

Atomicity is a **property of a Persistence Scope**, not a universal property of all Persistence Scopes.

When atomicity is required:

> Either the required logical persistence result is successfully completed, or the scope must not be reported as successfully completed with a partial published result.

Atomicity does not prescribe a physical mechanism.

Possible implementation mechanisms include:

* database transactions;
* journaling;
* staged writes;
* atomic replacement;
* append-only logs;
* recovery procedures;
* provider-specific transactional facilities;
* other mechanisms capable of preserving the required semantic guarantee.

The architecture does not require any particular mechanism.

The absence of an atomicity requirement does **not** prescribe a specific non-atomic behavior.

Therefore the semantic contract distinguishes:

```text
Atomicity Required
```

from:

```text
Atomicity Not Required
```

rather than defining a universal `Atomic / Non-Atomic` transaction model.

---

# 9. Completion Semantics

Completion is a semantic outcome.

A Persistence Scope is considered successfully completed only when the required persistence result has been achieved according to its applicable persistence contracts and consistency requirements.

The architecture does not require a specific lifecycle such as:

```text
Created → Active → Completing → Completed
```

Such lifecycle states may exist in an implementation, but they are not part of the semantic contract.

The semantic outcome model is:

```text
Not Completed
      │
      ├── Completed
      │
      └── Failed / Aborted
```

A physical implementation may use additional intermediate states internally.

Those states must not become architectural transaction semantics unless explicitly introduced by a future contract.

---

# 10. Failure Semantics

Failure is an explicit semantic outcome.

If a Persistence Scope fails, the higher-level operation must not treat the required persistence result as successfully completed.

The exact failure behavior depends on the scope's requirements.

Possible outcomes include:

* no required state becomes published;
* previously published state remains unchanged;
* partial physical work is retained but is not considered published logical state;
* recovery is required;
* retry is possible;
* the higher-level operation receives a persistence failure.

Persistence errors remain semantic errors at the Persistence Contract boundary.

Examples include:

* `NotFound`;
* `AlreadyExists`;
* `StorageFailure`;
* concurrency conflict;
* unsupported persistence operation;
* integrity or consistency failure.

Physical provider errors must not leak into higher-level business semantics without translation.

---

# 11. Failure After Partial Physical Work

Physical work may occur before a Persistence Scope reaches its final semantic outcome.

For example:

```text
write temporary file
write journal entry
write object state
write register state
```

A failure during this process does not automatically mean that partially written physical state has become part of the published logical state.

The architecture explicitly distinguishes:

```text
Physical Intermediate State
        ≠
Published Logical Persistence State
```

This distinction allows implementations to use:

* temporary files;
* staging areas;
* journals;
* write-ahead mechanisms;
* recovery records;
* atomic replacement;
* provider-specific buffering.

The selected mechanism must preserve the semantic guarantees required by the Persistence Scope.

---

# 12. Aborted Scope

An aborted Persistence Scope is a scope whose required persistence result was not completed.

Abortion may occur because of:

* validation failure;
* persistence failure;
* concurrency conflict;
* application cancellation;
* infrastructure failure;
* explicit higher-level operation cancellation.

An aborted scope must not be reported as successfully completed.

The architecture does not prescribe a universal `abort()` API.

---

# 13. Concurrency Requirement

Concurrency guarantees are explicit when correctness depends on concurrent modification behavior.

A Persistence Scope may require:

* no explicit concurrency guarantee;
* conflict detection;
* rejection of conflicting concurrent modification;
* another explicitly defined semantic concurrency guarantee.

The Persistence Scope does not prescribe the mechanism used to achieve the guarantee.

Possible mechanisms include:

* revision checks;
* compare-and-swap;
* optimistic concurrency;
* locks;
* MVCC;
* provider-specific coordination.

Such mechanisms remain implementation details unless elevated into an explicit persistence contract.

---

# 14. No Implicit Last-Write-Wins

The architecture must not assume implicit `last-write-wins` behavior where concurrent modification correctness matters.

If concurrent modification can affect business correctness, the applicable persistence contract must explicitly define the required behavior.

Examples:

```text
Concurrent modification → conflict
```

or:

```text
Concurrent modification → explicitly defined merge
```

or another explicitly defined semantic result.

Silent overwriting must not be treated as an architectural default for correctness-sensitive state.

---

# 15. Isolation Semantics

Phase 5 does not define universal database isolation levels.

The architecture does not standardize:

* `READ UNCOMMITTED`;
* `READ COMMITTED`;
* `REPEATABLE READ`;
* `SERIALIZABLE`;
* snapshot isolation;
* MVCC semantics.

Instead:

> Operations participating in a Persistence Scope must be evaluated against the logical state required by their persistence contract.

If a particular operation requires stronger isolation or observation guarantees, those guarantees must be defined explicitly at the appropriate persistence boundary.

The physical mechanism remains provider-specific.

---

# 16. Durability

Durability is a semantic guarantee associated with successful completion where required by the applicable persistence contract.

Completion must not imply one universal durability level for every Persistence Scope.

Different persistence operations may have different durability requirements.

For example:

```text
Business-critical primary state
→ durable completion required
```

while:

```text
Optional derived cache
→ durable completion may not be required
```

Where durability is required, the implementation must ensure that successful completion does not falsely report persistence before the required durability guarantee has been achieved.

The physical definition of durability remains below the Storage Boundary.

---

# 17. Scope Boundary

A Persistence Scope must be explicit about which persistence operations participate in its consistency requirements.

The scope must not automatically become:

* global;
* application-wide;
* request-wide;
* process-wide;
* session-wide.

The existence of multiple persistence operations does not by itself imply that they belong to one Persistence Scope.

The higher-level operation determines the required persistence result and therefore the required scope boundary.

---

# 18. Cross-Resource Scopes

A Persistence Scope may span multiple logical or physical persistence resources.

For example:

```text
Document Persistence
        +
Register Movement Persistence
        +
Required Register State Persistence
```

may form one logical consistency boundary even when the underlying resources are physically distinct.

This is one of the primary reasons the Persistence Scope exists as an architectural concept above the Storage Provider.

The architecture does not require all participating resources to share:

* one database;
* one connection;
* one filesystem;
* one provider;
* one physical transaction.

If a cross-resource scope requires atomicity, the selected implementation mechanism must provide the required semantic guarantee.

Distributed transaction technology is not part of the Phase 5 contract.

---

# 19. Interaction with Posting

Posting produces accounting facts; it does not own persistence mechanics.

The responsibility chain remains:

```text
Posting Handler
    │
    └── generates MovementSet
              │
              ▼
       Posting / Application Layer
              │
              ├── validates required state
              ├── determines persistence result
              ├── establishes required Persistence Scope
              └── coordinates persistence
                         │
                         ▼
                 Persistence Contracts
```

A Posting Handler must not:

* open transactions;
* commit persistence;
* rollback persistence;
* manage storage providers;
* coordinate physical resources.

The Posting Handler remains responsible for business logic that produces the `MovementSet`.

The higher-level Posting Engine or application operation coordinates the persistence result.

---

# 20. Interaction with Register Persistence

Register persistence is a participant in the persistence model when register facts form part of the required persistence result.

For example:

```text
Posted Object State
+
MovementSet
+
Required Register State
```

may belong to one Persistence Scope when business correctness requires them to be coordinated.

The Persistence Scope does not change the semantic role of register facts.

Register facts remain primary accounting facts produced by posting.

Derived register state remains derived state and does not redefine the primary facts.

---

# 21. Provider Independence

Persistence Scope semantics must remain independent of the Storage Provider.

The Persistence Scope must not require:

* SQL transactions;
* filesystem transactions;
* ORM transactions;
* database sessions;
* provider-specific transaction handles;
* a particular locking mechanism;
* a particular journal format.

A provider may implement the required guarantee using mechanisms appropriate to its physical storage model.

The provider mechanism must remain below the Storage Boundary.

---

# 22. Provider Capability Limitation

A Storage Provider may have capabilities that are weaker than the guarantees required by a Persistence Scope.

In such a case, the architecture must not silently weaken the semantic requirement.

The system must instead:

1. select another implementation mechanism;
2. use a higher-level coordination mechanism;
3. reject the unsupported operation;
4. or otherwise explicitly handle the capability mismatch.

A provider must not redefine the business-required consistency semantics merely because its physical storage mechanism is limited.

---

# 23. Persistence Scope Does Not Own Business Semantics

A Persistence Scope coordinates persistence requirements.

It does not define:

* accounting rules;
* posting rules;
* valuation;
* workflow;
* authorization;
* document lifecycle;
* register business semantics;
* dependency rules.

Those remain the responsibility of their respective architectural layers.

The Persistence Scope only expresses the persistence guarantees required to preserve the result of those higher-level operations.

---

# 24. Semantic Contract Summary

The Persistence Scope establishes the following model:

```text
Business / Application Operation
            │
            ▼
Required Persistence Result
            │
            ▼
Persistence Scope
            │
            ├── Participating Operations
            ├── Consistency Requirements
            │      └── Atomicity, when required
            ├── Completion Semantics
            ├── Failure Semantics
            ├── Concurrency Requirements
            └── Durability Requirements
            │
            ▼
Persistence Contracts
            │
            ▼
Storage Boundary
            │
            ▼
Storage Provider
```

The central architectural rule is:

> **Persistence Scope defines the required semantic relationship between persistence operations; it does not define the physical mechanism used to achieve that relationship.**

---

# 25. Contract Invariants

The following invariants define the Persistence Scope semantic contract.

### P5-PSC1 — Explicit Scope Boundary

A Persistence Scope covers only persistence operations required to satisfy a defined higher-level persistence result.

### P5-PSC2 — Logical Consistency Boundary

A Persistence Scope is a logical consistency boundary and is independent of physical transaction technology.

### P5-PSC3 — Explicit Atomicity

Atomicity is required only where explicitly defined by the applicable persistence requirements.

### P5-PSC4 — No Partial Published State

Where atomicity is required, a failed scope must not be reported as successfully completed with a partial published logical result.

### P5-PSC5 — Physical Intermediate State Is Not Published State

Physical intermediate work does not automatically constitute published logical persistence state.

### P5-PSC6 — Semantic Completion

Successful completion means that the required persistence result has been achieved according to its applicable persistence contracts.

### P5-PSC7 — Explicit Failure

A failed or aborted scope must not be reported as successfully completed.

### P5-PSC8 — Explicit Concurrency

Concurrency guarantees must be explicitly defined where concurrent modification affects correctness.

### P5-PSC9 — No Implicit Last-Write-Wins

Implicit last-write-wins behavior must not be treated as a correctness guarantee.

### P5-PSC10 — No Universal Isolation Model

Phase 5 does not prescribe universal database isolation levels.

### P5-PSC11 — Required Durability

Where durability is part of successful completion, the implementation must satisfy the required durability guarantee before reporting successful completion.

### P5-PSC12 — Provider Independence

Persistence Scope semantics must not depend on a specific Storage Provider or physical storage technology.

### P5-PSC13 — Provider Mechanism Is Hidden

Physical mechanisms used to implement consistency remain below the Storage Boundary unless explicitly promoted into a future contract.

### P5-PSC14 — Business Semantics Stay Above Persistence

Persistence Scope coordinates persistence requirements but does not own business semantics.

---

# 26. Explicitly Out of Scope

The following are intentionally not defined by Step 5.2:

* universal `begin()` / `commit()` / `rollback()` API;
* generic transaction object;
* universal Unit of Work;
* universal repository abstraction;
* database isolation-level abstraction;
* database connection/session semantics;
* provider-independent locking API;
* provider-independent compare-and-swap API;
* universal optimistic concurrency API;
* nested Persistence Scope semantics;
* distributed transaction protocol;
* two-phase commit;
* saga orchestration;
* compensation workflow;
* recovery protocol;
* journal format;
* physical transaction implementation;
* physical schema;
* storage-specific transaction semantics.

These may be introduced later only when a concrete architectural requirement justifies them.

---

# 27. Resulting Architectural Position

Step 5.2 establishes the following architectural rule:

```text
Persistence Scope
    ≠ Transaction API
    ≠ Unit of Work
    ≠ Storage Provider
```

Instead:

```text
Persistence Scope
        ↓
Semantic Consistency Requirements
        ↓
Persistence Contracts
        ↓
Storage Boundary
        ↓
Provider-specific Mechanism
```

This preserves the separation between:

```text
Business Semantics
        ↓
Persistence Semantics
        ↓
Physical Storage Mechanism
```

while allowing a single logical persistence operation to coordinate multiple persistence resources when required.

---

# 28. Finalization Status

Step 5.2 is complete. The Persistence Scope semantic model is the governing abstraction for logical consistency across persistence operations.

It is intentionally independent from the physical transaction mechanism. The concrete persistence contracts and consistency/failure matrix implement the semantic rules established here without introducing a universal transaction API.

**Status: Final.**
