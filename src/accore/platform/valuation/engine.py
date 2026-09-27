from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.posting import MovementSet
from accore.platform.registers import Movement, MovementType

from .consumption import ConsumptionRequest, SyntheticConsumptionService, ValuationMethod
from .errors import ValuationValidationError
from .facts import ValuationLayer
from .input import ValuationInput
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
        layer_reader: ValuationLayerReader,
        method: ValuationMethod,
        *,
        quantity_resource_name: str = "quantity",
    ) -> None:
        if not quantity_resource_name:
            raise ValueError("quantity_resource_name must be non-empty.")
        self._layer_reader = layer_reader
        self._consumption = SyntheticConsumptionService(method)
        self._quantity_resource_name = quantity_resource_name

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
            valuation_key = self._valuation_key(movement)
            quantity = self._quantity(movement)
            occurred_at = self._occurred_at(movement)

            if movement.movement_type is MovementType.INCOME:
                reference = PlannedLayerReference(Identifier.new())
                layer = ValuationLayer(
                    identity=reference.value,
                    valuation_key=valuation_key,
                    quantity=quantity,
                    total_cost=Decimal(0),
                    source_document_identity=movement.source_document_identity,
                    source_movement_identity=movement.identity,
                    created_at=occurred_at,
                )
                available_layers[valuation_key] = (
                    *available_layers.get(valuation_key, ()),
                    layer,
                )
                planned_references[reference.value] = reference
                operations.append(
                    LayerEstablishmentPlan(
                        reference=reference,
                        valuation_key=valuation_key,
                        quantity=quantity,
                        source_document_identity=movement.source_document_identity,
                        source_movement_identity=movement.identity,
                        created_at=occurred_at,
                    )
                )
                continue

            if movement.movement_type is MovementType.EXPENSE:
                layers = available_layers.get(valuation_key)
                if layers is None:
                    layers = self._layer_reader.find_available_layers(valuation_key)
                    available_layers[valuation_key] = layers

                valuation_input = ValuationInput(
                    request=ConsumptionRequest(
                        identity=Identifier.new(),
                        valuation_key=valuation_key,
                        quantity=quantity,
                        document_identity=document_identity,
                        source_identity=movement.identity,
                        occurred_at=occurred_at,
                    ),
                    layers=layers,
                )
                result = self._consumption.consume(
                    valuation_input.layers,
                    valuation_input.request,
                )
                available_layers[valuation_key] = result.remaining_layers
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
                        document_identity=document_identity,
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

    def _valuation_key(self, movement: Movement) -> ValuationKey:
        dimensions: dict[str, str] = {}
        for name, value in movement.dimensions.values.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise ValuationValidationError(
                    f"Invalid valuation dimensions for movement {movement.identity}."
                )
            dimensions[name] = value
        try:
            return ValuationKey(dimensions)
        except (TypeError, ValueError) as exc:
            raise ValuationValidationError(
                f"Invalid valuation dimensions for movement {movement.identity}: {exc}"
            ) from exc

    def _quantity(self, movement: Movement) -> Decimal:
        quantity = movement.resources.get(self._quantity_resource_name)
        if not isinstance(quantity, Decimal) or quantity <= Decimal(0):
            raise ValuationValidationError(
                f"Movement {movement.identity} requires a positive Decimal "
                f"'{self._quantity_resource_name}' resource."
            )
        return quantity

    @staticmethod
    def _occurred_at(movement: Movement) -> datetime:
        if movement.accounting_time is None:
            raise ValuationValidationError(
                f"Movement {movement.identity} requires accounting_time for valuation."
            )
        return movement.accounting_time
