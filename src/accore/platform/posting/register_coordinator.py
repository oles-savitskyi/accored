from __future__ import annotations

from collections.abc import Sequence

from accore.platform.foundation import Identifier
from accore.platform.object import ObjectInstance
from accore.platform.persistence import RegisterFactPersistence
from accore.platform.persistence.errors import PersistenceError, PersistenceIndeterminateError
from accore.platform.registers import RegisterMutationOrchestrator

from .coordinator import PostingLifecycleOutcome, PostingLifecycleResult, RegisterPostingPlan
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

    def prepare(self, document: ObjectInstance, movement_set: MovementSet) -> RegisterPostingPlan:
        del document
        return RegisterPostingPlan(movements=movement_set)

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
    ) -> PostingLifecycleResult:
        del document, movement_set
        if not isinstance(plan, RegisterPostingPlan):
            raise TypeError("Register participant received an invalid posting plan.")
        try:
            self._mutation.establish(plan.movements.movements)
        except PersistenceIndeterminateError as exc:
            return PostingLifecycleResult(PostingLifecycleOutcome.INDETERMINATE, exc)
        except PersistenceError as exc:
            return PostingLifecycleResult(PostingLifecycleOutcome.FAILURE, exc)
        return PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult:
        try:
            for register_identity in self._register_identities:
                movements = self._persistence.find_by_source_document(
                    register_identity,
                    document.identity,
                )
                if movements:
                    self._mutation.remove(movements)
        except PersistenceIndeterminateError as exc:
            return PostingLifecycleResult(PostingLifecycleOutcome.INDETERMINATE, exc)
        except PersistenceError as exc:
            return PostingLifecycleResult(PostingLifecycleOutcome.FAILURE, exc)
        return PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)


__all__ = ["RegisterPostingResultCoordinator"]
