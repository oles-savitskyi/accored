from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PasswordCredentials:
    """Credentials accepted only at the local authentication boundary."""

    login: str
    password: str

    def __post_init__(self) -> None:
        if not self.login:
            raise ValueError("Password credentials login must be non-empty")
