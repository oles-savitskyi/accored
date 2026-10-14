from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from accore.platform.foundation import Identifier
from accore.platform.integration import (
    CommandRequest,
    IntegrationContractKind,
    IntegrationContractValidationError,
    QueryRequest,
)
from accore.platform.processing import ProcessingCommand, ProcessingIdentity
from accore.platform.reporting import (
    CompiledReport,
    ReportAggregateOperation,
    ReportExecutionPlan,
    ReportSchema,
)
from accore.platform.security import SecurityContext
from standard.bootstrap import StandardConfigurationBootstrap
from standard.integration import (
    STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT,
    STANDARD_INVENTORY_REBUILD_CONTRACT,
    compose_standard_integration,
)
from standard.processings import InventoryDerivedStateRebuildParameters
from standard.reporting.inventory_balance import (
    INVENTORY_BALANCE_REPORT_DEFINITION,
    INVENTORY_BALANCE_REPORT_IDENTITY,
)


@dataclass
class FakeProcessingRuntime:
    command: ProcessingCommand | None = None
    result: object = "processing-result"

    def execute(self, command: ProcessingCommand, progress_observer: object = None) -> object:
        del progress_observer
        self.command = command
        return self.result


@dataclass
class FakeReportRuntime:
    plan: ReportExecutionPlan | None = None
    result: object = "report-result"

    def execute(self, plan: ReportExecutionPlan) -> object:
        self.plan = plan
        return self.result


def make_plan(
    report_identity: Identifier = INVENTORY_BALANCE_REPORT_IDENTITY,
) -> ReportExecutionPlan:
    definition = INVENTORY_BALANCE_REPORT_DEFINITION
    if report_identity != definition.identity:
        definition = replace(definition, identity=report_identity)
    compiled = CompiledReport(
        definition=definition,
        source_schema=ReportSchema(()),
        output_schema=ReportSchema(()),
    )
    return ReportExecutionPlan(
        compiled=compiled,
        filter_operation=None,
        group_operation=None,
        aggregate_operation=ReportAggregateOperation(definition.measures),
    )


def make_security_context() -> SecurityContext:
    return SecurityContext(principal=None, session=None)


def make_command_request() -> CommandRequest[InventoryDerivedStateRebuildParameters]:
    return CommandRequest(
        contract=STANDARD_INVENTORY_REBUILD_CONTRACT.identity,
        payload=InventoryDerivedStateRebuildParameters(),
        security_context=make_security_context(),
        request_identity=Identifier.new(),
    )


def make_query_request(plan: ReportExecutionPlan) -> QueryRequest[ReportExecutionPlan]:
    return QueryRequest(
        contract=STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT.identity,
        payload=plan,
        security_context=make_security_context(),
        request_identity=Identifier.new(),
    )


def test_standard_contract_definitions_have_expected_identities_and_kinds() -> None:
    assert STANDARD_INVENTORY_REBUILD_CONTRACT.identity.namespace == "standard.processing"
    assert STANDARD_INVENTORY_REBUILD_CONTRACT.identity.kind is IntegrationContractKind.COMMAND
    assert STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT.identity.namespace == "standard.reporting"
    assert STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT.identity.kind is IntegrationContractKind.QUERY


def test_standard_command_uses_processing_runtime_and_propagates_security_context() -> None:
    runtime_configuration, _ = StandardConfigurationBootstrap().initialize()
    processing_runtime = FakeProcessingRuntime()
    composition = compose_standard_integration(
        processing_runtime=processing_runtime,  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=FakeReportRuntime(),  # type: ignore[arg-type]
    )
    request = make_command_request()

    response = composition.service.execute_command(request)

    assert response.request_identity is request.request_identity
    assert response.result == "processing-result"
    assert processing_runtime.command is not None
    assert processing_runtime.command.processing_identity == ProcessingIdentity("inventory.rebuild")
    assert processing_runtime.command.parameters is request.payload
    assert processing_runtime.command.runtime_configuration is runtime_configuration
    assert processing_runtime.command.security_context is request.security_context


def test_standard_query_uses_reporting_runtime_with_inventory_balance_plan() -> None:
    runtime_configuration, _ = StandardConfigurationBootstrap().initialize()
    report_runtime = FakeReportRuntime()
    composition = compose_standard_integration(
        processing_runtime=FakeProcessingRuntime(),  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=report_runtime,  # type: ignore[arg-type]
    )
    plan = make_plan()
    request = make_query_request(plan)

    response = composition.service.execute_query(request)

    assert response.request_identity is request.request_identity
    assert response.result == "report-result"
    assert report_runtime.plan is plan


def test_standard_query_rejects_a_plan_for_another_report() -> None:
    runtime_configuration, _ = StandardConfigurationBootstrap().initialize()
    report_runtime = FakeReportRuntime()
    composition = compose_standard_integration(
        processing_runtime=FakeProcessingRuntime(),  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=report_runtime,  # type: ignore[arg-type]
    )
    request = make_query_request(make_plan(Identifier.new()))

    with pytest.raises(IntegrationContractValidationError):
        composition.service.execute_query(request)

    assert report_runtime.plan is None


def test_standard_composition_shares_registry_and_exposes_posting_event_bridge() -> None:
    runtime_configuration, _ = StandardConfigurationBootstrap().initialize()
    composition = compose_standard_integration(
        processing_runtime=FakeProcessingRuntime(),  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=FakeReportRuntime(),  # type: ignore[arg-type]
    )

    assert composition.registry.resolve(STANDARD_INVENTORY_REBUILD_CONTRACT.identity).contract == (
        STANDARD_INVENTORY_REBUILD_CONTRACT
    )
    assert (
        composition.registry.resolve(STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT.identity).contract
        == STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT
    )
    assert composition.import_export_service is not None
    assert composition.event_dispatcher is not None
    assert composition.posting_event_bridge is not None
