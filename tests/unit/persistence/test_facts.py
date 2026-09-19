from __future__ import annotations

from datetime import UTC, datetime
from inspect import signature

import pytest

from accore.platform.foundation import Identifier
from accore.platform.persistence import (
    PersistenceAlreadyExistsError,
    PersistenceNotFoundError,
    RegisterFactPersistence,
)
from accore.platform.registers import (
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
)


def make_movement(
    *,
    identity: Identifier | None = None,
    source_document_identity: Identifier | None = None,
    register_identity: Identifier | None = None,
    movement_type: MovementType = MovementType.INCOME,
    product: str = "product-1",
    warehouse: str = "warehouse-1",
    quantity: str = "10",
    accounting_time: datetime | None = datetime(
        2026,
        9,
        18,
        tzinfo=UTC,
    ),
) -> Movement:
    return Movement(
        identity=identity or Identifier.new(),
        source_document_identity=source_document_identity or Identifier.new(),
        register_identity=register_identity or Identifier.new(),
        movement_type=movement_type,
        dimensions=MovementDimensions.from_mapping(
            {
                "Product": product,
                "Warehouse": warehouse,
            }
        ),
        resources=MovementResources.from_mapping(
            {
                "Quantity": quantity,
            }
        ),
        attributes=MovementAttributes.from_mapping(
            {
                "source": "test",
            }
        ),
        accounting_time=accounting_time,
    )


class InMemoryRegisterFactPersistence:
    """Reference implementation used only to verify the contract."""

    def __init__(self) -> None:
        self._movements: dict[Identifier, Movement] = {}

    def append(self, movements: list[Movement]) -> None:
        identities = [movement.identity for movement in movements]

        if len(identities) != len(set(identities)):
            raise PersistenceAlreadyExistsError("Duplicate Movement identity in append")

        for identity in identities:
            if identity in self._movements:
                raise PersistenceAlreadyExistsError(f"Movement already exists: {identity}")

        for movement in movements:
            self._movements[movement.identity] = movement

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            sorted(
                (
                    movement
                    for movement in self._movements.values()
                    if movement.register_identity == register_identity
                    and movement.source_document_identity == source_document_identity
                ),
                key=lambda movement: str(movement.identity),
            )
        )

    def remove(self, movement_identities: list[Identifier]) -> None:
        identities = tuple(movement_identities)

        missing = [identity for identity in identities if identity not in self._movements]

        if missing:
            raise PersistenceNotFoundError(f"Movement not found: {missing[0]}")

        for identity in identities:
            del self._movements[identity]

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            sorted(
                (
                    movement
                    for movement in self._movements.values()
                    if movement.register_identity == register_identity
                ),
                key=lambda movement: str(movement.identity),
            )
        )


def test_register_fact_persistence_contract_shape() -> None:
    assert list(signature(RegisterFactPersistence.append).parameters) == [
        "self",
        "movements",
    ]

    assert list(signature(RegisterFactPersistence.find_by_source_document).parameters) == [
        "self",
        "register_identity",
        "source_document_identity",
    ]

    assert list(signature(RegisterFactPersistence.remove).parameters) == [
        "self",
        "movement_identities",
    ]

    assert list(signature(RegisterFactPersistence.enumerate).parameters) == [
        "self",
        "register_identity",
    ]


def test_append_preserves_complete_movement() -> None:
    persistence = InMemoryRegisterFactPersistence()
    movement = make_movement()

    assert persistence.append([movement]) is None

    assert persistence.enumerate(movement.register_identity) == (movement,)


def test_append_rejects_duplicate_movement_identity() -> None:
    persistence = InMemoryRegisterFactPersistence()

    movement = make_movement()
    duplicate = make_movement(
        identity=movement.identity,
        register_identity=movement.register_identity,
    )

    persistence.append([movement])

    with pytest.raises(PersistenceAlreadyExistsError):
        persistence.append([duplicate])

    assert persistence.enumerate(movement.register_identity) == (movement,)


