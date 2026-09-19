from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import PersistenceError
from accore.platform.registers import (
    DefaultTotalsEngine,
    DefaultTotalsMaintenanceCoordinator,
    MaintenanceOperation,
    MaintenanceOutcome,
    MaintenanceResult,
    Movement,
    MovementAttributes,
    MovementDimensions,
    MovementResources,
    MovementType,
    RegisterMutationOrchestrator,
    TotalsConsistencyState,
    TotalsDefinition,
    TotalsLifecycleState,
    TotalsMaintenanceState,
)
from accore.platform.registers.operation_domain import RegisterOperationDomainRegistry


class InMemoryPersistence:
    def __init__(self, movements: tuple[Movement, ...] = ()) -> None:
        self.movements = {movement.identity: movement for movement in movements}
        self.append_calls = 0
        self.remove_calls = 0
        self.enumerate_calls = 0

    def append(self, movements: tuple[Movement, ...]) -> None:
        self.append_calls += 1
        self.movements.update({movement.identity: movement for movement in movements})

    def find_by_source_document(self, register_identity, source_document_identity):
        return tuple(
            movement
            for movement in self.movements.values()
            if movement.register_identity == register_identity
            and movement.source_document_identity == source_document_identity
        )

    def remove(self, movement_identities: tuple[Identifier, ...]) -> None:
        self.remove_calls += 1
        for identity in movement_identities:
            self.movements.pop(identity, None)

    def enumerate(self, register_identity: Identifier) -> tuple[Movement, ...]:
        self.enumerate_calls += 1
        return tuple(
            movement
            for movement in self.movements.values()
            if movement.register_identity == register_identity
        )


def make_movement(register: Identifier, quantity: str = "10") -> Movement:
    return Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register,
        movement_type=MovementType.INCOME,
        dimensions=MovementDimensions.from_mapping(
            {"product": "product-1", "warehouse": "warehouse-1"}
        ),
        resources=MovementResources.from_mapping({"quantity": Decimal(quantity)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=datetime(2026, 9, 19, tzinfo=UTC),
    )


def make_orchestrator(
    register: Identifier,
    persistence: InMemoryPersistence | None = None,
) -> tuple[RegisterMutationOrchestrator, InMemoryPersistence]:
    persistence = persistence or InMemoryPersistence()
    engine = DefaultTotalsEngine(
        (
            TotalsDefinition(
                register_identity=register,
                dimensions=("product", "warehouse"),
                resource_name="quantity",
                movement_type_signs={MovementType.INCOME: 1, MovementType.EXPENSE: -1},
            ),
        )
    )
    totals = DefaultTotalsMaintenanceCoordinator(engine=engine, persistence=persistence)
    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=totals,
        domains=RegisterOperationDomainRegistry(),
    )
    return orchestrator, persistence


def test_establish_persists_and_maintains_totals() -> None:
    register = Identifier.new()
    movement = make_movement(register)
    orchestrator, persistence = make_orchestrator(register)

    orchestrator.establish((movement,))

    assert persistence.movements[movement.identity] == movement


def test_establish_rejects_mixed_register_input_before_persistence() -> None:
    first = make_movement(Identifier.new())
    second = make_movement(Identifier.new())
    orchestrator, persistence = make_orchestrator(first.register_identity)

    with pytest.raises(ValueError):
        orchestrator.establish((first, second))

    assert persistence.append_calls == 0
    assert persistence.movements == {}


def test_empty_establish_is_noop() -> None:
    register = Identifier.new()
    orchestrator, persistence = make_orchestrator(register)

    orchestrator.establish(())

    assert persistence.append_calls == 0
    assert persistence.movements == {}


def test_rebuild_uses_authoritative_persistence_under_domain() -> None:
    register = Identifier.new()
    movement = make_movement(register)
    persistence = InMemoryPersistence((movement,))
    orchestrator, _ = make_orchestrator(register, persistence)

    result = orchestrator.rebuild(register)

    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert persistence.enumerate_calls == 1


def test_recover_uses_same_rebuild_path() -> None:
    register = Identifier.new()
    persistence = InMemoryPersistence((make_movement(register),))
    orchestrator, _ = make_orchestrator(register, persistence)

    result = orchestrator.recover(register)

    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert persistence.enumerate_calls == 1


