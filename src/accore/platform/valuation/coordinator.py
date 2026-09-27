from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import (
    PersistenceError,
    PersistenceIndeterminateError,
)

from .errors import ValuationPersistenceError, ValuationValidationError
from .facts import ValuationConsumption, ValuationFact, ValuationLayer, ValuationReversal
from .key import ValuationKey
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


class ValuationRemovalOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ValuationRemovalResult:
    outcome: ValuationRemovalOutcome
    error: Exception | None = None


class ValuationLifecycleCoordinator(Protocol):
    def establish(self, plan: ValuationPlan) -> ValuationEstablishmentResult: ...

    def remove(self, document_identity: Identifier) -> ValuationRemovalResult: ...


ValuationCoordinator = ValuationLifecycleCoordinator


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

            balances: dict[ValuationKey, CostBalance] = {}
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

    def remove(self, document_identity: Identifier) -> ValuationRemovalResult:
        all_facts = tuple(self._fact_persistence.enumerate())

        document_facts = tuple(
            fact
            for fact in all_facts
            if (
                isinstance(fact, ValuationLayer)
                and fact.source_document_identity == document_identity
            )
            or (
                isinstance(fact, ValuationConsumption)
                and fact.document_identity == document_identity
            )
            or (isinstance(fact, ValuationReversal) and fact.document_identity == document_identity)
        )

        if not document_facts:
            return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)

        all_reversed_ids = {
            reversal.reversed_identity
            for reversal in all_facts
            if isinstance(reversal, ValuationReversal)
        }

        document_reversals = tuple(
            fact for fact in document_facts if isinstance(fact, ValuationReversal)
        )
        document_reversed_ids = {reversal.reversed_identity for reversal in document_reversals}

        originals = tuple(
            fact
            for fact in document_facts
            if not isinstance(fact, ValuationReversal)
            and fact.identity not in document_reversed_ids
        )

        if not originals:
            return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)

        active_consumptions = tuple(
            fact
            for fact in all_facts
            if isinstance(fact, ValuationConsumption) and fact.identity not in all_reversed_ids
        )

        try:
            self._validate_removal(
                document_identity=document_identity,
                originals=originals,
                active_consumptions=active_consumptions,
            )

            reversal_facts, movements = self._build_reversals(
                document_identity=document_identity,
                originals=originals,
            )

            self._fact_persistence.append(reversal_facts)
            self._result_persistence.append_movements(movements)
            self._rebuild_derived_state(movements)

        except ValuationValidationError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.FAILURE,
                exc,
            )
        except PersistenceIndeterminateError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.INDETERMINATE,
                exc,
            )
        except PersistenceError as exc:
            return ValuationRemovalResult(
                ValuationRemovalOutcome.FAILURE,
                exc,
            )

        return ValuationRemovalResult(ValuationRemovalOutcome.SUCCESS)

    def _validate_removal(
        self,
        *,
        document_identity: Identifier,
        originals: tuple[ValuationFact, ...],
        active_consumptions: tuple[ValuationConsumption, ...],
    ) -> None:
        removed_consumption_ids = {
            fact.identity for fact in originals if isinstance(fact, ValuationConsumption)
        }

        for fact in originals:
            if isinstance(fact, ValuationLayer) and any(
                consumption.layer_identity == fact.identity
                and consumption.identity not in removed_consumption_ids
                and consumption.document_identity != document_identity
                for consumption in active_consumptions
            ):
                raise ValuationValidationError(
                    "Valuation layer cannot be reversed while another document consumes it."
                )

    @staticmethod
    def _build_reversals(
        *,
        document_identity: Identifier,
        originals: tuple[ValuationFact, ...],
    ) -> tuple[tuple[ValuationFact, ...], tuple[CostMovement, ...]]:
        reversal_facts: list[ValuationFact] = []
        movements: list[CostMovement] = []

        for fact in originals:
            if isinstance(fact, ValuationLayer):
                source_identity = fact.source_movement_identity
                quantity = -fact.quantity
                cost = -fact.total_cost
            elif isinstance(fact, ValuationConsumption):
                source_identity = fact.source_identity
                quantity = fact.quantity
                cost = fact.cost
            else:
                continue

            reversal_facts.append(
                ValuationReversal(
                    identity=Identifier.new(),
                    reversed_identity=fact.identity,
                    valuation_key=fact.valuation_key,
                    document_identity=document_identity,
                    source_identity=source_identity,
                    created_at=fact.created_at,
                )
            )
            movements.append(
                CostMovement(
                    identity=Identifier.new(),
                    valuation_key=fact.valuation_key,
                    quantity=quantity,
                    cost=cost,
                    source_identity=source_identity,
                    created_at=fact.created_at,
                )
            )

        return tuple(reversal_facts), tuple(movements)

    def _rebuild_derived_state(
        self,
        movements: tuple[CostMovement, ...],
    ) -> None:
        balances: dict[ValuationKey, CostBalance] = {}

        for movement in movements:
            balances[movement.valuation_key] = self._totals_engine.apply(movement)

        for balance in balances.values():
            self._result_persistence.replace_balance(balance)

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
                        document_identity=operation.document_identity,
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
