"""Contract-to-operation registry for protocol-independent Integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contract import IntegrationContract, IntegrationContractIdentity
from .errors import IntegrationConflictError, IntegrationContractNotFoundError


class IntegrationOperationBinding(Protocol):
    """Executable behavior bound to an Integration contract."""

    def execute(self, request: object) -> object:
        """Execute a request using the operation's integration behavior."""
        ...


class IntegrationOperation(Protocol):
    """An Integration contract paired with its executable binding."""

    @property
    def contract(self) -> IntegrationContract:
        """Return the descriptive contract implemented by this operation."""
        ...

    @property
    def binding(self) -> IntegrationOperationBinding:
        """Return the executable behavior for this operation."""
        ...


@dataclass(frozen=True, slots=True)
class BoundIntegrationOperation:
    """Default immutable implementation of an Integration operation."""

    contract: IntegrationContract
    binding: IntegrationOperationBinding

    def __post_init__(self) -> None:
        if not isinstance(self.contract.identity, IntegrationContractIdentity):
            raise TypeError("Integration operation contract must expose a valid identity.")
        if not callable(getattr(self.binding, "execute", None)):
            raise TypeError("Integration operation binding must provide callable execute().")


class IntegrationOperationRegistry(Protocol):
    """Resolve stable contract identities to executable operations."""

    def register(self, operation: IntegrationOperation) -> None:
        """Register an operation, rejecting an identity already registered."""
        ...

    def resolve(self, identity: IntegrationContractIdentity) -> IntegrationOperation:
        """Resolve an exact contract identity or raise a contract error."""
        ...


class InMemoryIntegrationOperationRegistry:
    """In-memory registry with exact, deterministic identity resolution.

    Contract identity includes namespace, name, version, and kind. No version
    negotiation or fallback is performed. An identity can be registered only
    once; registration never silently replaces an existing operation.
    """

    def __init__(self) -> None:
        self._operations: dict[IntegrationContractIdentity, IntegrationOperation] = {}

    def register(self, operation: IntegrationOperation) -> None:
        try:
            contract = operation.contract
            identity = contract.identity
            binding = operation.binding
        except AttributeError as exc:
            raise TypeError(
                "Integration operation must expose contract.identity and binding."
            ) from exc

        if not isinstance(identity, IntegrationContractIdentity):
            raise TypeError("Integration operation contract must expose a valid identity.")
        if not callable(getattr(binding, "execute", None)):
            raise TypeError("Integration operation binding must provide callable execute().")
        if identity in self._operations:
            raise IntegrationConflictError(
                f"An Integration operation is already registered for {identity!r}."
            )

        self._operations[identity] = operation

    def resolve(self, identity: IntegrationContractIdentity) -> IntegrationOperation:
        if not isinstance(identity, IntegrationContractIdentity):
            raise TypeError("identity must be an IntegrationContractIdentity.")
        try:
            return self._operations[identity]
        except KeyError as exc:
            raise IntegrationContractNotFoundError(
                f"No Integration operation is registered for {identity!r}."
            ) from exc
