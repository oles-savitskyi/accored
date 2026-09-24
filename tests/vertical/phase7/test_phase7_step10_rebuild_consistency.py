from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.persistence.errors import PersistenceError, PersistenceIndeterminateError
from accore.platform.registers import (
    BalanceQuery,
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
    TotalsError,
    TotalsKey,
    TotalsLifecycleState,
    TotalsMaintenanceAdmissionError,
)
from standard.bootstrap import StandardConfigurationBootstrap
from standard.registers.inventory import (
    INVENTORY_PRODUCT_DIMENSION,
    INVENTORY_QUANTITY_RESOURCE,
    INVENTORY_REGISTER_ID,
    INVENTORY_WAREHOUSE_DIMENSION,
)
from tests.vertical.phase7.test_phase7_step9_vertical_slice import (
    InMemoryRegisterFactPersistence,
    make_state,
    post_goods_receipt,
)


def inventory_key(*, product: str, warehouse: str) -> TotalsKey:
    return TotalsKey.from_mapping(
        {
            INVENTORY_PRODUCT_DIMENSION: product,
            INVENTORY_WAREHOUSE_DIMENSION: warehouse,
        }
    )


def assert_active_valid(*, composition, register_identity: Identifier) -> None:
    state = composition.maintenance.state(register_identity)
    assert state.lifecycle is TotalsLifecycleState.ACTIVE
    assert state.consistency is TotalsConsistencyState.VALID


def expected_inventory_total(
    persistence: InMemoryRegisterFactPersistence,
    *,
    product: str,
    warehouse: str,
) -> Decimal:
    expected = Decimal(0)
    for movement in persistence.enumerate(INVENTORY_REGISTER_ID):
        if (
            movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION) == product
            and movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION) == warehouse
        ):
            quantity = movement.resources.get(INVENTORY_QUANTITY_RESOURCE)
            assert isinstance(quantity, Decimal)
            if movement.movement_type is MovementType.INCOME:
                expected += quantity
            elif movement.movement_type is MovementType.EXPENSE:
                expected -= quantity
    return expected


def inventory_snapshot(*, composition, keys: tuple[TotalsKey, ...]) -> tuple[Decimal, ...]:
    return tuple(composition.totals_engine.get(INVENTORY_REGISTER_ID, key) for key in keys)


def make_movement(
    *,
    register_identity: Identifier,
    movement_type: MovementType,
    product: str,
    warehouse: str,
    quantity: Decimal,
    accounting_time: datetime,
) -> Movement:
    return Movement(
        identity=Identifier.new(),
        source_document_identity=Identifier.new(),
        register_identity=register_identity,
        movement_type=movement_type,
        dimensions=MovementDimensions.from_mapping(
            {
                INVENTORY_PRODUCT_DIMENSION: product,
                INVENTORY_WAREHOUSE_DIMENSION: warehouse,
            }
        ),
        resources=MovementResources.from_mapping({INVENTORY_QUANTITY_RESOURCE: quantity}),
        attributes=MovementAttributes.from_mapping({}),
        accounting_time=accounting_time,
    )


def test_incremental_totals_equal_rebuilt_totals_and_balance() -> None:
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="10",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )
    post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="2.5",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )
    post_goods_receipt(
        product="P1",
        warehouse="W2",
        quantity="4",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )

    key_w1 = inventory_key(product="P1", warehouse="W1")
    key_w2 = inventory_key(product="P1", warehouse="W2")
    incremental = inventory_snapshot(
        composition=composition,
        keys=(key_w1, key_w2),
    )
    expected = (
        expected_inventory_total(persistence, product="P1", warehouse="W1"),
        expected_inventory_total(persistence, product="P1", warehouse="W2"),
    )

    result = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert result.state.consistency is TotalsConsistencyState.VALID
    assert inventory_snapshot(composition=composition, keys=(key_w1, key_w2)) == incremental
    assert inventory_snapshot(composition=composition, keys=(key_w1, key_w2)) == expected
    assert (
        composition.balance_query.query(
            BalanceQuery(
                register_identity=INVENTORY_REGISTER_ID,
                aggregation_scope=key_w1,
            )
        ).value
        == expected[0]
    )
    assert_active_valid(
        composition=composition,
        register_identity=INVENTORY_REGISTER_ID,
    )


