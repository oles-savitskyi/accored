# Phase 6 — Step 5: Consistency, Failure & Reposting

## 1. Purpose

This document defines the semantic contract for consistency, failure handling, and reposting within Posting Architecture.

The purpose of this step is to establish:

* the logical consistency boundary of a Posting operation;
* the meaning of a required persistent accounting result;
* the semantic meaning of atomicity;
* failure semantics across the Posting lifecycle;
* behavior when persistent effects are partially established;
* semantics of indeterminate Posting outcomes;
* consistency requirements for Unposting;
* semantics of Reposting;
* the relationship between Reposting, retry, and idempotency;
* consistency requirements for dependencies and Posting events.

This step defines semantic guarantees and architectural boundaries.

It does NOT define a concrete transaction mechanism, rollback implementation, recovery subsystem, or physical persistence algorithm.


## 2. Relationship with Existing Architecture

Step 5 builds on the contracts established by:

* Posting Architecture;
* Posting Semantic Contract;
* Posting Lifecycle & Validation;
* Register Movement Contract;
* Movement Validation;
* Register Posting Contracts;
* Phase 5 Persistence Architecture;
* Phase 5 Storage Provider Boundary.

The resulting model is:

```text
Posting Request
        ↓
Posting Lifecycle
        ↓
MovementSet
        ↓
Movement Validation
        ↓
Register Acceptance
        ↓
Required Persistent Result
        ↓
Logical Completion
        ↓
Posting Events
```

Consistency and failure semantics apply to the complete logical Posting operation.

They MUST NOT introduce a second persistence architecture or bypass the Phase 5 persistence boundaries.

## 3. Consistency Model

A Posting operation is a logical accounting operation.

Its result is not limited to the generation of a MovementSet.

The logical Posting result consists of all mandatory persistent effects required for the Posting operation to be considered successfully completed.

Conceptually:

```text
Posting Operation
        ↓
MovementSet
        ↓
Validation
        ↓
Required Persistent Effects
        ↓
Logical Posting Result

The consistency model therefore distinguishes:

Generated Accounting Facts
        ≠
Validated Accounting Facts
        ≠
Required Persistent Accounting Result
        ≠
Logical Posting Completion
```

Successful Posting exists only when the required persistent accounting result has been established according to the applicable consistency boundary.

## 4. Posting as a Logical Consistency Unit

A Posting operation forms one logical consistency unit.

All persistent effects that are mandatory for successful completion of that Posting operation MUST be considered together when determining Posting success.

Such effects MAY include:

register accounting effects;
replacement or removal of previous accounting effects;
persistent document posting state, when applicable;
dependency-related persistent effects that form part of the Posting result;
other persistent effects explicitly required by the Posting contract.

The exact set of persistent effects is determined by the applicable Posting scenario.

The Posting Architecture MUST NOT declare success based only on one successfully persisted effect when other mandatory effects remain unresolved.

## 5. Required Persistent Result

The Required Persistent Result is the persistent accounting state that MUST exist for a Posting operation to be considered logically successful.

It is defined by the Posting scenario and applicable architecture boundaries.

For example:

```text
MovementSet
    ↓
Register acceptance
    ↓
Required Persistent Accounting Result
```

The Required Persistent Result is a semantic concept.

It does not prescribe:

a database representation;
a transaction implementation;
a storage provider;
a commit protocol;
a rollback mechanism;
a journal;
a recovery worker.

The Posting Engine coordinates establishment of the Required Persistent Result through applicable persistence/application services.

## 6. Persistence Scope Boundary

When multiple persistent effects form one logical Posting result, they MUST participate in the applicable Persistence Scope.

The Persistence Scope defines the logical consistency boundary for those persistent effects.

Conceptually:

                Posting Operation
                       ↓
          ┌────────────┼────────────┐
          ↓            ↓            ↓
      Register     Document     Dependency
       Effect       State         Effect
          └────────────┼────────────┘
                       ↓
              Persistence Scope
                       ↓
              Logical Result

The Posting Architecture determines which effects belong to the logical Posting result.

