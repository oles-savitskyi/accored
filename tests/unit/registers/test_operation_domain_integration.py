from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from threading import Event, RLock, Thread
from time import sleep

import pytest

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    BalanceQuery,
    DefaultBalanceQueryService,
    DefaultMovementQueryService,
    DefaultTotalsEngine,
    DefaultTotalsMaintenanceCoordinator,
    MaintenanceOperation,
    MaintenanceOutcome,
    MaintenanceResult,
    Movement,
    MovementAttributes,
    MovementDimensionFilter,
    MovementDimensions,
    MovementQuery,
    MovementQueryPeriod,
    MovementResources,
    MovementType,
    RegisterMutationMaintenanceError,
    RegisterMutationOrchestrator,
    RegisterOperationDomain,
    RegisterOperationDomainRegistry,
    TotalsAggregationError,
    TotalsConsistencyState,
    TotalsDefinition,
    TotalsLifecycleState,
    TotalsMaintenanceAdmissionError,
)
from accore.platform.registers.validation import MovementSetLike


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


@pytest.mark.parametrize(
    ("first_name", "second_name"),
    [
        ("mutation", "mutation"),
        ("mutation", "rebuild"),
        ("mutation", "recovery"),
        ("rebuild", "rebuild"),
        ("rebuild", "recovery"),
        ("recovery", "recovery"),
    ],
)
def test_same_register_operations_are_serialized(
    first_name: str,
    second_name: str,
) -> None:
    domain = RegisterOperationDomain(Identifier.new())
    first_entered = Event()
    second_started = Event()
    second_entered = Event()
    release_first = Event()

    def first_operation() -> None:
        first_entered.set()
        assert not second_entered.wait(0.05)
        release_first.wait(1)

    def second_operation() -> None:
        second_started.set()

    first = Thread(target=lambda: domain.execute(first_operation))
    first.start()
    assert first_entered.wait(1), f"{first_name} did not enter the Domain"

    def run_second() -> None:
        second_started.set()
        domain.execute(second_operation)
        second_entered.set()

    second = Thread(target=run_second)
    second.start()
    assert second_started.wait(1), f"{second_name} did not attempt the Domain"
    sleep(0.05)
    assert not second_entered.is_set()

    release_first.set()
    first.join(timeout=1)
    second.join(timeout=1)

    assert not first.is_alive()
    assert not second.is_alive()
    assert second_entered.is_set()


def test_different_registers_are_isolated() -> None:
    registry = RegisterOperationDomainRegistry()
    first_domain = registry.get(Identifier.new())
    second_domain = registry.get(Identifier.new())
    first_entered = Event()
    second_entered = Event()
    release_first = Event()

    def first_operation() -> None:
        first_entered.set()
        release_first.wait(1)

    first = Thread(target=lambda: first_domain.execute(first_operation))
    first.start()
    assert first_entered.wait(1)

    second = Thread(target=lambda: second_domain.execute(second_entered.set))
    second.start()
    assert second_entered.wait(1)

    release_first.set()
    first.join(timeout=1)
    second.join(timeout=1)

    assert not first.is_alive()
    assert not second.is_alive()


def test_shared_registry_resolves_same_domain_for_all_operation_classes() -> None:
    register = Identifier.new()
    registry = RegisterOperationDomainRegistry()

    mutation_domain = registry.get(register)
    rebuild_domain = registry.get(register)
    recovery_domain = registry.get(register)

    assert mutation_domain is rebuild_domain
    assert rebuild_domain is recovery_domain


def test_coordinator_does_not_own_register_operation_lock_map() -> None:
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=object(),
        persistence=object(),
    )

    assert not hasattr(coordinator, "_locks")
    assert not hasattr(coordinator, "_locks_guard")
    assert hasattr(coordinator, "_state_lock")


def test_maintenance_invocation_uses_shared_domain() -> None:
    register = Identifier.new()
    registry = RegisterOperationDomainRegistry()
    domain = registry.get(register)

    class Persistence:
        def enumerate(self, register_identity: Identifier) -> tuple[object, ...]:
            return ()

    class Engine:
        def rebuild(self, register_identity: Identifier, movements: tuple[object, ...]) -> None:
            assert register_identity == register
            assert movements == ()

    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=Engine(),
        persistence=Persistence(),
    )

    result = domain.execute(lambda: coordinator.rebuild(register))
    recovery = domain.execute(lambda: coordinator.recover(register))

    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert recovery.outcome is MaintenanceOutcome.SUCCESS


