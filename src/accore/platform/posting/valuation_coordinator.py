from __future__ import annotations

from accore.platform.object import ObjectInstance
from accore.platform.valuation import (
    ValuationEngine,
    ValuationLifecycleCoordinator,
    ValuationPlan,
)

from .coordinator import PostingLifecycleOutcome, PostingLifecycleResult
from .movement_set import MovementSet


class ValuationPostingCoordinator:
    """Adapt valuation preparation and lifecycle semantics to Posting."""

    def __init__(
        self,
        engine: ValuationEngine,
        lifecycle: ValuationLifecycleCoordinator,
    ) -> None:
        self._engine = engine
        self._lifecycle = lifecycle

    def prepare(self, document: ObjectInstance, movement_set: MovementSet) -> ValuationPlan:
        if movement_set.movements and any(
            movement.source_document_identity != document.identity
            for movement in movement_set.movements
        ):
            raise ValueError("Posting movements must belong to the posting document.")
        return self._engine.prepare(movement_set)

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
    ) -> PostingLifecycleResult:
        del document, movement_set
        if not isinstance(plan, ValuationPlan):
            raise TypeError("Valuation participant received an invalid posting plan.")
        result = self._lifecycle.establish(plan)
        return PostingLifecycleResult(
            PostingLifecycleOutcome(result.outcome.value),
            result.error,
        )

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult:
        result = self._lifecycle.remove(document.identity)
        return PostingLifecycleResult(
            PostingLifecycleOutcome(result.outcome.value),
            result.error,
        )