The Persistence Architecture determines how the applicable Persistence Scope is implemented.

Posting MUST NOT prescribe the physical consistency mechanism.

The concrete Persistence Scope API and implementation remain outside the scope of this step.

## 7. Atomicity Semantics

Posting has semantic atomicity.

Semantic atomicity means:

A Posting operation MUST NOT be exposed as successfully completed while the mandatory persistent accounting result is only partially established.

Therefore:

```text
Complete Required Result
        →
    Success

Incomplete Required Result
        →
    Failure or Indeterminate Outcome
```

Semantic atomicity does NOT mean that Posting Architecture defines a particular physical transaction mechanism.

The implementation MAY use any persistence mechanism capable of satisfying the required semantic consistency guarantees.

Physical transaction behavior remains the responsibility of Persistence Architecture and its implementation.

## 8. Failure Model

Posting failure means that the Posting operation did not establish a successful logical Posting result.

Failure MAY occur at different stages.

Conceptually:

```text
Precondition Failure
        ↓
Handler Failure
        ↓
Movement Validation Failure
        ↓
Register Acceptance Failure
        ↓
Persistence Failure
        ↓
Dependency / Consistency Failure
        ↓
Event Publication Failure
```

These failure categories do not have identical consistency semantics.

Failures that occur before Logical Completion MUST prevent successful Posting.

A failure related to event publication MUST NOT automatically imply that the Required Persistent Result was not established.

Event publication failure therefore requires separate handling from accounting-result establishment.

The concrete event delivery and recovery semantics are outside the scope of this step.

These categories describe failure causes.

They MUST NOT automatically be interpreted as separate persistent Posting lifecycle states.

A failure MUST NOT be reported as successful Posting.

## 9. Failure Before Persistent Effects

A Posting operation MAY fail before any persistent accounting effect is established.

Examples include:

invalid Posting preconditions;
Posting Handler resolution failure;
Posting Handler execution failure;
incomplete MovementSet;
Movement validation failure;
Register Posting Contract failure.

In such cases:

```text
Posting Failure
        ↓
No Required Persistent Accounting Result
```

The Posting operation MUST NOT publish a successful Posting event.

No partial accounting result may be exposed as a successful Posting result.

## 10. Failure During Persistent Coordination

A Posting operation MAY fail while establishing the Required Persistent Result.

Examples include:

register persistence failure;
document persistence failure;
dependency persistence failure;
persistence service failure;
consistency boundary failure.

The Posting operation MUST NOT report success unless the Required Persistent Result has been established.

The concrete handling of already-created physical effects belongs to the applicable Persistence Architecture.

Posting Architecture defines the semantic outcome, not the physical rollback mechanism.

## 11. Failure After Partial Persistent Effects

A physical implementation MAY encounter a situation where some persistent effects have been established while other mandatory effects have not.

Such a state MUST NOT be exposed as successful Posting.

Conceptually:

```text
Mandatory Effect A   → established
Mandatory Effect B   → not established

        ↓

Required Persistent Result
        ↓
     incomplete
```

The resulting Posting outcome is either:

a clean failure, when the system can establish that the logical result was not completed and the consistency boundary guarantees the required state;
or an Indeterminate Outcome, when the system cannot determine whether the Required Persistent Result was established.

The semantic contract does not prescribe how partial physical effects are removed or reconciled.

## 12. Indeterminate Posting Outcome

An Indeterminate Posting Outcome exists when the system cannot reliably determine whether the Required Persistent Result was established.

For example:

```text
Persistence operation
        ↓
communication / infrastructure uncertainty
        ↓
actual persistent state unknown
```

In such a case the system MUST NOT silently interpret the operation as successful.

It MUST also NOT silently interpret the operation as a clean failure if the actual accounting state remains unknown.

The distinction is:

Known Success
Known Failure
Indeterminate Outcome

An Indeterminate Outcome is an infrastructure/consistency condition, not a successful Posting result.

Recovery, reconciliation, retry, and operator-facing handling mechanisms are outside the scope of this semantic contract.

## 13. Movement-Level Failure

Movement-level failure occurs when a generated Movement does not satisfy applicable semantic requirements.