def test_mutation_state_changes_execute_inside_operation_domain() -> None:
    register = Identifier.new()
    movement = Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register,
        movement_type=MovementType.INCOME,
        dimensions=MovementDimensions.from_mapping({"product": "product-1"}),
        resources=MovementResources.from_mapping({"quantity": Decimal(1)}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=datetime(2026, 9, 19, tzinfo=UTC),
    )

    class RecordingDomain:
        active = False

        def execute(self, operation):
            assert not self.active
            self.active = True
            try:
                return operation()
            finally:
                self.active = False

    class RecordingRegistry:
        def __init__(self, domain: RecordingDomain) -> None:
            self.domain = domain

        def get(self, register_identity: Identifier) -> RecordingDomain:
            assert register_identity == register
            return self.domain

    class Persistence:
        def __init__(self, domain: RecordingDomain) -> None:
            self.domain = domain
            self.movements: dict[Identifier, Movement] = {}

        def append(self, movements: tuple[Movement, ...]) -> None:
            assert self.domain.active
            self.movements.update({movement.identity: movement for movement in movements})

        def remove(self, movement_identities: tuple[Identifier, ...]) -> None:
            assert self.domain.active
            for identity in movement_identities:
                self.movements.pop(identity, None)

    domain = RecordingDomain()
    persistence = Persistence(domain)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            assert not domain.active

    class SuccessfulTotals:
        def ensure_mutation_admitted(self, register_identity: Identifier) -> None:
            assert domain.active

        def apply(self, movement: Movement):
            assert domain.active
            from accore.platform.registers import (
                MaintenanceOperation,
                MaintenanceOutcome,
                MaintenanceResult,
                TotalsConsistencyState,
                TotalsLifecycleState,
                TotalsMaintenanceState,
            )

            return MaintenanceResult(
                operation=MaintenanceOperation.APPLY,
                outcome=MaintenanceOutcome.SUCCESS,
                state=TotalsMaintenanceState(
                    lifecycle=TotalsLifecycleState.ACTIVE,
                    consistency=TotalsConsistencyState.VALID,
                ),
            )

        def remove(self, movement: Movement):
            raise AssertionError("remove must not be called")

        def rebuild(self, register_identity: Identifier):
            raise AssertionError("rebuild must not be called")

        def recover(self, register_identity: Identifier):
            raise AssertionError("recover must not be called")

        def state(self, register_identity: Identifier):
            raise AssertionError("state must not be called")

    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=SuccessfulTotals(),
        domains=RecordingRegistry(domain),
        validator=Validator(),
    )

    orchestrator.establish((movement,))

    assert persistence.movements[movement.identity] == movement


def test_same_register_maintenance_operations_are_serialized_by_operation_domain() -> None:
    register = Identifier.new()
    definition = make_definition(register)

    class TrackingEngine(DefaultTotalsEngine):
        def __init__(self) -> None:
            super().__init__((definition,))
            self.active_calls = 0
            self.maximum_active_calls = 0
            self._tracking_lock = RLock()

        def apply(self, movement: Movement) -> Decimal:
            with self._tracking_lock:
                self.active_calls += 1
                self.maximum_active_calls = max(
                    self.maximum_active_calls,
                    self.active_calls,
                )

            try:
                sleep(0.02)
                return super().apply(movement)
            finally:
                with self._tracking_lock:
                    self.active_calls -= 1

    persistence = InMemoryRegisterFactPersistence()
    engine = TrackingEngine()
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=persistence,
    )
    domains = RegisterOperationDomainRegistry()

    domain = domains.get(register)

    first_movement = make_movement(register=register)
    second_movement = make_movement(register=register)

    results: list[MaintenanceResult] = []

    def apply_movement(movement: Movement) -> None:
        result = domain.execute(lambda: coordinator.apply(movement))
        results.append(result)

    first = Thread(
        target=apply_movement,
        args=(first_movement,),
    )
    second = Thread(
        target=apply_movement,
        args=(second_movement,),
    )

    first.start()
    second.start()

    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert len(results) == 2
    assert all(result.outcome is MaintenanceOutcome.SUCCESS for result in results)
    assert engine.maximum_active_calls == 1


