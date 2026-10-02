from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SecurityObjectIdentity:
    """Logical identity of a protected security target."""

    object_type: str
    object_code: str

    def __post_init__(self) -> None:
        if not self.object_type:
            raise ValueError("Security object type must be non-empty")
        if not self.object_code:
            raise ValueError("Security object code must be non-empty")
