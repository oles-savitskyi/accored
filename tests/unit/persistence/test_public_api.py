from accore.platform.persistence import (
    ConfigurationPersistence,
    Movement,
    ObjectDeletion,
    ObjectPersistence,
    PersistenceAlreadyExistsError,
    PersistenceConflictError,
    PersistenceError,
    PersistenceFailure,
    PersistenceIndeterminateError,
    PersistenceIntegrityError,
    PersistenceNotFoundError,
    PersistenceUnsupportedError,
    PersistentConfiguration,
    PersistentObject,
    RegisterFactPersistence,
)


def test_public_api_exports_final_persistence_contracts() -> None:
    assert ConfigurationPersistence is not None
    assert Movement is not None
    assert ObjectDeletion is not None
    assert ObjectPersistence is not None
    assert PersistentConfiguration is not None
    assert PersistentObject is not None
    assert RegisterFactPersistence is not None


def test_public_api_exports_final_error_taxonomy() -> None:
    errors = (
        PersistenceError,
        PersistenceNotFoundError,
        PersistenceAlreadyExistsError,
        PersistenceConflictError,
        PersistenceIntegrityError,
        PersistenceUnsupportedError,
        PersistenceFailure,
        PersistenceIndeterminateError,
    )

    assert all(error is not None for error in errors)
