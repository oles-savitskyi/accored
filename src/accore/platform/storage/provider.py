from typing import Protocol

from .key import StorageKey


class StorageProvider(Protocol):
    """Provider-neutral contract for opaque persistent storage."""

    def put(self, key: StorageKey, payload: bytes) -> None:
        """Create or replace the payload associated with key."""
        ...

    def get(self, key: StorageKey) -> bytes:
        """Return the payload associated with key."""
        ...

    def exists(self, key: StorageKey) -> bool:
        """Return whether a payload exists for key."""
        ...

    def delete(self, key: StorageKey) -> None:
        """Delete the payload associated with key."""
        ...
