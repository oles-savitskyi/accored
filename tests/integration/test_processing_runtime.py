from __future__ import annotations

from unittest.mock import Mock
from uuid import UUID

from accore.platform.processing import (
    DefaultProcessingRuntime,
    ProcessingCommand,
    ProcessingExecutionIdentity,
    ProcessingIdentity,
    ProcessingOutcome,
    ProcessingProgress,
)
from accore.platform.registers import MaintenanceOutcome, MaintenanceResult
from accore.platform.security import AuthorizationService, SecurityContext
from accore.platform.valuation import ValuationRebuildOutcome, ValuationRebuildResult
from standard.bootstrap import StandardConfigurationBootstrap
from standard.processings import InventoryDerivedStateRebuildParameters
from standard.registers.inventory import INVENTORY_REGISTER_ID

_PROCESSING_IDENTITY = ProcessingIdentity("inventory.rebuild")
_EXECUTION_IDENTITY = ProcessingExecutionIdentity(UUID("12345678-1234-5678-1234-567812345678"))


class _AllowingAuthorizationService:
    def require(self, request: object) -> None:
        del request


AUTHORIZATION_SERVICE: AuthorizationService = _AllowingAuthorizationService()
SECURITY_CONTEXT = SecurityContext(principal=None, session=None)


class _ProgressObserver:
    def __init__(self) -> None:
        self.notifications: list[ProcessingProgress] = []

    def report(self, progress: ProcessingProgress) -> None:
        self.notifications.append(progress)


def _make_runtime_configuration() -> object:
    configuration, _ = StandardConfigurationBootstrap().initialize()
    return configuration


def test_standard_processing_executes_through_platform_runtime() -> None:
    bootstrap = StandardConfigurationBootstrap()
    register_maintenance = Mock()
    valuation_rebuilder = Mock()

    register_result = Mock(spec=MaintenanceResult)
    register_result.outcome = MaintenanceOutcome.SUCCESS
    valuation_result = Mock(spec=ValuationRebuildResult)
    valuation_result.outcome = ValuationRebuildOutcome.SUCCESS
    register_maintenance.rebuild.return_value = register_result
    valuation_rebuilder.rebuild.return_value = valuation_result

    processing = bootstrap.compose_inventory_rebuild_processing(
        register_maintenance=register_maintenance,
        valuation_rebuilder=valuation_rebuilder,
    )
    runtime = DefaultProcessingRuntime({_PROCESSING_IDENTITY: processing}, AUTHORIZATION_SERVICE)
    observer = _ProgressObserver()

    result = runtime.execute(
        ProcessingCommand(
            processing_identity=_PROCESSING_IDENTITY,
            parameters=InventoryDerivedStateRebuildParameters(),
            runtime_configuration=_make_runtime_configuration(),
            security_context=SECURITY_CONTEXT,
            execution_identity=_EXECUTION_IDENTITY,
        ),
        progress_observer=observer,
    )

    assert result.execution_identity is _EXECUTION_IDENTITY
    assert result.processing_identity == _PROCESSING_IDENTITY
    assert result.outcome is ProcessingOutcome.SUCCESS
    assert result.details.register_result is register_result
    assert result.details.valuation_result is valuation_result
    register_maintenance.rebuild.assert_called_once_with(INVENTORY_REGISTER_ID)
    valuation_rebuilder.rebuild.assert_called_once_with()
    assert observer.notifications == []


def test_standard_processing_runtime_uses_authoritative_standard_configuration() -> None:
    bootstrap = StandardConfigurationBootstrap()
    register_maintenance = Mock()
    valuation_rebuilder = Mock()

    register_result = Mock(spec=MaintenanceResult)
    register_result.outcome = MaintenanceOutcome.SUCCESS
    valuation_result = Mock(spec=ValuationRebuildResult)
    valuation_result.outcome = ValuationRebuildOutcome.SUCCESS
    register_maintenance.rebuild.return_value = register_result
    valuation_rebuilder.rebuild.return_value = valuation_result

    processing = bootstrap.compose_inventory_rebuild_processing(
        register_maintenance=register_maintenance,
        valuation_rebuilder=valuation_rebuilder,
    )
    runtime = DefaultProcessingRuntime({_PROCESSING_IDENTITY: processing}, AUTHORIZATION_SERVICE)
    runtime_configuration = _make_runtime_configuration()

    runtime.execute(
        ProcessingCommand(
            processing_identity=_PROCESSING_IDENTITY,
            parameters=InventoryDerivedStateRebuildParameters(),
            runtime_configuration=runtime_configuration,
            security_context=SECURITY_CONTEXT,
        )
    )

    register_maintenance.rebuild.assert_called_once_with(
        runtime_configuration.application_configuration.inventory_register_identity
    )