Examples include:

invalid structure;
invalid register reference;
invalid dimension;
invalid resource;
invalid attribute;
invalid movement type;
Register Posting Contract violation.

Such a Movement MUST NOT be accepted for Register processing.

Movement-level failure therefore prevents the corresponding Posting operation from establishing its Required Persistent Result.

## 14. Register-Level Failure

Register-level failure occurs when the target Register cannot accept or process a Movement according to its applicable Register Posting Contract or Register semantics.

The Register MUST NOT silently reinterpret or repair an invalid Movement in order to make it acceptable.

Register rejection MUST propagate into the Posting result.

Conceptually:

```text
Movement
    ↓
Register Posting Contract
    ↓
Rejected
    ↓
Posting Failure
```

No successful Posting result may be exposed when mandatory Register effects remain unestablished.

## 15. Persistence-Level Failure

Persistence-level failure occurs when the required persistent accounting result cannot be established through the applicable persistence/application boundary.

Examples include:

persistence operation failure;
consistency boundary failure;
inability to establish required persistent state;
infrastructure failure affecting persistence outcome.

Persistence-level failure is distinct from Movement validation failure.

The Posting Architecture MUST preserve this distinction because:

```text
Invalid Accounting Fact
        ≠
Failure to Persist Valid Accounting Fact
```

The concrete storage and transaction behavior remains outside the Posting contract.

## 16. Posting Success Boundary

Posting success is established only after:

Posting preconditions have succeeded;
Posting Handler has been resolved;
Posting Context has been created;
Handler execution has completed;
a complete MovementSet has been generated;
MovementSet validation has succeeded;
applicable Register Posting Contracts have been satisfied;
the Required Persistent Result has been established;
all other mandatory Posting stages have completed;
the operation has reached Logical Completion.

Only then may Posting success be exposed.

Conceptually:

```text
Required Persistent Result
        ↓
Logical Completion
        ↓
Posting Success
        ↓
Posting Events
```

Successful Posting MUST represent a completed logical accounting result.

## 17. Posting Failure Boundary

Posting failure exists when a mandatory Posting stage cannot be successfully completed.

A failed Posting operation MUST NOT be reported as successfully completed.

Failure MUST preserve the distinction between:

no persistent effect established;
known incomplete persistent result;
Indeterminate Outcome.

The concrete mechanism for ensuring or restoring consistency is outside the Posting semantic contract.

## 18. Unposting Consistency

Unposting is a logical accounting operation that removes the applicable accounting effects previously established by Posting.

Conceptually:

```text
Posted Document
        ↓
Unposting Request
        ↓
Identify Existing Posting Effects
        ↓
Remove Applicable Accounting Effects
        ↓
Logical Completion
        ↓
DocumentUnposted
```

Unposting MUST be treated as one logical consistency unit.

If removal of applicable accounting effects is mandatory for successful Unposting, partial completion MUST NOT be exposed as successful Unposting.

The concrete mechanism for identifying and removing physical effects remains outside this step.

## 19. Reposting Semantics

Reposting establishes a new accounting result from the current semantic state of the source document.

The core principle is:

Reposting rebuilds accounting effects from the current document state rather than treating the previous MovementSet as the source of truth.

Conceptually:

```text
Already Posted Document
        ↓
Reposting Request
        ↓
Current Document State
        ↓
Generate New MovementSet
        ↓
Validate New MovementSet
        ↓
Establish New Persistent Accounting Result
        ↓
Logical Completion
        ↓
DocumentReposted
```

The document remains the source of truth.

The previous accounting result does not become the semantic source for the new result.

## 20. Reposting Preconditions

Reposting MUST operate only when its applicable preconditions are satisfied.

These MAY include:

the document exists;
the document is in a state that permits Reposting;
the current document state is available;
the required Posting Handler can be resolved;
required Posting Context inputs are available;
existing accounting effects can be identified when replacement is required.

Concrete document-state rules are outside the scope of this step unless defined by the specific Posting scenario.

## 21. Reposting Result

A successful Reposting operation establishes the accounting result corresponding to the current document state.

