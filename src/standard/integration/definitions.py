from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.integration import (
    ContractVersion,
    IntegrationContractIdentity,
    IntegrationContractKind,
)
from accore.platform.reporting import ReportExecutionPlan
from accore.platform.security import SecurityContext
from standard.reporting.inventory_balance import INVENTORY_BALANCE_REPORT_IDENTITY


@dataclass(frozen=True, slots=True)
class StandardIntegrationContract:
    """Immutable descriptive contract metadata published by Standard Edition."""

    identity: IntegrationContractIdentity
    description: str

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Standard Integration contract description must be non-empty.")


STANDARD_INVENTORY_REBUILD_CONTRACT = StandardIntegrationContract(
    identity=IntegrationContractIdentity(
        namespace="standard.processing",
        name="inventory.rebuild",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.COMMAND,
    ),
    description="Rebuild Inventory Register Totals and Valuation derived state.",
)

STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT = StandardIntegrationContract(
    identity=IntegrationContractIdentity(
        namespace="standard.reporting",
        name="inventory.balance",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.QUERY,
    ),
    description="Execute the Standard Inventory Balance report.",
)


@dataclass(frozen=True, slots=True)
class StandardGoodsReceiptImportLine:
    """One validated line in a Standard Goods Receipt import."""

    product: str
    warehouse: str
    quantity: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.product, str) or not self.product.strip():
            raise ValueError("Goods Receipt import product must be non-empty.")
        if not isinstance(self.warehouse, str) or not self.warehouse.strip():
            raise ValueError("Goods Receipt import warehouse must be non-empty.")
        if (
            not isinstance(self.quantity, Decimal)
            or not self.quantity.is_finite()
            or self.quantity <= 0
        ):
            raise ValueError("Goods Receipt import quantity must be a positive finite Decimal.")


@dataclass(frozen=True, slots=True)
class StandardGoodsReceiptImportPayload:
    """Logical payload for importing a single Goods Receipt document."""

    lines: tuple[StandardGoodsReceiptImportLine, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.lines, tuple) or not self.lines:
            raise ValueError("Goods Receipt import must contain at least one line.")
        if not all(isinstance(line, StandardGoodsReceiptImportLine) for line in self.lines):
            raise TypeError("Goods Receipt import lines must be validated line objects.")


def decode_standard_goods_receipt_import_payload(
    payload: object,
) -> StandardGoodsReceiptImportPayload:
    """Decode the public JSON shape into validated Goods Receipt import values."""
    if not isinstance(payload, dict):
        raise TypeError("Goods Receipt import payload must be a JSON object.")
    raw_lines = payload.get("lines")
    if not isinstance(raw_lines, list) or not raw_lines:
        raise ValueError("Goods Receipt import payload must contain a non-empty lines array.")
    lines: list[StandardGoodsReceiptImportLine] = []
    for index, raw_line in enumerate(raw_lines):
        if not isinstance(raw_line, dict):
            raise TypeError(f"Goods Receipt import line {index} must be an object.")
        product = raw_line.get("product")
        warehouse = raw_line.get("warehouse")
        quantity = raw_line.get("quantity")
        if not isinstance(product, str) or not isinstance(warehouse, str):
            raise TypeError(
                f"Goods Receipt import line {index} requires product and warehouse strings."
            )
        if isinstance(quantity, bool) or not isinstance(quantity, (int, float, str, Decimal)):
            raise TypeError(f"Goods Receipt import line {index} requires a decimal quantity.")
        try:
            decimal_quantity = Decimal(str(quantity))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Goods Receipt import line {index} has an invalid quantity.") from exc
        lines.append(StandardGoodsReceiptImportLine(product, warehouse, decimal_quantity))
    return StandardGoodsReceiptImportPayload(tuple(lines))


@dataclass(frozen=True, slots=True)
class StandardGoodsReceiptImportContract(StandardIntegrationContract):
    """Contract for importing a Goods Receipt through the Standard business boundary."""

    def validate(self, payload: object) -> None:
        if not isinstance(payload, StandardGoodsReceiptImportPayload):
            raise TypeError("Goods Receipt import payload has an unsupported type.")
        if not payload.lines:
            raise ValueError("Goods Receipt import must contain at least one line.")


@dataclass(frozen=True, slots=True)
class StandardInventoryBalanceExportContract(StandardIntegrationContract):
    """Contract for exporting the Standard Inventory Balance report as JSON."""

    def validate(self, payload: object) -> None:
        if not isinstance(payload, ReportExecutionPlan):
            raise TypeError("Inventory Balance export requires a ReportExecutionPlan.")
        if payload.compiled.definition.identity != INVENTORY_BALANCE_REPORT_IDENTITY:
            raise ValueError("Inventory Balance export requires the Standard report plan.")


class StandardGoodsReceiptImportExecutor(Protocol):
    """Host-owned business boundary that persists and posts an imported receipt."""

    def execute(
        self,
        payload: StandardGoodsReceiptImportPayload,
        security_context: SecurityContext,
        request_identity: Identifier,
    ) -> object:
        """Create and post the receipt using existing object and Posting services."""
        ...


STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT = StandardGoodsReceiptImportContract(
    identity=IntegrationContractIdentity(
        namespace="standard.posting",
        name="goods-receipt.import",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.IMPORT,
    ),
    description="Import and post a Goods Receipt through the Standard Posting boundary.",
)

STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT = StandardInventoryBalanceExportContract(
    identity=IntegrationContractIdentity(
        namespace="standard.reporting",
        name="inventory.balance",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.EXPORT,
    ),
    description="Export the Standard Inventory Balance report as JSON.",
)


__all__ = [
    "STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT",
    "STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT",
    "STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT",
    "STANDARD_INVENTORY_REBUILD_CONTRACT",
    "StandardGoodsReceiptImportContract",
    "StandardGoodsReceiptImportExecutor",
    "StandardGoodsReceiptImportLine",
    "StandardGoodsReceiptImportPayload",
    "StandardIntegrationContract",
    "StandardInventoryBalanceExportContract",
    "decode_standard_goods_receipt_import_payload",
]
