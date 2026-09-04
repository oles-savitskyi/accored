from accore.platform.storage import (
    StorageKey,
    StorageNotFoundError,
)


class InMemoryStorageProvider:
    """Test-only storage provider used to verify the storage contract."""

    def __init__(self) -> None:
        self._data: dict[StorageKey, bytes] = {}

    def put(self, key: StorageKey, payload: bytes) -> None:
        self._data[key] = payload

    def get(self, key: StorageKey) -> bytes:
        try:
            return self._data[key]
        except KeyError as exc:
            raise StorageNotFoundError(f"Storage key not found: {key.value}") from exc

    def exists(self, key: StorageKey) -> bool:
        return key in self._data

    def delete(self, key: StorageKey) -> None:
        try:
            del self._data[key]
        except KeyError as exc:
            raise StorageNotFoundError(f"Storage key not found: {key.value}") from exc
