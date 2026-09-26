from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .facts import ValuationConsumption, ValuationLayer
from .persistence import ValuationFactPersistence
from .plan import (
    ConsumptionPlan,
    LayerEstablishmentPlan,
    LayerReference,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationPlan,
)

identity: LayerReference


class ValuationPlanValidator(Protocol):
    """Semantic validation boundary for complete valuation plans."""

    def validate(self, plan: ValuationPlan) -> None:
        """Validate the complete plan before authoritative persistence."""
        ...


class DefaultValuationPlanValidator:
    """Validate plan structure, references, ordering, and available quantity."""

    def __init__(self, fact_persistence: ValuationFactPersistence) -> None:
        self._facts = fact_persistence

    def validate(self, plan: ValuationPlan) -> None:
        planned: dict[PlannedLayerReference, LayerEstablishmentPlan] = {}
        available: dict[
            Identifier | PlannedLayerReference | PersistedLayerReference,
            Decimal,
        ] = defaultdict(lambda: Decimal(0))
        costs: dict[
            Identifier | PlannedLayerReference | PersistedLayerReference,
            Decimal,
        ] = defaultdict(lambda: Decimal(0))

        persisted_layers = self._current_layers()
        for layer in persisted_layers:
            available[layer.identity] = layer.quantity
            costs[layer.identity] = layer.total_cost

        for operation in plan.operations:
            if isinstance(operation, LayerEstablishmentPlan):
                if operation.reference in planned:
                    raise ValuationValidationError("Planned layer references must be unique.")
                planned[operation.reference] = operation
                available[operation.reference] = operation.quantity
                costs[operation.reference] = Decimal(0)
                continue

            if not isinstance(operation, ConsumptionPlan):
                raise TypeError("ValuationPlan contains an unsupported operation.")
            reference = operation.layer_reference
            state_key: PlannedLayerReference | PersistedLayerReference

            if isinstance(reference, PlannedLayerReference):
                establishment = planned.get(reference)
                if establishment is None:
                    raise ValuationValidationError(
                        "Planned layer reference must be established earlier in the plan."
                    )
                if establishment.valuation_key != operation.valuation_key:
                    raise ValuationValidationError(
                        "Consumption and referenced layer must use the same valuation key."
                    )
                state_key = reference

            elif isinstance(reference, PersistedLayerReference):
                persisted_layer = persisted_layers_by_identity(persisted_layers).get(
                    reference.identity
                )
                if persisted_layer is None:
                    raise ValuationValidationError("Persisted layer reference cannot be resolved.")
                if persisted_layer.valuation_key != operation.valuation_key:
                    raise ValuationValidationError(
                        "Consumption and referenced layer must use the same valuation key."
                    )
                state_key = reference

            else:
                raise TypeError("ConsumptionPlan contains an unsupported layer reference.")

            if operation.quantity > available[state_key]:
                raise ValuationValidationError(
                    "Consumption exceeds available valuation layer quantity."
                )
            if operation.cost > costs[state_key]:
                raise ValuationValidationError(
                    "Consumption cost exceeds available valuation layer cost."
                )

            available[state_key] -= operation.quantity
            costs[state_key] -= operation.cost

    def _current_layers(self) -> tuple[ValuationLayer, ...]:
        facts = self._facts.enumerate()
        layers = [fact for fact in facts if isinstance(fact, ValuationLayer)]
        consumptions = [fact for fact in facts if isinstance(fact, ValuationConsumption)]
        consumed_quantity: dict[object, Decimal] = defaultdict(lambda: Decimal(0))
        consumed_cost: dict[object, Decimal] = defaultdict(lambda: Decimal(0))
        for consumption in consumptions:
            consumed_quantity[consumption.layer_identity] += consumption.quantity
            consumed_cost[consumption.layer_identity] += consumption.cost
        return tuple(
            ValuationLayer(
                identity=layer.identity,
                valuation_key=layer.valuation_key,
                quantity=layer.quantity - consumed_quantity[layer.identity],
                total_cost=layer.total_cost - consumed_cost[layer.identity],
                source_document_identity=layer.source_document_identity,
                source_movement_identity=layer.source_movement_identity,
                created_at=layer.created_at,
            )
            for layer in layers
            if layer.quantity > consumed_quantity[layer.identity]
        )


def persisted_layers_by_identity(
    layers: tuple[ValuationLayer, ...],
) -> dict[object, ValuationLayer]:
    return {layer.identity: layer for layer in layers}
