from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from accore.platform.configuration.context import RuntimeConfigurationContext

from .definition import ProcessingIdentity


@dataclass(frozen=True, slots=True)
class ProcessingExecutionIdentity:
    """Immutable correlation identity of one Processing execution."""

    value: UUID


@dataclass(frozen=True, slots=True)
class ProcessingCommand:
    """Immutable request to execute one Processing against a configuration snapshot."""

    processing_identity: ProcessingIdentity
    parameters: object
    runtime_configuration: RuntimeConfigurationContext
    execution_identity: ProcessingExecutionIdentity | None = None