def test_bootstrap_blocks_mutation_until_rebuild_completes() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    persistence = InMemoryRegisterFactPersistence((movement,))
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=persistence,
    )

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=RegisterOperationDomainRegistry(),
        validator=Validator(),
    )

    new_movement = make_movement(register=register, quantity="5")

    with pytest.raises(TotalsMaintenanceAdmissionError):
        orchestrator.establish((new_movement,))

    assert new_movement.identity not in {
        persisted.identity for persisted in persistence.enumerate(register)
    }

    domain = orchestrator._domains.get(register)
    result = domain.execute(lambda: coordinator.rebuild(register))

    assert result.outcome is MaintenanceOutcome.SUCCESS
    orchestrator.establish((new_movement,))

    definition = make_definition(register)
    persisted = persistence.enumerate(register)
    assert {item.identity for item in persisted} == {
        movement.identity,
        new_movement.identity,
    }
    assert engine.get(register, definition.key_for(movement)) == Decimal(15)
    assert engine.get(register, definition.key_for(new_movement)) == Decimal(15)


def test_rebuild_serializes_mutation_and_prevents_stale_totals() -> None:
    register = Identifier.new()
    first = make_movement(register=register, quantity="10")
    second = make_movement(register=register, quantity="5")

    class BlockingPersistence(InMemoryRegisterFactPersistence):
        def __init__(self, movements: tuple[Movement, ...]) -> None:
            super().__init__(movements)
            self.enumerate_started = Event()
            self.release_enumerate = Event()
            self.block_enumerate = False

        def enumerate(self, register_identity: Identifier) -> tuple[Movement, ...]:
            movements = super().enumerate(register_identity)
            if self.block_enumerate:
                self.enumerate_started.set()
                assert self.release_enumerate.wait(1)
            return movements

    persistence = BlockingPersistence((first,))
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=engine,
        persistence=persistence,
    )
    registry = RegisterOperationDomainRegistry()
    domain = registry.get(register)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=registry,
        validator=Validator(),
    )

    bootstrap_result = domain.execute(lambda: coordinator.rebuild(register))
    assert bootstrap_result.outcome is MaintenanceOutcome.SUCCESS
    persistence.block_enumerate = True

    rebuild_result: list[MaintenanceResult] = []
    mutation_completed = Event()

    def rebuild() -> None:
        rebuild_result.append(domain.execute(lambda: coordinator.rebuild(register)))

    def mutate() -> None:
        orchestrator.establish((second,))
        mutation_completed.set()

    rebuild_thread = Thread(target=rebuild)
    rebuild_thread.start()
    assert persistence.enumerate_started.wait(1)

    mutation_thread = Thread(target=mutate)
    mutation_thread.start()
    sleep(0.05)

    assert not mutation_completed.is_set()
    assert second.identity not in persistence._movements

    persistence.release_enumerate.set()
    rebuild_thread.join(timeout=1)
    mutation_thread.join(timeout=1)

    persisted = persistence.enumerate(register)
    assert {item.identity for item in persisted} == {
        first.identity,
        second.identity,
    }
    assert not rebuild_thread.is_alive()
    assert not mutation_thread.is_alive()
    assert len(rebuild_result) == 1
    assert rebuild_result[0].outcome is MaintenanceOutcome.SUCCESS
    assert mutation_completed.is_set()

    definition = make_definition(register)
    assert engine.get(register, definition.key_for(first)) == Decimal(15)
    assert engine.get(register, definition.key_for(second)) == Decimal(15)


