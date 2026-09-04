import pytest

from accore.platform.storage import StorageKey


def test_storage_key_accepts_non_empty_value() -> None:
    key = StorageKey("objects/001")

    assert key.value == "objects/001"


def test_storage_key_is_immutable() -> None:
    key = StorageKey("objects/001")

    with pytest.raises(AttributeError):
        key.value = "objects/002"  # type: ignore[misc]


@pytest.mark.parametrize("value", ["", " ", "   ", "\t", "\n"])
def test_storage_key_rejects_empty_or_whitespace_value(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        StorageKey(value)


def test_storage_key_is_value_equal() -> None:
    assert StorageKey("objects/001") == StorageKey("objects/001")


def test_storage_key_is_not_equal_for_different_values() -> None:
    assert StorageKey("objects/001") != StorageKey("objects/002")
