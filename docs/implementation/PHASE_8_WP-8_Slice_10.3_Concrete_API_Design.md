WP-8 — Slice 10.3
Concrete API Design — Projected Repost Preparation State

Status: Proposed for Review
Scope: accore.platform.valuation + valuation posting adapter
Depends on: Slice 10.1, Slice 10.2, Slice 9
Does not include: implementation, recovery, Posting lifecycle completion

1. Slice objective

Slice 10.3 introduces a read-only valuation preparation state that allows Repost preparation to evaluate the replacement document against a virtual state in which the old document's effective valuation effect has already been removed.

The authoritative state is never mutated during preparation.

Required lifecycle remains:

prepare(replacement)
        ↓
remove(original)
        ↓
establish(replacement)

The preparation phase must therefore behave as if:

effective_state_after_virtual_remove(original)

were already authoritative.

No reversal facts, operation records, totals mutations, or persistence writes are performed by the projection.

2. Architectural decisions
2.1 Authoritative source

The projection is built from authoritative valuation facts, not from the already materialized available-layer view.

Therefore:

ValuationFactPersistence
        ↓
effective valuation facts
        ↓
projected preparation state
        ↓
ValuationEngine.prepare()

This is necessary because an available-layer reader does not contain enough information to reconstruct consumed quantities that must become available again.

2.2 Preparation state abstraction

Introduce a read-only semantic boundary:

class ValuationPreparationState(Protocol):
    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        ...

The ValuationEngine consumes this abstraction and does not know whether it represents:

authoritative state;
projected replacement state.

This keeps projection semantics outside the engine's FIFO/planning algorithm.

2.3 State factory

Introduce:

class ValuationPreparationStateFactory(Protocol):
    def authoritative(self) -> ValuationPreparationState:
        ...

    def for_replacement(
        self,
        document_identity: Identifier,
    ) -> ValuationPreparationState:
        ...

The factory is responsible for selecting/building the appropriate read-only state.

authoritative() represents normal preparation.

for_replacement(document_identity) represents:

the effective state that would exist if the specified document were removed successfully.

3. Concrete projected-state API

The concrete implementation is:

class DefaultValuationPreparationStateFactory:
    def __init__(
        self,
        fact_persistence: ValuationFactPersistence,
    ) -> None:
        ...

    def authoritative(self) -> ValuationPreparationState:
        ...

    def for_replacement(
        self,
        document_identity: Identifier,
    ) -> ValuationPreparationState:
        ...

However, the authoritative implementation should not duplicate existing valuation-state logic.

Where the current code already has an appropriate ValuationLayerReader implementation, authoritative() should return/adapt that existing reader.

The new implementation is primarily required for:

for_replacement(...)
4. Projected state representation

The projected state itself is immutable/read-only:

@dataclass(frozen=True, slots=True)
class ProjectedValuationPreparationState:
    layers: tuple[ValuationLayer, ...]

It implements:

class ValuationPreparationState(Protocol):
    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        ...

layers must already represent the effective projected state.

The engine therefore does not need to know how the projection was produced.

Using a frozen dataclass is consistent with the project's immutable value-object approach; Python's dataclass model supports frozen=True for preventing ordinary field reassignment.

5. Projection algorithm

For:

factory.for_replacement(old_document_identity)

the implementation performs the following logical operation.

Step 1 — load authoritative facts
all persisted valuation facts
Step 2 — determine effective facts

Use the same existing active/effective-fact semantics already established by valuation removal and Slice 9 rebuild.

No new independent definition of "active fact" is introduced.

Step 3 — identify old document's effective facts

Partition the effective facts belonging to:

old_document_identity

into:

old layer establishments
old consumptions
Step 4 — reverse old consumptions in memory

For every effective consumption of the old document:

layer X
quantity Q

the projected state restores Q to that layer.

Step 5 — remove old establishments in memory

Every layer established by the old document is excluded from the projected state.

Step 6 — return immutable state

The result is:

ProjectedValuationPreparationState

and nothing has been persisted.

