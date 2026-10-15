from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration import RuntimeConfigurationContext
from accore.platform.integration import (
    BoundIntegrationOperation,
    DefaultImportExportService,
    DefaultIntegrationService,
    ImportExportService,
    InMemoryEventDispatcher,
    InMemoryIntegrationOperationRegistry,
    IntegrationService,
    PostingEventBridge,
)
from accore.platform.integration.registry import (
    IntegrationOperation,
    IntegrationOperationRegistry,
)
from accore.platform.processing import ProcessingRuntime
from accore.platform.reporting import ReportRuntime

from .definitions import (
    STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT,
    STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT,
    STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT,
    STANDARD_INVENTORY_REBUILD_CONTRACT,
    StandardGoodsReceiptImportExecutor,
)
from .operations import (
    StandardGoodsReceiptImportBinding,
    StandardInventoryBalanceExportBinding,
    StandardInventoryBalanceQueryBinding,
    StandardInventoryRebuildBinding,
)


@dataclass(frozen=True, slots=True)
class StandardIntegrationComposition:
    """Composed Standard Integration services and their shared registry."""

    registry: IntegrationOperationRegistry
    service: IntegrationService
    import_export_service: ImportExportService
    event_dispatcher: InMemoryEventDispatcher
    posting_event_bridge: PostingEventBridge


def compose_standard_integration(
    *,
    processing_runtime: ProcessingRuntime,
    runtime_configuration: RuntimeConfigurationContext,
    report_runtime: ReportRuntime,
    additional_operations: tuple[IntegrationOperation, ...] = (),
    goods_receipt_import_executor: StandardGoodsReceiptImportExecutor | None = None,
) -> StandardIntegrationComposition:
    """Compose Standard operations over the existing platform Runtime boundaries.

    All operation kinds share one registry. Inventory Balance export is always
    registered. Goods Receipt import is registered only when the host supplies
    an executor that creates/persists the document and invokes the Posting API.
    """
    registry = InMemoryIntegrationOperationRegistry()
    registry.register(
        BoundIntegrationOperation(
            contract=STANDARD_INVENTORY_REBUILD_CONTRACT,
            binding=StandardInventoryRebuildBinding(
                processing_runtime,
                runtime_configuration,
            ),
        )
    )
    registry.register(
        BoundIntegrationOperation(
            contract=STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT,
            binding=StandardInventoryBalanceQueryBinding(report_runtime),
        )
    )
    registry.register(
        BoundIntegrationOperation(
            contract=STANDARD_INVENTORY_BALANCE_EXPORT_CONTRACT,
            binding=StandardInventoryBalanceExportBinding(report_runtime),
        )
    )
    if goods_receipt_import_executor is not None:
        registry.register(
            BoundIntegrationOperation(
                contract=STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT,
                binding=StandardGoodsReceiptImportBinding(goods_receipt_import_executor),
            )
        )
    for operation in additional_operations:
        registry.register(operation)

    event_dispatcher = InMemoryEventDispatcher()
    return StandardIntegrationComposition(
        registry=registry,
        service=DefaultIntegrationService(registry),
        import_export_service=DefaultImportExportService(registry),
        event_dispatcher=event_dispatcher,
        posting_event_bridge=PostingEventBridge(event_dispatcher),
    )


__all__ = ["StandardIntegrationComposition", "compose_standard_integration"]
