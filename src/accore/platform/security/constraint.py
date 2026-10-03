from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .authorization import AuthorizationRequest


class AuthorizationConstraint(Protocol):
    """Constraint evaluated as part of an authorization permission."""

    @property
    def code(self) -> str: ...

    def evaluate(self, request: AuthorizationRequest) -> bool: ...
