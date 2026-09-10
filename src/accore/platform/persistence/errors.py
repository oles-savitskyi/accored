from __future__ import annotations

from accore.platform.foundation.errors import AcCoreError


class PersistenceError(AcCoreError):
    """Base error for semantic persistence failures."""


class PersistenceNotFoundError(PersistenceError):
    """Raised when a required persistent resource does not exist."""


class PersistenceAlreadyExistsError(PersistenceError):
    """Raised when creation conflicts with an existing logical identity."""


class PersistenceConflictError(PersistenceError):
    """Raised when a contract-specific concurrency conflict is detected."""


class PersistenceIntegrityError(PersistenceError):
    """Raised when a persistence integrity invariant is violated."""


class PersistenceUnsupportedError(PersistenceError):
    """Raised when the required persistence capability is unsupported."""


class PersistenceFailure(PersistenceError):
    """Raised when persistence fails without an indeterminate outcome."""


class PersistenceIndeterminateError(PersistenceError):
    """Raised when the outcome of a persistence operation cannot be established."""
