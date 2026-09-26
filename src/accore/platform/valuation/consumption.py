from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier

from .errors import ValuationInsufficientQuantityError, ValuationValidationError
from .facts import ValuationConsumption, ValuationLayer
from .key import ValuationKey


@dataclass(frozen=True, slots=True)
class ConsumptionRequest:
    """Immutable request for synthetic valuation consumption."""

    identity: Identifier
    valuation_key: ValuationKey
    quantity: Decimal
    source_identity: Identifier
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.quantity, Decimal):
            raise TypeError("ConsumptionRequest quantity must be a Decimal.")
        if self.quantity <= Decimal(0):
            raise ValuationValidationError("ConsumptionRequest quantity must be greater than zero.")


@dataclass(frozen=True, slots=True)
class ConsumptionResult:
    """Immutable result of a synthetic valuation consumption operation."""

    consumptions: tuple[ValuationConsumption, ...]
    total_cost: Decimal
    remaining_layers: tuple[ValuationLayer, ...]


class ValuationMethod(Protocol):
    """Strategy for calculating valuation consumption from available layers."""

    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult: ...


class FIFOValuationMethod:
    """Consume valuation layers in deterministic first-in-first-out order."""

    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult:
        self._validate_layers(layers, request)

        ordered_layers = tuple(
            sorted(
                layers,
                key=lambda layer: (layer.created_at, str(layer.identity)),
            )
        )

        available = sum(
            (layer.quantity for layer in ordered_layers),
            Decimal(0),
        )
        if available < request.quantity:
            raise ValuationInsufficientQuantityError(
                "Insufficient valuation layer quantity for synthetic consumption."
            )

        remaining_to_consume = request.quantity
        consumptions: list[ValuationConsumption] = []
        remaining_layers: list[ValuationLayer] = []

        for layer in ordered_layers:
            if remaining_to_consume <= Decimal(0):
                remaining_layers.append(layer)
                continue

            consumed_quantity = min(layer.quantity, remaining_to_consume)
            consumed_cost = self._proportional_cost(layer, consumed_quantity)

            consumptions.append(
                ValuationConsumption(
                    identity=Identifier.new(),
                    valuation_key=layer.valuation_key,
                    layer_identity=layer.identity,
                    quantity=consumed_quantity,
                    cost=consumed_cost,
                    source_identity=request.source_identity,
                    created_at=request.occurred_at,
                )
            )

            remaining_quantity = layer.quantity - consumed_quantity
            if remaining_quantity > Decimal(0):
                remaining_layers.append(
                    ValuationLayer(
                        identity=layer.identity,
                        valuation_key=layer.valuation_key,
                        quantity=remaining_quantity,
                        total_cost=layer.total_cost - consumed_cost,
                        source_document_identity=layer.source_document_identity,
                        source_movement_identity=layer.source_movement_identity,
                        created_at=layer.created_at,
                    )
                )

            remaining_to_consume -= consumed_quantity

        total_cost = sum(
            (consumption.cost for consumption in consumptions),
            Decimal(0),
        )
        return ConsumptionResult(
            consumptions=tuple(consumptions),
            total_cost=total_cost,
            remaining_layers=tuple(remaining_layers),
        )

    @staticmethod
    def _proportional_cost(layer: ValuationLayer, quantity: Decimal) -> Decimal:
        if quantity == layer.quantity:
            return layer.total_cost
        return layer.total_cost * quantity / layer.quantity

    @staticmethod
    def _validate_layers(
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> None:
        for layer in layers:
            if not isinstance(layer, ValuationLayer):
                raise TypeError("FIFO layers must contain ValuationLayer instances.")
            if layer.valuation_key != request.valuation_key:
                raise ValuationValidationError(
                    "FIFO layers must match the ConsumptionRequest valuation key."
                )


class SyntheticConsumptionService:
    """Explicit valuation-domain service delegating synthetic consumption to a method."""

    def __init__(self, method: ValuationMethod) -> None:
        self._method = method

    def consume(
        self,
        layers: Sequence[ValuationLayer],
        request: ConsumptionRequest,
    ) -> ConsumptionResult:
        return self._method.consume(layers, request)