def test_rebuild_is_idempotent_and_replaces_stale_derived_state() -> None:
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="10",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )

    valid_key = inventory_key(product="P1", warehouse="W1")
    stale_key = inventory_key(product="STALE", warehouse="W1")
    stale_movement = make_movement(
        register_identity=INVENTORY_REGISTER_ID,
        movement_type=MovementType.INCOME,
        product="STALE",
        warehouse="W1",
        quantity=Decimal(99),
        accounting_time=accounting_time,
    )

    facts_before = tuple(persistence.enumerate(INVENTORY_REGISTER_ID))

    # Deliberately diverge derived state without changing authoritative Movement Facts.
    composition.totals_engine.apply(stale_movement)
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, stale_key) == Decimal(99)

    first = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)
    first_snapshot = inventory_snapshot(
        composition=composition,
        keys=(valid_key, stale_key),
    )
    second = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)
    second_snapshot = inventory_snapshot(
        composition=composition,
        keys=(valid_key, stale_key),
    )

    assert first.outcome is MaintenanceOutcome.SUCCESS
    assert second.outcome is MaintenanceOutcome.SUCCESS
    assert first_snapshot == (Decimal(10), Decimal(0))
    assert second_snapshot == first_snapshot
    assert_active_valid(
        composition=composition,
        register_identity=INVENTORY_REGISTER_ID,
    )
    assert tuple(persistence.enumerate(INVENTORY_REGISTER_ID)) == facts_before


def test_empty_inventory_register_rebuilds_to_active_valid() -> None:
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    key = inventory_key(product="P1", warehouse="W1")

    result = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)

    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert result.operation is MaintenanceOperation.REBUILD
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == Decimal(0)
    assert_active_valid(
        composition=composition,
        register_identity=INVENTORY_REGISTER_ID,
    )


class FaultInjectingPersistence(InMemoryRegisterFactPersistence):
    def __init__(self) -> None:
        super().__init__()
        self.fail = False

    def enumerate(self, register_identity: Identifier):
        if self.fail:
            raise PersistenceError("controlled rebuild failure")
        return super().enumerate(register_identity)


def test_rebuild_failure_classification_uses_existing_generic_boundaries() -> None:
    register_identity = Identifier.new()

    class EmptyPersistence:
        def enumerate(self, _register_identity: Identifier) -> tuple[Movement, ...]:
            return ()

    class IndeterminatePersistence:
        def enumerate(self, _register_identity: Identifier) -> tuple[Movement, ...]:
            raise PersistenceIndeterminateError("controlled indeterminate persistence failure")

    class TotalsFailingEngine:
        def rebuild(
            self,
            _register_identity: Identifier,
            _movements: tuple[Movement, ...],
        ) -> None:
            raise TotalsError("controlled totals failure")

    class UnexpectedFailingEngine:
        def rebuild(
            self,
            _register_identity: Identifier,
            _movements: tuple[Movement, ...],
        ) -> None:
            raise RuntimeError("controlled unexpected failure")

    failing_persistence = FaultInjectingPersistence()
    failing_persistence.fail = True
    persistence_failure = DefaultTotalsMaintenanceCoordinator(
        engine=DefaultTotalsEngine(()),
        persistence=failing_persistence,
    )

    indeterminate = DefaultTotalsMaintenanceCoordinator(
        engine=DefaultTotalsEngine(()),
        persistence=IndeterminatePersistence(),
    )
    totals_failure = DefaultTotalsMaintenanceCoordinator(
        engine=TotalsFailingEngine(),
        persistence=EmptyPersistence(),
    )
    unexpected_failure = DefaultTotalsMaintenanceCoordinator(
        engine=UnexpectedFailingEngine(),
        persistence=EmptyPersistence(),
    )

    cases = (
        (persistence_failure, MaintenanceOutcome.FAILURE),
        (indeterminate, MaintenanceOutcome.INDETERMINATE),
        (totals_failure, MaintenanceOutcome.FAILURE),
        (unexpected_failure, MaintenanceOutcome.INDETERMINATE),
    )

    for coordinator, expected_outcome in cases:
        result = coordinator.rebuild(register_identity)
        assert result.operation is MaintenanceOperation.REBUILD
        assert result.outcome is expected_outcome
        assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
        assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_recovery_rebuilds_after_failure_condition_is_removed() -> None:
    persistence = FaultInjectingPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    persistence.fail = True

    failure = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)

    assert failure.operation is MaintenanceOperation.REBUILD
    assert failure.outcome is MaintenanceOutcome.FAILURE
    assert failure.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert failure.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED
    with pytest.raises(TotalsMaintenanceAdmissionError):
        composition.maintenance.ensure_mutation_admitted(INVENTORY_REGISTER_ID)

    persistence.fail = False
    recovery = composition.maintenance.recover(INVENTORY_REGISTER_ID)

    assert recovery.operation is MaintenanceOperation.REBUILD
    assert recovery.outcome is MaintenanceOutcome.SUCCESS
    assert recovery.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert recovery.state.consistency is TotalsConsistencyState.VALID
    composition.maintenance.ensure_mutation_admitted(INVENTORY_REGISTER_ID)


