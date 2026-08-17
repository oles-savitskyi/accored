
---

### `PHASE_2_CONFIGURATION_ACTIVATION_IMPLEMENTATION_PLAN.md`

```markdown
# Phase 2 — Configuration Activation Implementation Plan

**Status:** Planned  
**Version:** 1.0  
**Phase:** Phase 2 — Metadata Lifecycle / Configuration Loading  
**Step:** Step 5 — Configuration Activation Boundary

---

## 1. Purpose

This document defines the implementation plan for the Configuration Activation Boundary v1.0.

The implementation must realize the architecture defined in:

`PHASE_2_CONFIGURATION_ACTIVATION_BOUNDARY.md`

The implementation is intentionally limited to in-memory activation.

---

## 2. Implementation Goal

Implement the smallest complete activation boundary that can:

1. accept a validated `ConfigurationCandidate`;
2. reject candidates that are not activatable;
3. create an `ActiveConfiguration`;
4. publish it as the current configuration;
5. replace an existing active configuration;
6. preserve the previous active configuration when activation fails.

---

## 3. Proposed Module Structure

Add:

```text
src/accore/platform/configuration/
    activation.py

Update:

src/accore/platform/configuration/__init__.py

Add tests:

tests/unit/configuration/
    test_activation.py

Update:

tests/unit/configuration/test_configuration_public_api.py
4. ActiveConfiguration

Introduce:

@dataclass(frozen=True, slots=True)
class ActiveConfiguration:
    identity: ConfigurationIdentity
    version: ConfigurationVersion
    metadata_registry: MetadataRegistry

The object should be immutable at the object level.

The registry ownership semantics must remain consistent with the activation boundary design.

5. ConfigurationActivator

Introduce:

class ConfigurationActivator:
    def activate(
        self,
        candidate: ConfigurationCandidate,
    ) -> ActiveConfiguration:
        ...


    def current(self) -> ActiveConfiguration | None:
        ...

The activator should maintain the current active configuration in memory.

No persistence is required.

6. Activation Preconditions

activate() must require:

candidate.state == VALIDATED

If the candidate is in any other state, activation must fail.

The current active configuration must remain unchanged.

7. First Activation

Test and implement:

current() → None

followed by:

activate(validated_candidate)

which must result in:

current() → ActiveConfiguration
8. Replacement Activation

Test and implement:

activate(candidate_a)
activate(candidate_b)

The second activation must make candidate B the active configuration.

The active configuration returned by current() must correspond to B.

9. Failed Activation Isolation

Test:

active = A
candidate B = invalid activation state
activate(B) → failure
current() == A

This is a mandatory invariant.

10. Candidate Immutability During Activation

Activation must not mutate:

candidate identity;
candidate version;
candidate metadata registry contents.

The candidate remains a configuration artifact representing the loaded/validated configuration.

11. Metadata Registry Publication

Activation should publish the candidate's complete metadata registry.

The implementation should not recompile or selectively copy metadata.

Conceptually:

candidate.metadata_registry
        │
        ▼
active_configuration.metadata_registry

The exact future immutability mechanism for MetadataRegistry is not part of this step.

12. Public API

Update:

src/accore/platform/configuration/__init__.py

to expose:

ActiveConfiguration
ConfigurationActivator

Update the public API test accordingly.

13. Unit Test Matrix

test_activation.py should cover at least:

13.1. Initial state
current() is None
13.2. Successful first activation
VALIDATED candidate
        ↓
activate()
        ↓
ActiveConfiguration
13.3. Identity preservation

The active configuration preserves candidate identity.

13.4. Version preservation

The active configuration preserves candidate version.

13.5. Registry preservation

The active configuration exposes the candidate's complete metadata registry.

13.6. Replacement

Activation of B replaces active A.

13.7. Invalid candidate rejection

LOADED candidate cannot be activated.

13.8. Failed activation isolation

Failed activation leaves the existing active configuration unchanged.

13.9. Candidate remains unchanged

Activation does not mutate candidate metadata or identity/version.

14. Integration With Runtime

Step 5 should not yet redesign RuntimeResolver.

The existing runtime metadata resolution model remains unchanged.

The activation boundary should only establish the object that can later become the source of runtime metadata.

A later integration step may introduce:

ActiveConfiguration
        │
        ▼
RuntimeResolver

but this is not required for Step 5 implementation.

15. Error Model

Use the existing AcCore error hierarchy where appropriate.

If a dedicated activation error is required, introduce it only if the existing error model does not provide a suitable boundary error.

Do not introduce a large new error taxonomy for this step.

16. Validation and Tooling

Before committing the implementation, run:

pytest tests/unit/configuration -q
ruff check .
black .
black --check .
mypy src
pytest

The complete test suite must pass.

17. Commit Boundary

The Step 5 implementation should be committed separately from later runtime integration.

Recommended commit:

feat(configuration): add activation boundary

The commit should contain only:

activation model;
activator;
tests;
public API updates;
implementation documentation updates required by Step 5.
18. Completion Criteria

Step 5 is complete when:

ActiveConfiguration exists;
ConfigurationActivator exists;
only validated candidates can be activated;
first activation works;
replacement activation works;
failed activation preserves the previous active configuration;
candidate data is not mutated;
metadata registry is published as a complete snapshot;
public API tests pass;
configuration unit tests pass;
full test suite passes;
ruff passes;
black --check passes;
mypy passes;
documentation is synchronized;
implementation is committed and pushed.
19. Explicit Non-Goals

The following must not be implemented as part of Step 5:

persistent activation;
database storage;
configuration migration;
rollback;
version compatibility checking;
concurrent activation handling;
distributed locks;
hot reload;
multi-tenant activation;
configuration history;
registry freezing;
cache invalidation.

These concerns remain future architectural work.

20. Next Step

After successful Step 5 implementation and review, the next architectural question is the integration of the active configuration with the runtime metadata resolution boundary.

That work should be treated as a separate step rather than silently expanding the activation implementation.