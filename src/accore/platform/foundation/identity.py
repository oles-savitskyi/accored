from __future__ import annotations

from dataclasses import dataclass

import ulid


@dataclass(frozen=True, slots=True)
class Identifier:
    """Immutable AcCoreD identifier backed by a ULID."""

    _value: ulid.ULID

    @classmethod
    def new(cls) -> Identifier:
        """Create a new identifier."""
        return cls(ulid.new())

    @classmethod
    def from_str(cls, value: str) -> Identifier:
        """Create an identifier from its string representation."""
        return cls(ulid.from_str(value))

    def __str__(self) -> str:
        """Return the canonical string representation."""
        return str(self._value)