def test_rebuild_preserves_movement_facts_and_inventory_semantics() -> None:
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="10",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )
    post_goods_receipt(
        product="P1",
        warehouse="W2",
        quantity="7.5",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )
    expense = make_movement(
        register_identity=INVENTORY_REGISTER_ID,
        movement_type=MovementType.EXPENSE,
        product="P1",
        warehouse="W1",
        quantity=Decimal(3),
        accounting_time=accounting_time,
    )
    persistence.append((expense,))

    facts_before = tuple(persistence.enumerate(INVENTORY_REGISTER_ID))
    key_w1 = inventory_key(product="P1", warehouse="W1")
    key_w2 = inventory_key(product="P1", warehouse="W2")

    result = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)

    facts_after = tuple(persistence.enumerate(INVENTORY_REGISTER_ID))
    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert facts_after == facts_before
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key_w1) == Decimal(7)
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key_w2) == Decimal("7.5")
    assert composition.totals_engine.get(
        INVENTORY_REGISTER_ID,
        key_w1,
    ) != composition.totals_engine.get(
        INVENTORY_REGISTER_ID,
        key_w2,
    )


def test_unpost_then_rebuild_matches_incremental_totals() -> None:
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    persistence, document, _state_provider, engine, composition = post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="10",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )
    key = inventory_key(product="P1", warehouse="W1")

    result = engine.unpost(document)
    assert result.is_success
    incremental = composition.totals_engine.get(INVENTORY_REGISTER_ID, key)

    rebuild = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)

    assert rebuild.outcome is MaintenanceOutcome.SUCCESS
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == incremental == Decimal(0)
    assert persistence.find_by_source_document(INVENTORY_REGISTER_ID, document.identity) == ()
    assert_active_valid(
        composition=composition,
        register_identity=INVENTORY_REGISTER_ID,
    )


def test_repost_then_rebuild_matches_incremental_totals() -> None:
    persistence = InMemoryRegisterFactPersistence()
    composition = StandardConfigurationBootstrap().compose_inventory_register_platform(persistence)
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    _persistence, document, state_provider, engine, composition = post_goods_receipt(
        product="P1",
        warehouse="W1",
        quantity="10",
        accounting_time=accounting_time,
        persistence=persistence,
        composition=composition,
    )
    state_provider.state = make_state(
        product="P1",
        warehouse="W1",
        quantity=Decimal(15),
    )

    result = engine.repost(document)
    assert result.is_success
    key = inventory_key(product="P1", warehouse="W1")
    incremental = composition.totals_engine.get(INVENTORY_REGISTER_ID, key)

    rebuild = composition.maintenance.rebuild(INVENTORY_REGISTER_ID)

    assert rebuild.outcome is MaintenanceOutcome.SUCCESS
    assert composition.totals_engine.get(INVENTORY_REGISTER_ID, key) == incremental == Decimal(15)
    assert_active_valid(
        composition=composition,
        register_identity=INVENTORY_REGISTER_ID,
    )


def test_generic_register_rebuild_does_not_change_other_register_totals() -> None:
    register_a = Identifier.new()
    register_b = Identifier.new()
    persistence = InMemoryRegisterFactPersistence()
    definition_a = TotalsDefinition(
        register_identity=register_a,
        dimensions=("product",),
        resource_name="quantity",
        movement_type_signs={MovementType.INCOME: 1, MovementType.EXPENSE: -1},
    )
    definition_b = TotalsDefinition(
        register_identity=register_b,
        dimensions=("product",),
        resource_name="quantity",
        movement_type_signs={MovementType.INCOME: 1, MovementType.EXPENSE: -1},
    )
    engine = DefaultTotalsEngine((definition_a, definition_b))
    maintenance = DefaultTotalsMaintenanceCoordinator(engine=engine, persistence=persistence)
    accounting_time = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    movement_a = make_movement(
        register_identity=register_a,
        movement_type=MovementType.INCOME,
        product="P1",
        warehouse="W1",
        quantity=Decimal(10),
        accounting_time=accounting_time,
    )
    movement_b = make_movement(
        register_identity=register_b,
        movement_type=MovementType.INCOME,
        product="P2",
        warehouse="W2",
        quantity=Decimal(20),
        accounting_time=accounting_time,
    )
    persistence.append((movement_a, movement_b))
    engine.apply(movement_a)
    engine.apply(movement_b)

    key_a = TotalsKey.from_mapping({"product": "P1"})
    key_b = TotalsKey.from_mapping({"product": "P2"})
    before_b = engine.get(register_b, key_b)

    result = maintenance.rebuild(register_a)

    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert engine.get(register_a, key_a) == Decimal(10)
    assert engine.get(register_b, key_b) == before_b == Decimal(20)
    assert maintenance.state(register_a).consistency is TotalsConsistencyState.VALID
