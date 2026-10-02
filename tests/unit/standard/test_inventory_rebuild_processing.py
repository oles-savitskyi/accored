from __future__ import annotations

from uuid import UUID

import pytest

from accore.platform.configuration.activation import ActiveConfiguration
from accore.platform.configuration.context import RuntimeConfigurationContext
from accore.platform.configuration.identity import ConfigurationIdentity, ConfigurationVersion
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataRegistry
from accore.platform.processing import (
    ProcessingContext,
    ProcessingExecutionError,
    ProcessingExecutionIdentity,
    ProcessingOutcome,
)
from accore.platform.registers import (
    MaintenanceOperation,
    MaintenanceOutcome,
    MaintenanceResult,
    TotalsConsistencyState,
    TotalsLifecycleState,
    TotalsMaintenanceState,
)
from accore.platform.valuation import (
    ValuationKey,
    ValuationRebuildOutcome,
    ValuationRebuildResult,
)
from standard.configuration import StandardRuntimeConfiguration
from standard.processings import (
    InventoryDerivedStateRebuildParameters,
    InventoryDerivedStateRebuildProcessing,
    InventoryDerivedStateRebuildResult,
)

REGISTER_ID = Identifier.new()
EXECUTION_ID = ProcessingExecutionIdentity(UUID("12345678-1234-5678-1234-567812345678"))


def make_context(
    *,
    application_configuration: object | None = StandardRuntimeConfiguration(REGISTER_ID),
) -> ProcessingContext[InventoryDerivedStateRebuildParameters]:
    return ProcessingContext(
        execution_identity=EXECUTION_ID,
        runtime_configuration=RuntimeConfigurationContext(
            configuration=ActiveConfiguration(
                identity=ConfigurationIdentity("standard"),
                version=ConfigurationVersion(1),
                published_metadata=MetadataRegistry().publish(),
            ),
            application_configuration=application_configuration,
        ),
        parameters=InventoryDerivedStateRebuildParameters(),
        progress_observer=lambda progress: None,
    )


def make_register_result(outcome: MaintenanceOutcome) -> MaintenanceResult:
    return MaintenanceResult(
        operation=MaintenanceOperation.REBUILD,
        outcome=outcome,
        state=TotalsMaintenanceState(
            lifecycle=TotalsLifecycleState.ACTIVE,
            consistency=TotalsConsistencyState.VALID,
        ),
    )


def make_valuation_result(outcome: ValuationRebuildOutcome) -> ValuationRebuildResult:
    return ValuationRebuildResult(outcome)


class FakeRegisterMaintenance:
    def __init__(self, result: MaintenanceResult) -> None:
        self.result = result
        self.register_identity: Identifier | None = None
        self.calls = 0

    def rebuild(self, register_identity: Identifier) -> MaintenanceResult:
        self.calls += 1
        self.register_identity = register_identity
        return self.result


class FakeValuationRebuilder:
    def __init__(self, result: ValuationRebuildResult) -> None:
        self.result = result
        self.calls = 0

    def rebuild(self) -> ValuationRebuildResult:
        self.calls += 1
        return self.result

    def rebuild_for(self, valuation_key: ValuationKey) -> ValuationRebuildResult:
        raise AssertionError(f"unexpected rebuild_for call: {valuation_key!r}")


