from collections.abc import Callable
from pathlib import Path

import pytest

from accore.platform.storage import (
    StorageKey,
    StorageNotFoundError,
    StorageProvider,
)
from accore.platform.storage.filesystem import FilesystemStorageProvider

from .support import InMemoryStorageProvider

ProviderFactory = Callable[[], StorageProvider]


@pytest.fixture(
    params=[
        InMemoryStorageProvider,
        "filesystem",
    ],
    ids=["in-memory", "filesystem"],
)
def provider_factory(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> ProviderFactory:
    if request.param == "filesystem":
        return lambda: FilesystemStorageProvider(tmp_path)

    return request.param


@pytest.fixture
def provider(provider_factory: ProviderFactory) -> StorageProvider:
    return provider_factory()


def test_put_then_get_returns_payload(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/001")
    payload = b"hello"

    provider.put(key, payload)

    assert provider.get(key) == payload


def test_put_replaces_existing_payload(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, b"first")
    provider.put(key, b"second")

    assert provider.get(key) == b"second"


def test_get_missing_key_raises_not_found(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/missing")

    with pytest.raises(StorageNotFoundError):
        provider.get(key)


def test_exists_returns_false_for_missing_key(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/missing")

    assert provider.exists(key) is False


def test_exists_returns_true_after_put(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, b"payload")

    assert provider.exists(key) is True


def test_exists_returns_false_after_delete(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, b"payload")
    provider.delete(key)

    assert provider.exists(key) is False


def test_delete_removes_existing_payload(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, b"payload")
    provider.delete(key)

    with pytest.raises(StorageNotFoundError):
        provider.get(key)


def test_delete_missing_key_raises_not_found(
    provider: StorageProvider,
) -> None:
    key = StorageKey("objects/missing")

    with pytest.raises(StorageNotFoundError):
        provider.delete(key)


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"hello",
        b"\x00\x01\x02\xff",
        bytes(range(256)),
    ],
)
def test_arbitrary_bytes_are_preserved(
    provider: StorageProvider,
    payload: bytes,
) -> None:
    key = StorageKey("objects/001")

    provider.put(key, payload)

    assert provider.get(key) == payload
