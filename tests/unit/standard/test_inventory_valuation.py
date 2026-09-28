from datetime import UTC, datetime
from decimal import Decimal

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
)
from standard.valuation import InventoryValuationInputProvider, InventoryValuationKeyMapper


def movement() -> Movement:
    return Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=INVENTORY_REGISTER_ID,
        movement_type=MovementType.INCOME,
        dimensions=MovementDimensions.from_mapping(
            {
                INVENTORY_PRODUCT_DIMENSION: "P1",
                INVENTORY_WAREHOUSE_DIMENSION: "W1",
            }
        ),
        resources=MovementResources.from_mapping({INVENTORY_QUANTITY_RESOURCE: Decimal("2.5")}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
    )


def test_inventory_key_mapper_uses_standard_dimensions() -> None:
    key = InventoryValuationKeyMapper().map(movement())

    assert key.canonical_dimensions == (("product", "P1"), ("warehouse", "W1"))


def test_inventory_input_provider_preserves_document_and_source_identity() -> None:
    source = movement()
    result = InventoryValuationInputProvider(InventoryValuationKeyMapper()).provide(source)

    assert result.valuation_key.canonical_dimensions == (("product", "P1"), ("warehouse", "W1"))
    assert result.quantity == Decimal("2.5")
    assert result.document_identity == source.source_document_identity
    assert result.source_identity == source.identity
    assert result.occurred_at == source.accounting_time
