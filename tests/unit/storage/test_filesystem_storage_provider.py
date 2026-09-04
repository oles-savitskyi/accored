from pathlib import Path
from unittest.mock import patch

import pytest

from accore.platform.storage import StorageKey, StorageNotFoundError, StorageOperationError
from accore.platform.storage.filesystem import FilesystemStorageProvider


@pytest.fixture
def provider(tmp_path: Path) -> FilesystemStorageProvider:
    return FilesystemStorageProvider(tmp_path)


def test_resolve_path_maps_relative_key_under_root(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/001")

    result = provider._resolve_path(key)

    assert result == tmp_path / "objects" / "001"


def test_resolve_path_supports_nested_relative_key(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/2026/09/item.bin")

    result = provider._resolve_path(key)

    assert result == tmp_path / "objects" / "2026" / "09" / "item.bin"


@pytest.mark.parametrize(
    "value",
    [
        "/absolute/path",
        "/etc/passwd",
    ],
)
def test_resolve_path_rejects_absolute_key(
    provider: FilesystemStorageProvider,
    value: str,
) -> None:
    with pytest.raises(StorageOperationError):
        provider._resolve_path(StorageKey(value))


@pytest.mark.parametrize(
    "value",
    [
        "..",
        "../outside",
        "objects/../outside",
        "objects/../../outside",
    ],
)
def test_resolve_path_rejects_parent_traversal(
    provider: FilesystemStorageProvider,
    value: str,
) -> None:
    with pytest.raises(StorageOperationError):
        provider._resolve_path(StorageKey(value))


def test_resolve_path_does_not_require_existing_target(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/not-yet-created")

    result = provider._resolve_path(key)

    assert result == tmp_path / "objects" / "not-yet-created"
    assert not result.exists()


def test_put_creates_payload(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/001")
    payload = b"hello"

    provider.put(key, payload)

    assert (tmp_path / "objects" / "001").read_bytes() == payload


def test_put_creates_parent_directories(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/2026/09/item.bin")
    payload = b"payload"

    provider.put(key, payload)

    target = tmp_path / "objects" / "2026" / "09" / "item.bin"

    assert target.is_file()
    assert target.read_bytes() == payload


def test_put_preserves_empty_payload(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/empty")
    payload = b""

    provider.put(key, payload)

    target = tmp_path / "objects" / "empty"

    assert target.is_file()
    assert target.read_bytes() == payload


def test_put_preserves_arbitrary_binary_payload(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/binary")
    payload = bytes(range(256))

    provider.put(key, payload)

    assert (tmp_path / "objects" / "binary").read_bytes() == payload


def test_put_replaces_existing_payload(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/001")
    target = tmp_path / "objects" / "001"

    provider.put(key, b"first")
    provider.put(key, b"second")

    assert target.read_bytes() == b"second"


@pytest.mark.parametrize(
    "value",
    [
        "/absolute/path",
        "../outside",
        "objects/../outside",
    ],
)
def test_put_rejects_invalid_key(
    provider: FilesystemStorageProvider,
    value: str,
) -> None:
    with pytest.raises(StorageOperationError):
        provider.put(StorageKey(value), b"payload")


def test_put_does_not_leave_temporary_file(
    provider: FilesystemStorageProvider,
    tmp_path: Path,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, b"payload")

    files = list((tmp_path / "objects").iterdir())

    assert files == [tmp_path / "objects" / "001"]


def test_put_translates_directory_creation_failure(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/001")

    filesystem_error = OSError("cannot create directory")

    with (
        patch.object(
            Path,
            "mkdir",
            side_effect=filesystem_error,
        ),
        pytest.raises(StorageOperationError) as exc_info,
    ):
        provider.put(key, b"payload")

    assert exc_info.value.__cause__ is filesystem_error


def test_put_translates_temporary_file_failure(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/001")

    filesystem_error = OSError("cannot create temporary file")

    with (
        patch(
            "accore.platform.storage.filesystem.tempfile.NamedTemporaryFile",
            side_effect=filesystem_error,
        ),
        pytest.raises(StorageOperationError) as exc_info,
    ):
        provider.put(key, b"payload")

    assert exc_info.value.__cause__ is filesystem_error


def test_put_translates_replace_failure(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/001")

    filesystem_error = OSError("cannot replace target")

    with (
        patch.object(
            Path,
            "replace",
            side_effect=filesystem_error,
        ),
        pytest.raises(StorageOperationError) as exc_info,
    ):
        provider.put(key, b"payload")

    assert exc_info.value.__cause__ is filesystem_error


def test_get_returns_stored_payload(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/001")
    payload = b"hello"

    provider.put(key, payload)

    assert provider.get(key) == payload


def test_get_returns_empty_payload(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/empty")

    provider.put(key, b"")

    assert provider.get(key) == b""


def test_get_returns_arbitrary_binary_payload(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/binary")
    payload = bytes(range(256))

    provider.put(key, payload)

    assert provider.get(key) == payload


def test_get_missing_key_raises_storage_not_found_error(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/missing")

    with pytest.raises(StorageNotFoundError) as exc_info:
        provider.get(key)

    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


@pytest.mark.parametrize(
    "value",
    [
        "/absolute/path",
        "../outside",
        "objects/../outside",
    ],
)
def test_get_rejects_invalid_key(
    provider: FilesystemStorageProvider,
    value: str,
) -> None:
    with pytest.raises(StorageOperationError):
        provider.get(StorageKey(value))


def test_get_translates_filesystem_failure(
    provider: FilesystemStorageProvider,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, b"payload")

    filesystem_error = OSError("cannot read file")

    with (
        patch.object(
            Path,
            "read_bytes",
            side_effect=filesystem_error,
        ),
        pytest.raises(StorageOperationError) as exc_info,
    ):
        provider.get(key)

    assert exc_info.value.__cause__ is filesystem_error


def test_exists_returns_true_for_existing_payload(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("payload.bin")

    provider.put(key, b"payload")

    assert provider.exists(key) is True


def test_exists_returns_false_for_missing_payload(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("missing.bin")

    assert provider.exists(key) is False


def test_exists_returns_true_for_empty_payload(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("empty.bin")

    provider.put(key, b"")

    assert provider.exists(key) is True


def test_exists_supports_nested_keys(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("nested/path/payload.bin")

    provider.put(key, b"payload")

    assert provider.exists(key) is True


@pytest.mark.parametrize(
    "value",
    [
        "/absolute/path",
        "../outside",
        "nested/../outside",
        "nested/../../outside",
    ],
)
def test_exists_rejects_invalid_filesystem_keys(
    tmp_path: Path,
    value: str,
) -> None:
    provider = FilesystemStorageProvider(tmp_path)

    with pytest.raises(StorageOperationError):
        provider.exists(StorageKey(value))


def test_exists_translates_filesystem_error(
    tmp_path: Path,
) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("payload.bin")

    with (
        patch.object(
            Path,
            "exists",
            side_effect=OSError("simulated failure"),
        ),
        pytest.raises(StorageOperationError) as exc_info,
    ):
        provider.exists(key)

    assert isinstance(exc_info.value.__cause__, OSError)


def test_delete_removes_existing_payload(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("payload.bin")

    provider.put(key, b"payload")

    provider.delete(key)

    assert provider.exists(key) is False


def test_delete_removes_empty_payload(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("empty.bin")

    provider.put(key, b"")

    provider.delete(key)

    assert provider.exists(key) is False


def test_delete_removes_nested_payload(tmp_path: Path) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("nested/path/payload.bin")

    provider.put(key, b"payload")

    provider.delete(key)

    assert provider.exists(key) is False


def test_delete_missing_payload_raises_storage_not_found_error(
    tmp_path: Path,
) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("missing.bin")

    with pytest.raises(StorageNotFoundError) as exc_info:
        provider.delete(key)

    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


@pytest.mark.parametrize(
    "value",
    [
        "/absolute/path",
        "../outside",
        "nested/../outside",
        "nested/../../outside",
    ],
)
def test_delete_rejects_invalid_filesystem_keys(
    tmp_path: Path,
    value: str,
) -> None:
    provider = FilesystemStorageProvider(tmp_path)

    with pytest.raises(StorageOperationError):
        provider.delete(StorageKey(value))


def test_delete_translates_filesystem_error(
    tmp_path: Path,
) -> None:
    provider = FilesystemStorageProvider(tmp_path)
    key = StorageKey("payload.bin")

    provider.put(key, b"payload")

    with (
        patch.object(
            Path,
            "unlink",
            side_effect=OSError("simulated failure"),
        ),
        pytest.raises(StorageOperationError) as exc_info,
    ):
        provider.delete(key)

    assert isinstance(exc_info.value.__cause__, OSError)
