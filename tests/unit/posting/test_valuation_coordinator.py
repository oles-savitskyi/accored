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
    ValuationRecoveryOutcome,
    ValuationRecoveryResult,
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
        self.recovery_calls: list[ValuationOperationIdentity] = []
        self.recovery_result = ValuationRecoveryResult(ValuationRecoveryOutcome.SUCCESS)

    def establish(self, plan, operation_identity):
        self.establish_calls.append((plan, operation_identity))
        return ValuationEstablishmentResult(ValuationEstablishmentOutcome.SUCCESS)

    def remove(self, document_identity, operation_identity):
        self.remove_calls.append((document_identity, operation_identity))
        return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)

    def prepare_establish(self, plan, operation_identity):
        self.prepare_establish_call = (plan, operation_identity)
        from accore.platform.valuation import (
            ValuationEstablishPreparationOutcome,
            ValuationEstablishPreparationResult,
        )

        return ValuationEstablishPreparationResult(ValuationEstablishPreparationOutcome.SUCCESS)

    def recover(self, operation_identity):
        self.recovery_calls.append(operation_identity)
        return self.recovery_result


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


def test_prepare_establish_uses_establish_child_identity() -> None:
    engine = RecordingEngine()
    lifecycle = RecordingLifecycle()
    coordinator = ValuationPostingCoordinator(engine, lifecycle)
    document = FakeDocument(Identifier.new())
    parent = PostingOperationIdentity("posting-1")

    result = coordinator.prepare_establish(document, MovementSet(()), engine.plan, parent)

    assert result.outcome.value == "success"
    assert lifecycle.prepare_establish_call == (
        engine.plan,
        ValuationOperationIdentity(_child_identity(parent, "establish")),
    )


def test_recover_orders_remove_before_establish() -> None:
    engine = RecordingEngine()
    lifecycle = RecordingLifecycle()
    coordinator = ValuationPostingCoordinator(engine, lifecycle)
    parent = PostingOperationIdentity("posting-1")

    result = coordinator.recover(parent)

    assert result.outcome.value == "success"
    assert lifecycle.recovery_calls == [
        ValuationOperationIdentity(_child_identity(parent, "remove")),
        ValuationOperationIdentity(_child_identity(parent, "establish")),
    ]


def test_recover_stops_after_remove_failure() -> None:
    engine = RecordingEngine()
    lifecycle = RecordingLifecycle()
    lifecycle.recovery_result = ValuationRecoveryResult(ValuationRecoveryOutcome.FAILURE)
    coordinator = ValuationPostingCoordinator(engine, lifecycle)
    parent = PostingOperationIdentity("posting-1")

    result = coordinator.recover(parent)

    assert result.outcome.value == "failure"
    assert lifecycle.recovery_calls == [
        ValuationOperationIdentity(_child_identity(parent, "remove")),
    ]