def test_movement_query_composes_with_persisted_mutation_facts() -> None:
    register = "goods"
    persistence = InMemoryRegisterFactPersistence()
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domains = RegisterOperationDomainRegistry()
    domain = domains.get(register)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    validator = Validator()
    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=domains,
        validator=validator,
    )

    domain.execute(lambda: coordinator.rebuild(register))

    movement = Movement(
        identity="movement-1",
        source_document_identity="movement-1",
        register_identity=register,
        movement_type=MovementType.INCOME,
        accounting_time=datetime(2026, 9, 19, 12, tzinfo=UTC),
        dimensions=MovementDimensions(
            values={
                "product": "product-1",
                "warehouse": "warehouse-1",
            }
        ),
        resources=MovementResources(values={"quantity": Decimal(10)}),
        attributes=MovementAttributes.from_mapping({}),
    )

    orchestrator.establish((movement,))

    query_service = DefaultMovementQueryService(persistence)
    query = MovementQuery(
        register_identity=register,
        period=MovementQueryPeriod(
            start=datetime(2026, 9, 18, tzinfo=UTC),
            end=datetime(2026, 9, 20, tzinfo=UTC),
        ),
        dimensions=MovementDimensionFilter(
            values={
                "product": "product-1",
                "warehouse": "warehouse-1",
            }
        ),
    )

    state_before = coordinator.state(register)
    result = query_service.query(query)

    assert result == (movement,)
    assert coordinator.state(register) == state_before


def test_balance_query_composes_with_published_totals_after_mutation() -> None:
    register = "goods"
    persistence = InMemoryRegisterFactPersistence()
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domains = RegisterOperationDomainRegistry()
    domain = domains.get(register)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    validator = Validator()
    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=domains,
        validator=validator,
    )

    domain.execute(lambda: coordinator.rebuild(register))

    movement = Movement(
        identity="movement-1",
        source_document_identity="movement-1",
        register_identity=register,
        movement_type=MovementType.INCOME,
        accounting_time=datetime(2026, 9, 19, 12, tzinfo=UTC),
        dimensions=MovementDimensions(
            values={
                "product": "product-1",
                "warehouse": "warehouse-1",
            }
        ),
        resources=MovementResources(values={"quantity": Decimal(10)}),
        attributes=MovementAttributes.from_mapping({}),
    )

    orchestrator.establish((movement,))

    state_before = coordinator.state(register)

    query_service = DefaultBalanceQueryService(engine)
    definition = make_definition(register)
    aggregation_scope = definition.key_for(movement)

    query = BalanceQuery(
        register_identity=register,
        aggregation_scope=aggregation_scope,
    )

    result = query_service.query(query)

    assert result.register_identity == register
    assert result.aggregation_scope == aggregation_scope
    assert result.value == Decimal(10)

    # Read-side balance query must not mutate maintenance state.
    assert coordinator.state(register) == state_before


def test_recovery_serializes_same_register_mutation() -> None:
    register = Identifier.new()
    persistence, engine, _, domains, domain, _ = make_integrated_stack(register)
    initial = make_movement(register=register)

    entered = Event()
    release = Event()
    mutation_completed = Event()

    class BlockingPersistence(InMemoryRegisterFactPersistence):
        def enumerate(self, register_identity: Identifier) -> tuple[Movement, ...]:
            movements = super().enumerate(register_identity)
            entered.set()
            assert release.wait(1)
            return movements

    persistence = BlockingPersistence((initial,))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=domains,
        validator=Validator(),
    )

    recovery_thread = Thread(target=lambda: domain.execute(lambda: coordinator.recover(register)))
    recovery_thread.start()
    assert entered.wait(1)

    replacement = make_movement(register=register, quantity="5")

    def mutate() -> None:
        orchestrator.establish((replacement,))
        mutation_completed.set()

    mutation_thread = Thread(target=mutate)
    mutation_thread.start()
    assert not mutation_completed.wait(0.05)
    assert replacement.identity not in persistence._movements

    release.set()
    recovery_thread.join(timeout=1)
    mutation_thread.join(timeout=1)

    assert not recovery_thread.is_alive()
    assert not mutation_thread.is_alive()
    assert mutation_completed.is_set()


