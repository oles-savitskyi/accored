from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    ConsumptionRequest,
    FIFOValuationMethod,
    SyntheticConsumptionService,
    ValuationInsufficientQuantityError,
    ValuationKey,
    ValuationLayer,
    ValuationValidationError,
)


@pytest.fixture
def valuation_key() -> ValuationKey:
    return ValuationKey({"product": "PR-01", "warehouse": "WH-01"})


@pytest.fixture
def timestamp() -> datetime:
    return datetime(2026, 9, 25, 15, 0, tzinfo=UTC)


def make_layer(
    key: ValuationKey,
    *,
    quantity: str,
    cost: str,
    created_at: datetime,
) -> ValuationLayer:
    return ValuationLayer(
        identity=Identifier.new(),
        valuation_key=key,
        quantity=Decimal(quantity),
        total_cost=Decimal(cost),
        source_document_identity=Identifier.new(),
        source_movement_identity=Identifier.new(),
        created_at=created_at,
    )


def make_request(key: ValuationKey, *, quantity: str, timestamp: datetime) -> ConsumptionRequest:
    return ConsumptionRequest(
        identity=Identifier.new(),
        valuation_key=key,
        quantity=Decimal(quantity),
        source_identity=Identifier.new(),
        occurred_at=timestamp,
    )


def test_fifo_consumes_partial_single_layer(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)
    result = FIFOValuationMethod().consume(
        [layer],
        make_request(valuation_key, quantity="4", timestamp=timestamp),
    )

    assert len(result.consumptions) == 1
    assert result.consumptions[0].quantity == Decimal(4)
    assert result.consumptions[0].cost == Decimal(40)
    assert result.total_cost == Decimal(40)
    assert result.remaining_layers[0].quantity == Decimal(6)
    assert result.remaining_layers[0].total_cost == Decimal(60)
    assert result.remaining_layers[0].identity == layer.identity


def test_fifo_consumes_exact_single_layer(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)
    result = FIFOValuationMethod().consume(
        [layer],
        make_request(valuation_key, quantity="10", timestamp=timestamp),
    )

    assert result.consumptions[0].cost == Decimal(100)
    assert result.total_cost == Decimal(100)
    assert result.remaining_layers == ()


def test_fifo_consumes_multiple_layers_in_creation_order(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    first = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)
    second = make_layer(
        valuation_key,
        quantity="20",
        cost="300",
        created_at=timestamp + timedelta(seconds=1),
    )

    result = FIFOValuationMethod().consume(
        [second, first],
        make_request(valuation_key, quantity="15", timestamp=timestamp),
    )

    assert [item.layer_identity for item in result.consumptions] == [
        first.identity,
        second.identity,
    ]
    assert [item.quantity for item in result.consumptions] == [Decimal(10), Decimal(5)]
    assert [item.cost for item in result.consumptions] == [Decimal(100), Decimal(75)]
    assert result.total_cost == Decimal(175)
    assert result.remaining_layers == (
        ValuationLayer(
            identity=second.identity,
            valuation_key=second.valuation_key,
            quantity=Decimal(15),
            total_cost=Decimal(225),
            source_document_identity=second.source_document_identity,
            source_movement_identity=second.source_movement_identity,
            created_at=second.created_at,
        ),
    )


def test_fifo_uses_identity_as_tie_breaker_for_equal_timestamps(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    first = make_layer(valuation_key, quantity="5", cost="50", created_at=timestamp)
    second = make_layer(valuation_key, quantity="5", cost="100", created_at=timestamp)
    expected_first, expected_second = sorted(
        (first, second),
        key=lambda layer: str(layer.identity),
    )

    result = FIFOValuationMethod().consume(
        [first, second],
        make_request(valuation_key, quantity="5", timestamp=timestamp),
    )

    assert result.consumptions[0].layer_identity == expected_first.identity
    assert result.remaining_layers[0].identity == expected_second.identity


def test_fifo_rejects_insufficient_quantity(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)

    with pytest.raises(ValuationInsufficientQuantityError):
        FIFOValuationMethod().consume(
            [layer],
            make_request(valuation_key, quantity="11", timestamp=timestamp),
        )


def test_fifo_accepts_zero_cost_layer(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="0", created_at=timestamp)
    result = FIFOValuationMethod().consume(
        [layer],
        make_request(valuation_key, quantity="4", timestamp=timestamp),
    )

    assert result.total_cost == Decimal(0)
    assert result.consumptions[0].cost == Decimal(0)


def test_fifo_does_not_mutate_input_layers(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)

    FIFOValuationMethod().consume(
        [layer],
        make_request(valuation_key, quantity="4", timestamp=timestamp),
    )

    assert layer.quantity == Decimal(10)
    assert layer.total_cost == Decimal(100)


def test_fifo_rejects_layer_for_different_valuation_key(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)
    other_key = ValuationKey({"product": "PR-02", "warehouse": "WH-01"})

    with pytest.raises(ValuationValidationError, match="valuation key"):
        FIFOValuationMethod().consume(
            [layer],
            make_request(other_key, quantity="1", timestamp=timestamp),
        )


def test_synthetic_consumption_service_delegates_to_method(
    valuation_key: ValuationKey,
    timestamp: datetime,
) -> None:
    layer = make_layer(valuation_key, quantity="10", cost="100", created_at=timestamp)
    service = SyntheticConsumptionService(FIFOValuationMethod())

    result = service.consume(
        [layer],
        make_request(valuation_key, quantity="2", timestamp=timestamp),
    )

    assert result.total_cost == Decimal(20)
    assert result.consumptions[0].layer_identity == layer.identity
