from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from accore.platform.value import (
    CollectionValue,
    DurableValueError,
    StructuredValue,
    is_durable_value,
    validate_durable_value,
)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        0,
        42,
        Decimal("10.50"),
        "text",
        date(2026, 9, 8),
        datetime(2026, 9, 8, 12, 30, tzinfo=UTC),
    ],
)
def test_supported_scalar_values_are_durable(value: object) -> None:
    assert is_durable_value(value)
    validate_durable_value(value)


@pytest.mark.parametrize("value", [1.0, None, object(), {"a": 1}, [1, 2], {1, 2}, (1, 2)])
def test_unsupported_values_are_not_durable(value: object) -> None:
    assert not is_durable_value(value)
    with pytest.raises(DurableValueError):
        validate_durable_value(value)


def test_datetime_and_date_are_distinct_scalar_kinds() -> None:
    value = datetime(2026, 9, 8, 12, 30, tzinfo=UTC)
    assert is_durable_value(value)
    assert type(value) is datetime
    assert type(value) is not date


def test_scalar_subclasses_are_rejected() -> None:
    class CustomString(str):
        pass

    assert not is_durable_value(CustomString("value"))


def test_structured_value_is_immutable_and_order_independent() -> None:
    first = StructuredValue({"b": 2, "a": 1})
    second = StructuredValue({"a": 1, "b": 2})

    assert first == second
    assert hash(first) == hash(second)
    assert first.items() == (("a", 1), ("b", 2))
    assert first["a"] == 1
    assert first.get("missing") is None
    assert "a" in first
    assert len(first) == 2


def test_structured_value_takes_an_immutable_snapshot() -> None:
    source = {"name": "Alice"}
    value = StructuredValue(source)

    source["name"] = "Bob"
    source["age"] = 42

    assert value["name"] == "Alice"
    assert "age" not in value


def test_structured_value_rejects_duplicate_keys() -> None:
    with pytest.raises(DurableValueError):
        StructuredValue([("name", "Alice"), ("name", "Bob")])


def test_structured_value_rejects_invalid_keys() -> None:
    with pytest.raises(DurableValueError):
        StructuredValue({"": 1})

    with pytest.raises(DurableValueError):
        StructuredValue({"   ": 1})


def test_structured_value_rejects_non_durable_values() -> None:
    with pytest.raises(DurableValueError):
        StructuredValue({"runtime": object()})


def test_structured_value_supports_recursive_values() -> None:
    value = StructuredValue(
        {
            "items": CollectionValue(
                [
                    1,
                    "two",
                    StructuredValue({"active": True}),
                ]
            )
        }
    )

    assert is_durable_value(value)
    items = value["items"]
    assert isinstance(items, CollectionValue)
    active = items[2]
    assert isinstance(active, StructuredValue)
    assert active["active"] is True


def test_collection_value_is_immutable_and_ordered() -> None:
    first = CollectionValue([1, 2, 3])
    second = CollectionValue([1, 2, 3])
    reversed_value = CollectionValue([3, 2, 1])

    assert first == second
    assert hash(first) == hash(second)
    assert first != reversed_value
    assert list(first) == [1, 2, 3]
    assert first[0] == 1
    assert first[1:] == CollectionValue([2, 3])


def test_collection_value_takes_an_immutable_snapshot() -> None:
    source = [1, 2]
    value = CollectionValue(source)

    source.append(3)

    assert list(value) == [1, 2]


def test_collection_value_rejects_non_durable_values() -> None:
    with pytest.raises(DurableValueError):
        CollectionValue([1, object()])


def test_empty_composites_are_valid() -> None:
    assert is_durable_value(StructuredValue({}))
    assert is_durable_value(CollectionValue(()))


def test_nested_composites_are_hashable() -> None:
    value = StructuredValue(
        {"values": CollectionValue([StructuredValue({"amount": Decimal("10.50")})])}
    )

    assert hash(value)
