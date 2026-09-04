class StorageError(Exception):
    """Base exception for storage provider failures."""


class StorageNotFoundError(StorageError):
    """Raised when a requested storage key does not exist."""


class StorageOperationError(StorageError):
    """Raised when a storage operation fails due to the underlying provider."""
