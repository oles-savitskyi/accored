from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfigurationIdentity:
    """Immutable logical identity of a metadata configuration."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Configuration identity must not be empty.")

    def __str__(self) -> str:
        """Return the canonical configuration identity."""
        return self.value


@dataclass(frozen=True, slots=True)
class ConfigurationVersion:
    """Immutable revision number of a metadata configuration."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("Configuration version must be greater than zero.")

    def __str__(self) -> str:
        """Return the canonical configuration version."""
        return str(self.value)
