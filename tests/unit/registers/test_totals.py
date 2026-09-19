from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    DefaultTotalsEngine,
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
    TotalsDefinition,
    TotalsDefinitionError,
    TotalsKey,
    TotalsKeyError,
    TotalsMovementTypeError,
    TotalsResourceError,
)


def make_definition(register: Identifier) -> TotalsDefinition:
    return TotalsDefinition(
        register_identity=register,
        dimensions=("product", "warehouse"),
        resource_name="quantity",
        movement_type_signs={
            MovementType.INCOME: 1,
            MovementType.EXPENSE: -1,
        },
    )


def make_movement(
    *,
    register: Identifier,
    movement_type: MovementType = MovementType.INCOME,
    product: str = "P1",
    warehouse: str = "W1",
    quantity: Decimal = Decimal(1),
) -> Movement:
    return Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register,
        movement_type=movement_type,
        dimensions=MovementDimensions.from_mapping({"product": product, "warehouse": warehouse}),
        resources=MovementResources.from_mapping({"quantity": quantity}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=None,
    )


def test_totals_key_is_immutable_and_order_independent() -> None:
    first = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    second = TotalsKey.from_mapping({"warehouse": "W1", "product": "P1"})

    assert first == second
    assert first.get("product") == "P1"
    assert dict(first.items()) == {"product": "P1", "warehouse": "W1"}
    with pytest.raises(TypeError):
        first.values["product"] = "P2"  # type: ignore[index]


def test_apply_aggregates_income_and_expense_into_one_total() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))

    engine.apply(make_movement(register=register, quantity=Decimal(10)))
    engine.apply(
        make_movement(
            register=register,
            movement_type=MovementType.EXPENSE,
            quantity=Decimal(3),
        )
    )

    key = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    assert engine.get(register, key) == Decimal(7)


def test_remove_reverses_one_movement_contribution() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    movement = make_movement(register=register, quantity=Decimal(10))

    engine.apply(movement)
    engine.remove(movement)

    key = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    assert engine.get(register, key) == Decimal(0)


def test_rebuild_reconstructs_from_authoritative_movements() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    first = make_movement(register=register, quantity=Decimal(100))
    second = make_movement(
        register=register,
        movement_type=MovementType.EXPENSE,
        quantity=Decimal(30),
    )
    third = make_movement(register=register, product="P2", quantity=Decimal(20))

    engine.apply(first)
    engine.apply(second)
    engine.apply(third)
    engine.rebuild(register, (third, first, second))

    assert engine.get(
        register, TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    ) == Decimal(70)
    assert engine.get(
        register, TotalsKey.from_mapping({"product": "P2", "warehouse": "W1"})
    ) == Decimal(20)


def test_rebuild_isolated_from_previous_totals_on_success() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    stale = make_movement(register=register, quantity=Decimal(99))
    current = make_movement(register=register, quantity=Decimal(7))

    engine.apply(stale)
    engine.rebuild(register, (current,))

    key = TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"})
    assert engine.get(register, key) == Decimal(7)


def test_failed_rebuild_does_not_publish_partial_replacement() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    existing = make_movement(register=register, quantity=Decimal(7))
    missing_dimension = make_movement(register=register, quantity=Decimal(3))
    missing_dimension = Movement(
        identity=missing_dimension.identity,
        source_document_identity=missing_dimension.source_document_identity,
        register_identity=register,
        movement_type=missing_dimension.movement_type,
        dimensions=MovementDimensions.from_mapping({"product": "P1"}),
        resources=missing_dimension.resources,
        attributes=missing_dimension.attributes,
        accounting_time=missing_dimension.accounting_time,
    )
    engine.apply(existing)

    with pytest.raises(TotalsKeyError):
        engine.rebuild(register, (missing_dimension,))

    assert engine.get(
        register,
        TotalsKey.from_mapping({"product": "P1", "warehouse": "W1"}),
    ) == Decimal(7)


def test_missing_resource_is_explicit_failure() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    movement = make_movement(register=register)
    movement = Movement(
        identity=movement.identity,
        source_document_identity=movement.source_document_identity,
        register_identity=register,
        movement_type=movement.movement_type,
        dimensions=movement.dimensions,
        resources=MovementResources.from_mapping({}),
        attributes=movement.attributes,
        accounting_time=movement.accounting_time,
    )

    with pytest.raises(TotalsResourceError):
        engine.apply(movement)


def test_invalid_resource_type_is_not_coerced() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    movement = make_movement(register=register)
    movement = Movement(
        identity=movement.identity,
        source_document_identity=movement.source_document_identity,
        register_identity=register,
        movement_type=movement.movement_type,
        dimensions=movement.dimensions,
        resources=MovementResources.from_mapping({"quantity": "1"}),
        attributes=movement.attributes,
        accounting_time=movement.accounting_time,
    )

    with pytest.raises(TotalsResourceError):
        engine.apply(movement)


def test_unknown_movement_type_is_explicit_failure() -> None:
    register = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(register),))
    movement = make_movement(register=register)
    movement = Movement(
        identity=movement.identity,
        source_document_identity=movement.source_document_identity,
        register_identity=register,
        movement_type="TRANSFER",  # type: ignore[arg-type]
        dimensions=movement.dimensions,
        resources=movement.resources,
        attributes=movement.attributes,
        accounting_time=movement.accounting_time,
    )

    with pytest.raises(TotalsMovementTypeError):
        engine.apply(movement)


def test_unconfigured_register_is_explicit_failure() -> None:
    configured = Identifier.new()
    other = Identifier.new()
    engine = DefaultTotalsEngine((make_definition(configured),))

    with pytest.raises(TotalsDefinitionError):
        engine.apply(make_movement(register=other))
