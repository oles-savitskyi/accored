from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from accore.platform.foundation import Identifier

from .errors import ValuationPersistenceError, ValuationValidationError
from .facts import ValuationConsumption, ValuationFact, ValuationLayer
from .persistence import ValuationFactPersistence, ValuationResultPersistence
from .plan import (
    ConsumptionPlan,
    LayerEstablishmentPlan,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationPlan,
)
from .results import CostBalance, CostMovement
from .totals import CostTotalsEngine
from .validation import ValuationPlanValidator


class ValuationEstablishmentOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationEstablishmentResult:
    outcome: ValuationEstablishmentOutcome
    error: Exception | None = None


class ValuationCoordinator(Protocol):
    def establish(self, plan: ValuationPlan) -> ValuationEstablishmentResult: ...


class DefaultValuationCoordinator:
    """Orchestrate valuation establishment without owning physical transactions."""

    def __init__(
        self,
        *,
        fact_persistence: ValuationFactPersistence,
        result_persistence: ValuationResultPersistence,
        totals_engine: CostTotalsEngine,
        validator: ValuationPlanValidator,
    ) -> None:
        self._fact_persistence = fact_persistence
        self._result_persistence = result_persistence
        self._totals_engine = totals_engine
        self._validator = validator

    def establish(self, plan: ValuationPlan) -> ValuationEstablishmentResult:
        try:
            self._validator.validate(plan)
        except ValuationValidationError as exc:
            return ValuationEstablishmentResult(
                ValuationEstablishmentOutcome.FAILURE,
                exc,
            )

        try:
            facts, movements = self._construct(plan)
            self._fact_persistence.append(facts)
            self._result_persistence.append_movements(movements)

            balances: dict[object, CostBalance] = {}
            for movement in movements:
                balances[movement.valuation_key] = self._totals_engine.apply(movement)
            for balance in balances.values():
                self._result_persistence.replace_balance(balance)
        except ValuationPersistenceError as exc:
            outcome = (
                ValuationEstablishmentOutcome.FAILURE
                if exc.rollback_guaranteed
                else ValuationEstablishmentOutcome.INDETERMINATE
            )
            return ValuationEstablishmentResult(outcome, exc)

        return ValuationEstablishmentResult(ValuationEstablishmentOutcome.SUCCESS)

    def _construct(
        self,
        plan: ValuationPlan,
    ) -> tuple[tuple[ValuationFact, ...], tuple[CostMovement, ...]]:
        references: dict[PlannedLayerReference, Identifier] = {}
        facts: list[ValuationFact] = []
        movements: list[CostMovement] = []

        for operation in plan.operations:
            if isinstance(operation, LayerEstablishmentPlan):
                identity = Identifier.new()
                references[operation.reference] = identity
                facts.append(
                    ValuationLayer(
                        identity=identity,
                        valuation_key=operation.valuation_key,
                        quantity=operation.quantity,
                        total_cost=Decimal(0),
                        source_document_identity=operation.source_document_identity,
                        source_movement_identity=operation.source_movement_identity,
                        created_at=operation.created_at,
                    )
                )
                movements.append(
                    CostMovement(
                        identity=Identifier.new(),
                        valuation_key=operation.valuation_key,
                        quantity=operation.quantity,
                        cost=Decimal(0),
                        source_identity=operation.source_movement_identity,
                        created_at=operation.created_at,
                    )
                )
                continue

            if isinstance(operation, ConsumptionPlan):
                layer_identity = self._resolve_reference(operation, references)
                facts.append(
                    ValuationConsumption(
                        identity=Identifier.new(),
                        valuation_key=operation.valuation_key,
                        layer_identity=layer_identity,
                        quantity=operation.quantity,
                        cost=operation.cost,
                        source_identity=operation.source_identity,
                        created_at=operation.created_at,
                    )
                )
                movements.append(
                    CostMovement(
                        identity=Identifier.new(),
                        valuation_key=operation.valuation_key,
                        quantity=-operation.quantity,
                        cost=-operation.cost,
                        source_identity=operation.source_identity,
                        created_at=operation.created_at,
                    )
                )
                continue

            raise TypeError("ValuationPlan contains an unsupported operation.")

        return tuple(facts), tuple(movements)

    @staticmethod
    def _resolve_reference(
        operation: ConsumptionPlan,
        references: dict[PlannedLayerReference, Identifier],
    ) -> Identifier:
        reference = operation.layer_reference
        if isinstance(reference, PersistedLayerReference):
            return reference.identity
        try:
            return references[reference]
        except KeyError as exc:
            raise ValueError("Planned layer reference was not resolved.") from exc
