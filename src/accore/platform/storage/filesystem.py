import tempfile
from pathlib import Path

from .errors import StorageNotFoundError, StorageOperationError
from .key import StorageKey


class FilesystemStorageProvider:
    """Filesystem-backed implementation of the StorageProvider contract."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def _resolve_path(self, key: StorageKey) -> Path:
        relative = Path(key.value)

        if relative.is_absolute():
            raise StorageOperationError(f"Storage key must be relative: {key.value!r}")

        if ".." in relative.parts:
            raise StorageOperationError(
                f"Storage key must not contain parent traversal: {key.value!r}"
            )

        return self._root / relative

    def put(self, key: StorageKey, payload: bytes) -> None:
        target = self._resolve_path(key)
        temporary_path: Path | None = None

        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as temporary_file:
                temporary_file.write(payload)
                temporary_file.flush()
                temporary_path = Path(temporary_file.name)

            temporary_path.replace(target)
        except OSError as exc:
            raise StorageOperationError(f"Failed to store payload for key: {key.value!r}") from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def get(self, key: StorageKey) -> bytes:
        target = self._resolve_path(key)

        try:
            return target.read_bytes()
        except FileNotFoundError as exc:
            raise StorageNotFoundError(f"Storage key not found: {key.value!r}") from exc
        except OSError as exc:
            raise StorageOperationError(f"Failed to read payload for key: {key.value!r}") from exc

    def exists(self, key: StorageKey) -> bool:
        target = self._resolve_path(key)

        try:
            return target.exists()
        except OSError as exc:
            raise StorageOperationError(
                f"Failed to check existence for key: {key.value!r}"
            ) from exc

    def delete(self, key: StorageKey) -> None:
        target = self._resolve_path(key)

        try:
            target.unlink()
        except FileNotFoundError as exc:
            raise StorageNotFoundError(f"Storage key not found: {key.value!r}") from exc
        except OSError as exc:
            raise StorageOperationError(f"Failed to delete payload for key: {key.value!r}") from exc
