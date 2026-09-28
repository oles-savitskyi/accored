from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from accore.platform.object import ObjectInstance

from .movement_set import MovementSet


@dataclass(frozen=True, slots=True)
class RegisterPostingPlan:
    """Immutable register-side posting plan."""

    movements: MovementSet


@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    """Opaque immutable plan containing ordered participant preparations."""

    participant_plans: tuple[object, ...]


class PostingLifecycleOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class PostingLifecycleResult:
    outcome: PostingLifecycleOutcome
    error: Exception | None = None


class PostingResultParticipant(Protocol):
    """One independent posting-result lifecycle participant."""

    def prepare(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> object: ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: object,
    ) -> PostingLifecycleResult: ...

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult: ...


class PostingResultCoordinator(Protocol):
    def prepare(self, document: ObjectInstance, movement_set: MovementSet) -> PostingResultPlan: ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> PostingLifecycleResult: ...

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult: ...
