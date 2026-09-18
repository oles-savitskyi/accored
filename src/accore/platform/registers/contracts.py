from __future__ import annotations

from typing import Protocol

from accore.platform.foundation import Identifier

from .movement import Movement


class RegisterPostingContract(Protocol):
    def validate(self, movement: Movement) -> None: ...


class RegisterPostingContractResolver(Protocol):
    def resolve(self, register_identity: Identifier) -> RegisterPostingContract: ...
