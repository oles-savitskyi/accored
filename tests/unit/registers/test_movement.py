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


def test_movement_is_immutable_and_explicit() -> None:
    movement = Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=Identifier.new(),
        movement_type=MovementType.INCOME,
        dimensions=MovementDimensions.from_mapping({"product": "P1"}),
        resources=MovementResources.from_mapping({"quantity": Decimal(1)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=datetime(2026, 9, 16, tzinfo=UTC),
    )
    assert movement.movement_type is MovementType.INCOME
    assert movement.resources.get("quantity") == Decimal(1)
