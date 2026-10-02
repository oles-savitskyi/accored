from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier

from .constraint import AuthorizationConstraint
from .object import SecurityObjectIdentity
from .operation import SecurityOperation


@dataclass(frozen=True, slots=True)
class Permission:
    """Atomic authorization grant for one logical target and operation."""

    identity: Identifier
    target: SecurityObjectIdentity
    operation: SecurityOperation
    constraints: tuple[AuthorizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
