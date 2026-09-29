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
        self._facts: dict[Identifier, ValuationFact] = {}
        self._order: list[Identifier] = []

    def append(
        self,
        facts: Sequence[ValuationFact],
    ) -> None:
        pending: dict[Identifier, ValuationFact] = {}
        for fact in facts:
            existing = self._facts.get(fact.identity) or pending.get(fact.identity)
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

    def find_by_source_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        return tuple(
            fact
            for fact in self._facts.values()
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
            for fact in self._facts.values()
            if getattr(fact, "source_movement_identity", None) == movement_identity
        )

    def find_by_valuation_key(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationFact, ...]:
        return tuple(fact for fact in self._facts.values() if fact.valuation_key == valuation_key)

    def enumerate(
        self,
    ) -> tuple[ValuationFact, ...]:
        return tuple(self._facts[identity] for identity in self._order)


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


def _operation_record() -> tuple[object, object]:
    from accore.platform.valuation import (
        ValuationOperationIdentity,
        ValuationOperationRecord,
        ValuationOperationType,
    )

    identity = ValuationOperationIdentity("operation-001")
    record = ValuationOperationRecord(
        identity=identity,
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=_identifier(),
        fingerprint="fingerprint-001",
    )
    return identity, record


def test_operation_persistence_appends_and_finds_record() -> None:
    from standard.valuation import StandardValuationOperationPersistence

    persistence = StandardValuationOperationPersistence()
    identity, operation = _operation_record()

    persistence.append(operation)

    assert persistence.find(identity) == operation
    assert persistence.enumerate() == (operation,)


def test_operation_persistence_finds_by_document() -> None:
    from accore.platform.valuation import (
        ValuationOperationIdentity,
        ValuationOperationRecord,
        ValuationOperationType,
    )
    from standard.valuation import StandardValuationOperationPersistence

    persistence = StandardValuationOperationPersistence()
    document_identity = _identifier()
    operation = ValuationOperationRecord(
        identity=ValuationOperationIdentity("operation-001"),
        operation_type=ValuationOperationType.REMOVE,
        document_identity=document_identity,
        fingerprint="fingerprint-001",
    )
    other = ValuationOperationRecord(
        identity=ValuationOperationIdentity("operation-002"),
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=_identifier(),
        fingerprint="fingerprint-002",
    )

    persistence.append(operation)
    persistence.append(other)

    assert persistence.find_by_document(document_identity) == (operation,)


def test_operation_persistence_repeated_identical_append_is_idempotent() -> None:
    from standard.valuation import StandardValuationOperationPersistence

    persistence = StandardValuationOperationPersistence()
    _, operation = _operation_record()

    persistence.append(operation)
    persistence.append(operation)

    assert persistence.enumerate() == (operation,)


def test_operation_persistence_rejects_conflicting_identity() -> None:
    import pytest

    from accore.platform.valuation import (
        ValuationConflictError,
        ValuationOperationIdentity,
        ValuationOperationRecord,
        ValuationOperationType,
    )
    from standard.valuation import StandardValuationOperationPersistence

    persistence = StandardValuationOperationPersistence()
    identity = ValuationOperationIdentity("operation-001")
    first = ValuationOperationRecord(
        identity=identity,
        operation_type=ValuationOperationType.ESTABLISH,
        document_identity=_identifier(),
        fingerprint="fingerprint-001",
    )
    second = ValuationOperationRecord(
        identity=identity,
        operation_type=ValuationOperationType.REMOVE,
        document_identity=first.document_identity,
        fingerprint="fingerprint-002",
        target_fact_identities=(_identifier(),),
    )

    persistence.append(first)

    with pytest.raises(ValuationConflictError):
        persistence.append(second)

    assert persistence.find(identity) == first


def test_standard_fact_persistence_repeated_identical_append_is_idempotent() -> None:
    from standard.valuation import StandardValuationFactPersistence

    persistence = StandardValuationFactPersistence()
    fact = _layer()

    persistence.append((fact,))
    persistence.append((fact,))

    assert persistence.enumerate() == (fact,)
    assert persistence.find(fact.identity) == fact


def test_standard_fact_persistence_reconstructed_equal_fact_is_idempotent() -> None:
    from standard.valuation import StandardValuationFactPersistence

    persistence = StandardValuationFactPersistence()
    fact = _layer()
    reconstructed = ValuationLayer(
        identity=fact.identity,
        valuation_key=fact.valuation_key,
        quantity=fact.quantity,
        total_cost=fact.total_cost,
        source_document_identity=fact.source_document_identity,
        source_movement_identity=fact.source_movement_identity,
        created_at=fact.created_at,
        operation_identity=fact.operation_identity,
    )

    persistence.append((fact,))
    persistence.append((reconstructed,))

    assert persistence.enumerate() == (fact,)


def test_standard_fact_persistence_rejects_conflicting_identity_without_mutation() -> None:
    import pytest

    from accore.platform.valuation import ValuationConflictError
    from standard.valuation import StandardValuationFactPersistence

    persistence = StandardValuationFactPersistence()
    original = _layer()
    conflicting = ValuationLayer(
        identity=original.identity,
        valuation_key=original.valuation_key,
        quantity=Decimal(99),
        total_cost=original.total_cost,
        source_document_identity=original.source_document_identity,
        source_movement_identity=original.source_movement_identity,
        created_at=original.created_at,
        operation_identity=original.operation_identity,
    )

    persistence.append((original,))

    with pytest.raises(ValuationConflictError):
        persistence.append((conflicting,))

    assert persistence.enumerate() == (original,)


def test_standard_fact_persistence_accepts_identical_duplicate_in_one_batch() -> None:
    from standard.valuation import StandardValuationFactPersistence

    persistence = StandardValuationFactPersistence()
    fact = _layer()

    persistence.append((fact, fact))

    assert persistence.enumerate() == (fact,)


def test_standard_fact_persistence_rejects_conflicting_duplicate_in_one_batch_atomically() -> None:
    import pytest

    from accore.platform.valuation import ValuationConflictError
    from standard.valuation import StandardValuationFactPersistence

    persistence = StandardValuationFactPersistence()
    first = _layer()
    second = _layer()
    conflicting = ValuationLayer(
        identity=second.identity,
        valuation_key=second.valuation_key,
        quantity=Decimal(99),
        total_cost=second.total_cost,
        source_document_identity=second.source_document_identity,
        source_movement_identity=second.source_movement_identity,
        created_at=second.created_at,
        operation_identity=second.operation_identity,
    )

    with pytest.raises(ValuationConflictError):
        persistence.append((first, second, conflicting))

    assert persistence.enumerate() == ()


def test_standard_fact_persistence_preserves_append_order_with_idempotent_batches() -> None:
    from standard.valuation import StandardValuationFactPersistence

    persistence = StandardValuationFactPersistence()
    first = _layer()
    second = _consumption()

    persistence.append((first, second))
    persistence.append((first,))
    persistence.append((second,))

    assert persistence.enumerate() == (first, second)
