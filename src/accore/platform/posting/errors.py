from __future__ import annotations

from accore.platform.persistence.errors import PersistenceIndeterminateError


class PostingError(Exception):
    """Base error for Posting semantic failures."""


class PostingValidationError(PostingError):
    pass


class PostingHandlerResolutionError(PostingError):
    pass


class PostingHandlerError(PostingError):
    pass


class PostingMovementValidationError(PostingError):
    pass


class PostingRegisterAcceptanceError(PostingError):
    pass


class PostingPersistenceError(PostingError):
    pass


class PostingIndeterminateError(PostingError):
    pass


def is_indeterminate(exc: BaseException) -> bool:
    return isinstance(exc, (PostingIndeterminateError, PersistenceIndeterminateError))
