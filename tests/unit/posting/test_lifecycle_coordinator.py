from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation import Identifier
from accore.platform.posting import (
    CompositePostingResultCoordinator,
    PostingLifecycleOutcome,
    PostingLifecycleResult,
    RegisterPostingPlan,
)
from accore.platform.posting.movement_set import MovementSet


@dataclass(frozen=True)
class FakeDocument:
    identity: Identifier


class RecordingRegisterCoordinator:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.result = PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)

    def prepare(self, document, movement_set):
        self.calls.append("register.prepare")
        return RegisterPostingPlan(movements=movement_set)

    def establish(self, document, movement_set, plan):
        self.calls.append("register.establish")
        return self.result

    def remove(self, document):
        self.calls.append("register.remove")
        return self.result


class RecordingValuationCoordinator:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.plan = object()
        self.result = PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)

    def prepare(self, document, movement_set):
        self.calls.append("valuation.prepare")
        return self.plan

    def establish(self, plan):
        self.calls.append("valuation.establish")
        assert plan is self.plan
        return self.result

    def remove(self, document_identity):
        self.calls.append("valuation.remove")
        return self.result


def test_prepare_creates_explicit_composite_plan_without_establishing_effects() -> None:
    register = RecordingRegisterCoordinator()
    valuation = RecordingValuationCoordinator()
    coordinator = CompositePostingResultCoordinator(register, valuation)
    movement_set = MovementSet(())
    document = FakeDocument(Identifier.new())

    plan = coordinator.prepare(document, movement_set)

    assert plan.register.movements is movement_set
    assert plan.valuation is valuation.plan
    assert register.calls == ["register.prepare"]
    assert valuation.calls == ["valuation.prepare"]


def test_establish_uses_the_prepared_valuation_plan() -> None:
    register = RecordingRegisterCoordinator()
    valuation = RecordingValuationCoordinator()
    coordinator = CompositePostingResultCoordinator(register, valuation)
    movement_set = MovementSet(())
    document = FakeDocument(Identifier.new())
    plan = coordinator.prepare(document, movement_set)

    result = coordinator.establish(document, movement_set, plan)

    assert result.outcome is PostingLifecycleOutcome.SUCCESS
    assert register.calls == ["register.prepare", "register.establish"]
    assert valuation.calls == ["valuation.prepare", "valuation.establish"]


def test_remove_stops_before_valuation_when_register_removal_is_indeterminate() -> None:
    register = RecordingRegisterCoordinator()
    register.result = PostingLifecycleResult(PostingLifecycleOutcome.INDETERMINATE)
    valuation = RecordingValuationCoordinator()
    coordinator = CompositePostingResultCoordinator(register, valuation)
    document = FakeDocument(Identifier.new())

    result = coordinator.remove(document)

    assert result.outcome is PostingLifecycleOutcome.INDETERMINATE
    assert register.calls == ["register.remove"]
    assert valuation.calls == []


def test_establish_does_not_run_valuation_after_register_failure() -> None:
    register = RecordingRegisterCoordinator()
    register.result = PostingLifecycleResult(PostingLifecycleOutcome.FAILURE)
    valuation = RecordingValuationCoordinator()
    coordinator = CompositePostingResultCoordinator(register, valuation)
    movement_set = MovementSet(())
    document = FakeDocument(Identifier.new())
    plan = coordinator.prepare(document, movement_set)

    result = coordinator.establish(document, movement_set, plan)

    assert result.outcome is PostingLifecycleOutcome.FAILURE
    assert register.calls[-1] == "register.establish"
    assert valuation.calls == ["valuation.prepare"]