def test_append_rejects_duplicate_identity_inside_same_batch() -> None:
    persistence = InMemoryRegisterFactPersistence()

    movement = make_movement()

    with pytest.raises(PersistenceAlreadyExistsError):
        persistence.append([movement, movement])

    assert persistence.enumerate(movement.register_identity) == ()


def test_find_by_source_document_is_scoped_by_register() -> None:
    persistence = InMemoryRegisterFactPersistence()

    source_document = Identifier.new()
    register_a = Identifier.new()
    register_b = Identifier.new()

    movement_a = make_movement(
        source_document_identity=source_document,
        register_identity=register_a,
    )
    movement_b = make_movement(
        source_document_identity=source_document,
        register_identity=register_b,
    )

    persistence.append([movement_a, movement_b])

    assert persistence.find_by_source_document(
        register_a,
        source_document,
    ) == (movement_a,)

    assert persistence.find_by_source_document(
        register_b,
        source_document,
    ) == (movement_b,)


def test_find_by_source_document_returns_empty_tuple_when_nothing_matches() -> None:
    persistence = InMemoryRegisterFactPersistence()

    assert (
        persistence.find_by_source_document(
            Identifier.new(),
            Identifier.new(),
        )
        == ()
    )


def test_remove_supports_batch_removal() -> None:
    persistence = InMemoryRegisterFactPersistence()

    register = Identifier.new()
    first = make_movement(register_identity=register)
    second = make_movement(register_identity=register)

    persistence.append([first, second])

    assert persistence.remove([first.identity, second.identity]) is None

    assert persistence.enumerate(register) == ()


def test_remove_does_not_partially_remove_when_identity_is_missing() -> None:
    persistence = InMemoryRegisterFactPersistence()

    register = Identifier.new()
    movement = make_movement(register_identity=register)
    missing_identity = Identifier.new()

    persistence.append([movement])

    with pytest.raises(PersistenceNotFoundError):
        persistence.remove([movement.identity, missing_identity])

    assert persistence.enumerate(register) == (movement,)


def test_remove_empty_batch_is_noop() -> None:
    persistence = InMemoryRegisterFactPersistence()

    assert persistence.remove([]) is None


def test_enumerate_is_scoped_by_register() -> None:
    persistence = InMemoryRegisterFactPersistence()

    register_a = Identifier.new()
    register_b = Identifier.new()

    movement_a = make_movement(register_identity=register_a)
    movement_b = make_movement(register_identity=register_b)

    persistence.append([movement_a, movement_b])

    assert persistence.enumerate(register_a) == (movement_a,)
    assert persistence.enumerate(register_b) == (movement_b,)


def test_enumerate_is_deterministic() -> None:
    persistence = InMemoryRegisterFactPersistence()

    register = Identifier.new()

    first = make_movement(register_identity=register)
    second = make_movement(register_identity=register)

    persistence.append([second, first])

    expected = tuple(
        sorted(
            (first, second),
            key=lambda movement: str(movement.identity),
        )
    )

    assert persistence.enumerate(register) == expected
    assert persistence.enumerate(register) == expected


def test_persisted_movement_fields_remain_unchanged() -> None:
    persistence = InMemoryRegisterFactPersistence()

    movement = make_movement(
        movement_type=MovementType.EXPENSE,
        product="product-42",
        warehouse="warehouse-7",
        quantity="12.50",
    )

    persistence.append([movement])

    restored = persistence.enumerate(movement.register_identity)[0]

    assert restored.identity == movement.identity
    assert restored.source_document_identity == movement.source_document_identity
    assert restored.register_identity == movement.register_identity
    assert restored.movement_type == movement.movement_type
    assert restored.dimensions == movement.dimensions
    assert restored.resources == movement.resources
    assert restored.attributes == movement.attributes
    assert restored.accounting_time == movement.accounting_time
