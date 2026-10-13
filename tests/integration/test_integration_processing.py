from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from accore.platform.foundation.identity import Identifier
from accore.platform.integration import (
    BoundIntegrationOperation,
    CommandRequest,
    ContractVersion,
    DefaultIntegrationService,
    InMemoryIntegrationOperationRegistry,
    IntegrationContractIdentity,
    IntegrationContractKind,
)
from accore.platform.processing import (
    DefaultProcessingRuntime,
    ProcessingCommand,
    ProcessingContext,
    ProcessingDefinition,
    ProcessingIdentity,
    ProcessingOutcome,
    ProcessingResult,
)
from accore.platform.processing.runtime import ProcessingRuntime
from accore.platform.security import (
    AuthorizationRequest,
    AuthorizationService,
    SecurityContext,
)
from standard.bootstrap import StandardConfigurationBootstrap

_PROCESSING_IDENTITY = ProcessingIdentity("integration.example")


class _AuthorizationProbe:
    def __init__(self) -> None:
        self.contexts: list[SecurityContext] = []

    def require(self, request: AuthorizationRequest) -> None:
        self.contexts.append(request.context)


@dataclass(frozen=True, slots=True)
class _Payload:
    value: str


class _CapturingProcessing:
    def __init__(self) -> None:
        self.definition = ProcessingDefinition(
            _PROCESSING_IDENTITY,
            "Integration example",
            "Capture an Integration request through Processing Runtime",
        )
        self.context: ProcessingContext[object] | None = None

    def execute(self, context: ProcessingContext[object]) -> ProcessingResult[object]:
        self.context = context
        return ProcessingResult(
            execution_identity=context.execution_identity,
            processing_identity=_PROCESSING_IDENTITY,
            outcome=ProcessingOutcome.SUCCESS,
            details=context.parameters,
        )


class _ProcessingBinding:
    """Test binding that translates the Integration request into ProcessingCommand."""

    def __init__(self, runtime: ProcessingRuntime, runtime_configuration: object) -> None:
        self._runtime = runtime
        self._runtime_configuration = runtime_configuration

    def execute(self, request: object) -> object:
        assert isinstance(request, CommandRequest)
        assert isinstance(request.payload, _Payload)
        command = ProcessingCommand(
            processing_identity=_PROCESSING_IDENTITY,
            parameters=request.payload,
            runtime_configuration=self._runtime_configuration,  # type: ignore[arg-type]
            security_context=request.security_context,
        )
        return self._runtime.execute(command)


def test_processing_path_preserves_security_context() -> None:
    runtime_configuration, _ = StandardConfigurationBootstrap().initialize()
    security_context = SecurityContext(principal=None, session=None)
    authorization = _AuthorizationProbe()
    processing = _CapturingProcessing()
    runtime = DefaultProcessingRuntime(
        {_PROCESSING_IDENTITY: processing},
        cast(AuthorizationService, authorization),
    )
    identity = IntegrationContractIdentity(
        namespace="standard.example",
        name="run-processing",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.COMMAND,
    )
    registry = InMemoryIntegrationOperationRegistry()
    registry.register(
        BoundIntegrationOperation(
            contract=_Contract(identity),
            binding=_ProcessingBinding(runtime, runtime_configuration),
        )
    )
    service = DefaultIntegrationService(registry)
    request_identity = Identifier.new()

    response = service.execute_command(
        CommandRequest(
            contract=identity,
            payload=_Payload("hello"),
            security_context=security_context,
            request_identity=request_identity,
        )
    )

    assert response.request_identity is request_identity
    assert response.result.outcome is ProcessingOutcome.SUCCESS
    assert response.result.details == _Payload("hello")
    assert processing.context is not None
    assert processing.context.security_context is security_context
    assert authorization.contexts == [security_context]


@dataclass(frozen=True, slots=True)
class _Contract:
    identity: IntegrationContractIdentity
    description: str = "Execute a Processing"
