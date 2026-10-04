from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from accore.platform.configuration.activation import ActiveConfiguration
from accore.platform.configuration.context import RuntimeConfigurationContext
from accore.platform.configuration.identity import ConfigurationIdentity, ConfigurationVersion
from accore.platform.metadata import MetadataRegistry
from accore.platform.processing import (
    Processing,
    ProcessingCommand,
    ProcessingContext,
    ProcessingDefinition,
    ProcessingDefinitionMismatchError,
    ProcessingError,
    ProcessingExecutionError,
    ProcessingExecutionIdentity,
    ProcessingIdentity,
    ProcessingNotFoundError,
    ProcessingOutcome,
    ProcessingProgress,
    ProcessingProgressObserver,
    ProcessingResult,
)
from accore.platform.security import SecurityContext

PROCESSING_ID = ProcessingIdentity("inventory.rebuild")
EXECUTION_ID = ProcessingExecutionIdentity(UUID("12345678-1234-5678-1234-567812345678"))


class _TestProgressObserver:
    def report(self, progress: ProcessingProgress) -> None:
        del progress


def make_runtime_configuration() -> RuntimeConfigurationContext:
    return RuntimeConfigurationContext(
        configuration=ActiveConfiguration(
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
            published_metadata=MetadataRegistry().publish(),
        ),
        application_configuration="standard-projection",
    )


def test_processing_identity_and_definition_are_immutable() -> None:
    identity = ProcessingIdentity("inventory.rebuild")
    definition = ProcessingDefinition(identity, "Inventory rebuild", "Rebuild inventory state")

    assert identity.value == "inventory.rebuild"
    assert definition.identity is identity
    assert definition.name == "Inventory rebuild"
    assert definition.description == "Rebuild inventory state"

    with pytest.raises(FrozenInstanceError):
        identity.value = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        definition.name = "other"  # type: ignore[misc]


def test_command_preserves_configuration_parameters_and_optional_execution_identity() -> None:
    configuration = make_runtime_configuration()
    parameters = object()
    command = ProcessingCommand(
        PROCESSING_ID, parameters, configuration, SecurityContext(None, None), EXECUTION_ID
    )

    assert command.processing_identity is PROCESSING_ID
    assert command.parameters is parameters
    assert command.runtime_configuration is configuration
    assert command.execution_identity is EXECUTION_ID


def test_command_allows_runtime_to_generate_execution_identity() -> None:
    command = ProcessingCommand(
        PROCESSING_ID,
        parameters=(),
        runtime_configuration=make_runtime_configuration(),
        security_context=SecurityContext(None, None),
    )

    assert command.execution_identity is None


def test_processing_context_is_typed_and_immutable() -> None:
    configuration = make_runtime_configuration()
    parameters = ("parameter",)
    context = ProcessingContext(
        execution_identity=EXECUTION_ID,
        runtime_configuration=configuration,
        security_context=SecurityContext(None, None),
        parameters=parameters,
        progress_observer=_TestProgressObserver(),
    )

    assert context.execution_identity is EXECUTION_ID
    assert context.runtime_configuration is configuration
    assert context.parameters == parameters

    with pytest.raises(FrozenInstanceError):
        context.parameters = ()  # type: ignore[misc]


def test_processing_result_preserves_identity_outcome_and_typed_details() -> None:
    result = ProcessingResult(
        execution_identity=EXECUTION_ID,
        processing_identity=PROCESSING_ID,
        outcome=ProcessingOutcome.SUCCESS,
        details={"rebuilt": True},
    )

    assert result.execution_identity is EXECUTION_ID
    assert result.processing_identity is PROCESSING_ID
    assert result.outcome is ProcessingOutcome.SUCCESS
    assert result.details == {"rebuilt": True}

    with pytest.raises(FrozenInstanceError):
        result.outcome = ProcessingOutcome.FAILURE  # type: ignore[misc]


def test_processing_outcomes_are_stable_string_values() -> None:
    assert ProcessingOutcome.SUCCESS.value == "success"
    assert ProcessingOutcome.FAILURE.value == "failure"
    assert ProcessingOutcome.INDETERMINATE.value == "indeterminate"


def test_progress_is_immutable_and_observer_is_structural_protocol() -> None:
    progress = ProcessingProgress(completed=1, total=2, description="rebuild register")

    class Observer:
        def report(self, value: ProcessingProgress) -> None:
            assert value is progress

    observer: ProcessingProgressObserver = Observer()
    observer.report(progress)

    with pytest.raises(FrozenInstanceError):
        progress.completed = 2  # type: ignore[misc]


def test_processing_protocol_accepts_concrete_implementation() -> None:
    class ConcreteProcessing:
        @property
        def definition(self) -> ProcessingDefinition:
            return ProcessingDefinition(
                PROCESSING_ID,
                "Inventory rebuild",
                "Rebuild inventory state",
            )

        def execute(self, context: ProcessingContext[tuple[str, ...]]) -> ProcessingResult[str]:
            return ProcessingResult(
                execution_identity=context.execution_identity,
                processing_identity=self.definition.identity,
                outcome=ProcessingOutcome.SUCCESS,
                details="ok",
            )

    processing: Processing[tuple[str, ...], str] = ConcreteProcessing()
    context = ProcessingContext(
        EXECUTION_ID,
        make_runtime_configuration(),
        ("rebuild",),
        ("parameter",),
        _TestProgressObserver(),
    )
    result = processing.execute(context)
    assert result.details == "ok"
    assert processing.definition.identity is PROCESSING_ID


def test_processing_errors_share_common_base() -> None:
    errors = (
        ProcessingNotFoundError(),
        ProcessingDefinitionMismatchError(),
        ProcessingExecutionError(),
    )

    assert all(isinstance(error, ProcessingError) for error in errors)
