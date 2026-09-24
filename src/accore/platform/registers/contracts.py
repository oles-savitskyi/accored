from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from accore.platform.foundation import Identifier

from .movement import Movement


class RegisterPostingContract(Protocol):
    def validate(self, movement: Movement) -> None: ...


class RegisterPostingContractResolver(Protocol):
    def resolve(self, register_identity: Identifier) -> RegisterPostingContract: ...


class MappingRegisterPostingContractResolver:
    """Resolve register posting contracts from a configured identity mapping."""

    def __init__(self, contracts: Mapping[Identifier, RegisterPostingContract]) -> None:
        self._contracts = dict(contracts)

    def resolve(self, register_identity: Identifier) -> RegisterPostingContract:
        try:
            return self._contracts[register_identity]
        except KeyError as exc:
            raise KeyError(
                f"No posting contract is configured for Register {register_identity!r}."
            ) from exc
