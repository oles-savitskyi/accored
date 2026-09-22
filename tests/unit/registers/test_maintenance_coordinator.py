from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import (
    PersistenceFailure,
    PersistenceIndeterminateError,
)
from accore.platform.registers import (
    DefaultTotalsEngine,
    DefaultTotalsMaintenanceCoordinator,
    MaintenanceOperation,
    MaintenanceOutcome,
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
    TotalsConsistencyState,
    TotalsDefinition,
    TotalsLifecycleState,
    TotalsMaintenanceState,
)
from accore.platform.registers.totals import TotalsError


def make_movement(
    *,
    register: Identifier,
    identity: Identifier | None = None,
    product: str = "product-1",
    warehouse: str = "warehouse-1",
    quantity: str = "10",
    movement_type: MovementType = MovementType.INCOME,
) -> Movement:
    return Movement(
        identity=identity or Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register,
        movement_type=movement_type,
        dimensions=MovementDimensions.from_mapping(
            {
                "product": product,
                "warehouse": warehouse,
            }
        ),
        resources=MovementResources.from_mapping(
            {
                "quantity": Decimal(quantity),
            }
        ),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=datetime(2026, 9, 19, tzinfo=UTC),
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


class InMemoryRegisterFactPersistence:
    def __init__(
        self,
        movements: tuple[Movement, ...] = (),
    ) -> None:
        self._movements = {movement.identity: movement for movement in movements}

    def append(self, movements: tuple[Movement, ...]) -> None:
        self._movements.update({movement.identity: movement for movement in movements})

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            movement
            for movement in self._movements.values()
            if movement.register_identity == register_identity
            and movement.source_document_identity == source_document_identity
        )

    def remove(
        self,
        movement_identities: tuple[Identifier, ...],
    ) -> None:
        for identity in movement_identities:
            self._movements.pop(identity, None)

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        return tuple(
            movement
            for movement in self._movements.values()
            if movement.register_identity == register_identity
        )


def make_coordinator(
    register: Identifier,
    persistence: InMemoryRegisterFactPersistence | None = None,
) -> tuple[
    DefaultTotalsMaintenanceCoordinator,
    DefaultTotalsEngine,
    InMemoryRegisterFactPersistence,
]:
    persistence = persistence or InMemoryRegisterFactPersistence()
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=persistence,
    )
    return coordinator, engine, persistence


def test_apply_is_idempotent() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    coordinator, engine, _ = make_coordinator(register)

    first = coordinator.apply(movement)
    second = coordinator.apply(movement)

    assert first.outcome is MaintenanceOutcome.SUCCESS
    assert second.outcome is MaintenanceOutcome.SUCCESS
    assert first.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert first.state.consistency is TotalsConsistencyState.VALID

    assert engine.get(
        register,
        make_definition(register).key_for(movement),
    ) == Decimal(10)


def test_remove_is_idempotent() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    coordinator, engine, _ = make_coordinator(register)

    coordinator.apply(movement)

    first = coordinator.remove(movement)
    second = coordinator.remove(movement)

    assert first.outcome is MaintenanceOutcome.SUCCESS
    assert second.outcome is MaintenanceOutcome.SUCCESS

    assert engine.get(
        register,
        make_definition(register).key_for(movement),
    ) == Decimal(0)


def test_apply_and_remove_are_symmetric() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    coordinator, engine, _ = make_coordinator(register)
    key = make_definition(register).key_for(movement)

    coordinator.apply(movement)
    assert engine.get(register, key) == Decimal(10)

    coordinator.remove(movement)
    assert engine.get(register, key) == Decimal(0)


def test_rebuild_uses_authoritative_movement_facts() -> None:
    register = Identifier.new()
    first = make_movement(
        register=register,
        quantity="10",
    )
    second = make_movement(
        register=register,
        quantity="7",
        product="product-2",
    )

    persistence = InMemoryRegisterFactPersistence((first, second))
    coordinator, engine, _ = make_coordinator(
        register,
        persistence,
    )

    result = coordinator.rebuild(register)

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert result.state.consistency is TotalsConsistencyState.VALID

    definition = make_definition(register)

    assert engine.get(register, definition.key_for(first)) == Decimal(10)
    assert engine.get(register, definition.key_for(second)) == Decimal(7)


def test_rebuild_is_idempotent() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    persistence = InMemoryRegisterFactPersistence((movement,))
    coordinator, engine, _ = make_coordinator(
        register,
        persistence,
    )

    first = coordinator.rebuild(register)
    second = coordinator.rebuild(register)

    assert first.outcome is MaintenanceOutcome.SUCCESS
    assert second.outcome is MaintenanceOutcome.SUCCESS

    assert engine.get(
        register,
        make_definition(register).key_for(movement),
    ) == Decimal(10)