@pytest.mark.parametrize(
    ("register_outcome", "valuation_outcome", "expected"),
    [
        (MaintenanceOutcome.SUCCESS, ValuationRebuildOutcome.SUCCESS, ProcessingOutcome.SUCCESS),
        (MaintenanceOutcome.FAILURE, ValuationRebuildOutcome.SUCCESS, ProcessingOutcome.FAILURE),
        (MaintenanceOutcome.SUCCESS, ValuationRebuildOutcome.FAILURE, ProcessingOutcome.FAILURE),
        (MaintenanceOutcome.FAILURE, ValuationRebuildOutcome.FAILURE, ProcessingOutcome.FAILURE),
        (
            MaintenanceOutcome.INDETERMINATE,
            ValuationRebuildOutcome.SUCCESS,
            ProcessingOutcome.INDETERMINATE,
        ),
        (
            MaintenanceOutcome.SUCCESS,
            ValuationRebuildOutcome.INDETERMINATE,
            ProcessingOutcome.INDETERMINATE,
        ),
        (
            MaintenanceOutcome.INDETERMINATE,
            ValuationRebuildOutcome.FAILURE,
            ProcessingOutcome.INDETERMINATE,
        ),
        (
            MaintenanceOutcome.FAILURE,
            ValuationRebuildOutcome.INDETERMINATE,
            ProcessingOutcome.INDETERMINATE,
        ),
        (
            MaintenanceOutcome.INDETERMINATE,
            ValuationRebuildOutcome.INDETERMINATE,
            ProcessingOutcome.INDETERMINATE,
        ),
    ],
)
def test_processing_aggregates_subsystem_outcomes(
    register_outcome: MaintenanceOutcome,
    valuation_outcome: ValuationRebuildOutcome,
    expected: ProcessingOutcome,
) -> None:
    register_result = make_register_result(register_outcome)
    valuation_result = make_valuation_result(valuation_outcome)
    register = FakeRegisterMaintenance(register_result)
    valuation = FakeValuationRebuilder(valuation_result)
    processing = InventoryDerivedStateRebuildProcessing(register, valuation)

    result = processing.execute(make_context())

    assert result.outcome is expected
    assert result.details == InventoryDerivedStateRebuildResult(register_result, valuation_result)
    assert register.calls == 1
    assert valuation.calls == 1
    assert register.register_identity == REGISTER_ID


def test_processing_parameters_are_empty_and_immutable() -> None:
    parameters = InventoryDerivedStateRebuildParameters()

    assert parameters == InventoryDerivedStateRebuildParameters()


def test_processing_definition_has_standard_inventory_rebuild_identity() -> None:
    processing = InventoryDerivedStateRebuildProcessing(
        FakeRegisterMaintenance(make_register_result(MaintenanceOutcome.SUCCESS)),
        FakeValuationRebuilder(make_valuation_result(ValuationRebuildOutcome.SUCCESS)),
    )

    assert processing.definition.identity.value == "inventory.rebuild"
    assert processing.definition.name == "Inventory Derived State Rebuild"


def test_processing_does_not_read_register_identity_from_parameters() -> None:
    register = FakeRegisterMaintenance(make_register_result(MaintenanceOutcome.SUCCESS))
    valuation = FakeValuationRebuilder(make_valuation_result(ValuationRebuildOutcome.SUCCESS))
    processing = InventoryDerivedStateRebuildProcessing(register, valuation)

    result = processing.execute(make_context())

    assert result.details.register_result is register.result
    assert register.register_identity == REGISTER_ID


def test_processing_requires_standard_runtime_configuration() -> None:
    processing = InventoryDerivedStateRebuildProcessing(
        FakeRegisterMaintenance(make_register_result(MaintenanceOutcome.SUCCESS)),
        FakeValuationRebuilder(make_valuation_result(ValuationRebuildOutcome.SUCCESS)),
    )

    with pytest.raises(ProcessingExecutionError):
        processing.execute(make_context(application_configuration=None))


def test_processing_invokes_valuation_even_when_register_reports_failure() -> None:
    register = FakeRegisterMaintenance(make_register_result(MaintenanceOutcome.FAILURE))
    valuation = FakeValuationRebuilder(make_valuation_result(ValuationRebuildOutcome.SUCCESS))
    processing = InventoryDerivedStateRebuildProcessing(register, valuation)

    processing.execute(make_context())

    assert register.calls == 1
    assert valuation.calls == 1


def test_processing_invokes_register_even_when_valuation_reports_failure() -> None:
    register = FakeRegisterMaintenance(make_register_result(MaintenanceOutcome.SUCCESS))
    valuation = FakeValuationRebuilder(make_valuation_result(ValuationRebuildOutcome.FAILURE))
    processing = InventoryDerivedStateRebuildProcessing(register, valuation)

    processing.execute(make_context())

    assert register.calls == 1
    assert valuation.calls == 1
