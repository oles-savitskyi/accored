# Phase 2 — Configuration Loading Implementation Plan

**Status:** Planned  
**Version:** 1.0  
**Phase:** Phase 2 — Metadata → Runtime  
**Step:** Step 3 — Configuration Loading Boundary

---

## 1. Objective

Implement the minimum configuration loading path required to transform an
existing set of `Definition` objects into an isolated
`ConfigurationCandidate`.

Target flow:

```text
Definitions
    ↓
ConfigurationLoader
    ↓
MetadataCompiler
    ↓
candidate-local MetadataRegistry
    ↓
ConfigurationCandidate(state=LOADED)

The implementation must preserve all existing Phase 1 and Phase 2 contracts.

2. Preconditions

The following components already exist and are considered stable:

Definition;
CatalogDefinition;
AttributeDefinition;
Metadata;
CatalogMetadata;
MetadataCompiler;
MetadataRegistry;
ConfigurationIdentity;
ConfigurationVersion;
ConfigurationLifecycleState;
ConfigurationCandidate.

Current baseline:

f6b7db1 feat(configuration): add configuration candidate
3. Implementation Scope

Step 3 introduces:

src/accore/platform/configuration/loader.py

and:

tests/unit/configuration/test_loader.py

The existing configuration public API will be extended with
ConfigurationLoader.

No source abstraction is introduced.

No lifecycle manager is introduced.

No runtime integration is introduced.

4. Loader API

The initial implementation should expose:

class ConfigurationLoader:
    def __init__(self, compiler: MetadataCompiler) -> None:
        ...


    def load(
        self,
        definitions: Sequence[Definition],
        *,
        identity: ConfigurationIdentity,
        version: ConfigurationVersion,
    ) -> ConfigurationCandidate:
        ...

The exact concrete type of Definition should follow the existing definition
model.

The loader must not introduce a new definition abstraction.

5. Loader Construction

The loader receives the compiler through dependency injection:

compiler = MetadataCompiler(...)
loader = ConfigurationLoader(compiler)

The loader must not instantiate a compiler internally.

This allows:

deterministic tests;
explicit dependency ownership;
future compiler configuration;
separation between orchestration and compilation.
6. Loading Algorithm

The implementation sequence is:

1. Create MetadataRegistry
2. For each Definition:
   a. Compile definition
   b. Register compiled metadata
3. Create ConfigurationCandidate
4. Return candidate

Conceptually:

registry = MetadataRegistry()


for definition in definitions:
    metadata = compiler.compile(definition)
    registry.register(metadata)


return ConfigurationCandidate(
    identity=identity,
    version=version,
    metadata_registry=registry,
)

The exact compiler API must follow the existing implementation.

7. Registry Isolation

The registry must be created inside the load() operation.

Correct:

def load(...):
    registry = MetadataRegistry()

Incorrect:

class ConfigurationLoader:
    def __init__(...):
        self._registry = MetadataRegistry()

The loader must not retain candidate metadata between load operations.

8. Candidate Construction

Candidate construction occurs only after successful processing of all
definitions.

Therefore:

definition 1 → compile → register
definition 2 → compile → register
definition 3 → compile → register
                    │
                    ▼
              Candidate created

If any operation fails:

definition N
    ↓
error
    ↓
load() raises

and no candidate is returned.

9. Atomicity

No partial candidate may escape the loader.

The implementation does not need an explicit transaction object because the
candidate is not created until processing succeeds.

The local registry may contain partially processed metadata internally while
loading is in progress, but that registry must never become externally
observable as a ConfigurationCandidate.

10. Error Handling

The initial implementation should allow existing platform exceptions to
propagate unless an existing error boundary explicitly requires translation.

Do not add a new ConfigurationLoadingError solely for this step.

The implementation should preserve the underlying cause when translation is
required.

Expected failure sources include:

MetadataCompiler
    ↓
existing compilation / validation exception


MetadataRegistry
    ↓
duplicate registration
    ↓
existing registry exception

The precise mapping must follow the existing error architecture.

11. Public API

Update:

src/accore/platform/configuration/__init__.py

to export:

ConfigurationLoader

The expected public API becomes:

__all__ = [
    "ConfigurationCandidate",
    "ConfigurationIdentity",
    "ConfigurationLifecycleState",
    "ConfigurationLoader",
    "ConfigurationVersion",
]

Ordering should follow the project's existing formatting/style conventions.

12. Unit Tests

Create:

tests/unit/configuration/test_loader.py
Test 1 — Empty definitions

Loading an empty definition sequence should produce a valid candidate with an
empty registry.

Expected:

candidate.state == LOADED

and:

candidate.identity == supplied identity
candidate.version == supplied version
Test 2 — Single definition

Given one valid definition:

Definition
    ↓
Loader
    ↓
Candidate

the resulting candidate must contain the compiled metadata.

The test should verify the metadata can be retrieved from the candidate's
registry.

Test 3 — Multiple definitions

Given multiple valid definitions, all compiled metadata must be registered in
the same candidate-local registry.

Test 4 — Candidate isolation

Two separate load() calls must produce candidates with distinct registries:

candidate_a.metadata_registry is not candidate_b.metadata_registry
Test 5 — Compiler failure

If compilation of a definition fails:

load()
    ↓
CompilationError

No candidate should be returned.

Test 6 — Duplicate metadata identity

If two definitions compile to the same metadata identity, registration must
fail through the existing registry contract.

The loader must not silently overwrite existing metadata.

Test 7 — Loader does not activate

A successfully loaded candidate must always have:

LOADED

regardless of the definitions supplied.

13. Public API Tests

Update:

tests/unit/configuration/test_configuration_public_api.py

to include:

ConfigurationLoader

in both import/export verification and __all__ verification.

14. Vertical Integration Test

Step 3 should add or extend a Phase 2 vertical test only if the existing
vertical slice can exercise the new loading boundary without introducing
Standard Configuration-specific coupling.

The desired vertical flow is:

Definition
    ↓
ConfigurationLoader
    ↓
ConfigurationCandidate
    ↓
MetadataRegistry
    ↓
RuntimeResolver

However, RuntimeResolver integration is not required to close Step 3.

If such integration requires additional architecture, defer it.

15. Quality Gates

Before review:

pytest tests/unit/configuration -q
ruff check .
black --check .
mypy src
pytest

All must pass.

No existing tests may regress.

16. Review Gate

Step 3 implementation is complete only if:

Functional
loader accepts definitions;
loader compiles definitions;
loader creates candidate-local registry;
loader registers compiled metadata;
loader returns ConfigurationCandidate;
candidate is LOADED.
Isolation
every load operation creates a fresh registry;
registries are not shared between candidates;
no global metadata registry is used.
Atomicity
failed compilation does not return a candidate;
duplicate metadata identity does not overwrite existing metadata.
Architectural
loader does not create runtime;
loader does not activate configuration;
loader does not know Standard Configuration;
loader does not introduce a second compiler;
loader does not introduce a second registry mechanism.
Quality
pytest   ✓
ruff     ✓
black    ✓
mypy     ✓
17. Deferred Work

The following remain explicitly outside Step 3:

Configuration Sources
FileSystemConfigurationSource
PackageConfigurationSource
DatabaseConfigurationSource
RemoteConfigurationSource
Configuration Descriptor

A concrete ConfigurationDescriptor remains deferred.

Lifecycle Management
LOADED
   ↓
VALIDATED
   ↓
PREPARED
   ↓
READY
   ↓
ACTIVE
Runtime Integration

Candidate-to-runtime binding remains a subsequent step.

Configuration Persistence

Saving/loading configuration from persistent storage remains outside this
step.

Standard Bootstrap Migration

Existing Standard Configuration bootstrap code will be migrated only after
the generic loading boundary is proven.

18. Expected Result

After Step 3 the platform will have the following complete construction path:

┌──────────────┐
│ Definition   │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ ConfigurationLoader  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ MetadataCompiler     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ MetadataRegistry     │
│ candidate-local      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ ConfigurationCandidate│
│ state = LOADED       │
└──────────────────────┘

This establishes the first complete Configuration Loading Boundary while
leaving lifecycle management and runtime activation independent.

