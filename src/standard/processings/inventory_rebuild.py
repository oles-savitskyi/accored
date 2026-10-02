from __future__ import annotations

from dataclasses import dataclass

from accore.platform.processing import (
    ProcessingContext,
    ProcessingDefinition,
    ProcessingExecutionError,
    ProcessingIdentity,
    ProcessingOutcome,
    ProcessingResult,
)
from accore.platform.registers import (
    MaintenanceOutcome,
    MaintenanceResult,
    TotalsMaintenanceCoordinator,
)
from accore.platform.valuation import (
    ValuationRebuilder,
    ValuationRebuildOutcome,
    ValuationRebuildResult,
)
from standard.configuration import StandardRuntimeConfiguration

_PROCESSING_IDENTITY = ProcessingIdentity("inventory.rebuild")
_PROCESSING_DEFINITION = ProcessingDefinition(
    identity=_PROCESSING_IDENTITY,
    name="Inventory Derived State Rebuild",
    description="Rebuild Inventory Register Totals and Valuation derived state.",
)


@dataclass(frozen=True, slots=True)
class InventoryDerivedStateRebuildParameters:
    """Parameters for rebuilding Inventory derived state."""


@dataclass(frozen=True, slots=True)
class InventoryDerivedStateRebuildResult:
    """Complete results of the Register and Valuation rebuild operations."""

    register_result: MaintenanceResult
    valuation_result: ValuationRebuildResult


class InventoryDerivedStateRebuildProcessing:
    """Orchestrate independent Register and Valuation derived-state rebuilds."""

    def __init__(
        self,
        register_maintenance: TotalsMaintenanceCoordinator,
        valuation_rebuilder: ValuationRebuilder,
    ) -> None:
        self._register_maintenance = register_maintenance
        self._valuation_rebuilder = valuation_rebuilder

    @property
    def definition(self) -> ProcessingDefinition:
        return _PROCESSING_DEFINITION

    def execute(
        self,
        context: ProcessingContext[InventoryDerivedStateRebuildParameters],
    ) -> ProcessingResult[InventoryDerivedStateRebuildResult]:
        configuration = context.runtime_configuration.application_configuration
        if not isinstance(configuration, StandardRuntimeConfiguration):
            raise ProcessingExecutionError(
                "Inventory Derived State Rebuild requires StandardRuntimeConfiguration."
            )

        register_result = self._register_maintenance.rebuild(
            configuration.inventory_register_identity
        )
        valuation_result = self._valuation_rebuilder.rebuild()
        details = InventoryDerivedStateRebuildResult(
            register_result=register_result,
            valuation_result=valuation_result,
        )

        return ProcessingResult(
            execution_identity=context.execution_identity,
            processing_identity=_PROCESSING_IDENTITY,
            outcome=_aggregate_outcome(register_result, valuation_result),
            details=details,
        )


def _aggregate_outcome(
    register_result: MaintenanceResult,
    valuation_result: ValuationRebuildResult,
) -> ProcessingOutcome:
    if (
        register_result.outcome is MaintenanceOutcome.INDETERMINATE
        or valuation_result.outcome is ValuationRebuildOutcome.INDETERMINATE
    ):
        return ProcessingOutcome.INDETERMINATE

    if (
        register_result.outcome is MaintenanceOutcome.FAILURE
        or valuation_result.outcome is ValuationRebuildOutcome.FAILURE
    ):
        return ProcessingOutcome.FAILURE

    return ProcessingOutcome.SUCCESS
