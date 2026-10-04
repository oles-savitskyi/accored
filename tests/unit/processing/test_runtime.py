from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

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
    ProcessingDefinitionMismatchError,
    ProcessingExecutionIdentity,
    ProcessingIdentity,
    ProcessingNotFoundError,
    ProcessingOutcome,
    ProcessingProgress,
    ProcessingResult,
)
from accore.platform.security import AuthorizationService, SecurityContext


@dataclass(frozen=True, slots=True)
class Parameters:
    value: str


@dataclass(frozen=True, slots=True)
class Details:
    value: str


class StubProcessing:
    def __init__(self, definition: ProcessingDefinition) -> None:
        self._definition = definition
        self.received_context: ProcessingContext[object] | None = None

    @property
    def definition(self) -> ProcessingDefinition:
        return self._definition

    def execute(self, context: ProcessingContext[object]) -> ProcessingResult[object]:
        self.received_context = context
        return ProcessingResult(
            execution_identity=context.execution_identity,
            processing_identity=self.definition.identity,
            outcome=ProcessingOutcome.SUCCESS,
            details=Details("done"),
        )


class ReportingProcessing(StubProcessing):
    def execute(self, context: ProcessingContext[object]) -> ProcessingResult[object]:
        self.received_context = context
        context.progress_observer.report(
            ProcessingProgress(completed=1, total=2, description="started")
        )
        context.progress_observer.report(
            ProcessingProgress(completed=2, total=2, description="completed")
        )
        return ProcessingResult(
            execution_identity=context.execution_identity,
            processing_identity=self.definition.identity,
            outcome=ProcessingOutcome.SUCCESS,
            details=Details("done"),
        )


class FailingProcessing(StubProcessing):
    def execute(self, context: ProcessingContext[object]) -> ProcessingResult[object]:
        raise RuntimeError("processing failed")


class RecordingObserver:
    def __init__(self) -> None:
        self.progress: list[ProcessingProgress] = []

    def report(self, progress: ProcessingProgress) -> None:
        self.progress.append(progress)


class AllowingAuthorizationService:
    def require(self, request: object) -> None:
        del request


AUTHORIZATION_SERVICE: AuthorizationService = AllowingAuthorizationService()
SECURITY_CONTEXT = SecurityContext(principal=None, session=None)


def _runtime_configuration() -> RuntimeConfigurationContext:
    return RuntimeConfigurationContext(
        configuration=ActiveConfiguration(
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
            published_metadata=MetadataRegistry().publish(),
        ),
        application_configuration="standard-projection",
    )


def _command(identity: ProcessingIdentity) -> ProcessingCommand:
    return ProcessingCommand(
        processing_identity=identity,
        parameters=Parameters("input"),
        runtime_configuration=_runtime_configuration(),
        security_context=SECURITY_CONTEXT,
    )


def test_execute_resolves_processing_and_preserves_command_data() -> None:
    identity = ProcessingIdentity("processing.example")
    definition = ProcessingDefinition(identity, "Example", "Example processing")
    processing = StubProcessing(definition)
    execution_identity = ProcessingExecutionIdentity(uuid4())
    parameters = Parameters("input")
    configuration = _runtime_configuration()
    runtime = DefaultProcessingRuntime({identity: processing}, AUTHORIZATION_SERVICE)
    command = ProcessingCommand(
        processing_identity=identity,
        parameters=parameters,
        runtime_configuration=configuration,
        security_context=SECURITY_CONTEXT,
        execution_identity=execution_identity,
    )

    result = runtime.execute(command)

    assert result.execution_identity == execution_identity
    assert result.processing_identity == identity
    assert processing.received_context is not None
    assert processing.received_context.execution_identity == execution_identity
    assert processing.received_context.runtime_configuration is configuration
    assert processing.received_context.security_context is SECURITY_CONTEXT
    assert processing.received_context.parameters is parameters


def test_execute_generates_execution_identity_when_command_does_not_provide_one() -> None:
    identity = ProcessingIdentity("processing.example")
    definition = ProcessingDefinition(identity, "Example", "Example processing")
    processing = StubProcessing(definition)
    runtime = DefaultProcessingRuntime({identity: processing}, AUTHORIZATION_SERVICE)
    command = _command(identity)

    result = runtime.execute(command)

    assert result.execution_identity.value is not None
    assert processing.received_context is not None
    assert processing.received_context.execution_identity == result.execution_identity


def test_execute_raises_when_processing_is_not_registered() -> None:
    identity = ProcessingIdentity("processing.missing")
    runtime = DefaultProcessingRuntime({}, AUTHORIZATION_SERVICE)

    with pytest.raises(ProcessingNotFoundError):
        runtime.execute(_command(identity))


def test_execute_raises_when_resolved_definition_identity_does_not_match() -> None:
    requested_identity = ProcessingIdentity("processing.requested")
    actual_identity = ProcessingIdentity("processing.actual")
    definition = ProcessingDefinition(actual_identity, "Actual", "Actual processing")
    processing = StubProcessing(definition)
    runtime = DefaultProcessingRuntime({requested_identity: processing}, AUTHORIZATION_SERVICE)

    with pytest.raises(ProcessingDefinitionMismatchError):
        runtime.execute(_command(requested_identity))


def test_execute_propagates_processing_exception() -> None:
    identity = ProcessingIdentity("processing.example")
    definition = ProcessingDefinition(identity, "Example", "Example processing")
    processing = FailingProcessing(definition)
    runtime = DefaultProcessingRuntime({identity: processing}, AUTHORIZATION_SERVICE)

    with pytest.raises(RuntimeError, match="processing failed"):
        runtime.execute(_command(identity))


def test_execute_forwards_progress_to_supplied_observer() -> None:
    identity = ProcessingIdentity("processing.example")
    definition = ProcessingDefinition(identity, "Example", "Example processing")
    processing = ReportingProcessing(definition)
    observer = RecordingObserver()
    runtime = DefaultProcessingRuntime({identity: processing}, AUTHORIZATION_SERVICE)

    runtime.execute(_command(identity), progress_observer=observer)

    assert observer.progress == [
        ProcessingProgress(completed=1, total=2, description="started"),
        ProcessingProgress(completed=2, total=2, description="completed"),
    ]


def test_execute_without_observer_provides_usable_noop_observer() -> None:
    identity = ProcessingIdentity("processing.example")
    definition = ProcessingDefinition(identity, "Example", "Example processing")
    processing = ReportingProcessing(definition)
    runtime = DefaultProcessingRuntime({identity: processing}, AUTHORIZATION_SERVICE)

    result = runtime.execute(_command(identity))

    assert result.outcome is ProcessingOutcome.SUCCESS
    assert processing.received_context is not None


def test_execute_isolates_progress_observer_failure() -> None:
    identity = ProcessingIdentity("processing.example")
    definition = ProcessingDefinition(identity, "Example", "Example processing")
    processing = ReportingProcessing(definition)
    runtime = DefaultProcessingRuntime({identity: processing}, AUTHORIZATION_SERVICE)

    class FailingObserver:
        def report(self, progress: ProcessingProgress) -> None:
            raise RuntimeError("observer failed")

    result = runtime.execute(_command(identity), progress_observer=FailingObserver())

    assert result.outcome is ProcessingOutcome.SUCCESS
