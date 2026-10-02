from __future__ import annotations


class ProcessingError(Exception):
    """Base error for Processing runtime failures."""


class ProcessingNotFoundError(ProcessingError):
    """Raised when a requested Processing identity is not registered."""


class ProcessingDefinitionMismatchError(ProcessingError):
    """Raised when a resolved Processing does not match its requested definition."""


class ProcessingExecutionError(ProcessingError):
    """Raised for Processing execution failures at the runtime boundary."""
