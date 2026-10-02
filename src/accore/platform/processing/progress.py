from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProcessingProgress:
    """Immutable observational progress notification."""

    completed: int
    total: int
    description: str


class ProcessingProgressObserver(Protocol):
    """Observer notified synchronously about Processing progress."""

    def report(self, progress: ProcessingProgress) -> None:
        """Receive one progress notification."""
        ...
