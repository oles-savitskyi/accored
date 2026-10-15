from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationContext,
)
from accore.platform.foundation import Identifier
from accore.platform.integration import (
    ExportRequest,
    ImportRequest,
    IntegrationContractKind,
    IntegrationContractNotFoundError,
)
from accore.platform.metadata import PublishedMetadataView
from accore.platform.processing import ProcessingCommand
from accore.platform.reporting import (
    CompiledReport,
    ReportAggregateOperation,
    ReportExecutionPlan,
    ReportSchema,
)
from accore.platform.security import SecurityContext
from standard.integration import (
    STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT,
    STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT,
    StandardGoodsReceiptImportLine,
    StandardGoodsReceiptImportPayload,
    compose_standard_integration,
    decode_standard_goods_receipt_import_payload,
)
from standard.reporting.inventory_balance import (
    INVENTORY_BALANCE_REPORT_DEFINITION,
)


@dataclass
class FakeProcessingRuntime:
    result: object = "processing-result"

    def execute(self, command: ProcessingCommand, progress_observer: object = None) -> object:
        del command, progress_observer
        return self.result


@dataclass
class FakeReportRuntime:
    plan: ReportExecutionPlan | None = None
    result: object = "report-result"

    def execute(self, plan: ReportExecutionPlan) -> object:
        self.plan = plan
        return self.result


def make_runtime_configuration() -> RuntimeConfigurationContext:
    active = ActiveConfiguration(
        ConfigurationIdentity("test"),
        ConfigurationVersion(1),
        PublishedMetadataView(()),
    )
    return RuntimeConfigurationContext(active)


def make_plan() -> ReportExecutionPlan:
    definition = INVENTORY_BALANCE_REPORT_DEFINITION
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


@dataclass
class FakeGoodsReceiptImportExecutor:
    payload: StandardGoodsReceiptImportPayload | None = None
    security_context: SecurityContext | None = None
    request_identity: Identifier | None = None

    def execute(
        self,
        payload: StandardGoodsReceiptImportPayload,
        security_context: SecurityContext,
        request_identity: Identifier,
    ) -> object:
        self.payload = payload
        self.security_context = security_context
        self.request_identity = request_identity
        return {"posted": True, "line_count": len(payload.lines)}


def test_standard_goods_receipt_import_contract_validates_logical_payload() -> None:
    payload = StandardGoodsReceiptImportPayload(
        (StandardGoodsReceiptImportLine("P1", "W1", Decimal("2.5")),)
    )

    STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT.validate(payload)

    assert STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT.identity.kind is IntegrationContractKind.IMPORT


def test_standard_goods_receipt_json_payload_decoder_uses_decimal_quantities() -> None:
    payload = decode_standard_goods_receipt_import_payload(
        {"lines": [{"product": "P1", "warehouse": "W1", "quantity": 2.75}]}
    )

    assert payload.lines[0].quantity == Decimal("2.75")


def test_standard_goods_receipt_import_rejects_non_positive_quantity() -> None:
    try:
        StandardGoodsReceiptImportLine("P1", "W1", Decimal(0))
    except ValueError as exc:
        assert "positive finite Decimal" in str(exc)
    else:
        raise AssertionError("Expected invalid quantity to be rejected.")


def test_standard_import_binding_propagates_security_and_request_identity() -> None:
    runtime_configuration = make_runtime_configuration()
    executor = FakeGoodsReceiptImportExecutor()
    composition = compose_standard_integration(
        processing_runtime=FakeProcessingRuntime(),  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=FakeReportRuntime(),  # type: ignore[arg-type]
        goods_receipt_import_executor=executor,
    )
    payload = StandardGoodsReceiptImportPayload(
        (StandardGoodsReceiptImportLine("P1", "W1", Decimal(3)),)
    )
    security_context = SecurityContext(principal=None, session=None)
    request_identity = Identifier.new()
    request = ImportRequest(
        STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT.identity,
        payload,
        security_context,
        request_identity,
    )

    result = composition.import_export_service.execute_import(request)

    assert result.request_identity is request_identity
    assert result.result == {"posted": True, "line_count": 1}
    assert executor.payload is payload
    assert executor.security_context is security_context
    assert executor.request_identity is request_identity


def test_standard_inventory_balance_export_is_registered_and_executes_report() -> None:
    runtime_configuration = make_runtime_configuration()
    report_runtime = FakeReportRuntime(result={"rows": [{"product": "P1"}]})
    composition = compose_standard_integration(
        processing_runtime=FakeProcessingRuntime(),  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=report_runtime,  # type: ignore[arg-type]
    )
    plan = make_plan()
    request_identity = Identifier.new()
    request = ExportRequest(
        STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT.identity,
        plan,
        SecurityContext(principal=None, session=None),
        request_identity,
    )

    result = composition.import_export_service.execute_export(request)

    assert result.request_identity is request_identity
    assert result.content == {"rows": [{"product": "P1"}]}
    assert report_runtime.plan is plan
    assert (
        composition.registry.resolve(STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT.identity).contract
        == STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT
    )


def test_standard_import_is_not_registered_without_business_executor() -> None:
    runtime_configuration = make_runtime_configuration()
    composition = compose_standard_integration(
        processing_runtime=FakeProcessingRuntime(),  # type: ignore[arg-type]
        runtime_configuration=runtime_configuration,
        report_runtime=FakeReportRuntime(),  # type: ignore[arg-type]
    )

    try:
        composition.registry.resolve(STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT.identity)
    except IntegrationContractNotFoundError as exc:
        assert "No Integration operation" in str(exc)
    else:
        raise AssertionError("Import must not be advertised without a business executor.")
