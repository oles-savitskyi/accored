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
    STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT,
    STANDARD_INVENTORY_REBUILD_CONTRACT,
)
from .operations import StandardInventoryBalanceQueryBinding, StandardInventoryRebuildBinding


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
) -> StandardIntegrationComposition:
    """Compose Standard operations over the existing platform Runtime boundaries.

    Additional operations may be supplied by Standard modules (for example, a
    concrete import/export capability). All operation kinds share one registry.
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