def test_same_register_rebuild_operations_are_serialized() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    persistence = InMemoryRegisterFactPersistence((movement,))
    domain = RegisterOperationDomain(register)
    entered = Event()
    release = Event()
    results: list[MaintenanceResult] = []

    class BlockingEngine(DefaultTotalsEngine):
        def rebuild(self, register_identity: Identifier, movements: tuple[Movement, ...]) -> None:
            entered.set()
            assert release.wait(1)
            super().rebuild(register_identity, movements)

    engine = BlockingEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)

    first = Thread(
        target=lambda: results.append(domain.execute(lambda: coordinator.rebuild(register)))
    )
    second = Thread(
        target=lambda: results.append(domain.execute(lambda: coordinator.rebuild(register)))
    )
    first.start()
    assert entered.wait(1)
    second.start()
    sleep(0.05)
    assert second.is_alive()

    release.set()
    first.join(timeout=1)
    second.join(timeout=1)

    assert not first.is_alive()
    assert not second.is_alive()
    assert len(results) == 2
    assert all(result.outcome is MaintenanceOutcome.SUCCESS for result in results)
    assert engine.get(register, make_definition(register).key_for(movement)) == Decimal(10)


def make_integrated_stack(register: Identifier):
    persistence = InMemoryRegisterFactPersistence()
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domains = RegisterOperationDomainRegistry()
    domain = domains.get(register)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=domains,
        validator=Validator(),
    )
    return persistence, engine, coordinator, domains, domain, orchestrator


def test_recovery_delegates_to_rebuild_and_restores_mutation_admission() -> None:
    register = Identifier.new()
    movement = make_movement(register=register, quantity="10")
    persistence, engine, coordinator, _, domain, orchestrator = make_integrated_stack(register)
    persistence.append((movement,))

    result = domain.execute(lambda: coordinator.recover(register))

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert result.state.consistency is TotalsConsistencyState.VALID
    assert engine.get(register, make_definition(register).key_for(movement)) == Decimal(10)

    replacement = make_movement(register=register, quantity="5")
    orchestrator.establish((replacement,))
    assert replacement in persistence.enumerate(register)


def test_rebuild_replaces_stale_derived_totals_with_authoritative_facts() -> None:
    register = Identifier.new()
    first = make_movement(register=register, quantity="10")
    second = make_movement(register=register, quantity="5")
    persistence, engine, coordinator, _, domain, _ = make_integrated_stack(register)
    persistence.append((first, second))

    engine.apply(make_movement(register=register, identity=first.identity, quantity="99"))
    engine.apply(make_movement(register=register, identity=second.identity, quantity="77"))

    result = domain.execute(lambda: coordinator.rebuild(register))
    definition = make_definition(register)

    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert engine.get(register, definition.key_for(first)) == Decimal(15)
    assert engine.get(register, definition.key_for(second)) == Decimal(15)


def test_repeated_rebuild_does_not_double_count() -> None:
    register = Identifier.new()
    movement = make_movement(register=register, quantity="10")
    persistence, engine, coordinator, _, domain, _ = make_integrated_stack(register)
    persistence.append((movement,))

    first = domain.execute(lambda: coordinator.rebuild(register))
    second = domain.execute(lambda: coordinator.rebuild(register))

    assert first.outcome is MaintenanceOutcome.SUCCESS
    assert second.outcome is MaintenanceOutcome.SUCCESS
    assert engine.get(register, make_definition(register).key_for(movement)) == Decimal(10)


def test_failure_from_persistence_marks_rebuild_failed_and_requires_recovery() -> None:
    register = Identifier.new()

    class FailingPersistence(InMemoryRegisterFactPersistence):
        def enumerate(self, register_identity: Identifier) -> tuple[Movement, ...]:
            from accore.platform.persistence.errors import PersistenceFailure

            raise PersistenceFailure("read failed")

    persistence = FailingPersistence()
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domain = RegisterOperationDomain(register)

    result = domain.execute(lambda: coordinator.rebuild(register))

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.FAILURE
    assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED
    assert coordinator.state(register) == result.state


