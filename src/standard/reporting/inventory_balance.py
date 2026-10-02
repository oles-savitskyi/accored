from __future__ import annotations

from accore.platform.foundation import Identifier
from accore.platform.reporting import (
    ReportAggregation,
    ReportDefinition,
    ReportDimension,
    ReportMeasure,
)
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_WAREHOUSE_DIMENSION,
)

from .inventory import INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY

INVENTORY_BALANCE_REPORT_IDENTITY = Identifier.from_str("01ARZ3NDEKTSV4RRFFQ69G5FB0")

INVENTORY_BALANCE_REPORT_DEFINITION = ReportDefinition(
    identity=INVENTORY_BALANCE_REPORT_IDENTITY,
    name="Inventory Balance",
    source=INVENTORY_BALANCE_REPORT_SOURCE_IDENTITY,
    filters=(),
    dimensions=(
        ReportDimension(
            name="product",
            source_field=INVENTORY_PRODUCT_DIMENSION,
        ),
        ReportDimension(
            name="warehouse",
            source_field=INVENTORY_WAREHOUSE_DIMENSION,
        ),
    ),
    measures=(
        ReportMeasure(
            name="quantity",
            aggregation=ReportAggregation.SUM,
            source_field="quantity",
        ),
        ReportMeasure(
            name="cost",
            aggregation=ReportAggregation.SUM,
            source_field="cost",
        ),
    ),
)

__all__ = [
    "INVENTORY_BALANCE_REPORT_DEFINITION",
    "INVENTORY_BALANCE_REPORT_IDENTITY",
]
