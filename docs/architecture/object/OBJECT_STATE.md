# Object State

**Version:** 1.1
**Status:** Architecture Specification
**Phase:** 4 — Object Runtime
**Architecture Baseline:** `architecture-core-3.0`

---

# 1. Purpose

This document defines the Object State model of AcCoreD.

Object State describes the current runtime state of an individual
`ObjectInstance`.

Object State belongs to the Object Runtime and is independent from physical
persistence.

The purpose of this model is to provide the minimum generic state semantics
required for Object Runtime lifecycle management without introducing a
generalized state machine, persistence state model, or workflow engine.

---

# 2. Scope

This document defines:

- Object State;
- the state values used by Object Runtime;
- initial state semantics;
- the relationship between Object State and Object Identity;
- the relationship between Object State and Object Lifecycle;
- the separation between runtime state and persistent state.

This document does not define:

- persistence state;
- database state;
- dirty tracking;
- Unit of Work;
- transactions;
- optimistic locking;
- generalized state machines;
- workflow state;
- business-specific state models.

---

# 3. Architectural Position

Object State belongs to the individual Object Instance.

The relationship is:

```text
Runtime Object Type
        ↓
Object Instance
        ↓
Object State

Object State does not belong to:

Metadata;
Metadata Identity;
Runtime Object Type;
Configuration;
RuntimeConfigurationContext;
Storage.

The Object Runtime therefore owns runtime object state semantics without
owning physical persistence.

4. Object State Model

The initial generic Object Runtime state model contains three states:

CREATED
ACTIVE
DISPOSED

These states represent the runtime lifecycle condition of an individual
Object Instance.

They do not represent business-specific object states.

For example, a future Assortment object may have business concepts such as
"available", "blocked", or "discontinued". Such concepts are not part of the
generic Object State model.

5. State Definitions
5.1 CREATED

CREATED indicates that an Object Instance has been created by the Object
Creation Boundary but has not yet entered the active runtime state.

Every newly created Object Instance enters CREATED.

The initial state is established by the Object Runtime itself.

Callers cannot select an alternative initial state during object
construction.

5.2 ACTIVE

ACTIVE indicates that the Object Instance has entered the active runtime
state and may participate in normal runtime object operations permitted by
its contract.

Transition into ACTIVE is an explicit Object Lifecycle operation.

Object activation is not Configuration Activation.

In particular:

Object Lifecycle Activation
        ≠
Configuration Activation

Activating an Object Instance must not modify the active runtime
configuration.

5.3 DISPOSED

DISPOSED indicates that the Object Instance has left normal runtime use.

A disposed Object Instance must not be used for normal runtime operations.

Disposal is an Object Lifecycle concern.

It does not imply:

deletion from Storage;
database deletion;
archival;
cancellation of a business object;
deactivation of configuration.

Those meanings belong to other architectural layers.

6. Initial State

Object creation always establishes:

ObjectInstance
      ↓
ObjectState.CREATED

The constructor of ObjectInstance must not expose an argument allowing the
caller to choose the initial state.

This prevents callers from bypassing the Object Runtime lifecycle boundary.

The initial state is therefore a runtime invariant.

7. Object State and Object Identity

Object Identity and Object State are independent concepts.

Object Identity
      ≠
Object State

Object Identity identifies the individual Object Instance.

Object State describes its current runtime condition.

The existing immutable foundation.Identifier is used as the technical
representation of Object Identity.

Therefore:

Identifier
    ↓
Object Instance Identity

ObjectState
    ↓
Object Instance Runtime State

Changing Object State must not change Object Identity.

8. Object State Ownership

Each Object Instance owns its runtime state.

Two Object Instances must not implicitly share one mutable Object State.

For example:

Object Instance A
    ├── Identity A
    └── State A

Object Instance B
    ├── Identity B
    └── State B

Even when both instances have the same Runtime Object Type, their runtime
state is independent.

9. Object State and Equality

Object Instance equality is based on Object Identity.

It is not based on Object State.

Therefore, two Object Instance representations carrying the same Object
Identity remain equal even if their runtime state differs.

Conceptually:

Identity A == Identity B
        ↓
ObjectInstance A == ObjectInstance B

regardless of:

State A != State B

Object State must therefore never become part of Object Identity semantics.

10. Object State and Lifecycle

Object State provides the state representation used by Object Lifecycle.

The intended lifecycle is:

CREATE
  ↓
CREATED
  ↓
ACTIVE
  ↓
DISPOSED

State values describe the lifecycle condition.

Lifecycle operations own the rules governing transitions between those
states.

Object State itself is not a generalized transition engine.

The separation is:

Object State
    ↓
represents current state

Object Lifecycle
    ↓
controls legal transitions
11. Object State and Persistence

Object State is a runtime concept.

It must not be interpreted as persistent state.

The distinction is:

Object State
    ≠
Persistent State

An Object Instance may exist in runtime state without any physical
persistence having occurred.

For example:

Create Object Instance
        ↓
State = CREATED
        ↓
No Storage access required

Object Runtime therefore does not require Storage merely to establish or
maintain the basic runtime state of an Object Instance.

12. Object State and Storage Boundary

The Object Runtime must not introduce a direct dependency from Object State
to Storage.

In particular, Object State must not:

read from Storage;
write to Storage;
manage persistence transactions;
determine database persistence status;
perform synchronization with a repository.

Future persistence architecture may define how runtime state is represented
persistently, but that mapping is outside the scope of this document.

13. Object State and Configuration Lifecycle

Object State is independent from Configuration Lifecycle.

The distinction is:

Configuration Lifecycle
        ≠
Object Lifecycle

and:

Configuration State
        ≠
Object State

Creating, activating, or disposing an Object Instance must not activate,
deactivate, or otherwise mutate the runtime configuration.

Likewise, changing the active configuration must not silently mutate the
state of an already existing Object Instance.

14. Object State and Runtime Context

Object State operates within an explicit Object Context.

The context is associated with the RuntimeConfigurationContext snapshot
under which the Object Instance exists.

The relationship is:

RuntimeConfigurationContext
        ↓
Object Context
        ↓
Object Instance
        ↓
Object State

Object State itself does not resolve configuration and does not access
configuration binding.

15. State Transition Responsibility

State transitions are owned by the Object Lifecycle boundary.

The Object State model does not provide generalized transition orchestration.

The lifecycle boundary is responsible for:

validating transitions;
rejecting illegal transitions;
protecting disposed objects;
maintaining deterministic lifecycle semantics.

This separation prevents Object State from becoming a generalized workflow or
state-machine subsystem.

16. Explicit Non-Goals

The Object State model does not implement:

generalized state machines;
business state machines;
workflow state;
dirty tracking;
persistence state tracking;
Unit of Work;
repository state;
transaction state;
optimistic locking;
concurrency state;
version state.

These capabilities may be introduced by later architectural layers when
required.

17. Architectural Invariants

The following invariants apply:

I1. Every Object Instance has exactly one runtime Object State.

I2. Every newly created Object Instance starts in CREATED.

I3. The initial state cannot be selected by the Object Instance caller.

I4. Object State is independent from Object Identity.

I5. Object State is independent from Metadata Identity.

I6. Object State is independent from Runtime Object Type identity.

I7. Object State is independent from persistent state.

I8. Object State has no direct Storage dependency.

I9. Object Lifecycle owns state transitions.

I10. Object Lifecycle is independent from Configuration Lifecycle.

I11. Object Instances of the same Runtime Object Type maintain independent
runtime state.

I12. Object State does not participate in Object Instance equality.

18. Relationship to Object Runtime

The resulting Object Runtime model is:

RuntimeConfigurationContext
        ↓
Object Context
        ↓
Runtime Object Type
        ↓
Object Creation Boundary
        ↓
Object Instance
    ├── Object Identity
    ├── Object Type
    ├── Object State
    └── Object Context
        ↓
Object Lifecycle

Storage remains outside this boundary.

Object Runtime
      ↓
Future Persistence Boundary
      ↓
Storage
19. Implementation Correspondence

The current implementation represents Object State as the generic
ObjectState abstraction used by ObjectInstance.

The initial values are:

CREATED
ACTIVE
DISPOSED

ObjectInstance establishes CREATED during construction.

Lifecycle operations are implemented separately from the state declaration.

The implementation must preserve the architectural separation defined in
this document.

20. Conclusion

Object State provides the minimal runtime state model required by AcCoreD
Object Runtime.

It identifies the runtime condition of an individual Object Instance without
becoming a persistence model, workflow engine, or generalized state machine.

The canonical distinction is:

Object Identity
      ≠
Object State
      ≠
Persistent State

Object State is therefore a local runtime concern owned by Object Runtime and
controlled through the Object Lifecycle boundary.