6. Important semantic constraint

Projection is not a second implementation of ValuationCoordinator.remove().

Instead, both operations must use the same semantic rules for determining whether a document can be removed.

The desired relationship is:

projection(old)
    ≈
state_after_successful_remove(old)

but:

projection(old)
    !=
remove(old)

in terms of side effects.

7. Removal conflict handling

Consider:

A → establishes L1
B → consumes L1

Then:

repost(A)

cannot produce an arbitrary projected state in which L1 simply disappears.

The projection must detect that the effective state cannot legally represent removal of A.

Therefore:

factory.for_replacement(A)

must fail using the existing valuation validation/error semantics.

We should not introduce a new parallel removal error hierarchy in this slice.

The exact existing exception/result type should be reused after inspecting the current coordinator validation path.

8. ValuationEngine API

The existing Slice 10.2 preparation API remains:

def prepare(
    self,
    movement_set: ValuationMovementSet,
    context: ValuationPreparationContext,
) -> ValuationPlan:
    ...

The engine receives a ValuationPreparationState dependency.

Conceptually:

class ValuationEngine:
    def __init__(
        self,
        preparation_state: ValuationPreparationState,
        ...
    ) -> None:
        ...

and uses:

layers = self._preparation_state.find_available_layers(
    valuation_key,
)

No projected_state parameter is added to prepare().

No is_repost flag is added.

No conditional valuation logic based on posting lifecycle is added.

9. Selecting the state

The state selection belongs to:

ValuationPostingCoordinator

because this is the valuation-specific adapter that already interprets:

ValuationPreparationContext.replacement_document_identity

The generic PostingEngine remains unaware of valuation projection.

Conceptually:

def prepare(
    self,
    document: PostingDocument,
    movement_set: MovementSet,
    operation_identity: PostingOperationIdentity,
) -> ValuationPlan:
    ...

The coordinator derives:

ValuationPreparationContext(
    operation_identity=valuation_operation_identity,
    replacement_document_identity=...,
)

and chooses:

replacement_document_identity is None
    → authoritative state

replacement_document_identity is not None
    → projected replacement state
10. Important implementation refinement

I do not want the ValuationEngine itself to switch its state dynamically during prepare().

Instead, the coordinator should construct/use the appropriate engine state boundary.

The preferred dependency direction is:

ValuationPostingCoordinator
        │
        ├── ValuationPreparationStateFactory
        │
        └── ValuationEngine
                │
                └── ValuationPreparationState

This avoids introducing mutable engine state such as:

engine.set_preparation_state(...)

which would be dangerous for deterministic preparation and concurrent/reentrant use.

11. Context semantics

The existing:

@dataclass(frozen=True, slots=True)
class ValuationPreparationContext:
    operation_identity: ValuationOperationIdentity
    replacement_document_identity: Identifier | None = None

remains unchanged.

Its semantics become explicit:

Normal establish
replacement_document_identity = None
Repost replacement preparation
replacement_document_identity = old document identity

The context tells the valuation posting coordinator which preparation state is required.

It does not itself contain the state.

12. Plan identity semantics

Slice 10.2 deterministic identity rules remain unchanged.

For the same:

movement_set
operation_identity
replacement_document_identity
authoritative facts

preparation must produce the same semantic plan.

The projection itself must not introduce random identities.

In particular:

ProjectedValuationPreparationState

must never generate:

Identifier.new()

for layers, consumptions, or any planning identity.

This preserves the Slice 10.2 deterministic-preparation contract.

13. Semantic fingerprint

Projection does not become part of the persistence identity.

The semantic fingerprint remains based on the valuation plan's semantic contents.

The replacement document identity may influence deterministic opaque planning identities through the existing Slice 10.2 identity mechanism, but must not become an artificial semantic difference in the valuation fingerprint.

Therefore:

same effective projected valuation
        ↓
same semantic plan
        ↓
same semantic fingerprint

regardless of the persistence identity derivation mechanism.

14. No persistence mutation

The following are explicitly forbidden during:

factory.for_replacement(...)

