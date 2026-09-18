from __future__ import annotations

from typing import Protocol

from .contracts import RegisterPostingContractResolver
from .movement import Movement


class MovementSetLike(Protocol):
    @property
    def movements(self) -> tuple[Movement, ...]: ...


class MovementValidationError(ValueError):
    """Raised when a MovementSet is not acceptable for Register posting."""


class MovementValidator(Protocol):
    def validate(self, movement_set: MovementSetLike) -> None: ...


class DefaultMovementValidator:
    def __init__(self, contracts: RegisterPostingContractResolver) -> None:
        self._contracts = contracts

    def validate(self, movement_set: MovementSetLike) -> None:
        for movement in movement_set.movements:
            if not isinstance(movement, Movement):
                raise MovementValidationError("MovementSet contains an invalid Movement.")
            contract = self._contracts.resolve(movement.register_identity)
            contract.validate(movement)
