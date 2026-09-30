from __future__ import annotations

from accore.platform.object import ObjectInstance
from accore.platform.valuation import (
    ValuationEngine,
    ValuationLifecycleCoordinator,
    ValuationOperationIdentity,
    ValuationPlan,
    ValuationPreparationContext,
)

from .context import PostingPreparationContext
from .coordinator import PostingLifecycleOutcome, PostingLifecycleResult
from .identity import (
    DefaultPostingParticipantOperationIdentityFactory,
    PostingOperationIdentity,
    PostingParticipantOperationIdentityFactory,
)
from .movement_set import MovementSet


class ValuationPostingCoordinator:
    """Adapt valuation preparation and lifecycle semantics to Posting."""

    def __init__(
        self,
        engine: ValuationEngine,
        lifecycle: ValuationLifecycleCoordinator,
        operation_identity_factory: PostingParticipantOperationIdentityFactory | None = None,
    ) -> None:
        self._engine = engine
        self._lifecycle = lifecycle
        self._operation_identity_factory = (
            operation_identity_factory or DefaultPostingParticipantOperationIdentityFactory()
        )

    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        context: PostingPreparationContext,
    ) -> ValuationPlan:
        if movement_set.movements and any(
            movement.source_document_identity != document.identity
            for movement in movement_set.movements
        ):
            raise ValueError("Posting movements must belong to the posting document.")
        preparation_identity = ValuationOperationIdentity(
            self._operation_identity_factory.derive(
                context.operation_identity, "valuation", "prepare"
            )
        )
        valuation_context = ValuationPreparationContext(
            operation_identity=preparation_identity,
            replacement_document_identity=context.replacement_document_identity,
        )
        return self._engine.prepare(movement_set, valuation_context)

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        del document, movement_set
        if not isinstance(plan, ValuationPlan):
            raise TypeError("Valuation participant received an invalid posting plan.")
        valuation_operation_identity = ValuationOperationIdentity(
            self._operation_identity_factory.derive(operation_identity, "valuation", "establish")
        )
        result = self._lifecycle.establish(plan, valuation_operation_identity)
        return PostingLifecycleResult(
            PostingLifecycleOutcome(result.outcome.value),
            result.error,
        )

    def remove(
        self,
        document: ObjectInstance,
        operation_identity: PostingOperationIdentity,
    ) -> PostingLifecycleResult:
        valuation_operation_identity = ValuationOperationIdentity(
            self._operation_identity_factory.derive(operation_identity, "valuation", "remove")
        )
        result = self._lifecycle.remove(document.identity, valuation_operation_identity)
        return PostingLifecycleResult(
            PostingLifecycleOutcome(result.outcome.value),
            result.error,
        )
