from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from accore.platform.foundation import Identifier

from .errors import ValuationValidationError
from .facts import ValuationConsumption, ValuationFact, ValuationLayer, ValuationReversal
from .key import ValuationKey
from .persistence import ValuationFactPersistence


class ValuationPreparationState(Protocol):
    """Read-only valuation-layer state used during preparation."""

    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]: ...


@dataclass(frozen=True, slots=True)
class ProjectedValuationPreparationState:
    """Immutable valuation state projected as if one document had been removed."""

    layers: tuple[ValuationLayer, ...]

    def find_available_layers(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationLayer, ...]:
        return tuple(layer for layer in self.layers if layer.valuation_key == valuation_key)


class ValuationPreparationStateFactory(Protocol):
    """Construct authoritative or replacement-specific read-only preparation state."""

    def authoritative(self) -> ValuationPreparationState: ...

    def for_replacement(
        self,
        document_identity: Identifier,
    ) -> ValuationPreparationState: ...


class DefaultValuationPreparationStateFactory:
    """Build preparation state directly from immutable authoritative valuation facts."""

    def __init__(self, fact_persistence: ValuationFactPersistence) -> None:
        self._facts = fact_persistence

    def authoritative(self) -> ValuationPreparationState:
        return ProjectedValuationPreparationState(
            layers=self._current_layers(tuple(self._facts.enumerate()))
        )

    def for_replacement(
        self,
        document_identity: Identifier,
    ) -> ValuationPreparationState:
        facts = tuple(self._facts.enumerate())
        active_facts = self._active_facts(facts)
        targets = self._select_removal_targets(document_identity, active_facts)
        self._validate_removal(document_identity, targets, active_facts)

        removed_ids = {fact.identity for fact in targets}
        projected_facts = tuple(fact for fact in active_facts if fact.identity not in removed_ids)
        return ProjectedValuationPreparationState(layers=self._current_layers(projected_facts))

    @staticmethod
    def _active_facts(facts: tuple[ValuationFact, ...]) -> tuple[ValuationFact, ...]:
        reversed_ids = {
            fact.reversed_identity for fact in facts if isinstance(fact, ValuationReversal)
        }
        return tuple(
            fact
            for fact in facts
            if not isinstance(fact, ValuationReversal) and fact.identity not in reversed_ids
        )

    @staticmethod
    def _select_removal_targets(
        document_identity: Identifier,
        active_facts: tuple[ValuationFact, ...],
    ) -> tuple[ValuationFact, ...]:
        candidates = tuple(
            fact
            for fact in active_facts
            if (
                isinstance(fact, ValuationLayer)
                and fact.source_document_identity == document_identity
            )
            or (
                isinstance(fact, ValuationConsumption)
                and fact.document_identity == document_identity
            )
        )
        return tuple(sorted(candidates, key=lambda fact: str(fact.identity)))

    @staticmethod
    def _validate_removal(
        document_identity: Identifier,
        targets: tuple[ValuationFact, ...],
        active_facts: tuple[ValuationFact, ...],
    ) -> None:
        removed_consumption_ids = {
            fact.identity for fact in targets if isinstance(fact, ValuationConsumption)
        }
        active_consumptions = tuple(
            fact for fact in active_facts if isinstance(fact, ValuationConsumption)
        )
        for fact in targets:
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
    def _current_layers(facts: tuple[ValuationFact, ...]) -> tuple[ValuationLayer, ...]:
        layers = tuple(fact for fact in facts if isinstance(fact, ValuationLayer))
        consumptions = tuple(fact for fact in facts if isinstance(fact, ValuationConsumption))
        consumed_quantity: dict[Identifier, Decimal] = defaultdict(lambda: Decimal(0))
        consumed_cost: dict[Identifier, Decimal] = defaultdict(lambda: Decimal(0))
        for consumption in consumptions:
            consumed_quantity[consumption.layer_identity] += consumption.quantity
            consumed_cost[consumption.layer_identity] += consumption.cost

        current: list[ValuationLayer] = []
        for layer in layers:
            quantity = layer.quantity - consumed_quantity[layer.identity]
            if quantity <= Decimal(0):
                continue
            current.append(
                ValuationLayer(
                    identity=layer.identity,
                    valuation_key=layer.valuation_key,
                    quantity=quantity,
                    total_cost=layer.total_cost - consumed_cost[layer.identity],
                    source_document_identity=layer.source_document_identity,
                    source_movement_identity=layer.source_movement_identity,
                    created_at=layer.created_at,
                    operation_identity=layer.operation_identity,
                )
            )
        return tuple(sorted(current, key=lambda layer: (layer.created_at, str(layer.identity))))


__all__ = [
    "DefaultValuationPreparationStateFactory",
    "ProjectedValuationPreparationState",
    "ValuationPreparationState",
    "ValuationPreparationStateFactory",
]
