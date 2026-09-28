from __future__ import annotations

from collections.abc import Sequence

from accore.platform.object import ObjectInstance

from .coordinator import (
    PostingLifecycleOutcome,
    PostingLifecycleResult,
    PostingResultParticipant,
    PostingResultPlan,
)
from .movement_set import MovementSet


class CompositePostingResultCoordinator:
    """Coordinate independent posting-result participants without transactions."""

    def __init__(self, participants: Sequence[PostingResultParticipant]) -> None:
        participants_tuple = tuple(participants)
        if not participants_tuple:
            raise ValueError("At least one posting-result participant is required.")
        self._participants = participants_tuple

    def prepare(self, document: ObjectInstance, movement_set: MovementSet) -> PostingResultPlan:
        return PostingResultPlan(
            participant_plans=tuple(
                participant.prepare(document, movement_set) for participant in self._participants
            )
        )

    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
        plan: PostingResultPlan,
    ) -> PostingLifecycleResult:
        if len(plan.participant_plans) != len(self._participants):
            raise ValueError("Posting result plan does not match the configured participants.")

        for participant, participant_plan in zip(
            self._participants,
            plan.participant_plans,
            strict=True,
        ):
            result = participant.establish(document, movement_set, participant_plan)
            if result.outcome is not PostingLifecycleOutcome.SUCCESS:
                return result
        return PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)

    def remove(self, document: ObjectInstance) -> PostingLifecycleResult:
        for participant in self._participants:
            result = participant.remove(document)
            if result.outcome is not PostingLifecycleOutcome.SUCCESS:
                return result
        return PostingLifecycleResult(PostingLifecycleOutcome.SUCCESS)


__all__ = ["CompositePostingResultCoordinator"]
