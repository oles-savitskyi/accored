from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, TypeVar
from uuid import uuid4

from accore.platform.security import (
    AuthorizationRequest,
    AuthorizationService,
    SecurityObjectIdentity,
    SecurityOperation,
)

from .command import ProcessingCommand, ProcessingExecutionIdentity
from .context import ProcessingContext
from .definition import ProcessingDefinition, ProcessingIdentity
from .errors import ProcessingDefinitionMismatchError, ProcessingNotFoundError
from .progress import ProcessingProgress, ProcessingProgressObserver
from .result import ProcessingResult

P_contra = TypeVar("P_contra", contravariant=True)
R_co = TypeVar("R_co", covariant=True)


class Processing(Protocol[P_contra, R_co]):
    @property
    def definition(self) -> ProcessingDefinition: ...

    def execute(
        self,
        context: ProcessingContext[P_contra],
    ) -> ProcessingResult[R_co]: ...


class ProcessingRuntime(Protocol):
    """Runtime boundary for executing a Processing command."""

    def execute(
        self,
        command: ProcessingCommand,
        progress_observer: ProcessingProgressObserver | None = None,
    ) -> ProcessingResult[object]: ...


class _NoOpProcessingProgressObserver:
    """Discard progress notifications when no external observer is supplied."""

    def report(self, progress: ProcessingProgress) -> None:
        del progress


class _SafeProcessingProgressObserver:
    """Isolate external observer failures from Processing execution."""

    def __init__(self, observer: ProcessingProgressObserver) -> None:
        self._observer = observer

    def report(self, progress: ProcessingProgress) -> None:
        try:
            self._observer.report(progress)
        except Exception:  # noqa: BLE001
            return


class DefaultProcessingRuntime:
    """Default in-memory runtime resolving Processing implementations by identity."""

    def __init__(
        self,
        processings: Mapping[ProcessingIdentity, Processing[object, object]],
        authorization_service: AuthorizationService,
    ) -> None:
        self._processings = processings
        self._authorization_service = authorization_service

    def execute(
        self,
        command: ProcessingCommand,
        progress_observer: ProcessingProgressObserver | None = None,
    ) -> ProcessingResult[object]:
        self._authorization_service.require(
            AuthorizationRequest(
                context=command.security_context,
                target=SecurityObjectIdentity(
                    object_type="processing",
                    object_code=command.processing_identity.value,
                ),
                operation=SecurityOperation.EXECUTE,
            )
        )

        processing = self._processings.get(command.processing_identity)
        if processing is None:
            raise ProcessingNotFoundError(command.processing_identity)

        if processing.definition.identity != command.processing_identity:
            raise ProcessingDefinitionMismatchError(command.processing_identity)

        execution_identity = command.execution_identity or ProcessingExecutionIdentity(uuid4())
        observer = (
            _NoOpProcessingProgressObserver()
            if progress_observer is None
            else _SafeProcessingProgressObserver(progress_observer)
        )
        context = ProcessingContext(
            execution_identity=execution_identity,
            runtime_configuration=command.runtime_configuration,
            security_context=command.security_context,
            parameters=command.parameters,
            progress_observer=observer,
        )
        return processing.execute(context)
