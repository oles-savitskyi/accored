from __future__ import annotations

from collections.abc import Sequence

from accore.platform.foundation import Identifier
from accore.platform.object import ObjectInstance
from accore.platform.persistence import RegisterFactPersistence
from accore.platform.registers import RegisterMutationOrchestrator

from .movement_set import MovementSet


class RegisterPostingResultCoordinator:
    """Bridge Posting results to authoritative Register mutation."""

    def __init__(
        self,
        mutation: RegisterMutationOrchestrator,
        persistence: RegisterFactPersistence,
        register_identities: Sequence[Identifier],
    ) -> None:
        identities = tuple(register_identities)
        if not identities:
            raise ValueError("At least one Register identity is required.")
        if len(set(identities)) != len(identities):
            raise ValueError("Register identities must be unique.")

        self._mutation = mutation
        self._persistence = persistence
        self._register_identities = identities

    def establish(self, document: ObjectInstance, movement_set: MovementSet) -> None:
        del document
        self._mutation.establish(movement_set.movements)

    def remove(self, document: ObjectInstance) -> None:
        for register_identity in self._register_identities:
            movements = self._persistence.find_by_source_document(
                register_identity,
                document.identity,
            )
            if movements:
                self._mutation.remove(movements)


__all__ = ["RegisterPostingResultCoordinator"]