def test_rebuild_replaces_previous_derived_state() -> None:
    register = Identifier.new()
    first = make_movement(register=register, quantity="10")
    second = make_movement(
        register=register,
        quantity="5",
        product="product-2",
    )

    persistence = InMemoryRegisterFactPersistence((first,))
    coordinator, engine, _ = make_coordinator(
        register,
        persistence,
    )

    coordinator.rebuild(register)

    persistence.remove((first.identity,))
    persistence.append((second,))

    result = coordinator.rebuild(register)

    assert result.outcome is MaintenanceOutcome.SUCCESS

    definition = make_definition(register)

    assert engine.get(register, definition.key_for(first)) == Decimal(0)
    assert engine.get(register, definition.key_for(second)) == Decimal(5)


def test_recover_rebuilds_from_authoritative_facts() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    persistence = InMemoryRegisterFactPersistence((movement,))
    coordinator, engine, _ = make_coordinator(
        register,
        persistence,
    )

    result = coordinator.recover(register)

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert result.state.consistency is TotalsConsistencyState.VALID

    assert engine.get(
        register,
        make_definition(register).key_for(movement),
    ) == Decimal(10)


def test_rebuild_failure_requires_recovery() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)

    class FailingPersistence(InMemoryRegisterFactPersistence):
        def enumerate(
            self,
            register_identity: Identifier,
        ) -> tuple[Movement, ...]:
            raise PersistenceFailure("rebuild failed")

    coordinator, _, _ = make_coordinator(
        register,
        FailingPersistence((movement,)),
    )

    result = coordinator.rebuild(register)

    assert result.outcome is MaintenanceOutcome.FAILURE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_rebuild_indeterminate_persistence_outcome_is_indeterminate() -> None:
    register = Identifier.new()

    class IndeterminatePersistence(InMemoryRegisterFactPersistence):
        def enumerate(
            self,
            register_identity: Identifier,
        ) -> tuple[Movement, ...]:
            raise PersistenceIndeterminateError("outcome unknown")

    coordinator, _, _ = make_coordinator(
        register,
        IndeterminatePersistence(),
    )

    result = coordinator.rebuild(register)

    assert result.outcome is MaintenanceOutcome.INDETERMINATE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_failed_totals_apply_does_not_publish_partial_state() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)

    class FailingEngine(DefaultTotalsEngine):
        def apply(self, movement: Movement) -> Decimal:
            raise ValueError("unexpected failure")

    engine = FailingEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=InMemoryRegisterFactPersistence(),
    )

    result = coordinator.apply(movement)

    assert result.outcome is MaintenanceOutcome.INDETERMINATE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_registers_are_maintained_independently() -> None:
    first_register = Identifier.new()
    second_register = Identifier.new()

    first = make_movement(register=first_register, quantity="10")
    second = make_movement(register=second_register, quantity="20")

    persistence = InMemoryRegisterFactPersistence((first, second))

    first_engine = DefaultTotalsEngine((make_definition(first_register),))
    second_engine = DefaultTotalsEngine((make_definition(second_register),))

    first_coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=first_engine,
        persistence=persistence,
    )
    second_coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=second_engine,
        persistence=persistence,
    )

    first_coordinator.rebuild(first_register)
    second_coordinator.rebuild(second_register)

    assert first_engine.get(
        first_register,
        make_definition(first_register).key_for(first),
    ) == Decimal(10)

    assert second_engine.get(
        second_register,
        make_definition(second_register).key_for(second),
    ) == Decimal(20)


def test_apply_totals_failure_requires_recovery() -> None:
    register = Identifier.new()

    class FailingEngine(DefaultTotalsEngine):
        def apply(self, movement: Movement) -> Decimal:
            raise TotalsError("totals application failed")

    persistence = InMemoryRegisterFactPersistence()
    engine = FailingEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=persistence,
    )
    movement = make_movement(register=register)

    result = coordinator.apply(movement)

    assert result.operation is MaintenanceOperation.APPLY
    assert result.outcome is MaintenanceOutcome.FAILURE
    assert result.state == TotalsMaintenanceState(
        lifecycle=TotalsLifecycleState.ACTIVE,
        consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
    )


def test_remove_totals_failure_requires_recovery() -> None:
    register = Identifier.new()

    class FailingEngine(DefaultTotalsEngine):
        def remove(self, movement: Movement) -> Decimal:
            raise TotalsError("totals removal failed")

    persistence = InMemoryRegisterFactPersistence()
    engine = FailingEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=persistence,
    )
    movement = make_movement(register=register)

    applied = coordinator.apply(movement)
    assert applied.outcome is MaintenanceOutcome.SUCCESS

    result = coordinator.remove(movement)

    assert result.operation is MaintenanceOperation.REMOVE
    assert result.outcome is MaintenanceOutcome.FAILURE
    assert result.state == TotalsMaintenanceState(
        lifecycle=TotalsLifecycleState.ACTIVE,
        consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
    )
