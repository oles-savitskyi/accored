from datetime import UTC, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.registers import TotalsKey, TotalsReader
from accore.platform.reporting import (
    ReportDataSourceRequest,
    ReportDataType,
    ReportFilter,
    ReportFilterOperator,
    ReportValue,
)
from accore.platform.valuation import CostBalance, CostTotalsReader, ValuationKey
from standard.registers.inventory import INVENTORY_REGISTER_ID
from standard.reporting import (
    INVENTORY_BALANCE_REPORT_SCHEMA,
    INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY,
    InventoryBalanceReportSource,
    InventoryBalanceReportSourceError,
)


class StubTotals(TotalsReader):
    def __init__(
        self,
        entries: tuple[tuple[TotalsKey, Decimal], ...],
        enumerate_error: Exception | None = None,
    ) -> None:
        self.entries = entries
        self.enumerate_error = enumerate_error

    def get(self, register_identity: Identifier, key: TotalsKey) -> Decimal:
        return Decimal(0)

    def enumerate(self, register_identity: Identifier) -> tuple[tuple[TotalsKey, Decimal], ...]:
        assert register_identity == INVENTORY_REGISTER_ID
        if self.enumerate_error is not None:
            raise self.enumerate_error
        return self.entries


class StubCostTotals(CostTotalsReader):
    def __init__(
        self,
        balances: tuple[CostBalance, ...],
        enumerate_error: Exception | None = None,
    ) -> None:
        self.balances = balances
        self.enumerate_error = enumerate_error

    def get(self, valuation_key: ValuationKey) -> CostBalance:
        return next(balance for balance in self.balances if balance.valuation_key == valuation_key)

    def enumerate(self) -> tuple[CostBalance, ...]:
        if self.enumerate_error is not None:
            raise self.enumerate_error
        return self.balances


def balance(product: str, warehouse: str, cost: str) -> CostBalance:
    return CostBalance(
        valuation_key=ValuationKey({"product": product, "warehouse": warehouse}),
        quantity=Decimal(10),
        cost=Decimal(cost),
        calculated_at=datetime(2026, 10, 1, tzinfo=UTC),
    )


def source(
    register_entries: tuple[tuple[TotalsKey, Decimal], ...],
    balances: tuple[CostBalance, ...],
) -> InventoryBalanceReportSource:
    return InventoryBalanceReportSource(StubTotals(register_entries), StubCostTotals(balances))


def test_source_exposes_inventory_balance_schema_and_identity() -> None:
    report_source = source((), ())

    assert report_source.identity is INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY
    assert report_source.schema() is INVENTORY_BALANCE_REPORT_SCHEMA
    assert [field.data_type for field in report_source.schema().fields] == [
        ReportDataType.STRING,
        ReportDataType.STRING,
        ReportDataType.DECIMAL,
        ReportDataType.DECIMAL,
    ]


def test_source_reads_register_scopes_and_matching_valuation_balances() -> None:
    entries = (
        (TotalsKey.from_mapping({"product": "P2", "warehouse": "W2"}), Decimal(3)),
        (TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}), Decimal(7)),
    )

    rows = source(
        entries,
        (balance("P2", "W2", "30"), balance("P1", "W1", "70")),
    ).read(ReportDataSourceRequest())

    assert [
        (
            row["product"].value,
            row["warehouse"].value,
            row["quantity"].value,
            row["cost"].value,
        )
        for row in rows
    ] == [
        ("P1", "W1", Decimal(7), Decimal(70)),
        ("P2", "W2", Decimal(3), Decimal(30)),
    ]


def test_source_returns_empty_for_empty_register_state() -> None:
    assert source((), ()).read(ReportDataSourceRequest()) == ()


def test_source_fails_when_register_scope_has_no_valuation_balance() -> None:
    entries = ((TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}), Decimal(7)),)

    with pytest.raises(InventoryBalanceReportSourceError):
        source(entries, ()).read(ReportDataSourceRequest())


def test_source_ignores_valuation_only_scope() -> None:
    assert source((), (balance("P1", "W1", "70"),)).read(ReportDataSourceRequest()) == ()


def test_source_preserves_explicit_zero_valuation_cost() -> None:
    entries = ((TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}), Decimal(7)),)

    rows = source(entries, (balance("P1", "W1", "0"),)).read(ReportDataSourceRequest())

    assert rows[0]["cost"].value == Decimal(0)


def test_source_ignores_request_filters_and_returns_complete_state() -> None:
    entries = ((TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}), Decimal(7)),)

    request = ReportDataSourceRequest(
        filters=(
            ReportFilter(
                "warehouse",
                ReportFilterOperator.EQUALS,
                ReportValue("OTHER"),
            ),
        )
    )

    rows = source(entries, (balance("P1", "W1", "70"),)).read(request)

    assert len(rows) == 1
    assert rows[0]["warehouse"].value == "W1"


@pytest.mark.parametrize("failing_reader", ["register", "valuation"])
def test_source_propagates_reader_failures(failing_reader: str) -> None:
    error = RuntimeError(f"{failing_reader} read failed")
    entries = ((TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}), Decimal(7)),)
    balances = (balance("P1", "W1", "70"),)

    register_totals = StubTotals(
        entries,
        enumerate_error=error if failing_reader == "register" else None,
    )
    cost_totals = StubCostTotals(
        balances,
        enumerate_error=error if failing_reader == "valuation" else None,
    )

    with pytest.raises(RuntimeError, match=f"{failing_reader} read failed"):
        InventoryBalanceReportSource(register_totals, cost_totals).read(ReportDataSourceRequest())


def test_source_does_not_mutate_reader_state() -> None:
    entries = ((TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}), Decimal(7)),)
    balances = (balance("P1", "W1", "70"),)
    register_totals = StubTotals(entries)
    cost_totals = StubCostTotals(balances)

    InventoryBalanceReportSource(register_totals, cost_totals).read(ReportDataSourceRequest())

    assert register_totals.entries == entries
    assert cost_totals.balances == balances
