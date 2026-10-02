from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from accore.platform.foundation.identity import Identifier


class PrincipalType(StrEnum):
    USER = "user"
    SERVICE = "service"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class SecurityClaim:
    """Opaque immutable authentication attribute."""

    name: str
    value: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Security claim name must be non-empty")


@dataclass(frozen=True, slots=True)
class Principal:
    """Runtime authenticated identity."""

    identity: Identifier
    identity_type: PrincipalType
    claims: tuple[SecurityClaim, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", tuple(self.claims))