Conceptually:

```text
Current Document State
        ↓
New MovementSet
        ↓
Validated MovementSet
        ↓
New Required Persistent Result
```

The resulting accounting state MUST correspond to the current semantic document state.

A successful Reposting MUST result in a persistent accounting state that corresponds to the current semantic document state.

Obsolete accounting effects that are no longer part of the current Posting result MUST NOT remain as part of the effective accounting result.

The mechanism by which obsolete physical effects are identified, removed, replaced, or reconciled belongs to the applicable Persistence / Application boundary.

## 22. Reposting and Existing Movements

Reposting MUST NOT use mutation of the existing MovementSet as its primary semantic mechanism.

The semantic operation is:

```text
Current Document State
        ↓
New MovementSet
```

rather than:

```text
Previous MovementSet
        ↓
Manual Mutation
        ↓
New Result
```

Existing accounting effects MAY be removed, replaced, or otherwise reconciled by the applicable persistence/application mechanism.

However, those mechanisms do not change the semantic principle that the new Posting result is generated from the current source document state.

## 23. Reposting and Failure

Reposting is subject to the same consistency requirements as Posting.

If generation or validation of the new MovementSet fails:

```text
Reposting Failure
        ↓
No Successful New Accounting Result
```

If establishment of the new Required Persistent Result fails, Reposting MUST NOT be reported as successful.

If the system cannot determine whether the new Required Persistent Result was established, the outcome is Indeterminate.

Reposting MUST NOT silently report success merely because part of the replacement process completed.

## 24. Reposting and Determinism

For equivalent relevant semantic inputs, Reposting MUST generate the same semantic MovementSet as a fresh Posting operation against the same document state.

The relevant inputs include, as applicable:

current document semantic state;
relevant metadata;
relevant reference state;
Posting Context inputs;
accounting time/environment inputs.

Reposting MUST NOT derive its accounting semantics from:

runtime object identity;
previous Movement object identity;
storage layout;
arbitrary collection ordering;
uncontrolled system time;
uncontrolled external state.

This preserves the deterministic Posting contract established in Step 2.

## 25. Reposting vs Idempotency

Reposting, retry, and idempotency are distinct concepts.

Retry:
```text
same logical request
        ↓
retry operation
```

Idempotency:
```text
repeat same request
        ↓
same logical effect
```

Reposting:
```text
current document state
        ↓
new MovementSet
        ↓
new accounting result
```

Retry describes execution behavior.

Idempotency describes repeated-request semantics.

Reposting describes rebuilding accounting effects from current source document state.

The implementation MUST NOT treat these concepts as interchangeable.

## 26. Dependency Consistency

Posting MAY interact with dependency state and restoration workflows through the applicable integration boundary.

Dependency-related effects that form part of the Required Persistent Result MUST participate in the applicable consistency boundary.

Conceptually:

```text
Posting Result
     │
     ├── Register Effects
     ├── Document State
     └── Dependency Effects
              ↓
       Logical Consistency Unit
```

Dependency management itself remains outside Posting Handler responsibility.

Concrete dependency update, restoration, reconciliation, and consistency mechanisms are outside the scope of this step.

## 27. Event Consistency

Posting events represent successful logical completion.

Therefore:

```text
Logical Completion
        ↓
Posting Event
```

A successful event MUST NOT be published before the Required Persistent Result has been established.

This applies to:

DocumentPosted;
DocumentUnposted;
DocumentReposted.

No success event may be used to infer successful Posting before the Posting operation reaches its success boundary.

If Posting has an Indeterminate Outcome, a successful Posting event MUST NOT be emitted merely because the operation was initiated or partially executed.

The semantic contract does not prescribe the physical event transport mechanism.

Event publication occurs after the Posting operation has reached Logical Completion.

Therefore, failure to publish or deliver a Posting event MUST NOT be interpreted as proof that the Required Persistent Result was not established.

Event publication success and accounting-result establishment are distinct semantic outcomes.

The concrete handling of event delivery failure is outside the scope of this step.

## 28. Recovery Boundary

