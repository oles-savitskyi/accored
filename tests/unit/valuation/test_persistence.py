from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation.facts import (
    ValuationAdjustment,
    ValuationAllocation,
    ValuationConsumption,
    ValuationFact,
    ValuationLayer,
    ValuationReversal,
)
from accore.platform.valuation.key import ValuationKey
from accore.platform.valuation.results import CostBalance, CostMovement


class InMemoryValuationFactPersistence:
    """Test implementation proving the authoritative fact protocol."""

    def __init__(self) -> None:
        self._facts: list[ValuationFact] = []

    def append(
        self,
        facts: Sequence[ValuationFact],
    ) -> None:
        self._facts.extend(facts)

    def find_by_source_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self._facts
            if (
                getattr(fact, "source_document_identity", None) == document_identity
                or getattr(fact, "document_identity", None) == document_identity
            )
        )

    def find_by_source_movement(
        self,
        movement_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self._facts
            if getattr(fact, "source_movement_identity", None) == movement_identity
        )

    def find_by_valuation_key(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationFact, ...]:
        return tuple(fact for fact in self._facts if fact.valuation_key == valuation_key)

    def enumerate(
        self,
    ) -> tuple[ValuationFact, ...]:
        return tuple(self._facts)


class InMemoryValuationResultPersistence:
    """Test implementation proving the derived result protocol."""

    def __init__(self) -> None:
        self._movements: list[CostMovement] = []
        self._balances: dict[ValuationKey, CostBalance] = {}

    def append_movements(
        self,
        movements: Sequence[CostMovement],
    ) -> None:
        self._movements.extend(movements)

    def replace_balance(
        self,
        balance: CostBalance,
    ) -> None:
        self._balances[balance.valuation_key] = balance

    def find_movements(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[CostMovement, ...]:
        return tuple(
            movement for movement in self._movements if movement.valuation_key == valuation_key
        )

    def find_balance(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance | None:
        return self._balances.get(valuation_key)

    def enumerate_balances(
        self,
    ) -> tuple[CostBalance, ...]:
        return tuple(self._balances.values())


def _identifier() -> Identifier:
    return Identifier.new()


def _valuation_key() -> ValuationKey:
    return ValuationKey({"product": "PRODUCT-001", "warehouse": "WH-001"})


def _created_at() -> datetime:
    return datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


def _layer() -> ValuationLayer:
    return ValuationLayer(
        identity=_identifier(),
        valuation_key=_valuation_key(),
        quantity=Decimal(100),
        total_cost=Decimal(0),
        source_document_identity=_identifier(),
        source_movement_identity=_identifier(),
        created_at=_created_at(),
    )


def _consumption() -> ValuationConsumption:
    return ValuationConsumption(
        identity=_identifier(),
        valuation_key=_valuation_key(),
        layer_identity=_identifier(),
        quantity=Decimal(10),
        cost=Decimal(0),
        document_identity=_identifier(),
        source_identity=_identifier(),
        created_at=_created_at(),
    )


def _adjustment() -> ValuationAdjustment:
    return ValuationAdjustment(
        identity=_identifier(),
        valuation_key=_valuation_key(),
        amount=Decimal(100),
        source_identity=_identifier(),
        reason="Additional acquisition cost",
        created_at=_created_at(),
    )


def _allocation() -> ValuationAllocation:
    return ValuationAllocation(
        identity=_identifier(),
        adjustment_identity=_identifier(),
        layer_identity=_identifier(),
        valuation_key=_valuation_key(),
        amount=Decimal(100),
        created_at=_created_at(),
    )


def _reversal() -> ValuationReversal:
    return ValuationReversal(
        identity=_identifier(),
        reversed_identity=_identifier(),
        valuation_key=_valuation_key(),
        document_identity=_identifier(),
        source_identity=_identifier(),
        created_at=_created_at(),
    )


def _movement() -> CostMovement:
    return CostMovement(
        identity=_identifier(),
        valuation_key=_valuation_key(),
        quantity=Decimal(10),
        cost=Decimal(0),
        source_identity=_identifier(),
        created_at=_created_at(),
    )


def _balance() -> CostBalance:
    return CostBalance(
        valuation_key=_valuation_key(),
        quantity=Decimal(90),
        cost=Decimal(0),
        calculated_at=_created_at(),
    )


def test_fact_persistence_appends_immutable_facts() -> None:
    persistence = InMemoryValuationFactPersistence()

    facts: tuple[ValuationFact, ...] = (
        _layer(),
        _consumption(),
        _adjustment(),
        _allocation(),
        _reversal(),
    )

    persistence.append(facts)

    assert persistence.enumerate() == facts


def test_fact_persistence_finds_by_source_document() -> None:
    persistence = InMemoryValuationFactPersistence()

    layer = _layer()
    consumption = _consumption()
    other_layer = _layer()

    persistence.append((layer, consumption, other_layer))

    assert persistence.find_by_source_document(layer.source_document_identity) == (layer,)
    assert persistence.find_by_source_document(consumption.document_identity) == (consumption,)
    assert persistence.find_by_source_document(other_layer.source_document_identity) == (
        other_layer,
    )

    assert persistence.find_by_source_document(_identifier()) == ()


def test_fact_persistence_finds_by_source_movement() -> None:
    persistence = InMemoryValuationFactPersistence()

    layer = _layer()
    persistence.append((layer,))

    assert persistence.find_by_source_movement(layer.source_movement_identity) == (layer,)
    assert persistence.find_by_source_movement(_identifier()) == ()


def test_fact_persistence_finds_by_valuation_key() -> None:
    persistence = InMemoryValuationFactPersistence()

    layer = _layer()
    adjustment = _adjustment()
    persistence.append((layer, adjustment))

    assert persistence.find_by_valuation_key(_valuation_key()) == (
        layer,
        adjustment,
    )


def test_fact_persistence_preserves_append_only_order() -> None:
    persistence = InMemoryValuationFactPersistence()

    first = _layer()
    second = _consumption()

    persistence.append((first,))
    persistence.append((second,))

    assert persistence.enumerate() == (first, second)


def test_result_persistence_appends_movements() -> None:
    persistence = InMemoryValuationResultPersistence()

    movement = _movement()
    persistence.append_movements((movement,))

    assert persistence.find_movements(_valuation_key()) == (movement,)


def test_result_persistence_replaces_derived_balance() -> None:
    persistence = InMemoryValuationResultPersistence()

    initial = _balance()
    replacement = CostBalance(
        valuation_key=_valuation_key(),
        quantity=Decimal(80),
        cost=Decimal(10),
        calculated_at=datetime(2026, 9, 25, 13, 0, tzinfo=UTC),
    )

    persistence.replace_balance(initial)
    persistence.replace_balance(replacement)

    assert persistence.find_balance(_valuation_key()) == replacement
    assert persistence.enumerate_balances() == (replacement,)


def test_result_persistence_returns_empty_results_for_unknown_key() -> None:
    persistence = InMemoryValuationResultPersistence()
    unknown_key = ValuationKey({"product": "UNKNOWN", "warehouse": "UNKNOWN"})

    assert persistence.find_movements(unknown_key) == ()
    assert persistence.find_balance(unknown_key) is None


def test_result_persistence_enumerates_balances() -> None:
    persistence = InMemoryValuationResultPersistence()

    first = _balance()
    second = CostBalance(
        valuation_key=ValuationKey({"product": "PRODUCT-002", "warehouse": "WH-001"}),
        quantity=Decimal(50),
        cost=Decimal(25),
        calculated_at=_created_at(),
    )

    persistence.replace_balance(first)
    persistence.replace_balance(second)

    assert persistence.enumerate_balances() == (first, second)
