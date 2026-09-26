from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    ValuationAdjustment,
    ValuationAllocation,
    ValuationConsumption,
    ValuationFact,
    ValuationKey,
    ValuationLayer,
    ValuationReversal,
    ValuationValidationError,
)


@pytest.fixture
def valuation_key() -> ValuationKey:
    return ValuationKey(
        {
            "product": "PR-01",
            "warehouse": "WH-01",
        }
    )


@pytest.fixture
def timestamp() -> datetime:
    return datetime(2026, 9, 25, 15, 0, tzinfo=UTC)


def test_valuation_layer_accepts_positive_quantity_and_zero_cost(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = ValuationLayer(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        quantity=Decimal(100),
        total_cost=Decimal(0),
        source_document_identity=Identifier.new(),
        source_movement_identity=Identifier.new(),
        created_at=timestamp,
    )

    assert layer.quantity == Decimal(100)
    assert layer.total_cost == Decimal(0)


def test_valuation_layer_rejects_non_positive_quantity(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    with pytest.raises(
        ValuationValidationError,
        match="quantity must be greater than zero",
    ):
        ValuationLayer(
            identity=Identifier.new(),
            valuation_key=valuation_key,
            quantity=Decimal(0),
            total_cost=Decimal(100),
            source_document_identity=Identifier.new(),
            source_movement_identity=Identifier.new(),
            created_at=timestamp,
        )


def test_valuation_layer_rejects_negative_cost(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    with pytest.raises(
        ValuationValidationError,
        match="total_cost cannot be negative",
    ):
        ValuationLayer(
            identity=Identifier.new(),
            valuation_key=valuation_key,
            quantity=Decimal(100),
            total_cost=Decimal(-1),
            source_document_identity=Identifier.new(),
            source_movement_identity=Identifier.new(),
            created_at=timestamp,
        )


def test_valuation_consumption_accepts_zero_cost(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    consumption = ValuationConsumption(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        layer_identity=Identifier.new(),
        quantity=Decimal(10),
        cost=Decimal(0),
        source_identity=Identifier.new(),
        created_at=timestamp,
    )

    assert consumption.quantity == Decimal(10)
    assert consumption.cost == Decimal(0)


def test_valuation_consumption_rejects_non_positive_quantity(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    with pytest.raises(
        ValuationValidationError,
        match="quantity must be greater than zero",
    ):
        ValuationConsumption(
            identity=Identifier.new(),
            valuation_key=valuation_key,
            layer_identity=Identifier.new(),
            quantity=Decimal(0),
            cost=Decimal(10),
            source_identity=Identifier.new(),
            created_at=timestamp,
        )


def test_valuation_consumption_rejects_negative_cost(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    with pytest.raises(
        ValuationValidationError,
        match="cost cannot be negative",
    ):
        ValuationConsumption(
            identity=Identifier.new(),
            valuation_key=valuation_key,
            layer_identity=Identifier.new(),
            quantity=Decimal(10),
            cost=Decimal(-1),
            source_identity=Identifier.new(),
            created_at=timestamp,
        )


def test_valuation_adjustment_preserves_decimal_amount(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    adjustment = ValuationAdjustment(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        amount=Decimal("100.25"),
        source_identity=Identifier.new(),
        reason="Supplier acquisition cost",
        created_at=timestamp,
    )

    assert adjustment.amount == Decimal("100.25")
    assert isinstance(adjustment.amount, Decimal)


def test_valuation_allocation_preserves_decimal_amount(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    allocation = ValuationAllocation(
        identity=Identifier.new(),
        adjustment_identity=Identifier.new(),
        layer_identity=Identifier.new(),
        valuation_key=valuation_key,
        amount=Decimal("50.25"),
        created_at=timestamp,
    )

    assert allocation.amount == Decimal("50.25")
    assert isinstance(allocation.amount, Decimal)


def test_valuation_reversal_is_immutable(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    reversal = ValuationReversal(
        identity=Identifier.new(),
        reversed_identity=Identifier.new(),
        valuation_key=valuation_key,
        source_identity=Identifier.new(),
        created_at=timestamp,
    )

    with pytest.raises(AttributeError):
        reversal.source_identity = Identifier.new()  # type: ignore[misc]


def test_valuation_facts_are_immutable(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = ValuationLayer(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        quantity=Decimal(100),
        total_cost=Decimal(1000),
        source_document_identity=Identifier.new(),
        source_movement_identity=Identifier.new(),
        created_at=timestamp,
    )

    with pytest.raises(AttributeError):
        layer.total_cost = Decimal(2000)  # type: ignore[misc]


def test_valuation_fact_union_accepts_all_fact_types(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = ValuationLayer(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        quantity=Decimal(100),
        total_cost=Decimal(1000),
        source_document_identity=Identifier.new(),
        source_movement_identity=Identifier.new(),
        created_at=timestamp,
    )

    consumption = ValuationConsumption(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        layer_identity=layer.identity,
        quantity=Decimal(10),
        cost=Decimal(100),
        source_identity=Identifier.new(),
        created_at=timestamp,
    )

    adjustment = ValuationAdjustment(
        identity=Identifier.new(),
        valuation_key=valuation_key,
        amount=Decimal(50),
        source_identity=Identifier.new(),
        reason="Additional cost",
        created_at=timestamp,
    )

    allocation = ValuationAllocation(
        identity=Identifier.new(),
        adjustment_identity=adjustment.identity,
        layer_identity=layer.identity,
        valuation_key=valuation_key,
        amount=Decimal(50),
        created_at=timestamp,
    )

    reversal = ValuationReversal(
        identity=Identifier.new(),
        reversed_identity=consumption.identity,
        valuation_key=valuation_key,
        source_identity=Identifier.new(),
        created_at=timestamp,
    )

    facts: tuple[ValuationFact, ...] = (
        layer,
        consumption,
        adjustment,
        allocation,
        reversal,
    )

    assert len(facts) == 5
