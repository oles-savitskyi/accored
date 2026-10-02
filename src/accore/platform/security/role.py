from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier

from .permission import Permission


@dataclass(frozen=True, slots=True)
class Role:
    """Explicit aggregate of authorization permissions."""

    identity: Identifier
    code: str
    name: str
    permissions: tuple[Permission, ...]

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("Role code must be non-empty")
        object.__setattr__(self, "permissions", tuple(self.permissions))
