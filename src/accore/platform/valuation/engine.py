from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.posting import MovementSet
from accore.platform.registers import MovementType

from .consumption import ConsumptionRequest, SyntheticConsumptionService, ValuationMethod
from .errors import ValuationValidationError
from .facts import ValuationLayer
from .input_provider import ValuationInputProvider
from .key import ValuationKey
from .plan import (
    ConsumptionPlan,
    LayerEstablishmentPlan,
    PersistedLayerReference,
    PlannedLayerReference,
    ValuationPlan,
)


class ValuationLayerReader(Protocol):
    """Semantic read boundary for currently available valuation layers."""

    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]: ...


class ValuationEngine:
    """Prepare deterministic valuation operations without authoritative mutation."""

    def __init__(
        self,
        input_provider: ValuationInputProvider,
        layer_reader: ValuationLayerReader,
        method: ValuationMethod,
    ) -> None:
        self._input_provider = input_provider
        self._layer_reader = layer_reader
        self._consumption = SyntheticConsumptionService(method)

    def prepare(self, movement_set: MovementSet) -> ValuationPlan:
        if not movement_set.movements:
            raise ValuationValidationError("MovementSet must contain at least one movement.")

        document_identity = movement_set.movements[0].source_document_identity
        if any(
            movement.source_document_identity != document_identity
            for movement in movement_set.movements[1:]
        ):
            raise ValuationValidationError(
                "All movements in a valuation plan must belong to one posting document."
            )

        operations: list[LayerEstablishmentPlan | ConsumptionPlan] = []
        available_layers: dict[ValuationKey, tuple[ValuationLayer, ...]] = {}
        planned_references: dict[Identifier, PlannedLayerReference] = {}

        for movement in movement_set.movements:
            valuation_input = self._input_provider.provide(movement)

            if valuation_input.document_identity != document_identity:
                raise ValuationValidationError(
                    "Valuation input document identity must match the posting document."
                )

            if movement.movement_type is MovementType.INCOME:
                reference = PlannedLayerReference(Identifier.new())
                layer = ValuationLayer(
                    identity=reference.value,
                    valuation_key=valuation_input.valuation_key,
                    quantity=valuation_input.quantity,
                    total_cost=Decimal(0),
                    source_document_identity=valuation_input.document_identity,
                    source_movement_identity=valuation_input.source_identity,
                    created_at=valuation_input.occurred_at,
                )
                available_layers[valuation_input.valuation_key] = (
                    *available_layers.get(valuation_input.valuation_key, ()),
                    layer,
                )
                planned_references[reference.value] = reference
                operations.append(
                    LayerEstablishmentPlan(
                        reference=reference,
                        valuation_key=valuation_input.valuation_key,
                        quantity=valuation_input.quantity,
                        source_document_identity=valuation_input.document_identity,
                        source_movement_identity=valuation_input.source_identity,
                        created_at=valuation_input.occurred_at,
                    )
                )
                continue

            if movement.movement_type is MovementType.EXPENSE:
                layers = available_layers.get(valuation_input.valuation_key)
                if layers is None:
                    layers = self._layer_reader.find_available_layers(valuation_input.valuation_key)
                    available_layers[valuation_input.valuation_key] = layers

                request = ConsumptionRequest(
                    identity=Identifier.new(),
                    valuation_key=valuation_input.valuation_key,
                    quantity=valuation_input.quantity,
                    document_identity=valuation_input.document_identity,
                    source_identity=valuation_input.source_identity,
                    occurred_at=valuation_input.occurred_at,
                )
                result = self._consumption.consume(layers, request)
                available_layers[valuation_input.valuation_key] = result.remaining_layers
                operations.extend(
                    ConsumptionPlan(
                        valuation_key=consumption.valuation_key,
                        layer_reference=(
                            planned_references[consumption.layer_identity]
                            if consumption.layer_identity in planned_references
                            else PersistedLayerReference(consumption.layer_identity)
                        ),
                        quantity=consumption.quantity,
                        cost=consumption.cost,
                        document_identity=consumption.document_identity,
                        source_identity=consumption.source_identity,
                        created_at=consumption.created_at,
                    )
                    for consumption in result.consumptions
                )
                continue

            raise ValuationValidationError(
                f"Unsupported movement type for valuation: {movement.movement_type}."
            )

        return ValuationPlan(
            document_identity=document_identity,
            operations=tuple(operations),
        )
