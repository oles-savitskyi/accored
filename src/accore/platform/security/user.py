from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier


@dataclass(frozen=True, slots=True)
class User:
    """Persistent security subject."""

    identity: Identifier
    login: str
    display_name: str
    email: str | None
    active: bool
    role_ids: tuple[Identifier, ...]

    def __post_init__(self) -> None:
        if not self.login:
            raise ValueError("User login must be non-empty")
        object.__setattr__(self, "role_ids", tuple(self.role_ids))
