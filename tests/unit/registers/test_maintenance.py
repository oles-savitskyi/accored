from __future__ import annotations

from dataclasses import FrozenInstanceError
from inspect import signature

import pytest

from accore.platform.foundation import Identifier
from accore.platform.registers import (
    DefaultTotalsMaintenanceCoordinator,
    MaintenanceOperation,
    MaintenanceOutcome,
    MaintenanceResult,
    TotalsConsistencyState,
    TotalsLifecycleState,
    TotalsMaintenanceCoordinator,
    TotalsMaintenanceState,
)


def make_state(
    *,
    lifecycle: TotalsLifecycleState = TotalsLifecycleState.ACTIVE,
    consistency: TotalsConsistencyState = TotalsConsistencyState.VALID,
) -> TotalsMaintenanceState:
    return TotalsMaintenanceState(
        lifecycle=lifecycle,
        consistency=consistency,
    )


def test_maintenance_operation_vocabulary_is_fixed() -> None:
    assert [operation.value for operation in MaintenanceOperation] == [
        "apply",
        "remove",
        "rebuild",
    ]

    assert not hasattr(MaintenanceOperation, "RECOVER")


def test_totals_lifecycle_state_vocabulary_is_fixed() -> None:
    assert [state.value for state in TotalsLifecycleState] == [
        "created",
        "active",
        "maintenance",
    ]


def test_totals_consistency_state_vocabulary_is_fixed() -> None:
    assert [state.value for state in TotalsConsistencyState] == [
        "valid",
        "indeterminate",
        "recovery_required",
    ]


def test_maintenance_outcome_vocabulary_is_fixed() -> None:
    assert [outcome.value for outcome in MaintenanceOutcome] == [
        "success",
        "failure",
        "indeterminate",
    ]


def test_maintenance_state_preserves_lifecycle_and_consistency_separately() -> None:
    state = TotalsMaintenanceState(
        lifecycle=TotalsLifecycleState.MAINTENANCE,
        consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
    )

    assert state.lifecycle is TotalsLifecycleState.MAINTENANCE
    assert state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_maintenance_state_is_frozen_and_slot_based() -> None:
    state = make_state()

    assert TotalsMaintenanceState.__slots__ == (
        "lifecycle",
        "consistency",
    )

    with pytest.raises(FrozenInstanceError):
        state.lifecycle = TotalsLifecycleState.MAINTENANCE  # type: ignore[misc]


def test_maintenance_result_is_frozen_and_slot_based() -> None:
    result = MaintenanceResult(
        operation=MaintenanceOperation.REBUILD,
        outcome=MaintenanceOutcome.SUCCESS,
        state=make_state(),
    )

    assert MaintenanceResult.__slots__ == (
        "operation",
        "outcome",
        "state",
    )

    with pytest.raises(FrozenInstanceError):
        result.outcome = MaintenanceOutcome.FAILURE  # type: ignore[misc]


def test_maintenance_result_preserves_operation_outcome_and_state() -> None:
    state = TotalsMaintenanceState(
        lifecycle=TotalsLifecycleState.ACTIVE,
        consistency=TotalsConsistencyState.VALID,
    )
    result = MaintenanceResult(
        operation=MaintenanceOperation.APPLY,
        outcome=MaintenanceOutcome.SUCCESS,
        state=state,
    )

    assert result.operation is MaintenanceOperation.APPLY
    assert result.outcome is MaintenanceOutcome.SUCCESS
    assert result.state is state


def test_outcome_and_consistency_are_independent() -> None:
    result = MaintenanceResult(
        operation=MaintenanceOperation.APPLY,
        outcome=MaintenanceOutcome.INDETERMINATE,
        state=TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.MAINTENANCE,
            consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
        ),
    )

    assert result.outcome is MaintenanceOutcome.INDETERMINATE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_rebuild_failure_can_return_recovery_required_state() -> None:
    result = MaintenanceResult(
        operation=MaintenanceOperation.REBUILD,
        outcome=MaintenanceOutcome.FAILURE,
        state=TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.MAINTENANCE,
            consistency=TotalsConsistencyState.RECOVERY_REQUIRED,
        ),
    )

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.FAILURE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED


def test_recovery_is_not_an_aggregation_operation() -> None:
    assert {operation.value for operation in MaintenanceOperation} == {
        "apply",
        "remove",
        "rebuild",
    }


def test_totals_maintenance_coordinator_is_a_runtime_checkable_protocol_contract() -> None:
    assert getattr(TotalsMaintenanceCoordinator, "_is_protocol", False) is True


def test_totals_maintenance_coordinator_has_the_public_api_only() -> None:
    public_methods = {
        name for name in dir(TotalsMaintenanceCoordinator) if not name.startswith("_")
    }

    assert public_methods == {
        "apply",
        "ensure_mutation_admitted",
        "remove",
        "rebuild",
        "recover",
        "state",
    }


def test_apply_signature() -> None:
    method = TotalsMaintenanceCoordinator.apply
    parameters = list(signature(method).parameters.values())

    assert [parameter.name for parameter in parameters] == ["self", "movement"]
    assert parameters[1].annotation == "Movement"
    assert method.__annotations__["return"] == "MaintenanceResult"


def test_remove_signature() -> None:
    method = TotalsMaintenanceCoordinator.remove
    parameters = list(signature(method).parameters.values())

    assert [parameter.name for parameter in parameters] == ["self", "movement"]
    assert parameters[1].annotation == "Movement"
    assert method.__annotations__["return"] == "MaintenanceResult"


def test_rebuild_signature() -> None:
    method = TotalsMaintenanceCoordinator.rebuild
    parameters = list(signature(method).parameters.values())

    assert [parameter.name for parameter in parameters] == ["self", "register_identity"]
    assert parameters[1].annotation == "Identifier"
    assert method.__annotations__["return"] == "MaintenanceResult"


def test_recover_signature() -> None:
    method = TotalsMaintenanceCoordinator.recover
    parameters = list(signature(method).parameters.values())

    assert [parameter.name for parameter in parameters] == ["self", "register_identity"]
    assert parameters[1].annotation == "Identifier"
    assert method.__annotations__["return"] == "MaintenanceResult"


def test_rebuild_unexpected_failure_returns_indeterminate_recovery_required_state() -> None:
    register = Identifier.new()

    class Persistence:
        def enumerate(self, register_identity: Identifier) -> tuple[object, ...]:
            return ()

    class FailingEngine:
        def rebuild(self, register_identity: Identifier, movements: tuple[object, ...]) -> None:
            raise RuntimeError("unexpected rebuild failure")

    coordinator = DefaultTotalsMaintenanceCoordinator(
        engine=FailingEngine(),
        persistence=Persistence(),
    )

    result = coordinator.rebuild(register)

    assert result.operation is MaintenanceOperation.REBUILD
    assert result.outcome is MaintenanceOutcome.INDETERMINATE
    assert result.state.lifecycle is TotalsLifecycleState.ACTIVE
    assert result.state.consistency is TotalsConsistencyState.RECOVERY_REQUIRED
    assert coordinator.state(register) == result.state
