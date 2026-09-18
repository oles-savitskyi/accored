from __future__ import annotations

from decimal import Decimal

from accore.platform.registers import Movement

from .goods_receipt import GOODS_RECEIPT_MOVEMENT_TYPE, INVENTORY_REGISTER_ID


class InventoryRegisterPostingContract:
    def validate(self, movement: Movement) -> None:
        if movement.register_identity != INVENTORY_REGISTER_ID:
            raise ValueError("Movement does not target the Inventory register.")
        if movement.movement_type is not GOODS_RECEIPT_MOVEMENT_TYPE:
            raise ValueError("Movement Type is not configured for Goods Receipt.")

        product = movement.dimensions.get("product")
        warehouse = movement.dimensions.get("warehouse")
        quantity = movement.resources.get("quantity")
        if not isinstance(product, str) or not product.strip():
            raise ValueError("Inventory Movement requires Product.")
        if not isinstance(warehouse, str) or not warehouse.strip():
            raise ValueError("Inventory Movement requires Warehouse.")
        if not isinstance(quantity, Decimal) or quantity <= 0:
            raise ValueError("Inventory Movement requires a positive Decimal Quantity.")
