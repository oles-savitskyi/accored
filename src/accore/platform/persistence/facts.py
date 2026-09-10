from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

# Movement is the Register domain's accounting-fact type. The concrete Register
# implementation is not present yet, so this boundary deliberately avoids
# introducing a duplicate persistence-owned Movement type.
Movement = Any


class RegisterFactPersistence(Protocol):
    """Append-only persistence contract for accepted register movements."""

    def append(self, movements: Sequence[Movement]) -> None:
        """Append accounting movements as persistent register facts."""
