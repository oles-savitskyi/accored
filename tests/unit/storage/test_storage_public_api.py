from accore.platform.storage import (
    StorageError,
    StorageKey,
    StorageNotFoundError,
    StorageOperationError,
    StorageProvider,
)


def test_storage_public_api_exports_contract_types() -> None:
    assert StorageKey is not None
    assert StorageProvider is not None
    assert StorageError is not None
    assert StorageNotFoundError is not None
    assert StorageOperationError is not None


def test_storage_provider_is_protocol() -> None:
    assert getattr(StorageProvider, "_is_protocol", False) is True
