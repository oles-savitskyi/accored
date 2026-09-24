from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    Movement,
    MovementType,
    RegisterPostingContract,
    TotalsDefinition,
)

INVENTORY_REGISTER_ID = Identifier.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAT")
INVENTORY_PRODUCT_DIMENSION = "product"
INVENTORY_WAREHOUSE_DIMENSION = "warehouse"
INVENTORY_QUANTITY_RESOURCE = "quantity"

_ALLOWED_MOVEMENT_TYPES = frozenset({MovementType.INCOME, MovementType.EXPENSE})


class InventoryRegisterPostingContract:
    def validate(self, movement: Movement) -> None:
        if movement.register_identity != INVENTORY_REGISTER_ID:
            raise ValueError("Movement does not target the Inventory register.")
        if movement.movement_type not in _ALLOWED_MOVEMENT_TYPES:
            raise ValueError("Movement Type is not configured for the Inventory register.")

        product = movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION)
        warehouse = movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION)
        quantity = movement.resources.get(INVENTORY_QUANTITY_RESOURCE)

        if not isinstance(product, str) or not product.strip():
            raise ValueError("Inventory Movement requires Product.")
        if not isinstance(warehouse, str) or not warehouse.strip():
            raise ValueError("Inventory Movement requires Warehouse.")
        if not isinstance(quantity, Decimal) or quantity <= 0:
            raise ValueError("Inventory Movement requires a positive Decimal Quantity.")


def inventory_totals_definition() -> TotalsDefinition:
    return TotalsDefinition(
        register_identity=INVENTORY_REGISTER_ID,
        dimensions=(INVENTORY_PRODUCT_DIMENSION, INVENTORY_WAREHOUSE_DIMENSION),
        resource_name=INVENTORY_QUANTITY_RESOURCE,
        movement_type_signs={
            MovementType.INCOME: 1,
            MovementType.EXPENSE: -1,
        },
        resource_type=Decimal,
    )


@dataclass(frozen=True, slots=True)
class InventoryRegisterConfiguration:
    register_identity: Identifier
    totals_definition: TotalsDefinition
    posting_contract: RegisterPostingContract


def inventory_register_configuration() -> InventoryRegisterConfiguration:
    return InventoryRegisterConfiguration(
        register_identity=INVENTORY_REGISTER_ID,
        totals_definition=inventory_totals_definition(),
        posting_contract=InventoryRegisterPostingContract(),
    )


__all__ = [
    "INVENTORY_PRODUCT_DIMENSION",
    "INVENTORY_QUANTITY_RESOURCE",
    "INVENTORY_REGISTER_ID",
    "INVENTORY_WAREHOUSE_DIMENSION",
    "InventoryRegisterConfiguration",
    "InventoryRegisterPostingContract",
    "inventory_register_configuration",
    "inventory_totals_definition",
]
