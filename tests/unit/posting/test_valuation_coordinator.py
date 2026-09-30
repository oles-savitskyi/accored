from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation import Identifier
from accore.platform.posting import (
    DefaultPostingParticipantOperationIdentityFactory,
    PostingOperationIdentity,
    PostingPreparationContext,
    ValuationPostingCoordinator,
)
from accore.platform.posting.movement_set import MovementSet
from accore.platform.valuation import (
    ValuationEstablishmentOutcome,
    ValuationEstablishmentResult,
    ValuationOperationIdentity,
    ValuationPlan,
    ValuationPreparationContext,
    ValuationRemovalOutcome,
    ValuationRemovalResult,
)


@dataclass(frozen=True)
class FakeDocument:
    identity: Identifier


class RecordingEngine:
    def __init__(self) -> None:
        self.contexts: list[ValuationPreparationContext] = []
        self.plan = ValuationPlan(document_identity=Identifier.new(), operations=())

    def prepare(self, movement_set, context):
        del movement_set
        self.contexts.append(context)
        return self.plan


class RecordingLifecycle:
    def __init__(self) -> None:
        self.establish_calls: list[tuple[object, ValuationOperationIdentity]] = []
        self.remove_calls: list[tuple[Identifier, ValuationOperationIdentity]] = []

    def establish(self, plan, operation_identity):
        self.establish_calls.append((plan, operation_identity))
        return ValuationEstablishmentResult(ValuationEstablishmentOutcome.SUCCESS)

    def remove(self, document_identity, operation_identity):
        self.remove_calls.append((document_identity, operation_identity))
        return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)


def test_prepare_translates_posting_context_to_deterministic_valuation_context() -> None:
    engine = RecordingEngine()
    lifecycle = RecordingLifecycle()
    coordinator = ValuationPostingCoordinator(engine, lifecycle)
    document = FakeDocument(Identifier.new())
    parent = PostingOperationIdentity("posting-1")
    replacement = Identifier.new()

    plan = coordinator.prepare(
        document,
        MovementSet(()),
        PostingPreparationContext(
            operation_identity=parent,
            replacement_document_identity=replacement,
        ),
    )

    assert plan is engine.plan
    context = engine.contexts[0]
    assert context.operation_identity == ValuationOperationIdentity(
        _child_identity(parent, "prepare")
    )
    assert context.replacement_document_identity == replacement


def test_establish_and_remove_use_deterministic_child_identities() -> None:
    engine = RecordingEngine()
    lifecycle = RecordingLifecycle()
    coordinator = ValuationPostingCoordinator(engine, lifecycle)
    document = FakeDocument(Identifier.new())
    parent = PostingOperationIdentity("posting-1")

    coordinator.establish(document, MovementSet(()), engine.plan, parent)
    coordinator.remove(document, parent)

    assert lifecycle.establish_calls == [
        (engine.plan, ValuationOperationIdentity(_child_identity(parent, "establish")))
    ]
    assert lifecycle.remove_calls == [
        (document.identity, ValuationOperationIdentity(_child_identity(parent, "remove")))
    ]


def test_child_identity_derivation_is_deterministic_and_operation_specific() -> None:
    factory = DefaultPostingParticipantOperationIdentityFactory()
    parent = PostingOperationIdentity("posting-1")

    first = factory.derive(parent, "valuation", "remove")
    second = factory.derive(parent, "valuation", "remove")
    establish = factory.derive(parent, "valuation", "establish")

    assert first == second
    assert first != establish


def _child_identity(parent: PostingOperationIdentity, operation_type: str) -> str:
    from accore.platform.posting import DefaultPostingParticipantOperationIdentityFactory

    return DefaultPostingParticipantOperationIdentityFactory().derive(
        parent, "valuation", operation_type
    )
