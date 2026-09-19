from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.persistence import RegisterFactPersistence
from accore.platform.registers import (
    DefaultMovementQueryService,
    Movement,
    MovementAttributes,
    MovementDimensionFilter,
    MovementDimensions,
    MovementQuery,
    MovementQueryPeriod,
    MovementQueryValidationError,
    MovementResources,
    MovementType,
)


class InMemoryRegisterFactPersistence:
    def __init__(self, movements: tuple[Movement, ...] = ()) -> None:
        self.movements = list(movements)

    def append(self, movements: tuple[Movement, ...]) -> None:
        self.movements.extend(movements)

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            movement
            for movement in self.movements
            if movement.register_identity == register_identity
            and movement.source_document_identity == source_document_identity
        )

    def remove(self, movement_identities: tuple[Identifier, ...]) -> None:
        identities = set(movement_identities)
        self.movements = [
            movement for movement in self.movements if movement.identity not in identities
        ]

    def enumerate(self, register_identity: Identifier) -> tuple[Movement, ...]:
        return tuple(
            movement
            for movement in self.movements
            if movement.register_identity == register_identity
        )


def make_movement(
    *,
    register_identity: Identifier,
    accounting_time: datetime | None,
    product: str = "P1",
    warehouse: str = "W1",
    movement_identity: Identifier | None = None,
) -> Movement:
    return Movement(
        identity=movement_identity or Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register_identity,
        movement_type=MovementType.INCOME,
        dimensions=MovementDimensions.from_mapping({"product": product, "warehouse": warehouse}),
        resources=MovementResources.from_mapping({"quantity": Decimal(1)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=accounting_time,
    )


def make_query(
    *,
    register_identity: Identifier,
    start: datetime,
    end: datetime,
    dimensions: dict[str, object] | None = None,
) -> MovementQuery:
    return MovementQuery(
        register_identity=register_identity,
        period=MovementQueryPeriod(start=start, end=end),
        dimensions=MovementDimensionFilter.from_mapping(dimensions or {}),
    )


def test_query_service_protocol_shape() -> None:
    assert hasattr(RegisterFactPersistence, "enumerate")


def test_period_requires_start_before_end() -> None:
    moment = datetime(2026, 1, 1, tzinfo=UTC)

    with pytest.raises(MovementQueryValidationError):
        MovementQueryPeriod(start=moment, end=moment)

    with pytest.raises(MovementQueryValidationError):
        MovementQueryPeriod(start=moment + timedelta(days=1), end=moment)


def test_period_requires_timezone_aware_boundaries() -> None:
    aware = datetime(2026, 1, 1, tzinfo=UTC)
    naive = datetime(2026, 1, 2)  # noqa: DTZ001

    with pytest.raises(MovementQueryValidationError):
        MovementQueryPeriod(start=naive, end=aware)

    with pytest.raises(MovementQueryValidationError):
        MovementQueryPeriod(start=aware, end=naive)


def test_dimension_filter_defensively_copies_mapping() -> None:
    source = {"product": "P1"}
    dimensions = MovementDimensionFilter.from_mapping(source)

    source["product"] = "P2"

    assert dimensions.values["product"] == "P1"
    with pytest.raises(TypeError):
        dimensions.values["product"] = "P3"  # type: ignore[index]


def test_empty_dimension_filter_matches_all_dimensions() -> None:
    register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    first = make_movement(register_identity=register, accounting_time=start)
    second = make_movement(register_identity=register, accounting_time=start + timedelta(days=1))

    service = DefaultMovementQueryService(InMemoryRegisterFactPersistence((second, first)))

    assert service.query(make_query(register_identity=register, start=start, end=end)) == (
        first,
        second,
    )


def test_query_applies_half_open_period_and_excludes_missing_accounting_time() -> None:
    register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    at_start = make_movement(register_identity=register, accounting_time=start)
    at_end = make_movement(register_identity=register, accounting_time=end)
    missing = make_movement(register_identity=register, accounting_time=None)
    before = make_movement(
        register_identity=register,
        accounting_time=start - timedelta(seconds=1),
    )

    service = DefaultMovementQueryService(
        InMemoryRegisterFactPersistence((before, missing, at_end, at_start))
    )

    assert service.query(make_query(register_identity=register, start=start, end=end)) == (
        at_start,
    )


def test_query_applies_partial_dimension_filter() -> None:
    register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    product_match = make_movement(
        register_identity=register,
        accounting_time=start,
        product="P1",
        warehouse="W1",
    )
    other_warehouse = make_movement(
        register_identity=register,
        accounting_time=start,
        product="P1",
        warehouse="W2",
    )
    other_product = make_movement(
        register_identity=register,
        accounting_time=start,
        product="P2",
        warehouse="W1",
    )

    service = DefaultMovementQueryService(
        InMemoryRegisterFactPersistence((other_product, other_warehouse, product_match))
    )

    result = service.query(
        make_query(
            register_identity=register,
            start=start,
            end=end,
            dimensions={"product": "P1"},
        )
    )

    expected = tuple(
        sorted(
            (product_match, other_warehouse),
            key=lambda movement: str(movement.identity),
        )
    )

    assert result == expected


def test_missing_requested_dimension_is_non_match() -> None:
    register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    movement = make_movement(register_identity=register, accounting_time=start)
    movement = Movement(
        identity=movement.identity,
        source_document_identity=movement.source_document_identity,
        register_identity=movement.register_identity,
        movement_type=movement.movement_type,
        dimensions=MovementDimensions.from_mapping({"warehouse": "W1"}),
        resources=movement.resources,
        attributes=movement.attributes,
        accounting_time=movement.accounting_time,
    )

    service = DefaultMovementQueryService(InMemoryRegisterFactPersistence((movement,)))

    assert (
        service.query(
            make_query(
                register_identity=register,
                start=start,
                end=end,
                dimensions={"product": "P1"},
            )
        )
        == ()
    )


def test_query_is_scoped_to_register() -> None:
    register = Identifier.new()
    other_register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    selected = make_movement(register_identity=register, accounting_time=start)
    other = make_movement(register_identity=other_register, accounting_time=start)

    service = DefaultMovementQueryService(InMemoryRegisterFactPersistence((other, selected)))

    assert service.query(make_query(register_identity=register, start=start, end=end)) == (
        selected,
    )


def test_query_order_is_deterministic_by_accounting_time_then_identity() -> None:
    register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    first_id = Identifier.new()
    second_id = Identifier.new()
    first = make_movement(
        register_identity=register,
        accounting_time=start,
        movement_identity=first_id,
    )
    second = make_movement(
        register_identity=register,
        accounting_time=start,
        movement_identity=second_id,
    )
    expected = tuple(sorted((first, second), key=lambda m: str(m.identity)))

    service = DefaultMovementQueryService(InMemoryRegisterFactPersistence((second, first)))

    assert service.query(make_query(register_identity=register, start=start, end=end)) == expected


def test_query_preserves_complete_movement() -> None:
    register = Identifier.new()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    movement = make_movement(register_identity=register, accounting_time=start)

    service = DefaultMovementQueryService(InMemoryRegisterFactPersistence((movement,)))

    result = service.query(make_query(register_identity=register, start=start, end=end))

    assert result == (movement,)
    assert result[0].identity == movement.identity
    assert result[0].source_document_identity == movement.source_document_identity
    assert result[0].register_identity == movement.register_identity
    assert result[0].movement_type is movement.movement_type
    assert result[0].dimensions == movement.dimensions
    assert result[0].resources == movement.resources
    assert result[0].attributes == movement.attributes
    assert result[0].accounting_time == movement.accounting_time
