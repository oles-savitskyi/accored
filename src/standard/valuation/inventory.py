from __future__ import annotations

from decimal import Decimal

from accore.platform.registers import Movement
from accore.platform.valuation import (
    ValuationInput,
    ValuationKey,
    ValuationKeyMapper,
    ValuationValidationError,
)
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_QUANTITY_RESOURCE,
    INVENTORY_WAREHOUSE_DIMENSION,
)


class InventoryValuationKeyMapper:
    """Map Standard Inventory dimensions to the generic valuation key."""

    def map(self, movement: Movement) -> ValuationKey:
        product = movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION)
        warehouse = movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION)
        if not isinstance(product, str) or not product.strip():
            raise ValuationValidationError("Inventory valuation requires Product.")
        if not isinstance(warehouse, str) or not warehouse.strip():
            raise ValuationValidationError("Inventory valuation requires Warehouse.")
        return ValuationKey(
            {
                INVENTORY_PRODUCT_DIMENSION: product,
                INVENTORY_WAREHOUSE_DIMENSION: warehouse,
            }
        )


class InventoryValuationInputProvider:
    """Provide generic valuation input from Standard Inventory movements."""

    def __init__(self, key_mapper: ValuationKeyMapper) -> None:
        self._key_mapper = key_mapper

    def provide(self, movement: Movement) -> ValuationInput:
        quantity = movement.resources.get(INVENTORY_QUANTITY_RESOURCE)
        if not hasattr(movement, "accounting_time") or movement.accounting_time is None:
            raise ValuationValidationError("Inventory valuation requires accounting_time.")
        if not isinstance(quantity, Decimal) or quantity <= 0:
            raise ValuationValidationError(
                "Inventory valuation requires a positive Decimal Quantity."
            )
        return ValuationInput(
            valuation_key=self._key_mapper.map(movement),
            quantity=quantity,
            document_identity=movement.source_document_identity,
            source_identity=movement.identity,
            occurred_at=movement.accounting_time,
        )


__all__ = ["InventoryValuationInputProvider", "InventoryValuationKeyMapper"]
