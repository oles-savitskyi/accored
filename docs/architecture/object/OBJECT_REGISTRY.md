# Object Registry

**Version:** 1.1
**Status:** Deferred Architecture Specification
**Phase:** 4 — Object Runtime
**Architecture Baseline:** `architecture-core-3.0`

---

# 1. Purpose

This document defines the architectural status of Object Registry in AcCoreD.

The key decision is that a global Object Registry is **not required by the
current Object Runtime architecture**.

Object Instances are created and operated through explicit runtime
references.

No Object Registry is introduced during Phase 4 unless a concrete
architectural requirement demonstrates that centralized object registration
is necessary.

---

# 2. Current Status

Object Registry is intentionally deferred.

```text
Object Registry
      ↓
NOT IMPLEMENTED

This is an intentional architectural decision, not an implementation gap.

The current Object Runtime does not require a registry to satisfy:

Object Identity;
Object Instance creation;
Object State;
Object Context;
Object Lifecycle;
RuntimeResolver integration;
Catalog / Assortment vertical slice.
3. Architectural Position

The current Object Runtime flow is:

RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance

Object Instances are explicit runtime objects.

Their existence does not imply the existence of a global collection or
registry.

The current model therefore does not require:

Object Registry
      ↓
Object Instance

as an intermediate architectural boundary.

4. Why No Registry Is Required

A registry is useful when the system needs centralized discovery,
coordination, ownership, or lifecycle management of multiple objects.

Phase 4 does not currently establish such a requirement.

The current responsibilities can be fulfilled directly:

RuntimeResolver
    → resolves Runtime Object Type

ObjectCreator
    → creates Object Instance

ObjectLifecycle
    → manages Object Instance lifecycle

ObjectContext
    → carries explicit runtime context

Introducing a registry at this stage would add a global ownership mechanism
without a demonstrated architectural need.

5. Object Identity Does Not Require a Registry

Object Identity is sufficient to identify an individual Object Instance.

The current technical representation is the existing immutable
foundation.Identifier.

Therefore:

Object Identity
      ↓
Identifier

does not imply:

Identifier
      ↓
Object Registry

Identity and centralized discovery are separate concerns.

An Object Instance can carry a valid Object Identity without being registered
globally.

6. Object Creation Does Not Require a Registry

Object Creation is owned by an explicit Object Creation Boundary.

The flow is:

Runtime Object Type
        +
Object Context
        ↓
Object Creation Boundary
        ↓
Object Instance

Creation does not require insertion into a global registry.

The creation boundary must not:

create a global registry;
register every newly created object implicitly;
perform global object discovery;
acquire hidden global state.
7. Object Lifecycle Does Not Require a Registry

Object Lifecycle operates on an explicit Object Instance.

The lifecycle is:

CREATED
   ↓
ACTIVE
   ↓
DISPOSED

Lifecycle operations do not require centralized registry ownership.

In particular:

ObjectLifecycle
      ≠
ObjectRegistry

A future lifecycle coordination requirement may justify additional
architecture, but no such requirement exists in the current Phase 4 model.

8. Object Context Does Not Require a Registry

Object Context provides explicit runtime context for an Object Instance.

The relationship is:

RuntimeConfigurationContext
        ↓
Object Context
        ↓
Object Instance

Object Context must not become a service locator or hidden object registry.

It must not provide:

global object discovery;
global configuration discovery;
implicit dependency resolution;
object ownership management.
9. RuntimeResolver Does Not Require a Registry

RuntimeResolver resolves Runtime Object Types.

Its responsibility is:

Metadata Identity
      +
RuntimeConfigurationContext
      ↓
Runtime Object Type

It does not resolve or manage individual Object Instances.

Therefore RuntimeResolver does not require an Object Registry.

The separation remains:

RuntimeResolver
      ↓
Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance
10. Catalog Integration Does Not Require a Registry

The Phase 4 vertical slice uses Standard Configuration Assortment.

The flow is:

Assortment Metadata
      ↓
RuntimeResolver
      ↓
CatalogRuntime
      ↓
Object Creation Boundary
      ↓
Assortment Object Instance

Multiple Assortment instances can therefore exist without a global registry:

CatalogRuntime
   ├── Assortment Object A
   ├── Assortment Object B
   └── Assortment Object C

Each instance has its own Object Identity and Object State.

No central registration mechanism is required by this scenario.

11. Registry vs Persistence

An Object Registry must not be confused with persistence.

These are separate concepts:

Object Registry
      ≠
Storage

A registry, if introduced in the future, would provide runtime organization
or discovery.

Storage would provide persistence.

Neither concept is implied by the other.

An Object Instance can:

exist without a registry;
exist without Storage;
have an Object Identity without persistence.
12. Registry vs Object Identity

Object Identity answers:

Which individual object is this?

A registry would answer questions such as:

Which objects are currently known to this runtime?

or:

Where can a particular runtime object be found?

These are different responsibilities.

Therefore:

Object Identity
      ≠
Object Registry

Object Identity is already established by Phase 4.

Object Registry remains deferred.

13. Registry vs Object Lifecycle

Object Lifecycle answers:

What runtime lifecycle state does this Object Instance have?

A registry would potentially answer:

Which Object Instances are currently managed or discoverable?

These concerns must remain separate.

The current lifecycle model therefore does not imply a registry.

14. Conditions That Could Justify a Future Registry

An Object Registry may become architecturally justified if a future
requirement establishes a concrete need for one or more of the following:

centralized runtime object discovery;
explicit runtime object ownership;
lifecycle coordination across multiple objects;
identity-based object lookup within a defined runtime scope;
controlled object retention;
coordination of object references;
another capability that cannot be provided cleanly through explicit
object references.

Any such requirement must be demonstrated before introducing the registry.

15. Future Registry Requirements

If a registry is introduced in the future, its architecture must explicitly
define:

ownership scope;
lifetime;
identity lookup semantics;
registration semantics;
unregistration semantics;
duplicate identity behavior;
disposal behavior;
concurrency behavior;
interaction with Object Context;
interaction with persistence;
memory ownership;
whether registration is mandatory or optional.

These decisions must not be inferred implicitly from the existence of
Object Identity.

16. Possible Future Registry Shape

No concrete implementation is prescribed at this stage.

A future registry could conceptually look like:

ObjectRegistry
    ↓
Object Identity
    ↓
Object Instance

but the following questions must be answered first:

Who owns the registry?
What is its lifetime?
What is its scope?
Who registers objects?
Who removes them?
Is registration automatic?
What happens on disposal?
Is lookup local or global?

Until those questions are driven by a real requirement, implementation should
remain deferred.

17. Explicit Non-Goals

This document does not define:

a registry implementation;
a global singleton registry;
a process-wide object map;
an application-wide object cache;
a persistence identity map;
a repository;
a Unit of Work;
a dependency injection container;
a service locator.

None of these mechanisms is required by the current Phase 4 Object Runtime.

18. Architectural Invariants

I1. Object Identity does not imply Object Registry.

I2. Object Instance creation does not require Object Registry.

I3. Object Lifecycle does not require Object Registry.

I4. Object Context does not provide Object Registry semantics.

I5. RuntimeResolver does not own Object Registry.

I6. Catalog / Assortment does not require Object Registry.

I7. Object Runtime does not contain a global object registry.

I8. A future registry requires an explicit architectural justification.

I9. Registry semantics must not be introduced implicitly through another
Object Runtime component.

I10. Registry and Storage are separate architectural concepts.

19. Relationship to Phase 4

Phase 4 explicitly establishes:

Object Identity
Object Instance
Object State
Object Context
Object Lifecycle
Object Creation Boundary

It does not establish:

Object Registry

The Phase 4 implementation must therefore remain registry-free unless a
specific requirement appears during implementation or audit.

20. Relationship to Future Architecture

A future Object Registry may become useful when AcCoreD introduces more
complex runtime scenarios such as:

coordinated business operations;
object references;
long-lived object graphs;
caching;
interactive sessions;
Unit of Work;
repository integration;
concurrency coordination.

Those capabilities must be designed independently before being used as
justification for a registry.

A future registry must not become a mechanism for compensating for missing
architectural boundaries elsewhere.

21. Conclusion

AcCoreD deliberately does not introduce an Object Registry during Phase 4.

The current Object Runtime is sufficiently expressed by:

Runtime Object Type
      ↓
Object Creation Boundary
      ↓
Object Instance
      ↓
Object Lifecycle

Object Identity provides individual identity.

Explicit references provide object access.

Object Context provides execution context.

Object Lifecycle provides lifecycle semantics.

Storage remains a future persistence concern.

Therefore:

No Object Registry
        ↓
by design

An Object Registry may be introduced later only when a concrete architectural
requirement demonstrates that centralized runtime object discovery,
ownership, or coordination is necessary.