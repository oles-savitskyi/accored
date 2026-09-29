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
    ValuationOperationIdentity,
    ValuationOperationPersistence,
    ValuationOperationRecord,
    ValuationResultPersistence,
    ValuationReversal,
)


class StandardValuationOperationPersistence(ValuationOperationPersistence):
    """Append-only Standard valuation operation store used by the composition root."""

    def __init__(self) -> None:
        self._operations: dict[ValuationOperationIdentity, ValuationOperationRecord] = {}

    def append(self, operation: ValuationOperationRecord) -> None:
        existing = self._operations.get(operation.identity)
        if existing is None:
            self._operations[operation.identity] = operation
            return
        if existing != operation:
            from accore.platform.valuation.errors import ValuationConflictError

            raise ValuationConflictError(
                "Valuation operation identity already exists with different semantics."
            )

    def find(
        self,
        identity: ValuationOperationIdentity,
    ) -> ValuationOperationRecord | None:
        return self._operations.get(identity)

    def find_by_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationOperationRecord, ...]:
        return tuple(
            operation
            for operation in self._operations.values()
            if operation.document_identity == document_identity
        )

    def enumerate(self) -> tuple[ValuationOperationRecord, ...]:
        return tuple(self._operations.values())


class StandardValuationFactPersistence(ValuationFactPersistence):
    """Append-only Standard valuation fact store used by the composition root."""

    def __init__(self) -> None:
        self._facts: dict[Identifier, ValuationFact] = {}
        self._order: list[Identifier] = []

    def append(self, facts: Sequence[ValuationFact]) -> None:
        pending: dict[Identifier, ValuationFact] = {}
        for fact in facts:
            existing = self._facts.get(fact.identity)
            if existing is None:
                existing = pending.get(fact.identity)
            if existing is not None and existing != fact:
                from accore.platform.valuation.errors import ValuationConflictError

                raise ValuationConflictError(
                    "Valuation fact identity already exists with different semantics."
                )
            pending[fact.identity] = fact

        for identity, fact in pending.items():
            if identity not in self._facts:
                self._facts[identity] = fact
                self._order.append(identity)

    def find(self, identity: Identifier) -> ValuationFact | None:
        return self._facts.get(identity)

    def find_by_source_document(self, document_identity: Identifier) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self._facts.values()
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
            for fact in self._facts.values()
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
        return tuple(fact for fact in self._facts.values() if fact.valuation_key == valuation_key)

    def enumerate(self) -> tuple[ValuationFact, ...]:
        return tuple(self._facts[identity] for identity in self._order)

    def find_available_layers(self, valuation_key: ValuationKey) -> tuple[ValuationLayer, ...]:
        facts = self.enumerate()
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
                operation_identity=layer.operation_identity,
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

    def find_movement(self, identity: Identifier) -> CostMovement | None:
        return next(
            (movement for movement in self._movements if movement.identity == identity),
            None,
        )

    def enumerate_movements(self) -> tuple[CostMovement, ...]:
        return tuple(self._movements)

    def reconcile_movements(self, movements: Sequence[CostMovement]) -> None:
        from accore.platform.valuation.errors import ValuationConflictError

        existing_by_identity = {movement.identity: movement for movement in self._movements}
        expected_by_identity: dict[Identifier, CostMovement] = {}
        for movement in movements:
            duplicate = expected_by_identity.get(movement.identity)
            if duplicate is not None and duplicate != movement:
                raise ValuationConflictError(
                    "Valuation movement identity has conflicting semantics."
                )
            persisted = existing_by_identity.get(movement.identity)
            if persisted is not None and persisted != movement:
                raise ValuationConflictError(
                    "Persisted valuation movement identity has conflicting semantics."
                )
            expected_by_identity[movement.identity] = movement
        self._movements = list(expected_by_identity.values())

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


__all__ = [
    "StandardValuationFactPersistence",
    "StandardValuationOperationPersistence",
    "StandardValuationResultPersistence",
]