and during preparation using the projected state:

append valuation fact
append operation record
persist valuation result
persist cost movement
update totals
delete fact
mutate fact
create reversal fact

The only permitted operation against authoritative persistence is read access.

This is a strict architectural invariant.

15. No reuse of reversal facts

A tempting implementation would be:

load old document
construct reversal facts
apply reversal in memory
prepare

This is rejected.

Reversal facts are authoritative historical facts and belong to the actual remove() lifecycle.

Slice 10.3 must not create a second representation of historical reversal facts.

The projection is a derived transient read model, not a valuation operation.

16. Relationship to Slice 9 rebuild

Slice 9 remains the authoritative derived-state rebuild mechanism.

No new rebuild implementation is introduced.

The relationship is:

authoritative valuation facts
        │
        ├── DefaultValuationRebuilder
        │       → persistent derived state
        │
        └── ValuationPreparationStateFactory
                → transient projected preparation state

These are intentionally separate because one is persistent derived-state reconstruction and the other is a temporary read-only preparation view.

17. Tests

The implementation must add tests covering at least the following.

17.1 Projection is read-only

Before:

facts_before
results_before
movements_before
balances_before

After:

factory.for_replacement(document)

all authoritative persistence state must remain identical.

17.2 Remove old layer
A establishes L1

Projection for A:

L1 not available
17.3 Restore old consumption
A establishes L1
B consumes Q from L1

Projection for B:

L1.quantity_available += Q
17.4 Combined document
B:
    consumes L1
    establishes L2

Projection for B:

L1 → consumption restored
L2 → removed

This is a mandatory test because it validates both projection directions simultaneously.

17.5 FIFO behavior

Given:

L1
L2
B consumes from L1

the projected state must make L1 available again and the subsequent preparation must evaluate FIFO against:

L1, L2

rather than:

L2
17.6 External dependency conflict
A establishes L1
B consumes L1

Projection for A must fail according to the existing valuation removal validation semantics.

It must not silently fabricate a valid state.

17.7 Determinism

Repeated:

factory.for_replacement(A)
engine.prepare(...)

with unchanged authoritative facts must produce equivalent plans.

17.8 Existing preparation regression

All existing non-Repost preparation scenarios must continue to use the authoritative state unchanged.

18. Files / components in scope

Expected implementation surface:

src/accore/platform/valuation/
    preparation_state.py        # new state/projection contracts
    engine.py                   # consume ValuationPreparationState
    coordinator.py              # only if integration requires adjustment

src/accore/platform/posting/
    valuation_coordinator.py    # select projected state for replacement

tests/unit/valuation/
    test_preparation_state.py
    test_engine.py              # extend existing tests where appropriate

tests/unit/posting/
    test_valuation_coordinator.py

The exact filename may be adjusted to the repository's current module organization if inspection shows a better existing integration point. The API contract above is the invariant; file naming is not.

19. Explicit non-goals

Slice 10.3 does not implement:

ESTABLISH recovery descriptor;
unified valuation recovery;
Repost execution itself;
Repost failure recovery;
Posting recovery;
event publication;
persistence of preparation state;
PostingOperationRecord;
mutable posting lifecycle state;
new transaction boundaries.

Those belong to later Slice 10 stages.

20. Acceptance criteria

Slice 10.3 is complete only when all of the following are true:

ValuationPreparationState is a read-only semantic boundary.
Authoritative and projected preparation states use the same engine contract.
Projection is derived from authoritative valuation facts.
Old document consumptions are virtually restored.
Old document layer establishments are virtually removed.
External-consumer conflicts are detected using existing removal semantics.
No persistence mutation occurs during projection/preparation.
ValuationEngine.prepare() remains deterministic.
Existing Slice 10.2 identity semantics remain intact.
Generic Posting remains unaware of valuation projection.
Slice 9 rebuild remains the sole derived-state rebuild implementation.
All existing tests remain green.
New projection/FIFO/conflict/read-only tests are green.
ruff check . passes.
black --check . passes.
mypy src passes.
