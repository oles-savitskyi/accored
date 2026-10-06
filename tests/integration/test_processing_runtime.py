from __future__ import annotations

from collections.abc import Mapping
from unittest.mock import Mock
from uuid import UUID

import pytest

from accore.platform.processing import (
    DefaultProcessingRuntime,
    ProcessingCommand,
    ProcessingContext,
    ProcessingDefinition,
    ProcessingExecutionIdentity,
    ProcessingIdentity,
    ProcessingOutcome,
    ProcessingProgress,
    ProcessingResult,
)
from accore.platform.registers import MaintenanceOutcome, MaintenanceResult
from accore.platform.security import (
    AuthorizationDeniedError,
    AuthorizationService,
    PasswordCredentials,
    SecurityContext,
)
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


class _ResolutionProbe(dict[ProcessingIdentity, object]):
    def __init__(self, values: Mapping[ProcessingIdentity, object]) -> None:
        super().__init__(values)
        self.lookups: list[ProcessingIdentity] = []

    def get(self, key: ProcessingIdentity, default: object = None) -> object:
        self.lookups.append(key)
        return super().get(key, default)


class _CapturingProcessing:
    def __init__(self, identity: ProcessingIdentity) -> None:
        self._definition = ProcessingDefinition(identity, "Capture", "Capture security context")
        self.context: ProcessingContext[object] | None = None

    @property
    def definition(self) -> ProcessingDefinition:
        return self._definition

    def execute(self, context: ProcessingContext[object]) -> ProcessingResult[object]:
        self.context = context
        return ProcessingResult(
            execution_identity=context.execution_identity,
            processing_identity=self._definition.identity,
            outcome=ProcessingOutcome.SUCCESS,
            details=None,
        )


class _ProgressObserver:
    def __init__(self) -> None:
        self.notifications: list[ProcessingProgress] = []

    def report(self, progress: ProcessingProgress) -> None:
        self.notifications.append(progress)


def _make_runtime_configuration() -> object:
    configuration, _ = StandardConfigurationBootstrap().initialize()
    return configuration


def test_processing_runtime_propagates_the_same_security_context_instance() -> None:
    bootstrap = StandardConfigurationBootstrap()
    security = bootstrap.compose_security(
        initial_passwords={
            "administrator": "administrator-test-password",
            "operator": "operator-test-password",
            "auditor": "auditor-test-password",
        }
    )
    operator_result = security.authentication.authenticate(
        PasswordCredentials(login="operator", password="operator-test-password")
    )
    security_context = security.context_factory.from_authentication(operator_result)
    processing = _CapturingProcessing(_PROCESSING_IDENTITY)
    runtime = DefaultProcessingRuntime({_PROCESSING_IDENTITY: processing}, security.authorization)

    runtime.execute(
        ProcessingCommand(
            processing_identity=_PROCESSING_IDENTITY,
            parameters=InventoryDerivedStateRebuildParameters(),
            runtime_configuration=_make_runtime_configuration(),
            security_context=security_context,
        )
    )

    assert processing.context is not None
    assert processing.context.security_context is security_context


def test_denied_processing_is_rejected_before_processing_resolution() -> None:
    bootstrap = StandardConfigurationBootstrap()
    security = bootstrap.compose_security(
        initial_passwords={
            "administrator": "administrator-test-password",
            "operator": "operator-test-password",
            "auditor": "auditor-test-password",
        }
    )
    auditor_result = security.authentication.authenticate(
        PasswordCredentials(login="auditor", password="auditor-test-password")
    )
    auditor_context = security.context_factory.from_authentication(auditor_result)
    processings = _ResolutionProbe({})
    runtime = DefaultProcessingRuntime(processings, security.authorization)

    with pytest.raises(AuthorizationDeniedError):
        runtime.execute(
            ProcessingCommand(
                processing_identity=_PROCESSING_IDENTITY,
                parameters=InventoryDerivedStateRebuildParameters(),
                runtime_configuration=_make_runtime_configuration(),
                security_context=auditor_context,
            )
        )

    assert processings.lookups == []


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


def test_standard_security_composition_authorizes_real_processing_and_denies_auditor() -> None:
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
    security = bootstrap.compose_security(
        initial_passwords={
            "administrator": "administrator-test-password",
            "operator": "operator-test-password",
            "auditor": "auditor-test-password",
        }
    )
    runtime = bootstrap.compose_processing_runtime(
        {_PROCESSING_IDENTITY: processing}, security.authorization
    )
    runtime_configuration = _make_runtime_configuration()

    operator_result = security.authentication.authenticate(
        PasswordCredentials(login="operator", password="operator-test-password")
    )
    operator_context = security.context_factory.from_authentication(operator_result)
    runtime.execute(
        ProcessingCommand(
            processing_identity=_PROCESSING_IDENTITY,
            parameters=InventoryDerivedStateRebuildParameters(),
            runtime_configuration=runtime_configuration,
            security_context=operator_context,
        )
    )
    register_maintenance.rebuild.assert_called_once_with(INVENTORY_REGISTER_ID)
    valuation_rebuilder.rebuild.assert_called_once_with()

    register_maintenance.reset_mock()
    valuation_rebuilder.reset_mock()

    auditor_result = security.authentication.authenticate(
        PasswordCredentials(login="auditor", password="auditor-test-password")
    )
    auditor_context = security.context_factory.from_authentication(auditor_result)

    with pytest.raises(AuthorizationDeniedError):
        runtime.execute(
            ProcessingCommand(
                processing_identity=_PROCESSING_IDENTITY,
                parameters=InventoryDerivedStateRebuildParameters(),
                runtime_configuration=runtime_configuration,
                security_context=auditor_context,
            )
        )

    register_maintenance.rebuild.assert_not_called()
    valuation_rebuilder.rebuild.assert_not_called()
