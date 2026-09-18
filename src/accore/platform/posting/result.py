from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PostingOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class PostingResult:
    outcome: PostingOutcome
    error: Exception | None = None

    @property
    def is_success(self) -> bool:
        return self.outcome is PostingOutcome.SUCCESS

    @property
    def is_failure(self) -> bool:
        return self.outcome is PostingOutcome.FAILURE

    @property
    def is_indeterminate(self) -> bool:
        return self.outcome is PostingOutcome.INDETERMINATE

    @classmethod
    def success(cls) -> PostingResult:
        return cls(PostingOutcome.SUCCESS)

    @classmethod
    def failure(cls, error: Exception) -> PostingResult:
        return cls(PostingOutcome.FAILURE, error)

    @classmethod
    def indeterminate(cls, error: Exception) -> PostingResult:
        return cls(PostingOutcome.INDETERMINATE, error)
