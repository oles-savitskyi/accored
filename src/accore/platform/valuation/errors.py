from __future__ import annotations


class ValuationError(Exception):
    """Base error for Valuation semantic failures."""


class ValuationValidationError(ValuationError):
    """Raised when valuation input or a valuation fact is invalid."""


class ValuationConflictError(ValuationError):
    """Raised when a valuation operation conflicts with existing state."""


class ValuationInsufficientQuantityError(ValuationError):
    """Raised when valuation consumption exceeds available quantity."""


class ValuationNotFoundError(ValuationError):
    """Raised when a required valuation entity cannot be found."""


class ValuationPersistenceError(ValuationError):
    """Persistence failure with an explicitly known rollback outcome."""

    def __init__(self, message: str, *, rollback_guaranteed: bool) -> None:
        super().__init__(message)
        self.rollback_guaranteed = rollback_guaranteed
