from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from accore.platform.configuration.context import RuntimeConfigurationContext
from accore.platform.security import SecurityContext

from .command import ProcessingExecutionIdentity
from .progress import ProcessingProgressObserver

P = TypeVar("P")


@dataclass(frozen=True, slots=True)
class ProcessingContext[P]:
    """Immutable execution context supplied to a Processing implementation."""

    execution_identity: ProcessingExecutionIdentity
    runtime_configuration: RuntimeConfigurationContext
    security_context: SecurityContext
    parameters: P
    progress_observer: ProcessingProgressObserver