Recovery is required only when the physical implementation can produce states in which the logical Posting result cannot immediately be established or determined.

Recovery MAY include mechanisms such as:

reconciliation;
retry;
repair;
restoration;
operator intervention.

However, this step does not define a Recovery subsystem.

The semantic boundary is:

```text
Posting Architecture
        ↓
defines required result
        ↓
Persistence Architecture
        ↓
defines physical consistency/recovery mechanisms
```

Posting MUST expose enough semantic information to distinguish known success, known failure, and Indeterminate Outcome.

The concrete recovery mechanism remains outside the scope of Phase 6 Step 5.

## 29. Consistency Invariants

The following invariants are normative.

### PST-CFR-01 — Logical Consistency Unit

A Posting operation is one logical accounting consistency unit.

### PST-CFR-02 — Required Result

Posting success requires establishment of the Required Persistent Result.

### PST-CFR-03 — No Partial Success

A partially established Required Persistent Result MUST NOT be exposed as successful Posting.

### PST-CFR-04 — Semantic Atomicity

Posting MUST provide semantic atomicity regardless of the concrete physical persistence mechanism.

### PST-CFR-05 — Persistence Scope

All mandatory persistent effects belonging to one logical Posting result MUST participate in the applicable Persistence Scope.

### PST-CFR-06 — Physical Mechanism Independence

Posting semantics MUST NOT prescribe a physical transaction or persistence mechanism.

### PST-CFR-07 — Success Boundary

Posting success exists only after Logical Completion.

### PST-CFR-08 — Event Boundary

Posting success events MUST occur only after Logical Completion.

### PST-CFR-09 — Unposting Consistency

Unposting MUST be treated as one logical consistency operation.

### PST-CFR-10 — Reposting Source of Truth

Reposting MUST derive its new accounting result from the current source document state.

### PST-CFR-11 — Reposting Result

Successful Reposting MUST establish the accounting result corresponding to the current document state.

### PST-CFR-12 — Reposting Determinism

Equivalent semantic Posting inputs MUST produce equivalent semantic MovementSets.

### PST-CFR-13 — Idempotency Distinction

Reposting MUST NOT be defined as idempotency.

### PST-CFR-14 — Retry Distinction

Retry MUST NOT be defined as Reposting.

### PST-CFR-15 — Indeterminate Outcome

An unknown persistent outcome MUST NOT be silently interpreted as success.

### PST-CFR-16 — Failure Transparency

Failure at any mandatory Posting stage MUST prevent successful Posting completion.

### PST-CFR-17 — Register Failure Propagation

Failure to establish mandatory Register effects MUST prevent successful Posting.

### PST-CFR-18 — Dependency Consistency

Mandatory dependency effects MUST participate in the applicable consistency boundary.

### PST-CFR-19 — Phase 5 Boundary

Consistency handling MUST NOT bypass Persistence Architecture or Storage Provider boundaries.

### PST-CFR-20 — No Handler Consistency Ownership

Posting Handler MUST NOT own persistence consistency, transaction control, rollback, or recovery.

## 30. Failure Invariants

The following failure invariants are normative.

### PST-CFR-F01

A failed Posting operation MUST NOT be reported as successful.

### PST-CFR-F02

Movement validation failure MUST prevent persistence acceptance of the invalid Movement.

### PST-CFR-F03

Register acceptance failure MUST prevent successful establishment of the corresponding mandatory accounting result.

### PST-CFR-F04

Persistence failure MUST prevent successful Posting unless the Required Persistent Result has nevertheless been reliably established.

### PST-CFR-F05

Partial physical effects MUST NOT be interpreted as a successful logical Posting result.

### PST-CFR-F06

Indeterminate persistent state MUST remain distinguishable from both known success and known failure.

### PST-CFR-F07

No success event MUST be emitted for a Posting operation that has not reached Logical Completion.

### PST-CFR-F08

Failure handling MUST NOT require Posting Handler to perform rollback or recovery.

## 31. Reposting Invariants

The following Reposting invariants are normative.

### PST-CFR-R01 — Current State

Reposting uses the current semantic state of the source document.

