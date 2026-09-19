from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    BalanceQuery,
    BalanceQueryValidationError,
    BalanceResult,
    DefaultBalanceQueryService,
    TotalsKey,
)


class StubTotalsReader:
    def __init__(self, value: Decimal) -> None:
        self.value = value
        self.calls: list[tuple[Identifier, TotalsKey]] = []

    def get(self, register_identity: Identifier, key: TotalsKey) -> Decimal:
        self.calls.append((register_identity, key))
        return self.value


def test_balance_query_is_immutable_and_uses_one_concrete_scope() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    query = BalanceQuery(register_identity=register, aggregation_scope=scope)

    assert query.register_identity == register
    assert query.aggregation_scope == scope

    with pytest.raises(AttributeError):
        query.register_identity = Identifier.new()  # type: ignore[misc]


def test_balance_query_requires_register_identity() -> None:
    scope = TotalsKey.from_mapping({"product": "P1"})

    with pytest.raises(BalanceQueryValidationError):
        BalanceQuery(register_identity=None, aggregation_scope=scope)  # type: ignore[arg-type]


def test_balance_query_requires_aggregation_scope() -> None:
    register = Identifier.new()

    with pytest.raises(BalanceQueryValidationError):
        BalanceQuery(register_identity=register, aggregation_scope=None)  # type: ignore[arg-type]


def test_balance_query_reads_exactly_one_total() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    totals = StubTotalsReader(Decimal(125))
    service = DefaultBalanceQueryService(totals)

    result = service.query(BalanceQuery(register_identity=register, aggregation_scope=scope))

    assert result == BalanceResult(
        register_identity=register,
        aggregation_scope=scope,
        value=Decimal(125),
    )
    assert totals.calls == [(register, scope)]


def test_balance_query_returns_zero_for_empty_aggregate() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    totals = StubTotalsReader(Decimal(0))

    result = DefaultBalanceQueryService(totals).query(
        BalanceQuery(register_identity=register, aggregation_scope=scope)
    )

    assert result.value == Decimal(0)


def test_balance_query_preserves_negative_total() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    totals = StubTotalsReader(Decimal("-12.5"))

    result = DefaultBalanceQueryService(totals).query(
        BalanceQuery(register_identity=register, aggregation_scope=scope)
    )

    assert result.value == Decimal("-12.5")


def test_balance_result_is_immutable() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    result = BalanceResult(register, scope, Decimal(10))

    with pytest.raises(AttributeError):
        result.value = Decimal(20)  # type: ignore[misc]


def test_balance_result_rejects_invalid_value_type() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})

    with pytest.raises(BalanceQueryValidationError):
        BalanceResult(register, scope, "10")  # type: ignore[arg-type]


def test_balance_query_propagates_totals_failures() -> None:
    register = Identifier.new()
    scope = TotalsKey.from_mapping({"product": "P1"})

    class FailingTotalsReader:
        def get(self, register_identity: Identifier, key: TotalsKey) -> Decimal:
            raise RuntimeError("totals unavailable")

    service = DefaultBalanceQueryService(FailingTotalsReader())

    with pytest.raises(RuntimeError, match="totals unavailable"):
        service.query(BalanceQuery(register, scope))
