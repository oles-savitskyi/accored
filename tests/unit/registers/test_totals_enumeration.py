from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    DefaultTotalsEngine,
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
    TotalsDefinition,
    TotalsKey,
)


def test_enumerate_returns_current_non_zero_totals() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine(
        (
            TotalsDefinition(
                register_identity=register,
                dimensions=("product", "warehouse"),
                resource_name="quantity",
                movement_type_signs={
                    MovementType.INCOME: 1,
                    MovementType.EXPENSE: -1,
                },
            ),
        )
    )

    movement = Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register,
        movement_type=MovementType.INCOME,
        dimensions=MovementDimensions.from_mapping({"product": "P1", "warehouse": "W1"}),
        resources=MovementResources.from_mapping({"quantity": Decimal(5)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=None,
    )
    engine.apply(movement)
    key = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})

    assert engine.enumerate(register) == ((key, Decimal(5)),)
