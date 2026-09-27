from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from accore.platform.object import ObjectInstance

from .movement_set import MovementSet

if TYPE_CHECKING:
    from accore.platform.valuation import ValuationPlan


@dataclass(frozen=True, slots=True)
class RegisterPostingPlan:
    """Immutable register-side posting plan."""

    movements: MovementSet


@dataclass(frozen=True, slots=True)
class PostingResultPlan:
    """Immutable composite posting plan prepared before destructive lifecycle work."""

    register: RegisterPostingPlan
    valuation: ValuationPlan


class PostingLifecycleOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class PostingLifecycleResult:
    outcome: PostingLifecycleOutcome
    error: Exception | None = None


class PostingResultCoordinator(Protocol):
    def prepare(self, document: ObjectInstance, movement_set: MovementSet) -> PostingResultPlan: ...

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> PostingLifecycleResult: ...

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult: ...