### PST-CFR-R02 — New MovementSet

Reposting generates a new MovementSet rather than mutating the previous MovementSet as the primary semantic mechanism.

### PST-CFR-R03 — Validation

The new MovementSet MUST pass all applicable validation and Register acceptance requirements.

### PST-CFR-R04 — Consistency

The new accounting result MUST satisfy the same logical consistency guarantees as ordinary Posting.

### PST-CFR-R05 — No Obsolete Result

A successful Reposting MUST NOT leave obsolete accounting effects that contradict the current Posting result.

### PST-CFR-R06 — Failure

Reposting failure MUST NOT be reported as successful Reposting.

### PST-CFR-R07 — Indeterminate Reposting

An unknown result of Reposting MUST remain Indeterminate and MUST NOT be silently reported as success.

### PST-CFR-R08 — Determinism

Equivalent current document state and applicable Posting inputs MUST produce equivalent Reposting MovementSets.

## 32. Explicit Non-Goals

This step does NOT define:

concrete Python APIs;
concrete Posting Engine implementation;
concrete Posting Context API;
concrete Posting Handler API;
concrete MovementSet implementation;
concrete Movement persistence API;
concrete Register Service API;
transaction API;
BEGIN TRANSACTION;
COMMIT;
ROLLBACK;
SAVEPOINT;
isolation levels;
locking strategy;
journal implementation;
undo log;
recovery worker;
outbox implementation;
retry count or retry policy;
exact Persistence Scope implementation;
exact rollback algorithm;
exact reconciliation algorithm;
exact dependency restoration algorithm;
event transport implementation;
idempotency-key implementation;
database schema;
Inventory-specific reposting rules;
Standard Configuration implementation.

## 33. Step 5 Acceptance Criteria

Step 5 is complete when:

Posting is defined as a logical consistency unit.
Required Persistent Result is explicitly defined.
Persistence Scope is established as the applicable consistency boundary.
Semantic atomicity is defined without prescribing physical transactions.
Posting failure semantics are defined.
Partial persistent effects are explicitly distinguished from successful Posting.
Indeterminate Posting Outcome is explicitly defined.
Movement-level and Register-level failures are distinguished.
Persistence-level failure is explicitly defined.
Posting success boundary is explicitly defined.
Unposting consistency is defined.
Reposting semantics are defined.
Reposting is explicitly based on current document state.
Reposting does not rely on mutation of the previous MovementSet as the primary semantic mechanism.
Reposting, retry, and idempotency are explicitly distinguished.
Dependency effects are covered by the applicable consistency boundary when they form part of the Posting result.
Posting events are restricted to the successful logical completion boundary.
Recovery remains outside the Posting semantic contract.
No concrete transaction, rollback, recovery, or persistence API is introduced.
Phase 5 Persistence and Storage Provider boundaries remain intact.
Event publication failure is explicitly distinguished from failure to establish the Required Persistent Result.

## 34. Architecture Review

Architecture Review: PENDING

Review result:

Blockers: TBD
Major architectural issues: TBD
Minor alignment issues: TBD
Required alignments: TBD

This section is intentionally left pending until the architecture review of Step 5 is completed.

## 35. Related Architecture

docs/architecture/posting/POSTING_ARCHITECTURE.md
docs/architecture/posting/POSTING_LIFECYCLE.md
docs/architecture/posting/POSTING_HANDLERS.md
docs/architecture/posting/POSTING_CONTEXT.md
docs/architecture/posting/MOVEMENT_VALIDATION.md
docs/architecture/posting/REGISTER_POSTING_CONTRACTS.md
docs/implementation/PHASE_6_STEP_2_POSTING_SEMANTIC_CONTRACT.md
docs/implementation/PHASE_6_STEP_3_POSTING_LIFECYCLE_AND_VALIDATION.md
docs/implementation/PHASE_6_STEP_4_REGISTER_MOVEMENT_CONTRACT.md
Phase 5 Persistence Architecture
Phase 5 Storage Provider Boundary

## 36. Step 5 Status

Step 5 — Consistency, Failure & Reposting

Status: DRAFT