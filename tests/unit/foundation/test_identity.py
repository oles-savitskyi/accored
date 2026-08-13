import pytest
import ulid

from accore.platform.foundation.identity import Identifier


def test_new_creates_identifier() -> None:
    identifier = Identifier.new()

    assert isinstance(identifier, Identifier)
    assert len(str(identifier)) == 26


def test_from_str_restores_identifier() -> None:
    value = "01KZXYTCY5ZGTC81ANSWAHKYV8"

    identifier = Identifier.from_str(value)

    assert str(identifier) == value


def test_identifiers_with_same_value_are_equal() -> None:
    value = "01KZXYTCY5ZGTC81ANSWAHKYV8"

    first = Identifier.from_str(value)
    second = Identifier.from_str(value)

    assert first == second


def test_identifier_is_immutable() -> None:
    identifier = Identifier.new()

    with pytest.raises(AttributeError):
        identifier._value = ulid.new()  # type: ignore[misc]


def test_invalid_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        Identifier.from_str("not-a-valid-ulid")