def test_totals_rebuild_failure_is_reported_as_failure_and_requires_recovery() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    persistence = InMemoryRegisterFactPersistence((movement,))

    class FailingEngine(DefaultTotalsEngine):
        def rebuild(self, register_identity: Identifier, movements: tuple[Movement, ...]) -> None:
            raise TotalsAggregationError("rebuild failed")

    engine = FailingEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domain = RegisterOperationDomain(register)

    result = domain.execute(lambda: coordinator.rebuild(register))

    assert result.outcome is MaintenanceOutcome.FAILURE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_unexpected_rebuild_failure_marks_state_indeterminate_and_requires_recovery() -> None:
    register = Identifier.new()

    class FailingPersistence(InMemoryRegisterFactPersistence):
        def enumerate(self, register_identity: Identifier) -> tuple[Movement, ...]:
            raise RuntimeError("unexpected read failure")

    persistence = FailingPersistence()
    engine = DefaultTotalsEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domain = RegisterOperationDomain(register)

    result = domain.execute(lambda: coordinator.rebuild(register))

    assert result.outcome is MaintenanceOutcome.INDETERMINATE
    assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_mutation_totals_failure_is_exposed_as_register_mutation_maintenance_error() -> None:
    register = Identifier.new()
    movement = make_movement(register=register)
    persistence = InMemoryRegisterFactPersistence()

    class FailingEngine(DefaultTotalsEngine):
        def apply(self, movement: Movement) -> Decimal:
            raise RuntimeError("unexpected totals failure")

    engine = FailingEngine((make_definition(register),))
    coordinator = DefaultTotalsMaintenanceCoordinator(engine, persistence)
    domains = RegisterOperationDomainRegistry()
    domain = domains.get(register)

    class Validator:
        def validate(self, movement_set: MovementSetLike) -> None:
            return None

    domain.execute(lambda: coordinator.rebuild(register))
    orchestrator = RegisterMutationOrchestrator(
        persistence=persistence,
        totals=coordinator,
        domains=domains,
        validator=Validator(),
    )

    with pytest.raises(RegisterMutationMaintenanceError) as error:
        orchestrator.establish((movement,))

    assert error.value.result.outcome is MaintenanceOutcome.INDETERMINATE
    assert persistence.enumerate(register) == (movement,)


def test_remove_updates_persistence_and_balance_without_mutating_read_side_state() -> None:
    register = Identifier.new()
    persistence, engine, coordinator, _, domain, orchestrator = make_integrated_stack(register)
    movement = make_movement(register=register, quantity="10")
    domain.execute(lambda: coordinator.rebuild(register))

    orchestrator.establish((movement,))
    state_before_remove = coordinator.state(register)
    orchestrator.remove((movement,))

    definition = make_definition(register)
    balance_service = DefaultBalanceQueryService(engine)
    balance = balance_service.query(
        BalanceQuery(
            register_identity=register,
            aggregation_scope=definition.key_for(movement),
        )
    )

    assert persistence.enumerate(register) == ()
    assert balance.value == Decimal(0)
    assert coordinator.state(register) == state_before_remove


def test_complete_register_capability_flow_preserves_authoritative_and_derived_views() -> None:
    register = Identifier.new()
    (
        persistence,
        engine,
        coordinator,
        domains,
        domain,
        orchestrator,
    ) = make_integrated_stack(register)
    movement = make_movement(register=register, quantity="10")
    definition = make_definition(register)

    bootstrap = domain.execute(lambda: coordinator.rebuild(register))
    assert bootstrap.outcome is MaintenanceOutcome.SUCCESS

    orchestrator.establish((movement,))

    movement_query_service = DefaultMovementQueryService(persistence)
    movement_query = MovementQuery(
        register_identity=register,
        period=MovementQueryPeriod(
            start=datetime(2026, 9, 18, tzinfo=UTC),
            end=datetime(2026, 9, 20, tzinfo=UTC),
        ),
        dimensions=MovementDimensionFilter(values={}),
    )
    assert movement_query_service.query(movement_query) == (movement,)

    balance_query_service = DefaultBalanceQueryService(engine)
    balance_query = BalanceQuery(
        register_identity=register,
        aggregation_scope=definition.key_for(movement),
    )
    assert balance_query_service.query(balance_query).value == Decimal(10)

    orchestrator.remove((movement,))
    assert movement_query_service.query(movement_query) == ()
    assert balance_query_service.query(balance_query).value == Decimal(0)

    rebuild = domain.execute(lambda: coordinator.rebuild(register))
    assert rebuild.outcome is MaintenanceOutcome.SUCCESS
    assert balance_query_service.query(balance_query).value == Decimal(0)
    assert coordinator.state(register).consistency is TotalsConsistencyState.VALID
    assert domains.get(register) is domain
