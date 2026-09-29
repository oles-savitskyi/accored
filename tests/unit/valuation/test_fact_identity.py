from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.valuation import (
    DefaultValuationFactIdentityFactory,
    ValuationFactType,
    ValuationOperationIdentity,
)

WHEN = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def test_same_operation_fact_semantics_produce_same_identity() -> None:
    factory = DefaultValuationFactIdentityFactory()
    operation = ValuationOperationIdentity("operation-1")
    key = (Identifier.new(), Decimal("10.00"), WHEN)

    first = factory.for_operation_fact(operation, ValuationFactType.LAYER, key)
    second = factory.for_operation_fact(operation, ValuationFactType.LAYER, key)

    assert first == second


def test_different_operation_identity_produces_different_identity() -> None:
    factory = DefaultValuationFactIdentityFactory()
    key = (Identifier.new(), Decimal("10.00"), WHEN)

    first = factory.for_operation_fact(
        ValuationOperationIdentity("operation-1"), ValuationFactType.LAYER, key
    )
    second = factory.for_operation_fact(
        ValuationOperationIdentity("operation-2"), ValuationFactType.LAYER, key
    )

    assert first != second


def test_different_fact_kind_produces_different_identity() -> None:
    factory = DefaultValuationFactIdentityFactory()
    operation = ValuationOperationIdentity("operation-1")
    key = (Identifier.new(), Decimal("10.00"), WHEN)

    first = factory.for_operation_fact(operation, ValuationFactType.LAYER, key)
    second = factory.for_operation_fact(operation, ValuationFactType.CONSUMPTION, key)

    assert first != second


def test_mapping_order_does_not_change_identity() -> None:
    factory = DefaultValuationFactIdentityFactory()
    operation = ValuationOperationIdentity("operation-1")

    first = factory.for_operation_fact(
        operation,
        ValuationFactType.LAYER,
        ({"b": "2", "a": "1"},),
    )
    second = factory.for_operation_fact(
        operation,
        ValuationFactType.LAYER,
        ({"a": "1", "b": "2"},),
    )

    assert first == second


def test_different_semantic_key_produces_different_identity() -> None:
    factory = DefaultValuationFactIdentityFactory()
    operation = ValuationOperationIdentity("operation-1")
    identity = Identifier.new()

    first = factory.for_operation_fact(
        operation,
        ValuationFactType.LAYER,
        (identity, Decimal("10.00"), WHEN),
    )
    second = factory.for_operation_fact(
        operation,
        ValuationFactType.LAYER,
        (identity, Decimal("11.00"), WHEN),
    )

    assert first != second


def test_identity_is_a_valid_identifier() -> None:
    factory = DefaultValuationFactIdentityFactory()
    identity = factory.for_operation_fact(
        ValuationOperationIdentity("operation-1"),
        ValuationFactType.REVERSAL,
        (Identifier.new(),),
    )

    assert len(str(identity)) == 26
    assert Identifier.from_str(str(identity)) == identity
