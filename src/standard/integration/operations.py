from __future__ import annotations

from accore.platform.configuration import RuntimeConfigurationContext
from accore.platform.integration import (
    CommandRequest,
    IntegrationContractValidationError,
    QueryRequest,
)
from accore.platform.processing import ProcessingCommand, ProcessingIdentity, ProcessingRuntime
from accore.platform.reporting import ReportExecutionPlan, ReportRuntime
from standard.processings import InventoryDerivedStateRebuildParameters
from standard.reporting.inventory_balance import INVENTORY_BALANCE_REPORT_IDENTITY


class StandardInventoryRebuildBinding:
    """Adapt the published Standard rebuild command to Processing Runtime."""

    def __init__(
        self,
        runtime: ProcessingRuntime,
        runtime_configuration: RuntimeConfigurationContext,
    ) -> None:
        self._runtime = runtime
        self._runtime_configuration = runtime_configuration

    def execute(self, request: object) -> object:
        if not isinstance(request, CommandRequest):
            raise IntegrationContractValidationError(
                "Inventory rebuild requires a command request."
            )
        if not isinstance(request.payload, InventoryDerivedStateRebuildParameters):
            raise IntegrationContractValidationError(
                "Inventory rebuild payload has an unsupported type."
            )

        command = ProcessingCommand(
            processing_identity=ProcessingIdentity("inventory.rebuild"),
            parameters=request.payload,
            runtime_configuration=self._runtime_configuration,
            security_context=request.security_context,
        )
        return self._runtime.execute(command)


class StandardInventoryBalanceQueryBinding:
    """Adapt the published Inventory Balance query to Reporting Runtime."""

    def __init__(self, runtime: ReportRuntime) -> None:
        self._runtime = runtime

    def execute(self, request: object) -> object:
        if not isinstance(request, QueryRequest):
            raise IntegrationContractValidationError("Inventory Balance requires a query request.")
        if not isinstance(request.payload, ReportExecutionPlan):
            raise IntegrationContractValidationError(
                "Inventory Balance query payload must be a ReportExecutionPlan."
            )
        if request.payload.compiled.definition.identity != INVENTORY_BALANCE_REPORT_IDENTITY:
            raise IntegrationContractValidationError(
                "Inventory Balance query requires the Standard Inventory Balance plan."
            )
        return self._runtime.execute(request.payload)
