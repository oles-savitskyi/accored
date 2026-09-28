from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    CostBalance,
    CostMovement,
    ValuationConsumption,
    ValuationFact,
    ValuationFactPersistence,
    ValuationKey,
    ValuationLayer,
    ValuationResultPersistence,
    ValuationReversal,
)


class StandardValuationFactPersistence(ValuationFactPersistence):
    """Append-only Standard valuation fact store used by the composition root."""

    def __init__(self) -> None:
        self._facts: list[ValuationFact] = []

    def append(self, facts: Sequence[ValuationFact]) -> None:
        self._facts.extend(facts)

    def find_by_source_document(self, document_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self._facts
            if (
                isinstance(fact, ValuationLayer)
                and fact.source_document_identity == document_identity
            )
            or (
                isinstance(fact, (ValuationConsumption, ValuationReversal))
                and fact.document_identity == document_identity
            )
        )

    def find_by_source_movement(self, movement_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self._facts
            if (
                isinstance(fact, ValuationLayer)
                and fact.source_movement_identity == movement_identity
            )
            or (
                isinstance(fact, (ValuationConsumption, ValuationReversal))
                and fact.source_identity == movement_identity
            )
        )

    def find_by_valuation_key(self, valuation_key: ValuationKey) -> tuple[ValuationFact, ...]:
        return tuple(fact for fact in self._facts if fact.valuation_key == valuation_key)

    def enumerate(self) -> tuple[ValuationFact, ...]:
        return tuple(self._facts)

    def find_available_layers(self, valuation_key: ValuationKey) -> tuple[ValuationLayer, ...]:
        facts = self._facts
        reversed_ids = {
            fact.reversed_identity for fact in facts if isinstance(fact, ValuationReversal)
        }
        layers = [
            fact
            for fact in facts
            if isinstance(fact, ValuationLayer)
            and fact.identity not in reversed_ids
            and fact.valuation_key == valuation_key
        ]
        consumptions = [
            fact
            for fact in facts
            if isinstance(fact, ValuationConsumption) and fact.identity not in reversed_ids
        ]
        consumed_quantity: dict[Identifier, Decimal] = defaultdict(lambda: Decimal(0))
        consumed_cost: dict[Identifier, Decimal] = defaultdict(lambda: Decimal(0))
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


class StandardValuationResultPersistence(ValuationResultPersistence):
    """Materialized Standard valuation result store."""

    def __init__(self) -> None:
        self._movements: list[CostMovement] = []
        self._balances: dict[ValuationKey, CostBalance] = {}

    def append_movements(self, movements: Sequence[CostMovement]) -> None:
        self._movements.extend(movements)

    def replace_balance(self, balance: CostBalance) -> None:
        self._balances[balance.valuation_key] = balance

    def find_movements(self, valuation_key: ValuationKey) -> tuple[CostMovement, ...]:
        return tuple(
            movement for movement in self._movements if movement.valuation_key == valuation_key
        )

    def find_balance(self, valuation_key: ValuationKey) -> CostBalance | None:
        return self._balances.get(valuation_key)

    def enumerate_balances(self) -> tuple[CostBalance, ...]:
        return tuple(self._balances.values())


__all__ = ["StandardValuationFactPersistence", "StandardValuationResultPersistence"]
