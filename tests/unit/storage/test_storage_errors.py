from accore.platform.storage import (
    StorageError,
    StorageNotFoundError,
    StorageOperationError,
)


def test_storage_not_found_error_is_storage_error() -> None:
    assert issubclass(StorageNotFoundError, StorageError)


def test_storage_operation_error_is_storage_error() -> None:
    assert issubclass(StorageOperationError, StorageError)


def test_storage_errors_are_exceptions() -> None:
    assert issubclass(StorageError, Exception)


def test_storage_not_found_error_can_carry_message() -> None:
    error = StorageNotFoundError("missing key")

    assert str(error) == "missing key"


def test_storage_operation_error_can_carry_message() -> None:
    error = StorageOperationError("backend failure")

    assert str(error) == "backend failure"
