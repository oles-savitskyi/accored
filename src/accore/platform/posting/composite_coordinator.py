from __future__ import annotations

from accore.platform.object import ObjectInstance

from .coordinator import (
    PostingLifecycleOutcome,
    PostingLifecycleResult,
    PostingResultPlan,
)
from .movement_set import MovementSet
from .register_coordinator import RegisterPostingResultCoordinator
from .valuation_coordinator import ValuationPostingCoordinator


class CompositePostingResultCoordinator:
    """Coordinate Register and Valuation lifecycle without distributed transactions."""

    def __init__(
        self,
        register: RegisterPostingResultCoordinator,
        valuation: ValuationPostingCoordinator,
    ) -> None:
        self._register = register
        self._valuation = valuation

    def prepare(self, document: ObjectInstance, movement_set: MovementSet) -> PostingResultPlan:
        register_plan = self._register.prepare(document, movement_set)
        valuation_plan = self._valuation.prepare(document, movement_set)
        return PostingResultPlan(
            register=register_plan,
            valuation=valuation_plan,
        )

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> PostingLifecycleResult:
        register_result = self._register.establish(document, movement_set, plan.register)
        if register_result.outcome is not PostingLifecycleOutcome.SUCCESS:
            return register_result

        valuation_result = self._valuation.establish(plan.valuation)
        return self._aggregate(register_result, valuation_result)

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult:
        register_result = self._register.remove(document)
        if register_result.outcome is not PostingLifecycleOutcome.SUCCESS:
            return register_result
        valuation_result = self._valuation.remove(document.identity)
        return self._aggregate(register_result, valuation_result)

    @staticmethod
    def _aggregate(
        first: PostingLifecycleResult,
        second: PostingLifecycleResult,
    ) -> PostingLifecycleResult:
        if first.outcome is PostingLifecycleOutcome.INDETERMINATE:
            return first
        if second.outcome is PostingLifecycleOutcome.INDETERMINATE:
            return second
        if first.outcome is PostingLifecycleOutcome.FAILURE:
            return first
        if second.outcome is PostingLifecycleOutcome.FAILURE:
            return second
        return PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)


__all__ = ["CompositePostingResultCoordinator"]
