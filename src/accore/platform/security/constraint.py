from __future__ import annotations

from typing import Protocol


class AuthorizationConstraint(Protocol):
    """Constraint evaluated as part of an authorization permission."""

    @property
    def code(self) -> str: ...

    def evaluate(self, request: object) -> bool: ...
