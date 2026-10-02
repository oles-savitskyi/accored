from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

from .command import ProcessingExecutionIdentity
from .definition import ProcessingIdentity

R = TypeVar("R")


class ProcessingOutcome(StrEnum):
    """Business outcome of a completed Processing execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ProcessingResult[R]:
    """Immutable result of a completed Processing execution."""

    execution_identity: ProcessingExecutionIdentity
    processing_identity: ProcessingIdentity
    outcome: ProcessingOutcome
    details: R
