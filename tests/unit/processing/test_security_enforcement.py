from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from accore.platform.configuration.activation import ActiveConfiguration
from accore.platform.configuration.context import RuntimeConfigurationContext
from accore.platform.configuration.identity import ConfigurationIdentity, ConfigurationVersion
from accore.platform.metadata import MetadataRegistry
from accore.platform.processing import (
    DefaultProcessingRuntime,
    ProcessingCommand,
    ProcessingContext,
    ProcessingDefinition,
    ProcessingIdentity,
    ProcessingOutcome,
    ProcessingResult,
)
from accore.platform.security import (
    AuthorizationDecision,
    AuthorizationDeniedError,
    AuthorizationDenyReason,
    AuthorizationOutcome,
    AuthorizationRequest,
    AuthorizationService,
    SecurityContext,
    SecurityInfrastructureError,
    SecurityObjectIdentity,
    SecurityOperation,
)


@dataclass(frozen=True, slots=True)
class Parameters:
    value: str


@dataclass(frozen=True, slots=True)
class Details:
    value: str


class StubProcessing:
    def __init__(self, definition: ProcessingDefinition) -> None:
        self.definition = definition
        self.executed = False
        self.received_context: ProcessingContext[object] | None = None

    def execute(self, context: ProcessingContext[object]) -> ProcessingResult[object]:
        self.executed = True
        self.received_context = context
        return ProcessingResult(
            execution_identity=context.execution_identity,
            processing_identity=self.definition.identity,
            outcome=ProcessingOutcome.SUCCESS,
            details=Details("done"),
        )


def _runtime_configuration() -> RuntimeConfigurationContext:
    return RuntimeConfigurationContext(
        configuration=ActiveConfiguration(
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
            published_metadata=MetadataRegistry().publish(),
        ),
        application_configuration="standard-projection",
    )


def _context() -> SecurityContext:
    return SecurityContext(principal=None, session=None)


def _command(
    identity: ProcessingIdentity, context: SecurityContext | None = None
) -> ProcessingCommand:
    return ProcessingCommand(
        processing_identity=identity,
        parameters=Parameters("input"),
        runtime_configuration=_runtime_configuration(),
        security_context=context or _context(),
    )


def _definition(identity: ProcessingIdentity) -> ProcessingDefinition:
    return ProcessingDefinition(identity, "Example", "Example processing")


def test_runtime_authorizes_before_processing_resolution_and_execution() -> None:
    identity = ProcessingIdentity("processing.example")
    processing = StubProcessing(_definition(identity))
    authorization = Mock(spec=AuthorizationService)
    security_context = _context()
    runtime = DefaultProcessingRuntime({identity: processing}, authorization)

    runtime.execute(_command(identity, security_context))

    authorization.require.assert_called_once()
    request = authorization.require.call_args.args[0]
    assert isinstance(request, AuthorizationRequest)
    assert request.context is security_context
    assert request.target == SecurityObjectIdentity("processing", "processing.example")
    assert request.operation is SecurityOperation.EXECUTE
    assert request.resource is None
    assert processing.executed
    assert processing.received_context is not None
    assert processing.received_context.security_context is security_context


def test_runtime_does_not_resolve_processing_when_authorization_is_denied() -> None:
    identity = ProcessingIdentity("processing.example")
    processing = StubProcessing(_definition(identity))
    authorization = Mock(spec=AuthorizationService)
    authorization.require.side_effect = AuthorizationDeniedError(
        AuthorizationDecision(AuthorizationOutcome.DENY, AuthorizationDenyReason.MISSING_PERMISSION)
    )
    runtime = DefaultProcessingRuntime({identity: processing}, authorization)

    with pytest.raises(AuthorizationDeniedError):
        runtime.execute(_command(identity))

    assert not processing.executed


def test_runtime_propagates_authorization_infrastructure_failure() -> None:
    identity = ProcessingIdentity("processing.example")
    processing = StubProcessing(_definition(identity))
    authorization = Mock(spec=AuthorizationService)
    failure = SecurityInfrastructureError("security infrastructure unavailable")
    authorization.require.side_effect = failure
    runtime = DefaultProcessingRuntime({identity: processing}, authorization)

    with pytest.raises(SecurityInfrastructureError, match="security infrastructure unavailable"):
        runtime.execute(_command(identity))

    assert not processing.executed