def test_persistence_failure_prevents_totals_apply() -> None:
    register = Identifier.new()
    movement = make_movement(register)

    class FailingPersistence(InMemoryPersistence):
        def append(self, movements: tuple[Movement, ...]) -> None:
            raise PersistenceError("append failed")

    persistence = FailingPersistence()
    orchestrator, _ = make_orchestrator(register, persistence)

    with pytest.raises(PersistenceError):
        orchestrator.establish((movement,))

    assert persistence.movements == {}


def test_establish_persistence_success_totals_failure_leaves_persisted_movement() -> None:
    register = Identifier.new()
    movement = make_movement(register)

    class FailingTotals:
        def apply(self, movement: Movement) -> MaintenanceResult:
            return MaintenanceResult(
                operation=MaintenanceOperation.APPLY,
                outcome=MaintenanceOutcome.FAILURE,
                state=TotalsMaintenanceState(
                    lifecycle=TotalsLifecycleState.ACTIVE,
                    consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
                ),
            )

        def remove(self, movement: Movement) -> MaintenanceResult:
            raise AssertionError("remove must not be called")

        def rebuild(self, register_identity: Identifier) -> MaintenanceResult:
            raise AssertionError("rebuild must not be called")

        def recover(self, register_identity: Identifier) -> MaintenanceResult:
            raise AssertionError("recover must not be called")

    persistence = InMemoryPersistence()
    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=FailingTotals(),
        domains=RegisterOperationDomainRegistry(),
    )

    with pytest.raises(
        RuntimeError,
        match="Totals maintenance did not successfully apply",
    ):
        orchestrator.establish((movement,))

    assert persistence.movements[movement.identity] == movement


def test_establish_persistence_success_totals_indeterminate_leaves_persisted_movement() -> None:
    register = Identifier.new()
    movement = make_movement(register)

    class IndeterminateTotals:
        def apply(self, movement: Movement) -> MaintenanceResult:
            return MaintenanceResult(
                operation=MaintenanceOperation.APPLY,
                outcome=MaintenanceOutcome.INDETERMINATE,
                state=TotalsMaintenanceState(
                    lifecycle=TotalsLifecycleState.ACTIVE,
                    consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
                ),
            )

        def remove(self, movement: Movement) -> MaintenanceResult:
            raise AssertionError("remove must not be called")

        def rebuild(self, register_identity: Identifier) -> MaintenanceResult:
            raise AssertionError("rebuild must not be called")

        def recover(self, register_identity: Identifier) -> MaintenanceResult:
            raise AssertionError("recover must not be called")

    persistence = InMemoryPersistence()
    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=IndeterminateTotals(),
        domains=RegisterOperationDomainRegistry(),
    )

    with pytest.raises(
        RuntimeError,
        match="Totals maintenance did not successfully apply",
    ):
        orchestrator.establish((movement,))

    assert persistence.movements[movement.identity] == movement


def test_remove_deletes_persisted_movement_and_removes_totals() -> None:
    register = Identifier.new()
    movement = make_movement(register)
    orchestrator, persistence = make_orchestrator(register)

    orchestrator.establish((movement,))
    assert movement.identity in persistence.movements

    orchestrator.remove((movement,))

    assert movement.identity not in persistence.movements
    assert persistence.remove_calls == 1


def test_remove_is_idempotent_for_already_unapplied_movement() -> None:
    register = Identifier.new()
    movement = make_movement(register)
    orchestrator, persistence = make_orchestrator(register)

    orchestrator.remove((movement,))

    assert movement.identity not in persistence.movements
    assert persistence.remove_calls == 1

    orchestrator.remove((movement,))

    assert movement.identity not in persistence.movements
    assert persistence.remove_calls == 2


def test_remove_rejects_movements_from_different_registers() -> None:
    register_a = Identifier.new()
    register_b = Identifier.new()

    movement_a = make_movement(register_a)
    movement_b = make_movement(register_b)

    orchestrator, persistence = make_orchestrator(register_a)

    with pytest.raises(ValueError, match="one Register"):
        orchestrator.remove((movement_a, movement_b))

    assert persistence.remove_calls == 0
    assert persistence.movements == {}
