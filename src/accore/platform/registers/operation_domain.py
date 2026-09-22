from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import TypeVar

from accore.platform.foundation import Identifier

T = TypeVar("T")


class RegisterOperationDomain:
    """Register-scoped process-local operation domain."""

    def __init__(self, register_identity: Identifier) -> None:
        self._register_identity = register_identity
        self._lock = RLock()

    @property
    def register_identity(self) -> Identifier:
        return self._register_identity

    def execute(self, operation: Callable[[], T]) -> T:
        with self._lock:
            return operation()


class RegisterOperationDomainRegistry:
    """Registry providing one shared operation domain per Register identity."""

    def __init__(self) -> None:
        self._guard = RLock()
        self._domains: dict[Identifier, RegisterOperationDomain] = {}

    def get(self, register_identity: Identifier) -> RegisterOperationDomain:
        with self._guard:
            domain = self._domains.get(register_identity)
            if domain is None:
                domain = RegisterOperationDomain(register_identity)
                self._domains[register_identity] = domain
            return domain
