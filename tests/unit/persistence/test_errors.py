from accore.platform.foundation.errors import AcCoreError
from accore.platform.persistence import (
    PersistenceAlreadyExistsError,
    PersistenceConflictError,
    PersistenceError,
    PersistenceFailure,
    PersistenceIndeterminateError,
    PersistenceIntegrityError,
    PersistenceNotFoundError,
    PersistenceUnsupportedError,
)


def test_persistence_error_is_ac_core_error() -> None:
    assert issubclass(PersistenceError, AcCoreError)


def test_semantic_persistence_errors_inherit_from_persistence_error() -> None:
    errors = (
        PersistenceNotFoundError,
        PersistenceAlreadyExistsError,
        PersistenceConflictError,
        PersistenceIntegrityError,
        PersistenceUnsupportedError,
        PersistenceFailure,
        PersistenceIndeterminateError,
    )

    assert all(issubclass(error, PersistenceError) for error in errors)
