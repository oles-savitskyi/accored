from __future__ import annotations

from accore.platform.registers import TotalsKey, TotalsReader
from accore.platform.reporting import (
    ReportDataSourceError,
    ReportDataSourceIdentity,
    ReportDataSourceRequest,
    ReportDataType,
    ReportField,
    ReportReadConsistency,
    ReportRow,
    ReportSchema,
    ReportValue,
)
from accore.platform.valuation import CostBalance, CostTotalsReader, ValuationKey
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_REGISTER_ID,
    INVENTORY_WAREHOUSE_DIMENSION,
)

INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY = ReportDataSourceIdentity("inventory.balance")

INVENTORY_BALANCE_REPORT_SCHEMA = ReportSchema(
    (
        ReportField(INVENTORY_PRODUCT_DIMENSION, ReportDataType.STRING),
        ReportField(INVENTORY_WAREHOUSE_DIMENSION, ReportDataType.STRING),
        ReportField("quantity", ReportDataType.DECIMAL),
        ReportField("cost", ReportDataType.DECIMAL),
    )
)


class InventoryBalanceReportSourceError(ReportDataSourceError):
    """Raised when Inventory Balance cannot be composed from domain state."""


class InventoryBalanceReportSource:
    """Expose current Inventory quantity and valuation cost as Reporting rows."""

    identity = INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY

    def __init__(self, totals: TotalsReader, cost_totals: CostTotalsReader) -> None:
        self._totals = totals
        self._cost_totals = cost_totals

    def schema(self) -> ReportSchema:
        return INVENTORY_BALANCE_REPORT_SCHEMA

    def consistency(self) -> ReportReadConsistency:
        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]:
        del request
        register_totals = self._totals.enumerate(INVENTORY_REGISTER_ID)
        valuation_balances = self._valuation_balances()
        rows: list[tuple[str, str, ReportRow]] = []

        for key, quantity in register_totals:
            product, warehouse = self._inventory_scope(key)
            valuation = valuation_balances.get((product, warehouse))
            if valuation is None:
                raise InventoryBalanceReportSourceError(
                    "Inventory Balance is missing valuation state for "
                    f"product={product!r}, warehouse={warehouse!r}."
                )
            rows.append(
                (
                    product,
                    warehouse,
                    ReportRow(
                        {
                            INVENTORY_PRODUCT_DIMENSION: ReportValue(product),
                            INVENTORY_WAREHOUSE_DIMENSION: ReportValue(warehouse),
                            "quantity": ReportValue(quantity),
                            "cost": ReportValue(valuation.cost),
                        }
                    ),
                )
            )

        rows.sort(key=lambda item: (item[0], item[1]))
        return tuple(row for _, _, row in rows)

    def _valuation_balances(self) -> dict[tuple[str, str], CostBalance]:
        balances: dict[tuple[str, str], CostBalance] = {}
        for balance in self._cost_totals.enumerate():
            product, warehouse = self._valuation_scope(balance.valuation_key)
            balances[(product, warehouse)] = balance
        return balances

    @staticmethod
    def _inventory_scope(key: TotalsKey) -> tuple[str, str]:
        product = key.get(INVENTORY_PRODUCT_DIMENSION)
        warehouse = key.get(INVENTORY_WAREHOUSE_DIMENSION)
        if not isinstance(product, str) or not product.strip():
            raise InventoryBalanceReportSourceError(
                "Inventory Register TotalsKey has an invalid product dimension."
            )
        if not isinstance(warehouse, str) or not warehouse.strip():
            raise InventoryBalanceReportSourceError(
                "Inventory Register TotalsKey has an invalid warehouse dimension."
            )
        return product, warehouse

    @staticmethod
    def _valuation_scope(key: ValuationKey) -> tuple[str, str]:
        product = key.get(INVENTORY_PRODUCT_DIMENSION)
        warehouse = key.get(INVENTORY_WAREHOUSE_DIMENSION)
        if not isinstance(product, str) or not product.strip():
            raise InventoryBalanceReportSourceError(
                "Inventory valuation key has an invalid product dimension."
            )
        if not isinstance(warehouse, str) or not warehouse.strip():
            raise InventoryBalanceReportSourceError(
                "Inventory valuation key has an invalid warehouse dimension."
            )
        return product, warehouse


__all__ = [
    "INVENTORY_BALANCE_REPORT_SCHEMA",
    "INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY",
    "InventoryBalanceReportSource",
    "InventoryBalanceReportSourceError",
]
