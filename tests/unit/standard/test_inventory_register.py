from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
)
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_QUANTITY_RESOURCE,
    INVENTORY_REGISTER_ID,
    INVENTORY_WAREHOUSE_DIMENSION,
    InventoryRegisterPostingContract,
    inventory_register_configuration,
    inventory_totals_definition,
)


def make_movement(movement_type: MovementType) -> Movement:
    return Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=INVENTORY_REGISTER_ID,
        movement_type=movement_type,
        dimensions=MovementDimensions.from_mapping({"product": "P1", "warehouse": "W1"}),
        resources=MovementResources.from_mapping({"quantity": Decimal(2)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=None,
    )


def test_inventory_totals_definition_is_inventory_specific() -> None:
    definition = inventory_totals_definition()

    assert definition.register_identity == INVENTORY_REGISTER_ID
    assert definition.dimensions == (INVENTORY_PRODUCT_DIMENSION, INVENTORY_WAREHOUSE_DIMENSION)
    assert definition.resource_name == INVENTORY_QUANTITY_RESOURCE
    assert definition.movement_type_signs[MovementType.INCOME] == 1
    assert definition.movement_type_signs[MovementType.EXPENSE] == -1
    assert definition.resource_type is Decimal


@pytest.mark.parametrize("movement_type", [MovementType.INCOME, MovementType.EXPENSE])
def test_inventory_contract_accepts_supported_movement_types(movement_type: MovementType) -> None:
    InventoryRegisterPostingContract().validate(make_movement(movement_type))


def test_inventory_configuration_is_declarative() -> None:
    configuration = inventory_register_configuration()

    assert configuration.register_identity == INVENTORY_REGISTER_ID
    assert isinstance(configuration.posting_contract, InventoryRegisterPostingContract)
